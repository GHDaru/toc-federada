"""O esquema físico, declarado como SQLAlchemy Core — sem ORM e sem `create_all`.

Duas escolhas explicadas, porque as duas são fáceis de fazer errado:

1. **Core `Table` e não modelos ORM.** O agregado do domínio já existe e é puro; um
   modelo ORM em cima dele criaria um segundo lugar onde a regra mora. O repositório
   traduz linha ↔ agregado à mão, num arquivo só.
2. **`MetaData` sem `schema` fixo.** As tabelas nascem sem qualificação e caem onde o
   `search_path` da conexão manda (ver `motor.py`). É o que permite a suíte de integração
   migrar num esquema descartável.

Este `MetaData` é o `target_metadata` do Alembic — serve para conferir deriva entre o
código e as migrações. **Ele nunca cria tabela**: quem cria é a migração (brief §4).
"""
from __future__ import annotations

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    MetaData,
    Numeric,
    Table,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.dialects.postgresql import UUID as PgUUID

CONVENCAO_DE_NOMES = {
    "ix": "ix_%(table_name)s_%(column_0_N_name)s",
    "uq": "uq_%(table_name)s_%(column_0_N_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_N_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

metadados = MetaData(naming_convention=CONVENCAO_DE_NOMES)

INSTANTE = DateTime(timezone=True)

# `tenant_ref` — espelho mínimo do inquilino do hospedeiro (spec 003, data-model).
# Existe para chave estrangeira e diagnóstico, NUNCA como fonte de verdade de autorização:
# a autorização é sempre a resposta mais recente de `POST /auth/introspect` (P2).
tenant_ref = Table(
    "tenant_ref",
    metadados,
    Column("tenant_id", Text, primary_key=True),
    Column("nome_exibicao", Text, nullable=True),
    Column("visto_em", INSTANTE, nullable=False),
    comment="Espelho mínimo do inquilino do hospedeiro; nunca fonte de autorização.",
)

# `projeto` — o agregado. `usuario_id` entra na migração 0002 (M1, spec 004): o dono é o
# par (inquilino, usuário) da introspecção, e é ele que isola.
projeto = Table(
    "projeto",
    metadados,
    Column("id", PgUUID(as_uuid=True), primary_key=True),
    Column("tenant_id", Text, ForeignKey("tenant_ref.tenant_id"), nullable=False),
    Column("usuario_id", Text, nullable=False),
    Column("nome", Text, nullable=False),
    Column("ferramenta", Text, nullable=False),
    Column("descricao_do_problema", Text, nullable=False, server_default=""),
    Column("versao", Integer, nullable=False, server_default="1"),
    Column("criado_em", INSTANTE, nullable=False),
    Column("atualizado_em", INSTANTE, nullable=False),
    Column("apagado_em", INSTANTE, nullable=True),
    Index("ix_projeto_tenant_id_atualizado_em", "tenant_id", "atualizado_em"),
)

# `no` — filho do agregado (spec 004). Sem semântica TOC: `tipo` é enum extensível e vale
# `generico` no M1; Efeito Indesejável e premissa são M2 em diante (RN-04).
no = Table(
    "no",
    metadados,
    Column("id", PgUUID(as_uuid=True), primary_key=True),
    Column(
        "projeto_id",
        PgUUID(as_uuid=True),
        ForeignKey("projeto.id", ondelete="CASCADE"),
        nullable=False,
    ),
    Column("tipo", Text, nullable=False, server_default="generico"),
    Column("titulo", Text, nullable=False),
    Column("descricao", Text, nullable=True),
    Column("pos_x", Numeric(12, 3), nullable=False),
    Column("pos_y", Numeric(12, 3), nullable=False),
    Column("recolhido", Boolean, nullable=False, server_default="false"),
    Column("criado_em", INSTANTE, nullable=False),
    Column("alterado_em", INSTANTE, nullable=False),
    Column("apagado_em", INSTANTE, nullable=True),
    Index("ix_no_projeto_id", "projeto_id"),
    comment="Nó de um diagrama lógico. `tipo` é enum extensível; sem semântica TOC no M1.",
)

# `aresta_causal` — dirigida, lê-se "Se origem, então destino" (spec 004, RN-01).
# As duas restrições abaixo são as regras RN-02 e RN-03 impostas PELO BANCO, além do
# domínio: invariante que só vive no código é invariante que a próxima ferramenta viola.
aresta_causal = Table(
    "aresta_causal",
    metadados,
    Column("id", PgUUID(as_uuid=True), primary_key=True),
    Column(
        "projeto_id",
        PgUUID(as_uuid=True),
        ForeignKey("projeto.id", ondelete="CASCADE"),
        nullable=False,
    ),
    Column(
        "origem_id", PgUUID(as_uuid=True), ForeignKey("no.id", ondelete="CASCADE"),
        nullable=False,
    ),
    Column(
        "destino_id", PgUUID(as_uuid=True), ForeignKey("no.id", ondelete="CASCADE"),
        nullable=False,
    ),
    Column("rotulo", Text, nullable=True),
    Column("criado_em", INSTANTE, nullable=False),
    Column("alterado_em", INSTANTE, nullable=False),
    Column("apagado_em", INSTANTE, nullable=True),
    CheckConstraint("origem_id <> destino_id", name="sem_auto_laco"),
    UniqueConstraint("projeto_id", "origem_id", "destino_id", name="uq_aresta_par"),
    Index("ix_aresta_causal_projeto_id", "projeto_id"),
    comment='Aresta dirigida: lê-se "Se origem, então destino" (RN-01).',
)

# ---------------------------------------------------------------------------------------
# M2 · Árvore da Realidade Atual (spec 005). O que NÃO está aqui é tão informativo quanto
# o que está: **a validação formal não é persistida**. Ela é função pura e determinística
# do texto do nó (`toc_api.dominio.criterios_ude`), então gravá-la criaria uma segunda
# fonte de verdade que envelheceria em silêncio na primeira vez que o léxico mudasse de
# versão. O repositório a recalcula ao reidratar; o que fica gravado é o que NÃO se
# recalcula: a ficha, o status (decisão humana), os pareceres e o exame dos elos.
# ---------------------------------------------------------------------------------------

# `ude` — o marcador e a ficha, um por nó marcado (spec 005, RF-02/RF-03).
ude = Table(
    "ude",
    metadados,
    Column(
        "no_id", PgUUID(as_uuid=True), ForeignKey("no.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "projeto_id", PgUUID(as_uuid=True), ForeignKey("projeto.id", ondelete="CASCADE"),
        nullable=False,
    ),
    Column("status", Text, nullable=False, server_default="pendente"),
    Column("area_impactada", Text, nullable=False, server_default=""),
    Column("objetivo_afetado", Text, nullable=False, server_default=""),
    Column("evidencias", ARRAY(Text), nullable=False, server_default="{}"),
    Column("frequencia", Text, nullable=False, server_default=""),
    Column("impactos_estimados", Text, nullable=False, server_default=""),
    Index("ix_ude_projeto_id", "projeto_id"),
    comment="Marcador de Efeito Indesejável e a ficha da TOC; um por nó marcado.",
)

# `ude_parecer` — o julgamento sobre o que nenhuma função pura decide. SOMENTE-ACRÉSCIMO:
# a spec 005 (RF-13) diz "pareceres se acumulam, nunca se sobrescrevem", e é por isso que
# a chave é do parecer e não do nó.
ude_parecer = Table(
    "ude_parecer",
    metadados,
    Column("id", PgUUID(as_uuid=True), primary_key=True),
    Column(
        "no_id", PgUUID(as_uuid=True), ForeignKey("ude.no_id", ondelete="CASCADE"),
        nullable=False,
    ),
    Column("autor", Text, nullable=False),
    Column("origem", Text, nullable=False),
    Column("favoravel", Boolean, nullable=False),
    Column("justificativa", Text, nullable=False),
    Column("instante", INSTANTE, nullable=False),
    Column("proposta_id", Text, nullable=True),
    Column("criterios", ARRAY(Text), nullable=False, server_default="{}"),
    Index("ix_ude_parecer_no_id", "no_id"),
    comment="Parecer de julgamento, somente-acréscimo (RF-13). `origem`: humano|catalogo.",
)

# `elo_exame` — o exame de suficiência da aresta (RF-22). Um por aresta, no máximo.
elo_exame = Table(
    "elo_exame",
    metadados,
    Column(
        "aresta_id", PgUUID(as_uuid=True),
        ForeignKey("aresta_causal.id", ondelete="CASCADE"), primary_key=True,
    ),
    Column(
        "projeto_id", PgUUID(as_uuid=True), ForeignKey("projeto.id", ondelete="CASCADE"),
        nullable=False,
    ),
    Column("estado", Text, nullable=False, server_default="nao_examinado"),
    Column("reserva", Text, nullable=False, server_default=""),
    CheckConstraint(
        "estado <> 'insuficiente' and estado <> 'com_reserva' or length(reserva) > 0",
        name="reserva_obrigatoria",
    ),
    Index("ix_elo_exame_projeto_id", "projeto_id"),
    comment="Exame de suficiência do elo; reserva obrigatória em insuficiente/com_reserva.",
)

# `conector_e` — a conjunção "Se A e B, então C" (RN-11).
conector_e = Table(
    "conector_e",
    metadados,
    Column("id", PgUUID(as_uuid=True), primary_key=True),
    Column(
        "projeto_id", PgUUID(as_uuid=True), ForeignKey("projeto.id", ondelete="CASCADE"),
        nullable=False,
    ),
    Column(
        "destino_id", PgUUID(as_uuid=True), ForeignKey("no.id", ondelete="CASCADE"),
        nullable=False,
    ),
    Index("ix_conector_e_projeto_id", "projeto_id"),
    comment='Conector E (conjunção): "Se A e B, então C" — RN-11 da spec 005.',
)

# A restrição de unicidade abaixo é a RN-11 imposta PELO BANCO: uma aresta pertence a no
# máximo um conector. Invariante que só vive no código é invariante que a próxima
# ferramenta viola sem perceber.
conector_e_aresta = Table(
    "conector_e_aresta",
    metadados,
    Column(
        "conector_id", PgUUID(as_uuid=True),
        ForeignKey("conector_e.id", ondelete="CASCADE"), primary_key=True,
    ),
    Column(
        "aresta_id", PgUUID(as_uuid=True),
        ForeignKey("aresta_causal.id", ondelete="CASCADE"), primary_key=True,
    ),
    UniqueConstraint("aresta_id", name="uq_conector_aresta_unica"),
)
