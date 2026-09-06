"""M6 — os cinco passos de focalização, o módulo que dá à aplicação o nome da teoria.

Siglas, uma vez neste arquivo: **M6** — Focalização · **M1** — Núcleo de Diagramas
Lógicos · **TOC** — Teoria das Restrições · **ARA** — Árvore da Realidade Atual · **NC** —
Nuvem de Conflito · **ARF** — Árvore da Realidade Futura · **APR** — Árvore de
Pré-Requisitos · **AT** — Árvore de Transição · **RN/RF/RNF** — regra de negócio /
requisito funcional / requisito não funcional · **DDD** — *Domain-Driven Design* (Design
Orientado a Domínio).

## O que este módulo é, e por que ele não tinha de onde ser copiado

Os cinco passos — identificar a restrição → explorá-la → subordinar tudo o mais a ela →
elevá-la → recomeçar sem deixar a inércia virar a restrição — são o algoritmo central da
TOC, e as árvores lógicas dos módulos M2–M4 são as ferramentas que cada passo usa. Sem
eles, seis ferramentas são seis editores desconexos.

**Este módulo é inteiramente novo.** A prova é negativa e está colada na spec 009 (F-01) e
no ADR 0005: o `grep -rniE "focaliza|five focusing|cinco passos"` sobre as quatro gerações
da linhagem TOC-Builder devolve `0`. Não há modelo a herdar nem defeito de implementação a
corrigir — o que existe é o método, e ele entra aqui como **invariante**, não como texto
de ajuda na tela.

## As quatro decisões que moram no código, e não num documento

1. **Jornada é agregado próprio, não vista sobre as ferramentas** (plano 009, decisão 1).
   A `AnaliseDeFocalizacao` **contém** um `Projeto` do M1 — a mesma composição de
   `ProjetoARA` e `NuvemDeConflito` — e guarda restrição, passos, decisões e vínculos como
   dado seu. Os módulos M2–M4 não ganham campo nenhum: o acoplamento é unidirecional, e é
   ele que permite costurar a jornada por cima de ferramentas já prontas sem tocá-las.
   A diferença estrutural para as ferramentas: **a análise não é diagrama**. Ela não usa
   nó nem aresta; a superfície dela é a jornada e a linha do tempo.

2. **Vínculo opaco no domínio, validado na borda** (decisão 2). Aqui um
   `VinculoDeFerramenta` é `(tipo, projeto, papel, justificativa)` e a única regra é a
   canônica (RN-06). Existência, inquilino e estado do projeto referenciado são conferidos
   **no servidor** (RNF-04) — que é o que faz esta suíte de domínio rodar offline, sem que
   M2, M3 e M4 sequer existam.

3. **Histórico por imutabilidade, não por versionamento** (decisão 3). Ciclo fechado é
   somente leitura (RN-04). Não há *snapshot*, não há *diff*: a linha do tempo é a própria
   lista de ciclos, e ela **cresce, nunca encolhe**. Reabrir um passo acrescenta decisão à
   lista dele em vez de sobrescrever a que estava lá.

4. **Anti-inércia como bloqueio de domínio, não como lembrete de interface** (decisão 4).
   O quinto passo do método de Goldratt não é "volte ao passo 1": é "volte ao passo 1 **e
   não deixe a inércia virar a restrição do sistema**". A segunda metade é a que costuma
   morrer, porque não tem tela óbvia. Aqui ela é invariante: no recomeço toda decisão de
   exploração e de subordinação herda com veredito `pendente`, e o passo `subordinar` do
   ciclo novo **não conclui** enquanto houver pendência (RN-05).

## Uma regra que a spec não escreveu e o método exige

A spec manda herdar as decisões de exploração e subordinação do ciclo que fecha (RF-16).
Ela não diz o que fazer com uma decisão que o ciclo anterior já herdou e **manteve**. Se
"mantida" valesse para sempre, uma regra atravessaria a análise inteira por um julgamento
feito uma vez — que é a definição exata de inércia, e a coisa que o quinto passo existe
para impedir. Por isso o recomeço herda as decisões de exploração e subordinação do ciclo
que fecha **mais as herdadas que aquele ciclo decidiu MANTER**; as revogadas morrem ali,
que é o que revogar quer dizer. Está coberto por
`tests/dominio/test_heranca.py::test_uma_decisao_mantida_volta_a_ser_julgada_no_recomeco_seguinte`.

Camada pura (P3): sem framework, sem rede, sem banco e **sem relógio** — o instante entra
por argumento (`em=`) em toda mutação, como no resto deste domínio.
"""
from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime
from enum import Enum
from typing import Iterable, Sequence
from uuid import UUID, uuid4

from .erros import DadoInvalido, MutacaoRecusada, NaoEncontrado
from .eventos import (
    AnaliseCriada,
    CicloAberto,
    CicloFechado,
    DecisaoHerdadaJulgada,
    EventoDeDominio,
    NotaRegistrada,
    PassoConcluido,
    PassoIniciado,
    PassoReaberto,
    RestricaoEditada,
    RestricaoRegistrada,
    VinculoCriado,
    VinculoRemovido,
)
from .identidade import DonoDoProjeto
from .projeto import Projeto, registrar_raiz_de_ferramenta
from .valores import LIMITE_DESCRICAO, texto as texto_de_dominio

#: O tipo de projeto do M6 (spec 009, RF-01). O M1 nunca precisa saber deste nome.
FERRAMENTA_FOCALIZACAO = "focalizacao"

#: A análise É a raiz do agregado do M6. Registrar-se aqui é o que faz o núcleo do M1
#: recusar mutação de grafo vinda de fora (`Projeto._exigir_raiz`) — e no M6 a recusa é
#: total por construção: a análise não tem nó nem aresta, então nenhuma rota genérica de
#: `/toc/projetos` tem o que fazer com ela.
registrar_raiz_de_ferramenta(FERRAMENTA_FOCALIZACAO, "AnaliseDeFocalizacao")

LIMITE_SISTEMA = 200
LIMITE_RESTRICAO = 300
LIMITE_JUSTIFICATIVA = 4000
LIMITE_DECISAO = 4000
LIMITE_NOTA = 4000
LIMITE_PAPEL = 200
LIMITE_AUTOR = 200


class TipoDePasso(str, Enum):
    """RN-01: cinco, nomeados e ordenados. Não se cria, não se exclui, não se reordena.

    Configurabilidade aqui seria YAGNI puro: o método tem cinco passos há quarenta anos, e
    um motor de *workflow* transformaria a invariante num arquivo de configuração.
    """

    IDENTIFICAR = "identificar"
    EXPLORAR = "explorar"
    SUBORDINAR = "subordinar"
    ELEVAR = "elevar"
    RECOMECAR = "recomecar"


#: A ordem canônica. É desta tupla que sai TUDO: a instanciação do ciclo, o "passo
#: seguinte" da conclusão e o "passo anterior" da reabertura.
ORDEM_CANONICA: tuple[TipoDePasso, ...] = (
    TipoDePasso.IDENTIFICAR,
    TipoDePasso.EXPLORAR,
    TipoDePasso.SUBORDINAR,
    TipoDePasso.ELEVAR,
    TipoDePasso.RECOMECAR,
)


class EstadoDoPasso(str, Enum):
    PENDENTE = "pendente"
    EM_ANDAMENTO = "em_andamento"
    CONCLUIDO = "concluido"


class EstadoDoCiclo(str, Enum):
    ABERTO = "aberto"
    FECHADO = "fechado"


class TipoDeRestricao(str, Enum):
    """L-01: os três tipos clássicos da literatura da TOC, como enum fechado.

    Fechado e não livre porque a linha do tempo compara restrições **entre ciclos**, e
    texto livre faria "capacidade" e "física" virarem duas coisas em análises vizinhas.
    Ampliar é migração aditiva pequena; a decisão está registrada no ADR 0013.
    """

    FISICA = "fisica"
    POLITICA = "politica"
    DE_MERCADO = "de_mercado"


class VereditoDeHeranca(str, Enum):
    """RN-05: `pendente` é o estado de partida; sair dele exige justificativa."""

    PENDENTE = "pendente"
    MANTIDA = "mantida"
    REVOGADA = "revogada"


class TipoDeFerramentaVinculada(str, Enum):
    """RF-14: o vocabulário fechado dos vínculos — as ferramentas dos módulos M2–M4."""

    ARA = "ara"
    NC = "nc"
    ARF = "arf"
    APR = "apr"
    AT = "at"


#: RN-06, como **tabela** e não como `if` espalhado: `identificar`→ARA; `explorar`→NC/ARF;
#: `subordinar`→NC; `elevar`→APR/AT. Fora daqui o vínculo exige justificativa e carrega
#: aviso — o método educa, o dado obedece ao grupo (o mesmo desenho não bloqueante do M2 e
#: do M3). `recomecar` não tem ferramenta canônica: o ato dele é abrir o ciclo seguinte.
FERRAMENTAS_CANONICAS_DO_PASSO: dict[TipoDePasso, frozenset[TipoDeFerramentaVinculada]] = {
    TipoDePasso.IDENTIFICAR: frozenset({TipoDeFerramentaVinculada.ARA}),
    TipoDePasso.EXPLORAR: frozenset(
        {TipoDeFerramentaVinculada.NC, TipoDeFerramentaVinculada.ARF}
    ),
    TipoDePasso.SUBORDINAR: frozenset({TipoDeFerramentaVinculada.NC}),
    TipoDePasso.ELEVAR: frozenset(
        {TipoDeFerramentaVinculada.APR, TipoDeFerramentaVinculada.AT}
    ),
    TipoDePasso.RECOMECAR: frozenset(),
}

#: RN-05 / L-02: os passos cuja decisão **sobrevive por inércia**.
#:
#: A leitura direta do quinto passo do método: o que atravessa um ciclo por conta própria
#: são **regras de operação** — como se explora a restrição e a que ela subordina o resto.
#: A decisão de `identificar` morre com o ciclo (a restrição dela foi quebrada; é por isso
#: que se recomeçou) e a de `elevar` é um plano executado, não uma regra vigente.
PASSOS_QUE_GERAM_INERCIA: tuple[TipoDePasso, ...] = (
    TipoDePasso.EXPLORAR,
    TipoDePasso.SUBORDINAR,
)


# ---------------------------------------------------------------------------------------
# Erros — cada um com a REGRA nomeada, para a borda traduzir sem adivinhar por texto
# ---------------------------------------------------------------------------------------


class PassoInvalido(MutacaoRecusada):
    """`regra`: `ordem_canonica` · `passo_fora_de_vez` · `sem_restricao` ·
    `decisao_obrigatoria` · `heranca_pendente` · `recomecar_nao_conclui` ·
    `sem_passo_anterior` · `justificativa_obrigatoria`."""

    def __init__(self, regra: str, detalhe: str = "") -> None:
        super().__init__(f"{regra}: {detalhe}" if detalhe else regra)
        self.regra = regra


class CicloInvalido(MutacaoRecusada):
    """`regra`: `ciclo_fechado` · `ja_ha_ciclo_aberto` · `sem_ciclo_aberto` ·
    `recomeco_fora_do_passo`."""

    def __init__(self, regra: str, detalhe: str = "") -> None:
        super().__init__(f"{regra}: {detalhe}" if detalhe else regra)
        self.regra = regra


class RestricaoInvalida(MutacaoRecusada):
    """`regra`: `restricao_ja_registrada` · `sem_restricao` · `nada_a_editar`."""

    def __init__(self, regra: str, detalhe: str = "") -> None:
        super().__init__(f"{regra}: {detalhe}" if detalhe else regra)
        self.regra = regra


class VinculoInvalido(MutacaoRecusada):
    """`regra`: `justificativa_obrigatoria` · `vinculo_duplicado`."""

    def __init__(self, regra: str, detalhe: str = "") -> None:
        super().__init__(f"{regra}: {detalhe}" if detalhe else regra)
        self.regra = regra


class HerancaInvalida(MutacaoRecusada):
    """`regra`: `justificativa_obrigatoria` · `veredito_invalido`."""

    def __init__(self, regra: str, detalhe: str = "") -> None:
        super().__init__(f"{regra}: {detalhe}" if detalhe else regra)
        self.regra = regra


# ---------------------------------------------------------------------------------------
# Objetos de valor
# ---------------------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class SistemaAnalisado:
    """O sistema cuja meta a análise serve — nome e descrição (F6.1.1).

    Sem ele a pergunta "restrição de quê?" não tem resposta, e uma restrição sem sistema é
    uma frase, não um alvo.
    """

    nome: str
    descricao: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "nome",
            texto_de_dominio(self.nome, campo="sistema.nome", minimo=1, maximo=LIMITE_SISTEMA),
        )
        object.__setattr__(
            self,
            "descricao",
            texto_de_dominio(
                self.descricao, campo="sistema.descricao", minimo=0, maximo=LIMITE_DESCRICAO
            ),
        )


@dataclass(frozen=True, slots=True)
class ReferenciaDeOrigemDaRestricao:
    """INT-02: de onde a restrição veio — a causa raiz de uma ARA, tipada.

    Tipada é o ponto, e é a mesma lição da `ReferenciaDeOrigem` do M3: na linhagem, "de
    onde isto veio" não existia em modelo nenhum. Aqui é dado do agregado — ferramenta,
    projeto e o nó exato —, e a navegação de volta resolve por consulta ao M6, **sem
    campo novo na ARA** (L-03).
    """

    ferramenta: str
    projeto_id: UUID
    no_id: UUID

    def __post_init__(self) -> None:
        if not (self.ferramenta or "").strip():
            raise DadoInvalido("origem: ferramenta de origem é obrigatória")
        if self.projeto_id is None or self.no_id is None:
            raise DadoInvalido("origem: projeto e nó de origem são obrigatórios")
        object.__setattr__(self, "ferramenta", self.ferramenta.strip())


@dataclass(frozen=True, slots=True)
class DecisaoDePasso:
    """RF-09: o texto que encerra um passo, com autor e data. Nunca se sobrescreve."""

    texto: str
    autor: str
    instante: datetime

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "texto",
            texto_de_dominio(self.texto, campo="decisao", minimo=1, maximo=LIMITE_DECISAO),
        )
        object.__setattr__(
            self,
            "autor",
            texto_de_dominio(self.autor, campo="decisao.autor", minimo=1, maximo=LIMITE_AUTOR),
        )


@dataclass(frozen=True, slots=True)
class NotaDePasso:
    """RF-11: texto livre acumulável, com autoria — distinto da decisão de conclusão."""

    id: UUID
    texto: str
    autor: str
    instante: datetime

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "texto",
            texto_de_dominio(self.texto, campo="nota", minimo=1, maximo=LIMITE_NOTA),
        )
        object.__setattr__(
            self,
            "autor",
            texto_de_dominio(self.autor, campo="nota.autor", minimo=1, maximo=LIMITE_AUTOR),
        )


@dataclass(frozen=True, slots=True)
class Reabertura:
    """RF-10: a reabertura é FATO registrado ao lado da decisão, nunca no lugar dela."""

    justificativa: str
    autor: str
    instante: datetime


@dataclass(frozen=True, slots=True)
class VinculoDeFerramenta:
    """RF-14: referência tipada a um projeto de outra ferramenta. **Nunca cópia.**

    Os seis campos são o contrato inteiro: identidade, tipo, projeto, papel do vínculo no
    passo, justificativa (obrigatória fora do canônico) e se ele é canônico. Não há campo
    de conteúdo aqui de propósito — um título de nó ou um texto de obstáculo copiado para
    dentro do M6 seria a sétima cópia que o núcleo M1 existe para impedir, e envelheceria
    no primeiro `PUT` do outro módulo.
    """

    id: UUID
    tipo: TipoDeFerramentaVinculada
    projeto_id: UUID
    papel: str = ""
    justificativa: str = ""
    canonico: bool = True


@dataclass(slots=True)
class DecisaoHerdada:
    """RN-05: uma regra de operação do ciclo anterior, esperando veredito.

    Mutável de propósito — ela existe para RECEBER um julgamento. O que não muda é o
    `texto`: a decisão herdada é o que a pessoa escreveu no ciclo passado, e reescrevê-la
    aqui seria apagar história para não ter de julgá-la.
    """

    id: UUID
    ciclo_de_origem: int
    passo: TipoDePasso
    texto: str
    veredito: VereditoDeHeranca = VereditoDeHeranca.PENDENTE
    justificativa: str = ""
    autor: str = ""
    julgada_em: datetime | None = None

    def __post_init__(self) -> None:
        self.passo = TipoDePasso(self.passo)
        self.veredito = VereditoDeHeranca(self.veredito)

    @property
    def pendente(self) -> bool:
        return self.veredito is VereditoDeHeranca.PENDENTE


@dataclass(slots=True)
class Restricao:
    """A entidade que dá nome à teoria — e a que o round 009 marca "nunca sai" (F-04).

    Até este módulo, a aplicação inteira sabia desenhar as ferramentas da TOC e não sabia
    dizer **qual é a restrição**. É esta classe que fecha esse buraco.
    """

    id: UUID
    descricao: str
    tipo: TipoDeRestricao
    justificativa: str
    autor: str
    registrada_em: datetime
    origem: ReferenciaDeOrigemDaRestricao | None = None

    def __post_init__(self) -> None:
        self.descricao = texto_de_dominio(
            self.descricao, campo="restricao.descricao", minimo=1, maximo=LIMITE_RESTRICAO
        )
        self.justificativa = texto_de_dominio(
            self.justificativa,
            campo="restricao.justificativa",
            minimo=1,
            maximo=LIMITE_JUSTIFICATIVA,
        )
        self.autor = texto_de_dominio(
            self.autor, campo="restricao.autor", minimo=1, maximo=LIMITE_AUTOR
        )
        self.tipo = TipoDeRestricao(self.tipo)

    def retrato(self) -> tuple:
        return (
            str(self.id),
            self.descricao,
            self.tipo.value,
            self.justificativa,
            self.autor,
            None if self.origem is None
            else (self.origem.ferramenta, str(self.origem.projeto_id), str(self.origem.no_id)),
        )


# ---------------------------------------------------------------------------------------
# Entidades do agregado
# ---------------------------------------------------------------------------------------


@dataclass(slots=True)
class PassoDeFocalizacao:
    """Um dos cinco. O `tipo` é imutável — quem cria os passos é o ciclo, na origem."""

    tipo: TipoDePasso
    estado: EstadoDoPasso = EstadoDoPasso.PENDENTE
    #: TODAS as decisões que já concluíram este passo, em ordem. Reabrir e concluir de
    #: novo **acrescenta**; a lista nunca encolhe (RN-04).
    decisoes: tuple[DecisaoDePasso, ...] = ()
    notas: tuple[NotaDePasso, ...] = ()
    vinculos: tuple[VinculoDeFerramenta, ...] = ()
    reaberturas: tuple[Reabertura, ...] = ()

    def __post_init__(self) -> None:
        self.tipo = TipoDePasso(self.tipo)
        self.estado = EstadoDoPasso(self.estado)
        self.decisoes = tuple(self.decisoes)
        self.notas = tuple(self.notas)
        self.vinculos = tuple(self.vinculos)
        self.reaberturas = tuple(self.reaberturas)

    @property
    def decisao(self) -> DecisaoDePasso | None:
        """A decisão VIGENTE — a última registrada. As anteriores continuam em `decisoes`."""
        return self.decisoes[-1] if self.decisoes else None

    @property
    def canonicas(self) -> frozenset[TipoDeFerramentaVinculada]:
        return FERRAMENTAS_CANONICAS_DO_PASSO[self.tipo]

    def vinculo(self, vinculo_id: UUID) -> VinculoDeFerramenta:
        for candidato in self.vinculos:
            if candidato.id == vinculo_id:
                return candidato
        raise NaoEncontrado(f"vinculo:{vinculo_id}")

    def avisos(self) -> tuple[str, ...]:
        """RN-06: um aviso por vínculo fora do canônico. Aviso — nunca pendência."""
        return tuple(
            f"o vínculo com {v.tipo.value} não é canônico do passo {self.tipo.value}; "
            f"as combinações canônicas são "
            f"{sorted(c.value for c in self.canonicas) or ['nenhuma']}"
            for v in self.vinculos
            if not v.canonico
        )

    def retrato(self) -> tuple:
        """O CONTEÚDO que as pessoas escreveram — a base da prova do RN-04."""
        return (
            self.tipo.value,
            tuple((d.texto, d.autor, d.instante.isoformat()) for d in self.decisoes),
            tuple((n.texto, n.autor, n.instante.isoformat()) for n in self.notas),
            tuple(
                (str(v.id), v.tipo.value, str(v.projeto_id), v.papel, v.justificativa, v.canonico)
                for v in self.vinculos
            ),
            tuple((r.justificativa, r.autor, r.instante.isoformat()) for r in self.reaberturas),
        )


@dataclass(slots=True)
class CicloDeFocalizacao:
    """Uma volta completa dos cinco passos — a unidade da linha do tempo (F6.1.1)."""

    id: UUID
    ordem: int
    aberto_em: datetime
    passos: tuple[PassoDeFocalizacao, ...]
    estado: EstadoDoCiclo = EstadoDoCiclo.ABERTO
    fechado_em: datetime | None = None
    restricao: Restricao | None = None
    heranca: tuple[DecisaoHerdada, ...] = ()

    def __post_init__(self) -> None:
        self.estado = EstadoDoCiclo(self.estado)
        self.passos = tuple(self.passos)
        self.heranca = tuple(self.heranca)
        tipos = tuple(p.tipo for p in self.passos)
        if tipos != ORDEM_CANONICA:
            raise PassoInvalido(
                "ordem_canonica",
                f"um ciclo tem os cinco passos na ordem "
                f"{[t.value for t in ORDEM_CANONICA]}; vieram {[t.value for t in tipos]}",
            )

    # -- consultas ---------------------------------------------------------------

    def passo(self, tipo: TipoDePasso | str) -> PassoDeFocalizacao:
        try:
            alvo = TipoDePasso(tipo)
        except ValueError as erro:
            raise NaoEncontrado(f"passo:{tipo}") from erro
        for candidato in self.passos:
            if candidato.tipo is alvo:
                return candidato
        raise NaoEncontrado(f"passo:{alvo.value}")  # pragma: no cover - a invariante impede

    @property
    def passo_atual(self) -> PassoDeFocalizacao:
        """O primeiro que não está concluído — em andamento ou pendente."""
        for candidato in self.passos:
            if candidato.estado is not EstadoDoPasso.CONCLUIDO:
                return candidato
        return self.passos[-1]

    @property
    def concluidos(self) -> int:
        return sum(1 for p in self.passos if p.estado is EstadoDoPasso.CONCLUIDO)

    @property
    def aberto(self) -> bool:
        return self.estado is EstadoDoCiclo.ABERTO

    def herancas_pendentes(self) -> tuple[DecisaoHerdada, ...]:
        return tuple(h for h in self.heranca if h.pendente)

    def decisao_herdada(self, decisao_id: UUID) -> DecisaoHerdada:
        for candidata in self.heranca:
            if candidata.id == decisao_id:
                return candidata
        raise NaoEncontrado(f"decisao_herdada:{decisao_id}")

    def exigir_aberto(self, operacao: str) -> None:
        """RN-04: ciclo fechado é somente leitura NO DOMÍNIO, não na tela."""
        if not self.aberto:
            raise CicloInvalido(
                "ciclo_fechado",
                f"{operacao}: o ciclo {self.ordem} está fechado desde "
                f"{self.fechado_em}; histórico é apêndice, nunca sobrescrita (RN-04)",
            )

    def retrato(self) -> tuple:
        """O conteúdo escrito pelas pessoas: restrição, passos e herança julgada.

        **Não inclui o ciclo de vida** (estado do ciclo, estado dos passos) de propósito.
        É este retrato que o teste do RN-04 compara antes e depois do recomeço: o que não
        pode mudar é o que alguém escreveu; o que muda, e só isso, é o ciclo passar de
        aberto a fechado e o quinto passo de em andamento a concluído, porque o recomeço
        **é** o ato daquele passo (RN-07).
        """
        return (
            self.ordem,
            None if self.restricao is None else self.restricao.retrato(),
            tuple(p.retrato() for p in self.passos),
            tuple(
                (str(h.id), h.ciclo_de_origem, h.passo.value, h.texto, h.veredito.value,
                 h.justificativa, h.autor)
                for h in self.heranca
            ),
        )


def _novos_passos() -> tuple[PassoDeFocalizacao, ...]:
    """RN-01: os cinco passos nascem juntos, e `identificar` já nasce em andamento."""
    return tuple(
        PassoDeFocalizacao(
            tipo=tipo,
            estado=(
                EstadoDoPasso.EM_ANDAMENTO
                if tipo is TipoDePasso.IDENTIFICAR
                else EstadoDoPasso.PENDENTE
            ),
        )
        for tipo in ORDEM_CANONICA
    )


# ---------------------------------------------------------------------------------------
# O agregado
# ---------------------------------------------------------------------------------------


@dataclass(slots=True)
class AnaliseDeFocalizacao:
    """A raiz: um `Projeto` do M1 mais a jornada dos cinco passos.

    Toda mutação entra por aqui. Os ciclos e os passos são entidades do agregado e não têm
    caminho próprio de escrita — quem guarda a coleção é a raiz, e o que ela devolve são
    tuplas.
    """

    projeto: Projeto
    sistema: SistemaAnalisado
    _ciclos: list[CicloDeFocalizacao] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.projeto.ferramenta != FERRAMENTA_FOCALIZACAO:
            raise MutacaoRecusada(
                f"AnaliseDeFocalizacao exige ferramenta {FERRAMENTA_FOCALIZACAO!r}, "
                f"veio {self.projeto.ferramenta!r}"
            )

    # -- consultas ---------------------------------------------------------------

    @property
    def id(self) -> UUID:
        return self.projeto.id

    @property
    def dono(self) -> DonoDoProjeto:
        return self.projeto.dono

    @property
    def ciclos(self) -> tuple[CicloDeFocalizacao, ...]:
        return tuple(self._ciclos)

    @property
    def ciclo_aberto(self) -> CicloDeFocalizacao:
        for ciclo in self._ciclos:
            if ciclo.aberto:
                return ciclo
        raise CicloInvalido(
            "sem_ciclo_aberto",
            "a análise não tem ciclo aberto; abrir um exige recomeçar (RN-02)",
        )

    def ciclo(self, ciclo_id: UUID) -> CicloDeFocalizacao:
        for candidato in self._ciclos:
            if candidato.id == ciclo_id:
                return candidato
        raise NaoEncontrado(f"ciclo:{ciclo_id}")

    @property
    def passo_atual(self) -> PassoDeFocalizacao:
        return self.ciclo_aberto.passo_atual

    @property
    def eventos(self) -> tuple[EventoDeDominio, ...]:
        return self.projeto.eventos

    def drenar_eventos(self) -> list[EventoDeDominio]:
        return self.projeto.drenar_eventos()

    def vinculos_do_projeto(
        self, projeto_id: UUID
    ) -> tuple[tuple[TipoDePasso, VinculoDeFerramenta], ...]:
        """L-03: a navegação de volta — de um projeto de ferramenta para esta análise.

        Consulta pura sobre o agregado, e por isso **nenhum campo novo** nasce em M2–M4.
        Se um dia a escala provar que a consulta não basta, um índice materializado resolve
        sem tocar nos agregados das ferramentas.
        """
        achados: list[tuple[TipoDePasso, VinculoDeFerramenta]] = []
        for ciclo in self._ciclos:
            for passo in ciclo.passos:
                for vinculo in passo.vinculos:
                    if vinculo.projeto_id == projeto_id:
                        achados.append((passo.tipo, vinculo))
        return tuple(achados)

    def projetos_vinculados(self) -> tuple[UUID, ...]:
        """Os identificadores que a borda tem de validar contra M2–M4 (RNF-04)."""
        vistos: list[UUID] = []
        for _, vinculo in self.vinculos_do_projeto_todos():
            if vinculo.projeto_id not in vistos:
                vistos.append(vinculo.projeto_id)
        return tuple(vistos)

    def vinculos_do_projeto_todos(
        self,
    ) -> tuple[tuple[TipoDePasso, VinculoDeFerramenta], ...]:
        return tuple(
            (passo.tipo, vinculo)
            for ciclo in self._ciclos
            for passo in ciclo.passos
            for vinculo in passo.vinculos
        )

    def linha_do_tempo(self) -> tuple["EntradaDaLinhaDoTempo", ...]:
        """RF-17: os ciclos em ordem, com restrição, datas e desfecho."""
        return tuple(
            EntradaDaLinhaDoTempo(
                ciclo_id=c.id,
                ordem=c.ordem,
                estado=c.estado,
                restricao=None if c.restricao is None else c.restricao.descricao,
                tipo_de_restricao=None if c.restricao is None else c.restricao.tipo,
                aberto_em=c.aberto_em,
                fechado_em=c.fechado_em,
                decisoes=sum(len(p.decisoes) for p in c.passos),
                vinculos=sum(len(p.vinculos) for p in c.passos),
                herancas=len(c.heranca),
                herancas_pendentes=len(c.herancas_pendentes()),
                passo_atual=c.passo_atual.tipo,
            )
            for c in self._ciclos
        )

    # -- ciclo de vida do M1, herdado sem reimplementação (RF-01, RF-04) ---------

    def renomear(self, nome: str, *, em: datetime) -> None:
        self.projeto.renomear(nome, em=em)

    def descrever_sistema(self, *, nome: str | None = None, descricao: str | None = None,
                          em: datetime) -> SistemaAnalisado:
        self.projeto._exigir_ativo("descrever_sistema")
        self.sistema = SistemaAnalisado(
            nome=self.sistema.nome if nome is None else nome,
            descricao=self.sistema.descricao if descricao is None else descricao,
        )
        self.projeto.descrever_problema(self.sistema.descricao, em=em)
        return self.sistema

    def excluir(self, *, em: datetime) -> None:
        """RF-04: exclusão suave do M1 — ciclos, passos, restrições e vínculos juntos."""
        self.projeto.excluir(em=em)

    def restaurar(self, *, em: datetime) -> None:
        self.projeto.restaurar(em=em)

    # -- RN-01: a ordem canônica não se mexe -------------------------------------

    def adicionar_passo(self, *_: object, **__: object) -> PassoDeFocalizacao:
        raise PassoInvalido(
            "ordem_canonica",
            "os cinco passos nascem com o ciclo e não se criam (RN-01)",
        )

    def excluir_passo(self, *_: object, **__: object) -> None:
        raise PassoInvalido(
            "ordem_canonica",
            "passo de focalização não se exclui: o método tem cinco, sempre (RN-01)",
        )

    def reordenar_passos(self, *_: object, **__: object) -> None:
        raise PassoInvalido(
            "ordem_canonica",
            f"a ordem é fixa: {[t.value for t in ORDEM_CANONICA]} (RN-01)",
        )

    # -- RF-05..RF-07: a restrição ------------------------------------------------

    def registrar_restricao(
        self,
        *,
        descricao: str,
        tipo: TipoDeRestricao | str,
        justificativa: str,
        autor: str,
        em: datetime,
        origem: ReferenciaDeOrigemDaRestricao | None = None,
        restricao_id: UUID | None = None,
    ) -> Restricao:
        """RF-05/RF-06: no máximo uma restrição vigente por ciclo (RN-03)."""
        self.projeto._exigir_ativo("registrar_restricao")
        ciclo = self.ciclo_aberto
        ciclo.exigir_aberto("registrar_restricao")
        if ciclo.restricao is not None:
            raise RestricaoInvalida(
                "restricao_ja_registrada",
                f"o ciclo {ciclo.ordem} já aponta para {ciclo.restricao.descricao!r}; "
                "mudar o alvo da análise não é editar a restrição — é recomeçar (RN-03)",
            )
        restricao = Restricao(
            id=restricao_id or uuid4(),
            descricao=descricao,
            tipo=TipoDeRestricao(tipo),
            justificativa=justificativa,
            autor=autor,
            registrada_em=em,
            origem=origem,
        )
        ciclo.restricao = restricao
        self.projeto._avancar(em)
        self._emitir(
            RestricaoRegistrada,
            em,
            restricao_id=restricao.id,
            ciclo_id=ciclo.id,
            tipo=restricao.tipo.value,
            autor=restricao.autor,
            origem_ferramenta="" if origem is None else origem.ferramenta,
            origem_projeto_id=None if origem is None else origem.projeto_id,
            origem_no_id=None if origem is None else origem.no_id,
        )
        return restricao

    def editar_restricao(
        self,
        *,
        em: datetime,
        descricao: str | None = None,
        justificativa: str | None = None,
    ) -> Restricao:
        """RF-07: descrição e justificativa. **O tipo não entra** — trocar alvo é recomeço.

        A assinatura é `keyword-only` e não tem `tipo` de propósito: quem tentar mudar o
        tipo recebe `TypeError` do próprio Python, e não uma recusa que alguém possa
        esquecer de escrever. A regra vira impossibilidade em vez de disciplina.
        """
        self.projeto._exigir_ativo("editar_restricao")
        ciclo = self.ciclo_aberto
        ciclo.exigir_aberto("editar_restricao")
        if ciclo.restricao is None:
            raise RestricaoInvalida(
                "sem_restricao", f"o ciclo {ciclo.ordem} ainda não registrou a restrição"
            )
        campos: list[str] = []
        if descricao is not None:
            ciclo.restricao.descricao = texto_de_dominio(
                descricao, campo="restricao.descricao", minimo=1, maximo=LIMITE_RESTRICAO
            )
            campos.append("descricao")
        if justificativa is not None:
            ciclo.restricao.justificativa = texto_de_dominio(
                justificativa,
                campo="restricao.justificativa",
                minimo=1,
                maximo=LIMITE_JUSTIFICATIVA,
            )
            campos.append("justificativa")
        if not campos:
            raise RestricaoInvalida("nada_a_editar", "informe descrição ou justificativa")
        self.projeto._avancar(em)
        self._emitir(
            RestricaoEditada,
            em,
            restricao_id=ciclo.restricao.id,
            campos=tuple(campos),
        )
        return ciclo.restricao

    # -- RF-09..RF-11: avanço, reabertura e notas ---------------------------------

    def concluir_passo(
        self, tipo: TipoDePasso | str, *, decisao: str, autor: str, em: datetime
    ) -> PassoDeFocalizacao:
        """RF-09: o avanço é ato explícito, com a decisão que o encerra.

        A ordem das recusas não é acidental — ela vai da forma ao conteúdo, para a
        mensagem apontar sempre o obstáculo mais próximo de quem pediu.
        """
        self.projeto._exigir_ativo("concluir_passo")
        ciclo = self.ciclo_aberto
        ciclo.exigir_aberto("concluir_passo")
        passo = ciclo.passo(tipo)

        if passo.tipo is TipoDePasso.RECOMECAR:
            raise PassoInvalido(
                "recomecar_nao_conclui",
                "o quinto passo não tem decisão de conclusão própria: o ato dele é "
                "recomeçar (RN-07)",
            )
        if ciclo.passo_atual.tipo is not passo.tipo:
            raise PassoInvalido(
                "passo_fora_de_vez",
                f"o passo em andamento é {ciclo.passo_atual.tipo.value!r}; a conclusão "
                f"avança um passo por vez (RN-01)",
            )
        if not (decisao or "").strip():
            raise PassoInvalido(
                "decisao_obrigatoria",
                f"concluir {passo.tipo.value} exige a decisão que o encerra (RF-09)",
            )
        if passo.tipo is TipoDePasso.IDENTIFICAR and ciclo.restricao is None:
            raise PassoInvalido(
                "sem_restricao",
                "identificar não conclui sem restrição registrada (RF-08) — é o passo "
                "cujo produto é a restrição",
            )
        if passo.tipo is TipoDePasso.SUBORDINAR:
            pendentes = ciclo.herancas_pendentes()
            if pendentes:
                raise PassoInvalido(
                    "heranca_pendente",
                    f"{len(pendentes)} decisão(ões) herdada(s) do ciclo anterior ainda "
                    "sem veredito; manter é decisão tão explícita quanto revogar, e a "
                    "inércia não pode virar a restrição (RN-05)",
                )

        registrada = DecisaoDePasso(texto=decisao, autor=autor, instante=em)
        passo.decisoes = passo.decisoes + (registrada,)
        passo.estado = EstadoDoPasso.CONCLUIDO
        self.projeto._avancar(em)
        self._emitir(
            PassoConcluido,
            em,
            passo=passo.tipo.value,
            ciclo_id=ciclo.id,
            autor=registrada.autor,
            decisao=registrada.texto,
        )
        seguinte = self._seguinte(passo.tipo)
        if seguinte is not None:
            proximo = ciclo.passo(seguinte)
            if proximo.estado is EstadoDoPasso.PENDENTE:
                proximo.estado = EstadoDoPasso.EM_ANDAMENTO
                self._emitir(PassoIniciado, em, passo=proximo.tipo.value, ciclo_id=ciclo.id)
        return passo

    def reabrir_passo_anterior(
        self, *, justificativa: str, autor: str, em: datetime
    ) -> PassoDeFocalizacao:
        """RF-10: o passo imediatamente anterior volta — **sem apagar** a decisão dele."""
        self.projeto._exigir_ativo("reabrir_passo_anterior")
        ciclo = self.ciclo_aberto
        ciclo.exigir_aberto("reabrir_passo_anterior")
        motivo = (justificativa or "").strip()
        if not motivo:
            raise PassoInvalido(
                "justificativa_obrigatoria",
                "reabrir um passo concluído exige dizer por quê (RF-10)",
            )
        atual = ciclo.passo_atual
        anterior_tipo = self._anterior(atual.tipo)
        if anterior_tipo is None:
            raise PassoInvalido(
                "sem_passo_anterior",
                f"{atual.tipo.value} é o primeiro passo do ciclo: não há anterior a reabrir",
            )
        anterior = ciclo.passo(anterior_tipo)
        if anterior.estado is not EstadoDoPasso.CONCLUIDO:
            raise PassoInvalido(
                "sem_passo_anterior",
                f"o passo {anterior_tipo.value} não está concluído",
            )
        anterior.estado = EstadoDoPasso.EM_ANDAMENTO
        anterior.reaberturas = anterior.reaberturas + (
            Reabertura(justificativa=motivo, autor=autor, instante=em),
        )
        if atual.estado is EstadoDoPasso.EM_ANDAMENTO:
            atual.estado = EstadoDoPasso.PENDENTE
        self.projeto._avancar(em)
        self._emitir(
            PassoReaberto,
            em,
            passo=anterior.tipo.value,
            ciclo_id=ciclo.id,
            autor=autor,
            justificativa=motivo,
        )
        return anterior

    def anotar_passo(
        self, tipo: TipoDePasso | str, *, texto: str, autor: str, em: datetime,
        nota_id: UUID | None = None,
    ) -> NotaDePasso:
        """RF-11: anotar NÃO conclui e NÃO avança — o avanço é ato explícito (RN-01)."""
        self.projeto._exigir_ativo("anotar_passo")
        ciclo = self.ciclo_aberto
        ciclo.exigir_aberto("anotar_passo")
        passo = ciclo.passo(tipo)
        nota = NotaDePasso(id=nota_id or uuid4(), texto=texto, autor=autor, instante=em)
        passo.notas = passo.notas + (nota,)
        self.projeto._avancar(em)
        self._emitir(
            NotaRegistrada, em, passo=passo.tipo.value, nota_id=nota.id, autor=nota.autor
        )
        return nota

    # -- RF-14 / RN-06: os vínculos de ferramenta ---------------------------------

    def vincular_ferramenta(
        self,
        tipo_do_passo: TipoDePasso | str,
        *,
        tipo: TipoDeFerramentaVinculada | str,
        projeto_id: UUID,
        papel: str = "",
        justificativa: str = "",
        em: datetime,
        vinculo_id: UUID | None = None,
    ) -> VinculoDeFerramenta:
        """Cada passo aponta a ferramenta certa — por TIPO, nunca por texto na descrição."""
        self.projeto._exigir_ativo("vincular_ferramenta")
        ciclo = self.ciclo_aberto
        ciclo.exigir_aberto("vincular_ferramenta")
        passo = ciclo.passo(tipo_do_passo)
        try:
            ferramenta = TipoDeFerramentaVinculada(tipo)
        except ValueError as erro:
            raise DadoInvalido(
                f"vinculo: ferramenta desconhecida {tipo!r}; esperado uma de "
                f"{[f.value for f in TipoDeFerramentaVinculada]}"
            ) from erro

        canonico = ferramenta in passo.canonicas
        motivo = (justificativa or "").strip()
        if not canonico and not motivo:
            raise VinculoInvalido(
                "justificativa_obrigatoria",
                f"{ferramenta.value} não é canônica do passo {passo.tipo.value}; vincular "
                f"fora do canônico exige justificativa (RN-06) — as canônicas são "
                f"{sorted(c.value for c in passo.canonicas) or ['nenhuma']}",
            )
        if any(
            v.tipo is ferramenta and v.projeto_id == projeto_id for v in passo.vinculos
        ):
            raise VinculoInvalido(
                "vinculo_duplicado",
                f"o passo {passo.tipo.value} já referencia este projeto {ferramenta.value}",
            )

        vinculo = VinculoDeFerramenta(
            id=vinculo_id or uuid4(),
            tipo=ferramenta,
            projeto_id=projeto_id,
            papel=texto_de_dominio(papel, campo="vinculo.papel", minimo=0, maximo=LIMITE_PAPEL),
            justificativa=motivo,
            canonico=canonico,
        )
        passo.vinculos = passo.vinculos + (vinculo,)
        self.projeto._avancar(em)
        self._emitir(
            VinculoCriado,
            em,
            vinculo_id=vinculo.id,
            passo=passo.tipo.value,
            ferramenta=ferramenta.value,
            alvo_projeto_id=projeto_id,
            canonico=canonico,
        )
        return vinculo

    def remover_vinculo(
        self, tipo_do_passo: TipoDePasso | str, vinculo_id: UUID, *, em: datetime
    ) -> None:
        self.projeto._exigir_ativo("remover_vinculo")
        ciclo = self.ciclo_aberto
        ciclo.exigir_aberto("remover_vinculo")
        passo = ciclo.passo(tipo_do_passo)
        alvo = passo.vinculo(vinculo_id)
        passo.vinculos = tuple(v for v in passo.vinculos if v.id != alvo.id)
        self.projeto._avancar(em)
        self._emitir(VinculoRemovido, em, vinculo_id=alvo.id, passo=passo.tipo.value)

    # -- RN-05: o julgamento da herança -------------------------------------------

    def julgar_heranca(
        self,
        decisao_id: UUID,
        *,
        veredito: VereditoDeHeranca | str,
        justificativa: str,
        autor: str,
        em: datetime,
    ) -> DecisaoHerdada:
        """Manter é decisão tão explícita quanto revogar — as duas exigem justificativa."""
        self.projeto._exigir_ativo("julgar_heranca")
        ciclo = self.ciclo_aberto
        ciclo.exigir_aberto("julgar_heranca")
        herdada = ciclo.decisao_herdada(decisao_id)
        try:
            novo = VereditoDeHeranca(veredito)
        except ValueError as erro:
            raise HerancaInvalida(
                "veredito_invalido",
                f"veredito {veredito!r} fora do vocabulário "
                f"{[v.value for v in VereditoDeHeranca]}",
            ) from erro
        if novo is VereditoDeHeranca.PENDENTE:
            raise HerancaInvalida(
                "veredito_invalido",
                "um veredito não volta a `pendente`: isso apagaria um julgamento, e "
                "histórico é apêndice (RN-04)",
            )
        motivo = (justificativa or "").strip()
        if not motivo:
            raise HerancaInvalida(
                "justificativa_obrigatoria",
                f"{novo.value} exige justificativa: manter sem dizer por quê é exatamente "
                "a inércia que a RN-05 impede",
            )
        herdada.veredito = novo
        herdada.justificativa = motivo
        herdada.autor = texto_de_dominio(
            autor, campo="heranca.autor", minimo=1, maximo=LIMITE_AUTOR
        )
        herdada.julgada_em = em
        self.projeto._avancar(em)
        self._emitir(
            DecisaoHerdadaJulgada,
            em,
            decisao_id=herdada.id,
            ciclo_id=ciclo.id,
            passo_de_origem=herdada.passo.value,
            veredito=novo.value,
            autor=herdada.autor,
        )
        return herdada

    def julgar_todas_as_herancas(
        self, *, veredito: VereditoDeHeranca | str, justificativa: str, autor: str,
        em: datetime,
    ) -> int:
        """Atalho de conveniência para o mesmo veredito em bloco. Devolve quantas julgou.

        Existe porque a alternativa — a borda iterar e chamar N vezes — colocaria o laço
        fora da raiz do agregado. Cada julgamento continua emitindo o seu evento.
        """
        pendentes = self.ciclo_aberto.herancas_pendentes()
        for herdada in pendentes:
            self.julgar_heranca(
                herdada.id,
                veredito=veredito,
                justificativa=justificativa,
                autor=autor,
                em=em,
            )
        return len(pendentes)

    # -- RF-15/RF-16: o recomeço ---------------------------------------------------

    def abrir_ciclo(self, *, em: datetime, herdadas: Sequence[DecisaoHerdada] = ()) -> CicloDeFocalizacao:
        """RN-02: no máximo um ciclo aberto. Abrir com um aberto é recusado, sempre."""
        self.projeto._exigir_ativo("abrir_ciclo")
        if any(c.aberto for c in self._ciclos):
            raise CicloInvalido(
                "ja_ha_ciclo_aberto",
                "uma análise tem no máximo um ciclo aberto; abrir outro exige fechar o "
                "atual pelo recomeço (RN-02)",
            )
        ciclo = CicloDeFocalizacao(
            id=uuid4(),
            ordem=len(self._ciclos) + 1,
            aberto_em=em,
            passos=_novos_passos(),
            heranca=tuple(herdadas),
        )
        self._ciclos.append(ciclo)
        self.projeto._avancar(em)
        self._emitir(
            CicloAberto, em, ciclo_id=ciclo.id, ordem=ciclo.ordem, herdadas=len(ciclo.heranca)
        )
        return ciclo

    def recomecar(self, *, em: datetime) -> CicloDeFocalizacao:
        """RF-15: fecha o ciclo atual e abre o próximo — **sem apagar nada** (RN-04).

        O ciclo que fecha vira somente leitura e continua na linha do tempo com tudo o que
        tinha. O ciclo novo abre em `identificar`, **sem restrição** — porque procurar a
        nova restrição é o trabalho do primeiro passo, e vir com uma preenchida seria
        responder a pergunta que o método manda refazer.
        """
        self.projeto._exigir_ativo("recomecar")
        ciclo = self.ciclo_aberto
        ciclo.exigir_aberto("recomecar")
        if ciclo.passo_atual.tipo is not TipoDePasso.RECOMECAR:
            raise CicloInvalido(
                "recomeco_fora_do_passo",
                f"o recomeço é o ato do quinto passo; o ciclo {ciclo.ordem} está em "
                f"{ciclo.passo_atual.tipo.value!r} (RN-02, RN-07)",
            )

        herdadas = _herdar(ciclo)
        quinto = ciclo.passo(TipoDePasso.RECOMECAR)
        quinto.estado = EstadoDoPasso.CONCLUIDO
        ciclo.estado = EstadoDoCiclo.FECHADO
        ciclo.fechado_em = em
        self.projeto._avancar(em)
        self._emitir(
            CicloFechado,
            em,
            ciclo_id=ciclo.id,
            ordem=ciclo.ordem,
            decisoes=sum(len(p.decisoes) for p in ciclo.passos),
        )
        return self.abrir_ciclo(em=em, herdadas=herdadas)

    # -- internos ------------------------------------------------------------------

    @staticmethod
    def _seguinte(tipo: TipoDePasso) -> TipoDePasso | None:
        indice = ORDEM_CANONICA.index(tipo)
        return ORDEM_CANONICA[indice + 1] if indice + 1 < len(ORDEM_CANONICA) else None

    @staticmethod
    def _anterior(tipo: TipoDePasso) -> TipoDePasso | None:
        indice = ORDEM_CANONICA.index(tipo)
        return ORDEM_CANONICA[indice - 1] if indice > 0 else None

    def _emitir(self, classe, em: datetime, **carga) -> None:
        self.projeto.eventos = self.projeto.eventos + (
            classe(
                projeto_id=self.projeto.id,
                dono=self.projeto.dono,
                instante=em,
                **carga,
            ),
        )


def _herdar(ciclo: CicloDeFocalizacao) -> tuple[DecisaoHerdada, ...]:
    """RN-05: o que atravessa o recomeço, e por quê.

    Duas fontes, e a segunda é a que a spec não escreveu (ver o cabeçalho do módulo):

    1. as decisões de `explorar` e `subordinar` do ciclo que está fechando — as regras de
       operação que ele criou;
    2. as decisões que **este** ciclo herdou e decidiu **MANTER** — porque um "mantida"
       vitalício seria a inércia com outro nome.

    As revogadas não voltam: revogar é justamente dizer que aquela regra deixou de valer.
    Toda herdada nasce `pendente` outra vez, com o texto original preservado.
    """
    herdadas: list[DecisaoHerdada] = []
    for tipo in PASSOS_QUE_GERAM_INERCIA:
        passo = ciclo.passo(tipo)
        # A decisão VIGENTE, e só ela. Um passo reaberto e concluído de novo tem duas
        # decisões no histórico (RN-04), mas a regra de operação que sobreviveu é **a
        # última** — a anterior já foi substituída pelo próprio grupo. Herdar as duas
        # mandaria à mesa uma regra que ninguém segue mais, e ruído é como um aviso deixa
        # de funcionar: quem recebe pendência inútil aprende a despachar todas.
        if passo.decisao is not None:
            herdadas.append(
                DecisaoHerdada(
                    id=uuid4(),
                    ciclo_de_origem=ciclo.ordem,
                    passo=tipo,
                    texto=passo.decisao.texto,
                )
            )
    for antiga in ciclo.heranca:
        if antiga.veredito is VereditoDeHeranca.MANTIDA:
            herdadas.append(
                DecisaoHerdada(
                    id=uuid4(),
                    ciclo_de_origem=antiga.ciclo_de_origem,
                    passo=antiga.passo,
                    texto=antiga.texto,
                )
            )
    return tuple(herdadas)


# ---------------------------------------------------------------------------------------
# RF-12/RF-13 — o mapa da jornada: serviço de domínio, função PURA
# ---------------------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class EntradaDaLinhaDoTempo:
    """RF-17: uma linha da história da análise — um ciclo."""

    ciclo_id: UUID
    ordem: int
    estado: EstadoDoCiclo
    restricao: str | None
    tipo_de_restricao: TipoDeRestricao | None
    aberto_em: datetime
    fechado_em: datetime | None
    decisoes: int
    vinculos: int
    herancas: int
    herancas_pendentes: int
    passo_atual: TipoDePasso


@dataclass(frozen=True, slots=True)
class PendenciaDoPasso:
    """O que falta num passo, com a REGRA nomeada — a tela não reconstrói por texto."""

    passo: TipoDePasso
    regra: str
    detalhe: str


@dataclass(frozen=True, slots=True)
class PassoNaJornada:
    """Um passo, como a jornada o apresenta (RI-01, RI-02)."""

    tipo: TipoDePasso
    estado: EstadoDoPasso
    decisao: str
    autor_da_decisao: str
    notas: int
    vinculos: tuple[VinculoDeFerramenta, ...]
    canonicas: tuple[TipoDeFerramentaVinculada, ...]
    avisos: tuple[str, ...]
    #: RF-13: o produto dos passos ANTERIORES do mesmo ciclo, pronto para o topo do painel.
    herdado: tuple[str, ...]
    pendencias: tuple[PendenciaDoPasso, ...]
    reaberturas: int


@dataclass(frozen=True, slots=True)
class MapaDaJornada:
    """O que a tela 6.1 mostra — computado, nunca guardado (RF-12)."""

    ciclo_id: UUID
    ordem: int
    estado: EstadoDoCiclo
    restricao: Restricao | None
    passo_atual: TipoDePasso
    passos: tuple[PassoNaJornada, ...]
    heranca: tuple[DecisaoHerdada, ...]
    herancas_pendentes: int
    ciclos_no_total: int

    def de(self, tipo: TipoDePasso | str) -> PassoNaJornada:
        alvo = TipoDePasso(tipo)
        for passo in self.passos:
            if passo.tipo is alvo:
                return passo
        raise NaoEncontrado(f"passo:{alvo.value}")  # pragma: no cover - invariante

    @property
    def progresso(self) -> tuple[int, int]:
        concluidos = sum(1 for p in self.passos if p.estado is EstadoDoPasso.CONCLUIDO)
        return (concluidos, len(ORDEM_CANONICA))

    def resumo(self) -> dict[str, object]:
        """O resumo quantitativo — o que entra no traço e no evento. Nunca texto de pessoa."""
        concluidos, total = self.progresso
        return {
            "ciclo": self.ordem,
            "ciclos_no_total": self.ciclos_no_total,
            "estado": self.estado.value,
            "passo_atual": self.passo_atual.value,
            "passos_concluidos": concluidos,
            "passos_no_total": total,
            "tem_restricao": self.restricao is not None,
            "vinculos": sum(len(p.vinculos) for p in self.passos),
            "vinculos_nao_canonicos": sum(
                1 for p in self.passos for v in p.vinculos if not v.canonico
            ),
            "herancas_pendentes": self.herancas_pendentes,
            "pendencias": sum(len(p.pendencias) for p in self.passos),
        }


def mapa_da_jornada(analise: AnaliseDeFocalizacao) -> MapaDaJornada:
    """RF-12: o mapa do ciclo aberto. **Função pura**: não muta nada, não fala com nada.

    É o que a interface consome para mostrar onde a análise está e o que falta — e é aqui
    que o RF-13 acontece: cada passo carrega o produto dos anteriores do mesmo ciclo, para
    que ninguém decida no vácuo.
    """
    ciclo = analise.ciclo_aberto
    return _mapa_do_ciclo(ciclo, ciclos_no_total=len(analise.ciclos))


def mapa_do_ciclo(analise: AnaliseDeFocalizacao, ciclo_id: UUID) -> MapaDaJornada:
    """O mesmo mapa, para um ciclo QUALQUER — inclusive fechado (RF-17: abre somente leitura)."""
    return _mapa_do_ciclo(analise.ciclo(ciclo_id), ciclos_no_total=len(analise.ciclos))


def _mapa_do_ciclo(ciclo: CicloDeFocalizacao, *, ciclos_no_total: int) -> MapaDaJornada:
    passos: list[PassoNaJornada] = []
    herdado: list[str] = []
    if ciclo.restricao is not None:
        legenda = f"Restrição do ciclo: {ciclo.restricao.descricao}"
    else:
        legenda = None

    for passo in ciclo.passos:
        # RF-13: o que este passo herda são a restrição (produto de `identificar`) e as
        # decisões já registradas nos passos anteriores DESTE ciclo — nesta ordem.
        herdado_deste = tuple(herdado)
        passos.append(
            PassoNaJornada(
                tipo=passo.tipo,
                estado=passo.estado,
                decisao="" if passo.decisao is None else passo.decisao.texto,
                autor_da_decisao="" if passo.decisao is None else passo.decisao.autor,
                notas=len(passo.notas),
                vinculos=passo.vinculos,
                canonicas=tuple(sorted(passo.canonicas, key=lambda f: f.value)),
                avisos=passo.avisos(),
                herdado=herdado_deste,
                pendencias=_pendencias(ciclo, passo),
                reaberturas=len(passo.reaberturas),
            )
        )
        if passo.tipo is TipoDePasso.IDENTIFICAR and legenda:
            herdado.append(legenda)
        if passo.decisao is not None:
            herdado.append(f"Decisão de {passo.tipo.value}: {passo.decisao.texto}")

    return MapaDaJornada(
        ciclo_id=ciclo.id,
        ordem=ciclo.ordem,
        estado=ciclo.estado,
        restricao=ciclo.restricao,
        passo_atual=ciclo.passo_atual.tipo,
        passos=tuple(passos),
        heranca=ciclo.heranca,
        herancas_pendentes=len(ciclo.herancas_pendentes()),
        ciclos_no_total=ciclos_no_total,
    )


def _pendencias(
    ciclo: CicloDeFocalizacao, passo: PassoDeFocalizacao
) -> tuple[PendenciaDoPasso, ...]:
    """O que impede ESTE passo de concluir. Cada uma é a mesma regra que o agregado recusa.

    Vínculo fora do canônico **não** entra aqui: ele é aviso (RN-06), e misturar aviso com
    pendência transformaria uma escolha legítima do grupo numa tarefa por fazer.
    """
    if passo.estado is EstadoDoPasso.CONCLUIDO:
        return ()
    faltas: list[PendenciaDoPasso] = []
    if passo.tipo is TipoDePasso.IDENTIFICAR and ciclo.restricao is None:
        faltas.append(
            PendenciaDoPasso(
                passo=passo.tipo,
                regra="sem_restricao",
                detalhe="o passo identificar não conclui sem restrição registrada (RF-08)",
            )
        )
    if passo.tipo is TipoDePasso.SUBORDINAR:
        pendentes = ciclo.herancas_pendentes()
        if pendentes:
            faltas.append(
                PendenciaDoPasso(
                    passo=passo.tipo,
                    regra="heranca_pendente",
                    detalhe=(
                        f"{len(pendentes)} decisão(ões) do ciclo anterior ainda sem "
                        "veredito (RN-05)"
                    ),
                )
            )
    if passo.tipo is not TipoDePasso.RECOMECAR and not passo.decisoes:
        faltas.append(
            PendenciaDoPasso(
                passo=passo.tipo,
                regra="decisao_ausente",
                detalhe="o passo se encerra com a decisão que o encerra (RF-09)",
            )
        )
    return tuple(faltas)


# ---------------------------------------------------------------------------------------
# Fábricas: criar e reidratar
# ---------------------------------------------------------------------------------------


def nova_analise_de_focalizacao(
    *,
    id: UUID,
    dono: DonoDoProjeto,
    nome: str,
    sistema: SistemaAnalisado,
    em: datetime,
) -> AnaliseDeFocalizacao:
    """RF-01/RF-02: a análise nasce com o primeiro ciclo aberto no passo `identificar`.

    Não existe análise sem ciclo, nem ciclo sem os cinco passos: quem cria não escolhe a
    forma da jornada, e por isso não pode errá-la.
    """
    projeto = Projeto(
        id=id,
        dono=dono,
        nome=nome,
        ferramenta=FERRAMENTA_FOCALIZACAO,
        descricao_do_problema=sistema.descricao,
        criado_em=em,
        alterado_em=em,
    )
    analise = AnaliseDeFocalizacao(projeto=projeto, sistema=sistema)
    analise._emitir(AnaliseCriada, em, sistema=sistema.nome)
    analise.abrir_ciclo(em=em)
    return analise


def reidratar_analise(
    projeto: Projeto,
    *,
    sistema: SistemaAnalisado,
    ciclos: Iterable[CicloDeFocalizacao] = (),
) -> AnaliseDeFocalizacao:
    """Monta a análise a partir do que estava GRAVADO — sem emitir evento nenhum.

    Carregar não é mutar (a mesma regra de `reidratar_ara` e `reidratar_nuvem`): se a
    reidratação emitisse `AnaliseCriada`, abrir a jornada escreveria história que não
    aconteceu.
    """
    analise = AnaliseDeFocalizacao(projeto=projeto, sistema=sistema)
    analise._ciclos = sorted(ciclos, key=lambda c: c.ordem)
    abertos = [c for c in analise._ciclos if c.aberto]
    if len(abertos) > 1:
        # RN-02 conferida na reidratação também: dois ciclos abertos no banco é corrupção,
        # e carregá-los em silêncio esconderia o defeito em vez de mostrá-lo.
        raise CicloInvalido(
            "ja_ha_ciclo_aberto",
            f"{len(abertos)} ciclos abertos no projeto {projeto.id}: a análise tem no "
            "máximo um (RN-02)",
        )
    projeto.eventos = ()
    return analise


# ---------------------------------------------------------------------------------------
# RF-18 — exportação e importação sem perda
# ---------------------------------------------------------------------------------------

#: A versão do formato canônico da análise. Ela viaja no documento porque um arquivo sem
#: versão é um arquivo que ninguém consegue migrar depois — e migração de export é
#: exatamente o tipo de dívida que só aparece quando já é tarde.
VERSAO_DA_EXPORTACAO = "toc.focalizacao/1"


def exportar_analise(analise: AnaliseDeFocalizacao) -> dict:
    """O documento canônico da análise — determinístico e sem nada da infraestrutura.

    **Função pura, e o formato é ordenado**: os ciclos saem por ordem, os passos na ordem
    canônica, as decisões na ordem em que foram tomadas. Exportação que muda de forma
    entre duas execuções não serve para comparar nem para versionar, e a primeira coisa
    que alguém faz com um export é justamente comparar dois.

    O que o documento **não** carrega, e a ausência é o desenho: o inquilino e o usuário
    (identidade é da fundação, e importar num destino é adotar a identidade de LÁ) e
    qualquer conteúdo dos módulos M2–M4 — o vínculo viaja como referência, que é o que ele
    é (RF-18: "vínculos (como referências)").
    """
    return {
        "versao": VERSAO_DA_EXPORTACAO,
        "nome": analise.projeto.nome,
        "sistema": {
            "nome": analise.sistema.nome,
            "descricao": analise.sistema.descricao,
        },
        "ciclos": [_ciclo_exportado(c) for c in analise.ciclos],
    }


def _ciclo_exportado(ciclo: CicloDeFocalizacao) -> dict:
    return {
        "ordem": ciclo.ordem,
        "estado": ciclo.estado.value,
        "aberto_em": ciclo.aberto_em.isoformat(),
        "fechado_em": None if ciclo.fechado_em is None else ciclo.fechado_em.isoformat(),
        "restricao": None
        if ciclo.restricao is None
        else {
            "descricao": ciclo.restricao.descricao,
            "tipo": ciclo.restricao.tipo.value,
            "justificativa": ciclo.restricao.justificativa,
            "autor": ciclo.restricao.autor,
            "registrada_em": ciclo.restricao.registrada_em.isoformat(),
            "origem": None
            if ciclo.restricao.origem is None
            else {
                "ferramenta": ciclo.restricao.origem.ferramenta,
                "projeto_id": str(ciclo.restricao.origem.projeto_id),
                "no_id": str(ciclo.restricao.origem.no_id),
            },
        },
        "passos": [
            {
                "tipo": p.tipo.value,
                "estado": p.estado.value,
                "decisoes": [
                    {"texto": d.texto, "autor": d.autor, "instante": d.instante.isoformat()}
                    for d in p.decisoes
                ],
                "notas": [
                    {"texto": n.texto, "autor": n.autor, "instante": n.instante.isoformat()}
                    for n in p.notas
                ],
                "reaberturas": [
                    {
                        "justificativa": r.justificativa,
                        "autor": r.autor,
                        "instante": r.instante.isoformat(),
                    }
                    for r in p.reaberturas
                ],
                "vinculos": [
                    {
                        "ferramenta": v.tipo.value,
                        "projeto_id": str(v.projeto_id),
                        "papel": v.papel,
                        "justificativa": v.justificativa,
                        "canonico": v.canonico,
                    }
                    for v in p.vinculos
                ],
            }
            for p in ciclo.passos
        ],
        "heranca": [
            {
                "ciclo_de_origem": h.ciclo_de_origem,
                "passo": h.passo.value,
                "texto": h.texto,
                "veredito": h.veredito.value,
                "justificativa": h.justificativa,
                "autor": h.autor,
                "julgada_em": None if h.julgada_em is None else h.julgada_em.isoformat(),
            }
            for h in ciclo.heranca
        ],
    }


@dataclass(frozen=True, slots=True)
class ReferenciaPendente:
    """RF-18: um vínculo cujo projeto de destino não existe no destino da importação.

    Ele **não some e não falha em silêncio**: entra na análise importada como está e sai
    declarado nesta lista, para quem importou saber exatamente o que ficou pendurado. É a
    mesma disciplina do "referência a projeto arquivado" da RNF-04 — dado órfão em
    silêncio é a coisa que os dois requisitos proíbem.
    """

    ciclo: int
    passo: TipoDePasso
    ferramenta: TipoDeFerramentaVinculada
    projeto_id: UUID


def importar_analise(
    documento: dict,
    *,
    id: UUID,
    dono: DonoDoProjeto,
    projetos_existentes: Iterable[UUID] = (),
) -> tuple[AnaliseDeFocalizacao, tuple[ReferenciaPendente, ...]]:
    """RF-18: ida e volta sem perda, com as referências sem destino DECLARADAS.

    O inquilino e o usuário vêm de QUEM IMPORTA, nunca do documento: identidade é da
    fundação, e um export que carregasse o dono de origem seria um caminho para escrever
    no inquilino errado.

    A importação **não emite evento nenhum**: importar não é viver a jornada de novo. É a
    mesma regra de `reidratar_analise`, e pelo mesmo motivo — escrever história que não
    aconteceu é pior do que não ter história.
    """
    versao = documento.get("versao")
    if versao != VERSAO_DA_EXPORTACAO:
        raise DadoInvalido(
            f"exportação de versão {versao!r}; esta aplicação lê "
            f"{VERSAO_DA_EXPORTACAO!r}"
        )
    conhecidos = set(projetos_existentes)
    sistema = SistemaAnalisado(
        nome=documento["sistema"]["nome"],
        descricao=documento["sistema"].get("descricao", ""),
    )
    projeto = Projeto(
        id=id,
        dono=dono,
        nome=documento["nome"],
        ferramenta=FERRAMENTA_FOCALIZACAO,
        descricao_do_problema=sistema.descricao,
        criado_em=datetime.fromisoformat(documento["ciclos"][0]["aberto_em"]),
        alterado_em=datetime.fromisoformat(documento["ciclos"][0]["aberto_em"]),
    )
    pendentes: list[ReferenciaPendente] = []
    ciclos: list[CicloDeFocalizacao] = []
    for bruto in documento["ciclos"]:
        ciclos.append(_ciclo_importado(bruto, conhecidos, pendentes))
    analise = reidratar_analise(projeto, sistema=sistema, ciclos=ciclos)
    return analise, tuple(pendentes)


def _ciclo_importado(
    bruto: dict, conhecidos: set[UUID], pendentes: list[ReferenciaPendente]
) -> CicloDeFocalizacao:
    passos: list[PassoDeFocalizacao] = []
    por_tipo = {p["tipo"]: p for p in bruto["passos"]}
    for tipo in ORDEM_CANONICA:
        do_passo = por_tipo.get(tipo.value, {})
        vinculos: list[VinculoDeFerramenta] = []
        for v in do_passo.get("vinculos", []):
            ferramenta = TipoDeFerramentaVinculada(v["ferramenta"])
            alvo = UUID(v["projeto_id"])
            if conhecidos and alvo not in conhecidos:
                pendentes.append(
                    ReferenciaPendente(
                        ciclo=bruto["ordem"], passo=tipo, ferramenta=ferramenta,
                        projeto_id=alvo,
                    )
                )
            vinculos.append(
                VinculoDeFerramenta(
                    id=uuid4(),
                    tipo=ferramenta,
                    projeto_id=alvo,
                    papel=v.get("papel", ""),
                    justificativa=v.get("justificativa", ""),
                    canonico=bool(v.get("canonico", True)),
                )
            )
        passos.append(
            PassoDeFocalizacao(
                tipo=tipo,
                estado=EstadoDoPasso(do_passo.get("estado", EstadoDoPasso.PENDENTE.value)),
                decisoes=tuple(
                    DecisaoDePasso(
                        texto=d["texto"],
                        autor=d["autor"],
                        instante=datetime.fromisoformat(d["instante"]),
                    )
                    for d in do_passo.get("decisoes", [])
                ),
                notas=tuple(
                    NotaDePasso(
                        id=uuid4(),
                        texto=n["texto"],
                        autor=n["autor"],
                        instante=datetime.fromisoformat(n["instante"]),
                    )
                    for n in do_passo.get("notas", [])
                ),
                reaberturas=tuple(
                    Reabertura(
                        justificativa=r["justificativa"],
                        autor=r["autor"],
                        instante=datetime.fromisoformat(r["instante"]),
                    )
                    for r in do_passo.get("reaberturas", [])
                ),
                vinculos=tuple(vinculos),
            )
        )
    restricao = bruto.get("restricao")
    return CicloDeFocalizacao(
        id=uuid4(),
        ordem=bruto["ordem"],
        aberto_em=datetime.fromisoformat(bruto["aberto_em"]),
        passos=tuple(passos),
        estado=EstadoDoCiclo(bruto["estado"]),
        fechado_em=None
        if bruto.get("fechado_em") is None
        else datetime.fromisoformat(bruto["fechado_em"]),
        restricao=None
        if restricao is None
        else Restricao(
            id=uuid4(),
            descricao=restricao["descricao"],
            tipo=TipoDeRestricao(restricao["tipo"]),
            justificativa=restricao["justificativa"],
            autor=restricao["autor"],
            registrada_em=datetime.fromisoformat(restricao["registrada_em"]),
            origem=None
            if restricao.get("origem") is None
            else ReferenciaDeOrigemDaRestricao(
                ferramenta=restricao["origem"]["ferramenta"],
                projeto_id=UUID(restricao["origem"]["projeto_id"]),
                no_id=UUID(restricao["origem"]["no_id"]),
            ),
        ),
        heranca=tuple(
            DecisaoHerdada(
                id=uuid4(),
                ciclo_de_origem=h["ciclo_de_origem"],
                passo=TipoDePasso(h["passo"]),
                texto=h["texto"],
                veredito=VereditoDeHeranca(h["veredito"]),
                justificativa=h.get("justificativa", ""),
                autor=h.get("autor", ""),
                julgada_em=None
                if h.get("julgada_em") is None
                else datetime.fromisoformat(h["julgada_em"]),
            )
            for h in bruto.get("heranca", [])
        ),
    )


__all__ = [
    "FERRAMENTAS_CANONICAS_DO_PASSO",
    "VERSAO_DA_EXPORTACAO",
    "FERRAMENTA_FOCALIZACAO",
    "ORDEM_CANONICA",
    "PASSOS_QUE_GERAM_INERCIA",
    "AnaliseDeFocalizacao",
    "CicloDeFocalizacao",
    "CicloInvalido",
    "DecisaoDePasso",
    "DecisaoHerdada",
    "EntradaDaLinhaDoTempo",
    "EstadoDoCiclo",
    "EstadoDoPasso",
    "HerancaInvalida",
    "MapaDaJornada",
    "NotaDePasso",
    "PassoDeFocalizacao",
    "PassoInvalido",
    "PassoNaJornada",
    "PendenciaDoPasso",
    "Reabertura",
    "ReferenciaPendente",
    "ReferenciaDeOrigemDaRestricao",
    "Restricao",
    "RestricaoInvalida",
    "SistemaAnalisado",
    "TipoDeFerramentaVinculada",
    "TipoDePasso",
    "TipoDeRestricao",
    "VereditoDeHeranca",
    "VinculoDeFerramenta",
    "VinculoInvalido",
    "exportar_analise",
    "importar_analise",
    "mapa_da_jornada",
    "mapa_do_ciclo",
    "nova_analise_de_focalizacao",
    "reidratar_analise",
]
