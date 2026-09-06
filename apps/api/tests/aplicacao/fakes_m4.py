"""Duplos das portas do M4 — a camada de aplicação testa sem banco e sem rede (P3, P4).

Siglas, uma vez neste arquivo: **M4** — Árvores de Futuro e Implementação · **ARF** —
Árvore da Realidade Futura · **APR** — Árvore de Pré-Requisitos · **AT** — Árvore de
Transição · **ARA** — Árvore da Realidade Atual · **NC** — Nuvem de Conflito.

Herdam do duplo do M3 (`fakes.RepositorioDeNuvemFalso`) pelo mesmo motivo que ele herda do
duplo do M2: **o encadeamento atravessa as cinco ferramentas na mesma operação**. Um duplo
que soubesse só um lado esconderia justamente a costura que o ciclo 008 entrega — e a
suíte ficaria verde sobre a ilha que o defeito D-11 nomeia.

O duplo **não** prova persistência: quem prova é `tests/integracao/`, contra o PostgreSQL
real. O que ele prova é a orquestração — span, autorização, ordem das chamadas.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from uuid import UUID

from toc_api.dominio.projeto import Projeto
from toc_api.dominio.referencia import ReferenciaCruzada

from .fakes import RepositorioDeNuvemFalso


@dataclass
class RepositorioDoM4Falso(RepositorioDeNuvemFalso):
    """Conforme às portas do M4 **e** às do M1, M2 e M3 — a forma que a cadeia exige."""

    arfs: dict[UUID, object] = field(default_factory=dict)
    aprs: dict[UUID, object] = field(default_factory=dict)
    ats: dict[UUID, object] = field(default_factory=dict)
    referencias: dict[UUID, ReferenciaCruzada] = field(default_factory=dict)

    def salvar(self, projeto: Projeto) -> None:
        super().salvar(projeto)
        for guardadas in (self.arfs, self.aprs, self.ats):
            agregado = guardadas.get(projeto.id)
            if agregado is not None and agregado.projeto is not projeto:
                agregado.projeto = projeto

    # -- ARF ---------------------------------------------------------------------
    def salvar_arf(self, arf) -> None:
        self.arfs[arf.projeto.id] = arf
        self.itens[arf.projeto.id] = arf.projeto

    def obter_arf(self, inquilino_id: str, projeto_id: UUID):
        arf = self.arfs.get(projeto_id)
        if arf is None or arf.projeto.dono.inquilino_id != inquilino_id:
            return None
        return arf

    # -- APR ---------------------------------------------------------------------
    def salvar_apr(self, apr) -> None:
        self.aprs[apr.projeto.id] = apr
        self.itens[apr.projeto.id] = apr.projeto

    def obter_apr(self, inquilino_id: str, projeto_id: UUID):
        apr = self.aprs.get(projeto_id)
        if apr is None or apr.projeto.dono.inquilino_id != inquilino_id:
            return None
        return apr

    # -- AT ----------------------------------------------------------------------
    def salvar_at(self, at) -> None:
        self.ats[at.projeto.id] = at
        self.itens[at.projeto.id] = at.projeto

    def obter_at(self, inquilino_id: str, projeto_id: UUID):
        at = self.ats.get(projeto_id)
        if at is None or at.projeto.dono.inquilino_id != inquilino_id:
            return None
        return at

    # -- referências cruzadas ------------------------------------------------------
    def salvar_referencia(self, referencia: ReferenciaCruzada) -> None:
        self.referencias[referencia.id] = referencia

    def obter_referencia(self, inquilino_id: str, referencia_id: UUID):
        referencia = self.referencias.get(referencia_id)
        if referencia is None or referencia.dono.inquilino_id != inquilino_id:
            return None
        return referencia

    def listar_referencias(
        self, inquilino_id: str, *, projeto_id: UUID | None = None
    ) -> list[ReferenciaCruzada]:
        achadas = [
            r for r in self.referencias.values() if r.dono.inquilino_id == inquilino_id
        ]
        if projeto_id is not None:
            achadas = [r for r in achadas if r.toca(projeto_id)]
        return sorted(achadas, key=lambda r: (r.criada_em, str(r.id)))
