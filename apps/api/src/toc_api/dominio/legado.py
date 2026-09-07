"""F1.4.3 — o adaptador do formato da quarta geração (spec 011, RF-25..RF-30).

Siglas, uma vez neste arquivo: **ARA** — Árvore da Realidade Atual · **UDE** — Efeito
Indesejável · **JSON** — *JavaScript Object Notation* · **UUID** — identificador único
universal · **IA** — inteligência artificial · **RF/RN** — requisito funcional / regra de
negócio · **ADR** — *Architecture Decision Record* (Registro de Decisão Arquitetural).

**É o `PlanoDeConversao` da spec**: a única peça desta aplicação que conhece o formato
antigo. Trocar ou aposentar o formato legado é trocar este módulo, não a importação — que
é o motivo de ele produzir o **documento canônico** (`toc.consolidado/1`) e parar aí. O
que grava é `exportacao.importar_consolidado`, o mesmo caminho de todo mundo (RF-25: "para
dentro daquele caminho — não uma segunda importação").

**O formato de origem**, medido em `/home/user/tocbuilderv3`:

- `types.ts:55-65` — `AraProject`: `id`, `userId`, `name`, `problemDescription`,
  `createdAt`, `updatedAt`, `nodes`, `edges`, `chatHistory?`.
- `types.ts:9-15` — `Node`: `id`, `position {x,y}`, `data`, `width?`, `height?`.
- `types.ts:38-50` — `NodeData`: `id`, `type` (`EI` — Efeito Indesejável), `title`,
  `description`, `details?`, `aiValidatedDescription?`, `udeValidationData?`,
  `isCollapsed?`.
- `types.ts:17-31` — `Edge`: `id`, `source`, `target`, mais enfeite de desenho.
- `components/NodeZoneView.tsx:186` — o export escreve `{ ...project, chatHistory:
  chatMessages }`: **o diálogo com o modelo viaja dentro do arquivo do projeto**.

**Três decisões, e cada uma tem teste:**

1. **Reconhecimento por assinatura de conteúdo, nunca por nome de arquivo** (RF-25). O
   nome `<nome>_ARA_Export.json` é escolha de quem exporta, e quem baixa renomeia.
2. **Nada é herdado como auditado.** Um nó `EI` entra como UDE com status `pendente`: a
   linhagem não tinha auditoria humana, e importar não pode auditar por ela.
3. **Todo descarte é declarado com o campo e a contagem** (RN-06). São quatro: o
   histórico de conversa (RF-29), a saída de modelo guardada no nó (`aiValidatedDescription`,
   `udeValidationData` — ADR 0007), o `userId` de origem (identidade é do destino) e
   qualquer campo do arquivo que esta aplicação não conheça.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Mapping, Sequence
from uuid import UUID, uuid4

from .ara import FERRAMENTA_ARA
from .exportacao import (
    FORMA_NUCLEO,
    VERSAO_DO_CONSOLIDADO,
    DescarteDeclarado,
    ProblemaDeImportacao,
    RelatoDeImportacao,
)
from .valores import LIMITE_DESCRICAO, LIMITE_TITULO

#: Teto padrão do arquivo aceito (RF-30). É configuração com valor de partida, não lei:
#: quem chama pode apertá-lo. 5 MB (megabytes) cobrem com folga uma ARA de 200 nós e 300
#: arestas — o tamanho que a RNF-08 usa como referência de desempenho.
LIMITE_PADRAO_DE_TAMANHO = 5 * 1024 * 1024

#: Os campos do arquivo antigo que esta aplicação SABE ler. Qualquer outro é descartado e
#: declarado — nunca ignorado em silêncio.
CAMPOS_CONHECIDOS = frozenset(
    {"id", "userId", "name", "problemDescription", "createdAt", "updatedAt", "nodes", "edges", "chatHistory"}
)

#: O mesmo, para o bloco `data` de cada nó.
CAMPOS_DO_NO = frozenset(
    {"id", "type", "title", "description", "details", "isCollapsed", "pos_x", "pos_y"}
)

#: Saída de modelo guardada dentro do nó pela geração anterior. Não entra (ADR 0007).
CAMPOS_DE_MODELO = ("aiValidatedDescription", "udeValidationData")

#: `NodeType.EI` (`tocbuilderv3/types.ts:34-36`) — Efeito Indesejável.
TIPO_EFEITO_INDESEJAVEL = "EI"

INSTANTE_PADRAO = datetime(1970, 1, 1, tzinfo=timezone.utc)


def reconhecer_legado(dado: Any) -> bool:
    """RF-25: assinatura de CONTEÚDO — nome de arquivo não é evidência de formato.

    A assinatura é a que só o formato antigo tem: um projeto com `nodes` e `edges` em
    lista, nós com bloco `data` contendo `title`, e **sem** o campo `versao` do formato
    próprio desta aplicação.
    """
    if not isinstance(dado, Mapping):
        return False
    if "versao" in dado:
        return False
    nos = dado.get("nodes")
    arestas = dado.get("edges")
    if not isinstance(nos, list) or not isinstance(arestas, list):
        return False
    if not isinstance(dado.get("name"), str):
        return False
    # **Ao menos um** nó com `data.title`, e não todos: um arquivo antigo com um nó
    # estragado continua sendo um arquivo antigo, e quem tem de dizer isso é o relato
    # campo a campo (RF-27) — não uma recusa genérica de "formato não reconhecido", que
    # é justamente a caixa de alerta que este módulo existe para substituir.
    return not nos or any(
        isinstance(no, Mapping) and isinstance(no.get("data"), Mapping) and "title" in no["data"]
        for no in nos
    )


def converter_legado(
    dado: Any,
    *,
    teto_de_bytes: int = LIMITE_PADRAO_DE_TAMANHO,
    novo_id=uuid4,
) -> tuple[dict | None, RelatoDeImportacao]:
    """Converte o arquivo antigo no documento canônico — ou recusa, campo a campo.

    Devolve `(documento, relato)`. Com qualquer problema, `documento` é `None`: **sem
    relato aceito não há escrita**, e escrever a metade de um arquivo inválido é o que a
    RF-27 proíbe. Função pura: não lê relógio, não gera efeito e não muta o que recebeu.
    """
    problemas: list[ProblemaDeImportacao] = []
    descartes: list[DescarteDeclarado] = []

    tamanho = len(json.dumps(dado, ensure_ascii=False).encode("utf-8")) if dado is not None else 0
    if tamanho > teto_de_bytes:
        return None, RelatoDeImportacao(
            problemas=(
                ProblemaDeImportacao(
                    "documento",
                    f"o arquivo tem {tamanho} bytes e o teto configurado é de "
                    f"{teto_de_bytes} bytes",
                ),
            )
        )

    if not reconhecer_legado(dado):
        return None, RelatoDeImportacao(
            problemas=(
                ProblemaDeImportacao(
                    "documento",
                    "não tem a assinatura do formato da quarta geração (projeto com "
                    "`nodes` e `edges`, cada nó com `data.title`)",
                ),
            )
        )

    nome = str(dado.get("name") or "").strip()
    if not nome:
        problemas.append(ProblemaDeImportacao("name", "o nome do projeto é obrigatório"))

    _declarar_descartes_do_topo(dado, descartes)

    identidade: dict[str, str] = {}
    nos: list[dict] = []
    udes: dict[str, dict] = {}
    status: dict[str, str] = {}
    for posicao, bruto in enumerate(dado["nodes"]):
        _converter_no(bruto, posicao, identidade, nos, udes, status, problemas, descartes, novo_id)

    arestas: list[dict] = []
    pares: set[tuple[str, str]] = set()
    for posicao, bruto in enumerate(dado["edges"]):
        _converter_aresta(bruto, posicao, identidade, arestas, pares, problemas, novo_id)

    if problemas:
        return None, RelatoDeImportacao(
            problemas=tuple(problemas), descartes=tuple(descartes)
        )

    entrada = {
        "id": str(novo_id()),
        "ferramenta": FERRAMENTA_ARA,
        "forma": FORMA_NUCLEO,
        "nome": nome,
        "descricao_do_problema": str(dado.get("problemDescription") or "")[:LIMITE_DESCRICAO],
        "criado_em": _instante(dado.get("createdAt")),
        "alterado_em": _instante(dado.get("updatedAt")),
        "nos": nos,
        "arestas": arestas,
        "secao": {
            "udes": udes,
            "status": status,
            "pareceres": {},
            "exames": {},
            "conectores": [],
        },
    }
    documento = {
        "versao": VERSAO_DO_CONSOLIDADO,
        "exportado_em": _instante(dado.get("updatedAt")),
        "projetos": [entrada],
        "vinculos": [],
    }
    contagens = {
        "projetos": 1,
        "nos": len(nos),
        "arestas": len(arestas),
        "udes": len(udes),
        "vinculos": 0,
    }
    return documento, RelatoDeImportacao(contagens=contagens, descartes=tuple(descartes))


# ---------------------------------------------------------------------------------------


def _declarar_descartes_do_topo(dado: Mapping[str, Any], descartes: list[DescarteDeclarado]) -> None:
    conversa = dado.get("chatHistory")
    if isinstance(conversa, Sequence) and not isinstance(conversa, (str, bytes)) and conversa:
        descartes.append(
            DescarteDeclarado(
                "chatHistory",
                "histórico de conversa com o modelo: não entra no banco desta aplicação "
                "sem decisão de retenção (spec 011, § Fora de escopo)",
                len(conversa),
            )
        )
    if dado.get("userId"):
        descartes.append(
            DescarteDeclarado(
                "userId",
                "a identidade é de quem importa, nunca do arquivo",
            )
        )
    for campo in sorted(set(dado) - CAMPOS_CONHECIDOS):
        descartes.append(
            DescarteDeclarado(campo, "campo que esta aplicação não conhece no formato antigo")
        )


def _converter_no(
    bruto: Any,
    posicao: int,
    identidade: dict[str, str],
    nos: list[dict],
    udes: dict[str, dict],
    status: dict[str, str],
    problemas: list[ProblemaDeImportacao],
    descartes: list[DescarteDeclarado],
    novo_id,
) -> None:
    caminho = f"nodes[{posicao}]"
    if not isinstance(bruto, Mapping):
        problemas.append(ProblemaDeImportacao(caminho, "esperava um objeto de nó"))
        return
    # O identificador é registrado ANTES de qualquer outra conferência do nó, e por um
    # motivo: sem isto, um nó sem título faria as arestas que chegam nele reportarem "nó
    # inexistente" também — um defeito virando três itens no relato. O relato tem de ter
    # uma linha por defeito real, ou quem lê corrige o sintoma errado.
    original = str(bruto.get("id") or (bruto.get("data") or {}).get("id") or "")
    if not original:
        problemas.append(ProblemaDeImportacao(f"{caminho}.id", "o nó não tem identificador"))
        return
    if original in identidade:
        problemas.append(
            ProblemaDeImportacao(f"{caminho}.id", f"o identificador {original!r} aparece duas vezes")
        )
        return
    identidade[original] = str(novo_id())

    dados = bruto.get("data")
    if not isinstance(dados, Mapping):
        problemas.append(
            ProblemaDeImportacao(f"{caminho}.data", "o nó não tem o bloco de dados do formato antigo")
        )
        return
    titulo = str(dados.get("title") or "").strip()
    if not titulo:
        problemas.append(
            ProblemaDeImportacao(f"{caminho}.data.title", "todo nó precisa de título")
        )
        return
    if len(titulo) > LIMITE_TITULO:
        problemas.append(
            ProblemaDeImportacao(
                f"{caminho}.data.title",
                f"título com {len(titulo)} caracteres; o limite é {LIMITE_TITULO}",
            )
        )
        return

    for campo in CAMPOS_DE_MODELO:
        if dados.get(campo):
            _somar_descarte(descartes, f"nodes[].data.{campo}", "saída de modelo da geração anterior não entra como conteúdo (ADR 0007)")
    for campo in sorted(set(dados) - CAMPOS_DO_NO - set(CAMPOS_DE_MODELO)):
        _somar_descarte(descartes, f"nodes[].data.{campo}", "campo que esta aplicação não conhece no formato antigo")

    posicao_no_canvas = bruto.get("position") if isinstance(bruto.get("position"), Mapping) else {}
    nos.append(
        {
            "id": identidade[original],
            "titulo": titulo,
            "descricao": str(dados.get("description") or "")[:LIMITE_DESCRICAO],
            "tipo": "generico",
            "posicao": {
                "x": _numero(posicao_no_canvas.get("x")),
                "y": _numero(posicao_no_canvas.get("y")),
            },
            "recolhido": bool(dados.get("isCollapsed")),
        }
    )
    if str(dados.get("type") or "") == TIPO_EFEITO_INDESEJAVEL:
        # A ficha nasce VAZIA e o status `pendente`: a linhagem não auditava, e importar
        # não audita por ela (RN-13 do M4 — "a cadeia só avança sobre material auditado").
        udes[identidade[original]] = {}
        status[identidade[original]] = "pendente"


def _converter_aresta(
    bruto: Any,
    posicao: int,
    identidade: dict[str, str],
    arestas: list[dict],
    pares: set[tuple[str, str]],
    problemas: list[ProblemaDeImportacao],
    novo_id,
) -> None:
    caminho = f"edges[{posicao}]"
    if not isinstance(bruto, Mapping):
        problemas.append(ProblemaDeImportacao(caminho, "esperava um objeto de aresta"))
        return
    origem = str(bruto.get("source") or "")
    destino = str(bruto.get("target") or "")
    faltou = False
    for campo, valor in (("source", origem), ("target", destino)):
        if valor not in identidade:
            problemas.append(
                ProblemaDeImportacao(
                    f"{caminho}.{campo}",
                    f"aponta para o nó {valor!r}, que não existe neste arquivo",
                )
            )
            faltou = True
    if faltou:
        return
    if origem == destino:
        problemas.append(
            ProblemaDeImportacao(caminho, "auto-laço: a aresta liga um nó a ele mesmo")
        )
        return
    if (origem, destino) in pares:
        problemas.append(
            ProblemaDeImportacao(caminho, "a mesma dupla de nós já tem aresta neste sentido")
        )
        return
    pares.add((origem, destino))
    arestas.append(
        {
            "id": str(novo_id()),
            "origem_id": identidade[origem],
            "destino_id": identidade[destino],
            # O `label` do formato antigo é nó de interface (`ReactNode`), não texto
            # garantido; só entra quando é texto de verdade.
            "rotulo": str(bruto["label"])[:200] if isinstance(bruto.get("label"), str) else "",
        }
    )


def _somar_descarte(descartes: list[DescarteDeclarado], campo: str, motivo: str) -> None:
    """Um descarte por CAMPO, com a contagem de quantas vezes ele apareceu."""
    for posicao, existente in enumerate(descartes):
        if existente.campo == campo:
            descartes[posicao] = DescarteDeclarado(campo, motivo, existente.quantidade + 1)
            return
    descartes.append(DescarteDeclarado(campo, motivo, 1))


def _instante(valor: Any) -> str:
    try:
        texto = str(valor).replace("Z", "+00:00")
        return datetime.fromisoformat(texto).isoformat()
    except (ValueError, TypeError):
        return INSTANTE_PADRAO.isoformat()


def _numero(valor: Any) -> float:
    if isinstance(valor, bool) or not isinstance(valor, (int, float)):
        return 0.0
    return float(valor)


__all__ = [
    "CAMPOS_CONHECIDOS",
    "LIMITE_PADRAO_DE_TAMANHO",
    "TIPO_EFEITO_INDESEJAVEL",
    "converter_legado",
    "reconhecer_legado",
]
