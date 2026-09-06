"""M2 — a Árvore da Realidade Atual (ARA) sobre o núcleo do M1 (spec 005).

**Por composição, nunca por herança do núcleo.** A regra RN-04 da spec 004 diz que o M1
não conhece semântica da Teoria das Restrições (TOC) — nem Efeito Indesejável (UDE), nem
premissa, nem injeção. É essa fronteira que impede a sétima cópia de canvas: as
ferramentas de M2 a M6 acrescentam entidades e regras próprias **sobre** o núcleo, sem
reimplementar grafo. Por isso `ProjetoARA` **contém** um `Projeto` em vez de estendê-lo, e
o que é semântica da ARA (marcador de UDE, ficha, status, parecer, exame de elo, conector
E) vive em mapas deste módulo.

O que este módulo corrige da linhagem, em uma frase por item:

- a **validação formal** é função pura do domínio (`criterios_ude`), não prompt de modelo
  interpolado no navegador (`tocbuilderv3/constants.ts:123-133`, defeito D-08);
- **quem validou e quando** vive em evento, não em campo editável — na linhagem
  `validado_por` era texto devolvido pelo modelo (`tocbuilderv3/types.ts:171-213`);
- o **status `Validado`** tem guarda de máquina de estados (RN-10): decidíveis verdes
  **e** parecer humano confirmado. Parecer de inteligência artificial (IA) nunca fecha
  status sozinho.
"""
from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass, field, replace
from datetime import datetime
from enum import Enum
from typing import Iterator
from uuid import UUID, uuid4

from .analise import RelatorioEstrutural, analisar_estrutura
from .criterios_ude import ValidacaoFormal, validar_formalmente
from .erros import DadoInvalido, MutacaoRecusada, NaoEncontrado
from .eventos import (
    AnaliseEstruturalGerada,
    ConectorEDesfeito,
    ConectorEFormado,
    EloExaminado,
    FichaDeUdeEditada,
    ParecerRegistrado,
    StatusDeValidacaoMudou,
    UdeArquivado,
    UdeDesmarcado,
    UdeMarcado,
    ValidacaoFormalExecutada,
)
from .grafo import ArestaCausal, No
from .identidade import DonoDoProjeto
from .projeto import Projeto, registrar_raiz_de_ferramenta
from .valores import PosicaoNoCanvas

#: O tipo de projeto do M2 (spec 005, RF-01) — o M1 nunca precisa saber deste nome.
FERRAMENTA_ARA = "ara"

#: A ARA é a RAIZ do agregado do M2: o grafo de um projeto `ara` só muda por dentro
#: dela (`Projeto._exigir_raiz`). Sem isto, `Projeto.ligar` criava elo sem exame,
#: `Projeto.excluir_no` sumia com um Efeito Indesejável sem arquivar a ficha e
#: `Projeto.excluir_aresta` deixava conector apontando para aresta que não existe mais.
registrar_raiz_de_ferramenta(FERRAMENTA_ARA, "ProjetoARA")

#: Todo nó da ARA é um **efeito**; "causa" é POSIÇÃO na cadeia, não tipo de nó (F-15).
TIPO_DE_NO_EFEITO = "efeito"


class StatusDeValidacao(str, Enum):
    """Os quatro estados da linhagem (`tocbuilderv3/types.ts:207`), agora com guarda."""

    PENDENTE = "pendente"
    REQUER_REFINAMENTO = "requer_refinamento"
    VALIDADO = "validado"
    REJEITADO = "rejeitado"


class OrigemDoParecer(str, Enum):
    HUMANO = "humano"
    CATALOGO = "catalogo"


class EstadoDoExame(str, Enum):
    """O exame de suficiência do elo (RF-22) — dado de primeira classe, não anotação."""

    NAO_EXAMINADO = "nao_examinado"
    SUFICIENTE = "suficiente"
    INSUFICIENTE = "insuficiente"
    COM_RESERVA = "com_reserva"


EXIGEM_RESERVA = (EstadoDoExame.INSUFICIENTE, EstadoDoExame.COM_RESERVA)


class TransicaoDeStatusRecusada(MutacaoRecusada):
    """A guarda da RN-10 falou. `motivo` é legível por máquina, não só por gente."""

    def __init__(self, motivo: str, detalhe: str = "") -> None:
        super().__init__(f"{motivo}: {detalhe}" if detalhe else motivo)
        self.motivo = motivo


class ConectorInvalido(MutacaoRecusada):
    """RN-11 violada. `regra`: `minimo_duas_arestas`, `destino_unico`, `aresta_ja_conectada`."""

    def __init__(self, regra: str, detalhe: str = "") -> None:
        super().__init__(f"{regra}: {detalhe}" if detalhe else regra)
        self.regra = regra


@dataclass(frozen=True, slots=True)
class FichaDeUde:
    """Os campos da ficha da linhagem (`types.ts:171-213`), SEM os de auditoria.

    Os de auditoria viraram evento, e é essa a diferença que faz "Validado" significar
    algo (RF-16): campo se edita, evento não.
    """

    area_impactada: str = ""
    objetivo_afetado: str = ""
    evidencias: tuple[str, ...] = ()
    frequencia: str = ""
    impactos_estimados: str = ""


@dataclass(frozen=True, slots=True)
class ParecerDeJulgamento:
    """O julgamento sobre o que nenhuma função pura decide. Acumula, nunca sobrescreve."""

    autor: str
    origem: OrigemDoParecer
    favoravel: bool
    justificativa: str
    instante: datetime
    proposta_id: str | None = None
    criterios: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.autor.strip():
            raise DadoInvalido("parecer sem autor")
        if not self.justificativa.strip():
            raise DadoInvalido("parecer sem justificativa")


@dataclass(frozen=True, slots=True)
class Exame:
    estado: EstadoDoExame = EstadoDoExame.NAO_EXAMINADO
    reserva: str = ""


@dataclass(frozen=True, slots=True)
class ConectorE:
    """Conjunção: "Se A **e** B, então C" — a elipse canônica da TOC (RN-11)."""

    id: UUID
    destino_id: UUID
    arestas: tuple[UUID, ...]


@dataclass(slots=True)
class ProjetoARA:
    """A ARA: um `Projeto` do M1 mais a semântica da ferramenta."""

    projeto: Projeto
    _udes: dict[UUID, FichaDeUde] = field(default_factory=dict)
    _validacoes: dict[UUID, ValidacaoFormal] = field(default_factory=dict)
    _pareceres: dict[UUID, list[ParecerDeJulgamento]] = field(default_factory=dict)
    _status: dict[UUID, StatusDeValidacao] = field(default_factory=dict)
    _exames: dict[UUID, Exame] = field(default_factory=dict)
    _conectores: dict[UUID, ConectorE] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.projeto.ferramenta != FERRAMENTA_ARA:
            raise MutacaoRecusada(
                f"ProjetoARA exige ferramenta {FERRAMENTA_ARA!r}, "
                f"veio {self.projeto.ferramenta!r}"
            )

    # -- delegação ao núcleo -----------------------------------------------------

    @contextmanager
    def _nucleo(self) -> Iterator[Projeto]:
        """Abre o núcleo do M1 PARA A RAIZ. Toda delegação da ARA passa por aqui.

        Fora deste `with`, o `Projeto` de uma ARA recusa mutação de grafo — é o que
        fecha a porta dos fundos que as rotas genéricas de `/toc/projetos` abriam, e por
        onde a própria interface da ferramenta estava passando.
        """
        with self.projeto.sob_a_raiz() as nucleo:
            yield nucleo

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

    def adicionar_efeito(
        self,
        *,
        titulo: str,
        em: datetime,
        descricao: str = "",
        posicao: PosicaoNoCanvas | None = None,
        no_id: UUID | None = None,
    ) -> No:
        """Nó da ARA. Todo nó é um efeito: causa é posição na cadeia, não tipo (F-15)."""
        with self._nucleo() as nucleo:
            return nucleo.adicionar_no(
                titulo=titulo,
                descricao=descricao,
                tipo=TIPO_DE_NO_EFEITO,
                posicao=posicao,
                no_id=no_id,
                em=em,
            )

    def ligar(self, origem_id: UUID, destino_id: UUID, *, em: datetime, **kw):
        """Aresta de suficiência. Herda as invariantes do M1 sem exceção nova (RF-20)."""
        with self._nucleo() as nucleo:
            aresta = nucleo.ligar(origem_id, destino_id, em=em, **kw)
        self._exames[aresta.id] = Exame()
        return aresta

    def excluir_no(self, no_id: UUID, *, em: datetime) -> list[UUID]:
        """Exclui o nó pelo núcleo e ARQUIVA ficha, pareceres e status (RF-05)."""
        marcado = no_id in self._udes
        ficha = self._udes.get(no_id)
        pareceres = tuple(self._pareceres.get(no_id, ()))
        status = self._status.get(no_id)
        with self._nucleo() as nucleo:
            removidas = nucleo.excluir_no(no_id, em=em)
        for aresta_id in removidas:
            self._exames.pop(aresta_id, None)
            self._soltar_das_conjuncoes(aresta_id)
        if marcado:
            self._udes.pop(no_id, None)
            self._validacoes.pop(no_id, None)
            self._pareceres.pop(no_id, None)
            self._status.pop(no_id, None)
            self._emitir(
                UdeArquivado, em,
                no_id=no_id, ficha=ficha, pareceres=pareceres, status=status,
            )
        return removidas

    # -- as operações de grafo que faltavam à raiz -------------------------------
    #
    # Não são conveniência: enquanto a ARA não as tinha, a interface da própria
    # ferramenta chamava as rotas genéricas de `/toc/projetos` para mover, editar,
    # rotular e apagar — e cada uma dessas chamadas passava por fora das invariantes
    # abaixo. Uma raiz sem a operação que o produto precisa é uma raiz que o produto
    # contorna.

    def editar_no(
        self,
        no_id: UUID,
        *,
        em: datetime,
        titulo: str | None = None,
        descricao: str | None = None,
    ) -> No:
        """Edita o nó. Mudar o TÍTULO de um Efeito Indesejável REVALIDA (RF-10).

        É a mesma garantia de `reformular`, agora sem porta alternativa: não existe
        caminho em que o texto de um Efeito Indesejável mude e o veredito formal anterior
        continue pendurado sobre ele.
        """
        anterior = self.projeto.no(no_id).titulo
        with self._nucleo() as nucleo:
            alvo = nucleo.editar_no(no_id, titulo=titulo, descricao=descricao, em=em)
        if self.e_ude(no_id) and alvo.titulo != anterior:
            self._revalidar(alvo, em=em, texto_anterior=anterior)
        return alvo

    def mover_no(self, no_id: UUID, posicao: PosicaoNoCanvas, *, em: datetime) -> No:
        """Arrastar no canvas. Sem semântica da ARA acima — e ainda assim pela raiz."""
        with self._nucleo() as nucleo:
            return nucleo.mover_no(no_id, posicao, em=em)

    def recolher_no(self, no_id: UUID, recolhido: bool, *, em: datetime) -> No:
        with self._nucleo() as nucleo:
            return nucleo.recolher_no(no_id, recolhido, em=em)

    def editar_aresta(self, aresta_id: UUID, rotulo: str, *, em: datetime) -> ArestaCausal:
        with self._nucleo() as nucleo:
            return nucleo.editar_aresta(aresta_id, rotulo, em=em)

    def excluir_aresta(self, aresta_id: UUID, *, em: datetime) -> None:
        """Some com o elo E com o que dependia dele: o exame e a citação em conector.

        A RN-11 diz que aresta que some leva junto o conector que a citava — "nunca deixa
        referência órfã". `_soltar_das_conjuncoes` já existia e só rodava por dentro de
        `excluir_no`: apagar a aresta sozinha não tinha caminho pela raiz, então o
        produto apagava pela rota genérica e o conector ficava apontando para uma aresta
        que não existe mais.
        """
        with self._nucleo() as nucleo:
            nucleo.excluir_aresta(aresta_id, em=em)
        self._exames.pop(aresta_id, None)
        self._soltar_das_conjuncoes(aresta_id)

    # -- UDE: marcador, ficha e validação formal ---------------------------------

    def e_ude(self, no_id: UUID) -> bool:
        return no_id in self._udes

    @property
    def udes(self) -> frozenset[UUID]:
        return frozenset(self._udes)

    def ficha(self, no_id: UUID) -> FichaDeUde:
        try:
            return self._udes[no_id]
        except KeyError as ausente:
            raise NaoEncontrado(f"ude:{no_id}") from ausente

    def validacao(self, no_id: UUID) -> ValidacaoFormal:
        try:
            return self._validacoes[no_id]
        except KeyError as ausente:
            raise NaoEncontrado(f"validacao:{no_id}") from ausente

    def pareceres(self, no_id: UUID) -> tuple[ParecerDeJulgamento, ...]:
        return tuple(self._pareceres.get(no_id, ()))

    def status(self, no_id: UUID) -> StatusDeValidacao:
        try:
            return self._status[no_id]
        except KeyError as ausente:
            raise NaoEncontrado(f"status:{no_id}") from ausente

    def marcar_ude(
        self, no_id: UUID, *, em: datetime, ficha: FichaDeUde | None = None
    ) -> FichaDeUde:
        alvo = self.projeto.no(no_id)  # NaoEncontrado se não existe
        if self.e_ude(no_id):
            raise MutacaoRecusada(f"marcar_ude: {no_id} já é UDE")
        self._udes[no_id] = ficha or FichaDeUde()
        self._pareceres.setdefault(no_id, [])
        self._status[no_id] = StatusDeValidacao.PENDENTE
        self._emitir(UdeMarcado, em, no_id=no_id)
        self._revalidar(alvo, em=em, texto_anterior=None)
        return self._udes[no_id]

    def desmarcar_ude(self, no_id: UUID, *, em: datetime) -> None:
        self.ficha(no_id)
        self._udes.pop(no_id)
        self._validacoes.pop(no_id, None)
        self._status.pop(no_id, None)
        self._emitir(UdeDesmarcado, em, no_id=no_id)

    def editar_ficha(self, no_id: UUID, ficha: FichaDeUde, *, em: datetime) -> FichaDeUde:
        self.ficha(no_id)
        self._udes[no_id] = ficha
        self._emitir(FichaDeUdeEditada, em, no_id=no_id)
        return ficha

    def reformular(self, no_id: UUID, titulo: str, *, em: datetime) -> No:
        """Edita o texto do nó e REEXECUTA a validação formal (RF-10).

        O veredito anterior não fica pendurado: o evento guarda os dois textos, e é por
        isso que "reformular" é uma operação nomeada e não um `editar_no` qualquer.
        """
        anterior = self.projeto.no(no_id).titulo
        with self._nucleo() as nucleo:
            alvo = nucleo.editar_no(no_id, titulo=titulo, em=em)
        if self.e_ude(no_id):
            self._revalidar(alvo, em=em, texto_anterior=anterior)
        return alvo

    def _revalidar(self, no: No, *, em: datetime, texto_anterior: str | None) -> None:
        validacao = validar_formalmente(no.titulo)
        self._validacoes[no.id] = validacao
        # Reprovado nos decidíveis não pode continuar `Validado` nem `Pendente`: o texto
        # mudou e a máquina já tem veredito. Só o `Rejeitado` é decisão humana e fica.
        if (
            not validacao.aprovado_nos_decidiveis
            and self._status.get(no.id) is not StatusDeValidacao.REJEITADO
        ):
            self._status[no.id] = StatusDeValidacao.REQUER_REFINAMENTO
        self._emitir(
            ValidacaoFormalExecutada,
            em,
            no_id=no.id,
            texto=no.titulo,
            texto_anterior=texto_anterior,
            aprovado_nos_decidiveis=validacao.aprovado_nos_decidiveis,
            reprovacoes=tuple(v.criterio.codigo for v in validacao.reprovacoes),
            versao_do_lexico=validacao.versao_do_lexico,
        )

    # -- parecer e máquina de estados do status ----------------------------------

    def registrar_parecer(
        self, no_id: UUID, parecer: ParecerDeJulgamento, *, em: datetime
    ) -> None:
        self.ficha(no_id)
        self._pareceres.setdefault(no_id, []).append(parecer)
        self._emitir(
            ParecerRegistrado,
            em,
            no_id=no_id,
            autor=parecer.autor,
            origem=parecer.origem.value,
            favoravel=parecer.favoravel,
            proposta_id=parecer.proposta_id,
        )

    def mudar_status(
        self,
        no_id: UUID,
        novo: StatusDeValidacao,
        *,
        em: datetime,
        justificativa: str = "",
    ) -> StatusDeValidacao:
        """A guarda da RN-10, escrita uma vez e verificável (RF-14, RF-17)."""
        atual = self.status(no_id)
        if novo is atual:
            raise TransicaoDeStatusRecusada("sem_mudanca", f"já está em {atual.value}")
        if novo is StatusDeValidacao.VALIDADO:
            if not self.validacao(no_id).aprovado_nos_decidiveis:
                raise TransicaoDeStatusRecusada(
                    "criterio_decidivel_reprovado",
                    "há critério decidível vermelho; reformule o texto antes de validar",
                )
            if not self._tem_parecer_humano_favoravel(no_id):
                raise TransicaoDeStatusRecusada(
                    "sem_parecer_humano",
                    "falta parecer humano favorável cobrindo os critérios de julgamento; "
                    "parecer de IA nunca fecha status sozinho",
                )
        if atual is StatusDeValidacao.VALIDADO and not justificativa.strip():
            raise TransicaoDeStatusRecusada(
                "reabertura_sem_justificativa",
                "reabrir um UDE validado exige justificativa explícita (RF-17)",
            )
        self._status[no_id] = novo
        self._emitir(
            StatusDeValidacaoMudou,
            em,
            no_id=no_id,
            de=atual,
            para=novo,
            justificativa=justificativa.strip(),
        )
        return novo

    def _tem_parecer_humano_favoravel(self, no_id: UUID) -> bool:
        return any(
            p.origem is OrigemDoParecer.HUMANO and p.favoravel
            for p in self._pareceres.get(no_id, ())
        )

    def resumo_por_status(self) -> dict[StatusDeValidacao, int]:
        """RF-04: a contagem por status, para saber se a base da análise está madura."""
        contagem = {estado: 0 for estado in StatusDeValidacao}
        for estado in self._status.values():
            contagem[estado] += 1
        return contagem

    # -- exame de suficiência do elo ---------------------------------------------

    def exame(self, aresta_id: UUID) -> Exame:
        self.projeto.aresta(aresta_id)
        return self._exames.get(aresta_id, Exame())

    def examinar_elo(
        self,
        aresta_id: UUID,
        estado: EstadoDoExame,
        *,
        em: datetime,
        reserva: str = "",
    ) -> Exame:
        self.projeto.aresta(aresta_id)
        if estado in EXIGEM_RESERVA and not reserva.strip():
            raise MutacaoRecusada(
                f"examinar_elo: o estado {estado.value} exige a reserva escrita (RF-22)"
            )
        novo = Exame(estado=estado, reserva=reserva.strip())
        self._exames[aresta_id] = novo
        self._emitir(
            EloExaminado, em, aresta_id=aresta_id, estado=estado, reserva=novo.reserva
        )
        return novo

    def leitura_do_elo(self, aresta_id: UUID) -> str:
        """RF-19: montada dos textos ATUAIS dos nós — nunca de uma cópia congelada."""
        aresta = self.projeto.aresta(aresta_id)
        origem = self.projeto.no(aresta.origem_id).titulo
        destino = self.projeto.no(aresta.destino_id).titulo
        return f"Se {origem}, então {destino}"

    # -- conector E ---------------------------------------------------------------

    def formar_conector_e(
        self, arestas: tuple[UUID, ...], *, em: datetime, conector_id: UUID | None = None
    ) -> ConectorE:
        if len(set(arestas)) < 2:
            raise ConectorInvalido(
                "minimo_duas_arestas", "conjunção com uma aresta só não é conjunção"
            )
        alvos = [self.projeto.aresta(a) for a in arestas]
        destinos = {a.destino_id for a in alvos}
        if len(destinos) != 1:
            raise ConectorInvalido(
                "destino_unico", "toda aresta do conector aponta para o mesmo destino"
            )
        ja_conectadas = {a for c in self._conectores.values() for a in c.arestas}
        repetidas = sorted(set(arestas) & ja_conectadas, key=str)
        if repetidas:
            raise ConectorInvalido(
                "aresta_ja_conectada",
                f"a(s) aresta(s) {repetidas} já pertence(m) a um conector",
            )
        conector = ConectorE(
            id=conector_id or uuid4(),
            destino_id=destinos.pop(),
            arestas=tuple(arestas),
        )
        self._conectores[conector.id] = conector
        self._emitir(
            ConectorEFormado,
            em,
            conector_id=conector.id,
            destino_id=conector.destino_id,
            arestas=conector.arestas,
        )
        return conector

    def desfazer_conector_e(self, conector_id: UUID, *, em: datetime) -> None:
        if conector_id not in self._conectores:
            raise NaoEncontrado(f"conector:{conector_id}")
        self._conectores.pop(conector_id)
        self._emitir(ConectorEDesfeito, em, conector_id=conector_id)

    def leitura_do_conector(self, conector_id: UUID) -> str:
        """RF-24: "Se A **e** B, então C"."""
        try:
            conector = self._conectores[conector_id]
        except KeyError as ausente:
            raise NaoEncontrado(f"conector:{conector_id}") from ausente
        causas = [
            self.projeto.no(self.projeto.aresta(a).origem_id).titulo
            for a in conector.arestas
        ]
        destino = self.projeto.no(conector.destino_id).titulo
        return f"Se {' e '.join(causas)}, então {destino}"

    def _soltar_das_conjuncoes(self, aresta_id: UUID) -> None:
        """Aresta que some leva junto o conector que a citava — nunca deixa referência órfã."""
        for conector in list(self._conectores.values()):
            if aresta_id in conector.arestas:
                restantes = tuple(a for a in conector.arestas if a != aresta_id)
                if len(restantes) < 2:
                    self._conectores.pop(conector.id)
                else:
                    self._conectores[conector.id] = replace(conector, arestas=restantes)

    # -- análise estrutural --------------------------------------------------------

    def analisar(self, *, em: datetime) -> RelatorioEstrutural:
        """RF-26..RF-31. Não muta o grafo; emite o evento com o resumo quantitativo."""
        examinados = frozenset(
            aresta_id
            for aresta_id, exame in self._exames.items()
            if exame.estado is not EstadoDoExame.NAO_EXAMINADO
        )
        relatorio = analisar_estrutura(
            nos=tuple(n.id for n in self.projeto.nos),
            arestas=self.projeto.arestas,
            udes=self.udes,
            elos_examinados=examinados,
        )
        self._emitir(AnaliseEstruturalGerada, em, resumo=relatorio.resumo())
        return relatorio

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


def novo_projeto_ara(
    *,
    id: UUID,
    dono: DonoDoProjeto,
    nome: str,
    em: datetime,
    descricao_do_problema: str = "",
) -> ProjetoARA:
    """Cria o `Projeto` do M1 já com a ferramenta certa e o embrulha."""
    return ProjetoARA(
        Projeto(
            id=id,
            dono=dono,
            nome=nome,
            ferramenta=FERRAMENTA_ARA,
            descricao_do_problema=descricao_do_problema,
            criado_em=em,
            alterado_em=em,
        )
    )


def reidratar_ara(
    projeto: Projeto,
    *,
    udes: dict[UUID, FichaDeUde],
    status: dict[UUID, StatusDeValidacao],
    pareceres: dict[UUID, list[ParecerDeJulgamento]],
    exames: dict[UUID, Exame],
    conectores: tuple[ConectorE, ...] = (),
) -> ProjetoARA:
    """Monta uma ARA a partir do que estava GRAVADO — sem emitir evento nenhum.

    Carregar não é mutar: se a reidratação emitisse `UdeMarcado`, abrir um projeto
    escreveria história que não aconteceu. Por isso ela não passa pelos métodos de
    mutação, e por isso mora no domínio e não no adaptador: quem sabe montar o agregado é
    o agregado.

    A **validação formal é recalculada**, nunca lida do banco: ela é função pura e
    determinística do texto do nó, e persisti-la criaria uma segunda fonte de verdade que
    envelheceria em silêncio na primeira mudança de versão do léxico.
    """
    ara = ProjetoARA(projeto)
    ara._udes = dict(udes)
    ara._status = dict(status)
    ara._pareceres = {no_id: list(lista) for no_id, lista in pareceres.items()}
    ara._exames = dict(exames)
    ara._conectores = {c.id: c for c in conectores}
    for no_id in ara._udes:
        ara._validacoes[no_id] = validar_formalmente(projeto.no(no_id).titulo)
        ara._pareceres.setdefault(no_id, [])
        ara._status.setdefault(no_id, StatusDeValidacao.PENDENTE)
    return ara
