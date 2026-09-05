"""Os repositórios SQL da governança — proposta e traço no PostgreSQL de verdade.

Siglas, uma vez: **APH** — Aplicação ↔ Harness · **SQL** — *Structured Query Language* ·
**FSM** — máquina de estados finitos · **JSON** — *JavaScript Object Notation*.

Mesma disciplina do `repositorio_projetos.py` do núcleo: **SQLAlchemy Core**, tradução
linha ↔ agregado à mão, num arquivo só. Um modelo de mapeamento objeto-relacional criaria
um segundo lugar onde a regra mora, e a regra da FSM já mora no domínio.

**Nenhuma leitura sem inquilino**: o `tenant_id` é o primeiro parâmetro posicional de toda
consulta, sem valor padrão. É o mesmo invariante do M1, e vale aqui pelo motivo mais forte:
a proposta de outro inquilino, se vazasse, seria uma mutação alheia esperando confirmação.

O traço é **somente-acréscimo**: este arquivo não tem `UPDATE` nem `DELETE` sobre
`traco_de_execucao`, e a ausência é o requisito (APH-5.5). O que aconteceu não se reescreve.
"""
from __future__ import annotations

from typing import Any
from uuid import uuid4

from sqlalchemy import insert, select
from sqlalchemy.dialects.postgresql import insert as insert_pg

from ...dominio.federacao.proposta import Desfecho, Origem, PropostaDeAcao
from ...dominio.federacao.traco import TracoDeExecucao
from ..persistencia.tabelas import proposta_de_acao, traco_de_execucao


def _outcomes_para_json(outcomes: tuple[tuple[str, str, str], ...]) -> list[dict[str, str]]:
    return [{"target": alvo, "status": status, "message": msg} for alvo, status, msg in outcomes]


def _outcomes_do_json(bruto: Any) -> tuple[tuple[str, str, str], ...]:
    if not isinstance(bruto, list):
        return ()
    return tuple(
        (str(item.get("target", "")), str(item.get("status", "")), str(item.get("message", "")))
        for item in bruto
        if isinstance(item, dict)
    )


class RepositorioDePropostasSQL:
    """Implementa `RepositorioDePropostas`. `salvar` é inserção-ou-atualização por chave."""

    def __init__(self, fabrica_de_sessao) -> None:
        self._sessao = fabrica_de_sessao

    def salvar(self, inquilino_id: str, usuario_id: str, proposta: PropostaDeAcao) -> None:
        desfecho = proposta.desfecho
        valores = {
            "proposal_id": proposta.proposal_id,
            "tenant_id": inquilino_id,
            "usuario_id": usuario_id,
            "action_id": proposta.action_id,
            "risk": proposta.risk,
            "origem": proposta.origem.value,
            "estado": proposta.estado,
            "args": dict(proposta.args),
            "alvos": list(proposta.alvos),
            "contexto_hash": proposta.contexto_hash,
            "criada_em": proposta.criada_em,
            "vence_em": proposta.vence_em,
            "decidida_em": proposta.decidida_em,
            "idempotency_key": proposta.idempotency_key,
            "execucoes": proposta.execucoes,
            "desfecho_status": desfecho.status if desfecho else None,
            "desfecho_mensagem": desfecho.mensagem if desfecho else "",
            "outcomes": _outcomes_para_json(desfecho.outcomes) if desfecho else [],
        }
        atualizaveis = {
            k: valores[k]
            for k in (
                "estado",
                "decidida_em",
                "idempotency_key",
                "execucoes",
                "desfecho_status",
                "desfecho_mensagem",
                "outcomes",
            )
        }
        with self._sessao() as sessao:
            sessao.execute(
                insert_pg(proposta_de_acao)
                .values(**valores)
                .on_conflict_do_update(index_elements=["proposal_id"], set_=atualizaveis)
            )
            sessao.commit()

    def obter(self, inquilino_id: str, proposal_id: str) -> PropostaDeAcao | None:
        with self._sessao() as sessao:
            linha = sessao.execute(
                select(proposta_de_acao).where(
                    proposta_de_acao.c.tenant_id == inquilino_id,
                    proposta_de_acao.c.proposal_id == proposal_id,
                )
            ).mappings().first()
        return self._reidratar(linha) if linha else None

    def listar_pendentes(self, inquilino_id: str) -> list[PropostaDeAcao]:
        with self._sessao() as sessao:
            linhas = sessao.execute(
                select(proposta_de_acao).where(
                    proposta_de_acao.c.tenant_id == inquilino_id,
                    proposta_de_acao.c.estado == "awaiting_approval",
                )
            ).mappings().all()
        return [self._reidratar(linha) for linha in linhas]

    @staticmethod
    def _reidratar(linha) -> PropostaDeAcao:
        proposta = PropostaDeAcao(
            proposal_id=linha["proposal_id"],
            action_id=linha["action_id"],
            args=dict(linha["args"] or {}),
            risk=linha["risk"],
            alvos=tuple(linha["alvos"] or ()),
            origem=Origem(linha["origem"]),
            criada_em=linha["criada_em"],
            ttl=linha["vence_em"] - linha["criada_em"],
            contexto_hash=linha["contexto_hash"],
            estado=linha["estado"],
            decidida_em=linha["decidida_em"],
            idempotency_key=linha["idempotency_key"],
            execucoes=linha["execucoes"],
        )
        if linha["desfecho_status"]:
            proposta.desfecho = Desfecho(
                status=linha["desfecho_status"],
                outcomes=_outcomes_do_json(linha["outcomes"]),
                mensagem=linha["desfecho_mensagem"] or "",
            )
        return proposta


class RepositorioDeTracoSQL:
    """Implementa `RepositorioDeTraco`. **Só insere e lê** — a ausência é o requisito."""

    def __init__(self, fabrica_de_sessao) -> None:
        self._sessao = fabrica_de_sessao

    def registrar(self, traco: TracoDeExecucao) -> None:
        with self._sessao() as sessao:
            sessao.execute(
                insert(traco_de_execucao).values(
                    id=uuid4(),
                    proposal_id=traco.proposal_id,
                    action_id=traco.action_id,
                    desfecho=traco.desfecho,
                    tenant_id=traco.inquilino_id,
                    usuario_id=traco.usuario_id,
                    origem=traco.origem.value,
                    instante=traco.instante,
                    trace_id=traco.trace_id,
                    motivo=traco.motivo,
                    outcomes=_outcomes_para_json(traco.outcomes),
                )
            )
            sessao.commit()

    def listar(self, inquilino_id: str, *, usuario_id: str | None = None) -> list[TracoDeExecucao]:
        consulta = select(traco_de_execucao).where(traco_de_execucao.c.tenant_id == inquilino_id)
        if usuario_id is not None:
            consulta = consulta.where(traco_de_execucao.c.usuario_id == usuario_id)
        with self._sessao() as sessao:
            linhas = sessao.execute(consulta.order_by(traco_de_execucao.c.instante)).mappings().all()
        return [
            TracoDeExecucao(
                proposal_id=linha["proposal_id"],
                action_id=linha["action_id"],
                desfecho=linha["desfecho"],
                inquilino_id=linha["tenant_id"],
                usuario_id=linha["usuario_id"],
                origem=Origem(linha["origem"]),
                instante=linha["instante"],
                trace_id=linha["trace_id"] or "",
                motivo=linha["motivo"] or "",
                outcomes=_outcomes_do_json(linha["outcomes"]),
            )
            for linha in linhas
        ]
