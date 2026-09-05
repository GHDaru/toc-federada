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
CODIGOS_PROPRIOS: dict[str, str] = {
    "SESSION_NOT_FOUND": "sessão inexistente ou de outro principal (§A.2, superfície de sessão)",
    "ACTION_NOT_FOUND": "action_id fora do catálogo composto para este principal (RF-09)",
    "INVALID_ARGUMENTS": "args reprovados pelo input_schema da ação (RF-31)",
    "PROPOSAL_NOT_FOUND": "proposta inexistente nesta sessão",
    "RATE_LIMITED": "limite de taxa da borda federada excedido (RNF-08)",
    "FUNDACAO_INDISPONIVEL": "introspecção fora do ar; falha fechada (spec 003, RF-10)",
    "GRANT_INATIVO": "introspecção respondeu {active:false} (spec 003, RF-09)",
    "CREDENCIAL_RECUSADA": "o hospedeiro respondeu 401 à nossa credencial (spec 003, RF-11)",
    "SESSAO_EXPIRADA": "`expires_at` do principal venceu (spec 003, RF-13)",
    "ADMISSAO_INCOMPLETA": "parâmetro de admissão ausente (§B.4.1; ver contracts/parametros-de-admissao.md)",
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

