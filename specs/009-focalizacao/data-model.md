# Data model 009 — Focalização (M6)

> Siglas, uma vez neste documento: **TOC** — Teoria das Restrições · **M1** — Núcleo de
> Diagramas Lógicos · **M2** — Árvore da Realidade Atual (ARA) · **M3** — Nuvem de
> Conflito (NC) · **M4** — Árvores de Futuro e Implementação · **ARF** — Árvore da
> Realidade Futura · **APR** — Árvore de Pré-Requisitos · **AT** — Árvore de Transição ·
> **M6** — Focalização · **DDD** — *Domain-Driven Design* (Design Orientado a Domínio) ·
> **UUID** — *Universally Unique Identifier* (identificador único universal) · **RF/RN/
> RNF/RI** — requisito funcional / regra de negócio / requisito não funcional / requisito
> de interface · **SQL** — *Structured Query Language* · **ADR** — *Architecture Decision
> Record* (Registro de Decisão Arquitetural) · **HTTP** — *HyperText Transfer Protocol*.

- **Estado**: consolidado na execução do ciclo 009. Os testes de domínio nascem primeiro
  (P4) e **prevalecem** sobre este documento; divergência se resolve a favor do teste e
  volta aqui como correção.
- **Origem**: [`spec.md`](spec.md) § Entidades · extensão declarada de
  [`../004-nucleo-de-diagramas/data-model.md`](../004-nucleo-de-diagramas/data-model.md).
- **Forma final em código**: [`../../apps/api/src/toc_api/dominio/focalizacao.py`](../../apps/api/src/toc_api/dominio/focalizacao.py)
  · persistência em [`../../apps/api/src/toc_api/infra/persistencia/tabelas.py`](../../apps/api/src/toc_api/infra/persistencia/tabelas.py)
  · migração [`../../apps/api/src/toc_api/alembic/versions/0008_m6_focalizacao.py`](../../apps/api/src/toc_api/alembic/versions/0008_m6_focalizacao.py).

## O corte: composição sobre o M1, e nenhum grafo

A `AnaliseDeFocalizacao` **contém** um `Projeto` do M1 (`ferramenta="focalizacao"`) e
herda dele o que já estava resolvido: dono por inquilino, exclusão suave, restauração e a
**trava otimista por versão lida** (ADR 0010). O que ela **não** usa é o grafo: uma
análise não tem nó nem aresta causal, e por isso o adaptador de escrita chama
`_gravar_projeto` sem `_reconciliar_grafo`. A jornada não é um diagrama — é um percurso.

## Agregado: AnaliseDeFocalizacao (raiz)

| Atributo | Tipo | Regra |
|---|---|---|
| `projeto` | `Projeto` (M1) | composição; `projeto.ferramenta` tem de ser `focalizacao`, senão `MutacaoRecusada` |
| `id` / `dono` / `versao` / `estado` | delegados ao `Projeto` | isolamento, trava otimista e exclusão suave vêm do núcleo, não são reimplementados |
| `sistema` | `SistemaAnalisado` | obrigatório: "restrição de quê?" precisa de resposta |
| `_ciclos` | lista de `CicloDeFocalizacao` | interna ao agregado; a raiz só devolve tupla |

Toda mutação entra pela raiz. Ciclo, passo, restrição, vínculo e herança **não têm caminho
próprio de escrita** — é a invariante que `scripts/check-raiz-do-agregado.sh` mede.

## Entidades internas

**CicloDeFocalizacao** — uma volta completa dos cinco passos; a unidade da linha do tempo.

| Atributo | Tipo | Regra |
|---|---|---|
| `id` | UUID | único na análise |
| `ordem` | inteiro ≥ 1 | sequencial, único por análise (`uq_foco_ciclo_ordem`) |
| `estado` | `aberto` \| `fechado` | **no máximo um `aberto` por análise** (RN-02) |
| `aberto_em` / `fechado_em` | instante \| nulo | `fechado_em` só existe no estado `fechado` |
| `passos` | tupla de 5 `PassoDeFocalizacao` | tem de ser exatamente `ORDEM_CANONICA`, senão `PassoInvalido("ordem_canonica")` |
| `restricao` | `Restricao` \| nulo | **no máximo uma por ciclo** (RN-03) |
| `heranca` | tupla de `DecisaoHerdada` | vazia no ciclo 1; preenchida pelo recomeço |

**PassoDeFocalizacao** — um dos cinco. O `tipo` é imutável: quem cria os passos é o ciclo.

| Atributo | Tipo | Regra |
|---|---|---|
| `tipo` | `identificar` \| `explorar` \| `subordinar` \| `elevar` \| `recomecar` | RN-01: cinco, nomeados, ordenados; não se cria, não se exclui, não se reordena |
| `estado` | `pendente` \| `em_andamento` \| `concluido` | |
| `decisoes` | tupla de `DecisaoDePasso` | **somente-acréscimo** (RN-04); `decisao` é a última |
| `notas` | tupla de `NotaDePasso` | acumulável; anotar **não** avança a jornada |
| `vinculos` | tupla de `VinculoDeFerramenta` | |
| `reaberturas` | tupla de `Reabertura` | fato registrado **ao lado** da decisão, nunca no lugar dela |

**Restricao** — a entidade que dá nome à teoria.

| Atributo | Tipo | Regra |
|---|---|---|
| `id` | UUID | |
| `descricao` | texto 1..300 | obrigatório |
| `tipo` | `fisica` \| `politica` \| `de_mercado` | enum **fechado** (ADR 0013) |
| `justificativa` | texto 1..4000 | obrigatória — restrição sem porquê é palpite |
| `autor` | texto 1..200 | |
| `registrada_em` | instante | do relógio-porta, nunca `datetime.now()` no domínio |
| `origem` | `ReferenciaDeOrigemDaRestricao` \| nulo | opcional: a ARA ajuda, nunca condiciona (RF-06) |

**DecisaoHerdada** — uma regra de operação do ciclo anterior, esperando veredito. Mutável
de propósito (existe para **receber** julgamento); o `texto` nunca muda.

| Atributo | Tipo | Regra |
|---|---|---|
| `id` / `ciclo_de_origem` / `passo` / `texto` | UUID / inteiro / tipo de passo / texto | imutáveis |
| `veredito` | `pendente` \| `mantida` \| `revogada` | nasce `pendente`; sair dele exige `justificativa` **e** `autor` (RN-05) |
| `justificativa` / `autor` / `julgada_em` | texto / texto / instante \| nulo | preenchidos só depois do veredito |

## Objetos de valor

- **SistemaAnalisado** — `(nome 1..200, descricao 0..4000)`. Imutável.
- **ReferenciaDeOrigemDaRestricao** — `(ferramenta, projeto_id, no_id)`. Tipada, nunca
  texto solto (INT-02). A navegação de volta resolve por consulta ao M6, **sem campo novo
  em M2–M4** (L-03: `AnaliseDeFocalizacao.vinculos_do_projeto`).
- **DecisaoDePasso** — `(texto 1..4000, autor 1..200, instante)`. Imutável; nunca se
  sobrescreve.
- **NotaDePasso** — `(id, texto 1..4000, autor, instante)`.
- **Reabertura** — `(justificativa, autor, instante)`.
- **VinculoDeFerramenta** — `(id, tipo ∈ {ara, nc, arf, apr, at}, projeto_id, papel,
  justificativa, canonico)`. **Referência, nunca cópia**: não há campo de conteúdo aqui de
  propósito — um título de nó copiado para dentro do M6 envelheceria no primeiro `PUT` do
  outro módulo.

## A tabela canônica (RN-06) — regra de domínio, não `if` espalhado

| Passo | Ferramentas canônicas |
|---|---|
| `identificar` | ARA |
| `explorar` | NC, ARF |
| `subordinar` | NC |
| `elevar` | APR, AT |
| `recomecar` | nenhuma — o ato dele é abrir o ciclo seguinte |

Fora da tabela o vínculo **não é proibido**: exige `justificativa` e carrega aviso. O
método educa; o dado obedece ao grupo — o mesmo desenho não bloqueante do M2 e do M3.

## Inércia: quais decisões atravessam o recomeço

`PASSOS_QUE_GERAM_INERCIA = (explorar, subordinar)`. O que sobrevive por conta própria são
**regras de operação**: como se explora a restrição e a que ela subordina o resto. A
decisão de `identificar` morre com o ciclo (a restrição dela foi quebrada — é por isso que
se recomeçou) e a de `elevar` é um plano executado, não uma regra vigente.

Uma decisão herdada julgada `mantida` **volta à mesa no recomeço seguinte** (ADR 0013): o
contrário faria de "mantida uma vez" um passe vitalício, que é a definição operacional da
inércia que o quinto passo existe para impedir. Julgada `revogada`, ela morre ali.

## Eventos de domínio (somente-acréscimo)

`AnaliseCriada` · `CicloAberto` · `CicloFechado` · `RestricaoRegistrada` ·
`RestricaoEditada` · `PassoIniciado` · `PassoConcluido` · `PassoReaberto` ·
`NotaRegistrada` · `VinculoCriado` · `VinculoRemovido` · `DecisaoHerdadaJulgada`.

Declarados em [`../../apps/api/src/toc_api/dominio/eventos.py`](../../apps/api/src/toc_api/dominio/eventos.py),
por acréscimo ao registro do M1 — o arquivo nunca é reescrito.

## Invariantes (cada uma nasce como teste de domínio que falha primeiro)

| # | Invariante | Erro de domínio | Guarda no banco |
|---|---|---|---|
| RN-01 | cinco passos, nomeados e ordenados; não se cria, exclui ou reordena | `PassoInvalido("ordem_canonica")` | `pk_foco_passo (ciclo_id, tipo)` + `ck ordem between 1 and 5` |
| RN-02 | no máximo um ciclo aberto por análise | `CicloInvalido` | índice parcial único `uq_foco_ciclo_aberto_por_analise` |
| RN-03 | no máximo uma restrição vigente por ciclo | `RestricaoInvalida` | `pk_foco_restricao (ciclo_id)` |
| RN-04 | reabrir não apaga: decisão anterior permanece, reabertura é fato novo | — (append em `decisoes`/`reaberturas`) | linhas com `ordem`, nunca `UPDATE` destrutivo |
| RN-05 | veredito de herança exige justificativa e autor | `HerancaInvalida` | `ck veredito_exige_justificativa_e_autor` |
| RN-06 | vínculo fora do canônico exige justificativa | `VinculoInvalido` | `ck nao_canonico_exige_justificativa` |
| RN-07 | ciclo fechado é imutável | `CicloInvalido` | — (invariante de domínio; o retrato prova) |
| — | concluir `subordinar` com herança pendente é recusado | `HerancaInvalida` | — |

A prova do RN-04 não é uma asserção sobre contagem: `CicloDeFocalizacao.retrato()` produz
o **conteúdo** que as pessoas escreveram, e o teste compara o retrato do ciclo fechado
antes e depois do recomeço.

## Persistência (nove tabelas `foco_*`)

`foco_analise` (1:1 com `projeto`) · `foco_ciclo` · `foco_restricao` · `foco_passo` ·
`foco_decisao` · `foco_nota` · `foco_reabertura` · `foco_vinculo` · `foco_heranca`.

Toda tabela com `projeto_id` participa do filtro de inquilino do M1; a escrita passa por
`salvar_focalizacao`, que condiciona o `UPDATE` de `projeto` à `versao_lida` e chama
`confirmar_gravacao()` — sem isso, o portão `scripts/check-trava-otimista.sh` reprova.

## O que NÃO é modelo de domínio

- **A sugestão de restrição** (`toc.suggest_constraint`) não é entidade: é uma leitura das
  causas raiz da ARA vinculada, que devolve candidatas e um `action_id`. A rota não
  escreve; quem escreve é a confirmação da proposta.
- **O estado do projeto vinculado** (ativo, arquivado, inexistente) não vive no vínculo:
  ele é resolvido na camada de aplicação, contra os repositórios dos outros módulos. Guardá-lo
  aqui seria cache de dado alheio, e envelheceria em silêncio.
