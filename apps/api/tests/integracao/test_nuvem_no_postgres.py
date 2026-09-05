"""A Nuvem de Conflito (NC) contra o PostgreSQL REAL — nunca SQLite (brief §1).

Siglas, uma vez: **NC** — Nuvem de Conflito · **ARA** — Árvore da Realidade Atual ·
**UDE** — Efeito Indesejável · **TOC** — Teoria das Restrições · **TRIZ** — Teoria da
Resolução Inventiva de Problemas · **SQL** — *Structured Query Language*.

O que só um banco de verdade prova, e por isso está aqui e não na suíte de domínio:

- a **migração 0005** cria as três tabelas do M3 e o `downgrade` as remove sem resíduo;
- a **ida e volta** não perde nada — premissa desafiada continua desafiada, injeção
  escolhida continua escolhida com a separação TRIZ e a referência de semeadura;
- o **isolamento por inquilino** vale para a nuvem como vale para o projeto (RNF-03);
- as invariantes que o domínio impõe estão **também** no banco: premissa vazia não entra,
  injeção sem premissa não entra, desafiada sem justificativa não entra. Invariante que só
  vive no código é invariante que a próxima ferramenta viola sem perceber.
"""
from __future__ import annotations

import subprocess
from uuid import uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from toc_api.dominio.ara import novo_projeto_ara
from toc_api.dominio.nuvem import (
    ChaveDaAresta,
    EstadoDaPremissa,
    PapelDaEntidade,
    SeparacaoTRIZ,
    StatusDeInjecao,
    derivar_nuvem_de_udes,
    novo_projeto_nc,
)
from toc_api.infra.configuracao import Configuracao
from toc_api.infra.persistencia.fabrica import criar_persistencia

from ..dominio.nuvem_sintetica import AGORA, DILEMA, DONO, OUTRO_DONO, UDES_SINTETICOS
from .conftest import RAIZ_DA_API

pytestmark = pytest.mark.integracao

TABELAS_DO_M3 = ("nc_nuvem", "nc_premissa", "nc_injecao")


def persistencia_de(url: str, esquema: str):
    return criar_persistencia(
        Configuracao.do_ambiente({"DATABASE_URL": url, "TOC_DB_SCHEMA": esquema})
    )


def nuvem_preenchida(dono=DONO):
    nuvem = novo_projeto_nc(id=uuid4(), dono=dono, nome="Dilema da expansão", em=AGORA)
    for papel, texto in DILEMA.items():
        nuvem.editar_entidade(papel, texto, em=AGORA)
    nuvem.editar_racional("A instituição precisa de caixa e de reputação.", em=AGORA)
    return nuvem


def test_a_migracao_cria_as_tres_tabelas_do_m3(url_postgres, esquema_migrado) -> None:
    motor = persistencia_de(url_postgres, esquema_migrado).motor
    with motor.connect() as conexao:
        existentes = {
            linha[0]
            for linha in conexao.execute(
                text(
                    "select table_name from information_schema.tables "
                    "where table_schema = :esquema"
                ),
                {"esquema": esquema_migrado},
            )
        }
    print(f"tabelas no esquema {esquema_migrado}: {sorted(existentes)}")
    assert set(TABELAS_DO_M3) <= existentes


def test_downgrade_do_m3_volta_ao_esquema_do_m2_sem_residuo(
    url_postgres, esquema_migrado
) -> None:
    """A reversibilidade é medida, não prometida: sobe, desce e conta o que sobrou."""
    ambiente = {
        "DATABASE_URL": url_postgres,
        "TOC_DB_SCHEMA": esquema_migrado,
        "PATH": __import__("os").environ["PATH"],
    }
    executado = subprocess.run(
        ["alembic", "downgrade", "0004"],
        cwd=RAIZ_DA_API,
        env={**__import__("os").environ, **ambiente},
        capture_output=True,
        text=True,
    )
    assert executado.returncode == 0, executado.stderr

    motor = persistencia_de(url_postgres, esquema_migrado).motor
    with motor.connect() as conexao:
        restantes = {
            linha[0]
            for linha in conexao.execute(
                text(
                    "select table_name from information_schema.tables "
                    "where table_schema = :esquema"
                ),
                {"esquema": esquema_migrado},
            )
        }
    print(f"depois do downgrade 0005→0004 sobraram: {sorted(restantes)}")
    assert set(TABELAS_DO_M3) & restantes == set()
    assert "ude" in restantes, "o downgrade do M3 não pode levar o M2 junto"


def test_a_nuvem_inteira_sobrevive_a_um_processo_novo(url_postgres, esquema_migrado) -> None:
    """Ida e volta sem perda: topologia, premissas com estado, injeções com TRIZ."""
    repositorio = persistencia_de(url_postgres, esquema_migrado).projetos
    nuvem = nuvem_preenchida()
    central = nuvem.registrar_premissa(
        ChaveDaAresta.D_D_PRIME, "não há orçamento para as duas ações", em=AGORA
    )
    outra = nuvem.registrar_premissa(
        ChaveDaAresta.D_D_PRIME, "as duas disputam a mesma equipe", em=AGORA
    )
    desafiada = nuvem.registrar_premissa(
        ChaveDaAresta.A_C, "reputação depende de credenciamento", em=AGORA
    )
    nuvem.desafiar_premissa(
        desafiada.id, justificativa="o credenciamento saiu em julho", em=AGORA
    )
    escolhida = nuvem.registrar_injecao(
        central.id,
        "faseamento orçamentário por marco de receita",
        separacao=SeparacaoTRIZ.TEMPO,
        em=AGORA,
    )
    nuvem.registrar_injecao(outra.id, "turno noturno na segunda cidade", em=AGORA)
    nuvem.mudar_status_de_injecao(escolhida.id, StatusDeInjecao.ESCOLHIDA, em=AGORA)
    repositorio.salvar_nuvem(nuvem)

    # Processo novo: outra fábrica, outra conexão, nenhum estado em memória.
    outro = persistencia_de(url_postgres, esquema_migrado).projetos
    lida = outro.obter_nuvem(DONO.inquilino_id, nuvem.projeto.id)

    print(
        f"lida do banco: {len(lida.entidades)} entidade(s), {len(lida.arestas)} aresta(s), "
        f"{len(lida.premissas())} premissa(s) viva(s), "
        f"completude={lida.validar().completude}"
    )
    assert (len(lida.entidades), len(lida.arestas)) == (5, 7)
    assert lida.texto(PapelDaEntidade.D_PRIME) == DILEMA[PapelDaEntidade.D_PRIME]
    assert lida.racional.startswith("A instituição")
    assert [p.texto for p in lida.premissas(ChaveDaAresta.D_D_PRIME)] == [
        central.texto,
        outra.texto,
    ]
    assert lida.premissa(desafiada.id).estado is EstadoDaPremissa.DESAFIADA
    assert lida.premissa(desafiada.id).justificativa == "o credenciamento saiu em julho"
    viva = lida.injecao(escolhida.id)
    assert viva.status is StatusDeInjecao.ESCOLHIDA
    assert viva.separacao is SeparacaoTRIZ.TEMPO
    assert viva.semeadura is not None and viva.semeadura.injecao_id == escolhida.id
    assert lida.leitura(ChaveDaAresta.D_D_PRIME) == nuvem.leitura(ChaveDaAresta.D_D_PRIME)
    # Reidratar NÃO é mutar: o agregado volta do banco sem evento pendente.
    assert lida.eventos == ()


def test_premissa_arquivada_e_injecoes_dela_continuam_no_banco(
    url_postgres, esquema_migrado
) -> None:
    """RF-15: arquivar não apaga — some da leitura viva, fica no dado."""
    repositorio = persistencia_de(url_postgres, esquema_migrado).projetos
    nuvem = nuvem_preenchida()
    premissa = nuvem.registrar_premissa(ChaveDaAresta.D_C, "turma nova improvisada", em=AGORA)
    nuvem.registrar_injecao(premissa.id, "formação prévia obrigatória", em=AGORA)
    arquivadas = nuvem.arquivar_premissa(premissa.id, em=AGORA)
    repositorio.salvar_nuvem(nuvem)

    lida = repositorio.obter_nuvem(DONO.inquilino_id, nuvem.projeto.id)
    motor = persistencia_de(url_postgres, esquema_migrado).motor
    with motor.connect() as conexao:
        linhas = conexao.execute(
            text(
                f'select count(*) from "{esquema_migrado}".nc_injecao where arquivada'
            )
        ).scalar_one()

    print(f"arquivadas junto: {arquivadas}; linhas arquivadas no banco: {linhas}")
    assert arquivadas == 1
    assert linhas == 1
    assert lida.premissas(ChaveDaAresta.D_C) == ()
    assert lida.premissa(premissa.id).arquivada


def test_o_isolamento_por_inquilino_vale_para_a_nuvem(url_postgres, esquema_migrado) -> None:
    repositorio = persistencia_de(url_postgres, esquema_migrado).projetos
    nuvem = nuvem_preenchida()
    repositorio.salvar_nuvem(nuvem)

    print(
        f"dono: {DONO.inquilino_id}; consultando como {OUTRO_DONO.inquilino_id}"
    )
    assert repositorio.obter_nuvem(DONO.inquilino_id, nuvem.projeto.id) is not None
    assert repositorio.obter_nuvem(OUTRO_DONO.inquilino_id, nuvem.projeto.id) is None


def test_a_costura_com_a_ara_atravessa_o_banco(url_postgres, esquema_migrado) -> None:
    """INT-05: a `ReferenciaDeOrigem` é gravada e volta tipada — não é texto colado."""
    repositorio = persistencia_de(url_postgres, esquema_migrado).projetos
    ara = novo_projeto_ara(id=uuid4(), dono=DONO, nome="Realidade atual", em=AGORA)
    udes = []
    for enunciado in UDES_SINTETICOS:
        no = ara.adicionar_efeito(titulo=enunciado, em=AGORA)
        ara.marcar_ude(no.id, em=AGORA)
        udes.append(no.id)
    repositorio.salvar_ara(ara)
    nuvem = derivar_nuvem_de_udes(
        ara, no_ids=tuple(udes), id=uuid4(), nome="Dilema da expansão", em=AGORA
    )
    repositorio.salvar_nuvem(nuvem)

    lida = repositorio.obter_nuvem(DONO.inquilino_id, nuvem.projeto.id)

    print(f"origem lida do banco: {lida.origem}; leitura: {lida.leitura_da_origem()}")
    assert lida.origem is not None
    assert lida.origem.ferramenta == "ara"
    assert lida.origem.projeto_id == ara.projeto.id
    assert lida.origem.nos == tuple(udes)
    # E a ARA de origem continua íntegra, com os dois UDEs marcados.
    ara_lida = repositorio.obter_ara(DONO.inquilino_id, ara.projeto.id)
    assert len(ara_lida.udes) == len(udes)


def test_o_banco_recusa_premissa_vazia_e_desafio_sem_justificativa(
    url_postgres, esquema_migrado
) -> None:
    """As invariantes do domínio, impostas TAMBÉM pelo banco."""
    persistencia = persistencia_de(url_postgres, esquema_migrado)
    nuvem = nuvem_preenchida()
    premissa = nuvem.registrar_premissa(ChaveDaAresta.A_B, "premissa legítima", em=AGORA)
    persistencia.projetos.salvar_nuvem(nuvem)
    aresta = nuvem.aresta(ChaveDaAresta.A_B).id

    recusas = []
    with persistencia.motor.begin() as conexao:
        conexao.execute(text(f'set search_path to "{esquema_migrado}"'))
    for descricao, comando, parametros in (
        (
            "premissa vazia",
            "insert into nc_premissa (id, projeto_id, aresta_id, texto, ordem, estado,"
            " justificativa, arquivada) values (:id, :projeto, :aresta, '', 9,"
            " 'vigente', '', false)",
            {"id": uuid4(), "projeto": nuvem.projeto.id, "aresta": aresta},
        ),
        (
            "desafiada sem justificativa",
            "insert into nc_premissa (id, projeto_id, aresta_id, texto, ordem, estado,"
            " justificativa, arquivada) values (:id, :projeto, :aresta, 'texto', 9,"
            " 'desafiada', '', false)",
            {"id": uuid4(), "projeto": nuvem.projeto.id, "aresta": aresta},
        ),
        (
            "estado fora do vocabulário",
            "insert into nc_premissa (id, projeto_id, aresta_id, texto, ordem, estado,"
            " justificativa, arquivada) values (:id, :projeto, :aresta, 'texto', 9,"
            " 'talvez', '', false)",
            {"id": uuid4(), "projeto": nuvem.projeto.id, "aresta": aresta},
        ),
        (
            "injeção sem premissa existente",
            "insert into nc_injecao (id, projeto_id, premissa_id, texto, status,"
            " arquivada) values (:id, :projeto, :premissa, 'injeção órfã', 'candidata',"
            " false)",
            {"id": uuid4(), "projeto": nuvem.projeto.id, "premissa": uuid4()},
        ),
        (
            "status de injeção fora da FSM",
            "insert into nc_injecao (id, projeto_id, premissa_id, texto, status,"
            " arquivada) values (:id, :projeto, :premissa, 'injeção', 'talvez', false)",
            {"id": uuid4(), "projeto": nuvem.projeto.id, "premissa": premissa.id},
        ),
        (
            "separação TRIZ fora do vocabulário",
            "insert into nc_injecao (id, projeto_id, premissa_id, texto, status,"
            " separacao, arquivada) values (:id, :projeto, :premissa, 'injeção',"
            " 'candidata', 'cor', false)",
            {"id": uuid4(), "projeto": nuvem.projeto.id, "premissa": premissa.id},
        ),
    ):
        with pytest.raises(IntegrityError):
            with persistencia.motor.begin() as conexao:
                conexao.execute(text(f'set search_path to "{esquema_migrado}"'))
                conexao.execute(text(comando), parametros)
        recusas.append(descricao)

    print(f"recusas do banco examinadas: {len(recusas)} → {recusas}")
    assert len(recusas) == 6
