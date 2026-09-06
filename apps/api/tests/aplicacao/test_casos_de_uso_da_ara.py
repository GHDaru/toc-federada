"""Casos de uso da Árvore da Realidade Atual (ARA, M2) — sobre as portas, com duplos.

O caso de uso que mais importa aqui é `ValidarTextoDeUde`: ele **não toca repositório
nenhum**, porque a validação formal de um Efeito Indesejável (UDE) é função pura de
domínio. Na linhagem, a mesma operação custava uma chamada de rede a um provedor de
modelo de linguagem a partir do navegador (`tocbuilderv3/services/geminiService.ts:16`).
A assinatura deste caso de uso é a prova de que a dependência sumiu.
"""
from datetime import datetime, timezone

import pytest

from toc_api.aplicacao.ara import (
    AdicionarEfeito,
    AnalisarArvore,
    CriarProjetoARA,
    ExaminarElo,
    LigarNaARA,
    MarcarUde,
    MudarStatusDeUde,
    RegistrarParecer,
    ReformularUde,
    ValidarTextoDeUde,
)
from toc_api.dominio.ara import (
    EstadoDoExame,
    FichaDeUde,
    OrigemDoParecer,
    ParecerDeJulgamento,
    StatusDeValidacao,
    TransicaoDeStatusRecusada,
)
from toc_api.dominio.identidade import DonoDoProjeto

from .fakes import RastreadorFalso, RelogioFalso, RepositorioDeARAFalso

DONO = DonoDoProjeto(inquilino_id="inq-horizonte", usuario_id="usr-facilitadora")
INTRUSA = DonoDoProjeto(inquilino_id="inq-outra", usuario_id="usr-outra")
T0 = datetime(2026, 9, 5, 12, 0, tzinfo=timezone.utc)

BOM = "A taxa de conclusão dos cursos técnicos é de 54%."
RUIM = "Falta um sistema integrado de matrícula na secretaria."


@pytest.fixture()
def cenario():
    pecas = dict(
        rastreador=RastreadorFalso(),
        repositorio=RepositorioDeARAFalso(),
        relogio=RelogioFalso(instante=T0),
    )
    projeto = CriarProjetoARA(**pecas).rodar(dono=DONO, nome="Horizonte — ARA da evasão")
    return pecas, pecas["rastreador"], projeto


def test_validar_texto_de_ude_nao_precisa_de_repositorio_nem_de_rede():
    """A correção do defeito D-08 aparece na ASSINATURA, não só na implementação."""
    rastreador = RastreadorFalso()
    caso = ValidarTextoDeUde(rastreador=rastreador)
    validacao = caso.rodar(dono=DONO, texto="Falta de treinamento causa erros.")
    assert validacao.aprovado_nos_decidiveis is False
    assert validacao.veredito_de("CD-7").trecho == "causa"
    span = rastreador.spans[-1]
    assert span.nome == "caso_de_uso.validar_texto_de_ude"
    assert span.atributos["toc.criterios_reprovados"] == 1
    assert "texto" not in str(span.atributos)


def test_criar_projeto_ara_nasce_com_a_ferramenta_certa(cenario):
    pecas, _, projeto = cenario
    guardado = pecas["repositorio"].obter(DONO.inquilino_id, projeto.id)
    assert guardado.ferramenta == "ara"


def test_marcar_ude_valida_de_imediato_e_persiste_o_status(cenario):
    pecas, rastreador, projeto = cenario
    no = AdicionarEfeito(**pecas).rodar(dono=DONO, projeto_id=projeto.id, titulo=RUIM)
    ficha = MarcarUde(**pecas).rodar(
        dono=DONO,
        projeto_id=projeto.id,
        no_id=no.id,
        ficha=FichaDeUde(area_impactada="Secretaria"),
    )
    assert ficha.area_impactada == "Secretaria"
    span = rastreador.spans[-1]
    assert span.atributos["toc.status_do_ude"] == StatusDeValidacao.REQUER_REFINAMENTO.value
    assert span.atributos["toc.criterios_reprovados"] == 1


def test_reformular_reexecuta_a_validacao_e_libera_o_caminho_do_validado(cenario):
    pecas, _, projeto = cenario
    no = AdicionarEfeito(**pecas).rodar(dono=DONO, projeto_id=projeto.id, titulo=RUIM)
    MarcarUde(**pecas).rodar(dono=DONO, projeto_id=projeto.id, no_id=no.id)

    with pytest.raises(TransicaoDeStatusRecusada):
        MudarStatusDeUde(**pecas).rodar(
            dono=DONO, projeto_id=projeto.id, no_id=no.id,
            status=StatusDeValidacao.VALIDADO,
        )

    ReformularUde(**pecas).rodar(
        dono=DONO, projeto_id=projeto.id, no_id=no.id, texto=BOM
    )
    RegistrarParecer(**pecas).rodar(
        dono=DONO,
        projeto_id=projeto.id,
        no_id=no.id,
        parecer=ParecerDeJulgamento(
            autor="papel:facilitadora",
            origem=OrigemDoParecer.HUMANO,
            favoravel=True,
            justificativa="queixa contínua, dentro da esfera da coordenação",
            instante=T0,
        ),
    )
    status = MudarStatusDeUde(**pecas).rodar(
        dono=DONO, projeto_id=projeto.id, no_id=no.id, status=StatusDeValidacao.VALIDADO
    )
    assert status is StatusDeValidacao.VALIDADO


def test_a_ara_persistida_reabre_com_ficha_status_e_exame(cenario):
    """RF-05 da spec 004 aplicado ao M2: reabrir devolve o que foi gravado."""
    pecas, _, projeto = cenario
    causa = AdicionarEfeito(**pecas).rodar(
        dono=DONO, projeto_id=projeto.id, titulo="Os formulários chegam incompletos."
    )
    efeito = AdicionarEfeito(**pecas).rodar(dono=DONO, projeto_id=projeto.id, titulo=BOM)
    elo = LigarNaARA(**pecas).rodar(
        dono=DONO, projeto_id=projeto.id, origem_id=causa.id, destino_id=efeito.id
    )
    MarcarUde(**pecas).rodar(dono=DONO, projeto_id=projeto.id, no_id=efeito.id)
    ExaminarElo(**pecas).rodar(
        dono=DONO,
        projeto_id=projeto.id,
        aresta_id=elo.id,
        estado=EstadoDoExame.COM_RESERVA,
        reserva="falta a condição de volume",
    )

    reaberta = pecas["repositorio"].obter_ara(DONO.inquilino_id, projeto.id)
    assert reaberta.e_ude(efeito.id) is True
    assert reaberta.status(efeito.id) is StatusDeValidacao.PENDENTE
    assert reaberta.exame(elo.id).estado is EstadoDoExame.COM_RESERVA
    assert reaberta.exame(elo.id).reserva == "falta a condição de volume"


def test_analisar_arvore_e_leitura_e_leva_o_resumo_para_o_traco(cenario):
    pecas, rastreador, projeto = cenario
    adicionar, ligar = AdicionarEfeito(**pecas), LigarNaARA(**pecas)
    raiz = adicionar.rodar(
        dono=DONO, projeto_id=projeto.id, titulo="A conferência de matrícula é manual."
    )
    ude = adicionar.rodar(dono=DONO, projeto_id=projeto.id, titulo=BOM)
    ligar.rodar(dono=DONO, projeto_id=projeto.id, origem_id=raiz.id, destino_id=ude.id)
    MarcarUde(**pecas).rodar(dono=DONO, projeto_id=projeto.id, no_id=ude.id)

    relatorio = AnalisarArvore(**pecas).rodar(dono=DONO, projeto_id=projeto.id)

    assert relatorio.causa_raiz_candidata == raiz.id
    span = rastreador.spans[-1]
    assert span.atributos["toc.nos"] == 2
    assert span.atributos["toc.udes"] == 1
    assert span.atributos["toc.causas_raiz_candidatas"] == 1


def test_a_ara_de_outro_inquilino_nao_e_alcancavel(cenario):
    from toc_api.dominio.erros import NaoEncontrado

    pecas, _, projeto = cenario
    with pytest.raises(NaoEncontrado):
        AnalisarArvore(**pecas).rodar(dono=INTRUSA, projeto_id=projeto.id)
