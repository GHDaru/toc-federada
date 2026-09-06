"""M4 · E4.1 — a Árvore da Realidade Futura (ARF) sobre o núcleo do M1 (spec 008).

Siglas, uma vez neste arquivo: **ARF** — Árvore da Realidade Futura · **ARA** — Árvore da
Realidade Atual · **UDE** — Efeito Indesejável · **ED** — Efeito Desejável · **NC** —
Nuvem de Conflito · **TOC** — Teoria das Restrições · **M1** — Núcleo de Diagramas
Lógicos · **M2** — o módulo da ARA · **RF/RN** — requisito funcional / regra de negócio.

**Esta ferramenta nunca existiu na linhagem.** Nas quatro gerações do TOC-Builder a ARF
foi um botão cinza: `tocbuilderv3/components/Sidebar.tsx:55` (`view: 'ARF', disabled:
true`) e o tipo de navegação em `types.ts:249-258` — zero componentes, zero prompts, zero
linhas de domínio. É o defeito D-04 da visão, e este módulo é a correção.

**Por composição, nunca por herança** — a mesma fronteira do M2 (`ara.py`) e do M3
(`nuvem.py`): o M1 não conhece semântica da TOC (RN-04 da spec 004), então `ProjetoARF`
**contém** um `Projeto` e acrescenta o que é da ferramenta. Três coisas são da ferramenta:

1. **O papel do nó** (`injecao` | `efeito_futuro`), gravado no `tipo` do nó do M1 — enum
   extensível por decisão do próprio núcleo. Injeção é o que **ainda não existe** na
   realidade; efeito futuro é o que passa a ser verdade quando ela existir (RN-02).
2. **O espelho UDE → ED**: marcar um efeito futuro como o Efeito Desejável que converte um
   UDE **da cadeia**. Um UDE tem no máximo um ED por ARF (RN-03), e sem cadeia vinculada o
   espelho não existe — a cobertura declara "sem origem vinculada" em vez de inventar
   (RF-07).
3. **O ramo negativo**: o efeito indevido que a própria injeção traz. É ele que separa uma
   árvore de futuro séria de uma lista de desejos, e por isso a transição é estreita —
   `tratado` **exige** a injeção que corta, `aceito` **exige** justificativa e autor
   (RN-04).

A lógica das arestas é **suficiência causal**, a mesma da ARA (RN-01), e vem do pacote
compartilhado `toc_api.dominio.suficiencia` — extraído, nunca copiado (RF-03; decisão 1 do
plano do ciclo 008). O que a ARF **não** tem é a lógica de condição necessária da Árvore
de Pré-Requisitos: as duas não se misturam no mesmo projeto (RN-05), e a garantia é a
ausência da operação, não um `if` na interface.

Ramo negativo assistido está **fora deste ciclo** por decisão de round (RF-10): não há, e
não deve haver, rota de sugestão de ramo negativo. A prova é negativa e está na DoD 8.
"""
from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Iterable, Iterator, Mapping, Sequence
from uuid import UUID, uuid4

from .erros import MutacaoRecusada, NaoEncontrado
from .eventos import (
    ArfCriada,
    EfeitoEspelhouUde,
    EspelhoDesfeito,
    PapelNaArfMudou,
    RamoNegativoAceito,
    RamoNegativoMarcado,
    RamoNegativoReaberto,
    RamoNegativoTratado,
    VerificacaoDaArfGerada,
)
from .grafo import ArestaCausal, No, alcanca, sucessores
from .identidade import DonoDoProjeto
from .projeto import Projeto, registrar_raiz_de_ferramenta
from .referencia import Ponta
from .suficiencia import (
    ConectorE,
    EstadoDoExame,
    Exame,
    exame_de,
    formar_conector,
    leitura_de_conjuncao,
    leitura_de_suficiencia,
    soltar_das_conjuncoes,
)
from .valores import LIMITE_DESCRICAO, PosicaoNoCanvas, texto as texto_de_dominio

#: O tipo de projeto do M4 · E4.1 (spec 008, RF-01) — o M1 nunca precisa saber deste nome.
FERRAMENTA_ARF = "arf"

#: A ARF é a RAIZ do agregado: o grafo de um projeto `arf` só muda por dentro dela
#: (`Projeto._exigir_raiz`). Sem isto, `Projeto.ligar` criaria elo sem exame e
#: `Projeto.excluir_no` sumiria com a injeção que corta um ramo tratado, deixando o ramo
#: apontando para o vazio — a mesma classe de defeito que o M2 e o M3 fecharam.
registrar_raiz_de_ferramenta(FERRAMENTA_ARF, "ProjetoARF")

LIMITE_JUSTIFICATIVA = 2000
LIMITE_AUTOR = 200


class PapelNaARF(str, Enum):
    """RF-02. Injeção **não existe ainda**; efeito futuro é o que ela passa a causar."""

    INJECAO = "injecao"
    EFEITO_FUTURO = "efeito_futuro"


class EstadoDoRamo(str, Enum):
    """RN-04: `aberto → tratado | aceito`, e os dois voltam por ação explícita."""

    ABERTO = "aberto"
    TRATADO = "tratado"
    ACEITO = "aceito"


#: `papel → tipo de nó do M1`. É o tipo que faz o papel sobreviver ao banco sem tabela
#: nova: quem reidrata lê o `tipo` do nó e sabe qual papel é.
TIPO_DE_NO_POR_PAPEL: dict[PapelNaARF, str] = {
    PapelNaARF.INJECAO: "arf_injecao",
    PapelNaARF.EFEITO_FUTURO: "arf_efeito_futuro",
}
PAPEL_POR_TIPO_DE_NO: dict[str, PapelNaARF] = {
    tipo: papel for papel, tipo in TIPO_DE_NO_POR_PAPEL.items()
}


class PapelNaArfInvalido(MutacaoRecusada):
    """RF-02. `regra`: `papel_desconhecido` · `injecao_de_corte` · `sem_mudanca`."""

    def __init__(self, regra: str, detalhe: str = "") -> None:
        super().__init__(f"{regra}: {detalhe}" if detalhe else regra)
        self.regra = regra


class EspelhoInvalido(MutacaoRecusada):
    """RF-04/RN-03. `regra`: `sem_cadeia` · `ude_fora_da_cadeia` · `ude_ja_espelhado` ·
    `papel_incompativel` · `sem_espelho`."""

    def __init__(self, regra: str, detalhe: str = "") -> None:
        super().__init__(f"{regra}: {detalhe}" if detalhe else regra)
        self.regra = regra


class RamoNegativoInvalido(MutacaoRecusada):
    """RN-04. `regra`: `ramo_ja_marcado` · `corte_nao_e_injecao` ·
    `justificativa_obrigatoria` · `autor_obrigatorio` · `ja_aberto`."""

    def __init__(self, regra: str, detalhe: str = "") -> None:
        super().__init__(f"{regra}: {detalhe}" if detalhe else regra)
        self.regra = regra


# --------------------------------------------------------------------------------------
# Entidades internas e objetos de valor
# --------------------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class EspelhoDeUde:
    """A marca de ED: qual UDE **este** efeito futuro converte (RN-03).

    Objeto de valor, não entidade: dois espelhos do mesmo UDE no mesmo efeito são o mesmo
    espelho. `projeto_de_origem_id` é o projeto da ARA de onde o UDE veio, quando a cadeia
    o informa — é o que permite à ficha dizer "origem: ARA <nome>" sem perguntar a
    ninguém.
    """

    ude_id: UUID
    projeto_de_origem_id: UUID | None = None


@dataclass(slots=True)
class RamoNegativo:
    """O efeito indevido que a injeção traz — entidade do agregado ARF (RN-04)."""

    id: UUID
    raiz_id: UUID
    estado: EstadoDoRamo = EstadoDoRamo.ABERTO
    injecao_de_corte_id: UUID | None = None
    justificativa: str = ""
    autor: str = ""

    def __post_init__(self) -> None:
        self.estado = EstadoDoRamo(self.estado)


@dataclass(frozen=True, slots=True)
class CoberturaDeUde:
    """Uma linha do resumo de cobertura (RF-05): o UDE, o ED que o espelha, e se há caminho."""

    ude_id: UUID
    espelhado_por: UUID | None = None
    alcancado: bool = False


@dataclass(frozen=True, slots=True)
class VerificacaoDaARF:
    """RF-11: função pura sobre o grafo. Não muta nada, não fala com rede, não chama modelo.

    `pronta` não é veto: é leitura. A ARF continua editável com pendência — o que a
    verificação faz é impedir que alguém a declare pronta sem olhar (RF-11, US-05).
    """

    eds_sem_caminho: tuple[UUID, ...]
    injecoes_sem_efeito: tuple[UUID, ...]
    ramos_abertos: tuple[UUID, ...]
    cobertura: tuple[CoberturaDeUde, ...]
    sem_origem_vinculada: bool

    @property
    def pronta(self) -> bool:
        return not (
            self.eds_sem_caminho
            or self.injecoes_sem_efeito
            or self.ramos_abertos
            or any(not c.alcancado for c in self.cobertura)
        )

    def resumo(self) -> dict[str, int | bool]:
        return {
            "eds_sem_caminho": len(self.eds_sem_caminho),
            "injecoes_sem_efeito": len(self.injecoes_sem_efeito),
            "ramos_negativos_abertos": len(self.ramos_abertos),
            "udes_referenciados": len(self.cobertura),
            "udes_espelhados": sum(1 for c in self.cobertura if c.espelhado_por),
            "udes_cobertos": sum(1 for c in self.cobertura if c.alcancado),
            "sem_origem_vinculada": self.sem_origem_vinculada,
            "pronta": self.pronta,
        }


# --------------------------------------------------------------------------------------
# O agregado
# --------------------------------------------------------------------------------------


@dataclass(slots=True)
class ProjetoARF:
    """A ARF: um `Projeto` do M1 mais a semântica da ferramenta."""

    projeto: Projeto
    #: De onde esta árvore veio (a injeção escolhida da NC), quando veio de alguma coisa.
    origem: Ponta | None = None
    #: Os UDEs que a cadeia da análise disponibiliza para espelho (RN-03). Vazio = ARF do
    #: zero: o espelho não existe, e a cobertura declara "sem origem vinculada" (RF-07).
    udes_da_cadeia: tuple[UUID, ...] = ()
    _espelhos: dict[UUID, EspelhoDeUde] = field(default_factory=dict)
    _ramos: dict[UUID, RamoNegativo] = field(default_factory=dict)
    _exames: dict[UUID, Exame] = field(default_factory=dict)
    _conectores: dict[UUID, ConectorE] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.projeto.ferramenta != FERRAMENTA_ARF:
            raise MutacaoRecusada(
                f"ProjetoARF exige ferramenta {FERRAMENTA_ARF!r}, "
                f"veio {self.projeto.ferramenta!r}"
            )
        self.udes_da_cadeia = tuple(self.udes_da_cadeia)

    # -- a única porta para o `Projeto` contido ----------------------------------

    @contextmanager
    def _nucleo(self) -> Iterator[Projeto]:
        """Abre o núcleo do M1 PARA A RAIZ. Toda delegação da ARF passa por aqui."""
        with self.projeto.sob_a_raiz() as nucleo:
            yield nucleo

    # -- consultas ---------------------------------------------------------------

    @property
    def nos(self) -> tuple[No, ...]:
        return self.projeto.nos

    @property
    def arestas(self) -> tuple[ArestaCausal, ...]:
        return self.projeto.arestas

    @property
    def eventos(self):
        return self.projeto.eventos

    @property
    def conectores(self) -> tuple[ConectorE, ...]:
        return tuple(self._conectores.values())

    def drenar_eventos(self):
        return self.projeto.drenar_eventos()

    def papel_do_no(self, no_id: UUID) -> PapelNaARF:
        no = self.projeto.no(no_id)
        try:
            return PAPEL_POR_TIPO_DE_NO[no.tipo]
        except KeyError as ausente:  # pragma: no cover - a raiz impede tipo fora do mapa
            raise PapelNaArfInvalido(
                "papel_desconhecido", f"o nó {no_id} tem tipo {no.tipo!r}, fora da ARF"
            ) from ausente

    def nos_do_papel(self, papel: PapelNaARF) -> tuple[No, ...]:
        alvo = TIPO_DE_NO_POR_PAPEL[PapelNaARF(papel)]
        return tuple(n for n in self.projeto.nos if n.tipo == alvo)

    @property
    def injecoes(self) -> tuple[No, ...]:
        return self.nos_do_papel(PapelNaARF.INJECAO)

    @property
    def efeitos_futuros(self) -> tuple[No, ...]:
        return self.nos_do_papel(PapelNaARF.EFEITO_FUTURO)

    def e_efeito_desejavel(self, no_id: UUID) -> bool:
        return no_id in self._espelhos

    def espelho(self, no_id: UUID) -> EspelhoDeUde:
        try:
            return self._espelhos[no_id]
        except KeyError as ausente:
            raise EspelhoInvalido("sem_espelho", f"o nó {no_id} não espelha UDE algum") from ausente

    def espelhos(self) -> tuple[tuple[UUID, EspelhoDeUde], ...]:
        return tuple(sorted(self._espelhos.items(), key=lambda par: str(par[0])))

    def ramo(self, ramo_id: UUID) -> RamoNegativo:
        try:
            return self._ramos[ramo_id]
        except KeyError as ausente:
            raise NaoEncontrado(f"ramo_negativo:{ramo_id}") from ausente

    def ramos(self, estado: EstadoDoRamo | None = None) -> tuple[RamoNegativo, ...]:
        todos = sorted(self._ramos.values(), key=lambda r: str(r.id))
        if estado is None:
            return tuple(todos)
        alvo = EstadoDoRamo(estado)
        return tuple(r for r in todos if r.estado is alvo)

    # -- grafo, pela raiz --------------------------------------------------------

    def adicionar_injecao(self, *, titulo: str, em: datetime, **kw) -> No:
        return self._adicionar(PapelNaARF.INJECAO, titulo=titulo, em=em, **kw)

    def adicionar_efeito_futuro(self, *, titulo: str, em: datetime, **kw) -> No:
        return self._adicionar(PapelNaARF.EFEITO_FUTURO, titulo=titulo, em=em, **kw)

    def _adicionar(
        self,
        papel: PapelNaARF,
        *,
        titulo: str,
        em: datetime,
        descricao: str = "",
        posicao: PosicaoNoCanvas | None = None,
        no_id: UUID | None = None,
    ) -> No:
        with self._nucleo() as nucleo:
            return nucleo.adicionar_no(
                titulo=titulo,
                descricao=descricao,
                tipo=TIPO_DE_NO_POR_PAPEL[PapelNaARF(papel)],
                posicao=posicao,
                no_id=no_id,
                em=em,
            )

    def mudar_papel(self, no_id: UUID, papel: PapelNaARF, *, em: datetime) -> No:
        """RF-02: o papel muda enquanto não houver vínculo que o proíba.

        O vínculo que proíbe é nomeado: uma injeção que **corta um ramo tratado** não vira
        efeito futuro, porque o ramo passaria a declarar-se tratado por algo que já não é
        uma injeção — a referência ficaria de pé e sem sentido, que é pior do que órfã.
        """
        papel = PapelNaARF(papel)
        atual = self.papel_do_no(no_id)
        if papel is atual:
            raise PapelNaArfInvalido("sem_mudanca", f"o nó já é {atual.value}")
        if atual is PapelNaARF.INJECAO and self._ramos_cortados_por(no_id):
            raise PapelNaArfInvalido(
                "injecao_de_corte",
                f"a injeção {no_id} trata ramo(s) negativo(s); reabra-os antes de mudar o papel",
            )
        alvo = self.projeto.no(no_id)
        alvo.tipo = TIPO_DE_NO_POR_PAPEL[papel]
        if papel is PapelNaARF.INJECAO:
            # Injeção não espelha UDE (RF-04): mudar o papel leva o espelho junto, em vez
            # de deixar um Efeito Desejável que não é mais efeito.
            self._espelhos.pop(no_id, None)
        self.projeto._avancar(em)
        self._emitir(PapelNaArfMudou, em, no_id=no_id, de=atual.value, para=papel.value)
        return alvo

    def ligar(self, origem_id: UUID, destino_id: UUID, *, em: datetime, **kw) -> ArestaCausal:
        """Aresta de suficiência: "Se origem, então destino" — e o exame nasce com ela."""
        with self._nucleo() as nucleo:
            aresta = nucleo.ligar(origem_id, destino_id, em=em, **kw)
        self._exames[aresta.id] = Exame()
        return aresta

    def editar_no(self, no_id: UUID, *, em: datetime, **kw) -> No:
        with self._nucleo() as nucleo:
            return nucleo.editar_no(no_id, em=em, **kw)

    def mover_no(self, no_id: UUID, posicao: PosicaoNoCanvas, *, em: datetime) -> No:
        with self._nucleo() as nucleo:
            return nucleo.mover_no(no_id, posicao, em=em)

    def recolher_no(self, no_id: UUID, recolhido: bool, *, em: datetime) -> No:
        with self._nucleo() as nucleo:
            return nucleo.recolher_no(no_id, recolhido, em=em)

    def editar_aresta(self, aresta_id: UUID, rotulo: str, *, em: datetime) -> ArestaCausal:
        with self._nucleo() as nucleo:
            return nucleo.editar_aresta(aresta_id, rotulo, em=em)

    def excluir_aresta(self, aresta_id: UUID, *, em: datetime) -> None:
        with self._nucleo() as nucleo:
            nucleo.excluir_aresta(aresta_id, em=em)
        self._exames.pop(aresta_id, None)
        soltar_das_conjuncoes(self._conectores, aresta_id)

    def excluir_no(self, no_id: UUID, *, em: datetime) -> list[UUID]:
        """Exclui o nó e **não deixa referência órfã** — nem espelho, nem ramo, nem corte.

        Três consequências, cada uma nascida de um teste: o espelho do nó some com ele; o
        ramo cuja raiz é o nó some com ele; e o ramo que era tratado **por** este nó
        **reabre**, em vez de continuar dizendo-se tratado por uma injeção que não existe.
        """
        self.papel_do_no(no_id)  # NaoEncontrado quando o nó não é deste projeto
        with self._nucleo() as nucleo:
            removidas = nucleo.excluir_no(no_id, em=em)
        for aresta_id in removidas:
            self._exames.pop(aresta_id, None)
            soltar_das_conjuncoes(self._conectores, aresta_id)
        self._espelhos.pop(no_id, None)
        for ramo in list(self._ramos.values()):
            if ramo.raiz_id == no_id:
                self._ramos.pop(ramo.id)
        for ramo in self._ramos_cortados_por(no_id):
            self._reabrir(ramo, em=em, automatico=True)
        return removidas

    # -- exame de suficiência e conector E (pacote compartilhado, RF-03) ---------

    def exame(self, aresta_id: UUID) -> Exame:
        self.projeto.aresta(aresta_id)
        return self._exames.get(aresta_id, Exame())

    def examinar_elo(
        self, aresta_id: UUID, estado: EstadoDoExame, *, em: datetime, reserva: str = ""
    ) -> Exame:
        self.projeto.aresta(aresta_id)
        novo = exame_de(estado, reserva)
        self._exames[aresta_id] = novo
        self.projeto._avancar(em)
        return novo

    def leitura_do_elo(self, aresta_id: UUID) -> str:
        """RF-03: montada dos textos ATUAIS dos nós — nunca de cópia congelada."""
        aresta = self.projeto.aresta(aresta_id)
        return leitura_de_suficiencia(
            self.projeto.no(aresta.origem_id).titulo,
            self.projeto.no(aresta.destino_id).titulo,
        )

    def formar_conector_e(
        self, arestas: Sequence[UUID], *, em: datetime, conector_id: UUID | None = None
    ) -> ConectorE:
        conector = formar_conector(
            self._conectores, arestas, aresta_de=self.projeto.aresta, conector_id=conector_id
        )
        self._conectores[conector.id] = conector
        self.projeto._avancar(em)
        return conector

    def desfazer_conector_e(self, conector_id: UUID, *, em: datetime) -> None:
        if conector_id not in self._conectores:
            raise NaoEncontrado(f"conector:{conector_id}")
        self._conectores.pop(conector_id)
        self.projeto._avancar(em)

    def leitura_do_conector(self, conector_id: UUID) -> str:
        try:
            conector = self._conectores[conector_id]
        except KeyError as ausente:
            raise NaoEncontrado(f"conector:{conector_id}") from ausente
        causas = [
            self.projeto.no(self.projeto.aresta(a).origem_id).titulo for a in conector.arestas
        ]
        return leitura_de_conjuncao(causas, self.projeto.no(conector.destino_id).titulo)

    # -- espelho UDE → ED (RF-04, RF-05, RF-07, RN-03) ---------------------------

    def espelhar_ude(
        self,
        no_id: UUID,
        ude_id: UUID,
        *,
        em: datetime,
        projeto_de_origem_id: UUID | None = None,
    ) -> EspelhoDeUde:
        self.projeto._exigir_ativo("espelhar_ude")
        if self.papel_do_no(no_id) is not PapelNaARF.EFEITO_FUTURO:
            raise EspelhoInvalido(
                "papel_incompativel",
                "quem espelha um Efeito Indesejável é o efeito futuro, nunca a injeção",
            )
        if not self.udes_da_cadeia:
            raise EspelhoInvalido(
                "sem_cadeia",
                "esta ARF não tem cadeia vinculada: não há Efeito Indesejável referenciável "
                "(RF-07); semeie-a a partir de uma injeção escolhida para espelhar",
            )
        if ude_id not in self.udes_da_cadeia:
            raise EspelhoInvalido(
                "ude_fora_da_cadeia",
                f"o Efeito Indesejável {ude_id} não é referenciado pela cadeia desta ARF",
            )
        ja = {e.ude_id: alvo for alvo, e in self._espelhos.items()}
        if ude_id in ja and ja[ude_id] != no_id:
            raise EspelhoInvalido(
                "ude_ja_espelhado",
                f"o Efeito Indesejável {ude_id} já é espelhado pelo efeito {ja[ude_id]} "
                "nesta ARF (RN-03: no máximo um Efeito Desejável por ARF)",
            )
        espelho = EspelhoDeUde(ude_id=ude_id, projeto_de_origem_id=projeto_de_origem_id)
        self._espelhos[no_id] = espelho
        self.projeto._avancar(em)
        self._emitir(EfeitoEspelhouUde, em, no_id=no_id, ude_id=ude_id)
        return espelho

    def desfazer_espelho(self, no_id: UUID, *, em: datetime) -> None:
        espelho = self.espelho(no_id)
        self._espelhos.pop(no_id)
        self.projeto._avancar(em)
        self._emitir(EspelhoDesfeito, em, no_id=no_id, ude_id=espelho.ude_id)

    # -- ramos negativos (RF-08, RF-09, RN-04) -----------------------------------

    def marcar_ramo_negativo(
        self, no_id: UUID, *, em: datetime, ramo_id: UUID | None = None
    ) -> RamoNegativo:
        self.projeto._exigir_ativo("marcar_ramo_negativo")
        self.papel_do_no(no_id)  # NaoEncontrado quando o nó não é deste projeto
        if any(r.raiz_id == no_id for r in self._ramos.values()):
            raise RamoNegativoInvalido(
                "ramo_ja_marcado", f"o nó {no_id} já é raiz de um ramo negativo"
            )
        ramo = RamoNegativo(id=ramo_id or uuid4(), raiz_id=no_id)
        self._ramos[ramo.id] = ramo
        self.projeto._avancar(em)
        self._emitir(RamoNegativoMarcado, em, ramo_id=ramo.id, raiz_id=no_id)
        return ramo

    def tratar_ramo(
        self, ramo_id: UUID, *, injecao_id: UUID, em: datetime
    ) -> RamoNegativo:
        """RN-04: `tratado` **somente** com a injeção que corta o ramo, e ela é da ARF."""
        self.projeto._exigir_ativo("tratar_ramo")
        ramo = self.ramo(ramo_id)
        if self.papel_do_no(injecao_id) is not PapelNaARF.INJECAO:
            raise RamoNegativoInvalido(
                "corte_nao_e_injecao",
                f"o nó {injecao_id} não é uma injeção; um ramo negativo é cortado por "
                "injeção adicional, nunca por um efeito",
            )
        ramo.estado = EstadoDoRamo.TRATADO
        ramo.injecao_de_corte_id = injecao_id
        ramo.justificativa = ""
        ramo.autor = ""
        self.projeto._avancar(em)
        self._emitir(
            RamoNegativoTratado, em, ramo_id=ramo.id, injecao_de_corte_id=injecao_id
        )
        return ramo

    def aceitar_ramo(
        self, ramo_id: UUID, *, justificativa: str, autor: str, em: datetime
    ) -> RamoNegativo:
        """RN-04: `aceito` **somente** com justificativa — e o autor fica no ramo."""
        self.projeto._exigir_ativo("aceitar_ramo")
        ramo = self.ramo(ramo_id)
        motivo = (justificativa or "").strip()
        quem = (autor or "").strip()
        if not motivo:
            raise RamoNegativoInvalido(
                "justificativa_obrigatoria",
                "aceitar um efeito colateral exige dizer por que ele é aceitável (RN-04)",
            )
        if not quem:
            raise RamoNegativoInvalido(
                "autor_obrigatorio", "aceitar um ramo negativo é decisão de alguém"
            )
        ramo.estado = EstadoDoRamo.ACEITO
        ramo.injecao_de_corte_id = None
        ramo.justificativa = texto_de_dominio(
            motivo, campo="ramo.justificativa", minimo=1, maximo=LIMITE_JUSTIFICATIVA
        )
        ramo.autor = texto_de_dominio(quem, campo="ramo.autor", minimo=1, maximo=LIMITE_AUTOR)
        self.projeto._avancar(em)
        self._emitir(
            RamoNegativoAceito, em, ramo_id=ramo.id, autor=ramo.autor, justificativa=ramo.justificativa
        )
        return ramo

    def reabrir_ramo(self, ramo_id: UUID, *, em: datetime) -> RamoNegativo:
        ramo = self.ramo(ramo_id)
        if ramo.estado is EstadoDoRamo.ABERTO:
            raise RamoNegativoInvalido("ja_aberto", f"o ramo {ramo_id} já está aberto")
        return self._reabrir(ramo, em=em, automatico=False)

    def _reabrir(self, ramo: RamoNegativo, *, em: datetime, automatico: bool) -> RamoNegativo:
        anterior = ramo.estado
        ramo.estado = EstadoDoRamo.ABERTO
        ramo.injecao_de_corte_id = None
        ramo.justificativa = ""
        ramo.autor = ""
        self.projeto._avancar(em)
        self._emitir(
            RamoNegativoReaberto,
            em,
            ramo_id=ramo.id,
            de=anterior.value,
            automatico=automatico,
        )
        return ramo

    def _ramos_cortados_por(self, no_id: UUID) -> tuple[RamoNegativo, ...]:
        return tuple(
            r for r in self._ramos.values() if r.injecao_de_corte_id == no_id
        )

    # -- verificação estrutural (RF-11..RF-13) -----------------------------------

    def verificar(self) -> VerificacaoDaARF:
        """Função pura: não muta, não emite, não fala com rede nem com modelo (RNF-01)."""
        saida = sucessores(self.projeto.arestas)
        alcancados: set[UUID] = set()
        for injecao in self.injecoes:
            alcancados |= alcanca(injecao.id, saida)

        eds = [no_id for no_id, _ in self.espelhos()]
        sem_caminho = tuple(no_id for no_id in eds if no_id not in alcancados)
        sem_efeito = tuple(
            n.id for n in self.injecoes if not saida.get(n.id)
        )
        abertos = tuple(r.id for r in self.ramos(EstadoDoRamo.ABERTO))

        por_ude = {espelho.ude_id: no_id for no_id, espelho in self._espelhos.items()}
        cobertura = tuple(
            CoberturaDeUde(
                ude_id=ude_id,
                espelhado_por=por_ude.get(ude_id),
                alcancado=por_ude.get(ude_id) in alcancados if ude_id in por_ude else False,
            )
            for ude_id in self.udes_da_cadeia
        )
        return VerificacaoDaARF(
            eds_sem_caminho=sem_caminho,
            injecoes_sem_efeito=sem_efeito,
            ramos_abertos=abertos,
            cobertura=cobertura,
            sem_origem_vinculada=not self.udes_da_cadeia,
        )

    def gerar_verificacao(self, *, em: datetime) -> VerificacaoDaARF:
        """RF-13: a mesma função pura, com o evento do resumo quantitativo por cima."""
        verificacao = self.verificar()
        self._emitir(VerificacaoDaArfGerada, em, resumo=verificacao.resumo())
        return verificacao

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
# Fábricas: criar e reidratar
# --------------------------------------------------------------------------------------


def novo_projeto_arf(
    *,
    id: UUID,
    dono: DonoDoProjeto,
    nome: str,
    em: datetime,
    descricao_do_problema: str = "",
    origem: Ponta | None = None,
    udes_da_cadeia: Sequence[UUID] = (),
) -> ProjetoARF:
    """Cria o `Projeto` do M1 com a ferramenta certa e o embrulha na raiz da ARF."""
    projeto = Projeto(
        id=id,
        dono=dono,
        nome=nome,
        ferramenta=FERRAMENTA_ARF,
        descricao_do_problema=texto_de_dominio(
            descricao_do_problema,
            campo="descricao_do_problema",
            minimo=0,
            maximo=LIMITE_DESCRICAO,
        ),
        criado_em=em,
        alterado_em=em,
    )
    arf = ProjetoARF(
        projeto=projeto, origem=origem, udes_da_cadeia=tuple(udes_da_cadeia)
    )
    arf._emitir(ArfCriada, em, udes_da_cadeia=len(arf.udes_da_cadeia))
    return arf


def reidratar_arf(
    projeto: Projeto,
    *,
    espelhos: Mapping[UUID, EspelhoDeUde] | None = None,
    ramos: Iterable[RamoNegativo] = (),
    exames: Mapping[UUID, Exame] | None = None,
    conectores: Iterable[ConectorE] = (),
    origem: Ponta | None = None,
    udes_da_cadeia: Sequence[UUID] = (),
) -> ProjetoARF:
    """Monta a ARF a partir do que estava GRAVADO — sem emitir evento nenhum.

    Carregar não é mutar (a mesma regra de `reidratar_ara` e `reidratar_nuvem`): se a
    reidratação emitisse `ArfCriada`, abrir um projeto escreveria história que não
    aconteceu.
    """
    arf = ProjetoARF(projeto=projeto, origem=origem, udes_da_cadeia=tuple(udes_da_cadeia))
    arf._espelhos = dict(espelhos or {})
    arf._ramos = {r.id: r for r in ramos}
    arf._exames = dict(exames or {})
    arf._conectores = {c.id: c for c in conectores}
    projeto.eventos = ()
    return arf


__all__ = [
    "FERRAMENTA_ARF",
    "PAPEL_POR_TIPO_DE_NO",
    "TIPO_DE_NO_POR_PAPEL",
    "CoberturaDeUde",
    "EspelhoDeUde",
    "EspelhoInvalido",
    "EstadoDoRamo",
    "PapelNaARF",
    "PapelNaArfInvalido",
    "ProjetoARF",
    "RamoNegativo",
    "RamoNegativoInvalido",
    "VerificacaoDaARF",
    "novo_projeto_arf",
    "reidratar_arf",
]
