"""Adaptador da porta `Relogio`. O único lugar do serviço que lê o relógio do sistema."""
from __future__ import annotations

from datetime import datetime, timezone


class RelogioDoSistema:
    """Sempre com fuso: instante ingênuo em banco é bug esperando o horário de verão."""

    def agora(self) -> datetime:
        return datetime.now(timezone.utc)


class RelogioFixo:
    """Relógio parado, para ensaios e para o `seed` de fixtures sintéticas."""

    def __init__(self, instante: datetime) -> None:
        self._instante = instante

    def agora(self) -> datetime:
        return self._instante
