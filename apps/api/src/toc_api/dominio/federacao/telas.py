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
