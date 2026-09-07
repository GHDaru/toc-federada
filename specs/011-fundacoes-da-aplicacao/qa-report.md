# QA Report 011 — Fundações da aplicação

> Siglas: **QA** — Quality Assurance (garantia de qualidade) · **DoD** — Definition of Done
> (Definição de Pronto) · **ADR** — Architecture Decision Record (Registro de Decisão
> Arquitetural) · **RF/RI/RNF/RN/INT** — requisito funcional / de interface / não funcional
> / regra de negócio / integração · **i18n** — internacionalização · **APH** — Aplicação ↔
> Harness · **OTel** — OpenTelemetry · **CI** — integração contínua · **IA** — inteligência
> artificial · **RPO/RTO** — Recovery Point / Time Objective (objetivo de ponto / tempo de
> recuperação) · **DDL** — Data Definition Language (linguagem de definição de dados).

- **Data**: 2026-09-06 · **Raia**: plena · **Veredito**: **execução parcial — E8.3, E8.4,
  E1.4 e F8.1.3 entregues; a cauda e o gate humano continuam abertos**

**O que este lote executou, e o que ele deliberadamente não executou.** Entraram o portão
de internacionalização (E8.3), a documentação embutida com cobertura (E8.4), a exportação
e importação consolidadas com o adaptador do formato legado (E1.4) e o **ensaio de
restauração** (F8.1.3). **Não** entraram, e por isso as linhas correspondentes seguem com
`—`: a persistência da preferência de idioma no servidor (RF-13, DoD 6 — exige migração,
tabela e rota novas), a formatação localizada de data/número/colação (RF-16, DoD 7), a
jornada viva com captura nos dois idiomas (DoD 17) e a cauda inteira. Uma linha preenchida
com "parcialmente" seria pior que uma vazia: `—` é o estado honesto.

Toda célula abaixo foi preenchida **depois** do comando rodar, com a saída colada
(regra R1) e o tamanho examinado (regra R2). Um `✓` sem a saída é defeito, não evidência.

## Pré-condições de abertura (T-01)

> **Preenchida em 2026-09-06, no lote de fechamento documental.** Ela estava com seis `—`,
> o que é ambíguo: `—` pode significar "não verificado" ou "não cumprido". Abaixo está o que
> cada uma **é**, com a evidência — e cinco das seis **não foram cumpridas**. O ciclo foi
> executado assim mesmo, e isso é um fato do relatório, não uma nota de rodapé.

| Pré-condição | Verificado em | Evidência (saída colada) | Estado |
|---|---|---|---|
| Ciclo 008 promovido (as seis ferramentas existem — há o que documentar) | [`../008-arvores-de-futuro-e-implementacao/tasks.md`](../008-arvores-de-futuro-e-implementacao/tasks.md) e o `qa-report.md` de lá | o `TAIL:gate` do 008 **não está marcado** e o veredito dele é "— (o veredito só existe depois da cauda completa)" | ✗ **não cumprida**. O que a tornou dispensável na prática: a documentação embutida cobre as **ferramentas registradas pelo serviço**, e o portão mede isso — `ferramentas registradas pelo serviço: 7 (apr ara arf at focalizacao nc snt)`. O acoplamento foi ao registro, não à promoção |
| Os 5 `[DÚVIDA]` do Clarify respondidos no gate | [`spec.md`](spec.md), seção `## Clarify` | nenhuma resposta registrada em ADR nem em `docs/records/decisoes.jsonl` (`scripts/check-adrs-sucessao.sh` → `ADRs examinados: 14`, nenhum sobre idioma) | ✗ **não cumprida** — as cinco seguem abertas e são matéria do `TAIL:gate` |
| Idioma padrão decidido ([DÚVIDA] 1 — muda o RF-12) | `apps/web/src/i18n/index.tsx`, `apps/web/src/i18n/idioma-efetivo.test.ts` | a implementação **assumiu** a proposta da spec (português como língua-fonte, com a ordem preferência → embarque → língua-fonte), e os 10 testes de idioma efetivo provam a ordem: `Tests 10 passed (10)` | ◑ **assumida, não decidida**. Se o gate escolher "idioma do navegador", muda o RF-12 e o `idioma-efetivo` — o custo está localizado num módulo e nos seus 10 testes |
| Data de aposentadoria do formato legado decidida ([DÚVIDA] 2) | `apps/api/src/toc_api/dominio/legado.py` | nenhuma data no código nem em ADR; o adaptador é permanente por omissão | ✗ **não cumprida** — dívida com dono no gate (§ *Pendências*) |
| Teto de crescimento do pacote inicial fixado (RNF-09, spec L-04) | § *Medições registradas*, linha do RNF-09 | teto **não fixado**; o que foi medido é o crescimento real: **zero** no pacote inicial, porque cada verbete é pedaço próprio (`ara-*.js 5.34 kB` … contra `index-*.js 348.49 kB`) | ✗ **não cumprida**, com a mitigação medida ao lado |
| Plano do provedor permite restaurar para destino separado (spec L-01) — ou ADR da alternativa | [`../../scripts/ensaio-de-restauracao.sh`](../../scripts/ensaio-de-restauracao.sh) e § *Ensaio de restauração* | o ensaio rodou contra o **PostgreSQL local**, restaurando para um banco de destino separado: `37 tabelas, 71 linhas, 6 projetos lidos do destino` | ◑ **ensaiada localmente; não contra o provedor de produção** (Neon), que não existe ainda — o ciclo 003 não executou a metade operacional |

## DoD (as 18 linhas da spec — comando, saída colada, quanto examinou)

| # | Critério | Comando | Saída (colada) | Examinou | Código de saída |
|---|---|---|---|---|---|
| 1 | Domínio novo puro, testes sem rede | `pytest tests/dominio tests/aplicacao` + `scripts/check-arquitetura.sh` | `761 passed in 3.22s` · `Contracts: 3 kept, 0 broken.` | 761 testes puros; 3 contratos do `import-linter` | `0` |
| 2 | Zero literal órfão | `scripts/check-i18n.sh` | `✓ nenhuma cadeia visível fora do dicionário` | `arquivos .tsx varridos: 48` · `cadeias examinadas: 64 candidatas a literal solto` · `cadeias pelo dicionário: 656 chamadas a t()/tc()` | `0` |
| 3 | Paridade de dicionários `pt` × `en` | `scripts/check-i18n.sh` | `pendências de tradução (só em pt): 0` · `chaves órfãs (só em en): 0` · `traduções vazias: 0` | `chaves em pt (língua-fonte): 614` × `chaves em en (tradução): 614` | `0` |
| 4 | Chave ausente falha alto | `npx vitest run src/i18n/` + sabotagens do portão | `Tests 10 passed (10)` (idioma-efetivo) · sabotagens `chave-ausente-deixa-de-falhar-alto` e `a-chave-crua-volta-para-a-tela` → `saiu 1 pelo motivo declarado` | 10 testes + 2 sabotagens | `0` |
| 5 | Idioma efetivo pela ordem declarada | `npx vitest run src/i18n/idioma-efetivo.test.ts` | `Tests 10 passed (10)` — os três caminhos (preferência, embarque, língua-fonte) com o motivo verificado, mais a queda registrada | 3 caminhos + 5 casos de chave ausente | `0` |
| 6 | Preferência persiste no servidor | — | — (**não executado neste lote**: exige migração e rota novas — RF-13) | — | — |
| 7 | Formatação e colação localizadas | — | — (**não executado neste lote** — RF-16) | — | — |
| 8 | Cobertura ferramenta × verbete | `scripts/check-documentacao.sh` | `✓ cobertura completa: 7 de 7 ferramentas com verbete` | `ferramentas registradas pelo serviço: 7 (apr ara arf at focalizacao nc snt)` × `verbetes no acervo: 7` | `0` |
| 9 | Procedência dos verbetes resolve | `scripts/check-documentacao.sh` + `scripts/check-caminhos.sh` | `caminhos de procedência conferidos: 12` · `✓ todo caminho citado entre crases existe.` | 12 procedências; `caminhos conferidos: 1279` no repositório | `0` |
| 10 | Conversão do formato legado | `pytest tests/dominio/test_conversao_legado.py` | `26 passed` | 26 testes, incluindo assinatura de conteúdo, posição, recolhido e tipo `EI` → UDE pendente | `0` |
| 11 | Recusa campo a campo | `pytest tests/dominio/test_conversao_legado.py -k orfa` | `problemas: [('nodes[1].data.title', 'todo nó precisa de título'), ('edges[0].target', "aponta para o nó 'no-que-nao-existe', que não existe neste arquivo")]` | 2 problemas → 2 itens, `documento is None` | `0` |
| 12 | Histórico de conversa descartado e declarado | `pytest tests/dominio/test_conversao_legado.py -k historico` | `descarte declarado: chatHistory — 3 mensagem(ns)` | 3 mensagens contadas; `"chatHistory" not in json.dumps(documento)` | `0` |
| 13 | Ida e volta do formato consolidado | `pytest tests/integracao/test_portabilidade_no_postgres.py` | `8 passed` · `projetos no arquivo: 2 · vínculos: 1 · esqueletos iguais: True` | 8 testes contra o PostgreSQL real | `0` |
| 14 | Restauração ensaiada | `scripts/ensaio-de-restauracao.sh` | ver § *Ensaio de restauração* abaixo — saída inteira colada | 37 tabelas, 71 linhas, 6 projetos lidos do destino | `0` |
| 15 | Migração reversível sem resíduo | — | — (**este lote não criou migração**: nenhum requisito entregue aqui mudou esquema) | — | — |
| 16 | Sem segredo e sem dado real de pessoa | `grep -rniE "api[_-]?key\|secret" apps/web/src/ \| grep -viE "secretaria\|secreta" \| wc -l` + `scripts/check-vazamento.sh` | `0` · `✓ nenhum nome próprio em campo de pessoa…` | 19 ocorrências brutas, todas do português "secretaria"/"secreta"; 687 arquivos e 163 669 linhas varridos pelo portão | `0` |
| 17 | Jornada viva presente (dois idiomas) | — | — (**não executado neste lote** — P6, DoD 17) | — | — |
| 18 | Conformidade, caminhos e links | `scripts/evidencia.sh` | ver § *Evidência dos portões* | 12 portões executados | `0` |

## Portões nomeados do roadmap (ciclo 011)

| Portão | Como se verificou | Evidência colada |
|---|---|---|
| Nenhuma cadeia de interface fora do dicionário de i18n, com a contagem na saída (R2) | `scripts/check-i18n.sh` | `✓ i18n conforme: 48 arquivos, 64 cadeias examinadas (656 pelo dicionário), 614 chaves pt × 614 chaves en, 0 pendência, 0 órfã.` |
| Cada ferramenta com rota de documentação embutida respondendo | `scripts/check-documentacao.sh` + `npx vitest run src/documentacao/` | `✓ documentação conforme: 7 ferramentas registradas × 7 verbetes, 12 procedências conferidas, 1 âncoras casadas.` · `Tests 17 passed (17)` |
| Importar um export sintético da quarta geração cria o projeto **ou** recusa com relato campo a campo | `pytest tests/integracao/test_portabilidade_no_postgres.py` | `formato=legado descartes=[{'campo': 'chatHistory', 'motivo': '…', 'quantidade': 3}, …]` (aceito) e `código=IMPORT_REFUSED problemas=[{…}, {…}]` com `c.get("/toc/projetos").json() == []` (recusado) |

## Ensaio de restauração (RF-02, RF-03 — DoD 14)

> A saída vai colada aqui, **sem credencial** (RNF-10): variável de ambiente entra, valor
> não sai.

| Item | Declarado | Medido | Fonte |
|---|---|---|---|
| Instante alvo da restauração | o `now()` do banco de origem, tomado antes do despejo | `2026-09-06 22:28:01.023427Z` | saída do passo `[2/7]` |
| Destino separado usado | banco **novo**, criado no ato | `toc_ensaio_20260906222758` | saída do cabeçalho e do passo `[4/7]` |
| Duração até a aplicação responder | — | despejo `118 ms` + restauração `1099 ms` = `1221 ms`; aplicação de pé `1160 ms` depois | passos `[3/7]`, `[4/7]` e `[6/7]` |
| Objetivo de ponto de recuperação (RPO) | 5 minutos (proposta — depende do plano do provedor, lacuna L-01) | não medido: é política, e o ensaio local não o mede | `docs/integracao/restauracao.md` § Objetivos |
| Objetivo de tempo de recuperação (RTO) | 60 minutos (proposta) | piso medido de `1221 ms` para despejo→restauração com 71 linhas | mesma fonte |
| O que **não** voltou com o banco | arquivos em armazenamento compatível com S3, o escrito depois do instante alvo, índices e estatísticas (reconstruídos), sessões de embarque em curso | declarado, não medido — é a lista do relatório | passo `[7/7]` |
| Nenhum outro produto compartilha esta unidade | banco próprio (ADR 0002) | o ensaio restaurou num banco novo e a aplicação subiu contra **ele**: `/saude` responde `"banco":"postgresql+psycopg://***@/toc_ensaio_20260906222758…"` | passo `[6/7]` |

### Saída inteira do ensaio (colada — regra R1; sem credencial, RNF-10)

```text
$ export DATABASE_URL='postgresql+psycopg://toc@/toc_federada?host=/var/run/postgresql&port=5433'
$ scripts/ensaio-de-restauracao.sh
── Ensaio de restauração — unidade de restauração da aplicação (F8.1.3) ──
  banco de origem: toc_federada · esquema semeado: ensaio_20260906222758
  destino da restauração: toc_ensaio_20260906222758 (banco NOVO, criado agora)

[1/7] migrando e semeando a base sintética no esquema de origem…
/home/user/toc-federada/apps/api/.venv/lib/python3.11/site-packages/fastapi/testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
  from starlette.testclient import TestClient as TestClient  # noqa
  {"projetos_criados": 3, "projetos_listados": 6, "nomes": ["Dilema da expansão 1", "Dilema da expansão 2", "Dilema da expansão 3", "Horizonte — realidade atual 1", "Horizonte — realidade atual 2", "Horizonte — realidade atual 3"], "inquilino": "instituicao-horizonte", "token": "ensaio-facilitadora"}
[2/7] instante alvo da restauração (o ponto no tempo a que ela devolve): 2026-09-06 22:28:01.023427Z
[3/7] despejando o banco de origem…
  despejo: 420K em 118 ms
[4/7] restaurando em toc_ensaio_20260906222758…
  restauração: 1099 ms
[5/7] conferindo o conteúdo tabela a tabela…
  tabelas conferidas: 37 · linhas na origem: 71 · divergências de contagem: 0
  resumo md5 de projetos+nós — origem: 144beb7ec8ad29ddac8ae13321bef7b7
                              destino: 144beb7ec8ad29ddac8ae13321bef7b7
[6/7] subindo a aplicação contra o destino restaurado…
  de pé em 1160 ms · /saude: {"servico":"toc-api","ambiente":"teste","persistencia":"postgres","banco":"postgresql+psycopg://***@/toc_ensaio_20260906222758?host=/var/run/postgresql&port=5433","traco":"RastreadorNulo","geracao":"local-deterministico","identidade":"ProvedorDeIdentidadeFalso","admissao":"admitida","app_id":"toc"}
  projetos lidos do destino restaurado: 6
  ✓ a lista de projetos sintéticos aparece ÍNTEGRA (US-01)

[7/7] relatório do ensaio
  instante alvo (ponto de recuperação): 2026-09-06 22:28:01.023427Z
  despejo: 118 ms · restauração: 1099 ms
  duração medida do ciclo despejo→restauração: 1221 ms
  semeadura (preparo do ensaio, fora da conta acima): 2320 ms
  tamanho do despejo: 420K

  O QUE NÃO VOLTA COM O BANCO (declarado, não medido — RF-03):
    · arquivos em armazenamento compatível com S3 (anexos e capturas), que vivem
      fora do banco e têm apólice própria;
    · o que foi escrito DEPOIS do instante alvo — é o objetivo de ponto de
      recuperação em pessoa, e nenhuma restauração o inventa;
    · índices e estatísticas são RECONSTRUÍDOS pelo restore (não copiados): o
      primeiro acesso depois da restauração é mais lento até o `ANALYZE`;
    · sessões de embarque em curso (o grant é de uso único e TTL curto): quem
      estava dentro refaz o handshake.

  OBJETIVOS DECLARADOS (política do produto, a confirmar pelo Product Steward):
    · objetivo de ponto de recuperação (RPO): 5 minutos — o intervalo máximo de
      trabalho que se aceita perder;
    · objetivo de tempo de recuperação (RTO): 60 minutos — da decisão de restaurar
      até a aplicação de pé, com o ensaio acima como piso medido.

  UNIDADE DE RESTAURAÇÃO: esta aplicação tem banco PRÓPRIO (ADR 0002), e restaurá-la
  não rebobina nenhum outro produto da plataforma — foi por isso que o ensaio
  restaurou num banco NOVO e a aplicação subiu contra ELE, e não sobre a origem.

✓ restauração ensaiada: 37 tabelas, 71 linhas, resumo de conteúdo idêntico,
  e a aplicação de pé contra o destino restaurado lendo a base sintética íntegra.
$ echo $?
0
```

> A cadeia de conexão que a aplicação devolve em `/saude` sai **redigida**
> (`postgresql+psycopg://***@/…`) e a credencial de admissão do ensaio é sintética, vive
> dentro do processo e não aparece em nenhuma linha acima (P7, RNF-10).

## Medições registradas

| Métrica | Alvo | Valor medido | Fonte |
|---|---|---|---|
| Converter arquivo legado de 200 nós e 200 arestas — percentil 95 (RNF-08) | < 5 s | `p95 = 3.1 ms` na primeira execução e `p95 = 11.2 ms` na segunda, mediana `2.3–2.6 ms`, 20 repetições cada | `pytest tests/dominio/test_conversao_legado.py -k teto -s` |
| Importar 200 nós e 199 arestas — percentil 95 (RNF-08) | < 5 s | `p95 = 96.4 ms` / `98.4 ms` em duas execuções, mediana `84.6–84.8 ms` | mesmo comando |
| Crescimento do pacote inicial pela documentação embutida (RNF-09) | ≤ teto declarado (teto ainda não fixado — lacuna L-04) | **zero**: cada verbete é pedaço próprio fora do pacote inicial — `ara-*.js 5.34 kB`, `nc-*.js 4.86 kB`, os outros cinco entre `1.65` e `2.30 kB`, contra `index-*.js 348.49 kB` | `npx vite build` |
| Cobertura de testes do domínio novo (RNF-12) | ≥ 85% | `exportacao.py 87%` · `legado.py 87%` · `serializacao.py 85%` · `TOTAL 87%` | `pytest --cov=toc_api.dominio.{serializacao,exportacao,legado}` |

> **Nota de volatilidade (regra R1).** O percentil 95 da conversão variou de `3.1 ms` para
> `11.2 ms` entre duas execuções da mesma suíte na mesma máquina. Os dois números estão
> aqui de propósito: colar só o menor seria escolher a execução de sorte, e o que a RNF-08
> pede (menos de 5 s) é atendido com três ordens de grandeza de folga nos dois casos.


## Evidência dos portões (DoD 18 — gerada por `scripts/evidencia.sh`)

> O bloco abaixo é o **resumo** que o agregador imprimiu, colado sem edição. As saídas
> completas dos 19 portões saem no mesmo comando e não são repetidas aqui por tamanho — o
> comando é a testemunha, não este arquivo.
>
> **Denominadores desta corrida, não de hoje.** Os portões que contam linhas do corpus
> (`check-caminhos.sh`, `check-links.sh`, `check-vazamento.sh`) cresceram depois, porque o
> lote de fechamento documental de 2026-09-06 acrescentou documento ao repositório. A
> reexecução, com a tabela portão a portão, está no `qa-report.md` do ciclo 012, §11.4 —
> [`../012-jornadas-e-autodeclaracao/qa-report.md`](../012-jornadas-e-autodeclaracao/qa-report.md):
> **19 portões, 19 verdes, 0 vermelhos**, o mesmo veredito com números maiores.

<!-- gerado por scripts/evidencia.sh em 2026-09-06 — não editar à mão: rode de novo -->

## Evidência dos portões — 2026-09-06

Portões executados: **19** · verdes: **19** · vermelhos: **0**.
Cada linha traz o código de saída e o denominador que o próprio portão imprimiu
(regra R2: verde sem "quanto examinou?" não é evidência; regra R1: as linhas abaixo
são coladas da execução, não transcritas).

| Portão | Comando | Saída | Veredito | Denominador (linha do próprio portão) |
|---|---|---|---|---|
| `check-caminhos.sh` | `scripts/check-caminhos.sh` | `0` | ✓ verde | arquivos varridos: 139 caminhos conferidos: 1313 · isentos declarados: 478 · entregas futuras declaradas: 106 · moldes ignorados: 20 <br>· saída completa: 5 linhas (contadas por este script) |
| `check-adrs-sucessao.sh` | `scripts/check-adrs-sucessao.sh` | `0` | ✓ verde | ADRs examinados: 14 · linhas de tabela no índice: 15 · linhas em docs/records/decisoes.jsonl: 15 verificações executadas: 56 · sucessões declaradas: 0 · sucedidos declarados: 0 · linhas adr-* conferidas: 14 <br>· saída completa: 7 linhas (contadas por este script) |
| `check-rounds.sh` | `scripts/check-rounds.sh` | `0` | ✓ verde | rounds examinados: 11 (002, 003, 004, 005, 006, 007, 008, 009, 010, 011, 012) campos obrigatórios por round: 7 · conferências de campo: 77 defeitos medidos em docs/produto/visao.md: 12 · alocados a round: 10 · declarados sem round: 2 <br>· saída completa: 8 linhas (contadas por este script) |
| `check-specs.sh` | `scripts/check-specs.sh` | `0` | ✓ verde | ciclos examinados: 12 (001, 002, 003, 004, 005, 006, 007, 008, 009, 010, 011, 012) verificações: artefatos 48 · seções e status 185 · tipos de requisito 71 · linhas de Constitution Check 204 · tokens ART 60 · tokens TAIL 48 · specs pontuadas 12 = 628 <br>· saída completa: 38 linhas (contadas por este script) |
| `check-links.sh` | `scripts/check-links.sh` | `0` | ✓ verde | checked: 605 <br>· saída completa: 3 linhas (contadas por este script) |
| `check-install.sh` | `scripts/check-install.sh` | `0` | ✓ verde | ok: skills (skills) ok: cycle script (scripts/new-cycle.sh) ok: promotion script (scripts/promote-main.sh) ok: spec-driven templates (.specify/templates) ok: constitution (docs/governance/principles.md) ok: operating model (docs/governance/operating-model.md)  <br>· saída completa: 24 linhas (contadas por este script) |
| `check-vazamento.sh` | `scripts/check-vazamento.sh` | `0` | ✓ verde | arquivos varridos: 688 · linhas varridas: 164007 · registros JSON inspecionados: 3476 sinais aplicados: 3 (V1 nome próprio em campo de pessoa · V2 registro no formato da base da irmã · V3 base real lida por código) campos de pessoa vigiados: 21 · chaves do esq <br>· saída completa: 8 linhas (contadas por este script) |
| `check-jornadas.sh` | `scripts/check-jornadas.sh` | `0` | ✓ verde | jornadas examinadas: 7 (001-chegada-e-embarque.md, 002-primeiro-projeto-e-ara.md, 003-nuvem-de-conflito.md, 007-a-travessia.md, 009-cinco-passos-de-focalizacao.md, 010-as-tres-arvores-e-a-cadeia.md, 011-estrategia-e-taticas.md) capturas em disco: 81 · citações <br>· saída completa: 8 linhas (contadas por este script) |
| `check-arquitetura.sh` | `scripts/check-arquitetura.sh` | `0` | ✓ verde | contratos declarados no pyproject.toml: 3 Analyzed 124 files, 741 dependencies. <br>· saída completa: 12 linhas (contadas por este script) |
| `check-raiz-do-agregado.sh` | `scripts/check-raiz-do-agregado.sh` | `0` | ✓ verde | arquivos Python varridos: 222 guardas `_exigir_raiz` encontradas: 8 de 8 mutações de grafo raízes de ferramenta registradas: 7 <br>· saída completa: 14 linhas (contadas por este script) |
| `check-trava-otimista.sh` | `scripts/check-trava-otimista.sh` | `0` | ✓ verde | arquivos varridos: 5 (adaptador SQL, duplo em memória, agregado, registro §A.7, borda HTTP) caminhos de escrita conferidos: 9 declarados · 9 encontrados no adaptador guardas `_gravar_projeto` encontradas: 9 de 9 caminhos de escrita ✓ trava otimista íntegra: 9  <br>· saída completa: 15 linhas (contadas por este script) |
| `check-trava-da-proposta.sh` | `scripts/check-trava-da-proposta.sh` | `0` | ✓ verde | arquivos varridos: 7 (agregado, registro §A.7, adaptador SQL, duplo em caminhos de escrita classificados: 12 com 12 caminho(s) de escrita persistente classificado(s) e a reserva <br>· saída completa: 36 linhas (contadas por este script) |
| `check-evidencia-colada.sh` | `scripts/check-evidencia-colada.sh` | `0` | ✓ verde | afirmações registradas: 33 · comandos executados com sucesso: 33/33 ocorrências conferidas: 37 · arquivos alcançados: 9 <br>· saída completa: 7 linhas (contadas por este script) |
| `check-i18n.sh` | `scripts/check-i18n.sh` | `0` | ✓ verde | arquivos .tsx varridos: 48 cadeias examinadas: 64 candidatas a literal solto cadeias pelo dicionário: 656 chamadas a t()/tc() chaves em pt (língua-fonte): 614 chaves em en (tradução): 614 pendências de tradução (só em pt): 0 ✓ i18n conforme: 48 arquivos, 64 ca <br>· saída completa: 14 linhas (contadas por este script) |
| `check-documentacao.sh` | `scripts/check-documentacao.sh` | `0` | ✓ verde | ferramentas registradas pelo serviço: 7 (apr ara arf at focalizacao nc snt) verbetes no acervo: 7 (apr ara arf at focalizacao nc snt) caminhos de procedência conferidos: 12 âncoras declaradas pela interface: 1 ✓ documentação conforme: 7 ferramentas registradas <br>· saída completa: 8 linhas (contadas por este script) |
| `check-manifesto.sh` | `scripts/check-manifesto.sh` | `0` | ✓ verde | telas declaradas: 12 ações declaradas: 16 sabotagens aplicadas: 7; repelidas: 7 <br>· saída completa: 16 linhas (contadas por este script) |
| `check-politica.sh` | `scripts/check-politica.sh` | `0` | ✓ verde | arquivos de produção varridos: 106 arquivos que compõem PoliticaPorCapability: 3 <br>· saída completa: 4 linhas (contadas por este script) |
| `check-canal.sh` | `scripts/check-canal.sh` | `0` | ✓ verde | arquivos de teste encontrados: 1 # tests 21 # pass 21 # fail 0 <br>· saída completa: 7 linhas (contadas por este script) |
| `check-conformidade-aph.sh` | `scripts/check-conformidade-aph.sh` | `0` | ✓ verde | · persistência ......... postgres (exigida: postgres) · migração (alembic) ... 0009 · natureza do turno .... ENLATADO E DETERMINÍSTICO — não há provedor de modelo Veredito: APTO nos itens verificáveis — 11/11 verificados; 12 itens a autodeclarar. <br>· saída completa: 62 linhas (contadas por este script) |

```text
$ scripts/evidencia.sh > /tmp/evidencia.md
$ echo $?
0
```

### Sabotagem: a prova de que os portões sabem reprovar

```text
$ scripts/tests/run-sabotagem.sh
  portões cobertos: 12  ·  bases válidas aceitas: 12/12
  sabotagens declaradas: 76  ·  reprovadas pelo motivo certo: 76/76
  sabotagens de ambiente: 2  ·  recusadas pelo motivo certo: 2/2

✓ os 12 portões aceitam a base válida e reprovam as 76 sabotagens,
  cada uma pelo motivo que a tabela declara.
$ echo $?
0
```

As **15 sabotagens novas** deste lote são as nove do `check-i18n.sh` (literal no JSX e em
atributo visível, exceção sem motivo, exceção órfã, chave sem tradução, chave só na
tradução, tradução vazia, mecanismo que deixa de lançar, chave crua de volta na tela) e as
seis do `check-documentacao.sh` (ferramenta sem verbete, verbete órfão, procedência que
não resolve, verbete sem procedência, âncora inexistente, verbete sem exemplo).

## Suítes de teste (colado da execução)

```text
$ cd apps/api && pytest -q          # com DATABASE_URL apontando para o PostgreSQL local
1485 passed, 13 warnings in 169.45s (0:02:49)
$ echo $?
0

$ cd apps/web && npx vitest run
 Test Files  26 passed (26)
      Tests  307 passed (307)
$ echo $?
0

$ cd apps/web && npx tsc --noEmit
$ echo $?
0
```

A linha de partida deste lote era `1394 passed` no serviço e `280 passed (280)` na
interface: **+91** e **+27** testes, nenhum deles marcado como pulado.

## Defeito encontrado pelos próprios portões deste lote

O agregador `scripts/evidencia.sh` truncava o resumo com `cut -c1-260`, que conta **bytes**
quando o locale é `POSIX` — e é o caso deste ambiente (`locale` devolve
`LC_CTYPE="POSIX"`). Cortar 260 bytes no meio de um `ç` produzia UTF-8 inválido no meio do
relatório, e quem lesse o arquivo como texto quebrava. Foi encontrado ao colar a saída
**aqui**, e o corte passou a ser por caractere. `awk` não serviu de substituto: o `mawk`
deste ambiente também é orientado a byte.

## Matriz de aderência ao APH re-verificada (INT-04)

> Preenchida em 2026-09-06, quando a matriz inteira deixou de ser um campo de
> `○ planejado` (tarefa T-07 do ciclo 012). As duas linhas que este ciclo declarou tocar são
> as de baixo, e **uma delas não avançou** — o que é resultado, não omissão.

| Linha tocada | Estado antes | Estado depois | Evidência por caminho |
|---|---|---|---|
| APH-6.4 — preenchimento estruturado de argumentos (candidata declarada ao ciclo 011) | ✗ fora do alvo v1, com o ciclo 011 nomeado como candidato | ✗ **continua fora do alvo v1** | Nenhum preenchimento assistido de argumento foi implementado: o ciclo entregou i18n, documentação embutida e portabilidade. A linha está assim, com esta razão escrita, em [`../../docs/integracao/aderencia-aph.md`](../../docs/integracao/aderencia-aph.md) |
| APH-3.1 — registro de telas (telas novas deste ciclo, INT-02) | ○ planejado — ciclo 006 | ● **atendido** | `apps/web/src/telas/registro.ts` × `apps/api/src/toc_api/dominio/federacao/telas.py`, com paridade cobrada por [`../../scripts/check-manifesto.sh`](../../scripts/check-manifesto.sh): `telas declaradas: 12 · ações declaradas: 16 · sabotagens aplicadas: 7; repelidas: 7`. Este ciclo **não criou tela nova** — criou o painel de documentação, que é sobreposição de ajuda e não entra no registro |

## Achados deste lote (registrados, não escondidos)

Numerados para que a revisão independente possa referenciá-los um a um. Os dois primeiros
foram encontrados **durante** a execução; os dois últimos, no lote de fechamento documental
de 2026-09-06, que reexecutou os portões e leu este relatório contra o repositório.

| # | Achado | Onde apareceu | Desfecho |
|---|---|---|---|
| A-01 | O agregador `scripts/evidencia.sh` truncava o resumo com `cut -c1-260`, que conta **bytes** quando o locale é `POSIX` (é o caso deste ambiente): cortar no meio de um `ç` produzia UTF-8 inválido no meio do relatório | ao colar a saída **neste arquivo** — nenhum teste pegou, porque nenhum teste lê o relatório | corrigido: o corte passou a ser por caractere, via `python3`. `awk` não serviu — o `mawk` deste ambiente também é orientado a byte |
| A-02 | O percentil 95 da conversão do formato legado variou de `3.1 ms` para `11.2 ms` entre duas execuções da mesma suíte na mesma máquina | § *Medições registradas* | **os dois números ficaram colados**, com a volatilidade dita ao lado: colar só o menor seria escolher a execução de sorte. O alvo (< 5 s) é atendido com três ordens de grandeza de folga nos dois casos |
| A-03 | A tabela de pré-condições e a de aderência ao APH ficaram com seis e duas células `—`, e `—` é ambíguo: pode ser "não verificado" ou "não cumprido" | lote de fechamento documental (2026-09-06) | preenchidas acima: **cinco pré-condições não foram cumpridas** e uma das duas linhas de APH não avançou. O ciclo foi executado assim mesmo, e agora isso está escrito |
| A-04 | `scripts/tests/sabotagem/README.md` afirma **67** mutações e explica a diferença para as 76 da suíte dizendo que as do `check-i18n.sh` e do `check-documentacao.sh` "são escritas em forma de várias linhas". **A explicação está errada nas duas metades**: as nove que o `grep` não casa são **todas** do `check-i18n.sh`, são de uma linha só, e o motivo é o padrão `check-[a-z-]+\.sh` do registro, que não casa o dígito de `i18n` | lote de fechamento documental, ao contar as sabotagens para o site de produto | **explicação corrigida no README**; o número colado (67) continua sendo o que aquele comando devolve, e a suíte continua declarando 76. O portão `check-evidencia-colada.sh` seguiu verde nos dois momentos — ele confere que o número bate com o comando, não que a **prosa ao lado** esteja certa, e este achado é a demonstração desse limite |

## Pendências (com dono, e nada aqui está resolvido)

| # | Pendência | Dono | Por que não foi feita neste lote |
|---|---|---|---|
| P-01 | **RF-13 — preferência de idioma persistida no servidor** | próximo ciclo de M8 | exige migração, tabela e rota novas; entrar por cima do fim do lote seria esquema de banco sem TDD |
| P-02 | **RF-16 — formatação e colação localizadas** (data, número, ordenação) | próximo ciclo de M8 | idem: escopo próprio, com teste próprio |
| P-03 | **Jornada viva nos dois idiomas** (DoD 17, princípio P6) | próximo ciclo de M8 | as sete jornadas existentes são em português; a captura em inglês exige rodar o script versionado com o idioma trocado |
| P-04 | **As cinco `[DÚVIDA]` do `## Clarify` seguem sem resposta** — inclusive a que muda o RF-12 (idioma padrão) e a que fixa a aposentadoria do formato legado | Product Steward (`TAIL:gate`) | é gate humano, e a implementação **assumiu** a proposta da spec em vez de esperar; a assunção está declarada na tabela de pré-condições |
| P-05 | **Teto de crescimento do pacote inicial (RNF-09, lacuna L-04) não fixado** | Product Steward + próximo ciclo | o crescimento medido foi **zero**, o que torna o teto barato de fixar — mas fixá-lo é decisão, não medição |
| P-06 | **O ensaio de restauração rodou contra o PostgreSQL local, não contra o provedor de produção** | ciclo 003 (metade operacional da raia infra) | não há ambiente de produção: deploy, endereço e rollback não foram executados |
| P-07 | **A cauda deste ciclo está aberta**: `TAIL:review`, `TAIL:security` e `TAIL:gate` | revisão em contexto fresco (as duas primeiras) e Product Steward (a terceira) | quem executou não verifica (Princípio II do Maestro) |
| P-08 | **`data-model.md` declarado `ART:data-model=yes` e ausente** | ciclo 011, tarefa T-02 | depende da resposta do Clarify sobre a preferência de idioma ser por pessoa ou por inquilino — escrever o modelo antes seria fixar por conta própria matéria de gate. O portão diz isso a cada execução (§ *Portão vermelho declarado*) |
| P-09 | **`ux-design.md` declarado `ART:ux-design=yes` e ausente** | ciclo 011, tarefa T-04 | as duas superfícies novas (painel de documentação com âncoras e relato de importação) foram construídas sobre os padrões já desenhados; o adendo de papel semântico, que o `plan.md` exige antes da UI, **não foi escrito** |

## Cauda

| Item | Executor (contexto fresco) | Achados | Evidência |
|---|---|---|---|
| TAIL:review | **não executada** — indelegável a quem construiu (Princípio II do Maestro: quem executa não verifica) | — | ver a linha escrita abaixo |
| TAIL:security | **não executada**, pelo mesmo motivo | — | ver a linha escrita abaixo |
| TAIL:mutation | agente do lote M8 (a sabotagem é executável, não julgamento) | 15 sabotagens novas, 15 recusas pelo motivo declarado | `sabotagens declaradas: 76 · reprovadas pelo motivo certo: 76/76` |
| TAIL:gate | **NÃO marcado, de propósito** — é do Product Steward | — | ver a linha escrita abaixo |

Em forma de lista, porque `—` numa tabela não é registro de estado — é ausência de registro:

- **TAIL:review** — **não executada**, e não pode ser executada por quem construiu
  (Princípio II). O que este lote deixa pronto para ela: as 14 linhas da DoD com comando e
  saída colada, os quatro achados numerados A-01 a A-04, as sete pendências com dono, e as
  duas tabelas que saíram do `—` (pré-condições e matriz de aderência ao APH). Os dois
  pontos que mais pedem olho de fora: **cinco das seis pré-condições de abertura não
  estavam cumpridas** e o ciclo foi executado assim mesmo; e a preferência de idioma
  (RF-13) ficou de fora, o que deixa a metade servidora do E8.3 por fazer.
- **TAIL:security** — **não executada**, pelo mesmo motivo. O que já está medido e espera
  conferência independente: nenhum segredo no cliente (DoD 16 — `0` ocorrências reais de
  `api[_-]?key`/`secret` em `apps/web/src/`, as 19 brutas sendo o português
  "secretaria"/"secreta"); nenhum dado real de pessoa (`scripts/check-vazamento.sh` sobre
  689 arquivos e 166 910 linhas); o ensaio de restauração **sem credencial na saída**
  (RNF-10); e o adaptador do formato legado, que é a superfície que recebe arquivo de fora
  — recusa campo a campo, teto de tamanho e descarte de `chatHistory` declarado.
- **TAIL:mutation** — **executada**: `scripts/tests/run-sabotagem.sh` saiu `0` com
  `portões cobertos: 12 · bases válidas aceitas: 12/12` e
  `sabotagens declaradas: 76 · reprovadas pelo motivo certo: 76/76`. As **15 novas** deste
  lote plantam, uma por vez: o literal `"Salvar"` dentro do JSX e um `aria-label` literal
  (o defeito de `tocbuilderv3/components/SnTView.tsx:182`); exceção sem motivo e exceção
  que não corresponde a literal nenhum; chave sem tradução, chave só na tradução e
  tradução vazia; o mecanismo que deixa de lançar em chave ausente e o que devolve a chave
  crua (`tocbuilderv3/i18n/I18nProvider.tsx:41` de volta); ferramenta registrada sem
  verbete e verbete órfão; procedência que não resolve e verbete sem procedência nenhuma;
  âncora de ajuda inexistente; verbete sem exemplo sintético. Cada uma exige o **trecho
  declarado** na saída — reprovar por acidente não conta.
- **TAIL:gate** — **NÃO marcado, de propósito.** É o Product Steward quem assina, e a
  assinatura inclui matéria substantiva: as cinco `[DÚVIDA]` do `## Clarify` (P-04), a
  aposentadoria do formato legado, o teto do pacote inicial (P-05) e a decisão sobre as
  cinco pré-condições que não estavam cumpridas quando o ciclo rodou. Quem executou não
  aprova o que executou.

## Portão vermelho declarado — `scripts/check-conformance.sh 011`

Ele sai `1`, e o vermelho está **certo**. Saída colada da execução de 2026-09-06, **depois**
da revisão que preencheu as tabelas deste relatório:

```text
$ scripts/check-conformance.sh 011
── Conformance: did the method survive into the artifacts? ──
   (floor: cycle 42; older cycles carry declared debt — see the roadmap)
• 011-fundacoes-da-aplicacao
    ✓ Constitution Check complete (8/8)
    · acceptance-criteria checkboxes: not checked below cycle 45
    ✗ data-model: declared ART:data-model=yes but no data-model.md in the cycle
    ✗ ux-design: declared ART:ux-design=yes but no ux-design.md in the cycle
    ✓ TAIL:review evidence: não executada**, e não pode ser executada por quem const
    ✓ TAIL:security evidence: não executada**, pelo mesmo motivo. O que já está medid
    ✓ TAIL:gate evidence: NÃO marcado, de propósito.** É o Product Steward quem a
──
cycles checked: 1
✗ mutation floor 55 is above the newest cycle 012 — TAIL:mutation was charged to nobody.
✗ declared-absence floor 61 is above the newest cycle 012 — 'pendente' would pass as evidence everywhere.
✗ the method did not survive into the artifacts of at least one cycle.
$ echo $?
1
```

Quatro `✗` — dois do ciclo e dois de piso —, e cada um é uma coisa diferente:

| `✗` / `✓` | O que é | O que se faz com ele |
|---|---|---|
| `✗ data-model` e `✗ ux-design` declarados `yes` e ausentes | **dívida real**, e já declarada no [`plan.md`](plan.md): os dois nascem na abertura do ciclo (T-02 e T-04) e dependem de respostas do Clarify e do gate de UX | pendências **P-08** e **P-09**. Declarar `no` para o portão calar seria mentir sobre um ciclo que persiste estrutura e desenha tela nova |
| `✓` nas três linhas de cauda | **elas eram `✗` até esta revisão**, com a mensagem `TAIL:review applies but is absent from qa-report.md — a tick is not a witness`, porque a tabela da Cauda trazia `—`. O `—` não é evidência de nada: não distingue "não executada" de "ninguém escreveu" | o que mudou foi o **registro**, não a execução: as três agora dizem por extenso que **não foram executadas** e por quê. O portão confere que existe registro de estado — não que a cauda rodou —, e as três continuam por executar (P-07) |
| os dois pisos (`mutation floor 55`, `declared-absence floor 61`) | **externos**: são números absolutos de ciclo do repositório canônico do método, e um repositório que começa em 001 nunca os alcança | relatado e parado em [`../../mensagens/002-para-maestro-pisos-absolutos-de-ciclo.md`](../../mensagens/002-para-maestro-pisos-absolutos-de-ciclo.md) (P1: não se corrige lá). O mesmo comando sobre qualquer ciclo daqui devolve os mesmos dois |

## Cobertura de requisitos

*(a linha-a-linha por RF-01..RF-32, RI-01..RI-11, RNF-01..RNF-12, RN-01..RN-07 e
INT-01..INT-04 continua pendente, e continua sendo trabalho do fechamento do ciclo — não do
lote documental. O que **existe** hoje, e que a revisão pode usar como ponto de partida, é o
mapa por família:)*

| Família | Coberto neste lote | Não coberto | Onde está a prova |
|---|---|---|---|
| Internacionalização (E8.3) | ordem do idioma efetivo, paridade pt × en, chave ausente que falha alto, zero literal órfão | RF-13 (preferência no servidor) e RF-16 (formatação/colação) — P-01 e P-02 | DoD 2 a 5; [`../../scripts/check-i18n.sh`](../../scripts/check-i18n.sh) |
| Documentação embutida (E8.4) | cobertura ferramenta × verbete, procedência que resolve, âncora de ajuda, exemplo sintético por verbete | verbete de "por onde começar" ([DÚVIDA] 3) | DoD 8 e 9; [`../../scripts/check-documentacao.sh`](../../scripts/check-documentacao.sh) |
| Exportação e importação (E1.4) | documento consolidado com ida e volta, conversão do formato legado, recusa campo a campo, descarte declarado | aposentadoria do adaptador legado ([DÚVIDA] 2) | DoD 10 a 13, com os comandos rodados de `apps/api` (`apps/api/tests/dominio/test_conversao_legado.py` e `apps/api/tests/integracao/test_portabilidade_no_postgres.py`) |
| Fundações de operação | ensaio de restauração executado e medido | contra o provedor de produção — P-06 | DoD 14; [`../../scripts/ensaio-de-restauracao.sh`](../../scripts/ensaio-de-restauracao.sh) |
| Jornada viva (P6) | — | a jornada nos dois idiomas — P-03 | DoD 17, não executada |

## Veredito

**Execução parcial, provada no que fez e explícita no que não fez; ciclo NÃO fechado.**
**Catorze** das 18 linhas da DoD têm comando executado e saída colada; as outras quatro
estão com `—`, e não com "parcialmente": as linhas 6, 7 e 17 porque o lote **não** as
executou (RF-13, RF-16 e a jornada nos dois idiomas), e a 15 porque não se aplica —
nenhum requisito entregue aqui mudou esquema, logo não houve migração para reverter. Os 19 portões do agregador saíram verdes e as sabotagens
reprovam pelo motivo declarado — inclusive as 15 que este ciclo acrescentou.

O que este relatório passou a dizer em 2026-09-06, e não dizia: **cinco das seis
pré-condições de abertura não estavam cumpridas**, e o ciclo foi executado assim mesmo.
Isso é material de gate, não de nota de rodapé.

`TAIL:review`, `TAIL:security` e `TAIL:gate` continuam **em branco**. Caixa marcada não é
testemunha, e nenhuma foi marcada.
