"""M2 — a Árvore da Realidade Atual (ARA) sobre o núcleo do M1 (spec 005).

O M2 **estende por composição**: o núcleo não ganhou uma linha de semântica da Teoria das
Restrições (TOC) — a RN-04 da spec 004 é justamente essa fronteira, e é ela que impede a
sétima cópia de canvas. Aqui moram o marcador de Efeito Indesejável (UDE), a ficha, a
máquina de estados do status, o parecer de julgamento, o exame de suficiência do elo e o
conector E.

Testes puros: sem rede, sem banco, sem modelo.
"""
from datetime import datetime, timezone
from uuid import uuid4

import pytest

from toc_api.dominio.ara import (
    FERRAMENTA_ARA,
    ConectorInvalido,
    EstadoDoExame,
    FichaDeUde,
    OrigemDoParecer,
    ParecerDeJulgamento,
    ProjetoARA,
    StatusDeValidacao,
    TransicaoDeStatusRecusada,
    novo_projeto_ara,
)
from toc_api.dominio.criterios_ude import Veredito
from toc_api.dominio.erros import MutacaoRecusada
from toc_api.dominio.identidade import DonoDoProjeto

DONO = DonoDoProjeto(inquilino_id="inq-horizonte", usuario_id="usr-facilitadora")
T0 = datetime(2026, 9, 5, 12, 0, tzinfo=timezone.utc)
T1 = datetime(2026, 9, 5, 13, 0, tzinfo=timezone.utc)

BOM = "A taxa de conclusão dos cursos técnicos é de 54%."
RUIM = "Falta um sistema integrado de matrícula na secretaria."


def nova_ara() -> ProjetoARA:
    return novo_projeto_ara(
        id=uuid4(), dono=DONO, nome="Instituição Horizonte — ARA da evasão", em=T0
    )


def parecer_humano(favoravel: bool = True) -> ParecerDeJulgamento:
    return ParecerDeJulgamento(
        autor="papel:facilitadora",
        origem=OrigemDoParecer.HUMANO,
        favoravel=favoravel,
        justificativa="a queixa é contínua e está na esfera da coordenação",
        instante=T1,
    )


# -- o tipo de projeto -------------------------------------------------------------------


def test_projeto_ara_e_um_projeto_do_m1_com_a_ferramenta_declarada():
    ara = nova_ara()
    assert ara.projeto.ferramenta == FERRAMENTA_ARA
    no = ara.adicionar_efeito(titulo=BOM, em=T0)
    assert ara.projeto.no(no.id).titulo == BOM


def test_um_projeto_generico_nao_vira_ara_por_engano():
    from toc_api.dominio.projeto import Projeto

    generico = Projeto(id=uuid4(), dono=DONO, nome="genérico", criado_em=T0, alterado_em=T0)
    with pytest.raises(MutacaoRecusada):
        ProjetoARA(generico)


# -- marcar UDE e ficha ------------------------------------------------------------------


def test_marcar_ude_guarda_a_ficha_e_valida_formalmente_de_imediato():
    ara = nova_ara()
    no = ara.adicionar_efeito(titulo=BOM, em=T0)
    ara.marcar_ude(
        no.id,
        ficha=FichaDeUde(area_impactada="Secretaria", evidencias=("relatório interno",)),
        em=T0,
    )
    assert ara.e_ude(no.id) is True
    assert ara.ficha(no.id).area_impactada == "Secretaria"
    assert ara.validacao(no.id).aprovado_nos_decidiveis is True
    assert ara.status(no.id) is StatusDeValidacao.PENDENTE
    assert [type(e).__name__ for e in ara.eventos[-2:]] == [
        "UdeMarcado",
        "ValidacaoFormalExecutada",
    ]


def test_marcar_ude_de_texto_mal_formulado_cai_em_requer_refinamento():
    ara = nova_ara()
    no = ara.adicionar_efeito(titulo=RUIM, em=T0)
    ara.marcar_ude(no.id, em=T0)
    assert ara.validacao(no.id).aprovado_nos_decidiveis is False
    assert ara.status(no.id) is StatusDeValidacao.REQUER_REFINAMENTO


def test_desmarcar_ude_apaga_o_marcador_mas_nao_o_no():
    ara = nova_ara()
    no = ara.adicionar_efeito(titulo=BOM, em=T0)
    ara.marcar_ude(no.id, em=T0)
    ara.desmarcar_ude(no.id, em=T1)
    assert ara.e_ude(no.id) is False
    assert ara.projeto.no(no.id).titulo == BOM


def test_editar_o_texto_reexecuta_a_validacao_e_o_evento_guarda_os_dois():
    """RF-10: mudou o texto, o veredito anterior é invalidado — não fica pendurado."""
    ara = nova_ara()
    no = ara.adicionar_efeito(titulo=RUIM, em=T0)
    ara.marcar_ude(no.id, em=T0)
    assert ara.validacao(no.id).aprovado_nos_decidiveis is False

    ara.reformular(no.id, BOM, em=T1)

    assert ara.validacao(no.id).aprovado_nos_decidiveis is True
    evento = [e for e in ara.eventos if type(e).__name__ == "ValidacaoFormalExecutada"][-1]
    assert evento.texto_anterior == RUIM
    assert evento.texto == BOM


# -- FSM de status (RN-10) ---------------------------------------------------------------


def test_validado_e_recusado_enquanto_houver_criterio_decidivel_vermelho():
    ara = nova_ara()
    no = ara.adicionar_efeito(titulo=RUIM, em=T0)
    ara.marcar_ude(no.id, em=T0)
    ara.registrar_parecer(no.id, parecer_humano(), em=T1)
    with pytest.raises(TransicaoDeStatusRecusada) as erro:
        ara.mudar_status(no.id, StatusDeValidacao.VALIDADO, em=T1)
    assert "decidivel" in erro.value.motivo


def test_validado_e_recusado_sem_parecer_humano_confirmado():
    ara = nova_ara()
    no = ara.adicionar_efeito(titulo=BOM, em=T0)
    ara.marcar_ude(no.id, em=T0)
    with pytest.raises(TransicaoDeStatusRecusada) as erro:
        ara.mudar_status(no.id, StatusDeValidacao.VALIDADO, em=T1)
    assert "parecer" in erro.value.motivo


def test_parecer_de_ia_sozinho_nunca_fecha_o_status():
    """RN-10 em letras: "parecer de IA nunca fecha status sozinho"."""
    ara = nova_ara()
    no = ara.adicionar_efeito(titulo=BOM, em=T0)
    ara.marcar_ude(no.id, em=T0)
    ara.registrar_parecer(
        no.id,
        ParecerDeJulgamento(
            autor="acao:toc.validate_ude",
            origem=OrigemDoParecer.CATALOGO,
            favoravel=True,
            justificativa="parece contínuo e acionável",
            instante=T1,
            proposta_id="prop-001",
        ),
        em=T1,
    )
    with pytest.raises(TransicaoDeStatusRecusada):
        ara.mudar_status(no.id, StatusDeValidacao.VALIDADO, em=T1)


def test_validado_com_decidiveis_verdes_e_parecer_humano_favoravel():
    ara = nova_ara()
    no = ara.adicionar_efeito(titulo=BOM, em=T0)
    ara.marcar_ude(no.id, em=T0)
    ara.registrar_parecer(no.id, parecer_humano(), em=T1)
    ara.mudar_status(no.id, StatusDeValidacao.VALIDADO, em=T1)
    assert ara.status(no.id) is StatusDeValidacao.VALIDADO
    evento = ara.eventos[-1]
    assert type(evento).__name__ == "StatusDeValidacaoMudou"
    assert evento.de is StatusDeValidacao.PENDENTE and evento.para is StatusDeValidacao.VALIDADO


def test_pareceres_se_acumulam_e_nunca_se_sobrescrevem():
    """RF-13: "pareceres se acumulam, nunca se sobrescrevem"."""
    ara = nova_ara()
    no = ara.adicionar_efeito(titulo=BOM, em=T0)
    ara.marcar_ude(no.id, em=T0)
    ara.registrar_parecer(no.id, parecer_humano(favoravel=False), em=T0)
    ara.registrar_parecer(no.id, parecer_humano(favoravel=True), em=T1)
    assert len(ara.pareceres(no.id)) == 2
    assert [p.favoravel for p in ara.pareceres(no.id)] == [False, True]


def test_reabrir_validado_exige_justificativa_e_registra_o_motivo():
    """RF-17: reabrir é ação explícita, com motivo no evento."""
    ara = nova_ara()
    no = ara.adicionar_efeito(titulo=BOM, em=T0)
    ara.marcar_ude(no.id, em=T0)
    ara.registrar_parecer(no.id, parecer_humano(), em=T1)
    ara.mudar_status(no.id, StatusDeValidacao.VALIDADO, em=T1)

    with pytest.raises(TransicaoDeStatusRecusada):
        ara.mudar_status(no.id, StatusDeValidacao.REQUER_REFINAMENTO, em=T1)

    ara.mudar_status(
        no.id, StatusDeValidacao.REQUER_REFINAMENTO, em=T1,
        justificativa="a evidência não sustenta o número",
    )
    assert ara.status(no.id) is StatusDeValidacao.REQUER_REFINAMENTO
    assert ara.eventos[-1].justificativa == "a evidência não sustenta o número"


def test_resumo_por_status_conta_os_udes(capsys):
    ara = nova_ara()
    for texto in (BOM, "O índice de presença nas aulas práticas é de 58%.", RUIM):
        no = ara.adicionar_efeito(titulo=texto, em=T0)
        ara.marcar_ude(no.id, em=T0)
    resumo = ara.resumo_por_status()
    assert resumo[StatusDeValidacao.PENDENTE] == 2
    assert resumo[StatusDeValidacao.REQUER_REFINAMENTO] == 1
    assert sum(resumo.values()) == 3


# -- exame de suficiência do elo -----------------------------------------------------------


def test_elo_nasce_nao_examinado_e_o_exame_e_dado_de_primeira_classe():
    ara = nova_ara()
    causa = ara.adicionar_efeito(titulo="Os formulários chegam incompletos.", em=T0)
    efeito = ara.adicionar_efeito(titulo=BOM, em=T0)
    elo = ara.ligar(causa.id, efeito.id, em=T0)
    assert ara.exame(elo.id).estado is EstadoDoExame.NAO_EXAMINADO

    ara.examinar_elo(elo.id, EstadoDoExame.SUFICIENTE, em=T1)
    assert ara.exame(elo.id).estado is EstadoDoExame.SUFICIENTE
    assert type(ara.eventos[-1]).__name__ == "EloExaminado"


@pytest.mark.parametrize(
    "estado", [EstadoDoExame.INSUFICIENTE, EstadoDoExame.COM_RESERVA]
)
def test_insuficiente_e_com_reserva_exigem_a_reserva_escrita(estado):
    """RF-22: "com texto de reserva obrigatório nos dois últimos"."""
    ara = nova_ara()
    causa = ara.adicionar_efeito(titulo="Os formulários chegam incompletos.", em=T0)
    efeito = ara.adicionar_efeito(titulo=BOM, em=T0)
    elo = ara.ligar(causa.id, efeito.id, em=T0)
    with pytest.raises(MutacaoRecusada):
        ara.examinar_elo(elo.id, estado, em=T1)
    ara.examinar_elo(
        elo.id, estado, reserva="a causa sozinha não produz o efeito", em=T1
    )
    assert ara.exame(elo.id).reserva == "a causa sozinha não produz o efeito"


def test_leitura_de_suficiencia_e_montada_dos_textos_atuais(capsys):
    """RF-19: "Se <origem>, então <destino>", montada dos textos ATUAIS dos nós."""
    ara = nova_ara()
    causa = ara.adicionar_efeito(titulo="Os formulários chegam incompletos.", em=T0)
    efeito = ara.adicionar_efeito(titulo=BOM, em=T0)
    elo = ara.ligar(causa.id, efeito.id, em=T0)
    assert ara.leitura_do_elo(elo.id) == (
        "Se Os formulários chegam incompletos., então A taxa de conclusão dos cursos "
        "técnicos é de 54%."
    )
    ara.reformular(causa.id, "A conferência manual leva 3 dias.", em=T1)
    assert "A conferência manual leva 3 dias." in ara.leitura_do_elo(elo.id)


# -- conector E ---------------------------------------------------------------------------


def test_conector_e_agrupa_arestas_do_mesmo_destino_e_le_em_conjuncao():
    ara = nova_ara()
    a = ara.adicionar_efeito(titulo="Os formulários chegam incompletos.", em=T0)
    b = ara.adicionar_efeito(titulo="O volume de pedidos dobra em janeiro.", em=T0)
    c = ara.adicionar_efeito(titulo=BOM, em=T0)
    e1 = ara.ligar(a.id, c.id, em=T0)
    e2 = ara.ligar(b.id, c.id, em=T0)

    conector = ara.formar_conector_e((e1.id, e2.id), em=T1)

    assert conector.destino_id == c.id
    assert set(conector.arestas) == {e1.id, e2.id}
    leitura = ara.leitura_do_conector(conector.id)
    assert " e " in leitura and leitura.startswith("Se ")
    assert type(ara.eventos[-1]).__name__ == "ConectorEFormado"


def test_conector_e_recusa_arestas_de_destinos_diferentes():
    """RN-11: "toda aresta de um conector aponta para o mesmo destino"."""
    ara = nova_ara()
    a = ara.adicionar_efeito(titulo="Os formulários chegam incompletos.", em=T0)
    b = ara.adicionar_efeito(titulo="O volume de pedidos dobra em janeiro.", em=T0)
    c = ara.adicionar_efeito(titulo=BOM, em=T0)
    e1 = ara.ligar(a.id, c.id, em=T0)
    e2 = ara.ligar(a.id, b.id, em=T0)
    with pytest.raises(ConectorInvalido) as erro:
        ara.formar_conector_e((e1.id, e2.id), em=T1)
    assert erro.value.regra == "destino_unico"


def test_conector_e_exige_ao_menos_duas_arestas():
    ara = nova_ara()
    a = ara.adicionar_efeito(titulo="Os formulários chegam incompletos.", em=T0)
    c = ara.adicionar_efeito(titulo=BOM, em=T0)
    e1 = ara.ligar(a.id, c.id, em=T0)
    with pytest.raises(ConectorInvalido) as erro:
        ara.formar_conector_e((e1.id,), em=T1)
    assert erro.value.regra == "minimo_duas_arestas"


def test_uma_aresta_pertence_a_no_maximo_um_conector_por_destino():
    ara = nova_ara()
    a = ara.adicionar_efeito(titulo="Os formulários chegam incompletos.", em=T0)
    b = ara.adicionar_efeito(titulo="O volume de pedidos dobra em janeiro.", em=T0)
    d = ara.adicionar_efeito(titulo="A conferência manual leva 3 dias.", em=T0)
    c = ara.adicionar_efeito(titulo=BOM, em=T0)
    e1 = ara.ligar(a.id, c.id, em=T0)
    e2 = ara.ligar(b.id, c.id, em=T0)
    e3 = ara.ligar(d.id, c.id, em=T0)
    ara.formar_conector_e((e1.id, e2.id), em=T1)
    with pytest.raises(ConectorInvalido) as erro:
        ara.formar_conector_e((e2.id, e3.id), em=T1)
    assert erro.value.regra == "aresta_ja_conectada"


def test_desfazer_conector_solta_as_arestas():
    ara = nova_ara()
    a = ara.adicionar_efeito(titulo="Os formulários chegam incompletos.", em=T0)
    b = ara.adicionar_efeito(titulo="O volume de pedidos dobra em janeiro.", em=T0)
    c = ara.adicionar_efeito(titulo=BOM, em=T0)
    e1 = ara.ligar(a.id, c.id, em=T0)
    e2 = ara.ligar(b.id, c.id, em=T0)
    conector = ara.formar_conector_e((e1.id, e2.id), em=T1)
    ara.desfazer_conector_e(conector.id, em=T1)
    assert ara.conectores == ()
    assert type(ara.eventos[-1]).__name__ == "ConectorEDesfeito"


# -- exclusão do nó marcado ---------------------------------------------------------------


def test_excluir_no_marcado_arquiva_ficha_e_pareceres_no_evento():
    """RF-05: a ficha e os pareceres vão para o evento — a restauração devolve tudo."""
    ara = nova_ara()
    no = ara.adicionar_efeito(titulo=BOM, em=T0)
    ara.marcar_ude(no.id, ficha=FichaDeUde(area_impactada="Secretaria"), em=T0)
    ara.registrar_parecer(no.id, parecer_humano(), em=T1)

    ara.excluir_no(no.id, em=T1)

    assert ara.e_ude(no.id) is False
    arquivo = [e for e in ara.eventos if type(e).__name__ == "UdeArquivado"][-1]
    assert arquivo.ficha.area_impactada == "Secretaria"
    assert len(arquivo.pareceres) == 1


def test_a_validacao_guardada_e_a_mesma_funcao_pura_do_dominio():
    """Nada de veredito vindo de fora: o que a ficha exibe é a função, byte a byte."""
    from toc_api.dominio.criterios_ude import validar_formalmente

    ara = nova_ara()
    no = ara.adicionar_efeito(titulo=RUIM, em=T0)
    ara.marcar_ude(no.id, em=T0)
    assert ara.validacao(no.id) == validar_formalmente(RUIM)
    assert ara.validacao(no.id).veredito_de("CD-5").veredito is Veredito.NAO_ATENDE
