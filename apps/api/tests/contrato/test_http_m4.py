"""A superfície HTTP do M4 — ARF, APR, AT e a cadeia, sob `/toc` (spec 008).

Siglas, uma vez neste arquivo: **M4** — Árvores de Futuro e Implementação · **ARF** —
Árvore da Realidade Futura · **APR** — Árvore de Pré-Requisitos · **AT** — Árvore de
Transição · **ARA** — Árvore da Realidade Atual · **UDE** — Efeito Indesejável · **NC** —
Nuvem de Conflito · **OI** — Objetivo Intermediário · **HTTP** — *HyperText Transfer
Protocol* · **RF/RN** — requisito funcional / regra de negócio da spec 008.

Cada corpo é validado contra o **OpenAPI que a própria aplicação declara** — a diferença
entre "a resposta tem os campos que eu quis" e "a resposta é o que eu prometi ao cliente".

Quatro provas que só a borda dá:

1. a cadeia inteira atravessa o HTTP, e a vista da cadeia a devolve percorrível (RF-42);
2. a recusa da RN-13 chega ao cliente como **código estável**, não como texto;
3. a rota genérica do M1 **recusa** mexer no grafo dos três tipos novos de projeto — a
   porta dos fundos continua fechada para as ferramentas que nascem agora;
4. **não existe rota assistida de ramo negativo** (RF-10), e a ausência é medida no
   OpenAPI publicado, não afirmada em prosa.
"""
from __future__ import annotations

from uuid import uuid4

from .conftest import valida_contra_o_contrato, valida_envelope_de_erro

UDE_UM = "A taxa de evasão no primeiro semestre é de 22%."
UDE_DOIS = "O caixa da instituição fecha o trimestre negativo."
INJECAO = "faseamento orçamentário condicionado a marco de receita"
EFEITO = "as duas frentes recebem verba no trimestre"
OBSTACULO = "Há apenas uma pessoa treinada no acompanhamento do marco"
OI = "Existem três pessoas treinadas e escaladas"


# --------------------------------------------------------------------------------------
# Apoio: a análise sintética da Instituição Horizonte, montada pelas rotas
# --------------------------------------------------------------------------------------


def ara_com_udes_validados(plena, app):
    r = plena.post("/toc/ara/projetos", json={"nome": "Realidade atual"})
    assert r.status_code == 201, r.text
    ara = r.json()
    udes = []
    for enunciado in (UDE_UM, UDE_DOIS):
        no = plena.post(
            f"/toc/ara/projetos/{ara['id']}/efeitos", json={"titulo": enunciado}
        ).json()
        plena.post(f"/toc/ara/projetos/{ara['id']}/nos/{no['id']}/ude", json={})
        plena.post(
            f"/toc/ara/projetos/{ara['id']}/nos/{no['id']}/pareceres",
            json={
                "favoravel": True,
                "justificativa": "a queixa é contínua e está na esfera da coordenação",
            },
        )
        r = plena.put(
            f"/toc/ara/projetos/{ara['id']}/nos/{no['id']}/status",
            json={"status": "validado"},
        )
        assert r.status_code == 200, r.text
        udes.append(no["id"])
    return ara["id"], udes


def nuvem_com_injecao_escolhida(plena, app):
    ara_id, udes = ara_com_udes_validados(plena, app)
    r = plena.post(
        "/toc/cadeia/promocoes",
        json={"ara_projeto_id": ara_id, "no_ids": udes, "nome": "Dilema da expansão"},
    )
    assert r.status_code == 201, r.text
    nuvem = valida_contra_o_contrato(app, r, "POST", "/toc/cadeia/promocoes")
    premissa = plena.post(
        f"/toc/nc/projetos/{nuvem['id']}/arestas/D_D_PRIME/premissas",
        json={"texto": "o orçamento é indivisível dentro do exercício"},
    ).json()
    injecao = plena.post(
        f"/toc/nc/projetos/{nuvem['id']}/premissas/{premissa['id']}/injecoes",
        json={"texto": INJECAO},
    ).json()
    r = plena.put(
        f"/toc/nc/projetos/{nuvem['id']}/injecoes/{injecao['id']}/status",
        json={"status": "escolhida"},
    )
    assert r.status_code == 200, r.text
    return ara_id, udes, nuvem["id"], injecao["id"]


# --------------------------------------------------------------------------------------
# E4.1 — a ARF pelo HTTP
# --------------------------------------------------------------------------------------


def test_criar_a_arf_devolve_o_projeto_com_os_papeis_e_a_verificacao(plena, app):
    r = plena.post("/toc/arf/projetos", json={"nome": "Futuro da expansão"})
    assert r.status_code == 201, r.text
    arf = valida_contra_o_contrato(app, r, "POST", "/toc/arf/projetos")

    print(f"ARF criada: {arf['nome']!r} · verificação={arf['verificacao']}")
    assert arf["nos"] == []
    assert arf["verificacao"]["sem_origem_vinculada"] is True
    assert arf["ramos"] == []


def test_a_arf_tipa_o_no_pelo_papel_e_le_a_aresta_por_suficiencia(plena, app):
    arf = plena.post("/toc/arf/projetos", json={"nome": "Futuro"}).json()
    injecao = plena.post(
        f"/toc/arf/projetos/{arf['id']}/nos",
        json={"papel": "injecao", "titulo": INJECAO},
    ).json()
    efeito = plena.post(
        f"/toc/arf/projetos/{arf['id']}/nos",
        json={"papel": "efeito_futuro", "titulo": EFEITO},
    ).json()
    r = plena.post(
        f"/toc/arf/projetos/{arf['id']}/arestas",
        json={"origem_id": injecao["id"], "destino_id": efeito["id"]},
    )
    assert r.status_code == 201, r.text

    corpo = valida_contra_o_contrato(
        app, plena.get(f"/toc/arf/projetos/{arf['id']}"), "GET", "/toc/arf/projetos/{projeto_id}"
    )
    elo = corpo["elos"][0]
    print(f"papéis: {[n['papel'] for n in corpo['nos']]} · leitura: {elo['leitura']}")
    assert sorted(n["papel"] for n in corpo["nos"]) == ["efeito_futuro", "injecao"]
    assert elo["leitura"] == f"Se {INJECAO}, então {EFEITO}"
    assert elo["exame"]["estado"] == "nao_examinado"


def test_o_ramo_negativo_e_marcado_tratado_e_aceito_pela_borda(plena, app):
    arf = plena.post("/toc/arf/projetos", json={"nome": "Futuro"}).json()
    colateral = plena.post(
        f"/toc/arf/projetos/{arf['id']}/nos",
        json={"papel": "efeito_futuro", "titulo": "a Secretaria acumula dupla jornada"},
    ).json()
    corte = plena.post(
        f"/toc/arf/projetos/{arf['id']}/nos",
        json={"papel": "injecao", "titulo": "contratação temporária no pico"},
    ).json()

    r = plena.post(
        f"/toc/arf/projetos/{arf['id']}/ramos", json={"no_id": colateral["id"]}
    )
    assert r.status_code == 201, r.text
    ramo = valida_contra_o_contrato(app, r, "POST", "/toc/arf/projetos/{projeto_id}/ramos")
    assert ramo["estado"] == "aberto"

    r = plena.put(
        f"/toc/arf/projetos/{arf['id']}/ramos/{ramo['id']}",
        json={"estado": "tratado", "injecao_de_corte_id": corte["id"]},
    )
    assert r.status_code == 200, r.text
    tratado = valida_contra_o_contrato(
        app, r, "PUT", "/toc/arf/projetos/{projeto_id}/ramos/{ramo_id}"
    )
    print(f"ramo: {tratado['estado']} por {tratado['injecao_de_corte_id']}")
    assert tratado["estado"] == "tratado"
    assert tratado["injecao_de_corte_id"] == corte["id"]


def test_tratar_sem_injecao_de_corte_e_recusado_com_codigo_estavel(plena, app):
    arf = plena.post("/toc/arf/projetos", json={"nome": "Futuro"}).json()
    colateral = plena.post(
        f"/toc/arf/projetos/{arf['id']}/nos",
        json={"papel": "efeito_futuro", "titulo": "a Secretaria acumula jornada"},
    ).json()
    ramo = plena.post(
        f"/toc/arf/projetos/{arf['id']}/ramos", json={"no_id": colateral["id"]}
    ).json()

    r = plena.put(
        f"/toc/arf/projetos/{arf['id']}/ramos/{ramo['id']}", json={"estado": "tratado"}
    )

    erro = valida_envelope_de_erro(r)
    print(f"{r.status_code} {erro['code']} — {erro.get('details')}")
    assert r.status_code == 422
    # O campo obrigatório é conferido na BORDA, antes do domínio: é problema de argumento,
    # e o código é o que o cliente web já discrimina.
    assert erro["code"] == "INVALID_ARGUMENT"


def test_aceitar_um_ramo_exige_justificativa_pela_borda(plena, app):
    arf = plena.post("/toc/arf/projetos", json={"nome": "Futuro"}).json()
    colateral = plena.post(
        f"/toc/arf/projetos/{arf['id']}/nos",
        json={"papel": "efeito_futuro", "titulo": "a Secretaria acumula jornada"},
    ).json()
    ramo = plena.post(
        f"/toc/arf/projetos/{arf['id']}/ramos", json={"no_id": colateral["id"]}
    ).json()

    r = plena.put(
        f"/toc/arf/projetos/{arf['id']}/ramos/{ramo['id']}", json={"estado": "aceito"}
    )
    erro = valida_envelope_de_erro(r)
    print(f"{r.status_code} {erro['code']} regra={erro.get('details', {}).get('regra')}")
    assert r.status_code == 409
    assert erro["details"]["regra"] == "justificativa_obrigatoria"

    r = plena.put(
        f"/toc/arf/projetos/{arf['id']}/ramos/{ramo['id']}",
        json={"estado": "aceito", "justificativa": "o pico dura três semanas"},
    )
    assert r.status_code == 200, r.text
    # O autor vem do PRINCIPAL, nunca do corpo do pedido — a mesma regra do parecer do M2.
    assert r.json()["autor"] == "usr-facilitadora"


def test_a_verificacao_da_arf_e_publicada_com_o_resumo(plena, app):
    arf = plena.post("/toc/arf/projetos", json={"nome": "Futuro"}).json()
    plena.post(
        f"/toc/arf/projetos/{arf['id']}/nos",
        json={"papel": "injecao", "titulo": INJECAO},
    )

    r = plena.post(f"/toc/arf/projetos/{arf['id']}/verificacoes")

    assert r.status_code == 200, r.text
    corpo = valida_contra_o_contrato(
        app, r, "POST", "/toc/arf/projetos/{projeto_id}/verificacoes"
    )
    print(f"verificação: {corpo}")
    assert corpo["injecoes_sem_efeito"] == 1
    assert corpo["pronta"] is False


# --------------------------------------------------------------------------------------
# E4.2 — a APR pelo HTTP
# --------------------------------------------------------------------------------------


def test_a_apr_nasce_com_o_objetivo_e_le_a_dependencia_por_necessidade(plena, app):
    r = plena.post(
        "/toc/apr/projetos",
        json={"nome": "Implantação", "objetivo": "O faseamento está implantado"},
    )
    assert r.status_code == 201, r.text
    apr = valida_contra_o_contrato(app, r, "POST", "/toc/apr/projetos")
    print(f"objetivo: {apr['objetivo']['titulo']!r} papel={apr['objetivo']['papel']}")
    assert apr["objetivo"]["papel"] == "objetivo"

    um = plena.post(
        f"/toc/apr/projetos/{apr['id']}/nos",
        json={"papel": "objetivo_intermediario", "titulo": OI},
    ).json()
    r = plena.post(
        f"/toc/apr/projetos/{apr['id']}/dependencias",
        json={"antes_id": um["id"], "depois_id": apr["objetivo"]["id"]},
    )
    assert r.status_code == 201, r.text

    corpo = plena.get(f"/toc/apr/projetos/{apr['id']}").json()
    leitura = corpo["dependencias"][0]["leitura"]
    print(f"leitura: {leitura}")
    assert "precisa existir antes de" in leitura
    assert "então" not in leitura


def test_a_verbalizacao_avisa_e_nao_veta_pela_borda(plena, app):
    apr = plena.post(
        "/toc/apr/projetos", json={"nome": "Implantação", "objetivo": "O processo responde"}
    ).json()
    r = plena.post(
        f"/toc/apr/projetos/{apr['id']}/nos",
        json={"papel": "obstaculo", "titulo": "Precisamos criar a conversão de dados"},
    )
    assert r.status_code == 201, r.text  # RN-08: aviso, nunca veto — o nó É criado
    no = r.json()

    r = plena.get(f"/toc/apr/projetos/{apr['id']}/nos/{no['id']}/verbalizacao")
    corpo = valida_contra_o_contrato(
        app, r, "GET", "/toc/apr/projetos/{projeto_id}/nos/{no_id}/verbalizacao"
    )
    print(f"veredito={corpo['veredito']} avisos={[a['codigo'] for a in corpo['avisos']]}")
    assert corpo["veredito"] == "aviso"
    assert corpo["avisos"][0]["codigo"] == "verbo_de_acao"
    assert corpo["avisos"][0]["trecho"]


def test_o_par_e_o_julgamento_atravessam_a_borda_com_a_leitura_do_teste(plena, app):
    apr = plena.post(
        "/toc/apr/projetos",
        json={"nome": "Implantação", "objetivo": "O faseamento está implantado"},
    ).json()
    obstaculo = plena.post(
        f"/toc/apr/projetos/{apr['id']}/nos",
        json={"papel": "obstaculo", "titulo": OBSTACULO},
    ).json()
    oi = plena.post(
        f"/toc/apr/projetos/{apr['id']}/nos",
        json={"papel": "objetivo_intermediario", "titulo": OI},
    ).json()

    r = plena.post(
        f"/toc/apr/projetos/{apr['id']}/pares",
        json={"obstaculo_id": obstaculo["id"], "objetivo_intermediario_id": oi["id"]},
    )
    assert r.status_code == 201, r.text
    par = valida_contra_o_contrato(app, r, "POST", "/toc/apr/projetos/{projeto_id}/pares")
    print(f"teste de validade: {par['teste_de_validade']}")
    assert par["teste_de_validade"].startswith(f"Se {OI}, então {OBSTACULO}")

    r = plena.post(
        f"/toc/apr/projetos/{apr['id']}/pares/{par['id']}/julgamentos",
        json={"valido": True, "justificativa": "três pessoas cobrem o pico"},
    )
    assert r.status_code == 201, r.text
    # O autor vem do principal, nunca do corpo (RN-07 com a regra do M2).
    assert r.json()["julgamentos"][0]["autor"] == "usr-facilitadora"


def test_o_sequenciamento_e_a_tabela_resumo_saem_pela_borda(plena, app):
    apr = plena.post(
        "/toc/apr/projetos",
        json={"nome": "Implantação", "objetivo": "O faseamento está implantado"},
    ).json()
    obstaculo = plena.post(
        f"/toc/apr/projetos/{apr['id']}/nos",
        json={"papel": "obstaculo", "titulo": OBSTACULO},
    ).json()
    oi = plena.post(
        f"/toc/apr/projetos/{apr['id']}/nos",
        json={"papel": "objetivo_intermediario", "titulo": OI},
    ).json()
    plena.post(
        f"/toc/apr/projetos/{apr['id']}/pares",
        json={"obstaculo_id": obstaculo["id"], "objetivo_intermediario_id": oi["id"]},
    )
    plena.post(
        f"/toc/apr/projetos/{apr['id']}/dependencias",
        json={"antes_id": oi["id"], "depois_id": apr["objetivo"]["id"]},
    )

    r = plena.post(f"/toc/apr/projetos/{apr['id']}/sequenciamentos")
    sequencia = valida_contra_o_contrato(
        app, r, "POST", "/toc/apr/projetos/{projeto_id}/sequenciamentos"
    )
    resumo = valida_contra_o_contrato(
        app,
        plena.get(f"/toc/apr/projetos/{apr['id']}/resumo"),
        "GET",
        "/toc/apr/projetos/{projeto_id}/resumo",
    )
    print(f"camadas={sequencia['camadas']} · linhas do resumo={len(resumo['linhas'])}")
    assert sequencia["completo"] is True
    assert sequencia["bloqueado"] is False
    assert resumo["linhas"][0]["obstaculo"] == OBSTACULO


def test_dependencia_circular_e_pendencia_bloqueante_na_resposta(plena, app):
    apr = plena.post(
        "/toc/apr/projetos", json={"nome": "Implantação", "objetivo": "O processo responde"}
    ).json()
    um = plena.post(
        f"/toc/apr/projetos/{apr['id']}/nos",
        json={"papel": "objetivo_intermediario", "titulo": OI},
    ).json()
    outro = plena.post(
        f"/toc/apr/projetos/{apr['id']}/nos",
        json={"papel": "objetivo_intermediario", "titulo": "A escala está publicada"},
    ).json()
    plena.post(
        f"/toc/apr/projetos/{apr['id']}/dependencias",
        json={"antes_id": um["id"], "depois_id": outro["id"]},
    )
    plena.post(
        f"/toc/apr/projetos/{apr['id']}/dependencias",
        json={"antes_id": outro["id"], "depois_id": um["id"]},
    )

    sequencia = plena.post(f"/toc/apr/projetos/{apr['id']}/sequenciamentos").json()

    print(f"bloqueado={sequencia['bloqueado']} ciclos={sequencia['ciclos']}")
    assert sequencia["bloqueado"] is True
    assert len(sequencia["ciclos"]) == 1


# --------------------------------------------------------------------------------------
# E4.3 — a AT pelo HTTP
# --------------------------------------------------------------------------------------


def test_o_passo_exige_a_tripla_e_publica_a_leitura_corrida(plena, app):
    at = plena.post("/toc/at/projetos", json={"nome": "Transição"}).json()

    incompleto = plena.post(
        f"/toc/at/projetos/{at['id']}/passos",
        json={"acao": "publicar a chamada", "necessidade": "  ", "resultado_esperado": "lista"},
    )
    erro = valida_envelope_de_erro(incompleto)
    print(f"sem a tripla: {incompleto.status_code} {erro['code']}")
    assert incompleto.status_code == 422

    r = plena.post(
        f"/toc/at/projetos/{at['id']}/passos",
        json={
            "acao": "publicar a chamada interna de treinamento",
            "necessidade": "não há hoje candidato mapeado",
            "resultado_esperado": "lista de inscritos até sexta",
        },
    )
    assert r.status_code == 201, r.text
    passo = valida_contra_o_contrato(app, r, "POST", "/toc/at/projetos/{projeto_id}/passos")
    print(f"leitura: {passo['leitura']}")
    assert passo["leitura"] == (
        "Para não há hoje candidato mapeado, publicar a chamada interna de treinamento; "
        "espero lista de inscritos até sexta"
    )


def test_o_status_do_passo_muda_e_a_divergencia_aparece_no_resumo(plena, app):
    at = plena.post("/toc/at/projetos", json={"nome": "Transição"}).json()
    passo = plena.post(
        f"/toc/at/projetos/{at['id']}/passos",
        json={
            "acao": "publicar a chamada interna",
            "necessidade": "não há candidato mapeado",
            "resultado_esperado": "lista de inscritos até sexta",
        },
    ).json()

    sem_motivo = plena.put(
        f"/toc/at/projetos/{at['id']}/passos/{passo['id']}/status",
        json={"status": "bloqueado"},
    )
    assert sem_motivo.status_code == 409
    assert valida_envelope_de_erro(sem_motivo)["details"]["motivo"] == "motivo_obrigatorio"

    r = plena.put(
        f"/toc/at/projetos/{at['id']}/passos/{passo['id']}/status",
        json={"status": "concluido", "resultado_real": "apenas duas inscritas"},
    )
    assert r.status_code == 200, r.text
    corpo = valida_contra_o_contrato(
        app, r, "PUT", "/toc/at/projetos/{projeto_id}/passos/{no_id}/status"
    )
    print(f"esperado={corpo['resultado_esperado']!r} real={corpo['resultado_real']!r}")
    assert corpo["resultado_esperado"] == "lista de inscritos até sexta"
    assert corpo["divergente"] is True

    at_lida = plena.get(f"/toc/at/projetos/{at['id']}").json()
    assert at_lida["resumo"]["concluido"] == 1


# --------------------------------------------------------------------------------------
# E4.4 — o encadeamento e a vista da cadeia pelo HTTP
# --------------------------------------------------------------------------------------


def test_promover_ude_nao_validado_e_recusado_com_a_regra_nomeada(plena, app):
    r = plena.post("/toc/ara/projetos", json={"nome": "Realidade atual"})
    ara = r.json()
    no = plena.post(f"/toc/ara/projetos/{ara['id']}/efeitos", json={"titulo": UDE_UM}).json()
    plena.post(f"/toc/ara/projetos/{ara['id']}/nos/{no['id']}/ude", json={})

    r = plena.post(
        "/toc/cadeia/promocoes",
        json={"ara_projeto_id": ara["id"], "no_ids": [no["id"]], "nome": "Dilema"},
    )

    erro = valida_envelope_de_erro(r)
    print(f"{r.status_code} {erro['code']} regra={erro['details']['regra']}")
    assert r.status_code == 409
    assert erro["details"]["regra"] == "ude_nao_validado"


def test_semear_injecao_candidata_e_recusado(plena, app):
    ara_id, udes = ara_com_udes_validados(plena, app)
    nuvem = plena.post(
        "/toc/cadeia/promocoes",
        json={"ara_projeto_id": ara_id, "no_ids": udes, "nome": "Dilema"},
    ).json()
    premissa = plena.post(
        f"/toc/nc/projetos/{nuvem['id']}/arestas/D_D_PRIME/premissas",
        json={"texto": "o orçamento é indivisível"},
    ).json()
    injecao = plena.post(
        f"/toc/nc/projetos/{nuvem['id']}/premissas/{premissa['id']}/injecoes",
        json={"texto": INJECAO},
    ).json()

    r = plena.post(
        "/toc/cadeia/semeaduras",
        json={"nc_projeto_id": nuvem["id"], "injecao_id": injecao["id"], "nome": "Futuro"},
    )

    erro = valida_envelope_de_erro(r)
    print(f"{r.status_code} {erro['code']} regra={erro['details']['regra']}")
    assert r.status_code == 409
    assert erro["details"]["regra"] == "injecao_nao_escolhida"


def test_a_cadeia_inteira_atravessa_a_borda_e_a_vista_a_percorre(plena, app):
    ara_id, udes, nc_id, injecao_id = nuvem_com_injecao_escolhida(plena, app)

    r = plena.post(
        "/toc/cadeia/semeaduras",
        json={"nc_projeto_id": nc_id, "injecao_id": injecao_id, "nome": "Futuro da expansão"},
    )
    assert r.status_code == 201, r.text
    arf = valida_contra_o_contrato(app, r, "POST", "/toc/cadeia/semeaduras")
    assert arf["nos"][0]["titulo"] == INJECAO
    assert arf["nos"][0]["papel"] == "injecao"

    efeito = plena.post(
        f"/toc/arf/projetos/{arf['id']}/nos",
        json={"papel": "efeito_futuro", "titulo": EFEITO},
    ).json()
    r = plena.post(
        f"/toc/arf/projetos/{arf['id']}/espelhos",
        json={"no_id": efeito["id"], "ude_id": udes[0]},
    )
    assert r.status_code == 201, r.text

    r = plena.post(
        "/toc/cadeia/derivacoes/apr",
        json={"arf_projeto_id": arf["id"], "no_id": efeito["id"], "nome": "Implantação"},
    )
    assert r.status_code == 201, r.text
    apr = valida_contra_o_contrato(app, r, "POST", "/toc/cadeia/derivacoes/apr")
    oi = plena.post(
        f"/toc/apr/projetos/{apr['id']}/nos",
        json={"papel": "objetivo_intermediario", "titulo": OI},
    ).json()

    r = plena.post(
        "/toc/cadeia/derivacoes/at",
        json={"apr_projeto_id": apr["id"], "no_id": oi["id"], "nome": "Transição"},
    )
    assert r.status_code == 201, r.text
    at = valida_contra_o_contrato(app, r, "POST", "/toc/cadeia/derivacoes/at")

    r = plena.get(f"/toc/cadeia/{arf['id']}")
    cadeia = valida_contra_o_contrato(app, r, "GET", "/toc/cadeia/{projeto_id}")
    print(
        f"cadeia pelo HTTP: {' → '.join(cadeia['ferramentas'])} · "
        f"elos={len(cadeia['elos'])} · resumo={cadeia['resumo']}"
    )
    assert cadeia["ferramentas"] == ["ara", "nc", "arf", "apr", "at"]
    assert len(cadeia["elos"]) == 4
    assert all(elo["estado"] == "ativa" for elo in cadeia["elos"])
    assert at["alvo"]["projeto_id"] == apr["id"]


def test_excluir_um_projeto_da_cadeia_deixa_o_elo_pendente_e_nao_o_apaga(plena, app):
    ara_id, udes = ara_com_udes_validados(plena, app)
    nuvem = plena.post(
        "/toc/cadeia/promocoes",
        json={"ara_projeto_id": ara_id, "no_ids": udes, "nome": "Dilema"},
    ).json()

    assert plena.delete(f"/toc/projetos/{nuvem['id']}").status_code in (200, 204)

    cadeia = plena.get(f"/toc/cadeia/{ara_id}").json()
    print(f"elos={len(cadeia['elos'])} · estados={[e['estado'] for e in cadeia['elos']]}")
    assert len(cadeia["elos"]) == 1
    assert cadeia["elos"][0]["estado"] == "pendente"
    assert cadeia["elos"][0]["motivo"]

    assert plena.post(f"/toc/projetos/{nuvem['id']}/restaurar").status_code == 200
    assert plena.get(f"/toc/cadeia/{ara_id}").json()["elos"][0]["estado"] == "ativa"


# --------------------------------------------------------------------------------------
# A porta dos fundos continua fechada, e a rota assistida de ramo não existe
# --------------------------------------------------------------------------------------


def test_a_rota_generica_do_m1_recusa_mexer_no_grafo_das_tres_arvores_novas(plena, app):
    for caminho, corpo, raiz in (
        ("/toc/arf/projetos", {"nome": "Futuro"}, "ProjetoARF"),
        (
            "/toc/apr/projetos",
            {"nome": "Implantação", "objetivo": "O processo responde"},
            "ProjetoAPR",
        ),
        ("/toc/at/projetos", {"nome": "Transição"}, "ProjetoAT"),
    ):
        projeto = plena.post(caminho, json=corpo).json()
        r = plena.post(f"/toc/projetos/{projeto['id']}/nos", json={"titulo": "por fora"})
        erro = valida_envelope_de_erro(r)
        print(f"{caminho}: {r.status_code} {erro['code']} raiz={erro['details']['raiz']}")
        assert r.status_code == 409
        assert erro["code"] == "AGGREGATE_ROOT_REQUIRED"
        assert erro["details"]["raiz"] == raiz


def test_nao_existe_rota_assistida_de_ramo_negativo(app):
    """RF-10: a marcação é manual por decisão de round — a prova é NEGATIVA (DoD 8)."""
    caminhos = list(app.openapi()["paths"])
    suspeitas = [
        c
        for c in caminhos
        if "ramo" in c and ("sugest" in c or "suggest" in c or "assistid" in c)
    ]
    print(f"rotas publicadas: {len(caminhos)} · assistidas de ramo negativo: {suspeitas}")
    assert suspeitas == []


def test_quem_so_le_nao_muta_as_tres_arvores(leitora, plena, app):
    arf = plena.post("/toc/arf/projetos", json={"nome": "Futuro"}).json()
    r = leitora.post(
        f"/toc/arf/projetos/{arf['id']}/nos", json={"papel": "injecao", "titulo": INJECAO}
    )
    erro = valida_envelope_de_erro(r)
    print(f"{r.status_code} {erro['code']} capacidade={erro['details']['capacidade']}")
    assert r.status_code == 403
    assert erro["details"]["capacidade"] == "toc:write"
    # E lê sem problema: a leitura é operação governada, com `toc:read`.
    assert leitora.get(f"/toc/arf/projetos/{arf['id']}").status_code == 200


def test_projeto_de_outro_inquilino_e_indistinguivel_de_inexistente(plena, outro_inquilino):
    arf = plena.post("/toc/arf/projetos", json={"nome": "Futuro"}).json()
    r = outro_inquilino.get(f"/toc/arf/projetos/{arf['id']}")
    print(f"outro inquilino: {r.status_code} {r.json()['error']['code']}")
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "NOT_FOUND"
