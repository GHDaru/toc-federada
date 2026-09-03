# QA report 004 — Núcleo de diagramas (ciclo planejado)

> Siglas: QA — Quality Assurance (garantia de qualidade) · DoD — Definition of Done
> (Definição de Pronto) · RF/RI/RNF/RN/INT — requisito funcional / de interface / não
> funcional / regra de negócio / integração · TDD — Test-Driven Development
> (desenvolvimento guiado por teste) · OTel — OpenTelemetry · JSON — JavaScript Object
> Notation

- **Data**: 2026-09-03 · **Raia**: plena · **Veredito**: **ciclo ainda não aberto**

> **Ciclo planejado no 001; execução ainda não iniciada.** Este relatório existe vazio de
> propósito, com a estrutura que a execução vai preencher: caixa marcada não é
> testemunha. Cada linha abaixo só recebe conteúdo quando o comando tiver sido
> executado, com a saída colada (regra R1) e o tamanho do que foi examinado (regra R2).
> Um `✓` transcrito sem a saída é defeito, não evidência.

## Funções de aptidão (DoD)

| # | Verificação | Comando | Esperado | Observado (colar a saída) | Código de saída |
|---|---|---|---|---|---|
| 1 | Domínio puro, testes sem rede | `pytest tests/domain/` + `lint-imports` | verde + código 0 | | |
| 2 | Teste do filtro de exclusão (spec F-06) | `pytest tests/domain/test_excluir_no.py -k cascata -v` | caso "só o nó e suas arestas" verde | | |
| 3 | Exclusão suave reversível | `pytest tests/application/test_lixeira.py` | excluir → restaurar → idêntico | | |
| 4 | Ida e volta do export | `pytest tests/application/test_export_import.py -k roundtrip` | verde | | |
| 5 | Export determinístico | duas execuções + `diff` | diferença vazia | | |
| 6 | Importação inválida recusa com relato | `pytest tests/application/test_import_invalido.py` | nada criado, relato por item | | |
| 7 | Isolamento por inquilino | `pytest tests/integration/test_isolamento.py` | leitura cruzada falha | | |
| 8 | Toda mutação com traço | `pytest tests/integration/test_traco.py` | falha sem traço | | |
| 9 | Política por tipo de ação, nunca por origem | teste de dois caminhos (T-07) | decisão vem da tabela de tipos | | |
| 10 | Sem segredo no cliente | `grep -rniE "api[_-]?key\|secret" frontend/src/ \| wc -l` | `0` | | |
| 11 | i18n sem literal solto | função de aptidão de literais | código 0 + quanto examinou | | |
| 12 | Jornada viva presente | `ls docs/jornadas/` | jornada do M1 com capturas | | |
| 13 | Conformidade do ciclo | `scripts/check-conformance.sh 004` | código 0 | | |
| 14 | Caminhos e links | `scripts/check-caminhos.sh` + `scripts/check-links.sh` | código 0 + quanto examinaram | | |

## Cauda de fechamento — a evidência

<!-- One entry per non-n/a TAIL token. What was OBSERVED, never the intention restated. -->
- TAIL:review — *(pendente: quem revisou, contexto fresco, veredito — incluindo a
  conferência do item 8: política por tipo de ação, nunca por origem alegada; e a
  equivalência canvas↔tabela)*
- TAIL:security — *(pendente: o passe — segredo no cliente, isolamento por inquilino,
  fail-closed, payload de importação, dado real em fixture/captura — e o resultado por
  item)*
- TAIL:mutation — *(pendente: cada sabotagem de T-18 — import-linter, validação de
  importação, filtro de exclusão, mutação sem traço — com o comando e a recusa que
  imprimiu)*
- TAIL:gate — *(pendente: DoD apresentada ao Product Steward, jornada revista, decisão de
  merge registrada)*

## Cobertura de requisitos

*(pendente — uma linha por RF-01..RF-36, RI-01..RI-12, RNF-01..RNF-10, RN-01..RN-06,
INT-01..INT-03, preenchida no fechamento, cada uma apontando a linha da DoD, o teste ou a
captura que a cobre)*

## Gate pendente

- **Abertura**: gate humano do ciclo 001 fechado + aptidão do ciclo 003 verde ("a junta
  fecha contra a ghdaru real", reexecutada — T-02) + os 4 `[DÚVIDA]` do Clarify da spec
  respondidos (retenção da lixeira, concorrência, matriz papel×ação, teto de nós) +
  `ux-design.md` do ciclo 002 cobrindo as telas 6.1–6.6.
- **Fechamento**: DoD verde com evidência colada acima, cauda completa, aprovação de
  merge pelo Product Steward.
