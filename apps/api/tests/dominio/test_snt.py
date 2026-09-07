"""M5 — a Árvore de Estratégia & Táticas (S&T): estrutura hierárquica (spec 010, E5.1).

Siglas, uma vez neste arquivo: **S&T** — Estratégia & Táticas (*Strategy & Tactics*) ·
**M1** — Núcleo de Diagramas Lógicos · **M5** — o módulo da S&T · **TOC** — Teoria das
Restrições · **RF/RN** — requisito funcional / regra de negócio da spec 010.

Três defeitos medidos da linhagem viram caso de teste aqui, e são o motivo do arquivo:

1. **Número digitado à mão** (`tocbuilderv3/types.ts:288` e
   `tocbuilderv3/components/SnTStepEditorModal.tsx:56-57`): aqui não existe parâmetro de
   número em operação nenhuma — a assinatura é a prova (RF-06, RN-01).
2. **Aresta livre reusada "por simplicidade"** (`tocbuilderv3/types.ts:310`): aqui a
   árvore é estrita, e mover para a própria subárvore é recusado no domínio (RN-04).
3. **Excluir um passo descartava todos os outros**
   (`tocbuilderv3/services/mockApiService.ts:521` — `filter(n => n.id === nodeId)`
   mantinha SÓ o nó excluído): aqui a exclusão remove a subárvore exata, e o teste compara
   os demais passos campo a campo antes e depois (RN-05).

Base sintética (ADR 0006): "Instituição Horizonte", personas fictícias.
"""
from __future__ import annotations

from uuid import UUID, uuid4

import pytest

from toc_api.dominio.erros import (
    DadoInvalido,
    MutacaoForaDaRaiz,
    MutacaoRecusada,
)
from toc_api.dominio.eventos import (
    ArvoreSnTCriada,
    MetaGlobalEditada,
    PassoDaSnTAdicionado,
    PassoDaSnTMovido,
    SubarvoreExcluida,
)
from toc_api.dominio.snt import (
    FERRAMENTA_SNT,
    TIPO_DE_NO_PASSO,
    ArvoreSnT,
    CategoriaDoPasso,
    MovimentoRecusado,
    PassoInvalido,
    StatusDoPasso,
    nova_arvore_snt,
    reidratar_snt,
)

from .snt_sintetica import AGORA, DONO, ID_DA_ARVORE, META_GLOBAL, NOME, PLANO


def arvore() -> ArvoreSnT:
    a = nova_arvore_snt(
        id=ID_DA_ARVORE, dono=DONO, nome=NOME, meta_global=META_GLOBAL, em=AGORA
    )
    a.drenar_eventos()
    return a


def plano_completo() -> tuple[ArvoreSnT, dict[str, UUID]]:
    """A S&T sintética de TRÊS níveis — o portão do roadmap para o ciclo 010."""
    a = arvore()
    por_chave: dict[str, UUID] = {}
    for chave, pai, estrategia, tatica in PLANO:
        no = a.adicionar_passo(
            estrategia=estrategia,
            tatica=tatica,
            pai_id=None if pai is None else por_chave[pai],
            em=AGORA,
        )
        por_chave[chave] = no.id
    a.drenar_eventos()
    return a, por_chave


# ---------------------------------------------------------------------------------------
# F5.1.1 · o projeto S&T com meta global (RF-01, RF-02)
# ---------------------------------------------------------------------------------------


def test_a_arvore_nasce_vazia_com_a_ferramenta_propria_e_a_meta_no_topo() -> None:
    a = nova_arvore_snt(
        id=ID_DA_ARVORE, dono=DONO, nome=NOME, meta_global=META_GLOBAL, em=AGORA
    )
    print(f"ferramenta={a.projeto.ferramenta!r} passos={len(a.passos)}")
    assert a.projeto.ferramenta == FERRAMENTA_SNT
    assert a.passos == ()
    assert a.meta_global == META_GLOBAL
    assert [type(e).__name__ for e in a.eventos] == [ArvoreSnTCriada.__name__]


def test_a_arvore_recusa_nascer_sem_meta_global() -> None:
    """RF-01: a meta global é obrigatória — S&T sem alvo não decompõe coisa nenhuma."""
    with pytest.raises(DadoInvalido) as erro:
        nova_arvore_snt(id=ID_DA_ARVORE, dono=DONO, nome=NOME, meta_global="  ", em=AGORA)
    print(f"recusa: {erro.value}")


def test_editar_a_meta_global_tem_evento_proprio() -> None:
    a = arvore()
    a.editar_meta_global("Dobrar a capacidade em dezoito meses", em=AGORA)
    print(f"eventos={[type(e).__name__ for e in a.eventos]}")
    assert [type(e).__name__ for e in a.eventos] == [MetaGlobalEditada.__name__]
    assert a.meta_global == "Dobrar a capacidade em dezoito meses"


def test_o_projeto_da_snt_recusa_mutacao_que_nao_venha_pela_raiz() -> None:
    """A porta dos fundos do agregado não existe: quem tenta, ouve o nome da raiz certa."""
    a = arvore()
    with pytest.raises(MutacaoForaDaRaiz) as erro:
        a.projeto.adicionar_no(titulo="por fora", em=AGORA)
    print(f"recusa: raiz={erro.value.raiz!r} ferramenta={erro.value.ferramenta!r}")
    assert erro.value.raiz == "ArvoreSnT"


def test_a_arvore_recusa_embrulhar_projeto_de_outra_ferramenta() -> None:
    from toc_api.dominio.projeto import Projeto

    projeto = Projeto(
        id=ID_DA_ARVORE, dono=DONO, nome=NOME, ferramenta="ara", criado_em=AGORA,
        alterado_em=AGORA,
    )
    with pytest.raises(MutacaoRecusada) as erro:
        ArvoreSnT(projeto=projeto, meta_global=META_GLOBAL)
    print(f"recusa: {erro.value}")


def test_projeto_excluido_recusa_toda_mutacao_do_modulo() -> None:
    a, chaves = plano_completo()
    a.projeto.excluir(em=AGORA)
    for operacao in (
        lambda: a.adicionar_passo(estrategia="depois da exclusão", em=AGORA),
        lambda: a.editar_meta_global("outra meta", em=AGORA),
        lambda: a.excluir_subarvore(chaves["1.1"], em=AGORA),
        lambda: a.mudar_status(
            chaves["1.1"], StatusDoPasso.VALIDADO, autor="u-gestora", em=AGORA
        ),
    ):
        with pytest.raises(MutacaoRecusada):
            operacao()
    print("4 mutações recusadas sobre projeto excluído")


# ---------------------------------------------------------------------------------------
# F5.1.2 · numeração derivada e renumeração (RF-04..RF-07, RN-01)
# ---------------------------------------------------------------------------------------


def test_a_arvore_sintetica_de_tres_niveis_numera_como_o_plano_declara() -> None:
    a, chaves = plano_completo()
    obtidos = {chave: a.numero(no_id) for chave, no_id in chaves.items()}
    print(f"numeração obtida: {obtidos}")
    assert obtidos == {chave: chave for chave in chaves}
    assert a.numero(chaves["1.1.2"]) == "1.1.2"


def test_nenhuma_operacao_de_escrita_aceita_numero_de_passo() -> None:
    """RF-06: numeração é saída, nunca entrada — a assinatura é a prova executável."""
    import inspect

    proibidos = {"numero", "numero_do_passo", "step_number", "stepnumber"}
    achados = []
    for nome, metodo in inspect.getmembers(ArvoreSnT, predicate=inspect.isfunction):
        if nome.startswith("_"):
            continue
        for parametro in inspect.signature(metodo).parameters:
            if parametro.lower().replace("_", "") in {p.replace("_", "") for p in proibidos}:
                achados.append(f"{nome}({parametro})")
    print(f"métodos públicos examinados: {len([m for m in dir(ArvoreSnT) if not m.startswith('_')])}"
          f" · parâmetros de número encontrados: {len(achados)}")
    assert achados == []


def test_o_terceiro_filho_nasce_como_um_ponto_um_ponto_tres() -> None:
    """US-03: dado 1.1 com dois filhos, o terceiro nasce 1.1.3 — sem campo de número."""
    a, chaves = plano_completo()
    novo = a.adicionar_passo(
        estrategia="Encurtar a triagem inicial",
        tatica="Triar por formulário assíncrono",
        pai_id=chaves["1.1"],
        em=AGORA,
    )
    print(f"novo passo numerado como {a.numero(novo.id)}")
    assert a.numero(novo.id) == "1.1.3"
    evento = [e for e in a.eventos if isinstance(e, PassoDaSnTAdicionado)][-1]
    assert evento.numero == "1.1.3" and evento.pai_id == chaves["1.1"]


def test_inserir_no_meio_dos_irmaos_empurra_os_seguintes_sem_lacuna() -> None:
    a, chaves = plano_completo()
    novo = a.adicionar_passo(
        estrategia="Mapear o fluxo atual ponta a ponta",
        pai_id=chaves["1"],
        posicao=0,
        em=AGORA,
    )
    numeros = {a.numero(chaves["1.1"]), a.numero(chaves["1.2"]), a.numero(chaves["1.3"])}
    print(f"novo={a.numero(novo.id)} · antigos agora={sorted(numeros)}")
    assert a.numero(novo.id) == "1.1"
    assert numeros == {"1.2", "1.3", "1.4"}
    # E os netos acompanham o pai: o prefixo novo desce inteiro (RF-07).
    assert a.numero(chaves["1.1.1"]) == "1.2.1"
    assert a.numero(chaves["1.1.2"]) == "1.2.2"


def test_posicao_fora_da_faixa_de_irmaos_e_recusada() -> None:
    a, chaves = plano_completo()
    for posicao in (-1, 99):
        with pytest.raises(DadoInvalido) as erro:
            a.adicionar_passo(estrategia="fora da faixa", pai_id=chaves["1"], posicao=posicao, em=AGORA)
        print(f"posicao={posicao} recusada: {erro.value}")


def test_adicionar_passo_sob_pai_inexistente_e_recusado() -> None:
    a = arvore()
    with pytest.raises(PassoInvalido) as erro:
        a.adicionar_passo(estrategia="órfão", pai_id=uuid4(), em=AGORA)
    print(f"recusa: regra={erro.value.regra!r}")
    assert erro.value.regra == "pai_inexistente"


def test_o_passo_exige_estrategia_e_admite_tatica_vazia() -> None:
    """RF-11: estratégia obrigatória; tática nasce vazia e vira pendência, não bloqueio."""
    a = arvore()
    with pytest.raises(DadoInvalido):
        a.adicionar_passo(estrategia="   ", em=AGORA)
    no = a.adicionar_passo(estrategia="Sustentar a demanda nova", em=AGORA)
    print(f"passo criado sem tática: tatica={a.ficha(no.id).tatica!r}")
    assert a.ficha(no.id).tatica == ""
    assert no.tipo == TIPO_DE_NO_PASSO


# ---------------------------------------------------------------------------------------
# RF-08 / RN-04 · mover a subárvore, e a árvore estrita
# ---------------------------------------------------------------------------------------


def test_mover_leva_a_subarvore_inteira_e_renumera_os_dois_lados() -> None:
    """US-04: 1.2 vira 2.1 debaixo do 2 — e os filhos viram 2.1.1 e 2.1.2."""
    a, chaves = plano_completo()
    segunda_frente = a.adicionar_passo(estrategia="Abrir a segunda frente", em=AGORA)
    assert a.numero(segunda_frente.id) == "2"

    a.mover_passo(chaves["1.1"], novo_pai_id=segunda_frente.id, em=AGORA)

    print(
        "depois do mover: "
        f"1.1→{a.numero(chaves['1.1'])} · filhos {a.numero(chaves['1.1.1'])} e "
        f"{a.numero(chaves['1.1.2'])} · irmãos antigos {a.numero(chaves['1.2'])} e "
        f"{a.numero(chaves['1.3'])}"
    )
    assert a.numero(chaves["1.1"]) == "2.1"
    assert a.numero(chaves["1.1.1"]) == "2.1.1"
    assert a.numero(chaves["1.1.2"]) == "2.1.2"
    # Os antigos irmãos renumeram sem lacuna.
    assert a.numero(chaves["1.2"]) == "1.1"
    assert a.numero(chaves["1.3"]) == "1.2"


def test_mover_preserva_estrategia_tatica_premissas_e_status_de_cada_descendente() -> None:
    a, chaves = plano_completo()
    a.editar_premissas(chaves["1.1.1"], paralela="o painel já existe em outra área", em=AGORA)
    a.mudar_status(chaves["1.1.1"], StatusDoPasso.VALIDADO, autor="u-gestora", em=AGORA)
    antes = {no_id: a.ficha(no_id) for no_id in (chaves["1.1"], chaves["1.1.1"], chaves["1.1.2"])}

    destino = a.adicionar_passo(estrategia="Abrir a segunda frente", em=AGORA)
    a.mover_passo(chaves["1.1"], novo_pai_id=destino.id, em=AGORA)

    depois = {no_id: a.ficha(no_id) for no_id in antes}
    print(f"fichas comparadas: {len(antes)} · iguais: {sum(antes[k] == depois[k] for k in antes)}")
    assert antes == depois


def test_mover_para_a_propria_subarvore_e_recusado_no_dominio() -> None:
    """RN-04: ciclo é impossível por construção — a única recusa necessária."""
    a, chaves = plano_completo()
    for alvo, destino in (
        (chaves["1"], chaves["1.1.1"]),
        (chaves["1.1"], chaves["1.1"]),
    ):
        with pytest.raises(MovimentoRecusado) as erro:
            a.mover_passo(alvo, novo_pai_id=destino, em=AGORA)
        print(f"recusa: motivo={erro.value.motivo!r}")
        assert erro.value.motivo == "para_a_propria_subarvore"
    # E nada mudou: a árvore continua com a numeração de antes.
    assert a.numero(chaves["1.1.1"]) == "1.1.1"


def test_arvore_estrita_todo_passo_tem_no_maximo_um_pai_e_nenhuma_aresta() -> None:
    a, chaves = plano_completo()
    pais = {no_id: a.pai(no_id) for no_id in chaves.values()}
    print(f"passos={len(pais)} · arestas no projeto={len(a.projeto.arestas)}")
    assert a.projeto.arestas == ()
    assert sum(1 for pai in pais.values() if pai is None) == 1
    assert all(not isinstance(pai, (list, tuple)) for pai in pais.values())


def test_mover_para_raiz_e_para_posicao_entre_irmaos() -> None:
    a, chaves = plano_completo()
    a.mover_passo(chaves["1.1"], novo_pai_id=None, posicao=0, em=AGORA)
    print(f"promovido a raiz: {a.numero(chaves['1.1'])} · o antigo 1 virou {a.numero(chaves['1'])}")
    assert a.numero(chaves["1.1"]) == "1"
    assert a.numero(chaves["1"]) == "2"
    assert a.numero(chaves["1.1.1"]) == "1.1"


def test_o_evento_de_mover_carrega_os_numeros_de_antes_e_de_depois() -> None:
    a, chaves = plano_completo()
    destino = a.adicionar_passo(estrategia="Abrir a segunda frente", em=AGORA)
    a.drenar_eventos()
    a.mover_passo(chaves["1.1"], novo_pai_id=destino.id, em=AGORA)
    evento = [e for e in a.eventos if isinstance(e, PassoDaSnTMovido)][0]
    print(f"evento: {evento.numero_anterior} → {evento.numero_novo} ({evento.descendentes} descendentes)")
    assert (evento.numero_anterior, evento.numero_novo) == ("1.1", "2.1")
    assert evento.descendentes == 2


# ---------------------------------------------------------------------------------------
# RF-09 / RN-05 · exclusão de subárvore — o defeito F-07 da linhagem como caso de teste
# ---------------------------------------------------------------------------------------


def test_exclusao_subarvore_remove_exatamente_a_subarvore_e_nao_toca_no_resto() -> None:
    """O contraexemplo é `tocbuilderv3/services/mockApiService.ts:521`.

    Lá, `project.nodes = project.nodes.filter(n => n.id === nodeId)` mantinha SÓ o nó
    excluído e descartava todos os outros passos do projeto. Aqui o teste compara os
    demais passos campo a campo, antes e depois — não "parece igual".
    """
    a, chaves = plano_completo()
    fora_da_subarvore = [c for c in chaves if not c.startswith("1.1")]
    antes = {
        chave: (a.ficha(chaves[chave]), a.projeto.no(chaves[chave]))
        for chave in fora_da_subarvore
    }

    removidos = a.excluir_subarvore(chaves["1.1"], em=AGORA)

    depois = {
        chave: (a.ficha(chaves[chave]), a.projeto.no(chaves[chave]))
        for chave in fora_da_subarvore
    }
    print(
        f"excluídos: {len(removidos)} · passos fora da subárvore comparados: {len(antes)}"
        f" · idênticos: {sum(antes[c] == depois[c] for c in antes)}"
    )
    assert len(removidos) == 3  # 1.1 + 1.1.1 + 1.1.2
    assert antes == depois
    assert len(a.passos) == len(PLANO) - 3
    for chave in ("1.1", "1.1.1", "1.1.2"):
        with pytest.raises(PassoInvalido):
            a.ficha(chaves[chave])


def test_a_exclusao_avisa_a_contagem_antes_e_o_evento_a_repete() -> None:
    """US-05/RF-09: "5 passos serão excluídos" é consulta ANTES de confirmar."""
    a, chaves = plano_completo()
    quantos = a.contar_subarvore(chaves["1"])
    print(f"contar_subarvore(1) = {quantos} · passos na árvore = {len(a.passos)}")
    assert quantos == len(PLANO)

    a.excluir_subarvore(chaves["1.1"], em=AGORA)
    evento = [e for e in a.eventos if isinstance(e, SubarvoreExcluida)][0]
    print(f"evento: numero={evento.numero!r} passos_excluidos={evento.passos_excluidos}")
    assert evento.passos_excluidos == 3
    assert evento.numero == "1.1"


def test_excluir_renumera_os_irmaos_seguintes_sem_lacuna() -> None:
    a, chaves = plano_completo()
    a.excluir_subarvore(chaves["1.1"], em=AGORA)
    print(f"depois da exclusão: 1.2→{a.numero(chaves['1.2'])} · 1.3→{a.numero(chaves['1.3'])}")
    assert a.numero(chaves["1.2"]) == "1.1"
    assert a.numero(chaves["1.3"]) == "1.2"


def test_a_numeracao_esquece_os_passos_que_sairam_da_arvore() -> None:
    """Achado da mutação (TAIL:mutation, ciclo 010): número órfão é número fantasma.

    A mutação `renumerar-nao-descarta-o-que-saiu` — trocar o filtro por `dict(numeros)` —
    passava por toda a suíte: `numero()` exige a ficha antes, e a ficha do excluído já não
    existe. O mapa devolvido por `numeros()`, porém, é público, e continuava carregando o
    número de passos que não estão mais na árvore. Este é o teste que faltava.
    """
    a, chaves = plano_completo()
    removidos = a.excluir_subarvore(chaves["1.1"], em=AGORA)
    numeros = a.numeros()
    print(f"removidos={len(removidos)} · chaves no mapa de numeração={len(numeros)}")
    assert set(numeros) & set(removidos) == set()
    assert len(numeros) == len(a.passos)


def test_excluir_passo_inexistente_e_recusado() -> None:
    a, _ = plano_completo()
    with pytest.raises(PassoInvalido):
        a.excluir_subarvore(uuid4(), em=AGORA)


# ---------------------------------------------------------------------------------------
# RF-19 / RF-21 · vista tabular e exportação sem número
# ---------------------------------------------------------------------------------------


def test_a_vista_tabular_sai_em_ordem_estrutural_com_nivel_e_numero() -> None:
    a, chaves = plano_completo()
    linhas = a.linhas()
    print(f"linhas={[ (l.numero, l.nivel) for l in linhas ]}")
    assert [linha.numero for linha in linhas] == [c for c, _, _, _ in PLANO]
    assert [linha.nivel for linha in linhas] == [0, 1, 2, 2, 1, 2, 1]
    assert linhas[1].tem_premissa_de_necessidade is False


def test_a_exportacao_nao_carrega_numero_e_a_ida_e_volta_preserva_a_estrutura() -> None:
    """RF-21: a numeração deriva na importação; divergência é impossível."""
    import json

    from toc_api.dominio.snt import exportar_arvore_snt, importar_arvore_snt

    a, chaves = plano_completo()
    a.editar_premissas(chaves["1.1"], necessidade_ao_pai="sem cortar a espera, a fila dobra", em=AGORA)
    a.mudar_status(chaves["1.1"], StatusDoPasso.EM_EXECUCAO, autor="u-gestora", em=AGORA)

    documento = exportar_arvore_snt(a)
    bruto = json.dumps(documento, ensure_ascii=False)
    print(f"documento com {len(documento['passos'])} passos · {len(bruto)} bytes")
    assert "numero" not in bruto and "stepNumber" not in bruto

    volta = importar_arvore_snt(documento, id=uuid4(), dono=DONO)
    numeros_originais = [a.numero(no.id) for no in a.passos]
    numeros_importados = [volta.numero(no.id) for no in volta.passos]
    print(f"números originais={numeros_originais} · importados={numeros_importados}")
    assert numeros_originais == numeros_importados
    assert [a.ficha(no.id) for no in a.passos] == [volta.ficha(no.id) for no in volta.passos]
    assert volta.meta_global == a.meta_global


def test_a_importacao_recusa_versao_desconhecida() -> None:
    from toc_api.dominio.snt import importar_arvore_snt

    with pytest.raises(DadoInvalido) as erro:
        importar_arvore_snt({"versao": "toc.snt/99", "passos": []}, id=uuid4(), dono=DONO)
    print(f"recusa: {erro.value}")


def test_reidratar_nao_emite_evento_e_recalcula_a_numeracao() -> None:
    a, chaves = plano_completo()
    volta = reidratar_snt(
        a.projeto,
        meta_global=a.meta_global,
        fichas=dict(a.fichas()),
        estrutura=a.estrutura(),
    )
    print(f"eventos após reidratar: {len(volta.eventos)} · numeração: {volta.numero(chaves['1.1.2'])}")
    assert volta.eventos == ()
    assert volta.numero(chaves["1.1.2"]) == "1.1.2"


# ---------------------------------------------------------------------------------------
# RF-11 · categoria portada da linhagem — opcional, e nunca substitui os dois campos
# ---------------------------------------------------------------------------------------


def test_a_categoria_da_linhagem_e_opcional_e_carrega_os_seis_valores() -> None:
    """ADR 0014: `SnTStepCategory` (`tocbuilderv3/types.ts:277-284`) entra como rótulo."""
    a = arvore()
    no = a.adicionar_passo(
        estrategia="Sustentar a demanda nova",
        categoria=CategoriaDoPasso.VCD,
        em=AGORA,
    )
    padrao = a.adicionar_passo(estrategia="Sem rótulo", em=AGORA)
    print(
        f"valores={[c.value for c in CategoriaDoPasso]} · "
        f"padrão={padrao and a.ficha(padrao.id).categoria.value!r}"
    )
    assert [c.value for c in CategoriaDoPasso] == [
        "nenhuma", "estrategia", "tatica", "vcd", "build", "leverage",
    ]
    assert a.ficha(no.id).categoria is CategoriaDoPasso.VCD
    assert a.ficha(padrao.id).categoria is CategoriaDoPasso.NENHUMA


def test_editar_passo_muda_estrategia_tatica_e_categoria_e_o_titulo_do_no_acompanha() -> None:
    a, chaves = plano_completo()
    ficha = a.editar_passo(
        chaves["1.3"],
        estrategia="Sustentar a demanda sem perder qualidade",
        tatica="Abrir vagas por lote com revisão a cada lote",
        categoria=CategoriaDoPasso.ESTRATEGIA,
        em=AGORA,
    )
    print(f"título do nó={a.projeto.no(chaves['1.3']).titulo!r}")
    assert a.projeto.no(chaves["1.3"]).titulo == ficha.estrategia
    assert ficha.categoria is CategoriaDoPasso.ESTRATEGIA


def test_editar_passo_sem_campo_nenhum_e_recusado() -> None:
    a, chaves = plano_completo()
    with pytest.raises(MutacaoRecusada):
        a.editar_passo(chaves["1"], em=AGORA)


def test_a_ficha_de_passo_inexistente_levanta_erro_nomeado() -> None:
    a, _ = plano_completo()
    with pytest.raises(PassoInvalido) as erro:
        a.ficha(uuid4())
    print(f"recusa: regra={erro.value.regra!r}")
    assert erro.value.regra == "sem_ficha"
