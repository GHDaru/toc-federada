"""O EMBARQUE inteiro — grant → introspecção HTTP de verdade → catálogo → ação → banco.

Siglas, uma vez neste arquivo: **APH** — Aplicação ↔ Harness (o padrão da fronteira) ·
**HTTP** — *HyperText Transfer Protocol* · **UDE** — Efeito Indesejável · **JSON** —
*JavaScript Object Notation* · **URL** — *Uniform Resource Locator* · **RF/RN** —
requisito funcional / regra de negócio · **ADR** — *Architecture Decision Record*.

## O buraco que este arquivo fecha

A identidade da aplicação vem da fundação: `POST {HOST_BASE_URL}/auth/introspect`, servidor
a servidor, com o grant no **corpo** e a credencial da aplicação no cabeçalho (§B.6.2). O
adaptador que faz isso é `infra/federacao/introspeccao.IntrospeccaoHttp`. Antes deste
arquivo, ele aparecia em **um** teste da suíte inteira —
`apps/api/tests/federacao/test_portas_da_federacao.py`, que só confere que a classe satisfaz a porta
(`isinstance` contra um `Protocol`), sem jamais fazer uma chamada. Todo o resto do embarque
era testado pelo lado NEGATIVO: `test_arranque_e_admissao.py` prova que, sem os parâmetros
do §B.4, nenhum embarque é aceito.

Resultado: **o caminho feliz do embarque não era percorrido por nenhum teste**. A porta de
entrada do produto federado — a única — dependia de código que a suíte nunca executava.

Aqui sobe uma **fundação de mentira** (`http.server` em porta local, sem rede externa) que
implementa `/auth/introspect` conforme o §B.6.3, e o caminho é percorrido inteiro:

```
POST /toc/embarque {"token": grant}          →  201 com sessão, tenant e capabilities
GET  /aph/catalog  (Bearer sessão)           →  o catálogo DERIVADO daquelas capabilities
POST /toc/propostas → decisão                →  o nó no PostgreSQL
```

E as três falhas fechadas que o §B.6 exige: grant inativo, credencial recusada (401) e
fundação fora do ar (5xx) — cada uma com o código estável que a norma nomeia.

Base sintética da **Instituição Horizonte** (ADR 0006). Marcado `integracao`: pulado com o
motivo quando o banco não responde.
"""
from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest
from fastapi.testclient import TestClient

from toc_api.http.app import criar_app

from .conftest import liberar_conexoes as _liberar

pytestmark = pytest.mark.integracao

CREDENCIAL = "ghd_credencial_da_aplicacao_de_teste"
GRANT_VALIDO = "grant-facilitadora-horizonte"
GRANT_INATIVO = "grant-ja-consumido"
UDE = "A taxa de evasão no primeiro semestre é de 22%."

#: A resposta do §B.6.3 para um grant ativo. Persona fictícia (ADR 0006).
IDENTIDADE_DA_FUNDACAO = {
    "active": True,
    "user": {"id": "usr-facilitadora", "name": "Facilitadora TOC"},
    "tenant_id": "inq-horizonte",
    "capabilities": ["toc:read", "toc:write"],
    "app_id": "toc-federada",
}


class _FundacaoDeMentira(BaseHTTPRequestHandler):
    """Implementa `POST /auth/introspect` — e nada mais, de propósito.

    Ela **confere a credencial da aplicação no cabeçalho** e **lê o grant do corpo**, que
    é a inversão do §B.6.2 posta à prova: se o adaptador mandasse o grant como bearer, esta
    fundação responderia 401 e o teste do caminho feliz cairia. É o oposto de um duplo
    complacente — ela é escrita para pegar exatamente o erro que a norma nomeia.
    """

    modo = "normal"  # `normal` · `credencial_recusada` · `fora_do_ar`
    recebidos: list[dict] = []

    def log_message(self, *args):  # silencia o log do http.server na saída do pytest
        return

    def do_POST(self):  # noqa: N802 - nome exigido por BaseHTTPRequestHandler
        tamanho = int(self.headers.get("Content-Length") or 0)
        corpo = json.loads(self.rfile.read(tamanho) or b"{}")
        _FundacaoDeMentira.recebidos.append(
            {
                "caminho": self.path,
                "authorization": self.headers.get("Authorization"),
                "corpo": corpo,
            }
        )
        if _FundacaoDeMentira.modo == "fora_do_ar":
            return self._responder(503, {"error": "indisponivel"})
        if self.path != "/auth/introspect":
            return self._responder(404, {"error": "rota inexistente"})
        if self.headers.get("Authorization") != f"Bearer {CREDENCIAL}":
            # §B.6.2: quem autentica a CHAMADA é a credencial da aplicação.
            return self._responder(401, {"error": "credencial da aplicação recusada"})
        if _FundacaoDeMentira.modo == "credencial_recusada":
            return self._responder(401, {"error": "credencial rotacionada"})
        if corpo.get("token") == GRANT_VALIDO:
            return self._responder(200, IDENTIDADE_DA_FUNDACAO)
        # §B.6.5: grant inexistente, vencido ou consumido respondem IGUAL — `active: false`.
        return self._responder(200, {"active": False})

    def _responder(self, status: int, corpo: dict) -> None:
        bruto = json.dumps(corpo).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(bruto)))
        self.end_headers()
        self.wfile.write(bruto)


@pytest.fixture()
def fundacao():
    """A fundação de mentira, de pé em `127.0.0.1` numa porta livre. Sem rede externa."""
    _FundacaoDeMentira.modo = "normal"
    _FundacaoDeMentira.recebidos = []
    servidor = HTTPServer(("127.0.0.1", 0), _FundacaoDeMentira)
    fio = threading.Thread(target=servidor.serve_forever, daemon=True)
    fio.start()
    try:
        yield servidor
    finally:
        servidor.shutdown()
        servidor.server_close()


@pytest.fixture()
def aplicacoes(url_postgres, esquema_migrado, fundacao):
    """Aplicações ADMITIDAS: os seis parâmetros do §B.4, com a fundação de mentira na base.

    Note o que **não** está aqui: `TOC_IDENTIDADES_FALSAS`. Este arquivo é o único da suíte
    que não usa o provedor de identidade de desenvolvimento — a identidade vem da
    introspecção de verdade, que é o que ele existe para exercitar.
    """
    porta = fundacao.server_address[1]
    abertas: list[TestClient] = []

    def abrir() -> TestClient:
        app = criar_app(
            {
                "DATABASE_URL": url_postgres,
                "TOC_DB_SCHEMA": esquema_migrado,
                "TOC_AMBIENTE": "teste",
                "HOST_ORIGIN": "https://app.exemplo",
                "HOST_BASE_URL": f"http://127.0.0.1:{porta}",
                "APP_ID": "toc-federada",
                "EMBED_URL": "https://toc.exemplo/embed",
                "TOC_APP_CREDENTIAL": CREDENCIAL,
            }
        )
        c = TestClient(app)
        _liberar(abertas)
        abertas.append(c)
        return c

    try:
        yield abrir
    finally:
        _liberar(abertas)


def embarcar(c: TestClient, grant: str = GRANT_VALIDO):
    return c.post("/toc/embarque", json={"token": grant})


# =======================================================================================
# O caminho feliz, inteiro
# =======================================================================================


def test_a_aplicacao_sobe_admitida_e_declara_a_admissao_no_saude(aplicacoes):
    """RF-04: com os seis parâmetros presentes, o serviço está **admitido** — e diz isso."""
    saude = aplicacoes().get("/saude")

    corpo = saude.json()
    print(f"\n/saude: admissao={corpo['admissao']!r} app_id={corpo['app_id']!r} "
          f"persistencia={corpo['persistencia']!r} identidade={corpo['identidade']!r}")
    assert corpo["admissao"] == "admitida"
    assert corpo["app_id"] == "toc-federada"
    assert corpo["persistencia"] == "postgres"
    # P7: a credencial da aplicação nunca sai daqui.
    assert CREDENCIAL not in saude.text


def test_o_grant_vira_sessao_pela_introspeccao_servidor_a_servidor(aplicacoes):
    """§B.6.2 medido no fio: grant no CORPO, credencial da aplicação no CABEÇALHO."""
    resposta = embarcar(aplicacoes())

    assert resposta.status_code == 201, resposta.text
    corpo = resposta.json()
    print(
        f"\nembarque: tenant={corpo['tenant_id']!r} usuario={corpo['usuario']} "
        f"capabilities={corpo['capabilities']}"
    )
    assert corpo["tenant_id"] == "inq-horizonte"
    assert corpo["usuario"] == {"id": "usr-facilitadora", "nome": "Facilitadora TOC"}
    assert sorted(corpo["capabilities"]) == ["toc:read", "toc:write"]
    assert corpo["sessao"] and corpo["sessao"] != GRANT_VALIDO, (
        "a sessão devolvida é o próprio grant — o grant sairia do servidor para o cliente"
    )

    chamada = _FundacaoDeMentira.recebidos[-1]
    print(f"o que a fundação recebeu: {chamada['caminho']} · corpo={chamada['corpo']}")
    assert chamada["caminho"] == "/auth/introspect"
    assert chamada["corpo"] == {"token": GRANT_VALIDO}, chamada["corpo"]
    assert chamada["authorization"] == f"Bearer {CREDENCIAL}", (
        "o grant viajou como bearer — §B.6.2 diz que quem autentica a chamada é a "
        "credencial da APLICAÇÃO, e o grant vai no corpo"
    )


def test_do_embarque_ate_o_no_gravado_no_postgres(aplicacoes):
    """A jornada inteira de quem chega pela fundação: embarcar, ver, propor, decidir, ler."""
    c = aplicacoes()
    sessao = embarcar(c).json()["sessao"]
    cabecalho = {"Authorization": f"Bearer {sessao}"}

    catalogo = c.get("/aph/catalog", headers=cabecalho)
    assert catalogo.status_code == 200, catalogo.text
    acoes = {a["action_id"] for a in catalogo.json()}
    print(f"\ncatálogo servido ao principal embarcado: {len(acoes)} ação(ões)")
    assert "toc.criar_nos" in acoes

    projeto = c.post("/toc/projetos", json={"nome": "Horizonte"}, headers=cabecalho)
    assert projeto.status_code == 201, projeto.text
    projeto_id = projeto.json()["id"]

    proposta = c.post(
        "/toc/propostas",
        headers=cabecalho,
        json={
            "action_id": "toc.criar_nos",
            "args": {"projeto_id": projeto_id, "nos": [{"titulo": UDE, "tipo": "ude"}]},
        },
    )
    assert proposta.status_code == 201, proposta.text
    decidida = c.post(
        f"/toc/propostas/{proposta.json()['proposal_id']}/decisao",
        headers=cabecalho,
        json={"aprovado": True},
    )
    assert decidida.json()["status"] == "executed", decidida.json()

    # Aplicação NOVA, embarque NOVO: o nó está no banco, não na memória do processo.
    outra = aplicacoes()
    nova_sessao = embarcar(outra).json()["sessao"]
    lida = outra.get(
        f"/toc/projetos/{projeto_id}", headers={"Authorization": f"Bearer {nova_sessao}"}
    )
    titulos = [n["titulo"] for n in lida.json()["nos"]]
    print(f"nó lido por outra aplicação, com outro embarque: {titulos}")
    assert titulos == [UDE]


def test_a_sessao_de_um_embarque_nao_serve_a_outra_aplicacao(aplicacoes):
    """O token de sessão é de processo — e a consequência é medida, não suposta.

    O embarque abre a sessão em `RegistroDeSessoesDeAplicacao`, que é memória (ADR 0011,
    §"o que fica de fora"). Este teste fixa a fronteira: quem tem a sessão de uma instância
    é **anônimo** para a outra, e anônimo tem catálogo vazio — nunca acesso parcial.
    """
    primeira = aplicacoes()
    sessao = embarcar(primeira).json()["sessao"]
    segunda = aplicacoes()

    resposta = segunda.get("/aph/catalog", headers={"Authorization": f"Bearer {sessao}"})

    print(f"\nsessão de outra instância no catálogo: {resposta.status_code} {resposta.text[:120]}")
    assert resposta.status_code == 401
    assert resposta.json()["error"]["code"] == "SESSAO_EXPIRADA"


# =======================================================================================
# As três falhas fechadas do §B.6 — cada uma com o código que a norma nomeia
# =======================================================================================


def test_grant_inativo_recebe_um_codigo_so_e_nenhum_oraculo(aplicacoes):
    """§B.6.5: inexistente, vencido e consumido respondem IGUAL — a resposta não diz qual."""
    resposta = embarcar(aplicacoes(), GRANT_INATIVO)

    print(f"\ngrant inativo: {resposta.status_code} {resposta.json()}")
    assert resposta.status_code == 401
    assert resposta.json()["error"]["code"] == "GRANT_INATIVO"
    texto = resposta.text.lower()
    for oraculo in ("expirado", "vencido", "consumido", "inexistente"):
        assert oraculo not in texto, f"a recusa entregou o oráculo {oraculo!r}"


def test_credencial_recusada_pela_fundacao_nao_vira_retry(aplicacoes):
    """RF-11: o 401 do hospedeiro é uniforme por desenho; tentar de novo é gastar tentativa.

    O que se mede aqui é o desfecho **e** a contagem: uma chamada por embarque, nunca duas.
    """
    c = aplicacoes()
    _FundacaoDeMentira.modo = "credencial_recusada"
    antes = len(_FundacaoDeMentira.recebidos)

    resposta = embarcar(c)

    chamadas = len(_FundacaoDeMentira.recebidos) - antes
    print(f"\ncredencial recusada: {resposta.status_code} {resposta.json()} · chamadas={chamadas}")
    assert resposta.status_code == 502
    assert resposta.json()["error"]["code"] == "CREDENCIAL_RECUSADA"
    assert chamadas == 1, f"{chamadas} chamadas à introspecção para UM embarque (RF-11)"


def test_fundacao_fora_do_ar_e_falha_fechada_e_nunca_presume_valido(aplicacoes):
    """RF-10: 5xx da fundação nega tudo — nunca cache de identidade "para não incomodar"."""
    c = aplicacoes()
    _FundacaoDeMentira.modo = "fora_do_ar"

    resposta = embarcar(c)

    print(f"\nfundação fora do ar: {resposta.status_code} {resposta.json()}")
    assert resposta.status_code == 503
    assert resposta.json()["error"]["code"] == "FUNDACAO_INDISPONIVEL"
    # E o catálogo continua fechado: sem identidade, nada é servido.
    assert c.get("/aph/catalog").json() == []


def test_o_grant_nunca_aparece_na_resposta_nem_no_erro(aplicacoes):
    """RNF-01: o grant não entra em log, span, exceção nem corpo de resposta."""
    c = aplicacoes()
    aceito = embarcar(c)
    _FundacaoDeMentira.modo = "fora_do_ar"
    recusado = embarcar(c)

    print(f"\nresposta aceita: {len(aceito.text)} byte(s) · recusada: {recusado.text}")
    assert GRANT_VALIDO not in aceito.text
    assert GRANT_VALIDO not in recusado.text
    assert CREDENCIAL not in aceito.text and CREDENCIAL not in recusado.text


def test_a_sessao_do_embarque_autentica_a_SUPERFICIE_INTEIRA_e_nao_so_o_aph(aplicacoes):
    """O defeito que este arquivo achou: havia DOIS resolvedores de identidade na borda.

    `http/aph.py::principal_de` procurava o portador em **duas** origens — as sessões
    abertas por `POST /toc/embarque` e o `ProvedorDeIdentidade` da composição.
    `http/dependencias.py::obter_principal`, que é quem autentica **todas** as rotas de
    produto (`/toc/projetos`, `/toc/ara`, `/toc/nc`, `/toc/arf`, `/toc/apr`, `/toc/at`,
    `/toc/snt`, `/toc/focalizacao`, `/toc/portabilidade`, `/toc/cadeia`, `/toc/propostas`),
    procurava em **uma** só: o provedor. A sessão emitida pelo embarque não estava lá.

    A consequência, medida antes da correção: o token que `POST /toc/embarque` devolve
    abria `/aph/catalog` (200) e era recusado por `POST /toc/projetos` com
    `401 UNAUTHENTICATED`. Como a interface manda esse mesmo token em toda chamada
    (`apps/web/src/api/cliente.ts:119`), a aplicação embarcada não alcançava rota nenhuma
    do produto fora da fronteira conversacional.

    Nenhum teste pegava porque nenhum atravessava as duas superfícies com a MESMA
    identidade: os testes de `/aph/*` usavam o token de desenvolvimento e os de `/toc/*`
    usavam `TOC_IDENTIDADES_FALSAS` — dois tokens, duas metades, e a junta no meio.
    """
    c = aplicacoes()
    sessao = embarcar(c).json()["sessao"]
    cabecalho = {"Authorization": f"Bearer {sessao}"}

    projeto = c.post("/toc/projetos", json={"nome": "Horizonte"}, headers=cabecalho)
    assert projeto.status_code == 201, projeto.text
    projeto_id = projeto.json()["id"]

    # Uma rota de cada roteador do produto, com a MESMA sessão do embarque.
    superficie = {
        "/aph/catalog": c.get("/aph/catalog", headers=cabecalho),
        "/toc/projetos": c.get("/toc/projetos", headers=cabecalho),
        "/toc/ara/projetos": c.post(
            "/toc/ara/projetos", json={"nome": "ARA"}, headers=cabecalho
        ),
        "/toc/nc/projetos": c.post(
            "/toc/nc/projetos", json={"nome": "NC"}, headers=cabecalho
        ),
        "/toc/arf/projetos": c.post(
            "/toc/arf/projetos", json={"nome": "ARF"}, headers=cabecalho
        ),
        "/toc/apr/projetos": c.post(
            "/toc/apr/projetos", json={"nome": "APR", "objetivo": "obj"}, headers=cabecalho
        ),
        "/toc/at/projetos": c.post(
            "/toc/at/projetos", json={"nome": "AT"}, headers=cabecalho
        ),
        "/toc/snt/projetos": c.post(
            "/toc/snt/projetos", json={"nome": "SnT", "meta_global": "meta"}, headers=cabecalho
        ),
        "/toc/focalizacao/analises": c.post(
            "/toc/focalizacao/analises",
            json={"nome": "Foco", "sistema": "sistema"},
            headers=cabecalho,
        ),
        "/toc/portabilidade/projetos": c.get(
            f"/toc/portabilidade/projetos/{projeto_id}", headers=cabecalho
        ),
        "/toc/cadeia": c.get(f"/toc/cadeia/{projeto_id}", headers=cabecalho),
    }

    codigos = {rota: r.status_code for rota, r in superficie.items()}
    print(f"\nsuperfície alcançada pela sessão do embarque: {codigos}")
    recusadas = {rota: c for rota, c in codigos.items() if c == 401}
    assert not recusadas, (
        f"a sessão emitida pelo embarque foi recusada em {sorted(recusadas)} — a borda tem "
        f"mais de um resolvedor de identidade e eles divergiram"
    )


def test_token_desconhecido_continua_recusado_na_superficie_inteira(aplicacoes):
    """A correção do defeito acima NÃO pode ter aberto a porta: o desconhecido continua fora.

    É a metade que um conserto apressado quebraria — passar a aceitar a sessão do embarque
    e, no caminho, aceitar qualquer coisa.
    """
    c = aplicacoes()
    embarcar(c)  # há UMA sessão válida aberta; o token abaixo não é ela
    cabecalho = {"Authorization": "Bearer nao-existe-esta-sessao"}

    codigos = {
        "/aph/catalog": c.get("/aph/catalog", headers=cabecalho).status_code,
        "/toc/projetos": c.get("/toc/projetos", headers=cabecalho).status_code,
        "/toc/propostas": c.post(
            "/toc/propostas",
            json={"action_id": "toc.listar_projetos", "args": {}},
            headers=cabecalho,
        ).status_code,
    }
    print(f"\ntoken desconhecido: {codigos}")
    assert set(codigos.values()) == {401}, codigos
