# QA Report 011 — Fundações da aplicação

> Siglas: **QA** — Quality Assurance (garantia de qualidade) · **DoD** — Definition of Done
> (Definição de Pronto) · **ADR** — Architecture Decision Record (Registro de Decisão
> Arquitetural) · **RF/RI/RNF/RN/INT** — requisito funcional / de interface / não funcional
> / regra de negócio / integração · **i18n** — internacionalização · **APH** — Aplicação ↔
> Harness · **OTel** — OpenTelemetry · **CI** — integração contínua · **IA** — inteligência
> artificial · **RPO/RTO** — Recovery Point / Time Objective (objetivo de ponto / tempo de
> recuperação) · **DDL** — Data Definition Language (linguagem de definição de dados).

- **Data**: 2026-09-03 · **Raia**: plena · **Veredito**: **ciclo ainda não aberto**

**Ciclo planejado no 001; execução ainda não iniciada.** Este arquivo existe vazio de
propósito: a estrutura abaixo é o que a execução vai preencher, e **nenhuma célula se
preenche antes do comando rodar** — R1 (saída colada, nunca transcrita) e R2 (todo verde diz
quanto examinou). Um `✓` sem a saída é defeito, não evidência.

## Pré-condições de abertura (T-01)

| Pré-condição | Verificado em | Evidência (saída colada) | Estado |
|---|---|---|---|
| Ciclo 008 promovido (as seis ferramentas existem — há o que documentar) | — | — | — |
| Os 5 `[DÚVIDA]` do Clarify respondidos no gate | — | — | — |
| Idioma padrão decidido ([DÚVIDA] 1 — muda o RF-12) | — | — | — |
| Data de aposentadoria do formato legado decidida ([DÚVIDA] 2) | — | — | — |
| Teto de crescimento do pacote inicial fixado (RNF-09, spec L-04) | — | — | — |
| Plano do provedor permite restaurar para destino separado (spec L-01) — ou ADR da alternativa | — | — | — |

## DoD (as 18 linhas da spec — comando, saída colada, quanto examinou)

| # | Critério | Comando | Saída (colada) | Examinou | Código de saída |
|---|---|---|---|---|---|
| 1 | Domínio novo puro, testes sem rede | — | — | — | — |
| 2 | Zero literal órfão | — | — | — | — |
| 3 | Paridade de dicionários `pt` × `en` | — | — | — | — |
| 4 | Chave ausente falha alto | — | — | — | — |
| 5 | Idioma efetivo pela ordem declarada | — | — | — | — |
| 6 | Preferência persiste no servidor | — | — | — | — |
| 7 | Formatação e colação localizadas | — | — | — | — |
| 8 | Cobertura ferramenta × verbete | — | — | — | — |
| 9 | Procedência dos verbetes resolve | — | — | — | — |
| 10 | Conversão do formato legado | — | — | — | — |
| 11 | Recusa campo a campo | — | — | — | — |
| 12 | Histórico de conversa descartado e declarado | — | — | — | — |
| 13 | Ida e volta do formato consolidado | — | — | — | — |
| 14 | Restauração ensaiada | — | — | — | — |
| 15 | Migração reversível sem resíduo | — | — | — | — |
| 16 | Sem segredo e sem dado real de pessoa | — | — | — | — |
| 17 | Jornada viva presente (dois idiomas) | — | — | — | — |
| 18 | Conformidade, caminhos e links | — | — | — | — |

## Portões nomeados do roadmap (ciclo 011)

| Portão | Como se verificou | Evidência colada |
|---|---|---|
| Nenhuma cadeia de interface fora do dicionário de i18n, com a contagem na saída (R2) | — | — |
| Cada ferramenta com rota de documentação embutida respondendo | — | — |
| Importar um export sintético da quarta geração cria o projeto **ou** recusa com relato campo a campo | — | — |

## Ensaio de restauração (RF-02, RF-03 — DoD 14)

> A saída vai colada aqui, **sem credencial** (RNF-10): variável de ambiente entra, valor
> não sai.

| Item | Declarado | Medido | Fonte |
|---|---|---|---|
| Instante alvo da restauração | — | — | — |
| Destino separado usado | — | — | — |
| Duração até a aplicação responder | — | — | — |
| Objetivo de ponto de recuperação (RPO) | — | — | — |
| Objetivo de tempo de recuperação (RTO) | — | — | — |
| O que **não** voltou com o banco | — | — | — |
| Nenhum outro produto compartilha esta unidade | — | — | — |

## Medições registradas

| Métrica | Alvo | Valor medido | Fonte |
|---|---|---|---|
| Importar arquivo legado de 200 nós e 300 arestas — percentil 95 (RNF-08) | < 5 s | — | — |
| Crescimento do pacote inicial pela documentação embutida (RNF-09) | ≤ teto declarado | — | — |
| Cobertura de testes do domínio novo (RNF-12) | ≥ 85% | — | — |

## Matriz de aderência ao APH re-verificada (INT-04)

| Linha tocada | Estado antes | Estado depois | Evidência por caminho |
|---|---|---|---|
| APH-6.4 — preenchimento estruturado de argumentos (candidata declarada ao ciclo 011) | — | — | — |
| APH-3.1 — registro de telas (telas novas deste ciclo, INT-02) | — | — | — |

## Cauda

| Item | Executor (contexto fresco) | Achados | Evidência |
|---|---|---|---|
| TAIL:review | — | — | — |
| TAIL:security | — | — | — |
| TAIL:mutation | — | — | — |
| TAIL:gate | — | — | — |

## Cobertura de requisitos

*(pendente — uma linha por RF-01..RF-32, RI-01..RI-11, RNF-01..RNF-12, RN-01..RN-07 e
INT-01..INT-04, preenchida no fechamento, cada uma apontando a linha da DoD, o teste ou a
captura que a cobre.)*

## Veredito

— (o veredito só existe depois da cauda completa; caixa marcada não é testemunha)
