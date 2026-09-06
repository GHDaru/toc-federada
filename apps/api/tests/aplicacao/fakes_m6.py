"""Duplos das portas do M6 — a camada de aplicação testa sem banco e sem rede (P3, P4).

Siglas, uma vez neste arquivo: **M6** — Focalização · **M1** — Núcleo de Diagramas
Lógicos · **ARA** — Árvore da Realidade Atual · **RNF** — requisito não funcional.

O duplo conforma à `RepositorioDaJornada`, que é a porta composta que a validação de
vínculo exige (RNF-04): ler o projeto de destino pelo NÚCLEO e gravar a análise. Ele
filtra por inquilino como o adaptador SQL — um duplo mais permissivo que o real deixa a
suíte verde sobre um isolamento que não existe.

O duplo **não** prova persistência: quem prova é `tests/integracao/`, contra o PostgreSQL
real. O que ele prova é a orquestração — span, autorização, validação de borda.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from uuid import UUID

from toc_api.dominio.focalizacao import AnaliseDeFocalizacao

from .fakes import RepositorioDeProjetosFalso


@dataclass
class RepositorioDaJornadaFalso(RepositorioDeProjetosFalso):
    """Conforme à `RepositorioDeFocalizacao` **e** à `RepositorioDeProjetos` do M1."""

    analises: dict[UUID, AnaliseDeFocalizacao] = field(default_factory=dict)

    def salvar_focalizacao(self, analise: AnaliseDeFocalizacao) -> None:
        self.analises[analise.projeto.id] = analise
        self.itens[analise.projeto.id] = analise.projeto

    def obter_focalizacao(
        self, inquilino_id: str, projeto_id: UUID
    ) -> AnaliseDeFocalizacao | None:
        achada = self.analises.get(projeto_id)
        if achada is None or achada.projeto.dono.inquilino_id != inquilino_id:
            return None
        return achada

    def salvar(self, projeto) -> None:
        super().salvar(projeto)
        analise = self.analises.get(projeto.id)
        if analise is not None and analise.projeto is not projeto:
            analise.projeto = projeto
