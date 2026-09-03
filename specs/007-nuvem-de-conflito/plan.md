# Plan 007 — Nuvem de Conflito (ciclo planejado)

> Siglas: TOC — Teoria das Restrições · NC — Nuvem de Conflito · UDE — Efeito
> Indesejável (*Undesirable Effect*) · ARF — Árvore da Realidade Futura · APH —
> Aplicação ↔ Harness · ADR — Architecture Decision Record (Registro de Decisão
> Arquitetural) · DoD — Definition of Done (Definição de Pronto) · DoR — Definition of
> Ready (Definição de Prontidão) · TDD — Test-Driven Development (desenvolvimento
> guiado por teste) · DDD — Domain-Driven Design (Design Orientado a Domínio) · IA —
> inteligência artificial · FSM — máquina de estados finitos · OTel — OpenTelemetry ·
> CI — integração contínua · UI — interface de usuário · YAGNI — You Aren't Gonna Need
> It · JSON — JavaScript Object Notation · TRIZ — Teoria da Resolução Inventiva de
> Problemas · i18n — internacionalização · SDK — Software Development Kit

- **Spec**: `spec.md` (Rascunho — aprovação no gate humano que abre o ciclo) · **Raia**:
  plena · **Data**: 2026-09-03
- **Estado**: **planejado no ciclo 001, não executado.** Este plano é escrito antes de o
  ciclo abrir; o Constitution Check abaixo avalia o plano como está e será reconferido
  na abertura, com o M1 (ciclo 004) e o catálogo (ciclo 006) promovidos.

## Constitution Check (governance/principles.md)

| Princípio | Conformidade |
|---|---|
| I. Spec-driven | ✅ A spec 007 precede este plano, e ambos precedem qualquer código do módulo. O escopo é o do round 007 (E3.1–E3.4; semear ARF fica no 008) — mudança de escopo volta à spec antes de virar código; os 5 `[DÚVIDA]` do Clarify vão ao Product Steward no gate de abertura. |
| II. Human-governed orchestration | ✅ O humano decide no gate: aprovação da spec, respostas do Clarify (multiplicidade de premissas, granularidade da geração, TRIZ, injeções escolhidas, modo estrito), corte de apetite. Agentes implementam por fronteira (domínio da nuvem, borda da geração, UI); a revisão independente em contexto fresco confere os dois portões que o roadmap fixou: **invariantes por teste de domínio** e **recusar deixa intacto** (`TAIL:review`). |
| III. Reversibility / risk gates | ✅ Tudo neste ciclo é reversível por desenho herdado do M1 (exclusão suave, desfazer de sessão) mais o próprio conteúdo: arquivar premissa arquiva injeções junto com aviso quantificado (RF-15) em vez de apagar, status de injeção volta a `candidata` com justificativa (RN-08), e a geração assistida — a única escrita originada de modelo — nasce proposta recusável com prova de intocabilidade (RF-24). Nenhuma ação externa ou irreversível nova nasce aqui. |
| IV. Test-first / verifiable DoD | ✅ TDD estrito com dois alvos de estreia: as invariantes da topologia fixa (DoD 2) e a recusa intacta byte a byte (DoD 5) nascem como teste antes do agregado e da borda de proposta. DoD com 16 linhas executáveis; `TAIL:mutation` sabota as invariantes, a FSM de injeção e o validador de schema e os vê recusar. |
| V. Context economy / boundary | ✅ Corte por fronteira dentro do ciclo: o domínio da nuvem (topologia, premissas, injeções) é implementável sem catálogo nenhum (RF-28); a borda da geração (schema + proposta) é cliente da FSM do 006 e não a toca; a UI vem depois dos dois. O encadeamento com M2/M4 fica inteiro fora da execução — só os campos de referência nascem (L-05). |
| VI. Living artifacts | ✅ O schema do ResultadoDeGeracao é consumido pelo validador com função forçante (resultado fora do schema é recusado — DoD 6); o corpus de formulação é consumido pelos testes (RNF-08); a declaração das 3 ações `toc.*` é consumida pelo catálogo do 006 como segundo cliente. Nenhum artefato sem consumidor. |
| VII. Light governance / YAGNI | ✅ Descartados por YAGNI neste ciclo, cada um com porta de volta: promoção UDE→NC e semeadura da ARF (round 008 — os campos ficam, a ação não); editor de topologia livre (a NC é topologia fixa por método — voltar seria ADR); classificação TRIZ obrigatória ([DÚVIDA] 3); modo estrito de formulação ([DÚVIDA] 5); versionamento de nuvem além do desfazer de sessão (o histórico é de eventos, não de snapshots). |
| VIII. Intelligible communication | ✅ Bloco de siglas no topo dos quatro artefatos do ciclo; termos novos (aresta de perigo, injeção, separação TRIZ, referência de semeadura) definidos onde nascem, no modelo de domínio da spec. Conferência por amostragem do revisor da cauda. |

### Project Constitution Check (governance/constitution.md — ADR 0001)

| Princípio | Conformidade |
|---|---|
| P1. Fronteira de escrita | ✅ Só este repositório. As fontes da linhagem foram lidas com `arquivo:linha` e saída colada (F-01..F-09 da spec); os defeitos do v3 (parser por regex, prompt no cliente, injeções invisíveis) são fonte, não conserto — ninguém commita no `tocbuilderv3`. Lacuna externa achada durante o ciclo vira `mensagens/NNN-...`. |
| P2. Federação por contrato (APH) | ✅ O desenho obedece o alcance declarado do P2: edição de entidade é manipulação direta do titular (item 8 — aplica na hora sob os três testes, RF-05); tudo que vem de modelo nasce `action_proposal` na FSM **do servidor do 006** (RF-23, RN-05), com recusa provada intocável (RF-24) e falha fechada no schema (RF-22); capability ausente esconde as 3 mutadoras (RF-27); narrativa colada é camada não-confiável no snapshot (INT-07, item 7). Nenhum segundo protocolo: a NC fala com a IA só pelo catálogo. |
| P3. Domínio puro (DDD + hexagonal) | ✅ As invariantes da nuvem — topologia fixa, injeção referencia premissa, FSM de status — são regra de domínio pura sem rede e sem modelo (RNF-01), com `import-linter` falhando o build na violação (RNF-02). A validação de schema fica na borda da aplicação, não no domínio — o domínio recebe estrutura já válida. |
| P4. TDD | ✅ Teste antes em todos os recortes: invariantes antes do agregado, casos de schema inválido antes do validador, prova de recusa intacta antes da integração com a FSM, o defeito das injeções invisíveis do v3 como caso de teste de UI (DoD 9). Zero commit de domínio sem teste correspondente. |
| P5. Observabilidade de nascença | ✅ Toda mutação nova com traço correlacionado (RNF-03, DoD 11), sobre a fundação OTel do 003; mutação originada de proposta aceita carrega o identificador da proposta no traço (RF-25) — a linha IA → proposta → efeito, exigida pelo P2, atravessa este módulo inteira. |
| P6. Jornada viva com prova visual | ✅ Jornada do dilema sintético da "Instituição Horizonte" de ponta a ponta — incluindo uma recusa de proposta, que é o momento de confiança da ferramenta — com captura gerada por script do build real e avaliação heurística datada, no mesmo pull request (T-14). |
| P7. Segredo nunca no cliente | ✅ Nenhum SDK, chave ou prompt no produto (DoD 12); o grep de CI cobre também os padrões do v3 (`CONFLICT_CLOUD_PROMPT`, `GoogleGenAI` — RNF-07). Os contraexemplos estão medidos na fonte: a chave no navegador (`geminiService.ts:16`) e o prompt de 75 linhas no cliente (F-05). |

**Sem violações.** A ressalva honesta: o P2 é avaliado aqui sobre a FSM que o ciclo 006
entrega — este plano assume aquela FSM pronta e promovida (DoR abaixo); se o 006
escorregar, o 007 não abre, e antecipar uma FSM provisória está proibido por
constituição (uma só e do servidor).

## Artefatos deste ciclo (declare todos os cinco — silêncio não é decisão)

| Artefato | Declaração | Por quê |
|---|---|---|
| `research.md` | `ART:research=no` | Não há incógnita a resolver por experimento: a estrutura vem verbatim da linhagem medida (F-01, F-02) e o método vem da skill `toc-evaporating-cloud` (F-10); a única dúvida empírica — o acerto das heurísticas de formulação — tem instrumento próprio (corpus sintético, RNF-08) que é teste, não pesquisa. |
| `data-model.md` | `ART:data-model=yes` | O módulo estende o modelo persistido do M1 com NuvemDeConflito (topologia fixa), EntidadeDaNuvem, ArestaDaNuvem, Premissa, Injecao (FSM + TRIZ) e as duas referências de costura. O documento nasce na abertura do ciclo (T-02), como extensão declarada de [`../004-nucleo-de-diagramas/data-model.md`](../004-nucleo-de-diagramas/data-model.md) — os testes de domínio são a forma final e prevalecem sobre o documento. |
| `contracts/` | `ART:contracts=yes` | Três contratos: a extensão REST dos recursos do M1 (nuvem, premissa, injeção), o **schema JSON versionado do ResultadoDeGeracao** (a peça que substitui o parser por regex — F-03) e a declaração das 3 ações `toc.*` (INT-02..INT-04) no formato do catálogo do 006. Escritos na abertura (T-02/T-03), verificados pelas DoD 6 e 7. |
| `checklist.md` | `ART:checklist=no` | A DoD da spec já é executável (16 linhas com comando); lista adicional duplicaria função (Princípio VI). |
| `ux-design.md` | `ART:ux-design=no` | As telas da NC (canvas, ficha de aresta, visão conflito+solução) são entrega do ciclo 002, que este ciclo consome; ajuste que a implementação exigir volta ao `ux-design.md` de lá no mesmo pull request. O fluxo de geração com diff (tela 6.3) usa a bandeja de propostas desenhada no 006. |

## Decisões de arquitetura do módulo

1. **Topologia fixa é invariante de agregado, não convenção de UI.** A nuvem nasce
   inteira num ato atômico (RF-02) e o domínio não tem operação de criar/excluir
   entidade ou aresta (RF-03) — o precedente é o helper do v3 (F-02), promovido de
   costume a invariante testada. A NC **não** reusa o grafo livre do M1 por dentro:
   reusa o Projeto (ciclo de vida, tenant, exportação) e modela a topologia própria —
   fingir que 5 nós fixos são um grafo genérico custaria invariante por cima de
   liberdade que ninguém quer.
2. **Schema na borda, domínio limpo.** O ResultadoDeGeracao é validado por schema JSON
   versionado **na borda da aplicação, no servidor** (RNF-04) antes de virar proposta;
   o domínio só recebe estrutura válida. O contraexemplo é o parser do v3 (F-03): lá a
   estrutura dependia da forma do texto; aqui a forma é contrato e a violação é recusa
   em falha fechada com traço (RF-22).
3. **Proposta completa × propostas granulares por estado da nuvem** (RF-23): nuvem
   vazia recebe uma proposta de preenchimento completo (revisão de uma vez, diff
   inteiro); nuvem com conteúdo recebe propostas por seção via ações granulares
   (INT-03, INT-04). A prova central é negativa: recusar deixa o estado serializado
   idêntico byte a byte (RF-24, DoD 5) — o teste roda antes da integração existir.
4. **Injeção referencia premissa por identidade, não por posição** (RN-04): a
   referência é chave estrangeira de domínio validada no agregado; arquivamento
   propaga com aviso quantificado (RF-15). O v3 pareava premissa e solução por aresta
   (F-01) — um para um, sem escolha; aqui a ligação é dado explícito porque várias
   injeções podem atacar a mesma premissa e uma aresta pode ter várias premissas.
5. **Heurísticas de formulação reusam o mecanismo do M2**: léxico como dado versionado
   por idioma, corpus sintético como função forçante, `indeterminado` honesto — nenhuma
   infraestrutura nova, só léxico novo (substantivo/infinitivo/negação). Aviso, nunca
   bloqueio (RN-06): o método educa, o dado obedece ao grupo.
6. **Campos de costura nascem agora, ações de costura no 008** (L-05):
   ReferenciaDeOrigem e ReferenciaDeSemeadura são colunas anuláveis criadas nas
   migrações deste ciclo; promover UDE→NC e semear ARF são do round 008. Custo: duas
   colunas; benefício: o 008 encadeia sem migrar o M3.
7. **Visão de solução é projeção, não segundo dado**: o diagrama de solução renderiza
   as injeções do mesmo agregado — não existe "dado da visão de solução". É o que
   torna estrutural a correção do defeito do v3 (5 de 7 injeções renderizadas — F-07):
   a projeção itera as 7 arestas por construção (RF-31, DoD 9).

## Grafo de dependência das tarefas

```
T-01 (DoD fixada)
  └─► T-02 (data-model + contratos REST estendidos)
        ├─► T-03 (schema do ResultadoDeGeracao + declaração das 3 ações toc.*)
        ├─► T-04 (fixture sintética do dilema + testes de invariante, vermelhos)
        │     └─► T-05 (domínio da nuvem: agregado, topologia fixa, premissas, TDD)
        │           └─► T-06 (injeções: referência a premissa, FSM, TRIZ, TDD)
        ├─► T-07 (heurísticas de formulação: léxico pt/en + corpus, TDD)
        └─► T-08 (migrações Alembic + repositórios, incl. campos de costura)
T-03, T-05, T-06 ─► T-09 (borda da geração: validador de schema + integração
                          com a FSM do 006 + prova de recusa intacta)
T-05..T-08 ─► T-10 (casos de uso + adaptadores REST + traço)
T-10 ─► T-11 (UI: canvas da NC + edição direta + avisos de formulação)
T-10 ─► T-12 (UI: ficha de aresta — premissas, injeções, TRIZ — + vista tabular)
T-09, T-10 ─► T-13 (UI: fluxo de geração com diff + visão conflito+solução)
T-11..T-13 ─► T-14 (jornada viva do dilema sintético) ─► T-15 (aptidões + qa-report)
T-15 ─► cauda (T-16..T-19: TAIL:review · TAIL:security · TAIL:mutation · TAIL:gate)
```

## Gates (DoR / DoD)

- **DoR — o ciclo não abre sem**: gate humano do 001 fechado; ciclos **004 e 006
  promovidos** (a NC precisa do Projeto do M1 e da FSM de proposta do catálogo —
  pré-condição do roadmap); a spec do M3 com as **7 premissas modeladas** (feito —
  RN-01, RN-02, entidades e arestas nomeadas chave a chave; a skill é a fonte técnica,
  a spec é a norma); os 5 `[DÚVIDA]` do Clarify respondidos; `ux-design.md` do 002
  cobrindo as telas 6.1, 6.2, 6.4 e 6.5.
- **DoD — o ciclo não fecha sem**: as 16 linhas da tabela de aceite da spec verdes com
  saída colada no `qa-report.md` (R1) e o tamanho do que cada portão examinou (R2); os
  dois portões executáveis do roadmap cumpridos — **invariantes da nuvem por teste de
  domínio** e **recusar deixa o projeto intacto** — com as saídas coladas; o portão de
  jornada (dilema sintético de ponta a ponta com captura); cauda completa
  (`TAIL:review`, `TAIL:security`, `TAIL:mutation`, `TAIL:gate`).
- **Corte de apetite** (round 007 — F-11 da spec): estourou → sai primeiro a **visão
  conflito+solução** (E3.4 — fica a lista de injeções sobre o diagrama do conflito);
  depois a regeneração granular (INT-03/INT-04 — fica só a geração completa); **nunca
  saem** as premissas por aresta — nuvem sem premissa explícita é desenho de opinião.
  Perde escopo, não ganha ciclo.

## Riscos e portões

| Risco | Ligado a | Mitigação |
|---|---|---|
| GATE-fsm — o ciclo 006 atrasar ou a FSM divergir do que este plano assume | DoR | O domínio inteiro (T-04..T-08) e a UI de modelagem (T-11, T-12) não dependem do catálogo (RF-28) — só T-09 e T-13 esperam o 006; a ordem do grafo já isola a espera, e antecipar FSM provisória é proibido por constituição. |
| GATE-granularidade — o corte "nuvem vazia × preenchida" da geração (RF-23) não cobrir o uso real | L-02 | [DÚVIDA] 2 no gate de abertura; as ações granulares (INT-03/INT-04) são a válvula — se o Product Steward recusar a proposta completa sobre nuvem preenchida, a mudança é de roteamento na borda, não de domínio. |
| GATE-schema — o schema do ResultadoDeGeracao divergir do formato que o catálogo do 006 fixar | L-03 | Schema versionado com recusa de versão desconhecida (RF-29); divergência custa migração de um contrato em `contracts/`, não de domínio; o 006 herda a declaração como rascunho de entrada. |
| GATE-premissas — a multiplicidade de premissas por aresta (≥ 0, ordenadas) ser contestada no gate | L-01 | [DÚVIDA] 1; voltar à forma estrita (1 por seta) é restrição de dado com teste, não migração — a decisão do gate cai sobre uma invariante, não sobre arquitetura. |
| GATE-formulacao — as heurísticas de formulação errarem para o lado errado (aviso falso em vez de silêncio) | L-04 | Corpus sintético com casos adversariais antes do código (T-07); política conservadora testada: na dúvida, `indeterminado` sem aviso (RF-10); `TAIL:mutation` sabota o léxico e exige que o corpus pegue. |
| GATE-costura — os campos de referência (origem/semeadura) anteciparem um desenho de encadeamento que o 008 contradiga | L-05 | Colunas anuláveis sem consumidor e sem regra (INT-05/INT-06 declaram, não executam); pior caso é uma migração pequena sobre dado ainda nulo; a decisão de desenho do encadeamento continua inteira no round 008. |
| GATE-apetite — E3.1–E3.4 com TDD e integração com a FSM estourarem o ciclo | apetite (round 007) | Corte em dois degraus declarado antes de abrir (visão de solução primeiro, regeneração granular depois, premissas nunca); reavaliação no meio do ciclo contra o grafo de tarefas. |
