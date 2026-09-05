"""Configuração do serviço — função pura sobre um mapa, nunca leitura solta de `os.environ`.

Por que recebe o ambiente como argumento em vez de lê-lo: assim a configuração é testável
sem processo e sem monkeypatch, e existe **um** lugar que sabe o nome de cada variável.
É o mesmo motivo pelo qual o `ghdaru` concentra a escolha de backend num módulo só
(`apps/api/src/ghdaru_api/persistence/factory.py`, leitura apenas).

P7 — segredo nunca no cliente: tudo aqui vem de variável de ambiente do SERVIDOR, e o
`__repr__` de `Configuracao` **redige** a cadeia de conexão, porque cadeia de conexão de
produção carrega senha e cai em log por acidente.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Mapping

# Nome de esquema entra em DDL por interpolação (o driver não parametriza identificador),
# então ele é validado aqui e em lugar nenhum mais.
ESQUEMA_VALIDO = re.compile(r"^[a-z_][a-z0-9_]{0,62}$")

VERDADEIROS = {"1", "true", "sim", "on", "yes"}


class ConfiguracaoInvalida(ValueError):
    """Configuração que não pode subir — recusada nomeando o que está errado."""


def _sem_credencial(url: str) -> str:
    """`postgresql+psycopg://usuario:senha@host/base` → `postgresql+psycopg://***@host/base`."""
    return re.sub(r"://[^/@\s]*@", "://***@", url)


@dataclass(frozen=True, slots=True)
class Configuracao:
    url_do_banco: str | None = None
    esquema_do_banco: str | None = None
    nome_do_servico: str = "toc-api"
    ambiente: str = "desenvolvimento"
    otel_ligado: bool = False
    otel_endpoint: str | None = None

    @classmethod
    def do_ambiente(cls, ambiente: Mapping[str, str]) -> "Configuracao":
        url = (ambiente.get("DATABASE_URL") or "").strip() or None
        esquema = (ambiente.get("TOC_DB_SCHEMA") or "").strip() or None
        if esquema and not ESQUEMA_VALIDO.match(esquema):
            raise ConfiguracaoInvalida(
                f"TOC_DB_SCHEMA inválido: {esquema!r} — esperado [a-z_][a-z0-9_]*"
            )
        return cls(
            url_do_banco=url,
            esquema_do_banco=esquema,
            nome_do_servico=(ambiente.get("OTEL_SERVICE_NAME") or "toc-api").strip(),
            ambiente=(ambiente.get("TOC_AMBIENTE") or "desenvolvimento").strip(),
            otel_ligado=(ambiente.get("OTEL_LIGADO") or "").strip().lower() in VERDADEIROS,
            otel_endpoint=(ambiente.get("OTEL_EXPORTER_OTLP_ENDPOINT") or "").strip() or None,
        )

    @property
    def url_redigida(self) -> str:
        return _sem_credencial(self.url_do_banco) if self.url_do_banco else "(ausente)"

    def __repr__(self) -> str:  # pragma: no cover - existe para o log não vazar senha
        return (
            f"Configuracao(url_do_banco={self.url_redigida!r}, "
            f"esquema_do_banco={self.esquema_do_banco!r}, "
            f"nome_do_servico={self.nome_do_servico!r}, ambiente={self.ambiente!r}, "
            f"otel_ligado={self.otel_ligado!r})"
        )
