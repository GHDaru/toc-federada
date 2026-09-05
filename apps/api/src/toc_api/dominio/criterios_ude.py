"""Os critérios de um Efeito Indesejável (UDE) bem articulado — REGRA DE DOMÍNIO PURA.

Esta é a correção estrutural do defeito D-08 da visão. A 4ª geração da linhagem enterrou
as onze características de um UDE bem articulado dentro de um texto de prompt
(`tocbuilderv3/constants.ts:123-133`), interpolado numa chamada ao provedor **a partir do
navegador** — regra de negócio central que custava rede, variava com o modelo e nunca
teve um teste. Aqui ela é função pura: sem rede, sem modelo, sem estado, determinística.

A fronteira é declarada, não sugerida (spec 005, RF-08 e RF-09):

- **oito checagens decidíveis** cobrem sete características (a 2 vira duas: frase completa
  e tempo presente). Elas aprovam ou reprovam, e apontam o trecho;
- **quatro características são julgamento** — 1 (queixa sobre problema contínuo),
  4 (área de responsabilidade), 5 (algo pode ser feito) e 7 (não é causa especulada).
  Nenhuma função pura as decide, e por isso elas devolvem `INDETERMINADO`, **nunca** um
  chute: contam como pendência de parecer, não como reprovação (RF-08, RN-10).

A tradução original é `docs/produto/dados/medir-base.py`; a paridade veredito a veredito é
medida em `tests/dominio/test_paridade_com_medir_base.py`, com uma única divergência
declarada — o falso negativo K-03, que este módulo fecha.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .erros import NaoEncontrado
from .lexico import FUTURO, INFINITIVO, PALAVRAS, PASSADO, RE_COORDENACAO, Lexico, lexico_de


class ClasseDeCriterio(str, Enum):
    DECIDIVEL = "decidivel"
    JULGAMENTO = "julgamento"


class Veredito(str, Enum):
    ATENDE = "atende"
    NAO_ATENDE = "nao_atende"
    INDETERMINADO = "indeterminado"


@dataclass(frozen=True, slots=True)
class Criterio:
    """Uma das onze características, com a sua classe e a sua rastreabilidade.

    `nome` é a **chave de i18n estável** (RNF-09: "a chave do critério é a mesma da regra
    de domínio, para a rastreabilidade spec ↔ código ↔ tela"); `regra` é a regra de
    negócio da spec 005 (RN-01..RN-09); `caracteristica` é o número no prompt da linhagem.
    """

    codigo: str
    caracteristica: str
    nome: str
    classe: ClasseDeCriterio
    regra: str
    enunciado: str


@dataclass(frozen=True, slots=True)
class VereditoDeCriterio:
    criterio: Criterio
    veredito: Veredito
    motivo: str = ""
    trecho: str = ""

    @property
    def reprovou(self) -> bool:
        return self.veredito is Veredito.NAO_ATENDE


@dataclass(frozen=True, slots=True)
class ValidacaoFormal:
    """O resultado inteiro — objeto de valor, igual por valor, determinístico."""

    texto: str
    idioma: str
    versao_do_lexico: str
    vereditos: tuple[VereditoDeCriterio, ...]

    def veredito_de(self, codigo: str) -> VereditoDeCriterio:
        for v in self.vereditos:
            if v.criterio.codigo == codigo:
                return v
        raise NaoEncontrado(f"criterio:{codigo}")

    @property
    def reprovacoes(self) -> tuple[VereditoDeCriterio, ...]:
        return tuple(v for v in self.vereditos if v.reprovou)

    @property
    def aprovado_nos_decidiveis(self) -> bool:
        """RF-14/RN-10: é isto que o status `Validado` exige do lado da máquina."""
        return not self.reprovacoes

    @property
    def pendencias_de_julgamento(self) -> tuple[VereditoDeCriterio, ...]:
        return tuple(
            v for v in self.vereditos if v.veredito is Veredito.INDETERMINADO
        )

    @property
    def motivos(self) -> tuple[str, ...]:
        return tuple(f"{v.criterio.codigo} {v.motivo}" for v in self.reprovacoes)


# ---------------------------------------------------------------------------------------
# As oito checagens decidíveis. Cada uma é função pura `(texto, lexico) -> (ok, motivo,
# trecho)`; nenhuma toca rede, relógio ou estado.
# ---------------------------------------------------------------------------------------


def _palavras(texto: str) -> list[str]:
    return PALAVRAS.findall(texto)


def cd1_frase_completa(t: str, lex: Lexico):
    """Característica 2 (parte 1): deve ser uma frase completa."""
    ok = bool(t[:1].isupper() and t.rstrip().endswith(".") and len(_palavras(t)) >= 4)
    if ok:
        return True, "", ""
    return (
        False,
        "não é frase completa (maiúscula inicial, ponto final, ≥4 palavras)",
        t.strip(),
    )


def cd2_tempo_presente(t: str, lex: Lexico):
    """Característica 2 (parte 2): escrita no tempo presente."""
    for p in _palavras(t):
        b = p.lower()
        if b in lex.excecao_temporal:
            continue
        if b in lex.passado_irregular or PASSADO.fullmatch(b) or FUTURO.fullmatch(b):
            return False, f'verbo fora do presente: "{p}"', p
    return True, "", ""


def cd3_estado_nao_acao(t: str, lex: Lexico):
    """Característica 3: descrição do estado do sistema, não uma ação."""
    palavras = _palavras(t)
    primeira = palavras[0] if palavras else ""
    if INFINITIVO.fullmatch(primeira):
        return (
            False,
            f'a frase começa pela ação "{primeira}" (verbo no infinitivo)',
            primeira,
        )
    return True, "", ""


def cd4_nao_culpa(t: str, lex: Lexico):
    """Característica 6: não deve culpar alguém."""
    b = t.lower()
    for m in lex.culpa:
        if m in b:
            return False, f'atribui culpa a pessoas: "{m}"', m
    return True, "", ""


def cd5_nao_e_solucao(t: str, lex: Lexico):
    """Característica 8: não deve ser uma solução oculta."""
    b = t.lower()
    for m in lex.solucao_oculta:
        if m in b:
            return False, f'solução disfarçada de efeito: "{m.strip()}"', m.strip()
    return True, "", ""


def cd6_uma_entidade(t: str, lex: Lexico):
    """Característica 9: deve conter apenas uma entidade."""
    b = t.lower()
    for m in lex.coordenacao:
        if m in b:
            return False, f'duas entidades na mesma frase: "{m.strip()}"', m.strip()
    achado = RE_COORDENACAO.search(t)
    if achado:
        alvo = achado.group(0).strip()
        return False, f'duas entidades na mesma frase: "{alvo}"', alvo
    return True, "", ""


def cd7_sem_causa_embutida(t: str, lex: Lexico):
    """Característica 10: não deve incluir sua causa na verbalização.

    Procura DUAS coisas, e a segunda é a correção de um defeito medido:

    1. **conectivos** causais ("porque", "devido a", "já que"…) — o que
       `docs/produto/dados/medir-base.py:141-147` já procurava;
    2. **verbos** causais ("causa", "leva a", "resulta em", "provoca"…) — o que ele
       **não** procurava, e por isso aprovava "Falta de treinamento causa erros.",
       enunciado que a própria linhagem rotula como *Exemplo Ruim: UDE + Causa*
       (`tocbuilderv3/constants.ts:162`). Era o único falso negativo do conjunto de
       controle (`docs/produto/visao.md` §6, defeito D-12), e a visão declarou o destino:
       "tem de fechar o falso negativo K-03 — que hoje falha e é o caso de teste que
       nasce vermelho".

    A causa raiz do defeito está nomeada na visão e não é "faltou um marcador": é que a
    base autoral e as checagens tiveram o mesmo autor, então nenhum enunciado dela usava
    verbo causal. Por isso o remédio é a **família** do marcador, e não o caso avulso.

    Os verbos ambíguos ("causa", "causas" — verbo ou substantivo) só valem quando não vêm
    precedidos de determinante: sem essa guarda, "A causa do atraso permanece
    desconhecida" viraria um falso positivo, e trocar um defeito por outro não é fechar
    nada.
    """
    b = t.lower()
    for m in lex.causa_na_frase:
        if m in b:
            return False, f'traz a própria causa: "{m.strip()}"', m.strip()

    palavras = [p.lower() for p in _palavras(t)]
    for m in lex.verbos_causais:
        # Locuções ("leva a") têm de casar na sequência de palavras, não na cadeia crua:
        # a busca por subcadeia acharia "leva a" dentro de "eleva alunos".
        alvo = m.split()
        for indice in range(len(palavras) - len(alvo) + 1):
            if palavras[indice : indice + len(alvo)] == alvo:
                return False, f'traz a própria causa (verbo causal): "{m}"', m
    for m in lex.verbos_causais_ambiguos:
        for indice, palavra in enumerate(palavras):
            anterior = palavras[indice - 1] if indice else ""
            if palavra == m and anterior not in lex.determinantes:
                return False, f'traz a própria causa (verbo causal): "{m}"', m
    return True, "", ""


def cd8_factual(t: str, lex: Lexico):
    """Característica 11: deve ser factual, não subjetivo."""
    b = t.lower()
    for m in lex.subjetivo:
        if m in b:
            return False, f'juízo de valor: "{m.strip()}"', m.strip()
    return True, "", ""


# ---------------------------------------------------------------------------------------
# O catálogo — dado versionado do domínio (RF-09), não texto de prompt.
# ---------------------------------------------------------------------------------------

_DECIDIVEIS: tuple[tuple[Criterio, object], ...] = (
    (
        Criterio("CD-1", "2", "criterio.frase_completa", ClasseDeCriterio.DECIDIVEL,
                 "RN-01", "É uma frase completa."),
        cd1_frase_completa,
    ),
    (
        Criterio("CD-2", "2", "criterio.tempo_presente", ClasseDeCriterio.DECIDIVEL,
                 "RN-01", "Está escrita no tempo presente."),
        cd2_tempo_presente,
    ),
    (
        Criterio("CD-3", "3", "criterio.estado_nao_acao", ClasseDeCriterio.DECIDIVEL,
                 "RN-02", "Descreve o estado do sistema, não uma ação."),
        cd3_estado_nao_acao,
    ),
    (
        Criterio("CD-4", "6", "criterio.nao_culpa", ClasseDeCriterio.DECIDIVEL,
                 "RN-05", "Não culpa pessoa nem grupo."),
        cd4_nao_culpa,
    ),
    (
        Criterio("CD-5", "8", "criterio.nao_e_solucao", ClasseDeCriterio.DECIDIVEL,
                 "RN-04", "Não é uma solução oculta."),
        cd5_nao_e_solucao,
    ),
    (
        Criterio("CD-6", "9", "criterio.uma_entidade", ClasseDeCriterio.DECIDIVEL,
                 "RN-06", "Contém uma única entidade."),
        cd6_uma_entidade,
    ),
    (
        Criterio("CD-7", "10", "criterio.sem_causa_embutida", ClasseDeCriterio.DECIDIVEL,
                 "RN-03", "Não inclui a própria causa na verbalização."),
        cd7_sem_causa_embutida,
    ),
    (
        Criterio("CD-8", "11", "criterio.factual", ClasseDeCriterio.DECIDIVEL,
                 "RN-07", "É factual, não subjetivo."),
        cd8_factual,
    ),
)

#: As quatro que nenhuma função pura decide (`medir-base.py:170-175`). Declaradas aqui
#: para a ficha poder exibi-las como julgamento — o que separa esta ARA do prompt que
#: ela aposenta (spec 005, "Fora de escopo").
CRITERIOS_DE_JULGAMENTO: tuple[Criterio, ...] = (
    Criterio("J-1", "1", "criterio.queixa_continua", ClasseDeCriterio.JULGAMENTO,
             "RN-09", "É queixa sobre um problema contínuo que limita o desempenho."),
    Criterio("J-2", "4", "criterio.esfera_de_influencia", ClasseDeCriterio.JULGAMENTO,
             "RN-08", "Está dentro da área de responsabilidade ou influência."),
    Criterio("J-3", "5", "criterio.acionavel", ClasseDeCriterio.JULGAMENTO,
             "RN-08", "Algo pode ser feito a respeito."),
    Criterio("J-4", "7", "criterio.nao_e_causa_especulada", ClasseDeCriterio.JULGAMENTO,
             "RN-03", "Não é uma causa especulada."),
)

CRITERIOS_DECIDIVEIS: tuple[Criterio, ...] = tuple(c for c, _ in _DECIDIVEIS)
CRITERIOS: tuple[Criterio, ...] = CRITERIOS_DECIDIVEIS + CRITERIOS_DE_JULGAMENTO

MOTIVO_DE_JULGAMENTO = (
    "critério de julgamento: nenhuma função pura o decide — depende de parecer"
)


def validar_formalmente(texto: str, *, idioma: str = "pt") -> ValidacaoFormal:
    """Avalia um texto de UDE. Pura, offline, determinística (RNF-01, RNF-04)."""
    lex = lexico_de(idioma)
    alvo = texto or ""
    vereditos: list[VereditoDeCriterio] = []
    for criterio, checagem in _DECIDIVEIS:
        ok, motivo, trecho = checagem(alvo, lex)
        vereditos.append(
            VereditoDeCriterio(
                criterio=criterio,
                veredito=Veredito.ATENDE if ok else Veredito.NAO_ATENDE,
                motivo=motivo,
                trecho=trecho,
            )
        )
    for criterio in CRITERIOS_DE_JULGAMENTO:
        vereditos.append(
            VereditoDeCriterio(
                criterio=criterio,
                veredito=Veredito.INDETERMINADO,
                motivo=MOTIVO_DE_JULGAMENTO,
            )
        )
    return ValidacaoFormal(
        texto=alvo,
        idioma=lex.idioma,
        versao_do_lexico=lex.versao,
        vereditos=tuple(vereditos),
    )
