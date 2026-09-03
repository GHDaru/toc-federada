# QA report 001 — Fundação e planejamento (ciclo documental)

> Siglas: DoD — Definition of Done · DoR — Definition of Ready

- **Data**: 2026-09-03 · **Raia**: plena · **Veredito**: **pendente**

> **Evidência preenchida pelos portões ao fechar o ciclo.** Este relatório nasce vazio de
> propósito: caixa marcada não é testemunha. Cada linha abaixo só recebe conteúdo quando
> o comando tiver sido executado, com a saída colada (regra R1) e o tamanho do que foi
> examinado (regra R2). Um `✓` transcrito sem a saída é defeito, não evidência.

## Funções de aptidão (DoD)

| # | Verificação | Comando | Esperado | Observado (colar a saída) | Código de saída |
|---|---|---|---|---|---|
| 1 | Constituição com 7 princípios | `grep -c '^### P[1-7]\.' docs/governance/constitution.md` | `7` | | |
| 2 | Bloco do instalador preservado | `grep -c '^## Method: Maestro' CLAUDE.md` | `1` | | |
| 3 | Oito ADRs | `ls docs/adr/000[1-8]-*.md \| wc -l` | `8` | | |
| 4 | Sucessão e índices de ADR | `scripts/check-adrs-sucessao.sh` | código 0 + quanto examinou | | |
| 5 | 12 pastas × 4 arquivos de spec | ver spec, DoD linha 5 | `12` e `48` | | |
| 6 | Roadmap com 12 ciclos | `grep -c '^| \*\*0[0-9][0-9]\*\*' docs/roadmap.md` | `12` | | |
| 7 | Régua DoR das specs | `scripts/check-specs.sh` | código 0 + quanto examinou | | |
| 8 | Caminhos entre crases | `scripts/check-caminhos.sh` | código 0 + quanto examinou | | |
| 9 | Links relativos | `scripts/check-links.sh` | código 0 + quanto examinou | | |
| 10 | Site gerado por script | ver spec, DoD linha 10 | código 0 | | |
| 11 | Sem vazamento da base real da irmã | `grep -rn "gestaodeprioridades/protot[i]po" --include='*.md' . \| wc -l` | `0` | | |
| 12 | Método instalado e coerente | `scripts/check-install.sh` | código 0 | | |
| 13 | Conformidade do ciclo | `scripts/check-conformance.sh 001` | código 0 | | |

## Cauda de fechamento — a evidência

<!-- One entry per non-n/a TAIL token. What was OBSERVED, never the intention restated. -->
- TAIL:review — *(pendente: quem revisou, contexto fresco, veredito, o que se fez com os
  achados)*
- TAIL:security — *(pendente: o passe — vazamento de dado real, segredo em texto — e seu
  resultado)*
- TAIL:mutation — *(pendente: cada portão de T-10 sabotado, o comando, a recusa que
  imprimiu)*
- TAIL:gate — *(pendente: o que aguarda o Product Steward — aprovação da spec, respostas
  do Clarify, gate de merge)*

## Cobertura de requisitos

*(pendente — uma linha por RF-01..RF-12 e RNF-01..RNF-05, preenchida no fechamento, cada
uma apontando a linha da DoD ou a evidência que a cobre)*

## Gauntlet (crítica às cegas)

| Barra | Veredito | Maior lacuna nomeada |
|---|---|---|
| Corpus da `gestaodeprioridades` | *(pendente)* | |
| ECS `specs/001-catalogo-itens` | *(pendente)* | |
| ECS `docs/product-site/` | *(pendente)* | |

## Gate pendente

- Aprovação da spec 001, respostas aos três `[DÚVIDA]` do Clarify e promoção dev → main
  aguardam o Product Steward.
