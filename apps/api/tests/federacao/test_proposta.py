"""A máquina de estados da proposta de ação (APH-5.1) — o coração da governança.

Siglas: **APH** — Aplicação ↔ Harness · **FSM** — máquina de estados finitos · **TTL** —
*Time To Live* (tempo de vida) · **UDE** — Efeito Indesejável.

O requisito central da spec 006 (RF-11) é literal: *"transição fora da tabela DEVE falhar
com `INVALID_TRANSITION`"*. Um teste que só percorra o caminho feliz deixaria a metade que
importa sem prova — por isso aqui a tabela inteira é percorrida **e** o complemento dela
também: para cada par (estado, evento) que **não** está na tabela, a transição tem de
falhar. É a diferença entre testar o que a FSM faz e testar o que ela **impede**.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from toc_api.dominio.federacao.proposta import (
    ESTADOS,
    ESTADOS_TERMINAIS,
    EVENTOS,
    TABELA_DE_TRANSICOES,
    Desfecho,
    Origem,
    PropostaDeAcao,
    TransicaoInvalida,
    risco_do_lote,
)

AGORA = datetime(2026, 9, 5, 12, 0, tzinfo=timezone.utc)
TTL = timedelta(minutes=10)


def _proposta(risk: str = "confirm", alvos: tuple[str, ...] = ("Entregas atrasam",)) -> PropostaDeAcao:
    return PropostaDeAcao.nova(
        proposal_id="prop-001",
        action_id="toc.criar_nos",
        args={"projeto_id": "p1", "nos": [{"titulo": a, "tipo": "ude"} for a in alvos]},
        risk=risk,
        alvos=alvos,
        origem=Origem.IA,
        criada_em=AGORA,
        ttl=TTL,
        contexto_hash="0123456789abcdef",
    )


# --------------------------------------------------------------------------------------
# A tabela, inteira e pelo complemento
# --------------------------------------------------------------------------------------


def test_a_fsm_nao_adota_o_estado_stale_e_diz_por_que() -> None:
    """RF-11: `stale` é 🧪 na norma e **não** é adotado.

    Contexto divergente encerra a proposta em `cancelled` com o código
    `PROPOSAL_CONTEXT_STALE` — o mesmo desenho do laboratório A registrado no §A.8. O
    vocabulário do fio admite `stale` como `action_result.status`; **nós não o emitimos**,
    e é isso que este teste fixa para a decisão não virar esquecimento.
    """
    assert "stale" not in ESTADOS
    assert set(ESTADOS) == {
        "proposed",
        "awaiting_approval",
        "confirmed",
        "executing",
        "executed",
        "failed",
        "cancelled",
        "denied",
        "expired",
    }


def test_estados_terminais_sao_os_cinco_do_vocabulario_do_fio() -> None:
    assert ESTADOS_TERMINAIS == frozenset({"executed", "failed", "cancelled", "denied", "expired"})


@pytest.mark.parametrize(("origem", "evento"), sorted(TABELA_DE_TRANSICOES))
def test_toda_transicao_da_tabela_acontece(origem: str, evento: str) -> None:
    # Risco `read`: a única guarda além da tabela é a que impede a mutadora de pular o
    # gate (`proposed → confirmed`), e ela tem teste próprio logo abaixo. Com `read`, a
    # tabela é percorrida inteira, sem guarda nenhuma no caminho.
    proposta = _proposta(risk="read")
    proposta._forcar_estado_para_teste(origem)

    proposta.transicionar(evento, em=AGORA)

    assert proposta.estado == TABELA_DE_TRANSICOES[(origem, evento)]


@pytest.mark.parametrize(
    ("origem", "evento"),
    sorted(
        (estado, evento)
        for estado in ESTADOS
        for evento in EVENTOS
        if (estado, evento) not in TABELA_DE_TRANSICOES
    ),
)
def test_toda_transicao_fora_da_tabela_falha_com_invalid_transition(origem: str, evento: str) -> None:
    """O complemento da tabela — a metade que a maioria dos testes de FSM esquece."""
    proposta = _proposta()
    proposta._forcar_estado_para_teste(origem)

    with pytest.raises(TransicaoInvalida) as erro:
        proposta.transicionar(evento, em=AGORA)

    assert erro.value.codigo == "INVALID_TRANSITION"
    assert erro.value.http == 409
    assert proposta.estado == origem, "uma transição recusada não pode mexer no estado"


def test_estado_terminal_e_imutavel() -> None:
    proposta = _proposta()
    proposta.transicionar("apresentar", em=AGORA)
    proposta.transicionar("negar", em=AGORA)

    assert proposta.estado == "denied"
    for evento in EVENTOS:
        with pytest.raises(TransicaoInvalida):
            proposta.transicionar(evento, em=AGORA)


# --------------------------------------------------------------------------------------
# Risco, confirmação e TTL
# --------------------------------------------------------------------------------------


def test_risco_read_executa_direto_sem_gate_humano() -> None:
    """RF-12: `read` executa direto; `confirm` para no gate. Decidido no servidor."""
    leitura = _proposta(risk="read")

    assert leitura.requer_confirmacao is False
    leitura.transicionar("confirmar", em=AGORA)
    assert leitura.estado == "confirmed"


def test_risco_confirm_nao_pode_pular_o_gate() -> None:
    mutadora = _proposta(risk="confirm")

    assert mutadora.requer_confirmacao is True
    with pytest.raises(TransicaoInvalida):
        # `proposed → confirmed` só existe para `read`; a mutadora tem de passar por
        # `awaiting_approval`, e é a FSM que impõe isso — não a boa vontade da rota.
        mutadora.confirmar(em=AGORA)
    # e a guarda vive em `transicionar`, não só no método de conveniência: uma rota que
    # chamasse a transição crua também não consegue pular o gate
    with pytest.raises(TransicaoInvalida) as erro:
        mutadora.transicionar("confirmar", em=AGORA)
    assert erro.value.codigo == "INVALID_TRANSITION"
    assert mutadora.estado == "proposed"


def test_confirmar_fora_de_awaiting_approval_falha() -> None:
    """US-04 da spec 006, literal."""
    proposta = _proposta()

    with pytest.raises(TransicaoInvalida) as erro:
        proposta.confirmar(em=AGORA)

    assert erro.value.codigo == "INVALID_TRANSITION"


def test_ttl_vencido_expira_e_a_decisao_tardia_falha() -> None:
    """RF-13: vencido, transiciona a `expired`; a decisão tardia é `PROPOSAL_EXPIRED`."""
    proposta = _proposta()
    proposta.transicionar("apresentar", em=AGORA)

    depois = AGORA + TTL + timedelta(seconds=1)
    assert proposta.vencida_em(depois) is True

    with pytest.raises(TransicaoInvalida) as erro:
        proposta.confirmar(em=depois)

    assert erro.value.codigo == "PROPOSAL_EXPIRED"
    assert proposta.estado == "expired", "vencer é desfecho, não limbo"


def test_contexto_divergente_encerra_em_cancelled_com_codigo_proprio() -> None:
    """RF-15: comparar `context_hash` e recusar sem executar (APH-5.4)."""
    proposta = _proposta()
    proposta.transicionar("apresentar", em=AGORA)

    with pytest.raises(TransicaoInvalida) as erro:
        proposta.confirmar(em=AGORA, contexto_hash="fedcba9876543210")

    assert erro.value.codigo == "PROPOSAL_CONTEXT_STALE"
    assert proposta.estado == "cancelled"


def test_contexto_igual_deixa_confirmar() -> None:
    proposta = _proposta()
    proposta.transicionar("apresentar", em=AGORA)

    proposta.confirmar(em=AGORA, contexto_hash="0123456789abcdef")

    assert proposta.estado == "confirmed"


def test_confirmacao_sem_context_hash_e_aceita_porque_o_campo_e_opcional_no_fio() -> None:
    proposta = _proposta()
    proposta.transicionar("apresentar", em=AGORA)

    proposta.confirmar(em=AGORA)

    assert proposta.estado == "confirmed"


def test_negar_encerra_em_denied_e_isso_tambem_e_desfecho() -> None:
    proposta = _proposta()
    proposta.transicionar("apresentar", em=AGORA)

    proposta.negar(em=AGORA)

    assert proposta.estado == "denied"
    assert proposta.terminal is True


# --------------------------------------------------------------------------------------
# Deduplicação (RF-16) e idempotência (DÚVIDA 4)
# --------------------------------------------------------------------------------------


def test_confirmar_duas_vezes_nao_reexecuta_e_devolve_o_mesmo_desfecho() -> None:
    """RF-16/APH-5.3: a primeira decisão produz o efeito; as seguintes repetem o resultado."""
    proposta = _proposta()
    proposta.transicionar("apresentar", em=AGORA)
    proposta.confirmar(em=AGORA)
    proposta.transicionar("executar", em=AGORA)
    proposta.concluir(
        desfecho=Desfecho(status="executed", outcomes=(("Entregas atrasam", "executed", ""),)),
        em=AGORA,
    )

    repetida = proposta.decisao_ja_tomada(aprovado=True)

    assert repetida is not None
    assert repetida.status == "executed"
    assert proposta.execucoes == 1


def test_idempotency_key_repetida_devolve_o_mesmo_resultado() -> None:
    proposta = _proposta()
    proposta.transicionar("apresentar", em=AGORA)
    chave = "8f14e45f-ceea-467a-9e07-4e0a9a9a9a9a"

    proposta.confirmar(em=AGORA, idempotency_key=chave)

    assert proposta.mesma_chave(chave) is True
    assert proposta.mesma_chave("outra-chave") is False


# --------------------------------------------------------------------------------------
# Lote (APH-5.9) — a parte em que o `status` não pode mentir
# --------------------------------------------------------------------------------------


def test_lote_e_uma_proposta_com_n_alvos() -> None:
    """RF-24: uma proposta, N alvos — nunca N propostas (ADR 0009 da irmã)."""
    oito = tuple(f"UDE {i}" for i in range(1, 9))
    proposta = _proposta(alvos=oito)

    assert proposta.quantidade_de_alvos == 8
    assert proposta.alvos == oito


def test_status_terminal_nao_afirma_mais_sucesso_do_que_os_outcomes() -> None:
    """RF-27 / APH-5.9(e): com um alvo fora de `executed`, o terminal não é `executed`.

    O schema normativo do fio rejeita a combinação; aqui a invariante é do agregado, para
    a mentira ser impossível **antes** de virar evento.
    """
    proposta = _proposta(alvos=("a", "b"))
    proposta.transicionar("apresentar", em=AGORA)
    proposta.confirmar(em=AGORA)
    proposta.transicionar("executar", em=AGORA)

    with pytest.raises(ValueError) as erro:
        proposta.concluir(
            desfecho=Desfecho(
                status="executed",
                outcomes=(("a", "executed", ""), ("b", "failed", "mãe inexistente")),
            ),
            em=AGORA,
        )

    assert "outcomes" in str(erro.value)


def test_lote_com_falha_parcial_termina_em_failed_com_desfecho_por_alvo() -> None:
    """O fluxo 6.4 da spec: sete executam, o oitavo falha."""
    alvos = tuple(f"UDE {i}" for i in range(1, 9))
    proposta = _proposta(alvos=alvos)
    proposta.transicionar("apresentar", em=AGORA)
    proposta.confirmar(em=AGORA)
    proposta.transicionar("executar", em=AGORA)

    outcomes = tuple(
        (alvo, "executed" if i < 7 else "failed", "" if i < 7 else "título duplicado")
        for i, alvo in enumerate(alvos)
    )
    proposta.concluir(desfecho=Desfecho(status="failed", outcomes=outcomes), em=AGORA)

    assert proposta.estado == "failed"
    assert len(proposta.desfecho.outcomes) == 8
    assert sum(1 for _, s, _ in proposta.desfecho.outcomes if s == "executed") == 7


def test_outcome_com_status_fora_do_vocabulario_e_recusado() -> None:
    """§A.3: `executed | failed | denied | skipped`, e nada mais."""
    with pytest.raises(ValueError):
        Desfecho(status="failed", outcomes=(("a", "quase", ""),))


def test_status_terminal_fora_do_vocabulario_e_recusado() -> None:
    with pytest.raises(ValueError):
        Desfecho(status="quase", outcomes=())


def test_risco_do_lote_e_o_mais_alto_dos_itens() -> None:
    """RF-29 / APH-5.9(d)."""
    assert risco_do_lote(["read", "read"]) == "read"
    assert risco_do_lote(["read", "confirm"]) == "confirm"
    assert risco_do_lote([]) == "read"


def test_uma_proposta_nunca_mistura_action_ids() -> None:
    """RN-04: lote não mistura ações — a assinatura de `nova` só admite um `action_id`."""
    import inspect

    assinatura = inspect.signature(PropostaDeAcao.nova)
    assert "action_id" in assinatura.parameters
    assert "action_ids" not in assinatura.parameters


def test_a_origem_e_dado_e_nao_muda_o_fluxo() -> None:
    """RI-02 e o ADR 0009 da irmã: origem humana × IA percorre exatamente o mesmo caminho.

    O teste compara as duas trajetórias inteiras. No instante em que alguém escrever um
    `if origem == IA`, as duas listas divergem e este teste cai — que é a ideia.
    """
    trajetorias = {}
    for origem in (Origem.HUMANO, Origem.IA):
        proposta = PropostaDeAcao.nova(
            proposal_id="p",
            action_id="toc.criar_nos",
            args={"projeto_id": "p1", "nos": [{"titulo": "t", "tipo": "ude"}]},
            risk="confirm",
            alvos=("t",),
            origem=origem,
            criada_em=AGORA,
            ttl=TTL,
        )
        caminho = [proposta.estado]
        proposta.transicionar("apresentar", em=AGORA)
        caminho.append(proposta.estado)
        proposta.confirmar(em=AGORA)
        caminho.append(proposta.estado)
        proposta.transicionar("executar", em=AGORA)
        caminho.append(proposta.estado)
        proposta.concluir(desfecho=Desfecho(status="executed", outcomes=()), em=AGORA)
        caminho.append(proposta.estado)
        trajetorias[origem] = caminho

    assert trajetorias[Origem.HUMANO] == trajetorias[Origem.IA]


def test_o_evento_de_proposta_do_fio_sai_do_agregado() -> None:
    """O payload `action_proposal` do §A.3, montado por quem tem a invariante."""
    proposta = _proposta()

    payload = proposta.como_action_proposal(titulo="Criar nos na arvore", justificativa="Você pediu.")

    assert payload["proposal_id"] == "prop-001"
    assert payload["action_id"] == "toc.criar_nos"
    assert payload["risk"] == "confirm"
    assert payload["requires_confirmation"] is True
    assert payload["context_hash"] == "0123456789abcdef"


def test_o_evento_de_resultado_do_fio_sai_do_agregado() -> None:
    proposta = _proposta(alvos=("a", "b"))
    proposta.transicionar("apresentar", em=AGORA)
    proposta.confirmar(em=AGORA)
    proposta.transicionar("executar", em=AGORA)
    proposta.concluir(
        desfecho=Desfecho(status="failed", outcomes=(("a", "executed", ""), ("b", "failed", "x"))),
        em=AGORA,
    )

    payload = proposta.como_action_result()

    assert payload["status"] == "failed"
    assert payload["outcomes"] == [
        {"target": "a", "status": "executed"},
        {"target": "b", "status": "failed", "message": "x"},
    ]
