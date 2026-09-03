# QA report 002 — Protótipo de interfaces (ciclo planejado)

> Siglas: DoD — Definition of Done (Definição de Pronto) · QA — Quality Assurance
> (garantia de qualidade) · RF/RI/RNF/INT — requisito funcional / de interface / não
> funcional / integração

- **Data**: 2026-09-03 · **Raia**: plena · **Veredito**: **ciclo ainda não aberto**

> **Ciclo planejado no 001; execução ainda não iniciada.** Este relatório existe vazio de
> propósito, com a estrutura que a execução vai preencher: caixa marcada não é
> testemunha. Cada linha abaixo só recebe conteúdo quando o comando tiver sido executado,
> com a saída colada (regra R1) e o tamanho do que foi examinado (regra R2). Um `✓`
> transcrito sem a saída é defeito, não evidência.

## Funções de aptidão (DoD)

| # | Verificação | Comando | Esperado | Observado (colar a saída) | Código de saída |
|---|---|---|---|---|---|
| 1 | `ux-design.md` com `ai_visible` por objeto | ver spec, DoD linha 1 | ≥ nº de objetos | | |
| 2 | Protótipo fora da aplicação | ver spec, DoD linha 2 | `0` (declarar se vácuo) | | |
| 3 | Estados vêm de fixture, não de cálculo | ver spec, DoD linha 3 | ≥ 1 + veredito da revisão | | |
| 4 | Base 100% sintética, sem vazamento | ver spec, DoD linha 4 | `0` | | |
| 5 | Capturas regeneram byte-idênticas | duas execuções + `diff -r` | diferença vazia | | |
| 6 | Nenhuma captura órfã | conferidor com contagem na saída | 1 jornada por imagem | | |
| 7 | Dois temas × duas larguras | ver spec, DoD linha 7 | capturas presentes | | |
| 8 | Modo só-conteúdo demonstrado | ver spec, DoD linha 8 | captura presente | | |
| 9 | Nenhum provedor de modelo no cliente | ver spec, DoD linha 9 | `0` | | |
| 10 | Caminhos das jornadas resolvem | `scripts/check-caminhos.sh` | código 0 + quanto examinou | | |
| 11 | Conformidade do ciclo | `scripts/check-conformance.sh 002` | código 0 | | |

## Cauda de fechamento — a evidência

<!-- One entry per non-n/a TAIL token. What was OBSERVED, never the intention restated. -->
- TAIL:review — *(pendente: quem revisou, contexto fresco, veredito — incluindo a
  conferência de que o protótipo não calcula nada)*
- TAIL:security — *(pendente: o passe — dado real em fixture/captura, segredo ou provedor
  no cliente — e seu resultado)*
- TAIL:mutation — *(pendente: portões novos deste ciclo sabotados e vistos recusando, ou
  `n/a` com motivo)*
- TAIL:gate — *(pendente: aprovação da spec e das respostas do Clarify na abertura;
  aprovação do corte de telas e gate de merge no fechamento — Product Steward)*

## Cobertura de requisitos

*(pendente — uma linha por RF-01..RF-09, RI-01..RI-14, RNF-01..RNF-05, INT-01..INT-02,
preenchida no fechamento, cada uma apontando a linha da DoD, a captura ou a evidência que
a cobre)*

## Gate pendente

- **Abertura**: gate humano do ciclo 001 fechado + as duas precondições do roadmap
  (pergunta 1 da visão §7 respondida; specs de M1–M3 ratificadas em rascunho) + os três
  `[DÚVIDA]` do Clarify da spec respondidos.
- **Fechamento**: DoD verde com evidência colada acima, cauda completa, aprovação do
  corte de telas pelo Product Steward.
