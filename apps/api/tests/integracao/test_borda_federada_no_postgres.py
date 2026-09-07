"""O caminho do HOSPEDEIRO até o estado gravado — a borda federada e o fio, ponta a ponta.

Siglas, uma vez neste arquivo: **APH** — Aplicação ↔ Harness (o padrão da fronteira) ·
**ARA** — Árvore da Realidade Atual · **UDE** — Efeito Indesejável · **FSM** — máquina de
estados finitos · **SSE** — *Server-Sent Events* (eventos enviados pelo servidor) ·
**HTTP** — *HyperText Transfer Protocol* · **JSON** — *JavaScript Object Notation* ·
**RF** — requisito funcional.

## O buraco que este arquivo fecha

`apps/api/tests/federacao/test_superficie_aph.py` cobre a superfície inteira do Anexo A — fio,
replay, cancelamento, envelope de erro, catálogo derivado de permissão, máquina de estados
da proposta. E cobre tudo isso **contra um projeto que não existe**: todas as propostas
daquele arquivo apontam para `UUID_INEXISTENTE`, e um dos testes depende disso
(`test_lote_com_falha_em_todos_os_alvos_nao_diz_executed` só passa porque os oito alvos
falham).

O efeito colateral é o defeito de cobertura: **nenhum teste levava o caminho do hospedeiro
até `executed` sobre estado real**. Todas as verificações positivas do desfecho eram feitas
pela porta da própria aplicação (`/toc/propostas`), que é outro roteador. Se a execução
quebrasse só do lado federado — que é precisamente a forma da regressão da onda anterior,
onde a guarda do agregado matou as ações do catálogo sem derrubar um teste sequer — a
suíte continuaria verde.

Aqui o caminho é percorrido inteiro, nas suas **duas** formas:

1. **borda de execução** (`POST /aph/actions/{action_id}`, o contrato do ADR 0023 do
   hospedeiro) → decisão pelo §A.6 → o nó lido do PostgreSQL por outra aplicação;
2. **fio conversacional** (`POST /aph/sessions/{id}/messages`, SSE sobre POST) → o evento
   `action_proposal` que sai no fio → decisão → o nó lido do PostgreSQL.

Base sintética da **Instituição Horizonte** (ADR 0006). Marcado `integracao`: pulado com o
motivo quando o banco não responde, jamais substituído por um duplo.
"""
from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient

from toc_api.dominio.federacao.catalogo import CATALOGO_TOC
from toc_api.http.app import criar_app

from .conftest import liberar_conexoes as _liberar

pytestmark = pytest.mark.integracao

TOKEN = "tok-borda-facilitadora"
TOKEN_SO_LE = "tok-borda-observadora"
CABECALHO = {"Authorization": f"Bearer {TOKEN}"}
CABECALHO_SO_LE = {"Authorization": f"Bearer {TOKEN_SO_LE}"}

IDENTIDADES = {
    TOKEN: {
        "inquilino_id": "inq-horizonte",
        "usuario_id": "usr-facilitadora",
        "capabilities": ["toc:read", "toc:write"],
    },
    TOKEN_SO_LE: {
        "inquilino_id": "inq-horizonte",
        "usuario_id": "usr-observadora",
        "capabilities": ["toc:read"],
    },
}

#: A frase que roteia para `toc.criar_nos` é DERIVADA do próprio catálogo, e não escrita
#: à mão. O roteamento é determinístico sobre `intent_keywords` (§A.2); uma frase fixa aqui
#: passaria a testar a redação de um comentário em vez do roteamento, e apodreceria calada
#: no dia em que as palavras-chave da ação mudassem — que é como este teste nasceu.
FRASE_QUE_ROTEIA = " ".join(CATALOGO_TOC.acao("toc.criar_nos").intent_keywords)

UDE = "A taxa de evasão no primeiro semestre é de 22%."
SEGUNDO_UDE = "O caixa da instituição fecha o trimestre negativo."


#: Toda aplicação aberta por este arquivo, para as conexões ociosas voltarem ao cluster.
#: Sem isso, uma execução deste arquivo sozinha segura dezenas de conexões (cinco por
#: `criar_app`, que é o *pool* padrão do SQLAlchemy) e o cluster responde `FATAL: sorry,
#: too many clients already` — medido, e por um motivo que não é o que os testes medem.
_ABERTAS: list[TestClient] = []


@pytest.fixture(autouse=True)
def _devolver_conexoes():
    yield
    _liberar(_ABERTAS)
    _ABERTAS.clear()


def cliente(url: str, esquema: str) -> TestClient:
    """Uma aplicação NOVA a cada chamada — o equivalente a recarregar a tela."""
    app = criar_app(
        {
            "DATABASE_URL": url,
            "TOC_DB_SCHEMA": esquema,
            "TOC_AMBIENTE": "teste",
            # Turno quase instantâneo: quem exercita a duração real do turno é a suíte de
            # conformidade, contra o serviço de pé.
            "TOC_INTERVALO_DO_TURNO_MS": "1",
            "TOC_IDENTIDADES_FALSAS": json.dumps(IDENTIDADES),
        }
    )
    c = TestClient(app)
    c.headers["Authorization"] = f"Bearer {TOKEN}"
    _liberar(_ABERTAS)
    _ABERTAS.append(c)
    return c


def eventos_do_fio(texto: str) -> list[dict]:
    return [json.loads(l[len("data: ") :]) for l in texto.splitlines() if l.startswith("data: ")]


def projeto_novo(c: TestClient, nome: str = "Horizonte — árvore") -> str:
    resposta = c.post("/toc/projetos", json={"nome": nome})
    assert resposta.status_code == 201, resposta.text
    return resposta.json()["id"]


def titulos_no_banco(url: str, esquema: str, projeto_id: str) -> list[str]:
    """Lido por uma aplicação que não participou de nenhuma escrita."""
    outra = cliente(url, esquema)
    resposta = outra.get(f"/toc/projetos/{projeto_id}")
    assert resposta.status_code == 200, resposta.text
    return [no["titulo"] for no in resposta.json()["nos"]]


# =======================================================================================
# 1 · A borda de execução federada (RF-30..RF-33) até o estado gravado
# =======================================================================================


def test_a_borda_federada_leva_a_mutacao_ate_o_banco_depois_do_gate(
    url_postgres, esquema_migrado
):
    """O caminho do hospedeiro inteiro: propor pela borda, confirmar pelo §A.6, ler do banco.

    Antes deste teste o lado federado só era exercitado contra projeto inexistente — e um
    `executed` que nunca acontece não prova que a execução funciona.
    """
    c = cliente(url_postgres, esquema_migrado)
    projeto_id = projeto_novo(c)
    sessao = c.post("/aph/sessions", headers=CABECALHO).json()["session_id"]

    proposta = c.post(
        f"/aph/actions/toc.criar_nos",
        headers=CABECALHO,
        json={"params": {"projeto_id": projeto_id, "nos": [
            {"titulo": UDE, "tipo": "ude"},
            {"titulo": SEGUNDO_UDE, "tipo": "ude"},
        ]}},
    )
    assert proposta.status_code == 200, proposta.text
    corpo = proposta.json()
    assert set(corpo) == {"result"}, corpo
    proposal_id = corpo["result"].split()[1]

    # Nada foi escrito ainda: a proposta ESPERA (P2, APH-5.2).
    assert titulos_no_banco(url_postgres, esquema_migrado, projeto_id) == []

    decisao = c.post(
        f"/aph/sessions/{sessao}/proposals/{proposal_id}",
        headers=CABECALHO,
        json={"approved": True},
    )
    assert decisao.status_code == 200, decisao.text
    assert decisao.json() == {"proposal_id": proposal_id, "status": "executed"}, decisao.json()

    gravados = titulos_no_banco(url_postgres, esquema_migrado, projeto_id)
    print(f"\nborda federada → banco: {gravados}")
    assert sorted(gravados) == sorted([UDE, SEGUNDO_UDE]), gravados


def test_recusar_pela_borda_federada_deixa_o_projeto_intacto(url_postgres, esquema_migrado):
    """A outra metade do gate: `approved: false` não escreve, e o desfecho é `denied`."""
    c = cliente(url_postgres, esquema_migrado)
    projeto_id = projeto_novo(c)
    sessao = c.post("/aph/sessions", headers=CABECALHO).json()["session_id"]

    proposta = c.post(
        "/aph/actions/toc.criar_nos",
        headers=CABECALHO,
        json={"params": {"projeto_id": projeto_id, "nos": [{"titulo": UDE, "tipo": "ude"}]}},
    ).json()["result"].split()[1]

    decisao = c.post(
        f"/aph/sessions/{sessao}/proposals/{proposta}",
        headers=CABECALHO,
        json={"approved": False},
    )

    assert decisao.json()["status"] == "denied", decisao.json()
    gravados = titulos_no_banco(url_postgres, esquema_migrado, projeto_id)
    print(f"depois da recusa, nós no banco: {gravados}")
    assert gravados == []


def test_o_desfecho_executado_pela_borda_atravessa_o_processo_e_o_traco(
    url_postgres, esquema_migrado
):
    """RF-16 + US-06: confirmar numa aplicação e reler noutra devolve o MESMO desfecho.

    A proposta e o traço têm tabela e migração (`0004`). Se a governança vivesse em
    memória, a segunda aplicação não acharia a proposta — e a idempotência da confirmação
    seria uma promessa que só vale enquanto o processo não reinicia.

    **A sessão de conversa é o oposto, e de propósito** (ADR 0011, §"o que fica de fora"):
    ela é de processo, então cada aplicação abre a sua. O teste faz isso explicitamente —
    e a linha seguinte, `test_a_sessao_do_fio_nao_atravessa_o_processo`, é a que fixa essa
    fronteira para ela não mudar sem que alguém perceba.
    """
    primeira = cliente(url_postgres, esquema_migrado)
    projeto_id = projeto_novo(primeira)
    proposta = primeira.post(
        "/aph/actions/toc.criar_nos",
        headers=CABECALHO,
        json={"params": {"projeto_id": projeto_id, "nos": [{"titulo": UDE, "tipo": "ude"}]}},
    ).json()["result"].split()[1]

    segunda = cliente(url_postgres, esquema_migrado)
    sessao_da_segunda = segunda.post("/aph/sessions", headers=CABECALHO).json()["session_id"]
    decisao = segunda.post(
        f"/aph/sessions/{sessao_da_segunda}/proposals/{proposta}",
        headers=CABECALHO,
        json={"approved": True},
    )
    assert decisao.json()["status"] == "executed", decisao.json()

    terceira = cliente(url_postgres, esquema_migrado)
    sessao_da_terceira = terceira.post("/aph/sessions", headers=CABECALHO).json()["session_id"]
    repetida = terceira.post(
        f"/aph/sessions/{sessao_da_terceira}/proposals/{proposta}",
        headers=CABECALHO,
        json={"approved": True},
    )
    print(
        f"\nproposta {proposta}: confirmada pela 2ª aplicação, reconfirmada pela 3ª → "
        f"{repetida.json()}"
    )
    assert repetida.json() == decisao.json(), (repetida.json(), decisao.json())
    assert titulos_no_banco(url_postgres, esquema_migrado, projeto_id) == [UDE]

    traco = terceira.get("/aph/traco", headers=CABECALHO)
    assert traco.status_code == 200, traco.text
    linhas = [l for l in traco.json() if l.get("action_id") == "toc.criar_nos"]
    print(f"linhas de traço para a ação: {len(linhas)} de {len(traco.json())} no total")
    assert linhas, traco.json()
    # RF-26: o traço discrimina o desfecho POR ALVO, e o alvo de `toc.criar_nos` é o
    # enunciado — é o vocabulário que a ação declara em `campo_de_alvos`. Medido aqui, e
    # não suposto: `apps/api/tests/federacao/test_superficie_aph.py::
    # test_o_traco_nunca_carrega_o_enunciado_do_no` tem nome e docstring que dizem o
    # contrário do que ele próprio afirma (`assert "UDE 1" in corpo`), e crer no nome
    # levaria alguém a concluir que o traço é anônimo quando ele não é.
    despejo = json.dumps(traco.json(), ensure_ascii=False)
    assert UDE in despejo, "o desfecho por alvo sumiu do traço (RF-26)"
    # O que o traço de fato NÃO carrega: identificador de projeto.
    assert "projeto_id" not in despejo


def test_a_sessao_do_fio_nao_atravessa_o_processo_mas_a_proposta_sim(
    url_postgres, esquema_migrado
):
    """A fronteira declarada no ADR 0011, medida — e a saída que a torna não-fatal.

    A sessão de conversa mora em `RepositorioDeSessoesEmMemoria`: ela é de processo, e o
    ADR 0011 diz isso com todas as letras ("no dia de duas réplicas, a sessão precisa de
    armazenamento"). O que **não** estava medido é a consequência: o hospedeiro que
    confirmar pela rota do §A.6 usando uma sessão de OUTRA instância recebe
    `SESSION_NOT_FOUND` — mesmo com a proposta viva no banco.

    Este teste fixa as duas metades, porque só as duas juntas contam a verdade:

    1. a rota do §A.6 **recusa** com a sessão da instância anterior (a fronteira existe);
    2. a rota `/toc/propostas/{id}/decisao` **executa** a mesma proposta de outra instância
       (a fronteira não perde trabalho — há caminho, e ele atravessa o banco).

    Se um dia a sessão passar a ser persistida, o item 1 falha aqui e alguém decide de
    propósito — em vez de a mudança entrar calada.
    """
    primeira = cliente(url_postgres, esquema_migrado)
    projeto_id = projeto_novo(primeira)
    sessao_da_primeira = primeira.post("/aph/sessions", headers=CABECALHO).json()["session_id"]
    proposta = primeira.post(
        "/aph/actions/toc.criar_nos",
        headers=CABECALHO,
        json={"params": {"projeto_id": projeto_id, "nos": [{"titulo": UDE, "tipo": "ude"}]}},
    ).json()["result"].split()[1]

    segunda = cliente(url_postgres, esquema_migrado)
    recusa = segunda.post(
        f"/aph/sessions/{sessao_da_primeira}/proposals/{proposta}",
        headers=CABECALHO,
        json={"approved": True},
    )
    print(f"\n§A.6 com sessão de outra instância: {recusa.status_code} {recusa.json()}")
    assert recusa.status_code == 404
    assert recusa.json()["error"]["code"] == "SESSION_NOT_FOUND"
    assert titulos_no_banco(url_postgres, esquema_migrado, projeto_id) == []

    terceira = cliente(url_postgres, esquema_migrado)
    pela_aplicacao = terceira.post(
        f"/toc/propostas/{proposta}/decisao", json={"aprovado": True}
    )
    assert pela_aplicacao.status_code == 200, pela_aplicacao.text
    assert pela_aplicacao.json()["status"] == "executed", pela_aplicacao.json()
    gravados = titulos_no_banco(url_postgres, esquema_migrado, projeto_id)
    print(f"a MESMA proposta, decidida por /toc/propostas de outra instância → {gravados}")
    assert gravados == [UDE]


def test_sem_capability_de_escrita_a_borda_nem_propoe(url_postgres, esquema_migrado):
    """§B.7.3: a ação mutadora **não existe** para quem só lê — ausência, não recusa visível."""
    c = cliente(url_postgres, esquema_migrado)
    projeto_id = projeto_novo(c)

    resposta = c.post(
        "/aph/actions/toc.criar_nos",
        headers=CABECALHO_SO_LE,
        json={"params": {"projeto_id": projeto_id, "nos": [{"titulo": UDE, "tipo": "ude"}]}},
    )

    print(f"\nsó-leitura na borda federada: {resposta.status_code} {resposta.json()}")
    assert resposta.status_code == 404
    assert resposta.json()["error"]["code"] == "ACTION_NOT_FOUND"
    assert titulos_no_banco(url_postgres, esquema_migrado, projeto_id) == []


# =======================================================================================
# 2 · O fio conversacional (§A.1..A.6) até o estado gravado
# =======================================================================================


def test_o_fio_conversacional_leva_a_proposta_ao_gate_e_a_execucao_ao_banco(
    url_postgres, esquema_migrado
):
    """O caminho que a pessoa percorre na conversa: falar, ver a proposta, confirmar, ver o nó.

    O roteamento é determinístico sobre o catálogo já filtrado por permissão, e a aplicação
    **não inventa argumento**: os parâmetros completos viajam no campo `args` do corpo.
    """
    c = cliente(url_postgres, esquema_migrado)
    projeto_id = projeto_novo(c)
    sessao = c.post("/aph/sessions", headers=CABECALHO).json()["session_id"]

    with c.stream(
        "POST",
        f"/aph/sessions/{sessao}/messages",
        headers=CABECALHO,
        json={
            "text": FRASE_QUE_ROTEIA,
            "args": {"projeto_id": projeto_id, "nos": [{"titulo": UDE, "tipo": "ude"}]},
        },
    ) as resposta:
        assert resposta.status_code == 200
        assert resposta.headers["content-type"].startswith("text/event-stream")
        eventos = eventos_do_fio("".join(resposta.iter_text()))

    tipos = [(e["kind"], e["seq"]) for e in eventos]
    print(f"\neventos do turno: {tipos}")
    assert [s for _, s in tipos] == sorted(s for _, s in tipos), "o seq não é monotônico"
    assert tipos[-1][0] == "done"

    propostas = [e for e in eventos if e["kind"] == "action_proposal"]
    assert len(propostas) == 1, tipos
    carga = propostas[0]["payload"]
    assert carga["action_id"] == "toc.criar_nos"
    assert carga["requires_confirmation"] is True
    assert carga["targets_count"] == 1
    # A conversa NÃO escreveu: a proposta espera o gate.
    assert titulos_no_banco(url_postgres, esquema_migrado, projeto_id) == []

    decisao = c.post(
        f"/aph/sessions/{sessao}/proposals/{carga['proposal_id']}",
        headers=CABECALHO,
        json={"approved": True},
    )
    assert decisao.json()["status"] == "executed", decisao.json()

    gravados = titulos_no_banco(url_postgres, esquema_migrado, projeto_id)
    print(f"fio conversacional → banco: {gravados}")
    assert gravados == [UDE]

    # E o desfecho volta para a conversa, pelo replay (§A.1): a pessoa vê no que deu.
    replay = c.get(
        f"/aph/sessions/{sessao}/events", params={"after": 0}, headers=CABECALHO
    ).json()
    resultados = [e for e in replay if e["kind"] == "action_result"]
    assert resultados, [e["kind"] for e in replay]
    assert resultados[-1]["payload"]["status"] == "executed", resultados[-1]


def test_o_fio_sem_os_argumentos_completos_conversa_e_nao_propoe_nada(
    url_postgres, esquema_migrado
):
    """A aplicação não adivinha `projeto_id`: sem os argumentos, o turno segue como conversa.

    Adivinhar o alvo de uma mutação seria a aplicação decidindo por conta própria em que
    projeto escrever — e o *slot filling* do APH-6.4 está declarado fora de escopo.
    """
    c = cliente(url_postgres, esquema_migrado)
    projeto_id = projeto_novo(c)
    sessao = c.post("/aph/sessions", headers=CABECALHO).json()["session_id"]

    with c.stream(
        "POST",
        f"/aph/sessions/{sessao}/messages",
        headers=CABECALHO,
        json={"text": FRASE_QUE_ROTEIA},
    ) as resposta:
        eventos = eventos_do_fio("".join(resposta.iter_text()))

    tipos = [e["kind"] for e in eventos]
    print(f"\nturno sem args: {tipos}")
    assert "action_proposal" not in tipos, eventos
    assert tipos[-1] == "done"
    assert titulos_no_banco(url_postgres, esquema_migrado, projeto_id) == []


def test_o_replay_do_fio_devolve_o_mesmo_que_o_stream_depois_da_execucao(
    url_postgres, esquema_migrado
):
    """§A.1: `?after=N` reentrega sem perda nem duplicação — inclusive o desfecho da ação."""
    c = cliente(url_postgres, esquema_migrado)
    projeto_id = projeto_novo(c)
    sessao = c.post("/aph/sessions", headers=CABECALHO).json()["session_id"]

    with c.stream(
        "POST",
        f"/aph/sessions/{sessao}/messages",
        headers=CABECALHO,
        json={
            "text": FRASE_QUE_ROTEIA,
            "args": {"projeto_id": projeto_id, "nos": [{"titulo": UDE, "tipo": "ude"}]},
        },
    ) as resposta:
        do_stream = eventos_do_fio("".join(resposta.iter_text()))

    proposta = next(e for e in do_stream if e["kind"] == "action_proposal")["payload"]
    c.post(
        f"/aph/sessions/{sessao}/proposals/{proposta['proposal_id']}",
        headers=CABECALHO,
        json={"approved": True},
    )

    do_replay = c.get(
        f"/aph/sessions/{sessao}/events", params={"after": 0}, headers=CABECALHO
    ).json()
    sequencias = [e["seq"] for e in do_replay]
    print(
        f"\nstream={len(do_stream)} evento(s) · replay={len(do_replay)} evento(s) · "
        f"seq={sequencias}"
    )
    assert sequencias == sorted(sequencias)
    assert len(sequencias) == len(set(sequencias)), "o replay duplicou evento"
    assert do_replay[: len(do_stream)] == do_stream, "o replay divergiu do stream"
