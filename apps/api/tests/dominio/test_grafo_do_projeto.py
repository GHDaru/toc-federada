"""M1 — nós, arestas causais e as invariantes do agregado (spec 004).

Estes testes nascem **antes** do código (P4). Cada um é uma linha do
`specs/004-nucleo-de-diagramas/data-model.md`, seção "Invariantes":

1. aresta só referencia nós existentes do próprio projeto (RF-20);
2. sem auto-laço (RN-02) e sem par (origem, destino) duplicado (RN-03);
3. excluir nó remove exatamente o nó e suas arestas incidentes, nada mais — o teste que
   teria pego o filtro invertido de `tocbuilderv3/services/mockApiService.ts:521`
   (`project.nodes = project.nodes.filter(n => n.id === nodeId);`), que apagava todos os
   nós **menos** o excluído (spec 004, F-06 e RF-16);
4. projeto excluído recusa mutação (RF-10);
5. restaurar devolve o conteúdo idêntico (RF-08).

Sem rede, sem banco, sem relógio: o instante entra por argumento.
"""
from datetime import datetime, timezone
from uuid import uuid4

import pytest

from toc_api.dominio.erros import ArestaInvalida, MutacaoRecusada, NaoEncontrado
from toc_api.dominio.eventos import (
    ArestaExcluida,
    ArestaLigada,
    NoAdicionado,
    NoExcluido,
    NoMovido,
)
from toc_api.dominio.identidade import DonoDoProjeto
from toc_api.dominio.projeto import Projeto
from toc_api.dominio.valores import PosicaoNoCanvas

DONO = DonoDoProjeto(inquilino_id="inq-horizonte", usuario_id="usr-facilitadora")
T0 = datetime(2026, 9, 5, 12, 0, tzinfo=timezone.utc)
T1 = datetime(2026, 9, 5, 13, 0, tzinfo=timezone.utc)


def novo_projeto() -> Projeto:
    return Projeto(
        id=uuid4(),
        dono=DONO,
        nome="Instituição Horizonte — diagrama",
        criado_em=T0,
        alterado_em=T0,
    )


def com_dois_nos():
    p = novo_projeto()
    a = p.adicionar_no(titulo="Os formulários chegam incompletos.", em=T0)
    b = p.adicionar_no(titulo="O prazo médio de resposta é de 9 dias.", em=T0)
    return p, a, b


# -- nós ------------------------------------------------------------------------------


def test_adicionar_no_entra_no_agregado_e_emite_evento():
    p = novo_projeto()
    no = p.adicionar_no(
        titulo="A taxa de conclusão é de 54%.",
        descricao="medida no semestre corrente",
        posicao=PosicaoNoCanvas(120, 40),
        em=T0,
    )
    assert p.nos == (no,)
    assert p.no(no.id).titulo == "A taxa de conclusão é de 54%."
    assert p.no(no.id).posicao == PosicaoNoCanvas(120, 40)
    assert isinstance(p.eventos[-1], NoAdicionado)
    assert p.eventos[-1].no_id == no.id


def test_no_sem_titulo_e_recusado():
    p = novo_projeto()
    with pytest.raises(Exception):
        p.adicionar_no(titulo="   ", em=T0)


def test_mover_no_troca_a_posicao_e_emite_no_movido():
    p, a, _ = com_dois_nos()
    p.mover_no(a.id, PosicaoNoCanvas(10, 20), em=T1)
    assert p.no(a.id).posicao == PosicaoNoCanvas(10, 20)
    assert isinstance(p.eventos[-1], NoMovido)


def test_operacao_sobre_no_inexistente_e_nao_encontrado():
    p = novo_projeto()
    with pytest.raises(NaoEncontrado):
        p.mover_no(uuid4(), PosicaoNoCanvas(0, 0), em=T0)


# -- arestas --------------------------------------------------------------------------


def test_ligar_dois_nos_cria_aresta_dirigida():
    p, a, b = com_dois_nos()
    aresta = p.ligar(a.id, b.id, em=T0)
    assert (aresta.origem_id, aresta.destino_id) == (a.id, b.id)
    assert p.arestas == (aresta,)
    assert isinstance(p.eventos[-1], ArestaLigada)


def test_aresta_para_no_de_fora_do_projeto_e_recusada():
    """Invariante 1: a ponta tem de ser nó DESTE projeto (RF-20)."""
    p, a, _ = com_dois_nos()
    outro = novo_projeto()
    forasteiro = outro.adicionar_no(titulo="Nó de outro projeto.", em=T0)
    with pytest.raises(ArestaInvalida) as erro:
        p.ligar(a.id, forasteiro.id, em=T0)
    assert erro.value.regra == "pontas_no_projeto"


def test_auto_laco_e_recusado_nomeando_a_regra():
    p, a, _ = com_dois_nos()
    with pytest.raises(ArestaInvalida) as erro:
        p.ligar(a.id, a.id, em=T0)
    assert erro.value.regra == "sem_auto_laco"


def test_aresta_duplicada_e_recusada_mas_o_sentido_inverso_e_permitido():
    """RN-03: (A→B) não se repete; (B→A) é legítimo — laço de reforço é da TOC."""
    p, a, b = com_dois_nos()
    p.ligar(a.id, b.id, em=T0)
    with pytest.raises(ArestaInvalida) as erro:
        p.ligar(a.id, b.id, em=T0)
    assert erro.value.regra == "sem_duplicata"
    inversa = p.ligar(b.id, a.id, em=T0)
    assert (inversa.origem_id, inversa.destino_id) == (b.id, a.id)
    assert len(p.arestas) == 2


def test_criaria_ciclo_e_consulta_do_dominio_nao_proibicao():
    """O ciclo é DETECTADO, não recusado: a spec 005 (RF-29) o lista como legítimo.

    Quem proíbe seria uma regra que a spec 004 nega em RN-03 — por isso o núcleo
    responde à pergunta e deixa a decisão para a ferramenta.
    """
    p, a, b = com_dois_nos()
    p.ligar(a.id, b.id, em=T0)
    assert p.criaria_ciclo(b.id, a.id) is True
    assert p.criaria_ciclo(a.id, b.id) is False


# -- exclusão de nó: o teste que teria pego o defeito da linhagem ----------------------


def test_excluir_no_remove_exatamente_o_no_e_suas_arestas_incidentes():
    """F-06 · o filtro invertido de `mockApiService.ts:521` morre aqui.

    Três nós, três arestas. Excluir o do meio tem de deixar DOIS nós e UMA aresta —
    a linhagem deixava um nó (o excluído) e apagava os outros dois.
    """
    p = novo_projeto()
    a = p.adicionar_no(titulo="Os formulários chegam incompletos.", em=T0)
    m = p.adicionar_no(titulo="A conferência manual leva 3 dias.", em=T0)
    z = p.adicionar_no(titulo="O prazo médio de resposta é de 9 dias.", em=T0)
    p.ligar(a.id, m.id, em=T0)
    p.ligar(m.id, z.id, em=T0)
    solta = p.ligar(a.id, z.id, em=T0)

    removidas = p.excluir_no(m.id, em=T1)

    assert {n.id for n in p.nos} == {a.id, z.id}
    assert [ar.id for ar in p.arestas] == [solta.id]
    assert len(removidas) == 2
    evento = p.eventos[-1]
    assert isinstance(evento, NoExcluido)
    assert set(evento.arestas_removidas) == set(removidas)


def test_excluir_no_isolado_nao_toca_aresta_nenhuma():
    p, a, b = com_dois_nos()
    aresta = p.ligar(a.id, b.id, em=T0)
    solto = p.adicionar_no(titulo="Um nó sem elo nenhum.", em=T0)
    assert p.excluir_no(solto.id, em=T1) == []
    assert [ar.id for ar in p.arestas] == [aresta.id]


def test_excluir_aresta_nao_toca_os_nos():
    p, a, b = com_dois_nos()
    aresta = p.ligar(a.id, b.id, em=T0)
    p.excluir_aresta(aresta.id, em=T1)
    assert p.arestas == ()
    assert {n.id for n in p.nos} == {a.id, b.id}
    assert isinstance(p.eventos[-1], ArestaExcluida)


# -- exclusão suave do projeto --------------------------------------------------------


def test_projeto_excluido_recusa_mutacao_de_grafo():
    """Invariante 4 (RF-10): excluído só aceita restauração."""
    p, a, b = com_dois_nos()
    p.excluir(em=T1)
    with pytest.raises(MutacaoRecusada):
        p.adicionar_no(titulo="Não deveria entrar.", em=T1)
    with pytest.raises(MutacaoRecusada):
        p.ligar(a.id, b.id, em=T1)
    with pytest.raises(MutacaoRecusada):
        p.excluir_no(a.id, em=T1)


def test_restaurar_devolve_nos_e_arestas_identicos():
    """Invariante 5 (RF-08): a exclusão é suave e o conteúdo volta igual."""
    p, a, b = com_dois_nos()
    aresta = p.ligar(a.id, b.id, rotulo="se A, então B", em=T0)
    antes = ([n.id for n in p.nos], [(x.origem_id, x.destino_id, x.rotulo) for x in p.arestas])

    p.excluir(em=T1)
    p.restaurar(em=T1)

    depois = ([n.id for n in p.nos], [(x.origem_id, x.destino_id, x.rotulo) for x in p.arestas])
    assert depois == antes
    assert p.aresta(aresta.id).rotulo == "se A, então B"


# -- eventos --------------------------------------------------------------------------


def test_eventos_sao_somente_acrescimo_e_drenaveis_uma_vez():
    p, a, b = com_dois_nos()
    p.ligar(a.id, b.id, em=T0)
    drenados = p.drenar_eventos()
    assert [type(e).__name__ for e in drenados] == [
        "NoAdicionado",
        "NoAdicionado",
        "ArestaLigada",
    ]
    assert p.eventos == ()
    assert all(e.projeto_id == p.id and e.dono == DONO for e in drenados)
    assert all(e.tipo_de_acao for e in drenados)
