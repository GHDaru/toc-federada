"""O traço de execução — existe para **100%** das ações, inclusive as recusadas (APH-5.5).

Siglas, uma vez: **APH** — Aplicação ↔ Harness · **OTel** — OpenTelemetry.

A cláusula é dura e vale a pena citar: *"ação sem traço é ação não governada, e DEVE ser
rejeitada"*. Daí o desenho: o traço não é um efeito colateral que o caso de uso lembra de
produzir — é o objeto que **precede** o efeito. `exigir_traco` é chamado antes de tocar o
domínio, e a sabotagem que o remove derruba os testes de execução (RF-21, DoD 5).

Entidade **somente-acréscimo**: um traço registrado não se corrige, se sucede. É a mesma
disciplina do parecer de Efeito Indesejável (spec 005, RF-13) e do índice de decisões do
método — o que aconteceu não se reescreve.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from ..erros import ErroDeDominio
from .proposta import Origem, PropostaDeAcao

# O vocabulário fechado dos desfechos (§A.3) — o mesmo do `action_result`.
DESFECHOS: frozenset[str] = frozenset(
    {"executed", "failed", "denied", "cancelled", "expired"}
)


class AcaoSemTraco(ErroDeDominio):
    """Execução tentada sem traço — rejeitada **antes** do efeito (APH-5.5)."""


@dataclass(frozen=True, slots=True)
class TracoDeExecucao:
    """Uma linha de auditoria. Escopada por inquilino e usuário (APH-7.4)."""

    proposal_id: str
    action_id: str
    desfecho: str
    inquilino_id: str
    usuario_id: str
    origem: Origem
    instante: datetime
    trace_id: str = ""
    motivo: str = ""
    outcomes: tuple[tuple[str, str, str], ...] = ()

    def __post_init__(self) -> None:
        if self.desfecho not in DESFECHOS:
            raise ValueError(f"desfecho {self.desfecho!r} fora de {sorted(DESFECHOS)} (§A.3)")
        if not self.inquilino_id or not self.usuario_id:
            raise ValueError(
                "traço sem inquilino ou sem usuário — auditoria sem escopo é auditoria "
                "que não responde 'o que a IA fez neste projeto' (APH-7.4)"
            )

    @classmethod
    def da_proposta(
        cls,
        proposta: PropostaDeAcao,
        *,
        inquilino_id: str,
        usuario_id: str,
        instante: datetime,
        trace_id: str = "",
        motivo: str = "",
    ) -> "TracoDeExecucao":
        desfecho = proposta.desfecho
        return cls(
            proposal_id=proposta.proposal_id,
            action_id=proposta.action_id,
            desfecho=desfecho.status if desfecho else proposta.estado,
            inquilino_id=inquilino_id,
            usuario_id=usuario_id,
            origem=proposta.origem,
            instante=instante,
            trace_id=trace_id,
            motivo=motivo or (desfecho.mensagem if desfecho else ""),
            outcomes=desfecho.outcomes if desfecho else (),
        )

    def como_dicionario(self) -> dict[str, Any]:
        return {
            "proposal_id": self.proposal_id,
            "action_id": self.action_id,
            "desfecho": self.desfecho,
            "origem": self.origem.value,
            "instante": self.instante.isoformat(),
            "trace_id": self.trace_id,
            "motivo": self.motivo,
            "outcomes": [
                {"target": alvo, "status": status, "message": msg}
                for alvo, status, msg in self.outcomes
            ],
        }
