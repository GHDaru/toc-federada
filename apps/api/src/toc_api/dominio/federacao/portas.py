"""As portas da federação — todo efeito da fronteira sai por aqui (P3).

Siglas, uma vez: **APH** — Aplicação ↔ Harness · **HTTP** — *HyperText Transfer Protocol* ·
**SSE** — *Server-Sent Events*.

São `typing.Protocol`, como as portas do núcleo (`dominio/portas.py`): o adaptador não
herda nada nosso e o duplo do teste conforma pela **forma**. É o padrão lido em `ghdaru`
(`apps/api/src/ghdaru_api/documents/ports/storage.py`), trazido, não copiado.

Uma decisão que vale explicar: a porta de introspecção devolve o **Principal**, não o
dicionário cru da resposta. Se devolvesse o dicionário, a tradução "resposta → identidade"
existiria em cada chamador, e o §B.6.2 ("quem autoriza é a resposta da introspecção")
viraria disciplina em vez de tipo. Traduzir uma vez, no adaptador, é o que faz a regra ser
inescapável.
"""
from __future__ import annotations

from typing import Iterator, Protocol, runtime_checkable
from uuid import UUID

from .principal import Principal
from .proposta import PropostaDeAcao
from .snapshot import SnapshotDeContexto
from .traco import TracoDeExecucao
from .wire import SessaoDeConversa


@runtime_checkable
class PortaDeIntrospeccao(Protocol):
    """`POST {HOST_BASE_URL}/auth/introspect`, servidor a servidor (§B.6).

    O grant entra e **não volta**: o que sai é identidade. Falha de rede ou 5xx levanta
    `FundacaoIndisponivel`; `{active:false}` levanta `IntrospeccaoInvalida` com
    `GRANT_INATIVO`; 401 à nossa credencial levanta `CredencialRecusada`.
    """

    def trocar_grant(self, grant: str) -> Principal: ...


@runtime_checkable
class RepositorioDeSessoes(Protocol):
    """O log de conversa. Escopado por principal: sessão de outro é `None`, não erro."""

    def criar(self, *, inquilino_id: str | None, usuario_id: str | None) -> SessaoDeConversa: ...

    def obter(
        self, sessao_id: str, *, inquilino_id: str | None, usuario_id: str | None
    ) -> SessaoDeConversa | None: ...

    def salvar(self, sessao: SessaoDeConversa) -> None: ...


@runtime_checkable
class RepositorioDePropostas(Protocol):
    """As propostas, com o seu estado da máquina. Toda leitura carrega o inquilino.

    `salvar` recebe o par (inquilino, usuário) explicitamente, e não o lê de dentro do
    agregado, porque a proposta é do **domínio da governança** e o dono é da **fronteira**:
    enfiar o usuário dentro dos `args` para o repositório achá-lo lá seria contrabandear
    identidade por dentro do payload — que é a classe de defeito que o §B.9.4 nomeia.

    **`salvar` é a trava, e por isso é a serialização.** A gravação é condicionada ao
    `estado_lido` do agregado (`UPDATE … WHERE estado = :estado_lido`): quem não partiu do
    estado que a linha tem recebe `CorridaDeDecisao`. É o que faz a transição
    `confirmed → executing` existir **no banco e antes do efeito** — sem isso a máquina de
    estados finitos (FSM) guarda o objeto e não a linha, e oito confirmações simultâneas da
    mesma proposta executam oito vezes.
    """

    def salvar(self, inquilino_id: str, usuario_id: str, proposta: PropostaDeAcao) -> None: ...

    def obter(self, inquilino_id: str, proposal_id: str) -> PropostaDeAcao | None: ...

    def listar_pendentes(self, inquilino_id: str) -> list[PropostaDeAcao]: ...

    def aguardar_desfecho(
        self, inquilino_id: str, proposal_id: str
    ) -> PropostaDeAcao | None: ...


@runtime_checkable
class RepositorioDeTraco(Protocol):
    """Somente-acréscimo. `listar` responde "o que a IA fez neste projeto" (US-06)."""

    def registrar(self, traco: TracoDeExecucao) -> None: ...

    def listar(self, inquilino_id: str, *, usuario_id: str | None = None) -> list[TracoDeExecucao]: ...


@runtime_checkable
class ExecutorDeAcao(Protocol):
    """Quem de fato toca o domínio quando uma proposta é confirmada.

    Existe como porta para a máquina de estados não conhecer os casos de uso do M1/M2 —
    e para o teste da FSM rodar sem repositório de projeto nenhum.
    """

    def executar(
        self, *, action_id: str, args: dict, principal: Principal
    ) -> tuple[str, str]: ...


@runtime_checkable
class MotorDeConversa(Protocol):
    """O produtor do turno.

    **Não é um provedor de modelo** (ADR 0007: nenhum SDK de provedor no produto). É a
    porta pela qual o turno é produzido; o adaptador deste ciclo é determinístico e local,
    e quem fala com modelo é a fundação, pelo catálogo. A porta existe para que o dia em
    que a fundação repassar o fio dela seja troca de adaptador, não reescrita.
    """

    def responder(
        self,
        *,
        texto: str,
        snapshot: SnapshotDeContexto | None,
        principal: Principal,
    ) -> Iterator[tuple[str, dict]]: ...


@runtime_checkable
class GeradorDeIdentificadores(Protocol):
    """`uuid4` é efeito: o caso de uso recebe o gerador e o teste fixa a sequência."""

    def novo(self) -> UUID: ...
