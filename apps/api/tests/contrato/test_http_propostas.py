"""O laço da assistência fechado pelo caminho certo — a proposta que a interface confirma.

Siglas, uma vez neste arquivo: **APH** — Aplicação ↔ Harness (o padrão da fronteira) ·
**NC** — Nuvem de Conflito · **FSM** — máquina de estados finitos · **HTTP** —
*HyperText Transfer Protocol* · **TTL** — *Time To Live* (tempo de vida) · **RF/RI** —
requisito funcional / de interface.

**O defeito que este arquivo existe para fechar.** A pré-visualização da geração assistida
mostrava o diff e só oferecia "Recusar": não havia, em lugar nenhum da aplicação, caminho
para **aceitar** a proposta e ver a nuvem mudar. A ausência estava documentada ("quem
escreve é a proposta que atravessa a máquina de estados no servidor"), mas a rota que a
interface usaria para levar a proposta ao gate **não existia** — documentar a ausência é
descrever o buraco, não fechá-lo.

O caminho certo é o que a spec 006 e o Padrão APH mandam, e é o que estes testes fixam:
aceitar é **confirmar uma proposta de ação** que atravessa a FSM do servidor
(`proposed → awaiting_approval → confirmed → executing → executed`), com traço em todo
desfecho — inclusive na recusa (RI-04 da spec 006: recusa silenciosa é defeito).

**Escopo declarado** (para este arquivo não fingir cobrir o que não cobre): aqui mede-se a
superfície `/toc/propostas` sobre o repositório em memória — forma da resposta, ordem das
transições, recusa por capacidade e fronteira de inquilino. A prova de que a mudança
**sobrevive à recarga** exige banco de verdade e está em
`tests/integracao/test_propostas_no_postgres.py`.
"""
from __future__ import annotations

from uuid import uuid4

from .conftest import valida_contra_o_contrato, valida_envelope_de_erro

ACAO_DE_GERACAO = "toc.generate_conflict_cloud"

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


def gera(plena, app, projeto_id, narrativa=NARRATIVA):
    """A pré-visualização — a MESMA que a tela mostra em diff. Não aplica nada."""
    r = plena.post(f"/toc/nc/projetos/{projeto_id}/geracoes", json={"narrativa": narrativa})
    assert r.status_code == 200, r.text
    return valida_contra_o_contrato(app, r, "POST", "/toc/nc/projetos/{projeto_id}/geracoes")


def propoe(cliente, app, action_id, args, origem="ia"):
    return cliente.post(
        "/toc/propostas", json={"action_id": action_id, "args": args, "origem": origem}
    )


def decide(cliente, proposal_id, aprovado):
    return cliente.post(f"/toc/propostas/{proposal_id}/decisao", json={"aprovado": aprovado})


def propoe_a_geracao(plena, app, projeto_id, previa=None):
    previa = previa or gera(plena, app, projeto_id)
    r = propoe(
        plena,
        app,
        previa["action_id"],
        {"projeto_id": projeto_id, "narrativa": NARRATIVA, "resultado": previa["resultado"]},
    )
    assert r.status_code == 201, r.text
    return valida_contra_o_contrato(app, r, "POST", "/toc/propostas"), previa


# -- o laço inteiro ----------------------------------------------------------------------


def test_a_nuvem_so_muda_depois_da_confirmacao_e_a_proposta_atravessa_a_fsm(plena, app):
    """O laço que faltava: gerar → propor → **confirmar** → a nuvem mudou.

    Duas leituras da nuvem — antes de decidir e depois — respondem a pergunta que a tela
    fazia sem resposta. Antes: idêntica byte a byte à de antes de propor. Depois: com o
    texto da geração aplicado, escrito pelo executor da ação governada.
    """
    projeto = cria_nuvem(plena, app)
    antes = abre(plena, app, projeto["id"])

    proposta, previa = propoe_a_geracao(plena, app, projeto["id"])

    assert proposta["action_id"] == ACAO_DE_GERACAO
    assert proposta["risk"] == "confirm"
    assert proposta["requires_confirmation"] is True
    assert proposta["estado"] == "awaiting_approval", (
        "verbo mutador nasce proposta e ESPERA (P2, APH-5.2) — nascer confirmado seria o "
        "gate humano virando formalidade"
    )
    assert proposta["status"] is None
    assert abre(plena, app, projeto["id"]) == antes, (
        "propor não é escrever: a nuvem tem de continuar byte a byte igual até a decisão"
    )

    r = decide(plena, proposta["proposal_id"], True)
    assert r.status_code == 200, r.text
    decidida = valida_contra_o_contrato(
        app, r, "POST", "/toc/propostas/{proposal_id}/decisao"
    )

    depois = abre(plena, app, projeto["id"])
    print(
        f"proposta {decidida['proposal_id']}: {proposta['estado']} → {decidida['estado']}"
        f" · desfecho={decidida['status']} · {decidida['mensagem']}"
    )
    assert decidida["estado"] == "executed"
    assert decidida["status"] == "executed"
    assert depois != antes, "confirmar TEM de mudar a nuvem — é o laço que estava aberto"
    textos = {e["papel"]: e["texto"] for e in depois["entidades"]}
    propostos = previa["resultado"]["entidades"]
    assert textos == propostos, (
        f"o que a prévia mostrou não foi o que a confirmação escreveu: {textos} != {propostos}"
    )


def test_o_desfecho_da_confirmacao_deixa_traco_com_a_origem_e_a_proposta(plena, app):
    """APH-5.5 e RF-25 da spec 007: a escrita assistida é rastreável para sempre."""
    projeto = cria_nuvem(plena, app)
    proposta, _ = propoe_a_geracao(plena, app, projeto["id"])
    decide(plena, proposta["proposal_id"], True)

    linhas = plena.get("/aph/traco").json()
    minhas = [t for t in linhas if t["proposal_id"] == proposta["proposal_id"]]
    print(f"linhas de traço do inquilino: {len(linhas)}; desta proposta: {len(minhas)}")
    assert len(minhas) == 1
    assert minhas[0]["desfecho"] == "executed"
    assert minhas[0]["action_id"] == ACAO_DE_GERACAO
    assert minhas[0]["origem"] == "ia"


# -- recusar é de graça, e nunca é silenciosa --------------------------------------------


def test_recusar_no_gate_deixa_a_nuvem_intacta_e_ainda_assim_deixa_traco(plena, app):
    """RF-24 (nada aplicado) + RI-04 da spec 006 (recusa silenciosa é defeito)."""
    projeto = cria_nuvem(plena, app)
    antes = abre(plena, app, projeto["id"])
    proposta, _ = propoe_a_geracao(plena, app, projeto["id"])

    r = decide(plena, proposta["proposal_id"], False)

    assert r.status_code == 200, r.text
    corpo = valida_contra_o_contrato(app, r, "POST", "/toc/propostas/{proposal_id}/decisao")
    depois = abre(plena, app, projeto["id"])
    traco = [t for t in plena.get("/aph/traco").json() if t["proposal_id"] == proposta["proposal_id"]]
    print(f"recusa: estado={corpo['estado']} · traço={[t['desfecho'] for t in traco]}")
    assert corpo["estado"] == "denied"
    assert corpo["status"] == "denied"
    assert depois == antes, "recusar tem de deixar o projeto byte a byte intacto (RF-24)"
    assert [t["desfecho"] for t in traco] == ["denied"]


# -- a máquina de estados, pela borda ----------------------------------------------------


def test_confirmar_de_novo_devolve_o_mesmo_desfecho_sem_executar_duas_vezes(plena, app):
    """RF-16: decisão repetida é a mesma decisão — nunca um segundo efeito."""
    projeto = cria_nuvem(plena, app)
    proposta, _ = propoe_a_geracao(plena, app, projeto["id"])

    primeira = decide(plena, proposta["proposal_id"], True).json()
    depois_da_primeira = abre(plena, app, projeto["id"])
    segunda = decide(plena, proposta["proposal_id"], True)

    assert segunda.status_code == 200, segunda.text
    corpo = segunda.json()
    print(
        f"1ª: {primeira['status']} · 2ª: {corpo['status']} · "
        f"nuvem mudou entre as duas: {abre(plena, app, projeto['id']) != depois_da_primeira}"
    )
    assert corpo["status"] == primeira["status"] == "executed"
    assert abre(plena, app, projeto["id"]) == depois_da_primeira


def test_negar_o_que_ja_executou_e_transicao_invalida_com_o_codigo_do_a7(plena, app):
    """A FSM é do domínio e a borda a traduz: 409 `INVALID_TRANSITION` (§A.7)."""
    projeto = cria_nuvem(plena, app)
    proposta, _ = propoe_a_geracao(plena, app, projeto["id"])
    decide(plena, proposta["proposal_id"], True)

    r = decide(plena, proposta["proposal_id"], False)

    assert r.status_code == 409, r.text
    erro = valida_envelope_de_erro(r)
    print(f"transição recusada: {r.status_code} {erro['code']}")
    assert erro["code"] == "INVALID_TRANSITION"


def test_decisao_sem_o_booleano_obrigatorio_e_recusada_na_borda(plena, app):
    projeto = cria_nuvem(plena, app)
    proposta, _ = propoe_a_geracao(plena, app, projeto["id"])

    r = plena.post(f"/toc/propostas/{proposta['proposal_id']}/decisao", json={})

    assert r.status_code == 422, r.text
    assert valida_envelope_de_erro(r)["code"] == "INVALID_ARGUMENT"


# -- fronteira: inquilino, capacidade e esquema ------------------------------------------


def test_proposta_de_outro_inquilino_e_indistinguivel_de_inexistente(
    plena, outro_inquilino, app
):
    projeto = cria_nuvem(plena, app)
    antes = abre(plena, app, projeto["id"])
    proposta, _ = propoe_a_geracao(plena, app, projeto["id"])

    r = decide(outro_inquilino, proposta["proposal_id"], True)

    assert r.status_code == 404, r.text
    assert valida_envelope_de_erro(r)["code"] == "PROPOSAL_NOT_FOUND"
    # E a recusa não é só de resposta: a proposta continua **intocada** para quem é dono,
    # e a nuvem não foi escrita por quem não podia decidi-la.
    assert abre(plena, app, projeto["id"]) == antes
    assert decide(plena, proposta["proposal_id"], True).json()["status"] == "executed"


def test_quem_so_le_nao_consegue_nem_propor_e_a_acao_some_do_catalogo(
    plena, leitora, app
):
    """§B.7.3: ausência, nunca recusa visível — "existe e você não pode" vazaria o inventário."""
    projeto = cria_nuvem(plena, app)
    previa = gera(plena, app, projeto["id"])

    r = propoe(
        leitora,
        app,
        ACAO_DE_GERACAO,
        {"projeto_id": projeto["id"], "resultado": previa["resultado"]},
    )

    assert r.status_code == 404, r.text
    assert valida_envelope_de_erro(r)["code"] == "ACTION_NOT_FOUND"
    catalogo = [a["action_id"] for a in leitora.get("/aph/catalog").json()]
    print(f"ações visíveis para quem só lê: {len(catalogo)}; a mutadora está lá: "
          f"{ACAO_DE_GERACAO in catalogo}")
    assert ACAO_DE_GERACAO not in catalogo


def test_resultado_fora_do_esquema_nao_cria_proposta_nenhuma(plena, app):
    """RF-22: a validação acontece ANTES de a proposta existir — falha fechada."""
    projeto = cria_nuvem(plena, app)

    r = propoe(
        plena, app, ACAO_DE_GERACAO, {"projeto_id": projeto["id"], "resultado": {"versao": "9.9.9"}}
    )

    assert r.status_code == 400, r.text
    assert valida_envelope_de_erro(r)["code"] == "INVALID_ARGUMENT"


def test_acao_fora_do_catalogo_nao_existe(plena, app):
    r = propoe(plena, app, "toc.inventada", {"projeto_id": str(uuid4())})

    assert r.status_code == 404, r.text
    assert valida_envelope_de_erro(r)["code"] == "ACTION_NOT_FOUND"


def test_sem_identidade_nem_propor_nem_decidir(anonima, app):
    assert propoe(anonima, app, ACAO_DE_GERACAO, {}).status_code == 401
    assert decide(anonima, str(uuid4()), True).status_code == 401
