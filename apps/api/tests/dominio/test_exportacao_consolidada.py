"""E1.4 — a exportação consolidada e a ida e volta que a prova (spec 011, RF-31 e RF-32).

Siglas, uma vez neste arquivo: **ARA** — Árvore da Realidade Atual · **UDE** — Efeito
Indesejável · **NC** — Nuvem de Conflito · **ARF** — Árvore da Realidade Futura · **APR**
— Árvore de Pré-Requisitos · **AT** — Árvore de Transição · **S&T** — Estratégia &
Táticas · **JSON** — *JavaScript Object Notation* · **UUID** — identificador único
universal · **RF/RN** — requisito funcional / regra de negócio.

**O que estes testes provam, e por que cada um existe:**

- **RF-31** — um projeto que atravessou ARA → NC → ARF → APR → AT sai num arquivo só, com
  seção por ferramenta E os vínculos entre elas. A US-17 diz o motivo em uma linha: "não
  seis arquivos soltos".
- **RF-32** — exportar, importar e exportar de novo produz arquivo estruturalmente
  idêntico, **a menos de identificadores e carimbos**. É a prova de que a ida e volta não
  perde conteúdo — e a de que não o duplica.
- **RN-05** — importar **nunca** muta projeto existente: nascem projetos novos, com
  identificadores novos, e o relato conta o que entrou. É a regra herdada do M1 (ciclo
  004, RF-35), e aqui ela é testada contra a cadeia inteira.
- **RF-27** — arquivo inválido não cria nada e explica **campo a campo**. O contraste
  medido é `tocbuilderv3/components/NodeZoneView.tsx:314-317`: três campos conferidos,
  `alert()` genérico, e o resto passando.

Base sintética (ADR 0006 — *Architecture Decision Record*): "Instituição Horizonte".
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from uuid import UUID, uuid4

import pytest

from toc_api.dominio.apr import ProjetoAPR
from toc_api.dominio.ara import ProjetoARA, StatusDeValidacao
from toc_api.dominio.arf import ProjetoARF
from toc_api.dominio.at import ProjetoAT, StatusDoPasso
from toc_api.dominio.exportacao import (
    VERSAO_DO_CONSOLIDADO,
    esqueleto,
    exportar_consolidado,
    importar_consolidado,
)
from toc_api.dominio.identidade import DonoDoProjeto
from toc_api.dominio.nuvem import NuvemDeConflito, StatusDeInjecao
from toc_api.dominio.snt import ArvoreSnT

from .cadeia_sintetica import AGORA, DONO, montar_cadeia, montar_snt

DEPOIS = datetime(2026, 9, 7, 8, 0, tzinfo=timezone.utc)
OUTRO_DONO = DonoDoProjeto(inquilino_id="instituicao-aurora", usuario_id="u-aurora")


def exportar(cadeia) -> dict:
    return exportar_consolidado(
        cadeia.projetos, vinculos=cadeia.vinculos, exportado_em=AGORA
    )


# ---------------------------------------------------------------------------------------
# RF-31 — um arquivo, seções por ferramenta, vínculos contados
# ---------------------------------------------------------------------------------------


def test_exporta_as_cinco_ferramentas_e_os_quatro_vinculos_num_arquivo_so() -> None:
    documento = exportar(montar_cadeia())

    ferramentas = [p["ferramenta"] for p in documento["projetos"]]
    print(f"ferramentas exportadas: {ferramentas} · vínculos: {len(documento['vinculos'])}")
    assert documento["versao"] == VERSAO_DO_CONSOLIDADO
    assert ferramentas == ["ara", "nc", "arf", "apr", "at"]
    assert len(documento["vinculos"]) == 4
    assert [v["tipo"] for v in documento["vinculos"]] == [
        "promocao_ude_nc",
        "semeadura_injecao_arf",
        "derivacao_arf_apr",
        "derivacao_oi_at",
    ]


def test_cada_secao_carrega_o_estado_que_so_a_ferramenta_conhece() -> None:
    documento = exportar(montar_cadeia())
    por_ferramenta = {p["ferramenta"]: p for p in documento["projetos"]}

    ara = por_ferramenta["ara"]["secao"]
    nc = por_ferramenta["nc"]["secao"]
    arf = por_ferramenta["arf"]["secao"]
    apr = por_ferramenta["apr"]["secao"]
    at = por_ferramenta["at"]["secao"]
    print(
        f"ARA: {len(ara['udes'])} UDE(s), {len(ara['exames'])} exame(s), "
        f"{len(ara['conectores'])} conector(es) · NC: {len(nc['premissas'])} premissa(s), "
        f"{len(nc['injecoes'])} injeção(ões) · ARF: {len(arf['ramos'])} ramo(s) · "
        f"APR: {len(apr['pares'])} par(es) · AT: {len(at['fichas'])} ficha(s)"
    )
    assert len(ara["udes"]) == 2 and len(ara["pareceres"]) == 2
    assert len(ara["exames"]) == 3 and len(ara["conectores"]) == 1
    assert nc["racional"].startswith("o grupo aceitou")
    assert len(nc["premissas"]) == 2 and len(nc["injecoes"]) == 1
    assert len(arf["espelhos"]) == 1 and len(arf["ramos"]) == 1
    assert len(apr["pares"]) == 1 and apr["pares"][0]["julgamentos"]
    assert len(at["fichas"]) == 1


def test_o_documento_nao_carrega_inquilino_nem_usuario() -> None:
    """Identidade é da fundação: importar num destino é adotar a identidade de LÁ."""
    bruto = json.dumps(exportar(montar_cadeia()))
    print(f"documento com {len(bruto)} caracteres; procurando identidade dentro dele")
    assert DONO.inquilino_id not in bruto
    assert DONO.usuario_id not in bruto
    assert "inquilino" not in bruto and "usuario" not in bruto


def test_a_exportacao_e_deterministica_byte_a_byte() -> None:
    """Comparar dois exports é a primeira coisa que se faz com um export."""
    cadeia = montar_cadeia()
    primeiro = json.dumps(exportar(cadeia), ensure_ascii=False)
    segundo = json.dumps(exportar(cadeia), ensure_ascii=False)
    assert primeiro == segundo


def test_a_ferramenta_com_documento_proprio_delega_em_vez_de_inventar_formato() -> None:
    """S&T e focalização já têm formato canônico (RF-21 da 010, RF-18 da 009)."""
    documento = exportar_consolidado((montar_snt(),), exportado_em=AGORA)
    entrada = documento["projetos"][0]
    print(f"forma={entrada['forma']} · versão da seção={entrada['secao']['versao']}")
    assert entrada["forma"] == "documento_da_ferramenta"
    assert entrada["secao"]["versao"] == "toc.snt/1"


# ---------------------------------------------------------------------------------------
# RF-32 — a ida e volta
# ---------------------------------------------------------------------------------------


def test_ida_e_volta_produz_documento_estruturalmente_identico() -> None:
    cadeia = montar_cadeia()
    primeiro = exportar(cadeia)

    resultado = importar_consolidado(primeiro, dono=OUTRO_DONO)
    segundo = exportar_consolidado(
        resultado.projetos, vinculos=resultado.vinculos, exportado_em=DEPOIS
    )

    print(
        f"relato: {dict(resultado.relato.contagens)} · problemas: "
        f"{len(resultado.relato.problemas)}"
    )
    assert resultado.relato.aceito
    assert esqueleto(primeiro) == esqueleto(segundo)


def test_a_igualdade_nao_e_trivial_os_identificadores_mudaram_todos() -> None:
    """Sem esta conferência, a ida e volta passaria verde sobre uma cópia por referência."""
    cadeia = montar_cadeia()
    primeiro = exportar(cadeia)
    resultado = importar_consolidado(primeiro, dono=OUTRO_DONO)
    segundo = exportar_consolidado(
        resultado.projetos, vinculos=resultado.vinculos, exportado_em=DEPOIS
    )

    antes = set(_uuids(primeiro))
    depois = set(_uuids(segundo))
    print(f"{len(antes)} identificador(es) no primeiro, {len(depois)} no segundo, "
          f"{len(antes & depois)} em comum")
    assert antes and depois
    assert not (antes & depois)


def test_o_conteudo_escrito_por_pessoa_atravessa_a_ida_e_volta_sem_mudar() -> None:
    cadeia = montar_cadeia()
    resultado = importar_consolidado(exportar(cadeia), dono=OUTRO_DONO)
    por_ferramenta = {_ferramenta(p): p for p in resultado.projetos}

    ara: ProjetoARA = por_ferramenta["ara"]
    nuvem: NuvemDeConflito = por_ferramenta["nc"]
    at: ProjetoAT = por_ferramenta["at"]
    titulos = sorted(n.titulo for n in ara.nos)
    print(f"títulos da ARA importada: {titulos}")
    assert titulos == sorted(n.titulo for n in cadeia.ara.nos)
    assert nuvem.racional == cadeia.nuvem.racional
    assert [f.acao for f in at._fichas.values()] == [
        f.acao for f in cadeia.at._fichas.values()
    ]


def test_o_estado_de_cada_ferramenta_volta_inteiro_e_apontando_para_os_novos_nos() -> None:
    """A referência interna é o que uma remarcação ingênua de identificador quebra."""
    cadeia = montar_cadeia()
    resultado = importar_consolidado(exportar(cadeia), dono=OUTRO_DONO)
    por_ferramenta = {_ferramenta(p): p for p in resultado.projetos}

    ara: ProjetoARA = por_ferramenta["ara"]
    nuvem: NuvemDeConflito = por_ferramenta["nc"]
    arf: ProjetoARF = por_ferramenta["arf"]
    apr: ProjetoAPR = por_ferramenta["apr"]

    nos_da_ara = {n.id for n in ara.nos}
    arestas_da_ara = {a.id for a in ara.arestas}
    assert set(ara.udes) <= nos_da_ara
    assert all(ara.status(u) is StatusDeValidacao.VALIDADO for u in ara.udes)
    assert set(ara._exames) <= arestas_da_ara
    conector = ara.conectores[0]
    assert set(conector.arestas) <= arestas_da_ara and conector.destino_id in nos_da_ara

    injecao = next(iter(nuvem._injecoes.values()))
    assert injecao.premissa_id in nuvem._premissas
    assert injecao.status is StatusDeInjecao.ESCOLHIDA
    assert nuvem.origem.projeto_id == ara.projeto.id
    assert set(nuvem.origem.nos) <= nos_da_ara

    assert arf.origem.projeto_id == nuvem.projeto.id
    assert set(arf.udes_da_cadeia) <= nos_da_ara
    ramo = arf.ramos()[0]
    assert ramo.raiz_id in {n.id for n in arf.nos}

    par = apr.pares()[0]
    assert {par.obstaculo_id, par.objetivo_intermediario_id} <= {n.id for n in apr.projeto.nos}


def test_os_vinculos_sao_recriados_apontando_para_os_projetos_novos_e_contados() -> None:
    cadeia = montar_cadeia()
    resultado = importar_consolidado(exportar(cadeia), dono=OUTRO_DONO)

    ids = {p.projeto.id if hasattr(p, "projeto") else p.id for p in resultado.projetos}
    print(f"vínculos recriados: {resultado.relato.contagens['vinculos']}")
    assert resultado.relato.contagens["vinculos"] == 4
    for vinculo in resultado.vinculos:
        assert vinculo.origem.projeto_id in ids
        assert vinculo.destino.projeto_id in ids
        assert vinculo.dono == OUTRO_DONO


def test_a_ferramenta_com_documento_proprio_tambem_faz_a_ida_e_volta() -> None:
    documento = exportar_consolidado((montar_snt(),), exportado_em=AGORA)
    resultado = importar_consolidado(documento, dono=OUTRO_DONO)
    arvore: ArvoreSnT = resultado.projetos[0]

    de_volta = exportar_consolidado(resultado.projetos, exportado_em=DEPOIS)
    print(f"S&T importada: meta={arvore.meta_global!r}, {len(arvore.projeto.nos)} passo(s)")
    assert isinstance(arvore, ArvoreSnT)
    assert esqueleto(documento) == esqueleto(de_volta)


# ---------------------------------------------------------------------------------------
# RN-05 — importar cria projeto novo, e não toca no que já existe
# ---------------------------------------------------------------------------------------


def test_importar_nao_muta_o_que_ja_existe() -> None:
    cadeia = montar_cadeia()
    retrato = lambda: [
        (p.projeto.id, p.projeto.versao, len(p.projeto.nos), len(p.projeto.arestas),
         len(p.projeto.eventos))
        for p in cadeia.projetos
    ]
    antes = retrato()

    importar_consolidado(exportar(cadeia), dono=OUTRO_DONO)

    depois = retrato()
    print(f"origem antes={antes[0]} depois={depois[0]}")
    assert antes == depois


def test_o_dono_vem_de_quem_importa_e_nunca_do_documento() -> None:
    resultado = importar_consolidado(exportar(montar_cadeia()), dono=OUTRO_DONO)
    for projeto in resultado.projetos:
        assert projeto.projeto.dono == OUTRO_DONO


def test_importar_duas_vezes_o_mesmo_arquivo_cria_dois_conjuntos_distintos() -> None:
    documento = exportar(montar_cadeia())
    primeira = importar_consolidado(documento, dono=OUTRO_DONO)
    segunda = importar_consolidado(documento, dono=OUTRO_DONO)

    um = {p.projeto.id for p in primeira.projetos}
    dois = {p.projeto.id for p in segunda.projetos}
    print(f"primeira importação: {len(um)} projeto(s); segunda: {len(dois)}; comuns: {len(um & dois)}")
    assert not (um & dois)


def test_a_importacao_nao_emite_evento_nenhum() -> None:
    """Importar não é viver a análise de novo — a mesma regra do M6 e do M5.

    A cadeia de origem TEM eventos pendentes (o encadeamento emite na ponta de origem a
    cada derivação); os agregados importados não podem ter nenhum, ou abrir o projeto
    importado escreveria história que não aconteceu.
    """
    resultado = importar_consolidado(exportar(montar_cadeia()), dono=OUTRO_DONO)
    for projeto in resultado.projetos:
        assert projeto.projeto.eventos == ()


# ---------------------------------------------------------------------------------------
# RF-27 — recusa campo a campo, sem criar nada
# ---------------------------------------------------------------------------------------


def test_aresta_apontando_para_no_inexistente_e_recusada_com_campo_e_motivo() -> None:
    documento = exportar(montar_cadeia())
    documento["projetos"][0]["arestas"][0]["destino_id"] = str(uuid4())

    resultado = importar_consolidado(documento, dono=OUTRO_DONO)

    print(f"problemas: {[(p.campo, p.motivo) for p in resultado.relato.problemas]}")
    assert not resultado.relato.aceito
    assert resultado.projetos == ()
    assert len(resultado.relato.problemas) == 1
    problema = resultado.relato.problemas[0]
    assert problema.campo.startswith("projetos[0].arestas[0].destino_id")
    assert "não existe" in problema.motivo


def test_dois_problemas_geram_dois_itens_no_relato_e_nada_e_criado() -> None:
    documento = exportar(montar_cadeia())
    documento["projetos"][0]["arestas"][0]["destino_id"] = str(uuid4())
    documento["projetos"][0]["nome"] = ""

    resultado = importar_consolidado(documento, dono=OUTRO_DONO)

    campos = [p.campo for p in resultado.relato.problemas]
    print(f"dois problemas, dois itens: {campos}")
    assert len(resultado.relato.problemas) == 2
    assert any(c.endswith(".nome") for c in campos)
    assert resultado.projetos == ()


def test_vinculo_para_projeto_fora_do_arquivo_e_problema_e_nao_silencio() -> None:
    documento = exportar(montar_cadeia())
    documento["vinculos"][0]["destino"]["projeto_id"] = str(uuid4())

    resultado = importar_consolidado(documento, dono=OUTRO_DONO)

    assert not resultado.relato.aceito
    assert any("vinculos[0]" in p.campo for p in resultado.relato.problemas)


def test_versao_desconhecida_e_recusada_nomeando_a_que_esta_aplicacao_le() -> None:
    documento = exportar(montar_cadeia())
    documento["versao"] = "toc.consolidado/99"

    resultado = importar_consolidado(documento, dono=OUTRO_DONO)

    problema = resultado.relato.problemas[0]
    print(f"recusa de versão: {problema.campo} — {problema.motivo}")
    assert problema.campo == "versao"
    assert VERSAO_DO_CONSOLIDADO in problema.motivo


def test_campo_desconhecido_na_secao_e_recusado_em_vez_de_ignorado() -> None:
    documento = exportar(montar_cadeia())
    documento["projetos"][0]["secao"]["invencao"] = {"x": 1}

    resultado = importar_consolidado(documento, dono=OUTRO_DONO)

    print(f"campo inventado: {[p.campo for p in resultado.relato.problemas]}")
    assert not resultado.relato.aceito
    assert any("invencao" in p.campo or "invencao" in p.motivo for p in resultado.relato.problemas)


def test_documento_que_nao_e_objeto_nao_derruba_o_dominio() -> None:
    resultado = importar_consolidado(["isto não é um documento"], dono=OUTRO_DONO)
    assert not resultado.relato.aceito
    assert resultado.relato.problemas


# ---------------------------------------------------------------------------------------
# O relato: contagens por tipo de entidade
# ---------------------------------------------------------------------------------------


def test_o_relato_conta_por_tipo_de_entidade() -> None:
    resultado = importar_consolidado(exportar(montar_cadeia()), dono=OUTRO_DONO)
    contagens = dict(resultado.relato.contagens)
    print(f"contagens: {contagens}")
    assert contagens["projetos"] == 5
    assert contagens["nos"] == sum(len(p.projeto.nos) for p in resultado.projetos)
    assert contagens["arestas"] == sum(len(p.projeto.arestas) for p in resultado.projetos)
    assert contagens["vinculos"] == 4


def test_o_status_do_passo_da_at_sobrevive_a_ida_e_volta() -> None:
    cadeia = montar_cadeia()
    resultado = importar_consolidado(exportar(cadeia), dono=OUTRO_DONO)
    at: ProjetoAT = next(p for p in resultado.projetos if _ferramenta(p) == "at")
    ficha = next(iter(at._fichas.values()))
    print(f"status do passo importado: {ficha.status.value}")
    assert ficha.status is StatusDoPasso.EM_EXECUCAO


# ---------------------------------------------------------------------------------------


def _ferramenta(agregado) -> str:
    return agregado.projeto.ferramenta


def _uuids(valor, saida=None):
    saida = [] if saida is None else saida
    if isinstance(valor, dict):
        for chave, item in valor.items():
            _talvez_uuid(chave, saida)
            _uuids(item, saida)
    elif isinstance(valor, list):
        for item in valor:
            _uuids(item, saida)
    else:
        _talvez_uuid(valor, saida)
    return saida


def _talvez_uuid(valor, saida) -> None:
    if isinstance(valor, str):
        try:
            saida.append(str(UUID(valor)))
        except ValueError:
            return


@pytest.fixture(autouse=True)
def _sem_rede_e_sem_banco():
    """Marca de intenção: estes testes são de domínio puro — sem porta, sem adaptador."""
    yield


# ---------------------------------------------------------------------------------------
# Ordem canônica — o defeito que a ida e volta PELO BANCO revelou
# ---------------------------------------------------------------------------------------


def test_a_exportacao_nao_depende_da_ordem_em_que_o_repositorio_devolveu() -> None:
    """O documento é ordenado pelo CONTEÚDO, e não pela ordem de chegada.

    Achado pela ida e volta contra o PostgreSQL real: o adaptador devolve os nós por
    `(criado_em, id)` (`infra/persistencia/repositorio_projetos.py:560`), e os cinco nós
    de uma Nuvem de Conflito nascem no MESMO instante — logo o desempate é por
    identificador, que muda na importação. O conteúdo voltava inteiro e o arquivo saía com
    as linhas em outra ordem: dois exports da mesma análise deixavam de ser comparáveis,
    que é a única coisa que a RF-32 pede.
    """
    cadeia = montar_cadeia()
    original = exportar(cadeia)

    # A mesma nuvem, com os nós e as arestas embaralhados como o banco os devolveria.
    nuvem = cadeia.nuvem
    nuvem.projeto.nos = tuple(reversed(nuvem.projeto.nos))
    nuvem.projeto.arestas = tuple(reversed(nuvem.projeto.arestas))
    embaralhado = exportar(cadeia)

    print(
        f"nós da NC na origem: {[n['titulo'][:12] for n in original['projetos'][1]['nos']]}"
    )
    assert embaralhado == original
