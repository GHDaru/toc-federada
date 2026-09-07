"""Semeadura da base sintética do ENSAIO DE RESTAURAÇÃO (spec 011, RF-02 e RF-05).

Siglas, uma vez neste arquivo: **ARA** — Árvore da Realidade Atual · **NC** — Nuvem de
Conflito · **UDE** — Efeito Indesejável · **HTTP** — *HyperText Transfer Protocol* ·
**ADR** — *Architecture Decision Record* (Registro de Decisão Arquitetural).

**Por que este arquivo existe, e por que ele é um COMANDO.** A RF-05 é explícita: "a
semeadura da base sintética DEVE ser comando explícito, jamais efeito colateral de tabela
vazia, e NÃO DEVE existir caminho de execução que a dispare em produção". Então ela mora
aqui, num script que alguém digita — e não num `if not projetos: criar_exemplos()` dentro
do arranque, que é o Princípio XIII da constituição da fundação em pessoa.

**Por que ele escreve pela API e não por `INSERT`.** Um ensaio de restauração que semeasse
com `INSERT` direto provaria que o PostgreSQL copia linhas — o que ninguém duvida. O que o
ensaio precisa provar é que **a aplicação volta a funcionar** contra o destino restaurado,
e para isso o dado tem de ter nascido como o dado de verdade nasce: pelos casos de uso,
com as invariantes do domínio aplicadas.

Base 100% sintética (ADR 0006): "Instituição Horizonte", "Facilitadora TOC" — personas
fictícias, nenhum dado real de pessoa.

Uso (chamado por `scripts/ensaio-de-restauracao.sh`):
    python scripts/ensaio/semear.py <quantos-projetos>
Ambiente: `DATABASE_URL`, `TOC_DB_SCHEMA`.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

RAIZ_DA_API = Path(__file__).resolve().parents[2] / "apps" / "api"
sys.path.insert(0, str(RAIZ_DA_API / "src"))

from fastapi.testclient import TestClient  # noqa: E402

from toc_api.http.app import criar_app  # noqa: E402

TOKEN = "ensaio-facilitadora"
IDENTIDADES = {
    TOKEN: {
        "inquilino_id": "instituicao-horizonte",
        "usuario_id": "papel-facilitadora",
        "capabilities": ["toc:read", "toc:write"],
    }
}

UDES = (
    "A taxa de evasão no primeiro semestre é de 22%.",
    "O caixa da instituição fecha o trimestre negativo.",
)
CAUSA = "O acolhimento do primeiro ano não é acompanhado."


def semear(quantos: int) -> dict:
    app = criar_app(
        {
            "DATABASE_URL": os.environ["DATABASE_URL"],
            "TOC_DB_SCHEMA": os.environ["TOC_DB_SCHEMA"],
            # `teste`, e não um ambiente novo: `AMBIENTES_DE_MENTIRA` (em
            # `infra/identidade/falso.py:35`) só admite `desenvolvimento` e `teste`, e
            # inventar um terceiro nome para o ensaio caber seria alargar a fronteira em
            # que uma identidade de mentira responde — pelo motivo errado. O ensaio roda
            # num esquema descartável de um banco descartável; ele é teste.
            "TOC_AMBIENTE": "teste",
            "TOC_IDENTIDADES_FALSAS": json.dumps(IDENTIDADES),
        }
    )
    cliente = TestClient(app)
    cliente.headers["Authorization"] = f"Bearer {TOKEN}"

    criados = []
    for indice in range(quantos):
        ara = cliente.post(
            "/toc/ara/projetos",
            json={"nome": f"Horizonte — realidade atual {indice + 1}"},
        ).json()
        nos = [
            cliente.post(
                f"/toc/ara/projetos/{ara['id']}/efeitos", json={"titulo": texto}
            ).json()
            for texto in (*UDES, CAUSA)
        ]
        for destino in nos[:2]:
            cliente.post(
                f"/toc/ara/projetos/{ara['id']}/arestas",
                json={"origem_id": nos[2]["id"], "destino_id": destino["id"]},
            )
        cliente.post(f"/toc/ara/projetos/{ara['id']}/nos/{nos[0]['id']}/ude", json={})
        cliente.post(
            f"/toc/ara/projetos/{ara['id']}/nos/{nos[0]['id']}/pareceres",
            json={
                "favoravel": True,
                "justificativa": "queixa contínua e na esfera da coordenação",
            },
        )
        cliente.put(
            f"/toc/ara/projetos/{ara['id']}/nos/{nos[0]['id']}/status",
            json={"status": "validado"},
        )
        # A cadeia atravessa duas ferramentas: sem isto, o ensaio provaria só que uma
        # tabela volta — e o que a restauração tem de devolver é a ANÁLISE.
        promocao = cliente.post(
            "/toc/cadeia/promocoes",
            json={
                "ara_projeto_id": ara["id"],
                "no_ids": [nos[0]["id"]],
                "nome": f"Dilema da expansão {indice + 1}",
            },
        )
        criados.append({"ara": ara["id"], "nc": promocao.json().get("id")})

    listagem = cliente.get("/toc/projetos").json()
    return {
        "projetos_criados": len(criados),
        "projetos_listados": len(listagem),
        "nomes": sorted(p["nome"] for p in listagem),
        "inquilino": IDENTIDADES[TOKEN]["inquilino_id"],
        "token": TOKEN,
    }


if __name__ == "__main__":
    quantos = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    print(json.dumps(semear(quantos), ensure_ascii=False))
