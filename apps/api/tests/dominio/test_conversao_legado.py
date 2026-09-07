"""F1.4.3–F1.4.5 — o adaptador do formato da quarta geração (spec 011, RF-25..RF-29).

Siglas, uma vez neste arquivo: **ARA** — Árvore da Realidade Atual · **UDE** — Efeito
Indesejável · **JSON** — *JavaScript Object Notation* · **UUID** — identificador único
universal · **IA** — inteligência artificial · **RF/RN** — requisito funcional / regra de
negócio · **ADR** — *Architecture Decision Record*.

**Os três defeitos da linhagem que estes testes fecham**, todos medidos em
`tocbuilderv3/components/NodeZoneView.tsx`:

1. **:314** — validação rasa: `!data.name || !Array.isArray(data.nodes) ||
   !Array.isArray(data.edges)`. Três campos conferidos, o resto passando. Aqui a
   validação é campo a campo, e um arquivo com dois erros produz **dois** itens no relato
   (RF-27).
2. **:315** — o erro chegava por `alert()` do navegador, sem dizer qual campo. Aqui o
   relato é dado: caminho do campo mais motivo.
3. **:317** — `chatHistory: data.chatHistory || []` reintroduzia o diálogo com o modelo
   dentro do projeto criado. Aqui ele é **descartado e declarado**, com a contagem
   (RF-29, RN-06) — o dado não entra no banco desta aplicação.

E o reconhecimento é **por assinatura de conteúdo, nunca pelo nome do arquivo** (RF-25):
o nome `<nome>_ARA_Export.json` é escolha de quem exporta, e quem baixa renomeia.

Base sintética (ADR 0006): "Instituição Horizonte", personas fictícias.
"""
from __future__ import annotations

import json

from toc_api.dominio.ara import ProjetoARA, StatusDeValidacao
from toc_api.dominio.exportacao import VERSAO_DO_CONSOLIDADO, importar_consolidado
from toc_api.dominio.identidade import DonoDoProjeto
from toc_api.dominio.legado import (
    LIMITE_PADRAO_DE_TAMANHO,
    converter_legado,
    reconhecer_legado,
)

from .cadeia_sintetica import DONO
from .legado_sintetico import arquivo_legado

DESTINO = DonoDoProjeto(inquilino_id="instituicao-horizonte", usuario_id="u-facilitadora")


# ---------------------------------------------------------------------------------------
# RF-25 — reconhecimento por assinatura de conteúdo
# ---------------------------------------------------------------------------------------


def test_reconhece_o_formato_legado_pela_forma_do_conteudo() -> None:
    assert reconhecer_legado(arquivo_legado()) is True


def test_nao_reconhece_o_formato_proprio_como_legado() -> None:
    """O consolidado desta aplicação tem versão declarada — não é adivinhado."""
    nosso = {"versao": VERSAO_DO_CONSOLIDADO, "projetos": [], "vinculos": []}
    assert reconhecer_legado(nosso) is False


def test_nao_reconhece_json_qualquer_nem_lista() -> None:
    assert reconhecer_legado({"nodes": "não é lista", "edges": []}) is False
    assert reconhecer_legado([1, 2, 3]) is False
    assert reconhecer_legado({"name": "sem nós"}) is False


# ---------------------------------------------------------------------------------------
# RF-26 — conversão para o formato canônico, como domínio puro
# ---------------------------------------------------------------------------------------


def test_converte_nos_arestas_e_metadados_para_o_documento_canonico() -> None:
    documento, relato = converter_legado(arquivo_legado())

    print(f"contagens: {dict(relato.contagens)}")
    assert relato.aceito
    assert documento["versao"] == VERSAO_DO_CONSOLIDADO
    entrada = documento["projetos"][0]
    assert entrada["ferramenta"] == "ara"
    assert entrada["nome"] == "Realidade atual da Instituição Horizonte"
    assert entrada["descricao_do_problema"] == "A evasão do primeiro semestre não cede."
    assert len(entrada["nos"]) == 3 and len(entrada["arestas"]) == 2
    assert relato.contagens["nos"] == 3 and relato.contagens["arestas"] == 2


def test_o_identificador_do_arquivo_antigo_nao_e_um_uuid_e_vira_um() -> None:
    documento, _ = converter_legado(arquivo_legado())
    ids = [no["id"] for no in documento["projetos"][0]["nos"]]
    print(f"identificadores convertidos: {ids[:1]}…")
    assert all(len(i) == 36 for i in ids)
    # A aresta continua ligando os MESMOS dois nós depois da conversão.
    aresta = documento["projetos"][0]["arestas"][0]
    assert aresta["origem_id"] in ids and aresta["destino_id"] in ids


def test_o_no_do_tipo_efeito_indesejavel_vira_ude_pendente_e_nao_validado() -> None:
    """O status não é herdado: a linhagem não auditava, e importar não audita por ela."""
    documento, _ = converter_legado(arquivo_legado())
    secao = documento["projetos"][0]["secao"]
    print(f"UDEs convertidos: {len(secao['udes'])} · status: {set(secao['status'].values())}")
    assert len(secao["udes"]) == 3
    assert set(secao["status"].values()) == {"pendente"}


def test_a_posicao_e_o_estado_recolhido_atravessam_a_conversao() -> None:
    documento, _ = converter_legado(arquivo_legado())
    nos = documento["projetos"][0]["nos"]
    primeiro = nos[0]
    recolhido = [n for n in nos if n["recolhido"]]
    print(f"posição do primeiro nó: {primeiro['posicao']} · recolhidos: {len(recolhido)}")
    assert primeiro["posicao"] == {"x": 120.0, "y": 40.0}
    assert len(recolhido) == 1


def test_o_documento_convertido_entra_pelo_mesmo_caminho_de_importacao_do_m1() -> None:
    """RF-25: adaptador PARA DENTRO do caminho do M1, não uma segunda importação."""
    documento, _ = converter_legado(arquivo_legado())

    resultado = importar_consolidado(documento, dono=DESTINO)

    ara: ProjetoARA = resultado.projetos[0]
    print(f"projeto importado: {len(ara.nos)} nó(s), {len(ara.arestas)} aresta(s)")
    assert resultado.relato.aceito
    assert isinstance(ara, ProjetoARA)
    assert len(ara.nos) == 3 and len(ara.arestas) == 2
    assert all(ara.status(u) is StatusDeValidacao.PENDENTE for u in ara.udes)
    assert ara.projeto.dono == DESTINO


# ---------------------------------------------------------------------------------------
# RF-29 / RN-06 — o histórico de conversa é descartado E declarado
# ---------------------------------------------------------------------------------------


def test_o_historico_de_conversa_e_descartado_com_a_contagem_no_relato() -> None:
    documento, relato = converter_legado(arquivo_legado(com_chat=3))

    descarte = next(d for d in relato.descartes if d.campo == "chatHistory")
    print(f"descarte declarado: {descarte.campo} — {descarte.quantidade} mensagem(ns)")
    assert descarte.quantidade == 3
    assert "chatHistory" not in json.dumps(documento)
    assert "mensagem sintética" not in json.dumps(documento)


def test_nada_do_historico_de_conversa_chega_ao_agregado_importado() -> None:
    documento, _ = converter_legado(arquivo_legado(com_chat=5))
    resultado = importar_consolidado(documento, dono=DESTINO)
    bruto = json.dumps(
        [
            {"titulo": n.titulo, "descricao": n.descricao}
            for n in resultado.projetos[0].nos
        ]
    )
    assert "diálogo com o modelo" not in bruto


def test_o_texto_produzido_pelo_modelo_da_geracao_anterior_tambem_e_descartado() -> None:
    """ADR 0007: saída de modelo não entra como conteúdo — e o descarte é declarado."""
    documento, relato = converter_legado(arquivo_legado())

    campos = {d.campo for d in relato.descartes}
    print(f"descartes declarados: {sorted(campos)}")
    assert "nodes[].data.aiValidatedDescription" in campos
    assert "nodes[].data.udeValidationData" in campos
    assert "texto reescrito pelo modelo" not in json.dumps(documento)


def test_o_usuario_do_arquivo_antigo_e_descartado_a_identidade_e_do_destino() -> None:
    documento, relato = converter_legado(arquivo_legado())
    assert any(d.campo == "userId" for d in relato.descartes)
    assert "usuario-da-geracao-anterior" not in json.dumps(documento)


def test_campo_desconhecido_do_arquivo_antigo_e_descartado_com_o_nome_dito() -> None:
    """Descarte silencioso é defeito mesmo quando é a decisão certa (RN-06)."""
    bruto = arquivo_legado()
    bruto["campoQueNaoConhecemos"] = {"qualquer": "coisa"}

    _documento, relato = converter_legado(bruto)

    descarte = next(d for d in relato.descartes if d.campo == "campoQueNaoConhecemos")
    print(f"descarte: {descarte.campo} — {descarte.motivo}")
    assert relato.aceito


# ---------------------------------------------------------------------------------------
# RF-27 — recusa campo a campo, sem criar nada
# ---------------------------------------------------------------------------------------


def test_aresta_orfa_e_no_sem_titulo_produzem_dois_itens_no_relato() -> None:
    """O caso literal da US-15: dois problemas, dois itens, nada criado."""
    bruto = arquivo_legado()
    bruto["edges"][0]["target"] = "no-que-nao-existe"
    bruto["nodes"][1]["data"]["title"] = "   "

    documento, relato = converter_legado(bruto)

    itens = [(p.campo, p.motivo) for p in relato.problemas]
    print(f"problemas: {itens}")
    assert documento is None
    assert len(relato.problemas) == 2
    assert any(c == "edges[0].target" for c, _ in itens)
    assert any(c == "nodes[1].data.title" for c, _ in itens)


def test_arquivo_sem_nome_e_recusado_nomeando_o_campo() -> None:
    bruto = arquivo_legado()
    bruto["name"] = ""

    documento, relato = converter_legado(bruto)

    assert documento is None
    assert relato.problemas[0].campo == "name"


def test_no_sem_bloco_de_dados_e_recusado_em_vez_de_virar_no_vazio() -> None:
    bruto = arquivo_legado()
    del bruto["nodes"][0]["data"]

    documento, relato = converter_legado(bruto)

    print(f"recusa: {relato.problemas[0].campo} — {relato.problemas[0].motivo}")
    assert documento is None
    assert relato.problemas[0].campo == "nodes[0].data"


def test_arquivo_que_nao_e_do_formato_legado_e_recusado_sem_adivinhar() -> None:
    documento, relato = converter_legado({"qualquer": "coisa"})
    assert documento is None
    assert relato.problemas[0].campo == "documento"


def test_duas_arestas_iguais_sao_recusadas_porque_o_m1_nao_as_aceita() -> None:
    """A validação acontece ANTES do efeito: melhor recusar aqui que estourar lá dentro."""
    bruto = arquivo_legado()
    bruto["edges"].append({"id": "elo-3", "source": "no-2", "target": "no-1"})

    documento, relato = converter_legado(bruto)

    print(f"problemas: {[(p.campo, p.motivo) for p in relato.problemas]}")
    assert documento is None
    assert any("edges[2]" in p.campo for p in relato.problemas)


def test_auto_laco_e_recusado_com_o_campo_apontado() -> None:
    bruto = arquivo_legado()
    bruto["edges"].append({"id": "elo-4", "source": "no-1", "target": "no-1"})

    documento, relato = converter_legado(bruto)

    assert documento is None
    assert any("edges[2]" in p.campo for p in relato.problemas)


# ---------------------------------------------------------------------------------------
# RF-30 — teto de tamanho, com código de erro categorizado
# ---------------------------------------------------------------------------------------


def test_arquivo_acima_do_teto_e_recusado_sem_ser_convertido() -> None:
    bruto = arquivo_legado()
    documento, relato = converter_legado(bruto, teto_de_bytes=10)

    print(f"teto padrão: {LIMITE_PADRAO_DE_TAMANHO} bytes · recusa: {relato.problemas[0].motivo}")
    assert documento is None
    assert relato.problemas[0].campo == "documento"
    assert "teto" in relato.problemas[0].motivo


def test_o_teto_padrao_deixa_passar_um_arquivo_normal() -> None:
    documento, relato = converter_legado(arquivo_legado())
    assert documento is not None and relato.aceito


# ---------------------------------------------------------------------------------------
# A conversão é pura: sem rede, sem banco, sem relógio
# ---------------------------------------------------------------------------------------


def test_a_conversao_nao_muta_o_arquivo_recebido() -> None:
    bruto = arquivo_legado()
    copia = json.loads(json.dumps(bruto))

    converter_legado(bruto)

    assert bruto == copia


def test_a_mesma_entrada_produz_a_mesma_estrutura_duas_vezes() -> None:
    """Identificadores mudam (são novos); a estrutura, não."""
    primeiro, _ = converter_legado(arquivo_legado())
    segundo, _ = converter_legado(arquivo_legado())
    from toc_api.dominio.exportacao import esqueleto

    assert esqueleto(primeiro) == esqueleto(segundo)


def test_o_dono_nao_entra_na_conversao_ele_entra_na_importacao() -> None:
    """A conversão é de FORMA; identidade é da fundação e chega depois."""
    documento, _ = converter_legado(arquivo_legado())
    assert DONO.inquilino_id not in json.dumps(documento)


# ---------------------------------------------------------------------------------------
# RNF-08 — 200 nós e 300 arestas em menos de 5 segundos (percentil 95)
# ---------------------------------------------------------------------------------------


def test_arquivo_de_200_nos_e_300_arestas_converte_dentro_do_teto_de_tempo() -> None:
    """A RNF-08 dá o número; este teste o mede, e imprime o que mediu (regra R1).

    O percentil 95 de vinte execuções, e não a melhor de vinte: a melhor mede a máquina
    num instante de sorte. O teto é 5 s; o valor medido vai para o `qa-report.md`.
    """
    import statistics
    import time

    grande = {
        "id": "ara-grande",
        "name": "Instituição Horizonte — árvore grande",
        "problemDescription": "medição de desempenho, base sintética",
        "createdAt": "2024-08-02T10:00:00.000Z",
        "updatedAt": "2024-08-02T18:30:00.000Z",
        "nodes": [
            {
                "id": f"no-{i}",
                "position": {"x": float(i % 20) * 40, "y": float(i // 20) * 40},
                "data": {
                    "id": f"no-{i}",
                    "type": "EI",
                    "title": f"O indicador sintético {i} está fora da meta.",
                    "description": "gerado por script, persona fictícia",
                },
            }
            for i in range(200)
        ],
        "edges": [
            {"id": f"elo-{j}", "source": f"no-{j % 200}", "target": f"no-{(j * 7 + 1) % 200}"}
            for j in range(300)
        ],
    }
    # A geração acima pode produzir auto-laço e par repetido; a conversão os recusaria, e
    # o que se mede aqui é o caminho FELIZ. Filtra-se antes, mantendo 200 nós e o máximo
    # de arestas válidas — o número real medido é impresso.
    vistos: set[tuple[str, str]] = set()
    validas = []
    for aresta in grande["edges"]:
        par = (aresta["source"], aresta["target"])
        if par[0] == par[1] or par in vistos:
            continue
        vistos.add(par)
        validas.append(aresta)
    grande["edges"] = validas

    tempos = []
    for _ in range(20):
        inicio = time.perf_counter()
        documento, relato = converter_legado(grande)
        tempos.append(time.perf_counter() - inicio)
        assert relato.aceito, relato.problemas
    p95 = statistics.quantiles(tempos, n=20)[-1]
    print(
        f"conversão de {len(grande['nodes'])} nós e {len(grande['edges'])} arestas: "
        f"p95 = {p95 * 1000:.1f} ms (20 execuções), mediana {statistics.median(tempos) * 1000:.1f} ms"
    )
    assert len(documento["projetos"][0]["nos"]) == 200
    assert p95 < 5.0


def test_a_importacao_do_arquivo_grande_tambem_cabe_no_teto() -> None:
    """Converter é metade: o que a RNF-08 cronometra é importar o arquivo inteiro."""
    import statistics
    import time

    from toc_api.dominio.exportacao import importar_consolidado

    bruto = arquivo_legado()
    bruto["nodes"] = [
        {
            "id": f"no-{i}",
            "position": {"x": 0.0, "y": float(i)},
            "data": {"id": f"no-{i}", "type": "EI", "title": f"O indicador {i} está fora da meta."},
        }
        for i in range(200)
    ]
    bruto["edges"] = [
        {"id": f"elo-{i}", "source": f"no-{i}", "target": f"no-{i + 1}"} for i in range(199)
    ]
    documento, relato = converter_legado(bruto)
    assert relato.aceito, relato.problemas

    tempos = []
    for _ in range(20):
        inicio = time.perf_counter()
        resultado = importar_consolidado(documento, dono=DESTINO)
        tempos.append(time.perf_counter() - inicio)
        assert resultado.relato.aceito
    p95 = statistics.quantiles(tempos, n=20)[-1]
    print(
        f"importação de 200 nós e 199 arestas: p95 = {p95 * 1000:.1f} ms (20 execuções), "
        f"mediana {statistics.median(tempos) * 1000:.1f} ms"
    )
    assert p95 < 5.0
