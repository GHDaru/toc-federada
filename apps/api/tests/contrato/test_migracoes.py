"""As migrações são contrato de reversibilidade (spec 003, RF-29; spec 011, RNF-09).

Não sobem banco: leem a cadeia Alembic como dado. O teste que SOBE banco é
`tests/integracao/test_migracao_e_isolamento.py`.

Por que ler a cadeia importa: a raia infra do ciclo 003 exige `downgrade` testado, e um
`downgrade` que só existe como `pass` passa despercebido numa revisão de diff — mas não
aqui, porque o corpo é medido.
"""
from __future__ import annotations

import ast
import pathlib

RAIZ = pathlib.Path(__file__).resolve().parents[2]
VERSOES = RAIZ / "src" / "toc_api" / "alembic" / "versions"


def modulos() -> list[pathlib.Path]:
    return sorted(p for p in VERSOES.glob("*.py") if not p.name.startswith("_"))


def literais(caminho: pathlib.Path) -> dict[str, object]:
    arvore = ast.parse(caminho.read_text(encoding="utf-8"))
    achados: dict[str, object] = {}
    for no in arvore.body:
        if isinstance(no, ast.Assign) and len(no.targets) == 1:
            alvo = no.targets[0]
            if isinstance(alvo, ast.Name) and alvo.id in ("revision", "down_revision"):
                achados[alvo.id] = ast.literal_eval(no.value)
    return achados


def corpo_da_funcao(caminho: pathlib.Path, nome: str) -> list[ast.stmt]:
    arvore = ast.parse(caminho.read_text(encoding="utf-8"))
    for no in arvore.body:
        if isinstance(no, ast.FunctionDef) and no.name == nome:
            return [c for c in no.body if not isinstance(c, ast.Expr)
                    or not isinstance(c.value, ast.Constant)]
    raise AssertionError(f"{caminho.name} não define {nome}()")


def test_existe_ao_menos_uma_migracao():
    assert modulos(), f"nenhuma migração em {VERSOES}"


def test_a_cadeia_e_linear_e_tem_uma_cabeca_so():
    revisoes = {literais(m)["revision"]: literais(m).get("down_revision") for m in modulos()}
    assert len(revisoes) == len(modulos()), "revisões duplicadas na cadeia"

    bases = [r for r, anterior in revisoes.items() if anterior is None]
    assert len(bases) == 1, f"a cadeia precisa de uma base só, achei {bases}"

    apontadas = {anterior for anterior in revisoes.values() if anterior is not None}
    cabecas = [r for r in revisoes if r not in apontadas]
    assert len(cabecas) == 1, f"a cadeia precisa de uma cabeça só, achei {cabecas}"

    for anterior in apontadas:
        assert anterior in revisoes, f"down_revision órfã: {anterior}"


def test_toda_migracao_tem_upgrade_e_downgrade_com_corpo_de_verdade():
    for m in modulos():
        for nome in ("upgrade", "downgrade"):
            corpo = corpo_da_funcao(m, nome)
            assert corpo, f"{m.name}: {nome}() está vazio"
            assert not all(isinstance(c, ast.Pass) for c in corpo), (
                f"{m.name}: {nome}() é só `pass` — downgrade que não desfaz não é reversível"
            )


def ddl_cega(caminho: pathlib.Path) -> list[str]:
    """Chamadas de `create_all`/`drop_all` — medidas na árvore, não no texto.

    A primeira versão procurava a cadeia `"create_all"` no fonte e reprovava os três
    arquivos que EXPLICAM por que não se usa `create_all` (`tabelas.py`, `fabrica.py`,
    este próprio módulo). Um portão que reprova a explicação da regra ensina a apagar a
    explicação — e o portão fica mais fraco, não mais forte. Uma chamada de verdade
    continua reprovando; a mudança é de precisão, não de rigor.
    """
    arvore = ast.parse(caminho.read_text(encoding="utf-8"))
    achados = []
    for no in ast.walk(arvore):
        if isinstance(no, ast.Call):
            alvo = no.func
            nome = alvo.attr if isinstance(alvo, ast.Attribute) else getattr(alvo, "id", "")
            if nome in ("create_all", "drop_all"):
                achados.append(f"{caminho.name}:{no.lineno} {nome}()")
    return achados


def test_nenhuma_migracao_usa_create_all():
    """Brief §4: 'nada de create_all' — migração é DDL declarada, não varredura cega."""
    for m in modulos():
        assert ddl_cega(m) == [], f"{m.name}: {ddl_cega(m)}"


def test_o_codigo_de_producao_nao_usa_create_all_nem_drop_all():
    fonte = RAIZ / "src" / "toc_api"
    ofensores = [o for p in sorted(fonte.rglob("*.py")) for o in ddl_cega(p)]
    assert ofensores == [], f"esquema por DDL cego, não por migração: {ofensores}"
