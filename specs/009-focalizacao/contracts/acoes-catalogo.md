# Contrato do catálogo 009 — `toc.suggest_constraint`

> Siglas, uma vez neste documento: **TOC** — Teoria das Restrições · **ARA** — Árvore da
> Realidade Atual · **UDE** — Efeito Indesejável · **M2** — Árvore da Realidade Atual
> (módulo) · **M6** — Focalização · **APH** — Aplicação ↔ Harness · **FSM** — máquina de
> estados finitos · **IA** — inteligência artificial · **SDK** — *Software Development
> Kit* · **JSON** — *JavaScript Object Notation* · **UUID** — *Universally Unique
> Identifier* · **HTTP** — *HyperText Transfer Protocol* · **RF/RN** — requisito funcional
> / regra de negócio · **ADR** — *Architecture Decision Record* · **UI** — interface de
> usuário.

- **Manifesto**: [`../../006-acoes-governadas-e-snapshot/contracts/manifesto.json`](../../006-acoes-governadas-e-snapshot/contracts/manifesto.json)
  — o M6 acrescenta **1 ação** (total 16) e **3 telas** (total 12).
- **Execução**: [`../../../apps/api/src/toc_api/infra/federacao/executor.py`](../../../apps/api/src/toc_api/infra/federacao/executor.py)
  · declaração: [`../../../apps/api/src/toc_api/dominio/federacao/catalogo.py`](../../../apps/api/src/toc_api/dominio/federacao/catalogo.py)
  · telas: [`../../../apps/api/src/toc_api/dominio/federacao/telas.py`](../../../apps/api/src/toc_api/dominio/federacao/telas.py).
- **Regra que não se negocia (P2, ADR 0007)**: nenhum SDK de provedor, nenhuma chave e
  nenhum prompt no produto. A assistência entra pela fundação, pelo catálogo, e o verbo
  mutador **nasce `action_proposal`**.

## A ação

| Campo | Valor |
|---|---|
| `action_id` | `toc.suggest_constraint` |
| `title` | Sugerir a restrição a partir da Árvore da Realidade Atual |
| `risk` | `confirm` — mutadora: nasce proposta e espera o gate humano |
| `reversible` | `true` |
| `ui_route` | `/toc/focalizacao` |
| `intent_keywords` | `restricao`, `gargalo`, `focalizacao`, `sugerir` |

### `input_schema`

Objeto com `additionalProperties: false`. Obrigatórios: `projeto_id`, `ara_projeto_id`,
`no_id`, `descricao` (1..300), `tipo` (`fisica` \| `politica` \| `de_mercado`),
`justificativa` (1..4000). Opcional: `autor` (até 200; ausente, vale o principal da
introspecção).

**Por que `ara_projeto_id` e `no_id` são obrigatórios aqui e a rota manual não os exige.**
A assimetria é o requisito, não um descuido: uma restrição registrada à mão pode não ter de
onde ter vindo (RF-06), mas uma que **nasceu de uma sugestão sobre a ARA** tem — e a
referência é justamente a evidência que sustenta a conclusão (US-04). Uma proposta sem eles
não chega ao executor: o esquema a recusa antes.

### Saída

A confirmação executa `RegistrarRestricao` com a `ReferenciaDeOrigemDaRestricao`
(`ferramenta="ara"`, o projeto e o nó exato) e devolve `("executed", <id da restrição>)`.
Repositório não composto devolve `("failed", …)` — **fail-closed**, nunca sucesso mudo.

## O caminho de leitura que precede a ação

`POST /toc/focalizacao/analises/{projeto_id}/sugestoes-de-restricao` **não escreve nada**.
Devolve, por candidata, o nó de causa raiz da ARA vinculada ao passo `identificar`, o
racional, quantos UDEs ela alcança e a fração desse alcance — mais o `action_id` e o aviso
de que aplicar exige proposta. Sem ARA vinculada, a lista volta vazia e a jornada segue: a
sugestão é aceleradora, nunca dependência (RF-20).

**Uma proposta por candidata.** Não existe "aplicar todas": cada restrição sugerida é uma
decisão do grupo, e agrupá-las num único gate transformaria cinco julgamentos em um clique.

## A prova de que recusar é de graça (RF-21)

O teste compara o **estado serializado da análise byte a byte** antes de propor e depois de
recusar. Não é uma asserção sobre contagem de linhas: é a exportação canônica inteira. Uma
proposta recusada que tivesse tocado qualquer campo reprovaria.

## Capability ausente esconde a mutadora (RN, DoD 10)

Sem a capability declarada, `toc.suggest_constraint` **não aparece** no catálogo servido —
não aparece desabilitada, não aparece com aviso. A autorização vive fora do modelo de
linguagem (P2, §B.7.2/B.7.3 do APH): esconder é a projeção da política, não uma decisão da
UI.

## As três telas (INT-06)

Tela é **dado**, nunca instrução (item 7 da constituição). Cada campo declara `ai_visible`
individualmente, e a regra é a mesma dos módulos anteriores: **grandeza e vocabulário sim,
texto de pessoa não**.

| Tela | Rota | `ai_actions` | Campos com `ai_visible: false` |
|---|---|---|---|
| `toc.foco_jornada` | `/toc/focalizacao` | `READ`, `NAVIGATE` | `descricao_da_restricao` |
| `toc.foco_passo` | `/toc/focalizacao/passo` | `READ`, `NAVIGATE` | `decisao_em_rascunho`, `notas` |
| `toc.foco_linha_do_tempo` | `/toc/focalizacao/linha-do-tempo` | `READ` | nenhum (só contagens) |

Passo atual, tipo de restrição e contagem de pendências descrevem **onde** a análise está.
A descrição da restrição, as notas e as decisões são o que o grupo escreveu — conteúdo do
inquilino, que a assistência só recebe quando a pessoa o coloca numa ação governada, nunca
por raspagem de tela.

## Paridade cliente ↔ servidor

O registro de telas da interface
([`../../../apps/web/src/telas/registro.ts`](../../../apps/web/src/telas/registro.ts))
espelha as três com `declaradaNoManifesto: true`. A aptidão que mede o espelho é
`scripts/check-manifesto.sh` do lado do serviço e [`../../../apps/web/src/telas/registro.test.ts`](../../../apps/web/src/telas/registro.test.ts) do lado da
interface.
