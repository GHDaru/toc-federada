"""M6 — a travessia dos cinco passos com estado herdado, e o recomeço que não apaga.

Siglas, uma vez neste arquivo: **M6** — Focalização · **TOC** — Teoria das Restrições ·
**ARA** — Árvore da Realidade Atual · **NC** — Nuvem de Conflito · **APR** — Árvore de
Pré-Requisitos · **AT** — Árvore de Transição · **RN/RF** — regra de negócio / requisito
funcional · **DoD** — *Definition of Done* (Definição de Pronto).

**Este é o teste que o roadmap nomeia como portão do ciclo 009** (spec 009, F-06 — os dois
portões executáveis): "teste percorre os cinco passos com estado herdado" e "recomeçar
reabre sem apagar histórico". Ele é a linha 3 e a linha 4 da tabela de aceite da spec.

Domínio puro: sem rede, sem banco, sem relógio (RNF-01). O instante entra por argumento.
"""
from __future__ import annotations

import pytest

from toc_api.dominio.eventos import CicloAberto, CicloFechado, PassoConcluido
from toc_api.dominio.focalizacao import (
    ORDEM_CANONICA,
    AnaliseDeFocalizacao,
    CicloInvalido,
    EstadoDoCiclo,
    EstadoDoPasso,
    SistemaAnalisado,
    TipoDePasso,
    TipoDeRestricao,
    mapa_da_jornada,
    nova_analise_de_focalizacao,
)

from .focalizacao_sintetica import (
    AGORA,
    AUTORA,
    CONFLITO_DE_SUBORDINACAO,
    DECISAO_DE_ELEVAR,
    DECISAO_DE_EXPLORAR,
    DECISAO_DE_SUBORDINAR,
    DESCRICAO_DO_SISTEMA,
    DONO,
    GESTORA,
    ID_DA_ANALISE,
    ID_DA_APR,
    ID_DA_ARA,
    ID_DA_AT,
    ID_DA_NC,
    ID_DO_NO_DE_CAUSA_RAIZ,
    JUSTIFICATIVA_DA_RESTRICAO,
    NOME,
    RESTRICAO,
    SISTEMA,
    depois,
)
from toc_api.dominio.focalizacao import ReferenciaDeOrigemDaRestricao


@pytest.fixture()
def analise() -> AnaliseDeFocalizacao:
    return nova_analise_de_focalizacao(
        id=ID_DA_ANALISE,
        dono=DONO,
        nome=NOME,
        sistema=SistemaAnalisado(nome=SISTEMA, descricao=DESCRICAO_DO_SISTEMA),
        em=AGORA,
    )


# ---------------------------------------------------------------------------------------
# DoD 3 — a travessia completa, cada passo lendo o produto do anterior
# ---------------------------------------------------------------------------------------


def test_a_travessia_dos_cinco_passos_com_estado_herdado(analise: AnaliseDeFocalizacao):
    """O portão do roadmap: identificar → explorar → subordinar → elevar → recomeçar.

    Cada asserção de "herdado" é o RF-13 em ato: ao abrir um passo, o que os passos
    anteriores do MESMO ciclo produziram está à vista — a restrição (de identificar) e as
    decisões já registradas. Sem isto a jornada seria cinco caixas de texto em fila.
    """
    # --- passo 1: identificar. A ferramenta do passo é a ARA (RN-06, INT-02) -----------
    assert analise.passo_atual.tipo is TipoDePasso.IDENTIFICAR
    analise.vincular_ferramenta(
        TipoDePasso.IDENTIFICAR, tipo="ara", projeto_id=ID_DA_ARA, papel="causa raiz",
        em=depois(2),
    )
    analise.registrar_restricao(
        descricao=RESTRICAO,
        tipo=TipoDeRestricao.FISICA,
        justificativa=JUSTIFICATIVA_DA_RESTRICAO,
        autor=AUTORA,
        origem=ReferenciaDeOrigemDaRestricao(
            ferramenta="ara", projeto_id=ID_DA_ARA, no_id=ID_DO_NO_DE_CAUSA_RAIZ
        ),
        em=depois(5),
    )
    mapa = mapa_da_jornada(analise)
    assert mapa.passo_atual is TipoDePasso.IDENTIFICAR
    assert mapa.restricao.descricao == RESTRICAO
    # a restrição está registrada: a única pendência que sobra é a decisão que encerra
    assert tuple(p.regra for p in mapa.de(TipoDePasso.IDENTIFICAR).pendencias) == (
        "decisao_ausente",
    )
    # o passo 1 é o primeiro: não herda nada, e o mapa diz isso em vez de mentir
    assert mapa.de(TipoDePasso.IDENTIFICAR).herdado == ()

    analise.concluir_passo(
        TipoDePasso.IDENTIFICAR,
        decisao="A restrição do fluxo é a conferência da secretaria",
        autor=AUTORA,
        em=depois(10),
    )

    # --- passo 2: explorar. Herda a restrição (RF-13) ----------------------------------
    assert analise.passo_atual.tipo is TipoDePasso.EXPLORAR
    herdado = mapa_da_jornada(analise).de(TipoDePasso.EXPLORAR).herdado
    assert any(RESTRICAO in linha for linha in herdado), herdado
    assert any("conferência da secretaria" in linha for linha in herdado), herdado

    analise.anotar_passo(
        TipoDePasso.EXPLORAR,
        texto="a secretaria gasta metade do tempo com matrículas incompletas",
        autor=AUTORA,
        em=depois(15),
    )
    analise.concluir_passo(
        TipoDePasso.EXPLORAR, decisao=DECISAO_DE_EXPLORAR, autor=AUTORA, em=depois(20)
    )

    # --- passo 3: subordinar. Herda restrição + decisão de explorar (US-08) ------------
    assert analise.passo_atual.tipo is TipoDePasso.SUBORDINAR
    herdado = mapa_da_jornada(analise).de(TipoDePasso.SUBORDINAR).herdado
    assert any(RESTRICAO in linha for linha in herdado), herdado
    assert any(DECISAO_DE_EXPLORAR in linha for linha in herdado), herdado

    # US-10: o conflito de subordinação vira NC — vínculo tipado, não texto solto
    analise.anotar_passo(
        TipoDePasso.SUBORDINAR, texto=CONFLITO_DE_SUBORDINACAO, autor=GESTORA, em=depois(25)
    )
    analise.vincular_ferramenta(
        TipoDePasso.SUBORDINAR, tipo="nc", projeto_id=ID_DA_NC, papel="conflito da regra",
        em=depois(26),
    )
    analise.concluir_passo(
        TipoDePasso.SUBORDINAR, decisao=DECISAO_DE_SUBORDINAR, autor=AUTORA, em=depois(30)
    )

    # --- passo 4: elevar. Herda os três anteriores; planeja com APR e AT (US-11) -------
    assert analise.passo_atual.tipo is TipoDePasso.ELEVAR
    herdado = mapa_da_jornada(analise).de(TipoDePasso.ELEVAR).herdado
    assert any(DECISAO_DE_SUBORDINAR in linha for linha in herdado), herdado
    # a restrição (produto de identificar) mais as decisões dos três passos anteriores
    assert len(herdado) == 4, herdado
    assert herdado[0].startswith("Restrição do ciclo:")

    analise.vincular_ferramenta(
        TipoDePasso.ELEVAR, tipo="apr", projeto_id=ID_DA_APR, papel="ampliar a secretaria",
        em=depois(35),
    )
    analise.vincular_ferramenta(
        TipoDePasso.ELEVAR, tipo="at", projeto_id=ID_DA_AT, papel="plano de contratação",
        em=depois(36),
    )
    analise.concluir_passo(
        TipoDePasso.ELEVAR, decisao=DECISAO_DE_ELEVAR, autor=AUTORA, em=depois(40)
    )

    # --- passo 5: recomeçar ------------------------------------------------------------
    assert analise.passo_atual.tipo is TipoDePasso.RECOMECAR
    mapa = mapa_da_jornada(analise)
    assert [p.estado for p in mapa.passos] == [
        EstadoDoPasso.CONCLUIDO,
        EstadoDoPasso.CONCLUIDO,
        EstadoDoPasso.CONCLUIDO,
        EstadoDoPasso.CONCLUIDO,
        EstadoDoPasso.EM_ANDAMENTO,
    ]
    assert mapa.progresso == (4, 5)
    # US-07: cada passo com a sua decisão registrada — nenhuma pendência sobrou
    assert [p.decisao for p in mapa.passos[:4]] == [
        "A restrição do fluxo é a conferência da secretaria",
        DECISAO_DE_EXPLORAR,
        DECISAO_DE_SUBORDINAR,
        DECISAO_DE_ELEVAR,
    ]
    # os vínculos do passo estão no mapa, com o tipo — a jornada aponta a ferramenta certa
    assert [v.tipo.value for v in mapa.de(TipoDePasso.IDENTIFICAR).vinculos] == ["ara"]
    assert [v.tipo.value for v in mapa.de(TipoDePasso.SUBORDINAR).vinculos] == ["nc"]
    assert [v.tipo.value for v in mapa.de(TipoDePasso.ELEVAR).vinculos] == ["apr", "at"]


def test_a_jornada_aponta_a_pendencia_de_cada_passo_sem_nunca_travar_o_mapa(
    analise: AnaliseDeFocalizacao,
):
    """RF-12: o mapa computa pendência por passo — função pura, sem mutar nada."""
    mapa = mapa_da_jornada(analise)
    regras = {p.tipo: tuple(x.regra for x in p.pendencias) for p in mapa.passos}
    assert regras[TipoDePasso.IDENTIFICAR] == ("sem_restricao", "decisao_ausente")
    assert regras[TipoDePasso.EXPLORAR] == ("decisao_ausente",)
    # RN-07: o quinto passo não tem decisão de conclusão, logo nunca pende por ela
    assert regras[TipoDePasso.RECOMECAR] == ()
    assert mapa.resumo()["pendencias"] >= 1
    # a função é pura: chamar duas vezes devolve o mesmo, e nada foi para a fila de eventos
    assert mapa_da_jornada(analise).resumo() == mapa.resumo()
    assert analise.projeto.eventos != ()  # os da criação, intocados
    assert [type(e).__name__ for e in analise.projeto.eventos] == ["AnaliseCriada", "CicloAberto"]


# ---------------------------------------------------------------------------------------
# DoD 4 — recomeçar reabre sem apagar histórico (RN-04, o portão do roadmap)
# ---------------------------------------------------------------------------------------


def test_recomeco_fecha_o_ciclo_anterior_e_abre_um_novo_em_identificar(
    analise: AnaliseDeFocalizacao,
):
    """US-12: "o ciclo atual fecha (somente leitura), um novo ciclo abre em identificar"."""
    _travessia_completa(analise)
    analise.drenar_eventos()

    analise.recomecar(em=depois(50))

    assert len(analise.ciclos) == 2
    fechado, novo = analise.ciclos
    assert fechado.estado is EstadoDoCiclo.FECHADO
    assert fechado.fechado_em == depois(50)
    assert novo.estado is EstadoDoCiclo.ABERTO
    assert novo.ordem == 2
    assert novo.restricao is None, "o ciclo novo abre SEM restrição — o passo 1 a busca"
    assert tuple(p.tipo for p in novo.passos) == ORDEM_CANONICA
    assert analise.passo_atual.tipo is TipoDePasso.IDENTIFICAR

    tipos = [type(e) for e in analise.drenar_eventos()]
    assert CicloFechado in tipos and CicloAberto in tipos


def test_recomeco_preserva_o_ciclo_anterior_intacto(analise: AnaliseDeFocalizacao):
    """RN-04: "histórico é apêndice, nunca sobrescrita".

    O retrato do ciclo é o conteúdo que as pessoas escreveram — restrição, decisões,
    notas e vínculos, passo a passo. É ELE que tem de sair do recomeço idêntico; o que
    muda, e só isso, é o ciclo de aberto para fechado e o quinto passo de em andamento
    para concluído, porque o recomeço É o ato daquele passo (RN-07).
    """
    _travessia_completa(analise)
    antes = analise.ciclo_aberto.retrato()
    estados_antes = [p.estado for p in analise.ciclo_aberto.passos]

    analise.recomecar(em=depois(50))

    fechado = analise.ciclos[0]
    assert fechado.retrato() == antes, "o conteúdo do ciclo fechado é byte a byte o mesmo"
    assert [p.estado for p in fechado.passos] == estados_antes[:4] + [EstadoDoPasso.CONCLUIDO]


def test_o_ciclo_fechado_nunca_mais_muda_nem_depois_de_dois_recomecos(
    analise: AnaliseDeFocalizacao,
):
    """A linha do tempo CRESCE, nunca encolhe — e o primeiro ciclo não se move mais."""
    _travessia_completa(analise)
    retrato_do_primeiro = None

    analise.recomecar(em=depois(50))
    retrato_do_primeiro = analise.ciclos[0].retrato()

    _travessia_completa(analise, base=100, restricao="Capacidade do laboratório de informática")
    analise.recomecar(em=depois(150))

    assert len(analise.ciclos) == 3
    assert analise.ciclos[0].retrato() == retrato_do_primeiro
    assert [c.estado for c in analise.ciclos] == [
        EstadoDoCiclo.FECHADO,
        EstadoDoCiclo.FECHADO,
        EstadoDoCiclo.ABERTO,
    ]


def test_ciclo_fechado_e_somente_leitura_no_dominio(analise: AnaliseDeFocalizacao):
    """RN-04: a imutabilidade é do domínio, não um `disabled` na tela."""
    _travessia_completa(analise)
    analise.recomecar(em=depois(50))
    fechado = analise.ciclos[0]

    with pytest.raises(CicloInvalido) as erro:
        fechado.exigir_aberto("anotar")
    assert erro.value.regra == "ciclo_fechado"


def test_recomecar_fora_do_quinto_passo_e_recusado(analise: AnaliseDeFocalizacao):
    """RN-02: "abrir ciclo novo exige fechar o atual pelo recomeço" — e só de lá."""
    analise.registrar_restricao(
        descricao=RESTRICAO,
        tipo=TipoDeRestricao.FISICA,
        justificativa=JUSTIFICATIVA_DA_RESTRICAO,
        autor=AUTORA,
        em=depois(5),
    )
    with pytest.raises(CicloInvalido) as erro:
        analise.recomecar(em=depois(6))
    assert erro.value.regra == "recomeco_fora_do_passo"
    assert len(analise.ciclos) == 1


def test_a_linha_do_tempo_conta_a_historia_da_analise(analise: AnaliseDeFocalizacao):
    """RF-17: os ciclos em ordem, com restrição, datas e desfecho."""
    _travessia_completa(analise)
    analise.recomecar(em=depois(50))
    _travessia_completa(analise, base=100, restricao="Capacidade do laboratório de informática")

    linha = analise.linha_do_tempo()
    assert [e.ordem for e in linha] == [1, 2]
    assert linha[0].restricao == RESTRICAO
    assert linha[0].estado is EstadoDoCiclo.FECHADO
    assert linha[0].fechado_em == depois(50)
    assert linha[0].decisoes == 4
    assert linha[1].restricao == "Capacidade do laboratório de informática"
    assert linha[1].estado is EstadoDoCiclo.ABERTO
    assert linha[1].fechado_em is None


# ---------------------------------------------------------------------------------------
# apoio
# ---------------------------------------------------------------------------------------


def _travessia_completa(
    analise: AnaliseDeFocalizacao, *, base: int = 0, restricao: str = RESTRICAO
) -> None:
    """Leva o ciclo aberto de `identificar` até `recomecar`, pelo caminho legítimo."""
    analise.registrar_restricao(
        descricao=restricao,
        tipo=TipoDeRestricao.FISICA,
        justificativa=JUSTIFICATIVA_DA_RESTRICAO,
        autor=AUTORA,
        em=depois(base + 5),
    )
    analise.concluir_passo(
        TipoDePasso.IDENTIFICAR,
        decisao=f"A restrição do ciclo é: {restricao}",
        autor=AUTORA,
        em=depois(base + 10),
    )
    analise.julgar_todas_as_herancas(
        veredito="mantida",
        justificativa="revisada e ainda válida para o novo alvo",
        autor=AUTORA,
        em=depois(base + 12),
    )
    analise.concluir_passo(
        TipoDePasso.EXPLORAR, decisao=DECISAO_DE_EXPLORAR, autor=AUTORA, em=depois(base + 20)
    )
    analise.concluir_passo(
        TipoDePasso.SUBORDINAR, decisao=DECISAO_DE_SUBORDINAR, autor=AUTORA, em=depois(base + 30)
    )
    analise.concluir_passo(
        TipoDePasso.ELEVAR, decisao=DECISAO_DE_ELEVAR, autor=AUTORA, em=depois(base + 40)
    )
