# QA Report 003 — Esqueleto federado

> Siglas: **DoD** — Definition of Done · **QA** — Quality Assurance (garantia de
> qualidade) · **OTel** — OpenTelemetry.

**Ciclo planejado no 001; execução ainda não iniciada.** Este arquivo existe vazio de
propósito: a estrutura abaixo é o que a execução vai preencher, e nenhuma célula se
preenche antes do comando rodar (R1 — saída colada, nunca transcrita; R2 — todo verde
diz quanto examinou).

## Re-medição dos bloqueios externos (T-02)

| Bloqueio | Medido em | Evidência (`arquivo:linha` + saída colada) | Estado |
|---|---|---|---|
| L-01 — schemas de manifesto | — | — | — |
| L-02 — fatia de federação | — | — | — |
| L-03 — grants em memória | — | — | — |

## DoD (14 linhas da spec — comando, saída colada, quanto examinou)

| # | Critério | Comando | Saída (colada) | Examinou | Código de saída |
|---|---|---|---|---|---|
| 1 | Admissão recusa nomeando o que faltou | — | — | — | — |
| 2 | Handshake nunca confiado | — | — | — | — |
| 3 | Grant trocado e descartado | — | — | — | — |
| 4 | Falha fechada | — | — | — | — |
| 5 | Trava dupla do canal | — | — | — | — |
| 6 | `targetOrigin` dirigido | — | — | — | — |
| 7 | Envelope canônico | — | — | — | — |
| 8 | Migração reversível sem resíduo | — | — | — | — |
| 9 | Isolamento por tenant | — | — | — | — |
| 10 | Traço de ponta a ponta | — | — | — | — |
| 11 | eTLD+1 distinto | — | — | — | — |
| 12 | Junta fecha contra a `ghdaru` real | — | — | — | — |
| 13 | Sem segredo versionado | — | — | — | — |
| 14 | Rollback ensaiado | — | — | — | — |

## Gates de reversibilidade (raia infra — prova, não promessa)

| Gate | Ensaio | Evidência colada |
|---|---|---|
| GATE-migracao | — | — |
| GATE-deploy | — | — |
| GATE-admissao | — | — |
| GATE-endereco (portão humano) | — | — |
| GATE-seguranca | — | — |

## Medições registradas (RNF-06 / T-18)

| Métrica | Valor medido | Fonte (traço) |
|---|---|---|
| `ghd.ready` → lista renderizada | — | — |

## Cauda

| Item | Executor (contexto fresco) | Achados | Evidência |
|---|---|---|---|
| TAIL:review | — | — | — |
| TAIL:security | — | — | — |
| TAIL:mutation | — | — | — |
| TAIL:gate | — | — | — |

## Veredito

— (o veredito só existe depois da cauda completa; caixa marcada não é testemunha)
