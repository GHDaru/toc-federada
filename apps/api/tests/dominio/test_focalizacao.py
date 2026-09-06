"""M6 · Focalização — as invariantes do agregado (spec 009, RN-01..RN-04, RN-07).

Siglas, uma vez neste arquivo: **M6** — Focalização · **M1** — Núcleo de Diagramas
Lógicos · **TOC** — Teoria das Restrições · **ARA** — Árvore da Realidade Atual ·
**RN/RF** — regra de negócio / requisito funcional · **DoD** — *Definition of Done*
(Definição de Pronto).

Suíte de domínio: **sem rede, sem banco, sem relógio e sem modelo** (RNF-01). O instante
entra por argumento (`em=`), como em todo o resto deste domínio.

Estes testes nasceram VERMELHOS, antes de `toc_api.dominio.focalizacao` existir (P4,
T-04 do `tasks.md` do ciclo 009). Eles cobrem as linhas 2 e 6 da tabela de aceite da
spec: a ordem canônica dos cinco passos e as duas unicidades.
"""
from __future__ import annotations

from uuid import uuid4

import pytest

from toc_api.dominio.erros import DadoInvalido, MutacaoRecusada, NaoEncontrado
from toc_api.dominio.eventos import (
    AnaliseCriada,
    CicloAberto,
    NotaRegistrada,
    PassoConcluido,
    PassoReaberto,
    RestricaoEditada,
    RestricaoRegistrada,
)
from toc_api.dominio.focalizacao import (
    FERRAMENTA_FOCALIZACAO,
    ORDEM_CANONICA,
    AnaliseDeFocalizacao,
    CicloInvalido,
    EstadoDoCiclo,
    EstadoDoPasso,
    PassoInvalido,
    ReferenciaDeOrigemDaRestricao,
    RestricaoInvalida,
    SistemaAnalisado,
    TipoDePasso,
    TipoDeRestricao,
    nova_analise_de_focalizacao,
)
from toc_api.dominio.projeto import Projeto

from .focalizacao_sintetica import (
    AGORA,
    AUTORA,
    DECISAO_DE_EXPLORAR,
    DESCRICAO_DO_SISTEMA,
    DONO,
    ID_DA_ANALISE,
    ID_DA_ARA,
    ID_DO_NO_DE_CAUSA_RAIZ,
    JUSTIFICATIVA_DA_RESTRICAO,
    NOME,
    RESTRICAO,
    SISTEMA,
    depois,
)


def nova() -> AnaliseDeFocalizacao:
    return nova_analise_de_focalizacao(
        id=ID_DA_ANALISE,
        dono=DONO,
        nome=NOME,
        sistema=SistemaAnalisado(nome=SISTEMA, descricao=DESCRICAO_DO_SISTEMA),
        em=AGORA,
    )


def com_restricao(analise: AnaliseDeFocalizacao, *, em=None) -> AnaliseDeFocalizacao:
    analise.registrar_restricao(
        descricao=RESTRICAO,
        tipo=TipoDeRestricao.FISICA,
        justificativa=JUSTIFICATIVA_DA_RESTRICAO,
        autor=AUTORA,
        em=em or depois(5),
    )
    return analise


# ---------------------------------------------------------------------------------------
# RF-01/RF-02 — a análise nasce com o primeiro ciclo aberto e os cinco passos
# ---------------------------------------------------------------------------------------


def test_a_analise_nasce_com_um_ciclo_aberto_no_passo_identificar():
    """US-01: "nasce com o primeiro ciclo de focalização aberto no passo identificar"."""
    analise = nova()

    assert analise.projeto.ferramenta == FERRAMENTA_FOCALIZACAO
    assert len(analise.ciclos) == 1
    ciclo = analise.ciclo_aberto
    assert ciclo.estado is EstadoDoCiclo.ABERTO
    assert ciclo.ordem == 1
    assert ciclo.restricao is None
    assert analise.passo_atual.tipo is TipoDePasso.IDENTIFICAR
    assert analise.passo_atual.estado is EstadoDoPasso.EM_ANDAMENTO


def test_o_ciclo_instancia_os_cinco_passos_na_ordem_canonica_sempre():
    """RN-01: "todo ciclo os instancia todos, na criação" — cinco, nesta ordem."""
    analise = nova()

    tipos = tuple(p.tipo for p in analise.ciclo_aberto.passos)
    assert tipos == ORDEM_CANONICA
    assert tipos == (
        TipoDePasso.IDENTIFICAR,
        TipoDePasso.EXPLORAR,
        TipoDePasso.SUBORDINAR,
        TipoDePasso.ELEVAR,
        TipoDePasso.RECOMECAR,
    )
    pendentes = [p for p in analise.ciclo_aberto.passos if p.estado is EstadoDoPasso.PENDENTE]
    assert len(pendentes) == 4  # só `identificar` começa em andamento


def test_a_criacao_emite_analise_criada_e_ciclo_aberto():
    eventos = nova().drenar_eventos()

    assert [type(e) for e in eventos] == [AnaliseCriada, CicloAberto]
    assert eventos[0].tipo_de_acao == "focalizacao.criar_analise"
    assert eventos[1].ordem == 1


def test_a_analise_exige_a_ferramenta_focalizacao():
    """A mesma guarda de `ProjetoARA` e `NuvemDeConflito`: raiz não adota projeto alheio."""
    projeto = Projeto(
        id=uuid4(), dono=DONO, nome=NOME, ferramenta="ara", criado_em=AGORA, alterado_em=AGORA
    )
    with pytest.raises(MutacaoRecusada):
        AnaliseDeFocalizacao(projeto=projeto, sistema=SistemaAnalisado(nome=SISTEMA))


def test_sistema_analisado_sem_nome_nao_existe():
    with pytest.raises(DadoInvalido):
        SistemaAnalisado(nome="   ")


# ---------------------------------------------------------------------------------------
# RN-01 — a ordem canônica: não se cria, não se exclui, não se reordena passo
# ---------------------------------------------------------------------------------------


def test_ordem_canonica_recusa_criar_passo():
    analise = nova()
    with pytest.raises(PassoInvalido) as erro:
        analise.adicionar_passo(TipoDePasso.EXPLORAR, em=depois(1))
    assert erro.value.regra == "ordem_canonica"


def test_ordem_canonica_recusa_excluir_passo():
    analise = nova()
    with pytest.raises(PassoInvalido) as erro:
        analise.excluir_passo(TipoDePasso.ELEVAR, em=depois(1))
    assert erro.value.regra == "ordem_canonica"


def test_ordem_canonica_recusa_reordenar_passo():
    analise = nova()
    with pytest.raises(PassoInvalido) as erro:
        analise.reordenar_passos(
            (
                TipoDePasso.EXPLORAR,
                TipoDePasso.IDENTIFICAR,
                TipoDePasso.SUBORDINAR,
                TipoDePasso.ELEVAR,
                TipoDePasso.RECOMECAR,
            ),
            em=depois(1),
        )
    assert erro.value.regra == "ordem_canonica"


def test_ordem_canonica_avanca_um_passo_por_vez():
    """RN-01: "A conclusão avança um passo por vez" — pular passo é recusado."""
    analise = com_restricao(nova())

    with pytest.raises(PassoInvalido) as erro:
        analise.concluir_passo(
            TipoDePasso.SUBORDINAR, decisao="pular a fila", autor=AUTORA, em=depois(10)
        )
    assert erro.value.regra == "passo_fora_de_vez"

    analise.concluir_passo(
        TipoDePasso.IDENTIFICAR, decisao="a restrição é a secretaria", autor=AUTORA, em=depois(11)
    )
    assert analise.passo_atual.tipo is TipoDePasso.EXPLORAR


def test_ordem_canonica_sobrevive_a_um_recomeco():
    """Ciclo novo nasce com os mesmos cinco passos, na mesma ordem — nunca configurável."""
    analise = _ate_o_recomeco(nova())
    analise.recomecar(em=depois(60))

    assert tuple(p.tipo for p in analise.ciclo_aberto.passos) == ORDEM_CANONICA


# ---------------------------------------------------------------------------------------
# RN-02 e RN-03 — as duas unicidades
# ---------------------------------------------------------------------------------------


def test_unicidade_de_ciclo_aberto_ha_no_maximo_um():
    """RN-02: "não existe 'fechar sem recomeçar' nem dois ciclos correndo"."""
    analise = _ate_o_recomeco(nova())
    analise.recomecar(em=depois(60))

    assert len(analise.ciclos) == 2
    assert [c.estado for c in analise.ciclos] == [EstadoDoCiclo.FECHADO, EstadoDoCiclo.ABERTO]
    assert len([c for c in analise.ciclos if c.estado is EstadoDoCiclo.ABERTO]) == 1

    with pytest.raises(CicloInvalido) as erro:
        analise.abrir_ciclo(em=depois(61))
    assert erro.value.regra == "ja_ha_ciclo_aberto"


def test_unicidade_de_restricao_vigente_a_segunda_e_recusada():
    """RN-03: "Um ciclo tem no máximo uma restrição vigente"."""
    analise = com_restricao(nova())

    with pytest.raises(RestricaoInvalida) as erro:
        analise.registrar_restricao(
            descricao="Orçamento anual",
            tipo=TipoDeRestricao.POLITICA,
            justificativa="a diretoria não libera verba",
            autor=AUTORA,
            em=depois(6),
        )
    assert erro.value.regra == "restricao_ja_registrada"
    assert analise.ciclo_aberto.restricao.descricao == RESTRICAO


def test_unicidade_a_troca_de_alvo_e_recomeco_nunca_edicao():
    """RN-03: mudar o alvo não é editar — e a edição não deixa trocar o tipo."""
    analise = com_restricao(nova())

    with pytest.raises(TypeError):
        analise.editar_restricao(tipo=TipoDeRestricao.POLITICA, em=depois(7))


# ---------------------------------------------------------------------------------------
# RF-05..RF-08 — o registro da restrição
# ---------------------------------------------------------------------------------------


def test_registrar_restricao_torna_a_vigente_e_emite_evento_com_autor():
    analise = nova()
    analise.registrar_restricao(
        descricao=RESTRICAO,
        tipo=TipoDeRestricao.FISICA,
        justificativa=JUSTIFICATIVA_DA_RESTRICAO,
        autor=AUTORA,
        em=depois(5),
    )
    analise.drenar_eventos()  # limpa os da criação

    restricao = analise.ciclo_aberto.restricao
    assert restricao.descricao == RESTRICAO
    assert restricao.tipo is TipoDeRestricao.FISICA
    assert restricao.justificativa == JUSTIFICATIVA_DA_RESTRICAO
    assert restricao.origem is None
    assert restricao.autor == AUTORA


def test_registrar_restricao_emite_restricao_registrada():
    analise = nova()
    analise.drenar_eventos()
    analise.registrar_restricao(
        descricao=RESTRICAO,
        tipo=TipoDeRestricao.FISICA,
        justificativa=JUSTIFICATIVA_DA_RESTRICAO,
        autor=AUTORA,
        em=depois(5),
    )
    (evento,) = analise.drenar_eventos()
    assert isinstance(evento, RestricaoRegistrada)
    assert evento.tipo == TipoDeRestricao.FISICA.value
    assert evento.autor == AUTORA
    assert evento.tipo_de_acao == "focalizacao.registrar_restricao"


def test_registrar_restricao_a_partir_de_uma_causa_raiz_guarda_a_origem():
    """RF-06/US-04: a conclusão carrega a evidência que a sustenta (INT-02)."""
    analise = nova()
    analise.vincular_ferramenta(
        TipoDePasso.IDENTIFICAR, tipo="ara", projeto_id=ID_DA_ARA, em=depois(2)
    )
    analise.registrar_restricao(
        descricao=RESTRICAO,
        tipo=TipoDeRestricao.FISICA,
        justificativa=JUSTIFICATIVA_DA_RESTRICAO,
        autor=AUTORA,
        origem=ReferenciaDeOrigemDaRestricao(
            ferramenta="ara", projeto_id=ID_DA_ARA, no_id=ID_DO_NO_DE_CAUSA_RAIZ
        ),
        em=depois(5),
    )

    origem = analise.ciclo_aberto.restricao.origem
    assert origem.ferramenta == "ara"
    assert origem.projeto_id == ID_DA_ARA
    assert origem.no_id == ID_DO_NO_DE_CAUSA_RAIZ


def test_a_ferramenta_ajuda_e_nunca_condiciona_restricao_manual_e_valida():
    """RF-06: "DEVE permitir registrá-la manualmente, sem ARA nenhuma"."""
    analise = com_restricao(nova())
    assert analise.ciclo_aberto.restricao.origem is None
    analise.concluir_passo(
        TipoDePasso.IDENTIFICAR, decisao="restrição confirmada", autor=AUTORA, em=depois(10)
    )
    assert analise.passo_atual.tipo is TipoDePasso.EXPLORAR


def test_origem_da_restricao_exige_ferramenta_projeto_e_no():
    with pytest.raises(DadoInvalido):
        ReferenciaDeOrigemDaRestricao(ferramenta="  ", projeto_id=ID_DA_ARA, no_id=ID_DO_NO_DE_CAUSA_RAIZ)


def test_editar_restricao_muda_descricao_e_justificativa_com_evento():
    analise = com_restricao(nova())
    analise.drenar_eventos()

    analise.editar_restricao(
        descricao="Capacidade de conferência documental da secretaria",
        justificativa="a fila só cresce nesta etapa, medido em três períodos de entrada",
        em=depois(8),
    )

    (evento,) = analise.drenar_eventos()
    assert isinstance(evento, RestricaoEditada)
    assert sorted(evento.campos) == ["descricao", "justificativa"]
    assert analise.ciclo_aberto.restricao.tipo is TipoDeRestricao.FISICA


def test_editar_restricao_sem_campo_nenhum_e_recusado():
    analise = com_restricao(nova())
    with pytest.raises(RestricaoInvalida) as erro:
        analise.editar_restricao(em=depois(8))
    assert erro.value.regra == "nada_a_editar"


def test_editar_restricao_inexistente_e_recusado():
    analise = nova()
    with pytest.raises(RestricaoInvalida) as erro:
        analise.editar_restricao(descricao="qualquer coisa", em=depois(8))
    assert erro.value.regra == "sem_restricao"


def test_identificar_nao_conclui_sem_restricao_registrada():
    """RF-08: a recusa é DO DOMÍNIO, não da borda."""
    analise = nova()
    with pytest.raises(PassoInvalido) as erro:
        analise.concluir_passo(
            TipoDePasso.IDENTIFICAR, decisao="seguimos assim", autor=AUTORA, em=depois(10)
        )
    assert erro.value.regra == "sem_restricao"
    assert analise.passo_atual.tipo is TipoDePasso.IDENTIFICAR


# ---------------------------------------------------------------------------------------
# RF-09..RF-11 — conclusão, reabertura e notas
# ---------------------------------------------------------------------------------------


def test_concluir_passo_exige_decisao_escrita():
    analise = com_restricao(nova())
    with pytest.raises(PassoInvalido) as erro:
        analise.concluir_passo(TipoDePasso.IDENTIFICAR, decisao="   ", autor=AUTORA, em=depois(10))
    assert erro.value.regra == "decisao_obrigatoria"


def test_concluir_passo_guarda_autor_data_e_decisao_no_evento():
    analise = com_restricao(nova())
    analise.drenar_eventos()

    analise.concluir_passo(
        TipoDePasso.IDENTIFICAR, decisao="a restrição é a secretaria", autor=AUTORA, em=depois(10)
    )
    eventos = analise.drenar_eventos()
    concluido = [e for e in eventos if isinstance(e, PassoConcluido)]
    assert len(concluido) == 1
    assert concluido[0].passo == TipoDePasso.IDENTIFICAR.value
    assert concluido[0].autor == AUTORA
    assert concluido[0].instante == depois(10)
    passo = analise.ciclo_aberto.passo(TipoDePasso.IDENTIFICAR)
    assert passo.decisao.texto == "a restrição é a secretaria"
    assert passo.decisao.autor == AUTORA
    assert passo.decisao.instante == depois(10)


def test_avanco_e_ato_explicito_nunca_efeito_colateral_de_vinculo_ou_nota():
    """RN-01: registrar nota ou vincular ferramenta NÃO move a jornada."""
    analise = com_restricao(nova())
    analise.anotar_passo(TipoDePasso.IDENTIFICAR, texto="a fila cresce", autor=AUTORA, em=depois(6))
    analise.vincular_ferramenta(
        TipoDePasso.IDENTIFICAR, tipo="ara", projeto_id=ID_DA_ARA, em=depois(7)
    )
    assert analise.passo_atual.tipo is TipoDePasso.IDENTIFICAR
    assert analise.passo_atual.estado is EstadoDoPasso.EM_ANDAMENTO


def test_reabrir_o_passo_anterior_nao_apaga_a_decisao_que_o_concluiu():
    """RF-10 + RN-04: o histórico de decisões é somente-acréscimo."""
    analise = com_restricao(nova())
    analise.concluir_passo(
        TipoDePasso.IDENTIFICAR, decisao="a restrição é a secretaria", autor=AUTORA, em=depois(10)
    )
    analise.drenar_eventos()

    analise.reabrir_passo_anterior(
        justificativa="a medição da fila mudou depois da conferência de setembro",
        autor=AUTORA,
        em=depois(12),
    )

    passo = analise.ciclo_aberto.passo(TipoDePasso.IDENTIFICAR)
    assert passo.estado is EstadoDoPasso.EM_ANDAMENTO
    assert len(passo.decisoes) == 1, "a decisão anterior continua no histórico"
    assert passo.decisoes[0].texto == "a restrição é a secretaria"
    assert analise.ciclo_aberto.passo(TipoDePasso.EXPLORAR).estado is EstadoDoPasso.PENDENTE
    (evento,) = [e for e in analise.drenar_eventos() if isinstance(e, PassoReaberto)]
    assert evento.passo == TipoDePasso.IDENTIFICAR.value
    assert "setembro" in evento.justificativa


def test_reabrir_e_concluir_de_novo_acumula_decisoes_e_nunca_sobrescreve():
    analise = com_restricao(nova())
    analise.concluir_passo(
        TipoDePasso.IDENTIFICAR, decisao="primeira leitura", autor=AUTORA, em=depois(10)
    )
    analise.reabrir_passo_anterior(justificativa="a medição mudou", autor=AUTORA, em=depois(12))
    analise.concluir_passo(
        TipoDePasso.IDENTIFICAR, decisao="segunda leitura", autor=AUTORA, em=depois(14)
    )

    passo = analise.ciclo_aberto.passo(TipoDePasso.IDENTIFICAR)
    assert [d.texto for d in passo.decisoes] == ["primeira leitura", "segunda leitura"]
    assert passo.decisao.texto == "segunda leitura"


def test_reabrir_exige_justificativa():
    analise = com_restricao(nova())
    analise.concluir_passo(
        TipoDePasso.IDENTIFICAR, decisao="a restrição é a secretaria", autor=AUTORA, em=depois(10)
    )
    with pytest.raises(PassoInvalido) as erro:
        analise.reabrir_passo_anterior(justificativa="  ", autor=AUTORA, em=depois(12))
    assert erro.value.regra == "justificativa_obrigatoria"


def test_reabrir_sem_passo_anterior_concluido_e_recusado():
    analise = com_restricao(nova())
    with pytest.raises(PassoInvalido) as erro:
        analise.reabrir_passo_anterior(justificativa="quero voltar", autor=AUTORA, em=depois(12))
    assert erro.value.regra == "sem_passo_anterior"


def test_notas_acumulam_com_autoria_e_sao_distintas_da_decisao():
    """RF-11: nota é texto livre acumulável — não é a decisão que encerra o passo."""
    analise = com_restricao(nova())
    analise.anotar_passo(
        TipoDePasso.IDENTIFICAR, texto="a fila cresce todo período", autor=AUTORA, em=depois(6)
    )
    analise.anotar_passo(
        TipoDePasso.IDENTIFICAR, texto="nenhuma outra etapa acumula", autor=AUTORA, em=depois(7)
    )
    analise.drenar_eventos()

    passo = analise.ciclo_aberto.passo(TipoDePasso.IDENTIFICAR)
    assert [n.texto for n in passo.notas] == [
        "a fila cresce todo período",
        "nenhuma outra etapa acumula",
    ]
    assert all(n.autor == AUTORA for n in passo.notas)
    assert passo.decisao is None


def test_nota_emite_evento_e_nao_conclui_nada():
    analise = com_restricao(nova())
    analise.drenar_eventos()
    analise.anotar_passo(TipoDePasso.IDENTIFICAR, texto="a fila cresce", autor=AUTORA, em=depois(6))
    (evento,) = analise.drenar_eventos()
    assert isinstance(evento, NotaRegistrada)
    assert analise.ciclo_aberto.passo(TipoDePasso.IDENTIFICAR).estado is EstadoDoPasso.EM_ANDAMENTO


def test_nota_vazia_e_recusada():
    analise = com_restricao(nova())
    with pytest.raises(DadoInvalido):
        analise.anotar_passo(TipoDePasso.IDENTIFICAR, texto="   ", autor=AUTORA, em=depois(6))


def test_passo_desconhecido_e_nao_encontrado():
    analise = nova()
    with pytest.raises(NaoEncontrado):
        analise.ciclo_aberto.passo("inventado")


# ---------------------------------------------------------------------------------------
# RN-07 — o passo `recomecar` não tem decisão de conclusão própria
# ---------------------------------------------------------------------------------------


def test_recomecar_nao_conclui_por_decisao_o_ato_dele_e_o_recomeco():
    analise = _ate_o_recomeco(nova())
    assert analise.passo_atual.tipo is TipoDePasso.RECOMECAR

    with pytest.raises(PassoInvalido) as erro:
        analise.concluir_passo(
            TipoDePasso.RECOMECAR, decisao="terminamos", autor=AUTORA, em=depois(50)
        )
    assert erro.value.regra == "recomecar_nao_conclui"


# ---------------------------------------------------------------------------------------
# RN-04 — herança do M1: exclusão suave, restauração, e o ciclo de vida do projeto
# ---------------------------------------------------------------------------------------


def test_analise_excluida_recusa_toda_mutacao_e_volta_intacta_na_restauracao():
    """US-02: "ela volta com ciclos, passos, restrições e vínculos intactos"."""
    analise = com_restricao(nova())
    analise.vincular_ferramenta(
        TipoDePasso.IDENTIFICAR, tipo="ara", projeto_id=ID_DA_ARA, em=depois(7)
    )
    antes = analise.ciclo_aberto.retrato()

    analise.excluir(em=depois(20))
    with pytest.raises(MutacaoRecusada):
        analise.anotar_passo(TipoDePasso.IDENTIFICAR, texto="depois", autor=AUTORA, em=depois(21))

    analise.restaurar(em=depois(22))
    assert analise.ciclo_aberto.retrato() == antes


def test_a_analise_carrega_a_trava_otimista_do_m1():
    """A versão lida é a base da trava; toda mutação avança a versão do projeto."""
    analise = nova()
    assert analise.projeto.versao_lida == 0
    versao = analise.projeto.versao
    com_restricao(analise)
    assert analise.projeto.versao > versao

    analise.projeto.confirmar_gravacao()
    assert analise.projeto.versao_lida == analise.projeto.versao


# ---------------------------------------------------------------------------------------
# apoio
# ---------------------------------------------------------------------------------------


def _ate_o_recomeco(analise: AnaliseDeFocalizacao) -> AnaliseDeFocalizacao:
    """Leva a análise até o quinto passo do primeiro ciclo, pelo caminho legítimo."""
    com_restricao(analise)
    analise.concluir_passo(
        TipoDePasso.IDENTIFICAR, decisao="a restrição é a secretaria", autor=AUTORA, em=depois(10)
    )
    analise.concluir_passo(
        TipoDePasso.EXPLORAR, decisao=DECISAO_DE_EXPLORAR, autor=AUTORA, em=depois(20)
    )
    analise.concluir_passo(
        TipoDePasso.SUBORDINAR, decisao="nenhuma turma abre antes da conferência", autor=AUTORA,
        em=depois(30),
    )
    analise.concluir_passo(
        TipoDePasso.ELEVAR, decisao="contratar duas pessoas", autor=AUTORA, em=depois(40)
    )
    return analise
