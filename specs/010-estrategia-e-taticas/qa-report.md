# QA Report 010 — Estratégia & Táticas

> Siglas: **QA** — Quality Assurance (garantia de qualidade) · **DoD** — Definition of
> Done (Definição de Pronto) · **S&T** — Estratégia & Táticas (*Strategy & Tactics*) ·
> **ADR** — Architecture Decision Record (Registro de Decisão Arquitetural) · **SDK**
> — Software Development Kit (kit de desenvolvimento) · **UX** — experiência de
> usuário.

**Ciclo planejado no 001; execução ainda não iniciada.** Este arquivo existe vazio de
propósito: a estrutura abaixo é o que a execução vai preencher, e nenhuma célula se
preenche antes do comando rodar (R1 — saída colada, nunca transcrita; R2 — todo verde
diz quanto examinou).

## Pré-condições de abertura (T-01)

| Pré-condição | Verificado em | Evidência (saída colada) | Estado |
|---|---|---|---|
| Ciclo 004 promovido (o Projeto do M1 existe — única dependência técnica) | — | — | — |
| 5 `[DÚVIDA]` do Clarify respondidos no gate | — | — | — |
| [DÚVIDA] 1 (categoria da linhagem) respondido antes do data-model | — | — | — |
| [DÚVIDA] 5 (ux da árvore) refletido na declaração de artefatos | — | — | — |

## DoD (16 linhas da spec — comando, saída colada, quanto examinou)

| # | Critério | Comando | Saída (colada) | Examinou | Código de saída |
|---|---|---|---|---|---|
| 1 | Domínio do M5 puro, offline | — | — | — | — |
| 2 | Numeração derivada e determinística | — | — | — | — |
| 3 | Renumeração da subárvore ao inserir/remover/mover | — | — | — | — |
| 4 | Número nunca é entrada | — | — | — | — |
| 5 | As três premissas persistidas e regras de pendência | — | — | — | — |
| 6 | Árvore estrita: sem ciclo, um pai | — | — | — | — |
| 7 | Excluir subárvore não toca no resto (F-07 como teste) | — | — | — | — |
| 8 | Status com evento | — | — | — | — |
| 9 | Pendências e contagens por função pura | — | — | — | — |
| 10 | Exportação sem perda; numeração deriva na importação | — | — | — | — |
| 11 | Toda mutação nova com traço | — | — | — | — |
| 12 | Sem SDK, chave, prompt ou ação de catálogo no módulo | — | — | — | — |
| 13 | Desempenho da árvore e do mover | — | — | — | — |
| 14 | Jornada viva de três níveis | — | — | — | — |
| 15 | Conformidade do ciclo | — | — | — | — |
| 16 | Caminhos e links | — | — | — | — |

## Portões nomeados do roadmap (ciclo 010)

| Portão | Como se verificou | Evidência colada |
|---|---|---|
| Teste de renumeração da subárvore (inserir/remover renumera corretamente) | — | — |
| As três premissas persistidas e exibidas por nó | — | — |
| S&T sintética de três níveis, com captura | — | — |

## Medições registradas (RNF-04)

| Métrica | Alvo | Valor medido | Fonte |
|---|---|---|---|
| Abrir árvore S&T (100 passos, 5 níveis) — p95 | < 1 s | — | — |
| Mover subárvore de 20 passos (renumeração incluída) | < 500 ms | — | — |

## Cauda

| Item | Executor (contexto fresco) | Achados | Evidência |
|---|---|---|---|
| TAIL:review | — | — | — |
| TAIL:security | — | — | — |
| TAIL:mutation | — | — | — |
| TAIL:gate | — | — | — |

## Veredito

— (o veredito só existe depois da cauda completa; caixa marcada não é testemunha —
e o fechamento deste ciclo registra que a regressão D-05 foi desfeita com decisão
registrada, o que a linhagem nunca fez)
