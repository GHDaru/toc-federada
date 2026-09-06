"""Agregado Projeto — a raiz de consistência do M1 (spec 004, `data-model.md`).

Toda mutação de nó ou de aresta entra por aqui. Não existe caminho em que alguém
adicione uma aresta sem passar pelas invariantes, porque quem guarda as coleções é o
agregado e o que ele devolve são tuplas: uma cópia da coleção não é a coleção.

Regras que valem aqui, cada uma nascida de um teste que falhou antes (P4):

- o instante entra como argumento (`em=`), nunca `datetime.now()` — relógio é porta;
- exclusão é SUAVE e reversível, e o conteúdo volta idêntico (invariantes 4 e 5);
- aresta só liga nós **deste** projeto, sem auto-laço e sem par duplicado (RF-20, RN-02,
  RN-03);
- excluir nó remove exatamente o nó e as arestas incidentes — o teste que teria pego o
  filtro invertido de `tocbuilderv3/services/mockApiService.ts:521`, que apagava todos os
  nós **menos** o excluído (spec 004, F-06 e RF-16);
- projeto excluído recusa toda mutação que não seja restauração (invariante 4).

**Ciclo causal**: o núcleo *detecta* (`criaria_ciclo`, `ciclos`) e **não proíbe**. A
proibição contradiria duas linhas de spec escritas com motivo: a RN-03 do ciclo 004
("a mesma dupla de nós pode ter arestas nos dois sentidos — laços de reforço são
legítimos na TOC") e o RF-29 do ciclo 005 ("QUANDO houver ciclo, O SISTEMA DEVE listá-lo
com seus nós — laços de reforço são legítimos na TOC — e DEVE excluí-los do cálculo de
causa raiz candidata"). Quem decide o que fazer com um ciclo é a ferramenta, com a
resposta que o núcleo dá.
"""
from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Iterator
from uuid import UUID, uuid4

from .erros import (
    ArestaInvalida,
    MutacaoForaDaRaiz,
    MutacaoRecusada,
    NaoEncontrado,
)
from .eventos import (
    ArestaEditada,
    ArestaExcluida,
    ArestaLigada,
    EventoDeDominio,
    MetadadosEditados,
    NoAdicionado,
    NoEditado,
    NoExcluido,
    NoMovido,
    NoRecolhido,
    ProjetoExcluido,
    ProjetoRestaurado,
)
from .grafo import ArestaCausal, No, alcanca, ciclos, sucessores
from .identidade import DonoDoProjeto
from .valores import (
    FERRAMENTA_GENERICA,
    LIMITE_DESCRICAO,
    LIMITE_ROTULO,
    LIMITE_TIPO,
    TIPO_DE_NO_PADRAO,
    PosicaoNoCanvas,
    texto,
)

LIMITE_NOME = 200

#: `ferramenta → nome da raiz de agregado que governa o grafo dela`.
#:
#: **Por que existe, e por que a segurança NÃO depende dela.** O `Projeto` é o núcleo do
#: M1 (Núcleo de Diagramas Lógicos) e não conhece semântica da Teoria das Restrições
#: (TOC) — é a RN-04 da spec 004, e é ela que impede a sétima cópia de canvas. Então o
#: núcleo não pode importar `ProjetoARA` nem `NuvemDeConflito` para saber quem o governa.
#: O que ele sabe é mais simples e mais forte: **um projeto cuja ferramenta não é a
#: genérica pertence a alguma raiz**, e o grafo dele só muda por dentro dela. Este mapa
#: só empresta o NOME da raiz para a mensagem de recusa; uma ferramenta nova que esqueça
#: de se registrar fica **bloqueada**, nunca liberada. Fail-closed por construção.
RAIZ_POR_FERRAMENTA: dict[str, str] = {}


def registrar_raiz_de_ferramenta(ferramenta: str, raiz: str) -> None:
    """Cada raiz de ferramenta se anuncia ao ser importada (M2 em `ara`, M3 em `nuvem`)."""
    RAIZ_POR_FERRAMENTA[ferramenta] = raiz


def raiz_da_ferramenta(ferramenta: str) -> str:
    """O nome da raiz que governa a ferramenta — ou uma descrição, se ela não se registrou."""
    return RAIZ_POR_FERRAMENTA.get(ferramenta, f"a raiz da ferramenta {ferramenta!r}")


def tem_raiz_propria(ferramenta: str) -> bool:
    """Toda ferramenta que não é a genérica tem raiz própria. É a regra, não a exceção."""
    return ferramenta != FERRAMENTA_GENERICA


class EstadoDoProjeto(str, Enum):
    ATIVO = "ativo"
    EXCLUIDO = "excluido"


def _texto(valor: str, *, campo: str, minimo: int, maximo: int) -> str:
    return texto(valor, campo=campo, minimo=minimo, maximo=maximo)


@dataclass(slots=True)
class Projeto:
    id: UUID
    dono: DonoDoProjeto
    nome: str
    criado_em: datetime
    alterado_em: datetime
    ferramenta: str = FERRAMENTA_GENERICA
    descricao_do_problema: str = ""
    versao: int = 1
    excluido_em: datetime | None = field(default=None)
    nos: tuple[No, ...] = ()
    arestas: tuple[ArestaCausal, ...] = ()
    eventos: tuple[EventoDeDominio, ...] = ()
    #: Profundidade da entrada pela raiz da ferramenta. NÃO é estado de negócio: não
    #: entra no construtor, não é comparado, não é persistido e vale zero em todo
    #: agregado que volta do banco. É o contador do `sob_a_raiz`, e é contador (e não
    #: booleano) porque uma raiz chama outra operação sua por dentro.
    _profundidade_da_raiz: int = field(default=0, init=False, repr=False, compare=False)
    #: A versão que este agregado tinha **no banco** quando foi lido. `0` = nunca foi
    #: gravado. É a base da trava otimista, e existe porque `versao` sozinha não serve:
    #: ela é incrementada em memória a cada mutação, então na hora de gravar já não é
    #: mais o número contra o qual o `WHERE` tem de casar. Sem este campo o adaptador
    #: não teria como condicionar a escrita — que é exatamente por que a coluna `versao`
    #: existia, era incrementada, e não protegia nada.
    #:
    #: Não é comparado nem entra no construtor pelo mesmo motivo do contador acima: é
    #: estado de SINCRONIA com o repositório, não estado de negócio. Quem o preenche é o
    #: adaptador, ao reidratar (`versao_lida = <coluna>`) e ao confirmar uma gravação
    #: (`confirmar_gravacao()`).
    versao_lida: int = field(default=0, init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        self.nome = _texto(self.nome, campo="nome", minimo=1, maximo=LIMITE_NOME)
        self.descricao_do_problema = _texto(
            self.descricao_do_problema, campo="descricao_do_problema",
            minimo=0, maximo=LIMITE_DESCRICAO,
        )
        self.ferramenta = _texto(
            self.ferramenta, campo="ferramenta", minimo=1, maximo=LIMITE_TIPO
        )
        self.nos = tuple(self.nos)
        self.arestas = tuple(self.arestas)
        self.eventos = tuple(self.eventos)

    # -- consultas ---------------------------------------------------------------

    @property
    def estado(self) -> EstadoDoProjeto:
        return EstadoDoProjeto.EXCLUIDO if self.excluido_em else EstadoDoProjeto.ATIVO

    def no(self, no_id: UUID) -> No:
        for candidato in self.nos:
            if candidato.id == no_id:
                return candidato
        raise NaoEncontrado(f"no:{no_id}")

    def aresta(self, aresta_id: UUID) -> ArestaCausal:
        for candidata in self.arestas:
            if candidata.id == aresta_id:
                return candidata
        raise NaoEncontrado(f"aresta:{aresta_id}")

    def tem_no(self, no_id: UUID) -> bool:
        return any(candidato.id == no_id for candidato in self.nos)

    def arestas_incidentes(self, no_id: UUID) -> tuple[ArestaCausal, ...]:
        """Toda aresta que toca o nó — como origem OU como destino (o raio do RF-15)."""
        return tuple(
            a for a in self.arestas if no_id in (a.origem_id, a.destino_id)
        )

    def criaria_ciclo(self, origem_id: UUID, destino_id: UUID) -> bool:
        """A aresta origem→destino fecharia um ciclo? Consulta, não proibição."""
        return origem_id == destino_id or origem_id in alcanca(
            destino_id, sucessores(self.arestas)
        )

    def ciclos(self) -> list[tuple[UUID, ...]]:
        return ciclos(tuple(n.id for n in self.nos), self.arestas)

    # -- a raiz do agregado é o único caminho para o grafo ------------------------

    @contextmanager
    def sob_a_raiz(self) -> Iterator["Projeto"]:
        """A chave da raiz da ferramenta. **Só o domínio a usa** — há portão para isso.

        `ProjetoARA` e `NuvemDeConflito` contêm este `Projeto` e acrescentam invariantes
        que ele não conhece. Enquanto qualquer chamador podia mutar o grafo direto,
        existiam duas portas para o mesmo estado e as invariantes moravam numa só — o
        agregado com porta dos fundos. Aqui a porta dos fundos não é fechada por um `if`
        na borda: ela deixa de existir, porque quem guarda o grafo passa a exigir a raiz.

        Quem chama isto de fora de `toc_api.dominio` está reabrindo o defeito, e
        `scripts/check-raiz-do-agregado.sh` reprova.
        """
        self._profundidade_da_raiz += 1
        try:
            yield self
        finally:
            self._profundidade_da_raiz -= 1

    def _exigir_raiz(self, operacao: str) -> None:
        """Recusa toda mutação de grafo que não venha de dentro da raiz da ferramenta.

        A genérica (`generico`) não tem raiz acima dela: nela o `Projeto` **é** a raiz, e
        é por isso que o M1 não perde nada. Toda outra ferramenta é bloqueada por padrão,
        registrada ou não — a ferramenta nova nasce fechada e se abre ao passar a
        delegar por `sob_a_raiz`.
        """
        if self._profundidade_da_raiz or not tem_raiz_propria(self.ferramenta):
            return
        raise MutacaoForaDaRaiz(
            operacao, self.ferramenta, raiz_da_ferramenta(self.ferramenta)
        )

    # -- mutações de metadados ---------------------------------------------------

    def renomear(self, nome: str, *, em: datetime) -> None:
        self._exigir_ativo("renomear")
        self.nome = _texto(nome, campo="nome", minimo=1, maximo=LIMITE_NOME)
        self._avancar(em)
        self._emitir(MetadadosEditados, em, campo="nome")

    def descrever_problema(self, descricao: str, *, em: datetime) -> None:
        self._exigir_ativo("descrever_problema")
        self.descricao_do_problema = _texto(
            descricao, campo="descricao_do_problema", minimo=0, maximo=LIMITE_DESCRICAO
        )
        self._avancar(em)
        self._emitir(MetadadosEditados, em, campo="descricao_do_problema")

    def excluir(self, *, em: datetime) -> None:
        """Exclusão suave: o conteúdo fica, o estado muda (spec 004, RF-06)."""
        self._exigir_ativo("excluir")
        self.excluido_em = em
        self._avancar(em)
        self._emitir(ProjetoExcluido, em)

    def restaurar(self, *, em: datetime) -> None:
        if self.estado is EstadoDoProjeto.ATIVO:
            raise MutacaoRecusada("restaurar: o projeto já está ativo")
        self.excluido_em = None
        self._avancar(em)
        self._emitir(ProjetoRestaurado, em)

    # -- mutações de nó ----------------------------------------------------------

    def adicionar_no(
        self,
        *,
        titulo: str,
        em: datetime,
        descricao: str = "",
        tipo: str = TIPO_DE_NO_PADRAO,
        posicao: PosicaoNoCanvas | None = None,
        no_id: UUID | None = None,
    ) -> No:
        self._exigir_raiz("adicionar_no")
        self._exigir_ativo("adicionar_no")
        novo = No(
            id=no_id or uuid4(),
            titulo=titulo,
            descricao=descricao,
            tipo=tipo,
            posicao=posicao or PosicaoNoCanvas(),
        )
        if self.tem_no(novo.id):
            raise MutacaoRecusada(f"adicionar_no: id repetido {novo.id}")
        self.nos = self.nos + (novo,)
        self._avancar(em)
        self._emitir(NoAdicionado, em, no_id=novo.id, tipo=novo.tipo)
        return novo

    def editar_no(
        self,
        no_id: UUID,
        *,
        em: datetime,
        titulo: str | None = None,
        descricao: str | None = None,
    ) -> No:
        self._exigir_raiz("editar_no")
        self._exigir_ativo("editar_no")
        alvo = self.no(no_id)
        campos: list[str] = []
        if titulo is not None:
            alvo.titulo = _texto(titulo, campo="titulo", minimo=1, maximo=LIMITE_NOME)
            campos.append("titulo")
        if descricao is not None:
            alvo.descricao = _texto(
                descricao, campo="descricao", minimo=0, maximo=LIMITE_DESCRICAO
            )
            campos.append("descricao")
        if not campos:
            raise MutacaoRecusada("editar_no: nenhum campo informado")
        self._avancar(em)
        self._emitir(NoEditado, em, no_id=no_id, campos=tuple(campos))
        return alvo

    def mover_no(self, no_id: UUID, posicao: PosicaoNoCanvas, *, em: datetime) -> No:
        self._exigir_raiz("mover_no")
        self._exigir_ativo("mover_no")
        alvo = self.no(no_id)
        alvo.posicao = posicao
        self._avancar(em)
        self._emitir(NoMovido, em, no_id=no_id)
        return alvo

    def recolher_no(self, no_id: UUID, recolhido: bool, *, em: datetime) -> No:
        self._exigir_raiz("recolher_no")
        self._exigir_ativo("recolher_no")
        alvo = self.no(no_id)
        alvo.recolhido = bool(recolhido)
        self._avancar(em)
        self._emitir(NoRecolhido, em, no_id=no_id, recolhido=alvo.recolhido)
        return alvo

    def excluir_no(self, no_id: UUID, *, em: datetime) -> list[UUID]:
        """Remove o nó e SOMENTE as arestas que o tocam. Devolve o raio (RF-15/RF-16)."""
        self._exigir_raiz("excluir_no")
        self._exigir_ativo("excluir_no")
        alvo = self.no(no_id)
        removidas = [a.id for a in self.arestas_incidentes(alvo.id)]
        self.nos = tuple(n for n in self.nos if n.id != alvo.id)
        self.arestas = tuple(a for a in self.arestas if a.id not in set(removidas))
        self._avancar(em)
        self._emitir(
            NoExcluido, em, no_id=alvo.id, arestas_removidas=tuple(removidas)
        )
        return removidas

    # -- mutações de aresta ------------------------------------------------------

    def ligar(
        self,
        origem_id: UUID,
        destino_id: UUID,
        *,
        em: datetime,
        rotulo: str = "",
        aresta_id: UUID | None = None,
    ) -> ArestaCausal:
        self._exigir_raiz("ligar")
        self._exigir_ativo("ligar")
        if not (self.tem_no(origem_id) and self.tem_no(destino_id)):
            raise ArestaInvalida(
                "pontas_no_projeto",
                "origem e destino têm de ser nós deste projeto",
            )
        if origem_id == destino_id:
            raise ArestaInvalida("sem_auto_laco", "um nó não pode causar a si mesmo")
        if any(a.par == (origem_id, destino_id) for a in self.arestas):
            raise ArestaInvalida(
                "sem_duplicata", "já existe uma aresta deste par origem→destino"
            )
        nova = ArestaCausal(
            id=aresta_id or uuid4(),
            origem_id=origem_id,
            destino_id=destino_id,
            rotulo=rotulo,
        )
        self.arestas = self.arestas + (nova,)
        self._avancar(em)
        self._emitir(
            ArestaLigada,
            em,
            aresta_id=nova.id,
            origem_id=origem_id,
            destino_id=destino_id,
        )
        return nova

    def editar_aresta(self, aresta_id: UUID, rotulo: str, *, em: datetime) -> ArestaCausal:
        self._exigir_raiz("editar_aresta")
        self._exigir_ativo("editar_aresta")
        alvo = self.aresta(aresta_id)
        alvo.rotulo = _texto(rotulo, campo="rotulo", minimo=0, maximo=LIMITE_ROTULO)
        self._avancar(em)
        self._emitir(ArestaEditada, em, aresta_id=aresta_id)
        return alvo

    def excluir_aresta(self, aresta_id: UUID, *, em: datetime) -> None:
        self._exigir_raiz("excluir_aresta")
        self._exigir_ativo("excluir_aresta")
        alvo = self.aresta(aresta_id)
        self.arestas = tuple(a for a in self.arestas if a.id != alvo.id)
        self._avancar(em)
        self._emitir(ArestaExcluida, em, aresta_id=alvo.id)

    # -- sincronia com o repositório ---------------------------------------------

    def confirmar_gravacao(self) -> None:
        """A gravação passou: a versão em memória passa a ser a versão do banco.

        Chamado pelo adaptador DEPOIS do commit, nunca antes — confirmar uma escrita que
        ainda pode falhar deixaria o agregado achando que está sincronizado com um banco
        que não recebeu nada, e a próxima gravação passaria por cima de trabalho alheio
        com a bênção da trava.
        """
        self.versao_lida = self.versao

    # -- eventos -----------------------------------------------------------------

    def drenar_eventos(self) -> list[EventoDeDominio]:
        """Entrega os eventos acumulados e zera a fila. Ninguém os reescreve nem apaga."""
        drenados = list(self.eventos)
        self.eventos = ()
        return drenados

    # -- internos ----------------------------------------------------------------

    def _emitir(self, classe, em: datetime, **carga) -> None:
        self.eventos = self.eventos + (
            classe(projeto_id=self.id, dono=self.dono, instante=em, **carga),
        )

    def _exigir_ativo(self, operacao: str) -> None:
        if self.estado is EstadoDoProjeto.EXCLUIDO:
            raise MutacaoRecusada(f"{operacao}: o projeto está excluído")

    def _avancar(self, em: datetime) -> None:
        self.versao += 1
        self.alterado_em = em
