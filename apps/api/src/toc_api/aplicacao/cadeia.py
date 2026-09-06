"""Casos de uso do encadeamento (E4.4) — promover, semear, derivar e percorrer.

Siglas, uma vez neste arquivo: **ARA** — Árvore da Realidade Atual · **UDE** — Efeito
Indesejável · **NC** — Nuvem de Conflito · **ARF** — Árvore da Realidade Futura · **APR**
— Árvore de Pré-Requisitos · **AT** — Árvore de Transição · **OI** — Objetivo
Intermediário · **OTel** — OpenTelemetry · **RF/RN/RNF** — requisito funcional / regra de
negócio / requisito não funcional da spec 008.

**O que estes quatro casos de uso têm em comum, e é o requisito**: cada um grava DOIS
agregados — o projeto novo e a `ReferenciaCruzada` — e leva ao traço o identificador da
referência criada (RNF-03). É a linha auditável do encadeamento, e ela nasce junto com
ele, não depois.

**Regime de governança** (INT-04, item 8 da constituição do projeto): promover, semear e
derivar são **manipulação direta do titular** — alvo nomeado pelo gesto, reversível por
exclusão suave, traço obrigatório. Aplicam na hora, sem tela de confirmação e sem máquina
de estados de proposta. Quem nasce `action_proposal` são as sugestões inferidas por modelo
(as quatro `toc.suggest_*` deste módulo), e elas passam por outro caminho.

A ordem de gravação é sempre a mesma e não é estética: **primeiro o projeto, depois a
referência**. Uma referência gravada antes do projeto de destino apontaria, por um
instante, para o que ainda não existe — e é justamente esse instante que a vista da cadeia
mostraria como elo pendente sem que nada tivesse acontecido.
"""
from __future__ import annotations

from typing import Any, Sequence
from uuid import UUID, uuid4

from ..dominio.apr import ProjetoAPR
from ..dominio.ara import ProjetoARA
from ..dominio.arf import ProjetoARF
from ..dominio.at import ProjetoAT
from ..dominio.erros import NaoEncontrado
from ..dominio.encadeamento import (
    derivar_apr_de_arf,
    derivar_at_de_oi,
    promover_udes_para_nc,
    semear_arf_de_injecao,
)
from ..dominio.identidade import DonoDoProjeto
from ..dominio.nuvem import NuvemDeConflito
from ..dominio.portas import Rastreador, Relogio, RepositorioDaCadeia, SpanDeTraco
from ..dominio.referencia import Cadeia, ReferenciaCruzada, travessia
from .casos_de_uso import CasoDeUso


class _ComCadeia(CasoDeUso):
    """Recebe o repositório composto: a cadeia lê uma ferramenta e grava outra."""

    def __init__(
        self,
        *,
        rastreador: Rastreador,
        repositorio: RepositorioDaCadeia,
        relogio: Relogio | None = None,
    ) -> None:
        super().__init__(rastreador=rastreador)
        self._repositorio = repositorio
        self._relogio = relogio

    def _agora(self):
        if self._relogio is None:  # pragma: no cover - erro de composição
            raise RuntimeError(f"{type(self).__name__} precisa de um relógio")
        return self._relogio.agora()

    def _anotar_referencia(self, span: SpanDeTraco, referencia: ReferenciaCruzada) -> None:
        """RNF-03: o identificador da referência **no traço** — a linha auditável."""
        span.atributo("toc.referencia_id", str(referencia.id))
        span.atributo("toc.referencia_tipo", referencia.tipo.value)
        span.atributo("toc.projeto_origem", str(referencia.origem.projeto_id))
        span.atributo("toc.projeto_destino", str(referencia.destino.projeto_id))


class PromoverUdesParaNC(_ComCadeia):
    """RF-36: UDEs `Validado` de uma ARA viram o dilema de uma Nuvem de Conflito nova.

    Executa o INT-05 da spec 007 — a ação que aquele ciclo prometeu e delegou a este.
    """

    nome = "promover_udes_para_nc"

    def executar(
        self,
        *,
        dono: DonoDoProjeto,
        projeto_id: UUID,
        no_ids: Sequence[UUID],
        nome: str,
    ) -> NuvemDeConflito:
        ara: ProjetoARA | None = self._repositorio.obter_ara(dono.inquilino_id, projeto_id)
        if ara is None:
            raise NaoEncontrado(str(projeto_id))
        self._udes = tuple(no_ids)
        promocao = promover_udes_para_nc(
            ara, no_ids=self._udes, id=uuid4(), nome=nome, em=self._agora()
        )
        self._repositorio.salvar_nuvem(promocao.nuvem)
        self._repositorio.salvar_referencia(promocao.referencia)
        self._referencia = promocao.referencia
        return promocao.nuvem

    def anotar_resultado(self, span: SpanDeTraco, resultado: NuvemDeConflito) -> None:
        span.atributo("toc.udes_promovidos", len(self._udes))
        self._anotar_referencia(span, self._referencia)


class SemearArfDeInjecao(_ComCadeia):
    """RF-38: a injeção `escolhida` semeia a ARF — o INT-06 da spec 007, executado aqui.

    Grava TRÊS coisas: a ARF nova, a nuvem (cuja `ReferenciaDeSemeadura` passou a apontar
    o destino) e a referência cruzada. A nuvem é gravada porque ela mudou — omiti-la
    deixaria a projeção local de leitura desatualizada no banco enquanto a memória a
    mostrava correta, que é o pior dos dois mundos.
    """

    nome = "semear_arf_de_injecao"

    def executar(
        self, *, dono: DonoDoProjeto, projeto_id: UUID, injecao_id: UUID, nome: str
    ) -> ProjetoARF:
        nuvem = self._repositorio.obter_nuvem(dono.inquilino_id, projeto_id)
        if nuvem is None:
            raise NaoEncontrado(str(projeto_id))
        semeadura = semear_arf_de_injecao(
            nuvem, injecao_id=injecao_id, id=uuid4(), nome=nome, em=self._agora()
        )
        self._repositorio.salvar_arf(semeadura.arf)
        self._repositorio.salvar_nuvem(nuvem)
        self._repositorio.salvar_referencia(semeadura.referencia)
        self._referencia = semeadura.referencia
        return semeadura.arf

    def anotar_resultado(self, span: SpanDeTraco, resultado: ProjetoARF) -> None:
        span.atributo("toc.udes_da_cadeia", len(resultado.udes_da_cadeia))
        self._anotar_referencia(span, self._referencia)


class DerivarAprDeArf(_ComCadeia):
    """RF-39: a ARF verificada deriva a APR de implementação, com objetivo proposto."""

    nome = "derivar_apr_de_arf"

    def executar(
        self,
        *,
        dono: DonoDoProjeto,
        projeto_id: UUID,
        no_id: UUID,
        nome: str,
        objetivo: str | None = None,
    ) -> ProjetoAPR:
        arf = self._repositorio.obter_arf(dono.inquilino_id, projeto_id)
        if arf is None:
            raise NaoEncontrado(str(projeto_id))
        derivacao = derivar_apr_de_arf(
            arf, no_id=no_id, id=uuid4(), nome=nome, objetivo=objetivo, em=self._agora()
        )
        self._repositorio.salvar_apr(derivacao.apr)
        # A ARF muda: ela recebe o evento `ArfDerivouApr`, que é a memória do vínculo do
        # lado de quem derivou. Não gravá-la perderia metade da rastreabilidade.
        self._repositorio.salvar_arf(arf)
        self._repositorio.salvar_referencia(derivacao.referencia)
        self._referencia = derivacao.referencia
        return derivacao.apr

    def anotar_resultado(self, span: SpanDeTraco, resultado: ProjetoAPR) -> None:
        self._anotar_referencia(span, self._referencia)


class DerivarAtDeOi(_ComCadeia):
    """RF-40: o objetivo intermediário sequenciado vira a Árvore de Transição dele."""

    nome = "derivar_at_de_oi"

    def executar(
        self, *, dono: DonoDoProjeto, projeto_id: UUID, no_id: UUID, nome: str
    ) -> ProjetoAT:
        apr = self._repositorio.obter_apr(dono.inquilino_id, projeto_id)
        if apr is None:
            raise NaoEncontrado(str(projeto_id))
        derivacao = derivar_at_de_oi(
            apr, no_id=no_id, id=uuid4(), nome=nome, em=self._agora()
        )
        self._repositorio.salvar_at(derivacao.at)
        self._repositorio.salvar_apr(apr)
        self._repositorio.salvar_referencia(derivacao.referencia)
        self._referencia = derivacao.referencia
        return derivacao.at

    def anotar_resultado(self, span: SpanDeTraco, resultado: ProjetoAT) -> None:
        self._anotar_referencia(span, self._referencia)


class AbrirCadeia(_ComCadeia):
    """RF-41/RF-42: a travessia completa a partir de qualquer elemento encadeado.

    Leitura pura sobre as referências — sem tabela materializada e sem cache (decisão 7 do
    plano do ciclo 008). O elo com ponta excluída vem `pendente`, **nunca** ausente: é a
    US-18 em uma linha.
    """

    nome = "abrir_cadeia"

    def executar(self, *, dono: DonoDoProjeto, projeto_id: UUID) -> Cadeia:
        # Todas as referências do inquilino, e não só as que tocam este projeto: a
        # travessia sobe até a raiz da análise e desce dali, então filtrar pelo projeto de
        # partida devolveria um pedaço da cadeia como se fosse a cadeia inteira.
        referencias = self._repositorio.listar_referencias(dono.inquilino_id)
        return travessia(tuple(referencias), projeto_id=projeto_id)

    def anotar_resultado(self, span: SpanDeTraco, resultado: Cadeia) -> None:
        for chave, valor in resultado.resumo().items():
            span.atributo(f"toc.{chave}", valor)


class ListarReferenciasDoProjeto(_ComCadeia):
    """RF-34: as referências de origem e de destino de um projeto, para a ficha."""

    nome = "listar_referencias_do_projeto"

    def executar(
        self, *, dono: DonoDoProjeto, projeto_id: UUID
    ) -> list[ReferenciaCruzada]:
        return self._repositorio.listar_referencias(
            dono.inquilino_id, projeto_id=projeto_id
        )

    def anotar_resultado(self, span: SpanDeTraco, resultado) -> None:
        span.atributo("toc.referencias", len(resultado))


__all__ = [
    "AbrirCadeia",
    "DerivarAprDeArf",
    "DerivarAtDeOi",
    "ListarReferenciasDoProjeto",
    "PromoverUdesParaNC",
    "SemearArfDeInjecao",
]
