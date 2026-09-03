# Tasks 010 — Estratégia & Táticas

> Siglas: **TOC** — Teoria das Restrições · **S&T** — Estratégia & Táticas (*Strategy
> & Tactics*) · **ADR** — Architecture Decision Record (Registro de Decisão
> Arquitetural) · **DoD** — Definition of Done (Definição de Pronto) · **TDD** —
> Test-Driven Development (desenvolvimento guiado por teste) · **UI** — interface de
> usuário · **UX** — experiência de usuário · **OTel** — OpenTelemetry · **i18n** —
> internacionalização · **REST** — Representational State Transfer (estilo de
> interface de programação sobre HTTP).
>
> Ciclo **planejado** — nenhuma caixa marcada antes do fato (as marcações abaixo são
> todas vazias de propósito). Ordem TDD: em toda tarefa de código, o teste vermelho
> vem antes da implementação — e neste ciclo os testes vermelhos centrais são a
> numeração derivada com renumeração (T-03/T-04) e a reprodução do defeito de exclusão
> da linhagem (F-07 da spec), que nascem antes do agregado.

## Verificação primeiro

- [ ] T-01 — Fixar a DoD executável do ciclo (as 16 linhas da spec, com comando e
  valor esperado) e conferir a pré-condição do roadmap: **ciclo 004 promovido**;
  conferir as respostas do Clarify que mudam modelo ([DÚVIDA] 1 — categoria) e
  artefatos ([DÚVIDA] 5 — ux). · Dep: — · Ref: `spec.md` § Critérios de aceite;
  `docs/roadmap.md` § "O que o ciclo 010 não pode começar sem" · Aceite: cada linha
  tem comando; nenhum critério subjetivo; pré-condição e respostas coladas no
  `qa-report.md`.

- [ ] T-02 — Consolidar `data-model.md` (extensão do modelo do M1: ArvoreSnT, PassoSnT
  com **pai + ordem** — sem campo de número —, PremissasDoPasso, StatusDoPasso,
  eventos) e `contracts/rest-api.md` estendendo os recursos do M1, com a ausência de
  número em rota de escrita como cláusula explícita. · Dep: T-01 · Ref: spec §
  Entidades; RF-06; plan § Artefatos (`ART:data-model=yes`, `ART:contracts=yes`) ·
  Aceite: todo agregado/evento da spec aparece no documento; nenhuma entidade sem
  invariante escrita; nenhum contrato de catálogo (INT-04).

## Domínio da árvore (E5.1 — o coração do resgate)

- [ ] T-03 — Fixture sintética da S&T "Dobrar a capacidade de atendimento" da
  Instituição Horizonte (3 níveis) + testes vermelhos: numeração 1/1.1/1.1.2 pela
  posição, renumeração ao inserir/mover/excluir, árvore estrita (mover para a própria
  subárvore recusado), **a reprodução do defeito de exclusão da linhagem** (excluir um
  passo → todos os demais permanecem — F-07) e a ida e volta das três premissas.
  Inclui um caso na forma do export do v3 (número digitado + arestas) para o contrato
  do 011. **Nenhum agregado antes disto.** · Dep: T-02 · Ref: RN-01, RN-02, RN-04,
  RN-05; DoD 2, 3, 5, 6, 7 · Aceite: DoD 2–7 vermelhos pelo motivo certo (agregado
  inexistente); zero dado real de pessoa (ADR 0006).

- [ ] T-04 — Função pura de numeração + renumeração local: raízes 1..n, filhos X.1..
  X.m, determinística e sem lacuna; renumeração da subárvore afetada e dos irmãos
  seguintes, com propriedade de equivalência contra o recálculo total. TDD sobre a
  fixture. · Dep: T-03 · Ref: RF-04, RF-05, RF-07; RN-01; RNF-05; plan § Decisões 1 e
  6 · Aceite: DoD 2 e 3 verdes; propriedade de determinismo e de equivalência na
  suíte.

- [ ] T-05 — Domínio da árvore: agregado ArvoreSnT com meta global, PassoSnT
  (estratégia obrigatória, tática como pendência), adicionar filho/irmão em posição,
  mover subárvore preservando conteúdo, excluir subárvore com contagem, as três
  premissas com regras de pendência, status com evento, PendenciasDaArvore. TDD. ·
  Dep: T-04 · Ref: RF-01..RF-03, RF-08..RF-18; RN-02..RN-06; plan § Decisões 2..5 ·
  Aceite: DoD 5, 6, 7 e 8 verdes; DoD 9 — a saída das pendências diz quantos passos
  examinou (R2).

- [ ] T-06 — Migrações Alembic (árvore, passo com pai+ordem, premissas, status) com
  `upgrade` **e** `downgrade` testados; repositórios mantendo o isolamento por
  inquilino do M1. · Dep: T-02 · Ref: spec § Entidades; RNF-01 · Aceite: ciclo
  upgrade→downgrade sem resíduo, saída colada; teste de isolamento do 004 verde sobre
  as tabelas novas.

## Borda e interface

- [ ] T-07 — Casos de uso + adaptadores REST (criar/editar, adicionar, mover, excluir
  subárvore, premissas, status) com traço OTel por mutação, autorização fail-closed e
  o desfazer de sessão do M1 estendido à exclusão de subárvore inteira. · Dep: T-04..
  T-06 · Ref: RF-15, RF-20, RF-21; RNF-03; contratos do T-02 · Aceite: DoD 4 (nenhum
  campo de número em rota de escrita, grep colado), 10 e 11 verdes; teste falha se
  `PassoAdicionado`, `PassoMovido`, `SubarvoreExcluida` ou `StatusMudou` não emitirem
  traço.

- [ ] T-08 — UI da árvore + ficha do passo: árvore com layout calculado de cima para
  baixo (meta no topo), nó com número + estratégia + status (forma e rótulo, nunca só
  cor), ações contextuais de adicionar (sem campo de número em formulário nenhum),
  ficha com estratégia/tática e as três premissas **nas posições de leitura** com
  leitura dirigida montada de pai e filhos. · Dep: T-07 (e adendo de ux se o [DÚVIDA]
  5 o criar) · Ref: RI-01..RI-04; RF-13; F-06 · Aceite: teste de fluxo de edição
  direta; leitura dirigida coberta por teste de UI; i18n sem literal solto.

- [ ] T-09 — UI da vista tabular + painel de acompanhamento: tabela indentada com
  paridade de edição, contagens por status como filtros acionáveis, pendências lógicas
  com salto direto, filtro mantendo ancestrais visíveis. · Dep: T-07 · Ref: RI-07,
  RI-08; RF-17..RF-19 · Aceite: paridade tabela × ficha coberta; filtro por status
  testado com ancestrais visíveis; identificadores de tela (`toc.snt_arvore`,
  `toc.snt_passo`, `toc.snt_tabela`, `toc.snt_acompanhamento`) registrados com
  `ai_visible` campo a campo (INT-02).

- [ ] T-10 — Mover por arrastar com pré-visualização de renumeração + exclusão com
  contagem e primeiro nível visível — os dois fluxos de mutação estrutural com a
  reversibilidade anunciada na própria confirmação. **Nota de apetite: se o E5.2 sair
  pelo corte, esta tarefa absorve o painel mínimo (contagem por status na árvore).** ·
  Dep: T-08, T-09 · Ref: RI-05, RI-06; RF-08, RF-09 · Aceite: pré-visualização mostra
  os números novos antes de confirmar; contagem da exclusão bate com o evento
  `SubarvoreExcluida`.

- [ ] T-11 — Jornada viva: a S&T sintética da Instituição Horizonte com **três
  níveis** — criar meta, decompor em passos numerados, preencher as três premissas nos
  três papéis, mover uma subárvore (renumeração à vista), conduzir a reunião por
  status e pendências — captura gerada por script versionado do build real +
  avaliação heurística datada, no mesmo pull request. · Dep: T-10 · Ref: spec §
  Entregáveis (P6); F-12; ADR 0006 · Aceite: DoD 14 — script em
  `docs/jornadas/scripts/`, grep negativo de nome real de pessoa.

- [ ] T-12 — Rodar as aptidões e preencher o `qa-report.md`: as 16 linhas da DoD com
  saída colada (R1) e quanto cada portão examinou (R2); medições de desempenho da
  jornada coladas (DoD 13); atualizar CHANGELOG; ADR da categoria não portada se o
  gate a confirmar ([DÚVIDA] 1). · Dep: T-11 · Ref: DoD 15 e 16 · Aceite:
  `scripts/check-conformance.sh 010` código 0; nenhuma célula do qa-report preenchida
  sem comando executado.

## Cauda (fechamento — nenhuma marcada antes da evidência no qa-report)

- [ ] TAIL:review — Revisão independente em contexto fresco (quem executou não
  revisa): spec × código × DoD, com os portões nomeados do roadmap — **teste de
  renumeração da subárvore** e **as três premissas persistidas e exibidas por nó** —
  verificados por leitura e por execução, achados registrados. · Dep: T-01..T-12

- [ ] TAIL:security — Passagem de segurança em contexto fresco: nenhum SDK, chave,
  prompt ou ação de catálogo no módulo (DoD 12, INT-04), autorização fail-closed nas
  rotas novas, isolamento por inquilino nas tabelas novas, textos de usuário marcados
  camada não-confiável no registro de telas (INT-02). · Dep: T-07, T-09

- [ ] TAIL:mutation — Testes de mutação sobre a função de numeração, a renumeração
  local, a invariante de árvore estrita e o recorte da exclusão de subárvore — as
  funções cuja falha silenciosa reintroduz os defeitos F-05 e F-07 da linhagem; taxa e
  sobreviventes no `qa-report.md`. · Dep: T-04, T-05

- [ ] TAIL:gate — Portão humano de merge com as evidências das 16 linhas da DoD, as
  respostas dos 5 `[DÚVIDA]` e a cauda acima — incluindo o registro de que a regressão
  D-05 está desfeita **com decisão registrada**, que é o que faltou à linhagem. ·
  Dep: tudo
