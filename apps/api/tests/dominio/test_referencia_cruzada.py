"""M4 · E4.4 — a referência cruzada como cidadã do modelo, e a vista da cadeia.

Siglas, uma vez neste arquivo: **ARA** — Árvore da Realidade Atual · **UDE** — Efeito
Indesejável · **NC** — Nuvem de Conflito · **ARF** — Árvore da Realidade Futura · **APR**
— Árvore de Pré-Requisitos · **AT** — Árvore de Transição · **OI** — Objetivo
Intermediário · **RN/RF/RNF** — regra de negócio / requisito funcional / requisito não
funcional da spec 008.

**O defeito que este agregado corrige tem número: D-11.** Na 4ª geração da linhagem não
existia uma referência entre projetos — a contagem colada na spec é
`grep -c "araProjectId\\|sourceUdeId\\|linkedProject\\|crossTool" tocbuilderv3/types.ts` →
`0`. Cada ferramenta era uma ilha, e a intenção de encadeá-las existia só na navegação
(`Sidebar.tsx:86`, que desabilitava ARF/APR/AT sem projeto ARA carregado).

Três regras mandam neste arquivo, e cada uma tem teste que falha sem ela:

- **RN-11**: a referência nasce SOMENTE por ação nomeada. Não há construtor anônimo.
- **RN-12**: exclusão suave de qualquer ponta **suspende** (`pendente`); restaurar
  **reativa**; nada apaga referência por efeito colateral.
- **RNF-09**: teste de propriedade — qualquer sequência de exclusões e restaurações
  termina com toda referência `ativa` ou `pendente`, nunca apontando para o vazio em
  silêncio.
"""
from __future__ import annotations

import itertools
from datetime import datetime, timezone
from uuid import UUID, uuid4

import pytest

from toc_api.dominio.erros import ConflitoDeVersao
from toc_api.dominio.eventos import (
    ReferenciaCriada,
    ReferenciaReativada,
    ReferenciaSuspensa,
)
from toc_api.dominio.identidade import DonoDoProjeto
from toc_api.dominio.referencia import (
    EstadoDaReferencia,
    Ponta,
    ReferenciaCruzada,
    ReferenciaInvalida,
    TipoDeReferencia,
    reidratar_referencia,
    travessia,
)

AGORA = datetime(2026, 9, 6, 10, 0, tzinfo=timezone.utc)
DONO = DonoDoProjeto(inquilino_id="instituicao-horizonte", usuario_id="u-facilitadora")

ARA = UUID("55555555-5555-4555-8555-555555555551")
NC = UUID("66666666-6666-4666-8666-666666666661")
ARF = UUID("44444444-4444-4444-8444-444444444401")
APR = UUID("33333333-3333-4333-8333-333333333301")
AT = UUID("22222222-2222-4222-8222-222222222201")


def _ref(tipo: TipoDeReferencia, origem: Ponta, destino: Ponta) -> ReferenciaCruzada:
    return ReferenciaCruzada.nomeada(
        id=uuid4(), tipo=tipo, origem=origem, destino=destino, dono=DONO, em=AGORA
    )


def cadeia_completa() -> tuple[ReferenciaCruzada, ...]:
    """A análise sintética inteira da Instituição Horizonte, em quatro referências."""
    ude, injecao, efeito, oi = uuid4(), uuid4(), uuid4(), uuid4()
    return (
        _ref(
            TipoDeReferencia.PROMOCAO_UDE_NC,
            Ponta(ferramenta="ara", projeto_id=ARA, elementos=(ude,), papel="ude"),
            Ponta(ferramenta="nc", projeto_id=NC),
        ),
        _ref(
            TipoDeReferencia.SEMEADURA_INJECAO_ARF,
            Ponta(ferramenta="nc", projeto_id=NC, elementos=(injecao,), papel="injecao"),
            Ponta(ferramenta="arf", projeto_id=ARF),
        ),
        _ref(
            TipoDeReferencia.DERIVACAO_ARF_APR,
            Ponta(ferramenta="arf", projeto_id=ARF, elementos=(efeito,), papel="efeito_futuro"),
            Ponta(ferramenta="apr", projeto_id=APR),
        ),
        _ref(
            TipoDeReferencia.DERIVACAO_OI_AT,
            Ponta(
                ferramenta="apr",
                projeto_id=APR,
                elementos=(oi,),
                papel="objetivo_intermediario",
            ),
            Ponta(ferramenta="at", projeto_id=AT),
        ),
    )


# --------------------------------------------------------------------------------------
# RN-11 — nasce somente por ação nomeada
# --------------------------------------------------------------------------------------


def test_a_referencia_nao_tem_construtor_anonimo() -> None:
    """RN-11: "nunca por inferência silenciosa de sistema ou modelo"."""
    with pytest.raises(ReferenciaInvalida) as erro:
        ReferenciaCruzada(
            id=uuid4(),
            tipo=TipoDeReferencia.PROMOCAO_UDE_NC,
            origem=Ponta(ferramenta="ara", projeto_id=ARA),
            destino=Ponta(ferramenta="nc", projeto_id=NC),
            dono=DONO,
            criada_em=AGORA,
        )
    print(f"recusa: regra={erro.value.regra!r}")
    assert erro.value.regra == "sem_acao_nomeada"


def test_a_acao_nomeada_cria_a_referencia_ativa_e_emite_o_evento() -> None:
    referencia = _ref(
        TipoDeReferencia.PROMOCAO_UDE_NC,
        Ponta(ferramenta="ara", projeto_id=ARA, elementos=(uuid4(),), papel="ude"),
        Ponta(ferramenta="nc", projeto_id=NC),
    )
    evento = referencia.eventos[-1]
    print(f"estado={referencia.estado.value} evento={type(evento).__name__}")
    assert referencia.estado is EstadoDaReferencia.ATIVA
    assert isinstance(evento, ReferenciaCriada)
    assert evento.tipo == TipoDeReferencia.PROMOCAO_UDE_NC.value
    assert evento.origem_projeto_id == ARA and evento.destino_projeto_id == NC


def test_ponta_sem_ferramenta_ou_sem_projeto_nao_existe() -> None:
    with pytest.raises(Exception):
        Ponta(ferramenta="  ", projeto_id=ARA)


# --------------------------------------------------------------------------------------
# RN-12 — suspende e reativa; nunca apaga por efeito colateral
# --------------------------------------------------------------------------------------


def test_exclusao_suave_de_uma_ponta_suspende_a_referencia_com_o_motivo() -> None:
    referencia = cadeia_completa()[0]
    referencia.drenar_eventos()

    referencia.suspender(motivo=f"projeto {ARA} excluído", em=AGORA)

    print(f"estado={referencia.estado.value} motivo={referencia.motivo!r}")
    assert referencia.estado is EstadoDaReferencia.PENDENTE
    assert str(ARA) in referencia.motivo
    assert isinstance(referencia.eventos[-1], ReferenciaSuspensa)


def test_restaurar_reativa_e_limpa_o_motivo() -> None:
    referencia = cadeia_completa()[0]
    referencia.suspender(motivo="projeto excluído", em=AGORA)
    referencia.drenar_eventos()

    referencia.reativar(em=AGORA)

    assert referencia.estado is EstadoDaReferencia.ATIVA
    assert referencia.motivo == ""
    assert isinstance(referencia.eventos[-1], ReferenciaReativada)


def test_suspender_duas_vezes_e_recusado_sem_mudanca() -> None:
    referencia = cadeia_completa()[0]
    referencia.suspender(motivo="projeto excluído", em=AGORA)
    with pytest.raises(ReferenciaInvalida) as erro:
        referencia.suspender(motivo="de novo", em=AGORA)
    assert erro.value.regra == "sem_mudanca"


def test_suspender_exige_motivo() -> None:
    """Suspender sem dizer por quê devolve o silêncio que a RN-12 existe para acabar."""
    referencia = cadeia_completa()[0]
    with pytest.raises(ReferenciaInvalida) as erro:
        referencia.suspender(motivo="   ", em=AGORA)
    assert erro.value.regra == "motivo_obrigatorio"


def test_a_referencia_nasce_com_a_trava_otimista_do_agregado() -> None:
    """Agregado próprio, e por isso trava própria: `versao_lida` e `confirmar_gravacao`."""
    referencia = cadeia_completa()[0]
    print(f"versao={referencia.versao} versao_lida={referencia.versao_lida}")
    assert referencia.versao == 1
    assert referencia.versao_lida == 0

    referencia.confirmar_gravacao()
    assert referencia.versao_lida == 1

    referencia.suspender(motivo="projeto excluído", em=AGORA)
    assert referencia.versao == 2 and referencia.versao_lida == 1


def test_o_conflito_de_versao_da_referencia_carrega_os_dois_numeros() -> None:
    erro = ConflitoDeVersao("referencia:x", versao_lida=1, versao_atual=3)
    assert (erro.versao_lida, erro.versao_atual) == (1, 3)


# --------------------------------------------------------------------------------------
# RNF-09 — propriedade: qualquer sequência termina em `ativa` ou `pendente`
# --------------------------------------------------------------------------------------


def test_propriedade_toda_sequencia_de_exclusoes_e_restauracoes_termina_com_estado_dito() -> None:
    """RNF-09: nunca apontando para elemento inexistente **sem estado que o diga**.

    A propriedade é exercida sobre todas as sequências de até 4 eventos de exclusão e
    restauração das duas pontas — 2⁴ ordens × 2 pontas. O que se prova não é uma execução
    feliz: é que **nenhuma** ordem produz uma referência que se diga ativa enquanto uma
    ponta está excluída, e nenhuma some do conjunto.
    """
    combinacoes = 0
    for tamanho in range(1, 5):
        for sequencia in itertools.product(["excluir_a", "excluir_b", "restaurar"], repeat=tamanho):
            referencia = cadeia_completa()[0]
            excluidos: set[str] = set()
            for passo in sequencia:
                if passo == "restaurar":
                    excluidos.clear()
                else:
                    excluidos.add(passo)
                deveria = EstadoDaReferencia.PENDENTE if excluidos else EstadoDaReferencia.ATIVA
                if referencia.estado is not deveria:
                    if deveria is EstadoDaReferencia.PENDENTE:
                        referencia.suspender(motivo=f"ponta {sorted(excluidos)} excluída", em=AGORA)
                    else:
                        referencia.reativar(em=AGORA)
                assert referencia.estado in tuple(EstadoDaReferencia)
                assert referencia.estado is deveria
                if referencia.estado is EstadoDaReferencia.PENDENTE:
                    assert referencia.motivo, "pendente sem motivo é o silêncio que a RN-12 proíbe"
            combinacoes += 1
    print(f"sequências de exclusão/restauração exercidas: {combinacoes}")
    assert combinacoes == 3 + 9 + 27 + 81


# --------------------------------------------------------------------------------------
# RF-41 — a vista da cadeia: função pura sobre as referências, nos dois sentidos
# --------------------------------------------------------------------------------------


def test_a_travessia_percorre_do_ude_ao_passo_a_partir_de_qualquer_ponto() -> None:
    referencias = cadeia_completa()

    do_meio = travessia(referencias, projeto_id=ARF)

    ferramentas = do_meio.ferramentas()
    print(f"cadeia a partir da ARF: {' → '.join(ferramentas)}")
    assert ferramentas == ("ara", "nc", "arf", "apr", "at")
    assert len(do_meio.elos) == 4
    assert do_meio.elos[0].tipo is TipoDeReferencia.PROMOCAO_UDE_NC
    assert do_meio.elos[-1].tipo is TipoDeReferencia.DERIVACAO_OI_AT


def test_a_travessia_da_ponta_final_devolve_a_mesma_cadeia() -> None:
    referencias = cadeia_completa()
    assert travessia(referencias, projeto_id=AT).ferramentas() == (
        travessia(referencias, projeto_id=ARA).ferramentas()
    )


def test_elo_com_ponta_excluida_aparece_pendente_e_nunca_some_em_silencio() -> None:
    """RF-35/US-18: "um elo com ponta excluída aparece `pendente` (nunca some em silêncio)"."""
    referencias = list(cadeia_completa())
    referencias[2].suspender(motivo=f"projeto {ARF} excluído", em=AGORA)

    cadeia = travessia(referencias, projeto_id=ARA)

    pendentes = cadeia.pendentes()
    print(f"elos={len(cadeia.elos)} pendentes={len(pendentes)} resumo={cadeia.resumo()}")
    assert len(cadeia.elos) == 4
    assert len(pendentes) == 1
    assert pendentes[0].estado is EstadoDaReferencia.PENDENTE
    assert str(ARF) in pendentes[0].motivo


def test_a_travessia_de_um_projeto_sem_referencia_e_uma_cadeia_vazia() -> None:
    assert travessia(cadeia_completa(), projeto_id=uuid4()).elos == ()


def test_a_travessia_e_deterministica_e_nao_entra_em_laco() -> None:
    """Um ciclo entre projetos é dado torto vindo do banco — e não pode travar a leitura."""
    laco = (
        _ref(
            TipoDeReferencia.DERIVACAO_ARF_APR,
            Ponta(ferramenta="arf", projeto_id=ARF),
            Ponta(ferramenta="apr", projeto_id=APR),
        ),
        _ref(
            TipoDeReferencia.DERIVACAO_OI_AT,
            Ponta(ferramenta="apr", projeto_id=APR),
            Ponta(ferramenta="arf", projeto_id=ARF),
        ),
    )
    cadeia = travessia(laco, projeto_id=ARF)
    print(f"cadeia com laço: {len(cadeia.elos)} elo(s)")
    assert len(cadeia.elos) == 2
    assert travessia(laco, projeto_id=ARF).elos == cadeia.elos


def test_reidratar_uma_referencia_nao_emite_evento() -> None:
    original = cadeia_completa()[0]
    de_volta = reidratar_referencia(
        id=original.id,
        tipo=original.tipo,
        origem=original.origem,
        destino=original.destino,
        dono=DONO,
        criada_em=AGORA,
        estado=EstadoDaReferencia.PENDENTE,
        motivo="projeto excluído",
        versao=7,
    )
    print(f"eventos após reidratar: {len(de_volta.eventos)} versao_lida={de_volta.versao_lida}")
    assert de_volta.eventos == ()
    assert de_volta.versao == 7
    assert de_volta.versao_lida == 7
    assert de_volta.estado is EstadoDaReferencia.PENDENTE
