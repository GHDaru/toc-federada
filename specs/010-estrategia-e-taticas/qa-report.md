# QA Report 010 — Estratégia & Táticas (M5)

> Siglas, uma vez neste documento: **QA** — *Quality Assurance* (garantia de qualidade) ·
> **DoD** — *Definition of Done* (Definição de Pronto) · **ADR** — *Architecture Decision
> Record* (Registro de Decisão Arquitetural) · **TOC** — Teoria das Restrições · **S&T** —
> Estratégia & Táticas (*Strategy & Tactics*) · **M1** — Núcleo de Diagramas Lógicos ·
> **M5** — o módulo Estratégia & Táticas · **IA** — inteligência artificial · **SDK** —
> *Software Development Kit* · **APH** — Aplicação ↔ Harness · **HTTP** — *HyperText
> Transfer Protocol* · **SQL** — *Structured Query Language* · **UI/UX** — interface /
> experiência de usuário · **RF/RN/RNF/RI** — requisito funcional / regra de negócio /
> requisito não funcional / requisito de interface · **p95** — percentil 95 · **CI** —
> integração contínua.

**Execução: 2026-09-06.** Toda célula abaixo foi preenchida **depois** do comando rodar,
com a saída colada e não transcrita (R1), e com o denominador que o próprio comando
imprimiu (R2). Onde o comando da spec citava um caminho que não existe com aquele nome no
repositório (a spec foi escrita antes de o serviço nascer, e falava em uma árvore `backend/…`,
`frontend/…` e `tests/domain/…` que este repositório não tem), o caminho **real** está dito ao lado — e não silenciosamente
trocado.

Ambiente: `apps/api` com `PATH` incluindo `.venv/bin`, e
`DATABASE_URL=postgresql+psycopg://toc@/toc_federada?host=/var/run/postgresql&port=5433`
— o PostgreSQL real do ambiente, nunca SQLite.

## Pré-condições de abertura (T-01)

| Pré-condição | Verificado em | Evidência (saída colada) | Estado |
|---|---|---|---|
| Ciclo 004 promovido (o `Projeto` do M1 existe — única dependência técnica) | `apps/api/src/toc_api/dominio/projeto.py` | o agregado existe com `sob_a_raiz`, `versao_lida` e `confirmar_gravacao`; `scripts/check-raiz-do-agregado.sh` → `✓ operação só pela raiz: 8 guardas, 7 raízes, 214 arquivos varridos.` | ✓ (o **gate humano** do 004 é do Product Steward e não do agente) |
| [DÚVIDA] 1 (categoria da linhagem) respondida antes do `data-model.md` | [`../../docs/adr/0014-categoria-portada-e-transicao-de-status-livre-na-snt.md`](../../docs/adr/0014-categoria-portada-e-transicao-de-status-livre-na-snt.md) | ADR 0014 §1: portada como **rótulo opcional** de seis valores; `docs/adr/README.md` e `docs/records/decisoes.jsonl` com a linha `adr-0014` (`✓ todo ADR está no índice e no registro`) | ✓ decidida e registrada |
| [DÚVIDA] 2 (transições de status) respondida | mesmo ADR, §2 | livre entre os quatro, com três recusas nomeadas | ✓ decidida e registrada |
| [DÚVIDA] 3 (raízes múltiplas) | `apps/api/tests/dominio/test_numeracao.py::test_multiplas_raizes_sao_permitidas_e_numeram_em_sequencia` | permitidas, como a spec assumiu (L-05) — coberto por teste | ✓ como assumido |
| [DÚVIDA] 4 (tática obrigatória) | `apps/api/tests/dominio/test_snt.py::test_o_passo_exige_estrategia_e_admite_tatica_vazia` | estratégia obrigatória, tática como pendência — como a RF-11 assume | ✓ como assumido |
| [DÚVIDA] 5 (ux da árvore no ciclo 002) | `specs/002-prototipo-de-interfaces/ux-design.md` | o protótipo do 002 **não** cobriu a árvore hierárquica com renumeração | ✗ **`ART:ux-design` continua `no`, e a consequência está em *Pendências*** |
| Os 5 `[DÚVIDA]` **confirmados** pelo Product Steward | — | — | **pendente** — matéria do `TAIL:gate`, que não está marcado |

## DoD — as 16 linhas da spec, com comando, saída colada e "quanto examinou"

| # | Critério | Comando executado | Saída (colada) | Examinou | Código |
|---|---|---|---|---|---|
| 1 | Domínio do M5 puro, offline | `pytest tests/dominio/test_snt.py -p no:cacheprovider -q` + `lint-imports` (a spec dizia `tests/domain/…`, pasta que não existe aqui) | `32 passed in 0.09s` · `Contracts: 3 kept, 0 broken.` | 32 testes de domínio da S&T · 3 contratos sobre `Analyzed 121 files, 705 dependencies` | `0` |
| 2 | Numeração derivada e determinística (RN-01) | `pytest tests/dominio/test_numeracao.py -v` | `10 passed in 0.09s` | 10 testes: raízes `1..n`, prefixo do pai, `1.1.3`, determinismo entre duas execuções, árvore vazia, múltiplas raízes | `0` |
| 3 | Renumeração da subárvore ao inserir/remover/mover | `pytest tests/dominio/test_numeracao.py -k "renumerar or propriedade"` | `propriedade local==total: 200 árvores geradas, 1849 passos numerados, 0 divergências` · `3 passed, 7 deselected in 0.08s` | 200 árvores geradas com semente fixa · 1849 passos numerados · 0 divergências | `0` |
| 4 | Número nunca é entrada (RF-06) | `grep -rn "numero\|stepNumber" apps/api/src/toc_api/aplicacao/snt.py apps/web/src/telas/TelaDaSnT.tsx apps/web/src/componentes/snt/ \| grep -iE "input\|request\|form\|<input\|campo" \| wc -l` **e** o teste que lê o OpenAPI publicado | `0` · `rotas do M5 examinadas: 11 · esquemas de entrada: 8 · campos de número encontrados: 0` | 3 alvos de código · 11 rotas e 8 esquemas de entrada do OpenAPI | `0` |
| 5 | As três premissas persistidas e regras de pendência | `pytest tests/dominio/test_premissas_do_passo.py -q` + a ida e volta ao banco | `12 passed in 0.08s` · integração: `passos gravados=7 · relidos=7 · numeração relida=[…]` | 12 testes de domínio · 7 passos gravados e relidos contra o PostgreSQL real | `0` |
| 6 | Árvore estrita: sem ciclo, um pai (RN-04) | `pytest tests/dominio/test_snt.py -k "arvore_estrita or propria_subarvore"` | `2 passed, 30 deselected in 0.07s` | 2 de 32 — mover para a própria subárvore recusado, e nenhuma aresta no projeto | `0` |
| 7 | Excluir subárvore não toca no resto (RN-05) | `pytest tests/dominio/test_snt.py -k "exclusao or excluir"` | `4 passed, 28 deselected in 0.08s` — inclui `test_exclusao_subarvore_remove_exatamente_a_subarvore_e_nao_toca_no_resto`, que compara os passos de fora **campo a campo** | 4 de 32 · o defeito `mockApiService.ts:521` como caso de teste | `0` |
| 8 | Status com evento (RN-03) | `pytest tests/dominio/test_status_do_passo.py -k transicoes -s` | `transições entre valores distintos examinadas: 12 · recusadas: 0` · `1 passed, 10 deselected in 0.09s` | 12 transições (4×3) · o arquivo inteiro tem 11 testes | `0` |
| 9 | Pendências e contagens por função pura | `pytest tests/dominio/test_pendencias.py -k arvore_recem -s` | `passos examinados=7 · pendências=9 · resumo={'passos': 7, 'pendencias': 9, 'sem_premissa_de_necessidade': 6, 'sem_premissa_de_suficiencia': 3, 'sem_tatica': 0, …}` | 7 passos examinados — **a saída diz o denominador** (R2) | `0` |
| 10 | Exportação sem perda; numeração deriva na importação (RF-21) | `pytest tests/dominio/test_snt.py -k "exportacao or importacao" -s` (a spec dizia `tests/application/…`, pasta que não existe aqui) | `documento com 7 passos · 2278 bytes` · `números originais=['1','1.1','1.1.1','1.1.2','1.2','1.2.1','1.3'] · importados=[idem]` · `2 passed, 30 deselected` | 7 passos na ida e na volta · a palavra `numero` **não aparece** no documento | `0` |
| 11 | Toda mutação nova com traço | `pytest tests/aplicacao/test_casos_de_uso_da_snt.py -k span` | `6 passed, 10 deselected in 0.13s` | 6 testes de span: adicionar (com o número), excluir subárvore (com a contagem), mover (números antes/depois), status (vocabulário fechado), a recusa marcada como erro, e o span que **não** carrega o texto da estratégia | `0` |
| 12 | Sem SDK, chave, prompt ou ação de catálogo no módulo | `grep -rniE "genai\|openai\|anthropic\|api[_-]?key" <os 5 arquivos do M5> \| wc -l` **e** `grep -rn "toc\." apps/api/src/toc_api/dominio/federacao/catalogo.py \| grep -c snt` | `0` · `0` | 5 arquivos do módulo · 16 ações do catálogo varridas pelo teste `test_nenhuma_acao_do_catalogo_pertence_a_snt` (`ações no catálogo: 16 · ações da S&T: 0 []`) | `0` |
| 13 | Desempenho da árvore e do mover (RNF-04) | medição da jornada viva, contra o serviço real | `desempenho (RNF-04): abrir 100 passos em 5 níveis — p95 10.7 ms sobre 20 amostras (alvo < 1000 ms) · mover subárvore de 20 passos — 176 ms (alvo < 500 ms)` | 100 passos em 5 níveis · 20 amostras de abertura · 1 mover de subárvore de 20 | `0` |
| 14 | Jornada viva de três níveis | `scripts/check-jornadas.sh` + `ls docs/jornadas/capturas/011-estrategia-e-taticas/ \| wc -l` | `jornadas examinadas: 7 … capturas em disco: 81 · citações de imagem: 81 … verificações executadas: 176 · heurísticas datadas: 7/7 · comandos de regeneração: 7/7` · `12` | 12 capturas da J-011 · 81 no repositório · 176 verificações | `0` |
| 15 | Conformidade do ciclo | `scripts/check-conformance.sh 010` | ver *Portão vermelho declarado*, abaixo | 1 ciclo · 5 artefatos condicionais · 4 itens de cauda | `1` (o portão é consultivo; o `✗` é **lido**, não ignorado) |
| 16 | Caminhos e links | `scripts/check-caminhos.sh` · `scripts/check-links.sh` | `arquivos varridos: 137 · caminhos conferidos: 1271 · isentos declarados: 466` · `checked: 601` | 1271 caminhos entre crases · 601 links relativos | `0` · `0` |

## Portões nomeados do roadmap (ciclo 010)

| Portão | Como se verificou | Evidência colada |
|---|---|---|
| **Teste de renumeração da subárvore** (inserir/remover renumera corretamente) | `apps/api/tests/dominio/test_numeracao.py` e `test_snt.py`: a renumeração local é comparada com o recálculo total sobre árvores geradas, e a árvore sintética exercita inserir no meio, mover entre pais e excluir | `propriedade local==total: 200 árvores geradas, 1849 passos numerados, 0 divergências` · na jornada, no build real: `renumeração após o mover: 1, 1.1, 1.1.1, 1.1.2, 1.2, 1.2.1, 1.3 → 1, 1.1, 1.1.1, 1.2, 2, 2.1, 2.2` |
| **As três premissas persistidas e exibidas por nó** | ida e volta contra o PostgreSQL real (`test_snt_no_postgres.py`) e a ficha do passo na tela, com a leitura dirigida montada no servidor | `7 passed in 5.44s` (integração) · `12 passed` (domínio das premissas) · captura `05-leitura-dirigida-das-tres-premissas.png` |
| **S&T sintética de três níveis, com captura** | `docs/jornadas/011-estrategia-e-taticas.md`, 12 capturas geradas pelo script versionado a partir do build real | `árvore com 7 passos em 3 níveis: 1, 1.1, 1.1.1, 1.1.2, 1.2, 1.2.1, 1.3` · corrida inteira: `81 captura(s), 13311234 bytes, 0 falha(s), 96.4s` |

## Migração 0009 — `upgrade` **e** `downgrade`, medidos

```text
$ TOC_DB_SCHEMA=teste_dg_… alembic upgrade head
tabelas snt: 2
$ alembic downgrade 0008
tabelas snt: 0
índices snt: 0
```

O ciclo `upgrade → downgrade → upgrade` roda num esquema descartável e não deixa resíduo:
duas tabelas (`snt_arvore`, `snt_passo`) e três índices sobem juntos e descem juntos. E a
coluna que **não** existe é medida:

```text
$ pytest tests/integracao/test_snt_no_postgres.py -k "numeracao_nao" -s
colunas das tabelas do M5 (13): ['meta_global', 'projeto_id', 'categoria', 'estrategia',
 'no_id', 'ordem', 'pai_id', 'premissa_necessidade_ao_pai', 'premissa_paralela',
 'premissa_suficiencia_dos_filhos', 'projeto_id', 'status', 'tatica']
```

Treze colunas, e nenhuma com "numero" no nome (RN-01).

## `TAIL:mutation` — a suíte sabe reprovar?

```text
$ scripts/tests/mutacao-m5.sh
── Mutação do M5: a suíte da árvore de Estratégia & Táticas sabe reprovar? ──
  alvo: apps/api/src/toc_api/dominio/snt.py
  suíte: 5 arquivos de teste de domínio
  ✓ morta      numeracao-comeca-em-zero  (função: numeracao) — 23 failed
  ✓ morta      numeracao-sem-prefixo-do-pai  (função: numeracao) — 23 failed
  ✓ morta      numeracao-nao-desce-para-os-filhos  (função: numeracao) — 14 failed
  ✓ morta      renumerar-ignora-o-pai-afetado  (função: renumerar) — 51 failed
  ✓ morta      renumerar-nao-descarta-o-que-saiu  (função: renumerar) — 1 failed
  ✓ morta      mover-aceita-a-propria-subarvore  (função: mover_passo) — 1 failed
  ✓ morta      exclusao-tira-so-o-passo  (função: excluir_subarvore) — 4 failed
  ✓ morta      exclusao-mantem-so-o-excluido  (função: excluir_subarvore) — 2 failed

  mutações aplicadas: 8  ·  mortas: 8  ·  sobreviventes: 0
  funções cobertas: numeracao · renumerar · mover_passo · excluir_subarvore
  arquivo restaurado: sha256 confere (0e6a6b3d2fad2b33077171be4d978e6d39691358e5bc56916de80aa1451f2ab2)

✓ as 8 mutações morreram: a suíte do M5 reprova cada defeito que ela existe para ver.
$ echo $?
0
```

**A primeira execução tinha uma sobrevivente, e ela era um buraco real.** A mutação
`renumerar-nao-descarta-o-que-saiu` — trocar o filtro de `renumerar` por `dict(numeros)` —
passava por toda a suíte: `numero()` exige a ficha antes, e a ficha de um passo excluído já
não existe, então o número fantasma não era observável por ali. O mapa devolvido por
`numeros()`, porém, é público, e continuava carregando o número de passos que saíram da
árvore. O teste que faltava
(`test_a_numeracao_esquece_os_passos_que_sairam_da_arvore`) entrou junto, e a mutação
passou a morrer. **É o valor do TAIL:mutation em uma linha**: ele não confirmou o que já
sabíamos; ele achou o que não sabíamos.

## Suítes completas

Os **121 testes do M5**, juntos:

```text
$ (apps/api) pytest -q -p no:cacheprovider \
    tests/dominio/test_snt.py tests/dominio/test_numeracao.py \
    tests/dominio/test_premissas_do_passo.py tests/dominio/test_status_do_passo.py \
    tests/dominio/test_pendencias.py tests/aplicacao/test_casos_de_uso_da_snt.py \
    tests/contrato/test_http_snt.py tests/federacao/test_telas_do_m5.py \
    tests/integracao/test_snt_no_postgres.py
121 passed, 2 warnings in 15.04s
```

A suíte inteira do serviço, logo depois de o módulo fechar:

```text
$ (apps/api) pytest -q -p no:cacheprovider
1412 passed, 12 warnings in 163.42s (0:02:43)
```

O ciclo entrou com **1274** testes no serviço e essa execução fechou com **1412** (+138).

A interface:

```text
$ (apps/web) npx vitest run
 Test Files  25 passed (25)
      Tests  280 passed (280)

$ (apps/web) npm run typecheck
> tsc --noEmit          (sem saída — nenhum erro de tipo)

$ (apps/web) npm run build
dist/assets/index-gMAQeriT.js   340.29 kB │ gzip: 95.52 kB
✓ built in 332ms
```

A interface entrou com 269 testes e sai com **280** (+11).

### Uma execução posterior com 3 vermelhos que **não são deste lote** — dito, não escondido

Uma execução feita depois, às 22h, devolveu `3 failed, 1480 passed`. Os três estão em dois
arquivos que **não pertencem a este ciclo** e que foram criados por outro construtor
enquanto este relatório era escrito (carimbo de modificação `22:01` e `22:03`, minutos antes
da execução):

```text
FAILED tests/dominio/test_exportacao_consolidada.py::test_a_exportacao_nao_depende_da_ordem_em_que_o_repositorio_devolveu
FAILED tests/integracao/test_portabilidade_no_postgres.py::test_a_ida_e_volta_pelo_banco_preserva_o_conteudo
FAILED tests/integracao/test_portabilidade_no_postgres.py::test_o_projeto_importado_abre_pela_rota_da_ferramenta_dele
```

São a exportação consolidada e a portabilidade da **spec 011**, em construção **agora**: o
primeiro embaralha nós de uma Nuvem de Conflito e compara documentos; os dois de integração
percorrem `/toc/portabilidade`, rota que não existe neste lote. Os 121 testes do M5 passam
dentro dessa mesma execução, e nenhum dos três toca `snt`. **Não foram corrigidos aqui de
propósito**: mexer em arquivo que outro construtor está escrevendo neste minuto é a receita
de dois trabalhos perdidos — o achado fica registrado para quem os escreve, que é quem tem o
contexto deles.

### Execução de fechamento — os três vermelhos alheios já não existem

O construtor do ciclo 011 terminou o trecho dele, e a execução final deste fechamento (com
`alembic` no `PATH`, sem o qual as 102 fixtures de integração erram no `subprocess`) volta
inteira verde. É esta a execução que vale como evidência do fechamento:

```text
$ (apps/api) PATH=apps/api/.venv/bin:$PATH pytest -q
1483 passed, 14 warnings in 164.24s (0:02:44)

$ (apps/api) pytest -q -p no:cacheprovider  <os nove arquivos do M5>
121 passed, 2 warnings in 13.89s

$ (apps/web) npm run test
 Test Files  26 passed (26)
      Tests  290 passed (290)

$ scripts/tests/mutacao-m5.sh
  mutações aplicadas: 8  ·  mortas: 8  ·  sobreviventes: 0
  arquivo restaurado: sha256 confere (0e6a6b3d2fad2b33077171be4d978e6d39691358e5bc56916de80aa1451f2ab2)
```

Os **1483** do serviço e os **290** da interface incluem o que o ciclo 011 acrescentou
depois de este lote fechar — por isso são maiores que os 1412 e os 280 medidos acima, que
continuam sendo o número **deste** lote no momento em que ele fechou. Os 121 do M5 não se
mexeram, que é o que este relatório precisa afirmar.

## Portões do repositório (`scripts/evidencia.sh`)

```text
Portões executados: **17** · verdes: **17** · vermelhos: **0**.
```

Dois deles precisaram entrar na própria lista, porque as duas listas são **escritas à mão
de propósito** (derivar do código faria o portão concordar com quem esquecesse):

- `scripts/check-trava-otimista.sh` passou a conhecer **nove** caminhos de escrita
  (`salvar_snt` entrou no mesmo commit em que nasceu): `caminhos de escrita conferidos: 9
  declarados · 9 encontrados no adaptador`;
- `scripts/check-trava-da-proposta.sh` passou a conhecer **dez** métodos `salvar*`:
  `os dois adaptadores têm 10 método(s) salvar*, todos na lista` · `28 de 28 verificações`.

E a suíte de sabotagem continua provando que os portões sabem reprovar — com as duas
fixtures atualizadas para conterem `salvar_snt`, sem as quais elas reprovariam a própria
base válida:

```text
$ scripts/tests/run-sabotagem.sh
  portões cobertos: 11  ·  bases válidas aceitas: 11/11
  sabotagens declaradas: 70  ·  reprovadas pelo motivo certo: 70/70
  sabotagens de ambiente: 2  ·  recusadas pelo motivo certo: 2/2
✓ os 11 portões aceitam a base válida e reprovam as 70 sabotagens,
  cada uma pelo motivo que a tabela declara.
```

O décimo primeiro portão (`check-i18n.sh`) e as nove sabotagens dele **não são deste
ciclo** — entraram no repositório às 22h10, pelo ciclo 011, enquanto este relatório fechava.
Entram aqui porque a execução acima é a deste fechamento e o número tem de ser o que a
suíte devolveu, não o que este lote produziu.

## Conformidade APH mantida

```text
$ scripts/check-conformidade-aph.sh
  · persistência ......... postgres (exigida: postgres)
  · migração (alembic) ... 0009
  · natureza do turno .... ENLATADO E DETERMINÍSTICO — não há provedor de modelo
Veredito: APTO nos itens verificáveis — 11/11 verificados; 12 itens a autodeclarar.
```

O M5 **não muda a fronteira**: nenhuma ação de catálogo nasceu aqui (INT-04), e as quatro
telas novas entram no registro com `ai_visible` campo a campo:

```text
$ pytest tests/federacao/test_telas_do_m5.py -s
ações no catálogo: 16 · ações da S&T: 0 []
telas no registro: 16 · do M5: ['toc.snt_acompanhamento', 'toc.snt_arvore', 'toc.snt_passo', 'toc.snt_tabela']
telas do M5 examinadas: 4 · anunciando SUBMIT: 0
campos examinados: 29 · texto de pessoa visível: 0 []
campos visíveis em toc.snt_passo: ['categoria', 'filhos', 'numero', 'premissas_preenchidas', 'projeto_id', 'status']
5 passed in 0.09s
```

## Medições registradas (RNF-04)

| Métrica | Alvo | Valor medido | Fonte |
|---|---|---|---|
| Abrir árvore S&T (100 passos, 5 níveis) — p95 | < 1 s | **10,7 ms** (20 amostras; mediana 9,8 ms) | `docs/jornadas/capturas/manifesto.json` → `medidas.snt.desempenho`, escrito pela corrida das capturas |
| Mover subárvore de 20 passos (renumeração incluída) | < 500 ms | **176,0 ms** | idem |

**Limite declarado da medição**: ela mede a rota que a interface chama, e **não** o tempo
de pintura do navegador. A folga na abertura é de duas ordens de grandeza, o que mantém o
alvo de pé com o custo da renderização somado — mas o número da tela precisa ser medido na
tela, e não foi.

## Portão vermelho declarado — `scripts/check-conformance.sh 010`

```text
$ scripts/check-conformance.sh 010
• 010-estrategia-e-taticas
    ✓ Constitution Check complete (8/8)
    · acceptance-criteria checkboxes: not checked below cycle 45
    ✗ research: declared ART:research=no with no reason — a declaration without a why is silence
    ✗ data-model: declared ART:data-model=yes with no reason — a declaration without a why is silence
    ✓ contracts: declared and present
    ✗ ux-design: declared ART:ux-design=no with no reason — a declaration without a why is silence
    ✓ TAIL:review evidence: não executada**, e não pode ser executada por quem const
    ✓ TAIL:security evidence: não executada**, pelo mesmo motivo. O que já está medid
    ✓ TAIL:gate evidence: NÃO marcado, de propósito.** É o Product Steward quem a
──
cycles checked: 1
✗ mutation floor 55 is above the newest cycle 012 — TAIL:mutation was charged to nobody.
✗ declared-absence floor 61 is above the newest cycle 012 — 'pendente' would pass as evidence everywhere.
✗ the method did not survive into the artifacts of at least one cycle.
```

Sobraram **cinco `✗`, e o ciclo 009 — já fechado — devolve exatamente os mesmos cinco**.
Os três primeiros são o **falso positivo já relatado** em
[`../../mensagens/006-para-maestro-colchete-anula-a-razao-do-artefato.md`](../../mensagens/006-para-maestro-colchete-anula-a-razao-do-artefato.md):
o `plan.md` **declara o porquê de cada artefato**, em prosa, na coluna "Por quê" da tabela;
o portão procura o motivo num formato que o modelo do método não produz. Os dois últimos são
**pisos do método** (ciclos 55 e 61), acima do ciclo mais novo deste repositório (012), e
valem igualmente para todos os ciclos daqui — inclusive os já fechados: o mesmo comando
sobre o ciclo 009 devolve os mesmos dois. Nenhum dos cinco é do M5, e nenhum foi contornado:
`contracts/` e `data-model.md` **passaram a existir** neste ciclo, e as três linhas de cauda
que o portão cobrava do `qa-report.md` estão abaixo.

## Achados deste ciclo (registrados, não escondidos)

Numerados para que a revisão independente possa referenciá-los um a um. Os cinco primeiros
apareceram **durante** a execução; os dois últimos, no lote de fechamento documental de
2026-09-06, que reexecutou os portões e leu este relatório contra o repositório.

| # | Achado | Onde apareceu | Desfecho |
|---|---|---|---|
| A-01 | A suíte de mutação do módulo devolveu **uma sobrevivente real** na primeira execução: uma mutação no domínio da S&T que nenhum teste matava | `scripts/tests/mutacao-m5.sh`, primeira corrida | o teste que faltava entrou junto; a segunda corrida deu `mutações aplicadas: 8 · mortas: 8 · sobreviventes: 0`. Uma suíte de mutação que nasce com zero sobreviventes normalmente é uma suíte que não sabota nada — esta sabotou |
| A-02 | A confirmação de exclusão prometia "dá para desfazer nesta sessão", e a tela **não cumpre**: o `useDesfazer` do M1 existe e só a tela da Árvore da Realidade Atual o usa | corrida de captura do build real (achado A-03 da jornada [J-011](../../docs/jornadas/011-estrategia-e-taticas.md)) | texto trocado por um aviso verdadeiro ("Esta exclusão ainda NÃO tem desfazer nesta tela"). O RF-20 fica como **dívida nomeada** — pendência 1 abaixo. Promessa falsa é pior que ausência declarada |
| A-03 | A spec do ciclo cita caminhos que este repositório não tem (`backend/…`, `frontend/…`, `tests/domain/…`): ela foi escrita antes de o serviço nascer | ao montar a tabela de DoD | **declarado no topo deste relatório**, com o caminho real ao lado de cada comando — nunca trocado em silêncio |
| A-04 | `scripts/check-conformance.sh 010` sai `1` com cinco `✗`, e **o ciclo 009, já construído, devolve exatamente os mesmos cinco** | fechamento do ciclo | três são o falso positivo já relatado em [`../../mensagens/006-para-maestro-colchete-anula-a-razao-do-artefato.md`](../../mensagens/006-para-maestro-colchete-anula-a-razao-do-artefato.md) (o portão procura a razão do artefato num formato que o modelo do método não produz) e dois são **pisos absolutos de ciclo** do método, acima do ciclo mais novo daqui. Nenhum é do M5, e nenhum foi contornado |
| A-05 | Quatro denominadores de portão cresceram entre a primeira corrida e a de fechamento (vazamento 647→678 arquivos, arquitetura 121→124 arquivos e 705→741 dependências, raiz do agregado 214→222, política 103→106) | comparação das duas corridas do agregador | **é o comportamento que a regra R2 pede**, não instabilidade: o ciclo 011 acrescentou código no intervalo. O número que vale é o da última corrida, e é ele que está na tabela |
| A-06 | Os números de portão colados neste relatório envelheceram de novo: eram **17 portões** e **61 sabotagens** no fechamento, e hoje são 19 e 76 | lote de fechamento documental (2026-09-06) | reexecutados e colados na seção *Reexecução no lote de fechamento documental*, abaixo — a corrida original fica onde está, com a data. Um relatório de ciclo é um registro datado: ele não se reescreve, ganha um apêndice |
| A-07 | A jornada [J-011](../../docs/jornadas/011-estrategia-e-taticas.md) deixou **três achados heurísticos sem correção** (A-04 atalho de teclado, A-05 página que cresce com ficha e painel abertos, A-06 rota fora da URL) | avaliação heurística datada da jornada | continuam **abertos e escritos**, não corrigidos: são código de produção, e código de produção nasce por ciclo com teste que falha antes (P4). O A-06 é o mesmo achado A-01 da J-02 — reincidência, e está dito como tal |

## Cauda

| Item | Executor (contexto fresco) | Achados | Evidência |
|---|---|---|---|
| `TAIL:review` | **não executada**, e não pode ser executada por quem construiu (Princípio II: quem executa não verifica). O que fica pronto para ela: os dois portões nomeados do roadmap com saída colada, as 16 linhas da DoD, e os quatro achados de UX da jornada | — | pendente |
| `TAIL:security` | **não executada**, pelo mesmo motivo. O que já está medido e a espera de conferência independente: `grep` de SDK/chave/prompt → `0` nos cinco arquivos do módulo; zero ações de catálogo (`ações da S&T: 0`); autorização fail-closed com 4 leituras e 8 escritas na `POLITICA`, e as 7 escritas recusadas para principal só-leitura (`escritas recusadas para principal só-leitura: 7 de 7`); isolamento por inquilino no PostgreSQL real; texto de usuário marcado camada não-confiável nas 4 telas (`texto de pessoa visível: 0`) | — | pendente |
| `TAIL:mutation` | **executada e reprodutível** — `scripts/tests/mutacao-m5.sh`, saída colada acima | **1 sobrevivente na primeira execução**, corrigida com o teste que faltava | `mutações aplicadas: 8 · mortas: 8 · sobreviventes: 0` |
| `TAIL:gate` | **NÃO marcado, de propósito.** É o Product Steward quem assina, e a assinatura inclui confirmar os cinco `[DÚVIDA]` (dois já decididos por ADR 0014) e as pendências abaixo | — | pendente |

Em forma de lista, para quem lê o registro linha a linha:

- **TAIL:review** — **não executada**, e não pode ser executada por quem construiu
  (Princípio II: quem executa não verifica). O que fica pronto para ela: os três portões
  nomeados do roadmap com saída colada, as 16 linhas da DoD, os quatro achados de UX da
  jornada e as três pendências declaradas abaixo.
- **TAIL:security** — **não executada**, pelo mesmo motivo. O que já está medido e espera
  conferência independente: `grep` de SDK, chave e prompt → `0` nos cinco arquivos do
  módulo; zero ações de catálogo (`ações da S&T: 0`); autorização fail-closed com 4
  leituras e 8 escritas na `POLITICA` e as 7 escritas recusadas para principal só-leitura;
  isolamento por inquilino verificado contra o PostgreSQL real; texto de usuário marcado
  camada não-confiável nas quatro telas (`texto de pessoa visível: 0`).
- **TAIL:mutation** — **executada e reprodutível**: `scripts/tests/mutacao-m5.sh`, 8
  mutações aplicadas, 8 mortas, 0 sobreviventes, com o `sha256` do arquivo conferido depois
  da restauração. A primeira execução tinha **uma sobrevivente real**, e o teste que faltava
  entrou junto.
- **TAIL:gate** — **NÃO marcado, de propósito.** É o Product Steward quem assina, e a
  assinatura inclui confirmar os cinco `[DÚVIDA]` (dois já decididos pelo ADR 0014) e
  aceitar, ou recusar, as três pendências declaradas abaixo.

## Pendências declaradas — o que **não** foi entregue

Nenhuma delas foi contornada, escondida ou renomeada. As três estão aqui porque a alternativa
seria uma caixa marcada sem testemunha.

1. **RF-20 — o desfazer de sessão não cobre as mutações da S&T.** O `useDesfazer` do M1
   existe (`apps/web/src/estado/useDesfazer.ts`) e hoje **só a tela da Árvore da Realidade
   Atual o usa**. A primeira versão da confirmação de exclusão dizia "dá para desfazer nesta
   sessão" — promessa que a tela não cumpre —, e o texto foi trocado por um aviso verdadeiro
   ("Esta exclusão ainda NÃO tem desfazer nesta tela — confira a contagem acima antes de
   confirmar"). A mitigação que existe é a **prévia com a contagem**, que acontece antes de
   qualquer escrita. Achado A-03 da jornada.
2. **RI-05 — mover por arrastar não foi entregue; o movimento é por comando explícito.** A
   pré-visualização da renumeração, que é a parte que a spec chama de essencial, **foi**
   entregue. O arrastar é o segundo degrau do corte de apetite declarado no `plan.md`, e ele
   não subiu.
3. **`ART:ux-design` continua `no`.** O protótipo do ciclo 002 não cobriu a árvore
   hierárquica, e o adendo de ux-design que o `plan.md` previa como condicional **não foi
   escrito**: as telas seguiram os padrões já desenhados de nó, ficha, tabela e painel, e a
   avaliação heurística datada da jornada faz o papel de conferência. Se o gate quiser o
   adendo, ele é trabalho do ciclo seguinte — está dito, não omitido.

## Evidência dos portões — `scripts/evidencia.sh`, saída colada

```text
Portões executados: **17** · verdes: **17** · vermelhos: **0**.

| Portão | Saída | Denominador (linha do próprio portão) |
|---|---|---|
| check-caminhos.sh | 0 | arquivos varridos: 137 · caminhos conferidos: 1271 |
| check-adrs-sucessao.sh | 0 | ADRs examinados: 14 · verificações executadas: 56 |
| check-rounds.sh | 0 | rounds examinados: 11 · conferências de campo: 77 |
| check-specs.sh | 0 | ciclos examinados: 12 · verificações: 628 |
| check-links.sh | 0 | checked: 601 |
| check-install.sh | 0 | método instalado e coerente |
| check-vazamento.sh | 0 | arquivos varridos: 678 · linhas varridas: 162668 |
| check-jornadas.sh | 0 | jornadas examinadas: 7 · capturas em disco: 81 · verificações: 176 |
| check-arquitetura.sh | 0 | contratos: 3 · Analyzed 124 files, 741 dependencies |
| check-raiz-do-agregado.sh | 0 | 8 guardas · 7 raízes · 222 arquivos varridos |
| check-trava-otimista.sh | 0 | 9 de 9 caminhos de escrita |
| check-trava-da-proposta.sh | 0 | 28 de 28 verificações · 12 caminhos classificados |
| check-evidencia-colada.sh | 0 | 33 afirmações · 37 ocorrências conferidas |
| check-manifesto.sh | 0 | 12 telas · 16 ações · 7 sabotagens repelidas |
| check-politica.sh | 0 | 106 arquivos de produção varridos |
| check-canal.sh | 0 | # tests 21 · # pass 21 · # fail 0 |
| check-conformidade-aph.sh | 0 | APTO — 11/11 verificados; migração 0009; persistência postgres |
```

O bloco inteiro, com a saída completa de cada portão, é o que `scripts/evidencia.sh`
imprime; a tabela acima é o recorte do denominador de cada um (R2). O código de saída do
agregador foi `0`. Os denominadores acima são os da execução de **fechamento**: quatro
deles cresceram entre a primeira corrida e esta (varredura de vazamento 647→678 arquivos,
arquitetura 121→124 arquivos e 705→741 dependências, raiz do agregado 214→222 arquivos,
política 103→106) porque o ciclo 011 acrescentou código ao repositório no intervalo. O
número que vale é o da última corrida, e é ele que está na tabela.

## Reexecução no lote de fechamento documental (2026-09-06)

> **Acréscimo, não reescrita.** A corrida de fechamento acima fica onde está, com os
> números que tinha: um relatório de ciclo é um registro datado. O que segue é a
> reexecução dos mesmos portões depois de o ciclo 011 e o lote de fechamento documental
> acrescentarem código e documento ao repositório — é o achado **A-06** desta seção de
> achados.

```text
$ scripts/evidencia.sh
Portões executados: 19 · verdes: 19 · vermelhos: 0.
$ echo $?
0

$ scripts/tests/run-sabotagem.sh
  portões cobertos: 12  ·  bases válidas aceitas: 12/12
  sabotagens declaradas: 76  ·  reprovadas pelo motivo certo: 76/76
  sabotagens de ambiente: 2  ·  recusadas pelo motivo certo: 2/2
$ echo $?
0
```

Eram **17 portões e 61 sabotagens** no fechamento deste ciclo; são **19 e 76** hoje. Os dois
portões novos (`check-i18n.sh` e `check-documentacao.sh`) e as 15 sabotagens novas vieram do
ciclo 011. A tabela completa, portão a portão e com o denominador que cada um imprimiu, está
no `qa-report.md` do ciclo 012, §11.4 —
[`../012-jornadas-e-autodeclaracao/qa-report.md`](../012-jornadas-e-autodeclaracao/qa-report.md).

E o portão de conformidade continua vermelho pelos mesmos motivos que esta seção já
declarava — nenhum deles do M5. Saída colada da reexecução:

```text
$ scripts/check-conformance.sh 010
── Conformance: did the method survive into the artifacts? ──
   (floor: cycle 42; older cycles carry declared debt — see the roadmap)
• 010-estrategia-e-taticas
    ✓ Constitution Check complete (8/8)
    · acceptance-criteria checkboxes: not checked below cycle 45
    ✗ research: declared ART:research=no with no reason — a declaration without a why is silence
    ✗ data-model: declared ART:data-model=yes with no reason — a declaration without a why is silence
    ✓ contracts: declared and present
    ✗ ux-design: declared ART:ux-design=no with no reason — a declaration without a why is silence
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

As três linhas de cauda aparecem `✓` porque **existe registro do estado delas** neste
arquivo — não porque tenham sido executadas. `TAIL:review`, `TAIL:security` e `TAIL:gate`
continuam abertas, e a seção *Cauda* diz isso por extenso.

## Veredito

**Entregue do lado do agente; não aprovado.** Os três portões nomeados do roadmap estão
cumpridos com saída colada, as 16 linhas da DoD estão medidas (15 verdes e a 15 lida como
falso positivo já relatado), os 17 portões do repositório estão verdes, as 61 sabotagens
continuam reprovando pelo motivo certo e as 8 mutações do módulo morrem.

O que este ciclo registra e a linhagem nunca registrou: **a regressão D-05 está desfeita, e
a decisão que a desfaz tem número** (ADR 0014). Caixa marcada não é testemunha — o
`TAIL:gate` fica em branco até o Product Steward assinar.

> **Os números deste parágrafo são os do fechamento do ciclo** (17 portões, 61 sabotagens) e
> continuam sendo o registro daquela data. A reexecução de 2026-09-06 devolve **19 portões
> verdes e 76 sabotagens**, e está na seção *Reexecução no lote de fechamento documental*,
> acima — com a saída colada. Nenhum dos dois conjuntos foi apagado: um relatório de ciclo
> ganha apêndice, não correção silenciosa.
