"""A superfície HTTP contra o PostgreSQL REAL — nunca SQLite (brief §1).

Os testes de contrato rodam sobre o repositório em memória, que é honesto para medir
forma de resposta e recusa de capacidade e **não prova persistência nenhuma**. Este
arquivo fecha a diferença: o mesmo `criar_app` sobe apontando para um esquema recém
migrado por `alembic upgrade head`, e o que se confere é o que a 4ª geração da linhagem
nunca teve — recarregar e reencontrar (defeito D-07: a "persistência" dela era um vetor em
memória, `tocbuilderv3/services/mockApiService.ts`).

Marcado `integracao`: pulado com o motivo quando o banco não responde, jamais substituído
por um duplo.
"""
from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient

from toc_api.http.app import criar_app

pytestmark = pytest.mark.integracao

BOM = "A taxa de erros no processo X é de 15%."
SEGUNDO = "O retrabalho consome a equipe de análise."

IDENTIDADES = {
    "tok-integra-facilitadora": {
        "inquilino_id": "inq-horizonte",
        "usuario_id": "usr-facilitadora",
        "capabilities": ["toc:read", "toc:write"],
    },
    "tok-integra-outra": {
        "inquilino_id": "inq-outra-instituicao",
        "usuario_id": "usr-visitante",
        "capabilities": ["toc:read", "toc:write"],
    },
}


def cliente(url: str, esquema: str, token: str) -> TestClient:
    app = criar_app(
        {
            "DATABASE_URL": url,
            "TOC_DB_SCHEMA": esquema,
            "TOC_AMBIENTE": "teste",
            "TOC_IDENTIDADES_FALSAS": json.dumps(IDENTIDADES),
        }
    )
    c = TestClient(app)
    c.headers["Authorization"] = f"Bearer {token}"
    return c


def test_saude_declara_postgres_e_nunca_a_credencial(url_postgres, esquema_migrado):
    c = cliente(url_postgres, esquema_migrado, "tok-integra-facilitadora")
    corpo = c.get("/saude").json()
    assert corpo["persistencia"] == "postgres"
    assert corpo["identidade"] == "ProvedorDeIdentidadeFalso"
    assert "***" in corpo["banco"] or "@" not in corpo["banco"]


def test_a_ara_inteira_sobrevive_a_um_processo_novo(url_postgres, esquema_migrado):
    """Grava por uma aplicação, lê por OUTRA — nada de estado escondido em memória."""
    escrita = cliente(url_postgres, esquema_migrado, "tok-integra-facilitadora")
    projeto = escrita.post("/toc/ara/projetos", json={"nome": "Horizonte — ARA"}).json()
    a = escrita.post(
        f"/toc/ara/projetos/{projeto['id']}/efeitos", json={"titulo": BOM}
    ).json()
    b = escrita.post(
        f"/toc/ara/projetos/{projeto['id']}/efeitos", json={"titulo": SEGUNDO}
    ).json()
    aresta = escrita.post(
        f"/toc/projetos/{projeto['id']}/arestas",
        json={"origem_id": a["id"], "destino_id": b["id"]},
    ).json()
    escrita.post(f"/toc/ara/projetos/{projeto['id']}/nos/{b['id']}/ude", json={})
    escrita.post(
        f"/toc/ara/projetos/{projeto['id']}/nos/{b['id']}/pareceres",
        json={"favoravel": True, "justificativa": "É queixa contínua e acionável."},
    )
    escrita.put(
        f"/toc/ara/projetos/{projeto['id']}/nos/{b['id']}/status",
        json={"status": "validado"},
    )
    escrita.put(
        f"/toc/ara/projetos/{projeto['id']}/arestas/{aresta['id']}/exame",
        json={"estado": "com_reserva", "reserva": "Falta a condição de volume."},
    )

    # Aplicação NOVA: outra composição, outro motor, o mesmo banco.
    leitura = cliente(url_postgres, esquema_migrado, "tok-integra-facilitadora")
    ara = leitura.get(f"/toc/ara/projetos/{projeto['id']}").json()

    # Conjunto, e não lista: a ORDEM dos nós vinda do PostgreSQL **não é** a ordem de
    # criação, e isto é um defeito medido do adaptador do M1, não uma escolha deste
    # teste. `infra/persistencia/repositorio_projetos.py:162` grava em cada nó o
    # `criado_em` **do projeto** — o mesmo instante para todos —, de modo que o
    # `ORDER BY criado_em, id` da leitura (linha 223) degenera em ordenar por
    # identificador aleatório. O repositório em memória preserva a ordem de inserção, e
    # por isso os testes de contrato passam com lista: os dois adaptadores divergem.
    # O teste de ida e volta do M1 já compara por conjunto pelo mesmo motivo
    # (`tests/integracao/test_grafo_e_ara_no_postgres.py:97`). Fechar o defeito exige ou
    # instante próprio por nó, ou coluna de ordem com migração — os dois fora deste lote,
    # e ambos necessários antes do RF-32 (exportação byte-idêntica).
    assert {n["id"] for n in ara["projeto"]["nos"]} == {a["id"], b["id"]}
    ude = ara["udes"][0]
    assert ude["no_id"] == b["id"] and ude["status"] == "validado"
    assert ude["pareceres"][0]["autor"] == "usr-facilitadora"
    assert ara["elos"][0]["exame"]["reserva"] == "Falta a condição de volume."
    assert ara["elos"][0]["leitura"] == f"Se {BOM}, então {SEGUNDO}"


def test_o_isolamento_por_inquilino_vale_pelo_HTTP_tambem(url_postgres, esquema_migrado):
    dona = cliente(url_postgres, esquema_migrado, "tok-integra-facilitadora")
    outra = cliente(url_postgres, esquema_migrado, "tok-integra-outra")
    projeto = dona.post("/toc/projetos", json={"nome": "Só meu"}).json()

    assert outra.get(f"/toc/projetos/{projeto['id']}").status_code == 404
    assert outra.get("/toc/projetos").json() == []
    assert outra.delete(f"/toc/projetos/{projeto['id']}").status_code == 404
    assert dona.get(f"/toc/projetos/{projeto['id']}").status_code == 200


def test_exclusao_suave_e_restauracao_atravessam_o_banco(url_postgres, esquema_migrado):
    c = cliente(url_postgres, esquema_migrado, "tok-integra-facilitadora")
    projeto = c.post("/toc/projetos", json={"nome": "Vai e volta"}).json()
    no = c.post(f"/toc/projetos/{projeto['id']}/nos", json={"titulo": BOM}).json()

    c.delete(f"/toc/projetos/{projeto['id']}")
    assert [p["id"] for p in c.get("/toc/projetos/lixeira").json()] == [projeto["id"]]

    c.post(f"/toc/projetos/{projeto['id']}/restaurar")
    aberto = c.get(f"/toc/projetos/{projeto['id']}").json()
    assert aberto["estado"] == "ativo"
    assert [n["id"] for n in aberto["nos"]] == [no["id"]]
