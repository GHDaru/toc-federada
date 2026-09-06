# QA report 007 — Nuvem de Conflito (M3)

> Siglas deste documento: **QA** — *Quality Assurance* (garantia de qualidade) · **DoD** —
> *Definition of Done* (Definição de Pronto) · **NC** — Nuvem de Conflito · **ARA** — Árvore
> da Realidade Atual · **UDE** — Efeito Indesejável (*Undesirable Effect*) · **M1** — Núcleo
> de Diagramas Lógicos · **M3** — a NC · **FSM** — máquina de estados finitos · **IA** —
> inteligência artificial · **TRIZ** — Teoria da Resolução Inventiva de Problemas · **SDK** —
> *Software Development Kit* · **ADR** — *Architecture Decision Record* (Registro de Decisão
> Arquitetural) · **APH** — Aplicação ↔ Harness · **RF/RI/RN/RNF/INT** — requisito funcional
> / de interface / regra de negócio / não funcional / integração · **AST** — árvore sintática
> abstrata · **p95** — percentil 95.

- **Data da bateria**: 2026-09-06 · **Raia**: plena
- **Veredito atual**: **executado e medido; NÃO fechado.** Das 16 linhas da DoD, **13 estão
  verdes com saída colada**, **1 verde com ressalva declarada** (linha 12 — o grep pega a
  denylist do snapshot), **1 VERMELHA** (linha 10 — a exportação sem perda não existe) e
  **1 vermelha por causa externa já relatada** (conformidade).
- **O que este ciclo entregou e a linhagem nunca teve**: a Nuvem com **topologia
  indestrutível** (5 entidades, 7 arestas, criadas na origem), a **premissa como entidade de
  primeira classe**, a injeção que **não existe sem premissa viva**, a geração assistida com
  **contrato e não parser** — e o **encadeamento M2 → M3**, a costura que as quatro gerações
  do TOC-Builder nunca fizeram: lá, ARA e Nuvem eram dois bancos simulados sem referência
  entre si.
- **O achado de revisão independente deste ciclo**: o laço da assistência **não fechava na
  tela** — a pré-visualização mostrava o diff inteiro e oferecia **um** botão, "Recusar".
  Corrigido pelo caminho que o padrão manda, com ADR (§5.1).

> **R1 e R2 aplicadas linha a linha.** Toda saída foi executada em **2026-09-06**, entre
> 04:50Z e 05:41Z, e está **colada**.
>
> **Ressalva de medição.** O repositório **estava sendo construído enquanto era medido** (o
> lote do M6, spec 009). O mesmo comando de suíte devolveu `1201 passed` às 05:07Z e
> `1219 passed` às 05:19Z; e às **05:41Z** o portão `scripts/check-trava-da-proposta.sh`
> passou de verde a **vermelho** porque um caminho de escrita novo do M6 entrou sem entrar na
> lista dele — fato registrado no `qa-report.md` do ciclo 006, §1.1, com dono. Os números
> abaixo são os da medição mais recente, com a volatilidade dita ao lado.

## 0 · Histórico de veredito — os estados por que este ciclo passou

| # | Data | Estado | O que aconteceu | Evidência |
|---|---|---|---|---|
| **V1** | 2026-09-06 | **construído** | Agregado `NuvemDeConflito` com topologia fixa sobre o núcleo do M1 por composição; premissas e injeções; classificação TRIZ; encadeamento `derivar_nuvem_de_udes`; geração validada por esquema JSON versionado; três ações governadas; migração `0005`; 20 operações sob `/toc/nc`; interface (diagrama, ficha de aresta, vista tabular, visão conflito+solução, prévia da geração). | `apps/api/src/toc_api/dominio/nuvem.py` (mtime 01:24Z), `apps/api/src/toc_api/alembic/versions/0005_m3_nuvem_de_conflito.py` |
| **V2** | 2026-09-06 | **REPROVADO — o agregado tinha porta dos fundos, e a NC foi onde isso se provou** | A reprodução do achado usou **esta** ferramenta: `DELETE aresta D_D_PRIME pela rota generica -> 204` e, em seguida, `GET /toc/nc/projetos/{id} -> 404` sobre um projeto que continuava no banco. | §5.2, achado **A-02** |
| **V3** | 2026-09-06 | **REPROVADO — o laço da assistência não fechava na tela** | A pré-visualização da geração era um beco sem saída: mostrava o diff e oferecia só "Recusar". A funcionalidade mais vistosa do produto **não concluía**. | §5.1, achado **A-01** |
| **V4** | 2026-09-06 | **corrigido pelo caminho que o padrão manda** | `POST /toc/propostas` e `POST /toc/propostas/{id}/decisao` (ADR 0009), sobre os **mesmos** casos de uso — mesma FSM, mesma política, mesmo traço. Nenhum segundo caminho de escrita. | §5.1 |
| **V5** | 2026-09-06 | **medido** | Esta bateria: 16 linhas com comando, saída colada e denominador; e a métrica de RNF-05 **medida**, não estimada (§4). | §2, §4 |
| **V6** | — | **aguardando gate humano** | `TAIL:gate` **não marcado**. | §8 |

## 1 · Bateria de portões (denominador colado — regra R2)

`scripts/evidencia.sh`, executado às **04:50Z**, saiu **0**:
`Portões executados: 17 · verdes: 17 · vermelhos: 0.`

| # | Portão | Código | Denominador — a linha do próprio portão |
|---|---|---|---|
| G1 | `scripts/check-arquitetura.sh` (P3) | **0** ✓ | `contratos declarados no pyproject.toml: 3` · `Contracts: 3 kept, 0 broken.` sobre `Analyzed 114 files, 629 dependencies.` |
| G2 | `scripts/check-raiz-do-agregado.sh` | **0** ✓ | `operação só pela raiz: 8 guardas, 6 raízes, 192 arquivos varridos.` — e `NuvemDeConflito` é uma das raízes registradas (`apps/api/src/toc_api/dominio/nuvem.py:75`) |
| G3 | `scripts/check-trava-otimista.sh` | **0** ✓ | `caminhos de escrita conferidos: 8 declarados · 8 encontrados no adaptador` — inclui `salvar_nuvem` |
| G4 | `scripts/check-manifesto.sh` | **0** ✓ | `telas declaradas: 9` · `ações declaradas: 15` · `sabotagens aplicadas: 7; repelidas: 7` |
| G5 | `scripts/check-vazamento.sh` (ADR 0006) | **0** ✓ | `arquivos varridos: 579 · linhas varridas: 131024 · registros JSON inspecionados: 3364` |
| G6 | `scripts/check-jornadas.sh` (P6) | **0** ✓ | `jornadas examinadas: 4 · capturas em disco: 36 · citações de imagem: 36 · data das capturas (manifesto): 2026-09-06` · `verificações executadas: 80` |
| G7 | `scripts/check-caminhos.sh` · `scripts/check-links.sh` | **0** ✓ | `caminhos conferidos: 1005 · isentos declarados: 330` · `checked: 469` |
| G8 | `scripts/check-conformance.sh 007` | **1** ✗ | `cycles checked: 1` — diagnóstico em §4.1 |

## 2 · DoD — as 16 linhas da spec, com comando, saída colada e veredito

> **Ajuste de caminho declarado.** A spec cita quatro arquivos de teste que não existem com
> aquele nome — um de injeção, um de geração proposta, um de visão de solução e um de traço
> do M3 — nas árvores em inglês que o planejamento supunha, mais as duas que ela chama de
> *backend* e *frontend* (os caminhos exatos estão na spec, §Critérios de aceite). A árvore
> real é `apps/api/tests/dominio/…`, `…/aplicacao/…`,
> `…/federacao/…`, `…/contrato/…` e `apps/web/src/…`, e a camada de interface é testada por
> Vitest, não por pytest. Os comandos abaixo são **os mesmos critérios sobre os caminhos que
> existem**; os de pytest rodam de `apps/api` e os de Vitest de `apps/web`.

| # | Critério | Comando | Saída (colada) | Examinou | Código | Veredito |
|---|---|---|---|---|---|---|
| 1 | Invariantes da nuvem no domínio puro, offline | `pytest tests/dominio/test_nuvem_invariantes.py -p no:cacheprovider -q` + `lint-imports` | `13 passed in 0.10s` · `Contracts: 3 kept, 0 broken.` | 13 casos sem rede nem banco; 3 contratos de arquitetura sobre 114 arquivos | `0` · `0` | ✓ verde |
| 2 | 5 entidades e 7 arestas indestrutíveis (RN-01) | `pytest tests/dominio/test_nuvem_invariantes.py -k "topologia or indestrut or aresta or entidade" -v` | `9 passed, 4 deselected in 0.11s`, com `test_a_nuvem_nasce_com_as_cinco_entidades_e_as_sete_arestas PASSED`, `test_nao_existe_caminho_para_criar_ou_excluir_entidade_ou_aresta PASSED` e `test_a_chave_da_aresta_e_derivada_do_par_de_papeis_e_nunca_digitada PASSED` | 9 casos. O segundo é o que dá dente à RN-01: **não existe caminho** para criar ou excluir — não é validação, é ausência de operação | `0` | ✓ verde |
| 3 | Injeção sempre referencia premissa (RN-04) | `pytest tests/dominio/test_premissas_e_injecoes.py -q -s` | `18 passed in 0.12s`, com a saída `posições da visão de solução: 7; com injeção=['D_C', 'D_D_PRIME']` | 18 casos: sem premissa viva não há construtor de injeção; arquivar premissa arquiva as injeções **dizendo quantas** | `0` | ✓ verde |
| 4 | FSM de status de injeção (RN-08) | mesmo arquivo, dentro dos `18 passed` | `18 passed in 0.12s` | `candidata → escolhida \| descartada`, com o retorno a candidata exigindo justificativa | `0` | ✓ verde |
| 5 | Recusar geração deixa o projeto intacto (RF-24) | `pytest tests/federacao/test_catalogo_m3.py -k "byte_a_byte" -v` | `1 passed, 8 deselected in 0.18s`: `test_recusar_a_geracao_deixa_o_projeto_byte_a_byte_intacto PASSED` | a comparação é de **bytes do estado serializado** antes e depois — não de "parece igual" | `0` | ✓ verde |
| 6 | Resultado fora do schema é recusado em falha fechada (RF-22) | `pytest tests/dominio/test_resultado_de_geracao.py -v` | `17 passed`, com **12 casos parametrizados de recusa**: `campo obrigatório ausente`, `entidade faltando`, `aresta faltando`, `aresta desconhecida`, `papel desconhecido`, `versão desconhecida`, `versão que nem é texto`, `premissa vazia`, `separação TRIZ fora do vocabulário`, `entidade sem texto`, `campo fora do contrato`, `aresta que não é lista` | 17 casos, e cada recusa **nomeia o motivo** | `0` | ✓ verde |
| 7 | Nenhum parse de markdown no caminho da geração | `pytest tests/dominio/test_resultado_de_geracao.py -q -s` (o caso `test_nenhum_parse_de_markdown_no_caminho_da_geracao`) | `caminho da geração examinado por árvore sintática — toc_api.dominio.geracao: 108 literal(is) de código; toc_api.dominio.nuvem: 182 literal(is) de código` | **290 literais** varridos por AST nos dois módulos do caminho da geração. O grep textual pedido pela spec devolve `2`, e as duas são **comentários** que citam o defeito da linhagem (`apps/api/src/toc_api/dominio/portas.py:282`, `apps/api/src/toc_api/dominio/geracao.py:14`) — a varredura por AST é a versão séria do mesmo critério | `0` | ✓ verde |
| 8 | Heurísticas de formulação com corpus | `pytest tests/dominio/test_formulacao.py -q -s -v` | `corpus de formulação v1.0.0: 20 caso(s) — 10 bem formulado(s), 10 mal formulado(s); idiomas=['en', 'pt']` · `casos conferidos: 20; divergentes: 0` · `códigos de aviso: 3; cobertos pelo corpus: 3` · `10 passed in 0.10s` | 20 casos nos dois idiomas; **todo código de aviso tem caso no corpus** — ampliar a heurística exige ampliar o corpus (RNF-08) | `0` | ✓ verde |
| 9 | Visão de solução cobre as 7 arestas (RF-31) | `npx vitest run src/componentes/nuvem src/telas/TelaDaNuvem.test.tsx --reporter=verbose` | `Tests  44 passed (44)`, com `✓ desenha as SETE arestas — inclusive D⇸C e D↯D′, que o v3 nunca renderizou` e `✓ alterna para a solução e mostra as SETE posições, com a pendência marcada` | 44 testes de interface da NC; **o defeito do v3 — que renderizava cinco — virou caso de teste** | `0` | ✓ verde |
| 10 | Exportação sem perda (RF-33) | `grep -rn "export" apps/api/src/toc_api/aplicacao/nuvem.py apps/api/src/toc_api/http/roteadores/nuvem.py` | **saída vazia** | o caso de uso e o roteador inteiros da NC; das 20 operações de `/toc/nc`, nenhuma é exportação. O que existe é **travessia do banco** ida-e-volta (`7 passed in 7.64s`), que é outra coisa | `1` | ✗ **VERMELHO** — ver A-04 |
| 11 | Toda mutação nova com traço | `pytest tests/aplicacao/test_casos_de_uso_da_nuvem.py -q` | `15 passed in 0.18s` | 15 casos de uso do M3; o span é da classe-base, e a recusa também deixa traço — `test_desafiar_premissa_sem_justificativa_e_recusado_e_a_recusa_vira_traco` | `0` | ✓ verde |
| 12 | Sem SDK, chave ou prompt no produto | `grep -rniE "genai\|openai\|anthropic\|api[_-]?key" apps/api/src/ apps/web/src/` | `3`, as três em `apps/api/src/toc_api/dominio/federacao/snapshot.py:46`, `:58`, `:59` — a **denylist** de segredos do snapshot | as duas árvores de código-fonte. `CONFLICT_CLOUD_PROMPT` (o nome do prompt da linhagem) devolve **0** | `0` (grep) | ⚠ **verde no conteúdo, vermelho na letra** — ver A-05 |
| 13 | Capability ausente esconde as 3 mutadoras (RF-27) | `pytest tests/federacao/test_catalogo_m3.py -k capab -v` | `1 passed, 8 deselected in 0.17s`: `test_sem_capability_de_escrita_as_tres_mutadoras_do_m3_nao_existem PASSED`; e o catálogo inteiro imprime `com toc:read+toc:write → 15; só com toc:read → 4; anônimo → 0` | as três ações `toc.generate_conflict_cloud`, `toc.suggest_assumptions`, `toc.suggest_injections` **somem** do catálogo, não são "recusadas depois" | `0` | ✓ verde |
| 14 | Jornada viva do dilema sintético | `scripts/check-jornadas.sh` | `jornadas examinadas: 4 · capturas em disco: 36 · citações de imagem: 36 · data das capturas (manifesto): 2026-09-06` · `verificações executadas: 80` | `docs/jornadas/003-nuvem-de-conflito.md` (o dilema da "Instituição Horizonte" de ponta a ponta) e `docs/jornadas/007-a-travessia.md` (ARA → NC), as duas com captura do build real e heurística datada; o grep negativo de nome real é o portão de vazamento (G5) | `0` | ✓ verde |
| 15 | Conformidade do ciclo | `scripts/check-conformance.sh 007` | ver §4.1 | `cycles checked: 1` | `1` | ✗ **vermelho — três causas, uma externa** |
| 16 | Caminhos e links | `scripts/check-caminhos.sh` · `scripts/check-links.sh` | `✓ todo caminho citado entre crases existe.` (`caminhos conferidos: 1005 · isentos declarados: 330`) · `✓ every relative link resolves.` (`checked: 469`) | 125 arquivos · 469 links | `0` · `0` | ✓ verde |

**Placar da DoD: 13 verdes · 1 verde com ressalva declarada · 2 vermelhas** (1 substantiva +
a de conformidade).

## 3 · Portões nomeados do roadmap (ciclo 007)

| Portão | Como se verificou | Evidência colada |
|---|---|---|
| Invariantes da nuvem por teste de domínio (5 entidades, 7 arestas, injeção referencia premissa) | `pytest tests/dominio/test_nuvem_invariantes.py tests/dominio/test_premissas_e_injecoes.py -q` | `13 passed in 0.10s` e `18 passed in 0.12s` |
| A geração a partir de narrativa entra como `action_proposal`; recusar deixa o projeto intacto | `pytest tests/federacao/test_catalogo_m3.py -q -s` | `9 passed in 0.18s`, com `recusas registradas no traço: ['denied', 'denied', 'denied']` e o caso byte a byte |
| Jornada do dilema sintético da "Instituição Horizonte" de ponta a ponta, com captura | `scripts/check-jornadas.sh` | `jornadas examinadas: 4 · capturas em disco: 36 · citações de imagem: 36` — J-03 é a do dilema |
| A costura M2 → M3 atravessa o banco (INT-05) | `pytest tests/integracao/test_nuvem_no_postgres.py -q` | `7 passed in 7.64s`, incluindo `test_a_costura_com_a_ara_atravessa_o_banco` |

## 4 · Medições registradas (RNF-05 / RNF-06)

| Métrica | Alvo | Valor medido | Fonte |
|---|---|---|---|
| Abrir projeto NC completo (7 arestas, 30 premissas, 50 injeções) — p95 | < 1 s | **0,649 ms** — `RNF-05 (007) abrir a nuvem completa: 7 arestas, 30 premissas, 50 injecoes na visao de solucao · p95 = 0.649 ms (teto 1000 ms) · 200 execucoes` | medição sobre o domínio puro (validação + matriz + leitura das 7 arestas + visão de solução), 200 execuções, 2026-09-06 |
| Recusa de proposta (sem escrita no agregado) | < 500 ms | — | ✗ **não medido**: não há medição de tempo em teste nenhum (`grep "perf_counter\|p95" apps/api/tests/` devolve vazio). O que está provado é que a recusa **não escreve** (`corrida de recusa · nós no banco 0`), não quanto ela demora. Dívida **Dv-5** |

**Alcance declarado**: a medição acima é de uma execução **ad-hoc**, não de um script
versionado no repositório. O número é real e foi produzido agora; a reprodutibilidade por
terceiro ainda não está garantida (**Dv-6**).

### 4.1 · O portão vermelho de conformidade

```text
$ scripts/check-conformance.sh 007
• 007-nuvem-de-conflito
    ✓ Constitution Check complete (8/8)
    · acceptance-criteria checkboxes: not checked below cycle 45
    ✗ data-model: declared ART:data-model=yes with no reason — a declaration without a why is silence
    ✗ contracts: declared ART:contracts=yes but no contracts.md in the cycle
    ✗ TAIL:review applies but is absent from qa-report.md — a tick is not a witness
    ✗ TAIL:security applies but is absent from qa-report.md — a tick is not a witness
    ✗ TAIL:gate applies but is absent from qa-report.md — a tick is not a witness
──
cycles checked: 1
✗ mutation floor 55 is above the newest cycle 012 — TAIL:mutation was charged to nobody.
✗ declared-absence floor 61 is above the newest cycle 012 — 'pendente' would pass as evidence everywhere.
$ echo $?
1
```

Três causas: **(a)** os pisos absolutos do script do método — externos, relatados em
`mensagens/002-para-maestro-pisos-absolutos-de-ciclo.md`, `GHDaru/maestro` é leitura (P1);
**(b)** as três linhas `TAIL:*`, que eram verdadeiras e que este documento fecha em §10;
**(c)** `contracts: declared ART:contracts=yes but no contracts.md in the cycle`. A terceira
merece precisão: o **schema versionado do resultado da geração existe** e está em código
(`apps/api/src/toc_api/dominio/geracao.py`), com 17 testes e uma varredura AST; o que não
existe é o diretório de contratos que o `plan.md` declarou. É defeito de declaração, não de
entrega — e mesmo assim fica vermelho (**Dv-1**).

## 5 · TAIL:review — a revisão independente, com os achados numerados

### 5.1 · A-01 · O laço da assistência não fechava na tela

**A pré-visualização da geração assistida era um beco sem saída.** Ela mostrava o diff inteiro
do que a geração propunha e oferecia **um** botão: "Recusar". Não existia, em lugar nenhum da
aplicação, caminho para a pessoa **aceitar** a proposta e ver a Nuvem mudar — a funcionalidade
mais vistosa do produto **não concluía**. A ausência estava documentada no próprio componente
(*"a escrita é da proposta que atravessa a máquina de estados no servidor"*), e **a
documentação da ausência é a descrição do buraco, não o conserto dele**. A avaliação heurística
datada da J-03 já registrava o mesmo achado (A-03), aberto desde então.

**Causa raiz**: o servidor tinha a ação governada, a FSM, a política, o traço e o executor — e
as duas portas de proposta que existiam servem o **hospedeiro** (o fio do §A.6 e a borda
`POST /aph/actions/{id}`, que devolve `{"result": <frase>}` por contrato dele). Faltava a porta
do **terceiro consumidor**: a interface da própria aplicação, que precisa do `proposal_id` em
dado estruturado — extraí-lo da frase seria o cliente discriminando por mensagem, o que o §A.7
proíbe.

**Destino — corrigido pelo caminho que a spec 006 e o padrão mandam** (ADR 0009):
`POST /toc/propostas` (a proposta nasce e **espera**) e
`POST /toc/propostas/{proposal_id}/decisao` (o gate humano), montadas sobre os **mesmos**
`ProporAcao` e `DecidirProposta` — mesma FSM, mesma política verificada no caso de uso, mesmo
registro de erros, mesmo traço. **Nenhum segundo caminho de escrita**: a rota não toca
repositório. Do lado da tela, "Aceitar" leva a proposta ao gate e a superfície de confirmação
decide, com os dois botões de mesmo peso e o desfecho anunciado por `aria-live`.

Verificação de hoje:

```text
$ cd apps/api && pytest tests/contrato/test_http_propostas.py tests/integracao/test_propostas_no_postgres.py -q -s
proposta 6d4b55d5-…: awaiting_approval → executed · desfecho=executed · 5 entidade(s), 7 premissa(s) e 1 injeção(ões) aplicadas
linhas de traço do inquilino: 1; desta proposta: 1
recusa: estado=denied · traço=['denied']
1ª: executed · 2ª: executed · nuvem mudou entre as duas: False
proposta 2deb2f5e-…  confirmada por outra aplicação; entidades reescritas: 5 de 5 · premissas gravadas: 7
recusa persistida · traço: ['denied']
13 passed, 2 warnings in 8.47s
```

A última linha é a prova que interessa: a proposta é **propostas numa aplicação, confirmada
noutra, lida numa terceira**. Se vivesse em memória, a segunda não a encontraria.

E do lado da tela, os quatro casos que fecham o laço:

```text
$ cd apps/web && npx vitest run src/componentes/nuvem src/telas/TelaDaNuvem.test.tsx --reporter=verbose
 ✓ tela da nuvem — o laço da assistência fecha pelo gate governado > aceitar cria a proposta governada com o resultado que a prévia mostrou
 ✓ tela da nuvem — o laço da assistência fecha pelo gate governado > confirmar no gate muda a nuvem na tela — e a mudança vem do servidor
 ✓ tela da nuvem — o laço da assistência fecha pelo gate governado > recusar no gate deixa a nuvem intacta e o desfecho aparece — nunca em silêncio
 ✓ tela da nuvem — o laço da assistência fecha pelo gate governado > a recusa do servidor ao criar a proposta vira frase, e a prévia continua lá
 Tests  44 passed (44)
```

### 5.2 · A-02 · A nuvem foi onde a porta dos fundos do agregado se provou

O achado da fronteira do agregado é do M1 e está relatado no `qa-report.md` do ciclo 004 —
mas **a reprodução usou a NC**, e o efeito nela era o pior do repositório:

```text
nasceu: 5 entidades, 7 arestas
DELETE aresta D_D_PRIME pela rota generica -> 204
GET /toc/nc/projetos/{id} depois -> 404 {"error":{"code":"NOT_FOUND","message":"recurso não encontrado"}}
DELETE entidade A pela rota generica -> 200 {"no_id":"…","arestas_removidas":["…","…"]}
```

A nuvem **sumia da leitura** — `404` sobre um projeto que continuava no banco — e a resposta
da mutilação era `204 No Content`. A RN-01 ("topologia indestrutível") era verdadeira **dentro**
do agregado e falsa **fora** dele.

**Destino — corrigido, com a terceira porta fechada junto**: `Projeto._exigir_raiz` nas oito
mutações de grafo, e a recusa também no **executor do catálogo federado** — uma ação governada
aprovada por gate humano mutilaria a nuvem igual. Verificação de hoje:
`33 passed, 2 warnings in 1.29s` nos três arquivos da fronteira, e
`✓ operação só pela raiz: 8 guardas, 6 raízes, 192 arquivos varridos.`

### 5.3 · Os demais achados

| # | Achado | Severidade | Destino |
|---|---|---|---|
| **A-03** | **A pré-visualização abria numa coluna estreita** enquanto a metade direita da janela ficava vazia; o diff Hoje × Proposto ficava com três a quatro palavras por linha | Média | ✅ **corrigido em 2026-09-06**: prévia e superfície de confirmação a `min(880px, 100%)` — as duas são leitura para decidir, não formulário lateral |
| **A-04** | **A exportação sem perda (RF-33, linha 10 da DoD) não existe.** Nem caso de uso, nem rota: das 20 operações de `/toc/nc`, nenhuma exporta. O que está provado é a **travessia do banco** (`test_a_nuvem_inteira_sobrevive_a_um_processo_novo`), que responde outra pergunta | Média | ✗ **VERMELHO assumido**. Dono: **ciclo 011** — é onde a exportação canônica está alocada, e os `qa-report.md` dos ciclos 004 e 008 declaram a mesma pendência |
| **A-05** | A linha 12 pede `= 0` e devolve `3`, as três a denylist do snapshot. O critério não distingue "cita o nome do segredo para bloqueá-lo" de "usa o segredo" | Baixa | 📝 registrado: é o **quarto ciclo** a tropeçar no mesmo critério mal escrito (005, 006, 007, 008) — o que sugere corrigir o critério uma vez, e não quatro ressalvas |
| **A-06** | O grep textual da linha 7 (`markdown`) devolve `2` e não `0`; as duas são comentários que **citam** o parser da linhagem como contraexemplo. A versão séria do critério existe e é melhor: a varredura AST sobre 290 literais | Baixa | 📝 registrado junto com A-05 |
| **A-07** | A **verbalização de origem** existe no dado e está ilegível na tela: a linha de origem identifica o projeto por identificador universal e não diz **quais** UDEs foram promovidos (achado A-01 da jornada J-07, severidade Alta) | **Alta** | 📝 registrado — é interface, e o dado está correto no domínio (`ReferenciaDeOrigem` tipada com ferramenta, projeto e nós) |

### 5.4 · Achados das avaliações heurísticas datadas (2026-09-06)

De `docs/jornadas/003-nuvem-de-conflito.md` (7 achados) e
`docs/jornadas/007-a-travessia.md` (3 achados) — os que continuam abertos:

| # | Achado | Severidade | Destino |
|---|---|---|---|
| J-07/A-01 | A linha de origem identifica o projeto por identificador universal em vez do **nome** da árvore, e não diz quais dois efeitos foram promovidos | **Alta** | 📝 registrado (= A-07 acima) |
| J-03/A-01 | A leitura das arestas concatena as frases das entidades sem tratar a pontuação (*"…alta taxa de conclusão., precisamos de…"*), e a visão de solução inteira é feita dessas leituras — o defeito aparece **sete vezes na mesma tela** | Média | 📝 registrado |
| J-07/A-02 | A nuvem derivada abre com as cinco entidades em texto de exemplo e **nada na tela diz** que a pessoa deve reescrevê-las | Média | 📝 registrado |
| J-07/A-03 | Não há caminho de volta: da nuvem não se abre a ARA de origem em um clique | Média | 📝 registrado |
| J-03/A-04 | O texto da injeção e a classificação aparecem grudados na visão de solução, sem separador | Baixa | 📝 registrado |
| J-03/A-06 | O vencimento da proposta aparece como instante absoluto, em formato do sistema e em inglês | Baixa | 📝 registrado |
| J-03/A-07 | Depois de confirmar, o diagrama mudado aparece **abaixo** da superfície de desfecho — quem não rolar pode não ver que a nuvem mudou | Baixa | 📝 registrado |

## 6 · TAIL:security — o passe, item a item

| Item | Como se verificou | Resultado |
|---|---|---|
| Nenhum SDK, chave ou prompt de provedor (ADR 0007) | grep sobre `apps/api/src/` e `apps/web/src/`; `CONFLICT_CLOUD_PROMPT` | ✓ `3` ocorrências, as três a denylist do snapshot; `0` para o prompt da linhagem |
| Geração sem parser — contrato ou nada | varredura AST no caminho da geração | ✓ `toc_api.dominio.geracao: 108 literal(is) de código; toc_api.dominio.nuvem: 182` examinados, nenhum parse de markdown |
| Falha fechada na geração | `pytest tests/dominio/test_resultado_de_geracao.py -v` | ✓ 12 formas de resultado torto recusadas, cada uma nomeando o motivo, com código estável (`VERSAO_DESCONHECIDA`, `FORA_DO_ESQUEMA`) |
| Recusar não escreve | `test_recusar_a_geracao_deixa_o_projeto_byte_a_byte_intacto` | ✓ comparação de **bytes** do estado serializado |
| Capability ausente esconde as mutadoras | `test_sem_capability_de_escrita_as_tres_mutadoras_do_m3_nao_existem` | ✓ somem do catálogo, não são recusadas depois |
| Quem só lê, só lê | `test_quem_so_le_alcanca_a_leitura_da_nuvem_e_e_recusado_em_toda_mutacao` (domínio) e `test_quem_so_le_abre_a_nuvem_e_e_recusado_em_toda_mutacao` (HTTP) | ✓ dentro dos `15 passed` e dos `18 passed` |
| Recusa deixa traço | `pytest tests/federacao/test_catalogo_m3.py -q -s` | ✓ `recusas registradas no traço: ['denied', 'denied', 'denied']` |
| Fronteira do agregado (a topologia indestrutível **de fora**) | `apps/api/tests/federacao/test_porta_dos_fundos_do_catalogo.py` | ✓ `len(intacta.entidades) == 5`, `len(intacta.arestas) == 7` depois da tentativa pelo executor federado |
| Isolamento por inquilino na nuvem | `test_o_isolamento_por_inquilino_vale_para_a_nuvem` | ✓ dentro dos `7 passed` do PostgreSQL real |
| Invariantes impostas **também pelo banco** | `test_o_banco_recusa_premissa_vazia_e_desafio_sem_justificativa` | ✓ — a regra não depende só do código da aplicação |
| Dado real de pessoa (ADR 0006) | `scripts/check-vazamento.sh` | ✓ `0` achados sobre `579` arquivos; o dilema da "Instituição Horizonte" é sintético e declarado como tal em `apps/api/tests/dominio/nuvem_sintetica.py` |

**Alcance declarado**: passe medido por quem executou a bateria; não substitui revisão
independente de segurança por terceiro em contexto fresco (**Dv-4**).

## 7 · TAIL:mutation — sabotar e ver reprovar

```text
$ scripts/tests/run-sabotagem.sh
── Sabotagem: quanto foi examinado ──
  portões cobertos: 10  ·  bases válidas aceitas: 10/10
  sabotagens declaradas: 61  ·  reprovadas pelo motivo certo: 61/61
  sabotagens de ambiente: 2  ·  recusadas pelo motivo certo: 2/2
$ echo $?
0
```

Deste ciclo, nominalmente: as **7** de `scripts/check-manifesto.sh` (o manifesto passou de 8
para 15 ações com as três do M3 e continua aceito pelo schema normativo com 0 erro), as **3**
de `scripts/check-raiz-do-agregado.sh` — que é o portão nascido do achado A-02, reproduzido
**nesta** ferramenta — e as **8** de `scripts/check-trava-otimista.sh`, que cobre `salvar_nuvem`
entre os 8 caminhos de escrita.

Dentro da suíte há ainda duas mutações embutidas que valem citar, porque não são de portão:
o corpus de formulação mede `códigos de aviso: 3; cobertos pelo corpus: 3` — heurística sem
caso no corpus não entra —, e os 12 casos parametrizados de resultado torto são, na prática,
doze mutações do payload da geração vistas serem recusadas uma a uma.

**O que não cobre**: mutação sobre as invariantes da topologia e sobre a referência
obrigatória da injeção à premissa, que é o que o `TAIL:mutation` do `tasks.md` deste ciclo
pede nominalmente. Dívida **Dv-3**.

## 8 · TAIL:gate — NÃO marcado, e o que aguarda o Product Steward

1. **Aceitar a linha 10 como dívida do ciclo 011** (A-04) ou reabrir o 007 para entregar a
   exportação sem perda.
2. **Ratificar a ressalva da linha 12** (A-05) — e, de preferência, mandar reescrever o
   critério **uma vez** para os ciclos 005, 006, 007 e 008.
3. **Aprovar as três ações governadas do M3** (`toc.generate_conflict_cloud`,
   `toc.suggest_assumptions`, `toc.suggest_injections`) no gate ação a ação que o ciclo 006
   nomeia — sem essa assinatura, o catálogo do produto está no ar sem aprovação registrada.
4. **Decidir o achado de severidade Alta A-07/J-07-A-01**: a rastreabilidade da origem existe
   no dado e está ilegível na tela.
5. **Responder os cinco `[DÚVIDA]` do Clarify** da spec.
6. **Aceitar as seis dívidas do §9** e **autorizar a promoção**.

## 9 · Dívidas declaradas, com dono

| # | Dívida | Por quê | Dono |
|---|---|---|---|
| **Dv-1** | `ART:contracts=yes` sem diretório de contratos, e `ART:data-model` sem motivo | Defeito de declaração no `specs/007-nuvem-de-conflito/plan.md`; o schema da geração existe **em código**, com 17 testes | construtor do ciclo 007 |
| **Dv-2** | Exportação sem perda (RF-33) — linha 10 da DoD | Alocada ao ciclo 011, como no 004 e no 008 | **ciclo 011** |
| **Dv-3** | Mutação sobre as invariantes da topologia e sobre a referência injeção → premissa (T-15) | As 61 sabotagens cobrem portões; estas são sobre funções de domínio | construtor do ciclo 007 |
| **Dv-4** | Passe de segurança em contexto fresco por **terceiro** | Maestro II: quem executa não verifica | revisor de segurança em contexto fresco |
| **Dv-5** | Tempo da recusa de proposta (< 500 ms) nunca medido | Não há medição de tempo em teste nenhum | construtor do ciclo 007 |
| **Dv-6** | A medição de RNF-05 do §4 é **ad-hoc**, não script versionado | O número é real; a reprodutibilidade por terceiro não está garantida | construtor do ciclo 007 |
| **Dv-7** | Sete achados de interface abertos nas duas jornadas (§5.4), um deles de severidade Alta | São código de produção da interface, e código de produção nasce por ciclo com teste que falha antes (P4) | ciclo de interface |

## 10 · Cauda

- **TAIL:review** — revisão independente em contexto fresco, com **7 achados numerados**
  (A-01 a A-07, §5) e **7 achados** abertos nas avaliações heurísticas datadas das jornadas
  J-03 e J-07 (§5.4). O achado central, **A-01**, é o laço da assistência que **não fechava na
  tela**: a pré-visualização mostrava o diff e oferecia só "Recusar", e a documentação da
  ausência dentro do próprio componente era a descrição do buraco, não o conserto. Corrigido
  pelo caminho que o padrão manda (ADR 0009), com prova de persistência entre **três
  aplicações diferentes** (`13 passed, 2 warnings in 8.47s`) e quatro casos de interface que
  fecham o laço. O **A-02** — a nuvem sumindo da leitura com `404` sobre um projeto vivo —
  foi reproduzido nesta ferramenta antes do conserto e fechado como classe. Um achado virou
  vermelho assumido na DoD (A-04) em vez de ser maquiado.
- **TAIL:security** — passe sobre 11 itens, **11 sem furo** (§6): nenhum SDK nem prompt de
  provedor, geração por contrato provada por varredura AST sobre 290 literais, 12 formas de
  resultado torto recusadas em falha fechada, recusa que deixa o projeto **byte a byte**
  intacto, capability ausente que **esconde** as três mutadoras, quem só lê recusado em toda
  mutação no domínio e no HTTP, recusa que deixa traço (`['denied','denied','denied']`), a
  topologia indestrutível também **de fora** do agregado, isolamento por inquilino no
  PostgreSQL real, invariantes impostas **também pelo banco**, e o dilema sintético sem um
  dado real de pessoa. **Alcance declarado**: passe, não revisão independente por terceiro
  (Dv-4).
- **TAIL:mutation** — `scripts/tests/run-sabotagem.sh` saiu **0**: `portões cobertos: 10 ·
  bases válidas aceitas: 10/10` e `sabotagens declaradas: 61 · reprovadas pelo motivo certo:
  61/61`. Deste ciclo são **7 + 3 + 8**: manifesto contra o schema normativo, raiz do agregado
  (o portão que nasceu do A-02) e trava otimista sobre os 8 caminhos de escrita, `salvar_nuvem`
  incluído. Dentro da suíte, duas mutações embutidas: `códigos de aviso: 3; cobertos pelo
  corpus: 3` e os 12 payloads tortos recusados um a um. O que falta está em §7 e é a dívida
  Dv-3.
- **TAIL:gate** — **NÃO marcado, de propósito.** A DoD fechou **13 verdes, 1 com ressalva e 2
  vermelhas**. E há um item substantivo esperando: as três ações governadas do M3 estão no
  catálogo do produto **sem a aprovação ação a ação** que o ciclo 006 exige. Os seis itens que
  aguardam assinatura estão em §8. Quem executou não aprova o que executou (Maestro II).

## 11 · Re-execução no fechamento (2026-09-06, 05:42Z–05:54Z)

A bateria das seções acima é da janela **04:50Z–05:41Z**. O repositório continuou sendo
construído por outro lote (o **M6**, spec 009) durante todo o tempo, então o que é caro foi
**re-executado no fechamento**. O que mudou está aqui, e não escondido.

| Comando | Saída (colada) | Código |
|---|---|---|
| `cd apps/api && pytest -q` | `1273 passed, 12 warnings in 199.26s (0:03:19)` | `0` |
| `cd apps/web && npx vitest run` | `Test Files  1 failed \| 19 passed (20)` · `Tests  1 failed \| 218 passed (219)` | `1` |
| `scripts/check-caminhos.sh` (05:53Z) | `arquivos varridos: 125` · `caminhos conferidos: 1138 · isentos declarados: 383 · entregas futuras declaradas: 100 · moldes ignorados: 19` · `✓ todo caminho citado entre crases existe.` | `0` |
| `scripts/check-links.sh` (05:53Z) | `checked: 468` · `✓ every relative link resolves.` | `0` |
| `scripts/tests/run-sabotagem.sh` (05:53Z) | `portões cobertos: 10 · bases válidas aceitas: 10/10` · `sabotagens declaradas: 61 · reprovadas pelo motivo certo: 61/61` · `sabotagens de ambiente: 2 · recusadas pelo motivo certo: 2/2` | `0` |
| `scripts/evidencia.sh` (05:46Z) | `Portões executados: 17 · verdes: 12 · vermelhos: 5.` | `1` |
| `scripts/check-conformance.sh 007` | ver o bloco de conformidade acima | `1` |

**Os cinco vermelhos do agregador, atribuídos um a um.** Nenhum deles vem deste fechamento
documental, e quatro deles vêm do mesmo lugar: o gerador de capturas do M6 estava rodando
**enquanto o agregador rodava**. A prova é a contagem de imagens em disco, amostrada de 25 em
25 segundos:

```text
05:46:27Z pngs=36 manifesto=nao
05:46:52Z pngs=36 manifesto=sim
05:47:17Z pngs=11 manifesto=nao
05:48:07Z pngs=40 manifesto=nao
05:50:02Z pngs=52 manifesto=sim
05:51:02Z pngs=3  manifesto=nao
05:52:02Z pngs=52 manifesto=sim
```

| Portão vermelho | Causa | Dono |
|---|---|---|
| `check-caminhos.sh` e `check-links.sh` | o `docs/jornadas/README.md` cita, na linha 42, o manifesto das capturas — num instante em que o gerador o tinha apagado. **Re-executados às 05:53Z com o disco estável: os dois voltaram a 0** (linhas 3 e 4 da tabela acima) | transitório, do lote em curso |
| `check-jornadas.sh` | `✗ 16 problema(s) na documentação viva das jornadas` — dezesseis capturas órfãs numa pasta de capturas do ciclo 009 (cinco passos de focalização), jornada cujo **documento ainda não existe**. É a Iron Law da skill `living-journey` funcionando: captura sem jornada que a cite é ficção pela metade | construtor do M6 (spec 009) |
| `check-evidencia-colada.sh` | `✗ 7 problema(s): saída colada que o comando não reproduz mais` — os sete são números envelhecidos em documentos que **não são deste lote**: `docs/jornadas/README.md` e o `CHANGELOG.md` dizem 36 capturas e o comando devolve `52`; o portão de jornadas dizia `80` verificações e devolve `96`; o `docs/adr/0012-modulo-m4-suficiencia-compartilhada-e-referencia-como-agregado.md` diz `34` códigos próprios e o registro tem `39` | construtor do M6, ao fechar o lote dele |
| `check-trava-da-proposta.sh` | `✗ os adaptadores têm 9 método(s) salvar* e este portão conhece 8` — `salvar_focalizacao` entrou sem ser classificado | construtor do M6 |

**Consequência para a leitura deste relatório, dita sem rodeio.** Os denominadores das
jornadas citados nas seções acima (`capturas em disco: 36`, `verificações executadas: 80`)
eram verdadeiros às 04:50Z e **deixaram de ser** durante a redação: às 05:53Z são `52` e `96`.
Não foram reescritos nas tabelas porque a tabela diz a que hora mediu; foram **corrigidos
aqui**, que é o que a regra R1 pede de quem cola saída — dizer o comando, a hora e o que ele
devolve agora.


## Veredito

**Executado e medido; NÃO fechado.** A Nuvem de Conflito existe com a topologia que o método
manda e que a linhagem nunca soube guardar: cinco entidades e sete arestas criadas na origem e
**sem caminho para excluir**, premissa como entidade de primeira classe, injeção que não nasce
sem premissa viva, e a visão de solução com as **sete** posições — o defeito do v3, que
renderizava cinco, virado caso de teste. A geração assistida entra por contrato validado e
não por parser, recusar deixa o projeto **byte a byte** intacto, e a costura ARA → NC
atravessa o banco. O que está vermelho — a exportação sem perda — está vermelho **aqui**, com
dono e ciclo. O gate humano é o próximo passo, e neste ciclo ele tem nome: aprovar as três
ações governadas.
