# Tasks 003 — Esqueleto federado

> Siglas: **APH** — Aplicação ↔ Harness · **ADR** — Architecture Decision Record
> (Registro de Decisão Arquitetural) · **DoD** — Definition of Done · **OTel** —
> OpenTelemetry · **CI** — integração contínua · **TDD** — Test-Driven Development ·
> **TOC** — Teoria das Restrições.
>
> Ciclo **planejado** — nenhuma caixa marcada antes do fato (as marcações abaixo são
> todas vazias de propósito). Raia infra: as tarefas de reversibilidade (T-07, T-15) são
> entrega, não cerimônia. Ordem TDD: em toda tarefa de código, o teste vermelho vem
> antes do adaptador.

## Verificação primeiro

- [ ] T-01 — Fixar a DoD executável do ciclo (as 14 linhas da spec, com comando e valor
  esperado) e o roteiro do ensaio "junta fecha contra a `ghdaru` real". · Dep: — ·
  Ref: `spec.md` § Critérios de aceite · Aceite: cada linha tem comando; nenhum critério
  subjetivo; o roteiro do DoD 12 lista as evidências a colar.

- [ ] T-02 — Re-medir os três bloqueios externos (L-01 schemas do manifesto, L-02
  `FEDERATION_MANIFESTS_ENABLED`, L-03 grants em memória) contra o commit atual da
  fundação e do normativo, **com saída colada**. · Dep: — · Ref: `spec.md` § Lacunas ·
  Aceite: as três medições no `qa-report.md` com `arquivo:linha` e data; decisão
  registrada se L-01 persistir ([DÚVIDA] 5).

## Identidade e admissão (E7.1)

- [ ] T-03 — Admissão fail-fast: teste por parâmetro ausente (6 códigos do contrato) →
  função pura `admitir(env)` → `main` que sai com código ≠ 0 nomeando o que faltou. ·
  Dep: T-01 · Ref: RF-01..RF-05, `contracts/parametros-de-admissao.md` · Aceite: DoD 1;
  nenhuma porta aberta após recusa.

- [ ] T-04 — Porta de identidade (`IdentityPort`) com retorno tipado
  (Principal | GrantInativo | FundacaoIndisponivel | CredencialRecusada) e adaptador
  falso para teste. · Dep: T-03 · Ref: RF-07, RF-12, RNF-03; plan § Decisão 1 e 5 ·
  Aceite: DoD 2 e 4 — payload forjado não produz Principal; exceção nunca vira acesso.

- [ ] T-05 — Adaptador de introspecção real: `POST {HOST_BASE_URL}/auth/introspect` com
  `Authorization: Bearer`, troca imediata, grant descartado, 401 sem retry. ·
  Dep: T-04 · Ref: RF-06, RF-08..RF-11, RNF-01 · Aceite: DoD 3 — introspecção chamada
  1×; grep negativo do grant em log e traço.

## Serviço e persistência (E8.1, E8.2)

- [ ] T-06 — Esqueleto FastAPI com OTel de nascença: middleware de traço, log
  estruturado com `trace_id`, métrica de descarte/admissão, exportador nulo sem
  coletor. · Dep: T-01 · Ref: RF-32..RF-35 · Aceite: DoD 10 parcial — todo endpoint com
  span; teste asserta a correlação.

- [ ] T-07 — Migração Alembic `0001` (tenant_ref, projeto) com `upgrade` **e**
  `downgrade`; ensaio em Neon limpo com **branch Neon criado antes** (GATE-migracao). ·
  Dep: T-06 · Ref: RF-28, RF-29, `data-model.md` · Aceite: DoD 8 — saída do ciclo
  upgrade→downgrade sem resíduo, colada.

- [ ] T-08 — Repositórios com isolamento por tenant (factory Postgres × in-memory por
  `DATABASE_URL`); teste com dois principais provando interseção vazia. · Dep: T-07 ·
  Ref: RF-30, RF-31 · Aceite: DoD 9.

- [ ] T-09 — Rota de leitura de projetos (sintéticos — ADR 0006), autorizada por
  `toc:read` do Principal, com span e seed de fixture. · Dep: T-05, T-08 ·
  Ref: RF-12, RF-27, RN-01, RNF-04 · Aceite: sem `toc:read`, lista vazia (US-03);
  fixture sem dado real (grep das personas).

## Embarque (E7.2)

- [ ] T-10 — Adaptador do canal `ghd.*` (módulo `federacao/` na interface), TDD a partir
  dos três contraexemplos da norma: envelope divergente ignorado, `ev.source` +
  `ev.origin` verificados nesta ordem, `targetOrigin` sempre `HOST_ORIGIN`, `ghd.ready`
  primeiro, `type` desconhecido ignorado, descarte registrado. · Dep: T-03 ·
  Ref: RF-14..RF-23 · Aceite: DoD 5, 6 e 7.

- [ ] T-11 — Telas de estado de fronteira (aguardando handshake · sem canal ·
  `GRANT_INATIVO` · `FUNDACAO_INDISPONIVEL`) — nunca frame branco, sem detalhe interno,
  `aria-live`. · Dep: T-10 · Ref: RI-01, RI-02, RI-05; spec § 6.2 · Aceite: teste de
  fluxo por estado; janela de 6 s dispara "sem canal".

- [ ] T-12 — Modo conteúdo + tema: sinal explícito de embarque na URL, zero cromo
  próprio, `theme.tokens` por lista de permissão com fallback completo claro/escuro;
  modo autônomo de desenvolvimento visivelmente distinto. · Dep: T-10 · Ref: RF-24..
  RF-26, RI-03, RI-04, RI-08 · Aceite: teste com tokens parciais — nenhum elemento sem
  cor; heurística na jornada (T-17).

## Deploy, CI e junta real (E8.5)

- [ ] T-13 — CI: suíte de testes, `import-linter` (fronteiras porta/adaptador e módulo
  `federacao/`), aptidões do projeto, grep de segredo (DoD 13) — tudo em pull request,
  vermelho bloqueia. · Dep: T-06, T-10 · Ref: RF-38, RNF-09, RNF-10 · Aceite: pipeline
  < 10 min; execução de exemplo colada.

- [ ] T-14 — Deploy: serviço no Railway, interface na Vercel, no endereço aprovado pelo
  portão humano ([DÚVIDA] 1); comparação de eTLD+1 com o hospedeiro colada. ·
  Dep: T-13, gate do endereço · Ref: RF-36 · Aceite: DoD 11.

- [ ] T-15 — Ensaio de rollback (GATE-deploy): reverter interface e serviço ao deploy
  anterior, documentar o procedimento em `docs/operacao/rollback.md`, colar a saída. ·
  Dep: T-14 · Ref: RF-39 · Aceite: DoD 14.

- [ ] T-16 — Manifesto (`mode: embedded`, `app_id: toc`, `capabilities_required` conforme
  [DÚVIDA] 3, `url`/`origin` do deploy) validado contra o schema normativo **e** o golden
  da fundação; submissão à rota real de administração. · Dep: T-02, T-14 ·
  Ref: RF-37; L-01/L-02 · Aceite: DoD 12 — aceito com resposta colada, **ou** L-01
  re-medido + T-19.

- [ ] T-17 — Jornada viva do embarque: fluxo feliz + três falhas, capturas geradas por
  script versionado do build embarcado, avaliação heurística datada, no mesmo pull
  request. · Dep: T-11, T-12, T-14 · Ref: RI-07 (P6) · Aceite: script em
  `docs/jornadas/scripts/`, capturas referenciadas na jornada.

- [ ] T-18 — Medição do embarque: tempo `ghd.ready` → lista renderizada extraído do
  traço OTel de embarques reais; registrar baseline (L-06) para o gate calibrar o alvo
  do RNF-06. · Dep: T-14, T-17 · Ref: RNF-06 · Aceite: números medidos no
  `qa-report.md`, não estimados.

- [ ] T-19 — Mensagens externas (somente se T-02 confirmar L-01 e/ou L-02):
  `mensagens/NNN-para-ghdaru-*` e/ou `mensagens/NNN-para-protocolos-*`, com evidência
  por `arquivo:linha`, referenciando a mensagem 005 da irmã. · Dep: T-02, T-16 ·
  Ref: P1 (relatar e parar) · Aceite: mensagem no formato de `mensagens/README.md`;
  nenhuma escrita externa.

## Cauda (fechamento — nenhuma marcada antes da evidência no qa-report)

- [ ] TAIL:review — Revisão independente em contexto fresco (quem executou não revisa):
  spec × código × DoD, com achados registrados. · Dep: T-01..T-18
- [ ] TAIL:security — Passagem de segurança em contexto fresco sobre admissão, canal e
  introspecção (GATE-seguranca — a irmã achou quatro furos na dela; procurar os nossos,
  não celebrar a ausência). · Dep: T-03..T-05, T-10
- [ ] TAIL:mutation — Testes de mutação sobre a lógica de admissão e de verificação de
  fonte/origem (as funções cuja falha silenciosa custa mais); taxa e sobreviventes no
  `qa-report.md`. · Dep: T-03, T-10
- [ ] TAIL:gate — Portão humano de merge com as evidências das 14 linhas da DoD, dos 5
  gates de reversibilidade e da cauda acima. · Dep: tudo
