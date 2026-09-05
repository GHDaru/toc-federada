"""Premissas por aresta e injeções ligadas a premissa — o coração do método (E3.2).

Siglas, uma vez: **NC** — Nuvem de Conflito · **TOC** — Teoria das Restrições · **TRIZ** —
Teoria da Resolução Inventiva de Problemas · **FSM** — máquina de estados finitos ·
**ARF** — Árvore da Realidade Futura.

As três regras que este arquivo prova, e que a linhagem não tinha como provar (lá premissa
e solução eram dois campos de texto pareados por aresta,
`tocbuilderv3/types.ts:72-76`, sem referência, sem estado e sem arquivamento):

- **premissa vazia numa aresta é erro** — nuvem sem premissa explícita é desenho de
  opinião (round 007: "nunca sai");
- **injeção sem premissa não existe** (RN-04) — e arquivar a premissa arquiva as injeções
  que a referenciam, **dizendo quantas** (RF-15);
- **o status da injeção obedece a uma FSM** (RN-08), e o retorno a `candidata` exige
  justificativa.
"""
from __future__ import annotations

from uuid import uuid4

import pytest

from toc_api.dominio.erros import DadoInvalido, NaoEncontrado
from toc_api.dominio.nuvem import (
    ChaveDaAresta,
    EstadoDaPremissa,
    InjecaoInvalida,
    PremissaInvalida,
    SeparacaoTRIZ,
    StatusDeInjecao,
    TransicaoDeInjecaoRecusada,
    novo_projeto_nc,
)

from .nuvem_sintetica import AGORA, DILEMA, DONO, ID_DA_NUVEM, NOME


def nuvem():
    n = novo_projeto_nc(id=ID_DA_NUVEM, dono=DONO, nome=NOME, em=AGORA)
    for papel, texto in DILEMA.items():
        n.editar_entidade(papel, texto, em=AGORA)
    return n


# --------------------------------------------------------------------------------------
# Premissas (RF-12, RF-13, RF-14)
# --------------------------------------------------------------------------------------


def test_uma_aresta_aceita_mais_de_uma_premissa_ordenada() -> None:
    n = nuvem()

    primeira = n.registrar_premissa(
        ChaveDaAresta.D_D_PRIME, "não há orçamento para as duas ações", em=AGORA
    )
    segunda = n.registrar_premissa(
        ChaveDaAresta.D_D_PRIME, "as duas disputam a mesma equipe", em=AGORA
    )

    premissas = n.premissas(ChaveDaAresta.D_D_PRIME)
    print(f"premissas em D_D_PRIME: {[(p.ordem, p.texto) for p in premissas]}")
    assert [p.id for p in premissas] == [primeira.id, segunda.id]
    assert [p.ordem for p in premissas] == [0, 1]
    assert all(p.estado is EstadoDaPremissa.VIGENTE for p in premissas)
    assert "PremissaRegistrada" in [type(e).__name__ for e in n.eventos]


def test_premissa_vazia_numa_aresta_e_erro() -> None:
    n = nuvem()

    for vazio in ("", "   ", "\n\t"):
        with pytest.raises(DadoInvalido):
            n.registrar_premissa(ChaveDaAresta.A_B, vazio, em=AGORA)

    assert n.premissas(ChaveDaAresta.A_B) == ()


def test_premissa_em_aresta_desconhecida_e_recusada() -> None:
    n = nuvem()

    with pytest.raises(ValueError):
        n.registrar_premissa("A_Z", "premissa de aresta que não existe", em=AGORA)


def test_desafiar_premissa_exige_justificativa_e_registra_autor_no_evento() -> None:
    n = nuvem()
    premissa = n.registrar_premissa(ChaveDaAresta.A_C, "reputação depende de credenciamento", em=AGORA)

    with pytest.raises(PremissaInvalida) as erro:
        n.desafiar_premissa(premissa.id, justificativa="  ", em=AGORA)
    assert erro.value.regra == "justificativa_obrigatoria"

    n.desafiar_premissa(
        premissa.id, justificativa="o credenciamento saiu em julho", em=AGORA
    )
    assert n.premissa(premissa.id).estado is EstadoDaPremissa.DESAFIADA
    assert "PremissaDesafiada" in [type(e).__name__ for e in n.eventos]

    n.revigorar_premissa(premissa.id, em=AGORA)
    assert n.premissa(premissa.id).estado is EstadoDaPremissa.VIGENTE


def test_editar_e_reordenar_premissas_da_mesma_aresta() -> None:
    n = nuvem()
    a = n.registrar_premissa(ChaveDaAresta.B_D, "só há caixa novo em turma nova", em=AGORA)
    b = n.registrar_premissa(ChaveDaAresta.B_D, "matrícula entra no mesmo semestre", em=AGORA)

    n.editar_premissa(a.id, "só há caixa novo em turma presencial nova", em=AGORA)
    n.reordenar_premissas(ChaveDaAresta.B_D, (b.id, a.id), em=AGORA)

    ordem = [p.id for p in n.premissas(ChaveDaAresta.B_D)]
    print(f"ordem depois de reordenar: {[str(i)[:8] for i in ordem]}")
    assert ordem == [b.id, a.id]
    assert n.premissa(a.id).texto.endswith("presencial nova")
    assert "PremissaEditada" in [type(e).__name__ for e in n.eventos]


def test_reordenar_com_conjunto_diferente_de_premissas_e_recusado() -> None:
    n = nuvem()
    a = n.registrar_premissa(ChaveDaAresta.B_D, "premissa a", em=AGORA)
    n.registrar_premissa(ChaveDaAresta.B_D, "premissa b", em=AGORA)

    with pytest.raises(PremissaInvalida) as erro:
        n.reordenar_premissas(ChaveDaAresta.B_D, (a.id,), em=AGORA)
    assert erro.value.regra == "ordem_incompleta"


def test_a_completude_conta_arestas_com_pelo_menos_uma_premissa_vigente() -> None:
    """RF-14/RN-03: a completude informa e prioriza — nunca trava a edição."""
    n = nuvem()
    assert n.validar().completude == (0, 7)

    for chave in (ChaveDaAresta.A_B, ChaveDaAresta.A_C, ChaveDaAresta.B_D):
        n.registrar_premissa(chave, f"premissa de {chave.value}", em=AGORA)

    validacao = n.validar()
    print(
        f"completude: {validacao.completude[0]} de {validacao.completude[1]}; "
        f"pendentes={[c.value for c in validacao.arestas_sem_premissa]}"
    )
    assert validacao.completude == (3, 7)
    assert not validacao.modelada
    assert len(validacao.arestas_sem_premissa) == 4

    for chave in ChaveDaAresta:
        if not n.premissas(chave):
            n.registrar_premissa(chave, f"premissa de {chave.value}", em=AGORA)
    assert n.validar().completude == (7, 7)
    assert n.validar().modelada


def test_premissa_desafiada_deixa_de_sustentar_a_aresta_mas_continua_no_dado() -> None:
    n = nuvem()
    premissa = n.registrar_premissa(ChaveDaAresta.A_B, "sem receita não há instituição", em=AGORA)

    n.desafiar_premissa(premissa.id, justificativa="há reserva de dois anos", em=AGORA)

    assert n.validar().completude == (0, 7)
    assert len(n.premissas(ChaveDaAresta.A_B)) == 1


# --------------------------------------------------------------------------------------
# Injeções (RF-15..RF-20, RN-04, RN-07, RN-08)
# --------------------------------------------------------------------------------------


def test_injecao_sem_premissa_existente_nao_existe() -> None:
    """RN-04: não existe construtor de injeção sem premissa."""
    n = nuvem()

    with pytest.raises(NaoEncontrado):
        n.registrar_injecao(uuid4(), "faseamento orçamentário", em=AGORA)


def test_injecao_nasce_ligada_a_premissa_que_quebra() -> None:
    n = nuvem()
    premissa = n.registrar_premissa(
        ChaveDaAresta.D_D_PRIME, "não há orçamento para as duas ações", em=AGORA
    )

    injecao = n.registrar_injecao(
        premissa.id,
        "faseamento orçamentário condicionado a marco de receita",
        em=AGORA,
        separacao=SeparacaoTRIZ.TEMPO,
    )

    assert injecao.premissa_id == premissa.id
    assert injecao.status is StatusDeInjecao.CANDIDATA
    assert n.injecoes_da_premissa(premissa.id) == (injecao,)
    assert n.injecoes_da_aresta(ChaveDaAresta.D_D_PRIME) == (injecao,)
    assert "InjecaoRegistrada" in [type(e).__name__ for e in n.eventos]


def test_injecao_com_texto_vazio_e_recusada() -> None:
    n = nuvem()
    premissa = n.registrar_premissa(ChaveDaAresta.D_C, "turma nova é turma improvisada", em=AGORA)

    with pytest.raises(DadoInvalido):
        n.registrar_injecao(premissa.id, "   ", em=AGORA)


def test_injecao_em_premissa_arquivada_e_recusada() -> None:
    n = nuvem()
    premissa = n.registrar_premissa(ChaveDaAresta.D_C, "premissa que vai sair", em=AGORA)
    n.arquivar_premissa(premissa.id, em=AGORA)

    with pytest.raises(InjecaoInvalida) as erro:
        n.registrar_injecao(premissa.id, "injeção órfã", em=AGORA)
    assert erro.value.regra == "premissa_arquivada"


def test_arquivar_premissa_arquiva_as_injecoes_dela_e_nenhuma_outra() -> None:
    """RF-15: nunca injeção órfã, nunca apagar em silêncio — e o ato diz quantas."""
    n = nuvem()
    alvo = n.registrar_premissa(ChaveDaAresta.D_D_PRIME, "premissa alvo", em=AGORA)
    vizinha = n.registrar_premissa(ChaveDaAresta.D_D_PRIME, "premissa vizinha", em=AGORA)
    duas = [
        n.registrar_injecao(alvo.id, "injeção 1", em=AGORA),
        n.registrar_injecao(alvo.id, "injeção 2", em=AGORA),
    ]
    intocada = n.registrar_injecao(vizinha.id, "injeção da vizinha", em=AGORA)

    arquivadas = n.arquivar_premissa(alvo.id, em=AGORA)

    print(f"injeções arquivadas junto: {arquivadas}; intocadas: 1")
    assert arquivadas == 2
    assert all(n.injecao(i.id).arquivada for i in duas)
    assert not n.injecao(intocada.id).arquivada
    assert n.injecoes_da_premissa(alvo.id) == ()
    assert n.premissas(ChaveDaAresta.D_D_PRIME) == (n.premissa(vizinha.id),)
    evento = [e for e in n.eventos if type(e).__name__ == "PremissaArquivada"][-1]
    assert evento.injecoes_arquivadas == 2


def test_a_fsm_do_status_da_injecao_e_tabela_e_o_retorno_exige_justificativa() -> None:
    n = nuvem()
    premissa = n.registrar_premissa(ChaveDaAresta.D_D_PRIME, "premissa central", em=AGORA)
    injecao = n.registrar_injecao(premissa.id, "separar por condição de matrícula", em=AGORA)

    n.mudar_status_de_injecao(injecao.id, StatusDeInjecao.ESCOLHIDA, em=AGORA)
    assert n.injecao(injecao.id).status is StatusDeInjecao.ESCOLHIDA

    with pytest.raises(TransicaoDeInjecaoRecusada) as erro:
        n.mudar_status_de_injecao(injecao.id, StatusDeInjecao.DESCARTADA, em=AGORA)
    print(f"transição recusada: {erro.value.motivo}")
    assert erro.value.motivo == "transicao_invalida"

    with pytest.raises(TransicaoDeInjecaoRecusada) as sem_justificativa:
        n.mudar_status_de_injecao(injecao.id, StatusDeInjecao.CANDIDATA, em=AGORA)
    assert sem_justificativa.value.motivo == "retorno_sem_justificativa"

    n.mudar_status_de_injecao(
        injecao.id, StatusDeInjecao.CANDIDATA, em=AGORA, justificativa="o grupo reabriu"
    )
    assert n.injecao(injecao.id).status is StatusDeInjecao.CANDIDATA
    assert "StatusDeInjecaoMudou" in [type(e).__name__ for e in n.eventos]


def test_escolher_injecao_cria_a_referencia_de_semeadura_vazia() -> None:
    """RF-20/INT-06: a costura com a ARF nasce vazia aqui; quem a preenche é o ciclo 008."""
    n = nuvem()
    premissa = n.registrar_premissa(ChaveDaAresta.D_D_PRIME, "premissa central", em=AGORA)
    injecao = n.registrar_injecao(premissa.id, "faseamento por marco de receita", em=AGORA)

    assert n.injecao(injecao.id).semeadura is None

    n.mudar_status_de_injecao(injecao.id, StatusDeInjecao.ESCOLHIDA, em=AGORA)

    semeadura = n.injecao(injecao.id).semeadura
    print(f"semeadura: {semeadura}")
    assert semeadura is not None
    assert semeadura.injecao_id == injecao.id
    assert semeadura.projeto_destino_id is None
    assert n.semeaduras() == (semeadura,)


def test_mais_de_uma_injecao_pode_ser_escolhida() -> None:
    """RN-08, última frase — e o teste existe porque é fácil implementar 'só uma'."""
    n = nuvem()
    premissa = n.registrar_premissa(ChaveDaAresta.D_D_PRIME, "premissa central", em=AGORA)
    uma = n.registrar_injecao(premissa.id, "injeção uma", em=AGORA)
    outra = n.registrar_injecao(premissa.id, "injeção outra", em=AGORA)

    n.mudar_status_de_injecao(uma.id, StatusDeInjecao.ESCOLHIDA, em=AGORA)
    n.mudar_status_de_injecao(outra.id, StatusDeInjecao.ESCOLHIDA, em=AGORA)

    assert len(n.semeaduras()) == 2


def test_classificar_injecao_por_separacao_triz_e_a_cobertura_do_conflito() -> None:
    """RN-07: o sistema mostra quais das 5 separações faltam; o humano decide."""
    n = nuvem()
    premissa = n.registrar_premissa(ChaveDaAresta.D_D_PRIME, "premissa central", em=AGORA)
    injecao = n.registrar_injecao(premissa.id, "abrir uma cidade por trimestre", em=AGORA)

    assert n.validar().separacoes_ausentes == tuple(SeparacaoTRIZ)

    n.classificar_injecao(injecao.id, SeparacaoTRIZ.TEMPO, em=AGORA)

    ausentes = n.validar().separacoes_ausentes
    print(f"separações ainda sem injeção: {[s.value for s in ausentes]}")
    assert SeparacaoTRIZ.TEMPO not in ausentes
    assert len(ausentes) == 4
    assert "InjecaoReclassificada" in [type(e).__name__ for e in n.eventos]


def test_a_visao_de_solucao_cobre_as_sete_posicoes_inclusive_d_c_e_d_d_prime() -> None:
    """RF-31 e a DoD 9: o defeito do v3 vira caso de teste.

    Em `tocbuilderv3/components/ConflictCloudView.tsx` o diagrama de solução renderizava
    5 nós de injeção, e `D_C.solution` / `D_D_PRIME.solution` não apareciam em lugar
    nenhum (F-07 da spec). Aqui as 7 posições existem SEMPRE — com injeção ou com
    pendência explícita.
    """
    n = nuvem()
    for chave in (ChaveDaAresta.D_C, ChaveDaAresta.D_D_PRIME):
        premissa = n.registrar_premissa(chave, f"premissa de {chave.value}", em=AGORA)
        n.registrar_injecao(premissa.id, f"injeção de {chave.value}", em=AGORA)

    visao = n.visao_de_solucao()
    print(
        f"posições da visão de solução: {len(visao)}; "
        f"com injeção={[c.value for c, i in visao.items() if i]}"
    )
    assert set(visao) == set(ChaveDaAresta)
    assert len(visao) == 7
    assert visao[ChaveDaAresta.D_C] and visao[ChaveDaAresta.D_D_PRIME]
    assert n.validar().arestas_sem_injecao == tuple(
        c for c in ChaveDaAresta if c not in (ChaveDaAresta.D_C, ChaveDaAresta.D_D_PRIME)
    )
