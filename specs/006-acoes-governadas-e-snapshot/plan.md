# Plan 006 — Ações governadas e snapshot (ciclo planejado)

> Siglas: TOC — Teoria das Restrições · APH — Aplicação ↔ Harness · ADR — Architecture
> Decision Record (Registro de Decisão Arquitetural) · DoD — Definition of Done
> (Definição de Pronto) · DoR — Definition of Ready (Definição de Prontidão) · FSM —
> máquina de estados finitos · IA — inteligência artificial · LLM — modelo de linguagem
> de grande porte · SSE — *Server-Sent Events* · UI — interface de usuário · TDD —
> Test-Driven Development (desenvolvimento guiado por teste) · DDD — Domain-Driven
> Design · OTel — OpenTelemetry · CI — integração contínua · JSON — JavaScript Object
> Notation · YAGNI — You Aren't Gonna Need It · MCP — Model Context Protocol · UDE —
> Efeito Indesejável · ARA — Árvore da Realidade Atual

- **Spec**: `spec.md` (Rascunho — aprovação no gate humano que abre o ciclo) · **Raia**:
  plena · **Data**: 2026-09-03
- **Estado**: **planejado no ciclo 001, não executado.** Escrito antes de o ciclo abrir;
  o Constitution Check abaixo avalia o plano como está e será reconferido na abertura,
  com os ciclos 003–005 promovidos.

## Constitution Check (governance/principles.md)

| Princípio | Conformidade |
|---|---|
| I. Spec-driven | ✅ A spec 006 nasce no ciclo 001, antes de qualquer código de fronteira; o catálogo `toc.*` está escrito como contrato ([`contracts/manifesto.json`](contracts/manifesto.json)) **antes** de existir executor. Mudança de escopo (ação nova, classe de risco nova) volta à spec e re-submete o manifesto (RF-03). Os 5 `[DÚVIDA]` vão ao Product Steward no gate de abertura. |
| II. Human-governed orchestration | ✅ O gate humano deste ciclo é duplo e declarado: o catálogo aprovado ação a ação (portão do roadmap — é contrato que circula) e as respostas do Clarify. O conteúdo do ciclo é a própria matriz RACI em código: a IA propõe (Responsible), o humano decide (Accountable) — a FSM é o princípio II compilado. Revisão independente em contexto fresco na cauda. |
| III. Reversibility / risk gates | ✅ A linha executa-direto × propõe é traçada pela reversibilidade em política do servidor (RN-02, APH-6.3); exclusão definitiva fica fora do catálogo da IA; o lote herda o risco mais alto (RF-29); a borda federada nasce fail-closed (RF-32). Política declarativa, autorização fora do modelo — o princípio citado pela própria norma (APH-7.2). |
| IV. Test-first / verifiable DoD | ✅ TDD estrito: a tabela da FSM nasce como teste de transições (todas as válidas + todas as inválidas) antes do código; os golden da norma (`senha_vazada`, schemas do fio) entram como testes de CI; DoD com 14 linhas executáveis; `TAIL:mutation` sabota a política de autorização (`lambda: True`), o traço e a sanitização, e vê os portões recusarem. |
| V. Context economy / boundary | ✅ Corte por fronteira dentro do ciclo: catálogo (fonte única) → FSM/traço → snapshot/registro → wire → borda federada → UI — cada fatia implementável em contexto separado com a spec como integrador. O corte maior já foi feito no roadmap: E7.1/E7.2 saíram no 003 e nada deles se repete aqui. |
| VI. Living artifacts | ✅ O manifesto é consumido pela admissão real (função forçante externa); o registro de telas é consumido pela sanitização (allowlist) e pelo manifesto (teste de paridade RF-36); a matriz `docs/integracao/aderencia-aph.md` é re-verificada no mesmo pull request de fronteira — nenhum artefato sem consumidor. |
| VII. Light governance / YAGNI | ✅ Descartados por YAGNI com porta de volta declarada (INT-06): projeção MCP headless (fora do alvo Nível 2), slot filling estruturado (ciclo 011 se doer), fila de aprovação por classe (uma classe mutadora só, hoje), seleção parcial dentro do lote (o próprio ADR de origem da norma suspeita que seja peso morto). |
| VIII. Intelligible communication | ✅ Bloco de siglas no topo da spec, deste plano, das tasks e do qa-report; termos novos (proposta, traço, lote, snapshot, capability) definidos onde nascem e na linguagem ubíqua. Conferência por amostragem do revisor da cauda. |

### Project Constitution Check (governance/constitution.md — ADR 0001)

| Princípio | Conformidade |
|---|---|
| P1. Fronteira de escrita | ✅ Só este repositório. As lacunas externas já encontradas no planejamento estão declaradas com evidência (L-02 schema do manifesto sem `batch_atomicity`; L-03 borda sem credencial; L-06 `endpoints.actions` inexistente) — se qualquer uma doer na execução, vira `mensagens/NNN-para-<repo>-*`, nunca commit alheio. |
| P2. Federação por contrato (APH) | ✅ É o ciclo que **executa** o P2, e o alcance declarado no princípio é o escopo da spec: catálogo como única superfície (RF-08), verbo mutador nasce `action_proposal` (RF-10), autorização fora do LLM e nos casos de uso (RF-17, RNF-01), tela é dado (RF-40), nenhum segundo protocolo (a borda federada segue a convenção publicada do hospedeiro, não uma invenção nossa — INT-03). Princípio INEGOCIÁVEL: qualquer corte de apetite que toque estes requisitos volta ao Product Steward, não se decide sozinho (regra R3, quarta condição). |
| P3. Domínio puro (DDD + hexagonal) | ✅ FSM, composição de catálogo, sanitização e validação de lote são funções puras testáveis sem rede; wire, borda federada e persistência de traço são adaptadores atrás de portas; `import-linter` continua gate de CI (herdado do 003/004). |
| P4. TDD | ✅ Teste de transição antes da FSM; golden da norma antes da borda; teste de recusa antes da política; o contraexemplo `senha_vazada` da norma vira teste nosso antes do sanitizador existir. |
| P5. Observabilidade de nascença | ✅ Toda proposta com span correlacionado criação→decisão→execução→traço (RNF-06); a borda federada mede o orçamento de 5 s por span (RF-33); teste falha se mutação não emitir traço técnico. |
| P6. Jornada viva | ✅ Jornada dos 4 fluxos (proposta confirmada, recusada, lote com falha parcial, expirada — RI-11), captura por script versionado do build real, heurística datada, mesmo pull request. Base sintética (Instituição Horizonte). |
| P7. Segredo nunca no cliente | ✅ Wire e borda no servidor; nenhum SDK de provedor em lugar nenhum (ADR 0007 — quem fala com modelo é a fundação); grant e snapshot nunca em log (RNF-10). |

**Sem violações.** Nenhum "não aplicável".

## Artefatos deste ciclo (declare todos os cinco — silêncio não é decisão)

| Artefato | Declaração | Por quê |
|---|---|---|
| `research.md` | `ART:research=no` | Não há incógnita de desenho: a FSM, o wire e o lote estão **especificados pela norma** com contraexemplos prontos (Anexo A §A.3/§A.7, APH-5.9); as duas incógnitas reais são externas e viram lacunas com dono (L-03 credencial do hospedeiro, L-04 atenuação), não pesquisa nossa. |
| `data-model.md` | `ART:data-model=no` | Os agregados novos (PropostaDeAção, TraçoDeExecução, SessãoDeConversa) estão modelados na spec § Entidades com invariantes; o modelo persistido do domínio TOC é do ciclo 004 ([`../004-nucleo-de-diagramas/data-model.md`](../004-nucleo-de-diagramas/data-model.md)) e este ciclo só o **referencia**. Um segundo documento duplicaria a spec (Princípio VI). Se a implementação revelar modelo maior, o artefato nasce na abertura por decisão registrada. |
| `contracts/` | `ART:contracts=yes` | O ciclo **é** um contrato: [`contracts/manifesto.json`](contracts/manifesto.json) já validado contra o schema normativo (saída na DoD linha 11 e no qa-report do 001), com as 8 ações `toc.*`, 4 telas e capabilities. O wire não ganha contrato próprio aqui porque o normativo já existe no `protocolos` e o nosso gate é validar contra **ele** (RNF-03) — copiá-lo seria duplicar contrato alheio. |
| `checklist.md` | `ART:checklist=no` | A DoD da spec já é executável (14 linhas com comando); a matriz `docs/integracao/aderencia-aph.md` cumpre o papel de checklist da fronteira e é viva — uma terceira lista duplicaria função. |
| `ux-design.md` | `ART:ux-design=no` | A superfície `proposta-de-acao` herda o desenho decidido no ADR 0009 da irmã (uma tela, origem como dado) e as telas do ciclo 002 ([`../002-prototipo-de-interfaces/`](../002-prototipo-de-interfaces/)); o delta (estados de proposta, lote) entra como ajuste no `ux-design.md` de lá, no mesmo pull request — regra do ciclo 004, mesma razão. |

## Decisões de arquitetura do módulo

1. **Fonte única do catálogo.** Um `ActionSpec` por ação, do qual derivam manifesto,
   catálogo servido e tools — com teste de paridade (RF-04). É a resposta estrutural ao
   APH-4.4 ("uma fonte, duas projeções"; aqui três) e o que impede o manifesto de
   apodrecer separado do código.
2. **FSM no domínio, transições como dados.** A tabela de transições é estrutura
   declarativa validada em código puro; `INVALID_TRANSITION` é exceção de domínio que a
   borda traduz em 409. O estado `stale` da norma (🧪) **não** entra: contexto
   divergente encerra em `cancelled` + `PROPOSAL_CONTEXT_STALE`, o desenho já mapeado
   no §A.8 — aderir ao comprovado, não ao desenhado (spec RF-11).
3. **Traço antes do efeito.** O caso de uso de execução grava o traço em estado
   `executing` antes de tocar o domínio e o fecha com o desfecho; se a gravação do
   traço falhar, a execução não acontece (RF-21 — "ação sem traço é rejeitada" vira
   ordem de operações, não aspiração).
4. **Lote como validação pura.** `validar_lote(acao, alvos)` é função pura que aplica
   as cinco obrigações do APH-5.9 (atomicidade declarada, contagem, risco herdado,
   `outcomes`, estado terminal honesto) antes de qualquer efeito; o executor por item
   só roda depois do sim.
5. **Sanitização como pipeline de três estágios nomeados** (denylist → sensíveis do
   registro → allowlist do registro), cada estágio com teste próprio e o golden
   `senha_vazada` cobrindo o conjunto — espelha os três conjuntos do APH-3.3 para a
   auditoria ler o código com a norma do lado.
6. **Borda federada como adaptador fino**: `/aph/actions/{action_id}` valida
   credencial → valida `params` contra o `input_schema` → invoca o **mesmo caso de
   uso** que o wire invoca. Nenhuma lógica própria: dois adaptadores, uma aplicação —
   é o que garante que a capability é verificada uma vez, no lugar certo (RF-17).
7. **Eventos do wire persistidos como fonte do replay** (mesma tabela que alimenta o
   traço da conversa): replay é `SELECT ... WHERE seq > N`, não reconstrução — a
   garantia do APH-1.3 vem do armazenamento, não de buffer.

## Grafo de dependência das tarefas

```
T-01 (DoD fixada)
  └─► T-02 (junta 003 + ciclos 004/005 verificados)
        └─► T-03 (golden da norma no CI: schemas + senha_vazada, vermelhos)
              ├─► T-04 (ActionSpec fonte única + composição por capability)
              │     └─► T-05 (manifesto gerado da fonte + validação + paridade)
              ├─► T-06 (FSM TDD: tabela + inválidas + TTL + dedup)
              │     └─► T-07 (casos de uso: propor/decidir/executar + capability + traço-antes)
              │           ├─► T-08 (lote: validação pura + outcomes + estado honesto)
              │           └─► T-09 (borda federada /aph/actions + auth + rate limit)
              └─► T-10 (registro de telas + snapshot sanitizado)
T-07, T-10 ─► T-11 (wire: sessões, SSE, seq, replay, cancelamento, códigos)
T-08, T-11 ─► T-12 (UI: proposta-de-acao + desfecho + painel de assistência)
T-12 ─► T-13 (ghd.action_result no canal 003 + inspeção do snapshot)
T-13 ─► T-14 (jornada viva 4 fluxos) ─► T-15 (aptidões + qa-report + matriz aderência)
T-15 ─► cauda (T-16..T-19)
```

## Gates (DoR / DoD)

- **DoR — o ciclo não abre sem**: ciclos 003 (aptidão "a junta fecha" reexecutada),
  004 e 005 promovidos; os 5 `[DÚVIDA]` respondidos — em particular o catálogo
  aprovado ação a ação ([DÚVIDA] 1) e o alcance da borda sob L-03 ([DÚVIDA] 5); os
  bloqueios externos do round 006 re-medidos e aceitos como limite de alcance
  ([`../../docs/produto/rounds.md`](../../docs/produto/rounds.md)).
- **DoD — o ciclo não fecha sem**: as 14 linhas da tabela de aceite verdes com saída
  colada no `qa-report.md` (R1) e o tamanho examinado (R2); os dois portões executáveis
  do roadmap com contagem impressa (ações somem sem `toc:write`; mutação só pela FSM);
  a matriz [`../../docs/integracao/aderencia-aph.md`](../../docs/integracao/aderencia-aph.md)
  atualizada com evidência por linha; cauda completa.
- **Corte de apetite** (estourou → perde escopo, não ganha ciclo): sai primeiro a
  **borda federada** (T-09 — o hospedeiro ainda chama sem credencial, L-03, então o
  valor imediato é baixo e a FSM não depende dela); sai depois a inspeção do snapshot
  (RI-12). **Nunca saem**: FSM, traço 100%, sanitização no servidor, capability no
  caso de uso — são o P2, e cortá-los é decisão do Product Steward, não do agente
  (R3, quarta condição).

## Riscos e portões

| Risco | Ligado a | Mitigação |
|---|---|---|
| GATE-suite — Nível 2 sem suíte executável externa: verde nosso pode ser auto-engano | L-01 | Golden da norma no CI (RNF-03) + sabotagens da cauda (`TAIL:mutation`) + autodeclaração com evidência por path adiada para o ciclo 012, revisada em contexto fresco. |
| GATE-manifesto — schema normativo sem `batch_atomicity` e sem `endpoints.actions` | L-02, L-06 | Atomicidade declarada no catálogo servido; convenção do ADR 0023 seguida à letra; se a admissão real recusar por isso, `mensagens/NNN-para-protocolos-*` com a medição colada (P1). |
| GATE-credencial — borda federada sem credencial do hospedeiro vira porta aberta | L-03 | RF-32: a borda nasce recusando; só `read` responde até o F7 do hospedeiro; teste de sabotagem chama sem credencial e exige recusa com traço. |
| GATE-atenuacao — pressupor APH-9.4b e herdar capability inflada do hospedeiro | L-04 | RF-17/RF-19: verificação local em todo caso de uso, sempre; o teste da DoD linha 4 chama o caso de uso por fora da rota e prova a recusa. |
| GATE-fsm-bypass — um caminho novo (borda, script, rota futura) executar sem FSM | spec RF-08, RF-10 | Decisão de arquitetura 6 (dois adaptadores, uma aplicação) + portão do roadmap: teste prova que nenhuma mutação proposta por modelo aplica fora da FSM. |
| GATE-apetite — 4 épicos de fronteira estourarem o ciclo | roadmap 006 | Corte declarado acima, com o que nunca sai protegido por gate humano. |
