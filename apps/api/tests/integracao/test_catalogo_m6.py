"""A ação assistida do M6 na máquina de estados do servidor (spec 009, RF-19..RF-21).

Siglas, uma vez neste arquivo: **M6** — Focalização · **APH** — Aplicação ↔ Harness ·
**ARA** — Árvore da Realidade Atual · **FSM** — máquina de estados finitos · **HTTP** —
*HyperText Transfer Protocol* · **RF/RN** — requisito funcional / regra de negócio ·
**DoD** — *Definition of Done* (Definição de Pronto) · **IA** — inteligência artificial.

Este arquivo cobre as linhas 9 e 10 da tabela de aceite da spec, e cada uma responde a uma
pergunta diferente:

- **DoD 9** — *recusar deixa a análise intacta?* A prova é feita com **três aplicações
  diferentes** sobre o mesmo esquema migrado: uma propõe, outra recusa, uma terceira lê. Se
  a "persistência" fosse estado de tela, a segunda não acharia a proposta e a terceira não
  acharia a análise. E o estado serializado antes e depois é comparado inteiro.
- **DoD 10** — *capability ausente esconde a mutadora?* Um principal só-leitura não vê a
  ação no catálogo composto, e citá-la pelo identificador recebe a MESMA recusa de uma
  ação inexistente — porque distinguir vazaria o inventário de quem tem mais permissão
  (§B.7.3 do Anexo B).

Marcado `integracao`: pulado com o motivo quando o banco não responde, jamais substituído
por um duplo. As personas são fictícias (ADR 0006).
"""
from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient

from toc_api.http.app import criar_app

pytestmark = pytest.mark.integracao

ACAO = "toc.suggest_constraint"
AUTORA = "Facilitadora TOC"
SISTEMA = "Da inscrição do candidato à primeira aula assistida"
RESTRICAO = "Capacidade de conferência da secretaria acadêmica"
JUSTIFICATIVA = "a fila de matrículas só cresce nesta etapa, em todo período de entrada"

IDENTIDADES = {
    "tok-integra-facilitadora": {
        "inquilino_id": "inq-horizonte",
        "usuario_id": "usr-facilitadora",
        "capabilities": ["toc:read", "toc:write"],
    },
    "tok-integra-observadora": {
        "inquilino_id": "inq-horizonte",
        "usuario_id": "usr-observadora",
        "capabilities": ["toc:read"],
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


def montar_analise_com_ara(c: TestClient) -> tuple[str, str, str]:
    """A análise sintética com uma ARA vinculada ao passo `identificar` e uma causa raiz."""
    analise = c.post(
        "/toc/focalizacao/analises",
        json={"nome": "Fluxo de matrículas", "sistema": SISTEMA},
    ).json()
    projeto_id = analise["projeto"]["id"]
    ara = c.post("/toc/ara/projetos", json={"nome": "ARA do fluxo"}).json()
    causa = c.post(
        f"/toc/ara/projetos/{ara['id']}/efeitos",
        json={"titulo": "A secretaria confere documentos um a um."},
    ).json()
    efeito = c.post(
        f"/toc/ara/projetos/{ara['id']}/efeitos",
        json={"titulo": "A fila de matrículas passa de 200 pedidos em março."},
    ).json()
    c.post(f"/toc/ara/projetos/{ara['id']}/nos/{efeito['id']}/ude", json={})
    c.post(
        f"/toc/ara/projetos/{ara['id']}/arestas",
        json={"origem_id": causa["id"], "destino_id": efeito["id"]},
    )
    c.post(
        f"/toc/focalizacao/analises/{projeto_id}/passos/identificar/vinculos",
        json={"ferramenta": "ara", "projeto_id": ara["id"]},
    )
    return projeto_id, ara["id"], causa["id"]


# ---------------------------------------------------------------------------------------
# DoD 9 — a proposta nasce, e RECUSAR deixa a análise byte a byte intacta
# ---------------------------------------------------------------------------------------


def test_a_sugestao_aceita_registra_a_restricao_com_a_referencia_de_origem(
    url_postgres, esquema_migrado
):
    """RF-19 + INT-02: aceitar escreve — e escreve com a evidência que sustenta."""
    primeira = cliente(url_postgres, esquema_migrado)
    projeto_id, ara_id, causa_id = montar_analise_com_ara(primeira)

    previa = primeira.post(
        f"/toc/focalizacao/analises/{projeto_id}/sugestoes-de-restricao"
    ).json()
    assert previa["action_id"] == ACAO
    assert previa["candidatas"], previa

    criada = primeira.post(
        "/toc/propostas",
        json={
            "action_id": ACAO,
            "args": {
                "projeto_id": projeto_id,
                "ara_projeto_id": ara_id,
                "no_id": causa_id,
                "descricao": RESTRICAO,
                "tipo": "fisica",
                "justificativa": JUSTIFICATIVA,
                "autor": AUTORA,
            },
        },
    )
    assert criada.status_code == 201, criada.text
    proposta = criada.json()
    assert proposta["estado"] == "awaiting_approval"

    # Aplicação NOVA: a proposta só está aqui porque foi para o PostgreSQL.
    segunda = cliente(url_postgres, esquema_migrado)
    decidida = segunda.post(
        f"/toc/propostas/{proposta['proposal_id']}/decisao", json={"aprovado": True}
    )
    assert decidida.status_code == 200, decidida.text
    assert decidida.json()["status"] == "executed", decidida.text

    # Outra aplicação NOVA: a restrição lida do banco, não de estado de tela.
    terceira = cliente(url_postgres, esquema_migrado)
    jornada = terceira.get(f"/toc/focalizacao/analises/{projeto_id}/jornada").json()
    print(
        f"\nproposta {proposta['proposal_id']} aceita por outra aplicação; "
        f"restrição gravada: {jornada['restricao']['descricao']!r}"
    )
    assert jornada["restricao"]["descricao"] == RESTRICAO
    assert jornada["restricao"]["tipo"] == "fisica"
    assert jornada["restricao"]["origem"] == {
        "ferramenta": "ara",
        "projeto_id": ara_id,
        "no_id": causa_id,
    }


def test_recusar_a_sugestao_deixa_a_analise_identica(url_postgres, esquema_migrado):
    """DoD 9: "estado serializado idêntico antes/depois da recusa" — medido, não prometido."""
    primeira = cliente(url_postgres, esquema_migrado)
    projeto_id, ara_id, causa_id = montar_analise_com_ara(primeira)
    antes = primeira.get(f"/toc/focalizacao/analises/{projeto_id}").json()

    proposta = primeira.post(
        "/toc/propostas",
        json={
            "action_id": ACAO,
            "args": {
                "projeto_id": projeto_id,
                "ara_projeto_id": ara_id,
                "no_id": causa_id,
                "descricao": RESTRICAO,
                "tipo": "fisica",
                "justificativa": JUSTIFICATIVA,
            },
        },
    ).json()
    assert primeira.get(f"/toc/focalizacao/analises/{projeto_id}").json() == antes, (
        "propor não escreve: a análise já teria mudado aqui"
    )

    segunda = cliente(url_postgres, esquema_migrado)
    recusada = segunda.post(
        f"/toc/propostas/{proposta['proposal_id']}/decisao", json={"aprovado": False}
    )
    assert recusada.status_code == 200, recusada.text
    assert recusada.json()["status"] == "denied"

    terceira = cliente(url_postgres, esquema_migrado)
    depois = terceira.get(f"/toc/focalizacao/analises/{projeto_id}").json()
    traco = [
        t
        for t in terceira.get("/aph/traco").json()
        if t["proposal_id"] == proposta["proposal_id"]
    ]
    print(
        f"recusa persistida · traço: {[t['desfecho'] for t in traco]} · "
        f"restrição depois: {depois['jornada']['restricao']}"
    )
    assert depois == antes, "recusar tem de deixar a análise byte a byte igual"
    assert depois["jornada"]["restricao"] is None
    # APH-5.5: o traço existe para 100% das ações, inclusive as recusadas.
    assert [t["desfecho"] for t in traco] == ["denied"]


def test_a_proposta_sem_a_referencia_de_origem_nem_nasce(url_postgres, esquema_migrado):
    """O `input_schema` recusa ANTES de a proposta existir — e a recusa deixa traço."""
    c = cliente(url_postgres, esquema_migrado)
    projeto_id, _, _ = montar_analise_com_ara(c)

    resposta = c.post(
        "/toc/propostas",
        json={
            "action_id": ACAO,
            "args": {
                "projeto_id": projeto_id,
                "descricao": RESTRICAO,
                "tipo": "fisica",
                "justificativa": JUSTIFICATIVA,
            },
        },
    )

    # `400` e não `422`: a validação do `input_schema` acontece no SERVIDOR, antes de a
    # proposta existir (RF-22 do ciclo 006), e a borda a traduz no código estável do §A.7.
    assert resposta.status_code == 400, resposta.text
    assert resposta.json()["error"]["code"] == "INVALID_ARGUMENT"
    assert "ara_projeto_id" in resposta.json()["error"]["message"]


# ---------------------------------------------------------------------------------------
# DoD 10 — capability ausente esconde a mutadora
# ---------------------------------------------------------------------------------------


def test_capability_ausente_esconde_a_acao_mutadora_do_m6(url_postgres, esquema_migrado):
    """RF-21: sem `toc:write`, a ação **não existe** para aquele principal (APH-4.3)."""
    plena = cliente(url_postgres, esquema_migrado)
    leitora = cliente(url_postgres, esquema_migrado, token="tok-integra-observadora")

    do_pleno = {a["action_id"] for a in plena.get("/aph/catalog").json()}
    do_leitor = {a["action_id"] for a in leitora.get("/aph/catalog").json()}

    medida = (
        f"catálogo composto: pleno → {len(do_pleno)} ações; "
        f"só-leitura → {len(do_leitor)}; a mutadora do M6 está no primeiro: "
        f"{ACAO in do_pleno}; no segundo: {ACAO in do_leitor}"
    )
    print(f"\n{medida}")
    assert ACAO in do_pleno, medida
    assert ACAO not in do_leitor, medida
    assert do_leitor < do_pleno


def test_citar_a_acao_sem_capability_recebe_a_recusa_de_acao_inexistente(
    url_postgres, esquema_migrado
):
    """§B.7.3: "não existe" e "existe e você não pode" respondem IGUAL — senão o inventário
    de quem tem mais permissão vaza pela mensagem de erro."""
    plena = cliente(url_postgres, esquema_migrado)
    projeto_id, ara_id, causa_id = montar_analise_com_ara(plena)
    leitora = cliente(url_postgres, esquema_migrado, token="tok-integra-observadora")

    args = {
        "projeto_id": projeto_id,
        "ara_projeto_id": ara_id,
        "no_id": causa_id,
        "descricao": RESTRICAO,
        "tipo": "fisica",
        "justificativa": JUSTIFICATIVA,
    }
    conhecida = leitora.post("/toc/propostas", json={"action_id": ACAO, "args": args})
    inventada = leitora.post(
        "/toc/propostas", json={"action_id": "toc.nao_existe", "args": args}
    )

    print(
        f"ação conhecida sem capability → {conhecida.status_code} "
        f"{conhecida.json()['error']['code']}; ação inventada → "
        f"{inventada.status_code} {inventada.json()['error']['code']}"
    )
    assert conhecida.status_code == inventada.status_code
    assert conhecida.json()["error"]["code"] == inventada.json()["error"]["code"]


def test_a_jornada_inteira_funciona_com_o_catalogo_de_fora(url_postgres, esquema_migrado):
    """RF-20: a jornada guiada é completa por construção — a sugestão é aceleradora.

    O teste não desliga o catálogo (ele é da composição); ele faz o que a RF-20 promete:
    percorre os cinco passos **sem tocar em ação nenhuma** e chega ao recomeço.
    """
    c = cliente(url_postgres, esquema_migrado)
    analise = c.post(
        "/toc/focalizacao/analises",
        json={"nome": "Fluxo de matrículas", "sistema": SISTEMA},
    ).json()
    projeto_id = analise["projeto"]["id"]

    assert c.post(
        f"/toc/focalizacao/analises/{projeto_id}/restricao",
        json={
            "descricao": RESTRICAO,
            "tipo": "fisica",
            "justificativa": JUSTIFICATIVA,
            "autor": AUTORA,
        },
    ).status_code == 201
    for passo, decisao in (
        ("identificar", "a restrição é a conferência da secretaria"),
        ("explorar", "priorizar matrículas com documentação completa"),
        ("subordinar", "nenhuma turma abre antes da conferência"),
        ("elevar", "contratar duas pessoas para a conferência"),
    ):
        resposta = c.post(
            f"/toc/focalizacao/analises/{projeto_id}/passos/{passo}/conclusao",
            json={"decisao": decisao, "autor": AUTORA},
        )
        assert resposta.status_code == 200, resposta.text

    recomecada = c.post(f"/toc/focalizacao/analises/{projeto_id}/recomecos")
    assert recomecada.status_code == 201, recomecada.text
    print(
        "jornada completa sem catálogo: "
        f"{recomecada.json()['jornada']['ordem']} ciclos, "
        f"{recomecada.json()['jornada']['herancas_pendentes']} vereditos herdados"
    )
    assert recomecada.json()["jornada"]["ordem"] == 2
    assert recomecada.json()["jornada"]["herancas_pendentes"] == 2
