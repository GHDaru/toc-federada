"""Ambiente do Alembic — a URL vem do ambiente, nunca do arquivo versionado (P7).

`TOC_DB_SCHEMA` existe para a suíte de integração migrar num esquema descartável do banco
real: o ambiente medido no brief §1 tem docker SEM daemon, então não há contêiner por
teste, e sujar o `public` do banco de desenvolvimento seria pior. Ausente, tudo cai no
`public` — que é o comportamento de produção.
"""
from __future__ import annotations

import os
import sys

from alembic import context
from sqlalchemy import pool, text

from toc_api.infra.configuracao import ESQUEMA_VALIDO
from toc_api.infra.persistencia.motor import criar_motor
from toc_api.infra.persistencia.tabelas import metadados

config = context.config
target_metadata = metadados


def url_obrigatoria() -> str:
    url = (os.environ.get("DATABASE_URL") or "").strip()
    if not url:
        print(
            "✗ DATABASE_URL ausente. A migração roda contra banco de verdade — defina, por "
            "exemplo:\n"
            "  export DATABASE_URL='postgresql+psycopg://toc@/toc_federada"
            "?host=/var/run/postgresql&port=5433'",
            file=sys.stderr,
        )
        raise SystemExit(2)
    return url


def esquema_configurado() -> str | None:
    esquema = (os.environ.get("TOC_DB_SCHEMA") or "").strip() or None
    if esquema and not ESQUEMA_VALIDO.match(esquema):
        print(f"✗ TOC_DB_SCHEMA inválido: {esquema!r}", file=sys.stderr)
        raise SystemExit(2)
    return esquema


def rodar_offline() -> None:
    context.configure(
        url=url_obrigatoria(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        version_table_schema=esquema_configurado(),
    )
    with context.begin_transaction():
        context.run_migrations()


def rodar_online() -> None:
    esquema = esquema_configurado()
    motor = criar_motor(url_obrigatoria(), esquema=esquema)
    motor = motor.execution_options()

    with motor.connect() as conexao:
        if esquema:
            # O esquema é validado por `ESQUEMA_VALIDO` acima — identificador não é
            # parametrizável pelo driver, então a validação é a defesa.
            conexao.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{esquema}"'))
            conexao.commit()
        context.configure(
            connection=conexao,
            target_metadata=target_metadata,
            version_table_schema=esquema,
            compare_type=True,
        )
        with context.begin_transaction():
            context.run_migrations()
    motor.dispose()


if context.is_offline_mode():
    rodar_offline()
else:
    rodar_online()
