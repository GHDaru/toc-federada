"""A superfície HTTP do M6 medida contra o contrato que a própria aplicação declara.

Siglas, uma vez neste arquivo: **M6** — Focalização · **M1** — Núcleo de Diagramas
Lógicos · **TOC** — Teoria das Restrições · **ARA** — Árvore da Realidade Atual · **NC** —
Nuvem de Conflito · **APR** — Árvore de Pré-Requisitos · **HTTP** — *HyperText Transfer
Protocol* · **RF/RN/RNF** — requisito funcional / regra de negócio / requisito não
funcional · **DoD** — *Definition of Done* (Definição de Pronto).

`valida_contra_o_contrato` não confere o corpo contra o que o teste esperava, e sim contra
o esquema que o serviço publica no próprio OpenAPI — a diferença entre "a resposta tem os
campos que eu quis" e "a resposta é o que eu prometi ao cliente".

As personas são fictícias por regra (ADR 0006): Facilitadora TOC, Instituição Horizonte.
"""
from __future__ import annotations

from uuid import uuid4

import pytest

from .conftest import valida_contra_o_contrato

AUTORA = "Facilitadora TOC"
SISTEMA = "Da inscrição do candidato à primeira aula assistida"
RESTRICAO = "Capacidade de conferência da secretaria acadêmica"
JUSTIFICATIVA = "a fila de matrículas só cresce nesta etapa, em todo período de entrada"


def criar_analise(cliente, nome="Fluxo de matrículas") -> dict:
    resposta = cliente.post(
        "/toc/focalizacao/analises",
        json={"nome": nome, "sistema": SISTEMA, "descricao_do_sistema": "fluxo completo"},
    )
    assert resposta.status_code == 201, resposta.text
    return resposta.json()


def registrar_restricao(cliente, projeto_id, **extra) -> dict:
    corpo = {
        "descricao": RESTRICAO,
        "tipo": "fisica",
        "justificativa": JUSTIFICATIVA,
        "autor": AUTORA,
        **extra,
    }
    return cliente.post(f"/toc/focalizacao/analises/{projeto_id}/restricao", json=corpo)


def concluir(cliente, projeto_id, passo, decisao):
    return cliente.post(
        f"/toc/focalizacao/analises/{projeto_id}/passos/{passo}/conclusao",
        json={"decisao": decisao, "autor": AUTORA},
    )


def travessia(cliente, projeto_id) -> None:
    registrar_restricao(cliente, projeto_id)
    for passo, decisao in (
        ("identificar", "a restrição é a conferência da secretaria"),
        ("explorar", "priorizar matrículas com documentação completa"),
        ("subordinar", "nenhuma turma abre antes da conferência"),
        ("elevar", "contratar duas pessoas para a conferência"),
    ):
        assert concluir(cliente, projeto_id, passo, decisao).status_code == 200


# ---------------------------------------------------------------------------------------
# RF-01..RF-03 — criar, abrir, listar
# ---------------------------------------------------------------------------------------


def test_criar_analise_devolve_a_jornada_inteira_e_valida_contra_o_contrato(app, plena):
    resposta = plena.post(
        "/toc/focalizacao/analises",
        json={"nome": "Fluxo de matrículas", "sistema": SISTEMA},
    )

    assert resposta.status_code == 201
    valida_contra_o_contrato(app, resposta, "post", "/toc/focalizacao/analises")
    corpo = resposta.json()
    assert corpo["jornada"]["ordem"] == 1
    assert corpo["jornada"]["passo_atual"] == "identificar"
    assert [p["tipo"] for p in corpo["jornada"]["passos"]] == [
        "identificar",
        "explorar",
        "subordinar",
        "elevar",
        "recomecar",
    ]
    assert corpo["jornada"]["restricao"] is None
    assert corpo["jornada"]["somente_leitura"] is False
    assert len(corpo["linha_do_tempo"]) == 1


def test_a_listagem_traz_passo_atual_e_restricao_vigente(app, plena):
    primeira = criar_analise(plena)
    registrar_restricao(plena, primeira["projeto"]["id"])
    concluir(plena, primeira["projeto"]["id"], "identificar", "a restrição é a secretaria")
    criar_analise(plena, nome="Fluxo de estágio")

    resposta = plena.get("/toc/focalizacao/analises")

    assert resposta.status_code == 200
    valida_contra_o_contrato(app, resposta, "get", "/toc/focalizacao/analises")
    por_nome = {linha["nome"]: linha for linha in resposta.json()}
    assert por_nome["Fluxo de matrículas"]["passo_atual"] == "explorar"
    assert por_nome["Fluxo de matrículas"]["restricao"] == RESTRICAO
    assert por_nome["Fluxo de estágio"]["restricao"] is None


def test_analise_de_outro_inquilino_e_404(plena, outro_inquilino):
    analise = criar_analise(plena)
    resposta = outro_inquilino.get(
        f"/toc/focalizacao/analises/{analise['projeto']['id']}"
    )
    assert resposta.status_code == 404
    assert resposta.json()["error"]["code"] == "NOT_FOUND"


# ---------------------------------------------------------------------------------------
# RF-05..RF-08 — a restrição
# ---------------------------------------------------------------------------------------


def test_registrar_restricao_pela_borda(app, plena):
    analise = criar_analise(plena)
    resposta = registrar_restricao(plena, analise["projeto"]["id"])

    assert resposta.status_code == 201
    valida_contra_o_contrato(
        app, resposta, "post", "/toc/focalizacao/analises/{projeto_id}/restricao"
    )
    assert resposta.json()["tipo"] == "fisica"
    assert resposta.json()["autor"] == AUTORA
    assert resposta.json()["origem"] is None


def test_registrar_restricao_com_origem_guarda_a_referencia(plena):
    """RF-06/INT-02: a evidência que sustenta a conclusão viaja no dado, não no texto."""
    analise = criar_analise(plena)
    ara_id, no_id = str(uuid4()), str(uuid4())

    resposta = registrar_restricao(
        plena,
        analise["projeto"]["id"],
        origem={"ferramenta": "ara", "projeto_id": ara_id, "no_id": no_id},
    )

    assert resposta.status_code == 201
    assert resposta.json()["origem"] == {
        "ferramenta": "ara",
        "projeto_id": ara_id,
        "no_id": no_id,
    }


def test_a_segunda_restricao_do_ciclo_e_recusada_com_codigo_estavel(plena):
    """RN-03 pela borda, com o código do §A.7 — o cliente discrimina por código."""
    analise = criar_analise(plena)
    registrar_restricao(plena, analise["projeto"]["id"])

    resposta = registrar_restricao(plena, analise["projeto"]["id"], descricao="Outra coisa")

    assert resposta.status_code == 409
    assert resposta.json()["error"]["code"] == "INVALID_CONSTRAINT"
    assert resposta.json()["error"]["details"]["regra"] == "restricao_ja_registrada"


def test_editar_restricao_recusa_o_campo_tipo_na_borda(plena):
    """RN-03: trocar o alvo não é editar — e o esquema fechado recusa antes do domínio."""
    analise = criar_analise(plena)
    registrar_restricao(plena, analise["projeto"]["id"])

    resposta = plena.put(
        f"/toc/focalizacao/analises/{analise['projeto']['id']}/restricao",
        json={"descricao": "Outra descrição", "tipo": "politica"},
    )

    assert resposta.status_code == 422, resposta.text
    assert resposta.json()["error"]["code"] == "INVALID_ARGUMENT"


def test_concluir_identificar_sem_restricao_e_recusado_com_a_regra_nomeada(plena):
    """RF-08: a recusa é do domínio, e a borda a traduz sem perder o nome da regra."""
    analise = criar_analise(plena)

    resposta = concluir(plena, analise["projeto"]["id"], "identificar", "seguimos assim")

    assert resposta.status_code == 409
    assert resposta.json()["error"]["code"] == "INVALID_FOCUSING_STEP"
    assert resposta.json()["error"]["details"]["regra"] == "sem_restricao"


def test_passo_desconhecido_e_422_com_a_lista_do_que_era_esperado(plena):
    analise = criar_analise(plena)
    resposta = concluir(plena, analise["projeto"]["id"], "medir", "qualquer coisa")
    assert resposta.status_code == 422
    assert "identificar" in resposta.json()["error"]["message"]


# ---------------------------------------------------------------------------------------
# RF-09..RF-11 — a jornada pela borda
# ---------------------------------------------------------------------------------------


def test_a_travessia_dos_cinco_passos_pela_borda(app, plena):
    """O portão do roadmap visto pelo HTTP: cada passo herda o produto do anterior."""
    analise = criar_analise(plena)
    projeto_id = analise["projeto"]["id"]
    registrar_restricao(plena, projeto_id)

    concluir(plena, projeto_id, "identificar", "a restrição é a secretaria")
    resposta_da_jornada = plena.get(f"/toc/focalizacao/analises/{projeto_id}/jornada")
    depois = resposta_da_jornada.json()
    valida_contra_o_contrato(
        app, resposta_da_jornada, "get", "/toc/focalizacao/analises/{projeto_id}/jornada"
    )
    explorar = next(p for p in depois["passos"] if p["tipo"] == "explorar")
    assert any(RESTRICAO in linha for linha in explorar["herdado"])

    concluir(plena, projeto_id, "explorar", "priorizar documentação completa")
    concluir(plena, projeto_id, "subordinar", "nenhuma turma abre antes")
    resposta = concluir(plena, projeto_id, "elevar", "contratar duas pessoas")

    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["passo_atual"] == "recomecar"
    assert corpo["passos_concluidos"] == 4
    elevar = next(p for p in corpo["passos"] if p["tipo"] == "elevar")
    assert len(elevar["herdado"]) == 4


def test_anotar_nao_avanca_a_jornada(plena):
    analise = criar_analise(plena)
    projeto_id = analise["projeto"]["id"]

    resposta = plena.post(
        f"/toc/focalizacao/analises/{projeto_id}/passos/identificar/notas",
        json={"texto": "a fila cresce todo período", "autor": AUTORA},
    )

    assert resposta.status_code == 201
    assert resposta.json()["passo_atual"] == "identificar"
    identificar = next(p for p in resposta.json()["passos"] if p["tipo"] == "identificar")
    assert [n["texto"] for n in identificar["notas"]] == ["a fila cresce todo período"]


def test_reabrir_nao_apaga_a_decisao_anterior(plena):
    """RF-10 + RN-04: o histórico de decisões é somente-acréscimo, e a resposta mostra."""
    analise = criar_analise(plena)
    projeto_id = analise["projeto"]["id"]
    registrar_restricao(plena, projeto_id)
    concluir(plena, projeto_id, "identificar", "primeira leitura")

    resposta = plena.post(
        f"/toc/focalizacao/analises/{projeto_id}/reaberturas",
        json={"justificativa": "a medição da fila mudou", "autor": AUTORA},
    )

    assert resposta.status_code == 200
    identificar = next(p for p in resposta.json()["passos"] if p["tipo"] == "identificar")
    assert identificar["estado"] == "em_andamento"
    assert [d["texto"] for d in identificar["decisoes"]] == ["primeira leitura"]
    assert len(identificar["reaberturas"]) == 1


def test_nao_existe_rota_que_crie_exclua_ou_reordene_passo(app):
    """RN-01 medida na SUPERFÍCIE: a ausência da rota é a garantia mais barata.

    Este teste conta as rotas publicadas do módulo e exige que nenhuma delas ofereça criar,
    excluir ou reordenar passo. Um `POST /passos` que alguém acrescentasse por engano
    apareceria aqui antes de aparecer em produção.
    """
    caminhos = {
        p: set(m.upper() for m in metodos)
        for p, metodos in app.openapi()["paths"].items()
        if p.startswith("/toc/focalizacao")
    }
    print(f"rotas do M6 publicadas: {len(caminhos)}")
    assert caminhos, "o módulo não publicou rota nenhuma"

    proibidas = [
        p
        for p, metodos in caminhos.items()
        if p.endswith("/passos") or p.endswith("/passos/ordem")
    ]
    assert proibidas == [], f"rota que mexeria na ordem canônica dos passos: {proibidas}"
    # A única rota `DELETE` sobre passo é a de vínculo — não a do passo em si.
    deletes = [p for p, metodos in caminhos.items() if "DELETE" in metodos]
    assert all(p.endswith("/{vinculo_id}") or p.endswith("/{projeto_id}") for p in deletes), (
        f"DELETE inesperado no módulo: {deletes}"
    )


# ---------------------------------------------------------------------------------------
# RF-14 / RNF-04 — os vínculos, validados no servidor
# ---------------------------------------------------------------------------------------


def test_vincular_ara_do_passo_identificar(app, plena):
    analise = criar_analise(plena)
    ara = plena.post("/toc/ara/projetos", json={"nome": "ARA do fluxo"}).json()

    resposta = plena.post(
        f"/toc/focalizacao/analises/{analise['projeto']['id']}/passos/identificar/vinculos",
        json={"ferramenta": "ara", "projeto_id": ara["id"], "papel": "causa raiz"},
    )

    assert resposta.status_code == 201, resposta.text
    valida_contra_o_contrato(
        app,
        resposta,
        "post",
        "/toc/focalizacao/analises/{projeto_id}/passos/{passo}/vinculos",
    )
    assert resposta.json()["canonico"] is True
    assert resposta.json()["estado"] == "ativo"
    assert resposta.json()["nome"] == "ARA do fluxo"


def test_vinculo_para_projeto_inexistente_e_recusado_no_servidor(plena):
    """RNF-04: a existência é conferida no servidor, e a recusa tem regra nomeada."""
    analise = criar_analise(plena)

    resposta = plena.post(
        f"/toc/focalizacao/analises/{analise['projeto']['id']}/passos/identificar/vinculos",
        json={"ferramenta": "ara", "projeto_id": str(uuid4())},
    )

    assert resposta.status_code == 409
    assert resposta.json()["error"]["code"] == "INVALID_TOOL_LINK"
    assert resposta.json()["error"]["details"]["regra"] == "alvo_inexistente"


def test_vinculo_para_projeto_de_outro_inquilino_e_indistinguivel_de_inexistente(
    plena, outro_inquilino
):
    analise = criar_analise(plena)
    alheia = outro_inquilino.post("/toc/ara/projetos", json={"nome": "ARA alheia"}).json()

    resposta = plena.post(
        f"/toc/focalizacao/analises/{analise['projeto']['id']}/passos/identificar/vinculos",
        json={"ferramenta": "ara", "projeto_id": alheia["id"]},
    )

    assert resposta.status_code == 409
    assert resposta.json()["error"]["details"]["regra"] == "alvo_inexistente"


def test_vinculo_fora_do_canonico_exige_justificativa_e_sai_com_aviso(plena):
    """RN-06: o método educa, o dado obedece ao grupo — aviso, nunca bloqueio."""
    analise = criar_analise(plena)
    projeto_id = analise["projeto"]["id"]
    apr = plena.post(
        "/toc/apr/projetos",
        json={"nome": "APR do plano", "objetivo": "Ampliar a secretaria acadêmica"},
    ).json()

    sem_motivo = plena.post(
        f"/toc/focalizacao/analises/{projeto_id}/passos/identificar/vinculos",
        json={"ferramenta": "apr", "projeto_id": apr["id"]},
    )
    assert sem_motivo.status_code == 409
    assert sem_motivo.json()["error"]["details"]["regra"] == "justificativa_obrigatoria"

    com_motivo = plena.post(
        f"/toc/focalizacao/analises/{projeto_id}/passos/identificar/vinculos",
        json={
            "ferramenta": "apr",
            "projeto_id": apr["id"],
            "justificativa": "o plano de pré-requisitos já existia quando a análise começou",
        },
    )
    assert com_motivo.status_code == 201
    assert com_motivo.json()["canonico"] is False

    jornada = plena.get(f"/toc/focalizacao/analises/{projeto_id}/jornada").json()
    identificar = next(p for p in jornada["passos"] if p["tipo"] == "identificar")
    assert len(identificar["avisos"]) == 1
    assert all(x["regra"] != "vinculo_nao_canonico" for x in identificar["pendencias"])


def test_alvo_arquivado_depois_degrada_para_referencia_legivel(plena):
    """RNF-04: nunca erro opaco, nunca dado órfão silencioso."""
    analise = criar_analise(plena)
    projeto_id = analise["projeto"]["id"]
    ara = plena.post("/toc/ara/projetos", json={"nome": "ARA do fluxo"}).json()
    plena.post(
        f"/toc/focalizacao/analises/{projeto_id}/passos/identificar/vinculos",
        json={"ferramenta": "ara", "projeto_id": ara["id"]},
    )

    plena.delete(f"/toc/projetos/{ara['id']}")

    jornada = plena.get(f"/toc/focalizacao/analises/{projeto_id}/jornada").json()
    identificar = next(p for p in jornada["passos"] if p["tipo"] == "identificar")
    (vinculo,) = identificar["vinculos"]
    assert vinculo["estado"] == "arquivado"
    assert "arquivado" in vinculo["legenda"]


def test_a_navegacao_de_volta_resolve_por_consulta_ao_m6(app, plena):
    """L-03: nenhum campo novo na ARA — quem responde "quem me cita?" é o M6."""
    analise = criar_analise(plena)
    ara = plena.post("/toc/ara/projetos", json={"nome": "ARA do fluxo"}).json()
    plena.post(
        f"/toc/focalizacao/analises/{analise['projeto']['id']}/passos/identificar/vinculos",
        json={"ferramenta": "ara", "projeto_id": ara["id"]},
    )

    resposta = plena.get(f"/toc/focalizacao/ferramentas/{ara['id']}/analises")

    assert resposta.status_code == 200
    valida_contra_o_contrato(
        app, resposta, "get", "/toc/focalizacao/ferramentas/{alvo_id}/analises"
    )
    (achado,) = resposta.json()
    assert achado["analise_nome"] == "Fluxo de matrículas"
    assert achado["passo"] == "identificar"


# ---------------------------------------------------------------------------------------
# RF-15/RF-16 — recomeço e anti-inércia pela borda
# ---------------------------------------------------------------------------------------


def test_recomecar_fecha_o_ciclo_e_herda_o_que_pode_virar_inercia(app, plena):
    analise = criar_analise(plena)
    projeto_id = analise["projeto"]["id"]
    travessia(plena, projeto_id)

    resposta = plena.post(f"/toc/focalizacao/analises/{projeto_id}/recomecos")

    assert resposta.status_code == 201, resposta.text
    valida_contra_o_contrato(
        app, resposta, "post", "/toc/focalizacao/analises/{projeto_id}/recomecos"
    )
    corpo = resposta.json()
    assert corpo["jornada"]["ordem"] == 2
    assert corpo["jornada"]["restricao"] is None
    assert corpo["jornada"]["herancas_pendentes"] == 2
    assert [c["estado"] for c in corpo["linha_do_tempo"]] == ["fechado", "aberto"]
    assert corpo["linha_do_tempo"][0]["restricao"] == RESTRICAO


def test_recomecar_fora_do_quinto_passo_e_recusado(plena):
    analise = criar_analise(plena)
    projeto_id = analise["projeto"]["id"]
    registrar_restricao(plena, projeto_id)

    resposta = plena.post(f"/toc/focalizacao/analises/{projeto_id}/recomecos")

    assert resposta.status_code == 409
    assert resposta.json()["error"]["code"] == "INVALID_CYCLE"
    assert resposta.json()["error"]["details"]["regra"] == "recomeco_fora_do_passo"


def test_subordinar_do_novo_ciclo_nao_conclui_com_veredito_pendente(plena):
    """RN-05 pela borda: a inércia não atravessa o recomeço."""
    analise = criar_analise(plena)
    projeto_id = analise["projeto"]["id"]
    travessia(plena, projeto_id)
    plena.post(f"/toc/focalizacao/analises/{projeto_id}/recomecos")
    registrar_restricao(plena, projeto_id, descricao="Capacidade do laboratório")
    concluir(plena, projeto_id, "identificar", "a restrição mudou de lugar")
    concluir(plena, projeto_id, "explorar", "explorar de novo")

    bloqueado = concluir(plena, projeto_id, "subordinar", "mantemos tudo")

    assert bloqueado.status_code == 409
    assert bloqueado.json()["error"]["code"] == "INVALID_FOCUSING_STEP"
    assert bloqueado.json()["error"]["details"]["regra"] == "heranca_pendente"


def test_julgar_a_heranca_desbloqueia_subordinar(plena):
    analise = criar_analise(plena)
    projeto_id = analise["projeto"]["id"]
    travessia(plena, projeto_id)
    recomecada = plena.post(f"/toc/focalizacao/analises/{projeto_id}/recomecos").json()
    registrar_restricao(plena, projeto_id, descricao="Capacidade do laboratório")
    concluir(plena, projeto_id, "identificar", "a restrição mudou de lugar")
    concluir(plena, projeto_id, "explorar", "explorar de novo")

    for herdada in recomecada["jornada"]["heranca"]:
        resposta = plena.post(
            f"/toc/focalizacao/analises/{projeto_id}/heranca/{herdada['id']}/veredito",
            json={
                "veredito": "revogada",
                "justificativa": "a restrição migrou de etapa",
                "autor": AUTORA,
            },
        )
        assert resposta.status_code == 200, resposta.text

    assert concluir(plena, projeto_id, "subordinar", "subordinar ao laboratório").status_code == 200


def test_veredito_pendente_e_recusado_na_borda(plena):
    """Voltar a `pendente` apagaria um julgamento — o `Literal` do esquema não aceita."""
    analise = criar_analise(plena)
    projeto_id = analise["projeto"]["id"]
    travessia(plena, projeto_id)
    recomecada = plena.post(f"/toc/focalizacao/analises/{projeto_id}/recomecos").json()
    herdada = recomecada["jornada"]["heranca"][0]

    resposta = plena.post(
        f"/toc/focalizacao/analises/{projeto_id}/heranca/{herdada['id']}/veredito",
        json={"veredito": "pendente", "justificativa": "deixa pensar", "autor": AUTORA},
    )

    assert resposta.status_code == 422
    assert resposta.json()["error"]["code"] == "INVALID_ARGUMENT"


def test_manter_sem_justificativa_e_recusado(plena):
    analise = criar_analise(plena)
    projeto_id = analise["projeto"]["id"]
    travessia(plena, projeto_id)
    recomecada = plena.post(f"/toc/focalizacao/analises/{projeto_id}/recomecos").json()
    herdada = recomecada["jornada"]["heranca"][0]

    resposta = plena.post(
        f"/toc/focalizacao/analises/{projeto_id}/heranca/{herdada['id']}/veredito",
        json={"veredito": "mantida", "justificativa": "", "autor": AUTORA},
    )

    assert resposta.status_code == 422


def test_o_ciclo_fechado_abre_somente_leitura(app, plena):
    """RF-17/RI-04: o servidor DIZ que é somente leitura — não é um `if` na tela."""
    analise = criar_analise(plena)
    projeto_id = analise["projeto"]["id"]
    travessia(plena, projeto_id)
    recomecada = plena.post(f"/toc/focalizacao/analises/{projeto_id}/recomecos").json()
    fechado = recomecada["linha_do_tempo"][0]["ciclo_id"]

    resposta = plena.get(
        f"/toc/focalizacao/analises/{projeto_id}/jornada", params={"ciclo_id": fechado}
    )

    assert resposta.status_code == 200
    assert resposta.json()["somente_leitura"] is True
    assert resposta.json()["ordem"] == 1
    assert resposta.json()["restricao"]["descricao"] == RESTRICAO


# ---------------------------------------------------------------------------------------
# RF-19/RF-20 — a sugestão NÃO aplica, e a jornada funciona sem ela
# ---------------------------------------------------------------------------------------


def test_sugerir_restricao_devolve_candidatas_e_o_action_id_sem_escrever_nada(app, plena):
    analise = criar_analise(plena)
    projeto_id = analise["projeto"]["id"]
    ara = plena.post("/toc/ara/projetos", json={"nome": "ARA do fluxo"}).json()
    ara_id = ara["id"]
    causa = plena.post(
        f"/toc/ara/projetos/{ara_id}/efeitos",
        json={"titulo": "A secretaria confere documentos um a um."},
    ).json()
    efeito = plena.post(
        f"/toc/ara/projetos/{ara_id}/efeitos",
        json={"titulo": "A fila de matrículas passa de 200 pedidos em março."},
    ).json()
    plena.post(f"/toc/ara/projetos/{ara_id}/nos/{efeito['id']}/ude", json={})
    plena.post(
        f"/toc/ara/projetos/{ara_id}/arestas",
        json={"origem_id": causa["id"], "destino_id": efeito["id"]},
    )
    plena.post(
        f"/toc/focalizacao/analises/{projeto_id}/passos/identificar/vinculos",
        json={"ferramenta": "ara", "projeto_id": ara_id},
    )

    antes = plena.get(f"/toc/focalizacao/analises/{projeto_id}").json()
    resposta = plena.post(
        f"/toc/focalizacao/analises/{projeto_id}/sugestoes-de-restricao"
    )

    assert resposta.status_code == 200, resposta.text
    valida_contra_o_contrato(
        app,
        resposta,
        "post",
        "/toc/focalizacao/analises/{projeto_id}/sugestoes-de-restricao",
    )
    corpo = resposta.json()
    assert corpo["action_id"] == "toc.suggest_constraint"
    assert corpo["ara_projeto_id"] == ara_id
    assert [c["no_id"] for c in corpo["candidatas"]] == [causa["id"]]
    assert "Efeito(s) Indesejável(is)" in corpo["candidatas"][0]["racional"]

    # DoD 9 (metade da prova): SUGERIR não escreve. A análise volta idêntica.
    depois = plena.get(f"/toc/focalizacao/analises/{projeto_id}").json()
    assert depois["jornada"] == antes["jornada"]


def test_sem_ara_vinculada_a_sugestao_volta_vazia_e_a_jornada_segue(plena):
    """RF-20: a jornada guiada é completa por construção — a sugestão é aceleradora."""
    analise = criar_analise(plena)
    projeto_id = analise["projeto"]["id"]

    resposta = plena.post(f"/toc/focalizacao/analises/{projeto_id}/sugestoes-de-restricao")

    assert resposta.status_code == 200
    assert resposta.json()["candidatas"] == []
    assert registrar_restricao(plena, projeto_id).status_code == 201


# ---------------------------------------------------------------------------------------
# Autorização — fail-closed nas rotas novas
# ---------------------------------------------------------------------------------------


def test_quem_so_le_nao_muta_a_jornada(plena, leitora):
    analise = criar_analise(plena)
    projeto_id = analise["projeto"]["id"]

    mutacoes = [
        plena and leitora.post(
            "/toc/focalizacao/analises", json={"nome": "x", "sistema": "y"}
        ),
        leitora.post(
            f"/toc/focalizacao/analises/{projeto_id}/restricao",
            json={
                "descricao": RESTRICAO,
                "tipo": "fisica",
                "justificativa": JUSTIFICATIVA,
                "autor": AUTORA,
            },
        ),
        leitora.post(
            f"/toc/focalizacao/analises/{projeto_id}/passos/identificar/conclusao",
            json={"decisao": "x", "autor": AUTORA},
        ),
        leitora.post(
            f"/toc/focalizacao/analises/{projeto_id}/passos/identificar/notas",
            json={"texto": "x", "autor": AUTORA},
        ),
        leitora.post(f"/toc/focalizacao/analises/{projeto_id}/recomecos"),
        leitora.post(f"/toc/focalizacao/analises/{projeto_id}/sugestoes-de-restricao"),
        leitora.delete(f"/toc/focalizacao/analises/{projeto_id}"),
    ]
    print(f"mutações do M6 recusadas para quem só lê: {len(mutacoes)}")
    for resposta in mutacoes:
        assert resposta.status_code == 403, resposta.text
        assert resposta.json()["error"]["code"] == "UNAUTHORIZED"

    # E as leituras continuam abertas para ela.
    assert leitora.get(f"/toc/focalizacao/analises/{projeto_id}").status_code == 200
    assert leitora.get("/toc/focalizacao/analises").status_code == 200


def test_sem_token_nenhuma_rota_do_m6_responde(app):
    from fastapi.testclient import TestClient

    anonima = TestClient(app)
    assert anonima.get("/toc/focalizacao/analises").status_code == 401
    assert anonima.post(
        "/toc/focalizacao/analises", json={"nome": "x", "sistema": "y"}
    ).status_code == 401


# ---------------------------------------------------------------------------------------
# A trava otimista pela borda (§A.7 — VERSION_CONFLICT)
# ---------------------------------------------------------------------------------------


@pytest.mark.parametrize("com_restricao", [True])
def test_exclusao_suave_e_restauracao_preservam_a_jornada(plena, com_restricao):
    """RF-04/US-02: volta com ciclos, passos, restrições e vínculos intactos."""
    analise = criar_analise(plena)
    projeto_id = analise["projeto"]["id"]
    registrar_restricao(plena, projeto_id)
    antes = plena.get(f"/toc/focalizacao/analises/{projeto_id}/jornada").json()

    excluida = plena.delete(f"/toc/focalizacao/analises/{projeto_id}")
    assert excluida.status_code == 200
    assert excluida.json()["projeto"]["estado"] == "excluido"

    restaurada = plena.post(f"/toc/focalizacao/analises/{projeto_id}/restauracao")
    assert restaurada.status_code == 200
    assert restaurada.json()["jornada"] == antes
