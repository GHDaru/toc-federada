#!/usr/bin/env python3
"""medir-base.py — valida a base sintética da Instituição Horizonte e mede o domínio.

Por que existe: a regra R1 do `CLAUDE.md` proíbe número digitado à mão. Toda contagem
sobre a base — nós, arestas, UDEs aprovados nos critérios formais — sai daqui, e o que
vai para `docs/produto/visao.md` e para `docs/produto/dados/README.md` é a saída colada
deste comando.

O que ele faz, em três partes:

  1. **Valida a estrutura** da base (`analise-horizonte.json`): identificadores únicos,
     arestas com as duas pontas existentes, nenhum ciclo na Árvore da Realidade Atual
     (ARA), nenhum nó órfão, a Nuvem de Conflito com as cinco entidades e as sete
     arestas com premissa escrita.
  2. **Aplica os critérios formais de UDE** — Efeito Indesejável — que a 4ª geração da
     linhagem embutiu num prompt de modelo de linguagem
     (`tocbuilderv3/constants.ts:122-133`, características 1 a 11 de um UDE bem
     articulado). Sete das onze características viram função pura aqui; quatro delas
     (1, 4, 5 e 7) dependem de julgamento sobre o sistema analisado e ficam declaradas
     como fora do alcance de qualquer função — é essa fronteira que o épico E2.1
     (spec 005) precisa implementar.
  3. **Confere o veredito contra a documentação da base**: cada UDE traz o campo
     `esperado_reprovado`, escrito por quem redigiu a base. Divergência entre o
     esperado e o medido é falha — é o que impede o critério de ser ajustado em
     silêncio até "dar certo".

Uso: python3 docs/produto/dados/medir-base.py [caminho-do-json]
Saída: relatório em texto. Código 0 se a base é válida e o veredito bate; 1 se não.
Sem dependência externa: biblioteca padrão apenas.
"""

import json
import re
import sys
from pathlib import Path

BASE_PADRAO = Path(__file__).with_name("analise-horizonte.json")

# --------------------------------------------------------------------------------------
# Os critérios decidíveis, mapeados uma a uma às características de
# tocbuilderv3/constants.ts:122-133. Cada um é uma função pura sobre o texto do UDE:
# sem rede, sem modelo, sem estado. Devolve (passou, motivo).
# --------------------------------------------------------------------------------------

PASSADO = re.compile(
    r"\b\w{3,}(?:ou|eu|iu|aram|eram|iram|ava|avam|iam)\b", re.IGNORECASE)
PASSADO_IRREGULAR = {"foi", "foram", "era", "eram", "teve", "tiveram", "houve",
                     "fez", "fizeram", "pôde", "puderam", "veio", "vieram"}
EXCECAO_TEMPORAL = {"seu", "seus", "meu", "meus", "teu", "céu", "grau", "europeu",
                    "ateu", "judeu", "chapéu", "troféu", "museu"}
FUTURO = re.compile(r"\b\w{3,}r(?:á|ão|ei|emos|eis|íamos)\b", re.IGNORECASE)

INFINITIVO = re.compile(r"^[A-ZÁÉÍÓÚÂÊÔÃÕÇ]\w{2,}(?:ar|er|ir)$")

CULPA = ("desleixad", "não se importa", "incompeten", "preguiç", "por culpa",
         "falta de comprometimento", "relapso", "descuidad", "má vontade")
SOLUCAO_OCULTA = ("falta um ", "falta uma ", "falta de um ", "falta de uma ",
                  "precisamos de ", "deveria haver", "não temos um ", "não temos uma ",
                  "seria necessário", "bastaria ")
COORDENACAO = (";", " e também ", " bem como ", " além disso", " e ainda ")
RE_COORDENACAO = re.compile(r"\se\s(?:o|a|os|as)\s", re.IGNORECASE)
CAUSA_NA_FRASE = ("porque", "devido a", "por causa de", "já que", "uma vez que",
                  "em razão de", "em função de", "pois ", "em decorrência de")
SUBJETIVO = ("péssim", "ruim", "horrív", "absurd", "inaceitáv", "excessivamente",
             "claramente", "desleixad", "muito ", "ótim", "terrível")


def _palavras(texto):
    return re.findall(r"[\wÀ-ÿ%]+", texto)


def c01_frase_completa(t):
    """Característica 2 (parte 1): deve ser uma frase completa."""
    ok = bool(t[:1].isupper() and t.rstrip().endswith(".") and len(_palavras(t)) >= 4)
    return ok, "" if ok else "não é frase completa (maiúscula inicial, ponto final, ≥4 palavras)"


def c02_tempo_presente(t):
    """Característica 2 (parte 2): escrita no tempo presente."""
    for p in _palavras(t):
        b = p.lower()
        if b in EXCECAO_TEMPORAL:
            continue
        if b in PASSADO_IRREGULAR or PASSADO.fullmatch(b):
            return False, f'verbo fora do presente: "{p}"'
        if FUTURO.fullmatch(b):
            return False, f'verbo fora do presente: "{p}"'
    return True, ""


def c03_estado_nao_acao(t):
    """Característica 3: descrição do estado do sistema, não uma ação."""
    primeira = _palavras(t)[0] if _palavras(t) else ""
    if INFINITIVO.fullmatch(primeira):
        return False, f'a frase começa pela ação "{primeira}" (verbo no infinitivo)'
    return True, ""


def c04_nao_culpa(t):
    """Característica 6: não deve culpar alguém."""
    b = t.lower()
    for m in CULPA:
        if m in b:
            return False, f'atribui culpa a pessoas: "{m}"'
    return True, ""


def c05_nao_e_solucao(t):
    """Característica 8: não deve ser uma solução oculta."""
    b = t.lower()
    for m in SOLUCAO_OCULTA:
        if m in b:
            return False, f'solução disfarçada de efeito: "{m.strip()}"'
    return True, ""


def c06_uma_entidade(t):
    """Característica 9: deve conter apenas uma entidade."""
    b = t.lower()
    for m in COORDENACAO:
        if m in b:
            return False, f'duas entidades na mesma frase: "{m.strip()}"'
    achado = RE_COORDENACAO.search(t)
    if achado:
        return False, f'duas entidades na mesma frase: "{achado.group(0).strip()}"'
    return True, ""


def c07_sem_causa_embutida(t):
    """Característica 10: não deve incluir sua causa na verbalização."""
    b = t.lower()
    for m in CAUSA_NA_FRASE:
        if m in b:
            return False, f'traz a própria causa: "{m.strip()}"'
    return True, ""


def c08_factual(t):
    """Característica 11: deve ser factual, não subjetivo."""
    b = t.lower()
    for m in SUBJETIVO:
        if m in b:
            return False, f'juízo de valor: "{m.strip()}"'
    return True, ""


CRITERIOS = [
    ("CD-1", "frase completa", "2", c01_frase_completa),
    ("CD-2", "tempo presente", "2", c02_tempo_presente),
    ("CD-3", "estado, não ação", "3", c03_estado_nao_acao),
    ("CD-4", "não culpa pessoas", "6", c04_nao_culpa),
    ("CD-5", "não é solução oculta", "8", c05_nao_e_solucao),
    ("CD-6", "uma única entidade", "9", c06_uma_entidade),
    ("CD-7", "não traz a causa", "10", c07_sem_causa_embutida),
    ("CD-8", "factual, não subjetivo", "11", c08_factual),
]

INDECIDIVEIS = [
    ("1", "é queixa sobre um problema contínuo que limita o desempenho"),
    ("4", "está dentro da área de responsabilidade ou influência"),
    ("5", "algo pode ser feito a respeito"),
    ("7", "não é uma causa especulada"),
]


# --------------------------------------------------------------------------------------
# Validação estrutural
# --------------------------------------------------------------------------------------

def valida(base):
    falhas = []
    nos = base["ara"]["nos"]
    ids = [n["id"] for n in nos]
    if len(ids) != len(set(ids)):
        falhas.append("há identificadores repetidos entre os nós da ARA")
    conhecidos = set(ids)
    arestas = base["ara"]["arestas"]
    for a in arestas:
        for ponta in ("de", "para"):
            if a[ponta] not in conhecidos:
                falhas.append(f'aresta {a["de"]}→{a["para"]}: ponta "{a[ponta]}" não existe')

    ligados = {a["de"] for a in arestas} | {a["para"] for a in arestas}
    for n in nos:
        if n["id"] not in ligados:
            falhas.append(f'nó {n["id"]} não participa de nenhuma aresta causal')

    # ciclo na ARA: busca em profundidade com marcação de cinza
    saida = {}
    for a in arestas:
        saida.setdefault(a["de"], []).append(a["para"])
    cor = {i: 0 for i in ids}
    ciclos = []

    def visita(n, pilha):
        cor[n] = 1
        pilha.append(n)
        for d in saida.get(n, []):
            if cor.get(d) == 1:
                ciclos.append(" → ".join(pilha[pilha.index(d):] + [d]))
            elif cor.get(d) == 0:
                visita(d, pilha)
        pilha.pop()
        cor[n] = 2

    for n in ids:
        if cor[n] == 0:
            visita(n, [])
    for c in sorted(set(ciclos)):
        falhas.append(f"ciclo causal na ARA: {c}")

    nuvem = base["nuvem"]
    if len(nuvem["entidades"]) != 5:
        falhas.append(f'a Nuvem de Conflito tem {len(nuvem["entidades"])} entidades, e são 5')
    if len(nuvem["arestas"]) != 7:
        falhas.append(f'a Nuvem de Conflito tem {len(nuvem["arestas"])} arestas, e são 7')
    ids_nuvem = {e["id"] for e in nuvem["entidades"]}
    for a in nuvem["arestas"]:
        if not a.get("premissa", "").strip():
            falhas.append(f'a aresta {a["de"]}→{a["para"]} da nuvem não declara premissa')
        for ponta in ("de", "para"):
            if a[ponta] not in ids_nuvem:
                falhas.append(f'aresta da nuvem cita entidade inexistente: "{a[ponta]}"')
    if not base.get("sintetica"):
        falhas.append('a base não declara "sintetica": true — exigência do ADR 0006')
    return falhas, len(arestas)


def main():
    caminho = Path(sys.argv[1]) if len(sys.argv) > 1 else BASE_PADRAO
    base = json.loads(caminho.read_text(encoding="utf-8"))

    falhas, n_arestas = valida(base)

    nos = base["ara"]["nos"]
    udes = [n for n in nos if n["tipo"] == "ude"]
    causas = [n for n in nos if n["tipo"] in ("causa", "causa_raiz")]

    print(f"── Base sintética · {base['organizacao']['nome']} · versão {base['versao']} ──")
    print(f"  arquivo: {caminho.name}  ·  sintética: {base['sintetica']}  ·  personas: "
          f"{len(base['personas'])}")
    print(f"  ARA: {len(nos)} nós ({len(udes)} UDEs, {len(causas)} causas) · "
          f"{n_arestas} arestas causais")
    print(f"  Nuvem de Conflito: {len(base['nuvem']['entidades'])} entidades · "
          f"{len(base['nuvem']['arestas'])} arestas com premissa · "
          f"{len(base['nuvem']['injecoes'])} injeções")
    print(f"  validação estrutural: {len(falhas)} falha(s)")
    for f in falhas:
        print(f"    ✗ {f}")

    print()
    print(f"── Critérios formais de UDE (tocbuilderv3/constants.ts:122-133) ──")
    print(f"  características do prompt: 11  ·  decidíveis por função pura: "
          f"{len(CRITERIOS)} checagens cobrindo 7  ·  dependentes de julgamento: "
          f"{len(INDECIDIVEIS)}")
    print()

    aprovados, reprovados, divergencias = [], [], []
    for u in udes:
        motivos = []
        for sigla, _, _, fn in CRITERIOS:
            ok, motivo = fn(u["texto"])
            if not ok:
                motivos.append(f"{sigla} {motivo}")
        passou = not motivos
        (aprovados if passou else reprovados).append(u["id"])
        marca = "PASSA " if passou else "REPROVA"
        print(f"  {u['id']}  {marca}  {u['texto']}")
        for m in motivos:
            print(f"            └ {m}")
        if passou == u.get("esperado_reprovado", False):
            divergencias.append(u["id"])

    total = len(udes)
    print()
    print(f"  UDEs medidos: {total}  ·  passam nos {len(CRITERIOS)} critérios decidíveis: "
          f"{len(aprovados)} ({', '.join(aprovados)})  ·  reprovam: {len(reprovados)}")
    print(f"  divergências entre o esperado na base e o medido: {len(divergencias)}")
    print("  fora do alcance de qualquer função pura (exigem julgamento):")
    for num, texto in INDECIDIVEIS:
        print(f"    característica {num} — {texto}")

    if falhas or divergencias:
        print()
        print(f"✗ {len(falhas)} falha(s) estrutural(is) e {len(divergencias)} divergência(s).")
        return 1
    print()
    print(f"✓ base válida ({len(nos)} nós, {n_arestas} arestas, nuvem de 5 entidades e 7 "
          f"premissas) e veredito dos critérios bate com o documentado.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
