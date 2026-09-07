"""Duplo da porta da portabilidade — exportar e importar sem banco (P3, P4).

Siglas, uma vez neste arquivo: **ARA** — Árvore da Realidade Atual · **NC** — Nuvem de
Conflito · **ARF** — Árvore da Realidade Futura · **APR** — Árvore de Pré-Requisitos ·
**AT** — Árvore de Transição · **S&T** — Estratégia & Táticas · **M1..M6** — os módulos
do produto.

A exportação consolidada atravessa **todas** as ferramentas na mesma operação, então o
duplo precisa saber guardar todas — herda do duplo do M4 (que já cobre M1, M2, M3 e as
três árvores) e acrescenta a S&T e a jornada de focalização. Um duplo que soubesse menos
esconderia justamente a costura que este caso de uso entrega.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from uuid import UUID

from toc_api.dominio.projeto import Projeto

from .fakes_m4 import RepositorioDoM4Falso


@dataclass
class RepositorioDaPortabilidadeFalso(RepositorioDoM4Falso):
    """Conforme às portas do M1..M6 — a forma que a portabilidade exige."""

    arvores: dict[UUID, object] = field(default_factory=dict)
    analises: dict[UUID, object] = field(default_factory=dict)

    def salvar(self, projeto: Projeto) -> None:
        super().salvar(projeto)
        for guardadas in (self.arvores, self.analises):
            agregado = guardadas.get(projeto.id)
            if agregado is not None and agregado.projeto is not projeto:
                agregado.projeto = projeto

    # -- S&T (M5) ------------------------------------------------------------------
    def salvar_snt(self, arvore) -> None:
        self.arvores[arvore.projeto.id] = arvore
        self.itens[arvore.projeto.id] = arvore.projeto

    def obter_snt(self, inquilino_id: str, projeto_id: UUID):
        arvore = self.arvores.get(projeto_id)
        if arvore is None or arvore.projeto.dono.inquilino_id != inquilino_id:
            return None
        return arvore

    # -- focalização (M6) ----------------------------------------------------------
    def salvar_focalizacao(self, analise) -> None:
        self.analises[analise.projeto.id] = analise
        self.itens[analise.projeto.id] = analise.projeto

    def obter_focalizacao(self, inquilino_id: str, projeto_id: UUID):
        analise = self.analises.get(projeto_id)
        if analise is None or analise.projeto.dono.inquilino_id != inquilino_id:
            return None
        return analise


def guardar_cadeia(repositorio: RepositorioDaPortabilidadeFalso, cadeia) -> None:
    """Coloca a cadeia sintética inteira no duplo, cada agregado pela porta dele."""
    repositorio.salvar_ara(cadeia.ara)
    repositorio.salvar_nuvem(cadeia.nuvem)
    repositorio.salvar_arf(cadeia.arf)
    repositorio.salvar_apr(cadeia.apr)
    repositorio.salvar_at(cadeia.at)
    for vinculo in cadeia.vinculos:
        repositorio.salvar_referencia(vinculo)
