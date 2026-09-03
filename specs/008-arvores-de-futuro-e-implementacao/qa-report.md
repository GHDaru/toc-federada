# QA Report 008 — Árvores de Futuro e Implementação

> Siglas: **QA** — Quality Assurance (garantia de qualidade) · **DoD** — Definition of
> Done (Definição de Pronto) · **UDE** — Efeito Indesejável (*Undesirable Effect*) ·
> **NC** — Nuvem de Conflito · **ARF** — Árvore da Realidade Futura · **APR** — Árvore
> de Pré-Requisitos · **AT** — Árvore de Transição · **OI** — Objetivo Intermediário ·
> **FSM** — máquina de estados finitos · **IA** — inteligência artificial · **SDK** —
> Software Development Kit (kit de desenvolvimento).

**Ciclo planejado no 001; execução ainda não iniciada.** Este arquivo existe vazio de
propósito: a estrutura abaixo é o que a execução vai preencher, e nenhuma célula se
preenche antes de o comando rodar (R1 — saída colada, nunca transcrita; R2 — todo verde
diz quanto examinou).

## Pré-condições de abertura (T-01)

| Pré-condição | Verificado em | Evidência (saída colada) | Estado |
|---|---|---|---|
| Ciclo 005 promovido (a ARA e o UDE `Validado` existem) | — | — | — |
| Ciclo 007 promovido (a NC e a injeção `escolhida` existem) | — | — | — |
| FSM do 006 no ar (as ações do M4 executam por ela) | — | — | — |
| Decisão registrada: ramos negativos manuais nesta v1 | — | — | — |
| 5 `[DÚVIDA]` do Clarify respondidos no gate | — | — | — |

## DoD (16 linhas da spec — comando, saída colada, quanto examinou)

| # | Critério | Comando | Saída (colada) | Examinou | Código de saída |
|---|---|---|---|---|---|
| 1 | Cadeia inteira percorrida com referência em cada elo | — | — | — | — |
| 2 | Referência só por ação nomeada; sobrevive a exclusão suave | — | — | — | — |
| 3 | Promoção exige `Validado`; semeadura exige `escolhida` | — | — | — | — |
| 4 | Três árvores exportam/importam ida-e-volta com referências | — | — | — | — |
| 5 | Sequenciamento acíclico, em camadas, com elipses | — | — | — | — |
| 6 | Verificação da ARF pura e correta | — | — | — | — |
| 7 | Verbalização avaliada offline sobre corpus versionado | — | — | — | — |
| 8 | Ramo negativo sem rota assistida | — | — | — | — |
| 9 | Tripla do passo obrigatória; divergência preservada | — | — | — | — |
| 10 | Ações do M4 só mutam por `action_proposal` | — | — | — | — |
| 11 | Sem SDK, chave ou prompt no produto | — | — | — | — |
| 12 | Telas do módulo registradas | — | — | — | — |
| 13 | Toda mutação nova com traço | — | — | — | — |
| 14 | Jornada viva da cadeia sintética | — | — | — | — |
| 15 | Conformidade do ciclo | — | — | — | — |
| 16 | Caminhos e links | — | — | — | — |

## Portões nomeados do roadmap (ciclo 008)

| Portão | Como se verificou | Evidência colada |
|---|---|---|
| Teste de domínio percorre a cadeia inteira e prova a referência de origem em cada elo | — | — |
| As três árvores exportáveis/importáveis pelo E1.4 | — | — |
| Jornada da injeção à APR sequenciada, com captura | — | — |

## Medições registradas (RNF-04 / RNF-05 / RNF-06)

| Métrica | Alvo | Valor medido | Fonte |
|---|---|---|---|
| Sequenciamento com 100 OIs / 200 dependências (p95) | < 2 s | — | — |
| Vista da cadeia com até 50 referências (p95) | < 1 s | — | — |
| Verbalização avaliada de texto ≤ 500 caracteres | < 100 ms | — | — |

## Rede de proteção da extração (T-03)

| Verificação | Comando | Saída (colada) | Estado |
|---|---|---|---|
| Suíte do ciclo 005 continua verde após a extração do pacote de suficiência | — | — | — |
| Nenhuma regra de suficiência duplicada (um único módulo de definição) | — | — | — |

## Cauda

| Item | Executor (contexto fresco) | Achados | Evidência |
|---|---|---|---|
| TAIL:review | — | — | — |
| TAIL:security | — | — | — |
| TAIL:mutation | — | — | — |
| TAIL:gate | — | — | — |

## Veredito

— (o veredito só existe depois da cauda completa; caixa marcada não é testemunha)
