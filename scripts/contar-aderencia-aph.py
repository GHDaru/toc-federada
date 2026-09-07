#!/usr/bin/env python3
"""contar-aderencia-aph.py — conta o status por linha da matriz de aderência ao APH.

Siglas, uma vez: **APH** — Aplicação ↔ Harness (o padrão da fronteira) · **R1** — a regra
"verifique antes de afirmar" do `CLAUDE.md` · **R2** — "portão verde diz quanto examinou".

Por que existe: a matriz `docs/integracao/aderencia-aph.md` abre com uma tabela de
distribuição ("47 atendidos, 1 parcial, …"). Digitar esses números à mão é exatamente o que
a regra R1 proíbe, e contá-los com `grep -o` sobre o arquivo inteiro **mente**: a legenda,
a prosa e o registro de revisões também contêm as marcas, e o `grep` devolveu 52 onde as
tabelas têm 47. Este script conta **só as linhas de requisito** das três tabelas — as que
começam com `| APH-` ou `| §B` — e imprime o denominador (R2).

Ele não julga: não decide se um status está certo, só conta o que está escrito. Quem
confere se `● atendido` tem mesmo caminho e teste é a revisão independente.

Uso:  scripts/contar-aderencia-aph.py [caminho-da-matriz]
Saída: uma linha por tabela e uma de total. Código de saída 0; 1 se o arquivo não existir.
"""
from __future__ import annotations

import re
import sys
from collections import Counter
from pathlib import Path

MARCAS = ("● atendido", "◑ parcial", "○ planejado", "○ não emitido",
          "✦ delegado", "✗ fora do alvo")


def main() -> int:
    alvo = Path(sys.argv[1] if len(sys.argv) > 1 else "docs/integracao/aderencia-aph.md")
    if not alvo.is_file():
        print(f"✗ matriz não encontrada: {alvo}", file=sys.stderr)
        return 1

    texto = alvo.read_text(encoding="utf-8")
    total: Counter[str] = Counter()
    tabelas = 0

    for secao in re.split(r"^## ", texto, flags=re.M):
        titulo = secao.split("\n", 1)[0]
        if not titulo.startswith(("Nível 1", "Nível 2", "Anexo B")):
            continue
        tabelas += 1
        conta: Counter[str] = Counter()
        linhas = [l for l in secao.splitlines() if re.match(r"^\| (APH-|§B)", l)]
        sem_marca = []
        for linha in linhas:
            for m in MARCAS:
                if m in linha:
                    conta[m] += 1
                    break
            else:
                sem_marca.append(linha.split("|")[1].strip())
        print(f"{titulo.split(' —')[0]:<9} linhas={len(linhas):<3} " +
              "  ".join(f"{m}={conta[m]}" for m in MARCAS if conta[m]))
        if sem_marca:
            print(f"  ✗ sem status reconhecido: {', '.join(sem_marca)}")
        total.update(conta)

    print(f"{'TOTAL':<9} linhas={sum(total.values()):<3} " +
          "  ".join(f"{m}={total[m]}" for m in MARCAS if total[m]))
    print(f"tabelas examinadas: {tabelas}  ·  arquivo: {alvo}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
