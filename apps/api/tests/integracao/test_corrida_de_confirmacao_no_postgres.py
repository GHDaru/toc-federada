"""O gate humano multiplicado por uma corrida — a proposta de ação sem trava.

Siglas, uma vez neste arquivo: **APH** — Aplicação ↔ Harness (o padrão da fronteira) ·
**FSM** — máquina de estados finitos · **HTTP** — *HyperText Transfer Protocol* · **M1** —
Núcleo de Diagramas Lógicos · **SQL** — *Structured Query Language* · **TTL** — *Time To
Live* (tempo de vida).

## O defeito que este arquivo reproduz

A trava otimista do ciclo anterior fechou a escrita de **projeto** (`versao_lida` +
`UPDATE … WHERE versao = :versao_lida`) e deixou a **proposta de ação** de fora: quem a
instalou declarou a lacuna como pendência em vez de dizer que estava resolvida, e o ataque
confirmou que a pendência era real.

`DecidirProposta.executar` fazia, nesta ordem: `obter` (lê a linha) → confirma na FSM **em
memória** → executa os efeitos → `salvar` (um `INSERT … ON CONFLICT DO UPDATE`
incondicional). Nenhum passo consulta o estado que está no banco no instante da escrita, e
o `salvar` só acontece **depois** do efeito. Logo N confirmações simultâneas da MESMA
proposta leem todas `awaiting_approval`, atravessam N cópias distintas do agregado, e
executam N vezes. A FSM guardava o **objeto**; havia N objetos para uma linha.

Reprodução do crítico independente, colada: proposta `toc.criar_nos` com 30 alvos em
`awaiting_approval`; oito confirmações simultâneas do MESMO `proposal_id` com a MESMA
chave de idempotência devolveram `{200: 8}`, gravaram 49 nós para 30 pedidos, com 13
títulos repetidos e **oito linhas de traço para uma proposta só**. Estável em oito
repetições.

É grave por dois motivos somados: quebra a deduplicação que o próprio padrão exige
(APH-5.3 — `idempotency_key` com deduplicação REAL) e multiplica por uma corrida o portão
humano, que o método trata como inegociável.

## Por que estes testes são concorrentes de verdade e ainda assim determinísticos

Mesma disciplina de `test_concorrencia_no_postgres.py`: uma `threading.Barrier` garante a
ordem `R1…Rn · W1…Wn` (todas leem antes de qualquer uma decidir), que é a definição da
corrida; cada fio monta a **sua própria aplicação** sobre o mesmo esquema migrado, com
motor, sessão e repositório próprios — o equivalente a processos à parte. PostgreSQL real,
nunca SQLite (brief §1).

Base sintética (ADR 0006): Instituição Horizonte, personas fictícias, nenhum dado de
pessoa real.
"""
from __future__ import annotations

import json
import threading
from collections import Counter

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text

from toc_api.http.app import criar_app

pytestmark = pytest.mark.integracao

#: Quantas pessoas (ou quantos cliques) confirmam ao mesmo tempo. É o número da reprodução
#: do crítico: oito confirmações simultâneas devolveram `{200: 8}`.
QUANTAS = 8

#: Quantos alvos o lote carrega. Também da reprodução: 30 pedidos viraram 49 nós.
ALVOS = 30

ACAO_DE_LOTE = "toc.criar_nos"

IDENTIDADES = {
    "tok-corrida-facilitadora": {
        "inquilino_id": "inq-horizonte",
        "usuario_id": "usr-facilitadora",
        "capabilities": ["toc:read", "toc:write"],
        "app_id": "toc-federada",
    }
}


def cliente(url: str, esquema: str) -> TestClient:
    """Uma aplicação NOVA — motor, sessão e repositórios próprios, como outro processo."""
    app = criar_app(
        {
            "DATABASE_URL": url,
            "TOC_DB_SCHEMA": esquema,
            "TOC_AMBIENTE": "teste",
            "TOC_IDENTIDADES_FALSAS": json.dumps(IDENTIDADES),
        }
    )
    c = TestClient(app)
    c.headers["Authorization"] = "Bearer tok-corrida-facilitadora"
    return c


def _titulos(indice_do_lote: int = 0) -> list[dict[str, str]]:
    """Os 30 alvos, com título único por posição — repetição no banco é dado duplicado."""
    return [
        {"titulo": f"Efeito indesejável nº {i:02d} da Instituição Horizonte", "tipo": "ude"}
        for i in range(ALVOS)
    ]


def _propoe(c: TestClient, projeto_id: str) -> dict:
    resposta = c.post(
        "/toc/propostas",
        json={
            "action_id": ACAO_DE_LOTE,
            "args": {"projeto_id": projeto_id, "nos": _titulos()},
        },
    )
    assert resposta.status_code == 201, resposta.text
    corpo = resposta.json()
    assert corpo["estado"] == "awaiting_approval", corpo
    assert corpo["quantidade_de_alvos"] == ALVOS, corpo
    return corpo


def _em_paralelo(quantos: int, trabalho):
    """Roda `trabalho(i, barreira)` em `quantos` fios; todos leem antes de qualquer decidir."""
    barreira = threading.Barrier(quantos)
    resultados: list[tuple[str, object] | None] = [None] * quantos

    def corre(i: int) -> None:
        try:
            resultados[i] = ("ok", trabalho(i, barreira))
        except BaseException as erro:  # noqa: BLE001 - o teste classifica depois
            resultados[i] = ("erro", erro)

    fios = [threading.Thread(target=corre, args=(i,)) for i in range(quantos)]
    for fio in fios:
        fio.start()
    for fio in fios:
        fio.join(timeout=120)
    assert all(r is not None for r in resultados), "algum fio não terminou em 120s"
    return resultados  # type: ignore[return-value]


def _nos_do_projeto(c: TestClient, projeto_id: str) -> list[dict]:
    resposta = c.get(f"/toc/projetos/{projeto_id}")
    assert resposta.status_code == 200, resposta.text
    return resposta.json()["nos"]


def _traco(c: TestClient, proposal_id: str) -> list[dict]:
    resposta = c.get("/aph/traco")
    assert resposta.status_code == 200, resposta.text
    return [t for t in resposta.json() if t["proposal_id"] == proposal_id]


def _execucoes_no_banco(url: str, esquema: str, proposal_id: str) -> tuple[str, int]:
    """O que a LINHA diz, e não o que o agregado em memória acha — estado e `execucoes`."""
    motor = create_engine(url)
    with motor.connect() as conexao:
        linha = conexao.execute(
            text(
                f'select estado, execucoes from "{esquema}".proposta_de_acao '
                "where proposal_id = :p"
            ),
            {"p": proposal_id},
        ).first()
    motor.dispose()
    assert linha is not None, "a proposta não está no banco"
    return (linha.estado, linha.execucoes)


# -- a reprodução do crítico, com a chave de idempotência do APH-5.3 ---------------------


def test_oito_confirmacoes_com_a_mesma_chave_executam_uma_vez_so(
    url_postgres, esquema_migrado
):
    """APH-5.3: a mesma chave produz **uma** execução e quantas respostas idênticas pedirem.

    A reprodução colada do crítico: `{200: 8}`, 49 nós para 30 pedidos, 13 títulos
    repetidos, oito linhas de traço. O invariante que a corrigi tem de sustentar são
    quatro números ao mesmo tempo — nós no banco, títulos distintos, linhas de traço e o
    contador `execucoes` da própria linha.
    """
    primeira = cliente(url_postgres, esquema_migrado)
    projeto = primeira.post("/toc/projetos", json={"nome": "Horizonte — árvore"}).json()
    proposta = _propoe(primeira, projeto["id"])
    chave = "idem-0e6f9d5c-uma-decisao-humana"

    def decide(i: int, barreira: threading.Barrier):
        c = cliente(url_postgres, esquema_migrado)
        barreira.wait(timeout=120)  # todas leram a mesma proposta antes de qualquer decidir
        r = c.post(
            f"/toc/propostas/{proposta['proposal_id']}/decisao",
            json={"aprovado": True, "idempotency_key": chave},
        )
        return (r.status_code, r.json())

    resultados = _em_paralelo(QUANTAS, decide)
    erros = [e for estado, e in resultados if estado == "erro"]
    assert not erros, [f"{type(e).__name__}: {e}" for e in erros]
    respostas = [valor for _, valor in resultados]

    codigos = Counter(codigo for codigo, _ in respostas)
    nos = _nos_do_projeto(primeira, projeto["id"])
    titulos = [n["titulo"] for n in nos]
    traco = _traco(primeira, proposta["proposal_id"])
    estado, execucoes = _execucoes_no_banco(
        url_postgres, esquema_migrado, proposta["proposal_id"]
    )
    print(
        f"\ncorrida de confirmação · chave única · códigos {dict(codigos)} · "
        f"nós no banco {len(nos)} para {ALVOS} pedidos · títulos repetidos "
        f"{len(titulos) - len(set(titulos))} · linhas de traço {len(traco)} · "
        f"linha no banco: estado={estado} execucoes={execucoes}"
    )

    assert len(nos) == ALVOS, (
        f"{len(nos)} nós no banco para {ALVOS} pedidos — a confirmação executou mais de "
        "uma vez"
    )
    assert len(set(titulos)) == ALVOS, (
        f"{len(titulos) - len(set(titulos))} título(s) repetido(s): o mesmo alvo foi "
        "criado mais de uma vez"
    )
    assert len(traco) == 1, (
        f"{len(traco)} linha(s) de traço para UMA proposta — a auditoria conta execuções "
        "que a pessoa não autorizou"
    )
    assert execucoes == 1, f"o contador de execuções da linha está em {execucoes}"
    assert estado == "executed", estado

    # A outra metade do APH-5.3: **quantas respostas idênticas forem pedidas**.
    assert set(codigos) == {200}, dict(codigos)
    corpos = [corpo for _, corpo in respostas]
    referencia = corpos[0]
    assert all(corpo == referencia for corpo in corpos), (
        "a mesma chave devolveu respostas DIFERENTES — a deduplicação do APH-5.3 exige "
        "a mesma resposta, não só uma execução"
    )
    assert referencia["status"] == "executed", referencia
    assert len(referencia["outcomes"]) == ALVOS, referencia


# -- a mesma corrida SEM chave: quem perde tem de saber que perdeu -----------------------


def test_oito_confirmacoes_sem_chave_executam_uma_e_recusam_as_outras(
    url_postgres, esquema_migrado
):
    """Sem `idempotency_key` não há a quem devolver resposta idêntica — mas há FSM.

    A segunda confirmação encontra a proposta fora de `awaiting_approval` e recebe o
    código que o §A.7 nomeia para isso (`INVALID_TRANSITION`, 409). O que **não** pode
    acontecer é o que acontecia: oito `200` e o efeito repetido.
    """
    primeira = cliente(url_postgres, esquema_migrado)
    projeto = primeira.post("/toc/projetos", json={"nome": "Horizonte — árvore"}).json()
    proposta = _propoe(primeira, projeto["id"])

    def decide(i: int, barreira: threading.Barrier):
        c = cliente(url_postgres, esquema_migrado)
        barreira.wait(timeout=120)
        r = c.post(
            f"/toc/propostas/{proposta['proposal_id']}/decisao", json={"aprovado": True}
        )
        return (r.status_code, r.json())

    resultados = _em_paralelo(QUANTAS, decide)
    erros = [e for estado, e in resultados if estado == "erro"]
    assert not erros, [f"{type(e).__name__}: {e}" for e in erros]
    respostas = [valor for _, valor in resultados]
    codigos = Counter(codigo for codigo, _ in respostas)

    nos = _nos_do_projeto(primeira, projeto["id"])
    traco = _traco(primeira, proposta["proposal_id"])
    print(
        f"\ncorrida de confirmação · sem chave · códigos {dict(codigos)} · "
        f"nós no banco {len(nos)} · linhas de traço {len(traco)}"
    )

    # O invariante NÃO é "exatamente um 200": um fio que chegue depois do commit do
    # vencedor lê uma proposta já terminal e recebe o desfecho original pela RF-16, que é
    # comportamento correto e não corrida. O invariante é que houve **uma execução** e que
    # todo `200` fala dela.
    assert len(nos) == ALVOS, f"{len(nos)} nós no banco para {ALVOS} pedidos"
    assert len(traco) == 1, f"{len(traco)} linha(s) de traço para UMA proposta"
    aceitas = [corpo for codigo, corpo in respostas if codigo == 200]
    assert aceitas, dict(codigos)
    assert all(corpo == aceitas[0] for corpo in aceitas), (
        "duas confirmações aceitas com desfechos DIFERENTES — houve mais de uma execução"
    )
    assert aceitas[0]["status"] == "executed", aceitas[0]

    recusas = [(codigo, corpo) for codigo, corpo in respostas if codigo != 200]
    assert recusas, (
        "nenhuma confirmação foi recusada: com oito fios e uma barreira, ao menos um "
        "perde a corrida — se todos passaram, a reserva não está serializando"
    )
    assert all(codigo == 409 for codigo, _ in recusas), dict(codigos)
    assert all(
        corpo["error"]["code"] == "INVALID_TRANSITION" for _, corpo in recusas
    ), [corpo.get("error", corpo) for _, corpo in recusas]


# -- a CLASSE: recusar também é decisão, e também é escrita ------------------------------


def test_oito_recusas_simultaneas_deixam_um_unico_traco(url_postgres, esquema_migrado):
    """`negar` grava e registra traço pelo mesmo caminho sem trava — logo tem o defeito.

    Fechar só a confirmação seria fechar o caso e não a classe: oito recusas simultâneas
    produziriam oito linhas de traço `denied` para uma decisão só, e a auditoria passaria
    a contar recusas que ninguém deu.
    """
    primeira = cliente(url_postgres, esquema_migrado)
    projeto = primeira.post("/toc/projetos", json={"nome": "Horizonte — árvore"}).json()
    proposta = _propoe(primeira, projeto["id"])

    def decide(i: int, barreira: threading.Barrier):
        c = cliente(url_postgres, esquema_migrado)
        barreira.wait(timeout=120)
        r = c.post(
            f"/toc/propostas/{proposta['proposal_id']}/decisao", json={"aprovado": False}
        )
        return (r.status_code, r.json())

    resultados = _em_paralelo(QUANTAS, decide)
    erros = [e for estado, e in resultados if estado == "erro"]
    assert not erros, [f"{type(e).__name__}: {e}" for e in erros]
    respostas = [valor for _, valor in resultados]
    codigos = Counter(codigo for codigo, _ in respostas)

    nos = _nos_do_projeto(primeira, projeto["id"])
    traco = _traco(primeira, proposta["proposal_id"])
    print(
        f"\ncorrida de recusa · códigos {dict(codigos)} · nós no banco {len(nos)} · "
        f"linhas de traço {[t['desfecho'] for t in traco]}"
    )

    assert len(nos) == 0, "recusar não escreve nada (RF-24)"
    assert len(traco) == 1, (
        f"{len(traco)} linha(s) de traço para UMA recusa — a auditoria conta decisões que "
        "não houve"
    )
    assert traco[0]["desfecho"] == "denied", traco

    aceitas = [corpo for codigo, corpo in respostas if codigo == 200]
    assert aceitas and all(corpo == aceitas[0] for corpo in aceitas), dict(codigos)
    assert aceitas[0]["status"] == "denied", aceitas[0]
    assert all(
        codigo == 409 and corpo["error"]["code"] == "INVALID_TRANSITION"
        for codigo, corpo in respostas
        if codigo != 200
    ), dict(codigos)
