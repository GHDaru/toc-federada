# TOC Federada

> Aplicação dos **Processos de Pensamento da Teoria das Restrições (TOC)** como ferramenta
> multiusuário — Árvore da Realidade Atual (ARA), Nuvem de Conflito (NC), Árvore da
> Realidade Futura (ARF), Árvore de Pré-Requisitos (APR), Árvore de Transição (AT),
> Estratégia & Táticas (S&T) e a jornada dos **cinco passos de focalização** costurando as
> ferramentas. Sucessora definitiva da linhagem TOC-Builder (quatro gerações de protótipo
> frontend) e **segunda aplicação candidata à federação** da plataforma `GHDaru/ghdaru`:
> Nível 2 (Operador) do padrão APH — **Aplicação ↔ Harness** — em repositório, serviço e
> banco **próprios**, `mode: embedded`, lado aplicação do Anexo B (ADR 0003). Assistência
> de inteligência artificial **exclusivamente pela fundação**, via catálogo de ações
> governadas — nunca por SDK de provedor no produto (ADR 0007).
>
> **Ordem de leitura obrigatória, antes de qualquer trabalho:**
> 1. `docs/governance/principles.md` — constituição do **método** (Maestro, I–VIII)
> 2. `docs/governance/constitution.md` — constituição do **projeto** (P1–P7)
> 3. `docs/governance/operating-model.md` — o modelo operacional vigente
>
> O que o produto é: `docs/produto/visao.md`. Mapa de módulos: `docs/produto/modulos.md`.
> Onde estamos: `docs/roadmap.md`. Decisões tomadas: `docs/adr/`.

> ✅ **A base é sintética desde o dia 1 (ADR 0006), e isso é uma regra, não um estado.**
> A irmã `gestaodeprioridades` nasceu com dados reais de pessoas e por isso o repositório
> dela é obrigatoriamente privado (ADR 0015 de lá). Aqui a dívida não existe e **não pode
> nascer**: nenhum dado real de pessoa — nome, enunciado de trabalho, data de desempenho —
> entra em fixture, captura, spec ou exemplo. Personas são fictícias ("Facilitadora TOC",
> "Instituição Horizonte"). É isso que permite o repositório aberto; quem colar um dado
> real aqui reverte essa possibilidade inteira. Está neste arquivo porque é o que todo
> agente lê primeiro.

## Regras do projeto (constituição, P1–P7 — resumo operacional)

- **P1 · Fronteira de escrita.** Escreva **somente** em `GHDaru/toc-federada`. `maestro`,
  `protocolos`, `ghdaru`, `gestaodeprioridades` e a linhagem TOC-Builder são **leitura**.
  Encontrou uma lacuna lá fora? **Relate e pare** — a escrita externa exige aprovação
  humana explícita, caso a caso. Relatar **não é** avisar no chat: escreva
  `mensagens/NNN-para-<repo>-<assunto>.md`, com evidência por `arquivo:linha` e o commit
  lido. A conversa se perde; o artefato fica, e é ele que o humano leva ao destino.
  Convenção: `mensagens/README.md`.
- **P2 · Federação por contrato.** Nada de segundo protocolo, nada de login próprio
  (identidade por `POST /auth/introspect`), autorização **fora** do modelo de linguagem,
  verbo mutador nasce `action_proposal`, tela é dado e nunca instrução. O alcance está
  declarado no próprio texto do princípio — lição do ADR 0011→0016 da irmã.
- **P3 · DDD + hexagonal.** Domínio e aplicação puros; efeito só por porta; adaptador na
  borda; `import-linter` como função de aptidão. As regras da TOC (critérios de UDE —
  Efeito Indesejável —, suficiência causal) são **regra de domínio pura**, testável sem
  rede.
- **P4 · TDD.** Teste que falha **antes** do código de produção. Defeito começa pelo teste
  que o reproduz.
- **P5 · Observabilidade de nascença.** Traço (OpenTelemetry), log estruturado
  correlacionado e métrica nascem com a funcionalidade — sem traço, não está pronta.
- **P6 · Jornada viva.** Interface entrega jornada + captura gerada por script versionado
  + avaliação heurística, no mesmo pull request (skill `living-journey`).
- **P7 · Segredo nunca no cliente.** Chave e credencial só no servidor, por variável de
  ambiente. A violação canônica que este princípio proíbe está na própria linhagem:
  `tocbuilderv3/services/geminiService.ts:16` inicializa o cliente do provedor **no
  navegador**.

## Regras herdadas de retrospectiva (nunca corrigir a mesma coisa duas vezes)

As cinco regras abaixo **não nasceram aqui**: são o custo já pago pelas retrospectivas dos
ciclos 001 e 002 da irmã `gestaodeprioridades` (ADR 0001). Herdá-las prontas é o motivo de
ter uma irmã mais velha; reaprendê-las na prática seria pagar duas vezes.

- **R1 · Verifique antes de afirmar.** Afirmação factual sobre artefato — número, saída de
  script, estado de arquivo, defeito em código alheio — só entra num documento **depois de
  executada, com o que voltou colado**. Nunca transcreva um `✓`: copie a linha que o
  script imprimiu. Nunca descreva o comportamento de uma fórmula: calcule. *(Irmã, ciclo
  001: o mesmo defeito em cinco disfarces, os cinco pegos por revisor independente,
  nenhum pelo autor.)*
- **R2 · Portão verde exige "quanto ele examinou?".** Se a saída não disser o tamanho do
  que foi verificado, o verde não é evidência. A resposta vai para o `qa-report.md` junto
  com o código de saída. *(Irmã, ciclo 001: quatro portões verdes que não tinham olhado
  para o que se supunha que olhassem.)*
- **R3 · Portão proporcional: decida, registre e siga.** Ação **reversível e de baixo
  raio** — protótipo descartável, rascunho, escolha de layout, nome de arquivo — é do
  agente (Princípio III). Decida, registre em ADR e **prossiga**: parar para perguntar o
  que o método já autoriza é teatro de cerimônia. Pergunte só o que é irreversível,
  externo, muda contrato — **ou toca princípio inegociável**. A quarta condição não é
  enfeite: na irmã, um ADR usou esta mesma regra para decidir matéria que tocava o P2
  (INEGOCIÁVEL) **sem sequer citá-lo**, e a correção exigiu emenda constitucional (ADR
  0011→0016 de lá). Por isso **todo ADR daqui declara o campo "Princípios tocados"**, com
  `nenhum` escrito por extenso quando for o caso.
- **R4 · Caminho citado é caminho aberto.** O `check-links.sh` do método apaga trechos em
  crase **antes** de procurar link — logo a forma como esta documentação mais cita
  arquivo é a que ele nunca verifica. Na irmã, uma jornada citou um arquivo inexistente e
  o portão respondeu verde sobre 43 links. Citou arquivo? Abra antes de gravar — e rode
  `scripts/check-caminhos.sh`, o portão deste projeto que confere caminho entre crases.
- **R5 · Decisão que contradiz decisão tem de se declarar.** Na irmã, dois ADRs
  mutuamente contraditórios ficaram os dois "Aceita" e a contradição atravessou sete
  portões verdes — quem pegou foi a revisão independente. Sucedeu um ADR? Diga no novo
  (`**Sucede**`) **e** no antigo (`Superseded by`); a aptidão é
  `scripts/check-adrs-sucessao.sh`, que também exige o ADR no índice do
  `docs/adr/README.md` e no índice de decisões.

## Stack (ADR 0002 — mudar exige ADR novo)

React + TypeScript/Vite (interface) · FastAPI/Python (serviço) · PostgreSQL Neon (banco,
**projeto próprio**) · armazenamento compatível com S3 atrás de porta · OpenTelemetry ·
deploy Vercel (interface) + Railway (serviço), em eTLD+1 **distinto** do hospedeiro.

Exemplos de adaptador para **ler, nunca copiar por atalho**: `GHDaru/ghdaru` —
`apps/api/src/ghdaru_api/documents/ports/storage.py` e `.../adapters/s3_compat.py`.

## Idioma

Documentação do projeto (constituição, specs, jornadas, ADRs) em **português**. A
superfície instalável do Maestro (`.claude/`, `skills/`, `scripts/` do método,
`.specify/`, `docs/governance/principles.md` e `operating-model.md`) permanece em
**inglês** (ADR 0014 do método). Linguagem ubíqua do domínio é portuguesa: `projeto`,
`nó`, `aresta causal`, `efeito indesejável`, `premissa`, `injeção`, `restrição`,
`obstáculo`, `objetivo intermediário`.

## Method: Maestro
@docs/governance/principles.md

- The constitution above is loaded automatically. Read
  `docs/governance/operating-model.md` before any work — it is not.
- **Skills first**: before acting, check whether one of the skills below applies; if
  there is a reasonable chance, follow it (each carries its Iron Law):
  - `anti-patterns` — Catalogue of what NOT to do when one human runs many agents — the recurring mistakes observed in our own retrospectives and in the ecosystem.
  - `constitution-check` — Produces the Constitution Check table (Maestro Principles I–VIII) inside a plan.md, decides when a principle counts as violated and what to do with the violation.
  - `diagnose-before-fix` — Root-cause discipline — investigate before fixing.
  - `fight-the-pile-up` — Editorial checklist that turns a dense document (a "pile-up" — many acronyms with no dictionary, everything on one page, no narrative) into clear text without changing the technical content.
  - `living-journey` — Living journey documentation — one document per journey, screenshots generated from the real build by a versioned script, and a dated heuristic evaluation, all in the same pull request.
  - `verifiable-dod` — Turns vague acceptance criteria into executable fitness functions (grep, ls, tests) that a machine can verify without human judgement.
- Flow: `spec → plan (Constitution Check) → tasks → implement → DoD → review in
  fresh context → human gate → merge`.
- Lanes: light (the pull request is the artifact) · full (complete spec) · infra (full +
  reversibility).
- Every cycle declares its conditional artifacts and carries the closing tail
  (`TAIL:review`, `TAIL:security`, `TAIL:mutation`, `TAIL:gate`) in `tasks.md`, with
  the evidence in
  `qa-report.md`. Catalogue: `docs/governance/artifacts.md`.
- **Asked "are you following the method?" — do NOT answer from memory.** Run
  `scripts/check-conformance.sh <NNN>` and read it: memory reports intention, not fact.
- Never REWRITE what the method keeps as history: the body of a committed ADR,
  `docs/records/decisoes.jsonl`, and the dated idea cards under `docs/ecosystem/ideias/`.
  The route is always to APPEND — a new ADR that supersedes, `scripts/record-decision.sh`,
  a new state line. **A `PreToolUse` guard refuses the rewrite**, so this is enforced,
  not asked.
