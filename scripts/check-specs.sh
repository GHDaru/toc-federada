#!/usr/bin/env bash
# check-specs.sh — fitness function for `specs/NNN-slug/`: the four artifacts exist, the
# spec carries the sections and the requirement types the taxonomy promises, the plan
# carries BOTH Constitution Check tables and declares all five conditional artifacts, the
# tasks carry the closing tail, and every spec is SCORED against the readiness rubric of
# ADR 0004 (cut-off ≥ 80).
#
# Por que existe: a taxonomia do ADR 0004 (Architecture Decision Record, registro de decisão
# arquitetural) e o formato de spec só valem se alguém os conferir. Sem portão, "a spec está
# no formato" é memória de agente, que relata intenção e não fato. Na irmã
# `gestaodeprioridades`, um plano nasceu com **uma** tabela de Constitution Check em vez de
# duas e ninguém viu — o `CLAUDE.md` de lá teve de ganhar a frase "um plano com apenas a
# primeira está incompleta" porque nenhum script olhava.
#
# ═════════════════════════════════════════════════════════════════════════════════
# A RÉGUA DE PRONTIDÃO (DoR — Definition of Ready, definição de pronto para começar)
# ═════════════════════════════════════════════════════════════════════════════════
# O ADR 0004 §5 fixa uma régua de 100 pontos, com corte em **≥ 80**, para uma spec poder
# abrir ciclo, e promete "verificação executável por `scripts/check-specs.sh`". **Este
# portão cumpre a promessa**: ele pontua, imprime a nota por spec e reprova quem ficar
# abaixo do corte.
#
#   | Dimensão      | Peso | O que a dimensão pergunta                                   |
#   |---------------|------|-------------------------------------------------------------|
#   | Completude    |  30  | as seções obrigatórias existem e estão preenchidas?         |
#   | Testabilidade |  25  | cada critério de aceite tem verificação executável?         |
#   | Clareza       |  20  | requisito em EARS, sigla aberta, sem termo vago?            |
#   | Escopo        |  15  | o que fica de fora está escrito? história tem dono?         |
#   | Casos-limite  |  10  | erro, vazio, concorrência e recusa estão previstos?         |
#
# ── Como cada dimensão é medida (o número não é mágico; é a conta abaixo) ─────────
#
# Cada dimensão é a soma de sinais **verificáveis do texto**, nunca de julgamento
# estético. Todo sinal é uma fração medida (numerador/denominador reais), e o portão
# imprime o denominador — regra R2, "portão verde exige quanto ele examinou".
#
#   COMPLETUDE (30) = C1 + C2 + C3
#     C1 (10) seções obrigatórias presentes, cabeçalho verbatim
#             → 10 × (seções presentes ÷ seções exigidas)
#     C2 (10) seção presente está PREENCHIDA, não só titulada
#             → 10 × (seções com ≥ 3 linhas de corpo não vazias ÷ seções presentes)
#     C3 (10) os tipos de item da taxonomia existem, cada um com ao menos uma linha
#             `SIGLA-NN:` própria → 10 × (tipos presentes ÷ tipos exigidos)
#             tipos exigidos: RF, RNF, F, L sempre; RI, RN, INT, US quando há módulo
#
#   TESTABILIDADE (25) = T1 + T2 + T3
#     T1 (12) linha da tabela de DoD (Definition of Done, definição de pronto) cuja
#             célula "Verificação executável" traz comando de verdade — trecho entre
#             crases fechadas ou ferramenta nomeada (pytest, grep, ls, diff, curl,
#             scripts/..., npm, node, python, jq, make, alembic, playwright, vitest,
#             lint-imports, test -f, wc) → 12 × (linhas com comando ÷ linhas da tabela)
#     T2  (8) requisito funcional citado em alguma linha da DoD ou do `tasks.md`
#             (intervalos `RF-11..RF-20` são expandidos) → 8 × (RF citados ÷ RF totais)
#     T3  (5) user story com critério Gherkin (Dado/Quando/Então) no próprio bloco
#             → 5 × (US com Gherkin ÷ US totais)
#
#   CLAREZA (20) = L1 + L2 + L3
#     L1  (8) RF em forma EARS (Easy Approach to Requirements Syntax): o modal DEVE/DEVEM
#             em maiúscula aparece até a 12ª palavra do requisito, ou até a 25ª quando a
#             linha abre com gatilho (QUANDO/SE/ENQUANTO/ONDE/CASO)
#             → 8 × (RF em EARS ÷ RF totais)
#     L2  (7) Princípio VIII, "sigla nunca nasce nua": toda sigla do catálogo abaixo que
#             aparece no corpo tem de estar aberta no bloco `> Siglas:` do cabeçalho
#             → 7 × (siglas do catálogo cobertas ÷ siglas do catálogo usadas)
#     L3  (5) ausência de termo vago (adequado, amigável, robusto, intuitivo, fácil,
#             simples, rápido, eficiente, otimizado, flexível, escalável, moderno, "se
#             possível", "etc.") nas linhas de requisito
#             → 5 × (linhas de requisito sem termo vago ÷ linhas de requisito)
#
#   ESCOPO (15) = E1 + E2
#     E1  (8) o que fica de fora está escrito: seção "Fora de escopo" (nível 2 ou 3) com
#             ≥ 2 linhas de conteúdo = 8; com 1 linha = 4; ausente = 0
#     E2  (7) história ligada a feature: toda feature (`**F1.1.1 — …`/`**FT-01 — …`) tem
#             ao menos uma US no próprio bloco; quando a spec não usa features, o
#             contêiner é o cabeçalho de nível 3 da seção (épico `### E1.1 — …` ou
#             frente de trabalho)
#             → 7 × (contêineres com ≥ 1 US ÷ contêineres)
#
#   CASOS-LIMITE (10) = B1 + B2 + B3
#     B1  (4) lacuna com risco declarado: linha `L-NN:` que diz risco baixo/médio/alto
#             → 4 × (lacunas com risco ÷ lacunas)
#     B2  (3) `## Clarify` com 1 a 5 marcadores `[DÚVIDA]` (o teto de 5 é do ADR 0004 §4):
#             dentro da faixa = 3; nenhuma dúvida ou mais de 5 = 0
#     B3  (3) requisito de erro/recusa/limite: linha RF/RI/RNF/RN cujo texto fala de
#             recusa, erro, inválido, vazio, concorrência, conflito, limite, falha,
#             timeout, expiração, duplicidade ou negação → 3 × (min(achados, 3) ÷ 3)
#
# Sinal declarado **não aplicável** por isenção (abaixo) sai da conta: a dimensão é
# reescalada sobre os sinais que restam, para a isenção não virar desconto silencioso.
# Ausência sem isenção **não** é não-aplicável: vale zero. A diferença é a que separa
# "o ciclo documental não tem tela" de "a spec esqueceu a user story".
#
# O que o portão NÃO faz: julgar se o requisito é *bom*. Ele mede forma, cobertura e
# presença de sinal — não substitui a revisão independente nem o gate humano, que
# continuam decidindo se a spec é a coisa certa. Passar em 80 é ter forma verificável,
# não ter razão.
#
# Isenção declarada (com o motivo escrito, para a lista não virar tapete): o **ciclo 001**
# é documental — não tem interface, não tem módulo de domínio e não entrega tela. As
# seções de módulo e o requisito de interface (RI) não se aplicam a ele; tudo o mais se
# aplica.
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

CORTE_DOR = 80.0

# ── insumos da régua ────────────────────────────────────────────────────────────
# Catálogo de siglas do projeto (sinal L2). Só entra sigla que o vocabulário deste
# repositório usa: medir sigla genérica produziria ruído (números romanos, palavras
# portuguesas em caixa alta), e ruído em portão é o anti-padrão 13.
CATALOGO_SIGLAS = [
    "TOC", "ARA", "ARF", "APR", "AT", "NC", "UDE", "APH", "ADR", "DoR", "DoD",
    "TDD", "DDD", "EARS", "RF", "RI", "RNF", "RN", "INT", "US", "OTel", "OTLP",
    "API", "JSON", "UUID", "SSE", "FSM", "CRUD", "SDK", "HTTP", "REST", "CI",
    "UI", "UX", "IA", "MIT", "DBR", "JWT", "SQL", "HTML", "CSS", "URL", "i18n",
]

TERMOS_VAGOS = re.compile(
    r"\b(adequad\w+|amigáve\w+|robust\w+|intuitiv\w+|fácil|fáceis|simples|rápid\w+|"
    r"eficiente\w*|otimizad\w+|flexíve\w+|escaláve\w+|modern\w+|se possível)\b|\betc\.",
    re.IGNORECASE)

KW_LIMITE = re.compile(
    r"recus\w+|erro|errado|inválid\w+|vazio|vazia|concorrên\w+|conflit\w+|limite|"
    r"falh\w+|timeout|expira\w+|duplicad\w+|duplicidade|negad\w+|nega\b",
    re.IGNORECASE)

FERRAMENTAS = re.compile(
    r"(?<![\w/])(pytest|grep|ls|npm|node|python3?|diff|curl|jq|make|alembic|playwright|"
    r"vitest|lint-imports|test -f|wc)(?![\w])")

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

def corpo_das_secoes(texto):
    """nome do cabeçalho de nível 2 -> corpo até o próximo cabeçalho de nível 2."""
    out, nome, buf = {}, None, []
    for l in texto.split("\n"):
        if l.startswith("## "):
            if nome is not None:
                out[nome] = "\n".join(buf)
            nome, buf = l[3:].strip(), []
        elif nome is not None:
            buf.append(l)
    if nome is not None:
        out[nome] = "\n".join(buf)
    return out

def blocos_de_item(texto, prefixo):
    """[(numero, texto do item até a linha em branco)] para linhas `PREFIXO-NN: ...`."""
    out, num, buf = [], None, None
    for l in texto.split("\n"):
        m = re.match(rf"^{prefixo}-(\d+):(.*)$", l)
        if m:
            if num is not None:
                out.append((num, " ".join(buf)))
            num, buf = m.group(1), [m.group(2).strip()]
        elif buf is not None:
            if not l.strip():
                out.append((num, " ".join(buf)))
                num, buf = None, None
            else:
                buf.append(l.strip())
    if num is not None:
        out.append((num, " ".join(buf)))
    return out

def celulas(linha):
    """Células de uma linha de tabela markdown, respeitando o pipe escapado `\\|`."""
    return [c.strip() for c in re.split(r"(?<!\\)\|", linha)][1:-1]

def refs_rf(texto):
    """Números de RF citados, com `RF-11..RF-20` e `RF-11–RF-20` expandidos."""
    vistos = set(int(n) for n in re.findall(r"RF-(\d+)", texto))
    for a, b in re.findall(r"RF-(\d+)\s*(?:\.\.|–|—|-|a)\s*RF-(\d+)", texto):
        ini, fim = int(a), int(b)
        if ini <= fim:
            vistos.update(range(ini, fim + 1))
    return vistos

def ears(txt):
    m = re.search(r"\bDEVEM?\b", txt)
    if not m:
        return False
    palavras = len(txt[:m.start()].split())
    gatilho = bool(re.match(r"^\s*(QUANDO|SE|ENQUANTO|ONDE|CASO)\b", txt))
    return palavras <= 12 or (gatilho and palavras <= 25)

def sigla_usada(sigla, texto):
    return re.search(rf"(?<![A-Za-z0-9]){re.escape(sigla)}(?![A-Za-z0-9])", texto)

conf = dict(artefatos=0, secoes=0, requisitos=0, tabelas=0, art=0, tail=0, dor=0)
isentos_aplicados = 0
notas = []          # (ciclo, nota, {dimensão: (pontos, peso)}, denominadores)
sinais_medidos = 0

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

        # ---- 2b · a régua de prontidão do ADR 0004 --------------------------------
        secoes = corpo_das_secoes(spec)
        tasks_txt = presentes.get("tasks.md", "")
        den = {}   # denominadores, para a saída dizer quanto examinou

        def frac(num, tot):
            return (num / tot) if tot else 0.0

        # -- COMPLETUDE ------------------------------------------------------------
        presentes_sec = [s for s in exigidas if s in secoes]
        c1 = 10.0 * frac(len(presentes_sec), len(exigidas))
        preenchidas = [s for s in presentes_sec
                       if len([l for l in secoes[s].split("\n") if l.strip()]) >= 3]
        c2 = 10.0 * frac(len(preenchidas), len(presentes_sec))
        tipos = ["RF", "RNF", "F", "L"] + ([] if isencao else ["RI", "RN", "INT", "US"])
        tipos_ok = []
        for tp in tipos:
            padrao = r"^- US-\d+" if tp == "US" else rf"^{tp}-\d+:"
            if re.search(padrao, spec, re.MULTILINE):
                tipos_ok.append(tp)
        c3 = 10.0 * frac(len(tipos_ok), len(tipos))
        den["seções"] = f"{len(presentes_sec)}/{len(exigidas)} presentes, " \
                        f"{len(preenchidas)} preenchidas"
        den["tipos"] = f"{len(tipos_ok)}/{len(tipos)}"
        completude = c1 + c2 + c3
        sinais_medidos += 3

        # -- TESTABILIDADE ---------------------------------------------------------
        dod = secoes.get("Critérios de aceite (DoD)", "")
        linhas_dod = [l for l in dod.split("\n")
                      if l.strip().startswith("|") and celulas(l)
                      and re.match(r"^\d+$", celulas(l)[0])]
        cab = [l for l in dod.split("\n")
               if l.strip().startswith("|") and "Verificação executável" in l]
        idx_verif = None
        if cab:
            cs = celulas(cab[0])
            for i, c in enumerate(cs):
                if "Verificação executável" in c:
                    idx_verif = i
        com_comando = 0
        for l in linhas_dod:
            cs = celulas(l)
            cel = cs[idx_verif] if (idx_verif is not None and idx_verif < len(cs)) else cs[-1]
            if re.search(r"`[^`]+`", cel) or FERRAMENTAS.search(cel):
                com_comando += 1
        t1 = 12.0 * frac(com_comando, len(linhas_dod))

        rf_itens = blocos_de_item(spec, "RF")
        citados = refs_rf(dod) | refs_rf(tasks_txt)
        rf_cobertos = [n for n, _ in rf_itens if int(n) in citados]
        t2 = 8.0 * frac(len(rf_cobertos), len(rf_itens))

        # user stories e o Gherkin do próprio bloco
        us_blocos = []
        atual = None
        for l in spec.split("\n"):
            if re.match(r"^- US-\d+", l):
                if atual is not None:
                    us_blocos.append(atual)
                atual = l
            elif atual is not None:
                if not l.strip() or l.startswith(("#", "**")):
                    us_blocos.append(atual)
                    atual = None
                else:
                    atual += " " + l.strip()
        if atual is not None:
            us_blocos.append(atual)
        com_gherkin = [b for b in us_blocos
                       if "Dado" in b and "Quando" in b and "Então" in b]
        t3_aplica = not (isencao and not us_blocos)
        t3 = 5.0 * frac(len(com_gherkin), len(us_blocos)) if t3_aplica else None
        den["DoD"] = f"{com_comando}/{len(linhas_dod)} linhas com comando"
        den["RF"] = f"{len(rf_cobertos)}/{len(rf_itens)} citados em DoD ou tasks"
        den["US"] = (f"{len(com_gherkin)}/{len(us_blocos)} com Gherkin"
                     if t3_aplica else "não aplicável (isenção)")
        pesos_t = [(t1, 12.0), (t2, 8.0)] + ([(t3, 5.0)] if t3_aplica else [])
        testabilidade = 25.0 * frac(sum(p for p, _ in pesos_t), sum(w for _, w in pesos_t))
        sinais_medidos += len(pesos_t)

        # -- CLAREZA ---------------------------------------------------------------
        em_ears = [n for n, txt in rf_itens if ears(txt)]
        l1 = 8.0 * frac(len(em_ears), len(rf_itens))

        m_sig = re.search(r"^> Siglas:(.*?)(?:\n\n|\Z)", spec, re.S | re.MULTILINE)
        bloco_siglas = m_sig.group(1) if m_sig else ""
        corpo_sem_codigo = re.sub(r"`[^`]*`", "", spec[m_sig.end():] if m_sig else spec)
        usadas = [s for s in CATALOGO_SIGLAS if sigla_usada(s, corpo_sem_codigo)]
        cobertas = [s for s in usadas if sigla_usada(s, bloco_siglas)]
        l2 = 7.0 * frac(len(cobertas), len(usadas))

        linhas_req = blocos_de_item(spec, "RF") + blocos_de_item(spec, "RI") \
            + blocos_de_item(spec, "RNF") + blocos_de_item(spec, "RN")
        sem_vago = [n for n, txt in linhas_req if not TERMOS_VAGOS.search(txt)]
        l3 = 5.0 * frac(len(sem_vago), len(linhas_req))
        den["EARS"] = f"{len(em_ears)}/{len(rf_itens)} RF"
        den["siglas"] = f"{len(cobertas)}/{len(usadas)} do catálogo abertas"
        den["vagos"] = f"{len(linhas_req) - len(sem_vago)} em {len(linhas_req)} requisitos"
        clareza = l1 + l2 + l3
        sinais_medidos += 3

        # -- ESCOPO ----------------------------------------------------------------
        fora = None
        for nome_sec, corpo in secoes.items():
            if re.match(r"(?i)^fora de escopo\b", nome_sec):
                fora = corpo
        if fora is None:
            m_h3 = re.search(r"(?im)^###\s+fora de escopo\b(.*?)(?=^#{2,3}\s|\Z)",
                             spec, re.S | re.M)
            fora = m_h3.group(1) if m_h3 else None
        n_fora = len([l for l in fora.split("\n") if l.strip()]) if fora is not None else 0
        e1 = 8.0 if n_fora >= 2 else (4.0 if n_fora == 1 else 0.0)

        secao_epicos = secoes.get("Épicos, features e user stories", "")
        conteineres, atual_c = [], None
        feats = re.findall(r"(?m)^\*\*(F[\w.\-]+)\s+—", secao_epicos)
        # Sem feature nomeada, o contêiner declarado é o cabeçalho de nível 3 da seção
        # (épico `### E1.1 — …` ou frente de trabalho): o sinal mede história com dono,
        # não a escolha de nomenclatura.
        chave = r"^\*\*(F[\w.\-]+)\s+—" if feats else r"^###\s+(.+?)\s*$"
        for l in secao_epicos.split("\n"):
            m = re.match(chave, l)
            if m:
                atual_c = [m.group(1), 0]
                conteineres.append(atual_c)
            elif atual_c is not None and re.match(r"^- US-\d+", l):
                atual_c[1] += 1
        e2_aplica = not (isencao and not conteineres)
        com_us = [c for c in conteineres if c[1] > 0]
        e2 = (7.0 * frac(len(com_us), len(conteineres))) if e2_aplica else None
        den["fora de escopo"] = f"{n_fora} linha(s)"
        den["features↔US"] = (f"{len(com_us)}/{len(conteineres)} com história"
                              if e2_aplica else "não aplicável (isenção)")
        pesos_e = [(e1, 8.0)] + ([(e2, 7.0)] if e2_aplica else [])
        escopo = 15.0 * frac(sum(p for p, _ in pesos_e), sum(w for _, w in pesos_e))
        sinais_medidos += len(pesos_e)

        # -- CASOS-LIMITE ----------------------------------------------------------
        lacunas = blocos_de_item(spec, "L")
        com_risco = [n for n, txt in lacunas
                     if re.search(r"risco\s*\**\s*(baixo|médio|medio|alto)", txt, re.I)]
        b1 = 4.0 * frac(len(com_risco), len(lacunas))
        n_duvidas = len(re.findall(r"\[DÚVIDA\]", secoes.get("Clarify", "")))
        b2 = 3.0 if 1 <= n_duvidas <= 5 else 0.0
        de_limite = [n for n, txt in linhas_req if KW_LIMITE.search(txt)]
        b3 = 3.0 * (min(len(de_limite), 3) / 3.0)
        den["lacunas"] = f"{len(com_risco)}/{len(lacunas)} com risco declarado"
        den["dúvidas"] = f"{n_duvidas} no Clarify (teto 5)"
        den["erro/recusa"] = f"{len(de_limite)} requisito(s) (alvo 3)"
        casos = b1 + b2 + b3
        sinais_medidos += 3

        dims = {"Completude": (completude, 30.0),
                "Testabilidade": (testabilidade, 25.0),
                "Clareza": (clareza, 20.0),
                "Escopo": (escopo, 15.0),
                "Casos-limite": (casos, 10.0)}
        nota = sum(p for p, _ in dims.values())
        conf["dor"] += 1
        notas.append((ciclo, nota, dims, den))

        if nota + 1e-9 < CORTE_DOR:
            pior = min(dims.items(), key=lambda kv: kv[1][0] / kv[1][1])
            falha(f"{caminho}: nota DoR {nota:.1f} < {CORTE_DOR:.0f} (régua do ADR 0004 §5) "
                  f"— dimensão mais baixa: {pior[0]} ({pior[1][0]:.1f}/{pior[1][1]:.0f}, "
                  f"aproveitamento {100 * pior[1][0] / pior[1][1]:.0f}%); "
                  + " · ".join(f"{k} {v[0]:.1f}/{v[1]:.0f}" for k, v in dims.items()))

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
      f"{conf['tabelas']} · tokens ART {conf['art']} · tokens TAIL {conf['tail']} · "
      f"specs pontuadas {conf['dor']}"
      f"  =  {total}")
print(f"  isenções aplicadas: {isentos_aplicados}"
      + ("".join(f"\n    · ciclo {c}: {o} — {m}" for c, (o, m) in ISENTOS.items())
         if isentos_aplicados else ""))

if notas:
    print()
    print(f"── Régua de prontidão (DoR) do ADR 0004 §5 — corte ≥ {CORTE_DOR:.0f} ──")
    print("  ciclo │ Compl/30 │ Teste/25 │ Clar/20 │ Escopo/15 │ Limite/10 │  nota │")
    for ciclo, nota, dims, _ in notas:
        marca = "✓" if nota + 1e-9 >= CORTE_DOR else "✗"
        print(f"   {ciclo}  │   {dims['Completude'][0]:5.1f}  │   "
              f"{dims['Testabilidade'][0]:5.1f}  │  {dims['Clareza'][0]:5.1f}  │   "
              f"{dims['Escopo'][0]:5.1f}   │   {dims['Casos-limite'][0]:5.1f}   │ "
              f"{nota:5.1f} │ {marca}")
    print("  denominadores medidos (R2 — o verde diz quanto examinou):")
    for ciclo, _, _, den in notas:
        print(f"    {ciclo}: " + " · ".join(f"{k} {v}" for k, v in den.items()))
    print(f"  sinais medidos ao todo: {sinais_medidos} "
          f"(14 por spec, menos os declarados não aplicáveis por isenção)")

if falhas:
    print(f"\n✗ {len(falhas)} falha(s):", file=sys.stderr)
    for f in falhas:
        print(f"    {f}", file=sys.stderr)
    sys.exit(1)

print("\n✓ todo ciclo tem os quatro artefatos, spec com as seções e os tipos de requisito,\n"
      "  plano com as duas tabelas e os cinco artefatos declarados, tasks com a cauda,\n"
      f"  e toda spec pontua ≥ {CORTE_DOR:.0f} na régua de prontidão do ADR 0004.")
PY
