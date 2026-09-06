"""A TERCEIRA porta para o mesmo estado: o catálogo `toc.*` da federação.

Siglas, uma vez neste arquivo: **APH** — Aplicação ↔ Harness · **M1** — Núcleo de
Diagramas Lógicos · **M3** — Nuvem de Conflito (NC) · **TOC** — Teoria das Restrições ·
**DDD** — *Domain-Driven Design* (Design Orientado a Domínio) · **UUID** — *Universally
Unique Identifier*.

O crítico achou a porta dos fundos do agregado pelas rotas de `/toc/projetos`. Fechar as
rotas teria deixado esta aqui aberta: `ExecutorDoCatalogo` monta os MESMOS casos de uso
genéricos do M1 (`AdicionarNo`, `LigarNos`, `EditarNo`, `ExcluirNo`) para servir
`toc.criar_nos`, `toc.criar_arestas`, `toc.atualizar_no` e `toc.excluir_nos`. Uma ação
governada, aprovada por gate humano, mutilaria a nuvem exatamente como a rota mutilava.

É por isso que a correção mora no `Projeto` e não na borda: a recusa aqui não foi
programada nesta camada — ela vem de graça, do mesmo lugar. E o desfecho é `failed` com o
motivo, que é a forma que o §A.5.9(b) do Anexo A do Padrão APH dá para "este alvo não
executou": recusa de invariante é dado de desfecho, não erro de sistema.
"""
from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

import pytest

from toc_api.dominio.federacao.principal import Capability, Principal
from toc_api.dominio.identidade import DonoDoProjeto
from toc_api.dominio.nuvem import ChaveDaAresta, PapelDaEntidade, novo_projeto_nc
from toc_api.infra.federacao.executor import ExecutorDoCatalogo
from toc_api.infra.observabilidade.otel import RastreadorNulo
from toc_api.infra.persistencia.memoria import RepositorioDeProjetosEmMemoria
from toc_api.infra.relogio import RelogioDoSistema

T0 = datetime(2026, 9, 6, 12, 0, tzinfo=timezone.utc)
DONA = DonoDoProjeto(inquilino_id="inq-horizonte", usuario_id="usr-facilitadora")

#: Persona fictícia (ADR 0006) com o par de capacidades que o catálogo mutador exige.
PRINCIPAL = Principal(
    usuario_id="usr-facilitadora",
    nome_de_exibicao="Facilitadora TOC",
    inquilino_id="inq-horizonte",
    capabilities=(Capability("toc:read"), Capability("toc:write")),
    app_id="toc-federada",
)


@pytest.fixture()
def cenario():
    repositorio = RepositorioDeProjetosEmMemoria()
    nuvem = novo_projeto_nc(id=uuid4(), dono=DONA, nome="Dilema da expansão", em=T0)
    repositorio.salvar_nuvem(nuvem)
    executor = ExecutorDoCatalogo(
        rastreador=RastreadorNulo(),
        projetos=repositorio,
        aras=repositorio,
        relogio=RelogioDoSistema(),
        nuvens=repositorio,
    )
    return {"executor": executor, "repositorio": repositorio, "nuvem": nuvem}


def acoes_mutadoras_do_m1(nuvem):
    entidade = {p: nuvem.entidade(p).id for p in PapelDaEntidade}
    aresta = nuvem.aresta(ChaveDaAresta.D_D_PRIME)
    projeto_id = str(nuvem.projeto.id)
    return (
        (
            "toc.criar_nos",
            {"projeto_id": projeto_id, "nos": [{"titulo": "Sexta entidade", "tipo": "ude"}],
             "__indice__": 0},
        ),
        (
            "toc.criar_arestas",
            {
                "projeto_id": projeto_id,
                "arestas": [
                    {"origem_id": str(entidade[PapelDaEntidade.A]),
                     "destino_id": str(entidade[PapelDaEntidade.D])}
                ],
                "__indice__": 0,
            },
        ),
        (
            "toc.atualizar_no",
            {
                "projeto_id": projeto_id,
                "no_id": str(entidade[PapelDaEntidade.A]),
                "titulo": "Texto entrando pela ação governada",
            },
        ),
        (
            "toc.excluir_nos",
            {"projeto_id": projeto_id, "no_ids": [str(entidade[PapelDaEntidade.A])],
             "__indice__": 0},
        ),
    )


def test_nenhuma_acao_mutadora_do_catalogo_mutila_uma_nuvem(cenario):
    executor, repositorio, nuvem = (
        cenario["executor"], cenario["repositorio"], cenario["nuvem"]
    )

    desfechos = []
    for action_id, args in acoes_mutadoras_do_m1(nuvem):
        status, mensagem = executor.executar(
            action_id=action_id, args=args, principal=PRINCIPAL
        )
        desfechos.append((action_id, status, mensagem))

    for action_id, status, mensagem in desfechos:
        assert status == "failed", f"{action_id} EXECUTOU sobre a nuvem: {mensagem}"
        assert "raiz do agregado" in mensagem, f"{action_id} falhou por outro motivo: {mensagem}"
        assert "NuvemDeConflito" in mensagem
    print("\n" + "\n".join(f"{a}: {s} — {m}" for a, s, m in desfechos))

    intacta = repositorio.obter_nuvem(DONA.inquilino_id, nuvem.projeto.id)
    assert len(intacta.entidades) == 5
    assert len(intacta.arestas) == 7
    assert sorted(c.value for c in intacta.chaves) == sorted(c.value for c in ChaveDaAresta)


def test_a_acao_de_leitura_do_catalogo_continua_alcancando_a_nuvem(cenario):
    """A trava é sobre ESCRITA do grafo: exportar e listar continuam servindo a nuvem."""
    executor, nuvem = cenario["executor"], cenario["nuvem"]

    status, mensagem = executor.executar(
        action_id="toc.exportar_projeto",
        args={"projeto_id": str(nuvem.projeto.id)},
        principal=PRINCIPAL,
    )

    print(f"toc.exportar_projeto: {status} — {mensagem}")
    assert status == "executed"
    assert executor.saidas[-1]["nos"] == 5
    assert executor.saidas[-1]["arestas"] == 7


def test_o_catalogo_continua_mutando_o_projeto_generico(cenario):
    """O M1 genérico não perde nada: lá o `Projeto` é a própria raiz do agregado."""
    executor, repositorio = cenario["executor"], cenario["repositorio"]
    from toc_api.dominio.projeto import Projeto

    projeto = Projeto(
        id=uuid4(), dono=DONA, nome="Rascunho livre", criado_em=T0, alterado_em=T0
    )
    repositorio.salvar(projeto)

    status, mensagem = executor.executar(
        action_id="toc.criar_nos",
        args={
            "projeto_id": str(projeto.id),
            "nos": [{"titulo": "A evasão aumenta a cada semestre.", "tipo": "ude"}],
            "__indice__": 0,
        },
        principal=PRINCIPAL,
    )

    print(f"toc.criar_nos sobre projeto genérico: {status} — {mensagem}")
    assert status == "executed"
    assert len(repositorio.obter(DONA.inquilino_id, projeto.id).nos) == 1
