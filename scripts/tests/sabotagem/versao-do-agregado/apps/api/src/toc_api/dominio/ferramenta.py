"""Raiz de ferramenta sintética nº 1 — estado próprio, com a versão acompanhando.

Cobre os três caminhos que o portão aceita como avanço: a chamada direta
(`marcar`), a delegação ao núcleo pela chave da raiz (`adicionar_efeito`) e o auxiliar
privado cujo chamador já avançou (`_arquivar`).
"""
from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime

from .projeto import Projeto, registrar_raiz_de_ferramenta

FERRAMENTA_SINTETICA = "sintetica"

registrar_raiz_de_ferramenta(FERRAMENTA_SINTETICA, "ProjetoSintetico")


@dataclass(slots=True)
class ProjetoSintetico:
    projeto: Projeto
    _marcados: dict[str, str] = field(default_factory=dict)
    _arquivados: dict[str, str] = field(default_factory=dict)

    @contextmanager
    def _nucleo(self):
        with self.projeto.sob_a_raiz() as nucleo:
            yield nucleo

    def adicionar_efeito(self, titulo: str, *, em: datetime) -> str:
        """Delega ao núcleo: quem avança a versão é o `Projeto`, por dentro."""
        with self._nucleo() as nucleo:
            return nucleo.adicionar_no(titulo, em=em)

    def marcar(self, titulo: str, ficha: str, *, em: datetime) -> None:
        """Estado PRÓPRIO do agregado: a versão tem de acompanhar, ou a escrita se perde."""
        self._marcados[titulo] = ficha
        self.projeto._avancar(em)
        self._arquivar(titulo)

    def resumo(self) -> int:
        """Só lê. Leitura não avança versão — e um portão que exigisse isso seria ignorado."""
        return len(self._marcados)

    def _arquivar(self, titulo: str) -> None:
        """Auxiliar privado: escreve estado próprio, e quem o chama já avançou."""
        self._arquivados[titulo] = self._marcados.get(titulo, "")
