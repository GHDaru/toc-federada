# QA report 006 — Ações governadas e snapshot (ciclo planejado)

> Siglas: QA — Quality Assurance (garantia de qualidade) · DoD — Definition of Done
> (Definição de Pronto) · RF/RI/RNF/RN/INT — requisito funcional / de interface / não
> funcional / regra de negócio / integração · FSM — máquina de estados finitos · APH —
> Aplicação ↔ Harness · SSE — *Server-Sent Events* · IA — inteligência artificial ·
> JSON — JavaScript Object Notation

- **Data**: 2026-09-03 · **Raia**: plena · **Veredito**: **ciclo ainda não aberto**

> **Ciclo planejado no 001; execução ainda não iniciada.** Este relatório existe vazio
> de propósito, com a estrutura que a execução vai preencher: caixa marcada não é
> testemunha. Cada linha abaixo só recebe conteúdo quando o comando tiver sido
> executado, com a saída colada (regra R1) e o tamanho do que foi examinado (regra
> R2). Um `✓` transcrito sem a saída é defeito, não evidência.
>
> Única evidência já existente, produzida **no planejamento** (ciclo 001, 2026-09-03)
> e colada aqui porque já foi executada: a validação do
> [`contracts/manifesto.json`](contracts/manifesto.json) contra o schema normativo
> `protocolos/padrao/schemas/federacao-manifesto.schema.json` (jsonschema 4.26.0,
> draft 2020-12), com três sabotagens que provam que o validador não é leniente:
>
> ```
> VALIDO: contracts/manifesto.json passa no schema normativo federacao-manifesto.schema.json (draft 2020-12) sem erros
> telas: 4 · acoes: 8 · capabilities_required: ['toc:read', 'toc:write']
> sabotagem 1 (sem theme.fallback): 1 erro(s)
> sabotagem 2 (capability curinga toc:*): 1 erro(s)
> sabotagem 3 (batch_atomicity na acao do MANIFESTO): 1 erro(s)
> ```
>
> A sabotagem 3 é também a prova da lacuna L-02 da spec (o schema do manifesto rejeita
> a declaração de atomicidade que o fio §A.5 pede). A validação será **reexecutada**
> neste ciclo (DoD linha 11): evidência não migra, se reproduz.

## Funções de aptidão (DoD)

| # | Verificação | Comando | Esperado | Observado (colar a saída) | Código de saída |
|---|---|---|---|---|---|
| 1 | FSM completa e fechada | `pytest tests/propostas -q` | todas as transições válidas verdes; inválidas → `INVALID_TRANSITION` | | |
| 2 | Nada executa na menção | `pytest tests/propostas -q -k mencao` | domínio intocado até a decisão | | |
| 3 | Catálogo derivado de permissão | `pytest tests/catalogo -q -k capability` | contagem com/sem `toc:write` impressa | | |
| 4 | Capability no caso de uso | `pytest tests/autorizacao -q` | recusa sem HTTP; sabotagem derruba | | |
| 5 | Traço 100% (inclusive recusas) | `pytest tests/traco -q` | 4 desfechos com traço; sem traço → rejeição | | |
| 6 | Lote honesto | `pytest tests/lote -q` | `outcomes` por alvo; 1 falha ⇒ `status` ≠ `executed` | | |
| 7 | Snapshot sanitizado no servidor | `pytest tests/snapshot -q` | `INVALID_CONTEXT`; `senha_vazada` ausente; teto < 32 KB | | |
| 8 | Wire golden contra a norma | teste de CI (schemas do `protocolos`) | contagem de exemplos validados + código 0 | | |
| 9 | Replay íntegro | `pytest tests/wire -q -k replay` | `?after=0` idêntico; `?after=<último>` vazio | | |
| 10 | Cancelamento cooperativo | `pytest tests/wire -q -k cancel` | `error` `STREAM_CANCELLED` | | |
| 11 | Manifesto valida no schema normativo | script de validação (jsonschema 2020-12) + 3 sabotagens | 0 erros; sabotagens recusadas | | |
| 12 | Borda federada fechada | `pytest tests/borda -q` | sem credencial → recusa com traço; < 5 s | | |
| 13 | Jornada viva presente | `ls docs/jornadas/` | jornada dos 4 fluxos com capturas | | |
| 14 | Conformidade e caminhos | `scripts/check-conformance.sh 006` + `scripts/check-caminhos.sh` + `scripts/check-links.sh` | código 0 + quanto examinaram | | |

## Portões executáveis do roadmap (ciclo 006)

- *(pendente)* Sem capability de escrita, as ações mutadoras **somem do catálogo** —
  teste com a contagem antes/depois na saída (DoD linha 3).
- *(pendente)* Nenhuma mutação proposta por modelo aplica fora da FSM; snapshot sem
  campo não declarado no registro; replay por `seq` testado (DoD linhas 2, 7 e 9).
- *(pendente)* Portão humano: catálogo `toc.*` aprovado ação a ação (registro do gate).

## Cauda de fechamento — a evidência

<!-- One entry per non-n/a TAIL token. What was OBSERVED, never the intention restated. -->
- TAIL:review — *(pendente: quem revisou, contexto fresco, veredito — incluindo a
  conferência de que capability é verificada no caso de uso e não na rota, que nada
  executa fora da FSM, e que o estado terminal do lote nunca afirma mais sucesso que
  os `outcomes`)*
- TAIL:security — *(pendente: o passe — borda sem credencial, capability inflada do
  hospedeiro, injeção via snapshot/`params`, segredo no cliente, dado real em
  fixture/captura — e o resultado por item)*
- TAIL:mutation — *(pendente: cada sabotagem de T-18 — política sempre-verdadeira,
  execução sem traço, transição forçada, campo fora do registro, `executed` mentiroso
  no lote, manifesto sabotado — com o comando e a recusa que imprimiu)*
- TAIL:gate — *(pendente: DoD apresentada ao Product Steward, catálogo conferido
  contra o aprovado, jornada revista, decisão de merge registrada)*

## Cobertura de requisitos

*(pendente — uma linha por RF-01..RF-48, RI-01..RI-12, RNF-01..RNF-10, RN-01..RN-05,
INT-01..INT-06, preenchida no fechamento, cada uma apontando a linha da DoD, o teste
ou a captura que a cobre)*

## Gate pendente

- **Abertura**: gate humano do ciclo 001 fechado + ciclos 003/004/005 promovidos (com
  a aptidão do 003 reexecutada — T-02) + os 5 `[DÚVIDA]` do Clarify respondidos
  (catálogo ação a ação, TTL, atomicidade por ação, `idempotency_key`, alcance da
  borda sob L-03) + os 2 bloqueios externos do round 006 re-medidos.
- **Fechamento**: DoD verde com evidência colada acima, portões do roadmap com
  contagem impressa, matriz `docs/integracao/aderencia-aph.md` atualizada, cauda
  completa, aprovação de merge pelo Product Steward.
