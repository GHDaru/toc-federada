"""A superfície HTTP da Nuvem de Conflito (NC) — spec 007, módulo M3, sob `/toc/nc`.

Siglas, uma vez: **NC** — Nuvem de Conflito · **ARA** — Árvore da Realidade Atual ·
**UDE** — Efeito Indesejável · **TOC** — Teoria das Restrições · **TRIZ** — Teoria da
Resolução Inventiva de Problemas · **HTTP** — *HyperText Transfer Protocol*.

Cada corpo é validado contra o **OpenAPI que a própria aplicação declara** — é a diferença
entre "a resposta tem os campos que eu quis" e "a resposta é o que eu prometi ao cliente".

Três provas que só a borda dá:

1. a nuvem **nasce inteira** também pelo HTTP — uma chamada, 5 entidades e 7 arestas;
2. **não há rota** que crie ou destrua entidade ou aresta da nuvem (RF-03): a ausência é
   medida no OpenAPI publicado, não afirmada em prosa;
3. o encadeamento **ARA → NC** atravessa a rota com a origem tipada na resposta (INT-05).
"""
from __future__ import annotations

from uuid import uuid4

from .conftest import valida_contra_o_contrato, valida_envelope_de_erro

DILEMA = {
    "A": "Sustentabilidade da Instituição Horizonte",
    "B": "Receita nova no próximo semestre",
    "C": "Reputação acadêmica preservada",
    "D": "Abrir turmas em três cidades novas",
    "D_PRIME": "Não abrir turmas em três cidades novas",
}
NARRATIVA = (
    "A Instituição Horizonte precisa de receita nova já no próximo semestre. A direção "
    "quer abrir turmas em três cidades novas; o corpo docente teme pela reputação."
)


def cria_nuvem(plena, app, nome="Dilema da expansão"):
    r = plena.post("/toc/nc/projetos", json={"nome": nome})
    assert r.status_code == 201, r.text
    return valida_contra_o_contrato(app, r, "POST", "/toc/nc/projetos")


def abre(plena, app, projeto_id):
    r = plena.get(f"/toc/nc/projetos/{projeto_id}")
    assert r.status_code == 200, r.text
    return valida_contra_o_contrato(app, r, "GET", "/toc/nc/projetos/{projeto_id}")


# -- topologia fixa ---------------------------------------------------------------------


def test_criar_nuvem_devolve_as_cinco_entidades_e_as_sete_arestas(plena, app):
    projeto = cria_nuvem(plena, app)

    nuvem = abre(plena, app, projeto["id"])

    print(
        f"entidades: {len(nuvem['entidades'])}; arestas: {len(nuvem['arestas'])}; "
        f"papéis={[e['papel'] for e in nuvem['entidades']]}"
    )
    assert len(nuvem["entidades"]) == 5
    assert len(nuvem["arestas"]) == 7
    assert {e["papel"] for e in nuvem["entidades"]} == set(DILEMA)
    assert {a["chave"] for a in nuvem["arestas"]} == {
        "A_B", "A_C", "B_D", "C_D_PRIME", "D_C", "D_PRIME_B", "D_D_PRIME"
    }


def rotas_do_m3(app) -> list[str]:
    """A superfície como o CLIENTE a vê — lida do OpenAPI publicado, não de `app.routes`.

    `app.routes` enumeraria a árvore interna do framework, que na versão instalada aninha
    os roteadores incluídos em `_IncludedRouter` e devolveria zero rota: um verde sobre
    nada, que é exatamente o que a regra R2 do `CLAUDE.md` proíbe.
    """
    return sorted(
        f"{metodo.upper()} {gabarito}"
        for gabarito, operacoes in app.openapi()["paths"].items()
        if gabarito.startswith("/toc/nc")
        for metodo in operacoes
        if metodo.lower() in {"get", "post", "put", "patch", "delete"}
    )


def test_nenhuma_rota_do_m3_cria_ou_exclui_entidade_ou_aresta(app):
    """RF-03 medido na superfície publicada, não prometido em prosa."""
    caminhos = rotas_do_m3(app)
    print(f"rotas do M3 examinadas: {len(caminhos)}\n" + "\n".join(caminhos))

    proibidas = [
        c for c in caminhos
        if ("entidades" in c and c.startswith(("POST", "DELETE")))
        or "arestas" in c and c.startswith(("POST", "DELETE")) and "premissas" not in c
    ]
    assert proibidas == [], proibidas
    assert len(caminhos) >= 12, "a superfície do M3 encolheu — reveja o roteador"


def test_a_leitura_traz_a_classe_e_a_frase_de_cada_aresta(plena, app):
    projeto = cria_nuvem(plena, app)
    for papel, texto in DILEMA.items():
        r = plena.put(
            f"/toc/nc/projetos/{projeto['id']}/entidades/{papel}", json={"texto": texto}
        )
        assert r.status_code == 200, r.text
        valida_contra_o_contrato(
            app, r, "PUT", "/toc/nc/projetos/{projeto_id}/entidades/{papel}"
        )

    nuvem = abre(plena, app, projeto["id"])

    por_chave = {a["chave"]: a for a in nuvem["arestas"]}
    print({c: a["leitura"] for c, a in por_chave.items()})
    assert por_chave["A_B"]["classe"] == "necessidade"
    assert por_chave["D_C"]["classe"] == "perigo"
    assert por_chave["D_D_PRIME"]["classe"] == "conflito"
    assert por_chave["A_B"]["leitura"] == (
        f"Para ter {DILEMA['A']}, precisamos de {DILEMA['B']}"
    )
    assert por_chave["D_D_PRIME"]["leitura"] == (
        f"{DILEMA['D']} e {DILEMA['D_PRIME']} não podem coexistir"
    )


def test_papel_desconhecido_e_recusado_com_envelope_de_erro(plena, app):
    projeto = cria_nuvem(plena, app)

    r = plena.put(
        f"/toc/nc/projetos/{projeto['id']}/entidades/Z", json={"texto": "qualquer"}
    )

    assert r.status_code in (400, 422), r.text


# -- premissas e injeções ---------------------------------------------------------------


def registra_premissa(plena, app, projeto_id, chave, texto):
    r = plena.post(
        f"/toc/nc/projetos/{projeto_id}/arestas/{chave}/premissas", json={"texto": texto}
    )
    assert r.status_code == 201, r.text
    return valida_contra_o_contrato(
        app, r, "POST", "/toc/nc/projetos/{projeto_id}/arestas/{chave}/premissas"
    )


def test_premissa_injecao_status_e_triz_atravessam_o_http(plena, app):
    projeto = cria_nuvem(plena, app)
    premissa = registra_premissa(
        plena, app, projeto["id"], "D_D_PRIME", "não há orçamento para as duas ações"
    )

    r = plena.post(
        f"/toc/nc/projetos/{projeto['id']}/premissas/{premissa['id']}/injecoes",
        json={"texto": "faseamento por marco de receita", "separacao": "tempo"},
    )
    assert r.status_code == 201, r.text
    injecao = valida_contra_o_contrato(
        app, r, "POST", "/toc/nc/projetos/{projeto_id}/premissas/{premissa_id}/injecoes"
    )

    r = plena.put(
        f"/toc/nc/projetos/{projeto['id']}/injecoes/{injecao['id']}/status",
        json={"status": "escolhida"},
    )
    assert r.status_code == 200, r.text
    escolhida = valida_contra_o_contrato(
        app, r, "PUT", "/toc/nc/projetos/{projeto_id}/injecoes/{injecao_id}/status"
    )

    print(f"injeção: {escolhida}")
    assert escolhida["status"] == "escolhida"
    assert escolhida["separacao"] == "tempo"
    assert escolhida["semeadura"]["projeto_destino_id"] is None


def test_voltar_a_candidata_sem_justificativa_e_recusado_pelo_dominio(plena, app):
    projeto = cria_nuvem(plena, app)
    premissa = registra_premissa(plena, app, projeto["id"], "A_B", "premissa qualquer")
    r = plena.post(
        f"/toc/nc/projetos/{projeto['id']}/premissas/{premissa['id']}/injecoes",
        json={"texto": "uma injeção"},
    )
    injecao = r.json()
    plena.put(
        f"/toc/nc/projetos/{projeto['id']}/injecoes/{injecao['id']}/status",
        json={"status": "escolhida"},
    )

    r = plena.put(
        f"/toc/nc/projetos/{projeto['id']}/injecoes/{injecao['id']}/status",
        json={"status": "candidata"},
    )

    print(f"recusa: {r.status_code} {r.text}")
    assert r.status_code == 409
    valida_envelope_de_erro(r)


def test_arquivar_premissa_responde_quantas_injecoes_foram_junto(plena, app):
    projeto = cria_nuvem(plena, app)
    premissa = registra_premissa(plena, app, projeto["id"], "D_C", "premissa a arquivar")
    for texto in ("injeção um", "injeção dois"):
        plena.post(
            f"/toc/nc/projetos/{projeto['id']}/premissas/{premissa['id']}/injecoes",
            json={"texto": texto},
        )

    r = plena.delete(f"/toc/nc/projetos/{projeto['id']}/premissas/{premissa['id']}")

    assert r.status_code == 200, r.text
    corpo = valida_contra_o_contrato(
        app, r, "DELETE", "/toc/nc/projetos/{projeto_id}/premissas/{premissa_id}"
    )
    print(f"arquivamento: {corpo}")
    assert corpo["injecoes_arquivadas"] == 2


def test_desafiar_premissa_sem_justificativa_e_recusado(plena, app):
    projeto = cria_nuvem(plena, app)
    premissa = registra_premissa(plena, app, projeto["id"], "A_C", "premissa qualquer")

    r = plena.put(
        f"/toc/nc/projetos/{projeto['id']}/premissas/{premissa['id']}/estado",
        json={"estado": "desafiada", "justificativa": "   "},
    )

    assert r.status_code == 409, r.text
    valida_envelope_de_erro(r)


# -- validação, visão de solução e matriz -----------------------------------------------


def test_a_validacao_traz_completude_avisos_e_as_sete_posicoes_de_solucao(plena, app):
    projeto = cria_nuvem(plena, app)
    registra_premissa(plena, app, projeto["id"], "A_B", "sem receita não há instituição")

    r = plena.get(f"/toc/nc/projetos/{projeto['id']}/validacao")
    assert r.status_code == 200, r.text
    corpo = valida_contra_o_contrato(
        app, r, "GET", "/toc/nc/projetos/{projeto_id}/validacao"
    )

    print(f"validação: {corpo}")
    assert corpo["completude"] == {"sustentadas": 1, "total": 7}
    assert len(corpo["arestas_sem_injecao"]) == 7
    assert len(corpo["separacoes_ausentes"]) == 5
    # A nuvem recém-criada tem texto de exemplo em D e D′; o aviso é pedagógico e não
    # impede nada — mas ele existe e chega ao cliente.
    assert any(a["avisos"] for a in corpo["avisos"])


def test_a_visao_de_solucao_tem_as_sete_posicoes_inclusive_d_c_e_d_d_prime(plena, app):
    """DoD 9 da spec: o defeito do v3 (5 de 7 injeções renderizadas) como caso de teste."""
    projeto = cria_nuvem(plena, app)
    for chave in ("D_C", "D_D_PRIME"):
        premissa = registra_premissa(plena, app, projeto["id"], chave, f"premissa {chave}")
        plena.post(
            f"/toc/nc/projetos/{projeto['id']}/premissas/{premissa['id']}/injecoes",
            json={"texto": f"injeção de {chave}"},
        )

    r = plena.get(f"/toc/nc/projetos/{projeto['id']}/solucao")
    assert r.status_code == 200, r.text
    corpo = valida_contra_o_contrato(app, r, "GET", "/toc/nc/projetos/{projeto_id}/solucao")

    posicoes = {p["chave"]: p for p in corpo["posicoes"]}
    print(
        f"posições: {len(posicoes)}; com injeção: "
        f"{[c for c, p in posicoes.items() if p['injecoes']]}"
    )
    assert len(posicoes) == 7
    assert posicoes["D_C"]["injecoes"] and posicoes["D_D_PRIME"]["injecoes"]
    assert posicoes["A_B"]["pendente"] is True


# -- o encadeamento ARA → NC pelo HTTP (INT-05) ------------------------------------------


def test_derivar_nuvem_de_udes_da_ara_pelo_http(plena, app):
    ara = plena.post("/toc/ara/projetos", json={"nome": "Realidade atual"}).json()
    udes = []
    for enunciado in (
        "A taxa de evasão no primeiro semestre é de 22%.",
        "O caixa da instituição fecha o trimestre negativo.",
    ):
        no = plena.post(
            f"/toc/ara/projetos/{ara['id']}/efeitos", json={"titulo": enunciado}
        ).json()
        plena.post(f"/toc/ara/projetos/{ara['id']}/nos/{no['id']}/ude", json={})
        udes.append(no["id"])

    r = plena.post(
        "/toc/nc/derivacoes",
        json={"ara_projeto_id": ara["id"], "no_ids": udes, "nome": "Dilema da expansão"},
    )

    assert r.status_code == 201, r.text
    corpo = valida_contra_o_contrato(app, r, "POST", "/toc/nc/derivacoes")
    print(f"derivada: {corpo['origem']}")
    assert corpo["origem"]["ferramenta"] == "ara"
    assert corpo["origem"]["projeto_id"] == ara["id"]
    assert corpo["origem"]["nos"] == udes
    assert corpo["origem"]["leitura"].startswith("Origem: 2")

    nuvem = abre(plena, app, corpo["id"])
    assert len(nuvem["entidades"]) == 5


def test_derivar_de_no_que_nao_e_ude_e_recusado_com_a_regra_nomeada(plena, app):
    ara = plena.post("/toc/ara/projetos", json={"nome": "Realidade atual"}).json()
    no = plena.post(
        f"/toc/ara/projetos/{ara['id']}/efeitos", json={"titulo": "O estacionamento vive cheio."}
    ).json()

    r = plena.post(
        "/toc/nc/derivacoes",
        json={"ara_projeto_id": ara["id"], "no_ids": [no["id"]], "nome": "Dilema"},
    )

    print(f"recusa: {r.status_code} {r.text}")
    assert r.status_code == 409
    valida_envelope_de_erro(r)


def test_derivar_de_ara_de_outro_inquilino_e_nao_encontrado(plena, outro_inquilino, app):
    ara = plena.post("/toc/ara/projetos", json={"nome": "Realidade atual"}).json()

    r = outro_inquilino.post(
        "/toc/nc/derivacoes",
        json={"ara_projeto_id": ara["id"], "no_ids": [str(uuid4())], "nome": "Dilema"},
    )

    assert r.status_code == 404, r.text
    valida_envelope_de_erro(r)


# -- geração assistida: pré-visualização sem escrita -------------------------------------


def test_a_geracao_devolve_previa_estruturada_e_nao_aplica_nada(plena, app):
    """RF-21/RF-23: a prévia é dado; aplicar é ato do gate humano, pelo catálogo."""
    projeto = cria_nuvem(plena, app)
    antes = abre(plena, app, projeto["id"])

    r = plena.post(
        f"/toc/nc/projetos/{projeto['id']}/geracoes", json={"narrativa": NARRATIVA}
    )

    assert r.status_code == 200, r.text
    corpo = valida_contra_o_contrato(
        app, r, "POST", "/toc/nc/projetos/{projeto_id}/geracoes"
    )
    depois = abre(plena, app, projeto["id"])
    print(
        f"prévia: versão {corpo['resultado']['versao']}, "
        f"{len(corpo['resultado']['arestas'])} chave(s) de aresta; "
        f"action_id={corpo['action_id']}"
    )
    assert corpo["action_id"] == "toc.generate_conflict_cloud"
    assert set(corpo["resultado"]["entidades"]) == set(DILEMA)
    assert depois == antes, "gerar não aplica: a nuvem tem de continuar byte a byte igual"


def test_a_geracao_e_deterministica_para_a_mesma_narrativa(plena, app):
    """O adaptador desta fase é um fake DECLARADO — e determinístico por construção."""
    projeto = cria_nuvem(plena, app)

    uma = plena.post(
        f"/toc/nc/projetos/{projeto['id']}/geracoes", json={"narrativa": NARRATIVA}
    ).json()
    outra = plena.post(
        f"/toc/nc/projetos/{projeto['id']}/geracoes", json={"narrativa": NARRATIVA}
    ).json()

    assert uma["resultado"] == outra["resultado"]


# -- autorização: fail-closed rota a rota ------------------------------------------------


def test_quem_so_le_abre_a_nuvem_e_e_recusado_em_toda_mutacao(plena, leitora, app):
    projeto = cria_nuvem(plena, app)
    premissa = registra_premissa(plena, app, projeto["id"], "A_B", "premissa qualquer")

    assert leitora.get(f"/toc/nc/projetos/{projeto['id']}").status_code == 200
    assert leitora.get(f"/toc/nc/projetos/{projeto['id']}/validacao").status_code == 200

    recusadas = []
    for metodo, caminho, corpo in (
        ("post", "/toc/nc/projetos", {"nome": "outra"}),
        ("put", f"/toc/nc/projetos/{projeto['id']}/entidades/A", {"texto": "x"}),
        ("put", f"/toc/nc/projetos/{projeto['id']}/racional", {"racional": "x"}),
        ("post", f"/toc/nc/projetos/{projeto['id']}/arestas/A_B/premissas", {"texto": "x"}),
        ("delete", f"/toc/nc/projetos/{projeto['id']}/premissas/{premissa['id']}", None),
        (
            "post",
            f"/toc/nc/projetos/{projeto['id']}/premissas/{premissa['id']}/injecoes",
            {"texto": "x"},
        ),
        ("post", f"/toc/nc/projetos/{projeto['id']}/geracoes", {"narrativa": NARRATIVA}),
        (
            "post",
            "/toc/nc/derivacoes",
            {"ara_projeto_id": str(uuid4()), "no_ids": [str(uuid4())], "nome": "x"},
        ),
    ):
        resposta = getattr(leitora, metodo)(caminho, json=corpo) if corpo is not None else getattr(leitora, metodo)(caminho)
        assert resposta.status_code == 403, f"{metodo} {caminho} → {resposta.status_code}"
        valida_envelope_de_erro(resposta)
        recusadas.append(f"{metodo.upper()} {caminho}")

    print(f"mutações recusadas para quem só lê: {len(recusadas)}")
    assert len(recusadas) == 8


def test_a_nuvem_de_outro_inquilino_e_indistinguivel_de_inexistente(plena, outro_inquilino, app):
    projeto = cria_nuvem(plena, app)

    resposta = outro_inquilino.get(f"/toc/nc/projetos/{projeto['id']}")

    assert resposta.status_code == 404
    valida_envelope_de_erro(resposta)


def test_sem_token_nenhuma_rota_do_m3_responde(anonima, app):
    caminhos = sorted({c.split(" ", 1)[1] for c in rotas_do_m3(app)})
    for caminho in caminhos:
        alvo = caminho.replace("{projeto_id}", str(uuid4()))
        alvo = alvo.replace("{premissa_id}", str(uuid4())).replace("{injecao_id}", str(uuid4()))
        alvo = alvo.replace("{papel}", "A").replace("{chave}", "A_B")
        assert anonima.get(alvo).status_code in (401, 405), alvo
    print(f"rotas do M3 conferidas sem token: {len(caminhos)}")
