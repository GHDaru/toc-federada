"""Raiz de ferramenta sintética nº 2 — avança pela mutação PÚBLICA do núcleo.

`Projeto.descrever_problema` chama `_avancar` por dentro; exigir uma segunda chamada aqui
faria a versão pular de dois em dois. O portão lê de `projeto.py` quais mutações do núcleo
avançam, em vez de guardar uma lista escrita à mão.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from .projeto import Projeto, registrar_raiz_de_ferramenta

FERRAMENTA_SEGUNDA = "segunda"

registrar_raiz_de_ferramenta(FERRAMENTA_SEGUNDA, "ProjetoSegundo")


@dataclass(slots=True)
class ProjetoSegundo:
    projeto: Projeto
    rotulo: str = ""

    def __post_init__(self) -> None:
        # Construção, não mutação: roda também na reidratação, que é leitura.
        self.rotulo = self.rotulo.strip()

    def descrever(self, rotulo: str, *, em: datetime) -> str:
        self.rotulo = rotulo
        self.projeto.descrever_problema(rotulo, em=em)
        return self.rotulo
