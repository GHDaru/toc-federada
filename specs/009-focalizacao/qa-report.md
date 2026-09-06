# QA Report 009 — Focalização (M6)

> Siglas, uma vez neste documento: **QA** — *Quality Assurance* (garantia de qualidade) ·
> **DoD** — *Definition of Done* (Definição de Pronto) · **ADR** — *Architecture Decision
> Record* (Registro de Decisão Arquitetural) · **TOC** — Teoria das Restrições · **M1** —
> Núcleo de Diagramas Lógicos · **M2** — Árvore da Realidade Atual (ARA) · **M3** — Nuvem
> de Conflito (NC) · **M4** — Árvores de Futuro e Implementação · **ARF** — Árvore da
> Realidade Futura · **APR** — Árvore de Pré-Requisitos · **AT** — Árvore de Transição ·
> **M6** — Focalização · **IA** — inteligência artificial · **SDK** — *Software
> Development Kit* · **APH** — Aplicação ↔ Harness · **HTTP** — *HyperText Transfer
> Protocol* · **SQL** — *Structured Query Language* · **UI/UX** — interface / experiência
> de usuário · **RF/RN/RNF/RI** — requisito funcional / regra de negócio / requisito não
> funcional / requisito de interface · **p95** — percentil 95 · **CI** — integração
> contínua.

**Execução: 2026-09-06.** Toda célula abaixo foi preenchida **depois** do comando rodar,
com a saída colada e não transcrita (R1), e com o denominador que o próprio portão imprimiu
(R2). Onde o comando da spec citava um caminho que não existe com aquele nome no
repositório, o caminho real está dito ao lado — e não silenciosamente trocado.

## Pré-condições de abertura (T-01)

| Pré-condição | Verificado em | Evidência (saída colada) | Estado |
|---|---|---|---|
| Ciclo 008 promovido (ARA, NC, ARF, APR e AT existem — a jornada tem para onde apontar) | `specs/008-arvores-de-futuro-e-implementacao/tasks.md` | `168:- [ ] TAIL:gate — Portão humano de merge com as evidências das 16 linhas da DoD, as` | ✗ **NÃO cumprida** — o M4 estava sendo construído **em paralelo** por outro construtor durante este ciclo. Consequência declarada abaixo, em *Pendências*. |
| ADR 0005 (escopo v1) inalterado | `docs/adr/0005-escopo-do-dominio-v1.md` | `3:- **Status**: Aceita` (sem `Superseded by`; `scripts/check-adrs-sucessao.sh` confirma `sucedidos declarados: 0`) | ✓ |
| 5 `[DÚVIDA]` do Clarify respondidos no gate | — | — | **pendente** — é matéria do `TAIL:gate`, que não está marcado |
| Decisão sobre o ux da jornada (`[DÚVIDA]` 5) registrada | `specs/009-focalizacao/ux-design.md` | documento escrito antes da UI, com papéis semânticos consumidos e introduzidos | ✓ (a **confirmação** é do gate humano) |

## DoD — as 16 linhas da spec, com comando, saída colada e "quanto examinou"

Ambiente das linhas 1–12: `apps/api`, `DATABASE_URL` apontando para o PostgreSQL real do
ambiente (nunca SQLite).

| # | Critério | Comando executado | Saída (colada) | Examinou | Código |
|---|---|---|---|---|---|
| 1 | Domínio do M6 puro, offline | `pytest tests/dominio/test_focalizacao.py -p no:cacheprovider -q` + `lint-imports` | `36 passed in 0.13s` · `Contracts: 3 kept, 0 broken.` | 36 testes de domínio · 3 contratos de arquitetura sobre `Analyzed 115 files, 642 dependencies` | `0` |
| 2 | Cinco passos fixos e ordenados (RN-01) | `pytest tests/dominio/test_focalizacao.py -k "ordem_canonica or ordem or reordenar or excluir_passo or adicionar" -q` | `6 passed, 30 deselected in 0.11s` | 6 de 36 testes do arquivo | `0` |
| 3 | Travessia dos cinco passos com estado herdado | `pytest tests/dominio/test_jornada_completa.py -q` | `8 passed in 0.11s` | 8 testes | `0` |
| 4 | Recomeçar reabre sem apagar histórico (RN-04) | `pytest tests/dominio/test_jornada_completa.py -k recomeco -q` | `3 passed, 5 deselected in 0.10s` | 3 de 8 | `0` |
| 5 | Inércia bloqueada (RN-05) | `pytest tests/dominio/test_heranca.py -q` | `15 passed in 0.13s` | 15 testes | `0` |
| 6 | Uma restrição vigente, um ciclo aberto (RN-02, RN-03) | `pytest tests/dominio/test_focalizacao.py -k "unicidade or um_ciclo or uma_restricao" -q` | `4 passed, 32 deselected in 0.11s` | 4 de 36 | `0` |
| 7 | Vínculo canônico e não-canônico (RN-06) | `pytest tests/dominio/test_vinculos.py -q` | `18 passed in 0.12s` | 18 testes | `0` |
| 8 | Vínculo validado no servidor (RNF-04) | `pytest tests/aplicacao/test_vinculos_borda.py -q` | `11 passed in 0.16s` | 11 testes | `0` |
| 9 | Sugestão nasce proposta; recusar deixa intacto (RF-19/RF-21) | `pytest tests/integracao/test_catalogo_m6.py -k "recusa or intacto" -q` | `2 passed, 4 deselected, 2 warnings in 4.38s` | 2 de 6 · contra o PostgreSQL real | `0` |
| 10 | Capability ausente esconde a mutadora | `pytest tests/integracao/test_catalogo_m6.py -k capability -q` | `2 passed, 4 deselected, 2 warnings in 3.87s` | 2 de 6 | `0` |
| 11 | Exportação sem perda (RF-18) | `pytest tests/dominio/test_export_focalizacao.py -q` | `11 passed in 0.11s` | 11 testes | `0` |
| 12 | Toda mutação nova com traço (P5) | `pytest tests/integracao/test_traco_m6.py -q` | `5 passed, 2 warnings in 10.35s` | 5 testes de traço | `0` |
| 13 | Sem SDK, chave ou prompt no produto (P7) | `grep -rniE "genai\|openai\|anthropic\|api[_-]?key" apps/api/src apps/web/src \| wc -l` | `3` — **as três são a *denylist* de sanitização**, em `apps/api/src/toc_api/dominio/federacao/snapshot.py:46,58,59` (`"api_key"`, `"apikey"` e o comentário que as explica): o oposto de uma violação. No código do M6 o mesmo grep devolve `0`. | 2 árvores de fonte · 3 ocorrências lidas uma a uma | `0` |
| 14 | Jornada viva com captura por passo (P6) | `ls docs/jornadas/capturas/009-cinco-passos-de-focalizacao/ \| wc -l` + `scripts/check-jornadas.sh` | `16` · `jornadas examinadas: 5 … capturas em disco: 52 · citações de imagem: 52 · verificações executadas: 114 · heurísticas datadas: 5/5 · comandos de regeneração: 5/5` | 16 capturas da J-09 · 52 no repositório · 114 verificações | `0` |
| 15 | Conformidade do ciclo | `scripts/check-conformance.sh 009` | ver *Portão vermelho declarado* abaixo — 4 `✗` restantes, **todos** do falso positivo relatado em `mensagens/006`, mais a cauda que ainda não tem evidência | 1 ciclo · 5 artefatos condicionais · 4 itens de cauda | `0` (o portão é consultivo; o `✗` é lido, não ignorado) |
| 16 | Caminhos e links | `scripts/check-caminhos.sh` · `scripts/check-links.sh` | `arquivos varridos: 132 · caminhos conferidos: 1213 · isentos declarados: 398` · `checked: 523` | 1213 caminhos entre crases · 523 links relativos | `0` · `0` |

## Portões nomeados do roadmap (ciclo 009)

| Portão | Como se verificou | Evidência colada |
|---|---|---|
| Teste percorre os cinco passos com estado herdado entre eles | `apps/api/tests/dominio/test_jornada_completa.py` — a análise sintética da Instituição Horizonte atravessa `identificar → explorar → subordinar → elevar → recomecar`, e cada passo lê o produto do anterior pelo mapa (RF-13) | `8 passed in 0.11s` |
| "Recomeçar" reabre sem apagar histórico | mesmo arquivo, `-k recomeco`: o ciclo fechado é comparado pelo **retrato de conteúdo** (`CicloDeFocalizacao.retrato()`) antes e depois do recomeço — não por contagem de linhas | `3 passed, 5 deselected in 0.10s` |
| Análise sintética atravessa os cinco passos com captura por passo | `docs/jornadas/009-cinco-passos-de-focalizacao.md`, 16 capturas geradas pelo script versionado a partir do build real | `52 captura(s), 8481359 bytes, 0 falha(s), 61.6s` (corrida inteira) · `check-jornadas.sh`: `verificações executadas: 114` |

## Suítes completas

```text
$ cd apps/api && python -m pytest -q
1274 passed, 11 warnings in 197.18s (0:03:17)

$ python -m pytest -q tests/dominio/test_focalizacao.py tests/dominio/test_jornada_completa.py \
    tests/dominio/test_heranca.py tests/dominio/test_vinculos.py tests/dominio/test_export_focalizacao.py \
    tests/aplicacao/test_casos_de_uso_da_focalizacao.py tests/aplicacao/test_vinculos_borda.py \
    tests/contrato/test_http_focalizacao.py tests/integracao/test_focalizacao_no_postgres.py \
    tests/integracao/test_catalogo_m6.py tests/integracao/test_traco_m6.py
169 passed, 2 warnings in 43.34s
```

169 dos 1274 testes são do M6 (mais a medição da RNF-05, abaixo). A linha de base antes
deste ciclo era **1070**.

```text
$ cd apps/web && npm run -s test
 Test Files  1 failed | 19 passed (20)
      Tests  1 failed | 218 passed (219)
```

**A única falha é pré-existente e não é deste módulo.** `apps/web/src/telas/registro.test.ts` compara
o registro de telas da interface com o manifesto; o `diff` acusa exatamente cinco telas
ausentes do lado da interface — `toc.apr_canvas`, `toc.apr_sequencia`, `toc.arf_canvas`,
`toc.at_canvas` e `toc.cadeia` —, todas do M4, que estava sendo construído em paralelo. As
**três telas do M6** (`toc.foco_jornada`, `toc.foco_passo`, `toc.foco_linha_do_tempo`) estão
nos dois lados e não aparecem no `diff`. Não foi corrigida aqui de propósito: é a fronteira
do outro construtor.

## Agregador de evidência e prova de que os portões sabem reprovar

```text
$ scripts/evidencia.sh ; echo $?
Portões executados: 17 · verdes: 17 · vermelhos: 0.
0

$ scripts/tests/run-sabotagem.sh ; echo $?
── Sabotagem: quanto foi examinado ──
  portões cobertos: 10  ·  bases válidas aceitas: 10/10
  sabotagens declaradas: 61  ·  reprovadas pelo motivo certo: 61/61
  sabotagens de ambiente: 2  ·  recusadas pelo motivo certo: 2/2
  cada sabotagem roda sobre uma cópia em /tmp/tmp.ixgY9uQSz3 — o repositório não é tocado

✓ os 10 portões aceitam a base válida e reprovam as 61 sabotagens,
  cada uma pelo motivo que a tabela declara.
0
```

Os portões que este ciclo **teve de estender** para continuar dizendo a verdade:

```text
$ scripts/check-trava-otimista.sh
  caminhos de escrita conferidos: 8 declarados · 8 encontrados no adaptador
  guardas `_gravar_projeto` encontradas: 8 de 8 caminhos de escrita
  ✓ o duplo em memória recusa a mesma escrita nos 8 caminhos

$ scripts/check-trava-da-proposta.sh
  ✓ os dois adaptadores têm 9 método(s) `salvar*`, todos na lista
✓ trava da proposta íntegra: 27 de 27 verificações em 7 arquivos,
  com 11 caminho(s) de escrita persistente classificado(s) e a reserva
  provadamente ANTES do efeito.

$ scripts/check-raiz-do-agregado.sh
✓ operação só pela raiz: 8 guardas, 6 raízes, 193 arquivos varridos.

$ scripts/check-manifesto.sh
  telas declaradas: 12
  ações declaradas: 16
✓ manifesto válido e as 7 sabotagens recusadas.
```

`salvar_focalizacao` entrou nas duas listas de caminhos de escrita **e** nas duas fixtures
de sabotagem correspondentes — um caminho novo que entra só na lista do portão faz a base
válida da sabotagem falhar, e foi o que aconteceu na primeira tentativa.

## Medições registradas (RNF-05)

```text
$ cd apps/api && python -m pytest tests/integracao/test_desempenho_do_mapa.py -q -s
RNF-05 · 5 ciclos · 30 vínculos · 40 leituras · mediana 9.2 ms · p95 11.5 ms · máximo 51.9 ms · passos no mapa 5
1 passed in 1.88s
```

| Métrica | Alvo | Valor medido | Fonte |
|---|---|---|---|
| Abrir o mapa da jornada (5 ciclos, 30 vínculos) — p95 | < 1 s | **11,5 ms** (mediana 9,2 ms; máximo 51,9 ms, em 40 leituras) | [`../../apps/api/tests/integracao/test_desempenho_do_mapa.py`](../../apps/api/tests/integracao/test_desempenho_do_mapa.py), contra o PostgreSQL real |

**O que esta medição NÃO mede**, dito e não escondido: não mede rede, serialização HTTP nem
navegador. Mede o caminho que o módulo controla — leitura do agregado pela porta mais o
mapa, que é função pura. O alvo da spec é do caminho inteiro; este é o piso dele.

## Portão vermelho declarado — `check-conformance.sh 009`

```text
$ scripts/check-conformance.sh 009 ; echo $?
── Conformance: did the method survive into the artifacts? ──
   (floor: cycle 42; older cycles carry declared debt — see the roadmap)
• 009-focalizacao
    ✓ Constitution Check complete (8/8)
    · acceptance-criteria checkboxes: not checked below cycle 45
    ✗ research: declared ART:research=no with no reason — a declaration without a why is silence
    ✗ data-model: declared ART:data-model=yes with no reason — a declaration without a why is silence
    ✓ contracts: declared and present
    ✗ ux-design: declared ART:ux-design=yes with no reason — a declaration without a why is silence
    ✓ TAIL:review evidence: não executada**, e não pode ser executada por quem const
    ✓ TAIL:security evidence: não executada**. O que já está medido e a espera de con
    ✓ TAIL:gate evidence: NÃO marcado, de propósito.** As 16 linhas da DoD fechara
──
cycles checked: 1
✗ mutation floor 55 is above the newest cycle 012 — TAIL:mutation was charged to nobody.
✗ declared-absence floor 61 is above the newest cycle 012 — 'pendente' would pass as evidence everywhere.
✗ the method did not survive into the artifacts of at least one cycle.
0
```

- Os três primeiros `✗` são **falso positivo do portão**, não ausência de razão: as razões
  têm 265, 401 e 343 caracteres, e são recusadas porque contêm o caractere `[` — de um link
  markdown e das referências `[DÚVIDA]`. Reproduzido, medido e relatado em
  [`../../mensagens/006-para-maestro-colchete-anula-a-razao-do-artefato.md`](../../mensagens/006-para-maestro-colchete-anula-a-razao-do-artefato.md).
  **As razões não foram encurtadas para agradar o portão**: apagar a citação para ficar
  verde é exatamente o comportamento que a mensagem denuncia, e contraria a regra R4 deste
  projeto.
- O `contracts` deixou de aparecer quando `specs/009-focalizacao/contracts/` passou a
  existir — esse era ausência real, e foi corrigido produzindo o artefato.
- Os `✓` de cauda dizem **"alguém escreveu o que aconteceu"**, e não "a etapa foi feita":
  as quatro caixas seguem **desmarcadas** em `tasks.md`, e o texto de cada linha na § Cauda
  diz por extenso que não foram executadas. Confundir as duas coisas seria a caixa marcada
  fazendo de testemunha.
- As duas últimas linhas (`mutation floor 55`, `declared-absence floor 61`) são a **dívida
  Dv-3 já declarada** deste repositório: os pisos de retroatividade do portão são absolutos e
  reprovam qualquer repositório recém-instalado, cujo ciclo mais novo é 012. Relatado em
  [`../../mensagens/002-para-maestro-pisos-absolutos-de-ciclo.md`](../../mensagens/002-para-maestro-pisos-absolutos-de-ciclo.md).

## Artefatos condicionais deste ciclo

| Artefato | Declarado | Produzido |
|---|---|---|
| `research.md` | `ART:research=no` | — (não há incógnita a resolver por experimento) |
| `data-model.md` | `ART:data-model=yes` | [`data-model.md`](data-model.md) |
| `contracts/` | `ART:contracts=yes` | [`contracts/rest-api.md`](contracts/rest-api.md) · [`contracts/acoes-catalogo.md`](contracts/acoes-catalogo.md) |
| `checklist.md` | `ART:checklist=no` | — (a DoD já é executável) |
| `ux-design.md` | `ART:ux-design=yes` | [`ux-design.md`](ux-design.md) |

Decisão material do ciclo:
[ADR 0013](../../docs/adr/0013-taxonomia-fechada-da-restricao-e-heranca-que-volta-a-mesa.md),
com o campo **"Princípios tocados"** preenchido e registrado em
`docs/records/decisoes.jsonl` por `scripts/record-decision.sh`.

## Achados deste ciclo (registrados, não escondidos)

| # | Achado | Onde apareceu | Desfecho |
|---|---|---|---|
| A-01 | O painel do passo guardava a ferramenta canônica **do passo em que foi montado**: navegar de `identificar` para `subordinar` deixava "vincular" desabilitado sem motivo | corrida de captura do build real (nenhum teste de unidade pegou — cada um monta o painel uma vez) | corrigido com `key={passo.tipo}`; documentado na jornada e no `ux-design.md` |
| A-02 | `_herdar` levava à mesa **todas** as decisões de um passo reaberto (3 onde a jornada esperava 2) | `apps/api/tests/integracao/test_traco_m6.py` | corrigido: herda só a decisão vigente; teste próprio + § 3 do ADR 0013 |
| A-03 | A lista de pendências do passo reusava o `aria-label` da decisão, e a consulta casava dois elementos | corrida de captura (falha da corrida, não do teste) | chave `foco.pendencias_do_passo` criada |
| A-04 | A migração nomeava as restrições `CHECK` já prefixadas, e o Alembic aplica a convenção de nomes por cima | primeira execução de `alembic upgrade head` | nomes encurtados; conferidos contra `pg_constraint` no banco real |
| A-05 | A base válida da sabotagem quebrou quando a lista do portão de trava cresceu | `scripts/tests/run-sabotagem.sh` | as duas fixtures de sabotagem ganharam `salvar_focalizacao` |
| A-06 | Evidência colada envelhecida em cinco documentos por efeito deste ciclo (capturas 36→52, ADRs 12→13, medida do canvas, contagem do §A.7) | `scripts/check-evidencia-colada.sh` | todas re-executadas e recoladas; as duas contagens do §A.7 **reapontadas** do ADR 0012 para o 0013, pelo mesmo precedente que o registro já carregava — corpo de ADR não se reescreve |
| A-07 | `check-conformance.sh` chama de "sem razão" 401 caracteres de razão, por causa de um `[` | fechamento deste ciclo | relatado em `mensagens/006`; **nada alterado** no texto das razões |
| A-08 | A pré-condição "ciclo 008 promovido" não estava cumprida | `specs/008-.../tasks.md`, `TAIL:gate` desmarcado | declarado aqui e em *Pendências*; a combinação com o M4 foi feita **pela porta e pelo tipo de ligação**, nunca pela implementação dele |

## Pendências (nada aqui está resolvido — é o que fica para o gate e para o próximo ciclo)

1. **`apps/web/src/telas/registro.test.ts` vermelho, pré-existente e do M4.** Cinco telas do
   manifesto sem par no registro da interface. É a fronteira do construtor paralelo e não
   foi tocada.
2. **A pré-condição "ciclo 008 promovido" não foi cumprida** (construção em paralelo). O M6
   se protegeu combinando pela porta (`RepositorioDeProjetos`) e pelo tipo de ligação
   (`TipoDeFerramentaVinculada`), nunca pela implementação do M4 — é por isso que a suíte de
   domínio do M6 roda offline. Ainda assim, a integração real dos vínculos depende do M4
   promovido.
3. **RF-18 (exportação sem perda) está implementado só da metade do M6.** A E1.4 do M1 — a
   exportação do projeto — **não existe ainda**: o único vestígio é a ação de catálogo
   `toc.exportar_projeto`. Este ciclo entregou o documento canônico do M6
   (`VERSAO_DA_EXPORTACAO = "toc.focalizacao/1"`), a ida e volta e as referências pendentes
   declaradas; a costura com o formato do M1 é do ciclo que entregar a E1.4.
4. **`mensagens/006` está aberta** e depende do repositório `GHDaru/maestro`. Enquanto ela
   não for respondida, `check-conformance.sh` mostra três `✗` que não são defeito deste
   ciclo — e essa leitura tem de ser feita por quem abrir o portão.
5. **Achados heurísticos A-03, A-04, A-07 e A-08 da jornada viva** continuam registrados na
   [`../../docs/jornadas/009-cinco-passos-de-focalizacao.md`](../../docs/jornadas/009-cinco-passos-de-focalizacao.md)
   sem correção neste lote: são código de produção, e código de produção nasce por ciclo com
   teste que falha antes (P4).

## Cauda

As quatro linhas abaixo estão **desmarcadas em `tasks.md`**, e o que segue não é evidência de
que foram feitas: é o registro de qual é o estado de cada uma no momento em que a construção
terminou. Quem executou não revisa (Princípio II).

- **TAIL:review** — **não executada**, e não pode ser executada por quem construiu. O que
  este ciclo deixa pronto para ela: os oito achados numerados A-01 a A-08 acima (dois deles
  **encontrados e corrigidos** durante a construção — o `<select>` que guardava o passo
  errado e a herança que levava à mesa uma decisão substituída), as cinco pendências da
  seção anterior e os dois portões nomeados do roadmap com a evidência colada. Os dois
  pontos que mais pedem olho de fora: a costura com o M4 (construído em paralelo, ver
  pendências 1 e 2) e a metade do RF-18 que depende da E1.4 do M1 (pendência 3).
- **TAIL:security** — **não executada**. O que já está medido e a espera de conferência
  independente: DoD 13 (nenhum SDK, chave ou prompt no produto — as três ocorrências do grep
  são a *denylist* de sanitização, lidas uma a uma), DoD 8 (vínculo validado no servidor com
  inquilino conferido, `11 passed`), DoD 10 (capability ausente **esconde** a mutadora,
  `2 passed`), DoD 9 (recusar deixa o estado serializado byte a byte intacto) e as três telas
  novas com `ai_visible` campo a campo — descrição da restrição, notas e decisão em rascunho
  marcadas **invisíveis** para a assistência, porque são texto de pessoa e não grandeza.
- **TAIL:mutation** — **não executada como passe dedicado**. O que existe hoje é a suíte de
  sabotagem do repositório, que saiu `0`: `portões cobertos: 10 · bases válidas aceitas:
  10/10` e `sabotagens declaradas: 61 · reprovadas pelo motivo certo: 61/61`. Deste ciclo
  saíram as duas fixtures atualizadas (`trava-otimista` e `trava-da-proposta`, com
  `salvar_focalizacao`), e a base válida **falhou na primeira tentativa** — prova de que a
  fixture não é decorativa. O que falta é o alvo que a própria tarefa nomeia: mutação sobre a
  ordem canônica, as duas unicidades, a imutabilidade do ciclo fechado e o bloqueio por
  herança pendente, com taxa e sobreviventes.
- **TAIL:gate** — **NÃO marcado, de propósito.** As 16 linhas da DoD fecharam com comando e
  saída colada, e os 17 portões do agregador estão verdes; ainda assim o gate tem matéria
  substantiva esperando assinatura humana: a pré-condição "ciclo 008 promovido" **não** foi
  cumprida (§ Pré-condições), os cinco `[DÚVIDA]` do Clarify seguem sem resposta registrada,
  e a ação governada `toc.suggest_constraint` entra no catálogo do produto sob o regime do
  ciclo 006, que exige aprovação **ação a ação**. Quem executou não aprova o que executou
  (Maestro II).

## Veredito

**Construção concluída; ciclo NÃO fechado.** As 16 linhas da DoD têm comando executado e
saída colada, os 17 portões do agregador estão verdes (`scripts/evidencia.sh` código `0`) e
as 61 sabotagens reprovam pelo motivo declarado. O que falta é o que **não pode** ser feito
por quem construiu: as quatro linhas da cauda. Caixa marcada não é testemunha, e as quatro
seguem desmarcadas.
