"""M6 — o vínculo de ferramenta como dado tipado (spec 009, RN-06; RF-14; INT-02..INT-04).

Siglas, uma vez neste arquivo: **M6** — Focalização · **TOC** — Teoria das Restrições ·
**ARA** — Árvore da Realidade Atual · **NC** — Nuvem de Conflito · **ARF** — Árvore da
Realidade Futura · **APR** — Árvore de Pré-Requisitos · **AT** — Árvore de Transição ·
**RN/RF/RNF** — regra de negócio / requisito funcional / requisito não funcional.

O que este arquivo prova, e é a linha 7 da tabela de aceite: cada passo aponta para a
ferramenta certa **por tipo**, não por texto solto na descrição. A combinação canônica
passa direto; a de fora exige justificativa e sai com **aviso, nunca bloqueio** — o mesmo
desenho de aviso não bloqueante já escolhido no M2 e no M3.

O vínculo é **opaco no domínio** (decisão 2 do plano do ciclo 009): tipo, identificador,
papel e justificativa. Existência, inquilino e estado do projeto referenciado são
verificados no servidor (RNF-04), e é por isso que esta suíte roda sem que M2, M3 e M4
existam. Domínio puro: sem rede, sem banco.
"""
from __future__ import annotations

from uuid import uuid4

import pytest

from toc_api.dominio.erros import DadoInvalido, NaoEncontrado
from toc_api.dominio.eventos import VinculoCriado, VinculoRemovido
from toc_api.dominio.focalizacao import (
    FERRAMENTAS_CANONICAS_DO_PASSO,
    AnaliseDeFocalizacao,
    SistemaAnalisado,
    TipoDeFerramentaVinculada,
    TipoDePasso,
    VinculoInvalido,
    mapa_da_jornada,
    nova_analise_de_focalizacao,
)

from .focalizacao_sintetica import (
    AGORA,
    DESCRICAO_DO_SISTEMA,
    DONO,
    ID_DA_ANALISE,
    ID_DA_APR,
    ID_DA_ARA,
    ID_DA_ARF,
    ID_DA_AT,
    ID_DA_NC,
    NOME,
    SISTEMA,
    depois,
)

JUSTIFICATIVA = (
    "a exploração desta restrição depende do plano de pré-requisitos já iniciado; o "
    "grupo decidiu olhar os dois juntos"
)


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
# RN-06 — a tabela canônica é DADO, não `if` espalhado
# ---------------------------------------------------------------------------------------


def test_as_combinacoes_canonicas_sao_as_da_regra():
    assert FERRAMENTAS_CANONICAS_DO_PASSO[TipoDePasso.IDENTIFICAR] == frozenset(
        {TipoDeFerramentaVinculada.ARA}
    )
    assert FERRAMENTAS_CANONICAS_DO_PASSO[TipoDePasso.EXPLORAR] == frozenset(
        {TipoDeFerramentaVinculada.NC, TipoDeFerramentaVinculada.ARF}
    )
    assert FERRAMENTAS_CANONICAS_DO_PASSO[TipoDePasso.SUBORDINAR] == frozenset(
        {TipoDeFerramentaVinculada.NC}
    )
    assert FERRAMENTAS_CANONICAS_DO_PASSO[TipoDePasso.ELEVAR] == frozenset(
        {TipoDeFerramentaVinculada.APR, TipoDeFerramentaVinculada.AT}
    )
    assert FERRAMENTAS_CANONICAS_DO_PASSO[TipoDePasso.RECOMECAR] == frozenset()


@pytest.mark.parametrize(
    "passo,tipo,projeto_id",
    [
        (TipoDePasso.IDENTIFICAR, "ara", ID_DA_ARA),
        (TipoDePasso.EXPLORAR, "nc", ID_DA_NC),
        (TipoDePasso.EXPLORAR, "arf", ID_DA_ARF),
        (TipoDePasso.SUBORDINAR, "nc", ID_DA_NC),
        (TipoDePasso.ELEVAR, "apr", ID_DA_APR),
        (TipoDePasso.ELEVAR, "at", ID_DA_AT),
    ],
)
def test_o_vinculo_canonico_entra_direto_sem_justificativa(
    analise: AnaliseDeFocalizacao, passo, tipo, projeto_id
):
    vinculo = analise.vincular_ferramenta(passo, tipo=tipo, projeto_id=projeto_id, em=depois(2))

    assert vinculo.canonico is True
    assert vinculo.justificativa == ""
    assert vinculo.tipo is TipoDeFerramentaVinculada(tipo)
    assert vinculo.projeto_id == projeto_id


def test_o_vinculo_fora_do_canonico_exige_justificativa(analise: AnaliseDeFocalizacao):
    with pytest.raises(VinculoInvalido) as erro:
        analise.vincular_ferramenta(
            TipoDePasso.IDENTIFICAR, tipo="apr", projeto_id=ID_DA_APR, em=depois(2)
        )
    assert erro.value.regra == "justificativa_obrigatoria"


def test_o_vinculo_fora_do_canonico_com_justificativa_entra_e_leva_aviso(
    analise: AnaliseDeFocalizacao,
):
    """RN-06: "o método educa, o dado obedece ao grupo" — aviso, nunca bloqueio."""
    vinculo = analise.vincular_ferramenta(
        TipoDePasso.EXPLORAR,
        tipo="apr",
        projeto_id=ID_DA_APR,
        justificativa=JUSTIFICATIVA,
        em=depois(2),
    )

    assert vinculo.canonico is False
    assert vinculo.justificativa == JUSTIFICATIVA
    passo = mapa_da_jornada(analise).de(TipoDePasso.EXPLORAR)
    assert len(passo.vinculos) == 1
    assert len(passo.avisos) == 1
    assert "apr" in passo.avisos[0] and "explorar" in passo.avisos[0]
    # aviso não é pendência: ele não entra na conta do que falta fazer
    assert all(p.regra != "vinculo_nao_canonico" for p in passo.pendencias)


def test_o_passo_recomecar_nao_tem_ferramenta_canonica_e_todo_vinculo_ali_avisa(
    analise: AnaliseDeFocalizacao,
):
    vinculo = analise.vincular_ferramenta(
        TipoDePasso.RECOMECAR,
        tipo="ara",
        projeto_id=ID_DA_ARA,
        justificativa="a ARA nova do próximo ciclo já começou aqui",
        em=depois(2),
    )
    assert vinculo.canonico is False


# ---------------------------------------------------------------------------------------
# RF-14 — o vínculo é referência, nunca cópia; e é único por (tipo, projeto) no passo
# ---------------------------------------------------------------------------------------


def test_o_vinculo_e_referencia_e_nao_copia(analise: AnaliseDeFocalizacao):
    """INT-02..INT-04: "o vínculo carrega identificador e leitura, nunca o dado"."""
    vinculo = analise.vincular_ferramenta(
        TipoDePasso.IDENTIFICAR, tipo="ara", projeto_id=ID_DA_ARA, papel="causa raiz",
        em=depois(2),
    )
    campos = set(vinculo.__slots__)
    assert campos == {"id", "tipo", "projeto_id", "papel", "justificativa", "canonico"}
    # Nenhum campo de CONTEÚDO do outro módulo: um título de nó, um enunciado de
    # obstáculo ou um texto de premissa aqui seria a sétima cópia que o núcleo M1 existe
    # para impedir — e envelheceria no primeiro `PUT` do módulo de origem.
    proibidos = {"titulo", "texto", "descricao", "nos", "arestas", "premissas", "conteudo"}
    assert campos & proibidos == set()


def test_o_mesmo_projeto_no_mesmo_passo_nao_vincula_duas_vezes(analise: AnaliseDeFocalizacao):
    analise.vincular_ferramenta(
        TipoDePasso.IDENTIFICAR, tipo="ara", projeto_id=ID_DA_ARA, em=depois(2)
    )
    with pytest.raises(VinculoInvalido) as erro:
        analise.vincular_ferramenta(
            TipoDePasso.IDENTIFICAR, tipo="ara", projeto_id=ID_DA_ARA, em=depois(3)
        )
    assert erro.value.regra == "vinculo_duplicado"


def test_o_mesmo_projeto_pode_ser_vinculado_a_passos_diferentes(analise: AnaliseDeFocalizacao):
    """A mesma NC serve a explorar e a subordinar — são vínculos distintos, com papéis."""
    analise.vincular_ferramenta(
        TipoDePasso.EXPLORAR, tipo="nc", projeto_id=ID_DA_NC, papel="dilema da fila",
        em=depois(2),
    )
    analise.vincular_ferramenta(
        TipoDePasso.SUBORDINAR, tipo="nc", projeto_id=ID_DA_NC, papel="conflito da regra",
        em=depois(3),
    )
    assert len(analise.vinculos_do_projeto(ID_DA_NC)) == 2


def test_tipo_de_ferramenta_desconhecido_e_recusado(analise: AnaliseDeFocalizacao):
    with pytest.raises(DadoInvalido):
        analise.vincular_ferramenta(
            TipoDePasso.IDENTIFICAR, tipo="s&t", projeto_id=ID_DA_ARA, em=depois(2)
        )


def test_vincular_e_remover_emitem_evento_com_o_tipo(analise: AnaliseDeFocalizacao):
    analise.drenar_eventos()
    vinculo = analise.vincular_ferramenta(
        TipoDePasso.IDENTIFICAR, tipo="ara", projeto_id=ID_DA_ARA, em=depois(2)
    )
    (criado,) = [e for e in analise.drenar_eventos() if isinstance(e, VinculoCriado)]
    assert criado.ferramenta == "ara"
    assert criado.passo == "identificar"
    assert criado.canonico is True

    analise.remover_vinculo(TipoDePasso.IDENTIFICAR, vinculo.id, em=depois(4))
    (removido,) = [e for e in analise.drenar_eventos() if isinstance(e, VinculoRemovido)]
    assert removido.vinculo_id == vinculo.id
    assert analise.ciclo_aberto.passo(TipoDePasso.IDENTIFICAR).vinculos == ()


def test_remover_vinculo_inexistente_e_nao_encontrado(analise: AnaliseDeFocalizacao):
    with pytest.raises(NaoEncontrado):
        analise.remover_vinculo(TipoDePasso.IDENTIFICAR, uuid4(), em=depois(4))


def test_a_navegacao_de_volta_resolve_por_consulta_ao_m6(analise: AnaliseDeFocalizacao):
    """L-03: nenhum campo novo nos módulos M2–M4; a volta é consulta sobre a análise."""
    analise.vincular_ferramenta(
        TipoDePasso.ELEVAR, tipo="apr", projeto_id=ID_DA_APR, em=depois(2)
    )
    achados = analise.vinculos_do_projeto(ID_DA_APR)
    assert len(achados) == 1
    passo, vinculo = achados[0]
    assert passo is TipoDePasso.ELEVAR
    assert vinculo.projeto_id == ID_DA_APR
    assert analise.vinculos_do_projeto(uuid4()) == ()


def test_vinculo_em_ciclo_fechado_e_recusado(analise: AnaliseDeFocalizacao):
    """RN-04: ciclo fechado é somente leitura — inclusive para vincular ferramenta."""
    from toc_api.dominio.focalizacao import CicloInvalido, TipoDeRestricao

    from .focalizacao_sintetica import AUTORA, JUSTIFICATIVA_DA_RESTRICAO, RESTRICAO

    analise.registrar_restricao(
        descricao=RESTRICAO,
        tipo=TipoDeRestricao.FISICA,
        justificativa=JUSTIFICATIVA_DA_RESTRICAO,
        autor=AUTORA,
        em=depois(5),
    )
    for passo, quando in (
        (TipoDePasso.IDENTIFICAR, 10),
        (TipoDePasso.EXPLORAR, 20),
        (TipoDePasso.SUBORDINAR, 30),
        (TipoDePasso.ELEVAR, 40),
    ):
        analise.concluir_passo(passo, decisao=f"decisão de {passo.value}", autor=AUTORA, em=depois(quando))
    analise.recomecar(em=depois(50))
    fechado = analise.ciclos[0]

    with pytest.raises(CicloInvalido) as erro:
        fechado.exigir_aberto("vincular_ferramenta")
    assert erro.value.regra == "ciclo_fechado"
