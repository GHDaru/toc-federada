"""A superfície HTTP da portabilidade — `/toc/portabilidade`, spec 011 (E1.4).

Siglas, uma vez neste arquivo: **ARA** — Árvore da Realidade Atual · **NC** — Nuvem de
Conflito · **HTTP** — *HyperText Transfer Protocol* · **JSON** — *JavaScript Object
Notation* · **RF/RN** — requisito funcional / regra de negócio · **APH** — Aplicação ↔
Harness.

**Duas rotas, e o desenho de cada uma é a decisão:**

- `GET /toc/portabilidade/projetos/{projeto_id}` — a análise INTEIRA a partir de qualquer
  ponto dela. A resposta é o documento canônico do domínio, entregue tal como saiu: um
  modelo de saída aqui seria uma segunda declaração do mesmo formato, e as duas
  divergiriam na primeira seção nova de ferramenta.
- `POST /toc/portabilidade/importacoes` — envia o arquivo. **Um `POST` que cria projetos
  novos e nunca substitui** (RN-05), e por isso responde `201` com o relato do que nasceu.

**A recusa é `422` com o relato campo a campo** (`IMPORT_REFUSED`), e não uma mensagem
solta: a US-15 pede saber "exatamente qual campo está errado", e o contraste medido é o
`alert()` de `tocbuilderv3/components/NodeZoneView.tsx:315`. O código é estável e em caixa
alta porque **o cliente discrimina por código, nunca por mensagem** (§A.7 do Anexo A).

A rota não decide acesso e não conhece repositório: quem verifica a capacidade é a camada
de aplicação (§B.7.2 do Anexo B) — aqui só se traduz JSON em argumento e resultado em
resposta.
"""
from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

from ...aplicacao.portabilidade import ExportarConsolidado, ImportarConsolidado
from ..dependencias import ExecutorDependente
from ..erros import envelope
from ..esquemas import ImportacaoIn, RelatoDeImportacaoOut

roteador = APIRouter(prefix="/toc/portabilidade", tags=["portabilidade"])


@roteador.get("/projetos/{projeto_id}")
def exportar(projeto_id: UUID, executor: ExecutorDependente) -> dict[str, Any]:
    """RF-31: a cadeia inteira num arquivo só, a partir de qualquer elo dela.

    Fora do inquilino a resposta é `404`, nunca `403`: distinguir os dois confirmaria a
    existência do projeto alheio.
    """
    return executor.rodar(ExportarConsolidado, projeto_id=projeto_id)


@roteador.post("/importacoes", status_code=status.HTTP_201_CREATED)
def importar(corpo: ImportacaoIn, executor: ExecutorDependente):
    """RF-25..RF-30: reconhece o formato pelo conteúdo, valida inteiro, e só então grava.

    O `201` só sai quando o relato foi aceito. Recusado, **nada foi criado nem alterado** e
    a resposta é o `422` com um item por defeito — que é o requisito, não um detalhe de
    apresentação.
    """
    resultado = executor.rodar(
        ImportarConsolidado, documento=corpo.documento, teto_de_bytes=corpo.teto_de_bytes
    )
    if not resultado.relato.aceito:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=envelope(
                "IMPORT_REFUSED",
                f"arquivo recusado: {len(resultado.relato.problemas)} problema(s); "
                "nada foi criado nem alterado",
                detalhes={
                    "formato": resultado.formato,
                    "problemas": [
                        {"campo": p.campo, "motivo": p.motivo}
                        for p in resultado.relato.problemas
                    ],
                },
            ),
        )
    return RelatoDeImportacaoOut.de(resultado)
