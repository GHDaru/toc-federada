# Tasks 006 — Ações governadas e snapshot (ciclo planejado)

> Siglas: TOC — Teoria das Restrições · APH — Aplicação ↔ Harness · ADR — Architecture
> Decision Record (Registro de Decisão Arquitetural) · DoD — Definition of Done
> (Definição de Pronto) · FSM — máquina de estados finitos · IA — inteligência
> artificial · SSE — *Server-Sent Events* · UI — interface de usuário · TDD —
> Test-Driven Development (desenvolvimento guiado por teste) · CI — integração
> contínua · TTL — Time To Live (tempo de vida) · OTel — OpenTelemetry · JSON —
> JavaScript Object Notation · UDE — Efeito Indesejável

> **Ciclo planejado no 001, não executado.** Nenhuma caixa se marca antes do fato; o
> aceite de cada tarefa é executável e a evidência vai para o `qa-report.md` com a
> saída colada (regra R1) e o tamanho examinado (regra R2).

## Verificação primeiro

- [ ] T-01 — Fixar a DoD executável do ciclo (as 14 linhas da spec § Critérios de
  aceite) nos caminhos reais do repositório. · Dep: — · Ref: `spec.md` § Critérios de
  aceite · Aceite: cada linha tem comando que roda no CI local; nenhum critério
  subjetivo.
- [ ] T-02 — Verificar as pré-condições: aptidão do 003 reexecutada ("a junta fecha"),
  ciclos 004/005 promovidos, os 2 bloqueios externos do round 006 re-medidos (borda sem
  credencial; capabilities sem interseção com o usuário). · Dep: T-01 · Ref: plan §
  Gates (DoR); spec L-03, L-04 · Aceite: saídas das re-medições coladas no qa-report,
  com data e commit lido.

## Fundações de teste (o teste nasce antes)

- [ ] T-03 — Golden da norma no CI, vermelhos primeiro: validação dos nossos eventos
  contra `protocolos/padrao/schemas/*.schema.json`; o contraexemplo `senha_vazada`
  como teste de sanitização; manifesto contra `federacao-manifesto.schema.json` com as
  3 sabotagens do ciclo 001 (sem `theme.fallback`, capability curinga,
  `batch_atomicity` no manifesto). · Dep: T-02 · Ref: RNF-02, RNF-03, RF-01; spec
  L-02 · Aceite: suíte existe e falha (nada implementado ainda); sabotagens do
  manifesto recusadas com contagem de erros impressa.

## Catálogo (fonte única)

- [ ] T-04 — `ActionSpec` fonte única das 8 ações `toc.*` + composição por capability
  (função pura): sem `toc:write`, ação `confirm` ausente; capability curinga rejeitada.
  · Dep: T-03 · Ref: RF-04..RF-09, RF-18, RN-05 · Aceite: DoD linha 3 — contagem de
  ações com/sem `toc:write` impressa; `GET /aph/catalog` servido filtrado.
- [ ] T-05 — Manifesto gerado da fonte única + teste de paridade (manifesto ⊆ registro
  de telas; ações do manifesto = ações da fonte) + validação contra o schema normativo
  no CI. · Dep: T-04 · Ref: RF-01..RF-04, RF-36 · Aceite: DoD linha 11 com a saída da
  validação; divergência fonte×manifesto derruba o build.

## Ações governadas (TDD estrito)

- [ ] T-06 — FSM de proposta: tabela declarativa
  `proposed → awaiting_approval → confirmed → executing → executed | failed |
  cancelled | denied | expired`; toda transição válida e toda inválida testadas antes
  do código; TTL → `expired`/`PROPOSAL_EXPIRED`; confirmação duplicada não re-executa;
  `context_hash` divergente → `PROPOSAL_CONTEXT_STALE`. · Dep: T-03 · Ref: RF-10..RF-16
  · Aceite: DoD linhas 1 e 2; cobertura da FSM 100% das transições.
- [ ] T-07 — Casos de uso propor/decidir/executar: capability verificada **no caso de
  uso** (não na rota), fail-closed; traço gravado **antes** do efeito e fechado com o
  desfecho; recusas (política, catálogo, contexto, TTL) todas com traço. · Dep: T-06 ·
  Ref: RF-09, RF-17..RF-23; plan decisão 3 · Aceite: DoD linhas 4 e 5 — caso de uso
  chamado sem HTTP recusa; sabotagem `lambda: True` derruba os testes de recusa;
  sabotagem sem traço → execução rejeitada.
- [ ] T-08 — Proposta em lote: `validar_lote` pura (atomicidade declarada no catálogo
  servido, contagem, risco herdado), execução por item, `outcomes` por alvo, estado
  terminal nunca mais otimista que os `outcomes`. · Dep: T-07 · Ref: RF-24..RF-29,
  RN-04 · Aceite: DoD linha 6 — 1 proposta/8 alvos, 1 falha ⇒ `status` ≠ `executed`;
  lote sobre ação sem `batch_atomicity` recusado.
- [ ] T-09 — Borda federada `POST /aph/actions/{action_id}`: autenticação exigida,
  `params` validados contra o `input_schema`, só `risk: read` enquanto L-03 vigente,
  limite de taxa, orçamento de 5 s medido por span. · Dep: T-07 · Ref: RF-30..RF-33,
  RNF-08; ADR 0023 do hospedeiro (convenção) · Aceite: DoD linha 12. **Primeira tarefa
  a sair se o apetite estourar** (plan § Gates) — a FSM não depende dela.

## Tela é dado

- [ ] T-10 — Registro de telas versionado (compartilhado front/back) + snapshot:
  pipeline de sanitização em 3 estágios no servidor, schema fechado, teto < 32
  kilobytes → `INVALID_CONTEXT`; tela `ai_actions: []` nunca produz snapshot. · Dep:
  T-03 · Ref: RF-34..RF-40 · Aceite: DoD linha 7 — campo fora do registro rejeitado;
  `senha_vazada` ausente de todo prompt montado (golden verde).

## Wire Nível 1

- [ ] T-11 — Sessões e stream: SSE sobre POST com `{seq, kind, payload}` atribuído no
  servidor, eventos persistidos, replay `?after=N` sem perda/duplicação, aprovações
  pendentes reconstruídas, cancelamento cooperativo `STREAM_CANCELLED`, envelope de
  erro com o registro do §A.7 + códigos próprios documentados. · Dep: T-07, T-10 ·
  Ref: RF-41..RF-48 · Aceite: DoD linhas 8, 9 e 10 — golden dos schemas com contagem;
  replay `?after=0` idêntico e `?after=<último>` vazio.

## Interface

- [ ] T-12 — UI: superfície única `proposta-de-acao` (resumo, origem como dado, N
  alvos com contagem, confirmar/recusar), desfecho por alvo, painel de assistência
  (stream tipado, `kind` desconhecido ignorado, cancelar visível), estados de proposta
  (aguardando/expirada/negada/contexto mudou), acessibilidade e tema com fallback.
  · Dep: T-08, T-11 · Ref: RI-01..RI-10 · Aceite: fluxo lote completo no navegador
  (fluxo 6.4 da spec); nenhum `if` sobre a origem no código da tela (revisão + grep).
- [ ] T-13 — Integração com o canal do 003: emissão de `ghd.action_result` (palpite de
  UI) após execução; inspeção "o que a IA vê desta tela" (RI-12). · Dep: T-12 · Ref:
  INT-04, RI-12 · Aceite: teste do canal simulado mostra o envelope canônico; a
  inspeção exibe exatamente o snapshot sanitizado enviado.

## Jornada e fechamento

- [ ] T-14 — Jornada viva dos 4 fluxos (proposta confirmada · recusada · lote com
  falha parcial · expirada), base sintética "Instituição Horizonte", capturas geradas
  por script versionado do build real, avaliação heurística datada, no mesmo pull
  request. · Dep: T-13 · Ref: RI-11; P6 · Aceite: DoD linha 13; capturas regeneram
  determinísticas.
- [ ] T-15 — Rodar TODAS as aptidões (DoD 14 linhas + portões do método) e colar
  saída, código de saída e tamanho examinado no `qa-report.md`; cobertura linha a
  linha (RF/RI/RNF/RN/INT); atualizar a matriz
  `docs/integracao/aderencia-aph.md` com evidência por path nas linhas que este ciclo
  fecha. · Dep: T-14 · Aceite: nenhuma linha com `✓` transcrito sem a saída colada
  (R1/R2); matriz sem linha "atendido" sem path.

## Cauda de fechamento

- [ ] T-16 — `TAIL:review` — revisão independente em contexto fresco por quem não
  implementou, com instrução explícita: conferir que capability é verificada no caso
  de uso e não na rota (a armadilha do §B.7.2 — auditar `Depends(...)` produz falso
  positivo), que nenhum caminho executa fora da FSM, que o estado terminal do lote
  nunca mente, e a seção Fontes da spec por amostragem. · Dep: T-15 · Aceite: veredito
  + achados e o que se fez com eles, no qa-report.
- [ ] T-17 — `TAIL:security` — passe de segurança: borda federada sem credencial,
  capability inflada do hospedeiro (L-04), injeção via snapshot/`params`, segredo no
  cliente, `senha_vazada` em log/traço, dado real em fixture/captura. · Dep: T-15 ·
  Aceite: resultado por item no qa-report.
- [ ] T-18 — `TAIL:mutation` — sabotar e ver recusar: política `lambda: True` (T-07),
  execução sem traço (T-07), transição inválida forçada (T-06), campo fora do registro
  no snapshot (T-10), `status: executed` com `outcomes` contendo falha (T-08),
  manifesto sabotado (T-03). · Dep: T-15 · Aceite: cada sabotagem com o comando e a
  recusa impressa, no qa-report.
- [ ] T-19 — `TAIL:gate` — gate humano: DoD verde apresentada, catálogo `toc.*`
  conferido contra o aprovado na abertura, jornada revista, decisão de merge do
  Product Steward registrada. · Dep: T-16..T-18 · Aceite: registro do gate no
  qa-report e em `docs/records/decisoes.jsonl` via `scripts/record-decision.sh`.
