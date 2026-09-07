"""0009 — M5: a árvore de Estratégia & Táticas (S&T).

Siglas, uma vez neste arquivo: **S&T** — Estratégia & Táticas (*Strategy & Tactics*) ·
**M1** — Núcleo de Diagramas Lógicos · **M5** — o módulo da S&T · **RN/RF/RNF** — regra de
negócio / requisito funcional / requisito não funcional da spec 010.

A spec 010 acrescenta ao núcleo **um tipo de projeto e duas tabelas**, e o que essas duas
tabelas **não** têm é a decisão central do módulo:

1. **Não há coluna de número.** Na quarta geração da linhagem o número do passo era texto
   digitado à mão (`tocbuilderv3/types.ts:288`: `stepNumber: string; // e.g., "1", "1.1",
   "1.1.2"`), obrigatório e sem validação de formato ou unicidade
   (`tocbuilderv3/components/SnTStepEditorModal.tsx:56-57`) — e nenhuma das dez funções de
   serviço da geração o calculava ou conferia. Aqui grava-se `(pai_id, ordem)`, e o número
   é calculado da estrutura na leitura (RN-01). Não existe lugar onde estrutura e número
   possam discordar, porque só existe um deles no banco.
2. **Não há tabela de aresta.** A linhagem reusava `AraEdge` "por simplicidade"
   (`tocbuilderv3/types.ts:310`), o que admitia topologias que não são árvore. Aqui o pai
   é coluna do próprio passo: multi-pai e ciclo ficam irrepresentáveis, não "recusados por
   código".

E três invariantes do domínio entram como restrição de banco, pelo mesmo motivo das
migrações anteriores — invariante que só vive no código é invariante que a próxima
ferramenta viola sem perceber:

- **ordem única entre irmãos**, em duas peças: `uq_snt_passo_ordem_entre_irmaos` para os
  filhos e o índice **parcial** `uq_snt_passo_raiz_ordem` para as raízes. A segunda peça
  existe porque, em SQL, `NULL` não é igual a `NULL`: a restrição única normal deixaria as
  raízes de fora, e é justamente nas raízes que a numeração `1..n` começa.
- **estratégia nunca vazia** (RF-11) e **meta global nunca vazia** (RF-01);
- **status e categoria em vocabulário fechado** — os quatro valores da linhagem
  (`tocbuilderv3/types.ts:270-275`) e os seis da classificação (`:277-284`, portada como
  rótulo opcional pelo ADR 0014).

Revisão: 0009
Anterior: 0008 (M6 — a jornada dos cinco passos de focalização)
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID as PgUUID

revision = "0009"
down_revision = "0008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "snt_arvore",
        sa.Column("projeto_id", PgUUID(as_uuid=True), nullable=False),
        sa.Column("meta_global", sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint("projeto_id", name="pk_snt_arvore"),
        sa.ForeignKeyConstraint(
            ["projeto_id"], ["projeto.id"], name="fk_snt_arvore_projeto_id_projeto",
            ondelete="CASCADE",
        ),
        sa.CheckConstraint("length(btrim(meta_global)) > 0", name="meta_global_obrigatoria"),
        comment=(
            "Cabeçalho da árvore de Estratégia & Táticas: a meta global que os passos "
            "decompõem (RF-01). Uma linha por projeto do tipo snt."
        ),
    )

    op.create_table(
        "snt_passo",
        sa.Column("no_id", PgUUID(as_uuid=True), nullable=False),
        sa.Column("projeto_id", PgUUID(as_uuid=True), nullable=False),
        sa.Column("pai_id", PgUUID(as_uuid=True), nullable=True),
        sa.Column("ordem", sa.Integer(), nullable=False),
        sa.Column("estrategia", sa.Text(), nullable=False),
        sa.Column("tatica", sa.Text(), nullable=False, server_default=""),
        sa.Column("categoria", sa.Text(), nullable=False, server_default="nenhuma"),
        sa.Column("status", sa.Text(), nullable=False, server_default="nenhum"),
        sa.Column("premissa_paralela", sa.Text(), nullable=False, server_default=""),
        sa.Column(
            "premissa_necessidade_ao_pai", sa.Text(), nullable=False, server_default=""
        ),
        sa.Column(
            "premissa_suficiencia_dos_filhos", sa.Text(), nullable=False, server_default=""
        ),
        sa.PrimaryKeyConstraint("no_id", name="pk_snt_passo"),
        sa.ForeignKeyConstraint(
            ["no_id"], ["no.id"], name="fk_snt_passo_no_id_no", ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["projeto_id"], ["projeto.id"], name="fk_snt_passo_projeto_id_projeto",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["pai_id"], ["no.id"], name="fk_snt_passo_pai_id_no", ondelete="CASCADE"
        ),
        sa.CheckConstraint("length(btrim(estrategia)) > 0", name="estrategia_obrigatoria"),
        sa.CheckConstraint("ordem >= 0", name="ordem_nao_negativa"),
        sa.CheckConstraint("pai_id is null or pai_id <> no_id", name="pai_diferente_do_passo"),
        sa.CheckConstraint(
            "status in ('nenhum', 'validado', 'nao_validado', 'em_execucao')",
            name="status_do_passo_snt",
        ),
        sa.CheckConstraint(
            "categoria in ('nenhuma', 'estrategia', 'tatica', 'vcd', 'build', 'leverage')",
            name="categoria_do_passo_snt",
        ),
        sa.UniqueConstraint(
            "projeto_id", "pai_id", "ordem", name="uq_snt_passo_ordem_entre_irmaos"
        ),
        comment=(
            "Passo da S&T: estratégia, tática, as três premissas, status e a POSIÇÃO "
            "(pai + ordem). Sem coluna de número — a numeração deriva da estrutura (RN-01)."
        ),
    )
    op.create_index("ix_snt_passo_projeto_id", "snt_passo", ["projeto_id"])
    op.create_index("ix_snt_passo_pai_id", "snt_passo", ["pai_id"])
    # A metade que falta da ordem única: em SQL, `NULL` não é igual a `NULL`, então a
    # restrição única acima **não** cobre as raízes. Sem este índice parcial, duas raízes
    # poderiam gravar a mesma ordem e a numeração `1..n` deixaria de ser determinística
    # entre leituras — que é justamente a propriedade que a RN-01 promete.
    op.create_index(
        "uq_snt_passo_raiz_ordem",
        "snt_passo",
        ["projeto_id", "ordem"],
        unique=True,
        postgresql_where=sa.text("pai_id is null"),
    )


def downgrade() -> None:
    op.drop_index("uq_snt_passo_raiz_ordem", "snt_passo")
    op.drop_index("ix_snt_passo_pai_id", "snt_passo")
    op.drop_index("ix_snt_passo_projeto_id", "snt_passo")
    op.drop_table("snt_passo")
    op.drop_table("snt_arvore")
