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

from dataclasses import dataclass, field
from uuid import UUID, uuid4

from ...dominio.federacao.principal import Principal
from ...dominio.federacao.proposta import PropostaDeAcao
from ...dominio.federacao.traco import TracoDeExecucao
from ...dominio.federacao.wire import SessaoDeConversa


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
    itens: dict[tuple[str, str], PropostaDeAcao] = field(default_factory=dict)
    donos: dict[str, str] = field(default_factory=dict)

    def salvar(self, inquilino_id: str, usuario_id: str, proposta: PropostaDeAcao) -> None:
        self.itens[(inquilino_id, proposta.proposal_id)] = proposta
        self.donos[proposta.proposal_id] = usuario_id

    def obter(self, inquilino_id: str, proposal_id: str) -> PropostaDeAcao | None:
        return self.itens.get((inquilino_id, proposal_id))

    def listar_pendentes(self, inquilino_id: str) -> list[PropostaDeAcao]:
        return [
            p
            for (inq, _), p in self.itens.items()
            if inq == inquilino_id and p.estado == "awaiting_approval"
        ]


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
