"""O ResultadoDeGeracao — estrutura validada por esquema, nunca markdown por regex.

Siglas, uma vez: **NC** — Nuvem de Conflito · **JSON** — *JavaScript Object Notation* ·
**IA** — inteligência artificial · **TRIZ** — Teoria da Resolução Inventiva de Problemas ·
**FSM** — máquina de estados finitos.

O contraexemplo está medido na spec (F-03): em
`tocbuilderv3/services/parserService.ts` a nuvem era arrancada de markdown por 5 extrações
de entidade e 7 pares premissa/solução em expressão regular, e **qualquer** variação de
formato devolvia `null` inteiro (l.67) — a estrutura dependia da FORMA do texto do modelo.
Aqui a forma é contrato: o resultado entra como dado estruturado, é validado contra um
esquema versionado, e o que não valida é recusado em falha fechada ANTES de virar
proposta (RF-21, RF-22, RF-29; RN-05).
"""
from __future__ import annotations

import copy

import pytest

from toc_api.dominio.geracao import (
    ESQUEMA_DO_RESULTADO,
    VERSAO_DO_RESULTADO,
    ResultadoDeGeracao,
    ResultadoDeGeracaoInvalido,
)
from toc_api.dominio.nuvem import ChaveDaAresta, PapelDaEntidade, SeparacaoTRIZ

BRUTO = {
    "versao": VERSAO_DO_RESULTADO,
    "racional": "A instituição precisa de caixa e de reputação; as duas cabem em A.",
    "entidades": {
        "A": "Sustentabilidade da Instituição Horizonte",
        "B": "Receita nova no próximo semestre",
        "C": "Reputação acadêmica preservada",
        "D": "Abrir turmas em três cidades novas",
        "D_PRIME": "Não abrir turmas em três cidades novas",
    },
    "arestas": {
        "A_B": [{"texto": "sem caixa novo a instituição não se sustenta"}],
        "A_C": [{"texto": "sem reputação não há matrícula futura"}],
        "B_D": [{"texto": "só turma nova gera receita no semestre"}],
        "C_D_PRIME": [{"texto": "não abrir preserva o corpo docente atual"}],
        "D_C": [{"texto": "turma nova sem professor formado derruba a reputação"}],
        "D_PRIME_B": [{"texto": "não abrir deixa o semestre sem receita nova"}],
        "D_D_PRIME": [
            {
                "texto": "não há orçamento para as duas ações",
                "injecoes": [
                    {
                        "texto": "faseamento orçamentário por marco de receita",
                        "separacao": "tempo",
                    }
                ],
            }
        ],
    },
}


def test_o_resultado_valido_vira_objeto_tipado_com_as_cinco_entidades_e_as_sete_arestas() -> None:
    resultado = ResultadoDeGeracao.de_dicionario(BRUTO)

    print(
        f"resultado v{resultado.versao}: {len(resultado.entidades)} entidade(s), "
        f"{len(resultado.premissas)} chave(s) de aresta, "
        f"{resultado.total_de_premissas} premissa(s), {resultado.total_de_injecoes} injeção(ões)"
    )
    assert set(resultado.entidades) == set(PapelDaEntidade)
    assert set(resultado.premissas) == set(ChaveDaAresta)
    assert resultado.total_de_premissas == 7
    assert resultado.total_de_injecoes == 1
    injecao = resultado.premissas[ChaveDaAresta.D_D_PRIME][0].injecoes[0]
    assert injecao.separacao is SeparacaoTRIZ.TEMPO


def test_o_resultado_volta_a_dicionario_sem_perda() -> None:
    resultado = ResultadoDeGeracao.de_dicionario(BRUTO)

    ida_e_volta = ResultadoDeGeracao.de_dicionario(resultado.como_dicionario())

    assert ida_e_volta == resultado


@pytest.mark.parametrize(
    "mutacao,motivo",
    [
        (lambda d: d.pop("entidades"), "campo obrigatório ausente"),
        (lambda d: d["entidades"].pop("D_PRIME"), "entidade faltando"),
        (lambda d: d["arestas"].pop("D_D_PRIME"), "aresta faltando"),
        (lambda d: d["arestas"].update({"D_Z": []}), "aresta desconhecida"),
        (lambda d: d["entidades"].update({"E": "quinta necessidade"}), "papel desconhecido"),
        (lambda d: d.update({"versao": "9.9.9"}), "versão desconhecida"),
        (lambda d: d.update({"versao": 1}), "versão que nem é texto"),
        (lambda d: d["arestas"].update({"A_B": [{"texto": ""}]}), "premissa vazia"),
        (
            lambda d: d["arestas"]["D_D_PRIME"][0]["injecoes"][0].update({"separacao": "cor"}),
            "separação TRIZ fora do vocabulário",
        ),
        (lambda d: d["entidades"].update({"A": ""}), "entidade sem texto"),
        (lambda d: d.update({"extra": "campo que ninguém contratou"}), "campo fora do contrato"),
        (lambda d: d["arestas"].update({"A_B": "premissa em texto solto"}), "aresta que não é lista"),
    ],
)
def test_resultado_fora_do_esquema_e_recusado_em_falha_fechada(mutacao, motivo) -> None:
    """RF-22: falha fechada, com erro legível — nada aplicado, nada meio-aplicado."""
    bruto = copy.deepcopy(BRUTO)
    mutacao(bruto)

    with pytest.raises(ResultadoDeGeracaoInvalido) as erro:
        ResultadoDeGeracao.de_dicionario(bruto)

    print(f"{motivo}: recusado com {erro.value.codigo} — {erro.value}")
    assert str(erro.value)


def test_a_versao_desconhecida_tem_codigo_proprio() -> None:
    """RF-29: evoluir o esquema é mudança de contrato, nunca afrouxamento do parse."""
    bruto = {**copy.deepcopy(BRUTO), "versao": "2.0.0"}

    with pytest.raises(ResultadoDeGeracaoInvalido) as erro:
        ResultadoDeGeracao.de_dicionario(bruto)

    assert erro.value.codigo == "VERSAO_DESCONHECIDA"


def test_o_esquema_e_o_subconjunto_que_este_projeto_sabe_validar() -> None:
    """O mesmo validador do catálogo (§A.5): palavra desconhecida não passa em silêncio."""
    from toc_api.dominio.federacao.esquema import exigir_esquema_suportado

    exigir_esquema_suportado(ESQUEMA_DO_RESULTADO)

    chaves = ESQUEMA_DO_RESULTADO["properties"]["arestas"]["properties"]
    print(f"chaves de aresta no esquema: {sorted(chaves)}")
    assert sorted(chaves) == sorted(c.value for c in ChaveDaAresta)


def test_nenhum_parse_de_markdown_no_caminho_da_geracao() -> None:
    """DoD 7 da spec: o contraexemplo do v3 não atravessa — e o teste o mede.

    A leitura é por **árvore sintática**, não por `grep` no arquivo: a prosa deste módulo
    e a docstring dele *citam* o parser da linhagem de propósito (é o contraexemplo que
    justifica o contrato), e um `grep` de texto reprovaria a explicação em vez do código.
    O que o teste mede é o executável: nenhuma importação do módulo de expressão regular
    e nenhum literal de código citando markdown, em qualquer dos dois módulos do caminho
    da geração.
    """
    import ast
    import inspect

    from toc_api.dominio import geracao, nuvem

    examinados: list[str] = []
    for modulo in (geracao, nuvem):
        arvore = ast.parse(inspect.getsource(modulo))
        importados = {
            alias.name.split(".")[0]
            for no in ast.walk(arvore)
            if isinstance(no, ast.Import)
            for alias in no.names
        } | {
            (no.module or "").split(".")[0]
            for no in ast.walk(arvore)
            if isinstance(no, ast.ImportFrom)
        }
        assert "re" not in importados, f"{modulo.__name__} importa expressão regular"

        docstrings = {
            id(no.body[0].value)
            for no in ast.walk(arvore)
            if isinstance(no, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))
            and no.body
            and isinstance(no.body[0], ast.Expr)
            and isinstance(no.body[0].value, ast.Constant)
            and isinstance(no.body[0].value.value, str)
        }
        literais = [
            no.value
            for no in ast.walk(arvore)
            if isinstance(no, ast.Constant)
            and isinstance(no.value, str)
            and id(no) not in docstrings
        ]
        for literal in literais:
            for proibido in ("markdown", "```"):
                assert proibido not in literal.lower(), (modulo.__name__, literal)
        examinados.append(f"{modulo.__name__}: {len(literais)} literal(is) de código")

    print(f"caminho da geração examinado por árvore sintática — {'; '.join(examinados)}")
