#!/usr/bin/env bash
# check-jornadas.sh — a Iron Law da skill `living-journey`, virada portão executável.
#
# "Jornada sem captura do build real é ficção — e heurística sem data é ficção vencida."
# Uma frase numa skill não reprova nada. Este script reprova, e mede quatro invariantes:
#
#   J1 · toda captura em docs/jornadas/capturas/ é citada por EXATAMENTE UMA jornada
#        (captura órfã é defeito; captura citada duas vezes esconde qual jornada a
#        governa, e nenhuma das duas fica responsável por regenerá-la);
#   J2 · toda imagem citada por uma jornada EXISTE em disco;
#   J3 · toda jornada declara a avaliação heurística com DATA, e a data é
#        >= a data em que as capturas foram geradas (o manifesto diz qual é).
#        É o passo que a própria skill chama de "o que todo mundo esquece";
#   J4 · toda jornada declara o COMANDO que regenera as capturas dela, e o script
#        citado existe — captura que não regenera apodrece na primeira mudança de tela.
#
# Denominador na saída (regra R2): sem "quanto examinou?", verde não é evidência.
# Prova de que ele reprova: as cinco sabotagens de `scripts/tests/run-sabotagem.sh`.
# Uso: scripts/check-jornadas.sh [raiz]     (padrão: a raiz do repositório)
set -uo pipefail
RAIZ="${1:-$(cd "$(dirname "$0")/.." && pwd)}"
cd "$RAIZ" || { echo "✗ raiz inexistente: $RAIZ" >&2; exit 2; }

python3 - <<'PY'
import json
import os
import re
import sys

RAIZ = "docs/jornadas"
CAPTURAS = os.path.join(RAIZ, "capturas")
MANIFESTO = os.path.join(CAPTURAS, "manifesto.json")

print("── Jornadas vivas: captura, citação e heurística datada (P6) ──")

problemas = []

# Os documentos de jornada são NNN-slug.md; README.md é convenção, não jornada.
jornadas = sorted(
    os.path.join(RAIZ, f)
    for f in os.listdir(RAIZ)
    if re.fullmatch(r"\d{3}-[a-z0-9-]+\.md", f)
)

if not jornadas:
    print("  jornadas encontradas: 0")
    print("\n✗ nenhuma jornada em docs/jornadas/ — o portão não examinou nada.")
    sys.exit(1)

# -- a data das capturas, dita pelo manifesto que o próprio gerador escreve -------------
if not os.path.exists(MANIFESTO):
    print(f"\n✗ {MANIFESTO} não existe — sem manifesto não há data de captura para comparar.")
    sys.exit(1)

manifesto = json.load(open(MANIFESTO, encoding="utf-8"))
data_das_capturas = str(manifesto.get("gerado_em", ""))[:10]
if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", data_das_capturas):
    print(f"\n✗ manifesto sem `gerado_em` em formato de data: {data_das_capturas!r}")
    sys.exit(1)

capturas_em_disco = sorted(
    os.path.relpath(os.path.join(pasta, arq), RAIZ)
    for pasta, _, arqs in os.walk(CAPTURAS)
    for arq in arqs
    if arq.endswith(".png")
)

# -- J1 e J2: citação exata --------------------------------------------------------------
citacoes = {}          # caminho relativo a docs/jornadas -> [jornadas que o citam]
imagens_citadas = 0
for doc in jornadas:
    texto = open(doc, encoding="utf-8").read()
    for alvo in re.findall(r"!\[[^\]]*\]\((capturas/[^)]+\.png)\)", texto):
        imagens_citadas += 1
        citacoes.setdefault(alvo, []).append(os.path.basename(doc))

for caminho in capturas_em_disco:
    quem = citacoes.get(caminho, [])
    if not quem:
        problemas.append(f"J1 captura órfã (nenhuma jornada a cita): {caminho}")
    elif len(quem) > 1:
        problemas.append(f"J1 captura citada por {len(quem)} jornadas ({', '.join(quem)}): {caminho}")

for caminho, quem in sorted(citacoes.items()):
    if caminho not in capturas_em_disco:
        problemas.append(f"J2 imagem citada e inexistente ({quem[0]}): {caminho}")

# -- J3 e J4: heurística datada e comando de regeneração ---------------------------------
heuristicas = 0
comandos = 0
for doc in jornadas:
    texto = open(doc, encoding="utf-8").read()
    nome = os.path.basename(doc)

    achado = re.search(r"^##\s+Avaliação heurística\s+—\s+(\d{4}-\d{2}-\d{2})\s*$", texto, re.M)
    if not achado:
        problemas.append(
            f"J3 {nome}: sem seção '## Avaliação heurística — AAAA-MM-DD' "
            "(heurística sem data é ficção vencida)"
        )
    else:
        heuristicas += 1
        if achado.group(1) < data_das_capturas:
            problemas.append(
                f"J3 {nome}: heurística de {achado.group(1)} é ANTERIOR às capturas de "
                f"{data_das_capturas} — a avaliação fala de um sistema que já mudou"
            )

    comando = re.search(r"node\s+(docs/jornadas/scripts/[\w.-]+\.mjs)", texto)
    if not comando:
        problemas.append(f"J4 {nome}: não declara o comando que regenera as capturas")
    else:
        comandos += 1
        if not os.path.exists(comando.group(1)):
            problemas.append(f"J4 {nome}: o gerador citado não existe: {comando.group(1)}")

print(f"  jornadas examinadas: {len(jornadas)} ({', '.join(os.path.basename(j) for j in jornadas)})")
print(
    f"  capturas em disco: {len(capturas_em_disco)}  ·  citações de imagem: {imagens_citadas}"
    f"  ·  data das capturas (manifesto): {data_das_capturas}"
)
print(
    f"  invariantes: J1 órfã/duplicada · J2 citada e inexistente · J3 heurística datada e"
    f" >= captura · J4 comando de regeneração"
)
print(
    f"  verificações executadas: {len(capturas_em_disco) + imagens_citadas + len(jornadas) * 2}"
    f"  ·  heurísticas datadas: {heuristicas}/{len(jornadas)}"
    f"  ·  comandos de regeneração: {comandos}/{len(jornadas)}"
)

if problemas:
    print()
    for p in problemas:
        print(f"  ✗ {p}")
    print(f"\n✗ {len(problemas)} problema(s) na documentação viva das jornadas.")
    sys.exit(1)

print(
    "\n✓ toda captura é citada por exatamente uma jornada, toda imagem citada existe,"
    "\n  toda jornada traz heurística datada não anterior às capturas e o comando que as regenera."
)
PY
