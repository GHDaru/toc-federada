"""Estabelecer identidade — o grant vira Principal, e o grant some (§B.6).

Siglas, uma vez: **APH** — Aplicação ↔ Harness · **TTL** — *Time To Live* (tempo de vida).

O caso de uso é curto de propósito. O que ele garante é a **ordem**: trocar primeiro,
verificar validade depois, e nunca construir identidade a partir do que o handshake disse
(RF-07). O grant entra como argumento e não é guardado em lugar nenhum — nem em atributo,
nem em span, nem em log (RNF-01).
"""
from __future__ import annotations

from ...dominio.federacao.principal import IntrospeccaoInvalida, Principal
from ...dominio.federacao.portas import PortaDeIntrospeccao
from ...dominio.portas import Rastreador, Relogio, SpanDeTraco
from ..casos_de_uso import CasoDeUso


class EstabelecerIdentidade(CasoDeUso):
    nome = "estabelecer_identidade"

    def __init__(
        self, *, rastreador: Rastreador, introspeccao: PortaDeIntrospeccao, relogio: Relogio
    ) -> None:
        super().__init__(rastreador=rastreador)
        self._introspeccao = introspeccao
        self._relogio = relogio

    def anotar(self, span: SpanDeTraco, **kwargs) -> None:
        # O grant NUNCA entra no span. O que entra é que houve uma troca.
        span.atributo("toc.introspeccao", "solicitada")

    def executar(self, *, grant: str) -> Principal:
        principal = self._introspeccao.trocar_grant(grant)
        agora = self._relogio.agora()
        if principal.expirado_em(agora):
            # RF-13: sem renovação por conta própria — não há rota para isso, e inventá-la
            # seria segundo protocolo (P2).
            raise IntrospeccaoInvalida(
                "SESSAO_EXPIRADA", "a identidade venceu; é preciso novo embarque pelo shell"
            )
        return principal

    def anotar_resultado(self, span: SpanDeTraco, resultado: Principal) -> None:
        # Identificador de inquilino é opaco e não é dado de pessoa (ADR 0006); nome e
        # e-mail do usuário não entram em span nenhum.
        if resultado.inquilino_id:
            span.atributo("toc.inquilino_id", resultado.inquilino_id)
        span.atributo("toc.capabilities", len(resultado.capabilities))
        if resultado.capabilities_recusadas:
            # O defeito do hospedeiro aparece aqui — e não vira indisponibilidade nossa.
            span.atributo("toc.capabilities_recusadas", len(resultado.capabilities_recusadas))
