"""O fio do Anexo A como regra de domínio — evento, erro e sessão de conversa.

Siglas, uma vez: **APH** — Aplicação ↔ Harness · **SSE** — *Server-Sent Events* · **JSON** —
*JavaScript Object Notation* · **HTTP** — *HyperText Transfer Protocol* · **UI** — interface
de usuário.

O transporte é da borda (SSE sobre POST vive em `http/aph.py`). O que mora aqui é o que a
borda **não pode inventar**, porque errar qualquer um destes pontos é errar o protocolo:

- **`seq` é atribuído no servidor, antes da emissão** (APH-1.2). A assinatura de `emitir`
  nem aceita `seq` — não há como um cliente sugerir um, e não há como dois caminhos de
  código atribuírem o mesmo.
- **Replay sem perda nem duplicação** (APH-1.3): o log é a fonte, o stream é uma vista
  dele. Por isso a mesma função serializa os dois — o check `replay-integral` da suíte de
  conformidade compara os eventos **completos**, e um campo a mais no stream reprovaria.
- **Terminador obrigatório** (APH-2.1): `done` ou `error`, nunca silêncio. Emitir depois
  do terminador é recusado, porque produziria um replay diferente do que o cliente viu.
- **Cancelamento nunca silencioso** (APH-1.4): cancelar acrescenta um `error` com
  `STREAM_CANCELLED` ao log, e é por isso que ele aparece no replay também.
- **Erro é protocolo** (APH-1.5): código estável em `MAIUSCULAS_COM_SUBLINHADO`, do
  registro mínimo do §A.7 ou dos nossos, **documentados**. Um código não declarado é
  recusado na construção: código inventado é o que quebra o cliente que discrimina por
  código.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Mapping

from ..erros import ErroDeDominio

# Vocabulário fechado do §A.3 — as seis famílias mínimas do APH-2.1 mais `citation`.
KINDS: tuple[str, ...] = (
    "content",
    "thinking",
    "action_proposal",
    "action_result",
    "ui_command",
    "citation",
    "error",
    "done",
)

TERMINADORES: frozenset[str] = frozenset({"done", "error"})

# O registro mínimo do §A.7, na ordem da tabela da norma: cinco ✅ e dois 🧪.
REGISTRO_MINIMO_A7: tuple[str, ...] = (
    "STREAM_CANCELLED",
    "PROVIDER_FAILURE",
    "INVALID_TRANSITION",
    "UNAUTHORIZED",
    "INVALID_CONTEXT",
    "PROPOSAL_EXPIRED",
    "PROPOSAL_CONTEXT_STALE",
)

# Códigos próprios. O §A.7 permite ("PODE adicionar os seus") **desde que documentados** —
# e é isto aqui a documentação, com o porquê de cada um, ao lado do registro mínimo que
# eles estendem. Um código sem linha nesta tabela não é emitido: `ErroDoFio` recusa.
#
# **Este é o registro do serviço inteiro, não só do fio**, e a unificação é o conserto de
# um defeito real: havia uma segunda tabela em `http/erros.py`, e as duas divergiram —
# a borda APH emitia `INVALID_ARGUMENTS` enquanto a borda REST emitia `INVALID_ARGUMENT`
# para a mesma situação, no mesmo serviço. Um cliente que compare o código por igualdade,
# que é o uso que o §A.7 prescreve, trataria um e ignoraria o outro. O §A.2 do Anexo A já
# dizia que os dois lados são o mesmo objeto — "Erros HTTP usam o corpo
# `{"error": <Erro §A.7>}`" —, logo o registro também é um só. A varredura que impede a
# divergência de voltar é `tests/contrato/test_registro_de_codigos_a7.py`.
CODIGOS_PROPRIOS: dict[str, str] = {
    # -- do fio e da fronteira federada ------------------------------------------------
    "SESSION_NOT_FOUND": "sessão inexistente ou de outro principal (§A.2, superfície de sessão)",
    "ACTION_NOT_FOUND": "action_id fora do catálogo composto para este principal (RF-09)",
    "INVALID_ARGUMENT": (
        "valor que nunca poderia entrar: args reprovados pelo input_schema da ação "
        "(RF-31), nome vazio, corpo fora do esquema declarado (400/422). Singular, e a "
        "grafia é a que o cliente web já discrimina (`apps/web/src/api/erros.ts`)"
    ),
    "PROPOSAL_NOT_FOUND": "proposta inexistente nesta sessão",
    "RATE_LIMITED": "limite de taxa da borda federada excedido (RNF-08)",
    "FUNDACAO_INDISPONIVEL": "introspecção fora do ar; falha fechada (spec 003, RF-10)",
    "GRANT_INATIVO": "introspecção respondeu {active:false} (spec 003, RF-09)",
    "CREDENCIAL_RECUSADA": "o hospedeiro respondeu 401 à nossa credencial (spec 003, RF-11)",
    "SESSAO_EXPIRADA": "`expires_at` do principal venceu (spec 003, RF-13)",
    "ADMISSAO_INCOMPLETA": "parâmetro de admissão ausente (§B.4.1; ver contracts/parametros-de-admissao.md)",
    # -- da borda REST (os mesmos códigos, o mesmo envelope §A.7) -----------------------
    "UNAUTHENTICATED": (
        "o pedido não trouxe identidade válida (401). Separado de UNAUTHORIZED porque o "
        "§A.7 registra a confusão entre os dois como ressalva de lastro do laboratório A"
    ),
    "NOT_FOUND": (
        "o recurso não existe PARA ESTE INQUILINO (404). O §A.7 não tem código para isto, "
        "e a fronteira do inquilino responde 404 justamente para não confirmar existência"
    ),
    "INVALID_EDGE": "aresta que viola regra de grafo; `details.regra` diz qual (409, RF-18)",
    "INVALID_CONNECTOR": "conector E que viola a RN-11; `details.regra` diz qual (409)",
    "MUTATION_REFUSED": "operação válida em geral, recusada NESTE estado do agregado (409)",
    "VERSION_CONFLICT": (
        "a escrita partiu de uma versão do agregado que já não é a do banco: outra "
        "pessoa gravou antes (409). `details.versao_lida` é a versão de que a escrita "
        "partiu e `details.versao_atual` é a que o registro tem, e os dois viajam porque "
        "é com eles que o cliente recarrega e refaz sozinho. **Acréscimo declarado**: o "
        "registro mínimo do §A.7 não tem código para perda de atualização — "
        "INVALID_TRANSITION é a máquina de estados da proposta (APH-5.1) e "
        "PROPOSAL_CONTEXT_STALE é a tela que mudou entre propor e confirmar (APH-5.4); "
        "nenhum dos dois nomeia duas escritas concorrentes sobre o MESMO agregado, que é "
        "o que uma ferramenta multiusuário encontra o tempo todo. Usar um deles diria ao "
        "cliente para tratar um caso que não é o dele"
    ),
    "IDEMPOTENCY_KEY_REUSED": (
        "a `idempotency_key` da confirmação já pertence a OUTRA proposta deste inquilino "
        "(409). O APH-5.3 pede deduplicação real — \"a mesma chave produz uma execução e "
        "quantas respostas idênticas forem pedidas\" —, e a unicidade por (inquilino, "
        "chave) é o que a torna verdade. **Acréscimo declarado**: o registro mínimo do "
        "§A.7 não tem código para chave reaproveitada; INVALID_TRANSITION nomeia a FSM da "
        "proposta e diria ao cliente para recarregar a proposta, quando o que ele tem de "
        "fazer é sortear outra chave. `details.idempotency_key` e `details.proposal_id` "
        "dizem qual chave e de quem ela é"
    ),
    "AGGREGATE_ROOT_REQUIRED": (
        "o estado pertence a uma ferramenta e a mutação NÃO veio pela raiz do agregado "
        "dela; `details.ferramenta` diz de quem é o estado e `details.raiz` diz qual é a "
        "porta certa (409). Separado de MUTATION_REFUSED porque a correção do cliente é "
        "outra: não é esperar outro estado, é chamar a rota da ferramenta"
    ),
    "FIXED_TOPOLOGY": (
        "a Nuvem de Conflito tem topologia fixa: 5 entidades e 7 arestas que nascem "
        "juntas e não se criam nem se destroem; `details.regra` diz qual (409, RN-01)"
    ),
    "INVALID_ASSUMPTION": (
        "premissa recusada pelo domínio — vazia, arquivada, desafiada sem justificativa "
        "ou reordenação incompleta; `details.regra` diz qual (409, RF-12/RF-13)"
    ),
    "INVALID_INJECTION": (
        "injeção recusada pelo domínio — sem premissa viva ou já arquivada; "
        "`details.regra` diz qual (409, RN-04)"
    ),
    "INVALID_DERIVATION": (
        "a derivação de nuvem a partir de Efeitos Indesejáveis da Árvore da Realidade "
        "Atual foi recusada; `details.regra` diz qual (409, INT-05)"
    ),
    "INVALID_GENERATION_RESULT": (
        "o resultado da geração assistida não valida contra o esquema versionado e foi "
        "recusado em falha fechada, antes de qualquer efeito (422, RF-22)"
    ),
    # -- M4 · Árvores de Futuro e Implementação (spec 008) -----------------------------
    #
    # Cada um destes nomeia uma recusa cuja CORREÇÃO do lado do cliente é diferente das
    # outras — que é o critério do §A.7 para código próprio. `MUTATION_REFUSED` diria
    # apenas "não neste estado", e o cliente não saberia se recarrega, se muda o alvo ou
    # se auditória o material antes de tentar de novo.
    "INVALID_ROLE": (
        "o papel do nó não permite a operação, ou não pode mudar: objetivo da Árvore de "
        "Pré-Requisitos é único e imutável, injeção que corta ramo tratado não vira "
        "efeito; `details.regra` diz qual (409, RF-02/RF-14)"
    ),
    "INVALID_MIRROR": (
        "o espelho Efeito Indesejável → Efeito Desejável foi recusado — sem cadeia "
        "vinculada, efeito fora da cadeia, ou o mesmo Efeito Indesejável espelhado duas "
        "vezes na mesma árvore; `details.regra` diz qual (409, RN-03)"
    ),
    "INVALID_NEGATIVE_BRANCH": (
        "a transição do ramo negativo foi recusada: `tratado` exige a injeção que corta e "
        "`aceito` exige justificativa e autor; `details.regra` diz qual (409, RN-04)"
    ),
    "INVALID_PAIR": (
        "o par obstáculo ↔ objetivo intermediário foi recusado — papel incompatível ou "
        "obstáculo que já tem resposta; `details.regra` diz qual (409, RF-17)"
    ),
    "INVALID_ELLIPSE": (
        "a elipse de simultaneidade foi recusada — menos de duas dependências, destinos "
        "diferentes ou dependência já agrupada; `details.regra` diz qual (409, RF-19)"
    ),
    "INVALID_STEP": (
        "o passo da Árvore de Transição não existe ou não tem ficha; `details.regra` diz "
        "qual (409, RN-10)"
    ),
    "INVALID_PROMOTION": (
        "a promoção de Efeito Indesejável para Nuvem de Conflito foi recusada: a cadeia "
        "só avança sobre material auditado, e o efeito precisa estar `Validado`; "
        "`details.regra` diz qual (409, RF-37/RN-13). Separado de INVALID_DERIVATION "
        "porque a correção do cliente é outra — não é escolher outro alvo, é **validar** "
        "o efeito antes de promover"
    ),
    "INVALID_SEEDING": (
        "a semeadura da Árvore da Realidade Futura foi recusada: só injeção `escolhida` "
        "semeia, e cada injeção semeia uma vez; `details.regra` diz qual (409, RF-38)"
    ),
    "INVALID_CROSS_REFERENCE": (
        "a referência cruzada foi recusada — criação sem ação nomeada (RN-11), suspensão "
        "sem motivo, ou transição sem mudança; `details.regra` diz qual (409, RF-33)"
    ),
    # -- M6 · Focalização (spec 009) ----------------------------------------------------
    #
    # Cinco códigos e não um: o cliente discrimina por código, e cada uma destas recusas
    # tem uma CORREÇÃO diferente. Colapsá-las em `DOMAIN_REFUSED` mandaria a interface ler
    # a mensagem para saber o que oferecer — que é o que o §A.7 proíbe.
    "INVALID_FOCUSING_STEP": (
        "o passo da jornada de focalização recusou a operação — passo fora de vez, "
        "conclusão sem restrição registrada, sem decisão escrita, com herança pendente, "
        "ou o quinto passo, que não conclui por decisão; `details.regra` diz qual "
        "(409, RN-01, RN-05, RN-07, RF-08/RF-09/RF-10). Separado de INVALID_STEP porque "
        "aquele é o passo da Árvore de Transição, e a correção do cliente é outra"
    ),
    "INVALID_CYCLE": (
        "o ciclo de focalização recusou a operação — ciclo fechado é somente leitura, já "
        "há um ciclo aberto, não há ciclo aberto, ou o recomeço foi pedido fora do quinto "
        "passo; `details.regra` diz qual (409, RN-02, RN-04, RN-07)"
    ),
    "INVALID_CONSTRAINT": (
        "o registro da restrição foi recusado — o ciclo já aponta para uma (mudar o alvo "
        "é recomeçar, não editar), a edição não tem campo, ou não há restrição a editar; "
        "`details.regra` diz qual (409, RN-03, RF-05/RF-07)"
    ),
    "INVALID_TOOL_LINK": (
        "o vínculo com um projeto de ferramenta foi recusado — alvo inexistente para este "
        "inquilino, ferramenta declarada diferente da do projeto, alvo arquivado, vínculo "
        "repetido no passo, ou combinação fora da canônica sem justificativa; "
        "`details.regra` diz qual (409, RN-06, RF-14, RNF-04)"
    ),
    "INVALID_INHERITED_DECISION": (
        "o julgamento da decisão herdada foi recusado — manter e revogar exigem "
        "justificativa, e um veredito não volta a `pendente`; `details.regra` diz qual "
        "(409, RN-05)"
    ),
    "DOMAIN_REFUSED": "recusa de domínio sem tradução mais específica (409)",
    "METHOD_NOT_ALLOWED": "verbo fora dos declarados para a rota (405)",
}

CODIGOS: tuple[str, ...] = REGISTRO_MINIMO_A7 + tuple(sorted(CODIGOS_PROPRIOS))

FORMA_DE_CODIGO = re.compile(r"^[A-Z][A-Z0-9_]*$")


class SessaoEncerrada(ErroDeDominio):
    """Tentativa de emitir depois do terminador."""


@dataclass(frozen=True, slots=True)
class Evento:
    """`{seq, kind, payload}` — o envelope fechado do §A.3."""

    seq: int
    kind: str
    payload: Mapping[str, Any]

    def __post_init__(self) -> None:
        if not isinstance(self.seq, int) or isinstance(self.seq, bool) or self.seq < 1:
            raise ValueError(f"seq {self.seq!r} deve ser inteiro ≥ 1 (APH-1.2)")
        if self.kind not in KINDS:
            raise ValueError(
                f"kind {self.kind!r} fora do vocabulário fechado {list(KINDS)} — o produtor "
                "documenta antes de emitir (APH-2.2)"
            )

    def como_json(self) -> dict[str, Any]:
        """A **única** serialização. Stream e replay usam esta, e é por isso que batem."""
        return {"seq": self.seq, "kind": self.kind, "payload": dict(self.payload)}


@dataclass(frozen=True, slots=True)
class ErroDoFio:
    """`{code, message, details?}` do §A.7 — schema fechado, código estável."""

    code: str
    message: str
    details: Mapping[str, Any] | None = None

    def __post_init__(self) -> None:
        if not FORMA_DE_CODIGO.match(self.code):
            raise ValueError(
                f"código {self.code!r} fora de MAIUSCULAS_COM_SUBLINHADO (§A.7) — "
                "o cliente discrimina por código, nunca por mensagem"
            )
        if self.code not in CODIGOS:
            raise ValueError(
                f"código {self.code!r} não declarado — o §A.7 permite códigos próprios, mas "
                "só documentados: acrescente-o a CODIGOS_PROPRIOS com a situação que ele nomeia"
            )
        if not self.message:
            raise ValueError("erro sem mensagem exibível")

    def como_payload(self) -> dict[str, Any]:
        payload: dict[str, Any] = {"code": self.code, "message": self.message}
        if self.details:
            payload["details"] = dict(self.details)
        return payload

    def como_corpo_http(self) -> dict[str, Any]:
        """§A.2: erros HTTP usam o corpo `{"error": <Erro §A.7>}`."""
        return {"error": self.como_payload()}


@dataclass
class SessaoDeConversa:
    """O log somente-acréscimo de uma sessão. `seq` monotônico **por sessão**.

    A sessão vive além do turno: `abrir_turno` recomeça a emissão sem reiniciar o `seq`,
    porque o APH-1.2 fala de sessão e o replay reconstrói a **conversa**, não o último
    turno.
    """

    id: str
    eventos: list[Evento] = field(default_factory=list)
    _proximo_seq: int = 1
    # Nasce com turno aberto: a sessão recém-criada está pronta para o primeiro turno, e
    # exigir um `abrir_turno` antes do primeiro `emitir` seria cerimônia que só existiria
    # para ser esquecida na borda.
    _turno_terminado: bool = False
    cancelamento_pedido: bool = False

    @property
    def turno_terminado(self) -> bool:
        return self._turno_terminado

    def abrir_turno(self) -> None:
        self._turno_terminado = False
        self.cancelamento_pedido = False

    def emitir(self, kind: str, payload: Mapping[str, Any]) -> Evento:
        """Acrescenta um evento ao log, com o `seq` que o servidor atribui."""
        if self._turno_terminado:
            raise SessaoEncerrada(
                f"sessão {self.id}: o turno já terminou em "
                f"{self.eventos[-1].kind!r}; emitir agora faria o replay divergir do stream"
            )
        evento = Evento(seq=self._proximo_seq, kind=kind, payload=dict(payload))
        self._proximo_seq += 1
        self.eventos.append(evento)
        if kind in TERMINADORES:
            self._turno_terminado = True
        return evento

    def replay(self, apos: int) -> tuple[Evento, ...]:
        """APH-1.3: `?after=N` devolve os eventos com `seq > N`, sem perda nem duplicação."""
        return tuple(e for e in self.eventos if e.seq > apos)

    def pedir_cancelamento(self) -> None:
        """O sinal cooperativo: quem emite verifica no laço (APH-1.4)."""
        self.cancelamento_pedido = True

    def cancelar(self, mensagem: str = "stream cancelado a pedido do cliente") -> Evento | None:
        """Encerra com `error STREAM_CANCELLED`. Turno já terminado: nada a fazer."""
        if self._turno_terminado:
            return None
        erro = ErroDoFio(code="STREAM_CANCELLED", message=mensagem)
        return self.emitir("error", erro.como_payload())

    @property
    def ultimo_seq(self) -> int:
        return self.eventos[-1].seq if self.eventos else 0

    def propostas_pendentes(self, decididas: set[str]) -> tuple[Evento, ...]:
        """RF-45: os gates que o replay tem de reapresentar depois da reconexão."""
        return tuple(
            e
            for e in self.eventos
            if e.kind == "action_proposal"
            and e.payload.get("requires_confirmation")
            and e.payload.get("proposal_id") not in decididas
        )

