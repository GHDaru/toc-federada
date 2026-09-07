# Contrato REST 010 — Estratégia & Táticas (M5)

> Siglas, uma vez neste documento: **TOC** — Teoria das Restrições · **S&T** — Estratégia &
> Táticas (*Strategy & Tactics*) · **M1** — Núcleo de Diagramas Lógicos · **M5** — o módulo
> Estratégia & Táticas · **REST** — *Representational State Transfer* · **HTTP** —
> *HyperText Transfer Protocol* · **UUID** — *Universally Unique Identifier* · **JSON** —
> *JavaScript Object Notation* · **APH** — Aplicação ↔ Harness · **IA** — inteligência
> artificial · **RF/RN/RNF/RI** — requisito funcional / regra de negócio / requisito não
> funcional / requisito de interface · **ADR** — *Architecture Decision Record*.

- **Prefixo**: `/toc/snt` — 11 caminhos, 13 pares verbo + caminho · **implementação**:
  [`../../../apps/api/src/toc_api/http/roteadores/snt.py`](../../../apps/api/src/toc_api/http/roteadores/snt.py)
  · **esquemas**: [`../../../apps/api/src/toc_api/http/esquemas.py`](../../../apps/api/src/toc_api/http/esquemas.py)
- **Contrato executável**: [`../../../apps/api/tests/contrato/test_http_snt.py`](../../../apps/api/tests/contrato/test_http_snt.py)
  valida cada resposta contra o OpenAPI da própria aplicação. Divergência entre este
  documento e o teste se resolve a favor do teste.
- **Autorização**: `fail-closed`, fora do modelo de linguagem (P2). A política vive em
  [`../../../apps/api/src/toc_api/aplicacao/governanca.py`](../../../apps/api/src/toc_api/aplicacao/governanca.py):
  4 casos de uso de leitura sob `TOC_LEITURA`, 8 de escrita sob `TOC_ESCRITA`.
- **Isolamento**: todo recurso é filtrado pelo dono `(inquilino_id, usuario_id)` vindo da
  introspecção (INT-01). Projeto de outro inquilino responde `404`, nunca `403` — a
  existência não vaza.

## A cláusula que governa este contrato inteiro (RF-06)

**Nenhum esquema de entrada tem campo de número de passo.** Não é disciplina de quem
escreve: é medido no OpenAPI publicado por
`test_nenhuma_rota_de_escrita_do_m5_declara_campo_de_numero`, que percorre os esquemas de
`POST`/`PUT`/`PATCH` do prefixo e exige zero campos cujo nome contenha "numero" ou "step".

O contraexemplo é a quarta geração da linhagem
(`tocbuilderv3/components/SnTStepEditorModal.tsx:56-57`), onde o número era obrigatório,
texto livre, sem validação de formato nem de unicidade. Nos esquemas de **saída** o número
aparece sempre — ele é calculado da estrutura a cada leitura (RN-01).

## A árvore

| Verbo | Caminho | Requisito | Resposta |
|---|---|---|---|
| `POST` | `/projetos` | RF-01 | `201` `SnTOut` — meta global **obrigatória**; sem ela, `422 INVALID_ARGUMENT` |
| `GET` | `/projetos/{projeto_id}` | RF-05 | `200` `SnTOut` — passos em ordem estrutural, cada um com `numero`, `nivel`, `pai_id` e `filhos` |
| `PUT` | `/projetos/{projeto_id}/meta-global` | RF-02 | `200` `SnTOut` — evento próprio `MetaGlobalEditada` |

## Os passos

| Verbo | Caminho | Requisito | Resposta |
|---|---|---|---|
| `POST` | `/projetos/{projeto_id}/passos` | RF-04 | `201` `PassoDaSnTOut` — corpo com `estrategia`, `tatica`, `pai_id`, `posicao`, `categoria` e as três premissas. **Sem campo de número** |
| `GET` | `/projetos/{projeto_id}/passos/{no_id}` | RF-13 | `200` `FichaDoPassoOut` — o passo mais as **três leituras dirigidas**, montadas no servidor |
| `PATCH` | `/projetos/{projeto_id}/passos/{no_id}` | RF-11 | `200` `FichaDoPassoOut` — estratégia, tática e categoria |
| `PUT` | `/projetos/{projeto_id}/passos/{no_id}/premissas` | RF-12 | `200` `FichaDoPassoOut` — grava sempre; ausência é pendência, nunca trava (RN-06) |
| `PUT` | `/projetos/{projeto_id}/passos/{no_id}/posicao` | RF-08 | `200` `SnTOut` — move a subárvore inteira; a resposta é a árvore **já renumerada** |
| `DELETE` | `/projetos/{projeto_id}/passos/{no_id}` | RF-09, RN-05 | `200` `SnTOut` — remove a subárvore exata e devolve a árvore renumerada |
| `PUT` | `/projetos/{projeto_id}/passos/{no_id}/status` | RF-16, RN-03 | `200` `FichaDoPassoOut` — corpo com **um campo só**: `status` |

### Por que a exclusão devolve `200` e não `204`

Quem exclui uma subárvore precisa ver a renumeração que sobrou. Um `204 No Content`
obrigaria a interface a um segundo pedido para descobrir o que mudou — e o intervalo entre
os dois é onde a tela mostra números velhos.

### Por que o corpo do status tem um campo só

O autor da mudança vem do **principal da introspecção**, nunca do corpo (RN-03). O caso de
uso `MudarStatusDoPassoDaSnT` não tem parâmetro `autor`, e um teste confere a assinatura. Na
quarta geração da linhagem, status não registrava autoria nenhuma.

## As prévias — **leitura**, e por isso um principal só-leitura as alcança

| Verbo | Caminho | Requisito | Resposta |
|---|---|---|---|
| `POST` | `/projetos/{projeto_id}/previas-de-mover` | RI-05 | `200` `PreviaDeMoverOut` — a lista de `(no_id, numero_atual, numero_novo)`. **Nada muta** |
| `GET` | `/projetos/{projeto_id}/passos/{no_id}/previa-de-exclusao` | RI-06, RF-09 | `200` `PreviaDeExclusaoOut` — `passos` (a contagem) e o `primeiro_nivel` do que cai |

`POST` na prévia de mover não é contradição: o pedido tem corpo (alvo, destino, posição), e
um `GET` com três parâmetros de consulta seria pior de ler e mais fácil de cachear errado. O
que decide a classificação é a **política**, não o verbo: `PreverRenumeracao` está sob
`TOC_LEITURA` porque não grava evento nenhum.

## As vistas

| Verbo | Caminho | Requisito | Resposta |
|---|---|---|---|
| `GET` | `/projetos/{projeto_id}/acompanhamento` | RF-17 | `200` `AcompanhamentoOut` — `passos`, `por_status`, `progresso` e as pendências com `no_id`, `numero` e `tipo` |
| `GET` | `/projetos/{projeto_id}/tabela` | RF-19 | `200` `TabelaDaSnTOut` — linhas indentadas por `nivel`, em ordem estrutural fixa |
| `GET` | `/projetos/{projeto_id}/exportacao` | RF-21 | `200` documento `toc.snt/1` — **sem número nenhum** |

## Recusas, por código estável (§A.7 do Anexo A)

| Código | HTTP | Quando | `details` |
|---|---|---|---|
| `INVALID_SNT_STEP` | `409` | passo inexistente nesta árvore, ou pai indicado que não é passo dela | `regra`: `sem_ficha` · `pai_inexistente` |
| `INVALID_MOVE` | `409` | mover para dentro da própria subárvore, ou destino inexistente | `motivo`: `para_a_propria_subarvore` · `destino_inexistente` |
| `INVALID_TRANSITION` | `409` | mudar para o status que já está, ou sem autor | `motivo`: `sem_mudanca` · `autor_obrigatorio` |
| `INVALID_ARGUMENT` | `422` | meta global vazia, estratégia vazia, posição fora da faixa de irmãos, status ou categoria fora do vocabulário | — |
| `AGGREGATE_ROOT_REQUIRED` | `409` | tentar mexer no grafo da S&T pela rota genérica do M1 | `ferramenta`, `raiz` |
| `VERSION_CONFLICT` | `409` | duas escritas da mesma versão lida (ADR 0010) | `versao_lida`, `versao_atual` |
| `NOT_FOUND` | `404` | projeto de outro inquilino, inexistente, ou que não é uma S&T | — |
| `FORBIDDEN` | `403` | principal sem `toc:write` numa rota de escrita | — |

`INVALID_SNT_STEP` é separado de `INVALID_STEP` (o passo da Árvore de Transição) porque a
**correção do cliente é outra**, que é o critério do §A.7 para código próprio.

## O que este contrato NÃO tem, e a ausência é declarada

**Nenhuma ação de catálogo `toc.*`** nasce neste módulo (INT-04 da spec 010): o round 010
não inclui assistência de IA para a S&T, e por isso não existe
`contracts/acoes-catalogo.md` neste ciclo — ao contrário dos ciclos 006, 007, 008 e 009. A
ausência é decisão declarada, não esquecimento, e um teste a mede:
`test_nenhuma_acao_do_catalogo_pertence_a_snt`.

O que existe do lado da fronteira APH são as **quatro telas** no registro
(`toc.snt_arvore`, `toc.snt_passo`, `toc.snt_tabela`, `toc.snt_acompanhamento`), com
`ai_visible` campo a campo: número, contagens, status e categoria são visíveis; meta global,
estratégia, tática e as três premissas **não são** — texto de usuário é sempre camada
não-confiável (INT-02, item 7 da constituição).
