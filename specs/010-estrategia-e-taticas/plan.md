# Plan 010 — Estratégia & Táticas (ciclo planejado)

> Siglas: TOC — Teoria das Restrições · S&T — Estratégia & Táticas (*Strategy &
> Tactics*) · APR — Árvore de Pré-Requisitos · AT — Árvore de Transição · APH —
> Aplicação ↔ Harness · ADR — Architecture Decision Record (Registro de Decisão
> Arquitetural) · DoD — Definition of Done (Definição de Pronto) · DoR — Definition of
> Ready (Definição de Prontidão) · TDD — Test-Driven Development (desenvolvimento
> guiado por teste) · DDD — Domain-Driven Design (Design Orientado a Domínio) · IA —
> inteligência artificial · OTel — OpenTelemetry · CI — integração contínua · UI —
> interface de usuário · UX — experiência de usuário · YAGNI — You Aren't Gonna Need
> It · i18n — internacionalização · SDK — Software Development Kit · VCD — Value
> Creating Deliverable (entregável gerador de valor, jargão da linhagem)

- **Spec**: `spec.md` (Rascunho — aprovação no gate humano que abre o ciclo) · **Raia**:
  plena · **Data**: 2026-09-03
- **Estado**: **planejado no ciclo 001, não executado.** Este plano é escrito antes de o
  ciclo abrir; o Constitution Check abaixo avalia o plano como está e será reconferido
  na abertura, com o ciclo 004 promovido (a única dependência técnica — F-12 da spec).

## Constitution Check (governance/principles.md)

| Princípio | Conformidade |
|---|---|
| I. Spec-driven | ✅ A spec 010 precede este plano, e ambos precedem qualquer código do módulo. O escopo é o do round 010 (E5.1–E5.2; vínculo automático com APR/AT fora) — mudança de escopo volta à spec antes de virar código; os 5 `[DÚVIDA]` do Clarify vão ao Product Steward no gate de abertura. |
| II. Human-governed orchestration | ✅ O humano decide no gate: aprovação da spec, respostas do Clarify (categoria não portada, transições de status, raízes, tática obrigatória, ux), corte de apetite. Agentes implementam por fronteira (domínio da árvore, borda, UI); a revisão independente em contexto fresco confere os portões do roadmap — **renumeração da subárvore por teste** e **três premissas persistidas** (`TAIL:review`). |
| III. Reversibility / risk gates | ✅ Tudo é reversível por desenho herdado do M1 (exclusão suave, desfazer de sessão — estendido à exclusão de subárvore inteira, RF-20) mais o próprio conteúdo: exclusão avisa quantificado antes (RN-05), mover pré-visualiza a renumeração (RI-05). Nenhuma ação externa, irreversível ou originada de modelo nasce aqui — o módulo não tem ação de catálogo (INT-04). |
| IV. Test-first / verifiable DoD | ✅ TDD estrito com os testes centrais nascendo primeiro: numeração derivada/determinística (DoD 2), renumeração (DoD 3) e o defeito de exclusão da linhagem como caso de teste (DoD 7 — F-07). DoD com 16 linhas executáveis; `TAIL:mutation` sabota a função de numeração, a invariante de árvore e o recorte da exclusão e os vê recusar. |
| V. Context economy / boundary | ✅ Corte por fronteira dentro do ciclo: a função de numeração é pura e nasce isolada (T-04/T-05); o domínio da árvore não depende de UI nem de banco; a UI vem depois da borda. O módulo inteiro depende só do M1 — é o menor corte de contexto do roadmap, e a posição tardia é escolha de valor, não de dependência (F-12). |
| VI. Living artifacts | ✅ PendenciasDaArvore é consumida pelo painel e pela árvore com função forçante (pendência não computada não aparece e o teste falha); a fixture de 3 níveis é consumida pela jornada viva que o portão exige; o modelo pai+ordem é consumido pelo importador do ciclo 011 (INT-03). Nenhum artefato sem consumidor. |
| VII. Light governance / YAGNI | ✅ Descartados por YAGNI neste ciclo, cada um com porta de volta: a categoria da linhagem ([DÚVIDA] 1 — ADR se confirmado); vínculo com APR/AT (fora pelo round — decisão nova); FSM de status ([DÚVIDA] 2); assistência de IA (decisão nova sob ADR 0007); layout livre `pos_x`/`pos_y` (a árvore desenha-se da estrutura — voltar seria ADR). |
| VIII. Intelligible communication | ✅ Bloco de siglas no topo dos quatro artefatos do ciclo; termos novos (numeração derivada, premissa paralela/de necessidade/de suficiência, árvore estrita) definidos onde nascem, no modelo de domínio da spec. Conferência por amostragem do revisor da cauda. |

### Project Constitution Check (governance/constitution.md — ADR 0001)

| Princípio | Conformidade |
|---|---|
| P1. Fronteira de escrita | ✅ Só este repositório. As fontes da linhagem foram lidas com `arquivo:linha` e saída colada (F-01..F-09 da spec); os defeitos do v3 (número digitado, exclusão destrutiva, aresta livre) são fonte e caso de teste, não conserto — ninguém commita no `tocbuilderv3`. Lacuna externa achada durante o ciclo vira `mensagens/NNN-...`. |
| P2. Federação por contrato (APH) | ✅ Toda mutação é manipulação direta do titular (item 8 — alvo nomeado pelo gesto, valor no controle, reversível na sessão; a exclusão de subárvore confirma com contagem e continua coberta pelo desfazer). Nenhuma ação de catálogo, nenhum verbo originado de modelo neste módulo (INT-04 declara explicitamente) — o P2 é satisfeito por não haver superfície: e a declaração explícita evita o silêncio que o alcance do P2 proíbe. Telas registradas com `ai_visible` campo a campo (INT-02, item 7). |
| P3. Domínio puro (DDD + hexagonal) | ✅ Numeração, renumeração, árvore estrita e pendências são regra de domínio pura sem rede e sem modelo (RNF-01), com `import-linter` falhando o build na violação (RNF-02). O contraexemplo da linhagem — numeração como responsabilidade do usuário em 10 funções CRUD que nunca a validam (F-08) — é exatamente o que o domínio absorve. |
| P4. TDD | ✅ Teste antes em todos os recortes: propriedades da numeração antes da função, renumeração antes do mover, o defeito F-07 reproduzido como teste antes da exclusão existir, ida e volta das premissas antes do repositório. Zero commit de domínio sem teste correspondente. |
| P5. Observabilidade de nascença | ✅ Toda mutação do módulo com traço correlacionado e log estruturado (RNF-03, DoD 11), sobre a fundação OTel do 003 — inclusive `SubarvoreExcluida` com a contagem no traço. |
| P6. Jornada viva com prova visual | ✅ Jornada da S&T sintética da "Instituição Horizonte" com três níveis — o portão do roadmap — cobrindo decomposição, as três premissas nos três papéis, mover com renumeração e status em reunião, com captura gerada por script do build real e avaliação heurística datada, no mesmo pull request (T-11). |
| P7. Segredo nunca no cliente | ✅ Nenhum SDK, chave ou prompt no produto (DoD 12) — este módulo nem superfície de IA tem; o grep de CI herdado continua cobrindo o repositório inteiro. |

**Sem violações.** A ressalva honesta: o P2 é avaliado aqui sobre um módulo sem verbo
de modelo — a conformidade é por ausência declarada (INT-04), não por FSM exercitada;
se o gate decidir incluir assistência, o plano volta ao Constitution Check antes de
qualquer código.

## Artefatos deste ciclo (declare todos os cinco — silêncio não é decisão)

| Artefato | Declaração | Por quê |
|---|---|---|
| `research.md` | `ART:research=no` | Não há incógnita a resolver por experimento: o modelo vem verbatim da linhagem medida (F-03, F-04), os defeitos estão localizados por linha (F-05, F-07, F-08) e a semântica das três premissas é literatura estabelecida do método S&T. As dúvidas restantes são de produto ([DÚVIDA] 1–5), resolvidas por gate humano. |
| `data-model.md` | `ART:data-model=yes` | O módulo estende o modelo persistido do M1 com ArvoreSnT, PassoSnT (pai + ordem — a estrutura que substitui número digitado e aresta livre), PremissasDoPasso e StatusDoPasso. O documento nasce na abertura do ciclo (T-02), como extensão declarada de [`../004-nucleo-de-diagramas/data-model.md`](../004-nucleo-de-diagramas/data-model.md) — os testes de domínio são a forma final e prevalecem sobre o documento. |
| `contracts/` | `ART:contracts=yes` | Um contrato: a extensão REST dos recursos do M1 (árvore, passo, mover, excluir subárvore, premissas, status) — com a ausência de campo de número em toda rota de escrita como cláusula explícita (RF-06, DoD 4). Nenhum contrato de catálogo: INT-04 declara zero ações `toc.*`. |
| `checklist.md` | `ART:checklist=no` | A DoD da spec já é executável (16 linhas com comando); lista adicional duplicaria função (Princípio VI). |
| `ux-design.md` | `ART:ux-design=no` (condicional) | As telas da S&T seguem os padrões já desenhados (árvore/nó/ficha/tabela do M1–M2, painel do M3); se o protótipo do ciclo 002 não tiver coberto a árvore hierárquica com renumeração, um adendo nasce neste ciclo antes da UI ([DÚVIDA] 5 decide no gate — e a declaração vira `yes` na reconferência da abertura). |

## Decisões de arquitetura do módulo

1. **Numeração é projeção, nunca dado.** O passo persiste (pai, ordem); o número
   1/1.1/1.1.2 é função pura dessa estrutura, calculada no domínio e servida como
   campo somente leitura (RN-01). O contraexemplo está medido: no v3 o número era
   texto digitado obrigatório sem validação (F-05) e nenhuma das 10 funções CRUD o
   conferia (F-08) — duas fontes de verdade que divergiam por design. Aqui a
   divergência é impossível por construção, e a exportação nem carrega números
   (RF-21).
2. **Árvore estrita no domínio, sem entidade de aresta.** Pai único + ordem ordinal
   substituem o `edges: AraEdge[]` da linhagem (F-03): ciclo e multi-pai ficam
   irrepresentáveis, e mover-para-a-própria-subárvore é a única recusa necessária
   (RF-08). Menos entidade, mais invariante — o mesmo movimento do M3 com a topologia
   fixa.
3. **O defeito da linhagem vira o teste da exclusão.** A exclusão de subárvore nasce
   do teste que reproduz F-07 (excluir um passo e provar que **todos os demais**
   permanecem byte a byte) mais o aviso quantificado (RN-05). Teste de regressão sobre
   defeito de outro código-fonte: o custo é uma fixture, o benefício é nunca herdar o
   pior defeito da ferramenta por reescrita distraída.
4. **Estratégia e tática como campos; categoria não portada.** O método pede o quê e o
   como por passo; a categoria de 6 valores da linhagem (F-03) só existia porque o
   passo tinha um texto só. Não portar é decisão com porta de volta (campo opcional
   futuro) e vai a ADR se o gate confirmar ([DÚVIDA] 1, L-01).
5. **Premissas com semântica estrutural, pendência sem trava.** Os três campos da
   linhagem (F-03, F-04) ganham papel normativo (RN-02) e leitura dirigida contra pai
   e filhos (RF-13, RI-03) — mas gravação nunca bloqueia (RN-06): o painel diz onde o
   plano ainda é organograma, o grupo decide quando deixar de ser.
6. **Renumeração é local por construção.** Inserir/mover/excluir renumera a subárvore
   afetada e os irmãos seguintes — nunca a árvore inteira (RF-07); a propriedade de
   determinismo (RNF-05) cobre a equivalência com o recálculo total. É o que mantém o
   alvo de desempenho do mover (RNF-04) honesto em árvores grandes.

## Grafo de dependência das tarefas

```
T-01 (DoD fixada + pré-condição: 004 promovido)
  └─► T-02 (data-model + contrato REST — sem campo de número em rota de escrita)
        ├─► T-03 (fixture sintética de 3 níveis + testes vermelhos: numeração,
        │         renumeração, árvore estrita, exclusão F-07, premissas)
        │     └─► T-04 (função pura de numeração + renumeração local, TDD)
        │           └─► T-05 (domínio da árvore: agregado, passos, mover,
        │                     excluir subárvore, premissas, status, TDD)
        └─► T-06 (migrações Alembic + repositórios)
T-04, T-05, T-06 ─► T-07 (casos de uso + adaptadores REST + traço + desfazer
                          estendido à subárvore)
T-07 ─► T-08 (UI: árvore com layout calculado + ficha do passo com leitura
              dirigida das premissas)
T-07 ─► T-09 (UI: vista tabular indentada + painel de acompanhamento + filtros)
T-08, T-09 ─► T-10 (mover por arrastar com pré-visualização de renumeração +
                    exclusão com contagem)          ← primeiro corte de apetite: E5.2
T-10 ─► T-11 (jornada viva de 3 níveis) ─► T-12 (aptidões + qa-report + medições)
T-12 ─► cauda (T-13..T-16: TAIL:review · TAIL:security · TAIL:mutation · TAIL:gate)
```

## Gates (DoR / DoD)

- **DoR — o ciclo não abre sem**: gate humano do 001 fechado; **ciclo 004 promovido**
  (a única dependência técnica — pré-condição do roadmap, F-12); os 5 `[DÚVIDA]` do
  Clarify respondidos — em particular o 1 (categoria), que muda o modelo persistido, e
  o 5 (ux), que muda a declaração de artefatos.
- **DoD — o ciclo não fecha sem**: as 16 linhas da tabela de aceite da spec verdes com
  saída colada no `qa-report.md` (R1) e o tamanho do que cada portão examinou (R2); os
  portões executáveis do roadmap cumpridos — **teste de renumeração da subárvore** e
  **as três premissas persistidas** — com as saídas coladas; o portão de jornada (S&T
  sintética de **três níveis** com captura); cauda completa (`TAIL:review`,
  `TAIL:security`, `TAIL:mutation`, `TAIL:gate`).
- **Corte de apetite** (round 010 — F-11): estourou → sai primeiro o **E5.2** (status
  e acompanhamento — fica a estrutura com premissas); depois o arrastar com
  pré-visualização (fica o mover por comando na ficha); **nunca saem** as três
  premissas por nó — S&T sem premissa é organograma, e a linhagem já as tinha:
  entregar menos que o protótipo seria regressão sobre regressão. Perde escopo, não
  ganha ciclo.

## Riscos e portões

| Risco | Ligado a | Mitigação |
|---|---|---|
| GATE-categoria — o gate decidir portar a categoria da linhagem e mudar o modelo | L-01 | [DÚVIDA] 1 respondido **antes** de T-02 (é DoR); portar é um campo opcional a mais no PassoSnT — custo contido se a resposta vier no gate, caro se vier depois das migrações; por isso está na DoR, não no meio do ciclo. |
| GATE-renumeracao — a renumeração local divergir do recálculo total em casos de borda (mover entre irmãos do mesmo pai, raízes) | RN-01 | Propriedade de equivalência local × total na suíte (RNF-05) desde T-04; `TAIL:mutation` sabota a função de numeração e exige que a propriedade pegue. |
| GATE-importacao — o modelo pai+ordem não reconstruir os exports reais da 4ª geração | L-04 | O risco é do ciclo 011 (INT-03), mas o modelo é deste: T-03 inclui um caso de fixture com a forma do export do v3 (número + arestas) provando a reconstrução num caso feliz e a recusa num ambíguo — o 011 herda o contrato, não a dúvida. |
| GATE-desempenho — renderização da árvore de 100 passos ou o mover de 20 estourarem os alvos | RNF-04 | Layout calculado sem física de canvas (RI-01); renumeração local (decisão 6); medição na jornada viva com valores colados (DoD 13) — se estourar, o corte é de animação/pré-visualização, nunca de invariante. |
| GATE-ux — a árvore hierárquica não ter sido prototipada no 002 | [DÚVIDA] 5 | Adendo de ux-design nasce antes da UI (a declaração `ART:ux-design` vira `yes` na reconferência); os padrões de nó/ficha/tabela do M1–M3 reduzem o desenho novo à árvore e à pré-visualização de renumeração. |
| GATE-apetite — E5.1 + E5.2 com TDD estourarem o ciclo | apetite (round 010) | Corte em dois degraus declarado antes de abrir (E5.2 primeiro, arrastar depois, premissas nunca); reavaliação no meio do ciclo contra o grafo de tarefas. |
