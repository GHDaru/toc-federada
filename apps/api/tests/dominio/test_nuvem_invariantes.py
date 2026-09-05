"""As invariantes da Nuvem de Conflito (NC) — domínio puro, sem rede e sem banco.

Siglas, uma vez: **NC** — Nuvem de Conflito · **TOC** — Teoria das Restrições · **UDE** —
Efeito Indesejável · **ARA** — Árvore da Realidade Atual · **TRIZ** — Teoria da Resolução
Inventiva de Problemas.

O que este arquivo fixa, e que a 4ª geração da linhagem não tinha teste nenhum para fixar:

1. **A nuvem nasce inteira** — 5 entidades e 7 arestas num ato só (RN-01; o acerto de
   `tocbuilderv3/services/mockApiService.ts:17-41`, que criava a estrutura completa na
   origem).
2. **A topologia é indestrutível** — não existe caminho para criar ou excluir entidade ou
   aresta; o vocabulário de mutação é preencher (RF-03).
3. **A chave da aresta e a classe dela são derivadas**, não digitadas (RN-02).
4. **A leitura por extenso** de cada classe sai dos textos ATUAIS das entidades (RF-07).

Nenhum número aqui é transcrito: as contagens são calculadas pelo próprio teste.
"""
from __future__ import annotations

import pytest

from toc_api.dominio.erros import DadoInvalido, MutacaoRecusada
from toc_api.dominio.nuvem import (
    CLASSE_POR_CHAVE,
    FERRAMENTA_NC,
    PAR_DA_ARESTA,
    ChaveDaAresta,
    ClasseDaAresta,
    NuvemDeConflito,
    PapelDaEntidade,
    TopologiaImutavel,
    novo_projeto_nc,
)
from toc_api.dominio.projeto import Projeto

from .nuvem_sintetica import AGORA, DILEMA, DONO, ID_DA_NUVEM, NOME


def nuvem_vazia() -> NuvemDeConflito:
    return novo_projeto_nc(id=ID_DA_NUVEM, dono=DONO, nome=NOME, em=AGORA)


def nuvem_preenchida() -> NuvemDeConflito:
    nuvem = nuvem_vazia()
    for papel, texto in DILEMA.items():
        nuvem.editar_entidade(papel, texto, em=AGORA)
    return nuvem


# --------------------------------------------------------------------------------------
# Topologia fixa (RN-01, RF-02, RF-03)
# --------------------------------------------------------------------------------------


def test_a_nuvem_nasce_com_as_cinco_entidades_e_as_sete_arestas() -> None:
    nuvem = nuvem_vazia()

    medida = (
        f"topologia: {len(nuvem.entidades)} entidade(s), {len(nuvem.arestas)} aresta(s), "
        f"papéis={sorted(p.value for p in nuvem.papeis)}, "
        f"chaves={sorted(c.value for c in nuvem.chaves)}"
    )
    print(medida)

    assert len(nuvem.entidades) == 5, medida
    assert len(nuvem.arestas) == 7, medida
    assert set(nuvem.papeis) == set(PapelDaEntidade), medida
    assert set(nuvem.chaves) == set(ChaveDaAresta), medida
    assert nuvem.projeto.ferramenta == FERRAMENTA_NC


def test_toda_entidade_nasce_com_texto_de_exemplo_neutro_e_nenhuma_vazia() -> None:
    nuvem = nuvem_vazia()

    for papel in PapelDaEntidade:
        assert nuvem.texto(papel).strip(), papel


def test_a_nuvem_nasce_em_um_ato_so_com_um_evento_de_criacao() -> None:
    nuvem = nuvem_vazia()

    tipos = [type(e).__name__ for e in nuvem.eventos]
    print(f"eventos na criação: {tipos}")

    assert tipos.count("NuvemCriada") == 1, tipos


def test_nao_existe_caminho_para_criar_ou_excluir_entidade_ou_aresta() -> None:
    """RF-03: o vocabulário de mutação é preencher — nunca criar nem destruir."""
    nuvem = nuvem_vazia()
    alguma = nuvem.aresta(ChaveDaAresta.A_B)
    alguma_entidade = nuvem.entidade(PapelDaEntidade.A)

    recusas: list[str] = []
    for chamada, acao in (
        (lambda: nuvem.adicionar_entidade(titulo="uma sexta", em=AGORA), "adicionar_entidade"),
        (lambda: nuvem.excluir_entidade(PapelDaEntidade.A, em=AGORA), "excluir_entidade"),
        (
            lambda: nuvem.ligar(alguma_entidade.id, alguma_entidade.id, em=AGORA),
            "ligar",
        ),
        (lambda: nuvem.excluir_aresta(alguma.id, em=AGORA), "excluir_aresta"),
    ):
        with pytest.raises(TopologiaImutavel) as erro:
            chamada()
        recusas.append(f"{acao}→{erro.value.regra}")

    print(f"recusas de topologia examinadas: {recusas}")
    assert len(recusas) == 4, recusas
    assert all(r.endswith("topologia_fixa") for r in recusas), recusas
    # E a recusa é de verdade: a topologia continua inteira depois das quatro tentativas.
    assert (len(nuvem.entidades), len(nuvem.arestas)) == (5, 7)


def test_a_nuvem_recusa_ser_montada_sobre_um_projeto_de_outra_ferramenta() -> None:
    projeto = Projeto(
        id=ID_DA_NUVEM, dono=DONO, nome=NOME, criado_em=AGORA, alterado_em=AGORA,
        ferramenta="ara",
    )

    with pytest.raises(MutacaoRecusada):
        NuvemDeConflito(projeto)


def test_a_nuvem_recusa_ser_montada_sobre_um_projeto_de_topologia_incompleta() -> None:
    """Nuvem incompleta não é válida: faltando entidade ou aresta, o agregado recusa."""
    nuvem = nuvem_vazia()
    projeto = nuvem.projeto
    projeto.nos = projeto.nos[:-1]

    with pytest.raises(TopologiaImutavel) as erro:
        NuvemDeConflito(projeto)
    print(f"regra da recusa: {erro.value.regra}")
    assert erro.value.regra == "topologia_incompleta"


# --------------------------------------------------------------------------------------
# Classe e leitura das arestas (RN-02, RF-07)
# --------------------------------------------------------------------------------------


def test_a_classe_de_cada_aresta_e_derivada_da_chave() -> None:
    esperado = {
        ChaveDaAresta.A_B: ClasseDaAresta.NECESSIDADE,
        ChaveDaAresta.A_C: ClasseDaAresta.NECESSIDADE,
        ChaveDaAresta.B_D: ClasseDaAresta.PRE_REQUISITO,
        ChaveDaAresta.C_D_PRIME: ClasseDaAresta.PRE_REQUISITO,
        ChaveDaAresta.D_C: ClasseDaAresta.PERIGO,
        ChaveDaAresta.D_PRIME_B: ClasseDaAresta.PERIGO,
        ChaveDaAresta.D_D_PRIME: ClasseDaAresta.CONFLITO,
    }

    print(f"classes examinadas: {len(esperado)} de {len(ChaveDaAresta)} chaves")
    assert CLASSE_POR_CHAVE == esperado
    assert set(esperado) == set(ChaveDaAresta)


def test_a_chave_da_aresta_e_derivada_do_par_de_papeis_e_nunca_digitada() -> None:
    """A chave sai do par (origem, destino); é isso que dispensa uma coluna de chave."""
    nuvem = nuvem_vazia()

    derivadas = {nuvem.chave_da_aresta(a.id) for a in nuvem.arestas}
    pares = {PAR_DA_ARESTA[c] for c in ChaveDaAresta}

    print(f"chaves derivadas: {len(derivadas)}; pares distintos: {len(pares)}")
    assert derivadas == set(ChaveDaAresta)
    assert len(pares) == 7


def test_a_leitura_por_extenso_sai_dos_textos_atuais_das_entidades() -> None:
    nuvem = nuvem_preenchida()

    leituras = {chave: nuvem.leitura(chave) for chave in ChaveDaAresta}
    for chave, frase in leituras.items():
        print(f"{chave.value}: {frase}")

    assert leituras[ChaveDaAresta.A_B] == (
        "Para ter Sustentabilidade da Instituição Horizonte, precisamos de "
        "Receita nova no próximo semestre"
    )
    assert leituras[ChaveDaAresta.B_D] == (
        "Para ter Receita nova no próximo semestre, devemos "
        "Abrir turmas em três cidades novas"
    )
    assert leituras[ChaveDaAresta.C_D_PRIME] == (
        "Para ter Reputação acadêmica preservada, devemos "
        "Não abrir turmas em três cidades novas"
    )
    assert leituras[ChaveDaAresta.D_C] == (
        "Abrir turmas em três cidades novas ameaça Reputação acadêmica preservada"
    )
    assert leituras[ChaveDaAresta.D_PRIME_B] == (
        "Não abrir turmas em três cidades novas ameaça Receita nova no próximo semestre"
    )
    assert leituras[ChaveDaAresta.D_D_PRIME] == (
        "Abrir turmas em três cidades novas e Não abrir turmas em três cidades novas "
        "não podem coexistir"
    )
    assert len({f for f in leituras.values()}) == 7


def test_editar_a_entidade_muda_a_leitura_de_todas_as_arestas_que_a_citam() -> None:
    nuvem = nuvem_preenchida()
    antes = nuvem.leitura(ChaveDaAresta.A_B)

    nuvem.editar_entidade(PapelDaEntidade.B, "Receita recorrente de cursos livres", em=AGORA)

    depois = nuvem.leitura(ChaveDaAresta.A_B)
    print(f"antes: {antes}\ndepois: {depois}")
    assert antes != depois
    assert "Receita recorrente de cursos livres" in depois
    assert "EntidadeEditada" in [type(e).__name__ for e in nuvem.eventos]


def test_entidade_com_texto_vazio_e_recusada() -> None:
    nuvem = nuvem_vazia()

    with pytest.raises(DadoInvalido):
        nuvem.editar_entidade(PapelDaEntidade.A, "   ", em=AGORA)


# --------------------------------------------------------------------------------------
# Racional (RF-06)
# --------------------------------------------------------------------------------------


def test_o_racional_e_texto_do_agregado_com_evento_proprio() -> None:
    nuvem = nuvem_vazia()
    assert nuvem.racional == ""

    nuvem.editar_racional(
        "B e C emergem da narrativa: a instituição precisa de caixa e de reputação.",
        em=AGORA,
    )

    assert nuvem.racional.startswith("B e C emergem")
    assert "RacionalEditado" in [type(e).__name__ for e in nuvem.eventos]


# --------------------------------------------------------------------------------------
# Herança do M1: exclusão suave e restauração (RF-01, RF-04)
# --------------------------------------------------------------------------------------


def test_a_exclusao_suave_do_m1_vale_para_a_nuvem_e_recusa_mutacao() -> None:
    nuvem = nuvem_preenchida()
    nuvem.projeto.excluir(em=AGORA)

    with pytest.raises(MutacaoRecusada):
        nuvem.editar_entidade(PapelDaEntidade.A, "outro objetivo", em=AGORA)

    nuvem.projeto.restaurar(em=AGORA)
    nuvem.editar_entidade(PapelDaEntidade.A, "outro objetivo", em=AGORA)
    assert nuvem.texto(PapelDaEntidade.A) == "outro objetivo"
    assert (len(nuvem.entidades), len(nuvem.arestas)) == (5, 7)
