"""M5 — a Árvore de Estratégia & Táticas (S&T) sobre o núcleo do M1 (spec 010).

Siglas, uma vez neste arquivo: **S&T** — Estratégia & Táticas (*Strategy & Tactics*) ·
**M1** — Núcleo de Diagramas Lógicos · **M5** — o módulo da S&T · **TOC** — Teoria das
Restrições · **APR** — Árvore de Pré-Requisitos · **AT** — Árvore de Transição ·
**RF/RN/RNF** — requisito funcional / regra de negócio / requisito não funcional da
spec 010.

**Este módulo é um resgate.** A S&T é a única ferramenta que REGREDIU na linhagem:
`TOC-Builder/components/Sidebar.tsx:44` a declara habilitada na primeira geração, sem
`disabled`, e `tocbuilderv3/components/Sidebar.tsx:58` a declara `disabled: true` na
quarta — com o modelo de dados inteiro parado no código (`tocbuilderv3/types.ts:270-311`).
Funcionalidade que regride sem decisão registrada é o que um ADR (*Architecture Decision
Record*) existe para impedir; o que entra aqui desfaz a regressão com a decisão registrada.

O que a linhagem tinha de bom atravessa: **as três premissas lógicas** por passo, que
existem desde a primeira geração (`TOC-Builder/types.ts:243-245`) e são o que faz uma S&T
ser S&T em vez de organograma. O que ela tinha de defeito não atravessa, e cada defeito
vira invariante deste arquivo:

1. **O número era digitado à mão** (`tocbuilderv3/types.ts:288`, obrigatório e sem
   validação de formato ou unicidade em `SnTStepEditorModal.tsx:56-57`). Aqui o número é
   **projeção pura da posição** (RN-01): não existe campo de número, não se persiste
   número, e a exportação não carrega número. Duas fontes de verdade não podem divergir
   quando só existe uma.
2. **A estrutura reusava aresta de grafo livre** (`edges: AraEdge[] // Reusing AraEdge for
   simplicity`). Aqui a S&T é **árvore estrita** (RN-04): pai único, ordem explícita entre
   irmãos, nenhuma aresta como entidade — ciclo e multi-pai ficam irrepresentáveis, e a
   única recusa necessária é mover um passo para dentro da própria subárvore.
3. **Excluir um passo descartava todos os outros**
   (`tocbuilderv3/services/mockApiService.ts:521`: `project.nodes.filter(n => n.id ===
   nodeId)` — o predicado correto seria `!==`). Aqui a exclusão é da **subárvore exata**,
   com a contagem informada antes (RN-05), e o defeito da linhagem é caso de teste.

A regra que **não** trava nada é a RN-06: premissa ausente é pendência, nunca bloqueio de
gravação. O painel diz onde o plano ainda é organograma; quem decide quando deixar de ser
é o grupo.
"""
from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from enum import Enum
from typing import Iterable, Iterator, Mapping, Sequence
from uuid import UUID, uuid4

from .erros import DadoInvalido, MutacaoRecusada, NaoEncontrado
from .eventos import (
    ArvoreSnTCriada,
    MetaGlobalEditada,
    PassoDaSnTAdicionado,
    PassoDaSnTEditado,
    PassoDaSnTMovido,
    PremissasEditadas,
    StatusDoPassoMudou,
    SubarvoreExcluida,
)
from .grafo import No
from .identidade import DonoDoProjeto
from .projeto import Projeto, registrar_raiz_de_ferramenta
from .valores import (
    LIMITE_DESCRICAO,
    LIMITE_TITULO,
    PosicaoNoCanvas,
    texto as texto_de_dominio,
)

#: O tipo de projeto do M5 (spec 010, RF-01).
FERRAMENTA_SNT = "snt"

#: A S&T é a RAIZ do agregado: o grafo de um projeto `snt` só muda por dentro dela. Sem
#: isto, `Projeto.adicionar_no` criaria passo **sem posição na árvore** — um nó solto que
#: a numeração não alcança, que é a versão nossa do número digitado da linhagem.
registrar_raiz_de_ferramenta(FERRAMENTA_SNT, "ArvoreSnT")

#: Todo nó da S&T é um passo. Não há segundo papel — e não há aresta (RN-04).
TIPO_DE_NO_PASSO = "snt_passo"

LIMITE_META = 2000
LIMITE_PREMISSA = 2000

#: O separador da numeração hierárquica, verbatim do comentário da linhagem
#: (`tocbuilderv3/types.ts:288`: `// e.g., "1", "1.1", "1.1.2"`).
SEPARADOR = "."


# ---------------------------------------------------------------------------------------
# RN-01 · a numeração — função pura sobre a estrutura, nunca campo
# ---------------------------------------------------------------------------------------

#: `pai (ou None para as raízes) → filhos na ordem`. É TODA a estrutura da árvore: a
#: posição entre irmãos é o índice, e por isso não existe lacuna a manter nem número a
#: conferir. O que a linhagem guardava como texto (`stepNumber`) e como aresta livre
#: (`edges: AraEdge[]`), aqui é este mapa e mais nada.
Estrutura = Mapping[UUID | None, Sequence[UUID]]


def numeracao(estrutura: Estrutura) -> dict[UUID, str]:
    """O número de cada passo: raízes `1..n`, filhos de `X` são `X.1..X.m` (RN-01).

    Função pura, determinística e sem lacuna **por construção** — o número é o índice na
    lista de irmãos, e uma lista não tem buraco. Não há caminho em que a numeração
    discorde da estrutura, porque ela não é armazenada em lugar nenhum: é calculada.
    """
    numeros: dict[UUID, str] = {}
    _numerar_sob(estrutura, pai=None, prefixo="", numeros=numeros)
    return numeros


def renumerar(
    numeros: Mapping[UUID, str],
    estrutura: Estrutura,
    *,
    pais_afetados: Iterable[UUID | None],
) -> dict[UUID, str]:
    """RF-07: renumera só a subárvore dos pais afetados — o resto fica como estava.

    A propriedade que sustenta esta função é testada e não suposta (RNF-05, decisão 6 do
    plano): **renumerar localmente devolve o mesmo mapa que recalcular tudo**. É o que
    mantém o mover de uma subárvore de 20 passos dentro do alvo de desempenho (RNF-04)
    sem criar uma segunda verdade sobre a numeração.

    `None` entre os pais afetados significa "as raízes mudaram", e então tudo é
    recalculado — que é o caso honesto de uma inserção na primeira linha.
    """
    novos = {k: v for k, v in numeros.items() if k in _todos_os_nos(estrutura)}
    for pai in dict.fromkeys(pais_afetados):
        if pai is None:
            return numeracao(estrutura)
        if pai not in novos:
            # O pai afetado não tem número (foi removido, ou nunca existiu): o escopo
            # local perdeu o sentido, e recalcular tudo é a resposta correta — nunca
            # deixar meia árvore com número velho.
            return numeracao(estrutura)
        _numerar_sob(estrutura, pai=pai, prefixo=novos[pai], numeros=novos)
    return novos


def _numerar_sob(
    estrutura: Estrutura, *, pai: UUID | None, prefixo: str, numeros: dict[UUID, str]
) -> None:
    for indice, filho in enumerate(estrutura.get(pai, ()), start=1):
        numero = f"{prefixo}{SEPARADOR}{indice}" if prefixo else str(indice)
        numeros[filho] = numero
        _numerar_sob(estrutura, pai=filho, prefixo=numero, numeros=numeros)


def _todos_os_nos(estrutura: Estrutura) -> set[UUID]:
    return {filho for filhos in estrutura.values() for filho in filhos}


def ordem_estrutural(estrutura: Estrutura) -> tuple[UUID, ...]:
    """A ordem de leitura da árvore: profundidade primeiro, irmãos na ordem declarada.

    É a ordem da vista tabular (RF-19) e da exportação (RF-21) — e é reprodutível, porque
    um plano que se lê em ordem diferente a cada abertura não se leva a lugar nenhum.
    """
    saida: list[UUID] = []

    def descer(pai: UUID | None) -> None:
        for filho in estrutura.get(pai, ()):
            saida.append(filho)
            descer(filho)

    descer(None)
    return tuple(saida)


def descendentes(estrutura: Estrutura, no_id: UUID) -> tuple[UUID, ...]:
    """Todos os descendentes de um passo, em ordem estrutural. Sem ele próprio."""
    saida: list[UUID] = []

    def descer(pai: UUID) -> None:
        for filho in estrutura.get(pai, ()):
            saida.append(filho)
            descer(filho)

    descer(no_id)
    return tuple(saida)



# ---------------------------------------------------------------------------------------
# Os valores do passo — o modelo da linhagem, com a semântica que ele nunca teve
# ---------------------------------------------------------------------------------------


class StatusDoPasso(str, Enum):
    """RN-03: os quatro valores da linhagem (`tocbuilderv3/types.ts:270-275`).

    Lá eles já eram portugueses (`'Nenhum'`, `'Validado'`, `'Não Validado'`, `'Em
    Execução'`); aqui viram vocabulário fechado do domínio, e a mudança passa a ter autor
    e data — que é o que faltava.

    **Transição é livre entre os quatro** (decisão do ADR 0014, [DÚVIDA] 2 da spec 010):
    impor "só executa depois de validado" travaria a reunião real em que o plano executa
    antes de a validação formal acontecer. O que a operação recusa é outra coisa —
    mudança para o mesmo valor, valor fora do vocabulário e mudança sem autor —, e as três
    recusas são exercitadas em `tests/dominio/test_status_do_passo.py`.
    """

    NENHUM = "nenhum"
    VALIDADO = "validado"
    NAO_VALIDADO = "nao_validado"
    EM_EXECUCAO = "em_execucao"


class CategoriaDoPasso(str, Enum):
    """A classificação da linhagem (`tocbuilderv3/types.ts:277-284`), portada como RÓTULO.

    A spec 010 assumiu não portá-la (L-01) e mandou a decisão para o gate ([DÚVIDA] 1). O
    gate respondeu **portar como campo opcional**, e o ADR 0014 registra o porquê: os seis
    valores existiam na linhagem desde a primeira geração, são vocabulário que o método
    S&T usa em sala, e um rótulo opcional não disputa função com os campos `estrategia` e
    `tatica` — ele classifica o papel do passo no plano, não substitui o quê nem o como.

    O padrão é `NENHUMA` — nunca obrigatório, nunca bloqueando gravação (RN-06).
    """

    NENHUMA = "nenhuma"
    ESTRATEGIA = "estrategia"
    TATICA = "tatica"
    #: *Value Creating Deliverable* — entregável gerador de valor, jargão da linhagem.
    VCD = "vcd"
    BUILD = "build"
    LEVERAGE = "leverage"


class PassoInvalido(MutacaoRecusada):
    """`regra`: `sem_ficha` · `pai_inexistente`."""

    def __init__(self, regra: str, detalhe: str = "") -> None:
        super().__init__(f"{regra}: {detalhe}" if detalhe else regra)
        self.regra = regra


class MovimentoRecusado(MutacaoRecusada):
    """RN-04. `motivo`: `para_a_propria_subarvore` · `destino_inexistente`."""

    def __init__(self, motivo: str, detalhe: str = "") -> None:
        super().__init__(f"{motivo}: {detalhe}" if detalhe else motivo)
        self.motivo = motivo


class TransicaoDeStatusRecusada(MutacaoRecusada):
    """RN-03. `motivo`: `sem_mudanca` · `autor_obrigatorio`."""

    def __init__(self, motivo: str, detalhe: str = "") -> None:
        super().__init__(f"{motivo}: {detalhe}" if detalhe else motivo)
        self.motivo = motivo


@dataclass(frozen=True, slots=True)
class PremissasDoPasso:
    """RN-02: as três premissas lógicas, com papel estrutural fixo.

    Os três campos são verbatim os do modelo da linhagem — `parallelAssumption`,
    `necessaryAssumptionToParent`, `sufficiencyOfChildrenAssumption`
    (`tocbuilderv3/types.ts:293-295`, e já em `TOC-Builder/types.ts:243-245`). O que muda
    é que lá eram três áreas de texto empilhadas sem leitura dirigida
    (`SnTStepEditorModal.tsx:137-159`) e aqui cada uma tem posição de leitura e regra de
    pendência:

    - **paralela** — o pressuposto de contexto; lê-se sozinha e nunca é pendência;
    - **necessidade ao pai** — não se aplica à raiz; ausente em passo não-raiz é pendência;
    - **suficiência dos filhos** — só significa algo com filhos; ausente com filhos é
      pendência.

    Objeto de valor: mudar um campo cria premissas novas. É isso que impede a lógica do
    plano de ser mutada por baixo do agregado, sem passar pelo evento.
    """

    paralela: str = ""
    necessidade_ao_pai: str = ""
    suficiencia_dos_filhos: str = ""

    def __post_init__(self) -> None:
        for campo in ("paralela", "necessidade_ao_pai", "suficiencia_dos_filhos"):
            object.__setattr__(
                self,
                campo,
                texto_de_dominio(
                    getattr(self, campo), campo=campo, minimo=0, maximo=LIMITE_PREMISSA
                ),
            )

    @property
    def vazias(self) -> bool:
        return not (self.paralela or self.necessidade_ao_pai or self.suficiencia_dos_filhos)


@dataclass(frozen=True, slots=True)
class FichaDoPasso:
    """O conteúdo de um passo: o quê, o como, os porquês e onde ele está (RF-11, RF-12).

    A estratégia é obrigatória e a tática pode nascer vazia (RF-11) — vazia ela é
    **pendência**, nunca bloqueio (RN-06). A linhagem tinha um texto só (`strategyText`)
    mais uma categoria de seis valores; aqui o quê e o como são campos distintos, e a
    categoria fica como rótulo opcional (ADR 0014).
    """

    estrategia: str
    tatica: str = ""
    premissas: PremissasDoPasso = field(default_factory=PremissasDoPasso)
    status: StatusDoPasso = StatusDoPasso.NENHUM
    categoria: CategoriaDoPasso = CategoriaDoPasso.NENHUMA

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "estrategia",
            texto_de_dominio(self.estrategia, campo="estrategia", minimo=1, maximo=LIMITE_TITULO),
        )
        object.__setattr__(
            self,
            "tatica",
            texto_de_dominio(self.tatica, campo="tatica", minimo=0, maximo=LIMITE_DESCRICAO),
        )
        object.__setattr__(self, "status", StatusDoPasso(self.status))
        object.__setattr__(self, "categoria", CategoriaDoPasso(self.categoria))
        if not isinstance(self.premissas, PremissasDoPasso):  # pragma: no cover - contrato
            raise DadoInvalido("premissas: precisa ser PremissasDoPasso")


# ---------------------------------------------------------------------------------------
# RF-13 · a leitura dirigida — a ficha ensina o método pela disposição
# ---------------------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class Leitura:
    """Uma premissa lida no papel dela, com o pai e os filhos NOMEADOS.

    `aplicavel` é falso quando a estrutura torna a premissa sem sentido (necessidade numa
    raiz, suficiência num passo sem filhos); `completa` é falso quando ela ainda não foi
    escrita. Os dois juntos são o que a pendência do RF-14 consulta — e o que a ficha usa
    para mostrar a frase pela metade, que é como se ensina o método sem travar ninguém.
    """

    papel: str
    texto: str
    aplicavel: bool
    completa: bool


@dataclass(frozen=True, slots=True)
class LinhaDaArvore:
    """Uma linha da vista tabular indentada (RF-19) — número, conteúdo e presença."""

    no_id: UUID
    numero: str
    nivel: int
    pai_id: UUID | None
    estrategia: str
    tatica: str
    status: StatusDoPasso
    categoria: CategoriaDoPasso
    filhos: int
    tem_premissa_paralela: bool
    tem_premissa_de_necessidade: bool
    tem_premissa_de_suficiencia: bool


# ---------------------------------------------------------------------------------------
# RF-14 / RF-17 · pendências e contagens — função pura, e a única fonte do painel
# ---------------------------------------------------------------------------------------

#: Os três tipos de pendência lógica do RF-14. Vocabulário fechado: pendência nova exige
#: spec, não um `if` a mais numa função de tela.
PENDENCIA_SEM_NECESSIDADE = "sem_premissa_de_necessidade"
PENDENCIA_SEM_SUFICIENCIA = "sem_premissa_de_suficiencia"
PENDENCIA_SEM_TATICA = "sem_tatica"


@dataclass(frozen=True, slots=True)
class Pendencia:
    """Onde o plano ainda é organograma — com salto direto para o passo (RF-14)."""

    no_id: UUID
    numero: str
    tipo: str


@dataclass(frozen=True, slots=True)
class PendenciasDaArvore:
    """O resultado do serviço de domínio: pendências, contagens e o denominador.

    `passos_examinados` existe porque a regra R2 do projeto vale também para uma função:
    dizer "3 pendências" sem dizer sobre quantos passos é o verde sem denominador que a
    retrospectiva da irmã `gestaodeprioridades` nomeou.
    """

    pendencias: tuple[Pendencia, ...]
    por_status: Mapping[str, int]
    passos_examinados: int

    @property
    def total(self) -> int:
        return len(self.pendencias)

    def do_tipo(self, tipo: str) -> tuple[Pendencia, ...]:
        return tuple(p for p in self.pendencias if p.tipo == tipo)

    @property
    def progresso(self) -> float:
        """A fração de passos validados — o "progresso" do painel (RF-17).

        Validado, e não "em execução": o que a S&T acompanha é a validação lógica do
        plano. Zero passos é zero por cento, e não divisão por zero.
        """
        if not self.passos_examinados:
            return 0.0
        return self.por_status.get(StatusDoPasso.VALIDADO.value, 0) / self.passos_examinados

    def resumo(self) -> dict[str, int]:
        """As grandezas que o span e o painel consomem — nunca texto de pessoa (ADR 0006)."""
        return {
            "passos": self.passos_examinados,
            "pendencias": self.total,
            PENDENCIA_SEM_NECESSIDADE: len(self.do_tipo(PENDENCIA_SEM_NECESSIDADE)),
            PENDENCIA_SEM_SUFICIENCIA: len(self.do_tipo(PENDENCIA_SEM_SUFICIENCIA)),
            PENDENCIA_SEM_TATICA: len(self.do_tipo(PENDENCIA_SEM_TATICA)),
            **{f"status_{status.value}": 0 for status in StatusDoPasso},
            **{f"status_{k}": v for k, v in self.por_status.items()},
        }


def pendencias_da_arvore(
    estrutura: Estrutura,
    fichas: Mapping[UUID, FichaDoPasso],
    numeros: Mapping[UUID, str],
) -> PendenciasDaArvore:
    """RF-14/RF-17: o serviço de domínio. Função pura — sem rede, sem banco, sem modelo.

    O painel e a árvore consomem ESTA função, e não um dado paralelo: contagem que se
    calcula em dois lugares é contagem que diverge no primeiro requisito novo.
    """
    pais = {filho: pai for pai, filhos in estrutura.items() for filho in filhos}
    por_status: dict[str, int] = {status.value: 0 for status in StatusDoPasso}
    achadas: list[Pendencia] = []
    for no_id in ordem_estrutural(estrutura):
        ficha = fichas.get(no_id)
        if ficha is None:  # pragma: no cover - estrutura e fichas andam juntas
            continue
        por_status[ficha.status.value] += 1
        numero = numeros.get(no_id, "")
        if pais.get(no_id) is not None and not ficha.premissas.necessidade_ao_pai:
            achadas.append(Pendencia(no_id, numero, PENDENCIA_SEM_NECESSIDADE))
        if estrutura.get(no_id) and not ficha.premissas.suficiencia_dos_filhos:
            achadas.append(Pendencia(no_id, numero, PENDENCIA_SEM_SUFICIENCIA))
        if not ficha.tatica:
            achadas.append(Pendencia(no_id, numero, PENDENCIA_SEM_TATICA))
    return PendenciasDaArvore(
        pendencias=tuple(achadas),
        por_status=por_status,
        passos_examinados=len(ordem_estrutural(estrutura)),
    )


# ---------------------------------------------------------------------------------------
# O agregado — a raiz por onde tudo passa
# ---------------------------------------------------------------------------------------


@dataclass(slots=True)
class ArvoreSnT:
    """A S&T: um `Projeto` do M1, a meta global, uma ficha por passo e a ESTRUTURA.

    A estrutura (`pai → filhos na ordem`) é o que substitui as duas coisas que a linhagem
    tinha e que divergiam entre si: o `stepNumber` digitado e o `edges: AraEdge[]`. Aqui
    não há número para conferir nem aresta para validar — há uma árvore, e o número é
    projeção dela.
    """

    projeto: Projeto
    meta_global: str
    _fichas: dict[UUID, FichaDoPasso] = field(default_factory=dict)
    _estrutura: dict[UUID | None, tuple[UUID, ...]] = field(default_factory=dict)
    _numeros: dict[UUID, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.projeto.ferramenta != FERRAMENTA_SNT:
            raise MutacaoRecusada(
                f"ArvoreSnT exige ferramenta {FERRAMENTA_SNT!r}, "
                f"veio {self.projeto.ferramenta!r}"
            )
        self.meta_global = texto_de_dominio(
            self.meta_global, campo="meta_global", minimo=1, maximo=LIMITE_META
        )
        self._estrutura.setdefault(None, ())
        self._numeros = numeracao(self._estrutura)

    # -- a única porta para o `Projeto` contido ----------------------------------

    @contextmanager
    def _nucleo(self) -> Iterator[Projeto]:
        with self.projeto.sob_a_raiz() as nucleo:
            yield nucleo

    # -- consultas ---------------------------------------------------------------

    @property
    def passos(self) -> tuple[No, ...]:
        return self.projeto.nos

    @property
    def eventos(self):
        return self.projeto.eventos

    def drenar_eventos(self):
        return self.projeto.drenar_eventos()

    def ficha(self, no_id: UUID) -> FichaDoPasso:
        try:
            return self._fichas[no_id]
        except KeyError as ausente:
            raise PassoInvalido(
                "sem_ficha", f"o nó {no_id} não é um passo desta árvore"
            ) from ausente

    def fichas(self) -> tuple[tuple[UUID, FichaDoPasso], ...]:
        """As fichas em ORDEM ESTRUTURAL — a mesma da tabela e da exportação."""
        return tuple((no_id, self._fichas[no_id]) for no_id in self.ordem())

    def estrutura(self) -> dict[UUID | None, tuple[UUID, ...]]:
        """Uma CÓPIA da estrutura: quem a recebe não muta a árvore por ela."""
        return {pai: tuple(filhos) for pai, filhos in self._estrutura.items()}

    def ordem(self) -> tuple[UUID, ...]:
        return ordem_estrutural(self._estrutura)

    def numero(self, no_id: UUID) -> str:
        self.ficha(no_id)
        return self._numeros[no_id]

    def numeros(self) -> dict[UUID, str]:
        return dict(self._numeros)

    def pai(self, no_id: UUID) -> UUID | None:
        self.ficha(no_id)
        return self._pai_de(no_id)

    def filhos(self, no_id: UUID | None) -> tuple[UUID, ...]:
        return tuple(self._estrutura.get(no_id, ()))

    def nivel(self, no_id: UUID) -> int:
        nivel = 0
        atual = self._pai_de(no_id)
        while atual is not None:
            nivel += 1
            atual = self._pai_de(atual)
        return nivel

    def subarvore(self, no_id: UUID) -> tuple[UUID, ...]:
        """O passo e todos os descendentes dele, em ordem estrutural."""
        self.ficha(no_id)
        return (no_id,) + descendentes(self._estrutura, no_id)

    def contar_subarvore(self, no_id: UUID) -> int:
        """RF-09: "N passos serão excluídos" — a consulta que a confirmação usa ANTES."""
        return len(self.subarvore(no_id))

    def ancestrais(self, no_id: UUID) -> tuple[UUID, ...]:
        """Do pai até a raiz. É o que mantém o contexto visível no filtro (RF-18)."""
        cadeia: list[UUID] = []
        atual = self._pai_de(no_id)
        while atual is not None:
            cadeia.append(atual)
            atual = self._pai_de(atual)
        return tuple(cadeia)

    def com_ancestrais(self, alvos: Iterable[UUID]) -> tuple[UUID, ...]:
        """RF-18: filtrar por status NÃO esconde os ancestrais — sem eles não há contexto."""
        visiveis: set[UUID] = set()
        for alvo in alvos:
            visiveis.add(alvo)
            visiveis.update(self.ancestrais(alvo))
        return tuple(no_id for no_id in self.ordem() if no_id in visiveis)

    def por_status(self, status: StatusDoPasso) -> tuple[UUID, ...]:
        alvo = StatusDoPasso(status)
        return tuple(no_id for no_id in self.ordem() if self._fichas[no_id].status is alvo)

    def linhas(self) -> tuple[LinhaDaArvore, ...]:
        """RF-19: a vista tabular indentada, em ordem estrutural fixa."""
        saida: list[LinhaDaArvore] = []
        for no_id in self.ordem():
            ficha = self._fichas[no_id]
            saida.append(
                LinhaDaArvore(
                    no_id=no_id,
                    numero=self._numeros[no_id],
                    nivel=self.nivel(no_id),
                    pai_id=self._pai_de(no_id),
                    estrategia=ficha.estrategia,
                    tatica=ficha.tatica,
                    status=ficha.status,
                    categoria=ficha.categoria,
                    filhos=len(self._estrutura.get(no_id, ())),
                    tem_premissa_paralela=bool(ficha.premissas.paralela),
                    tem_premissa_de_necessidade=bool(ficha.premissas.necessidade_ao_pai),
                    tem_premissa_de_suficiencia=bool(ficha.premissas.suficiencia_dos_filhos),
                )
            )
        return tuple(saida)

    def pendencias(self) -> PendenciasDaArvore:
        return pendencias_da_arvore(self._estrutura, self._fichas, self._numeros)

    # -- RF-13 · a leitura dirigida ----------------------------------------------

    def leituras(self, no_id: UUID) -> tuple[Leitura, Leitura, Leitura]:
        """As três premissas nos três papéis, montadas dos textos ATUAIS.

        A frase é montada aqui, no domínio, e não na tela: é regra do método — "para
        alcançar X é necessário Y porque…" —, e regra de método que mora na tela é regra
        que a segunda tela reescreve diferente.
        """
        ficha = self.ficha(no_id)
        numero = self._numeros[no_id]
        pai_id = self._pai_de(no_id)
        filhos = self._estrutura.get(no_id, ())
        premissas = ficha.premissas

        paralela = Leitura(
            papel="paralela",
            texto=(
                f"No contexto de <{numero}> {ficha.estrategia}, "
                f"{premissas.paralela or '…'}"
            ),
            aplicavel=True,
            completa=bool(premissas.paralela),
        )

        if pai_id is None:
            necessidade = Leitura(
                papel="necessidade_ao_pai",
                texto=f"<{numero}> é raiz do plano: não se lê contra pai nenhum",
                aplicavel=False,
                completa=True,
            )
        else:
            pai = self._fichas[pai_id]
            necessidade = Leitura(
                papel="necessidade_ao_pai",
                texto=(
                    f"Para alcançar <{self._numeros[pai_id]}> {pai.estrategia}, "
                    f"é necessário <{numero}> {ficha.estrategia} porque "
                    f"{premissas.necessidade_ao_pai or '…'}"
                ),
                aplicavel=True,
                completa=bool(premissas.necessidade_ao_pai),
            )

        if not filhos:
            suficiencia = Leitura(
                papel="suficiencia_dos_filhos",
                texto=f"<{numero}> ainda não tem filhos: não há suficiência a declarar",
                aplicavel=False,
                completa=True,
            )
        else:
            nomeados = " e ".join(
                f"<{self._numeros[f]}> {self._fichas[f].estrategia}" for f in filhos
            )
            suficiencia = Leitura(
                papel="suficiencia_dos_filhos",
                texto=(
                    f"{nomeados} bastam para <{numero}> {ficha.estrategia} porque "
                    f"{premissas.suficiencia_dos_filhos or '…'}"
                ),
                aplicavel=True,
                completa=bool(premissas.suficiencia_dos_filhos),
            )

        return paralela, necessidade, suficiencia

    # -- mutações ----------------------------------------------------------------

    def editar_meta_global(self, meta: str, *, em: datetime) -> str:
        """RF-02: a meta tem evento próprio — mudar o alvo do plano não é editar metadado."""
        self.projeto._exigir_ativo("editar_meta_global")
        self.meta_global = texto_de_dominio(
            meta, campo="meta_global", minimo=1, maximo=LIMITE_META
        )
        self.projeto._avancar(em)
        self._emitir(MetaGlobalEditada, em)
        return self.meta_global

    def adicionar_passo(
        self,
        *,
        estrategia: str,
        em: datetime,
        tatica: str = "",
        pai_id: UUID | None = None,
        posicao: int | None = None,
        premissas: PremissasDoPasso | None = None,
        categoria: CategoriaDoPasso | str = CategoriaDoPasso.NENHUMA,
        no_id: UUID | None = None,
    ) -> No:
        """RF-04: filho ou raiz, em posição entre irmãos — e **sem parâmetro de número**.

        A ficha é construída ANTES do nó: se a estratégia falta, nada nasce — a mesma
        ordem que a Árvore de Transição usa para a tripla obrigatória dela.
        """
        ficha = FichaDoPasso(
            estrategia=estrategia,
            tatica=tatica,
            premissas=premissas or PremissasDoPasso(),
            categoria=CategoriaDoPasso(categoria),
        )
        if pai_id is not None and pai_id not in self._fichas:
            raise PassoInvalido("pai_inexistente", f"{pai_id} não é um passo desta árvore")
        indice = self._indice_valido(pai_id, posicao, entre=len(self._estrutura.get(pai_id, ())))

        with self._nucleo() as nucleo:
            no = nucleo.adicionar_no(
                titulo=ficha.estrategia,
                tipo=TIPO_DE_NO_PASSO,
                posicao=PosicaoNoCanvas(),
                no_id=no_id,
                em=em,
            )
        self._fichas[no.id] = ficha
        irmaos = list(self._estrutura.get(pai_id, ()))
        irmaos.insert(indice, no.id)
        self._estrutura[pai_id] = tuple(irmaos)
        self._estrutura.setdefault(no.id, ())
        self._renumerar({pai_id})
        self._emitir(
            PassoDaSnTAdicionado, em, no_id=no.id, pai_id=pai_id, numero=self._numeros[no.id]
        )
        return no

    def editar_passo(
        self,
        no_id: UUID,
        *,
        em: datetime,
        estrategia: str | None = None,
        tatica: str | None = None,
        categoria: CategoriaDoPasso | str | None = None,
    ) -> FichaDoPasso:
        atual = self.ficha(no_id)
        nova = atual
        campos: list[str] = []
        if estrategia is not None:
            nova = replace(nova, estrategia=estrategia)
            campos.append("estrategia")
        if tatica is not None:
            nova = replace(nova, tatica=tatica)
            campos.append("tatica")
        if categoria is not None:
            nova = replace(nova, categoria=CategoriaDoPasso(categoria))
            campos.append("categoria")
        if not campos:
            raise MutacaoRecusada("editar_passo: nenhum campo informado")
        if "estrategia" in campos:
            # O título do nó do M1 É a estratégia: manter os dois em sincronia por dentro
            # da raiz evita a segunda fonte de verdade que envelheceria na primeira edição.
            with self._nucleo() as nucleo:
                nucleo.editar_no(no_id, titulo=nova.estrategia, em=em)
        else:
            self.projeto._exigir_ativo("editar_passo")
            self.projeto._avancar(em)
        self._fichas[no_id] = nova
        self._emitir(PassoDaSnTEditado, em, no_id=no_id, campos=tuple(campos))
        return nova

    def editar_premissas(
        self,
        no_id: UUID,
        *,
        em: datetime,
        paralela: str | None = None,
        necessidade_ao_pai: str | None = None,
        suficiencia_dos_filhos: str | None = None,
    ) -> FichaDoPasso:
        """RF-12/RN-06: as três premissas gravam sempre — ausência é pendência, não trava."""
        self.projeto._exigir_ativo("editar_premissas")
        atual = self.ficha(no_id)
        premissas = atual.premissas
        campos: list[str] = []
        if paralela is not None:
            premissas = replace(premissas, paralela=paralela)
            campos.append("paralela")
        if necessidade_ao_pai is not None:
            premissas = replace(premissas, necessidade_ao_pai=necessidade_ao_pai)
            campos.append("necessidade_ao_pai")
        if suficiencia_dos_filhos is not None:
            premissas = replace(premissas, suficiencia_dos_filhos=suficiencia_dos_filhos)
            campos.append("suficiencia_dos_filhos")
        if not campos:
            raise MutacaoRecusada("editar_premissas: nenhum campo informado")
        nova = replace(atual, premissas=premissas)
        self._fichas[no_id] = nova
        self.projeto._avancar(em)
        self._emitir(PremissasEditadas, em, no_id=no_id, campos=tuple(campos))
        return nova

    def mover_passo(
        self,
        no_id: UUID,
        *,
        novo_pai_id: UUID | None,
        em: datetime,
        posicao: int | None = None,
    ) -> tuple[str, str]:
        """RF-08: leva a subárvore inteira; devolve `(número antes, número depois)`.

        A recusa da RN-04 acontece **antes** de qualquer mutação: mover um passo para
        dentro da própria subárvore é a única topologia que a árvore estrita precisa
        proibir, porque todas as outras já são irrepresentáveis.
        """
        self.projeto._exigir_ativo("mover_passo")
        self.ficha(no_id)
        if novo_pai_id is not None and novo_pai_id not in self._fichas:
            raise MovimentoRecusado(
                "destino_inexistente", f"{novo_pai_id} não é um passo desta árvore"
            )
        if novo_pai_id is not None and novo_pai_id in self.subarvore(no_id):
            raise MovimentoRecusado(
                "para_a_propria_subarvore",
                f"{self._numeros[no_id]} não pode virar descendente de si mesmo",
            )

        pai_anterior = self._pai_de(no_id)
        numero_anterior = self._numeros[no_id]
        restantes = [x for x in self._estrutura.get(novo_pai_id, ()) if x != no_id]
        indice = self._indice_valido(novo_pai_id, posicao, entre=len(restantes))

        self._estrutura[pai_anterior] = tuple(
            x for x in self._estrutura.get(pai_anterior, ()) if x != no_id
        )
        restantes.insert(indice, no_id)
        self._estrutura[novo_pai_id] = tuple(restantes)
        self._renumerar({pai_anterior, novo_pai_id})

        self.projeto._avancar(em)
        quantos = len(descendentes(self._estrutura, no_id))
        self._emitir(
            PassoDaSnTMovido,
            em,
            no_id=no_id,
            pai_anterior_id=pai_anterior,
            pai_novo_id=novo_pai_id,
            numero_anterior=numero_anterior,
            numero_novo=self._numeros[no_id],
            descendentes=quantos,
        )
        return numero_anterior, self._numeros[no_id]

    def previa_da_renumeracao(
        self, no_id: UUID, *, novo_pai_id: UUID | None, posicao: int | None = None
    ) -> dict[UUID, str]:
        """RI-05: os números que o mover PRODUZIRIA — consulta pura, nada muta.

        Existe porque a spec manda pré-visualizar a renumeração antes de confirmar, e
        porque a alternativa (mover, mostrar, desfazer) grava um fato que ninguém pediu.
        """
        self.ficha(no_id)
        if novo_pai_id is not None and novo_pai_id in self.subarvore(no_id):
            raise MovimentoRecusado(
                "para_a_propria_subarvore",
                f"{self._numeros[no_id]} não pode virar descendente de si mesmo",
            )
        simulada = self.estrutura()
        pai_anterior = self._pai_de(no_id)
        simulada[pai_anterior] = tuple(
            x for x in simulada.get(pai_anterior, ()) if x != no_id
        )
        restantes = [x for x in simulada.get(novo_pai_id, ()) if x != no_id]
        indice = self._indice_valido(novo_pai_id, posicao, entre=len(restantes))
        restantes.insert(indice, no_id)
        simulada[novo_pai_id] = tuple(restantes)
        return numeracao(simulada)

    def excluir_subarvore(self, no_id: UUID, *, em: datetime) -> tuple[UUID, ...]:
        """RN-05: a subárvore EXATA, com a contagem no evento — o contraexemplo é F-07.

        `tocbuilderv3/services/mockApiService.ts:521` mantinha só o nó excluído e
        descartava todos os outros passos do projeto. Aqui a lista de removidos é
        calculada da estrutura, e nenhum passo fora dela é tocado.
        """
        self.projeto._exigir_ativo("excluir_subarvore")
        alvos = self.subarvore(no_id)
        numero = self._numeros[no_id]
        pai = self._pai_de(no_id)
        with self._nucleo() as nucleo:
            for alvo in reversed(alvos):
                nucleo.excluir_no(alvo, em=em)
        for alvo in alvos:
            self._fichas.pop(alvo, None)
            self._estrutura.pop(alvo, None)
        self._estrutura[pai] = tuple(x for x in self._estrutura.get(pai, ()) if x != no_id)
        self._renumerar({pai})
        self._emitir(
            SubarvoreExcluida, em, no_id=no_id, numero=numero, passos_excluidos=len(alvos)
        )
        return alvos

    def mudar_status(
        self, no_id: UUID, status: StatusDoPasso | str, *, autor: str, em: datetime
    ) -> FichaDoPasso:
        """RN-03: transição livre entre os quatro valores, com autor e data no evento.

        O que é recusado: mudar para o mesmo valor (`sem_mudanca`), mudar sem autor
        (`autor_obrigatorio`) e valor fora do vocabulário (`ValueError` do enum, traduzido
        na borda). Restringir a ORDEM das transições é o que a spec decidiu não fazer
        ([DÚVIDA] 2 → ADR 0014): plano real executa antes de a validação formal sair.
        """
        self.projeto._exigir_ativo("mudar_status")
        atual = self.ficha(no_id)
        novo = StatusDoPasso(status)
        if novo is atual.status:
            raise TransicaoDeStatusRecusada(
                "sem_mudanca", f"o passo já está {novo.value}"
            )
        if not (autor or "").strip():
            raise TransicaoDeStatusRecusada(
                "autor_obrigatorio", "mudança de status registra QUEM mudou (RN-03)"
            )
        ficha = replace(atual, status=novo)
        self._fichas[no_id] = ficha
        self.projeto._avancar(em)
        self._emitir(
            StatusDoPassoMudou,
            em,
            no_id=no_id,
            de=atual.status.value,
            para=novo.value,
            autor=autor.strip(),
        )
        return ficha

    # -- internos ------------------------------------------------------------------

    def _pai_de(self, no_id: UUID) -> UUID | None:
        for pai, filhos in self._estrutura.items():
            if no_id in filhos:
                return pai
        return None  # pragma: no cover - todo passo está em alguma lista de irmãos

    def _indice_valido(self, pai_id: UUID | None, posicao: int | None, *, entre: int) -> int:
        if posicao is None:
            return entre
        if isinstance(posicao, bool) or not isinstance(posicao, int):
            raise DadoInvalido("posicao: precisa ser inteiro")
        if posicao < 0 or posicao > entre:
            raise DadoInvalido(
                f"posicao: {posicao} fora da faixa 0..{entre} de irmãos deste pai"
            )
        return posicao

    def _renumerar(self, pais_afetados: Iterable[UUID | None]) -> None:
        self._numeros = renumerar(
            self._numeros, self._estrutura, pais_afetados=pais_afetados
        )

    def _emitir(self, classe, em: datetime, **carga) -> None:
        self.projeto.eventos = self.projeto.eventos + (
            classe(
                projeto_id=self.projeto.id,
                dono=self.projeto.dono,
                instante=em,
                **carga,
            ),
        )


def nova_arvore_snt(
    *,
    id: UUID,
    dono: DonoDoProjeto,
    nome: str,
    meta_global: str,
    em: datetime,
    descricao_do_problema: str = "",
) -> ArvoreSnT:
    """Cria o `Projeto` do M1 com a ferramenta certa e o embrulha na raiz da S&T."""
    projeto = Projeto(
        id=id,
        dono=dono,
        nome=nome,
        ferramenta=FERRAMENTA_SNT,
        descricao_do_problema=texto_de_dominio(
            descricao_do_problema,
            campo="descricao_do_problema",
            minimo=0,
            maximo=LIMITE_DESCRICAO,
        ),
        criado_em=em,
        alterado_em=em,
    )
    arvore = ArvoreSnT(projeto=projeto, meta_global=meta_global)
    arvore._emitir(ArvoreSnTCriada, em)
    return arvore


def reidratar_snt(
    projeto: Projeto,
    *,
    meta_global: str,
    fichas: Mapping[UUID, FichaDoPasso] | None = None,
    estrutura: Estrutura | None = None,
) -> ArvoreSnT:
    """Monta a árvore a partir do que estava GRAVADO — sem emitir evento nenhum.

    A numeração NÃO vem do banco: ela é recalculada aqui, da estrutura. É a RN-01 na
    fronteira da persistência — se o número viesse gravado, existiria um lugar onde
    estrutura e número poderiam discordar, e é esse lugar que este módulo não tem.
    """
    arvore = ArvoreSnT(
        projeto=projeto,
        meta_global=meta_global,
        _fichas=dict(fichas or {}),
        _estrutura={pai: tuple(filhos) for pai, filhos in (estrutura or {}).items()},
    )
    projeto.eventos = ()
    return arvore


# ---------------------------------------------------------------------------------------
# RF-21 · exportação e importação — e a numeração que NÃO viaja
# ---------------------------------------------------------------------------------------

#: A versão do formato canônico da árvore. Viaja no documento porque um arquivo sem versão
#: é um arquivo que ninguém migra depois.
VERSAO_DA_EXPORTACAO = "toc.snt/1"


def exportar_arvore_snt(arvore: ArvoreSnT) -> dict:
    """O documento canônico da S&T — determinístico, e **sem número de passo nenhum**.

    O que viaja é a estrutura: `pai` (por índice na própria lista) e a ordem. O número
    deriva na importação, e por isso divergência entre estrutura e numeração é impossível
    por construção (RN-01) — que é a diferença para o export da quarta geração, onde
    `stepNumber` digitado e `edges` livres podiam contar histórias diferentes.
    """
    ordem = arvore.ordem()
    indice = {no_id: i for i, no_id in enumerate(ordem)}
    passos = []
    for no_id in ordem:
        ficha = arvore.ficha(no_id)
        pai = arvore.pai(no_id)
        passos.append(
            {
                "pai": None if pai is None else indice[pai],
                "estrategia": ficha.estrategia,
                "tatica": ficha.tatica,
                "categoria": ficha.categoria.value,
                "status": ficha.status.value,
                "premissas": {
                    "paralela": ficha.premissas.paralela,
                    "necessidade_ao_pai": ficha.premissas.necessidade_ao_pai,
                    "suficiencia_dos_filhos": ficha.premissas.suficiencia_dos_filhos,
                },
            }
        )
    return {
        "versao": VERSAO_DA_EXPORTACAO,
        "nome": arvore.projeto.nome,
        "meta_global": arvore.meta_global,
        "passos": passos,
    }


def importar_arvore_snt(
    documento: Mapping[str, object], *, id: UUID, dono: DonoDoProjeto
) -> ArvoreSnT:
    """RF-21: ida e volta sem perda; o inquilino vem de QUEM IMPORTA, nunca do documento.

    A importação **não emite evento nenhum** de conteúdo: importar não é decompor o plano
    de novo. É a mesma regra de `reidratar_snt`, e pelo mesmo motivo — escrever história
    que não aconteceu é pior do que não ter história.
    """
    versao = documento.get("versao")
    if versao != VERSAO_DA_EXPORTACAO:
        raise DadoInvalido(
            f"exportação de versão {versao!r}; esta aplicação lê {VERSAO_DA_EXPORTACAO!r}"
        )
    brutos = list(documento.get("passos") or [])
    ids = [uuid4() for _ in brutos]
    fichas: dict[UUID, FichaDoPasso] = {}
    estrutura: dict[UUID | None, tuple[UUID, ...]] = {None: ()}
    for posicao, bruto in enumerate(brutos):
        premissas = bruto.get("premissas") or {}
        fichas[ids[posicao]] = FichaDoPasso(
            estrategia=bruto["estrategia"],
            tatica=bruto.get("tatica", ""),
            categoria=CategoriaDoPasso(bruto.get("categoria", CategoriaDoPasso.NENHUMA.value)),
            status=StatusDoPasso(bruto.get("status", StatusDoPasso.NENHUM.value)),
            premissas=PremissasDoPasso(
                paralela=premissas.get("paralela", ""),
                necessidade_ao_pai=premissas.get("necessidade_ao_pai", ""),
                suficiencia_dos_filhos=premissas.get("suficiencia_dos_filhos", ""),
            ),
        )
        indice_do_pai = bruto.get("pai")
        pai = None if indice_do_pai is None else ids[int(indice_do_pai)]
        estrutura[pai] = estrutura.get(pai, ()) + (ids[posicao],)
        estrutura.setdefault(ids[posicao], ())

    instante = datetime.fromtimestamp(0, tz=timezone.utc)
    projeto = Projeto(
        id=id,
        dono=dono,
        nome=str(documento.get("nome") or "S&T importada"),
        ferramenta=FERRAMENTA_SNT,
        criado_em=instante,
        alterado_em=instante,
        nos=tuple(
            No(id=ids[i], titulo=fichas[ids[i]].estrategia, tipo=TIPO_DE_NO_PASSO)
            for i in range(len(brutos))
        ),
    )
    return reidratar_snt(
        projeto,
        meta_global=str(documento.get("meta_global") or ""),
        fichas=fichas,
        estrutura=estrutura,
    )


__all__ = [
    "FERRAMENTA_SNT",
    "PENDENCIA_SEM_NECESSIDADE",
    "PENDENCIA_SEM_SUFICIENCIA",
    "PENDENCIA_SEM_TATICA",
    "SEPARADOR",
    "TIPO_DE_NO_PASSO",
    "VERSAO_DA_EXPORTACAO",
    "ArvoreSnT",
    "CategoriaDoPasso",
    "Estrutura",
    "FichaDoPasso",
    "Leitura",
    "LinhaDaArvore",
    "MovimentoRecusado",
    "PassoInvalido",
    "Pendencia",
    "PendenciasDaArvore",
    "PremissasDoPasso",
    "StatusDoPasso",
    "TransicaoDeStatusRecusada",
    "descendentes",
    "exportar_arvore_snt",
    "importar_arvore_snt",
    "nova_arvore_snt",
    "numeracao",
    "ordem_estrutural",
    "pendencias_da_arvore",
    "reidratar_snt",
    "renumerar",
]
