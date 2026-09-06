"""A porta dos fundos do agregado: o núcleo genérico do M1 alcançando estado de ferramenta.

Siglas, uma vez neste arquivo: **M1** — Núcleo de Diagramas Lógicos · **M2** — Árvore da
Realidade Atual (ARA) · **M3** — Nuvem de Conflito (NC) · **UDE** — Efeito Indesejável ·
**TOC** — Teoria das Restrições · **DDD** — *Domain-Driven Design* (Design Orientado a
Domínio) · **RN** — regra de negócio · **HTTP** — *HyperText Transfer Protocol*.

**O defeito que este arquivo reproduz e depois trava.** As ferramentas M2 e M3 são raízes
de agregado por composição: `ProjetoARA` e `NuvemDeConflito` **contêm** um `Projeto` do M1
e acrescentam as invariantes da ferramenta — a topologia fixa de 5 entidades e 7 arestas
da nuvem (RN-01 da spec 007), o exame que nasce com todo elo da ARA (RF-22 da spec 005), o
arquivamento da ficha quando um UDE some (RF-05), o conector que nunca fica com referência
órfã (RN-11). Só que o `Projeto` que elas contêm é **a mesma linha de banco** que as rotas
genéricas de `/toc/projetos` abrem, e essas rotas carregam o `Projeto` cru, sem a raiz.

Duas portas para o mesmo estado, e as invariantes moram numa só. É o defeito clássico de
agregado com porta dos fundos, e é exatamente o que o DDD existe para impedir: **operação
só pela raiz do agregado**.

Cada teste aqui é uma tentativa de alcançar o estado de uma ferramenta pela porta genérica.
Nenhum deles afirma "a rota devolve 409" por gosto de código de erro: o que cada um mede é
que **o estado da ferramenta continua íntegro depois da tentativa** — a leitura pela raiz
responde, e responde a mesma coisa que antes.
"""
from __future__ import annotations

from uuid import uuid4

from .conftest import valida_envelope_de_erro

DILEMA_NOME = "Dilema da expansão da Instituição Horizonte"

#: Efeito Indesejável sintético que passa nos critérios formais (ADR 0006: persona e
#: enunciado fictícios, nunca dado real de pessoa).
UDE_BOM = "A evasão de estudantes aumenta a cada semestre na Instituição Horizonte"
UDE_OUTRO = "O corpo docente perde horas de preparo com retrabalho de matrícula"
UDE_TERCEIRO = "A reputação acadêmica da Instituição Horizonte cai entre os pares"


# -- utilitários ------------------------------------------------------------------------


def cria_nuvem(plena) -> dict:
    r = plena.post("/toc/nc/projetos", json={"nome": DILEMA_NOME})
    assert r.status_code == 201, r.text
    return r.json()


def abre_nuvem(plena, projeto_id) -> dict:
    r = plena.get(f"/toc/nc/projetos/{projeto_id}")
    assert r.status_code == 200, (
        f"a nuvem {projeto_id} deixou de abrir depois da tentativa pela porta genérica: "
        f"{r.status_code} {r.text}"
    )
    return r.json()


def cria_ara(plena, nome="Árvore da Instituição Horizonte") -> dict:
    r = plena.post("/toc/ara/projetos", json={"nome": nome})
    assert r.status_code == 201, r.text
    return r.json()


def abre_ara(plena, projeto_id) -> dict:
    r = plena.get(f"/toc/ara/projetos/{projeto_id}")
    assert r.status_code == 200, (
        f"a ARA {projeto_id} deixou de abrir depois da tentativa pela porta genérica: "
        f"{r.status_code} {r.text}"
    )
    return r.json()


def efeito(plena, projeto_id, titulo) -> dict:
    r = plena.post(f"/toc/ara/projetos/{projeto_id}/efeitos", json={"titulo": titulo})
    assert r.status_code == 201, r.text
    return r.json()


def recusa_de_porta_dos_fundos(resposta, *, onde: str) -> dict:
    """Toda tentativa pela porta genérica recusa com o MESMO código legível por máquina."""
    assert resposta.status_code == 409, (
        f"{onde}: a porta genérica NÃO recusou — respondeu {resposta.status_code} "
        f"{resposta.text}"
    )
    erro = valida_envelope_de_erro(resposta)
    assert erro["code"] == "AGGREGATE_ROOT_REQUIRED", (
        f"{onde}: recusou com {erro['code']!r}, e o contrato desta classe de recusa é "
        f"'AGGREGATE_ROOT_REQUIRED' — o cliente discrimina por código, nunca por mensagem"
    )
    assert erro["details"]["ferramenta"], f"{onde}: a recusa não diz de que ferramenta é"
    assert erro["details"]["raiz"], f"{onde}: a recusa não nomeia a raiz que é o caminho"
    return erro


# =======================================================================================
# M3 — Nuvem de Conflito: as 7 arestas nascem com a nuvem e não se destroem (RN-01)
# =======================================================================================


def test_a_porta_generica_nao_acrescenta_entidade_a_uma_nuvem(plena):
    nuvem = cria_nuvem(plena)

    r = plena.post(
        f"/toc/projetos/{nuvem['id']}/nos", json={"titulo": "Sexta entidade clandestina"}
    )

    recusa_de_porta_dos_fundos(r, onde="POST /toc/projetos/{id}/nos sobre nuvem")
    depois = abre_nuvem(plena, nuvem["id"])
    print(
        f"nuvem depois da tentativa: {len(depois['entidades'])} entidades, "
        f"{len(depois['arestas'])} arestas"
    )
    assert len(depois["entidades"]) == 5
    assert len(depois["arestas"]) == 7


def test_a_porta_generica_nao_exclui_entidade_de_uma_nuvem(plena):
    nuvem = cria_nuvem(plena)
    entidade_a = next(e for e in nuvem["entidades"] if e["papel"] == "A")

    r = plena.delete(f"/toc/projetos/{nuvem['id']}/nos/{entidade_a['no_id']}")

    recusa_de_porta_dos_fundos(r, onde="DELETE /toc/projetos/{id}/nos/{no_id} sobre nuvem")
    depois = abre_nuvem(plena, nuvem["id"])
    assert len(depois["entidades"]) == 5
    assert len(depois["arestas"]) == 7
    assert sorted(e["papel"] for e in depois["entidades"]) == ["A", "B", "C", "D", "D_PRIME"]


def test_a_porta_generica_nao_destroi_aresta_de_uma_nuvem(plena):
    """A reprodução limpa do crítico: mutilar a nuvem por baixo, aresta a aresta."""
    nuvem = cria_nuvem(plena)
    conflito = next(a for a in nuvem["arestas"] if a["chave"] == "D_D_PRIME")

    r = plena.delete(f"/toc/projetos/{nuvem['id']}/arestas/{conflito['aresta_id']}")

    recusa_de_porta_dos_fundos(
        r, onde="DELETE /toc/projetos/{id}/arestas/{aresta_id} sobre nuvem"
    )
    depois = abre_nuvem(plena, nuvem["id"])
    print(f"chaves depois da tentativa: {sorted(a['chave'] for a in depois['arestas'])}")
    assert sorted(a["chave"] for a in depois["arestas"]) == [
        "A_B", "A_C", "B_D", "C_D_PRIME", "D_C", "D_D_PRIME", "D_PRIME_B",
    ]


def test_a_porta_generica_nao_liga_aresta_nova_numa_nuvem(plena):
    nuvem = cria_nuvem(plena)
    papel = {e["papel"]: e["no_id"] for e in nuvem["entidades"]}

    r = plena.post(
        f"/toc/projetos/{nuvem['id']}/arestas",
        json={"origem_id": papel["A"], "destino_id": papel["D"]},
    )

    recusa_de_porta_dos_fundos(r, onde="POST /toc/projetos/{id}/arestas sobre nuvem")
    assert len(abre_nuvem(plena, nuvem["id"])["arestas"]) == 7


def test_a_porta_generica_nao_reescreve_o_texto_de_uma_entidade_da_nuvem(plena):
    """O texto das entidades é o que TODAS as sete leituras montam (RF-07)."""
    nuvem = cria_nuvem(plena)
    entidade_a = next(e for e in nuvem["entidades"] if e["papel"] == "A")

    r = plena.patch(
        f"/toc/projetos/{nuvem['id']}/nos/{entidade_a['no_id']}",
        json={"titulo": "Texto entrando por baixo da raiz"},
    )

    recusa_de_porta_dos_fundos(r, onde="PATCH /toc/projetos/{id}/nos/{no_id} sobre nuvem")
    depois = abre_nuvem(plena, nuvem["id"])
    atual = next(e for e in depois["entidades"] if e["papel"] == "A")
    assert atual["texto"] == entidade_a["texto"]


def test_a_porta_generica_nao_rotula_aresta_de_uma_nuvem(plena):
    nuvem = cria_nuvem(plena)
    aresta = next(a for a in nuvem["arestas"] if a["chave"] == "A_B")

    r = plena.patch(
        f"/toc/projetos/{nuvem['id']}/arestas/{aresta['aresta_id']}",
        json={"rotulo": "rótulo clandestino"},
    )

    recusa_de_porta_dos_fundos(
        r, onde="PATCH /toc/projetos/{id}/arestas/{aresta_id} sobre nuvem"
    )
    assert len(abre_nuvem(plena, nuvem["id"])["arestas"]) == 7


# =======================================================================================
# M2 — Árvore da Realidade Atual: as invariantes com a MESMA exposição
# =======================================================================================


def test_a_porta_generica_nao_cria_no_fora_do_tipo_efeito_numa_ara(plena):
    """F-15: todo nó da ARA é um `efeito`; "causa" é posição na cadeia, não tipo de nó.

    A rota genérica cria com o tipo padrão do M1 (`generico`) — e um nó de tipo estranho
    numa ARA é um nó que a análise estrutural conta e a ferramenta não sabe ler.
    """
    ara = cria_ara(plena)

    r = plena.post(f"/toc/projetos/{ara['id']}/nos", json={"titulo": UDE_BOM})

    recusa_de_porta_dos_fundos(r, onde="POST /toc/projetos/{id}/nos sobre ARA")
    depois = abre_ara(plena, ara["id"])
    tipos = sorted({n["tipo"] for n in depois["projeto"]["nos"]})
    print(f"tipos de nó na ARA depois da tentativa: {tipos}")
    assert tipos in ([], ["efeito"])


def test_a_porta_generica_nao_liga_elo_sem_exame_numa_ara(plena):
    """RF-22: todo elo da ARA nasce com um exame de suficiência — é dado, não anotação.

    `ProjetoARA.ligar` cria o `Exame`; `Projeto.ligar` não sabe que exame existe. Uma
    aresta criada pela porta genérica é um elo que a raiz nunca registrou.
    """
    ara = cria_ara(plena)
    a = efeito(plena, ara["id"], UDE_BOM)
    b = efeito(plena, ara["id"], UDE_OUTRO)

    r = plena.post(
        f"/toc/projetos/{ara['id']}/arestas",
        json={"origem_id": a["id"], "destino_id": b["id"]},
    )

    recusa_de_porta_dos_fundos(r, onde="POST /toc/projetos/{id}/arestas sobre ARA")
    assert abre_ara(plena, ara["id"])["elos"] == []


def test_a_porta_generica_nao_apaga_ude_sem_arquivar_a_ficha_numa_ara(plena):
    """RF-05: sumir com um UDE ARQUIVA ficha, pareceres e status, com evento.

    Pela porta genérica o nó some e a ficha fica pendurada num identificador que não
    existe mais — a ARA passa a listar um UDE sem nó.
    """
    ara = cria_ara(plena)
    no = efeito(plena, ara["id"], UDE_BOM)
    assert plena.post(f"/toc/ara/projetos/{ara['id']}/nos/{no['id']}/ude", json={}).status_code == 201

    r = plena.delete(f"/toc/projetos/{ara['id']}/nos/{no['id']}")

    recusa_de_porta_dos_fundos(r, onde="DELETE /toc/projetos/{id}/nos/{no_id} sobre ARA")
    depois = abre_ara(plena, ara["id"])
    nos = {n["id"] for n in depois["projeto"]["nos"]}
    orfaos = [u["no_id"] for u in depois["udes"] if u["no_id"] not in nos]
    print(f"UDEs órfãos depois da tentativa: {orfaos}")
    assert orfaos == []
    assert len(depois["udes"]) == 1


def test_a_porta_generica_nao_deixa_conector_com_aresta_fantasma_numa_ara(plena):
    """RN-11: aresta que some leva junto o conector que a citava — nunca referência órfã.

    `_soltar_das_conjuncoes` só roda por dentro da raiz. Pela porta genérica a aresta
    some e o conector continua apontando para ela, e aí `leitura_do_conector` procura uma
    aresta que não existe.
    """
    ara = cria_ara(plena)
    causa_um = efeito(plena, ara["id"], UDE_BOM)
    causa_dois = efeito(plena, ara["id"], UDE_OUTRO)
    destino = efeito(plena, ara["id"], UDE_TERCEIRO)
    elos = []
    for origem in (causa_um, causa_dois):
        r = plena.post(
            f"/toc/ara/projetos/{ara['id']}/arestas",
            json={"origem_id": origem["id"], "destino_id": destino["id"]},
        )
        assert r.status_code == 201, r.text
        elos.append(r.json())
    formado = plena.post(
        f"/toc/ara/projetos/{ara['id']}/conectores",
        json={"arestas": [e["id"] for e in elos]},
    )
    assert formado.status_code == 201, formado.text

    r = plena.delete(f"/toc/projetos/{ara['id']}/arestas/{elos[0]['id']}")

    recusa_de_porta_dos_fundos(
        r, onde="DELETE /toc/projetos/{id}/arestas/{aresta_id} sobre ARA"
    )
    depois = abre_ara(plena, ara["id"])
    vivas = {e["aresta_id"] for e in depois["elos"]}
    fantasmas = [
        a for c in depois["conectores"] for a in c["arestas"] if a not in vivas
    ]
    print(f"arestas fantasmas em conector depois da tentativa: {fantasmas}")
    assert fantasmas == []


def test_a_porta_generica_nao_reescreve_ude_sem_revalidar_numa_ara(plena):
    """RF-10: mudar o texto de um UDE REEXECUTA a validação formal — por isso a operação
    tem nome (`reformular`) e não é um `editar_no` qualquer.

    Pela porta genérica o veredito anterior fica pendurado sobre um texto que não é mais
    o dele.
    """
    ara = cria_ara(plena)
    no = efeito(plena, ara["id"], UDE_BOM)
    assert plena.post(f"/toc/ara/projetos/{ara['id']}/nos/{no['id']}/ude", json={}).status_code == 201
    antes = abre_ara(plena, ara["id"])["udes"][0]

    r = plena.patch(
        f"/toc/projetos/{ara['id']}/nos/{no['id']}", json={"titulo": "coisa ruim"}
    )

    recusa_de_porta_dos_fundos(r, onde="PATCH /toc/projetos/{id}/nos/{no_id} sobre ARA")
    depois = abre_ara(plena, ara["id"])["udes"][0]
    print(
        f"texto do UDE antes={antes['titulo']!r} depois={depois['titulo']!r}; "
        f"veredito antes={antes['validacao']['aprovado_nos_decidiveis']} "
        f"depois={depois['validacao']['aprovado_nos_decidiveis']}"
    )
    assert depois["titulo"] == antes["titulo"]
    assert depois["validacao"] == antes["validacao"]


# =======================================================================================
# O projeto genérico continua sendo do M1 — a trava não pode fechar a porta da frente
# =======================================================================================


def test_o_projeto_generico_continua_aceitando_no_e_aresta_pela_rota_do_m1(plena):
    """A trava é por FERRAMENTA, não por rota: o M1 genérico não perde nada."""
    projeto = plena.post("/toc/projetos", json={"nome": "Rascunho livre"}).json()
    a = plena.post(f"/toc/projetos/{projeto['id']}/nos", json={"titulo": UDE_BOM})
    b = plena.post(f"/toc/projetos/{projeto['id']}/nos", json={"titulo": UDE_OUTRO})
    assert (a.status_code, b.status_code) == (201, 201), (a.text, b.text)

    aresta = plena.post(
        f"/toc/projetos/{projeto['id']}/arestas",
        json={"origem_id": a.json()["id"], "destino_id": b.json()["id"]},
    )

    assert aresta.status_code == 201, aresta.text
    assert plena.delete(
        f"/toc/projetos/{projeto['id']}/arestas/{aresta.json()['id']}"
    ).status_code == 204
    assert plena.delete(
        f"/toc/projetos/{projeto['id']}/nos/{a.json()['id']}"
    ).status_code == 200


def test_excluir_e_restaurar_um_projeto_de_ferramenta_continua_pela_rota_generica(plena):
    """A trava é sobre o GRAFO, não sobre o ciclo de vida: a lixeira serve as três."""
    nuvem = cria_nuvem(plena)

    assert plena.delete(f"/toc/projetos/{nuvem['id']}").status_code == 200
    assert nuvem["id"] in [p["id"] for p in plena.get("/toc/projetos/lixeira").json()]
    assert plena.post(f"/toc/projetos/{nuvem['id']}/restaurar").status_code == 200
    assert len(abre_nuvem(plena, nuvem["id"])["arestas"]) == 7


def test_a_recusa_nao_confirma_existencia_de_projeto_de_outro_inquilino(plena, outro_inquilino):
    """A trava não pode virar oráculo: fora do inquilino a resposta continua 404."""
    nuvem = cria_nuvem(plena)

    r = outro_inquilino.post(
        f"/toc/projetos/{nuvem['id']}/nos", json={"titulo": "sonda"}
    )

    assert r.status_code == 404, r.text
    assert valida_envelope_de_erro(r)["code"] == "NOT_FOUND"
    assert outro_inquilino.post(
        f"/toc/projetos/{uuid4()}/nos", json={"titulo": "sonda"}
    ).status_code == 404
