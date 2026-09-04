# QA report 001 — Fundação e planejamento (ciclo documental)

> Siglas deste documento: **DoD** — Definition of Done (definição de pronto) · **DoR** —
> Definition of Ready (definição de pronto para começar) · **ADR** — Architecture Decision
> Record (Registro de Decisão Arquitetural) · **TOC** — Teoria das Restrições · **APH** —
> Aplicação ↔ Harness · **UDE** — Efeito Indesejável · **ARA** — Árvore da Realidade Atual ·
> **NC** — Nuvem de Conflito · **RF** — requisito funcional · **RI** — requisito de
> interface · **RNF** — requisito não funcional · **RN** — regra de negócio · **INT** —
> integração · **L** — lacuna declarada · **D-NN** — defeito medido da linhagem.

- **Data**: 2026-09-03 (bateria de portões) · **Fecho do lado do agente**: 2026-09-04 ·
  **Raia**: plena
- **Veredito atual**: **revisado, corrigido e fechado do lado do agente — aguardando o gate
  humano.** O percurso completo, estado por estado e com data, está em **§0**; os achados da
  revisão independente, numerados e com destino, em **§5**; o que aguarda a assinatura do
  Product Steward em **§8**; o que fica de dívida para o ciclo seguinte, com dono, em **§9**.
- **Portões executados**: 18 verificações distintas — **17 verdes, 1 vermelha**. A vermelha
  que restou é a de conformidade (§4.1), que é do método e não deste repositório. A outra —
  a linha 11 da DoD — **não foi afrouxada para passar**: o critério media caminho citado
  quando dizia medir vazamento, foi **reescrito para medir conteúdo**, a troca está
  **declarada na própria spec** (`spec.md`, "Mudança declarada no critério 11") e o critério
  novo só conta como verde porque **reprova quatro sabotagens** que plantam vazamento de
  verdade (§4.2, §7).

> **Regra R1 e R2 aplicadas linha a linha.** Toda saída abaixo é a saída **literal** do
> comando escrito ao lado, executado neste repositório — em **2026-09-03** nas seções §1 a
> §4 e §6 a §7, e em **2026-09-04** no que este fechamento acrescentou (§0, §1.1, §5, §9),
> com a data dita em cada bloco. Nenhum `✓` foi transcrito; nenhum número foi lembrado. Onde o portão imprime o tamanho do que examinou,
> esse número está colado — verde sem denominador não é evidência.

## 0 · Histórico de veredito — os estados por que este ciclo passou

> Um relatório que mostra só o estado final apaga a diferença entre "passou de primeira" e
> "reprovou, foi corrigido e passou". As duas coisas custam o mesmo a ler e valem coisas
> opostas. A tabela abaixo é o percurso; cada linha aponta a seção deste documento que a
> sustenta.

| # | Data | Estado | O que aconteceu | Evidência |
|---|---|---|---|---|
| **V1** | 2026-09-03 | **construído** | Dez peças do corpus produzidas em lotes paralelos sem sobreposição de caminho (tarefas T-06 a T-12 do `tasks.md`). | `tasks.md`, seção "Construção" |
| **V2** | 2026-09-03 | **REPROVADO — 9 × 1** | Gauntlet de crítica às cegas: cada peça comparada por um crítico em contexto fresco contra dois corpora externos. Nove venceram; a **visão de produto** perdeu, pela circularidade da base autoral das checagens de Efeito Indesejável (UDE). | §5 |
| **V3** | 2026-09-03 | **corrigido** | Oito achados aplicados (**A1–A8**, §5), o maior deles o retrabalho da visão dirigido pela lacuna nomeada: conjunto de controle externo, lacuna L-03 declarada em aberto, defeito D-12 alocado ao round 005. | §5, A1–A8 |
| **V4** | 2026-09-03 | **rejulgado — 10/10** | A peça retrabalhada venceu o rejulgamento e o placar fechou em dez de dez. | §5 |
| **V5** | 2026-09-03 | **entregue com evidência** | Bateria de 17 verificações com saída literal e denominador: **15 verdes, 2 vermelhas**, as duas diagnosticadas por causa raiz e nenhuma afrouxada. | §1–§4 |
| **V6** | 2026-09-03 | **pendência externa registrada** | O vermelho de conformidade é do método, não deste repositório: virou a mensagem externa `mensagens/002-para-maestro-pisos-absolutos-de-ciclo.md`, na rota que o P1 obriga (relatar e parar). | §4.1 |
| **V7** | 2026-09-04 | **fechado do lado do agente** | Este fecho: histórico de veredito, achados da revisão numerados com destino, ressalvas explícitas, dívida com dono, e a bateria re-executada (§1.1). | §0, §5, §9 |
| **V7b** | 2026-09-04 | **critério corrigido e provado** | A linha 11 da DoD media a **string do caminho** da base da irmã quando dizia medir vazamento. Foi reescrita para medir **conteúdo** (portão `scripts/check-vazamento.sh`), a troca ficou declarada na spec, e o critério novo foi provado por **quatro sabotagens** que plantam vazamento fictício e o veem reprovar. | §2 (linha 11), §4.2, §7 |
| **V8** | — | **aguardando gate humano** | `TAIL:gate` **não marcado**, de propósito: quem executou não aprova o que executou. | §8, `tasks.md` |

**Sobre as datas, com a honestidade que a regra R1 cobra.** V1 a V6 aconteceram todos em
2026-09-03 — o ciclo 001 foi construído num dia só. A prova disponível no disco é a data de
modificação do que cada estado deixou; ela **ordena arquivos**, e não prova quem os escreveu
nem em que ordem foram pensados. É o que há, e é dito como tal (artefatos de conteúdo do
ciclo, na ordem em que o disco os traz):

```text
$ for f in docs/produto/dados/analise-horizonte.json docs/product-site/data.json \
           docs/produto/dados/medir-base.py docs/produto/visao.md \
           mensagens/002-para-maestro-pisos-absolutos-de-ciclo.md; do \
      printf '%s  %s\n' "$(date -u -r "$f" +%Y-%m-%dT%H:%MZ)" "$f"; done
2026-09-03T17:00Z  docs/produto/dados/analise-horizonte.json
2026-09-03T17:08Z  docs/product-site/data.json
2026-09-03T17:33Z  docs/produto/dados/medir-base.py
2026-09-03T17:37Z  docs/produto/visao.md
2026-09-03T17:54Z  mensagens/002-para-maestro-pisos-absolutos-de-ciclo.md
```

A ordem lida assim: a base sintética (17:00) veio antes do medidor (17:33) e da visão
retrabalhada (17:37), e a mensagem externa (17:54) veio depois de tudo — que é a sequência
que os estados V3 a V6 descrevem. **Portões e suítes ficaram de fora desta lista de
propósito**: eles continuam sendo editados por lotes paralelos deste mesmo fechamento, e a
data de modificação deles falaria do lote, não do estado do ciclo.

**O que este histórico NÃO diz.** Não diz "aprovado". Aprovação é assinatura de humano, e
ela não existe — o estado V8 é o de hoje. O que os estados V1 a V7b registram é que o
trabalho de agente acabou: construir, ser reprovado, corrigir, ser rejulgado, medir e
declarar o que ficou. O passo seguinte é §8, e não é delegável.

## 1 · Bateria de portões (denominador colado)

| # | Portão | Comando | Código de saída | Denominador — quanto examinou (linha do próprio portão) |
|---|---|---|---|---|
| G1 | Agregador de evidência | `scripts/evidencia.sh` | **0** ✓ | `Portões executados: 6 · verdes: 6 · vermelhos: 0.` |
| G2 | Método instalado | `scripts/check-install.sh` | **0** ✓ | 7 camadas do método + 1 instrução de IA + 6 skills conferidas; `saída completa: 24 linhas` |
| G3 | Links relativos | `scripts/check-links.sh` | **0** ✓ | `checked: 337` |
| G4 | Caminhos entre crases (R4) | `scripts/check-caminhos.sh` | **0** ✓ | `arquivos varridos: 74` · `caminhos conferidos: 572 · isentos declarados: 135 · entregas futuras declaradas: 70 · moldes ignorados: 13` |
| G5 | Specs: artefatos, seções, cauda e régua DoR | `scripts/check-specs.sh` | **0** ✓ | `ciclos examinados: 12` · `artefatos 48 · seções e status 185 · tipos de requisito 71 · linhas de Constitution Check 204 · tokens ART 60 · tokens TAIL 48 · specs pontuadas 12 = 628` · `sinais medidos ao todo: 166` |
| G6 | Rounds: campos, dependências, defeitos | `scripts/check-rounds.sh` | **0** ✓ | `rounds examinados: 11` · `conferências de campo: 77` · `arestas de dependência: 15 · ciclos encontrados: 0` · `defeitos medidos: 12 · alocados a round: 10 · declarados sem round: 2` |
| G7 | ADRs: índice, registro, sucessão (R5) | `scripts/check-adrs-sucessao.sh` | **0** ✓ | `ADRs examinados: 8 · linhas de tabela no índice: 9 · linhas em docs/records/decisoes.jsonl: 8` · `verificações executadas: 32` |
| G8 | Suíte de sabotagem (mutação) | `scripts/tests/run-sabotagem.sh` | **0** ✓ | `portões cobertos: 5 · bases válidas aceitas: 5/5` · `sabotagens declaradas: 27 · reprovadas pelo motivo certo: 27/27` |
| G9 | Base sintética e critérios de UDE | `python3 docs/produto/dados/medir-base.py` | **0** ✓ | ARA `16 nós (12 UDEs, 4 causas) · 16 arestas`; NC `5 entidades · 7 arestas com premissa · 2 injeções`; 8 checagens decidíveis sobre 12 UDEs autorais **e** 9 enunciados de controle externos |
| G10 | Conformidade do ciclo | `scripts/check-conformance.sh 001` | **1** ✗ | `cycles checked: 1` — **vermelho estrutural, diagnóstico em §4.1** |
| G11 | Vazamento de dado real de pessoa (RNF-03 · ADR 0006) | `scripts/check-vazamento.sh` | **0** ✓ | `arquivos varridos: 194 · linhas varridas: 51022 · registros JSON inspecionados: 2557` · `campos de pessoa vigiados: 21 · chaves do esquema da irmã: 16 (limiar 4 no mesmo registro)` · `elenco fictício declarado: 4 · isenções de sabotagem declaradas: 3` |

### Saídas literais

```text
$ scripts/evidencia.sh
$ echo $?
0
```

*(o agregador imprime o relatório completo dos seis portões G2–G7; as linhas de
denominador citadas na tabela acima são recortes literais dessa saída.)*

```text
$ scripts/check-links.sh
── Relative links across the repository ──
  checked: 337
✓ every relative link resolves.
$ echo $?
0
```

```text
$ scripts/check-caminhos.sh
── Caminhos citados entre crases (regra R4) ──
  arquivos varridos: 74
  caminhos conferidos: 572  ·  isentos declarados: 135  ·  entregas futuras declaradas: 70  ·  moldes ignorados: 13

✓ todo caminho citado entre crases existe.
$ echo $?
0
```

```text
$ scripts/check-adrs-sucessao.sh
── ADRs: índice, registro e sucessão (regra R5) ──
  ADRs examinados: 8  ·  linhas de tabela no índice: 9  ·  linhas em docs/records/decisoes.jsonl: 8
  invariantes por ADR: 4 (índice · registro append-only · campo "Princípios tocados" · campo "Sucede")
  verificações executadas: 32  ·  sucessões declaradas: 0  ·  sucedidos declarados: 0  ·  linhas adr-* conferidas: 8

✓ todo ADR está no índice e no registro, declara os princípios que toca e o que sucede,
  e toda sucessão está declarada nos dois lados.
$ echo $?
0
```

```text
$ scripts/check-rounds.sh
── Rounds: campos, dependências e alocação de defeitos ──
  rounds examinados: 11 (002, 003, 004, 005, 006, 007, 008, 009, 010, 011, 012)
  campos obrigatórios por round: 7  ·  conferências de campo: 77
  arestas de dependência: 15  ·  ciclos encontrados: 0
  defeitos medidos em docs/produto/visao.md: 12  ·  alocados a round: 10  ·  declarados sem round: 2

✓ todo round declara os sete campos, as dependências não formam ciclo,
  e cada defeito medido tem exatamente um destino.
$ echo $?
0
```

```text
$ scripts/check-specs.sh
── Specs: artefatos, seções, taxonomia e cauda ──
  ciclos examinados: 12 (001, 002, 003, 004, 005, 006, 007, 008, 009, 010, 011, 012)
  verificações: artefatos 48 · seções e status 185 · tipos de requisito 71 · linhas de Constitution Check 204 · tokens ART 60 · tokens TAIL 48 · specs pontuadas 12  =  628
  isenções aplicadas: 1
    · ciclo 001: seções de módulo e requisito de interface (RI) — ciclo documental: sem interface, sem módulo de domínio e sem tela — o formato do brief §7 é o da spec de MÓDULO
...
  sinais medidos ao todo: 166 (14 por spec, menos os declarados não aplicáveis por isenção)

✓ todo ciclo tem os quatro artefatos, spec com as seções e os tipos de requisito,
  plano com as duas tabelas e os cinco artefatos declarados, tasks com a cauda,
  e toda spec pontua ≥ 80 na régua de prontidão do ADR 0004.
$ echo $?
0
```

A régua DoR do ADR 0004 §5 (corte ≥ 80) pontuou as doze specs, a mais baixa em 92,6:

```text
   ciclo │ Compl/30 │ Teste/25 │ Clar/20 │ Escopo/15 │ Limite/10 │  nota │
    001  │    30.0  │    25.0  │   17.9  │    15.0   │     7.0   │  94.9 │ ✓
    002  │    28.8  │    21.9  │   19.5  │    15.0   │     9.0   │  94.1 │ ✓
    003  │    30.0  │    24.8  │   19.6  │    15.0   │    10.0   │  99.4 │ ✓
    004  │    30.0  │    24.1  │   19.4  │    15.0   │    10.0   │  98.6 │ ✓
    005  │    30.0  │    24.8  │   18.5  │    15.0   │    10.0   │  98.3 │ ✓
    006  │    30.0  │    25.0  │   18.3  │    15.0   │    10.0   │  98.3 │ ✓
    007  │    30.0  │    24.5  │   19.0  │    15.0   │    10.0   │  98.6 │ ✓
    008  │    30.0  │    25.0  │   19.7  │    15.0   │    10.0   │  99.7 │ ✓
    009  │    30.0  │    23.9  │   19.1  │    15.0   │    10.0   │  98.0 │ ✓
    010  │    30.0  │    24.2  │   18.3  │    15.0   │    10.0   │  97.6 │ ✓
    011  │    30.0  │    21.4  │   19.7  │    15.0   │    10.0   │  96.1 │ ✓
    012  │    30.0  │    17.9  │   19.6  │    15.0   │    10.0   │  92.6 │ ✓
```

### 1.1 · Re-execução no fechamento (2026-09-04)

A tabela acima é da execução de **2026-09-03**. O repositório mudou depois dela — entrou a
mensagem externa `mensagens/002-para-maestro-pisos-absolutos-de-ciclo.md` (§4.1) e entrou
este próprio fechamento —, e portão cujo denominador depende do corpus **tem** de se mover
quando o corpus se move. Por isso a bateria foi rodada de novo, com o documento já fechado:

```text
$ scripts/check-links.sh
── Relative links across the repository ──
  checked: 338
✓ every relative link resolves.
$ echo $?
0

$ scripts/check-caminhos.sh
── Caminhos citados entre crases (regra R4) ──
  arquivos varridos: 75
  caminhos conferidos: 661  ·  isentos declarados: 138  ·  entregas futuras declaradas: 70  ·  moldes ignorados: 13

✓ todo caminho citado entre crases existe.
$ echo $?
0

$ scripts/evidencia.sh | sed -n '5p'
Portões executados: **6** · verdes: **6** · vermelhos: **0**.
$ scripts/evidencia.sh > /dev/null ; echo $?
0
```

**Por que os denominadores subiram, e por que isso é o comportamento certo.** Os dois
portões que varrem o repositório inteiro — `scripts/check-links.sh` e
`scripts/check-caminhos.sh` — contam também **este arquivo**, inclusive os caminhos citados
nas seções novas. Um denominador que não subisse depois de o corpus crescer seria o sintoma
da regra R2: verde sobre um universo menor do que o que existe. O que **não** mudou é o
veredito: seis portões, seis verdes, código de saída 0 nos seis.

**E estes números se moveram durante o próprio fechamento.** O lote paralelo que reescreveu
o critério 11 (achado A13, estado V7b) entregou arquivos novos — o portão de vazamento e as
suas quatro sabotagens —, e cada arquivo novo entra nos dois denominadores acima. O número
colado aqui é o da última execução de 2026-09-04, com os dois lotes já no disco; quem for ao
gate humano roda a bateria outra vez e compara **o veredito**, que é o que tem de ser
estável — não o denominador, que tem de crescer com o corpus.

## 2 · Funções de aptidão da spec (DoD, 13 linhas)

| # | Verificação | Comando | Esperado | Observado (saída literal) | Código |
|---|---|---|---|---|---|
| 1 | Constituição com 7 princípios | `grep -c '^### P[1-7]\.' docs/governance/constitution.md` | `7` | `7` | 0 ✓ |
| 2 | Bloco do instalador preservado | `grep -c '^## Method: Maestro' CLAUDE.md` | `1` | `1` | 0 ✓ |
| 3 | Oito ADRs | `ls docs/adr/000[1-8]-*.md \| wc -l` | `8` | `8` | 0 ✓ |
| 4 | Sucessão e índices de ADR | `scripts/check-adrs-sucessao.sh` | 0 + denominador | G7: 8 ADRs, 32 verificações | 0 ✓ |
| 5 | 12 pastas × 4 arquivos | `ls -d specs/0*/ \| wc -l` e `ls specs/0*/{spec,plan,tasks,qa-report}.md \| wc -l` | `12` e `48` | `12` e `48` | 0 ✓ |
| 6 | Roadmap com 12 ciclos | `grep -c '^\| \*\*0[0-9][0-9]\*\*' docs/roadmap.md` | `12` | `12` | 0 ✓ |
| 7 | Régua DoR das specs | `scripts/check-specs.sh` | 0 + denominador | G5: 12 ciclos, 628 verificações, menor nota 92,6 | 0 ✓ |
| 8 | Caminhos entre crases | `scripts/check-caminhos.sh` | 0 + denominador | G4: 74 arquivos, 572 caminhos | 0 ✓ |
| 9 | Links relativos | `scripts/check-links.sh` | 0 + denominador | G3: `checked: 337` | 0 ✓ |
| 10 | Site gerado por script | `test -f docs/product-site/index.html && test -f tools/product-site/generate.py` | código 0 | *(sem saída; código 0)* | 0 ✓ |
| 11 | Sem vazamento de **dado real de pessoa** da base da irmã | `scripts/check-vazamento.sh` | código 0 + denominador | G11: 194 arquivos, 51 022 linhas, 2 557 registros JSON; **0 achados** — critério **reescrito** neste fechamento, ver §4.2 | 0 ✓ |
| 12 | Método instalado e coerente | `scripts/check-install.sh` | código 0 | G2: 7 camadas, 6 skills | 0 ✓ |
| 13 | Conformidade do ciclo | `scripts/check-conformance.sh 001` | código 0 | `cycles checked: 1` + 2 falhas de piso | **✗ ver §4.1** |

Saídas literais das linhas 1, 2, 3, 5, 6, 10 e 11, na ordem:

```text
$ grep -c '^### P[1-7]\.' docs/governance/constitution.md
7
$ grep -c '^## Method: Maestro' CLAUDE.md
1
$ ls docs/adr/000[1-8]-*.md | wc -l
8
$ ls -d specs/0*/ | wc -l
12
$ ls specs/0*/spec.md specs/0*/plan.md specs/0*/tasks.md specs/0*/qa-report.md | wc -l
48
$ grep -c '^| \*\*0[0-9][0-9]\*\*' docs/roadmap.md
12
$ test -f docs/product-site/index.html && test -f tools/product-site/generate.py
$ echo $?
0
```text
$ scripts/check-vazamento.sh
── Vazamento de dado real de pessoa (RNF-03 · ADR 0006) ──
  arquivos varridos: 194  ·  linhas varridas: 51022  ·  registros JSON inspecionados: 2557
  sinais aplicados: 3 (V1 nome próprio em campo de pessoa · V2 registro no formato da base da irmã · V3 base real lida por código)
  campos de pessoa vigiados: 21  ·  chaves do esquema da irmã: 16 (limiar 4 no mesmo registro)
  elenco fictício declarado: 4  ·  isenções de sabotagem declaradas: 3

✓ nenhum nome próprio em campo de pessoa, nenhum registro no formato da base real
  da irmã e nenhum código lendo essa base.
$ echo $?
0
```
```

*(a linha 11 é a única da tabela cujo **comando mudou** durante o fechamento. O comando
antigo — `grep -rn "gestaodeprioridades/protot[i]po" --include='*.md' . | wc -l` — media a
string do caminho e devolvia `2`, contando a denúncia junto com o denunciado; o novo mede
conteúdo vazado e devolve `0` sobre 194 arquivos. A troca está declarada em §4.2 e na
própria spec, e é o oposto de afrouxar: o critério novo pega três classes de vazamento que
o antigo não pegava, e há quatro sabotagens provando que ele reprova.)*

## 3 · Cobertura de requisitos

| Requisito | Coberto por | Estado |
|---|---|---|
| RF-01 — identidade no `CLAUDE.md` antes do bloco instalado | DoD 2 (`1`) + G2 (`checked: CLAUDE.md`) | ✓ |
| RF-02 — constituição v1.0.0 com sete princípios | DoD 1 (`7`) | ✓ |
| RF-03 — convenção `mensagens/README.md` | G4 (`mensagens/README.md` entre os 74 arquivos varridos, 572 caminhos resolvidos) | ✓ |
| RF-04 — licença MIT e avisos de terceiros | G4 (`LICENSE` e `THIRD-PARTY-NOTICES.md` citados e resolvidos) | ✓ |
| RF-05 — ADRs 0001–0008 | DoD 3 (`8`) + G7 (`ADRs examinados: 8`) | ✓ |
| RF-06 — ADR aceito no índice e no `decisoes.jsonl` | G7 (`linhas de tabela no índice: 9 · linhas em docs/records/decisoes.jsonl: 8`, 32 verificações) | ✓ |
| RF-07 — visão do produto medida | G6 (`defeitos medidos em docs/produto/visao.md: 12`) + G9 (a base e o controle da §6) | ✓ |
| RF-08 — módulos M1–M8 | G4 e G3 sobre `docs/produto/modulos.md` | ✓ |
| RF-09 — roadmap 001–012 | DoD 6 (`12`) | ✓ |
| RF-10 — doze pastas com quatro artefatos | DoD 5 (`12` e `48`) + G5 (`artefatos 48`) | ✓ |
| RF-11 — portões executáveis e **não lenientes** | G8 (`bases válidas aceitas: 5/5` · `sabotagens reprovadas pelo motivo certo: 27/27`) + G11 (o portão novo da linha 11 nasceu com 4 sabotagens) | ✓ |
| RF-12 — site gerado só pelo gerador vendorizado | DoD 10 (código 0) | ✓ |
| RNF-01 — português no projeto, inglês na superfície instalável | Revisão do gauntlet (§5); sem portão executável — **dívida declarada** | 🟡 |
| RNF-02 — sigla por extenso na primeira ocorrência | G5 (`siglas 12/17 do catálogo abertas` na spec 001, depois de a spec abrir **JSON** ao declarar a mudança do critério 11; medido spec a spec) + revisão | ✓ |
| RNF-03 — nenhum dado real de pessoa | G11 / DoD 11 (`scripts/check-vazamento.sh`: 194 arquivos, 0 achados nos três sinais) + TAIL:security (§6): 189 arquivos varridos, 0 segredos, 0 imagens, base `sintetica: True` | ✓ |
| RNF-04 — todo caminho relativo resolve | G3 (`337`) + G4 (`572`) | ✓ |
| RNF-05 — todo número afirmado foi executado | Este relatório inteiro; G1 (`Portões executados: 6 · verdes: 6`) | ✓ |

## 4 · Os dois portões vermelhos (diagnóstico antes de correção)

Nenhum dos dois foi corrigido afrouxando o portão. O da §4.1 continua vermelho e é
**externo** — piso do método, não deste repositório. O da §4.2 **foi corrigido durante este
fechamento**, e corrigido pela ponta certa: o critério, que media caminho citado quando
dizia medir vazamento, foi reescrito para medir conteúdo, com a troca declarada na spec e
provada por sabotagem. A §4.2 abaixo mantém o diagnóstico inteiro e acrescenta a correção
no fim — apagar o diagnóstico deixaria o documento dizendo "sempre esteve verde", que é o
contrário do que aconteceu.

### 4.1 · `check-conformance.sh 001` sai 1 — piso do método calibrado para outro repositório

**Sintoma.** Saída literal:

```text
$ scripts/check-conformance.sh 001
── Conformance: did the method survive into the artifacts? ──
   (floor: cycle 42; older cycles carry declared debt — see the roadmap)
• 001-fundacao-e-planejamento
    ✓ Constitution Check complete (8/8)
    · acceptance-criteria checkboxes: not checked below cycle 45
    ✓ all 5 conditional artifacts declared with a reason
──
cycles checked: 1
✗ mutation floor 55 is above the newest cycle 012 — TAIL:mutation was charged to nobody.
✗ declared-absence floor 61 is above the newest cycle 012 — 'pendente' would pass as evidence everywhere.
✗ the method did not survive into the artifacts of at least one cycle.
$ echo $?
1
```

**Causa raiz — não é este repositório.** O script é a **superfície instalável do método**
e seus pisos são **números absolutos de ciclo da história do repositório canônico**
`GHDaru/maestro`, não números relativos:

- `scripts/check-conformance.sh:52` — `FLOOR="${MAESTRO_MIN_CYCLE_CONFORMANCE:-42}"`
- `scripts/check-conformance.sh:54` — `CRIT_FLOOR="${MAESTRO_MIN_CYCLE_CRITERIA:-45}"`
- `scripts/check-conformance.sh:77` — `ABSENCE_FLOOR="${MAESTRO_MIN_CYCLE_ABSENCE:-61}"`
- `scripts/check-conformance.sh:91` — `MUT_FLOOR="${MAESTRO_MIN_CYCLE_MUTATION:-55}"`

Os dois blocos de sanidade do fecho (`scripts/check-conformance.sh:468-475`) reprovam
quando o piso está **acima do ciclo mais novo do disco**. Num repositório recém-instalado
que começa no ciclo 001, `NEWEST_CYCLE` vale `012` por construção — logo `55 > 12` e
`61 > 12` são **verdadeiros para sempre**, e o script não pode sair 0 por nada que este
repositório escreva. O `--ticked-only` confirma o mesmo pela outra ponta:

```text
$ scripts/check-conformance.sh --ticked-only
── Conformance: did the method survive into the artifacts? ──
   (floor: cycle 42; older cycles carry declared debt — see the roadmap)
──
✗ no cycle in range (floor 42) — the gate checked nothing.
$ echo $?
1
```

**Não é escopo deste ciclo consertar.** O arquivo é do método; `GHDaru/maestro` é
**leitura** pelo princípio P1. Editá-lo aqui bifurcaria o método instalado — que é
exatamente o que o `check-install.sh` existe para impedir. **Relatar e parar**: o achado fica
como **pendência declarada**, e a rota do P1 é uma mensagem externa ao método em
`mensagens/`, redigida na convenção de `mensagens/README.md`, com as quatro linhas de
piso acima como evidência.

**A mensagem existe — e é isto que mudou desde a primeira redação deste parágrafo.** Quando
este relatório nasceu, ela não existia, e o parágrafo dizia isso: citar como pronto um
arquivo que não está no disco é exatamente o defeito que a regra R4 existe para pegar, e ele
foi pego aqui mesmo. Hoje o arquivo está no disco, com destino, commit lido e estado:

```text
$ ls -1 mensagens/
001-para-daruskills-defeitos-do-gerador-de-site.md
002-para-maestro-pisos-absolutos-de-ciclo.md
README.md
$ grep -n '^- \*\*Destino\*\*\|^- \*\*Commit lido\*\*\|^- \*\*Data\*\*' \
    mensagens/002-para-maestro-pisos-absolutos-de-ciclo.md
9:- **Destino**: `GHDaru/maestro`, arquivo `scripts/check-conformance.sh`
10:- **Commit lido**: `534a088e62bcd2deb50353d5a6c60606a37e4e5f` (2026-08-23) — clone lido em `/home/user/maestro`, somente leitura
14:- **Data**: 2026-09-03 · **Estado**: **aberta**
```

**O que continua aberto não é escrever a mensagem: é entregá-la.** Levá-la a
`GHDaru/maestro` é escrita fora da fronteira do P1 e exige aprovação humana explícita, caso a
caso — está em §8, item 4, e é por isso que o estado do arquivo é `aberta` e não `entregue`.

**O veredito substantivo existe e foi obtido apertando os pisos, nunca afrouxando.** Os
knobs do próprio script só admitem **apertar** (`check-conformance.sh:86-88`: um
`ABSENCE_FLOOR` acima do padrão é recusado). Baixá-los para 1 cobra do ciclo 001 as
regras que o padrão dispensaria — é a leitura **mais severa** possível:

```text
$ MAESTRO_MIN_CYCLE_CONFORMANCE=1 MAESTRO_MIN_CYCLE_CRITERIA=1 \
  MAESTRO_MIN_CYCLE_MUTATION=1 MAESTRO_MIN_CYCLE_ABSENCE=1 \
  scripts/check-conformance.sh 001
── Conformance: did the method survive into the artifacts? ──
   (floor: cycle 1; older cycles carry declared debt — see the roadmap)
• 001-fundacao-e-planejamento
    ✓ Constitution Check complete (8/8)
    ✓ acceptance criteria located and stated without checkboxes
    ✓ all 5 conditional artifacts declared with a reason
    ✗ TAIL:review in qa-report.md is still the placeholder — nobody wrote what happened
    ✗ TAIL:security in qa-report.md is still the placeholder — nobody wrote what happened
    ✗ TAIL:gate in qa-report.md is still the placeholder — nobody wrote what happened
    ✗ TAIL:mutation in qa-report.md is still the placeholder — nobody wrote what happened
──
cycles checked: 1
✗ the method did not survive into the artifacts of at least one cycle.
$ echo $?
1
```

Aquela execução foi feita **com este relatório ainda vazio**, e as quatro reprovações
eram precisamente o trabalho que este documento faz. Com as caudas escritas, a **mesma
leitura severa** passa:

```text
$ MAESTRO_MIN_CYCLE_CONFORMANCE=1 MAESTRO_MIN_CYCLE_CRITERIA=1 \
  MAESTRO_MIN_CYCLE_MUTATION=1 MAESTRO_MIN_CYCLE_ABSENCE=1 \
  scripts/check-conformance.sh 001
── Conformance: did the method survive into the artifacts? ──
   (floor: cycle 1; older cycles carry declared debt — see the roadmap)
• 001-fundacao-e-planejamento
    ✓ Constitution Check complete (8/8)
    ✓ acceptance criteria located and stated without checkboxes
    ✓ all 5 conditional artifacts declared with a reason
    ✓ TAIL:review evidence: a revisão independente foi o **gauntlet de crítica às c
    ✓ TAIL:security evidence: passe proporcional à classe de risco (corpus documental, 
    ✓ TAIL:gate evidence: NÃO marcado.** A DoD fechou **17 de 18 verificações ver
    ✓ TAIL:mutation evidence: `scripts/tests/run-sabotagem.sh` saiu **0** provando as du
──
cycles checked: 1
✓ every cycle checked declares its artifacts and carries the closing tail with evidence.
$ echo $?
0
```

**Leia-se com precisão o que isso quer dizer.** A conformidade **de conteúdo** do ciclo 001
está verde sob a régua mais severa que o script admite — Constitution Check completo 8/8,
critérios de aceite sem caixa, cinco artefatos condicionais declarados com motivo, e as
quatro caudas com evidência. O que continua vermelho é **só a régua estrutural do piso**
(`55 > 12` e `61 > 12`), que não fala do ciclo 001: fala de o método ter sido instalado num
repositório cuja numeração de ciclos começa do zero. Essa é a mensagem externa, não um
defeito local — e é por isso que a linha 13 da DoD permanece marcada **✗** nesta tabela em
vez de ser silenciosamente reescrita para a variante que passa.

### 4.2 · DoD linha 11 não zera — a única ocorrência no corpus é legítima

**Sintoma.** O critério espera `0`. A ocorrência que ele encontra no corpus é uma só, e
esta é a linha, colada:

```text
./docs/adr/0006-base-sintetica-desde-o-dia-1.md:22:d = json.load(open('/home/user/gestaodeprioridades/prototipo/dados/fixture.json'))
```

**O número cru do critério é instável, e a instabilidade é o segundo rosto do mesmo
defeito.** Como o critério casa a **string do caminho** e não conteúdo vazado, ele conta o
relatório do achado junto com o achado: cada vez que este documento cita a linha acima, a
contagem sobe. Por isso a medida que significa alguma coisa é a que exclui este próprio
relatório — e as duas estão coladas aqui, com os comandos:

```text
$ grep -rn "gestaodeprioridades/protot[i]po" --include='*.md' . | wc -l
2
$ grep -rln "gestaodeprioridades/protot[i]po" --include='*.md' . \
    | grep -v 'specs/001-fundacao-e-planejamento/qa-report.md' | wc -l
1
```

A segunda linha é a resposta à pergunta que o critério **queria** fazer: fora deste
relatório, **um** arquivo em todo o repositório cita a base da irmã — o ADR 0006. Nenhum
outro.

**Causa raiz.** A ocorrência é **um caminho dentro do bloco de evidência do próprio ADR
0006** — o comando que mediu a base da irmã para justificar a decisão "base sintética
desde o dia 1". O que ele imprime são **contagens** (`tarefas: 114`,
`valores distintos em responsavel: 6`), nunca conteúdo: nenhum enunciado de trabalho,
nenhum nome de pessoa, nenhuma data de desempenho atravessou. O ADR diz isso na linha
acima do bloco: *"contagens apenas — nenhum dado copiado, e é este ADR que explica por
quê"*. O critério, como está escrito na spec (`spec.md:149`), casa a **string do
caminho**; a intenção declarada dele é *"nenhum vazamento da base real da irmã"*. O
critério é mais estrito do que a sua própria intenção, e a única coisa que ele pegou é
a evidência que fundamenta a regra da privacidade.

**O que estava errado era o critério, e é o critério que mudou.** Duas rotas estavam
fechadas antes de começar. Editar o corpo do ADR 0006 é proibido — o método guarda ADR
committado como histórico e um guarda `PreToolUse` recusa a reescrita; a rota, se fosse o
caso, seria um ADR novo que sucedesse. E **baixar o número esperado, ou isentar o arquivo
que incomoda, é afrouxar** — o anti-padrão que este relatório existe para não cometer.
Sobrou a rota certa, que é também a mais trabalhosa: reescrever o critério para medir o que
ele **diz** medir.

**A correção, em quatro peças executadas.**

1. **O critério novo está na spec, e a troca está declarada lá** — `spec.md`, seção
   "Mudança declarada no critério 11", com o critério antigo, por que estava errado (falso
   positivo sobre a evidência **e** instabilidade) e o critério novo. Trocar critério de
   aceite em silêncio seria marcar caixa sem testemunha.
2. **O portão é `scripts/check-vazamento.sh`**, e ele procura vazamento nos termos do ADR
   0006 — *"nome, enunciado de trabalho, data de desempenho"* — em três sinais: **V1** nome
   próprio de pessoa num campo de pessoa (inclusive coluna de tabela e registro JSON
   impresso em várias linhas); **V2** registro no formato da base real da irmã (quatro ou
   mais campos do esquema dela no mesmo registro, que é como enunciado e data viajam sem
   nome); **V3** base real dela lida por código que **não** é `*.md`. Nenhum dos três casa
   um caminho citado dentro de um bloco de documentação — por isso o bloco de evidência do
   ADR 0006 continua onde está, intocado, e o portão sai `0`.
3. **É estável, e isto foi medido, não afirmado**: o portão foi executado duas vezes
   seguidas sobre o repositório e devolveu o mesmo veredito, e este parágrafo — que cita o
   caminho da base da irmã de novo — não move o número. O denominador (linhas varridas)
   cresce quando o corpus cresce, que é o comportamento que a regra R2 pede.
4. **Ele reprova** — a metade que transforma verde em evidência. `scripts/tests/sabotagem/vazamento/`
   é uma base válida que guarda **de propósito** um ADR com bloco de evidência citando o
   caminho da base real (o controle de regressão do critério antigo), e
   `scripts/tests/run-sabotagem.sh` planta nela **quatro vazamentos de verdade** — nome
   fictício em campo de pessoa, nome fictício em coluna de responsável, registro no esquema
   da irmã, e leitura da base real em `*.py` — exigindo que o portão reprove **pelo motivo
   declarado** em cada um. Os nomes plantados são inventados e a não-colisão com a base real
   foi executada antes (comparação de conjuntos imprimindo só booleanos). Saída em §7.

**O que continua sendo do Product Steward.** A execução está feita e provada; o que não é
delegável é a **ratificação** do critério trocado — §8, item 4. E o que o critério queria
proteger segue verificado pelo outro caminho também: §6, TAIL:security.

## Cauda de fechamento — a evidência, uma linha por passo

<!-- Uma entrada por token TAIL não-n/a. O que foi OBSERVADO, nunca a intenção repetida.
     O detalhe de cada linha está na seção de mesmo nome, logo abaixo. -->

- TAIL:review — a revisão independente foi o **gauntlet de crítica às cegas**: 10 peças do
  corpus julgadas por críticos em contexto fresco contra dois corpora externos (o da irmã
  `gestaodeprioridades` e o do PROJETO_ECS), placar **9 vitórias e 1 derrota** na primeira
  rodada; a peça derrotada foi `docs/produto/visao.md`, por circularidade da base autoral
  das checagens de Efeito Indesejável (UDE), foi retrabalhada dirigida por essa lacuna e
  venceu o rejulgamento — **10/10**. **Oito achados foram corrigidos** (A1–A8, cada um com a
  prova re-executada no fecho) e **sete continuam abertos** (A9–A15, dois deles encontrados
  no próprio fechamento e marcados como tal). O retrabalho é verificável: conjunto de
  controle de 9 enunciados externos que achou um **falso negativo real** (K-03), lacuna L-03
  declarada em `docs/produto/visao.md:521` e o defeito D-12 alocado ao round 005. Detalhe: §5.
- TAIL:security — passe proporcional à classe de risco (corpus documental, zero linha de
  código de produção) sobre **189 arquivos**, o repositório inteiro fora de `.git`:
  **0 segredos e 0 credenciais** em duas varreduras (atribuição de chave/senha/token e os
  formatos `AKIA…`, `sk-…`, `ghp_…`, `AIza…`, `postgres://user:senha@`), **0 capturas de
  tela**, e a base do projeto declarando-se sintética na origem (`sintetica: True`, três
  personas que são papéis fictícios). Um achado de **forma**, nenhum de conteúdo: a única
  citação da base da irmã é o caminho no bloco de evidência do ADR 0006, num comando que
  imprime só contagens. Detalhe: §6.
- TAIL:mutation — `scripts/tests/run-sabotagem.sh` saiu **0** provando as duas metades:
  os 5 portões deste projeto **aceitam** a base válida (`bases válidas aceitas: 5/5`) e
  **reprovam pelo motivo declarado** as 27 mutações (`sabotagens declaradas: 27 ·
  reprovadas pelo motivo certo: 27/27`), cada uma sobre uma cópia em `/tmp`, sem tocar o
  repositório. As quatro últimas são as do `check-vazamento.sh`, o portão que substituiu a
  linha 11 da DoD: sem elas, o verde do critério reescrito seria só uma afirmação. Limite declarado: os portões vindos do método são sabotados no método, não
  aqui (P1). Detalhe: §7.
- TAIL:gate — **NÃO marcado.** A DoD fechou **17 de 18 verificações verdes**, com a única
  vermelha (§4.1, externa ao repositório) diagnosticada por causa raiz e **nenhuma
  afrouxada** — a segunda vermelha virou verde por **reescrita declarada do critério**, não
  por afrouxamento (§4.2) —, e as três caudas
  acima escritas com a saída colada; a caixa correspondente em `tasks.md` fica **em branco
  de propósito**, porque quem executou não aprova o que executou. Aguardam a assinatura do
  Product Steward **sete itens**, tabelados em §8: ratificar a constituição e os 8 ADRs;
  responder as cinco perguntas da visão §7 e os três `[DÚVIDA]` do Clarify; decidir o
  achado A13 — agora **ratificar** o critério 11 reescrito, já executado e provado;
  autorizar a entrega da mensagem 002 ao método (A12);
  aceitar ou recusar as três ressalvas do §9; e autorizar a promoção `dev` → `main`.
  Detalhe: §8; a dívida que sobra, com dono, em §9.

## 5 · TAIL:review — a revisão independente foi o gauntlet

**Como funcionou.** A revisão independente deste ciclo não foi uma leitura de cortesia:
foi um **gauntlet de crítica às cegas**. O corpus do ciclo 001 foi cortado em **10 peças
julgáveis por si sós**; para cada peça, um construtor produziu e um **crítico separado, em
contexto fresco**, comparou o resultado **às cegas** contra a barra — sem saber qual lado
era o nosso. A barra tem dois corpora, ambos lidos, nenhum escrito por nós:

- o corpus da aplicação irmã **`GHDaru/gestaodeprioridades`** (constituição, regras R1–R5,
  specs, ADRs 0012 e 0016) — a régua de rigor de governança;
- o **PROJETO_ECS** (`specs/001-catalogo-itens` e `docs/product-site/`) — a régua de
  profundidade de requisito e de apresentação.

**Resultado: 10/10, com uma derrota real no caminho.** Na primeira rodada o placar foi
**9 vitórias e 1 derrota**. A peça derrotada foi a **visão de produto**
(`docs/produto/visao.md`), pelo achado **A4** abaixo. Ela foi **retrabalhada dirigida por
essa lacuna nomeada** e **venceu o rejulgamento**, fechando **10/10**.

### 5.1 · Os oito achados corrigidos — numerados, com destino e com a prova executada agora

| # | O que o crítico apontou | Peça | Destino |
|---|---|---|---|
| **A1** | Um bloco de console media um clone temporário que não está no repositório: o número era verdadeiro e **irreproduzível** por quem lesse depois. | ADR 0004 | **corrigido** — a origem do caminho passou a ser declarada, e o portão de caminhos carrega a isenção com motivo |
| **A2** | O selo 🔴 LACUNA foi declarado na taxonomia e **não aparecia em documento nenhum**. Selo que ninguém usa é decoração, e decoração num sistema de confiança é pior que ausência. | ADR 0004 / visão | **corrigido** — três lacunas declaradas em aberto, L-01 a L-03 |
| **A3** | A visão media a **linhagem** (os defeitos das quatro gerações do TOC-Builder) e não o **domínio**: nada no corpus dizia se as regras da Teoria das Restrições (TOC) eram decidíveis por função pura. | visão | **corrigido** — a base sintética e o medidor nasceram para responder isso |
| **A4** | **A derrota.** A base da "Instituição Horizonte" foi escrita pelo mesmo autor das checagens de UDE e *para* trazer as patologias que elas procuram — logo "3 de 12 passam" media o acordo do autor consigo mesmo, e "divergências: 0" era tautologia, não evidência. | visão | **corrigido** — conjunto de controle externo, que achou um falso negativo real |
| **A5** | A matriz de rastreabilidade do site descartava as regras de negócio e as integrações — **132 itens** — e as **58 lacunas** declaradas. | site de produto | **corrigido** — as cinco classes e as lacunas entraram na matriz |
| **A6** | O ADR 0004 §5 prometia a régua de prontidão de especificação (DoR) com "verificação executável por `scripts/check-specs.sh`" enquanto o portão **não existia**: promessa em documento de decisão é dívida sem dono. | ADR 0004 | **corrigido** — o portão nasceu no mesmo ciclo e pontua as doze specs |
| **A7** | O portão de caminhos estava **sem bit de execução**: a linha da definição de pronto (DoD) que manda rodá-lo não rodaria. | portões | **corrigido** |
| **A8** | Dez das doze specs não diziam o que fica **fora** de escopo — a metade do escopo que evita o ciclo inchar em execução. | specs | **corrigido**, com ressalva registrada em **A14** |

**A prova de cada correção, executada em 2026-09-04 neste repositório.** Regra R1: cada
bloco abaixo é a saída literal do comando escrito na linha acima dela, não a descrição do
que ela diria.

**A1 — o bloco de console agora declara que o clone é de fora, e o portão carrega a isenção
com motivo escrito.**

```text
$ sed -n '29,33p' docs/adr/0004-taxonomia-de-planejamento-e-absorcao-da-reversa.md

**A metodologia reversa** (`sandeco/reversa`, clone lido em modo leitura — nas medições
abaixo, `scratchpad/reversa` abrevia o caminho do clone temporário da sessão de
construção; o clone não faz parte deste repositório). Medida, não estimada:

$ ls scratchpad ; echo "exit=$?"
ls: cannot access 'scratchpad': No such file or directory
exit=2
$ grep -n "reversa/" scripts/check-caminhos.sh
67:    ("reversa/",           "clone de sandeco/reversa lido no ciclo 001, fora do repositório (ADR 0004)"),
```

O diretório continua não existindo — e é esse o ponto. O que mudou é que a medição **diz
que ele é de fora**, e a isenção do portão diz **por quê**, em vez de o número parecer
reproduzível e não ser. Isenção sem motivo escrito é tapete, e é a lição que o próprio
cabeçalho do `scripts/check-caminhos.sh` cobra.

**A2 — o selo 🔴 deixou de ser decoração.**

```text
$ grep -c "🔴" docs/produto/visao.md
8
$ grep -o "🔴 \*\*L-0[0-9]\*\*" docs/produto/visao.md | sort -u
🔴 **L-01**
🔴 **L-02**
🔴 **L-03**
$ sed -n '511p' docs/produto/visao.md
O selo 🔴 deste documento não é decorativo: as três lacunas abaixo são o que **não se sabe**
```

**A3 — a visão passou a medir o domínio, não só a linhagem.** O corpus ganhou uma base
sintética e um medidor que decide, item a item, quais características de UDE são função
pura e quais exigem julgamento:

```text
$ python3 docs/produto/dados/medir-base.py | sed -n '1,10p'
── Base sintética · Instituição Horizonte · versão 1.0.0 ──
  arquivo: analise-horizonte.json  ·  sintética: True  ·  personas: 3
  ARA: 16 nós (12 UDEs, 4 causas) · 16 arestas causais
  Nuvem de Conflito: 5 entidades · 7 arestas com premissa · 2 injeções
  validação estrutural: 0 falha(s)

── Critérios formais de UDE (tocbuilderv3/constants.ts:122-133) ──
  características do prompt: 11  ·  decidíveis por função pura: 8 checagens cobrindo 7  ·  dependentes de julgamento: 4

  U-01  PASSA   O intervalo médio da matrícula até a primeira aula é de 43 dias.
```

É o mesmo movimento que o P3 exige: regra de TOC como **regra de domínio pura**, testável
sem rede e sem modelo de linguagem. O que sobrou fora do alcance de função pura está
contado — **4 das 11** —, não escondido.

**A4 — a circularidade foi atacada com um conjunto que não foi escrito para as checagens, e
ele achou um defeito real.**

```text
$ python3 docs/produto/dados/medir-base.py | grep -E "NÚMERO AUTORAL|NÚMERO DE CONTROLE|FALSO|sem veredito"
  NÚMERO AUTORAL — UDEs medidos: 12  ·  passam nos 8 critérios decidíveis: 3 (U-01, U-02, U-03)  ·  reprovam: 9
  NÚMERO DE CONTROLE — enunciados: 9  ·  passam (texto normalizado): 8  ·  passam (texto literal, como citado): 6
  FALSO POSITIVO (a fonte diz bom, a checagem reprova): 0 (—)
  FALSO NEGATIVO (a fonte diz ruim, a checagem aprova): 1 (K-03)
  sem veredito possível (a fonte não rotula bom/ruim): 3 (K-02, K-08, K-09)
```

**O falso negativo é o que prova que o conserto não foi cosmético.** K-03 —
*"Falta de treinamento causa erros."* — é rotulado **pela própria fonte** como exemplo ruim
(UDE misturado com causa), e as oito checagens o **aprovam**. Um conjunto de controle que
só confirmasse o autor não teria achado nada; este achou. O retrabalho deixou três marcas
verificáveis, e as três estão no disco: o conjunto de controle acima, a lacuna **L-03**
declarada em aberto em `docs/produto/visao.md:521` — dizendo por que o defeito **não fecha
neste projeto**, já que corpus de oficina real é dado de pessoa real e o ADR 0006 o proíbe —
e o defeito **D-12** alocado ao round 005 em `docs/produto/rounds.md`, virando critério de
aceite do épico E2.1.

**A5 — a matriz de rastreabilidade parou de descartar as regras de negócio (RN), as
integrações (INT) e as lacunas.**

```text
$ python3 -c "
import json; m=json.load(open('docs/product-site/data.json'))['traceability']['modules']
n=lambda k: sum(len(x[k]) for x in m)
print('RF %d · RI %d · RNF %d · RN %d · INT %d · L %d' % (n('rfs'),n('ris'),n('rnfs'),n('rns'),n('ints'),n('lacunas')))
print('itens rastreados: %d · dos quais RN+INT: %d' % (n('rfs')+n('ris')+n('rnfs')+n('rns')+n('ints'), n('rns')+n('ints')))
"
RF 359 · RI 114 · RNF 105 · RN 71 · INT 61 · L 58
itens rastreados: 710 · dos quais RN+INT: 132
$ grep -o "RN-[0-9]*\|INT-[0-9]*\|L-[0-9]*" docs/product-site/traceability.html \
    | sed "s/-[0-9]*//" | sort | uniq -c
    108 INT
     95 L
    172 RN
```

Os **132** do achado são exatamente `RN 71 + INT 61`, e as **58** são as lacunas — as três
classes que a versão reprovada deixava de fora e que a página renderizada hoje carrega.
Siglas, por extenso: **RF** requisito funcional · **RI** requisito de interface · **RNF**
requisito não funcional · **RN** regra de negócio · **INT** integração · **L** lacuna
declarada.

**A6 — a promessa do ADR 0004 §5 tem portão, e o portão pontua as doze specs.**

```text
$ grep -n "check-specs.sh" docs/adr/0004-taxonomia-de-planejamento-e-absorcao-da-reversa.md
74:   Verificação executável por `scripts/check-specs.sh` 🟡 PLANEJADO (nasce neste ciclo).
106:  (`check-specs.sh` 🟡) — entre a escrita e o portão, o número da rubrica é opinião, e a
```

O selo 🟡 e a consequência negativa escrita no próprio ADR (*"a régua ≥ 80 é auto-atribuída
por agente até o portão executável existir"*) eram a promessa. O portão nasceu no mesmo
ciclo e é o G5 da §1: `ciclos examinados: 12`, `specs pontuadas 12`, menor nota **92,6**.

**A7 — o bit de execução.**

```text
$ find scripts -name "*.sh" ! -perm -u+x -print | wc -l
0
$ test -x scripts/check-caminhos.sh ; echo "exit=$?"
exit=0
```

Nenhum arquivo `.sh` de `scripts/` está sem bit de execução, e o portão de caminhos — o que
o achado nomeou — roda. É o tipo de defeito que nenhuma leitura pega e uma execução
pega na primeira tentativa: a razão de a revisão independente rodar, e não só ler.

**A8 — as doze specs dizem o que fica fora.**

```text
$ for f in specs/0*/spec.md; do grep -c '^#\{2,3\} .*Fora de escopo' "$f"; done \
    | sort | uniq -c
     12 1
```

Doze arquivos, cada um com exatamente uma seção "Fora de escopo". O `scripts/check-specs.sh`
mede o conteúdo dela spec a spec e imprime o denominador (`fora de escopo N linha(s)` por
ciclo, na saída do G5). **Com uma ressalva medida, que é o achado A14 abaixo**: essa
verificação **pontua**, não bloqueia.

**O que estas provas não são.** Elas mostram o **estado corrigido**, medido agora. Nenhuma
delas re-mede o estado **anterior** à correção — o "dez das doze specs", o "132 descartados"
e o placar 9 × 1 vêm do registro do gauntlet conduzido durante o ciclo, e quem escreve este
fecho **não os presenciou**. Onde o número anterior pôde ser reconstruído a partir do que
está no disco, ele está: os 132 do A5 são a soma exata das duas classes que hoje aparecem
na matriz. Onde não pôde, está dito aqui em vez de ser apresentado como medição.

### 5.2 · Os achados que continuam abertos

| # | Achado | Onde | Estado e destino |
|---|---|---|---|
| **A9** | A base autoral não valida as checagens de UDE; o conjunto de controle é pequeno (9 enunciados, 6 com rótulo) e didático, e 4 das 11 características seguem indecidíveis por função pura | `docs/produto/visao.md:521` (L-03), defeito D-12 | 🔴 **aberto — aceito como dívida**, alocado ao ciclo 005 (épico E2.1). Declarado como **não fechável neste projeto**: o que fecharia é corpus de oficina real, que o ADR 0006 proíbe |
| **A10** | A aptidão executável de `docs/produto/rounds.md` foi escrita **depois** do documento que verifica — nasceu junto do que deveria julgar | `scripts/check-rounds.sh` | 🟡 **mitigado neste ciclo**: as 5 sabotagens do §7 são o que o torna evidência, não a sua própria saída verde |
| **A11** | RNF-01 (português no projeto, inglês na superfície instalável) não tem portão executável — hoje é verificado por leitura | tabela §3 | 🟡 **aceito como dívida declarada**, candidato ao ciclo 002 |
| **A12** | Piso absoluto de ciclo no `scripts/check-conformance.sh` reprova todo repositório recém-instalado | §4.1 | 🔴 **aberto e externo**: a mensagem está escrita (`mensagens/002-para-maestro-pisos-absolutos-de-ciclo.md`); **entregá-la** é decisão humana (§8, item 5) |
| **A13** | A linha 11 da DoD é mais estrita que a própria intenção: casa **caminho**, não conteúdo | §4.2 | 🟢 **corrigido neste fechamento**: critério reescrito para medir conteúdo (`scripts/check-vazamento.sh`), troca declarada na `spec.md`, base válida com o bloco de evidência dentro como controle de regressão, e **4 sabotagens** que o veem reprovar (§7). Fica com o Product Steward só a **ratificação** (§8, item 4) |
| **A14** | *(achado deste fechamento, 2026-09-04 — não veio do gauntlet)* A seção "Fora de escopo" que o A8 corrigiu é **pontuada e não bloqueante**: uma spec que a perca cai de 92,6 para 84,6 e **continua passando** no corte ≥ 80 | `scripts/check-specs.sh` (sinal E1, 8 de 15 pontos de Escopo) | 🟡 **aberto — dívida declarada com dono no §9**. Medido, não estimado: ver o bloco abaixo |
| **A15** | *(achado deste fechamento, 2026-09-04 — não veio do gauntlet)* `docs/produto/rounds.md` e o `CHANGELOG.md` declaram que o verificador executável dos rounds **"ainda não existe"** — e ele existe, passa com 77 conferências de campo e é sabotado 5 vezes | `docs/produto/rounds.md:18`, `CHANGELOG.md:115` | 🟡 **aberto — não corrigido aqui de propósito**: os dois arquivos estão fora do lote que escreve este relatório. Dono no §9 |

**A14, medido em cópia, sem tocar o repositório.** A afirmação "pontua, não bloqueia" seria
opinião se não fosse executada. A spec de menor nota (012, **92,6**) foi copiada para um
diretório temporário, a seção "Fora de escopo" removida da cópia, e o portão rodado lá:

```text
$ TMP=$(mktemp -d)
$ cp -r --preserve=mode docs scripts specs "$TMP"/
$ python3 - "$TMP" <<'EOF'
import re, sys
p = sys.argv[1] + '/specs/012-jornadas-e-autodeclaracao/spec.md'
out, skip = [], False
for l in open(p).read().split('\n'):
    if re.match(r'^#{2,3} .*Fora de escopo', l): skip = True; continue
    if skip and re.match(r'^#{1,3} ', l): skip = False
    if not skip: out.append(l)
open(p, 'w').write('\n'.join(out))
EOF
$ cd "$TMP" && scripts/check-specs.sh \
    | grep -E "^   012 |fora de escopo 0|^. todo ciclo" ; echo "exit=${PIPESTATUS[0]}"
   012  │    30.0  │    17.9  │   19.6  │     7.0   │    10.0   │  84.6 │ ✓
    012: seções 15/15 presentes, 15 preenchidas · tipos 8/8 · DoD 7/17 linhas com comando · RF 24/24 citados em DoD ou tasks · US 13/13 com Gherkin · EARS 24/24 RF · siglas 19/20 do catálogo abertas · vagos 0 em 44 requisitos · fora de escopo 0 linha(s) · features↔US 12/12 com história · lacunas 5/5 com risco declarado · dúvidas 5 no Clarify (teto 5) · erro/recusa 11 requisito(s) (alvo 3)
✓ todo ciclo tem os quatro artefatos, spec com as seções e os tipos de requisito,
exit=0
```

Escopo caiu de **15,0 para 7,0** (o sinal E1 vale 8), a nota de **92,6 para 84,6**, o
denominador passou a dizer `fora de escopo 0 linha(s)` — e o portão **saiu 0**. A boa
notícia é que a ausência fica **visível no denominador**, que é a regra R2 funcionando; a má
é que ela não reprova. Fechar isso é apertar o portão, e apertar portão exige a sabotagem
que o veja reprovar — trabalho de ciclo, não de relatório. Fica em §9 com dono.

**A15, as duas linhas e o portão que elas dizem não existir.** É um defeito de forma, não
de conteúdo — mas é exatamente a classe que a regra R4 existe para pegar, na direção
inversa: em vez de citar um arquivo que não existe, negar um portão que existe. Documento
que declara dívida já paga ensina o leitor a desconfiar das dívidas que **não** foram pagas.

```text
$ grep -n "não existe" docs/produto/rounds.md CHANGELOG.md
docs/produto/rounds.md:18:  campos e da alocação exaustiva de D-01..D-11 ainda não existe; até ele entrar (candidato
CHANGELOG.md:115:  verificador dos seis campos e da alocação D-NN não existe ainda; a revisão
$ scripts/check-rounds.sh | sed -n "2,3p"
  rounds examinados: 11 (002, 003, 004, 005, 006, 007, 008, 009, 010, 011, 012)
  campos obrigatórios por round: 7  ·  conferências de campo: 77
```

**Limite de honestidade sobre esta seção.** Os vereditos peça a peça vêm do registro do
gauntlet conduzido durante o ciclo; quem escreve este relatório **não os presenciou**. O
que foi executado aqui e agora são os artefatos que o gauntlet produziu — o conjunto de
controle, a lacuna L-03, o D-12 alocado, os portões, a cópia sabotada do A14 — e os
comandos colados acima. Distinguir as duas coisas é a regra R1 aplicada à própria narrativa
do ciclo, e é por isso que A14 e A15 estão marcados como achados **deste fechamento**: eles
não são mérito da revisão de ontem.


## 6 · TAIL:security — passe proporcional à classe de risco

**Classe de risco desta entrega: baixa, e por um motivo estrutural.** O ciclo 001 é
**corpus documental**: zero linha de código de produção, zero dependência de execução,
zero segredo a manejar, nenhuma superfície de rede. Não há autenticação para furar,
migração para reverter nem borda para autenticar — essas superfícies nascem no ciclo 003
(esqueleto federado), que já traz **passe de segurança em contexto fresco** como portão
próprio no `docs/roadmap.md`. O risco real que **existe** aqui é outro e é exatamente o que
foi varrido: **segredo em texto** (P7) e **dado real de pessoa** (ADR 0006 / RNF-03).

Denominador do passe: **189 arquivos** (todo o repositório fora de `.git`).

```text
$ find . -path ./.git -prune -o -type f -print | wc -l
189
```

**Segredo e credencial — nada.**

```text
$ grep -rEn "(api[_-]?key|secret|password|senha|token|bearer|BEGIN [A-Z ]*PRIVATE KEY)[\"' ]*[:=][\"' ]*[A-Za-z0-9_/+-]{16,}" --include="*.md" --include="*.py" --include="*.sh" --include="*.json" --include="*.ts" --include="*.js" --include="*.yml" . | wc -l
0
$ grep -rEn "AKIA[0-9A-Z]{16}|sk-[A-Za-z0-9]{20,}|ghp_[A-Za-z0-9]{20,}|AIza[0-9A-Za-z_-]{35}|postgres(ql)?://[^ )\`]*:[^ )\`]*@" --include="*" . | grep -v "^./.git/" | wc -l
0
```

Zero atribuição de chave, zero credencial em URL de banco, zero chave privada — incluindo
o formato exato da violação canônica da linhagem (`AIza...`, a chave do provedor que
`tocbuilderv3/services/geminiService.ts:16` inicializa **no navegador** e que fundamenta o
princípio P7).

**Dado real de pessoa — nada, e a base declara-se sintética na origem.**

```text
$ python3 -c "import json; d=json.load(open('docs/produto/dados/analise-horizonte.json')); print('sintetica:', d['sintetica']); print('organizacao:', d['organizacao']); print('personas:', [p['papel'] for p in d['personas']])"
sintetica: True
organizacao: {'nome': 'Instituição Horizonte', 'descricao': 'Instituição de ensino técnico fictícia, com oferta semestral de turmas presenciais.', 'meta_declarada': 'Formar profissionais técnicos em turmas completas, com alta taxa de conclusão.'}
personas: ['Facilitadora TOC', 'Participante', 'Gestora']
```

As três personas são **papéis fictícios**, não pessoas: nenhum nome próprio, nenhum
enunciado de trabalho real, nenhuma data de desempenho. É a diferença medida no ADR 0006
entre este repositório e a irmã, onde 114 tarefas e 6 valores de responsável tornaram o
repositório obrigatoriamente privado.

**Nenhuma captura de tela existe ainda** — o vetor que na irmã exibe a base real em 21
imagens aqui tem denominador zero, e é assim que ele deve entrar no ciclo 002:

```text
$ find . -path ./.git -prune -o -type f \( -name "*.png" -o -name "*.jpg" -o -name "*.jpeg" -o -name "*.webp" \) -print | wc -l
0
```

**Um achado, e ele é o da §4.2:** a única citação da base da irmã em todo o repositório é
o **caminho** dentro do bloco de evidência do ADR 0006, num comando que imprime somente
contagens. É citação de origem, não cópia de conteúdo — e era isso que o critério antigo
da linha 11 chamava de vazamento. O critério foi reescrito para medir conteúdo, e o portão
`scripts/check-vazamento.sh` (G11) confirma este passe pela via executável: **0 achados**
nos três sinais sobre 194 arquivos. **Veredito do passe: sem vazamento de segredo e sem
dado real de pessoa em 189 arquivos; um achado de forma, nenhum de conteúdo.**

## 7 · TAIL:mutation — a suíte de sabotagem

Os quatro portões nascidos neste ciclo (`check-caminhos.sh`, `check-adrs-sucessao.sh`,
`check-specs.sh` e, no fechamento, `check-vazamento.sh`), mais o `check-rounds.sh`, foram
**sabotados de propósito** e vistos recusando. Um portão que só sabe dizer "verde" não é
evidência de nada — é a lição que a suíte cobra.

**Contagem, colada da saída:**

```text
$ scripts/tests/run-sabotagem.sh
(…as 5 bases e as 27 sabotagens, uma linha cada; o resumo que fecha a saída:)
── Sabotagem: quanto foi examinado ──
  portões cobertos: 5  ·  bases válidas aceitas: 5/5
  sabotagens declaradas: 27  ·  reprovadas pelo motivo certo: 27/27
  cada sabotagem roda sobre uma cópia em /tmp/tmp.Erz6nXquzY — o repositório não é tocado

✓ os 5 portões aceitam a base válida e reprovam as 27 sabotagens,
  cada uma pelo motivo que a tabela declara.
$ echo $?
0
```

**As duas metades importam.** A primeira prova que o portão **aceita** o que é válido (5
de 5 bases) — sem ela, um portão que reprova tudo passaria por rigoroso. A segunda prova
que ele **reprova pelo motivo declarado**, não por acidente:

| Portão | Sabotagens | Reprovou pelo motivo certo |
|---|---|---|
| `check-caminhos.sh` | 2 (`caminho-nosso-inexistente`, `isencao-nao-declarada`) | 2/2 |
| `check-adrs-sucessao.sh` | 6 (`antigo-sem-superseded-by`, `sem-campo-principios-tocados`, `sem-campo-sucede`, `fora-do-registro-jsonl`, `fora-do-indice`, `sucede-adr-inexistente`) | 6/6 |
| `check-rounds.sh` | 5 (`campo-obrigatorio-ausente`, `dependencia-circular`, `dependencia-inexistente`, `defeito-sem-destino`, `defeito-em-dois-destinos`) | 5/5 |
| `check-specs.sh` | 10 (`artefato-do-ciclo-ausente`, `secao-obrigatoria-renomeada`, `sem-requisito-de-interface`, `sem-status`, `dod-sem-coluna-de-verificacao`, `plano-com-uma-tabela-so`, `linha-de-principio-vazia`, `artefato-condicional-nao-declarado`, `cauda-incompleta`, `dod-sem-linha-executavel-cai-na-regua`) | 10/10 |
| `check-vazamento.sh` | 4 (`vazamento-nome-de-pessoa-em-campo-de-pessoa`, `vazamento-nome-de-pessoa-em-coluna-de-tabela`, `vazamento-registro-no-formato-da-base-da-irma`, `vazamento-base-real-lida-por-codigo`) | 4/4 |
| **Total** | **27** | **27/27** |

**A base válida do `check-vazamento.sh` é, ela própria, um controle de regressão.**
`scripts/tests/sabotagem/vazamento/` guarda **de propósito** um ADR com bloco de evidência
citando o caminho da base real da irmã — exatamente a linha que o critério antigo chamava
de vazamento. Se o portão novo reprovasse essa base, teria voltado a ser o critério antigo;
ele a aceita (`bases válidas aceitas: 5/5`) e reprova as quatro mutações que plantam
vazamento de verdade. Os nomes plantados são **inventados**: a não-colisão com a base real
foi executada antes de escrevê-los, comparando conjuntos e imprimindo só booleanos, para
que o teste da regra do ADR 0006 não violasse a própria regra.

**Limite declarado.** A sabotagem cobre **5 portões**, os deste projeto. O
`check-conformance.sh`, o `check-links.sh` e o `check-install.sh` vêm do método e são
sabotados **lá**, não aqui — cobrá-los seria escrever no `maestro`, que o P1 proíbe.

## 8 · TAIL:gate — NÃO marcado, e a lista do que aguarda o Product Steward

A DoD fechou com **17 de 18 verificações verdes**, a única vermelha diagnosticada em §4.1
com causa raiz e **não contornada** — a outra virou verde porque o **critério** foi
reescrito e a reescrita foi declarada e provada por sabotagem (§4.2), nunca porque o número
esperado baixou; a cauda de revisão, segurança e mutação
está escrita com a saída colada, e a revisão independente virou achados numerados com
destino (§5). Daqui em diante o que falta **não é delegável a agente**, e a caixa
`TAIL:gate` em `tasks.md` fica deliberadamente **em branco**: quem executou não aprova o
que executou.

**O que aguarda a assinatura do Product Steward — sete itens, nenhum deles marcável por
agente:**

| # | O que decidir | Por que é humano | Onde está a matéria |
|---|---|---|---|
| **1** | **Ratificar a constituição do projeto v1.0.0** e os **oito ADRs 0001–0008** | Ratificação é ato de quem responde pela política (Princípio II do método: o *Accountable* é sempre humano) | `docs/governance/constitution.md`, `docs/adr/` |
| **2** | **Responder as cinco perguntas** de `docs/produto/visao.md` §7 — ou adiar cada uma explicitamente | Mudam o produto, não a execução. A **pergunta 1** (colaboração por projeto ou isolamento por usuário) é pré-condição declarada do ciclo 002, porque muda as telas do épico E1.1 | `docs/produto/visao.md` §7 |
| **3** | **Responder os três `[DÚVIDA]`** do `## Clarify` da `spec.md` deste ciclo | Dúvida declarada fica aberta até o gate, por regra do ADR 0004 §4 | `spec.md`, seção `## Clarify` |
| **4** | **Ratificar o critério 11 reescrito** (achado A13): ele deixou de casar a **string do caminho** da base da irmã e passou a medir **conteúdo vazado**, pelo portão `scripts/check-vazamento.sh`. A execução está feita, declarada na spec e provada por quatro sabotagens; o que falta é a assinatura | Mudar critério de aceite é mexer no contrato do ciclo — quem executou a troca não a ratifica | §4.2, §7, §5 (A13) · `spec.md`, "Mudança declarada no critério 11" |
| **5** | **Autorizar a entrega da mensagem 002 ao método** (achado A12) — levá-la a `GHDaru/maestro` é escrita fora da fronteira do P1 | O P1 exige aprovação humana explícita, caso a caso, para escrita externa | `mensagens/002-para-maestro-pisos-absolutos-de-ciclo.md` |
| **6** | **Aceitar (ou recusar) as três ressalvas do §9** — o que fica de dívida e com que dono | Aceitar dívida é decidir o que o próximo ciclo carrega | §9 |
| **7** | **Autorizar a promoção `dev` → `main`** — o gate de merge | É o portão de merge, indelegável por definição | `scripts/promote-main.sh`, que **não foi executado por agente nenhum neste ciclo** |

Enquanto essa assinatura não existe, **o veredito deste ciclo é "revisado e corrigido,
aguardando gate humano"**, e nada abaixo do ciclo 002 começa. Dizer qualquer outra coisa
seria marcar uma caixa sem testemunha, que é o defeito que este projeto herdou pronto para
não repetir.

## 9 · Fecho — o que fica de dívida para o ciclo seguinte, com dono

> Um ciclo fecha quando o que **não** foi feito está escrito, numerado e tem dono. Sem isso,
> o que fica aberto vira memória de quem estava na sala — e o método existe justamente
> porque essa memória não sobrevive ao próximo contexto.

| # | Dívida | Por que não fecha aqui | Dono | Onde entra |
|---|---|---|---|---|
| **Dv-1** | RNF-01 (português no projeto, inglês na superfície instalável) não tem portão executável — é verificado por leitura | Escrever o portão é trabalho de ciclo, e ele precisa da sabotagem que o veja reprovar antes de valer como evidência | **construtor do ciclo 002** | round 002, `docs/produto/rounds.md` · achado **A11** |
| **Dv-2** | A circularidade da base autoral está **mitigada, não resolvida**: 9 enunciados de controle, 6 com rótulo, e 4 das 11 características de UDE indecidíveis por função pura | **Não fecha neste projeto**: o que fecharia é corpus de oficina real, escrito e rotulado por facilitadores humanos — dado de pessoa real, que o ADR 0006 proíbe em fixture, spec e exemplo | **ciclo 005**, épico E2.1 (amplia o controle e transforma cada divergência em teste) | lacuna L-03 em `docs/produto/visao.md:521`, defeito D-12 · achado **A9** |
| **Dv-3** | O portão de conformidade do método reprova todo repositório recém-instalado, por pisos absolutos de ciclo | O arquivo é do método e `GHDaru/maestro` é leitura (P1). A mensagem está escrita; **entregá-la** é escrita externa | **Product Steward** (§8, item 5) · depois, o método | `mensagens/002-para-maestro-pisos-absolutos-de-ciclo.md`, estado `aberta` · achado **A12** |
| **Dv-4** | ~~A linha 11 da DoD casa caminho e não conteúdo~~ — **executada no fechamento**: o critério foi reescrito para medir conteúdo (`scripts/check-vazamento.sh`), a troca está declarada na spec e quatro sabotagens provam que o portão reprova vazamento plantado | O que sobra não é dívida técnica, é **ratificação**: quem executou a troca de critério não a aprova | **Product Steward** ratifica (§8, item 4) | §4.2, §7 · achado **A13** |
| **Dv-5** | A seção "Fora de escopo" é **pontuada e não bloqueante**: perdê-la custa 8 dos 15 pontos de Escopo e a spec continua passando no corte ≥ 80 (medido: 92,6 → 84,6, portão saiu 0) | Apertar o portão exige a sabotagem que o veja reprovar, e sabotagem nova é trabalho de ciclo — não de relatório de fechamento | **construtor do ciclo 002**, junto com Dv-1 (os dois mexem em `scripts/check-specs.sh` e em `scripts/tests/run-sabotagem.sh`) | achado **A14** |
| **Dv-6** | `docs/produto/rounds.md:18` e o `CHANGELOG.md:115` ainda declaram que o verificador executável dos rounds **"ainda não existe"** — e ele existe, passou com 77 conferências de campo e foi sabotado 5 vezes | Os dois arquivos estão **fora do lote** que escreve este relatório; corrigi-los daqui seria escrever onde não fui encarregado, e a dívida declarada é preferível à correção fora de escopo | **construtor do ciclo 002**, na abertura (é uma linha em cada arquivo) | achado **A15** |
| **Dv-7** | A aptidão dos rounds nasceu **depois** do documento que verifica | Mitigado, não anulado: o que a torna evidência são as 5 sabotagens do §7, não a sua saída verde | **revisão independente do ciclo 002**, que a exercita contra um `rounds.md` adversário | achado **A10** |

**Três ressalvas explícitas, para que ninguém as descubra depois.**

1. **O placar 10/10 não é o veredito deste relatório — é o do gauntlet.** O corpus venceu as
   dez comparações às cegas contra dois corpora externos, e isso mede *forma e profundidade
   contra uma barra*. Não mede se o produto é o certo: essa pergunta é a §7 da visão e está
   aberta com o Product Steward (§8, item 2).
2. **Seis achados seguem abertos, e a conta é esta:** **um** é externo (**A12**, do
   método) e depende de autorização humana para sair daqui; **cinco** são dívida com dono e
   ciclo declarados (**A9**, **A10**, **A11**, **A14**, **A15**). O **A13** saiu da lista
   por ter sido **corrigido e provado** neste fechamento — o único achado que fechou, e
   fechou com sabotagem, não com uma frase. Nenhum foi fechado escrevendo que estava
   fechado, que é o único desfecho que este projeto proíbe.
3. **Uma linha da DoD continua vermelha no fecho, e continua vermelha de propósito.** A de
   conformidade (linha 13) é **externa** — piso absoluto de ciclo no portão do método — e
   está relatada em `mensagens/002-para-maestro-pisos-absolutos-de-ciclo.md`; ela **não** foi
   reescrita para a variante que passa. A linha 11 ficou verde, e a distinção importa: o que
   mudou foi o **critério**, porque ele media caminho citado quando dizia medir vazamento; a
   troca está declarada na spec e no §4.2, e o critério novo é **mais largo** que o antigo —
   pega nome próprio, registro transplantado e leitura da base real em código, três classes
   que o antigo não via. Afrouxar teria sido baixar o número ou isentar o arquivo que
   incomoda; nenhuma das duas foi feita.
