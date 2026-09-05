"""Heurísticas de boa formulação das entidades da Nuvem de Conflito (spec 007).

Siglas, uma vez neste arquivo: **NC** — Nuvem de Conflito · **TOC** — Teoria das
Restrições · **UDE** — Efeito Indesejável · **IA** — inteligência artificial.

O método (skill `toc-evaporating-cloud`) pede uma forma canônica: **A, B e C em
substantivo** (com adjetivo opcional), **D e D′ em infinitivo verbal**, e **D′ negando ou
excluindo D**. A spec transforma isso em RF-09, RF-10 e RN-06 com uma condição que manda
no desenho inteiro deste módulo: **é aviso, nunca bloqueio**. O método educa; o dado
obedece ao grupo.

Três decisões que valem estar escritas:

1. **Léxico é dado versionado por idioma** (RF-11), como o do M2 em `lexico.py`. Nada de
   literal solto no meio da função: quem amplia a heurística amplia o corpus
   (`tests/dominio/corpus_formulacao.json`), e o teste reprova código de aviso sem caso.
2. **`indeterminado` é resposta de primeira classe** (RF-10). Quando a heurística não
   alcança o caso — sem marcador de negação e sem palavra em comum entre D e D′ — ela
   **admite** e não avisa. Aviso errado ensina o método errado, e é pior do que silêncio.
3. **Nada de modelo, nada de rede.** Isto é regra de domínio pura, testável offline (P3,
   RNF-01). O contraste com a linhagem é o ponto: lá, o que cumpria este papel era um
   prompt de 75 linhas no cliente (`tocbuilderv3/constants.ts:264-338`), servido pelo SDK
   com a chave no navegador.

O alcance é declarado, não presumido: em português a detecção do infinitivo é morfológica
(terminação `-ar`/`-er`/`-ir`, com lista de exceção para substantivos como "lugar"); em
inglês é o infinitivo **marcado** (`to open`). Forma inglesa sem `to` não gera aviso — é
`indeterminado` por construção, e está assim de propósito.
"""
from __future__ import annotations

import unicodedata
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover - só para o verificador de tipos
    from .nuvem import PapelDaEntidade

VERSAO_DO_LEXICO_DE_FORMULACAO = "1.0.0"
"""1.0.0 = a forma canônica da skill `toc-evaporating-cloud` traduzida em heurística."""

#: Quanto de palavra em comum basta para dizer que dois textos falam da mesma ação.
#: Abaixo disto a heurística se declara `indeterminado` em vez de chutar.
LIMIAR_DE_SOBREPOSICAO = 0.34


class CodigoDeAviso(str, Enum):
    """Os avisos que a heurística sabe emitir. Cada um tem caso no corpus (RNF-08)."""

    PEDE_SUBSTANTIVO = "pede_substantivo"
    D_PEDE_INFINITIVO = "d_pede_infinitivo"
    D_LINHA_NAO_NEGA_D = "d_linha_nao_nega_d"


class Negacao(str, Enum):
    """O veredito sobre "D′ nega ou exclui D?" — com o `indeterminado` honesto (RF-10)."""

    NEGA = "nega"
    NAO_NEGA = "nao_nega"
    INDETERMINADO = "indeterminado"


@dataclass(frozen=True, slots=True)
class AvisoDeFormulacao:
    """O aviso que a interface mostra no próprio nó (RI-05): explicação **e** exemplo.

    O exemplo não é enfeite: um aviso que diz "está errado" sem mostrar a forma certa
    ensina que a ferramenta implica, não que o método existe.
    """

    codigo: CodigoDeAviso
    papel: "PapelDaEntidade"
    explicacao: str
    exemplo: str


@dataclass(frozen=True, slots=True)
class LexicoDeFormulacao:
    """Os marcadores de um idioma. Congelado: quem quiser outro, declara outro."""

    idioma: str
    versao: str
    #: Terminações que denunciam infinitivo verbal (vazio quando o idioma usa marcador).
    terminacoes_de_infinitivo: tuple[str, ...]
    #: Prefixo do infinitivo marcado ("to " em inglês); vazio quando não há.
    marcador_de_infinitivo: str
    #: Substantivos com terminação de infinitivo — sem eles, "Lugar" vira verbo.
    excecoes_de_infinitivo: frozenset[str]
    #: O que abre uma negação de D em D′.
    marcadores_de_negacao: tuple[str, ...]
    #: Palavras que não contam na sobreposição entre D e D′.
    vazias: frozenset[str]


LEXICO_PT = LexicoDeFormulacao(
    idioma="pt",
    versao=VERSAO_DO_LEXICO_DE_FORMULACAO,
    terminacoes_de_infinitivo=("ar", "er", "ir"),
    marcador_de_infinitivo="",
    excecoes_de_infinitivo=frozenset(
        {
            "lugar", "mar", "ar", "par", "bar", "altar", "andar", "celular", "militar",
            "escolar", "familiar", "auxiliar", "pilar", "colar", "olhar", "jantar",
            "poder", "prazer", "dever", "saber", "amanhecer", "lider", "carater",
            "porvir", "elixir", "sir",
        }
    ),
    marcadores_de_negacao=(
        "nao ", "deixar de ", "evitar ", "parar de ", "abrir mao de ", "sem ", "recusar ",
    ),
    vazias=frozenset(
        {
            "a", "as", "o", "os", "um", "uma", "uns", "umas", "de", "da", "das", "do",
            "dos", "em", "no", "na", "nos", "nas", "por", "para", "com", "que", "e",
            "ou", "ao", "aos", "pela", "pelo", "sua", "seu", "suas", "seus",
        }
    ),
)

LEXICO_EN = LexicoDeFormulacao(
    idioma="en",
    versao=VERSAO_DO_LEXICO_DE_FORMULACAO,
    terminacoes_de_infinitivo=(),
    marcador_de_infinitivo="to ",
    excecoes_de_infinitivo=frozenset(),
    marcadores_de_negacao=("not ", "do not ", "dont ", "avoid ", "stop ", "refrain from "),
    vazias=frozenset(
        {
            "a", "an", "the", "of", "in", "on", "at", "to", "for", "and", "or", "with",
            "by", "from", "its", "their",
        }
    ),
)

LEXICOS_DE_FORMULACAO = {LEXICO_PT.idioma: LEXICO_PT, LEXICO_EN.idioma: LEXICO_EN}


def lexico_de_formulacao(idioma: str = "pt") -> LexicoDeFormulacao:
    """O léxico do idioma. Idioma sem léxico é erro explícito, nunca silêncio."""
    try:
        return LEXICOS_DE_FORMULACAO[idioma]
    except KeyError as ausente:
        raise KeyError(
            f"sem léxico de formulação para o idioma {idioma!r}; declare-o em "
            "toc_api.dominio.formulacao **com corpus**"
        ) from ausente


# -- as explicações, por código e por idioma -------------------------------------------
# Ficam como dado, e não interpoladas no meio da regra, porque a RNF-09 quer chave estável
# ligada à regra: a interface traduz por `codigo`, e o texto abaixo é o padrão do servidor.

EXPLICACOES: dict[tuple[str, CodigoDeAviso], tuple[str, str]] = {
    ("pt", CodigoDeAviso.PEDE_SUBSTANTIVO): (
        "objetivo e necessidades vêm em substantivo (com adjetivo opcional), não em ação",
        "Reputação acadêmica preservada",
    ),
    ("pt", CodigoDeAviso.D_PEDE_INFINITIVO): (
        "esta posição pede uma ação em infinitivo verbal",
        "Abrir turmas em três cidades novas",
    ),
    ("pt", CodigoDeAviso.D_LINHA_NAO_NEGA_D): (
        "D′ nega ou exclui D — duas ações positivas diferentes não formam conflito",
        "Não abrir turmas em três cidades novas",
    ),
    ("en", CodigoDeAviso.PEDE_SUBSTANTIVO): (
        "goal and needs are nouns (with an optional adjective), not actions",
        "Preserved academic reputation",
    ),
    ("en", CodigoDeAviso.D_PEDE_INFINITIVO): (
        "this position asks for an action in the marked infinitive",
        "To open classes in three new cities",
    ),
    ("en", CodigoDeAviso.D_LINHA_NAO_NEGA_D): (
        "D′ negates or excludes D — two different positive actions are not a conflict",
        "Not to open classes in three new cities",
    ),
}


def _sem_acento(texto: str) -> str:
    decomposto = unicodedata.normalize("NFD", texto)
    return "".join(c for c in decomposto if unicodedata.category(c) != "Mn")


def _normalizar(texto: str) -> str:
    """Minúsculas, sem acento e sem pontuação — a forma em que dois textos se comparam."""
    limpo = _sem_acento(texto.strip().lower())
    return " ".join("".join(c for c in limpo if c.isalnum() or c.isspace()).split())


def _palavras_de_conteudo(texto: str, lexico: LexicoDeFormulacao) -> set[str]:
    return {p for p in _normalizar(texto).split() if p not in lexico.vazias and len(p) > 2}


def _sem_marcador(texto: str, lexico: LexicoDeFormulacao) -> tuple[str, bool]:
    """Tira o marcador de negação da frente, se houver. Devolve (núcleo, tinha marcador)."""
    normalizado = _normalizar(texto)
    for marcador in sorted(lexico.marcadores_de_negacao, key=len, reverse=True):
        if normalizado.startswith(marcador):
            return normalizado[len(marcador) :].strip(), True
    return normalizado, False


def _e_infinitivo(nucleo: str, lexico: LexicoDeFormulacao) -> bool:
    """A frase começa por verbo no infinitivo? Morfologia em pt, marcador em en."""
    if not nucleo:
        return False
    if lexico.marcador_de_infinitivo:
        prefixo = lexico.marcador_de_infinitivo
        return nucleo.startswith(prefixo) and len(nucleo) > len(prefixo)
    primeira = nucleo.split()[0]
    if primeira in lexico.excecoes_de_infinitivo:
        return False
    return len(primeira) >= 4 and primeira.endswith(lexico.terminacoes_de_infinitivo)


def avaliar_negacao(texto_de_d: str, texto_de_d_linha: str, idioma: str = "pt") -> Negacao:
    """RF-10: D′ nega ou exclui D? Três vereditos, e o terceiro é "não sei" (honesto)."""
    lexico = lexico_de_formulacao(idioma)
    d = _normalizar(texto_de_d)
    if not d or not _normalizar(texto_de_d_linha):
        return Negacao.INDETERMINADO

    nucleo, teve_marcador = _sem_marcador(texto_de_d_linha, lexico)
    palavras_de_d = _palavras_de_conteudo(texto_de_d, lexico)
    palavras_do_nucleo = {
        p for p in nucleo.split() if p not in lexico.vazias and len(p) > 2
    }
    comuns = palavras_de_d & palavras_do_nucleo
    denominador = min(len(palavras_de_d), len(palavras_do_nucleo)) or 1
    sobreposicao = len(comuns) / denominador

    if teve_marcador:
        if nucleo == d or sobreposicao >= 0.5:
            return Negacao.NEGA
        return Negacao.INDETERMINADO
    if sobreposicao >= LIMIAR_DE_SOBREPOSICAO:
        # Duas ações positivas sobre o mesmo assunto: dá para dizer que NÃO é negação.
        return Negacao.NAO_NEGA
    return Negacao.INDETERMINADO


def _aviso(codigo: CodigoDeAviso, papel: "PapelDaEntidade", idioma: str) -> AvisoDeFormulacao:
    explicacao, exemplo = EXPLICACOES[(idioma, codigo)]
    return AvisoDeFormulacao(
        codigo=codigo, papel=papel, explicacao=explicacao, exemplo=exemplo
    )


def avaliar_formulacao(
    papel: "PapelDaEntidade",
    texto: str,
    *,
    idioma: str = "pt",
    texto_de_d: str | None = None,
) -> tuple[AvisoDeFormulacao, ...]:
    """Os avisos de uma entidade. Lista vazia = a forma canônica foi reconhecida.

    `texto_de_d` só interessa a D′: sem ele não há como avaliar a negação, e a ausência
    de veredito **não** vira aviso.
    """
    from .nuvem import PapelDaEntidade  # local: evita ciclo entre os dois módulos

    lexico = lexico_de_formulacao(idioma)
    limpo = (texto or "").strip()
    if not limpo:
        return ()

    avisos: list[AvisoDeFormulacao] = []
    nucleo, _ = _sem_marcador(limpo, lexico)

    if papel in (PapelDaEntidade.A, PapelDaEntidade.B, PapelDaEntidade.C):
        if _e_infinitivo(_normalizar(limpo), lexico):
            avisos.append(_aviso(CodigoDeAviso.PEDE_SUBSTANTIVO, papel, idioma))
    else:
        if not _e_infinitivo(nucleo, lexico):
            avisos.append(_aviso(CodigoDeAviso.D_PEDE_INFINITIVO, papel, idioma))

    if papel is PapelDaEntidade.D_PRIME and texto_de_d:
        if avaliar_negacao(texto_de_d, limpo, idioma) is Negacao.NAO_NEGA:
            avisos.append(_aviso(CodigoDeAviso.D_LINHA_NAO_NEGA_D, papel, idioma))

    return tuple(avisos)


__all__ = [
    "EXPLICACOES",
    "LEXICOS_DE_FORMULACAO",
    "LEXICO_EN",
    "LEXICO_PT",
    "LIMIAR_DE_SOBREPOSICAO",
    "VERSAO_DO_LEXICO_DE_FORMULACAO",
    "AvisoDeFormulacao",
    "CodigoDeAviso",
    "LexicoDeFormulacao",
    "Negacao",
    "avaliar_formulacao",
    "avaliar_negacao",
    "lexico_de_formulacao",
]
