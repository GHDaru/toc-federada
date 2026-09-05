"""Adaptador OpenTelemetry da porta `Rastreador` (P5 — observabilidade de nascença).

Dois adaptadores, e os dois importam: o real, que abre span de verdade, e o **nulo**, que
é o que roda em teste de aplicação e em qualquer ambiente sem coletor. O nulo não é
desculpa para não instrumentar — é o que permite instrumentar desde o primeiro caso de uso
sem exigir coletor em toda máquina.

Este é o ÚNICO módulo do serviço que importa `opentelemetry`. Os contratos P3-1 e P3-2 do
`import-linter` provam isso a cada portão.
"""
from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator

from ..configuracao import Configuracao


class SpanNulo:
    def atributo(self, chave: str, valor: str | int | float | bool) -> None:
        return None


class RastreadorNulo:
    """Sem coletor. A chamada é idêntica; o custo é uma alocação por caso de uso."""

    @contextmanager
    def span(self, nome: str, **atributos: str | int | float | bool) -> Iterator[SpanNulo]:
        yield SpanNulo()


class SpanOTel:
    def __init__(self, span_real: object) -> None:
        self._span = span_real

    def atributo(self, chave: str, valor: str | int | float | bool) -> None:
        self._span.set_attribute(chave, valor)  # type: ignore[attr-defined]


class RastreadorOTel:
    """Adaptador real. Recebe o tracer pronto — quem o constrói é `configurar_traco`."""

    def __init__(self, tracer: object) -> None:
        self._tracer = tracer

    @contextmanager
    def span(self, nome: str, **atributos: str | int | float | bool) -> Iterator[SpanOTel]:
        with self._tracer.start_as_current_span(nome) as span_real:  # type: ignore[attr-defined]
            envolvido = SpanOTel(span_real)
            for chave, valor in atributos.items():
                envolvido.atributo(chave, valor)
            yield envolvido


def configurar_traco(config: Configuracao):
    """Liga o traço POR CONFIGURAÇÃO e devolve a porta — nunca o SDK.

    `OTEL_LIGADO` desligado (o padrão) devolve `RastreadorNulo`: nenhum provedor global é
    instalado, nada é exportado, e o serviço sobe igual. Ligado, instala um
    `TracerProvider` com `service.name` vindo da configuração e exporta por OTLP se houver
    endpoint; sem endpoint, o provedor existe e os spans ficam em memória — o que é o
    bastante para o teste de instrumentação e não inventa destino.
    """
    if not config.otel_ligado:
        return RastreadorNulo()

    from opentelemetry import trace
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor

    recurso = Resource.create(
        {
            "service.name": config.nome_do_servico,
            "deployment.environment": config.ambiente,
        }
    )
    provedor = TracerProvider(resource=recurso)

    if config.otel_endpoint:
        try:
            from opentelemetry.exporter.otlp.proto.http.trace_exporter import (
                OTLPSpanExporter,
            )
        except ImportError as erro:  # pragma: no cover - depende de extra opcional
            raise RuntimeError(
                "OTEL_EXPORTER_OTLP_ENDPOINT definido mas o exportador OTLP não está "
                f"instalado: {erro}. Instale o extra, ou desligue o endpoint."
            ) from erro
        provedor.add_span_processor(
            BatchSpanProcessor(OTLPSpanExporter(endpoint=config.otel_endpoint))
        )

    trace.set_tracer_provider(provedor)
    return RastreadorOTel(trace.get_tracer(config.nome_do_servico))
