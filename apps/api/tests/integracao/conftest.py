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


def liberar_conexoes(clientes) -> None:
    """Devolve ao cluster as conexões ociosas dos clientes já abertos.

    Cada `criar_app` monta o seu motor, e o motor guarda um *pool* — cinco conexões por
    aplicação, no padrão do SQLAlchemy. Um teste que abre uma aplicação por etapa (é assim
    que se prova que o estado está no banco, e não na memória do processo) chega a segurar
    dezenas, e o cluster de desenvolvimento responde `FATAL: sorry, too many clients
    already` — medido, e por um motivo que não é o que o teste mede.

    `Engine.dispose()` fecha o *pool* **sem invalidar o motor**: um cliente liberado que
    volte a ser usado simplesmente abre conexão nova. Por isso é seguro liberar os
    anteriores a cada nova aplicação, em vez de só no fim.
    """
    for cliente in clientes:
        motor = getattr(cliente.app.state.composicao.persistencia, "motor", None)
        if motor is not None:
            motor.dispose()


@pytest.fixture(autouse=True)
def devolver_conexoes_ao_cluster():
    """Todo motor criado durante um teste devolve o *pool* ao cluster quando ele acaba.

    ── O defeito que esta fixture existe para não deixar voltar ───────────────────────

    Cada `criar_app` monta um motor, e cada motor guarda um *pool* (cinco conexões, mais
    até dez de transbordo, no padrão do SQLAlchemy). Uma aplicação por etapa é
    deliberado — é assim que se prova que o estado está no banco e não na memória do
    processo —, mas o *pool* só era devolvido nos cinco arquivos que chamavam
    `liberar_conexoes` **à mão**; os outros quinze seguravam as conexões até a coleta de
    lixo, que não é determinística.

    O resultado, medido: `max_connections = 100` neste cluster de desenvolvimento, e a
    suíte inteira caindo com `FATAL: sorry, too many clients already` — **111 ocorrências
    numa execução, 5 falhas e 51 erros**, e a execução imediatamente anterior, sobre o
    mesmo código, verde com 1593 testes. Suíte que falha em ordem aleatória não é
    evidência de nada: o vermelho não fala do que o teste mede, e o verde não prova que
    o defeito não está lá.

    `Engine.dispose()` fecha o *pool* **sem invalidar o motor** — quem voltar a usá-lo
    abre conexão nova —, então liberar ao fim de cada teste é seguro inclusive para
    cliente de escopo de módulo.
    """
    from toc_api.infra.persistencia import motor as modulo_do_motor

    criados: list = []
    original = modulo_do_motor.create_engine

    def registrando(*args, **kwargs):
        criado = original(*args, **kwargs)
        criados.append(criado)
        return criado

    modulo_do_motor.create_engine = registrando
    try:
        yield criados
    finally:
        modulo_do_motor.create_engine = original
        for criado in criados:
            criado.dispose()
