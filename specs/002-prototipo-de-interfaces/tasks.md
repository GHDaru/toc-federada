# Tasks 002 — Protótipo de interfaces (ciclo planejado)

> Siglas: ADR — Architecture Decision Record (Registro de Decisão Arquitetural) · TOC —
> Teoria das Restrições · ARA — Árvore da Realidade Atual · NC — Nuvem de Conflito ·
> UDE — Undesirable Effect (Efeito Indesejável) · DoD — Definition of Done (Definição de
> Pronto) · IA — inteligência artificial · P6 — princípio "Jornada viva" da constituição
> do projeto

> **Ciclo planejado no 001 — nenhuma caixa marcada porque nada foi executado.** O ciclo
> abre depois do gate humano do 001, com as duas precondições do
> [`../../docs/roadmap.md`](../../docs/roadmap.md) fechadas: a pergunta 1 da
> [`../../docs/produto/visao.md`](../../docs/produto/visao.md) §7 respondida e as specs
> de M1–M3 ratificadas ao menos em rascunho.

## Verificação primeiro

- [ ] T-01 — Fixar a DoD executável do ciclo (as 11 verificações da spec, incluindo a que
  prova que a captura regenera byte-idêntica do build). · Dep: — · Ref: `spec.md`
  § Critérios de aceite · Aceite: cada linha tem comando e saída esperada; nenhum
  critério subjetivo.

## Precondições (portão de abertura)

- [ ] T-02 — Registrar as respostas do gate 001 que entram como dado: pergunta 1 da visão
  §7, apetite da visão conflito+solução (RI-13), fonte dos `theme.tokens` de teste
  (Clarify da spec). · Dep: gate humano do 001 · Aceite: as três respostas escritas na
  spec (seção "O que entra como dado" emendada), nenhuma resolvida em silêncio.

## Fase 1 — Semântica antes de pixel (bloqueia a fase 2)

- [ ] T-03 — `ux-design.md`: papel semântico, estados obrigatórios e `ai_visible` de cada
  objeto de tela, com padrão **não visível** e justificativa escrita em cada `sim`. ·
  Dep: T-02 · Ref: RF-01, US-01 · Aceite: DoD linha 1.
- [ ] T-04 — Fixture sintética da "Instituição Horizonte" em `prototipo/dados/`: projeto,
  nós, arestas, UDEs **com estado de validação resolvido no dado**, NC completa (5
  entidades, 7 premissas, 1 injeção). · Dep: T-02 · Ref: RF-06, RI-11, RI-12 · Aceite:
  DoD linhas 3 e 4; nenhum nome real de pessoa.

## Fase 2 — Protótipo descartável (quatro condições cumulativas — F-01 da spec)

- [ ] T-05 — Esqueleto em `prototipo/` com os tokens dos dois temas (claro/escuro) e o
  adaptador falso do handshake devolvendo o envelope do guia da fundação. · Dep: T-03 ·
  Ref: RF-02, RF-09, RI-06 · Aceite: DoD linha 2; envelope com o mesmo formato de
  F-05 da spec.
- [ ] T-06 — Canvas + vista tabular equivalente, com alternância sem perda de estado e
  degradação digna em 420px. · Dep: T-04, T-05 · Ref: RI-01..RI-05, US-02, US-03 ·
  Aceite: as duas vistas mostram os mesmos dados da fixture; alternância preserva edição
  em curso.
- [ ] T-07 — Telas de ARA (UDEs com estado de validação vindo da fixture) e NC (forma
  canônica; visão conflito+solução só se o apetite couber — decisão registrada de T-02).
  · Dep: T-06 · Ref: RI-11..RI-13, US-04 · Aceite: nenhum estado calculado pelo
  protótipo (condição 2); premissas acessíveis pelas 7 arestas.
- [ ] T-08 — Casca de hospedeiro local com iframe: modo só-conteúdo, tema do inquilino
  aplicado por cima com *fallback* cobrindo os tokens ausentes, alternância
  autônomo/embarcado × claro/escuro × mesa/estreito. · Dep: T-05, T-06 · Ref: RF-08,
  RI-07..RI-10, US-05 · Aceite: DoD linhas 7 e 8.

## Fase 3 — A prova (P6)

- [ ] T-09 — Script versionado de captura em `prototipo/scripts/`; capturas
  determinísticas (fixture fixa, relógio congelado) em `docs/jornadas/capturas/`,
  regeneráveis byte-idênticas. · Dep: T-06..T-08 · Ref: RF-03, RNF-03 · Aceite: DoD
  linha 5 (duas execuções, `diff -r` limpo).
- [ ] T-10 — Documentos de jornada em versão de protótipo, cada um com avaliação
  heurística **datada** e limite declarado (feita por quem construiu);
  `docs/jornadas/README.md` atualizado com o estágio de cada J-NN. · Dep: T-09 · Ref:
  RF-04, RF-05 · Aceite: DoD linhas 6 e 10; nenhuma captura órfã.
- [ ] T-11 — Rodar a DoD completa e as aptidões do projeto; colar saída, código de saída
  e **tamanho do que cada uma examinou** no `qa-report.md`. · Dep: T-01..T-10 · Aceite:
  nenhuma linha do qa-report com `✓` transcrito sem a saída colada (R1/R2).

## Cauda de fechamento — OBRIGATÓRIA, uma linha cada, nunca apagar

<!-- TICK ONLY WHILE WRITING THE EVIDENCE, never in advance: the box records what happened.
     Do not delete a line to say it does not apply: write `n/a: <reason>` on it.
     check-conformance.sh requires the evidence of every non-n/a step in qa-report.md. -->
- [ ] TAIL:review — revisão independente em contexto fresco, por quem não construiu
  (inclui conferir que o protótipo não calcula nada — condição 2)
- [ ] TAIL:security — passe de segurança proporcional à classe de risco (aqui: dado real
  em fixture/captura, segredo ou provedor de modelo no cliente)
- [ ] TAIL:mutation — se algum portão novo nascer neste ciclo (ex.: conferidor de captura
  órfã), sabotá-lo de propósito e vê-lo recusar; se nenhum nascer, marcar `n/a` com o
  motivo
- [ ] TAIL:gate — DoD verde → veredito do guardião → gate humano de merge (indelegável)
