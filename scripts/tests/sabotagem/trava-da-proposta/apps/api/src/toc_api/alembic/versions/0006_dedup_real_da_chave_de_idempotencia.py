"""Esqueleto da migração — o índice único nasce no banco, não só no modelo."""

revision = "0006"
down_revision = "0005"

NOME = "uq_proposta_de_acao_tenant_id_idempotency_key"


def upgrade() -> None:
    op.create_index(
        NOME,
        "proposta_de_acao",
        ["tenant_id", "idempotency_key"],
        unique=True,
        postgresql_where="idempotency_key is not null",
    )


def downgrade() -> None:
    op.drop_index(NOME, table_name="proposta_de_acao")
