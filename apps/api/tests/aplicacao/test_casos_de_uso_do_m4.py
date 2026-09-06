"""Casos de uso do M4 — sobre as portas, sem banco e sem rede (spec 008).

Siglas, uma vez neste arquivo: **M4** — Árvores de Futuro e Implementação · **ARF** —
Árvore da Realidade Futura · **APR** — Árvore de Pré-Requisitos · **AT** — Árvore de
Transição · **ARA** — Árvore da Realidade Atual · **UDE** — Efeito Indesejável · **NC** —
Nuvem de Conflito · **OI** — Objetivo Intermediário · **OTel** — OpenTelemetry ·
**RF/RNF** — requisito funcional / requisito não funcional da spec 008.

O que este arquivo protege, e que nenhum teste de domínio alcança sozinho:

- **cada mutação abre um span** (P5, RNF-03) — e o span carrega grandeza e identificador,
  **nunca** o texto que a pessoa escreveu (ADR 0006);
- **promover, semear e derivar carregam no traço o identificador da referência criada**
  (RNF-03) — a linha auditável do encadeamento nasce junto com ele;
- **a autorização acontece no caso de uso** (§B.7.2 do Anexo B), pelo `Executor`;
- **a exclusão suave de um projeto suspende as referências que o tocam** (RF-35), e a
  restauração as reativa — pelo caso de uso, não por gatilho de banco.
"""
from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

import pytest

from toc_api.aplicacao.arvores import (
    AbrirProjetoAPR,
    AbrirProjetoARF,
    AbrirProjetoAT,
    AceitarRamoNegativo,
    AdicionarNoDaAPR,
    AdicionarNoDaARF,
    AvaliarVerbalizacao,
    CriarProjetoAPR,
    CriarProjetoARF,
    CriarProjetoAT,
    DeclararDependencia,
    EspelharUde,
    JulgarTesteDeValidade,
    LigarNaARF,
    MarcarRamoNegativo,
    MudarStatusDoPasso,
    ParearObstaculo,
    RegistrarPasso,
    SequenciarAPR,
    TratarRamoNegativo,
    VerificarARF,
)
from toc_api.aplicacao.cadeia import (
    AbrirCadeia,
    DerivarAprDeArf,
    DerivarAtDeOi,
    PromoverUdesParaNC,
    SemearArfDeInjecao,
)
from toc_api.aplicacao.governanca import (
    TOC_ESCRITA,
    TOC_LEITURA,
    AutorizacaoNegada,
    Executor,
)
from toc_api.aplicacao.projetos import ExcluirProjeto, RestaurarProjeto
from toc_api.dominio.apr import PapelNaAPR
from toc_api.dominio.ara import OrigemDoParecer, ParecerDeJulgamento, StatusDeValidacao, novo_projeto_ara
from toc_api.dominio.arf import EstadoDoRamo, PapelNaARF
from toc_api.dominio.at import StatusDoPasso
from toc_api.dominio.encadeamento import PromocaoInvalida
from toc_api.dominio.federacao.principal import principal_de_introspeccao
from toc_api.dominio.nuvem import ChaveDaAresta, StatusDeInjecao
from toc_api.dominio.referencia import EstadoDaReferencia

from .fakes import RelogioFalso, RastreadorFalso
from .fakes_m4 import RepositorioDoM4Falso

AGORA = datetime(2026, 9, 6, 10, 0, tzinfo=timezone.utc)
UDES = (
    "A taxa de evasão no primeiro semestre é de 22%.",
    "O caixa da instituição fecha o trimestre negativo.",
)
INJECAO = "faseamento orçamentário condicionado a marco de receita"
EFEITO = "as duas frentes recebem verba no trimestre"


def principal(capabilities=(TOC_LEITURA, TOC_ESCRITA)):
    return principal_de_introspeccao(
        {
            "active": True,
            "user": {"id": "u-facilitadora", "name": "Facilitadora TOC"},
            "tenant_id": "instituicao-horizonte",
            "capabilities": list(capabilities),
            "app_id": "toc",
        }
    )


@pytest.fixture()
def pecas():
    rastreador = RastreadorFalso()
    repositorio = RepositorioDoM4Falso()
    executor = Executor(
        principal=principal(),
        rastreador=rastreador,
        repositorio=repositorio,
        relogio=RelogioFalso(AGORA),
    )
    return executor, repositorio, rastreador


def ara_validada(repositorio, dono):
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
    repositorio.salvar_ara(ara)
    return ara, tuple(ids)


# --------------------------------------------------------------------------------------
# ARF — criação, papéis, espelho, ramos e verificação
# --------------------------------------------------------------------------------------


def test_criar_e_abrir_a_arf_pelo_executor_abre_span_por_caso_de_uso(pecas) -> None:
    executor, _, rastreador = pecas

    projeto = executor.rodar(CriarProjetoARF, nome="Futuro da expansão")
    arf = executor.rodar(AbrirProjetoARF, projeto_id=projeto.id)

    print(f"spans: {rastreador.nomes}")
    assert rastreador.nomes == ["caso_de_uso.criar_projeto_arf", "caso_de_uso.abrir_projeto_arf"]
    assert arf.projeto.id == projeto.id
    assert rastreador.spans[0].atributos["toc.inquilino_id"] == "instituicao-horizonte"


def test_o_span_da_arf_carrega_grandeza_e_papel_nunca_o_texto(pecas) -> None:
    """ADR 0006: enunciado de pessoa não entra em traço. O papel é vocabulário nosso."""
    executor, _, rastreador = pecas
    projeto = executor.rodar(CriarProjetoARF, nome="Futuro")

    executor.rodar(
        AdicionarNoDaARF, projeto_id=projeto.id, papel=PapelNaARF.INJECAO, titulo=INJECAO
    )

    atributos = rastreador.spans[-1].atributos
    print(f"atributos do span: {atributos}")
    assert atributos["toc.papel"] == "injecao"
    assert INJECAO not in str(atributos)


def test_a_verificacao_da_arf_anota_o_resumo_quantitativo_no_span(pecas) -> None:
    executor, _, rastreador = pecas
    projeto = executor.rodar(CriarProjetoARF, nome="Futuro")
    injecao = executor.rodar(
        AdicionarNoDaARF, projeto_id=projeto.id, papel=PapelNaARF.INJECAO, titulo=INJECAO
    )
    efeito = executor.rodar(
        AdicionarNoDaARF, projeto_id=projeto.id, papel=PapelNaARF.EFEITO_FUTURO, titulo=EFEITO
    )
    executor.rodar(LigarNaARF, projeto_id=projeto.id, origem_id=injecao.id, destino_id=efeito.id)

    verificacao = executor.rodar(VerificarARF, projeto_id=projeto.id)

    atributos = rastreador.spans[-1].atributos
    print(f"resumo no span: {atributos}")
    assert verificacao.injecoes_sem_efeito == ()
    assert atributos["toc.ramos_negativos_abertos"] == 0
    assert atributos["toc.sem_origem_vinculada"] is True


def test_o_ramo_negativo_atravessa_marcar_tratar_e_aceitar_pelo_executor(pecas) -> None:
    executor, _, _ = pecas
    projeto = executor.rodar(CriarProjetoARF, nome="Futuro")
    colateral = executor.rodar(
        AdicionarNoDaARF,
        projeto_id=projeto.id,
        papel=PapelNaARF.EFEITO_FUTURO,
        titulo="a equipe da Secretaria acumula dupla jornada",
    )
    corte = executor.rodar(
        AdicionarNoDaARF,
        projeto_id=projeto.id,
        papel=PapelNaARF.INJECAO,
        titulo="contratação temporária no pico",
    )
    ramo = executor.rodar(MarcarRamoNegativo, projeto_id=projeto.id, no_id=colateral.id)

    tratado = executor.rodar(
        TratarRamoNegativo, projeto_id=projeto.id, ramo_id=ramo.id, injecao_id=corte.id
    )
    print(f"ramo tratado por: {tratado.injecao_de_corte_id}")
    assert tratado.estado is EstadoDoRamo.TRATADO

    outro = executor.rodar(
        AdicionarNoDaARF,
        projeto_id=projeto.id,
        papel=PapelNaARF.EFEITO_FUTURO,
        titulo="a fila de matrícula cresce em janeiro",
    )
    segundo = executor.rodar(MarcarRamoNegativo, projeto_id=projeto.id, no_id=outro.id)
    aceito = executor.rodar(
        AceitarRamoNegativo,
        projeto_id=projeto.id,
        ramo_id=segundo.id,
        justificativa="o pico dura três semanas",
        autor="Facilitadora TOC",
    )
    assert aceito.estado is EstadoDoRamo.ACEITO


def test_o_principal_so_leitura_nao_muta_a_arf(pecas) -> None:
    """§B.7.2: a verificação de acesso acontece no caso de uso, e é fail-closed."""
    _, repositorio, rastreador = pecas
    so_le = Executor(
        principal=principal([TOC_LEITURA]),
        rastreador=rastreador,
        repositorio=repositorio,
        relogio=RelogioFalso(AGORA),
    )
    with pytest.raises(AutorizacaoNegada) as erro:
        so_le.rodar(CriarProjetoARF, nome="Futuro")
    print(f"negado: capability={erro.value.capability} operação={erro.value.operacao}")
    assert erro.value.capability == TOC_ESCRITA


# --------------------------------------------------------------------------------------
# APR — pareamento, julgamento, dependência e sequenciamento
# --------------------------------------------------------------------------------------


def test_a_apr_sequencia_e_anota_o_resumo_no_span(pecas) -> None:
    executor, _, rastreador = pecas
    projeto = executor.rodar(
        CriarProjetoAPR, nome="Implantação", objetivo="O faseamento está implantado"
    )
    obstaculo = executor.rodar(
        AdicionarNoDaAPR,
        projeto_id=projeto.id,
        papel=PapelNaAPR.OBSTACULO,
        titulo="Há apenas uma pessoa treinada no acompanhamento",
    )
    oi = executor.rodar(
        AdicionarNoDaAPR,
        projeto_id=projeto.id,
        papel=PapelNaAPR.OBJETIVO_INTERMEDIARIO,
        titulo="Existem três pessoas treinadas e escaladas",
    )
    par = executor.rodar(
        ParearObstaculo, projeto_id=projeto.id, obstaculo_id=obstaculo.id, oi_id=oi.id
    )
    executor.rodar(
        JulgarTesteDeValidade,
        projeto_id=projeto.id,
        par_id=par.id,
        autor="Facilitadora TOC",
        valido=True,
        justificativa="com três pessoas o acompanhamento não depende de uma só",
    )
    apr = executor.rodar(AbrirProjetoAPR, projeto_id=projeto.id)
    executor.rodar(
        DeclararDependencia,
        projeto_id=projeto.id,
        antes_id=oi.id,
        depois_id=apr.objetivo.id,
    )

    sequencia = executor.rodar(SequenciarAPR, projeto_id=projeto.id)

    atributos = rastreador.spans[-1].atributos
    print(f"sequenciamento: {sequencia.resumo()} · span={atributos}")
    assert sequencia.completo is True
    assert atributos["toc.camadas"] == 1
    assert atributos["toc.bloqueado"] is False


def test_a_verbalizacao_avaliada_e_leitura_pura_e_alcanca_o_principal_so_leitura(pecas) -> None:
    """RN-08: avisa, não veta — e por ser leitura pura, quem só lê também a alcança."""
    executor, repositorio, rastreador = pecas
    projeto = executor.rodar(
        CriarProjetoAPR, nome="Implantação", objetivo="O faseamento está implantado"
    )
    torto = executor.rodar(
        AdicionarNoDaAPR,
        projeto_id=projeto.id,
        papel=PapelNaAPR.OBSTACULO,
        titulo="Precisamos criar a conversão de dados",
    )

    so_le = Executor(
        principal=principal([TOC_LEITURA]),
        rastreador=rastreador,
        repositorio=repositorio,
        relogio=RelogioFalso(AGORA),
    )
    avaliacao = so_le.rodar(AvaliarVerbalizacao, projeto_id=projeto.id, no_id=torto.id)

    print(f"veredito={avaliacao.veredito.value} códigos={avaliacao.codigos}")
    assert avaliacao.codigos == ("verbo_de_acao",)


# --------------------------------------------------------------------------------------
# AT — passo com a tripla e acompanhamento
# --------------------------------------------------------------------------------------


def test_o_passo_da_at_nasce_com_a_tripla_e_o_status_muda_pelo_executor(pecas) -> None:
    executor, _, rastreador = pecas
    projeto = executor.rodar(CriarProjetoAT, nome="Transição")
    passo = executor.rodar(
        RegistrarPasso,
        projeto_id=projeto.id,
        acao="publicar a chamada interna de treinamento",
        necessidade="não há hoje candidato mapeado",
        resultado_esperado="lista de inscritos até sexta",
    )

    executor.rodar(
        MudarStatusDoPasso,
        projeto_id=projeto.id,
        no_id=passo.id,
        status=StatusDoPasso.CONCLUIDO,
        resultado_real="apenas duas inscritas até sexta",
    )

    at = executor.rodar(AbrirProjetoAT, projeto_id=projeto.id)
    atributos = rastreador.spans[-2].atributos
    print(f"resumo={at.resumo_de_execucao()} · span={atributos}")
    assert at.resumo_de_execucao()["concluido"] == 1
    assert atributos["toc.status_do_passo"] == "concluido"
    assert atributos["toc.divergente"] is True


# --------------------------------------------------------------------------------------
# A cadeia — promover, semear, derivar, e o traço com a referência
# --------------------------------------------------------------------------------------


def test_promover_carrega_a_referencia_criada_no_traco(pecas) -> None:
    """RNF-03: "promoções, semeaduras e derivações carregam no traço o identificador da
    referência criada — a linha auditável do encadeamento"."""
    executor, repositorio, rastreador = pecas
    ara, udes = ara_validada(repositorio, executor.principal.dono())

    nuvem = executor.rodar(
        PromoverUdesParaNC, projeto_id=ara.projeto.id, no_ids=udes, nome="Dilema da expansão"
    )

    atributos = rastreador.spans[-1].atributos
    print(f"span da promoção: {atributos}")
    assert atributos["toc.udes_promovidos"] == 2
    assert atributos["toc.referencia_id"]
    assert atributos["toc.projeto_destino"] == str(nuvem.projeto.id)
    guardada = repositorio.listar_referencias("instituicao-horizonte")
    assert len(guardada) == 1
    assert guardada[0].estado is EstadoDaReferencia.ATIVA


def test_promover_ude_nao_validado_e_recusado_e_a_recusa_tambem_deixa_span(pecas) -> None:
    executor, repositorio, rastreador = pecas
    dono = executor.principal.dono()
    ara = novo_projeto_ara(id=uuid4(), dono=dono, nome="Realidade atual", em=AGORA)
    no = ara.adicionar_efeito(titulo=UDES[0], em=AGORA)
    ara.marcar_ude(no.id, em=AGORA)
    repositorio.salvar_ara(ara)

    with pytest.raises(PromocaoInvalida):
        executor.rodar(
            PromoverUdesParaNC, projeto_id=ara.projeto.id, no_ids=(no.id,), nome="Dilema"
        )

    span = rastreador.spans[-1]
    print(f"span da recusa: {span.atributos}")
    assert span.atributos["toc.resultado"] == "erro"
    assert span.atributos["toc.erro"] == "PromocaoInvalida"
    assert repositorio.listar_referencias("instituicao-horizonte") == []


def cadeia_ate_a_apr(executor, repositorio):
    ara, udes = ara_validada(repositorio, executor.principal.dono())
    nuvem = executor.rodar(
        PromoverUdesParaNC, projeto_id=ara.projeto.id, no_ids=udes, nome="Dilema"
    )
    premissa = nuvem.registrar_premissa(
        ChaveDaAresta.D_D_PRIME, "o orçamento é indivisível no exercício", em=AGORA
    )
    injecao = nuvem.registrar_injecao(premissa.id, INJECAO, em=AGORA)
    nuvem.mudar_status_de_injecao(injecao.id, StatusDeInjecao.ESCOLHIDA, em=AGORA)
    repositorio.salvar_nuvem(nuvem)

    arf = executor.rodar(
        SemearArfDeInjecao,
        projeto_id=nuvem.projeto.id,
        injecao_id=injecao.id,
        nome="Futuro da expansão",
    )
    efeito = executor.rodar(
        AdicionarNoDaARF,
        projeto_id=arf.projeto.id,
        papel=PapelNaARF.EFEITO_FUTURO,
        titulo=EFEITO,
    )
    executor.rodar(
        EspelharUde, projeto_id=arf.projeto.id, no_id=efeito.id, ude_id=udes[0]
    )
    apr = executor.rodar(
        DerivarAprDeArf, projeto_id=arf.projeto.id, no_id=efeito.id, nome="Implantação"
    )
    return ara, nuvem, arf, apr, efeito


def test_a_cadeia_inteira_roda_pelos_casos_de_uso_e_a_vista_a_percorre(pecas) -> None:
    executor, repositorio, _ = pecas
    ara, nuvem, arf, apr, _ = cadeia_ate_a_apr(executor, repositorio)
    oi = executor.rodar(
        AdicionarNoDaAPR,
        projeto_id=apr.projeto.id,
        papel=PapelNaAPR.OBJETIVO_INTERMEDIARIO,
        titulo="Existem três pessoas treinadas e escaladas",
    )
    at = executor.rodar(
        DerivarAtDeOi, projeto_id=apr.projeto.id, no_id=oi.id, nome="Transição"
    )

    cadeia = executor.rodar(AbrirCadeia, projeto_id=arf.projeto.id)

    print(f"cadeia: {' → '.join(cadeia.ferramentas())} · resumo={cadeia.resumo()}")
    assert cadeia.ferramentas() == ("ara", "nc", "arf", "apr", "at")
    assert len(cadeia.elos) == 4
    assert at.alvo.projeto_id == apr.projeto.id


def test_a_semeadura_grava_a_nuvem_com_a_referencia_de_semeadura_preenchida(pecas) -> None:
    """INT-03: o campo criado vazio no ciclo 007 volta do repositório preenchido."""
    executor, repositorio, _ = pecas
    _, nuvem, arf, _, _ = cadeia_ate_a_apr(executor, repositorio)

    de_volta = repositorio.obter_nuvem("instituicao-horizonte", nuvem.projeto.id)
    semeaduras = de_volta.semeaduras()

    print(f"semeaduras gravadas: {[(str(s.injecao_id)[:8], s.projeto_destino_id) for s in semeaduras]}")
    assert len(semeaduras) == 1
    assert semeaduras[0].projeto_destino_id == arf.projeto.id


def test_excluir_o_projeto_suspende_as_referencias_e_restaurar_as_reativa(pecas) -> None:
    """RF-35: "referência nunca é apagada por efeito colateral" — suspende e reativa."""
    executor, repositorio, rastreador = pecas
    ara, udes = ara_validada(repositorio, executor.principal.dono())
    nuvem = executor.rodar(
        PromoverUdesParaNC, projeto_id=ara.projeto.id, no_ids=udes, nome="Dilema"
    )

    executor.rodar(ExcluirProjeto, projeto_id=nuvem.projeto.id)

    referencia = repositorio.listar_referencias("instituicao-horizonte")[0]
    print(f"após excluir: estado={referencia.estado.value} motivo={referencia.motivo!r}")
    assert referencia.estado is EstadoDaReferencia.PENDENTE
    assert str(nuvem.projeto.id) in referencia.motivo
    assert rastreador.spans[-1].atributos["toc.referencias_suspensas"] == 1

    executor.rodar(RestaurarProjeto, projeto_id=nuvem.projeto.id)

    assert referencia.estado is EstadoDaReferencia.ATIVA
    assert rastreador.spans[-1].atributos["toc.referencias_reativadas"] == 1


def test_a_vista_da_cadeia_mostra_o_elo_pendente_em_vez_de_esconde_lo(pecas) -> None:
    executor, repositorio, _ = pecas
    ara, udes = ara_validada(repositorio, executor.principal.dono())
    nuvem = executor.rodar(
        PromoverUdesParaNC, projeto_id=ara.projeto.id, no_ids=udes, nome="Dilema"
    )
    executor.rodar(ExcluirProjeto, projeto_id=nuvem.projeto.id)

    cadeia = executor.rodar(AbrirCadeia, projeto_id=ara.projeto.id)

    print(f"elos={len(cadeia.elos)} pendentes={len(cadeia.pendentes())}")
    assert len(cadeia.elos) == 1
    assert len(cadeia.pendentes()) == 1


def test_projeto_de_outro_inquilino_e_indistinguivel_de_inexistente(pecas) -> None:
    executor, repositorio, rastreador = pecas
    projeto = executor.rodar(CriarProjetoARF, nome="Futuro")

    de_outro = Executor(
        principal=principal_de_introspeccao(
            {
                "active": True,
                "user": {"id": "u-aurora"},
                "tenant_id": "instituicao-aurora",
                "capabilities": [TOC_LEITURA, TOC_ESCRITA],
                "app_id": "toc",
            }
        ),
        rastreador=rastreador,
        repositorio=repositorio,
        relogio=RelogioFalso(AGORA),
    )
    from toc_api.dominio.erros import NaoEncontrado

    with pytest.raises(NaoEncontrado):
        de_outro.rodar(AbrirProjetoARF, projeto_id=projeto.id)
