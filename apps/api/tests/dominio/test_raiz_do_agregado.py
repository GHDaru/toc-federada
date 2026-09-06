"""A raiz do agregado é o único caminho para o grafo dela — no domínio puro.

Siglas, uma vez neste arquivo: **DDD** — *Domain-Driven Design* (Design Orientado a
Domínio) · **M1** — Núcleo de Diagramas Lógicos · **M2** — Árvore da Realidade Atual
(ARA) · **M3** — Nuvem de Conflito (NC) · **UDE** — Efeito Indesejável · **TOC** — Teoria
das Restrições · **RN** — regra de negócio.

Os testes de `tests/contrato/test_http_porta_dos_fundos.py` medem o defeito pela borda,
que é onde o crítico o achou. Estes medem a **causa**, sem banco e sem rede: o `Projeto`
de uma ferramenta recusa mutação de grafo que não venha de dentro da raiz, e as duas
raízes existentes delegam por dentro dela.

Por que a causa merece teste próprio: fechar só as rotas seria remendo — sobrariam o
executor do catálogo federado, o próximo caso de uso e o próximo script. Aqui se mede que
a porta dos fundos **deixou de existir**, e não que alguém se lembrou de trancá-la.
"""
from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

import pytest

from toc_api.dominio.ara import FERRAMENTA_ARA, ProjetoARA, novo_projeto_ara
from toc_api.dominio.erros import MutacaoForaDaRaiz
from toc_api.dominio.identidade import DonoDoProjeto
from toc_api.dominio.nuvem import (
    FERRAMENTA_NC,
    ChaveDaAresta,
    NuvemDeConflito,
    PapelDaEntidade,
    novo_projeto_nc,
)
from toc_api.dominio.projeto import (
    RAIZ_POR_FERRAMENTA,
    Projeto,
    raiz_da_ferramenta,
    tem_raiz_propria,
)
from toc_api.dominio.valores import FERRAMENTA_GENERICA, PosicaoNoCanvas

DONA = DonoDoProjeto(inquilino_id="inq-horizonte", usuario_id="usr-facilitadora")
T0 = datetime(2026, 9, 6, 12, 0, tzinfo=timezone.utc)
BOM = "A taxa de conclusão dos cursos técnicos é de 54%."
OUTRO = "O intervalo médio da matrícula até a primeira aula é de 43 dias."

#: As oito mutações de grafo do M1, com um pedido mínimo válido para cada uma. A tabela é
#: escrita à mão de propósito: derivá-la do código faria o teste concordar com o defeito
#: se alguém acrescentasse uma mutação sem guarda.
MUTACOES_DE_GRAFO = (
    "adicionar_no",
    "editar_no",
    "mover_no",
    "recolher_no",
    "excluir_no",
    "ligar",
    "editar_aresta",
    "excluir_aresta",
)


def nuvem() -> NuvemDeConflito:
    return novo_projeto_nc(id=uuid4(), dono=DONA, nome="Dilema da expansão", em=T0)


def ara() -> ProjetoARA:
    return novo_projeto_ara(id=uuid4(), dono=DONA, nome="Árvore da Horizonte", em=T0)


def chamar(projeto: Projeto, operacao: str, nuvem_de_apoio: NuvemDeConflito):
    """Um pedido mínimo e VÁLIDO por operação — a recusa tem de ser da raiz, não do dado."""
    no = projeto.nos[0].id
    aresta = projeto.arestas[0].id
    outro_no = projeto.nos[1].id
    pedidos = {
        "adicionar_no": lambda: projeto.adicionar_no(titulo=BOM, em=T0),
        "editar_no": lambda: projeto.editar_no(no, titulo=BOM, em=T0),
        "mover_no": lambda: projeto.mover_no(no, PosicaoNoCanvas(1.0, 2.0), em=T0),
        "recolher_no": lambda: projeto.recolher_no(no, True, em=T0),
        "excluir_no": lambda: projeto.excluir_no(no, em=T0),
        # A ponta origem→destino escolhida é a do par A→D, que a nuvem NÃO tem: se a
        # guarda falhasse, o erro seguinte seria de topologia e não de raiz.
        "ligar": lambda: projeto.ligar(
            nuvem_de_apoio.entidade(PapelDaEntidade.A).id,
            nuvem_de_apoio.entidade(PapelDaEntidade.D).id,
            em=T0,
        ),
        "editar_aresta": lambda: projeto.editar_aresta(aresta, "rótulo", em=T0),
        "excluir_aresta": lambda: projeto.excluir_aresta(aresta, em=T0),
    }
    assert outro_no  # a nuvem tem cinco nós; o segundo existe e serve de sanidade
    return pedidos[operacao]()


# -- a regra --------------------------------------------------------------------------


@pytest.mark.parametrize("operacao", MUTACOES_DE_GRAFO)
def test_toda_mutacao_de_grafo_de_uma_nuvem_recusa_fora_da_raiz(operacao):
    nc = nuvem()

    with pytest.raises(MutacaoForaDaRaiz) as recusa:
        chamar(nc.projeto, operacao, nc)

    assert recusa.value.operacao == operacao
    assert recusa.value.ferramenta == FERRAMENTA_NC
    assert recusa.value.raiz == "NuvemDeConflito"
    assert len(nc.entidades) == 5 and len(nc.arestas) == 7


def test_toda_mutacao_de_grafo_de_uma_ara_recusa_fora_da_raiz():
    """A ARA nasce vazia, então a tabela acima não serve: aqui vale o que ela tem."""
    arvore = ara()
    a = arvore.adicionar_efeito(titulo=BOM, em=T0)
    b = arvore.adicionar_efeito(titulo=OUTRO, em=T0)
    elo = arvore.ligar(a.id, b.id, em=T0)
    cru = arvore.projeto

    recusadas = []
    for chamada, nome in (
        (lambda: cru.adicionar_no(titulo=BOM, em=T0), "adicionar_no"),
        (lambda: cru.editar_no(a.id, titulo=OUTRO, em=T0), "editar_no"),
        (lambda: cru.mover_no(a.id, PosicaoNoCanvas(3.0, 4.0), em=T0), "mover_no"),
        (lambda: cru.recolher_no(a.id, True, em=T0), "recolher_no"),
        (lambda: cru.excluir_no(a.id, em=T0), "excluir_no"),
        (lambda: cru.ligar(b.id, a.id, em=T0), "ligar"),
        (lambda: cru.editar_aresta(elo.id, "porque", em=T0), "editar_aresta"),
        (lambda: cru.excluir_aresta(elo.id, em=T0), "excluir_aresta"),
    ):
        with pytest.raises(MutacaoForaDaRaiz) as recusa:
            chamada()
        assert recusa.value.operacao == nome
        recusadas.append(nome)

    print(f"mutações de grafo recusadas fora da raiz da ARA: {len(recusadas)} — {recusadas}")
    assert recusadas == list(MUTACOES_DE_GRAFO)
    assert [n.id for n in arvore.nos] == [a.id, b.id]
    assert [x.id for x in arvore.arestas] == [elo.id]


def test_o_projeto_generico_nao_perde_nada_porque_ele_e_a_propria_raiz():
    """A trava é por FERRAMENTA. No M1 genérico o `Projeto` é a raiz, e nada muda."""
    projeto = Projeto(
        id=uuid4(), dono=DONA, nome="Rascunho livre", criado_em=T0, alterado_em=T0
    )
    assert projeto.ferramenta == FERRAMENTA_GENERICA

    a = projeto.adicionar_no(titulo=BOM, em=T0)
    b = projeto.adicionar_no(titulo=OUTRO, em=T0)
    elo = projeto.ligar(a.id, b.id, em=T0)
    projeto.editar_no(a.id, titulo=OUTRO, em=T0)
    projeto.mover_no(a.id, PosicaoNoCanvas(5.0, 6.0), em=T0)
    projeto.recolher_no(a.id, True, em=T0)
    projeto.editar_aresta(elo.id, "porque", em=T0)
    projeto.excluir_aresta(elo.id, em=T0)
    projeto.excluir_no(a.id, em=T0)

    assert [n.id for n in projeto.nos] == [b.id]
    assert projeto.arestas == ()


def test_ferramenta_nova_nasce_FECHADA_mesmo_sem_se_registrar():
    """Fail-closed é o ponto: quem esquece de registrar fica bloqueado, nunca liberado.

    Este é o teste que distingue a correção de um remendo. Se a trava dependesse da
    tabela `RAIZ_POR_FERRAMENTA`, a sétima ferramenta da TOC nasceria com a porta dos
    fundos aberta e ninguém perceberia até a próxima revisão independente.
    """
    # A ferramenta usada aqui tem de ser uma que AINDA não existe no repositório: era
    # `arf` até o ciclo 008 entregar a Árvore da Realidade Futura, e passa a ser `snt` —
    # Estratégia & Táticas, o M5 do ciclo 010. O que o teste prova não mudou: ferramenta
    # não registrada nasce **fechada**.
    futura = "snt"  # Estratégia & Táticas — ainda não existe neste repositório
    assert futura not in RAIZ_POR_FERRAMENTA
    assert tem_raiz_propria(futura) is True
    projeto = Projeto(
        id=uuid4(), dono=DONA, nome="ARF do futuro", ferramenta=futura,
        criado_em=T0, alterado_em=T0,
    )

    with pytest.raises(MutacaoForaDaRaiz) as recusa:
        projeto.adicionar_no(titulo=BOM, em=T0)

    assert recusa.value.ferramenta == futura
    assert recusa.value.raiz == raiz_da_ferramenta(futura)
    assert projeto.nos == ()


def test_as_duas_raizes_de_ferramenta_estao_registradas_com_o_proprio_nome():
    """A tabela empresta o NOME à recusa; um nome errado manda o cliente para a porta errada."""
    print(f"raízes registradas: {RAIZ_POR_FERRAMENTA}")
    assert RAIZ_POR_FERRAMENTA[FERRAMENTA_ARA] == ProjetoARA.__name__
    assert RAIZ_POR_FERRAMENTA[FERRAMENTA_NC] == NuvemDeConflito.__name__
    assert FERRAMENTA_GENERICA not in RAIZ_POR_FERRAMENTA


# -- a raiz continua conseguindo tudo o que precisa ------------------------------------


def test_a_nuvem_edita_entidade_por_dentro_da_raiz_e_a_leitura_acompanha():
    nc = nuvem()

    nc.editar_entidade(PapelDaEntidade.A, "Sustentabilidade da Horizonte", em=T0)

    assert nc.texto(PapelDaEntidade.A) == "Sustentabilidade da Horizonte"
    assert "Sustentabilidade da Horizonte" in nc.leitura(ChaveDaAresta.A_B)


def test_a_ara_exclui_aresta_pela_raiz_e_solta_o_conector_que_a_citava():
    """RN-11: aresta que some leva junto o conector — a operação que faltava à raiz."""
    arvore = ara()
    c1 = arvore.adicionar_efeito(titulo="Os formulários chegam incompletos.", em=T0)
    c2 = arvore.adicionar_efeito(titulo="O volume de pedidos dobra em janeiro.", em=T0)
    destino = arvore.adicionar_efeito(titulo=BOM, em=T0)
    e1 = arvore.ligar(c1.id, destino.id, em=T0)
    e2 = arvore.ligar(c2.id, destino.id, em=T0)
    arvore.formar_conector_e((e1.id, e2.id), em=T0)

    arvore.excluir_aresta(e1.id, em=T0)

    vivas = {x.id for x in arvore.arestas}
    print(f"arestas vivas: {sorted(map(str, vivas))}; conectores: {len(arvore.conectores)}")
    assert vivas == {e2.id}
    # Sobrou uma aresta só na conjunção: o conector inteiro sai, nunca fica meio conector.
    assert arvore.conectores == ()


def test_a_ara_editando_o_titulo_de_um_ude_pela_raiz_REVALIDA():
    """RF-10 sem porta alternativa: não há caminho que troque o texto e mantenha o veredito."""
    arvore = ara()
    no = arvore.adicionar_efeito(titulo=BOM, em=T0)
    arvore.marcar_ude(no.id, em=T0)
    assert arvore.validacao(no.id).aprovado_nos_decidiveis is True

    arvore.editar_no(no.id, titulo="Falta um sistema integrado de matrícula.", em=T0)

    assert arvore.validacao(no.id).aprovado_nos_decidiveis is False


def test_a_chave_da_raiz_e_reentrante():
    """Uma raiz chama outra operação sua por dentro — por isso é contador, não booleano."""
    nc = nuvem()
    with nc.projeto.sob_a_raiz() as fora:
        with fora.sob_a_raiz() as dentro:
            dentro.editar_no(nc.entidade(PapelDaEntidade.B).id, titulo="Receita nova", em=T0)
        # ainda dentro do `with` externo: a chave não pode ter sido devolvida cedo demais
        fora.editar_no(nc.entidade(PapelDaEntidade.C).id, titulo="Reputação", em=T0)

    assert nc.texto(PapelDaEntidade.B) == "Receita nova"
    assert nc.texto(PapelDaEntidade.C) == "Reputação"
    with pytest.raises(MutacaoForaDaRaiz):
        nc.projeto.editar_no(nc.entidade(PapelDaEntidade.A).id, titulo="tarde demais", em=T0)
