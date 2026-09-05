"""Heurísticas de boa formulação — aviso pedagógico, nunca bloqueio (RF-09..RF-11, RN-06).

Siglas, uma vez: **NC** — Nuvem de Conflito · **TOC** — Teoria das Restrições · **UDE** —
Efeito Indesejável · **R2** — a regra "portão verde exige 'quanto ele examinou?'" do
`CLAUDE.md`.

O corpus (`corpus_formulacao.json`) é o mecanismo do M2 reusado: **ampliar a heurística
exige ampliar o corpus** (RNF-08). O teste imprime quantos casos bons e maus examinou —
sem esse número, o verde não é evidência (R2).

A honestidade da heurística é parte do contrato: quando ela não alcança o caso, o veredito
é `indeterminado` e **não** gera aviso (RF-10). Um `indeterminado` silencioso é melhor do
que um aviso errado, porque aviso errado ensina o método errado.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from toc_api.dominio.formulacao import (
    VERSAO_DO_LEXICO_DE_FORMULACAO,
    CodigoDeAviso,
    Negacao,
    avaliar_formulacao,
    avaliar_negacao,
    lexico_de_formulacao,
)
from toc_api.dominio.nuvem import PapelDaEntidade

CORPUS = json.loads((Path(__file__).parent / "corpus_formulacao.json").read_text("utf-8"))


def test_o_corpus_examina_casos_bons_e_maus_nos_dois_idiomas() -> None:
    """R2: o verde diz quanto examinou — e o número sai do próprio corpus."""
    bons = [c for c in CORPUS["casos"] if not c["avisos"]]
    maus = [c for c in CORPUS["casos"] if c["avisos"]]
    idiomas = sorted({c["idioma"] for c in CORPUS["casos"]})

    medida = (
        f"corpus de formulação v{CORPUS['versao']}: {len(CORPUS['casos'])} caso(s) — "
        f"{len(bons)} bem formulado(s), {len(maus)} mal formulado(s); idiomas={idiomas}"
    )
    print(medida)

    assert len(bons) >= 8, medida
    assert len(maus) >= 8, medida
    assert idiomas == ["en", "pt"], medida


def test_cada_caso_do_corpus_recebe_exatamente_os_avisos_declarados() -> None:
    divergentes: list[str] = []
    for caso in CORPUS["casos"]:
        papel = PapelDaEntidade(caso["papel"])
        avisos = avaliar_formulacao(
            papel,
            caso["texto"],
            idioma=caso["idioma"],
            texto_de_d=caso.get("texto_de_d"),
        )
        obtidos = sorted(a.codigo.value for a in avisos)
        if obtidos != sorted(caso["avisos"]):
            divergentes.append(f"{caso['texto']!r} → {obtidos} ≠ {sorted(caso['avisos'])}")

    print(f"casos conferidos: {len(CORPUS['casos'])}; divergentes: {len(divergentes)}")
    assert divergentes == [], divergentes


def test_todo_codigo_de_aviso_tem_pelo_menos_um_caso_no_corpus() -> None:
    """A regra do M2 reusada: heurística sem caso no corpus não entra (RNF-08)."""
    cobertos = {codigo for caso in CORPUS["casos"] for codigo in caso["avisos"]}

    faltando = sorted({c.value for c in CodigoDeAviso} - cobertos)
    print(f"códigos de aviso: {len(CodigoDeAviso)}; cobertos pelo corpus: {len(cobertos)}")
    assert faltando == [], faltando


def test_o_aviso_carrega_explicacao_e_exemplo_e_nunca_bloqueia() -> None:
    """US-05: 'Qualidade' em D avisa que D pede ação — e o texto fica salvo mesmo assim."""
    avisos = avaliar_formulacao(PapelDaEntidade.D, "Qualidade")

    assert [a.codigo for a in avisos] == [CodigoDeAviso.D_PEDE_INFINITIVO]
    aviso = avisos[0]
    print(f"aviso: {aviso.codigo.value} — {aviso.explicacao} (ex.: {aviso.exemplo})")
    assert aviso.explicacao and aviso.exemplo
    assert aviso.papel is PapelDaEntidade.D


def test_entidade_de_objetivo_ou_necessidade_avisa_quando_vem_em_forma_de_acao() -> None:
    for papel in (PapelDaEntidade.A, PapelDaEntidade.B, PapelDaEntidade.C):
        avisos = avaliar_formulacao(papel, "Abrir turmas em três cidades novas")
        assert [a.codigo for a in avisos] == [CodigoDeAviso.PEDE_SUBSTANTIVO], papel


def test_a_negacao_de_d_por_d_linha_tem_tres_vereditos_e_o_indeterminado_e_honesto() -> None:
    d = "Abrir turmas em três cidades novas"

    assert avaliar_negacao(d, "Não abrir turmas em três cidades novas") is Negacao.NEGA
    assert avaliar_negacao(d, "Deixar de abrir turmas em três cidades novas") is Negacao.NEGA
    # Duas ações positivas sobre o mesmo assunto: não é negação, e dá para dizer isso.
    assert avaliar_negacao(d, "Abrir turmas em uma cidade nova") is Negacao.NAO_NEGA
    # Sem marcador e sem palavra em comum: a heurística não alcança — e admite.
    assert avaliar_negacao(d, "Contratar professores efetivos") is Negacao.INDETERMINADO


def test_indeterminado_nao_gera_aviso() -> None:
    """RF-10, última frase — literal."""
    avisos = avaliar_formulacao(
        PapelDaEntidade.D_PRIME,
        "Contratar professores efetivos",
        texto_de_d="Abrir turmas em três cidades novas",
    )

    codigos = [a.codigo for a in avisos]
    print(f"avisos com veredito indeterminado: {codigos}")
    assert CodigoDeAviso.D_LINHA_NAO_NEGA_D not in codigos


def test_d_linha_que_nao_nega_d_recebe_aviso() -> None:
    avisos = avaliar_formulacao(
        PapelDaEntidade.D_PRIME,
        "Abrir turmas em uma cidade nova",
        texto_de_d="Abrir turmas em três cidades novas",
    )

    assert CodigoDeAviso.D_LINHA_NAO_NEGA_D in [a.codigo for a in avisos]


def test_o_lexico_e_dado_versionado_por_idioma_e_idioma_sem_lexico_e_erro() -> None:
    """RF-11: léxico é dado versionado, nunca literal espalhado no código."""
    pt = lexico_de_formulacao("pt")
    en = lexico_de_formulacao("en")

    print(
        f"léxico v{VERSAO_DO_LEXICO_DE_FORMULACAO}: "
        f"pt={len(pt.marcadores_de_negacao)} marcador(es) de negação; "
        f"en={len(en.marcadores_de_negacao)}"
    )
    assert pt.idioma == "pt" and en.idioma == "en"
    assert pt.versao == en.versao == VERSAO_DO_LEXICO_DE_FORMULACAO
    assert pt.marcadores_de_negacao and en.marcadores_de_negacao

    with pytest.raises(KeyError):
        lexico_de_formulacao("tlh")


def test_a_heuristica_e_pura_e_nao_toca_o_agregado() -> None:
    """RNF-01: sem rede, sem banco, sem modelo — só texto entra e aviso sai."""
    import inspect

    from toc_api.dominio import formulacao

    fonte = inspect.getsource(formulacao)
    for proibido in ("import requests", "httpx", "sqlalchemy", "fastapi", "open("):
        assert proibido not in fonte, proibido
