# QA Report 012 — Jornadas e autodeclaração

> Siglas: **QA** — Quality Assurance (garantia de qualidade) · **DoD** — Definition of Done
> (Definição de Pronto) · **ADR** — Architecture Decision Record (Registro de Decisão
> Arquitetural) · **APH** — Aplicação ↔ Harness · **RF/RI/RNF/RN/INT** — requisito
> funcional / de interface / não funcional / regra de negócio / integração · **P6** —
> princípio "Jornada viva" da constituição do projeto · **ARA** — Árvore da Realidade Atual
> · **NC** — Nuvem de Conflito · **ARF** — Árvore da Realidade Futura · **APR** — Árvore de
> Pré-Requisitos · **AT** — Árvore de Transição · **S&T** — Árvore de Estratégia & Táticas ·
> **UI** — interface de usuário · **CI** — integração contínua · **IA** — inteligência
> artificial.

- **Data**: 2026-09-03 · **Raia**: plena · **Veredito**: **ciclo ainda não aberto**

**Ciclo planejado no 001; execução ainda não iniciada.** Este arquivo existe vazio de
propósito: a estrutura abaixo é o que a execução vai preencher, e **nenhuma célula se
preenche antes do comando rodar** — R1 (saída colada, nunca transcrita) e R2 (todo verde diz
quanto examinou). Num ciclo cujo produto é uma declaração, isso deixa de ser disciplina e
passa a ser o conteúdo: uma tabela preenchida sem execução aqui é exatamente a mentira que a
autodeclaração existe para não ser.

## Pré-condições de abertura (T-01)

| Pré-condição | Verificado em | Evidência (saída colada) | Estado |
|---|---|---|---|
| Ciclos 009, 010 e 011 promovidos | — | — | — |
| As seis jornadas (J-01..J-06) existem com script de captura versionado | — | — | — |
| Aplicação publicada e alcançável, em ambiente com base sintética (spec L-03) | — | — | — |
| Os 5 `[DÚVIDA]` do Clarify respondidos no gate | — | — | — |
| Política para veredito "não apto" decidida ([DÚVIDA] 1) | — | — | — |
| Decisão sobre publicação externa da autodeclaração ([DÚVIDA] 2) | — | — | — |

## DoD (as 17 linhas da spec — comando, saída colada, quanto examinou)

| # | Critério | Comando | Saída (colada) | Examinou | Código de saída |
|---|---|---|---|---|---|
| 1 | Todas as capturas regeneram do build atual | — | — | — | — |
| 2 | Regeneração determinística | — | — | — | — |
| 3 | Nenhuma captura órfã, nenhuma citação quebrada | — | — | — | — |
| 4 | Travessia com persona única | — | — | — | — |
| 5 | Avaliação heurística datada e limitada | — | — | — | — |
| 6 | Matriz sem célula de evidência vazia | — | — | — | — |
| 7 | Evidência da matriz resolve | — | — | — | — |
| 8 | Suíte do Nível 1 executada contra a URL publicada | — | — | — | — |
| 9 | Perfil (se usado) versionado e sem isenção | — | — | — | — |
| 10 | Itens não observáveis listados com evidência interna | — | — | — | — |
| 11 | ADR de autodeclaração com lado e maturidade | — | — | — | — |
| 12 | Autodeclaração derivada da matriz | — | — | — | — |
| 13 | ADR no índice e no registro de decisões | — | — | — | — |
| 14 | Site regenerado sem divergência | — | — | — | — |
| 15 | Contagens do site derivadas dos arquivos | — | — | — | — |
| 16 | Sem dado real de pessoa | — | — | — | — |
| 17 | Conformidade, caminhos e links | — | — | — | — |

## Portões nomeados do roadmap (ciclo 012)

| Portão | Como se verificou | Evidência colada |
|---|---|---|
| Todas as capturas de todas as jornadas regeneram do build atual | — | — |
| A matriz tem um veredito por requisito APH, cada um com evidência por caminho, sem célula vazia | — | — |
| O site regenerado não diverge do commitado (diferença vazia na CI) | — | — |
| Portão de revisão: matriz revisada em contexto fresco | — | — |
| Portão humano: o Product Steward assina a autodeclaração | — | — |

## Jornadas — estado no fechamento

| J | Jornada | Ciclo de nascimento | Capturas regeradas | Divergência (achado, se houver) |
|---|---|---|---|---|
| J-01 | Chegada e embarque | 003 | — | — |
| J-02 | Primeiro projeto e ARA | 004 · 005 | — | — |
| J-03 | Nuvem de Conflito | 007 | — | — |
| J-04 | Da injeção ao plano (ARF → APR → AT) | 008 | — | — |
| J-05 | Focalização | 009 | — | — |
| J-06 | Estratégia & Táticas | 010 | — | — |
| J-07 | Travessia de ponta a ponta (persona única) | 012 | — | — |

## Execução da suíte de conformidade — Nível 1 (T-05, T-06)

| Item | Valor | Fonte |
|---|---|---|
| Data da execução | — | — |
| Alvo (URL) e ambiente | — | — |
| Versão da norma medida (padrão · Anexo A · Anexo B) | — | — |
| Revisão do nosso código | — | — |
| Perfil de adaptação usado | — | — |
| Traduções aplicadas pelo perfil | — | — |
| **Veredito (como saiu)** | — | — |
| Checks verificados / falhas / avisos | — | — |
| Itens que a caixa-preta não alcança, com evidência interna | — | — |

> O relatório integral entra colado abaixo desta tabela, **sem credencial** (RNF-03).
> Veredito negativo entra como saiu (RN-04); cada falha recebe decisão associada (RF-18).

## Matriz de aderência — contagem por status no fechamento

| Status | Antes (ciclo 001) | Depois (ciclo 012) | Evidência |
|---|---|---|---|
| ● atendido | — | — | — |
| ◑ parcial (com o que falta nomeado) | — | — | — |
| ○ planejado | — | — | — |
| ✦ delegado à fundação por desenho | — | — | — |
| ✗ fora do alvo (com porta de volta) | — | — | — |

## Avaliação heurística do conjunto (T-08)

| Limite declarado | Quem avaliou | Quando | O que não foi avaliado |
|---|---|---|---|
| — | — | — | — |

| Severidade | Tela | Achado | Destino (corrigido aqui / dívida com dono) |
|---|---|---|---|
| — | — | — | — |

## Cauda

| Item | Executor (contexto fresco) | Achados | Evidência |
|---|---|---|---|
| TAIL:review | — | — | — |
| TAIL:security | — | — | — |
| TAIL:mutation | — | — | — |
| TAIL:gate | — | — | — |

## Cobertura de requisitos

*(pendente — uma linha por RF-01..RF-24, RI-01..RI-06, RNF-01..RNF-08, RN-01..RN-06 e
INT-01..INT-04, preenchida no fechamento, cada uma apontando a linha da DoD, o portão ou a
captura que a cobre.)*

## Veredito

— (o veredito só existe depois da cauda completa; caixa marcada não é testemunha)
