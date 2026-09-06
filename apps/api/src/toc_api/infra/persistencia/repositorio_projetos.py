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

**A trava otimista, e por que a reconciliação a torna obrigatória.** A reconciliação
grava o retrato do agregado que está em memória e apaga do banco o que ficou fora dele.
Isso é correto quando existe UM retrato por vez e catastrófico quando existem dois: duas
pessoas que abriram a mesma análise leem a versão 7, cada uma acrescenta o seu nó, e a
segunda gravação apaga o nó da primeira pelo `id.notin_` — sem exceção, sem código de
erro, sem aviso. Medido antes do conserto: **20 escritas concorrentes de nó, 20 aceitas,
1 nó no banco**. A coluna `versao` existia e era incrementada, mas nunca aparecia num
`WHERE`, então era um contador, não uma trava.

Agora toda gravação passa por `_gravar_projeto`, e ela condiciona a escrita à versão que
foi LIDA (`UPDATE … WHERE versao = :versao_lida`). É o mesmo ponto para as três portas —
`salvar` (M1), `salvar_ara` (M2) e `salvar_nuvem` (M3) —, o que fecha a classe e não o
caso: nenhuma delas alcança as reconciliações sem passar pela trava primeiro. Quem perde
a corrida recebe `ConflitoDeVersao` com os dois números, a transação inteira volta atrás,
e a borda HTTP traduz em `409 VERSION_CONFLICT`. Perder é legítimo; perder sem saber, não.
A aptidão que impede o retorno é `scripts/check-trava-otimista.sh`.
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
from ...dominio.nuvem import (
    EstadoDaPremissa,
    Injecao,
    NuvemDeConflito,
    Premissa,
    ReferenciaDeOrigem,
    ReferenciaDeSemeadura,
    SeparacaoTRIZ,
    StatusDeInjecao,
    reidratar_nuvem,
)
from ...dominio.erros import ConflitoDeVersao, NaoEncontrado
from ...dominio.identidade import DonoDoProjeto
from ...dominio.projeto import Projeto
from ...dominio.valores import PosicaoNoCanvas
from .tabelas import aresta_causal as tabela_aresta
from .tabelas import conector_e as tabela_conector
from .tabelas import conector_e_aresta as tabela_conector_aresta
from .tabelas import elo_exame as tabela_exame
from .tabelas import nc_injecao as tabela_injecao
from .tabelas import nc_nuvem as tabela_nuvem
from .tabelas import nc_premissa as tabela_premissa
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
    # A base da trava otimista: o agregado sai daqui sabendo de que versão ele partiu.
    # Sem esta linha `versao` é só um contador em memória — que foi exatamente o defeito.
    projeto.versao_lida = linha.versao
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
        projeto.confirmar_gravacao()

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
            select(tabela_projeto.c.versao).where(
                tabela_projeto.c.id == projeto.id,
                tabela_projeto.c.tenant_id == projeto.dono.inquilino_id,
            )
        ).first()

        if projeto.versao_lida == 0:
            # Agregado que nunca foi gravado. Se já existe linha com este identificador,
            # quem chamou está prestes a passar por cima de um registro que não leu — e é
            # a mesma perda de atualização, só que com o retrato inteiro.
            if existe is not None:
                raise ConflitoDeVersao(
                    f"projeto:{projeto.id}", versao_lida=0, versao_atual=existe.versao
                )
            s.execute(insert(tabela_projeto).values(**linha))
            return

        if existe is None:
            # O registro sumiu debaixo de quem o leu (exclusão DEFINITIVA por outro
            # caminho). Recriá-lo aqui ressuscitaria dado apagado de propósito.
            raise NaoEncontrado(str(projeto.id))

        # A TRAVA. O `WHERE versao = :versao_lida` é a linha inteira do conserto: quem
        # não leu a versão que está no banco não escreve. O PostgreSQL serializa as duas
        # escritas no bloqueio desta linha — a segunda espera a primeira comitar, refaz o
        # predicado sob READ COMMITTED, não casa mais, e volta com `rowcount` 0.
        resultado = s.execute(
            update(tabela_projeto)
            .where(
                tabela_projeto.c.id == projeto.id,
                tabela_projeto.c.tenant_id == projeto.dono.inquilino_id,
                tabela_projeto.c.versao == projeto.versao_lida,
            )
            .values(**{k: v for k, v in linha.items() if k != "id"})
        )
        if resultado.rowcount == 0:
            # Relê a versão AGORA, e não a do `select` acima: entre um e outro a
            # concorrente pode ter comitado, e o número que o cliente recebe tem de ser
            # o que o banco tem, para ele recarregar e refazer.
            atual = s.execute(
                select(tabela_projeto.c.versao).where(
                    tabela_projeto.c.id == projeto.id,
                    tabela_projeto.c.tenant_id == projeto.dono.inquilino_id,
                )
            ).first()
            if atual is None:
                raise NaoEncontrado(str(projeto.id))
            raise ConflitoDeVersao(
                f"projeto:{projeto.id}",
                versao_lida=projeto.versao_lida,
                versao_atual=atual.versao,
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
        projeto.confirmar_gravacao()

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

    # -- Nuvem de Conflito (M3, spec 007) ---------------------------------------------
    #
    # Mesma disciplina do M2: reconciliação, nunca apagar-e-reinserir. Aqui ela vale por um
    # motivo a mais — `nc_injecao.premissa_id` tem `ON DELETE CASCADE`, então apagar todas
    # as premissas para reinseri-las levaria junto injeções que ninguém tocou, e a
    # invariante RN-04 (injeção referencia premissa viva) se cumpriria por destruição.
    #
    # A ordem também é imposta pelas chaves estrangeiras: projeto → grafo (as 5 entidades e
    # as 7 arestas são nó e aresta do M1) → nuvem → premissas → injeções.

    def salvar_nuvem(self, nuvem: NuvemDeConflito) -> None:
        projeto = nuvem.projeto
        with self._sessao.begin() as s:
            self._gravar_projeto(s, projeto)
            self._reconciliar_grafo(s, projeto)
            self._reconciliar_nuvem(s, nuvem)
        projeto.confirmar_gravacao()

    def _reconciliar_nuvem(self, s, nuvem: NuvemDeConflito) -> None:
        projeto_id = nuvem.projeto.id
        origem = nuvem.origem
        valores = {
            "projeto_id": projeto_id,
            "racional": nuvem.racional,
            "origem_ferramenta": origem.ferramenta if origem else None,
            "origem_projeto_id": origem.projeto_id if origem else None,
            "origem_nos": list(origem.nos) if origem else [],
        }
        s.execute(
            insert_pg(tabela_nuvem)
            .values(**valores)
            .on_conflict_do_update(
                index_elements=[tabela_nuvem.c.projeto_id],
                set_={k: v for k, v in valores.items() if k != "projeto_id"},
            )
        )

        # Premissas e injeções ARQUIVADAS continuam no agregado (RF-15: arquivar não
        # apaga), então a reconciliação escreve todas — o que sai da lista é o que o
        # agregado deixou de conhecer, e aí a linha vai embora mesmo.
        todas_as_premissas = list(nuvem._premissas.values())
        ids_de_premissa = [p.id for p in todas_as_premissas]
        todas_as_injecoes = list(nuvem._injecoes.values())
        ids_de_injecao = [i.id for i in todas_as_injecoes]

        s.execute(
            delete(tabela_injecao).where(
                tabela_injecao.c.projeto_id == projeto_id,
                tabela_injecao.c.id.notin_(ids_de_injecao) if ids_de_injecao else true(),
            )
        )
        s.execute(
            delete(tabela_premissa).where(
                tabela_premissa.c.projeto_id == projeto_id,
                tabela_premissa.c.id.notin_(ids_de_premissa) if ids_de_premissa else true(),
            )
        )

        arestas_por_chave = {
            nuvem.chave_da_aresta(a.id): a.id for a in nuvem.projeto.arestas
        }
        for premissa in todas_as_premissas:
            linha = {
                "id": premissa.id,
                "projeto_id": projeto_id,
                "aresta_id": arestas_por_chave[premissa.aresta],
                "texto": premissa.texto,
                "ordem": premissa.ordem,
                "estado": premissa.estado.value,
                "justificativa": premissa.justificativa,
                "arquivada": premissa.arquivada,
            }
            s.execute(
                insert_pg(tabela_premissa)
                .values(**linha)
                .on_conflict_do_update(
                    index_elements=[tabela_premissa.c.id],
                    set_={k: v for k, v in linha.items() if k != "id"},
                )
            )
        for injecao in todas_as_injecoes:
            linha = {
                "id": injecao.id,
                "projeto_id": projeto_id,
                "premissa_id": injecao.premissa_id,
                "texto": injecao.texto,
                "status": injecao.status.value,
                "separacao": injecao.separacao.value if injecao.separacao else None,
                "arquivada": injecao.arquivada,
                # A referência de semeadura EXISTE quando a injeção está escolhida; o que
                # se grava é o destino, que o ciclo 008 preencherá (INT-06).
                "semeadura_projeto_id": (
                    injecao.semeadura.projeto_destino_id if injecao.semeadura else None
                ),
            }
            s.execute(
                insert_pg(tabela_injecao)
                .values(**linha)
                .on_conflict_do_update(
                    index_elements=[tabela_injecao.c.id],
                    set_={k: v for k, v in linha.items() if k != "id"},
                )
            )

    def obter_nuvem(self, inquilino_id: str, projeto_id: UUID) -> NuvemDeConflito | None:
        projeto = self.obter(inquilino_id, projeto_id)
        if projeto is None:
            return None
        with self._sessao() as s:
            cabecalho = s.execute(
                select(tabela_nuvem).where(tabela_nuvem.c.projeto_id == projeto_id)
            ).first()
            linhas_de_premissa = s.execute(
                select(tabela_premissa)
                .where(tabela_premissa.c.projeto_id == projeto_id)
                .order_by(tabela_premissa.c.ordem, tabela_premissa.c.id)
            ).all()
            linhas_de_injecao = s.execute(
                select(tabela_injecao)
                .where(tabela_injecao.c.projeto_id == projeto_id)
                .order_by(tabela_injecao.c.id)
            ).all()

        if cabecalho is None:
            # Projeto que não tem cabeçalho de nuvem não é uma Nuvem de Conflito. A
            # resposta é `None` pelo mesmo motivo do inquilino: quem pergunta descobre que
            # não achou, e não o que o projeto é.
            return None

        # A chave da aresta é derivada do par de papéis, e é o agregado quem sabe derivá-la
        # — por isso a nuvem é montada com a topologia antes de as premissas entrarem.
        provisoria = NuvemDeConflito(projeto=projeto)
        chave_por_aresta = {
            aresta.id: provisoria.chave_da_aresta(aresta.id) for aresta in projeto.arestas
        }
        premissas = [
            Premissa(
                id=linha.id,
                aresta=chave_por_aresta[linha.aresta_id],
                texto=linha.texto,
                ordem=linha.ordem,
                estado=EstadoDaPremissa(linha.estado),
                justificativa=linha.justificativa,
                arquivada=linha.arquivada,
            )
            for linha in linhas_de_premissa
        ]
        injecoes = []
        for linha in linhas_de_injecao:
            status = StatusDeInjecao(linha.status)
            injecoes.append(
                Injecao(
                    id=linha.id,
                    premissa_id=linha.premissa_id,
                    texto=linha.texto,
                    status=status,
                    separacao=SeparacaoTRIZ(linha.separacao) if linha.separacao else None,
                    arquivada=linha.arquivada,
                    semeadura=(
                        ReferenciaDeSemeadura(
                            injecao_id=linha.id,
                            projeto_destino_id=linha.semeadura_projeto_id,
                        )
                        if status is StatusDeInjecao.ESCOLHIDA
                        else None
                    ),
                )
            )
        origem = (
            ReferenciaDeOrigem(
                ferramenta=cabecalho.origem_ferramenta,
                projeto_id=cabecalho.origem_projeto_id,
                nos=tuple(cabecalho.origem_nos or ()),
            )
            if cabecalho.origem_ferramenta
            else None
        )
        return reidratar_nuvem(
            projeto,
            racional=cabecalho.racional or "",
            premissas=premissas,
            injecoes=injecoes,
            origem=origem,
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
