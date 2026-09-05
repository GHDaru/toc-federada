"""A fábrica que escolhe o backend por `DATABASE_URL` — um lugar só sabe da escolha.

É o padrão da fundação (`apps/api/src/ghdaru_api/persistence/factory.py`, leitura apenas),
com a mesma regra central: **`DATABASE_URL` presente → PostgreSQL; ausente → memória**, e o
esquema vem de `alembic upgrade head`, nunca de DDL no arranque. A frase que a fundação
apagou da sua própria docstring — "`create_all` idempotente como rede de segurança" — não é
repetida aqui: `create_all` não é idempotente, é cego, e o brief §4 o proíbe.

O que muda em relação à fundação: `Persistencia` expõe o `motor` além dos repositórios,
porque a suíte de integração precisa conferir no banco o que o repositório escondeu (por
exemplo: a linha continua lá depois da exclusão suave). Expor o motor é deliberado e não
é atalho para o caso de uso — a camada de aplicação só enxerga a porta.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ...dominio.portas import RepositorioDeProjetos
from ..configuracao import Configuracao
from .memoria import RepositorioDeProjetosEmMemoria
from .motor import criar_fabrica_de_sessao, criar_motor
from .repositorio_projetos import RepositorioDeProjetosSQL


@dataclass(frozen=True)
class Persistencia:
    backend: str
    projetos: RepositorioDeProjetos
    motor: Any | None = None


def criar_persistencia(config: Configuracao) -> Persistencia:
    if not config.url_do_banco:
        return Persistencia(backend="memoria", projetos=RepositorioDeProjetosEmMemoria())

    motor = criar_motor(config.url_do_banco, esquema=config.esquema_do_banco)
    sessao = criar_fabrica_de_sessao(motor)
    return Persistencia(
        backend="postgres",
        projetos=RepositorioDeProjetosSQL(sessao),
        motor=motor,
    )
