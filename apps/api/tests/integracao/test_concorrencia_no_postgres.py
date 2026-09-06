"""Perda de atualização (*lost update*) entre duas pessoas na mesma análise.

Siglas, uma vez neste arquivo: **M1** — Núcleo de Diagramas Lógicos · **M2** — Árvore da
Realidade Atual (ARA) · **M3** — Nuvem de Conflito (NC) · **HTTP** — *HyperText Transfer
Protocol* · **APH** — Aplicação ↔ Harness · **DDD** — *Domain-Driven Design*.

**O defeito que este arquivo reproduz.** `RepositorioDeProjetosSQL.salvar` gravava o
retrato do agregado que estava em memória e `_reconciliar_grafo` apagava do banco toda
linha fora desse retrato (`delete(... id.notin_(ids))`). Duas escritas que leram a MESMA
versão produzem dois retratos, e o segundo apaga o que o primeiro acrescentou — sem erro,
sem aviso, sem código de saída diferente. A coluna `versao` existia e era incrementada
(`dominio/projeto.py`), mas nunca aparecia num `WHERE`: era ler-modificar-escrever sem
trava. Numa ferramenta de facilitação em grupo, que é o que esta aplicação se propõe a
ser, isso é trabalho de gente perdido em silêncio.

**Por que estes testes são determinísticos e ainda assim concorrentes de verdade.** Uma
corrida disparada "e torcer para colidir" reprova por sorte e passa por sorte. Aqui as
*threads* leem todas antes de qualquer uma gravar — uma `threading.Barrier` garante a
ordem `R1…Rn · W1…Wn`, que é a definição da perda de atualização — e cada uma usa a sua
própria sessão contra o PostgreSQL REAL (nunca SQLite, brief §1), como processos à parte
fariam.

Base sintética (ADR 0006): Instituição Horizonte, papéis, nenhum nome de pessoa.
"""
from __future__ import annotations

import json
import threading
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from toc_api.aplicacao.ara import CriarProjetoARA
from toc_api.aplicacao.nuvem import CriarProjetoNC
from toc_api.aplicacao.projetos import CriarProjeto
from toc_api.dominio.erros import ConflitoDeVersao
from toc_api.dominio.identidade import DonoDoProjeto
from toc_api.dominio.nuvem import ChaveDaAresta
from toc_api.http.app import criar_app
from toc_api.infra.configuracao import Configuracao
from toc_api.infra.observabilidade.otel import RastreadorNulo
from toc_api.infra.persistencia.fabrica import criar_persistencia
from toc_api.infra.relogio import RelogioDoSistema

pytestmark = pytest.mark.integracao

HORIZONTE = DonoDoProjeto(inquilino_id="inq-horizonte", usuario_id="usr-facilitadora")
T0 = datetime(2026, 9, 6, 12, 0, tzinfo=timezone.utc)

UDE = "A evasão de estudantes aumenta a cada semestre na Instituição Horizonte"

TOKEN = "tok-concorrencia-facilitadora"
IDENTIDADES = {
    TOKEN: {
        "inquilino_id": HORIZONTE.inquilino_id,
        "usuario_id": HORIZONTE.usuario_id,
        "capabilities": ["toc:read", "toc:write"],
        "app_id": "toc-federada",
    }
}

#: Quantas pessoas escrevem ao mesmo tempo. É o número da reprodução do crítico
#: independente: 20 requisições concorrentes de criação de nó devolviam 20 vezes
#: `201 Created` e persistiam UM nó.
QUANTAS = 20


def _pecas(url: str, esquema: str) -> dict:
    """Uma composição NOVA — motor, sessão e repositório próprios, como outro processo."""
    persistencia = criar_persistencia(
        Configuracao.do_ambiente({"DATABASE_URL": url, "TOC_DB_SCHEMA": esquema})
    )
    return dict(
        rastreador=RastreadorNulo(),
        repositorio=persistencia.projetos,
        relogio=RelogioDoSistema(),
    )


@pytest.fixture()
def pecas(url_postgres, esquema_migrado):
    return _pecas(url_postgres, esquema_migrado)


def _em_paralelo(quantos: int, trabalho):
    """Roda `trabalho(i)` em `quantos` threads, TODAS lendo antes de qualquer gravar.

    Devolve a lista de resultados na ordem dos índices; cada posição é
    `("ok", valor)` ou `("erro", excecao)`.
    """
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
        fio.join(timeout=60)
    assert all(r is not None for r in resultados), "alguma thread não terminou em 60s"
    return resultados  # type: ignore[return-value]


# -- M1 · o caso mínimo, sem thread nenhuma ---------------------------------------------


def test_a_segunda_escrita_da_mesma_versao_e_recusada_e_nao_apaga_a_primeira(pecas):
    """Ler duas vezes, mutar as duas cópias, gravar as duas. O caso puro do defeito.

    Antes do conserto as duas gravações respondiam igual (nada) e o banco ficava com UM
    nó: a segunda apagava o da primeira por `id.notin_`. Agora a segunda é recusada com a
    versão que ela leu e a que o banco tem, e o trabalho da primeira continua lá.
    """
    repositorio = pecas["repositorio"]
    projeto = CriarProjeto(**pecas).rodar(dono=HORIZONTE, nome="Horizonte — diagrama")

    primeira = repositorio.obter(HORIZONTE.inquilino_id, projeto.id)
    segunda = repositorio.obter(HORIZONTE.inquilino_id, projeto.id)
    assert primeira.versao == segunda.versao, "as duas leram a mesma versão"

    no_da_primeira = primeira.adicionar_no(titulo="Os formulários chegam incompletos.", em=T0)
    no_da_segunda = segunda.adicionar_no(titulo="A fila do balcão dobrou.", em=T0)

    repositorio.salvar(primeira)

    with pytest.raises(ConflitoDeVersao) as recusa:
        repositorio.salvar(segunda)

    assert recusa.value.versao_lida == segunda.versao - 1
    assert recusa.value.versao_atual == primeira.versao

    reaberto = repositorio.obter(HORIZONTE.inquilino_id, projeto.id)
    ids = {n.id for n in reaberto.nos}
    assert no_da_primeira.id in ids, "o trabalho da primeira escrita foi apagado em silêncio"
    assert no_da_segunda.id not in ids, "a escrita recusada não pode ter efeito parcial"


def test_a_escrita_recusada_nao_deixa_efeito_parcial_nenhum(pecas):
    """A recusa é atômica: nem o nó novo, nem a `versao`, nem o `atualizado_em` avançam."""
    repositorio = pecas["repositorio"]
    projeto = CriarProjeto(**pecas).rodar(dono=HORIZONTE, nome="Horizonte — diagrama")
    primeira = repositorio.obter(HORIZONTE.inquilino_id, projeto.id)
    segunda = repositorio.obter(HORIZONTE.inquilino_id, projeto.id)

    primeira.adicionar_no(titulo="Os formulários chegam incompletos.", em=T0)
    repositorio.salvar(primeira)
    depois_da_vencedora = repositorio.obter(HORIZONTE.inquilino_id, projeto.id)

    segunda.adicionar_no(titulo="A fila do balcão dobrou.", em=T0)
    segunda.renomear("Horizonte — nome que a perdedora quis", em=T0)
    with pytest.raises(ConflitoDeVersao):
        repositorio.salvar(segunda)

    agora = repositorio.obter(HORIZONTE.inquilino_id, projeto.id)
    assert agora.versao == depois_da_vencedora.versao
    assert agora.nome == depois_da_vencedora.nome
    assert {n.id for n in agora.nos} == {n.id for n in depois_da_vencedora.nos}


# -- M1 · a reprodução do crítico: 20 escritas concorrentes de verdade -------------------


def test_vinte_escritas_concorrentes_de_no_nao_perdem_trabalho_em_silencio(
    url_postgres, esquema_migrado
):
    """A reprodução do crítico, agora determinística: 20 leem, 20 gravam.

    O invariante é o que uma ferramenta multiusuário precisa: **quem foi aceito está no
    banco**. Antes do conserto as 20 eram aceitas e o banco tinha 1 nó — 19 pessoas
    perdiam o trabalho sem saber. Agora as aceitas e as persistidas são o mesmo conjunto,
    e cada recusada sabe contra qual versão perdeu.
    """
    pecas = _pecas(url_postgres, esquema_migrado)
    projeto = CriarProjeto(**pecas).rodar(dono=HORIZONTE, nome="Horizonte — diagrama")

    def escreve(i: int, barreira: threading.Barrier):
        proprias = _pecas(url_postgres, esquema_migrado)
        repositorio = proprias["repositorio"]
        copia = repositorio.obter(HORIZONTE.inquilino_id, projeto.id)
        barreira.wait(timeout=60)  # todas leram antes de qualquer uma gravar
        no = copia.adicionar_no(titulo=f"Efeito indesejável nº {i}", em=T0)
        repositorio.salvar(copia)
        return no.id

    resultados = _em_paralelo(QUANTAS, escreve)

    aceitas = {valor for estado, valor in resultados if estado == "ok"}
    recusas = [erro for estado, erro in resultados if estado == "erro"]

    assert all(isinstance(e, ConflitoDeVersao) for e in recusas), [
        f"{type(e).__name__}: {e}" for e in recusas
    ]
    assert aceitas, "nenhuma escrita passou — a trava não pode travar todo mundo"

    reaberto = pecas["repositorio"].obter(HORIZONTE.inquilino_id, projeto.id)
    persistidos = {n.id for n in reaberto.nos}
    print(
        f"concorrência M1: {QUANTAS} escritas · aceitas {len(aceitas)} · "
        f"recusadas {len(recusas)} · nós no banco {len(persistidos)}"
    )
    assert persistidos == aceitas, (
        f"{len(aceitas)} escrita(s) aceita(s) e {len(persistidos)} nó(s) no banco: "
        "trabalho aceito e perdido em silêncio"
    )
    assert len(aceitas) + len(recusas) == QUANTAS


# -- a CLASSE, não o caso: as três portas do mesmo repositório ---------------------------


def test_a_ara_tem_a_mesma_trava_que_o_m1(url_postgres, esquema_migrado):
    """`salvar_ara` grava pelo mesmo `_gravar_projeto` — logo tem o mesmo defeito."""
    pecas = _pecas(url_postgres, esquema_migrado)
    projeto = CriarProjetoARA(**pecas).rodar(dono=HORIZONTE, nome="Horizonte — ARA")

    def escreve(i: int, barreira: threading.Barrier):
        proprias = _pecas(url_postgres, esquema_migrado)
        repositorio = proprias["repositorio"]
        ara = repositorio.obter_ara(HORIZONTE.inquilino_id, projeto.id)
        barreira.wait(timeout=60)
        no = ara.adicionar_efeito(titulo=f"{UDE} — variação {i}", em=T0)
        repositorio.salvar_ara(ara)
        return no.id

    resultados = _em_paralelo(QUANTAS, escreve)
    aceitas = {valor for estado, valor in resultados if estado == "ok"}
    recusas = [erro for estado, erro in resultados if estado == "erro"]
    assert all(isinstance(e, ConflitoDeVersao) for e in recusas), [
        f"{type(e).__name__}: {e}" for e in recusas
    ]

    reaberta = pecas["repositorio"].obter_ara(HORIZONTE.inquilino_id, projeto.id)
    persistidos = {n.id for n in reaberta.projeto.nos}
    print(
        f"concorrência M2 (ARA): {QUANTAS} escritas · aceitas {len(aceitas)} · "
        f"recusadas {len(recusas)} · nós no banco {len(persistidos)}"
    )
    assert persistidos == aceitas


def test_a_nuvem_tem_a_mesma_trava_que_o_m1(url_postgres, esquema_migrado):
    """A Nuvem de Conflito tem topologia fixa: o que se disputa é a premissa escrita."""
    pecas = _pecas(url_postgres, esquema_migrado)
    projeto = CriarProjetoNC(**pecas).rodar(
        dono=HORIZONTE, nome="Dilema da expansão da Instituição Horizonte"
    )

    def escreve(i: int, barreira: threading.Barrier):
        proprias = _pecas(url_postgres, esquema_migrado)
        repositorio = proprias["repositorio"]
        nuvem = repositorio.obter_nuvem(HORIZONTE.inquilino_id, projeto.id)
        barreira.wait(timeout=60)
        premissa = nuvem.registrar_premissa(
            ChaveDaAresta.A_B,
            f"Para o objetivo, a necessidade B é indispensável — leitura {i}",
            em=T0,
        )
        repositorio.salvar_nuvem(nuvem)
        return premissa.id

    resultados = _em_paralelo(QUANTAS, escreve)
    aceitas = {valor for estado, valor in resultados if estado == "ok"}
    recusas = [erro for estado, erro in resultados if estado == "erro"]
    assert all(isinstance(e, ConflitoDeVersao) for e in recusas), [
        f"{type(e).__name__}: {e}" for e in recusas
    ]

    reaberta = pecas["repositorio"].obter_nuvem(HORIZONTE.inquilino_id, projeto.id)
    persistidas = {p.id for p in reaberta.premissas()}
    print(
        f"concorrência M3 (NC): {QUANTAS} escritas · aceitas {len(aceitas)} · "
        f"recusadas {len(recusas)} · premissas no banco {len(persistidas)}"
    )
    assert persistidas == aceitas


# -- a borda: quem perdeu a corrida SABE que perdeu --------------------------------------


def test_pela_borda_http_o_perdedor_recebe_409_com_a_versao_atual(
    url_postgres, esquema_migrado
):
    """20 requisições concorrentes de criação de nó, pela superfície de verdade.

    Antes: 20 × `201 Created` e um nó no banco. Agora: quem perde recebe `409` com o
    código estável do §A.7 e a versão que o banco tem — o dado que permite recarregar e
    tentar de novo, que é o que "não silêncio" quer dizer.
    """
    ambiente = {
        "DATABASE_URL": url_postgres,
        "TOC_DB_SCHEMA": esquema_migrado,
        "TOC_AMBIENTE": "teste",
        "TOC_IDENTIDADES_FALSAS": json.dumps(IDENTIDADES),
    }

    def cliente() -> TestClient:
        c = TestClient(criar_app(dict(ambiente)))
        c.headers["Authorization"] = f"Bearer {TOKEN}"
        return c

    abertura = cliente()
    projeto = abertura.post("/toc/projetos", json={"nome": "Horizonte — diagrama"}).json()

    def escreve(i: int, barreira: threading.Barrier):
        c = cliente()
        barreira.wait(timeout=60)
        return c.post(
            f"/toc/projetos/{projeto['id']}/nos",
            json={"titulo": f"Efeito indesejável nº {i}"},
        )

    resultados = _em_paralelo(QUANTAS, escreve)
    respostas = [valor for estado, valor in resultados if estado == "ok"]
    assert len(respostas) == QUANTAS, [e for estado, e in resultados if estado == "erro"]

    criados = [r for r in respostas if r.status_code == 201]
    conflitos = [r for r in respostas if r.status_code == 409]
    print(
        f"concorrência HTTP: {QUANTAS} requisições · 201 {len(criados)} · "
        f"409 {len(conflitos)} · outros "
        f"{sorted({r.status_code for r in respostas} - {201, 409})}"
    )
    assert len(criados) + len(conflitos) == QUANTAS, sorted(
        {r.status_code for r in respostas}
    )

    for r in conflitos:
        corpo = r.json()
        assert set(corpo) == {"error"}, corpo
        assert corpo["error"]["code"] == "VERSION_CONFLICT", corpo
        detalhes = corpo["error"].get("details", {})
        assert isinstance(detalhes.get("versao_atual"), int), corpo
        assert isinstance(detalhes.get("versao_lida"), int), corpo

    depois = abertura.get(f"/toc/projetos/{projeto['id']}").json()
    assert len(depois["nos"]) == len(criados), (
        f"{len(criados)} resposta(s) 201 e {len(depois['nos'])} nó(s) no banco"
    )
