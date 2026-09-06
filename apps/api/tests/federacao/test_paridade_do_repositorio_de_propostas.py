"""O duplo em memória não pode ser mais permissivo que o PostgreSQL. Nunca.

Siglas, uma vez neste arquivo: **APH** — Aplicação ↔ Harness · **SQL** — *Structured Query
Language* · **FSM** — máquina de estados finitos · **HTTP** — *HyperText Transfer Protocol*.

É a lição já paga em `infra/persistencia/memoria.py`, item 3 do cabeçalho de lá: enquanto o
adaptador real recusa a segunda escrita da mesma leitura e o duplo aceita, **a suíte de
contrato fica verde sobre um defeito que o banco de verdade recusa** — e a suíte de
contrato é onde roda quase tudo. A trava da proposta nasce com este arquivo junto para não
repetir isso.

Aqui mede-se o duplo (`RepositorioDePropostasEmMemoria`), sem banco. A mesma bateria contra
o PostgreSQL real está em `tests/integracao/test_corrida_de_confirmacao_no_postgres.py` e em
`tests/integracao/test_propostas_no_postgres.py`.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from toc_api.dominio.federacao.proposta import (
    ChaveDeIdempotenciaReutilizada,
    CorridaDeDecisao,
    Desfecho,
    Origem,
    PropostaDeAcao,
)
from toc_api.infra.federacao.memoria import RepositorioDePropostasEmMemoria

AGORA = datetime(2026, 9, 6, 12, 0, tzinfo=timezone.utc)
TTL = timedelta(minutes=10)
INQ = "inq-horizonte"
USR = "usr-facilitadora"


def _nova(proposal_id: str = "prop-001") -> PropostaDeAcao:
    return PropostaDeAcao.nova(
        proposal_id=proposal_id,
        action_id="toc.criar_nos",
        args={"projeto_id": "p1", "nos": [{"titulo": "Entregas atrasam", "tipo": "ude"}]},
        risk="confirm",
        alvos=("Entregas atrasam",),
        origem=Origem.IA,
        criada_em=AGORA,
        ttl=TTL,
    )


def _apresentada(repositorio: RepositorioDePropostasEmMemoria) -> PropostaDeAcao:
    proposta = _nova()
    proposta.apresentar(em=AGORA)
    repositorio.salvar(INQ, USR, proposta)
    return proposta


# -- a fronteira: ler não é ficar com o objeto do "banco" --------------------------------


def test_obter_devolve_uma_copia_e_nao_a_linha_guardada() -> None:
    """Sem cópia na fronteira, mutar o agregado devolvido mutaria o "banco" sem gravar.

    E, pior no caso da proposta: dois leitores receberiam o MESMO objeto, a segunda
    transição encontraria o estado que a primeira já mudou, e a corrida ficaria invisível
    no duplo — verde sobre o defeito que o PostgreSQL mostra.
    """
    repositorio = RepositorioDePropostasEmMemoria()
    _apresentada(repositorio)

    uma = repositorio.obter(INQ, "prop-001")
    outra = repositorio.obter(INQ, "prop-001")

    assert uma is not outra
    uma.confirmar(em=AGORA)
    assert repositorio.obter(INQ, "prop-001").estado == "awaiting_approval"


def test_obter_preenche_o_estado_lido_com_o_estado_da_linha() -> None:
    repositorio = RepositorioDePropostasEmMemoria()
    _apresentada(repositorio)

    lida = repositorio.obter(INQ, "prop-001")

    assert lida.estado == "awaiting_approval"
    assert lida.estado_lido == "awaiting_approval"


# -- a trava: a segunda gravação da mesma leitura é recusada -----------------------------


def test_a_segunda_gravacao_da_mesma_leitura_e_recusada() -> None:
    """O caso puro do defeito: duas confirmações que leram o mesmo `awaiting_approval`."""
    repositorio = RepositorioDePropostasEmMemoria()
    _apresentada(repositorio)

    primeira = repositorio.obter(INQ, "prop-001")
    segunda = repositorio.obter(INQ, "prop-001")

    primeira.confirmar(em=AGORA)
    primeira.transicionar("executar", em=AGORA)
    repositorio.salvar(INQ, USR, primeira)

    segunda.confirmar(em=AGORA)
    segunda.transicionar("executar", em=AGORA)
    with pytest.raises(CorridaDeDecisao) as recusa:
        repositorio.salvar(INQ, USR, segunda)

    assert recusa.value.estado_lido == "awaiting_approval"
    assert recusa.value.estado_atual == "executing"
    assert repositorio.obter(INQ, "prop-001").estado == "executing"


def test_a_gravacao_do_vencedor_continua_passando_depois_da_reserva() -> None:
    """Quem reservou grava o desfecho: `executing → executed` parte do estado que ele tem."""
    repositorio = RepositorioDePropostasEmMemoria()
    _apresentada(repositorio)

    proposta = repositorio.obter(INQ, "prop-001")
    proposta.confirmar(em=AGORA)
    proposta.transicionar("executar", em=AGORA)
    repositorio.salvar(INQ, USR, proposta)

    proposta.concluir(
        desfecho=Desfecho(status="executed", outcomes=(("Entregas atrasam", "executed", ""),)),
        em=AGORA,
    )
    repositorio.salvar(INQ, USR, proposta)

    guardada = repositorio.obter(INQ, "prop-001")
    assert guardada.estado == "executed"
    assert guardada.execucoes == 1


def test_a_insercao_de_uma_proposta_que_ja_existe_e_recusada() -> None:
    """`estado_lido` vazio quer dizer "nunca gravada" — e não "grave por cima"."""
    repositorio = RepositorioDePropostasEmMemoria()
    _apresentada(repositorio)

    intrusa = _nova()  # mesmo proposal_id, estado_lido vazio
    with pytest.raises(CorridaDeDecisao):
        repositorio.salvar(INQ, USR, intrusa)


# -- a deduplicação REAL do APH-5.3 ------------------------------------------------------


def test_a_chave_de_idempotencia_e_unica_por_inquilino() -> None:
    """APH-5.3: a mesma chave produz UMA execução — inclusive em outra proposta.

    Sem esta recusa, `idempotency_key` volta a ser uma coluna que ninguém consulta, que é
    exatamente como ela estava: gravada em toda confirmação e lida em lugar nenhum.
    """
    repositorio = RepositorioDePropostasEmMemoria()
    primeira = _apresentada(repositorio)
    primeira = repositorio.obter(INQ, "prop-001")
    primeira.confirmar(em=AGORA, idempotency_key="idem-001")
    primeira.transicionar("executar", em=AGORA)
    repositorio.salvar(INQ, USR, primeira)

    outra = _nova("prop-002")
    outra.apresentar(em=AGORA)
    repositorio.salvar(INQ, USR, outra)
    outra = repositorio.obter(INQ, "prop-002")
    outra.confirmar(em=AGORA, idempotency_key="idem-001")
    outra.transicionar("executar", em=AGORA)

    with pytest.raises(ChaveDeIdempotenciaReutilizada) as recusa:
        repositorio.salvar(INQ, USR, outra)

    assert recusa.value.idempotency_key == "idem-001"


def test_a_mesma_chave_no_mesmo_inquilino_de_outro_inquilino_nao_colide() -> None:
    """A unicidade é POR inquilino: chave de outro inquilino não é a nossa."""
    repositorio = RepositorioDePropostasEmMemoria()
    _apresentada(repositorio)
    minha = repositorio.obter(INQ, "prop-001")
    minha.confirmar(em=AGORA, idempotency_key="idem-001")
    minha.transicionar("executar", em=AGORA)
    repositorio.salvar(INQ, USR, minha)

    alheia = _nova("prop-002")
    alheia.apresentar(em=AGORA)
    repositorio.salvar("inq-outro", "usr-outro", alheia)
    alheia = repositorio.obter("inq-outro", "prop-002")
    alheia.confirmar(em=AGORA, idempotency_key="idem-001")
    alheia.transicionar("executar", em=AGORA)

    repositorio.salvar("inq-outro", "usr-outro", alheia)  # não levanta

    assert repositorio.obter("inq-outro", "prop-002").estado == "executing"


# -- a espera pelo desfecho de quem venceu ----------------------------------------------


def test_aguardar_desfecho_devolve_a_proposta_terminal() -> None:
    """Quem perdeu a corrida com a MESMA chave recebe o desfecho de quem venceu."""
    repositorio = RepositorioDePropostasEmMemoria()
    _apresentada(repositorio)
    vencedora = repositorio.obter(INQ, "prop-001")
    vencedora.confirmar(em=AGORA, idempotency_key="idem-001")
    vencedora.transicionar("executar", em=AGORA)
    repositorio.salvar(INQ, USR, vencedora)
    vencedora.concluir(
        desfecho=Desfecho(status="executed", outcomes=(("Entregas atrasam", "executed", ""),)),
        em=AGORA,
    )
    repositorio.salvar(INQ, USR, vencedora)

    esperada = repositorio.aguardar_desfecho(INQ, "prop-001")

    assert esperada is not None
    assert esperada.terminal
    assert esperada.como_action_result() == vencedora.como_action_result()


def test_aguardar_desfecho_de_proposta_inexistente_devolve_nada() -> None:
    repositorio = RepositorioDePropostasEmMemoria()

    assert repositorio.aguardar_desfecho(INQ, "prop-que-nao-existe") is None
