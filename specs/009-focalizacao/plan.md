# Plan 009 — Focalização (ciclo planejado)

> Siglas: TOC — Teoria das Restrições · ARA — Árvore da Realidade Atual · NC — Nuvem
> de Conflito · ARF — Árvore da Realidade Futura · APR — Árvore de Pré-Requisitos ·
> AT — Árvore de Transição · APH — Aplicação ↔ Harness · ADR — Architecture Decision
> Record (Registro de Decisão Arquitetural) · DoD — Definition of Done (Definição de
> Pronto) · DoR — Definition of Ready (Definição de Prontidão) · TDD — Test-Driven
> Development (desenvolvimento guiado por teste) · DDD — Domain-Driven Design (Design
> Orientado a Domínio) · IA — inteligência artificial · FSM — máquina de estados
> finitos · OTel — OpenTelemetry · CI — integração contínua · UI — interface de
> usuário · UX — experiência de usuário · YAGNI — You Aren't Gonna Need It · DBR —
> tambor-pulmão-corda (*Drum-Buffer-Rope*) · i18n — internacionalização · SDK —
> Software Development Kit

- **Spec**: `spec.md` (Rascunho — aprovação no gate humano que abre o ciclo) · **Raia**:
  plena · **Data**: 2026-09-03
- **Estado**: **planejado no ciclo 001, não executado.** Este plano é escrito antes de o
  ciclo abrir; o Constitution Check abaixo avalia o plano como está e será reconferido
  na abertura, com o ciclo 008 promovido e o ADR 0005 conferido inalterado.

## Constitution Check (governance/principles.md)

| Princípio | Conformidade |
|---|---|
| I. Spec-driven | ✅ A spec 009 precede este plano, e ambos precedem qualquer código do módulo. O escopo é o do round 009 (E6.1–E6.2; métricas da restrição fora por ADR 0005) — mudança de escopo volta à spec antes de virar código; os 5 `[DÚVIDA]` do Clarify vão ao Product Steward no gate de abertura. |
| II. Human-governed orchestration | ✅ O humano decide no gate: aprovação da spec, respostas do Clarify (tipos de restrição, alcance da herança, reabertura de passo, desfecho da análise, ux do M6), corte de apetite. Agentes implementam por fronteira (domínio da jornada, borda dos vínculos, UI); a revisão independente em contexto fresco confere os dois portões do roadmap — **os cinco passos com estado herdado** e **recomeçar sem apagar** (`TAIL:review`). |
| III. Reversibility / risk gates | ✅ Tudo é reversível por desenho: exclusão suave herdada do M1, histórico somente-acréscimo no domínio (RN-04 — recomeçar preserva o ciclo fechado íntegro), reabertura de passo registra evento sem apagar decisão (RF-10), e a única escrita originada de modelo (`toc.suggest_constraint`) nasce proposta recusável com prova de intocabilidade (DoD 9). Nenhuma ação externa ou irreversível nova nasce aqui. |
| IV. Test-first / verifiable DoD | ✅ TDD estrito com o teste central do módulo nascendo primeiro: a travessia dos cinco passos com estado herdado (DoD 3) e o recomeço sem apagar (DoD 4) são testes de domínio escritos antes do agregado. DoD com 16 linhas executáveis; `TAIL:mutation` sabota a ordem canônica, a unicidade e o bloqueio de herança e os vê recusar. |
| V. Context economy / boundary | ✅ Corte por fronteira dentro do ciclo: o domínio da jornada (passos, restrição, herança) é implementável sem nenhum outro módulo — vínculos entram por identificador opaco no domínio e só a borda os valida contra M2–M4 (RNF-04); a UI vem depois. A ação de catálogo é o último recorte e o primeiro corte de apetite. |
| VI. Living artifacts | ✅ A JornadaDaAnalise (função pura) é consumida pelo mapa da jornada com função forçante — pendência não computada não aparece e o teste falha; a declaração de `toc.suggest_constraint` é consumida pelo catálogo do 006; a jornada viva do módulo é o portão de merge. Nenhum artefato sem consumidor. |
| VII. Light governance / YAGNI | ✅ Descartados por YAGNI neste ciclo, cada um com porta de volta: métricas de desempenho da restrição (fora por ADR 0005 — entrada é ADR novo); sugestão assistida de ferramenta por passo (o round solta primeiro; a trilha estática cumpre o job); desfecho de primeira classe da análise ([DÚVIDA] 4); índice materializado de navegação reversa (L-03 — consulta basta até prova em contrário). |
| VIII. Intelligible communication | ✅ Bloco de siglas no topo dos quatro artefatos do ciclo; termos novos (ciclo de focalização, decisão herdada, veredito, vínculo canônico) definidos onde nascem, no modelo de domínio da spec. Conferência por amostragem do revisor da cauda. |

### Project Constitution Check (governance/constitution.md — ADR 0001)

| Princípio | Conformidade |
|---|---|
| P1. Fronteira de escrita | ✅ Só este repositório. O M6 nem fonte de linhagem tem — a prova de ausência (F-01, grep com `0` colado) foi lida, nunca editada; lacuna externa achada durante o ciclo vira `mensagens/NNN-...`. |
| P2. Federação por contrato (APH) | ✅ Registrar restrição, concluir passo e julgar herança são manipulação direta do titular (item 8 — alvo nomeado pelo gesto, valor no controle, reversível por histórico somente-acréscimo); a única escrita originada de modelo nasce `action_proposal` na FSM **do servidor do 006** (RF-19), com recusa provada intocável (DoD 9); capability ausente esconde a mutadora (RF-21); notas e decisões são camada não-confiável no snapshot (INT-06, item 7). Nenhum segundo protocolo. |
| P3. Domínio puro (DDD + hexagonal) | ✅ As invariantes da jornada — ordem canônica, unicidades, imutabilidade de ciclo fechado, bloqueio por herança — são regra de domínio pura sem rede e sem modelo (RNF-01), com `import-linter` falhando o build na violação (RNF-02). A validação de vínculo contra M2–M4 fica na borda (RNF-04) — o domínio guarda referência opaca. |
| P4. TDD | ✅ Teste antes em todos os recortes: a travessia dos cinco passos (DoD 3) e o recomeço íntegro (DoD 4) nascem vermelhos antes do agregado; o bloqueio de herança (DoD 5) antes do veredito; a recusa intacta (DoD 9) antes da integração com a FSM. Zero commit de domínio sem teste correspondente. |
| P5. Observabilidade de nascença | ✅ Toda mutação nova com traço correlacionado (RNF-03, DoD 12), sobre a fundação OTel do 003; mutação originada de proposta aceita carrega o identificador da proposta — a linha IA → proposta → efeito atravessa o módulo inteira. |
| P6. Jornada viva com prova visual | ✅ A análise sintética da "Instituição Horizonte" atravessa os cinco passos com vínculos reais de ARA, NC e APR e o julgamento de herança no recomeço — captura **por passo** (o portão do roadmap) gerada por script do build real e avaliação heurística datada, no mesmo pull request (T-13). |
| P7. Segredo nunca no cliente | ✅ Nenhum SDK, chave ou prompt no produto (DoD 13); o prompt da sugestão de restrição é versionado no servidor da fundação (ADR 0007) e nunca circula no cliente. |

**Sem violações.** A ressalva honesta: o M6 é o único módulo de superfície nova sem
protótipo do ciclo 002 (L-05) — o Constitution Check do P6 assume que o desenho de UX
nasce dentro deste ciclo, e isso consome apetite; o corte declarado abaixo protege o
que o round marca como inegociável.

## Artefatos deste ciclo (declare todos os cinco — silêncio não é decisão)

| Artefato | Declaração | Por quê |
|---|---|---|
| `research.md` | `ART:research=no` | Não há incógnita a resolver por experimento: o método dos cinco passos é literatura estabelecida da TOC, o modelo é greenfield decidido por ADR 0005, e as dúvidas restantes são de produto ([DÚVIDA] 1–5), resolvidas por gate humano, não por pesquisa. |
| `data-model.md` | `ART:data-model=yes` | O módulo estende o modelo persistido do M1 com AnaliseDeFocalizacao, CicloDeFocalizacao, PassoDeFocalizacao, Restricao, VinculoDeFerramenta e DecisaoHerdada. O documento nasce na abertura do ciclo (T-02), como extensão declarada de [`../004-nucleo-de-diagramas/data-model.md`](../004-nucleo-de-diagramas/data-model.md) — os testes de domínio são a forma final e prevalecem sobre o documento. |
| `contracts/` | `ART:contracts=yes` | Dois contratos: a extensão REST dos recursos do M1 (análise, ciclo, passo, restrição, vínculo, herança) e a declaração de `toc.suggest_constraint` (INT-05) no formato do catálogo do 006, com schema de entrada/saída. Escritos na abertura (T-02/T-03). |
| `checklist.md` | `ART:checklist=no` | A DoD da spec já é executável (16 linhas com comando); lista adicional duplicaria função (Princípio VI). |
| `ux-design.md` | `ART:ux-design=yes` | **Diferente dos módulos M1–M3**: as telas da jornada (mapa, painel do passo, julgamento de herança, linha do tempo) não foram prototipadas no ciclo 002 (L-05). O `ux-design.md` nasce neste ciclo (T-09), antes da UI, sob o mesmo processo — papel semântico → desenho → jornada viva — e o [DÚVIDA] 5 confirma o arranjo no gate. |

## Decisões de arquitetura do módulo

1. **Jornada é agregado próprio, não view sobre as ferramentas.** A análise de
   focalização guarda restrição, passos, decisões e vínculos como dado seu; os módulos
   M2–M4 não ganham nenhum campo (INT-02..INT-04, L-03). O acoplamento é unidirecional
   — o M6 conhece os outros pela referência opaca; os outros não conhecem o M6 — e é o
   que permite construir a jornada por cima de ferramentas já promovidas sem tocá-las.
2. **Vínculo opaco no domínio, validado na borda.** O domínio trata VinculoDeFerramenta
   como (tipo, identificador, papel, justificativa) e aplica só a regra canônica
   (RN-06); existência, tenant e estado do projeto referenciado são verificados no
   servidor da aplicação (RNF-04). O domínio do M6 permanece testável sem os outros
   módulos existirem — é o corte que deixa T-04..T-06 rodarem antes de qualquer
   integração.
3. **Histórico por imutabilidade, não por versionamento.** Ciclo fechado é objeto
   somente leitura no domínio (RN-04); não há snapshot, diff nem versão — a linha do
   tempo é a própria lista de ciclos. Recomeçar é a única operação que fecha, e o teste
   do portão compara o ciclo fechado byte a byte antes/depois do recomeço (DoD 4).
4. **Anti-inércia como bloqueio de domínio, não como lembrete de UI.** O veredito
   pendente impede a conclusão do passo `subordinar` no agregado (RN-05) — a UI mostra o
   contador (RI-05), mas quem recusa é o domínio. É a decisão que transforma o quinto
   passo do método de conselho em invariante.
5. **A trilha estática é o produto; a sugestão é acessório.** A jornada guiada completa
   (E6.1 + E6.2) funciona sem catálogo (RF-20); `toc.suggest_constraint` é o último
   recorte implementado e o primeiro cortado (round 009 — F-04). A ordem do grafo de
   tarefas reflete isso: T-11 é folha, sem nada dependendo dele.
6. **Cinco passos como tipo fechado, não como workflow configurável.** Nenhuma tabela
   de "definição de passo", nenhum motor de workflow: os cinco passos são enum e ordem
   fixa no domínio (RN-01). Configurabilidade aqui seria YAGNI puro — o método tem
   cinco passos há quarenta anos.

## Grafo de dependência das tarefas

```
T-01 (DoD fixada + pré-condições: 008 promovido, ADR 0005 inalterado)
  └─► T-02 (data-model + contratos REST estendidos)
        ├─► T-03 (declaração de toc.suggest_constraint no formato do catálogo)
        ├─► T-04 (fixture sintética + testes vermelhos: travessia dos 5 passos,
        │         recomeço íntegro, bloqueio de herança)
        │     └─► T-05 (domínio da jornada: análise, ciclo, passos, restrição, TDD)
        │           └─► T-06 (recomeço + decisões herdadas + vínculos opacos, TDD)
        └─► T-07 (migrações Alembic + repositórios)
T-05, T-06, T-07 ─► T-08 (casos de uso + adaptadores REST + validação de vínculo
                          na borda + traço)
T-02 ─► T-09 (ux-design.md das telas da jornada — antes de qualquer UI)
T-08, T-09 ─► T-10 (UI: mapa da jornada + painel do passo + julgamento de herança
                    + linha do tempo)
T-03, T-08 ─► T-11 (borda da sugestão: toc.suggest_constraint na FSM do 006 +
                    prova de recusa intacta)   ← primeiro corte de apetite
T-10 (e T-11 se ficar) ─► T-12 (vínculos navegáveis contra M2–M4 reais)
T-12 ─► T-13 (jornada viva com captura por passo) ─► T-14 (aptidões + qa-report)
T-14 ─► cauda (T-15..T-18: TAIL:review · TAIL:security · TAIL:mutation · TAIL:gate)
```

## Gates (DoR / DoD)

- **DoR — o ciclo não abre sem**: gate humano do 001 fechado; **ciclo 008 promovido**
  (a jornada aponta para ARA, NC, ARF, APR e AT — todas precisam existir; pré-condição
  do roadmap, F-06); **ADR 0005 conferido inalterado** (se DBR entrar, é decisão nova
  antes, não durante — F-06); os 5 `[DÚVIDA]` do Clarify respondidos; decisão do
  [DÚVIDA] 5 sobre onde nasce o ux da jornada.
- **DoD — o ciclo não fecha sem**: as 16 linhas da tabela de aceite da spec verdes com
  saída colada no `qa-report.md` (R1) e o tamanho do que cada portão examinou (R2); os
  dois portões executáveis do roadmap cumpridos — **teste percorre os cinco passos com
  estado herdado** e **recomeçar reabre sem apagar histórico** — com as saídas coladas;
  o portão de jornada (análise sintética de ponta a ponta com captura **por passo**);
  cauda completa (`TAIL:review`, `TAIL:security`, `TAIL:mutation`, `TAIL:gate`).
- **Corte de apetite** (round 009 — F-04): estourou → sai primeiro a **sugestão
  assistida** (T-11 — fica a jornada guiada estática); depois a linha do tempo
  comparativa (fica a lista simples de ciclos); **nunca sai** o registro da restrição —
  é a entidade que dá nome à teoria. Perde escopo, não ganha ciclo.

## Riscos e portões

| Risco | Ligado a | Mitigação |
|---|---|---|
| GATE-dependencia — o ciclo 008 atrasar e a jornada não ter para onde apontar | DoR | O domínio do M6 inteiro (T-04..T-07) usa vínculo opaco e roda sem M2–M4 (decisão 2); só T-12 exige as ferramentas reais. Se o 008 escorregar, o 009 não abre — pré-condição do roadmap, não deste plano. |
| GATE-ux — o M6 é o único módulo de superfície nova sem protótipo do 002 | L-05 | `ART:ux-design=yes` com T-09 **antes** de qualquer UI no grafo; [DÚVIDA] 5 decide no gate se o desenho antecipa; o corte de apetite protege E6.1 se o desenho custar mais que o previsto. |
| GATE-heranca — o alcance da herança anti-inércia (só explorar+subordinar) estar errado | L-02 | [DÚVIDA] 2 no gate de abertura; mudar o alcance é mudar um filtro sobre eventos já registrados, não o modelo — o custo da resposta tardia é baixo por construção. |
| GATE-taxonomia — o enum de tipos de restrição não cobrir o uso real | L-01 | [DÚVIDA] 1; enum fechado com migração aditiva pequena como saída; tipo livre custaria a consistência da linha do tempo entre ciclos. |
| GATE-navegacao — a navegação reversa por consulta (sem campo nos M2–M4) ficar lenta ou confusa | L-03 | Consulta indexada na borda (decisão 2); se a escala provar o contrário, índice materializado sem tocar nos agregados das ferramentas — medição na jornada viva (RNF-05). |
| GATE-sugestao — `toc.suggest_constraint` sem precedente errar o recorte das candidatas | L-04 | É o primeiro corte de apetite (T-11 é folha no grafo); a prova de recusa intacta (DoD 9) garante que errar a sugestão nunca corrompe a análise. |
| GATE-apetite — E6.1 + E6.2 + ux novo estourarem o ciclo | apetite (round 009) | Corte em dois degraus declarado antes de abrir (sugestão primeiro, linha do tempo comparativa depois, registro da restrição nunca); reavaliação no meio do ciclo contra o grafo de tarefas. |
