"""A regressão do catálogo federado, reproduzida de ponta a ponta contra o Postgres real.

Siglas, uma vez neste arquivo: **APH** — Aplicação ↔ Harness · **ARA** — Árvore da
Realidade Atual · **NC** — Nuvem de Conflito · **ARF** — Árvore da Realidade Futura ·
**APR** — Árvore de Pré-Requisitos · **AT** — Árvore de Transição · **S&T** — Estratégia
& Táticas · **UDE** — Efeito Indesejável · **HTTP** — *HyperText Transfer Protocol* ·
**M1** — Núcleo de Diagramas Lógicos · **IA** — inteligência artificial.

Este arquivo nasceu como sonda sem asserção — impressões que ninguém podia reprovar. Ele
é agora o teste que o achado exigia: **proposta de verdade, gate humano de verdade, banco
de verdade**, uma ferramenta por vez.

O percurso é o do crítico: criar o projeto pela rota da ferramenta, propor a ação
mutadora pelo `POST /toc/propostas`, aprovar em `POST /toc/propostas/{id}/decisao`, e ler
o desfecho. Antes do ADR 0015 a Árvore da Realidade Atual voltava `failed` com "o grafo de
um projeto da ferramenta 'ara' só muda pela raiz" — a assistência da fundação não
alcançava a ferramenta principal do produto.

E o outro lado, no mesmo arquivo de propósito: a ação **genérica** do M1 continua recusada
em todas as ferramentas com raiz. As duas coisas ao mesmo tempo, senão trocamos um defeito
por outro.
"""
from __future__ import annotations

import json
import os
import pathlib
import subprocess
import uuid

import pytest
from fastapi.testclient import TestClient

from toc_api.http.app import criar_app

from .conftest import _derruba, liberar_conexoes

pytestmark = pytest.mark.integracao

IDENTIDADES = {
    "tok": {
        "inquilino_id": "inq-horizonte",
        "usuario_id": "usr-facilitadora",
        "capabilities": ["toc:read", "toc:write"],
    }
}

#: Enunciados sintéticos (ADR 0006) — nenhuma pessoa real, nenhum trabalho real.
UDE_UM = "A evasão no primeiro semestre aumenta a cada entrada."
UDE_DOIS = "A taxa de reprovação em cálculo cresce todo ano."


@pytest.fixture(scope="module")
def esquema_do_modulo(url_postgres):
    """Um esquema migrado para o arquivo inteiro, derrubado no fim.

    Por que módulo e não função: cada `criar_app` monta um motor com *pool* próprio, e o
    cluster de desenvolvimento medido aqui tem `max_connections = 100` — cinco aplicações
    a mais no arquivo custam conexões que a suíte inteira não tem de sobra. Os cinco
    testes deste arquivo semeiam os **seus** projetos e só afirmam sobre eles, então
    dividir o esquema não divide estado que alguma asserção leia.
    """
    nome = f"teste_{uuid.uuid4().hex[:12]}"
    ambiente = {**os.environ, "DATABASE_URL": url_postgres, "TOC_DB_SCHEMA": nome}
    executado = subprocess.run(
        ["alembic", "upgrade", "head"],
        cwd=pathlib.Path(__file__).resolve().parents[2],
        env=ambiente, capture_output=True, text=True,
    )
    if executado.returncode != 0:
        _derruba(url_postgres, nome)
        raise AssertionError(f"alembic upgrade head falhou:\n{executado.stderr}")
    try:
        yield nome
    finally:
        _derruba(url_postgres, nome)


@pytest.fixture(scope="module")
def cliente(url_postgres, esquema_do_modulo):
    """Uma aplicação para o arquivo — e o *pool* dela devolvido ao cluster no fim."""
    app = criar_app(
        {
            "DATABASE_URL": url_postgres,
            "TOC_DB_SCHEMA": esquema_do_modulo,
            "TOC_AMBIENTE": "teste",
            "TOC_IDENTIDADES_FALSAS": json.dumps(IDENTIDADES),
        }
    )
    c = TestClient(app)
    c.headers["Authorization"] = "Bearer tok"
    try:
        yield c
    finally:
        liberar_conexoes([c])


def ciclo(c: TestClient, action_id: str, args: dict) -> dict:
    """Propõe, aprova no gate humano e devolve o corpo do desfecho."""
    proposta = c.post("/toc/propostas", json={"action_id": action_id, "args": args})
    assert proposta.status_code == 201, (action_id, proposta.status_code, proposta.text)
    corpo = proposta.json()
    if corpo["estado"] == "executed":  # ação de leitura executa direto (APH-5.2)
        return corpo
    decisao = c.post(
        f"/toc/propostas/{corpo['proposal_id']}/decisao", json={"aprovado": True}
    )
    assert decisao.status_code == 200, (action_id, decisao.status_code, decisao.text)
    return decisao.json()


def detalhe(desfecho: dict) -> str:
    if desfecho.get("outcomes"):
        return "; ".join(f"{o['target']}: {o['status']} {o['message']}"
                         for o in desfecho["outcomes"])
    return str(desfecho.get("mensagem"))


def semear(c: TestClient) -> dict[str, str]:
    """Um projeto de cada ferramenta, pela rota da ferramenta — nunca pela genérica."""
    projetos: dict[str, str] = {}
    projetos["generico"] = c.post("/toc/projetos", json={"nome": "Rascunho livre"}).json()["id"]
    projetos["ara"] = c.post(
        "/toc/ara/projetos", json={"nome": "Evasão no ciclo básico"}
    ).json()["id"]
    projetos["nc"] = c.post("/toc/nc/projetos", json={"nome": "Dilema da expansão"}).json()["id"]
    projetos["arf"] = c.post("/toc/arf/projetos", json={"nome": "Futuro da expansão"}).json()["id"]
    projetos["apr"] = c.post(
        "/toc/apr/projetos",
        json={"nome": "Implantação", "objetivo": "O faseamento está implantado"},
    ).json()["id"]
    projetos["at"] = c.post("/toc/at/projetos", json={"nome": "Transição"}).json()["id"]
    projetos["snt"] = c.post(
        "/toc/snt/projetos", json={"nome": "Estratégia", "meta_global": "Crescer com qualidade"}
    ).json()["id"]
    projetos["focalizacao"] = c.post(
        "/toc/focalizacao/analises",
        json={"nome": "Focalização do ciclo básico", "sistema": "Oferta do ciclo básico"},
    ).json()["projeto"]["id"]
    return projetos


# --------------------------------------------------------------------------------------
# 1. A assistência da fundação ESCREVE na Árvore da Realidade Atual (o achado)
# --------------------------------------------------------------------------------------


def test_a_proposta_em_lote_registra_dois_udes_na_ara_e_o_desfecho_diz_executed(cliente) -> None:
    """O percurso exato do crítico: dois alvos, uma confirmação, desfecho por alvo."""
    projetos = semear(cliente)

    desfecho = ciclo(
        cliente,
        "toc.suggest_udes",
        {"projeto_id": projetos["ara"], "udes": [{"texto": UDE_UM}, {"texto": UDE_DOIS}]},
    )

    print(f"\ntoc.suggest_udes sobre a ARA → {desfecho['status']} :: {detalhe(desfecho)}")
    assert desfecho["status"] == "executed", detalhe(desfecho)
    assert [o["status"] for o in desfecho["outcomes"]] == ["executed", "executed"]

    ara = cliente.get(f"/toc/ara/projetos/{projetos['ara']}").json()
    titulos = sorted(n["titulo"] for n in ara["projeto"]["nos"])
    print(f"nós persistidos: {titulos}")
    assert titulos == sorted([UDE_UM, UDE_DOIS])
    # RF-32: o UDE sugerido nasce MARCADO — o que dispara a validação formal, que é regra
    # de domínio pura. Se ele nascesse nó solto, a ficha não existiria e o produto teria
    # ganho dois nós sem o exame que é a razão de a ferramenta existir.
    print(f"UDEs com ficha: {len(ara['udes'])} de {len(ara['projeto']['nos'])}; "
          f"status: {ara['resumo_por_status']}")
    assert len(ara["udes"]) == 2
    assert all(u["validacao"] for u in ara["udes"]), "UDE sem validação formal executada"


def test_causa_e_relacao_entram_pela_raiz_com_o_elo_nascendo_nao_examinado(cliente) -> None:
    """INT-03/INT-04: a causa nasce ligada, e todo elo da ARA nasce por examinar (RF-22)."""
    projetos = semear(cliente)
    ciclo(cliente, "toc.suggest_udes", {"projeto_id": projetos["ara"], "udes": [{"texto": UDE_UM}]})
    ara = cliente.get(f"/toc/ara/projetos/{projetos['ara']}").json()
    alvo = ara["projeto"]["nos"][0]["id"]

    desfecho = ciclo(
        cliente,
        "toc.suggest_causes",
        {
            "projeto_id": projetos["ara"],
            "no_id": alvo,
            "causas": [{"texto": "A turma entra sem o pré-requisito de álgebra"}],
        },
    )

    print(f"toc.suggest_causes → {desfecho['status']} :: {detalhe(desfecho)}")
    assert desfecho["status"] == "executed", detalhe(desfecho)
    ara = cliente.get(f"/toc/ara/projetos/{projetos['ara']}").json()
    assert len(ara["projeto"]["nos"]) == 2
    assert len(ara["projeto"]["arestas"]) == 1
    exames = [e["exame"]["estado"] for e in ara["elos"]]
    print(f"elos: {len(ara['elos'])}; exames: {exames}; leitura: {ara['elos'][0]['leitura']}")
    assert exames == ["nao_examinado"]


# --------------------------------------------------------------------------------------
# 2. Cada ferramenta com raiz tem ação mutadora que executa — no banco de verdade
# --------------------------------------------------------------------------------------


def test_cada_ferramenta_com_raiz_e_alcancada_pelo_catalogo_federado(cliente) -> None:
    projetos = semear(cliente)
    ara = projetos["ara"]
    ciclo(cliente, "toc.suggest_udes", {"projeto_id": ara, "udes": [{"texto": UDE_UM}]})
    no_da_ara = cliente.get(f"/toc/ara/projetos/{ara}").json()["projeto"]["nos"][0]["id"]
    injecao = cliente.post(
        f"/toc/arf/projetos/{projetos['arf']}/nos",
        json={
            "papel": "injecao",
            "titulo": "faseamento orçamentário condicionado a marco de receita",
        },
    ).json()["id"]

    casos = {
        "ara": ("toc.suggest_udes", {"projeto_id": ara, "udes": [{"texto": UDE_DOIS}]}),
        "nc": (
            "toc.suggest_assumptions",
            {
                "projeto_id": projetos["nc"],
                "aresta": "A_B",
                "texto": "Crescer exige atender mais turmas com a mesma equipe.",
            },
        ),
        "arf": (
            "toc.suggest_future_effects",
            {
                "projeto_id": projetos["arf"],
                "injecao_id": injecao,
                "texto": "As duas frentes recebem verba no trimestre.",
            },
        ),
        "apr": (
            "toc.suggest_obstacles",
            {
                "projeto_id": projetos["apr"],
                "texto": "Não há hoje sala disponível no turno da noite",
            },
        ),
        "at": (
            "toc.suggest_transition_steps",
            {
                "projeto_id": projetos["at"],
                "acao": "publicar a chamada interna de treinamento",
                "necessidade": "não há hoje candidato mapeado",
                "resultado_esperado": "lista de inscritos até sexta",
            },
        ),
        "focalizacao": (
            "toc.suggest_constraint",
            {
                "projeto_id": projetos["focalizacao"],
                "ara_projeto_id": ara,
                "no_id": no_da_ara,
                "descricao": "A oferta de laboratório limita as turmas do ciclo básico",
                "tipo": "fisica",
                "justificativa": "É o nó com mais efeitos a jusante na árvore",
            },
        ),
    }

    resultados = []
    for ferramenta, (action_id, args) in casos.items():
        desfecho = ciclo(cliente, action_id, args)
        resultados.append((ferramenta, action_id, desfecho["status"], detalhe(desfecho)))

    print("\n── catálogo federado × ferramenta ──")
    for ferramenta, action_id, status, msg in resultados:
        print(f"  {ferramenta:12s} {action_id:32s} → {status} :: {msg}")
    reprovadas = [(f, m) for f, _, s, m in resultados if s != "executed"]
    assert reprovadas == [], reprovadas
    print(f"  ferramentas com raiz alcançadas: {len(resultados)} de {len(resultados)}")


# --------------------------------------------------------------------------------------
# 3. A porta dos fundos continua fechada — no MESMO banco, pelo MESMO caminho
# --------------------------------------------------------------------------------------


def test_a_acao_generica_do_m1_continua_recusada_em_toda_ferramenta_com_raiz(cliente) -> None:
    """E o `generico` continua funcionando: é lá que o `Projeto` É a raiz do agregado."""
    projetos = semear(cliente)

    resultados = []
    for ferramenta, pid in projetos.items():
        desfecho = ciclo(
            cliente,
            "toc.criar_nos",
            {"projeto_id": pid, "nos": [{"titulo": "no entrando por fora da raiz", "tipo": "ude"}]},
        )
        resultados.append((ferramenta, desfecho["status"], detalhe(desfecho)))

    print("\n── toc.criar_nos (ação do projeto genérico) × ferramenta ──")
    for ferramenta, status, msg in resultados:
        print(f"  {ferramenta:12s} → {status} :: {msg}")

    por_ferramenta = {f: s for f, s, _ in resultados}
    assert por_ferramenta["generico"] == "executed"
    com_raiz = {f: s for f, s in por_ferramenta.items() if f != "generico"}
    assert set(com_raiz.values()) == {"failed"}, com_raiz
    print(f"  ferramentas com raiz que recusaram: {len(com_raiz)} de {len(com_raiz)}")

    # A ARA saiu intacta: a recusa não é meia-mutação.
    ara = cliente.get(f"/toc/ara/projetos/{projetos['ara']}").json()
    print(f"  nós na ARA depois da tentativa: {len(ara['projeto']['nos'])}")
    assert ara["projeto"]["nos"] == []


def test_a_recusa_diz_qual_e_a_acao_certa_daquela_ferramenta(cliente) -> None:
    """Recusa que não ensina a acertar transforma assistência governada em beco sem saída."""
    projetos = semear(cliente)

    desfecho = ciclo(
        cliente,
        "toc.criar_nos",
        {"projeto_id": projetos["ara"], "nos": [{"titulo": "no invasor", "tipo": "ude"}]},
    )

    mensagem = detalhe(desfecho)
    print(f"\nrecusa sobre a ARA: {mensagem}")
    assert desfecho["status"] == "failed"
    assert "'ara'" in mensagem
    assert "toc.suggest_udes" in mensagem, (
        "a recusa não nomeou a ação certa — a fundação não teria como se corrigir"
    )
