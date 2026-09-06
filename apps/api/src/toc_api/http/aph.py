"""A superfície APH (Aplicação ↔ Harness) — o fio do Anexo A e a borda federada.

Siglas, uma vez neste arquivo: **APH** — Aplicação ↔ Harness · **SSE** — *Server-Sent
Events* · **HTTP** — *HyperText Transfer Protocol* · **JSON** — *JavaScript Object
Notation* · **FSM** — máquina de estados finitos · **UI** — interface de usuário ·
**TTL** — *Time To Live* (tempo de vida).

Os caminhos são os de referência do §A.2 do Anexo A (grau DEVERIA); os **corpos** são
normativos, e é por isso que eles saem de funções do domínio (`Evento.como_json`,
`ErroDoFio.como_corpo_http`) e não de dicionários montados à mão em cada rota.

Três decisões de transporte que valem explicação, porque nenhuma delas é óbvia:

1. **A produção do turno é uma tarefa, não a resposta.** O `POST .../messages` dispara uma
   tarefa que escreve no log da sessão, e a resposta SSE é uma **vista** desse log. É o que
   faz o servidor continuar emitindo quando o cliente cai — o caminho normativo de
   recuperação é o replay (APH-1.3), e ele só reconstrói o que continuou a existir.
2. **O consumidor lê por sondagem curta do log**, em vez de uma fila por conexão. Uma fila
   por conexão é mais elegante e tem um defeito prático: reconexão no meio do turno
   precisaria de sincronização entre a fila e o log, e é exatamente aí que nascem os
   eventos duplicados que o APH-1.3 proíbe. Com o log como fonte única, stream e replay
   **são** a mesma coisa.
3. **Sessão sem identidade existe e não alcança nada.** A suíte de conformidade é
   caixa-preta e não tem grant; um principal anônimo tem inquilino `None` e zero
   capabilities, logo o catálogo composto é vazio e nenhum caso de uso do domínio é
   construível. Ausência é a fronteira (§B.7.3), e não uma recusa que revela o que existe.
"""
from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from typing import Any, AsyncIterator

from fastapi import APIRouter, Header, Request, Response
from fastapi.responses import JSONResponse, StreamingResponse

from ..aplicacao.federacao.acoes import DecidirProposta, ProporAcao
from ..aplicacao.federacao.catalogo import ComporCatalogo
from ..dominio.federacao.catalogo import AcaoDesconhecida
from ..dominio.federacao.esquema import ArgumentosInvalidos, EsquemaNaoSuportado
from ..dominio.federacao.principal import IntrospeccaoInvalida, Principal, principal_anonimo
from ..dominio.federacao.proposta import Origem, TransicaoInvalida
from ..dominio.federacao.snapshot import ContextoInvalido, sanitizar_snapshot
from ..dominio.federacao.traco import AcaoSemTraco
from ..dominio.federacao.wire import ErroDoFio, SessaoDeConversa
from ..infra.federacao.memoria import RegistroDeSessoesDeAplicacao  # noqa: F401  (reexport)

# Intervalo entre eventos do turno. Não é enfeite: um turno instantâneo não exercitaria o
# cancelamento cooperativo (APH-1.4), que só existe enquanto há o que cancelar. 180 ms × 6
# passos ≈ 1,1 s de turno — tempo de um cliente pedir cancelamento e de a suíte de
# conformidade derrubar a conexão no primeiro evento.
INTERVALO_DO_TURNO_S = 0.18
# Sondagem do log pelo consumidor. Curta o bastante para o stream parecer imediato e longa
# o bastante para não virar espera ocupada.
SONDAGEM_S = 0.02


def erro_http(codigo: str, mensagem: str, status: int, detalhes: dict | None = None) -> JSONResponse:
    """§A.2: erro HTTP usa o corpo `{"error": <Erro §A.7>}` — sempre esta função."""
    erro = ErroDoFio(code=codigo, message=mensagem, details=detalhes)
    return JSONResponse(status_code=status, content=erro.como_corpo_http())


def _sse(evento_json: dict[str, Any]) -> str:
    return f"data: {json.dumps(evento_json, ensure_ascii=False)}\n\n"


async def _produzir_turno(
    sessao: SessaoDeConversa,
    passos: list[tuple[str, dict]],
    *,
    intervalo: float,
) -> None:
    """A tarefa que escreve no log. Continua **mesmo se o cliente cair** (APH-1.3)."""
    try:
        for kind, payload in passos:
            await asyncio.sleep(intervalo)
            if sessao.cancelamento_pedido:
                # APH-1.4: cooperativo e nunca silencioso — o `error` fica no log, logo
                # aparece no stream E no replay.
                sessao.cancelar()
                return
            if sessao.turno_terminado:
                return
            sessao.emitir(kind, payload)
    finally:
        # APH-2.1: o stream termina com `done` ou `error`. Este `finally` é o que impede
        # um turno de acabar em silêncio por exceção no meio do caminho.
        if not sessao.turno_terminado:
            sessao.emitir("done", {})


async def _transmitir(sessao: SessaoDeConversa) -> AsyncIterator[str]:
    """A vista do log. Um frame por evento, na ordem do `seq`, sem duplicar."""
    # Comentário SSE: gramática do transporte, ignorada por parser conforme. Serve de
    # abertura imediata do stream para o cliente saber que a conexão vingou.
    yield ": toc-federada — fronteira conversacional APH\n\n"
    enviados = 0
    while True:
        for evento in sessao.replay(enviados):
            enviados = evento.seq
            yield _sse(evento.como_json())
        if sessao.turno_terminado and not sessao.replay(enviados):
            return
        await asyncio.sleep(SONDAGEM_S)


def criar_router_aph(composicao: Any) -> APIRouter:
    """Monta as rotas sobre a composição — um lugar só conhece as quatro camadas."""
    roteador = APIRouter()
    fed = composicao.federacao

    def principal_de(autorizacao: str | None) -> Principal | JSONResponse:
        """Resolve o portador em identidade — **um** mecanismo, duas origens legítimas.

        Sem cabeçalho, a sessão é anônima: existe e não alcança nada (§B.7.3). Com
        portador, o token é procurado primeiro entre as sessões abertas por
        `POST /toc/embarque` (o grant já trocado por identidade) e, depois, no
        `ProvedorDeIdentidade` da composição — que é o adaptador que a borda REST usa e
        que, fora de desenvolvimento, nega tudo. As duas origens desembocam no **mesmo**
        `Principal`, construído pela **mesma** função (`principal_de_introspeccao`): não há
        segundo caminho de nascimento de identidade, que é o que o P2 e o RF-07 proíbem.
        """
        if not autorizacao:
            return principal_anonimo()
        if not autorizacao.lower().startswith("bearer "):
            return erro_http("UNAUTHORIZED", "cabeçalho Authorization fora da forma Bearer", 401)
        token = autorizacao.split(" ", 1)[1].strip()
        principal = fed.sessoes_de_aplicacao.principal(token)
        if principal is None:
            principal = composicao.identidade.identificar(token)
        if principal is None:
            # §B.6.5: uma recusa só, sem motivo. Distinguir "inexistente" de "vencida" é
            # oráculo para quem testa tokens.
            return erro_http(
                # A mensagem é deliberadamente muda quanto ao motivo — nem "não existe",
                # nem "venceu", nem a lista dos dois: §B.6.5 chama a distinção de "oráculo
                # para quem testa tokens", e uma frase que enumera as hipóteses entrega o
                # mesmo oráculo em outra embalagem.
                "SESSAO_EXPIRADA",
                "sessão não reconhecida; recarregue pelo shell",
                401,
            )
        if principal.expirado_em(composicao.relogio.agora()):
            fed.sessoes_de_aplicacao.encerrar(token)
            return erro_http(
                "SESSAO_EXPIRADA", "a identidade venceu; é preciso novo embarque", 401
            )
        return principal

    # -- embarque: o grant vira identidade, uma vez (§B.6) --------------------------
    @roteador.post("/toc/embarque")
    async def embarcar(request: Request) -> Response:
        corpo = await _corpo_json(request)
        if isinstance(corpo, JSONResponse):
            return corpo
        grant = str(corpo.get("token") or "")
        if not grant:
            return erro_http("UNAUTHORIZED", "handshake sem token de embarque", 400)
        try:
            principal = fed.estabelecer_identidade.rodar(grant=grant)
        except IntrospeccaoInvalida as erro:
            codigo = erro.codigo if erro.codigo in {"GRANT_INATIVO", "SESSAO_EXPIRADA"} else "UNAUTHORIZED"
            return erro_http(codigo, "a introspecção não autorizou este embarque", 401)
        except Exception as erro:  # falha fechada: rede, 5xx, credencial recusada
            codigo = getattr(erro, "codigo", "FUNDACAO_INDISPONIVEL")
            status = 502 if codigo == "CREDENCIAL_RECUSADA" else 503
            return erro_http(codigo, "não foi possível validar a identidade agora", status)

        token_de_sessao = fed.identificadores.novo().hex
        fed.sessoes_de_aplicacao.abrir(token_de_sessao, principal)
        return JSONResponse(
            status_code=201,
            content={
                "sessao": token_de_sessao,
                "usuario": {"id": principal.usuario_id, "nome": principal.nome_de_exibicao},
                "tenant_id": principal.inquilino_id,
                "capabilities": [c.valor for c in principal.capabilities],
                "expira_em": principal.expira_em.isoformat() if principal.expira_em else None,
            },
        )

    # -- catálogo (§A.2, já filtrado por permissão) ---------------------------------
    @roteador.get("/aph/catalog")
    async def catalogo(authorization: str | None = Header(default=None)) -> Response:
        principal = principal_de(authorization)
        if isinstance(principal, JSONResponse):
            return principal
        return JSONResponse(content=fed.compor_catalogo.rodar(principal=principal))

    # -- sessões do fio -------------------------------------------------------------
    @roteador.post("/aph/sessions", status_code=201)
    async def criar_sessao(authorization: str | None = Header(default=None)) -> Response:
        principal = principal_de(authorization)
        if isinstance(principal, JSONResponse):
            return principal
        sessao = fed.sessoes.criar(
            inquilino_id=principal.inquilino_id, usuario_id=principal.usuario_id
        )
        return JSONResponse(status_code=201, content={"session_id": sessao.id})

    @roteador.post("/aph/sessions/{sessao_id}/messages")
    async def enviar_mensagem(
        sessao_id: str, request: Request, authorization: str | None = Header(default=None)
    ) -> Response:
        principal = principal_de(authorization)
        if isinstance(principal, JSONResponse):
            return principal
        sessao = fed.sessoes.obter(
            sessao_id, inquilino_id=principal.inquilino_id, usuario_id=principal.usuario_id
        )
        if sessao is None:
            return erro_http("SESSION_NOT_FOUND", f"sessão inexistente: {sessao_id}", 404)

        corpo = await _corpo_json(request)
        if isinstance(corpo, JSONResponse):
            return corpo

        # Sanitização **no servidor**, antes de qualquer uso (APH-3.3). Campo desconhecido
        # é rejeitado aqui e não viaja — o contraexemplo `senha_vazada` do §A.4.
        snapshot = None
        if corpo.get("snapshot") is not None:
            try:
                snapshot = sanitizar_snapshot(corpo["snapshot"], fed.registro_de_telas)
            except ContextoInvalido as erro:
                return erro_http("INVALID_CONTEXT", erro.detalhe, 400)

        em_andamento = fed.turnos.get(sessao_id)
        if em_andamento is not None and not em_andamento.done():
            return erro_http(
                "INVALID_TRANSITION", "já há um turno em andamento nesta sessão", 409
            )

        texto = str(corpo.get("text") or "")
        sessao.abrir_turno()

        passos: list[tuple[str, dict]] = []
        # Roteamento determinístico sobre o catálogo JÁ FILTRADO por permissão: o que o
        # principal não pode nem entra no conjunto de candidatos (APH-4.3).
        acao = fed.catalogo.rotear(texto, principal)
        if acao is not None:
            try:
                resultado = fed.propor_acao.rodar(
                    principal=principal,
                    action_id=acao.action_id,
                    args=_argumentos_do_texto(acao, corpo),
                    origem=Origem.IA,
                    contexto_hash=snapshot.context_hash if snapshot else None,
                )
                passos.extend(resultado.eventos)
            except (AcaoDesconhecida, ArgumentosInvalidos, IntrospeccaoInvalida, AcaoSemTraco):
                # Roteou para uma ação que este principal não pode, ou sem os argumentos
                # completos: o turno segue como conversa. A recusa já deixou traço lá
                # dentro quando havia identidade — nunca há execução silenciosa.
                passos = []
        passos.extend(fed.motor.responder(texto=texto, snapshot=snapshot, principal=principal))

        fed.turnos[sessao_id] = asyncio.create_task(
            _produzir_turno(sessao, passos, intervalo=fed.intervalo_do_turno)
        )
        return StreamingResponse(
            _transmitir(sessao),
            media_type="text/event-stream",
            headers={"cache-control": "no-store", "x-accel-buffering": "no"},
        )

    @roteador.get("/aph/sessions/{sessao_id}/events")
    async def replay(
        sessao_id: str, after: int = 0, authorization: str | None = Header(default=None)
    ) -> Response:
        principal = principal_de(authorization)
        if isinstance(principal, JSONResponse):
            return principal
        sessao = fed.sessoes.obter(
            sessao_id, inquilino_id=principal.inquilino_id, usuario_id=principal.usuario_id
        )
        if sessao is None:
            return erro_http("SESSION_NOT_FOUND", f"sessão inexistente: {sessao_id}", 404)
        return JSONResponse(content=[e.como_json() for e in sessao.replay(after)])

    @roteador.delete("/aph/sessions/{sessao_id}/stream", status_code=204)
    async def cancelar(
        sessao_id: str, authorization: str | None = Header(default=None)
    ) -> Response:
        principal = principal_de(authorization)
        if isinstance(principal, JSONResponse):
            return principal
        sessao = fed.sessoes.obter(
            sessao_id, inquilino_id=principal.inquilino_id, usuario_id=principal.usuario_id
        )
        if sessao is None:
            return erro_http("SESSION_NOT_FOUND", f"sessão inexistente: {sessao_id}", 404)
        sessao.pedir_cancelamento()
        return Response(status_code=204)

    # -- decisão de proposta (§A.6) -------------------------------------------------
    @roteador.post("/aph/sessions/{sessao_id}/proposals/{proposal_id}")
    async def decidir(
        sessao_id: str,
        proposal_id: str,
        request: Request,
        authorization: str | None = Header(default=None),
    ) -> Response:
        principal = principal_de(authorization)
        if isinstance(principal, JSONResponse):
            return principal
        sessao = fed.sessoes.obter(
            sessao_id, inquilino_id=principal.inquilino_id, usuario_id=principal.usuario_id
        )
        if sessao is None:
            return erro_http("SESSION_NOT_FOUND", f"sessão inexistente: {sessao_id}", 404)

        corpo = await _corpo_json(request)
        if isinstance(corpo, JSONResponse):
            return corpo
        # Schema fechado do §A.6: campo fora destes é rejeitado.
        sobrando = sorted(set(corpo) - {"approved", "idempotency_key", "context_hash"})
        if sobrando:
            return erro_http("INVALID_ARGUMENT", f"campos fora do §A.6: {sobrando}", 400)
        if not isinstance(corpo.get("approved"), bool):
            return erro_http("INVALID_ARGUMENT", "`approved` é booleano obrigatório (§A.6)", 400)

        try:
            resultado = fed.decidir_proposta.rodar(
                principal=principal,
                proposal_id=proposal_id,
                aprovado=corpo["approved"],
                contexto_hash=corpo.get("context_hash"),
                idempotency_key=corpo.get("idempotency_key"),
            )
        except AcaoDesconhecida:
            return erro_http("PROPOSAL_NOT_FOUND", "proposta inexistente nesta sessão", 404)
        except IntrospeccaoInvalida:
            return erro_http("UNAUTHORIZED", "esta sessão não decide propostas", 401)
        except TransicaoInvalida as erro:
            _acrescentar_ao_log(sessao, resultado_de_erro(erro))
            return erro_http(erro.codigo, erro.detalhe, erro.http)

        # O desfecho aparece na conversa (RF-21/RI-04): recusa silenciosa é defeito.
        _acrescentar_ao_log(sessao, *resultado.eventos)
        return JSONResponse(
            content={"proposal_id": proposal_id, "status": resultado.proposta.desfecho.status}
        )

    # -- borda de execução federada (ADR 0023 do hospedeiro) ------------------------
    @roteador.post("/aph/actions/{action_id}")
    async def executar_borda(
        action_id: str, request: Request, authorization: str | None = Header(default=None)
    ) -> Response:
        principal = principal_de(authorization)
        if isinstance(principal, JSONResponse):
            return principal
        if principal.anonimo:
            # RF-32, fail-closed: chamada não autenticada não executa nada. A fatia atual
            # do hospedeiro chama **sem credencial** (L-03 da spec 006, medido no ADR 0023
            # dele), e a norma permitiria abrir uma exceção para `risk: read`. Não abrimos:
            # uma leitura sem identidade não teria inquilino, e uma leitura sem inquilino
            # ou vaza ou mente. O limite fica declarado, e é mais estrito que o permitido —
            # não usar uma permissão é conformidade, não lacuna.
            return erro_http(
                "UNAUTHORIZED",
                "a borda federada exige identidade; apresente o grant do embarque",
                401,
            )
        if not fed.limitador.permitir(principal.inquilino_id or "anonimo"):
            return erro_http("RATE_LIMITED", "limite de taxa da borda federada excedido", 429)

        corpo = await _corpo_json(request)
        if isinstance(corpo, JSONResponse):
            return corpo
        params = corpo.get("params")
        if params is None or not isinstance(params, dict):
            return erro_http("INVALID_ARGUMENT", "corpo esperado: {\"params\": {…}}", 400)

        try:
            resultado = fed.propor_acao.rodar(
                principal=principal, action_id=action_id, args=params, origem=Origem.IA
            )
        except AcaoDesconhecida:
            return erro_http("ACTION_NOT_FOUND", "ação indisponível para este principal", 404)
        except (ArgumentosInvalidos, EsquemaNaoSuportado) as erro:
            return erro_http("INVALID_ARGUMENT", str(erro), 400)
        except AcaoSemTraco as erro:
            return erro_http("UNAUTHORIZED", str(erro), 503)

        proposta = resultado.proposta
        if proposta.estado == "awaiting_approval":
            # Verbo mutador nasce proposta, inclusive vindo do hospedeiro (P2). O contrato
            # do ADR 0023 quer `{"result": <string>}`; a string diz que há gate pendente.
            return JSONResponse(
                content={
                    "result": (
                        f"proposta {proposta.proposal_id} criada e aguardando confirmação "
                        f"humana ({proposta.quantidade_de_alvos} alvo(s))"
                    )
                }
            )
        desfecho = proposta.desfecho
        return JSONResponse(content={"result": f"{desfecho.status}: {desfecho.mensagem}"})

    # -- traço auditável (US-06) ----------------------------------------------------
    @roteador.get("/aph/traco")
    async def traco(authorization: str | None = Header(default=None)) -> Response:
        principal = principal_de(authorization)
        if isinstance(principal, JSONResponse):
            return principal
        if principal.anonimo:
            return erro_http("UNAUTHORIZED", "o traço é escopado por inquilino", 401)
        linhas = fed.tracos.listar(principal.inquilino_id or "")
        return JSONResponse(content=[t.como_dicionario() for t in linhas])

    return roteador


def resultado_de_erro(erro: TransicaoInvalida) -> tuple[str, dict]:
    """Traduz a recusa da FSM em evento `error` para a conversa (RI-04)."""
    return ("error", ErroDoFio(code=erro.codigo, message=erro.detalhe).como_payload())


def _acrescentar_ao_log(sessao: SessaoDeConversa, *passos: tuple[str, dict]) -> None:
    """Acrescenta um turno curto ao log — a decisão acontece **entre** turnos.

    O log é somente-acréscimo e o `seq` continua de onde parou; se o turno anterior já
    terminou, abre-se um turno novo para os eventos caberem.

    **Um terminador, não dois** (§A.1: "o stream termina com o evento `done`, ou com
    `error`"). O `done` daqui era incondicional, e quando o evento era `error` — que já é
    terminador — o turno tentava encerrar duas vezes. O domínio recusava a segunda
    (`SessaoEncerrada`, `dominio/federacao/wire.py`), e a recusa subia até a borda: quem
    tinha pedido uma confirmação com a tela desatualizada recebia `DOMAIN_REFUSED` com uma
    mensagem interna, em vez do `PROPOSAL_CONTEXT_STALE` que o §A.7 nomeia. Defeito de
    protocolo E de vazamento de mensagem, do mesmo `done`.

    Por isso o terminador é condicional e os passos entram no MESMO turno: uma decisão é
    um turno, não um turno por evento — emitir um `done` por evento faria o cliente ver a
    conversa acabar várias vezes seguidas.
    """
    if not passos:
        return
    for kind, payload in passos:
        if sessao.turno_terminado:
            sessao.abrir_turno()
        sessao.emitir(kind, payload)
    if not sessao.turno_terminado:
        sessao.emitir("done", {})


def _argumentos_do_texto(acao: Any, corpo: dict[str, Any]) -> dict[str, Any]:
    """Os `args` de uma ação roteada pelo texto.

    A aplicação **não inventa argumento**: o preenchimento estruturado por diálogo (*slot
    filling*, APH-6.4) está declarado fora de escopo na spec 006, e aqui a ação chega com
    os parâmetros completos (no campo `args` do corpo) ou o roteamento é descartado e o
    turno segue como conversa. Adivinhar `projeto_id` seria a aplicação decidindo o alvo
    de uma mutação por conta própria.
    """
    return dict(corpo.get("args") or {})


async def _corpo_json(request: Request) -> dict[str, Any] | JSONResponse:
    try:
        bruto = await request.body()
        corpo = json.loads(bruto or b"{}")
    except ValueError:
        return erro_http("INVALID_CONTEXT", "corpo não é JSON válido", 400)
    if not isinstance(corpo, dict):
        return erro_http("INVALID_CONTEXT", "corpo esperado: objeto JSON", 400)
    return corpo
