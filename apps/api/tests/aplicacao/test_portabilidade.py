"""E1.4 — exportar e importar pela camada de aplicação (spec 011, RF-25..RF-32).

Siglas, uma vez neste arquivo: **ARA** — Árvore da Realidade Atual · **NC** — Nuvem de
Conflito · **ARF** — Árvore da Realidade Futura · **APR** — Árvore de Pré-Requisitos ·
**AT** — Árvore de Transição · **UDE** — Efeito Indesejável · **OTel** — OpenTelemetry ·
**JSON** — *JavaScript Object Notation* · **RF/RNF** — requisito funcional / requisito não
funcional · **ADR** — *Architecture Decision Record*.

O que este arquivo protege, e que nenhum teste de domínio alcança sozinho:

- **a cadeia inteira é encontrada a partir de QUALQUER ponto dela** — exportar a partir da
  Árvore de Transição traz a Árvore da Realidade Atual junto, porque o vínculo é o que
  define a análise (RF-31);
- **cada operação abre span** com grandeza e identificador, **nunca** o texto que a pessoa
  escreveu (P5, ADR 0006);
- **a autorização acontece no caso de uso**, pelo `Executor` (§B.7.2 do Anexo B);
- **o isolamento por inquilino é da consulta**: exportar projeto de outro inquilino é
  `NaoEncontrado`, nunca "proibido";
- **importar não toca no que já existe** (RN-05), e o arquivo recusado não grava nada.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone

import pytest

from toc_api.aplicacao.governanca import (
    TOC_ESCRITA,
    TOC_LEITURA,
    AutorizacaoNegada,
    Executor,
)
from toc_api.aplicacao.portabilidade import ExportarConsolidado, ImportarConsolidado
from toc_api.dominio.erros import NaoEncontrado
from toc_api.dominio.exportacao import VERSAO_DO_CONSOLIDADO, esqueleto
from toc_api.dominio.federacao.principal import principal_de_introspeccao

from ..dominio.cadeia_sintetica import montar_cadeia, montar_snt
from ..dominio.legado_sintetico import arquivo_legado
from .fakes import RastreadorFalso, RelogioFalso
from .fakes_portabilidade import RepositorioDaPortabilidadeFalso, guardar_cadeia

AGORA = datetime(2026, 9, 6, 12, 0, tzinfo=timezone.utc)


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
    repositorio = RepositorioDaPortabilidadeFalso()
    executor = Executor(
        principal=principal(),
        rastreador=rastreador,
        repositorio=repositorio,
        relogio=RelogioFalso(AGORA),
    )
    return executor, repositorio, rastreador


def cadeia_guardada(repositorio):
    cadeia = montar_cadeia(
        dono=principal().dono(),
    )
    guardar_cadeia(repositorio, cadeia)
    return cadeia


# ---------------------------------------------------------------------------------------
# Exportação
# ---------------------------------------------------------------------------------------


def test_exportar_a_partir_de_qualquer_ponto_traz_a_cadeia_inteira(pecas) -> None:
    executor, repositorio, _ = pecas
    cadeia = cadeia_guardada(repositorio)

    documento = executor.rodar(ExportarConsolidado, projeto_id=cadeia.at.projeto.id)

    ferramentas = [p["ferramenta"] for p in documento["projetos"]]
    print(f"exportado a partir da AT: {ferramentas} · vínculos: {len(documento['vinculos'])}")
    assert ferramentas == ["ara", "nc", "arf", "apr", "at"]
    assert len(documento["vinculos"]) == 4
    assert documento["versao"] == VERSAO_DO_CONSOLIDADO


def test_exportar_projeto_sem_vinculo_traz_so_ele(pecas) -> None:
    executor, repositorio, _ = pecas
    arvore = montar_snt(dono=principal().dono())
    repositorio.salvar_snt(arvore)

    documento = executor.rodar(ExportarConsolidado, projeto_id=arvore.projeto.id)

    assert [p["ferramenta"] for p in documento["projetos"]] == ["snt"]
    assert documento["vinculos"] == []


def test_exportar_deixa_span_com_grandeza_e_sem_texto_de_pessoa(pecas) -> None:
    executor, repositorio, rastreador = pecas
    cadeia = cadeia_guardada(repositorio)

    executor.rodar(ExportarConsolidado, projeto_id=cadeia.ara.projeto.id)

    span = rastreador.spans[-1]
    print(f"span={span.nome} atributos={span.atributos}")
    assert span.nome == "caso_de_uso.exportar_consolidado"
    assert span.atributos["toc.projetos_exportados"] == 5
    assert span.atributos["toc.vinculos_exportados"] == 4
    bruto = json.dumps(span.atributos, ensure_ascii=False)
    assert cadeia.ara.projeto.nome not in bruto


def test_exportar_projeto_de_outro_inquilino_e_nao_encontrado(pecas) -> None:
    _executor, repositorio, rastreador = pecas
    cadeia = cadeia_guardada(repositorio)
    de_fora = Executor(
        principal=principal(inquilino="instituicao-aurora"),
        rastreador=rastreador,
        repositorio=repositorio,
        relogio=RelogioFalso(AGORA),
    )

    with pytest.raises(NaoEncontrado):
        de_fora.rodar(ExportarConsolidado, projeto_id=cadeia.ara.projeto.id)


def test_exportar_exige_capacidade_de_leitura(pecas) -> None:
    _executor, repositorio, rastreador = pecas
    cadeia = cadeia_guardada(repositorio)
    sem_nada = Executor(
        principal=principal(capabilities=()),
        rastreador=rastreador,
        repositorio=repositorio,
        relogio=RelogioFalso(AGORA),
    )

    with pytest.raises(AutorizacaoNegada) as erro:
        sem_nada.rodar(ExportarConsolidado, projeto_id=cadeia.ara.projeto.id)
    print(f"recusa: {erro.value}")


# ---------------------------------------------------------------------------------------
# Importação
# ---------------------------------------------------------------------------------------


def test_importar_o_proprio_arquivo_grava_a_cadeia_inteira_com_identidade_nova(pecas) -> None:
    executor, repositorio, _ = pecas
    cadeia = cadeia_guardada(repositorio)
    documento = executor.rodar(ExportarConsolidado, projeto_id=cadeia.ara.projeto.id)
    projetos_antes = set(repositorio.itens)

    resultado = executor.rodar(ImportarConsolidado, documento=documento)

    novos = set(repositorio.itens) - projetos_antes
    print(f"relato: {dict(resultado.relato.contagens)} · projetos novos: {len(novos)}")
    assert resultado.relato.aceito
    assert len(novos) == 5
    assert set(resultado.projetos_criados) == novos
    assert len(repositorio.referencias) == 8  # os 4 originais mais os 4 recriados


def test_importar_nao_destroi_o_que_ja_existe(pecas) -> None:
    """RN-05, e a frase do pedido: reimportar sem destruir o que já existe."""
    executor, repositorio, _ = pecas
    cadeia = cadeia_guardada(repositorio)
    documento = executor.rodar(ExportarConsolidado, projeto_id=cadeia.ara.projeto.id)
    retrato = {
        pid: (p.nome, p.versao, len(p.nos), len(p.arestas))
        for pid, p in repositorio.itens.items()
    }

    executor.rodar(ImportarConsolidado, documento=documento)

    for pid, antes in retrato.items():
        atual = repositorio.itens[pid]
        assert (atual.nome, atual.versao, len(atual.nos), len(atual.arestas)) == antes


def test_a_ida_e_volta_pela_aplicacao_preserva_o_conteudo(pecas) -> None:
    executor, repositorio, _ = pecas
    cadeia = cadeia_guardada(repositorio)
    primeiro = executor.rodar(ExportarConsolidado, projeto_id=cadeia.ara.projeto.id)

    resultado = executor.rodar(ImportarConsolidado, documento=primeiro)
    ara_nova = next(
        pid for pid in resultado.projetos_criados if repositorio.itens[pid].ferramenta == "ara"
    )
    segundo = executor.rodar(ExportarConsolidado, projeto_id=ara_nova)

    print(f"esqueletos iguais: {esqueleto(primeiro) == esqueleto(segundo)}")
    assert esqueleto(primeiro) == esqueleto(segundo)


def test_importar_o_arquivo_da_geracao_anterior_reconhece_e_converte(pecas) -> None:
    executor, repositorio, _ = pecas

    resultado = executor.rodar(ImportarConsolidado, documento=arquivo_legado())

    criado = repositorio.itens[resultado.projetos_criados[0]]
    print(
        f"formato reconhecido: {resultado.formato} · {resultado.relato.contagens['nos']} nó(s) · "
        f"descartes: {[(d.campo, d.quantidade) for d in resultado.relato.descartes]}"
    )
    assert resultado.formato == "legado"
    assert criado.ferramenta == "ara"
    assert len(criado.nos) == 3
    assert any(d.campo == "chatHistory" and d.quantidade == 3 for d in resultado.relato.descartes)


def test_o_historico_de_conversa_nao_e_persistido_em_lugar_nenhum(pecas) -> None:
    """RF-29: nada daquele conteúdo é persistido nem enviado a lugar nenhum."""
    executor, repositorio, _ = pecas

    executor.rodar(ImportarConsolidado, documento=arquivo_legado(com_chat=4))

    gravado = json.dumps(
        [
            {"nome": p.nome, "nos": [{"titulo": n.titulo, "descricao": n.descricao} for n in p.nos]}
            for p in repositorio.itens.values()
        ],
        ensure_ascii=False,
    )
    assert "mensagem sintética" not in gravado
    assert "chatHistory" not in gravado


def test_arquivo_recusado_nao_grava_nada_e_devolve_o_relato(pecas) -> None:
    executor, repositorio, _ = pecas
    bruto = arquivo_legado()
    bruto["edges"][0]["target"] = "no-que-nao-existe"

    resultado = executor.rodar(ImportarConsolidado, documento=bruto)

    print(f"problemas: {[(p.campo, p.motivo) for p in resultado.relato.problemas]}")
    assert not resultado.relato.aceito
    assert resultado.projetos_criados == ()
    assert repositorio.itens == {}


def test_importar_deixa_span_com_as_contagens_e_sem_texto_de_pessoa(pecas) -> None:
    executor, repositorio, rastreador = pecas

    executor.rodar(ImportarConsolidado, documento=arquivo_legado())

    span = rastreador.spans[-1]
    print(f"span={span.nome} atributos={span.atributos}")
    assert span.nome == "caso_de_uso.importar_consolidado"
    assert span.atributos["toc.projetos_importados"] == 1
    assert span.atributos["toc.nos_importados"] == 3
    assert span.atributos["toc.descartes_declarados"] >= 1
    assert span.atributos["toc.formato"] == "legado"
    bruto = json.dumps(span.atributos, ensure_ascii=False)
    assert "evasão" not in bruto


def test_a_recusa_tambem_deixa_traco(pecas) -> None:
    """Brief §4: traço de toda ação, inclusive recusas."""
    executor, _repositorio, rastreador = pecas
    bruto = arquivo_legado()
    bruto["name"] = ""

    executor.rodar(ImportarConsolidado, documento=bruto)

    span = rastreador.spans[-1]
    print(f"span da recusa: {span.atributos}")
    assert span.atributos["toc.problemas"] == 1
    assert span.atributos["toc.projetos_importados"] == 0


def test_importar_exige_capacidade_de_escrita(pecas) -> None:
    _executor, repositorio, rastreador = pecas
    so_leitura = Executor(
        principal=principal(capabilities=(TOC_LEITURA,)),
        rastreador=rastreador,
        repositorio=repositorio,
        relogio=RelogioFalso(AGORA),
    )

    with pytest.raises(AutorizacaoNegada):
        so_leitura.rodar(ImportarConsolidado, documento=arquivo_legado())


def test_o_dono_do_que_foi_importado_e_quem_importou_e_nunca_o_documento(pecas) -> None:
    executor, repositorio, _ = pecas

    resultado = executor.rodar(ImportarConsolidado, documento=arquivo_legado())

    criado = repositorio.itens[resultado.projetos_criados[0]]
    assert criado.dono == principal().dono()
