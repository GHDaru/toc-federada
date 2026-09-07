"""A árvore de Estratégia & Táticas (S&T) contra o PostgreSQL real (spec 010, T-06).

Siglas, uma vez neste arquivo: **S&T** — Estratégia & Táticas (*Strategy & Tactics*) ·
**M5** — o módulo da S&T · **M1** — Núcleo de Diagramas Lógicos · **RF/RN/RNF** —
requisito funcional / regra de negócio / requisito não funcional da spec 010.

Três coisas que só o banco de verdade prova, e por isso este arquivo não é opcional:

1. **A ida e volta das três premissas** (o portão nomeado do roadmap para o ciclo 010):
   gravadas, relidas e idênticas — e a numeração **recalculada da estrutura**, nunca lida
   de coluna nenhuma (RN-01).
2. **O isolamento por inquilino** sobre as tabelas novas: a árvore de um inquilino não
   existe para o outro (RNF-03 da spec 003).
3. **A trava otimista** do agregado (ADR 0010): duas escritas da mesma versão, e a
   segunda é recusada com `ConflitoDeVersao` — o que o duplo em memória imita e o banco
   decide.

Base sintética (ADR 0006): "Instituição Horizonte", personas fictícias.
"""
from __future__ import annotations

from uuid import uuid4

import pytest
from sqlalchemy import text

from toc_api.dominio.erros import ConflitoDeVersao
from toc_api.dominio.identidade import DonoDoProjeto
from toc_api.dominio.snt import (
    CategoriaDoPasso,
    PremissasDoPasso,
    StatusDoPasso,
    nova_arvore_snt,
)
from toc_api.infra.configuracao import Configuracao
from toc_api.infra.persistencia.fabrica import criar_persistencia

from ..dominio.snt_sintetica import AGORA, META_GLOBAL, NOME, PLANO, PREMISSAS_DE_1_1

pytestmark = pytest.mark.integracao


def repositorio_de(url: str, esquema: str):
    return criar_persistencia(
        Configuracao.do_ambiente({"DATABASE_URL": url, "TOC_DB_SCHEMA": esquema})
    ).projetos


def dono(inquilino: str = "instituicao-horizonte") -> DonoDoProjeto:
    return DonoDoProjeto(inquilino_id=inquilino, usuario_id="u-facilitadora")


def arvore_sintetica(inquilino: str = "instituicao-horizonte"):
    arvore = nova_arvore_snt(
        id=uuid4(), dono=dono(inquilino), nome=NOME, meta_global=META_GLOBAL, em=AGORA
    )
    chaves: dict[str, object] = {}
    for chave, pai, estrategia, tatica in PLANO:
        no = arvore.adicionar_passo(
            estrategia=estrategia,
            tatica=tatica,
            pai_id=None if pai is None else chaves[pai],
            em=AGORA,
        )
        chaves[chave] = no.id
    return arvore, chaves


def test_a_arvore_completa_faz_ida_e_volta_com_as_tres_premissas(url_postgres, esquema_migrado):
    """O portão do roadmap: as três premissas persistidas, e a numeração DERIVADA na volta."""
    repositorio = repositorio_de(url_postgres, esquema_migrado)
    arvore, chaves = arvore_sintetica()
    arvore.editar_premissas(chaves["1.1"], em=AGORA, **PREMISSAS_DE_1_1)
    arvore.editar_passo(chaves["1.2"], categoria=CategoriaDoPasso.VCD, em=AGORA)
    arvore.mudar_status(chaves["1.1"], StatusDoPasso.EM_EXECUCAO, autor="u-gestora", em=AGORA)
    repositorio.salvar_snt(arvore)

    volta = repositorio.obter_snt("instituicao-horizonte", arvore.projeto.id)
    print(
        f"passos gravados={len(arvore.passos)} · relidos={len(volta.passos)} · "
        f"numeração relida={[volta.numero(no.id) for no in volta.passos]}"
    )
    assert volta is not None
    assert volta.meta_global == META_GLOBAL
    assert dict(volta.fichas()) == dict(arvore.fichas())
    assert volta.estrutura() == arvore.estrutura()
    assert volta.numeros() == arvore.numeros()
    assert volta.ficha(chaves["1.1"]).premissas == PremissasDoPasso(**PREMISSAS_DE_1_1)
    assert volta.ficha(chaves["1.2"]).categoria is CategoriaDoPasso.VCD
    assert volta.ficha(chaves["1.1"]).status is StatusDoPasso.EM_EXECUCAO


def test_a_numeracao_nao_esta_no_banco_em_coluna_nenhuma(url_postgres, esquema_migrado):
    """RN-01 na fronteira da persistência: não há coluna de número para divergir."""
    persistencia = criar_persistencia(
        Configuracao.do_ambiente({"DATABASE_URL": url_postgres, "TOC_DB_SCHEMA": esquema_migrado})
    )
    with persistencia.motor.connect() as conexao:
        colunas = [
            linha[0]
            for linha in conexao.execute(
                text(
                    "select column_name from information_schema.columns "
                    "where table_schema = :e and table_name in ('snt_arvore', 'snt_passo') "
                    "order by table_name, column_name"
                ),
                {"e": esquema_migrado},
            )
        ]
    print(f"colunas das tabelas do M5 ({len(colunas)}): {colunas}")
    assert colunas, "as tabelas do M5 não existem no esquema migrado"
    assert not [c for c in colunas if "numero" in c or "step_number" in c]


def test_a_estrutura_volta_com_pai_e_ordem_e_a_arvore_e_estrita(url_postgres, esquema_migrado):
    repositorio = repositorio_de(url_postgres, esquema_migrado)
    arvore, chaves = arvore_sintetica()
    repositorio.salvar_snt(arvore)
    volta = repositorio.obter_snt("instituicao-horizonte", arvore.projeto.id)
    print(f"filhos de 1: {[volta.numero(f) for f in volta.filhos(chaves['1'])]}")
    assert [volta.numero(f) for f in volta.filhos(chaves["1"])] == ["1.1", "1.2", "1.3"]
    assert volta.projeto.arestas == ()


def test_mover_e_excluir_sobrevivem_a_ida_e_volta(url_postgres, esquema_migrado):
    """RF-07/RN-05: renumeração e recorte da exclusão continuam corretos depois de gravar."""
    repositorio = repositorio_de(url_postgres, esquema_migrado)
    arvore, chaves = arvore_sintetica()
    repositorio.salvar_snt(arvore)

    aberta = repositorio.obter_snt("instituicao-horizonte", arvore.projeto.id)
    aberta.excluir_subarvore(chaves["1.1"], em=AGORA)
    repositorio.salvar_snt(aberta)

    volta = repositorio.obter_snt("instituicao-horizonte", arvore.projeto.id)
    print(
        f"passos depois da exclusão={len(volta.passos)} · "
        f"numeração={[volta.numero(no.id) for no in volta.passos]}"
    )
    assert len(volta.passos) == len(PLANO) - 3
    assert volta.numero(chaves["1.2"]) == "1.1"
    assert volta.numero(chaves["1.3"]) == "1.2"


def test_a_arvore_de_um_inquilino_nao_existe_para_o_outro(url_postgres, esquema_migrado):
    repositorio = repositorio_de(url_postgres, esquema_migrado)
    arvore, _ = arvore_sintetica()
    repositorio.salvar_snt(arvore)
    print(f"projeto={arvore.projeto.id} · consulta como instituicao-aurora")
    assert repositorio.obter_snt("instituicao-aurora", arvore.projeto.id) is None
    assert repositorio.obter("instituicao-aurora", arvore.projeto.id) is None


def test_a_segunda_escrita_da_mesma_versao_e_recusada(url_postgres, esquema_migrado):
    """ADR 0010: a trava otimista vale para a S&T como vale para todo agregado."""
    repositorio = repositorio_de(url_postgres, esquema_migrado)
    arvore, chaves = arvore_sintetica()
    repositorio.salvar_snt(arvore)

    uma = repositorio.obter_snt("instituicao-horizonte", arvore.projeto.id)
    outra = repositorio.obter_snt("instituicao-horizonte", arvore.projeto.id)
    uma.adicionar_passo(estrategia="Quarta frente", em=AGORA)
    outra.adicionar_passo(estrategia="Quinta frente", em=AGORA)

    repositorio.salvar_snt(uma)
    with pytest.raises(ConflitoDeVersao) as erro:
        repositorio.salvar_snt(outra)
    print(
        f"recusa: versao_lida={erro.value.versao_lida} versao_atual={erro.value.versao_atual}"
    )
    assert erro.value.versao_atual > erro.value.versao_lida


def test_excluir_definitivamente_leva_as_tabelas_do_m5_junto(url_postgres, esquema_migrado):
    """A cascata é do banco: linha de passo órfã seria dado sem dono nenhum."""
    persistencia = criar_persistencia(
        Configuracao.do_ambiente({"DATABASE_URL": url_postgres, "TOC_DB_SCHEMA": esquema_migrado})
    )
    repositorio = persistencia.projetos
    arvore, _ = arvore_sintetica()
    repositorio.salvar_snt(arvore)
    repositorio.excluir_definitivamente("instituicao-horizonte", arvore.projeto.id)
    with persistencia.motor.connect() as conexao:
        restantes = conexao.execute(
            text("select count(*) from snt_passo where projeto_id = :p"),
            {"p": arvore.projeto.id},
        ).scalar_one()
    print(f"linhas de snt_passo restantes: {restantes}")
    assert restantes == 0
