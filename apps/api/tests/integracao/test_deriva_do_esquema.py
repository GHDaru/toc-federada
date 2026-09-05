"""O esquema migrado tem de conferir com o modelo declarado — medido, não confiado.

Por que este arquivo existe (achado real desta entrega, não hipótese): a primeira versão
da migração `0002` nomeou a restrição de auto-laço como `ck_aresta_causal_sem_auto_laco`.
O Alembic aplica a `naming_convention` do `target_metadata` às operações de `op`, e a
convenção do `ck` inclui `%(constraint_name)s` — o nome saiu **duplicado** no banco:

    "ck_aresta_causal_ck_aresta_causal_sem_auto_laco" CHECK (origem_id <> destino_id)

enquanto `tabelas.py` declarava `ck_aresta_causal_sem_auto_laco`. Nada quebrava hoje;
quebraria no primeiro `op.drop_constraint` que usasse o nome declarado. Uma restrição com
nome diferente do declarado é dívida silenciosa — e este é o portão que a torna barulhenta.

`compare_metadata` é **cego** a nome de `CheckConstraint` (é assinatura de colunas que ele
compara), então o nome é conferido separado, contra o catálogo do PostgreSQL. As duas
checagens juntas são o portão; nenhuma delas sozinha teria pego o defeito acima.
"""
from __future__ import annotations

import pytest
from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from sqlalchemy import text

from toc_api.infra.configuracao import Configuracao
from toc_api.infra.persistencia.fabrica import criar_persistencia
from toc_api.infra.persistencia.tabelas import metadados

pytestmark = pytest.mark.integracao

# Nomes que a migração DEVE ter produzido no banco. Escritos aqui à mão de propósito: é o
# que o modelo declara, e o teste falha se o banco disser outra coisa.
RESTRICOES_ESPERADAS = {
    "pk_tenant_ref",
    "pk_projeto",
    "fk_projeto_tenant_id_tenant_ref",
    "pk_no",
    "fk_no_projeto_id_projeto",
    "pk_aresta_causal",
    "fk_aresta_causal_projeto_id_projeto",
    "fk_aresta_causal_origem_id_no",
    "fk_aresta_causal_destino_id_no",
    "ck_aresta_causal_sem_auto_laco",
    "uq_aresta_par",
}


def motor_de(url: str, esquema: str):
    return criar_persistencia(
        Configuracao.do_ambiente({"DATABASE_URL": url, "TOC_DB_SCHEMA": esquema})
    ).motor


def test_o_banco_migrado_nao_deriva_do_modelo_declarado(url_postgres, esquema_migrado):
    motor = motor_de(url_postgres, esquema_migrado)
    with motor.connect() as conexao:
        contexto = MigrationContext.configure(
            conexao, opts={"compare_type": True, "include_schemas": False}
        )
        diferencas = compare_metadata(contexto, metadados)
    # `alembic_version` é do Alembic, não do modelo: não conta como deriva.
    diferencas = [d for d in diferencas if "alembic_version" not in repr(d)]
    assert diferencas == [], f"deriva entre migração e modelo: {diferencas}"


def test_os_nomes_das_restricoes_sao_os_declarados(url_postgres, esquema_migrado):
    motor = motor_de(url_postgres, esquema_migrado)
    with motor.connect() as conexao:
        nomes = {
            linha[0]
            for linha in conexao.execute(
                text(
                    "select con.conname from pg_constraint con"
                    " join pg_namespace ns on ns.oid = con.connamespace"
                    " where ns.nspname = :esquema"
                ),
                {"esquema": esquema_migrado},
            )
        }
    faltando = RESTRICOES_ESPERADAS - nomes
    assert faltando == set(), f"restrição com nome diferente do declarado. No banco: {nomes}"
