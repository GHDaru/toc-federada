"""A trava da proposta de ação — a mesma disciplina que o projeto já tinha, e não tinha.

Siglas, uma vez neste arquivo: **APH** — Aplicação ↔ Harness · **FSM** — máquina de estados
finitos · **SQL** — *Structured Query Language* · **HTTP** — *HyperText Transfer Protocol* ·
**TTL** — *Time To Live* (tempo de vida).

## O defeito medido, e por que a FSM não o impediu

Oito confirmações simultâneas da MESMA proposta `toc.criar_nos` com 30 alvos devolveram
`{200: 8}`, gravaram 50 nós para 30 pedidos, com 22 títulos repetidos, e deixaram **oito**
linhas de traço para uma proposta só (reprodução em
`tests/integracao/test_corrida_de_confirmacao_no_postgres.py`).

O diagnóstico, e é ele que decide o conserto: **a FSM guardava o objeto, não a linha.**
`RepositorioDePropostasSQL.obter` reidrata um `PropostaDeAcao` NOVO a cada chamada, e
`transicionar` consulta `self.estado`, que é atributo de memória. Oito confirmações leem
oito agregados, todos em `awaiting_approval`, e as oito transições são legítimas — cada uma
no seu objeto. Havia uma linha e N agregados; a tabela de transições nunca chegou a ver um
conflito.

O que faz a transição `confirmed → executing` ser a serialização natural é ela existir
**no banco e antes do efeito**. Este arquivo fixa a metade que é regra de domínio: a
proposta passa a saber de que estado partiu (`estado_lido`), e a gravação passa a poder ser
condicionada a ele — exatamente o que `Projeto.versao_lida` fez pelo M1 (Núcleo de Diagramas
Lógicos), pelo M2 (Árvore da Realidade Atual) e pelo M3 (Nuvem de Conflito).
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from toc_api.dominio.federacao.proposta import (
    ChaveDeIdempotenciaReutilizada,
    CorridaDeDecisao,
    Origem,
    PropostaDeAcao,
    TransicaoInvalida,
)

AGORA = datetime(2026, 9, 6, 12, 0, tzinfo=timezone.utc)
TTL = timedelta(minutes=10)


def _proposta() -> PropostaDeAcao:
    return PropostaDeAcao.nova(
        proposal_id="prop-corrida",
        action_id="toc.criar_nos",
        args={"projeto_id": "p1", "nos": [{"titulo": "Entregas atrasam", "tipo": "ude"}]},
        risk="confirm",
        alvos=("Entregas atrasam",),
        origem=Origem.IA,
        criada_em=AGORA,
        ttl=TTL,
    )


# -- o agregado sabe de que estado partiu ------------------------------------------------


def test_a_proposta_nova_nunca_foi_gravada_e_diz_isso() -> None:
    """`estado_lido` vazio é o `versao_lida == 0` do projeto: nada gravado ainda."""
    proposta = _proposta()

    assert proposta.estado_lido == ""


def test_confirmar_gravacao_alinha_o_estado_lido_ao_estado_corrente() -> None:
    """Depois do commit, o estado em memória passa a ser o estado da linha — e só depois.

    Alinhar antes do commit deixaria o agregado achando que está sincronizado com um banco
    que não recebeu nada, e a gravação seguinte partiria de um estado que a linha não tem.
    """
    proposta = _proposta()
    proposta.apresentar(em=AGORA)
    proposta.confirmar_gravacao()

    assert proposta.estado_lido == "awaiting_approval"

    proposta.confirmar(em=AGORA)

    assert proposta.estado == "confirmed"
    assert proposta.estado_lido == "awaiting_approval", (
        "transicionar não pode mexer no estado_lido: ele é o que a LINHA tem, e a linha "
        "ainda não recebeu nada"
    )


def test_o_estado_lido_nao_entra_no_construtor_nem_na_comparacao() -> None:
    """É estado de SINCRONIA com o repositório, não estado de negócio (como `versao_lida`)."""
    with pytest.raises(TypeError):
        PropostaDeAcao(  # type: ignore[call-arg]
            proposal_id="p",
            action_id="a",
            args={},
            risk="read",
            alvos=(),
            origem=Origem.IA,
            criada_em=AGORA,
            ttl=TTL,
            estado_lido="awaiting_approval",
        )


# -- a corrida perdida é audível, e sai com o código que o §A.7 nomeia --------------------


def test_a_corrida_perdida_carrega_os_dois_estados_e_o_codigo_do_a7() -> None:
    """`INVALID_TRANSITION` é o código do §A.7 para confirmação fora da FSM da proposta.

    Não é código novo, e é de propósito: da perspectiva de quem perdeu, a proposta não
    está mais em `awaiting_approval`. O que o erro acrescenta são os dois estados, pelo
    mesmo motivo que `ConflitoDeVersao` carrega os dois números — o cliente discrimina por
    código e por dado, nunca por mensagem.
    """
    erro = CorridaDeDecisao(
        "prop-corrida", estado_lido="awaiting_approval", estado_atual="executing"
    )

    assert isinstance(erro, TransicaoInvalida)
    assert erro.codigo == "INVALID_TRANSITION"
    assert erro.http == 409
    assert erro.estado_lido == "awaiting_approval"
    assert erro.estado_atual == "executing"
    assert "awaiting_approval" in str(erro) and "executing" in str(erro)


def test_a_chave_reutilizada_em_outra_proposta_tem_codigo_proprio() -> None:
    """APH-5.3: uma chave produz UMA execução — inclusive quando muda de proposta."""
    erro = ChaveDeIdempotenciaReutilizada("idem-001", proposal_id="prop-outra")

    assert isinstance(erro, TransicaoInvalida)
    assert erro.codigo == "IDEMPOTENCY_KEY_REUSED"
    assert erro.http == 409
    assert erro.idempotency_key == "idem-001"
    assert erro.proposal_id == "prop-outra"


def test_o_codigo_da_chave_reutilizada_esta_no_registro_unico_do_a7() -> None:
    """Código não declarado não sai do serviço — `ErroDoFio` recusa (§A.7)."""
    from toc_api.dominio.federacao.wire import CODIGOS, CODIGOS_PROPRIOS

    assert "IDEMPOTENCY_KEY_REUSED" in CODIGOS
    assert CODIGOS_PROPRIOS["IDEMPOTENCY_KEY_REUSED"]
