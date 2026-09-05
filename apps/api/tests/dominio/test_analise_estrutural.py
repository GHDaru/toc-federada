"""M2 — a análise estrutural da árvore como FUNÇÃO PURA (spec 005, E2.2/F2.2.4).

O prompt `ANALYZE_TREE_PROMPT_TEXT` da linhagem (`tocbuilderv3/constants.ts:83-107`)
pedia a um modelo de linguagem o que é leitura de grafo: fragmentos, nós soltos, o que
não leva a Efeito Indesejável (UDE) nenhum, conexões faltantes. O que é **estrutural**
disso é computável sem rede e sem modelo, e é o RF-26. O que é interpretativo continua
sendo julgamento, e vira ação do catálogo no ciclo 006 — não entra aqui.

Cobre: fragmentos, nós de entrada, alcance transitivo sobre os UDEs, UDEs não alcançados
(RF-28), elos não examinados, nós órfãos, ciclos (RF-29) e causa raiz candidata (RF-27,
RN-12) — que o sistema **aponta** e o humano **conclui**.
"""
from datetime import datetime, timezone
from uuid import uuid4

from toc_api.dominio.ara import EstadoDoExame, novo_projeto_ara
from toc_api.dominio.identidade import DonoDoProjeto

DONO = DonoDoProjeto(inquilino_id="inq-horizonte", usuario_id="usr-facilitadora")
T0 = datetime(2026, 9, 5, 12, 0, tzinfo=timezone.utc)


def nova_ara():
    return novo_projeto_ara(id=uuid4(), dono=DONO, nome="Horizonte — ARA", em=T0)


def arvore_da_horizonte():
    """Uma ARA pequena e determinística:

        raiz ──▶ meio ──▶ UDE-1
          │                 ▲
          └──────────────▶ UDE-2
        entrada_pobre ──▶ UDE-2
        solto (órfão, sem elo nenhum)
    """
    ara = nova_ara()
    raiz = ara.adicionar_efeito(titulo="A conferência de matrícula é manual.", em=T0)
    meio = ara.adicionar_efeito(titulo="A fila de conferência tem 200 pedidos.", em=T0)
    ude1 = ara.adicionar_efeito(
        titulo="O intervalo médio da matrícula até a primeira aula é de 43 dias.", em=T0
    )
    ude2 = ara.adicionar_efeito(
        titulo="A taxa de conclusão dos cursos técnicos é de 54%.", em=T0
    )
    pobre = ara.adicionar_efeito(titulo="O portal cai duas vezes por mês.", em=T0)
    solto = ara.adicionar_efeito(titulo="A biblioteca abre às 8 horas.", em=T0)
    ara.marcar_ude(ude1.id, em=T0)
    ara.marcar_ude(ude2.id, em=T0)
    ara.ligar(raiz.id, meio.id, em=T0)
    ara.ligar(meio.id, ude1.id, em=T0)
    ara.ligar(raiz.id, ude2.id, em=T0)
    ara.ligar(pobre.id, ude2.id, em=T0)
    return ara, dict(raiz=raiz, meio=meio, ude1=ude1, ude2=ude2, pobre=pobre, solto=solto)


def test_entradas_sao_os_nos_sem_antecessor():
    ara, n = arvore_da_horizonte()
    relatorio = ara.analisar(em=T0)
    assert set(relatorio.entradas) == {n["raiz"].id, n["pobre"].id, n["solto"].id}


def test_no_orfao_e_apontado_por_nome_proprio():
    """O nó que não participa de aresta nenhuma — a mesma checagem de `medir-base.py`."""
    ara, n = arvore_da_horizonte()
    relatorio = ara.analisar(em=T0)
    assert relatorio.orfaos == (n["solto"].id,)


def test_fragmentos_sao_os_componentes_desconexos():
    ara, n = arvore_da_horizonte()
    relatorio = ara.analisar(em=T0)
    tamanhos = sorted(len(f) for f in relatorio.fragmentos)
    assert tamanhos == [1, 5]
    assert (n["solto"].id,) in relatorio.fragmentos


def test_alcance_de_cada_entrada_sobre_os_udes():
    ara, n = arvore_da_horizonte()
    relatorio = ara.analisar(em=T0)
    alcance = {a.no_id: a for a in relatorio.alcances}
    assert set(alcance[n["raiz"].id].udes_alcancados) == {n["ude1"].id, n["ude2"].id}
    assert alcance[n["raiz"].id].fracao == 1.0
    assert set(alcance[n["pobre"].id].udes_alcancados) == {n["ude2"].id}
    assert alcance[n["pobre"].id].fracao == 0.5
    assert alcance[n["solto"].id].udes_alcancados == ()


def test_causa_raiz_candidata_e_a_entrada_que_alcanca_mais_udes():
    """RN-12: o sistema APONTA; o humano conclui. É sugestão nomeada, não veredito."""
    ara, n = arvore_da_horizonte()
    relatorio = ara.analisar(em=T0)
    assert relatorio.causa_raiz_candidata == n["raiz"].id
    assert relatorio.causas_raiz_candidatas == (n["raiz"].id,)


def test_empate_nao_vira_conclusao_automatica():
    """Duas entradas com o mesmo alcance: o relatório lista as duas e não escolhe."""
    ara = nova_ara()
    a = ara.adicionar_efeito(titulo="A conferência de matrícula é manual.", em=T0)
    b = ara.adicionar_efeito(titulo="O portal cai duas vezes por mês.", em=T0)
    ude = ara.adicionar_efeito(titulo="A taxa de conclusão é de 54%.", em=T0)
    ara.marcar_ude(ude.id, em=T0)
    ara.ligar(a.id, ude.id, em=T0)
    ara.ligar(b.id, ude.id, em=T0)
    relatorio = ara.analisar(em=T0)
    assert set(relatorio.causas_raiz_candidatas) == {a.id, b.id}
    assert relatorio.causa_raiz_candidata is None


def test_udes_nao_alcancados_medem_o_que_a_arvore_ainda_nao_explica():
    """RF-28: a fração da dor percebida que a árvore ainda não explica."""
    ara, n = arvore_da_horizonte()
    orfa = ara.adicionar_efeito(titulo="A evasão no primeiro semestre é de 31%.", em=T0)
    ara.marcar_ude(orfa.id, em=T0)
    relatorio = ara.analisar(em=T0)
    assert relatorio.udes_nao_alcancados == (orfa.id,)


def test_elos_nao_examinados_sao_listados():
    ara, n = arvore_da_horizonte()
    elo = ara.arestas[0]
    ara.examinar_elo(elo.id, EstadoDoExame.SUFICIENTE, em=T0)
    relatorio = ara.analisar(em=T0)
    assert elo.id not in relatorio.elos_nao_examinados
    assert len(relatorio.elos_nao_examinados) == len(ara.arestas) - 1


def test_ciclo_e_listado_e_seus_nos_ficam_fora_da_causa_raiz_candidata():
    """RF-29: laço de reforço é legítimo na TOC — o relatório o lista e o exclui do cálculo.

    Sem o ciclo, `a` seria a entrada de maior alcance. Com o ciclo, `a` deixa de ser
    entrada (passa a ter antecessor) e o relatório diz isso em vez de escondê-lo.
    """
    ara = nova_ara()
    a = ara.adicionar_efeito(titulo="A conferência de matrícula é manual.", em=T0)
    b = ara.adicionar_efeito(titulo="A fila de conferência tem 200 pedidos.", em=T0)
    ude = ara.adicionar_efeito(titulo="A taxa de conclusão é de 54%.", em=T0)
    fora = ara.adicionar_efeito(titulo="O portal cai duas vezes por mês.", em=T0)
    ara.marcar_ude(ude.id, em=T0)
    ara.ligar(a.id, b.id, em=T0)
    ara.ligar(b.id, a.id, em=T0)  # o laço de reforço
    ara.ligar(b.id, ude.id, em=T0)
    ara.ligar(fora.id, ude.id, em=T0)

    relatorio = ara.analisar(em=T0)

    assert len(relatorio.ciclos) == 1
    assert set(relatorio.ciclos[0]) == {a.id, b.id}
    assert relatorio.nos_em_ciclo == frozenset({a.id, b.id})
    assert relatorio.causa_raiz_candidata == fora.id
    assert relatorio.observacoes  # o relatório DIZ que excluiu os ciclos do cálculo


def test_analise_nao_muta_nada_e_emite_o_evento_com_o_resumo():
    ara, _ = arvore_da_horizonte()
    antes = (len(ara.nos), len(ara.arestas))
    ara.drenar_eventos()
    relatorio = ara.analisar(em=T0)
    assert (len(ara.nos), len(ara.arestas)) == antes
    evento = ara.eventos[-1]
    assert type(evento).__name__ == "AnaliseEstruturalGerada"
    assert evento.resumo["nos"] == antes[0]
    assert evento.resumo["udes"] == 2
    assert evento.resumo["ciclos"] == 0
    assert relatorio.resumo() == evento.resumo


def test_analise_de_arvore_vazia_nao_explode():
    ara = nova_ara()
    relatorio = ara.analisar(em=T0)
    assert relatorio.entradas == ()
    assert relatorio.causa_raiz_candidata is None
    assert relatorio.resumo()["nos"] == 0
