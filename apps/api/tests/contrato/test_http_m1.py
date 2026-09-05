"""A superfície HTTP do M1 — projetos, nós e arestas (spec 004, contrato `rest-api.md`).

Cada resposta é validada contra o esquema que a própria aplicação **declara** no seu
OpenAPI, não contra o que o teste esperava: é o que separa contrato de expectativa.

Prefixo `/toc`, por decisão declarada. O guia da fundação, ao tratar da classe de colisão
que a admissão não alcança — módulos de inquilino que nascem depois da aprovação —, diz
que "escolher um prefixo próprio (`/toc/…`) é a defesa prática"
(`ghdaru/docs/integration/guia-desenvolvedor-app-federada.md`, leitura apenas). O esboço
de contrato do ciclo 001 escrevia `/api/toc`, e ele mesmo declara que não fixa o byte
final; `/api` seria um prefixo genérico a mais para colidir, sem nada a ganhar.
"""
from __future__ import annotations

from uuid import uuid4

import pytest

from .conftest import valida_contra_o_contrato, valida_envelope_de_erro

BOM = "A taxa de erros no processo X é de 15%."
OUTRO = "O retrabalho consome a equipe de análise."


def cria_projeto(plena, app, nome="Horizonte — diagrama"):
    r = plena.post("/toc/projetos", json={"nome": nome, "descricao_do_problema": "Ensaio."})
    assert r.status_code == 201, r.text
    return valida_contra_o_contrato(app, r, "POST", "/toc/projetos")


def cria_no(plena, app, projeto_id, titulo=BOM):
    r = plena.post(f"/toc/projetos/{projeto_id}/nos", json={"titulo": titulo})
    assert r.status_code == 201, r.text
    return valida_contra_o_contrato(app, r, "POST", "/toc/projetos/{projeto_id}/nos")


# -- projetos -----------------------------------------------------------------------


def test_criar_projeto_devolve_201_e_o_agregado_declarado(plena, app):
    corpo = cria_projeto(plena, app)
    assert corpo["nome"] == "Horizonte — diagrama"
    assert corpo["ferramenta"] == "generico"
    assert corpo["estado"] == "ativo"
    assert corpo["nos"] == [] and corpo["arestas"] == []


def test_listar_traz_so_os_ativos_do_inquilino(plena, app, outro_inquilino):
    meu = cria_projeto(plena, app, nome="Meu projeto")
    outro_inquilino.post("/toc/projetos", json={"nome": "Projeto alheio"})

    r = plena.get("/toc/projetos")
    corpo = valida_contra_o_contrato(app, r, "GET", "/toc/projetos")
    assert [p["id"] for p in corpo] == [meu["id"]]


def test_abrir_traz_metadados_nos_e_arestas_num_carregamento_so(plena, app):
    projeto = cria_projeto(plena, app)
    a = cria_no(plena, app, projeto["id"], BOM)
    b = cria_no(plena, app, projeto["id"], OUTRO)
    plena.post(
        f"/toc/projetos/{projeto['id']}/arestas",
        json={"origem_id": a["id"], "destino_id": b["id"], "rotulo": "leva a"},
    )

    r = plena.get(f"/toc/projetos/{projeto['id']}")
    corpo = valida_contra_o_contrato(app, r, "GET", "/toc/projetos/{projeto_id}")
    assert {n["id"] for n in corpo["nos"]} == {a["id"], b["id"]}
    assert corpo["arestas"][0]["rotulo"] == "leva a"


def test_projeto_de_outro_inquilino_responde_404_nunca_403(plena, app, outro_inquilino):
    """RNF-03: distinguir 'não existe' de 'é de outro' vazaria a existência alheia."""
    projeto = cria_projeto(plena, app)
    r = outro_inquilino.get(f"/toc/projetos/{projeto['id']}")
    assert r.status_code == 404
    assert valida_envelope_de_erro(r)["code"] == "NOT_FOUND"


def test_excluir_e_suave_some_da_lista_e_aparece_na_lixeira(plena, app):
    projeto = cria_projeto(plena, app)

    r = plena.delete(f"/toc/projetos/{projeto['id']}")
    corpo = valida_contra_o_contrato(app, r, "DELETE", "/toc/projetos/{projeto_id}")
    assert corpo["estado"] == "excluido" and corpo["excluido_em"] is not None

    assert plena.get("/toc/projetos").json() == []
    lixeira = valida_contra_o_contrato(
        app, plena.get("/toc/projetos/lixeira"), "GET", "/toc/projetos/lixeira"
    )
    assert [p["id"] for p in lixeira] == [projeto["id"]]


def test_restaurar_devolve_o_projeto_com_o_conteudo_intacto(plena, app):
    projeto = cria_projeto(plena, app)
    no = cria_no(plena, app, projeto["id"])
    plena.delete(f"/toc/projetos/{projeto['id']}")

    r = plena.post(f"/toc/projetos/{projeto['id']}/restaurar")
    corpo = valida_contra_o_contrato(
        app, r, "POST", "/toc/projetos/{projeto_id}/restaurar"
    )
    assert corpo["estado"] == "ativo"
    aberto = plena.get(f"/toc/projetos/{projeto['id']}").json()
    assert [n["id"] for n in aberto["nos"]] == [no["id"]]


def test_mutacao_em_projeto_excluido_e_recusada_com_codigo_estavel(plena, app):
    projeto = cria_projeto(plena, app)
    plena.delete(f"/toc/projetos/{projeto['id']}")
    r = plena.post(f"/toc/projetos/{projeto['id']}/nos", json={"titulo": BOM})
    assert r.status_code == 409
    assert valida_envelope_de_erro(r)["code"] == "MUTATION_REFUSED"


# -- nós ----------------------------------------------------------------------------


def test_criar_no_aceita_posicao_e_devolve_o_no_declarado(plena, app):
    projeto = cria_projeto(plena, app)
    r = plena.post(
        f"/toc/projetos/{projeto['id']}/nos",
        json={"titulo": BOM, "descricao": "vem do relatório", "posicao": {"x": 12, "y": -3}},
    )
    corpo = valida_contra_o_contrato(app, r, "POST", "/toc/projetos/{projeto_id}/nos")
    assert corpo["posicao"] == {"x": 12.0, "y": -3.0}
    assert corpo["tipo"] == "generico"
    assert corpo["recolhido"] is False


def test_patch_de_no_aplica_titulo_posicao_e_recolhido_no_mesmo_pedido(plena, app):
    projeto = cria_projeto(plena, app)
    no = cria_no(plena, app, projeto["id"])
    r = plena.patch(
        f"/toc/projetos/{projeto['id']}/nos/{no['id']}",
        json={"titulo": OUTRO, "posicao": {"x": 5, "y": 6}, "recolhido": True},
    )
    corpo = valida_contra_o_contrato(
        app, r, "PATCH", "/toc/projetos/{projeto_id}/nos/{no_id}"
    )
    assert corpo["titulo"] == OUTRO
    assert corpo["posicao"] == {"x": 5.0, "y": 6.0}
    assert corpo["recolhido"] is True


def test_patch_de_no_sem_nenhum_campo_e_recusado(plena, app):
    projeto = cria_projeto(plena, app)
    no = cria_no(plena, app, projeto["id"])
    r = plena.patch(f"/toc/projetos/{projeto['id']}/nos/{no['id']}", json={})
    assert r.status_code == 422
    assert valida_envelope_de_erro(r)["code"] == "INVALID_ARGUMENT"


def test_excluir_no_declara_o_raio_das_arestas_removidas(plena, app):
    projeto = cria_projeto(plena, app)
    a = cria_no(plena, app, projeto["id"], BOM)
    b = cria_no(plena, app, projeto["id"], OUTRO)
    aresta = plena.post(
        f"/toc/projetos/{projeto['id']}/arestas",
        json={"origem_id": a["id"], "destino_id": b["id"]},
    ).json()

    r = plena.delete(f"/toc/projetos/{projeto['id']}/nos/{a['id']}")
    corpo = valida_contra_o_contrato(
        app, r, "DELETE", "/toc/projetos/{projeto_id}/nos/{no_id}"
    )
    assert corpo["arestas_removidas"] == [aresta["id"]]

    aberto = plena.get(f"/toc/projetos/{projeto['id']}").json()
    assert [n["id"] for n in aberto["nos"]] == [b["id"]], "sobrou o nó errado (defeito D-06)"


def test_no_inexistente_responde_404(plena, app):
    projeto = cria_projeto(plena, app)
    r = plena.patch(
        f"/toc/projetos/{projeto['id']}/nos/{uuid4()}", json={"titulo": OUTRO}
    )
    assert r.status_code == 404
    assert valida_envelope_de_erro(r)["code"] == "NOT_FOUND"


# -- arestas ------------------------------------------------------------------------


def test_ligar_devolve_201_e_a_aresta_declarada(plena, app):
    projeto = cria_projeto(plena, app)
    a = cria_no(plena, app, projeto["id"], BOM)
    b = cria_no(plena, app, projeto["id"], OUTRO)
    r = plena.post(
        f"/toc/projetos/{projeto['id']}/arestas",
        json={"origem_id": a["id"], "destino_id": b["id"], "rotulo": "leva a"},
    )
    corpo = valida_contra_o_contrato(app, r, "POST", "/toc/projetos/{projeto_id}/arestas")
    assert (corpo["origem_id"], corpo["destino_id"]) == (a["id"], b["id"])


@pytest.mark.parametrize(
    "regra, monta",
    [
        ("sem_auto_laco", lambda a, b: {"origem_id": a, "destino_id": a}),
        ("sem_duplicata", lambda a, b: {"origem_id": a, "destino_id": b}),
    ],
)
def test_aresta_invalida_diz_a_REGRA_violada_e_nao_so_que_falhou(plena, app, regra, monta):
    """RF-18: 'mensagem que diga a regra violada'. A regra vai em `details`, legível
    por máquina — o cliente discrimina por código e por dado, nunca por texto (§A.7)."""
    projeto = cria_projeto(plena, app)
    a = cria_no(plena, app, projeto["id"], BOM)
    b = cria_no(plena, app, projeto["id"], OUTRO)
    plena.post(
        f"/toc/projetos/{projeto['id']}/arestas",
        json={"origem_id": a["id"], "destino_id": b["id"]},
    )

    r = plena.post(f"/toc/projetos/{projeto['id']}/arestas", json=monta(a["id"], b["id"]))
    assert r.status_code == 409
    erro = valida_envelope_de_erro(r)
    assert erro["code"] == "INVALID_EDGE"
    assert erro["details"]["regra"] == regra


def test_aresta_com_ponta_fora_do_projeto_e_recusada_pela_regra_nomeada(plena, app):
    projeto = cria_projeto(plena, app)
    a = cria_no(plena, app, projeto["id"], BOM)
    r = plena.post(
        f"/toc/projetos/{projeto['id']}/arestas",
        json={"origem_id": a["id"], "destino_id": str(uuid4())},
    )
    assert r.status_code == 409
    assert valida_envelope_de_erro(r)["details"]["regra"] == "pontas_no_projeto"


def test_editar_e_excluir_aresta(plena, app):
    projeto = cria_projeto(plena, app)
    a = cria_no(plena, app, projeto["id"], BOM)
    b = cria_no(plena, app, projeto["id"], OUTRO)
    aresta = plena.post(
        f"/toc/projetos/{projeto['id']}/arestas",
        json={"origem_id": a["id"], "destino_id": b["id"]},
    ).json()

    r = plena.patch(
        f"/toc/projetos/{projeto['id']}/arestas/{aresta['id']}", json={"rotulo": "porque"}
    )
    corpo = valida_contra_o_contrato(
        app, r, "PATCH", "/toc/projetos/{projeto_id}/arestas/{aresta_id}"
    )
    assert corpo["rotulo"] == "porque"

    r = plena.delete(f"/toc/projetos/{projeto['id']}/arestas/{aresta['id']}")
    assert r.status_code == 204
    valida_contra_o_contrato(
        app, r, "DELETE", "/toc/projetos/{projeto_id}/arestas/{aresta_id}"
    )
    assert plena.get(f"/toc/projetos/{projeto['id']}").json()["arestas"] == []


# -- o que o domínio recusa chega como recusa tipada --------------------------------


def test_titulo_vazio_e_dado_invalido_nao_erro_interno(plena, app):
    projeto = cria_projeto(plena, app)
    r = plena.post(f"/toc/projetos/{projeto['id']}/nos", json={"titulo": "   "})
    assert r.status_code == 422
    assert valida_envelope_de_erro(r)["code"] == "INVALID_ARGUMENT"


def test_corpo_fora_do_esquema_tambem_usa_o_envelope_do_anexo_a(plena, app):
    """Erro do próprio framework não pode escapar do envelope: cliente único, forma única."""
    r = plena.post("/toc/projetos", json={"descricao_do_problema": "faltou o nome"})
    assert r.status_code == 422
    erro = valida_envelope_de_erro(r)
    assert erro["code"] == "INVALID_ARGUMENT"


def test_rota_inexistente_sob_o_prefixo_tambem_responde_no_envelope(plena):
    r = plena.get("/toc/nao-existe")
    assert r.status_code == 404
    assert valida_envelope_de_erro(r)["code"] == "NOT_FOUND"
