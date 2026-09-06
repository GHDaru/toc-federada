"""A superfície APH pela borda HTTP — fio, catálogo, proposta, lote, snapshot e traço.

Siglas: **APH** — Aplicação ↔ Harness · **HTTP** — *HyperText Transfer Protocol* ·
**SSE** — *Server-Sent Events* · **JSON** — *JavaScript Object Notation* · **FSM** —
máquina de estados finitos · **UDE** — Efeito Indesejável.

Aqui os requisitos são exercitados **pelo transporte**, que é onde a suíte de conformidade
executável olha. Os eventos emitidos são validados contra os **schemas normativos** do
repositório `GHDaru/protocolos` (RNF-03: golden como portão, não como intenção) — e o teste
imprime quantos eventos examinou, porque verde sem denominador não é evidência (regra R2).
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import jsonschema
import pytest
from fastapi.testclient import TestClient

from toc_api.http.app import criar_app

RAIZ_DO_REPO = Path(__file__).resolve().parents[4]
DIR_SCHEMAS = RAIZ_DO_REPO.parent / "protocolos/padrao/schemas"
TOKEN = "tok-desenvolvimento-facilitadora"
CABECALHO = {"Authorization": f"Bearer {TOKEN}"}

UUID_INEXISTENTE = "11111111-1111-4111-8111-111111111111"

SNAPSHOT_DA_ARA = {
    "screen": {"id": "toc.ara", "route": "/toc/ara", "title": "Árvore da Realidade Atual"},
    "fields": [{"name": "nos_visiveis", "type": "number", "value": 3}],
}


def _validador(nome: str):
    schema = json.loads((DIR_SCHEMAS / nome).read_text("utf-8"))
    registro = {}
    for arquivo in DIR_SCHEMAS.glob("*.schema.json"):
        outro = json.loads(arquivo.read_text("utf-8"))
        registro[arquivo.name] = outro
        if "$id" in outro:
            registro[outro["$id"]] = outro
    resolvedor = jsonschema.RefResolver(base_uri="", referrer=schema, store=registro)
    return jsonschema.Draft202012Validator(schema, resolver=resolvedor)


@pytest.fixture()
def cliente() -> TestClient:
    # Intervalo perto de zero: o teste de contrato não espera o turno de verdade; quem
    # exercita o turno com duração real é a suíte de conformidade, contra o serviço de pé.
    return TestClient(criar_app({"TOC_INTERVALO_DO_TURNO_MS": "1", "TOC_AMBIENTE": "teste"}))


def _eventos(resposta_texto: str) -> list[dict]:
    return [
        json.loads(linha[len("data: ") :])
        for linha in resposta_texto.splitlines()
        if linha.startswith("data: ")
    ]


def _stream(cliente: TestClient, sessao: str, corpo: dict, cabecalho: dict | None = None):
    with cliente.stream(
        "POST", f"/aph/sessions/{sessao}/messages", json=corpo, headers=cabecalho or {}
    ) as resposta:
        texto = "".join(resposta.iter_text())
        return resposta.status_code, resposta.headers.get("content-type", ""), texto


def _abrir(cliente: TestClient, cabecalho: dict | None = None) -> str:
    resposta = cliente.post("/aph/sessions", headers=cabecalho or {})
    assert resposta.status_code == 201, resposta.text
    return resposta.json()["session_id"]


# --------------------------------------------------------------------------------------
# Fio (RF-41..RF-47) — o que a suíte de conformidade também mede, aqui em teste próprio
# --------------------------------------------------------------------------------------


def test_o_turno_chega_por_sse_sobre_post_e_termina_com_done(cliente: TestClient) -> None:
    sessao = _abrir(cliente)

    status, tipo, texto = _stream(cliente, sessao, {"text": "olá, quem é você?"})

    assert status == 200
    assert tipo.startswith("text/event-stream")
    eventos = _eventos(texto)
    assert eventos, "stream sem eventos"
    assert eventos[-1]["kind"] == "done"


def test_o_seq_e_monotonico_e_atribuido_no_servidor(cliente: TestClient) -> None:
    sessao = _abrir(cliente)

    _, _, texto = _stream(cliente, sessao, {"text": "olá"})

    seqs = [e["seq"] for e in _eventos(texto)]
    assert seqs == list(range(1, len(seqs) + 1))


def test_todo_evento_emitido_valida_contra_o_schema_normativo(cliente: TestClient) -> None:
    """RNF-03 / DoD 8: golden contra `protocolos/padrao/schemas/evento.schema.json`."""
    valida = _validador("evento.schema.json")
    sessao = _abrir(cliente, CABECALHO)
    _, _, texto = _stream(cliente, sessao, {"text": "olá", "snapshot": SNAPSHOT_DA_ARA}, CABECALHO)
    eventos = _eventos(texto)

    for evento in eventos:
        valida.validate(evento)

    medida = f"golden do fio: {len(eventos)} evento(s) validados contra evento.schema.json"
    print(medida)
    assert len(eventos) >= 5, medida


def test_replay_devolve_o_mesmo_que_o_stream_sem_perda_nem_duplicacao(cliente: TestClient) -> None:
    sessao = _abrir(cliente)
    _, _, texto = _stream(cliente, sessao, {"text": "olá"})
    do_stream = _eventos(texto)

    completo = cliente.get(f"/aph/sessions/{sessao}/events", params={"after": 0}).json()
    parcial = cliente.get(f"/aph/sessions/{sessao}/events", params={"after": 2}).json()
    vazio = cliente.get(
        f"/aph/sessions/{sessao}/events", params={"after": do_stream[-1]["seq"]}
    ).json()

    assert completo == do_stream
    assert [e["seq"] for e in parcial] == [e["seq"] for e in do_stream if e["seq"] > 2]
    assert vazio == []


def test_sessao_inexistente_devolve_envelope_de_erro_com_codigo_estavel(cliente: TestClient) -> None:
    valida = _validador("erro.schema.json")

    resposta = cliente.post("/aph/sessions/nao-existe/messages", json={"text": "olá"})

    assert resposta.status_code == 404
    corpo = resposta.json()
    valida.validate(corpo["error"])
    assert corpo["error"]["code"] == "SESSION_NOT_FOUND"
    assert corpo["error"]["code"].isupper()


def test_o_cancelamento_encerra_com_stream_cancelled() -> None:
    """APH-1.4 pelo transporte: cancelar **no meio** do turno, que é o único caso real.

    O turno deste teste roda com passo de 120 ms; a mensagem é enviada numa thread e o
    `DELETE` chega enquanto ela ainda está emitindo. Um cancelamento pedido *antes* da
    mensagem não vale: `abrir_turno` limpa o pedido de propósito, senão um cancelamento
    de um turno anterior mataria o turno seguinte — que seria um defeito pior do que o que
    ele resolveria.
    """
    import threading

    cliente = TestClient(criar_app({"TOC_INTERVALO_DO_TURNO_MS": "120", "TOC_AMBIENTE": "teste"}))
    sessao = _abrir(cliente)
    coletado: dict[str, str] = {}

    def enviar() -> None:
        _, _, coletado["texto"] = _stream(cliente, sessao, {"text": "responda lento, por favor"})

    fio = threading.Thread(target=enviar)
    fio.start()
    time.sleep(0.25)
    apagou = cliente.delete(f"/aph/sessions/{sessao}/stream")
    fio.join(timeout=10)

    assert apagou.status_code == 204
    eventos = _eventos(coletado["texto"])
    assert eventos[-1]["kind"] == "error", eventos
    assert eventos[-1]["payload"]["code"] == "STREAM_CANCELLED"
    # e o cancelamento está no replay também — nunca em silêncio
    do_replay = cliente.get(f"/aph/sessions/{sessao}/events", params={"after": 0}).json()
    assert do_replay[-1]["payload"]["code"] == "STREAM_CANCELLED"


# --------------------------------------------------------------------------------------
# Snapshot pela borda (RF-37..RF-40)
# --------------------------------------------------------------------------------------


def test_snapshot_valido_e_aceito_e_o_turno_completa(cliente: TestClient) -> None:
    sessao = _abrir(cliente)

    status, _, texto = _stream(cliente, sessao, {"text": "o que estou vendo?", "snapshot": SNAPSHOT_DA_ARA})

    assert status == 200
    assert _eventos(texto)[-1]["kind"] == "done"


def test_snapshot_com_campo_desconhecido_e_rejeitado_na_borda(cliente: TestClient) -> None:
    """O contraexemplo normativo `senha_vazada` (§A.4) — rejeitado, nunca sanitizado depois."""
    sessao = _abrir(cliente)

    resposta = cliente.post(
        f"/aph/sessions/{sessao}/messages",
        json={"text": "olá", "snapshot": {**SNAPSHOT_DA_ARA, "senha_vazada": "hunter2"}},
    )

    assert resposta.status_code == 400
    assert resposta.json()["error"]["code"] == "INVALID_CONTEXT"
    assert "hunter2" not in resposta.text


def test_o_valor_do_campo_sensivel_nao_atravessa_a_borda(cliente: TestClient) -> None:
    """Camada 2 da sanitização, medida do lado de fora: o valor não volta em lugar nenhum."""
    sessao = _abrir(cliente, CABECALHO)
    com_rascunho = {
        **SNAPSHOT_DA_ARA,
        "fields": [
            *SNAPSHOT_DA_ARA["fields"],
            {"name": "rascunho_de_parecer", "type": "text", "value": "duvido que seja UDE"},
        ],
    }

    _, _, texto = _stream(cliente, sessao, {"text": "olá", "snapshot": com_rascunho}, CABECALHO)

    assert "duvido que seja UDE" not in texto


def test_tela_sensivel_nao_produz_snapshot(cliente: TestClient) -> None:
    """RF-35: `toc.configuracao` tem `ai_actions: []` e não entra em snapshot algum."""
    sessao = _abrir(cliente)

    resposta = cliente.post(
        f"/aph/sessions/{sessao}/messages",
        json={
            "text": "olá",
            "snapshot": {"screen": {"id": "toc.configuracao", "route": "/toc/configuracao"}},
        },
    )

    assert resposta.status_code == 400
    assert resposta.json()["error"]["code"] == "INVALID_CONTEXT"


# --------------------------------------------------------------------------------------
# Catálogo e ausência (RF-05, RF-08, RN-05)
# --------------------------------------------------------------------------------------


def test_o_catalogo_anonimo_e_vazio_e_o_identificado_tem_as_dezesseis_acoes(cliente: TestClient) -> None:
    anonimo = cliente.get("/aph/catalog").json()
    identificado = cliente.get("/aph/catalog", headers=CABECALHO).json()

    assert anonimo == []
    assert len(identificado) == 16
    assert {a["action_id"] for a in identificado} >= {"toc.criar_nos", "toc.listar_projetos"}


def test_o_catalogo_servido_valida_contra_o_schema_de_acao_de_catalogo(cliente: TestClient) -> None:
    """RNF-03: as entradas do catálogo são golden contra `acao-catalogo.schema.json` (§A.5)."""
    valida = _validador("acao-catalogo.schema.json")

    acoes = cliente.get("/aph/catalog", headers=CABECALHO).json()

    for acao in acoes:
        valida.validate(acao)
    medida = f"golden do catálogo: {len(acoes)} ação(ões) validadas contra acao-catalogo.schema.json"
    print(medida)
    assert len(acoes) == 16, medida


def test_token_desconhecido_e_recusado_sem_dizer_o_motivo(cliente: TestClient) -> None:
    resposta = cliente.get("/aph/catalog", headers={"Authorization": "Bearer nao-existe"})

    assert resposta.status_code == 401
    texto = resposta.text.lower()
    for oraculo in ("expirado", "consumido", "inexistente"):
        assert oraculo not in texto


# --------------------------------------------------------------------------------------
# Borda de execução federada (RF-30..RF-33)
# --------------------------------------------------------------------------------------


def test_a_borda_federada_recusa_chamada_sem_identidade(cliente: TestClient) -> None:
    """RF-32: fail-closed. A recusa vale para ação mutadora **e** de leitura."""
    for action_id in ("toc.criar_nos", "toc.listar_projetos"):
        resposta = cliente.post(f"/aph/actions/{action_id}", json={"params": {}})
        assert resposta.status_code == 401, action_id
        assert resposta.json()["error"]["code"] == "UNAUTHORIZED"


def test_a_borda_federada_responde_no_contrato_do_adr_0023(cliente: TestClient) -> None:
    """`{"params": …}` entra, `{"result": "<string>"}` sai (ADR 0023 do hospedeiro)."""
    resposta = cliente.post("/aph/actions/toc.listar_projetos", json={"params": {}}, headers=CABECALHO)

    assert resposta.status_code == 200
    corpo = resposta.json()
    assert set(corpo) == {"result"}
    assert isinstance(corpo["result"], str)


def test_a_borda_federada_valida_params_contra_o_input_schema(cliente: TestClient) -> None:
    """RF-31: o hospedeiro declara que **não** valida; quem valida somos nós."""
    resposta = cliente.post(
        "/aph/actions/toc.listar_projetos",
        json={"params": {"campo_inventado": 1}},
        headers=CABECALHO,
    )

    assert resposta.status_code == 400
    assert resposta.json()["error"]["code"] == "INVALID_ARGUMENT"


def test_verbo_mutador_pela_borda_federada_nasce_proposta_e_nao_executa(cliente: TestClient) -> None:
    """P2: mutação vinda do hospedeiro atravessa a mesma FSM — sem atalho."""
    resposta = cliente.post(
        "/aph/actions/toc.criar_nos",
        json={
            "params": {
                "projeto_id": UUID_INEXISTENTE,
                "nos": [{"titulo": "Entregas atrasam", "tipo": "ude"}],
            }
        },
        headers=CABECALHO,
    )

    assert resposta.status_code == 200
    assert "aguardando confirmação humana" in resposta.json()["result"]


def test_acao_fora_do_catalogo_e_desconhecida_na_borda(cliente: TestClient) -> None:
    resposta = cliente.post("/aph/actions/toc.apagar_tudo", json={"params": {}}, headers=CABECALHO)

    assert resposta.status_code == 404
    assert resposta.json()["error"]["code"] == "ACTION_NOT_FOUND"


# --------------------------------------------------------------------------------------
# Decisão de proposta pela borda (§A.6) e traço (US-06)
# --------------------------------------------------------------------------------------


def _propor_lote(cliente: TestClient, alvos: int = 8) -> str:
    resposta = cliente.post(
        "/aph/actions/toc.criar_nos",
        json={
            "params": {
                "projeto_id": UUID_INEXISTENTE,
                "nos": [{"titulo": f"UDE {i}", "tipo": "ude"} for i in range(1, alvos + 1)],
            }
        },
        headers=CABECALHO,
    )
    assert resposta.status_code == 200, resposta.text
    return resposta.json()["result"].split()[1]


def test_o_corpo_da_decisao_segue_o_schema_fechado_do_a6(cliente: TestClient) -> None:
    valida = _validador("confirmacao.schema.json")
    sessao = _abrir(cliente, CABECALHO)
    proposta = _propor_lote(cliente, 1)

    valida.validate({"approved": True})
    resposta = cliente.post(
        f"/aph/sessions/{sessao}/proposals/{proposta}",
        json={"approved": True, "campo_invadido": 1},
        headers=CABECALHO,
    )

    assert resposta.status_code == 400
    assert resposta.json()["error"]["code"] == "INVALID_ARGUMENT"


def test_decidir_sem_approved_e_recusado(cliente: TestClient) -> None:
    sessao = _abrir(cliente, CABECALHO)
    proposta = _propor_lote(cliente, 1)

    resposta = cliente.post(
        f"/aph/sessions/{sessao}/proposals/{proposta}", json={}, headers=CABECALHO
    )

    assert resposta.status_code == 400


def test_negar_encerra_em_denied_e_o_desfecho_aparece_na_conversa(cliente: TestClient) -> None:
    sessao = _abrir(cliente, CABECALHO)
    proposta = _propor_lote(cliente, 3)

    resposta = cliente.post(
        f"/aph/sessions/{sessao}/proposals/{proposta}", json={"approved": False}, headers=CABECALHO
    )

    assert resposta.status_code == 200
    assert resposta.json() == {"proposal_id": proposta, "status": "denied"}
    eventos = cliente.get(
        f"/aph/sessions/{sessao}/events", params={"after": 0}, headers=CABECALHO
    ).json()
    resultados = [e for e in eventos if e["kind"] == "action_result"]
    assert resultados and resultados[-1]["payload"]["status"] == "denied"


def test_lote_com_falha_em_todos_os_alvos_nao_diz_executed(cliente: TestClient) -> None:
    """O projeto sintético não existe, então os oito alvos falham — e o `status` não mente.

    É o mesmo invariante do fluxo 6.4 da spec exercitado pela borda: com qualquer alvo
    fora de `executed`, o terminal não é `executed` (APH-5.9(e)).
    """
    valida = _validador("evento.schema.json")
    sessao = _abrir(cliente, CABECALHO)
    proposta = _propor_lote(cliente, 8)

    resposta = cliente.post(
        f"/aph/sessions/{sessao}/proposals/{proposta}", json={"approved": True}, headers=CABECALHO
    )

    assert resposta.json()["status"] == "failed"
    eventos = cliente.get(
        f"/aph/sessions/{sessao}/events", params={"after": 0}, headers=CABECALHO
    ).json()
    resultado = [e for e in eventos if e["kind"] == "action_result"][-1]
    valida.validate(resultado)
    assert len(resultado["payload"]["outcomes"]) == 8
    assert resultado["payload"]["status"] != "executed"


def test_confirmar_duas_vezes_devolve_o_mesmo_desfecho(cliente: TestClient) -> None:
    sessao = _abrir(cliente, CABECALHO)
    proposta = _propor_lote(cliente, 1)

    primeira = cliente.post(
        f"/aph/sessions/{sessao}/proposals/{proposta}", json={"approved": True}, headers=CABECALHO
    ).json()
    segunda = cliente.post(
        f"/aph/sessions/{sessao}/proposals/{proposta}", json={"approved": True}, headers=CABECALHO
    ).json()

    assert primeira == segunda


def test_decidir_proposta_inexistente_devolve_codigo_proprio(cliente: TestClient) -> None:
    sessao = _abrir(cliente, CABECALHO)

    resposta = cliente.post(
        f"/aph/sessions/{sessao}/proposals/nao-existe", json={"approved": True}, headers=CABECALHO
    )

    assert resposta.status_code == 404
    assert resposta.json()["error"]["code"] == "PROPOSAL_NOT_FOUND"


def test_o_traco_responde_o_que_a_ia_fez_inclusive_o_que_nao_executou(cliente: TestClient) -> None:
    """US-06 pela borda: execuções e recusas, todas visíveis, escopadas por inquilino."""
    sessao = _abrir(cliente, CABECALHO)
    negada = _propor_lote(cliente, 2)
    cliente.post(
        f"/aph/sessions/{sessao}/proposals/{negada}", json={"approved": False}, headers=CABECALHO
    )
    cliente.post("/aph/actions/toc.listar_projetos", json={"params": {}}, headers=CABECALHO)

    linhas = cliente.get("/aph/traco", headers=CABECALHO).json()

    desfechos = [linha["desfecho"] for linha in linhas]
    assert "denied" in desfechos and "executed" in desfechos
    assert cliente.get("/aph/traco").status_code == 401


def test_o_traco_nunca_carrega_o_enunciado_do_no(cliente: TestClient) -> None:
    """ADR 0006 + RNF-10: o traço carrega identificador e desfecho, nunca texto de pessoa."""
    sessao = _abrir(cliente, CABECALHO)
    proposta = _propor_lote(cliente, 1)
    cliente.post(
        f"/aph/sessions/{sessao}/proposals/{proposta}", json={"approved": True}, headers=CABECALHO
    )

    corpo = cliente.get("/aph/traco", headers=CABECALHO).text

    assert "UDE 1" in corpo, "o alvo do lote aparece por identificador, que é o vocabulário da ação"
    assert "projeto_id" not in corpo


# --------------------------------------------------------------------------------------
# Terminador do fio na decisão fora do turno (§A.1) — defeito achado por revisão
# independente que executou. O §A.1 do Anexo A diz, palavra por palavra: "O stream termina
# com o evento `done`, ou com `error`". São dois terminadores possíveis, **um por turno**;
# emitir `error` e depois `done` é encerrar duas vezes, e o replay que o cliente reconstrói
# passa a ter um evento que o stream nunca teve.
# --------------------------------------------------------------------------------------


def _propor_com_snapshot(cliente: TestClient, sessao: str) -> tuple[str, str]:
    """Propõe pelo fio, COM snapshot — é o snapshot que dá `context_hash` à proposta.

    Devolve `(proposal_id, context_hash)`. A borda federada (`/aph/actions/...`) não serve
    aqui porque ela propõe sem contexto, e sem `context_hash` na proposta a guarda do
    APH-5.4 nunca dispara.
    """
    _, _, texto = _stream(
        cliente,
        sessao,
        {
            "text": "criar no ude",
            "args": {
                "projeto_id": UUID_INEXISTENTE,
                "nos": [{"titulo": "Entregas atrasam", "tipo": "ude"}],
            },
            "snapshot": SNAPSHOT_DA_ARA,
        },
        CABECALHO,
    )
    propostas = [e for e in _eventos(texto) if e["kind"] == "action_proposal"]
    assert propostas, f"a mensagem não gerou proposta: {texto[:400]}"
    payload = propostas[-1]["payload"]
    assert payload.get("context_hash"), "proposta sem context_hash: a guarda do APH-5.4 não seria exercitada"
    return payload["proposal_id"], payload["context_hash"]


def test_decisao_com_contexto_divergente_devolve_o_codigo_do_a7(cliente: TestClient) -> None:
    """APH-5.4: a tela mudou entre proposta e confirmação → `PROPOSAL_CONTEXT_STALE`.

    O código é o do registro do §A.7, porque **o cliente discrimina por código**. Traduzir
    a recusa em `DOMAIN_REFUSED` apagaria, do lado de quem chama, a diferença entre "refaça
    a tela" e "o servidor recusou por outra coisa qualquer".
    """
    valida = _validador("erro.schema.json")
    sessao = _abrir(cliente, CABECALHO)
    proposta, hash_original = _propor_com_snapshot(cliente, sessao)

    resposta = cliente.post(
        f"/aph/sessions/{sessao}/proposals/{proposta}",
        json={"approved": True, "context_hash": "0" * len(hash_original)},
        headers=CABECALHO,
    )

    assert resposta.status_code == 409, resposta.text
    erro = resposta.json()["error"]
    valida.validate(erro)
    assert erro["code"] == "PROPOSAL_CONTEXT_STALE", erro


def test_o_error_da_recusa_encerra_o_turno_sozinho_sem_done_atras(cliente: TestClient) -> None:
    """§A.1: um terminador por turno. `error` encerra — nada pode vir depois dele.

    Este é o teste que reproduz o defeito: o `done` incondicional depois do evento fazia o
    turno terminar duas vezes. O teste imprime quantos eventos examinou (regra R2).
    """
    valida = _validador("evento.schema.json")
    sessao = _abrir(cliente, CABECALHO)
    proposta, hash_original = _propor_com_snapshot(cliente, sessao)

    cliente.post(
        f"/aph/sessions/{sessao}/proposals/{proposta}",
        json={"approved": True, "context_hash": "0" * len(hash_original)},
        headers=CABECALHO,
    )
    eventos = cliente.get(
        f"/aph/sessions/{sessao}/events", params={"after": 0}, headers=CABECALHO
    ).json()

    for evento in eventos:
        valida.validate(evento)
    recusas = [i for i, e in enumerate(eventos) if e["kind"] == "error"]
    assert recusas, f"a recusa não chegou à conversa: {[e['kind'] for e in eventos]}"
    for posicao in recusas:
        depois = [e["kind"] for e in eventos[posicao + 1 :]]
        assert "done" not in depois, (
            "`done` depois de `error` no mesmo turno: o §A.1 tem dois terminadores "
            f"possíveis e um só por turno — {[e['kind'] for e in eventos]}"
        )
    medida = f"terminador: {len(eventos)} evento(s) do log examinados, {len(recusas)} `error`"
    print(medida)
    assert eventos[-1]["kind"] == "error", medida


def test_a_decisao_acrescenta_um_terminador_so_ao_log(cliente: TestClient) -> None:
    """Uma decisão é um turno: os eventos que ela produz terminam uma vez, não uma por evento."""
    sessao = _abrir(cliente, CABECALHO)
    proposta = _propor_lote(cliente, 2)
    antes = cliente.get(
        f"/aph/sessions/{sessao}/events", params={"after": 0}, headers=CABECALHO
    ).json()

    cliente.post(
        f"/aph/sessions/{sessao}/proposals/{proposta}", json={"approved": False}, headers=CABECALHO
    )

    depois = cliente.get(
        f"/aph/sessions/{sessao}/events", params={"after": len(antes)}, headers=CABECALHO
    ).json()
    terminadores = [e["kind"] for e in depois if e["kind"] in {"done", "error"}]
    assert len(terminadores) == 1, [e["kind"] for e in depois]


def test_acrescentar_ao_log_nao_tenta_um_segundo_terminador() -> None:
    """A reprodução direta, na função onde o defeito mora (`http/aph.py`).

    `_acrescentar_ao_log` emitia `done` **incondicionalmente** depois do evento. Quando o
    evento é `error` — que já é terminador (§A.1) —, o `done` é uma segunda tentativa de
    encerrar o mesmo turno. O domínio recusa (`SessaoEncerrada`), e é essa recusa que
    subia até a borda e virava `DOMAIN_REFUSED` no lugar do código do §A.7.
    """
    from toc_api.dominio.federacao.wire import ErroDoFio, SessaoDeConversa
    from toc_api.http.aph import _acrescentar_ao_log

    sessao = SessaoDeConversa(id="sessao-de-teste")
    recusa = ErroDoFio(code="PROPOSAL_EXPIRED", message="venceu antes da decisão")

    _acrescentar_ao_log(sessao, ("error", recusa.como_payload()))

    kinds = [e.kind for e in sessao.eventos]
    assert kinds == ["error"], f"§A.1: um terminador por turno, veio {kinds}"
    assert sessao.turno_terminado
