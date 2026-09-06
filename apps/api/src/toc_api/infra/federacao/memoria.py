"""Repositórios em memória da federação — o backend de desenvolvimento e de teste.

Siglas, uma vez: **APH** — Aplicação ↔ Harness · **SQL** — *Structured Query Language*.

Mesma regra dos repositórios do núcleo (`infra/persistencia/memoria.py`): **nenhuma leitura
sem inquilino**. O filtro mora aqui de propósito — é assim que o adaptador SQL também tem
de se comportar, e o mesmo teste de contrato roda contra os dois.

O log de conversa vive em memória mesmo quando o resto está no PostgreSQL, e isso é
**decisão declarada**, não esquecimento: o replay do APH-1.3 reconstrói a conversa dentro
do processo que a atende, e a reconexão que o APH-5.6 protege é uma requisição nova no
mesmo processo. O que **não** pode ser volátil é a governança — proposta e traço têm tabela
e migração (`alembic/versions/0004_federacao_proposta_e_traco.py`). Um dia com várias
réplicas, a sessão precisará de armazenamento compartilhado; nesse dia, troca-se o
adaptador, porque a aplicação fala com a porta.
"""
from __future__ import annotations

import threading
import time
from copy import deepcopy
from dataclasses import dataclass, field
from uuid import UUID, uuid4

from ...dominio.federacao.principal import Principal
from ...dominio.federacao.proposta import (
    ChaveDeIdempotenciaReutilizada,
    CorridaDeDecisao,
    PropostaDeAcao,
)
from ...dominio.federacao.traco import TracoDeExecucao
from ...dominio.federacao.wire import SessaoDeConversa

#: O limite da espera por quem venceu a corrida, declarado em vez de suposto:
#: 300 × 20 ms = **6 s**. É o mesmo par de constantes do adaptador SQL, e está aqui para o
#: duplo não ser nem mais rápido nem mais paciente que o banco de verdade.
TENTATIVAS_DE_ESPERA = 300
PAUSA_DA_ESPERA = 0.02
ESPERA_MAXIMA = TENTATIVAS_DE_ESPERA * PAUSA_DA_ESPERA


class IdentificadoresUuid:
    """`uuid4` atrás de porta — o caso de uso não sorteia nada por conta própria."""

    def novo(self) -> UUID:
        return uuid4()


@dataclass
class RepositorioDeSessoesEmMemoria:
    """Sessões de conversa, escopadas pelo par (inquilino, usuário) — `None` para anônimo."""

    itens: dict[str, tuple[SessaoDeConversa, str | None, str | None]] = field(default_factory=dict)

    def criar(self, *, inquilino_id: str | None, usuario_id: str | None) -> SessaoDeConversa:
        sessao = SessaoDeConversa(id=str(uuid4()))
        self.itens[sessao.id] = (sessao, inquilino_id, usuario_id)
        return sessao

    def obter(
        self, sessao_id: str, *, inquilino_id: str | None, usuario_id: str | None
    ) -> SessaoDeConversa | None:
        achado = self.itens.get(sessao_id)
        if achado is None:
            return None
        sessao, inq, usu = achado
        if inq != inquilino_id or usu != usuario_id:
            # Sessão de outro principal responde `None`: distinguir "não existe" de "existe
            # e é de outro" vazaria a existência da conversa alheia.
            return None
        return sessao

    def salvar(self, sessao: SessaoDeConversa) -> None:
        achado = self.itens.get(sessao.id)
        if achado is not None:
            self.itens[sessao.id] = (sessao, achado[1], achado[2])


@dataclass
class RepositorioDePropostasEmMemoria:
    """As propostas em memória — com a MESMA trava do adaptador SQL, e pelo mesmo motivo.

    Enquanto o adaptador real recusava a segunda decisão da mesma leitura
    (`CorridaDeDecisao`) e este duplo aceitasse, os testes de contrato — que rodam quase
    todos sobre ele — ficariam verdes sobre uma corrida que o banco de verdade recusa. É a
    lição já paga no duplo do núcleo (`infra/persistencia/memoria.py`, item 3), aplicada
    aqui antes de custar de novo.

    Três diferenças em relação ao que este duplo era, e as três são o defeito:

    1. **Cópia na fronteira.** `obter` devolvia o próprio objeto guardado, então dois
       leitores recebiam o MESMO agregado e a corrida ficava invisível — o duplo mentia
       para melhor. Agora `obter` devolve `deepcopy`, como o duplo do núcleo.
    2. **A trava.** `salvar` era atribuição de dicionário: gravava por cima do que
       estivesse lá. Agora é condicionada ao `estado_lido`, que é o que lá é
       `UPDATE … WHERE estado = :estado_lido`.
    3. **A chave de idempotência é única por inquilino** (APH-5.3), que lá é um índice
       único parcial. Sem isso a chave volta a ser coluna que ninguém consulta.
    """

    itens: dict[tuple[str, str], PropostaDeAcao] = field(default_factory=dict)
    donos: dict[str, str] = field(default_factory=dict)
    _trava: threading.Lock = field(default_factory=threading.Lock, repr=False)

    def _exigir_estado_lido(self, inquilino_id: str, proposta: PropostaDeAcao) -> None:
        """A trava do duplo — a mesma regra do `WHERE estado =` do adaptador SQL."""
        guardada = self.itens.get((inquilino_id, proposta.proposal_id))
        if guardada is None:
            if proposta.estado_lido:
                # A linha sumiu debaixo de quem a leu. Não há caminho que apague neste
                # duplo, então isto é defeito de chamada, não corrida.
                raise CorridaDeDecisao(
                    proposta.proposal_id,
                    estado_lido=proposta.estado_lido,
                    estado_atual="<inexistente>",
                )
            return
        if not proposta.estado_lido:
            # `estado_lido` vazio quer dizer "nunca gravada": gravar por cima de uma linha
            # que existe é passar por cima de uma decisão que ninguém leu.
            raise CorridaDeDecisao(
                proposta.proposal_id, estado_lido="", estado_atual=guardada.estado
            )
        if proposta.estado_lido != guardada.estado:
            raise CorridaDeDecisao(
                proposta.proposal_id,
                estado_lido=proposta.estado_lido,
                estado_atual=guardada.estado,
            )

    def _exigir_chave_livre(self, inquilino_id: str, proposta: PropostaDeAcao) -> None:
        """APH-5.3: uma chave, uma execução — inclusive quando muda de proposta."""
        if not proposta.idempotency_key:
            return
        for (inq, proposal_id), guardada in self.itens.items():
            if (
                inq == inquilino_id
                and proposal_id != proposta.proposal_id
                and guardada.idempotency_key == proposta.idempotency_key
            ):
                raise ChaveDeIdempotenciaReutilizada(
                    proposta.idempotency_key, proposal_id=proposal_id
                )

    def salvar(self, inquilino_id: str, usuario_id: str, proposta: PropostaDeAcao) -> None:
        with self._trava:
            self._exigir_estado_lido(inquilino_id, proposta)
            self._exigir_chave_livre(inquilino_id, proposta)
            proposta.confirmar_gravacao()
            self.itens[(inquilino_id, proposta.proposal_id)] = deepcopy(proposta)
            self.donos[proposta.proposal_id] = usuario_id

    def obter(self, inquilino_id: str, proposal_id: str) -> PropostaDeAcao | None:
        with self._trava:
            achada = self.itens.get((inquilino_id, proposal_id))
            if achada is None:
                return None
            copia = deepcopy(achada)
        # O agregado sai daqui sabendo de que estado partiu. Sem esta linha `estado` é só
        # um atributo em memória — que foi exatamente o defeito.
        copia.estado_lido = copia.estado
        return copia

    def listar_pendentes(self, inquilino_id: str) -> list[PropostaDeAcao]:
        with self._trava:
            return [
                deepcopy(p)
                for (inq, _), p in self.itens.items()
                if inq == inquilino_id and p.estado == "awaiting_approval"
            ]

    def aguardar_desfecho(
        self, inquilino_id: str, proposal_id: str
    ) -> PropostaDeAcao | None:
        """Espera quem venceu a corrida terminar, e devolve o desfecho dele.

        É o que permite a segunda metade do APH-5.3 — "quantas respostas idênticas forem
        pedidas" — sem reexecutar nada. O limite é declarado (`ESPERA_MAXIMA`) e a espera
        é **fail-open para a borda**: esgotado o tempo, devolve o que houver, e quem chamou
        decide (a decisão fica na aplicação, não aqui).
        """
        for _ in range(TENTATIVAS_DE_ESPERA):
            proposta = self.obter(inquilino_id, proposal_id)
            if proposta is None or proposta.terminal:
                return proposta
            time.sleep(PAUSA_DA_ESPERA)
        return self.obter(inquilino_id, proposal_id)


@dataclass
class RepositorioDeTracoEmMemoria:
    """Somente-acréscimo, como o SQL: não existe método de alterar nem de apagar."""

    linhas: list[TracoDeExecucao] = field(default_factory=list)

    def registrar(self, traco: TracoDeExecucao) -> None:
        self.linhas.append(traco)

    def listar(self, inquilino_id: str, *, usuario_id: str | None = None) -> list[TracoDeExecucao]:
        return [
            t
            for t in self.linhas
            if t.inquilino_id == inquilino_id and (usuario_id is None or t.usuario_id == usuario_id)
        ]


@dataclass
class SessaoDeAplicacao:
    """O principal guardado depois da troca do grant — "guarde o principal, não o token".

    **Não é login próprio** (o P2 proíbe): é o resultado da introspecção da fundação,
    mantido no servidor pelo tempo que a *própria fundação* declarou em `expires_at`. Não
    há senha, não há cadastro e não há renovação por conta própria (RF-13) — vencida, a
    sessão morre e o caminho é novo embarque pelo shell.
    """

    principal: Principal


@dataclass
class RegistroDeSessoesDeAplicacao:
    """As sessões de aplicação abertas. Chave opaca, gerada pelo servidor."""

    itens: dict[str, SessaoDeAplicacao] = field(default_factory=dict)

    def abrir(self, token: str, principal: Principal) -> None:
        self.itens[token] = SessaoDeAplicacao(principal=principal)

    def principal(self, token: str) -> Principal | None:
        sessao = self.itens.get(token)
        return sessao.principal if sessao else None

    def encerrar(self, token: str) -> None:
        self.itens.pop(token, None)
