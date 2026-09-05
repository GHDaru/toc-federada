"""0002 — núcleo M1: dono por (inquilino, usuário), nó e aresta causal.

Por que são DUAS migrações e não uma: `specs/003-esqueleto-federado/data-model.md` declara
o conteúdo exato da `0001` e termina com a seção "O que o ciclo 004 muda" — `projeto` ganha
os filhos do M1 (`no`, `aresta_causal`) e a exclusão suave passa a operar. Fundir as duas
apagaria essa fronteira, que é a fronteira entre dois ciclos com specs próprias.

O `usuario_id` entra como NOT NULL sem valor padrão inventado, e isso é deliberado: a
`0001` não semeia linha nenhuma, então a tabela está vazia por construção quando esta roda.
O caminho fácil — um `server_default='usuario_desconhecido'` — reproduziria o defeito D-02
da linhagem citado em `specs/003-esqueleto-federado/spec.md`: um `'user_placeholder_001'`
que fazia parecer haver isolamento onde não havia.

Revisão: 0002
Anterior: 0001
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID as PgUUID

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None

INSTANTE = sa.DateTime(timezone=True)


def upgrade() -> None:
    # -- o dono passa a ser o PAR (inquilino, usuário) da introspecção -------------
    op.add_column("projeto", sa.Column("usuario_id", sa.Text(), nullable=False))
    op.add_column(
        "projeto",
        sa.Column(
            "descricao_do_problema", sa.Text(), nullable=False, server_default=""
        ),
    )
    op.add_column(
        "projeto", sa.Column("versao", sa.Integer(), nullable=False, server_default="1")
    )

    # -- os filhos do agregado ------------------------------------------------------
    op.create_table(
        "no",
        sa.Column("id", PgUUID(as_uuid=True), nullable=False),
        sa.Column("projeto_id", PgUUID(as_uuid=True), nullable=False),
        sa.Column("tipo", sa.Text(), nullable=False, server_default="generico"),
        sa.Column("titulo", sa.Text(), nullable=False),
        sa.Column("descricao", sa.Text(), nullable=True),
        sa.Column("pos_x", sa.Numeric(12, 3), nullable=False),
        sa.Column("pos_y", sa.Numeric(12, 3), nullable=False),
        sa.Column("recolhido", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("criado_em", INSTANTE, nullable=False),
        sa.Column("alterado_em", INSTANTE, nullable=False),
        sa.Column("apagado_em", INSTANTE, nullable=True),
        sa.PrimaryKeyConstraint("id", name="pk_no"),
        sa.ForeignKeyConstraint(
            ["projeto_id"], ["projeto.id"], name="fk_no_projeto_id_projeto",
            ondelete="CASCADE",
        ),
        comment="Nó de um diagrama lógico. `tipo` é enum extensível; sem semântica TOC no M1.",
    )
    op.create_index("ix_no_projeto_id", "no", ["projeto_id"])

    op.create_table(
        "aresta_causal",
        sa.Column("id", PgUUID(as_uuid=True), nullable=False),
        sa.Column("projeto_id", PgUUID(as_uuid=True), nullable=False),
        sa.Column("origem_id", PgUUID(as_uuid=True), nullable=False),
        sa.Column("destino_id", PgUUID(as_uuid=True), nullable=False),
        sa.Column("rotulo", sa.Text(), nullable=True),
        sa.Column("criado_em", INSTANTE, nullable=False),
        sa.Column("alterado_em", INSTANTE, nullable=False),
        sa.Column("apagado_em", INSTANTE, nullable=True),
        sa.PrimaryKeyConstraint("id", name="pk_aresta_causal"),
        sa.ForeignKeyConstraint(
            ["projeto_id"], ["projeto.id"],
            name="fk_aresta_causal_projeto_id_projeto", ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["origem_id"], ["no.id"], name="fk_aresta_causal_origem_id_no",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["destino_id"], ["no.id"], name="fk_aresta_causal_destino_id_no",
            ondelete="CASCADE",
        ),
        # RN-02 e RN-03 da spec 004, impostas PELO BANCO além do domínio. Invariante que
        # só vive no código é invariante que a próxima ferramenta viola sem perceber.
        sa.CheckConstraint("origem_id <> destino_id", name="sem_auto_laco"),
        sa.UniqueConstraint(
            "projeto_id", "origem_id", "destino_id", name="uq_aresta_par"
        ),
        comment='Aresta dirigida: lê-se "Se origem, então destino" (RN-01).',
    )
    op.create_index("ix_aresta_causal_projeto_id", "aresta_causal", ["projeto_id"])


def downgrade() -> None:
    op.drop_index("ix_aresta_causal_projeto_id", table_name="aresta_causal")
    op.drop_table("aresta_causal")
    op.drop_index("ix_no_projeto_id", table_name="no")
    op.drop_table("no")
    op.drop_column("projeto", "versao")
    op.drop_column("projeto", "descricao_do_problema")
    op.drop_column("projeto", "usuario_id")
