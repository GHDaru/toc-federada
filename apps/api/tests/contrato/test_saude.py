"""`/saude` diz qual backend está de pé — e nunca a credencial (P7).

A pergunta que este endpoint responde não é decorativa. A fundação publicou
`persistence: in-memory` com contas de repositório abertas (spec 056 dela, lida em
`apps/api/src/ghdaru_api/persistence/factory.py`): quem operava não tinha como saber, pela
própria aplicação, contra o que ela estava rodando.

Nota de honestidade sobre a ordem (P4): os testes de domínio, de aplicação e de
persistência deste lote nasceram VERMELHOS antes do código. Este arquivo não — a casca
HTTP foi escrita junto com a composição e o teste veio logo depois, caracterizando o que
ela faz. Está escrito aqui porque o P4 é literal e a exceção tem de aparecer, não sumir.
"""
from fastapi.testclient import TestClient

from toc_api.http.app import criar_app


def test_saude_sem_banco_declara_memoria():
    cliente = TestClient(criar_app({}))
    corpo = cliente.get("/saude").json()
    assert corpo["persistencia"] == "memoria"
    assert corpo["banco"] == "(ausente)"
    assert corpo["traco"] == "RastreadorNulo"


def test_saude_nunca_devolve_a_credencial_da_cadeia_de_conexao():
    ambiente = {
        "DATABASE_URL": "postgresql+psycopg://toc:senha-secreta@banco.exemplo/toc_federada"
    }
    cliente = TestClient(criar_app(ambiente))
    resposta = cliente.get("/saude")
    assert "senha-secreta" not in resposta.text
    assert resposta.json()["banco"] == "postgresql+psycopg://***@banco.exemplo/toc_federada"


def test_saude_declara_o_backend_postgres_quando_ha_cadeia():
    cliente = TestClient(criar_app({"DATABASE_URL": "postgresql://toc@localhost/toc_federada"}))
    assert cliente.get("/saude").json()["persistencia"] == "postgres"
