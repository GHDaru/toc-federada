"""0004 — M7: proposta de ação governada e traço de execução (spec 006).

Siglas, uma vez: **APH** — Aplicação ↔ Harness · **FSM** — máquina de estados finitos ·
**SQL** — *Structured Query Language*.

Duas tabelas, e serem duas é o requisito: a proposta é mutável (atravessa a FSM) e o traço
é **somente-acréscimo** (APH-5.5: existe para 100% das ações, inclusive as recusadas).
Guardar as duas coisas numa linha só faria a auditoria depender do estado corrente daquilo
que ela audita — e "o que a IA fez ontem" viraria "o que a proposta é hoje".

As restrições `origem_do_vocabulario`, `estado_da_fsm` e `desfecho_do_vocabulario_a3`
impõem **pelo banco** os vocabulários fechados do §A.3 e da FSM. Invariante que só vive no
código é invariante que a próxima ferramenta viola sem perceber — é o mesmo argumento das
restrições do M1 na migração 0002.

O que **não** entra aqui: o log de conversa do fio. Ele é de processo (o replay do APH-1.3
reconstrói a conversa dentro do processo que a atende) e está declarado assim em
`infra/federacao/memoria.py`. O que não pode ser volátil é a governança, e é ela que tem
tabela.

Revisão: 0004
Anterior: 0003
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.dialects.postgresql import UUID as PgUUID

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None

INSTANTE = sa.DateTime(timezone=True)


def upgrade() -> None:
    op.create_table(
        "proposta_de_acao",
        sa.Column("proposal_id", sa.Text(), nullable=False),
        sa.Column("tenant_id", sa.Text(), nullable=False),
        sa.Column("usuario_id", sa.Text(), nullable=False),
        sa.Column("action_id", sa.Text(), nullable=False),
        sa.Column("risk", sa.Text(), nullable=False),
        sa.Column("origem", sa.Text(), nullable=False),
        sa.Column("estado", sa.Text(), nullable=False),
        sa.Column("args", JSONB(), nullable=False, server_default="{}"),
        sa.Column("alvos", ARRAY(sa.Text()), nullable=False, server_default="{}"),
        sa.Column("contexto_hash", sa.Text(), nullable=True),
        sa.Column("criada_em", INSTANTE, nullable=False),
        sa.Column("vence_em", INSTANTE, nullable=False),
        sa.Column("decidida_em", INSTANTE, nullable=True),
        sa.Column("idempotency_key", sa.Text(), nullable=True),
        sa.Column("execucoes", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("desfecho_status", sa.Text(), nullable=True),
        sa.Column("desfecho_mensagem", sa.Text(), nullable=False, server_default=""),
        sa.Column("outcomes", JSONB(), nullable=False, server_default="[]"),
        sa.CheckConstraint("origem in ('humano','ia')", name="ck_proposta_de_acao_origem_do_vocabulario"),
        sa.CheckConstraint(
            "estado in ('proposed','awaiting_approval','confirmed','executing',"
            "'executed','failed','cancelled','denied','expired')",
            name="ck_proposta_de_acao_estado_da_fsm",
        ),
        sa.PrimaryKeyConstraint("proposal_id", name="pk_proposta_de_acao"),
        comment="Proposta de ação governada (APH-5.1); `estado` é a FSM validada em código.",
    )
    op.create_index(
        "ix_proposta_de_acao_tenant_id_estado", "proposta_de_acao", ["tenant_id", "estado"]
    )

    op.create_table(
        "traco_de_execucao",
        sa.Column("id", PgUUID(as_uuid=True), nullable=False),
        sa.Column("proposal_id", sa.Text(), nullable=False),
        sa.Column("action_id", sa.Text(), nullable=False),
        sa.Column("desfecho", sa.Text(), nullable=False),
        sa.Column("tenant_id", sa.Text(), nullable=False),
        sa.Column("usuario_id", sa.Text(), nullable=False),
        sa.Column("origem", sa.Text(), nullable=False),
        sa.Column("instante", INSTANTE, nullable=False),
        sa.Column("trace_id", sa.Text(), nullable=False, server_default=""),
        sa.Column("motivo", sa.Text(), nullable=False, server_default=""),
        sa.Column("outcomes", JSONB(), nullable=False, server_default="[]"),
        sa.CheckConstraint(
            "desfecho in ('executed','failed','denied','cancelled','expired')",
            name="ck_traco_de_execucao_desfecho_do_vocabulario_a3",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_traco_de_execucao"),
        comment="Traço somente-acréscimo; existe para 100% das ações, inclusive recusadas.",
    )
    op.create_index(
        "ix_traco_de_execucao_tenant_id_instante", "traco_de_execucao", ["tenant_id", "instante"]
    )


def downgrade() -> None:
    # A ordem inversa da criação, e sem resíduo: o portão da raia infra é
    # `alembic upgrade head && alembic downgrade base` num banco limpo terminando vazio.
    op.drop_index("ix_traco_de_execucao_tenant_id_instante", table_name="traco_de_execucao")
    op.drop_table("traco_de_execucao")
    op.drop_index("ix_proposta_de_acao_tenant_id_estado", table_name="proposta_de_acao")
    op.drop_table("proposta_de_acao")
