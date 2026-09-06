"""M4 · E4.4 — a referência cruzada: agregado próprio, fora dos projetos (spec 008).

Siglas, uma vez neste arquivo: **ARA** — Árvore da Realidade Atual · **UDE** — Efeito
Indesejável · **NC** — Nuvem de Conflito · **ARF** — Árvore da Realidade Futura · **APR**
— Árvore de Pré-Requisitos · **AT** — Árvore de Transição · **OI** — Objetivo
Intermediário · **TOC** — Teoria das Restrições · **RN/RF/RNF** — regra de negócio /
requisito funcional / requisito não funcional.

**O defeito com número.** A visão registra o D-11: nas quatro gerações da linhagem não
existia uma referência entre projetos. A contagem está colada na spec 008 (F-08):
`grep -c "araProjectId|sourceUdeId|linkedProject|crossTool" tocbuilderv3/types.ts` → `0`.
A intenção existia só na navegação — `Sidebar.tsx:86` desabilitava ARF, APR e AT sem uma
ARA carregada —, e nenhum modelo de dado jamais carregou o vínculo.

**Por que agregado próprio** (decisão 3 do plano do ciclo 008): um vínculo entre dois
projetos não pertence a nenhum dos dois. Guardá-lo dentro de um deles obrigaria a
consistência a atravessar duas raízes, e a ponta de fora ficaria sem quem respondesse por
ela. Aqui a referência tem identidade, estado, evento e **trava otimista própria** — a
mesma disciplina do `Projeto`: `versao_lida` diz de que versão a escrita partiu, e o
adaptador condiciona o `UPDATE` a ela.

Três regras vivem aqui, e cada uma é uma linha da spec:

- **RN-11** — nasce SOMENTE por ação nomeada (promover, semear, derivar, ou proposta
  aceita). Não há construtor anônimo: construir sem declarar a ação é recusado, e é por
  isso que "inferência silenciosa de sistema ou modelo" não é uma questão de disciplina.
- **RN-12** — exclusão suave de qualquer ponta **suspende** (`pendente`) e restauração
  **reativa**. Nenhuma operação do módulo apaga referência como efeito colateral.
- **RF-41** — a travessia da cadeia é **função pura** sobre as referências, nos dois
  sentidos, com o estado por elo. Sem tabela materializada e sem cache (decisão 7 do
  plano): 50 referências resolvem em memória.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Iterable, Sequence
from uuid import UUID

from .erros import DadoInvalido, MutacaoRecusada
from .eventos import (
    EventoDeDominio,
    ReferenciaCriada,
    ReferenciaReativada,
    ReferenciaSuspensa,
)
from .identidade import DonoDoProjeto

LIMITE_MOTIVO = 1000


class TipoDeReferencia(str, Enum):
    """RF-33: os quatro vínculos que a cadeia da análise conhece — vocabulário fechado."""

    PROMOCAO_UDE_NC = "promocao_ude_nc"
    SEMEADURA_INJECAO_ARF = "semeadura_injecao_arf"
    DERIVACAO_ARF_APR = "derivacao_arf_apr"
    DERIVACAO_OI_AT = "derivacao_oi_at"


class EstadoDaReferencia(str, Enum):
    """RN-12: `ativa` enquanto as duas pontas existem; `pendente` quando uma some."""

    ATIVA = "ativa"
    PENDENTE = "pendente"


class ReferenciaInvalida(MutacaoRecusada):
    """`regra`: `sem_acao_nomeada` · `motivo_obrigatorio` · `sem_mudanca` · `pontas_iguais`."""

    def __init__(self, regra: str, detalhe: str = "") -> None:
        super().__init__(f"{regra}: {detalhe}" if detalhe else regra)
        self.regra = regra


@dataclass(frozen=True, slots=True)
class Ponta:
    """Uma extremidade tipada: ferramenta, projeto, elementos e o papel deles.

    Tipada é o ponto — e é o contraste com a linhagem, onde "de onde isto veio" não
    existia em lugar nenhum do modelo. Aqui a origem é dado: qual ferramenta, qual
    projeto, quais elementos e em que papel.
    """

    ferramenta: str
    projeto_id: UUID
    elementos: tuple[UUID, ...] = ()
    papel: str = ""

    def __post_init__(self) -> None:
        if not (self.ferramenta or "").strip():
            raise DadoInvalido("ponta: ferramenta é obrigatória")
        if self.projeto_id is None:
            raise DadoInvalido("ponta: projeto é obrigatório")
        object.__setattr__(self, "ferramenta", self.ferramenta.strip())
        object.__setattr__(self, "elementos", tuple(self.elementos))


@dataclass(slots=True)
class ReferenciaCruzada:
    """O vínculo entre duas ferramentas — com identidade, estado, evento e trava."""

    id: UUID
    tipo: TipoDeReferencia
    origem: Ponta
    destino: Ponta
    dono: DonoDoProjeto
    criada_em: datetime
    estado: EstadoDaReferencia = EstadoDaReferencia.ATIVA
    motivo: str = ""
    versao: int = 1
    eventos: tuple[EventoDeDominio, ...] = ()
    #: RN-11 em forma de construtor: quem não declara a ação nomeada não constrói. As
    #: fábricas (`nomeada`, `reidratar_referencia`) são os dois únicos caminhos, e
    #: reidratar não é criar — é carregar o que já nasceu por uma ação.
    criada_por_acao: bool = field(default=False, repr=False, compare=False)
    #: A versão que esta referência tinha **no banco** quando foi lida. `0` = nunca
    #: gravada. Mesma semântica de `Projeto.versao_lida`, e pelo mesmo motivo: `versao`
    #: sozinha é contador em memória, e a escrita precisa de um número contra o qual
    #: casar o `WHERE`.
    versao_lida: int = field(default=0, init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        if not self.criada_por_acao:
            raise ReferenciaInvalida(
                "sem_acao_nomeada",
                "referência cruzada nasce somente por ação nomeada do titular (promover, "
                "semear, derivar) ou por proposta aceita (RN-11) — use "
                "ReferenciaCruzada.nomeada(...)",
            )
        self.tipo = TipoDeReferencia(self.tipo)
        self.estado = EstadoDaReferencia(self.estado)
        if self.origem.projeto_id == self.destino.projeto_id:
            raise ReferenciaInvalida(
                "pontas_iguais", "uma referência cruzada liga projetos diferentes"
            )
        self.eventos = tuple(self.eventos)

    # -- fábrica: a ação nomeada -------------------------------------------------

    @classmethod
    def nomeada(
        cls,
        *,
        id: UUID,
        tipo: TipoDeReferencia,
        origem: Ponta,
        destino: Ponta,
        dono: DonoDoProjeto,
        em: datetime,
    ) -> "ReferenciaCruzada":
        """RN-11: o ÚNICO caminho de criação, e ele emite o evento com as duas pontas."""
        referencia = cls(
            id=id,
            tipo=TipoDeReferencia(tipo),
            origem=origem,
            destino=destino,
            dono=dono,
            criada_em=em,
            criada_por_acao=True,
        )
        referencia._emitir(
            ReferenciaCriada,
            em,
            referencia_id=id,
            tipo=referencia.tipo.value,
            origem_projeto_id=origem.projeto_id,
            destino_projeto_id=destino.projeto_id,
        )
        return referencia

    # -- consultas ---------------------------------------------------------------

    @property
    def pontas(self) -> tuple[Ponta, Ponta]:
        return (self.origem, self.destino)

    def toca(self, projeto_id: UUID) -> bool:
        return projeto_id in (self.origem.projeto_id, self.destino.projeto_id)

    # -- RN-12: suspende e reativa, nunca apaga ----------------------------------

    def suspender(self, *, motivo: str, em: datetime) -> None:
        """Uma ponta sofreu exclusão suave. A referência **fica** — pendente e com motivo."""
        texto = (motivo or "").strip()
        if not texto:
            raise ReferenciaInvalida(
                "motivo_obrigatorio",
                "suspender sem dizer por quê devolve o silêncio que a RN-12 acaba",
            )
        if self.estado is EstadoDaReferencia.PENDENTE:
            raise ReferenciaInvalida("sem_mudanca", "a referência já está pendente")
        self.estado = EstadoDaReferencia.PENDENTE
        self.motivo = texto[:LIMITE_MOTIVO]
        self._avancar()
        self._emitir(ReferenciaSuspensa, em, referencia_id=self.id, motivo=self.motivo)

    def reativar(self, *, em: datetime) -> None:
        if self.estado is EstadoDaReferencia.ATIVA:
            raise ReferenciaInvalida("sem_mudanca", "a referência já está ativa")
        self.estado = EstadoDaReferencia.ATIVA
        self.motivo = ""
        self._avancar()
        self._emitir(ReferenciaReativada, em, referencia_id=self.id)

    # -- sincronia com o repositório ---------------------------------------------

    def confirmar_gravacao(self) -> None:
        """A gravação passou: a versão em memória passa a ser a versão do banco.

        Chamado pelo adaptador DEPOIS do commit, nunca antes — a mesma regra do
        `Projeto.confirmar_gravacao`, e pelo mesmo motivo: confirmar antes deixaria o
        agregado achando-se sincronizado com um banco que não recebeu nada.
        """
        self.versao_lida = self.versao

    def drenar_eventos(self) -> list[EventoDeDominio]:
        drenados = list(self.eventos)
        self.eventos = ()
        return drenados

    # -- internos ------------------------------------------------------------------

    def _avancar(self) -> None:
        self.versao += 1

    def _emitir(self, classe, em: datetime, **carga) -> None:
        self.eventos = self.eventos + (
            classe(
                projeto_id=self.destino.projeto_id,
                dono=self.dono,
                instante=em,
                **carga,
            ),
        )


def reidratar_referencia(
    *,
    id: UUID,
    tipo: TipoDeReferencia,
    origem: Ponta,
    destino: Ponta,
    dono: DonoDoProjeto,
    criada_em: datetime,
    estado: EstadoDaReferencia = EstadoDaReferencia.ATIVA,
    motivo: str = "",
    versao: int = 1,
) -> ReferenciaCruzada:
    """Monta a referência a partir do que estava GRAVADO — sem emitir evento nenhum.

    Carregar não é criar: se a reidratação emitisse `ReferenciaCriada`, abrir a vista da
    cadeia escreveria história que não aconteceu. `versao_lida` sai preenchida porque o
    agregado tem de saber de que versão partiu — é a base da trava otimista.
    """
    referencia = ReferenciaCruzada(
        id=id,
        tipo=TipoDeReferencia(tipo),
        origem=origem,
        destino=destino,
        dono=dono,
        criada_em=criada_em,
        estado=EstadoDaReferencia(estado),
        motivo=motivo,
        versao=versao,
        criada_por_acao=True,
    )
    referencia.eventos = ()
    referencia.versao_lida = versao
    return referencia


# --------------------------------------------------------------------------------------
# RF-41 — a vista da cadeia: função pura, nos dois sentidos
# --------------------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class EloDaCadeia:
    """Um elo da travessia: o vínculo, as duas pontas e o estado dele."""

    referencia_id: UUID
    tipo: TipoDeReferencia
    origem: Ponta
    destino: Ponta
    estado: EstadoDaReferencia
    motivo: str = ""


@dataclass(frozen=True, slots=True)
class Cadeia:
    """A travessia UDE → NC → injeção → ARF → obstáculo → OI → passo (RF-41)."""

    elos: tuple[EloDaCadeia, ...]

    def ferramentas(self) -> tuple[str, ...]:
        """As ferramentas na ordem em que a cadeia as atravessa, sem repetir a emenda."""
        nomes: list[str] = []
        for elo in self.elos:
            if not nomes or nomes[-1] != elo.origem.ferramenta:
                if elo.origem.ferramenta not in nomes:
                    nomes.append(elo.origem.ferramenta)
            if elo.destino.ferramenta not in nomes:
                nomes.append(elo.destino.ferramenta)
        return tuple(nomes)

    def pendentes(self) -> tuple[EloDaCadeia, ...]:
        return tuple(e for e in self.elos if e.estado is EstadoDaReferencia.PENDENTE)

    def projetos(self) -> tuple[UUID, ...]:
        vistos: list[UUID] = []
        for elo in self.elos:
            for ponta in (elo.origem, elo.destino):
                if ponta.projeto_id not in vistos:
                    vistos.append(ponta.projeto_id)
        return tuple(vistos)

    def resumo(self) -> dict[str, int]:
        return {
            "elos": len(self.elos),
            "elos_pendentes": len(self.pendentes()),
            "ferramentas": len(self.ferramentas()),
            "projetos": len(self.projetos()),
        }


#: A ordem canônica dos vínculos na análise. Serve para desempatar a travessia quando um
#: projeto tem mais de uma saída: a cadeia tem de ser **reprodutível**, senão a mesma
#: análise se lê diferente em dias diferentes e ninguém consegue conferir nada.
ORDEM_DOS_TIPOS: dict[TipoDeReferencia, int] = {
    TipoDeReferencia.PROMOCAO_UDE_NC: 0,
    TipoDeReferencia.SEMEADURA_INJECAO_ARF: 1,
    TipoDeReferencia.DERIVACAO_ARF_APR: 2,
    TipoDeReferencia.DERIVACAO_OI_AT: 3,
}


def _elo(referencia: ReferenciaCruzada) -> EloDaCadeia:
    return EloDaCadeia(
        referencia_id=referencia.id,
        tipo=referencia.tipo,
        origem=referencia.origem,
        destino=referencia.destino,
        estado=referencia.estado,
        motivo=referencia.motivo,
    )


def _ordenadas(referencias: Iterable[ReferenciaCruzada]) -> list[ReferenciaCruzada]:
    return sorted(
        referencias, key=lambda r: (ORDEM_DOS_TIPOS.get(r.tipo, 99), str(r.id))
    )


def travessia(
    referencias: Sequence[ReferenciaCruzada], *, projeto_id: UUID
) -> Cadeia:
    """A cadeia inteira a partir de QUALQUER ponto dela (RF-41, RF-42).

    Sobe até a raiz (o projeto que não é destino de ninguém) e desce dali, em profundidade
    e em ordem canônica. O laço — dado torto vindo do banco — é atravessado uma vez só:
    uma leitura que trava é pior do que uma leitura que mostra o laço.

    Elo **pendente não some**: ele entra na travessia com o estado e o motivo (RF-35), que
    é o requisito inteiro da US-18 — "nunca some em silêncio".
    """
    por_origem: dict[UUID, list[ReferenciaCruzada]] = {}
    por_destino: dict[UUID, list[ReferenciaCruzada]] = {}
    for referencia in referencias:
        por_origem.setdefault(referencia.origem.projeto_id, []).append(referencia)
        por_destino.setdefault(referencia.destino.projeto_id, []).append(referencia)

    # 1. subir até a raiz da análise, sem entrar em laço
    raiz = projeto_id
    visitados: set[UUID] = {raiz}
    while True:
        acima = _ordenadas(por_destino.get(raiz, []))
        acima = [r for r in acima if r.origem.projeto_id not in visitados]
        if not acima:
            break
        raiz = acima[0].origem.projeto_id
        visitados.add(raiz)

    # 2. descer dali em profundidade, cada referência usada uma única vez
    elos: list[EloDaCadeia] = []
    usadas: set[UUID] = set()
    pilha = [raiz]
    while pilha:
        atual = pilha.pop(0)
        for referencia in _ordenadas(por_origem.get(atual, [])):
            if referencia.id in usadas:
                continue
            usadas.add(referencia.id)
            elos.append(_elo(referencia))
            pilha.append(referencia.destino.projeto_id)
    return Cadeia(elos=tuple(elos))


def sincronizar_referencias(
    referencias: Iterable[ReferenciaCruzada],
    *,
    projeto_id: UUID,
    excluido: bool,
    em: datetime,
    motivo: str = "",
) -> tuple[ReferenciaCruzada, ...]:
    """Alinha o estado das referências que tocam um projeto com a existência dele.

    Chamada pelo caso de uso que exclui ou restaura um projeto. É **idempotente** de
    propósito: rodar duas vezes não emite dois eventos, porque o segundo não teria
    acontecido nada para relatar. E **não apaga nada** — RN-12: "apagar referência é ação
    própria, com evento".

    Devolve só as que mudaram, que é o que o traço tem de contar.
    """
    mudadas: list[ReferenciaCruzada] = []
    for referencia in referencias:
        if not referencia.toca(projeto_id):
            continue
        if excluido and referencia.estado is EstadoDaReferencia.ATIVA:
            referencia.suspender(
                motivo=motivo or f"projeto {projeto_id} excluído", em=em
            )
            mudadas.append(referencia)
        elif not excluido and referencia.estado is EstadoDaReferencia.PENDENTE:
            referencia.reativar(em=em)
            mudadas.append(referencia)
    return tuple(mudadas)


__all__ = [
    "ORDEM_DOS_TIPOS",
    "Cadeia",
    "EloDaCadeia",
    "EstadoDaReferencia",
    "Ponta",
    "ReferenciaCruzada",
    "ReferenciaInvalida",
    "TipoDeReferencia",
    "reidratar_referencia",
    "sincronizar_referencias",
    "travessia",
]
