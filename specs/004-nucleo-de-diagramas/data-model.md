# Data model 004 — Núcleo de Diagramas Lógicos (esboço do ciclo 001)

> Siglas: DDD — Domain-Driven Design (Design Orientado a Domínio) · TOC — Teoria das
> Restrições · UUID — Universally Unique Identifier (identificador único universal) ·
> JSON — JavaScript Object Notation · FSM — máquina de estados finitos · ADR —
> Architecture Decision Record (Registro de Decisão Arquitetural)

- **Estado**: esboço escrito no ciclo 001, consolidado na abertura do ciclo 004 — os
  testes de domínio (que nascem primeiro, P4) são a forma final; divergência entre este
  documento e o teste se resolve a favor do teste e volta aqui como correção.
- **Origem**: `spec.md` § Entidades e modelo de domínio · linhagem
  `tocbuilderv3/types.ts:9-65` (formas herdadas, citadas na spec F-01–F-03).

## Agregado: Projeto

Raiz de consistência. Toda mutação de nó ou aresta entra pelo agregado, que valida as
invariantes antes de emitir evento.

| Atributo | Tipo | Regra |
|---|---|---|
| `id` | UUID | imutável, gerado no servidor |
| `dono` | DonoDoProjeto | imutável após criação |
| `tipo_de_ferramenta` | enum extensível (`generico` no M1) | imutável após criação; M2–M5 estendem |
| `nome` | texto 1..200 | obrigatório |
| `descricao_do_problema` | texto 0..4000 | opcional |
| `estado` | `ativo` \| `excluido` | transições: ativo→excluido (suave), excluido→ativo (restauração) |
| `excluido_em` | instante \| nulo | preenchido só no estado `excluido` |
| `versao` | inteiro | bloqueio otimista (Clarify 2 da spec) |
| `criado_em` / `alterado_em` | instante | do relógio-porta, nunca `datetime.now()` no domínio |
| `nos` | coleção de Nó | interna ao agregado |
| `arestas` | coleção de ArestaCausal | interna ao agregado |

## Entidades internas

**Nó**

| Atributo | Tipo | Regra |
|---|---|---|
| `id` | UUID | único no projeto |
| `tipo` | enum extensível (`generico` no M1) | RN-04: sem semântica TOC aqui |
| `titulo` | texto 1..200 | obrigatório |
| `descricao` | texto 0..4000 | opcional |
| `posicao` | PosicaoNoCanvas | sempre presente (atribuída se criado pela tabela) |
| `recolhido` | booleano | padrão falso |

**ArestaCausal** — dirigida; lê-se "Se origem, então destino" (RN-01).

| Atributo | Tipo | Regra |
|---|---|---|
| `id` | UUID | único no projeto |
| `origem` / `destino` | id de Nó | ambos existentes no projeto; `origem ≠ destino` (RN-02) |
| `rotulo` | texto 0..200 | opcional |

Par (origem, destino) é único no projeto (RN-03); (destino, origem) é permitido — laço
de reforço é análise de M2, não proibição do núcleo.

## Objetos de valor

- **DonoDoProjeto** — `(inquilino_id, usuario_id)`, ambos vindos da introspecção
  (INT-01). Imutável; a igualdade é por valor. É a chave do isolamento (RNF-03).
- **PosicaoNoCanvas** — `(x: decimal, y: decimal)`. Imutável; mover cria valor novo.

## Eventos de domínio (somente-acréscimo)

`ProjetoCriado` · `MetadadosEditados` · `NoAdicionado` · `NoEditado` · `NoMovido` ·
`NoRecolhido` · `NoExcluido` (carrega o raio: ids das arestas removidas em cascata) ·
`ArestaLigada` · `ArestaEditada` · `ArestaExcluida` · `ProjetoExcluido` (suave) ·
`ProjetoRestaurado` · `ProjetoImportado` (carrega o mapeamento de ids) ·
`MutacaoCompensada` (o evento compensatório de desfazer/reverter, com `compensa_evento_id`
correlacionado — nunca se apaga o evento original).

Todo evento carrega: `evento_id`, `projeto_id`, `dono`, `instante`, `tipo_de_acao` (a
chave da política do RF-21) e o identificador de correlação do traço (RNF-01).

## Invariantes (cada uma nasce como teste de domínio que falha primeiro)

1. Aresta só referencia nós existentes do próprio projeto (RF-20).
2. Sem auto-laço (RN-02); sem par (origem, destino) duplicado (RN-03).
3. Excluir nó remove exatamente o nó e suas arestas incidentes, nada mais — o teste
   que teria pego o filtro invertido da linhagem (spec F-06, RF-16).
4. Projeto `excluido` recusa toda mutação exceto restauração e exclusão definitiva
   (RF-10).
5. Restauração devolve o conteúdo idêntico ao momento da exclusão (RF-08).
6. Importação valida tudo antes de criar qualquer coisa; falhou, nada existe (RF-33/34).

## O que NÃO é modelo de domínio

- **Pilha de desfazer** — estado de sessão da interface (spec F-13); o domínio só conhece
  a mutação inversa que ela dispara e o evento compensatório que resulta.
- **FSM de proposta** — uma só e do servidor, definida no ciclo 006 (item 8 do P2); o M1
  só declara `tipo_de_acao` em cada evento para a política encaixar.
- **Tabelas físicas e índices** — decisão do adaptador (Alembic, ciclo 004 com a junta
  do 003); este documento é domínio, não esquema de banco.
