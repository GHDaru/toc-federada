"""Duplos das portas da federação — a camada de aplicação testa sem rede e sem banco.

Siglas: **APH** — Aplicação ↔ Harness.

Conformam às portas de `toc_api.dominio.federacao.portas` **estruturalmente**
(`typing.Protocol`), sem herdar nada: se a porta mudar de forma, o teste de conformidade
em `tests/federacao/test_portas_da_federacao.py` acusa.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Iterator
from uuid import UUID, uuid5

from toc_api.dominio.federacao.principal import (
    IntrospeccaoInvalida,
    Principal,
    principal_de_introspeccao,
)
from toc_api.dominio.federacao.proposta import PropostaDeAcao
from toc_api.dominio.federacao.snapshot import SnapshotDeContexto
from toc_api.dominio.federacao.traco import TracoDeExecucao
from toc_api.dominio.federacao.wire import SessaoDeConversa
from toc_api.infra.federacao.memoria import RepositorioDePropostasEmMemoria

AGORA = datetime(2026, 9, 5, 12, 0, tzinfo=timezone.utc)

RESPOSTA_ATIVA = {
    "active": True,
    "user": {"id": "u-horizonte-01", "name": "Facilitadora TOC"},
    "tenant_id": "instituicao-horizonte",
    "capabilities": ["toc:read", "toc:write"],
    "app_id": "toc",
    "expires_at": "2026-09-05T12:30:00Z",
}


class FundacaoIndisponivel(Exception):
    """O que o adaptador real levanta quando a introspecção não responde."""


@dataclass
class IntrospeccaoFalsa:
    """Duplo da porta de introspecção. Guarda o que recebeu — e nunca devolve o grant."""

    resposta: dict[str, Any] = field(default_factory=lambda: dict(RESPOSTA_ATIVA))
    indisponivel: bool = False
    chamadas: list[str] = field(default_factory=list)

    def trocar_grant(self, grant: str) -> Principal:
        self.chamadas.append(grant)
        if self.indisponivel:
            raise FundacaoIndisponivel("introspecção fora do ar")
        return principal_de_introspeccao(self.resposta)


@dataclass
class RepositorioDeSessoesFalso:
    itens: dict[str, tuple[SessaoDeConversa, str | None, str | None]] = field(default_factory=dict)
    contador: int = 0

    def criar(self, *, inquilino_id: str | None, usuario_id: str | None) -> SessaoDeConversa:
        self.contador += 1
        sessao = SessaoDeConversa(id=f"sessao-{self.contador:04d}")
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
            # Sessão de outro principal é `None`, nunca "proibido": distinguir vazaria a
            # existência da conversa alheia.
            return None
        return sessao

    def salvar(self, sessao: SessaoDeConversa) -> None:
        achado = self.itens.get(sessao.id)
        if achado is not None:
            self.itens[sessao.id] = (sessao, achado[1], achado[2])


@dataclass
class RepositorioDePropostasFalso(RepositorioDePropostasEmMemoria):
    """O duplo do teste **é** o duplo de produção, de propósito.

    Enquanto este fake era uma atribuição de dicionário e o adaptador real recusava a
    segunda decisão da mesma leitura, os casos de uso ficavam verdes aqui sobre a corrida
    que o PostgreSQL mostra — e foi assim que oito confirmações simultâneas passaram por
    todo o corpo de testes até um crítico hostil as medir. Herdar em vez de reescrever é o
    que impede o duplo de voltar a ser mais permissivo que o adaptador.
    """


@dataclass
class RepositorioDeTracoFalso:
    linhas: list[TracoDeExecucao] = field(default_factory=list)

    def registrar(self, traco: TracoDeExecucao) -> None:
        self.linhas.append(traco)

    def listar(self, inquilino_id: str, *, usuario_id: str | None = None) -> list[TracoDeExecucao]:
        return [
            t
            for t in self.linhas
            if t.inquilino_id == inquilino_id and (usuario_id is None or t.usuario_id == usuario_id)
        ]

    @property
    def desfechos(self) -> list[str]:
        return [t.desfecho for t in self.linhas]


@dataclass
class ExecutorFalso:
    """Executa alvo a alvo. `falhar_em` diz quais alvos falham — é o lote parcial."""

    falhar_em: set[str] = field(default_factory=set)
    executados: list[tuple[str, str]] = field(default_factory=list)
    recusar_tudo: bool = False

    def executar(self, *, action_id: str, args: dict, principal: Principal) -> tuple[str, str]:
        alvo = str(args.get("__alvo__", ""))
        if self.recusar_tudo or alvo in self.falhar_em:
            return ("failed", f"o alvo {alvo!r} violou uma invariante do domínio")
        self.executados.append((action_id, alvo))
        return ("executed", "")


@dataclass
class MotorFalso:
    """Turno determinístico. Sem provedor de modelo — ADR 0007 (a fundação é quem fala)."""

    passos: list[tuple[str, dict]] = field(
        default_factory=lambda: [
            ("content", {"text": "Olá. "}),
            ("content", {"text": "Sou a fronteira conversacional da TOC Federada."}),
            ("done", {}),
        ]
    )

    def responder(
        self, *, texto: str, snapshot: SnapshotDeContexto | None, principal: Principal
    ) -> Iterator[tuple[str, dict]]:
        yield from self.passos


@dataclass
class IdentificadoresFalsos:
    """Sequência fixa — o teste sabe qual identificador vai sair."""

    contador: int = 0

    def novo(self) -> UUID:
        self.contador += 1
        return uuid5(UUID("00000000-0000-4000-8000-000000000000"), str(self.contador))


class RelogioFixo:
    def __init__(self, instante: datetime = AGORA) -> None:
        self.instante = instante

    def agora(self) -> datetime:
        return self.instante


__all__ = [
    "AGORA",
    "RESPOSTA_ATIVA",
    "ExecutorFalso",
    "FundacaoIndisponivel",
    "IdentificadoresFalsos",
    "IntrospeccaoFalsa",
    "IntrospeccaoInvalida",
    "MotorFalso",
    "RelogioFixo",
    "RepositorioDePropostasFalso",
    "RepositorioDeSessoesFalso",
    "RepositorioDeTracoFalso",
]
