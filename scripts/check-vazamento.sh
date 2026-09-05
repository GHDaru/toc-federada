#!/usr/bin/env bash
# check-vazamento.sh — fitness function for rule RNF-03 / ADR 0006: no real person's data
# in this repository. It looks for LEAKED CONTENT, never for a cited path.
#
# Why it exists (and why it is not the criterion it replaces): the first version of the
# acceptance criterion of cycle 001 matched the STRING of the sister's base path
# (`gestaodeprioridades/protot[i]po`) in every `*.md`. That measures citation, not leakage:
# it flagged the evidence block of ADR 0006 — a command that printed COUNTS to justify the
# very rule "synthetic base from day 1" — and it was unstable, because reporting the finding
# added another occurrence of the path and raised the count. A gate whose number changes
# when you write about it is a gate that measures the wrong thing.
#
# What a real leak looks like, per ADR 0006 and the notice at the top of CLAUDE.md — "nenhum
# dado real de pessoa: nome, enunciado de trabalho, data de desempenho":
#
#   V1 · a person's PROPER NAME assigned to a person field (`"responsavel": "<Nome Sobrenome>"`,
#        `**Responsável**: <Nome Sobrenome>`, or a person column of a table).
#   V2 · a RECORD in the shape of the sister's real base — four or more fields of her fixture
#        schema in the same record — which is how a work statement plus a performance date
#        travels even with the names stripped.
#   V3 · EXECUTABLE code of this repository (anything that is not `*.md`) reading the sister's
#        real base or her screenshots — the runtime version of the same leak.
#
# A path cited inside a documentation block is none of the three, on purpose: citing where
# the evidence came from is what an ADR is for. Writing about this gate does not change its
# number, which is the property the old criterion did not have.
#
# Declared exemption, one and narrow: a line UNDER scripts/tests/ that carries the token
# SABOTAGEM-SINTETICA — that is where the suite plants the defect on purpose. Anywhere else
# the token exempts nothing, and inside scripts/tests/ a line without it is a finding like
# any other.
#
# Usage: scripts/check-vazamento.sh [root]     (default: the repository root)
set -uo pipefail
RAIZ="${1:-$(cd "$(dirname "$0")/.." && pwd)}"
cd "$RAIZ" || { echo "✗ raiz inexistente: $RAIZ" >&2; exit 2; }

python3 - <<'PY'
import json, os, re, sys

MAI = "A-ZÁÀÂÃÄÉÈÊËÍÌÎÏÓÒÔÕÖÚÙÛÜÇÑ"
MIN = "a-záàâãäéèêëíìîïóòôõöúùûüçñ"
PALAVRA = f"[{MAI}][{MIN}]+"
PARTICULA = r"(?:d[aeo]s?|e|von|van|del|la)"
# A proper name: two or more capitalised words, particles allowed between them.
NOME = rf"{PALAVRA}(?:\s+(?:{PARTICULA}\s+)?{PALAVRA})+"
RE_NOME_INTEIRO = re.compile(rf"^\s*{NOME}\s*$")

# Fields that name a PERSON. Deliberately excludes the generic `nome`/`name`: in this corpus
# they name modules, cycles and the product ("Nuvem de Conflito"), so including them would
# make the gate cry wolf and teach people to ignore it.
PESSOA = ("responsavel", "responsável", "responsavel_nome", "nome_completo",
          "nome_da_pessoa", "assignee", "autor", "author", "participante",
          "solicitante", "executor", "colaborador", "funcionario", "funcionário",
          "aluno", "entrevistado", "facilitador", "facilitadora", "gestor",
          "gestora", "dono")
CH = "|".join(PESSOA)
# The key must be DELIMITED — quoted, backticked or bold — so that running prose
# ("...uma pessoa: as telas capturadas exibem...") is not read as a record.
# `\\?` porque uma citação JSON dentro de uma string de shell chega escapada (\\"chave\\":)
# — e um portão que não vê a forma escapada tem um buraco do tamanho de um script.
ASPA = r"(?:\\?[\"'`]|\*\*)"
RE_CAMPO_PESSOA = re.compile(
    rf"""{ASPA}({CH}){ASPA}?\s*[:=]\s*{ASPA}?\s*({NOME})""",
    re.IGNORECASE)

# The schema of the sister's REAL base, read from her fixture (GHDaru/gestaodeprioridades,
# leitura apenas — P1). Four or more of these in one record is a transplanted record.
CHAVES_IRMA = ("responsavel", "responsável", "data_inclusao", "data_conclusao",
               "data_prevista", "duracao_estimada", "duracao_real", "notas_gut",
               "grupo_id", "parent_id", "gravidade", "urgencia", "urgência",
               "tendencia", "tendência", "envelhecimento")
LIMIAR_IRMA = 4
RE_CHAVE_IRMA = re.compile(
    rf"""{ASPA}({"|".join(CHAVES_IRMA)}){ASPA}?\s*[:=]""", re.IGNORECASE)

# The sister's real base and her screenshots — the two artefacts that carry her people.
RE_BASE_REAL = re.compile(
    r"gestaodeprioridades/(?:prototipo|docs/jornadas/capturas)"
    r"|gestaodeprioridades[^\s'\"`)]*fixture\.json")

# O elenco declarado sintético (ADR 0006): papéis e organização fictícios, com o motivo.
# Uma isenção sem motivo escrito vira tapete — é a lição que a irmã já pagou.
ELENCO = (
    ("Facilitadora TOC",         "papel fictício declarado no ADR 0006 e em docs/produto/dados/analise-horizonte.json"),
    ("Instituição Horizonte",    "organização fictícia declarada no ADR 0006"),
    ("Coordenação de Operações", "papel fictício citado pelo ADR 0006"),
    ("Product Steward",          "papel de governança do método, não uma pessoa nomeada"),
)
ELENCO_NOMES = {n.lower() for n, _ in ELENCO}

MARCADOR = "SABOTAGEM-SINTETICA"
# Diretórios que não são conteúdo NOSSO: metadados do controle de versão, cache e código
# de terceiro baixado. `.venv` entrou quando o serviço nasceu (`apps/api/.venv`), pelo mesmo
# motivo pelo qual `node_modules` já estava aqui: o `.dist-info` de um pacote de terceiro
# lista os autores dele — pessoas reais, num arquivo que não é versionado (ver `.gitignore`)
# e que ninguém deste projeto escreveu. Manter a varredura sobre ele não protegeria dado
# nenhum; só ensinaria a ignorar o vermelho, que é o defeito que a regra R2 nomeia.
# NENHUM arquivo versionado é isentado por esta linha.
IGNORA_DIR = {".git", "__pycache__", "node_modules", ".venv", ".pytest_cache", ".ruff_cache"}
IGNORA_EXT = {".pyc", ".png", ".jpg", ".jpeg", ".webp", ".gif", ".pdf", ".ico", ".woff", ".woff2"}

def isento(caminho, linha):
    """A única isenção: a suíte de sabotagem planta o defeito de propósito, e diz isso na
    própria linha. Fora de scripts/tests/ o marcador não isenta nada."""
    return caminho.startswith("scripts/tests/") and MARCADOR in linha

achados = []      # (sinal, caminho, linha, evidência curta)
isencoes = 0
arquivos, linhas_varridas, registros_json = 0, 0, 0

def registra(sinal, caminho, n, texto, evidencia):
    global isencoes
    if isento(caminho, texto):
        isencoes += 1
        return
    achados.append((sinal, caminho, n, evidencia))

# ── varredura linha a linha (vale para .md, .json, .csv, .tsv, código) ────────────────
def celulas(linha, ext):
    """Células de TABELA — e só de tabela. A vírgula só corta em arquivo tabular (.csv);
    numa lista de código ela é vírgula de código, e um portão que confunde as duas coisas
    reprova a si mesmo (foi o que aconteceu na primeira execução deste arquivo)."""
    if ext in (".md", ".markdown") and linha.lstrip().startswith("|"):
        return [c.strip() for c in linha.strip().strip("|").split("|")]
    if ext == ".tsv" and "\t" in linha:
        return [c.strip() for c in linha.split("\t")]
    if ext == ".csv" and linha.count(",") >= 3:
        return [c.strip().strip('"') for c in linha.split(",")]
    return []

alvos = []
for base, dirs, nomes in os.walk("."):
    dirs[:] = [d for d in dirs if d not in IGNORA_DIR]
    for n in nomes:
        if os.path.splitext(n)[1].lower() in IGNORA_EXT:
            continue
        alvos.append(os.path.relpath(os.path.join(base, n), "."))
alvos.sort()

for caminho in alvos:
    try:
        texto = open(caminho, encoding="utf-8").read()
    except (UnicodeDecodeError, OSError):
        continue
    arquivos += 1
    linhas = texto.splitlines()
    linhas_varridas += len(linhas)
    md = caminho.endswith(".md")
    ext = os.path.splitext(caminho)[1].lower()
    colunas_pessoa = {}   # índice da coluna → nome do campo, para tabelas
    for n, linha in enumerate(linhas, 1):
        # V1 — nome próprio num campo de pessoa
        for m in RE_CAMPO_PESSOA.finditer(linha):
            if m.group(2).strip().lower() in ELENCO_NOMES:
                continue
            registra("V1", caminho, n, linha,
                     f"{m.group(1)} = {m.group(2)}")
        # V1 — tabela (markdown, CSV, TSV): coluna de pessoa + célula com nome próprio
        cs = celulas(linha, ext)
        if cs:
            cabecalho = {i: c for i, c in enumerate(cs)
                         if c.strip("*` ").lower() in PESSOA}
            if cabecalho:
                colunas_pessoa = cabecalho
            elif colunas_pessoa:
                for i, campo in colunas_pessoa.items():
                    if i < len(cs) and RE_NOME_INTEIRO.match(cs[i]) \
                       and cs[i].strip().lower() not in ELENCO_NOMES:
                        registra("V1", caminho, n, linha, f"coluna {campo} = {cs[i].strip()}")
        else:
            colunas_pessoa = {}
        # V2 — registro no formato da base real da irmã
        achadas = {m.group(1).lower() for m in RE_CHAVE_IRMA.finditer(linha)}
        if len(achadas) >= LIMIAR_IRMA:
            registra("V2", caminho, n, linha,
                     f"{len(achadas)} campos do esquema da base da irmã no mesmo registro")
        if cs and len({c.strip('*"` ').lower() for c in cs} & {k.lower() for k in CHAVES_IRMA}) >= LIMIAR_IRMA:
            registra("V2", caminho, n, linha,
                     "cabeçalho de tabela com o esquema da base da irmã")
        # V3 — código deste repositório lendo a base real (documento .md pode citá-la)
        if not md and RE_BASE_REAL.search(linha):
            registra("V3", caminho, n, linha, RE_BASE_REAL.search(linha).group(0))

    # ── varredura estrutural de JSON: pega o registro impresso em várias linhas ────────
    if caminho.endswith((".json", ".jsonl")):
        docs = []
        try:
            docs = [json.loads(texto)]
        except json.JSONDecodeError:
            for linha in linhas:
                linha = linha.strip()
                if linha.startswith("{"):
                    try:
                        docs.append(json.loads(linha))
                    except json.JSONDecodeError:
                        pass
        pilha = list(docs)
        while pilha:
            no = pilha.pop()
            if isinstance(no, dict):
                registros_json += 1
                chaves = {k.lower() for k in no}
                if len(chaves & {c.lower() for c in CHAVES_IRMA}) >= LIMIAR_IRMA:
                    registra("V2", caminho, 0, "",
                             "registro JSON com o esquema da base da irmã")
                for k, v in no.items():
                    if k.lower() in PESSOA and isinstance(v, str) \
                       and RE_NOME_INTEIRO.match(v) and v.strip().lower() not in ELENCO_NOMES:
                        registra("V1", caminho, 0, "", f"{k} = {v}")
                    pilha.append(v)
            elif isinstance(no, list):
                pilha.extend(no)

# Regra R2: o verde diz QUANTO examinou.
print("── Vazamento de dado real de pessoa (RNF-03 · ADR 0006) ──")
print(f"  arquivos varridos: {arquivos}  ·  linhas varridas: {linhas_varridas}"
      f"  ·  registros JSON inspecionados: {registros_json}")
print(f"  sinais aplicados: 3 (V1 nome próprio em campo de pessoa · "
      f"V2 registro no formato da base da irmã · V3 base real lida por código)")
print(f"  campos de pessoa vigiados: {len(PESSOA)}  ·  chaves do esquema da irmã: "
      f"{len(CHAVES_IRMA)} (limiar {LIMIAR_IRMA} no mesmo registro)")
print(f"  elenco fictício declarado: {len(ELENCO)}  ·  "
      f"isenções de sabotagem declaradas: {isencoes}")

if achados:
    print(f"\n✗ {len(achados)} vazamento(s) de dado real de pessoa:", file=sys.stderr)
    for sinal, caminho, n, evidencia in achados:
        alvo = f"{caminho}:{n}" if n else caminho
        print(f"    [{sinal}] {alvo}  {evidencia}", file=sys.stderr)
    print("\n  Dado real de pessoa não entra neste repositório (ADR 0006). Troque por "
          "persona fictícia declarada, ou — se for base de sabotagem — marque a linha "
          f"com {MARCADOR} dentro de scripts/tests/.", file=sys.stderr)
    sys.exit(1)

print("\n✓ nenhum nome próprio em campo de pessoa, nenhum registro no formato da base real\n"
      "  da irmã e nenhum código lendo essa base.")
PY
