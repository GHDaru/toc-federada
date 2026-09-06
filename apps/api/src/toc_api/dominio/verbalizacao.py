"""Heurísticas de verbalização de obstáculo e objetivo intermediário (spec 008, F4.2.3).

Siglas, uma vez neste arquivo: **APR** — Árvore de Pré-Requisitos · **OI** — Objetivo
Intermediário · **TOC** — Teoria das Restrições · **IA** — inteligência artificial ·
**RF/RN/RNF** — requisito funcional / regra de negócio / requisito não funcional.

A fonte técnica é a skill local `toc-prt` (`references/prt-methodology.md`), que destila
Dettmer (*The Logical Thinking Process*, 2007, cap. 7) e Scheinkopf (*Thinking for a
Change*, 1999, cap. 10). Ela dá três armadilhas com exemplo, e são exatamente estes três
avisos:

| ❌ o que o método recusa | ✅ o que ele pede | código deste módulo |
|---|---|---|
| "Precisamos criar a conversão…" (ação) | "Não existe conversão… disponível" | `verbo_de_acao` |
| "O board vai recusar" (previsão) | "O board é conservador em gastos" | `previsao_futura` |
| "Falta dinheiro" (ausência genérica) | "Temos apenas R$ 15.000" | `ausencia_generica` |

Quatro decisões que valem estar escritas:

1. **Avisa, nunca veta** (RN-08). O resultado é dado que a interface mostra; o agregado
   registra o obstáculo de qualquer forma. A sessão de "sim, mas…" não pode travar na
   gramática — se travasse, o grupo pararia de contribuir, que é o oposto do método.
2. **`indeterminado` é resposta de primeira classe.** Quando a heurística não alcança o
   caso — texto curto demais, sem marcador —, ela **admite**. Aviso errado ensina o
   método errado; é a mesma lição já paga no M3 (`formulacao.py`).
3. **Léxico é dado versionado por idioma**, como o do M2 (`lexico.py`), e o corpus é
   função forçante: heurística nova sem caso novo não entra (RNF-07). O corpus vive em
   `tests/dominio/corpus_verbalizacao.json`.
4. **O alcance é declarado.** `previsao_futura` e `ausencia_generica` valem **só para
   obstáculo**: o obstáculo descreve o que existe hoje, enquanto o OI descreve o estado
   que passará a existir. Cobrar os dois pela mesma régua seria ensinar o método errado.
   `verbo_de_acao` vale para os dois, porque tarefa não é nem condição nem estado.

Nada de modelo, nada de rede: regra de domínio pura, testável offline (P3, RNF-01).
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from enum import Enum

VERSAO_DO_LEXICO_DE_VERBALIZACAO = "1.0.0"
"""1.0.0 = as três armadilhas da referência da skill `toc-prt` traduzidas em heurística."""

#: Abaixo disto, **e sem nenhum marcador encontrado**, a heurística se declara
#: `indeterminado` em vez de chutar: duas palavras sem marcador não descrevem condição nem
#: estado, descrevem um assunto. Com marcador, o piso não se aplica — ver `avaliar_verbalizacao`.
MINIMO_DE_PALAVRAS = 3


class PapelVerbalizado(str, Enum):
    """Os dois papéis que a APR avalia. O objetivo (o topo) não é avaliado por heurística."""

    OBSTACULO = "obstaculo"
    OBJETIVO_INTERMEDIARIO = "objetivo_intermediario"


class CodigoDeVerbalizacao(str, Enum):
    """Os avisos que a heurística sabe emitir. Cada um tem caso no corpus (RNF-07)."""

    VERBO_DE_ACAO = "verbo_de_acao"
    PREVISAO_FUTURA = "previsao_futura"
    AUSENCIA_GENERICA = "ausencia_generica"


class Veredito(str, Enum):
    ATENDE = "atende"
    AVISO = "aviso"
    INDETERMINADO = "indeterminado"


@dataclass(frozen=True, slots=True)
class AvisoDeVerbalizacao:
    """O aviso que a interface mostra inline (RI-05): trecho apontado, motivo e exemplo."""

    codigo: CodigoDeVerbalizacao
    trecho: str
    explicacao: str
    exemplo: str


@dataclass(frozen=True, slots=True)
class VerbalizacaoAvaliada:
    """O objeto de valor que sai da função pura — dado, nunca veto (RN-08)."""

    papel: PapelVerbalizado
    veredito: Veredito
    avisos: tuple[AvisoDeVerbalizacao, ...]
    versao_do_lexico: str

    @property
    def codigos(self) -> tuple[str, ...]:
        return tuple(a.codigo.value for a in self.avisos)


@dataclass(frozen=True, slots=True)
class LexicoDeVerbalizacao:
    """Os marcadores de um idioma. Congelado: quem quiser outro, declara outro."""

    idioma: str
    versao: str
    #: Terminações de infinitivo (o verbo de ação começando a frase).
    terminacoes_de_infinitivo: tuple[str, ...]
    #: Substantivos com terminação de infinitivo — sem eles, "Lugar" viraria verbo.
    excecoes_de_infinitivo: frozenset[str]
    #: Verbos de ação em infinitivo que a referência cita nominalmente.
    verbos_de_acao: tuple[str, ...]
    #: O que anuncia tarefa mesmo sem começar por infinitivo ("precisamos criar…").
    marcadores_de_tarefa: tuple[str, ...]
    #: O que anuncia previsão em vez de condição atual ("vai recusar", "poderá").
    marcadores_de_futuro: tuple[str, ...]
    #: O que anuncia ausência **genérica** — dizer o que falta em vez do que existe.
    marcadores_de_ausencia: tuple[str, ...]
    #: O que salva uma ausência de ser genérica: quantidade, recorte, exclusividade.
    marcadores_de_especificidade: tuple[str, ...]

    @property
    def marcadores(self) -> dict[str, tuple[str, ...]]:
        """Todo marcador, por família — o que o corpus tem de cobrir (RNF-07)."""
        return {
            "verbos_de_acao": self.verbos_de_acao,
            "tarefa": self.marcadores_de_tarefa,
            "futuro": self.marcadores_de_futuro,
            "ausencia": self.marcadores_de_ausencia,
            "especificidade": self.marcadores_de_especificidade,
        }


LEXICO_PT = LexicoDeVerbalizacao(
    idioma="pt",
    versao=VERSAO_DO_LEXICO_DE_VERBALIZACAO,
    terminacoes_de_infinitivo=("ar", "er", "ir"),
    excecoes_de_infinitivo=frozenset(
        {
            "lugar", "mar", "ar", "par", "bar", "altar", "andar", "celular", "militar",
            "escolar", "familiar", "auxiliar", "pilar", "colar", "jantar", "poder",
            "prazer", "dever", "saber", "lider", "carater", "porvir", "elixir",
            "computador", "coordenador", "diretor", "setor", "valor", "professor",
        }
    ),
    verbos_de_acao=(
        "criar", "implementar", "desenvolver", "mapear", "estudar", "configurar",
        "contratar", "treinar", "migrar", "integrar", "publicar", "revisar", "ajustar",
        "construir", "levantar", "definir", "documentar", "automatizar", "comprar",
    ),
    marcadores_de_tarefa=(
        "precisamos ", "precisa-se ", "é preciso ", "temos que ", "vamos ", "devemos ",
    ),
    marcadores_de_futuro=(
        "vai ", "vão ", "irá ", "irão ", "poderá ", "poderão ", "deverá ", "deverão ",
    ),
    marcadores_de_ausencia=(
        "falta ", "faltam ", "falta de ", "não temos ", "nao temos ", "carência de ",
        "sem recursos",
    ),
    marcadores_de_especificidade=(
        "apenas", "somente", "só ", "único", "única", "no máximo", "por dia", "por mês",
    ),
)

LEXICOS = {LEXICO_PT.idioma: LEXICO_PT}

#: Futuro do presente sintético: "cobrirá", "recusarão", "faremos". É a mesma expressão
#: da `FUTURO` do M2 (`lexico.py`), e ela é **sensível a acento de propósito**: a versão
#: sem acento aceitaria a terminação "-ra" e faria "a Secretaria **opera** com duas
#: pessoas" — presente, e obstáculo bem verbalizado — virar aviso de previsão futura.
#: Falso positivo ensina o método errado, que é o que a RF-22 manda evitar.
#:
#: **Alcance declarado**: texto digitado sem acento cai só nos marcadores perifrásticos
#: ("vai recusar", "poderá"), como o alcance declarado da formulação do M3 para o inglês
#: sem `to`. Ampliá-lo exige caso novo no corpus (RNF-07).
FUTURO_SINTETICO = re.compile(r"\b\w{3,}r(?:á|ão|ei|emos|eis)\b", re.IGNORECASE)
PALAVRAS = re.compile(r"[\wÀ-ÿ]+")

_EXPLICACOES: dict[CodigoDeVerbalizacao, dict[str, str]] = {
    CodigoDeVerbalizacao.VERBO_DE_ACAO: {
        PapelVerbalizado.OBSTACULO.value: (
            "verbo de ação: obstáculo descreve condição que existe hoje, não tarefa a fazer"
        ),
        PapelVerbalizado.OBJETIVO_INTERMEDIARIO.value: (
            "verbo de ação: objetivo intermediário é estado conquistado, não atividade"
        ),
    },
    CodigoDeVerbalizacao.PREVISAO_FUTURA: {
        PapelVerbalizado.OBSTACULO.value: (
            "previsão futura: obstáculo é condição atual real, não o que pode acontecer"
        ),
    },
    CodigoDeVerbalizacao.AUSENCIA_GENERICA: {
        PapelVerbalizado.OBSTACULO.value: (
            "ausência genérica: diga o que EXISTE hoje, com recorte — é mais fácil de superar"
        ),
    },
}

_EXEMPLOS: dict[CodigoDeVerbalizacao, dict[str, str]] = {
    CodigoDeVerbalizacao.VERBO_DE_ACAO: {
        PapelVerbalizado.OBSTACULO.value: (
            "em vez de \"Precisamos criar a conferência\", escreva \"Não existe rotina de "
            "conferência entre matrícula e contrato\""
        ),
        PapelVerbalizado.OBJETIVO_INTERMEDIARIO.value: (
            "em vez de \"Criar a rotina de conferência\", escreva \"A rotina de conferência "
            "está operacional e validada\""
        ),
    },
    CodigoDeVerbalizacao.PREVISAO_FUTURA: {
        PapelVerbalizado.OBSTACULO.value: (
            "em vez de \"O conselho vai recusar\", escreva \"O conselho é conservador em "
            "gasto não essencial\""
        ),
    },
    CodigoDeVerbalizacao.AUSENCIA_GENERICA: {
        PapelVerbalizado.OBSTACULO.value: (
            "em vez de \"Falta dinheiro\", escreva \"Temos apenas quinze mil reais "
            "disponíveis para a frente\""
        ),
    },
}


def lexico_de_verbalizacao(idioma: str = "pt") -> LexicoDeVerbalizacao:
    """O léxico do idioma. Idioma sem léxico é erro explícito, nunca silêncio."""
    try:
        return LEXICOS[idioma]
    except KeyError as ausente:
        raise KeyError(f"sem léxico de verbalização para o idioma {idioma!r}") from ausente


def _sem_acento(texto: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFD", texto) if unicodedata.category(c) != "Mn"
    )


def _e_infinitivo(palavra: str, lexico: LexicoDeVerbalizacao) -> bool:
    limpa = _sem_acento(palavra.lower())
    if limpa in lexico.excecoes_de_infinitivo:
        return False
    if len(limpa) < 4:
        return False
    return limpa.endswith(lexico.terminacoes_de_infinitivo)


def avaliar_verbalizacao(
    papel: PapelVerbalizado | str, texto: str, *, idioma: str = "pt"
) -> VerbalizacaoAvaliada:
    """RF-20: a avaliação — função pura, offline, com o trecho apontado (RI-05).

    A ordem das checagens é a ordem das armadilhas da referência, e ela importa só para o
    relato: um texto pode disparar mais de um aviso, e os dois aparecem.
    """
    papel = PapelVerbalizado(papel)
    lexico = lexico_de_verbalizacao(idioma)
    bruto = (texto or "").strip()
    minusculo = bruto.lower()
    sem_acento = _sem_acento(minusculo)
    palavras = PALAVRAS.findall(bruto)

    avisos: list[AvisoDeVerbalizacao] = []

    # 1. verbo de ação — tarefa disfarçada. Vale para os dois papéis.
    trecho_de_acao = _trecho_de_acao(bruto, minusculo, palavras, lexico)
    if trecho_de_acao:
        avisos.append(_aviso(CodigoDeVerbalizacao.VERBO_DE_ACAO, papel, trecho_de_acao))

    if papel is PapelVerbalizado.OBSTACULO:
        # 2. previsão futura — só o obstáculo, que descreve o presente.
        trecho_de_futuro = _trecho_de_futuro(bruto, minusculo, sem_acento, lexico)
        if trecho_de_futuro:
            avisos.append(
                _aviso(CodigoDeVerbalizacao.PREVISAO_FUTURA, papel, trecho_de_futuro)
            )

        # 3. ausência genérica — e a especificidade a desarma.
        trecho_de_ausencia = _trecho_de_ausencia(minusculo, sem_acento, lexico)
        if trecho_de_ausencia:
            avisos.append(
                _aviso(CodigoDeVerbalizacao.AUSENCIA_GENERICA, papel, trecho_de_ausencia)
            )

    # O piso de palavras vem DEPOIS de procurar marcador, e não antes: "Falta dinheiro" —
    # o exemplo canônico de ausência genérica da referência da skill `toc-prt` — tem duas
    # palavras, e sumiria em `indeterminado` se o piso viesse primeiro. "Curto demais para
    # julgar" só vale quando não há nada a julgar.
    if avisos:
        veredito = Veredito.AVISO
    elif len(palavras) < MINIMO_DE_PALAVRAS:
        veredito = Veredito.INDETERMINADO
    else:
        veredito = Veredito.ATENDE
    return VerbalizacaoAvaliada(
        papel=papel,
        veredito=veredito,
        avisos=tuple(avisos),
        versao_do_lexico=lexico.versao,
    )


def _posicao_do_marcador(texto: str, marcador: str) -> int:
    """Onde o marcador começa, **respeitando fronteira de palavra** — ou `-1`.

    A busca por substring cru é o defeito que este helper existe para não deixar voltar:
    o marcador `"irá "` casava dentro de `"cobrirá as"`, e o aviso apontava um trecho que
    ninguém escreveu. Fronteira de palavra é o que separa "irá" de "cobrirá".
    """
    achado = re.search(rf"\b{re.escape(marcador.strip())}\b", texto, re.IGNORECASE)
    return achado.start() if achado else -1


def _trecho_de_acao(
    bruto: str, minusculo: str, palavras: list[str], lexico: LexicoDeVerbalizacao
) -> str:
    for marcador in lexico.marcadores_de_tarefa:
        if _posicao_do_marcador(minusculo, marcador) >= 0:
            return marcador.strip()
    primeira = palavras[0]
    if primeira.lower() in lexico.verbos_de_acao or _e_infinitivo(primeira, lexico):
        return primeira
    return ""


def _trecho_de_futuro(
    bruto: str, minusculo: str, sem_acento: str, lexico: LexicoDeVerbalizacao
) -> str:
    for marcador in lexico.marcadores_de_futuro:
        posicao = _posicao_do_marcador(minusculo, marcador)
        if posicao >= 0:
            # O trecho apontado inclui o verbo que vem depois: "vai recusar" diz mais do
            # que "vai", e o aviso serve para reformular, não para acusar.
            resto = bruto[posicao + len(marcador) :].split()
            return (marcador + (resto[0] if resto else "")).strip()
    achado = FUTURO_SINTETICO.search(minusculo)
    if achado:
        return achado.group(0)
    return ""


def _trecho_de_ausencia(
    minusculo: str, sem_acento: str, lexico: LexicoDeVerbalizacao
) -> str:
    for marcador in lexico.marcadores_de_especificidade:
        if _posicao_do_marcador(minusculo, marcador) >= 0 or _posicao_do_marcador(
            sem_acento, marcador
        ) >= 0:
            # "Temos apenas quinze mil reais" diz o que existe, com recorte: não é
            # ausência genérica, é a forma CORRETA da mesma frase.
            return ""
    for marcador in lexico.marcadores_de_ausencia:
        if _posicao_do_marcador(minusculo, marcador) >= 0:
            return marcador
    return ""


def _aviso(
    codigo: CodigoDeVerbalizacao, papel: PapelVerbalizado, trecho: str
) -> AvisoDeVerbalizacao:
    return AvisoDeVerbalizacao(
        codigo=codigo,
        trecho=trecho,
        explicacao=_EXPLICACOES[codigo][papel.value],
        exemplo=_EXEMPLOS[codigo][papel.value],
    )


__all__ = [
    "VERSAO_DO_LEXICO_DE_VERBALIZACAO",
    "AvisoDeVerbalizacao",
    "CodigoDeVerbalizacao",
    "LexicoDeVerbalizacao",
    "PapelVerbalizado",
    "Veredito",
    "VerbalizacaoAvaliada",
    "avaliar_verbalizacao",
    "lexico_de_verbalizacao",
]
