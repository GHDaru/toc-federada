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
from uuid import UUID, uuid4, uuid5

from sqlalchemy import delete, insert, or_, select, true, update
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
from ...dominio.apr import (
    ElipseDeSimultaneidade,
    JulgamentoDeValidade,
    ParObstaculoOI,
    ProjetoAPR,
    reidratar_apr,
)
from ...dominio.arf import (
    EspelhoDeUde,
    EstadoDoRamo,
    ProjetoARF,
    RamoNegativo,
    reidratar_arf,
)
from ...dominio.at import FichaDePasso, ProjetoAT, StatusDoPasso, reidratar_at
from ...dominio.focalizacao import (
    ORDEM_CANONICA,
    AnaliseDeFocalizacao,
    CicloDeFocalizacao,
    DecisaoDePasso,
    DecisaoHerdada,
    EstadoDoCiclo,
    EstadoDoPasso,
    NotaDePasso,
    PassoDeFocalizacao,
    Reabertura,
    ReferenciaDeOrigemDaRestricao,
    Restricao,
    SistemaAnalisado,
    TipoDeFerramentaVinculada,
    TipoDePasso,
    TipoDeRestricao,
    VereditoDeHeranca,
    VinculoDeFerramenta,
    reidratar_analise,
)
from ...dominio.grafo import ArestaCausal, No
from ...dominio.referencia import (
    EstadoDaReferencia,
    Ponta,
    ReferenciaCruzada,
    TipoDeReferencia,
    reidratar_referencia,
)
from ...dominio.suficiencia import ConectorE as ConectorDeSuficiencia
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
from .tabelas import apr_arvore as tabela_apr
from .tabelas import apr_elipse as tabela_elipse
from .tabelas import apr_elipse_dependencia as tabela_elipse_dependencia
from .tabelas import apr_julgamento as tabela_julgamento
from .tabelas import apr_par as tabela_par
from .tabelas import aresta_causal as tabela_aresta
from .tabelas import arf_arvore as tabela_arf
from .tabelas import arf_espelho as tabela_espelho
from .tabelas import arf_ramo_negativo as tabela_ramo
from .tabelas import at_arvore as tabela_at
from .tabelas import at_passo as tabela_passo
from .tabelas import referencia_cruzada as tabela_referencia
from .tabelas import conector_e as tabela_conector
from .tabelas import conector_e_aresta as tabela_conector_aresta
from .tabelas import elo_exame as tabela_exame
from .tabelas import foco_analise as tabela_foco
from .tabelas import foco_ciclo as tabela_foco_ciclo
from .tabelas import foco_decisao as tabela_foco_decisao
from .tabelas import foco_heranca as tabela_foco_heranca
from .tabelas import foco_nota as tabela_foco_nota
from .tabelas import foco_passo as tabela_foco_passo
from .tabelas import foco_reabertura as tabela_foco_reabertura
from .tabelas import foco_restricao as tabela_foco_restricao
from .tabelas import foco_vinculo as tabela_foco_vinculo
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


def _para_ponta(ferramenta, projeto_id, elementos, papel) -> Ponta | None:
    """A ponta tipada de volta do banco — ou `None` quando a coluna está vazia.

    As duas metades andam juntas por restrição de tabela (`origem_da_arf_completa`), então
    conferir a ferramenta basta: ou as duas estão preenchidas, ou nenhuma está.
    """
    if not ferramenta:
        return None
    return Ponta(
        ferramenta=ferramenta,
        projeto_id=projeto_id,
        elementos=tuple(elementos or ()),
        papel=papel or "",
    )


def _referencia_para_linha(r: ReferenciaCruzada) -> dict[str, Any]:
    return {
        "id": r.id,
        "tenant_id": r.dono.inquilino_id,
        "usuario_id": r.dono.usuario_id,
        "tipo": r.tipo.value,
        "origem_ferramenta": r.origem.ferramenta,
        "origem_projeto_id": r.origem.projeto_id,
        "origem_elementos": list(r.origem.elementos),
        "origem_papel": r.origem.papel,
        "destino_ferramenta": r.destino.ferramenta,
        "destino_projeto_id": r.destino.projeto_id,
        "destino_elementos": list(r.destino.elementos),
        "destino_papel": r.destino.papel,
        "estado": r.estado.value,
        "motivo": r.motivo,
        "versao": r.versao,
        "criada_em": r.criada_em,
    }


def _para_referencia(linha: Any) -> ReferenciaCruzada:
    return reidratar_referencia(
        id=linha.id,
        tipo=TipoDeReferencia(linha.tipo),
        origem=Ponta(
            ferramenta=linha.origem_ferramenta,
            projeto_id=linha.origem_projeto_id,
            elementos=tuple(linha.origem_elementos or ()),
            papel=linha.origem_papel or "",
        ),
        destino=Ponta(
            ferramenta=linha.destino_ferramenta,
            projeto_id=linha.destino_projeto_id,
            elementos=tuple(linha.destino_elementos or ()),
            papel=linha.destino_papel or "",
        ),
        dono=DonoDoProjeto(inquilino_id=linha.tenant_id, usuario_id=linha.usuario_id),
        criada_em=linha.criada_em,
        estado=EstadoDaReferencia(linha.estado),
        motivo=linha.motivo or "",
        versao=linha.versao,
    )


# ---------------------------------------------------------------------------------------
# M6 · Focalização — a tradução linha ↔ agregado
# ---------------------------------------------------------------------------------------


def _id_da_decisao(ciclo_id: UUID, passo: TipoDePasso, indice: int) -> UUID:
    """A chave de linha de uma decisão de passo — DERIVADA, nunca sorteada.

    Decisão de passo e reabertura são objetos de VALOR numa lista somente-acréscimo: elas
    não têm identidade no domínio, e inventar um `uuid4()` aqui geraria uma chave nova a
    cada gravação — o que transformaria toda escrita numa reinserção completa e faria a
    reconciliação apagar e recriar histórico que ninguém tocou.

    `uuid5` sobre `(ciclo, passo, índice)` é estável porque a lista **só cresce** (RN-04):
    o índice de uma decisão já gravada nunca muda. É a mesma escolha, pelo mesmo motivo,
    que qualquer mapeamento de coleção ordenada imutável para linhas de tabela.
    """
    return uuid5(ciclo_id, f"foco.decisao:{passo.value}:{indice}")


def _id_da_reabertura(ciclo_id: UUID, passo: TipoDePasso, indice: int) -> UUID:
    return uuid5(ciclo_id, f"foco.reabertura:{passo.value}:{indice}")


def _para_ciclo(
    linha: Any,
    *,
    restricao: Any,
    passos: list[Any],
    decisoes: list[Any],
    notas: list[Any],
    reaberturas: list[Any],
    vinculos: list[Any],
    herancas: list[Any],
) -> CicloDeFocalizacao:
    """Monta um ciclo a partir das linhas — na ORDEM CANÔNICA, sempre.

    Os passos vêm do banco ordenados por `ordem`, mas o ciclo é montado percorrendo
    `ORDEM_CANONICA`: um banco que devolvesse quatro passos, ou os cinco fora de ordem,
    faz o construtor de `CicloDeFocalizacao` levantar `PassoInvalido` em vez de carregar
    uma jornada torta em silêncio.
    """
    estado_por_tipo = {p.tipo: p.estado for p in passos}
    montados: list[PassoDeFocalizacao] = []
    for tipo in ORDEM_CANONICA:
        do_passo = tipo.value
        montados.append(
            PassoDeFocalizacao(
                tipo=tipo,
                estado=EstadoDoPasso(estado_por_tipo.get(do_passo, EstadoDoPasso.PENDENTE.value)),
                decisoes=tuple(
                    DecisaoDePasso(texto=d.texto, autor=d.autor, instante=d.instante)
                    for d in decisoes
                    if d.passo == do_passo
                ),
                notas=tuple(
                    NotaDePasso(id=n.id, texto=n.texto, autor=n.autor, instante=n.instante)
                    for n in notas
                    if n.passo == do_passo
                ),
                vinculos=tuple(
                    VinculoDeFerramenta(
                        id=v.id,
                        tipo=TipoDeFerramentaVinculada(v.ferramenta),
                        projeto_id=v.alvo_projeto_id,
                        papel=v.papel or "",
                        justificativa=v.justificativa or "",
                        canonico=v.canonico,
                    )
                    for v in vinculos
                    if v.passo == do_passo
                ),
                reaberturas=tuple(
                    Reabertura(
                        justificativa=r.justificativa, autor=r.autor, instante=r.instante
                    )
                    for r in reaberturas
                    if r.passo == do_passo
                ),
            )
        )
    return CicloDeFocalizacao(
        id=linha.id,
        ordem=linha.ordem,
        aberto_em=linha.aberto_em,
        passos=tuple(montados),
        estado=EstadoDoCiclo(linha.estado),
        fechado_em=linha.fechado_em,
        restricao=None
        if restricao is None
        else Restricao(
            id=restricao.id,
            descricao=restricao.descricao,
            tipo=TipoDeRestricao(restricao.tipo),
            justificativa=restricao.justificativa,
            autor=restricao.autor,
            registrada_em=restricao.registrada_em,
            origem=None
            if not restricao.origem_ferramenta
            else ReferenciaDeOrigemDaRestricao(
                ferramenta=restricao.origem_ferramenta,
                projeto_id=restricao.origem_projeto_id,
                no_id=restricao.origem_no_id,
            ),
        ),
        heranca=tuple(
            DecisaoHerdada(
                id=h.id,
                ciclo_de_origem=h.ciclo_de_origem,
                passo=TipoDePasso(h.passo),
                texto=h.texto,
                veredito=VereditoDeHeranca(h.veredito),
                justificativa=h.justificativa or "",
                autor=h.autor or "",
                julgada_em=h.julgada_em,
            )
            for h in herancas
        ),
    )


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

        # Exame de elo e conector E: as MESMAS tabelas e o MESMO caminho da ARF. O
        # pacote de suficiência causal é compartilhado no domínio (RF-03 da spec 008), e
        # duplicar a reconciliação aqui seria a cópia voltando pela porta do adaptador.
        self._reconciliar_suficiencia(
            s, projeto_id, ara.arestas, ara.exame, ara.conectores
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

            exames, conectores = self._carregar_suficiencia(s, projeto_id)

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


    # -- M4 · Árvores de Futuro e Implementação (spec 008) ----------------------------
    #
    # Mesma disciplina do M2 e do M3: reconciliação, nunca apagar-e-reinserir, e a MESMA
    # trava otimista — as três árvores gravam por `_gravar_projeto`, como o M1, o M2 e o
    # M3. Fechar a classe e não o caso é o que `scripts/check-trava-otimista.sh` confere.
    #
    # A ARF não tem tabela própria de exame nem de conector: ela reusa `elo_exame` e
    # `conector_e`, do M2. É a contraparte física da decisão 1 do plano do ciclo 008 — o
    # pacote de suficiência causal é extraído, nunca copiado.

    def salvar_arf(self, arf: ProjetoARF) -> None:
        projeto = arf.projeto
        with self._sessao.begin() as s:
            self._gravar_projeto(s, projeto)
            self._reconciliar_grafo(s, projeto)
            self._reconciliar_arf(s, arf)
        projeto.confirmar_gravacao()

    def _reconciliar_arf(self, s, arf: ProjetoARF) -> None:
        projeto_id = arf.projeto.id
        origem = arf.origem
        cabecalho = {
            "projeto_id": projeto_id,
            "origem_ferramenta": origem.ferramenta if origem else None,
            "origem_projeto_id": origem.projeto_id if origem else None,
            "origem_elementos": list(origem.elementos) if origem else [],
            "origem_papel": origem.papel if origem else "",
            "udes_da_cadeia": list(arf.udes_da_cadeia),
        }
        s.execute(
            insert_pg(tabela_arf)
            .values(**cabecalho)
            .on_conflict_do_update(
                index_elements=[tabela_arf.c.projeto_id],
                set_={k: v for k, v in cabecalho.items() if k != "projeto_id"},
            )
        )

        espelhos = dict(arf.espelhos())
        s.execute(
            delete(tabela_espelho).where(
                tabela_espelho.c.projeto_id == projeto_id,
                tabela_espelho.c.no_id.notin_(list(espelhos)) if espelhos else true(),
            )
        )
        for no_id, espelho in espelhos.items():
            linha = {
                "no_id": no_id,
                "projeto_id": projeto_id,
                "ude_id": espelho.ude_id,
                "projeto_de_origem_id": espelho.projeto_de_origem_id,
            }
            s.execute(
                insert_pg(tabela_espelho)
                .values(**linha)
                .on_conflict_do_update(
                    index_elements=[tabela_espelho.c.no_id],
                    set_={k: v for k, v in linha.items() if k != "no_id"},
                )
            )

        ramos = arf.ramos()
        s.execute(
            delete(tabela_ramo).where(
                tabela_ramo.c.projeto_id == projeto_id,
                tabela_ramo.c.id.notin_([r.id for r in ramos]) if ramos else true(),
            )
        )
        for ramo in ramos:
            linha = {
                "id": ramo.id,
                "projeto_id": projeto_id,
                "raiz_id": ramo.raiz_id,
                "estado": ramo.estado.value,
                "injecao_de_corte_id": ramo.injecao_de_corte_id,
                "justificativa": ramo.justificativa,
                "autor": ramo.autor,
            }
            s.execute(
                insert_pg(tabela_ramo)
                .values(**linha)
                .on_conflict_do_update(
                    index_elements=[tabela_ramo.c.id],
                    set_={k: v for k, v in linha.items() if k != "id"},
                )
            )

        self._reconciliar_suficiencia(s, projeto_id, arf.arestas, arf.exame, arf.conectores)

    def _reconciliar_suficiencia(self, s, projeto_id, arestas, exame_de, conectores) -> None:
        """O exame de elo e o conector E — as MESMAS tabelas do M2, para as duas árvores."""
        examinados = {
            aresta.id: exame_de(aresta.id)
            for aresta in arestas
            if exame_de(aresta.id).estado is not EstadoDoExame.NAO_EXAMINADO
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
                    id=conector.id, projeto_id=projeto_id, destino_id=conector.destino_id
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

    def obter_arf(self, inquilino_id: str, projeto_id: UUID) -> ProjetoARF | None:
        projeto = self.obter(inquilino_id, projeto_id)
        if projeto is None:
            return None
        with self._sessao() as s:
            cabecalho = s.execute(
                select(tabela_arf).where(tabela_arf.c.projeto_id == projeto_id)
            ).first()
            if cabecalho is None:
                # Projeto sem cabeçalho de ARF não é uma Árvore da Realidade Futura. A
                # resposta é `None` pelo mesmo motivo do inquilino: quem pergunta descobre
                # que não achou, e não o que o projeto é.
                return None
            espelhos = {
                linha.no_id: EspelhoDeUde(
                    ude_id=linha.ude_id, projeto_de_origem_id=linha.projeto_de_origem_id
                )
                for linha in s.execute(
                    select(tabela_espelho).where(tabela_espelho.c.projeto_id == projeto_id)
                ).all()
            }
            ramos = tuple(
                RamoNegativo(
                    id=linha.id,
                    raiz_id=linha.raiz_id,
                    estado=EstadoDoRamo(linha.estado),
                    injecao_de_corte_id=linha.injecao_de_corte_id,
                    justificativa=linha.justificativa,
                    autor=linha.autor,
                )
                for linha in s.execute(
                    select(tabela_ramo).where(tabela_ramo.c.projeto_id == projeto_id)
                ).all()
            )
            exames, conectores = self._carregar_suficiencia(s, projeto_id)

        return reidratar_arf(
            projeto,
            espelhos=espelhos,
            ramos=ramos,
            exames=exames,
            conectores=conectores,
            origem=_para_ponta(
                cabecalho.origem_ferramenta,
                cabecalho.origem_projeto_id,
                cabecalho.origem_elementos,
                cabecalho.origem_papel,
            ),
            udes_da_cadeia=tuple(cabecalho.udes_da_cadeia or ()),
        )

    def _carregar_suficiencia(self, s, projeto_id: UUID):
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
            arestas_por_conector.setdefault(linha.conector_id, []).append(linha.aresta_id)
        conectores = tuple(
            ConectorDeSuficiencia(
                id=linha.id,
                destino_id=linha.destino_id,
                arestas=tuple(arestas_por_conector.get(linha.id, ())),
            )
            for linha in s.execute(
                select(tabela_conector).where(tabela_conector.c.projeto_id == projeto_id)
            ).all()
        )
        return exames, conectores

    # -- Árvore de Pré-Requisitos -----------------------------------------------------

    def salvar_apr(self, apr: ProjetoAPR) -> None:
        projeto = apr.projeto
        with self._sessao.begin() as s:
            self._gravar_projeto(s, projeto)
            self._reconciliar_grafo(s, projeto)
            self._reconciliar_apr(s, apr)
        projeto.confirmar_gravacao()

    def _reconciliar_apr(self, s, apr: ProjetoAPR) -> None:
        projeto_id = apr.projeto.id
        origem = apr.origem
        cabecalho = {
            "projeto_id": projeto_id,
            "origem_ferramenta": origem.ferramenta if origem else None,
            "origem_projeto_id": origem.projeto_id if origem else None,
            "origem_elementos": list(origem.elementos) if origem else [],
            "origem_papel": origem.papel if origem else "",
        }
        s.execute(
            insert_pg(tabela_apr)
            .values(**cabecalho)
            .on_conflict_do_update(
                index_elements=[tabela_apr.c.projeto_id],
                set_={k: v for k, v in cabecalho.items() if k != "projeto_id"},
            )
        )

        pares = apr.pares()
        s.execute(
            delete(tabela_par).where(
                tabela_par.c.projeto_id == projeto_id,
                tabela_par.c.id.notin_([p.id for p in pares]) if pares else true(),
            )
        )
        for par in pares:
            linha = {
                "id": par.id,
                "projeto_id": projeto_id,
                "obstaculo_id": par.obstaculo_id,
                "objetivo_intermediario_id": par.objetivo_intermediario_id,
            }
            s.execute(
                insert_pg(tabela_par)
                .values(**linha)
                .on_conflict_do_update(
                    index_elements=[tabela_par.c.id],
                    set_={k: v for k, v in linha.items() if k != "id"},
                )
            )
            # Os julgamentos são somente-acréscimo no agregado, e o agregado é a fonte —
            # reescrevê-los na íntegra devolve a mesma sequência, na mesma ordem.
            s.execute(delete(tabela_julgamento).where(tabela_julgamento.c.par_id == par.id))
            for julgamento in par.julgamentos:
                s.execute(
                    insert(tabela_julgamento).values(
                        id=uuid4(),
                        par_id=par.id,
                        autor=julgamento.autor,
                        valido=julgamento.valido,
                        justificativa=julgamento.justificativa,
                        instante=julgamento.instante,
                    )
                )

        elipses = apr.elipses()
        s.execute(
            delete(tabela_elipse).where(
                tabela_elipse.c.projeto_id == projeto_id,
                tabela_elipse.c.id.notin_([e.id for e in elipses]) if elipses else true(),
            )
        )
        for elipse in elipses:
            s.execute(
                insert_pg(tabela_elipse)
                .values(id=elipse.id, projeto_id=projeto_id, destino_id=elipse.destino_id)
                .on_conflict_do_update(
                    index_elements=[tabela_elipse.c.id],
                    set_={"destino_id": elipse.destino_id},
                )
            )
            s.execute(
                delete(tabela_elipse_dependencia).where(
                    tabela_elipse_dependencia.c.elipse_id == elipse.id
                )
            )
            for aresta_id in elipse.dependencias:
                s.execute(
                    insert(tabela_elipse_dependencia).values(
                        elipse_id=elipse.id, aresta_id=aresta_id
                    )
                )

    def obter_apr(self, inquilino_id: str, projeto_id: UUID) -> ProjetoAPR | None:
        projeto = self.obter(inquilino_id, projeto_id)
        if projeto is None:
            return None
        with self._sessao() as s:
            cabecalho = s.execute(
                select(tabela_apr).where(tabela_apr.c.projeto_id == projeto_id)
            ).first()
            if cabecalho is None:
                return None
            julgamentos: dict[UUID, list[JulgamentoDeValidade]] = {}
            for linha in s.execute(
                select(tabela_julgamento)
                .join(tabela_par, tabela_par.c.id == tabela_julgamento.c.par_id)
                .where(tabela_par.c.projeto_id == projeto_id)
                .order_by(tabela_julgamento.c.instante, tabela_julgamento.c.id)
            ).all():
                julgamentos.setdefault(linha.par_id, []).append(
                    JulgamentoDeValidade(
                        autor=linha.autor,
                        valido=linha.valido,
                        justificativa=linha.justificativa,
                        instante=linha.instante,
                    )
                )
            pares = tuple(
                ParObstaculoOI(
                    id=linha.id,
                    obstaculo_id=linha.obstaculo_id,
                    objetivo_intermediario_id=linha.objetivo_intermediario_id,
                    julgamentos=tuple(julgamentos.get(linha.id, ())),
                )
                for linha in s.execute(
                    select(tabela_par).where(tabela_par.c.projeto_id == projeto_id)
                ).all()
            )
            dependencias_por_elipse: dict[UUID, list[UUID]] = {}
            for linha in s.execute(
                select(tabela_elipse_dependencia)
                .join(
                    tabela_elipse,
                    tabela_elipse.c.id == tabela_elipse_dependencia.c.elipse_id,
                )
                .where(tabela_elipse.c.projeto_id == projeto_id)
            ).all():
                dependencias_por_elipse.setdefault(linha.elipse_id, []).append(
                    linha.aresta_id
                )
            elipses = tuple(
                ElipseDeSimultaneidade(
                    id=linha.id,
                    destino_id=linha.destino_id,
                    dependencias=tuple(dependencias_por_elipse.get(linha.id, ())),
                )
                for linha in s.execute(
                    select(tabela_elipse).where(tabela_elipse.c.projeto_id == projeto_id)
                ).all()
            )

        return reidratar_apr(
            projeto,
            pares=pares,
            elipses=elipses,
            origem=_para_ponta(
                cabecalho.origem_ferramenta,
                cabecalho.origem_projeto_id,
                cabecalho.origem_elementos,
                cabecalho.origem_papel,
            ),
        )

    # -- Árvore de Transição -----------------------------------------------------------

    def salvar_at(self, at: ProjetoAT) -> None:
        projeto = at.projeto
        with self._sessao.begin() as s:
            self._gravar_projeto(s, projeto)
            self._reconciliar_grafo(s, projeto)
            self._reconciliar_at(s, at)
        projeto.confirmar_gravacao()

    def _reconciliar_at(self, s, at: ProjetoAT) -> None:
        projeto_id = at.projeto.id
        alvo = at.alvo
        cabecalho = {
            "projeto_id": projeto_id,
            "alvo_ferramenta": alvo.ferramenta if alvo else None,
            "alvo_projeto_id": alvo.projeto_id if alvo else None,
            "alvo_elementos": list(alvo.elementos) if alvo else [],
            "alvo_papel": alvo.papel if alvo else "",
        }
        s.execute(
            insert_pg(tabela_at)
            .values(**cabecalho)
            .on_conflict_do_update(
                index_elements=[tabela_at.c.projeto_id],
                set_={k: v for k, v in cabecalho.items() if k != "projeto_id"},
            )
        )
        fichas = dict(at.fichas())
        s.execute(
            delete(tabela_passo).where(
                tabela_passo.c.projeto_id == projeto_id,
                tabela_passo.c.no_id.notin_(list(fichas)) if fichas else true(),
            )
        )
        for no_id, ficha in fichas.items():
            linha = {
                "no_id": no_id,
                "projeto_id": projeto_id,
                "acao": ficha.acao,
                "necessidade": ficha.necessidade,
                "resultado_esperado": ficha.resultado_esperado,
                "status": ficha.status.value,
                "motivo_do_bloqueio": ficha.motivo_do_bloqueio,
                "resultado_real": ficha.resultado_real,
            }
            s.execute(
                insert_pg(tabela_passo)
                .values(**linha)
                .on_conflict_do_update(
                    index_elements=[tabela_passo.c.no_id],
                    set_={k: v for k, v in linha.items() if k != "no_id"},
                )
            )

    def obter_at(self, inquilino_id: str, projeto_id: UUID) -> ProjetoAT | None:
        projeto = self.obter(inquilino_id, projeto_id)
        if projeto is None:
            return None
        with self._sessao() as s:
            cabecalho = s.execute(
                select(tabela_at).where(tabela_at.c.projeto_id == projeto_id)
            ).first()
            if cabecalho is None:
                return None
            fichas = {
                linha.no_id: FichaDePasso(
                    acao=linha.acao,
                    necessidade=linha.necessidade,
                    resultado_esperado=linha.resultado_esperado,
                    status=StatusDoPasso(linha.status),
                    motivo_do_bloqueio=linha.motivo_do_bloqueio,
                    resultado_real=linha.resultado_real,
                )
                for linha in s.execute(
                    select(tabela_passo).where(tabela_passo.c.projeto_id == projeto_id)
                ).all()
            }
        return reidratar_at(
            projeto,
            fichas=fichas,
            alvo=_para_ponta(
                cabecalho.alvo_ferramenta,
                cabecalho.alvo_projeto_id,
                cabecalho.alvo_elementos,
                cabecalho.alvo_papel,
            ),
        )

    # -- M6 · Focalização: a jornada dos cinco passos (spec 009) -----------------------

    def salvar_focalizacao(self, analise: AnaliseDeFocalizacao) -> None:
        """A MESMA trava otimista dos outros caminhos de escrita.

        Aqui ela protege algo que nenhuma outra ferramenta tem: a jornada é **estado
        compartilhado numa sessão de facilitação**. Duas pessoas concluindo o mesmo passo
        a partir da mesma versão gravariam duas decisões, e a reconciliação da segunda
        apagaria os vínculos que a primeira acabara de criar. `_gravar_projeto` recusa a
        segunda com `ConflitoDeVersao` e os dois números; perder a corrida é legítimo,
        perder sem saber não é.

        **Não há `_reconciliar_grafo` aqui, e a ausência é o desenho**: a análise de
        focalização não é diagrama — não tem nó nem aresta. Chamar a reconciliação de
        grafo sobre ela seria um `DELETE` sobre coleções sempre vazias.
        """
        projeto = analise.projeto
        with self._sessao.begin() as s:
            self._gravar_projeto(s, projeto)
            self._reconciliar_focalizacao(s, analise)
        projeto.confirmar_gravacao()

    def _reconciliar_focalizacao(self, s, analise: AnaliseDeFocalizacao) -> None:
        """Grava o retrato da jornada, apagando do banco só o que saiu do agregado.

        A ordem das operações é a que as chaves estrangeiras impõem, de cima para baixo:
        cabeçalho → ciclos → passos → filhos do passo (decisão, nota, reabertura,
        vínculo) → herança do ciclo. As deleções vêm antes das inserções em cada nível,
        pelo mesmo motivo do `_reconciliar_grafo`: apagar-e-reinserir tudo levaria junto,
        pela cascata, o que ninguém tocou.
        """
        projeto_id = analise.projeto.id
        cabecalho = {
            "projeto_id": projeto_id,
            "sistema_nome": analise.sistema.nome,
            "sistema_descricao": analise.sistema.descricao,
        }
        s.execute(
            insert_pg(tabela_foco)
            .values(**cabecalho)
            .on_conflict_do_update(
                index_elements=[tabela_foco.c.projeto_id],
                set_={k: v for k, v in cabecalho.items() if k != "projeto_id"},
            )
        )

        ids_de_ciclo = [c.id for c in analise.ciclos]
        s.execute(
            delete(tabela_foco_ciclo).where(
                tabela_foco_ciclo.c.projeto_id == projeto_id,
                tabela_foco_ciclo.c.id.notin_(ids_de_ciclo) if ids_de_ciclo else true(),
            )
        )
        for ciclo in analise.ciclos:
            self._gravar_ciclo(s, projeto_id, ciclo)

    def _gravar_ciclo(self, s, projeto_id: UUID, ciclo: CicloDeFocalizacao) -> None:
        linha = {
            "id": ciclo.id,
            "projeto_id": projeto_id,
            "ordem": ciclo.ordem,
            "estado": ciclo.estado.value,
            "aberto_em": ciclo.aberto_em,
            "fechado_em": ciclo.fechado_em,
        }
        s.execute(
            insert_pg(tabela_foco_ciclo)
            .values(**linha)
            .on_conflict_do_update(
                index_elements=[tabela_foco_ciclo.c.id],
                set_={k: v for k, v in linha.items() if k != "id"},
            )
        )

        # A restrição: `ciclo_id` é a chave primária — a RN-03 no banco. Sem restrição
        # registrada, a linha não existe (e não é uma linha de nulos).
        if ciclo.restricao is None:
            s.execute(
                delete(tabela_foco_restricao).where(
                    tabela_foco_restricao.c.ciclo_id == ciclo.id
                )
            )
        else:
            r = ciclo.restricao
            linha_r = {
                "ciclo_id": ciclo.id,
                "id": r.id,
                "projeto_id": projeto_id,
                "descricao": r.descricao,
                "tipo": r.tipo.value,
                "justificativa": r.justificativa,
                "autor": r.autor,
                "registrada_em": r.registrada_em,
                "origem_ferramenta": None if r.origem is None else r.origem.ferramenta,
                "origem_projeto_id": None if r.origem is None else r.origem.projeto_id,
                "origem_no_id": None if r.origem is None else r.origem.no_id,
            }
            s.execute(
                insert_pg(tabela_foco_restricao)
                .values(**linha_r)
                .on_conflict_do_update(
                    index_elements=[tabela_foco_restricao.c.ciclo_id],
                    set_={k: v for k, v in linha_r.items() if k != "ciclo_id"},
                )
            )

        for ordem, passo in enumerate(ciclo.passos, start=1):
            self._gravar_passo(s, projeto_id, ciclo.id, passo, ordem)

        ids_de_heranca = [h.id for h in ciclo.heranca]
        s.execute(
            delete(tabela_foco_heranca).where(
                tabela_foco_heranca.c.ciclo_id == ciclo.id,
                tabela_foco_heranca.c.id.notin_(ids_de_heranca)
                if ids_de_heranca
                else true(),
            )
        )
        for ordem, herdada in enumerate(ciclo.heranca):
            linha_h = {
                "id": herdada.id,
                "ciclo_id": ciclo.id,
                "projeto_id": projeto_id,
                "ciclo_de_origem": herdada.ciclo_de_origem,
                "passo": herdada.passo.value,
                "texto": herdada.texto,
                "veredito": herdada.veredito.value,
                "justificativa": herdada.justificativa,
                "autor": herdada.autor,
                "julgada_em": herdada.julgada_em,
                "ordem": ordem,
            }
            s.execute(
                insert_pg(tabela_foco_heranca)
                .values(**linha_h)
                .on_conflict_do_update(
                    index_elements=[tabela_foco_heranca.c.id],
                    set_={k: v for k, v in linha_h.items() if k != "id"},
                )
            )

    def _gravar_passo(
        self, s, projeto_id: UUID, ciclo_id: UUID, passo: PassoDeFocalizacao, ordem: int
    ) -> None:
        linha = {
            "ciclo_id": ciclo_id,
            "tipo": passo.tipo.value,
            "projeto_id": projeto_id,
            "estado": passo.estado.value,
            "ordem": ordem,
        }
        s.execute(
            insert_pg(tabela_foco_passo)
            .values(**linha)
            .on_conflict_do_update(
                index_elements=[tabela_foco_passo.c.ciclo_id, tabela_foco_passo.c.tipo],
                set_={"estado": passo.estado.value, "ordem": ordem},
            )
        )
        alvo = (
            tabela_foco_decisao.c.ciclo_id == ciclo_id,
            tabela_foco_decisao.c.passo == passo.tipo.value,
        )
        # Decisões, notas e reaberturas são SOMENTE-ACRÉSCIMO no domínio; aqui a
        # reconciliação as reinsere por identidade, e o `delete` só alcança o que saiu do
        # agregado — que, por construção, é nada.
        ids_de_decisao = [_id_da_decisao(ciclo_id, passo.tipo, i) for i in range(len(passo.decisoes))]
        s.execute(
            delete(tabela_foco_decisao).where(
                *alvo,
                tabela_foco_decisao.c.id.notin_(ids_de_decisao) if ids_de_decisao else true(),
            )
        )
        for i, decisao in enumerate(passo.decisoes):
            linha_d = {
                "id": _id_da_decisao(ciclo_id, passo.tipo, i),
                "ciclo_id": ciclo_id,
                "passo": passo.tipo.value,
                "texto": decisao.texto,
                "autor": decisao.autor,
                "instante": decisao.instante,
                "ordem": i,
            }
            s.execute(
                insert_pg(tabela_foco_decisao)
                .values(**linha_d)
                .on_conflict_do_update(
                    index_elements=[tabela_foco_decisao.c.id],
                    set_={k: v for k, v in linha_d.items() if k != "id"},
                )
            )

        ids_de_nota = [n.id for n in passo.notas]
        s.execute(
            delete(tabela_foco_nota).where(
                tabela_foco_nota.c.ciclo_id == ciclo_id,
                tabela_foco_nota.c.passo == passo.tipo.value,
                tabela_foco_nota.c.id.notin_(ids_de_nota) if ids_de_nota else true(),
            )
        )
        for nota in passo.notas:
            linha_n = {
                "id": nota.id,
                "ciclo_id": ciclo_id,
                "passo": passo.tipo.value,
                "texto": nota.texto,
                "autor": nota.autor,
                "instante": nota.instante,
            }
            s.execute(
                insert_pg(tabela_foco_nota)
                .values(**linha_n)
                .on_conflict_do_update(
                    index_elements=[tabela_foco_nota.c.id],
                    set_={k: v for k, v in linha_n.items() if k != "id"},
                )
            )

        ids_de_reabertura = [
            _id_da_reabertura(ciclo_id, passo.tipo, i) for i in range(len(passo.reaberturas))
        ]
        s.execute(
            delete(tabela_foco_reabertura).where(
                tabela_foco_reabertura.c.ciclo_id == ciclo_id,
                tabela_foco_reabertura.c.passo == passo.tipo.value,
                tabela_foco_reabertura.c.id.notin_(ids_de_reabertura)
                if ids_de_reabertura
                else true(),
            )
        )
        for i, reabertura in enumerate(passo.reaberturas):
            linha_r = {
                "id": _id_da_reabertura(ciclo_id, passo.tipo, i),
                "ciclo_id": ciclo_id,
                "passo": passo.tipo.value,
                "justificativa": reabertura.justificativa,
                "autor": reabertura.autor,
                "instante": reabertura.instante,
            }
            s.execute(
                insert_pg(tabela_foco_reabertura)
                .values(**linha_r)
                .on_conflict_do_update(
                    index_elements=[tabela_foco_reabertura.c.id],
                    set_={k: v for k, v in linha_r.items() if k != "id"},
                )
            )

        ids_de_vinculo = [v.id for v in passo.vinculos]
        s.execute(
            delete(tabela_foco_vinculo).where(
                tabela_foco_vinculo.c.ciclo_id == ciclo_id,
                tabela_foco_vinculo.c.passo == passo.tipo.value,
                tabela_foco_vinculo.c.id.notin_(ids_de_vinculo) if ids_de_vinculo else true(),
            )
        )
        for vinculo in passo.vinculos:
            linha_v = {
                "id": vinculo.id,
                "ciclo_id": ciclo_id,
                "passo": passo.tipo.value,
                "projeto_id": projeto_id,
                "ferramenta": vinculo.tipo.value,
                "alvo_projeto_id": vinculo.projeto_id,
                "papel": vinculo.papel,
                "justificativa": vinculo.justificativa,
                "canonico": vinculo.canonico,
            }
            s.execute(
                insert_pg(tabela_foco_vinculo)
                .values(**linha_v)
                .on_conflict_do_update(
                    index_elements=[tabela_foco_vinculo.c.id],
                    set_={k: v for k, v in linha_v.items() if k != "id"},
                )
            )

    def obter_focalizacao(
        self, inquilino_id: str, projeto_id: UUID
    ) -> AnaliseDeFocalizacao | None:
        projeto = self.obter(inquilino_id, projeto_id)
        if projeto is None:
            return None
        with self._sessao() as s:
            cabecalho = s.execute(
                select(tabela_foco).where(tabela_foco.c.projeto_id == projeto_id)
            ).first()
            if cabecalho is None:
                # Existe o projeto, mas ele não é uma análise de focalização. A resposta é
                # a mesma de "não existe": quem pediu pela porta errada não descobre nada.
                return None
            linhas_de_ciclo = s.execute(
                select(tabela_foco_ciclo)
                .where(tabela_foco_ciclo.c.projeto_id == projeto_id)
                .order_by(tabela_foco_ciclo.c.ordem)
            ).all()
            restricoes = {
                linha.ciclo_id: linha
                for linha in s.execute(
                    select(tabela_foco_restricao).where(
                        tabela_foco_restricao.c.projeto_id == projeto_id
                    )
                ).all()
            }
            passos = s.execute(
                select(tabela_foco_passo)
                .where(tabela_foco_passo.c.projeto_id == projeto_id)
                .order_by(tabela_foco_passo.c.ordem)
            ).all()
            decisoes = s.execute(
                select(tabela_foco_decisao)
                .where(tabela_foco_decisao.c.ciclo_id.in_([c.id for c in linhas_de_ciclo] or [None]))
                .order_by(tabela_foco_decisao.c.ordem, tabela_foco_decisao.c.instante)
            ).all()
            notas = s.execute(
                select(tabela_foco_nota)
                .where(tabela_foco_nota.c.ciclo_id.in_([c.id for c in linhas_de_ciclo] or [None]))
                .order_by(tabela_foco_nota.c.instante)
            ).all()
            reaberturas = s.execute(
                select(tabela_foco_reabertura)
                .where(
                    tabela_foco_reabertura.c.ciclo_id.in_(
                        [c.id for c in linhas_de_ciclo] or [None]
                    )
                )
                .order_by(tabela_foco_reabertura.c.instante)
            ).all()
            vinculos = s.execute(
                select(tabela_foco_vinculo)
                .where(tabela_foco_vinculo.c.projeto_id == projeto_id)
                .order_by(tabela_foco_vinculo.c.ferramenta, tabela_foco_vinculo.c.id)
            ).all()
            herancas = s.execute(
                select(tabela_foco_heranca)
                .where(tabela_foco_heranca.c.projeto_id == projeto_id)
                .order_by(tabela_foco_heranca.c.ordem)
            ).all()

        ciclos = [
            _para_ciclo(
                linha,
                restricao=restricoes.get(linha.id),
                passos=[p for p in passos if p.ciclo_id == linha.id],
                decisoes=[d for d in decisoes if d.ciclo_id == linha.id],
                notas=[n for n in notas if n.ciclo_id == linha.id],
                reaberturas=[r for r in reaberturas if r.ciclo_id == linha.id],
                vinculos=[v for v in vinculos if v.ciclo_id == linha.id],
                herancas=[h for h in herancas if h.ciclo_id == linha.id],
            )
            for linha in linhas_de_ciclo
        ]
        return reidratar_analise(
            projeto,
            sistema=SistemaAnalisado(
                nome=cabecalho.sistema_nome, descricao=cabecalho.sistema_descricao or ""
            ),
            ciclos=ciclos,
        )

    # -- referência cruzada: agregado PRÓPRIO, com trava própria (RF-33) ---------------

    def salvar_referencia(self, referencia: ReferenciaCruzada) -> None:
        with self._sessao.begin() as s:
            self._gravar_referencia(s, referencia)
        referencia.confirmar_gravacao()

    def _gravar_referencia(self, s, referencia: ReferenciaCruzada) -> None:
        """A MESMA trava otimista do `_gravar_projeto`, sobre o agregado do encadeamento.

        A referência tem versão própria porque é agregado próprio: duas pessoas podem
        suspender e reativar o mesmo vínculo, e quem partiu da versão velha tem de ser
        recusado com os dois números — nunca sobrescrever em silêncio.
        """
        linha = _referencia_para_linha(referencia)
        existe = s.execute(
            select(tabela_referencia.c.versao).where(
                tabela_referencia.c.id == referencia.id,
                tabela_referencia.c.tenant_id == referencia.dono.inquilino_id,
            )
        ).first()

        if referencia.versao_lida == 0:
            if existe is not None:
                raise ConflitoDeVersao(
                    f"referencia:{referencia.id}", versao_lida=0, versao_atual=existe.versao
                )
            s.execute(insert(tabela_referencia).values(**linha))
            return

        if existe is None:
            raise NaoEncontrado(str(referencia.id))

        resultado = s.execute(
            update(tabela_referencia)
            .where(
                tabela_referencia.c.id == referencia.id,
                tabela_referencia.c.tenant_id == referencia.dono.inquilino_id,
                tabela_referencia.c.versao == referencia.versao_lida,
            )
            .values(**{k: v for k, v in linha.items() if k != "id"})
        )
        if resultado.rowcount == 0:
            atual = s.execute(
                select(tabela_referencia.c.versao).where(
                    tabela_referencia.c.id == referencia.id,
                    tabela_referencia.c.tenant_id == referencia.dono.inquilino_id,
                )
            ).first()
            if atual is None:
                raise NaoEncontrado(str(referencia.id))
            raise ConflitoDeVersao(
                f"referencia:{referencia.id}",
                versao_lida=referencia.versao_lida,
                versao_atual=atual.versao,
            )

    def obter_referencia(
        self, inquilino_id: str, referencia_id: UUID
    ) -> ReferenciaCruzada | None:
        with self._sessao() as s:
            linha = s.execute(
                select(tabela_referencia).where(
                    tabela_referencia.c.id == referencia_id,
                    tabela_referencia.c.tenant_id == inquilino_id,
                )
            ).first()
        return _para_referencia(linha) if linha is not None else None

    def listar_referencias(
        self, inquilino_id: str, *, projeto_id: UUID | None = None
    ) -> list[ReferenciaCruzada]:
        consulta = select(tabela_referencia).where(
            tabela_referencia.c.tenant_id == inquilino_id
        )
        if projeto_id is not None:
            consulta = consulta.where(
                or_(
                    tabela_referencia.c.origem_projeto_id == projeto_id,
                    tabela_referencia.c.destino_projeto_id == projeto_id,
                )
            )
        consulta = consulta.order_by(tabela_referencia.c.criada_em, tabela_referencia.c.id)
        with self._sessao() as s:
            return [_para_referencia(linha) for linha in s.execute(consulta).all()]

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
