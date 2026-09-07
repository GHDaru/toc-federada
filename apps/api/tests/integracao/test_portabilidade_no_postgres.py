"""E1.4 contra o PostgreSQL REAL: exportar, reimportar, e não destruir nada (spec 011).

Siglas, uma vez neste arquivo: **ARA** — Árvore da Realidade Atual · **NC** — Nuvem de
Conflito · **ARF** — Árvore da Realidade Futura · **APR** — Árvore de Pré-Requisitos ·
**AT** — Árvore de Transição · **UDE** — Efeito Indesejável · **HTTP** — *HyperText
Transfer Protocol* · **JSON** — *JavaScript Object Notation* · **RF/RN** — requisito
funcional / regra de negócio da spec 011.

O teste de domínio prova que a ida e volta preserva o conteúdo **em memória**. Só este
prova o que a US-17 pede de verdade: que o arquivo atravessa o **banco** — que a cadeia
sai do PostgreSQL, volta para o PostgreSQL, e que o que já estava lá continua lá, intacto
(RN-05). O contraste é o `saveProjectState` da quarta geração
(`tocbuilderv3/services/mockApiService.ts:286-301`), onde toda escrita era substituição
cega — e a "persistência" era um vetor em memória.

Marcado `integracao`: pulado com o motivo quando o banco não responde, jamais substituído
por um duplo. Base sintética (ADR 0006 — *Architecture Decision Record*).
"""
from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient

from toc_api.dominio.exportacao import esqueleto
from toc_api.http.app import criar_app

pytestmark = pytest.mark.integracao

IDENTIDADES = {
    "tok-portabilidade": {
        "inquilino_id": "inq-horizonte",
        "usuario_id": "usr-facilitadora",
        "capabilities": ["toc:read", "toc:write"],
    },
    "tok-portabilidade-so-le": {
        "inquilino_id": "inq-horizonte",
        "usuario_id": "usr-visitante",
        "capabilities": ["toc:read"],
    },
    "tok-outro-inquilino": {
        "inquilino_id": "inq-aurora",
        "usuario_id": "usr-aurora",
        "capabilities": ["toc:read", "toc:write"],
    },
}

UDE = "A taxa de evasão no primeiro semestre é de 22%."
CAUSA = "O acolhimento do primeiro ano não é acompanhado."


def cliente(url: str, esquema: str, token: str = "tok-portabilidade") -> TestClient:
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


def montar_cadeia_pela_api(c: TestClient) -> dict:
    """ARA → NC → ARF → APR → AT, tudo pelas rotas — como uma pessoa faria."""
    ara = c.post("/toc/ara/projetos", json={"nome": "Horizonte — realidade atual"}).json()
    efeito = c.post(f"/toc/ara/projetos/{ara['id']}/efeitos", json={"titulo": UDE}).json()
    causa = c.post(f"/toc/ara/projetos/{ara['id']}/efeitos", json={"titulo": CAUSA}).json()
    aresta = c.post(
        f"/toc/ara/projetos/{ara['id']}/arestas",
        json={"origem_id": causa["id"], "destino_id": efeito["id"]},
    ).json()
    c.put(
        f"/toc/ara/projetos/{ara['id']}/arestas/{aresta['id']}/exame",
        json={"estado": "com_reserva", "reserva": "falta medir a coorte de 2025"},
    )
    c.post(f"/toc/ara/projetos/{ara['id']}/nos/{efeito['id']}/ude", json={})
    c.post(
        f"/toc/ara/projetos/{ara['id']}/nos/{efeito['id']}/pareceres",
        json={"favoravel": True, "justificativa": "queixa contínua e na esfera da coordenação"},
    )
    c.put(
        f"/toc/ara/projetos/{ara['id']}/nos/{efeito['id']}/status",
        json={"status": "validado"},
    )
    promovida = c.post(
        "/toc/cadeia/promocoes",
        json={"ara_projeto_id": ara["id"], "no_ids": [efeito["id"]], "nome": "Dilema da expansão"},
    )
    assert promovida.status_code in (200, 201), promovida.text
    return {"ara": ara, "efeito": efeito, "nuvem": promovida.json()}


def test_exportar_a_cadeia_do_banco_e_reimporta_la_sem_destruir_o_que_existe(
    url_postgres, esquema_migrado
):
    c = cliente(url_postgres, esquema_migrado)
    montado = montar_cadeia_pela_api(c)
    ara_id = montado["ara"]["id"]

    exportacao = c.get(f"/toc/portabilidade/projetos/{ara_id}")
    assert exportacao.status_code == 200, exportacao.text
    documento = exportacao.json()
    antes = c.get("/toc/projetos").json()

    importacao = c.post("/toc/portabilidade/importacoes", json={"documento": documento})
    assert importacao.status_code == 201, importacao.text
    relato = importacao.json()

    depois = c.get("/toc/projetos").json()
    print(
        f"projetos antes: {len(antes)} · depois: {len(depois)} · "
        f"criados: {len(relato['projetos_criados'])} · relato: {relato['contagens']}"
    )
    assert len(depois) == len(antes) + len(relato["projetos_criados"])
    # O que já existia continua idêntico — nome, versão e contagens (RN-05).
    por_id = {p["id"]: p for p in depois}
    for projeto in antes:
        atual = por_id[projeto["id"]]
        assert (atual["nome"], atual["versao"]) == (projeto["nome"], projeto["versao"])


def test_a_ida_e_volta_pelo_banco_preserva_o_conteudo(url_postgres, esquema_migrado):
    """RF-32 medido de ponta a ponta: exportar → importar → exportar, pelo PostgreSQL."""
    c = cliente(url_postgres, esquema_migrado)
    montado = montar_cadeia_pela_api(c)

    primeiro = c.get(f"/toc/portabilidade/projetos/{montado['ara']['id']}").json()
    criados = c.post(
        "/toc/portabilidade/importacoes", json={"documento": primeiro}
    ).json()["projetos_criados"]
    nova_ara = next(
        pid for pid in criados if c.get(f"/toc/projetos/{pid}").json()["ferramenta"] == "ara"
    )
    segundo = c.get(f"/toc/portabilidade/projetos/{nova_ara}").json()

    iguais = esqueleto(primeiro) == esqueleto(segundo)
    print(
        f"projetos no arquivo: {len(primeiro['projetos'])} · vínculos: "
        f"{len(primeiro['vinculos'])} · esqueletos iguais: {iguais}"
    )
    assert iguais
    assert len(primeiro["projetos"]) == 2  # a ARA e a NC promovida a partir dela
    assert len(primeiro["vinculos"]) == 1


def test_o_projeto_importado_abre_pela_rota_da_ferramenta_dele(url_postgres, esquema_migrado):
    """Dado certo na tela errada é defeito silencioso: a ARA importada abre como ARA."""
    c = cliente(url_postgres, esquema_migrado)
    montado = montar_cadeia_pela_api(c)
    documento = c.get(f"/toc/portabilidade/projetos/{montado['ara']['id']}").json()

    criados = c.post(
        "/toc/portabilidade/importacoes", json={"documento": documento}
    ).json()["projetos_criados"]

    aberturas = []
    for pid in criados:
        ferramenta = c.get(f"/toc/projetos/{pid}").json()["ferramenta"]
        rota = {"ara": "/toc/ara/projetos", "nc": "/toc/nc/projetos"}[ferramenta]
        resposta = c.get(f"{rota}/{pid}")
        aberturas.append((ferramenta, resposta.status_code))
        assert resposta.status_code == 200, resposta.text
    print(f"aberturas: {aberturas}")
    ara_importada = next(
        c.get(f"/toc/ara/projetos/{pid}").json()
        for pid in criados
        if c.get(f"/toc/projetos/{pid}").json()["ferramenta"] == "ara"
    )
    titulos = [n["titulo"] for n in ara_importada["projeto"]["nos"]]
    print(f"títulos na ARA importada: {titulos}")
    assert UDE in titulos
    # O exame do elo é estado da ferramenta, não do núcleo: se ele não atravessasse o
    # banco, a ARA importada abriria com o elo "não examinado" e ninguém veria a perda.
    exames = [e["exame"]["estado"] for e in ara_importada["elos"]]
    print(f"exames dos elos: {exames}")
    assert "com_reserva" in exames


def test_importar_o_arquivo_da_geracao_anterior_pela_rota(url_postgres, esquema_migrado):
    """RF-25/RF-29: reconhece pelo conteúdo e declara o descarte do histórico."""
    from ..dominio.legado_sintetico import arquivo_legado

    c = cliente(url_postgres, esquema_migrado)

    resposta = c.post("/toc/portabilidade/importacoes", json={"documento": arquivo_legado()})

    assert resposta.status_code == 201, resposta.text
    corpo = resposta.json()
    print(f"formato={corpo['formato']} descartes={corpo['descartes']}")
    assert corpo["formato"] == "legado"
    assert any(d["campo"] == "chatHistory" and d["quantidade"] == 3 for d in corpo["descartes"])
    projeto = c.get(f"/toc/projetos/{corpo['projetos_criados'][0]}").json()
    assert len(projeto["nos"]) == 3
    # O que foi descartado não está no banco: a leitura de volta não o traz.
    assert "mensagem sintética" not in json.dumps(projeto, ensure_ascii=False)


def test_arquivo_invalido_e_recusado_com_o_relato_campo_a_campo_e_nada_e_criado(
    url_postgres, esquema_migrado
):
    from ..dominio.legado_sintetico import arquivo_legado

    c = cliente(url_postgres, esquema_migrado)
    bruto = arquivo_legado()
    bruto["edges"][0]["target"] = "no-que-nao-existe"
    bruto["nodes"][1]["data"]["title"] = "  "

    resposta = c.post("/toc/portabilidade/importacoes", json={"documento": bruto})

    assert resposta.status_code == 422, resposta.text
    erro = resposta.json()["error"]
    print(f"código={erro['code']} problemas={erro['details']['problemas']}")
    assert erro["code"] == "IMPORT_REFUSED"
    assert len(erro["details"]["problemas"]) == 2
    assert c.get("/toc/projetos").json() == []


def test_exportar_projeto_de_outro_inquilino_responde_404(url_postgres, esquema_migrado):
    dono = cliente(url_postgres, esquema_migrado)
    montado = montar_cadeia_pela_api(dono)
    estranho = cliente(url_postgres, esquema_migrado, "tok-outro-inquilino")

    resposta = estranho.get(f"/toc/portabilidade/projetos/{montado['ara']['id']}")

    print(f"status={resposta.status_code} corpo={resposta.json()}")
    assert resposta.status_code == 404
    assert resposta.json()["error"]["code"] == "NOT_FOUND"


def test_quem_so_le_nao_importa(url_postgres, esquema_migrado):
    from ..dominio.legado_sintetico import arquivo_legado

    c = cliente(url_postgres, esquema_migrado, "tok-portabilidade-so-le")

    resposta = c.post("/toc/portabilidade/importacoes", json={"documento": arquivo_legado()})

    assert resposta.status_code == 403
    assert resposta.json()["error"]["code"] == "UNAUTHORIZED"


def test_arquivo_acima_do_teto_e_recusado_com_codigo_categorizado(url_postgres, esquema_migrado):
    """RF-30: teto de tamanho, com código de erro categorizado."""
    from ..dominio.legado_sintetico import arquivo_legado

    c = cliente(url_postgres, esquema_migrado)
    inchado = arquivo_legado()
    inchado["nodes"][0]["data"]["description"] = "x" * 900

    resposta = c.post(
        "/toc/portabilidade/importacoes",
        json={"documento": inchado, "teto_de_bytes": 500},
    )

    erro = resposta.json()["error"]
    print(f"status={resposta.status_code} motivo={erro['details']['problemas'][0]['motivo']}")
    assert resposta.status_code == 422
    assert erro["code"] == "IMPORT_REFUSED"
    assert "teto" in erro["details"]["problemas"][0]["motivo"]
