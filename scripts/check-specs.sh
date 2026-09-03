#!/usr/bin/env bash
# check-specs.sh — fitness function for `specs/NNN-slug/`: the four artifacts exist, the
# spec carries the sections and the requirement types the taxonomy promises, the plan
# carries BOTH Constitution Check tables and declares all five conditional artifacts, and
# the tasks carry the closing tail.
#
# Por que existe: a taxonomia do ADR 0004 (Architecture Decision Record, registro de decisão
# arquitetural) e o formato de spec só valem se alguém os conferir. Sem portão, "a spec está
# no formato" é memória de agente, que relata intenção e não fato. Na irmã
# `gestaodeprioridades`, um plano nasceu com **uma** tabela de Constitution Check em vez de
# duas e ninguém viu — o `CLAUDE.md` de lá teve de ganhar a frase "um plano com apenas a
# primeira está incompleto" porque nenhum script olhava.
#
# ─────────────────────────────────────────────────────────────────────────────────
# A RÉGUA DE PRONTIDÃO (DoR — Definition of Ready, definição de pronto para começar)
# ─────────────────────────────────────────────────────────────────────────────────
# O ADR 0004 fixa uma régua de 100 pontos, com corte em **≥ 80**, para uma spec poder abrir
# ciclo:
#
#   | Dimensão      | Peso | O que a dimensão pergunta                                    |
#   |---------------|------|--------------------------------------------------------------|
#   | Completude    |  30  | as seções obrigatórias existem e estão preenchidas?          |
#   | Testabilidade |  25  | cada critério de aceite tem verificação executável?          |
#   | Clareza       |  20  | requisito em EARS (Easy Approach to Requirements Syntax), sem ambiguidade? |
#   | Escopo        |  15  | o que fica de fora está escrito?                             |
#   | Casos-limite  |  10  | erro, vazio, concorrência e recusa estão previstos?          |
#
# **Este portão não calcula a nota** — e a distinção importa (anti-padrão 13: um portão que
# finge medir julgamento mente com número). Clareza e Casos-limite são leitura humana. O que
# o portão faz é conferir, por máquina, o **piso mecânico** de Completude e o **insumo** de
# Testabilidade e Escopo: as seções existem, os tipos de requisito existem, há linha de
# fonte e de lacuna, e a DoD (Definition of Done, definição de pronto) tem tabela com coluna
# de verificação. Reprovar aqui é reprovar a régua sem chegar a pontuá-la; passar aqui
# **não** dá 80 — dá o direito de ser pontuada pela revisão independente e pelo gate humano.
#
# Isenção declarada (com o motivo escrito, para a lista não virar tapete): o **ciclo 001** é
# documental — não tem interface, não tem módulo de domínio e não entrega tela. As seções de
# módulo e o requisito de interface (RI) não se aplicam a ele; tudo o mais se aplica.
#
# Uso: scripts/check-specs.sh [raiz]     (padrão: a raiz do repositório)
set -uo pipefail
RAIZ="${1:-$(cd "$(dirname "$0")/.." && pwd)}"
cd "$RAIZ" || { echo "✗ raiz inexistente: $RAIZ" >&2; exit 2; }

python3 - <<'PY'
import glob, os, re, sys

BASE = "specs"

ARTEFATOS = ("spec.md", "plan.md", "tasks.md", "qa-report.md")

# Cabeçalhos verbatim — o gerador do site (ADR 0008) depende deles, então o portão os
# confere letra a letra e não por aproximação.
SECOES_SEMPRE = [
    "O quê e por quê",
    "O que entra como dado",
    "Requisitos funcionais",
    "Requisitos não funcionais",
    "Critérios de aceite (DoD)",
    "Fontes",
    "Lacunas e assunções",
    "Clarify",
]
SECOES_DE_MODULO = [
    "Épicos, features e user stories",
    "Entidades e modelo de domínio",
    "Requisitos de interface",
    "Regras de negócio",
    "Integrações",
    "Telas e fluxos",
    "Entregáveis",
]

# ciclo -> (o que não se aplica, o motivo escrito)
ISENTOS = {
    "001": ("seções de módulo e requisito de interface (RI)",
            "ciclo documental: sem interface, sem módulo de domínio e sem tela — "
            "o formato do brief §7 é o da spec de MÓDULO"),
}

ARTEFATOS_CONDICIONAIS = ("research", "data-model", "contracts", "checklist", "ux-design")
CAUDA = ("review", "security", "mutation", "gate")
MAESTRO = ["I.", "II.", "III.", "IV.", "V.", "VI.", "VII.", "VIII."]
PROJETO = ["P1.", "P2.", "P3.", "P4.", "P5.", "P6.", "P7."]

falhas = []
def falha(msg):
    falhas.append(msg)

if not os.path.isdir(BASE):
    print(f"✗ {BASE}/ não existe.", file=sys.stderr)
    sys.exit(2)

dirs = sorted(d for d in glob.glob(os.path.join(BASE, "[0-9][0-9][0-9]-*")) if os.path.isdir(d))
if not dirs:
    print(f"✗ nenhum ciclo em {BASE}/NNN-slug/.", file=sys.stderr)
    sys.exit(2)

def ler(caminho):
    return open(caminho, encoding="utf-8").read()

def cabecalhos(texto, nivel="## "):
    return [l[len(nivel):].strip() for l in texto.splitlines() if l.startswith(nivel)]

conf = dict(artefatos=0, secoes=0, requisitos=0, tabelas=0, art=0, tail=0)
isentos_aplicados = 0

for d in dirs:
    ciclo = os.path.basename(d)[:3]
    isencao = ISENTOS.get(ciclo)

    # ---- 1 · os quatro artefatos --------------------------------------------------
    presentes = {}
    for nome in ARTEFATOS:
        conf["artefatos"] += 1
        caminho = os.path.join(d, nome)
        if os.path.exists(caminho):
            presentes[nome] = ler(caminho)
        else:
            falha(f"{d}/: falta {nome} — os quatro artefatos são o ciclo; três deles é um "
                  f"ciclo que não fecha")

    # ---- 2 · spec.md --------------------------------------------------------------
    if "spec.md" in presentes:
        spec = presentes["spec.md"]
        caminho = f"{d}/spec.md"

        conf["secoes"] += 1
        if not re.search(r"^- \*\*Status\*\*:\s*\S", spec, re.MULTILINE):
            falha(f'{caminho}: não declara "- **Status**:" — sem status ninguém sabe se a '
                  f"spec está aprovada, em rascunho ou vencida")

        h2 = cabecalhos(spec)
        exigidas = list(SECOES_SEMPRE)
        if isencao:
            isentos_aplicados += 1
        else:
            exigidas += SECOES_DE_MODULO
        for sec in exigidas:
            conf["secoes"] += 1
            if sec not in h2:
                falha(f'{caminho}: falta a seção obrigatória "## {sec}" '
                      f"(cabeçalho verbatim — o gerador do site depende dele)")

        for prefixo, nome, isento in (("RF", "requisito funcional", False),
                                      ("RI", "requisito de interface", bool(isencao)),
                                      ("RNF", "requisito não funcional", False)):
            if isento:
                continue
            conf["requisitos"] += 1
            n = len(re.findall(rf"^{prefixo}-\d+:", spec, re.MULTILINE))
            if n == 0:
                falha(f"{caminho}: nenhum {prefixo}- ({nome}) na forma "
                      f"`{prefixo}-01: texto` em linha própria (ADR 0004)")

        # Fonte e lacuna: a metade "prove, não declare" da taxonomia. Uma spec sem fonte
        # é opinião; uma spec sem lacuna declarada é uma spec que fingiu não ter dúvida.
        for prefixo, secao in (("F", "Fontes"), ("L", "Lacunas e assunções")):
            conf["requisitos"] += 1
            if len(re.findall(rf"^{prefixo}-\d+:", spec, re.MULTILINE)) == 0:
                falha(f'{caminho}: a seção "## {secao}" não tem nenhuma linha '
                      f"`{prefixo}-01: ...` — {'fonte' if prefixo == 'F' else 'lacuna'} "
                      f"declarada é o que separa spec de opinião")

        # A DoD é executável: tabela com coluna de verificação (insumo de Testabilidade).
        conf["requisitos"] += 1
        corpo_dod = spec.split("## Critérios de aceite (DoD)")
        if len(corpo_dod) > 1:
            trecho = corpo_dod[1].split("\n## ")[0]
            if "Verificação executável" not in trecho:
                falha(f'{caminho}: a DoD não tem a coluna "Verificação executável" — '
                      f"critério sem comando é julgamento disfarçado de portão")

    # ---- 3 · plan.md --------------------------------------------------------------
    if "plan.md" in presentes:
        plan = presentes["plan.md"]
        caminho = f"{d}/plan.md"

        titulos = [l for l in plan.splitlines() if re.match(r"^#{2,3}\s", l)]
        maestro_h = [t for t in titulos if "Constitution Check" in t
                     and "Project Constitution Check" not in t]
        projeto_h = [t for t in titulos if "Project Constitution Check" in t]
        conf["tabelas"] += 2
        if len(maestro_h) != 1:
            falha(f'{caminho}: esperava 1 cabeçalho "Constitution Check" (Maestro I–VIII), '
                  f"encontrou {len(maestro_h)}")
        if len(projeto_h) != 1:
            falha(f'{caminho}: esperava 1 cabeçalho "Project Constitution Check" (projeto '
                  f"P1–P7), encontrou {len(projeto_h)} — um plano com só a primeira tabela "
                  f"está incompleto")

        # As linhas das duas tabelas, com célula de conformidade preenchida.
        for rotulos, nome in ((MAESTRO, "Maestro I–VIII"), (PROJETO, "projeto P1–P7")):
            for r in rotulos:
                conf["tabelas"] += 1
                m = re.search(r"^\|\s*" + re.escape(r) + r"\s([^|]*)\|([^|]*)\|",
                              plan, re.MULTILINE)
                if not m:
                    falha(f"{caminho}: a tabela {nome} não tem linha para o princípio "
                          f'"{r}" — nenhuma linha vazia, e nenhuma linha ausente')
                elif len(re.sub(r"[*_`\s✅⚠️❌]", "", m.group(2))) < 10:
                    falha(f'{caminho}: o princípio "{r}" tem célula de conformidade vazia '
                          f"ou só com o símbolo — um ✅ sozinho não é avaliação")

        for a in ARTEFATOS_CONDICIONAIS:
            conf["art"] += 1
            if not re.search(rf"ART:{re.escape(a)}=(yes|no)\b", plan):
                falha(f"{caminho}: não declara `ART:{a}=yes|no` — silêncio não é decisão "
                      f"(catálogo: docs/governance/artifacts.md)")

    # ---- 4 · tasks.md -------------------------------------------------------------
    if "tasks.md" in presentes:
        tasks = presentes["tasks.md"]
        for t in CAUDA:
            conf["tail"] += 1
            if f"TAIL:{t}" not in tasks:
                falha(f"{d}/tasks.md: não carrega `TAIL:{t}` — a cauda de fechamento "
                      f"(revisão · segurança · mutação · gate) não é opcional")

# Regra R2: o verde diz QUANTO examinou.
total = sum(conf.values())
print("── Specs: artefatos, seções, taxonomia e cauda ──")
print(f"  ciclos examinados: {len(dirs)} "
      f"({', '.join(os.path.basename(x)[:3] for x in dirs)})")
print(f"  verificações: artefatos {conf['artefatos']} · seções e status {conf['secoes']} · "
      f"tipos de requisito {conf['requisitos']} · linhas de Constitution Check "
      f"{conf['tabelas']} · tokens ART {conf['art']} · tokens TAIL {conf['tail']}"
      f"  =  {total}")
print(f"  isenções aplicadas: {isentos_aplicados}"
      + ("".join(f"\n    · ciclo {c}: {o} — {m}" for c, (o, m) in ISENTOS.items())
         if isentos_aplicados else ""))
print("  régua DoR (ADR 0004): Completude 30 · Testabilidade 25 · Clareza 20 · Escopo 15 ·"
      "\n    Casos-limite 10, corte ≥ 80 — este portão confere o piso mecânico, não pontua.")

if falhas:
    print(f"\n✗ {len(falhas)} falha(s):", file=sys.stderr)
    for f in falhas:
        print(f"    {f}", file=sys.stderr)
    sys.exit(1)

print("\n✓ todo ciclo tem os quatro artefatos, spec com as seções e os tipos de requisito,\n"
      "  plano com as duas tabelas e os cinco artefatos declarados, e tasks com a cauda.")
PY
