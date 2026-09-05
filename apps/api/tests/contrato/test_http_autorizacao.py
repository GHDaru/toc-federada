"""Fail-closed rota a rota — e a contagem que impede o portão de responder sobre nada.

Este arquivo é o par HTTP do `tests/aplicacao/test_politica_de_capacidades.py`. Lá a
contagem é por caso de uso e por árvore sintática; aqui é pela **superfície publicada**:
toda rota que a aplicação expõe sob `/toc` é enumerada a partir do próprio `app.routes`,
nenhuma é digitada à mão, e o teste falha se aparecer rota sem amostra de pedido. É o que
responde à regra R2 do `CLAUDE.md` — um verde que não diz quanto examinou não é evidência.

A separação entre `401` e `403` não é estética. `401 UNAUTHENTICATED` é "não sei quem é
você"; `403 UNAUTHORIZED` é "sei quem é você e a política nega". O Anexo A §A.7 do Padrão
APH (Aplicação ↔ Harness) registra a confusão entre os dois como ressalva de lastro do
laboratório A, que emite `UNAUTHORIZED` para falha de autenticação
(`ghdaru/apps/api/src/ghdaru_api/conversation/domain/wire.py:161`, leitura apenas).
"""
from __future__ import annotations

import json

import pytest

from toc_api.http.erros import CODIGOS_ACRESCENTADOS

from .conftest import (
    ERRO_SCHEMA_APH,
    schema_de_erro_da_norma,
    valida_envelope_de_erro,
)

#: O escopo desta contagem: a superfície dos módulos M1 (núcleo de diagramas) e M2
#: (Árvore da Realidade Atual). A superfície federada — catálogo de ações, proposta,
#: snapshot e o fio — vive sob outros prefixos e carrega os seus próprios testes de
#: recusa em `tests/federacao/`. Declarar o escopo é o que impede este arquivo de fingir
#: cobrir o que não cobre, e de ficar vermelho por trabalho alheio.
PREFIXOS_DESTE_LOTE = ("/toc/projetos", "/toc/ara")

BOM = "A taxa de erros no processo X é de 15%."
SEGUNDO = "O retrabalho consome a equipe de análise."
TERCEIRO = "O prazo de entrega escorrega todo mês."

#: As rotas que um principal com APENAS `toc:read` alcança. Escrita à mão de propósito:
#: se uma rota MUTADORA passar a ser alcançável por leitura, esta lista não muda e o
#: teste cai. Uma lista derivada do código concordaria com o defeito.
ROTAS_DE_LEITURA = {
    ("GET", "/toc/projetos"),
    ("GET", "/toc/projetos/lixeira"),
    ("GET", "/toc/projetos/{projeto_id}"),
    ("GET", "/toc/ara/projetos/{projeto_id}"),
    # Validar o texto de um Efeito Indesejável (UDE) é função pura: não grava nada.
    ("POST", "/toc/ara/validacoes"),
}

#: Um corpo VÁLIDO por rota — para a recusa ser por capacidade e não por esquema.
#: A cobertura desta tabela contra `app.routes` é o próprio teste.
CORPOS = {
    ("POST", "/toc/projetos"): {"nome": "Tentativa"},
    ("DELETE", "/toc/projetos/{projeto_id}"): None,
    ("POST", "/toc/projetos/{projeto_id}/restaurar"): None,
    ("POST", "/toc/projetos/{projeto_id}/nos"): {"titulo": BOM},
    ("PATCH", "/toc/projetos/{projeto_id}/nos/{no_id}"): {"titulo": SEGUNDO},
    ("DELETE", "/toc/projetos/{projeto_id}/nos/{no_id}"): None,
    ("POST", "/toc/projetos/{projeto_id}/arestas"): "@ligar",
    ("PATCH", "/toc/projetos/{projeto_id}/arestas/{aresta_id}"): {"rotulo": "porque"},
    ("DELETE", "/toc/projetos/{projeto_id}/arestas/{aresta_id}"): None,
    ("POST", "/toc/ara/projetos"): {"nome": "Tentativa ARA"},
    ("POST", "/toc/ara/projetos/{projeto_id}/efeitos"): {"titulo": BOM},
    ("POST", "/toc/ara/projetos/{projeto_id}/nos/{no_id}/ude"): {},
    ("DELETE", "/toc/ara/projetos/{projeto_id}/nos/{no_id}/ude"): None,
    ("PUT", "/toc/ara/projetos/{projeto_id}/nos/{no_id}/ficha"): {"area_impactada": "X"},
    ("POST", "/toc/ara/projetos/{projeto_id}/nos/{no_id}/reformulacoes"): {"texto": SEGUNDO},
    ("POST", "/toc/ara/projetos/{projeto_id}/nos/{no_id}/pareceres"): {
        "favoravel": True,
        "justificativa": "Parece contínuo.",
    },
    ("PUT", "/toc/ara/projetos/{projeto_id}/nos/{no_id}/status"): {"status": "rejeitado"},
    ("PUT", "/toc/ara/projetos/{projeto_id}/arestas/{aresta_id}/exame"): {
        "estado": "suficiente"
    },
    ("POST", "/toc/ara/projetos/{projeto_id}/conectores"): "@conector",
    ("DELETE", "/toc/ara/projetos/{projeto_id}/conectores/{conector_id}"): None,
    ("POST", "/toc/ara/projetos/{projeto_id}/analises"): None,
    ("GET", "/toc/projetos"): None,
    ("GET", "/toc/projetos/lixeira"): None,
    ("GET", "/toc/projetos/{projeto_id}"): None,
    ("GET", "/toc/ara/projetos/{projeto_id}"): None,
    ("POST", "/toc/ara/validacoes"): {"texto": BOM},
}


def rotas_do_toc(app) -> list[tuple[str, str]]:
    """A superfície como o CLIENTE a vê: lida do documento OpenAPI publicado.

    Enumerar por `app.routes` seria enumerar a árvore interna do framework — que na
    versão instalada aninha os roteadores incluídos em `_IncludedRouter` e devolveria
    zero rota, um verde sobre nada. O OpenAPI é o contrato publicado, e é contra ele que
    a contagem tem sentido.
    """
    caminhos = app.openapi()["paths"]
    return sorted(
        (metodo.upper(), gabarito)
        for gabarito, operacoes in caminhos.items()
        if gabarito.startswith(PREFIXOS_DESTE_LOTE)
        for metodo in operacoes
        if metodo.lower() in {"get", "post", "put", "patch", "delete"}
    )


@pytest.fixture()
def cenario(plena):
    """Um projeto ARA completo — nós, aresta e conector — para as rotas terem alvo real."""
    projeto = plena.post("/toc/ara/projetos", json={"nome": "Horizonte — ARA"}).json()
    def efeito(titulo):
        return plena.post(
            f"/toc/ara/projetos/{projeto['id']}/efeitos", json={"titulo": titulo}
        ).json()

    a, b, c = efeito(BOM), efeito(SEGUNDO), efeito(TERCEIRO)
    ac = plena.post(
        f"/toc/projetos/{projeto['id']}/arestas",
        json={"origem_id": a["id"], "destino_id": c["id"]},
    ).json()
    bc = plena.post(
        f"/toc/projetos/{projeto['id']}/arestas",
        json={"origem_id": b["id"], "destino_id": c["id"]},
    ).json()
    plena.post(f"/toc/ara/projetos/{projeto['id']}/nos/{a['id']}/ude", json={})
    conector = plena.post(
        f"/toc/ara/projetos/{projeto['id']}/conectores",
        json={"arestas": [ac["id"], bc["id"]]},
    ).json()
    return {
        "projeto_id": projeto["id"],
        "no_id": a["id"],
        "aresta_id": ac["id"],
        "conector_id": conector["id"],
        "ligar": {"origem_id": b["id"], "destino_id": a["id"]},
        "conector_novo": {"arestas": [ac["id"], bc["id"]]},
    }


def dispara(cliente, metodo, gabarito, cenario):
    caminho = gabarito.format(**{k: cenario[k] for k in ("projeto_id", "no_id", "aresta_id", "conector_id") if "{" + k + "}" in gabarito})
    corpo = CORPOS[(metodo, gabarito)]
    if corpo == "@ligar":
        corpo = cenario["ligar"]
    elif corpo == "@conector":
        corpo = cenario["conector_novo"]
    return cliente.request(metodo, caminho, json=corpo)


def test_a_tabela_de_amostras_cobre_TODA_rota_publicada(app):
    """Sem isto, os testes abaixo ficariam verdes sobre o subconjunto que alguém lembrou."""
    publicadas = set(rotas_do_toc(app))
    faltando = sorted(publicadas - set(CORPOS))
    sobrando = sorted(set(CORPOS) - publicadas)
    print(f"\nrotas publicadas sob /toc: {len(publicadas)}")
    assert faltando == [], f"rota publicada sem amostra de pedido: {faltando}"
    assert sobrando == [], f"amostra para rota que não existe: {sobrando}"
    assert len(publicadas) >= 26


def test_toda_rota_recusa_quem_nao_tem_capacidade_nenhuma(app, sem_capacidade, cenario):
    """Identidade ATIVA, conjunto de capacidades vazio: nada passa (fail-closed puro)."""
    rotas = rotas_do_toc(app)
    for metodo, gabarito in rotas:
        r = dispara(sem_capacidade, metodo, gabarito, cenario)
        assert r.status_code == 403, f"{metodo} {gabarito} respondeu {r.status_code}"
        erro = valida_envelope_de_erro(r)
        assert erro["code"] == "UNAUTHORIZED"
        assert erro["details"]["capacidade"] in {"toc:read", "toc:write"}
    print(f"\nrotas recusadas para principal sem capacidade: {len(rotas)} de {len(rotas)}")


def test_a_leitora_alcanca_a_leitura_e_e_recusada_em_TODA_mutacao(app, leitora, cenario):
    rotas = rotas_do_toc(app)
    passaram, recusadas = [], []
    for metodo, gabarito in rotas:
        r = dispara(leitora, metodo, gabarito, cenario)
        if r.status_code == 403:
            assert valida_envelope_de_erro(r)["details"]["capacidade"] == "toc:write"
            recusadas.append((metodo, gabarito))
        else:
            passaram.append((metodo, gabarito))
    print(
        f"\ncom `toc:read` apenas — alcançadas: {len(passaram)}, "
        f"recusadas: {len(recusadas)}, de {len(rotas)} rotas"
    )
    assert set(passaram) == ROTAS_DE_LEITURA
    assert set(recusadas) == set(rotas) - ROTAS_DE_LEITURA
    assert len(recusadas) >= 21


def test_sem_identidade_TODA_rota_responde_401_com_o_desafio(app, anonima, cenario):
    rotas = rotas_do_toc(app)
    for metodo, gabarito in rotas:
        r = dispara(anonima, metodo, gabarito, cenario)
        assert r.status_code == 401, f"{metodo} {gabarito} respondeu {r.status_code}"
        assert r.headers.get("www-authenticate") == "Bearer"
        assert valida_envelope_de_erro(r)["code"] == "UNAUTHENTICATED"
    print(f"\nrotas que exigem identidade: {len(rotas)} de {len(rotas)}")


@pytest.mark.parametrize(
    "cabecalho",
    [
        "Bearer tok-que-nao-existe",
        "Bearer ",
        "Basic dXNlcjpzZW5oYQ==",
        "tok-sem-esquema",
        "",
    ],
)
def test_credencial_ruim_responde_sempre_igual_sem_dizer_o_motivo(app, plena, cabecalho):
    """§B.6.5: inexistente, expirado e já consumido respondem a MESMA coisa."""
    plena.headers["Authorization"] = cabecalho
    r = plena.get("/toc/projetos")
    assert r.status_code == 401
    erro = valida_envelope_de_erro(r)
    assert erro["code"] == "UNAUTHENTICATED"
    assert set(erro) == {"code", "message"}, "o motivo não vai em `details` — é oráculo"


def test_a_recusa_nao_muta_nada(app, leitora, plena, cenario):
    """403 é recusa, não é "aplicou e avisou": o estado tem de ficar idêntico."""
    antes = plena.get(f"/toc/ara/projetos/{cenario['projeto_id']}").json()
    for metodo, gabarito in rotas_do_toc(app):
        if (metodo, gabarito) in ROTAS_DE_LEITURA:
            continue
        dispara(leitora, metodo, gabarito, cenario)
    depois = plena.get(f"/toc/ara/projetos/{cenario['projeto_id']}").json()
    assert depois["projeto"]["versao"] == antes["projeto"]["versao"]
    assert depois == antes


# -- o registro de códigos ------------------------------------------------------------

#: O registro mínimo do §A.7, transcrito da tabela do anexo. Os 🧪 (`PROPOSAL_EXPIRED`,
#: `PROPOSAL_CONTEXT_STALE`) e os do fio (`STREAM_CANCELLED`, `PROVIDER_FAILURE`) são do
#: lote da federação e do fio, não deste.
REGISTRO_MINIMO_A7 = {
    "STREAM_CANCELLED",
    "PROVIDER_FAILURE",
    "INVALID_TRANSITION",
    "UNAUTHORIZED",
    "INVALID_CONTEXT",
    "PROPOSAL_EXPIRED",
    "PROPOSAL_CONTEXT_STALE",
}


def test_todo_codigo_acrescentado_esta_declarado_com_o_motivo():
    """O §A.7 permite acrescentar códigos; acrescentar SEM declarar é o que ele não permite."""
    assert CODIGOS_ACRESCENTADOS
    for codigo, motivo in CODIGOS_ACRESCENTADOS.items():
        assert codigo not in REGISTRO_MINIMO_A7, f"{codigo} já é do registro mínimo"
        assert codigo == codigo.upper() and codigo.replace("_", "").isalnum()
        assert len(motivo) > 20, f"{codigo} sem motivo escrito"


def test_o_codigo_emitido_em_cada_situacao_esta_no_registro(app, plena, leitora, cenario):
    """Nenhuma resposta de erro sai com código fora do registro conhecido."""
    conhecidos = REGISTRO_MINIMO_A7 | set(CODIGOS_ACRESCENTADOS)
    emitidos = set()
    respostas = [
        plena.get("/toc/projetos/00000000-0000-4000-8000-000000000000"),
        plena.post("/toc/projetos", json={}),
        plena.post(f"/toc/projetos/{cenario['projeto_id']}/arestas",
                   json={"origem_id": cenario["no_id"], "destino_id": cenario["no_id"]}),
        leitora.post("/toc/projetos", json={"nome": "x"}),
        plena.get("/toc/nao-existe"),
        plena.put("/toc/projetos"),
    ]
    for r in respostas:
        assert r.status_code >= 400, r.text
        emitidos.add(valida_envelope_de_erro(r)["code"])
    print(f"\ncódigos emitidos nas {len(respostas)} situações: {sorted(emitidos)}")
    assert emitidos <= conhecidos, f"código fora do registro: {sorted(emitidos - conhecidos)}"


def test_a_copia_local_do_schema_de_erro_nao_derivou_da_norma():
    """R5/R1: cópia sem verificação de deriva é dívida silenciosa.

    Quando o repositório `GHDaru/protocolos` está montado (leitura apenas), a cópia local
    é comparada campo a campo com `padrao/schemas/erro.schema.json`. Quando não está, o
    teste **diz** que não verificou, em vez de responder verde sobre nada.
    """
    norma = schema_de_erro_da_norma()
    if norma is None:
        pytest.skip(
            "repositório da norma não montado em /home/user/protocolos — a cópia local "
            "de `erro.schema.json` NÃO foi comparada nesta execução"
        )
    for chave in ("type", "required", "additionalProperties", "properties"):
        assert ERRO_SCHEMA_APH[chave] == norma[chave], f"deriva em `{chave}`"


def test_saude_declara_qual_adaptador_de_identidade_esta_de_pe(app):
    from fastapi.testclient import TestClient

    corpo = TestClient(app).get("/saude").json()
    assert corpo["identidade"] == "ProvedorDeIdentidadeFalso"
    assert "TOC_IDENTIDADES_FALSAS" not in json.dumps(corpo)


def test_toda_rota_do_toc_declara_o_esquema_da_resposta(app):
    """Rota sem contrato declarado é rota que não pode ser validada contra contrato."""
    documento = app.openapi()
    sem_contrato = []
    for metodo, gabarito in rotas_do_toc(app):
        operacao = documento["paths"][gabarito][metodo.lower()]
        sucesso = [c for c in operacao["responses"] if c.startswith("2")]
        assert len(sucesso) == 1, f"{metodo} {gabarito} declara {sucesso}"
        corpo = operacao["responses"][sucesso[0]].get("content")
        if sucesso[0] != "204" and corpo is None:
            sem_contrato.append((metodo, gabarito))
    assert sem_contrato == []
