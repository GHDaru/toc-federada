# Tasks 001 — Fundação e planejamento (ciclo documental)

> Siglas: ADR — Architecture Decision Record · APH — Aplicação ↔ Harness · TOC — Teoria
> das Restrições · DoD — Definition of Done · DoR — Definition of Ready

## Verificação primeiro

- [x] T-01 — Fixar a DoD executável do ciclo (13 verificações com comando e valor
  esperado). · Dep: — · Ref: `spec.md` § Critérios de aceite · Aceite: cada linha da
  tabela tem comando e saída esperada; nenhum critério subjetivo.

## Leitura (fontes antes de escrita)

- [x] T-02 — Ler a linhagem `tocbuilderv3` (propósito, tipos, API mock, prompts) e
  extrair domínio + defeitos com `arquivo:linha`. · Dep: — · Aceite: F-01 da spec cita a
  violação canônica com a linha colada.
- [x] T-03 — Ler a norma APH (`padrao-aph.md`, Anexos A e B, schema do manifesto) e o guia
  do desenvolvedor de aplicação federada. · Dep: — · Aceite: F-02–F-04 citam nível, modo
  e introspecção por `arquivo:linha`.
- [x] T-04 — Ler o corpus da irmã (constituição, R1–R5, specs, ADRs 0012/0016), a spec 001
  do ECS e o gerador `spec-to-code-docs`. · Dep: — · Aceite: F-05 cita as regras herdadas
  por linha; as barras do gauntlet estão nomeadas no plan.

## Síntese

- [x] T-05 — Sintetizar o brief que amarra os construtores (identidade, taxonomia,
  módulos, roadmap, formatos, regras). · Dep: T-02..T-04 · Aceite: todo construtor lê o
  brief inteiro antes de escrever; o brief NÃO entra no repositório.

## Construção (lotes paralelos, sem sobreposição de caminho)

- [ ] T-06 — Identidade e governança: `CLAUDE.md` (preservando o bloco do instalador),
  `docs/governance/constitution.md` v1.0.0, `mensagens/README.md`, `LICENSE`,
  `THIRD-PARTY-NOTICES.md`, e os quatro arquivos reais deste ciclo. · Dep: T-05 ·
  Ref: RF-01..RF-04 · Aceite: DoD linhas 1, 2 e 11.
- [ ] T-07 — Produto e planejamento: `docs/produto/visao.md`, `docs/produto/modulos.md`,
  `docs/roadmap.md` (12 ciclos, portões, "não pode começar sem"). · Dep: T-05 ·
  Ref: RF-07..RF-09 · Aceite: DoD linha 6.
- [ ] T-08 — ADRs 0001–0008 no formato da irmã (Princípios tocados, alternativas com
  número executado, consequência negativa, "o que NÃO decide"), índice em
  `docs/adr/README.md` e linhas em `docs/records/decisoes.jsonl` via
  `scripts/record-decision.sh`. · Dep: T-05 · Ref: RF-05, RF-06 · Aceite: DoD linhas 3, 4.
- [ ] T-09 — Specs de módulo 002–012 (formato do brief §7: taxonomia, EARS, selos,
  Fontes, Lacunas, Clarify ≤ 5; plan com DUAS tabelas; tasks com cauda; qa-report vazio
  declarado). · Dep: T-05, T-07 · Ref: RF-10 · Aceite: DoD linhas 5, 7.
- [ ] T-10 — Portões novos: `scripts/check-caminhos.sh` (R4),
  `scripts/check-adrs-sucessao.sh` (R5), `scripts/check-specs.sh` (DoR ≥ 80) — cada um
  imprime **quanto examinou** (R2) e falha com código ≠ 0. · Dep: T-05 · Ref: RF-11 ·
  Aceite: DoD linhas 4, 7, 8.
- [ ] T-11 — Site: vendorizar o gerador em `tools/product-site/` com atribuição (ADR
  0008), adaptar para RI e vocabulário TOC, gerar `docs/product-site/`. · Dep: T-07,
  T-09 · Ref: RF-12 · Aceite: DoD linha 10.
- [ ] T-12 — `CHANGELOG.md` com a entrada desta fundação. · Dep: T-06..T-11 · Aceite:
  entrada em `[Unreleased]` citando o ciclo 001.

## Portões e crítica

- [ ] T-13 — Rodar TODAS as aptidões (método + as três novas + DoD completa) e colar
  saída, código de saída e tamanho examinado no `qa-report.md`. · Dep: T-06..T-12 ·
  Aceite: nenhuma linha do qa-report com `✓` transcrito sem a saída colada (R1/R2).
- [ ] T-14 — Gauntlet: críticos em contexto fresco comparam às cegas contra as três
  barras (corpus da irmã · ECS spec 001 · ECS product-site); perdeu → retrabalho dirigido
  pela maior lacuna nomeada, e o veredito entra no qa-report. · Dep: T-13 · Aceite:
  veredito por barra registrado.

## Cauda de fechamento — OBRIGATÓRIA, uma linha cada, nunca apagar

<!-- TICK ONLY WHILE WRITING THE EVIDENCE, never in advance: the box records what happened.
     Do not delete a line to say it does not apply: write `n/a: <reason>` on it.
     check-conformance.sh requires the evidence of every non-n/a step in qa-report.md. -->
- [ ] TAIL:review — revisão independente em contexto fresco, por quem não construiu
- [ ] TAIL:security — passe de segurança proporcional à classe de risco (aqui: vazamento
  de dado real e de segredo em texto)
- [ ] TAIL:mutation — cada portão criado neste ciclo (T-10), sabotado de propósito e
  visto recusando
- [ ] TAIL:gate — DoD verde → veredito do guardião → gate humano de merge (indelegável)
