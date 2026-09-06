# QA report 006 — Ações governadas e snapshot

> Siglas deste documento: **QA** — *Quality Assurance* (garantia de qualidade) · **DoD** —
> *Definition of Done* (Definição de Pronto) · **APH** — Aplicação ↔ Harness · **FSM** —
> máquina de estados finitos · **SSE** — *Server-Sent Events* · **IA** — inteligência
> artificial · **SDK** — *Software Development Kit* · **JSON** — *JavaScript Object
> Notation* · **ADR** — *Architecture Decision Record* (Registro de Decisão Arquitetural) ·
> **ARA** — Árvore da Realidade Atual · **NC** — Nuvem de Conflito · **M4** — módulo das
> árvores de futuro e implementação · **RF/RI/RNF/RN/INT** — requisito funcional / de
> interface / não funcional / regra de negócio / integração · **AST** — árvore sintática
> abstrata · **TTL** — *Time To Live*.

- **Data da bateria**: 2026-09-06 · **Raia**: plena
- **Veredito atual**: **executado e medido; NÃO fechado, e com um vermelho vivo.** Das 14
  linhas da DoD, **11 estão verdes com saída colada**, **1 verde com ressalva declarada**
  (linha 12 — a metade "resposta < 5 s **medida**" não foi medida), **1 VERMELHA** (linha 13
  — a jornada dos quatro fluxos não existe como documento) e **1 vermelha por causa externa
  já relatada** (conformidade).
- **Vermelho vivo, medido às 05:41Z**: o teste de paridade **registro de telas × manifesto
  publicado** está **falhando** — o manifesto declara **9 telas** e a interface declara
  **4**. É a função de aptidão do APH-3.1 ("a IA nunca infere a interface") e ela está
  vermelha agora. Achado **A-05**, §5.4.
- **Dois achados de revisão independente deste ciclo custaram caro e foram fechados**: a
  proposta de ação era o **único agregado sem trava** — uma aprovação humana executava oito
  vezes — e o fio emitia `done` depois de `error`, o que vazava mensagem interna no lugar do
  código do §A.7.

> **R1 e R2 aplicadas linha a linha.** Toda saída foi executada em **2026-09-06**, entre
> 04:50Z e 05:41Z, e está **colada**.
>
> **Ressalva de medição — e desta vez ela mudou um veredito.** O repositório **estava sendo
> construído enquanto era medido** (o lote do M6, spec 009). Às **04:50Z**,
> `scripts/evidencia.sh` devolveu `Portões executados: 17 · verdes: 17 · vermelhos: 0.` Às
> **05:41Z**, `scripts/check-trava-da-proposta.sh` saiu **1**, porque um método de escrita
> novo (`salvar_focalizacao`, do M6) entrou no adaptador **sem entrar na lista do portão**.
> O portão está certo e o repositório está momentaneamente vermelho; os dois fatos estão
> colados em §1.1, e nenhum deles foi apagado para o relatório ficar bonito.

## 0 · Histórico de veredito — os estados por que este ciclo passou

| # | Data | Estado | O que aconteceu | Evidência |
|---|---|---|---|---|
| **V1** | 2026-09-05/06 | **construído** | FSM de proposta declarativa, catálogo derivado de capability, capability verificada **no caso de uso**, traço de todo desfecho, lote honesto, snapshot sanitizado com registro de telas, fio SSE sobre POST com `seq` do servidor, replay, cancelamento, borda federada e manifesto validado contra o schema normativo. | `apps/api/src/toc_api/dominio/federacao/proposta.py`, `.../catalogo.py`, `.../snapshot.py`, `apps/api/src/toc_api/http/aph.py` |
| **V2** | 2026-09-06 | **REPROVADO — três achados de revisão independente que executou** | `done` depois de `error` no fio; duas grafias do mesmo código de erro no mesmo serviço; e o portão de conformidade APH que **não dizia contra o que mediu** (regra R2). | §5.2, achados **A-02**, **A-03**, **A-04** |
| **V3** | 2026-09-06 | **REPROVADO — o gate humano multiplicado por uma corrida** | Crítico hostil reproduziu: oito confirmações simultâneas da **mesma** proposta executavam oito vezes. `códigos {200: 8} · nós no banco 50 para 30 pedidos · títulos repetidos 22 · linha no banco: estado=failed execucoes=1`. | §5.1, achado **A-01** |
| **V4** | 2026-09-06 | **corrigido, e a classe fechada** | `estado_lido` + `confirmar_gravacao()` na proposta, `UPDATE … WHERE estado = :estado_lido`, e a **reserva antes do efeito**; `idempotency_key` com índice único parcial (migração `0007`) e leitura de verdade. Portão novo com 10 sabotagens. | §5.1, §7 |
| **V5** | 2026-09-06 | **corrigido — o laço da assistência ganhou porta** | `POST /toc/propostas` e `POST /toc/propostas/{id}/decisao` (ADR 0009): a interface da própria aplicação passou a ter a porta de proposta que só o hospedeiro tinha. | §5.3 |
| **V6** | 2026-09-06 | **medido — e com um vermelho vivo** | Esta bateria. **11 verdes · 1 com ressalva · 2 vermelhas**, mais o vermelho de paridade do registro de telas (A-05) e o vermelho de portão herdado do lote em curso (§1.1). | §2 |
| **V7** | — | **aguardando gate humano** | `TAIL:gate` **não marcado** — e este é o ciclo em que o gate humano **é o produto**: aprovar o catálogo `toc.*` ação a ação é portão indelegável. | §8 |

## 1 · Bateria de portões (denominador colado — regra R2)

`scripts/evidencia.sh`, executado às **04:50Z**, saiu **0**:
`Portões executados: 17 · verdes: 17 · vermelhos: 0.`

| # | Portão | Código | Denominador — a linha do próprio portão |
|---|---|---|---|
| G1 | `scripts/check-manifesto.sh` | **0** ✓ | `telas declaradas: 9` · `ações declaradas: 15` · `sabotagens aplicadas: 7; repelidas: 7` |
| G2 | `scripts/check-politica.sh` | **0** ✓ | `arquivos de produção varridos: 96` · `arquivos que compõem PoliticaPorCapability: 3` |
| G3 | `scripts/check-conformidade-aph.sh` | **0** ✓ | `persistência ......... postgres (exigida: postgres)` · `migração (alembic) ... 0007` · `natureza do turno .... ENLATADO E DETERMINÍSTICO — não há provedor de modelo` · `Veredito: APTO nos itens verificáveis — 11/11 verificados; 12 itens a autodeclarar.` |
| G4 | `scripts/check-trava-da-proposta.sh` | **0** ✓ às 04:50Z · **1** ✗ às 05:41Z | ver §1.1 |
| G5 | `scripts/check-trava-otimista.sh` | **0** ✓ | `caminhos de escrita conferidos: 8 declarados · 8 encontrados no adaptador` |
| G6 | `scripts/check-raiz-do-agregado.sh` | **0** ✓ | `operação só pela raiz: 8 guardas, 6 raízes, 192 arquivos varridos.` |
| G7 | `scripts/check-evidencia-colada.sh` | **0** ✓ | `afirmações registradas: 31 · comandos executados com sucesso: 31/31` · `ocorrências conferidas: 35 · arquivos alcançados: 8` |
| G8 | `scripts/check-caminhos.sh` · `scripts/check-links.sh` | **0** ✓ | `caminhos conferidos: 1005 · isentos declarados: 330` · `checked: 469` |
| G9 | `scripts/check-conformance.sh 006` | **1** ✗ | `cycles checked: 1` — diagnóstico em §4 |

### 1.1 · O portão que ficou vermelho durante esta bateria, e por quê

```text
$ scripts/check-trava-da-proposta.sh
── Trava da proposta: uma aprovação humana, uma execução ──
  arquivos varridos: 7 (agregado, registro §A.7, adaptador SQL, duplo em
  memória, caso de uso, tabelas, adaptador do núcleo)
  ✓ o agregado declara `estado_lido` e `confirmar_gravacao`
  ✓ a reserva (linha 202) acontece ANTES do efeito (linha 204)
  ✓ a `idempotency_key` tem índice único por inquilino no modelo declarado
  ✓ a aplicação CONSULTA a chave de idempotência
  ✓ o traço continua somente-acréscimo (0 `UPDATE`/`DELETE` sobre ele)
  caminhos de escrita classificados: 10
✗ os adaptadores têm 9 método(s) `salvar*` e este portão conhece 8
  Um caminho de escrita novo entrou sem entrar na lista deste portão — e um caminho
  fora da lista é um caminho que ninguém conferiu.
    …/infra/persistencia/repositorio_projetos.py:1365:    def salvar_focalizacao(self, analise: AnaliseDeFocalizacao) -> None:
✗ a trava da proposta deixou de proteger algum caminho — verificações: 25 de 26.
$ echo $?
1
```

**Diagnóstico, e ele não é deste ciclo.** O método `salvar_focalizacao` é do **M6 (spec
009)**, um lote que está sendo escrito neste mesmo repositório agora — o arquivo tem mtime
**05:06Z** e o portão foi executado às **05:41Z**. O portão está fazendo exatamente o que
existe para fazer: **um caminho de escrita fora da lista é um caminho que ninguém conferiu**.
Não foi afrouxado, não foi contornado, e não foi corrigido por este relatório — corrigir o
lote de outro construtor enquanto ele o escreve é como se produz conflito, e a lista do
portão precisa da **classificação** (retrato · acréscimo · identidade) que só quem escreveu o
caminho pode dar. Fica como achado **A-10** e dívida **Dv-6**, com dono nomeado.

## 2 · DoD — as 14 linhas da spec, com comando, saída colada e veredito

> **Ajuste de caminho declarado.** A spec cita `tests/propostas`, `tests/catalogo`,
> `tests/autorizacao`, `tests/traco`, `tests/lote`, `tests/snapshot`, `tests/wire` e
> `tests/borda` — uma pasta por assunto. A árvore real agrupa por **camada**
> (`apps/api/tests/federacao/…`, `…/aplicacao/…`, `…/contrato/…`), e o assunto vira arquivo
> ou seletor `-k`. Os comandos abaixo são os mesmos critérios sobre os arquivos que existem,
> rodados de `apps/api`.

| # | Critério | Comando | Saída (colada) | Examinou | Código | Veredito |
|---|---|---|---|---|---|---|
| 1 | FSM completa e fechada | `pytest tests/federacao/test_proposta.py -q` e `-k "invalid or invalida" -v` | `95 passed in 0.10s` · `63 passed, 32 deselected in 0.09s` | 95 casos; **63 deles** são a matriz de transições inválidas, uma a uma (`[failed-falhar]`, `[proposed-concluir]`, `[proposed-executar]`…), cada uma exigindo `INVALID_TRANSITION` | `0` | ✓ verde |
| 2 | Nada executa na menção | `pytest tests/federacao/test_casos_de_uso_da_federacao.py -k "intocado or nasce_proposta" -v` + `pytest tests/federacao/test_superficie_aph.py -k "nasce_proposta" -v` | `1 passed, 29 deselected in 0.17s` (`test_acao_mutadora_nasce_proposta_e_o_dominio_fica_intocado`) · `1 passed, 29 deselected, 2 warnings in 1.26s` (`test_verbo_mutador_pela_borda_federada_nasce_proposta_e_nao_executa`) | as duas metades: pelo caso de uso e pela borda federada | `0` · `0` | ✓ verde |
| 3 | Catálogo derivado de permissão | `pytest tests/federacao/test_catalogo.py -q -s` | `catálogo: 15 ações declaradas; com toc:read+toc:write → 15; só com toc:read → 4; anônimo → 0` · `16 passed in 0.11s` | a contagem **antes e depois** impressa na saída, que é o que o portão do roadmap pede: sem `toc:write`, 11 ações **somem** do catálogo; anônimo vê zero | `0` | ✓ verde |
| 4 | Capability no caso de uso, não na rota | `pytest tests/aplicacao/test_governanca_de_capacidades.py -q` + `pytest tests/federacao/test_casos_de_uso_da_federacao.py -k "sem_http or sabotagem" -v` | `13 passed in 0.25s` · `2 passed, 28 deselected in 0.16s`, com `test_a_recusa_por_capability_acontece_no_caso_de_uso_sem_http PASSED` e `test_a_sabotagem_da_politica_derruba_o_teste_de_recusa PASSED` | 15 casos; o segundo é a **mutação embutida**: trocar a política por `lambda: True` derruba os testes de recusa | `0` · `0` | ✓ verde |
| 5 | Traço 100% (inclusive recusas) | `pytest tests/federacao/test_casos_de_uso_da_federacao.py -k "traco" -q` | `11 passed, 19 deselected in 0.17s` | 11 casos, incluindo `test_todo_desfecho_deixa_traco_inclusive_os_que_nao_executaram` e `test_sem_repositorio_de_traco_a_execucao_e_rejeitada_antes_do_efeito` — **sem traço, não executa** | `0` | ✓ verde |
| 6 | Lote honesto | `pytest tests/federacao/test_casos_de_uso_da_federacao.py -k "lote" -v` | `5 passed, 25 deselected in 0.17s`, com `test_lote_com_uma_falha_nao_termina_em_executed PASSED` e `test_o_evento_de_resultado_de_lote_valida_a_invariante_do_status PASSED` | 5 casos: contagem antes, `outcomes` por alvo, e o estado terminal que **nunca afirma mais sucesso** do que os desfechos | `0` | ✓ verde |
| 7 | Snapshot sanitizado no servidor | `pytest tests/federacao/test_telas_e_snapshot.py -q` + `pytest tests/federacao/test_superficie_aph.py -k "snapshot or sensivel" -v` | `20 passed in 0.03s` · `test_snapshot_com_campo_desconhecido_e_rejeitado_na_borda PASSED`, `test_o_valor_do_campo_sensivel_nao_atravessa_a_borda PASSED`, `test_tela_sensivel_nao_produz_snapshot PASSED` | 20 casos de registro/snapshot + 3 de borda: campo fora do registro → `INVALID_CONTEXT`; `ai_actions: []` marca item sensível e não produz snapshot | `0` | ✓ verde |
| 8 | Wire golden contra a norma | `pytest tests/federacao/test_paridade_com_jsonschema.py tests/federacao/test_superficie_aph.py -q -s` | `81 passed, 9 warnings in 6.39s`, com `golden do fio: 6 evento(s) validados contra evento.schema.json`, `golden do catálogo: 15 ação(ões) validadas contra acao-catalogo.schema.json` e `paridade jsonschema × domínio: 50 casos sobre 15 de 15 ações do catálogo; válidos=18 inválidos=32` | 81 casos contra os **schemas reais** do `GHDaru/protocolos`; a paridade cobre **15 de 15** ações do catálogo | `0` | ✓ verde |
| 9 | Replay íntegro | `pytest tests/federacao/test_wire.py -k replay -v` | `5 passed, 18 deselected in 0.02s`: `test_replay_after_zero_devolve_tudo`, `test_replay_after_n_devolve_so_o_que_falta_sem_duplicar`, `test_replay_de_after_maior_que_o_ultimo_e_vazio_e_nao_e_erro`, `test_stream_e_replay_serializam_o_mesmo_objeto`, `test_propostas_pendentes_sobrevivem_ao_replay` | 5 casos; e a suíte de conformidade do `GHDaru/protocolos` confirma de fora: `replay íntegro (?after=0, ?after=4, ?after=último)` e `queda após seq 1; replay reconstruiu 6 eventos até done` | `0` | ✓ verde |
| 10 | Cancelamento cooperativo | `pytest tests/federacao/test_wire.py -k "cancel" -v` | `2 passed, 21 deselected in 0.02s`: `test_cancelar_encerra_com_error_stream_cancelled_no_log`, `test_cancelar_turno_ja_terminado_nao_acrescenta_evento` | 2 casos; a suíte externa confirma: `cancelado no meio do turno; STREAM_CANCELLED presente no stream e no replay` | `0` | ✓ verde |
| 11 | Manifesto valida contra o schema normativo | `scripts/check-manifesto.sh` | `telas declaradas: 9` · `ações declaradas: 15` · `sabotagens aplicadas: 7; repelidas: 7` | o manifesto inteiro contra `federacao-manifesto.schema.json` (draft 2020-12) + **7 sabotagens** que provam que o validador não é leniente | `0` | ✓ verde |
| 12 | Borda federada fechada | `pytest tests/federacao/test_superficie_aph.py -k "borda or token_desconhecido or fora_do_catalogo" -v` | `8 passed, 22 deselected, 2 warnings in 2.64s`: sem identidade recusa, token desconhecido recusa **sem dizer o motivo**, `params` inválidos recusados contra o `input_schema`, ação fora do catálogo é desconhecida | 8 casos. **A metade que falta**: "resposta < 5 s **medida**" — não há medição de tempo em teste nenhum (`grep "perf_counter\|p95" apps/api/tests/` devolve vazio) | `0` | ⚠ **verde na recusa, não medido no tempo** — ver A-09 |
| 13 | Jornada viva presente | `ls docs/jornadas/` | `001-chegada-e-embarque.md  002-primeiro-projeto-e-ara.md  003-nuvem-de-conflito.md  007-a-travessia.md  README.md  capturas  scripts` | 4 jornadas; **nenhuma é a jornada dos quatro fluxos governados (RI-11)**. Os fluxos aparecem *dentro* da J-03 (capturas 08 a 10: propor, confirmar, recusar), o que é bem menos do que o critério pede | `0` (o `ls`) | ✗ **VERMELHO** — ver A-06 |
| 14 | Conformidade e caminhos | `scripts/check-conformance.sh 006` · `scripts/check-caminhos.sh` · `scripts/check-links.sh` | ver §4 · `✓ todo caminho citado entre crases existe.` (`caminhos conferidos: 1005 · isentos declarados: 330`) · `✓ every relative link resolves.` (`checked: 469`) | 125 arquivos · 469 links | `1` · `0` · `0` | ✗ **vermelho na conformidade**, verde nos caminhos |

**Placar da DoD: 11 verdes · 1 verde com ressalva declarada · 2 vermelhas.** Fora da DoD, há
o vermelho de paridade do registro de telas (A-05) e o vermelho de portão herdado do lote em
curso (§1.1).

## 3 · Portões executáveis do roadmap (ciclo 006)

| Portão | Como se verificou | Evidência colada |
|---|---|---|
| Sem capability de escrita, as ações mutadoras **somem do catálogo** — com a contagem antes/depois na saída | `pytest tests/federacao/test_catalogo.py -q -s` | `catálogo: 15 ações declaradas; com toc:read+toc:write → 15; só com toc:read → 4; anônimo → 0` |
| Nenhuma mutação proposta por modelo aplica fora da FSM | `pytest tests/federacao/test_proposta.py -k "invalid or invalida" -v` | `63 passed, 32 deselected in 0.09s` — a matriz inteira de transições inválidas |
| Snapshot sem campo não declarado no registro | `pytest tests/federacao/test_superficie_aph.py -k snapshot -v` | `test_snapshot_com_campo_desconhecido_e_rejeitado_na_borda PASSED`; e a suíte externa: `rejeitado com HTTP 400 INVALID_CONTEXT — o campo desconhecido não viajou` |
| Replay por `seq` testado | `pytest tests/federacao/test_wire.py -k replay -v` | `5 passed, 18 deselected in 0.02s` |
| Portão humano: catálogo `toc.*` aprovado ação a ação | — | ✗ **não executado** — é o gate humano deste ciclo (§8) |

## 4 · O portão vermelho de conformidade, diagnosticado

```text
$ scripts/check-conformance.sh 006
• 006-acoes-governadas-e-snapshot
    ✓ Constitution Check complete (8/8)
    · acceptance-criteria checkboxes: not checked below cycle 45
    ✗ data-model: declared ART:data-model=no with no reason — a declaration without a why is silence
    ✗ contracts: declared ART:contracts=yes with no reason — a declaration without a why is silence
    ✗ ux-design: declared ART:ux-design=no with no reason — a declaration without a why is silence
    ✗ tasks.md has no TAIL:review — the row was deleted, and the template says never delete
    ✗ tasks.md has no TAIL:security — the row was deleted, and the template says never delete
    ✗ tasks.md has no TAIL:gate — the row was deleted, and the template says never delete
──
cycles checked: 1
✗ mutation floor 55 is above the newest cycle 012 — TAIL:mutation was charged to nobody.
✗ declared-absence floor 61 is above the newest cycle 012 — 'pendente' would pass as evidence everywhere.
$ echo $?
1
```

Três causas: **(a)** os pisos absolutos do script do método — externos, relatados em
`mensagens/002-para-maestro-pisos-absolutos-de-ciclo.md`, `GHDaru/maestro` é leitura (P1);
**(b)** a cauda do `specs/006-acoes-governadas-e-snapshot/tasks.md`, que existe mas está
escrita como `T-16 — \`TAIL:review\``, e o portão ancora no token no início do item —
**Dv-1**; **(c)** três declarações `ART:*` do `plan.md` sem o motivo escrito — **Dv-2**. Uma
observação sobre a terceira: `ART:ux-design=no` é uma declaração **substancialmente
discutível** neste ciclo, porque ele entregou tela (a superfície de confirmação `proposta-de-acao`,
RI-01). O portão só cobra o motivo; o motivo, aqui, é o que merece a discussão do gate.

## 5 · TAIL:review — a revisão independente, com os achados numerados

### 5.1 · A-01 · O gate humano multiplicado por uma corrida (achado de crítico hostil que o reproduziu)

**Uma aprovação humana executava N vezes.** A trava otimista instalada no ciclo 004 fechou o
agregado `Projeto` e deixou a **proposta de ação** de fora; quem a instalou declarou a lacuna
como pendência, e o ataque confirmou que a pendência era real. Reproduzido contra o
PostgreSQL real, **antes de qualquer linha de conserto**:

```text
corrida de confirmação · chave única · códigos {200: 8} · nós no banco 50 para 30 pedidos
  · títulos repetidos 22 · linhas de traço 8 · linha no banco: estado=failed execucoes=1
corrida de confirmação · sem chave · códigos {200: 8} · nós no banco 49 · linhas de traço 8
corrida de recusa · códigos {200: 8} · nós no banco 0
  · linhas de traço ['denied', 'denied', 'denied', 'denied', 'denied']
```

**Diagnóstico antes do conserto — por que a FSM não impediu.** Ela guardava o **objeto**, não
a linha: `obter` reidrata um `PropostaDeAcao` novo a cada chamada, então oito confirmações
atravessavam oito agregados e as oito transições eram legítimas. E a gravação era um
`ON CONFLICT DO UPDATE` **incondicional** que rodava **depois** do efeito — a prova está na
própria linha: `estado=failed execucoes=1` depois de oito execuções, porque o último a gravar
escreveu o retrato dele por cima.

**Conserto na causa** (ADR 0011): `PropostaDeAcao.estado_lido` + `confirmar_gravacao()`;
`UPDATE … WHERE estado = :estado_lido` com `rowcount == 0` levantando `CorridaDeDecisao`; e —
a peça central — a **reserva acontece antes do efeito**: quem não escreve, não executa.
Recusar também reserva, porque recusar também é decidir. E a `idempotency_key`, que existia
desde a migração `0004` e era **lida em lugar nenhum**, ganhou índice único parcial (migração
`0007`) e leitor.

Verificação de hoje:

```text
$ cd apps/api && pytest tests/integracao/test_corrida_de_confirmacao_no_postgres.py -q -s
corrida de confirmação · chave única · códigos {200: 8} · nós no banco 30 para 30 pedidos · títulos repetidos 0 · linhas de traço 1 · linha no banco: estado=executed execucoes=1
corrida de confirmação · sem chave · códigos {409: 7, 200: 1} · nós no banco 30 · linhas de traço 1
corrida de recusa · códigos {409: 4, 200: 4} · nós no banco 0 · linhas de traço ['denied']
3 passed, 3 warnings in 10.51s
```

**Destino**: ✅ corrigido, com portão próprio (`scripts/check-trava-da-proposta.sh`, 26
verificações, 10 caminhos de escrita classificados) e **10 sabotagens** — a mais importante
não olha texto e sim **ordem de linhas**: mover a reserva para depois do efeito deixa a trava
inteira no lugar e inútil.

### 5.2 · Os três achados de revisão independente que executou

| # | Achado | Severidade | Destino |
|---|---|---|---|
| **A-02** | **`done` depois de `error` no fio (§A.1).** `_acrescentar_ao_log` emitia o terminador `done` **incondicionalmente** depois do evento; quando o evento é `error` — que já é terminador — o turno tentava encerrar duas vezes, o domínio recusava e a recusa subia até a borda. **Efeito medido**: quem confirmava uma proposta com a tela desatualizada recebia `409 DOMAIN_REFUSED` com a mensagem interna `"sessão …: o turno já terminou em 'error'"` em vez do `PROPOSAL_CONTEXT_STALE` que o §A.7 nomeia — defeito de protocolo **e** vazamento de mensagem interna no mesmo `done` | **Alta** | ✅ **corrigido**: terminador condicional, e os eventos de uma decisão num turno só. Quatro testes que reproduzem antes do conserto: `4 passed, 26 deselected, 4 warnings in 1.71s` |
| **A-03** | **Duas grafias do mesmo código de erro no mesmo serviço.** A borda REST emitia `INVALID_ARGUMENT` e a borda APH emitia `INVALID_ARGUMENTS` para a mesma situação. O §A.7 diz que "o cliente discrimina por código e nunca por mensagem": quem comparasse por igualdade trataria um e ignoraria o outro — e o cliente web já discriminava só o singular. **Causa raiz**: eram **dois registros declarados**, um por borda, e nada comparava os dois | **Alta** | ✅ **corrigido**: **um registro só** (`apps/api/src/toc_api/dominio/federacao/wire.py`), `envelope()` construído pelo domínio (código não declarado levanta antes de virar resposta) e a aptidão nova por varredura AST: `registro §A.7: 65 emissão(ões) literal(is) varridas em 96 arquivo(s) de produção, 39 código(s) distintos, contra 46 declarado(s)` · `cliente web: 21 código(s) de serviço discriminados na interface` · `5 passed` |
| **A-04** | **O portão de conformidade APH não dizia o que mediu (regra R2).** Ele herdava o ambiente do shell: sem `DATABASE_URL` exportada, o serviço sobe em `persistencia: memoria` e a suíte, que é caixa-preta, devolve **11/11 do mesmo jeito**. Foi o que aconteceu na corrida da revisão: verde legítimo, **alvo errado**, e a saída não dizia nem uma coisa nem outra | **Alta** | ✅ **corrigido**: o portão monta o alvo com ambiente explícito, **sonda o banco antes** de subir o serviço, **declara campo a campo** o que mediu, e **RECUSA** (saída 3) medir contra alvo em memória. Duas sabotagens **por ambiente** provam as duas metades |

### 5.3 · A-05 a A-10 — os achados abertos desta bateria

| # | Achado | Severidade | Destino |
|---|---|---|---|
| **A-05** | **VERMELHO VIVO — o registro de telas da interface divergiu do manifesto publicado.** O teste que é a função de aptidão do APH-3.1 está falhando: `AssertionError: expected [ { id: 'toc.ara', …(3) }, …(3) ] to deeply equal [ Array(9) ]`. O manifesto declara **9 telas** (`toc.projetos`, `toc.ara`, `toc.arf_canvas`, `toc.apr_canvas`, `toc.apr_sequencia`, `toc.at_canvas`, `toc.cadeia`, `toc.lixeira`, `toc.configuracao`); `apps/web/src/telas/registro.ts` declara **4** como estando no manifesto. **Causa**: o M4 (ciclo 008) cresceu o manifesto e o registro do servidor, e a interface do M4 é pendência declarada daquele lote (P-01 de lá) | **Alta** | ✗ **VERMELHO assumido, e ele é do ciclo 006 por natureza**: o registro compartilhado é o contrato deste ciclo, e ele está quebrado. Dono: o ciclo de interface do M4 — **ou** este ciclo, se o manifesto tiver de andar junto com a tela |
| **A-06** | **A jornada dos quatro fluxos (RI-11, T-14) não existe.** Existem 4 jornadas e nenhuma é dos fluxos governados. Os três desfechos aparecem dentro da J-03 (capturas 08 a 10), com evidência de build real — o que cobre parte do assunto e **não** o critério | Média | ✗ **VERMELHO assumido**. Dono: ciclo de jornadas (012) ou reabertura do 006 |
| **A-07** | **`ghd.action_result` (T-13) não é emitido pela interface.** `grep -rn "action_result" apps/web/src/` devolve **0**. O evento existe e é honesto **do lado do servidor** (`PropostaDeAcao.como_action_result`, §A.3), e o canal só conhece `["ghd.handshake", "ghd.resource_changed"]` | Média | ✗ registrado: o palpite de interface para o hospedeiro (§B.9.1) não sai daqui. Dono: ciclo de interface federada |
| **A-08** | O nome do teste `test_o_catalogo_anonimo_e_vazio_e_o_identificado_tem_as_onze_acoes` diz **onze** e a asserção é `len(identificado) == 15` (`apps/api/tests/federacao/test_superficie_aph.py:245`). O teste está certo; o nome envelheceu com o catálogo | Baixa | 📝 registrado — é a mesma classe que o `scripts/check-evidencia-colada.sh` pega em documento, num lugar onde ele não olha |
| **A-09** | A linha 12 pede "resposta < 5 s **medida**" e **não há medição de tempo em teste nenhum**: `grep "perf_counter\|p95" apps/api/tests/` devolve vazio. A recusa está provada; o tempo, não | Baixa | 📝 registrado, **Dv-5** |
| **A-10** | **O portão da trava da proposta ficou vermelho durante esta bateria** (§1.1): `salvar_focalizacao` (M6, spec 009, mtime 05:06Z) entrou no adaptador sem entrar na lista do portão | **Alta** enquanto durar | ✗ registrado, **Dv-6** — dono: o construtor do M6, que é quem sabe classificar o caminho novo (retrato · acréscimo · identidade) |

### 5.4 · A prova do vermelho A-05, colada

```text
$ cd apps/web && npx vitest run --reporter=dot
 FAIL  src/telas/registro.test.ts > registro de telas × manifesto publicado > declara exatamente as telas do manifesto, com rota, título e ações iguais
AssertionError: expected [ { id: 'toc.ara', …(3) }, …(3) ] to deeply equal [ Array(9) ]
…
-     "id": "toc.apr_canvas",
-     "route": "/toc/apr",
…
 Test Files  1 failed | 18 passed (19)
      Tests  1 failed | 199 passed (200)
```

### 5.5 · Achados da avaliação heurística da jornada J-03 sobre a superfície de decisão

Transcritos de `docs/jornadas/003-nuvem-de-conflito.md` (2026-09-06) — os que são do gate
governado, que é o produto deste ciclo:

| # | Achado | Severidade | Destino |
|---|---|---|---|
| J-03/A-03 | ~~Na pré-visualização, o único botão de decisão é **Recusar** — não há "Aceitar" nenhum~~ | Média | ✅ **corrigido em 2026-09-06** (ADR 0009): "Aceitar" leva a proposta ao gate governado, a superfície de confirmação decide, e a nuvem muda — capturas 08 a 10 |
| J-03/A-02 | ~~A pré-visualização abre numa coluna estreita enquanto metade da janela fica vazia~~ | Média | ✅ corrigido: prévia e superfície de confirmação a `min(880px, 100%)` |
| J-03/A-06 | O vencimento da proposta aparece como instante absoluto (`9/6/2026, 2:14:22 AM`), em formato do sistema e **em inglês**; quem decide quer saber quanto tempo **resta** | Baixa | 📝 registrado |
| J-03/A-07 | Depois de confirmar, a superfície de desfecho fica até alguém clicar em "Fechar", e o diagrama mudado aparece **abaixo** dela — quem não rolar pode não ver que a nuvem mudou | Baixa | 📝 registrado |

## 6 · TAIL:security — o passe, item a item

| Item | Como se verificou | Resultado |
|---|---|---|
| Borda federada sem credencial | `test_a_borda_federada_recusa_chamada_sem_identidade` | ✓ recusa com traço |
| Token desconhecido | `test_token_desconhecido_e_recusado_sem_dizer_o_motivo` | ✓ recusa **sem discriminar o motivo** — não vaza se o token existe |
| Capability inflada pelo hospedeiro | `test_capability_desconhecida_do_hospedeiro_e_ignorada_nao_derruba_o_embarque`, `test_curinga_vindo_do_hospedeiro_e_descartado_sem_derrubar_e_sem_autorizar` | ✓ o curinga é descartado **sem autorizar** |
| Capability verificada no caso de uso, não na rota | `test_a_recusa_por_capability_acontece_no_caso_de_uso_sem_http` | ✓ — e a sabotagem `lambda: True` derruba os testes de recusa |
| Injeção via snapshot | `test_snapshot_com_campo_desconhecido_e_rejeitado_na_borda`, `test_o_valor_do_campo_sensivel_nao_atravessa_a_borda`, `test_tela_sensivel_nao_produz_snapshot` | ✓ `INVALID_CONTEXT`; o valor sensível **não atravessa a borda** |
| Injeção via `params` | `test_a_borda_federada_valida_params_contra_o_input_schema` | ✓ validado contra o `input_schema` da ação |
| Nada executa sem gate | `test_acao_mutadora_nasce_proposta_e_o_dominio_fica_intocado` + a matriz de 63 transições inválidas | ✓ |
| Uma aprovação, uma execução | `apps/api/tests/integracao/test_corrida_de_confirmacao_no_postgres.py` | ✓ `códigos {200: 8} · nós no banco 30 para 30 pedidos · títulos repetidos 0` |
| Traço não reescrevível | `scripts/check-trava-da-proposta.sh` | ✓ `o traço continua somente-acréscimo (0 UPDATE/DELETE sobre ele)` |
| Segredo no cliente / dado real (ADR 0006 e 0007) | `scripts/check-vazamento.sh` + o grep de SDK | ✓ `0` achados sobre `579` arquivos; `3` ocorrências de "api_key", as três a **denylist** do snapshot |
| Política de autorização fora do modelo | `scripts/check-politica.sh` | ✓ `96` arquivos de produção varridos |

**Alcance declarado**: passe medido por quem executou a bateria; não substitui revisão
independente de segurança por terceiro em contexto fresco (**Dv-4**).

## 7 · TAIL:mutation — sabotar e ver reprovar

```text
$ scripts/tests/run-sabotagem.sh
  ✓ efeito-antes-da-reserva → check-trava-da-proposta.sh saiu 1 pelo motivo declarado
  ✓ caso-de-uso-sem-reserva-nenhuma → check-trava-da-proposta.sh saiu 1 pelo motivo declarado
  ✓ duplo-da-proposta-sem-trava → check-trava-da-proposta.sh saiu 1 pelo motivo declarado
  ✓ duplo-da-proposta-devolve-a-linha-guardada → check-trava-da-proposta.sh saiu 1 pelo motivo declarado
  ✓ chave-de-idempotencia-nunca-consultada → check-trava-da-proposta.sh saiu 1 pelo motivo declarado
  ✓ indice-unico-da-chave-removido → check-trava-da-proposta.sh saiu 1 pelo motivo declarado
  ✓ traco-deixa-de-ser-somente-acrescimo → check-trava-da-proposta.sh saiu 1 pelo motivo declarado
── Terceira metade: sabotagem por AMBIENTE (portão sem fixture de arquivo) ──
  ✓ aph-alvo-em-memoria-recusado → check-conformidade-aph.sh saiu 3 pelo motivo declarado
  ✓ aph-alvo-em-memoria-carimbado-quando-pedido → check-conformidade-aph.sh saiu 1 pelo motivo declarado
── Sabotagem: quanto foi examinado ──
  portões cobertos: 10  ·  bases válidas aceitas: 10/10
  sabotagens declaradas: 61  ·  reprovadas pelo motivo certo: 61/61
  sabotagens de ambiente: 2  ·  recusadas pelo motivo certo: 2/2
$ echo $?
0
```

Deste ciclo, nominalmente: as **10** de `scripts/check-trava-da-proposta.sh` (a mais
importante é `efeito-antes-da-reserva`, que **não olha texto e sim ordem de linhas**: mover a
reserva para depois do efeito deixa a trava inteira no lugar e inútil, e nenhuma varredura de
presença veria isso), as **7** de `scripts/check-manifesto.sh` e as **2 de ambiente** do
portão de conformidade APH — que só existem porque o achado A-04 mostrou que um portão pode
ser verde contra o alvo errado. Dentro da suíte de testes há ainda a mutação embutida da
política (`test_a_sabotagem_da_politica_derruba_o_teste_de_recusa`).

**O que não cobre**: a transição forçada e o `executed` mentiroso no lote têm teste, mas não
sabotagem de portão — o `TAIL:mutation` do `tasks.md` deste ciclo (T-18) pede as duas.
Dívida **Dv-3**.

## 8 · TAIL:gate — NÃO marcado, e o que aguarda o Product Steward

Neste ciclo o gate humano **é o produto**, e por isso a ausência dele pesa mais:

1. **Aprovar o catálogo `toc.*` ação a ação** — são **15 ações** hoje, e o portão do roadmap
   diz "aprovado ação a ação, com registro do gate". Nenhum registro existe.
2. **Decidir o vermelho A-05** (registro de telas × manifesto): a interface do M4 fecha a
   paridade, ou o manifesto recua até a tela existir? Enquanto a decisão não vier, a função
   de aptidão do APH-3.1 fica vermelha.
3. **Decidir a jornada dos quatro fluxos** (A-06): reabrir o 006 ou alocar ao 012.
4. **Responder os cinco `[DÚVIDA]` do Clarify**: catálogo ação a ação, TTL, atomicidade por
   ação, `idempotency_key` (que o achado A-01 respondeu na prática, com ADR) e o alcance da
   borda sob L-03.
5. **Ratificar `ART:ux-design=no`** (§4) num ciclo que entregou tela.
6. **Aceitar as seis dívidas do §9** e **autorizar a promoção**.

## 9 · Dívidas declaradas, com dono

| # | Dívida | Por quê | Dono |
|---|---|---|---|
| **Dv-1** | A cauda do `tasks.md` não é encontrável pelo portão de conformidade | Artefato de outro lote; editá-lo aqui seria mudança silenciosa de escopo | construtor do ciclo 006 |
| **Dv-2** | Três `ART:*` do `plan.md` declarados sem motivo, um deles (`ux-design=no`) substancialmente discutível | Idem | construtor do ciclo 006 + gate |
| **Dv-3** | Sabotagem de portão para transição forçada e `executed` mentiroso no lote (T-18) | Existem testes; falta a mutação que prove que o portão reprova | construtor do ciclo 006 |
| **Dv-4** | Passe de segurança em contexto fresco por **terceiro** | Maestro II: quem executa não verifica | revisor de segurança em contexto fresco |
| **Dv-5** | Tempo de resposta da borda federada (< 5 s) nunca medido | Não há medição de tempo em teste nenhum | construtor do ciclo 006 |
| **Dv-6** | `scripts/check-trava-da-proposta.sh` vermelho por caminho de escrita novo não classificado (§1.1) | O caminho é do M6 (spec 009), em construção agora; classificar é de quem o escreveu | **construtor do M6** |
| **Dv-7** | Paridade registro de telas × manifesto quebrada (A-05) | O manifesto andou com o M4 e a interface não | ciclo de interface do M4 |
| **Dv-8** | `ghd.action_result` não emitido pela interface (A-07) | O palpite de interface do §B.9.1 não sai daqui | ciclo de interface federada |

## 10 · Cauda

- **TAIL:review** — revisão independente em contexto fresco, com **10 achados numerados**
  (A-01 a A-10, §5) e 4 achados da avaliação heurística da J-03 sobre a superfície de decisão
  (§5.5). Quatro dos achados eram de severidade **Alta** e foram **corrigidos com a causa
  nomeada**: a proposta sem trava (uma aprovação humana executando oito vezes, reproduzida
  com `códigos {200: 8} · nós no banco 50 para 30 pedidos` **antes** do conserto e medida em
  `nós no banco 30 para 30 pedidos · títulos repetidos 0` depois), o `done` depois de `error`
  no fio, as duas grafias do mesmo código do §A.7 e o portão de conformidade APH que não
  dizia contra o que media. Três continuam **abertos e vermelhos** neste relatório (A-05,
  A-06, A-10) em vez de terem sido maquiados.
- **TAIL:security** — passe sobre 11 itens, **11 sem furo** (§6): borda sem credencial
  recusada, token desconhecido recusado sem dizer o motivo, curinga do hospedeiro descartado
  sem autorizar, capability verificada no caso de uso (com a sabotagem `lambda: True`
  derrubando os testes de recusa), snapshot com campo fora do registro rejeitado na borda e
  valor sensível que não atravessa, `params` validados contra o `input_schema`, nada
  executando sem gate (63 transições inválidas), uma aprovação = uma execução no PostgreSQL
  real, traço somente-acréscimo (`0 UPDATE/DELETE`), `scripts/check-vazamento.sh` sem achado
  sobre 579 arquivos e a política composta em 3 arquivos sobre 96 de produção. **Alcance
  declarado**: passe, não revisão independente por terceiro (Dv-4).
- **TAIL:mutation** — `scripts/tests/run-sabotagem.sh` saiu **0**: `portões cobertos: 10 ·
  bases válidas aceitas: 10/10` e `sabotagens declaradas: 61 · reprovadas pelo motivo certo:
  61/61`, mais `sabotagens de ambiente: 2 · recusadas pelo motivo certo: 2/2`. Deste ciclo
  são **10 + 7 + 2**: a trava da proposta (incluindo `efeito-antes-da-reserva`, que mede
  **ordem de linhas** e não presença de texto), o manifesto contra o schema normativo, e as
  duas de ambiente que nasceram do achado A-04. O que falta está em §7 e é a dívida Dv-3.
- **TAIL:gate** — **NÃO marcado, de propósito**, e neste ciclo isso é substantivo: aprovar o
  catálogo `toc.*` **ação a ação** é o portão humano que o roadmap nomeia, são 15 ações, e
  nenhum registro de aprovação existe. Os seis itens que aguardam assinatura estão em §8.
  Quem executou não aprova o que executou (Maestro II).

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
| `scripts/check-conformance.sh 006` | ver o bloco de conformidade acima | `1` |

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

**Executado e medido; NÃO fechado, e com vermelho vivo.** As ações governadas existem e são
sérias: verbo mutador nasce `action_proposal`, a matriz inteira de transições inválidas falha
com `INVALID_TRANSITION`, o catálogo encolhe de 15 para 4 sem `toc:write` e para 0 no
anônimo, o snapshot é sanitizado no servidor com esquema fechado, o fio passa nos **11/11**
checks da suíte de conformidade do `GHDaru/protocolos`, e uma aprovação humana executa
**exatamente uma vez** contra o PostgreSQL real — o que só é verdade porque um crítico hostil
provou o contrário primeiro. O que está vermelho — a paridade do registro de telas, a jornada
dos quatro fluxos, e um portão derrubado por um caminho de escrita que outro lote acabou de
criar — está vermelho **aqui**, com dono. O gate humano deste ciclo é o catálogo, e ele não
foi dado.
