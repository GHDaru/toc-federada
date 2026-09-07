"""Codec de domínio: `dataclass` ↔ documento JSON, sem framework nenhum (spec 011, E1.4).

Siglas, uma vez neste arquivo: **JSON** — *JavaScript Object Notation* · **UUID** —
identificador único universal · **ISO** — *International Organization for
Standardization* · **TOC** — Teoria das Restrições.

**Por que ele existe.** A exportação consolidada (RF-31) e a ida e volta que a prova
(RF-32) são **domínio puro**: rodam sem rede e sem banco, porque "o arquivo que sai é
igual ao que entrou" é propriedade do modelo e não do transporte. O P3 proíbe o domínio
de importar Pydantic — logo a parte mecânica da conversão é escrita aqui, uma vez, e os
exportadores por ferramenta ficam com o que é decisão: **quais seções existem, e o que
fica declaradamente de fora**.

**O que ele garante, e é testado:**

1. **Ordem determinística** — os campos saem na ordem de declaração do `dataclass`.
   Exportação que muda de forma entre duas execuções não serve para comparar nem para
   versionar, e comparar dois exports é a primeira coisa que alguém faz com um.
2. **Nada é ignorado em silêncio** — campo desconhecido no documento é **recusado**, não
   descartado. O contraste é a importação da linhagem
   (`tocbuilderv3/components/NodeZoneView.tsx:314-317`), que validava três campos, deixava
   todo o resto passar e reintroduzia o histórico de conversa sem dizer nada. Descarte
   silencioso é defeito mesmo quando é a decisão certa (RN-06).
3. **Tipo que ele não conhece falha alto** — em vez de virar texto por `str()`, que é como
   um `datetime` local vira uma data sem fuso e ninguém percebe até a leitura errada.

**O que ele NÃO faz**: não conhece nenhuma regra da TOC, não sabe o que é um projeto, não
gera identificador e não lê relógio. Ele traduz forma, e só.
"""
from __future__ import annotations

import types
import typing
from dataclasses import MISSING, fields, is_dataclass
from datetime import datetime
from enum import Enum
from uuid import UUID

from .erros import DadoInvalido

#: Os tipos primitivos que atravessam o JSON sem tradução nenhuma.
PRIMITIVOS = (str, int, float, bool)


def codificar(valor: object) -> object:
    """Converte um valor de domínio em algo que `json.dumps` aceita, sem perder ordem."""
    if valor is None or isinstance(valor, bool):
        return valor
    if isinstance(valor, Enum):
        return valor.value
    if isinstance(valor, UUID):
        return str(valor)
    if isinstance(valor, datetime):
        return valor.isoformat()
    if isinstance(valor, PRIMITIVOS):
        return valor
    if is_dataclass(valor) and not isinstance(valor, type):
        return {campo.name: codificar(getattr(valor, campo.name)) for campo in fields(valor)}
    if isinstance(valor, dict):
        return {_chave(chave): codificar(item) for chave, item in valor.items()}
    if isinstance(valor, (list, tuple)):
        return [codificar(item) for item in valor]
    raise DadoInvalido(
        f"serializacao: não sei codificar {type(valor).__name__} — "
        "um tipo novo no domínio entra aqui por decisão, nunca por `str()`"
    )


def _chave(chave: object) -> str:
    if isinstance(chave, UUID):
        return str(chave)
    if isinstance(chave, Enum):
        return str(chave.value)
    if isinstance(chave, str):
        return chave
    if isinstance(chave, int) and not isinstance(chave, bool):
        return str(chave)
    raise DadoInvalido(f"serializacao: chave de dicionário {type(chave).__name__} não é suportada")


def decodificar(tipo: object, dado: object, *, caminho: str = "") -> object:
    """Reconstrói um valor de domínio a partir do documento, recusando o que não bate.

    `caminho` é o rastro do campo (por exemplo `folhas[0].id`), e ele existe para o relato
    de importação poder dizer **onde** o arquivo está errado — campo a campo, que é o
    RF-27 da spec 011 e o defeito exato que a caixa de alerta genérica da linhagem tinha.
    """
    origem = typing.get_origin(tipo)

    # `X | None` e `Optional[X]`: o documento pode trazer nulo, e nulo é o valor.
    if origem in (typing.Union, types.UnionType):
        argumentos = [a for a in typing.get_args(tipo) if a is not type(None)]
        if dado is None:
            return None
        if len(argumentos) == 1:
            return decodificar(argumentos[0], dado, caminho=caminho)
        raise DadoInvalido(f"{caminho or 'valor'}: união de mais de um tipo não é suportada")

    if tipo is typing.Any or tipo is object:
        return dado

    if origem in (tuple, list):
        argumentos = typing.get_args(tipo)
        interno = argumentos[0] if argumentos else typing.Any
        if not isinstance(dado, (list, tuple)):
            raise DadoInvalido(f"{caminho or 'valor'}: esperava lista, veio {type(dado).__name__}")
        itens = [
            decodificar(interno, item, caminho=f"{caminho}[{i}]") for i, item in enumerate(dado)
        ]
        return tuple(itens) if origem is tuple else itens

    if origem is dict:
        argumentos = typing.get_args(tipo) or (str, typing.Any)
        tipo_da_chave, tipo_do_item = argumentos[0], argumentos[1]
        if not isinstance(dado, dict):
            raise DadoInvalido(f"{caminho or 'valor'}: esperava objeto, veio {type(dado).__name__}")
        return {
            _decodificar_chave(tipo_da_chave, chave, caminho): decodificar(
                tipo_do_item, item, caminho=f"{caminho}.{chave}"
            )
            for chave, item in dado.items()
        }

    if isinstance(tipo, type) and issubclass(tipo, Enum):
        try:
            return tipo(dado)
        except ValueError as erro:
            raise DadoInvalido(f"{caminho or 'valor'}: {dado!r} não é {tipo.__name__}") from erro

    if tipo is UUID:
        return _uuid(dado, caminho)

    if tipo is datetime:
        try:
            return datetime.fromisoformat(str(dado))
        except ValueError as erro:
            raise DadoInvalido(f"{caminho or 'valor'}: {dado!r} não é instante ISO 8601") from erro

    if isinstance(tipo, type) and is_dataclass(tipo):
        return _decodificar_dataclass(tipo, dado, caminho)

    if tipo in PRIMITIVOS:
        if tipo is float and isinstance(dado, int) and not isinstance(dado, bool):
            return float(dado)
        if not isinstance(dado, tipo) or (tipo is not bool and isinstance(dado, bool)):
            raise DadoInvalido(
                f"{caminho or 'valor'}: esperava {tipo.__name__}, veio {type(dado).__name__}"
            )
        return dado

    raise DadoInvalido(f"{caminho or 'valor'}: não sei decodificar para {tipo!r}")


def _decodificar_chave(tipo: object, chave: str, caminho: str) -> object:
    if tipo is UUID:
        return _uuid(chave, f"{caminho}.{chave}")
    if isinstance(tipo, type) and issubclass(tipo, Enum):
        return decodificar(tipo, chave, caminho=f"{caminho}.{chave}")
    if tipo is int:
        return int(chave)
    return chave


def _uuid(dado: object, caminho: str) -> UUID:
    try:
        return UUID(str(dado))
    except (ValueError, AttributeError, TypeError) as erro:
        raise DadoInvalido(f"{caminho or 'valor'}: {dado!r} não é UUID") from erro


def _decodificar_dataclass(tipo: type, dado: object, caminho: str) -> object:
    if not isinstance(dado, dict):
        raise DadoInvalido(
            f"{caminho or 'valor'}: esperava objeto de {tipo.__name__}, veio {type(dado).__name__}"
        )
    anotacoes = typing.get_type_hints(tipo)
    declarados = {campo.name for campo in fields(tipo)}
    desconhecidos = sorted(set(dado) - declarados)
    if desconhecidos:
        raise DadoInvalido(
            f"{caminho or tipo.__name__}: campo(s) que {tipo.__name__} não tem: "
            f"{', '.join(desconhecidos)}"
        )
    argumentos: dict[str, object] = {}
    for campo in fields(tipo):
        if not campo.init:
            continue
        sub = f"{caminho}.{campo.name}" if caminho else campo.name
        if campo.name in dado:
            argumentos[campo.name] = decodificar(
                anotacoes[campo.name], dado[campo.name], caminho=sub
            )
            continue
        se_tem_padrao = campo.default is not MISSING or campo.default_factory is not MISSING  # type: ignore[misc]
        if not se_tem_padrao:
            raise DadoInvalido(f"{sub}: campo obrigatório ausente")
    return tipo(**argumentos)


__all__ = ["codificar", "decodificar"]
