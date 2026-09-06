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
    ForeignKeyConstraint,
    Index,
    Integer,
    MetaData,
    Numeric,
    Table,
    Text,
    UniqueConstraint,
    text,
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
    # A deduplicação REAL do APH-5.3, no único lugar em que ela não depende de disciplina.
    # Parcial porque `idempotency_key` é opcional no §A.6 e `NULL` não colide com `NULL`;
    # por inquilino porque a chave é do cliente daquele inquilino. Antes disto a coluna era
    # gravada em toda confirmação e lida em lugar nenhum — uma chave que não deduplicava.
    Index(
        "uq_proposta_de_acao_tenant_id_idempotency_key",
        "tenant_id",
        "idempotency_key",
        unique=True,
        postgresql_where=text("idempotency_key is not null"),
    ),
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


# ---------------------------------------------------------------------------------------
# M4 · Árvores de Futuro e Implementação (spec 008). O que NÃO está aqui é decisão
# registrada, não esquecimento:
#
# 1. **Não há tabela de nó nem de aresta das três árvores.** Injeção, efeito futuro,
#    obstáculo, objetivo intermediário e passo são linhas de `no` cujo `tipo` carrega o
#    papel (`arf_injecao`, `apr_obstaculo`, `at_passo`, …); dependência e precedência são
#    linhas de `aresta_causal`. O `tipo` é enum extensível por decisão do próprio M1
#    (spec 004, RN-04).
# 2. **A Árvore da Realidade Futura reusa `elo_exame` e `conector_e`** — as tabelas do M2.
#    É a contraparte física da decisão 1 do plano do ciclo 008: o pacote de suficiência
#    causal é extraído, nunca copiado, e duas tabelas gêmeas seriam a cópia com outro nome.
# 3. **`referencia_cruzada` não tem chave estrangeira para `projeto`**, e o motivo é a
#    RN-12: exclusão suave SUSPENDE a referência, e `ON DELETE CASCADE` a apagaria numa
#    exclusão definitiva — exatamente o "apagar por efeito colateral" que a regra proíbe.
#    A integridade fica onde a regra mora (o agregado e a vista da cadeia, que mostram o
#    elo `pendente`), e não numa cascata que decide sozinha. É a mesma decisão, pelo mesmo
#    tipo de motivo, que `proposta_de_acao` tomou no ciclo 006.
# ---------------------------------------------------------------------------------------

# `arf_arvore` — o que é do agregado ARF e não cabe no `projeto`: a costura de origem
# (a injeção que a semeou) e os Efeitos Indesejáveis que a cadeia disponibiliza para
# espelho. Uma linha por projeto do tipo `arf`.
arf_arvore = Table(
    "arf_arvore",
    metadados,
    Column(
        "projeto_id", PgUUID(as_uuid=True), ForeignKey("projeto.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column("origem_ferramenta", Text, nullable=True),
    Column("origem_projeto_id", PgUUID(as_uuid=True), nullable=True),
    Column("origem_elementos", ARRAY(PgUUID(as_uuid=True)), nullable=False, server_default="{}"),
    Column("origem_papel", Text, nullable=False, server_default=""),
    Column("udes_da_cadeia", ARRAY(PgUUID(as_uuid=True)), nullable=False, server_default="{}"),
    CheckConstraint(
        "(origem_ferramenta is null and origem_projeto_id is null)"
        " or (origem_ferramenta is not null and origem_projeto_id is not null)",
        name="origem_da_arf_completa",
    ),
    comment=(
        "Cabeçalho da Árvore da Realidade Futura: origem (injeção que a semeou) e os "
        "Efeitos Indesejáveis referenciáveis pelo espelho (RN-03)."
    ),
)

# `arf_espelho` — a marca de Efeito Desejável: qual Efeito Indesejável este efeito futuro
# converte. A unicidade `(projeto_id, ude_id)` é a RN-03 imposta PELO BANCO — "um UDE tem
# no máximo um ED por ARF" deixa de ser disciplina e vira impossibilidade física.
arf_espelho = Table(
    "arf_espelho",
    metadados,
    Column(
        "no_id", PgUUID(as_uuid=True), ForeignKey("no.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "projeto_id", PgUUID(as_uuid=True), ForeignKey("projeto.id", ondelete="CASCADE"),
        nullable=False,
    ),
    Column("ude_id", PgUUID(as_uuid=True), nullable=False),
    Column("projeto_de_origem_id", PgUUID(as_uuid=True), nullable=True),
    UniqueConstraint("projeto_id", "ude_id", name="uq_espelho_por_ude"),
    Index("ix_arf_espelho_projeto_id", "projeto_id"),
    comment="Espelho UDE → Efeito Desejável; no máximo um por UDE em cada ARF (RN-03).",
)

# `arf_ramo_negativo` — o efeito indevido que a injeção traz. As três restrições abaixo são
# a RN-04 imposta pelo banco: vocabulário fechado do estado, `tratado` exige a injeção de
# corte, `aceito` exige justificativa e autor.
arf_ramo_negativo = Table(
    "arf_ramo_negativo",
    metadados,
    Column("id", PgUUID(as_uuid=True), primary_key=True),
    Column(
        "projeto_id", PgUUID(as_uuid=True), ForeignKey("projeto.id", ondelete="CASCADE"),
        nullable=False,
    ),
    Column(
        "raiz_id", PgUUID(as_uuid=True), ForeignKey("no.id", ondelete="CASCADE"),
        nullable=False,
    ),
    Column("estado", Text, nullable=False, server_default="aberto"),
    Column(
        "injecao_de_corte_id", PgUUID(as_uuid=True),
        ForeignKey("no.id", ondelete="SET NULL"), nullable=True,
    ),
    Column("justificativa", Text, nullable=False, server_default=""),
    Column("autor", Text, nullable=False, server_default=""),
    CheckConstraint(
        "estado in ('aberto', 'tratado', 'aceito')", name="estado_do_ramo_negativo"
    ),
    CheckConstraint(
        "estado <> 'tratado' or injecao_de_corte_id is not null",
        name="tratado_exige_injecao_de_corte",
    ),
    CheckConstraint(
        "estado <> 'aceito' or (length(btrim(justificativa)) > 0 and length(btrim(autor)) > 0)",
        name="aceito_exige_justificativa_e_autor",
    ),
    UniqueConstraint("raiz_id", name="uq_ramo_por_raiz"),
    Index("ix_arf_ramo_negativo_projeto_id", "projeto_id"),
    comment="Ramo negativo da ARF: aberto → tratado (com injeção) | aceito (com motivo).",
)

# `apr_arvore` — o cabeçalho da Árvore de Pré-Requisitos: de onde ela foi derivada.
apr_arvore = Table(
    "apr_arvore",
    metadados,
    Column(
        "projeto_id", PgUUID(as_uuid=True), ForeignKey("projeto.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column("origem_ferramenta", Text, nullable=True),
    Column("origem_projeto_id", PgUUID(as_uuid=True), nullable=True),
    Column("origem_elementos", ARRAY(PgUUID(as_uuid=True)), nullable=False, server_default="{}"),
    Column("origem_papel", Text, nullable=False, server_default=""),
    CheckConstraint(
        "(origem_ferramenta is null and origem_projeto_id is null)"
        " or (origem_ferramenta is not null and origem_projeto_id is not null)",
        name="origem_da_apr_completa",
    ),
    comment="Cabeçalho da Árvore de Pré-Requisitos: a origem (efeito ou injeção da ARF).",
)

# `apr_par` — obstáculo ↔ objetivo intermediário que o supera. A unicidade do obstáculo é a
# RF-17 imposta pelo banco: "um OI pode superar vários obstáculos" — a recíproca, não.
apr_par = Table(
    "apr_par",
    metadados,
    Column("id", PgUUID(as_uuid=True), primary_key=True),
    Column(
        "projeto_id", PgUUID(as_uuid=True), ForeignKey("projeto.id", ondelete="CASCADE"),
        nullable=False,
    ),
    Column(
        "obstaculo_id", PgUUID(as_uuid=True), ForeignKey("no.id", ondelete="CASCADE"),
        nullable=False,
    ),
    Column(
        "objetivo_intermediario_id", PgUUID(as_uuid=True),
        ForeignKey("no.id", ondelete="CASCADE"), nullable=False,
    ),
    UniqueConstraint("obstaculo_id", name="uq_par_por_obstaculo"),
    Index("ix_apr_par_projeto_id", "projeto_id"),
    comment="Par obstáculo ↔ objetivo intermediário; o obstáculo tem uma resposta só.",
)

# `apr_julgamento` — o teste de validade do par. SOMENTE-ACRÉSCIMO, como `ude_parecer`:
# a RN-07 diz que o julgamento acumula e nunca é sobrescrito, e por isso a chave é do
# julgamento e não do par.
apr_julgamento = Table(
    "apr_julgamento",
    metadados,
    Column("id", PgUUID(as_uuid=True), primary_key=True),
    Column(
        "par_id", PgUUID(as_uuid=True), ForeignKey("apr_par.id", ondelete="CASCADE"),
        nullable=False,
    ),
    Column("autor", Text, nullable=False),
    Column("valido", Boolean, nullable=False),
    Column("justificativa", Text, nullable=False),
    Column("instante", INSTANTE, nullable=False),
    CheckConstraint("length(btrim(autor)) > 0", name="julgamento_com_autor"),
    CheckConstraint(
        "length(btrim(justificativa)) > 0", name="julgamento_com_justificativa"
    ),
    Index("ix_apr_julgamento_par_id", "par_id"),
    comment="Julgamento do teste IO-Obstáculo, somente-acréscimo (RN-07).",
)

# `apr_elipse` — a conjunção de NECESSIDADE ("A e B precisam existir antes de C").
apr_elipse = Table(
    "apr_elipse",
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
    Index("ix_apr_elipse_projeto_id", "projeto_id"),
    comment='Elipse de simultaneidade: conjunção de necessidade, não de suficiência.',
)

# A unicidade abaixo é a RN-06 imposta pelo banco: uma dependência pertence a no máximo uma
# elipse — a mesma forma da `uq_conector_aresta_unica` do M2, para a lógica irmã.
apr_elipse_dependencia = Table(
    "apr_elipse_dependencia",
    metadados,
    Column(
        "elipse_id", PgUUID(as_uuid=True), ForeignKey("apr_elipse.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "aresta_id", PgUUID(as_uuid=True),
        ForeignKey("aresta_causal.id", ondelete="CASCADE"), primary_key=True,
    ),
    UniqueConstraint("aresta_id", name="uq_elipse_dependencia_unica"),
)

# `at_arvore` — o cabeçalho da Árvore de Transição: o alvo que ela desce a passos.
at_arvore = Table(
    "at_arvore",
    metadados,
    Column(
        "projeto_id", PgUUID(as_uuid=True), ForeignKey("projeto.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column("alvo_ferramenta", Text, nullable=True),
    Column("alvo_projeto_id", PgUUID(as_uuid=True), nullable=True),
    Column("alvo_elementos", ARRAY(PgUUID(as_uuid=True)), nullable=False, server_default="{}"),
    Column("alvo_papel", Text, nullable=False, server_default=""),
    CheckConstraint(
        "(alvo_ferramenta is null and alvo_projeto_id is null)"
        " or (alvo_ferramenta is not null and alvo_projeto_id is not null)",
        name="alvo_da_at_completo",
    ),
    comment="Cabeçalho da Árvore de Transição: o objetivo intermediário de origem.",
)

# `at_passo` — a ficha do passo. As restrições são a RN-10 e a RF-30 impostas pelo banco:
# a tripla nunca é vazia, o status é vocabulário fechado, `bloqueado` exige motivo e
# `concluido` exige o resultado real. Invariante que só vive no código é invariante que a
# próxima ferramenta viola sem perceber.
at_passo = Table(
    "at_passo",
    metadados,
    Column(
        "no_id", PgUUID(as_uuid=True), ForeignKey("no.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "projeto_id", PgUUID(as_uuid=True), ForeignKey("projeto.id", ondelete="CASCADE"),
        nullable=False,
    ),
    Column("acao", Text, nullable=False),
    Column("necessidade", Text, nullable=False),
    Column("resultado_esperado", Text, nullable=False),
    Column("status", Text, nullable=False, server_default="pendente"),
    Column("motivo_do_bloqueio", Text, nullable=False, server_default=""),
    Column("resultado_real", Text, nullable=False, server_default=""),
    CheckConstraint(
        "length(btrim(acao)) > 0 and length(btrim(necessidade)) > 0"
        " and length(btrim(resultado_esperado)) > 0",
        name="tripla_do_passo_obrigatoria",
    ),
    CheckConstraint(
        "status in ('pendente', 'em_execucao', 'concluido', 'bloqueado')",
        name="status_do_passo",
    ),
    CheckConstraint(
        "status <> 'bloqueado' or length(btrim(motivo_do_bloqueio)) > 0",
        name="bloqueado_exige_motivo",
    ),
    CheckConstraint(
        "status <> 'concluido' or length(btrim(resultado_real)) > 0",
        name="concluido_exige_resultado_real",
    ),
    Index("ix_at_passo_projeto_id", "projeto_id"),
    comment="Passo da AT: ação · necessidade · resultado esperado (RN-10) + status.",
)

# `referencia_cruzada` — o agregado do encadeamento (RF-33). `versao` existe pelo mesmo
# motivo da coluna homônima de `projeto`: é a trava otimista, e ela aparece no `WHERE` de
# toda atualização (`scripts/check-trava-otimista.sh` confere).
referencia_cruzada = Table(
    "referencia_cruzada",
    metadados,
    Column("id", PgUUID(as_uuid=True), primary_key=True),
    Column("tenant_id", Text, nullable=False),
    Column("usuario_id", Text, nullable=False),
    Column("tipo", Text, nullable=False),
    Column("origem_ferramenta", Text, nullable=False),
    Column("origem_projeto_id", PgUUID(as_uuid=True), nullable=False),
    Column("origem_elementos", ARRAY(PgUUID(as_uuid=True)), nullable=False, server_default="{}"),
    Column("origem_papel", Text, nullable=False, server_default=""),
    Column("destino_ferramenta", Text, nullable=False),
    Column("destino_projeto_id", PgUUID(as_uuid=True), nullable=False),
    Column("destino_elementos", ARRAY(PgUUID(as_uuid=True)), nullable=False, server_default="{}"),
    Column("destino_papel", Text, nullable=False, server_default=""),
    Column("estado", Text, nullable=False, server_default="ativa"),
    Column("motivo", Text, nullable=False, server_default=""),
    Column("versao", Integer, nullable=False, server_default="1"),
    Column("criada_em", INSTANTE, nullable=False),
    CheckConstraint(
        "tipo in ('promocao_ude_nc', 'semeadura_injecao_arf', 'derivacao_arf_apr',"
        " 'derivacao_oi_at')",
        name="tipo_da_referencia",
    ),
    CheckConstraint("estado in ('ativa', 'pendente')", name="estado_da_referencia"),
    CheckConstraint(
        "estado <> 'pendente' or length(btrim(motivo)) > 0",
        name="pendente_exige_motivo",
    ),
    CheckConstraint(
        "origem_projeto_id <> destino_projeto_id", name="referencia_liga_projetos_distintos"
    ),
    Index("ix_referencia_cruzada_tenant_id_origem_projeto_id", "tenant_id", "origem_projeto_id"),
    Index("ix_referencia_cruzada_tenant_id_destino_projeto_id", "tenant_id", "destino_projeto_id"),
    comment=(
        "Referência cruzada entre ferramentas (RF-33). Sem chave estrangeira para projeto "
        "de propósito: exclusão suave SUSPENDE (RN-12), e cascata apagaria."
    ),
)


# ---------------------------------------------------------------------------------------
# M6 · Focalização (spec 009). O que está aqui e não em `no`/`aresta_causal` é a diferença
# estrutural do módulo: **a análise de focalização não é diagrama**. Ela não tem nó nem
# aresta; o que ela tem é jornada com estado, e por isso as tabelas são próprias.
#
# Três invariantes do domínio impostas **pelo banco**, além do código — invariante que só
# vive no código é invariante que a próxima ferramenta viola sem perceber:
#
# 1. **RN-02** — no máximo um ciclo aberto por análise: índice único PARCIAL sobre
#    `projeto_id` onde `estado = 'aberto'`. Parcial porque os ciclos fechados são muitos e
#    é justamente isso que a regra permite.
# 2. **RN-03** — no máximo uma restrição vigente por ciclo: `ciclo_id` é a chave primária
#    de `foco_restricao`, o que torna a segunda restrição fisicamente impossível.
# 3. **RN-01** — os cinco passos não se criam nem se excluem: a chave primária de
#    `foco_passo` é `(ciclo_id, tipo)` com `tipo` num vocabulário fechado de cinco valores.
#    Não há coluna de identidade a inventar, e não há como um sexto passo entrar.
#
# E o que NÃO está aqui: nenhuma cópia de conteúdo dos módulos M2–M4. `foco_vinculo`
# guarda ferramenta e identificador do projeto de destino, e mais nada — a sétima cópia
# que o núcleo M1 existe para impedir não nasce por uma coluna de conveniência.
# ---------------------------------------------------------------------------------------

# `foco_analise` — o que é do agregado e não cabe no `projeto`: o sistema analisado.
foco_analise = Table(
    "foco_analise",
    metadados,
    Column(
        "projeto_id", PgUUID(as_uuid=True), ForeignKey("projeto.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column("sistema_nome", Text, nullable=False),
    Column("sistema_descricao", Text, nullable=False, server_default=""),
    CheckConstraint("length(btrim(sistema_nome)) > 0", name="sistema_com_nome"),
    comment=(
        "Cabeçalho da análise de focalização: o sistema cuja meta a análise serve. "
        "Uma linha por projeto do tipo focalizacao."
    ),
)

# `foco_ciclo` — uma volta completa dos cinco passos, a unidade da linha do tempo.
foco_ciclo = Table(
    "foco_ciclo",
    metadados,
    Column("id", PgUUID(as_uuid=True), primary_key=True),
    Column(
        "projeto_id", PgUUID(as_uuid=True), ForeignKey("projeto.id", ondelete="CASCADE"),
        nullable=False,
    ),
    Column("ordem", Integer, nullable=False),
    Column("estado", Text, nullable=False, server_default="aberto"),
    Column("aberto_em", INSTANTE, nullable=False),
    Column("fechado_em", INSTANTE, nullable=True),
    CheckConstraint("estado in ('aberto', 'fechado')", name="estado_do_ciclo"),
    CheckConstraint("ordem >= 1", name="ordem_do_ciclo"),
    CheckConstraint(
        "(estado = 'aberto' and fechado_em is null)"
        " or (estado = 'fechado' and fechado_em is not null)",
        name="fechado_tem_data",
    ),
    UniqueConstraint("projeto_id", "ordem", name="uq_foco_ciclo_ordem"),
    # RN-02 imposta PELO BANCO: um ciclo aberto por análise, no máximo.
    Index(
        "uq_foco_ciclo_aberto_por_analise",
        "projeto_id",
        unique=True,
        postgresql_where=text("estado = 'aberto'"),
    ),
    comment="Ciclo de focalização; RN-02 (um aberto por análise) imposta por índice parcial.",
)

# `foco_restricao` — a entidade que dá nome à teoria. `ciclo_id` é a chave primária: é a
# RN-03 ("uma restrição vigente por ciclo") virada impossibilidade física.
foco_restricao = Table(
    "foco_restricao",
    metadados,
    Column(
        "ciclo_id", PgUUID(as_uuid=True), ForeignKey("foco_ciclo.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column("id", PgUUID(as_uuid=True), nullable=False, unique=True),
    Column(
        "projeto_id", PgUUID(as_uuid=True), ForeignKey("projeto.id", ondelete="CASCADE"),
        nullable=False,
    ),
    Column("descricao", Text, nullable=False),
    Column("tipo", Text, nullable=False),
    Column("justificativa", Text, nullable=False),
    Column("autor", Text, nullable=False),
    Column("registrada_em", INSTANTE, nullable=False),
    Column("origem_ferramenta", Text, nullable=True),
    Column("origem_projeto_id", PgUUID(as_uuid=True), nullable=True),
    Column("origem_no_id", PgUUID(as_uuid=True), nullable=True),
    CheckConstraint(
        "tipo in ('fisica', 'politica', 'de_mercado')", name="tipo_da_restricao"
    ),
    CheckConstraint("length(btrim(descricao)) > 0", name="restricao_nao_vazia"),
    CheckConstraint(
        "length(btrim(justificativa)) > 0", name="restricao_com_justificativa"
    ),
    CheckConstraint("length(btrim(autor)) > 0", name="restricao_com_autor"),
    # A origem (INT-02) é tudo ou nada: meia referência não navega para lugar nenhum.
    CheckConstraint(
        "(origem_ferramenta is null and origem_projeto_id is null and origem_no_id is null)"
        " or (origem_ferramenta is not null and origem_projeto_id is not null"
        " and origem_no_id is not null)",
        name="origem_da_restricao_completa",
    ),
    Index("ix_foco_restricao_projeto_id", "projeto_id"),
    comment="Restrição vigente do ciclo; a chave primária por ciclo é a RN-03 no banco.",
)

# `foco_passo` — os cinco. A chave primária `(ciclo_id, tipo)` é a RN-01 no banco: não há
# identidade a inventar, não há sexto passo possível, e reordenar não tem onde acontecer.
foco_passo = Table(
    "foco_passo",
    metadados,
    Column(
        "ciclo_id", PgUUID(as_uuid=True), ForeignKey("foco_ciclo.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column("tipo", Text, primary_key=True),
    Column(
        "projeto_id", PgUUID(as_uuid=True), ForeignKey("projeto.id", ondelete="CASCADE"),
        nullable=False,
    ),
    Column("estado", Text, nullable=False, server_default="pendente"),
    Column("ordem", Integer, nullable=False),
    CheckConstraint(
        "tipo in ('identificar', 'explorar', 'subordinar', 'elevar', 'recomecar')",
        name="tipo_do_passo",
    ),
    CheckConstraint(
        "estado in ('pendente', 'em_andamento', 'concluido')", name="estado_do_passo"
    ),
    CheckConstraint("ordem between 1 and 5", name="ordem_do_passo"),
    Index("ix_foco_passo_projeto_id", "projeto_id"),
    comment="Passo de focalização; a chave (ciclo, tipo) é a ordem canônica no banco (RN-01).",
)

# `foco_decisao` — SOMENTE-ACRÉSCIMO, como `ude_parecer` e `apr_julgamento`. A RN-04 diz
# "decisões de passo não se apagam (reabrir registra novo evento)", e é por isso que a
# chave é da decisão e não do passo: concluir de novo INSERE, nunca sobrescreve.
foco_decisao = Table(
    "foco_decisao",
    metadados,
    Column("id", PgUUID(as_uuid=True), primary_key=True),
    Column("ciclo_id", PgUUID(as_uuid=True), nullable=False),
    Column("passo", Text, nullable=False),
    Column("texto", Text, nullable=False),
    Column("autor", Text, nullable=False),
    Column("instante", INSTANTE, nullable=False),
    Column("ordem", Integer, nullable=False, server_default="0"),
    ForeignKeyConstraint(
        ["ciclo_id", "passo"],
        ["foco_passo.ciclo_id", "foco_passo.tipo"],
        name="fk_foco_decisao_passo",
        ondelete="CASCADE",
    ),
    CheckConstraint("length(btrim(texto)) > 0", name="decisao_nao_vazia"),
    CheckConstraint("length(btrim(autor)) > 0", name="decisao_com_autor"),
    Index("ix_foco_decisao_ciclo_id_passo", "ciclo_id", "passo"),
    comment="Decisão que encerra um passo; somente-acréscimo (RN-04, RF-10).",
)

foco_nota = Table(
    "foco_nota",
    metadados,
    Column("id", PgUUID(as_uuid=True), primary_key=True),
    Column("ciclo_id", PgUUID(as_uuid=True), nullable=False),
    Column("passo", Text, nullable=False),
    Column("texto", Text, nullable=False),
    Column("autor", Text, nullable=False),
    Column("instante", INSTANTE, nullable=False),
    ForeignKeyConstraint(
        ["ciclo_id", "passo"],
        ["foco_passo.ciclo_id", "foco_passo.tipo"],
        name="fk_foco_nota_passo",
        ondelete="CASCADE",
    ),
    CheckConstraint("length(btrim(texto)) > 0", name="nota_nao_vazia"),
    Index("ix_foco_nota_ciclo_id_passo", "ciclo_id", "passo"),
    comment="Nota de passo: texto livre acumulável com autoria (RF-11).",
)

foco_reabertura = Table(
    "foco_reabertura",
    metadados,
    Column("id", PgUUID(as_uuid=True), primary_key=True),
    Column("ciclo_id", PgUUID(as_uuid=True), nullable=False),
    Column("passo", Text, nullable=False),
    Column("justificativa", Text, nullable=False),
    Column("autor", Text, nullable=False),
    Column("instante", INSTANTE, nullable=False),
    ForeignKeyConstraint(
        ["ciclo_id", "passo"],
        ["foco_passo.ciclo_id", "foco_passo.tipo"],
        name="fk_foco_reabertura_passo",
        ondelete="CASCADE",
    ),
    CheckConstraint(
        "length(btrim(justificativa)) > 0", name="reabertura_com_justificativa"
    ),
    Index("ix_foco_reabertura_ciclo_id_passo", "ciclo_id", "passo"),
    comment="Reabertura de passo concluído (RF-10); fica AO LADO da decisão, nunca no lugar.",
)

# `foco_vinculo` — a referência tipada a um projeto de outra ferramenta.
#
# **Sem chave estrangeira para `projeto` na ponta de destino**, e o motivo é o mesmo de
# `referencia_cruzada` do M4: a RNF-04 manda o vínculo cujo destino foi arquivado degradar
# para "referência a projeto arquivado" **legível**, e uma cascata o apagaria numa
# exclusão definitiva — perdendo exatamente o registro que o requisito obriga a mostrar.
# A integridade fica onde a regra mora (o caso de uso `ResolverVinculos`, que responde
# ativo/arquivado/ausente), e não numa cascata que decide sozinha.
foco_vinculo = Table(
    "foco_vinculo",
    metadados,
    Column("id", PgUUID(as_uuid=True), primary_key=True),
    Column("ciclo_id", PgUUID(as_uuid=True), nullable=False),
    Column("passo", Text, nullable=False),
    Column(
        "projeto_id", PgUUID(as_uuid=True), ForeignKey("projeto.id", ondelete="CASCADE"),
        nullable=False,
    ),
    Column("ferramenta", Text, nullable=False),
    Column("alvo_projeto_id", PgUUID(as_uuid=True), nullable=False),
    Column("papel", Text, nullable=False, server_default=""),
    Column("justificativa", Text, nullable=False, server_default=""),
    Column("canonico", Boolean, nullable=False, server_default="true"),
    ForeignKeyConstraint(
        ["ciclo_id", "passo"],
        ["foco_passo.ciclo_id", "foco_passo.tipo"],
        name="fk_foco_vinculo_passo",
        ondelete="CASCADE",
    ),
    CheckConstraint(
        "ferramenta in ('ara', 'nc', 'arf', 'apr', 'at')", name="ferramenta_vinculada"
    ),
    # RN-06 imposta pelo banco: vínculo fora do canônico sem justificativa não existe.
    CheckConstraint(
        "canonico or length(btrim(justificativa)) > 0",
        name="nao_canonico_exige_justificativa",
    ),
    UniqueConstraint(
        "ciclo_id", "passo", "ferramenta", "alvo_projeto_id", name="uq_foco_vinculo"
    ),
    Index("ix_foco_vinculo_projeto_id", "projeto_id"),
    # A navegação de VOLTA (L-03): das ferramentas M2–M4 para a análise que as cita.
    # Consulta indexada em vez de campo novo nos agregados delas.
    Index("ix_foco_vinculo_alvo_projeto_id", "alvo_projeto_id"),
    comment=(
        "Vínculo tipado passo → projeto de ferramenta (RF-14). Sem chave estrangeira para "
        "o destino de propósito: arquivar degrada (RNF-04), cascata apagaria."
    ),
)

# `foco_heranca` — o mecanismo anti-inércia (RN-05). A restrição de check é a regra
# "manter é decisão tão explícita quanto revogar" imposta pelo banco.
foco_heranca = Table(
    "foco_heranca",
    metadados,
    Column("id", PgUUID(as_uuid=True), primary_key=True),
    Column(
        "ciclo_id", PgUUID(as_uuid=True), ForeignKey("foco_ciclo.id", ondelete="CASCADE"),
        nullable=False,
    ),
    Column(
        "projeto_id", PgUUID(as_uuid=True), ForeignKey("projeto.id", ondelete="CASCADE"),
        nullable=False,
    ),
    Column("ciclo_de_origem", Integer, nullable=False),
    Column("passo", Text, nullable=False),
    Column("texto", Text, nullable=False),
    Column("veredito", Text, nullable=False, server_default="pendente"),
    Column("justificativa", Text, nullable=False, server_default=""),
    Column("autor", Text, nullable=False, server_default=""),
    Column("julgada_em", INSTANTE, nullable=True),
    Column("ordem", Integer, nullable=False, server_default="0"),
    CheckConstraint(
        "veredito in ('pendente', 'mantida', 'revogada')", name="veredito_da_heranca"
    ),
    CheckConstraint(
        "passo in ('identificar', 'explorar', 'subordinar', 'elevar', 'recomecar')",
        name="passo_de_origem_da_heranca",
    ),
    CheckConstraint("length(btrim(texto)) > 0", name="heranca_nao_vazia"),
    CheckConstraint(
        "veredito = 'pendente'"
        " or (length(btrim(justificativa)) > 0 and length(btrim(autor)) > 0)",
        name="veredito_exige_justificativa_e_autor",
    ),
    Index("ix_foco_heranca_ciclo_id", "ciclo_id"),
    comment=(
        "Decisão herdada do ciclo anterior com veredito (RN-05): manter exige "
        "justificativa tanto quanto revogar."
    ),
)
