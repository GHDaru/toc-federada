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


# -- M4 · Árvores de Futuro e Implementação (spec 008) ----------------------------------
# Mesma decisão do M2 e do M3: os eventos moram AQUI, na fila única do agregado, porque a
# ordem entre `NoAdicionado`, `EfeitoEspelhouUde` e `RamoNegativoMarcado` é informação —
# ela conta como a árvore amadureceu, e um arquivo por módulo a perderia.
#
# Os eventos do **encadeamento** (E4.4) estão no fim deste bloco e são os que fecham o
# defeito D-11 da visão: nas quatro gerações da linhagem não havia UMA referência entre
# projetos (`grep -c "araProjectId\|sourceUdeId\|linkedProject\|crossTool" types.ts` → 0).
# Aqui a costura tem evento com autor, data e as duas pontas.


# --- E4.1 · Árvore da Realidade Futura -------------------------------------------------


@dataclass(frozen=True, slots=True)
class ArfCriada(EventoDeDominio):
    udes_da_cadeia: int = 0
    tipo_de_acao: str = "arf.criar"


@dataclass(frozen=True, slots=True)
class PapelNaArfMudou(EventoDeDominio):
    no_id: UUID | None = None
    de: str = ""
    para: str = ""
    tipo_de_acao: str = "arf.mudar_papel"


@dataclass(frozen=True, slots=True)
class EfeitoEspelhouUde(EventoDeDominio):
    """RN-03: o efeito futuro passa a ser Efeito Desejável de um UDE nomeado."""

    no_id: UUID | None = None
    ude_id: UUID | None = None
    tipo_de_acao: str = "arf.espelhar_ude"


@dataclass(frozen=True, slots=True)
class EspelhoDesfeito(EventoDeDominio):
    no_id: UUID | None = None
    ude_id: UUID | None = None
    tipo_de_acao: str = "arf.desfazer_espelho"


@dataclass(frozen=True, slots=True)
class RamoNegativoMarcado(EventoDeDominio):
    ramo_id: UUID | None = None
    raiz_id: UUID | None = None
    tipo_de_acao: str = "arf.marcar_ramo_negativo"


@dataclass(frozen=True, slots=True)
class RamoNegativoTratado(EventoDeDominio):
    """RN-04: tratar é NOMEAR a injeção que corta — sem ela não há transição."""

    ramo_id: UUID | None = None
    injecao_de_corte_id: UUID | None = None
    tipo_de_acao: str = "arf.tratar_ramo_negativo"


@dataclass(frozen=True, slots=True)
class RamoNegativoAceito(EventoDeDominio):
    ramo_id: UUID | None = None
    autor: str = ""
    justificativa: str = ""
    tipo_de_acao: str = "arf.aceitar_ramo_negativo"


@dataclass(frozen=True, slots=True)
class RamoNegativoReaberto(EventoDeDominio):
    """RN-04: `tratado` e `aceito` reabrem por ação explícita — e por exclusão da ponta.

    `automatico` distingue os dois: reabrir porque alguém decidiu é uma coisa; reabrir
    porque a injeção de corte foi excluída é outra, e some do relato se não for marcada.
    """

    ramo_id: UUID | None = None
    de: str = ""
    automatico: bool = False
    tipo_de_acao: str = "arf.reabrir_ramo_negativo"


@dataclass(frozen=True, slots=True)
class VerificacaoDaArfGerada(EventoDeDominio):
    """RF-13: o resumo quantitativo — grandeza, nunca o texto de quem escreveu."""

    resumo: dict = field(default_factory=dict)
    tipo_de_acao: str = "arf.verificar"


# --- E4.2 · Árvore de Pré-Requisitos ---------------------------------------------------


@dataclass(frozen=True, slots=True)
class AprCriada(EventoDeDominio):
    objetivo_id: UUID | None = None
    tipo_de_acao: str = "apr.criar"


@dataclass(frozen=True, slots=True)
class PapelNaAprMudou(EventoDeDominio):
    no_id: UUID | None = None
    de: str = ""
    para: str = ""
    tipo_de_acao: str = "apr.mudar_papel"


@dataclass(frozen=True, slots=True)
class ObstaculoPareado(EventoDeDominio):
    par_id: UUID | None = None
    obstaculo_id: UUID | None = None
    objetivo_intermediario_id: UUID | None = None
    tipo_de_acao: str = "apr.parear_obstaculo"


@dataclass(frozen=True, slots=True)
class ParDesfeito(EventoDeDominio):
    par_id: UUID | None = None
    tipo_de_acao: str = "apr.desfazer_par"


@dataclass(frozen=True, slots=True)
class TesteDeValidadeJulgado(EventoDeDominio):
    """RN-07: julgamento registrado como parecer com autor — nunca campo calculado."""

    par_id: UUID | None = None
    autor: str = ""
    valido: bool = False
    tipo_de_acao: str = "apr.julgar_teste_de_validade"


@dataclass(frozen=True, slots=True)
class ElipseFormada(EventoDeDominio):
    elipse_id: UUID | None = None
    destino_id: UUID | None = None
    dependencias: tuple[UUID, ...] = ()
    tipo_de_acao: str = "apr.formar_elipse"


@dataclass(frozen=True, slots=True)
class ElipseDesfeita(EventoDeDominio):
    elipse_id: UUID | None = None
    tipo_de_acao: str = "apr.desfazer_elipse"


@dataclass(frozen=True, slots=True)
class SequenciamentoGerado(EventoDeDominio):
    """RF-26: camadas, objetivos intermediários por camada e pendências."""

    resumo: dict = field(default_factory=dict)
    tipo_de_acao: str = "apr.sequenciar"


# --- E4.3 · Árvore de Transição --------------------------------------------------------


@dataclass(frozen=True, slots=True)
class AtCriada(EventoDeDominio):
    alvo_projeto_id: UUID | None = None
    alvo_no_id: UUID | None = None
    tipo_de_acao: str = "at.criar"


@dataclass(frozen=True, slots=True)
class PassoRegistrado(EventoDeDominio):
    no_id: UUID | None = None
    tipo_de_acao: str = "at.registrar_passo"


@dataclass(frozen=True, slots=True)
class FichaDePassoEditada(EventoDeDominio):
    no_id: UUID | None = None
    campos: tuple[str, ...] = ()
    tipo_de_acao: str = "at.editar_ficha_do_passo"


@dataclass(frozen=True, slots=True)
class PassoMudouDeStatus(EventoDeDominio):
    """RF-30: a divergência entre resultado esperado e real fica AQUI, não sobrescreve nada."""

    no_id: UUID | None = None
    de: str = ""
    para: str = ""
    motivo_do_bloqueio: str = ""
    resultado_real: str = ""
    divergente: bool = False
    tipo_de_acao: str = "at.mudar_status_do_passo"


# --- E4.4 · Encadeamento (a correção do D-11) ------------------------------------------


@dataclass(frozen=True, slots=True)
class ReferenciaCriada(EventoDeDominio):
    """RN-11: referência cruzada nasce SOMENTE por ação nomeada — e a ação fica no evento."""

    referencia_id: UUID | None = None
    tipo: str = ""
    origem_projeto_id: UUID | None = None
    destino_projeto_id: UUID | None = None
    tipo_de_acao: str = "cadeia.criar_referencia"


@dataclass(frozen=True, slots=True)
class ReferenciaSuspensa(EventoDeDominio):
    """RN-12: exclusão suave de uma ponta SUSPENDE — nunca apaga por efeito colateral."""

    referencia_id: UUID | None = None
    motivo: str = ""
    tipo_de_acao: str = "cadeia.suspender_referencia"


@dataclass(frozen=True, slots=True)
class ReferenciaReativada(EventoDeDominio):
    referencia_id: UUID | None = None
    tipo_de_acao: str = "cadeia.reativar_referencia"


@dataclass(frozen=True, slots=True)
class UdePromovidoParaNc(EventoDeDominio):
    """RF-36 (INT-05 da spec 007, executado aqui): o dilema por trás dos UDEs validados."""

    udes: tuple[UUID, ...] = ()
    nc_projeto_id: UUID | None = None
    referencia_id: UUID | None = None
    tipo_de_acao: str = "cadeia.promover_ude_para_nc"


@dataclass(frozen=True, slots=True)
class InjecaoSemeouArf(EventoDeDominio):
    """RF-38 (INT-06 da spec 007, executado aqui): a injeção escolhida vira nó semente."""

    injecao_id: UUID | None = None
    arf_projeto_id: UUID | None = None
    referencia_id: UUID | None = None
    tipo_de_acao: str = "cadeia.semear_arf"


@dataclass(frozen=True, slots=True)
class ArfDerivouApr(EventoDeDominio):
    origem_no_id: UUID | None = None
    apr_projeto_id: UUID | None = None
    referencia_id: UUID | None = None
    tipo_de_acao: str = "cadeia.derivar_apr"


@dataclass(frozen=True, slots=True)
class OiDerivouAt(EventoDeDominio):
    objetivo_intermediario_id: UUID | None = None
    at_projeto_id: UUID | None = None
    referencia_id: UUID | None = None
    tipo_de_acao: str = "cadeia.derivar_at"


# --- M6 · Focalização (spec 009) -------------------------------------------------------
#
# Somente-acréscimo, como todos os anteriores — e aqui a regra tem nome próprio na spec:
# RN-04, "histórico é apêndice, nunca sobrescrita". Nenhum destes eventos apaga outro;
# reabrir um passo emite `PassoReaberto` **ao lado** do `PassoConcluido` que já existia, e
# recomeçar emite `CicloFechado` sem tocar no que o ciclo guardava.


@dataclass(frozen=True, slots=True)
class AnaliseCriada(EventoDeDominio):
    """RF-01: a análise de focalização nasce com o sistema analisado nomeado."""

    sistema: str = ""
    tipo_de_acao: str = "focalizacao.criar_analise"


@dataclass(frozen=True, slots=True)
class CicloAberto(EventoDeDominio):
    """RF-02/RF-15: o ciclo abre em `identificar`, com os cinco passos instanciados."""

    ciclo_id: UUID | None = None
    ordem: int = 0
    herdadas: int = 0
    tipo_de_acao: str = "focalizacao.abrir_ciclo"


@dataclass(frozen=True, slots=True)
class CicloFechado(EventoDeDominio):
    """RN-04: fechar torna o ciclo somente leitura — e o conteúdo dele fica intacto."""

    ciclo_id: UUID | None = None
    ordem: int = 0
    decisoes: int = 0
    tipo_de_acao: str = "focalizacao.fechar_ciclo"


@dataclass(frozen=True, slots=True)
class RestricaoRegistrada(EventoDeDominio):
    """RF-05: a entidade que dá nome à teoria, com autoria por evento.

    `origem_projeto_id` e `origem_no_id` só vêm preenchidos quando a restrição nasceu de
    uma causa raiz de Árvore da Realidade Atual (RF-06) — a ferramenta ajuda, nunca
    condiciona, e o evento distingue os dois casos sem que ninguém precise adivinhar.
    """

    restricao_id: UUID | None = None
    ciclo_id: UUID | None = None
    tipo: str = ""
    autor: str = ""
    origem_ferramenta: str = ""
    origem_projeto_id: UUID | None = None
    origem_no_id: UUID | None = None
    tipo_de_acao: str = "focalizacao.registrar_restricao"


@dataclass(frozen=True, slots=True)
class RestricaoEditada(EventoDeDominio):
    """RF-07: descrição e justificativa. Trocar o alvo não é edição — é recomeço (RN-03)."""

    restricao_id: UUID | None = None
    campos: tuple[str, ...] = ()
    tipo_de_acao: str = "focalizacao.editar_restricao"


@dataclass(frozen=True, slots=True)
class PassoIniciado(EventoDeDominio):
    passo: str = ""
    ciclo_id: UUID | None = None
    tipo_de_acao: str = "focalizacao.iniciar_passo"


@dataclass(frozen=True, slots=True)
class PassoConcluido(EventoDeDominio):
    """RF-09: o avanço é um fato com autor, data e a decisão que o encerra."""

    passo: str = ""
    ciclo_id: UUID | None = None
    autor: str = ""
    decisao: str = ""
    tipo_de_acao: str = "focalizacao.concluir_passo"


@dataclass(frozen=True, slots=True)
class PassoReaberto(EventoDeDominio):
    """RF-10: reabrir NÃO apaga a decisão que havia concluído o passo."""

    passo: str = ""
    ciclo_id: UUID | None = None
    autor: str = ""
    justificativa: str = ""
    tipo_de_acao: str = "focalizacao.reabrir_passo"


@dataclass(frozen=True, slots=True)
class NotaRegistrada(EventoDeDominio):
    """RF-11: nota é acumulável e distinta da decisão de conclusão."""

    passo: str = ""
    nota_id: UUID | None = None
    autor: str = ""
    tipo_de_acao: str = "focalizacao.anotar_passo"


@dataclass(frozen=True, slots=True)
class VinculoCriado(EventoDeDominio):
    """RF-14/RN-06: o vínculo é tipado, e o evento diz se ele é canônico do passo."""

    vinculo_id: UUID | None = None
    passo: str = ""
    ferramenta: str = ""
    alvo_projeto_id: UUID | None = None
    canonico: bool = True
    tipo_de_acao: str = "focalizacao.vincular_ferramenta"


@dataclass(frozen=True, slots=True)
class VinculoRemovido(EventoDeDominio):
    vinculo_id: UUID | None = None
    passo: str = ""
    tipo_de_acao: str = "focalizacao.remover_vinculo"


@dataclass(frozen=True, slots=True)
class DecisaoHerdadaJulgada(EventoDeDominio):
    """RN-05: manter é decisão tão explícita quanto revogar — e as duas têm autor."""

    decisao_id: UUID | None = None
    ciclo_id: UUID | None = None
    passo_de_origem: str = ""
    veredito: str = ""
    autor: str = ""
    tipo_de_acao: str = "focalizacao.julgar_decisao_herdada"
