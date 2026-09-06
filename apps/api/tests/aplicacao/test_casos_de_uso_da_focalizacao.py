"""M6 — os casos de uso da jornada sobre as portas (spec 009, T-08).

Siglas, uma vez neste arquivo: **M6** — Focalização · **M1** — Núcleo de Diagramas
Lógicos · **ARA** — Árvore da Realidade Atual · **NC** — Nuvem de Conflito · **APR** —
Árvore de Pré-Requisitos · **OTel** — OpenTelemetry · **RF/RN/RNF** — requisito funcional
/ regra de negócio / requisito não funcional.

O que esta suíte prova, e o que ela deliberadamente não prova: aqui está a **orquestração**
— carregar pela porta, agir na raiz, gravar pela mesma porta, e o span de nascença (P5).
Persistência é `tests/integracao/`, contra o PostgreSQL real; autorização é
`tests/aplicacao/test_governanca_de_capacidades.py` mais os testes de contrato.
"""
from __future__ import annotations

from uuid import uuid4

import pytest

from toc_api.aplicacao.focalizacao import (
    AbrirAnaliseDeFocalizacao,
    AnotarPasso,
    ConcluirPasso,
    CriarAnaliseDeFocalizacao,
    EditarRestricao,
    JulgarDecisaoHerdada,
    LinhaDoTempoDaAnalise,
    ListarAnalisesDeFocalizacao,
    MapaDaJornadaDaAnalise,
    ReabrirPassoAnterior,
    Recomecar,
    RegistrarRestricao,
    RemoverVinculo,
    VincularFerramenta,
)
from toc_api.dominio.erros import NaoEncontrado
from toc_api.dominio.focalizacao import (
    EstadoDoCiclo,
    EstadoDoPasso,
    TipoDePasso,
    TipoDeRestricao,
    VereditoDeHeranca,
)
from toc_api.dominio.projeto import Projeto

from ..dominio.focalizacao_sintetica import (
    AGORA,
    AUTORA,
    DECISAO_DE_ELEVAR,
    DECISAO_DE_EXPLORAR,
    DECISAO_DE_SUBORDINAR,
    DESCRICAO_DO_SISTEMA,
    DONO,
    ID_DA_APR,
    ID_DA_ARA,
    ID_DA_NC,
    JUSTIFICATIVA_DA_RESTRICAO,
    NOME,
    OUTRO_DONO,
    RESTRICAO,
    SISTEMA,
    depois,
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


def criar(montagem) -> Projeto:
    return CriarAnaliseDeFocalizacao(**montagem).rodar(
        dono=DONO, nome=NOME, sistema=SISTEMA, descricao_do_sistema=DESCRICAO_DO_SISTEMA
    )


def registrar_restricao(montagem, projeto_id):
    return RegistrarRestricao(**montagem).rodar(
        dono=DONO,
        projeto_id=projeto_id,
        descricao=RESTRICAO,
        tipo=TipoDeRestricao.FISICA,
        justificativa=JUSTIFICATIVA_DA_RESTRICAO,
        autor=AUTORA,
    )


# ---------------------------------------------------------------------------------------
# RF-01/RF-02 — criar, abrir, listar
# ---------------------------------------------------------------------------------------


def test_criar_grava_a_analise_pela_porta_e_abre_o_span(montagem):
    projeto = criar(montagem)

    assert projeto.ferramenta == "focalizacao"
    guardada = montagem["repositorio"].analises[projeto.id]
    assert guardada.ciclo_aberto.ordem == 1
    assert guardada.passo_atual.tipo is TipoDePasso.IDENTIFICAR
    assert montagem["rastreador"].nomes == ["caso_de_uso.criar_analise_de_focalizacao"]
    (span,) = montagem["rastreador"].spans
    assert span.atributos["toc.inquilino_id"] == DONO.inquilino_id
    assert span.atributos["toc.resultado"] == "ok"


def test_o_span_carrega_grandeza_e_nunca_texto_de_pessoa(montagem):
    """ADR 0006 + P5: passo, contagem e enum — nunca o enunciado que alguém escreveu."""
    projeto = criar(montagem)
    montagem["rastreador"].spans.clear()
    registrar_restricao(montagem, projeto.id)

    (span,) = montagem["rastreador"].spans
    valores = [str(v) for v in span.atributos.values()]
    assert RESTRICAO not in valores
    assert JUSTIFICATIVA_DA_RESTRICAO not in valores
    assert span.atributos["toc.tipo_de_restricao"] == "fisica"
    assert span.atributos["toc.tem_origem"] is False


def test_abrir_analise_de_outro_inquilino_e_indistinguivel_de_inexistente(montagem):
    projeto = criar(montagem)
    with pytest.raises(NaoEncontrado):
        AbrirAnaliseDeFocalizacao(**montagem).rodar(dono=OUTRO_DONO, projeto_id=projeto.id)


def test_abrir_projeto_que_nao_e_focalizacao_e_nao_encontrado(montagem):
    """Um projeto de outra ferramenta não vira análise porque alguém pediu por aqui."""
    with pytest.raises(NaoEncontrado):
        AbrirAnaliseDeFocalizacao(**montagem).rodar(dono=DONO, projeto_id=uuid4())


def test_listar_traz_passo_atual_e_restricao_vigente_de_cada_analise(montagem):
    """RF-03: as duas colunas de primeira classe da listagem (RI-07)."""
    primeira = criar(montagem)
    registrar_restricao(montagem, primeira.id)
    ConcluirPasso(**montagem).rodar(
        dono=DONO, projeto_id=primeira.id, passo=TipoDePasso.IDENTIFICAR,
        decisao="a restrição é a secretaria", autor=AUTORA,
    )
    segunda = CriarAnaliseDeFocalizacao(**montagem).rodar(
        dono=DONO, nome="Fluxo de estágio", sistema="Da vaga ao termo assinado"
    )

    linhas = ListarAnalisesDeFocalizacao(**montagem).rodar(dono=DONO)

    por_id = {linha.projeto_id: linha for linha in linhas}
    assert por_id[primeira.id].passo_atual is TipoDePasso.EXPLORAR
    assert por_id[primeira.id].restricao == RESTRICAO
    assert por_id[primeira.id].ciclo == 1
    assert por_id[segunda.id].passo_atual is TipoDePasso.IDENTIFICAR
    assert por_id[segunda.id].restricao is None


def test_listar_nao_atravessa_a_fronteira_do_inquilino(montagem):
    criar(montagem)
    assert ListarAnalisesDeFocalizacao(**montagem).rodar(dono=OUTRO_DONO) == []


# ---------------------------------------------------------------------------------------
# RF-05..RF-13 — a jornada pela borda
# ---------------------------------------------------------------------------------------


def test_registrar_restricao_grava_e_a_traz_no_mapa(montagem):
    projeto = criar(montagem)
    registrar_restricao(montagem, projeto.id)

    mapa = MapaDaJornadaDaAnalise(**montagem).rodar(dono=DONO, projeto_id=projeto.id)
    assert mapa.restricao.descricao == RESTRICAO
    assert mapa.resumo()["tem_restricao"] is True


def test_editar_restricao_pela_borda_nao_aceita_trocar_o_tipo(montagem):
    """RF-07 + RN-03: o caso de uso não tem por onde receber o tipo."""
    import inspect

    projeto = criar(montagem)
    registrar_restricao(montagem, projeto.id)
    EditarRestricao(**montagem).rodar(
        dono=DONO, projeto_id=projeto.id, descricao="Conferência documental da secretaria"
    )

    parametros = inspect.signature(EditarRestricao.executar).parameters
    assert "tipo" not in parametros
    mapa = MapaDaJornadaDaAnalise(**montagem).rodar(dono=DONO, projeto_id=projeto.id)
    assert mapa.restricao.tipo is TipoDeRestricao.FISICA


def test_concluir_anotar_e_reabrir_atravessam_a_porta(montagem):
    projeto = criar(montagem)
    registrar_restricao(montagem, projeto.id)
    AnotarPasso(**montagem).rodar(
        dono=DONO, projeto_id=projeto.id, passo=TipoDePasso.IDENTIFICAR,
        texto="a fila cresce todo período", autor=AUTORA,
    )
    ConcluirPasso(**montagem).rodar(
        dono=DONO, projeto_id=projeto.id, passo=TipoDePasso.IDENTIFICAR,
        decisao="a restrição é a secretaria", autor=AUTORA,
    )
    ReabrirPassoAnterior(**montagem).rodar(
        dono=DONO, projeto_id=projeto.id, justificativa="a medição mudou", autor=AUTORA
    )

    guardada = montagem["repositorio"].analises[projeto.id]
    passo = guardada.ciclo_aberto.passo(TipoDePasso.IDENTIFICAR)
    assert passo.estado is EstadoDoPasso.EM_ANDAMENTO
    assert len(passo.decisoes) == 1
    assert len(passo.notas) == 1


def test_o_span_de_concluir_carrega_o_passo_e_o_progresso(montagem):
    projeto = criar(montagem)
    registrar_restricao(montagem, projeto.id)
    montagem["rastreador"].spans.clear()
    ConcluirPasso(**montagem).rodar(
        dono=DONO, projeto_id=projeto.id, passo=TipoDePasso.IDENTIFICAR,
        decisao="a restrição é a secretaria", autor=AUTORA,
    )
    (span,) = montagem["rastreador"].spans
    assert span.atributos["toc.passo"] == "identificar"
    assert span.atributos["toc.passos_concluidos"] == 1
    assert span.atributos["toc.passo_atual"] == "explorar"


def test_a_recusa_do_dominio_marca_o_span_e_reergue(montagem):
    """Recusa também é traço (P5): o span registra o erro e a exceção sobe."""
    from toc_api.dominio.focalizacao import PassoInvalido

    projeto = criar(montagem)
    montagem["rastreador"].spans.clear()
    with pytest.raises(PassoInvalido):
        ConcluirPasso(**montagem).rodar(
            dono=DONO, projeto_id=projeto.id, passo=TipoDePasso.IDENTIFICAR,
            decisao="sem restrição nenhuma", autor=AUTORA,
        )
    (span,) = montagem["rastreador"].spans
    assert span.atributos["toc.resultado"] == "erro"
    assert span.atributos["toc.erro"] == "PassoInvalido"


# ---------------------------------------------------------------------------------------
# RF-15/RF-16 — recomeço e herança
# ---------------------------------------------------------------------------------------


def test_recomecar_e_julgar_heranca_pela_borda(montagem):
    projeto = criar(montagem)
    _travessia(montagem, projeto.id)

    Recomecar(**montagem).rodar(dono=DONO, projeto_id=projeto.id)

    guardada = montagem["repositorio"].analises[projeto.id]
    assert [c.estado for c in guardada.ciclos] == [EstadoDoCiclo.FECHADO, EstadoDoCiclo.ABERTO]
    herdadas = guardada.ciclo_aberto.heranca
    assert len(herdadas) == 2

    JulgarDecisaoHerdada(**montagem).rodar(
        dono=DONO,
        projeto_id=projeto.id,
        decisao_id=herdadas[0].id,
        veredito=VereditoDeHeranca.REVOGADA,
        justificativa="a restrição mudou de etapa",
        autor=AUTORA,
    )
    guardada = montagem["repositorio"].analises[projeto.id]
    assert guardada.ciclo_aberto.decisao_herdada(herdadas[0].id).veredito is (
        VereditoDeHeranca.REVOGADA
    )


def test_o_span_do_recomeco_conta_ciclos_e_herancas(montagem):
    projeto = criar(montagem)
    _travessia(montagem, projeto.id)
    montagem["rastreador"].spans.clear()

    Recomecar(**montagem).rodar(dono=DONO, projeto_id=projeto.id)

    (span,) = montagem["rastreador"].spans
    assert span.atributos["toc.ciclo_fechado"] == 1
    assert span.atributos["toc.ciclo_aberto"] == 2
    assert span.atributos["toc.herancas_pendentes"] == 2


def test_a_linha_do_tempo_pela_borda(montagem):
    projeto = criar(montagem)
    _travessia(montagem, projeto.id)
    Recomecar(**montagem).rodar(dono=DONO, projeto_id=projeto.id)

    linha = LinhaDoTempoDaAnalise(**montagem).rodar(dono=DONO, projeto_id=projeto.id)
    assert [e.ordem for e in linha] == [1, 2]
    assert linha[0].restricao == RESTRICAO
    assert linha[1].herancas_pendentes == 2


# ---------------------------------------------------------------------------------------
# apoio
# ---------------------------------------------------------------------------------------


def _travessia(montagem, projeto_id) -> None:
    registrar_restricao(montagem, projeto_id)
    for passo, decisao in (
        (TipoDePasso.IDENTIFICAR, "a restrição é a secretaria"),
        (TipoDePasso.EXPLORAR, DECISAO_DE_EXPLORAR),
        (TipoDePasso.SUBORDINAR, DECISAO_DE_SUBORDINAR),
        (TipoDePasso.ELEVAR, DECISAO_DE_ELEVAR),
    ):
        ConcluirPasso(**montagem).rodar(
            dono=DONO, projeto_id=projeto_id, passo=passo, decisao=decisao, autor=AUTORA
        )
