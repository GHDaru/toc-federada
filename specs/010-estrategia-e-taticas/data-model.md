# Data model 010 — Estratégia & Táticas (M5)

> Siglas, uma vez neste documento: **TOC** — Teoria das Restrições · **S&T** — Estratégia &
> Táticas (*Strategy & Tactics*) · **M1** — Núcleo de Diagramas Lógicos · **M5** — o módulo
> Estratégia & Táticas · **DDD** — *Domain-Driven Design* (Design Orientado a Domínio) ·
> **UUID** — *Universally Unique Identifier* (identificador único universal) · **VCD** —
> *Value Creating Deliverable* (entregável gerador de valor, jargão da linhagem) ·
> **RF/RN/RNF/RI** — requisito funcional / regra de negócio / requisito não funcional /
> requisito de interface · **SQL** — *Structured Query Language* · **ADR** — *Architecture
> Decision Record* (Registro de Decisão Arquitetural) · **HTTP** — *HyperText Transfer
> Protocol*.

- **Estado**: consolidado na execução do ciclo 010. Os testes de domínio nascem primeiro
  (P4) e **prevalecem** sobre este documento; divergência se resolve a favor do teste e
  volta aqui como correção.
- **Origem**: [`spec.md`](spec.md) § Entidades · extensão declarada de
  [`../004-nucleo-de-diagramas/data-model.md`](../004-nucleo-de-diagramas/data-model.md).
- **Forma final em código**: [`../../apps/api/src/toc_api/dominio/snt.py`](../../apps/api/src/toc_api/dominio/snt.py)
  · persistência em [`../../apps/api/src/toc_api/infra/persistencia/tabelas.py`](../../apps/api/src/toc_api/infra/persistencia/tabelas.py)
  · migração [`../../apps/api/src/toc_api/alembic/versions/0009_m5_estrategia_e_taticas.py`](../../apps/api/src/toc_api/alembic/versions/0009_m5_estrategia_e_taticas.py).

## O corte: composição sobre o M1, árvore estrita, e **nenhum número gravado**

A `ArvoreSnT` **contém** um `Projeto` do M1 (`ferramenta="snt"`) e herda dele o que já
estava resolvido: dono por inquilino, exclusão suave, restauração, listagem e a **trava
otimista por versão lida** (ADR 0010). O que ela acrescenta são duas coisas que a linhagem
não tinha:

1. **Estrutura de árvore estrita.** Cada passo tem no máximo um pai e uma posição ordinal
   entre irmãos. **Não existe aresta como entidade** — o `edges: AraEdge[] // Reusing
   AraEdge for simplicity` da quarta geração (`tocbuilderv3/types.ts:310`) permitia
   topologias que não são árvore; aqui multi-pai e ciclo são irrepresentáveis, e a única
   recusa necessária é mover um passo para dentro da própria subárvore (RN-04).
2. **Numeração derivada.** O número `1`/`1.1`/`1.1.2` é **função pura da estrutura**, não
   um campo. Não há coluna de número no banco, não há parâmetro de número em operação
   nenhuma e a exportação não o carrega (RN-01). Na linhagem ele era texto digitado
   obrigatório sem validação (`tocbuilderv3/types.ts:288`,
   `components/SnTStepEditorModal.tsx:56-57`), e nenhuma das dez funções de serviço o
   conferia.

Toda mutação entra pela raiz. Passo, premissas e status **não têm caminho próprio de
escrita** — é a invariante que `scripts/check-raiz-do-agregado.sh` mede, e o `Projeto`
contido recusa mutação de grafo que não venha de `sob_a_raiz` (`MutacaoForaDaRaiz`).

## Agregado: ArvoreSnT (raiz)

| Atributo | Tipo | Regra |
|---|---|---|
| `projeto` | `Projeto` (M1) | composição; `projeto.ferramenta` tem de ser `snt`, senão `MutacaoRecusada` |
| `id` / `dono` / `versao` / `estado` | delegados ao `Projeto` | isolamento, trava otimista e exclusão suave vêm do núcleo |
| `meta_global` | texto, 1..2000 | **obrigatória** (RF-01) — é o `overallGoal` da linhagem, promovido a exigência |
| `_fichas` | `dict[UUID, FichaDoPasso]` | conteúdo do passo; a chave é o `no.id` do M1 |
| `_estrutura` | `dict[UUID \| None, tuple[UUID, ...]]` | `pai → filhos na ordem`; `None` são as raízes. É **toda** a estrutura da árvore |
| `_numeros` | `dict[UUID, str]` | **derivado**, nunca persistido; recalculado em `reidratar_snt` |

## Entidade do agregado: PassoSnT

O passo é um **nó do M1** (`tipo="snt_passo"`, título = estratégia) mais a ficha e a posição
na estrutura. Não há entidade nova de identidade: o `UUID` é o do nó, o que mantém a
exclusão em cascata, a exportação e a vista tabular do núcleo funcionando sem exceção.

## Objetos de valor

### FichaDoPasso

| Campo | Tipo | Regra |
|---|---|---|
| `estrategia` | texto, 1..200 | **obrigatória** na criação (RF-11); é o título do nó do M1, mantido em sincronia por dentro da raiz |
| `tatica` | texto, 0..4000 | pode nascer vazia — vira **pendência**, nunca bloqueio (RN-06) |
| `premissas` | `PremissasDoPasso` | as três, com papel estrutural (RN-02) |
| `status` | `StatusDoPasso` | os quatro da linhagem; padrão `nenhum` |
| `categoria` | `CategoriaDoPasso` | os seis da linhagem, **opcional**; padrão `nenhuma` (ADR 0014) |

### PremissasDoPasso

Os três campos são verbatim os do modelo da linhagem — `parallelAssumption`,
`necessaryAssumptionToParent`, `sufficiencyOfChildrenAssumption`
(`tocbuilderv3/types.ts:293-295`, e já em `TOC-Builder/types.ts:243-245`, na primeira
geração). O que este ciclo acrescenta é a semântica:

| Papel | Aplicável a | Pendência quando |
|---|---|---|
| `paralela` | todo passo | nunca — é pressuposto de contexto, e a ausência dele não quebra elo nenhum |
| `necessidade_ao_pai` | passo **não-raiz** | ausente em passo com pai |
| `suficiencia_dos_filhos` | passo **com filhos** | ausente em passo que tem filhos |

### NumeroDoPasso (derivado, não é campo)

Duas funções puras, e a segunda existe por desempenho:

- `numeracao(estrutura)` — recalcula a árvore inteira. É a **definição**.
- `renumerar(numeros, estrutura, pais_afetados=…)` — recalcula só a subárvore afetada.

A propriedade que sustenta a segunda é testada e não suposta: **local == total**, sobre 200
árvores geradas com semente fixa (`apps/api/tests/dominio/test_numeracao.py`). Sem ela, a otimização
seria uma segunda fonte de verdade — o defeito de que este módulo nasceu para se livrar.

## Enumerações (vocabulário fechado)

| Enum | Valores | Origem |
|---|---|---|
| `StatusDoPasso` | `nenhum` · `validado` · `nao_validado` · `em_execucao` | `tocbuilderv3/types.ts:270-275` (já em português lá) |
| `CategoriaDoPasso` | `nenhuma` · `estrategia` · `tatica` · `vcd` · `build` · `leverage` | `tocbuilderv3/types.ts:277-284` (ADR 0014) |

Transição de status é **livre entre os quatro** (ADR 0014). O que é recusado:
`sem_mudanca` (o valor já é esse), `autor_obrigatorio` (mudança sem autor) e valor fora do
enum.

## Serviço de domínio: PendenciasDaArvore

Função pura sobre `(estrutura, fichas, numeros)`. Devolve as pendências dos três tipos
fechados, as contagens por status e — porque a regra R2 vale também para uma função — o
**denominador**: `passos_examinados`.

| Tipo de pendência | Quando |
|---|---|
| `sem_premissa_de_necessidade` | passo não-raiz sem a premissa de necessidade |
| `sem_premissa_de_suficiencia` | passo com filhos sem a premissa de suficiência |
| `sem_tatica` | passo sem tática (a estratégia é impossível de faltar: é obrigatória) |

O painel e a árvore consomem **esta** função, nunca um dado paralelo.

## Eventos de domínio (somente-acréscimo)

`ArvoreSnTCriada` · `MetaGlobalEditada` · `PassoDaSnTAdicionado` (com `pai_id` e `numero`) ·
`PassoDaSnTEditado` · `PassoDaSnTMovido` (com número antes/depois e a contagem de
descendentes) · `SubarvoreExcluida` (**com a contagem**) · `PremissasEditadas` ·
`StatusDoPassoMudou` (com `de`, `para` e **autor**).

Nenhum deles carrega texto de pessoa: número, contagem e vocabulário fechado viajam;
estratégia, tática e premissa ficam no agregado (ADR 0006 e P5 juntos).

## Persistência (migração 0009)

Duas tabelas, e o que elas **não** têm é a decisão:

### `snt_arvore`

| Coluna | Tipo | Restrição |
|---|---|---|
| `projeto_id` | `uuid` | chave primária; `FK → projeto(id) ON DELETE CASCADE` |
| `meta_global` | `text` | `ck_snt_arvore_meta_global_obrigatoria`: `length(btrim(...)) > 0` |

### `snt_passo`

| Coluna | Tipo | Restrição |
|---|---|---|
| `no_id` | `uuid` | chave primária; `FK → no(id) ON DELETE CASCADE` |
| `projeto_id` | `uuid` | `FK → projeto(id) ON DELETE CASCADE`; índice |
| `pai_id` | `uuid` nulo | `FK → no(id) ON DELETE CASCADE`; nulo = raiz; `ck ... pai_diferente_do_passo` |
| `ordem` | `integer` | `ck ... ordem_nao_negativa`; posição entre irmãos |
| `estrategia` | `text` | `ck ... estrategia_obrigatoria` |
| `tatica` | `text` | padrão `''` |
| `categoria` | `text` | `ck ... categoria_do_passo_snt` — os seis valores |
| `status` | `text` | `ck ... status_do_passo_snt` — os quatro valores |
| `premissa_paralela` · `premissa_necessidade_ao_pai` · `premissa_suficiencia_dos_filhos` | `text` | padrão `''` |

**Ordem única entre irmãos, em duas peças**: `uq_snt_passo_ordem_entre_irmaos`
(`projeto_id, pai_id, ordem`) para os filhos e o índice **parcial**
`uq_snt_passo_raiz_ordem` (`projeto_id, ordem WHERE pai_id IS NULL`) para as raízes. A
segunda existe porque, em SQL, `NULL` não é igual a `NULL`: sem ela as raízes ficariam de
fora da unicidade, e é justamente nas raízes que a numeração `1..n` começa.

**Não existe coluna de número** — e isso é medido, não prometido:
`tests/integracao/test_snt_no_postgres.py::test_a_numeracao_nao_esta_no_banco_em_coluna_nenhuma`
lê o `information_schema` do esquema migrado e exige zero colunas com "numero" no nome.

### A reordenação e o afastamento das posições

A unicidade de `(projeto_id, pai_id, ordem)` é do banco, e uma reordenação move duas linhas
para posições que a outra ainda ocupa. O adaptador afasta **todas** as posições do projeto
por `AFASTAMENTO_DE_ORDEM` antes de regravá-las, dentro da mesma transação. O afastamento é
positivo (e não negativo) porque `ordem` tem restrição de não-negatividade — e alto o
bastante para não colidir com irmandade nenhuma de plano real.

## Exportação (RF-21)

`toc.snt/1`. O documento carrega meta global, nome e os passos em ordem estrutural, cada um
com `pai` **por índice na própria lista** — e **nenhum número**. A numeração deriva na
importação, e por isso divergência entre estrutura e numeração é impossível por construção.
Um teste faz a ida e volta e compara a numeração dos dois lados, além de conferir que a
palavra "numero" não aparece no documento serializado.
