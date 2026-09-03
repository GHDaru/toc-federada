# Spec 006 — Ações governadas e snapshot (M7 — Federação APH)

> Siglas: TOC — Teoria das Restrições · APH — Aplicação ↔ Harness · IA — inteligência
> artificial · ADR — Architecture Decision Record (Registro de Decisão Arquitetural) ·
> RF/RI/RNF/RN/INT — requisito funcional / de interface / não funcional / regra de
> negócio / integração · US — User Story · DoD — Definition of Done (Definição de
> Pronto) · FSM — máquina de estados finitos · SSE — *Server-Sent Events* · HTTP —
> HyperText Transfer Protocol · JSON — JavaScript Object Notation · UI — interface de
> usuário · LLM — modelo de linguagem de grande porte (*Large Language Model*) · UDE —
> Efeito Indesejável · ARA — Árvore da Realidade Atual · TTL — Time To Live (tempo de
> vida) · OTel — OpenTelemetry · CI — integração contínua · TDD — Test-Driven
> Development (desenvolvimento guiado por teste) · KB — kilobyte · MCP — Model Context
> Protocol · DOM — Document Object Model

- **Status**: Rascunho — ciclo **planejado, não executado** (abre após o ciclo 005;
  gate humano do ciclo 001)
- **Raia**: plena
- **Data**: 2026-09-03
- **Origem**: [`../../docs/roadmap.md`](../../docs/roadmap.md) ciclo 006 ·
  [`../../docs/produto/modulos.md`](../../docs/produto/modulos.md) (M7, épicos
  E7.3–E7.6) · ADR 0003 (federação) e ADR 0007 (IA somente pela fundação), que este
  ciclo executa

## O quê e por quê

Este ciclo completa o módulo M7 (Federação APH): ele transforma a junta que o ciclo 003
fechou — identidade, embarque, banco, traço — na **fronteira conversacional governada**
que faz da aplicação um Operador de verdade. Entram os quatro objetos que faltam: o
**catálogo `toc.*`** como única superfície executável, derivado das permissões reais; a
**FSM de proposta** pela qual todo verbo mutador do modelo atravessa antes de tocar o
domínio; a **tela como dado** — registro de telas e snapshot sanitizado no servidor,
com schema fechado e teto de tamanho; e o **wire APH Nível 1** (SSE sobre POST, `seq`,
replay, cancelamento, códigos de erro estáveis). O primeiro consumidor é a assistência
da ARA (E2.3 do módulo M2): sugerir UDEs, analisar suficiência, criar nós em lote —
tudo por proposta, nunca por execução direta.

O motivo de ser um ciclo próprio, e não uma fatia dos ciclos de ferramenta, é o P2
(federação por contrato, inegociável): a governança de ação é **uma** e serve a todas as
ferramentas — construí-la dentro do M2 a faria nascer acoplada à ARA, e cada módulo
seguinte reimplementaria a sua metade, que é exatamente como nasce um segundo protocolo.
A lição de forma vem paga pela irmã `gestaodeprioridades`: o ADR 0009 dela decidiu que a
superfície de confirmação é **uma só** para humano e IA e que **lote é uma proposta, não
N propostas** [F-05] — decisão que a norma APH absorveu como o requisito APH-5.9,
citando aquele ADR como fonte [F-04]. Este ciclo herda as duas coisas prontas.

**Recorte declarado.** Cobre os épicos **E7.3** (manifesto e catálogo `toc.*`), **E7.4**
(ações governadas), **E7.5** (tela é dado) e **E7.6** (wire Nível 1) do módulo M7. Os
épicos **E7.1** (identidade e admissão) e **E7.2** (embarque) **saem no ciclo 003** —
[`../003-esqueleto-federado/spec.md`](../003-esqueleto-federado/spec.md) — e nenhum
requisito deles se repete aqui: esta spec **consome** a introspecção, o Principal com
`capabilities`, o canal `ghd.*` e o deploy próprio como dados do 003.

## O que entra como dado

- **ADR 0003** ([`../../docs/adr/0003-federacao-aph-nivel-2-embedded.md`](../../docs/adr/0003-federacao-aph-nivel-2-embedded.md)):
  alvo Nível 2 (Operador), `mode: embedded`, `app_id: toc`, namespace `toc.*`. Uma
  aplicação que "conversa integralmente" é Nível 2, e o Nível 2 exige o §4.2 completo,
  §4.4–§4.8 do padrão [F-20] — é o mapa de obrigações deste ciclo.
- **ADR 0007** ([`../../docs/adr/0007-ia-somente-pela-fundacao.md`](../../docs/adr/0007-ia-somente-pela-fundacao.md)):
  nenhum SDK de provedor no produto. Quem fala com modelo é a fundação; esta aplicação
  **se descreve** (snapshot + catálogo) e **governa** (FSM + traço). A porta única de
  LLM (APH-8.1) é da fundação, não nossa — a matriz de aderência declara isso por linha.
- **A junta do ciclo 003**: Principal com `capabilities` vindas da introspecção
  ([`../003-esqueleto-federado/spec.md`](../003-esqueleto-federado/spec.md) RF-06..RF-13),
  isolamento por tenant, OTel e CI. Sem a aptidão "a junta fecha" verde, este ciclo não
  abre (DoR no plan).
- **O ciclo 005 promovido**: as primeiras ações do catálogo operam sobre a ARA
  ([`../005-arvore-da-realidade-atual/spec.md`](../005-arvore-da-realidade-atual/spec.md));
  os casos de uso de mutação que a FSM invoca já existem lá, com as regras de domínio.
- **A política por tipo de ação do ciclo 004**
  ([`../004-nucleo-de-diagramas/spec.md`](../004-nucleo-de-diagramas/spec.md), plan
  § Decisões 5): o vocabulário de classes de risco nasce lá e o catálogo `toc.*` o
  reutiliza — uma tabela, não duas.
- **A norma**: Padrão APH v0.8 (§4.2–§4.8), Anexo A v0.5 (wire) e Anexo B v0.4 (lado
  aplicação) — fontes [F-01]…[F-26], todas lidas e citadas por linha. O manifesto desta
  spec ([`contracts/manifesto.json`](contracts/manifesto.json)) **já valida** contra o
  schema normativo, com a saída colada na DoD (linha 11).

## Épicos, features e user stories

### E7.1 — Identidade e admissão · E7.2 — Embarque *(saem no ciclo 003)*

Entregues por [`../003-esqueleto-federado/spec.md`](../003-esqueleto-federado/spec.md)
(RF-01..RF-27 de lá). Aqui só a dependência: toda autorização deste ciclo parte do
Principal que a introspecção do 003 construiu, e o canal `ghd.*` de lá é por onde o
sinal `ghd.action_result` (palpite de UI, nunca prova) passa a ser emitido quando uma
ação executa (INT-04).

### E7.3 — Manifesto e catálogo `toc.*`

**F7.3.1 — Manifesto embedded** — a aplicação se declara por manifesto validável contra
o schema normativo do Anexo B; o rascunho é [`contracts/manifesto.json`](contracts/manifesto.json).

- US-01 — Como **Administradora do tenant**, quero admitir a aplicação a partir de um
  manifesto que valida contra o schema da norma, para a admissão ser conferência, não
  adivinhação.
  - Dado o `contracts/manifesto.json`, Quando o valido contra
    `federacao-manifesto.schema.json` (draft 2020-12), Então zero erros — e a sabotagem
    (remover `theme.fallback`, capability curinga) é rejeitada.

**F7.3.2 — Catálogo derivado de permissão** — uma fonte, três projeções: o mesmo
`ActionSpec` valida os `args` da proposta, vira a *tool* que a fundação entrega ao
modelo e entra no manifesto.

- US-02 — Como **Gestora**, quero que a IA só proponha o que eu posso fazer, para uma
  sugestão nunca ser um convite a um erro de permissão.
  - Dado um Principal sem `toc:write`, Quando o catálogo é composto, Então nenhuma ação
    `risk: confirm` aparece — ausência, não recusa — e a contagem antes/depois sai no
    teste (portão do roadmap).
- US-03 — Como **Agente de IA da fundação** (persona de contrato), quero que o catálogo
  seja a única superfície executável, para nenhum endpoint fora dele ser alcançável por
  mim.
  - Dado um `action_id` fora do catálogo composto, Quando uma proposta o cita, Então a
    proposta é recusada com traço e nada executa.

### E7.4 — Ações governadas

**F7.4.1 — FSM de proposta** — nenhuma ação executa na menção; toda ação nasce proposta
com identidade própria e atravessa a FSM validada em código.

- US-04 — Como **Participante**, quero que toda mutação sugerida pela IA espere a minha
  decisão, para a árvore nunca mudar sem alguém ter dito sim.
  - Dado um `action_proposal` de `toc.criar_nos`, Quando o stream o emite, Então o
    domínio está intocado até a confirmação — e confirmar fora de
    `awaiting_approval` falha com `INVALID_TRANSITION`.

**F7.4.2 — Autorização por capability nos casos de uso** — a verificação vive no caso
de uso, não na camada de rota (§B.7.2), e é fail-closed.

- US-05 — Como **Administradora do tenant**, quero que a permissão seja verificada onde
  a ação acontece, para nenhum caminho novo (rota, borda federada, script) nascer por
  fora dela.
  - Dado um caso de uso de mutação chamado **diretamente** (sem rota), Quando o
    Principal não tem `toc:write`, Então a recusa acontece ali, com traço — e o teste
    prova isso sem HTTP.

**F7.4.3 — Traço de 100%** — toda ação executada **e** toda recusada deixa traço
auditável no servidor e visível na conversa.

- US-06 — Como **Gestora**, quero perguntar "o que a IA fez neste projeto" e ter
  resposta completa, para a auditoria não depender de memória de ninguém.
  - Dado um dia de uso com execuções e recusas, Quando consulto o traço do projeto,
    Então cada proposta aparece com desfecho — inclusive as negadas e as expiradas.

**F7.4.4 — Proposta em lote** — ação com N alvos é **uma** proposta (APH-5.9; a decisão
é herdada do ADR 0009 da irmã [F-05]).

- US-07 — Como **Facilitadora TOC**, quero confirmar oito UDEs sugeridas numa tela só,
  vendo as oito e a contagem, para o rigor não virar oito cliques que ensinam a não ler.
  - Dado `toc.criar_nos` com 8 alvos, Quando confirmo uma vez, Então os 8 aparecem
    antes da decisão, o desfecho sai por alvo (`outcomes`) e, se um falhar, o `status`
    da proposta **não** diz `executed`.

**F7.4.5 — Borda de execução federada** — `POST /aph/actions/{action_id}`, a convenção
do ADR 0023 do hospedeiro [F-15], com `params` tratados como não-confiáveis.

- US-08 — Como **Administradora do tenant**, quero que a borda que o hospedeiro chama
  recuse chamada não autenticada e parâmetro inválido, para a aplicação nunca depender
  da validação que o hospedeiro declaradamente não faz [F-16].
  - Dado um POST sem credencial verificável, Quando ele chega em
    `/aph/actions/toc.criar_nos`, Então a resposta é recusa com traço — e nenhum caso
    de uso é invocado.

### E7.5 — Tela é dado

**F7.5.1 — Registro de telas** — fonte de verdade compartilhada entre frontend e
backend: cada tela com identidade, rota, campos tipados (`ai_visible`) e ações
(`ai_actions`).

- US-09 — Como **Participante**, quero que a IA saiba em que tela estou pelo registro,
  para a assistência ser precisa sem ninguém raspar a minha tela.
  - Dado a tela `toc.ara` aberta, Quando envio uma mensagem, Então o snapshot carrega o
    identificador da tela e só os campos que o registro declara `ai_visible`.

**F7.5.2 — Snapshot sanitizado no servidor** — schema fechado, teto declarado abaixo de
32 KB, sanitização antes do modelo, sempre no servidor.

- US-10 — Como **Administradora do tenant**, quero que campo sensível ou desconhecido
  nunca chegue ao modelo, para a fronteira de privacidade não depender do cliente se
  comportar.
  - Dado um snapshot com o campo `senha_vazada` (o contraexemplo do gate da norma
    [F-25]), Quando ele chega ao servidor, Então é rejeitado com `INVALID_CONTEXT` — e
    o teste prova que o valor não aparece em nenhum prompt montado.

### E7.6 — Wire APH Nível 1

**F7.6.1 — Transporte e sequência** — SSE sobre POST, envelope `{seq, kind, payload}`,
`seq` monotônico atribuído no servidor.

- US-11 — Como **Participante**, quero ver a resposta da assistência chegando em
  streaming tipado, para acompanhar raciocínio, proposta e resultado como eventos
  distintos, não como um texto amorfo.
  - Dado uma mensagem enviada, Quando o stream responde, Então cada frame é um JSON
    completo `{seq, kind, payload}` com `seq` crescente e o stream termina com `done`
    ou `error`.

**F7.6.2 — Replay e reconexão** — `?after=N` sem perda nem duplicação; aprovações
pendentes sobrevivem.

- US-12 — Como **Facilitadora TOC**, quero recarregar a página no meio de uma proposta
  pendente e reencontrá-la, para reconexão nunca custar governança (APH-5.6).
  - Dado uma proposta `awaiting_approval` e a conexão derrubada, Quando o cliente
    reconecta com `?after=N`, Então a conversa reconstrói sem duplicar e o gate
    pendente reaparece.

**F7.6.3 — Cancelamento cooperativo** — endpoint dedicado, verificação no laço, nunca
em silêncio.

- US-13 — Como **Participante**, quero cancelar uma resposta longa e saber que
  cancelei, para o botão não ser decorativo.
  - Dado um stream em andamento, Quando chamo `DELETE .../stream`, Então o stream
    termina com `error` de código `STREAM_CANCELLED`.

**F7.6.4 — Erros como protocolo** — envelope estável, códigos fixos em
`MAIUSCULAS_COM_SUBLINHADO`, registro mínimo do §A.7 adotado.

- US-14 — Como **Agente de IA da fundação** (consumidor do wire), quero discriminar
  falha por código, nunca por mensagem, para o meu tratamento de erro não quebrar
  quando o texto mudar de idioma.
  - Dado qualquer falha da fronteira, Quando o erro chega, Então `{code, message,
    details?}` com código do registro (ou extensão nossa documentada) — e o teste
    verifica que nenhum código sai em minúsculas.

## Entidades e modelo de domínio

Sem tabela física aqui (DDD puro); os agregados TOC (Projeto, Nó, Aresta) vêm dos
ciclos 004–005 — este ciclo acrescenta a governança em volta deles:

- **PropostaDeAção** (agregado): `proposal_id`, `action_id`, `args` validados contra o
  `input_schema`, `risk`, `origem` (`humano` | `ia` — dado, nunca desvio de fluxo,
  ADR 0009 da irmã [F-05]), estado da FSM, `criada_em`, TTL, `alvos[]` quando lote.
  Invariantes: transição só pela tabela da FSM (fora dela, exceção → `INVALID_TRANSITION`);
  estado terminal é imutável; em lote, `status` terminal nunca afirma mais sucesso que
  os `outcomes` [F-10].
- **TraçoDeExecução** (entidade, somente-acréscimo): `proposal_id`, desfecho, desfecho
  por alvo quando lote, `tenant_id`, `user_id`, `trace_id` OTel. Invariante: existe
  para **todo** desfecho, inclusive recusa — execução sem traço é rejeitada antes do
  efeito [F-03].
- **CatálogoComposto** (objeto de valor, derivado — nunca persistido): função pura
  `compor(catalogo_base, capabilities) → ações visíveis`. Invariante: ação cuja
  capability o Principal não tem **não está** no resultado (ausência é a fronteira,
  §B.7.3 [F-13]).
- **RegistroDeTelas** (objeto de valor versionado, compartilhado front/back): telas com
  `id`, `route`, campos `ai_visible`, `ai_actions`. Invariante: tela com
  `ai_actions: []` nunca produz snapshot [F-12].
- **SnapshotDeContexto** (objeto de valor): só nasce da sanitização no servidor; não há
  construtor a partir de dict livre. Invariante: schema fechado, teto declarado.
- **SessãoDeConversa** (agregado do wire): eventos `{seq, kind, payload}`
  somente-acréscimo, `seq` atribuído no servidor antes da emissão. Invariante: `seq`
  monotônico sem lacuna por sessão.
- **Eventos de domínio**: `PropostaCriada`, `PropostaDecidida`, `PropostaExpirada`,
  `AçãoExecutada`, `AçãoRecusada` — alimentam traço, replay e o sinal
  `ghd.action_result`.

## Requisitos funcionais

### F7.3.1 — Manifesto embedded

RF-01: O SISTEMA DEVE publicar manifesto com `app_id: toc`, `mode: embedded`,
`mount: iframe`, telas e ações namespaced `toc.*`, `capabilities_required`
(`toc:read`, `toc:write`), `endpoints.introspect` e `theme.fallback: true`, validável
sem erros contra o schema normativo do Anexo B ([`contracts/manifesto.json`](contracts/manifesto.json)).
[F-18] 🟡

RF-02: Toda tela e toda ação do manifesto DEVE usar o prefixo `toc` igual ao `app_id`
(forma `<ns>.<id>` do §B.5.2), e toda rota de tela DEVE viver sob `/toc/`, em forma
canônica (caixa baixa, sem barra final) — o prefixo próprio é a defesa contra colisão
de rota que o guia recomenda [F-27]. 🟡

RF-03: QUANDO o catálogo ou as telas mudarem, O SISTEMA DEVE tratar o manifesto como
mudança de admissão: nova versão, re-submissão e re-aprovação — nunca deriva silenciosa
entre o manifesto publicado e o catálogo servido. 🟡

RF-04: As ações do manifesto e as do catálogo servido DEVEM vir da **mesma fonte**
(`ActionSpec` único); um teste de paridade falha se divergirem. [F-02] 🟡

### F7.3.2 — Catálogo derivado de permissão

RF-05: O catálogo DEVE ser derivado das capabilities reais do Principal na composição:
sem `toc:write`, nenhuma ação `risk: confirm` entra no inventário que o modelo vê
(APH-4.3; ausência é melhor fronteira que recusa, §B.7.3). [F-02][F-13] 🟡

RF-06: Cada ação DEVE declarar `action_id`, título, `input_schema` (JSON Schema) e
classe de risco (APH-4.2); ação sem qualquer um dos quatro não entra no catálogo.
[F-02] 🟡

RF-07: O `input_schema` DEVE ser uma fonte com três projeções: valida os `args` da
proposta no servidor, vira a *tool* que a fundação entrega ao modelo e entra no
manifesto (APH-4.4; §A.5). [F-02][F-11] 🟡

RF-08: O SISTEMA DEVE servir `GET /aph/catalog` já filtrado por permissão (§A.2), e o
catálogo DEVE ser a única superfície executável: nenhum endpoint de mutação fora dele é
alcançável pelo modelo ou pela borda federada (APH-4.1). [F-02][F-08] 🟡

RF-09: QUANDO uma proposta citar `action_id` fora do catálogo composto para aquele
Principal, O SISTEMA DEVE recusá-la com traço, sem executar nada. [F-02][F-03] 🟡

### F7.4.1 — FSM de proposta

RF-10: Nenhuma ação DEVE executar no momento em que o modelo a menciona: toda ação
nasce proposta com `proposal_id` próprio (APH-5.1). [F-01] 🟡

RF-11: A FSM DEVE ser
`proposed → awaiting_approval → confirmed → executing → executed | failed | cancelled |
denied | expired`, validada em código; transição fora da tabela DEVE falhar com
`INVALID_TRANSITION` (HTTP 409). O estado `stale` da FSM de referência é 🧪 na norma e
**não** é adotado: contexto divergente encerra a proposta em `cancelled` com código
`PROPOSAL_CONTEXT_STALE`, o mesmo desenho do laboratório A (§A.8). [F-01][F-09] 🟡

RF-12: A confirmação DEVE ser proporcional ao risco, decidida no servidor e antes da
conversa: `read` executa direto; `confirm` para no gate humano (APH-5.2). O modelo
nunca decide a classe. [F-23] 🟡

RF-13: Toda proposta `awaiting_approval` DEVE ter TTL; vencido, a proposta transiciona
a `expired` e a decisão tardia falha com `PROPOSAL_EXPIRED`. [F-09][F-23] 🟡

RF-14: A decisão DEVE entrar por `POST /aph/sessions/{id}/proposals/{proposal_id}` com
corpo `{approved}` (§A.6); `approved: false` encerra em `denied` **com traço**.
[F-08] 🟡

RF-15: QUANDO a confirmação trouxer `context_hash` e ele divergir do snapshot corrente,
O SISTEMA DEVE recusar sem executar, encerrando a proposta com código
`PROPOSAL_CONTEXT_STALE` (APH-5.4 — a substância é comparar e recusar). [F-23][F-09] 🟡

RF-16: Confirmar duas vezes a mesma proposta NÃO DEVE re-executar: a primeira decisão
produz o efeito, as seguintes recebem o mesmo resultado (deduplicação — APH-5.3
adotado por desenho). [F-23] 🟡

### F7.4.2 — Autorização por capability nos casos de uso

RF-17: Toda mutação DEVE verificar a capability exigida **no caso de uso**, não na
camada de rota (§B.7.2 — a armadilha do `Depends(...)` está registrada na norma com
três equipes caindo nela); a recusa é fail-closed e deixa traço. [F-13] 🟡

RF-18: Capability DEVE ter a forma `recurso:verbo` sem curinga (`toc:read`,
`toc:write`); `toc:*` e afins DEVEM ser rejeitados na composição (§B.7.1). [F-13] 🟡

RF-19: O SISTEMA NÃO DEVE pressupor a atenuação de autoridade do hospedeiro
(APH-9.4b é 🧪 sem laboratório, e a norma mediu o caso em que as capabilities recebidas
**excedem** quem abriu o embarque [F-14]): as capabilities da introspecção são teto,
nunca dispensa — a verificação local do RF-17 acontece sempre, e decisões sensíveis do
domínio (ex.: exclusão) PODEM exigir política própria adicional. 🟡

RF-20: Política de autorização que devolve verdadeiro para tudo é não-conformidade
declarada (APH-7.2): a suíte DEVE conter a sabotagem que troca a política por
`lambda: True` e vê os testes de recusa falharem. [F-19] 🟡

### F7.4.3 — Traço de 100%

RF-21: 100% das ações — executadas, negadas, expiradas, recusadas por política ou por
contexto divergente — DEVEM deixar traço auditável no servidor e visível na conversa
(`action_result` no stream); ação sem traço DEVE ser rejeitada antes do efeito
(APH-5.5). [F-03] 🟡

RF-22: O traço DEVE ser escopado por tenant e usuário (APH-7.4) e correlacionado ao
traço OTel do ciclo 003 pelo `trace_id`. [F-19] 🟡

RF-23: O `action_result` DEVE ser honesto: `status` do vocabulário fechado do §A.3
(`executed | failed | denied | cancelled | expired`), nunca um estado inventado.
[F-10] 🟡

### F7.4.4 — Proposta em lote

RF-24: Ação que atinge N alvos DEVE ser **uma** proposta com N alvos nos `args` (no
formato do próprio `input_schema`), nunca N propostas (APH-5.9; decisão de origem:
ADR 0009 da irmã [F-05]). [F-04] 🟡

RF-25: A confirmação de lote DEVE mostrar a contagem de alvos **antes** da decisão
(APH-5.9(c)). [F-04] 🟡

RF-26: O traço e o `action_result` de lote DEVEM discriminar o desfecho por alvo
(`outcomes[]: {target, status}` com `status` em
`executed | failed | denied | skipped` — APH-5.9(b), §A.3). [F-04][F-10] 🟡

RF-27: QUANDO houver `outcomes`, o `status` terminal NÃO DEVE afirmar mais sucesso do
que eles mostram: com qualquer alvo fora de `executed`, o estado terminal não é
`executed` (APH-5.9(e) — o schema do fio v0.5 rejeita a combinação). [F-10] 🟡

RF-28: Cada ação desenhada para lote DEVE declarar `batch_atomicity`
(`all_or_nothing` | `per_item`) **no catálogo servido** (§A.5); ação sem o campo não
foi desenhada para lote e proposta em lote sobre ela DEVE ser recusada — a declaração
no **manifesto** está bloqueada pelo schema normativo (L-02). [F-11] 🟡

RF-29: A classe de risco de um lote DEVE ser ao menos a mais alta entre as dos seus
itens (APH-5.9(d)). [F-04] 🟡

### F7.4.5 — Borda de execução federada

RF-30: O SISTEMA DEVE expor `POST /aph/actions/{action_id}` na convenção do ADR 0023
do hospedeiro: corpo `{"params": …}`, resposta 2xx com `{"result": "<string>"}` —
resposta fora disso o hospedeiro degrada com o prefixo `erro:`. [F-15] 🟡

RF-31: Os `params` recebidos DEVEM ser tratados como não-confiáveis e validados contra
o `input_schema` da ação **no nosso servidor** — o hospedeiro declara que não valida
[F-16]; parâmetro inválido é recusa com traço, nunca execução parcial. 🟡

RF-32: A borda DEVE recusar chamada não autenticada, fail-closed com traço — mesmo
sabendo que a fatia atual do hospedeiro chama **sem credencial** (limite de alcance
L-03): enquanto não houver credencial verificável, só ações `risk: read` respondem
nesta borda, e toda ação mutadora é recusada. [F-16] 🟡

RF-33: A borda DEVE responder dentro do orçamento de 5 segundos do hospedeiro (acima
disso ele degrada [F-15]); o tempo de resposta é medido por span OTel, e a resposta de
falha nunca vaza detalhe interno (só código categorizado). 🟡

### F7.5.1 — Registro de telas

RF-34: O SISTEMA DEVE manter um registro de telas versionado, fonte de verdade
compartilhada entre frontend e backend, com identidade, rota, campos tipados
(`ai_visible`) e ações (`ai_actions`) por tela — a IA nunca infere a interface: nada
de raspagem de DOM nem captura de tela (APH-3.1). [F-06] 🟡

RF-35: Tela com `ai_actions: []` é sensível: NÃO DEVE entrar em snapshot algum
(§B.5.3) — a tela `toc.configuracao` do manifesto é o caso concreto. [F-12] 🟡

RF-36: As telas declaradas no manifesto DEVEM ser subconjunto do registro de telas, com
paridade testada (mesma fonte que gera os dois). 🟡

### F7.5.2 — Snapshot sanitizado no servidor

RF-37: Cada mensagem DEVE carregar snapshot estruturado com identidade da tela, rota,
campos tipados e entidade selecionada (APH-3.2), no formato do §A.4. [F-06][F-25] 🟡

RF-38: A sanitização DEVE acontecer **no servidor**, antes do modelo, em três camadas:
denylist de segredos, campos sensíveis do registro, e allowlist — campo que não está
no registro não passa (APH-3.3). [F-06] 🟡

RF-39: O schema do snapshot DEVE ser fechado (`additionalProperties: false` em todos os
níveis fechados) com teto declarado **abaixo de 32 KB**; campo desconhecido ou teto
estourado DEVE ser rejeitado na borda com `INVALID_CONTEXT`, nunca repassado ao modelo
(APH-3.5, §A.4). [F-06][F-25] 🟡

RF-40: O snapshot DEVE entrar no contexto como camada rotulada de sistema, distinta do
conteúdo do usuário; tudo que vem da tela é dado, nunca instrução (APH-7.1, APH-7.3).
[F-19] 🟡

### F7.6 — Wire APH Nível 1

RF-41: A resposta da fronteira conversacional DEVE chegar por SSE sobre POST
(`Content-Type: text/event-stream`), cada frame um JSON completo em UTF-8, terminado
por `done` ou `error` (APH-1.1, §A.1). [F-21][F-07] 🟡

RF-42: Cada evento DEVE carregar `{seq, kind, payload}` com `seq` inteiro ≥ 1,
monotônico por sessão, atribuído **no servidor antes da emissão** (APH-1.2). [F-07] 🟡

RF-43: O vocabulário de eventos DEVE ser fechado e conter as seis famílias mínimas —
conteúdo, raciocínio, ação (`action_proposal`/`action_result`), comando de UI, erro e
terminador (APH-2.1); a regra de evolução é a do APH-2.2: o consumidor ignora `kind`
desconhecido, o produtor documenta antes de emitir — escrita no contrato, não só
praticada. [F-22] 🟡

RF-44: A sessão DEVE oferecer replay por `GET …/events?after=N` sem perda nem
duplicação, e o cliente DEVE deduplicar por `seq` (APH-1.3): `?after=0` devolve tudo,
`?after=<último>` devolve vazio. [F-21][F-08] 🟡

RF-45: Propostas `awaiting_approval` DEVEM sobreviver à reconexão: o replay reconstrói
os gates pendentes (APH-5.6, adotado por desenho — perder aprovação pendente é perda
de governança). [F-24] 🟡

RF-46: O cancelamento DEVE ser cooperativo: `DELETE …/stream`, verificação no laço de
emissão, término com `error` de código `STREAM_CANCELLED` — nunca em silêncio
(APH-1.4). [F-21][F-08] 🟡

RF-47: Erro é parte do protocolo: envelope `{code, message, details?}` com códigos
estáveis em `MAIUSCULAS_COM_SUBLINHADO`; o registro mínimo do §A.7 (7 códigos: 5 ✅ e
2 🧪, contagem executada em [F-09]) DEVE ser adotado, e códigos próprios
(`ADMISSAO_*`, `FUNDACAO_INDISPONIVEL` do ciclo 003) DEVEM ser documentados no mesmo
contrato. [F-09] 🟡

RF-48: Comando de UI DEVE ser declarativo, de vocabulário fechado, com executor no
host da própria aplicação; o executor DEVE consultar a classe de risco e recusar
fail-closed comando mutador — verbo mutador nasce proposta (APH-6.1, 6.2, 6.6; o
contraexemplo `session.logout` do laboratório está registrado na norma). [F-28] 🟡

## Requisitos de interface

RI-01: Existe **uma** superfície de confirmação (`proposta-de-acao`) para toda ação
`confirm`, venha de humano ou de IA: resumo em português, alterações item a item,
contagem de afetados, confirmar e recusar com igual proeminência (herda o ADR 0009 da
irmã [F-05]). 🟡

RI-02: A origem da proposta (`humano` | `ia`) é exibida como dado e NUNCA muda fluxo,
estado ou conteúdo mostrado — no instante em que virar `if`, as duas telas divergem e a
menos testada é a de mais risco [F-05]. 🟡

RI-03: Lote: os N alvos listados e contados **antes** da decisão; depois dela, o
desfecho por alvo visível (executado / falhou / pulado), com o motivo por item quando
houver. 🟡

RI-04: O traço é visível na conversa para todo desfecho — inclusive recusa e expiração;
recusa silenciosa é defeito. 🟡

RI-05: Estados da proposta têm apresentação própria: aguardando decisão (com TTL
visível), expirada, negada, contexto mudou (`PROPOSAL_CONTEXT_STALE` — com ação
"propor de novo sobre a tela atual"). 🟡

RI-06: O painel de assistência renderiza `kind` desconhecido ignorando-o sem quebrar
(APH-2.2 no cliente), e nunca renderiza interface serializada gerada pelo modelo —
dados estruturados em componentes próprios (APH-6.5). 🟡

RI-07: Cancelar é visível durante o streaming e o cancelamento se confirma na
conversa (o evento `error` `STREAM_CANCELLED` vira estado visível, não sumiço). 🟡

RI-08: Após reconexão, a conversa reconstruída não duplica mensagens e as aprovações
pendentes reaparecem no mesmo lugar. 🟡

RI-09: A superfície de confirmação é acessível: foco vai ao resumo ao abrir, decisão
operável por teclado, mudança de estado anunciada por `aria-live`. 🟡

RI-10: As superfícies novas seguem o tema do inquilino com fallback completo (mesma
régua do ciclo 003) e i18n com português como língua-fonte. 🟡

RI-11: A jornada viva do ciclo cobre quatro fluxos: proposta simples confirmada,
proposta recusada, lote com falha parcial e proposta expirada — capturas geradas por
script versionado do build real, avaliação heurística datada (P6). 🟡

RI-12: O snapshot enviado é inspecionável pela pessoa ("o que a IA vê desta tela") — a
transparência é a contraparte de tela-é-dado. 🟡

## Requisitos não funcionais

RNF-01: Autorização sempre fora do modelo: nenhuma decisão de permissão usa texto de
LLM como entrada (APH-7.2); a política é função pura testável. [F-19] 🟡

RNF-02: A sanitização tem teste de golden: o campo `senha_vazada` do contraexemplo
normativo nunca alcança prompt, log ou traço [F-25]. 🟡

RNF-03: Os eventos emitidos validam contra os schemas normativos do `protocolos`
(`evento.schema.json`, `erro.schema.json`, `acao-catalogo.schema.json`,
`confirmacao.schema.json`, `snapshot.schema.json`) em teste de CI — golden como gate,
não como intenção. 🟡

RNF-04: Fail-closed em toda fronteira nova: exceção não tratada na FSM, na borda
federada ou na sanitização resulta em recusa com traço, nunca em execução. 🟡

RNF-05: Nenhum segredo no cliente (P7): a borda `/aph/actions` e o wire vivem no
servidor; o frontend nunca vê credencial nem chave. 🟡

RNF-06: Toda proposta tem span OTel correlacionado (criação → decisão → execução →
traço) sob o `trace_id` da sessão — sem traço técnico, não está pronta (P5). 🟡

RNF-07: Base 100% sintética em fixtures, testes e capturas (ADR 0006) — o portão é o
grep de personas proibidas do ciclo 003, reexecutado aqui. 🟡

RNF-08: A borda `/aph/actions` tem limite de taxa por origem/credencial — é a única
rota chamada de fora do nosso frontend, e nasce com proteção. 🟡

RNF-09: Desempenho do wire: primeiro evento do stream em ≤ 2 s sem contar o tempo do
provedor da fundação (medido por span próprio); replay de 500 eventos em ≤ 1 s — alvos
propostos, calibrados na primeira medição real (L-07). 🟡

RNF-10: Logs estruturados de toda a fronteira carregam `proposal_id`, `tenant_id` e
`trace_id`; o grant e o conteúdo de snapshot nunca aparecem em log (regra herdada do
003, RNF-01 de lá). 🟡

## Regras de negócio

RN-01: A taxonomia de risco do catálogo `toc.*` é a mínima comprovada da norma —
`read` e `confirm` (§B.5.3): `read` nunca muta; toda mutação é `confirm`. Classe nova
exige ADR. [F-12] 🟡

RN-02: A linha entre executar direto e propor é a **reversibilidade**, em política do
servidor por tipo de ação (APH-6.3) — a tabela de tipos nasce no ciclo 004 e o
catálogo a reutiliza; exclusão definitiva não entra no catálogo da IA. 🟡

RN-03: Sugestão da IA é rascunho até o gate: nenhuma UDE, causa ou aresta sugerida
vira nó do diagrama sem confirmação humana — autoria é da Facilitadora, assistência é
assistência (consome os critérios formais de UDE do M2 como regra de domínio pura). 🟡

RN-04: Lote herda o risco mais alto dos seus itens e nunca mistura ações de
`action_id` distintos numa proposta só. [F-04] 🟡

RN-05: Ação sem capability correspondente no Principal **não existe** para aquele
principal: não aparece em catálogo, manifesto composto ou tool — ausência, nunca
recusa visível (§B.7.3). [F-13] 🟡

## Integrações

INT-01: **Manifesto → admissão da fundação** — [`contracts/manifesto.json`](contracts/manifesto.json)
submetido à rota real de administração (o caminho e os bloqueios são os do ciclo 003,
INT-03 de lá); `url`/`origin` reais entram após o gate do endereço (DÚVIDA 1 do 003).

INT-02: **Superfície APH da aplicação** — `GET /aph/catalog` (filtrado por permissão),
`POST /aph/sessions`, `POST /aph/sessions/{id}/messages` (SSE),
`GET /aph/sessions/{id}/events?after=N`, `POST /aph/sessions/{id}/proposals/{pid}`,
`DELETE /aph/sessions/{id}/stream` — os caminhos de referência do §A.2 [F-08],
consumidos pela fundação.

INT-03: **Borda de execução federada** — `POST /aph/actions/{action_id}` chamada pelo
adapter remoto do hospedeiro (ADR 0023 [F-15]); contrato de resposta
`{"result": string}`; autenticação exigida do nosso lado (RF-32, L-03).

INT-04: **Canal `ghd.*` do ciclo 003** — após execução confirmada, a aplicação emite
`ghd.action_result` com payload `{}` como palpite de UI (nunca prova de execução —
§B.9.1); quem prova é o traço.

INT-05: **Assistência das ferramentas** — primeiro consumidor: E2.3 da ARA
([`../005-arvore-da-realidade-atual/spec.md`](../005-arvore-da-realidade-atual/spec.md));
M3 (E3.3) e M4 reutilizam o mesmo catálogo nos ciclos 007–008, acrescentando ações
`toc.*` novas por re-admissão de manifesto (RF-03).

INT-06: **O que este ciclo NÃO integra** (declarado para ninguém procurar): projeção
MCP headless (APH-9.3 — decisão futura, fora do alvo Nível 2), slot filling
estruturado (APH-6.4 — candidato ao ciclo 011), fila de aprovação por classe
(APH-5.7 — YAGNI enquanto só existe uma classe mutadora).

## Telas e fluxos

### 6.1 Proposta de ação — Job: decidir com informação completa · Campos: resumo em
português, origem (humano/IA), lista de alterações (N alvos com contagem), risco, TTL
restante · Ações: confirmar, recusar (igual proeminência), inspecionar snapshot
("o que a IA viu").

### 6.2 Desfecho e traço — Job: "o que aconteceu?" sempre tem resposta · Campos:
desfecho da proposta, desfecho por alvo (lote), quem decidiu, quando · Ações: nenhuma
mutadora; link para o nó criado/alterado quando executada.

### 6.3 Painel de assistência (na tela da ARA) — Job: conversar sobre a árvore com a
tela como dado · Campos: stream tipado (conteúdo, raciocínio quando houver, propostas,
resultados, erros) · Ações: enviar mensagem (com snapshot), cancelar stream, decidir
propostas pendentes.

### 6.4 Fluxo da proposta em lote (o crítico)
1. Facilitadora pede: "registre estes oito efeitos como UDEs".
2. Fundação propõe `toc.criar_nos` com 8 alvos → `action_proposal` (uma proposta).
3. Tela 6.1 mostra os 8, a contagem e o risco; Facilitadora confirma **uma vez**.
4. Servidor valida capability no caso de uso, executa item a item
   (`batch_atomicity: per_item`), item 7 falha na invariante de domínio.
5. `action_result`: `status: failed`(parcial — nunca `executed`), `outcomes` com 7
   `executed` e 1 `failed` com motivo; traço por alvo persistido.
6. Tela 6.2 mostra o desfecho por alvo; `ghd.action_result` avisa o hospedeiro
   (palpite de UI); árvore mostra os 7 nós novos.

## Entregáveis

- Catálogo `toc.*` (fonte única `ActionSpec` → manifesto, catálogo servido, tools) +
  composição por capability, com testes.
- FSM de proposta + TTL + deduplicação de confirmação + lote com `outcomes`, com
  testes de transição completos (tabela inteira + transições inválidas).
- Traço de execução persistido e servido; `action_result` no stream; emissão de
  `ghd.action_result` no canal do 003.
- Registro de telas versionado + snapshot com sanitização em três camadas, schema
  fechado e teto — com golden `senha_vazada`.
- Wire Nível 1: sessões, SSE, `seq`, replay, cancelamento, códigos — validado contra
  os schemas do `protocolos` no CI.
- Borda `POST /aph/actions/{action_id}` com autenticação, validação de `params` e
  limite de taxa.
- [`contracts/manifesto.json`](contracts/manifesto.json) validado (saída na DoD) e
  submetido; superfícies de UI 6.1–6.3; jornada viva; entrada no `CHANGELOG.md`;
  atualização da matriz [`../../docs/integracao/aderencia-aph.md`](../../docs/integracao/aderencia-aph.md)
  no mesmo pull request (é o artefato vivo da fronteira).

## Critérios de aceite (DoD)

| # | Critério | Verificação executável |
|---|---|---|
| 1 | FSM completa e fechada | `pytest tests/propostas -q` — toda transição da tabela + toda transição inválida → `INVALID_TRANSITION` (409) |
| 2 | Nada executa na menção | `pytest tests/propostas -q -k mencao` — `action_proposal` emitido, domínio intocado até a decisão |
| 3 | Catálogo derivado de permissão | `pytest tests/catalogo -q -k capability` — contagem de ações com/sem `toc:write` impressa na saída (portão do roadmap) |
| 4 | Capability no caso de uso, não na rota | `pytest tests/autorizacao -q` — caso de uso chamado direto (sem HTTP) recusa sem `toc:write`; sabotagem `lambda: True` derruba os testes de recusa |
| 5 | Traço 100% | `pytest tests/traco -q` — execução, negação, expiração e recusa por contexto, todas com traço; sabotagem sem traço → execução rejeitada |
| 6 | Lote honesto | `pytest tests/lote -q` — 1 proposta/8 alvos; contagem antes; `outcomes` por alvo; com 1 falha o `status` ≠ `executed` |
| 7 | Snapshot sanitizado no servidor | `pytest tests/snapshot -q` — campo fora do registro → `INVALID_CONTEXT`; `senha_vazada` ausente de todo prompt; teto < 32 KB verificado |
| 8 | Wire golden contra a norma | teste de CI valida eventos emitidos contra `protocolos/padrao/schemas/*.schema.json` — saída com a contagem de exemplos validados |
| 9 | Replay íntegro | `pytest tests/wire -q -k replay` — `?after=0` idêntico ao stream; `?after=<último>` vazio; dedup por `seq` |
| 10 | Cancelamento cooperativo | `pytest tests/wire -q -k cancel` — `DELETE .../stream` → `error` `STREAM_CANCELLED` |
| 11 | Manifesto valida contra o schema normativo | script de validação (jsonschema draft 2020-12) com saída colada; sabotagens (sem `theme.fallback`, capability curinga) rejeitadas |
| 12 | Borda federada fechada | `pytest tests/borda -q` — sem credencial → recusa com traço; `params` inválidos → recusa; resposta < 5 s medida |
| 13 | Jornada viva presente | `ls docs/jornadas/` — jornada dos 4 fluxos (RI-11) com capturas geradas por script |
| 14 | Conformidade e caminhos | `scripts/check-conformance.sh 006` + `scripts/check-caminhos.sh` + `scripts/check-links.sh` — código 0 e quanto examinaram |

## Fontes

F-01: `/home/user/protocolos/padrao/padrao-aph.md:102` — APH-5.1: toda ação nasce
proposta; FSM de referência
`proposed → awaiting_approval → confirmed → executing → executed | failed | cancelled |
denied | expired | stale`; transições fora da tabela DEVEM falhar; `stale` é a única
parte 🧪 — uso: RF-10, RF-11 🟢

F-02: `/home/user/protocolos/padrao/padrao-aph.md:95-98` — §4.4: catálogo é a única
superfície executável (APH-4.1), quatro declarações por ação (APH-4.2), derivado das
permissões reais (APH-4.3), uma fonte/duas projeções (APH-4.4 🧪) — uso: RF-04..RF-09 🟢

F-03: `/home/user/protocolos/padrao/padrao-aph.md:107` — APH-5.5: traço em 100% das
ações, inclusive recusadas; "ação sem traço é ação não governada, e DEVE ser
rejeitada" — uso: RF-09, RF-21 🟢

F-04: `/home/user/protocolos/padrao/padrao-aph.md:109-112` — APH-5.9: proposta em lote
é uma proposta com N alvos; as cinco obrigações (a)–(e); procedência cita
"docs/adr/0009-uma-so-tela-de-confirmacao.md da primeira aplicação federada" — uso:
RF-24..RF-29, RN-04 🟢

F-05: `/home/user/gestaodeprioridades/docs/adr/0009-uma-so-tela-de-confirmacao.md:27-36`
— uma única superfície de confirmação; origem é dado, nunca desvio de fluxo; "Lote é
uma proposta, não N propostas" — uso: RI-01, RI-02, RF-24 🟢

F-06: `/home/user/protocolos/padrao/padrao-aph.md:87-91` — §4.3: registro de telas
(APH-3.1), snapshot estruturado por mensagem (APH-3.2), sanitização no servidor em
três conjuntos (APH-3.3), teto < 32 KB e schema fechado (APH-3.5) — uso: RF-34,
RF-37..RF-39 🟢

F-07: `/home/user/protocolos/padrao/anexo-a-wire-format.md:46` — envelope
`{seq, kind, payload}`, `seq` inteiro ≥ 1 monotônico por sessão, `kind` de vocabulário
fechado — uso: RF-41, RF-42 🟢

F-08: `/home/user/protocolos/padrao/anexo-a-wire-format.md:33-41` — §A.2: superfície
de referência HTTP (sessões, mensagens SSE, replay `?after=N`, decisão de proposta,
cancelamento `DELETE`, catálogo já filtrado) — uso: RF-08, RF-14, RF-44, RF-46,
INT-02 🟢

F-09: `/home/user/protocolos/padrao/anexo-a-wire-format.md:92-102` — §A.7: erro
`{code, message, details?}` em `MAIUSCULAS_COM_SUBLINHADO`; registro mínimo com
**7 códigos** (5 ✅ + 2 🧪) — contagem executada:
`grep -nE '^\| (🧪 )?\`[A-Z_]+\`' anexo-a-wire-format.md` devolve as linhas 96–102 da
tabela (a 8ª ocorrência, linha 116, é a tabela de mapeamento do §A.8) — uso: RF-11,
RF-13, RF-47 🟢

F-10: `/home/user/protocolos/padrao/anexo-a-wire-format.md:53` — `action_result`:
vocabulário de `status`; `outcomes` por alvo (`executed | failed | denied | skipped`);
"O `status` não pode afirmar mais sucesso do que os `outcomes` mostram" — uso: RF-23,
RF-26, RF-27 🟢

F-11: `/home/user/protocolos/padrao/anexo-a-wire-format.md:84` — §A.5: ação de
catálogo com `batch_atomicity` (`all_or_nothing` | `per_item`); ausente = "não
desenhada para lote", nunca `per_item` por omissão; `input_schema` com três projeções
— uso: RF-07, RF-28 🟢

F-12: `/home/user/protocolos/padrao/anexo-b-federacao.md:117` — §B.5.3: mesma
`ActionSpec` do §4.4, `risk` string aberta com mínimo comprovado `read | confirm`;
"Tela com `ai_actions: []` marca item sensível: NÃO DEVE entrar no snapshot" — uso:
RF-35, RN-01 🟢

F-13: `/home/user/protocolos/padrao/anexo-b-federacao.md:149-155` — §B.7: capability
`recurso:verbo` sem curinga (B.7.1); derivação por política pura "verificada nos
**casos de uso**, não na camada de rota" com a armadilha do `Depends(...)` que pegou
três equipes (B.7.2); ausência é melhor fronteira que recusa (B.7.3) — uso: RF-05,
RF-17, RF-18, RN-05 🟢

F-14: `/home/user/protocolos/padrao/anexo-b-federacao.md:143-145` — §B.6.7: nenhum
laboratório intersecta com o usuário; caso medido: "uma usuária sem nenhuma capability
`toc:*` abre um embarque e a aplicação recebe `["toc:read","toc:write"]`" — uso:
RF-19, L-04 🟢

F-15: `/home/user/ghdaru/docs/adr/0023-acoes-federadas-por-adapter-remoto.md:32-39` —
adapter remoto: `POST {origin}/aph/actions/{action_id}` com `{"params": …}`; resposta
2xx + `{"result": <string>}` truncado em 2 000; timeout 5 s; degradação com prefixo
`erro:` obrigatório — uso: RF-30, RF-33, INT-03 🟢

F-16: `/home/user/ghdaru/docs/adr/0023-acoes-federadas-por-adapter-remoto.md:49-52` e
`:63-65` — "**Sem credencial nesta fatia**: a chamada à app federada vai sem token";
autenticação da borda é pré-requisito do F7; "O host não valida os args do LLM contra
o `input_schema` (…) A app federada DEVE tratar `params` como não-confiável" — uso:
RF-31, RF-32, L-03 🟢

F-17: `/home/user/ghdaru/docs/integration/guia-desenvolvedor-app-federada.md:50-56` —
§3.1: "o fio que sua app fala" — SSE sobre POST, `seq` monotônico no servidor, replay
`?after=N` + dedup, cancelamento cooperativo, envelope de erro — uso: E7.6 inteiro 🟢

F-18: `/home/user/protocolos/padrao/schemas/federacao-manifesto.schema.json:38-45,111-119,131-156,172-213`
— `mode` enum com `embedded`; `theme.fallback` `const true` obrigatório; `screens[].id`
na forma `<ns>.<id>` com `ai_actions` enum de 4 valores (`READ`, `FILL_FIELDS`,
`SUBMIT`, `NAVIGATE` — contado por grep = 4); `actions[]` com `risk` e `input_schema`
obrigatórios — uso: RF-01, RF-02, contracts/ 🟢

F-19: `/home/user/protocolos/padrao/padrao-aph.md:126-129` — §4.7: camadas de
confiança (APH-7.1), autorização sempre fora do LLM com o contraexemplo da política
sempre-verdadeira (APH-7.2), tela é dado (APH-7.3), auditoria com escopo (APH-7.4) —
uso: RF-20, RF-22, RF-40, RNF-01 🟢

F-20: `/home/user/protocolos/padrao/padrao-aph.md:53` e `:64` — tabela de níveis: o
Nível 2 (Operador) exige Nível 1 + §4.2 completo, §4.4–§4.8; "uma aplicação que
'conversa integralmente' (…) é Nível 2" — uso: escopo da spec 🟢

F-21: `/home/user/protocolos/padrao/padrao-aph.md:70-74` — §4.1: APH-1.1 (SSE sobre
POST), 1.2 (`seq` no servidor), 1.3 (replay sem perda/duplicação), 1.4 (cancelamento
cooperativo com código estável), 1.5 (erro como protocolo) — uso: RF-41..RF-47 🟢

F-22: `/home/user/protocolos/padrao/padrao-aph.md:78-79` — APH-2.1 (seis famílias
mínimas do vocabulário fechado) e APH-2.2 (consumidor ignora, produtor documenta
antes) — uso: RF-43, RI-06 🟢

F-23: `/home/user/protocolos/padrao/padrao-aph.md:103-105` — APH-5.2 (confirmação
proporcional ao risco, fora do modelo e antes da conversa), APH-5.3 🧪
(`idempotency_key` com deduplicação real), APH-5.4 (comparar `context_hash` na
confirmação; recusa sem execução com código estável) — uso: RF-12, RF-15, RF-16 🟢

F-24: `/home/user/protocolos/padrao/padrao-aph.md:108` — APH-5.6 🧪: propostas
pendentes sobrevivem à reconexão; "reconectar e perder uma aprovação pendente é perda
de governança" — uso: RF-45, RI-08 🟢

F-25: `/home/user/protocolos/padrao/anexo-a-wire-format.md:80` — §A.4: snapshot com
`additionalProperties: false` em todos os níveis fechados; "o contraexemplo
`senha_vazada` do gate prova a rejeição"; sanitização e composição no servidor — uso:
RF-37, RF-39, RNF-02 🟢

F-26: `/home/user/protocolos/padrao/padrao-aph.md:17` e `:200` — a suíte de
conformidade executável cobre o Nível 1 e o lado hospedeiro da federação; "o Nível 2
segue sem suíte" (§8: trabalho futuro) — uso: L-01 🟢

F-27: `/home/user/ghdaru/docs/integration/guia-desenvolvedor-app-federada.md:104-107`
— rotas de módulos do tenant não entram na recusa de admissão; "Escolher um prefixo
próprio (`/toc/…`) é a defesa prática" — uso: RF-02 🟢

F-28: `/home/user/protocolos/padrao/padrao-aph.md:117-122` — §4.6: comandos de UI
declarativos de vocabulário fechado (APH-6.1), executor no host (APH-6.2), linha da
reversibilidade (APH-6.3), executor recusa mutador fail-closed com o contraexemplo
`session.logout` vivo no laboratório (APH-6.6 ⚗️) — uso: RF-48, RN-02 🟢

## Lacunas e assunções

L-01: **O Nível 2 não tem suíte de conformidade executável** ([F-26]) — assunção: a
prova é autodeclaração com evidência por path + os golden dos schemas no nosso CI
(RNF-03); a autodeclaração formal é entrega do ciclo 012 — risco **médio** (sem
medição externa, o erro de auto-avaliação é nosso).

L-02: **O schema normativo do manifesto não admite `batch_atomicity`** — verificado:
`grep -c batch_atomicity federacao-manifesto.schema.json` → `0`, e a sabotagem que o
acrescenta a uma ação do manifesto é rejeitada (`1 erro`, saída no qa-report do 001);
o campo existe só no schema do catálogo do fio (§A.5 [F-11]) — assunção: declaramos
atomicidade no **catálogo servido** e não no manifesto; se o gap doer na admissão,
vira `mensagens/NNN-para-protocolos-*` (P1: relate e pare) — risco **baixo**.

L-03: **A fatia de ações federadas do hospedeiro chama sem credencial** ([F-16]) —
assunção: nossa borda nasce exigindo autenticação (RF-32); enquanto o F7 do hospedeiro
não emitir credencial de serviço, a borda federada só serve `risk: read` e o alcance
fica limitado à execução disparada do harness — a FSM e o catálogo não dependem disso
(é o limite aceito no roadmap, ciclo 006) — risco **médio**.

L-04: **APH-9.4b sem laboratório: as capabilities recebidas podem exceder o usuário**
([F-14]) — assunção: não pressupomos atenuação do hospedeiro; RF-17/RF-19 re-verificam
localmente em todo caso de uso — risco **médio** (a exposição residual é do lado do
hospedeiro, mas o traço é nosso).

L-05: **`usage` no `done` depende da porta da fundação** — sem provedor próprio
(ADR 0007), não medimos tokens; o campo é opcional no fio — assunção: emitimos `done`
sem `usage` até a fundação repassar o valor — risco **baixo**.

L-06: **`endpoints.actions` não existe no schema do manifesto** (o próprio ADR 0023 do
hospedeiro registra o gap e propõe formalização ao `protocolos` — [F-15], item 5 de
lá) — assunção: seguimos a convenção `POST {origin}/aph/actions/{action_id}` do ADR
até a norma formalizar — risco **baixo**.

L-07: **Não há baseline de desempenho do wire** — assunção: os alvos do RNF-09 são
propostos; a primeira medição real os calibra no gate — risco **baixo**.

## Clarify

- [DÚVIDA] 1 — O catálogo `toc.*` v1 (8 ações do
  [`contracts/manifesto.json`](contracts/manifesto.json)) está aprovado ação a ação —
  nomes, riscos, capabilities? O roadmap declara este o portão humano do ciclo; é
  contrato que circula no manifesto.
- [DÚVIDA] 2 — TTL da proposta `awaiting_approval`: proposta de 10 minutos (tempo de
  ler um lote com calma sem deixar gate pendurado). Aprovar ou calibrar.
- [DÚVIDA] 3 — `batch_atomicity` de `toc.criar_nos`/`toc.criar_arestas`/
  `toc.excluir_nos`: proposta `per_item` (falha no item 7 não desfaz os 6 — o desfecho
  por alvo informa). Alternativa `all_or_nothing` custa transação maior. Decidir por
  ação.
- [DÚVIDA] 4 — A confirmação exige `idempotency_key` (além da deduplicação por estado
  da FSM do RF-16)? A norma o tem como 🧪 opcional; a proposta é aceitar o campo e
  ativar dedução real quando presente, sem exigi-lo do cliente.
- [DÚVIDA] 5 — Com L-03 vigente (borda sem credencial do hospedeiro), confirmar que
  limitar a borda federada a `risk: read` é aceitável para fechar o ciclo — ou se
  preferimos não expor a borda até o F7 do hospedeiro existir.
