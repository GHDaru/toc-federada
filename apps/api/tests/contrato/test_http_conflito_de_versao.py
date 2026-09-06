"""Quem perde a corrida SABE que perdeu — a forma da resposta, sem banco.

Siglas, uma vez neste arquivo: **HTTP** — *HyperText Transfer Protocol* · **APH** —
Aplicação ↔ Harness · **M1** — Núcleo de Diagramas Lógicos · **ARA** — Árvore da Realidade
Atual · **NC** — Nuvem de Conflito.

A prova de que a trava otimista funciona **contra o PostgreSQL de verdade** é
`tests/integracao/test_concorrencia_no_postgres.py`, com 20 escritas concorrentes. Este
arquivo prova a outra metade, que aquele não consegue provar de forma determinística: o
**contrato da recusa** — status, código estável do §A.7 do Anexo A e os dois números que
o cliente usa para se recuperar sozinho.

E a corrida aqui é real, não uma exceção levantada à mão: `RepositorioComEscritaAlheia`
grava a alteração de OUTRA pessoa entre o carregar e o gravar do pedido em curso, e quem
recusa é o adaptador em memória, com a mesma regra que o adaptador SQL tem no
`UPDATE … WHERE versao = :versao_lida`. Um teste que levantasse `ConflitoDeVersao` à mão
provaria o tradutor e nada mais — e continuaria verde no dia em que a trava sumisse.

Base sintética (ADR 0006): Instituição Horizonte, papéis, nenhum nome de pessoa.
"""
from __future__ import annotations

import dataclasses
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from toc_api.dominio.erros import ConflitoDeVersao
from toc_api.dominio.nuvem import ChaveDaAresta
from toc_api.http.app import criar_app

from .conftest import AMBIENTE, TOKEN_PLENO, valida_envelope_de_erro

T_OUTRA = datetime(2026, 9, 6, 12, 0, tzinfo=timezone.utc)

UDE = "A evasão de estudantes aumenta a cada semestre na Instituição Horizonte"
DILEMA = "Dilema da expansão da Instituição Horizonte"


class RepositorioComEscritaAlheia:
    """Enrola o repositório real e faz OUTRA pessoa gravar no meio do pedido em curso.

    É a janela exata da perda de atualização: o pedido já carregou o agregado (versão N) e
    ainda não gravou; a outra pessoa grava (versão N+1); o pedido tenta gravar a partir da
    N. Sem trava, o retrato do pedido apagava o trabalho dela em silêncio.

    `armar_uma_vez()` deixa a próxima gravação — e só ela — encontrar a janela aberta.
    """

    def __init__(self, real) -> None:
        self._real = real
        self._armado: str | None = None

    def armar_uma_vez(self, porta: str) -> None:
        self._armado = porta

    # -- leitura: passa direto ----------------------------------------------------
    def obter(self, *args, **kw):
        return self._real.obter(*args, **kw)

    def listar(self, *args, **kw):
        return self._real.listar(*args, **kw)

    def obter_ara(self, *args, **kw):
        return self._real.obter_ara(*args, **kw)

    def obter_nuvem(self, *args, **kw):
        return self._real.obter_nuvem(*args, **kw)

    # -- escrita: a janela --------------------------------------------------------
    def salvar(self, projeto) -> None:
        self._escrita_alheia("salvar", projeto)
        self._real.salvar(projeto)

    def salvar_ara(self, ara) -> None:
        self._escrita_alheia("salvar_ara", ara.projeto)
        self._real.salvar_ara(ara)

    def salvar_nuvem(self, nuvem) -> None:
        self._escrita_alheia("salvar_nuvem", nuvem.projeto)
        self._real.salvar_nuvem(nuvem)

    def _escrita_alheia(self, porta: str, projeto) -> None:
        if self._armado != porta:
            return
        self._armado = None
        dono = projeto.dono
        if porta == "salvar_ara":
            alheio = self._real.obter_ara(dono.inquilino_id, projeto.id)
            alheio.adicionar_efeito(titulo=f"{UDE} — pela outra facilitadora", em=T_OUTRA)
            self._real.salvar_ara(alheio)
        elif porta == "salvar_nuvem":
            alheio = self._real.obter_nuvem(dono.inquilino_id, projeto.id)
            alheio.registrar_premissa(
                ChaveDaAresta.A_B, "Premissa escrita pela outra facilitadora", em=T_OUTRA
            )
            self._real.salvar_nuvem(alheio)
        else:
            alheio = self._real.obter(dono.inquilino_id, projeto.id)
            alheio.renomear("Nome que a outra facilitadora gravou antes", em=T_OUTRA)
            self._real.salvar(alheio)


@pytest.fixture()
def app_com_corrida():
    """A aplicação de contrato, com o repositório enrolado pela janela da corrida."""
    app = criar_app(dict(AMBIENTE))
    composicao = app.state.composicao
    enrolado = RepositorioComEscritaAlheia(composicao.persistencia.projetos)
    app.state.composicao = dataclasses.replace(
        composicao,
        persistencia=dataclasses.replace(composicao.persistencia, projetos=enrolado),
    )
    return app, enrolado


@pytest.fixture()
def plena_com_corrida(app_com_corrida):
    app, enrolado = app_com_corrida
    cliente = TestClient(app)
    cliente.headers["Authorization"] = f"Bearer {TOKEN_PLENO}"
    return cliente, enrolado


def confere_o_envelope(resposta) -> dict:
    """O contrato inteiro da recusa, numa função só — usada pelas três ferramentas."""
    assert resposta.status_code == 409, resposta.text
    erro = valida_envelope_de_erro(resposta)
    assert erro["code"] == "VERSION_CONFLICT"
    detalhes = erro["details"]
    assert isinstance(detalhes["versao_lida"], int)
    assert isinstance(detalhes["versao_atual"], int)
    assert detalhes["versao_atual"] > detalhes["versao_lida"], detalhes
    # P7: nada de cadeia de conexão, credencial ou texto de outra pessoa na mensagem.
    assert "postgresql" not in erro["message"]
    return detalhes


def test_o_m1_recusa_a_escrita_que_partiu_de_versao_velha(plena_com_corrida):
    plena, enrolado = plena_com_corrida
    projeto = plena.post("/toc/projetos", json={"nome": "Horizonte — diagrama"}).json()

    enrolado.armar_uma_vez("salvar")
    resposta = plena.post(
        f"/toc/projetos/{projeto['id']}/nos", json={"titulo": "Os formulários chegam incompletos."}
    )

    confere_o_envelope(resposta)
    depois = plena.get(f"/toc/projetos/{projeto['id']}").json()
    assert depois["nos"] == [], "a escrita recusada não pode ter efeito"
    assert depois["nome"] == "Nome que a outra facilitadora gravou antes"


def test_a_ara_recusa_a_escrita_que_partiu_de_versao_velha(plena_com_corrida):
    plena, enrolado = plena_com_corrida
    projeto = plena.post("/toc/ara/projetos", json={"nome": "Horizonte — ARA"}).json()

    enrolado.armar_uma_vez("salvar_ara")
    resposta = plena.post(f"/toc/ara/projetos/{projeto['id']}/efeitos", json={"titulo": UDE})

    confere_o_envelope(resposta)
    ara = plena.get(f"/toc/ara/projetos/{projeto['id']}").json()
    titulos = [n["titulo"] for n in ara["projeto"]["nos"]]
    assert titulos == [f"{UDE} — pela outra facilitadora"], titulos


def test_a_nuvem_recusa_a_escrita_que_partiu_de_versao_velha(plena_com_corrida):
    plena, enrolado = plena_com_corrida
    projeto = plena.post("/toc/nc/projetos", json={"nome": DILEMA}).json()

    enrolado.armar_uma_vez("salvar_nuvem")
    resposta = plena.post(
        f"/toc/nc/projetos/{projeto['id']}/arestas/A_B/premissas",
        json={"texto": "Sem a necessidade B o objetivo não se sustenta"},
    )

    confere_o_envelope(resposta)
    nuvem = plena.get(f"/toc/nc/projetos/{projeto['id']}").json()
    textos = [
        premissa["texto"]
        for aresta in nuvem["arestas"]
        for premissa in aresta["premissas"]
    ]
    assert textos == ["Premissa escrita pela outra facilitadora"], textos


def test_o_codigo_da_recusa_esta_no_registro_unico_do_a7():
    """Emitir código não declarado é o que `ErroDoFio` recusa — aqui prova-se o inverso."""
    from toc_api.dominio.federacao.wire import CODIGOS, CODIGOS_PROPRIOS

    assert "VERSION_CONFLICT" in CODIGOS
    assert CODIGOS_PROPRIOS["VERSION_CONFLICT"], "código próprio sem motivo declarado"


def test_o_conflito_nao_cai_no_tradutor_generico_de_recusa():
    """`ConflitoDeVersao` tem tradutor próprio; sem ele viraria `DOMAIN_REFUSED`.

    O código genérico dizia ao cliente "alguma regra recusou" — e a correção dele é
    outra: aqui não se muda o pedido, recarrega-se e refaz-se. Foi assim que a resposta
    saiu antes de o tradutor existir, e é o que este teste impede de voltar.
    """
    from toc_api.http import erros as tradutores

    app = criar_app(dict(AMBIENTE))
    tratador = app.exception_handlers.get(ConflitoDeVersao)
    assert tratador is not None, sorted(
        getattr(k, "__name__", str(k)) for k in app.exception_handlers
    )
    assert "VERSION_CONFLICT" in tradutores.CODIGOS_ACRESCENTADOS
