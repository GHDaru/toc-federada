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
../../scripts/check-raiz-do-agregado.sh   # operação só pela raiz do agregado (DDD)

# subir o serviço (é uma FÁBRICA, por isso `--factory`; sem ele o uvicorn procura um
# objeto `app` de módulo, que não existe aqui):
uv run uvicorn --factory toc_api.http.app:criar_app --port 8000
```

Resposta de `GET /saude` com o serviço no ar e a cadeia acima exportada, colada da
execução (a cadeia sai **redigida** — P7):

```json
{"servico":"toc-api","ambiente":"desenvolvimento","persistencia":"postgres",
 "banco":"postgresql+psycopg://***@/toc_federada?host=/var/run/postgresql&port=5433",
 "traco":"RastreadorNulo","geracao":"local-deterministico",
 "identidade":"ProvedorDeIdentidadeFalso","admissao":"ausente (desenvolvimento)","app_id":null}
```

### O que `DATABASE_URL` decide, e o que ela NÃO decide

Sem `DATABASE_URL`, a fábrica de persistência devolve o backend em memória — isso é do
serviço, e continua valendo:

```text
$ env -u DATABASE_URL uv run python -c "..."   # Configuracao.do_ambiente + criar_persistencia
backend = memoria | motor = None | repositorio = RepositorioDeProjetosEmMemoria
```

**A suíte de integração não segue essa escolha, e este parágrafo já afirmou que seguia.**
Ela tem cadeia própria: `tests/integracao/conftest.py` define `URL_PADRAO` com o cluster
local de desenvolvimento e usa `DATABASE_URL` só como sobreposição. Quem decide se ela roda
é o **banco responder**, não a variável existir:

```text
$ env -u DATABASE_URL uv run pytest -m integracao -q
40 passed, 786 deselected, 2 warnings in 35.29s

$ DATABASE_URL='postgresql+psycopg://toc@/toc_federada?host=/var/run/postgresql&port=59999' \
    uv run pytest -m integracao -q -rs
SKIPPED [1] tests/integracao/test_nuvem_no_postgres.py:232: PostgreSQL indisponível em
postgresql+psycopg://toc@/toc_federada?host=/var/run/postgresql&port=59999: ...
40 skipped, 786 deselected, 2 warnings in 1.38s
```

O que continua verdade, e é o que importa: a suíte de integração é **pulada com o motivo**
quando o PostgreSQL não responde — nunca substituída por SQLite. Um teste de integração
que cai em SQLite não integrou nada.

## Variáveis de ambiente

| Variável | Efeito | Padrão |
|---|---|---|
| `DATABASE_URL` | Backend do SERVIÇO: presente → PostgreSQL; ausente → memória. Não decide se a suíte de integração roda — veja acima | ausente |
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
| `0003` | marcador de UDE, ficha, parecer, exame de elo e conector E | 005 — `data-model.md` |
| `0004` | proposta de ação governada e traço de execução | 006 — `data-model.md` |
| `0005` | racional da nuvem, costura de origem, premissas e injeções | 007 — `data-model.md` |

São cinco e não uma porque são de cinco ciclos com specs próprias — cada spec declara o
conteúdo exato da sua revisão. A cadeia, lida do próprio Alembic (`uv run alembic history`,
saída colada):

```text
0004 -> 0005 (head), 0005 — M3: Nuvem de Conflito (racional, costura de origem, premissas e injeções).
0003 -> 0004, 0004 — M7: proposta de ação governada e traço de execução (spec 006).
0002 -> 0003, 0003 — M2: marcador de Efeito Indesejável (UDE), ficha, parecer, exame de elo e conector E.
0001 -> 0002, 0002 — núcleo M1: dono por (inquilino, usuário), nó e aresta causal.
<base> -> 0001, 0001 — esqueleto: referência de inquilino e o agregado projeto.
```

As regras RN-02 (sem auto-laço) e RN-03 (par origem→destino único) são impostas **pelo
banco**, não só pelo domínio.

Toda migração tem `downgrade` com corpo de verdade, e há portão para isso:
`tests/contrato/test_migracoes.py` mede a cadeia, e
`tests/integracao/test_migracao_e_isolamento.py` sobe e desce contra o banco real.

## Operação só pela raiz do agregado — e por que há duas famílias de rota

As ferramentas da TOC são **raízes de agregado por composição**: `ProjetoARA` (M2) e
`NuvemDeConflito` (M3) **contêm** um `Projeto` do M1 e acrescentam invariantes que o
núcleo não conhece — as 5 entidades e 7 arestas que nascem juntas e não se destroem
(RN-01), o exame de suficiência que nasce com todo elo, a ficha arquivada quando um UDE
some, o conector E que nunca fica com referência órfã.

O `Projeto` que elas contêm é **a mesma linha de banco** que `/toc/projetos` abre. Enquanto
ele aceitava mutação de quem o carregasse cru, havia duas portas para o mesmo estado e as
invariantes moravam numa só: criar uma nuvem e apagar a aresta D↯D′ por
`DELETE /toc/projetos/{id}/arestas/{id}` respondia `204 No Content`, e a nuvem sumia da
leitura em seguida — `404` sobre um projeto que continuava no banco.

O conserto não é um `if` na rota. `Projeto._exigir_raiz` recusa **toda** mutação de grafo
de um projeto cuja `ferramenta` não é a genérica, e a única maneira de destravá-la é o
`Projeto.sob_a_raiz()` que a raiz usa por dentro. Consequências:

| Projeto | Rotas de grafo | Fora delas |
|---|---|---|
| `generico` | `/toc/projetos/{id}/nos` e `/arestas` (o `Projeto` **é** a raiz) | — |
| `ara` | `/toc/ara/projetos/{id}/efeitos`, `/nos/{id}`, `/arestas`, `/arestas/{id}` | `409 AGGREGATE_ROOT_REQUIRED` |
| `nc` | nenhuma: a topologia é fixa e não se cria nem se destrói (RF-03) | `409 AGGREGATE_ROOT_REQUIRED` |

Ciclo de vida do projeto (excluir suave, restaurar, lixeira, leitura) continua pela rota
genérica para as três: a trava é sobre o **grafo**, não sobre o projeto.

Fail-closed é literal: uma ferramenta nova nasce **bloqueada** mesmo sem se registrar em
`RAIZ_POR_FERRAMENTA` — a tabela só empresta o nome da raiz à mensagem de recusa. O portão
é `../../scripts/check-raiz-do-agregado.sh`, que confere que a chave `sob_a_raiz` não sai
de `dominio/`, que as oito mutações de grafo têm guarda, e que cada raiz se registra.

## Não existe tabela de usuário — e a ausência é decisão

`specs/003-esqueleto-federado/data-model.md` diz, com todas as letras: "Usuário e senha:
não existem. Identidade é da fundação, por introspecção; persistir credencial criaria o
login próprio que o P2 proíbe". O que isola é o objeto de valor
`DonoDoProjeto(inquilino_id, usuario_id)`, que vem da introspecção e vira as colunas
`projeto.tenant_id` e `projeto.usuario_id`.
