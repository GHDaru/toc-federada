"""A proposta de ação e a sua máquina de estados (APH-5.1) — a governança em código.

Siglas, uma vez neste arquivo: **APH** — Aplicação ↔ Harness · **FSM** — máquina de estados
finitos · **TTL** — *Time To Live* (tempo de vida) · **HTTP** — *HyperText Transfer
Protocol* · **UI** — interface de usuário.

Nenhuma ação executa no instante em que o modelo a menciona: ela **nasce proposta**, com
identidade própria, e atravessa esta tabela. Três decisões merecem estar escritas aqui,
porque as três são fáceis de desfazer sem perceber:

1. **A tabela é dado, não `if`.** `TABELA_DE_TRANSICOES` é um dicionário, e `transicionar`
   consulta-o. O teste percorre a tabela inteira **e o complemento dela** — para todo par
   (estado, evento) que não está na tabela, a transição tem de falhar. Uma FSM testada só
   pelo caminho feliz é uma FSM sem a metade que importa.

2. **`stale` não é adotado** (RF-11 da spec 006). O estado existe na FSM de referência do
   padrão e é 🧪 lá; aqui, contexto divergente encerra a proposta em `cancelled` com o
   código `PROPOSAL_CONTEXT_STALE`, que é o desenho do laboratório A registrado no §A.8 do
   Anexo A. O vocabulário do fio aceita `stale` como `action_result.status`; **nós não o
   emitimos**, e há teste que fixa isso.

3. **A origem (`humano` | `ia`) é dado, nunca desvio de fluxo.** É a decisão do ADR 0009 da
   irmã `gestaodeprioridades`, que a norma absorveu no APH-5.9: no instante em que a origem
   virar `if`, as duas telas divergem e a menos testada é a de mais risco. Há um teste que
   compara as duas trajetórias inteiras.

E a invariante que impede o agregado de mentir: **o `status` terminal não afirma mais
sucesso do que os `outcomes` mostram** (APH-5.9(e)). O schema do fio rejeita a combinação;
aqui ela é impossível de construir.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Iterable, Mapping, Sequence

from ..erros import ErroDeDominio

ESTADOS: tuple[str, ...] = (
    "proposed",
    "awaiting_approval",
    "confirmed",
    "executing",
    "executed",
    "failed",
    "cancelled",
    "denied",
    "expired",
)

ESTADOS_TERMINAIS: frozenset[str] = frozenset(
    {"executed", "failed", "cancelled", "denied", "expired"}
)

EVENTOS: tuple[str, ...] = (
    "apresentar",   # proposta mutadora vai ao gate humano
    "confirmar",    # decisão positiva (ou execução direta, quando o risco é `read`)
    "negar",        # decisão negativa — desfecho, com traço
    "expirar",      # TTL vencido
    "invalidar",    # contexto divergente (PROPOSAL_CONTEXT_STALE)
    "executar",     # começou a executar
    "concluir",     # terminou com sucesso (ou com sucesso parcial — ver `Desfecho`)
    "falhar",       # terminou em falha
)

# A tabela. Ler de cima para baixo é ler o ciclo de vida inteiro.
TABELA_DE_TRANSICOES: dict[tuple[str, str], str] = {
    ("proposed", "apresentar"): "awaiting_approval",
    # `read` executa direto (APH-5.2): a proposta existe — para o traço —, mas não para.
    ("proposed", "confirmar"): "confirmed",
    ("proposed", "negar"): "denied",
    ("proposed", "invalidar"): "cancelled",
    ("awaiting_approval", "confirmar"): "confirmed",
    ("awaiting_approval", "negar"): "denied",
    ("awaiting_approval", "expirar"): "expired",
    ("awaiting_approval", "invalidar"): "cancelled",
    ("confirmed", "executar"): "executing",
    ("confirmed", "invalidar"): "cancelled",
    ("executing", "concluir"): "executed",
    ("executing", "falhar"): "failed",
}

STATUS_DE_ALVO: frozenset[str] = frozenset({"executed", "failed", "denied", "skipped"})
STATUS_TERMINAL: frozenset[str] = frozenset(
    {"executed", "failed", "denied", "cancelled", "expired"}
)

# Ordem da taxonomia mínima (RN-01): `confirm` é mais alto que `read`.
ORDEM_DE_RISCO: dict[str, int] = {"read": 0, "confirm": 1}


class Origem(str, Enum):
    """Quem propôs. **Dado**, nunca desvio de fluxo (ADR 0009 da irmã, APH-5.9)."""

    HUMANO = "humano"
    IA = "ia"


class TransicaoInvalida(ErroDeDominio):
    """Transição fora da tabela, proposta vencida ou contexto divergente.

    Carrega `codigo` (do registro do §A.7) e `http`, porque a borda traduz sem adivinhar:
    `INVALID_TRANSITION` → 409, `PROPOSAL_EXPIRED` → 409, `PROPOSAL_CONTEXT_STALE` → 409.
    """

    def __init__(self, codigo: str, detalhe: str, http: int = 409) -> None:
        super().__init__(f"{codigo}: {detalhe}")
        self.codigo = codigo
        self.detalhe = detalhe
        self.http = http


class CorridaDeDecisao(TransicaoInvalida):
    """Duas decisões partiram do MESMO estado da linha e a segunda perdeu a corrida.

    O defeito que este erro existe para tornar audível: a máquina de estados finitos (FSM)
    guardava o **objeto**, não a linha. `obter` reidrata um agregado NOVO a cada chamada, e
    `transicionar` consulta `self.estado`, que é atributo de memória — logo oito
    confirmações simultâneas atravessavam oito agregados, todas legítimas, e executavam
    oito vezes. Medido antes do conserto, contra o PostgreSQL real: **oito confirmações da
    mesma proposta de 30 alvos · oito respostas `200` · 50 nós no banco · 22 títulos
    repetidos · oito linhas de traço para uma proposta só.**

    O código é o `INVALID_TRANSITION` do registro mínimo do §A.7 do Anexo A do Padrão APH
    (Aplicação ↔ Harness), e é de propósito que não seja um código novo: da perspectiva de
    quem perdeu, a proposta **não está mais** em `awaiting_approval`, que é literalmente a
    situação que a norma dá a esse código ("confirmação ou transição fora da máquina de
    estados finitos da proposta").

    `estado_lido` e `estado_atual` viajam no erro pelo mesmo motivo que `versao_lida` e
    `versao_atual` viajam em `ConflitoDeVersao`: o cliente discrimina por código e por
    dado, nunca por mensagem (§A.7).
    """

    def __init__(self, proposal_id: str, *, estado_lido: str, estado_atual: str) -> None:
        super().__init__(
            "INVALID_TRANSITION",
            f"a decisão sobre {proposal_id} partiu do estado {estado_lido!r} e a proposta "
            f"está em {estado_atual!r} — outra decisão chegou antes",
        )
        self.proposal_id = proposal_id
        self.estado_lido = estado_lido
        self.estado_atual = estado_atual


class ChaveDeIdempotenciaReutilizada(TransicaoInvalida):
    """A chave já produziu uma execução — em OUTRA proposta deste mesmo inquilino.

    APH-5.3 pede deduplicação **real**: "a mesma chave produz uma execução e quantas
    respostas idênticas forem pedidas". Enquanto a chave era só uma coluna gravada e nunca
    consultada, ela não deduplicava nada; a unicidade por (inquilino, chave) é o que a
    torna verdade, e esta recusa é o que acontece quando alguém a reaproveita.
    """

    def __init__(self, idempotency_key: str, *, proposal_id: str) -> None:
        super().__init__(
            "IDEMPOTENCY_KEY_REUSED",
            f"a chave de idempotência {idempotency_key!r} já pertence à proposta "
            f"{proposal_id} — uma chave produz uma execução (APH-5.3)",
        )
        self.idempotency_key = idempotency_key
        self.proposal_id = proposal_id


@dataclass(frozen=True, slots=True)
class Desfecho:
    """O resultado terminal, com desfecho por alvo quando é lote (APH-5.9(b)).

    `outcomes` é uma tupla de `(alvo, status, mensagem)`. A invariante do APH-5.9(e) mora
    aqui: com qualquer alvo fora de `executed`, o `status` não pode ser `executed`.
    """

    status: str
    outcomes: tuple[tuple[str, str, str], ...] = ()
    mensagem: str = ""

    def __post_init__(self) -> None:
        if self.status not in STATUS_TERMINAL:
            raise ValueError(
                f"status {self.status!r} fora do vocabulário fechado {sorted(STATUS_TERMINAL)} (§A.3)"
            )
        for alvo, status, _ in self.outcomes:
            if not alvo:
                raise ValueError("outcome sem identificador de alvo")
            if status not in STATUS_DE_ALVO:
                raise ValueError(
                    f"outcome de {alvo!r}: status {status!r} fora de {sorted(STATUS_DE_ALVO)} (§A.3)"
                )
        if self.outcomes and self.status == "executed":
            fora = [a for a, s, _ in self.outcomes if s != "executed"]
            if fora:
                raise ValueError(
                    "APH-5.9(e): o status `executed` afirmaria mais sucesso do que os "
                    f"outcomes mostram — alvos fora de executed: {fora}"
                )

    def como_payload(self) -> dict[str, Any]:
        payload: dict[str, Any] = {"status": self.status}
        if self.mensagem:
            payload["message"] = self.mensagem
        if self.outcomes:
            payload["outcomes"] = [
                ({"target": alvo, "status": status, "message": msg} if msg else {"target": alvo, "status": status})
                for alvo, status, msg in self.outcomes
            ]
        return payload


def risco_do_lote(riscos: Iterable[str]) -> str:
    """APH-5.9(d): a classe de um lote é ao menos a mais alta entre as dos seus itens."""
    maior = "read"
    for risco in riscos:
        if ORDEM_DE_RISCO.get(risco, 0) > ORDEM_DE_RISCO[maior]:
            maior = risco
    return maior


@dataclass
class PropostaDeAcao:
    """O agregado. Mutável de propósito — o estado é o que ele existe para guardar."""

    proposal_id: str
    action_id: str
    args: Mapping[str, Any]
    risk: str
    alvos: tuple[str, ...]
    origem: Origem
    criada_em: datetime
    ttl: timedelta
    contexto_hash: str | None = None
    estado: str = "proposed"
    desfecho: Desfecho | None = None
    decidida_em: datetime | None = None
    idempotency_key: str | None = None
    execucoes: int = 0
    historico: list[tuple[str, str, str]] = field(default_factory=list)
    #: O estado que esta proposta tinha **na linha do banco** quando foi lida. `""` = nunca
    #: foi gravada. É a base da trava, e existe pelo mesmo motivo que `Projeto.versao_lida`:
    #: `estado` sozinho não serve, porque ele já foi mudado em memória pela transição, e na
    #: hora de gravar já não é mais o valor contra o qual o `WHERE` tem de casar. Sem este
    #: campo o adaptador não teria como condicionar a escrita — que é exatamente por que a
    #: coluna `estado` existia, era gravada, e não protegia nada.
    #:
    #: Não entra no construtor nem na comparação porque é estado de SINCRONIA com o
    #: repositório, não estado de negócio: quem o preenche é o adaptador, ao reidratar
    #: (`estado_lido = <coluna>`) e ao confirmar uma gravação (`confirmar_gravacao()`).
    estado_lido: str = field(default="", init=False, repr=False, compare=False)

    @classmethod
    def nova(
        cls,
        *,
        proposal_id: str,
        action_id: str,
        args: Mapping[str, Any],
        risk: str,
        alvos: Sequence[str] = (),
        origem: Origem = Origem.IA,
        criada_em: datetime,
        ttl: timedelta,
        contexto_hash: str | None = None,
    ) -> "PropostaDeAcao":
        """Uma proposta = **um** `action_id` (RN-04). Lote é N alvos, nunca N ações."""
        return cls(
            proposal_id=proposal_id,
            action_id=action_id,
            args=dict(args),
            risk=risk,
            alvos=tuple(alvos),
            origem=origem,
            criada_em=criada_em,
            ttl=ttl,
            contexto_hash=contexto_hash,
        )

    # -- consultas -----------------------------------------------------------------
    @property
    def requer_confirmacao(self) -> bool:
        return self.risk == "confirm"

    @property
    def terminal(self) -> bool:
        return self.estado in ESTADOS_TERMINAIS

    @property
    def quantidade_de_alvos(self) -> int:
        """RF-25: a contagem que a superfície de confirmação mostra **antes** da decisão."""
        return len(self.alvos)

    @property
    def vence_em(self) -> datetime:
        return self.criada_em + self.ttl

    def vencida_em(self, instante: datetime) -> bool:
        return instante > self.vence_em

    def mesma_chave(self, idempotency_key: str | None) -> bool:
        return idempotency_key is not None and self.idempotency_key == idempotency_key

    def decisao_ja_tomada(self, *, aprovado: bool) -> Desfecho | None:
        """RF-16: reenviar a mesma decisão devolve o desfecho original, sem reexecutar."""
        if not self.terminal:
            return None
        if aprovado and self.estado in {"executed", "failed"}:
            return self.desfecho
        if not aprovado and self.estado == "denied":
            return self.desfecho or Desfecho(status="denied")
        return None

    # -- transições ----------------------------------------------------------------
    def transicionar(self, evento: str, *, em: datetime, motivo: str = "") -> str:
        # A única guarda além da tabela, e ela é o APH-5.2 em uma linha: `proposed →
        # confirmed` existe para a ação `read`, que executa direto. Uma ação `confirm`
        # que a usasse teria pulado o gate humano — e a guarda vive AQUI, na transição
        # crua, e não só no método `confirmar`, para que nenhuma rota nova a contorne
        # chamando a FSM por baixo (§B.7.2: a verificação não mora na camada de rota).
        if evento == "confirmar" and self.estado == "proposed" and self.requer_confirmacao:
            raise TransicaoInvalida(
                "INVALID_TRANSITION",
                f"a proposta {self.proposal_id} é de risco {self.risk!r} e só pode ser "
                "confirmada a partir de `awaiting_approval` (APH-5.2)",
            )
        destino = TABELA_DE_TRANSICOES.get((self.estado, evento))
        if destino is None:
            raise TransicaoInvalida(
                "INVALID_TRANSITION",
                f"a proposta {self.proposal_id} está em {self.estado!r} e não admite {evento!r}",
            )
        anterior = self.estado
        self.estado = destino
        self.historico.append((anterior, evento, destino))
        if evento in {"confirmar", "negar"}:
            self.decidida_em = em
        if motivo:
            self.historico.append((destino, "motivo", motivo))
        return destino

    def apresentar(self, *, em: datetime) -> None:
        self.transicionar("apresentar", em=em)

    def confirmar(
        self,
        *,
        em: datetime,
        contexto_hash: str | None = None,
        idempotency_key: str | None = None,
    ) -> None:
        """A decisão positiva — com as duas guardas que a antecedem, nesta ordem.

        Primeiro o TTL (RF-13), depois o contexto (RF-15). A ordem importa: uma proposta
        vencida **e** com contexto mudado é, antes de tudo, vencida — e reportar
        `PROPOSAL_CONTEXT_STALE` mandaria a pessoa refazer a tela por nada.
        """
        if self.estado == "awaiting_approval" and self.vencida_em(em):
            # Vencer é desfecho, não limbo: a proposta muda de estado aqui, e o traço
            # registra a expiração mesmo que ninguém volte a olhar para ela.
            self.transicionar("expirar", em=em)
            self.desfecho = Desfecho(status="expired", mensagem="TTL vencido antes da decisão")
            raise TransicaoInvalida(
                "PROPOSAL_EXPIRED",
                f"a proposta {self.proposal_id} venceu em {self.vence_em.isoformat()}",
            )
        if (
            contexto_hash is not None
            and self.contexto_hash is not None
            and contexto_hash != self.contexto_hash
        ):
            self.transicionar("invalidar", em=em, motivo="context_hash divergente")
            self.desfecho = Desfecho(
                status="cancelled", mensagem="a tela mudou entre a proposta e a confirmação"
            )
            raise TransicaoInvalida(
                "PROPOSAL_CONTEXT_STALE",
                "o snapshot corrente difere do que originou a proposta (APH-5.4)",
            )
        self.transicionar("confirmar", em=em)
        if idempotency_key:
            self.idempotency_key = idempotency_key

    def negar(self, *, em: datetime) -> None:
        self.transicionar("negar", em=em)
        self.desfecho = Desfecho(status="denied", mensagem="recusada por quem decide")

    def expirar(self, *, em: datetime) -> None:
        self.transicionar("expirar", em=em)
        self.desfecho = Desfecho(status="expired", mensagem="TTL vencido antes da decisão")

    def concluir(self, *, desfecho: Desfecho, em: datetime) -> None:
        """Fecha a execução. `executed` e `failed` saem daqui — e só daqui."""
        evento = "concluir" if desfecho.status == "executed" else "falhar"
        self.transicionar(evento, em=em)
        self.desfecho = desfecho
        self.execucoes += 1

    def _forcar_estado_para_teste(self, estado: str) -> None:
        """Só o teste da tabela usa isto — e ele precisa, para exercitar o complemento.

        Deixar o atributo público seria abrir uma porta de fuga da FSM em produção; o
        sublinhado e este parágrafo são o contrato de que ninguém mais a usa.
        """
        if estado not in ESTADOS:  # pragma: no cover - erro de teste, não de produção
            raise ValueError(estado)
        self.estado = estado

    # -- sincronia com o repositório -----------------------------------------------

    def confirmar_gravacao(self) -> None:
        """A gravação passou: o estado em memória passa a ser o estado da linha.

        Chamado pelo adaptador DEPOIS do commit, nunca antes — confirmar uma escrita que
        ainda pode falhar deixaria o agregado achando que está sincronizado com um banco
        que não recebeu nada, e a gravação seguinte partiria de um estado que a linha não
        tem. É a mesma disciplina de `Projeto.confirmar_gravacao`, e a mesma frase, porque
        a regra é a mesma.
        """
        self.estado_lido = self.estado

    # -- projeções para o fio ------------------------------------------------------
    def como_action_proposal(self, *, titulo: str = "", justificativa: str = "") -> dict[str, Any]:
        """O payload do evento `action_proposal` (§A.3)."""
        payload: dict[str, Any] = {
            "proposal_id": self.proposal_id,
            "action_id": self.action_id,
            "risk": self.risk,
            "requires_confirmation": self.requer_confirmacao,
            "args": dict(self.args),
            "origem": self.origem.value,
            "targets_count": self.quantidade_de_alvos,
        }
        if titulo:
            payload["title"] = titulo
        if justificativa:
            payload["rationale"] = justificativa
        if self.contexto_hash:
            payload["context_hash"] = self.contexto_hash
        return payload

    def como_action_result(self) -> dict[str, Any]:
        """O payload do evento `action_result` (§A.3), honesto por construção."""
        desfecho = self.desfecho or Desfecho(status=self._status_do_estado())
        payload = desfecho.como_payload()
        payload["proposal_id"] = self.proposal_id
        payload["action_id"] = self.action_id
        return payload

    def _status_do_estado(self) -> str:
        if self.estado in STATUS_TERMINAL:
            return self.estado
        # Uma proposta não-terminal não tem `action_result`; chegar aqui é defeito de
        # chamada, e `failed` é a resposta fail-closed (nunca `executed`).
        return "failed"
