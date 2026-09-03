#!/usr/bin/env bash
# check-caminhos.sh — fitness function for rule R4 (CLAUDE.md): a cited path is an open path.
#
# Why it exists: the method's check-links.sh deletes every backtick span BEFORE looking for
# links — rightly, because `![x](y)` inside backticks is an example, not a link. Side effect:
# the way this documentation cites files THE MOST is the one no gate ever checks. The sister
# project paid for this (a journey cited a file that did not exist and the gate answered
# green over 43 links). This gate looks at exactly what that one does not: backticked paths.
#
# Usage: scripts/check-caminhos.sh [root]     (default: the repository root)
set -uo pipefail
RAIZ="${1:-$(cd "$(dirname "$0")/.." && pwd)}"
cd "$RAIZ" || { echo "✗ raiz inexistente: $RAIZ" >&2; exit 2; }

python3 - <<'PY'
import os, re, sys

# Our documentation only. Roots per rule R4: docs/, specs/, mensagens/ + top-level files.
RAIZES = ("docs", "specs", "mensagens")
ARQUIVOS = [a for a in ("CLAUDE.md", "README.md", "CHANGELOG.md") if os.path.exists(a)]
for raiz in RAIZES:
    for base, _, nomes in os.walk(raiz):
        ARQUIVOS += [os.path.join(base, n) for n in nomes if n.endswith(".md")]

# The installed Maestro surface is not ours to police (method's ADR 0014): it travels in
# English and describes the method's repository. constitution.md IS ours and stays in.
FORA = (
    "docs/governance/principles.md",
    "docs/governance/operating-model.md",
    "docs/governance/axioms.md",
    "docs/governance/artifacts.md",
    "docs/governance/glossary.md",
    "docs/governance/MAESTRO-LICENSE",
    "docs/governance/MAESTRO-THIRD-PARTY-NOTICES.md",
)
ARQUIVOS = [a for a in ARQUIVOS if a not in FORA]

# A path: has a slash, ends in a known extension (optionally with :line[-line] suffix),
# or is a directory citation ending in "/".
PADRAO_ARQ = re.compile(
    r"`([^`\s]+\.(?:md|json|jsonl|py|js|mjs|ts|tsx|css|html|sh|toml|yaml|yml|txt|sql|csv|svg|png))"
    r"(?::[0-9][0-9,–-]*)?`")
PADRAO_DIR = re.compile(r"`([^`\s]*/[^`\s]*/)`|`([^`\s]+/)`")

# What is NOT ours to resolve, and why. One line per exemption WITH the reason — without
# the written reason the list becomes a rug and the gate lies again (sister's lesson).
ISENTOS = (
    ("gestaodeprioridades/", "arquivo da irmã GHDaru/gestaodeprioridades, leitura apenas (P1)"),
    ("ghdaru/",              "arquivo da fundação GHDaru/ghdaru, leitura apenas (P1)"),
    ("apps/",                "caminho curto dentro do GHDaru/ghdaru, leitura apenas (P1)"),
    ("protocolos/",          "arquivo do GHDaru/protocolos (Padrão APH), leitura apenas (P1)"),
    ("padrao/",              "norma do GHDaru/protocolos citada por caminho curto (P1)"),
    ("conformidade/",        "suíte do GHDaru/protocolos, leitura apenas (P1)"),
    ("maestro/",             "arquivo do canônico GHDaru/maestro, leitura apenas (P1)"),
    ("bin/",                 "instalador do GHDaru/maestro (bin/maestro), não viaja para cá"),
    ("tocbuilderv3/",        "4ª geração da linhagem TOC-Builder, leitura apenas (P1)"),
    ("TOC-Builder",          "linhagem TOC-Builder (1ª–3ª gerações), leitura apenas (P1)"),
    ("toc_backend/",         "repositório natimorto da linhagem, leitura apenas (P1)"),
    ("toc_frontend/",        "repositório natimorto da linhagem, leitura apenas (P1)"),
    ("daruskills/",          "fonte do gerador vendorizado (ADR 0008), leitura apenas (P1)"),
    ("ECS/",                 "repositório de referência de profundidade, leitura apenas (P1)"),
    ("docs/integration/",    "documentação do GHDaru/ghdaru — em inglês; a nossa é docs/integracao/"),
    ("services/",            "caminho curto do tocbuilderv3 (violação canônica citada no P7)"),
)

quebrados, conferidos, isentos, moldes = [], 0, 0, 0
examinados = sorted(set(a for a in ARQUIVOS if os.path.exists(a)))

def classifica(arq, n, alvo):
    global conferidos, isentos, moldes
    alvo = alvo.split("#")[0]
    if "/" not in alvo:
        return
    # `<x>`, `*` and `NNN` are templates; `...` is a deliberate elision.
    if any(t in alvo for t in ("<", "*", "...", "NNN")):
        moldes += 1
        return
    if any(alvo.startswith(p) or alvo == p for p, _ in ISENTOS):
        isentos += 1
        return
    conferidos += 1
    relativo = os.path.normpath(os.path.join(os.path.dirname(arq), alvo))
    if not (os.path.exists(alvo) or os.path.exists(relativo)):
        quebrados.append(f"{arq}:{n}  {alvo}")

for arq in examinados:
    for n, linha in enumerate(open(arq, encoding="utf-8"), 1):
        for m in PADRAO_ARQ.finditer(linha):
            classifica(arq, n, m.group(1))
        for m in PADRAO_DIR.finditer(linha):
            classifica(arq, n, m.group(1) or m.group(2))

# Rule R2: green states HOW MUCH it examined.
print("── Caminhos citados entre crases (regra R4) ──")
print(f"  arquivos varridos: {len(examinados)}")
print(f"  caminhos conferidos: {conferidos}  ·  isentos declarados: {isentos}"
      f"  ·  moldes ignorados: {moldes}")

if quebrados:
    print(f"\n✗ {len(quebrados)} caminho(s) citado(s) que não existem:", file=sys.stderr)
    for q in quebrados:
        print(f"    {q}", file=sys.stderr)
    print("\n  Corrija o caminho, ou — se for de outro repositório — declare a isenção "
          "com o motivo em ISENTOS.", file=sys.stderr)
    sys.exit(1)

print("\n✓ todo caminho citado entre crases existe.")
PY
