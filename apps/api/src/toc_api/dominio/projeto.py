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

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4

from .erros import ArestaInvalida, MutacaoRecusada, NaoEncontrado
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
        self._exigir_ativo("mover_no")
        alvo = self.no(no_id)
        alvo.posicao = posicao
        self._avancar(em)
        self._emitir(NoMovido, em, no_id=no_id)
        return alvo

    def recolher_no(self, no_id: UUID, recolhido: bool, *, em: datetime) -> No:
        self._exigir_ativo("recolher_no")
        alvo = self.no(no_id)
        alvo.recolhido = bool(recolhido)
        self._avancar(em)
        self._emitir(NoRecolhido, em, no_id=no_id, recolhido=alvo.recolhido)
        return alvo

    def excluir_no(self, no_id: UUID, *, em: datetime) -> list[UUID]:
        """Remove o nó e SOMENTE as arestas que o tocam. Devolve o raio (RF-15/RF-16)."""
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
        self._exigir_ativo("editar_aresta")
        alvo = self.aresta(aresta_id)
        alvo.rotulo = _texto(rotulo, campo="rotulo", minimo=0, maximo=LIMITE_ROTULO)
        self._avancar(em)
        self._emitir(ArestaEditada, em, aresta_id=aresta_id)
        return alvo

    def excluir_aresta(self, aresta_id: UUID, *, em: datetime) -> None:
        self._exigir_ativo("excluir_aresta")
        alvo = self.aresta(aresta_id)
        self.arestas = tuple(a for a in self.arestas if a.id != alvo.id)
        self._avancar(em)
        self._emitir(ArestaExcluida, em, aresta_id=alvo.id)

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
