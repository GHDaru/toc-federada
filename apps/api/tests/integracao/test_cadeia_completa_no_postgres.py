"""O encadeamento INTEIRO pelo HTTP e contra o PostgreSQL real — ARA → NC → ARF → APR → AT.

Siglas, uma vez neste arquivo: **ARA** — Árvore da Realidade Atual · **NC** — Nuvem de
Conflito · **ARF** — Árvore da Realidade Futura · **APR** — Árvore de Pré-Requisitos ·
**AT** — Árvore de Transição · **UDE** — Efeito Indesejável · **OI** — Objetivo
Intermediário · **HTTP** — *HyperText Transfer Protocol* · **JSON** — *JavaScript Object
Notation* · **RF/RN** — requisito funcional / regra de negócio · **DDD** — *Domain-Driven
Design* (Design Orientado a Domínio).

## Por que este arquivo existe

O encadeamento é a funcionalidade diferencial do produto: ele atravessa **cinco agregados
distintos**, cada um com as suas invariantes, e cada um ganhou travas em ondas diferentes
(a raiz do agregado, a trava otimista por versão lida, a trava da proposta). Antes deste
arquivo, a cadeia inteira era percorrida por três testes que **nunca se encontravam**:

| Teste que existia | O que ele prova | O que ele NÃO prova |
|---|---|---|
| `apps/api/tests/dominio/test_encadeamento.py` | as funções puras encadeiam | nada de borda, nada de banco |
| `apps/api/tests/contrato/test_http_m4.py::test_a_cadeia_inteira_atravessa_a_borda_e_a_vista_a_percorre` | as rotas encadeiam **em memória** | que a cadeia sobrevive à gravação |
| `apps/api/tests/integracao/test_m4_no_postgres.py` | os agregados vão e voltam do banco | que a **travessia** funciona ponta a ponta |

Somar os três **não** dá o caminho inteiro: é exatamente a soma de testes de unidade de
cada pedaço que deixou passar a regressão da onda anterior (a guarda da raiz do agregado
matou as ações do catálogo federado, e cada peça continuou verde sozinha). Aqui a travessia
é uma só, do Efeito Indesejável ao passo de transição, com uma **aplicação nova a cada
etapa** — o equivalente a recarregar a tela — de modo que nenhum elo pode viver em memória.

Base sintética da **Instituição Horizonte** (ADR 0006 — *Architecture Decision Record*):
personas fictícias, nenhum dado real de pessoa.

Marcado `integracao`: pulado com o motivo quando o banco não responde, jamais substituído
por um duplo — um teste de integração que cai em SQLite não integrou nada.
"""
from __future__ import annotations

import json
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from toc_api.dominio.exportacao import esqueleto
from toc_api.http.app import criar_app

from .conftest import liberar_conexoes as _liberar

pytestmark = pytest.mark.integracao

IDENTIDADES = {
    "tok-cadeia-facilitadora": {
        "inquilino_id": "inq-horizonte",
        "usuario_id": "usr-facilitadora",
        "capabilities": ["toc:read", "toc:write"],
    },
    "tok-cadeia-outra-instituicao": {
        "inquilino_id": "inq-aurora",
        "usuario_id": "usr-aurora",
        "capabilities": ["toc:read", "toc:write"],
    },
}

# A narrativa sintética da Instituição Horizonte, a mesma das outras suítes.
UDE_UM = "A taxa de evasão no primeiro semestre é de 22%."
UDE_DOIS = "O caixa da instituição fecha o trimestre negativo."
CAUSA = "O acolhimento do primeiro ano não é acompanhado por ninguém."
PREMISSA = "o orçamento é indivisível dentro do exercício"
INJECAO = "faseamento orçamentário condicionado a marco de receita"
EFEITO_FUTURO = "as duas frentes recebem verba no trimestre"
OBSTACULO = "Há apenas uma pessoa treinada no acompanhamento do marco"
OI = "Existem três pessoas treinadas e escaladas"
ACAO_DO_PASSO = "Formar duas pessoas no acompanhamento do marco"
NECESSIDADE_DO_PASSO = "só há uma pessoa treinada e ela é ponto único de falha"
RESULTADO_DO_PASSO = "três pessoas escaladas na escala de acompanhamento"

FERRAMENTAS_DA_CADEIA = ["ara", "nc", "arf", "apr", "at"]


@pytest.fixture()
def aplicacoes(url_postgres, esquema_migrado):
    """Fábrica de aplicações NOVAS sobre o MESMO esquema migrado — e o descarte delas.

    Cada chamada devolve uma aplicação recém-composta: é o equivalente a recarregar a
    tela, e é o que separa "o objeto ainda está na memória do processo" de "o elo está no
    banco". Cada uma abre o seu motor de banco, então a fixture guarda todas e **descarta
    os motores no fim** — sem isso, uma travessia de cinco ferramentas esgota
    `max_connections` do cluster e o teste falha por um motivo que não é o que ele mede
    (medido: `FATAL: sorry, too many clients already` na primeira versão deste arquivo).
    """
    abertas: list[TestClient] = []

    def abrir(token: str = "tok-cadeia-facilitadora") -> TestClient:
        app = criar_app(
            {
                "DATABASE_URL": url_postgres,
                "TOC_DB_SCHEMA": esquema_migrado,
                "TOC_AMBIENTE": "teste",
                "TOC_IDENTIDADES_FALSAS": json.dumps(IDENTIDADES),
            }
        )
        c = TestClient(app)
        c.headers["Authorization"] = f"Bearer {token}"
        _liberar(abertas)
        abertas.append(c)
        return c

    try:
        yield abrir
    finally:
        _liberar(abertas)


def _ok(resposta, *esperados: int):
    assert resposta.status_code in esperados, (
        f"{resposta.request.method} {resposta.request.url.path} respondeu "
        f"{resposta.status_code}: {resposta.text[:400]}"
    )
    # `204 No Content` não tem corpo: pedir `.json()` aqui rebentaria com um erro de
    # decodificação que não tem nada a ver com o que o teste mede.
    return resposta.json() if resposta.content else None


def montar_a_cadeia_inteira(abrir) -> dict[str, str]:
    """Percorre as cinco ferramentas trocando de aplicação a cada elo.

    Devolve os cinco identificadores mais os identificadores intermediários que os testes
    conferem. Cada bloco abre um cliente próprio de propósito: se um elo dependesse de
    estado que ficou na aplicação anterior, ele quebraria aqui e não seis meses depois.
    """
    # -- ARA: dois Efeitos Indesejáveis validados e uma causa ligada a um deles --------
    c = abrir()
    ara = _ok(c.post("/toc/ara/projetos", json={"nome": "Horizonte — realidade atual"}), 201)
    udes = []
    for enunciado in (UDE_UM, UDE_DOIS):
        no = _ok(c.post(f"/toc/ara/projetos/{ara['id']}/efeitos", json={"titulo": enunciado}), 201)
        _ok(c.post(f"/toc/ara/projetos/{ara['id']}/nos/{no['id']}/ude", json={}), 200, 201, 204)
        _ok(
            c.post(
                f"/toc/ara/projetos/{ara['id']}/nos/{no['id']}/pareceres",
                json={
                    "favoravel": True,
                    "justificativa": "a queixa é contínua e está na esfera da coordenação",
                },
            ),
            200,
            201,
            204,
        )
        _ok(
            c.put(
                f"/toc/ara/projetos/{ara['id']}/nos/{no['id']}/status",
                json={"status": "validado"},
            ),
            200,
        )
        udes.append(no["id"])

    c = abrir()
    causa = _ok(c.post(f"/toc/ara/projetos/{ara['id']}/efeitos", json={"titulo": CAUSA}), 201)
    aresta = _ok(
        c.post(
            f"/toc/ara/projetos/{ara['id']}/arestas",
            json={"origem_id": causa["id"], "destino_id": udes[0]},
        ),
        201,
    )
    _ok(
        c.put(
            f"/toc/ara/projetos/{ara['id']}/arestas/{aresta['id']}/exame",
            json={"estado": "com_reserva", "reserva": "falta medir a coorte de 2025"},
        ),
        200,
    )

    # -- elo 1: ARA → NC (promoção dos Efeitos Indesejáveis validados) -----------------
    c = abrir()
    nuvem = _ok(
        c.post(
            "/toc/cadeia/promocoes",
            json={
                "ara_projeto_id": ara["id"],
                "no_ids": udes,
                "nome": "Horizonte — dilema da expansão",
            },
        ),
        201,
    )

    # -- NC: premissa, injeção e a escolha que habilita a semeadura --------------------
    c = abrir()
    premissa = _ok(
        c.post(
            f"/toc/nc/projetos/{nuvem['id']}/arestas/D_D_PRIME/premissas",
            json={"texto": PREMISSA},
        ),
        200,
        201,
    )
    injecao = _ok(
        c.post(
            f"/toc/nc/projetos/{nuvem['id']}/premissas/{premissa['id']}/injecoes",
            json={"texto": INJECAO},
        ),
        200,
        201,
    )
    _ok(
        c.put(
            f"/toc/nc/projetos/{nuvem['id']}/injecoes/{injecao['id']}/status",
            json={"status": "escolhida"},
        ),
        200,
    )

    # -- elo 2: NC → ARF (a injeção escolhida vira o nó semente) -----------------------
    c = abrir()
    arf = _ok(
        c.post(
            "/toc/cadeia/semeaduras",
            json={
                "nc_projeto_id": nuvem["id"],
                "injecao_id": injecao["id"],
                "nome": "Horizonte — futuro da expansão",
            },
        ),
        201,
    )

    # -- ARF: o efeito futuro e o espelho que o liga de volta ao Efeito Indesejável ----
    c = abrir()
    efeito = _ok(
        c.post(
            f"/toc/arf/projetos/{arf['id']}/nos",
            json={"papel": "efeito_futuro", "titulo": EFEITO_FUTURO},
        ),
        201,
    )
    _ok(
        c.post(
            f"/toc/arf/projetos/{arf['id']}/espelhos",
            json={"no_id": efeito["id"], "ude_id": udes[0]},
        ),
        200,
        201,
    )

    # -- elo 3: ARF → APR --------------------------------------------------------------
    c = abrir()
    apr = _ok(
        c.post(
            "/toc/cadeia/derivacoes/apr",
            json={
                "arf_projeto_id": arf["id"],
                "no_id": efeito["id"],
                "nome": "Horizonte — implantação",
            },
        ),
        201,
    )

    # -- APR: o obstáculo e o objetivo intermediário que o supera ----------------------
    c = abrir()
    obstaculo = _ok(
        c.post(
            f"/toc/apr/projetos/{apr['id']}/nos",
            json={"papel": "obstaculo", "titulo": OBSTACULO},
        ),
        201,
    )
    oi = _ok(
        c.post(
            f"/toc/apr/projetos/{apr['id']}/nos",
            json={"papel": "objetivo_intermediario", "titulo": OI},
        ),
        201,
    )
    _ok(
        c.post(
            f"/toc/apr/projetos/{apr['id']}/pares",
            json={"obstaculo_id": obstaculo["id"], "objetivo_intermediario_id": oi["id"]},
        ),
        200,
        201,
    )

    # -- elo 4: APR → AT ---------------------------------------------------------------
    c = abrir()
    at = _ok(
        c.post(
            "/toc/cadeia/derivacoes/at",
            json={
                "apr_projeto_id": apr["id"],
                "no_id": oi["id"],
                "nome": "Horizonte — transição",
            },
        ),
        201,
    )

    # -- AT: o passo com a tripla inteira ----------------------------------------------
    c = abrir()
    passo = _ok(
        c.post(
            f"/toc/at/projetos/{at['id']}/passos",
            json={
                "acao": ACAO_DO_PASSO,
                "necessidade": NECESSIDADE_DO_PASSO,
                "resultado_esperado": RESULTADO_DO_PASSO,
            },
        ),
        201,
    )

    return {
        "ara": ara["id"],
        "nc": nuvem["id"],
        "arf": arf["id"],
        "apr": apr["id"],
        "at": at["id"],
        "ude": udes[0],
        "ude_dois": udes[1],
        "injecao": injecao["id"],
        "premissa": premissa["id"],
        "efeito_futuro": efeito["id"],
        "obstaculo": obstaculo["id"],
        "oi": oi["id"],
        "passo": passo["id"],
    }


# =======================================================================================
# A travessia inteira, do Efeito Indesejável ao passo de transição
# =======================================================================================


def test_a_cadeia_das_cinco_ferramentas_atravessa_o_banco_de_ponta_a_ponta(aplicacoes):
    """RF-41/RF-42: cinco agregados, quatro elos, uma travessia — e nada em memória."""
    ids = montar_a_cadeia_inteira(aplicacoes)

    # A vista da cadeia, lida por uma aplicação que não participou de nenhuma escrita.
    c = aplicacoes()
    cadeia = _ok(c.get(f"/toc/cadeia/{ids['ara']}"), 200)

    print(
        f"\ncadeia no PostgreSQL: {' → '.join(cadeia['ferramentas'])} · "
        f"elos={len(cadeia['elos'])} · estados={[e['estado'] for e in cadeia['elos']]} · "
        f"resumo={cadeia['resumo']}"
    )
    assert cadeia["ferramentas"] == FERRAMENTAS_DA_CADEIA, cadeia["ferramentas"]
    assert len(cadeia["elos"]) == 4, cadeia["elos"]
    assert all(elo["estado"] == "ativa" for elo in cadeia["elos"]), cadeia["elos"]


@pytest.mark.parametrize("ponto", FERRAMENTAS_DA_CADEIA)
def test_a_cadeia_e_a_mesma_partindo_de_qualquer_uma_das_cinco(aplicacoes, ponto: str):
    """RF-42: "a travessia inteira a partir de QUALQUER elemento encadeado".

    A promessa é de simetria. Um teste que só abrisse pela Árvore da Realidade Atual
    responderia verde sobre um grafo dirigido que só sabe descer.
    """
    ids = montar_a_cadeia_inteira(aplicacoes)

    c = aplicacoes()
    cadeia = _ok(c.get(f"/toc/cadeia/{ids[ponto]}"), 200)

    print(
        f"partindo de {ponto!r}: {' → '.join(cadeia['ferramentas'])} · "
        f"elos={len(cadeia['elos'])}"
    )
    assert cadeia["ferramentas"] == FERRAMENTAS_DA_CADEIA, (ponto, cadeia["ferramentas"])
    assert len(cadeia["elos"]) == 4, (ponto, cadeia["elos"])


def test_o_conteudo_de_cada_elo_sobrevive_a_travessia_inteira(aplicacoes):
    """Não basta a cadeia existir: o que cada elo CARREGOU tem de estar lá.

    Cada asserção aqui é um elo que a costura poderia ter perdido em silêncio — o texto da
    injeção que virou nó semente, o espelho que liga o efeito futuro de volta ao Efeito
    Indesejável, o par obstáculo↔objetivo, a tripla do passo.
    """
    ids = montar_a_cadeia_inteira(aplicacoes)
    c = aplicacoes()

    nuvem = _ok(c.get(f"/toc/nc/projetos/{ids['nc']}"), 200)
    assert nuvem["origem"]["ferramenta"] == "ara"
    assert nuvem["origem"]["projeto_id"] == ids["ara"]
    assert set(nuvem["origem"]["nos"]) == {ids["ude"], ids["ude_dois"]}

    arf = _ok(c.get(f"/toc/arf/projetos/{ids['arf']}"), 200)
    semente = [n for n in arf["nos"] if n["papel"] == "injecao"]
    assert [n["titulo"] for n in semente] == [INJECAO], arf["nos"]
    assert any(n["titulo"] == EFEITO_FUTURO for n in arf["nos"]), arf["nos"]

    apr = _ok(c.get(f"/toc/apr/projetos/{ids['apr']}"), 200)
    assert apr["objetivo"], "a APR nasceu sem objetivo — a derivação não propôs nada"
    pares = apr["pares"]
    assert len(pares) == 1, pares
    assert pares[0]["obstaculo_id"] == ids["obstaculo"]
    assert pares[0]["objetivo_intermediario_id"] == ids["oi"]

    at = _ok(c.get(f"/toc/at/projetos/{ids['at']}"), 200)
    assert at["alvo"]["projeto_id"] == ids["apr"], at["alvo"]
    assert at["alvo"]["elementos"] == [ids["oi"]], at["alvo"]
    ficha = at["passos"][0]
    print(
        f"\npasso final da cadeia: ação={ficha['acao']!r} · "
        f"necessidade={ficha['necessidade']!r} · esperado={ficha['resultado_esperado']!r}"
    )
    assert (ficha["acao"], ficha["necessidade"], ficha["resultado_esperado"]) == (
        ACAO_DO_PASSO,
        NECESSIDADE_DO_PASSO,
        RESULTADO_DO_PASSO,
    )


def test_as_referencias_de_cada_projeto_da_cadeia_apontam_para_os_vizinhos(aplicacoes):
    """RF-34: a ficha do elemento mostra de onde ele veio e para onde ele foi.

    O meio da cadeia é o caso que discrimina: a Árvore da Realidade Futura tem de ter uma
    referência de origem (a Nuvem) **e** uma de destino (a Árvore de Pré-Requisitos).
    """
    ids = montar_a_cadeia_inteira(aplicacoes)
    c = aplicacoes()

    contagens = {}
    for ferramenta in FERRAMENTAS_DA_CADEIA:
        referencias = _ok(c.get(f"/toc/cadeia/{ids[ferramenta]}/referencias"), 200)
        contagens[ferramenta] = len(referencias)
    print(f"\nreferências por ferramenta: {contagens}")

    # As pontas participam de um elo; os três do meio, de dois.
    assert contagens == {"ara": 1, "nc": 2, "arf": 2, "apr": 2, "at": 1}, contagens


def test_a_cadeia_de_outro_inquilino_e_indistinguivel_de_uma_que_nunca_existiu(aplicacoes):
    """RNF-03 pela vista da cadeia — e o resultado é MEDIDO, não deduzido do resto da suíte.

    As rotas de ferramenta (`/toc/ara/projetos/{id}`) e a exportação respondem **404** através
    da fronteira do inquilino. A vista da cadeia responde **200 com a cadeia vazia** — e é
    outra forma de fechar a mesma porta, não um furo:

    | pedido de `inq-aurora` | resposta |
    |---|---|
    | cadeia de um projeto de `inq-horizonte` | `200` · `{"elos": [], "ferramentas": [], …}` |
    | cadeia de um identificador que nunca existiu | `200` · o MESMO corpo |
    | projeto próprio, ainda sem nenhum elo | `200` · o MESMO corpo |

    Como os três corpos são **iguais byte a byte**, a resposta não discrimina entre "não
    existe", "existe e é de outro" e "é seu e não tem elo" — que é a indistinguibilidade
    que o §B.7.3 do Anexo B pede, e é mais forte do que um 404 (que só cobre os dois
    primeiros casos). O que este teste impede é a mudança que quebrasse isso em silêncio:
    bastaria a travessia passar a listar as referências sem filtrar por inquilino, e o
    corpo do primeiro caso deixaria de ser vazio.
    """
    ids = montar_a_cadeia_inteira(aplicacoes)
    outra = aplicacoes("tok-cadeia-outra-instituicao")

    respostas = {f: outra.get(f"/toc/cadeia/{ids[f]}") for f in FERRAMENTAS_DA_CADEIA}
    nunca_existiu = outra.get(f"/toc/cadeia/{uuid4()}")
    proprio_sem_elo = outra.post("/toc/ara/projetos", json={"nome": "Aurora — realidade atual"})
    sem_elo = outra.get(f"/toc/cadeia/{proprio_sem_elo.json()['id']}")

    print(
        f"\ncadeia alheia: {[r.status_code for r in respostas.values()]} · "
        f"inexistente: {nunca_existiu.status_code} · própria sem elo: {sem_elo.status_code}"
    )
    print(f"corpo devolvido nos três casos: {nunca_existiu.json()}")

    assert nunca_existiu.status_code == 200
    assert nunca_existiu.json()["elos"] == []
    for ferramenta, resposta in respostas.items():
        assert resposta.status_code == 200, (ferramenta, resposta.text)
        assert resposta.json() == nunca_existiu.json(), (
            f"a cadeia de {ferramenta!r} de outro inquilino difere da de um identificador "
            f"inexistente — a resposta passou a confirmar a existência do projeto alheio"
        )
    assert sem_elo.json() == nunca_existiu.json()

    # E a fronteira do inquilino continua fechada nas rotas que devolvem CONTEÚDO.
    for ferramenta, rota in (
        ("ara", f"/toc/ara/projetos/{ids['ara']}"),
        ("nc", f"/toc/nc/projetos/{ids['nc']}"),
        ("arf", f"/toc/arf/projetos/{ids['arf']}"),
        ("apr", f"/toc/apr/projetos/{ids['apr']}"),
        ("at", f"/toc/at/projetos/{ids['at']}"),
        ("exportação", f"/toc/portabilidade/projetos/{ids['ara']}"),
    ):
        assert outra.get(rota).status_code == 404, (ferramenta, rota)


# =======================================================================================
# A cadeia inteira sai num arquivo e volta — E1.4 sobre as CINCO ferramentas
# =======================================================================================


def test_exportar_a_cadeia_inteira_e_reimporta_la_reproduz_as_cinco_ferramentas(aplicacoes):
    """RF-31/RF-32: o arquivo leva a cadeia toda, e a volta reconstrói a travessia.

    A suíte já provava a ida e volta de uma cadeia de DUAS ferramentas
    (`test_portabilidade_no_postgres.py`, que promove e para na Nuvem). Cinco é outro
    problema: é onde uma seção de ferramenta pode sumir do documento sem que nada acuse.
    """
    ids = montar_a_cadeia_inteira(aplicacoes)

    c = aplicacoes()
    documento = _ok(c.get(f"/toc/portabilidade/projetos/{ids['at']}"), 200)
    ferramentas_no_arquivo = sorted({p["ferramenta"] for p in documento["projetos"]})
    print(f"\nferramentas no arquivo exportado: {ferramentas_no_arquivo}")
    assert ferramentas_no_arquivo == sorted(FERRAMENTAS_DA_CADEIA), ferramentas_no_arquivo

    antes = len(_ok(c.get("/toc/projetos"), 200))
    relato = _ok(c.post("/toc/portabilidade/importacoes", json={"documento": documento}), 201)
    criados = relato["projetos_criados"]
    print(f"projetos antes={antes} · criados na importação={len(criados)}")
    assert len(criados) == 5, criados

    # A cadeia importada é percorrível inteira, e não uma pilha de projetos soltos.
    depois = aplicacoes()
    nova_ara = next(
        pid
        for pid in criados
        if depois.get(f"/toc/ara/projetos/{pid}").status_code == 200
    )
    cadeia = _ok(depois.get(f"/toc/cadeia/{nova_ara}"), 200)
    print(f"cadeia reimportada: {' → '.join(cadeia['ferramentas'])} · elos={len(cadeia['elos'])}")
    assert cadeia["ferramentas"] == FERRAMENTAS_DA_CADEIA, cadeia["ferramentas"]
    assert len(cadeia["elos"]) == 4, cadeia["elos"]

    # E o arquivo da cópia é estruturalmente o mesmo, a menos de identificadores (RF-32).
    documento_da_copia = _ok(depois.get(f"/toc/portabilidade/projetos/{nova_ara}"), 200)
    assert esqueleto(documento_da_copia) == esqueleto(documento), (
        "o arquivo da cópia divergiu do original em algo que não é identificador nem "
        "carimbo de tempo — a ida e volta perdeu conteúdo"
    )
