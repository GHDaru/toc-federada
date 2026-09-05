"""O validador de argumentos — subconjunto de JSON Schema, puro (APH-4.4, RF-07).

Siglas: **JSON** — *JavaScript Object Notation* · **APH** — Aplicação ↔ Harness.

Por que um validador nosso, e não a biblioteca `jsonschema`: o `input_schema` valida os
`args` **no domínio**, e o domínio não importa pacote de terceiro (P3, contrato P3-1 do
`import-linter`). A escolha tem um preço óbvio — um validador caseiro pode validar de
menos — e a defesa contra esse preço está em dois lugares, os dois testados aqui:

1. **Palavra-chave não suportada é ERRO, não silêncio.** Um schema que use `pattern` ou
   `oneOf` faz a construção do catálogo falhar. Um validador que ignora o que não entende
   é o portão verde que não olhou para nada — o defeito que a regra R2 do projeto nomeia.
2. **Paridade com a biblioteca real**, em `test_paridade_com_jsonschema.py`: o mesmo
   corpus passa pelos dois e o veredito tem de ser igual.
"""
from __future__ import annotations

import pytest

from toc_api.dominio.federacao.esquema import (
    PALAVRAS_SUPORTADAS,
    ArgumentosInvalidos,
    EsquemaNaoSuportado,
    validar_contra_esquema,
)

ESQUEMA_DE_CRIAR_NOS = {
    "type": "object",
    "additionalProperties": False,
    "required": ["projeto_id", "nos"],
    "properties": {
        "projeto_id": {"type": "string"},
        "nos": {
            "type": "array",
            "minItems": 1,
            "maxItems": 50,
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["titulo", "tipo"],
                "properties": {
                    "titulo": {"type": "string", "maxLength": 300},
                    "tipo": {"type": "string", "enum": ["ude", "causa", "causa_raiz"]},
                },
            },
        },
    },
}

ARGUMENTOS_VALIDOS = {
    "projeto_id": "11111111-1111-4111-8111-111111111111",
    "nos": [{"titulo": "Entregas atrasam", "tipo": "ude"}],
}


def test_argumentos_validos_passam() -> None:
    validar_contra_esquema(ARGUMENTOS_VALIDOS, ESQUEMA_DE_CRIAR_NOS)


def test_campo_desconhecido_e_recusado_porque_o_esquema_e_fechado() -> None:
    with pytest.raises(ArgumentosInvalidos) as erro:
        validar_contra_esquema(
            {**ARGUMENTOS_VALIDOS, "executar_agora": True}, ESQUEMA_DE_CRIAR_NOS
        )

    assert "executar_agora" in str(erro.value)


def test_campo_obrigatorio_ausente_e_recusado() -> None:
    with pytest.raises(ArgumentosInvalidos) as erro:
        validar_contra_esquema({"projeto_id": "p"}, ESQUEMA_DE_CRIAR_NOS)

    assert "nos" in str(erro.value)


def test_tipo_errado_e_recusado() -> None:
    with pytest.raises(ArgumentosInvalidos):
        validar_contra_esquema({"projeto_id": 7, "nos": [{"titulo": "t", "tipo": "ude"}]}, ESQUEMA_DE_CRIAR_NOS)


def test_enum_fora_do_conjunto_e_recusado() -> None:
    with pytest.raises(ArgumentosInvalidos) as erro:
        validar_contra_esquema(
            {"projeto_id": "p", "nos": [{"titulo": "t", "tipo": "injecao"}]},
            ESQUEMA_DE_CRIAR_NOS,
        )

    assert "tipo" in str(erro.value)


def test_lote_vazio_e_recusado_por_min_items() -> None:
    with pytest.raises(ArgumentosInvalidos):
        validar_contra_esquema({"projeto_id": "p", "nos": []}, ESQUEMA_DE_CRIAR_NOS)


def test_lote_acima_do_teto_e_recusado_por_max_items() -> None:
    grande = [{"titulo": f"n{i}", "tipo": "ude"} for i in range(51)]

    with pytest.raises(ArgumentosInvalidos):
        validar_contra_esquema({"projeto_id": "p", "nos": grande}, ESQUEMA_DE_CRIAR_NOS)


def test_texto_acima_do_teto_e_recusado_por_max_length() -> None:
    with pytest.raises(ArgumentosInvalidos):
        validar_contra_esquema(
            {"projeto_id": "p", "nos": [{"titulo": "x" * 301, "tipo": "ude"}]},
            ESQUEMA_DE_CRIAR_NOS,
        )


def test_booleano_nao_e_inteiro() -> None:
    """`True` é `int` em Python, e um validador ingênuo aceita `True` onde pede número.

    O defeito é invisível até alguém propor `{"limite": true}` e a ação executar com 1.
    """
    with pytest.raises(ArgumentosInvalidos):
        validar_contra_esquema({"limite": True}, {"type": "object", "properties": {"limite": {"type": "integer"}}})


def test_palavra_chave_nao_suportada_falha_alto_em_vez_de_validar_de_menos() -> None:
    """O ponto central: um schema que este validador não entende **não** passa batido."""
    esquema = {"type": "object", "properties": {"nome": {"type": "string", "pattern": "^a"}}}

    with pytest.raises(EsquemaNaoSuportado) as erro:
        validar_contra_esquema({"nome": "abc"}, esquema)

    assert "pattern" in str(erro.value)


def test_combinador_nao_suportado_falha_alto() -> None:
    for combinador in ("oneOf", "anyOf", "allOf", "not", "$ref"):
        with pytest.raises(EsquemaNaoSuportado):
            validar_contra_esquema({}, {"type": "object", combinador: []})


def test_additional_properties_verdadeiro_e_recusado_como_esquema() -> None:
    """Só `additionalProperties: false` é suportado — um `input_schema` aberto seria
    superfície executável sem contrato, e o APH-4.1 diz que o catálogo é a única."""
    with pytest.raises(EsquemaNaoSuportado):
        validar_contra_esquema({}, {"type": "object", "additionalProperties": True})


def test_a_lista_de_palavras_suportadas_e_publica_e_pequena() -> None:
    """A lista existe para ser lida por quem escreve uma ação nova."""
    assert "type" in PALAVRAS_SUPORTADAS
    assert "pattern" not in PALAVRAS_SUPORTADAS
