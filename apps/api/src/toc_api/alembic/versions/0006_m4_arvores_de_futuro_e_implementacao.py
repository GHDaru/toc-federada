"""0006 — M4: Árvores de Futuro e Implementação (ARF, APR, AT) e a referência cruzada.

Siglas, uma vez neste arquivo: **M1** — Núcleo de Diagramas Lógicos · **M2** — Árvore da
Realidade Atual · **M4** — Árvores de Futuro e Implementação · **ARF** — Árvore da
Realidade Futura · **APR** — Árvore de Pré-Requisitos · **AT** — Árvore de Transição ·
**UDE** — Efeito Indesejável · **OI** — Objetivo Intermediário.

A spec 008 acrescenta ao núcleo três tipos de projeto e **um agregado novo**. Nove
tabelas, e a ausência de três outras é decisão registrada, não esquecimento:

- **não há tabela de nó nem de aresta das três árvores**: injeção, efeito futuro,
  obstáculo, objetivo intermediário e passo são linhas de `no` cujo `tipo` carrega o papel
  (`arf_injecao`, `apr_obstaculo`, `at_passo`, …), e dependência e precedência são linhas
  de `aresta_causal`. O `tipo` é enum extensível por decisão do próprio M1 (RN-04 da
  spec 004);
- **não há `arf_elo_exame` nem `arf_conector_e`**: a ARF reusa `elo_exame` e `conector_e`
  do M2. É a contraparte física da decisão 1 do plano do ciclo 008 — o pacote de
  suficiência causal é **extraído, nunca copiado**, e duas tabelas gêmeas seriam a cópia
  com outro nome;
- **`referencia_cruzada` não tem chave estrangeira para `projeto`**: a RN-12 manda a
  exclusão suave **suspender** a referência, e `ON DELETE CASCADE` a apagaria na exclusão
  definitiva — exatamente o "apagar por efeito colateral" que a regra proíbe.

As restrições `uq_espelho_por_ude` (RN-03), `tratado_exige_injecao_de_corte` e
`aceito_exige_justificativa_e_autor` (RN-04), `uq_par_por_obstaculo` (RF-17),
`tripla_do_passo_obrigatoria` (RN-10) e `bloqueado_exige_motivo` / `concluido_exige_
resultado_real` (RF-30) são as regras do domínio impostas **pelo banco** além do código:
invariante que só vive no código é invariante que a próxima ferramenta viola sem perceber.

Revisão: 0006
Anterior: 0005 (M3 — Nuvem de Conflito)
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.dialects.postgresql import UUID as PgUUID

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None

INSTANTE = sa.DateTime(timezone=True)


def upgrade() -> None:
    # -- E4.1 · Árvore da Realidade Futura ----------------------------------------
    op.create_table(
        "arf_arvore",
        sa.Column("projeto_id", PgUUID(as_uuid=True), nullable=False),
        sa.Column("origem_ferramenta", sa.Text(), nullable=True),
        sa.Column("origem_projeto_id", PgUUID(as_uuid=True), nullable=True),
        sa.Column(
            "origem_elementos", ARRAY(PgUUID(as_uuid=True)), nullable=False, server_default="{}"
        ),
        sa.Column("origem_papel", sa.Text(), nullable=False, server_default=""),
        sa.Column(
            "udes_da_cadeia", ARRAY(PgUUID(as_uuid=True)), nullable=False, server_default="{}"
        ),
        sa.PrimaryKeyConstraint("projeto_id", name="pk_arf_arvore"),
        sa.ForeignKeyConstraint(
            ["projeto_id"], ["projeto.id"], name="fk_arf_arvore_projeto_id_projeto",
            ondelete="CASCADE",
        ),
        sa.CheckConstraint(
            "(origem_ferramenta is null and origem_projeto_id is null)"
            " or (origem_ferramenta is not null and origem_projeto_id is not null)",
            name="origem_da_arf_completa",
        ),
        comment=(
            "Cabeçalho da Árvore da Realidade Futura: origem (injeção que a semeou) e os "
            "Efeitos Indesejáveis referenciáveis pelo espelho (RN-03)."
        ),
    )

    op.create_table(
        "arf_espelho",
        sa.Column("no_id", PgUUID(as_uuid=True), nullable=False),
        sa.Column("projeto_id", PgUUID(as_uuid=True), nullable=False),
        sa.Column("ude_id", PgUUID(as_uuid=True), nullable=False),
        sa.Column("projeto_de_origem_id", PgUUID(as_uuid=True), nullable=True),
        sa.PrimaryKeyConstraint("no_id", name="pk_arf_espelho"),
        sa.ForeignKeyConstraint(
            ["no_id"], ["no.id"], name="fk_arf_espelho_no_id_no", ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["projeto_id"], ["projeto.id"], name="fk_arf_espelho_projeto_id_projeto",
            ondelete="CASCADE",
        ),
        # RN-03 imposta pelo banco: um UDE tem no máximo um Efeito Desejável por ARF.
        sa.UniqueConstraint("projeto_id", "ude_id", name="uq_espelho_por_ude"),
        comment="Espelho UDE → Efeito Desejável; no máximo um por UDE em cada ARF (RN-03).",
    )
    op.create_index("ix_arf_espelho_projeto_id", "arf_espelho", ["projeto_id"])

    op.create_table(
        "arf_ramo_negativo",
        sa.Column("id", PgUUID(as_uuid=True), nullable=False),
        sa.Column("projeto_id", PgUUID(as_uuid=True), nullable=False),
        sa.Column("raiz_id", PgUUID(as_uuid=True), nullable=False),
        sa.Column("estado", sa.Text(), nullable=False, server_default="aberto"),
        sa.Column("injecao_de_corte_id", PgUUID(as_uuid=True), nullable=True),
        sa.Column("justificativa", sa.Text(), nullable=False, server_default=""),
        sa.Column("autor", sa.Text(), nullable=False, server_default=""),
        sa.PrimaryKeyConstraint("id", name="pk_arf_ramo_negativo"),
        sa.ForeignKeyConstraint(
            ["projeto_id"], ["projeto.id"], name="fk_arf_ramo_negativo_projeto_id_projeto",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["raiz_id"], ["no.id"], name="fk_arf_ramo_negativo_raiz_id_no", ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["injecao_de_corte_id"], ["no.id"],
            name="fk_arf_ramo_negativo_injecao_de_corte_id_no", ondelete="SET NULL",
        ),
        sa.CheckConstraint(
            "estado in ('aberto', 'tratado', 'aceito')", name="estado_do_ramo_negativo"
        ),
        sa.CheckConstraint(
            "estado <> 'tratado' or injecao_de_corte_id is not null",
            name="tratado_exige_injecao_de_corte",
        ),
        sa.CheckConstraint(
            "estado <> 'aceito' or (length(btrim(justificativa)) > 0"
            " and length(btrim(autor)) > 0)",
            name="aceito_exige_justificativa_e_autor",
        ),
        sa.UniqueConstraint("raiz_id", name="uq_ramo_por_raiz"),
        comment="Ramo negativo da ARF: aberto → tratado (com injeção) | aceito (com motivo).",
    )
    op.create_index("ix_arf_ramo_negativo_projeto_id", "arf_ramo_negativo", ["projeto_id"])

    # -- E4.2 · Árvore de Pré-Requisitos -------------------------------------------
    op.create_table(
        "apr_arvore",
        sa.Column("projeto_id", PgUUID(as_uuid=True), nullable=False),
        sa.Column("origem_ferramenta", sa.Text(), nullable=True),
        sa.Column("origem_projeto_id", PgUUID(as_uuid=True), nullable=True),
        sa.Column(
            "origem_elementos", ARRAY(PgUUID(as_uuid=True)), nullable=False, server_default="{}"
        ),
        sa.Column("origem_papel", sa.Text(), nullable=False, server_default=""),
        sa.PrimaryKeyConstraint("projeto_id", name="pk_apr_arvore"),
        sa.ForeignKeyConstraint(
            ["projeto_id"], ["projeto.id"], name="fk_apr_arvore_projeto_id_projeto",
            ondelete="CASCADE",
        ),
        sa.CheckConstraint(
            "(origem_ferramenta is null and origem_projeto_id is null)"
            " or (origem_ferramenta is not null and origem_projeto_id is not null)",
            name="origem_da_apr_completa",
        ),
        comment="Cabeçalho da Árvore de Pré-Requisitos: a origem (efeito ou injeção da ARF).",
    )

    op.create_table(
        "apr_par",
        sa.Column("id", PgUUID(as_uuid=True), nullable=False),
        sa.Column("projeto_id", PgUUID(as_uuid=True), nullable=False),
        sa.Column("obstaculo_id", PgUUID(as_uuid=True), nullable=False),
        sa.Column("objetivo_intermediario_id", PgUUID(as_uuid=True), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_apr_par"),
        sa.ForeignKeyConstraint(
            ["projeto_id"], ["projeto.id"], name="fk_apr_par_projeto_id_projeto",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["obstaculo_id"], ["no.id"], name="fk_apr_par_obstaculo_id_no", ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["objetivo_intermediario_id"], ["no.id"],
            name="fk_apr_par_objetivo_intermediario_id_no", ondelete="CASCADE",
        ),
        # RF-17 imposta pelo banco: um objetivo intermediário supera vários obstáculos; o
        # obstáculo tem uma resposta só.
        sa.UniqueConstraint("obstaculo_id", name="uq_par_por_obstaculo"),
        comment="Par obstáculo ↔ objetivo intermediário; o obstáculo tem uma resposta só.",
    )
    op.create_index("ix_apr_par_projeto_id", "apr_par", ["projeto_id"])

    op.create_table(
        "apr_julgamento",
        sa.Column("id", PgUUID(as_uuid=True), nullable=False),
        sa.Column("par_id", PgUUID(as_uuid=True), nullable=False),
        sa.Column("autor", sa.Text(), nullable=False),
        sa.Column("valido", sa.Boolean(), nullable=False),
        sa.Column("justificativa", sa.Text(), nullable=False),
        sa.Column("instante", INSTANTE, nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_apr_julgamento"),
        sa.ForeignKeyConstraint(
            ["par_id"], ["apr_par.id"], name="fk_apr_julgamento_par_id_apr_par",
            ondelete="CASCADE",
        ),
        sa.CheckConstraint("length(btrim(autor)) > 0", name="julgamento_com_autor"),
        sa.CheckConstraint(
            "length(btrim(justificativa)) > 0", name="julgamento_com_justificativa"
        ),
        comment="Julgamento do teste IO-Obstáculo, somente-acréscimo (RN-07).",
    )
    op.create_index("ix_apr_julgamento_par_id", "apr_julgamento", ["par_id"])

    op.create_table(
        "apr_elipse",
        sa.Column("id", PgUUID(as_uuid=True), nullable=False),
        sa.Column("projeto_id", PgUUID(as_uuid=True), nullable=False),
        sa.Column("destino_id", PgUUID(as_uuid=True), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_apr_elipse"),
        sa.ForeignKeyConstraint(
            ["projeto_id"], ["projeto.id"], name="fk_apr_elipse_projeto_id_projeto",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["destino_id"], ["no.id"], name="fk_apr_elipse_destino_id_no", ondelete="CASCADE"
        ),
        comment="Elipse de simultaneidade: conjunção de necessidade, não de suficiência.",
    )
    op.create_index("ix_apr_elipse_projeto_id", "apr_elipse", ["projeto_id"])

    op.create_table(
        "apr_elipse_dependencia",
        sa.Column("elipse_id", PgUUID(as_uuid=True), nullable=False),
        sa.Column("aresta_id", PgUUID(as_uuid=True), nullable=False),
        sa.PrimaryKeyConstraint("elipse_id", "aresta_id", name="pk_apr_elipse_dependencia"),
        sa.ForeignKeyConstraint(
            ["elipse_id"], ["apr_elipse.id"],
            name="fk_apr_elipse_dependencia_elipse_id_apr_elipse", ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["aresta_id"], ["aresta_causal.id"],
            name="fk_apr_elipse_dependencia_aresta_id_aresta_causal", ondelete="CASCADE",
        ),
        # RN-06 imposta pelo banco: uma dependência pertence a no máximo uma elipse.
        sa.UniqueConstraint("aresta_id", name="uq_elipse_dependencia_unica"),
    )

    # -- E4.3 · Árvore de Transição -------------------------------------------------
    op.create_table(
        "at_arvore",
        sa.Column("projeto_id", PgUUID(as_uuid=True), nullable=False),
        sa.Column("alvo_ferramenta", sa.Text(), nullable=True),
        sa.Column("alvo_projeto_id", PgUUID(as_uuid=True), nullable=True),
        sa.Column(
            "alvo_elementos", ARRAY(PgUUID(as_uuid=True)), nullable=False, server_default="{}"
        ),
        sa.Column("alvo_papel", sa.Text(), nullable=False, server_default=""),
        sa.PrimaryKeyConstraint("projeto_id", name="pk_at_arvore"),
        sa.ForeignKeyConstraint(
            ["projeto_id"], ["projeto.id"], name="fk_at_arvore_projeto_id_projeto",
            ondelete="CASCADE",
        ),
        sa.CheckConstraint(
            "(alvo_ferramenta is null and alvo_projeto_id is null)"
            " or (alvo_ferramenta is not null and alvo_projeto_id is not null)",
            name="alvo_da_at_completo",
        ),
        comment="Cabeçalho da Árvore de Transição: o objetivo intermediário de origem.",
    )

    op.create_table(
        "at_passo",
        sa.Column("no_id", PgUUID(as_uuid=True), nullable=False),
        sa.Column("projeto_id", PgUUID(as_uuid=True), nullable=False),
        sa.Column("acao", sa.Text(), nullable=False),
        sa.Column("necessidade", sa.Text(), nullable=False),
        sa.Column("resultado_esperado", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False, server_default="pendente"),
        sa.Column("motivo_do_bloqueio", sa.Text(), nullable=False, server_default=""),
        sa.Column("resultado_real", sa.Text(), nullable=False, server_default=""),
        sa.PrimaryKeyConstraint("no_id", name="pk_at_passo"),
        sa.ForeignKeyConstraint(
            ["no_id"], ["no.id"], name="fk_at_passo_no_id_no", ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["projeto_id"], ["projeto.id"], name="fk_at_passo_projeto_id_projeto",
            ondelete="CASCADE",
        ),
        # RN-10 imposta pelo banco: passo sem a tripla é a lista de tarefas que a Árvore
        # de Transição existe para não ser.
        sa.CheckConstraint(
            "length(btrim(acao)) > 0 and length(btrim(necessidade)) > 0"
            " and length(btrim(resultado_esperado)) > 0",
            name="tripla_do_passo_obrigatoria",
        ),
        sa.CheckConstraint(
            "status in ('pendente', 'em_execucao', 'concluido', 'bloqueado')",
            name="status_do_passo",
        ),
        sa.CheckConstraint(
            "status <> 'bloqueado' or length(btrim(motivo_do_bloqueio)) > 0",
            name="bloqueado_exige_motivo",
        ),
        sa.CheckConstraint(
            "status <> 'concluido' or length(btrim(resultado_real)) > 0",
            name="concluido_exige_resultado_real",
        ),
        comment="Passo da AT: ação · necessidade · resultado esperado (RN-10) + status.",
    )
    op.create_index("ix_at_passo_projeto_id", "at_passo", ["projeto_id"])

    # -- E4.4 · a referência cruzada (o agregado que corrige o defeito D-11) --------
    op.create_table(
        "referencia_cruzada",
        sa.Column("id", PgUUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", sa.Text(), nullable=False),
        sa.Column("usuario_id", sa.Text(), nullable=False),
        sa.Column("tipo", sa.Text(), nullable=False),
        sa.Column("origem_ferramenta", sa.Text(), nullable=False),
        sa.Column("origem_projeto_id", PgUUID(as_uuid=True), nullable=False),
        sa.Column(
            "origem_elementos", ARRAY(PgUUID(as_uuid=True)), nullable=False, server_default="{}"
        ),
        sa.Column("origem_papel", sa.Text(), nullable=False, server_default=""),
        sa.Column("destino_ferramenta", sa.Text(), nullable=False),
        sa.Column("destino_projeto_id", PgUUID(as_uuid=True), nullable=False),
        sa.Column(
            "destino_elementos", ARRAY(PgUUID(as_uuid=True)), nullable=False, server_default="{}"
        ),
        sa.Column("destino_papel", sa.Text(), nullable=False, server_default=""),
        sa.Column("estado", sa.Text(), nullable=False, server_default="ativa"),
        sa.Column("motivo", sa.Text(), nullable=False, server_default=""),
        sa.Column("versao", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("criada_em", INSTANTE, nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_referencia_cruzada"),
        sa.CheckConstraint(
            "tipo in ('promocao_ude_nc', 'semeadura_injecao_arf', 'derivacao_arf_apr',"
            " 'derivacao_oi_at')",
            name="tipo_da_referencia",
        ),
        sa.CheckConstraint("estado in ('ativa', 'pendente')", name="estado_da_referencia"),
        sa.CheckConstraint(
            "estado <> 'pendente' or length(btrim(motivo)) > 0",
            name="pendente_exige_motivo",
        ),
        sa.CheckConstraint(
            "origem_projeto_id <> destino_projeto_id",
            name="referencia_liga_projetos_distintos",
        ),
        comment=(
            "Referência cruzada entre ferramentas (RF-33). Sem chave estrangeira para "
            "projeto de propósito: exclusão suave SUSPENDE (RN-12), e cascata apagaria."
        ),
    )
    op.create_index(
        "ix_referencia_cruzada_tenant_id_origem_projeto_id",
        "referencia_cruzada",
        ["tenant_id", "origem_projeto_id"],
    )
    op.create_index(
        "ix_referencia_cruzada_tenant_id_destino_projeto_id",
        "referencia_cruzada",
        ["tenant_id", "destino_projeto_id"],
    )


def downgrade() -> None:
    """Volta ao esquema do M3, sem resíduo. A ordem é a inversa das chaves estrangeiras."""
    op.drop_index("ix_referencia_cruzada_tenant_id_destino_projeto_id", "referencia_cruzada")
    op.drop_index("ix_referencia_cruzada_tenant_id_origem_projeto_id", "referencia_cruzada")
    op.drop_table("referencia_cruzada")

    op.drop_index("ix_at_passo_projeto_id", "at_passo")
    op.drop_table("at_passo")
    op.drop_table("at_arvore")

    op.drop_table("apr_elipse_dependencia")
    op.drop_index("ix_apr_elipse_projeto_id", "apr_elipse")
    op.drop_table("apr_elipse")
    op.drop_index("ix_apr_julgamento_par_id", "apr_julgamento")
    op.drop_table("apr_julgamento")
    op.drop_index("ix_apr_par_projeto_id", "apr_par")
    op.drop_table("apr_par")
    op.drop_table("apr_arvore")

    op.drop_index("ix_arf_ramo_negativo_projeto_id", "arf_ramo_negativo")
    op.drop_table("arf_ramo_negativo")
    op.drop_index("ix_arf_espelho_projeto_id", "arf_espelho")
    op.drop_table("arf_espelho")
    op.drop_table("arf_arvore")
