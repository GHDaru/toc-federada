"""A jornada dos cinco passos contra o PostgreSQL REAL — nunca SQLite (brief §1).

Siglas, uma vez neste arquivo: **M6** — Focalização · **M4** — Árvores de Futuro e
Implementação · **TOC** — Teoria das Restrições · **ARA** — Árvore da Realidade Atual ·
**NC** — Nuvem de Conflito · **APR** — Árvore de Pré-Requisitos · **SQL** — *Structured
Query Language* · **RN/RF/RNF** — regra de negócio / requisito funcional / requisito não
funcional.

O que só um banco de verdade prova, e por isso está aqui e não na suíte de domínio:

- a **migração 0008** cria as nove tabelas do M6, e o `downgrade` as remove sem resíduo;
- a **ida e volta** não perde nada — ciclo fechado continua fechado com a restrição dele,
  decisões continuam na ordem, notas e reaberturas continuam ao lado, vínculos continuam
  tipados e a herança continua com o veredito que recebeu;
- o **isolamento por inquilino** vale para a análise como vale para o projeto (RNF-03);
- as invariantes do domínio estão **também** no banco: dois ciclos abertos não entram
  (RN-02), duas restrições no mesmo ciclo não entram (RN-03), um sexto passo não entra
  (RN-01), vínculo fora do canônico sem justificativa não entra (RN-06) e veredito sem
  justificativa não entra (RN-05). Invariante que só vive no código é invariante que a
  próxima ferramenta viola sem perceber.
"""
from __future__ import annotations

import os
import subprocess
from uuid import uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from toc_api.dominio.focalizacao import (
    EstadoDoCiclo,
    EstadoDoPasso,
    SistemaAnalisado,
    TipoDePasso,
    TipoDeRestricao,
    VereditoDeHeranca,
    nova_analise_de_focalizacao,
)
from toc_api.infra.configuracao import Configuracao
from toc_api.infra.persistencia.fabrica import criar_persistencia

from ..dominio.focalizacao_sintetica import (
    AGORA,
    AUTORA,
    CONFLITO_DE_SUBORDINACAO,
    DECISAO_DE_ELEVAR,
    DECISAO_DE_EXPLORAR,
    DECISAO_DE_SUBORDINAR,
    DESCRICAO_DO_SISTEMA,
    DONO,
    ID_DA_APR,
    ID_DA_ARA,
    ID_DA_NC,
    JUSTIFICATIVA_DA_RESTRICAO,
    NOME,
    OUTRO_DONO,
    RESTRICAO,
    SISTEMA,
    depois,
)
from .conftest import RAIZ_DA_API

pytestmark = pytest.mark.integracao

TABELAS_DO_M6 = (
    "foco_analise",
    "foco_ciclo",
    "foco_restricao",
    "foco_passo",
    "foco_decisao",
    "foco_nota",
    "foco_reabertura",
    "foco_vinculo",
    "foco_heranca",
)


def persistencia_de(url: str, esquema: str):
    return criar_persistencia(
        Configuracao.do_ambiente({"DATABASE_URL": url, "TOC_DB_SCHEMA": esquema})
    )


def analise_nova(dono=DONO, nome=NOME):
    return nova_analise_de_focalizacao(
        id=uuid4(),
        dono=dono,
        nome=nome,
        sistema=SistemaAnalisado(nome=SISTEMA, descricao=DESCRICAO_DO_SISTEMA),
        em=AGORA,
    )


def travessia(analise, *, base: int = 0, restricao: str = RESTRICAO) -> None:
    analise.registrar_restricao(
        descricao=restricao,
        tipo=TipoDeRestricao.FISICA,
        justificativa=JUSTIFICATIVA_DA_RESTRICAO,
        autor=AUTORA,
        em=depois(base + 5),
    )
    analise.concluir_passo(
        TipoDePasso.IDENTIFICAR, decisao=f"a restrição é {restricao}", autor=AUTORA,
        em=depois(base + 10),
    )
    analise.julgar_todas_as_herancas(
        veredito=VereditoDeHeranca.MANTIDA,
        justificativa="revisada e ainda válida",
        autor=AUTORA,
        em=depois(base + 12),
    )
    analise.concluir_passo(
        TipoDePasso.EXPLORAR, decisao=DECISAO_DE_EXPLORAR, autor=AUTORA, em=depois(base + 20)
    )
    analise.concluir_passo(
        TipoDePasso.SUBORDINAR, decisao=DECISAO_DE_SUBORDINAR, autor=AUTORA,
        em=depois(base + 30),
    )
    analise.concluir_passo(
        TipoDePasso.ELEVAR, decisao=DECISAO_DE_ELEVAR, autor=AUTORA, em=depois(base + 40)
    )


# ---------------------------------------------------------------------------------------
# A migração 0008
# ---------------------------------------------------------------------------------------


def test_a_migracao_cria_as_nove_tabelas_do_m6(url_postgres, esquema_migrado) -> None:
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
    assert set(TABELAS_DO_M6) <= existentes


def test_downgrade_do_m6_volta_ao_esquema_do_m4_sem_residuo(
    url_postgres, esquema_migrado
) -> None:
    """A reversibilidade é medida, não prometida: sobe, desce e conta o que sobrou."""
    executado = subprocess.run(
        ["alembic", "downgrade", "0007"],
        cwd=RAIZ_DA_API,
        env={**os.environ, "DATABASE_URL": url_postgres, "TOC_DB_SCHEMA": esquema_migrado},
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
    print(f"depois do downgrade 0008→0007 sobraram: {sorted(restantes)}")
    assert set(TABELAS_DO_M6) & restantes == set()
    assert "referencia_cruzada" in restantes, "o downgrade do M6 não pode levar o M4 junto"


# ---------------------------------------------------------------------------------------
# Ida e volta sem perda
# ---------------------------------------------------------------------------------------


def test_a_jornada_inteira_sobrevive_a_um_processo_novo(url_postgres, esquema_migrado) -> None:
    """Dois ciclos, restrição, decisões, notas, reaberturas, vínculos e herança julgada."""
    repositorio = persistencia_de(url_postgres, esquema_migrado).projetos

    analise = analise_nova()
    analise.vincular_ferramenta(
        TipoDePasso.IDENTIFICAR, tipo="ara", projeto_id=ID_DA_ARA, papel="causa raiz",
        em=depois(2),
    )
    analise.anotar_passo(
        TipoDePasso.IDENTIFICAR, texto="a fila cresce todo período", autor=AUTORA, em=depois(3)
    )
    travessia(analise)
    analise.reabrir_passo_anterior(
        justificativa="o plano de elevação mudou depois da reunião", autor=AUTORA,
        em=depois(45),
    )
    analise.concluir_passo(
        TipoDePasso.ELEVAR, decisao="contratar três pessoas", autor=AUTORA, em=depois(46)
    )
    analise.vincular_ferramenta(
        TipoDePasso.SUBORDINAR, tipo="nc", projeto_id=ID_DA_NC,
        papel=CONFLITO_DE_SUBORDINACAO[:60], em=depois(47),
    )
    analise.vincular_ferramenta(
        TipoDePasso.ELEVAR, tipo="apr", projeto_id=ID_DA_APR, em=depois(48)
    )
    analise.recomecar(em=depois(50))
    herdada = analise.ciclo_aberto.heranca[0]
    analise.julgar_heranca(
        herdada.id,
        veredito=VereditoDeHeranca.REVOGADA,
        justificativa="a restrição migrou de etapa",
        autor=AUTORA,
        em=depois(55),
    )
    repositorio.salvar_focalizacao(analise)
    retratos = [c.retrato() for c in analise.ciclos]

    # Um "processo novo": outro repositório sobre o mesmo esquema.
    outro = persistencia_de(url_postgres, esquema_migrado).projetos
    voltou = outro.obter_focalizacao(DONO.inquilino_id, analise.projeto.id)

    assert voltou is not None
    assert voltou.sistema == analise.sistema
    assert [c.retrato() for c in voltou.ciclos] == retratos
    fechado, aberto = voltou.ciclos
    assert fechado.estado is EstadoDoCiclo.FECHADO
    assert fechado.restricao.descricao == RESTRICAO
    assert fechado.restricao.tipo is TipoDeRestricao.FISICA
    assert [d.texto for d in fechado.passo(TipoDePasso.ELEVAR).decisoes] == [
        DECISAO_DE_ELEVAR,
        "contratar três pessoas",
    ]
    assert len(fechado.passo(TipoDePasso.ELEVAR).reaberturas) == 1
    assert len(fechado.passo(TipoDePasso.IDENTIFICAR).notas) == 1
    assert [v.tipo.value for v in fechado.passo(TipoDePasso.ELEVAR).vinculos] == ["apr"]
    assert aberto.estado is EstadoDoCiclo.ABERTO
    assert aberto.restricao is None
    assert aberto.decisao_herdada(herdada.id).veredito is VereditoDeHeranca.REVOGADA
    assert aberto.decisao_herdada(herdada.id).autor == AUTORA
    # A trava otimista veio junto: o agregado sabe de que versão partiu.
    assert voltou.projeto.versao_lida == voltou.projeto.versao


def test_gravar_duas_vezes_atualiza_e_nao_duplica(url_postgres, esquema_migrado) -> None:
    repositorio = persistencia_de(url_postgres, esquema_migrado).projetos
    analise = analise_nova()
    travessia(analise)
    repositorio.salvar_focalizacao(analise)
    analise.anotar_passo(
        TipoDePasso.RECOMECAR, texto="a restrição parece quebrada", autor=AUTORA, em=depois(45)
    )
    repositorio.salvar_focalizacao(analise)

    motor = persistencia_de(url_postgres, esquema_migrado).motor
    with motor.connect() as conexao:
        ciclos = conexao.execute(text("select count(*) from foco_ciclo")).scalar_one()
        passos = conexao.execute(text("select count(*) from foco_passo")).scalar_one()
        decisoes = conexao.execute(text("select count(*) from foco_decisao")).scalar_one()
        notas = conexao.execute(text("select count(*) from foco_nota")).scalar_one()
    print(f"ciclos={ciclos} passos={passos} decisoes={decisoes} notas={notas}")
    assert (ciclos, passos, decisoes, notas) == (1, 5, 4, 1)


def test_o_isolamento_por_inquilino_vale_para_a_analise(url_postgres, esquema_migrado) -> None:
    repositorio = persistencia_de(url_postgres, esquema_migrado).projetos
    analise = analise_nova()
    repositorio.salvar_focalizacao(analise)

    assert repositorio.obter_focalizacao(DONO.inquilino_id, analise.projeto.id) is not None
    assert repositorio.obter_focalizacao(OUTRO_DONO.inquilino_id, analise.projeto.id) is None


def test_projeto_que_nao_e_analise_devolve_nada_pela_porta_do_m6(
    url_postgres, esquema_migrado
) -> None:
    """Pedir pela porta errada não descobre nada — nem a existência do projeto."""
    from toc_api.dominio.nuvem import novo_projeto_nc

    repositorio = persistencia_de(url_postgres, esquema_migrado).projetos
    nuvem = novo_projeto_nc(id=uuid4(), dono=DONO, nome="Dilema qualquer", em=AGORA)
    repositorio.salvar_nuvem(nuvem)

    assert repositorio.obter_focalizacao(DONO.inquilino_id, nuvem.projeto.id) is None


def test_a_exclusao_suave_preserva_a_jornada_e_a_restauracao_a_devolve(
    url_postgres, esquema_migrado
) -> None:
    """RF-04: arquiva ciclos, passos, restrições e vínculos juntos; restaurar devolve tudo."""
    repositorio = persistencia_de(url_postgres, esquema_migrado).projetos
    analise = analise_nova()
    travessia(analise)
    repositorio.salvar_focalizacao(analise)
    antes = analise.ciclo_aberto.retrato()

    analise.excluir(em=depois(60))
    repositorio.salvar_focalizacao(analise)

    motor = persistencia_de(url_postgres, esquema_migrado).motor
    with motor.connect() as conexao:
        ciclos = conexao.execute(text("select count(*) from foco_ciclo")).scalar_one()
        decisoes = conexao.execute(text("select count(*) from foco_decisao")).scalar_one()
    print(f"depois da exclusão suave: ciclos={ciclos} decisoes={decisoes}")
    assert (ciclos, decisoes) == (1, 4), "exclusão suave não apaga a jornada"

    voltou = repositorio.obter_focalizacao(DONO.inquilino_id, analise.projeto.id)
    voltou.restaurar(em=depois(61))
    repositorio.salvar_focalizacao(voltou)
    assert voltou.ciclo_aberto.retrato() == antes


# ---------------------------------------------------------------------------------------
# As invariantes do domínio, impostas TAMBÉM pelo banco
# ---------------------------------------------------------------------------------------


def test_o_banco_recusa_dois_ciclos_abertos_na_mesma_analise(
    url_postgres, esquema_migrado
) -> None:
    """RN-02 pelo índice único parcial — a regra não depende só do código."""
    repositorio = persistencia_de(url_postgres, esquema_migrado).projetos
    analise = analise_nova()
    repositorio.salvar_focalizacao(analise)

    motor = persistencia_de(url_postgres, esquema_migrado).motor
    with pytest.raises(IntegrityError) as erro:
        with motor.begin() as conexao:
            conexao.execute(
                text(
                    "insert into foco_ciclo (id, projeto_id, ordem, estado, aberto_em)"
                    " values (:id, :projeto, 2, 'aberto', now())"
                ),
                {"id": uuid4(), "projeto": analise.projeto.id},
            )
    assert "uq_foco_ciclo_aberto_por_analise" in str(erro.value)


def test_o_banco_recusa_a_segunda_restricao_do_mesmo_ciclo(
    url_postgres, esquema_migrado
) -> None:
    """RN-03: `ciclo_id` é a chave primária de `foco_restricao`."""
    repositorio = persistencia_de(url_postgres, esquema_migrado).projetos
    analise = analise_nova()
    analise.registrar_restricao(
        descricao=RESTRICAO,
        tipo=TipoDeRestricao.FISICA,
        justificativa=JUSTIFICATIVA_DA_RESTRICAO,
        autor=AUTORA,
        em=depois(5),
    )
    repositorio.salvar_focalizacao(analise)

    motor = persistencia_de(url_postgres, esquema_migrado).motor
    with pytest.raises(IntegrityError) as erro:
        with motor.begin() as conexao:
            conexao.execute(
                text(
                    "insert into foco_restricao"
                    " (ciclo_id, id, projeto_id, descricao, tipo, justificativa, autor,"
                    "  registrada_em)"
                    " values (:ciclo, :id, :projeto, 'outra', 'politica', 'porque sim',"
                    "         'Gestora', now())"
                ),
                {
                    "ciclo": analise.ciclo_aberto.id,
                    "id": uuid4(),
                    "projeto": analise.projeto.id,
                },
            )
    assert "pk_foco_restricao" in str(erro.value)


def test_o_banco_recusa_um_sexto_passo_e_um_tipo_fora_do_vocabulario(
    url_postgres, esquema_migrado
) -> None:
    """RN-01: `tipo` é vocabulário fechado, e `(ciclo, tipo)` é a chave primária."""
    repositorio = persistencia_de(url_postgres, esquema_migrado).projetos
    analise = analise_nova()
    repositorio.salvar_focalizacao(analise)
    motor = persistencia_de(url_postgres, esquema_migrado).motor

    # um passo com nome fora do vocabulário — mesmo cabendo na ordem 1..5
    with pytest.raises(IntegrityError) as erro:
        with motor.begin() as conexao:
            conexao.execute(
                text(
                    "insert into foco_passo (ciclo_id, tipo, projeto_id, estado, ordem)"
                    " values (:ciclo, 'medir', :projeto, 'pendente', 3)"
                ),
                {"ciclo": analise.ciclo_aberto.id, "projeto": analise.projeto.id},
            )
    assert "tipo_do_passo" in str(erro.value)

    # e um SEXTO passo, com nome canônico repetido: a chave primária (ciclo, tipo) recusa
    with pytest.raises(IntegrityError) as erro:
        with motor.begin() as conexao:
            conexao.execute(
                text(
                    "insert into foco_passo (ciclo_id, tipo, projeto_id, estado, ordem)"
                    " values (:ciclo, 'elevar', :projeto, 'pendente', 5)"
                ),
                {"ciclo": analise.ciclo_aberto.id, "projeto": analise.projeto.id},
            )
    assert "pk_foco_passo" in str(erro.value)


def test_o_banco_recusa_vinculo_fora_do_canonico_sem_justificativa(
    url_postgres, esquema_migrado
) -> None:
    """RN-06 no banco: a justificativa não é convenção de borda."""
    repositorio = persistencia_de(url_postgres, esquema_migrado).projetos
    analise = analise_nova()
    repositorio.salvar_focalizacao(analise)
    motor = persistencia_de(url_postgres, esquema_migrado).motor

    with pytest.raises(IntegrityError) as erro:
        with motor.begin() as conexao:
            conexao.execute(
                text(
                    "insert into foco_vinculo"
                    " (id, ciclo_id, passo, projeto_id, ferramenta, alvo_projeto_id,"
                    "  canonico, justificativa)"
                    " values (:id, :ciclo, 'identificar', :projeto, 'apr', :alvo,"
                    "         false, '')"
                ),
                {
                    "id": uuid4(),
                    "ciclo": analise.ciclo_aberto.id,
                    "projeto": analise.projeto.id,
                    "alvo": ID_DA_APR,
                },
            )
    assert "nao_canonico_exige_justificativa" in str(erro.value)


def test_o_banco_recusa_veredito_sem_justificativa(url_postgres, esquema_migrado) -> None:
    """RN-05 no banco: manter é decisão tão explícita quanto revogar."""
    repositorio = persistencia_de(url_postgres, esquema_migrado).projetos
    analise = analise_nova()
    repositorio.salvar_focalizacao(analise)
    motor = persistencia_de(url_postgres, esquema_migrado).motor

    with pytest.raises(IntegrityError) as erro:
        with motor.begin() as conexao:
            conexao.execute(
                text(
                    "insert into foco_heranca"
                    " (id, ciclo_id, projeto_id, ciclo_de_origem, passo, texto, veredito)"
                    " values (:id, :ciclo, :projeto, 1, 'subordinar', 'uma regra antiga',"
                    "         'mantida')"
                ),
                {
                    "id": uuid4(),
                    "ciclo": analise.ciclo_aberto.id,
                    "projeto": analise.projeto.id,
                },
            )
    assert "veredito_exige_justificativa_e_autor" in str(erro.value)


def test_o_banco_recusa_restricao_de_tipo_fora_do_enum(url_postgres, esquema_migrado) -> None:
    """L-01: o enum fechado é do domínio E do banco; ampliar exige migração aditiva."""
    repositorio = persistencia_de(url_postgres, esquema_migrado).projetos
    analise = analise_nova()
    repositorio.salvar_focalizacao(analise)
    motor = persistencia_de(url_postgres, esquema_migrado).motor

    with pytest.raises(IntegrityError) as erro:
        with motor.begin() as conexao:
            conexao.execute(
                text(
                    "insert into foco_restricao"
                    " (ciclo_id, id, projeto_id, descricao, tipo, justificativa, autor,"
                    "  registrada_em)"
                    " values (:ciclo, :id, :projeto, 'x', 'de_pessoal', 'y', 'z', now())"
                ),
                {
                    "ciclo": analise.ciclo_aberto.id,
                    "id": uuid4(),
                    "projeto": analise.projeto.id,
                },
            )
    assert "tipo_da_restricao" in str(erro.value)


# ---------------------------------------------------------------------------------------
# A trava otimista sobre a jornada — o estado mais compartilhado da aplicação
# ---------------------------------------------------------------------------------------


def test_a_analise_tem_a_mesma_trava_que_o_m1(url_postgres, esquema_migrado) -> None:
    """Duas facilitadoras concluindo o mesmo passo: a segunda é recusada, não silenciada."""
    from toc_api.dominio.erros import ConflitoDeVersao

    repositorio = persistencia_de(url_postgres, esquema_migrado).projetos
    analise = analise_nova()
    analise.registrar_restricao(
        descricao=RESTRICAO,
        tipo=TipoDeRestricao.FISICA,
        justificativa=JUSTIFICATIVA_DA_RESTRICAO,
        autor=AUTORA,
        em=depois(5),
    )
    repositorio.salvar_focalizacao(analise)

    uma = repositorio.obter_focalizacao(DONO.inquilino_id, analise.projeto.id)
    outra = repositorio.obter_focalizacao(DONO.inquilino_id, analise.projeto.id)
    assert uma.projeto.versao_lida == outra.projeto.versao_lida

    uma.anotar_passo(
        TipoDePasso.IDENTIFICAR, texto="a fila cresce", autor=AUTORA, em=depois(6)
    )
    repositorio.salvar_focalizacao(uma)

    outra.concluir_passo(
        TipoDePasso.IDENTIFICAR, decisao="a restrição é a secretaria", autor=AUTORA,
        em=depois(7),
    )
    with pytest.raises(ConflitoDeVersao) as erro:
        repositorio.salvar_focalizacao(outra)
    assert erro.value.versao_lida < erro.value.versao_atual

    # E a nota da primeira continua lá: a recusa não deixou efeito parcial.
    depois_da_recusa = repositorio.obter_focalizacao(DONO.inquilino_id, analise.projeto.id)
    assert len(depois_da_recusa.ciclo_aberto.passo(TipoDePasso.IDENTIFICAR).notas) == 1
    assert (
        depois_da_recusa.ciclo_aberto.passo(TipoDePasso.IDENTIFICAR).estado
        is EstadoDoPasso.EM_ANDAMENTO
    )
