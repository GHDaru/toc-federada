"""A fronteira do M5 — quatro telas declaradas, e **zero** ações de catálogo (spec 010).

Siglas, uma vez neste arquivo: **M5** — Estratégia & Táticas · **S&T** — Estratégia &
Táticas (*Strategy & Tactics*) · **APH** — Aplicação ↔ Harness · **IA** — inteligência
artificial · **ADR** — *Architecture Decision Record* (Registro de Decisão Arquitetural) ·
**INT/RF/RN** — integração / requisito funcional / regra de negócio da spec 010.

**Este arquivo prova uma ausência, e por isso ele existe.** A INT-04 da spec 010 declara,
com todas as letras, que *"nenhuma ação `toc.*` nasce neste ciclo"*: o round 010 não inclui
assistência de IA para a árvore de S&T, e quando ela entrar será decisão nova sob o
ADR 0007. Uma declaração dessas, sem teste, é uma frase — e frases não impedem que a
próxima pessoa acrescente `toc.suggest_snt_steps` "porque as outras ferramentas têm".

O que **existe** do lado da fronteira são as quatro telas do registro (INT-02), e o que este
arquivo mede nelas é a regra que decide o `ai_visible`: **grandeza e vocabulário fechado
sim, texto de pessoa não**. Meta global, estratégia, tática e as três premissas são o que o
grupo escreveu — item 7 da constituição: tela é dado, e texto de usuário é sempre camada
não-confiável.
"""
from __future__ import annotations

from toc_api.dominio.federacao.catalogo import CATALOGO_TOC
from toc_api.dominio.federacao.telas import REGISTRO_DE_TELAS

TELAS_DO_M5 = (
    "toc.snt_arvore",
    "toc.snt_passo",
    "toc.snt_tabela",
    "toc.snt_acompanhamento",
)

#: Os campos que carregam texto escrito por pessoa. Nenhum deles atravessa para o modelo.
TEXTO_DE_PESSOA = {
    "meta_global",
    "estrategia",
    "tatica",
    "premissa_paralela",
    "premissa_necessidade_ao_pai",
    "premissa_suficiencia_dos_filhos",
}


def test_nenhuma_acao_do_catalogo_pertence_a_snt() -> None:
    """INT-04: a prova negativa. Zero ações do módulo, e a contagem é a evidência."""
    acoes = [a.action_id for a in CATALOGO_TOC.acoes]
    da_snt = [
        a
        for a in acoes
        if "snt" in a.lower() or "strategy" in a.lower() or "tactic" in a.lower()
    ]
    print(f"ações no catálogo: {len(acoes)} · ações da S&T: {len(da_snt)} {da_snt}")
    assert da_snt == []


def test_as_quatro_telas_do_m5_estao_no_registro() -> None:
    """INT-02: identificador estável, rota canônica sob `/toc/`, vocabulário do §A.4."""
    ids = {t.id for t in REGISTRO_DE_TELAS.telas}
    print(f"telas no registro: {len(ids)} · do M5: {sorted(ids & set(TELAS_DO_M5))}")
    assert set(TELAS_DO_M5) <= ids
    for tela_id in TELAS_DO_M5:
        tela = REGISTRO_DE_TELAS.tela(tela_id)
        assert tela.route.startswith("/toc/snt")
        assert tela.campos, f"{tela_id} sem campo declarado"


def test_nenhuma_tela_do_m5_anuncia_submit() -> None:
    """Uma tela que anunciasse `SUBMIT` prometeria um verbo que não existe (INT-04)."""
    anunciam = [
        tela_id
        for tela_id in TELAS_DO_M5
        if "SUBMIT" in REGISTRO_DE_TELAS.tela(tela_id).ai_actions
    ]
    print(f"telas do M5 examinadas: {len(TELAS_DO_M5)} · anunciando SUBMIT: {len(anunciam)}")
    assert anunciam == []


def test_o_texto_que_a_pessoa_escreve_nao_e_visivel_para_o_modelo() -> None:
    """Item 7 da constituição: texto de usuário é sempre camada não-confiável."""
    vazando = []
    examinados = 0
    for tela_id in TELAS_DO_M5:
        for campo in REGISTRO_DE_TELAS.tela(tela_id).campos:
            examinados += 1
            if campo.name in TEXTO_DE_PESSOA and campo.ai_visible:
                vazando.append(f"{tela_id}.{campo.name}")
    print(f"campos examinados: {examinados} · texto de pessoa visível: {len(vazando)} {vazando}")
    assert vazando == []


def test_numero_status_e_categoria_SAO_visiveis_porque_nao_sao_texto_de_pessoa() -> None:
    """A regra tem os dois lados: esconder tudo esconderia o contexto que a ajuda precisa."""
    passo = REGISTRO_DE_TELAS.tela("toc.snt_passo")
    visiveis = {c.name for c in passo.campos if c.ai_visible}
    print(f"campos visíveis em toc.snt_passo: {sorted(visiveis)}")
    assert {"numero", "status", "categoria", "filhos", "premissas_preenchidas"} <= visiveis
