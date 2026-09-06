"""M4 contra o PostgreSQL REAL — migração, isolamento, cadeia e trava (spec 008).

Siglas, uma vez neste arquivo: **M4** — Árvores de Futuro e Implementação · **ARF** —
Árvore da Realidade Futura · **APR** — Árvore de Pré-Requisitos · **AT** — Árvore de
Transição · **ARA** — Árvore da Realidade Atual · **UDE** — Efeito Indesejável · **NC** —
Nuvem de Conflito · **OI** — Objetivo Intermediário · **SQL** — *Structured Query
Language* · **RF/RN/RNF** — requisito funcional / regra de negócio / requisito não
funcional da spec 008.

O que só aqui se prova (e nenhum duplo em memória alcança):

- a migração 0006 cria as **nove** tabelas do módulo, e o `downgrade` volta sem resíduo;
- a cadeia inteira **sobrevive a um processo novo**: um repositório recém-construído lê o
  que o outro gravou, com as referências e as duas costuras;
- as restrições do banco recusam o que o domínio recusa — RN-03 (um Efeito Desejável por
  UDE), RN-10 (a tripla do passo) e RF-30 (bloqueado exige motivo);
- a **trava otimista** da `ReferenciaCruzada`, que é agregado próprio e por isso tem versão
  própria: duas escritas da mesma versão, e a segunda é recusada com os dois números.

Base sintética (ADR 0006): "Instituição Horizonte", personas fictícias.
"""
from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

import pytest
from sqlalchemy import text

from toc_api.dominio.apr import PapelNaAPR
from toc_api.dominio.ara import (
    OrigemDoParecer,
    ParecerDeJulgamento,
    StatusDeValidacao,
    novo_projeto_ara,
)
from toc_api.dominio.arf import EstadoDoRamo, PapelNaARF
from toc_api.dominio.at import StatusDoPasso, novo_projeto_at
from toc_api.dominio.encadeamento import (
    derivar_apr_de_arf,
    derivar_at_de_oi,
    promover_udes_para_nc,
    semear_arf_de_injecao,
)
from toc_api.dominio.erros import ConflitoDeVersao
from toc_api.dominio.identidade import DonoDoProjeto
from toc_api.dominio.nuvem import ChaveDaAresta, StatusDeInjecao
from toc_api.dominio.referencia import EstadoDaReferencia, travessia
from toc_api.dominio.suficiencia import EstadoDoExame
from toc_api.infra.configuracao import Configuracao
from toc_api.infra.persistencia.fabrica import criar_persistencia

pytestmark = pytest.mark.integracao

AGORA = datetime(2026, 9, 6, 10, 0, tzinfo=timezone.utc)
DONO = DonoDoProjeto(inquilino_id="instituicao-horizonte", usuario_id="u-facilitadora")
OUTRO = DonoDoProjeto(inquilino_id="instituicao-aurora", usuario_id="u-aurora")

UDES = (
    "A taxa de evasão no primeiro semestre é de 22%.",
    "O caixa da instituição fecha o trimestre negativo.",
)
INJECAO = "faseamento orçamentário condicionado a marco de receita"
EFEITO = "as duas frentes recebem verba no trimestre"

TABELAS_DO_M4 = (
    "arf_arvore",
    "arf_espelho",
    "arf_ramo_negativo",
    "apr_arvore",
    "apr_par",
    "apr_julgamento",
    "apr_elipse",
    "apr_elipse_dependencia",
    "at_arvore",
    "at_passo",
    "referencia_cruzada",
)


def repositorio(url: str, esquema: str):
    return criar_persistencia(
        Configuracao.do_ambiente({"DATABASE_URL": url, "TOC_DB_SCHEMA": esquema})
    ).projetos


@pytest.fixture()
def repo(url_postgres, esquema_migrado):
    return repositorio(url_postgres, esquema_migrado)


def ara_validada(dono=DONO):
    ara = novo_projeto_ara(id=uuid4(), dono=dono, nome="Realidade atual", em=AGORA)
    ids = []
    for enunciado in UDES:
        no = ara.adicionar_efeito(titulo=enunciado, em=AGORA)
        ara.marcar_ude(no.id, em=AGORA)
        ara.registrar_parecer(
            no.id,
            ParecerDeJulgamento(
                autor="papel:facilitadora",
                origem=OrigemDoParecer.HUMANO,
                favoravel=True,
                justificativa="a queixa é contínua e está na esfera da coordenação",
                instante=AGORA,
            ),
            em=AGORA,
        )
        ara.mudar_status(no.id, StatusDeValidacao.VALIDADO, em=AGORA)
        ids.append(no.id)
    return ara, tuple(ids)


# --------------------------------------------------------------------------------------
# A migração
# --------------------------------------------------------------------------------------


def test_a_migracao_cria_as_onze_tabelas_do_m4(url_postgres, esquema_migrado):
    motor = criar_persistencia(
        Configuracao.do_ambiente(
            {"DATABASE_URL": url_postgres, "TOC_DB_SCHEMA": esquema_migrado}
        )
    ).motor
    with motor.connect() as conexao:
        nomes = {
            linha[0]
            for linha in conexao.execute(
                text(
                    "select table_name from information_schema.tables"
                    " where table_schema = :esquema"
                ),
                {"esquema": esquema_migrado},
            )
        }
    faltando = set(TABELAS_DO_M4) - nomes
    print(f"tabelas no esquema {esquema_migrado}: {len(nomes)} · do M4 faltando: {faltando}")
    assert faltando == set()


def test_downgrade_do_m4_volta_ao_esquema_do_m3_sem_residuo(url_postgres, esquema_migrado):
    import os
    import subprocess
    from pathlib import Path

    raiz = Path(__file__).resolve().parents[2]
    ambiente = {**os.environ, "DATABASE_URL": url_postgres, "TOC_DB_SCHEMA": esquema_migrado}
    executado = subprocess.run(
        ["alembic", "downgrade", "0005"],
        cwd=raiz,
        env=ambiente,
        capture_output=True,
        text=True,
    )
    assert executado.returncode == 0, executado.stderr

    motor = criar_persistencia(
        Configuracao.do_ambiente(
            {"DATABASE_URL": url_postgres, "TOC_DB_SCHEMA": esquema_migrado}
        )
    ).motor
    with motor.connect() as conexao:
        restantes = {
            linha[0]
            for linha in conexao.execute(
                text(
                    "select table_name from information_schema.tables"
                    " where table_schema = :esquema"
                ),
                {"esquema": esquema_migrado},
            )
        }
    sobrando = restantes & set(TABELAS_DO_M4)
    print(f"tabelas do M4 depois do downgrade: {sobrando or 'nenhuma'}")
    assert sobrando == set()
    # E o esquema do M3 continua de pé — o downgrade voltou um degrau, não derrubou tudo.
    assert {"nc_nuvem", "nc_premissa", "nc_injecao", "projeto"} <= restantes


# --------------------------------------------------------------------------------------
# A cadeia inteira atravessa o banco
# --------------------------------------------------------------------------------------


def test_a_cadeia_inteira_sobrevive_a_um_processo_novo(url_postgres, esquema_migrado):
    """A aptidão do round 008 contra o banco de verdade — do UDE ao passo concluído."""
    escrita = repositorio(url_postgres, esquema_migrado)

    ara, udes = ara_validada()
    escrita.salvar_ara(ara)

    promocao = promover_udes_para_nc(
        ara, no_ids=udes, id=uuid4(), nome="Dilema da expansão", em=AGORA
    )
    nuvem = promocao.nuvem
    premissa = nuvem.registrar_premissa(
        ChaveDaAresta.D_D_PRIME, "o orçamento é indivisível no exercício", em=AGORA
    )
    injecao = nuvem.registrar_injecao(premissa.id, INJECAO, em=AGORA)
    nuvem.mudar_status_de_injecao(injecao.id, StatusDeInjecao.ESCOLHIDA, em=AGORA)
    escrita.salvar_nuvem(nuvem)
    escrita.salvar_referencia(promocao.referencia)

    semeadura = semear_arf_de_injecao(
        nuvem, injecao_id=injecao.id, id=uuid4(), nome="Futuro da expansão", em=AGORA
    )
    arf = semeadura.arf
    semente = arf.injecoes[0]
    efeito = arf.adicionar_efeito_futuro(titulo=EFEITO, em=AGORA)
    elo = arf.ligar(semente.id, efeito.id, em=AGORA)
    arf.examinar_elo(elo.id, EstadoDoExame.COM_RESERVA, reserva="depende do marco", em=AGORA)
    arf.espelhar_ude(efeito.id, udes[0], em=AGORA)
    colateral = arf.adicionar_efeito_futuro(titulo="a Secretaria acumula jornada", em=AGORA)
    corte = arf.adicionar_injecao(titulo="contratação temporária no pico", em=AGORA)
    ramo = arf.marcar_ramo_negativo(colateral.id, em=AGORA)
    arf.tratar_ramo(ramo.id, injecao_id=corte.id, em=AGORA)
    escrita.salvar_arf(arf)
    escrita.salvar_nuvem(nuvem)
    escrita.salvar_referencia(semeadura.referencia)

    derivacao_apr = derivar_apr_de_arf(
        arf, no_id=efeito.id, id=uuid4(), nome="Implantação", em=AGORA
    )
    apr = derivacao_apr.apr
    obstaculo = apr.adicionar_obstaculo(titulo="Há apenas uma pessoa treinada", em=AGORA)
    oi = apr.adicionar_objetivo_intermediario(
        titulo="Existem três pessoas treinadas e escaladas", em=AGORA
    )
    par = apr.parear(obstaculo.id, oi.id, em=AGORA)
    apr.julgar_par(
        par.id,
        autor="Facilitadora TOC",
        valido=True,
        justificativa="com três pessoas o acompanhamento não depende de uma só",
        em=AGORA,
    )
    outro_oi = apr.adicionar_objetivo_intermediario(titulo="A escala está publicada", em=AGORA)
    d1 = apr.depender(oi.id, apr.objetivo.id, em=AGORA)
    d2 = apr.depender(outro_oi.id, apr.objetivo.id, em=AGORA)
    elipse = apr.formar_elipse((d1.id, d2.id), em=AGORA)
    escrita.salvar_apr(apr)
    escrita.salvar_arf(arf)
    escrita.salvar_referencia(derivacao_apr.referencia)

    derivacao_at = derivar_at_de_oi(apr, no_id=oi.id, id=uuid4(), nome="Transição", em=AGORA)
    at = derivacao_at.at
    passo = at.registrar_passo(
        acao="publicar a chamada interna de treinamento",
        necessidade="não há hoje candidato mapeado",
        resultado_esperado="lista de inscritos até sexta",
        em=AGORA,
    )
    at.mudar_status(
        passo.id, StatusDoPasso.CONCLUIDO, resultado_real="duas inscritas até sexta", em=AGORA
    )
    escrita.salvar_at(at)
    escrita.salvar_apr(apr)
    escrita.salvar_referencia(derivacao_at.referencia)

    # -- processo novo: outro repositório, outra sessão, o mesmo banco -----------------
    leitura = repositorio(url_postgres, esquema_migrado)

    arf_lida = leitura.obter_arf(DONO.inquilino_id, arf.projeto.id)
    apr_lida = leitura.obter_apr(DONO.inquilino_id, apr.projeto.id)
    at_lida = leitura.obter_at(DONO.inquilino_id, at.projeto.id)
    nuvem_lida = leitura.obter_nuvem(DONO.inquilino_id, nuvem.projeto.id)
    referencias = leitura.listar_referencias(DONO.inquilino_id)
    cadeia = travessia(tuple(referencias), projeto_id=arf.projeto.id)

    print(
        f"de volta do banco: ARF({len(arf_lida.nos)} nós, {len(arf_lida.ramos())} ramo(s), "
        f"exame={arf_lida.exame(elo.id).estado.value}) · "
        f"APR({len(apr_lida.pares())} par(es), {len(apr_lida.elipses())} elipse(s)) · "
        f"AT({at_lida.resumo_de_execucao()}) · "
        f"cadeia={' → '.join(cadeia.ferramentas())}"
    )
    assert arf_lida.udes_da_cadeia == udes
    assert arf_lida.e_efeito_desejavel(efeito.id)
    assert arf_lida.ramos()[0].estado is EstadoDoRamo.TRATADO
    assert arf_lida.ramos()[0].injecao_de_corte_id == corte.id
    assert arf_lida.exame(elo.id).reserva == "depende do marco"
    assert arf_lida.origem.elementos == (injecao.id,)

    assert apr_lida.objetivo.titulo == apr.objetivo.titulo
    assert apr_lida.pares()[0].julgamentos[0].autor == "Facilitadora TOC"
    assert apr_lida.elipses()[0].id == elipse.id
    assert set(apr_lida.elipses()[0].dependencias) == {d1.id, d2.id}
    assert apr_lida.sequenciar().completo is False  # `outro_oi` ainda não tem obstáculo

    assert at_lida.alvo.elementos == (oi.id,)
    assert at_lida.ficha(passo.id).resultado_real == "duas inscritas até sexta"
    assert at_lida.ficha(passo.id).divergente is True

    # INT-03/INT-06: a costura do lado da nuvem voltou preenchida.
    assert nuvem_lida.injecao(injecao.id).semeadura.projeto_destino_id == arf.projeto.id
    assert len(referencias) == 4
    assert cadeia.ferramentas() == ("ara", "nc", "arf", "apr", "at")


def test_o_isolamento_por_inquilino_vale_para_as_tres_arvores_e_a_referencia(repo):
    ara, udes = ara_validada()
    repo.salvar_ara(ara)
    promocao = promover_udes_para_nc(ara, no_ids=udes, id=uuid4(), nome="Dilema", em=AGORA)
    repo.salvar_nuvem(promocao.nuvem)
    repo.salvar_referencia(promocao.referencia)
    at = novo_projeto_at(id=uuid4(), dono=DONO, nome="Transição", em=AGORA)
    repo.salvar_at(at)

    print(
        f"do outro inquilino: at={repo.obter_at(OUTRO.inquilino_id, at.projeto.id)} · "
        f"referencias={repo.listar_referencias(OUTRO.inquilino_id)}"
    )
    assert repo.obter_at(OUTRO.inquilino_id, at.projeto.id) is None
    assert repo.obter_arf(OUTRO.inquilino_id, at.projeto.id) is None
    assert repo.listar_referencias(OUTRO.inquilino_id) == []
    assert repo.obter_referencia(OUTRO.inquilino_id, promocao.referencia.id) is None


def test_projeto_que_nao_e_da_ferramenta_nao_volta_como_se_fosse(repo):
    at = novo_projeto_at(id=uuid4(), dono=DONO, nome="Transição", em=AGORA)
    repo.salvar_at(at)
    assert repo.obter_arf(DONO.inquilino_id, at.projeto.id) is None
    assert repo.obter_apr(DONO.inquilino_id, at.projeto.id) is None


# --------------------------------------------------------------------------------------
# As restrições do banco recusam o que o domínio recusa
# --------------------------------------------------------------------------------------


def test_o_banco_recusa_dois_efeitos_desejaveis_para_o_mesmo_ude(
    url_postgres, esquema_migrado
):
    """RN-03 imposta PELO BANCO — invariante que só vive no código a próxima ferramenta viola."""
    from sqlalchemy import create_engine

    motor = create_engine(
        url_postgres, connect_args={"options": f"-csearch_path={esquema_migrado}"}
    )
    repo = repositorio(url_postgres, esquema_migrado)
    ara, udes = ara_validada()
    repo.salvar_ara(ara)
    promocao = promover_udes_para_nc(ara, no_ids=udes, id=uuid4(), nome="Dilema", em=AGORA)
    nuvem = promocao.nuvem
    premissa = nuvem.registrar_premissa(ChaveDaAresta.D_D_PRIME, "premissa", em=AGORA)
    injecao = nuvem.registrar_injecao(premissa.id, INJECAO, em=AGORA)
    nuvem.mudar_status_de_injecao(injecao.id, StatusDeInjecao.ESCOLHIDA, em=AGORA)
    repo.salvar_nuvem(nuvem)
    arf = semear_arf_de_injecao(
        nuvem, injecao_id=injecao.id, id=uuid4(), nome="Futuro", em=AGORA
    ).arf
    um = arf.adicionar_efeito_futuro(titulo=EFEITO, em=AGORA)
    outro = arf.adicionar_efeito_futuro(titulo="a fila anda em dois dias", em=AGORA)
    arf.espelhar_ude(um.id, udes[0], em=AGORA)
    repo.salvar_arf(arf)

    with motor.begin() as conexao, pytest.raises(Exception) as erro:
        conexao.execute(
            text(
                "insert into arf_espelho (no_id, projeto_id, ude_id)"
                " values (:no, :projeto, :ude)"
            ),
            {"no": outro.id, "projeto": arf.projeto.id, "ude": udes[0]},
        )
    print(f"o banco recusou: {type(erro.value).__name__}")
    assert "uq_espelho_por_ude" in str(erro.value)


def test_o_banco_recusa_passo_sem_a_tripla_e_bloqueio_sem_motivo(
    url_postgres, esquema_migrado
):
    """RN-10 e RF-30 impostas pelo banco."""
    from sqlalchemy import create_engine

    motor = create_engine(
        url_postgres, connect_args={"options": f"-csearch_path={esquema_migrado}"}
    )
    repo = repositorio(url_postgres, esquema_migrado)
    at = novo_projeto_at(id=uuid4(), dono=DONO, nome="Transição", em=AGORA)
    passo = at.registrar_passo(
        acao="publicar a chamada", necessidade="não há candidato", resultado_esperado="lista", em=AGORA
    )
    repo.salvar_at(at)

    with motor.begin() as conexao, pytest.raises(Exception) as sem_tripla:
        conexao.execute(
            text("update at_passo set necessidade = '   ' where no_id = :no"),
            {"no": passo.id},
        )
    with motor.begin() as conexao, pytest.raises(Exception) as sem_motivo:
        conexao.execute(
            text("update at_passo set status = 'bloqueado' where no_id = :no"),
            {"no": passo.id},
        )
    print(
        f"recusas do banco: {'tripla_do_passo_obrigatoria' in str(sem_tripla.value)} · "
        f"{'bloqueado_exige_motivo' in str(sem_motivo.value)}"
    )
    assert "tripla_do_passo_obrigatoria" in str(sem_tripla.value)
    assert "bloqueado_exige_motivo" in str(sem_motivo.value)


# --------------------------------------------------------------------------------------
# A trava otimista do agregado NOVO
# --------------------------------------------------------------------------------------


def test_a_referencia_cruzada_tem_trava_propria_e_a_segunda_escrita_e_recusada(repo):
    """A referência é agregado próprio, e por isso a versão é dela — não do projeto."""
    ara, udes = ara_validada()
    repo.salvar_ara(ara)
    promocao = promover_udes_para_nc(ara, no_ids=udes, id=uuid4(), nome="Dilema", em=AGORA)
    repo.salvar_nuvem(promocao.nuvem)
    repo.salvar_referencia(promocao.referencia)

    uma = repo.listar_referencias(DONO.inquilino_id)[0]
    outra = repo.listar_referencias(DONO.inquilino_id)[0]
    assert uma.versao_lida == outra.versao_lida == 1

    uma.suspender(motivo="projeto excluído pela facilitadora", em=AGORA)
    repo.salvar_referencia(uma)

    outra.suspender(motivo="projeto excluído por outra pessoa", em=AGORA)
    with pytest.raises(ConflitoDeVersao) as erro:
        repo.salvar_referencia(outra)

    print(
        f"perdeu a corrida: versao_lida={erro.value.versao_lida} "
        f"versao_atual={erro.value.versao_atual}"
    )
    assert (erro.value.versao_lida, erro.value.versao_atual) == (1, 2)
    guardada = repo.listar_referencias(DONO.inquilino_id)[0]
    assert guardada.estado is EstadoDaReferencia.PENDENTE
    assert guardada.motivo == "projeto excluído pela facilitadora"


def test_a_referencia_suspensa_e_reativada_atravessa_o_banco_sem_sumir(repo):
    ara, udes = ara_validada()
    repo.salvar_ara(ara)
    promocao = promover_udes_para_nc(ara, no_ids=udes, id=uuid4(), nome="Dilema", em=AGORA)
    repo.salvar_nuvem(promocao.nuvem)
    repo.salvar_referencia(promocao.referencia)

    referencia = repo.listar_referencias(DONO.inquilino_id)[0]
    referencia.suspender(motivo="projeto excluído", em=AGORA)
    repo.salvar_referencia(referencia)
    de_volta = repo.listar_referencias(DONO.inquilino_id)[0]
    de_volta.reativar(em=AGORA)
    repo.salvar_referencia(de_volta)

    final = repo.listar_referencias(DONO.inquilino_id)
    print(f"referências no banco: {len(final)} · estado={final[0].estado.value}")
    assert len(final) == 1
    assert final[0].estado is EstadoDaReferencia.ATIVA
    assert final[0].motivo == ""


def test_a_arf_grava_pela_mesma_trava_dos_outros_modulos(repo):
    """A trava é a classe inteira: o M4 grava pelo MESMO `_gravar_projeto`."""
    ara, udes = ara_validada()
    repo.salvar_ara(ara)
    promocao = promover_udes_para_nc(ara, no_ids=udes, id=uuid4(), nome="Dilema", em=AGORA)
    nuvem = promocao.nuvem
    premissa = nuvem.registrar_premissa(ChaveDaAresta.D_D_PRIME, "premissa", em=AGORA)
    injecao = nuvem.registrar_injecao(premissa.id, INJECAO, em=AGORA)
    nuvem.mudar_status_de_injecao(injecao.id, StatusDeInjecao.ESCOLHIDA, em=AGORA)
    repo.salvar_nuvem(nuvem)
    arf = semear_arf_de_injecao(
        nuvem, injecao_id=injecao.id, id=uuid4(), nome="Futuro", em=AGORA
    ).arf
    repo.salvar_arf(arf)

    uma = repo.obter_arf(DONO.inquilino_id, arf.projeto.id)
    outra = repo.obter_arf(DONO.inquilino_id, arf.projeto.id)
    uma.adicionar_efeito_futuro(titulo=EFEITO, em=AGORA)
    repo.salvar_arf(uma)
    outra.adicionar_efeito_futuro(titulo="a fila anda em dois dias", em=AGORA)

    with pytest.raises(ConflitoDeVersao) as erro:
        repo.salvar_arf(outra)

    print(f"ARF: versao_lida={erro.value.versao_lida} versao_atual={erro.value.versao_atual}")
    assert erro.value.versao_lida < erro.value.versao_atual
    # E o nó da primeira continua lá: a segunda escrita não passou por cima.
    assert len(repo.obter_arf(DONO.inquilino_id, arf.projeto.id).nos) == 2
