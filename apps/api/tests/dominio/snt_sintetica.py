"""A árvore de Estratégia & Táticas (S&T) sintética da "Instituição Horizonte" (ADR 0006).

Siglas, uma vez neste arquivo: **S&T** — Estratégia & Táticas (*Strategy & Tactics*) ·
**TOC** — Teoria das Restrições · **ADR** — *Architecture Decision Record* (Registro de
Decisão Arquitetural) · **M5** — módulo Estratégia & Táticas.

Nenhum dado real de pessoa entra aqui: a instituição é fictícia, as personas são
"Facilitadora TOC" e "Gestora", e o plano é inventado para o teste. É a regra do
`CLAUDE.md` ("a base é sintética desde o dia 1") e o que `scripts/check-vazamento.sh`
confere.

**Três níveis**, porque três níveis é o portão do roadmap para o ciclo 010 (F-12 da spec
010): uma árvore de dois níveis não exercita a numeração `1.1.2` nem a premissa de
suficiência lida contra netos, e foi a numeração hierárquica que a linhagem entregou como
texto digitado à mão (`tocbuilderv3/types.ts:288`).

A forma do plano segue o método: cada passo diz **o quê** (estratégia) e **como** (tática),
e as três premissas lógicas sustentam o elo — a paralela (o que no contexto sustenta o
passo), a de necessidade contra o pai, a de suficiência contra os filhos.
"""
from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from toc_api.dominio.identidade import DonoDoProjeto

AGORA = datetime(2026, 9, 6, 9, 0, tzinfo=timezone.utc)

DONO = DonoDoProjeto(inquilino_id="instituicao-horizonte", usuario_id="u-facilitadora")
OUTRO_DONO = DonoDoProjeto(inquilino_id="instituicao-aurora", usuario_id="u-aurora-01")

ID_DA_ARVORE = UUID("55555555-5555-4555-8555-555555555501")

NOME = "Dobrar a capacidade de atendimento"

META_GLOBAL = (
    "Dobrar a capacidade de atendimento da Instituição Horizonte em doze meses sem "
    "perder a qualidade acadêmica que sustenta a reputação dela."
)

#: `(chave, chave do pai, estratégia, tática)` na ordem em que os passos entram na árvore.
#: A ordem importa: é dela que a numeração deriva (RN-01), e é ela que o teste de
#: renumeração perturba.
PLANO: tuple[tuple[str, str | None, str, str], ...] = (
    (
        "1",
        None,
        "Atender o dobro de pessoas com a estrutura atual",
        "Trabalhar as três frentes — fluxo, equipe e demanda — na mesma cadência trimestral",
    ),
    (
        "1.1",
        "1",
        "Reduzir o tempo de espera do atendimento pela metade",
        "Medir a fila semanalmente e atacar a etapa mais lenta a cada quinzena",
    ),
    (
        "1.1.1",
        "1.1",
        "Enxergar a fila em tempo real",
        "Publicar um painel de fila alimentado pelo próprio sistema de agendamento",
    ),
    (
        "1.1.2",
        "1.1",
        "Eliminar a espera por conferência documental",
        "Conferir documentos na entrada, e não na véspera do atendimento",
    ),
    (
        "1.2",
        "1",
        "Formar a equipe necessária sem contratar em massa",
        "Formar internamente duas turmas de multiplicadores por semestre",
    ),
    (
        "1.2.1",
        "1.2",
        "Ter quem ensine dentro de casa",
        "Selecionar multiplicadores entre quem já executa o atendimento hoje",
    ),
    (
        "1.3",
        "1",
        "Sustentar a demanda nova sem quebrar a qualidade",
        "Abrir vagas por lote, com revisão de qualidade a cada lote",
    ),
)

#: As premissas do passo `1.1` — as três, nos três papéis, para a fixture exercitar a
#: leitura dirigida (RF-13) sem depender de dado de pessoa nenhum.
PREMISSAS_DE_1_1 = {
    "paralela": (
        "a fila é hoje o gargalo do atendimento, e não a falta de sala"
    ),
    "necessidade_ao_pai": (
        "sem cortar a espera, o dobro de pessoas só faz a fila dobrar junto"
    ),
    "suficiencia_dos_filhos": (
        "enxergar a fila e tirar a conferência do caminho crítico cobrem as duas "
        "únicas etapas que hoje respondem por mais de 80% da espera"
    ),
}

#: O que a Gestora conduz na reunião de acompanhamento — status por chave de passo.
STATUS_NA_REUNIAO = {
    "1.1": "em_execucao",
    "1.1.1": "validado",
    "1.1.2": "nao_validado",
}


def numeros_esperados() -> tuple[str, ...]:
    """Os números que a árvore sintética TEM de produzir — a chave é o próprio número."""
    return tuple(chave for chave, _, _, _ in PLANO)
