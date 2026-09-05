"""Adaptador SQLAlchemy das portas `RepositorioDeProjetos` (M1) e `RepositorioDeARA` (M2).

A regra que este arquivo existe para não deixar escapar: **toda consulta filtra pelo
inquilino**. Não há método que leia sem ele, e não há valor padrão — a assinatura da porta
já o exige, e aqui o `WHERE tenant_id = :inquilino` aparece em todas as consultas.

Exclusão suave: `apagado_em` preenchido. `obter()` devolve o projeto MESMO excluído — é o
que permite restaurar; quem esconde o excluído é `listar()`, que é o que a interface usa.

**Por que os filhos são gravados por reconciliação e não por apagar-e-reinserir.**
Apagar todos os nós e reinseri-los seria mais curto de escrever e destruiria dado alheio:
`aresta_causal`, `elo_exame`, `ude` e `conector_e` têm chave estrangeira com
`ON DELETE CASCADE` para `no`, então um apaga-tudo levaria junto o exame de um elo que
ninguém tocou. A reconciliação (inserir/atualizar o que está no agregado, apagar só o que
saiu dele) preserva o que sobreviveu, e a cascata continua fazendo o que deve: quando um
nó realmente sai, o que dependia dele sai com ele.

A ordem das operações não é estética, é a ordem que as chaves estrangeiras impõem:
projeto → apaga arestas que saíram → apaga nós que saíram → grava nós → grava arestas.
"""
from __future__ import annotations

from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import delete, insert, select, true, update
from sqlalchemy.dialects.postgresql import insert as insert_pg
from sqlalchemy.orm import sessionmaker

from ...dominio.ara import (
    ConectorE,
    Exame,
    EstadoDoExame,
    FichaDeUde,
    OrigemDoParecer,
    ParecerDeJulgamento,
    ProjetoARA,
    StatusDeValidacao,
    reidratar_ara,
)
from ...dominio.grafo import ArestaCausal, No
from ...dominio.identidade import DonoDoProjeto
from ...dominio.projeto import Projeto
from ...dominio.valores import PosicaoNoCanvas
from .tabelas import aresta_causal as tabela_aresta
from .tabelas import conector_e as tabela_conector
from .tabelas import conector_e_aresta as tabela_conector_aresta
from .tabelas import elo_exame as tabela_exame
from .tabelas import no as tabela_no
from .tabelas import projeto as tabela_projeto
from .tabelas import tenant_ref as tabela_tenant
from .tabelas import ude as tabela_ude
from .tabelas import ude_parecer as tabela_parecer


def _para_agregado(linha: Any, nos: tuple[No, ...], arestas: tuple[ArestaCausal, ...]) -> Projeto:
    projeto = Projeto(
        id=linha.id,
        dono=DonoDoProjeto(inquilino_id=linha.tenant_id, usuario_id=linha.usuario_id),
        nome=linha.nome,
        ferramenta=linha.ferramenta,
        descricao_do_problema=linha.descricao_do_problema or "",
        versao=linha.versao,
        criado_em=linha.criado_em,
        alterado_em=linha.atualizado_em,
        excluido_em=linha.apagado_em,
        nos=nos,
        arestas=arestas,
    )
    # Carregar não é mutar: o agregado volta do banco sem eventos pendentes.
    projeto.eventos = ()
    return projeto


def _para_linha(p: Projeto) -> dict[str, Any]:
    return {
        "id": p.id,
        "tenant_id": p.dono.inquilino_id,
        "usuario_id": p.dono.usuario_id,
        "nome": p.nome,
        "ferramenta": p.ferramenta,
        "descricao_do_problema": p.descricao_do_problema,
        "versao": p.versao,
        "criado_em": p.criado_em,
        "atualizado_em": p.alterado_em,
        "apagado_em": p.excluido_em,
    }


class RepositorioDeProjetosSQL:
    def __init__(self, sessao: sessionmaker) -> None:
        self._sessao = sessao

    # -- escrita (M1) --------------------------------------------------------------

    def salvar(self, projeto: Projeto) -> None:
        with self._sessao.begin() as s:
            self._gravar_projeto(s, projeto)
            self._reconciliar_grafo(s, projeto)

    def _gravar_projeto(self, s, projeto: Projeto) -> None:
        linha = _para_linha(projeto)
        # Garante a referência de inquilino que a chave estrangeira exige. Quem mantém
        # `nome_exibicao` é o adaptador de embarque (ciclo 003) — aqui só a existência
        # e o "visto em", e nunca sobrescrevendo o nome que o handshake gravou.
        s.execute(
            insert_pg(tabela_tenant)
            .values(
                tenant_id=projeto.dono.inquilino_id,
                nome_exibicao=None,
                visto_em=projeto.alterado_em,
            )
            .on_conflict_do_update(
                index_elements=[tabela_tenant.c.tenant_id],
                set_={"visto_em": projeto.alterado_em},
            )
        )
        existe = s.execute(
            select(tabela_projeto.c.id).where(
                tabela_projeto.c.id == projeto.id,
                tabela_projeto.c.tenant_id == projeto.dono.inquilino_id,
            )
        ).first()
        if existe is None:
            s.execute(insert(tabela_projeto).values(**linha))
        else:
            s.execute(
                update(tabela_projeto)
                .where(
                    tabela_projeto.c.id == projeto.id,
                    tabela_projeto.c.tenant_id == projeto.dono.inquilino_id,
                )
                .values(**{k: v for k, v in linha.items() if k != "id"})
            )

    def _reconciliar_grafo(self, s, projeto: Projeto) -> None:
        ids_de_no = [n.id for n in projeto.nos]
        ids_de_aresta = [a.id for a in projeto.arestas]

        s.execute(
            delete(tabela_aresta).where(
                tabela_aresta.c.projeto_id == projeto.id,
                tabela_aresta.c.id.notin_(ids_de_aresta) if ids_de_aresta else true(),
            )
        )
        s.execute(
            delete(tabela_no).where(
                tabela_no.c.projeto_id == projeto.id,
                tabela_no.c.id.notin_(ids_de_no) if ids_de_no else true(),
            )
        )
        for no in projeto.nos:
            valores = {
                "id": no.id,
                "projeto_id": projeto.id,
                "tipo": no.tipo,
                "titulo": no.titulo,
                "descricao": no.descricao,
                "pos_x": no.posicao.x,
                "pos_y": no.posicao.y,
                "recolhido": no.recolhido,
                "criado_em": projeto.criado_em,
                "alterado_em": projeto.alterado_em,
            }
            s.execute(
                insert_pg(tabela_no)
                .values(**valores)
                .on_conflict_do_update(
                    index_elements=[tabela_no.c.id],
                    set_={
                        k: v for k, v in valores.items() if k not in ("id", "criado_em")
                    },
                )
            )
        for aresta in projeto.arestas:
            valores = {
                "id": aresta.id,
                "projeto_id": projeto.id,
                "origem_id": aresta.origem_id,
                "destino_id": aresta.destino_id,
                "rotulo": aresta.rotulo,
                "criado_em": projeto.criado_em,
                "alterado_em": projeto.alterado_em,
            }
            s.execute(
                insert_pg(tabela_aresta)
                .values(**valores)
                .on_conflict_do_update(
                    index_elements=[tabela_aresta.c.id],
                    set_={
                        k: v for k, v in valores.items() if k not in ("id", "criado_em")
                    },
                )
            )

    # -- leitura (M1) --------------------------------------------------------------

    def obter(self, inquilino_id: str, projeto_id: UUID) -> Projeto | None:
        with self._sessao() as s:
            linha = s.execute(
                select(tabela_projeto).where(
                    tabela_projeto.c.id == projeto_id,
                    tabela_projeto.c.tenant_id == inquilino_id,
                )
            ).first()
            if linha is None:
                return None
            return _para_agregado(linha, *self._carregar_grafo(s, projeto_id))

    def _carregar_grafo(self, s, projeto_id: UUID):
        nos = tuple(
            No(
                id=linha.id,
                titulo=linha.titulo,
                descricao=linha.descricao or "",
                tipo=linha.tipo,
                posicao=PosicaoNoCanvas(float(linha.pos_x), float(linha.pos_y)),
                recolhido=linha.recolhido,
            )
            for linha in s.execute(
                select(tabela_no)
                .where(tabela_no.c.projeto_id == projeto_id)
                .order_by(tabela_no.c.criado_em, tabela_no.c.id)
            ).all()
        )
        arestas = tuple(
            ArestaCausal(
                id=linha.id,
                origem_id=linha.origem_id,
                destino_id=linha.destino_id,
                rotulo=linha.rotulo or "",
            )
            for linha in s.execute(
                select(tabela_aresta)
                .where(tabela_aresta.c.projeto_id == projeto_id)
                .order_by(tabela_aresta.c.criado_em, tabela_aresta.c.id)
            ).all()
        )
        return nos, arestas

    def listar(
        self,
        inquilino_id: str,
        *,
        usuario_id: str | None = None,
        incluir_excluidos: bool = False,
    ) -> list[Projeto]:
        consulta = select(tabela_projeto).where(tabela_projeto.c.tenant_id == inquilino_id)
        if usuario_id is not None:
            consulta = consulta.where(tabela_projeto.c.usuario_id == usuario_id)
        if not incluir_excluidos:
            consulta = consulta.where(tabela_projeto.c.apagado_em.is_(None))
        consulta = consulta.order_by(tabela_projeto.c.atualizado_em.desc())
        with self._sessao() as s:
            linhas = s.execute(consulta).all()
            return [
                _para_agregado(linha, *self._carregar_grafo(s, linha.id))
                for linha in linhas
            ]

    # -- Árvore da Realidade Atual (M2) ---------------------------------------------

    def salvar_ara(self, ara: ProjetoARA) -> None:
        projeto = ara.projeto
        with self._sessao.begin() as s:
            self._gravar_projeto(s, projeto)
            self._reconciliar_grafo(s, projeto)
            self._reconciliar_ara(s, ara)

    def _reconciliar_ara(self, s, ara: ProjetoARA) -> None:
        projeto_id = ara.projeto.id
        marcados = list(ara.udes)

        # A ficha e o status são estado ATUAL: reconcilia. Os pareceres são
        # somente-acréscimo no agregado, e o agregado é a fonte — reescrevê-los na íntegra
        # devolve exatamente a mesma sequência, na mesma ordem.
        s.execute(
            delete(tabela_ude).where(
                tabela_ude.c.projeto_id == projeto_id,
                tabela_ude.c.no_id.notin_(marcados) if marcados else true(),
            )
        )
        for no_id in marcados:
            ficha = ara.ficha(no_id)
            valores = {
                "no_id": no_id,
                "projeto_id": projeto_id,
                "status": ara.status(no_id).value,
                "area_impactada": ficha.area_impactada,
                "objetivo_afetado": ficha.objetivo_afetado,
                "evidencias": list(ficha.evidencias),
                "frequencia": ficha.frequencia,
                "impactos_estimados": ficha.impactos_estimados,
            }
            s.execute(
                insert_pg(tabela_ude)
                .values(**valores)
                .on_conflict_do_update(
                    index_elements=[tabela_ude.c.no_id],
                    set_={k: v for k, v in valores.items() if k != "no_id"},
                )
            )
            s.execute(delete(tabela_parecer).where(tabela_parecer.c.no_id == no_id))
            for parecer in ara.pareceres(no_id):
                s.execute(
                    insert(tabela_parecer).values(
                        id=uuid4(),
                        no_id=no_id,
                        autor=parecer.autor,
                        origem=parecer.origem.value,
                        favoravel=parecer.favoravel,
                        justificativa=parecer.justificativa,
                        instante=parecer.instante,
                        proposta_id=parecer.proposta_id,
                        criterios=list(parecer.criterios),
                    )
                )

        # Exame de elo: só as arestas que EXISTEM e que foram examinadas ganham linha.
        examinados = {
            aresta.id: ara.exame(aresta.id)
            for aresta in ara.arestas
            if ara.exame(aresta.id).estado is not EstadoDoExame.NAO_EXAMINADO
        }
        s.execute(
            delete(tabela_exame).where(
                tabela_exame.c.projeto_id == projeto_id,
                tabela_exame.c.aresta_id.notin_(list(examinados)) if examinados else true(),
            )
        )
        for aresta_id, exame in examinados.items():
            valores = {
                "aresta_id": aresta_id,
                "projeto_id": projeto_id,
                "estado": exame.estado.value,
                "reserva": exame.reserva,
            }
            s.execute(
                insert_pg(tabela_exame)
                .values(**valores)
                .on_conflict_do_update(
                    index_elements=[tabela_exame.c.aresta_id],
                    set_={k: v for k, v in valores.items() if k != "aresta_id"},
                )
            )

        conectores = ara.conectores
        s.execute(
            delete(tabela_conector).where(
                tabela_conector.c.projeto_id == projeto_id,
                tabela_conector.c.id.notin_([c.id for c in conectores])
                if conectores
                else true(),
            )
        )
        for conector in conectores:
            s.execute(
                insert_pg(tabela_conector)
                .values(
                    id=conector.id,
                    projeto_id=projeto_id,
                    destino_id=conector.destino_id,
                )
                .on_conflict_do_update(
                    index_elements=[tabela_conector.c.id],
                    set_={"destino_id": conector.destino_id},
                )
            )
            s.execute(
                delete(tabela_conector_aresta).where(
                    tabela_conector_aresta.c.conector_id == conector.id
                )
            )
            for aresta_id in conector.arestas:
                s.execute(
                    insert(tabela_conector_aresta).values(
                        conector_id=conector.id, aresta_id=aresta_id
                    )
                )

    def obter_ara(self, inquilino_id: str, projeto_id: UUID) -> ProjetoARA | None:
        projeto = self.obter(inquilino_id, projeto_id)
        if projeto is None:
            return None
        with self._sessao() as s:
            fichas, status = {}, {}
            for linha in s.execute(
                select(tabela_ude).where(tabela_ude.c.projeto_id == projeto_id)
            ).all():
                fichas[linha.no_id] = FichaDeUde(
                    area_impactada=linha.area_impactada,
                    objetivo_afetado=linha.objetivo_afetado,
                    evidencias=tuple(linha.evidencias or ()),
                    frequencia=linha.frequencia,
                    impactos_estimados=linha.impactos_estimados,
                )
                status[linha.no_id] = StatusDeValidacao(linha.status)

            pareceres: dict[UUID, list[ParecerDeJulgamento]] = {}
            if fichas:
                for linha in s.execute(
                    select(tabela_parecer)
                    .where(tabela_parecer.c.no_id.in_(list(fichas)))
                    .order_by(tabela_parecer.c.instante, tabela_parecer.c.id)
                ).all():
                    pareceres.setdefault(linha.no_id, []).append(
                        ParecerDeJulgamento(
                            autor=linha.autor,
                            origem=OrigemDoParecer(linha.origem),
                            favoravel=linha.favoravel,
                            justificativa=linha.justificativa,
                            instante=linha.instante,
                            proposta_id=linha.proposta_id,
                            criterios=tuple(linha.criterios or ()),
                        )
                    )

            exames = {
                linha.aresta_id: Exame(
                    estado=EstadoDoExame(linha.estado), reserva=linha.reserva
                )
                for linha in s.execute(
                    select(tabela_exame).where(tabela_exame.c.projeto_id == projeto_id)
                ).all()
            }

            arestas_por_conector: dict[UUID, list[UUID]] = {}
            for linha in s.execute(
                select(tabela_conector_aresta)
                .join(
                    tabela_conector,
                    tabela_conector.c.id == tabela_conector_aresta.c.conector_id,
                )
                .where(tabela_conector.c.projeto_id == projeto_id)
            ).all():
                arestas_por_conector.setdefault(linha.conector_id, []).append(
                    linha.aresta_id
                )
            conectores = tuple(
                ConectorE(
                    id=linha.id,
                    destino_id=linha.destino_id,
                    arestas=tuple(arestas_por_conector.get(linha.id, ())),
                )
                for linha in s.execute(
                    select(tabela_conector).where(
                        tabela_conector.c.projeto_id == projeto_id
                    )
                ).all()
            )

        return reidratar_ara(
            projeto,
            udes=fichas,
            status=status,
            pareceres=pareceres,
            exames=exames,
            conectores=conectores,
        )

    # -- administração ---------------------------------------------------------------

    def excluir_definitivamente(self, inquilino_id: str, projeto_id: UUID) -> bool:
        """Exclusão DEFINITIVA — fora da porta de propósito.

        A porta expõe só o que o domínio precisa; apagar linha é operação de administração
        e entra pelo caso de uso que a spec 004 definir (RF-10), com o portão que ela
        exigir. Está aqui porque o adaptador é quem sabe fazê-lo, não porque é rotina.
        """
        with self._sessao.begin() as s:
            resultado = s.execute(
                delete(tabela_projeto).where(
                    tabela_projeto.c.id == projeto_id,
                    tabela_projeto.c.tenant_id == inquilino_id,
                )
            )
        return bool(resultado.rowcount)
