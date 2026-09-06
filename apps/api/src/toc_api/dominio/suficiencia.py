"""Suficiência causal — o exame de elo e o conector E, de UMA ferramenta para as duas.

Siglas, uma vez neste arquivo: **TOC** — Teoria das Restrições · **ARA** — Árvore da
Realidade Atual (M2) · **ARF** — Árvore da Realidade Futura (M4) · **RF** — requisito
funcional · **RN** — regra de negócio · **M1** — Núcleo de Diagramas Lógicos.

**Por que este módulo existe.** A ARA e a ARF usam a MESMA lógica: a aresta se lê "Se
<causa>, então <efeito>", todo elo carrega um exame de suficiência, e duas ou mais causas
que só produzem o efeito **juntas** viram um conector E. A spec 008 (RF-03) manda a ARF
oferecer isso "sem duplicação de regra", e a decisão 1 do `plan.md` do ciclo 008 diz como:
**pacote extraído, nunca copiado**.

A diferença entre extrair e copiar é medível, e o teste
`tests/dominio/test_suficiencia_compartilhada.py` a mede por **identidade** (`is`), não
por comportamento: duas cópias que ainda não divergiram passam num teste de comportamento
e reprovam num de identidade. É a mesma disciplina do `check-raiz-do-agregado.sh` — a
propriedade tem de ser impossível de perder em silêncio.

O que este módulo **não** faz: guardar estado. Ele não é agregado nem sabe o que é um
projeto. As coleções (`dict` de exames, `dict` de conectores) continuam morando em quem é
raiz — `ProjetoARA` e `ProjetoARF` —, porque quem responde pelas invariantes de referência
é a raiz do agregado. Aqui moram a **regra** e o **vocabulário**; lá mora o estado.

A lógica de **condição necessária** da Árvore de Pré-Requisitos (APR) NÃO está aqui, e a
ausência é a regra RN-05 da spec 008 em forma de módulo: "as duas lógicas não se misturam
no mesmo projeto". A dependência da APR ("precisa existir antes de") mora em
`toc_api.dominio.apr`, sem exame e sem leitura de suficiência — a ferramenta que não
oferece a operação é a ferramenta em que ninguém a usa por engano.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum
from typing import Callable, Iterable, Mapping, MutableMapping, Sequence
from uuid import UUID, uuid4

from .erros import MutacaoRecusada
from .grafo import ArestaCausal


class EstadoDoExame(str, Enum):
    """O exame de suficiência do elo (spec 005, RF-22) — dado de primeira classe."""

    NAO_EXAMINADO = "nao_examinado"
    SUFICIENTE = "suficiente"
    INSUFICIENTE = "insuficiente"
    COM_RESERVA = "com_reserva"


#: Os dois estados em que a reserva escrita é obrigatória: dizer que o elo não fecha sem
#: dizer o que falta é registrar a dúvida e perder o motivo dela.
EXIGEM_RESERVA = (EstadoDoExame.INSUFICIENTE, EstadoDoExame.COM_RESERVA)


@dataclass(frozen=True, slots=True)
class Exame:
    estado: EstadoDoExame = EstadoDoExame.NAO_EXAMINADO
    reserva: str = ""


@dataclass(frozen=True, slots=True)
class ConectorE:
    """Conjunção: "Se A **e** B, então C" — a elipse canônica da TOC (RN-11 da spec 005)."""

    id: UUID
    destino_id: UUID
    arestas: tuple[UUID, ...]


class ConectorInvalido(MutacaoRecusada):
    """RN-11 violada. `regra`: `minimo_duas_arestas`, `destino_unico`, `aresta_ja_conectada`."""

    def __init__(self, regra: str, detalhe: str = "") -> None:
        super().__init__(f"{regra}: {detalhe}" if detalhe else regra)
        self.regra = regra


def exame_de(estado: EstadoDoExame, reserva: str = "") -> Exame:
    """Constrói o exame **já validado**: os dois estados de dúvida exigem a reserva escrita.

    A validação mora aqui, e não no agregado, porque é a mesma nas duas ferramentas — e
    porque uma regra que mora no agregado é uma regra que a próxima ferramenta reescreve.
    """
    estado = EstadoDoExame(estado)
    limpa = (reserva or "").strip()
    if estado in EXIGEM_RESERVA and not limpa:
        raise MutacaoRecusada(
            f"examinar_elo: o estado {estado.value} exige a reserva escrita (RF-22)"
        )
    return Exame(estado=estado, reserva=limpa)


def formar_conector(
    conectores: Mapping[UUID, ConectorE],
    arestas: Sequence[UUID],
    *,
    aresta_de: Callable[[UUID], ArestaCausal],
    conector_id: UUID | None = None,
) -> ConectorE:
    """As três regras nomeadas do conector, sobre os conectores que JÁ existem.

    `aresta_de` é a busca da aresta na raiz do agregado (ela levanta `NaoEncontrado` para
    aresta de outro projeto) — passada como função porque este módulo não conhece
    projeto. É o mesmo motivo de o estado morar na raiz: aqui é a regra, lá é o dono.
    """
    if len(set(arestas)) < 2:
        raise ConectorInvalido(
            "minimo_duas_arestas", "conjunção com uma aresta só não é conjunção"
        )
    alvos = [aresta_de(a) for a in arestas]
    destinos = {a.destino_id for a in alvos}
    if len(destinos) != 1:
        raise ConectorInvalido(
            "destino_unico", "toda aresta do conector aponta para o mesmo destino"
        )
    ja_conectadas = {a for c in conectores.values() for a in c.arestas}
    repetidas = sorted(set(arestas) & ja_conectadas, key=str)
    if repetidas:
        raise ConectorInvalido(
            "aresta_ja_conectada",
            f"a(s) aresta(s) {repetidas} já pertence(m) a um conector",
        )
    return ConectorE(
        id=conector_id or uuid4(), destino_id=destinos.pop(), arestas=tuple(arestas)
    )


def soltar_das_conjuncoes(
    conectores: MutableMapping[UUID, ConectorE], aresta_id: UUID
) -> None:
    """Aresta que some leva junto a citação — e o conector que fica com uma só se dissolve.

    RN-11: "nunca deixa referência órfã". Muta o dicionário que recebeu de propósito: quem
    é dono do estado é a raiz do agregado, e ela chama isto de dentro da própria operação
    de exclusão, na mesma transação lógica.
    """
    for conector in list(conectores.values()):
        if aresta_id in conector.arestas:
            restantes = tuple(a for a in conector.arestas if a != aresta_id)
            if len(restantes) < 2:
                conectores.pop(conector.id)
            else:
                conectores[conector.id] = replace(conector, arestas=restantes)


def leitura_de_suficiencia(origem: str, destino: str) -> str:
    """A frase da ferramenta: montada dos textos ATUAIS, nunca de cópia congelada."""
    return f"Se {origem}, então {destino}"


def leitura_de_conjuncao(causas: Iterable[str], destino: str) -> str:
    """RF-24 da spec 005, reusada pela ARF: "Se A **e** B, então C"."""
    return leitura_de_suficiencia(" e ".join(causas), destino)


__all__ = [
    "EXIGEM_RESERVA",
    "ConectorE",
    "ConectorInvalido",
    "EstadoDoExame",
    "Exame",
    "exame_de",
    "formar_conector",
    "leitura_de_conjuncao",
    "leitura_de_suficiencia",
    "soltar_das_conjuncoes",
]
