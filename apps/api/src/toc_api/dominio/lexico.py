"""O léxico das heurísticas — dado versionado por idioma, nunca literal espalhado no código.

A spec 005 (RF-11) exige exatamente isto: "O SISTEMA DEVE manter o léxico das heurísticas
(marcadores de causa, de solução, de culpa, verbos de ação) como dado versionado por
idioma, testável em isolamento — nunca literal espalhado no código". O motivo está na
linhagem: os oito prompts da 4ª geração eram dado **do navegador**, editáveis por uma tela
de administração (`tocbuilderv3/constants.ts:341-405`), e por isso a regra de negócio
mudava em produção sem teste. Aqui o léxico é dado do **domínio**, versionado, e a
RNF-07 amarra a mão de quem o amplia: ampliar o léxico exige ampliar o corpus
(`tests/dominio/test_corpus_udes.py` reprova marcador sem caso).

Os marcadores vieram, um a um, de `docs/produto/dados/medir-base.py` (linhas 57-77), que
os destilou de `tocbuilderv3/constants.ts:122-133`. A **única** adição são os campos
`verbos_causais`, `verbos_causais_ambiguos` e `determinantes`, e ela tem origem nomeada:
o falso negativo K-03 medido pelo conjunto de controle (`docs/produto/visao.md` §6,
defeito D-12).
"""
from __future__ import annotations

import re
from dataclasses import dataclass

VERSAO_DO_LEXICO = "1.1.0"
"""1.0.0 = a tradução de `medir-base.py`. 1.1.0 acrescenta os verbos causais (K-03)."""


@dataclass(frozen=True, slots=True)
class Lexico:
    """Os marcadores de um idioma. Congelado: quem quiser outro, declara outro."""

    idioma: str
    versao: str
    passado_irregular: frozenset[str]
    excecao_temporal: frozenset[str]
    culpa: tuple[str, ...]
    solucao_oculta: tuple[str, ...]
    coordenacao: tuple[str, ...]
    causa_na_frase: tuple[str, ...]
    verbos_causais: tuple[str, ...]
    verbos_causais_ambiguos: tuple[str, ...]
    determinantes: frozenset[str]
    subjetivo: tuple[str, ...]

    @property
    def marcadores(self) -> dict[str, tuple[str, ...]]:
        """Todo marcador lexical, por família — o que o corpus tem de cobrir (RNF-07)."""
        return {
            "culpa": self.culpa,
            "solucao_oculta": self.solucao_oculta,
            "coordenacao": self.coordenacao,
            "causa_na_frase": self.causa_na_frase,
            "verbos_causais": self.verbos_causais + self.verbos_causais_ambiguos,
            "subjetivo": self.subjetivo,
        }


LEXICO_PT = Lexico(
    idioma="pt",
    versao=VERSAO_DO_LEXICO,
    # `medir-base.py:59-60`
    passado_irregular=frozenset(
        {"foi", "foram", "era", "eram", "teve", "tiveram", "houve",
         "fez", "fizeram", "pôde", "puderam", "veio", "vieram"}
    ),
    # `medir-base.py:61-62` — sem esta lista, "céu" e "seu" viram verbo no passado.
    excecao_temporal=frozenset(
        {"seu", "seus", "meu", "meus", "teu", "céu", "grau", "europeu",
         "ateu", "judeu", "chapéu", "troféu", "museu"}
    ),
    culpa=(  # `medir-base.py:67-68` — característica 6
        "desleixad", "não se importa", "incompeten", "preguiç", "por culpa",
        "falta de comprometimento", "relapso", "descuidad", "má vontade",
    ),
    solucao_oculta=(  # `medir-base.py:69-71` — característica 8
        "falta um ", "falta uma ", "falta de um ", "falta de uma ",
        "precisamos de ", "deveria haver", "não temos um ", "não temos uma ",
        "seria necessário", "bastaria ",
    ),
    coordenacao=(  # `medir-base.py:72` — característica 9
        ";", " e também ", " bem como ", " além disso", " e ainda ",
    ),
    causa_na_frase=(  # `medir-base.py:74-75` — característica 10, os CONECTIVOS
        "porque", "devido a", "por causa de", "já que", "uma vez que",
        "em razão de", "em função de", "pois ", "em decorrência de",
    ),
    # A adição de 1.1.0 — característica 10, os VERBOS. O buraco que só um gabarito
    # alheio encontraria: a base autoral não tinha um só enunciado com verbo causal,
    # "quem a escreveu tinha na cabeça a mesma lista" dos conectivos (`visao.md` §6).
    verbos_causais=(
        "causam", "provoca", "provocam", "acarreta", "acarretam",
        "ocasiona", "ocasionam", "leva a", "levam a", "resulta em", "resultam em",
        "decorre de", "decorrem de", "é causado por", "são causados por",
        "é causada por", "são causadas por",
    ),
    # Ambíguos: são verbo OU substantivo. Só contam como verbo quando NÃO vêm precedidos
    # de determinante — sem isso, fechar o falso negativo K-03 abriria um falso positivo
    # em "A causa do atraso permanece desconhecida".
    verbos_causais_ambiguos=("causa", "causas"),
    determinantes=frozenset(
        {"a", "as", "o", "os", "uma", "umas", "um", "uns", "da", "das", "do", "dos",
         "na", "nas", "no", "nos", "à", "às", "essa", "essas", "esta", "estas",
         "aquela", "aquelas", "sua", "suas", "minha", "nossa", "outra", "outras",
         "mesma", "única", "alguma", "algumas", "nenhuma", "cada", "muitas", "poucas",
         "qual", "quais", "toda", "todas", "primeira", "segunda"}
    ),
    subjetivo=(  # `medir-base.py:76-77` — característica 11
        "péssim", "ruim", "horrív", "absurd", "inaceitáv", "excessivamente",
        "claramente", "desleixad", "muito ", "ótim", "terrível",
    ),
)

LEXICOS = {LEXICO_PT.idioma: LEXICO_PT}


def lexico_de(idioma: str = "pt") -> Lexico:
    """O léxico do idioma. Idioma sem léxico é erro explícito, nunca silêncio."""
    try:
        return LEXICOS[idioma]
    except KeyError as ausente:  # pragma: no cover - guarda de composição
        raise KeyError(f"sem léxico de UDE para o idioma {idioma!r}") from ausente


# -- expressões regulares que não dependem de idioma-alvo, só do português --------------
# `medir-base.py:57-65`, copiadas sem alteração: mudá-las mudaria o veredito publicado.

PASSADO = re.compile(
    r"\b\w{3,}(?:ou|eu|iu|aram|eram|iram|ava|avam|iam)\b", re.IGNORECASE
)
FUTURO = re.compile(r"\b\w{3,}r(?:á|ão|ei|emos|eis|íamos)\b", re.IGNORECASE)
INFINITIVO = re.compile(r"^[A-ZÁÉÍÓÚÂÊÔÃÕÇ]\w{2,}(?:ar|er|ir)$")
RE_COORDENACAO = re.compile(r"\se\s(?:o|a|os|as)\s", re.IGNORECASE)
PALAVRAS = re.compile(r"[\wÀ-ÿ%]+")
