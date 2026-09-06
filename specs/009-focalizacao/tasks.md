# Tasks 009 — Focalização

> Siglas: **TOC** — Teoria das Restrições · **ARA** — Árvore da Realidade Atual ·
> **NC** — Nuvem de Conflito · **APR** — Árvore de Pré-Requisitos · **AT** — Árvore de
> Transição · **ADR** — Architecture Decision Record (Registro de Decisão Arquitetural)
> · **DoD** — Definition of Done (Definição de Pronto) · **TDD** — Test-Driven
> Development (desenvolvimento guiado por teste) · **FSM** — máquina de estados
> finitos · **UI** — interface de usuário · **UX** — experiência de usuário · **IA** —
> inteligência artificial · **OTel** — OpenTelemetry · **i18n** — internacionalização.
>
> Ciclo **planejado** — nenhuma caixa marcada antes do fato (as marcações abaixo são
> todas vazias de propósito). Ordem TDD: em toda tarefa de código, o teste vermelho vem
> antes da implementação — e neste ciclo os testes vermelhos centrais são a travessia
> dos cinco passos com estado herdado e o recomeço que não apaga (T-04), que nascem
> antes do agregado.

> **Estado em 2026-09-06 (execução).** T-01 a T-14 marcadas com a evidência colada em
> [`qa-report.md`](qa-report.md) — cada marca tem comando executado e saída, nunca um `✓`
> transcrito. **As quatro linhas da cauda continuam desmarcadas de propósito**: quem
> executou não revisa (Princípio II), e caixa marcada não é testemunha. Duas ressalvas
> ficam registradas junto das marcas, e não escondidas por elas:
>
> - **T-01** — a pré-condição "ciclo 008 promovido" **não estava cumprida**: o M4 foi
>   construído em paralelo por outro construtor. O M6 se protegeu combinando pela porta e
>   pelo tipo de ligação, nunca pela implementação dele; a consequência está declarada no
>   `qa-report.md`.
> - **T-08** — a exportação sem perda (RF-18) está entregue **da metade do M6**: a E1.4 do
>   M1 (exportação do projeto) ainda não existe, e a costura com o formato dela é do ciclo
>   que a entregar.

## Verificação primeiro

- [x] T-01 — Fixar a DoD executável do ciclo (as 16 linhas da spec, com comando e valor
  esperado) e conferir as pré-condições do roadmap: **ciclo 008 promovido** e **ADR
  0005 inalterado** (diff vazio contra o corpo aceito). · Dep: — · Ref: `spec.md`
  § Critérios de aceite; `docs/roadmap.md` § "O que o ciclo 009 não pode começar sem" ·
  Aceite: cada linha tem comando; nenhum critério subjetivo; pré-condições coladas no
  `qa-report.md`.

- [x] T-02 — Consolidar `data-model.md` (extensão do modelo do M1: AnaliseDeFocalizacao,
  CicloDeFocalizacao, PassoDeFocalizacao, Restricao, VinculoDeFerramenta,
  DecisaoHerdada, eventos) e `contracts/rest-api.md` estendendo os recursos do M1. ·
  Dep: T-01 · Ref: spec § Entidades; plan § Artefatos (`ART:data-model=yes`,
  `ART:contracts=yes`) · Aceite: todo agregado/evento da spec aparece no documento;
  nenhuma entidade sem invariante escrita; vínculo modelado como referência opaca.

- [x] T-03 — Declarar `toc.suggest_constraint` (`contracts/acoes-catalogo.md`): nome,
  classe de risco, `input_schema`, saída (candidatas com nó de origem + racional), uma
  `action_proposal` por candidata. · Dep: T-02 · Ref: INT-05; RF-19; ADR 0007 · Aceite:
  a declaração segue o formato do catálogo do 006; nenhuma rota fora da FSM do
  servidor.

## Domínio da jornada (E6.1 + E6.2 — roda sem nenhum outro módulo)

- [x] T-04 — Fixture sintética da análise "Fluxo de matrículas" da Instituição
  Horizonte + testes de invariante vermelhos: os cinco passos fixos e ordenados, uma
  restrição vigente e um ciclo aberto, **a travessia completa com estado herdado**, o
  **recomeço que preserva o ciclo fechado byte a byte** e o **bloqueio por herança
  pendente**. **Nenhum agregado antes disto.** · Dep: T-02 · Ref: RN-01..RN-05; DoD 3,
  4, 5 · Aceite: DoD 2–6 vermelhos pelo motivo certo (agregado inexistente); zero dado
  real de pessoa (ADR 0006).

- [x] T-05 — Domínio da jornada: agregado AnaliseDeFocalizacao, ciclo com os cinco
  passos instanciados na criação, registro/edição de restrição (tipo, justificativa,
  referência de origem), conclusão de passo com decisão, reabertura do anterior com
  justificativa, notas, JornadaDaAnalise (pendências por função pura). TDD sobre a
  fixture. · Dep: T-04 · Ref: RF-02, RF-05..RF-13; RN-01..RN-03; plan § Decisões 1 e
  6 · Aceite: DoD 2, 3 e 6 verdes; reabrir não apaga a decisão anterior (evento novo,
  histórico somente-acréscimo).

- [x] T-06 — Recomeço e anti-inércia: fechar ciclo (imutável no domínio), abrir novo em
  `identificar`, herdar decisões de explorar/subordinar com veredito `pendente`,
  julgamento `mantida`/`revogada` com justificativa, bloqueio da conclusão de
  `subordinar` com pendência; vínculos de ferramenta como referência opaca com regra
  canônica e justificativa fora dela. TDD. · Dep: T-05 · Ref: RF-14..RF-17; RN-04..
  RN-07; plan § Decisões 2, 3 e 4 · Aceite: DoD 4, 5 e 7 verdes; ciclo fechado
  comparado byte a byte antes/depois do recomeço.

- [x] T-07 — Migrações Alembic (análise, ciclo, passo, restrição, vínculo, herança) com
  `upgrade` **e** `downgrade` testados; repositórios mantendo o isolamento por
  inquilino do M1. · Dep: T-02 · Ref: spec § Entidades; RNF-01 · Aceite: ciclo
  upgrade→downgrade sem resíduo, saída colada; teste de isolamento do 004 verde sobre
  as tabelas novas.

## Borda e interface

- [x] T-08 — Casos de uso + adaptadores REST (análise, restrição, passos, recomeço,
  herança, vínculos) com validação de vínculo na borda (existência, tenant, degradação
  legível para arquivado), traço OTel por mutação e autorização fail-closed. ·
  Dep: T-05..T-07 · Ref: RF-18; RNF-03, RNF-04; contratos do T-02 · Aceite: DoD 8, 11
  e 12 verdes; teste falha se `RestricaoRegistrada`, `PassoConcluido` ou `CicloFechado`
  não emitirem traço.

- [x] T-09 — `ux-design.md` das telas da jornada (mapa, painel do passo, julgamento de
  herança, linha do tempo): papel semântico antes do componente, estados vazios e de
  pendência desenhados, acessibilidade da trilha (nunca só cor). **Antes de qualquer
  UI** — o M6 não tem protótipo do ciclo 002 (L-05). · Dep: T-02 · Ref: RI-01..RI-08;
  plan § Artefatos (`ART:ux-design=yes`); [DÚVIDA] 5 · Aceite: as 4 telas da spec
  cobertas; gate de UX do método executado.

- [x] T-10 — UI da jornada: mapa dos cinco passos com estado e pendências, painel do
  passo em três camadas (herdado / trabalho / decisão), julgamento de herança com
  vereditos de mesmo peso, linha do tempo com ciclo fechado somente leitura, listagem
  com passo atual e restrição. · Dep: T-08, T-09 · Ref: RI-01..RI-05, RI-07, RI-08 ·
  Aceite: teste de fluxo feliz e de bloqueio por pendência; i18n sem literal solto;
  identificadores de tela (`toc.foco_jornada`, `toc.foco_passo`,
  `toc.foco_linha_do_tempo`) registrados com `ai_visible` campo a campo (INT-06).

- [x] T-11 — Borda da sugestão: `toc.suggest_constraint` na FSM do 006 — candidatas a
  partir dos nós de causa raiz da ARA vinculada, uma proposta por candidata, prova de
  recusa intacta (estado serializado idêntico byte a byte), capability ausente esconde
  a ação. **Primeiro corte de apetite — nada depende desta tarefa.** · Dep: T-03,
  T-08 · Ref: RF-19..RF-21; INT-05; plan § Decisão 5 · Aceite: DoD 9 e 10 verdes.

- [x] T-12 — Vínculos navegáveis contra os módulos reais: criar/vincular ARA do passo
  identificar (com registro de restrição a partir de causa raiz), NC de explorar/
  subordinar, APR/AT de elevar; navegação nos dois sentidos; estado do projeto
  vinculado visível. · Dep: T-10 (e T-11 se mantida) · Ref: RF-06, RF-14; INT-02..
  INT-04 · Aceite: teste de integração cobre as quatro combinações canônicas e uma
  não-canônica com justificativa.

- [x] T-13 — Jornada viva: a análise sintética da Instituição Horizonte de ponta a
  ponta — identificar (com ARA e sugestão, se mantida) → explorar → subordinar (com NC
  do conflito) → elevar (com APR) → recomeçar (com julgamento de herança) — **captura
  por passo** gerada por script versionado do build real + avaliação heurística datada,
  no mesmo pull request. · Dep: T-12 · Ref: spec § Entregáveis (P6); F-06; ADR 0006 ·
  Aceite: DoD 14 — script em `docs/jornadas/scripts/`, uma captura por passo, grep
  negativo de nome real de pessoa.

- [x] T-14 — Rodar as aptidões e preencher o `qa-report.md`: as 16 linhas da DoD com
  saída colada (R1) e quanto cada portão examinou (R2); atualizar CHANGELOG; ADR novo
  se o Clarify tiver gerado decisão material (candidata: taxonomia de tipos de
  restrição). · Dep: T-13 · Ref: DoD 15 e 16 · Aceite: `scripts/check-conformance.sh
  009` código 0; nenhuma célula do qa-report preenchida sem comando executado.

## Cauda (fechamento — nenhuma marcada antes da evidência no qa-report)

- [ ] TAIL:review — Revisão independente em contexto fresco (quem executou não revisa):
  spec × código × DoD, com os dois portões nomeados do roadmap — **teste percorre os
  cinco passos com estado herdado** e **recomeçar reabre sem apagar histórico** —
  verificados por leitura e por execução, achados registrados. · Dep: T-01..T-14

- [ ] TAIL:security — Passagem de segurança em contexto fresco: nenhum SDK, chave ou
  prompt no produto (DoD 13), validação de vínculo no servidor com tenant conferido
  (DoD 8), autorização fail-closed nas rotas novas, capability ausente esconde a
  mutadora (DoD 10), notas e decisões tratadas como camada não-confiável no snapshot
  (INT-06). · Dep: T-08, T-10, T-11

- [ ] TAIL:mutation — Testes de mutação sobre a ordem canônica dos passos, as
  unicidades (restrição vigente, ciclo aberto), a imutabilidade de ciclo fechado e o
  bloqueio por herança pendente — as funções cuja falha silenciosa transforma a jornada
  em lista de tarefas sem método; taxa e sobreviventes no `qa-report.md`. · Dep: T-05,
  T-06

- [ ] TAIL:gate — Portão humano de merge com as evidências das 16 linhas da DoD, as
  respostas dos 5 `[DÚVIDA]` e a cauda acima. · Dep: tudo
