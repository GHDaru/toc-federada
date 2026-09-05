"""A superfície HTTP da Árvore da Realidade Atual (ARA) — spec 005, módulo M2.

Os três casos canônicos da linhagem (RF-12) atravessam o HTTP aqui, e o que eles provam é
que a regra de negócio virou função pura de domínio: a mesma frase que a 4ª geração
mandava a um provedor de modelo de linguagem **do navegador**
(`tocbuilderv3/services/geminiService.ts:16`) é decidida agora sem rede, sem chave e sem
variação entre execuções.
"""
from __future__ import annotations

from uuid import uuid4

from .conftest import valida_contra_o_contrato, valida_envelope_de_erro

BOM = "A taxa de erros no processo X é de 15%."
CAUSA_EMBUTIDA = "Falta de treinamento causa erros."
SOLUCAO_EMBUTIDA = "Precisamos de um novo software."
SEGUNDO = "O retrabalho consome a equipe de análise."
TERCEIRO = "O prazo de entrega escorrega todo mês."


def cria_ara(plena, app, nome="Horizonte — ARA"):
    r = plena.post("/toc/ara/projetos", json={"nome": nome})
    assert r.status_code == 201, r.text
    return valida_contra_o_contrato(app, r, "POST", "/toc/ara/projetos")


def cria_efeito(plena, app, projeto_id, titulo):
    r = plena.post(f"/toc/ara/projetos/{projeto_id}/efeitos", json={"titulo": titulo})
    assert r.status_code == 201, r.text
    return valida_contra_o_contrato(
        app, r, "POST", "/toc/ara/projetos/{projeto_id}/efeitos"
    )


def liga(plena, projeto_id, origem, destino):
    r = plena.post(
        f"/toc/projetos/{projeto_id}/arestas",
        json={"origem_id": origem, "destino_id": destino},
    )
    assert r.status_code == 201, r.text
    return r.json()


# -- validação formal: a operação que não toca projeto nenhum -------------------------


def test_os_tres_casos_canonicos_da_linhagem_decidem_como_o_metodo_manda(plena, app):
    """RF-12, palavra por palavra da spec 005."""
    def valida(texto):
        r = plena.post("/toc/ara/validacoes", json={"texto": texto})
        return valida_contra_o_contrato(app, r, "POST", "/toc/ara/validacoes")

    assert valida(CAUSA_EMBUTIDA)["aprovado_nos_decidiveis"] is False
    assert valida(SOLUCAO_EMBUTIDA)["aprovado_nos_decidiveis"] is False
    assert valida(BOM)["aprovado_nos_decidiveis"] is True


def test_a_validacao_devolve_o_criterio_a_classe_e_o_trecho_que_a_motivou(plena, app):
    r = plena.post("/toc/ara/validacoes", json={"texto": CAUSA_EMBUTIDA})
    corpo = valida_contra_o_contrato(app, r, "POST", "/toc/ara/validacoes")

    assert len(corpo["vereditos"]) == 12, "8 decidíveis + 4 de julgamento (RF-07, RF-09)"
    reprovado = next(v for v in corpo["vereditos"] if v["veredito"] == "nao_atende")
    assert reprovado["classe"] == "decidivel"
    assert reprovado["trecho"], "sem trecho apontado não há como reformular (RF-15)"
    assert len(corpo["pendencias_de_julgamento"]) == 4
    assert corpo["versao_do_lexico"]


def test_indeterminado_conta_como_pendencia_e_nunca_como_reprovacao(plena, app):
    """RF-08: o critério de julgamento não vira chute nem vira vermelho."""
    corpo = plena.post("/toc/ara/validacoes", json={"texto": BOM}).json()
    de_julgamento = [v for v in corpo["vereditos"] if v["classe"] == "julgamento"]
    assert {v["veredito"] for v in de_julgamento} == {"indeterminado"}
    assert corpo["reprovacoes"] == []
    assert corpo["aprovado_nos_decidiveis"] is True


def test_a_leitora_valida_texto_porque_validar_nao_grava_nada(leitora, app):
    r = leitora.post("/toc/ara/validacoes", json={"texto": BOM})
    assert r.status_code == 200
    valida_contra_o_contrato(app, r, "POST", "/toc/ara/validacoes")


# -- projeto ARA, UDE e ficha -----------------------------------------------------------


def test_criar_ara_nasce_com_a_ferramenta_ara_e_o_no_nasce_efeito(plena, app):
    projeto = cria_ara(plena, app)
    assert projeto["ferramenta"] == "ara"
    no = cria_efeito(plena, app, projeto["id"], BOM)
    assert no["tipo"] == "efeito", "F-15: todo nó da ARA é um efeito, e quem decide é o servidor"


def test_marcar_ude_com_ficha_e_ler_a_ara_inteira(plena, app):
    projeto = cria_ara(plena, app)
    no = cria_efeito(plena, app, projeto["id"], BOM)

    r = plena.post(
        f"/toc/ara/projetos/{projeto['id']}/nos/{no['id']}/ude",
        json={
            "ficha": {
                "area_impactada": "Atendimento",
                "objetivo_afetado": "Entregar no prazo",
                "evidencias": ["Relatório de setembro"],
                "frequencia": "Semanal",
                "impactos_estimados": "Retrabalho de 12 horas por semana",
            }
        },
    )
    valida_contra_o_contrato(
        app, r, "POST", "/toc/ara/projetos/{projeto_id}/nos/{no_id}/ude"
    )

    leitura = plena.get(f"/toc/ara/projetos/{projeto['id']}")
    ara = valida_contra_o_contrato(app, leitura, "GET", "/toc/ara/projetos/{projeto_id}")
    assert len(ara["udes"]) == 1
    ude = ara["udes"][0]
    assert ude["no_id"] == no["id"]
    assert ude["status"] == "pendente"
    assert ude["ficha"]["area_impactada"] == "Atendimento"
    assert ude["validacao"]["aprovado_nos_decidiveis"] is True
    assert ara["resumo_por_status"]["pendente"] == 1


def test_marcar_texto_reprovado_cai_em_requer_refinamento_sozinho(plena, app):
    projeto = cria_ara(plena, app)
    no = cria_efeito(plena, app, projeto["id"], CAUSA_EMBUTIDA)
    plena.post(f"/toc/ara/projetos/{projeto['id']}/nos/{no['id']}/ude", json={})

    ara = plena.get(f"/toc/ara/projetos/{projeto['id']}").json()
    assert ara["udes"][0]["status"] == "requer_refinamento"


def test_reformular_reexecuta_a_validacao_no_mesmo_comando(plena, app):
    """RF-10: o veredito anterior não fica pendurado."""
    projeto = cria_ara(plena, app)
    no = cria_efeito(plena, app, projeto["id"], CAUSA_EMBUTIDA)
    plena.post(f"/toc/ara/projetos/{projeto['id']}/nos/{no['id']}/ude", json={})

    r = plena.post(
        f"/toc/ara/projetos/{projeto['id']}/nos/{no['id']}/reformulacoes",
        json={"texto": BOM},
    )
    valida_contra_o_contrato(
        app, r, "POST", "/toc/ara/projetos/{projeto_id}/nos/{no_id}/reformulacoes"
    )
    ude = plena.get(f"/toc/ara/projetos/{projeto['id']}").json()["udes"][0]
    assert ude["titulo"] == BOM
    assert ude["validacao"]["aprovado_nos_decidiveis"] is True


def test_desmarcar_ude_tira_o_marcador_e_mantem_o_no(plena, app):
    projeto = cria_ara(plena, app)
    no = cria_efeito(plena, app, projeto["id"], BOM)
    plena.post(f"/toc/ara/projetos/{projeto['id']}/nos/{no['id']}/ude", json={})

    r = plena.delete(f"/toc/ara/projetos/{projeto['id']}/nos/{no['id']}/ude")
    assert r.status_code == 204
    ara = plena.get(f"/toc/ara/projetos/{projeto['id']}").json()
    assert ara["udes"] == []
    assert [n["id"] for n in ara["projeto"]["nos"]] == [no["id"]]


# -- status: a guarda da RN-10 chega inteira ao cliente ---------------------------------


def test_validar_sem_parecer_humano_e_recusado_com_o_motivo_legivel_por_maquina(plena, app):
    projeto = cria_ara(plena, app)
    no = cria_efeito(plena, app, projeto["id"], BOM)
    plena.post(f"/toc/ara/projetos/{projeto['id']}/nos/{no['id']}/ude", json={})

    r = plena.put(
        f"/toc/ara/projetos/{projeto['id']}/nos/{no['id']}/status",
        json={"status": "validado"},
    )
    assert r.status_code == 409
    erro = valida_envelope_de_erro(r)
    assert erro["code"] == "INVALID_TRANSITION"
    assert erro["details"]["motivo"] == "sem_parecer_humano"


def test_validar_com_criterio_decidivel_vermelho_e_recusado(plena, app):
    projeto = cria_ara(plena, app)
    no = cria_efeito(plena, app, projeto["id"], CAUSA_EMBUTIDA)
    plena.post(f"/toc/ara/projetos/{projeto['id']}/nos/{no['id']}/ude", json={})
    plena.post(
        f"/toc/ara/projetos/{projeto['id']}/nos/{no['id']}/pareceres",
        json={"favoravel": True, "justificativa": "É queixa contínua e acionável."},
    )
    r = plena.put(
        f"/toc/ara/projetos/{projeto['id']}/nos/{no['id']}/status",
        json={"status": "validado"},
    )
    assert r.status_code == 409
    assert valida_envelope_de_erro(r)["details"]["motivo"] == "criterio_decidivel_reprovado"


def test_o_autor_do_parecer_e_o_principal_nunca_o_corpo_do_pedido(plena, app):
    """RF-16: quem validou vive em evento, e o autor não é texto que alguém mandou."""
    projeto = cria_ara(plena, app)
    no = cria_efeito(plena, app, projeto["id"], BOM)
    plena.post(f"/toc/ara/projetos/{projeto['id']}/nos/{no['id']}/ude", json={})

    recusado = plena.post(
        f"/toc/ara/projetos/{projeto['id']}/nos/{no['id']}/pareceres",
        json={
            "favoravel": True,
            "justificativa": "Confio em mim.",
            "autor": "quem-eu-quiser",
        },
    )
    assert recusado.status_code == 422, "o campo `autor` não existe no pedido e é rejeitado"

    ok = plena.post(
        f"/toc/ara/projetos/{projeto['id']}/nos/{no['id']}/pareceres",
        json={"favoravel": True, "justificativa": "É queixa contínua e acionável."},
    )
    assert ok.status_code == 204
    parecer = plena.get(f"/toc/ara/projetos/{projeto['id']}").json()["udes"][0]["pareceres"][0]
    assert parecer["autor"] == "usr-facilitadora"
    assert parecer["origem"] == "humano"
    assert parecer["proposta_id"] is None


def test_com_decidiveis_verdes_e_parecer_humano_o_status_fecha(plena, app):
    projeto = cria_ara(plena, app)
    no = cria_efeito(plena, app, projeto["id"], BOM)
    plena.post(f"/toc/ara/projetos/{projeto['id']}/nos/{no['id']}/ude", json={})
    plena.post(
        f"/toc/ara/projetos/{projeto['id']}/nos/{no['id']}/pareceres",
        json={"favoravel": True, "justificativa": "É queixa contínua e acionável."},
    )
    r = plena.put(
        f"/toc/ara/projetos/{projeto['id']}/nos/{no['id']}/status",
        json={"status": "validado"},
    )
    corpo = valida_contra_o_contrato(
        app, r, "PUT", "/toc/ara/projetos/{projeto_id}/nos/{no_id}/status"
    )
    assert corpo["status"] == "validado"


def test_reabrir_validado_sem_justificativa_e_recusado(plena, app):
    """RF-17: reabrir exige justificativa explícita."""
    projeto = cria_ara(plena, app)
    no = cria_efeito(plena, app, projeto["id"], BOM)
    plena.post(f"/toc/ara/projetos/{projeto['id']}/nos/{no['id']}/ude", json={})
    plena.post(
        f"/toc/ara/projetos/{projeto['id']}/nos/{no['id']}/pareceres",
        json={"favoravel": True, "justificativa": "É queixa contínua e acionável."},
    )
    plena.put(
        f"/toc/ara/projetos/{projeto['id']}/nos/{no['id']}/status",
        json={"status": "validado"},
    )
    r = plena.put(
        f"/toc/ara/projetos/{projeto['id']}/nos/{no['id']}/status",
        json={"status": "requer_refinamento"},
    )
    assert r.status_code == 409
    assert valida_envelope_de_erro(r)["details"]["motivo"] == "reabertura_sem_justificativa"


def test_status_desconhecido_e_recusado_na_borda(plena, app):
    projeto = cria_ara(plena, app)
    no = cria_efeito(plena, app, projeto["id"], BOM)
    plena.post(f"/toc/ara/projetos/{projeto['id']}/nos/{no['id']}/ude", json={})
    r = plena.put(
        f"/toc/ara/projetos/{projeto['id']}/nos/{no['id']}/status",
        json={"status": "quase-validado"},
    )
    assert r.status_code == 422
    assert valida_envelope_de_erro(r)["code"] == "INVALID_ARGUMENT"


# -- exame de suficiência do elo e conector E -------------------------------------------


def test_exame_com_reserva_obrigatoria_e_a_leitura_do_elo(plena, app):
    projeto = cria_ara(plena, app)
    a = cria_efeito(plena, app, projeto["id"], BOM)
    b = cria_efeito(plena, app, projeto["id"], SEGUNDO)
    aresta = liga(plena, projeto["id"], a["id"], b["id"])

    recusado = plena.put(
        f"/toc/ara/projetos/{projeto['id']}/arestas/{aresta['id']}/exame",
        json={"estado": "insuficiente"},
    )
    assert recusado.status_code == 409
    assert valida_envelope_de_erro(recusado)["code"] == "MUTATION_REFUSED"

    r = plena.put(
        f"/toc/ara/projetos/{projeto['id']}/arestas/{aresta['id']}/exame",
        json={"estado": "com_reserva", "reserva": "Falta a condição de volume."},
    )
    corpo = valida_contra_o_contrato(
        app, r, "PUT", "/toc/ara/projetos/{projeto_id}/arestas/{aresta_id}/exame"
    )
    assert corpo["estado"] == "com_reserva"
    assert corpo["reserva"] == "Falta a condição de volume."

    elo = plena.get(f"/toc/ara/projetos/{projeto['id']}").json()["elos"][0]
    assert elo["leitura"] == f"Se {BOM}, então {SEGUNDO}"
    assert elo["exame"]["estado"] == "com_reserva"


def test_estado_de_exame_desconhecido_e_dado_invalido(plena, app):
    projeto = cria_ara(plena, app)
    a = cria_efeito(plena, app, projeto["id"], BOM)
    b = cria_efeito(plena, app, projeto["id"], SEGUNDO)
    aresta = liga(plena, projeto["id"], a["id"], b["id"])
    r = plena.put(
        f"/toc/ara/projetos/{projeto['id']}/arestas/{aresta['id']}/exame",
        json={"estado": "mais_ou_menos"},
    )
    assert r.status_code == 422
    assert valida_envelope_de_erro(r)["code"] == "INVALID_ARGUMENT"


def test_conector_e_exige_destino_unico_e_duas_arestas(plena, app):
    projeto = cria_ara(plena, app)
    a = cria_efeito(plena, app, projeto["id"], BOM)
    b = cria_efeito(plena, app, projeto["id"], SEGUNDO)
    c = cria_efeito(plena, app, projeto["id"], TERCEIRO)
    ac = liga(plena, projeto["id"], a["id"], c["id"])
    bc = liga(plena, projeto["id"], b["id"], c["id"])

    so_uma = plena.post(
        f"/toc/ara/projetos/{projeto['id']}/conectores", json={"arestas": [ac["id"]]}
    )
    assert so_uma.status_code == 409
    assert valida_envelope_de_erro(so_uma)["details"]["regra"] == "minimo_duas_arestas"

    r = plena.post(
        f"/toc/ara/projetos/{projeto['id']}/conectores",
        json={"arestas": [ac["id"], bc["id"]]},
    )
    conector = valida_contra_o_contrato(
        app, r, "POST", "/toc/ara/projetos/{projeto_id}/conectores"
    )
    assert conector["destino_id"] == c["id"]

    lido = plena.get(f"/toc/ara/projetos/{projeto['id']}").json()["conectores"][0]
    assert lido["leitura"] == f"Se {BOM} e {SEGUNDO}, então {TERCEIRO}"

    apagado = plena.delete(
        f"/toc/ara/projetos/{projeto['id']}/conectores/{conector['id']}"
    )
    assert apagado.status_code == 204
    assert plena.get(f"/toc/ara/projetos/{projeto['id']}").json()["conectores"] == []


# -- análise estrutural: a causa raiz candidata ------------------------------------------


def test_a_analise_aponta_a_causa_raiz_candidata_e_nao_conclui_no_empate(plena, app):
    """RN-12/RF-27: aponta como sugestão nomeada; empate NÃO vira conclusão automática."""
    projeto = cria_ara(plena, app)
    raiz = cria_efeito(plena, app, projeto["id"], "O processo de admissão não tem dono.")
    ude1 = cria_efeito(plena, app, projeto["id"], BOM)
    ude2 = cria_efeito(plena, app, projeto["id"], SEGUNDO)
    elo1 = liga(plena, projeto["id"], raiz["id"], ude1["id"])
    elo2 = liga(plena, projeto["id"], raiz["id"], ude2["id"])
    for alvo in (ude1, ude2):
        plena.post(f"/toc/ara/projetos/{projeto['id']}/nos/{alvo['id']}/ude", json={})

    r = plena.post(f"/toc/ara/projetos/{projeto['id']}/analises")
    corpo = valida_contra_o_contrato(
        app, r, "POST", "/toc/ara/projetos/{projeto_id}/analises"
    )
    assert corpo["causa_raiz_candidata"] == raiz["id"]
    assert corpo["causas_raiz_candidatas"] == [raiz["id"]]
    assert corpo["total_de_udes"] == 2
    assert corpo["udes_nao_alcancados"] == []
    # Na ORDEM DE CRIAÇÃO das arestas, que é a do agregado — resposta determinística,
    # sem reordenação escondida na borda (`analise.py:169` preserva a ordem do grafo).
    assert corpo["elos_nao_examinados"] == [elo1["id"], elo2["id"]]
    assert corpo["resumo"]["nos"] == 3


def test_a_analise_lista_ude_nao_alcancado_e_no_orfao(plena, app):
    """RF-28: a medida de quanto da dor percebida a árvore ainda NÃO explica."""
    projeto = cria_ara(plena, app)
    solto = cria_efeito(plena, app, projeto["id"], BOM)
    plena.post(f"/toc/ara/projetos/{projeto['id']}/nos/{solto['id']}/ude", json={})

    corpo = plena.post(f"/toc/ara/projetos/{projeto['id']}/analises").json()
    assert corpo["udes_nao_alcancados"] == [solto["id"]]
    assert corpo["orfaos"] == [solto["id"]]
    assert corpo["causa_raiz_candidata"] is None


def test_a_ara_de_outro_inquilino_nao_atravessa_a_fronteira(plena, app, outro_inquilino):
    projeto = cria_ara(plena, app)
    r = outro_inquilino.get(f"/toc/ara/projetos/{projeto['id']}")
    assert r.status_code == 404
    assert valida_envelope_de_erro(r)["code"] == "NOT_FOUND"


def test_projeto_ara_inexistente_responde_404(plena, app):
    r = plena.post(f"/toc/ara/projetos/{uuid4()}/analises")
    assert r.status_code == 404
    assert valida_envelope_de_erro(r)["code"] == "NOT_FOUND"
