"""A migração 0007 sobre um banco que já rodou o defeito — ela recusa, e diz o quê.

Siglas, uma vez neste arquivo: **APH** — Aplicação ↔ Harness · **SQL** — *Structured Query
Language* · **FSM** — máquina de estados finitos.

## Por que este arquivo existe

A migração 0007 cria o índice único parcial `(tenant_id, idempotency_key)` que faz a
deduplicação do APH-5.3 ser real. Um banco que rodou o código anterior **já pode conter** os
pares que ela passa a proibir — não é hipótese: o cluster de desenvolvimento deste
repositório trazia `(inq-alfa, k-1)` repetido, e `alembic upgrade head` falhou nele com a
mensagem crua do driver:

```text
sqlalchemy.exc.IntegrityError: (psycopg.errors.UniqueViolation) could not create unique
index "uq_proposta_de_acao_tenant_id_idempotency_key"
DETAIL:  Key (tenant_id, idempotency_key)=(inq-alfa, k-1) is duplicated.
```

Essa mensagem nomeia **um** par e não diz o que fazer. A migração passou a conferir antes e
recusar com a lista e o comando de inspeção — e a recusa é código, não comentário, que é o
que este arquivo prova. Sem ele, a guarda seria uma frase bonita numa docstring.

O caminho é o de um banco de verdade em três passos: migra até 0006, planta a duplicata que
o código antigo produzia, e tenta ir a `head`.

Base sintética (ADR 0006): Instituição Horizonte, personas fictícias.
"""
from __future__ import annotations

import os
import subprocess
import uuid
from pathlib import Path

import pytest
from sqlalchemy import create_engine, text

pytestmark = pytest.mark.integracao

RAIZ_DA_API = Path(__file__).resolve().parents[2]

INQ = "inq-horizonte"
CHAVE = "idem-repetida-pelo-codigo-antigo"


def _alembic(url: str, esquema: str, alvo: str):
    return subprocess.run(
        ["alembic", "upgrade", alvo],
        cwd=RAIZ_DA_API,
        env={**os.environ, "DATABASE_URL": url, "TOC_DB_SCHEMA": esquema},
        capture_output=True,
        text=True,
    )


def _planta_duplicata(url: str, esquema: str) -> None:
    """Duas propostas do MESMO inquilino com a MESMA chave — o que o defeito produzia."""
    motor = create_engine(url)
    with motor.begin() as conexao:
        conexao.execute(text(f'set search_path to "{esquema}"'))
        conexao.execute(
            text(
                "insert into tenant_ref (tenant_id, visto_em) values (:t, now())"
                " on conflict do nothing"
            ),
            {"t": INQ},
        )
        for proposal_id in ("prop-uma", "prop-outra"):
            conexao.execute(
                text(
                    "insert into proposta_de_acao (proposal_id, tenant_id, usuario_id,"
                    " action_id, risk, origem, estado, criada_em, vence_em,"
                    " idempotency_key)"
                    " values (:p, :t, 'usr-facilitadora', 'toc.criar_nos', 'confirm',"
                    " 'ia', 'executed', now(), now() + interval '10 minutes', :k)"
                ),
                {"p": proposal_id, "t": INQ, "k": CHAVE},
            )
    motor.dispose()


def _derruba(url: str, esquema: str) -> None:
    motor = create_engine(url, isolation_level="AUTOCOMMIT")
    with motor.connect() as conexao:
        conexao.execute(text(f'DROP SCHEMA IF EXISTS "{esquema}" CASCADE'))
    motor.dispose()


def test_a_0007_recusa_o_banco_com_chave_repetida_e_nomeia_os_pares(url_postgres):
    esquema = f"teste_{uuid.uuid4().hex[:12]}"
    try:
        ate_0005 = _alembic(url_postgres, esquema, "0006")
        assert ate_0005.returncode == 0, ate_0005.stderr
        _planta_duplicata(url_postgres, esquema)

        tentativa = _alembic(url_postgres, esquema, "head")

        saida = tentativa.stdout + tentativa.stderr
        print(f"\nmigração 0007 sobre banco com duplicata · saída {tentativa.returncode}")
        assert tentativa.returncode != 0, "a migração passou por cima da duplicata"
        assert "0007 recusada" in saida, saida[-2000:]
        assert CHAVE in saida, "a recusa não nomeia o par em colisão"
        assert "NÃO limpa linhas de governança" in saida, saida[-2000:]

        # E a recusa não deixou efeito parcial: nem o índice, nem a versão avançada.
        motor = create_engine(url_postgres)
        with motor.connect() as conexao:
            indices = conexao.execute(
                text(
                    "select indexname from pg_indexes"
                    " where schemaname = :e and tablename = 'proposta_de_acao'"
                ),
                {"e": esquema},
            ).scalars().all()
            versao = conexao.execute(
                text(f'select version_num from "{esquema}".alembic_version')
            ).scalar()
        motor.dispose()
        assert "uq_proposta_de_acao_tenant_id_idempotency_key" not in indices
        assert versao == "0006", versao
    finally:
        _derruba(url_postgres, esquema)


def test_a_0007_passa_quando_as_chaves_sao_distintas_ou_nulas(url_postgres):
    """O outro lado do portão: a migração não é paranoica — ela só recusa o que colide.

    `NULL` não colide com `NULL` (o índice é parcial), então uma base cheia de propostas sem
    chave passa — que é o caso da maioria, já que o §A.6 declara o campo opcional.
    """
    esquema = f"teste_{uuid.uuid4().hex[:12]}"
    try:
        assert _alembic(url_postgres, esquema, "0006").returncode == 0
        motor = create_engine(url_postgres)
        with motor.begin() as conexao:
            conexao.execute(text(f'set search_path to "{esquema}"'))
            conexao.execute(
                text(
                    "insert into tenant_ref (tenant_id, visto_em) values (:t, now())"
                    " on conflict do nothing"
                ),
                {"t": INQ},
            )
            for proposal_id, chave in (
                ("prop-sem-chave-1", None),
                ("prop-sem-chave-2", None),
                ("prop-com-chave", CHAVE),
            ):
                conexao.execute(
                    text(
                        "insert into proposta_de_acao (proposal_id, tenant_id, usuario_id,"
                        " action_id, risk, origem, estado, criada_em, vence_em,"
                        " idempotency_key)"
                        " values (:p, :t, 'usr-facilitadora', 'toc.criar_nos', 'confirm',"
                        " 'ia', 'executed', now(), now() + interval '10 minutes', :k)"
                    ),
                    {"p": proposal_id, "t": INQ, "k": chave},
                )
        motor.dispose()

        subida = _alembic(url_postgres, esquema, "head")
        assert subida.returncode == 0, subida.stdout + subida.stderr

        motor = create_engine(url_postgres)
        with motor.connect() as conexao:
            indices = conexao.execute(
                text(
                    "select indexname from pg_indexes"
                    " where schemaname = :e and tablename = 'proposta_de_acao'"
                ),
                {"e": esquema},
            ).scalars().all()
        motor.dispose()
        print(f"\nmigração 0007 sobre base sem colisão · índices: {sorted(indices)}")
        assert "uq_proposta_de_acao_tenant_id_idempotency_key" in indices
    finally:
        _derruba(url_postgres, esquema)
