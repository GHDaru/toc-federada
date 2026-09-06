"""Um registro de códigos de erro, e um só — a varredura que impede a divergência voltar.

Siglas, uma vez neste arquivo: **APH** — Aplicação ↔ Harness (o padrão da fronteira) ·
**HTTP** — *HyperText Transfer Protocol* · **AST** — *Abstract Syntax Tree* (árvore
sintática abstrata) · **API** — interface de programação de aplicações.

O §A.7 do Anexo A fixa `code` em `MAIUSCULAS_COM_SUBLINHADO` e **estável**, "porque o
cliente discrimina por código e nunca por mensagem". Um registro mínimo é normativo e uma
implementação "PODE adicionar os seus" — desde que declarados.

O defeito que este arquivo existe para impedir foi achado por revisão independente: o
**mesmo serviço** emitia `INVALID_ARGUMENT` pela borda REST (`http/erros.py`) e
`INVALID_ARGUMENTS` pela borda APH (`http/aph.py`). Um cliente que compare o código por
igualdade — que é o uso que a norma prescreve — trata um dos dois e ignora o outro. A
causa raiz não foi distração: eram **dois registros declarados**, um por borda, e nenhum
portão comparava os dois.

Por isso a varredura é sobre o **código-fonte**, e não sobre uma lista escrita à mão: ela
lê os pontos de emissão com a AST do próprio Python e exige que cada código literal esteja
no registro único (`dominio/federacao/wire.py`). Um código novo, emitido e não declarado,
derruba este teste — e não espera uma requisição que passe por aquela linha.
"""
from __future__ import annotations

import ast
import re
from pathlib import Path

from toc_api.dominio.federacao import wire
from toc_api.http import erros as tradutores

RAIZ_DA_API = Path(__file__).resolve().parents[2]
FONTES = RAIZ_DA_API / "src" / "toc_api"
RAIZ_DO_REPO = RAIZ_DA_API.parents[1]

#: Onde um código de erro nasce. Chave: nome da função/classe chamada. Valor: onde o
#: código está na chamada — índice do argumento posicional, ou nome do argumento nomeado.
#: Esta tabela é a definição operacional de "código emitido"; acrescentar um emissor novo
#: sem acrescentar a linha aqui é o jeito de furar a varredura, e é por isso que o teste
#: `test_todo_emissor_conhecido_aparece_no_codigo_fonte` confere que cada linha ainda casa.
EMISSORES: dict[str, int | str] = {
    "erro_http": 0,  # http/aph.py — o envelope do §A.2 na borda APH
    "_resposta": 1,  # http/erros.py — o tradutor de recusa em HTTP
    "envelope": 0,  # http/erros.py — o corpo `{"error": …}` cru
    "ErroDoFio": "code",  # dominio/federacao/wire.py — o próprio §A.7
    "TransicaoInvalida": 0,  # dominio/federacao/proposta.py — a recusa da máquina de estados
}

FORMA_DE_CODIGO = re.compile(r"^[A-Z][A-Z0-9_]*$")


def _emissoes() -> list[tuple[str, int, str]]:
    """`(arquivo, linha, código)` de cada emissão literal em `src/toc_api`."""
    achados: list[tuple[str, int, str]] = []
    for arquivo in sorted(FONTES.rglob("*.py")):
        arvore = ast.parse(arquivo.read_text("utf-8"), filename=str(arquivo))
        relativo = str(arquivo.relative_to(FONTES))
        for no in ast.walk(arvore):
            if not isinstance(no, ast.Call):
                continue
            alvo = no.func
            nome = alvo.attr if isinstance(alvo, ast.Attribute) else getattr(alvo, "id", None)
            onde = EMISSORES.get(nome or "")
            if onde is None:
                continue
            argumento: ast.expr | None = None
            if isinstance(onde, int):
                if len(no.args) > onde:
                    argumento = no.args[onde]
            else:
                for palavra in no.keywords:
                    if palavra.arg == onde:
                        argumento = palavra.value
            if isinstance(argumento, ast.Constant) and isinstance(argumento.value, str):
                achados.append((relativo, argumento.lineno, argumento.value))
    return achados


def test_todo_codigo_emitido_no_servico_esta_no_registro_declarado() -> None:
    """A varredura: nenhum código sai do serviço sem linha no registro do §A.7."""
    emissoes = _emissoes()
    declarados = set(wire.CODIGOS)

    fora = sorted({(a, l, c) for a, l, c in emissoes if c not in declarados})

    medida = (
        f"registro §A.7: {len(emissoes)} emissão(ões) literal(is) varridas em "
        f"{len(list(FONTES.rglob('*.py')))} arquivo(s) de produção, "
        f"{len({c for _, _, c in emissoes})} código(s) distintos, "
        f"contra {len(declarados)} declarado(s)"
    )
    print(medida)
    assert not fora, (
        "código emitido e não declarado (§A.7 permite os próprios, só declarados): "
        + "; ".join(f"{a}:{l} → {c}" for a, l, c in fora)
        + f" — {medida}"
    )
    assert len(emissoes) >= 20, medida


def test_o_servico_nao_emite_duas_grafias_do_mesmo_codigo() -> None:
    """O defeito nomeado: `INVALID_ARGUMENT` numa borda e `INVALID_ARGUMENTS` na outra.

    A checagem é geral, não um caso particular: dois códigos que só diferem por um `S`
    final são a assinatura desta classe de divergência, e nenhum par assim é legítimo.
    """
    codigos = sorted({c for _, _, c in _emissoes()} | set(wire.CODIGOS))

    pares = [
        (a, b)
        for a in codigos
        for b in codigos
        if a != b and (a + "S" == b or a.rstrip("S") == b.rstrip("S") and a != b)
    ]

    assert not pares, f"duas grafias do mesmo código no mesmo serviço: {pares}"


def test_ha_um_registro_so_e_a_borda_rest_usa_o_mesmo() -> None:
    """Um registro, não dois: o de `http/erros.py` é o do domínio, não uma segunda lista."""
    assert set(tradutores.CODIGOS_ACRESCENTADOS) <= set(wire.CODIGOS), sorted(
        set(tradutores.CODIGOS_ACRESCENTADOS) - set(wire.CODIGOS)
    )
    assert set(tradutores.CODIGO_POR_STATUS.values()) <= set(wire.CODIGOS)


def test_todo_codigo_do_registro_casa_a_forma_normativa() -> None:
    for codigo in wire.CODIGOS:
        assert FORMA_DE_CODIGO.match(codigo), codigo


def test_o_cliente_web_discrimina_por_codigos_que_o_servico_declara() -> None:
    """O outro lado da igualdade: a tela compara `codigo === "…"` (apps/web/src/api/erros.ts).

    Só os códigos do **serviço** entram na conferência; os dois do próprio cliente (rede
    fora do ar, resposta ilegível) não vêm de resposta HTTP alguma e estão nomeados aqui.
    """
    do_cliente = {"REDE_INDISPONIVEL", "RESPOSTA_INVALIDA"}
    fonte = (RAIZ_DO_REPO / "apps/web/src/api/erros.ts").read_text("utf-8")
    bloco = fonte.split("export const CODIGOS = {", 1)[1].split("} as const;", 1)[0]

    citados = {m for m in re.findall(r'"([A-Z][A-Z0-9_]*)"', bloco)} - do_cliente

    fora = sorted(citados - set(wire.CODIGOS))
    medida = f"cliente web: {len(citados)} código(s) de serviço discriminados na interface"
    print(medida)
    assert not fora, f"a tela trata código que o serviço não declara: {fora} — {medida}"
    assert citados, medida
