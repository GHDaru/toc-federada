# `toc-api` — o serviço

Esqueleto do serviço da **toc-federada**: as quatro camadas, o banco real, as migrações e
o traço. As ferramentas dos Processos de Pensamento da Teoria das Restrições (TOC) entram
por cima disto, ciclo a ciclo.

> Siglas usadas aqui: **TOC** — Teoria das Restrições · **DDD** — *Domain-Driven Design*
> (Design Orientado a Domínio) · **TDD** — *Test-Driven Development* (desenvolvimento
> guiado por teste) · **OTel** — OpenTelemetry · **M1** — Núcleo de Diagramas Lógicos
> (o módulo, em `../../docs/produto/modulos.md`) · **RN** — regra de negócio.

## As camadas (P3 — DDD + hexagonal)

```
src/toc_api/
  dominio/     PURO — entidades, objetos de valor, regras e PORTAS (typing.Protocol)
  aplicacao/   PURO — casos de uso; fala com portas, nunca com adaptador
  infra/       borda — SQLAlchemy, Alembic, OTel, configuração, relógio
  http/        borda — FastAPI e a composição das quatro camadas
  alembic/     migrações
tests/
  dominio/     sem banco, sem rede
  aplicacao/   com duplos das portas
  integracao/  com o PostgreSQL REAL
  contrato/    portas e cadeia de migrações medidas como dado
```

Quem impõe isso não é a boa vontade: são os três contratos `import-linter` do
[`pyproject.toml`](pyproject.toml), rodados pelo portão
[`../../scripts/check-arquitetura.sh`](../../scripts/check-arquitetura.sh).

## Montar e rodar

```bash
cd apps/api
uv sync

export DATABASE_URL='postgresql+psycopg://toc@/toc_federada?host=/var/run/postgresql&port=5433'
uv run alembic upgrade head          # migração de verdade; nunca create_all
uv run pytest                        # inclui a suíte de integração
../../scripts/check-arquitetura.sh   # os contratos de arquitetura
```

Sem `DATABASE_URL`, a fábrica de persistência devolve o backend em memória e a suíte de
integração é **pulada com o motivo** — nunca substituída por SQLite: um teste de
integração que cai em SQLite não integrou nada.

## Variáveis de ambiente

| Variável | Efeito | Padrão |
|---|---|---|
| `DATABASE_URL` | Presente → PostgreSQL; ausente → memória | ausente |
| `TOC_DB_SCHEMA` | Esquema do banco (a suíte de integração usa um descartável por teste) | `public` |
| `OTEL_LIGADO` | Liga o traço de verdade; desligado usa o rastreador nulo | desligado |
| `OTEL_SERVICE_NAME` | `service.name` do recurso OTel | `toc-api` |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | Destino do exportador | ausente |
| `TOC_AMBIENTE` | `deployment.environment` do recurso OTel | `desenvolvimento` |

Nenhuma delas tem valor no repositório, e a razão é o P7: cadeia de conexão carrega
credencial. `/saude` devolve a cadeia **redigida**, nunca a original.

## Migrações

| Revisão | O que cria | Spec |
|---|---|---|
| `0001` | `tenant_ref`, `projeto` (com `apagado_em` já presente) | 003 — `data-model.md` |
| `0002` | `projeto.usuario_id`/`descricao_do_problema`/`versao`, `no`, `aresta_causal` | 004 — `data-model.md` |

São duas e não uma porque são de dois ciclos com specs próprias — a spec 003 declara o
conteúdo exato da `0001` e termina dizendo o que o ciclo 004 acrescenta. As regras RN-02
(sem auto-laço) e RN-03 (par origem→destino único) são impostas **pelo banco**, não só
pelo domínio.

Toda migração tem `downgrade` com corpo de verdade, e há portão para isso:
`tests/contrato/test_migracoes.py` mede a cadeia, e
`tests/integracao/test_migracao_e_isolamento.py` sobe e desce contra o banco real.

## Não existe tabela de usuário — e a ausência é decisão

`specs/003-esqueleto-federado/data-model.md` diz, com todas as letras: "Usuário e senha:
não existem. Identidade é da fundação, por introspecção; persistir credencial criaria o
login próprio que o P2 proíbe". O que isola é o objeto de valor
`DonoDoProjeto(inquilino_id, usuario_id)`, que vem da introspecção e vira as colunas
`projeto.tenant_id` e `projeto.usuario_id`.
