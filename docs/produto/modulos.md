# Módulos — o mapa M1–M8

> Siglas deste documento: **TOC** — Teoria das Restrições; **ARA** — Árvore da Realidade
> Atual; **UDE** — Efeito Indesejável; **NC** — Nuvem de Conflito; **ARF** — Árvore da
> Realidade Futura; **APR** — Árvore de Pré-Requisitos; **AT** — Árvore de Transição;
> **S&T** — Árvore de Estratégia & Táticas; **OI** — Objetivo Intermediário; **APH** — o
> padrão Aplicação ↔ Harness; **ADR** — Registro de Decisão Arquitetural; **IA** —
> inteligência artificial; **FSM** — máquina de estados finitos; **OTel** — OpenTelemetry;
> **SSE** — *Server-Sent Events*; **i18n** — internacionalização; **CRUD** — criar, ler,
> atualizar, excluir; **eTLD+1** — o "site" no sentido do navegador.

- **Status**: rascunho do ciclo 001 (aprovação: gate humano do ciclo) · **Data**: 2026-09-03
- **Decisão de taxonomia**: ADR 0004 — Módulo (M) ⊃ Épico (E) ⊃ Feature (F) ⊃ User Story
  (US). Este documento fixa **módulos e épicos**; features, stories e requisitos vivem na
  spec de cada módulo.
- **Origem**: [`visao.md`](visao.md) (linhagem lida e medida) · ordem de construção em
  [`rounds.md`](rounds.md) e [`../roadmap.md`](../roadmap.md).

Cada módulo é um *bounded context* no sentido do Design Orientado a Domínio (DDD): um
vocabulário consistente, um modelo próprio, uma fronteira explícita. Os cortes seguem o
princípio V do método (paralelizar por fronteira de contexto) — e cada um responde a algo
que a linhagem provou, mediu ou nunca entregou (defeitos D-NN da
[`visao.md`](visao.md) §6).

## O mapa

| M | Nome | Bounded context (o vocabulário que governa) | Origem principal |
|---|---|---|---|
| **M1** | Núcleo de Diagramas Lógicos | projeto, nó, aresta causal, canvas + vista tabular | linhagem (todas as gerações) |
| **M2** | Árvore da Realidade Atual (ARA) | UDE validada, causas, suficiência, análise | a ferramenta mais madura da linhagem |
| **M3** | Nuvem de Conflito (NC) | 5 entidades, 7 premissas, injeções, visão conflito+solução | 3ª/4ª gerações + skill `toc-evaporating-cloud` |
| **M4** | Árvores de Futuro e Implementação | ARF, APR (obstáculo → OI), AT, encadeamento entre ferramentas | nunca entregues em 4 gerações (D-04); skill `toc-prt` |
| **M5** | Estratégia & Táticas (S&T) | numeração hierárquica, 3 premissas lógicas, status | única ferramenta que regrediu (D-05) |
| **M6** | Focalização | restrição registrada, jornada guiada pelos 5 passos | novo (ADR 0005; D-09) |
| **M7** | Federação APH | identidade/introspecção, admissão, embarque `ghd.*`, manifesto, catálogo `toc.*`, `action_proposal`, snapshot, wire | `GHDaru/protocolos` + `GHDaru/ghdaru` + lições da irmã |
| **M8** | Fundações da Aplicação | persistência própria, OTel, i18n, docs embutida, export/import, deploy | violações canônicas do v3 corrigidas (D-03, D-07) |

## M1 — Núcleo de Diagramas Lógicos

**O job**: tudo que é comum às seis ferramentas — projeto, nó, aresta causal, o canvas e a
sua vista tabular equivalente — existe **uma vez**, aqui. Na linhagem, cada ferramenta
carregava a sua cópia de canvas e painel; o M1 é a fatoração que impede a sétima cópia.

| Épico | Nome | Entrega |
|---|---|---|
| E1.1 | Projetos e organização | CRUD de projetos por (inquilino, usuário), *soft delete*, papéis de acesso |
| E1.2 | Canvas | nós, arestas, edição direta, desfazer de sessão |
| E1.3 | Vista tabular equivalente | o painel de entidades da linhagem, como projeção do mesmo modelo |
| E1.4 | Exportação/importação JSON | não destrutiva: valida, relata, nunca substitui em silêncio |

- **Fontes**: `tocbuilderv3/components/AraCanvas.tsx`, `EntitiesPanel.tsx` (a dupla
  canvas+tabela que funciona) · `tocbuilderv3/APLICATION_PURPOSE.md:22-25` 🟢
- **Depende de**: E8.1 (persistência) e E7.1 (identidade) — por isso o esqueleto vem antes.
- **Spec**: `specs/004-nucleo-de-diagramas/`

## M2 — Árvore da Realidade Atual

**O job**: dos sintomas à causa raiz. A ferramenta mais madura da linhagem, refeita com a
diferença que importa: os critérios formais de UDE saem do prompt
(`tocbuilderv3/constants.ts:109-137` 🟢, defeito D-08) e viram **regra de domínio pura**,
testável sem rede.

| Épico | Nome | Entrega |
|---|---|---|
| E2.1 | UDEs e validação formal | critérios da TOC como regra de domínio; o modelo só opina no que é julgamento |
| E2.2 | Construção da árvore | causas, relações causais, análise de suficiência |
| E2.3 | Assistência via catálogo | sugerir UDEs/causas/relações, analisar árvore — tudo `action_proposal` |

- **Fontes**: `tocbuilderv3/APLICATION_PURPOSE.md:53-58` (validação) 🟢 ·
  `tocbuilderv3/components/UdeValidationModal.tsx` 🟢
- **Depende de**: M1 (nó/aresta/canvas); E2.3 depende de E7.3–E7.4 (catálogo e FSM).
- **Spec**: `specs/005-arvore-da-realidade-atual/`

## M3 — Nuvem de Conflito

**O job**: o dilema em 5 entidades (objetivo A, necessidades B e C, ações D e D′ —
`tocbuilderv3/types.ts:77-82` 🟢), as 7 arestas com premissas, e as injeções que evaporam
o conflito. A geração assistida a partir de narrativa — o melhor recurso do v3
(`tocbuilderv3/APLICATION_PURPOSE.md:29` 🟢) — permanece, mas pela fundação.

| Épico | Nome | Entrega |
|---|---|---|
| E3.1 | Modelagem do conflito | as 5 entidades e as arestas, com edição direta |
| E3.2 | Premissas e injeções | premissas por aresta; injeção ligada à premissa que invalida |
| E3.3 | Geração assistida a partir de narrativa | texto livre → proposta de nuvem completa, via catálogo |
| E3.4 | Visão conflito+solução | os dois diagramas lado a lado, como no v3 |

- **Fontes**: `tocbuilderv3/types.ts:68-107` 🟢 ·
  `tocbuilderv3/components/ConflictCloudView.tsx` 🟢 · skill `toc-evaporating-cloud`
  (5 entidades, 7 premissas — conteúdo técnico)
- **Depende de**: M1; E3.3 depende de E7.3–E7.4.
- **Spec**: `specs/007-nuvem-de-conflito/`

## M4 — Árvores de Futuro e Implementação

**O job**: a metade da TOC que quatro gerações prometeram e nenhuma entregou (D-04) — e o
**encadeamento**, que nenhuma sequer modelou (D-11): UDE da ARA alimenta a NC; injeção da
NC semeia a ARF; a ARF gera os obstáculos que a APR sequencia em OIs.

| Épico | Nome | Entrega |
|---|---|---|
| E4.1 | ARF | injeções → efeitos futuros; ramos negativos identificados |
| E4.2 | APR | obstáculos → OIs, com sequenciamento de dependências |
| E4.3 | AT | passos de transição, cada um com a sua lógica |
| E4.4 | Encadeamento | as referências cruzadas entre ferramentas como cidadãs do modelo |

- **Fontes**: navegação desabilitada nas 4 gerações
  (`tocbuilderv3/components/Sidebar.tsx:55-57` 🟢) — a lacuna é a fonte · skill `toc-prt`
  (obstáculos → OIs — conteúdo técnico)
- **Depende de**: M2 e M3 (o encadeamento parte do que eles produzem).
- **Spec**: `specs/008-arvores-de-futuro-e-implementacao/`

## M5 — Estratégia & Táticas

**O job**: devolver a ferramenta que regrediu (D-05). O modelo de dados já existia
completo na linhagem — numeração hierárquica (1, 1.1, 1.1.2) e as três premissas lógicas
(paralelismo, necessidade ao pai, suficiência dos filhos:
`tocbuilderv3/types.ts:286-295` 🟢) — e ficou duas gerações desligado.

| Épico | Nome | Entrega |
|---|---|---|
| E5.1 | Estrutura hierárquica | numeração, três premissas por nó |
| E5.2 | Status e acompanhamento | Validado / Não Validado / Em Execução (`tocbuilderv3/types.ts:270-275` 🟢) |

- **Depende de**: M1.
- **Spec**: `specs/010-estrategia-e-taticas/`

## M6 — Focalização

**O job**: os cinco passos de focalização — identificar → explorar → subordinar → elevar →
recomeçar — como jornada que **liga** as ferramentas, e o registro da restrição como
entidade de primeira classe. Inteiramente novo: zero ocorrências na linhagem (D-09,
medição colada na [`visao.md`](visao.md) §6). Escopo fixado pelo ADR 0005.

| Épico | Nome | Entrega |
|---|---|---|
| E6.1 | Registro da restrição | a restrição e o passo atual, por análise |
| E6.2 | Jornada guiada | cada passo aponta a ferramenta certa, com o estado herdado do passo anterior |

- **Depende de**: M2 e M4 (a jornada costura o que eles produzem); registro (E6.1) só de M1.
- **Spec**: `specs/009-focalizacao/`

## M7 — Federação APH

**O job**: o lado aplicação do Anexo B do padrão APH, Nível 2 (Operador), `mode: embedded`
— identidade por `POST /auth/introspect`, embarque por iframe com envelope `ghd.*`,
manifesto e catálogo `toc.*`, todo verbo mutador do modelo nascendo `action_proposal`,
tela como dado (nunca instrução), snapshot sanitizado no servidor.

| Épico | Nome | Entrega |
|---|---|---|
| E7.1 | Identidade e admissão | introspecção; 4 parâmetros de admissão com falha rápida |
| E7.2 | Embarque | iframe, envelope `ghd.*`, tema por lista de permissões com *fallback*, modo conteúdo |
| E7.3 | Manifesto e catálogo `toc.*` | o que a aplicação declara e o que o modelo enxerga |
| E7.4 | Ações governadas | FSM de proposta, traço por ação, lote |
| E7.5 | Tela é dado | registro de telas; snapshot sanitizado no servidor |
| E7.6 | Wire APH Nível 1 | SSE, `seq`, replay, cancelamento, códigos de erro |

- **Fontes**: `protocolos/padrao/padrao-aph.md`, `protocolos/padrao/anexo-b-federacao.md`,
  `protocolos/padrao/schemas/federacao-manifesto.schema.json` 🟢 ·
  `ghdaru/docs/integration/guia-desenvolvedor-app-federada.md` 🟢 · as lições pagas pela
  irmã: `gestaodeprioridades/mensagens/005-para-ghdaru-embarque-da-prioridades.md` 🟢
- **Depende de**: E8.1/E8.2/E8.5 (não há introspecção sem servidor, nem manifesto sem
  endereço publicado). Bloqueios externos conhecidos: ver [`rounds.md`](rounds.md).
- **Specs**: `specs/003-esqueleto-federado/` (E7.1–E7.2) e
  `specs/006-acoes-governadas-e-snapshot/` (E7.3–E7.6)

## M8 — Fundações da Aplicação

**O job**: tudo que a linhagem simulou ou adiou, de verdade e de nascença — o backend que
foi especificado quatro vezes e construído zero (D-03), a persistência que era
`localStorage` (D-07), a observabilidade que nunca existiu.

| Épico | Nome | Entrega |
|---|---|---|
| E8.1 | Persistência própria | PostgreSQL Neon (projeto próprio), migrações Alembic, isolamento por inquilino |
| E8.2 | Observabilidade OTel | traço, log correlacionado e métrica nascem com cada funcionalidade (P5) |
| E8.3 | i18n pt/en | desde o início, português como língua-fonte |
| E8.4 | Documentação embutida | por ferramenta, na aplicação (sucede o `DocsView` do v3 🟢) |
| E8.5 | Deploy | site próprio em eTLD+1 distinto do hospedeiro |

- **Fontes**: `tocbuilderv3/api_specifications.md` (a intenção, 435 linhas, nunca
  implementada — md5 idêntico nas 4 gerações, medição na [`visao.md`](visao.md) §6 D-03)
  🟢 · stack por ADR 0002.
- **Depende de**: nada — é a base de todos.
- **Specs**: `specs/003-esqueleto-federado/` (E8.1, E8.2, E8.5) e
  `specs/011-fundacoes-da-aplicacao/` (E8.3, E8.4 e E1.4 avançado)

## Dependências entre módulos e ordem de construção

O grafo lê-se de cima para baixo; o número entre parênteses é o ciclo do
[`../roadmap.md`](../roadmap.md) que entrega o módulo (ou a fatia de épicos indicada).

```
                    ┌────────────────────────────────────────────┐
                    │  003 · esqueleto federado (raia infra)     │
                    │  E8.1 persistência · E8.2 OTel · E8.5 dep. │
                    │  E7.1 identidade  · E7.2 embarque          │
                    └─────────────────────┬──────────────────────┘
                                          │
                             ┌────────────▼────────────┐
                             │   M1 · Núcleo (004)     │
                             └──┬───────┬──────────┬───┘
                                │       │          │
             ┌──────────────────▼──┐    │     ┌────▼───────────────┐
             │   M2 · ARA (005)    │    │     │   M5 · S&T (010)   │
             └──────────┬──────────┘    │     └────────────────────┘
                        │               │
   ┌────────────────────▼───────────┐   │
   │ E7.3–E7.6 · catálogo toc.*,    │   │   (o catálogo assiste M2, M3 e M4:
   │ FSM, telas, snapshot, wire(006)│   │    E2.3, E3.3 e as sugestões do M4)
   └────────────────────┬───────────┘   │
                        │          ┌────▼───────────────┐
                        │          │   M3 · NC (007)    │
                        │          └────┬───────────────┘
                        └───────┬───────┘
                        ┌───────▼──────────────────────┐
                        │ M4 · ARF/APR/AT + encadeamento│
                        │           (008)               │
                        └───────┬──────────────────────┘
                        ┌───────▼──────────────────────┐
                        │   M6 · Focalização (009)      │
                        └───────┬──────────────────────┘
                        ┌───────▼──────────────────────┐
                        │ M8 restante · E8.3/E8.4/E1.4  │
                        │           (011)               │
                        └───────┬──────────────────────┘
                        ┌───────▼──────────────────────┐
                        │ 012 · jornadas consolidadas + │
                        │ autodeclaração APH Nível 2    │
                        └──────────────────────────────┘
```

Duas arestas merecem a explicação em texto:

- **M3 (007) vem depois do catálogo (006)**, e não antes, porque o melhor recurso da NC é
  a geração assistida (E3.3) — entregá-la sem catálogo forçaria ou um SDK provisório
  (violaria o ADR 0007 e repetiria D-01) ou uma NC amputada do que a distingue.
- **M5 (010) depende só de M1** e poderia ser construído mais cedo; fica atrás de M4 e M6
  porque o encadeamento e a focalização valem mais para o teste da federação, e apetite é
  fixo — a ordem é escolha de valor, não de técnica (registrada no
  [`../roadmap.md`](../roadmap.md)).

## O que este documento não decide

- **Features, user stories e requisitos** de cada módulo — são das specs (formato no ADR
  0004), com as suas lacunas L-NN e o seu `## Clarify`.
- **Escopo excluído da v1** (DBR, contabilidade de ganho) — é o ADR 0005, com a medição
  de zero ocorrências colada na [`visao.md`](visao.md) §6 (D-09).
- **A resposta às cinco dúvidas do Product Steward** ([`visao.md`](visao.md) §7) — a
  primeira delas (colaboração por projeto) muda o E1.1 e precisa estar respondida antes
  de a spec do M1 congelar.
