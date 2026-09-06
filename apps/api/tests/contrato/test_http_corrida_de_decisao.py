"""A corrida perdida e a chave reaproveitada vistas pela borda — códigos, não mensagens.

Siglas, uma vez neste arquivo: **APH** — Aplicação ↔ Harness (o padrão da fronteira) ·
**FSM** — máquina de estados finitos · **HTTP** — *HyperText Transfer Protocol* · **M1** —
Núcleo de Diagramas Lógicos.

A corrida de verdade (oito fios contra o PostgreSQL) está em
`tests/integracao/test_corrida_de_confirmacao_no_postgres.py`. **Este arquivo mede outra
coisa**, e a diferença é o motivo de ele existir: que a recusa **chega ao cliente** com o
código estável do §A.7 do Anexo A, e não como erro de sistema. Um conserto que serializasse
certo no banco e devolvesse `500` teria trocado execução múltipla por falha opaca.

Escopo declarado: repositório em memória — que tem a MESMA trava do adaptador SQL
(*Structured Query Language*), e é essa paridade que dá sentido a medir a borda aqui
(`tests/federacao/test_paridade_do_repositorio_de_propostas.py`).
"""
from __future__ import annotations

from .conftest import valida_envelope_de_erro

NARRATIVA = (
    "A Instituição Horizonte precisa de receita nova já no próximo semestre. A direção "
    "quer abrir turmas em três cidades novas; o corpo docente teme pela reputação."
)


def _projeto_com_proposta(plena, titulo="Efeito indesejável da Instituição Horizonte"):
    projeto = plena.post("/toc/projetos", json={"nome": "Horizonte — árvore"}).json()
    criada = plena.post(
        "/toc/propostas",
        json={
            "action_id": "toc.criar_nos",
            "args": {
                "projeto_id": projeto["id"],
                "nos": [{"titulo": titulo, "tipo": "ude"}],
            },
        },
    )
    assert criada.status_code == 201, criada.text
    return projeto, criada.json()


def test_a_confirmacao_repetida_com_a_mesma_chave_devolve_o_mesmo_corpo(plena):
    """APH-5.3: a mesma chave produz uma execução e quantas respostas idênticas pedirem.

    Sequencial aqui de propósito — é a metade do requisito que não depende de corrida, e
    ela sozinha já falhava antes: a chave era gravada e nunca consultada, então a segunda
    chamada caía na RF-16 por acaso e não pela chave.
    """
    projeto, proposta = _projeto_com_proposta(plena)
    corpo = {"aprovado": True, "idempotency_key": "idem-uma-decisao-humana"}

    primeira = plena.post(f"/toc/propostas/{proposta['proposal_id']}/decisao", json=corpo)
    segunda = plena.post(f"/toc/propostas/{proposta['proposal_id']}/decisao", json=corpo)

    assert primeira.status_code == 200, primeira.text
    assert segunda.status_code == 200, segunda.text
    assert segunda.json() == primeira.json()
    assert primeira.json()["status"] == "executed"
    nos = plena.get(f"/toc/projetos/{projeto['id']}").json()["nos"]
    assert len(nos) == 1, f"{len(nos)} nós para um alvo: a segunda decisão reexecutou"


def test_a_chave_reaproveitada_em_outra_proposta_e_recusada_com_codigo_proprio(plena):
    """Uma chave, uma execução — inclusive quando o cliente a leva para outra proposta."""
    _, primeira = _projeto_com_proposta(plena, "Primeiro efeito indesejável")
    _, segunda = _projeto_com_proposta(plena, "Segundo efeito indesejável")
    chave = "idem-reaproveitada-por-engano"

    aceita = plena.post(
        f"/toc/propostas/{primeira['proposal_id']}/decisao",
        json={"aprovado": True, "idempotency_key": chave},
    )
    recusada = plena.post(
        f"/toc/propostas/{segunda['proposal_id']}/decisao",
        json={"aprovado": True, "idempotency_key": chave},
    )

    assert aceita.status_code == 200, aceita.text
    assert recusada.status_code == 409, recusada.text
    envelope = valida_envelope_de_erro(recusada)
    assert envelope["code"] == "IDEMPOTENCY_KEY_REUSED", envelope
    assert "chave" in envelope["message"].lower()


def test_a_decisao_repetida_sem_chave_continua_devolvendo_o_desfecho_original(plena):
    """RF-16 não muda: a repetição SEQUENCIAL de uma decisão terminal devolve o original.

    A trava é sobre a corrida, não sobre o botão clicado duas vezes com um segundo de
    intervalo. Se a correção tivesse transformado esta repetição em `409`, ela teria
    trocado um defeito por uma regressão de experiência de uso.
    """
    projeto, proposta = _projeto_com_proposta(plena)

    primeira = plena.post(
        f"/toc/propostas/{proposta['proposal_id']}/decisao", json={"aprovado": True}
    )
    segunda = plena.post(
        f"/toc/propostas/{proposta['proposal_id']}/decisao", json={"aprovado": True}
    )

    assert primeira.status_code == 200 and segunda.status_code == 200
    assert segunda.json() == primeira.json()
    assert len(plena.get(f"/toc/projetos/{projeto['id']}").json()["nos"]) == 1


def test_a_recusa_repetida_tambem_devolve_o_desfecho_original(plena):
    projeto, proposta = _projeto_com_proposta(plena)

    primeira = plena.post(
        f"/toc/propostas/{proposta['proposal_id']}/decisao", json={"aprovado": False}
    )
    segunda = plena.post(
        f"/toc/propostas/{proposta['proposal_id']}/decisao", json={"aprovado": False}
    )

    assert primeira.status_code == 200 and segunda.status_code == 200
    assert primeira.json()["status"] == "denied"
    assert segunda.json() == primeira.json()
    traco = [
        t
        for t in plena.get("/aph/traco").json()
        if t["proposal_id"] == proposta["proposal_id"]
    ]
    assert len(traco) == 1, f"{len(traco)} linhas de traço para UMA recusa: {traco}"
    assert plena.get(f"/toc/projetos/{projeto['id']}").json()["nos"] == []
