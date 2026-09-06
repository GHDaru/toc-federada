"""M6 — exportação e importação da análise sem perda (spec 009, RF-18; DoD 11).

Siglas, uma vez neste arquivo: **M6** — Focalização · **M1** — Núcleo de Diagramas
Lógicos · **ARA** — Árvore da Realidade Atual · **APR** — Árvore de Pré-Requisitos ·
**JSON** — *JavaScript Object Notation* · **RF/RN** — requisito funcional / regra de
negócio.

**O que este arquivo prova, e o que ele deliberadamente NÃO prova.** A RF-18 diz que a
análise se exporta e importa "pelo E1.4 do M1". O E1.4 — exportação/importação canônica do
núcleo — **ainda não existe neste repositório**: a busca por `def exportar`/`def importar`
em `apps/api/src/toc_api` devolve apenas a ação de catálogo `toc.exportar_projeto`, que
resume um projeto e não o serializa. O que este ciclo entrega, então, é a **metade que é
dele**: a forma canônica da análise de focalização, com a ida e volta medida e a
referência sem destino declarada.

Quando o E1.4 nascer, `exportar_analise` é a função que ele chama para a parte do M6, e
este teste continua sendo a prova de que ela não perde nada. A dívida está registrada no
`qa-report.md` do ciclo, com a saída do `grep` colada.

Domínio puro: sem rede, sem banco, sem relógio.
"""
from __future__ import annotations

import json
from uuid import uuid4

import pytest

from toc_api.dominio.erros import DadoInvalido
from toc_api.dominio.focalizacao import (
    VERSAO_DA_EXPORTACAO,
    AnaliseDeFocalizacao,
    EstadoDoCiclo,
    ReferenciaDeOrigemDaRestricao,
    SistemaAnalisado,
    TipoDeFerramentaVinculada,
    TipoDePasso,
    TipoDeRestricao,
    VereditoDeHeranca,
    exportar_analise,
    importar_analise,
    nova_analise_de_focalizacao,
)

from .focalizacao_sintetica import (
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
    ID_DO_NO_DE_CAUSA_RAIZ,
    JUSTIFICATIVA_DA_RESTRICAO,
    NOME,
    OUTRO_DONO,
    RESTRICAO,
    SISTEMA,
    depois,
)


@pytest.fixture()
def cheia() -> AnaliseDeFocalizacao:
    """Uma análise com tudo o que a exportação tem de carregar: dois ciclos, um fechado."""
    analise = nova_analise_de_focalizacao(
        id=uuid4(),
        dono=DONO,
        nome=NOME,
        sistema=SistemaAnalisado(nome=SISTEMA, descricao=DESCRICAO_DO_SISTEMA),
        em=AGORA,
    )
    analise.vincular_ferramenta(
        TipoDePasso.IDENTIFICAR, tipo="ara", projeto_id=ID_DA_ARA, papel="causa raiz",
        em=depois(2),
    )
    analise.anotar_passo(
        TipoDePasso.IDENTIFICAR, texto="a fila cresce todo período", autor=AUTORA, em=depois(3)
    )
    analise.registrar_restricao(
        descricao=RESTRICAO,
        tipo=TipoDeRestricao.FISICA,
        justificativa=JUSTIFICATIVA_DA_RESTRICAO,
        autor=AUTORA,
        origem=ReferenciaDeOrigemDaRestricao(
            ferramenta="ara", projeto_id=ID_DA_ARA, no_id=ID_DO_NO_DE_CAUSA_RAIZ
        ),
        em=depois(5),
    )
    analise.concluir_passo(
        TipoDePasso.IDENTIFICAR, decisao="a restrição é a secretaria", autor=AUTORA,
        em=depois(10),
    )
    analise.concluir_passo(
        TipoDePasso.EXPLORAR, decisao=DECISAO_DE_EXPLORAR, autor=AUTORA, em=depois(20)
    )
    analise.vincular_ferramenta(
        TipoDePasso.SUBORDINAR, tipo="nc", projeto_id=ID_DA_NC, em=depois(25)
    )
    analise.concluir_passo(
        TipoDePasso.SUBORDINAR, decisao=DECISAO_DE_SUBORDINAR, autor=AUTORA, em=depois(30)
    )
    analise.vincular_ferramenta(
        TipoDePasso.ELEVAR, tipo="apr", projeto_id=ID_DA_APR, em=depois(35)
    )
    analise.concluir_passo(
        TipoDePasso.ELEVAR, decisao=DECISAO_DE_ELEVAR, autor=AUTORA, em=depois(40)
    )
    analise.reabrir_passo_anterior(
        justificativa="o plano mudou depois da reunião", autor=AUTORA, em=depois(42)
    )
    analise.concluir_passo(
        TipoDePasso.ELEVAR, decisao="contratar três pessoas", autor=AUTORA, em=depois(43)
    )
    analise.recomecar(em=depois(50))
    herdada = analise.ciclo_aberto.heranca[0]
    analise.julgar_heranca(
        herdada.id,
        veredito=VereditoDeHeranca.REVOGADA,
        justificativa="a restrição migrou de etapa",
        autor=AUTORA,
        em=depois(55),
    )
    return analise


# ---------------------------------------------------------------------------------------
# DoD 11 — ida e volta sem perda
# ---------------------------------------------------------------------------------------


def test_a_ida_e_volta_preserva_a_analise_inteira(cheia: AnaliseDeFocalizacao):
    documento = exportar_analise(cheia)
    voltou, pendentes = importar_analise(
        documento,
        id=uuid4(),
        dono=OUTRO_DONO,
        projetos_existentes=(ID_DA_ARA, ID_DA_NC, ID_DA_APR),
    )

    assert pendentes == ()
    assert exportar_analise(voltou) == documento, "a segunda exportação é idêntica à primeira"

    # O que a igualdade acima cobre e o `retrato()` não cobriria: os IDENTIFICADORES são
    # novos de propósito. Uma restrição importada é outra linha, num outro inquilino, num
    # outro banco — carregar o identificador de origem faria duas análises distintas
    # reivindicarem a mesma identidade no dia em que voltassem para o mesmo destino. O que
    # tem de sobreviver é o CONTEÚDO, e é ele que o documento carrega.
    assert voltou.ciclo_aberto.id != cheia.ciclo_aberto.id
    assert voltou.ciclos[0].restricao.id != cheia.ciclos[0].restricao.id
    assert voltou.ciclos[0].restricao.descricao == cheia.ciclos[0].restricao.descricao
    assert [p.estado for p in voltou.ciclos[0].passos] == [
        p.estado for p in cheia.ciclos[0].passos
    ]
    assert [
        tuple(d.texto for d in p.decisoes) for p in voltou.ciclos[0].passos
    ] == [tuple(d.texto for d in p.decisoes) for p in cheia.ciclos[0].passos]


def test_a_ida_e_volta_atravessa_json_de_verdade(cheia: AnaliseDeFocalizacao):
    """Exportação que não sobrevive a `json.dumps` não é exportação, é dicionário."""
    texto = json.dumps(exportar_analise(cheia), ensure_ascii=False, sort_keys=True)
    voltou, _ = importar_analise(json.loads(texto), id=uuid4(), dono=DONO)

    assert json.dumps(exportar_analise(voltou), ensure_ascii=False, sort_keys=True) == texto


def test_o_documento_preserva_ciclo_fechado_decisoes_notas_e_reaberturas(
    cheia: AnaliseDeFocalizacao,
):
    documento = exportar_analise(cheia)
    fechado = documento["ciclos"][0]

    assert fechado["estado"] == "fechado"
    assert fechado["fechado_em"] is not None
    assert fechado["restricao"]["descricao"] == RESTRICAO
    assert fechado["restricao"]["origem"]["ferramenta"] == "ara"
    elevar = next(p for p in fechado["passos"] if p["tipo"] == "elevar")
    assert [d["texto"] for d in elevar["decisoes"]] == [
        DECISAO_DE_ELEVAR,
        "contratar três pessoas",
    ]
    assert len(elevar["reaberturas"]) == 1
    identificar = next(p for p in fechado["passos"] if p["tipo"] == "identificar")
    assert [n["texto"] for n in identificar["notas"]] == ["a fila cresce todo período"]


def test_o_veredito_da_heranca_atravessa_a_exportacao(cheia: AnaliseDeFocalizacao):
    """RN-05: o julgamento é história, e história que não exporta é história perdida."""
    documento = exportar_analise(cheia)
    aberto = documento["ciclos"][1]

    julgada = [h for h in aberto["heranca"] if h["veredito"] == "revogada"]
    assert len(julgada) == 1
    assert julgada[0]["justificativa"] == "a restrição migrou de etapa"
    assert julgada[0]["autor"] == AUTORA
    assert julgada[0]["ciclo_de_origem"] == 1


def test_os_vinculos_viajam_como_referencia_nunca_como_copia(cheia: AnaliseDeFocalizacao):
    """RF-18: "vínculos (como referências)" — nenhum conteúdo dos outros módulos."""
    documento = exportar_analise(cheia)
    campos = {
        chave
        for ciclo in documento["ciclos"]
        for passo in ciclo["passos"]
        for vinculo in passo["vinculos"]
        for chave in vinculo
    }
    assert campos == {"ferramenta", "projeto_id", "papel", "justificativa", "canonico"}


# ---------------------------------------------------------------------------------------
# RF-18 — vínculo sem destino é PENDÊNCIA DECLARADA, nunca falha silenciosa
# ---------------------------------------------------------------------------------------


def test_vinculo_cujo_projeto_nao_existe_no_destino_e_declarado_pendente(
    cheia: AnaliseDeFocalizacao,
):
    documento = exportar_analise(cheia)

    voltou, pendentes = importar_analise(
        documento,
        id=uuid4(),
        dono=OUTRO_DONO,
        # No destino existe a Árvore da Realidade Atual, mas não a Nuvem nem a Árvore de
        # Pré-Requisitos: é o caso normal de mover uma análise entre inquilinos.
        projetos_existentes=(ID_DA_ARA,),
    )

    assert len(pendentes) == 2
    assert {p.ferramenta for p in pendentes} == {
        TipoDeFerramentaVinculada.NC,
        TipoDeFerramentaVinculada.APR,
    }
    assert {p.passo for p in pendentes} == {TipoDePasso.SUBORDINAR, TipoDePasso.ELEVAR}
    assert all(p.ciclo == 1 for p in pendentes)
    # E o vínculo NÃO sumiu: ele entrou, e a pendência é o aviso — nunca o apagamento.
    fechado = voltou.ciclos[0]
    assert len(fechado.passo(TipoDePasso.SUBORDINAR).vinculos) == 1
    assert len(fechado.passo(TipoDePasso.ELEVAR).vinculos) == 1


def test_sem_lista_de_projetos_conhecidos_nada_e_declarado_pendente(
    cheia: AnaliseDeFocalizacao,
):
    """A lista vazia significa "não sei o que existe lá", e não "nada existe lá".

    A diferença importa: declarar 30 pendências porque quem chamou não passou a lista
    seria ruído, e ruído treina quem lê a ignorar o aviso — que é como um aviso deixa de
    funcionar.
    """
    _, pendentes = importar_analise(exportar_analise(cheia), id=uuid4(), dono=DONO)
    assert pendentes == ()


# ---------------------------------------------------------------------------------------
# O que a importação NÃO faz
# ---------------------------------------------------------------------------------------


def test_a_identidade_vem_de_quem_importa_nunca_do_documento(cheia: AnaliseDeFocalizacao):
    """Identidade é da fundação (P2). Um export que carregasse o dono escreveria no
    inquilino errado — e o documento exportado nem tem onde guardá-lo."""
    documento = exportar_analise(cheia)
    assert "dono" not in json.dumps(documento)
    assert DONO.inquilino_id not in json.dumps(documento)

    voltou, _ = importar_analise(documento, id=uuid4(), dono=OUTRO_DONO)
    assert voltou.projeto.dono == OUTRO_DONO


def test_importar_nao_emite_evento_nenhum(cheia: AnaliseDeFocalizacao):
    """Importar não é viver a jornada de novo — a mesma regra da reidratação."""
    voltou, _ = importar_analise(exportar_analise(cheia), id=uuid4(), dono=DONO)
    assert voltou.projeto.eventos == ()


def test_documento_de_versao_desconhecida_e_recusado(cheia: AnaliseDeFocalizacao):
    documento = exportar_analise(cheia)
    documento["versao"] = "toc.focalizacao/999"

    with pytest.raises(DadoInvalido) as erro:
        importar_analise(documento, id=uuid4(), dono=DONO)
    assert VERSAO_DA_EXPORTACAO in str(erro.value)


def test_a_analise_importada_continua_obedecendo_as_invariantes(cheia: AnaliseDeFocalizacao):
    """Importar não é uma porta dos fundos: o ciclo fechado continua fechado, e o aberto
    continua sendo um só (RN-02, RN-04)."""
    voltou, _ = importar_analise(exportar_analise(cheia), id=uuid4(), dono=DONO)

    assert [c.estado for c in voltou.ciclos] == [EstadoDoCiclo.FECHADO, EstadoDoCiclo.ABERTO]
    assert voltou.ciclo_aberto.ordem == 2
    with pytest.raises(Exception):
        voltou.ciclos[0].exigir_aberto("anotar")
