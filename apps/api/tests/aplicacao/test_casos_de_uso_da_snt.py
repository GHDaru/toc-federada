"""Casos de uso do M5 — sobre as portas, sem banco e sem rede (spec 010).

Siglas, uma vez neste arquivo: **M5** — Estratégia & Táticas · **S&T** — Estratégia &
Táticas (*Strategy & Tactics*) · **M1** — Núcleo de Diagramas Lógicos · **OTel** —
OpenTelemetry · **APH** — Aplicação ↔ Harness · **ADR** — *Architecture Decision Record*
(Registro de Decisão Arquitetural) · **RF/RNF** — requisito funcional / requisito não
funcional da spec 010.

O que este arquivo protege, e que nenhum teste de domínio alcança sozinho:

- **cada mutação abre um span** (P5, RNF-03) — e o span carrega grandeza, número e
  vocabulário fechado, **nunca** o texto que a pessoa escreveu (ADR 0006);
- **`SubarvoreExcluida` leva a contagem para o traço** — é o número que a confirmação
  prometeu, agora auditável;
- **a autorização acontece no caso de uso** (§B.7.2 do Anexo B), pelo `Executor`, e um
  principal só-leitura não escreve;
- **o autor da mudança de status vem do principal**, nunca do corpo do pedido — a linhagem
  não registrava autor nenhum (RN-03).
"""
from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

import pytest

from toc_api.aplicacao.governanca import (
    TOC_ESCRITA,
    TOC_LEITURA,
    AutorizacaoNegada,
    Executor,
)
from toc_api.aplicacao.projetos import ExcluirProjeto, ListarProjetos, RestaurarProjeto
from toc_api.aplicacao.snt import (
    AbrirProjetoSnT,
    AdicionarPassoDaSnT,
    CriarProjetoSnT,
    EditarMetaGlobal,
    EditarPassoDaSnT,
    EditarPremissasDoPasso,
    ExcluirSubarvore,
    ExportarSnT,
    MoverPassoDaSnT,
    MudarStatusDoPassoDaSnT,
    PendenciasDaSnT,
    PreverRenumeracao,
)
from toc_api.dominio.erros import NaoEncontrado
from toc_api.dominio.federacao.principal import principal_de_introspeccao
from toc_api.dominio.snt import CategoriaDoPasso, StatusDoPasso

from ..dominio.snt_sintetica import META_GLOBAL, NOME, PLANO
from .fakes import RastreadorFalso, RelogioFalso
from .fakes_m5 import RepositorioDaSnTFalso

AGORA = datetime(2026, 9, 6, 10, 0, tzinfo=timezone.utc)


def principal(capabilities=(TOC_LEITURA, TOC_ESCRITA), inquilino="instituicao-horizonte"):
    return principal_de_introspeccao(
        {
            "active": True,
            "user": {"id": "u-facilitadora", "name": "Facilitadora TOC"},
            "tenant_id": inquilino,
            "capabilities": list(capabilities),
            "app_id": "toc",
        }
    )


@pytest.fixture()
def pecas():
    rastreador = RastreadorFalso()
    repositorio = RepositorioDaSnTFalso()
    executor = Executor(
        principal=principal(),
        rastreador=rastreador,
        repositorio=repositorio,
        relogio=RelogioFalso(AGORA),
    )
    return executor, repositorio, rastreador


def plano(executor) -> tuple[object, dict[str, object]]:
    projeto = executor.rodar(CriarProjetoSnT, nome=NOME, meta_global=META_GLOBAL)
    chaves: dict[str, object] = {}
    for chave, pai, estrategia, tatica in PLANO:
        no = executor.rodar(
            AdicionarPassoDaSnT,
            projeto_id=projeto.id,
            estrategia=estrategia,
            tatica=tatica,
            pai_id=None if pai is None else chaves[pai],
        )
        chaves[chave] = no.id
    return projeto, chaves


# ---------------------------------------------------------------------------------------
# Criar, abrir e o span de cada caso de uso (P5)
# ---------------------------------------------------------------------------------------


def test_criar_e_abrir_a_snt_pelo_executor_abre_span_por_caso_de_uso(pecas) -> None:
    executor, _, rastreador = pecas
    projeto = executor.rodar(CriarProjetoSnT, nome=NOME, meta_global=META_GLOBAL)
    arvore = executor.rodar(AbrirProjetoSnT, projeto_id=projeto.id)

    print(f"spans={rastreador.nomes}")
    assert rastreador.nomes == ["caso_de_uso.criar_projeto_snt", "caso_de_uso.abrir_projeto_snt"]
    assert arvore.meta_global == META_GLOBAL
    assert rastreador.spans[0].atributos["toc.inquilino_id"] == "instituicao-horizonte"


def test_a_snt_aparece_na_listagem_do_m1_com_a_ferramenta_propria(pecas) -> None:
    """RF-01: listagem, lixeira e restauração são herdadas do M1, sem reimplementação."""
    executor, _, _ = pecas
    projeto = executor.rodar(CriarProjetoSnT, nome=NOME, meta_global=META_GLOBAL)
    listados = executor.rodar(ListarProjetos)
    print(f"projetos listados={[(p.nome, p.ferramenta) for p in listados]}")
    assert [(p.id, p.ferramenta) for p in listados] == [(projeto.id, "snt")]


def test_excluir_e_restaurar_devolvem_a_arvore_inteira(pecas) -> None:
    """US-02: volta com passos, premissas e status intactos — a herança sem exceção."""
    executor, _, _ = pecas
    projeto, chaves = plano(executor)
    executor.rodar(
        EditarPremissasDoPasso,
        projeto_id=projeto.id,
        no_id=chaves["1.1"],
        paralela="a fila é o gargalo",
    )
    executor.rodar(
        MudarStatusDoPassoDaSnT,
        projeto_id=projeto.id,
        no_id=chaves["1.1"],
        status=StatusDoPasso.EM_EXECUCAO,
    )
    antes = executor.rodar(AbrirProjetoSnT, projeto_id=projeto.id)
    fichas_antes = dict(antes.fichas())

    executor.rodar(ExcluirProjeto, projeto_id=projeto.id)
    executor.rodar(RestaurarProjeto, projeto_id=projeto.id)

    depois = executor.rodar(AbrirProjetoSnT, projeto_id=projeto.id)
    print(f"fichas antes={len(fichas_antes)} depois={len(dict(depois.fichas()))}")
    assert dict(depois.fichas()) == fichas_antes
    assert depois.numero(chaves["1.1.2"]) == "1.1.2"


# ---------------------------------------------------------------------------------------
# O traço de cada mutação (RNF-03, DoD 11) — grandeza, nunca texto de pessoa
# ---------------------------------------------------------------------------------------


def test_o_span_de_adicionar_passo_carrega_o_numero_e_nao_a_estrategia(pecas) -> None:
    executor, _, rastreador = pecas
    projeto, chaves = plano(executor)
    span = [s for s in rastreador.spans if s.nome == "caso_de_uso.adicionar_passo_da_snt"][-1]
    print(f"atributos={span.atributos}")
    assert span.atributos["toc.numero"] == "1.3"
    valores = " ".join(str(v) for v in span.atributos.values())
    assert "Sustentar a demanda" not in valores


def test_o_span_da_exclusao_de_subarvore_carrega_a_contagem(pecas) -> None:
    """RN-05: o número que a confirmação prometeu vira o número que o traço registra."""
    executor, _, rastreador = pecas
    projeto, chaves = plano(executor)
    removidos = executor.rodar(ExcluirSubarvore, projeto_id=projeto.id, no_id=chaves["1.1"])
    span = [s for s in rastreador.spans if s.nome == "caso_de_uso.excluir_subarvore"][-1]
    print(f"removidos={len(removidos)} · atributos={span.atributos}")
    assert span.atributos["toc.passos_excluidos"] == 3 == len(removidos)


def test_o_span_do_mover_carrega_os_numeros_de_antes_e_depois(pecas) -> None:
    executor, _, rastreador = pecas
    projeto, chaves = plano(executor)
    destino = executor.rodar(
        AdicionarPassoDaSnT, projeto_id=projeto.id, estrategia="Abrir a segunda frente"
    )
    executor.rodar(
        MoverPassoDaSnT, projeto_id=projeto.id, no_id=chaves["1.1"], novo_pai_id=destino.id
    )
    span = [s for s in rastreador.spans if s.nome == "caso_de_uso.mover_passo_da_snt"][-1]
    print(f"atributos={span.atributos}")
    assert (span.atributos["toc.numero_anterior"], span.atributos["toc.numero"]) == ("1.1", "2.1")


def test_o_span_da_mudanca_de_status_carrega_o_vocabulario_fechado(pecas) -> None:
    executor, _, rastreador = pecas
    projeto, chaves = plano(executor)
    executor.rodar(
        MudarStatusDoPassoDaSnT,
        projeto_id=projeto.id,
        no_id=chaves["1.1"],
        status=StatusDoPasso.VALIDADO,
    )
    span = [s for s in rastreador.spans if s.nome == "caso_de_uso.mudar_status_do_passo_da_snt"][-1]
    print(f"atributos={span.atributos}")
    assert span.atributos["toc.status_do_passo"] == "validado"


def test_a_recusa_tambem_deixa_span_marcado_como_erro(pecas) -> None:
    """"Traço de toda ação, inclusive recusas" — o span sai marcado, e a exceção sobe."""
    executor, _, rastreador = pecas
    projeto, chaves = plano(executor)
    with pytest.raises(Exception):
        executor.rodar(
            MoverPassoDaSnT,
            projeto_id=projeto.id,
            no_id=chaves["1"],
            novo_pai_id=chaves["1.1.1"],
        )
    span = rastreador.spans[-1]
    print(f"span da recusa: {span.nome} · {span.atributos}")
    assert span.atributos["toc.resultado"] == "erro"
    assert span.atributos["toc.erro"] == "MovimentoRecusado"


def test_o_autor_da_mudanca_de_status_vem_do_principal_e_nao_do_pedido(pecas) -> None:
    """RN-03: quem mudou é a identidade da fundação — na linhagem não havia autor nenhum."""
    import inspect

    executor, repositorio, _ = pecas
    projeto, chaves = plano(executor)
    executor.rodar(
        MudarStatusDoPassoDaSnT,
        projeto_id=projeto.id,
        no_id=chaves["1.1"],
        status=StatusDoPasso.VALIDADO,
    )
    arvore = repositorio.obter_snt("instituicao-horizonte", projeto.id)
    eventos = [e for e in arvore.projeto.eventos if getattr(e, "autor", None)]
    print(f"autor no evento={eventos[-1].autor!r} · parâmetros do caso de uso="
          f"{list(inspect.signature(MudarStatusDoPassoDaSnT.executar).parameters)}")
    assert eventos[-1].autor == "u-facilitadora"
    assert "autor" not in inspect.signature(MudarStatusDoPassoDaSnT.executar).parameters


# ---------------------------------------------------------------------------------------
# Autorização no caso de uso (§B.7.2) e isolamento por inquilino
# ---------------------------------------------------------------------------------------


def test_principal_so_leitura_abre_a_arvore_e_nao_escreve(pecas) -> None:
    executor, repositorio, rastreador = pecas
    projeto, chaves = plano(executor)
    leitor = Executor(
        principal=principal(capabilities=(TOC_LEITURA,)),
        rastreador=rastreador,
        repositorio=repositorio,
        relogio=RelogioFalso(AGORA),
    )
    arvore = leitor.rodar(AbrirProjetoSnT, projeto_id=projeto.id)
    pendencias = leitor.rodar(PendenciasDaSnT, projeto_id=projeto.id)
    documento = leitor.rodar(ExportarSnT, projeto_id=projeto.id)
    previa = leitor.rodar(
        PreverRenumeracao, projeto_id=projeto.id, no_id=chaves["1.1"], novo_pai_id=None
    )
    print(
        f"leitura ok: passos={len(arvore.passos)} pendências={pendencias.total} "
        f"export={len(documento['passos'])} prévia={len(previa)}"
    )
    negadas = 0
    for caso, argumentos in (
        (AdicionarPassoDaSnT, {"estrategia": "não deveria entrar"}),
        (EditarMetaGlobal, {"meta_global": "outra meta"}),
        (EditarPassoDaSnT, {"no_id": chaves["1"], "tatica": "nova"}),
        (EditarPremissasDoPasso, {"no_id": chaves["1"], "paralela": "x"}),
        (ExcluirSubarvore, {"no_id": chaves["1.1"]}),
        (MudarStatusDoPassoDaSnT, {"no_id": chaves["1"], "status": StatusDoPasso.VALIDADO}),
        (MoverPassoDaSnT, {"no_id": chaves["1.1"], "novo_pai_id": None}),
    ):
        with pytest.raises(AutorizacaoNegada) as erro:
            leitor.rodar(caso, projeto_id=projeto.id, **argumentos)
        assert erro.value.capability == TOC_ESCRITA
        negadas += 1
    print(f"escritas recusadas para principal só-leitura: {negadas} de 7")
    assert negadas == 7


def test_arvore_de_outro_inquilino_nao_existe(pecas) -> None:
    executor, repositorio, rastreador = pecas
    projeto, _ = plano(executor)
    outro = Executor(
        principal=principal(inquilino="instituicao-aurora"),
        rastreador=rastreador,
        repositorio=repositorio,
        relogio=RelogioFalso(AGORA),
    )
    with pytest.raises(NaoEncontrado):
        outro.rodar(AbrirProjetoSnT, projeto_id=projeto.id)
    print("projeto de outro inquilino: NaoEncontrado (nunca 'proibido')")


def test_abrir_projeto_que_nao_e_snt_devolve_nao_encontrado(pecas) -> None:
    executor, _, _ = pecas
    with pytest.raises(NaoEncontrado):
        executor.rodar(AbrirProjetoSnT, projeto_id=uuid4())


# ---------------------------------------------------------------------------------------
# As operações do módulo, pela borda de aplicação
# ---------------------------------------------------------------------------------------


def test_editar_meta_global_passo_e_premissas_pelo_executor(pecas) -> None:
    executor, _, _ = pecas
    projeto, chaves = plano(executor)
    executor.rodar(EditarMetaGlobal, projeto_id=projeto.id, meta_global="Meta revista")
    executor.rodar(
        EditarPassoDaSnT,
        projeto_id=projeto.id,
        no_id=chaves["1.3"],
        tatica="Abrir vagas por lote",
        categoria=CategoriaDoPasso.VCD,
    )
    executor.rodar(
        EditarPremissasDoPasso,
        projeto_id=projeto.id,
        no_id=chaves["1.1"],
        necessidade_ao_pai="sem cortar a espera, a fila dobra junto",
    )
    arvore = executor.rodar(AbrirProjetoSnT, projeto_id=projeto.id)
    print(
        f"meta={arvore.meta_global!r} · categoria={arvore.ficha(chaves['1.3']).categoria.value!r}"
    )
    assert arvore.meta_global == "Meta revista"
    assert arvore.ficha(chaves["1.3"]).categoria is CategoriaDoPasso.VCD
    assert arvore.ficha(chaves["1.1"]).premissas.necessidade_ao_pai.startswith("sem cortar")


def test_prever_renumeracao_nao_muta_a_arvore(pecas) -> None:
    """RI-05: a pré-visualização mostra os números novos ANTES de confirmar."""
    executor, _, _ = pecas
    projeto, chaves = plano(executor)
    antes = executor.rodar(AbrirProjetoSnT, projeto_id=projeto.id).numeros()
    previa = executor.rodar(
        PreverRenumeracao, projeto_id=projeto.id, no_id=chaves["1.1"], novo_pai_id=None
    )
    depois = executor.rodar(AbrirProjetoSnT, projeto_id=projeto.id).numeros()
    print(f"prévia: 1.1 → {previa[chaves['1.1']]} · árvore continua com {depois[chaves['1.1']]}")
    assert previa[chaves["1.1"]] == "2"
    assert antes == depois


def test_exportar_devolve_o_documento_canonico_sem_numero(pecas) -> None:
    import json

    executor, _, _ = pecas
    projeto, _ = plano(executor)
    documento = executor.rodar(ExportarSnT, projeto_id=projeto.id)
    print(f"versao={documento['versao']!r} passos={len(documento['passos'])}")
    assert documento["versao"] == "toc.snt/1"
    assert "numero" not in json.dumps(documento, ensure_ascii=False)


def test_as_pendencias_saem_do_mesmo_servico_de_dominio(pecas) -> None:
    executor, _, rastreador = pecas
    projeto, _ = plano(executor)
    resultado = executor.rodar(PendenciasDaSnT, projeto_id=projeto.id)
    span = [s for s in rastreador.spans if s.nome == "caso_de_uso.pendencias_da_snt"][-1]
    print(f"pendências={resultado.total} sobre {resultado.passos_examinados} passos · {span.atributos}")
    assert span.atributos["toc.passos"] == 7
    assert span.atributos["toc.pendencias"] == resultado.total
