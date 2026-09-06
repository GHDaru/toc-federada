"""O registro de telas — fonte de verdade compartilhada entre interface e serviço (APH-3.1).

Siglas, uma vez: **APH** — Aplicação ↔ Harness · **UI** — interface de usuário · **DOM** —
*Document Object Model*.

A inteligência artificial **nunca infere a interface**: não raspa DOM, não olha captura de
tela. Ela sabe em que tela a pessoa está porque a tela está declarada aqui, com identidade,
rota, campos tipados e ações. Quem monta o snapshot consulta este registro, e o que não
está declarado não atravessa (a terceira camada da sanitização do APH-3.3).

Uma cláusula que é fácil de ler e fácil de esquecer: **tela com `ai_actions: []` é item
sensível e NÃO DEVE entrar em snapshot** (§B.5.3 do Anexo B). `toc.configuracao` é o caso
concreto — é a tela que mostra parâmetros de embarque, e ela não vai para modelo nenhum.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from ..erros import ErroDeDominio

PREFIXO_DO_APP = "toc"
FORMA_DE_ID = re.compile(rf"^{PREFIXO_DO_APP}\.[a-z][a-z0-9_]*$")

# O vocabulário fechado do schema normativo do manifesto (quatro valores).
ACOES_DE_IA: frozenset[str] = frozenset({"READ", "FILL_FIELDS", "SUBMIT", "NAVIGATE"})

# Vocabulário de tipo de campo do §A.4.
TIPOS_DE_CAMPO: frozenset[str] = frozenset(
    {"text", "number", "boolean", "date", "select", "entity", "other"}
)


class TelaDesconhecida(ErroDeDominio):
    """A tela não está no registro."""


@dataclass(frozen=True, slots=True)
class CampoDeTela:
    """Um campo declarado. `ai_visible: False` é omissão deliberada, não esquecimento."""

    name: str
    type: str
    ai_visible: bool = True
    label: str = ""

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("campo sem nome")
        if self.type not in TIPOS_DE_CAMPO:
            raise ValueError(f"{self.name}: tipo {self.type!r} fora do vocabulário do §A.4")


@dataclass(frozen=True, slots=True)
class Tela:
    """Uma tela do registro. A forma é a do §B.5.2, verificada na construção."""

    id: str
    route: str
    title: str
    ai_actions: tuple[str, ...] = ()
    campos: tuple[CampoDeTela, ...] = ()

    def __post_init__(self) -> None:
        if not FORMA_DE_ID.match(self.id):
            raise ValueError(f"id de tela {self.id!r} fora da forma <ns>.<id> com ns='toc'")
        if not self.route.startswith(f"/{PREFIXO_DO_APP}/") or self.route != self.route.lower():
            raise ValueError(f"rota {self.route!r} fora da forma canônica sob /toc/ (RF-02)")
        if self.route.endswith("/"):
            raise ValueError(f"rota {self.route!r} com barra final")
        fora = set(self.ai_actions) - ACOES_DE_IA
        if fora:
            raise ValueError(f"{self.id}: ai_actions fora do vocabulário fechado: {sorted(fora)}")

    @property
    def sensivel(self) -> bool:
        """§B.5.3: `ai_actions: []` marca item sensível — não entra em snapshot algum."""
        return not self.ai_actions

    def campo(self, nome: str) -> CampoDeTela | None:
        for campo in self.campos:
            if campo.name == nome:
                return campo
        return None

    def como_manifesto(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "route": self.route,
            "title": self.title,
            "ai_actions": list(self.ai_actions),
        }


@dataclass(frozen=True)
class RegistroDeTelas:
    telas: tuple[Tela, ...]

    def tela(self, tela_id: str) -> Tela:
        for tela in self.telas:
            if tela.id == tela_id:
                return tela
        raise TelaDesconhecida(tela_id)

    def procurar(self, tela_id: str) -> Tela | None:
        try:
            return self.tela(tela_id)
        except TelaDesconhecida:
            return None

    def como_manifesto(self) -> list[dict[str, Any]]:
        return [t.como_manifesto() for t in self.telas]


# O registro. Os títulos são exatamente os do `contracts/manifesto.json` (sem acento, como
# lá) porque o teste de paridade compara campo a campo — e a paridade é o requisito RF-36.
REGISTRO_DE_TELAS = RegistroDeTelas(
    (
        Tela(
            id="toc.projetos",
            route="/toc/projetos",
            title="Projetos",
            ai_actions=("READ", "NAVIGATE"),
            campos=(
                CampoDeTela("filtro_ferramenta", "text", label="Ferramenta"),
                CampoDeTela("quantidade_de_projetos", "number", label="Projetos listados"),
                CampoDeTela("projeto_selecionado", "entity", label="Projeto selecionado"),
            ),
        ),
        Tela(
            id="toc.ara",
            route="/toc/ara",
            title="Arvore da Realidade Atual",
            ai_actions=("READ", "FILL_FIELDS", "SUBMIT", "NAVIGATE"),
            campos=(
                CampoDeTela("projeto_id", "text", label="Projeto"),
                CampoDeTela("nos_visiveis", "number", label="Nós visíveis"),
                CampoDeTela("no_selecionado", "entity", label="Nó selecionado"),
                # O parecer em rascunho é julgamento humano em andamento (spec 005, RF-13).
                # Ele não é segredo — é opinião ainda não registrada, e mandá-la ao modelo
                # transformaria a assistência em espelho da própria dúvida de quem escreve.
                CampoDeTela("rascunho_de_parecer", "text", ai_visible=False),
            ),
        ),
        # M4 — Árvores de Futuro e Implementação (spec 008, INT-09). Os textos de efeito,
        # obstáculo, objetivo intermediário, passo e justificativa são `ai_visible` campo a
        # campo; o que fica de fora fica declarado, como o rascunho de parecer do M2.
        Tela(
            id="toc.arf_canvas",
            route="/toc/arf",
            title="Arvore da Realidade Futura",
            ai_actions=("READ", "FILL_FIELDS", "SUBMIT", "NAVIGATE"),
            campos=(
                CampoDeTela("projeto_id", "text", label="Projeto"),
                CampoDeTela("injecoes", "number", label="Injeções"),
                CampoDeTela("efeitos_futuros", "number", label="Efeitos futuros"),
                CampoDeTela("no_selecionado", "entity", label="Nó selecionado"),
                CampoDeTela("ramos_abertos", "number", label="Ramos negativos abertos"),
                # A justificativa de um ramo ACEITO é a decisão de alguém de conviver com
                # um efeito colateral. Ela é registro de responsabilidade, e mandá-la ao
                # modelo transformaria a assistência em juíza da decisão — não é o papel.
                CampoDeTela("justificativa_do_aceite", "text", ai_visible=False),
            ),
        ),
        Tela(
            id="toc.apr_canvas",
            route="/toc/apr",
            title="Arvore de Pre-Requisitos",
            ai_actions=("READ", "FILL_FIELDS", "SUBMIT", "NAVIGATE"),
            campos=(
                CampoDeTela("projeto_id", "text", label="Projeto"),
                CampoDeTela("objetivo", "text", label="Objetivo"),
                CampoDeTela("obstaculos", "number", label="Obstáculos"),
                CampoDeTela("objetivos_intermediarios", "number", label="Objetivos intermediários"),
                CampoDeTela("no_selecionado", "entity", label="Nó selecionado"),
                # O julgamento do teste de validade é humano por regra (RN-07). Em
                # rascunho, ele é opinião ainda não registrada — a mesma decisão do
                # `rascunho_de_parecer` do M2.
                CampoDeTela("rascunho_de_julgamento", "text", ai_visible=False),
            ),
        ),
        Tela(
            id="toc.apr_sequencia",
            route="/toc/apr/sequencia",
            title="Sequenciamento da Arvore de Pre-Requisitos",
            ai_actions=("READ", "NAVIGATE"),
            campos=(
                CampoDeTela("projeto_id", "text", label="Projeto"),
                CampoDeTela("camadas", "number", label="Camadas"),
                CampoDeTela("pendencias", "number", label="Pendências"),
                CampoDeTela("bloqueado", "boolean", label="Sequência bloqueada"),
            ),
        ),
        Tela(
            id="toc.at_canvas",
            route="/toc/at",
            title="Arvore de Transicao",
            ai_actions=("READ", "FILL_FIELDS", "SUBMIT", "NAVIGATE"),
            campos=(
                CampoDeTela("projeto_id", "text", label="Projeto"),
                CampoDeTela("passos", "number", label="Passos"),
                CampoDeTela("passo_selecionado", "entity", label="Passo selecionado"),
                CampoDeTela("bloqueados", "number", label="Passos bloqueados"),
            ),
        ),
        Tela(
            id="toc.cadeia",
            route="/toc/cadeia",
            title="Vista da cadeia",
            ai_actions=("READ", "NAVIGATE"),
            campos=(
                CampoDeTela("projeto_id", "text", label="Projeto de partida"),
                CampoDeTela("elos", "number", label="Elos"),
                CampoDeTela("elos_pendentes", "number", label="Elos pendentes"),
            ),
        ),
        # M6 — Focalização (spec 009, INT-06). Três telas, e a regra que decide o
        # `ai_visible` é a mesma dos módulos anteriores: **grandeza e vocabulário sim,
        # texto de pessoa não**. Passo atual, tipo de restrição e contagem de pendências
        # descrevem ONDE a análise está; a descrição da restrição, as notas e as decisões
        # são o que o grupo escreveu — e é o item 7 da constituição ("tela é dado e nunca
        # instrução"): texto de usuário é sempre camada não-confiável.
        Tela(
            id="toc.foco_jornada",
            route="/toc/focalizacao",
            title="Jornada dos cinco passos",
            ai_actions=("READ", "NAVIGATE"),
            campos=(
                CampoDeTela("projeto_id", "text", label="Análise"),
                CampoDeTela("ciclo", "number", label="Ciclo"),
                CampoDeTela("passo_atual", "select", label="Passo atual"),
                CampoDeTela("passos_concluidos", "number", label="Passos concluídos"),
                CampoDeTela("tipo_de_restricao", "select", label="Tipo da restrição"),
                CampoDeTela("pendencias", "number", label="Pendências"),
                CampoDeTela("herancas_pendentes", "number", label="Vereditos pendentes"),
                # O enunciado da restrição é texto de quem facilitou a sessão. Ele não é
                # segredo — é conteúdo do inquilino, e a assistência só o recebe quando a
                # pessoa o coloca numa ação governada, nunca por raspagem de tela.
                CampoDeTela("descricao_da_restricao", "text", ai_visible=False),
            ),
        ),
        Tela(
            id="toc.foco_passo",
            route="/toc/focalizacao/passo",
            title="Painel do passo",
            ai_actions=("READ", "NAVIGATE"),
            campos=(
                CampoDeTela("projeto_id", "text", label="Análise"),
                CampoDeTela("passo", "select", label="Passo"),
                CampoDeTela("estado", "select", label="Estado do passo"),
                CampoDeTela("vinculos", "number", label="Vínculos de ferramenta"),
                CampoDeTela("vinculos_nao_canonicos", "number", label="Vínculos com aviso"),
                # A decisão que encerra um passo e as notas do grupo são o trabalho da
                # sessão. Mesma decisão do `rascunho_de_parecer` do M2, pelo mesmo motivo.
                CampoDeTela("decisao_em_rascunho", "text", ai_visible=False),
                CampoDeTela("notas", "text", ai_visible=False),
            ),
        ),
        Tela(
            id="toc.foco_linha_do_tempo",
            route="/toc/focalizacao/linha-do-tempo",
            title="Linha do tempo dos ciclos",
            ai_actions=("READ",),
            campos=(
                CampoDeTela("projeto_id", "text", label="Análise"),
                CampoDeTela("ciclos", "number", label="Ciclos"),
                CampoDeTela("ciclos_fechados", "number", label="Ciclos fechados"),
            ),
        ),
        Tela(
            id="toc.lixeira",
            route="/toc/lixeira",
            title="Lixeira",
            ai_actions=("READ",),
            campos=(CampoDeTela("itens_na_lixeira", "number", label="Itens na lixeira"),),
        ),
        Tela(
            id="toc.configuracao",
            route="/toc/configuracao",
            title="Configuracao do embarque",
            ai_actions=(),
            campos=(
                CampoDeTela("host_origin", "text", ai_visible=False),
                CampoDeTela("app_id", "text", ai_visible=False),
            ),
        ),
    )
)
