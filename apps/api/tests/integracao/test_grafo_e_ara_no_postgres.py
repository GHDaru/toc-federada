"""O grafo do M1 e a Árvore da Realidade Atual (ARA, M2) contra o PostgreSQL REAL.

Nunca SQLite (brief §1): um teste de integração que cai num banco diferente do de
produção não integrou nada. Cada teste roda num esquema descartável, migrado por
`alembic upgrade head` de verdade (ver `conftest.py`).

O que só este arquivo consegue provar, e os duplos não:

- que o agregado **volta do banco igual** — nós, posições, arestas, ficha, status,
  pareceres, exame de elo e conector E;
- que a reconciliação não destrói dado alheio: excluir um nó leva as arestas dele e o
  exame delas, e **não** toca o exame do elo vizinho;
- que o **isolamento por inquilino** vale na consulta, não na disciplina de quem chama
  (RNF-03) — inclusive na porta do M2;
- que as invariantes RN-02, RN-03, RF-22 e RN-11 estão impostas **pelo banco** além do
  domínio: invariante que só vive no código é invariante que a próxima ferramenta viola.

Base sintética (ADR 0006): Instituição Horizonte, papéis, nenhum nome de pessoa.
"""
from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from toc_api.aplicacao.ara import (
    AdicionarEfeito,
    AnalisarArvore,
    CriarProjetoARA,
    ExaminarElo,
    ExcluirNoDaARA,
    FormarConectorE,
    LigarNaARA,
    MarcarUde,
    MoverNoDaARA,
    MudarStatusDeUde,
    RegistrarParecer,
    ReformularUde,
)
from toc_api.aplicacao.grafo import AdicionarNo, LigarNos, MoverNo
from toc_api.aplicacao.projetos import CriarProjeto
from toc_api.dominio.ara import (
    EstadoDoExame,
    FichaDeUde,
    OrigemDoParecer,
    ParecerDeJulgamento,
    StatusDeValidacao,
)
from toc_api.dominio.erros import NaoEncontrado
from toc_api.dominio.identidade import DonoDoProjeto
from toc_api.dominio.valores import PosicaoNoCanvas
from toc_api.infra.configuracao import Configuracao
from toc_api.infra.observabilidade.otel import RastreadorNulo
from toc_api.infra.persistencia.fabrica import criar_persistencia
from toc_api.infra.relogio import RelogioDoSistema

pytestmark = pytest.mark.integracao

HORIZONTE = DonoDoProjeto(inquilino_id="inq-horizonte", usuario_id="usr-facilitadora")
ALVORADA = DonoDoProjeto(inquilino_id="inq-alvorada", usuario_id="usr-consultor")

BOM = "A taxa de conclusão dos cursos técnicos é de 54%."
RUIM = "Falta um sistema integrado de matrícula na secretaria."


@pytest.fixture()
def pecas(url_postgres, esquema_migrado):
    persistencia = criar_persistencia(
        Configuracao.do_ambiente(
            {"DATABASE_URL": url_postgres, "TOC_DB_SCHEMA": esquema_migrado}
        )
    )
    return dict(
        rastreador=RastreadorNulo(),
        repositorio=persistencia.projetos,
        relogio=RelogioDoSistema(),
    )


# -- M1 · o grafo vai e volta ------------------------------------------------------------


def test_o_grafo_do_m1_volta_do_banco_identico(pecas):
    """M1 puro, sobre projeto GENÉRICO — onde o `Projeto` é a própria raiz do agregado."""
    projeto = CriarProjeto(**pecas).rodar(dono=HORIZONTE, nome="Horizonte — diagrama")
    a = AdicionarNo(**pecas).rodar(
        dono=HORIZONTE, projeto_id=projeto.id,
        titulo="Os formulários chegam incompletos.",
        descricao="observado na fila do balcão",
        posicao=PosicaoNoCanvas(120.5, -40.25),
    )
    b = AdicionarNo(**pecas).rodar(dono=HORIZONTE, projeto_id=projeto.id, titulo=BOM)
    elo = LigarNos(**pecas).rodar(
        dono=HORIZONTE, projeto_id=projeto.id, origem_id=a.id, destino_id=b.id,
        rotulo="se A, então B",
    )

    reaberto = pecas["repositorio"].obter(HORIZONTE.inquilino_id, projeto.id)

    assert {n.id for n in reaberto.nos} == {a.id, b.id}
    assert reaberto.no(a.id).posicao == PosicaoNoCanvas(120.5, -40.25)
    assert reaberto.no(a.id).descricao == "observado na fila do balcão"
    assert reaberto.aresta(elo.id).rotulo == "se A, então B"
    assert reaberto.eventos == ()  # carregar não é mutar


def test_mover_no_persiste_a_posicao_final(pecas):
    projeto = CriarProjeto(**pecas).rodar(dono=HORIZONTE, nome="Horizonte — diagrama")
    no = AdicionarNo(**pecas).rodar(dono=HORIZONTE, projeto_id=projeto.id, titulo=BOM)
    MoverNo(**pecas).rodar(
        dono=HORIZONTE, projeto_id=projeto.id, no_id=no.id,
        posicao=PosicaoNoCanvas(7.125, 9.5),
    )
    reaberto = pecas["repositorio"].obter(HORIZONTE.inquilino_id, projeto.id)
    assert reaberto.no(no.id).posicao == PosicaoNoCanvas(7.125, 9.5)


def test_excluir_no_leva_so_as_arestas_dele_e_preserva_o_exame_vizinho(pecas):
    """A prova de que a reconciliação não é um apaga-tudo disfarçado.

    É também o teste que teria pego o filtro invertido da linhagem
    (`tocbuilderv3/services/mockApiService.ts:521`), agora no banco.
    """
    projeto = CriarProjetoARA(**pecas).rodar(dono=HORIZONTE, nome="Horizonte — ARA")
    adicionar, ligar = AdicionarEfeito(**pecas), LigarNaARA(**pecas)
    a = adicionar.rodar(dono=HORIZONTE, projeto_id=projeto.id, titulo="Nó A qualquer.")
    m = adicionar.rodar(dono=HORIZONTE, projeto_id=projeto.id, titulo="Nó do meio.")
    z = adicionar.rodar(dono=HORIZONTE, projeto_id=projeto.id, titulo="Nó Z qualquer.")
    ligar.rodar(dono=HORIZONTE, projeto_id=projeto.id, origem_id=a.id, destino_id=m.id)
    ligar.rodar(dono=HORIZONTE, projeto_id=projeto.id, origem_id=m.id, destino_id=z.id)
    sobrevivente = ligar.rodar(
        dono=HORIZONTE, projeto_id=projeto.id, origem_id=a.id, destino_id=z.id
    )
    ExaminarElo(**pecas).rodar(
        dono=HORIZONTE, projeto_id=projeto.id, aresta_id=sobrevivente.id,
        estado=EstadoDoExame.SUFICIENTE,
    )

    removidas = ExcluirNoDaARA(**pecas).rodar(
        dono=HORIZONTE, projeto_id=projeto.id, no_id=m.id
    )

    assert len(removidas) == 2
    reaberta = pecas["repositorio"].obter_ara(HORIZONTE.inquilino_id, projeto.id)
    assert {n.id for n in reaberta.nos} == {a.id, z.id}
    assert [x.id for x in reaberta.arestas] == [sobrevivente.id]
    assert reaberta.exame(sobrevivente.id).estado is EstadoDoExame.SUFICIENTE


# -- M2 · a ARA inteira vai e volta -------------------------------------------------------


def test_a_ara_completa_volta_do_banco_com_ficha_status_parecer_exame_e_conector(pecas):
    projeto = CriarProjetoARA(**pecas).rodar(
        dono=HORIZONTE, nome="Horizonte — ARA da evasão"
    )
    adicionar, ligar = AdicionarEfeito(**pecas), LigarNaARA(**pecas)
    c1 = adicionar.rodar(
        dono=HORIZONTE, projeto_id=projeto.id, titulo="Os formulários chegam incompletos."
    )
    c2 = adicionar.rodar(
        dono=HORIZONTE, projeto_id=projeto.id, titulo="O volume de pedidos dobra em janeiro."
    )
    ude = adicionar.rodar(dono=HORIZONTE, projeto_id=projeto.id, titulo=BOM)
    e1 = ligar.rodar(dono=HORIZONTE, projeto_id=projeto.id, origem_id=c1.id, destino_id=ude.id)
    e2 = ligar.rodar(dono=HORIZONTE, projeto_id=projeto.id, origem_id=c2.id, destino_id=ude.id)

    MarcarUde(**pecas).rodar(
        dono=HORIZONTE, projeto_id=projeto.id, no_id=ude.id,
        ficha=FichaDeUde(
            area_impactada="Secretaria",
            objetivo_afetado="formar técnicos no prazo",
            evidencias=("relatório interno de conclusão", "painel da coordenação"),
            frequencia="todo semestre",
            impactos_estimados="46% dos matriculados não concluem",
        ),
    )
    RegistrarParecer(**pecas).rodar(
        dono=HORIZONTE, projeto_id=projeto.id, no_id=ude.id,
        parecer=ParecerDeJulgamento(
            autor="acao:toc.validate_ude",
            origem=OrigemDoParecer.CATALOGO,
            favoravel=True,
            justificativa="parece contínuo",
            instante=datetime(2026, 9, 5, 10, 0, tzinfo=timezone.utc),
            proposta_id="prop-001",
        ),
    )
    RegistrarParecer(**pecas).rodar(
        dono=HORIZONTE, projeto_id=projeto.id, no_id=ude.id,
        parecer=ParecerDeJulgamento(
            autor="papel:facilitadora",
            origem=OrigemDoParecer.HUMANO,
            favoravel=True,
            justificativa="queixa contínua e dentro da esfera da coordenação",
            instante=datetime(2026, 9, 5, 11, 0, tzinfo=timezone.utc),
        ),
    )
    MudarStatusDeUde(**pecas).rodar(
        dono=HORIZONTE, projeto_id=projeto.id, no_id=ude.id,
        status=StatusDeValidacao.VALIDADO,
    )
    ExaminarElo(**pecas).rodar(
        dono=HORIZONTE, projeto_id=projeto.id, aresta_id=e1.id,
        estado=EstadoDoExame.INSUFICIENTE, reserva="falta a condição de volume",
    )
    conector = FormarConectorE(**pecas).rodar(
        dono=HORIZONTE, projeto_id=projeto.id, arestas=(e1.id, e2.id)
    )

    reaberta = pecas["repositorio"].obter_ara(HORIZONTE.inquilino_id, projeto.id)

    assert reaberta.e_ude(ude.id) is True
    ficha = reaberta.ficha(ude.id)
    assert ficha.area_impactada == "Secretaria"
    assert ficha.evidencias == ("relatório interno de conclusão", "painel da coordenação")
    assert reaberta.status(ude.id) is StatusDeValidacao.VALIDADO
    assert [p.origem for p in reaberta.pareceres(ude.id)] == [
        OrigemDoParecer.CATALOGO,
        OrigemDoParecer.HUMANO,
    ]
    assert reaberta.pareceres(ude.id)[0].proposta_id == "prop-001"
    assert reaberta.exame(e1.id).estado is EstadoDoExame.INSUFICIENTE
    assert reaberta.exame(e1.id).reserva == "falta a condição de volume"
    assert reaberta.exame(e2.id).estado is EstadoDoExame.NAO_EXAMINADO
    assert [c.id for c in reaberta.conectores] == [conector.id]
    assert set(reaberta.conectores[0].arestas) == {e1.id, e2.id}


def test_a_validacao_formal_e_recalculada_na_reidratacao_nunca_lida_do_banco(pecas):
    """Por isso não existe tabela de validação: ela é função pura do texto do nó."""
    projeto = CriarProjetoARA(**pecas).rodar(dono=HORIZONTE, nome="Horizonte — ARA")
    no = AdicionarEfeito(**pecas).rodar(dono=HORIZONTE, projeto_id=projeto.id, titulo=RUIM)
    MarcarUde(**pecas).rodar(dono=HORIZONTE, projeto_id=projeto.id, no_id=no.id)

    reaberta = pecas["repositorio"].obter_ara(HORIZONTE.inquilino_id, projeto.id)
    assert reaberta.validacao(no.id).aprovado_nos_decidiveis is False
    assert reaberta.validacao(no.id).veredito_de("CD-5").reprovou is True

    ReformularUde(**pecas).rodar(
        dono=HORIZONTE, projeto_id=projeto.id, no_id=no.id, texto=BOM
    )
    depois = pecas["repositorio"].obter_ara(HORIZONTE.inquilino_id, projeto.id)
    assert depois.validacao(no.id).aprovado_nos_decidiveis is True


def test_analisar_a_arvore_persistida_acha_a_causa_raiz_candidata(pecas):
    projeto = CriarProjetoARA(**pecas).rodar(dono=HORIZONTE, nome="Horizonte — ARA")
    adicionar, ligar = AdicionarEfeito(**pecas), LigarNaARA(**pecas)
    raiz = adicionar.rodar(
        dono=HORIZONTE, projeto_id=projeto.id, titulo="A conferência de matrícula é manual."
    )
    meio = adicionar.rodar(
        dono=HORIZONTE, projeto_id=projeto.id, titulo="A fila de conferência tem 200 pedidos."
    )
    ude1 = adicionar.rodar(dono=HORIZONTE, projeto_id=projeto.id, titulo=BOM)
    ude2 = adicionar.rodar(
        dono=HORIZONTE, projeto_id=projeto.id,
        titulo="O intervalo médio da matrícula até a primeira aula é de 43 dias.",
    )
    orfao = adicionar.rodar(
        dono=HORIZONTE, projeto_id=projeto.id, titulo="A biblioteca abre às 8 horas."
    )
    ligar.rodar(dono=HORIZONTE, projeto_id=projeto.id, origem_id=raiz.id, destino_id=meio.id)
    ligar.rodar(dono=HORIZONTE, projeto_id=projeto.id, origem_id=meio.id, destino_id=ude1.id)
    ligar.rodar(dono=HORIZONTE, projeto_id=projeto.id, origem_id=raiz.id, destino_id=ude2.id)
    for alvo in (ude1, ude2):
        MarcarUde(**pecas).rodar(dono=HORIZONTE, projeto_id=projeto.id, no_id=alvo.id)

    relatorio = AnalisarArvore(**pecas).rodar(dono=HORIZONTE, projeto_id=projeto.id)

    assert relatorio.causa_raiz_candidata == raiz.id
    assert relatorio.orfaos == (orfao.id,)
    assert relatorio.resumo()["udes"] == 2
    assert relatorio.resumo()["elos_nao_examinados"] == 3


# -- isolamento por inquilino, também na porta do M2 ---------------------------------------


def test_a_ara_de_outro_inquilino_nao_atravessa_a_fronteira(pecas):
    projeto = CriarProjetoARA(**pecas).rodar(dono=HORIZONTE, nome="Horizonte — ARA")
    AdicionarEfeito(**pecas).rodar(dono=HORIZONTE, projeto_id=projeto.id, titulo=BOM)

    assert pecas["repositorio"].obter_ara(ALVORADA.inquilino_id, projeto.id) is None
    assert pecas["repositorio"].obter(ALVORADA.inquilino_id, projeto.id) is None
    with pytest.raises(NaoEncontrado):
        AdicionarEfeito(**pecas).rodar(
            dono=ALVORADA, projeto_id=projeto.id, titulo="Nó da intrusa."
        )
    # e o projeto do outro inquilino continua intacto
    intacto = pecas["repositorio"].obter(HORIZONTE.inquilino_id, projeto.id)
    assert len(intacto.nos) == 1


def test_dois_inquilinos_nao_veem_o_grafo_um_do_outro(pecas):
    do_horizonte = CriarProjetoARA(**pecas).rodar(dono=HORIZONTE, nome="Horizonte — ARA")
    da_alvorada = CriarProjetoARA(**pecas).rodar(dono=ALVORADA, nome="Alvorada — ARA")
    AdicionarEfeito(**pecas).rodar(dono=HORIZONTE, projeto_id=do_horizonte.id, titulo=BOM)
    AdicionarEfeito(**pecas).rodar(
        dono=ALVORADA, projeto_id=da_alvorada.id, titulo="Nó da Alvorada, só dela."
    )

    listados = pecas["repositorio"].listar(HORIZONTE.inquilino_id)
    assert [p.id for p in listados] == [do_horizonte.id]
    assert [n.titulo for n in listados[0].nos] == [BOM]


# -- as invariantes impostas PELO BANCO ----------------------------------------------------


def test_o_banco_recusa_auto_laco_e_aresta_duplicada(pecas, url_postgres, esquema_migrado):
    """RN-02 e RN-03 não dependem só do domínio: `sem_auto_laco` e `uq_aresta_par`."""
    projeto = CriarProjetoARA(**pecas).rodar(dono=HORIZONTE, nome="Horizonte — ARA")
    a = AdicionarEfeito(**pecas).rodar(dono=HORIZONTE, projeto_id=projeto.id, titulo="Nó A qualquer.")
    b = AdicionarEfeito(**pecas).rodar(dono=HORIZONTE, projeto_id=projeto.id, titulo="Nó B qualquer.")
    LigarNaARA(**pecas).rodar(
        dono=HORIZONTE, projeto_id=projeto.id, origem_id=a.id, destino_id=b.id
    )

    persistencia = criar_persistencia(
        Configuracao.do_ambiente(
            {"DATABASE_URL": url_postgres, "TOC_DB_SCHEMA": esquema_migrado}
        )
    )
    with persistencia.motor.begin() as conexao:
        with pytest.raises(IntegrityError):
            conexao.execute(
                text(
                    "insert into aresta_causal "
                    "(id, projeto_id, origem_id, destino_id, criado_em, alterado_em) "
                    "values (:i, :p, :o, :o, now(), now())"
                ),
                {"i": uuid4(), "p": projeto.id, "o": a.id},
            )
    with persistencia.motor.begin() as conexao:
        with pytest.raises(IntegrityError):
            conexao.execute(
                text(
                    "insert into aresta_causal "
                    "(id, projeto_id, origem_id, destino_id, criado_em, alterado_em) "
                    "values (:i, :p, :o, :d, now(), now())"
                ),
                {"i": uuid4(), "p": projeto.id, "o": a.id, "d": b.id},
            )


def test_o_banco_recusa_exame_sem_reserva_e_aresta_em_dois_conectores(
    pecas, url_postgres, esquema_migrado
):
    """RF-22 e RN-11 impostas pelo banco além do domínio."""
    projeto = CriarProjetoARA(**pecas).rodar(dono=HORIZONTE, nome="Horizonte — ARA")
    adicionar, ligar = AdicionarEfeito(**pecas), LigarNaARA(**pecas)
    c1 = adicionar.rodar(dono=HORIZONTE, projeto_id=projeto.id, titulo="Nó C1 qualquer.")
    c2 = adicionar.rodar(dono=HORIZONTE, projeto_id=projeto.id, titulo="Nó C2 qualquer.")
    destino = adicionar.rodar(dono=HORIZONTE, projeto_id=projeto.id, titulo=BOM)
    e1 = ligar.rodar(dono=HORIZONTE, projeto_id=projeto.id, origem_id=c1.id, destino_id=destino.id)
    e2 = ligar.rodar(dono=HORIZONTE, projeto_id=projeto.id, origem_id=c2.id, destino_id=destino.id)
    conector = FormarConectorE(**pecas).rodar(
        dono=HORIZONTE, projeto_id=projeto.id, arestas=(e1.id, e2.id)
    )

    persistencia = criar_persistencia(
        Configuracao.do_ambiente(
            {"DATABASE_URL": url_postgres, "TOC_DB_SCHEMA": esquema_migrado}
        )
    )
    with persistencia.motor.begin() as conexao:
        with pytest.raises(IntegrityError):
            conexao.execute(
                text(
                    "insert into elo_exame (aresta_id, projeto_id, estado, reserva) "
                    "values (:a, :p, 'insuficiente', '')"
                ),
                {"a": e1.id, "p": projeto.id},
            )
    with persistencia.motor.begin() as conexao:
        conexao.execute(
            text("insert into conector_e (id, projeto_id, destino_id) values (:i,:p,:d)"),
            {"i": (outro := uuid4()), "p": projeto.id, "d": destino.id},
        )
        with pytest.raises(IntegrityError):
            conexao.execute(
                text(
                    "insert into conector_e_aresta (conector_id, aresta_id) "
                    "values (:c, :a)"
                ),
                {"c": outro, "a": e1.id},
            )
    assert conector.destino_id == destino.id
