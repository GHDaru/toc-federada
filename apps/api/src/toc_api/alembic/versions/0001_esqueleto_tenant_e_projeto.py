"""0001 — esqueleto: referência de inquilino e o agregado projeto.

Escopo exatamente igual ao `specs/003-esqueleto-federado/data-model.md`: o suficiente para
provar identidade, isolamento e migração reversível. Nada do domínio TOC entra aqui —
"estoque é desperdício", nas palavras do próprio documento.

`apagado_em` nasce nesta migração embora a exclusão suave só passe a operar no ciclo 004.
O motivo está escrito no data-model e é de reversibilidade: se a coluna nascesse depois, o
`downgrade` da migração que a criasse teria de destruir dado.

Revisão: 0001
Anterior: (base)
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID as PgUUID

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None

INSTANTE = sa.DateTime(timezone=True)


def upgrade() -> None:
    op.create_table(
        "tenant_ref",
        sa.Column("tenant_id", sa.Text(), nullable=False),
        sa.Column("nome_exibicao", sa.Text(), nullable=True),
        sa.Column("visto_em", INSTANTE, nullable=False),
        sa.PrimaryKeyConstraint("tenant_id", name="pk_tenant_ref"),
        comment="Espelho mínimo do inquilino do hospedeiro; nunca fonte de autorização.",
    )
    op.create_table(
        "projeto",
        sa.Column("id", PgUUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", sa.Text(), nullable=False),
        sa.Column("nome", sa.Text(), nullable=False),
        sa.Column("ferramenta", sa.Text(), nullable=False),
        sa.Column("criado_em", INSTANTE, nullable=False),
        sa.Column("atualizado_em", INSTANTE, nullable=False),
        sa.Column("apagado_em", INSTANTE, nullable=True),
        sa.PrimaryKeyConstraint("id", name="pk_projeto"),
        sa.ForeignKeyConstraint(
            ["tenant_id"], ["tenant_ref.tenant_id"], name="fk_projeto_tenant_id_tenant_ref"
        ),
    )
    # O índice é do isolamento, não do desempenho: toda consulta filtra por inquilino
    # (invariante 1 do data-model), então a coluna líder é `tenant_id`.
    op.create_index(
        "ix_projeto_tenant_id_atualizado_em", "projeto", ["tenant_id", "atualizado_em"]
    )


def downgrade() -> None:
    op.drop_index("ix_projeto_tenant_id_atualizado_em", table_name="projeto")
    op.drop_table("projeto")
    op.drop_table("tenant_ref")
