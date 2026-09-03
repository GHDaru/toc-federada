# Plan 005 — Árvore da Realidade Atual (ciclo planejado)

> Siglas: TOC — Teoria das Restrições · ARA — Árvore da Realidade Atual · UDE — Efeito
> Indesejável (*Undesirable Effect*) · APH — Aplicação ↔ Harness · ADR — Architecture
> Decision Record (Registro de Decisão Arquitetural) · DoD — Definition of Done
> (Definição de Pronto) · DoR — Definition of Ready (Definição de Prontidão) · TDD —
> Test-Driven Development (desenvolvimento guiado por teste) · DDD — Domain-Driven
> Design (Design Orientado a Domínio) · IA — inteligência artificial · FSM — máquina de
> estados finitos · OTel — OpenTelemetry · CI — integração contínua · UI — interface de
> usuário · YAGNI — You Aren't Gonna Need It · CLR — Categorias de Reserva Legítima ·
> i18n — internacionalização

- **Spec**: `spec.md` (Rascunho — aprovação no gate humano que abre o ciclo) · **Raia**:
  plena · **Data**: 2026-09-03
- **Estado**: **planejado no ciclo 001, não executado.** Este plano é escrito antes de o
  ciclo abrir; o Constitution Check abaixo avalia o plano como está e será reconferido
  na abertura, com o M1 (ciclo 004) promovido.

## Constitution Check (governance/principles.md)

| Princípio | Conformidade |
|---|---|
| I. Spec-driven | ✅ A spec 005 precede este plano, e ambos precedem qualquer código do módulo. O escopo é o do round 005 (E2.1 + E2.2; E2.3 declarado como contrato e executado no 006) — mudança de escopo volta à spec antes de virar código; os 5 `[DÚVIDA]` do Clarify vão ao Product Steward no gate de abertura. |
| II. Human-governed orchestration | ✅ O humano decide no gate: aprovação da spec, respostas do Clarify (Validado formal, léxico, conector E, narrativa, reabertura), corte de apetite. Agentes implementam por fronteira (domínio da validação, domínio da árvore, adaptadores, UI); a revisão independente em contexto fresco confere o que o roadmap fixou como portão: **nenhum critério de UDE dependente de prompt** (`TAIL:review`). |
| III. Reversibility / risk gates | ✅ Tudo neste ciclo é reversível por desenho herdado do M1 (exclusão suave, desfazer de sessão, evento compensatório) mais o próprio conteúdo: reabrir um `Validado` é ação nomeada com justificativa (RF-17), parecer nunca se sobrescreve (RF-13), desmarcar UDE arquiva em vez de apagar (RF-05). Nenhuma ação externa ou irreversível nova nasce aqui. |
| IV. Test-first / verifiable DoD | ✅ TDD estrito com um alvo de estreia: a validação formal nasce dos testes dos casos canônicos da linhagem (RF-12, DoD 2) e do corpus sintético (DoD 4) **antes** da primeira heurística. DoD com 14 linhas executáveis; `TAIL:mutation` sabota o léxico e a FSM de status e os vê recusar. |
| V. Context economy / boundary | ✅ Corte por fronteira dentro do ciclo: validação formal (função pura + léxico) é implementável sem tocar árvore; análise estrutural é função sobre grafo sem tocar validação; UI vem depois das duas. E2.3 fica inteiro fora da execução — o corte que mantém o 006 dono da FSM de proposta. |
| VI. Living artifacts | ✅ O corpus sintético de UDEs é consumido pelos testes (função forçante: ampliar léxico exige ampliar corpus, RNF-07); a declaração das ações `toc.*` é consumida pelo ciclo 006 como primeiro cliente do catálogo; a classificação decidível × julgamento é dado versionado lido pela ficha (RF-09). Nenhum artefato sem consumidor. |
| VII. Light governance / YAGNI | ✅ Descartados por YAGNI neste ciclo, cada um com porta de volta: CLR completas (L-02 — ADR novo quando a prática pedir), processamento de linguagem além de heurística lexical (o `indeterminado` honesto cobre o resto), tela de administração de prompts (não é portada — INT-08), modo narrativa no `toc.suggest_udes` ([DÚVIDA] 4). |
| VIII. Intelligible communication | ✅ Bloco de siglas no topo dos quatro artefatos do ciclo; termos novos (exame de elo, conector E, parecer de julgamento, causa raiz candidata) definidos onde nascem, no modelo de domínio da spec. Conferência por amostragem do revisor da cauda. |

### Project Constitution Check (governance/constitution.md — ADR 0001)

| Princípio | Conformidade |
|---|---|
| P1. Fronteira de escrita | ✅ Só este repositório. As fontes da linhagem foram lidas com `arquivo:linha` e saída colada (F-01..F-16 da spec); o defeito D-08 é fonte, não conserto — ninguém commita no `tocbuilderv3`. Lacuna externa achada durante o ciclo vira `mensagens/NNN-...`. |
| P2. Federação por contrato (APH) | ✅ O ciclo **não executa** nenhuma ação de IA (round 005, decisão 4): E2.3 é contrato declarado (INT-02..INT-06, DoD 10 prova que não há rota de execução). O desenho já obedece o item 8: sugestão de modelo nasce `action_proposal` (RF-32..RF-36), veredito decidível nunca é recalculado por modelo (RF-33), capability ausente esconde ação mutadora (RF-37). A FSM de proposta é do 006 — uma só e do servidor. |
| P3. Domínio puro (DDD + hexagonal) | ✅ A regra central do ciclo — os critérios de UDE — é o caso de teste do P3: função pura + léxico como dado, sem rede e sem modelo (RNF-01), `import-linter` falhando o build se o domínio importar framework ou cliente de IA (RNF-02). A análise estrutural idem (RF-26). |
| P4. TDD | ✅ Teste antes em todos os recortes: casos canônicos e corpus antes das heurísticas, FSM de status antes das transições, grafos de fixture antes da análise estrutural. Zero commit de domínio sem teste correspondente. |
| P5. Observabilidade de nascença | ✅ Toda mutação nova com traço correlacionado (RNF-03, DoD 9), sobre a fundação OTel do 003; parecer e proposta aceita carregam o identificador de origem no traço — a linha que liga IA → proposta → efeito, exigida pelo P2, nasce aqui do lado do dado. |
| P6. Jornada viva com prova visual | ✅ Jornada da construção de uma ARA sintética completa da "Instituição Horizonte" — incluindo um UDE reprovado e reformulado, que é o valor da ferramenta — com captura gerada por script do build real e avaliação heurística datada, no mesmo pull request (T-14). |
| P7. Segredo nunca no cliente | ✅ Nenhum SDK, chave ou prompt no produto (DoD 3 e 11); o grep de CI do M1 é estendido aos padrões de prompt (RNF-08). O contraexemplo está medido na fonte: `geminiService.ts:16` (F-08) e os 8 prompts no cliente (F-07). |

**Sem violações.** A ressalva honesta: o P2 é avaliado aqui sobre um desenho que o
ciclo 006 executa — a prova executável da FSM pertence àquele ciclo, e este entrega a
prova negativa (nenhuma rota de execução, DoD 10).

## Artefatos deste ciclo (declare todos os cinco — silêncio não é decisão)

| Artefato | Declaração | Por quê |
|---|---|---|
| `research.md` | `ART:research=no` | Não há incógnita a resolver por experimento: os critérios vêm verbatim da linhagem medida (F-02) e do método TOC; a única dúvida empírica real — a taxa de acerto das heurísticas — tem instrumento próprio (corpus sintético, RNF-07) que é teste, não pesquisa. |
| `data-model.md` | `ART:data-model=yes` | O módulo estende o modelo persistido do M1 com FichaDeUde, ValidacaoFormal, ParecerDeJulgamento, FSM de status, ExameDeElo e ConectorE. O documento nasce na abertura do ciclo (T-02), como extensão declarada de [`../004-nucleo-de-diagramas/data-model.md`](../004-nucleo-de-diagramas/data-model.md) — os testes de domínio são a forma final e prevalecem sobre o documento. |
| `contracts/` | `ART:contracts=yes` | Dois contratos: a extensão REST dos recursos do M1 (ficha, parecer, exame, conector, relatório) e a **declaração das 5 ações `toc.*`** (INT-02..INT-06) no formato do catálogo — o artefato que o ciclo 006 consome como primeiro cliente. Escritos na abertura (T-02/T-03), verificados pela DoD 10. |
| `checklist.md` | `ART:checklist=no` | A DoD da spec já é executável (14 linhas com comando); lista adicional duplicaria função (Princípio VI). |
| `ux-design.md` | `ART:ux-design=no` | As telas da ARA (canvas, ficha, exame, relatório) são entrega do ciclo 002, que este ciclo consome; ajuste que a implementação exigir volta ao `ux-design.md` de lá no mesmo pull request. A bandeja de propostas (tela 6.5) é especificada aqui e desenhada no 006, quando ganhar comportamento. |

## Decisões de arquitetura do módulo

1. **Uma regra, dois lugares de execução, uma fonte.** A validação formal é função pura
   no domínio Python (fonte da verdade, testada); o cliente pode portá-la para resposta
   local em menos de 1 segundo (RI-04, RNF-04), mas a porta é **golden test
   compartilhado**: o mesmo corpus roda contra as duas implementações, e divergência é
   defeito que falha o CI — nunca duas regras.
2. **Léxico como dado versionado por idioma** (RF-11), com o corpus sintético como
   função forçante (RNF-07): heurística nova sem caso novo no corpus não entra. A
   classificação decidível × julgamento (RF-09) vive no mesmo pacote de dados — mover um
   critério de classe é mudança de dado com teste, não de código.
3. **`indeterminado` é veredito de primeira classe** (RF-08): a heurística conservadora
   prefere admitir que não alcança o caso a chutar — e o indeterminado degrada para
   julgamento humano. É o que torna honesta a promessa "decidível".
4. **Extensão por composição, nunca por `if` no núcleo** (herdado do RN-04 do M1): a ARA
   é tipo de projeto com dados anexos (ficha no nó, exame na aresta, conector no
   agregado); o M1 não ganha uma linha de semântica TOC.
5. **Parecer somente-acréscimo com autor tipado** (RF-13, RF-16): quem valida é evento,
   não campo — o contraste direto com a linhagem, onde `validado_por` era string
   devolvida pelo modelo (F-04).
6. **E2.3 declara, 006 executa**: as ações `toc.*` nascem como contrato estático
   (`contracts/`), e a prova deste ciclo é negativa — nenhuma rota de execução (DoD 10).
   O domínio já produz o que as ações vão consumir (relatório estrutural como contexto
   de `toc.analyze_tree`, veredito decidível anexado ao `toc.validate_ude`).
7. **Análise estrutural síncrona e pura**: grafo de 200 nós cabe em memória e em 2
   segundos (RNF-06); nenhuma fila ou worker no v1 — YAGNI com porta de volta declarada
   se a medição da jornada discordar.

## Grafo de dependência das tarefas

```
T-01 (DoD fixada)
  └─► T-02 (data-model + contratos REST estendidos)
        ├─► T-03 (contrato das ações toc.* — declaração)
        ├─► T-04 (corpus sintético de UDEs + casos canônicos, teste vermelho)
        │     └─► T-05 (validação formal: heurísticas + léxico pt/en, TDD)
        │           └─► T-06 (FSM de status + parecer, TDD)
        ├─► T-07 (domínio da árvore: marcador UDE, ficha, exame de elo, conector E)
        │     └─► T-08 (análise estrutural pura, TDD sobre grafos de fixture)
        └─► T-09 (migrações Alembic + repositórios estendidos)
T-05, T-06, T-07, T-09 ─► T-10 (casos de uso + adaptadores REST + traço)
T-10 ─► T-11 (UI: ficha de validação + fluxo reprovar→editar→reavaliar)
T-10 ─► T-12 (UI: canvas ARA — selo UDE, exame de elo, conector E)
T-08, T-10 ─► T-13 (UI: relatório estrutural com foco no canvas)
T-11..T-13 ─► T-14 (jornada viva da ARA sintética) ─► T-15 (aptidões + qa-report)
T-15 ─► cauda (T-16..T-19: TAIL:review · TAIL:security · TAIL:mutation · TAIL:gate)
```

## Gates (DoR / DoD)

- **DoR — o ciclo não abre sem**: gate humano do 001 fechado; ciclo 004 promovido (a
  ARA é feita de nós e arestas do M1 — pré-condição do roadmap); os critérios formais
  transcritos do prompt do v3 para a spec com a separação decidível × julgamento
  marcada requisito a requisito (feito — RN-01..RN-09, RF-09); os 5 `[DÚVIDA]` do
  Clarify respondidos; `ux-design.md` do 002 cobrindo as telas 6.1–6.4.
- **DoD — o ciclo não fecha sem**: as 14 linhas da tabela de aceite da spec verdes com
  saída colada no `qa-report.md` (R1) e o tamanho do que cada portão examinou (R2);
  o portão de revisão do roadmap cumprido — **nenhum critério de UDE dependente de
  prompt** — com o grep da DoD 3 colado; cauda completa (`TAIL:review`, `TAIL:security`,
  `TAIL:mutation`, `TAIL:gate`).
- **Corte de apetite** (round 005 — F-11 da spec): estourou → sai primeiro o relatório
  estrutural (fica a marcação manual de elos); depois o conector E ([DÚVIDA] 3); **nunca
  sai** a validação formal como domínio puro. Perde escopo, não ganha ciclo.

## Riscos e portões

| Risco | Ligado a | Mitigação |
|---|---|---|
| GATE-heuristica — as heurísticas lexicais errarem para o lado errado (veredito falso em vez de `indeterminado`) | L-01 | Corpus sintético com casos adversariais antes do código (T-04); política conservadora testada: na dúvida, `indeterminado` (RF-08); `TAIL:mutation` sabota o léxico e exige que o corpus pegue. |
| GATE-particao — a partição decidível × julgamento (RF-09) ser contestada no gate | L-05 | A partição é dado versionado com teste; mover critério de classe é mudança de dado — o gate humano decide sobre uma tabela, não sobre arquitetura. |
| GATE-clr — o subconjunto de suficiência (exame + conector E + relatório) ficar aquém da prática TOC | L-02 | Escopo declarado na spec (fora: CLR completas) com porta de volta por ADR; a jornada viva com a ARA sintética completa é o teste de suficiência prática antes do gate. |
| GATE-catalogo — o contrato das ações `toc.*` divergir do formato que o 006 fixar | L-03 | Declaração sem execução (DoD 10): divergência custa migração de um arquivo de contrato, não de domínio; o 006 herda esta declaração como rascunho de entrada. |
| GATE-apetite — E2.1 + E2.2 com TDD e léxico bilíngue estourarem o ciclo | L-04 | Corte em dois degraus declarado antes de abrir (relatório primeiro, conector E depois, validação nunca); reavaliação no meio do ciclo contra o grafo de tarefas. |
| GATE-regra-em-prompt — a regra vazar de volta para prompt durante a implementação da assistência | spec RF-33, DoD 3 | Prova executável dupla: grep negativo de prompt no domínio e no cliente (DoD 3), e o desenho do `toc.validate_ude` anexa o veredito da função — o revisor da cauda confere exatamente este portão (roadmap, ciclo 005). |
