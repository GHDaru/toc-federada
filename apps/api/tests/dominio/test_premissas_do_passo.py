"""As três premissas lógicas do passo — o que faz a S&T ser S&T (spec 010, F5.1.3).

Siglas, uma vez neste arquivo: **S&T** — Estratégia & Táticas (*Strategy & Tactics*) ·
**M5** — o módulo da S&T · **RF/RN** — requisito funcional / regra de negócio da spec 010.

**Por que este arquivo é o coração do módulo.** O round 010 declara o que "nunca sai" do
escopo: *"as três premissas por nó — S&T sem premissa é organograma, e o modelo de dados
da linhagem já as tinha"*. E tinha mesmo: `TOC-Builder/types.ts:243-245`, na PRIMEIRA
geração, já declarava `parallelAssumption`, `necessaryAssumptionToParent` e
`sufficiencyOfChildrenAssumption`; a quarta geração as manteve
(`tocbuilderv3/types.ts:293-295`) e as ofereceu em três áreas de texto empilhadas
(`SnTStepEditorModal.tsx:137-159`) — **sem leitura dirigida e sem consequência nenhuma**.

O que este ciclo acrescenta é a semântica (RN-02): cada premissa tem papel estrutural, a
leitura é montada contra o pai e contra os filhos nomeados (RF-13), e a ausência vira
pendência visível — **nunca trava de gravação** (RN-06).

Base sintética (ADR 0006): "Instituição Horizonte", personas fictícias.
"""
from __future__ import annotations

import pytest

from toc_api.dominio.erros import MutacaoRecusada
from toc_api.dominio.eventos import PremissasEditadas
from toc_api.dominio.snt import PremissasDoPasso, StatusDoPasso

from .snt_sintetica import AGORA, PREMISSAS_DE_1_1
from .test_snt import plano_completo


def test_o_objeto_de_valor_carrega_os_tres_campos_da_linhagem() -> None:
    premissas = PremissasDoPasso(**PREMISSAS_DE_1_1)
    print(f"campos={sorted(PREMISSAS_DE_1_1)}")
    assert sorted(PREMISSAS_DE_1_1) == [
        "necessidade_ao_pai", "paralela", "suficiencia_dos_filhos",
    ]
    assert premissas.vazias is False
    assert PremissasDoPasso().vazias is True


def test_premissa_e_objeto_de_valor_imutavel() -> None:
    premissas = PremissasDoPasso(paralela="a fila é o gargalo")
    with pytest.raises(Exception):
        premissas.paralela = "outra coisa"  # type: ignore[misc]
    print("premissas imutáveis: mudar um campo cria valor novo")


def test_as_tres_premissas_gravam_e_voltam_da_ficha() -> None:
    a, chaves = plano_completo()
    ficha = a.editar_premissas(chaves["1.1"], em=AGORA, **PREMISSAS_DE_1_1)
    print(
        "gravadas: "
        f"paralela={len(ficha.premissas.paralela)} car. · "
        f"necessidade={len(ficha.premissas.necessidade_ao_pai)} car. · "
        f"suficiência={len(ficha.premissas.suficiencia_dos_filhos)} car."
    )
    assert ficha.premissas == PremissasDoPasso(**PREMISSAS_DE_1_1)
    evento = [e for e in a.eventos if isinstance(e, PremissasEditadas)][-1]
    assert set(evento.campos) == set(PREMISSAS_DE_1_1)


def test_editar_uma_premissa_nao_apaga_as_outras_duas() -> None:
    a, chaves = plano_completo()
    a.editar_premissas(chaves["1.1"], em=AGORA, **PREMISSAS_DE_1_1)
    a.editar_premissas(chaves["1.1"], paralela="a fila mudou de lugar", em=AGORA)
    ficha = a.ficha(chaves["1.1"])
    print(f"paralela nova={ficha.premissas.paralela!r} · as outras duas intactas")
    assert ficha.premissas.paralela == "a fila mudou de lugar"
    assert ficha.premissas.necessidade_ao_pai == PREMISSAS_DE_1_1["necessidade_ao_pai"]
    assert ficha.premissas.suficiencia_dos_filhos == PREMISSAS_DE_1_1["suficiencia_dos_filhos"]


def test_editar_premissas_sem_campo_nenhum_e_recusado() -> None:
    a, chaves = plano_completo()
    with pytest.raises(MutacaoRecusada):
        a.editar_premissas(chaves["1.1"], em=AGORA)


def test_gravar_sem_premissa_nenhuma_e_permitido_e_vira_pendencia() -> None:
    """RN-06: pendência informa e prioriza, nunca trava. A árvore grava-se incompleta."""
    a, chaves = plano_completo()
    sem_nenhuma = [
        no_id for no_id in chaves.values() if a.ficha(no_id).premissas.vazias
    ]
    print(f"passos sem premissa nenhuma: {len(sem_nenhuma)} de {len(chaves)} — e a árvore existe")
    assert len(sem_nenhuma) == len(chaves)
    a.mudar_status(chaves["1.1"], StatusDoPasso.EM_EXECUCAO, autor="u-gestora", em=AGORA)


# ---------------------------------------------------------------------------------------
# RF-13 · a leitura dirigida contra o pai e contra os filhos nomeados
# ---------------------------------------------------------------------------------------


def test_a_leitura_de_necessidade_e_montada_contra_o_pai() -> None:
    a, chaves = plano_completo()
    a.editar_premissas(
        chaves["1.1"], necessidade_ao_pai=PREMISSAS_DE_1_1["necessidade_ao_pai"], em=AGORA
    )
    _, necessidade, _ = a.leituras(chaves["1.1"])
    print(f"leitura: {necessidade.texto}")
    assert necessidade.texto.startswith("Para alcançar <1> ")
    assert "é necessário <1.1> " in necessidade.texto
    assert necessidade.texto.endswith(PREMISSAS_DE_1_1["necessidade_ao_pai"])
    assert necessidade.aplicavel and necessidade.completa


def test_a_raiz_nao_tem_premissa_de_necessidade_e_isso_nao_e_pendencia() -> None:
    """RN-02: necessidade não se aplica à raiz — a leitura diz isso em vez de mentir."""
    a, chaves = plano_completo()
    _, necessidade, _ = a.leituras(chaves["1"])
    print(f"raiz: aplicavel={necessidade.aplicavel} texto={necessidade.texto!r}")
    assert necessidade.aplicavel is False
    assert "raiz do plano" in necessidade.texto


def test_a_leitura_de_suficiencia_nomeia_os_filhos() -> None:
    a, chaves = plano_completo()
    a.editar_premissas(
        chaves["1.1"],
        suficiencia_dos_filhos=PREMISSAS_DE_1_1["suficiencia_dos_filhos"],
        em=AGORA,
    )
    _, _, suficiencia = a.leituras(chaves["1.1"])
    print(f"leitura: {suficiencia.texto[:120]}…")
    assert suficiencia.texto.startswith("<1.1.1> ")
    assert "<1.1.2> " in suficiencia.texto
    assert "bastam para <1.1> " in suficiencia.texto
    assert suficiencia.aplicavel and suficiencia.completa


def test_passo_sem_filhos_nao_tem_suficiencia_a_declarar() -> None:
    a, chaves = plano_completo()
    _, _, suficiencia = a.leituras(chaves["1.1.1"])
    print(f"folha: aplicavel={suficiencia.aplicavel} texto={suficiencia.texto!r}")
    assert suficiencia.aplicavel is False


def test_a_premissa_paralela_le_se_sozinha_e_a_incompleta_mostra_a_frase_pela_metade() -> None:
    a, chaves = plano_completo()
    paralela, _, _ = a.leituras(chaves["1.2"])
    print(f"incompleta: {paralela.texto!r}")
    assert paralela.aplicavel is True and paralela.completa is False
    assert paralela.texto.endswith("…")

    a.editar_premissas(chaves["1.2"], paralela="há quem ensine dentro de casa", em=AGORA)
    paralela, _, _ = a.leituras(chaves["1.2"])
    print(f"completa: {paralela.texto!r}")
    assert paralela.completa is True
    assert paralela.texto.endswith("há quem ensine dentro de casa")


def test_a_leitura_acompanha_a_renumeracao_depois_de_mover() -> None:
    """A frase cita números; mover renumera; a frase tem de acompanhar sozinha."""
    a, chaves = plano_completo()
    a.editar_premissas(
        chaves["1.1"], necessidade_ao_pai=PREMISSAS_DE_1_1["necessidade_ao_pai"], em=AGORA
    )
    destino = a.adicionar_passo(estrategia="Abrir a segunda frente", em=AGORA)
    a.mover_passo(chaves["1.1"], novo_pai_id=destino.id, em=AGORA)
    _, necessidade, _ = a.leituras(chaves["1.1"])
    print(f"depois do mover: {necessidade.texto[:80]}…")
    assert "é necessário <2.1> " in necessidade.texto
    assert "Para alcançar <2> " in necessidade.texto
