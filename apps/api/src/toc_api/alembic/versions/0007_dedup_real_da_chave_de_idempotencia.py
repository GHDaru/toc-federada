"""0007 — a chave de idempotência passa a deduplicar de verdade (APH-5.3).

Siglas, uma vez neste arquivo: **APH** — Aplicação ↔ Harness · **FSM** — máquina de estados
finitos · **SQL** — *Structured Query Language*.

## O defeito que esta migração fecha

`proposta_de_acao.idempotency_key` existia desde a revisão 0004, era gravada em toda
confirmação e **nunca era consultada por ninguém** — a varredura
`grep -rn "idempotency_key"` mostrava só escritas. O APH-5.3 pede outra coisa: *"a
confirmação DEVERIA carregar `idempotency_key` com deduplicação real, isto é: a mesma chave
produz uma execução e quantas respostas idênticas forem pedidas"*. Uma coluna que ninguém lê
não deduplica nada.

O índice único **parcial** por `(tenant_id, idempotency_key)` é o que torna a promessa
verdade no único lugar em que ela não depende de disciplina: o banco. Parcial porque
`idempotency_key` é opcional no §A.6 do Anexo A — a maioria das propostas não a carrega, e
`NULL` não pode colidir com `NULL`. Por inquilino porque a chave é do cliente daquele
inquilino: duas instituições que sorteiem o mesmo identificador não são a mesma decisão.

Ele **não** é a trava da corrida — essa é o `UPDATE … WHERE estado = :estado_lido` do
adaptador, que não precisa de esquema novo porque a coluna `estado` já existe. Este índice
é a segunda metade: a que impede a mesma chave de produzir uma segunda execução por outro
caminho.

## Por que esta migração pode RECUSAR, e por que ela não limpa nada sozinha

Um banco que rodou o código antigo **já pode conter** os pares duplicados que o índice
passa a proibir — foi medido no cluster de desenvolvimento deste repositório, que trazia
`(inq-alfa, k-1)` repetido. Diante disso há duas rotas, e a escolhida está declarada:

- **apagar ou zerar a chave das linhas perdedoras** seria a migração mexendo, sozinha e em
  silêncio, em linhas de **governança** — o registro de quem decidiu o quê. Uma migração não
  tem autoridade para isso;
- **recusar, dizendo exatamente quais pares colidem e qual comando os inspeciona**, deixa a
  decisão com quem tem autoridade e não perde nada. É a mesma postura fail-closed do resto
  do serviço, e a recusa só acontece num banco que efetivamente executou o defeito.

Revisão: 0007
Anterior: 0006 (M4 — árvores de futuro e implementação)
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None

NOME = "uq_proposta_de_acao_tenant_id_idempotency_key"

DUPLICADAS = sa.text(
    """
    select tenant_id, idempotency_key, count(*) as quantas
      from proposta_de_acao
     where idempotency_key is not null
     group by tenant_id, idempotency_key
    having count(*) > 1
     order by quantas desc, tenant_id, idempotency_key
     limit 20
    """
)


def upgrade() -> None:
    # Fail-closed antes de criar o índice: `CREATE UNIQUE INDEX` sobre dado duplicado falha
    # com a mensagem do driver, que nomeia UM par e não diz o que fazer. Esta consulta
    # nomeia até vinte e entrega o comando de inspeção.
    colisoes = op.get_bind().execute(DUPLICADAS).fetchall()
    if colisoes:
        listadas = ", ".join(
            f"({t!r}, {k!r}) ×{n}" for t, k, n in colisoes
        )
        raise RuntimeError(
            "0007 recusada: este banco já tem chave de idempotência repetida dentro do "
            "mesmo inquilino — são linhas gravadas pelo código anterior, que permitia a "
            f"mesma chave produzir mais de uma execução (APH-5.3). Pares em colisão: "
            f"{listadas}. Esta migração NÃO limpa linhas de governança sozinha; decida o "
            "que fazer com elas e rode de novo. Para inspecionar: "
            "select tenant_id, idempotency_key, count(*) from proposta_de_acao "
            "where idempotency_key is not null group by 1, 2 having count(*) > 1;"
        )
    op.create_index(
        NOME,
        "proposta_de_acao",
        ["tenant_id", "idempotency_key"],
        unique=True,
        postgresql_where="idempotency_key is not null",
    )


def downgrade() -> None:
    op.drop_index(NOME, table_name="proposta_de_acao")
