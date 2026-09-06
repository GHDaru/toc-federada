"""Toda mutação do M6 nasce com traço (spec 009, RNF-03; DoD 12; P5).

Siglas, uma vez neste arquivo: **M6** — Focalização · **OTel** — OpenTelemetry · **HTTP** —
*HyperText Transfer Protocol* · **RNF** — requisito não funcional · **DoD** — *Definition
of Done* (Definição de Pronto) · **ADR** — *Architecture Decision Record* (Registro de
Decisão Arquitetural) · **APH** — Aplicação ↔ Harness.

**Por que aqui e não em `tests/aplicacao/`.** O teste de aplicação mede o span de um caso
de uso montado à mão; este mede o que atravessa a **aplicação inteira**, da requisição
HTTP até o banco, com o rastreador que a composição escolheu. É a diferença entre "o caso
de uso abre um span" e "o pedido que a interface faz deixa traço".

O P5 diz "sem traço, não está pronta", e a DoD 12 nomeia as três mutações que não podem
passar caladas: `RestricaoRegistrada`, `PassoConcluido` e `CicloFechado`. Este arquivo
confere as três — e mais as outras seis do módulo, porque fechar três e deixar seis é
fechar o caso, não a classe.

**O que o span carrega e o que ele nunca carrega** (ADR 0006): grandeza e vocabulário —
passo, tipo de restrição, contagens, identificador de inquilino. Nunca a descrição da
restrição, a justificativa, a decisão ou a nota; e há um teste medindo justamente isso,
porque a regra que só existe na revisão é a regra que vaza na pressa.
"""
from __future__ import annotations

import json
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Iterator

import pytest
from fastapi.testclient import TestClient

from toc_api.http.app import criar_app

pytestmark = pytest.mark.integracao

AUTORA = "Facilitadora TOC"
SISTEMA = "Da inscrição do candidato à primeira aula assistida"
RESTRICAO = "Capacidade de conferência da secretaria acadêmica"
JUSTIFICATIVA = "a fila de matrículas só cresce nesta etapa, em todo período de entrada"
NOTA = "a secretaria gasta metade do tempo com matrículas incompletas"

#: As mutações do M6 e o span que cada uma tem de abrir. Escrita à mão de propósito, como
#: as listas dos portões: derivá-la do próprio código faria este teste concordar com quem
#: esquecesse o traço numa delas.
MUTACOES_QUE_TEM_DE_DEIXAR_TRACO = (
    "caso_de_uso.criar_analise_de_focalizacao",
    "caso_de_uso.registrar_restricao",
    "caso_de_uso.anotar_passo",
    "caso_de_uso.vincular_ferramenta",
    "caso_de_uso.concluir_passo",
    "caso_de_uso.reabrir_passo_anterior",
    "caso_de_uso.recomecar",
    "caso_de_uso.julgar_decisao_herdada",
    "caso_de_uso.editar_restricao",
)

IDENTIDADES = {
    "tok-traco-facilitadora": {
        "inquilino_id": "inq-horizonte",
        "usuario_id": "usr-facilitadora",
        "capabilities": ["toc:read", "toc:write"],
    },
}


@dataclass
class SpanEspiao:
    nome: str
    atributos: dict = field(default_factory=dict)

    def atributo(self, chave: str, valor) -> None:
        self.atributos[chave] = valor


@dataclass
class RastreadorEspiao:
    """Um rastreador que **conforma à porta** e guarda o que passou por ela.

    Não é um duplo do OpenTelemetry: é a mesma porta `Rastreador` do domínio, com o
    adaptador trocado. Trocar o adaptador é exatamente o que a arquitetura hexagonal
    existe para permitir — e é o que torna "toda mutação tem traço" mensurável sem subir
    coletor nenhum.
    """

    spans: list = field(default_factory=list)

    @contextmanager
    def span(self, nome: str, **atributos) -> Iterator[SpanEspiao]:
        s = SpanEspiao(nome=nome, atributos=dict(atributos))
        self.spans.append(s)
        yield s

    @property
    def nomes(self) -> list[str]:
        return [s.nome for s in self.spans]

    def de(self, nome: str) -> list[SpanEspiao]:
        return [s for s in self.spans if s.nome == nome]


@pytest.fixture()
def espiao_e_cliente(url_postgres, esquema_migrado):
    """A aplicação real sobre o PostgreSQL real, com o rastreador trocado na composição."""
    app = criar_app(
        {
            "DATABASE_URL": url_postgres,
            "TOC_DB_SCHEMA": esquema_migrado,
            "TOC_AMBIENTE": "teste",
            "TOC_IDENTIDADES_FALSAS": json.dumps(IDENTIDADES),
        }
    )
    espiao = RastreadorEspiao()
    app.state.composicao = type(app.state.composicao)(
        **{
            **{
                campo: getattr(app.state.composicao, campo)
                for campo in app.state.composicao.__dataclass_fields__
            },
            "rastreador": espiao,
        }
    )
    cliente = TestClient(app)
    cliente.headers["Authorization"] = "Bearer tok-traco-facilitadora"
    return espiao, cliente


def travessia_completa(cliente) -> str:
    """A jornada inteira pela borda — é ela que tem de deixar traço em cada mutação."""
    analise = cliente.post(
        "/toc/focalizacao/analises",
        json={"nome": "Fluxo de matrículas", "sistema": SISTEMA},
    ).json()
    projeto_id = analise["projeto"]["id"]

    ara = cliente.post("/toc/ara/projetos", json={"nome": "ARA do fluxo"}).json()
    cliente.post(
        f"/toc/focalizacao/analises/{projeto_id}/passos/identificar/vinculos",
        json={"ferramenta": "ara", "projeto_id": ara["id"]},
    )
    cliente.post(
        f"/toc/focalizacao/analises/{projeto_id}/restricao",
        json={
            "descricao": RESTRICAO,
            "tipo": "fisica",
            "justificativa": JUSTIFICATIVA,
            "autor": AUTORA,
        },
    )
    cliente.put(
        f"/toc/focalizacao/analises/{projeto_id}/restricao",
        json={"justificativa": JUSTIFICATIVA + " — medido em três períodos"},
    )
    cliente.post(
        f"/toc/focalizacao/analises/{projeto_id}/passos/identificar/notas",
        json={"texto": NOTA, "autor": AUTORA},
    )
    for passo, decisao in (
        ("identificar", "a restrição é a conferência da secretaria"),
        ("explorar", "priorizar matrículas com documentação completa"),
    ):
        cliente.post(
            f"/toc/focalizacao/analises/{projeto_id}/passos/{passo}/conclusao",
            json={"decisao": decisao, "autor": AUTORA},
        )
    cliente.post(
        f"/toc/focalizacao/analises/{projeto_id}/reaberturas",
        json={"justificativa": "a medição da fila mudou", "autor": AUTORA},
    )
    cliente.post(
        f"/toc/focalizacao/analises/{projeto_id}/passos/identificar/conclusao",
        json={"decisao": "a restrição continua sendo a secretaria", "autor": AUTORA},
    )
    for passo, decisao in (
        ("explorar", "priorizar documentação completa"),
        ("subordinar", "nenhuma turma abre antes da conferência"),
        ("elevar", "contratar duas pessoas"),
    ):
        cliente.post(
            f"/toc/focalizacao/analises/{projeto_id}/passos/{passo}/conclusao",
            json={"decisao": decisao, "autor": AUTORA},
        )
    recomecada = cliente.post(f"/toc/focalizacao/analises/{projeto_id}/recomecos").json()
    herdada = recomecada["jornada"]["heranca"][0]
    cliente.post(
        f"/toc/focalizacao/analises/{projeto_id}/heranca/{herdada['id']}/veredito",
        json={
            "veredito": "revogada",
            "justificativa": "a restrição migrou de etapa",
            "autor": AUTORA,
        },
    )
    return projeto_id


# ---------------------------------------------------------------------------------------
# DoD 12 — toda mutação nova com traço
# ---------------------------------------------------------------------------------------


def test_toda_mutacao_do_m6_deixa_traco(espiao_e_cliente):
    espiao, cliente = espiao_e_cliente
    travessia_completa(cliente)

    abertos = set(espiao.nomes)
    faltando = [n for n in MUTACOES_QUE_TEM_DE_DEIXAR_TRACO if n not in abertos]
    print(
        f"\nspans abertos na travessia: {len(espiao.spans)} · mutações do M6 exigidas: "
        f"{len(MUTACOES_QUE_TEM_DE_DEIXAR_TRACO)} · sem traço: {len(faltando)}"
    )
    assert faltando == [], f"mutação do M6 sem traço (P5): {faltando}"


def test_as_tres_mutacoes_nomeadas_pela_dod_carregam_o_estado_da_jornada(espiao_e_cliente):
    """`RestricaoRegistrada`, `PassoConcluido` e `CicloFechado` — as três da linha 12."""
    espiao, cliente = espiao_e_cliente
    travessia_completa(cliente)

    (registro,) = espiao.de("caso_de_uso.registrar_restricao")[:1]
    assert registro.atributos["toc.tipo_de_restricao"] == "fisica"
    assert registro.atributos["toc.tem_origem"] is False
    assert registro.atributos["toc.resultado"] == "ok"

    conclusoes = espiao.de("caso_de_uso.concluir_passo")
    assert [c.atributos["toc.passo"] for c in conclusoes][:2] == ["identificar", "explorar"]
    assert conclusoes[0].atributos["toc.passos_concluidos"] == 1

    (recomeco,) = espiao.de("caso_de_uso.recomecar")
    assert recomeco.atributos["toc.ciclo_fechado"] == 1
    assert recomeco.atributos["toc.ciclo_aberto"] == 2
    # Duas, e não três: `explorar` foi concluída duas vezes nesta travessia (houve uma
    # reabertura), e a herança leva a decisão VIGENTE de cada passo — não o histórico
    # inteiro dele. A regra que o grupo já substituiu não volta à mesa.
    assert recomeco.atributos["toc.herancas_pendentes"] == 2


def test_o_traco_carrega_o_inquilino_da_introspeccao(espiao_e_cliente):
    """RNF-03: o inquilino vem da identidade da fundação, nunca do corpo do pedido."""
    espiao, cliente = espiao_e_cliente
    travessia_completa(cliente)

    inquilinos = {
        s.atributos.get("toc.inquilino_id")
        for s in espiao.spans
        if s.nome.startswith("caso_de_uso.")
    }
    assert inquilinos == {"inq-horizonte"}


def test_a_recusa_tambem_deixa_traco_e_diz_o_erro(espiao_e_cliente):
    """"Traço de toda ação, inclusive recusas" — o span marca o erro e reergue."""
    espiao, cliente = espiao_e_cliente
    analise = cliente.post(
        "/toc/focalizacao/analises",
        json={"nome": "Fluxo de matrículas", "sistema": SISTEMA},
    ).json()

    recusada = cliente.post(
        f"/toc/focalizacao/analises/{analise['projeto']['id']}/passos/identificar/conclusao",
        json={"decisao": "seguimos assim", "autor": AUTORA},
    )

    assert recusada.status_code == 409
    (span,) = espiao.de("caso_de_uso.concluir_passo")
    assert span.atributos["toc.resultado"] == "erro"
    assert span.atributos["toc.erro"] == "PassoInvalido"
    assert span.atributos["toc.passo"] == "identificar"


# ---------------------------------------------------------------------------------------
# ADR 0006 — o span carrega grandeza, nunca texto de pessoa
# ---------------------------------------------------------------------------------------


def test_nenhum_texto_do_usuario_entra_no_traco(espiao_e_cliente):
    """A regra que só existe na revisão é a regra que vaza na pressa. Aqui ela é medida.

    O que se procura é o conteúdo que o grupo escreveu — descrição da restrição,
    justificativa, decisão de passo e nota. Nenhum deles pode aparecer em atributo nenhum
    de span nenhum: o traço descreve **o que aconteceu**, não **o que se escreveu**.
    """
    espiao, cliente = espiao_e_cliente
    travessia_completa(cliente)

    textos_do_usuario = [
        RESTRICAO,
        JUSTIFICATIVA,
        NOTA,
        "a restrição é a conferência da secretaria",
        "priorizar matrículas com documentação completa",
        "a medição da fila mudou",
        "a restrição migrou de etapa",
        AUTORA,
    ]
    vazamentos = [
        (s.nome, chave, valor)
        for s in espiao.spans
        for chave, valor in s.atributos.items()
        if isinstance(valor, str)
        for texto in textos_do_usuario
        if texto in valor
    ]
    print(
        f"atributos de span examinados: "
        f"{sum(len(s.atributos) for s in espiao.spans)} · textos de usuário procurados: "
        f"{len(textos_do_usuario)} · vazamentos: {len(vazamentos)}"
    )
    assert vazamentos == [], f"texto de pessoa no traço (ADR 0006): {vazamentos}"
