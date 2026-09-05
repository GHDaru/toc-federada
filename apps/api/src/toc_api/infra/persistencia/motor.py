"""Um lugar só cria motor e sessão — o padrão lido em `ghdaru`, adaptado.

Diferença deliberada em relação à fundação: lá o esquema é uma constante do código
(`SCHEMA = "ghdaru"`, com o motivo escrito: "ambiente é branch e database, jamais nome de
schema"). Aqui o esquema é **opcional e configurável** por um motivo específico e local:
a suíte de integração roda cada teste num esquema descartável do MESMO banco, porque o
ambiente medido no brief §1 tem docker sem daemon — não há contêiner por teste. Fora do
teste, `TOC_DB_SCHEMA` fica ausente e tudo cai no `public`, como na fundação.
"""
from __future__ import annotations


from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import sessionmaker

from ..configuracao import ESQUEMA_VALIDO


def normalizar_url(url: str) -> str:
    """Aceita `postgres://` (Railway/Neon/Heroku) e força o driver psycopg 3."""
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://") :]
    if url.startswith("postgresql://"):
        url = "postgresql+psycopg://" + url[len("postgresql://") :]
    return url


def criar_motor(url: str, *, esquema: str | None = None) -> Engine:
    argumentos: dict[str, str] = {}
    if esquema:
        if not ESQUEMA_VALIDO.match(esquema):
            raise ValueError(f"esquema inválido: {esquema!r}")
        # `search_path` na conexão: a migração e o repositório enxergam o MESMO esquema
        # sem que nenhuma tabela precise ser qualificada no código.
        argumentos["options"] = f"-csearch_path={esquema}"
    return create_engine(
        normalizar_url(url),
        pool_pre_ping=True,
        future=True,
        connect_args=argumentos,
    )


def criar_fabrica_de_sessao(motor: Engine) -> sessionmaker:
    return sessionmaker(bind=motor, expire_on_commit=False, future=True)
