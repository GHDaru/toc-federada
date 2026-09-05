"""0005 — M3: Nuvem de Conflito (racional, costura de origem, premissas e injeções).

A spec 007 acrescenta ao núcleo a semântica da Nuvem de Conflito (NC). **Três** tabelas, e
a ausência de duas outras é decisão registrada, não esquecimento:

- **não há tabela de entidade nem de aresta da nuvem**: as 5 entidades são linhas de `no`
  cujo `tipo` carrega o papel (`nc_a` … `nc_d_prime`) e as 7 arestas são linhas de
  `aresta_causal`; a chave (`A_B`, `D_C`, …) é derivada do par de papéis no domínio. Uma
  coluna de chave seria segunda fonte de verdade para a topologia fixa (RN-01);
- **não há coluna "tem semeadura"**: a referência de semeadura (INT-06) existe exatamente
  quando a injeção está `escolhida`, e o que se grava é o destino — que o ciclo 008
  preencherá.

As restrições `premissa_nao_vazia`, `justificativa_do_desafio` e o `NOT NULL` de
`nc_injecao.premissa_id` são as regras RF-12, RF-13 e RN-04 impostas **pelo banco** além
do domínio: invariante que só vive no código é invariante que a próxima ferramenta viola
sem perceber.

Revisão: 0005
Anterior: 0004 (federação: proposta e traço)
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.dialects.postgresql import UUID as PgUUID

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "nc_nuvem",
        sa.Column("projeto_id", PgUUID(as_uuid=True), nullable=False),
        sa.Column("racional", sa.Text(), nullable=False, server_default=""),
        sa.Column("origem_ferramenta", sa.Text(), nullable=True),
        sa.Column("origem_projeto_id", PgUUID(as_uuid=True), nullable=True),
        sa.Column(
            "origem_nos", ARRAY(PgUUID(as_uuid=True)), nullable=False, server_default="{}"
        ),
        sa.PrimaryKeyConstraint("projeto_id", name="pk_nc_nuvem"),
        sa.ForeignKeyConstraint(
            ["projeto_id"], ["projeto.id"], name="fk_nc_nuvem_projeto_id_projeto",
            ondelete="CASCADE",
        ),
        sa.CheckConstraint(
            "(origem_ferramenta is null and origem_projeto_id is null"
            " and coalesce(array_length(origem_nos, 1), 0) = 0)"
            " or (origem_ferramenta is not null and origem_projeto_id is not null"
            " and coalesce(array_length(origem_nos, 1), 0) > 0)",
            name="origem_completa",
        ),
        comment=(
            "Racional e referência de origem (INT-05) da Nuvem de Conflito; "
            "uma linha por projeto do tipo nc."
        ),
    )

    op.create_table(
        "nc_premissa",
        sa.Column("id", PgUUID(as_uuid=True), nullable=False),
        sa.Column("projeto_id", PgUUID(as_uuid=True), nullable=False),
        sa.Column("aresta_id", PgUUID(as_uuid=True), nullable=False),
        sa.Column("texto", sa.Text(), nullable=False),
        sa.Column("ordem", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("estado", sa.Text(), nullable=False, server_default="vigente"),
        sa.Column("justificativa", sa.Text(), nullable=False, server_default=""),
        sa.Column("arquivada", sa.Boolean(), nullable=False, server_default="false"),
        sa.PrimaryKeyConstraint("id", name="pk_nc_premissa"),
        sa.ForeignKeyConstraint(
            ["projeto_id"], ["projeto.id"], name="fk_nc_premissa_projeto_id_projeto",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["aresta_id"], ["aresta_causal.id"],
            name="fk_nc_premissa_aresta_id_aresta_causal", ondelete="CASCADE",
        ),
        sa.CheckConstraint("length(btrim(texto)) > 0", name="premissa_nao_vazia"),
        sa.CheckConstraint("estado in ('vigente', 'desafiada')", name="estado_da_premissa"),
        sa.CheckConstraint(
            "estado <> 'desafiada' or length(btrim(justificativa)) > 0",
            name="justificativa_do_desafio",
        ),
        comment="Premissa de uma aresta da nuvem; vazia não entra, desafiada exige motivo.",
    )
    op.create_index("ix_nc_premissa_projeto_id", "nc_premissa", ["projeto_id"])
    op.create_index("ix_nc_premissa_aresta_id", "nc_premissa", ["aresta_id"])

    op.create_table(
        "nc_injecao",
        sa.Column("id", PgUUID(as_uuid=True), nullable=False),
        sa.Column("projeto_id", PgUUID(as_uuid=True), nullable=False),
        sa.Column("premissa_id", PgUUID(as_uuid=True), nullable=False),
        sa.Column("texto", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False, server_default="candidata"),
        sa.Column("separacao", sa.Text(), nullable=True),
        sa.Column("arquivada", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("semeadura_projeto_id", PgUUID(as_uuid=True), nullable=True),
        sa.PrimaryKeyConstraint("id", name="pk_nc_injecao"),
        sa.ForeignKeyConstraint(
            ["projeto_id"], ["projeto.id"], name="fk_nc_injecao_projeto_id_projeto",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["premissa_id"], ["nc_premissa.id"],
            name="fk_nc_injecao_premissa_id_nc_premissa", ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["semeadura_projeto_id"], ["projeto.id"],
            name="fk_nc_injecao_semeadura_projeto_id_projeto", ondelete="SET NULL",
        ),
        sa.CheckConstraint("length(btrim(texto)) > 0", name="injecao_nao_vazia"),
        sa.CheckConstraint(
            "status in ('candidata', 'escolhida', 'descartada')", name="status_da_injecao"
        ),
        sa.CheckConstraint(
            "separacao is null or separacao in"
            " ('espaco', 'tempo', 'partes', 'grau', 'condicao')",
            name="separacao_triz",
        ),
        sa.CheckConstraint(
            "semeadura_projeto_id is null or status = 'escolhida'",
            name="semeadura_so_de_escolhida",
        ),
        comment=(
            "Injeção ligada a UMA premissa (RN-04); status na FSM "
            "candidata/escolhida/descartada."
        ),
    )
    op.create_index("ix_nc_injecao_projeto_id", "nc_injecao", ["projeto_id"])
    op.create_index("ix_nc_injecao_premissa_id", "nc_injecao", ["premissa_id"])


def downgrade() -> None:
    op.drop_index("ix_nc_injecao_premissa_id", table_name="nc_injecao")
    op.drop_index("ix_nc_injecao_projeto_id", table_name="nc_injecao")
    op.drop_table("nc_injecao")
    op.drop_index("ix_nc_premissa_aresta_id", table_name="nc_premissa")
    op.drop_index("ix_nc_premissa_projeto_id", table_name="nc_premissa")
    op.drop_table("nc_premissa")
    op.drop_table("nc_nuvem")
