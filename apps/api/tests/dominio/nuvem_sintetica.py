"""O dilema sintético da "Instituição Horizonte" — a fixture do M3 (ADR 0006).

Siglas, uma vez neste arquivo: **NC** — Nuvem de Conflito · **TOC** — Teoria das
Restrições · **UDE** — Efeito Indesejável · **ADR** — *Architecture Decision Record*
(Registro de Decisão Arquitetural).

Nenhum dado real de pessoa entra aqui: a instituição é fictícia, as personas são
"Facilitadora TOC" e "Gestora", e o dilema é inventado para o teste. É a regra do
`CLAUDE.md` ("a base é sintética desde o dia 1") e o que `scripts/check-vazamento.sh`
confere.

O dilema respeita as regras de formulação do método (skill `toc-evaporating-cloud`):
A ⊇ C ⊇ B, com A, B e C em substantivo e D/D′ em infinitivo verbal, D′ negando D.
"""
from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from toc_api.dominio.identidade import DonoDoProjeto
from toc_api.dominio.nuvem import PapelDaEntidade

AGORA = datetime(2026, 9, 5, 12, 0, tzinfo=timezone.utc)

DONO = DonoDoProjeto(inquilino_id="instituicao-horizonte", usuario_id="u-horizonte-01")
OUTRO_DONO = DonoDoProjeto(inquilino_id="instituicao-aurora", usuario_id="u-aurora-01")

ID_DA_NUVEM = UUID("77777777-7777-4777-8777-777777777771")

NOME = "Dilema da expansão"

#: Os cinco textos do dilema sintético, na forma canônica do método.
DILEMA: dict[PapelDaEntidade, str] = {
    PapelDaEntidade.A: "Sustentabilidade da Instituição Horizonte",
    PapelDaEntidade.B: "Receita nova no próximo semestre",
    PapelDaEntidade.C: "Reputação acadêmica preservada",
    PapelDaEntidade.D: "Abrir turmas em três cidades novas",
    PapelDaEntidade.D_PRIME: "Não abrir turmas em três cidades novas",
}

NARRATIVA = (
    "A Instituição Horizonte precisa de receita nova já no próximo semestre para se "
    "sustentar. A direção quer abrir turmas em três cidades novas. O corpo docente teme "
    "que abrir turmas sem professores formados derrube a reputação acadêmica, e propõe "
    "não abrir turmas agora. As duas decisões disputam o mesmo orçamento."
)

#: Os enunciados de Efeito Indesejável da Árvore da Realidade Atual sintética que motivam
#: a nuvem — usados no teste do encadeamento M2 → M3.
UDES_SINTETICOS = (
    "A taxa de evasão no primeiro semestre é de 22%.",
    "O caixa da instituição fecha o trimestre negativo.",
)


def texto(papel: PapelDaEntidade) -> str:
    return DILEMA[papel]
