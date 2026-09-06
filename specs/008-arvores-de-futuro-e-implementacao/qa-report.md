# QA Report 008 — Árvores de Futuro e Implementação

> Siglas: **QA** — Quality Assurance (garantia de qualidade) · **DoD** — Definition of
> Done (Definição de Pronto) · **UDE** — Efeito Indesejável (*Undesirable Effect*) ·
> **NC** — Nuvem de Conflito · **ARF** — Árvore da Realidade Futura · **APR** — Árvore
> de Pré-Requisitos · **AT** — Árvore de Transição · **OI** — Objetivo Intermediário ·
> **FSM** — máquina de estados finitos · **IA** — inteligência artificial · **SDK** —
> Software Development Kit (kit de desenvolvimento).

**Execução do serviço (domínio, aplicação, persistência, superfície HTTP e catálogo)
concluída em 2026-09-06.** As linhas abaixo trazem a saída **colada** dos comandos (R1) e
o denominador que cada um imprimiu (R2). O que **não** foi executado neste lote está
declarado no fim do arquivo, com o nome de quem falta — silêncio não é decisão.

> **Ajuste de caminho declarado**: a coluna "Verificação executável" da spec cita
> `tests/domain/…` e `backend/src/…`; a árvore real deste repositório é
> `apps/api/tests/dominio/…` e `apps/api/src/toc_api/…` (decidida no ciclo 003, brief §3).
> Os comandos abaixo são os mesmos critérios sobre os caminhos que existem.

## Pré-condições de abertura (T-01)

| Pré-condição | Verificado em | Evidência (saída colada) | Estado |
|---|---|---|---|
| Ciclo 005 promovido (a ARA e o UDE `Validado` existem) | — | — | — |
| Ciclo 007 promovido (a NC e a injeção `escolhida` existem) | — | — | — |
| FSM do 006 no ar (as ações do M4 executam por ela) | — | — | — |
| Decisão registrada: ramos negativos manuais nesta v1 | — | — | — |
| 5 `[DÚVIDA]` do Clarify respondidos no gate | — | — | — |

## DoD (16 linhas da spec — comando, saída colada, quanto examinou)

| # | Critério | Comando | Saída (colada) | Examinou | Código de saída |
|---|---|---|---|---|---|
| 1 | Cadeia inteira percorrida com referência em cada elo | `pytest tests/dominio/test_encadeamento.py -k cadeia_completa` | `1 passed, 16 deselected in 0.13s` | 1 teste; a saída nomeia os 4 elos, as 5 ferramentas e o papel de cada origem | `0` |
| 2 | Referência só por ação nomeada; sobrevive a exclusão suave | `pytest tests/dominio/test_referencia_cruzada.py` | `16 passed in 0.11s` · `sequências de exclusão/restauração exercidas: 120` | 16 testes, incluindo a propriedade da RNF-09 sobre **120** sequências | `0` |
| 3 | Promoção exige `Validado`; semeadura exige `escolhida` | `pytest tests/dominio/test_encadeamento.py -k "recusa"` | `6 passed, 11 deselected in 0.13s` | 6 casos de recusa, com a regra nomeada em cada um | `0` |
| 4 | Três árvores atravessam o banco ida-e-volta com referências | `pytest tests/integracao/test_m4_no_postgres.py` | `10 passed in 10.26s` | 10 testes contra o PostgreSQL real; a exportação canônica do E1.4 é do ciclo 011 (ver pendências) | `0` |
| 5 | Sequenciamento acíclico, em camadas, com elipses | `pytest tests/dominio/test_apr.py -k "sequenciamento or elipse or circular"` | `7 passed, 19 deselected in 0.11s` | 7 testes; o de ciclo imprime `bloqueado=True` com o ciclo nomeado | `0` |
| 6 | Verificação da ARF pura e correta | `pytest tests/dominio/test_arf.py` + `lint-imports` | `26 passed in 0.08s` · `Contracts: 3 kept, 0 broken.` | 26 testes de domínio (offline) + 3 contratos de arquitetura sobre 112 arquivos | `0` |
| 7 | Verbalização avaliada offline sobre corpus versionado | `pytest tests/dominio/test_verbalizacao.py` | `29 passed in 0.04s` · `corpus de verbalização v1.0.0: 19 casos examinados — 8 bons, 9 maus, 2 indeterminados; 12 de obstáculo, 7 de objetivo intermediário` | 19 casos do corpus + 10 testes de alcance | `0` |
| 8 | Ramo negativo sem rota assistida | `grep -rn "suggest_negative\|negative_branch" apps/api/src apps/web/src \| wc -l` | `0` | as duas árvores de código-fonte | `0` |
| 9 | Tripla do passo obrigatória; divergência preservada | `pytest tests/dominio/test_at.py` | `18 passed in 0.10s` | 18 testes; a divergência esperado × real sai no evento e o esperado não é sobrescrito | `0` |
| 10 | Ações do M4 só mutam por `action_proposal` | `pytest tests/federacao/test_catalogo_m4.py` | `17 passed in 0.18s` | 17 testes: propor não escreve (4 ações), recusar deixa byte a byte igual, aceite cria, recusa deixa traço | `0` |
| 11 | Sem SDK, chave ou prompt no produto | `grep -rniE "genai\|openai\|anthropic\|api[_-]?key\|promptText\|system_prompt" apps/api/src/toc_api/dominio/ \| wc -l` | `3` — as três ocorrências são a **denylist de segredos** do snapshot (`api_key`, `apikey` e o comentário que as explica), não SDK nem chave; ver pendência P-03 | domínio inteiro | `0` (grep) |
| 12 | Telas do módulo registradas | `grep -c "toc\.arf_canvas\|toc\.apr_canvas\|toc\.apr_sequencia\|toc\.at_canvas\|toc\.cadeia" apps/api/src/toc_api/dominio/federacao/telas.py` | `5` | o registro de telas inteiro (9 telas) | `0` |
| 13 | Toda mutação nova com traço | `pytest tests/aplicacao/test_casos_de_uso_do_m4.py` | `15 passed in 0.16s` | 15 testes; o span de promover carrega `toc.referencia_id`, o de excluir carrega `toc.referencias_suspensas`, o do passo carrega `toc.divergente` | `0` |
| 14 | Jornada viva da cadeia sintética | — | — | — | **pendente (P-01)** — a interface do M4 não entra neste lote |
| 15 | Conformidade do ciclo | `scripts/check-conformance.sh 008` | ver bloco abaixo | — | ver P-02 |
| 16 | Caminhos e links | `scripts/check-caminhos.sh` · `scripts/check-links.sh` | `✓ todo caminho citado entre crases existe.` (1002 caminhos · 330 isentos) · `✓ every relative link resolves.` (checked: 469) | 125 arquivos · 469 links | `0` · `0` |

## Portões nomeados do roadmap (ciclo 008)

| Portão | Como se verificou | Evidência colada |
|---|---|---|
| Teste de domínio percorre a cadeia inteira e prova a referência de origem em cada elo | `pytest tests/dominio/test_encadeamento.py -k cadeia_completa -v` | `1 passed, 16 deselected in 0.13s`; a saída nomeia os quatro elos (`promocao_ude_nc`, `semeadura_injecao_arf`, `derivacao_arf_apr`, `derivacao_oi_at`), cada um com o papel da origem e `estado=ativa`, e a travessia `ara → nc → arf → apr → at` nos dois sentidos |
| As três árvores atravessam o banco com as referências | `pytest tests/integracao/test_m4_no_postgres.py` | `10 passed in 10.26s` — contra o PostgreSQL real, com a migração `0006` aplicada em esquema descartável. A **exportação canônica** do E1.4 é entrega do ciclo 011 (P-04) |
| Jornada da injeção à APR sequenciada, com captura | — | **pendente (P-01)** — depende da interface do M4 |

## Medições registradas (RNF-04 / RNF-05 / RNF-06)

| Métrica | Alvo | Valor medido | Fonte |
|---|---|---|---|
| Sequenciamento com 100 OIs / ~200 dependências (p95) | < 2 s | **4,57 ms** — `RNF-04 sequenciamento: 100 objetivos intermediarios, 197 dependencias, 100 camadas · p95 = 4.57 ms (teto 2000 ms) · 20 execucoes` | script de medição sobre o domínio puro, 20 execuções |
| Vista da cadeia com até 50 referências (p95) | < 1 s | **0,51 ms** — `RNF-05 vista da cadeia: 50 referencias, 50 elos resolvidos · p95 = 0.51 ms (teto 1000 ms) · 20 execucoes` | idem, 20 execuções |
| Verbalização avaliada de texto ≤ 500 caracteres | < 100 ms | **0,733 ms** — `RNF-06 verbalizacao: texto de 498 caracteres · p95 = 0.733 ms (teto 100 ms) · 200 execucoes` | idem, 200 execuções |

## Rede de proteção da extração (T-03)

| Verificação | Comando | Saída (colada) | Estado |
|---|---|---|---|
| Suíte do ciclo 005 continua verde após a extração do pacote de suficiência | `pytest tests/dominio/test_ara.py tests/dominio/test_analise_estrutural.py tests/dominio/test_corpus_udes.py tests/dominio/test_validacao_formal.py tests/dominio/test_suficiencia_compartilhada.py tests/contrato/test_http_ara.py` | `170 passed, 2 warnings in 10.85s` | ✓ verde |
| Nenhuma regra de suficiência duplicada (um único módulo de definição) | `pytest tests/dominio/test_suficiencia_compartilhada.py` | `13 passed in 0.11s` — a prova é de **identidade** (`ara.EstadoDoExame is suficiencia.EstadoDoExame` para as 5 peças), não de comportamento: duas cópias que ainda não divergiram passariam num teste de comportamento | ✓ verde |

## Cauda

| Item | Executor (contexto fresco) | Achados | Evidência |
|---|---|---|---|
| TAIL:review | — | — | — |
| TAIL:security | — | — | — |
| TAIL:mutation | — | — | — |
| TAIL:gate | — | — | — |

## Suíte inteira, no fim do lote

```text
$ cd apps/api && DATABASE_URL='postgresql+psycopg://toc@/toc_federada?host=/var/run/postgresql&port=5433' \
    pytest -q --ignore=tests/dominio/test_focalizacao.py --ignore=tests/dominio/test_heranca.py \
             --ignore=tests/dominio/test_jornada_completa.py --ignore=tests/dominio/test_vinculos.py
1100 passed, 12 warnings in 131.25s (0:02:11)
```

Os quatro `--ignore` **não** são exclusão de teste deste ciclo: são os quatro arquivos do
**M6 (Focalização, spec 009)** que outro construtor está escrevendo neste mesmo
repositório e que ainda importam `toc_api.dominio.focalizacao`, um módulo que ainda não
existe — testes vermelhos de um lote em andamento (P4: o teste vem antes do código). Sem
os `--ignore`, o pytest interrompe a **coleta** inteira e nenhuma suíte roda. O número
acima é o que este lote entrega; o do M6 é do lote dele.

## Pendências declaradas (o que este lote NÃO entregou)

| # | Pendência | Por quê | Quem fecha |
|---|---|---|---|
| P-01 | **Interface React do M4** (canvas ARF/APR/AT, painel de ramos, tabela resumo, vista da cadeia) e a **jornada viva** com captura do build real | O lote pedia domínio, casos de uso, persistência, superfície HTTP e catálogo — a interface e a jornada (DoD 14 e o terceiro portão do round) ficaram fora do recorte | o ciclo de interface do M4, com `ux-design.md` no gate de UX antes de qualquer tela |
| P-02 | `scripts/check-conformance.sh 008` não foi executado como fechamento | O ciclo 008 não foi **aberto** por `scripts/new-cycle.sh`: os artefatos vieram do planejamento do ciclo 001, e o conformance mede um ciclo aberto | o gate humano de abertura/fechamento do ciclo |
| P-03 | O `grep` da DoD 11 devolve `3`, não `0` | As três ocorrências são a **denylist de segredos** do snapshot (`api_key`, `apikey` e o comentário que as explica) — o oposto de um SDK no produto. É condição **anterior** a este lote (o mesmo grep já devolvia 3 antes do M4) e o critério, como escrito, não distingue "cita o nome do segredo para bloqueá-lo" de "usa o segredo" | o critério merece ser reescrito na spec, ou a denylist isentada por nome, no fechamento do ciclo |
| P-04 | Exportação/importação canônica dos três tipos (INT-10, DoD 4 na letra) | A exportação determinística do E1.4 é entrega do **ciclo 011**; aqui o que se prova é que as três árvores e as referências atravessam o banco ida-e-volta | ciclo 011 (E1.4 avançado) |
| P-05 | Cauda (`TAIL:review`, `TAIL:security`, `TAIL:mutation`) e `TAIL:gate` | Revisão em contexto fresco é de **outro** agente por princípio (Maestro II: quem executa não verifica); o gate é humano e indelegável | revisor independente + Product Steward |

## Veredito

— (o veredito só existe depois da cauda completa; caixa marcada não é testemunha)
