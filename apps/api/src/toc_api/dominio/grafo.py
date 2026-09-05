"""Nó e aresta causal — as entidades internas do agregado Projeto (spec 004).

São **entidades** e não objetos de valor porque têm identidade própria: dois nós com o
mesmo título continuam sendo dois nós. Elas não se validam contra o projeto — quem
conhece o projeto inteiro é o agregado, e é lá que moram as invariantes de referência
(`toc_api.dominio.projeto`). Aqui mora só o que é verdade sobre a entidade sozinha.

`ArestaCausal` é dirigida e lê-se **"Se origem, então destino"** — a semântica de
suficiência que todas as ferramentas da Teoria das Restrições (TOC) herdam (spec 004,
RN-01; a leitura está na linhagem, `tocbuilderv3/APLICATION_PURPOSE.md:24`).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from uuid import UUID

from .valores import (
    LIMITE_DESCRICAO,
    LIMITE_ROTULO,
    LIMITE_TIPO,
    LIMITE_TITULO,
    TIPO_DE_NO_PADRAO,
    PosicaoNoCanvas,
    texto,
)


@dataclass(slots=True)
class No:
    """Uma caixa do diagrama. `tipo` é enum extensível: o M1 só conhece `generico`."""

    id: UUID
    titulo: str
    descricao: str = ""
    tipo: str = TIPO_DE_NO_PADRAO
    posicao: PosicaoNoCanvas = field(default_factory=PosicaoNoCanvas)
    recolhido: bool = False

    def __post_init__(self) -> None:
        self.titulo = texto(self.titulo, campo="titulo", minimo=1, maximo=LIMITE_TITULO)
        self.descricao = texto(
            self.descricao, campo="descricao", minimo=0, maximo=LIMITE_DESCRICAO
        )
        self.tipo = texto(self.tipo, campo="tipo", minimo=1, maximo=LIMITE_TIPO)


@dataclass(slots=True)
class ArestaCausal:
    """Dirigida: origem → destino. Lê-se "Se origem, então destino"."""

    id: UUID
    origem_id: UUID
    destino_id: UUID
    rotulo: str = ""

    def __post_init__(self) -> None:
        self.rotulo = texto(self.rotulo, campo="rotulo", minimo=0, maximo=LIMITE_ROTULO)

    @property
    def par(self) -> tuple[UUID, UUID]:
        return (self.origem_id, self.destino_id)


def sucessores(arestas: tuple[ArestaCausal, ...]) -> dict[UUID, list[UUID]]:
    """Lista de adjacência origem → destinos. Função pura, usada pela análise do M2."""
    saida: dict[UUID, list[UUID]] = {}
    for aresta in arestas:
        saida.setdefault(aresta.origem_id, []).append(aresta.destino_id)
    return saida


def alcanca(
    partida: UUID, saida: dict[UUID, list[UUID]], *, incluir_partida: bool = False
) -> set[UUID]:
    """Fecho transitivo a partir de um nó. Suporta ciclo sem entrar em recursão infinita."""
    vistos: set[UUID] = set()
    pilha = list(saida.get(partida, []))
    while pilha:
        atual = pilha.pop()
        if atual in vistos:
            continue
        vistos.add(atual)
        pilha.extend(saida.get(atual, []))
    if incluir_partida:
        vistos.add(partida)
    return vistos


def ciclos(
    ids: tuple[UUID, ...], arestas: tuple[ArestaCausal, ...]
) -> list[tuple[UUID, ...]]:
    """Todos os ciclos elementares alcançados por busca em profundidade.

    Mesma marcação de cinza do `docs/produto/dados/medir-base.py` (`visita`, linha 383):
    nó em processamento é cinza, e reencontrá-lo fecha um ciclo. Devolve a sequência de
    nós do ciclo **sem** repetir o nó de fechamento, normalizada para começar sempre pelo
    mesmo elemento — assim o mesmo ciclo descoberto por caminhos diferentes é um só.
    """
    saida = sucessores(arestas)
    cor: dict[UUID, int] = {i: 0 for i in ids}
    achados: set[tuple[UUID, ...]] = set()

    def visita(no: UUID, pilha: list[UUID]) -> None:
        cor[no] = 1
        pilha.append(no)
        for destino in saida.get(no, []):
            if cor.get(destino) == 1:
                trecho = pilha[pilha.index(destino) :]
                giro = trecho.index(min(trecho, key=str))
                achados.add(tuple(trecho[giro:] + trecho[:giro]))
            elif cor.get(destino, 0) == 0:
                visita(destino, pilha)
        pilha.pop()
        cor[no] = 2

    for identificador in ids:
        if cor.get(identificador, 0) == 0:
            visita(identificador, [])
    return sorted(achados, key=lambda c: tuple(str(x) for x in c))
