# Plan 003 — Esqueleto federado

> Siglas: **APH** — Aplicação ↔ Harness · **TOC** — Teoria das Restrições · **ADR** —
> Architecture Decision Record (Registro de Decisão Arquitetural) · **DoD/DoR** —
> Definition of Done / Definition of Ready · **OTel** — OpenTelemetry · **CI** —
> integração contínua · **TDD** — Test-Driven Development · **DDD** — Domain-Driven
> Design · **eTLD+1** — *effective Top-Level Domain plus one* · **TTL** — Time To Live ·
> **IA** — inteligência artificial.

- **Spec**: [`spec.md`](spec.md) · **Raia**: **infra** (plena + reversibilidade) ·
  **Data**: 2026-09-03 · **Status**: planejado — executa após o gate humano do 001 e a
  entrega do 002

## Constitution Check (docs/governance/principles.md — Maestro I–VIII)

| Princípio | Conformidade |
|---|---|
| I. Spec-driven | ✅ Todo o ciclo deriva da `spec.md`, que por sua vez executa os ADRs 0002 e 0003 — nenhuma decisão nova de contrato nasce na implementação. Mudança de escopo (ex.: L-01 persistir) volta à spec antes de virar código. |
| II. Human-governed orchestration | ✅ Três portões humanos declarados no roadmap: aprovação do endereço publicado (irreversível na prática), gate de merge, e a leitura da passagem de segurança. A revisão independente (`TAIL:review`) e a de segurança (`TAIL:security`) rodam em contexto fresco, por quem não implementou. |
| III. Reversibility / risk gates | ✅ É a razão da raia infra: cada ação irreversível ou externa tem reversibilidade **engenheirada** na tabela de gates deste plano (branch Neon antes de migrar, downgrade testado, rollback de deploy ensaiado, credencial rotacionável). A única irreversível de verdade — o endereço público — sobe para portão humano. |
| IV. Test-first / verifiable DoD | ✅ TDD desde o primeiro commit de produção (P4): os testes de admissão, canal e introspecção nascem antes dos adaptadores — os contraexemplos da irmã ([F-02], [F-04], [F-05] da spec) viram testes vermelhos primeiro. A DoD tem 14 linhas, todas com comando. |
| V. Context economy / boundary | ✅ Corte por fronteira dupla: junta (E7.1/E7.2) e chão (E8.1/E8.2/E8.5) — nenhuma ferramenta TOC entra. O catálogo e o wire ficam no 006 justamente para este ciclo caber numa leitura. |
| VI. Living artifacts | ✅ O contrato de admissão é consumido pelo código de admissão (função forçante: os códigos de recusa dos testes vêm dele); o `data-model.md` é consumido pela migração `0001`; a jornada de embarque é gerada do build real. |
| VII. Light governance / YAGNI | ✅ Podados por YAGNI e declarados: modo anônimo (vai à [DÚVIDA] 2), evento de domínio sem consumidor (registrado no data-model), snapshot/catálogo (ciclo 006). Nada além do que a aptidão "a junta fecha" exige. |
| VIII. Intelligible communication | ✅ Todos os artefatos do ciclo abrem com o dicionário de siglas; primeira ocorrência por documento por extenso. A verificação é a leitura da revisão em contexto fresco — que na irmã pegou exatamente esta violação. |

### Project Constitution Check (docs/governance/constitution.md — P1–P7)

| Princípio | Conformidade |
|---|---|
| P1. Fronteira de escrita | ✅ Todo o código nasce em `GHDaru/toc-federada`. O ciclo **depende** de duas ações fora da fronteira — ligar `FEDERATION_MANIFESTS_ENABLED` e admitir o manifesto — e ambas são **pedidas por mensagem** (`mensagens/NNN-para-ghdaru-*`), nunca executadas por nós (L-01, L-02). |
| P2. Federada por contrato (INEGOCIÁVEL) | ✅ O ciclo é a **execução** do P2, e o alcance tocado é declarado: identidade só por introspecção (RF-06..RF-13), envelope canônico sem segundo protocolo (RF-14..RF-17), autorização fora do modelo (RF-12), nenhum verbo mutador exposto (RN-01 — a FSM de proposta chega com o primeiro mutador, no 006). Nada aqui estende nem excetua o princípio. |
| P3. Domínio puro (DDD + hexagonal) | ✅ Identidade e persistência entram por porta (`IdentityPort`, `ProjetoRepository`); introspecção, canal e Postgres são adaptadores na borda. O `import-linter` entra na CI **neste ciclo** (RF-38) — é o primeiro com código, então é aqui que a promessa do ADR 0002 vira gate. |
| P4. TDD | ✅ Teste que falha antes do código, começando pelos contraexemplos registrados na norma (envelope da irmã, `targetOrigin "*"`, `ev.source` ausente) — defeito alheio documentado vira nosso teste de regressão preventivo. |
| P5. Observabilidade de nascença | ✅ RF-32..RF-35: span em todo endpoint desde o primeiro, introspecção correlacionada ponta a ponta, log com `trace_id`, métrica de descarte. O traço é parte da aptidão central, não acessório. |
| P6. Jornada viva | ✅ RI-07: jornada do embarque (feliz + três falhas) com captura gerada por script versionado do build embarcado, avaliação heurística datada, no mesmo pull request. |
| P7. Segredo nunca no cliente | ✅ `TOC_APP_CREDENTIAL` e `DATABASE_URL` só no servidor (RNF-02, RNF-09); grant redigido em toda saída (RNF-01); DoD 13 é o grep que prova ausência de segredo versionado. |

**Sem violações.** O P2 é tocado por execução, não por mudança — declarado acima porque
a lição do ADR 0011→0016 da irmã é que a omissão é o sintoma.

## Artefatos deste ciclo (declare todos os cinco — silêncio não é decisão)

| Artefato | Declaração | Por quê |
|---|---|---|
| `research.md` | `ART:research=no` | Não há incógnita a pesquisar: a norma (Anexo B), o guia da fundação e o código real do introspect foram lidos e citados por linha na spec ([F-01]..[F-20]). A re-medição dos três bloqueios externos é **tarefa com saída colada** (T-02), não documento de pesquisa. |
| `data-model.md` | `ART:data-model=yes` | [`data-model.md`](data-model.md) — o modelo mínimo (tenant_ref, projeto, Principal em memória) que a migração `0001` consome. Existe porque a migração reversível é portão da raia infra, e migração sem modelo declarado é esquema por acidente. |
| `contracts/` | `ART:contracts=yes` | [`contracts/parametros-de-admissao.md`](contracts/parametros-de-admissao.md) — o contrato de admissão com códigos de recusa próprios, consumido pelos testes de admissão (DoD 1). É o artefato que a irmã provou valer: pergunta pendente vira item de especificação. |
| `checklist.md` | `ART:checklist=no` | A DoD da spec já tem 14 linhas executáveis; uma lista paralela duplicaria função servida (Princípio VI). |
| `ux-design.md` | `ART:ux-design=no` | As telas de conteúdo herdam o `ux-design.md` do ciclo 002; o que este ciclo acrescenta — os quatro estados de fronteira — está especificado com job, campos e ação na spec (§ Telas e fluxos, RI-01/RI-02). Se o 002 não entregar a casca, esta declaração vira `yes` e o plano é revisado. |

## Decisões de arquitetura do ciclo

1. **Porta de identidade única** (`IdentityPort.trocar_grant(token) -> Principal`):
   o adaptador de introspecção é o único lugar que conhece `HOST_BASE_URL` e
   `TOC_APP_CREDENTIAL`. Absorve a evolução da norma no §B.6.6 (L-04) sem tocar domínio.
2. **Admissão como função pura de configuração**: `admitir(env) -> Config | RecusaDeAdmissao`
   testável sem processo — o teste de "recusa nomeando o que faltou" roda sem subir
   servidor; o `main` só traduz `RecusaDeAdmissao` em exit ≠ 0 + log.
3. **Adaptador do canal isolado em módulo próprio** (`federacao/` na interface): todo
   `postMessage` entra e sai por ele; a regra "grep de `postMessage` fora do módulo ⇒
   vazio" vira aptidão (DoD 6 cobre o `targetOrigin`; o import-linter cobre o módulo).
4. **Factory de persistência por `DATABASE_URL`** (Postgres × in-memory), o padrão da
   fundação lido em [F-19] — os testes de isolamento rodam in-memory na CI e contra Neon
   no ensaio.
5. **Fail-closed por construção**: os estados de erro (`GRANT_INATIVO`,
   `FUNDACAO_INDISPONIVEL`…) são o retorno **tipado** da porta de identidade — não há
   caminho de código em que exceção vire acesso, porque não há `except` que devolva
   Principal.

## Gates de reversibilidade (raia infra — cada um com ensaio, não promessa)

| Gate | Ação coberta | Reversibilidade engenheirada | Prova (vai ao qa-report) |
|---|---|---|---|
| GATE-migracao | `alembic upgrade` em Neon | **Branch Neon** criado antes de aplicar (backup por cópia); `downgrade` testado em banco limpo | Saída do ciclo upgrade→downgrade sem resíduo (DoD 8) |
| GATE-deploy | Publicação Vercel/Railway | Rollback para o deploy anterior, **documentado e ensaiado uma vez** no ciclo | Saída do ensaio de rollback (DoD 14) |
| GATE-admissao | Registro do manifesto na fundação | Reversível pelo hospedeiro: re-aprovação/remoção pelo painel do admin; nossa credencial é rotacionável a qualquer momento | Registro da submissão + resposta (DoD 12) |
| GATE-endereco | Escolha do eTLD+1 público | **Não reversível na prática** (circula no manifesto) → sobe para portão humano ([DÚVIDA] 1) | Aprovação registrada no gate (DoD 11) |
| GATE-seguranca | Superfície de admissão + embarque | Passagem de segurança em contexto fresco antes do merge — a irmã achou quatro furos na dela; assumir que não temos seria vaidade | Relatório da passagem no qa-report (`TAIL:security`) |

## Riscos (ligados às lacunas da spec)

| Risco | Lacuna | Mitigação no plano |
|---|---|---|
| GATE-manifesto-bloqueado | L-01 (schemas mutuamente exclusivos — 4 erros quando a irmã mediu) | T-02 re-mede na abertura; persistindo, o ciclo entrega tudo menos o registro (decisão já na spec, [DÚVIDA] 5 confirma o fechamento do gate) e T-19 escreve a mensagem |
| GATE-fatia-desligada | L-02 (`FEDERATION_MANIFESTS_ENABLED` off) | Pedido ao operador na abertura (mensagem, não chat); até lá, ensaio contra ambiente de teste ([DÚVIDA] 4) |
| GATE-grants-volateis | L-03 (grants em memória no host) | Nenhuma mitigação nossa: RNF-07 trata reinício como `GRANT_INATIVO` comum, e o teste do estado cobre o caso |
| GATE-norma-experimental | L-04 (§B.6.6 é 🧪) | Decisão 1 (porta única) confina a mudança a um adaptador |
| GATE-sem-baseline | L-06 (desempenho sem medição) | RNF-06 registra a medição em todo embarque; o alvo é calibrado no gate, não inventado antes |

## Grafo de dependência das tarefas

```
T-01 DoD ─┬─ T-02 re-medição dos bloqueios (L-01..L-03)
          ├─ T-03 admissão fail-fast ──── T-04 porta de identidade ── T-05 introspecção real
          ├─ T-06 esqueleto FastAPI+OTel ─┬─ T-07 migração 0001 ── T-08 isolamento por tenant
          │                               └─ T-09 rota de leitura de projetos
          ├─ T-10 adaptador do canal ──── T-11 telas de estado ── T-12 tema com fallback
          └─ T-13 CI ── T-14 deploy ── T-15 ensaio de rollback ── T-16 manifesto+submissão
                                   └── T-17 jornada viva ── T-18 medição do embarque
T-19 mensagens externas (se L-01/L-02 persistirem)  ·  depois: a cauda (TAIL:*)
```

Paralelizável por fronteira: {T-03..T-05 identidade} · {T-06..T-09 serviço} ·
{T-10..T-12 interface} — integram em T-16/T-17.

## Gates DoR / DoD

**DoR (o ciclo não abre sem):**
- Gate humano do ciclo 001 aprovado; ciclo 002 entregue (a casca que este esqueleto
  embarca) — ou `ART:ux-design` revisto para `yes`.
- ADRs 0002 e 0003 ratificados (o ciclo é a execução deles).
- Re-medição dos três bloqueios externos com saída colada (T-02).
- Respostas do Clarify (5 dúvidas), ao menos as [DÚVIDA] 1 e 3 — endereço e capabilities
  entram no manifesto e mudam entrega.
- `scripts/check-specs.sh` com esta spec ≥ 80.

**DoD:** as 14 linhas executáveis da spec (§ Critérios de aceite) + os cinco gates de
reversibilidade com prova + a cauda completa (`TAIL:review`, `TAIL:security`,
`TAIL:mutation` sobre a lógica de admissão/verificação, `TAIL:gate`) com evidência no
[`qa-report.md`](qa-report.md).
