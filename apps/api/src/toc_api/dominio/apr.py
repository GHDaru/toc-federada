"""M4 · E4.2 — a Árvore de Pré-Requisitos (APR) sobre o núcleo do M1 (spec 008).

Siglas, uma vez neste arquivo: **APR** — Árvore de Pré-Requisitos · **OI** — Objetivo
Intermediário · **ARA** — Árvore da Realidade Atual · **ARF** — Árvore da Realidade
Futura · **TOC** — Teoria das Restrições · **M1** — Núcleo de Diagramas Lógicos ·
**RF/RN/RNF** — requisito funcional / regra de negócio / requisito não funcional.

**A distinção que manda neste módulo é lógica, não visual.** A ARA e a ARF encadeiam por
**suficiência** — "Se A, então B". A APR encadeia por **condição necessária** — "A precisa
existir antes de B". A fonte técnica é a skill local `toc-prt`
(`references/prt-methodology.md`): *"Lógica usada: Condição Necessária. Diferente das
árvores de Realidade Atual e Futura, que usam lógica de causa suficiente."*

A RN-05 diz que as duas lógicas **não se misturam no mesmo projeto**, e a garantia aqui é
estrutural: este módulo **não importa** o pacote de suficiência, e a APR **não tem**
`examinar_elo`, `exame`, `leitura_do_elo` nem `formar_conector_e`. A ferramenta que não
oferece a operação é a ferramenta em que ninguém a usa por engano — a mesma disciplina
com que a Nuvem de Conflito recusa criar entidade (RF-03 da spec 007).

Os três elementos, com a definição da referência:

- **Objetivo** — a condição final, verbalizada no presente. Exatamente um, criado na
  origem e indestrutível enquanto o projeto viver; texto editável, papel não (RF-14).
- **Obstáculo** — "an entity that exists in the current reality of the system and because
  of its existence, the objective cannot be achieved" (Scheinkopf, cap. 10). Não é tarefa
  e não é previsão — e é isso que a verbalização avaliada avisa (RF-20).
- **Objetivo intermediário** — a condição que, uma vez estabelecida, supera o obstáculo ou
  o torna irrelevante. Estado conquistado, nunca atividade.

O **teste de validade** do par — "Se <OI>, então <obstáculo> não impede mais <objetivo>" —
é **julgamento** registrado como parecer com autor e data (RN-07), acumulável e nunca
sobrescrito. Ele não é campo calculado, e transformá-lo num seria trocar o método por uma
caixa de seleção.
"""
from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Iterable, Iterator, Sequence
from uuid import UUID, uuid4

from .erros import DadoInvalido, MutacaoRecusada, NaoEncontrado
from .eventos import (
    AprCriada,
    ElipseDesfeita,
    ElipseFormada,
    ObstaculoPareado,
    PapelNaAprMudou,
    ParDesfeito,
    SequenciamentoGerado,
    TesteDeValidadeJulgado,
)
from .grafo import ArestaCausal, No, ciclos as ciclos_do_grafo, sucessores
from .identidade import DonoDoProjeto
from .projeto import Projeto, registrar_raiz_de_ferramenta
from .referencia import Ponta
from .valores import LIMITE_DESCRICAO, PosicaoNoCanvas, texto as texto_de_dominio
from .verbalizacao import (
    PapelVerbalizado,
    VerbalizacaoAvaliada,
    avaliar_verbalizacao,
)

#: O tipo de projeto do M4 · E4.2 (spec 008, RF-14).
FERRAMENTA_APR = "apr"

#: A APR é a RAIZ do agregado: o grafo de um projeto `apr` só muda por dentro dela
#: (`Projeto._exigir_raiz`). Sem isto, `Projeto.excluir_no` sumiria com o objetivo — que a
#: RF-14 declara indestrutível — pela rota genérica do M1.
registrar_raiz_de_ferramenta(FERRAMENTA_APR, "ProjetoAPR")

LIMITE_JUSTIFICATIVA = 2000
LIMITE_AUTOR = 200


class PapelNaAPR(str, Enum):
    """RF-15. O objetivo é único; obstáculo é condição de hoje; OI é estado conquistado."""

    OBJETIVO = "objetivo"
    OBSTACULO = "obstaculo"
    OBJETIVO_INTERMEDIARIO = "objetivo_intermediario"


TIPO_DE_NO_POR_PAPEL: dict[PapelNaAPR, str] = {
    PapelNaAPR.OBJETIVO: "apr_objetivo",
    PapelNaAPR.OBSTACULO: "apr_obstaculo",
    PapelNaAPR.OBJETIVO_INTERMEDIARIO: "apr_objetivo_intermediario",
}
PAPEL_POR_TIPO_DE_NO: dict[str, PapelNaAPR] = {
    tipo: papel for papel, tipo in TIPO_DE_NO_POR_PAPEL.items()
}

#: Quais papéis a heurística de verbalização avalia. O objetivo fica de fora de propósito:
#: ele é a condição final ambiciosa, e as armadilhas catalogadas pela referência são as do
#: obstáculo e do OI.
PAPEL_VERBALIZADO_POR_PAPEL: dict[PapelNaAPR, PapelVerbalizado] = {
    PapelNaAPR.OBSTACULO: PapelVerbalizado.OBSTACULO,
    PapelNaAPR.OBJETIVO_INTERMEDIARIO: PapelVerbalizado.OBJETIVO_INTERMEDIARIO,
}


class PapelNaAprInvalido(MutacaoRecusada):
    """`regra`: `objetivo_imutavel` · `objetivo_indestrutivel` · `papel_desconhecido` ·
    `dependencia_entre_objetivos` · `sem_mudanca` · `objetivo_unico`."""

    def __init__(self, regra: str, detalhe: str = "") -> None:
        super().__init__(f"{regra}: {detalhe}" if detalhe else regra)
        self.regra = regra


class ParInvalido(MutacaoRecusada):
    """RF-17/RN-07. `regra`: `papel_incompativel` · `obstaculo_ja_pareado`."""

    def __init__(self, regra: str, detalhe: str = "") -> None:
        super().__init__(f"{regra}: {detalhe}" if detalhe else regra)
        self.regra = regra


class ElipseInvalida(MutacaoRecusada):
    """RF-19/RN-06. `regra`: `minimo_duas_dependencias` · `destino_unico` ·
    `dependencia_ja_agrupada`."""

    def __init__(self, regra: str, detalhe: str = "") -> None:
        super().__init__(f"{regra}: {detalhe}" if detalhe else regra)
        self.regra = regra


# --------------------------------------------------------------------------------------
# Entidades internas e objetos de valor
# --------------------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class JulgamentoDeValidade:
    """RN-07: o parecer sobre o teste IO-Obstáculo. Acumula, nunca sobrescreve."""

    autor: str
    valido: bool
    justificativa: str
    instante: datetime

    def __post_init__(self) -> None:
        if not (self.autor or "").strip():
            raise DadoInvalido("julgamento sem autor")
        if not (self.justificativa or "").strip():
            raise DadoInvalido("julgamento sem justificativa")


@dataclass(slots=True)
class ParObstaculoOI:
    """O obstáculo e o OI que o supera — com o histórico de julgamento (RF-18)."""

    id: UUID
    obstaculo_id: UUID
    objetivo_intermediario_id: UUID
    julgamentos: tuple[JulgamentoDeValidade, ...] = ()

    def __post_init__(self) -> None:
        self.julgamentos = tuple(self.julgamentos)

    @property
    def ultimo_julgamento(self) -> JulgamentoDeValidade | None:
        return self.julgamentos[-1] if self.julgamentos else None


@dataclass(frozen=True, slots=True)
class ElipseDeSimultaneidade:
    """RF-19: ≥ 2 dependências com o MESMO destino, lidas em conjunção de necessidade.

    É a contraparte, na lógica de necessidade, do conector E da suficiência — e por isso
    ela **não** é o `ConectorE` do pacote compartilhado: mesma notação visual, lógica
    diferente. Reusar a classe faria as duas lógicas se misturarem justamente onde a
    RN-05 diz que não podem.
    """

    id: UUID
    destino_id: UUID
    dependencias: tuple[UUID, ...]


@dataclass(frozen=True, slots=True)
class LinhaDoResumo:
    """RF-25: uma linha da tabela que vai à reunião — obstáculo, OI, de quem depende."""

    camada: int | None
    objetivo_intermediario: str | None
    objetivo_intermediario_id: UUID | None
    obstaculo: str | None
    obstaculo_id: UUID | None
    depende_de: tuple[str, ...] = ()
    julgamento: str = ""


@dataclass(frozen=True, slots=True)
class Sequenciamento:
    """RF-23: função pura — camadas, ramos paralelos, elipses e o ciclo que bloqueia."""

    camadas: tuple[tuple[UUID, ...], ...]
    ramos_paralelos: tuple[tuple[UUID, ...], ...]
    elipses: tuple[UUID, ...]
    ciclos: tuple[tuple[UUID, ...], ...]
    obstaculos_sem_oi: tuple[UUID, ...]
    objetivos_sem_obstaculo: tuple[UUID, ...]

    @property
    def bloqueado(self) -> bool:
        """RN-06: dependência circular é pendência **bloqueante** — diferente da ARA."""
        return bool(self.ciclos)

    @property
    def completo(self) -> bool:
        """RN-09: "o sequenciamento só se declara completo com pareamento total"."""
        return not (self.bloqueado or self.obstaculos_sem_oi or self.objetivos_sem_obstaculo)

    def camada_de(self, no_id: UUID) -> int | None:
        for indice, camada in enumerate(self.camadas):
            if no_id in camada:
                return indice
        return None

    def resumo(self) -> dict[str, int | bool]:
        return {
            "camadas": len(self.camadas),
            "objetivos_intermediarios": sum(len(c) for c in self.camadas)
            or len({n for ciclo in self.ciclos for n in ciclo}),
            "ramos_paralelos": len(self.ramos_paralelos),
            "elipses": len(self.elipses),
            "ciclos": len(self.ciclos),
            "obstaculos_sem_oi": len(self.obstaculos_sem_oi),
            "objetivos_sem_obstaculo": len(self.objetivos_sem_obstaculo),
            "bloqueado": self.bloqueado,
            "completo": self.completo,
        }


# --------------------------------------------------------------------------------------
# O agregado
# --------------------------------------------------------------------------------------


@dataclass(slots=True)
class ProjetoAPR:
    """A APR: um `Projeto` do M1 mais a semântica da ferramenta."""

    projeto: Projeto
    origem: Ponta | None = None
    _pares: dict[UUID, ParObstaculoOI] = field(default_factory=dict)
    _elipses: dict[UUID, ElipseDeSimultaneidade] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.projeto.ferramenta != FERRAMENTA_APR:
            raise MutacaoRecusada(
                f"ProjetoAPR exige ferramenta {FERRAMENTA_APR!r}, "
                f"veio {self.projeto.ferramenta!r}"
            )

    # -- a única porta para o `Projeto` contido ----------------------------------

    @contextmanager
    def _nucleo(self) -> Iterator[Projeto]:
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

    def drenar_eventos(self):
        return self.projeto.drenar_eventos()

    def papel_do_no(self, no_id: UUID) -> PapelNaAPR:
        no = self.projeto.no(no_id)
        try:
            return PAPEL_POR_TIPO_DE_NO[no.tipo]
        except KeyError as ausente:  # pragma: no cover - a raiz impede tipo fora do mapa
            raise PapelNaAprInvalido(
                "papel_desconhecido", f"o nó {no_id} tem tipo {no.tipo!r}, fora da APR"
            ) from ausente

    def nos_do_papel(self, papel: PapelNaAPR) -> tuple[No, ...]:
        alvo = TIPO_DE_NO_POR_PAPEL[PapelNaAPR(papel)]
        return tuple(n for n in self.projeto.nos if n.tipo == alvo)

    @property
    def objetivo(self) -> No:
        alvos = self.nos_do_papel(PapelNaAPR.OBJETIVO)
        if not alvos:  # pragma: no cover - a fábrica garante o objetivo
            raise PapelNaAprInvalido("objetivo_unico", "a APR nasce com um objetivo")
        return alvos[0]

    @property
    def obstaculos(self) -> tuple[No, ...]:
        return self.nos_do_papel(PapelNaAPR.OBSTACULO)

    @property
    def objetivos_intermediarios(self) -> tuple[No, ...]:
        return self.nos_do_papel(PapelNaAPR.OBJETIVO_INTERMEDIARIO)

    def par(self, par_id: UUID) -> ParObstaculoOI:
        try:
            return self._pares[par_id]
        except KeyError as ausente:
            raise NaoEncontrado(f"par:{par_id}") from ausente

    def pares(self) -> tuple[ParObstaculoOI, ...]:
        return tuple(sorted(self._pares.values(), key=lambda p: str(p.id)))

    def elipse(self, elipse_id: UUID) -> ElipseDeSimultaneidade:
        try:
            return self._elipses[elipse_id]
        except KeyError as ausente:
            raise NaoEncontrado(f"elipse:{elipse_id}") from ausente

    def elipses(self) -> tuple[ElipseDeSimultaneidade, ...]:
        return tuple(sorted(self._elipses.values(), key=lambda e: str(e.id)))

    # -- grafo, pela raiz --------------------------------------------------------

    def adicionar_obstaculo(self, *, titulo: str, em: datetime, **kw) -> No:
        return self._adicionar(PapelNaAPR.OBSTACULO, titulo=titulo, em=em, **kw)

    def adicionar_objetivo_intermediario(self, *, titulo: str, em: datetime, **kw) -> No:
        return self._adicionar(PapelNaAPR.OBJETIVO_INTERMEDIARIO, titulo=titulo, em=em, **kw)

    def _adicionar(
        self,
        papel: PapelNaAPR,
        *,
        titulo: str,
        em: datetime,
        descricao: str = "",
        posicao: PosicaoNoCanvas | None = None,
        no_id: UUID | None = None,
    ) -> No:
        if PapelNaAPR(papel) is PapelNaAPR.OBJETIVO:
            raise PapelNaAprInvalido(
                "objetivo_unico", "a APR tem exatamente um objetivo, criado na origem"
            )
        with self._nucleo() as nucleo:
            return nucleo.adicionar_no(
                titulo=titulo,
                descricao=descricao,
                tipo=TIPO_DE_NO_POR_PAPEL[PapelNaAPR(papel)],
                posicao=posicao,
                no_id=no_id,
                em=em,
            )

    def editar_objetivo(self, texto: str, *, em: datetime) -> No:
        """RF-14: o texto do objetivo é editável — o papel dele não."""
        return self.editar_no(self.objetivo.id, titulo=texto, em=em)

    def editar_no(self, no_id: UUID, *, em: datetime, **kw) -> No:
        with self._nucleo() as nucleo:
            return nucleo.editar_no(no_id, em=em, **kw)

    def mover_no(self, no_id: UUID, posicao: PosicaoNoCanvas, *, em: datetime) -> No:
        with self._nucleo() as nucleo:
            return nucleo.mover_no(no_id, posicao, em=em)

    def recolher_no(self, no_id: UUID, recolhido: bool, *, em: datetime) -> No:
        with self._nucleo() as nucleo:
            return nucleo.recolher_no(no_id, recolhido, em=em)

    def mudar_papel(self, no_id: UUID, papel: PapelNaAPR, *, em: datetime) -> No:
        papel = PapelNaAPR(papel)
        atual = self.papel_do_no(no_id)
        if atual is PapelNaAPR.OBJETIVO or papel is PapelNaAPR.OBJETIVO:
            raise PapelNaAprInvalido(
                "objetivo_imutavel",
                "o objetivo da APR é único e o papel dele não muda (RF-14); o texto sim",
            )
        if papel is atual:
            raise PapelNaAprInvalido("sem_mudanca", f"o nó já é {atual.value}")
        # Mudar o papel desfaz o par que citava o nó: um obstáculo que virou objetivo
        # intermediário não é mais superado por ninguém, e o par ficaria de pé sem sentido.
        for par in list(self._pares.values()):
            if no_id in (par.obstaculo_id, par.objetivo_intermediario_id):
                self._pares.pop(par.id)
                self._emitir(ParDesfeito, em, par_id=par.id)
        alvo = self.projeto.no(no_id)
        alvo.tipo = TIPO_DE_NO_POR_PAPEL[papel]
        self.projeto._avancar(em)
        self._emitir(PapelNaAprMudou, em, no_id=no_id, de=atual.value, para=papel.value)
        return alvo

    def depender(self, antes_id: UUID, depois_id: UUID, *, em: datetime, **kw) -> ArestaCausal:
        """RF-16: "A precisa existir antes de B" — entre OIs, ou de um OI ao objetivo.

        Obstáculo não entra na dependência: ele é **anotado** ao lado do elo que motiva
        (RI-04), e quem entra na sequência é o OI que o supera. Deixar obstáculo virar
        etapa devolveria a lista de tarefas que a APR existe para não ser.
        """
        for identificador, ponta in ((antes_id, "origem"), (depois_id, "destino")):
            papel = self.papel_do_no(identificador)
            if papel is PapelNaAPR.OBSTACULO:
                raise PapelNaAprInvalido(
                    "dependencia_entre_objetivos",
                    f"a {ponta} da dependência é um obstáculo; a sequência liga objetivos "
                    "intermediários (e o objetivo no topo) — o obstáculo é anotado no elo",
                )
        if self.papel_do_no(antes_id) is PapelNaAPR.OBJETIVO:
            raise PapelNaAprInvalido(
                "dependencia_entre_objetivos",
                "o objetivo é o topo da árvore: nada depende dele",
            )
        with self._nucleo() as nucleo:
            return nucleo.ligar(antes_id, depois_id, em=em, **kw)

    def leitura_da_dependencia(self, aresta_id: UUID) -> str:
        """RF-16: a leitura de NECESSIDADE — montada dos textos atuais, sem "se… então"."""
        aresta = self.projeto.aresta(aresta_id)
        antes = self.projeto.no(aresta.origem_id).titulo
        depois = self.projeto.no(aresta.destino_id).titulo
        return f"{antes} precisa existir antes de {depois}"

    def excluir_dependencia(self, aresta_id: UUID, *, em: datetime) -> None:
        with self._nucleo() as nucleo:
            nucleo.excluir_aresta(aresta_id, em=em)
        self._soltar_das_elipses(aresta_id, em=em)

    def excluir_no(self, no_id: UUID, *, em: datetime) -> list[UUID]:
        """Exclui o nó e não deixa par nem elipse órfãos. O objetivo não se exclui."""
        papel = self.papel_do_no(no_id)
        if papel is PapelNaAPR.OBJETIVO:
            raise PapelNaAprInvalido(
                "objetivo_indestrutivel",
                "o objetivo é criado na origem e vive enquanto o projeto viver (RF-14)",
            )
        with self._nucleo() as nucleo:
            removidas = nucleo.excluir_no(no_id, em=em)
        for aresta_id in removidas:
            self._soltar_das_elipses(aresta_id, em=em)
        for par in list(self._pares.values()):
            if no_id in (par.obstaculo_id, par.objetivo_intermediario_id):
                self._pares.pop(par.id)
                self._emitir(ParDesfeito, em, par_id=par.id)
        return removidas

    # -- pareamento e teste de validade (RF-17, RF-18, RN-07) --------------------

    def parear(
        self, obstaculo_id: UUID, oi_id: UUID, *, em: datetime, par_id: UUID | None = None
    ) -> ParObstaculoOI:
        self.projeto._exigir_ativo("parear")
        if self.papel_do_no(obstaculo_id) is not PapelNaAPR.OBSTACULO:
            raise ParInvalido(
                "papel_incompativel", f"o nó {obstaculo_id} não é um obstáculo"
            )
        if self.papel_do_no(oi_id) is not PapelNaAPR.OBJETIVO_INTERMEDIARIO:
            raise ParInvalido(
                "papel_incompativel", f"o nó {oi_id} não é um objetivo intermediário"
            )
        if any(p.obstaculo_id == obstaculo_id for p in self._pares.values()):
            raise ParInvalido(
                "obstaculo_ja_pareado",
                f"o obstáculo {obstaculo_id} já tem objetivo intermediário; um OI supera "
                "vários obstáculos, mas o obstáculo tem uma resposta só",
            )
        par = ParObstaculoOI(
            id=par_id or uuid4(),
            obstaculo_id=obstaculo_id,
            objetivo_intermediario_id=oi_id,
        )
        self._pares[par.id] = par
        self.projeto._avancar(em)
        self._emitir(
            ObstaculoPareado,
            em,
            par_id=par.id,
            obstaculo_id=obstaculo_id,
            objetivo_intermediario_id=oi_id,
        )
        return par

    def desfazer_par(self, par_id: UUID, *, em: datetime) -> None:
        self.par(par_id)
        self._pares.pop(par_id)
        self.projeto._avancar(em)
        self._emitir(ParDesfeito, em, par_id=par_id)

    def leitura_do_teste_de_validade(self, par_id: UUID) -> str:
        """O teste IO-Obstáculo da referência, montado dos textos ATUAIS."""
        par = self.par(par_id)
        return (
            f"Se {self.projeto.no(par.objetivo_intermediario_id).titulo}, "
            f"então {self.projeto.no(par.obstaculo_id).titulo} "
            f"não impede mais {self.objetivo.titulo}"
        )

    def julgar_par(
        self,
        par_id: UUID,
        *,
        autor: str,
        valido: bool,
        justificativa: str,
        em: datetime,
    ) -> ParObstaculoOI:
        """RN-07: o julgamento **acumula**; nenhum parecer some para dar lugar a outro."""
        self.projeto._exigir_ativo("julgar_par")
        par = self.par(par_id)
        julgamento = JulgamentoDeValidade(
            autor=texto_de_dominio(autor, campo="julgamento.autor", minimo=1, maximo=LIMITE_AUTOR),
            valido=bool(valido),
            justificativa=texto_de_dominio(
                justificativa,
                campo="julgamento.justificativa",
                minimo=1,
                maximo=LIMITE_JUSTIFICATIVA,
            ),
            instante=em,
        )
        par.julgamentos = par.julgamentos + (julgamento,)
        self.projeto._avancar(em)
        self._emitir(
            TesteDeValidadeJulgado, em, par_id=par.id, autor=julgamento.autor, valido=julgamento.valido
        )
        return par

    def pendencias_de_pareamento(self) -> dict[str, tuple[UUID, ...]]:
        """RN-09: pendências listadas, **nunca** proibições de gravação."""
        pareados = {p.obstaculo_id for p in self._pares.values()}
        com_obstaculo = {p.objetivo_intermediario_id for p in self._pares.values()}
        return {
            "obstaculos_sem_oi": tuple(
                n.id for n in self.obstaculos if n.id not in pareados
            ),
            "objetivos_sem_obstaculo": tuple(
                n.id for n in self.objetivos_intermediarios if n.id not in com_obstaculo
            ),
        }

    # -- elipse de simultaneidade (RF-19, RN-06) ---------------------------------

    def formar_elipse(
        self, dependencias: Sequence[UUID], *, em: datetime, elipse_id: UUID | None = None
    ) -> ElipseDeSimultaneidade:
        if len(set(dependencias)) < 2:
            raise ElipseInvalida(
                "minimo_duas_dependencias",
                "a elipse agrupa duas ou mais dependências do MESMO destino",
            )
        alvos = [self.projeto.aresta(a) for a in dependencias]
        destinos = {a.destino_id for a in alvos}
        if len(destinos) != 1:
            raise ElipseInvalida(
                "destino_unico",
                "toda dependência da elipse aponta para o mesmo objetivo intermediário",
            )
        agrupadas = {a for e in self._elipses.values() for a in e.dependencias}
        repetidas = sorted(set(dependencias) & agrupadas, key=str)
        if repetidas:
            raise ElipseInvalida(
                "dependencia_ja_agrupada",
                f"a(s) dependência(s) {repetidas} já pertence(m) a uma elipse",
            )
        elipse = ElipseDeSimultaneidade(
            id=elipse_id or uuid4(),
            destino_id=destinos.pop(),
            dependencias=tuple(dependencias),
        )
        self._elipses[elipse.id] = elipse
        self.projeto._avancar(em)
        self._emitir(
            ElipseFormada,
            em,
            elipse_id=elipse.id,
            destino_id=elipse.destino_id,
            dependencias=elipse.dependencias,
        )
        return elipse

    def desfazer_elipse(self, elipse_id: UUID, *, em: datetime) -> None:
        self.elipse(elipse_id)
        self._elipses.pop(elipse_id)
        self.projeto._avancar(em)
        self._emitir(ElipseDesfeita, em, elipse_id=elipse_id)

    def leitura_da_elipse(self, elipse_id: UUID) -> str:
        """RF-19: "A **e** B precisam existir antes de C" — conjunção de NECESSIDADE."""
        elipse = self.elipse(elipse_id)
        antes = [
            self.projeto.no(self.projeto.aresta(a).origem_id).titulo
            for a in elipse.dependencias
        ]
        return (
            f"{' e '.join(antes)} precisam existir antes de "
            f"{self.projeto.no(elipse.destino_id).titulo}"
        )

    def _soltar_das_elipses(self, aresta_id: UUID, *, em: datetime) -> None:
        """Dependência que some leva junto a citação — nunca deixa referência órfã."""
        for elipse in list(self._elipses.values()):
            if aresta_id in elipse.dependencias:
                restantes = tuple(a for a in elipse.dependencias if a != aresta_id)
                self._elipses.pop(elipse.id)
                self._emitir(ElipseDesfeita, em, elipse_id=elipse.id)
                if len(restantes) >= 2:
                    nova = ElipseDeSimultaneidade(
                        id=elipse.id, destino_id=elipse.destino_id, dependencias=restantes
                    )
                    self._elipses[nova.id] = nova
                    self._emitir(
                        ElipseFormada,
                        em,
                        elipse_id=nova.id,
                        destino_id=nova.destino_id,
                        dependencias=nova.dependencias,
                    )

    # -- verbalização avaliada (RF-20, RF-21, RN-08) -----------------------------

    def avaliar_verbalizacao(self, no_id: UUID, *, idioma: str = "pt") -> VerbalizacaoAvaliada:
        """Função pura sobre o texto ATUAL — por isso a reavaliação é automática (RF-21).

        Não há campo guardado com o veredito, e é essa ausência que faz o aviso nunca
        ficar pendurado sobre um texto que já mudou. **Avisa, não veta** (RN-08): quem
        registra é o `adicionar_obstaculo`, e ele não consulta esta função.
        """
        papel = self.papel_do_no(no_id)
        alvo = PAPEL_VERBALIZADO_POR_PAPEL.get(papel)
        if alvo is None:
            raise MutacaoRecusada(
                "avaliar_verbalizacao: a heurística cobre obstáculo e objetivo "
                "intermediário; o objetivo da APR é a condição final e não tem armadilha "
                "catalogada na fonte técnica"
            )
        return avaliar_verbalizacao(alvo, self.projeto.no(no_id).titulo, idioma=idioma)

    # -- sequenciamento (RF-23..RF-27, RN-06) ------------------------------------

    def sequenciar(self) -> Sequenciamento:
        """Função pura: camadas topológicas, ramos paralelos, elipses e ciclos."""
        objetivos = [n.id for n in self.objetivos_intermediarios]
        conjunto = set(objetivos)
        dependencias = [
            a for a in self.projeto.arestas
            if a.origem_id in conjunto and a.destino_id in conjunto
        ]

        ciclos = tuple(
            tuple(c) for c in ciclos_do_grafo(tuple(objetivos), tuple(dependencias))
        )
        camadas: tuple[tuple[UUID, ...], ...] = ()
        if not ciclos:
            camadas = _camadas_topologicas(objetivos, dependencias)

        pendencias = self.pendencias_de_pareamento()
        return Sequenciamento(
            camadas=camadas,
            ramos_paralelos=_componentes(objetivos, dependencias),
            elipses=tuple(e.id for e in self.elipses()),
            ciclos=ciclos,
            obstaculos_sem_oi=pendencias["obstaculos_sem_oi"],
            objetivos_sem_obstaculo=pendencias["objetivos_sem_obstaculo"],
        )

    def gerar_sequenciamento(self, *, em: datetime) -> Sequenciamento:
        """RF-26: a mesma função pura, com o evento do resumo quantitativo por cima."""
        sequencia = self.sequenciar()
        self._emitir(SequenciamentoGerado, em, resumo=sequencia.resumo())
        return sequencia

    def tabela_resumo(self) -> tuple[LinhaDoResumo, ...]:
        """RF-25: obstáculo · OI que o supera · de quem depende, na ordem das camadas.

        O que **não** some da tabela: o obstáculo sem par entra no fim, com camada `None`
        — pendência à vista (RN-09), nunca linha ausente.
        """
        sequencia = self.sequenciar()
        por_oi: dict[UUID, list[ParObstaculoOI]] = {}
        for par in self.pares():
            por_oi.setdefault(par.objetivo_intermediario_id, []).append(par)

        entrada = {
            a.destino_id: [] for a in self.projeto.arestas
        }
        for aresta in self.projeto.arestas:
            entrada.setdefault(aresta.destino_id, []).append(aresta.origem_id)

        linhas: list[LinhaDoResumo] = []
        ordenados = [
            no_id for camada in sequencia.camadas for no_id in camada
        ] or [n.id for n in self.objetivos_intermediarios]
        for oi_id in ordenados:
            titulo = self.projeto.no(oi_id).titulo
            depende_de = tuple(
                self.projeto.no(origem).titulo for origem in entrada.get(oi_id, [])
            )
            pares = por_oi.get(oi_id, [])
            if not pares:
                linhas.append(
                    LinhaDoResumo(
                        camada=sequencia.camada_de(oi_id),
                        objetivo_intermediario=titulo,
                        objetivo_intermediario_id=oi_id,
                        obstaculo=None,
                        obstaculo_id=None,
                        depende_de=depende_de,
                    )
                )
                continue
            for par in pares:
                ultimo = par.ultimo_julgamento
                linhas.append(
                    LinhaDoResumo(
                        camada=sequencia.camada_de(oi_id),
                        objetivo_intermediario=titulo,
                        objetivo_intermediario_id=oi_id,
                        obstaculo=self.projeto.no(par.obstaculo_id).titulo,
                        obstaculo_id=par.obstaculo_id,
                        depende_de=depende_de,
                        julgamento=(
                            f"{'válido' if ultimo.valido else 'inválido'} — {ultimo.autor}"
                            if ultimo
                            else ""
                        ),
                    )
                )
        for obstaculo_id in sequencia.obstaculos_sem_oi:
            linhas.append(
                LinhaDoResumo(
                    camada=None,
                    objetivo_intermediario=None,
                    objetivo_intermediario_id=None,
                    obstaculo=self.projeto.no(obstaculo_id).titulo,
                    obstaculo_id=obstaculo_id,
                )
            )
        return tuple(linhas)

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
# Funções puras do sequenciamento — sem agregado, testáveis sozinhas
# --------------------------------------------------------------------------------------


def _camadas_topologicas(
    nos: Sequence[UUID], arestas: Sequence[ArestaCausal]
) -> tuple[tuple[UUID, ...], ...]:
    """Camadas de implementação: quem não depende de nada primeiro (RF-23).

    Ordem canônica dentro da camada (por identificador) porque o plano tem de sair igual
    duas vezes: um sequenciamento que muda de ordem a cada leitura não se leva a reunião.
    """
    restantes = {n for n in nos}
    entrada = {n: 0 for n in nos}
    for aresta in arestas:
        if aresta.destino_id in entrada:
            entrada[aresta.destino_id] += 1
    saida = sucessores(tuple(arestas))

    camadas: list[tuple[UUID, ...]] = []
    while restantes:
        nivel = sorted((n for n in restantes if entrada[n] == 0), key=str)
        if not nivel:  # pragma: no cover - `sequenciar` já barrou o ciclo antes
            break
        camadas.append(tuple(nivel))
        for no in nivel:
            restantes.discard(no)
            for destino in saida.get(no, []):
                if destino in entrada:
                    entrada[destino] -= 1
    return tuple(camadas)


def _componentes(
    nos: Sequence[UUID], arestas: Sequence[ArestaCausal]
) -> tuple[tuple[UUID, ...], ...]:
    """Ramos paralelos: as partes do grafo que não se tocam — o que pode andar junto."""
    vizinhos: dict[UUID, set[UUID]] = {n: set() for n in nos}
    for aresta in arestas:
        vizinhos[aresta.origem_id].add(aresta.destino_id)
        vizinhos[aresta.destino_id].add(aresta.origem_id)
    vistos: set[UUID] = set()
    ramos: list[tuple[UUID, ...]] = []
    for no in sorted(nos, key=str):
        if no in vistos:
            continue
        pilha, grupo = [no], []
        vistos.add(no)
        while pilha:
            atual = pilha.pop()
            grupo.append(atual)
            for vizinho in sorted(vizinhos[atual], key=str):
                if vizinho not in vistos:
                    vistos.add(vizinho)
                    pilha.append(vizinho)
        ramos.append(tuple(sorted(grupo, key=str)))
    return tuple(ramos)


# --------------------------------------------------------------------------------------
# Fábricas: criar e reidratar
# --------------------------------------------------------------------------------------


def novo_projeto_apr(
    *,
    id: UUID,
    dono: DonoDoProjeto,
    nome: str,
    objetivo: str,
    em: datetime,
    descricao_do_problema: str = "",
    origem: Ponta | None = None,
    objetivo_id: UUID | None = None,
) -> ProjetoAPR:
    """RF-14: a APR nasce **com** o objetivo — não existe APR sem o topo dela.

    A fábrica É a raiz nascendo: o nó do objetivo é criado de dentro do `sob_a_raiz`, e
    por isso o núcleo o aceita. Fora daqui não há caminho que o crie.
    """
    projeto = Projeto(
        id=id,
        dono=dono,
        nome=nome,
        ferramenta=FERRAMENTA_APR,
        descricao_do_problema=texto_de_dominio(
            descricao_do_problema,
            campo="descricao_do_problema",
            minimo=0,
            maximo=LIMITE_DESCRICAO,
        ),
        criado_em=em,
        alterado_em=em,
    )
    with projeto.sob_a_raiz() as nucleo:
        alvo = nucleo.adicionar_no(
            titulo=objetivo,
            tipo=TIPO_DE_NO_POR_PAPEL[PapelNaAPR.OBJETIVO],
            posicao=PosicaoNoCanvas(0.0, 0.0),
            no_id=objetivo_id,
            em=em,
        )
    # A fila do M1 descreve a mecânica (um `NoAdicionado`); o que a ferramenta relata é UM
    # ato — a APR nasceu com o seu objetivo.
    projeto.eventos = ()
    arvore = ProjetoAPR(projeto=projeto, origem=origem)
    arvore._emitir(AprCriada, em, objetivo_id=alvo.id)
    return arvore


def reidratar_apr(
    projeto: Projeto,
    *,
    pares: Iterable[ParObstaculoOI] = (),
    elipses: Iterable[ElipseDeSimultaneidade] = (),
    origem: Ponta | None = None,
) -> ProjetoAPR:
    """Monta a APR a partir do que estava GRAVADO — sem emitir evento nenhum."""
    arvore = ProjetoAPR(projeto=projeto, origem=origem)
    arvore._pares = {p.id: p for p in pares}
    arvore._elipses = {e.id: e for e in elipses}
    projeto.eventos = ()
    return arvore


__all__ = [
    "FERRAMENTA_APR",
    "PAPEL_POR_TIPO_DE_NO",
    "TIPO_DE_NO_POR_PAPEL",
    "ElipseDeSimultaneidade",
    "ElipseInvalida",
    "JulgamentoDeValidade",
    "LinhaDoResumo",
    "PapelNaAPR",
    "PapelNaAprInvalido",
    "ParInvalido",
    "ParObstaculoOI",
    "ProjetoAPR",
    "Sequenciamento",
    "novo_projeto_apr",
    "reidratar_apr",
]
