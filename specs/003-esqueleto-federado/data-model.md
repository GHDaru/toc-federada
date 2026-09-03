# Modelo de dados mínimo — ciclo 003

> Siglas: **TOC** — Teoria das Restrições · **ADR** — Architecture Decision Record
> (Registro de Decisão Arquitetural) · **TTL** — Time To Live (tempo de vida).
>
> Artefato condicional `ART:data-model=yes` do [`plan.md`](plan.md). Este é o modelo do
> **esqueleto**: o suficiente para provar identidade, isolamento e migração reversível.
> O domínio TOC (nó, aresta causal, Efeito Indesejável) nasce no ciclo 004
> ([`../004-nucleo-de-diagramas/spec.md`](../004-nucleo-de-diagramas/spec.md)) — nada
> dele é antecipado aqui (estoque é desperdício).

## O que NÃO é persistido — e por quê vem primeiro

- **Usuário e senha**: não existem. Identidade é da fundação, por introspecção
  (ADR 0003); persistir credencial criaria o login próprio que o P2 proíbe.
- **Grant e credencial**: o grant é trocado e descartado (uso único, TTL ≤ 120 s); a
  credencial da aplicação vive em variável de ambiente (P7). Nenhum dos dois toca o
  banco, o log ou o traço.
- **Principal**: objeto de valor **em memória**, com validade curta (`expires_at`).
  Persisti-lo seria cache de autorização — a autorização é sempre da resposta mais
  recente da introspecção.

## Entidades persistidas

### `tenant_ref` — referência de tenant

Espelho mínimo do tenant do hospedeiro; existe para chave estrangeira e diagnóstico,
nunca como fonte de verdade.

| Coluna | Tipo | Regra |
|---|---|---|
| `tenant_id` | text, chave primária | O identificador do hospedeiro, opaco para nós |
| `nome_exibicao` | text, nulo | Último `tenant.name` visto no handshake — **exibição**, nunca autorização |
| `visto_em` | timestamptz | Atualizado a cada embarque |

### `projeto` — o agregado mínimo

| Coluna | Tipo | Regra |
|---|---|---|
| `id` | uuid, chave primária | Gerado pela aplicação |
| `tenant_id` | text, não nulo, FK → `tenant_ref` | Invariante: nasce com tenant e nunca muda |
| `nome` | text, não nulo | Sintético neste ciclo (ADR 0006 — ex.: "Instituição Horizonte — ARA da evasão") |
| `ferramenta` | text, não nulo | Vocabulário fechado futuro (`ara`, `nc`, `arf`, `apr`, `at`, `set`); neste ciclo, dado de fixture |
| `criado_em` | timestamptz, não nulo | — |
| `atualizado_em` | timestamptz, não nulo | — |
| `apagado_em` | timestamptz, nulo | Soft delete nasce no ciclo 004 (E1.1); a coluna existe desde a migração `0001` para o downgrade dela nunca precisar destruir dado |

## Invariantes (verificadas por teste, não por disciplina)

1. **Nenhuma leitura sem tenant**: todo método de repositório exige `tenant_id`; o teste
   de isolamento consulta com dois principais e prova interseção vazia (RF-31, DoD 9).
2. **Nenhuma escrita vinda do hospedeiro** neste ciclo (RN-01): o repositório de
   projetos expõe leitura; a única escrita é o seed sintético da migração/fixture.
3. **Migração reversível**: `0001` cria `tenant_ref` e `projeto` com `upgrade` e
   `downgrade`; o downgrade num banco limpo não deixa resíduo (RF-29, DoD 8).

## O que o ciclo 004 muda (declarado para não parecer esquecimento)

`projeto` ganha os filhos do M1 (`no`, `aresta_causal`), o soft delete passa a operar, e
o primeiro evento de domínio (`ProjetoCriado`) nasce com a primeira escrita — cada um
com sua migração própria e reversível.
