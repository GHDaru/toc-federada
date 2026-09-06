"""0008 — M6: a jornada dos cinco passos de focalização.

Siglas, uma vez neste arquivo: **M1** — Núcleo de Diagramas Lógicos · **M6** —
Focalização · **TOC** — Teoria das Restrições · **ARA** — Árvore da Realidade Atual ·
**NC** — Nuvem de Conflito · **APR** — Árvore de Pré-Requisitos · **AT** — Árvore de
Transição · **RN/RF/RNF** — regra de negócio / requisito funcional / requisito não
funcional.

A spec 009 acrescenta ao núcleo **um tipo de projeto e nove tabelas**, e a forma delas é a
diferença estrutural do módulo: a análise de focalização **não é diagrama**. Ela não usa
`no` nem `aresta_causal` — a superfície dela é jornada e linha do tempo.

Três invariantes do domínio entram aqui como restrição de banco, além do código. O motivo
é o mesmo das migrações anteriores: invariante que só vive no código é invariante que a
próxima ferramenta viola sem perceber.

1. **RN-02** — `uq_foco_ciclo_aberto_por_analise`, índice único **parcial** sobre
   `projeto_id` onde `estado = 'aberto'`: no máximo um ciclo aberto por análise. Parcial
   porque os ciclos fechados são muitos, e é exatamente isso que a regra permite.
2. **RN-03** — `foco_restricao` tem `ciclo_id` como **chave primária**: a segunda
   restrição vigente num mesmo ciclo é fisicamente impossível, não "recusada por código".
3. **RN-01** — `foco_passo` tem chave primária `(ciclo_id, tipo)` com `tipo` num
   vocabulário fechado de cinco valores: não há identidade de passo a inventar, não há
   sexto passo possível, e reordenar não tem onde acontecer.

E duas ausências declaradas:

- **`foco_vinculo` não tem chave estrangeira para o projeto de DESTINO.** A RNF-04 manda o
  vínculo cujo destino foi arquivado degradar para "referência a projeto arquivado"
  legível; uma cascata o apagaria numa exclusão definitiva, perdendo o registro que o
  requisito obriga a mostrar. É a mesma decisão, pelo mesmo tipo de motivo, que
  `referencia_cruzada` tomou na 0006 e `proposta_de_acao` na 0004.
- **Nenhuma coluna de conteúdo dos módulos M2–M4.** `foco_vinculo` guarda ferramenta e
  identificador, e mais nada: a cópia por conveniência é o defeito que o núcleo M1 existe
  para impedir, e ela envelheceria no primeiro `PUT` do módulo de origem.

Revisão: 0008
Anterior: 0007 (deduplicação real da chave de idempotência)
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID as PgUUID

revision = "0008"
down_revision = "0007"
branch_labels = None
depends_on = None

INSTANTE = sa.DateTime(timezone=True)


def upgrade() -> None:
    op.create_table(
        "foco_analise",
        sa.Column("projeto_id", PgUUID(as_uuid=True), nullable=False),
        sa.Column("sistema_nome", sa.Text(), nullable=False),
        sa.Column("sistema_descricao", sa.Text(), nullable=False, server_default=""),
        sa.PrimaryKeyConstraint("projeto_id", name="pk_foco_analise"),
        sa.ForeignKeyConstraint(
            ["projeto_id"], ["projeto.id"], name="fk_foco_analise_projeto_id_projeto",
            ondelete="CASCADE",
        ),
        sa.CheckConstraint("length(btrim(sistema_nome)) > 0", name="sistema_com_nome"),
        comment=(
            "Cabeçalho da análise de focalização: o sistema cuja meta a análise serve. "
            "Uma linha por projeto do tipo focalizacao."
        ),
    )

    op.create_table(
        "foco_ciclo",
        sa.Column("id", PgUUID(as_uuid=True), nullable=False),
        sa.Column("projeto_id", PgUUID(as_uuid=True), nullable=False),
        sa.Column("ordem", sa.Integer(), nullable=False),
        sa.Column("estado", sa.Text(), nullable=False, server_default="aberto"),
        sa.Column("aberto_em", INSTANTE, nullable=False),
        sa.Column("fechado_em", INSTANTE, nullable=True),
        sa.PrimaryKeyConstraint("id", name="pk_foco_ciclo"),
        sa.ForeignKeyConstraint(
            ["projeto_id"], ["projeto.id"], name="fk_foco_ciclo_projeto_id_projeto",
            ondelete="CASCADE",
        ),
        sa.CheckConstraint("estado in ('aberto', 'fechado')", name="estado_do_ciclo"),
        sa.CheckConstraint("ordem >= 1", name="ordem_do_ciclo"),
        sa.CheckConstraint(
            "(estado = 'aberto' and fechado_em is null)"
            " or (estado = 'fechado' and fechado_em is not null)",
            name="fechado_tem_data",
        ),
        sa.UniqueConstraint("projeto_id", "ordem", name="uq_foco_ciclo_ordem"),
        comment="Ciclo de focalização; RN-02 (um aberto por análise) imposta por índice parcial.",
    )
    # RN-02 imposta PELO BANCO. Sem este índice, duas requisições simultâneas de recomeço
    # abririam dois ciclos e a análise passaria a ter duas jornadas correndo — que é a
    # coisa que a regra existe para impedir, e que a trava otimista sozinha não pega
    # quando as duas escritas partem de versões diferentes do agregado.
    op.create_index(
        "uq_foco_ciclo_aberto_por_analise",
        "foco_ciclo",
        ["projeto_id"],
        unique=True,
        postgresql_where=sa.text("estado = 'aberto'"),
    )

    op.create_table(
        "foco_restricao",
        sa.Column("ciclo_id", PgUUID(as_uuid=True), nullable=False),
        sa.Column("id", PgUUID(as_uuid=True), nullable=False),
        sa.Column("projeto_id", PgUUID(as_uuid=True), nullable=False),
        sa.Column("descricao", sa.Text(), nullable=False),
        sa.Column("tipo", sa.Text(), nullable=False),
        sa.Column("justificativa", sa.Text(), nullable=False),
        sa.Column("autor", sa.Text(), nullable=False),
        sa.Column("registrada_em", INSTANTE, nullable=False),
        sa.Column("origem_ferramenta", sa.Text(), nullable=True),
        sa.Column("origem_projeto_id", PgUUID(as_uuid=True), nullable=True),
        sa.Column("origem_no_id", PgUUID(as_uuid=True), nullable=True),
        # RN-03 no banco: a chave primária é o CICLO, e não a restrição.
        sa.PrimaryKeyConstraint("ciclo_id", name="pk_foco_restricao"),
        sa.UniqueConstraint("id", name="uq_foco_restricao_id"),
        sa.ForeignKeyConstraint(
            ["ciclo_id"], ["foco_ciclo.id"], name="fk_foco_restricao_ciclo_id_foco_ciclo",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["projeto_id"], ["projeto.id"], name="fk_foco_restricao_projeto_id_projeto",
            ondelete="CASCADE",
        ),
        sa.CheckConstraint(
            "tipo in ('fisica', 'politica', 'de_mercado')", name="tipo_da_restricao"
        ),
        sa.CheckConstraint("length(btrim(descricao)) > 0", name="restricao_nao_vazia"),
        sa.CheckConstraint(
            "length(btrim(justificativa)) > 0", name="restricao_com_justificativa"
        ),
        sa.CheckConstraint("length(btrim(autor)) > 0", name="restricao_com_autor"),
        sa.CheckConstraint(
            "(origem_ferramenta is null and origem_projeto_id is null and origem_no_id is null)"
            " or (origem_ferramenta is not null and origem_projeto_id is not null"
            " and origem_no_id is not null)",
            name="origem_da_restricao_completa",
        ),
        comment="Restrição vigente do ciclo; a chave primária por ciclo é a RN-03 no banco.",
    )
    op.create_index("ix_foco_restricao_projeto_id", "foco_restricao", ["projeto_id"])

    op.create_table(
        "foco_passo",
        sa.Column("ciclo_id", PgUUID(as_uuid=True), nullable=False),
        sa.Column("tipo", sa.Text(), nullable=False),
        sa.Column("projeto_id", PgUUID(as_uuid=True), nullable=False),
        sa.Column("estado", sa.Text(), nullable=False, server_default="pendente"),
        sa.Column("ordem", sa.Integer(), nullable=False),
        # RN-01 no banco: a identidade do passo É (ciclo, tipo).
        sa.PrimaryKeyConstraint("ciclo_id", "tipo", name="pk_foco_passo"),
        sa.ForeignKeyConstraint(
            ["ciclo_id"], ["foco_ciclo.id"], name="fk_foco_passo_ciclo_id_foco_ciclo",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["projeto_id"], ["projeto.id"], name="fk_foco_passo_projeto_id_projeto",
            ondelete="CASCADE",
        ),
        sa.CheckConstraint(
            "tipo in ('identificar', 'explorar', 'subordinar', 'elevar', 'recomecar')",
            name="tipo_do_passo",
        ),
        sa.CheckConstraint(
            "estado in ('pendente', 'em_andamento', 'concluido')", name="estado_do_passo"
        ),
        sa.CheckConstraint("ordem between 1 and 5", name="ordem_do_passo"),
        comment="Passo de focalização; a chave (ciclo, tipo) é a ordem canônica no banco (RN-01).",
    )
    op.create_index("ix_foco_passo_projeto_id", "foco_passo", ["projeto_id"])

    op.create_table(
        "foco_decisao",
        sa.Column("id", PgUUID(as_uuid=True), nullable=False),
        sa.Column("ciclo_id", PgUUID(as_uuid=True), nullable=False),
        sa.Column("passo", sa.Text(), nullable=False),
        sa.Column("texto", sa.Text(), nullable=False),
        sa.Column("autor", sa.Text(), nullable=False),
        sa.Column("instante", INSTANTE, nullable=False),
        sa.Column("ordem", sa.Integer(), nullable=False, server_default="0"),
        sa.PrimaryKeyConstraint("id", name="pk_foco_decisao"),
        sa.ForeignKeyConstraint(
            ["ciclo_id", "passo"],
            ["foco_passo.ciclo_id", "foco_passo.tipo"],
            name="fk_foco_decisao_passo",
            ondelete="CASCADE",
        ),
        sa.CheckConstraint("length(btrim(texto)) > 0", name="decisao_nao_vazia"),
        sa.CheckConstraint("length(btrim(autor)) > 0", name="decisao_com_autor"),
        comment="Decisão que encerra um passo; somente-acréscimo (RN-04, RF-10).",
    )
    op.create_index("ix_foco_decisao_ciclo_id_passo", "foco_decisao", ["ciclo_id", "passo"])

    op.create_table(
        "foco_nota",
        sa.Column("id", PgUUID(as_uuid=True), nullable=False),
        sa.Column("ciclo_id", PgUUID(as_uuid=True), nullable=False),
        sa.Column("passo", sa.Text(), nullable=False),
        sa.Column("texto", sa.Text(), nullable=False),
        sa.Column("autor", sa.Text(), nullable=False),
        sa.Column("instante", INSTANTE, nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_foco_nota"),
        sa.ForeignKeyConstraint(
            ["ciclo_id", "passo"],
            ["foco_passo.ciclo_id", "foco_passo.tipo"],
            name="fk_foco_nota_passo",
            ondelete="CASCADE",
        ),
        sa.CheckConstraint("length(btrim(texto)) > 0", name="nota_nao_vazia"),
        comment="Nota de passo: texto livre acumulável com autoria (RF-11).",
    )
    op.create_index("ix_foco_nota_ciclo_id_passo", "foco_nota", ["ciclo_id", "passo"])

    op.create_table(
        "foco_reabertura",
        sa.Column("id", PgUUID(as_uuid=True), nullable=False),
        sa.Column("ciclo_id", PgUUID(as_uuid=True), nullable=False),
        sa.Column("passo", sa.Text(), nullable=False),
        sa.Column("justificativa", sa.Text(), nullable=False),
        sa.Column("autor", sa.Text(), nullable=False),
        sa.Column("instante", INSTANTE, nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_foco_reabertura"),
        sa.ForeignKeyConstraint(
            ["ciclo_id", "passo"],
            ["foco_passo.ciclo_id", "foco_passo.tipo"],
            name="fk_foco_reabertura_passo",
            ondelete="CASCADE",
        ),
        sa.CheckConstraint(
            "length(btrim(justificativa)) > 0", name="reabertura_com_justificativa"
        ),
        comment="Reabertura de passo concluído (RF-10); fica AO LADO da decisão, nunca no lugar.",
    )
    op.create_index("ix_foco_reabertura_ciclo_id_passo", "foco_reabertura", ["ciclo_id", "passo"])

    op.create_table(
        "foco_vinculo",
        sa.Column("id", PgUUID(as_uuid=True), nullable=False),
        sa.Column("ciclo_id", PgUUID(as_uuid=True), nullable=False),
        sa.Column("passo", sa.Text(), nullable=False),
        sa.Column("projeto_id", PgUUID(as_uuid=True), nullable=False),
        sa.Column("ferramenta", sa.Text(), nullable=False),
        sa.Column("alvo_projeto_id", PgUUID(as_uuid=True), nullable=False),
        sa.Column("papel", sa.Text(), nullable=False, server_default=""),
        sa.Column("justificativa", sa.Text(), nullable=False, server_default=""),
        sa.Column("canonico", sa.Boolean(), nullable=False, server_default="true"),
        sa.PrimaryKeyConstraint("id", name="pk_foco_vinculo"),
        sa.ForeignKeyConstraint(
            ["ciclo_id", "passo"],
            ["foco_passo.ciclo_id", "foco_passo.tipo"],
            name="fk_foco_vinculo_passo",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["projeto_id"], ["projeto.id"], name="fk_foco_vinculo_projeto_id_projeto",
            ondelete="CASCADE",
        ),
        sa.CheckConstraint(
            "ferramenta in ('ara', 'nc', 'arf', 'apr', 'at')", name="ferramenta_vinculada"
        ),
        sa.CheckConstraint(
            "canonico or length(btrim(justificativa)) > 0",
            name="nao_canonico_exige_justificativa",
        ),
        sa.UniqueConstraint(
            "ciclo_id", "passo", "ferramenta", "alvo_projeto_id", name="uq_foco_vinculo"
        ),
        comment=(
            "Vínculo tipado passo → projeto de ferramenta (RF-14). Sem chave estrangeira "
            "para o destino de propósito: arquivar degrada (RNF-04), cascata apagaria."
        ),
    )
    op.create_index("ix_foco_vinculo_projeto_id", "foco_vinculo", ["projeto_id"])
    op.create_index("ix_foco_vinculo_alvo_projeto_id", "foco_vinculo", ["alvo_projeto_id"])

    op.create_table(
        "foco_heranca",
        sa.Column("id", PgUUID(as_uuid=True), nullable=False),
        sa.Column("ciclo_id", PgUUID(as_uuid=True), nullable=False),
        sa.Column("projeto_id", PgUUID(as_uuid=True), nullable=False),
        sa.Column("ciclo_de_origem", sa.Integer(), nullable=False),
        sa.Column("passo", sa.Text(), nullable=False),
        sa.Column("texto", sa.Text(), nullable=False),
        sa.Column("veredito", sa.Text(), nullable=False, server_default="pendente"),
        sa.Column("justificativa", sa.Text(), nullable=False, server_default=""),
        sa.Column("autor", sa.Text(), nullable=False, server_default=""),
        sa.Column("julgada_em", INSTANTE, nullable=True),
        sa.Column("ordem", sa.Integer(), nullable=False, server_default="0"),
        sa.PrimaryKeyConstraint("id", name="pk_foco_heranca"),
        sa.ForeignKeyConstraint(
            ["ciclo_id"], ["foco_ciclo.id"], name="fk_foco_heranca_ciclo_id_foco_ciclo",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["projeto_id"], ["projeto.id"], name="fk_foco_heranca_projeto_id_projeto",
            ondelete="CASCADE",
        ),
        sa.CheckConstraint(
            "veredito in ('pendente', 'mantida', 'revogada')", name="veredito_da_heranca"
        ),
        sa.CheckConstraint(
            "passo in ('identificar', 'explorar', 'subordinar', 'elevar', 'recomecar')",
            name="passo_de_origem_da_heranca",
        ),
        sa.CheckConstraint("length(btrim(texto)) > 0", name="heranca_nao_vazia"),
        # RN-05 no banco: manter é decisão tão explícita quanto revogar.
        sa.CheckConstraint(
            "veredito = 'pendente'"
            " or (length(btrim(justificativa)) > 0 and length(btrim(autor)) > 0)",
            name="veredito_exige_justificativa_e_autor",
        ),
        comment=(
            "Decisão herdada do ciclo anterior com veredito (RN-05): manter exige "
            "justificativa tanto quanto revogar."
        ),
    )
    op.create_index("ix_foco_heranca_ciclo_id", "foco_heranca", ["ciclo_id"])


def downgrade() -> None:
    """Volta ao esquema do M4, sem resíduo. A ordem é a inversa das chaves estrangeiras."""
    op.drop_index("ix_foco_heranca_ciclo_id", "foco_heranca")
    op.drop_table("foco_heranca")

    op.drop_index("ix_foco_vinculo_alvo_projeto_id", "foco_vinculo")
    op.drop_index("ix_foco_vinculo_projeto_id", "foco_vinculo")
    op.drop_table("foco_vinculo")

    op.drop_index("ix_foco_reabertura_ciclo_id_passo", "foco_reabertura")
    op.drop_table("foco_reabertura")

    op.drop_index("ix_foco_nota_ciclo_id_passo", "foco_nota")
    op.drop_table("foco_nota")

    op.drop_index("ix_foco_decisao_ciclo_id_passo", "foco_decisao")
    op.drop_table("foco_decisao")

    op.drop_index("ix_foco_passo_projeto_id", "foco_passo")
    op.drop_table("foco_passo")

    op.drop_index("ix_foco_restricao_projeto_id", "foco_restricao")
    op.drop_table("foco_restricao")

    op.drop_index("uq_foco_ciclo_aberto_por_analise", "foco_ciclo")
    op.drop_table("foco_ciclo")

    op.drop_table("foco_analise")
