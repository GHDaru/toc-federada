"""Limite de taxa da borda federada (RNF-08) — janela deslizante, em memória.

Siglas, uma vez: **APH** — Aplicação ↔ Harness.

A borda `POST /aph/actions/{action_id}` é **a única rota chamada de fora do nosso próprio
frontend**, e por isso nasce com proteção em vez de ganhá-la depois de um incidente.

O que este limitador é: uma janela deslizante por chave, em memória do processo. O que ele
**não** é: proteção distribuída. Com várias réplicas, cada uma conta a sua janela, e o
limite efetivo é o número de réplicas vezes o limite. Está escrito aqui porque limite que
promete mais do que entrega é pior que limite nenhum — quem lê a configuração precisa saber
o que ela vale.
"""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from typing import Callable, Deque


@dataclass
class LimitadorDeTaxa:
    """`permitir(chave)` devolve `False` quando a janela já está cheia."""

    limite: int = 60
    janela_s: float = 60.0
    agora: Callable[[], float] = field(default=None)  # type: ignore[assignment]
    _marcas: dict[str, Deque[float]] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.agora is None:
            import time

            # `monotonic`, não `time()`: relógio de parede pode andar para trás (ajuste de
            # horário, sincronização), e uma janela que anda para trás libera o que devia
            # barrar.
            self.agora = time.monotonic

    def permitir(self, chave: str) -> bool:
        instante = self.agora()
        marcas = self._marcas.setdefault(chave, deque())
        while marcas and instante - marcas[0] > self.janela_s:
            marcas.popleft()
        if len(marcas) >= self.limite:
            return False
        marcas.append(instante)
        return True
