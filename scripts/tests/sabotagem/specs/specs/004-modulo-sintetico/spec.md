# Spec 004 — Módulo sintético (M0 — módulo de fixture)

> Siglas: TOC — Teoria das Restrições · ADR — Architecture Decision Record (Registro de
> Decisão Arquitetural) · RF/RI/RNF/RN/INT — requisito funcional / de interface / não
> funcional / regra de negócio / integração · US — User Story (história de usuário) ·
> DoR — Definition of Ready (definição de pronto para começar) · DoD — Definition of Done
> (Definição de Pronto) · DDD — Domain-Driven Design (Design Orientado a Domínio) ·
> EARS — Easy Approach to Requirements Syntax (sintaxe de requisito em forma controlada).

- **Status**: Fixture (não é spec do produto)
- **Raia**: plena
- **Data**: 2026-09-03
- **Origem**: fixture de sabotagem de `scripts/check-specs.sh`

## O quê e por quê

Esta spec não descreve produto: descreve a **entrada válida mínima** que o portão
`check-specs.sh` tem de aceitar. Sem ela, o portão só provaria que sabe reprovar — e um
portão que reprova tudo é tão inútil quanto um que aprova tudo.

Desde que o portão passou a **pontuar** a régua de prontidão do ADR 0004 §5, a base
precisa também **passar no corte ≥ 80**: uma base que ficasse abaixo dele provaria que o
corte é impossível, não que a spec é válida. Por isso cada seção aqui carrega conteúdo de
verdade, e não só o cabeçalho.

## O que entra como dado

- A taxonomia do ADR 0004 (Módulo ⊃ Épico ⊃ Feature ⊃ Story; RF/RI/RNF/RN/INT/F/L).
- A régua de prontidão do ADR 0004 §5, com corte em 80 e as cinco dimensões pontuadas.
- A base sintética do ADR 0006: personas fictícias, nenhum dado real de pessoa.

## Épicos, features e user stories

### E0.1 — Épico sintético

**F0.1.1 — Feature sintética** — a menor unidade que ainda tem história e critério, para o
portão ter feature, história e Gherkin para medir.

- US-01 — Como **Facilitadora TOC**, quero uma entrada válida de fixture, para o portão
  poder provar que aceita o certo.
  - Dado uma spec completa · Quando o portão roda · Então ele sai com código 0.
- US-02 — Como **Product Steward**, quero que a base passe no mesmo corte que as specs
  reais, para o corte não ser uma exigência que só vale para os outros.
  - Dado a régua do ADR 0004 · Quando o portão pontua esta spec · Então a nota fica
    igual ou acima de 80 e a tabela de notas mostra as cinco dimensões.

## Entidades e modelo de domínio

- **Fixture** (agregado): identidade, conteúdo. Invariante: não contém dado real de pessoa.
- **Sabotagem** (objeto de valor): mutação declarada + trecho exigido na saída do portão.
- **Execução** (evento de domínio): fixture copiado, mutação aplicada, código de saída lido.

## Requisitos funcionais

### Grupo sintético

RF-01: O SISTEMA DEVE aceitar uma spec que carregue todas as seções obrigatórias com
conteúdo, sem exigir nenhuma seção fora da lista do portão. [F-01] 🟡

RF-02: O SISTEMA DEVE pontuar esta spec pelas cinco dimensões do ADR 0004 §5 e imprimir
a nota ao lado do denominador de cada sinal medido. [F-02] 🟡

RF-03: QUANDO a tabela de critérios de aceite ficar sem nenhuma linha com comando,
O SISTEMA DEVE recusar a spec por Testabilidade e nomear a dimensão na mensagem de
erro. [F-02] 🟡

## Requisitos de interface

A única "interface" do fixture é a saída do portão em terminal; ela é requisito porque a
regra R2 exige que o verde diga quanto examinou.

RI-01: A saída apresenta uma linha por ciclo com as cinco dimensões e a nota, e uma linha
de denominadores por ciclo, legível em terminal de 100 colunas. 🟡

## Requisitos não funcionais

RNF-01: O portão DEVE terminar em menos de 5 segundos sobre este fixture. 🟡

RNF-02: O portão DEVE ser determinístico: duas execuções sobre a mesma cópia produzem a
mesma nota, sem depender de rede, relógio ou ordem de sistema de arquivos. 🟡

## Regras de negócio

RN-01: Nenhum dado real de pessoa entra em fixture (ADR 0006). 🟢

RN-02: Sinal declarado não aplicável por isenção sai do denominador; ausência sem isenção
vale zero — a isenção nunca é desconto silencioso. 🟢

## Integrações

INT-01: Nenhuma — este fixture não atravessa fronteira alguma; ele é lido por
`scripts/check-specs.sh` e por `scripts/tests/run-sabotagem.sh`, e por mais ninguém.

## Telas e fluxos

### 6.1 Nenhuma tela — Job: fixture não tem tela · Campos: — · Ações: —

O fluxo inteiro é de linha de comando: copiar o fixture, aplicar a mutação na cópia,
rodar o portão, ler o código de saída e o motivo impresso.

## Fora de escopo

- Spec de raia leve: o fixture cobre a raia plena, que é o caso difícil.
- Ciclo com isenção declarada (como o 001 real): a isenção tem cobertura própria no
  portão e não se prova aqui.
- Qualquer conteúdo de produto: este arquivo não descreve o TOC Federada.

## Entregáveis

- Este arquivo e os outros três artefatos do ciclo sintético.
- A linha correspondente na tabela de sabotagens de `scripts/tests/run-sabotagem.sh`.
- A saída do portão colada no relatório de qualidade do ciclo que adotar a régua.

## Critérios de aceite (DoD)

| # | Critério | Verificação executável |
|---|---|---|
| 1 | O portão aceita esta spec (RF-01) | `scripts/check-specs.sh scripts/tests/sabotagem/specs` sai 0 |
| 2 | A nota e os denominadores aparecem (RF-02) | `scripts/check-specs.sh scripts/tests/sabotagem/specs \| grep -c 'Régua de prontidão'` → `1` |
| 3 | A base e as sabotagens rodam juntas (RF-03) | `scripts/tests/run-sabotagem.sh` sai 0 |

## Fontes

F-01: `scripts/check-specs.sh` — o cabeçalho do portão — define as seções obrigatórias 🟢

F-02: `docs/adr/0004-taxonomia-de-planejamento-e-absorcao-da-reversa.md` — §5 da decisão —
fixa os pesos das cinco dimensões e o corte em 80 🟢

## Lacunas e assunções

L-01: fixture não cobre spec de raia leve — assumimos que a raia plena é o caso difícil —
risco baixo.

L-02: a nota da base é medida, não escolhida; se a régua mudar de pesos, a base pode
precisar de mais conteúdo — assumimos que a suíte de sabotagem avisa antes do portão real
— risco baixo.

## Clarify

- [DÚVIDA] nenhuma: fixture não tem dúvida a levar ao Product Steward.
