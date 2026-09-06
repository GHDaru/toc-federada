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

import time
from typing import Any
from uuid import uuid4

from sqlalchemy import insert, select, update
from sqlalchemy.exc import IntegrityError

from ...dominio.federacao.proposta import (
    ChaveDeIdempotenciaReutilizada,
    CorridaDeDecisao,
    Desfecho,
    Origem,
    PropostaDeAcao,
)
from ...dominio.federacao.traco import TracoDeExecucao
from ..persistencia.tabelas import proposta_de_acao, traco_de_execucao

#: O nome do índice único parcial da revisão 0006. Aparece aqui porque a tradução de
#: `IntegrityError` para erro de domínio discrimina por ele — e não pelo texto da mensagem
#: do driver, que muda de versão para versão.
NOME_DO_INDICE_DE_IDEMPOTENCIA = "uq_proposta_de_acao_tenant_id_idempotency_key"

#: O limite da espera por quem venceu a corrida, declarado em vez de suposto:
#: 300 × 20 ms = **6 s**. É o mesmo par de constantes do duplo em memória, para o duplo não
#: ser nem mais rápido nem mais paciente que o banco de verdade.
TENTATIVAS_DE_ESPERA = 300
PAUSA_DA_ESPERA = 0.02
ESPERA_MAXIMA = TENTATIVAS_DE_ESPERA * PAUSA_DA_ESPERA


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
    """Implementa `RepositorioDePropostas`. **`salvar` é a trava, e por isso é a corrida.**

    ## O defeito que este adaptador tinha, medido

    `salvar` era um `INSERT … ON CONFLICT (proposal_id) DO UPDATE` **incondicional**: ele
    gravava `estado` por cima do que a linha tivesse. E `obter` reidrata um agregado NOVO a
    cada chamada. Somados, os dois faziam a máquina de estados finitos (FSM) guardar o
    **objeto** e não a linha: oito confirmações simultâneas liam oito agregados em
    `awaiting_approval`, atravessavam oito transições todas legítimas, e executavam oito
    vezes. Contra o PostgreSQL real: **oito confirmações da mesma proposta de 30 alvos ·
    oito respostas `200` · 50 nós no banco · 22 títulos repetidos · oito linhas de traço
    para uma proposta só.**

    ## O conserto, e onde ele mora

    A transição `confirmed → executing` **é** a serialização natural — desde que exista no
    banco e **antes** do efeito. Aqui ela vira `UPDATE … WHERE estado = :estado_lido`: o
    PostgreSQL serializa as escritas concorrentes no bloqueio da linha, a segunda espera a
    primeira comitar, refaz o predicado sob READ COMMITTED, não casa mais, e volta com
    `rowcount` 0 — que este adaptador traduz em `CorridaDeDecisao`, nunca em silêncio. É a
    mesma peça que `repositorio_projetos._gravar_projeto` instalou para o agregado Projeto;
    o que faltava era a proposta ter de que estado partiu (`estado_lido`).

    A segunda metade é o APH-5.3: a violação do índice único parcial
    `(tenant_id, idempotency_key)` (revisão 0006) vira `ChaveDeIdempotenciaReutilizada`.
    Uma chave, uma execução.
    """

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
            try:
                if not proposta.estado_lido:
                    # Nunca gravada. Se já existe linha com este identificador, quem chamou
                    # está prestes a passar por cima de uma decisão que não leu — a mesma
                    # perda do `versao_lida == 0` do núcleo, só que com o gate humano.
                    sessao.execute(insert(proposta_de_acao).values(**valores))
                else:
                    # A TRAVA. Esta linha é o conserto inteiro: quem não partiu do estado
                    # que a linha tem não escreve — e, como ela roda ANTES do efeito, quem
                    # não escreve também não executa.
                    resultado = sessao.execute(
                        update(proposta_de_acao)
                        .where(
                            proposta_de_acao.c.proposal_id == proposta.proposal_id,
                            proposta_de_acao.c.tenant_id == inquilino_id,
                            proposta_de_acao.c.estado == proposta.estado_lido,
                        )
                        .values(**atualizaveis)
                    )
                    if resultado.rowcount == 0:
                        # Relê o estado AGORA, e não o de antes: entre um e outro a
                        # concorrente pode ter comitado, e o estado que o cliente recebe
                        # tem de ser o que o banco tem.
                        atual = sessao.execute(
                            select(proposta_de_acao.c.estado).where(
                                proposta_de_acao.c.proposal_id == proposta.proposal_id,
                                proposta_de_acao.c.tenant_id == inquilino_id,
                            )
                        ).first()
                        sessao.rollback()
                        raise CorridaDeDecisao(
                            proposta.proposal_id,
                            estado_lido=proposta.estado_lido,
                            estado_atual=atual.estado if atual else "<inexistente>",
                        )
                sessao.commit()
            except IntegrityError as erro:
                sessao.rollback()
                raise self._traduzir(erro, inquilino_id, proposta) from erro
        # Só DEPOIS do commit: confirmar antes deixaria o agregado achando que está
        # sincronizado com um banco que não recebeu nada.
        proposta.confirmar_gravacao()

    def _traduzir(self, erro: IntegrityError, inquilino_id: str, proposta: PropostaDeAcao):
        """Violação de unicidade vira erro de domínio — nunca 500 disfarçado de sistema."""
        texto = str(getattr(erro, "orig", erro))
        if NOME_DO_INDICE_DE_IDEMPOTENCIA in texto and proposta.idempotency_key:
            dona = self._proposal_id_da_chave(inquilino_id, proposta.idempotency_key)
            return ChaveDeIdempotenciaReutilizada(
                proposta.idempotency_key, proposal_id=dona or "<desconhecida>"
            )
        # Chave primária: a proposta já existe e quem grava não a leu.
        return CorridaDeDecisao(
            proposta.proposal_id,
            estado_lido=proposta.estado_lido,
            estado_atual="<existente>",
        )

    def _proposal_id_da_chave(self, inquilino_id: str, chave: str) -> str | None:
        with self._sessao() as sessao:
            linha = sessao.execute(
                select(proposta_de_acao.c.proposal_id).where(
                    proposta_de_acao.c.tenant_id == inquilino_id,
                    proposta_de_acao.c.idempotency_key == chave,
                )
            ).first()
        return linha.proposal_id if linha else None

    def obter(self, inquilino_id: str, proposal_id: str) -> PropostaDeAcao | None:
        with self._sessao() as sessao:
            linha = sessao.execute(
                select(proposta_de_acao).where(
                    proposta_de_acao.c.tenant_id == inquilino_id,
                    proposta_de_acao.c.proposal_id == proposal_id,
                )
            ).mappings().first()
        return self._reidratar(linha) if linha else None

    def aguardar_desfecho(
        self, inquilino_id: str, proposal_id: str
    ) -> PropostaDeAcao | None:
        """Espera quem venceu a corrida terminar, e devolve o desfecho dele.

        É o que permite a segunda metade do APH-5.3 — "quantas respostas idênticas forem
        pedidas" — **sem reexecutar nada**: a resposta que o perdedor recebe é a linha que o
        vencedor gravou. O limite é declarado (`ESPERA_MAXIMA`, 6 s) em vez de suposto, e
        esgotá-lo devolve o que houver: quem decide o que fazer com uma proposta que não
        terminou é a aplicação, não o adaptador.
        """
        for _ in range(TENTATIVAS_DE_ESPERA):
            proposta = self.obter(inquilino_id, proposal_id)
            if proposta is None or proposta.terminal:
                return proposta
            time.sleep(PAUSA_DA_ESPERA)
        return self.obter(inquilino_id, proposal_id)

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
        # A base da trava: o agregado sai daqui sabendo de que estado partiu. Sem esta
        # linha `estado` volta a ser um atributo em memória — que foi o defeito.
        proposta.estado_lido = proposta.estado
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
