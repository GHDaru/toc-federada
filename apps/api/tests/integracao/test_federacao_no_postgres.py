"""A governança de ação no PostgreSQL real — proposta, traço, isolamento e restrições.

Siglas: **APH** — Aplicação ↔ Harness · **SQL** — *Structured Query Language* · **FSM** —
máquina de estados finitos · **UDE** — Efeito Indesejável.

Testes de integração **de verdade**: banco real, migração `alembic upgrade head` executada
pela fixture, nenhum duplo. O que só se prova aqui, e não com repositório em memória:

- que a migração 0004 cria o esquema da governança e o `downgrade` o desfaz sem resíduo;
- que a proposta **sobrevive ao processo** — reidratada com estado, alvos e desfecho;
- que o `tenant_id` isola de verdade, na consulta, e não por disciplina do chamador;
- que os vocabulários fechados do §A.3 e da FSM são impostos **pelo banco**, além do
  domínio: invariante que só vive no código é invariante que a próxima ferramenta viola.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import create_engine, insert, select, text
from sqlalchemy.exc import IntegrityError

from toc_api.dominio.federacao.proposta import Desfecho, Origem, PropostaDeAcao
from toc_api.dominio.federacao.traco import TracoDeExecucao
from toc_api.infra.federacao.repositorio_sql import (
    RepositorioDePropostasSQL,
    RepositorioDeTracoSQL,
)
from toc_api.infra.persistencia.motor import criar_fabrica_de_sessao, criar_motor
from toc_api.infra.persistencia.tabelas import proposta_de_acao, traco_de_execucao

pytestmark = pytest.mark.integracao

AGORA = datetime(2026, 9, 5, 12, 0, tzinfo=timezone.utc)
HORIZONTE = "inq-horizonte"
OUTRA = "inq-outra-instituicao"


@pytest.fixture()
def repos(url_postgres: str, esquema_migrado: str):
    motor = criar_motor(url_postgres, esquema=esquema_migrado)
    fabrica = criar_fabrica_de_sessao(motor)
    try:
        yield RepositorioDePropostasSQL(fabrica), RepositorioDeTracoSQL(fabrica), motor
    finally:
        motor.dispose()


def _proposta(alvos: tuple[str, ...] = ("UDE 1",), pid: str = "prop-001") -> PropostaDeAcao:
    return PropostaDeAcao.nova(
        proposal_id=pid,
        action_id="toc.criar_nos",
        args={"projeto_id": "p-1", "nos": [{"titulo": a, "tipo": "ude"} for a in alvos]},
        risk="confirm",
        alvos=alvos,
        origem=Origem.IA,
        criada_em=AGORA,
        ttl=timedelta(minutes=10),
        contexto_hash="0123456789abcdef",
    )


def test_a_migracao_0004_cria_as_duas_tabelas_da_governanca(url_postgres, esquema_migrado) -> None:
    motor = create_engine(url_postgres)
    with motor.connect() as conexao:
        tabelas = {
            linha[0]
            for linha in conexao.execute(
                text(
                    "select table_name from information_schema.tables where table_schema = :e"
                ),
                {"e": esquema_migrado},
            )
        }
    motor.dispose()

    assert {"proposta_de_acao", "traco_de_execucao"} <= tabelas
    print(f"migração 0004: {len(tabelas)} tabela(s) no esquema {esquema_migrado}: {sorted(tabelas)}")


def test_a_proposta_sobrevive_ao_processo_com_estado_alvos_e_desfecho(repos) -> None:
    propostas, _, _ = repos
    proposta = _proposta(alvos=("UDE 1", "UDE 2"))
    propostas.salvar(HORIZONTE, "usr-facilitadora", proposta)

    proposta.apresentar(em=AGORA)
    proposta.confirmar(em=AGORA)
    proposta.transicionar("executar", em=AGORA)
    proposta.concluir(
        desfecho=Desfecho(
            status="failed",
            outcomes=(("UDE 1", "executed", ""), ("UDE 2", "failed", "título duplicado")),
        ),
        em=AGORA,
    )
    propostas.salvar(HORIZONTE, "usr-facilitadora", proposta)

    # Processo novo: outro repositório sobre o mesmo banco.
    de_volta = propostas.obter(HORIZONTE, "prop-001")

    assert de_volta is not None
    assert de_volta.estado == "failed"
    assert de_volta.alvos == ("UDE 1", "UDE 2")
    assert de_volta.risk == "confirm"
    assert de_volta.origem is Origem.IA
    assert de_volta.contexto_hash == "0123456789abcdef"
    assert de_volta.desfecho.status == "failed"
    assert de_volta.desfecho.outcomes == (
        ("UDE 1", "executed", ""),
        ("UDE 2", "failed", "título duplicado"),
    )
    assert de_volta.execucoes == 1
    # E o TTL volta do par (criada_em, vence_em), não de um campo de duração gravado:
    # duração gravada e instantes gravados divergem no primeiro fuso horário.
    assert de_volta.ttl == timedelta(minutes=10)


def test_proposta_de_outro_inquilino_nao_atravessa_a_fronteira(repos) -> None:
    propostas, _, _ = repos
    propostas.salvar(HORIZONTE, "usr-facilitadora", _proposta())

    assert propostas.obter(HORIZONTE, "prop-001") is not None
    assert propostas.obter(OUTRA, "prop-001") is None
    assert propostas.listar_pendentes(OUTRA) == []


def test_apenas_as_pendentes_do_inquilino_aparecem(repos) -> None:
    propostas, _, _ = repos
    pendente = _proposta(pid="prop-pendente")
    pendente.apresentar(em=AGORA)
    propostas.salvar(HORIZONTE, "usr-facilitadora", pendente)
    decidida = _proposta(pid="prop-decidida")
    decidida.apresentar(em=AGORA)
    decidida.negar(em=AGORA)
    propostas.salvar(HORIZONTE, "usr-facilitadora", decidida)
    de_outra = _proposta(pid="prop-de-outra")
    de_outra.apresentar(em=AGORA)
    propostas.salvar(OUTRA, "usr-outra", de_outra)

    achadas = propostas.listar_pendentes(HORIZONTE)

    assert [p.proposal_id for p in achadas] == ["prop-pendente"]


def test_o_traco_e_somente_acrescimo_e_escopado(repos) -> None:
    _, tracos, _ = repos
    for i, (desfecho, inquilino) in enumerate(
        [("executed", HORIZONTE), ("denied", HORIZONTE), ("expired", OUTRA)]
    ):
        tracos.registrar(
            TracoDeExecucao(
                proposal_id=f"prop-{i}",
                action_id="toc.criar_nos",
                desfecho=desfecho,
                inquilino_id=inquilino,
                usuario_id="usr-facilitadora" if inquilino == HORIZONTE else "usr-outra",
                origem=Origem.IA,
                instante=AGORA + timedelta(seconds=i),
                motivo="registro sintético",
            )
        )

    do_horizonte = tracos.listar(HORIZONTE)

    assert [t.desfecho for t in do_horizonte] == ["executed", "denied"]
    assert [t.desfecho for t in tracos.listar(OUTRA)] == ["expired"]
    assert tracos.listar(HORIZONTE, usuario_id="usr-ninguem") == []
    # A ausência que é o requisito: o repositório não expõe alteração nem remoção.
    assert not hasattr(tracos, "atualizar")
    assert not hasattr(tracos, "remover")


def test_o_desfecho_por_alvo_volta_do_banco_intacto(repos) -> None:
    _, tracos, _ = repos
    tracos.registrar(
        TracoDeExecucao(
            proposal_id="prop-lote",
            action_id="toc.criar_nos",
            desfecho="failed",
            inquilino_id=HORIZONTE,
            usuario_id="usr-facilitadora",
            origem=Origem.HUMANO,
            instante=AGORA,
            outcomes=(("UDE 1", "executed", ""), ("UDE 2", "failed", "mãe inexistente")),
        )
    )

    linha = tracos.listar(HORIZONTE)[0]

    assert linha.outcomes == (("UDE 1", "executed", ""), ("UDE 2", "failed", "mãe inexistente"))
    assert linha.origem is Origem.HUMANO


def test_o_banco_recusa_estado_fora_da_fsm(repos) -> None:
    """A restrição `estado_da_fsm` imposta pelo banco, além do domínio."""
    _, _, motor = repos
    with pytest.raises(IntegrityError):
        with motor.begin() as conexao:
            conexao.execute(
                insert(proposta_de_acao).values(
                    proposal_id="prop-torta",
                    tenant_id=HORIZONTE,
                    usuario_id="usr",
                    action_id="toc.criar_nos",
                    risk="confirm",
                    origem="ia",
                    estado="stale",  # o estado que esta aplicação NÃO adota (RF-11)
                    criada_em=AGORA,
                    vence_em=AGORA + timedelta(minutes=10),
                )
            )


def test_o_banco_recusa_desfecho_fora_do_vocabulario_do_a3(repos) -> None:
    from uuid import uuid4

    _, _, motor = repos
    with pytest.raises(IntegrityError):
        with motor.begin() as conexao:
            conexao.execute(
                insert(traco_de_execucao).values(
                    id=uuid4(),
                    proposal_id="prop-x",
                    action_id="toc.criar_nos",
                    desfecho="quase",
                    tenant_id=HORIZONTE,
                    usuario_id="usr",
                    origem="ia",
                    instante=AGORA,
                )
            )


def test_o_banco_recusa_origem_fora_do_vocabulario(repos) -> None:
    _, _, motor = repos
    with pytest.raises(IntegrityError):
        with motor.begin() as conexao:
            conexao.execute(
                insert(proposta_de_acao).values(
                    proposal_id="prop-origem-torta",
                    tenant_id=HORIZONTE,
                    usuario_id="usr",
                    action_id="toc.criar_nos",
                    risk="confirm",
                    origem="robo",
                    estado="proposed",
                    criada_em=AGORA,
                    vence_em=AGORA + timedelta(minutes=10),
                )
            )


def test_salvar_duas_vezes_atualiza_e_nao_duplica(repos) -> None:
    propostas, _, motor = repos
    proposta = _proposta()
    propostas.salvar(HORIZONTE, "usr-facilitadora", proposta)
    proposta.apresentar(em=AGORA)
    propostas.salvar(HORIZONTE, "usr-facilitadora", proposta)

    with motor.connect() as conexao:
        linhas = conexao.execute(
            select(proposta_de_acao.c.proposal_id, proposta_de_acao.c.estado)
        ).all()

    assert linhas == [("prop-001", "awaiting_approval")]
