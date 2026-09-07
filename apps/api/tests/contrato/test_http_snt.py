"""A superfície HTTP do M5 — a árvore de Estratégia & Táticas sob `/toc/snt` (spec 010).

Siglas, uma vez neste arquivo: **M5** — Estratégia & Táticas · **S&T** — Estratégia &
Táticas (*Strategy & Tactics*) · **M1** — Núcleo de Diagramas Lógicos · **HTTP** —
*HyperText Transfer Protocol* · **RF/RN/RI** — requisito funcional / regra de negócio /
requisito de interface da spec 010 · **APH** — Aplicação ↔ Harness.

Cada corpo é validado contra o **OpenAPI que a própria aplicação declara** — a diferença
entre "a resposta tem os campos que eu quis" e "a resposta é o que eu prometi ao cliente".

Cinco provas que só a borda dá:

1. **Nenhuma rota de escrita aceita número de passo** (RF-06, DoD 4) — medido no OpenAPI
   publicado, esquema a esquema, e não afirmado em prosa. O contraexemplo é o formulário
   da quarta geração, onde o número era campo obrigatório digitado à mão
   (`tocbuilderv3/components/SnTStepEditorModal.tsx:56-57`).
2. **A rota genérica do M1 recusa mexer no grafo de uma S&T** — a porta dos fundos do
   agregado continua fechada para a ferramenta que nasce agora.
3. **A confirmação de exclusão sabe a contagem antes** (RF-09): a rota de prévia responde
   quantos passos caem, sem apagar nada.
4. **A prévia da renumeração é leitura** (RI-05): uma observadora só-leitura a alcança, e
   a árvore não muda.
5. **O autor da mudança de status vem do token**, nunca do corpo do pedido (RN-03).
"""
from __future__ import annotations

from uuid import uuid4

from .conftest import valida_contra_o_contrato, valida_envelope_de_erro

META = "Dobrar a capacidade de atendimento da Instituição Horizonte em doze meses"


def arvore_sintetica(plena, app):
    """A S&T de três níveis da Instituição Horizonte, montada pelas rotas."""
    r = plena.post(
        "/toc/snt/projetos",
        json={"nome": "Dobrar a capacidade de atendimento", "meta_global": META},
    )
    assert r.status_code == 201, r.text
    valida_contra_o_contrato(app, r, "post", "/toc/snt/projetos")
    projeto = r.json()["id"]

    def passo(estrategia: str, tatica: str = "", pai: str | None = None) -> str:
        resposta = plena.post(
            f"/toc/snt/projetos/{projeto}/passos",
            json={"estrategia": estrategia, "tatica": tatica, "pai_id": pai},
        )
        assert resposta.status_code == 201, resposta.text
        return resposta.json()["id"]

    um = passo("Atender o dobro de pessoas com a estrutura atual", "Três frentes por trimestre")
    um_um = passo("Reduzir o tempo de espera pela metade", "Medir a fila semanalmente", um)
    um_um_um = passo("Enxergar a fila em tempo real", "Publicar um painel de fila", um_um)
    um_um_dois = passo("Eliminar a espera por conferência", "Conferir na entrada", um_um)
    um_dois = passo("Formar a equipe necessária", "Duas turmas por semestre", um)
    return projeto, {
        "1": um, "1.1": um_um, "1.1.1": um_um_um, "1.1.2": um_um_dois, "1.2": um_dois,
    }


# ---------------------------------------------------------------------------------------
# RF-01..RF-05 · criar, abrir, decompor
# ---------------------------------------------------------------------------------------


def test_criar_a_arvore_exige_meta_global_e_devolve_a_arvore_vazia(plena, app) -> None:
    r = plena.post("/toc/snt/projetos", json={"nome": "Plano", "meta_global": META})
    corpo = valida_contra_o_contrato(app, r, "post", "/toc/snt/projetos")
    print(f"{r.status_code} · meta={corpo['meta_global'][:40]}… · passos={len(corpo['passos'])}")
    assert r.status_code == 201
    assert corpo["ferramenta"] == "snt"
    assert corpo["passos"] == []

    ruim = plena.post("/toc/snt/projetos", json={"nome": "Plano", "meta_global": "   "})
    print(f"sem meta global: {ruim.status_code} · {ruim.json()['error']['code']}")
    assert ruim.status_code == 422
    valida_envelope_de_erro(ruim)


def test_a_arvore_volta_numerada_e_com_a_leitura_dirigida_das_premissas(plena, app) -> None:
    projeto, chaves = arvore_sintetica(plena, app)
    r = plena.get(f"/toc/snt/projetos/{projeto}")
    corpo = valida_contra_o_contrato(app, r, "get", "/toc/snt/projetos/{projeto_id}")
    numeros = {p["numero"] for p in corpo["passos"]}
    print(f"{r.status_code} · números={sorted(numeros)}")
    assert numeros == {"1", "1.1", "1.1.1", "1.1.2", "1.2"}

    ficha = plena.get(f"/toc/snt/projetos/{projeto}/passos/{chaves['1.1']}")
    detalhe = valida_contra_o_contrato(
        app, ficha, "get", "/toc/snt/projetos/{projeto_id}/passos/{no_id}"
    )
    papeis = [leitura["papel"] for leitura in detalhe["leituras"]]
    print(f"leituras={papeis}")
    assert papeis == ["paralela", "necessidade_ao_pai", "suficiencia_dos_filhos"]
    assert detalhe["numero"] == "1.1"


def test_nenhuma_rota_de_escrita_do_m5_declara_campo_de_numero(app) -> None:
    """RF-06/DoD 4: numeração é saída, nunca entrada — medido no OpenAPI publicado."""
    documento = app.openapi()
    rotas = [caminho for caminho in documento["paths"] if caminho.startswith("/toc/snt")]
    esquemas_de_entrada = []
    for caminho in rotas:
        for metodo, operacao in documento["paths"][caminho].items():
            if metodo.lower() not in {"post", "put", "patch"}:
                continue
            corpo = operacao.get("requestBody")
            if corpo:
                referencia = corpo["content"]["application/json"]["schema"]["$ref"]
                esquemas_de_entrada.append(referencia.rsplit("/", 1)[-1])
    proibidos = []
    for nome in esquemas_de_entrada:
        for campo in documento["components"]["schemas"][nome].get("properties", {}):
            if "numero" in campo.lower() or "step" in campo.lower():
                proibidos.append(f"{nome}.{campo}")
    print(
        f"rotas do M5 examinadas: {len(rotas)} · esquemas de entrada: "
        f"{len(esquemas_de_entrada)} · campos de número encontrados: {len(proibidos)}"
    )
    assert rotas, "a superfície do M5 não existe no OpenAPI"
    assert proibidos == []


def test_adicionar_passo_em_posicao_renumera_os_irmaos(plena, app) -> None:
    projeto, chaves = arvore_sintetica(plena, app)
    r = plena.post(
        f"/toc/snt/projetos/{projeto}/passos",
        json={"estrategia": "Mapear o fluxo ponta a ponta", "pai_id": chaves["1"], "posicao": 0},
    )
    novo = valida_contra_o_contrato(app, r, "post", "/toc/snt/projetos/{projeto_id}/passos")
    arvore = plena.get(f"/toc/snt/projetos/{projeto}").json()
    por_id = {p["id"]: p["numero"] for p in arvore["passos"]}
    print(f"novo={novo['numero']} · 1.1 virou {por_id[chaves['1.1']]}")
    assert novo["numero"] == "1.1"
    assert por_id[chaves["1.1"]] == "1.2"
    assert por_id[chaves["1.1.2"]] == "1.2.2"


# ---------------------------------------------------------------------------------------
# RF-08 / RI-05 · mover, com pré-visualização da renumeração
# ---------------------------------------------------------------------------------------


def test_a_previa_da_renumeracao_e_leitura_e_nao_muda_a_arvore(plena, leitora, app) -> None:
    projeto, chaves = arvore_sintetica(plena, app)
    antes = plena.get(f"/toc/snt/projetos/{projeto}").json()

    r = leitora.post(
        f"/toc/snt/projetos/{projeto}/previas-de-mover",
        json={"no_id": chaves["1.1"], "novo_pai_id": None},
    )
    corpo = valida_contra_o_contrato(
        app, r, "post", "/toc/snt/projetos/{projeto_id}/previas-de-mover"
    )
    depois = plena.get(f"/toc/snt/projetos/{projeto}").json()
    mudancas = {m["no_id"]: (m["numero_atual"], m["numero_novo"]) for m in corpo["mudancas"]}
    print(f"{r.status_code} · mudanças previstas={len(mudancas)} · árvore intacta={antes == depois}")
    assert r.status_code == 200
    assert mudancas[chaves["1.1"]] == ("1.1", "2")
    assert antes == depois


def test_mover_leva_a_subarvore_e_renumera_os_dois_lados(plena, app) -> None:
    projeto, chaves = arvore_sintetica(plena, app)
    r = plena.put(
        f"/toc/snt/projetos/{projeto}/passos/{chaves['1.1']}/posicao",
        json={"novo_pai_id": None, "posicao": 0},
    )
    corpo = valida_contra_o_contrato(
        app, r, "put", "/toc/snt/projetos/{projeto_id}/passos/{no_id}/posicao"
    )
    por_id = {p["id"]: p["numero"] for p in corpo["passos"]}
    print(f"1.1 → {por_id[chaves['1.1']]} · filhos {por_id[chaves['1.1.1']]} · antigo 1 → {por_id[chaves['1']]}")
    assert por_id[chaves["1.1"]] == "1"
    assert por_id[chaves["1.1.1"]] == "1.1"
    assert por_id[chaves["1"]] == "2"


def test_mover_para_a_propria_subarvore_devolve_codigo_estavel(plena, app) -> None:
    """RN-04: o cliente discrimina por código, nunca por mensagem (§A.7 do Anexo A)."""
    projeto, chaves = arvore_sintetica(plena, app)
    r = plena.put(
        f"/toc/snt/projetos/{projeto}/passos/{chaves['1']}/posicao",
        json={"novo_pai_id": chaves["1.1.1"]},
    )
    corpo = r.json()
    print(f"{r.status_code} · code={corpo['error']['code']}")
    assert r.status_code == 409
    valida_envelope_de_erro(r)


# ---------------------------------------------------------------------------------------
# RF-09 · a exclusão que avisa a contagem — e não toca no resto
# ---------------------------------------------------------------------------------------


def test_a_previa_da_exclusao_diz_quantos_passos_caem_sem_apagar_nada(plena, app) -> None:
    projeto, chaves = arvore_sintetica(plena, app)
    r = plena.get(f"/toc/snt/projetos/{projeto}/passos/{chaves['1.1']}/previa-de-exclusao")
    corpo = valida_contra_o_contrato(
        app, r, "get", "/toc/snt/projetos/{projeto_id}/passos/{no_id}/previa-de-exclusao"
    )
    depois = plena.get(f"/toc/snt/projetos/{projeto}").json()
    print(f"{r.status_code} · passos que caem={corpo['passos']} · árvore ainda tem {len(depois['passos'])}")
    assert corpo["passos"] == 3
    assert [p["numero"] for p in corpo["primeiro_nivel"]] == ["1.1.1", "1.1.2"]
    assert len(depois["passos"]) == 5


def test_excluir_a_subarvore_nao_toca_nos_demais_passos(plena, app) -> None:
    """O contraexemplo é `tocbuilderv3/services/mockApiService.ts:521`."""
    projeto, chaves = arvore_sintetica(plena, app)
    antes = {p["id"]: p for p in plena.get(f"/toc/snt/projetos/{projeto}").json()["passos"]}
    r = plena.delete(f"/toc/snt/projetos/{projeto}/passos/{chaves['1.1']}")
    corpo = valida_contra_o_contrato(
        app, r, "delete", "/toc/snt/projetos/{projeto_id}/passos/{no_id}"
    )
    depois = {p["id"]: p for p in corpo["passos"]}
    print(f"{r.status_code} · antes={len(antes)} depois={len(depois)}")
    assert set(depois) == set(antes) - {chaves["1.1"], chaves["1.1.1"], chaves["1.1.2"]}
    assert depois[chaves["1.2"]]["numero"] == "1.1"
    assert depois[chaves["1"]]["estrategia"] == antes[chaves["1"]]["estrategia"]


# ---------------------------------------------------------------------------------------
# RF-12 / RN-03 · premissas e status
# ---------------------------------------------------------------------------------------


def test_as_tres_premissas_gravam_e_a_leitura_dirigida_as_incorpora(plena, app) -> None:
    projeto, chaves = arvore_sintetica(plena, app)
    r = plena.put(
        f"/toc/snt/projetos/{projeto}/passos/{chaves['1.1']}/premissas",
        json={
            "paralela": "a fila é hoje o gargalo",
            "necessidade_ao_pai": "sem cortar a espera, a fila dobra junto",
            "suficiencia_dos_filhos": "as duas etapas respondem por 80% da espera",
        },
    )
    corpo = valida_contra_o_contrato(
        app, r, "put", "/toc/snt/projetos/{projeto_id}/passos/{no_id}/premissas"
    )
    leituras = {leitura["papel"]: leitura for leitura in corpo["leituras"]}
    print(f"{r.status_code} · necessidade completa={leituras['necessidade_ao_pai']['completa']}")
    assert all(leitura["completa"] for leitura in leituras.values())
    assert "sem cortar a espera" in leituras["necessidade_ao_pai"]["texto"]


def test_o_status_muda_com_autor_vindo_do_token_e_o_corpo_nao_o_aceita(plena, app) -> None:
    projeto, chaves = arvore_sintetica(plena, app)
    documento = app.openapi()
    esquema = documento["components"]["schemas"]["StatusDoPassoSnTIn"]["properties"]
    r = plena.put(
        f"/toc/snt/projetos/{projeto}/passos/{chaves['1.1']}/status",
        json={"status": "validado"},
    )
    corpo = valida_contra_o_contrato(
        app, r, "put", "/toc/snt/projetos/{projeto_id}/passos/{no_id}/status"
    )
    print(f"{r.status_code} · status={corpo['status']} · campos do corpo={sorted(esquema)}")
    assert corpo["status"] == "validado"
    assert "autor" not in esquema


def test_status_fora_do_vocabulario_e_recusado_na_borda(plena, app) -> None:
    projeto, chaves = arvore_sintetica(plena, app)
    r = plena.put(
        f"/toc/snt/projetos/{projeto}/passos/{chaves['1.1']}/status",
        json={"status": "concluido"},
    )
    print(f"{r.status_code} · {r.json()['error']['code']} · {r.json()['error']['message'][:80]}")
    assert r.status_code == 422
    valida_envelope_de_erro(r)
    assert "nenhum" in r.json()["error"]["message"]


# ---------------------------------------------------------------------------------------
# RF-17 · painel de acompanhamento e RF-19 · vista tabular
# ---------------------------------------------------------------------------------------


def test_o_painel_traz_contagens_por_status_e_pendencias_com_salto(plena, app) -> None:
    projeto, chaves = arvore_sintetica(plena, app)
    plena.put(
        f"/toc/snt/projetos/{projeto}/passos/{chaves['1.1']}/status",
        json={"status": "em_execucao"},
    )
    r = plena.get(f"/toc/snt/projetos/{projeto}/acompanhamento")
    corpo = valida_contra_o_contrato(
        app, r, "get", "/toc/snt/projetos/{projeto_id}/acompanhamento"
    )
    print(
        f"{r.status_code} · passos={corpo['passos']} por_status={corpo['por_status']} "
        f"pendências={len(corpo['pendencias'])}"
    )
    assert corpo["passos"] == 5
    assert corpo["por_status"]["em_execucao"] == 1
    assert all({"no_id", "numero", "tipo"} <= set(p) for p in corpo["pendencias"])


def test_a_vista_tabular_sai_indentada_em_ordem_estrutural(plena, app) -> None:
    projeto, _ = arvore_sintetica(plena, app)
    r = plena.get(f"/toc/snt/projetos/{projeto}/tabela")
    corpo = valida_contra_o_contrato(app, r, "get", "/toc/snt/projetos/{projeto_id}/tabela")
    print(f"{r.status_code} · linhas={[(l['numero'], l['nivel']) for l in corpo['linhas']]}")
    assert [l["numero"] for l in corpo["linhas"]] == ["1", "1.1", "1.1.1", "1.1.2", "1.2"]
    assert [l["nivel"] for l in corpo["linhas"]] == [0, 1, 2, 2, 1]


def test_a_exportacao_sai_pelo_http_sem_numero_nenhum(plena, app) -> None:
    projeto, _ = arvore_sintetica(plena, app)
    r = plena.get(f"/toc/snt/projetos/{projeto}/exportacao")
    corpo = valida_contra_o_contrato(app, r, "get", "/toc/snt/projetos/{projeto_id}/exportacao")
    print(f"{r.status_code} · versao={corpo['versao']} passos={len(corpo['passos'])}")
    assert corpo["versao"] == "toc.snt/1"
    assert "numero" not in r.text


# ---------------------------------------------------------------------------------------
# A fronteira: autorização, inquilino e a porta dos fundos do agregado
# ---------------------------------------------------------------------------------------


def test_a_observadora_le_e_nao_escreve(plena, leitora, app) -> None:
    projeto, chaves = arvore_sintetica(plena, app)
    leitura = leitora.get(f"/toc/snt/projetos/{projeto}")
    negadas = 0
    for metodo, caminho, corpo in (
        ("post", f"/toc/snt/projetos/{projeto}/passos", {"estrategia": "não entra"}),
        ("put", f"/toc/snt/projetos/{projeto}/meta-global", {"meta_global": "outra"}),
        ("put", f"/toc/snt/projetos/{projeto}/passos/{chaves['1']}/status", {"status": "validado"}),
        ("delete", f"/toc/snt/projetos/{projeto}/passos/{chaves['1.1']}", None),
    ):
        resposta = getattr(leitora, metodo)(
            caminho, **({"json": corpo} if corpo is not None else {})
        )
        assert resposta.status_code == 403, f"{metodo} {caminho} → {resposta.status_code}"
        valida_envelope_de_erro(resposta)
        negadas += 1
    print(f"leitura={leitura.status_code} · escritas recusadas={negadas} de 4")
    assert negadas == 4


def test_a_arvore_de_outro_inquilino_nao_existe(plena, outro_inquilino, app) -> None:
    projeto, _ = arvore_sintetica(plena, app)
    r = outro_inquilino.get(f"/toc/snt/projetos/{projeto}")
    print(f"{r.status_code} · {r.json()['error']['code']}")
    assert r.status_code == 404
    valida_envelope_de_erro(r)


def test_a_rota_generica_do_m1_recusa_mexer_no_grafo_da_snt(plena, app) -> None:
    """A porta dos fundos do agregado continua fechada para a ferramenta que nasce agora."""
    projeto, _ = arvore_sintetica(plena, app)
    r = plena.post(f"/toc/projetos/{projeto}/nos", json={"titulo": "por fora"})
    corpo = r.json()
    print(f"{r.status_code} · code={corpo['error']['code']} · raiz={corpo['error'].get('details')}")
    assert r.status_code == 409
    valida_envelope_de_erro(r)


def test_a_anonima_nao_entra(anonima, app) -> None:
    r = anonima.get(f"/toc/snt/projetos/{uuid4()}")
    print(f"{r.status_code} · {r.json()['error']['code']}")
    assert r.status_code == 401
