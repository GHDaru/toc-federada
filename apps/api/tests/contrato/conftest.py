"""Apoio dos testes de contrato da superfície HTTP — clientes, personas e o validador.

**As personas são fictícias por regra** (ADR 0006): "Facilitadora TOC" e "Instituição
Horizonte". Nenhum dado real de pessoa entra em fixture, captura, spec ou exemplo.

O validador (`valida_contra_o_contrato`) é o que dá sentido à palavra "contrato" no nome
desta pasta: ele não confere o corpo contra o que o teste esperava, e sim contra o
**esquema que a aplicação declara no seu próprio OpenAPI**. É a diferença entre "a
resposta tem os campos que eu quis" e "a resposta é o que eu prometi ao cliente".
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient
from jsonschema import Draft202012Validator

from toc_api.http.app import criar_app

TOKEN_PLENO = "tok-teste-facilitadora"
TOKEN_LEITURA = "tok-teste-observadora"
TOKEN_OUTRO_INQUILINO = "tok-teste-outra-instituicao"
TOKEN_SEM_NADA = "tok-teste-sem-capacidade"

IDENTIDADES = {
    TOKEN_PLENO: {
        "inquilino_id": "inq-horizonte",
        "usuario_id": "usr-facilitadora",
        "capabilities": ["toc:read", "toc:write"],
        "app_id": "toc-federada",
    },
    TOKEN_LEITURA: {
        "inquilino_id": "inq-horizonte",
        "usuario_id": "usr-observadora",
        "capabilities": ["toc:read"],
        "app_id": "toc-federada",
    },
    TOKEN_OUTRO_INQUILINO: {
        "inquilino_id": "inq-outra-instituicao",
        "usuario_id": "usr-visitante",
        "capabilities": ["toc:read", "toc:write"],
        "app_id": "toc-federada",
    },
    TOKEN_SEM_NADA: {
        "inquilino_id": "inq-horizonte",
        "usuario_id": "usr-sem-nada",
        "capabilities": [],
        "app_id": "toc-federada",
    },
}

AMBIENTE = {
    "TOC_AMBIENTE": "teste",
    "TOC_IDENTIDADES_FALSAS": json.dumps(IDENTIDADES),
}


@pytest.fixture()
def app():
    return criar_app(dict(AMBIENTE))


def _cliente(app, token: str | None) -> TestClient:
    cliente = TestClient(app)
    if token is not None:
        cliente.headers["Authorization"] = f"Bearer {token}"
    return cliente


@pytest.fixture()
def plena(app) -> TestClient:
    """Facilitadora TOC — `toc:read` e `toc:write`."""
    return _cliente(app, TOKEN_PLENO)


@pytest.fixture()
def leitora(app) -> TestClient:
    """Observadora — só `toc:read`."""
    return _cliente(app, TOKEN_LEITURA)


@pytest.fixture()
def sem_capacidade(app) -> TestClient:
    """Identidade ativa e conjunto de capacidades VAZIO — o caso fail-closed puro."""
    return _cliente(app, TOKEN_SEM_NADA)


@pytest.fixture()
def outro_inquilino(app) -> TestClient:
    return _cliente(app, TOKEN_OUTRO_INQUILINO)


@pytest.fixture()
def anonima(app) -> TestClient:
    return _cliente(app, None)


def valida_contra_o_contrato(app, resposta, metodo: str, gabarito: str) -> Any:
    """Valida o corpo da resposta contra o esquema que o OpenAPI da aplicação declara.

    `gabarito` é o caminho COM os marcadores (`/toc/projetos/{projeto_id}`), que é como o
    OpenAPI o indexa. A resolução de `$ref` acontece contra o documento inteiro, por isso
    `components` viaja junto com o esquema da resposta.
    """
    documento = app.openapi()
    operacao = documento["paths"][gabarito][metodo.lower()]
    declarada = operacao["responses"].get(str(resposta.status_code))
    assert declarada is not None, (
        f"{metodo} {gabarito} respondeu {resposta.status_code}, que não está declarado "
        f"no contrato: {sorted(operacao['responses'])}"
    )
    conteudo = declarada.get("content")
    if conteudo is None:
        assert resposta.content == b"", (
            f"{metodo} {gabarito} declara resposta sem corpo e devolveu bytes"
        )
        return None
    esquema = conteudo["application/json"]["schema"]
    corpo = resposta.json()
    Draft202012Validator({**esquema, "components": documento["components"]}).validate(corpo)
    return corpo


#: Cópia local do `padrao/schemas/erro.schema.json` do repositório `GHDaru/protocolos`.
#: Existe porque o repositório da norma é LEITURA e pode não estar montado na máquina que
#: roda a suíte; quando ele está, `NORMA_ERRO` aponta para o arquivo de verdade e o teste
#: `test_a_copia_local_do_schema_de_erro_nao_derivou_da_norma` compara os dois. Cópia sem
#: verificação de deriva é a dívida silenciosa que a regra R5 do `CLAUDE.md` nomeia.
ERRO_SCHEMA_APH = {
    "type": "object",
    "required": ["code", "message"],
    "additionalProperties": False,
    "properties": {
        "code": {"type": "string", "pattern": "^[A-Z][A-Z0-9_]*$"},
        "message": {"type": "string", "minLength": 1},
        "details": {"type": "object"},
    },
}

NORMA_ERRO = Path("/home/user/protocolos/padrao/schemas/erro.schema.json")


def schema_de_erro_da_norma() -> dict | None:
    """O schema do Anexo A §A.7 lido do repositório da norma, se ele estiver montado."""
    if not NORMA_ERRO.is_file():
        return None
    return json.loads(NORMA_ERRO.read_text(encoding="utf-8"))


def valida_envelope_de_erro(resposta) -> dict:
    """O corpo de erro é `{"error": <Erro §A.7>}` — Anexo A do Padrão APH, linha 42."""
    corpo = resposta.json()
    assert set(corpo) == {"error"}, f"envelope fora do §A.7: {sorted(corpo)}"
    Draft202012Validator(ERRO_SCHEMA_APH).validate(corpo["error"])
    return corpo["error"]
