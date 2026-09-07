"""TODA ação do catálogo `toc.*`, percorrida INTEIRA contra o PostgreSQL real.

Siglas, uma vez neste arquivo: **APH** — Aplicação ↔ Harness (o padrão da fronteira) ·
**ARA** — Árvore da Realidade Atual · **UDE** — Efeito Indesejável · **NC** — Nuvem de
Conflito · **ARF** — Árvore da Realidade Futura · **APR** — Árvore de Pré-Requisitos ·
**AT** — Árvore de Transição · **FSM** — máquina de estados finitos · **HTTP** —
*HyperText Transfer Protocol* · **JSON** — *JavaScript Object Notation* · **RF** —
requisito funcional.

## O buraco que este arquivo fecha, e a forma dele

A superfície executável do produto é o catálogo `toc.*` (APH-4.1). Antes deste arquivo,
das ações do catálogo **três** eram levadas do pedido até o estado gravado —
`toc.criar_nos` (`test_corrida_de_confirmacao_no_postgres.py`),
`toc.generate_conflict_cloud` (`test_propostas_no_postgres.py`) e `toc.suggest_constraint`
(`test_catalogo_m6.py`). As demais eram cobertas por testes de **unidade da camada de
aplicação**, com duplos das portas — que é exatamente a forma de cobertura que deixou
passar a regressão da onda anterior: cada peça verde sozinha, o caminho inteiro nunca
percorrido.

Aqui cada ação atravessa o caminho inteiro, uma vez:

```
POST /toc/propostas → (se `confirm`) POST /toc/propostas/{id}/decisao
                    → o efeito RELIDO por uma aplicação NOVA
```

## A função de aptidão deste arquivo

`test_toda_acao_do_catalogo_tem_cenario_de_ponta_a_ponta` compara a tabela `CENARIOS` com o
catálogo servido. **Ação nova sem cenário derruba a suíte** — é a forcing function que
impede a próxima ação de nascer com o mesmo buraco. Não há como marcá-la coberta sem
escrever o cenário: o cenário é que produz os argumentos.

Base sintética da **Instituição Horizonte** (ADR 0006 — *Architecture Decision Record*):
personas fictícias, nenhum dado real de pessoa. Marcado `integracao`: pulado com o motivo
quando o banco não responde, jamais substituído por um duplo.
"""
from __future__ import annotations

import json
from typing import Any, Callable

import pytest
from fastapi.testclient import TestClient

from toc_api.dominio.federacao.catalogo import CATALOGO_TOC
from toc_api.http.app import criar_app

from .conftest import liberar_conexoes as _liberar

pytestmark = pytest.mark.integracao

TOKEN = "tok-catalogo-facilitadora"
IDENTIDADES = {
    TOKEN: {
        "inquilino_id": "inq-horizonte",
        "usuario_id": "usr-facilitadora",
        "capabilities": ["toc:read", "toc:write"],
    }
}

UDE = "A taxa de evasão no primeiro semestre é de 22%."
OUTRO_UDE = "O caixa da instituição fecha o trimestre negativo."
CAUSA = "O acolhimento do primeiro ano não é acompanhado por ninguém."
NARRATIVA = (
    "A Instituição Horizonte precisa de receita nova já no próximo semestre. A direção "
    "quer abrir turmas em três cidades novas; o corpo docente teme pela reputação."
)


@pytest.fixture()
def aplicacoes(url_postgres, esquema_migrado):
    """Fábrica de aplicações NOVAS sobre o mesmo esquema, com descarte dos motores.

    O descarte não é higiene opcional: sem ele uma execução deste arquivo esgota o
    `max_connections` do cluster e falha por um motivo que não é o que ela mede.
    """
    abertas: list[TestClient] = []

    def abrir() -> TestClient:
        app = criar_app(
            {
                "DATABASE_URL": url_postgres,
                "TOC_DB_SCHEMA": esquema_migrado,
                "TOC_AMBIENTE": "teste",
                "TOC_IDENTIDADES_FALSAS": json.dumps(IDENTIDADES),
            }
        )
        c = TestClient(app)
        c.headers["Authorization"] = f"Bearer {TOKEN}"
        _liberar(abertas)
        abertas.append(c)
        return c

    try:
        yield abrir
    finally:
        _liberar(abertas)


def _corpo(resposta, *esperados: int) -> Any:
    assert resposta.status_code in esperados, (
        f"{resposta.request.method} {resposta.request.url.path} respondeu "
        f"{resposta.status_code}: {resposta.text[:300]}"
    )
    return resposta.json() if resposta.content else None


# =======================================================================================
# Montagens sintéticas — o estado mínimo que cada ação precisa encontrar
# =======================================================================================


def _projeto_generico(c: TestClient) -> str:
    return _corpo(c.post("/toc/projetos", json={"nome": "Horizonte — rascunho"}), 201)["id"]


def _generico_com_dois_nos(c: TestClient) -> tuple[str, str, str]:
    projeto = _projeto_generico(c)
    um = _corpo(c.post(f"/toc/projetos/{projeto}/nos", json={"titulo": UDE}), 201)["id"]
    dois = _corpo(c.post(f"/toc/projetos/{projeto}/nos", json={"titulo": CAUSA}), 201)["id"]
    return projeto, um, dois


def _ara(c: TestClient) -> str:
    return _corpo(c.post("/toc/ara/projetos", json={"nome": "Horizonte — ARA"}), 201)["id"]


def _ara_com_ude(c: TestClient) -> tuple[str, str]:
    ara = _ara(c)
    no = _corpo(c.post(f"/toc/ara/projetos/{ara}/efeitos", json={"titulo": UDE}), 201)["id"]
    _corpo(c.post(f"/toc/ara/projetos/{ara}/nos/{no}/ude", json={}), 200, 201, 204)
    return ara, no


def _ara_com_dois_efeitos(c: TestClient) -> tuple[str, str, str]:
    ara, primeiro = _ara_com_ude(c)
    segundo = _corpo(
        c.post(f"/toc/ara/projetos/{ara}/efeitos", json={"titulo": CAUSA}), 201
    )["id"]
    return ara, primeiro, segundo


def _nuvem(c: TestClient) -> str:
    return _corpo(c.post("/toc/nc/projetos", json={"nome": "Horizonte — dilema"}), 201)["id"]


def _nuvem_com_premissa(c: TestClient) -> tuple[str, str]:
    nc = _nuvem(c)
    premissa = _corpo(
        c.post(
            f"/toc/nc/projetos/{nc}/arestas/D_D_PRIME/premissas",
            json={"texto": "o orçamento é indivisível dentro do exercício"},
        ),
        200,
        201,
    )["id"]
    return nc, premissa


def _resultado_de_geracao(c: TestClient, nc: str) -> dict:
    """O adaptador de geração é local e determinístico (ADR 0007): nenhum provedor externo."""
    return _corpo(
        c.post(f"/toc/nc/projetos/{nc}/geracoes", json={"narrativa": NARRATIVA}), 200, 201
    )["resultado"]


def _arf_com_injecao(c: TestClient) -> tuple[str, str]:
    arf = _corpo(c.post("/toc/arf/projetos", json={"nome": "Horizonte — futuro"}), 201)["id"]
    injecao = _corpo(
        c.post(
            f"/toc/arf/projetos/{arf}/nos",
            json={"papel": "injecao", "titulo": "faseamento orçamentário condicionado"},
        ),
        201,
    )["id"]
    return arf, injecao


def _apr(c: TestClient) -> str:
    return _corpo(
        c.post(
            "/toc/apr/projetos",
            json={"nome": "Horizonte — implantação", "objetivo": "Reduzir a evasão"},
        ),
        201,
    )["id"]


def _apr_com_obstaculo(c: TestClient) -> tuple[str, str]:
    apr = _apr(c)
    obstaculo = _corpo(
        c.post(
            f"/toc/apr/projetos/{apr}/nos",
            json={"papel": "obstaculo", "titulo": "Há uma só pessoa treinada"},
        ),
        201,
    )["id"]
    return apr, obstaculo


def _at(c: TestClient) -> str:
    return _corpo(c.post("/toc/at/projetos", json={"nome": "Horizonte — transição"}), 201)["id"]


def _focalizacao_com_ara(c: TestClient) -> tuple[str, str, str]:
    analise = _corpo(
        c.post(
            "/toc/focalizacao/analises",
            json={"nome": "Horizonte — matrículas", "sistema": "Da inscrição à primeira aula"},
        ),
        201,
    )
    projeto = analise["projeto"]["id"]
    ara, no = _ara_com_ude(c)
    _corpo(
        c.post(
            f"/toc/focalizacao/analises/{projeto}/passos/identificar/vinculos",
            json={"ferramenta": "ara", "projeto_id": ara},
        ),
        200,
        201,
    )
    return projeto, ara, no


# =======================================================================================
# A tabela de cenários — uma linha por ação do catálogo
# =======================================================================================
#
# Cada cenário recebe o cliente de montagem e devolve `(args, verificar)`. `verificar`
# recebe uma aplicação NOVA: se ele lesse pela mesma, provaria memória e não banco.


def _c_listar_projetos(c):
    _projeto_generico(c)

    def verificar(nova, proposta):
        assert "projeto" in proposta["mensagem"], proposta
        assert len(_corpo(nova.get("/toc/projetos"), 200)) >= 1

    return {}, verificar


def _c_sugerir_udes(c):
    ara = _ara(c)

    def verificar(nova, proposta):
        # RN-03: sugestão é RASCUNHO — não grava nada.
        lida = _corpo(nova.get(f"/toc/ara/projetos/{ara}"), 200)
        assert lida["projeto"]["nos"] == [], lida["projeto"]["nos"]
        assert lida["udes"] == []

    return {"projeto_id": ara, "narrativa": f"{UDE} {CAUSA}"}, verificar


def _c_analisar_suficiencia(c):
    ara, _ = _ara_com_ude(c)

    def verificar(nova, proposta):
        assert proposta["status"] == "executed"

    return {"projeto_id": ara}, verificar


def _c_suggest_udes(c):
    ara = _ara(c)

    def verificar(nova, proposta):
        lida = _corpo(nova.get(f"/toc/ara/projetos/{ara}"), 200)
        titulos = [n["titulo"] for n in lida["projeto"]["nos"]]
        assert titulos == [UDE], titulos
        assert lida["udes"], "o nó nasceu, mas não como Efeito Indesejável"

    return {"projeto_id": ara, "udes": [{"texto": UDE}]}, verificar


def _c_suggest_causes(c):
    ara, no = _ara_com_ude(c)

    def verificar(nova, proposta):
        lida = _corpo(nova.get(f"/toc/ara/projetos/{ara}"), 200)
        titulos = [n["titulo"] for n in lida["projeto"]["nos"]]
        assert CAUSA in titulos, titulos
        assert len(lida["elos"]) == 1, "a causa nasceu solta — o elo é o requisito"

    return {"projeto_id": ara, "no_id": no, "causas": [{"texto": CAUSA}]}, verificar


def _c_suggest_relations(c):
    ara, primeiro, segundo = _ara_com_dois_efeitos(c)

    def verificar(nova, proposta):
        lida = _corpo(nova.get(f"/toc/ara/projetos/{ara}"), 200)
        assert len(lida["elos"]) == 1, lida["elos"]

    args = {"projeto_id": ara, "relacoes": [{"origem_id": segundo, "destino_id": primeiro}]}
    return args, verificar


def _c_suggest_reformulation(c):
    ara, no = _ara_com_ude(c)
    novo = "A taxa de evasão no primeiro semestre subiu para 24% em 2026."

    def verificar(nova, proposta):
        lida = _corpo(nova.get(f"/toc/ara/projetos/{ara}"), 200)
        titulos = [n["titulo"] for n in lida["projeto"]["nos"]]
        assert titulos == [novo], titulos

    return {"projeto_id": ara, "no_id": no, "texto": novo}, verificar


def _c_criar_nos(c):
    projeto = _projeto_generico(c)

    def verificar(nova, proposta):
        lida = _corpo(nova.get(f"/toc/projetos/{projeto}"), 200)
        assert sorted(n["titulo"] for n in lida["nos"]) == sorted([UDE, CAUSA]), lida["nos"]

    args = {
        "projeto_id": projeto,
        "nos": [{"titulo": UDE, "tipo": "ude"}, {"titulo": CAUSA, "tipo": "causa"}],
    }
    return args, verificar


def _c_criar_arestas(c):
    projeto, um, dois = _generico_com_dois_nos(c)

    def verificar(nova, proposta):
        lida = _corpo(nova.get(f"/toc/projetos/{projeto}"), 200)
        assert len(lida["arestas"]) == 1, lida["arestas"]

    return {"projeto_id": projeto, "arestas": [{"origem_id": dois, "destino_id": um}]}, verificar


def _c_atualizar_no(c):
    projeto, um, _ = _generico_com_dois_nos(c)

    def verificar(nova, proposta):
        lida = _corpo(nova.get(f"/toc/projetos/{projeto}"), 200)
        assert "Enunciado reescrito" in [n["titulo"] for n in lida["nos"]], lida["nos"]

    return {"projeto_id": projeto, "no_id": um, "titulo": "Enunciado reescrito"}, verificar


def _c_excluir_nos(c):
    projeto, um, dois = _generico_com_dois_nos(c)

    def verificar(nova, proposta):
        lida = _corpo(nova.get(f"/toc/projetos/{projeto}"), 200)
        assert [n["id"] for n in lida["nos"]] == [dois], lida["nos"]

    return {"projeto_id": projeto, "no_ids": [um]}, verificar


def _c_exportar_projeto(c):
    projeto, _, _ = _generico_com_dois_nos(c)

    def verificar(nova, proposta):
        assert "nó" in proposta["mensagem"], proposta["mensagem"]

    return {"projeto_id": projeto}, verificar


def _c_generate_conflict_cloud(c):
    nc = _nuvem(c)
    resultado = _resultado_de_geracao(c, nc)

    def verificar(nova, proposta):
        lida = _corpo(nova.get(f"/toc/nc/projetos/{nc}"), 200)
        assert lida["racional"], "a geração aceita não escreveu o racional"
        assert any(a.get("premissas") for a in lida["arestas"]), lida["arestas"]

    return {"projeto_id": nc, "narrativa": NARRATIVA, "resultado": resultado}, verificar


def _c_suggest_assumptions(c):
    nc = _nuvem(c)
    texto = "o orçamento é indivisível dentro do exercício"

    def verificar(nova, proposta):
        lida = _corpo(nova.get(f"/toc/nc/projetos/{nc}"), 200)
        textos = [p["texto"] for a in lida["arestas"] for p in a.get("premissas", [])]
        assert textos == [texto], textos

    return {"projeto_id": nc, "aresta": "D_D_PRIME", "texto": texto}, verificar


def _c_suggest_injections(c):
    nc, premissa = _nuvem_com_premissa(c)
    texto = "faseamento orçamentário condicionado a marco de receita"

    def verificar(nova, proposta):
        lida = _corpo(nova.get(f"/toc/nc/projetos/{nc}"), 200)
        injecoes = [
            i for a in lida["arestas"] for p in a.get("premissas", []) for i in p.get("injecoes", [])
        ]
        assert [i["texto"] for i in injecoes] == [texto], injecoes

    args = {"projeto_id": nc, "premissa_id": premissa, "texto": texto, "separacao": "tempo"}
    return args, verificar


def _c_suggest_future_effects(c):
    arf, injecao = _arf_com_injecao(c)
    texto = "as duas frentes recebem verba no trimestre"

    def verificar(nova, proposta):
        lida = _corpo(nova.get(f"/toc/arf/projetos/{arf}"), 200)
        assert texto in [n["titulo"] for n in lida["nos"]], lida["nos"]
        # INT-05: o efeito nunca fica solto — ele nasce LIGADO à injeção.
        assert len(lida["elos"]) == 1, lida["elos"]

    return {"projeto_id": arf, "injecao_id": injecao, "texto": texto}, verificar


def _c_suggest_obstacles(c):
    apr = _apr(c)
    texto = "Não há conferência automatizada de documentos"

    def verificar(nova, proposta):
        lida = _corpo(nova.get(f"/toc/apr/projetos/{apr}"), 200)
        obstaculos = [n["titulo"] for n in lida["nos"] if n["papel"] == "obstaculo"]
        assert obstaculos == [texto], lida["nos"]

    return {"projeto_id": apr, "texto": texto}, verificar


def _c_suggest_intermediate_objectives(c):
    apr, obstaculo = _apr_com_obstaculo(c)
    texto = "Existem três pessoas treinadas e escaladas"

    def verificar(nova, proposta):
        lida = _corpo(nova.get(f"/toc/apr/projetos/{apr}"), 200)
        assert len(lida["pares"]) == 1, lida["pares"]
        assert lida["pares"][0]["obstaculo_id"] == obstaculo
        # RN-07: o julgamento do teste de validade continua HUMANO — não vem preenchido.
        assert lida["pares"][0]["julgamentos"] == [], lida["pares"][0]

    return {"projeto_id": apr, "obstaculo_id": obstaculo, "texto": texto}, verificar


def _c_suggest_transition_steps(c):
    at = _at(c)
    acao = "Formar duas pessoas no acompanhamento do marco"

    def verificar(nova, proposta):
        lida = _corpo(nova.get(f"/toc/at/projetos/{at}"), 200)
        assert len(lida["passos"]) == 1, lida["passos"]
        ficha = lida["passos"][0]
        assert (ficha["acao"], ficha["necessidade"], ficha["resultado_esperado"]) == (
            acao,
            "só há uma pessoa treinada",
            "três pessoas escaladas",
        ), ficha

    args = {
        "projeto_id": at,
        "acao": acao,
        "necessidade": "só há uma pessoa treinada",
        "resultado_esperado": "três pessoas escaladas",
    }
    return args, verificar


def _c_suggest_constraint(c):
    projeto, ara, no = _focalizacao_com_ara(c)
    descricao = "Capacidade de conferência da secretaria acadêmica"

    def verificar(nova, proposta):
        jornada = _corpo(nova.get(f"/toc/focalizacao/analises/{projeto}/jornada"), 200)
        assert jornada["restricao"]["descricao"] == descricao, jornada["restricao"]
        # INT-02: a referência de origem é a evidência que sustenta a conclusão.
        assert jornada["restricao"]["origem"] == {
            "ferramenta": "ara",
            "projeto_id": ara,
            "no_id": no,
        }, jornada["restricao"]["origem"]

    args = {
        "projeto_id": projeto,
        "ara_projeto_id": ara,
        "no_id": no,
        "descricao": descricao,
        "tipo": "fisica",
        "justificativa": "a fila de matrículas só cresce nesta etapa",
    }
    return args, verificar


#: `action_id → cenário`. Uma linha por ação do catálogo — e o teste de completude abaixo
#: recusa qualquer ação que não tenha a sua.
CENARIOS: dict[str, Callable[[TestClient], tuple[dict, Callable]]] = {
    "toc.listar_projetos": _c_listar_projetos,
    "toc.sugerir_udes": _c_sugerir_udes,
    "toc.analisar_suficiencia": _c_analisar_suficiencia,
    "toc.suggest_udes": _c_suggest_udes,
    "toc.suggest_causes": _c_suggest_causes,
    "toc.suggest_relations": _c_suggest_relations,
    "toc.suggest_reformulation": _c_suggest_reformulation,
    "toc.criar_nos": _c_criar_nos,
    "toc.criar_arestas": _c_criar_arestas,
    "toc.atualizar_no": _c_atualizar_no,
    "toc.excluir_nos": _c_excluir_nos,
    "toc.exportar_projeto": _c_exportar_projeto,
    "toc.generate_conflict_cloud": _c_generate_conflict_cloud,
    "toc.suggest_assumptions": _c_suggest_assumptions,
    "toc.suggest_injections": _c_suggest_injections,
    "toc.suggest_future_effects": _c_suggest_future_effects,
    "toc.suggest_obstacles": _c_suggest_obstacles,
    "toc.suggest_intermediate_objectives": _c_suggest_intermediate_objectives,
    "toc.suggest_transition_steps": _c_suggest_transition_steps,
    "toc.suggest_constraint": _c_suggest_constraint,
}

ACOES = tuple(a.action_id for a in CATALOGO_TOC.acoes)


# =======================================================================================
# A função de aptidão: o catálogo inteiro tem cenário
# =======================================================================================


def test_toda_acao_do_catalogo_tem_cenario_de_ponta_a_ponta():
    """Ação nova sem caminho percorrido inteiro DERRUBA a suíte — de propósito.

    É o portão que impede a próxima ação de nascer com o buraco que este arquivo fechou:
    coberta por teste de unidade da aplicação, com duplo da porta, e nunca exercitada do
    pedido ao estado gravado.
    """
    sem_cenario = sorted(set(ACOES) - set(CENARIOS))
    sobrando = sorted(set(CENARIOS) - set(ACOES))

    print(
        f"\ncatálogo servido: {len(ACOES)} ação(ões) · cenários ponta a ponta: "
        f"{len(CENARIOS)} · sem cenário: {sem_cenario} · cenário órfão: {sobrando}"
    )
    assert not sem_cenario, (
        f"ação(ões) do catálogo sem cenário de ponta a ponta: {sem_cenario}. "
        f"Escreva o cenário em CENARIOS — teste de unidade com duplo não conta, porque foi "
        f"exatamente essa cobertura que deixou passar a regressão da raiz do agregado."
    )
    assert not sobrando, f"cenário para ação que saiu do catálogo: {sobrando}"


# =======================================================================================
# Uma travessia por ação
# =======================================================================================


@pytest.mark.parametrize("action_id", ACOES)
def test_a_acao_do_catalogo_atravessa_do_pedido_ao_estado_gravado(aplicacoes, action_id: str):
    """Propor, decidir e RELER o efeito por uma aplicação nova — o caminho inteiro."""
    acao = CATALOGO_TOC.acao(action_id)
    montagem = aplicacoes()
    args, verificar = CENARIOS[action_id](montagem)

    proposta = montagem.post("/toc/propostas", json={"action_id": action_id, "args": args})
    assert proposta.status_code == 201, proposta.text
    corpo = proposta.json()

    if acao.requires_confirmation:
        assert corpo["estado"] == "awaiting_approval", corpo
        decisora = aplicacoes()
        decidida = decisora.post(
            f"/toc/propostas/{corpo['proposal_id']}/decisao", json={"aprovado": True}
        )
        assert decidida.status_code == 200, decidida.text
        corpo = decidida.json()
    else:
        # APH-5.2: risco `read` executa direto, e o desfecho já volta na resposta.
        assert corpo["estado"] == "executed", corpo

    print(
        f"\n{action_id} ({acao.risk}, ferramenta={acao.ferramenta}): "
        f"{corpo['status']} · alvos={corpo['quantidade_de_alvos']} · "
        f"desfechos={[(o['target'][:28], o['status']) for o in corpo['outcomes']]}"
    )
    assert corpo["status"] == "executed", corpo
    assert all(o["status"] == "executed" for o in corpo["outcomes"]), corpo["outcomes"]

    verificar(aplicacoes(), corpo)


@pytest.mark.parametrize(
    "action_id", [a.action_id for a in CATALOGO_TOC.acoes if a.requires_confirmation]
)
def test_recusar_a_acao_mutadora_deixa_o_estado_byte_a_byte_intacto(aplicacoes, action_id: str):
    """A outra metade do gate, para TODA mutadora: recusar não escreve nada.

    O retrato é comparado **serializado e inteiro** — "parece igual" não é evidência. O que
    se compara é o projeto alvo do cenário, lido antes e depois por aplicações novas.
    """
    montagem = aplicacoes()
    args, _ = CENARIOS[action_id](montagem)
    projeto_id = args["projeto_id"]

    def retrato() -> str:
        nova = aplicacoes()
        return json.dumps(_corpo(nova.get(f"/toc/projetos/{projeto_id}"), 200), sort_keys=True)

    antes = retrato()
    proposta = _corpo(
        montagem.post("/toc/propostas", json={"action_id": action_id, "args": args}), 201
    )
    decidida = _corpo(
        aplicacoes().post(
            f"/toc/propostas/{proposta['proposal_id']}/decisao", json={"aprovado": False}
        ),
        200,
    )
    depois = retrato()

    print(f"\n{action_id}: {decidida['status']} · retrato de {len(antes)} byte(s) preservado")
    assert decidida["status"] == "denied", decidida
    assert depois == antes, f"{action_id}: a recusa alterou o estado"
