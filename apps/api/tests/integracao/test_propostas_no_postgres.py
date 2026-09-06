"""O laço da assistência contra o PostgreSQL REAL — aceitar tem de sobreviver à recarga.

Siglas, uma vez neste arquivo: **APH** — Aplicação ↔ Harness (o padrão da fronteira) ·
**NC** — Nuvem de Conflito · **FSM** — máquina de estados finitos · **HTTP** —
*HyperText Transfer Protocol* · **RF** — requisito funcional.

Os testes de contrato de `/toc/propostas` rodam sobre o repositório em memória: eles medem
forma de resposta, ordem das transições e fronteira de inquilino, e **não provam
persistência nenhuma**. Este arquivo fecha a diferença, e é ele que responde à pergunta que
a interface faz de verdade: *aceitei a geração; ela continua lá quando eu recarrego?*

A prova é feita com **três aplicações diferentes** sobre o mesmo esquema migrado:

1. a primeira propõe (e nada é escrito);
2. a **segunda** confirma — se a proposta vivesse em memória, ela não existiria aqui;
3. a **terceira** lê a nuvem — se a escrita fosse estado de tela, não estaria aqui.

É o defeito D-07 da 4ª geração da linhagem medido pelo avesso: lá a "persistência" era um
vetor em memória (`tocbuilderv3/services/mockApiService.ts`), e recarregar perdia tudo.

Marcado `integracao`: pulado com o motivo quando o banco não responde, jamais substituído
por um duplo — um teste de integração que cai em SQLite não integrou nada.
"""
from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient

from toc_api.http.app import criar_app

pytestmark = pytest.mark.integracao

ACAO_DE_GERACAO = "toc.generate_conflict_cloud"
NARRATIVA = (
    "A Instituição Horizonte precisa de receita nova já no próximo semestre. A direção "
    "quer abrir turmas em três cidades novas; o corpo docente teme pela reputação."
)

IDENTIDADES = {
    "tok-integra-facilitadora": {
        "inquilino_id": "inq-horizonte",
        "usuario_id": "usr-facilitadora",
        "capabilities": ["toc:read", "toc:write"],
    },
}


def cliente(url: str, esquema: str, token: str = "tok-integra-facilitadora") -> TestClient:
    """Uma aplicação NOVA a cada chamada — o equivalente a recarregar a tela."""
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


def test_a_geracao_aceita_sobrevive_a_um_processo_novo(url_postgres, esquema_migrado):
    """O laço inteiro atravessando o banco: propor aqui, confirmar ali, ler acolá."""
    primeira = cliente(url_postgres, esquema_migrado)
    projeto = primeira.post("/toc/nc/projetos", json={"nome": "Horizonte — NC"}).json()
    previa = primeira.post(
        f"/toc/nc/projetos/{projeto['id']}/geracoes", json={"narrativa": NARRATIVA}
    ).json()
    antes = primeira.get(f"/toc/nc/projetos/{projeto['id']}").json()

    criada = primeira.post(
        "/toc/propostas",
        json={
            "action_id": previa["action_id"],
            "args": {
                "projeto_id": projeto["id"],
                "narrativa": NARRATIVA,
                "resultado": previa["resultado"],
            },
        },
    )
    assert criada.status_code == 201, criada.text
    proposta = criada.json()
    assert proposta["estado"] == "awaiting_approval"
    assert primeira.get(f"/toc/nc/projetos/{projeto['id']}").json() == antes

    # Aplicação NOVA: a proposta só está aqui porque foi para o PostgreSQL.
    segunda = cliente(url_postgres, esquema_migrado)
    decidida = segunda.post(
        f"/toc/propostas/{proposta['proposal_id']}/decisao", json={"aprovado": True}
    )
    assert decidida.status_code == 200, decidida.text
    assert decidida.json()["status"] == "executed", decidida.text

    # Outra aplicação NOVA: a nuvem lida do banco, não de estado de tela.
    terceira = cliente(url_postgres, esquema_migrado)
    depois = terceira.get(f"/toc/nc/projetos/{projeto['id']}").json()
    textos = {e["papel"]: e["texto"] for e in depois["entidades"]}
    premissas = sum(len(a["premissas"]) for a in depois["arestas"])
    print(
        f"\nproposta {proposta['proposal_id']} confirmada por outra aplicação; "
        f"entidades reescritas: {sum(1 for p, t in textos.items() if t == previa['resultado']['entidades'][p])}"
        f" de 5 · premissas gravadas: {premissas}"
    )
    assert textos == previa["resultado"]["entidades"]
    assert premissas > 0, "a geração propõe premissas: aplicá-las é parte do laço"

    # E o traço da execução também atravessou o banco (APH-5.5).
    traco = [
        t
        for t in terceira.get("/aph/traco").json()
        if t["proposal_id"] == proposta["proposal_id"]
    ]
    assert [t["desfecho"] for t in traco] == ["executed"], traco


def test_a_recusa_atravessa_o_banco_e_nao_escreve_nada(url_postgres, esquema_migrado):
    """RF-24: recusar deixa o projeto byte a byte intacto — inclusive depois de recarregar."""
    primeira = cliente(url_postgres, esquema_migrado)
    projeto = primeira.post("/toc/nc/projetos", json={"nome": "Horizonte — NC"}).json()
    previa = primeira.post(
        f"/toc/nc/projetos/{projeto['id']}/geracoes", json={"narrativa": NARRATIVA}
    ).json()
    antes = primeira.get(f"/toc/nc/projetos/{projeto['id']}").json()
    proposta = primeira.post(
        "/toc/propostas",
        json={
            "action_id": previa["action_id"],
            "args": {"projeto_id": projeto["id"], "resultado": previa["resultado"]},
        },
    ).json()

    segunda = cliente(url_postgres, esquema_migrado)
    recusada = segunda.post(
        f"/toc/propostas/{proposta['proposal_id']}/decisao", json={"aprovado": False}
    )

    assert recusada.status_code == 200, recusada.text
    assert recusada.json()["status"] == "denied"
    terceira = cliente(url_postgres, esquema_migrado)
    depois = terceira.get(f"/toc/nc/projetos/{projeto['id']}").json()
    traco = [
        t for t in terceira.get("/aph/traco").json() if t["proposal_id"] == proposta["proposal_id"]
    ]
    print(f"recusa persistida · traço: {[t['desfecho'] for t in traco]}")
    assert depois == antes
    assert [t["desfecho"] for t in traco] == ["denied"]
