# QA report 001 — Fundação e planejamento (ciclo documental)

> Siglas deste documento: **DoD** — Definition of Done (definição de pronto) · **DoR** —
> Definition of Ready (definição de pronto para começar) · **ADR** — Architecture Decision
> Record (Registro de Decisão Arquitetural) · **TOC** — Teoria das Restrições · **APH** —
> Aplicação ↔ Harness · **UDE** — Efeito Indesejável · **ARA** — Árvore da Realidade Atual ·
> **NC** — Nuvem de Conflito.

- **Data**: 2026-09-03 · **Raia**: plena · **Veredito**: **entregue, aguardando gate humano**
- **Portões executados**: 17 verificações distintas — **15 verdes, 2 vermelhas**, ambas as
  vermelhas diagnosticadas abaixo e **nenhuma delas afrouxada** para o repositório passar.

> **Regra R1 e R2 aplicadas linha a linha.** Toda saída abaixo é a saída **literal** do
> comando escrito ao lado, executado em 2026-09-03 neste repositório. Nenhum `✓` foi
> transcrito; nenhum número foi lembrado. Onde o portão imprime o tamanho do que examinou,
> esse número está colado — verde sem denominador não é evidência.

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
| G8 | Suíte de sabotagem (mutação) | `scripts/tests/run-sabotagem.sh` | **0** ✓ | `portões cobertos: 4 · bases válidas aceitas: 4/4` · `sabotagens declaradas: 23 · reprovadas pelo motivo certo: 23/23` |
| G9 | Base sintética e critérios de UDE | `python3 docs/produto/dados/medir-base.py` | **0** ✓ | ARA `16 nós (12 UDEs, 4 causas) · 16 arestas`; NC `5 entidades · 7 arestas com premissa · 2 injeções`; 8 checagens decidíveis sobre 12 UDEs autorais **e** 9 enunciados de controle externos |
| G10 | Conformidade do ciclo | `scripts/check-conformance.sh 001` | **1** ✗ | `cycles checked: 1` — **vermelho estrutural, diagnóstico em §4.1** |

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
    001  │    30.0  │    25.0  │   17.8  │    15.0   │     7.0   │  94.8 │ ✓
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
| 11 | Sem vazamento da base real da irmã | `grep -rn "gestaodeprioridades/protot[i]po" --include='*.md' . \| wc -l` | `0` | `2` (era `1` antes deste relatório citar o achado — ver §4.2) | **✗ ver §4.2** |
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
$ grep -rn "gestaodeprioridades/protot[i]po" --include='*.md' . | wc -l
2
```

*(a contagem era `1` quando este relatório começou a ser escrito e passou a `2` ao citar o
achado: a segunda ocorrência é a linha do §4.2 abaixo, que reproduz a primeira. Um portão
que casa **caminho** conta a denúncia junto com o denunciado — é o mesmo defeito de
critério, visto de outro ângulo, e está deixado à vista de propósito.)*

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
| RF-11 — portões executáveis e **não lenientes** | G8 (`bases válidas aceitas: 4/4` · `sabotagens reprovadas pelo motivo certo: 23/23`) | ✓ |
| RF-12 — site gerado só pelo gerador vendorizado | DoD 10 (código 0) | ✓ |
| RNF-01 — português no projeto, inglês na superfície instalável | Revisão do gauntlet (§5); sem portão executável — **dívida declarada** | 🟡 |
| RNF-02 — sigla por extenso na primeira ocorrência | G5 (`siglas 11/16 do catálogo abertas` na spec 001; medido spec a spec) + revisão | ✓ |
| RNF-03 — nenhum dado real de pessoa | TAIL:security (§6): 189 arquivos varridos, 0 segredos, 0 imagens, base `sintetica: True` | ✓ |
| RNF-04 — todo caminho relativo resolve | G3 (`337`) + G4 (`572`) | ✓ |
| RNF-05 — todo número afirmado foi executado | Este relatório inteiro; G1 (`Portões executados: 6 · verdes: 6`) | ✓ |

## 4 · Os dois portões vermelhos (diagnóstico antes de correção)

Nenhum dos dois foi corrigido afrouxando o portão. Os dois são registrados como
**achados abertos** e entram no gate humano.

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
piso acima como evidência. Ela **ainda não existe** — escrevê-la está fora do lote que
produziu este relatório, e citar como pronto um arquivo que não está no disco é
exatamente o defeito que a regra R4 existe para pegar (e pegou, neste próprio parágrafo,
na primeira redação).

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
    ✓ TAIL:gate evidence: a DoD fechou **15 de 17 verificações verdes**, com as 2 
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

**Não foi corrigido, por dois motivos que se somam.** Editar o corpo do ADR 0006 é
proibido — o método guarda ADR committado como histórico e o guarda `PreToolUse` recusa
a reescrita; a rota, se for o caso, é um ADR novo que suceda. E afrouxar o critério para
o repositório passar é o anti-padrão que este relatório existe para não cometer. Fica
como **achado aberto para o gate humano**: o Product Steward decide entre isentar
explicitamente `docs/adr/0006-*.md` no critério (a isenção declarada, como o
`check-caminhos.sh` já faz com 135 caminhos) ou reescrever o critério para casar
**conteúdo** e não caminho. Enquanto não decide, a linha 11 fica **vermelha e visível** —
que é a única coisa pior do que consertar errado: consertar em silêncio.

O que o critério queria proteger **foi verificado por outro caminho e está limpo**: ver
§6, TAIL:security.

## Cauda de fechamento — a evidência, uma linha por passo

<!-- Uma entrada por token TAIL não-n/a. O que foi OBSERVADO, nunca a intenção repetida.
     O detalhe de cada linha está na seção de mesmo nome, logo abaixo. -->

- TAIL:review — a revisão independente foi o **gauntlet de crítica às cegas**: 10 peças do
  corpus julgadas por críticos em contexto fresco contra dois corpora externos (o da irmã
  `gestaodeprioridades` e o do PROJETO_ECS), placar **9 vitórias e 1 derrota** na primeira
  rodada; a peça derrotada foi `docs/produto/visao.md`, por circularidade da base autoral
  das checagens de Efeito Indesejável (UDE), foi retrabalhada dirigida por essa lacuna e
  venceu o rejulgamento — **10/10**. Cinco achados ficaram **abertos**, tabelados em §5, e
  o retrabalho é verificável: conjunto de controle de 9 enunciados externos, lacuna L-03
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
  os 4 portões deste projeto **aceitam** a base válida (`bases válidas aceitas: 4/4`) e
  **reprovam pelo motivo declarado** as 23 mutações (`sabotagens declaradas: 23 ·
  reprovadas pelo motivo certo: 23/23`), cada uma sobre uma cópia em `/tmp`, sem tocar o
  repositório. Limite declarado: os portões vindos do método são sabotados no método, não
  aqui (P1). Detalhe: §7.
- TAIL:gate — a DoD fechou **15 de 17 verificações verdes**, com as 2 vermelhas
  diagnosticadas por causa raiz em §4 e **nenhuma afrouxada**, e as três caudas acima
  escritas com a saída colada; a caixa correspondente em `tasks.md` fica **em branco de
  propósito**, porque quem executou não aprova o que executou. Aguardam a assinatura do
  Product Steward a ratificação da constituição e dos 8 ADRs, as respostas às cinco
  perguntas da visão §7 e aos três `[DÚVIDA]` do Clarify, a decisão sobre os dois achados
  vermelhos, e a promoção `dev` → `main`. Detalhe: §8.

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
(`docs/produto/visao.md`): o crítico apontou que a base autoral da "Instituição Horizonte"
fora escrita pelo mesmo autor das oito checagens de UDE e **escrita para trazer as
patologias que elas procuram** — logo o "3 de 12 UDEs passam" media o acordo do autor
consigo mesmo, e o "divergências: 0" era tautologia, não evidência. A peça foi
**retrabalhada dirigida por essa lacuna nomeada** e **venceu o rejulgamento**, fechando
**10/10**.

**O retrabalho é verificável, não é palavra.** Ele deixou três marcas que este relatório
executou agora:

1. um **conjunto de controle de 9 enunciados colhidos da linhagem TOC-Builder**, escritos
   antes das checagens e por outra mão — `medir-base.py` os mede e imprime
   `FALSO POSITIVO ...: 0` e `FALSO NEGATIVO ...: 1 (K-03)`;
2. a **lacuna L-03 declarada em aberto** em `docs/produto/visao.md:521`, dizendo por que o
   defeito **não fecha neste projeto** — corpus de oficina real é dado de pessoa real, que
   o ADR 0006 proíbe — em vez de datar um fechamento falso;
3. o defeito virou **D-12**, alocado ao round 005 (`docs/produto/rounds.md:322`) e
   transformado em critério de aceite do épico E2.1.

**Achados que a revisão deixou abertos** (nenhum deles fechado por este relatório):

| Achado | Onde | Estado |
|---|---|---|
| A base autoral não valida as checagens de UDE; o controle de 9 enunciados é pequeno e didático, e 4 das 11 características seguem indecidíveis por função pura | `docs/produto/visao.md:521` (L-03), D-12 | 🔴 aberto, alocado ao ciclo 005 |
| A aptidão executável de `docs/produto/rounds.md` foi escrita **depois** do documento — o `check-rounds.sh` existe e passou (77 conferências), mas nasceu junto do que verifica | `scripts/check-rounds.sh` | 🟡 mitigado neste ciclo; a sabotagem (§7) é o que o torna evidência |
| RNF-01 (português no projeto, inglês na superfície instalável) não tem portão executável | tabela §3 | 🟡 dívida declarada, candidata ao ciclo 002 |
| Piso absoluto de ciclo no `check-conformance.sh` | §4.1 | 🔴 aberto, externo — mensagem ao método |
| DoD linha 11 mais estrita que a própria intenção | §4.2 | 🔴 aberto, decisão do Product Steward |

**Limite de honestidade sobre esta seção.** Os vereditos peça a peça vêm do registro do
gauntlet conduzido durante o ciclo; quem escreve este relatório **não os presenciou**. O
que foi executado aqui e agora são os artefatos que o gauntlet produziu — o conjunto de
controle, a lacuna L-03, o D-12 alocado — e os portões que passam sobre eles. Distinguir
as duas coisas é a regra R1 aplicada à própria narrativa do ciclo.

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
contagens. É citação de origem, não cópia de conteúdo — mas mantém a linha 11 da DoD
vermelha até o Product Steward decidir a isenção. **Veredito do passe: sem vazamento de
segredo e sem dado real de pessoa em 189 arquivos; um achado de forma, nenhum de
conteúdo.**

## 7 · TAIL:mutation — a suíte de sabotagem

Os três portões nascidos neste ciclo (`check-caminhos.sh`, `check-adrs-sucessao.sh`,
`check-specs.sh`), mais o `check-rounds.sh`, foram **sabotados de propósito** e vistos
recusando. Um portão que só sabe dizer "verde" não é evidência de nada — é a lição que a
suíte cobra.

**Contagem, colada da saída:**

```text
── Sabotagem: quanto foi examinado ──
  portões cobertos: 4  ·  bases válidas aceitas: 4/4
  sabotagens declaradas: 23  ·  reprovadas pelo motivo certo: 23/23
  cada sabotagem roda sobre uma cópia em /tmp/tmp.J8bglMWIG9 — o repositório não é tocado

✓ os 4 portões aceitam a base válida e reprovam as 23 sabotagens,
  cada uma pelo motivo que a tabela declara.
$ echo $?
0
```

**As duas metades importam.** A primeira prova que o portão **aceita** o que é válido (4
de 4 bases) — sem ela, um portão que reprova tudo passaria por rigoroso. A segunda prova
que ele **reprova pelo motivo declarado**, não por acidente:

| Portão | Sabotagens | Reprovou pelo motivo certo |
|---|---|---|
| `check-caminhos.sh` | 2 (`caminho-nosso-inexistente`, `isencao-nao-declarada`) | 2/2 |
| `check-adrs-sucessao.sh` | 6 (`antigo-sem-superseded-by`, `sem-campo-principios-tocados`, `sem-campo-sucede`, `fora-do-registro-jsonl`, `fora-do-indice`, `sucede-adr-inexistente`) | 6/6 |
| `check-rounds.sh` | 5 (`campo-obrigatorio-ausente`, `dependencia-circular`, `dependencia-inexistente`, `defeito-sem-destino`, `defeito-em-dois-destinos`) | 5/5 |
| `check-specs.sh` | 10 (`artefato-do-ciclo-ausente`, `secao-obrigatoria-renomeada`, `sem-requisito-de-interface`, `sem-status`, `dod-sem-coluna-de-verificacao`, `plano-com-uma-tabela-so`, `linha-de-principio-vazia`, `artefato-condicional-nao-declarado`, `cauda-incompleta`, `dod-sem-linha-executavel-cai-na-regua`) | 10/10 |
| **Total** | **23** | **23/23** |

**Limite declarado.** A sabotagem cobre **4 portões**, os deste projeto. O
`check-conformance.sh`, o `check-links.sh` e o `check-install.sh` vêm do método e são
sabotados **lá**, não aqui — cobrá-los seria escrever no `maestro`, que o P1 proíbe.

## 8 · TAIL:gate — do Product Steward, indelegável

A DoD fechou com **15 de 17 verificações verdes**, as duas vermelhas diagnosticadas em
§4 com causa raiz e **nenhuma delas contornada**, e a cauda de revisão, segurança e
mutação escrita com a saída colada. Daqui em diante o que falta **não é delegável a
agente**, e a caixa correspondente em `tasks.md` fica deliberadamente **em branco**: quem
executou não aprova o que executou. Aguardam a assinatura do Product Steward:

1. **Ratificar a constituição do projeto v1.0.0** e os **oito ADRs 0001–0008**;
2. **Responder as cinco perguntas** de `docs/produto/visao.md` §7 — ou adiar cada uma
   explicitamente. A **pergunta 1** (colaboração por projeto ou isolamento por usuário) é
   pré-condição declarada do ciclo 002, porque muda as telas do épico E1.1;
3. **Responder os três `[DÚVIDA]`** do `## Clarify` da `spec.md` deste ciclo;
4. **Decidir os dois achados vermelhos**: a isenção da DoD linha 11 (§4.2) e o envio da
   mensagem ao método sobre os pisos absolutos de ciclo (§4.1);
5. **Autorizar a promoção `dev` → `main`** — o gate de merge.

Enquanto essa assinatura não existe, **o veredito deste ciclo é "entregue, aguardando gate
humano"**, e nada abaixo do ciclo 002 começa. Dizer qualquer outra coisa seria marcar uma
caixa sem testemunha, que é o defeito que este projeto herdou pronto para não repetir.
