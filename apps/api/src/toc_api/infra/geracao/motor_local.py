"""O adaptador de geração desta fase — **um duplo determinístico, declarado como tal**.

Siglas, uma vez neste arquivo: **NC** — Nuvem de Conflito · **IA** — inteligência
artificial · **SDK** — *Software Development Kit* (kit de desenvolvimento) · **TRIZ** —
Teoria da Resolução Inventiva de Problemas · **ADR** — *Architecture Decision Record*
(Registro de Decisão Arquitetural).

**Isto não é um modelo de linguagem, e não fala com nenhum.** O ADR 0007 é explícito:
assistência de IA **somente pela fundação**, via catálogo de ações governadas — nenhum SDK
de provedor entra no produto. O que existe aqui é a implementação local e determinística
da porta `MotorDeGeracaoDeNuvem`, para que:

1. a **forma** do contrato (RF-21, RF-22) esteja exercitada de ponta a ponta desde já —
   estrutura validada por esquema versionado, nunca texto para interpretar;
2. a jornada e os testes rodem **offline**, sem chave, sem rede e sem variação entre
   execuções;
3. o dia em que a fundação repassar a geração seja **troca de adaptador**, não reescrita:
   quem muda é este arquivo, e o domínio, a aplicação e o catálogo ficam onde estão.

O que ele faz é honesto e pequeno: recorta a narrativa em frases, usa as primeiras como
texto das entidades (com a negação de D montada por regra) e escreve, para cada uma das 7
arestas, uma premissa derivada da **classe** daquela aresta. Nada aqui interpreta texto
livre nem promete análise: é ponto de partida para a pessoa revisar, e a nuvem inteira
continua funcionando sem ele (RF-28).

Determinismo é requisito, não acaso: a mesma narrativa produz o mesmo resultado, e é isso
que faz a pré-visualização em diff (RI-06) valer para a aplicação que virá depois dela.
"""
from __future__ import annotations

from typing import Any, Mapping, Sequence

from ...dominio.geracao import VERSAO_DO_RESULTADO
from ...dominio.nuvem import (
    LIMITE_INJECAO,
    LIMITE_PREMISSA,
    LIMITE_TEXTO_DE_ENTIDADE,
    PAR_DA_ARESTA,
    ChaveDaAresta,
    ClasseDaAresta,
    PapelDaEntidade,
)
from ...dominio.nuvem import CLASSE_POR_CHAVE

#: Como cada classe de aresta vira uma premissa a confirmar. A frase é do método (o que a
#: aresta afirma), não uma opinião sobre a narrativa.
PREMISSA_POR_CLASSE: dict[ClasseDaAresta, str] = {
    ClasseDaAresta.NECESSIDADE: "{destino} depende de {origem}",
    ClasseDaAresta.PRE_REQUISITO: "{origem} é o único caminho conhecido para {destino}",
    ClasseDaAresta.PERIGO: "{origem} ameaça {destino} enquanto nada mudar",
    ClasseDaAresta.CONFLITO: "{origem} e {destino} disputam o mesmo recurso",
}

#: Texto de partida quando a narrativa não tem frases suficientes. Neutro de propósito:
#: inventar conteúdo seria pior do que devolver a posição vazia de sentido.
PADRAO: dict[PapelDaEntidade, str] = {
    PapelDaEntidade.A: "Objetivo comum a confirmar",
    PapelDaEntidade.B: "Necessidade 1 a confirmar",
    PapelDaEntidade.C: "Necessidade 2 a confirmar",
    PapelDaEntidade.D: "Confirmar a ação em disputa",
}


def _frases(narrativa: str) -> list[str]:
    bruto = (narrativa or "").replace("\n", ". ")
    return [p.strip() for p in bruto.split(".") if len(p.strip()) > 3]


def _cortar(texto: str, limite: int) -> str:
    limpo = " ".join(texto.split())
    return limpo[:limite].strip() or "a confirmar"


def _negar(acao: str) -> str:
    limpo = acao.strip()
    if limpo.lower().startswith("não "):
        return limpo
    return f"Não {limpo[0].lower()}{limpo[1:]}" if limpo else "Não agir"


class MotorDeGeracaoLocal:
    """Implementa `MotorDeGeracaoDeNuvem` sem provedor nenhum (ADR 0007)."""

    #: Aparece no `/saude` e nas jornadas: quem lê descobre que a assistência desta
    #: instância é local, e não confunde o duplo com a fundação.
    nome = "local-deterministico"

    def gerar_nuvem(
        self, *, narrativa: str, contexto: Mapping[str, Any]
    ) -> Mapping[str, Any]:
        frases = _frases(narrativa)
        atuais = dict(contexto.get("entidades") or {})

        def entidade(papel: PapelDaEntidade, indice: int) -> str:
            if indice < len(frases):
                return _cortar(frases[indice], LIMITE_TEXTO_DE_ENTIDADE)
            # Sem frase para a posição: preserva o que a pessoa já escreveu, e só cai no
            # texto neutro quando nem isso existe.
            atual = str(atuais.get(papel.value) or "").strip()
            if atual and not atual.startswith("["):
                return _cortar(atual, LIMITE_TEXTO_DE_ENTIDADE)
            return PADRAO[papel]

        entidades = {
            PapelDaEntidade.A: entidade(PapelDaEntidade.A, 0),
            PapelDaEntidade.B: entidade(PapelDaEntidade.B, 1),
            PapelDaEntidade.C: entidade(PapelDaEntidade.C, 2),
            PapelDaEntidade.D: entidade(PapelDaEntidade.D, 3),
        }
        entidades[PapelDaEntidade.D_PRIME] = _cortar(
            _negar(entidades[PapelDaEntidade.D]), LIMITE_TEXTO_DE_ENTIDADE
        )

        arestas: dict[str, list[dict[str, Any]]] = {}
        for chave in ChaveDaAresta:
            origem, destino = PAR_DA_ARESTA[chave]
            premissa = {
                "texto": _cortar(
                    PREMISSA_POR_CLASSE[CLASSE_POR_CHAVE[chave]].format(
                        origem=entidades[origem], destino=entidades[destino]
                    ),
                    LIMITE_PREMISSA,
                )
            }
            if chave is ChaveDaAresta.D_D_PRIME:
                # A separação no tempo é a mais barata de propor e a mais fácil de recusar
                # — e recusar é de graça, porque nada disto está aplicado.
                premissa["injecoes"] = [
                    {
                        "texto": _cortar(
                            f"separar no tempo: {entidades[PapelDaEntidade.D]} em etapas",
                            LIMITE_INJECAO,
                        ),
                        "separacao": "tempo",
                    }
                ]
            arestas[chave.value] = [premissa]

        return {
            "versao": VERSAO_DO_RESULTADO,
            "racional": _cortar(
                "Proposta local determinística a partir da narrativa colada: "
                "confirme B e C e verifique se A abrange os dois.",
                1000,
            ),
            "entidades": {papel.value: texto for papel, texto in entidades.items()},
            "arestas": arestas,
        }

    def sugerir_premissas(
        self, *, aresta: str, narrativa: str, contexto: Mapping[str, Any]
    ) -> Sequence[Mapping[str, Any]]:
        chave = ChaveDaAresta(aresta)
        origem, destino = PAR_DA_ARESTA[chave]
        entidades = dict(contexto.get("entidades") or {})
        return (
            {
                "texto": _cortar(
                    PREMISSA_POR_CLASSE[CLASSE_POR_CHAVE[chave]].format(
                        origem=entidades.get(origem.value, origem.value),
                        destino=entidades.get(destino.value, destino.value),
                    ),
                    LIMITE_PREMISSA,
                )
            },
        )

    def sugerir_injecoes(
        self, *, premissa: str, contexto: Mapping[str, Any]
    ) -> Sequence[Mapping[str, Any]]:
        return (
            {
                "texto": _cortar(f"invalidar a premissa: {premissa}", LIMITE_INJECAO),
                "separacao": "condicao",
            },
        )


__all__ = ["PADRAO", "PREMISSA_POR_CLASSE", "MotorDeGeracaoLocal"]
