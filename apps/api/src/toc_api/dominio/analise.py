"""Análise estrutural da árvore — leitura pura do grafo (spec 005, RF-26..RF-31).

O prompt `ANALYZE_TREE_PROMPT_TEXT` da linhagem (`tocbuilderv3/constants.ts:83-107`)
pedia a um modelo de linguagem coisas que são leitura de grafo: fragmentos, nós soltos, o
que não leva a Efeito Indesejável (UDE) nenhum, conexões prováveis. Deste conjunto, tudo o
que é **estrutural** é computável sem rede e sem modelo — e é isto. O que sobra
(interpretação, elo fraco, redundância provável) continua sendo julgamento e vira ação do
catálogo governado no ciclo 006.

Nada aqui muta coisa nenhuma: entra grafo, sai relatório.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from uuid import UUID

from .grafo import ArestaCausal, alcanca, ciclos, sucessores


@dataclass(frozen=True, slots=True)
class AlcanceDeEntrada:
    """Quanto da dor percebida esta entrada explica (RF-26)."""

    no_id: UUID
    udes_alcancados: tuple[UUID, ...]
    fracao: float


@dataclass(frozen=True, slots=True)
class RelatorioEstrutural:
    fragmentos: tuple[tuple[UUID, ...], ...] = ()
    entradas: tuple[UUID, ...] = ()
    alcances: tuple[AlcanceDeEntrada, ...] = ()
    udes_nao_alcancados: tuple[UUID, ...] = ()
    elos_nao_examinados: tuple[UUID, ...] = ()
    orfaos: tuple[UUID, ...] = ()
    ciclos: tuple[tuple[UUID, ...], ...] = ()
    nos_em_ciclo: frozenset[UUID] = frozenset()
    causas_raiz_candidatas: tuple[UUID, ...] = ()
    observacoes: tuple[str, ...] = ()
    total_de_nos: int = 0
    total_de_udes: int = 0

    @property
    def causa_raiz_candidata(self) -> UUID | None:
        """A entrada de maior alcance — **só** quando ela é única (RN-12).

        Empate não vira conclusão automática: o relatório lista as candidatas e o humano
        conclui. "O sistema aponta, o humano conclui" é a regra escrita; devolver a
        primeira de uma lista empatada seria concluir escondido.
        """
        unica = self.causas_raiz_candidatas
        return unica[0] if len(unica) == 1 else None

    def resumo(self) -> dict:
        """O resumo quantitativo do RF-31 — o que entra no evento e no traço."""
        return {
            "nos": self.total_de_nos,
            "udes": self.total_de_udes,
            "fragmentos": len(self.fragmentos),
            "entradas": len(self.entradas),
            "orfaos": len(self.orfaos),
            "ciclos": len(self.ciclos),
            "elos_nao_examinados": len(self.elos_nao_examinados),
            "udes_nao_alcancados": len(self.udes_nao_alcancados),
            "causas_raiz_candidatas": len(self.causas_raiz_candidatas),
        }


def _fragmentos(
    ids: tuple[UUID, ...], arestas: tuple[ArestaCausal, ...]
) -> tuple[tuple[UUID, ...], ...]:
    """Componentes conexos ignorando a direção — dois fragmentos são duas conversas."""
    vizinhos: dict[UUID, set[UUID]] = {i: set() for i in ids}
    for aresta in arestas:
        if aresta.origem_id in vizinhos and aresta.destino_id in vizinhos:
            vizinhos[aresta.origem_id].add(aresta.destino_id)
            vizinhos[aresta.destino_id].add(aresta.origem_id)
    vistos: set[UUID] = set()
    achados: list[tuple[UUID, ...]] = []
    for identificador in ids:
        if identificador in vistos:
            continue
        pilha, componente = [identificador], []
        vistos.add(identificador)
        while pilha:
            atual = pilha.pop()
            componente.append(atual)
            for vizinho in vizinhos[atual]:
                if vizinho not in vistos:
                    vistos.add(vizinho)
                    pilha.append(vizinho)
        achados.append(tuple(sorted(componente, key=str)))
    return tuple(sorted(achados, key=lambda c: (len(c), tuple(str(x) for x in c))))


def analisar_estrutura(
    *,
    nos: tuple[UUID, ...],
    arestas: tuple[ArestaCausal, ...],
    udes: frozenset[UUID],
    elos_examinados: frozenset[UUID],
) -> RelatorioEstrutural:
    """A leitura inteira, numa passada. Pura: entra grafo, sai relatório."""
    validas = tuple(
        a for a in arestas if a.origem_id in set(nos) and a.destino_id in set(nos)
    )
    com_antecessor = {a.destino_id for a in validas}
    tocados = {a.origem_id for a in validas} | com_antecessor

    entradas = tuple(n for n in nos if n not in com_antecessor)
    orfaos = tuple(n for n in nos if n not in tocados)
    lacos = tuple(ciclos(nos, validas))
    em_ciclo = frozenset(n for laco in lacos for n in laco)

    saida = sucessores(validas)
    total_de_udes = len([n for n in nos if n in udes])
    alcances = []
    for entrada in entradas:
        # `incluir_partida=False` de propósito: uma entrada não explica a si mesma. Com
        # a partida incluída, um efeito indesejável SOLTO (entrada e destino ao mesmo
        # tempo) apareceria como "alcançado" e sumiria da lista do RF-28 — que é
        # exatamente a lista do que a árvore ainda NÃO explica.
        atingidos = tuple(
            sorted((alcanca(entrada, saida) & udes), key=str)
        )
        alcances.append(
            AlcanceDeEntrada(
                no_id=entrada,
                udes_alcancados=atingidos,
                fracao=(len(atingidos) / total_de_udes) if total_de_udes else 0.0,
            )
        )

    alcancados = {u for a in alcances for u in a.udes_alcancados}
    nao_alcancados = tuple(n for n in nos if n in udes and n not in alcancados)

    # RF-29: os nós de ciclo saem do cálculo da causa raiz candidata, e o relatório DIZ
    # isso — esconder a exclusão seria a mesma coisa que concluir sem mostrar a conta.
    elegiveis = [a for a in alcances if a.no_id not in em_ciclo and a.udes_alcancados]
    melhor = max((a.fracao for a in elegiveis), default=0.0)
    candidatas = tuple(
        sorted((a.no_id for a in elegiveis if a.fracao == melhor), key=str)
    )

    observacoes: list[str] = []
    if lacos:
        observacoes.append(
            f"{len(lacos)} ciclo(s) causal(is) encontrado(s): laço de reforço é legítimo "
            "na Teoria das Restrições, e os nós que participam deles ficam FORA do "
            "cálculo da causa raiz candidata (RF-29)."
        )
    if len(candidatas) > 1:
        observacoes.append(
            f"{len(candidatas)} entradas empatam no alcance sobre os efeitos "
            "indesejáveis: o relatório aponta as candidatas e não escolhe (RN-12)."
        )
    if nao_alcancados:
        observacoes.append(
            f"{len(nao_alcancados)} efeito(s) indesejável(is) não são alcançados por "
            "entrada nenhuma — é a medida do que a árvore ainda não explica (RF-28)."
        )

    return RelatorioEstrutural(
        fragmentos=_fragmentos(nos, validas),
        entradas=entradas,
        alcances=tuple(alcances),
        udes_nao_alcancados=nao_alcancados,
        elos_nao_examinados=tuple(a.id for a in arestas if a.id not in elos_examinados),
        orfaos=orfaos,
        ciclos=lacos,
        nos_em_ciclo=em_ciclo,
        causas_raiz_candidatas=candidatas,
        observacoes=tuple(observacoes),
        total_de_nos=len(nos),
        total_de_udes=total_de_udes,
    )
