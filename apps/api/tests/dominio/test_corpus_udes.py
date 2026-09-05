"""Corpus sintético do léxico — a aptidão da RNF-07 da spec 005.

"O léxico heurístico por idioma (RF-11) tem cobertura de teste própria com corpus
sintético versionado de UDEs bons e maus — **ampliar o léxico exige ampliar o corpus**."

Esta última frase é o que este arquivo transforma em portão: para cada marcador declarado
em `toc_api.dominio.lexico`, o corpus tem de trazer pelo menos um enunciado que o
contenha e que seja reprovado pela checagem certa. Acrescentar marcador sem caso derruba a
suíte — que é o oposto do que a linhagem permitia, onde a regra era texto de prompt
editável em produção (`tocbuilderv3/constants.ts:341-405`).

O corpus é sintético (ADR 0006): Instituição Horizonte, papéis, nenhum nome de pessoa.

Regra R2 (portão verde declara quanto examinou): este teste imprime o tamanho do que
examinou — quantos casos maus, quantos bons e quantos marcadores cobertos.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from toc_api.dominio.criterios_ude import Veredito, validar_formalmente
from toc_api.dominio.lexico import LEXICO_PT

CORPUS = json.loads(
    (Path(__file__).with_name("corpus_udes.json")).read_text(encoding="utf-8")
)
MAUS = CORPUS["maus"]
BONS = CORPUS["bons"]


def reprovados(texto: str) -> set[str]:
    return {
        v.criterio.codigo
        for v in validar_formalmente(texto).vereditos
        if v.veredito is Veredito.NAO_ATENDE
    }


def test_o_corpus_declara_a_versao_do_lexico_que_cobre():
    """Corpus e léxico andam juntos ou o portão vira decoração."""
    assert CORPUS["versao_do_lexico"] == LEXICO_PT.versao


@pytest.mark.parametrize("caso", MAUS, ids=[c["marcador"] for c in MAUS])
def test_cada_enunciado_mau_reprova_na_checagem_esperada(caso):
    assert caso["marcador"].strip().lower() in caso["texto"].lower()
    assert caso["codigo"] in reprovados(caso["texto"]), caso["texto"]


@pytest.mark.parametrize("texto", BONS)
def test_cada_enunciado_bom_passa_em_todas_as_oito_checagens(texto):
    assert reprovados(texto) == set(), texto


def test_todo_marcador_do_lexico_tem_caso_no_corpus(capsys):
    """A aptidão da RNF-07: marcador sem caso é marcador sem evidência."""
    cobertos = {c["marcador"] for c in MAUS}
    faltando = {}
    total_de_marcadores = 0
    for familia, marcadores in LEXICO_PT.marcadores.items():
        total_de_marcadores += len(marcadores)
        ausentes = [m for m in marcadores if m not in cobertos]
        if ausentes:
            faltando[familia] = ausentes

    with capsys.disabled():
        print(
            f"\n  corpus sintético v{CORPUS['versao_do_lexico']}: {len(MAUS)} enunciados "
            f"maus · {len(BONS)} bons · marcadores lexicais cobertos: "
            f"{total_de_marcadores - sum(len(v) for v in faltando.values())}"
            f"/{total_de_marcadores}"
        )
    assert faltando == {}, f"marcadores sem caso no corpus: {faltando}"
