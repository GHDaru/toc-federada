# Plan 008 — Árvores de Futuro e Implementação (ciclo planejado)

> Siglas: TOC — Teoria das Restrições · ARA — Árvore da Realidade Atual · UDE — Efeito
> Indesejável (*Undesirable Effect*) · NC — Nuvem de Conflito · ARF — Árvore da
> Realidade Futura · APR — Árvore de Pré-Requisitos · AT — Árvore de Transição · OI —
> Objetivo Intermediário · ED — Efeito Desejável · APH — Aplicação ↔ Harness · ADR —
> Architecture Decision Record (Registro de Decisão Arquitetural) · DoD — Definition of
> Done (Definição de Pronto) · DoR — Definition of Ready (Definição de Prontidão) · TDD
> — Test-Driven Development (desenvolvimento guiado por teste) · DDD — Domain-Driven
> Design (Design Orientado a Domínio) · IA — inteligência artificial · FSM — máquina de
> estados finitos · OTel — OpenTelemetry · CI — integração contínua · UI — interface de
> usuário · UX — experiência de usuário · YAGNI — You Aren't Gonna Need It · i18n —
> internacionalização · REST — Representational State Transfer · SDK — Software
> Development Kit (kit de desenvolvimento)

- **Spec**: `spec.md` (Rascunho — aprovação no gate humano que abre o ciclo) · **Raia**:
  plena · **Data**: 2026-09-03
- **Estado**: **planejado no ciclo 001, não executado.** Este plano é escrito antes de o
  ciclo abrir; o Constitution Check abaixo avalia o plano como está e será reconferido na
  abertura, com os ciclos 005 e 007 promovidos e a FSM do 006 no ar.

## Constitution Check (governance/principles.md)

| Princípio | Conformidade |
|---|---|
| I. Spec-driven | ✅ A spec 008 precede este plano, e ambos precedem qualquer código do módulo. O escopo é o do round 008 (E4.1–E4.4, com ramos negativos manuais); mudança de escopo volta à spec antes de virar código; os 5 `[DÚVIDA]` do Clarify vão ao Product Steward no gate de abertura. |
| II. Human-governed orchestration | ✅ O humano decide no gate: aprovação da spec, respostas do Clarify (re-semeadura, promoção multi-ARA, AT autônoma, aceite de ramo, objetivo derivado), corte de apetite. Agentes implementam por fronteira (ARF, APR, AT, encadeamento, UI); a revisão independente em contexto fresco confere o portão do roadmap: **a cadeia percorrida com referência de origem em cada elo** (`TAIL:review`). |
| III. Reversibility / risk gates | ✅ Promover, semear e derivar criam projetos — reversíveis por exclusão suave do M1; referência cruzada nunca é apagada por efeito colateral (RN-12: suspende e reativa); ramo negativo aceito registra autor e justificativa e reabre por ação explícita. Nenhuma ação externa ou irreversível nova nasce aqui. |
| IV. Test-first / verifiable DoD | ✅ TDD estrito com o teste de estreia do ciclo: a cadeia inteira com dados sintéticos (DoD 1) nasce **vermelha antes** de existir promoção, semeadura ou derivação. DoD com 16 linhas executáveis; `TAIL:mutation` sabota o sequenciamento, a verificação da ARF e a suspensão de referência e os vê recusar. |
| V. Context economy / boundary | ✅ Corte por fronteira dentro do ciclo: ARF, APR e AT são tipos de projeto independentes entre si (implementáveis em paralelo sobre o T-03); o encadeamento é um agregado próprio que os liga pelas bordas; a extração do pacote de suficiência é tarefa isolada com a suíte do 005 como rede. A UI vem depois do domínio de cada recorte. |
| VI. Living artifacts | ✅ A referência cruzada é consumida pela vista da cadeia, pela jornada e pelo traço (função forçante tripla); a tabela resumo da APR é dado exportado, não relatório solto; o corpus de verbalização repete a função forçante do M2 (heurística nova exige caso novo). O `ux-design.md` deste ciclo é consumido pelas tarefas de UI no mesmo pull request. |
| VII. Light governance / YAGNI | ✅ Descartados por YAGNI neste ciclo, cada um com porta de volta: tratamento assistido de ramo negativo (decisão do round; ADR novo quando a prática pedir), layout de grafo próprio para a vista da cadeia (L-05 — lista por elo basta), fila/worker para sequenciamento (síncrono no teto do RNF-04), gestor de projetos na AT (status leve, RF-30). |
| VIII. Intelligible communication | ✅ Bloco de siglas no topo dos quatro artefatos do ciclo; termos novos (espelho de UDE, ramo negativo, par obstáculo ↔ OI, elipse de simultaneidade, referência cruzada, vista da cadeia) definidos onde nascem, no modelo de domínio da spec. Conferência por amostragem do revisor da cauda. |

### Project Constitution Check (governance/constitution.md — ADR 0001)

| Princípio | Conformidade |
|---|---|
| P1. Fronteira de escrita | ✅ Só este repositório. As fontes da linhagem foram lidas com `arquivo:linha` e saída colada (F-01..F-08 da spec) — o botão cinza é fonte, não conserto; ninguém commita no `tocbuilderv3`. Lacuna externa achada durante o ciclo vira `mensagens/NNN-...`. |
| P2. Federação por contrato (APH) | ✅ As 4 ações do M4 executam pela FSM do 006 — uma só e do servidor —, cada sugestão nascendo `action_proposal` (RF-43), com contexto de domínio anexado (RF-44) e capability ausente escondendo mutadora (RF-45). Promover/semear/derivar são manipulação direta do titular sob o item 8 (INT-04): alvo nomeado pelo gesto, reversível, traço obrigatório — o alcance do P2 está declarado no texto do princípio, e este plano o cita em vez de reinterpretá-lo. |
| P3. Domínio puro (DDD + hexagonal) | ✅ As quatro funções centrais do ciclo — verificação da ARF, sequenciamento, verbalização avaliada, vista da cadeia — são puras, sem rede e sem modelo (RNF-01), com `import-linter` falhando o build na violação (RNF-02). A distinção suficiência × necessidade é tipo de domínio, não flag de UI (decisão 2 abaixo). |
| P4. TDD | ✅ Teste antes em todos os recortes: a cadeia sintética antes de qualquer promoção; grafos de fixture antes do sequenciamento; o corpus de verbalização antes das heurísticas; propriedade de integridade (RNF-09) antes do adaptador de persistência. Zero commit de domínio sem teste correspondente. |
| P5. Observabilidade de nascença | ✅ Toda mutação nova com traço correlacionado (RNF-03, DoD 13); promoções, semeaduras e derivações carregam o identificador da referência criada no traço — a linha auditável do encadeamento nasce junto com ele, não depois. |
| P6. Jornada viva com prova visual | ✅ Jornada da análise sintética completa da "Instituição Horizonte" — do UDE validado ao primeiro passo da AT concluído, atravessando as cinco ferramentas — com captura gerada por script do build real e avaliação heurística datada, no mesmo pull request (T-15). É a jornada que prova o valor central do produto (visão §2). |
| P7. Segredo nunca no cliente | ✅ Nenhum SDK, chave ou prompt no produto (DoD 11); prompts das 4 ações versionados no servidor (INT-11). O grep de CI herdado cobre os diretórios novos (RNF-08). |

**Sem violações.** A ressalva honesta: este é o primeiro ciclo em que ações de IA
**executam** (a FSM do 006 já existe) — o P2 deixa de ser prova negativa e passa a ser
prova positiva (DoD 10: mutação direta recusada, aceite cria com traço). O revisor da
cauda confere exatamente essa virada.

## Artefatos deste ciclo (declare todos os cinco — silêncio não é decisão)

| Artefato | Declaração | Por quê |
|---|---|---|
| `research.md` | `ART:research=no` | Não há incógnita a resolver por experimento: o método das três ferramentas vem da fonte técnica citada (spec F-09) e a analogia estrutural com M2/M3 está medida nos ciclos anteriores. A única aposta real — o apetite (L-03) — se resolve por corte declarado, não por pesquisa. |
| `data-model.md` | `ART:data-model=yes` | O módulo estende o modelo persistido do M1 com três tipos de projeto e seus anexos (papéis, EspelhoDeUde, RamoNegativo, ParObstaculoOI, ElipseDeSimultaneidade, FichaDePasso) **e cria um agregado novo** — ReferenciaCruzada — que atravessa projetos. O documento nasce na abertura do ciclo (T-02), como extensão declarada de [`../004-nucleo-de-diagramas/data-model.md`](../004-nucleo-de-diagramas/data-model.md); os testes de domínio prevalecem sobre o documento. |
| `contracts/` | `ART:contracts=yes` | Três contratos: a extensão REST (projetos `arf`/`apr`/`at`, promoções, semeaduras, derivações, vista da cadeia), a declaração das 4 ações `toc.*` no formato do catálogo do 006 (INT-05..INT-08 — aqui elas executam, não só declaram), e o esquema de exportação dos três tipos com referências (INT-10). Escritos na abertura (T-02/T-03). |
| `checklist.md` | `ART:checklist=no` | A DoD da spec já é executável (16 linhas com comando); lista adicional duplicaria função (Princípio VI). |
| `ux-design.md` | `ART:ux-design=yes` | **Diferença para M2/M3**: as telas do M4 não estavam no protótipo do ciclo 002 (que cobriu M1–M3). Canvas ARF/APR/AT, painel de ramos, tabela resumo e vista da cadeia precisam de papel semântico antes do componente. O artefato nasce na abertura (T-04), passa pelo gate de UX, e as tarefas de UI (T-11..T-14) o consomem. |

## Decisões de arquitetura do módulo

1. **Pacote de suficiência causal extraído, nunca copiado.** O exame de elo e o conector
   E saem do M2 para um pacote de domínio compartilhado que ARA e ARF importam (RF-03).
   A rede de proteção é a suíte do ciclo 005 continuando verde (entregável explícito).
   Plano B com dívida declarada: se a extração ameaçar o apetite, a ARF duplica
   temporariamente e um ADR registra a dívida com data (L-04).
2. **Suficiência e necessidade são tipos, não flags.** A aresta da ARF (suficiência,
   com exame) e a aresta da APR (dependência, sem exame) são conceitos de domínio
   distintos — o tipo de projeto determina qual existe, e nenhuma UI consegue misturá-los
   porque o domínio não oferece a operação (RN-05). É a materialização em código da
   distinção metodológica central da fonte técnica (spec F-09).
3. **ReferenciaCruzada é agregado próprio, fora dos projetos.** Um vínculo entre dois
   projetos não pertence a nenhum dos dois: vive em agregado próprio com tipo, origem e
   destino tipados, e os campos da NC (ReferenciaDeOrigem/Semeadura, spec 007) são
   preenchidos na mesma transação como projeção local de leitura — uma fonte, duas
   vistas, zero duplicação de verdade (RF-33).
4. **Promoção, semeadura e derivação são manipulação direta — as sugestões, não.** As
   três operações do titular aplicam na hora sob o item 8 (alvo nomeado, reversível,
   traço); as 4 ações `toc.suggest_*` nascem `action_proposal` sem exceção. A linha que
   separa os dois regimes está no autor do gesto, não no efeito — e é política declarada
   por tipo de ação, nunca origem alegada pelo cliente (constituição, item 8).
5. **Cadeia só avança sobre material auditado.** Promover exige UDE `Validado`; semear
   exige injeção `escolhida` (RN-13). As FSMs dos ciclos 005 e 007 são os portões de
   qualidade do encadeamento — o M4 os consome, não os reimplementa nem os afrouxa.
6. **Verbalização avaliada reusa a infraestrutura do M2 com léxico próprio.** Mesmo
   motor (função pura + léxico versionado por idioma + corpus como função forçante +
   `indeterminado` honesto), vocabulário novo (verbos de ação, marcadores de previsão,
   ausência genérica). Diferença deliberada: aqui o resultado é **aviso, não veto**
   (RN-08) — a APR registra primeiro e refina depois, porque a sessão de "sim, mas…" não
   pode travar na gramática.
7. **Vista da cadeia é leitura pura sobre referências.** Nenhuma tabela materializada,
   nenhum cache: 50 referências resolvem em memória no teto do RNF-05. YAGNI com porta
   de volta declarada se a medição da jornada discordar.
8. **AT sem entidade de projeto nova além da ficha.** O passo é nó do M1 com
   FichaDePasso (objeto de valor), a precedência é a aresta do M1 — o menor delta
   possível, coerente com o round ("dos três diagramas, o de menor risco") e com o corte
   (se a AT sair, sai limpa).

## Grafo de dependência das tarefas

```
T-01 (DoD fixada + pré-condições)
  └─► T-02 (data-model + contratos REST + esquema de exportação)
        ├─► T-03 (extração do pacote de suficiência causal; suíte do 005 verde)
        ├─► T-04 (ux-design.md do M4 + gate de UX)
        ├─► T-05 (teste da cadeia inteira, vermelho — a aptidão do round nasce aqui)
        ├─► T-06 (domínio ARF: papéis, espelho, ramos, verificação — TDD)   [usa T-03]
        ├─► T-07 (domínio APR: papéis, pares, elipses, corpus + verbalização — TDD)
        │     └─► T-08 (sequenciamento puro — TDD sobre grafos de fixture)
        ├─► T-09 (domínio AT: ficha do passo, status, precedência — TDD)
        └─► T-10 (agregado ReferenciaCruzada + promoções/semeaduras/derivações — TDD;
                  fica verde o T-05)
T-06..T-10 ─► T-11 (migrações Alembic + repositórios + casos de uso + REST + traço)
T-11 ─► T-12 (UI: canvas ARF + painel de ramos)          [consome T-04]
T-11 ─► T-13 (UI: canvas APR + tabela resumo + camadas)  [consome T-04]
T-11 ─► T-14 (UI: canvas AT + vista da cadeia + ações de promover/semear/derivar)
T-11 ─► T-15 (ações toc.* do M4 pela FSM do 006 + bandeja)
T-12..T-15 ─► T-16 (jornada viva da cadeia sintética) ─► T-17 (aptidões + qa-report)
T-17 ─► cauda (T-18..T-21: TAIL:review · TAIL:security · TAIL:mutation · TAIL:gate)
```

## Gates (DoR / DoD)

- **DoR — o ciclo não abre sem**: gate humano do 001 fechado; **ciclos 005 e 007
  promovidos** (o encadeamento parte do que eles produzem — pré-condição do roadmap);
  FSM do 006 no ar (as ações do M4 executam por ela); **decisão registrada sobre ramos
  negativos manuais nesta v1** (pré-condição do roadmap — a proposta do round é manual,
  o gate confirma); os 5 `[DÚVIDA]` do Clarify respondidos; `ux-design.md` do M4
  aprovado no gate de UX (T-04) antes de qualquer tarefa de UI.
- **DoD — o ciclo não fecha sem**: as 16 linhas da tabela de aceite da spec verdes com
  saída colada no `qa-report.md` (R1) e o tamanho do que cada portão examinou (R2); os
  três portões do roadmap cumpridos — a cadeia percorrida por teste com referência em
  cada elo, as três árvores exportáveis/importáveis pelo E1.4, a jornada da injeção à
  APR sequenciada com captura; cauda completa (`TAIL:review`, `TAIL:security`,
  `TAIL:mutation`, `TAIL:gate`).
- **Corte de apetite** (round 008 — F-12 da spec): estourou → **sai primeiro a AT**
  (E4.3) e com ela as derivações OI → AT; depois, as ações assistidas do M4 (INT-05..
  INT-08 viram declaração para ciclo futuro, o caminho que o M2 já pavimentou); **nunca
  sai o encadeamento** (E4.4) — sem ele o round entrega o próprio D-11. Perde escopo,
  não ganha ciclo.

## Riscos e portões

| Risco | Ligado a | Mitigação |
|---|---|---|
| GATE-apetite — três ferramentas + encadeamento estourarem o ciclo | L-03 | Corte em dois degraus declarado antes de abrir (AT primeiro, assistência depois, encadeamento nunca); os domínios ARF/APR/AT são paralelos por construção (decisão V do check) — o replanejamento no meio do ciclo corta ramo, não desfia o resto. |
| GATE-extracao — a extração do pacote de suficiência quebrar o M2 promovido | L-04 | A suíte do 005 verde é critério de aceite da T-03 (não do fim do ciclo); plano B declarado: duplicação temporária com dívida em ADR datado. |
| GATE-metodo — as três ferramentas nascerem sem precedente e errarem o método | L-01 | Fonte técnica citada com linha (spec F-09); regras decidíveis viram RN com teste; o que é julgamento fica declarado como julgamento (RN-07); a jornada viva completa é o teste de suficiência prática antes do gate humano. |
| GATE-verbalizacao — heurísticas de obstáculo/OI errarem para o lado do veto | L-02 | Aviso nunca bloqueia (RN-08); corpus sintético antes do código (T-07); `indeterminado` honesto herdado do M2; `TAIL:mutation` sabota o léxico e exige que o corpus pegue. |
| GATE-cadeia-linear — a vista da cadeia não representar análises ramificadas | L-05 | V1 declarada como travessia a partir de elemento de entrada com ramificações em lista (decisão 7); a jornada viva inclui um caso com duas ARFs semeadas para medir a dor real antes de investir em layout de grafo. |
| GATE-item8 — a linha entre manipulação direta e proposta borrar na implementação | spec RF-43..RF-45, INT-04 | Política declarada por tipo de ação (decisão 4); DoD 10 prova o lado da proposta (mutação direta recusada) e DoD 13 prova o lado direto (traço com referência); `TAIL:security` confere os dois regimes em contexto fresco. |
