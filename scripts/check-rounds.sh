#!/usr/bin/env bash
# check-rounds.sh — fitness function for `docs/produto/rounds.md`: every round declares the
# six fields, the dependencies form no cycle, and every measured lesson has exactly one home.
#
# Por que existe: o próprio `docs/produto/rounds.md` abre declarando a dívida — *"o
# verificador executável dos seis campos e da alocação exaustiva de D-01..D-11 ainda não
# existe"* — e nomeia a revisão independente como substituta provisória. Um documento que
# diz "onze defeitos, onze destinos, nenhum em dois lugares" e não tem quem confira é uma
# afirmação factual sem execução, que é o que a regra R1 (`CLAUDE.md`) proíbe. Este portão
# é a aptidão que a dívida pedia.
#
# As três coisas que ele mede, e por que cada uma:
#
#   1. **Os seis campos** — Apetite · Entrega · Fora · Aptidão executável · Depende de ·
#      Sai primeiro. O formato é herdado da irmã `gestaodeprioridades`. Campo ausente ou
#      vazio é escopo indefinido chegando ao ciclo; `Sai primeiro` vazio é o apetite
#      (um ciclo do método) sem válvula de escape. O campo **Defeitos** entra como sétimo
#      obrigatório porque é dele que sai a alocação do item 3: silêncio ali não é
#      declaração, é esquecimento.
#   2. **Nenhum ciclo nas dependências** — round A depende de B que depende de A é um
#      roadmap que nunca começa, e a leitura humana não pega isso num grafo de doze nós.
#   3. **Alocação exaustiva dos defeitos D-NN** — cada lição medida em
#      `docs/produto/visao.md` §6 aparece em **exatamente um** round ou na lista
#      "Defeitos não corrigidos em round próprio", nunca em dois e nunca em nenhum.
#
# **Como a alocação é escrita** (e por que o portão é literal quanto a isso): alocar é
# escrever o defeito em **negrito** no campo `Defeitos` do round — `**D-02** (...)`. Uma
# menção em prosa no mesmo campo — "o defeito dela era o SDK no cliente (D-01), que já
# morreu no 006" — é referência cruzada, **não** alocação, e o portão não a conta. Sem essa
# distinção o round 007 alocaria o D-01 pela segunda vez e o portão reprovaria um texto
# correto (anti-padrão 13: medir a frase em vez do fato).
#
# O que este portão NÃO mede: se o apetite é realista, se a aptidão executável de fato
# executa, ou se o defeito foi alocado ao round **certo**. Isso é julgamento, e fica com o
# gate humano. Ele mede presença, aciclicidade e partição — e diz quanto examinou (R2).
#
# Uso: scripts/check-rounds.sh [raiz]     (padrão: a raiz do repositório)
set -uo pipefail
RAIZ="${1:-$(cd "$(dirname "$0")/.." && pwd)}"
cd "$RAIZ" || { echo "✗ raiz inexistente: $RAIZ" >&2; exit 2; }

python3 - <<'PY'
import os, re, sys

ROUNDS = "docs/produto/rounds.md"
VISAO = "docs/produto/visao.md"

CAMPOS = ["Apetite", "Entrega", "Fora", "Aptidão executável", "Depende de",
          "Sai primeiro", "Defeitos"]
SEC_NAO_CORRIGIDOS = "Defeitos não corrigidos em round próprio"

falhas = []
def falha(msg):
    falhas.append(msg)

for arq in (ROUNDS, VISAO):
    if not os.path.exists(arq):
        print(f"✗ {arq} não existe — este portão confere o planejamento, e ele sumiu.",
              file=sys.stderr)
        sys.exit(2)

linhas = [l.rstrip("\n") for l in open(ROUNDS, encoding="utf-8")]

RE_ROUND = re.compile(r"^## Round\s+(\d{3})\s+[—-]\s*(.+?)\s*$")
RE_H2 = re.compile(r"^## ")
RE_CAMPO = re.compile(r"^-\s+\*\*([^*]+?)\*\*:\s*(.*)$")
RE_NUM3 = re.compile(r"\b(\d{3})\b")
RE_NENHUM = re.compile(r"\bnenhum\b", re.IGNORECASE)
RE_ALOCA = re.compile(r"\*\*(D-\d{2})\*\*")
RE_NAO_CORRIGIDO = re.compile(r"^-\s+\*\*(D-\d{2})\s")
RE_DEFINE = re.compile(r"^\*\*(D-\d{2})\s+·")

# ---- as seções ------------------------------------------------------------------
secoes = []          # (numero, titulo, inicio, fim)  — fim exclusivo
nao_corrigidos_span = None
atual = None
for i, l in enumerate(linhas):
    m = RE_ROUND.match(l)
    if m:
        if atual:
            secoes.append(atual + (i,))
        atual = (m.group(1), m.group(2), i + 1)
        continue
    if RE_H2.match(l):
        if atual:
            secoes.append(atual + (i,))
            atual = None
        if l[3:].strip() == SEC_NAO_CORRIGIDOS:
            nao_corrigidos_span = [i + 1, len(linhas)]
        elif nao_corrigidos_span and nao_corrigidos_span[1] == len(linhas):
            nao_corrigidos_span[1] = i
if atual:
    secoes.append(atual + (len(linhas),))

if not secoes:
    print(f"✗ nenhuma seção '## Round NNN — ...' em {ROUNDS}.", file=sys.stderr)
    sys.exit(2)

def campos_da_secao(ini, fim):
    """Campo -> (linha 1-based, valor com as continuações).

    O valor continua nas linhas seguintes até um novo campo (`- **X**:`), um cabeçalho,
    uma linha em branco ou um item de lista — que é como o documento realmente escreve."""
    achados = {}
    n = ini
    while n < fim:
        m = RE_CAMPO.match(linhas[n])
        if m:
            nome = m.group(1).strip()
            valor = [m.group(2).strip()]
            k = n + 1
            while k < fim:
                seg = linhas[k]
                if not seg.strip() or RE_CAMPO.match(seg) or seg.startswith("#") \
                   or re.match(r"^\s*[-*\d]+[.)]?\s+\*\*", seg):
                    break
                valor.append(seg.strip())
                k += 1
            achados.setdefault(nome, (n + 1, " ".join(valor).strip()))
            n = k
            continue
        n += 1
    return achados

# ---- 1 · os campos obrigatórios --------------------------------------------------
conferencias = 0
dependencias = {}
alocacoes = {}       # D-NN -> [rounds]
for num, titulo, ini, fim in secoes:
    campos = campos_da_secao(ini, fim)
    for nome in CAMPOS:
        conferencias += 1
        if nome not in campos:
            falha(f"Round {num} ({titulo}) não declara o campo obrigatório "
                  f'"- **{nome}**:" — silêncio não é declaração')
            continue
        ln, valor = campos[nome]
        limpo = re.sub(r"[*_`\s]", "", valor)
        if len(limpo) < 3:
            falha(f"{ROUNDS}:{ln} — Round {num}: o campo \"{nome}\" está vazio")
    if "Depende de" in campos:
        _, valor = campos["Depende de"]
        dependencias[num] = [] if RE_NENHUM.search(valor) else RE_NUM3.findall(valor)
    if "Defeitos" in campos:
        _, valor = campos["Defeitos"]
        for d in RE_ALOCA.findall(valor):
            alocacoes.setdefault(d, []).append(f"round {num}")

# ---- 2 · as dependências apontam para rounds reais e não fecham ciclo ------------
existentes = {num for num, _, _, _ in secoes}
arestas = 0
for num, deps in dependencias.items():
    for d in deps:
        arestas += 1
        if d == num:
            falha(f"Round {num} depende de si mesmo")
        elif d not in existentes:
            falha(f"Round {num} depende do round {d}, que não tem seção em {ROUNDS}")

BRANCO, CINZA, PRETO = 0, 1, 2
cor = {n: BRANCO for n in existentes}
ciclos = []

def visita(n, pilha):
    cor[n] = CINZA
    pilha.append(n)
    for d in dependencias.get(n, []):
        if d not in cor:
            continue
        if cor[d] == CINZA:
            ciclos.append(" → ".join(pilha[pilha.index(d):] + [d]))
        elif cor[d] == BRANCO:
            visita(d, pilha)
    pilha.pop()
    cor[n] = PRETO

for n in sorted(existentes):
    if cor[n] == BRANCO:
        visita(n, [])
for c in sorted(set(ciclos)):
    falha(f"ciclo de dependência entre rounds: {c} — um roadmap circular nunca começa")

# ---- 3 · alocação exaustiva dos defeitos medidos ---------------------------------
definidos = []
for i, l in enumerate(open(VISAO, encoding="utf-8"), 1):
    m = RE_DEFINE.match(l)
    if m:
        definidos.append((m.group(1), i))
definidos_set = {d for d, _ in definidos}
if not definidos:
    falha(f"{VISAO} não define nenhum defeito no formato \"**D-NN · ...**\" — sem eles a "
          f"alocação exaustiva não tem denominador")

nao_corrigidos = {}
if nao_corrigidos_span:
    ini, fim = nao_corrigidos_span
    for n in range(ini, fim):
        m = RE_NAO_CORRIGIDO.match(linhas[n])
        if m:
            nao_corrigidos.setdefault(m.group(1), []).append(
                f'lista "{SEC_NAO_CORRIGIDOS}"')
else:
    falha(f'{ROUNDS} não tem a seção "## {SEC_NAO_CORRIGIDOS}" — sem ela um defeito sem '
          f"round não tem onde ser declarado, e some")

destinos = {}
for d, onde in list(alocacoes.items()) + list(nao_corrigidos.items()):
    destinos.setdefault(d, []).extend(onde)

for d, ln in definidos:
    onde = destinos.get(d, [])
    if not onde:
        falha(f"{VISAO}:{ln} — o defeito {d} está medido e não foi alocado a round algum "
              f'nem à lista "{SEC_NAO_CORRIGIDOS}"')
    elif len(onde) > 1:
        falha(f"o defeito {d} está alocado em {len(onde)} lugares ({', '.join(onde)}) — "
              f"cada defeito tem um destino, ou dois donos e nenhum responsável")

for d in sorted(set(destinos) - definidos_set):
    falha(f'{ROUNDS} aloca o defeito {d} ({", ".join(destinos[d])}), que {VISAO} não define '
          f'no formato "**{d} · ...**"')

# Regra R2: o verde diz QUANTO examinou.
print("── Rounds: campos, dependências e alocação de defeitos ──")
print(f"  rounds examinados: {len(secoes)} ({', '.join(n for n, _, _, _ in secoes)})")
print(f"  campos obrigatórios por round: {len(CAMPOS)}  ·  conferências de campo: {conferencias}")
print(f"  arestas de dependência: {arestas}  ·  ciclos encontrados: {len(set(ciclos))}")
print(f"  defeitos medidos em {VISAO}: {len(definidos)}  ·  alocados a round: "
      f"{len(alocacoes)}  ·  declarados sem round: {len(nao_corrigidos)}")

if falhas:
    print(f"\n✗ {len(falhas)} falha(s):", file=sys.stderr)
    for f in falhas:
        print(f"    {f}", file=sys.stderr)
    sys.exit(1)

print("\n✓ todo round declara os sete campos, as dependências não formam ciclo,\n"
      "  e cada defeito medido tem exatamente um destino.")
PY
