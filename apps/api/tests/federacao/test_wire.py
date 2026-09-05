"""O fio (Anexo A) como regra de domínio: evento, `seq`, replay, erro e sessão.

Siglas: **APH** — Aplicação ↔ Harness · **SSE** — *Server-Sent Events* · **JSON** —
*JavaScript Object Notation* · **HTTP** — *HyperText Transfer Protocol*.

O transporte (SSE sobre POST) é da borda; o que está aqui é o que a borda **não pode
inventar**: a atribuição do `seq` no servidor antes da emissão (APH-1.2), o replay sem
perda nem duplicação (APH-1.3), o terminador obrigatório (APH-2.1), o cancelamento que
nunca é silencioso (APH-1.4) e o envelope de erro com código estável (APH-1.5).
"""
from __future__ import annotations

import pytest

from toc_api.dominio.federacao.wire import (
    CODIGOS,
    KINDS,
    REGISTRO_MINIMO_A7,
    ErroDoFio,
    Evento,
    SessaoDeConversa,
    SessaoEncerrada,
)


def _sessao() -> SessaoDeConversa:
    return SessaoDeConversa(id="sessao-001")


# --------------------------------------------------------------------------------------
# Vocabulário (APH-2.1) e evolução (APH-2.2)
# --------------------------------------------------------------------------------------


def test_o_vocabulario_tem_as_seis_familias_minimas() -> None:
    """APH-2.1: conteúdo, raciocínio, ação (proposta/resultado), comando de UI, erro e
    terminador — mais `citation`, que o schema do fio também declara."""
    assert KINDS == (
        "content",
        "thinking",
        "action_proposal",
        "action_result",
        "ui_command",
        "citation",
        "error",
        "done",
    )


def test_kind_fora_do_vocabulario_nao_e_emitido() -> None:
    """O produtor documenta antes de emitir (APH-2.2); emitir o que não está no contrato
    é o que a regra proíbe do lado de quem produz."""
    with pytest.raises(ValueError):
        Evento(seq=1, kind="inventado", payload={})


def test_o_registro_minimo_do_a7_tem_sete_codigos() -> None:
    """§A.7: cinco ✅ e dois 🧪 — contados na fonte, não de memória."""
    assert len(REGISTRO_MINIMO_A7) == 7
    assert REGISTRO_MINIMO_A7 == (
        "STREAM_CANCELLED",
        "PROVIDER_FAILURE",
        "INVALID_TRANSITION",
        "UNAUTHORIZED",
        "INVALID_CONTEXT",
        "PROPOSAL_EXPIRED",
        "PROPOSAL_CONTEXT_STALE",
    )


def test_todo_codigo_e_maiusculo_com_sublinhado() -> None:
    """RF-47: o cliente discrimina por código, nunca por mensagem — e nenhum sai minúsculo."""
    import re

    for codigo in CODIGOS:
        assert re.match(r"^[A-Z][A-Z0-9_]*$", codigo), codigo


def test_o_registro_minimo_e_subconjunto_dos_nossos_codigos() -> None:
    assert set(REGISTRO_MINIMO_A7) <= set(CODIGOS)


def test_codigo_de_erro_desconhecido_e_recusado_na_construcao() -> None:
    """Código próprio existe — documentado no mesmo contrato (RF-47). Inventado, não."""
    with pytest.raises(ValueError):
        ErroDoFio(code="deu_ruim", message="x")
    with pytest.raises(ValueError):
        ErroDoFio(code="ALGO_QUE_NINGUEM_DOCUMENTOU", message="x")


def test_o_envelope_de_erro_tem_a_forma_do_schema_normativo() -> None:
    erro = ErroDoFio(code="STREAM_CANCELLED", message="cancelado por quem pediu")

    assert erro.como_payload() == {
        "code": "STREAM_CANCELLED",
        "message": "cancelado por quem pediu",
    }
    assert erro.como_corpo_http() == {"error": erro.como_payload()}


def test_o_envelope_de_erro_com_detalhes_mantem_o_schema_fechado() -> None:
    erro = ErroDoFio(code="INVALID_CONTEXT", message="campo fora do schema", details={"campo": "x"})

    assert set(erro.como_payload()) == {"code", "message", "details"}


# --------------------------------------------------------------------------------------
# `seq` monotônico atribuído no servidor (APH-1.2)
# --------------------------------------------------------------------------------------


def test_o_seq_e_atribuido_pela_sessao_e_comeca_em_um() -> None:
    sessao = _sessao()

    primeiro = sessao.emitir("content", {"text": "olá"})
    segundo = sessao.emitir("thinking", {"text": "pensando"})

    assert (primeiro.seq, segundo.seq) == (1, 2)


def test_o_seq_e_estritamente_crescente_e_sem_lacuna() -> None:
    sessao = _sessao()
    for i in range(20):
        sessao.emitir("content", {"text": str(i)})

    seqs = [e.seq for e in sessao.eventos]

    assert seqs == list(range(1, 21))


def test_nao_ha_como_injetar_seq_de_fora() -> None:
    """A assinatura de `emitir` não aceita `seq` — o servidor atribui, e ponto."""
    import inspect

    assert "seq" not in inspect.signature(SessaoDeConversa.emitir).parameters


# --------------------------------------------------------------------------------------
# Replay (APH-1.3)
# --------------------------------------------------------------------------------------


def test_replay_after_zero_devolve_tudo() -> None:
    sessao = _sessao()
    sessao.emitir("content", {"text": "a"})
    sessao.emitir("done", {})

    assert [e.seq for e in sessao.replay(0)] == [1, 2]


def test_replay_after_n_devolve_so_o_que_falta_sem_duplicar() -> None:
    sessao = _sessao()
    for i in range(5):
        sessao.emitir("content", {"text": str(i)})

    assert [e.seq for e in sessao.replay(2)] == [3, 4, 5]
    assert [e.seq for e in sessao.replay(5)] == []


def test_replay_de_after_maior_que_o_ultimo_e_vazio_e_nao_e_erro() -> None:
    sessao = _sessao()
    sessao.emitir("done", {})

    assert sessao.replay(99) == ()


# --------------------------------------------------------------------------------------
# Terminador (APH-2.1) e cancelamento (APH-1.4)
# --------------------------------------------------------------------------------------


def test_a_sessao_sabe_quando_o_turno_terminou() -> None:
    sessao = _sessao()
    sessao.emitir("content", {"text": "a"})
    assert sessao.turno_terminado is False

    sessao.emitir("done", {})
    assert sessao.turno_terminado is True


def test_error_tambem_termina_o_turno() -> None:
    sessao = _sessao()
    sessao.emitir("error", ErroDoFio(code="PROVIDER_FAILURE", message="x").como_payload())

    assert sessao.turno_terminado is True


def test_emitir_depois_do_terminador_e_recusado() -> None:
    """Emitir depois de `done` produziria replay diferente do stream — e o check
    `replay-integral` da suíte compara os dois evento a evento."""
    sessao = _sessao()
    sessao.emitir("done", {})

    with pytest.raises(SessaoEncerrada):
        sessao.emitir("content", {"text": "tarde demais"})


def test_cancelar_encerra_com_error_stream_cancelled_no_log() -> None:
    """APH-1.4: nunca em silêncio — o evento fica no stream **e** no replay."""
    sessao = _sessao()
    sessao.emitir("content", {"text": "resposta longa"})

    evento = sessao.cancelar()

    assert evento.kind == "error"
    assert evento.payload["code"] == "STREAM_CANCELLED"
    assert sessao.replay(0)[-1].payload["code"] == "STREAM_CANCELLED"
    assert sessao.turno_terminado is True


def test_cancelar_turno_ja_terminado_nao_acrescenta_evento() -> None:
    sessao = _sessao()
    sessao.emitir("done", {})
    antes = len(sessao.eventos)

    assert sessao.cancelar() is None
    assert len(sessao.eventos) == antes


def test_um_novo_turno_continua_a_mesma_sequencia() -> None:
    """`seq` é monotônico **por sessão**, não por turno (APH-1.2)."""
    sessao = _sessao()
    sessao.emitir("content", {"text": "a"})
    sessao.emitir("done", {})

    sessao.abrir_turno()
    terceiro = sessao.emitir("content", {"text": "b"})

    assert terceiro.seq == 3
    assert sessao.turno_terminado is False


# --------------------------------------------------------------------------------------
# Serialização — a mesma de ponta a ponta
# --------------------------------------------------------------------------------------


def test_o_evento_serializa_com_exatamente_tres_campos() -> None:
    """O schema do evento é fechado: `{seq, kind, payload}` e nada mais."""
    evento = Evento(seq=3, kind="content", payload={"text": "olá"})

    assert evento.como_json() == {"seq": 3, "kind": "content", "payload": {"text": "olá"}}


def test_stream_e_replay_serializam_o_mesmo_objeto() -> None:
    """O check `replay-integral` da suíte compara os eventos completos: um campo a mais
    no stream do que no replay reprova. Uma função só de serialização impede isso."""
    sessao = _sessao()
    emitido = sessao.emitir("action_result", {"proposal_id": "p", "status": "executed"})

    do_replay = sessao.replay(0)[0]

    assert emitido.como_json() == do_replay.como_json()


def test_propostas_pendentes_sobrevivem_ao_replay() -> None:
    """RF-45 / APH-5.6: reconectar e perder uma aprovação pendente é perda de governança."""
    sessao = _sessao()
    sessao.emitir(
        "action_proposal",
        {"proposal_id": "prop-1", "action_id": "toc.criar_nos", "risk": "confirm", "requires_confirmation": True},
    )
    sessao.emitir("done", {})

    pendentes = [e for e in sessao.replay(0) if e.kind == "action_proposal"]

    assert [e.payload["proposal_id"] for e in pendentes] == ["prop-1"]
