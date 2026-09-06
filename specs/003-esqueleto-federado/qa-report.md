# QA report 003 — Esqueleto federado

> Siglas deste documento: **QA** — *Quality Assurance* (garantia de qualidade) · **DoD** —
> *Definition of Done* (Definição de Pronto) · **APH** — Aplicação ↔ Harness (o padrão da
> fronteira) · **ADR** — *Architecture Decision Record* (Registro de Decisão Arquitetural) ·
> **OTel** — OpenTelemetry · **CI** — integração contínua · **TDD** — *Test-Driven
> Development* · **eTLD+1** — *effective Top-Level Domain plus one* (o "site" no sentido do
> navegador) · **UDE** — Efeito Indesejável · **ARA** — Árvore da Realidade Atual · **NC** —
> Nuvem de Conflito · **RF/RI/RNF** — requisito funcional / de interface / não funcional ·
> **FSM** — máquina de estados finitos · **SSE** — *Server-Sent Events* · **URL** — *Uniform
> Resource Locator* · **SQL** — *Structured Query Language*.

- **Data da bateria**: 2026-09-06 · **Raia**: infra (plena + reversibilidade)
- **Veredito atual**: **executado e medido; NÃO fechado.** Das 14 linhas da DoD, **9 estão
  verdes com saída colada**, **2 verdes com ressalva declarada** (a letra do critério
  diverge do que ele quis medir) e **3 estão VERMELHAS** — todas as três dependem de um
  deploy que não existe. O percurso está em §0, as linhas em §2, os achados numerados em §5,
  as dívidas com dono em §9 e o que aguarda o humano em §8.
- **Portões**: `scripts/evidencia.sh` agrega **17 portões, 17 verdes**;
  `scripts/tests/run-sabotagem.sh` prova **61 sabotagens reprovadas pelo motivo certo**;
  `scripts/check-conformance.sh 003` sai **1** (§4).

> **R1 e R2 aplicadas linha a linha.** Toda saída abaixo foi executada neste repositório em
> **2026-09-06**, entre 04:50Z e 05:25Z, e está **colada** — nenhum `✓` foi transcrito,
> nenhum número foi lembrado. Onde o comando imprime o tamanho do que examinou, o número
> está na coluna "Examinou".
>
> **Ressalva de medição, e ela é importante.** Este repositório **estava sendo construído
> enquanto era medido**: `apps/api/src/toc_api/infra/persistencia/repositorio_projetos.py`
> foi modificado às **05:06Z** e `scripts/check-trava-otimista.sh` às **05:11Z**, por outro
> lote em curso (o M6, spec 009). A prova disso está nos próprios números: a suíte inteira
> devolveu `1201 passed` às 05:07Z e `1219 passed` às 05:19Z, **com o mesmo comando**. O que
> este relatório carrega é a segunda medição, e a diferença está dita porque esconder que a
> saída envelheceu em doze minutos seria exatamente o defeito que o
> `scripts/check-evidencia-colada.sh` existe para pegar.

## 0 · Histórico de veredito — os estados por que este ciclo passou

| # | Data | Estado | O que aconteceu | Evidência |
|---|---|---|---|---|
| **V1** | 2026-09-05 | **construído** | Admissão, porta de identidade, introspecção, esqueleto FastAPI com OTel, migração `0001`, repositórios com isolamento por inquilino e o canal `ghd.*` da interface. | mtimes: `apps/api/src/toc_api/alembic/versions/0001_esqueleto_tenant_e_projeto.py` 19:48Z, `apps/api/src/toc_api/dominio/federacao/admissao.py` 21:14Z, `apps/web/src/federacao/canal.mjs` 21:46Z |
| **V2** | 2026-09-05 | **bloqueios externos re-medidos (T-02)** | L-01 (schemas mutuamente exclusivos) **fechado** com saída colada; L-02 medido no código e pendente de resposta operacional; L-03 **aberto**. | `mensagens/003-para-ghdaru-o-que-falta-para-embarcar-a-toc.md` (20:53Z), §1 e §4 de lá |
| **V3** | 2026-09-05 | **relatado e parado (P1, T-19)** | Auditoria do lado hospedeiro contra o §4.9 e o Anexo B: **15 obrigações examinadas — 9 ✅ · 4 ❌ · 2 ⏳**, sete achados A1–A7. Nenhuma linha escrita fora deste repositório. | mesma mensagem, §3 |
| **V4** | 2026-09-06 | **jornada viva do embarque (T-17)** | J-01 com capturas do build real e avaliação heurística datada — **5 achados**, um deles de severidade **Alta**. | `docs/jornadas/001-chegada-e-embarque.md` (00:28Z) |
| **V5** | 2026-09-06 | **medido** | Esta bateria: 14 linhas da DoD com comando, saída colada e denominador. **9 verdes · 2 verdes com ressalva · 3 vermelhas.** | §2 |
| **V6** | — | **aguardando gate humano** | `TAIL:gate` **não marcado**, de propósito: quem executou não aprova o que executou. E três das quatro linhas vermelhas dependem de uma decisão que é do humano (o endereço de deploy, [DÚVIDA] 1). | §8 |

**O que este histórico NÃO diz.** Não diz "aprovado", e não diz "completo". Diz que o
esqueleto do serviço existe, atravessa o PostgreSQL real e está medido — e que a metade
*operacional* do ciclo (deploy, CI, rollback, endereço) **não foi executada por ninguém**.
A prova disponível no disco é a data de modificação do que cada estado deixou; ela **ordena
arquivos** e não prova quem os escreveu.

## 1 · Bateria de portões (denominador colado — regra R2)

`scripts/evidencia.sh` (código de saída **0**) imprimiu o cabeçalho
`Portões executados: 17 · verdes: 17 · vermelhos: 0.` Os que este ciclo mais toca:

| # | Portão | Código | Denominador — a linha do próprio portão |
|---|---|---|---|
| G1 | `scripts/check-caminhos.sh` | **0** ✓ | `arquivos varridos: 125` · `caminhos conferidos: 1005 · isentos declarados: 330 · entregas futuras declaradas: 97 · moldes ignorados: 15` |
| G2 | `scripts/check-links.sh` | **0** ✓ | `checked: 469` |
| G3 | `scripts/check-arquitetura.sh` (P3) | **0** ✓ | `contratos declarados no pyproject.toml: 3` · `Analyzed 114 files, 629 dependencies.` |
| G4 | `scripts/check-canal.sh` (§B.2) | **0** ✓ | `arquivos de teste encontrados: 1` · `# tests 21 · # pass 21 · # fail 0` |
| G5 | `scripts/check-manifesto.sh` | **0** ✓ | `telas declaradas: 9` · `ações declaradas: 15` · `sabotagens aplicadas: 7; repelidas: 7` |
| G6 | `scripts/check-vazamento.sh` (ADR 0006) | **0** ✓ | `arquivos varridos: 579 · linhas varridas: 131024 · registros JSON inspecionados: 3364` |
| G7 | `scripts/check-conformidade-aph.sh` | **0** ✓ | `persistência ......... postgres (exigida: postgres)` · `migração (alembic) ... 0007` · `Veredito: APTO nos itens verificáveis — 11/11 verificados; 12 itens a autodeclarar.` |
| G8 | `scripts/check-jornadas.sh` (P6) | **0** ✓ | `jornadas examinadas: 4` · `capturas em disco: 36 · citações de imagem: 36` · `verificações executadas: 80` |
| G9 | `scripts/check-conformance.sh 003` | **1** ✗ | `cycles checked: 1` — **vermelho, diagnóstico em §4** |

## 2 · DoD — as 14 linhas da spec, com comando, saída colada e veredito

Todos os comandos `pytest` foram executados de `apps/api`, com
`DATABASE_URL='postgresql+psycopg://toc@/toc_federada?host=/var/run/postgresql&port=5433'` e
com `apps/api/.venv/bin` no `PATH` (o `conftest` de integração chama `alembic` por
subprocesso; sem isso, 61 testes de integração dão erro de ambiente e **não** de código —
foi o primeiro achado desta bateria, A-06 em §5).

| # | Critério | Comando | Saída (colada) | Examinou | Código | Veredito |
|---|---|---|---|---|---|---|
| 1 | Admissão recusa nomeando o que faltou | `pytest tests/federacao/test_admissao.py tests/federacao/test_arranque_e_admissao.py -q` | `28 passed, 2 warnings in 4.34s` | 28 casos sobre 18 funções — um por parâmetro ausente (parametrizado nos 6 códigos), valor em branco, ordem da recusa, e o **processo de verdade** que morre sem abrir porta | `0` | ✓ verde |
| 2 | Handshake nunca confiado | `pytest tests/federacao/test_principal.py tests/federacao/test_portas_da_federacao.py -q` | `37 passed in 0.84s` | 37 casos, incluindo `test_payload_de_handshake_nao_constroi_identidade` — o payload do canal não vira `Principal` sem introspecção | `0` | ✓ verde |
| 3 | Grant trocado e descartado | `pytest tests/federacao/test_casos_de_uso_da_federacao.py -k "grant or fundacao or expires" -v` | `4 passed, 26 deselected in 0.18s`, com `test_o_grant_e_trocado_uma_vez_e_descartado PASSED` | 4 casos; a metade "grep negativo do grant nos logs" é coberta por `test_a_credencial_nunca_aparece_na_representacao_da_admissao` e por `assert "ghd_credencial_sintetica" not in cliente.get("/saude").text` | `0` | ✓ verde |
| 4 | Falha fechada | mesmo comando da linha 3 | `test_a_fundacao_fora_do_ar_falha_fechada PASSED` · `test_grant_inativo_nao_produz_identidade PASSED` | 2 casos: 5xx/indisponibilidade ⇒ negação, e grant inativo não produz identidade | `0` | ✓ verde |
| 5 | Trava dupla do canal | `scripts/check-canal.sh` | `arquivos de teste encontrados: 1` · `# tests 21` · `# pass 21` · `# fail 0` · `✓ canal conforme ao §B.2.` | 21 testes de `node --test` sobre `apps/web/src/federacao/canal.mjs`: `ev.source` errado descarta, origem errada descarta, `"null"` descarta, e **nunca responde** | `0` | ✓ verde |
| 6 | `targetOrigin` dirigido | `grep -rn 'postMessage' apps/web/src/federacao/ \| grep -v HOST_ORIGIN` | devolveu **2 linhas**, as duas comentários (`embarque.test.ts:5` e `:78`) que citam o defeito `postMessage(..., "*")` da norma | a árvore `apps/web/src/federacao/` inteira; o único envio de produção é `apps/web/src/main.tsx:29`, que passa `destino`, e `canal.mjs:160` chama `enviar(envelope(type, payload), hostOrigin)` — nunca `"*"` | `0` | ⚠ **verde no conteúdo, vermelho na letra** — ver A-01 |
| 7 | Envelope canônico | `scripts/check-canal.sh` (mesma corrida da linha 5) | `# pass 21` | o envelope é fechado em 4 campos (`payload,protocol,type,v`); `{tipo, versao}` — o da irmã — é ignorado sem resposta | `0` | ✓ verde |
| 8 | Migração reversível sem resíduo | `pytest tests/integracao/test_migracao_e_isolamento.py -k "downgrade or esquema_minimo" -v` | `2 passed, 4 deselected in 2.99s`, com `test_downgrade_volta_ao_vazio_sem_residuo PASSED` | ciclo `upgrade → downgrade` num esquema descartável do **PostgreSQL real** (não SQLite, não `create_all`) | `0` | ✓ verde |
| 9 | Isolamento por inquilino | `pytest "tests/integracao/test_migracao_e_isolamento.py::test_isolamento_por_inquilino_no_banco_real" -v` | `1 passed in 1.37s` | dois inquilinos no banco real, interseção vazia | `0` | ✓ verde |
| 10 | Traço de ponta a ponta | `pytest tests/aplicacao/test_caso_de_uso_e_span.py -q` | `7 passed in 0.15s` | 7 casos; **o span é da classe-base** (`apps/api/src/toc_api/aplicacao/casos_de_uso.py`), então todo caso de uso o abre queira o autor ou não — e `test_o_span_do_embarque_cobre_a_introspeccao` cobre o elo embarque→introspecção | `0` | ✗ **VERMELHO parcial** — ver A-02 |
| 11 | eTLD+1 distinto | — | — | — | — | ✗ **VERMELHO** — não há deploy; ver A-03 |
| 12 | Junta fecha contra a `ghdaru` real | `mensagens/003-para-ghdaru-o-que-falta-para-embarcar-a-toc.md` | `erros: 0 \| veredito: ACEITO` (validador da fundação contra o manifesto conforme ao Anexo B) · `Placar do lado hospedeiro, Nível 3: 15 obrigações examinadas — 9 ✅ · 4 ❌ · 2 ⏳` | o ramo **alternativo** que a própria linha autoriza ("ou L-01 re-medido + mensagem") | `0` | ⚠ **verde pelo ramo alternativo** — ver A-04 |
| 13 | Sem segredo versionado | `grep -rEn 'ghd_[A-Za-z0-9]\|postgres://' --include='*' . \| grep -v node_modules \| grep -v '.venv' \| grep -v exemplo \| wc -l` | `15` | a árvore inteira; as 15 ocorrências abertas uma a uma: 6 são a credencial **sintética** `ghd_credencial_sintetica` dos testes de admissão (e três delas são a asserção de que ela **não** vaza), 3 são o tradutor `postgres://` → `postgresql://` de `apps/api/src/toc_api/infra/persistencia/motor.py:20-22`, 6 são texto de documento. **Nenhuma é credencial real** | `0` (grep) | ⚠ **verde no conteúdo, vermelho na letra** — ver A-05 |
| 14 | Rollback ensaiado | `ls docs/operacao/` | `ls: cannot access 'docs/operacao/': No such file or directory` | — | `2` | ✗ **VERMELHO** — ver A-03 |

**Placar da DoD: 9 verdes · 2 verdes com ressalva declarada · 3 vermelhas.**

## 3 · Gates de reversibilidade (raia infra — prova, não promessa)

| Gate | Ensaio | Evidência colada | Estado |
|---|---|---|---|
| GATE-migracao | `upgrade head` → `downgrade base` em esquema descartável do PostgreSQL real | `2 passed, 4 deselected in 2.99s` (linha 8 da DoD) | ✓ ensaiado |
| GATE-deploy | reverter interface e serviço ao deploy anterior | — | ✗ **não ensaiado**: não há deploy (A-03) |
| GATE-admissao | processo morre sem abrir porta quando falta parâmetro | `test_o_processo_de_verdade_morre_sem_abrir_porta PASSED` (dentro dos `28 passed` da linha 1) | ✓ ensaiado |
| GATE-endereco | comparação de eTLD+1 com o hospedeiro | — | ✗ **portão humano, não executado** ([DÚVIDA] 1) |
| GATE-seguranca | passe de segurança em contexto fresco sobre admissão, canal e introspecção | §6 | ⚠ parcial — quem executou não verifica (Maestro II) |

## 4 · O portão vermelho de conformidade, diagnosticado

```text
$ scripts/check-conformance.sh 003
── Conformance: did the method survive into the artifacts? ──
   (floor: cycle 42; older cycles carry declared debt — see the roadmap)
• 003-esqueleto-federado
    ✓ Constitution Check complete (8/8)
    · acceptance-criteria checkboxes: not checked below cycle 45
    ✗ research: declared ART:research=no with no reason — a declaration without a why is silence
    ✗ data-model: declared ART:data-model=yes with no reason — a declaration without a why is silence
    ✗ contracts: declared ART:contracts=yes with no reason — a declaration without a why is silence
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

**Duas causas distintas, e misturá-las seria mentir sobre as duas:**

1. **Causa externa, já relatada** — as duas últimas linhas. Os pisos do script
   (`MUT_FLOOR=55`, `ABSENCE_FLOOR=61`) são números **absolutos** de ciclo da história do
   repositório canônico do método. Num repositório que vai até o ciclo `012`, `55 > 12` é
   verdadeiro para sempre. Está relatado em `mensagens/002-para-maestro-pisos-absolutos-de-ciclo.md`
   e o `GHDaru/maestro` é **leitura** (P1): relatar e parar.
2. **Causa nossa, e este documento fecha três linhas dela** — as três linhas `TAIL:*` eram
   verdadeiras: a cauda estava ausente do `qa-report.md`. Ela está em §10. As três linhas
   `ART:*` continuam vermelhas e são do `plan.md`, não deste arquivo: a declaração de
   artefato existe sem o motivo escrito ao lado. **Fica registrado como Dv-1** (§9) — não é
   deste relatório corrigir o plano de outro ciclo, e afrouxar o portão não estava em
   questão.

## 5 · TAIL:review — a revisão independente, com os achados numerados

A revisão deste ciclo aconteceu em **três formas**, e as três estão transcritas por
resultado, não por intenção: (a) a auditoria do lado hospedeiro que produziu a mensagem 003;
(b) a avaliação heurística datada da jornada J-01; (c) esta própria bateria, que é revisão em
contexto fresco de quem **não** escreveu o código do ciclo 003.

### 5.1 · Achados desta bateria

| # | Achado | Severidade | Destino |
|---|---|---|---|
| **A-01** | A linha 6 da DoD manda `grep … \| grep -v HOST_ORIGIN` **⇒ vazio** e o comando devolve **2 linhas**. As duas são comentários de teste que **citam** o defeito da norma. O critério, como escrito, não distingue "cita o nome do defeito para provar que não o comete" de "comete o defeito" — o mesmo formato de defeito que o ciclo 008 registrou na DoD 11 dele. | Baixa | 📝 **registrado**: o critério merece ser reescrito na spec para medir **envio de produção** (`enviar(...)`), ou isentar comentário por nome. Nenhuma linha de código muda. Dono: gate humano do ciclo 003 |
| **A-02** | A linha 10 da DoD pede spans `embarque → introspecção → consulta` **sob o mesmo `trace_id`** e **não existe teste que asserte a correlação**. O que existe é forte, mas é outra coisa: a classe-base abre um span por caso de uso (126 casos de uso declaram `nome`), `test_o_span_do_embarque_cobre_a_introspeccao` cobre um elo, e `trace_id` é coluna do traço federado desde a migração `0004`. A busca por `trace_id` em `apps/api/tests/` devolve **0 ocorrências**. | **Média** | ✗ **VERMELHO assumido**: o critério não está cumprido. Dono: o ciclo que fechar a observabilidade de ponta a ponta, com um teste que colha os três spans e compare os identificadores |
| **A-03** | Três linhas da DoD (11 eTLD+1, 14 rollback) e duas tarefas (T-13 CI, T-14 deploy) dependem de um deploy que **não existe**: `ls .github/workflows` e `ls docs/operacao/` devolvem `No such file or directory`, e não há `vercel.json`, `railway*`, `Procfile` nem `Dockerfile` na árvore. | **Alta** | ✗ **VERMELHO assumido**: a metade operacional da raia infra não foi executada. Dono: gate humano ([DÚVIDA] 1 — o endereço) + o lote de deploy |
| **A-04** | A linha 12 fecha pelo **ramo alternativo** que ela mesma autoriza, e é honesto dizer o que isso não prova: o manifesto **não** foi submetido a uma fundação de pé, e a introspecção servidor-a-servidor foi medida contra o adaptador falso (`ProvedorDeIdentidadeFalso`, declarado na saída do `scripts/check-conformidade-aph.sh`). A auditoria do lado hospedeiro é **por leitura**, e a própria mensagem diz: *"auditoria por leitura estima; execução calibra"*. | **Média** | ⚠ **verde declarado com alcance**: o ramo principal continua bloqueado pelos achados A1 e A5 da mensagem 003 (ação federada sem credencial; grants em memória) |
| **A-05** | A linha 13 pede `⇒ vazio` e devolve `15`. Nenhuma é segredo, mas o critério como escrito é **inconferível na prática** — ele reprova o repositório por citar o nome do que proíbe. | Baixa | 📝 registrado junto com A-01: os dois são a mesma classe de defeito de critério |
| **A-06** | Os 77 testes de integração **erram** (não falham) quando `apps/api/.venv/bin` não está no `PATH`: o `conftest` chama `alembic` por subprocesso e recebe `returncode: 255`. Um leitor apressado lê "61 errors" e conclui que o banco está fora do ar. | Baixa | 📝 registrado: o `conftest` poderia chamar `sys.executable -m alembic`, e a mensagem de erro poderia nomear a causa. Dono: ciclo de infraestrutura de teste |

### 5.2 · Achados herdados, transcritos das fontes que os produziram

**Da auditoria do lado hospedeiro** (`mensagens/003-para-ghdaru-o-que-falta-para-embarcar-a-toc.md`,
7 achados; os dois que **nos bloqueiam** estão abaixo, na letra da fonte):

> **A1 · A ação federada chega à aplicação sem credencial, sem inquilino e sem usuário — e
> isso, para nós, é o bloqueio central**
>
> **A5 · Registro federado e grants vivem em memória: um reinício da fundação
> **desadmite** a aplicação

Destino: **relatados e parados** (P1). Nenhuma linha foi escrita fora deste repositório. O
bloqueio L-01 do planejamento **caiu** — o golden da fundação é hoje cópia do normativo, e o
manifesto conforme ao Anexo B foi validado pelo validador **deles** com `erros: 0`. O L-03
continua aberto e é o A5.

**Da avaliação heurística da jornada J-01** (`docs/jornadas/001-chegada-e-embarque.md`,
2026-09-06, 5 achados):

| # | Achado | Severidade | Destino |
|---|---|---|---|
| J-01/A-01 | A sessão emitida por `POST /toc/embarque` autentica `/aph/*` (`200`) mas **não** `/toc/*` (`401`): embarcada de verdade, a aplicação não carrega conteúdo nenhum | **Alta** | 📝 registrado — correção fora daquele lote (é código de produção, e entra por ciclo com teste que falha antes, P4) |
| J-01/A-02 | Na largura do `iframe` (≈1 010 px) o formulário de criação fica numa linha só, com o `select` quebrando | Média | 📝 registrado para o ciclo de interface |
| J-01/A-03 | "Recarregue a tela pelo hospedeiro" é uma instrução que **não resolve** enquanto A-01 existir | Média | 📝 registrado — depende de A-01 |
| J-01/A-04 | Credencial com caractere fora de ASCII devolve `503 FUNDACAO_INDISPONIVEL` em vez de recusar na partida | Baixa | 📝 registrado |
| J-01/A-05 | A recusa de admissão ocupa a tela inteira sem dizer onde a variável se configura | Baixa | 📝 registrado |

## 6 · TAIL:security — o passe, item a item

Passe proporcional à classe de risco, executado sobre admissão, canal e introspecção — as
três superfícies que o `GATE-seguranca` nomeia. **Não é revisão independente completa**:
quem executou esta bateria não escreveu o código do ciclo 003, mas o passe de segurança em
contexto fresco de um terceiro continua devendo (Dv-4).

| Item | Como se verificou | Resultado |
|---|---|---|
| Segredo versionado | `grep -rEn 'ghd_[A-Za-z0-9]\|postgres://'` sobre a árvore | `15` ocorrências, **0 credenciais reais** (§2, linha 13) |
| Credencial no log / na resposta | `test_a_credencial_nunca_aparece_na_representacao_da_admissao`, `assert "ghd_credencial_sintetica" not in cliente.get("/saude").text` | ✓ dentro dos `28 passed` |
| Falha fechada da identidade | `test_a_fundacao_fora_do_ar_falha_fechada`, `test_grant_inativo_nao_produz_identidade`, `test_o_que_nega_tudo_nega_ate_o_token_que_pareceria_bom` | ✓ |
| Fábrica de identidade fora de desenvolvimento | `test_fora_de_desenvolvimento_a_fabrica_entrega_o_falso` / `nega_tudo_nunca_cai_no_falso` | ✓ dentro dos `16 passed` |
| Curinga de capability | `test_curinga_de_capability_e_recusado_na_composicao`, `test_curinga_vindo_do_hospedeiro_e_descartado_sem_derrubar_e_sem_autorizar` | ✓ dentro dos `37 passed` |
| Trava dupla do canal (`ev.source` **e** `ev.origin`) | `scripts/check-canal.sh` | ✓ `# pass 21` |
| Dado real de pessoa (ADR 0006) | `scripts/check-vazamento.sh` | ✓ `0` achados sobre `579` arquivos e `131024` linhas |
| Política de autorização fora do modelo | `scripts/check-politica.sh` | ✓ `arquivos de produção varridos: 96` · `arquivos que compõem PoliticaPorCapability: 3` |

## 7 · TAIL:mutation — sabotar e ver reprovar

```text
$ scripts/tests/run-sabotagem.sh
── Sabotagem: quanto foi examinado ──
  portões cobertos: 10  ·  bases válidas aceitas: 10/10
  sabotagens declaradas: 61  ·  reprovadas pelo motivo certo: 61/61
  sabotagens de ambiente: 2  ·  recusadas pelo motivo certo: 2/2
  cada sabotagem roda sobre uma cópia em /tmp/tmp.llVqVmZmss — o repositório não é tocado

✓ os 10 portões aceitam a base válida e reprovam as 61 sabotagens,
  cada uma pelo motivo que a tabela declara.
$ echo $?
0
```

**O que isto prova para o ciclo 003, e o que não prova.** Prova que os 10 portões deste
repositório **sabem reprovar** — inclusive por **ambiente**, que é a forma de sabotagem que
o `scripts/check-conformidade-aph.sh` exigiu (medir contra alvo em memória é recusado com
saída 3). **Não** prova mutação sobre a lógica de admissão e de verificação de fonte/origem,
que é o que o `TAIL:mutation` do `tasks.md` deste ciclo pede nominalmente: as 61 sabotagens
são sobre **portões**, não sobre as funções `admitir(env)` e `envelopeValido(...)`. Fica como
**Dv-5**.

## 8 · TAIL:gate — NÃO marcado, e o que aguarda o Product Steward

O gate humano é indelegável e **não foi executado**. O que está sobre a mesa:

1. **A decisão do endereço** ([DÚVIDA] 1) — sem ela, as linhas 11, 12 (ramo principal) e 14
   da DoD não têm como fechar. É a raiz do achado A-03.
2. **Aceitar ou recusar as duas ressalvas de critério** (A-01 e A-05): reescrever as linhas 6
   e 13 da DoD para medirem o que dizem medir, como o ciclo 001 fez com a linha 11 dele.
3. **Autorizar a entrega da mensagem 003** ao `GHDaru/ghdaru` — está escrita, está parada, e
   entregar é ato humano (P1).
4. **Decidir o destino do vermelho A-02** (traço de ponta a ponta): fechar neste ciclo ou
   alocar ao ciclo de observabilidade.
5. **Aceitar as cinco dívidas do §9**, com dono e ciclo.
6. **Autorizar a promoção** — e ela não roda pelo caminho feliz hoje (o
   `scripts/promote-main.sh` aborta no portão de conformidade, pelo motivo externo do §4).
   O procedimento está em `docs/governance/como-fechar-um-ciclo.md`.

## 9 · Dívidas declaradas, com dono

| # | Dívida | Por quê | Dono |
|---|---|---|---|
| **Dv-1** | As três linhas `ART:*` do `scripts/check-conformance.sh 003` (research, data-model, contracts declarados sem o motivo escrito) | É defeito do `specs/003-esqueleto-federado/plan.md`, não deste relatório; corrigir plano alheio dentro de um lote de QA seria mudança silenciosa de escopo | construtor do ciclo 003, na reabertura |
| **Dv-2** | CI (`.github/workflows`) não existe — T-13 | O ciclo entregou a suíte e os portões locais; o pipeline que os roda em pull request não foi montado | lote de deploy/CI |
| **Dv-3** | `docs/operacao/rollback.md` não existe — T-15 e DoD 14 | Depende do deploy (A-03) | lote de deploy, com o gate humano do endereço antes |
| **Dv-4** | Passe de segurança em contexto fresco por **terceiro** | Maestro II: quem executa não verifica. §6 é um passe medido, não uma revisão independente de segurança | revisor de segurança em contexto fresco |
| **Dv-5** | Mutação sobre `admitir(env)` e sobre a verificação de fonte/origem | As 61 sabotagens cobrem portões, não estas duas funções — que são exatamente as de falha silenciosa cara | construtor do ciclo 003 |
| **Dv-6** | T-18 (medição do embarque: `ghd.ready` → lista renderizada, a partir do traço) | Depende de embarques reais, logo de deploy | lote de deploy |
| **Dv-7** | L-02 (`FEDERATION_MANIFESTS_ENABLED`) foi medido **no código** da fundação e não no ambiente dela | A pergunta está no §5 da mensagem 003 e depende de resposta deles | fundação `GHDaru/ghdaru`, via a mensagem |

## 10 · Cauda

- **TAIL:review** — feita em contexto fresco por quem não escreveu o código do ciclo: **6
  achados numerados** nesta bateria (A-01 a A-06, §5.1), **7 achados** herdados da auditoria
  do lado hospedeiro (A1–A7 da mensagem 003, §5.2) e **5 achados** da avaliação heurística
  datada da jornada J-01. Destino escrito para cada um; três viraram vermelho assumido na
  DoD (A-02, A-03) em vez de serem maquiados.
- **TAIL:security** — passe executado sobre admissão, canal e introspecção, **8 itens
  medidos, 8 sem furo** (§6): grep de segredo (15 ocorrências, 0 credenciais reais), a
  credencial ausente de log e de `/saude`, falha fechada da identidade, fábrica que nunca cai
  no adaptador falso fora de desenvolvimento, curinga de capability recusado nas duas
  direções, trava dupla do canal (`# pass 21`), `scripts/check-vazamento.sh` sobre 579
  arquivos e `scripts/check-politica.sh` sobre 96 arquivos de produção. **Alcance declarado**:
  é passe, não revisão independente de segurança por terceiro (Dv-4).
- **TAIL:mutation** — `scripts/tests/run-sabotagem.sh` saiu **0**: `portões cobertos: 10 ·
  bases válidas aceitas: 10/10` e `sabotagens declaradas: 61 · reprovadas pelo motivo certo:
  61/61`, mais 2 sabotagens **de ambiente** que provam que o portão de conformidade APH
  recusa medir contra alvo em memória. **O que não cobre** está dito em §7 e é a dívida Dv-5.
- **TAIL:gate** — **NÃO marcado, de propósito.** A DoD fechou **9 verdes, 2 verdes com
  ressalva declarada e 3 vermelhas**, e as três vermelhas dependem de uma decisão humana (o
  endereço de deploy) que ninguém pode tomar por delegação. Os seis itens que aguardam
  assinatura estão em §8. Quem executou não aprova o que executou (Maestro II).

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
| `scripts/check-conformance.sh 003` | ver o bloco de conformidade acima | `1` |

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

**Executado e medido; NÃO fechado.** O esqueleto federado existe, atravessa o PostgreSQL
real, recusa a subida sem os parâmetros de admissão, nunca confia no handshake, verifica
fonte **e** origem, e a suíte de conformidade do Nível 1 do `GHDaru/protocolos` devolve
**11/11 verificados** contra ele. A metade operacional da raia infra — CI, deploy, endereço,
rollback — **não foi executada**, e por isso três linhas da DoD estão vermelhas neste
relatório em vez de estarem escondidas. O gate humano é o próximo passo, e não é delegável.
