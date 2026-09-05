"""O ResultadoDeGeracao — a forma que a assistência devolve, validada por esquema.

Siglas, uma vez neste arquivo: **NC** — Nuvem de Conflito · **TOC** — Teoria das
Restrições · **IA** — inteligência artificial · **JSON** — *JavaScript Object Notation* ·
**TRIZ** — Teoria da Resolução Inventiva de Problemas · **FSM** — máquina de estados
finitos · **SDK** — *Software Development Kit*.

**O contraexemplo é medido, e é a razão deste módulo existir.** Na 4ª geração da linhagem
a nuvem era arrancada da resposta do modelo por expressão regular sobre texto: 5 extrações
de entidade e 7 pares premissa/solução em `tocbuilderv3/services/parserService.ts`, com um
`catch` que devolvia `null` **inteiro** a qualquer variação de formato (l.67). O melhor
recurso da ferramenta quebrava pela **forma** do texto, não pelo conteúdo — e a origem
disso está uma camada acima: `services/geminiService.ts:173` devolvia
`{ markdown: textResponse }`, isto é, geração sem contrato nenhum.

Aqui a forma é contrato:

1. a assistência devolve **estrutura** (a porta `MotorDeGeracaoDeNuvem` entrega
   `Mapping`, nunca texto para interpretar);
2. a estrutura é validada contra `ESQUEMA_DO_RESULTADO`, **versionado**, pelo mesmo
   validador do catálogo (§A.5 do Anexo A) — palavra desconhecida não passa em silêncio;
3. o que não valida é recusado em **falha fechada**, antes de a proposta existir (RF-22),
   com código estável para a borda traduzir sem ler mensagem;
4. versão fora de `VERSOES_SUPORTADAS` é recusa própria (RF-29): evoluir o esquema é
   mudança de contrato com teste, nunca afrouxamento do parse.

Nenhuma linha deste módulo interpreta texto livre — e há teste que confere isso lendo o
próprio fonte.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from .erros import DadoInvalido
from .federacao.esquema import ArgumentosInvalidos, validar_contra_esquema
from .nuvem import (
    LIMITE_INJECAO,
    LIMITE_PREMISSA,
    LIMITE_RACIONAL,
    LIMITE_TEXTO_DE_ENTIDADE,
    ChaveDaAresta,
    PapelDaEntidade,
    SeparacaoTRIZ,
)

VERSAO_DO_RESULTADO = "1.0.0"
VERSOES_SUPORTADAS: tuple[str, ...] = (VERSAO_DO_RESULTADO,)

#: Teto de premissas por aresta e de injeções por premissa numa geração. Não é desempenho:
#: é o que impede uma resposta de modelo de encher a nuvem de conteúdo que ninguém revisa.
MAXIMO_DE_PREMISSAS_POR_ARESTA = 10
MAXIMO_DE_INJECOES_POR_PREMISSA = 10

_ESQUEMA_DE_INJECAO: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["texto"],
    "properties": {
        "texto": {"type": "string", "minLength": 1, "maxLength": LIMITE_INJECAO},
        "separacao": {"type": "string", "enum": [s.value for s in SeparacaoTRIZ]},
    },
}

_ESQUEMA_DE_PREMISSA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["texto"],
    "properties": {
        "texto": {"type": "string", "minLength": 1, "maxLength": LIMITE_PREMISSA},
        "injecoes": {
            "type": "array",
            "maxItems": MAXIMO_DE_INJECOES_POR_PREMISSA,
            "items": _ESQUEMA_DE_INJECAO,
        },
    },
}

_LISTA_DE_PREMISSAS: dict[str, Any] = {
    "type": "array",
    "maxItems": MAXIMO_DE_PREMISSAS_POR_ARESTA,
    "items": _ESQUEMA_DE_PREMISSA,
}

#: O esquema versionado do resultado (RF-21, RF-29). As 5 entidades e as 7 chaves de
#: aresta são **obrigatórias**: a nuvem é de topologia fixa, e resultado parcial não é
#: nuvem — é a metade que a interface teria de completar adivinhando.
ESQUEMA_DO_RESULTADO: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["versao", "entidades", "arestas"],
    "properties": {
        "versao": {"type": "string", "enum": list(VERSOES_SUPORTADAS)},
        "racional": {"type": "string", "maxLength": LIMITE_RACIONAL},
        "entidades": {
            "type": "object",
            "additionalProperties": False,
            "required": [p.value for p in PapelDaEntidade],
            "properties": {
                p.value: {
                    "type": "string",
                    "minLength": 1,
                    "maxLength": LIMITE_TEXTO_DE_ENTIDADE,
                }
                for p in PapelDaEntidade
            },
        },
        "arestas": {
            "type": "object",
            "additionalProperties": False,
            "required": [c.value for c in ChaveDaAresta],
            "properties": {c.value: _LISTA_DE_PREMISSAS for c in ChaveDaAresta},
        },
    },
}


class ResultadoDeGeracaoInvalido(DadoInvalido):
    """Falha fechada (RF-22). `codigo` é estável; a mensagem é para gente, não para código.

    Códigos: `VERSAO_DESCONHECIDA` (RF-29) · `FORA_DO_ESQUEMA` (o validador recusou) ·
    `NAO_E_OBJETO` (veio outra coisa no lugar de um objeto).
    """

    def __init__(self, codigo: str, detalhe: str) -> None:
        super().__init__(f"{codigo}: {detalhe}")
        self.codigo = codigo
        self.detalhe = detalhe


@dataclass(frozen=True, slots=True)
class InjecaoProposta:
    texto: str
    separacao: SeparacaoTRIZ | None = None


@dataclass(frozen=True, slots=True)
class PremissaProposta:
    texto: str
    injecoes: tuple[InjecaoProposta, ...] = ()


@dataclass(frozen=True, slots=True)
class ResultadoDeGeracao:
    """A nuvem proposta, tipada. Só existe se tiver validado — não há construtor frouxo."""

    versao: str
    entidades: Mapping[PapelDaEntidade, str]
    premissas: Mapping[ChaveDaAresta, tuple[PremissaProposta, ...]]
    racional: str = ""

    @classmethod
    def de_dicionario(cls, bruto: Any) -> "ResultadoDeGeracao":
        """Valida e tipa. **Toda** entrada de conteúdo de modelo passa por aqui (RN-05)."""
        if not isinstance(bruto, Mapping):
            raise ResultadoDeGeracaoInvalido(
                "NAO_E_OBJETO",
                f"o resultado da geração é um objeto; veio {type(bruto).__name__}",
            )
        versao = bruto.get("versao")
        if not isinstance(versao, str) or versao not in VERSOES_SUPORTADAS:
            raise ResultadoDeGeracaoInvalido(
                "VERSAO_DESCONHECIDA",
                f"versão {versao!r} fora das suportadas {list(VERSOES_SUPORTADAS)}; "
                "evoluir o esquema é mudança de contrato, com teste",
            )
        try:
            validar_contra_esquema(dict(bruto), ESQUEMA_DO_RESULTADO)
        except ArgumentosInvalidos as recusa:
            raise ResultadoDeGeracaoInvalido("FORA_DO_ESQUEMA", str(recusa)) from recusa

        entidades = {
            PapelDaEntidade(papel): str(texto)
            for papel, texto in bruto["entidades"].items()
        }
        premissas = {
            ChaveDaAresta(chave): tuple(
                PremissaProposta(
                    texto=str(item["texto"]),
                    injecoes=tuple(
                        InjecaoProposta(
                            texto=str(injecao["texto"]),
                            separacao=(
                                SeparacaoTRIZ(injecao["separacao"])
                                if injecao.get("separacao")
                                else None
                            ),
                        )
                        for injecao in item.get("injecoes") or ()
                    ),
                )
                for item in lista
            )
            for chave, lista in bruto["arestas"].items()
        }
        return cls(
            versao=versao,
            entidades=entidades,
            premissas=premissas,
            racional=str(bruto.get("racional") or ""),
        )

    def como_dicionario(self) -> dict[str, Any]:
        """A ida e volta é sem perda — é o que a pré-visualização em diff consome (RI-06)."""
        saida: dict[str, Any] = {
            "versao": self.versao,
            "entidades": {p.value: t for p, t in self.entidades.items()},
            "arestas": {
                chave.value: [
                    {
                        "texto": premissa.texto,
                        **(
                            {
                                "injecoes": [
                                    {
                                        "texto": injecao.texto,
                                        **(
                                            {"separacao": injecao.separacao.value}
                                            if injecao.separacao
                                            else {}
                                        ),
                                    }
                                    for injecao in premissa.injecoes
                                ]
                            }
                            if premissa.injecoes
                            else {}
                        ),
                    }
                    for premissa in lista
                ]
                for chave, lista in self.premissas.items()
            },
        }
        if self.racional:
            saida["racional"] = self.racional
        return saida

    @property
    def total_de_premissas(self) -> int:
        return sum(len(lista) for lista in self.premissas.values())

    @property
    def total_de_injecoes(self) -> int:
        return sum(len(p.injecoes) for lista in self.premissas.values() for p in lista)

    def resumo(self) -> dict[str, int]:
        """Grandeza, nunca texto: é isto que vai para o span (ADR 0006)."""
        return {
            "entidades": len(self.entidades),
            "premissas": self.total_de_premissas,
            "injecoes": self.total_de_injecoes,
        }


__all__ = [
    "ESQUEMA_DO_RESULTADO",
    "MAXIMO_DE_INJECOES_POR_PREMISSA",
    "MAXIMO_DE_PREMISSAS_POR_ARESTA",
    "VERSAO_DO_RESULTADO",
    "VERSOES_SUPORTADAS",
    "InjecaoProposta",
    "PremissaProposta",
    "ResultadoDeGeracao",
    "ResultadoDeGeracaoInvalido",
]
