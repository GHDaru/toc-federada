"""A casca HTTP — só o que o esqueleto precisa: composição e um endpoint de saúde.

As rotas de conteúdo (`/projetos`, `/aph/*`, o fio SSE) nascem nos ciclos 003, 004 e 006.
O que existe aqui é a **composição**: um lugar que lê a configuração, monta a persistência
e o traço, e os entrega. É o único lugar do serviço autorizado a conhecer as quatro
camadas — o contrato P3-3 do `import-linter` diz isso em forma de aptidão.

`/saude` não é enfeite: é o que responde "qual backend está de pé e em que migração", e
foi a ausência dessa resposta que deixou a fundação publicar `persistence: in-memory` com
contas de repositório abertas (spec 056 de lá, lida em
`apps/api/src/ghdaru_api/persistence/factory.py`).
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

from fastapi import FastAPI

from ..dominio.portas import Rastreador, RepositorioDeProjetos
from ..infra.configuracao import Configuracao
from ..infra.observabilidade.otel import configurar_traco
from ..infra.persistencia.fabrica import Persistencia, criar_persistencia
from ..infra.relogio import RelogioDoSistema


@dataclass(frozen=True)
class Composicao:
    """Tudo o que a borda monta uma vez e injeta nos casos de uso."""

    config: Configuracao
    persistencia: Persistencia
    rastreador: Rastreador
    relogio: RelogioDoSistema

    @property
    def projetos(self) -> RepositorioDeProjetos:
        return self.persistencia.projetos


def compor(ambiente: dict[str, str] | None = None) -> Composicao:
    # `is None`, e não `ambiente or os.environ`: um dicionário VAZIO é falso em Python, e
    # a versão com `or` fazia "compor sem nenhuma variável" cair silenciosamente no
    # ambiente do processo. O defeito só apareceu porque um `export DATABASE_URL` no shell
    # mudou o resultado de um teste que passava o ambiente explicitamente — que é
    # exatamente a classe de bug que some quando a máquina de quem testa é limpa.
    config = Configuracao.do_ambiente(dict(os.environ if ambiente is None else ambiente))
    return Composicao(
        config=config,
        persistencia=criar_persistencia(config),
        rastreador=configurar_traco(config),
        relogio=RelogioDoSistema(),
    )


def criar_app(ambiente: dict[str, str] | None = None) -> FastAPI:
    composicao = compor(ambiente)
    app = FastAPI(
        title="toc-api",
        version="0.1.0",
        summary="Serviço da toc-federada — Processos de Pensamento da Teoria das Restrições",
    )
    app.state.composicao = composicao

    @app.get("/saude")
    def saude() -> dict[str, Any]:
        # A cadeia de conexão NUNCA sai daqui: `url_redigida` já removeu a credencial (P7).
        return {
            "servico": composicao.config.nome_do_servico,
            "ambiente": composicao.config.ambiente,
            "persistencia": composicao.persistencia.backend,
            "banco": composicao.config.url_redigida,
            "traco": type(composicao.rastreador).__name__,
        }

    return app
