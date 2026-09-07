"""Duplo da porta do M5 — a camada de aplicação testa sem banco e sem rede (P3, P4).

Siglas, uma vez neste arquivo: **M5** — Estratégia & Táticas (S&T) · **S&T** — Estratégia
& Táticas (*Strategy & Tactics*) · **M1** — Núcleo de Diagramas Lógicos.

Herda do duplo do M1 (`RepositorioDeProjetosFalso`) e **não** dos duplos das outras
ferramentas: a S&T é a única ferramenta do produto que não participa de encadeamento
nenhum neste ciclo (o vínculo com Árvore de Pré-Requisitos e Árvore de Transição está
fora do round 010, declarado na spec 010). Um duplo que soubesse mais do que o módulo
precisa esconderia esse corte em vez de o mostrar.

O duplo **não** prova persistência: quem prova é `tests/integracao/`, contra o PostgreSQL
real. O que ele prova é a orquestração — span, autorização, ordem das chamadas.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from uuid import UUID

from toc_api.dominio.projeto import Projeto

from .fakes import RepositorioDeProjetosFalso


@dataclass
class RepositorioDaSnTFalso(RepositorioDeProjetosFalso):
    """Conforme à porta `RepositorioDaSnT` **e** à do M1 (listagem, lixeira, restauração)."""

    arvores: dict[UUID, object] = field(default_factory=dict)

    def salvar(self, projeto: Projeto) -> None:
        super().salvar(projeto)
        arvore = self.arvores.get(projeto.id)
        if arvore is not None and arvore.projeto is not projeto:
            arvore.projeto = projeto

    def salvar_snt(self, arvore) -> None:
        self.arvores[arvore.projeto.id] = arvore
        self.itens[arvore.projeto.id] = arvore.projeto

    def obter_snt(self, inquilino_id: str, projeto_id: UUID):
        arvore = self.arvores.get(projeto_id)
        if arvore is None or arvore.projeto.dono.inquilino_id != inquilino_id:
            return None
        return arvore
