"""Eventos de domínio — somente-acréscimo (spec 004, `data-model.md`).

Todo evento é congelado (`frozen=True`): depois de emitido, não se reescreve nem se
apaga. Quando uma mutação precisa ser desfeita, o que nasce é **outro** evento — o
compensatório (`MutacaoCompensada`), correlacionado ao original por `compensa_evento_id`.
É a regra herdada pronta da irmã `gestaodeprioridades` (ADR 0013 de lá), e é o motivo de
não existir aqui nenhum método que remova evento de lista nenhuma.

`tipo_de_acao` não é decoração: é **a chave da política** do RF-21 da spec 004 ("o portão
resolve por tipo de ação, nunca por origem alegada pelo cliente") e o nome que o ciclo 006
usa no catálogo `toc.*`. Por isso ele é declarado no próprio evento, e não inferido na
borda.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4

from .identidade import DonoDoProjeto


@dataclass(frozen=True, slots=True)
class EventoDeDominio:
    """Raiz de todo evento. Os campos comuns vêm do `data-model.md` do ciclo 004."""

    projeto_id: UUID
    dono: DonoDoProjeto
    instante: datetime
    evento_id: UUID = field(default_factory=uuid4)

    #: sufixo do nome do evento na política e no catálogo — sobrescrito por subclasse.
    tipo_de_acao: str = "desconhecida"


# -- projeto ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class ProjetoCriado(EventoDeDominio):
    nome: str = ""
    ferramenta: str = ""
    tipo_de_acao: str = "projeto.criar"


@dataclass(frozen=True, slots=True)
class MetadadosEditados(EventoDeDominio):
    campo: str = ""
    tipo_de_acao: str = "projeto.editar_metadados"


@dataclass(frozen=True, slots=True)
class ProjetoExcluido(EventoDeDominio):
    tipo_de_acao: str = "projeto.excluir"


@dataclass(frozen=True, slots=True)
class ProjetoRestaurado(EventoDeDominio):
    tipo_de_acao: str = "projeto.restaurar"


# -- nós -------------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class NoAdicionado(EventoDeDominio):
    no_id: UUID | None = None
    tipo: str = ""
    tipo_de_acao: str = "no.adicionar"


@dataclass(frozen=True, slots=True)
class NoEditado(EventoDeDominio):
    no_id: UUID | None = None
    campos: tuple[str, ...] = ()
    tipo_de_acao: str = "no.editar"


@dataclass(frozen=True, slots=True)
class NoMovido(EventoDeDominio):
    no_id: UUID | None = None
    tipo_de_acao: str = "no.mover"


@dataclass(frozen=True, slots=True)
class NoRecolhido(EventoDeDominio):
    no_id: UUID | None = None
    recolhido: bool = False
    tipo_de_acao: str = "no.recolher"


@dataclass(frozen=True, slots=True)
class NoExcluido(EventoDeDominio):
    """Carrega o RAIO: os identificadores das arestas removidas em cascata (RF-15)."""

    no_id: UUID | None = None
    arestas_removidas: tuple[UUID, ...] = ()
    tipo_de_acao: str = "no.excluir"


# -- arestas ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class ArestaLigada(EventoDeDominio):
    aresta_id: UUID | None = None
    origem_id: UUID | None = None
    destino_id: UUID | None = None
    tipo_de_acao: str = "aresta.ligar"


@dataclass(frozen=True, slots=True)
class ArestaEditada(EventoDeDominio):
    aresta_id: UUID | None = None
    tipo_de_acao: str = "aresta.editar"


@dataclass(frozen=True, slots=True)
class ArestaExcluida(EventoDeDominio):
    aresta_id: UUID | None = None
    tipo_de_acao: str = "aresta.excluir"


# -- compensação (desfazer / reverter) --------------------------------------------------


@dataclass(frozen=True, slots=True)
class MutacaoCompensada(EventoDeDominio):
    """O evento que desfazer e reverter produzem — nunca a remoção do original."""

    compensa_evento_id: UUID | None = None
    tipo_de_acao: str = "projeto.compensar"


# -- M2 · Árvore da Realidade Atual (spec 005) ------------------------------------------
# Ficam neste módulo, e não num `eventos_ara.py`, porque a fila de eventos do agregado é
# uma só: o M2 estende o M1 por composição (spec 005, "Entidades e modelo de domínio") e
# a ordem entre `NoAdicionado` e `UdeMarcado` é informação, não acidente.


@dataclass(frozen=True, slots=True)
class UdeMarcado(EventoDeDominio):
    no_id: UUID | None = None
    tipo_de_acao: str = "ude.marcar"


@dataclass(frozen=True, slots=True)
class UdeDesmarcado(EventoDeDominio):
    no_id: UUID | None = None
    tipo_de_acao: str = "ude.desmarcar"


@dataclass(frozen=True, slots=True)
class FichaDeUdeEditada(EventoDeDominio):
    no_id: UUID | None = None
    tipo_de_acao: str = "ude.editar_ficha"


@dataclass(frozen=True, slots=True)
class ValidacaoFormalExecutada(EventoDeDominio):
    """RF-10: mudou o texto, o evento guarda os DOIS — o anterior e o atual."""

    no_id: UUID | None = None
    texto: str = ""
    texto_anterior: str | None = None
    aprovado_nos_decidiveis: bool = False
    reprovacoes: tuple[str, ...] = ()
    versao_do_lexico: str = ""
    tipo_de_acao: str = "ude.validar_formalmente"


@dataclass(frozen=True, slots=True)
class ParecerRegistrado(EventoDeDominio):
    """RF-16: quem validou e quando vive em EVENTO, nunca em campo editável da ficha.

    O contraste é com a linhagem, onde `validado_por` era texto devolvido pelo modelo
    (`tocbuilderv3/types.ts:171-213`).
    """

    no_id: UUID | None = None
    autor: str = ""
    origem: str = ""
    favoravel: bool = False
    proposta_id: str | None = None
    tipo_de_acao: str = "ude.registrar_parecer"


@dataclass(frozen=True, slots=True)
class StatusDeValidacaoMudou(EventoDeDominio):
    no_id: UUID | None = None
    de: object = None
    para: object = None
    justificativa: str = ""
    tipo_de_acao: str = "ude.mudar_status"


@dataclass(frozen=True, slots=True)
class UdeArquivado(EventoDeDominio):
    """RF-05: excluir um nó marcado arquiva ficha e pareceres JUNTO ao evento."""

    no_id: UUID | None = None
    ficha: object = None
    pareceres: tuple = ()
    status: object = None
    tipo_de_acao: str = "ude.arquivar"


@dataclass(frozen=True, slots=True)
class EloExaminado(EventoDeDominio):
    aresta_id: UUID | None = None
    estado: object = None
    reserva: str = ""
    tipo_de_acao: str = "elo.examinar"


@dataclass(frozen=True, slots=True)
class ConectorEFormado(EventoDeDominio):
    conector_id: UUID | None = None
    destino_id: UUID | None = None
    arestas: tuple[UUID, ...] = ()
    tipo_de_acao: str = "conector_e.formar"


@dataclass(frozen=True, slots=True)
class ConectorEDesfeito(EventoDeDominio):
    conector_id: UUID | None = None
    tipo_de_acao: str = "conector_e.desfazer"


@dataclass(frozen=True, slots=True)
class AnaliseEstruturalGerada(EventoDeDominio):
    """RF-31: o resumo quantitativo, para a jornada e o traço mostrarem a evolução."""

    resumo: dict = field(default_factory=dict)
    tipo_de_acao: str = "ara.analisar"


# -- M3 · Nuvem de Conflito (spec 007) --------------------------------------------------
# Mesma decisão do M2: os eventos do M3 moram AQUI, e não num `eventos_nc.py`, porque a
# fila do agregado é uma só e a ordem entre `PremissaRegistrada` e `InjecaoRegistrada` é
# informação, não acidente.
#
# Dois campos aparecem em todo evento de conteúdo deste módulo e não existiam no M1/M2:
# `origem` (`humano` | `geracao`) e `proposta_id`. Eles são a RF-25 da spec 007 — "os
# eventos resultantes DEVEM declarar a origem (`geracao`, com a proposta) — distinguível
# de edição humana para sempre". Sem eles, um mês depois ninguém sabe qual premissa o
# grupo escreveu e qual veio de proposta aceita.
#
# O que NÃO está aqui é decisão registrada: `GeracaoProposta` e `GeracaoRecusada` não são
# eventos do agregado, porque **recusar não escreve nada no agregado** (RNF-06). Os dois
# vivem no registro de propostas e no traço da federação (ciclo 006), que é onde a
# história da governança mora.

ORIGEM_HUMANA = "humano"
ORIGEM_DE_GERACAO = "geracao"


@dataclass(frozen=True, slots=True)
class NuvemCriada(EventoDeDominio):
    """RF-02: a nuvem nasce inteira — o evento diz com quantas peças."""

    entidades: int = 0
    arestas: int = 0
    tipo_de_acao: str = "nc.criar"


@dataclass(frozen=True, slots=True)
class NuvemDerivadaDeUde(EventoDeDominio):
    """INT-05: a costura M2 → M3, tipada e datada, no lado que nasceu dela."""

    origem_ferramenta: str = ""
    origem_projeto_id: UUID | None = None
    udes: tuple[UUID, ...] = ()
    tipo_de_acao: str = "nc.derivar_de_ude"


@dataclass(frozen=True, slots=True)
class EntidadeEditada(EventoDeDominio):
    papel: str = ""
    origem: str = ORIGEM_HUMANA
    proposta_id: str | None = None
    tipo_de_acao: str = "nc.editar_entidade"


@dataclass(frozen=True, slots=True)
class RacionalEditado(EventoDeDominio):
    origem: str = ORIGEM_HUMANA
    proposta_id: str | None = None
    tipo_de_acao: str = "nc.editar_racional"


@dataclass(frozen=True, slots=True)
class PremissaRegistrada(EventoDeDominio):
    premissa_id: UUID | None = None
    aresta: str = ""
    origem: str = ORIGEM_HUMANA
    proposta_id: str | None = None
    tipo_de_acao: str = "nc.registrar_premissa"


@dataclass(frozen=True, slots=True)
class PremissaEditada(EventoDeDominio):
    premissa_id: UUID | None = None
    campo: str = "texto"
    origem: str = ORIGEM_HUMANA
    proposta_id: str | None = None
    tipo_de_acao: str = "nc.editar_premissa"


@dataclass(frozen=True, slots=True)
class PremissaDesafiada(EventoDeDominio):
    """RF-13: desafiar é registrar QUEM deixou de acreditar e POR QUÊ."""

    premissa_id: UUID | None = None
    justificativa: str = ""
    tipo_de_acao: str = "nc.desafiar_premissa"


@dataclass(frozen=True, slots=True)
class PremissaRevigorada(EventoDeDominio):
    premissa_id: UUID | None = None
    tipo_de_acao: str = "nc.revigorar_premissa"


@dataclass(frozen=True, slots=True)
class PremissaArquivada(EventoDeDominio):
    """RF-15: o evento carrega QUANTAS injeções foram junto — nunca em silêncio."""

    premissa_id: UUID | None = None
    injecoes_arquivadas: int = 0
    tipo_de_acao: str = "nc.arquivar_premissa"


@dataclass(frozen=True, slots=True)
class InjecaoRegistrada(EventoDeDominio):
    injecao_id: UUID | None = None
    premissa_id: UUID | None = None
    origem: str = ORIGEM_HUMANA
    proposta_id: str | None = None
    tipo_de_acao: str = "nc.registrar_injecao"


@dataclass(frozen=True, slots=True)
class InjecaoEditada(EventoDeDominio):
    injecao_id: UUID | None = None
    origem: str = ORIGEM_HUMANA
    proposta_id: str | None = None
    tipo_de_acao: str = "nc.editar_injecao"


@dataclass(frozen=True, slots=True)
class InjecaoReclassificada(EventoDeDominio):
    injecao_id: UUID | None = None
    separacao: str | None = None
    tipo_de_acao: str = "nc.classificar_injecao"


@dataclass(frozen=True, slots=True)
class StatusDeInjecaoMudou(EventoDeDominio):
    injecao_id: UUID | None = None
    de: str = ""
    para: str = ""
    justificativa: str = ""
    tipo_de_acao: str = "nc.mudar_status_de_injecao"


@dataclass(frozen=True, slots=True)
class GeracaoAplicada(EventoDeDominio):
    """RF-25: o que a proposta aceita escreveu, em grandeza, com o identificador dela."""

    proposta_id: str | None = None
    entidades: int = 0
    premissas: int = 0
    injecoes: int = 0
    tipo_de_acao: str = "nc.aplicar_geracao"
