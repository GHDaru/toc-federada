"""M4 · E4.1 — a Árvore da Realidade Futura (ARF): injeção → efeito futuro → ramo negativo.

Siglas, uma vez neste arquivo: **TOC** — Teoria das Restrições · **ARA** — Árvore da
Realidade Atual · **UDE** — Efeito Indesejável · **NC** — Nuvem de Conflito · **ARF** —
Árvore da Realidade Futura · **ED** — Efeito Desejável · **M1** — Núcleo de Diagramas
Lógicos · **RF/RN** — requisito funcional / regra de negócio da spec 008.

**Esta ferramenta nunca existiu.** Nas quatro gerações do TOC-Builder a ARF foi item de
menu desabilitado — `tocbuilderv3/components/Sidebar.tsx:55` (`view: 'ARF', disabled:
true`) e `types.ts:249-258` (o tipo de navegação sem nada atrás). Zero componentes, zero
prompts, zero linhas de domínio. Tudo o que estes testes fixam é 🟡 por construção.

O que separa uma árvore de futuro séria de uma lista de desejos é o **ramo negativo**: o
efeito indevido que a própria injeção traz, marcado, e tratado por uma injeção de corte ou
aceito com justificativa (RN-04). Por isso ele tem mais testes que qualquer outra parte
deste arquivo.

Base sintética (ADR 0006): "Instituição Horizonte" e personas fictícias.
"""
from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID, uuid4

import pytest

from toc_api.dominio.arf import (
    FERRAMENTA_ARF,
    EspelhoInvalido,
    EstadoDoRamo,
    PapelNaARF,
    PapelNaArfInvalido,
    ProjetoARF,
    RamoNegativoInvalido,
    novo_projeto_arf,
    reidratar_arf,
)
from toc_api.dominio.erros import MutacaoForaDaRaiz, MutacaoRecusada, NaoEncontrado
from toc_api.dominio.eventos import (
    EfeitoEspelhouUde,
    RamoNegativoAceito,
    RamoNegativoMarcado,
    RamoNegativoReaberto,
    RamoNegativoTratado,
    VerificacaoDaArfGerada,
)
from toc_api.dominio.identidade import DonoDoProjeto
from toc_api.dominio.projeto import Projeto
from toc_api.dominio.suficiencia import EstadoDoExame

AGORA = datetime(2026, 9, 6, 10, 0, tzinfo=timezone.utc)
DONO = DonoDoProjeto(inquilino_id="instituicao-horizonte", usuario_id="u-facilitadora")
ID_DA_ARF = UUID("44444444-4444-4444-8444-444444444401")
UDE_UM = UUID("11111111-1111-4111-8111-111111111101")
UDE_DOIS = UUID("11111111-1111-4111-8111-111111111102")
ID_DA_ARA = UUID("55555555-5555-4555-8555-555555555551")

INJECAO = "faseamento orçamentário condicionado a marco de receita"
EFEITO = "as duas frentes recebem verba no trimestre"
EFEITO_COLATERAL = "a equipe da Secretaria acumula dupla jornada"
CORTE = "contratação temporária no pico"


def arf_semeada(udes: tuple[UUID, ...] = (UDE_UM, UDE_DOIS)) -> ProjetoARF:
    """Uma ARF com a cadeia vinculada — o caso normal, porque ela nasce de uma injeção."""
    arf = novo_projeto_arf(
        id=ID_DA_ARF,
        dono=DONO,
        nome="Realidade futura da Instituição Horizonte",
        em=AGORA,
        udes_da_cadeia=udes,
    )
    arf.drenar_eventos()
    return arf


# --------------------------------------------------------------------------------------
# F4.1.1 — o projeto ARF sobre o núcleo, com papéis tipados
# --------------------------------------------------------------------------------------


def test_a_arf_nasce_vazia_com_a_ferramenta_propria() -> None:
    arf = novo_projeto_arf(id=ID_DA_ARF, dono=DONO, nome="Futuro", em=AGORA)
    print(f"ferramenta={arf.projeto.ferramenta!r} nós={len(arf.nos)} arestas={len(arf.arestas)}")
    assert arf.projeto.ferramenta == FERRAMENTA_ARF
    assert (len(arf.nos), len(arf.arestas)) == (0, 0)


def test_o_projeto_da_arf_recusa_mutacao_que_nao_venha_pela_raiz() -> None:
    """O defeito da porta dos fundos, fechado por construção também aqui."""
    arf = arf_semeada()
    with pytest.raises(MutacaoForaDaRaiz) as erro:
        arf.projeto.adicionar_no(titulo="por fora", em=AGORA)
    print(f"recusa: ferramenta={erro.value.ferramenta!r} raiz={erro.value.raiz!r}")
    assert erro.value.ferramenta == FERRAMENTA_ARF
    assert erro.value.raiz == "ProjetoARF"


def test_a_arf_exige_a_ferramenta_certa_no_projeto_contido() -> None:
    generico = Projeto(id=uuid4(), dono=DONO, nome="genérico", criado_em=AGORA, alterado_em=AGORA)
    with pytest.raises(MutacaoRecusada):
        ProjetoARF(projeto=generico)


def test_cada_no_nasce_com_o_papel_visivel_no_tipo_do_no() -> None:
    """RF-02: injeção e efeito futuro são papéis distintos, gravados no `tipo` do nó do M1."""
    arf = arf_semeada()
    injecao = arf.adicionar_injecao(titulo=INJECAO, em=AGORA)
    efeito = arf.adicionar_efeito_futuro(titulo=EFEITO, em=AGORA)

    print(f"tipos: injeção={injecao.tipo!r} efeito={efeito.tipo!r}")
    assert arf.papel_do_no(injecao.id) is PapelNaARF.INJECAO
    assert arf.papel_do_no(efeito.id) is PapelNaARF.EFEITO_FUTURO
    assert injecao.tipo != efeito.tipo


def test_a_aresta_da_arf_se_le_por_suficiencia_e_nasce_com_exame() -> None:
    """RF-03: "Se a injeção, então o efeito", com o exame de elo herdado da ARA."""
    arf = arf_semeada()
    injecao = arf.adicionar_injecao(titulo=INJECAO, em=AGORA)
    efeito = arf.adicionar_efeito_futuro(titulo=EFEITO, em=AGORA)

    elo = arf.ligar(injecao.id, efeito.id, em=AGORA)

    print(f"leitura: {arf.leitura_do_elo(elo.id)}")
    assert arf.leitura_do_elo(elo.id) == f"Se {INJECAO}, então {EFEITO}"
    assert arf.exame(elo.id).estado is EstadoDoExame.NAO_EXAMINADO
    arf.examinar_elo(elo.id, EstadoDoExame.SUFICIENTE, em=AGORA)
    assert arf.exame(elo.id).estado is EstadoDoExame.SUFICIENTE


def test_o_conector_e_da_arf_e_o_mesmo_da_ara() -> None:
    """RF-03: conjunção "Se A e B, então C" — do pacote compartilhado, sem cópia."""
    arf = arf_semeada()
    uma = arf.adicionar_injecao(titulo=INJECAO, em=AGORA)
    outra = arf.adicionar_injecao(titulo="calendário unificado de compras", em=AGORA)
    efeito = arf.adicionar_efeito_futuro(titulo=EFEITO, em=AGORA)
    elo_um = arf.ligar(uma.id, efeito.id, em=AGORA)
    elo_dois = arf.ligar(outra.id, efeito.id, em=AGORA)

    conector = arf.formar_conector_e((elo_um.id, elo_dois.id), em=AGORA)

    print(f"conjunção: {arf.leitura_do_conector(conector.id)}")
    assert arf.leitura_do_conector(conector.id) == (
        f"Se {INJECAO} e calendário unificado de compras, então {EFEITO}"
    )


def test_mudar_o_papel_de_um_no_e_permitido_enquanto_nao_ha_vinculo_que_proiba() -> None:
    """RF-02: o papel muda — até a injeção estar cortando um ramo tratado."""
    arf = arf_semeada()
    no = arf.adicionar_efeito_futuro(titulo=EFEITO, em=AGORA)

    arf.mudar_papel(no.id, PapelNaARF.INJECAO, em=AGORA)

    assert arf.papel_do_no(no.id) is PapelNaARF.INJECAO


def test_injecao_que_trata_ramo_nao_vira_efeito() -> None:
    """RF-02, a proibição nomeada: o corte de um ramo tratado não deixa de ser injeção."""
    arf = arf_semeada()
    injecao = arf.adicionar_injecao(titulo=INJECAO, em=AGORA)
    colateral = arf.adicionar_efeito_futuro(titulo=EFEITO_COLATERAL, em=AGORA)
    arf.ligar(injecao.id, colateral.id, em=AGORA)
    corte = arf.adicionar_injecao(titulo=CORTE, em=AGORA)
    ramo = arf.marcar_ramo_negativo(colateral.id, em=AGORA)
    arf.tratar_ramo(ramo.id, injecao_id=corte.id, em=AGORA)

    with pytest.raises(PapelNaArfInvalido) as erro:
        arf.mudar_papel(corte.id, PapelNaARF.EFEITO_FUTURO, em=AGORA)

    print(f"recusa: regra={erro.value.regra!r}")
    assert erro.value.regra == "injecao_de_corte"


# --------------------------------------------------------------------------------------
# F4.1.2 — o espelho UDE → ED (RF-04, RF-05, RF-07, RN-03)
# --------------------------------------------------------------------------------------


def test_marcar_um_efeito_futuro_como_ed_espelha_um_ude_da_cadeia() -> None:
    arf = arf_semeada()
    efeito = arf.adicionar_efeito_futuro(titulo=EFEITO, em=AGORA)

    espelho = arf.espelhar_ude(efeito.id, UDE_UM, em=AGORA)

    print(f"espelho: {espelho}")
    assert espelho.ude_id == UDE_UM
    assert arf.e_efeito_desejavel(efeito.id)
    assert isinstance(arf.projeto.eventos[-1], EfeitoEspelhouUde)


def test_o_mesmo_ude_nao_e_espelhado_em_dois_efeitos_da_mesma_arf() -> None:
    """RF-04/RN-03: um UDE tem no máximo um ED por ARF."""
    arf = arf_semeada()
    um = arf.adicionar_efeito_futuro(titulo=EFEITO, em=AGORA)
    outro = arf.adicionar_efeito_futuro(titulo="a fila de matrícula anda em dois dias", em=AGORA)
    arf.espelhar_ude(um.id, UDE_UM, em=AGORA)

    with pytest.raises(EspelhoInvalido) as erro:
        arf.espelhar_ude(outro.id, UDE_UM, em=AGORA)

    print(f"recusa: regra={erro.value.regra!r}")
    assert erro.value.regra == "ude_ja_espelhado"


def test_injecao_nao_espelha_ude() -> None:
    arf = arf_semeada()
    injecao = arf.adicionar_injecao(titulo=INJECAO, em=AGORA)
    with pytest.raises(EspelhoInvalido) as erro:
        arf.espelhar_ude(injecao.id, UDE_UM, em=AGORA)
    assert erro.value.regra == "papel_incompativel"


def test_ude_fora_da_cadeia_nao_e_espelhavel() -> None:
    """RN-03: o ED espelha um UDE **referenciado pela cadeia**, não um identificador qualquer."""
    arf = arf_semeada()
    efeito = arf.adicionar_efeito_futuro(titulo=EFEITO, em=AGORA)

    with pytest.raises(EspelhoInvalido) as erro:
        arf.espelhar_ude(efeito.id, uuid4(), em=AGORA)

    assert erro.value.regra == "ude_fora_da_cadeia"


def test_arf_criada_do_zero_nao_oferece_espelho_e_declara_sem_origem_vinculada() -> None:
    """RF-07: sem cadeia não há UDE referenciável — e a cobertura diz isso, não mente."""
    arf = novo_projeto_arf(id=ID_DA_ARF, dono=DONO, nome="Futuro do zero", em=AGORA)
    efeito = arf.adicionar_efeito_futuro(titulo=EFEITO, em=AGORA)

    with pytest.raises(EspelhoInvalido) as erro:
        arf.espelhar_ude(efeito.id, UDE_UM, em=AGORA)
    assert erro.value.regra == "sem_cadeia"

    verificacao = arf.verificar()
    print(f"cobertura sem cadeia: {verificacao.resumo()}")
    assert verificacao.sem_origem_vinculada is True
    assert verificacao.cobertura == ()


def test_desfazer_o_espelho_libera_o_ude_para_outro_efeito() -> None:
    arf = arf_semeada()
    um = arf.adicionar_efeito_futuro(titulo=EFEITO, em=AGORA)
    outro = arf.adicionar_efeito_futuro(titulo="a fila anda em dois dias", em=AGORA)
    arf.espelhar_ude(um.id, UDE_UM, em=AGORA)

    arf.desfazer_espelho(um.id, em=AGORA)
    arf.espelhar_ude(outro.id, UDE_UM, em=AGORA)

    assert not arf.e_efeito_desejavel(um.id)
    assert arf.e_efeito_desejavel(outro.id)


def test_excluir_o_efeito_leva_junto_o_espelho() -> None:
    arf = arf_semeada()
    efeito = arf.adicionar_efeito_futuro(titulo=EFEITO, em=AGORA)
    arf.espelhar_ude(efeito.id, UDE_UM, em=AGORA)

    arf.excluir_no(efeito.id, em=AGORA)

    assert arf.espelhos() == ()
    with pytest.raises(NaoEncontrado):
        arf.projeto.no(efeito.id)


# --------------------------------------------------------------------------------------
# F4.1.3 — ramos negativos (RF-08, RF-09, RN-04)
# --------------------------------------------------------------------------------------


def test_marcar_ramo_negativo_abre_o_ramo_e_registra_o_evento() -> None:
    arf = arf_semeada()
    injecao = arf.adicionar_injecao(titulo=INJECAO, em=AGORA)
    colateral = arf.adicionar_efeito_futuro(titulo=EFEITO_COLATERAL, em=AGORA)
    arf.ligar(injecao.id, colateral.id, em=AGORA)

    ramo = arf.marcar_ramo_negativo(colateral.id, em=AGORA)

    print(f"ramo: estado={ramo.estado.value} raiz={ramo.raiz_id}")
    assert ramo.estado is EstadoDoRamo.ABERTO
    assert arf.ramos(EstadoDoRamo.ABERTO) == (ramo,)
    assert isinstance(arf.projeto.eventos[-1], RamoNegativoMarcado)


def test_tratar_exige_injecao_de_corte_que_exista_na_arf() -> None:
    """RN-04: `aberto → tratado` **somente** com injeção de corte referenciada."""
    arf = arf_semeada()
    colateral = arf.adicionar_efeito_futuro(titulo=EFEITO_COLATERAL, em=AGORA)
    ramo = arf.marcar_ramo_negativo(colateral.id, em=AGORA)

    with pytest.raises(NaoEncontrado):
        arf.tratar_ramo(ramo.id, injecao_id=uuid4(), em=AGORA)

    efeito = arf.adicionar_efeito_futuro(titulo=EFEITO, em=AGORA)
    with pytest.raises(RamoNegativoInvalido) as erro:
        arf.tratar_ramo(ramo.id, injecao_id=efeito.id, em=AGORA)
    print(f"recusa: regra={erro.value.regra!r}")
    assert erro.value.regra == "corte_nao_e_injecao"


def test_o_ramo_tratado_carrega_a_injecao_que_o_corta() -> None:
    arf = arf_semeada()
    colateral = arf.adicionar_efeito_futuro(titulo=EFEITO_COLATERAL, em=AGORA)
    corte = arf.adicionar_injecao(titulo=CORTE, em=AGORA)
    ramo = arf.marcar_ramo_negativo(colateral.id, em=AGORA)

    tratado = arf.tratar_ramo(ramo.id, injecao_id=corte.id, em=AGORA)

    print(f"tratado por: {tratado.injecao_de_corte_id}")
    assert tratado.estado is EstadoDoRamo.TRATADO
    assert tratado.injecao_de_corte_id == corte.id
    assert arf.ramos(EstadoDoRamo.ABERTO) == ()
    assert isinstance(arf.projeto.eventos[-1], RamoNegativoTratado)


def test_aceitar_um_ramo_exige_justificativa_e_autor() -> None:
    """RN-04: `aberto → aceito` **somente** com justificativa — e o autor fica no ramo."""
    arf = arf_semeada()
    colateral = arf.adicionar_efeito_futuro(titulo=EFEITO_COLATERAL, em=AGORA)
    ramo = arf.marcar_ramo_negativo(colateral.id, em=AGORA)

    with pytest.raises(RamoNegativoInvalido) as erro:
        arf.aceitar_ramo(ramo.id, justificativa="   ", autor="Facilitadora TOC", em=AGORA)
    assert erro.value.regra == "justificativa_obrigatoria"

    aceito = arf.aceitar_ramo(
        ramo.id,
        justificativa="o pico dura três semanas e a equipe recebe folga compensatória",
        autor="Facilitadora TOC",
        em=AGORA,
    )
    print(f"aceito por {aceito.autor}: {aceito.justificativa[:40]}…")
    assert aceito.estado is EstadoDoRamo.ACEITO
    assert aceito.autor == "Facilitadora TOC"
    assert isinstance(arf.projeto.eventos[-1], RamoNegativoAceito)


def test_ramo_tratado_e_aceito_reabrem_por_acao_explicita() -> None:
    arf = arf_semeada()
    colateral = arf.adicionar_efeito_futuro(titulo=EFEITO_COLATERAL, em=AGORA)
    corte = arf.adicionar_injecao(titulo=CORTE, em=AGORA)
    ramo = arf.marcar_ramo_negativo(colateral.id, em=AGORA)
    arf.tratar_ramo(ramo.id, injecao_id=corte.id, em=AGORA)

    reaberto = arf.reabrir_ramo(ramo.id, em=AGORA)

    assert reaberto.estado is EstadoDoRamo.ABERTO
    assert reaberto.injecao_de_corte_id is None
    assert isinstance(arf.projeto.eventos[-1], RamoNegativoReaberto)


def test_excluir_a_injecao_de_corte_reabre_o_ramo_em_vez_de_deixar_referencia_orfa() -> None:
    """A regra do M2 aplicada aqui: nada some deixando referência apontando para o vazio."""
    arf = arf_semeada()
    colateral = arf.adicionar_efeito_futuro(titulo=EFEITO_COLATERAL, em=AGORA)
    corte = arf.adicionar_injecao(titulo=CORTE, em=AGORA)
    ramo = arf.marcar_ramo_negativo(colateral.id, em=AGORA)
    arf.tratar_ramo(ramo.id, injecao_id=corte.id, em=AGORA)

    arf.excluir_no(corte.id, em=AGORA)

    print(f"ramo depois da exclusão: {arf.ramo(ramo.id)}")
    assert arf.ramo(ramo.id).estado is EstadoDoRamo.ABERTO
    assert arf.ramo(ramo.id).injecao_de_corte_id is None


def test_excluir_a_raiz_do_ramo_leva_o_ramo_junto() -> None:
    arf = arf_semeada()
    colateral = arf.adicionar_efeito_futuro(titulo=EFEITO_COLATERAL, em=AGORA)
    ramo = arf.marcar_ramo_negativo(colateral.id, em=AGORA)

    arf.excluir_no(colateral.id, em=AGORA)

    assert arf.ramos() == ()
    with pytest.raises(NaoEncontrado):
        arf.ramo(ramo.id)


def test_o_mesmo_no_nao_e_raiz_de_dois_ramos() -> None:
    arf = arf_semeada()
    colateral = arf.adicionar_efeito_futuro(titulo=EFEITO_COLATERAL, em=AGORA)
    arf.marcar_ramo_negativo(colateral.id, em=AGORA)
    with pytest.raises(RamoNegativoInvalido) as erro:
        arf.marcar_ramo_negativo(colateral.id, em=AGORA)
    assert erro.value.regra == "ramo_ja_marcado"


# --------------------------------------------------------------------------------------
# F4.1.4 — a verificação estrutural (RF-11, RF-13, RNF-01): função pura, sem rede
# --------------------------------------------------------------------------------------


def test_a_verificacao_aponta_ed_sem_caminho_desde_injecao() -> None:
    arf = arf_semeada()
    solto = arf.adicionar_efeito_futuro(titulo=EFEITO, em=AGORA)
    arf.espelhar_ude(solto.id, UDE_UM, em=AGORA)

    verificacao = arf.verificar()

    print(f"EDs sem caminho: {verificacao.eds_sem_caminho}")
    assert verificacao.eds_sem_caminho == (solto.id,)
    assert verificacao.cobertura[0].ude_id == UDE_UM
    assert verificacao.cobertura[0].alcancado is False


def test_a_verificacao_reconhece_ed_alcancado_por_caminho_indireto() -> None:
    arf = arf_semeada()
    injecao = arf.adicionar_injecao(titulo=INJECAO, em=AGORA)
    intermediario = arf.adicionar_efeito_futuro(titulo="o edital sai em janeiro", em=AGORA)
    ed = arf.adicionar_efeito_futuro(titulo=EFEITO, em=AGORA)
    arf.ligar(injecao.id, intermediario.id, em=AGORA)
    arf.ligar(intermediario.id, ed.id, em=AGORA)
    arf.espelhar_ude(ed.id, UDE_UM, em=AGORA)

    verificacao = arf.verificar()

    print(f"cobertura: {[ (str(c.ude_id)[:8], c.alcancado) for c in verificacao.cobertura ]}")
    assert verificacao.eds_sem_caminho == ()
    assert verificacao.cobertura[0].alcancado is True
    # O segundo UDE da cadeia continua descoberto — e a verificação o lista.
    assert verificacao.cobertura[1].ude_id == UDE_DOIS
    assert verificacao.cobertura[1].espelhado_por is None


def test_a_verificacao_lista_injecao_sem_efeito_ligado_e_ramos_abertos() -> None:
    arf = arf_semeada()
    orfa = arf.adicionar_injecao(titulo=INJECAO, em=AGORA)
    colateral = arf.adicionar_efeito_futuro(titulo=EFEITO_COLATERAL, em=AGORA)
    ramo = arf.marcar_ramo_negativo(colateral.id, em=AGORA)

    verificacao = arf.verificar()

    print(f"resumo: {verificacao.resumo()}")
    assert verificacao.injecoes_sem_efeito == (orfa.id,)
    assert verificacao.ramos_abertos == (ramo.id,)
    assert verificacao.resumo()["ramos_negativos_abertos"] == 1
    assert verificacao.pronta is False


def test_a_verificacao_nao_muta_o_grafo_e_a_gerada_emite_o_resumo() -> None:
    """RF-13: `VerificacaoDaArfGerada` carrega o resumo quantitativo — grandeza, não texto."""
    arf = arf_semeada()
    injecao = arf.adicionar_injecao(titulo=INJECAO, em=AGORA)
    ed = arf.adicionar_efeito_futuro(titulo=EFEITO, em=AGORA)
    arf.ligar(injecao.id, ed.id, em=AGORA)
    arf.espelhar_ude(ed.id, UDE_UM, em=AGORA)
    antes = (len(arf.nos), len(arf.arestas))
    arf.drenar_eventos()

    verificacao = arf.gerar_verificacao(em=AGORA)

    depois = (len(arf.nos), len(arf.arestas))
    evento = arf.projeto.eventos[-1]
    print(f"antes={antes} depois={depois} resumo={evento.resumo}")
    assert antes == depois
    assert isinstance(evento, VerificacaoDaArfGerada)
    assert evento.resumo["udes_cobertos"] == 1
    assert evento.resumo["udes_referenciados"] == 2
    assert verificacao.resumo() == evento.resumo


# --------------------------------------------------------------------------------------
# Reidratação — carregar não é mutar (a mesma regra do M2 e do M3)
# --------------------------------------------------------------------------------------


def test_reidratar_nao_emite_evento_nenhum() -> None:
    arf = arf_semeada()
    injecao = arf.adicionar_injecao(titulo=INJECAO, em=AGORA)
    ed = arf.adicionar_efeito_futuro(titulo=EFEITO, em=AGORA)
    arf.ligar(injecao.id, ed.id, em=AGORA)
    espelho = arf.espelhar_ude(ed.id, UDE_UM, em=AGORA)
    ramo = arf.marcar_ramo_negativo(ed.id, em=AGORA)

    de_volta = reidratar_arf(
        arf.projeto,
        espelhos={ed.id: espelho},
        ramos=(ramo,),
        exames={},
        conectores=(),
        udes_da_cadeia=(UDE_UM, UDE_DOIS),
    )

    print(f"eventos após reidratar: {len(de_volta.projeto.eventos)}")
    assert de_volta.projeto.eventos == ()
    assert de_volta.e_efeito_desejavel(ed.id)
    assert de_volta.ramos()[0].id == ramo.id
