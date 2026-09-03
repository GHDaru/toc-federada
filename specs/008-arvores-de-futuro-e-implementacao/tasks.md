# Tasks 008 — Árvores de Futuro e Implementação

> Siglas: **TOC** — Teoria das Restrições · **ARA** — Árvore da Realidade Atual · **UDE**
> — Efeito Indesejável (*Undesirable Effect*) · **NC** — Nuvem de Conflito · **ARF** —
> Árvore da Realidade Futura · **APR** — Árvore de Pré-Requisitos · **AT** — Árvore de
> Transição · **OI** — Objetivo Intermediário · **ED** — Efeito Desejável · **ADR** —
> Architecture Decision Record (Registro de Decisão Arquitetural) · **DoD** — Definition
> of Done (Definição de Pronto) · **TDD** — Test-Driven Development · **FSM** — máquina
> de estados finitos · **UI** — interface de usuário · **UX** — experiência de usuário ·
> **IA** — inteligência artificial · **OTel** — OpenTelemetry · **REST** —
> Representational State Transfer · **SDK** — Software Development Kit (kit de
> desenvolvimento) · **i18n** — internacionalização.
>
> Ciclo **planejado** — nenhuma caixa marcada antes do fato (as marcações abaixo são
> todas vazias de propósito). Ordem TDD: em toda tarefa de código, o teste vermelho vem
> antes da implementação — e neste ciclo o teste vermelho central é o da **cadeia
> inteira** (T-05), que nasce antes de existir promoção, semeadura ou derivação.

## Verificação primeiro

- [ ] T-01 — Fixar a DoD executável do ciclo (as 16 linhas da spec, com comando e valor
  esperado) e conferir as pré-condições do roadmap: ciclos 005 e 007 promovidos, FSM do
  006 no ar, decisão registrada sobre ramos negativos manuais. · Dep: — · Ref: `spec.md`
  § Critérios de aceite; `docs/roadmap.md` § "O que o ciclo 008 não pode começar sem" ·
  Aceite: cada linha tem comando; nenhum critério subjetivo; pré-condições coladas no
  `qa-report.md`.

- [ ] T-02 — Consolidar `data-model.md` (extensões ARF/APR/AT do agregado Projeto:
  papéis, EspelhoDeUde, RamoNegativo, ParObstaculoOI, ElipseDeSimultaneidade,
  FichaDePasso; agregado novo ReferenciaCruzada; eventos) e `contracts/`: REST dos três
  tipos + promoções/semeaduras/derivações + esquema de exportação com referências. ·
  Dep: T-01 · Ref: spec § Entidades; plan § Artefatos (`ART:data-model=yes`,
  `ART:contracts=yes`) · Aceite: todo agregado/evento da spec aparece no documento;
  nenhuma entidade sem invariante escrita; o esquema de exportação declara os elos
  `pendente` na importação parcial (INT-10).

- [ ] T-03 — Extrair o pacote de suficiência causal (exame de elo + conector E) do M2
  para módulo de domínio compartilhado, importado por ARA e ARF. · Dep: T-02 · Ref:
  RF-03; plan § Decisão 1; spec L-04 · Aceite: **a suíte do ciclo 005 continua verde**
  com saída colada; `lint-imports` código 0; nenhuma regra duplicada (grep do nome das
  classes extraídas aponta um único módulo de definição).

- [ ] T-04 — `ux-design.md` do M4: papel semântico antes do componente para canvas
  ARF/APR/AT, painel de ramos, tabela resumo e vista da cadeia; gate de UX antes de
  qualquer tarefa de UI. · Dep: T-02 · Ref: plan § Artefatos (`ART:ux-design=yes`);
  RI-01..RI-13 · Aceite: toda tela da spec § Telas e fluxos coberta; leitura de baixo
  para cima da APR (RI-04) e notação da elipse (RI-07) desenhadas; gate de UX
  registrado.

## O teste que define o ciclo

- [ ] T-05 — Escrever **vermelho** o teste de domínio da cadeia inteira com dados
  sintéticos da "Instituição Horizonte": cria UDE na ARA, valida, promove à NC, registra
  injeção, escolhe, semeia ARF, espelha ED, deriva obstáculo na APR, pareia OI,
  sequencia, deriva AT, conclui um passo — provando a referência de origem em cada elo.
  **Nenhuma operação de encadeamento antes disto.** · Dep: T-02 · Ref: DoD 1; round 008
  (aptidão executável); RN-11..RN-13 · Aceite: DoD 1 vermelho pelo motivo certo
  (operações inexistentes), com os 6 elos nomeados na saída; zero dado real de pessoa
  (ADR 0006).

## Domínio das três ferramentas (paralelizável por fronteira)

- [ ] T-06 — Domínio ARF: tipo de projeto `arf`, papéis de nó (injeção · efeito futuro),
  EspelhoDeUde com unicidade por UDE, RamoNegativo (FSM `aberto → tratado | aceito` com
  invariantes RN-04), VerificacaoDaARF pura. TDD. · Dep: T-02, T-03 · Ref: RF-01..RF-13;
  RN-01..RN-04 · Aceite: DoD 6; exame de elo e conector E funcionando na ARF via pacote
  compartilhado; DoD 8 (nenhuma rota assistida de ramo).

- [ ] T-07 — Domínio APR: tipo `apr`, papéis (objetivo único · obstáculo · OI), aresta
  de dependência sem leitura de suficiência, ParObstaculoOI com parecer de validade,
  ElipseDeSimultaneidade; **corpus sintético de obstáculos/OIs primeiro**, depois a
  verbalização avaliada (léxico pt/en, aviso nunca veta). TDD. · Dep: T-02 · Ref:
  RF-14..RF-22; RN-05, RN-07..RN-09 · Aceite: DoD 7 com contagem de casos na saída
  (R2); teste prova que projeto `apr` não oferece exame de suficiência (RN-05).

- [ ] T-08 — Sequenciamento: função pura sobre o grafo de OIs — camadas topológicas,
  ramos paralelos, elipses, ciclo como pendência bloqueante — e a tabela resumo na ordem
  das camadas. TDD sobre grafos de fixture, incluindo grafo com ciclo e com elipse. ·
  Dep: T-07 · Ref: RF-23..RF-27; RN-06 · Aceite: DoD 5; desempenho do RNF-04 medido em
  teste com 100 OIs / 200 dependências, saída colada.

- [ ] T-09 — Domínio AT: tipo `at`, FichaDePasso (tripla obrigatória, status com motivo/
  resultado real, divergência preservada em evento), precedência e passos inalcançáveis.
  TDD. · Dep: T-02 · Ref: RF-28..RF-32; RN-10 · Aceite: DoD 9; leitura "Para …, …;
  espero …" montada no domínio, coberta por teste.

## Encadeamento (E4.4 — nunca sai)

- [ ] T-10 — Agregado ReferenciaCruzada + operações de encadeamento: promoção UDE → NC
  (preenchendo ReferenciaDeOrigem da NC na mesma transação), semeadura injeção → ARF
  (ReferenciaDeSemeadura + nó semente), derivações ARF → APR e OI → AT; suspensão/
  reativação por exclusão suave (teste de propriedade RNF-09); VistaDaCadeia pura. TDD —
  **fica verde o T-05**. · Dep: T-05, T-06, T-07, T-09 · Ref: RF-33..RF-42; RN-11..
  RN-13; INT-02..INT-04 · Aceite: DoD 1, 2 e 3 verdes com saída colada; recusa de UDE
  não-`Validado` e injeção não-`escolhida` coberta.

- [ ] T-11 — Migrações Alembic (papéis, fichas, pares, elipses, ramos, referências) com
  `upgrade` **e** `downgrade` testados; repositórios, casos de uso e adaptadores REST
  dos três tipos + encadeamento, com traço OTel por mutação (identificador da referência
  no traço) e autorização por capability fail-closed. · Dep: T-06..T-10 · Ref: RNF-03,
  RNF-09, RNF-10; contratos do T-02 · Aceite: DoD 4 e 13; ciclo upgrade→downgrade sem
  resíduo, saída colada; isolamento por inquilino do 004 verde sobre as tabelas novas.

## Interface (sobre o ux-design deste ciclo — T-04)

- [ ] T-12 — UI do canvas ARF + painel de ramos negativos: papéis por forma e texto,
  selo de ED com UDE referenciado, resumo de cobertura, ramos por estado com
  justificativa/injeção a um clique. · Dep: T-04, T-11 · Ref: RI-01..RI-03; RF-05 ·
  Aceite: teste de fluxo feliz (espelhar, marcar, tratar) e de recusa (aceitar sem
  justificativa); i18n sem literal solto.

- [ ] T-13 — UI do canvas APR + tabela resumo: leitura de baixo para cima, obstáculo
  anotado na dependência, avisos de verbalização inline, camadas como faixas,
  elipse de simultaneidade, pendências de pareamento e ciclo destacadas. · Dep: T-04,
  T-11 · Ref: RI-04..RI-07; RF-25, RF-27 · Aceite: teste de fluxo por pendência
  (obstáculo sem OI, ciclo); tabela exportada confere com o sequenciamento.

- [ ] T-14 — UI do canvas AT + vista da cadeia + ações de encadeamento no contexto do
  elemento (promover no UDE validado, semear na injeção escolhida, derivar no efeito/OI):
  ficha do passo com leitura corrida, selos de origem/destino, elo `pendente` esmaecido
  com motivo, navegação por teclado. · Dep: T-04, T-11 · Ref: RI-08..RI-11; RF-42 ·
  Aceite: navegar da vista da cadeia abre a ferramenta com o elemento focado (teste de
  fluxo); identificadores de tela registrados (DoD 12).

- [ ] T-15 — Ações `toc.suggest_future_effects` / `toc.suggest_obstacles` /
  `toc.suggest_intermediate_objectives` / `toc.suggest_transition_steps` pela FSM do
  006: declaração no catálogo, prompts versionados no servidor, contexto de domínio
  anexado, propostas na bandeja, aceite criando com traço correlacionado; capability
  ausente esconde as quatro. · Dep: T-11 · Ref: RF-43..RF-45; INT-05..INT-08, INT-11 ·
  Aceite: DoD 10 — mutação direta recusada fail-closed; proposta de passo sem a tripla
  recusada por schema (INT-08); RI-12 coberta.

## Fechamento

- [ ] T-16 — Jornada viva: a análise sintética completa da "Instituição Horizonte" — UDE
  validado → promoção à NC → injeção escolhida → ARF semeada com ramo negativo tratado →
  APR derivada e sequenciada → AT com o primeiro passo concluído — capturas geradas por
  script versionado do build real + avaliação heurística datada, no mesmo pull request;
  inclui o caso de duas ARFs semeadas (plan, GATE-cadeia-linear). · Dep: T-12..T-15 ·
  Ref: spec § Entregáveis (P6); ADR 0006 · Aceite: DoD 14 — script em
  `docs/jornadas/scripts/`, grep negativo de nome real de pessoa.

- [ ] T-17 — Rodar as aptidões e preencher o `qa-report.md`: as 16 linhas da DoD com
  saída colada (R1) e quanto cada portão examinou (R2); os três portões do roadmap com
  evidência; atualizar CHANGELOG; ADR novo se decisão material surgir (candidata: a
  extração do pacote de suficiência, se mudar contrato do M2). · Dep: T-16 · Ref: DoD 15
  e 16 · Aceite: `scripts/check-conformance.sh 008` código 0; nenhuma célula do
  qa-report preenchida sem comando executado.

## Cauda (fechamento — nenhuma marcada antes da evidência no qa-report)

- [ ] TAIL:review — Revisão independente em contexto fresco (quem executou não revisa):
  spec × código × DoD, com os portões nomeados do roadmap — a cadeia percorrida com
  referência em cada elo, as três árvores exportáveis — verificados por leitura e por
  execução, achados registrados. · Dep: T-01..T-17

- [ ] TAIL:security — Passagem de segurança em contexto fresco: os dois regimes do item
  8 conferidos (mutação por proposta recusada fail-closed — DoD 10; manipulação direta
  com traço e reversibilidade — DoD 13); nenhum prompt/chave/SDK no produto (DoD 11);
  capability ausente esconde as mutadoras (RF-45); snapshot sanitizado cobre os campos
  novos (INT-09). · Dep: T-11, T-15

- [ ] TAIL:mutation — Testes de mutação sobre o sequenciamento (camadas e detecção de
  ciclo), a verificação da ARF (cobertura e ramos), a FSM do ramo negativo, o léxico de
  verbalização e a suspensão/reativação de referência — as funções cuja falha silenciosa
  quebra a cadeia inteira; taxa e sobreviventes no `qa-report.md`. · Dep: T-06..T-10

- [ ] TAIL:gate — Portão humano de merge com as evidências das 16 linhas da DoD, as
  respostas dos 5 `[DÚVIDA]` e a cauda acima. · Dep: tudo
