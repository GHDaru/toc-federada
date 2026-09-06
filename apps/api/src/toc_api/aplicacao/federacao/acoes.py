"""Ações governadas — propor, decidir, executar; sempre com traço (APH-5.x).

Siglas, uma vez: **APH** — Aplicação ↔ Harness · **FSM** — máquina de estados finitos ·
**TTL** — *Time To Live* (tempo de vida) · **HTTP** — *HyperText Transfer Protocol*.

Este módulo é a orquestração da governança. A regra está no domínio (a FSM, a invariante do
lote, a validação de argumentos); o que está aqui é a **ordem** em que ela é aplicada, e a
ordem é a parte que se erra:

1. **Achar a ação no catálogo** — inexistente é `AcaoDesconhecida`.
2. **Autorizar, no caso de uso** (§B.7.2, RF-17). Não na rota. Não em `Depends`. Aqui.
   A recusa é `AcaoDesconhecida` também, porque "existe e você não pode" e "não existe"
   têm de ser indistinguíveis de fora (§B.7.3).
3. **Validar os `args`** contra o `input_schema` (RF-31) — antes de qualquer efeito.
4. **Exigir o sumidouro de traço** (APH-5.5) — antes de qualquer efeito. Sem ele, a
   execução é rejeitada; é a sabotagem que a DoD 5 da spec 006 pede.
5. Só então criar a proposta e deixá-la atravessar a FSM.

E o detalhe que o APH-9.4b torna obrigatório (RF-19): **a verificação local acontece
sempre**. As capabilities da introspecção são teto do hospedeiro, não retrato do usuário —
a norma mediu o caso em que elas excedem quem abriu o embarque. Confiar nelas como filtro
único seria confiar num filtro que a própria norma diz não existir.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from typing import Any, Mapping

from ...dominio.federacao.catalogo import AcaoDesconhecida, AcaoDoCatalogo, Catalogo
from ...dominio.federacao.portas import (
    ExecutorDeAcao,
    GeradorDeIdentificadores,
    RepositorioDePropostas,
    RepositorioDeTraco,
)
from ...dominio.federacao.principal import IntrospeccaoInvalida, Principal
from ...dominio.federacao.proposta import (
    CorridaDeDecisao,
    Desfecho,
    Origem,
    PropostaDeAcao,
    TransicaoInvalida,
)
from ...dominio.federacao.traco import AcaoSemTraco, TracoDeExecucao
from ...dominio.portas import Rastreador, Relogio, SpanDeTraco
from ..casos_de_uso import CasoDeUso
from ..politica import PoliticaDeAutorizacao


@dataclass(frozen=True)
class ResultadoDaAcao:
    """A proposta e os eventos do fio que ela produziu, nesta ordem.

    Os eventos saem daqui em vez de serem emitidos pelo caso de uso porque a sessão é do
    fio (borda), e a camada de aplicação é pura: ela **descreve** o que a borda emite.
    """

    proposta: PropostaDeAcao
    eventos: tuple[tuple[str, dict[str, Any]], ...]


class _ComGovernanca(CasoDeUso):
    """O que `ProporAcao` e `DecidirProposta` compartilham — inclusive o traço."""

    def __init__(
        self,
        *,
        rastreador: Rastreador,
        catalogo: Catalogo,
        propostas: RepositorioDePropostas,
        tracos: RepositorioDeTraco | None,
        executor: ExecutorDeAcao,
        relogio: Relogio,
        identificadores: GeradorDeIdentificadores,
        politica: PoliticaDeAutorizacao,
        ttl: timedelta = timedelta(minutes=10),
    ) -> None:
        super().__init__(rastreador=rastreador)
        self._catalogo = catalogo
        self._propostas = propostas
        self._tracos = tracos
        self._executor = executor
        self._relogio = relogio
        self._identificadores = identificadores
        self._politica = politica
        self._ttl = ttl

    # -- guardas -------------------------------------------------------------------
    def _exigir_identidade(self, principal: Principal) -> tuple[str, str]:
        if principal.anonimo or not principal.inquilino_id or not principal.usuario_id:
            raise IntrospeccaoInvalida(
                "SEM_IDENTIDADE", "só um principal identificado propõe ou decide ação"
            )
        return principal.inquilino_id, principal.usuario_id

    def _exigir_sumidouro_de_traco(self) -> RepositorioDeTraco:
        """APH-5.5: ação sem traço é ação não governada, e DEVE ser rejeitada.

        A verificação vem **antes** do efeito, e não depois: descobrir que não há traço
        depois de executar seria descobrir tarde demais.
        """
        if self._tracos is None:
            raise AcaoSemTraco(
                "não há sumidouro de traço configurado — a execução é rejeitada antes do "
                "efeito (APH-5.5)"
            )
        return self._tracos

    def _autorizar(self, principal: Principal, acao: AcaoDoCatalogo) -> None:
        """RF-17/RF-19: a verificação local, sempre — o teto do hospedeiro não dispensa."""
        if not self._politica.permite(principal, acao.capability_exigida):
            raise AcaoDesconhecida(acao.action_id)

    def _achar_acao(self, principal: Principal, action_id: str) -> AcaoDoCatalogo:
        acao = self._catalogo.acao(action_id)  # inexistente → AcaoDesconhecida
        self._autorizar(principal, acao)
        return acao

    # -- traço ---------------------------------------------------------------------
    def _registrar_traco(
        self,
        proposta: PropostaDeAcao,
        *,
        principal: Principal,
        motivo: str = "",
    ) -> None:
        tracos = self._exigir_sumidouro_de_traco()
        inquilino, usuario = self._exigir_identidade(principal)
        tracos.registrar(
            TracoDeExecucao.da_proposta(
                proposta,
                inquilino_id=inquilino,
                usuario_id=usuario,
                instante=self._relogio.agora(),
                motivo=motivo,
            )
        )

    def _traco_de_recusa(
        self, *, principal: Principal, action_id: str, motivo: str, origem: Origem
    ) -> None:
        """Recusa também é desfecho — e desfecho deixa traço (RF-21).

        A proposta é construída e imediatamente encerrada em `denied`: sem um agregado, o
        traço não teria `proposal_id`, e "o que a IA tentou fazer" ficaria sem identidade.
        """
        tracos = self._exigir_sumidouro_de_traco()
        inquilino, usuario = self._exigir_identidade(principal)
        agora = self._relogio.agora()
        proposta = PropostaDeAcao.nova(
            proposal_id=str(self._identificadores.novo()),
            action_id=action_id,
            args={},
            risk="confirm",
            alvos=(),
            origem=origem,
            criada_em=agora,
            ttl=self._ttl,
        )
        proposta.transicionar("negar", em=agora)
        proposta.desfecho = Desfecho(status="denied", mensagem=motivo)
        tracos.registrar(
            TracoDeExecucao.da_proposta(
                proposta,
                inquilino_id=inquilino,
                usuario_id=usuario,
                instante=agora,
                motivo=motivo,
            )
        )

    # -- execução ------------------------------------------------------------------
    def _reservar(self, proposta: PropostaDeAcao, principal: Principal) -> None:
        """Grava `executing` NO BANCO, condicionado ao estado lido — antes do efeito.

        **É aqui que a corrida se resolve, e é por isso que esta chamada não pode descer
        uma linha.** A transição `confirmed → executing` é a serialização natural do
        APH-5.1, mas só quando ela existe no banco: enquanto a máquina de estados finitos
        (FSM) transicionava um agregado em memória e a gravação vinha **depois** do efeito,
        oito confirmações simultâneas atravessavam oito objetos, todas legítimas, e
        executavam oito vezes — 50 nós para 30 pedidos, oito linhas de traço.

        O repositório condiciona a escrita ao `estado_lido` (`UPDATE … WHERE estado =`), e
        quem não casa recebe `CorridaDeDecisao`. Quem não escreve, **não executa**.
        """
        inquilino, usuario = self._exigir_identidade(principal)
        self._propostas.salvar(inquilino, usuario, proposta)

    def _executar(
        self,
        proposta: PropostaDeAcao,
        acao: AcaoDoCatalogo,
        principal: Principal,
        *,
        reservar: bool = True,
    ) -> None:
        """Executa e fecha a proposta. Lote: alvo a alvo, com desfecho por alvo."""
        agora = self._relogio.agora()
        proposta.transicionar("executar", em=agora)
        if reservar:
            self._reservar(proposta, principal)
        if not proposta.alvos:
            status, mensagem = self._executor.executar(
                action_id=acao.action_id,
                # `__proposta__` acompanha TODA execução: quem escreve no domínio precisa
                # saber qual proposta autorizou a escrita, e é isso que torna a mutação
                # vinda de modelo distinguível de edição humana para sempre (RF-25 da spec
                # 007). Chaves com `__` são vocabulário da governança, nunca do cliente: o
                # `input_schema` é fechado e as recusaria.
                args={**dict(proposta.args), "__proposta__": proposta.proposal_id},
                principal=principal,
            )
            desfecho = Desfecho(
                status="executed" if status == "executed" else "failed", mensagem=mensagem
            )
        else:
            outcomes: list[tuple[str, str, str]] = []
            for indice, alvo in enumerate(proposta.alvos):
                # `__alvo__` é o nome do alvo (o que aparece no `outcomes`); `__indice__` é
                # a posição dele no campo de lote declarado pela ação. O executor precisa
                # dos dois: o primeiro para relatar, o segundo para saber QUAL item do
                # `args` executar — adivinhar por "o primeiro array que eu achar" é a
                # heurística que quebra na ação seguinte.
                status, mensagem = self._executor.executar(
                    action_id=acao.action_id,
                    args={
                        **dict(proposta.args),
                        "__alvo__": alvo,
                        "__indice__": indice,
                        "__proposta__": proposta.proposal_id,
                    },
                    principal=principal,
                )
                outcomes.append((alvo, status, mensagem))
            # APH-5.9(e): o terminal não afirma mais sucesso do que os alvos mostram.
            # A conta é feita aqui, e a invariante do `Desfecho` a confere de novo — duas
            # vezes de propósito: uma engana-se por descuido, duas exigem intenção.
            todos_ok = all(status == "executed" for _, status, _ in outcomes)
            desfecho = Desfecho(status="executed" if todos_ok else "failed", outcomes=tuple(outcomes))
        proposta.concluir(desfecho=desfecho, em=self._relogio.agora())


class ProporAcao(_ComGovernanca):
    """Nasce a proposta. `read` executa direto; `confirm` para no gate humano (APH-5.2)."""

    nome = "propor_acao"

    def anotar(self, span: SpanDeTraco, **kwargs) -> None:
        principal = kwargs.get("principal")
        if principal is not None and principal.inquilino_id:
            span.atributo("toc.inquilino_id", principal.inquilino_id)
        # `action_id` é vocabulário nosso; `args` NUNCA entram no span (ADR 0006: nada de
        # enunciado de pessoa em traço).
        if kwargs.get("action_id"):
            span.atributo("toc.action_id", str(kwargs["action_id"]))

    def executar(
        self,
        *,
        principal: Principal,
        action_id: str,
        args: Mapping[str, Any],
        origem: Origem = Origem.IA,
        contexto_hash: str | None = None,
        titulo: str = "",
        justificativa: str = "",
    ) -> ResultadoDaAcao:
        self._exigir_identidade(principal)
        self._exigir_sumidouro_de_traco()

        try:
            acao = self._achar_acao(principal, action_id)
        except AcaoDesconhecida:
            self._traco_de_recusa(
                principal=principal,
                action_id=action_id,
                motivo="ação fora do catálogo composto para este principal",
                origem=origem,
            )
            raise

        try:
            acao.validar_args(args)
        except Exception as erro:
            self._traco_de_recusa(
                principal=principal,
                action_id=action_id,
                motivo=f"argumentos recusados pelo input_schema: {erro}",
                origem=origem,
            )
            raise

        agora = self._relogio.agora()
        proposta = PropostaDeAcao.nova(
            proposal_id=str(self._identificadores.novo()),
            action_id=acao.action_id,
            args=dict(args),
            risk=acao.risk,
            alvos=acao.alvos(args),
            origem=origem,
            criada_em=agora,
            ttl=self._ttl,
            contexto_hash=contexto_hash,
        )
        eventos: list[tuple[str, dict[str, Any]]] = [
            (
                "action_proposal",
                proposta.como_action_proposal(
                    titulo=titulo or acao.title, justificativa=justificativa
                ),
            )
        ]

        if acao.requires_confirmation:
            # Verbo mutador nasce proposta e **espera** (P2, APH-5.1). O domínio segue
            # intocado; o traço vem no desfecho, que ainda não existe.
            proposta.apresentar(em=agora)
        else:
            proposta.confirmar(em=agora)
            # A ação de leitura executa direto (APH-5.2) — e mesmo ela reserva antes do
            # efeito. Não é cerimônia: é o que faz "nenhum efeito acontece antes de a
            # reserva estar no banco" valer para TODO caminho, e não para o caminho que o
            # crítico atacou. Um invariante com exceção é um invariante que se perde na
            # próxima rota.
            self._executar(proposta, acao, principal)
            eventos.append(("action_result", proposta.como_action_result()))
            self._registrar_traco(proposta, principal=principal)

        self._propostas.salvar(
            principal.inquilino_id or "", principal.usuario_id or "", proposta
        )
        return ResultadoDaAcao(proposta=proposta, eventos=tuple(eventos))


class DecidirProposta(_ComGovernanca):
    """O gate humano: confirmar ou recusar, com deduplicação e contexto conferido."""

    nome = "decidir_proposta"

    def anotar(self, span: SpanDeTraco, **kwargs) -> None:
        principal = kwargs.get("principal")
        if principal is not None and principal.inquilino_id:
            span.atributo("toc.inquilino_id", principal.inquilino_id)
        if kwargs.get("proposal_id"):
            span.atributo("toc.proposal_id", str(kwargs["proposal_id"]))

    def _como_resultado(self, proposta: PropostaDeAcao) -> ResultadoDaAcao:
        return ResultadoDaAcao(
            proposta=proposta, eventos=(("action_result", proposta.como_action_result()),)
        )

    def _desfecho_da_mesma_chave(self, inquilino: str, proposta: PropostaDeAcao) -> ResultadoDaAcao:
        """APH-5.3, segunda metade: **quantas respostas idênticas forem pedidas**.

        A chave já está nesta proposta, então esta confirmação é uma repetição da que a
        gravou. Nada reexecuta e nada entra no traço: o que volta é a linha que o vencedor
        gravou. Se ele ainda estiver executando, espera-se por ele — o limite da espera é
        do adaptador e está declarado lá (`ESPERA_MAXIMA`, 6 s).
        """
        vencedora = self._propostas.aguardar_desfecho(inquilino, proposta.proposal_id) or proposta
        if not vencedora.terminal:
            # Fail-closed: uma proposta não-terminal não tem `action_result`, e devolver o
            # `failed` da projeção seria afirmar um desfecho que não houve.
            raise TransicaoInvalida(
                "INVALID_TRANSITION",
                f"a proposta {proposta.proposal_id} segue em {vencedora.estado!r}: a "
                "decisão que a reservou ainda não terminou",
            )
        return self._como_resultado(vencedora)

    def _resolver_corrida(
        self,
        inquilino: str,
        proposal_id: str,
        *,
        idempotency_key: str | None,
        corrida: CorridaDeDecisao,
    ) -> ResultadoDaAcao:
        """Perdeu a corrida. Com a MESMA chave, devolve o desfecho de quem venceu.

        Sem chave, a recusa é `INVALID_TRANSITION` (§A.7) e é a resposta certa: quem não
        pediu deduplicação recebe a verdade da máquina de estados — a proposta não está
        mais em `awaiting_approval`, e a decisão que executou não foi a dele. É por isso
        que a chave **significa** alguma coisa, que é literalmente o que o APH-5.3 diz ao
        colocá-la "além da proteção que a FSM já dá".
        """
        if not idempotency_key:
            raise corrida
        vencedora = self._propostas.aguardar_desfecho(inquilino, proposal_id)
        if vencedora is None or not vencedora.terminal or not vencedora.mesma_chave(
            idempotency_key
        ):
            raise corrida
        return self._como_resultado(vencedora)

    def executar(
        self,
        *,
        principal: Principal,
        proposal_id: str,
        aprovado: bool,
        contexto_hash: str | None = None,
        idempotency_key: str | None = None,
    ) -> ResultadoDaAcao:
        inquilino, usuario = self._exigir_identidade(principal)
        self._exigir_sumidouro_de_traco()

        proposta = self._propostas.obter(inquilino, proposal_id)
        if proposta is None:
            # Proposta de outro inquilino é indistinguível de inexistente — a fronteira é
            # a consulta, como no M1 (`NaoEncontrado`, nunca "proibido").
            raise AcaoDesconhecida(proposal_id)

        # APH-5.3, primeira metade: esta proposta JÁ carrega esta chave, logo esta
        # confirmação é a repetição de uma que já foi decidida. Antes deste bloco a coluna
        # `idempotency_key` era gravada em toda confirmação e lida em lugar nenhum — a
        # varredura `grep -rn idempotency_key` mostrava só escritas.
        if idempotency_key and proposta.mesma_chave(idempotency_key):
            return self._desfecho_da_mesma_chave(inquilino, proposta)

        # RF-16: a decisão repetida devolve o desfecho original, sem novo efeito e sem
        # novo traço. Duplicar o traço faria a auditoria contar duas execuções que não
        # houve — pior do que não registrar.
        repetida = proposta.decisao_ja_tomada(aprovado=aprovado)
        if repetida is not None:
            return self._como_resultado(proposta)

        acao = self._achar_acao(principal, proposta.action_id)
        agora = self._relogio.agora()

        if not aprovado:
            # Recusar também é decidir, e decidir também escreve: sem a mesma reserva,
            # oito recusas simultâneas gravariam oito vezes e deixariam oito linhas de
            # traço `denied` para uma decisão só. Medido antes do conserto: cinco.
            proposta.negar(em=agora)
            try:
                self._propostas.salvar(inquilino, usuario, proposta)
            except CorridaDeDecisao as corrida:
                return self._resolver_corrida(
                    inquilino, proposal_id, idempotency_key=idempotency_key, corrida=corrida
                )
            self._registrar_traco(proposta, principal=principal)
            return self._como_resultado(proposta)

        try:
            proposta.confirmar(
                em=agora, contexto_hash=contexto_hash, idempotency_key=idempotency_key
            )
        except TransicaoInvalida:
            # Expirada e contexto divergente já mudaram o estado do agregado dentro de
            # `confirmar` (vencer e invalidar são desfechos, não limbo) — o traço sai
            # aqui, e a exceção segue para a borda traduzir em HTTP 409.
            try:
                self._propostas.salvar(inquilino, usuario, proposta)
            except CorridaDeDecisao:
                # Outra decisão chegou antes e é ela que vale; o desfecho dela é que fica
                # gravado, e gravar o nosso por cima seria reescrever a decisão de quem
                # ganhou. A exceção original segue mesmo assim: quem chamou tem de saber
                # que a SUA decisão não vingou.
                raise
            if proposta.terminal:
                self._registrar_traco(proposta, principal=principal)
            raise

        try:
            # A reserva mora dentro de `_executar`, entre a transição e o efeito.
            self._executar(proposta, acao, principal)
        except CorridaDeDecisao as corrida:
            return self._resolver_corrida(
                inquilino, proposal_id, idempotency_key=idempotency_key, corrida=corrida
            )
        self._propostas.salvar(inquilino, usuario, proposta)
        self._registrar_traco(proposta, principal=principal)
        return self._como_resultado(proposta)
