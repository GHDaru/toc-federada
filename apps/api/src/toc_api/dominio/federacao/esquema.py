"""Validador do subconjunto de JSON Schema usado pelos `input_schema` do catálogo.

Siglas, uma vez: **JSON** — *JavaScript Object Notation* · **APH** — Aplicação ↔ Harness.

**Por que existe.** O APH-4.4 quer *uma fonte com três projeções*: o mesmo `input_schema`
valida os `args` da proposta, vira a ferramenta que a fundação entrega ao modelo e entra
no manifesto. A validação é decisão de **domínio** — recusar argumento inválido é regra de
negócio, não detalhe de transporte —, e o domínio deste projeto não importa pacote de
terceiro (P3; contrato P3-1 do `import-linter`). Daí um validador pequeno e nosso.

**O risco óbvio, e como ele é fechado.** Validador caseiro tende a validar de menos, e
validar de menos é pior do que não validar, porque produz um verde falso. Duas defesas:

1. **Palavra-chave desconhecida é `EsquemaNaoSuportado`** — o schema não passa, a ação
   nem entra no catálogo. Nada é ignorado em silêncio. Esta é a diferença entre um portão
   e um adereço (regra R2 do `CLAUDE.md`).
2. **Paridade medida com a biblioteca real** (`jsonschema`, dependência só de teste):
   `tests/federacao/test_paridade_com_jsonschema.py` roda o mesmo corpus nos dois e exige
   o mesmo veredito, caso a caso.

O subconjunto é deliberadamente pequeno: se um dia uma ação precisar de `pattern`, a
palavra entra aqui **com teste**, e não por omissão.
"""
from __future__ import annotations

from typing import Any, Mapping, Sequence

from ..erros import DadoInvalido, ErroDeDominio

PALAVRAS_SUPORTADAS: frozenset[str] = frozenset(
    {
        "type",
        "properties",
        "required",
        "additionalProperties",
        "items",
        "enum",
        "minItems",
        "maxItems",
        "maxLength",
        "minLength",
        "description",
        "title",
    }
)

TIPOS = {
    "object": Mapping,
    "array": (list, tuple),
    "string": str,
    "boolean": bool,
    "number": (int, float),
    "integer": int,
}


class ArgumentosInvalidos(DadoInvalido):
    """Os `args` não casam com o `input_schema` da ação. Recusa com caminho do campo."""

    def __init__(self, caminho: str, detalhe: str) -> None:
        onde = caminho or "(raiz)"
        super().__init__(f"{onde}: {detalhe}")
        self.caminho = caminho
        self.detalhe = detalhe


class EsquemaNaoSuportado(ErroDeDominio):
    """O `input_schema` usa uma construção que este validador não implementa.

    É erro do **autor da ação**, não do usuário — e ele aparece na construção do catálogo,
    antes de qualquer proposta existir.
    """


def _exigir_suportado(esquema: Mapping[str, Any], caminho: str) -> None:
    desconhecidas = sorted(set(esquema) - PALAVRAS_SUPORTADAS)
    if desconhecidas:
        raise EsquemaNaoSuportado(
            f"{caminho or '(raiz)'}: palavra(s) de JSON Schema não suportada(s) "
            f"{desconhecidas} — acrescente-as a PALAVRAS_SUPORTADAS **com teste**, "
            "nunca ignore em silêncio"
        )
    if "additionalProperties" in esquema and esquema["additionalProperties"] is not False:
        raise EsquemaNaoSuportado(
            f"{caminho or '(raiz)'}: só `additionalProperties: false` é suportado — "
            "um input_schema aberto seria superfície executável sem contrato (APH-4.1)"
        )


def _e_do_tipo(valor: Any, tipo: str) -> bool:
    esperado = TIPOS[tipo]
    if tipo in {"integer", "number"}:
        # `True` é instância de `int` em Python. Um validador que não sabe disso aceita
        # `{"limite": true}` onde o contrato pede número — e a ação executa com 1.
        return not isinstance(valor, bool) and isinstance(valor, esperado)
    if tipo == "object":
        return isinstance(valor, Mapping)
    if tipo == "array":
        return isinstance(valor, (list, tuple)) and not isinstance(valor, (str, bytes))
    return isinstance(valor, esperado)


def validar_contra_esquema(valor: Any, esquema: Mapping[str, Any], caminho: str = "") -> None:
    """Valida `valor` contra `esquema`. Silêncio é aprovação; recusa é exceção tipada."""
    if not isinstance(esquema, Mapping):
        raise EsquemaNaoSuportado(f"{caminho or '(raiz)'}: esquema não é objeto")
    _exigir_suportado(esquema, caminho)

    tipo = esquema.get("type")
    if tipo is not None:
        if not isinstance(tipo, str) or tipo not in TIPOS:
            raise EsquemaNaoSuportado(f"{caminho or '(raiz)'}: `type` {tipo!r} não suportado")
        if not _e_do_tipo(valor, tipo):
            raise ArgumentosInvalidos(
                caminho, f"esperado {tipo}, recebido {type(valor).__name__}"
            )

    if "enum" in esquema:
        permitidos = esquema["enum"]
        if not isinstance(permitidos, Sequence) or isinstance(permitidos, (str, bytes)):
            raise EsquemaNaoSuportado(f"{caminho or '(raiz)'}: `enum` deve ser lista")
        if valor not in permitidos:
            raise ArgumentosInvalidos(caminho, f"valor {valor!r} fora de {list(permitidos)!r}")

    if isinstance(valor, str):
        maximo = esquema.get("maxLength")
        if isinstance(maximo, int) and len(valor) > maximo:
            raise ArgumentosInvalidos(caminho, f"{len(valor)} caracteres acima do teto {maximo}")
        minimo = esquema.get("minLength")
        if isinstance(minimo, int) and len(valor) < minimo:
            raise ArgumentosInvalidos(caminho, f"{len(valor)} caracteres abaixo de {minimo}")

    if isinstance(valor, (list, tuple)):
        minimo = esquema.get("minItems")
        if isinstance(minimo, int) and len(valor) < minimo:
            raise ArgumentosInvalidos(caminho, f"{len(valor)} itens; mínimo {minimo}")
        maximo = esquema.get("maxItems")
        if isinstance(maximo, int) and len(valor) > maximo:
            raise ArgumentosInvalidos(caminho, f"{len(valor)} itens; máximo {maximo}")
        item = esquema.get("items")
        if isinstance(item, Mapping):
            for i, elemento in enumerate(valor):
                validar_contra_esquema(elemento, item, f"{caminho}[{i}]")

    if isinstance(valor, Mapping):
        propriedades = esquema.get("properties") or {}
        if not isinstance(propriedades, Mapping):
            raise EsquemaNaoSuportado(f"{caminho or '(raiz)'}: `properties` deve ser objeto")
        for obrigatorio in esquema.get("required") or ():
            if obrigatorio not in valor:
                raise ArgumentosInvalidos(caminho, f"campo obrigatório ausente: {obrigatorio}")
        if esquema.get("additionalProperties") is False:
            sobrando = sorted(set(valor) - set(propriedades))
            if sobrando:
                raise ArgumentosInvalidos(
                    caminho, f"campo(s) fora do contrato da ação: {sobrando}"
                )
        for nome, sub in propriedades.items():
            if nome in valor:
                filho = f"{caminho}.{nome}" if caminho else nome
                validar_contra_esquema(valor[nome], sub, filho)


def exigir_esquema_suportado(esquema: Mapping[str, Any], caminho: str = "") -> None:
    """Percorre o schema inteiro procurando construção não suportada — sem dado nenhum.

    Chamado na construção do catálogo: a ação com schema que não sabemos validar **não
    entra**, e o defeito aparece no arranque, não na primeira proposta.
    """
    if not isinstance(esquema, Mapping):
        raise EsquemaNaoSuportado(f"{caminho or '(raiz)'}: esquema não é objeto")
    _exigir_suportado(esquema, caminho)
    tipo = esquema.get("type")
    if tipo is not None and (not isinstance(tipo, str) or tipo not in TIPOS):
        raise EsquemaNaoSuportado(f"{caminho or '(raiz)'}: `type` {tipo!r} não suportado")
    propriedades = esquema.get("properties") or {}
    if not isinstance(propriedades, Mapping):
        raise EsquemaNaoSuportado(f"{caminho or '(raiz)'}: `properties` deve ser objeto")
    for nome, sub in propriedades.items():
        exigir_esquema_suportado(sub, f"{caminho}.{nome}" if caminho else nome)
    item = esquema.get("items")
    if item is not None:
        exigir_esquema_suportado(item, f"{caminho}[]")
