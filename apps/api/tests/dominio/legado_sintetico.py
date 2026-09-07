"""O arquivo da quarta geração, gerado por script a partir de personas fictícias.

Siglas, uma vez neste arquivo: **ARA** — Árvore da Realidade Atual · **UDE** — Efeito
Indesejável · **JSON** — *JavaScript Object Notation* · **ADR** — *Architecture Decision
Record* (Registro de Decisão Arquitetural).

**Por que gerado, e não colado.** O ADR 0006 diz que nenhum export real de pessoa entra no
repositório, "nem como caso de teste" (RNF-11 da spec 011). Então a fixture do formato
legado é **construída aqui**, com a forma exata que
`tocbuilderv3/components/NodeZoneView.tsx:186` escreve (`{ ...project, chatHistory:
chatMessages }`) e os tipos de `tocbuilderv3/types.ts:9-65` declaram — e com o conteúdo da
"Instituição Horizonte", que é fictícia.

O `chatHistory` está preenchido de propósito: é ele que o RF-29 manda descartar **e
declarar**. Uma fixture sem ele testaria o caminho fácil.
"""
from __future__ import annotations

from typing import Any


def arquivo_legado(*, com_chat: int = 3) -> dict[str, Any]:
    """Um `<nome>_ARA_Export.json` da quarta geração, válido e completo."""
    documento: dict[str, Any] = {
        "id": "ara-horizonte-01",
        "userId": "usuario-da-geracao-anterior",
        "name": "Realidade atual da Instituição Horizonte",
        "problemDescription": "A evasão do primeiro semestre não cede.",
        "createdAt": "2024-08-02T10:00:00.000Z",
        "updatedAt": "2024-08-02T18:30:00.000Z",
        "nodes": [
            {
                "id": "no-1",
                "position": {"x": 120.0, "y": 40.0},
                "width": 220,
                "height": 90,
                "data": {
                    "id": "no-1",
                    "type": "EI",
                    "title": "A taxa de evasão no primeiro semestre é de 22%.",
                    "description": "medida nas três turmas de ingresso",
                    "isCollapsed": False,
                    "aiValidatedDescription": "texto reescrito pelo modelo da geração anterior",
                    "udeValidationData": {"score": 0.9, "criteria": ["clear"]},
                },
            },
            {
                "id": "no-2",
                "position": {"x": 120.0, "y": 260.0},
                "data": {
                    "id": "no-2",
                    "type": "EI",
                    "title": "O acolhimento do primeiro ano não é acompanhado.",
                    "description": "",
                },
            },
            {
                "id": "no-3",
                "position": {"x": 420.0, "y": 260.0},
                "data": {
                    "id": "no-3",
                    "type": "EI",
                    "title": "A tutoria de pares foi descontinuada.",
                    "description": "",
                    "isCollapsed": True,
                },
            },
        ],
        "edges": [
            {"id": "elo-1", "source": "no-2", "target": "no-1", "label": "leva a"},
            {"id": "elo-2", "source": "no-3", "target": "no-1", "animated": True, "color": "#f00"},
        ],
    }
    if com_chat:
        documento["chatHistory"] = [
            {
                "id": f"msg-{i}",
                "sender": "ia" if i % 2 else "user",
                "text": f"mensagem sintética {i} do diálogo com o modelo",
                "timestamp": "2024-08-02T18:00:00.000Z",
            }
            for i in range(com_chat)
        ]
    return documento
