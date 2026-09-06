"""M3 — a Nuvem de Conflito (NC) sobre o núcleo do M1 (spec 007).

Siglas, uma vez neste arquivo: **NC** — Nuvem de Conflito · **TOC** — Teoria das
Restrições · **ARA** — Árvore da Realidade Atual · **UDE** — Efeito Indesejável ·
**ARF** — Árvore da Realidade Futura · **TRIZ** — Teoria da Resolução Inventiva de
Problemas · **FSM** — máquina de estados finitos · **IA** — inteligência artificial.

**Por composição, nunca por herança** — a mesma fronteira do M2 (`ara.py`): o M1 não
conhece semântica da TOC (RN-04 da spec 004), então `NuvemDeConflito` **contém** um
`Projeto` e acrescenta o que é da ferramenta. O que muda em relação à ARA é a topologia:
a ARA é grafo livre; a nuvem é **fixa** — 5 entidades e 7 arestas, criadas na origem e
indestrutíveis (RN-01).

Como a topologia fixa se apoia no núcleo sem duplicá-lo:

- cada entidade é um `No` do M1 cujo `tipo` carrega o papel (`nc_a` … `nc_d_prime`);
  `tipo` é enum extensível por decisão do próprio M1 (spec 004, RN-04);
- cada aresta é uma `ArestaCausal` do M1, e a **chave** (`A_B`, `D_C`, …) é **derivada do
  par de papéis** — não há coluna de chave para envelhecer, e não há como duas arestas
  reclamarem a mesma chave;
- a **classe** (necessidade, pré-requisito, perigo, conflito) é derivada da chave (RN-02),
  e a leitura por extenso sai dos textos **atuais** das entidades (RF-07).

O que a linhagem acertou e fica: a nuvem nascia inteira, com as 7 premissas criadas na
origem (`tocbuilderv3/services/mockApiService.ts:17-41`). O que ela não tinha e nasce
aqui: premissa como entidade (várias por aresta, com estado e arquivamento), injeção com
**referência obrigatória** à premissa que quebra (lá eram dois campos de texto pareados,
`types.ts:72-76`), FSM de status, classificação TRIZ e as duas costuras tipadas — a
origem (o dilema veio de UDEs da ARA) e a semeadura (a injeção escolhida semeará a ARF).
"""
from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Iterable, Iterator, Mapping, Sequence
from uuid import UUID, uuid4

from .erros import DadoInvalido, MutacaoRecusada, NaoEncontrado
from .eventos import (
    ORIGEM_DE_GERACAO,
    ORIGEM_HUMANA,
    EntidadeEditada,
    GeracaoAplicada,
    InjecaoEditada,
    InjecaoReclassificada,
    InjecaoRegistrada,
    NuvemCriada,
    NuvemDerivadaDeUde,
    PremissaArquivada,
    PremissaDesafiada,
    PremissaEditada,
    PremissaRegistrada,
    PremissaRevigorada,
    RacionalEditado,
    StatusDeInjecaoMudou,
)
from .formulacao import AvisoDeFormulacao, avaliar_formulacao
from .grafo import ArestaCausal, No
from .identidade import DonoDoProjeto
from .projeto import Projeto, registrar_raiz_de_ferramenta
from .valores import LIMITE_DESCRICAO, PosicaoNoCanvas, texto as texto_de_dominio

if TYPE_CHECKING:  # pragma: no cover - só para o verificador de tipos
    from .ara import ProjetoARA
    from .geracao import ResultadoDeGeracao

#: O tipo de projeto do M3 (spec 007, RF-01) — o M1 nunca precisa saber deste nome.
FERRAMENTA_NC = "nc"

#: A NC é a RAIZ do agregado do M3: o grafo de um projeto `nc` só muda por dentro
#: dela (`Projeto._exigir_raiz`). O núcleo do M1 não importa este módulo — quem se
#: anuncia é a ferramenta, e o nome serve à mensagem de recusa da borda.
registrar_raiz_de_ferramenta(FERRAMENTA_NC, "NuvemDeConflito")

LIMITE_PREMISSA = 1000
LIMITE_INJECAO = 1000
LIMITE_RACIONAL = 4000
LIMITE_TEXTO_DE_ENTIDADE = 300


class PapelDaEntidade(str, Enum):
    """Os 5 papéis, grafados como na linhagem (`tocbuilderv3/types.ts:69`).

    `D_PRIME` no dado, `D′` na interface: a grafia com apóstrofo não atravessa banco,
    JSON e URL sem virar três grafias diferentes.
    """

    A = "A"
    B = "B"
    C = "C"
    D = "D"
    D_PRIME = "D_PRIME"


class ChaveDaAresta(str, Enum):
    """As 7 chaves, verbatim da linhagem (`tocbuilderv3/types.ts:73`)."""

    A_B = "A_B"
    A_C = "A_C"
    B_D = "B_D"
    C_D_PRIME = "C_D_PRIME"
    D_C = "D_C"
    D_PRIME_B = "D_PRIME_B"
    D_D_PRIME = "D_D_PRIME"


class ClasseDaAresta(str, Enum):
    """RN-02: a classe é derivada da chave, e cada classe tem leitura própria (RF-07)."""

    NECESSIDADE = "necessidade"
    PRE_REQUISITO = "pre_requisito"
    PERIGO = "perigo"
    CONFLITO = "conflito"


class EstadoDaPremissa(str, Enum):
    VIGENTE = "vigente"
    DESAFIADA = "desafiada"


class StatusDeInjecao(str, Enum):
    """RN-08: `candidata → escolhida | descartada`, com retorno justificado."""

    CANDIDATA = "candidata"
    ESCOLHIDA = "escolhida"
    DESCARTADA = "descartada"


class SeparacaoTRIZ(str, Enum):
    """As 5 separações do método — o mapa de cobertura do conflito D↯D′ (RN-07)."""

    ESPACO = "espaco"
    TEMPO = "tempo"
    PARTES = "partes"
    GRAU = "grau"
    CONDICAO = "condicao"


#: `papel → tipo de nó do M1`. O tipo é o que faz o papel sobreviver ao banco sem tabela
#: nova: quem reidrata lê o `tipo` do nó e sabe qual entidade é.
TIPO_DE_NO_POR_PAPEL: dict[PapelDaEntidade, str] = {
    PapelDaEntidade.A: "nc_a",
    PapelDaEntidade.B: "nc_b",
    PapelDaEntidade.C: "nc_c",
    PapelDaEntidade.D: "nc_d",
    PapelDaEntidade.D_PRIME: "nc_d_prime",
}
PAPEL_POR_TIPO_DE_NO: dict[str, PapelDaEntidade] = {
    tipo: papel for papel, tipo in TIPO_DE_NO_POR_PAPEL.items()
}

#: `chave → (papel de origem, papel de destino)`. É desta tabela que sai TUDO: a criação
#: das 7 arestas, a derivação da chave a partir de uma aresta e a leitura por extenso.
PAR_DA_ARESTA: dict[ChaveDaAresta, tuple[PapelDaEntidade, PapelDaEntidade]] = {
    ChaveDaAresta.A_B: (PapelDaEntidade.B, PapelDaEntidade.A),
    ChaveDaAresta.A_C: (PapelDaEntidade.C, PapelDaEntidade.A),
    ChaveDaAresta.B_D: (PapelDaEntidade.D, PapelDaEntidade.B),
    ChaveDaAresta.C_D_PRIME: (PapelDaEntidade.D_PRIME, PapelDaEntidade.C),
    ChaveDaAresta.D_C: (PapelDaEntidade.D, PapelDaEntidade.C),
    ChaveDaAresta.D_PRIME_B: (PapelDaEntidade.D_PRIME, PapelDaEntidade.B),
    ChaveDaAresta.D_D_PRIME: (PapelDaEntidade.D, PapelDaEntidade.D_PRIME),
}
CHAVE_POR_PAR: dict[tuple[PapelDaEntidade, PapelDaEntidade], ChaveDaAresta] = {
    par: chave for chave, par in PAR_DA_ARESTA.items()
}

CLASSE_POR_CHAVE: dict[ChaveDaAresta, ClasseDaAresta] = {
    ChaveDaAresta.A_B: ClasseDaAresta.NECESSIDADE,
    ChaveDaAresta.A_C: ClasseDaAresta.NECESSIDADE,
    ChaveDaAresta.B_D: ClasseDaAresta.PRE_REQUISITO,
    ChaveDaAresta.C_D_PRIME: ClasseDaAresta.PRE_REQUISITO,
    ChaveDaAresta.D_C: ClasseDaAresta.PERIGO,
    ChaveDaAresta.D_PRIME_B: ClasseDaAresta.PERIGO,
    ChaveDaAresta.D_D_PRIME: ClasseDaAresta.CONFLITO,
}

#: A leitura por extenso de cada classe (RF-07) — `{origem}` e `{destino}` são os textos
#: ATUAIS das entidades, nunca cópia congelada.
LEITURA_POR_CLASSE: dict[ClasseDaAresta, str] = {
    ClasseDaAresta.NECESSIDADE: "Para ter {destino}, precisamos de {origem}",
    ClasseDaAresta.PRE_REQUISITO: "Para ter {destino}, devemos {origem}",
    ClasseDaAresta.PERIGO: "{origem} ameaça {destino}",
    ClasseDaAresta.CONFLITO: "{origem} e {destino} não podem coexistir",
}

#: RF-02: texto de exemplo **neutro**, o mesmo papel que o helper da linhagem cumpria
#: (`createEmptyConflictCloudData`). Neutro quer dizer: diz o que a posição é, não sugere
#: conteúdo — a nuvem é do dilema de quem a escreve.
TEXTO_DE_EXEMPLO: dict[PapelDaEntidade, str] = {
    PapelDaEntidade.A: "[A] Objetivo comum",
    PapelDaEntidade.B: "[B] Necessidade 1",
    PapelDaEntidade.C: "[C] Necessidade 2",
    PapelDaEntidade.D: "[D] Ação 1",
    PapelDaEntidade.D_PRIME: "[D′] Ação 2",
}

#: Posição canônica de cada papel no canvas (RI-01): A à esquerda, B/C ao centro, D/D′ à
#: direita. Mora no domínio porque é o que faz a nuvem nascer **desenhada** — a interface
#: não arruma caixas, e o usuário edita texto.
POSICAO_CANONICA: dict[PapelDaEntidade, tuple[float, float]] = {
    PapelDaEntidade.A: (0.0, 160.0),
    PapelDaEntidade.B: (280.0, 40.0),
    PapelDaEntidade.C: (280.0, 280.0),
    PapelDaEntidade.D: (560.0, 40.0),
    PapelDaEntidade.D_PRIME: (560.0, 280.0),
}

#: A FSM do status da injeção (RN-08) — tabela, não `if`. O retorno a `candidata` existe
#: nos dois sentidos e exige justificativa; `escolhida → descartada` **não** existe: o
#: grupo que mudou de ideia reabre a injeção antes de descartá-la, e isso fica no evento.
TRANSICOES_DE_INJECAO: dict[StatusDeInjecao, frozenset[StatusDeInjecao]] = {
    StatusDeInjecao.CANDIDATA: frozenset({StatusDeInjecao.ESCOLHIDA, StatusDeInjecao.DESCARTADA}),
    StatusDeInjecao.ESCOLHIDA: frozenset({StatusDeInjecao.CANDIDATA}),
    StatusDeInjecao.DESCARTADA: frozenset({StatusDeInjecao.CANDIDATA}),
}


# --------------------------------------------------------------------------------------
# Erros — cada um com a REGRA nomeada, para a borda traduzir sem adivinhar por texto
# --------------------------------------------------------------------------------------


class TopologiaImutavel(MutacaoRecusada):
    """RN-01/RF-03. `regra`: `topologia_fixa` (tentou criar/excluir) ou
    `topologia_incompleta` (o projeto não tem as 5 entidades e as 7 arestas)."""

    def __init__(self, regra: str, detalhe: str = "") -> None:
        super().__init__(f"{regra}: {detalhe}" if detalhe else regra)
        self.regra = regra


class PremissaInvalida(MutacaoRecusada):
    """`regra`: `justificativa_obrigatoria` · `ordem_incompleta` · `premissa_arquivada`."""

    def __init__(self, regra: str, detalhe: str = "") -> None:
        super().__init__(f"{regra}: {detalhe}" if detalhe else regra)
        self.regra = regra


class InjecaoInvalida(MutacaoRecusada):
    """RN-04. `regra`: `premissa_arquivada` · `injecao_arquivada`."""

    def __init__(self, regra: str, detalhe: str = "") -> None:
        super().__init__(f"{regra}: {detalhe}" if detalhe else regra)
        self.regra = regra


class TransicaoDeInjecaoRecusada(MutacaoRecusada):
    """RN-08. `motivo`: `transicao_invalida` · `retorno_sem_justificativa` · `sem_mudanca`."""

    def __init__(self, motivo: str, detalhe: str = "") -> None:
        super().__init__(f"{motivo}: {detalhe}" if detalhe else motivo)
        self.motivo = motivo


class DerivacaoInvalida(MutacaoRecusada):
    """INT-05. `regra`: `sem_ude` · `no_nao_e_ude` · `ude_rejeitado`."""

    def __init__(self, regra: str, detalhe: str = "") -> None:
        super().__init__(f"{regra}: {detalhe}" if detalhe else regra)
        self.regra = regra


# --------------------------------------------------------------------------------------
# Entidades internas e objetos de valor
# --------------------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class ReferenciaDeOrigem:
    """A costura M2 → M3, **tipada** (INT-05).

    Tipada é o ponto: na linhagem, ARA e NC eram dois bancos simulados sem uma referência
    entre si (`tocbuilderv3/services/mockApiService.ts:10-14`). Aqui "de onde esta nuvem
    veio" é dado do agregado — ferramenta, projeto e os UDEs —, e não convenção de nome
    nem texto colado na descrição.
    """

    ferramenta: str
    projeto_id: UUID
    nos: tuple[UUID, ...]

    def __post_init__(self) -> None:
        if not (self.ferramenta or "").strip():
            raise DadoInvalido("origem: ferramenta de origem é obrigatória")
        if not self.nos:
            raise DadoInvalido("origem: sem nó de origem, a referência não diz nada")


@dataclass(frozen=True, slots=True)
class ReferenciaDeSemeadura:
    """A costura M3 → M4 (INT-06). Nasce com destino vazio: quem o preenche é o ciclo 008."""

    injecao_id: UUID
    projeto_destino_id: UUID | None = None


@dataclass(slots=True)
class Premissa:
    """O que sustenta uma aresta. Dado de primeira classe, nunca legenda decorativa."""

    id: UUID
    aresta: ChaveDaAresta
    texto: str
    ordem: int = 0
    estado: EstadoDaPremissa = EstadoDaPremissa.VIGENTE
    justificativa: str = ""
    arquivada: bool = False

    def __post_init__(self) -> None:
        self.texto = texto_de_dominio(
            self.texto, campo="premissa.texto", minimo=1, maximo=LIMITE_PREMISSA
        )
        self.aresta = ChaveDaAresta(self.aresta)
        self.estado = EstadoDaPremissa(self.estado)

    @property
    def sustenta(self) -> bool:
        """Só premissa vigente e não arquivada sustenta a aresta (RN-03)."""
        return self.estado is EstadoDaPremissa.VIGENTE and not self.arquivada


@dataclass(slots=True)
class Injecao:
    """A solução que quebra uma premissa nomeada — nunca uma ideia solta (RN-04)."""

    id: UUID
    premissa_id: UUID
    texto: str
    status: StatusDeInjecao = StatusDeInjecao.CANDIDATA
    separacao: SeparacaoTRIZ | None = None
    arquivada: bool = False
    semeadura: ReferenciaDeSemeadura | None = None

    def __post_init__(self) -> None:
        self.texto = texto_de_dominio(
            self.texto, campo="injecao.texto", minimo=1, maximo=LIMITE_INJECAO
        )
        self.status = StatusDeInjecao(self.status)
        if self.separacao is not None:
            self.separacao = SeparacaoTRIZ(self.separacao)


@dataclass(frozen=True, slots=True)
class ValidacaoDaNuvem:
    """Serviço de domínio, função pura: completude, avisos e pendências (RF-14, RF-31).

    Não muta nada, não fala com rede e não chama modelo. É o que a interface consome para
    mostrar progresso — e progresso, aqui, **informa e prioriza; nunca trava** (RN-03).
    """

    arestas_sustentadas: tuple[ChaveDaAresta, ...]
    arestas_sem_premissa: tuple[ChaveDaAresta, ...]
    arestas_sem_injecao: tuple[ChaveDaAresta, ...]
    avisos: Mapping[PapelDaEntidade, tuple[AvisoDeFormulacao, ...]]
    separacoes_ausentes: tuple[SeparacaoTRIZ, ...]

    @property
    def completude(self) -> tuple[int, int]:
        return (len(self.arestas_sustentadas), len(ChaveDaAresta))

    @property
    def modelada(self) -> bool:
        """RN-03: nuvem modelada é nuvem com as 7 arestas sustentadas por premissa vigente."""
        return len(self.arestas_sustentadas) == len(ChaveDaAresta)

    def resumo(self) -> dict[str, int | bool]:
        return {
            "arestas_sustentadas": len(self.arestas_sustentadas),
            "arestas_no_total": len(ChaveDaAresta),
            "arestas_sem_injecao": len(self.arestas_sem_injecao),
            "entidades_com_aviso": sum(1 for a in self.avisos.values() if a),
            "separacoes_triz_ausentes": len(self.separacoes_ausentes),
            "modelada": self.modelada,
        }


# --------------------------------------------------------------------------------------
# O agregado
# --------------------------------------------------------------------------------------


@dataclass(slots=True)
class NuvemDeConflito:
    """A NC: um `Projeto` do M1 de topologia fixa mais a semântica da ferramenta."""

    projeto: Projeto
    racional: str = ""
    origem: ReferenciaDeOrigem | None = None
    _premissas: dict[UUID, Premissa] = field(default_factory=dict)
    _injecoes: dict[UUID, Injecao] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.projeto.ferramenta != FERRAMENTA_NC:
            raise MutacaoRecusada(
                f"NuvemDeConflito exige ferramenta {FERRAMENTA_NC!r}, "
                f"veio {self.projeto.ferramenta!r}"
            )
        self._exigir_topologia()

    # -- a única porta para o `Projeto` contido ----------------------------------

    @contextmanager
    def _nucleo(self) -> Iterator[Projeto]:
        """Abre o núcleo do M1 PARA A RAIZ. Toda delegação da nuvem passa por aqui.

        Fora deste `with`, o `Projeto` de uma nuvem recusa mutação de grafo — é o que
        fecha a porta dos fundos que as rotas genéricas de `/toc/projetos` abriam.
        """
        with self.projeto.sob_a_raiz() as nucleo:
            yield nucleo

    # -- topologia: a invariante central (RN-01) ---------------------------------

    def _exigir_topologia(self) -> None:
        papeis = [PAPEL_POR_TIPO_DE_NO.get(n.tipo) for n in self.projeto.nos]
        if sorted(p.value for p in papeis if p) != sorted(p.value for p in PapelDaEntidade):
            raise TopologiaImutavel(
                "topologia_incompleta",
                f"a nuvem tem exatamente 5 entidades (A, B, C, D, D′); vieram "
                f"{len(self.projeto.nos)} nó(s) com papéis {sorted(str(p) for p in papeis)}",
            )
        chaves = sorted(self.chave_da_aresta(a.id).value for a in self.projeto.arestas)
        if chaves != sorted(c.value for c in ChaveDaAresta):
            raise TopologiaImutavel(
                "topologia_incompleta",
                f"a nuvem tem exatamente 7 arestas; vieram {chaves}",
            )

    # -- consultas ---------------------------------------------------------------

    @property
    def entidades(self) -> tuple[No, ...]:
        return self.projeto.nos

    @property
    def arestas(self) -> tuple[ArestaCausal, ...]:
        return self.projeto.arestas

    @property
    def papeis(self) -> tuple[PapelDaEntidade, ...]:
        return tuple(PAPEL_POR_TIPO_DE_NO[n.tipo] for n in self.projeto.nos)

    @property
    def chaves(self) -> tuple[ChaveDaAresta, ...]:
        return tuple(self.chave_da_aresta(a.id) for a in self.projeto.arestas)

    @property
    def eventos(self):
        return self.projeto.eventos

    def drenar_eventos(self):
        return self.projeto.drenar_eventos()

    def entidade(self, papel: PapelDaEntidade) -> No:
        alvo = TIPO_DE_NO_POR_PAPEL[PapelDaEntidade(papel)]
        for no in self.projeto.nos:
            if no.tipo == alvo:
                return no
        raise NaoEncontrado(f"entidade:{papel}")  # pragma: no cover - a invariante impede

    def texto(self, papel: PapelDaEntidade) -> str:
        return self.entidade(papel).titulo

    def papel_do_no(self, no_id: UUID) -> PapelDaEntidade:
        return PAPEL_POR_TIPO_DE_NO[self.projeto.no(no_id).tipo]

    def chave_da_aresta(self, aresta_id: UUID) -> ChaveDaAresta:
        """A chave é DERIVADA do par de papéis — nunca digitada, nunca gravada torta."""
        aresta = self.projeto.aresta(aresta_id)
        par = (self.papel_do_no(aresta.origem_id), self.papel_do_no(aresta.destino_id))
        try:
            return CHAVE_POR_PAR[par]
        except KeyError as ausente:  # pragma: no cover - a invariante impede
            raise TopologiaImutavel(
                "topologia_incompleta", f"par de papéis fora da nuvem: {par}"
            ) from ausente

    def aresta(self, chave: ChaveDaAresta) -> ArestaCausal:
        chave = ChaveDaAresta(chave)
        origem, destino = PAR_DA_ARESTA[chave]
        ids = (self.entidade(origem).id, self.entidade(destino).id)
        for candidata in self.projeto.arestas:
            if candidata.par == ids:
                return candidata
        raise NaoEncontrado(f"aresta:{chave.value}")  # pragma: no cover - invariante

    def classe(self, chave: ChaveDaAresta) -> ClasseDaAresta:
        return CLASSE_POR_CHAVE[ChaveDaAresta(chave)]

    def leitura(self, chave: ChaveDaAresta) -> str:
        """RF-07: montada dos textos ATUAIS — editar a entidade muda todas as leituras."""
        chave = ChaveDaAresta(chave)
        origem, destino = PAR_DA_ARESTA[chave]
        modelo = LEITURA_POR_CLASSE[self.classe(chave)]
        return modelo.format(origem=self.texto(origem), destino=self.texto(destino))

    def leitura_da_origem(self) -> str:
        """INT-05: "origem: UDEs …" quando houver — e string vazia quando não houver."""
        if self.origem is None:
            return ""
        return (
            f"Origem: {len(self.origem.nos)} Efeito(s) Indesejável(is) da Árvore da "
            f"Realidade Atual (projeto {self.origem.projeto_id})"
        )

    # -- a topologia recusa criar e excluir (RF-03) ------------------------------

    def adicionar_entidade(self, **_: object) -> No:
        raise TopologiaImutavel(
            "topologia_fixa",
            "a nuvem tem exatamente 5 entidades, criadas na origem: preencha, não crie",
        )

    def excluir_entidade(self, *_: object, **__: object) -> None:
        raise TopologiaImutavel(
            "topologia_fixa",
            "entidade da nuvem não se exclui; o vocabulário de mutação é editar texto",
        )

    def ligar(self, *_: object, **__: object) -> ArestaCausal:
        raise TopologiaImutavel(
            "topologia_fixa", "as 7 arestas nascem com a nuvem e não se criam"
        )

    def excluir_aresta(self, *_: object, **__: object) -> None:
        raise TopologiaImutavel(
            "topologia_fixa", "as 7 arestas nascem com a nuvem e não se destroem"
        )

    # -- edição de entidade e racional (RF-05, RF-06) ----------------------------

    def editar_entidade(
        self,
        papel: PapelDaEntidade,
        texto: str,
        *,
        em: datetime,
        origem: str = ORIGEM_HUMANA,
        proposta_id: str | None = None,
    ) -> No:
        papel = PapelDaEntidade(papel)
        no = self.entidade(papel)
        # A validação de texto é do M1 (`editar_no`): reaproveitar é o ponto da composição.
        with self._nucleo() as nucleo:
            nucleo.editar_no(no.id, titulo=texto, em=em)
        # `editar_no` já emitiu `NoEditado`; o evento do M3 é o que carrega o PAPEL e a
        # origem, que é o vocabulário desta ferramenta.
        self._emitir(
            EntidadeEditada, em, papel=papel.value, origem=origem, proposta_id=proposta_id
        )
        return no

    def editar_racional(
        self,
        racional: str,
        *,
        em: datetime,
        origem: str = ORIGEM_HUMANA,
        proposta_id: str | None = None,
    ) -> str:
        self.projeto._exigir_ativo("editar_racional")
        self.racional = texto_de_dominio(
            racional, campo="racional", minimo=0, maximo=LIMITE_RACIONAL
        )
        self.projeto._avancar(em)
        self._emitir(RacionalEditado, em, origem=origem, proposta_id=proposta_id)
        return self.racional

    # -- premissas (RF-12..RF-15) -------------------------------------------------

    def premissa(self, premissa_id: UUID) -> Premissa:
        try:
            return self._premissas[premissa_id]
        except KeyError as ausente:
            raise NaoEncontrado(f"premissa:{premissa_id}") from ausente

    def premissas(self, chave: ChaveDaAresta | None = None) -> tuple[Premissa, ...]:
        """As premissas VIVAS, ordenadas. Arquivada não aparece — mas continua no dado."""
        vivas = [p for p in self._premissas.values() if not p.arquivada]
        if chave is not None:
            alvo = ChaveDaAresta(chave)
            vivas = [p for p in vivas if p.aresta is alvo]
        return tuple(sorted(vivas, key=lambda p: (p.aresta.value, p.ordem)))

    def registrar_premissa(
        self,
        chave: ChaveDaAresta,
        texto: str,
        *,
        em: datetime,
        premissa_id: UUID | None = None,
        origem: str = ORIGEM_HUMANA,
        proposta_id: str | None = None,
    ) -> Premissa:
        self.projeto._exigir_ativo("registrar_premissa")
        chave = ChaveDaAresta(chave)
        nova = Premissa(
            id=premissa_id or uuid4(),
            aresta=chave,
            texto=texto,
            ordem=len(self.premissas(chave)),
        )
        self._premissas[nova.id] = nova
        self.projeto._avancar(em)
        self._emitir(
            PremissaRegistrada,
            em,
            premissa_id=nova.id,
            aresta=chave.value,
            origem=origem,
            proposta_id=proposta_id,
        )
        return nova

    def editar_premissa(
        self,
        premissa_id: UUID,
        texto: str,
        *,
        em: datetime,
        origem: str = ORIGEM_HUMANA,
        proposta_id: str | None = None,
    ) -> Premissa:
        self.projeto._exigir_ativo("editar_premissa")
        alvo = self._exigir_premissa_viva(premissa_id)
        alvo.texto = texto_de_dominio(
            texto, campo="premissa.texto", minimo=1, maximo=LIMITE_PREMISSA
        )
        self.projeto._avancar(em)
        self._emitir(
            PremissaEditada,
            em,
            premissa_id=premissa_id,
            origem=origem,
            proposta_id=proposta_id,
        )
        return alvo

    def reordenar_premissas(
        self, chave: ChaveDaAresta, ordem: Sequence[UUID], *, em: datetime
    ) -> tuple[Premissa, ...]:
        self.projeto._exigir_ativo("reordenar_premissas")
        chave = ChaveDaAresta(chave)
        atuais = {p.id for p in self.premissas(chave)}
        if set(ordem) != atuais or len(set(ordem)) != len(ordem):
            raise PremissaInvalida(
                "ordem_incompleta",
                "a nova ordem tem de citar exatamente as premissas vivas desta aresta",
            )
        for posicao, premissa_id in enumerate(ordem):
            self._premissas[premissa_id].ordem = posicao
        self.projeto._avancar(em)
        self._emitir(PremissaEditada, em, premissa_id=None, campo="ordem")
        return self.premissas(chave)

    def desafiar_premissa(
        self, premissa_id: UUID, *, justificativa: str, em: datetime
    ) -> Premissa:
        """RF-13: desafiar exige justificativa — o evento guarda autor (dono) e motivo."""
        self.projeto._exigir_ativo("desafiar_premissa")
        alvo = self._exigir_premissa_viva(premissa_id)
        motivo = (justificativa or "").strip()
        if not motivo:
            raise PremissaInvalida(
                "justificativa_obrigatoria",
                "marcar uma premissa como desafiada exige dizer por quê (RF-13)",
            )
        alvo.estado = EstadoDaPremissa.DESAFIADA
        alvo.justificativa = motivo
        self.projeto._avancar(em)
        self._emitir(
            PremissaDesafiada, em, premissa_id=premissa_id, justificativa=motivo
        )
        return alvo

    def revigorar_premissa(self, premissa_id: UUID, *, em: datetime) -> Premissa:
        self.projeto._exigir_ativo("revigorar_premissa")
        alvo = self._exigir_premissa_viva(premissa_id)
        alvo.estado = EstadoDaPremissa.VIGENTE
        alvo.justificativa = ""
        self.projeto._avancar(em)
        self._emitir(PremissaRevigorada, em, premissa_id=premissa_id)
        return alvo

    def arquivar_premissa(self, premissa_id: UUID, *, em: datetime) -> int:
        """RF-15: arquiva a premissa e as injeções dela. Devolve QUANTAS foram junto."""
        self.projeto._exigir_ativo("arquivar_premissa")
        alvo = self._exigir_premissa_viva(premissa_id)
        junto = [
            i for i in self._injecoes.values()
            if i.premissa_id == alvo.id and not i.arquivada
        ]
        for injecao in junto:
            injecao.arquivada = True
        alvo.arquivada = True
        self.projeto._avancar(em)
        self._emitir(
            PremissaArquivada,
            em,
            premissa_id=alvo.id,
            injecoes_arquivadas=len(junto),
        )
        return len(junto)

    def _exigir_premissa_viva(self, premissa_id: UUID) -> Premissa:
        alvo = self.premissa(premissa_id)
        if alvo.arquivada:
            raise PremissaInvalida(
                "premissa_arquivada", f"a premissa {premissa_id} está arquivada"
            )
        return alvo

    # -- injeções (RF-16..RF-20) --------------------------------------------------

    def injecao(self, injecao_id: UUID) -> Injecao:
        try:
            return self._injecoes[injecao_id]
        except KeyError as ausente:
            raise NaoEncontrado(f"injecao:{injecao_id}") from ausente

    def injecoes_da_premissa(self, premissa_id: UUID) -> tuple[Injecao, ...]:
        return tuple(
            i for i in self._injecoes.values()
            if i.premissa_id == premissa_id and not i.arquivada
        )

    def injecoes_da_aresta(self, chave: ChaveDaAresta) -> tuple[Injecao, ...]:
        chave = ChaveDaAresta(chave)
        das_premissas = {p.id for p in self.premissas(chave)}
        return tuple(
            i for i in self._injecoes.values()
            if i.premissa_id in das_premissas and not i.arquivada
        )

    def registrar_injecao(
        self,
        premissa_id: UUID,
        texto: str,
        *,
        em: datetime,
        separacao: SeparacaoTRIZ | None = None,
        injecao_id: UUID | None = None,
        origem: str = ORIGEM_HUMANA,
        proposta_id: str | None = None,
    ) -> Injecao:
        """RN-04: não existe construtor de injeção sem premissa existente e viva."""
        self.projeto._exigir_ativo("registrar_injecao")
        alvo = self.premissa(premissa_id)  # NaoEncontrado quando a premissa não existe
        if alvo.arquivada:
            raise InjecaoInvalida(
                "premissa_arquivada",
                "injeção só referencia premissa viva — arquivada não recebe injeção nova",
            )
        nova = Injecao(
            id=injecao_id or uuid4(),
            premissa_id=alvo.id,
            texto=texto,
            separacao=separacao,
        )
        self._injecoes[nova.id] = nova
        self.projeto._avancar(em)
        self._emitir(
            InjecaoRegistrada,
            em,
            injecao_id=nova.id,
            premissa_id=alvo.id,
            origem=origem,
            proposta_id=proposta_id,
        )
        return nova

    def editar_injecao(
        self,
        injecao_id: UUID,
        texto: str,
        *,
        em: datetime,
        origem: str = ORIGEM_HUMANA,
        proposta_id: str | None = None,
    ) -> Injecao:
        self.projeto._exigir_ativo("editar_injecao")
        alvo = self._exigir_injecao_viva(injecao_id)
        alvo.texto = texto_de_dominio(
            texto, campo="injecao.texto", minimo=1, maximo=LIMITE_INJECAO
        )
        self.projeto._avancar(em)
        self._emitir(
            InjecaoEditada, em, injecao_id=injecao_id, origem=origem, proposta_id=proposta_id
        )
        return alvo

    def classificar_injecao(
        self, injecao_id: UUID, separacao: SeparacaoTRIZ | None, *, em: datetime
    ) -> Injecao:
        """RF-18: a classificação TRIZ vale para qualquer injeção; é esperada em D↯D′."""
        self.projeto._exigir_ativo("classificar_injecao")
        alvo = self._exigir_injecao_viva(injecao_id)
        alvo.separacao = SeparacaoTRIZ(separacao) if separacao is not None else None
        self.projeto._avancar(em)
        self._emitir(
            InjecaoReclassificada,
            em,
            injecao_id=injecao_id,
            separacao=alvo.separacao.value if alvo.separacao else None,
        )
        return alvo

    def mudar_status_de_injecao(
        self,
        injecao_id: UUID,
        novo: StatusDeInjecao,
        *,
        em: datetime,
        justificativa: str = "",
    ) -> Injecao:
        """RN-08: a FSM é tabela; o retorno a `candidata` exige justificativa."""
        self.projeto._exigir_ativo("mudar_status_de_injecao")
        alvo = self._exigir_injecao_viva(injecao_id)
        novo = StatusDeInjecao(novo)
        atual = alvo.status
        if novo is atual:
            raise TransicaoDeInjecaoRecusada("sem_mudanca", f"já está em {atual.value}")
        if novo not in TRANSICOES_DE_INJECAO[atual]:
            raise TransicaoDeInjecaoRecusada(
                "transicao_invalida",
                f"{atual.value} → {novo.value} não está na FSM; os destinos possíveis são "
                f"{sorted(s.value for s in TRANSICOES_DE_INJECAO[atual])}",
            )
        if novo is StatusDeInjecao.CANDIDATA and not justificativa.strip():
            raise TransicaoDeInjecaoRecusada(
                "retorno_sem_justificativa",
                "voltar uma injeção a candidata exige justificativa explícita (RN-08)",
            )
        alvo.status = novo
        # RF-20: escolher prepara a semeadura da ARF — com destino VAZIO. Criar árvore é
        # do ciclo 008; o que este ciclo entrega é o lugar onde ela será anotada.
        if novo is StatusDeInjecao.ESCOLHIDA:
            alvo.semeadura = ReferenciaDeSemeadura(injecao_id=alvo.id)
        else:
            alvo.semeadura = None
        self.projeto._avancar(em)
        self._emitir(
            StatusDeInjecaoMudou,
            em,
            injecao_id=alvo.id,
            de=atual.value,
            para=novo.value,
            justificativa=justificativa.strip(),
        )
        return alvo

    def semeaduras(self) -> tuple[ReferenciaDeSemeadura, ...]:
        return tuple(
            i.semeadura for i in self._injecoes.values()
            if i.semeadura is not None and not i.arquivada
        )

    def _exigir_injecao_viva(self, injecao_id: UUID) -> Injecao:
        alvo = self.injecao(injecao_id)
        if alvo.arquivada:
            raise InjecaoInvalida(
                "injecao_arquivada", f"a injeção {injecao_id} está arquivada"
            )
        return alvo

    # -- visões e validação (RF-14, RF-30..RF-34) ---------------------------------

    def visao_de_solucao(self) -> dict[ChaveDaAresta, tuple[Injecao, ...]]:
        """RF-31: **as 7 posições**, sempre — com injeção ou com pendência explícita.

        O defeito que isto fecha está medido: em
        `tocbuilderv3/components/ConflictCloudView.tsx` o diagrama de solução renderizava
        5 nós, e as injeções de D⇸C e D↯D′ — justamente a do conflito central — não
        apareciam em lugar nenhum (F-07 da spec 007). Aqui o dicionário tem as 7 chaves
        por construção; posição sem injeção é tupla vazia, que a interface mostra como
        pendência (RF-31) em vez de buraco.
        """
        return {chave: self.injecoes_da_aresta(chave) for chave in ChaveDaAresta}

    def matriz(self) -> dict[ChaveDaAresta, tuple[tuple[Premissa, tuple[Injecao, ...]], ...]]:
        """RF-34: a matriz aresta × premissas × injeções — projeção do MESMO dado."""
        return {
            chave: tuple(
                (premissa, self.injecoes_da_premissa(premissa.id))
                for premissa in self.premissas(chave)
            )
            for chave in ChaveDaAresta
        }

    def avisos_de_formulacao(
        self, idioma: str = "pt"
    ) -> dict[PapelDaEntidade, tuple[AvisoDeFormulacao, ...]]:
        """RF-09/RF-10: heurística pura por entidade. Aviso, nunca bloqueio (RN-06)."""
        texto_de_d = self.texto(PapelDaEntidade.D)
        return {
            papel: avaliar_formulacao(
                papel,
                self.texto(papel),
                idioma=idioma,
                texto_de_d=texto_de_d if papel is PapelDaEntidade.D_PRIME else None,
            )
            for papel in PapelDaEntidade
        }

    def validar(self, idioma: str = "pt") -> ValidacaoDaNuvem:
        sustentadas = tuple(
            chave for chave in ChaveDaAresta
            if any(p.sustenta for p in self.premissas(chave))
        )
        return ValidacaoDaNuvem(
            arestas_sustentadas=sustentadas,
            arestas_sem_premissa=tuple(c for c in ChaveDaAresta if c not in sustentadas),
            arestas_sem_injecao=tuple(
                c for c in ChaveDaAresta if not self.injecoes_da_aresta(c)
            ),
            avisos=self.avisos_de_formulacao(idioma),
            separacoes_ausentes=self._separacoes_ausentes(),
        )

    def _separacoes_ausentes(self) -> tuple[SeparacaoTRIZ, ...]:
        """RN-07: quais das 5 separações ainda não têm injeção no conflito D↯D′."""
        cobertas = {
            i.separacao for i in self.injecoes_da_aresta(ChaveDaAresta.D_D_PRIME)
            if i.separacao is not None
        }
        return tuple(s for s in SeparacaoTRIZ if s not in cobertas)

    # -- geração assistida (RF-23, RF-25) -----------------------------------------

    def aplicar_geracao(
        self, resultado: "ResultadoDeGeracao", *, em: datetime, proposta_id: str
    ) -> GeracaoAplicada:
        """Aplica um resultado JÁ validado, de uma vez, marcando a origem (RF-25).

        O agregado **não** valida o esquema: quem valida é `ResultadoDeGeracao`, antes de
        a proposta existir (RF-22). Aqui a regra é outra e é do domínio: as premissas
        **acumulam** — a geração nunca sobrescreve o que o grupo escreveu (RN-05).

        `proposta_id` é obrigatório de propósito: conteúdo de modelo só entra por proposta
        aceita, e um caminho que aplicasse sem identificar a proposta seria exatamente o
        caminho que a RN-05 fecha.
        """
        self.projeto._exigir_ativo("aplicar_geracao")
        if not (proposta_id or "").strip():
            raise MutacaoRecusada(
                "aplicar_geracao: sem proposta_id não há origem para declarar (RF-25)"
            )
        for papel, texto in resultado.entidades.items():
            self.editar_entidade(
                papel, texto, em=em, origem=ORIGEM_DE_GERACAO, proposta_id=proposta_id
            )
        if resultado.racional:
            self.editar_racional(
                resultado.racional, em=em, origem=ORIGEM_DE_GERACAO, proposta_id=proposta_id
            )
        premissas = injecoes = 0
        for chave, propostas in resultado.premissas.items():
            for premissa_proposta in propostas:
                premissa = self.registrar_premissa(
                    chave,
                    premissa_proposta.texto,
                    em=em,
                    origem=ORIGEM_DE_GERACAO,
                    proposta_id=proposta_id,
                )
                premissas += 1
                for injecao_proposta in premissa_proposta.injecoes:
                    self.registrar_injecao(
                        premissa.id,
                        injecao_proposta.texto,
                        em=em,
                        separacao=injecao_proposta.separacao,
                        origem=ORIGEM_DE_GERACAO,
                        proposta_id=proposta_id,
                    )
                    injecoes += 1
        evento = GeracaoAplicada(
            projeto_id=self.projeto.id,
            dono=self.projeto.dono,
            instante=em,
            proposta_id=proposta_id,
            entidades=len(resultado.entidades),
            premissas=premissas,
            injecoes=injecoes,
        )
        self.projeto.eventos = self.projeto.eventos + (evento,)
        return evento

    # -- internos ------------------------------------------------------------------

    def _emitir(self, classe, em: datetime, **carga) -> None:
        self.projeto.eventos = self.projeto.eventos + (
            classe(
                projeto_id=self.projeto.id,
                dono=self.projeto.dono,
                instante=em,
                **carga,
            ),
        )


# --------------------------------------------------------------------------------------
# Fábricas: criar, reidratar e derivar
# --------------------------------------------------------------------------------------


def novo_projeto_nc(
    *,
    id: UUID,
    dono: DonoDoProjeto,
    nome: str,
    em: datetime,
    descricao_do_problema: str = "",
    origem: ReferenciaDeOrigem | None = None,
) -> NuvemDeConflito:
    """RF-02: a nuvem inteira num ato atômico — 5 entidades, 7 arestas, racional vazio.

    Não existe nuvem parcial. É o acerto da linhagem (`createEmptyConflictCloudData`)
    promovido a invariante: quem cria não escolhe topologia, e por isso não pode errá-la.
    """
    projeto = Projeto(
        id=id,
        dono=dono,
        nome=nome,
        ferramenta=FERRAMENTA_NC,
        descricao_do_problema=descricao_do_problema,
        criado_em=em,
        alterado_em=em,
    )
    # A fábrica É a raiz nascendo: as 5 entidades e as 7 arestas são criadas de dentro
    # dela, e por isso o núcleo as aceita. Fora daqui não há caminho que as crie.
    with projeto.sob_a_raiz() as nucleo:
        for papel in PapelDaEntidade:
            x, y = POSICAO_CANONICA[papel]
            nucleo.adicionar_no(
                titulo=TEXTO_DE_EXEMPLO[papel],
                tipo=TIPO_DE_NO_POR_PAPEL[papel],
                posicao=PosicaoNoCanvas(x, y),
                em=em,
            )
        por_papel = {PAPEL_POR_TIPO_DE_NO[n.tipo]: n.id for n in nucleo.nos}
        for chave in ChaveDaAresta:
            origem_papel, destino_papel = PAR_DA_ARESTA[chave]
            nucleo.ligar(
                por_papel[origem_papel],
                por_papel[destino_papel],
                rotulo=chave.value,
                em=em,
            )
    # A fila de eventos do M1 (5 `NoAdicionado` + 7 `ArestaLigada`) descreve a mecânica;
    # o que a ferramenta relata é UM ato — a nuvem nasceu inteira (RF-02).
    projeto.eventos = ()
    nuvem = NuvemDeConflito(projeto=projeto, origem=origem)
    nuvem._emitir(
        NuvemCriada, em, entidades=len(PapelDaEntidade), arestas=len(ChaveDaAresta)
    )
    return nuvem


def reidratar_nuvem(
    projeto: Projeto,
    *,
    racional: str = "",
    premissas: Iterable[Premissa] = (),
    injecoes: Iterable[Injecao] = (),
    origem: ReferenciaDeOrigem | None = None,
) -> NuvemDeConflito:
    """Monta a nuvem a partir do que estava GRAVADO — sem emitir evento nenhum.

    Carregar não é mutar (a mesma regra de `reidratar_ara`): se a reidratação emitisse
    `NuvemCriada`, abrir um projeto escreveria história que não aconteceu.
    """
    nuvem = NuvemDeConflito(projeto=projeto, racional=racional, origem=origem)
    nuvem._premissas = {p.id: p for p in premissas}
    nuvem._injecoes = {i.id: i for i in injecoes}
    orfas = [
        i.id for i in nuvem._injecoes.values() if i.premissa_id not in nuvem._premissas
    ]
    if orfas:
        # RN-04 conferida na reidratação também: injeção órfã no banco é corrupção, e
        # carregá-la em silêncio esconderia o defeito em vez de mostrá-lo.
        raise InjecaoInvalida(
            "premissa_inexistente",
            f"{len(orfas)} injeção(ões) sem premissa no projeto {projeto.id}: {orfas}",
        )
    projeto.eventos = ()
    return nuvem


def derivar_nuvem_de_udes(
    ara: "ProjetoARA",
    *,
    no_ids: Sequence[UUID],
    id: UUID,
    nome: str,
    em: datetime,
) -> NuvemDeConflito:
    """INT-05 — **o encadeamento que nenhuma geração da linhagem fez**: da ARA para a NC.

    O Efeito Indesejável validado é o ponto de partida do dilema: a nuvem nasce inteira,
    com os enunciados dos UDEs na descrição do problema e a `ReferenciaDeOrigem` tipada
    apontando para o projeto de origem e para os nós exatos. As entidades continuam com
    texto de exemplo — derivar dá o **ponto de partida**, não inventa o conflito; quem
    escreve A, B, C, D e D′ é o grupo, ou a geração assistida por proposta aceita.

    Três recusas, cada uma com regra nomeada:

    - `sem_ude` — derivar sem efeito nenhum seria nuvem sem dilema;
    - `no_nao_e_ude` — o nó existe mas não está marcado; a marcação é o que diz que
      aquilo é um efeito indesejável, e não uma caixa qualquer do diagrama;
    - `ude_rejeitado` — o grupo já decidiu que aquele enunciado não se sustenta.

    **Por que `rejeitado` e não "exige `validado`"**: a INT-05 fala em "UDEs validados", e
    exigir `StatusDeValidacao.VALIDADO` tornaria a costura inalcançável antes do parecer
    humano (RN-10 da spec 005), justamente na sessão em que o dilema aparece. A regra
    entregue aqui é a maior que não trava o método: marcado e **não** rejeitado. Apertá-la
    é decisão do ciclo 008, que é quem executa a promoção (round 008).

    A ARA é **lida, nunca escrita**: derivar não emite evento nenhum do lado do M2.
    """
    from .ara import FERRAMENTA_ARA, StatusDeValidacao  # local: evita ciclo de import

    if ara.projeto.excluido_em is not None:
        raise MutacaoRecusada(
            "derivar_nuvem_de_udes: a Árvore da Realidade Atual de origem está excluída"
        )
    if not no_ids:
        raise DerivacaoInvalida(
            "sem_ude", "a derivação parte de pelo menos um Efeito Indesejável"
        )

    enunciados: list[str] = []
    for no_id in no_ids:
        no = ara.projeto.no(no_id)  # NaoEncontrado quando o nó não é deste projeto
        if not ara.e_ude(no_id):
            raise DerivacaoInvalida(
                "no_nao_e_ude",
                f"o nó {no_id} existe mas não está marcado como Efeito Indesejável",
            )
        if ara.status(no_id) is StatusDeValidacao.REJEITADO:
            raise DerivacaoInvalida(
                "ude_rejeitado",
                f"o Efeito Indesejável {no_id} está rejeitado; reabra-o antes de derivar",
            )
        enunciados.append(no.titulo)

    cabecalho = "Dilema por trás do(s) Efeito(s) Indesejável(is):"
    descricao = texto_de_dominio(
        "\n".join([cabecalho, *(f"- {e}" for e in enunciados)]),
        campo="descricao_do_problema",
        minimo=0,
        maximo=LIMITE_DESCRICAO,
    )
    origem = ReferenciaDeOrigem(
        ferramenta=FERRAMENTA_ARA, projeto_id=ara.projeto.id, nos=tuple(no_ids)
    )
    nuvem = novo_projeto_nc(
        id=id,
        dono=ara.projeto.dono,  # o inquilino vem do agregado de origem, nunca do chamador
        nome=nome,
        em=em,
        descricao_do_problema=descricao,
        origem=origem,
    )
    nuvem._emitir(
        NuvemDerivadaDeUde,
        em,
        origem_ferramenta=origem.ferramenta,
        origem_projeto_id=origem.projeto_id,
        udes=origem.nos,
    )
    return nuvem


__all__ = [
    "CHAVE_POR_PAR",
    "CLASSE_POR_CHAVE",
    "FERRAMENTA_NC",
    "LEITURA_POR_CLASSE",
    "PAPEL_POR_TIPO_DE_NO",
    "PAR_DA_ARESTA",
    "POSICAO_CANONICA",
    "TEXTO_DE_EXEMPLO",
    "TIPO_DE_NO_POR_PAPEL",
    "TRANSICOES_DE_INJECAO",
    "ChaveDaAresta",
    "ClasseDaAresta",
    "DerivacaoInvalida",
    "EstadoDaPremissa",
    "Injecao",
    "InjecaoInvalida",
    "NuvemDeConflito",
    "PapelDaEntidade",
    "Premissa",
    "PremissaInvalida",
    "ReferenciaDeOrigem",
    "ReferenciaDeSemeadura",
    "SeparacaoTRIZ",
    "StatusDeInjecao",
    "TopologiaImutavel",
    "TransicaoDeInjecaoRecusada",
    "ValidacaoDaNuvem",
    "derivar_nuvem_de_udes",
    "novo_projeto_nc",
    "reidratar_nuvem",
]
