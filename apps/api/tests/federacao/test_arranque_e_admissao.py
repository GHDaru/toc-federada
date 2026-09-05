"""O arranque recusa subir — com código de saída, código de recusa e nenhuma porta aberta.

Siglas: **APH** — Aplicação ↔ Harness · **HTTP** — *HyperText Transfer Protocol*.

O teste de unidade prova a regra; o de **subprocesso** prova o que o §B.4.1 pede de fato:
que o processo morre. Um teste que só chamasse a função em memória deixaria de fora
exatamente a metade que a norma nomeia ("subir pela metade, funcionar até alguém clicar").
"""
from __future__ import annotations

import io
import json
import subprocess
import sys
from pathlib import Path

import pytest

from toc_api.dominio.federacao.admissao import OBRIGATORIOS
from toc_api.http.arranque import CODIGO_DE_SAIDA_DA_RECUSA, verificar_admissao

AMBIENTE_COMPLETO = {
    "HOST_ORIGIN": "https://plataforma.exemplo",
    "HOST_BASE_URL": "https://api.plataforma.exemplo",
    "APP_ID": "toc",
    "EMBED_URL": "https://toc-federada.exemplo/toc/embarcado",
    "TOC_APP_CREDENTIAL": "ghd_credencial_sintetica",
    "DATABASE_URL": "postgresql+psycopg://toc@/toc_federada",
}

RAIZ_DO_SERVICO = Path(__file__).resolve().parents[2]


def test_ambiente_completo_deixa_subir_e_registra_o_que_admitiu() -> None:
    saida = io.StringIO()

    verificar_admissao(AMBIENTE_COMPLETO, saida)

    linha = json.loads(saida.getvalue().strip())
    assert linha["evento"] == "admissao_aceita"
    assert linha["app_id"] == "toc"
    # O log de admissão NUNCA carrega credencial nem cadeia de conexão (RNF-02, RNF-09).
    assert "ghd_credencial_sintetica" not in saida.getvalue()
    assert "postgresql" not in saida.getvalue()


@pytest.mark.parametrize("parametro", [p.variavel for p in OBRIGATORIOS])
def test_cada_ausencia_mata_o_processo_com_o_codigo_certo(parametro: str) -> None:
    ambiente = {k: v for k, v in AMBIENTE_COMPLETO.items() if k != parametro}
    esperado = next(p.codigo for p in OBRIGATORIOS if p.variavel == parametro)
    saida = io.StringIO()

    with pytest.raises(SystemExit) as saiu:
        verificar_admissao(ambiente, saida)

    assert saiu.value.code == CODIGO_DE_SAIDA_DA_RECUSA
    assert saiu.value.code != 0
    ultima = json.loads(saida.getvalue().strip().splitlines()[-1])
    assert ultima["codigo"] == esperado
    assert ultima["parametro"] == parametro
    assert ultima["nivel"] == "critical"


def test_o_processo_de_verdade_morre_sem_abrir_porta() -> None:
    """§B.4.1 na forma que importa: o **processo**, não a função.

    Roda `python -m toc_api.http.arranque` com o ambiente incompleto e confere o código de
    saída e a última linha do log. Nenhuma porta é aberta porque a verificação acontece
    antes de existir servidor.
    """
    executado = subprocess.run(
        [sys.executable, "-m", "toc_api.http.arranque"],
        cwd=RAIZ_DO_SERVICO,
        env={
            "PATH": "/usr/bin:/bin",
            "PYTHONPATH": str(RAIZ_DO_SERVICO / "src"),
            **{k: v for k, v in AMBIENTE_COMPLETO.items() if k != "HOST_ORIGIN"},
        },
        capture_output=True,
        text=True,
        timeout=60,
    )

    assert executado.returncode != 0, executado.stdout + executado.stderr
    assert executado.returncode == CODIGO_DE_SAIDA_DA_RECUSA
    ultima = json.loads(executado.stderr.strip().splitlines()[-1])
    assert ultima["codigo"] == "ADMISSAO_HOST_ORIGIN_AUSENTE"


def test_o_processo_de_verdade_aceita_o_ambiente_completo() -> None:
    executado = subprocess.run(
        [sys.executable, "-m", "toc_api.http.arranque"],
        cwd=RAIZ_DO_SERVICO,
        env={"PATH": "/usr/bin:/bin", "PYTHONPATH": str(RAIZ_DO_SERVICO / "src"), **AMBIENTE_COMPLETO},
        capture_output=True,
        text=True,
        timeout=60,
    )

    assert executado.returncode == 0, executado.stdout + executado.stderr
    assert '"admissao_aceita"' in executado.stderr


def test_com_admissao_o_servico_declara_que_foi_admitido() -> None:
    """O `/saude` diz em qual dos dois estados o serviço está (RF-04 é do arranque; o
    estado é observável aqui)."""
    from fastapi.testclient import TestClient

    from toc_api.http.app import criar_app

    cliente = TestClient(criar_app(dict(AMBIENTE_COMPLETO)))

    corpo = cliente.get("/saude").json()

    assert corpo["admissao"] == "admitida"
    assert corpo["app_id"] == "toc"
    assert "ghd_credencial_sintetica" not in cliente.get("/saude").text


def test_sem_admissao_o_servico_declara_modo_de_desenvolvimento() -> None:
    from fastapi.testclient import TestClient

    from toc_api.http.app import criar_app

    cliente = TestClient(criar_app({}))

    assert cliente.get("/saude").json()["admissao"] == "ausente (desenvolvimento)"


def test_sem_admissao_nao_existe_identidade_da_fundacao() -> None:
    """Fail-closed no modo de desenvolvimento: sem fundação, nenhum embarque é aceito.

    O caminho errado — "cai num principal de mentira quando o real não está montado" —
    seria a janela de acesso sem dono que a RF-10 fecha.
    """
    from fastapi.testclient import TestClient

    from toc_api.http.app import criar_app

    cliente = TestClient(criar_app({}))

    resposta = cliente.post("/toc/embarque", json={"token": "ghdg_qualquer"})

    assert resposta.status_code >= 400
    assert resposta.json()["error"]["code"] in {"FUNDACAO_INDISPONIVEL", "UNAUTHORIZED"}
