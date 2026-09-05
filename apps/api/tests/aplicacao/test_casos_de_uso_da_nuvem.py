"""Casos de uso da Nuvem de Conflito (M3) — sobre as portas, sem banco e sem rede.

Siglas, uma vez: **NC** — Nuvem de Conflito · **ARA** — Árvore da Realidade Atual ·
**UDE** — Efeito Indesejável · **TOC** — Teoria das Restrições · **TRIZ** — Teoria da
Resolução Inventiva de Problemas · **OTel** — OpenTelemetry · **IA** — inteligência
artificial.

O que este arquivo protege, e que nenhum teste de domínio alcança sozinho:

- **cada mutação abre um span** (P5, RNF-03) — e o span carrega grandeza, nunca o texto
  que a pessoa escreveu (ADR 0006);
- **a autorização acontece no caso de uso** (§B.7.2), pelo `Executor`, e não na rota;
- **a geração valida o esquema antes de qualquer efeito** (RF-22) — o motor é porta, e o
  duplo devolve estrutura torta de propósito para a falha fechada aparecer;
- **o encadeamento M2 → M3** roda como caso de uso, com o dono vindo da ARA de origem.
"""
from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID, uuid4

import pytest

from toc_api.aplicacao.governanca import (
    TOC_ESCRITA,
    TOC_LEITURA,
    AutorizacaoNegada,
    Executor,
)
from toc_api.aplicacao.nuvem import (
    AbrirProjetoNC,
    AplicarGeracaoDeNuvem,
    ArquivarPremissa,
    ClassificarInjecao,
    CriarProjetoNC,
    DerivarNuvemDeUdes,
    DesafiarPremissa,
    EditarEntidadeDaNuvem,
    EditarRacionalDaNuvem,
    GerarNuvemPorNarrativa,
    MudarStatusDeInjecao,
    RegistrarInjecao,
    RegistrarPremissa,
    SugerirInjecoes,
    SugerirPremissas,
    ValidarNuvem,
)
from toc_api.dominio.ara import novo_projeto_ara
from toc_api.dominio.federacao.principal import principal_de_introspeccao
from toc_api.dominio.geracao import ResultadoDeGeracao, ResultadoDeGeracaoInvalido
from toc_api.dominio.nuvem import (
    ChaveDaAresta,
    PapelDaEntidade,
    SeparacaoTRIZ,
    StatusDeInjecao,
)

from ..dominio.nuvem_sintetica import DILEMA, NARRATIVA, UDES_SINTETICOS
from ..dominio.test_resultado_de_geracao import BRUTO
from .fakes import (
    MotorDeGeracaoFalso,
    RastreadorFalso,
    RelogioFalso,
    RepositorioDeNuvemFalso,
)

AGORA = datetime(2026, 9, 5, 12, 0, tzinfo=timezone.utc)
INQUILINO = "instituicao-horizonte"


def principal_com(capabilities: list[str]):
    return principal_de_introspeccao(
        {
            "active": True,
            "user": {"id": "u-horizonte-01"},
            "tenant_id": INQUILINO,
            "capabilities": capabilities,
        }
    )


PLENA = principal_com([TOC_LEITURA, TOC_ESCRITA])
SO_LE = principal_com([TOC_LEITURA])


def montar(motor=None):
    rastreador = RastreadorFalso()
    repositorio = RepositorioDeNuvemFalso()
    executor = Executor(
        principal=PLENA,
        rastreador=rastreador,
        repositorio=repositorio,
        relogio=RelogioFalso(instante=AGORA),
        motor=motor,
    )
    return executor, rastreador, repositorio


def nuvem_criada(executor) -> UUID:
    projeto = executor.rodar(CriarProjetoNC, nome="Dilema da expansão")
    return projeto.id


# --------------------------------------------------------------------------------------
# Criação, leitura e edição
# --------------------------------------------------------------------------------------


def test_criar_projeto_nc_grava_a_nuvem_inteira_e_abre_span() -> None:
    executor, rastreador, repositorio = montar()

    projeto = executor.rodar(CriarProjetoNC, nome="Dilema da expansão")

    nuvem = repositorio.obter_nuvem(INQUILINO, projeto.id)
    print(f"spans: {rastreador.nomes}")
    assert (len(nuvem.entidades), len(nuvem.arestas)) == (5, 7)
    assert "caso_de_uso.criar_projeto_nc" in rastreador.nomes


def test_abrir_projeto_nc_devolve_o_agregado_do_inquilino_e_nada_de_outro() -> None:
    executor, _, repositorio = montar()
    projeto_id = nuvem_criada(executor)

    aberta = executor.rodar(AbrirProjetoNC, projeto_id=projeto_id)
    assert aberta.projeto.id == projeto_id

    de_fora = Executor(
        principal=principal_de_introspeccao(
            {
                "active": True,
                "user": {"id": "u-aurora"},
                "tenant_id": "instituicao-aurora",
                "capabilities": [TOC_LEITURA, TOC_ESCRITA],
            }
        ),
        rastreador=RastreadorFalso(),
        repositorio=repositorio,
        relogio=RelogioFalso(instante=AGORA),
    )
    from toc_api.dominio.erros import NaoEncontrado

    with pytest.raises(NaoEncontrado):
        de_fora.rodar(AbrirProjetoNC, projeto_id=projeto_id)


def test_editar_entidade_e_racional_gravam_e_anotam_grandeza_nunca_texto() -> None:
    executor, rastreador, repositorio = montar()
    projeto_id = nuvem_criada(executor)

    executor.rodar(
        EditarEntidadeDaNuvem,
        projeto_id=projeto_id,
        papel=PapelDaEntidade.B,
        texto=DILEMA[PapelDaEntidade.B],
    )
    executor.rodar(
        EditarRacionalDaNuvem,
        projeto_id=projeto_id,
        racional="A instituição precisa de caixa e de reputação.",
    )

    nuvem = repositorio.obter_nuvem(INQUILINO, projeto_id)
    atributos = [a for s in rastreador.spans for a in s.atributos.values()]
    print(f"atributos de span: {atributos}")
    assert nuvem.texto(PapelDaEntidade.B) == DILEMA[PapelDaEntidade.B]
    assert nuvem.racional.startswith("A instituição")
    for valor in atributos:
        assert DILEMA[PapelDaEntidade.B] != valor
        assert "A instituição precisa" != valor


def test_premissa_e_injecao_passam_pelo_caso_de_uso_com_traco() -> None:
    """RNF-03 e a DoD 11: registrar premissa e injeção SEM traço não é pronto."""
    executor, rastreador, repositorio = montar()
    projeto_id = nuvem_criada(executor)

    premissa = executor.rodar(
        RegistrarPremissa,
        projeto_id=projeto_id,
        chave=ChaveDaAresta.D_D_PRIME,
        texto="não há orçamento para as duas ações",
    )
    injecao = executor.rodar(
        RegistrarInjecao,
        projeto_id=projeto_id,
        premissa_id=premissa.id,
        texto="faseamento orçamentário por marco de receita",
        separacao=SeparacaoTRIZ.TEMPO,
    )
    executor.rodar(
        ClassificarInjecao,
        projeto_id=projeto_id,
        injecao_id=injecao.id,
        separacao=SeparacaoTRIZ.GRAU,
    )
    executor.rodar(
        MudarStatusDeInjecao,
        projeto_id=projeto_id,
        injecao_id=injecao.id,
        status=StatusDeInjecao.ESCOLHIDA,
    )

    nuvem = repositorio.obter_nuvem(INQUILINO, projeto_id)
    print(f"spans do M3: {[n for n in rastreador.nomes if 'nuvem' in n or 'premissa' in n or 'injecao' in n]}")
    assert nuvem.injecao(injecao.id).status is StatusDeInjecao.ESCOLHIDA
    assert nuvem.injecao(injecao.id).separacao is SeparacaoTRIZ.GRAU
    for esperado in (
        "caso_de_uso.registrar_premissa",
        "caso_de_uso.registrar_injecao",
        "caso_de_uso.classificar_injecao",
        "caso_de_uso.mudar_status_de_injecao",
    ):
        assert esperado in rastreador.nomes, esperado


def test_arquivar_premissa_devolve_quantas_injecoes_foram_junto() -> None:
    executor, rastreador, _ = montar()
    projeto_id = nuvem_criada(executor)
    premissa = executor.rodar(
        RegistrarPremissa,
        projeto_id=projeto_id,
        chave=ChaveDaAresta.D_C,
        texto="turma nova é turma improvisada",
    )
    for texto in ("formação prévia obrigatória", "convênio com universidade parceira"):
        executor.rodar(
            RegistrarInjecao, projeto_id=projeto_id, premissa_id=premissa.id, texto=texto
        )

    arquivadas = executor.rodar(
        ArquivarPremissa, projeto_id=projeto_id, premissa_id=premissa.id
    )

    span = [s for s in rastreador.spans if s.nome.endswith("arquivar_premissa")][-1]
    print(f"injeções arquivadas junto: {arquivadas}; span={span.atributos}")
    assert arquivadas == 2
    assert span.atributos["toc.injecoes_arquivadas"] == 2


def test_desafiar_premissa_sem_justificativa_e_recusado_e_a_recusa_vira_traco() -> None:
    executor, rastreador, _ = montar()
    projeto_id = nuvem_criada(executor)
    premissa = executor.rodar(
        RegistrarPremissa,
        projeto_id=projeto_id,
        chave=ChaveDaAresta.A_B,
        texto="sem receita nova não há instituição",
    )

    from toc_api.dominio.nuvem import PremissaInvalida

    with pytest.raises(PremissaInvalida):
        executor.rodar(
            DesafiarPremissa,
            projeto_id=projeto_id,
            premissa_id=premissa.id,
            justificativa="",
        )

    span = [s for s in rastreador.spans if s.nome.endswith("desafiar_premissa")][-1]
    print(f"span da recusa: {span.atributos}")
    assert span.atributos["toc.resultado"] == "erro"


def test_validar_nuvem_e_leitura_pura_e_devolve_completude() -> None:
    executor, _, _ = montar()
    projeto_id = nuvem_criada(executor)
    executor.rodar(
        RegistrarPremissa,
        projeto_id=projeto_id,
        chave=ChaveDaAresta.A_B,
        texto="sem receita nova não há instituição",
    )

    validacao = executor.rodar(ValidarNuvem, projeto_id=projeto_id)

    print(f"resumo da validação: {validacao.resumo()}")
    assert validacao.completude == (1, 7)


# --------------------------------------------------------------------------------------
# O encadeamento M2 → M3 como caso de uso
# --------------------------------------------------------------------------------------


def test_derivar_nuvem_de_udes_le_a_ara_e_grava_a_nuvem_com_a_origem() -> None:
    executor, rastreador, repositorio = montar()
    ara = novo_projeto_ara(
        id=uuid4(), dono=PLENA.dono(), nome="Realidade atual", em=AGORA
    )
    udes = []
    for enunciado in UDES_SINTETICOS:
        no = ara.adicionar_efeito(titulo=enunciado, em=AGORA)
        ara.marcar_ude(no.id, em=AGORA)
        udes.append(no.id)
    repositorio.salvar_ara(ara)

    nuvem = executor.rodar(
        DerivarNuvemDeUdes,
        projeto_id=ara.projeto.id,
        no_ids=tuple(udes),
        nome="Dilema da expansão",
    )

    gravada = repositorio.obter_nuvem(INQUILINO, nuvem.projeto.id)
    span = [s for s in rastreador.spans if s.nome.endswith("derivar_nuvem_de_udes")][-1]
    print(f"origem gravada: {gravada.origem}; span={span.atributos}")
    assert gravada.origem.projeto_id == ara.projeto.id
    assert gravada.origem.nos == tuple(udes)
    assert span.atributos["toc.udes_de_origem"] == len(udes)


def test_derivar_de_projeto_que_nao_e_ara_e_recusado_sem_criar_nada() -> None:
    executor, _, repositorio = montar()
    projeto_id = nuvem_criada(executor)  # um projeto NC, não uma ARA
    antes = len(repositorio.nuvens)

    from toc_api.dominio.erros import NaoEncontrado

    with pytest.raises(NaoEncontrado):
        executor.rodar(
            DerivarNuvemDeUdes, projeto_id=projeto_id, no_ids=(uuid4(),), nome="Dilema"
        )
    assert len(repositorio.nuvens) == antes


# --------------------------------------------------------------------------------------
# Geração assistida: porta, esquema e falha fechada
# --------------------------------------------------------------------------------------


def test_gerar_nuvem_por_narrativa_valida_o_esquema_e_nao_grava_nada() -> None:
    """RF-21/RF-23: gerar produz PROPOSTA de conteúdo; aplicar é outro ato."""
    motor = MotorDeGeracaoFalso(resultado=dict(BRUTO))
    executor, rastreador, repositorio = montar(motor=motor)
    projeto_id = nuvem_criada(executor)
    antes = repositorio.obter_nuvem(INQUILINO, projeto_id).texto(PapelDaEntidade.A)

    resultado = executor.rodar(
        GerarNuvemPorNarrativa, projeto_id=projeto_id, narrativa=NARRATIVA
    )

    depois = repositorio.obter_nuvem(INQUILINO, projeto_id).texto(PapelDaEntidade.A)
    span = [s for s in rastreador.spans if s.nome.endswith("gerar_nuvem_por_narrativa")][-1]
    print(f"resumo do resultado: {resultado.resumo()}; span={span.atributos}")
    assert isinstance(resultado, ResultadoDeGeracao)
    assert depois == antes, "gerar não aplica: a nuvem tem de continuar como estava"
    assert span.atributos["toc.premissas_propostas"] == resultado.total_de_premissas
    assert motor.chamadas[0][0] == "gerar_nuvem"


def test_resultado_torto_do_motor_e_recusado_antes_de_qualquer_efeito() -> None:
    """RF-22: falha fechada — e o traço registra a recusa (P5)."""
    motor = MotorDeGeracaoFalso(resultado={"versao": "1.0.0", "entidades": {}})
    executor, rastreador, repositorio = montar(motor=motor)
    projeto_id = nuvem_criada(executor)

    with pytest.raises(ResultadoDeGeracaoInvalido) as erro:
        executor.rodar(GerarNuvemPorNarrativa, projeto_id=projeto_id, narrativa=NARRATIVA)

    nuvem = repositorio.obter_nuvem(INQUILINO, projeto_id)
    span = [s for s in rastreador.spans if s.nome.endswith("gerar_nuvem_por_narrativa")][-1]
    print(f"recusa: {erro.value.codigo}; span={span.atributos}")
    assert span.atributos["toc.resultado"] == "erro"
    assert nuvem.premissas() == ()
    assert nuvem.texto(PapelDaEntidade.A).startswith("[A]")


def test_aplicar_geracao_exige_proposta_e_marca_a_origem_dos_eventos() -> None:
    """RF-25: mutação vinda de proposta aceita é distinguível de edição humana."""
    executor, rastreador, repositorio = montar()
    projeto_id = nuvem_criada(executor)
    resultado = ResultadoDeGeracao.de_dicionario(BRUTO)

    aplicada = executor.rodar(
        AplicarGeracaoDeNuvem,
        projeto_id=projeto_id,
        resultado=resultado,
        proposta_id="prop-0001",
    )

    nuvem = repositorio.obter_nuvem(INQUILINO, projeto_id)
    origens = {
        getattr(e, "origem", None) for e in nuvem.eventos if hasattr(e, "origem")
    }
    print(f"evento aplicado: {aplicada}; origens dos eventos: {origens}")
    assert nuvem.texto(PapelDaEntidade.A) == BRUTO["entidades"]["A"]
    assert nuvem.validar().completude == (7, 7)
    assert origens == {"geracao"}
    span = [s for s in rastreador.spans if s.nome.endswith("aplicar_geracao_de_nuvem")][-1]
    assert span.atributos["toc.proposta_id"] == "prop-0001"


def test_sugestoes_granulares_nao_tocam_o_que_ja_existe() -> None:
    """US-13/RF-26: refinar uma aresta não regenera a nuvem que o grupo validou."""
    motor = MotorDeGeracaoFalso(
        premissas=({"texto": "as duas ações disputam a mesma equipe"},),
        injecoes=({"texto": "turno noturno para a segunda cidade", "separacao": "tempo"},),
    )
    executor, _, repositorio = montar(motor=motor)
    projeto_id = nuvem_criada(executor)
    existente = executor.rodar(
        RegistrarPremissa,
        projeto_id=projeto_id,
        chave=ChaveDaAresta.D_D_PRIME,
        texto="não há orçamento para as duas ações",
    )

    premissas = executor.rodar(
        SugerirPremissas, projeto_id=projeto_id, chave=ChaveDaAresta.D_D_PRIME
    )
    injecoes = executor.rodar(
        SugerirInjecoes, projeto_id=projeto_id, premissa_id=existente.id
    )

    nuvem = repositorio.obter_nuvem(INQUILINO, projeto_id)
    print(f"sugestões: {len(premissas)} premissa(s), {len(injecoes)} injeção(ões)")
    assert [p.texto for p in premissas] == ["as duas ações disputam a mesma equipe"]
    assert injecoes[0].separacao is SeparacaoTRIZ.TEMPO
    # Sugerir é rascunho: nada entra no agregado sem proposta aceita (RN-05).
    assert [p.texto for p in nuvem.premissas(ChaveDaAresta.D_D_PRIME)] == [
        "não há orçamento para as duas ações"
    ]


def test_sem_motor_composto_a_geracao_falha_alto_e_nao_finge() -> None:
    executor, _, _ = montar(motor=None)
    projeto_id = nuvem_criada(executor)

    with pytest.raises(RuntimeError):
        executor.rodar(GerarNuvemPorNarrativa, projeto_id=projeto_id, narrativa=NARRATIVA)


# --------------------------------------------------------------------------------------
# Autorização — no caso de uso, nunca na rota (§B.7.2)
# --------------------------------------------------------------------------------------


def test_quem_so_le_alcanca_a_leitura_da_nuvem_e_e_recusado_em_toda_mutacao() -> None:
    executor, _, repositorio = montar()
    projeto_id = nuvem_criada(executor)
    leitor = Executor(
        principal=SO_LE,
        rastreador=RastreadorFalso(),
        repositorio=repositorio,
        relogio=RelogioFalso(instante=AGORA),
    )

    aberta = leitor.rodar(AbrirProjetoNC, projeto_id=projeto_id)
    assert aberta.projeto.id == projeto_id

    mutadoras = (
        (CriarProjetoNC, {"nome": "outra"}),
        (EditarEntidadeDaNuvem, {"projeto_id": projeto_id, "papel": PapelDaEntidade.A, "texto": "x"}),
        (RegistrarPremissa, {"projeto_id": projeto_id, "chave": ChaveDaAresta.A_B, "texto": "y"}),
        (GerarNuvemPorNarrativa, {"projeto_id": projeto_id, "narrativa": NARRATIVA}),
        (SugerirPremissas, {"projeto_id": projeto_id, "chave": ChaveDaAresta.A_B}),
        (AplicarGeracaoDeNuvem, {"projeto_id": projeto_id, "resultado": None, "proposta_id": "p"}),
        (DerivarNuvemDeUdes, {"projeto_id": projeto_id, "no_ids": (), "nome": "z"}),
    )
    negadas = []
    for classe, argumentos in mutadoras:
        with pytest.raises(AutorizacaoNegada):
            leitor.rodar(classe, **argumentos)
        negadas.append(classe.nome)

    print(f"mutadoras do M3 recusadas para quem só lê: {len(negadas)} → {negadas}")
    assert len(negadas) == len(mutadoras)
