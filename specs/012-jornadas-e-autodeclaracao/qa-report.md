# QA Report 012 — Jornadas e autodeclaração

> **Siglas deste documento**, na primeira ocorrência: **QA** — *Quality Assurance* (garantia
> de qualidade) · **DoD** — *Definition of Done* (Definição de Pronto) · **ADR** —
> *Architecture Decision Record* (Registro de Decisão Arquitetural) · **APH** — Aplicação ↔
> Harness, o padrão da fronteira · **TOC** — Teoria das Restrições · **ARA** — Árvore da
> Realidade Atual · **NC** — Nuvem de Conflito · **ARF** — Árvore da Realidade Futura ·
> **APR** — Árvore de Pré-Requisitos · **AT** — Árvore de Transição · **S&T** — Estratégia &
> Táticas · **UDE** — Efeito Indesejável (*Undesirable Effect*) · **RF/RI/RNF/RN/INT** —
> requisito funcional / de interface / não funcional / regra de negócio / integração ·
> **P1..P7** — princípios da constituição do projeto · **R1..R5** — regras herdadas de
> retrospectiva · **CI** — integração contínua · **IA** — inteligência artificial · **URL**
> — *Uniform Resource Locator* · **HTTP** — *HyperText Transfer Protocol* · **SSE** —
> *Server-Sent Events* · **UUID** — identificador universal único.

- **Data desta bateria**: 2026-09-06 · **Raia**: plena
- **Veredito atual**: **parcialmente executado, com o executado provado e o não executado
  nomeado — aguardando o gate humano.** Duas das quatro frentes fecharam com evidência
  (jornadas vivas e conformidade executável do Nível 1); uma **não foi executada** (a matriz
  de aderência, T-07) e uma fechou **pela metade** (o site regenerou, o ADR de
  autodeclaração não existe). O detalhe está em §2, o que falta em §9, e **nada aqui está
  marcado como pronto sem a saída colada ao lado**.
- **Portões executados nesta bateria**: **16 · verdes: 16 · vermelhos: 0** pelo agregador
  `scripts/evidencia.sh` (§1), mais três verificações que ele não cobre (§3, §4, §7).
  O `scripts/check-conformance.sh 012` continua **vermelho por causa externa**, e a causa
  está diagnosticada em §8.1 — não foi afrouxada, foi relatada e parada (P1).

> **R1 e R2 aplicadas linha a linha.** Toda saída deste documento é a saída **literal** do
> comando escrito ao lado, executada neste repositório em **2026-09-06**, com o horário dito
> onde o número se mexe. Nenhum `✓` foi transcrito. Onde o portão imprime o tamanho do que
> examinou, esse número está colado: verde sem denominador não é evidência.
>
> **Uma ressalva de leitura que este ciclo precisa fazer e o 001 não precisava.** O
> repositório esteve **sob construção concorrente** enquanto esta bateria rodava — a suíte
> do serviço passou de 839 para 854 testes e dois ADRs (0009 e 0010) nasceram no intervalo
> de algumas horas. Por isso cada contagem que depende do tamanho do corpus aparece aqui
> **com a hora**, e as que dependem de artefato em disco estão registradas em
> [`../../scripts/evidencia-colada.json`](../../scripts/evidencia-colada.json), para o
> portão do §3 as reprovar quando envelhecerem em vez de ninguém notar.

## 0 · Histórico de veredito — os estados por que este ciclo passou

| # | Data | Estado | O que aconteceu | Evidência |
|---|---|---|---|---|
| **V1** | 2026-09-06 | **construído em parte** | As quatro jornadas que têm tela nasceram vivas, com 36 capturas do build real geradas por script versionado, e o portão `scripts/check-jornadas.sh` nasceu com elas. | §3 |
| **V2** | 2026-09-06 | **medido de fora** | A suíte de conformidade do Nível 1 do `GHDaru/protocolos` foi executada contra o serviço: **11/11 verificados, 12 itens a autodeclarar**. | §4 |
| **V3** | 2026-09-06 | **REPROVADO por revisão independente — 3 achados de honestidade** | Um crítico em contexto fresco encontrou três defeitos, **nenhum de código, os três de evidência**: saída colada que não reproduzia mais, contagem errada anunciada, e a cauda deste ciclo vazia enquanto o trabalho existia. | §5 |
| **V4** | 2026-09-06 | **corrigido, com portão novo** | Os três achados foram corrigidos na raiz e o defeito virou **regra executável**: nasceu `scripts/check-evidencia-colada.sh`, que re-executa a saída colada e reprova quando ela envelhece. | §3, §5, §7 |
| **V5** | 2026-09-06 | **entregue com evidência** | Bateria de 16 portões verdes, 48 sabotagens reprovando pelo motivo declarado, site regenerado sem divergência, e as três caudas de agente escritas com a saída colada. | §1, §7 |
| **V6** | — | **aguardando gate humano** | `TAIL:gate` **não marcado**, de propósito: quem executou não aprova o que executou. | §8 |

## 1 · Bateria de portões (denominador colado)

Gerada por [`../../scripts/evidencia.sh`](../../scripts/evidencia.sh), que roda cada portão
e **cola** a linha de denominador que o próprio portão imprimiu — nunca a reescreve.

```text
$ scripts/evidencia.sh > /tmp/evid.md
$ echo $?
0
$ head -5 /tmp/evid.md
<!-- gerado por scripts/evidencia.sh em 2026-09-06 — não editar à mão: rode de novo -->

## Evidência dos portões — 2026-09-06

Portões executados: **16** · verdes: **16** · vermelhos: **0**.
```

| Portão | Comando | Saída | Veredito | Denominador (linha do próprio portão) |
|---|---|---|---|---|
| `check-caminhos.sh` | `scripts/check-caminhos.sh` | `0` | ✓ verde | arquivos varridos: 123 caminhos conferidos: 990 · isentos declarados: 313 · entregas futuras declaradas: 97 · moldes ignorados: 15 <br>· saída completa: 5 linhas (contadas por este script) |
| `check-adrs-sucessao.sh` | `scripts/check-adrs-sucessao.sh` | `0` | ✓ verde | ADRs examinados: 10 · linhas de tabela no índice: 11 · linhas em docs/records/decisoes.jsonl: 11 verificações executadas: 40 · sucessões declaradas: 0 · sucedidos declarados: 0 · linhas adr-* conferidas: 10 <br>· saída completa: 7 linhas (contadas por este script) |
| `check-rounds.sh` | `scripts/check-rounds.sh` | `0` | ✓ verde | rounds examinados: 11 (002, 003, 004, 005, 006, 007, 008, 009, 010, 011, 012) campos obrigatórios por round: 7 · conferências de campo: 77 defeitos medidos em docs/produto/visao.md: 12 · alocados a round: 10 · declarados sem round: 2 <br>· saída completa: 8 linhas (contadas por este script) |
| `check-specs.sh` | `scripts/check-specs.sh` | `0` | ✓ verde | ciclos examinados: 12 (001, 002, 003, 004, 005, 006, 007, 008, 009, 010, 011, 012) verificações: artefatos 48 · seções e status 185 · tipos de requisito 71 · linhas de Constitution Check 204 · tokens ART 60 · tokens TAIL 48 · specs pontuadas 12 = 628 <br>· saída completa: 38 linhas (contadas por este script) |
| `check-links.sh` | `scripts/check-links.sh` | `0` | ✓ verde | checked: 465 <br>· saída completa: 3 linhas (contadas por este script) |
| `check-install.sh` | `scripts/check-install.sh` | `0` | ✓ verde | ok: skills (skills) ok: cycle script (scripts/new-cycle.sh) ok: promotion script (scripts/promote-main.sh) ok: spec-driven templates (.specify/templates) ok: constitution (docs/governance/principles.md) ok: operating model (docs/governance/operating-model.md)  <br>· saída completa: 24 linhas (contadas por este script) |
| `check-vazamento.sh` | `scripts/check-vazamento.sh` | `0` | ✓ verde | arquivos varridos: 525 · linhas varridas: 109473 · registros JSON inspecionados: 3312 sinais aplicados: 3 (V1 nome próprio em campo de pessoa · V2 registro no formato da base da irmã · V3 base real lida por código) campos de pessoa vigiados: 21 · chave <br>· saída completa: 8 linhas (contadas por este script) |
| `check-jornadas.sh` | `scripts/check-jornadas.sh` | `0` | ✓ verde | jornadas examinadas: 4 (001-chegada-e-embarque.md, 002-primeiro-projeto-e-ara.md, 003-nuvem-de-conflito.md, 007-a-travessia.md) capturas em disco: 36 · citações de imagem: 36 · data das capturas (manifesto): 2026-09-06 verificações executadas: 80 · heur <br>· saída completa: 8 linhas (contadas por este script) |
| `check-arquitetura.sh` | `scripts/check-arquitetura.sh` | `0` | ✓ verde | contratos declarados no pyproject.toml: 3 Analyzed 100 files, 452 dependencies. <br>· saída completa: 12 linhas (contadas por este script) |
| `check-raiz-do-agregado.sh` | `scripts/check-raiz-do-agregado.sh` | `0` | ✓ verde | arquivos Python varridos: 146 guardas `_exigir_raiz` encontradas: 8 de 8 mutações de grafo raízes de ferramenta registradas: 2 <br>· saída completa: 9 linhas (contadas por este script) |
| `check-trava-otimista.sh` | `scripts/check-trava-otimista.sh` | `0` | ✓ verde | arquivos varridos: 5 (adaptador SQL, duplo em memória, agregado, registro §A.7, borda HTTP) caminhos de escrita conferidos: 3 declarados · 3 encontrados no adaptador guardas `_gravar_projeto` encontradas: 3 de 3 caminhos de escrita ✓ trava otimista ínteg <br>· saída completa: 13 linhas (contadas por este script) |
| `check-evidencia-colada.sh` | `scripts/check-evidencia-colada.sh` | `0` | ✓ verde | afirmações registradas: 31 · comandos executados com sucesso: 31/31 ocorrências conferidas: 36 · arquivos alcançados: 8 <br>· saída completa: 7 linhas (contadas por este script) |
| `check-manifesto.sh` | `scripts/check-manifesto.sh` | `0` | ✓ verde | telas declaradas: 4 ações declaradas: 11 sabotagens aplicadas: 7; repelidas: 7 <br>· saída completa: 16 linhas (contadas por este script) |
| `check-politica.sh` | `scripts/check-politica.sh` | `0` | ✓ verde | arquivos de produção varridos: 80 arquivos que compõem PoliticaPorCapability: 3 <br>· saída completa: 4 linhas (contadas por este script) |
| `check-canal.sh` | `scripts/check-canal.sh` | `0` | ✓ verde | arquivos de teste encontrados: 1 # tests 21 # pass 21 # fail 0 <br>· saída completa: 7 linhas (contadas por este script) |
| `check-conformidade-aph.sh` | `scripts/check-conformidade-aph.sh` | `0` | ✓ verde | · persistência ......... postgres (exigida: postgres) · migração (alembic) ... 0005 · natureza do turno .... ENLATADO E DETERMINÍSTICO — não há provedor de modelo Veredito: APTO nos itens verificáveis — 11/11 verificados; 12 itens a autodeclarar. <br>· saída completa: 62 linhas (contadas por este script) |

> **Estes denominadores são de 2026-09-06 03:14Z e movem-se, e dizê-lo é parte da prova.**
> Os portões que contam linhas do corpus — `check-caminhos.sh`, `check-vazamento.sh`,
> `check-links.sh` — incluem **este arquivo** no que varrem: re-executar a bateria depois
> desta revisão devolve números maiores, e isso é o comportamento que a regra R2 pede, não
> instabilidade. O que **não** se move é o código de saída de cada portão, e é ele que
> decide o veredito.
>
> **O que esta tabela NÃO diz** (o mesmo limite que o próprio agregador imprime no fim):
> ela diz que os portões **rodaram**, não que sabem **reprovar**. Essa prova é outra e está
> em §7 — 48 sabotagens sobre 9 bases, cada uma exigindo o motivo declarado na saída.

## 2 · A DoD do ciclo — as 17 linhas, com o que fechou e o que não fechou

**Sete linhas fecharam, uma fechou com ressalva declarada, e nove não foram executadas.**
Escrever "atendido" em qualquer uma delas sem comando seria exatamente a mentira que este
ciclo — cujo produto é uma **declaração** — existe para não ser.

| # | Critério (spec § Critérios de aceite) | Comando | Estado | Evidência |
|---|---|---|---|---|
| 1 | Todas as capturas regeneram do build atual | `node docs/jornadas/scripts/capturar-telas.mjs` | **fechado em parte** | 36 capturas geradas em 2026-09-06T02:08:44Z pelo script versionado; as jornadas J-04, J-05 e J-06 **não têm tela para capturar** (§3.2) |
| 2 | Regeneração determinística | — | **não executado** | Duas corridas seguidas não foram comparadas byte a byte. Dívida **Dv-1** (§9) |
| 3 | Nenhuma captura órfã, nenhuma citação quebrada | `scripts/check-jornadas.sh` | **✓ fechado** | `capturas em disco: 36 · citações de imagem: 36`, `verificações executadas: 80`, saída `0` (§3.1) |
| 4 | Travessia com persona única | jornada J-07 | **fechado em parte** | A travessia existe e é ARA → NC, com a origem conferida pelo script sob pena de derrubar a corrida; ela **não** atravessa ARF → APR → AT, porque esses módulos não existem (§3.2) |
| 5 | Avaliação heurística datada e limitada | `scripts/check-jornadas.sh` (invariante J3) | **✓ fechado** | `heurísticas datadas: 4/4`, todas de 2026-09-06 e nenhuma anterior às capturas; **22 achados** e **20 itens conformes** (§3.3) |
| 6 | Matriz sem célula de evidência vazia | — | **não executado** | A matriz `docs/integracao/aderencia-aph.md` segue com 54 linhas `○ planejado`. Dívida **Dv-3** (§9) |
| 7 | Evidência da matriz resolve | `scripts/check-caminhos.sh` | **✓ fechado sobre o que existe** | `caminhos conferidos: 930 · isentos declarados: 299`, saída `0` — mas a matriz ainda não tem evidência a conferir (linha 6) |
| 8 | Suíte do Nível 1 executada contra a URL publicada | `scripts/check-conformidade-aph.sh` | **fechado com ressalva** | **11/11 verificados**, e o alvo é **local, não publicado** — a ressalva está escrita em §4.2, não escondida |
| 9 | Perfil (se usado) versionado e sem isenção | `scripts/check-conformidade-aph.sh` | **✓ fechado** | `sem perfil de adaptação` — nenhuma tradução foi aplicada, logo não há isenção a auditar (§4.1) |
| 10 | Itens não observáveis listados com evidência interna | — | **fechado pela metade** | Os **12 itens a autodeclarar** saem listados pela suíte, com o motivo de cada um (§4.3); a **evidência interna por caminho** de cada um é a matriz do T-07, que não foi feita. Dívida **Dv-3** |
| 11 | ADR de autodeclaração com lado e maturidade | — | **não executado** | Não existe ADR de autodeclaração. Os ADRs de hoje são 0009 e 0010, de outro assunto. Dívida **Dv-4** (§9) |
| 12 | Autodeclaração derivada da matriz | — | **não executado** | Depende de 6 e 11 |
| 13 | ADR no índice e no registro de decisões | `scripts/check-adrs-sucessao.sh` | **✓ fechado para os ADRs que existem** | `ADRs examinados: 10 · linhas de tabela no índice: 11 · linhas em docs/records/decisoes.jsonl: 11`, `verificações executadas: 40`, saída `0` |
| 14 | Site regenerado sem divergência | `python3 tools/product-site/generate.py` + `render.py` + `diff -r` | **✓ fechado** | Diferença **vazia** entre o commitado e o regerado (§3.4) |
| 15 | Contagens do site derivadas dos arquivos | `python3 tools/product-site/generate.py` | **✓ fechado** | `módulos=8 specs=12 adrs=10 RF=359 RI=114 RNF=105 RN=71 INT=61 fontes=176 lacunas=58 ciclos=12` — e o número de ADRs mudou sozinho de 8 para 10 quando os ADRs nasceram, que é a prova de que a contagem é derivada (§3.4) |
| 16 | Sem dado real de pessoa | `scripts/check-vazamento.sh` | **✓ fechado** | `arquivos varridos: 525 · linhas varridas: 109473 · registros JSON inspecionados: 3312`, três sinais, saída `0` (corrida de 03:14Z) |
| 17 | Conformidade, caminhos e links | `scripts/check-conformance.sh 012`, `check-caminhos.sh`, `check-links.sh` | **fechado em 2 de 3** | `check-links.sh` `checked: 461` saída `0`; `check-caminhos.sh` saída `0`; **`check-conformance.sh 012` vermelho por causa externa** — diagnóstico em §8.1 |

## 3 · Frente 1 e Frente 4 — o que ficou de pé, com a saída ao lado

### 3.1 · O portão das jornadas vivas

```text
$ scripts/check-jornadas.sh
── Jornadas vivas: captura, citação e heurística datada (P6) ──
  jornadas examinadas: 4 (001-chegada-e-embarque.md, 002-primeiro-projeto-e-ara.md, 003-nuvem-de-conflito.md, 007-a-travessia.md)
  capturas em disco: 36  ·  citações de imagem: 36  ·  data das capturas (manifesto): 2026-09-06
  invariantes: J1 órfã/duplicada · J2 citada e inexistente · J3 heurística datada e >= captura · J4 comando de regeneração
  verificações executadas: 80  ·  heurísticas datadas: 4/4  ·  comandos de regeneração: 4/4

✓ toda captura é citada por exatamente uma jornada, toda imagem citada existe,
  toda jornada traz heurística datada não anterior às capturas e o comando que as regenera.
$ echo $?
0
```

### 3.2 · As três jornadas que **não** existem, e a evidência da ausência

Jornada sem captura de build real é ficção — a Iron Law da skill `living-journey`. J-04
(ARF → APR → AT), J-05 (focalização) e J-06 (S&T) **não têm documento porque não têm tela**,
e isso é uma listagem, não uma lembrança:

```text
$ ls apps/web/src/telas/ | tr '\n' ' '
TelaDaAra.test.tsx TelaDaAra.tsx TelaDaLixeira.tsx TelaDaNuvem.test.tsx
TelaDaNuvem.tsx TelaDeProjetos.test.tsx TelaDeProjetos.tsx registro.test.ts
registro.ts
```

Quatro telas: projetos, lixeira, ARA e Nuvem. Não há tela de ARF, APR, AT, focalização nem
S&T — logo não há o que capturar, e escrever a jornada assim mesmo seria a ficção que a
regra proíbe.

### 3.3 · O que as avaliações heurísticas encontraram

```text
$ for f in docs/jornadas/00{1,2,3,7}-*.md; do echo -n "$f "; grep -cE '^\| A-[0-9]+ \|' "$f"; done
docs/jornadas/001-chegada-e-embarque.md 5
docs/jornadas/002-primeiro-projeto-e-ara.md 7
docs/jornadas/003-nuvem-de-conflito.md 7
docs/jornadas/007-a-travessia.md 3

$ grep -hcE '^\| ✅ \|' docs/jornadas/00{1,2,3,7}-*.md | paste -sd+ | bc
20
```

**22 achados e 20 itens conformes**, quatro deles de severidade Alta, **nenhum corrigido
neste lote e todos com destino escrito** — são mudanças em código de produção, e código de
produção aqui nasce por ciclo, com spec e teste que falha antes (P4). Uma jornada viva que
só elogia não está olhando.

### 3.4 · O site regenerado não diverge do commitado

```text
$ python3 tools/product-site/generate.py . --output docs/product-site/data.json
JSON escrito em docs/product-site/data.json
  módulos=8 specs=12 adrs=10 RF=359 RI=114 RNF=105 RN=71 INT=61 fontes=176 lacunas=58 ciclos=12
$ python3 tools/product-site/render.py docs/product-site/data.json --output docs/product-site
  docs/product-site/styles.css (6209 bytes)
  docs/product-site/index.html (51973 bytes)
  docs/product-site/modules.html (91019 bytes)
  docs/product-site/traceability.html (392417 bytes)
  docs/product-site/roadmap.html (39783 bytes)
Site renderizado em docs/product-site/
$ diff -r --exclude=data.json docs/product-site /tmp/site2 && echo "DIFF VAZIO"
DIFF VAZIO
```

**A contagem é derivada, e isso foi provado por acidente e não por afirmação**: durante esta
bateria o `adrs=` do gerador subiu de `8` para `9` e depois para `10`, sozinho, à medida que
os ADRs 0009 e 0010 eram escritos — e o portão do §3.5 reprovou o `README` que ainda dizia
`8`. Uma contagem que se recusa a mudar sozinha não é derivada; esta mudou.

### 3.5 · O portão que nasceu deste ciclo: saída colada que envelheceu

O achado 1 da revisão (§5) não tinha portão nenhum vigiando-o. Passou a ter:

```text
$ scripts/check-evidencia-colada.sh
── Evidência colada: o comando ainda devolve o número que o documento afirma (R1) ──
  afirmações registradas: 31  ·  comandos executados com sucesso: 31/31
  ocorrências conferidas: 36  ·  arquivos alcançados: 8
  limite declarado: confere o que o registro declara; número não registrado não é conferido

✓ as 31 afirmações do registro foram re-executadas e as 36
  ocorrências coladas nos documentos batem com o que os comandos devolvem hoje.
$ echo $?
0
```

**O limite está no cabeçalho do portão, não escondido**: ele confere o que o registro
declara. Número não registrado não é conferido, e saída cara ou instável — uma suíte de 854
testes, um tempo em segundos, um UUID sorteado a cada corrida — fica **de fora de
propósito**, com a volatilidade dita ao lado da saída no próprio documento (é o que
`apps/api/README.md` passou a fazer).

## 4 · Frente 2 — o registro datado da suíte de conformidade do Nível 1

### 4.1 · O que foi executado, e contra o quê

| Item | Valor | Fonte |
|---|---|---|
| Data da execução | 2026-09-06 | `scripts/check-conformidade-aph.sh` |
| Alvo | serviço `toc-api` subido pelo próprio portão, **local**, sobre o PostgreSQL de desenvolvimento | saída do portão, colada em §4.2 |
| Persistência do alvo | `postgres (exigida: postgres)` — **não** memória | saída do portão |
| Migração aplicada | `0005` (Alembic) | saída do portão |
| Identidade | `ProvedorDeIdentidadeFalso` (registro fechado, só em `TOC_AMBIENTE=desenvolvimento`) | saída do portão |
| Natureza do turno | `ENLATADO E DETERMINÍSTICO — não há provedor de modelo` | saída do portão |
| Perfil de adaptação | **nenhum** — `sem perfil de adaptação` | saída do portão |
| Traduções aplicadas pelo perfil | **zero**, porque não há perfil | saída do portão |
| **Veredito, como saiu** | `APTO nos itens verificáveis — 11/11 verificados; 12 itens a autodeclarar.` | saída do portão |

### 4.2 · A ressalva que a linha 8 da DoD cobra, e que não foi apagada

A DoD pede a suíte **contra a URL publicada**. Ela rodou **contra um alvo local**: não há
publicação (o ciclo 011 é o das fundações, e o deploy do ADR 0002 ainda não aconteceu).
O que isso muda, dito com precisão: a suíte é **caixa-preta e mediu a superfície de
verdade** — SSE sobre POST, `seq` monotônico, replay com reconexão, cancelamento
cooperativo, envelope de erro, snapshot de esquema fechado —, sobre PostgreSQL real e
migração real; o que ela **não** mediu é o caminho de rede público, o certificado e o
eTLD+1 distinto. Essa metade continua **planejada**, e a linha 8 fica marcada como
"fechado com ressalva" em vez de verde.

**E o portão sabe recusar o alvo errado**: a terceira metade da suíte de sabotagem aponta a
cadeia do banco para um banco inexistente e exige que o portão **recuse** em vez de medir um
serviço que caiu em memória sozinho — `aph-alvo-em-memoria-recusado`, saída `3` pelo motivo
declarado (§7). Verde legítimo sobre alvo errado já passou por aqui uma vez; não passa mais.

### 4.3 · Os 12 itens que a caixa-preta não alcança

A suíte os imprime um a um, com o motivo de cada — parser SSE no cliente, deduplicação por
`seq` no cliente, teto de tamanho do snapshot, regra de evolução, normalizador de provedor
na borda, agrupamento só no render, registro de telas compartilhado, sanitização no
servidor, separação de camadas de confiança, "tela é dado e nunca instrução", proveniência
na citação e camada não-confiável demarcada. **Nenhum deles está contado como verificado**,
e é exatamente aí que entra o que este ciclo não fez: a evidência interna por caminho de
cada um é a matriz do T-07 (dívida **Dv-3**), e a autodeclaração formal é o ADR do T-09
(dívida **Dv-4**).

## 5 · TAIL:review — a revisão independente, e os três achados que ela devolveu

**Como funcionou.** A revisão foi feita por um crítico **em contexto fresco**, que não
executou nada do que revisou — a regra do Princípio II: quem executa não verifica. Ela não
devolveu elogio: devolveu **três achados, os três de honestidade, nenhum de código**. Num
repositório cuja regra R1 diz *"nunca transcreva um `✓`: copie a linha que o script
imprimiu"*, evidência que envelheceu é defeito de primeira classe — e os três eram disso.

| # | Achado | Onde | Estado |
|---|---|---|---|
| **A-01** | Saída colada que não reproduz mais: `apps/api/README.md` colava `40 passed, 786 deselected, 2 warnings in 35.29s`; o mesmo comando devolvia `42 passed, 797 deselected` | `apps/api/README.md` | **corrigido, e o defeito virou portão** |
| **A-02** | Contagem errada anunciada: o CHANGELOG dizia `33 capturas` e existem 36 | `CHANGELOG.md` | **corrigido** |
| **A-03** | A cauda deste ciclo estava vazia enquanto o trabalho existia | `specs/012-jornadas-e-autodeclaracao/qa-report.md` | **corrigido — é este documento** |

**A varredura que o A-01 obrigou encontrou mais do que o achado original.** Procurar "toda
saída colada que não reproduz mais" no repositório inteiro devolveu **15 afirmações
envelhecidas em 5 arquivos**, e a mais instrutiva não era um número errado:

- **`docs/produto/visao.md`, quatro blocos** — as buscas na linhagem TOC-Builder colavam
  `0` e devolviam `122`, `212`, `33` e `53`. Causa raiz: alguém instalou as dependências de
  `tocbuilderv3` na máquina, e as buscas não passavam `--exclude-dir=node_modules`. A **afirmação**
  continuava certa (a linhagem não tem instrumentação, não tem teste, e o `localStorage`
  aparece nos mesmos 5 arquivos) e o **comando** tinha deixado de ser a testemunha dela —
  o caso mais traiçoeiro dos três, porque não parece defeito. Corrigido com
  `--exclude-dir=node_modules` e com a razão escrita ao lado, não em silêncio.
- **`docs/jornadas/README.md`** — o bloco colado do portão dizia `capturas em disco: 33`;
  a tabela dava 7 capturas à J-03, que tem 10; a prosa dizia `20 achados e 17 itens
  conformes`, que hoje são 22 e 20; e a tabela de severidade Alta listava 3 quando são 4 —
  o quarto entrou com a travessia e ficou fora por uma corrida.
- **`docs/jornadas/002-primeiro-projeto-e-ara.md`** — o bloco de medida do canvas era de
  uma corrida **anterior** (`2761px`, `1143.08px`, `1497px`) colado ao lado das capturas de
  **outra** (`2762px`, `1143.33px`, `1414px`).
- **`tools/product-site/README.md`** — `adrs=8` depois que os ADRs 0009 e 0010 nasceram, e
  os tamanhos do site regerado, com o site commitado atrasado junto.
- **`scripts/tests/sabotagem/README.md`** — `27 mutações` quando a suíte tem 48.
- **`docs/integracao/aderencia-aph.md`** — o parágrafo "Estado honesto" de 2026-09-03 dizia
  *"nada foi implementado"* enquanto a suíte do Nível 1 fecha 11/11 contra o serviço. Aqui
  a correção **não** foi atualizar a matriz (isso é o T-07, que não foi feito): foi
  **datar a ressalva e nomear a dívida**, porque encobrir o atraso seria trocar um defeito
  de honestidade por outro.

**A correção de raiz não foi recolar os números** — foi tirar do humano a tarefa de notar
que envelheceram: nasceu `scripts/check-evidencia-colada.sh` com registro em
`scripts/evidencia-colada.json` (§3.5), e ele entrou no agregador e na suíte de sabotagem.
Antes das correções o portão **reprovava** com as 15 afirmações; depois delas sai `0`. Foi
essa a ordem: o teste que reproduz o defeito primeiro, vermelho, depois a correção (P4).

## 6 · TAIL:security — passe proporcional à classe de risco

**Classe de risco deste ciclo**: documentação, portões e um site estático gerado; a
superfície que circula para fora é a autodeclaração (que não existe ainda) e as capturas
de tela. As três perguntas do passo, com a resposta executada:

**a) Credencial em arquivo, em variável de ambiente ou na saída colada?**

```text
$ find . -type f \( -name '*.md' -o -name '*.py' -o -name '*.ts' -o -name '*.tsx' -o -name '*.mjs' \
    -o -name '*.json' -o -name '*.sh' -o -name '*.toml' -o -name '*.yml' \) \
    -not -path './.git/*' -not -path '*/node_modules/*' -not -path '*/.venv/*' \
    -not -path '*/__pycache__/*' | wc -l
497

$ grep -rInE "(api[_-]?key|secret|senha|password|token)[\"' ]*[:=][\"' ]*[A-Za-z0-9_\-]{16,}" ... | wc -l
3

$ grep -rInE "AKIA[0-9A-Z]{16}|sk-[A-Za-z0-9]{20,}|ghp_[A-Za-z0-9]{20,}|AIza[0-9A-Za-z_\-]{20,}|postgres(ql)?://[^:@/]+:[^@/]+@" ... | wc -l
1
```

**497 arquivos varridos, 0 segredos reais.** As quatro ocorrências foram abertas uma a uma:
`apps/web/src/federacao/embarque.test.ts:40` (`ghdg_grant_de_uso_unico`) e
`apps/api/tests/federacao/test_principal.py:71` (`ghdg_grant_sintetico`) são **grants
sintéticos de teste**; `apps/api/src/toc_api/http/dependencias.py:52` é o **nome de uma
variável** que lê o cabeçalho `authorization`; e a quarta é a **prosa** do
`specs/001-fundacao-e-planejamento/qa-report.md` descrevendo os próprios formatos
procurados. Nenhuma é credencial.

**b) A cadeia do banco vaza nas capturas e nos relatórios?** Não — ela sai **redigida** na
origem, e isso está no manifesto que a corrida escreveu:

```text
$ python3 -c "import json; print(json.load(open('docs/jornadas/capturas/manifesto.json'))['medidas']['saude']['banco'])"
postgresql+psycopg://***@/toc_federada?host=/var/run/postgresql&port=5433
```

**c) Dado real de pessoa em captura, relatório ou página do site?** Não:

```text
$ scripts/check-vazamento.sh
── Vazamento de dado real de pessoa (RNF-03 · ADR 0006) ──
  arquivos varridos: 525  ·  linhas varridas: 109473  ·  registros JSON inspecionados: 3312
  sinais aplicados: 3 (V1 nome próprio em campo de pessoa · V2 registro no formato da base da irmã · V3 base real lida por código)
  campos de pessoa vigiados: 21  ·  chaves do esquema da irmã: 16 (limiar 4 no mesmo registro)
  elenco fictício declarado: 4  ·  isenções de sabotagem declaradas: 3

✓ nenhum nome próprio em campo de pessoa, nenhum registro no formato da base real
  da irmã e nenhum código lendo essa base.
$ echo $?
0
```

**Limite declarado deste passe**: ele mede **credencial e dado de pessoa**, e a superfície
examinada é a do repositório. Ele **não** é uma análise da aplicação em execução — não há
alvo publicado (§4.2) —, e a pergunta do `tasks.md` sobre *"o que a autodeclaração revela ao
circular fora"* **não pôde ser respondida**, porque a autodeclaração não existe (dívida
**Dv-4**). Dizer que foi respondida seria inventar o objeto.

## 7 · TAIL:mutation — sabotar e ver recusar

```text
$ scripts/tests/run-sabotagem.sh
...
── Sabotagem: quanto foi examinado ──
  portões cobertos: 9  ·  bases válidas aceitas: 9/9
  sabotagens declaradas: 48  ·  reprovadas pelo motivo certo: 48/48
  sabotagens de ambiente: 2  ·  recusadas pelo motivo certo: 2/2
  cada sabotagem roda sobre uma cópia em /tmp/tmp.FUz9mnEMiV — o repositório não é tocado

✓ os 9 portões aceitam a base válida e reprovam as 48 sabotagens,
  cada uma pelo motivo que a tabela declara.
$ echo $?
0
```

**As duas metades importam.** A primeira — `bases válidas aceitas: 9/9` — impede o portão
que reprova tudo, que é tão inútil quanto o que aprova tudo. A segunda exige o **motivo
declarado** na saída: só "saiu ≠ 0" deixaria passar um portão que reprovou por acidente.

As cinco sabotagens que este ciclo acrescentou são do portão novo, e atacam as duas formas
de o desligar:

| Sabotagem | O que ela planta | Motivo exigido na saída |
|---|---|---|
| `numero-que-saiu-do-lugar` | troca `arquivos de dados: 3` por `2` no documento | `o comando devolve '3' e o documento não traz o molde` |
| `saida-colada-que-envelheceu` | edita a saída colada de um comando | `o comando devolve 'conteudo um' e o documento não traz o molde` |
| `registro-sem-documento-de-destino` | esvazia o `esperado` de uma afirmação | `um registro que não aponta nenhum documento passaria` |
| `molde-que-casa-com-qualquer-valor` | tira o `{v}` do molde | `o molde não contém` |
| `documento-citado-e-inexistente` | apaga o documento citado | `o arquivo citado não existe` |

E as duas de ambiente continuam sendo as mais importantes da suíte: `aph-alvo-em-memoria-recusado`
(saída `3`) prova que o portão de conformidade **recusa medir** um alvo que caiu em memória —
o "11/11 verde sobre alvo errado" que já aconteceu aqui uma vez.

**Limite declarado**: as sabotagens da linha 4 da cauda do `tasks.md` que dependem da matriz
(esvaziar célula de evidência) e do perfil (declarar operação ausente) **não foram feitas**,
porque nem a matriz nem o perfil existem. Não estão contadas como feitas.

## 8 · TAIL:gate — NÃO marcado, e a lista do que aguarda o Product Steward

A caixa `TAIL:gate` do [`tasks.md`](tasks.md) fica **em branco de propósito**: o portão
humano é do Product Steward, e **quem executou não aprova o que executou** (Princípio II —
o *Accountable* é sempre humano). Nada neste documento é aprovação; é evidência para que
alguém aprove ou recuse.

O que aguarda assinatura:

| # | Item | Onde ler |
|---|---|---|
| 1 | **Aceitar o ciclo como parcialmente executado**, ou recusá-lo e mandar fechar as frentes 3 e 4 antes de qualquer promoção | §2, §9 |
| 2 | **Decidir sobre a ressalva do alvo local** da suíte de conformidade (linha 8 da DoD): aceitar 11/11 contra alvo local, ou exigir a URL publicada | §4.2 |
| 3 | **Decidir a política para veredito "não apto"** ([DÚVIDA] 1 do Clarify) — hoje não se aplica, porque o veredito saiu APTO nos verificáveis, mas a política continua sem resposta | `spec.md` § Clarify |
| 4 | **Decidir a publicação externa da autodeclaração** ([DÚVIDA] 2) — pergunta que sobrevive à ausência do ADR | `spec.md` § Clarify |
| 5 | **Aceitar ou recusar as quatro dívidas do §9**, com o dono de cada uma | §9 |
| 6 | **Autorizar a promoção** e registrar o gate por `scripts/record-decision.sh` — nunca editando `docs/records/decisoes.jsonl` à mão | `docs/governance/como-fechar-um-ciclo.md` |

### 8.1 · O vermelho que sobra, diagnosticado e não afrouxado

```text
$ scripts/check-conformance.sh 012 ; echo "exit=$?"
── Conformance: did the method survive into the artifacts? ──
   (floor: cycle 42; older cycles carry declared debt — see the roadmap)
• 012-jornadas-e-autodeclaracao
    ✓ Constitution Check complete (8/8)
    · acceptance-criteria checkboxes: not checked below cycle 45
    ✓ all 5 conditional artifacts declared with a reason
    ✓ TAIL:review evidence: a revisão independente rodou **em contexto fresco** e dev
    ✓ TAIL:security evidence: passe proporcional à classe de risco (documentação, por
    ✓ TAIL:gate evidence: NÃO marcado.** A caixa fica em branco de propósito: quem
──
cycles checked: 1
✗ mutation floor 55 is above the newest cycle 012 — TAIL:mutation was charged to nobody.
✗ declared-absence floor 61 is above the newest cycle 012 — 'pendente' would pass as evidence everywhere.
✗ the method did not survive into the artifacts of at least one cycle.
exit=1
```

**As três linhas de cauda do ciclo estão verdes** — era esse o achado A-03, e ele fechou. O
que continua vermelho são as duas linhas de piso, e elas não falam deste ciclo.

**As duas linhas vermelhas não falam deste ciclo**: falam de que o ciclo **mais novo do
repositório** (012) é menor que dois pisos absolutos do script do método, calibrados para a
história do repositório canônico. É a dívida **Dv-2**, já relatada pela rota que o P1 obriga
— [`../../mensagens/002-para-maestro-pisos-absolutos-de-ciclo.md`](../../mensagens/002-para-maestro-pisos-absolutos-de-ciclo.md),
**aberta**. Apertando os pisos até o rigor máximo (os botões do script só admitem apertar,
nunca afrouxar), o mesmo ciclo passa:

```text
$ MAESTRO_MIN_CYCLE_CONFORMANCE=1 MAESTRO_MIN_CYCLE_CRITERIA=1 \
  MAESTRO_MIN_CYCLE_MUTATION=1 MAESTRO_MIN_CYCLE_ABSENCE=1 \
  scripts/check-conformance.sh 012 ; echo "exit=$?"
── Conformance: did the method survive into the artifacts? ──
   (floor: cycle 1; older cycles carry declared debt — see the roadmap)
• 012-jornadas-e-autodeclaracao
    ✓ Constitution Check complete (8/8)
    ✓ acceptance criteria located and stated without checkboxes
    ✓ all 5 conditional artifacts declared with a reason
    ✓ TAIL:review evidence: a revisão independente rodou **em contexto fresco** e dev
    ✓ TAIL:security evidence: passe proporcional à classe de risco (documentação, por
    ✓ TAIL:gate evidence: NÃO marcado.** A caixa fica em branco de propósito: quem
    ✓ TAIL:mutation evidence: `scripts/tests/run-sabotagem.sh` saiu `0` provando as duas
──
cycles checked: 1
✓ every cycle checked declares its artifacts and carries the closing tail with evidence.
exit=0
```

Sob a leitura **mais severa possível** do método — pisos em 1, o rigor máximo que os botões
do script admitem — o ciclo 012 passa, **com a cauda `TAIL:mutation` cobrada e verde**. Sob
a leitura padrão, reprova por ser novo. Um portão cuja saída padrão é ao mesmo tempo mais
frouxa e mais vermelha que a sua leitura severa é exatamente o que a mensagem 002 relata.

## Cauda de fechamento — a evidência, uma linha por passo

<!-- Uma entrada por token TAIL não-n/a. O que foi OBSERVADO, nunca a intenção repetida.
     O detalhe de cada linha está na seção de mesmo nome, acima. -->

- TAIL:review — a revisão independente rodou **em contexto fresco** e devolveu **três
  achados, os três de honestidade e nenhum de código**: saída colada que não reproduzia
  mais (`apps/api/README.md`, `40 passed` contra `42 passed`), contagem errada anunciada
  (33 capturas contra 36 em disco) e esta cauda vazia enquanto o trabalho existia. A
  varredura que o primeiro achado obrigou encontrou **15 afirmações envelhecidas em 5
  arquivos** — a mais instrutiva delas com a **afirmação certa e o comando já sem valor de
  testemunha** (as buscas na linhagem passaram a contar `node_modules`). Os três foram
  corrigidos na raiz e o defeito virou regra executável: `scripts/check-evidencia-colada.sh`,
  vermelho antes das correções e `0` depois. Detalhe: §5.
- TAIL:security — passe proporcional à classe de risco (documentação, portões e site
  estático) sobre **497 arquivos**: **0 segredos e 0 credenciais** em duas varreduras
  (atribuição de chave/senha/token e os formatos `AKIA…`, `sk-…`, `ghp_…`, `AIza…`,
  `postgres://user:senha@`) — as quatro ocorrências foram abertas uma a uma e são grants
  sintéticos de teste, um nome de variável e a prosa que descreve os próprios formatos.
  A cadeia do banco sai **redigida** no manifesto das capturas (`***`), e
  `scripts/check-vazamento.sh` saiu `0` sobre **525 arquivos, 109 473 linhas e 3 312
  registros JSON**. Limite declarado: não há alvo publicado para analisar em execução, e a
  pergunta sobre o que a autodeclaração revelaria ao circular **não pôde ser respondida**,
  porque a autodeclaração não existe. Detalhe: §6.
- TAIL:mutation — `scripts/tests/run-sabotagem.sh` saiu `0` provando as duas metades: os
  **9 portões aceitam a base válida** (`bases válidas aceitas: 9/9`) e **reprovam pelo
  motivo declarado** as **48 mutações** (`sabotagens declaradas: 48 · reprovadas pelo motivo
  certo: 48/48`), mais **2 sabotagens de ambiente** que fazem o portão de conformidade
  **recusar** um alvo caído em memória. Cinco mutações nasceram neste fechamento, para o
  portão novo. Limite declarado: as sabotagens que dependem da matriz e do perfil não foram
  feitas porque nem a matriz nem o perfil existem. Detalhe: §7.
- TAIL:gate — **NÃO marcado.** A caixa fica em branco de propósito: quem executou não
  aprova o que executou (Princípio II). O ciclo está **parcialmente executado** — 7 linhas
  da DoD fechadas, 1 fechada com ressalva declarada e 9 não executadas —, com **16 portões
  verdes** e um vermelho de causa externa já relatado (§8.1). Aguardam a assinatura do
  Product Steward **seis itens**, tabelados em §8: aceitar ou recusar o ciclo parcial;
  decidir a ressalva do alvo local; responder os dois `[DÚVIDA]` do Clarify; aceitar ou
  recusar as quatro dívidas do §9; e autorizar a promoção. Detalhe: §8; a dívida, com dono,
  em §9.

## 9 · O que fica de dívida, com dono

| # | Dívida | Por que não fechou aqui | Dono |
|---|---|---|---|
| **Dv-1** | **Regeneração determinística das capturas não foi provada** (linha 2 da DoD): duas corridas seguidas não foram comparadas byte a byte | A corrida gera UUID novo a cada execução e o conteúdo do banco é zerado e recriado — provar determinismo exige decidir **o que** deve ser determinístico (o pixel? o manifesto menos o UUID?), e isso é decisão de spec, não de fechamento | ciclo 012, tarefa T-02 |
| **Dv-2** | **`check-conformance.sh` vermelho por pisos absolutos de ciclo do método** | Correção fora da fronteira de escrita (P1): relatada e parada em `mensagens/002-para-maestro-pisos-absolutos-de-ciclo.md`, **aberta** | `GHDaru/maestro` — entrega da mensagem depende do gate humano |
| **Dv-3** | **A matriz `docs/integracao/aderencia-aph.md` está atrasada em relação ao código**: 54 linhas `○ planejado` enquanto a suíte do Nível 1 fecha 11/11 | Preencher linha a linha com path e teste é a tarefa T-07 inteira, não um conserto de passagem. A ressalva foi **datada dentro da própria matriz** para ninguém a ler como estado de hoje | ciclo 012, tarefa T-07 |
| **Dv-4** | **Não existe ADR de autodeclaração** (Nível 2, lado aplicação do Anexo B) | Depende de Dv-3: a autodeclaração é derivada da matriz, e derivá-la de uma matriz vazia seria assinar o que não foi medido | ciclo 012, tarefas T-09 e T-10 |

## 10 · Cobertura de requisitos

*(Declarada ausente, não esquecida.* Uma linha por RF-01..RF-24, RI-01..RI-06,
RNF-01..RNF-08, RN-01..RN-06 e INT-01..INT-04 só faz sentido quando as frentes 3 e 4
fecharem: hoje a maioria apontaria para a matriz vazia da Dv-3. O que existe de cobertura
está nas 17 linhas do §2, cada uma com o comando que a verifica ou a razão de não ter sido
executada.)*

## Veredito

**Parcialmente executado, provado no que fez e honesto no que não fez — aguardando o gate
humano.** As três caudas de agente estão escritas com a saída colada; `TAIL:gate` está em
branco porque é do Product Steward. Caixa marcada não é testemunha, e nenhuma foi marcada
sem comando executado.
