"""Objetos de valor do M1 — imutáveis, iguais por valor, sem identidade (spec 004).

Um objeto de valor não é um `float` com nome bonito: é onde a regra do valor mora. Aqui
`PosicaoNoCanvas` recusa o que não é número finito, e `movido_para` devolve valor NOVO —
mover não altera a posição, cria outra. É o que impede a posição de ser mutada por baixo
do agregado, sem passar pelo evento `NoMovido`.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

from .erros import DadoInvalido

# Enum extensível do M1 (spec 004, RN-04): o núcleo conhece `generico` e nada de TOC.
# Quem acrescenta `ara` é o M2, e quem acrescenta `efeito` como tipo de nó é o M2 também.
FERRAMENTA_GENERICA = "generico"
TIPO_DE_NO_PADRAO = "generico"

LIMITE_TITULO = 200
LIMITE_DESCRICAO = 4000
LIMITE_ROTULO = 200
LIMITE_TIPO = 32


def texto(valor: str | None, *, campo: str, minimo: int, maximo: int) -> str:
    """Normaliza e valida texto de domínio. Vazio depois do `strip` é vazio."""
    limpo = (valor or "").strip()
    if len(limpo) < minimo:
        raise DadoInvalido(f"{campo}: mínimo de {minimo} caractere(s)")
    if len(limpo) > maximo:
        raise DadoInvalido(f"{campo}: máximo de {maximo} caracteres")
    return limpo


@dataclass(frozen=True, slots=True)
class PosicaoNoCanvas:
    """`(x, y)` no plano do canvas. Imutável: mover cria valor novo."""

    x: float = 0.0
    y: float = 0.0

    def __post_init__(self) -> None:
        for nome, valor in (("x", self.x), ("y", self.y)):
            if isinstance(valor, bool) or not isinstance(valor, (int, float)):
                raise DadoInvalido(f"posicao.{nome}: precisa ser número")
            if not math.isfinite(float(valor)):
                raise DadoInvalido(f"posicao.{nome}: precisa ser finito")
        object.__setattr__(self, "x", float(self.x))
        object.__setattr__(self, "y", float(self.y))

    def movido_para(self, x: float, y: float) -> PosicaoNoCanvas:
        return PosicaoNoCanvas(x, y)
