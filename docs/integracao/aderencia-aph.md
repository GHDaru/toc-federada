# Aderência ao Padrão APH — lado aplicação (toc-federada)

> Siglas: APH — Aplicação ↔ Harness · IA — inteligência artificial · LLM — modelo de
> linguagem de grande porte (*Large Language Model*) · ADR — Architecture Decision
> Record (Registro de Decisão Arquitetural) · FSM — máquina de estados finitos · SSE —
> *Server-Sent Events* · UI — interface de usuário · DOM — Document Object Model ·
> TTL — Time To Live (tempo de vida) · KB — kilobyte · MCP — Model Context Protocol ·
> PR — pull request · CI — integração contínua
>
> Matriz de aderência do `GHDaru/toc-federada` contra o **Padrão APH v0.8**
> (`/home/user/protocolos/padrao/padrao-aph.md`), o **Anexo A v0.5** (wire format) e o
> **Anexo B v0.4** (federação, **lado aplicação** — a declaração por lado é obrigação
> do §B.12.1). Alvo declarado: **Nível 2 (Operador)**, `mode: embedded` (ADR 0003).
> Modelo deste documento: a matriz da fundação
> (`/home/user/ghdaru/docs/integration/aderencia-protocolo-aph.md`) e o roteiro de
> conformidade do handoff
> (`/home/user/protocolos/handoffs/ghdaru-roteiro-conformidade-aph-nivel2.md`).
>
> **Estado honesto (2026-09-03)**: o projeto está no ciclo 001 (planejamento). **Nada
> foi implementado; nenhuma linha está atendida; toda coluna de evidência está vazia
> de propósito.** Uma linha só muda de status quando houver path e teste — nunca por
> intenção. A norma evolui em `GHDaru/protocolos`; ao mudar de versão, revisar esta
> matriz.

## Como usar este documento

- É **o artefato vivo da fronteira**: toda spec/PR que tocar a fronteira
  aplicação ↔ harness (catálogo, FSM, snapshot, wire, borda federada, canal `ghd.*`)
  **DEVE declarar quais linhas avança e re-verificar esta matriz no mesmo PR** — a
  mesma regra que a fundação usa na matriz dela.
- O plano por linha vive nas specs: ciclo 003
  ([`../../specs/003-esqueleto-federado/spec.md`](../../specs/003-esqueleto-federado/spec.md)),
  ciclo 006 ([`../../specs/006-acoes-governadas-e-snapshot/spec.md`](../../specs/006-acoes-governadas-e-snapshot/spec.md)),
  ciclo 011 ([`../../specs/011-fundacoes-da-aplicacao/spec.md`](../../specs/011-fundacoes-da-aplicacao/spec.md)),
  ciclo 012 ([`../../specs/012-jornadas-e-autodeclaracao/spec.md`](../../specs/012-jornadas-e-autodeclaracao/spec.md)
  — a autodeclaração formal, em ADR).
- O Nível 2 **não tem suíte executável** (padrão §0 e §8): quando as linhas fecharem, a
  prova é autodeclaração com evidência por path + os golden dos schemas no nosso CI. A
  suíte do Nível 1 do `protocolos` roda contra a nossa URL a partir do ciclo 006.

**Legenda de status**: ● atendido (com path + teste na evidência) · ◑ parcial (com o
que falta nomeado) · **○ planejado — ciclo NNN** (nada implementado; o ciclo é onde a
linha fecha) · ✦ delegado à fundação por desenho (ADR 0007 — a evidência da delegação
entra na autodeclaração do ciclo 012) · ✗ fora do alvo v1 (com a porta de volta).
**Maturidade** (coluna "Mat.") é a da norma: ✅ comprovado · ⚗️ parcial · 🧪 desenhado.

## Nível 1 — Observador

| Req. | O que exige | Mat. | Status | Evidência |
|---|---|---|---|---|
| APH-1.1 | Resposta por streaming SSE sobre POST | ✅ | ○ planejado — ciclo 006 | |
| APH-1.2 | `seq` monotônico atribuído no servidor antes da emissão | ✅ | ○ planejado — ciclo 006 | |
| APH-1.3 | Replay `?after=N` sem perda/duplicação + dedup por `seq` no cliente | ✅ | ○ planejado — ciclo 006 | |
| APH-1.4 | Cancelamento cooperativo com código estável (`STREAM_CANCELLED`) | ✅ | ○ planejado — ciclo 006 | |
| APH-1.5 | Erro como protocolo: envelope estável, códigos fixos documentados | ✅ | ○ planejado — ciclo 006 | |
| APH-2.1 | Vocabulário de eventos fechado, seis famílias mínimas | ✅ | ○ planejado — ciclo 006 | |
| APH-2.2 | Regra de evolução **escrita em contrato** (consumidor ignora; produtor documenta antes) | ✅ | ○ planejado — ciclo 006 | |
| APH-2.3 | Normalizador de provedor (domínio nunca vê formato bruto) | ✅ | ✦ delegado — não há porta de provedor própria (ADR 0007); quem normaliza é a fundação. Registro na autodeclaração — ciclo 012 | |
| APH-2.5 | Agrupar/omitir é do render; ordem de append e replay intocados | ✅ | ○ planejado — ciclo 006 | |
| APH-2.6 | Proveniência na citação (vocabulário fechado) | 🧪 | ✗ fora do alvo v1 — sem geração aumentada por recuperação (RAG) no produto; volta se/quando houver citação | |
| APH-3.1 | Registro de telas como fonte de verdade compartilhada; IA nunca infere a UI | ✅ | ○ planejado — ciclo 006 | |
| APH-3.2 | Snapshot estruturado por mensagem (tela, rota, campos tipados, entidade) | ✅ | ○ planejado — ciclo 006 | |
| APH-3.3 | Sanitização no servidor: denylist + sensíveis + fora do registro | ✅ | ○ planejado — ciclo 006 | |
| APH-3.4 | `context_hash` canônico calculado no servidor (frescor, não autorização) | 🧪 | ○ planejado — ciclo 006 (verificação na confirmação — spec 006 RF-15; emissão canônica completa a decidir lá) | |
| APH-3.5 | Teto de tamanho (< 32 KB de referência) + schema fechado | ✅ | ○ planejado — ciclo 006 | |
| APH-7.1 | Separação de camadas de confiança; snapshot como sistema rotulado | ✅ | ○ planejado — ciclo 006 | |
| APH-7.3 | Tela/dados = dado, nunca instrução | ✅ | ○ planejado — ciclo 006 | |

## Nível 2 — Operador (adicionais)

| Req. | O que exige | Mat. | Status | Evidência |
|---|---|---|---|---|
| APH-4.1 | Catálogo declarado = única superfície executável | ✅ | ○ planejado — ciclo 006 | |
| APH-4.2 | Ação declara `action_id`, título, `input_schema`, classe de risco | ✅ | ○ planejado — ciclo 006 (rascunho do catálogo: [`../../specs/006-acoes-governadas-e-snapshot/contracts/manifesto.json`](../../specs/006-acoes-governadas-e-snapshot/contracts/manifesto.json) — contrato, não implementação) | |
| APH-4.3 | Catálogo derivado das permissões reais na composição | ✅ | ○ planejado — ciclo 006 | |
| APH-4.4 | `input_schema` = mesma definição entregue como *tool* (uma fonte) | 🧪 | ○ planejado — ciclo 006 (fonte única `ActionSpec`; a projeção em tool é da fundação) | |
| APH-5.1 | Toda ação nasce proposta; FSM validada em código; transição fora da tabela falha | ✅ | ○ planejado — ciclo 006 | |
| APH-5.2 | Confirmação proporcional ao risco, decidida fora do modelo e antes da conversa | ✅ | ○ planejado — ciclo 006 | |
| APH-5.3 | `idempotency_key` com deduplicação real | 🧪 | ○ planejado — ciclo 006 (dedup por estado da FSM; chave explícita é o `[DÚVIDA]` 4 da spec 006) | |
| APH-5.4 | Comparar `context_hash` na confirmação → recusa sem execução | ✅ | ○ planejado — ciclo 006 | |
| APH-5.5 | Traço em 100% das ações, inclusive recusadas | ✅ | ○ planejado — ciclo 006 | |
| APH-5.6 | Propostas pendentes sobrevivem à reconexão (via replay) | 🧪 | ○ planejado — ciclo 006 | |
| APH-5.7 | Filas de aprovação separadas por classe de ação | 🧪 | ✗ fora do alvo v1 — uma classe mutadora só; volta quando houver segunda classe com consequência distinta | |
| APH-5.8 | Valores server-authoritative em ação mutadora, construção fail-closed | 🧪 | ✗ fora do alvo v1 — sem submissão de formulário por ação; reavaliar se `SUBMIT` do registro virar ação de catálogo | |
| APH-5.9 | Proposta em lote: uma proposta com N alvos; atomicidade declarada; traço por alvo; contagem antes; estado terminal honesto | 🧪 | ○ planejado — ciclo 006 | |
| APH-6.1 | Comandos de UI declarativos, vocabulário fechado — nunca clique/DOM | ✅ | ○ planejado — ciclo 006 | |
| APH-6.2 | Executor no host (`applyUiCommand` ou equivalente) | ✅ | ○ planejado — ciclo 006 | |
| APH-6.3 | Linha executa-direto × propõe pela reversibilidade, política do servidor | ✅ | ○ planejado — ciclo 006 (a tabela de tipos de ação nasce no ciclo 004) | |
| APH-6.4 | Slot filling estruturado | 🧪 | ✗ fora do alvo v1 — candidato ao ciclo 011; gabarito externo (elicitation do MCP) registrado | |
| APH-6.5 | Nenhuma interface serializada gerada pelo modelo | ✅ | ○ planejado — ciclo 006 | |
| APH-6.6 | Executor de UI consulta risco e recusa mutador fail-closed | ⚗️ | ○ planejado — ciclo 006 (spec 006 RF-48 — as duas metades) | |
| APH-7.2 | Autorização sempre fora do LLM; capabilities verificadas nos casos de uso | ✅ | ○ planejado — ciclos 003 (identidade) e 006 (casos de uso) | |
| APH-7.4 | Auditoria por traço com escopo usuário/tenant | ✅ | ○ planejado — ciclos 003 (OTel/tenant) e 006 (traço de ação) | |
| APH-8.1 | Porta única de LLM; `usage`; chave nunca no cliente | ✅ | ✦ delegado — não há porta de LLM própria por desenho (ADR 0007): quem fala com provedor é a fundação; a metade "chave nunca no cliente" é nossa e é o P7. Registro na autodeclaração — ciclo 012 | |
| APH-8.2 | Intenção por tool calling derivado do catálogo | 🧪 | ✦ delegado — a derivação de tools é do harness da fundação; nosso lado entrega o `input_schema` (APH-4.4, ciclo 006). Registro — ciclo 012 | |

## Anexo B — lado aplicação (obrigações nossas e compartilhadas)

Recorte da [`matriz-obrigacoes.json`](https://github.com/GHDaru/protocolos/blob/main/padrao/matriz-obrigacoes.json)
do `protocolos` para `lado: aplicação` e `lado: ambos` — o lado hospedeiro não é nosso
para declarar (§B.12.1). O canal `postMessage` não tem suíte executável do lado da
aplicação (§B.11.2): quando fechar, a evidência é teste próprio + declaração.

| Cláusula | O que exige (da aplicação) | Status | Evidência |
|---|---|---|---|
| §B.1.3 | Espelho no cliente da verificação de origem do embarque | ○ planejado — ciclo 003 | |
| §B.2.1 | Envelope canônico `{protocol, v, type, payload}`; fora disso, ignorar sem resposta | ○ planejado — ciclo 003 | |
| §B.2.2 | A aplicação fala primeiro (`ghd.ready`) | ○ planejado — ciclo 003 | |
| §B.2.3 | Trava dupla em toda mensagem: `event.source`, depois `event.origin` de configuração, depois conteúdo | ○ planejado — ciclo 003 | |
| §B.2.4 | `targetOrigin` dirigido; `"*"` proibido inclusive no `ghd.ready` | ○ planejado — ciclo 003 | |
| §B.2.5 | Evolução aditiva: `type` desconhecido ignorado sem efeito | ○ planejado — ciclo 003 | |
| §B.3.1 | Sem handshake: modo anônimo (DEVERIA) ou estado honesto | ○ planejado — ciclo 003 (estado "sem canal"; modo anônimo é decisão adiada ao ciclo 011 — `[DÚVIDA]` 2 da spec 003) | |
| §B.3.3 | Nenhum comando direto app→hospedeiro; a aplicação é proponente | ○ planejado — ciclo 006 (por construção: o canal só emite `ghd.ready`/`ghd.action_result`) | |
| §B.4.1 | Recusar subir sem parâmetro de admissão, nomeando qual faltou | ○ planejado — ciclo 003 | |
| §B.5.2 | `app_id` estável; `action_id`/`screen.id` namespaced `toc.*` | ○ planejado — ciclo 006 (contrato já escrito e validado: `contracts/manifesto.json` da spec 006) | |
| §B.5.3 | Ações do manifesto = mesmo `ActionSpec` do §4.4; `ai_actions: []` nunca no snapshot | ○ planejado — ciclo 006 | |
| §B.6.2 | Nunca confiar na credencial do handshake; identidade só pela introspecção | ○ planejado — ciclo 003 | |
| §B.7.1 | Capability `recurso:verbo`, sem curinga | ○ planejado — ciclo 006 | |
| §B.7.2 | Derivação por política pura, verificada nos casos de uso — não na rota | ○ planejado — ciclo 006 | |
| §B.7.3 | Ação sem capability não entra no catálogo visível (ausência, não recusa) | ○ planejado — ciclo 006 | |
| §B.8.1 | Embarcada, renderizar só conteúdo (sem menu/rodapé/seletor próprios) | ○ planejado — ciclo 003 | |
| §B.8.2 | Saber-se embarcada por sinal explícito, nunca heurística de `window.parent` | ○ planejado — ciclo 003 | |
| §B.9.1 | `ghd.action_result` emitido como palpite de UI, nunca prova de execução | ○ planejado — ciclo 006 | |
| §B.9.5 | Payload do handshake é dado; identidade só após introspecção | ○ planejado — ciclo 003 | |
| §B.11.3 / §B.12.1 | Declarar conformidade **por lado** (aplicação) com a maturidade dos itens 🧪 | ○ planejado — ciclo 012 (autodeclaração em ADR) | |

## Requisitos do §4.9 que NÃO são nossos

APH-9.1 a APH-9.5 têm obrigações majoritariamente do **hospedeiro** (admissão,
sandbox, grant, introspecção, atenuação). O que nos toca deles já está distribuído
acima pelas cláusulas do Anexo B (manifesto validável → §B.5; não confiar no token →
§B.6.2; site distinto → obrigação de deploy do ciclo 003, spec 003 RF-36). Duas notas
de risco assumido, com lacuna registrada na spec 006:

- **APH-9.4b é 🧪 sem laboratório**: as capabilities que recebemos podem exceder o
  usuário que abriu o embarque (caso medido na norma, §B.6.7). **Não pressupomos
  atenuação**: re-verificamos localmente em todo caso de uso (spec 006, RF-17/RF-19,
  L-04).
- **A fatia de ações federadas do hospedeiro chama sem credencial** (ADR 0023 de lá):
  nossa borda nasce exigindo autenticação e limita o alcance (spec 006, RF-32, L-03).

## Registro de revisões desta matriz

| Data | O que mudou | Por quem |
|---|---|---|
| 2026-09-03 | Criação no ciclo 001 — todas as linhas planejadas, nenhuma evidência (estado honesto do planejamento) | ciclo 001 |
