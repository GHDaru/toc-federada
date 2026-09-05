"""Fixtures da suíte de integração — PostgreSQL REAL, nunca SQLite (brief §1).

Como o isolamento entre execuções é feito: cada teste ganha um **esquema** próprio
(`teste_<hex>`), a migração Alembic roda dentro dele pela variável `TOC_DB_SCHEMA`, e o
esquema é derrubado no fim. Assim a suíte não toca o `public` do banco de desenvolvimento
e duas execuções em paralelo não colidem — sem precisar de contêiner (o ambiente medido
no brief §1 tem docker instalado mas SEM daemon).

Se o Postgres não responder, os testes de integração são **pulados com o motivo**, nunca
substituídos por um duplo: um teste de integração que cai em SQLite não integrou nada.
"""
from __future__ import annotations

import os
import subprocess
import uuid
from pathlib import Path

import pytest
from sqlalchemy import create_engine, text

RAIZ_DA_API = Path(__file__).resolve().parents[2]

# A cadeia medida no brief §1. Fica aqui como PADRÃO de desenvolvimento, e é sobreposta
# por `DATABASE_URL` — nenhuma credencial: o cluster local autentica por socket confiado.
URL_PADRAO = "postgresql+psycopg://toc@/toc_federada?host=/var/run/postgresql&port=5433"


def url_do_banco() -> str:
    return os.environ.get("DATABASE_URL") or URL_PADRAO


@pytest.fixture(scope="session")
def url_postgres() -> str:
    url = url_do_banco()
    try:
        motor = create_engine(url, poolclass=None)
        with motor.connect() as conexao:
            conexao.execute(text("select 1"))
        motor.dispose()
    except Exception as erro:  # pragma: no cover - caminho de ambiente ausente
        pytest.skip(f"PostgreSQL indisponível em {url}: {erro}")
    return url


@pytest.fixture()
def esquema_migrado(url_postgres: str):
    """Cria um esquema, roda `alembic upgrade head` DE VERDADE nele, e derruba no fim."""
    nome = f"teste_{uuid.uuid4().hex[:12]}"
    ambiente = {**os.environ, "DATABASE_URL": url_postgres, "TOC_DB_SCHEMA": nome}

    executado = subprocess.run(
        ["alembic", "upgrade", "head"],
        cwd=RAIZ_DA_API,
        env=ambiente,
        capture_output=True,
        text=True,
    )
    if executado.returncode != 0:
        _derruba(url_postgres, nome)
        raise AssertionError(
            f"alembic upgrade head falhou ({executado.returncode}):\n"
            f"{executado.stdout}\n{executado.stderr}"
        )
    try:
        yield nome
    finally:
        _derruba(url_postgres, nome)


def _derruba(url: str, esquema: str) -> None:
    motor = create_engine(url, isolation_level="AUTOCOMMIT")
    with motor.connect() as conexao:
        conexao.execute(text(f'DROP SCHEMA IF EXISTS "{esquema}" CASCADE'))
    motor.dispose()
