"""O esqueleto que todo caso de uso herda — e o span que ele abre sozinho (P5).

Por que uma classe-base e não um decorador solto: o P5 diz "sem traço, não está pronta",
e a forma mais barata de garantir isso é tornar o traço parte de COMO se roda um caso de
uso. Quem escrever o próximo caso de uso implementa `executar()`; quem o chama chama
`rodar()`, e o span existe queira o autor ou não.

Recusa também é traço (brief §4: "traço de toda ação, inclusive recusas") — por isso o
`except` marca o span e **reergue**: não há caminho em que engolir a exceção pareça
sucesso.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, ClassVar

from ..dominio.portas import Rastreador, SpanDeTraco

PREFIXO_DO_SPAN = "caso_de_uso."


class CasoDeUso(ABC):
    """Base de todo caso de uso. `nome` é o sufixo do span e entra no contrato."""

    nome: ClassVar[str]

    def __init__(self, *, rastreador: Rastreador) -> None:
        self._rastreador = rastreador

    def rodar(self, *args: Any, **kwargs: Any) -> Any:
        with self._rastreador.span(f"{PREFIXO_DO_SPAN}{self.nome}") as span:
            self.anotar(span, **kwargs)
            try:
                resultado = self.executar(*args, **kwargs)
            except Exception as erro:
                span.atributo("toc.resultado", "erro")
                span.atributo("toc.erro", type(erro).__name__)
                raise
            self.anotar_resultado(span, resultado)
            span.atributo("toc.resultado", "ok")
            return resultado

    def anotar(self, span: SpanDeTraco, **kwargs: Any) -> None:
        """Atributos do span ANTES de executar — para a recusa também os carregar.

        O identificador de inquilino é opaco e não é dado de pessoa (ADR 0006); nome de
        projeto, enunciado e descrição **nunca** entram em span nem em log.
        """
        dono = kwargs.get("dono")
        if dono is not None:
            span.atributo("toc.inquilino_id", dono.inquilino_id)

    def anotar_resultado(self, span: SpanDeTraco, resultado: Any) -> None:
        """Atributos que só existem DEPOIS de executar — o raio de uma exclusão, o
        status a que um Efeito Indesejável (UDE) chegou, o resumo de uma análise.

        Fica aqui, e não dentro de cada `executar()`, para o caso de uso não precisar
        conhecer o span: quem instrumenta é a base (P5), quem decide é o domínio.
        O padrão é não anotar nada — só grandeza, nunca texto de pessoa (ADR 0006).
        """

    @abstractmethod
    def executar(self, *args: Any, **kwargs: Any) -> Any:
        """A regra do caso de uso. Nunca chamada direto: quem chama é `rodar()`."""
