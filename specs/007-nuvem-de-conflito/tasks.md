# Tasks 007 — Nuvem de Conflito

> Siglas: **TOC** — Teoria das Restrições · **NC** — Nuvem de Conflito · **ADR** —
> Architecture Decision Record (Registro de Decisão Arquitetural) · **DoD** —
> Definition of Done (Definição de Pronto) · **TDD** — Test-Driven Development
> (desenvolvimento guiado por teste) · **FSM** — máquina de estados finitos · **UI** —
> interface de usuário · **IA** — inteligência artificial · **OTel** — OpenTelemetry ·
> **JSON** — JavaScript Object Notation · **TRIZ** — Teoria da Resolução Inventiva de
> Problemas · **i18n** — internacionalização.
>
> Ciclo **planejado** — nenhuma caixa marcada antes do fato (as marcações abaixo são
> todas vazias de propósito). Ordem TDD: em toda tarefa de código, o teste vermelho vem
> antes da implementação — e neste ciclo os testes vermelhos centrais são as
> invariantes da topologia fixa (T-04) e a prova de recusa intacta (T-09), que nascem
> antes do agregado e da integração.

## Verificação primeiro

- [ ] T-01 — Fixar a DoD executável do ciclo (as 16 linhas da spec, com comando e valor
  esperado) e conferir as pré-condições do roadmap: ciclos 004 **e 006** promovidos,
  spec com as 7 premissas modeladas. · Dep: — · Ref: `spec.md` § Critérios de aceite;
  `docs/roadmap.md` § "O que o ciclo 007 não pode começar sem" · Aceite: cada linha tem
  comando; nenhum critério subjetivo; pré-condições coladas no `qa-report.md`.

- [ ] T-02 — Consolidar `data-model.md` (extensão do modelo do M1: NuvemDeConflito de
  topologia fixa, EntidadeDaNuvem, ArestaDaNuvem, Premissa, Injecao, referências de
  costura, eventos) e `contracts/rest-api.md` estendendo os recursos do M1. ·
  Dep: T-01 · Ref: spec § Entidades; plan § Artefatos (`ART:data-model=yes`,
  `ART:contracts=yes`) · Aceite: todo agregado/evento da spec aparece no documento;
  nenhuma entidade sem invariante escrita; campos de costura anuláveis e sem regra.

- [ ] T-03 — Escrever o **schema JSON versionado** do ResultadoDeGeracao
  (`contracts/resultado-geracao.schema.json`) e declarar as 3 ações `toc.*`
  (`contracts/acoes-catalogo.md`): nome, classe de risco, `input_schema`, saída, o que
  nasce `action_proposal`. · Dep: T-02 · Ref: INT-02..INT-04; RF-21, RF-29; ADR 0007 ·
  Aceite: o schema cobre 5 entidades, racional, premissas pelas 7 chaves e injeções por
  premissa; `grep -c "toc\." contracts/acoes-catalogo.md` ≥ 3; nenhuma rota fora da FSM
  do 006.

## Domínio da nuvem (E3.1 + E3.2 — funciona inteiro sem catálogo)

- [ ] T-04 — Fixture sintética do dilema da "Instituição Horizonte" + testes de
  invariante vermelhos: criação atômica (5 entidades, 7 arestas), recusa de
  criar/excluir entidade ou aresta, injeção sem premissa recusada. **Nenhum agregado
  antes disto.** · Dep: T-02 · Ref: RN-01, RN-04; spec F-01, F-02 · Aceite: DoD 2 e 3
  vermelhos pelo motivo certo (agregado inexistente); zero dado real de pessoa
  (ADR 0006).

- [ ] T-05 — Domínio da nuvem: agregado com topologia fixa, edição de entidade e
  racional, premissas por aresta (ordenadas, estado `vigente`/`desafiada`,
  arquivamento propagando às injeções com contagem), completude por função pura. TDD
  sobre a fixture. · Dep: T-04 · Ref: RF-02..RF-08, RF-12..RF-15; RN-01..RN-03; plan §
  Decisão 1 e 4 · Aceite: DoD 1 e 2 verdes; leitura por extenso das 4 classes de aresta
  coberta por teste (RF-07).

- [ ] T-06 — Injeções: referência obrigatória a premissa, FSM `candidata → escolhida |
  descartada` com retorno justificado, classificação TRIZ, cobertura das 5 separações
  para D↯D′, ReferenciaDeSemeadura vazia ao escolher. TDD. · Dep: T-05 · Ref:
  RF-16..RF-20; RN-04, RN-07, RN-08 · Aceite: DoD 3 e 4 verdes; teste prova que
  arquivar premissa arquiva as injeções ligadas e nenhuma outra.

- [ ] T-07 — Heurísticas de formulação: léxico pt/en como dado versionado
  (substantivo em A/B/C, infinitivo em D/D′, negação de D em D′) + corpus sintético de
  entidades bem e mal formuladas, `indeterminado` honesto. TDD sobre o corpus,
  reusando o mecanismo do M2. · Dep: T-02 · Ref: RF-09..RF-11; RN-06; RNF-08 · Aceite:
  DoD 8 — a saída diz quantos casos bons/maus examinou (R2); aviso nunca bloqueia
  gravação.

- [ ] T-08 — Migrações Alembic (nuvem, premissa, injeção, referências de costura como
  colunas anuláveis) com `upgrade` **e** `downgrade` testados; repositórios mantendo o
  isolamento por inquilino do M1. · Dep: T-02 · Ref: spec § Entidades; plan § Decisão
  6 · Aceite: ciclo upgrade→downgrade sem resíduo, saída colada; teste de isolamento do
  004 verde sobre as tabelas novas.

## Borda da geração (E3.3 — cliente da FSM do 006)

- [ ] T-09 — Borda da geração: validador do schema no servidor (falha fechada com erro
  legível e traço), roteamento proposta completa × granular por estado da nuvem,
  integração com a FSM do 006, e a **prova de recusa intacta** — teste que serializa o
  projeto, recusa a proposta e compara byte a byte. · Dep: T-03, T-05, T-06 · Ref:
  RF-21..RF-27; RN-05; plan § Decisões 2 e 3 · Aceite: DoD 5, 6 e 13 verdes; DoD 7
  (nenhum parse de markdown no caminho) com grep colado; capability ausente esconde as
  3 mutadoras.

- [ ] T-10 — Casos de uso + adaptadores REST (editar entidade/racional, premissas,
  injeções, status, geração) com traço OTel por mutação — mutação de proposta aceita
  carrega o identificador da proposta — e autorização fail-closed. · Dep: T-05..T-08 ·
  Ref: RF-25; RNF-03; contratos do T-02 · Aceite: DoD 11 — teste falha se
  `PremissaRegistrada`, `InjecaoRegistrada` ou `GeracaoAplicada` não emitirem traço.

## Interface (sobre o ux-design do ciclo 002)

- [ ] T-11 — UI do canvas da NC: layout canônico fixo, notação das arestas (perigo
  tracejado + rótulo, conflito com raio), edição direta de entidade e racional, avisos
  de formulação no nó, progresso de completude no cabeçalho. · Dep: T-10 · Ref:
  RI-01, RI-02, RI-05, RI-09; RF-05 · Aceite: teste de fluxo de edição direta; aviso
  some quando o texto vira forma canônica; i18n sem literal solto.

- [ ] T-12 — UI da ficha de aresta + vista tabular: leitura por extenso, premissas
  ordenadas com estado, injeções agrupadas por premissa com status e TRIZ, matriz
  aresta × premissas × injeções com paridade de edição. · Dep: T-10 · Ref: RI-03,
  RI-04, RI-10; RF-19, RF-34 · Aceite: teste de fluxo feliz e de arquivamento com
  aviso quantificado; paridade tabela × diagrama coberta.

- [ ] T-13 — UI do fluxo de geração + visão conflito+solução: pré-visualização em diff
  na bandeja do 006, aceitar/recusar com mesmo peso, visão espelhada com as **7**
  posições de injeção (pendência explícita onde faltar), foco cruzado
  injeção ↔ premissa, cobertura TRIZ do conflito. · Dep: T-09, T-10 · Ref: RI-06..
  RI-08; RF-30..RF-32 · Aceite: DoD 9 — as 7 posições renderizadas, incluindo D_C e
  D_D_PRIME (o defeito do v3 como caso de teste); identificadores de tela
  (`toc.nc_canvas`, `toc.nc_aresta`, `toc.nc_solucao`, `toc.nc_tabela`) registrados
  com `ai_visible` campo a campo (INT-07).

- [ ] T-14 — Jornada viva: o dilema sintético da "Instituição Horizonte" de ponta a
  ponta — narrativa → proposta → **recusa** → nova proposta → aceite → premissa
  desafiada → injeções com TRIZ → injeção escolhida — capturas geradas por script
  versionado do build real + avaliação heurística datada, no mesmo pull request. ·
  Dep: T-11..T-13 · Ref: spec § Entregáveis (P6); ADR 0006 · Aceite: DoD 14 — script em
  `docs/jornadas/scripts/`, grep negativo de nome real de pessoa.

- [ ] T-15 — Rodar as aptidões e preencher o `qa-report.md`: as 16 linhas da DoD com
  saída colada (R1) e quanto cada portão examinou (R2); atualizar CHANGELOG; ADR novo
  se o Clarify tiver gerado decisão material. · Dep: T-14 · Ref: DoD 15 e 16 · Aceite:
  `scripts/check-conformance.sh 007` código 0; nenhuma célula do qa-report preenchida
  sem comando executado.

## Cauda (fechamento — nenhuma marcada antes da evidência no qa-report)

- [ ] TAIL:review — Revisão independente em contexto fresco (quem executou não revisa):
  spec × código × DoD, com os dois portões nomeados do roadmap — **invariantes da
  nuvem por teste de domínio** e **recusar deixa o projeto intacto** — verificados por
  leitura e por execução, achados registrados. · Dep: T-01..T-15

- [ ] TAIL:security — Passagem de segurança em contexto fresco: nenhum SDK, chave ou
  prompt no produto (DoD 12), validação de schema no servidor (RNF-04), autorização
  fail-closed nas rotas novas, capability ausente esconde as mutadoras (DoD 13),
  narrativa colada tratada como camada não-confiável no snapshot (INT-07). ·
  Dep: T-09, T-10

- [ ] TAIL:mutation — Testes de mutação sobre as invariantes da topologia, a referência
  injeção → premissa, a FSM de status e o validador de schema — as funções cuja falha
  silenciosa corrompe a nuvem ou deixa passar geração inválida; taxa e sobreviventes no
  `qa-report.md`. · Dep: T-05, T-06, T-09

- [ ] TAIL:gate — Portão humano de merge com as evidências das 16 linhas da DoD, as
  respostas dos 5 `[DÚVIDA]` e a cauda acima. · Dep: tudo
