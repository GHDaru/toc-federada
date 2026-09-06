"""M6 — a inércia não pode virar a restrição (spec 009, RN-05; RF-16; US-13).

Siglas, uma vez neste arquivo: **M6** — Focalização · **TOC** — Teoria das Restrições ·
**RN/RF** — regra de negócio / requisito funcional · **DoD** — *Definition of Done*
(Definição de Pronto).

O quinto passo do método de Goldratt não é "volte ao passo 1": é "volte ao passo 1 **e não
deixe a inércia virar a restrição do sistema**". A segunda metade é a que morre em toda
implementação, porque é a metade que não tem tela óbvia. Aqui ela é **invariante de
domínio**: no recomeço, toda decisão de exploração e de subordinação do ciclo anterior
herda com veredito `pendente`, e o passo `subordinar` do novo ciclo **não conclui**
enquanto houver pendência. Manter é decisão tão explícita quanto revogar.

Esta é a linha 5 da tabela de aceite da spec. Domínio puro: sem rede, sem banco.
"""
from __future__ import annotations

import pytest

from toc_api.dominio.eventos import DecisaoHerdadaJulgada
from toc_api.dominio.focalizacao import (
    AnaliseDeFocalizacao,
    HerancaInvalida,
    PassoInvalido,
    SistemaAnalisado,
    TipoDePasso,
    TipoDeRestricao,
    VereditoDeHeranca,
    mapa_da_jornada,
    nova_analise_de_focalizacao,
)

from .focalizacao_sintetica import (
    AGORA,
    AUTORA,
    DECISAO_DE_ELEVAR,
    DECISAO_DE_EXPLORAR,
    DECISAO_DE_SUBORDINAR,
    DESCRICAO_DO_SISTEMA,
    DONO,
    ID_DA_ANALISE,
    JUSTIFICATIVA_DA_RESTRICAO,
    NOME,
    RESTRICAO,
    SISTEMA,
    depois,
)

MOTIVO = "a fila mudou de etapa; esta regra já não protege a restrição nova"


@pytest.fixture()
def recomecada() -> AnaliseDeFocalizacao:
    """Uma análise que atravessou o primeiro ciclo inteiro e recomeçou."""
    analise = nova_analise_de_focalizacao(
        id=ID_DA_ANALISE,
        dono=DONO,
        nome=NOME,
        sistema=SistemaAnalisado(nome=SISTEMA, descricao=DESCRICAO_DO_SISTEMA),
        em=AGORA,
    )
    analise.registrar_restricao(
        descricao=RESTRICAO,
        tipo=TipoDeRestricao.FISICA,
        justificativa=JUSTIFICATIVA_DA_RESTRICAO,
        autor=AUTORA,
        em=depois(5),
    )
    analise.concluir_passo(
        TipoDePasso.IDENTIFICAR, decisao="a restrição é a secretaria", autor=AUTORA, em=depois(10)
    )
    analise.concluir_passo(
        TipoDePasso.EXPLORAR, decisao=DECISAO_DE_EXPLORAR, autor=AUTORA, em=depois(20)
    )
    analise.concluir_passo(
        TipoDePasso.SUBORDINAR, decisao=DECISAO_DE_SUBORDINAR, autor=AUTORA, em=depois(30)
    )
    analise.concluir_passo(
        TipoDePasso.ELEVAR, decisao=DECISAO_DE_ELEVAR, autor=AUTORA, em=depois(40)
    )
    analise.recomecar(em=depois(50))
    analise.registrar_restricao(
        descricao="Capacidade do laboratório de informática",
        tipo=TipoDeRestricao.FISICA,
        justificativa="a fila migrou para a etapa de alocação de laboratório",
        autor=AUTORA,
        em=depois(55),
    )
    analise.concluir_passo(
        TipoDePasso.IDENTIFICAR, decisao="a restrição mudou de lugar", autor=AUTORA, em=depois(60)
    )
    return analise


# ---------------------------------------------------------------------------------------
# RF-16 — o que herda, e com que veredito
# ---------------------------------------------------------------------------------------


def test_o_recomeco_herda_as_decisoes_de_explorar_e_subordinar_com_veredito_pendente(
    recomecada: AnaliseDeFocalizacao,
):
    heranca = recomecada.ciclo_aberto.heranca
    assert [h.texto for h in heranca] == [DECISAO_DE_EXPLORAR, DECISAO_DE_SUBORDINAR]
    assert {h.veredito for h in heranca} == {VereditoDeHeranca.PENDENTE}
    assert [h.passo for h in heranca] == [TipoDePasso.EXPLORAR, TipoDePasso.SUBORDINAR]
    assert {h.ciclo_de_origem for h in heranca} == {1}


def test_a_heranca_nao_carrega_identificar_nem_elevar(recomecada: AnaliseDeFocalizacao):
    """L-02: o que sobrevive por inércia são REGRAS DE OPERAÇÃO.

    A decisão de identificar morre com o ciclo — a restrição dela já foi quebrada, e é
    justamente por isso que se recomeçou. A de elevar é um plano executado, não uma regra
    que continua valendo por conta própria.
    """
    passos = {h.passo for h in recomecada.ciclo_aberto.heranca}
    assert TipoDePasso.IDENTIFICAR not in passos
    assert TipoDePasso.ELEVAR not in passos


def test_o_mapa_da_jornada_conta_as_pendencias_de_heranca(recomecada: AnaliseDeFocalizacao):
    """RI-05: "o contador de pendências é visível do mapa da jornada"."""
    mapa = mapa_da_jornada(recomecada)
    assert mapa.herancas_pendentes == 2
    regras = tuple(p.regra for p in mapa.de(TipoDePasso.SUBORDINAR).pendencias)
    assert "heranca_pendente" in regras


# ---------------------------------------------------------------------------------------
# RN-05 — o bloqueio: subordinar não conclui com veredito pendente
# ---------------------------------------------------------------------------------------


def test_subordinar_do_novo_ciclo_nao_conclui_com_veredito_pendente(
    recomecada: AnaliseDeFocalizacao,
):
    recomecada.concluir_passo(
        TipoDePasso.EXPLORAR, decisao="explorar de novo", autor=AUTORA, em=depois(70)
    )

    with pytest.raises(PassoInvalido) as erro:
        recomecada.concluir_passo(
            TipoDePasso.SUBORDINAR, decisao="mantemos tudo", autor=AUTORA, em=depois(80)
        )
    assert erro.value.regra == "heranca_pendente"
    assert "2" in str(erro.value), "a recusa DIZ quantos vereditos faltam"
    assert recomecada.passo_atual.tipo is TipoDePasso.SUBORDINAR


def test_explorar_conclui_normalmente_o_bloqueio_e_so_de_subordinar(
    recomecada: AnaliseDeFocalizacao,
):
    """O bloqueio é cirúrgico: ele guarda o passo onde a regra de operação nasce."""
    recomecada.concluir_passo(
        TipoDePasso.EXPLORAR, decisao="explorar de novo", autor=AUTORA, em=depois(70)
    )
    assert recomecada.passo_atual.tipo is TipoDePasso.SUBORDINAR


def test_com_todos_os_vereditos_dados_subordinar_conclui(recomecada: AnaliseDeFocalizacao):
    recomecada.concluir_passo(
        TipoDePasso.EXPLORAR, decisao="explorar de novo", autor=AUTORA, em=depois(70)
    )
    for herdada in recomecada.ciclo_aberto.heranca:
        recomecada.julgar_heranca(
            herdada.id,
            veredito=VereditoDeHeranca.REVOGADA,
            justificativa=MOTIVO,
            autor=AUTORA,
            em=depois(75),
        )

    recomecada.concluir_passo(
        TipoDePasso.SUBORDINAR, decisao="subordinar ao laboratório", autor=AUTORA, em=depois(80)
    )
    assert recomecada.passo_atual.tipo is TipoDePasso.ELEVAR


# ---------------------------------------------------------------------------------------
# RN-05 — manter é decisão tão explícita quanto revogar
# ---------------------------------------------------------------------------------------


def test_manter_exige_justificativa(recomecada: AnaliseDeFocalizacao):
    herdada = recomecada.ciclo_aberto.heranca[0]
    with pytest.raises(HerancaInvalida) as erro:
        recomecada.julgar_heranca(
            herdada.id,
            veredito=VereditoDeHeranca.MANTIDA,
            justificativa="   ",
            autor=AUTORA,
            em=depois(75),
        )
    assert erro.value.regra == "justificativa_obrigatoria"


def test_revogar_exige_justificativa(recomecada: AnaliseDeFocalizacao):
    herdada = recomecada.ciclo_aberto.heranca[0]
    with pytest.raises(HerancaInvalida) as erro:
        recomecada.julgar_heranca(
            herdada.id,
            veredito=VereditoDeHeranca.REVOGADA,
            justificativa="",
            autor=AUTORA,
            em=depois(75),
        )
    assert erro.value.regra == "justificativa_obrigatoria"


def test_julgar_emite_evento_com_autor_veredito_e_motivo(recomecada: AnaliseDeFocalizacao):
    recomecada.drenar_eventos()
    herdada = recomecada.ciclo_aberto.heranca[0]

    recomecada.julgar_heranca(
        herdada.id,
        veredito=VereditoDeHeranca.MANTIDA,
        justificativa="a regra continua protegendo a nova restrição",
        autor=AUTORA,
        em=depois(75),
    )

    (evento,) = [e for e in recomecada.drenar_eventos() if isinstance(e, DecisaoHerdadaJulgada)]
    assert evento.veredito == "mantida"
    assert evento.autor == AUTORA
    assert evento.tipo_de_acao == "focalizacao.julgar_decisao_herdada"


def test_um_veredito_nunca_volta_a_pendente(recomecada: AnaliseDeFocalizacao):
    """Voltar a `pendente` apagaria um julgamento — e histórico é apêndice (RN-04)."""
    herdada = recomecada.ciclo_aberto.heranca[0]
    recomecada.julgar_heranca(
        herdada.id,
        veredito=VereditoDeHeranca.MANTIDA,
        justificativa="continua válida",
        autor=AUTORA,
        em=depois(75),
    )
    with pytest.raises(HerancaInvalida) as erro:
        recomecada.julgar_heranca(
            herdada.id,
            veredito=VereditoDeHeranca.PENDENTE,
            justificativa="deixa eu pensar",
            autor=AUTORA,
            em=depois(76),
        )
    assert erro.value.regra == "veredito_invalido"


def test_julgar_heranca_inexistente_e_recusado(recomecada: AnaliseDeFocalizacao):
    from uuid import uuid4

    from toc_api.dominio.erros import NaoEncontrado

    with pytest.raises(NaoEncontrado):
        recomecada.julgar_heranca(
            uuid4(),
            veredito=VereditoDeHeranca.MANTIDA,
            justificativa="continua válida",
            autor=AUTORA,
            em=depois(75),
        )


# ---------------------------------------------------------------------------------------
# A inércia atravessando MAIS de um ciclo — o caso que o método realmente teme
# ---------------------------------------------------------------------------------------


def test_uma_decisao_mantida_volta_a_ser_julgada_no_recomeco_seguinte(
    recomecada: AnaliseDeFocalizacao,
):
    """"Mantida" uma vez não é passe vitalício.

    Se a regra que sobreviveu ao primeiro recomeço não voltasse à mesa no segundo, ela
    atravessaria a análise inteira por decisão tomada uma vez — que é exatamente a
    definição de inércia. Por isso o recomeço herda as decisões de exploração e
    subordinação do ciclo que fecha **mais** as herdadas que aquele ciclo decidiu MANTER;
    as revogadas morrem ali, que é o que revogar quer dizer.
    """
    for herdada in recomecada.ciclo_aberto.heranca:
        recomecada.julgar_heranca(
            herdada.id,
            veredito=VereditoDeHeranca.MANTIDA,
            justificativa="continua válida no ciclo 2",
            autor=AUTORA,
            em=depois(75),
        )
    recomecada.concluir_passo(
        TipoDePasso.EXPLORAR, decisao="nova exploração", autor=AUTORA, em=depois(80)
    )
    recomecada.concluir_passo(
        TipoDePasso.SUBORDINAR, decisao="nova subordinação", autor=AUTORA, em=depois(85)
    )
    recomecada.concluir_passo(
        TipoDePasso.ELEVAR, decisao="novo plano de elevação", autor=AUTORA, em=depois(90)
    )
    recomecada.recomecar(em=depois(95))

    textos = [h.texto for h in recomecada.ciclo_aberto.heranca]
    assert "nova exploração" in textos and "nova subordinação" in textos
    assert DECISAO_DE_EXPLORAR in textos, "a mantida volta à mesa"
    assert DECISAO_DE_SUBORDINAR in textos
    assert {h.veredito for h in recomecada.ciclo_aberto.heranca} == {VereditoDeHeranca.PENDENTE}


def test_uma_decisao_revogada_nao_volta_no_recomeco_seguinte(
    recomecada: AnaliseDeFocalizacao,
):
    for herdada in recomecada.ciclo_aberto.heranca:
        recomecada.julgar_heranca(
            herdada.id,
            veredito=VereditoDeHeranca.REVOGADA,
            justificativa=MOTIVO,
            autor=AUTORA,
            em=depois(75),
        )
    recomecada.concluir_passo(
        TipoDePasso.EXPLORAR, decisao="nova exploração", autor=AUTORA, em=depois(80)
    )
    recomecada.concluir_passo(
        TipoDePasso.SUBORDINAR, decisao="nova subordinação", autor=AUTORA, em=depois(85)
    )
    recomecada.concluir_passo(
        TipoDePasso.ELEVAR, decisao="novo plano", autor=AUTORA, em=depois(90)
    )
    recomecada.recomecar(em=depois(95))

    textos = [h.texto for h in recomecada.ciclo_aberto.heranca]
    assert DECISAO_DE_EXPLORAR not in textos
    assert DECISAO_DE_SUBORDINAR not in textos
    assert sorted(textos) == ["nova exploração", "nova subordinação"]


def test_um_passo_reaberto_herda_so_a_decisao_vigente(recomecada: AnaliseDeFocalizacao):
    """RN-04 e RN-05 juntas: o histórico guarda as duas; a herança leva a que vale.

    Um passo reaberto e concluído de novo tem duas decisões no histórico — e é assim que
    tem de ser (reabrir não apaga, RF-10). Mas a regra de operação que atravessou o ciclo
    é **a última**: a anterior já foi substituída pelo próprio grupo. Herdar as duas
    mandaria à mesa de julgamento uma regra que ninguém segue mais, e pendência inútil
    treina quem lê a despachar todas sem olhar — que é exatamente como um bloqueio
    anti-inércia deixa de funcionar.
    """
    for herdada in recomecada.ciclo_aberto.heranca:
        recomecada.julgar_heranca(
            herdada.id,
            veredito=VereditoDeHeranca.REVOGADA,
            justificativa=MOTIVO,
            autor=AUTORA,
            em=depois(75),
        )
    recomecada.concluir_passo(
        TipoDePasso.EXPLORAR, decisao="primeira exploração", autor=AUTORA, em=depois(80)
    )
    recomecada.reabrir_passo_anterior(
        justificativa="a exploração estava incompleta", autor=AUTORA, em=depois(81)
    )
    recomecada.concluir_passo(
        TipoDePasso.EXPLORAR, decisao="exploração revista", autor=AUTORA, em=depois(82)
    )
    recomecada.concluir_passo(
        TipoDePasso.SUBORDINAR, decisao="nova subordinação", autor=AUTORA, em=depois(85)
    )
    recomecada.concluir_passo(
        TipoDePasso.ELEVAR, decisao="novo plano", autor=AUTORA, em=depois(90)
    )

    # o histórico do ciclo que vai fechar tem as DUAS decisões de explorar
    assert len(recomecada.ciclo_aberto.passo(TipoDePasso.EXPLORAR).decisoes) == 2

    recomecada.recomecar(em=depois(95))

    textos = [h.texto for h in recomecada.ciclo_aberto.heranca]
    assert sorted(textos) == ["exploração revista", "nova subordinação"]
    assert "primeira exploração" not in textos


def test_o_ciclo_anterior_guarda_o_veredito_que_recebeu(recomecada: AnaliseDeFocalizacao):
    """O julgamento fica no ciclo em que foi feito — é história, não estado corrente."""
    herdada = recomecada.ciclo_aberto.heranca[0]
    recomecada.julgar_heranca(
        herdada.id,
        veredito=VereditoDeHeranca.REVOGADA,
        justificativa=MOTIVO,
        autor=AUTORA,
        em=depois(75),
    )
    julgada = recomecada.ciclo_aberto.decisao_herdada(herdada.id)
    assert julgada.veredito is VereditoDeHeranca.REVOGADA
    assert julgada.justificativa == MOTIVO
    assert julgada.autor == AUTORA
