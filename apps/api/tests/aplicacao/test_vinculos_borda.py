"""M6 — a validação do vínculo acontece NO SERVIDOR (spec 009, RNF-04; DoD 8).

Siglas, uma vez neste arquivo: **M6** — Focalização · **M1** — Núcleo de Diagramas
Lógicos · **ARA** — Árvore da Realidade Atual · **NC** — Nuvem de Conflito · **APR** —
Árvore de Pré-Requisitos · **RN/RF/RNF** — regra de negócio / requisito funcional /
requisito não funcional.

A divisão de trabalho que este arquivo prova, e que é a decisão 2 do plano do ciclo 009:

| Quem | O que decide |
|---|---|
| domínio (`dominio/focalizacao.py`) | a regra canônica passo × ferramenta (RN-06) |
| aplicação (este teste) | existe? é deste inquilino? é da ferramenta certa? está vivo? |

Sem a segunda metade, um vínculo para um projeto de outro inquilino entraria em silêncio e
a jornada mostraria um cartão apontando para o nada. Com ela, e só com ela, "o vínculo é
navegável" deixa de ser promessa.
"""
from __future__ import annotations

from uuid import uuid4

import pytest

from toc_api.aplicacao.focalizacao import (
    CriarAnaliseDeFocalizacao,
    EstadoDoVinculo,
    ResolverVinculos,
    VincularFerramenta,
)
from toc_api.aplicacao.projetos import CriarProjeto, ExcluirProjeto
from toc_api.dominio.focalizacao import TipoDePasso, VinculoInvalido

from ..dominio.focalizacao_sintetica import (
    AGORA,
    DESCRICAO_DO_SISTEMA,
    DONO,
    NOME,
    OUTRO_DONO,
    SISTEMA,
)
from .fakes import RastreadorFalso, RelogioFalso
from .fakes_m6 import RepositorioDaJornadaFalso


@pytest.fixture()
def montagem():
    return {
        "rastreador": RastreadorFalso(),
        "repositorio": RepositorioDaJornadaFalso(),
        "relogio": RelogioFalso(instante=AGORA),
    }


def analise(montagem):
    return CriarAnaliseDeFocalizacao(**montagem).rodar(
        dono=DONO, nome=NOME, sistema=SISTEMA, descricao_do_sistema=DESCRICAO_DO_SISTEMA
    )


def projeto_de_ferramenta(montagem, ferramenta: str, *, dono=DONO):
    """Um projeto do M1 com a ferramenta pedida — o alvo do vínculo, gravado pela porta."""
    return CriarProjeto(**montagem).rodar(
        dono=dono, nome=f"projeto {ferramenta}", ferramenta=ferramenta
    )


# ---------------------------------------------------------------------------------------
# O caminho feliz: o alvo existe, é do inquilino e é da ferramenta declarada
# ---------------------------------------------------------------------------------------


def test_vincular_projeto_existente_do_mesmo_inquilino_passa(montagem):
    foco = analise(montagem)
    ara = projeto_de_ferramenta(montagem, "ara")

    vinculo = VincularFerramenta(**montagem).rodar(
        dono=DONO,
        projeto_id=foco.id,
        passo=TipoDePasso.IDENTIFICAR,
        tipo="ara",
        alvo_id=ara.id,
        papel="causa raiz",
    )

    assert vinculo.projeto_id == ara.id
    assert vinculo.canonico is True


# ---------------------------------------------------------------------------------------
# RNF-04 — as recusas, cada uma com a regra nomeada
# ---------------------------------------------------------------------------------------


def test_projeto_inexistente_e_recusado_com_a_regra_nomeada(montagem):
    foco = analise(montagem)
    with pytest.raises(VinculoInvalido) as erro:
        VincularFerramenta(**montagem).rodar(
            dono=DONO, projeto_id=foco.id, passo=TipoDePasso.IDENTIFICAR,
            tipo="ara", alvo_id=uuid4(),
        )
    assert erro.value.regra == "alvo_inexistente"


def test_projeto_de_outro_inquilino_e_indistinguivel_de_inexistente(montagem):
    """A fronteira não vaza: a recusa é a MESMA de um projeto que não existe."""
    foco = analise(montagem)
    alheio = projeto_de_ferramenta(montagem, "ara", dono=OUTRO_DONO)

    with pytest.raises(VinculoInvalido) as erro:
        VincularFerramenta(**montagem).rodar(
            dono=DONO, projeto_id=foco.id, passo=TipoDePasso.IDENTIFICAR,
            tipo="ara", alvo_id=alheio.id,
        )
    assert erro.value.regra == "alvo_inexistente"


def test_ferramenta_declarada_diferente_da_do_projeto_e_recusada(montagem):
    """Declarar `ara` e apontar para uma Nuvem de Conflito produziria cartão mentiroso."""
    foco = analise(montagem)
    nuvem = projeto_de_ferramenta(montagem, "nc")

    with pytest.raises(VinculoInvalido) as erro:
        VincularFerramenta(**montagem).rodar(
            dono=DONO, projeto_id=foco.id, passo=TipoDePasso.IDENTIFICAR,
            tipo="ara", alvo_id=nuvem.id,
        )
    assert erro.value.regra == "ferramenta_divergente"
    assert "nc" in str(erro.value)


def test_projeto_ja_arquivado_nao_recebe_vinculo_novo(montagem):
    foco = analise(montagem)
    ara = projeto_de_ferramenta(montagem, "ara")
    ExcluirProjeto(**montagem).rodar(dono=DONO, projeto_id=ara.id)

    with pytest.raises(VinculoInvalido) as erro:
        VincularFerramenta(**montagem).rodar(
            dono=DONO, projeto_id=foco.id, passo=TipoDePasso.IDENTIFICAR,
            tipo="ara", alvo_id=ara.id,
        )
    assert erro.value.regra == "alvo_arquivado"


def test_a_analise_nao_se_vincula_a_si_mesma(montagem):
    foco = analise(montagem)
    with pytest.raises(VinculoInvalido) as erro:
        VincularFerramenta(**montagem).rodar(
            dono=DONO, projeto_id=foco.id, passo=TipoDePasso.IDENTIFICAR,
            tipo="ara", alvo_id=foco.id,
        )
    assert erro.value.regra == "ferramenta_divergente"


# ---------------------------------------------------------------------------------------
# RNF-04 — a degradação legível: o alvo foi arquivado DEPOIS
# ---------------------------------------------------------------------------------------


def test_alvo_arquivado_depois_degrada_para_referencia_legivel_nunca_erro_opaco(montagem):
    """RNF-04: "nunca erro opaco, nunca dado órfão silencioso"."""
    foco = analise(montagem)
    ara = projeto_de_ferramenta(montagem, "ara")
    VincularFerramenta(**montagem).rodar(
        dono=DONO, projeto_id=foco.id, passo=TipoDePasso.IDENTIFICAR, tipo="ara", alvo_id=ara.id,
    )

    ExcluirProjeto(**montagem).rodar(dono=DONO, projeto_id=ara.id)

    (resolvido,) = ResolverVinculos(**montagem).rodar(dono=DONO, projeto_id=foco.id)
    assert resolvido.estado is EstadoDoVinculo.ARQUIVADO
    assert resolvido.nome == "projeto ara"
    assert resolvido.passo is TipoDePasso.IDENTIFICAR
    assert "arquivado" in resolvido.legenda.lower()


def test_alvo_que_sumiu_de_vez_aparece_como_ausente_e_nao_derruba_a_leitura(montagem):
    """Exclusão DEFINITIVA por outro caminho: o mapa continua abrindo, e diz o que houve."""
    foco = analise(montagem)
    ara = projeto_de_ferramenta(montagem, "ara")
    VincularFerramenta(**montagem).rodar(
        dono=DONO, projeto_id=foco.id, passo=TipoDePasso.IDENTIFICAR, tipo="ara", alvo_id=ara.id,
    )
    del montagem["repositorio"].itens[ara.id]

    (resolvido,) = ResolverVinculos(**montagem).rodar(dono=DONO, projeto_id=foco.id)
    assert resolvido.estado is EstadoDoVinculo.AUSENTE
    assert resolvido.nome == ""
    assert "não existe" in resolvido.legenda.lower()


def test_o_vinculo_ativo_traz_o_nome_e_o_estado_do_projeto_vinculado(montagem):
    """RF-14: "mostra o estado do projeto vinculado" — sem copiar o conteúdo dele."""
    foco = analise(montagem)
    apr = projeto_de_ferramenta(montagem, "apr")
    VincularFerramenta(**montagem).rodar(
        dono=DONO, projeto_id=foco.id, passo=TipoDePasso.ELEVAR, tipo="apr", alvo_id=apr.id,
    )

    (resolvido,) = ResolverVinculos(**montagem).rodar(dono=DONO, projeto_id=foco.id)
    assert resolvido.estado is EstadoDoVinculo.ATIVO
    assert resolvido.nome == "projeto apr"
    assert resolvido.ferramenta == "apr"


# ---------------------------------------------------------------------------------------
# RN-06 pela borda: fora do canônico exige justificativa, e passa com ela
# ---------------------------------------------------------------------------------------


def test_fora_do_canonico_sem_justificativa_e_recusado_pela_borda(montagem):
    foco = analise(montagem)
    apr = projeto_de_ferramenta(montagem, "apr")
    with pytest.raises(VinculoInvalido) as erro:
        VincularFerramenta(**montagem).rodar(
            dono=DONO, projeto_id=foco.id, passo=TipoDePasso.IDENTIFICAR,
            tipo="apr", alvo_id=apr.id,
        )
    assert erro.value.regra == "justificativa_obrigatoria"


def test_fora_do_canonico_com_justificativa_entra_e_o_span_registra_o_aviso(montagem):
    foco = analise(montagem)
    apr = projeto_de_ferramenta(montagem, "apr")
    montagem["rastreador"].spans.clear()

    VincularFerramenta(**montagem).rodar(
        dono=DONO, projeto_id=foco.id, passo=TipoDePasso.IDENTIFICAR,
        tipo="apr", alvo_id=apr.id,
        justificativa="o plano de pré-requisitos já existia quando a análise começou",
    )

    (span,) = montagem["rastreador"].spans
    assert span.atributos["toc.vinculo_canonico"] is False
    assert span.atributos["toc.ferramenta_vinculada"] == "apr"
