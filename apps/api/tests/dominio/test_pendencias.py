"""As pendências lógicas da árvore de Estratégia & Táticas — função pura (spec 010, RF-14).

Siglas, uma vez neste arquivo: **S&T** — Estratégia & Táticas (*Strategy & Tactics*) ·
**M5** — o módulo da S&T · **RF/RN** — requisito funcional / regra de negócio da spec 010
· **R2** — a regra do projeto que exige "quanto examinou?" em todo verde.

A pendência é o instrumento que responde à pergunta da US-08 — *"onde o plano ainda é
organograma e não S&T"* — e ela **informa, nunca trava** (RN-06). Os três tipos são
fechados: passo não-raiz sem premissa de necessidade, passo com filhos sem premissa de
suficiência, passo sem tática.

A saída carrega `passos_examinados` de propósito: dizer "3 pendências" sem dizer sobre
quantos passos é o verde sem denominador que a retrospectiva da irmã
`gestaodeprioridades` nomeou (regra R2).
"""
from __future__ import annotations

from toc_api.dominio.snt import (
    PENDENCIA_SEM_NECESSIDADE,
    PENDENCIA_SEM_SUFICIENCIA,
    PENDENCIA_SEM_TATICA,
    StatusDoPasso,
    pendencias_da_arvore,
)

from .snt_sintetica import AGORA, PREMISSAS_DE_1_1
from .test_snt import arvore, plano_completo


def test_a_arvore_recem_decomposta_acusa_a_falta_das_premissas() -> None:
    """US-08: 6 passos não-raiz sem necessidade + 3 pais sem suficiência, sobre 7 passos."""
    a, _ = plano_completo()
    resultado = a.pendencias()
    print(
        f"passos examinados={resultado.passos_examinados} · pendências={resultado.total} · "
        f"resumo={resultado.resumo()}"
    )
    assert resultado.passos_examinados == 7
    assert len(resultado.do_tipo(PENDENCIA_SEM_NECESSIDADE)) == 6
    assert len(resultado.do_tipo(PENDENCIA_SEM_SUFICIENCIA)) == 3
    # A fixture tem tática em todos os passos — nenhuma pendência deste tipo.
    assert len(resultado.do_tipo(PENDENCIA_SEM_TATICA)) == 0


def test_a_raiz_nunca_e_pendencia_de_necessidade() -> None:
    """RN-02: necessidade não se aplica a raiz — acusá-la seria ruído, não pendência."""
    a, chaves = plano_completo()
    das_necessidades = a.pendencias().do_tipo(PENDENCIA_SEM_NECESSIDADE)
    numeros = sorted(p.numero for p in das_necessidades)
    print(f"pendências de necessidade: {numeros} (a raiz `1` não está)")
    assert "1" not in numeros


def test_suficiencia_so_e_pendencia_quando_ha_filhos() -> None:
    a, chaves = plano_completo()
    das_suficiencias = {p.numero for p in a.pendencias().do_tipo(PENDENCIA_SEM_SUFICIENCIA)}
    print(f"pendências de suficiência: {sorted(das_suficiencias)}")
    assert das_suficiencias == {"1", "1.1", "1.2"}
    # As folhas (1.1.1, 1.1.2, 1.2.1, 1.3) não aparecem: sem filhos, não há o que bastar.
    assert not das_suficiencias & {"1.1.1", "1.1.2", "1.2.1", "1.3"}


def test_preencher_a_premissa_apaga_a_pendencia_correspondente() -> None:
    a, chaves = plano_completo()
    antes = a.pendencias().total
    a.editar_premissas(chaves["1.1"], em=AGORA, **PREMISSAS_DE_1_1)
    depois = a.pendencias()
    print(f"pendências antes={antes} · depois={depois.total} (duas do passo 1.1 saíram)")
    assert depois.total == antes - 2
    assert all(p.numero != "1.1" for p in depois.pendencias)


def test_passo_sem_tatica_e_pendencia_e_nao_impede_a_gravacao() -> None:
    """RF-11 + RN-06: a tática pode nascer vazia; a pendência avisa e a árvore existe."""
    a = arvore()
    sem_tatica = a.adicionar_passo(estrategia="Sustentar a demanda nova", em=AGORA)
    resultado = a.pendencias()
    print(
        f"passos={resultado.passos_examinados} · sem tática="
        f"{len(resultado.do_tipo(PENDENCIA_SEM_TATICA))}"
    )
    assert [p.no_id for p in resultado.do_tipo(PENDENCIA_SEM_TATICA)] == [sem_tatica.id]
    a.mudar_status(sem_tatica.id, StatusDoPasso.EM_EXECUCAO, autor="u-gestora", em=AGORA)


def test_a_pendencia_aponta_o_passo_com_numero_para_o_salto_direto() -> None:
    """RF-14: "cada pendência aparece nomeada com salto direto para o passo"."""
    a, chaves = plano_completo()
    por_no = {p.no_id: p for p in a.pendencias().do_tipo(PENDENCIA_SEM_NECESSIDADE)}
    alvo = por_no[chaves["1.1.2"]]
    print(f"pendência: numero={alvo.numero!r} tipo={alvo.tipo!r} no_id={alvo.no_id}")
    assert alvo.numero == "1.1.2"
    assert alvo.tipo == PENDENCIA_SEM_NECESSIDADE


def test_a_funcao_e_pura_e_nao_muta_a_arvore() -> None:
    a, chaves = plano_completo()
    estrutura = a.estrutura()
    fichas = dict(a.fichas())
    numeros = a.numeros()
    uma = pendencias_da_arvore(estrutura, fichas, numeros)
    outra = pendencias_da_arvore(estrutura, fichas, numeros)
    print(f"duas execuções sobre {uma.passos_examinados} passos · iguais: {uma == outra}")
    assert uma == outra
    assert a.estrutura() == estrutura and dict(a.fichas()) == fichas


def test_arvore_vazia_tem_zero_pendencias_e_zero_progresso() -> None:
    a = arvore()
    resultado = a.pendencias()
    print(f"vazia: passos={resultado.passos_examinados} pendências={resultado.total} "
          f"progresso={resultado.progresso}")
    assert (resultado.passos_examinados, resultado.total, resultado.progresso) == (0, 0, 0.0)


def test_o_resumo_declara_as_quatro_contagens_de_status_mesmo_zeradas() -> None:
    """O painel não some com uma coluna só porque nenhum passo está nela (RF-17)."""
    a, _ = plano_completo()
    resumo = a.pendencias().resumo()
    print(f"resumo={resumo}")
    for status in StatusDoPasso:
        assert f"status_{status.value}" in resumo
    assert resumo["passos"] == 7
