# Spec 004 — Módulo sintético (M0 — módulo de fixture)

> Siglas: TOC — Teoria das Restrições · ADR — Architecture Decision Record (Registro de
> Decisão Arquitetural) · RF/RI/RNF/RN/INT — requisito funcional / de interface / não
> funcional / regra de negócio / integração · US — User Story (história de usuário) ·
> DoD — Definition of Done (Definição de Pronto) · DDD — Domain-Driven Design (Design
> Orientado a Domínio).

- **Status**: Fixture (não é spec do produto)
- **Raia**: plena
- **Data**: 2026-09-03
- **Origem**: fixture de sabotagem de `scripts/check-specs.sh`

## O quê e por quê

Esta spec não descreve produto: descreve a **entrada válida mínima** que o portão
`check-specs.sh` tem de aceitar. Sem ela, o portão só provaria que sabe reprovar — e um
portão que reprova tudo é tão inútil quanto um que aprova tudo.

## O que entra como dado

- A taxonomia do ADR 0004 (Módulo ⊃ Épico ⊃ Feature ⊃ Story; RF/RI/RNF/RN/INT/F/L).
- A base sintética do ADR 0006: personas fictícias, nenhum dado real de pessoa.

## Épicos, features e user stories

### E0.1 — Épico sintético

**F0.1.1 — Feature sintética** — a menor unidade que ainda tem história e critério.

- US-01 — Como **Facilitadora TOC**, quero uma entrada válida de fixture, para o portão
  poder provar que aceita o certo.
  - Dado uma spec completa · Quando o portão roda · Então ele sai com código 0.

## Entidades e modelo de domínio

- **Fixture** (agregado): identidade, conteúdo. Invariante: não contém dado real de pessoa.

## Requisitos funcionais

### Grupo sintético

RF-01: O SISTEMA DEVE aceitar uma spec que carregue todas as seções obrigatórias. [F-01] 🟡

## Requisitos de interface

RI-01: A interface DEVE existir como requisito próprio, separado do funcional. 🟡

## Requisitos não funcionais

RNF-01: O portão DEVE terminar em menos de 5 segundos sobre este fixture. 🟡

## Regras de negócio

RN-01: Nenhum dado real de pessoa entra em fixture (ADR 0006). 🟢

## Integrações

INT-01: Nenhuma — este fixture não atravessa fronteira alguma.

## Telas e fluxos

### 6.1 Nenhuma tela — Job: fixture não tem tela · Campos: — · Ações: —

## Entregáveis

- Este arquivo e os outros três artefatos do ciclo sintético.

## Critérios de aceite (DoD)

| # | Critério | Verificação executável |
|---|---|---|
| 1 | O portão aceita esta spec | `scripts/check-specs.sh scripts/tests/sabotagem/specs` sai 0 |

## Fontes

F-01: `scripts/check-specs.sh` — o cabeçalho do portão — define as seções obrigatórias 🟢

## Lacunas e assunções

L-01: fixture não cobre spec de raia leve — assumimos que a raia plena é o caso difícil —
risco baixo.

## Clarify

- [DÚVIDA] nenhuma: fixture não tem dúvida a levar ao Product Steward.
