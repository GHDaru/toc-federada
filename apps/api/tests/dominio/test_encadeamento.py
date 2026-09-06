"""M4 · E4.4 — o ENCADEAMENTO: a cadeia UDE → NC → injeção → ARF → obstáculo → OI → passo.

Siglas, uma vez neste arquivo: **ARA** — Árvore da Realidade Atual · **UDE** — Efeito
Indesejável · **NC** — Nuvem de Conflito · **ARF** — Árvore da Realidade Futura · **APR**
— Árvore de Pré-Requisitos · **AT** — Árvore de Transição · **OI** — Objetivo
Intermediário · **TOC** — Teoria das Restrições · **RF/RN** — requisito funcional / regra
de negócio da spec 008.

**Este é o teste de estreia do ciclo e a aptidão do round 008**: percorrer a cadeia
inteira com dados sintéticos, provando a referência de origem em **cada elo** (DoD 1). É
também a correção do defeito D-11: nas quatro gerações da linhagem a contagem de
referências cruzadas no modelo era `0` — `grep -c
"araProjectId\\|sourceUdeId\\|linkedProject\\|crossTool" tocbuilderv3/types.ts` → `0`
(F-08 da spec 008).

As duas recusas que a RN-13 exige ("a cadeia só avança sobre material auditado") têm teste
próprio, e o nome delas carrega `recusa` — é o que o comando da DoD 3 filtra.

Base sintética (ADR 0006): "Instituição Horizonte", personas fictícias.
"""
from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID, uuid4

import pytest

from toc_api.dominio.apr import FERRAMENTA_APR, PapelNaAPR, ProjetoAPR
from toc_api.dominio.ara import (
    FERRAMENTA_ARA,
    OrigemDoParecer,
    ParecerDeJulgamento,
    ProjetoARA,
    StatusDeValidacao,
    novo_projeto_ara,
)
from toc_api.dominio.arf import FERRAMENTA_ARF, PapelNaARF, ProjetoARF
from toc_api.dominio.at import FERRAMENTA_AT, ProjetoAT, StatusDoPasso
from toc_api.dominio.encadeamento import (
    DerivacaoInvalidaDoM4,
    PromocaoInvalida,
    SemeaduraInvalida,
    derivar_apr_de_arf,
    derivar_at_de_oi,
    promover_udes_para_nc,
    semear_arf_de_injecao,
    sincronizar_referencias,
)
from toc_api.dominio.eventos import (
    ArfDerivouApr,
    InjecaoSemeouArf,
    OiDerivouAt,
    UdePromovidoParaNc,
)
from toc_api.dominio.identidade import DonoDoProjeto
from toc_api.dominio.nuvem import (
    FERRAMENTA_NC,
    ChaveDaAresta,
    NuvemDeConflito,
    StatusDeInjecao,
)
from toc_api.dominio.referencia import (
    EstadoDaReferencia,
    ReferenciaCruzada,
    TipoDeReferencia,
    travessia,
)

AGORA = datetime(2026, 9, 6, 10, 0, tzinfo=timezone.utc)
DONO = DonoDoProjeto(inquilino_id="instituicao-horizonte", usuario_id="u-facilitadora")
OUTRO_DONO = DonoDoProjeto(inquilino_id="instituicao-aurora", usuario_id="u-aurora")

UDES = (
    "A taxa de evasão no primeiro semestre é de 22%.",
    "O caixa da instituição fecha o trimestre negativo.",
)
INJECAO = "faseamento orçamentário condicionado a marco de receita"
EFEITO = "as duas frentes recebem verba no trimestre"
OBJETIVO_DA_APR = "O faseamento orçamentário está implantado nas duas frentes"
OI = "Existem três pessoas treinadas e escaladas para o acompanhamento do marco"


def parecer_humano() -> ParecerDeJulgamento:
    return ParecerDeJulgamento(
        autor="papel:facilitadora",
        origem=OrigemDoParecer.HUMANO,
        favoravel=True,
        justificativa="a queixa é contínua e está na esfera da coordenação",
        instante=AGORA,
    )


def ara_com_udes_validados(dono: DonoDoProjeto = DONO, validar: bool = True):
    """Uma ARA da Instituição Horizonte com os dois UDEs auditados (RN-13)."""
    ara = novo_projeto_ara(
        id=uuid4(), dono=dono, nome="Realidade atual da Instituição Horizonte", em=AGORA
    )
    ids = []
    for enunciado in UDES:
        no = ara.adicionar_efeito(titulo=enunciado, em=AGORA)
        ara.marcar_ude(no.id, em=AGORA)
        if validar:
            ara.registrar_parecer(no.id, parecer_humano(), em=AGORA)
            ara.mudar_status(no.id, StatusDeValidacao.VALIDADO, em=AGORA)
        ids.append(no.id)
    ara.drenar_eventos()
    return ara, tuple(ids)


# --------------------------------------------------------------------------------------
# RF-36/RF-37 — promoção UDE → NC (o INT-05 da spec 007, executado AQUI)
# --------------------------------------------------------------------------------------


def test_promover_udes_validados_cria_a_nuvem_com_referencia_tipada_nos_dois_lados() -> None:
    ara, udes = ara_com_udes_validados()

    promocao = promover_udes_para_nc(
        ara, no_ids=udes, id=uuid4(), nome="Dilema da expansão", em=AGORA
    )

    referencia = promocao.referencia
    print(
        f"referência: tipo={referencia.tipo.value} "
        f"origem={referencia.origem.ferramenta}/{referencia.origem.papel} "
        f"({len(referencia.origem.elementos)} elemento(s)) → destino={referencia.destino.ferramenta}"
    )
    assert referencia.tipo is TipoDeReferencia.PROMOCAO_UDE_NC
    assert referencia.origem.ferramenta == FERRAMENTA_ARA
    assert referencia.origem.projeto_id == ara.projeto.id
    assert referencia.origem.elementos == udes
    assert referencia.destino.ferramenta == FERRAMENTA_NC
    assert referencia.destino.projeto_id == promocao.nuvem.projeto.id
    # A projeção local de leitura do lado da NC (INT-02): a ReferenciaDeOrigem preenchida.
    assert promocao.nuvem.origem.nos == udes
    assert promocao.nuvem.leitura_da_origem().startswith("Origem: 2 Efeito")
    assert any(isinstance(e, UdePromovidoParaNc) for e in promocao.nuvem.projeto.eventos)


def test_recusa_promover_ude_que_nao_esteja_validado() -> None:
    """RF-37/RN-13: "a cadeia nasce de sintoma auditado, não de rascunho"."""
    ara, udes = ara_com_udes_validados(validar=False)

    with pytest.raises(PromocaoInvalida) as erro:
        promover_udes_para_nc(ara, no_ids=udes, id=uuid4(), nome="Dilema", em=AGORA)

    print(f"recusa: regra={erro.value.regra!r} — {erro.value}")
    assert erro.value.regra == "ude_nao_validado"


def test_recusa_promover_no_que_nao_e_ude_e_lista_vazia() -> None:
    ara, _ = ara_com_udes_validados()
    solto = ara.adicionar_efeito(titulo="A biblioteca abre às sete horas.", em=AGORA)

    with pytest.raises(PromocaoInvalida) as sem_marca:
        promover_udes_para_nc(ara, no_ids=(solto.id,), id=uuid4(), nome="Dilema", em=AGORA)
    with pytest.raises(PromocaoInvalida) as vazia:
        promover_udes_para_nc(ara, no_ids=(), id=uuid4(), nome="Dilema", em=AGORA)

    print(f"recusas: {sem_marca.value.regra} · {vazia.value.regra}")
    assert sem_marca.value.regra == "no_nao_e_ude"
    assert vazia.value.regra == "sem_ude"


def test_a_promocao_nao_muta_a_ara_de_origem() -> None:
    ara, udes = ara_com_udes_validados()
    antes = (len(ara.nos), len(ara.arestas), ara.projeto.versao)

    promover_udes_para_nc(ara, no_ids=udes, id=uuid4(), nome="Dilema", em=AGORA)

    print(f"ARA antes={antes} depois={(len(ara.nos), len(ara.arestas), ara.projeto.versao)}")
    assert (len(ara.nos), len(ara.arestas), ara.projeto.versao) == antes
    assert ara.projeto.eventos == ()


def test_o_dono_da_nuvem_vem_do_agregado_de_origem_e_nunca_do_chamador() -> None:
    ara, udes = ara_com_udes_validados(dono=OUTRO_DONO)
    promocao = promover_udes_para_nc(ara, no_ids=udes, id=uuid4(), nome="Dilema", em=AGORA)
    assert promocao.nuvem.projeto.dono == OUTRO_DONO
    assert promocao.referencia.dono == OUTRO_DONO


# --------------------------------------------------------------------------------------
# RF-38 — semeadura injeção → ARF (o INT-06 da spec 007, executado AQUI)
# --------------------------------------------------------------------------------------


def nuvem_com_injecao_escolhida(ara=None, udes=()) -> tuple[NuvemDeConflito, UUID]:
    if ara is None:
        ara, udes = ara_com_udes_validados()
    nuvem = promover_udes_para_nc(
        ara, no_ids=udes, id=uuid4(), nome="Dilema da expansão", em=AGORA
    ).nuvem
    premissa = nuvem.registrar_premissa(
        ChaveDaAresta.D_D_PRIME, "o orçamento é indivisível dentro do exercício", em=AGORA
    )
    injecao = nuvem.registrar_injecao(premissa.id, INJECAO, em=AGORA)
    nuvem.mudar_status_de_injecao(injecao.id, StatusDeInjecao.ESCOLHIDA, em=AGORA)
    nuvem.drenar_eventos()
    return nuvem, injecao.id


def test_semear_a_arf_a_partir_da_injecao_escolhida_cria_o_no_semente() -> None:
    """RF-06/RF-38: a ARF nasce do compromisso do grupo, não de uma folha em branco."""
    nuvem, injecao_id = nuvem_com_injecao_escolhida()

    semeadura = semear_arf_de_injecao(
        nuvem, injecao_id=injecao_id, id=uuid4(), nome="Futuro da expansão", em=AGORA
    )

    arf = semeadura.arf
    semente = arf.injecoes[0]
    print(
        f"ARF semeada: nó semente={semente.titulo!r} papel={arf.papel_do_no(semente.id).value} "
        f"udes_da_cadeia={len(arf.udes_da_cadeia)}"
    )
    assert arf.projeto.ferramenta == FERRAMENTA_ARF
    assert semente.titulo == INJECAO
    assert arf.papel_do_no(semente.id) is PapelNaARF.INJECAO
    # A cadeia chega inteira: os UDEs da ARA de origem viajam com ela (RN-03).
    assert len(arf.udes_da_cadeia) == 2
    assert semeadura.referencia.tipo is TipoDeReferencia.SEMEADURA_INJECAO_ARF
    assert semeadura.referencia.origem.elementos == (injecao_id,)


def test_a_semeadura_preenche_a_referencia_de_semeadura_da_nuvem() -> None:
    """INT-03/INT-06: o campo que o ciclo 007 criou vazio é preenchido aqui."""
    nuvem, injecao_id = nuvem_com_injecao_escolhida()
    assert nuvem.injecao(injecao_id).semeadura.projeto_destino_id is None

    semeadura = semear_arf_de_injecao(
        nuvem, injecao_id=injecao_id, id=uuid4(), nome="Futuro", em=AGORA
    )

    destino = nuvem.injecao(injecao_id).semeadura.projeto_destino_id
    print(f"ReferenciaDeSemeadura.projeto_destino_id = {destino}")
    assert destino == semeadura.arf.projeto.id
    assert any(isinstance(e, InjecaoSemeouArf) for e in nuvem.projeto.eventos)


def test_recusa_semear_a_partir_de_injecao_candidata_ou_descartada() -> None:
    """RF-38/RN-13: "injeção `candidata` ou `descartada` não semeia"."""
    nuvem, injecao_id = nuvem_com_injecao_escolhida()
    nuvem.mudar_status_de_injecao(
        injecao_id, StatusDeInjecao.CANDIDATA, justificativa="o grupo reabriu", em=AGORA
    )

    with pytest.raises(SemeaduraInvalida) as erro:
        semear_arf_de_injecao(nuvem, injecao_id=injecao_id, id=uuid4(), nome="Futuro", em=AGORA)

    print(f"recusa: regra={erro.value.regra!r} — {erro.value}")
    assert erro.value.regra == "injecao_nao_escolhida"


def test_recusa_semear_duas_arf_da_mesma_injecao() -> None:
    nuvem, injecao_id = nuvem_com_injecao_escolhida()
    semear_arf_de_injecao(nuvem, injecao_id=injecao_id, id=uuid4(), nome="Futuro", em=AGORA)

    with pytest.raises(SemeaduraInvalida) as erro:
        semear_arf_de_injecao(
            nuvem, injecao_id=injecao_id, id=uuid4(), nome="Outro futuro", em=AGORA
        )
    assert erro.value.regra == "injecao_ja_semeou"


# --------------------------------------------------------------------------------------
# RF-39/RF-40 — derivações ARF → APR e OI → AT
# --------------------------------------------------------------------------------------


def arf_verificada() -> tuple[ProjetoARF, UUID, NuvemDeConflito]:
    nuvem, injecao_id = nuvem_com_injecao_escolhida()
    arf = semear_arf_de_injecao(
        nuvem, injecao_id=injecao_id, id=uuid4(), nome="Futuro da expansão", em=AGORA
    ).arf
    semente = arf.injecoes[0]
    efeito = arf.adicionar_efeito_futuro(titulo=EFEITO, em=AGORA)
    arf.ligar(semente.id, efeito.id, em=AGORA)
    arf.espelhar_ude(efeito.id, arf.udes_da_cadeia[0], em=AGORA)
    arf.drenar_eventos()
    return arf, efeito.id, nuvem


def test_derivar_a_apr_da_arf_propoe_o_objetivo_a_partir_do_texto_escolhido() -> None:
    arf, efeito_id, _ = arf_verificada()

    derivacao = derivar_apr_de_arf(arf, no_id=efeito_id, id=uuid4(), nome="Implantação", em=AGORA)

    apr = derivacao.apr
    print(f"objetivo proposto: {apr.objetivo.titulo!r}")
    assert apr.projeto.ferramenta == FERRAMENTA_APR
    assert EFEITO in apr.objetivo.titulo
    assert derivacao.referencia.tipo is TipoDeReferencia.DERIVACAO_ARF_APR
    assert derivacao.referencia.origem.elementos == (efeito_id,)
    assert any(isinstance(e, ArfDerivouApr) for e in arf.projeto.eventos)


def test_o_objetivo_proposto_e_editavel_sem_quebrar_a_referencia() -> None:
    arf, efeito_id, _ = arf_verificada()
    derivacao = derivar_apr_de_arf(arf, no_id=efeito_id, id=uuid4(), nome="Implantação", em=AGORA)

    derivacao.apr.editar_objetivo(OBJETIVO_DA_APR, em=AGORA)

    assert derivacao.apr.objetivo.titulo == OBJETIVO_DA_APR
    assert derivacao.referencia.estado is EstadoDaReferencia.ATIVA
    assert derivacao.referencia.destino.projeto_id == derivacao.apr.projeto.id


def test_derivar_a_at_de_um_objetivo_intermediario_registra_o_alvo() -> None:
    arf, efeito_id, _ = arf_verificada()
    apr = derivar_apr_de_arf(arf, no_id=efeito_id, id=uuid4(), nome="Implantação", em=AGORA).apr
    oi = apr.adicionar_objetivo_intermediario(titulo=OI, em=AGORA)
    apr.drenar_eventos()

    derivacao = derivar_at_de_oi(apr, no_id=oi.id, id=uuid4(), nome="Transição", em=AGORA)

    at = derivacao.at
    print(f"AT derivada: alvo={at.alvo.ferramenta}/{at.alvo.papel} elementos={len(at.alvo.elementos)}")
    assert at.projeto.ferramenta == FERRAMENTA_AT
    assert at.alvo.projeto_id == apr.projeto.id
    assert at.alvo.elementos == (oi.id,)
    assert derivacao.referencia.tipo is TipoDeReferencia.DERIVACAO_OI_AT
    assert any(isinstance(e, OiDerivouAt) for e in apr.projeto.eventos)


def test_recusa_derivar_at_de_um_obstaculo() -> None:
    arf, efeito_id, _ = arf_verificada()
    apr = derivar_apr_de_arf(arf, no_id=efeito_id, id=uuid4(), nome="Implantação", em=AGORA).apr
    obstaculo = apr.adicionar_obstaculo(
        titulo="Há apenas uma pessoa treinada no acompanhamento", em=AGORA
    )

    with pytest.raises(DerivacaoInvalidaDoM4) as erro:
        derivar_at_de_oi(apr, no_id=obstaculo.id, id=uuid4(), nome="Transição", em=AGORA)

    print(f"recusa: regra={erro.value.regra!r}")
    assert erro.value.regra == "alvo_nao_e_objetivo"


def test_recusa_derivar_apr_de_projeto_excluido() -> None:
    arf, efeito_id, _ = arf_verificada()
    arf.projeto.excluir(em=AGORA)
    with pytest.raises(DerivacaoInvalidaDoM4) as erro:
        derivar_apr_de_arf(arf, no_id=efeito_id, id=uuid4(), nome="Implantação", em=AGORA)
    assert erro.value.regra == "origem_excluida"


# --------------------------------------------------------------------------------------
# DoD 1 — a CADEIA COMPLETA, com a referência de origem provada em cada elo
# --------------------------------------------------------------------------------------


def test_cadeia_completa_do_ude_ao_passo_com_referencia_em_cada_elo() -> None:
    """A aptidão executável do round 008 — e a correção do defeito D-11.

    Percorre a análise sintética inteira da Instituição Horizonte e prova, elo a elo, que
    a referência de origem existe, é tipada e aponta para o elemento certo. Na 4ª geração
    da linhagem esta contagem era `0`.
    """
    # 1 · ARA — dois Efeitos Indesejáveis auditados
    ara, udes = ara_com_udes_validados()

    # 2 · promoção UDE → NC
    promocao = promover_udes_para_nc(
        ara, no_ids=udes, id=uuid4(), nome="Dilema da expansão", em=AGORA
    )
    nuvem = promocao.nuvem
    premissa = nuvem.registrar_premissa(
        ChaveDaAresta.D_D_PRIME, "o orçamento é indivisível dentro do exercício", em=AGORA
    )
    injecao = nuvem.registrar_injecao(premissa.id, INJECAO, em=AGORA)
    nuvem.mudar_status_de_injecao(injecao.id, StatusDeInjecao.ESCOLHIDA, em=AGORA)

    # 3 · semeadura injeção → ARF, com ramo negativo tratado
    semeadura = semear_arf_de_injecao(
        nuvem, injecao_id=injecao.id, id=uuid4(), nome="Futuro da expansão", em=AGORA
    )
    arf = semeadura.arf
    semente = arf.injecoes[0]
    efeito = arf.adicionar_efeito_futuro(titulo=EFEITO, em=AGORA)
    arf.ligar(semente.id, efeito.id, em=AGORA)
    arf.espelhar_ude(efeito.id, udes[0], em=AGORA)
    colateral = arf.adicionar_efeito_futuro(
        titulo="a equipe da Secretaria acumula dupla jornada", em=AGORA
    )
    arf.ligar(semente.id, colateral.id, em=AGORA)
    corte = arf.adicionar_injecao(titulo="contratação temporária no pico", em=AGORA)
    ramo = arf.marcar_ramo_negativo(colateral.id, em=AGORA)
    arf.tratar_ramo(ramo.id, injecao_id=corte.id, em=AGORA)

    # 4 · derivação ARF → APR, com obstáculo pareado e sequenciado
    derivacao_apr = derivar_apr_de_arf(
        arf, no_id=efeito.id, id=uuid4(), nome="Implantação do faseamento", em=AGORA
    )
    apr = derivacao_apr.apr
    apr.editar_objetivo(OBJETIVO_DA_APR, em=AGORA)
    obstaculo = apr.adicionar_obstaculo(
        titulo="Há apenas uma pessoa treinada no acompanhamento do marco", em=AGORA
    )
    oi = apr.adicionar_objetivo_intermediario(titulo=OI, em=AGORA)
    par = apr.parear(obstaculo.id, oi.id, em=AGORA)
    apr.julgar_par(
        par.id,
        autor="Facilitadora TOC",
        valido=True,
        justificativa="com três pessoas escaladas o acompanhamento não depende de uma só",
        em=AGORA,
    )
    apr.depender(oi.id, apr.objetivo.id, em=AGORA)

    # 5 · derivação OI → AT, com o primeiro passo concluído
    derivacao_at = derivar_at_de_oi(apr, no_id=oi.id, id=uuid4(), nome="Transição do OI", em=AGORA)
    at = derivacao_at.at
    primeiro = at.registrar_passo(
        acao="publicar a chamada interna de treinamento",
        necessidade="não há hoje candidato mapeado",
        resultado_esperado="lista de inscritos até sexta",
        em=AGORA,
    )
    at.mudar_status(
        primeiro.id, StatusDoPasso.CONCLUIDO, resultado_real="lista de inscritos até sexta", em=AGORA
    )

    # -- a cadeia, percorrida de uma ponta à outra ------------------------------------
    referencias = (
        promocao.referencia,
        semeadura.referencia,
        derivacao_apr.referencia,
        derivacao_at.referencia,
    )
    cadeia = travessia(referencias, projeto_id=arf.projeto.id)

    esperados = (
        (TipoDeReferencia.PROMOCAO_UDE_NC, FERRAMENTA_ARA, FERRAMENTA_NC, "ude"),
        (TipoDeReferencia.SEMEADURA_INJECAO_ARF, FERRAMENTA_NC, FERRAMENTA_ARF, "injecao"),
        (TipoDeReferencia.DERIVACAO_ARF_APR, FERRAMENTA_ARF, FERRAMENTA_APR, "efeito_futuro"),
        (TipoDeReferencia.DERIVACAO_OI_AT, FERRAMENTA_APR, FERRAMENTA_AT, "objetivo_intermediario"),
    )
    print(f"cadeia: {' → '.join(cadeia.ferramentas())} · resumo={cadeia.resumo()}")
    assert len(cadeia.elos) == 4
    for elo, (tipo, origem, destino, papel) in zip(cadeia.elos, esperados):
        print(
            f"  elo {tipo.value}: {origem}/{papel} ({len(elo.origem.elementos)} elemento) "
            f"→ {destino} · estado={elo.estado.value}"
        )
        assert elo.tipo is tipo
        assert elo.origem.ferramenta == origem
        assert elo.destino.ferramenta == destino
        assert elo.origem.papel == papel
        assert elo.origem.elementos, "elo sem elemento de origem não prova nada"
        assert elo.estado is EstadoDaReferencia.ATIVA

    assert cadeia.ferramentas() == (
        FERRAMENTA_ARA, FERRAMENTA_NC, FERRAMENTA_ARF, FERRAMENTA_APR, FERRAMENTA_AT
    )
    # E os dois sentidos: partindo da AT, a mesma cadeia.
    assert travessia(referencias, projeto_id=at.projeto.id).elos == cadeia.elos

    # O estado das cinco ferramentas no fim da travessia — a jornada em números.
    print(
        f"estado final: UDEs validados={len([u for u in udes if ara.status(u) is StatusDeValidacao.VALIDADO])} · "
        f"injeção escolhida={nuvem.injecao(injecao.id).status.value} · "
        f"ARF: {arf.verificar().resumo()} · "
        f"APR: {apr.sequenciar().resumo()} · "
        f"AT: {at.resumo_de_execucao()}"
    )
    assert arf.verificar().resumo()["ramos_negativos_abertos"] == 0
    assert apr.sequenciar().completo is True
    assert at.resumo_de_execucao()["concluido"] == 1


# --------------------------------------------------------------------------------------
# RN-12 / RNF-09 — a exclusão suave suspende, a restauração reativa
# --------------------------------------------------------------------------------------


def test_a_exclusao_suave_de_uma_ponta_suspende_as_referencias_que_a_tocam() -> None:
    ara, udes = ara_com_udes_validados()
    promocao = promover_udes_para_nc(ara, no_ids=udes, id=uuid4(), nome="Dilema", em=AGORA)
    referencias = [promocao.referencia]

    mudadas = sincronizar_referencias(
        referencias,
        projeto_id=promocao.nuvem.projeto.id,
        excluido=True,
        motivo="projeto excluído",
        em=AGORA,
    )

    print(f"referências suspensas: {len(mudadas)}")
    assert len(mudadas) == 1
    assert referencias[0].estado is EstadoDaReferencia.PENDENTE

    de_volta = sincronizar_referencias(
        referencias, projeto_id=promocao.nuvem.projeto.id, excluido=False, em=AGORA
    )
    assert len(de_volta) == 1
    assert referencias[0].estado is EstadoDaReferencia.ATIVA


def test_sincronizar_e_idempotente_e_nao_apaga_referencia_nenhuma() -> None:
    """RN-12: "nenhuma operação do módulo apaga referência como efeito colateral"."""
    ara, udes = ara_com_udes_validados()
    promocao = promover_udes_para_nc(ara, no_ids=udes, id=uuid4(), nome="Dilema", em=AGORA)
    referencias = [promocao.referencia]

    primeira = sincronizar_referencias(
        referencias, projeto_id=ara.projeto.id, excluido=True, motivo="excluído", em=AGORA
    )
    segunda = sincronizar_referencias(
        referencias, projeto_id=ara.projeto.id, excluido=True, motivo="excluído", em=AGORA
    )

    print(f"primeira passada={len(primeira)} · segunda passada={len(segunda)}")
    assert len(primeira) == 1 and segunda == ()
    assert len(referencias) == 1
