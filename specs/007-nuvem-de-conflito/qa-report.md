# QA Report 007 — Nuvem de Conflito

> Siglas: **QA** — Quality Assurance (garantia de qualidade) · **DoD** — Definition of
> Done (Definição de Pronto) · **NC** — Nuvem de Conflito · **FSM** — máquina de
> estados finitos · **IA** — inteligência artificial · **TRIZ** — Teoria da Resolução
> Inventiva de Problemas · **SDK** — Software Development Kit (kit de
> desenvolvimento).

**Ciclo planejado no 001; execução ainda não iniciada.** Este arquivo existe vazio de
propósito: a estrutura abaixo é o que a execução vai preencher, e nenhuma célula se
preenche antes do comando rodar (R1 — saída colada, nunca transcrita; R2 — todo verde
diz quanto examinou).

## Pré-condições de abertura (T-01)

| Pré-condição | Verificado em | Evidência (saída colada) | Estado |
|---|---|---|---|
| Ciclo 004 promovido (o Projeto do M1 existe) | — | — | — |
| Ciclo 006 promovido (catálogo e FSM de proposta existem) | — | — | — |
| Spec do M3 com as 7 premissas modeladas | — | — | — |
| 5 `[DÚVIDA]` do Clarify respondidos no gate | — | — | — |

## DoD (16 linhas da spec — comando, saída colada, quanto examinou)

| # | Critério | Comando | Saída (colada) | Examinou | Código de saída |
|---|---|---|---|---|---|
| 1 | Invariantes da nuvem no domínio puro, offline | — | — | — | — |
| 2 | 5 entidades e 7 arestas indestrutíveis | — | — | — | — |
| 3 | Injeção sempre referencia premissa | — | — | — | — |
| 4 | FSM de status de injeção | — | — | — | — |
| 5 | Recusar geração deixa o projeto intacto | — | — | — | — |
| 6 | Resultado fora do schema recusado em falha fechada | — | — | — | — |
| 7 | Nenhum parse de markdown no caminho da geração | — | — | — | — |
| 8 | Heurísticas de formulação com corpus | — | — | — | — |
| 9 | Visão de solução cobre as 7 arestas | — | — | — | — |
| 10 | Exportação sem perda (ida e volta) | — | — | — | — |
| 11 | Toda mutação nova com traço | — | — | — | — |
| 12 | Sem SDK, chave ou prompt no produto | — | — | — | — |
| 13 | Capability ausente esconde as 3 mutadoras | — | — | — | — |
| 14 | Jornada viva do dilema sintético | — | — | — | — |
| 15 | Conformidade do ciclo | — | — | — | — |
| 16 | Caminhos e links | — | — | — | — |

## Portões nomeados do roadmap (ciclo 007)

| Portão | Como se verificou | Evidência colada |
|---|---|---|
| Invariantes da nuvem por teste de domínio (5 entidades, 7 arestas, injeção referencia premissa) | — | — |
| A geração a partir de narrativa entra como `action_proposal`; recusar deixa o projeto intacto (teste) | — | — |
| Jornada do dilema sintético da "Instituição Horizonte" de ponta a ponta, com captura | — | — |

## Medições registradas (RNF-05 / RNF-06)

| Métrica | Alvo | Valor medido | Fonte |
|---|---|---|---|
| Abrir projeto NC completo (7 arestas, 30 premissas, 50 injeções) — p95 | < 1 s | — | — |
| Recusa de proposta (sem escrita no agregado) | < 500 ms | — | — |

## Cauda

| Item | Executor (contexto fresco) | Achados | Evidência |
|---|---|---|---|
| TAIL:review | — | — | — |
| TAIL:security | — | — | — |
| TAIL:mutation | — | — | — |
| TAIL:gate | — | — | — |

## Veredito

— (o veredito só existe depois da cauda completa; caixa marcada não é testemunha)
