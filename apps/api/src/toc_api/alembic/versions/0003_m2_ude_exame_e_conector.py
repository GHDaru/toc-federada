"""0003 — M2: marcador de Efeito Indesejável (UDE), ficha, parecer, exame de elo e conector E.

A spec 005 acrescenta ao núcleo do M1 a semântica da Árvore da Realidade Atual (ARA).
Cinco tabelas, e a ausência de uma sexta é decisão registrada: **a validação formal não é
persistida**. Ela é função pura e determinística do texto do nó
(`toc_api.dominio.criterios_ude`); gravá-la criaria uma segunda fonte de verdade que
envelheceria em silêncio na primeira mudança de versão do léxico. O que fica gravado é o
que não se recalcula — ficha, status (decisão humana), pareceres e exames.

A `reserva_obrigatoria` é a RF-22 imposta pelo banco além do domínio: um elo marcado
`insuficiente` ou `com_reserva` sem a reserva escrita não entra. O `uq_conector_aresta_unica`
é a RN-11 ("uma aresta pertence a no máximo um conector") pela mesma razão.

Revisão: 0003
Anterior: 0002
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.dialects.postgresql import UUID as PgUUID

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None

INSTANTE = sa.DateTime(timezone=True)


def upgrade() -> None:
    op.create_table(
        "ude",
        sa.Column("no_id", PgUUID(as_uuid=True), nullable=False),
        sa.Column("projeto_id", PgUUID(as_uuid=True), nullable=False),
        sa.Column("status", sa.Text(), nullable=False, server_default="pendente"),
        sa.Column("area_impactada", sa.Text(), nullable=False, server_default=""),
        sa.Column("objetivo_afetado", sa.Text(), nullable=False, server_default=""),
        sa.Column("evidencias", ARRAY(sa.Text()), nullable=False, server_default="{}"),
        sa.Column("frequencia", sa.Text(), nullable=False, server_default=""),
        sa.Column("impactos_estimados", sa.Text(), nullable=False, server_default=""),
        sa.PrimaryKeyConstraint("no_id", name="pk_ude"),
        sa.ForeignKeyConstraint(
            ["no_id"], ["no.id"], name="fk_ude_no_id_no", ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["projeto_id"], ["projeto.id"], name="fk_ude_projeto_id_projeto",
            ondelete="CASCADE",
        ),
        comment="Marcador de Efeito Indesejável e a ficha da TOC; um por nó marcado.",
    )
    op.create_index("ix_ude_projeto_id", "ude", ["projeto_id"])

    op.create_table(
        "ude_parecer",
        sa.Column("id", PgUUID(as_uuid=True), nullable=False),
        sa.Column("no_id", PgUUID(as_uuid=True), nullable=False),
        sa.Column("autor", sa.Text(), nullable=False),
        sa.Column("origem", sa.Text(), nullable=False),
        sa.Column("favoravel", sa.Boolean(), nullable=False),
        sa.Column("justificativa", sa.Text(), nullable=False),
        sa.Column("instante", INSTANTE, nullable=False),
        sa.Column("proposta_id", sa.Text(), nullable=True),
        sa.Column("criterios", ARRAY(sa.Text()), nullable=False, server_default="{}"),
        sa.PrimaryKeyConstraint("id", name="pk_ude_parecer"),
        sa.ForeignKeyConstraint(
            ["no_id"], ["ude.no_id"], name="fk_ude_parecer_no_id_ude",
            ondelete="CASCADE",
        ),
        comment=(
            "Parecer de julgamento, somente-acréscimo (RF-13). "
            "`origem`: humano|catalogo."
        ),
    )
    op.create_index("ix_ude_parecer_no_id", "ude_parecer", ["no_id"])

    op.create_table(
        "elo_exame",
        sa.Column("aresta_id", PgUUID(as_uuid=True), nullable=False),
        sa.Column("projeto_id", PgUUID(as_uuid=True), nullable=False),
        sa.Column("estado", sa.Text(), nullable=False, server_default="nao_examinado"),
        sa.Column("reserva", sa.Text(), nullable=False, server_default=""),
        sa.PrimaryKeyConstraint("aresta_id", name="pk_elo_exame"),
        sa.ForeignKeyConstraint(
            ["aresta_id"], ["aresta_causal.id"],
            name="fk_elo_exame_aresta_id_aresta_causal", ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["projeto_id"], ["projeto.id"], name="fk_elo_exame_projeto_id_projeto",
            ondelete="CASCADE",
        ),
        sa.CheckConstraint(
            "estado <> 'insuficiente' and estado <> 'com_reserva' or length(reserva) > 0",
            name="reserva_obrigatoria",
        ),
        comment=(
            "Exame de suficiência do elo; reserva obrigatória em "
            "insuficiente/com_reserva."
        ),
    )
    op.create_index("ix_elo_exame_projeto_id", "elo_exame", ["projeto_id"])

    op.create_table(
        "conector_e",
        sa.Column("id", PgUUID(as_uuid=True), nullable=False),
        sa.Column("projeto_id", PgUUID(as_uuid=True), nullable=False),
        sa.Column("destino_id", PgUUID(as_uuid=True), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_conector_e"),
        sa.ForeignKeyConstraint(
            ["projeto_id"], ["projeto.id"], name="fk_conector_e_projeto_id_projeto",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["destino_id"], ["no.id"], name="fk_conector_e_destino_id_no",
            ondelete="CASCADE",
        ),
        comment='Conector E (conjunção): "Se A e B, então C" — RN-11 da spec 005.',
    )
    op.create_index("ix_conector_e_projeto_id", "conector_e", ["projeto_id"])

    op.create_table(
        "conector_e_aresta",
        sa.Column("conector_id", PgUUID(as_uuid=True), nullable=False),
        sa.Column("aresta_id", PgUUID(as_uuid=True), nullable=False),
        sa.PrimaryKeyConstraint("conector_id", "aresta_id", name="pk_conector_e_aresta"),
        sa.ForeignKeyConstraint(
            ["conector_id"], ["conector_e.id"],
            name="fk_conector_e_aresta_conector_id_conector_e", ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["aresta_id"], ["aresta_causal.id"],
            name="fk_conector_e_aresta_aresta_id_aresta_causal", ondelete="CASCADE",
        ),
        sa.UniqueConstraint("aresta_id", name="uq_conector_aresta_unica"),
    )


def downgrade() -> None:
    op.drop_table("conector_e_aresta")
    op.drop_index("ix_conector_e_projeto_id", table_name="conector_e")
    op.drop_table("conector_e")
    op.drop_index("ix_elo_exame_projeto_id", table_name="elo_exame")
    op.drop_table("elo_exame")
    op.drop_index("ix_ude_parecer_no_id", table_name="ude_parecer")
    op.drop_table("ude_parecer")
    op.drop_index("ix_ude_projeto_id", table_name="ude")
    op.drop_table("ude")
