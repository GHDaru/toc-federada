#!/usr/bin/env python3
"""medir-base.py — valida a base sintética da Instituição Horizonte e mede o domínio.

Por que existe: a regra R1 do `CLAUDE.md` proíbe número digitado à mão. Toda contagem
sobre a base — nós, arestas, UDEs aprovados nos critérios formais — sai daqui, e o que
vai para `docs/produto/visao.md` e para `docs/produto/dados/README.md` é a saída colada
deste comando.

O que ele faz, em quatro partes:

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
     silêncio até "dar certo". **Este passo não é evidência sobre as checagens**: a
     base e as checagens têm o mesmo autor, então concordância entre elas é
     tautologia. Por isso existe o passo 4.
  4. **Mede o CONJUNTO DE CONTROLE** (`CONTROLE`, mais abaixo): enunciados de UDE que
     já existiam antes e fora deste repositório, copiados literalmente da linhagem
     TOC-Builder, cada um com caminho e linha. O rótulo bom/ruim é o que a fonte
     escreveu, não o nosso, e nenhum item declara resultado esperado. É a única parte
     do script em que as checagens podem errar, e o relatório imprime o erro:
     **falso positivo** (a fonte diz bom, a checagem reprova) e **falso negativo**
     (a fonte diz ruim, a checagem aprova).

Uso: python3 docs/produto/dados/medir-base.py [caminho-do-json]
Saída: relatório em texto. Código 0 se a base é válida e o veredito autoral bate; 1 se
não. O resultado do controle NÃO altera o código de saída — ele é medição a publicar,
não portão: transformá-lo em portão convidaria a ajustar o controle até ficar verde,
que é exatamente a circularidade que ele existe para quebrar.
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
# CONJUNTO DE CONTROLE — os enunciados NÃO foram escritos aqui
#
# Por que existe: a base da Instituição Horizonte foi redigida pelo mesmo autor que
# escreveu as oito checagens, e escrita de propósito com as patologias que elas procuram.
# O "3 de 12" que sai dela mede o acordo do autor consigo mesmo, não o mundo — a linha
# "divergências entre o esperado na base e o medido: 0" é tautologia, não evidência.
#
# O controle abaixo corrige isso pela única via disponível sem dado de pessoa real:
# enunciados de UDE que já existiam ANTES e FORA deste repositório, colhidos da linhagem
# TOC-Builder, onde foram escritos como material didático de prompt e de tela — sem
# conhecimento nenhum destas checagens, que nasceram quatro gerações depois. Cada item
# traz o caminho e a linha de onde foi copiado, e o RÓTULO É DA FONTE, nunca nosso: o
# prompt da linhagem diz, com todas as letras, quais enunciados são bons e quais são
# ruins, e é contra esse rótulo alheio que as checagens são medidas.
#
# Regras que mantêm o controle independente:
#   1. Nenhum enunciado foi redigido, corrigido ou parafraseado aqui — são cópias literais.
#   2. Nenhum item declara resultado esperado. Não há campo `esperado_reprovado` no
#      controle: se houvesse, a tautologia voltaria por outra porta.
#   3. O rótulo é o da fonte. Onde a fonte não rotula, o rótulo é "sem rótulo", e o item
#      não entra na conta de concordância.
#
# Limite honesto, declarado no próprio dado: são NOVE enunciados. É amostra pequena, e
# pequena porque é tudo o que a linhagem escreveu — os oito de `constants.ts` aparecem
# idênticos nas quatro gerações, e o nono é o texto de exemplo da tela de boas-vindas.
# As skills locais de domínio (`toc-evaporating-cloud`, `toc-prt`) foram lidas e não
# trazem enunciado de UDE nenhum.
# --------------------------------------------------------------------------------------

CONTROLE = [
    {
        "id": "K-01",
        "texto": "Nosso desempenho de entrega no prazo é de 60%",
        "fonte": "tocbuilderv3/constants.ts:136",
        "rotulo": "bom",
        "rotulo_da_fonte": 'UDE de "existência de lacuna" — o tipo que o prompt manda PREFERIR',
    },
    {
        "id": "K-02",
        "texto": "Recursos frequentemente não estão disponíveis",
        "fonte": "tocbuilderv3/constants.ts:137",
        "rotulo": "nao_preferido",
        "rotulo_da_fonte": 'UDE de "dificuldade em fechar a lacuna" — aceito, mas preterido',
    },
    {
        "id": "K-03",
        "texto": "Falta de treinamento causa erros.",
        "fonte": "tocbuilderv3/constants.ts:162",
        "rotulo": "ruim",
        "rotulo_da_fonte": "Exemplo Ruim: UDE + Causa",
    },
    {
        "id": "K-04",
        "texto": "A taxa de erros no processo X é de 15%.",
        "fonte": "tocbuilderv3/constants.ts:162",
        "rotulo": "bom",
        "rotulo_da_fonte": "Bom UDE — a correção que a fonte propõe para K-03",
    },
    {
        "id": "K-05",
        "texto": "Precisamos de um novo software para gerenciar tarefas.",
        "fonte": "tocbuilderv3/constants.ts:163",
        "rotulo": "ruim",
        "rotulo_da_fonte": "Exemplo Ruim: Solução",
    },
    {
        "id": "K-06",
        "texto": "Tarefas frequentemente ultrapassam o prazo.",
        "fonte": "tocbuilderv3/constants.ts:163",
        "rotulo": "bom",
        "rotulo_da_fonte": "Bom UDE — a correção que a fonte propõe para K-05",
    },
    {
        "id": "K-07",
        "texto": "O tempo médio de ciclo do pedido é de 10 dias.",
        "fonte": "tocbuilderv3/constants.ts:171",
        "rotulo": "bom",
        "rotulo_da_fonte": "Exemplo de Lacuna (Preferível como UDE)",
    },
    {
        "id": "K-08",
        "texto": "Há muitos gargalos no processo de aprovação.",
        "fonte": "tocbuilderv3/constants.ts:172",
        "rotulo": "nao_preferido",
        "rotulo_da_fonte": "Exemplo de Dificuldade (Pode ser uma causa)",
    },
    {
        "id": "K-09",
        "texto": "O churn de clientes está alto.",
        "fonte": "tocbuilderv3/components/CanvasWelcome.tsx:11",
        "rotulo": "sem_rotulo",
        "rotulo_da_fonte": "texto de exemplo oferecido na tela de boas-vindas da ARA",
    },
]

# Os oito de constants.ts aparecem com o mesmo texto nas quatro gerações da linhagem.
CONTROLE_ESPELHOS = [
    "TOC-Builder/constants.ts:158,159,184,185,193,194",
    "TOC-Builder-V2/constants.ts:129,130,155,156,164,165",
    "TOC-Builder-APP/constants.ts:129,130,155,156,164,165",
    "tocbuilderv3/constants.ts:136,137,162,163,171,172",
]

FIM_DE_FRASE = (".", "!", "?", "…")


def normaliza_pontuacao(t):
    """Acrescenta ponto final ao enunciado citado sem ele.

    Não é correção de redação: dois enunciados da fonte estão dentro de parênteses ou de
    aspas num texto corrido e por isso foram citados sem o ponto. Medir só a forma
    literal faria a CD-1 reprovar um artefato de citação, e medir só a normalizada
    esconderia que a CD-1 depende de pontuação. Por isso as duas contas são impressas.
    """
    t = t.rstrip()
    return t if t.endswith(FIM_DE_FRASE) else t + "."


def avalia(texto):
    """Aplica as oito checagens e devolve (passou, [motivos])."""
    motivos = []
    for sigla, _, _, fn in CRITERIOS:
        ok, motivo = fn(texto)
        if not ok:
            motivos.append(f"{sigla} {motivo}")
    return not motivos, motivos


def mede_controle():
    """Roda as checagens sobre o controle e classifica cada item contra o rótulo da fonte.

    Devolve (linhas_do_relatorio, resumo). Nenhuma expectativa nossa entra aqui: o
    veredito é comparado apenas com o rótulo que a linhagem escreveu.
    """
    linhas = []
    passa_literal = passa_norm = 0
    concordancias, falsos_negativos, falsos_positivos, sem_veredito = [], [], [], []

    for item in CONTROLE:
        literal = item["texto"]
        normal = normaliza_pontuacao(literal)
        ok_lit, mot_lit = avalia(literal)
        ok_norm, mot_norm = avalia(normal)
        passa_literal += int(ok_lit)
        passa_norm += int(ok_norm)

        marca = "PASSA " if ok_norm else "REPROVA"
        linhas.append(f"  {item['id']}  {marca}  [fonte: {item['rotulo']}]  {literal}")
        linhas.append(f"            fonte: {item['fonte']} — {item['rotulo_da_fonte']}")
        for m in mot_norm:
            linhas.append(f"            └ {m}")
        if ok_lit != ok_norm:
            so_cd1 = all(m.startswith("CD-1") for m in mot_lit)
            nota = "só a CD-1, por pontuação" if so_cd1 else "checagens além da CD-1"
            linhas.append(f"            ⚠ literal (sem ponto final) REPROVA — {nota}")

        if item["rotulo"] == "bom":
            (concordancias if ok_norm else falsos_positivos).append(item["id"])
        elif item["rotulo"] == "ruim":
            (falsos_negativos if ok_norm else concordancias).append(item["id"])
        else:
            sem_veredito.append(item["id"])

    resumo = {
        "total": len(CONTROLE),
        "passa_literal": passa_literal,
        "passa_norm": passa_norm,
        "rotulados": len(concordancias) + len(falsos_positivos) + len(falsos_negativos),
        "concordancias": concordancias,
        "falsos_positivos": falsos_positivos,
        "falsos_negativos": falsos_negativos,
        "sem_veredito": sem_veredito,
    }
    return linhas, resumo


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
        passou, motivos = avalia(u["texto"])
        (aprovados if passou else reprovados).append(u["id"])
        marca = "PASSA " if passou else "REPROVA"
        print(f"  {u['id']}  {marca}  {u['texto']}")
        for m in motivos:
            print(f"            └ {m}")
        if passou == u.get("esperado_reprovado", False):
            divergencias.append(u["id"])

    total = len(udes)
    print()
    print(f"  NÚMERO AUTORAL — UDEs medidos: {total}  ·  passam nos {len(CRITERIOS)} "
          f"critérios decidíveis: {len(aprovados)} ({', '.join(aprovados)})  ·  "
          f"reprovam: {len(reprovados)}")
    print(f"  divergências entre o esperado na base e o medido: {len(divergencias)} "
          f"— isto é acordo do autor consigo mesmo, não evidência: quem escreveu os "
          f"enunciados")
    print(f"    escreveu as checagens. O que vale como evidência é o controle abaixo.")
    print("  fora do alcance de qualquer função pura (exigem julgamento):")
    for num, texto in INDECIDIVEIS:
        print(f"    característica {num} — {texto}")

    linhas_ctrl, r = mede_controle()
    print()
    print("── Conjunto de controle · enunciados NÃO escritos aqui ──")
    arquivos = sorted({i["fonte"].rsplit(":", 1)[0] for i in CONTROLE})
    print(f"  enunciados: {r['total']}  ·  colhidos de {len(arquivos)} arquivo(s) da "
          f"linhagem TOC-Builder, anteriores a estas checagens:")
    for a in arquivos:
        print(f"    {a}")
    print("  os oito de constants.ts aparecem com o mesmo texto nas quatro gerações:")
    for e in CONTROLE_ESPELHOS:
        print(f"    {e}")
    print("  rótulo de cada enunciado = o que a FONTE diz dele; nenhum resultado esperado "
          "foi declarado aqui")
    print()
    for l in linhas_ctrl:
        print(l)
    print()
    print(f"  NÚMERO DE CONTROLE — enunciados: {r['total']}  ·  passam (texto normalizado): "
          f"{r['passa_norm']}  ·  passam (texto literal, como citado): {r['passa_literal']}")
    print(f"  rotulados pela fonte como bom/ruim: {r['rotulados']}  ·  "
          f"concordância: {len(r['concordancias'])} "
          f"({', '.join(r['concordancias']) or '—'})")
    print(f"  FALSO POSITIVO (a fonte diz bom, a checagem reprova): "
          f"{len(r['falsos_positivos'])} ({', '.join(r['falsos_positivos']) or '—'})")
    print(f"  FALSO NEGATIVO (a fonte diz ruim, a checagem aprova): "
          f"{len(r['falsos_negativos'])} ({', '.join(r['falsos_negativos']) or '—'})")
    print(f"  sem veredito possível (a fonte não rotula bom/ruim): "
          f"{len(r['sem_veredito'])} ({', '.join(r['sem_veredito']) or '—'})")

    taxa_autoral = len(aprovados) / total if total else 0
    taxa_ctrl = r["passa_norm"] / r["total"] if r["total"] else 0
    print()
    print("── Autoral × controle ──")
    print(f"  autoral:  {len(aprovados)}/{total} passam ({taxa_autoral:.0%}) — base escrita "
          f"para exercitar as checagens")
    print(f"  controle: {r['passa_norm']}/{r['total']} passam ({taxa_ctrl:.0%}) — enunciados "
          f"escritos como material didático, a maioria para ser exemplar")
    print(f"  as duas taxas medem coisas diferentes e NENHUMA estima prevalência de oficina; "
          f"a amostra de")
    print(f"  controle tem {r['total']} enunciados e é pequena porque é tudo o que a "
          f"linhagem escreveu.")

    if falhas or divergencias:
        print()
        print(f"✗ {len(falhas)} falha(s) estrutural(is) e {len(divergencias)} divergência(s).")
        return 1
    print()
    print(f"✓ base válida ({len(nos)} nós, {n_arestas} arestas, nuvem de 5 entidades e 7 "
          f"premissas); veredito autoral bate com o documentado e o controle de "
          f"{r['total']} enunciados")
    print(f"  externos foi medido: {len(r['falsos_positivos'])} falso(s) positivo(s), "
          f"{len(r['falsos_negativos'])} falso(s) negativo(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
