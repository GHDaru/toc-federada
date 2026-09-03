# Contracts 004 — recursos REST do Núcleo de Diagramas (esboço do ciclo 001)

> Siglas: REST — Representational State Transfer · API — Application Programming
> Interface (interface de programação) · JSON — JavaScript Object Notation · APH —
> Aplicação ↔ Harness · UUID — Universally Unique Identifier · TOC — Teoria das
> Restrições · OTel — OpenTelemetry

- **Estado**: esboço escrito no ciclo 001; vira OpenAPI gerado do código na abertura do
  ciclo 004 (o contrato executável é o schema servido pelo FastAPI + os testes de
  contrato — este arquivo fixa recurso, verbo e semântica, não o byte final).
- **Antecedente honesto**: a linhagem especificou 20 endpoints e implementou zero
  (`tocbuilderv3/api_specifications.md`, spec F-07). A diferença deste esboço é que ele
  entra num ciclo com TDD e DoD executável — contrato sem teste de contrato não fecha o
  ciclo.

## Convenções

- Prefixo `/api/toc`. Identificadores UUID. Datas em ISO 8601 UTC.
- **Identidade**: toda rota exige o token da fundação; o serviço o valida por
  `POST /auth/introspect` (junta do ciclo 003) e deriva `(inquilino, usuario,
  capacidades)`. Nenhuma rota de login própria existe (P2, item 2).
- **Autorização**: leitura exige `toc:read`; mutação exige `toc:write`; fail-closed
  (RNF-04). Recusa: `403` com corpo de erro tipado.
- **Isolamento**: toda consulta filtra por inquilino no repositório (RNF-03) — `404`
  para recurso de outro inquilino (não `403`, para não confirmar existência).
- **Traço**: toda mutação propaga o identificador de correlação OTel (RNF-01) e carrega
  `tipo_de_acao` para a política do RF-21.
- **Concorrência**: mutações enviam `versao` (bloqueio otimista); conflito responde
  `409` com a versão atual — pendente do Clarify 2 da spec.
- **Erros**: envelope único `{ "erro": { "codigo", "mensagem", "detalhes": [] } }` —
  nunca texto cru.

## Recursos

### Projetos

| Verbo e rota | Semântica | Sucesso | Requisitos |
|---|---|---|---|
| `POST /api/toc/projects` | criar projeto (nome, descrição, tipo) | `201` + projeto | RF-01 |
| `GET /api/toc/projects` | listar ativos do usuário, ordem por alteração | `200` + página | RF-02 |
| `GET /api/toc/projects/{id}` | abrir com nós e arestas | `200` + agregado | RF-03 |
| `PATCH /api/toc/projects/{id}` | editar metadados (nome, descrição) | `200` | RF-04 |
| `DELETE /api/toc/projects/{id}` | **exclusão suave** (estado `excluido`) | `200` + estado | RF-06 |
| `GET /api/toc/projects/trash` | listar a lixeira do usuário | `200` + página | RF-07 |
| `POST /api/toc/projects/{id}/restore` | restaurar da lixeira | `200` + projeto | RF-08 |
| `DELETE /api/toc/projects/{id}/permanent` | exclusão definitiva (só de projeto na lixeira; confirmação é da interface, a rota exige `confirm=nome-do-projeto` na query) | `204` | RF-09, RN-05 |

### Nós e arestas (sub-recursos do agregado)

| Verbo e rota | Semântica | Sucesso | Requisitos |
|---|---|---|---|
| `POST /api/toc/projects/{id}/nodes` | criar nó (título, descrição, posição opcional) | `201` + nó | RF-11, RF-29 |
| `PATCH /api/toc/projects/{id}/nodes/{nodeId}` | editar título/descrição/posição/recolhido | `200` + nó | RF-12–RF-14 |
| `DELETE /api/toc/projects/{id}/nodes/{nodeId}` | excluir nó **e** arestas incidentes; resposta relata o raio | `200` + `{ "arestas_removidas": [] }` | RF-15, RF-16 |
| `POST /api/toc/projects/{id}/edges` | ligar origem→destino (valida existência, duplicata, auto-laço) | `201` + aresta | RF-17, RF-18, RF-20 |
| `PATCH /api/toc/projects/{id}/edges/{edgeId}` | editar rótulo | `200` + aresta | RF-19 |
| `DELETE /api/toc/projects/{id}/edges/{edgeId}` | excluir aresta | `204` | RF-19 |

Não há `PUT` de estado inteiro do projeto: o "salvar tudo por cima" da linhagem
(`mockApiService.ts:286-301`, `saveProjectState`) é o que tornava toda escrita uma
substituição cega — cada mutação aqui é um comando nomeado do agregado, com evento e
traço próprios.

### Histórico e reversão

| Verbo e rota | Semântica | Sucesso | Requisitos |
|---|---|---|---|
| `GET /api/toc/projects/{id}/events` | eventos do projeto, somente-acréscimo, paginado | `200` + página | RF-25, RF-26 |
| `POST /api/toc/projects/{id}/revert` | reverter campo para valor anterior — mutação nova com `MutacaoCompensada` correlacionado | `200` | RF-23, RF-25 |

O desfazer de sessão **não tem rota própria**: a interface dispara a operação inversa
pelos mesmos comandos acima, com `compensa_evento_id` no corpo — uma máquina de estados
só, do servidor (item 8 do P2).

### Exportação e importação

| Verbo e rota | Semântica | Sucesso | Requisitos |
|---|---|---|---|
| `GET /api/toc/projects/{id}/export` | JSON canônico com `schema_version`, determinístico | `200` + arquivo | RF-32 |
| `POST /api/toc/projects/import` | valida tudo; cria projeto **novo** com mapeamento; nada muta | `201` + `{ "projeto", "relato" }` | RF-33–RF-35 |
| — | validação falhou | `422` + relato por item | RF-34 |

## O que este esboço NÃO fixa

- Formato binário/byte final dos corpos (OpenAPI gerado do código decide).
- Paginação exata (limite/cursor) — decisão do ciclo 004, registrada no próprio código.
- Rotas do catálogo `toc.*` e de proposta/confirmação — ciclo 006, spec própria
  (`specs/006-acoes-governadas-e-snapshot/`).
