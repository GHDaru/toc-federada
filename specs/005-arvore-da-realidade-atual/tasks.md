# Tasks 005 — Árvore da Realidade Atual

> Siglas: **TOC** — Teoria das Restrições · **ARA** — Árvore da Realidade Atual · **UDE**
> — Efeito Indesejável (*Undesirable Effect*) · **ADR** — Architecture Decision Record
> (Registro de Decisão Arquitetural) · **DoD** — Definition of Done (Definição de
> Pronto) · **TDD** — Test-Driven Development · **FSM** — máquina de estados finitos ·
> **UI** — interface de usuário · **IA** — inteligência artificial · **OTel** —
> OpenTelemetry · **i18n** — internacionalização.
>
> Ciclo **planejado** — nenhuma caixa marcada antes do fato (as marcações abaixo são
> todas vazias de propósito). Ordem TDD: em toda tarefa de código, o teste vermelho vem
> antes da implementação — e neste ciclo o teste vermelho central é o corpus de UDEs
> (T-04), que nasce antes de qualquer heurística.

## Verificação primeiro

- [ ] T-01 — Fixar a DoD executável do ciclo (as 14 linhas da spec, com comando e valor
  esperado) e conferir a pré-condição do roadmap: ciclo 004 promovido, critérios
  transcritos com partição decidível × julgamento. · Dep: — · Ref: `spec.md` § Critérios
  de aceite; `docs/roadmap.md` § "O que o ciclo 005 não pode começar sem" · Aceite: cada
  linha tem comando; nenhum critério subjetivo; pré-condições coladas no `qa-report.md`.

- [ ] T-02 — Consolidar `data-model.md` (extensão do modelo do M1: FichaDeUde,
  ValidacaoFormal, ParecerDeJulgamento, FSM de status, ExameDeElo, ConectorE, eventos) e
  `contracts/rest-api.md` estendendo os recursos do M1. · Dep: T-01 ·
  Ref: spec § Entidades; plan § Artefatos (`ART:data-model=yes`, `ART:contracts=yes`) ·
  Aceite: todo agregado/evento da spec aparece no documento; nenhuma entidade sem
  invariante escrita; contratos sem rota de execução de ação de IA.

- [ ] T-03 — Declarar as 5 ações `toc.*` (`contracts/acoes-catalogo.md`): nome, classe
  de risco, `input_schema`, saída, o que nasce `action_proposal` — a entrada do ciclo
  006. · Dep: T-02 · Ref: INT-02..INT-06; RF-32..RF-37; ADR 0007 · Aceite: DoD 10 —
  `grep -c "toc\." contracts/acoes-catalogo.md` ≥ 5; nenhuma rota de execução no
  serviço.

## Validação formal (E2.1 — o coração do ciclo)

- [ ] T-04 — Corpus sintético de UDEs versionado (bons, maus e adversariais, pt e en) +
  os 3 casos canônicos da linhagem como teste vermelho. **Nenhuma heurística antes
  disto.** · Dep: T-02 · Ref: RF-12, RNF-07; spec F-02 · Aceite: DoD 2 e 4 vermelhos
  pelo motivo certo (função inexistente), com contagem de casos na saída; zero dado real
  de pessoa (ADR 0006).

- [ ] T-05 — Validação formal: função pura por critério decidível (RN-01..RN-06) +
  léxico pt/en como dado versionado + veredito `indeterminado` honesto. TDD sobre o
  corpus. · Dep: T-04 · Ref: RF-06..RF-12; plan § Decisão 1-3 · Aceite: DoD 1, 2 e 4
  verdes; DoD 3 (grep de prompt no domínio = 0); golden test pronto para a porta do
  cliente.

- [ ] T-06 — FSM de status (`Pendente → Requer Refinamento → Validado | Rejeitado`) +
  ParecerDeJulgamento somente-acréscimo com autor tipado; reabertura com justificativa.
  · Dep: T-05 · Ref: RF-13..RF-17; RN-10 · Aceite: DoD 5 — `Validado` recusado com
  decidível vermelho ou sem parecer humano; parecer nunca sobrescrito (teste de
  imutabilidade).

## Construção da árvore (E2.2)

- [ ] T-07 — Domínio da árvore: tipo de projeto `ara`, marcador UDE + FichaDeUde,
  exame de elo (4 estados, reserva obrigatória), conector E com invariantes. TDD. ·
  Dep: T-02 · Ref: RF-01..RF-05, RF-18..RF-25; RN-11 · Aceite: DoD 6; invariantes do M1
  intactas (suíte do 004 continua verde); reavaliação automática ao editar texto
  (RF-10) coberta.

- [ ] T-08 — Análise estrutural: função pura sobre o grafo (fragmentos, entradas,
  alcance transitivo, elos não examinados, ciclos, causa raiz candidata fora de ciclo).
  TDD sobre grafos de fixture, incluindo grafo com ciclo e com 2 fragmentos. ·
  Dep: T-07 · Ref: RF-26..RF-31; RN-12 · Aceite: DoD 7 e 8; desempenho do RNF-06 medido
  em teste com grafo de 200 nós, saída colada.

- [ ] T-09 — Migrações Alembic (ficha, parecer, exame, conector) com `upgrade` **e**
  `downgrade` testados; repositórios estendidos mantendo isolamento por inquilino do
  M1. · Dep: T-02 · Ref: spec § Entidades; herança RNF-09 do M1 · Aceite: ciclo
  upgrade→downgrade sem resíduo, saída colada; teste de isolamento do 004 verde sobre as
  tabelas novas.

- [ ] T-10 — Casos de uso + adaptadores REST (marcar UDE, validar, parecer, status,
  examinar elo, conector, relatório) com traço OTel por mutação e autorização por
  capability fail-closed. · Dep: T-05, T-06, T-07, T-09 · Ref: RNF-03; contratos do
  T-02 · Aceite: DoD 9 — teste falha se `UdeMarcado`, `ParecerRegistrado` ou
  `EloExaminado` não emitirem traço.

## Interface (sobre o ux-design do ciclo 002)

- [ ] T-11 — UI da ficha de validação: duas seções (decidíveis com trecho apontado
  inline · julgamento com pareceres), fluxo reprovar → editar → reavaliar na mesma
  superfície, resposta < 1 s. · Dep: T-10 · Ref: RI-02..RI-04; RNF-04, RNF-05 ·
  Aceite: teste de fluxo feliz e de reprovação; medição do ciclo editar→reavaliar
  registrada.

- [ ] T-12 — UI do canvas ARA: selo UDE com status (cor + texto), exame de elo na
  aresta, conector E como elipse, resumo por status no cabeçalho com filtro na tabela.
  · Dep: T-10 · Ref: RI-01, RI-05, RI-06, RI-09; RF-04 · Aceite: teste de fluxo por
  estado de exame; i18n sem literal solto (aptidão herdada do M1).

- [ ] T-13 — UI do relatório estrutural: painel lateral com seções recolhíveis e ação de
  foco por item; identificadores de tela registráveis (`toc.ara_canvas`,
  `toc.ude_ficha`, `toc.ara_relatorio`) com `ai_visible` campo a campo. · Dep: T-08,
  T-10 · Ref: RI-07, RI-10; INT-07 · Aceite: foco centraliza o elemento; grep dos
  identificadores de tela na saída.

- [ ] T-14 — Jornada viva: construção de uma ARA sintética completa da "Instituição
  Horizonte" — primeiro UDE reprovado e reformulado, causas, exame de elos, conector E,
  relatório com causa raiz candidata — capturas geradas por script versionado do build
  real + avaliação heurística datada, no mesmo pull request. · Dep: T-11..T-13 ·
  Ref: spec § Entregáveis (P6); ADR 0006 · Aceite: DoD 12 — script em
  `docs/jornadas/scripts/`, grep negativo de nome real de pessoa.

- [ ] T-15 — Rodar as aptidões e preencher o `qa-report.md`: as 14 linhas da DoD com
  saída colada (R1) e quanto cada portão examinou (R2); atualizar CHANGELOG; ADR novo
  se o Clarify tiver gerado decisão material. · Dep: T-14 · Ref: DoD 13 e 14 ·
  Aceite: `scripts/check-conformance.sh 005` código 0; nenhuma célula do qa-report
  preenchida sem comando executado.

## Cauda (fechamento — nenhuma marcada antes da evidência no qa-report)

- [ ] TAIL:review — Revisão independente em contexto fresco (quem executou não revisa):
  spec × código × DoD, com o portão nomeado do roadmap — **nenhum critério de UDE
  dependente de prompt** — verificado por leitura e por grep, achados registrados. ·
  Dep: T-01..T-15

- [ ] TAIL:security — Passagem de segurança em contexto fresco: nenhuma rota de execução
  de ação de IA (DoD 10), nenhum prompt/chave/SDK no produto (DoD 3 e 11), autorização
  fail-closed nas rotas novas, capability ausente esconde ação mutadora no contrato
  (RF-37). · Dep: T-03, T-10

- [ ] TAIL:mutation — Testes de mutação sobre a validação formal (léxico e vereditos), a
  FSM de status e a análise estrutural — as funções cuja falha silenciosa compromete a
  análise inteira; taxa e sobreviventes no `qa-report.md`. · Dep: T-05, T-06, T-08

- [ ] TAIL:gate — Portão humano de merge com as evidências das 14 linhas da DoD, as
  respostas dos 5 `[DÚVIDA]` e a cauda acima. · Dep: tudo
