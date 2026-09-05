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
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
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

# ---------------------------------------------------------------------------------------
# M7 · Federação APH (Aplicação ↔ Harness) — a governança de ação (spec 006).
#
# Duas tabelas, e a decisão de haver DUAS é o requisito: a proposta é **mutável** (ela
# atravessa a máquina de estados) e o traço é **somente-acréscimo** (APH-5.5: existe para
# 100% das ações, inclusive as recusadas). Guardar as duas coisas numa linha só faria a
# auditoria depender do estado corrente do que ela audita.
#
# O que NÃO está aqui, e é decisão declarada: o **log de conversa** do fio. Ele vive em
# memória (`infra/federacao/memoria.py`), porque o replay do APH-1.3 reconstrói a conversa
# dentro do processo que a atende. O que não pode ser volátil é a governança — e é
# exatamente ela que tem tabela.
#
# Nenhuma das duas tem chave estrangeira para `tenant_ref`, e o motivo é substantivo: uma
# proposta pode ser **recusada** antes de existir qualquer projeto daquele inquilino, e
# exigir a linha de espelho transformaria uma recusa auditável num erro de integridade —
# perdendo justamente o registro que o APH-5.5 obriga a manter.
# ---------------------------------------------------------------------------------------

proposta_de_acao = Table(
    "proposta_de_acao",
    metadados,
    Column("proposal_id", Text, primary_key=True),
    Column("tenant_id", Text, nullable=False),
    Column("usuario_id", Text, nullable=False),
    Column("action_id", Text, nullable=False),
    Column("risk", Text, nullable=False),
    Column("origem", Text, nullable=False),
    Column("estado", Text, nullable=False),
    Column("args", JSONB, nullable=False, server_default="{}"),
    Column("alvos", ARRAY(Text), nullable=False, server_default="{}"),
    Column("contexto_hash", Text, nullable=True),
    Column("criada_em", INSTANTE, nullable=False),
    Column("vence_em", INSTANTE, nullable=False),
    Column("decidida_em", INSTANTE, nullable=True),
    Column("idempotency_key", Text, nullable=True),
    Column("execucoes", Integer, nullable=False, server_default="0"),
    Column("desfecho_status", Text, nullable=True),
    Column("desfecho_mensagem", Text, nullable=False, server_default=""),
    Column("outcomes", JSONB, nullable=False, server_default="[]"),
    CheckConstraint(
        "origem in ('humano','ia')",
        name="origem_do_vocabulario",
    ),
    CheckConstraint(
        "estado in ('proposed','awaiting_approval','confirmed','executing',"
        "'executed','failed','cancelled','denied','expired')",
        name="estado_da_fsm",
    ),
    Index("ix_proposta_de_acao_tenant_id_estado", "tenant_id", "estado"),
    comment="Proposta de ação governada (APH-5.1); `estado` é a FSM validada em código.",
)

traco_de_execucao = Table(
    "traco_de_execucao",
    metadados,
    Column("id", PgUUID(as_uuid=True), primary_key=True),
    Column("proposal_id", Text, nullable=False),
    Column("action_id", Text, nullable=False),
    Column("desfecho", Text, nullable=False),
    Column("tenant_id", Text, nullable=False),
    Column("usuario_id", Text, nullable=False),
    Column("origem", Text, nullable=False),
    Column("instante", INSTANTE, nullable=False),
    Column("trace_id", Text, nullable=False, server_default=""),
    Column("motivo", Text, nullable=False, server_default=""),
    Column("outcomes", JSONB, nullable=False, server_default="[]"),
    CheckConstraint(
        "desfecho in ('executed','failed','denied','cancelled','expired')",
        name="desfecho_do_vocabulario_a3",
    ),
    Index("ix_traco_de_execucao_tenant_id_instante", "tenant_id", "instante"),
    comment="Traço somente-acréscimo; existe para 100% das ações, inclusive recusadas.",
)


# ---------------------------------------------------------------------------------------
# M3 · Nuvem de Conflito (spec 007). O que NÃO está aqui é decisão registrada:
#
# 1. **Não há tabela de entidade nem de aresta da nuvem.** As 5 entidades são linhas de
#    `no` cujo `tipo` carrega o papel (`nc_a` … `nc_d_prime`), e as 7 arestas são linhas de
#    `aresta_causal`. A chave da aresta (`A_B`, `D_C`, …) é **derivada do par de papéis**
#    no domínio — uma coluna de chave seria uma segunda fonte de verdade a envelhecer, e a
#    topologia fixa (RN-01) já garante que o par existe e é único.
# 2. **Não há coluna de "tem semeadura".** A `ReferenciaDeSemeadura` (INT-06) existe
#    exatamente quando a injeção está `escolhida`; guardar a redundância abriria a
#    possibilidade de as duas discordarem. O que se guarda é o destino, que o ciclo 008
#    preencherá.
# ---------------------------------------------------------------------------------------

# `nc_nuvem` — o que é do agregado e não cabe no `projeto`: o racional e a costura tipada
# com a Árvore da Realidade Atual (INT-05). Uma linha por projeto do tipo `nc`.
nc_nuvem = Table(
    "nc_nuvem",
    metadados,
    Column(
        "projeto_id", PgUUID(as_uuid=True), ForeignKey("projeto.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column("racional", Text, nullable=False, server_default=""),
    Column("origem_ferramenta", Text, nullable=True),
    Column("origem_projeto_id", PgUUID(as_uuid=True), nullable=True),
    Column("origem_nos", ARRAY(PgUUID(as_uuid=True)), nullable=False, server_default="{}"),
    CheckConstraint(
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

# `nc_premissa` — o que sustenta uma aresta (RF-12). As três restrições abaixo são as
# regras do domínio impostas PELO BANCO: premissa vazia não existe (round 007: "nunca
# sai"), estado fora do vocabulário não existe, e desafiar exige justificativa (RF-13).
nc_premissa = Table(
    "nc_premissa",
    metadados,
    Column("id", PgUUID(as_uuid=True), primary_key=True),
    Column(
        "projeto_id", PgUUID(as_uuid=True), ForeignKey("projeto.id", ondelete="CASCADE"),
        nullable=False,
    ),
    Column(
        "aresta_id", PgUUID(as_uuid=True),
        ForeignKey("aresta_causal.id", ondelete="CASCADE"), nullable=False,
    ),
    Column("texto", Text, nullable=False),
    Column("ordem", Integer, nullable=False, server_default="0"),
    Column("estado", Text, nullable=False, server_default="vigente"),
    Column("justificativa", Text, nullable=False, server_default=""),
    Column("arquivada", Boolean, nullable=False, server_default="false"),
    CheckConstraint("length(btrim(texto)) > 0", name="premissa_nao_vazia"),
    CheckConstraint("estado in ('vigente', 'desafiada')", name="estado_da_premissa"),
    CheckConstraint(
        "estado <> 'desafiada' or length(btrim(justificativa)) > 0",
        name="justificativa_do_desafio",
    ),
    Index("ix_nc_premissa_projeto_id", "projeto_id"),
    Index("ix_nc_premissa_aresta_id", "aresta_id"),
    comment="Premissa de uma aresta da nuvem; vazia não entra, desafiada exige motivo.",
)

# `nc_injecao` — a solução que quebra UMA premissa (RN-04). A chave estrangeira
# `premissa_id` é `NOT NULL` de propósito: "injeção sem premissa não existe" deixa de ser
# disciplina e vira impossibilidade física.
nc_injecao = Table(
    "nc_injecao",
    metadados,
    Column("id", PgUUID(as_uuid=True), primary_key=True),
    Column(
        "projeto_id", PgUUID(as_uuid=True), ForeignKey("projeto.id", ondelete="CASCADE"),
        nullable=False,
    ),
    Column(
        "premissa_id", PgUUID(as_uuid=True),
        ForeignKey("nc_premissa.id", ondelete="CASCADE"), nullable=False,
    ),
    Column("texto", Text, nullable=False),
    Column("status", Text, nullable=False, server_default="candidata"),
    Column("separacao", Text, nullable=True),
    Column("arquivada", Boolean, nullable=False, server_default="false"),
    Column(
        "semeadura_projeto_id", PgUUID(as_uuid=True),
        ForeignKey("projeto.id", ondelete="SET NULL"), nullable=True,
    ),
    CheckConstraint("length(btrim(texto)) > 0", name="injecao_nao_vazia"),
    CheckConstraint(
        "status in ('candidata', 'escolhida', 'descartada')", name="status_da_injecao"
    ),
    CheckConstraint(
        "separacao is null or separacao in"
        " ('espaco', 'tempo', 'partes', 'grau', 'condicao')",
        name="separacao_triz",
    ),
    CheckConstraint(
        "semeadura_projeto_id is null or status = 'escolhida'",
        name="semeadura_so_de_escolhida",
    ),
    Index("ix_nc_injecao_projeto_id", "projeto_id"),
    Index("ix_nc_injecao_premissa_id", "premissa_id"),
    comment="Injeção ligada a UMA premissa (RN-04); status na FSM candidata/escolhida/descartada.",
)
