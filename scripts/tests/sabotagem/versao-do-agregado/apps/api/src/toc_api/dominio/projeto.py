"""Núcleo sintético — a peça mínima que o portão da versão do agregado precisa ver.

Não é o `Projeto` do serviço: é a miniatura correta de propósito, com as três coisas que
o portão lê — o registro de raízes de ferramenta, o `_avancar` que move a versão, e a
chave `sob_a_raiz` pela qual uma raiz de ferramenta abre o núcleo.

Base sintética (ADR 0006): nenhum nome, enunciado ou data de pessoa real.
"""
from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime

RAIZ_POR_FERRAMENTA: dict[str, str] = {}


def registrar_raiz_de_ferramenta(ferramenta: str, raiz: str) -> None:
    RAIZ_POR_FERRAMENTA[ferramenta] = raiz


@dataclass(slots=True)
class Projeto:
    nome: str
    alterado_em: datetime
    ferramenta: str = "generico"
    descricao_do_problema: str = ""
    versao: int = 1
    titulos: tuple[str, ...] = ()
    versao_lida: int = field(default=0, init=False, repr=False, compare=False)

    @contextmanager
    def sob_a_raiz(self):
        yield self

    def adicionar_no(self, titulo: str, *, em: datetime) -> str:
        self.titulos = self.titulos + (titulo,)
        self._avancar(em)
        return titulo

    def descrever_problema(self, descricao: str, *, em: datetime) -> None:
        self.descricao_do_problema = descricao
        self._avancar(em)

    def confirmar_gravacao(self) -> None:
        self.versao_lida = self.versao

    def _avancar(self, em: datetime) -> None:
        self.versao += 1
        self.alterado_em = em
