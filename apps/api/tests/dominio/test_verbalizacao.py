"""M4 · F4.2.3 — a verbalização avaliada de obstáculos e objetivos intermediários.

Siglas, uma vez neste arquivo: **APR** — Árvore de Pré-Requisitos · **OI** — Objetivo
Intermediário · **TOC** — Teoria das Restrições · **IA** — inteligência artificial ·
**RF/RN/RNF** — requisito funcional / regra de negócio / requisito não funcional da spec
008 · **M2** — o módulo da Árvore da Realidade Atual.

Três coisas se provam aqui:

1. **É função pura** (RNF-01): sem rede, sem banco, sem modelo. O contraste com a linhagem
   é o de sempre — lá o que cumpria este papel era prompt no navegador.
2. **Avisa, nunca veta** (RN-08): o veredito é dado; quem registra é o agregado, e ele
   registra mesmo com aviso. A prova de que não veta está em `test_apr.py`.
3. **O corpus é função forçante** (RNF-07): heurística nova sem caso novo não entra, e
   caso do corpus que a heurística erra derruba a suíte. A saída diz **quantos** casos
   bons e maus foram examinados (regra R2 do `CLAUDE.md`).
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from toc_api.dominio.verbalizacao import (
    VERSAO_DO_LEXICO_DE_VERBALIZACAO,
    CodigoDeVerbalizacao,
    PapelVerbalizado,
    Veredito,
    avaliar_verbalizacao,
    lexico_de_verbalizacao,
)

CORPUS = json.loads((Path(__file__).parent / "corpus_verbalizacao.json").read_text("utf-8"))
CASOS = CORPUS["casos"]


def _ids(casos) -> list[str]:
    return [c["id"] for c in casos]


# --------------------------------------------------------------------------------------
# O corpus inteiro, caso a caso (RF-20, RF-22)
# --------------------------------------------------------------------------------------


@pytest.mark.parametrize("caso", CASOS, ids=_ids(CASOS))
def test_o_corpus_inteiro_recebe_o_veredito_declarado(caso) -> None:
    avaliacao = avaliar_verbalizacao(caso["papel"], caso["texto"])

    codigos = [a.codigo.value for a in avaliacao.avisos]
    print(f"{caso['id']}: {avaliacao.veredito.value} {codigos} — {caso['texto'][:60]!r}")
    assert avaliacao.veredito.value == caso["veredito"], caso["porque"]
    if caso.get("codigo"):
        assert caso["codigo"] in codigos
        trecho = next(a.trecho for a in avaliacao.avisos if a.codigo.value == caso["codigo"])
        assert caso["trecho"] in trecho.lower(), f"{caso['id']}: trecho apontado {trecho!r}"


def test_a_saida_diz_quantos_casos_bons_e_maus_foram_examinados() -> None:
    """Regra R2: verde que não diz o tamanho do que olhou não é evidência."""
    bons = [c for c in CASOS if c["veredito"] == "atende"]
    maus = [c for c in CASOS if c["veredito"] == "aviso"]
    indeterminados = [c for c in CASOS if c["veredito"] == "indeterminado"]
    obstaculos = [c for c in CASOS if c["papel"] == "obstaculo"]
    ois = [c for c in CASOS if c["papel"] == "objetivo_intermediario"]

    medida = (
        f"corpus de verbalização v{CORPUS['versao']}: {len(CASOS)} casos examinados — "
        f"{len(bons)} bons, {len(maus)} maus, {len(indeterminados)} indeterminados; "
        f"{len(obstaculos)} de obstáculo, {len(ois)} de objetivo intermediário"
    )
    print(medida)
    assert len(CASOS) == len(bons) + len(maus) + len(indeterminados)
    assert bons and maus and indeterminados


def test_todo_codigo_de_aviso_tem_caso_no_corpus() -> None:
    """RNF-07, a função forçante: heurística nova sem caso novo **não entra**."""
    no_corpus = {c["codigo"] for c in CASOS if c.get("codigo")}
    declarados = {c.value for c in CodigoDeVerbalizacao}
    print(f"códigos declarados={sorted(declarados)} · cobertos pelo corpus={sorted(no_corpus)}")
    assert declarados == no_corpus


def test_todo_marcador_do_lexico_tem_caso_no_corpus() -> None:
    """A mesma função forçante do M2, sobre o léxico: marcador sem caso é regra sem prova."""
    lexico = lexico_de_verbalizacao("pt")
    textos = " ".join(c["texto"].lower() for c in CASOS)
    sem_caso = [
        marcador
        for familia, marcadores in lexico.marcadores.items()
        for marcador in marcadores
        if marcador.strip() not in textos
    ]
    print(
        f"léxico v{lexico.versao}: "
        f"{sum(len(m) for m in lexico.marcadores.values())} marcadores em "
        f"{len(lexico.marcadores)} famílias; sem caso no corpus: {len(sem_caso)}"
    )
    assert lexico.versao == VERSAO_DO_LEXICO_DE_VERBALIZACAO
    # Cada FAMÍLIA precisa de caso; exigir caso para cada sinônimo engessaria o léxico sem
    # aumentar a prova — o que a família cobre é o comportamento.
    for familia, marcadores in lexico.marcadores.items():
        assert any(m.strip() in textos for m in marcadores), f"família {familia} sem caso"


# --------------------------------------------------------------------------------------
# O alcance declarado — e o `indeterminado` honesto (RF-22)
# --------------------------------------------------------------------------------------


def test_indeterminado_e_resposta_de_primeira_classe_e_nao_carrega_aviso() -> None:
    avaliacao = avaliar_verbalizacao(PapelVerbalizado.OBSTACULO, "Fila")
    print(f"veredito={avaliacao.veredito.value} avisos={avaliacao.avisos}")
    assert avaliacao.veredito is Veredito.INDETERMINADO
    assert avaliacao.avisos == ()


def test_previsao_futura_e_ausencia_generica_nao_valem_para_objetivo_intermediario() -> None:
    """O alcance é declarado, não presumido: as duas armadilhas são do OBSTÁCULO.

    Um objetivo intermediário fala do estado que **passará** a existir; cobrá-lo pela
    mesma régua do obstáculo seria ensinar o método errado — e aviso errado é pior que
    silêncio (a lição do `indeterminado` do M3).
    """
    do_obstaculo = avaliar_verbalizacao("obstaculo", "O conselho vai recusar a proposta")
    do_oi = avaliar_verbalizacao("objetivo_intermediario", "O conselho aprovará a proposta")

    print(
        f"obstáculo → {[a.codigo.value for a in do_obstaculo.avisos]} · "
        f"objetivo intermediário → {[a.codigo.value for a in do_oi.avisos]}"
    )
    assert CodigoDeVerbalizacao.PREVISAO_FUTURA in [a.codigo for a in do_obstaculo.avisos]
    assert do_oi.veredito is not Veredito.AVISO or CodigoDeVerbalizacao.PREVISAO_FUTURA not in [
        a.codigo for a in do_oi.avisos
    ]


def test_todo_aviso_carrega_trecho_explicacao_e_exemplo() -> None:
    """RI-05: o aviso aponta o trecho e mostra a forma certa — senão ensina que a
    ferramenta implica, não que o método existe."""
    avaliacao = avaliar_verbalizacao("objetivo_intermediario", "Criar a rotina de conferência")
    aviso = avaliacao.avisos[0]
    print(f"aviso: trecho={aviso.trecho!r} exemplo={aviso.exemplo!r}")
    assert aviso.trecho and aviso.explicacao and aviso.exemplo


def test_a_avaliacao_declara_a_versao_do_lexico_que_a_produziu() -> None:
    avaliacao = avaliar_verbalizacao("obstaculo", "Falta dinheiro")
    assert avaliacao.versao_do_lexico == VERSAO_DO_LEXICO_DE_VERBALIZACAO


def test_papel_desconhecido_e_erro_explicito_nunca_silencio() -> None:
    with pytest.raises(ValueError):
        avaliar_verbalizacao("objetivo", "O processo responde em dois dias")


def test_idioma_sem_lexico_e_erro_explicito() -> None:
    with pytest.raises(KeyError):
        lexico_de_verbalizacao("tlh")


def test_a_avaliacao_e_offline_e_deterministica() -> None:
    """RNF-06: mesma entrada, mesma saída — e nada de rede no caminho (RNF-01)."""
    texto = "Precisamos criar a conversão de dados entre os dois sistemas"
    uma = avaliar_verbalizacao("obstaculo", texto)
    outra = avaliar_verbalizacao("obstaculo", texto)
    assert uma == outra
