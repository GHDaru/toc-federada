"""Compor o catálogo — o inventário que **este** principal vê (APH-4.3).

Siglas, uma vez: **APH** — Aplicação ↔ Harness.

Uma linha de orquestração sobre uma função pura do domínio. Existe como caso de uso, e não
como chamada direta na rota, por causa do P5: a composição é o que a rota `GET /aph/catalog`
responde, e sem span ninguém consegue explicar por que um dia o catálogo veio menor.
"""
from __future__ import annotations

from typing import Any

from ...dominio.federacao.catalogo import Catalogo
from ...dominio.federacao.principal import Principal
from ...dominio.portas import Rastreador, SpanDeTraco
from ..casos_de_uso import CasoDeUso


class ComporCatalogo(CasoDeUso):
    nome = "compor_catalogo"

    def __init__(self, *, rastreador: Rastreador, catalogo: Catalogo) -> None:
        super().__init__(rastreador=rastreador)
        self._catalogo = catalogo

    def anotar(self, span: SpanDeTraco, **kwargs) -> None:
        principal = kwargs.get("principal")
        if principal is not None and principal.inquilino_id:
            span.atributo("toc.inquilino_id", principal.inquilino_id)

    def executar(self, *, principal: Principal) -> list[dict[str, Any]]:
        return self._catalogo.como_catalogo_servido(principal)

    def anotar_resultado(self, span: SpanDeTraco, resultado: list[dict[str, Any]]) -> None:
        # A contagem é o que responde "por que a ação sumiu?" sem expor o inventário.
        span.atributo("toc.acoes_visiveis", len(resultado))
