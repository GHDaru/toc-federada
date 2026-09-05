"""Paridade: o validador puro do domínio × a biblioteca `jsonschema` real.

Siglas: **JSON** — *JavaScript Object Notation*.

Este é o teste que compra o direito de ter um validador caseiro no domínio (P3 proíbe o
domínio de importar terceiro; a biblioteca entra aqui, que é dependência **de teste**).
Ele roda o **mesmo corpus** nos dois e exige o mesmo veredito caso a caso — e imprime
quantos casos examinou, porque verde sem denominador não é evidência (regra R2).

O corpus não é inventado do zero: os schemas são os `input_schema` reais do catálogo
`toc.*` (`dominio/federacao/catalogo.py`), que são os mesmos do
`specs/006-acoes-governadas-e-snapshot/contracts/manifesto.json`.
"""
from __future__ import annotations

import copy
from typing import Any

import jsonschema
import pytest

from toc_api.dominio.federacao.catalogo import CATALOGO_TOC
from toc_api.dominio.federacao.esquema import ArgumentosInvalidos, validar_contra_esquema

from ..dominio.test_resultado_de_geracao import BRUTO

UUID_SINTETICO = "11111111-1111-4111-8111-111111111111"

#: O resultado de geração do M3 — a mesma fixture sintética do domínio, reusada aqui para
#: os dois validadores atravessarem um schema ANINHADO (entidades, arestas, injeções).
RESULTADO = copy.deepcopy(BRUTO)
SEM_D_PRIME = copy.deepcopy(BRUTO)
SEM_D_PRIME["entidades"].pop("D_PRIME")
ARESTA_A_MAIS = copy.deepcopy(BRUTO)
ARESTA_A_MAIS["arestas"]["D_Z"] = []
VERSAO_ESTRANHA = {**copy.deepcopy(BRUTO), "versao": "9.9.9"}
TRIZ_INVALIDA = copy.deepcopy(BRUTO)
TRIZ_INVALIDA["arestas"]["D_D_PRIME"][0]["injecoes"][0]["separacao"] = "cor"

# (action_id, args, esperado_valido) — casos válidos e contraexemplos, ação a ação.
CORPUS: list[tuple[str, dict[str, Any], bool]] = [
    ("toc.listar_projetos", {}, True),
    ("toc.listar_projetos", {"ferramenta": "ara"}, True),
    ("toc.listar_projetos", {"ferramenta": 7}, False),
    ("toc.listar_projetos", {"desconhecido": "x"}, False),
    ("toc.sugerir_udes", {"projeto_id": UUID_SINTETICO, "narrativa": "Entregas atrasam."}, True),
    ("toc.sugerir_udes", {"projeto_id": UUID_SINTETICO}, False),
    ("toc.sugerir_udes", {"projeto_id": UUID_SINTETICO, "narrativa": "x" * 8001}, False),
    ("toc.analisar_suficiencia", {"projeto_id": UUID_SINTETICO}, True),
    ("toc.analisar_suficiencia", {}, False),
    (
        "toc.criar_nos",
        {"projeto_id": UUID_SINTETICO, "nos": [{"titulo": "Entregas atrasam", "tipo": "ude"}]},
        True,
    ),
    ("toc.criar_nos", {"projeto_id": UUID_SINTETICO, "nos": []}, False),
    (
        "toc.criar_nos",
        {"projeto_id": UUID_SINTETICO, "nos": [{"titulo": "t", "tipo": "injecao"}]},
        False,
    ),
    (
        "toc.criar_nos",
        {"projeto_id": UUID_SINTETICO, "nos": [{"titulo": "x" * 301, "tipo": "ude"}]},
        False,
    ),
    (
        "toc.criar_nos",
        {
            "projeto_id": UUID_SINTETICO,
            "nos": [{"titulo": "t", "tipo": "ude"}],
            "executar_agora": True,
        },
        False,
    ),
    (
        "toc.criar_nos",
        {"projeto_id": UUID_SINTETICO, "nos": [{"titulo": f"n{i}", "tipo": "ude"} for i in range(51)]},
        False,
    ),
    (
        "toc.criar_arestas",
        {"projeto_id": UUID_SINTETICO, "arestas": [{"origem_id": "a", "destino_id": "b"}]},
        True,
    ),
    (
        "toc.criar_arestas",
        {"projeto_id": UUID_SINTETICO, "arestas": [{"origem_id": "a"}]},
        False,
    ),
    ("toc.atualizar_no", {"projeto_id": UUID_SINTETICO, "no_id": "n1"}, True),
    ("toc.atualizar_no", {"projeto_id": UUID_SINTETICO, "no_id": "n1", "tipo": "causa"}, True),
    ("toc.atualizar_no", {"projeto_id": UUID_SINTETICO, "no_id": "n1", "tipo": "outro"}, False),
    ("toc.excluir_nos", {"projeto_id": UUID_SINTETICO, "no_ids": ["n1", "n2"]}, True),
    ("toc.excluir_nos", {"projeto_id": UUID_SINTETICO, "no_ids": []}, False),
    ("toc.excluir_nos", {"projeto_id": UUID_SINTETICO, "no_ids": [1]}, False),
    ("toc.exportar_projeto", {"projeto_id": UUID_SINTETICO}, True),
    ("toc.exportar_projeto", {"projeto_id": UUID_SINTETICO, "formato": "csv"}, False),
    # M3 — Nuvem de Conflito. O `input_schema` da geração embute o esquema versionado do
    # ResultadoDeGeracao, e é por isso que estes casos importam: eles medem se o validador
    # do domínio recusa exatamente o que a biblioteca recusa num schema ANINHADO — que é
    # onde um validador caseiro costuma passar a mão.
    ("toc.generate_conflict_cloud", {"projeto_id": UUID_SINTETICO, "resultado": RESULTADO}, True),
    (
        "toc.generate_conflict_cloud",
        {"projeto_id": UUID_SINTETICO, "narrativa": "O dilema da expansão.", "resultado": RESULTADO},
        True,
    ),
    ("toc.generate_conflict_cloud", {"projeto_id": UUID_SINTETICO}, False),
    ("toc.generate_conflict_cloud", {"projeto_id": UUID_SINTETICO, "resultado": SEM_D_PRIME}, False),
    ("toc.generate_conflict_cloud", {"projeto_id": UUID_SINTETICO, "resultado": ARESTA_A_MAIS}, False),
    ("toc.generate_conflict_cloud", {"projeto_id": UUID_SINTETICO, "resultado": VERSAO_ESTRANHA}, False),
    ("toc.generate_conflict_cloud", {"projeto_id": UUID_SINTETICO, "resultado": TRIZ_INVALIDA}, False),
    (
        "toc.suggest_assumptions",
        {"projeto_id": UUID_SINTETICO, "aresta": "D_D_PRIME", "texto": "orçamento único"},
        True,
    ),
    (
        "toc.suggest_assumptions",
        {"projeto_id": UUID_SINTETICO, "aresta": "D_Z", "texto": "aresta que não existe"},
        False,
    ),
    ("toc.suggest_assumptions", {"projeto_id": UUID_SINTETICO, "aresta": "A_B", "texto": ""}, False),
    (
        "toc.suggest_injections",
        {"projeto_id": UUID_SINTETICO, "premissa_id": "p1", "texto": "faseamento", "separacao": "tempo"},
        True,
    ),
    (
        "toc.suggest_injections",
        {"projeto_id": UUID_SINTETICO, "premissa_id": "p1", "texto": "faseamento", "separacao": "cor"},
        False,
    ),
    ("toc.suggest_injections", {"projeto_id": UUID_SINTETICO, "texto": "sem premissa"}, False),
]


def _valido_pela_biblioteca(args: dict[str, Any], esquema: dict[str, Any]) -> bool:
    try:
        jsonschema.Draft202012Validator(esquema).validate(args)
    except jsonschema.ValidationError:
        return False
    return True


def _valido_pelo_dominio(args: dict[str, Any], esquema: dict[str, Any]) -> bool:
    try:
        validar_contra_esquema(args, esquema)
    except ArgumentosInvalidos:
        return False
    return True


@pytest.mark.parametrize(("action_id", "args", "esperado"), CORPUS)
def test_os_dois_validadores_concordam(action_id: str, args: dict[str, Any], esperado: bool) -> None:
    esquema = CATALOGO_TOC.acao(action_id).input_schema

    pela_biblioteca = _valido_pela_biblioteca(args, esquema)
    pelo_dominio = _valido_pelo_dominio(args, esquema)

    assert pela_biblioteca == esperado, f"a biblioteca discorda do corpus em {action_id}"
    assert pelo_dominio == pela_biblioteca, (
        f"{action_id}: validador do domínio disse {pelo_dominio}, biblioteca disse "
        f"{pela_biblioteca} — para {args!r}"
    )


def test_o_corpus_examina_toda_acao_do_catalogo_e_diz_quanto() -> None:
    """R2: verde sem denominador não é evidência — o teste imprime o que examinou."""
    acoes_no_corpus = {action_id for action_id, _, _ in CORPUS}
    todas = {a.action_id for a in CATALOGO_TOC.acoes}

    medida = (
        f"paridade jsonschema × domínio: {len(CORPUS)} casos sobre "
        f"{len(acoes_no_corpus)} de {len(todas)} ações do catálogo; "
        f"válidos={sum(1 for _, _, v in CORPUS if v)} inválidos={sum(1 for _, _, v in CORPUS if not v)}"
    )
    print(medida)
    assert todas - acoes_no_corpus == set(), f"ações sem caso de paridade: {todas - acoes_no_corpus}"
    assert f"{len(CORPUS)} casos" in medida
