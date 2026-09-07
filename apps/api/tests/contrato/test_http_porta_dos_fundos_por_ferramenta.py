"""A porta dos fundos do agregado, varrida sobre TODAS as ferramentas — e as duas portas.

Siglas, uma vez neste arquivo: **M1** — Núcleo de Diagramas Lógicos · **ARA** — Árvore da
Realidade Atual · **NC** — Nuvem de Conflito · **ARF** — Árvore da Realidade Futura ·
**APR** — Árvore de Pré-Requisitos · **AT** — Árvore de Transição · **S&T** — Estratégia &
Táticas · **DDD** — *Domain-Driven Design* (Design Orientado a Domínio) · **APH** —
Aplicação ↔ Harness · **HTTP** — *HyperText Transfer Protocol* · **UDE** — Efeito
Indesejável.

## Por que este arquivo, se já existem dois sobre porta dos fundos

`apps/api/tests/contrato/test_http_porta_dos_fundos.py` cobre a rota genérica sobre **ARA e NC**;
`apps/api/tests/federacao/test_porta_dos_fundos_do_catalogo.py` cobre o catálogo sobre **NC**. As
ferramentas que nasceram depois — ARF, APR, AT, S&T e Focalização — ficaram de fora das
duas varreduras, e a proteção delas é **implícita**: `Projeto._exigir_raiz` bloqueia toda
ferramenta que não seja a genérica, registrada ou não.

Proteção implícita é a boa notícia; **proteção implícita não medida** é a mesma classe de
buraco que a regressão da onda anterior expôs. Este arquivo mede: para cada ferramenta e
para cada uma das **oito** mutações de grafo do `Projeto`, pelas **duas** portas que
alcançam aquele estado.

A varredura é **derivada do produto**, não escrita à mão duas vezes: as ferramentas saem do
mapa `RAIZ_POR_FERRAMENTA` do domínio, então uma ferramenta nova entra nesta varredura no
dia em que se registra — nunca no dia em que alguém lembrar.
"""
from __future__ import annotations

from uuid import uuid4

import pytest

from toc_api.dominio.projeto import FERRAMENTA_GENERICA, RAIZ_POR_FERRAMENTA

from .conftest import valida_envelope_de_erro

#: `ferramenta → como criar um projeto dela pela rota própria`. Derivar isto do produto
#: seria adivinhar rota; o que é derivado do produto é a LISTA de ferramentas, e o teste de
#: completude abaixo recusa qualquer uma que apareça sem entrada aqui.
CRIACAO_POR_FERRAMENTA: dict[str, tuple[str, dict]] = {
    "ara": ("/toc/ara/projetos", {"nome": "Horizonte — realidade atual"}),
    "nc": ("/toc/nc/projetos", {"nome": "Horizonte — dilema"}),
    "arf": ("/toc/arf/projetos", {"nome": "Horizonte — futuro"}),
    "apr": ("/toc/apr/projetos", {"nome": "Horizonte — implantação", "objetivo": "Reduzir a evasão"}),
    "at": ("/toc/at/projetos", {"nome": "Horizonte — transição"}),
    "snt": ("/toc/snt/projetos", {"nome": "Horizonte — estratégia", "meta_global": "Crescer sem perder qualidade"}),
    "focalizacao": (
        "/toc/focalizacao/analises",
        {"nome": "Horizonte — matrículas", "sistema": "Da inscrição à primeira aula"},
    ),
}

FERRAMENTAS = sorted(CRIACAO_POR_FERRAMENTA)

#: As quatro ações mutadoras do catálogo que montam os MESMOS casos de uso genéricos do M1
#: — a segunda porta para o mesmo estado.
ACOES_GENERICAS = ("toc.criar_nos", "toc.criar_arestas", "toc.atualizar_no", "toc.excluir_nos")


def criar(plena, ferramenta: str) -> str:
    rota, corpo = CRIACAO_POR_FERRAMENTA[ferramenta]
    resposta = plena.post(rota, json=corpo)
    assert resposta.status_code == 201, f"{ferramenta}: {resposta.status_code} {resposta.text[:200]}"
    corpo_lido = resposta.json()
    # A análise de focalização devolve o projeto embrulhado; as demais, o projeto.
    return corpo_lido["projeto"]["id"] if "projeto" in corpo_lido else corpo_lido["id"]


def mutacoes_genericas(projeto_id: str, no_id: str, aresta_id: str) -> dict[str, tuple]:
    """As oito mutações de grafo do `Projeto`, cada uma pela rota genérica do M1."""
    base = f"/toc/projetos/{projeto_id}"
    return {
        "adicionar_no": ("POST", f"{base}/nos", {"titulo": "nó invasor"}),
        "editar_no": ("PATCH", f"{base}/nos/{no_id}", {"titulo": "título invasor"}),
        "mover_no": ("PATCH", f"{base}/nos/{no_id}", {"posicao": {"x": 10.0, "y": 20.0}}),
        "recolher_no": ("PATCH", f"{base}/nos/{no_id}", {"recolhido": True}),
        "excluir_no": ("DELETE", f"{base}/nos/{no_id}", None),
        "ligar": ("POST", f"{base}/arestas", {"origem_id": no_id, "destino_id": str(uuid4())}),
        "editar_aresta": ("PATCH", f"{base}/arestas/{aresta_id}", {"rotulo": "rótulo invasor"}),
        "excluir_aresta": ("DELETE", f"{base}/arestas/{aresta_id}", None),
    }


# =======================================================================================
# Completude: a varredura acompanha o produto
# =======================================================================================


def test_toda_ferramenta_registrada_entra_na_varredura():
    """Ferramenta nova sem entrada aqui derruba a suíte — é a forcing function do arquivo.

    `RAIZ_POR_FERRAMENTA` é preenchido por `registrar_raiz_de_ferramenta`, que cada raiz
    chama ao ser importada. Comparar a varredura com ele é comparar com o produto, e não
    com a lembrança de quem escreveu o teste.
    """
    registradas = set(RAIZ_POR_FERRAMENTA) - {FERRAMENTA_GENERICA}
    faltando = sorted(registradas - set(CRIACAO_POR_FERRAMENTA))

    print(
        f"\nferramentas registradas no domínio: {sorted(registradas)} · "
        f"varridas aqui: {FERRAMENTAS} · faltando: {faltando}"
    )
    assert not faltando, (
        f"ferramenta(s) registrada(s) e fora da varredura da porta dos fundos: {faltando}"
    )


# =======================================================================================
# Porta 1 — as rotas genéricas do M1
# =======================================================================================


@pytest.mark.parametrize("ferramenta", FERRAMENTAS)
def test_as_oito_mutacoes_de_grafo_sao_recusadas_pela_rota_generica(plena, ferramenta: str):
    """DDD: o grafo de um projeto de ferramenta só muda pela raiz do agregado dela.

    As oito mutações são varridas de uma vez porque um teste que conferisse uma só
    responderia verde sobre sete portas abertas — que é o defeito que a regra R2 nomeia.
    """
    projeto_id = criar(plena, ferramenta)
    chamadas = mutacoes_genericas(projeto_id, str(uuid4()), str(uuid4()))

    desfechos = {}
    for operacao, (metodo, rota, corpo) in chamadas.items():
        resposta = plena.request(metodo, rota, json=corpo) if corpo else plena.request(metodo, rota)
        desfechos[operacao] = (resposta.status_code, resposta)

    print(
        f"\n{ferramenta}: {len(desfechos)} mutação(ões) pela rota genérica → "
        f"{ {op: st for op, (st, _) in desfechos.items()} }"
    )
    for operacao, (status, resposta) in desfechos.items():
        assert status == 409, f"{ferramenta}.{operacao} respondeu {status}: {resposta.text[:200]}"
        erro = valida_envelope_de_erro(resposta)
        assert erro["code"] == "AGGREGATE_ROOT_REQUIRED", (ferramenta, operacao, erro)
        # O cliente discrimina por CÓDIGO e por DADO, nunca por mensagem (§A.7).
        assert erro["details"]["ferramenta"] == ferramenta, (operacao, erro["details"])
        assert erro["details"]["operacao"] == operacao, (operacao, erro["details"])


def test_o_projeto_generico_continua_mutando_pela_rota_generica(plena):
    """O contraprova: a guarda fecha as ferramentas e NÃO fecha o M1.

    Sem esta linha, um `raise` incondicional passaria em todos os testes acima — verde
    sobre um produto que perdeu o núcleo.
    """
    projeto = plena.post("/toc/projetos", json={"nome": "Rascunho livre"}).json()
    um = plena.post(f"/toc/projetos/{projeto['id']}/nos", json={"titulo": "primeiro"})
    dois = plena.post(f"/toc/projetos/{projeto['id']}/nos", json={"titulo": "segundo"})
    aresta = plena.post(
        f"/toc/projetos/{projeto['id']}/arestas",
        json={"origem_id": um.json()["id"], "destino_id": dois.json()["id"]},
    )

    print(f"\ngenérico: nós {um.status_code}/{dois.status_code} · aresta {aresta.status_code}")
    assert (um.status_code, dois.status_code, aresta.status_code) == (201, 201, 201)


# =======================================================================================
# Porta 2 — o catálogo `toc.*`, que monta os MESMOS casos de uso do M1
# =======================================================================================


@pytest.mark.parametrize("ferramenta", FERRAMENTAS)
def test_as_acoes_genericas_do_catalogo_tambem_sao_recusadas(plena, ferramenta: str):
    """A segunda porta para o mesmo estado — e a recusa vem do MESMO lugar.

    A correção mora no `Projeto`, não na borda: aqui ela não é reprogramada, ela chega de
    graça. E o desfecho é `failed`, que é a forma do §A.5.9(b) para "este alvo não
    executou": recusa de invariante é dado de desfecho, não erro de sistema.

    **O que se afirma é o desfecho e o ESTADO, nunca o texto do motivo.** O produto tem
    hoje duas guardas em série no mesmo caminho — a da ferramenta declarada na ação e a da
    raiz do agregado — e qual delas fala primeiro é detalhe interno. Um teste preso à frase
    quebraria a cada vez que a ordem mudasse, sem que nada de verdade tivesse mudado; é a
    mesma armadilha que o §A.7 nomeia para o cliente ("discrimine por código e por dado,
    nunca por mensagem").
    """
    projeto_id = criar(plena, ferramenta)
    antes = plena.get(f"/toc/projetos/{projeto_id}").json()
    args_por_acao = {
        "toc.criar_nos": {"projeto_id": projeto_id, "nos": [{"titulo": "nó invasor", "tipo": "ude"}]},
        "toc.criar_arestas": {
            "projeto_id": projeto_id,
            "arestas": [{"origem_id": str(uuid4()), "destino_id": str(uuid4())}],
        },
        "toc.atualizar_no": {"projeto_id": projeto_id, "no_id": str(uuid4()), "titulo": "invasor"},
        "toc.excluir_nos": {"projeto_id": projeto_id, "no_ids": [str(uuid4())]},
    }

    desfechos = {}
    for action_id in ACOES_GENERICAS:
        proposta = plena.post(
            "/toc/propostas", json={"action_id": action_id, "args": args_por_acao[action_id]}
        )
        assert proposta.status_code == 201, (action_id, proposta.text[:200])
        decidida = plena.post(
            f"/toc/propostas/{proposta.json()['proposal_id']}/decisao", json={"aprovado": True}
        )
        assert decidida.status_code == 200, (action_id, decidida.text[:200])
        corpo = decidida.json()
        motivo = corpo["outcomes"][0]["message"] if corpo["outcomes"] else corpo["mensagem"]
        desfechos[action_id] = (corpo["status"], motivo)

    depois = plena.get(f"/toc/projetos/{projeto_id}").json()
    print(
        f"\n{ferramenta}: { {a: st for a, (st, _) in desfechos.items()} } · "
        f"nós {len(antes['nos'])}→{len(depois['nos'])} · "
        f"arestas {len(antes['arestas'])}→{len(depois['arestas'])}"
    )
    for action_id, (status, motivo) in desfechos.items():
        assert status == "failed", f"{ferramenta}/{action_id} executou: {motivo}"
        assert motivo, f"{ferramenta}/{action_id} falhou sem dizer por quê"
    assert depois == antes, (
        f"{ferramenta}: as quatro ações genéricas falharam e MESMO ASSIM o estado mudou"
    )


def test_as_acoes_genericas_do_catalogo_continuam_mutando_o_projeto_generico(plena):
    """A contraprova da segunda porta: o catálogo não perdeu o núcleo."""
    projeto = plena.post("/toc/projetos", json={"nome": "Rascunho livre"}).json()
    proposta = plena.post(
        "/toc/propostas",
        json={
            "action_id": "toc.criar_nos",
            "args": {"projeto_id": projeto["id"], "nos": [{"titulo": "nó legítimo", "tipo": "ude"}]},
        },
    ).json()
    decidida = plena.post(
        f"/toc/propostas/{proposta['proposal_id']}/decisao", json={"aprovado": True}
    ).json()

    lido = plena.get(f"/toc/projetos/{projeto['id']}").json()
    print(f"\ngenérico pelo catálogo: {decidida['status']} · nós={[n['titulo'] for n in lido['nos']]}")
    assert decidida["status"] == "executed", decidida
    assert [n["titulo"] for n in lido["nos"]] == ["nó legítimo"]
