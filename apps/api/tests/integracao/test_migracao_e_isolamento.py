"""O teste que sobe contra o PostgreSQL real: migração, isolamento e exclusão reversível.

Cobre, no banco de verdade (brief §1 e §4):
- `alembic upgrade head` cria o esquema mínimo do M1 (spec 004);
- toda leitura é filtrada pelo inquilino — a leitura cruzada volta vazia (spec 003,
  invariante 1 do `data-model.md`; spec 004, RNF-03);
- a exclusão é reversível de verdade: a linha continua lá, com `apagado_em` preenchido;
- o `downgrade` volta o esquema ao vazio sem resíduo (spec 003, RF-29 / DoD 8).

Nenhum dado real de pessoa: personas fictícias, ADR 0006.
"""
from __future__ import annotations

import os
import subprocess
from uuid import uuid4

import pytest
from sqlalchemy import inspect, text

from toc_api.aplicacao.projetos import (
    CriarProjeto,
    ExcluirProjeto,
    ListarProjetos,
    RestaurarProjeto,
)
from toc_api.dominio.identidade import DonoDoProjeto
from toc_api.infra.configuracao import Configuracao
from toc_api.infra.observabilidade.otel import RastreadorNulo
from toc_api.infra.persistencia.fabrica import criar_persistencia
from toc_api.infra.relogio import RelogioDoSistema

from .conftest import RAIZ_DA_API

pytestmark = pytest.mark.integracao

HORIZONTE = DonoDoProjeto(inquilino_id="inq-horizonte", usuario_id="usr-facilitadora")
ALVORADA = DonoDoProjeto(inquilino_id="inq-alvorada", usuario_id="usr-consultor")

TABELAS_ESPERADAS = {"tenant_ref", "projeto", "no", "aresta_causal", "alembic_version"}


def persistencia_de(url: str, esquema: str):
    return criar_persistencia(
        Configuracao.do_ambiente({"DATABASE_URL": url, "TOC_DB_SCHEMA": esquema})
    )


def test_a_migracao_cria_o_esquema_minimo_do_m1(url_postgres, esquema_migrado):
    persistencia = persistencia_de(url_postgres, esquema_migrado)
    inspetor = inspect(persistencia.motor)
    tabelas = set(inspetor.get_table_names(schema=esquema_migrado))
    assert TABELAS_ESPERADAS <= tabelas, f"faltou tabela: {TABELAS_ESPERADAS - tabelas}"


def test_a_fabrica_escolhe_postgres_quando_ha_database_url(url_postgres, esquema_migrado):
    assert persistencia_de(url_postgres, esquema_migrado).backend == "postgres"
    assert criar_persistencia(Configuracao.do_ambiente({})).backend == "memoria"


def test_isolamento_por_inquilino_no_banco_real(url_postgres, esquema_migrado):
    persistencia = persistencia_de(url_postgres, esquema_migrado)
    repo = persistencia.projetos
    rastro, relogio = RastreadorNulo(), RelogioDoSistema()
    criar = CriarProjeto(rastreador=rastro, repositorio=repo, relogio=relogio)

    meu = criar.rodar(dono=HORIZONTE, nome="Instituição Horizonte — ARA da evasão")
    alheio = criar.rodar(dono=ALVORADA, nome="Cooperativa Alvorada — ARA do atraso")

    listar = ListarProjetos(rastreador=rastro, repositorio=repo)
    meus = listar.rodar(dono=HORIZONTE)
    assert [p.id for p in meus] == [meu.id]

    # A leitura através da fronteira não devolve nada — e não vaza existência.
    assert repo.obter(HORIZONTE.inquilino_id, alheio.id) is None
    assert repo.obter(ALVORADA.inquilino_id, alheio.id) is not None

    # E as duas linhas existem mesmo no banco: a lista curta é filtro, não ausência.
    with persistencia.motor.connect() as conexao:
        total = conexao.execute(text("select count(*) from projeto")).scalar_one()
    assert total == 2


def test_exclusao_e_reversivel_no_banco_real(url_postgres, esquema_migrado):
    persistencia = persistencia_de(url_postgres, esquema_migrado)
    repo = persistencia.projetos
    rastro, relogio = RastreadorNulo(), RelogioDoSistema()

    criado = CriarProjeto(rastreador=rastro, repositorio=repo, relogio=relogio).rodar(
        dono=HORIZONTE, nome="Instituição Horizonte — ARA da evasão"
    )
    ExcluirProjeto(rastreador=rastro, repositorio=repo, relogio=relogio).rodar(
        dono=HORIZONTE, projeto_id=criado.id
    )

    assert ListarProjetos(rastreador=rastro, repositorio=repo).rodar(dono=HORIZONTE) == []

    # Exclusão SUAVE: a linha continua no banco, com o instante preenchido.
    with persistencia.motor.connect() as conexao:
        apagado_em = conexao.execute(
            text("select apagado_em from projeto where id = :i"), {"i": criado.id}
        ).scalar_one()
    assert apagado_em is not None

    RestaurarProjeto(rastreador=rastro, repositorio=repo, relogio=relogio).rodar(
        dono=HORIZONTE, projeto_id=criado.id
    )
    voltou = ListarProjetos(rastreador=rastro, repositorio=repo).rodar(dono=HORIZONTE)
    assert [p.nome for p in voltou] == ["Instituição Horizonte — ARA da evasão"]


def test_o_banco_recusa_auto_laco_e_aresta_duplicada(url_postgres, esquema_migrado):
    """RN-02 e RN-03 da spec 004 — impostas no esquema, não só no domínio."""
    persistencia = persistencia_de(url_postgres, esquema_migrado)
    repo = persistencia.projetos
    projeto = CriarProjeto(
        rastreador=RastreadorNulo(), repositorio=repo, relogio=RelogioDoSistema()
    ).rodar(dono=HORIZONTE, nome="Instituição Horizonte — ARA da evasão")

    a, b = uuid4(), uuid4()
    with persistencia.motor.begin() as conexao:
        for no_id, titulo in ((a, "Evasão alta no 1º semestre"), (b, "Tutoria não acontece")):
            conexao.execute(
                text(
                    "insert into no (id, projeto_id, tipo, titulo, pos_x, pos_y,"
                    " recolhido, criado_em, alterado_em)"
                    " values (:id, :p, 'generico', :t, 0, 0, false, now(), now())"
                ),
                {"id": no_id, "p": projeto.id, "t": titulo},
            )
        conexao.execute(
            text(
                "insert into aresta_causal (id, projeto_id, origem_id, destino_id,"
                " criado_em, alterado_em) values (:id, :p, :o, :d, now(), now())"
            ),
            {"id": uuid4(), "p": projeto.id, "o": a, "d": b},
        )

    from sqlalchemy.exc import IntegrityError

    with pytest.raises(IntegrityError):  # RN-02: origem ≠ destino
        with persistencia.motor.begin() as conexao:
            conexao.execute(
                text(
                    "insert into aresta_causal (id, projeto_id, origem_id, destino_id,"
                    " criado_em, alterado_em) values (:id, :p, :o, :o, now(), now())"
                ),
                {"id": uuid4(), "p": projeto.id, "o": a},
            )

    with pytest.raises(IntegrityError):  # RN-03: par (origem, destino) único
        with persistencia.motor.begin() as conexao:
            conexao.execute(
                text(
                    "insert into aresta_causal (id, projeto_id, origem_id, destino_id,"
                    " criado_em, alterado_em) values (:id, :p, :o, :d, now(), now())"
                ),
                {"id": uuid4(), "p": projeto.id, "o": a, "d": b},
            )


def test_downgrade_volta_ao_vazio_sem_residuo(url_postgres, esquema_migrado):
    """Spec 003, RF-29 / DoD 8: upgrade → downgrade num banco limpo, sem resíduo."""
    ambiente = {**os.environ, "DATABASE_URL": url_postgres, "TOC_DB_SCHEMA": esquema_migrado}
    executado = subprocess.run(
        ["alembic", "downgrade", "base"],
        cwd=RAIZ_DA_API,
        env=ambiente,
        capture_output=True,
        text=True,
    )
    assert executado.returncode == 0, f"{executado.stdout}\n{executado.stderr}"

    persistencia = persistencia_de(url_postgres, esquema_migrado)
    restantes = set(inspect(persistencia.motor).get_table_names(schema=esquema_migrado))
    # `alembic_version` sobrevive por desenho do Alembic; nenhuma tabela NOSSA sobrevive.
    assert restantes - {"alembic_version"} == set(), f"resíduo: {restantes}"
