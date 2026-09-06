"""Esqueleto do modelo declarado — o índice único da chave de idempotência."""

proposta_de_acao = Table(
    "proposta_de_acao",
    metadados,
    Column("proposal_id", Text, primary_key=True),
    Column("idempotency_key", Text, nullable=True),
    Index(
        "uq_proposta_de_acao_tenant_id_idempotency_key",
        "tenant_id",
        "idempotency_key",
        unique=True,
        postgresql_where=text("idempotency_key is not null"),
    ),
)
