#!/usr/bin/env bash
# check-adrs-sucessao.sh — fitness function for rule R5 (CLAUDE.md): a decision that
# contradicts a decision has to declare itself, and no decision hides from the record.
#
# Por que existe: na irmã `gestaodeprioridades`, dois ADRs (Architecture Decision Record,
# registro de decisão arquitetural) mutuamente contraditórios ficaram os dois "Aceita", sem
# relação declarada entre si, e a contradição atravessou sete portões verdes, 17 testes e
# 166 caminhos conferidos — quem pegou foi a revisão independente do fechamento. A lição
# virou a regra R5 do `CLAUDE.md`; este portão é a aptidão dela. O outro defeito da mesma
# família (o ADR 0011 de lá decidiu matéria que tocava um princípio INEGOCIÁVEL sem sequer
# citá-lo) virou o campo "Princípios tocados", conferido aqui.
#
# Sobreposição declarada com `scripts/check-adr.sh` (portão instalado do método): aquele
# confere índice × disco × **status**. Este confere o que aquele não olha — a linha no
# registro append-only `docs/records/decisoes.jsonl`, o par de sucessão nos **dois**
# sentidos, e os dois campos que este projeto exige por retrospectiva. A conferência de
# índice aqui é mínima de propósito (existe a linha? aponta para o arquivo?) para não
# duplicar função (Princípio VI — Living artifacts).
#
# O que este portão NÃO mede (anti-padrão 13 — medir a frase em vez do fato): se a decisão é
# boa, se a sucessão faz sentido, ou se os princípios declarados são os certos. Ele mede
# quatro fatos mecânicos por ADR, e diz quantos examinou (regra R2).
#
# Uso: scripts/check-adrs-sucessao.sh [raiz]     (padrão: a raiz do repositório)
set -uo pipefail
RAIZ="${1:-$(cd "$(dirname "$0")/.." && pwd)}"
cd "$RAIZ" || { echo "✗ raiz inexistente: $RAIZ" >&2; exit 2; }

python3 - <<'PY'
import glob, json, os, re, sys

DIR = "docs/adr"
INDICE = os.path.join(DIR, "README.md")
REGISTRO = "docs/records/decisoes.jsonl"

falhas = []
def falha(msg):
    falhas.append(msg)

if not os.path.isdir(DIR):
    print(f"✗ {DIR}/ não existe — este repositório declara um registro de decisões.",
          file=sys.stderr)
    sys.exit(2)

adrs = sorted(glob.glob(os.path.join(DIR, "[0-9][0-9][0-9][0-9]-*.md")))
if not adrs:
    print(f"✗ nenhum ADR em {DIR}/ — registro vazio não é registro limpo.", file=sys.stderr)
    sys.exit(2)

# ---- o índice: só as LINHAS DE TABELA -------------------------------------------
# Menção em prosa, linha comentada ou linha riscada não é listagem: se contassem, um ADR
# poderia sumir da tabela renderizada e ainda passar. Mesma lição do check-adr.sh.
linhas_indice = []
if os.path.exists(INDICE):
    linhas_indice = [l.rstrip("\n") for l in open(INDICE, encoding="utf-8")
                     if l.lstrip().startswith("|") and not re.match(r"^\|[\s:]*-{2,}", l.lstrip())]
else:
    falha(f"{INDICE} não existe — o índice É a porta de entrada das decisões")

# ---- o registro append-only ------------------------------------------------------
registros = []
if os.path.exists(REGISTRO):
    for n, l in enumerate(open(REGISTRO, encoding="utf-8"), 1):
        l = l.strip()
        if not l:
            continue
        try:
            registros.append((n, json.loads(l)))
        except json.JSONDecodeError as e:
            falha(f"{REGISTRO}:{n} não é JSON (JavaScript Object Notation) válido ({e.msg}) — o registro é lido por script, "
                  f"não só por gente")
else:
    falha(f"{REGISTRO} não existe — sem ele nenhuma decisão está registrada "
          f"(o arquivo é append-only: use scripts/record-decision.sh, nunca o editor)")

def campo(nome):
    return re.compile(r"^-\s+\*\*" + re.escape(nome) + r"\*\*:\s*(.*)$")

RE_SUCEDE = campo("Sucede")
RE_PRINC = campo("Princípios tocados")
RE_STATUS = campo("Status")
RE_NUM4 = re.compile(r"\b(\d{4})\b")
RE_NENHUM = re.compile(r"\bnenhum\b", re.IGNORECASE)

# "Superseded by" só conta na LINHA DE STATUS. A primeira versão deste portão procurava a
# frase em qualquer linha do ADR, e o fixture de sabotagem a derrubou na hora: o corpo de um
# ADR que *explica* a regra ("o 0001 declara «Superseded by» apontando para cá") passava a
# declarar-se sucedido. Portão que mede a frase em vez do fato é o anti-padrão 13, e foi
# assim que a irmã ganhou quatro verdes que não olhavam para nada. A declaração vive no
# status — é lá que a R5 a põe e é lá que o check-adr.sh a lê.
# Sinônimos aceitos porque quem escreve em português alcança o mais próximo primeiro; a
# lista é a mesma vertente que o check-adr.sh já mapeia.
RE_SUPERSEDED = re.compile(r"superseded by|supera[dn][ao] por|substitu[íi]d[ao] por|"
                           r"revogad[ao] por|replaced by", re.IGNORECASE)

info = {}
for caminho in adrs:
    base = os.path.basename(caminho)
    num = base[:4]
    sucede = principios = status = None
    status_ln = 0
    for i, linha in enumerate(open(caminho, encoding="utf-8"), 1):
        linha = linha.rstrip("\n")
        m = RE_SUCEDE.match(linha)
        if m and sucede is None:
            sucede = m.group(1).strip()
        m = RE_PRINC.match(linha)
        if m and principios is None:
            principios = m.group(1).strip()
        m = RE_STATUS.match(linha)
        if m and status is None:
            status, status_ln = m.group(1).strip(), i
    sup = []
    if status and RE_SUPERSEDED.search(status):
        sup = [(status_ln, status)]
    info[num] = dict(caminho=caminho.replace(os.sep, "/"), base=base, sucede=sucede,
                     principios=principios, status=status, superseded=sup)

def celula(linha, i):
    partes = linha.split("|")
    if len(partes) <= i:
        return ""
    return partes[i].replace("*", "").replace("`", "").strip()

conferencias = 0
for num in sorted(info):
    d = info[num]

    # 1 · o ADR está no índice, e a linha aponta para o arquivo dele
    conferencias += 1
    minhas = [l for l in linhas_indice
              if celula(l, 1).isdigit() and int(celula(l, 1)) == int(num)]
    if not minhas:
        falha(f"ADR {num} está em disco e não tem linha em {INDICE} — decisão não listada "
              f"é decisão que ninguém encontra")
    elif len(minhas) > 1:
        falha(f"ADR {num} tem {len(minhas)} linhas em {INDICE} — uma delas está errada e "
              f"nada diz qual")
    elif d["base"] not in minhas[0]:
        falha(f"ADR {num} tem linha no índice que não aponta para {d['base']} — o índice o "
              f"nomeia sem levar a ele")

    # 2 · o ADR tem linha no registro append-only, apontando para o arquivo
    conferencias += 1
    achados = [r for _, r in registros
               if str(r.get("registro", "")).lstrip("./") == d["caminho"]]
    if not achados:
        por_id = [r for _, r in registros if str(r.get("id", "")) == f"adr-{num}"]
        if por_id:
            falha(f'ADR {num}: há linha "adr-{num}" em {REGISTRO}, mas o campo "registro" '
                  f'não aponta para {d["caminho"]} — o registro precisa levar ao arquivo')
        else:
            falha(f"ADR {num} não tem linha em {REGISTRO} — decisão fora do registro "
                  f"append-only é decisão que a retrospectiva não vê "
                  f"(scripts/record-decision.sh; nunca editar à mão — há guard hook)")

    # 3 · "Princípios tocados" — a omissão é o sintoma (R3 quarta condição, R5)
    conferencias += 1
    if d["principios"] is None:
        falha(f'{d["base"]} não declara o campo "- **Princípios tocados**:" — a lição do '
              f"ADR 0011→0016 da irmã é que o defeito não foi dizer algo errado sobre o "
              f'princípio, foi não o mencionar. Escreva "nenhum" por extenso quando for o caso')
    elif len(d["principios"]) < 3:
        falha(f'{d["base"]} declara "Princípios tocados" vazio — "nenhum" se escreve por extenso')

    # 4 · "Sucede" — a metade nova do par de R5
    conferencias += 1
    if d["sucede"] is None:
        falha(f'{d["base"]} não declara o campo "- **Sucede**:" — sem ele um ADR pode '
              f'suceder outro em silêncio, que é exatamente o defeito que a R5 fecha. '
              f'Escreva "nenhum" por extenso quando não suceder ADR algum')
    elif len(d["sucede"]) < 3:
        falha(f'{d["base"]} declara "Sucede" vazio — "nenhum" se escreve por extenso')

# ---- o par de sucessão, nos dois sentidos ---------------------------------------
sucessoes = 0   # "eu sucedo NNNN" -> NNNN tem de dizer "Superseded by"
sucedidos = 0   # "Superseded by NNNN" -> NNNN tem de dizer "Sucede"

for num in sorted(info):
    d = info[num]
    val = d["sucede"] or ""
    antecessores = [] if RE_NENHUM.search(val) else sorted(set(RE_NUM4.findall(val)))
    for ant in antecessores:
        sucessoes += 1
        if ant not in info:
            falha(f"ADR {num} declara suceder o ADR {ant}, que não existe em {DIR}/")
            continue
        alvo = info[ant]
        if not [l for _, l in alvo["superseded"] if num in l]:
            falha(f'ADR {num} sucede o ADR {ant}, e {alvo["base"]} não declara '
                  f'"Superseded by" nomeando {num} — a R5 exige a declaração nos DOIS lados '
                  f"(foi a contradição silenciosa que atravessou sete portões verdes na irmã)")

for num in sorted(info):
    d = info[num]
    for i, linha in d["superseded"]:
        alvos = sorted(set(RE_NUM4.findall(linha)) - {num})
        if not alvos:
            falha(f'{d["base"]}:{i} diz "Superseded by" sem nomear o ADR sucessor '
                  f"(quatro dígitos) — quem lê fica sabendo que a decisão caiu e não por quê")
            continue
        for a in alvos:
            sucedidos += 1
            if a not in info:
                falha(f'{d["base"]}:{i} declara ser sucedido pelo ADR {a}, que não existe '
                      f"em {DIR}/")
                continue
            v = info[a]["sucede"] or ""
            if num not in RE_NUM4.findall(v):
                falha(f'{d["base"]}:{i} declara ser sucedido pelo ADR {a}, e '
                      f'{info[a]["base"]} não declara "- **Sucede**: {num}" — meio par é '
                      f"pior que nenhum: o leitor do ADR novo não sabe o que caiu")

# ---- toda linha "adr-NNNN" do registro tem arquivo em disco ----------------------
orfas = 0
for n, r in registros:
    ident = str(r.get("id", ""))
    m = re.fullmatch(r"adr-(\d{4})", ident)
    if not m:
        continue
    orfas += 1
    if m.group(1) not in info:
        falha(f"{REGISTRO}:{n} registra o ADR {m.group(1)}, que não existe em {DIR}/ — "
              f"decisão anunciada e inalcançável")

# Regra R2: o verde diz QUANTO examinou.
print("── ADRs: índice, registro e sucessão (regra R5) ──")
print(f"  ADRs examinados: {len(info)}  ·  linhas de tabela no índice: {len(linhas_indice)}"
      f"  ·  linhas em {REGISTRO}: {len(registros)}")
print(f"  invariantes por ADR: 4 (índice · registro append-only · "
      f'campo "Princípios tocados" · campo "Sucede")')
print(f"  verificações executadas: {conferencias}  ·  sucessões declaradas: {sucessoes}"
      f"  ·  sucedidos declarados: {sucedidos}  ·  linhas adr-* conferidas: {orfas}")

if falhas:
    print(f"\n✗ {len(falhas)} falha(s):", file=sys.stderr)
    for f in falhas:
        print(f"    {f}", file=sys.stderr)
    sys.exit(1)

print("\n✓ todo ADR está no índice e no registro, declara os princípios que toca e o que "
      "sucede,\n  e toda sucessão está declarada nos dois lados.")
PY
