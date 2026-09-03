# Tasks 004 — Núcleo de diagramas (ciclo planejado)

> Siglas: TOC — Teoria das Restrições · ADR — Architecture Decision Record (Registro de
> Decisão Arquitetural) · DoD — Definition of Done (Definição de Pronto) · TDD —
> Test-Driven Development (desenvolvimento guiado por teste) · UI — interface de usuário
> · REST — Representational State Transfer · JSON — JavaScript Object Notation · OTel —
> OpenTelemetry · CI — integração contínua · i18n — internacionalização

> **Ciclo planejado no 001, não executado.** Nenhuma caixa se marca antes do fato; o
> aceite de cada tarefa é executável e a evidência vai para o `qa-report.md` com a saída
> colada (regra R1) e o tamanho examinado (regra R2).

## Verificação primeiro

- [ ] T-01 — Fixar a DoD executável do ciclo (as 14 linhas da spec § Critérios de
  aceite) nos caminhos reais do repositório. · Dep: — · Ref: `spec.md` § Critérios de
  aceite · Aceite: cada linha tem comando que roda no CI local; nenhum critério
  subjetivo.
- [ ] T-02 — Verificar a junta do ciclo 003 antes de qualquer código: introspecção
  respondendo, banco migrável, OTel exportando, CI verde. · Dep: T-01 · Ref: plan §
  Gates (DoR); `spec.md` L-01 · Aceite: a aptidão do 003 ("a junta fecha contra a
  ghdaru real") executada de novo neste ciclo, saída colada no qa-report.

## Fundações de teste (o teste nasce antes)

- [ ] T-03 — Contrato de `import-linter`: domínio e aplicação sem framework/banco/HTTP;
  o build falha na violação. · Dep: T-02 · Ref: RNF-02 · Aceite: `lint-imports` código 0;
  sabotagem (import de `fastapi` no domínio) derruba o build (`TAIL:mutation`).
- [ ] T-04 — Teste-testemunha do defeito da linhagem: excluir um nó remove exatamente o
  nó e as arestas incidentes, nada mais (o filtro invertido de
  `tocbuilderv3/services/mockApiService.ts:521` teria falhado aqui). Escrito **antes**
  do agregado, visto falhar, guardado vermelho. · Dep: T-03 · Ref: RF-15, RF-16; spec
  F-06 · Aceite: o commit do teste antecede o commit do código que o faz passar.

## Domínio (TDD estrito)

- [ ] T-05 — Agregado Projeto: entidades, objetos de valor, as 6 invariantes do
  `data-model.md` e os eventos somente-acréscimo — cada invariante com teste que falhou
  primeiro. · Dep: T-04 · Ref: `data-model.md`; RF-11..RF-20, RN-01..RN-06 · Aceite:
  DoD linhas 1 e 2; cobertura do domínio ≥ 85%.
- [ ] T-06 — Casos de uso e portas: criar/listar/abrir/editar projeto, lixeira
  (excluir suave, restaurar, definitivo), mutações de nó/aresta, histórico, reverter
  com `MutacaoCompensada`. · Dep: T-05 · Ref: RF-01..RF-10, RF-23..RF-26 · Aceite: DoD
  linha 3; teste de reverter mostra o evento compensatório correlacionado, nunca evento
  apagado.

## Serviço e política

- [ ] T-07 — Política por tipo de ação no servidor (aplica-com-desfazer |
  exige-confirmação | nasce-proposta), traço incondicional em toda mutação. · Dep: T-06
  · Ref: RF-21, RF-26; plan risco GATE-politica-por-origem · Aceite: DoD linhas 8 e 9;
  teste envia a mesma mutação por dois caminhos (UI simulada e chamada direta) e prova
  que a decisão veio da tabela de tipos, nunca de origem alegada.
- [ ] T-08 — Adaptadores: rotas REST de `contracts/rest-api.md`, repositório
  PostgreSQL, migrações Alembic com downgrade testado, isolamento por inquilino na
  consulta. · Dep: T-06 · Ref: INT-01, RNF-03, RNF-09 · Aceite: DoD linha 7; testes de
  contrato verdes; `alembic downgrade` executado e colado.
- [ ] T-09 — Exportação canônica e importação não destrutiva: JSON versionado
  determinístico; validação total antes de qualquer efeito; projeto novo com relato.
  · Dep: T-06 · Ref: RF-32..RF-36 · Aceite: DoD linhas 4, 5 e 6; sabotagem (aresta
  órfã no arquivo) recusada com relato por item (`TAIL:mutation`).

## Interface

- [ ] T-10 — Lista de projetos e lixeira (telas 6.1 e 6.2): estados vazio/erro/recusa
  desenhados; exclusão definitiva com confirmação nomeada. · Dep: T-08 · Ref: RI-01,
  RI-02, RI-12; RF-09 · Aceite: fluxo excluir→restaurar completo no navegador; recusa
  403 vira tela, não exceção.
- [ ] T-11 — Canvas e painel de entidades (telas 6.3 e 6.4): nós, arestas, raio da
  exclusão no controle, equivalência tabela↔canvas, foco cruzado, redimensionar.
  · Dep: T-10 · Ref: RI-03..RI-05, RI-07, RI-08, RF-27..RF-31 · Aceite: a mesma
  operação pelas duas vistas produz o mesmo evento de domínio (verificado por teste de
  integração); desempenho DoD da RNF-06 medido.
- [ ] T-12 — Desfazer de sessão e reverter na UI: pilha por episódio, atalho e botão
  nomeado, histórico com "Reverter <campo> para <valor>" (tela 6.6). · Dep: T-11 · Ref:
  RF-22..RF-25, RI-06 · Aceite: os dois defeitos-classe do ADR 0013 da irmã reproduzidos
  como teste e verdes (trocar de vista não descarta edição; desfazer após 10 episódios
  volta ao estado de abertura). **Primeira tarefa a sair se o apetite estourar** (round
  004) — o corte remove a UI, nunca os comandos inversos do domínio.
- [ ] T-13 — i18n pt/en em toda cadeia visível, tema do hospedeiro com fallback, modo
  só-conteúdo, identificador estável de tela (`data-tela-id`). · Dep: T-10..T-12 · Ref:
  RNF-08, RI-10, INT-02 · Aceite: DoD linha 11; captura nos dois temas e nas duas
  larguras.

## Jornada e fechamento

- [ ] T-14 — Jornada viva do M1: construir um diagrama sintético ("Instituição
  Horizonte") do zero — criar projeto, nós, arestas, tabela, desfazer, exportar,
  importar — com capturas geradas por script versionado do build real e avaliação
  heurística datada, no mesmo pull request. · Dep: T-11..T-13 · Ref: P6; DoD linha 12 ·
  Aceite: capturas regeneram determinísticas; base 100% sintética (ADR 0006).
- [ ] T-15 — Rodar TODAS as aptidões (DoD 14 linhas + portões do método) e colar saída,
  código de saída e tamanho examinado no `qa-report.md`; cobertura de requisitos linha a
  linha (RF/RI/RNF/RN/INT). · Dep: T-14 · Aceite: nenhuma linha com `✓` transcrito sem a
  saída colada (R1/R2).

## Cauda de fechamento

- [ ] T-16 — `TAIL:review` — revisão independente em contexto fresco por quem não
  implementou, com instrução explícita: conferir item 8 (política por tipo, nunca por
  origem), equivalência das vistas, e a seção Fontes da spec por amostragem. · Dep:
  T-15 · Aceite: veredito + achados e o que se fez com eles, no qa-report.
- [ ] T-17 — `TAIL:security` — passe de segurança: segredo no cliente, isolamento por
  inquilino, fail-closed sem capacidade, payload de importação, dado real vazado em
  fixture/captura. · Dep: T-15 · Aceite: resultado por item no qa-report.
- [ ] T-18 — `TAIL:mutation` — sabotar e ver recusar: import-linter (T-03), validação de
  importação (T-09), teste do filtro (T-04 com a regressão reintroduzida de propósito),
  teste de traço (mutação sem traço). · Dep: T-15 · Aceite: cada sabotagem com o comando
  e a recusa impressa, no qa-report.
- [ ] T-19 — `TAIL:gate` — gate humano: DoD verde apresentada, jornada revista, decisão
  de merge do Product Steward registrada. · Dep: T-16..T-18 · Aceite: registro do gate
  no qa-report e em `docs/records/decisoes.jsonl` via `scripts/record-decision.sh`.
