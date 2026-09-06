# QA report 004 — Núcleo de diagramas (M1)

> Siglas deste documento: **QA** — *Quality Assurance* (garantia de qualidade) · **DoD** —
> *Definition of Done* (Definição de Pronto) · **M1** — Núcleo de Diagramas Lógicos ·
> **M2** — Árvore da Realidade Atual (ARA) · **M3** — Nuvem de Conflito (NC) · **UDE** —
> Efeito Indesejável · **ADR** — *Architecture Decision Record* (Registro de Decisão
> Arquitetural) · **APH** — Aplicação ↔ Harness · **RF/RI/RNF/RN/INT** — requisito
> funcional / de interface / não funcional / regra de negócio / integração · **TDD** —
> *Test-Driven Development* · **OTel** — OpenTelemetry · **JSON** — *JavaScript Object
> Notation* · **SQL** — *Structured Query Language* · **i18n** — internacionalização.

- **Data da bateria**: 2026-09-06 · **Raia**: plena
- **Veredito atual**: **executado e medido; NÃO fechado.** Das 14 linhas da DoD, **8 estão
  verdes com saída colada**, **1 verde com ressalva declarada**, **4 VERMELHAS** e **1
  vermelha por causa externa já relatada**. As quatro vermelhas substantivas são a mesma
  ausência em duas famílias: **exportação/importação canônica** (linhas 4, 5 e 6) e a
  **função de aptidão de i18n** (linha 11).
- **O maior achado deste ciclo não está na DoD**: a raiz do agregado tinha uma porta dos
  fundos, e ela foi encontrada por revisão independente, **reproduzida antes do conserto** e
  fechada como classe. Está em §5, achado **A-01**.

> **R1 e R2 aplicadas linha a linha.** Toda saída foi executada em **2026-09-06**, entre
> 04:50Z e 05:30Z, e está **colada**.
>
> **Ressalva de medição.** O repositório **estava sendo construído enquanto era medido**
> (o lote do M6, spec 009): `apps/api/src/toc_api/infra/persistencia/repositorio_projetos.py`
> mudou às 05:06Z e `scripts/check-trava-otimista.sh` às 05:11Z. O mesmo comando de suíte
> devolveu `1201 passed` às 05:07Z e `1219 passed` às 05:19Z; o portão da trava otimista
> dizia `7 caminhos` às 04:50Z e `8 caminhos` às 05:28Z. Os números abaixo são os da segunda
> medição, e a volatilidade está dita ao lado — que é o que a regra R1 cobra de quem cola
> saída.

## 0 · Histórico de veredito — os estados por que este ciclo passou

| # | Data | Estado | O que aconteceu | Evidência |
|---|---|---|---|---|
| **V1** | 2026-09-05 | **construído** | Agregado `Projeto` (nós, arestas causais, exclusão suave reversível, versão), casos de uso com span de nascença, política por tipo de ação, migração `0002`, rotas REST e a interface (lista, lixeira, canvas, painel de entidades, desfazer de sessão). | `apps/api/src/toc_api/dominio/projeto.py`, `apps/api/src/toc_api/alembic/versions/0002_nucleo_m1_no_e_aresta.py` |
| **V2** | 2026-09-06 | **REPROVADO — porta dos fundos do agregado** | Revisão independente achou que as rotas genéricas de `/toc/projetos` abriam o `Projeto` **contido** nas raízes do M2 e do M3 e mutavam o grafo delas por fora. Reproduzido com saída colada **antes** de qualquer conserto. | §5, achado **A-01** |
| **V3** | 2026-09-06 | **REPROVADO — perda de atualização silenciosa** | Vinte escritas concorrentes respondiam vinte vezes `201 Created` e persistiam **um** nó. Medido contra o PostgreSQL real antes do conserto: `escritas aceitas: 20 · nós no banco depois: 1 · TRABALHO PERDIDO EM SILÊNCIO: 19 nó(s)`. | §5, achado **A-02** |
| **V4** | 2026-09-06 | **corrigido, e a classe fechada** | `Projeto._exigir_raiz` nas **oito** mutações de grafo + `Projeto.versao_lida`/`confirmar_gravacao()` + `UPDATE … WHERE versao = :versao_lida`. Dois portões novos, com sabotagem própria. | §5, §7 |
| **V5** | 2026-09-06 | **medido** | Esta bateria: 14 linhas com comando, saída colada e denominador. **8 verdes · 1 com ressalva · 5 vermelhas** (4 nossas, 1 externa). | §2 |
| **V6** | — | **aguardando gate humano** | `TAIL:gate` **não marcado**. | §8 |

## 1 · Bateria de portões (denominador colado — regra R2)

`scripts/evidencia.sh` saiu **0** com `Portões executados: 17 · verdes: 17 · vermelhos: 0.`
Os que este ciclo mais toca:

| # | Portão | Código | Denominador — a linha do próprio portão |
|---|---|---|---|
| G1 | `scripts/check-arquitetura.sh` (P3 — DDD + hexagonal) | **0** ✓ | `contratos declarados no pyproject.toml: 3` · `Analyzed 114 files, 629 dependencies.` · `Contracts: 3 kept, 0 broken.` |
| G2 | `scripts/check-raiz-do-agregado.sh` (DDD — a correção de A-01 virada portão) | **0** ✓ | `operação só pela raiz: 8 guardas, 6 raízes, 192 arquivos varridos.` |
| G3 | `scripts/check-trava-otimista.sh` (a correção de A-02 virada portão) | **0** ✓ | `caminhos de escrita conferidos: 8 declarados · 8 encontrados no adaptador` · `guardas _gravar_projeto encontradas: 8 de 8` |
| G4 | `scripts/check-politica.sh` (autorização fora do modelo) | **0** ✓ | `arquivos de produção varridos: 96` · `arquivos que compõem PoliticaPorCapability: 3` |
| G5 | `scripts/check-vazamento.sh` (ADR 0006) | **0** ✓ | `arquivos varridos: 579 · linhas varridas: 131024 · registros JSON inspecionados: 3364` |
| G6 | `scripts/check-jornadas.sh` (P6) | **0** ✓ | `jornadas examinadas: 4` · `capturas em disco: 36 · citações de imagem: 36` · `verificações executadas: 80` |
| G7 | `scripts/check-caminhos.sh` · `scripts/check-links.sh` | **0** ✓ | `caminhos conferidos: 1005 · isentos declarados: 330` · `checked: 469` |
| G8 | `scripts/check-conformance.sh 004` | **1** ✗ | `cycles checked: 1` — **vermelho, diagnóstico em §4** |

## 2 · DoD — as 14 linhas da spec, com comando, saída colada e veredito

> **Ajuste de caminho declarado.** A coluna "Verificação executável" da spec cita
> `tests/domain/…`, `tests/application/…`, `tests/integration/…` e as duas árvores que ela
> chama de *backend* e *frontend*.
> A árvore real deste repositório é `apps/api/tests/dominio/…`, `…/aplicacao/…`,
> `…/integracao/…`, `apps/api/src/toc_api/` e `apps/web/src/` — decidida no ciclo 003 e
> escrita no brief de construção §3. Os comandos abaixo são **os mesmos critérios sobre os
> caminhos que existem**. Todos rodam de `apps/api`, com `DATABASE_URL` exportada e
> `apps/api/.venv/bin` no `PATH`.

| # | Critério | Comando | Saída (colada) | Examinou | Código | Veredito |
|---|---|---|---|---|---|---|
| 1 | Domínio puro, testes sem rede | `pytest tests/dominio -q` + `lint-imports` | `484 passed in 0.87s` · `Analyzed 114 files, 630 dependencies.` · `Contracts: 3 kept, 0 broken.` | 484 testes de domínio, todos offline; 3 contratos de arquitetura sobre 114 arquivos e 630 dependências | `0` · `0` | ✓ verde |
| 2 | Teste do filtro de exclusão (F-06) existe e passa | `pytest tests/dominio/test_grafo_do_projeto.py -k "excluir" -v` | `3 passed, 12 deselected in 0.09s`, com `test_excluir_no_remove_exatamente_o_no_e_suas_arestas_incidentes PASSED` | 3 casos: o nó e suas arestas incidentes, o nó isolado que não toca aresta nenhuma, e a aresta que não toca os nós | `0` | ✓ verde |
| 3 | Exclusão suave reversível | `pytest tests/dominio/test_projeto.py -k "exclusao or restaurar" -v` | `2 passed, 11 deselected in 0.10s`, com `test_exclusao_e_reversivel_e_preserva_o_conteudo PASSED` | 2 casos no domínio; a travessia pelo banco real é `test_exclusao_e_reversivel_no_banco_real`, dentro dos `6 passed` da linha 7 | `0` | ✓ verde |
| 4 | Ida e volta do export | `grep -rn "class .*Export\|class .*Import\|Exportar\|Importar" apps/api/src/toc_api/aplicacao/` | **saída vazia** | a camada de aplicação inteira | `1` | ✗ **VERMELHO** — ver A-03 |
| 5 | Export determinístico | — | — | — | — | ✗ **VERMELHO** — ver A-03 |
| 6 | Importação inválida recusa com relato | — | — | — | — | ✗ **VERMELHO** — ver A-03 |
| 7 | Isolamento por inquilino | `pytest "tests/integracao/test_migracao_e_isolamento.py::test_isolamento_por_inquilino_no_banco_real" -v` | `1 passed in 1.37s` | dois inquilinos no PostgreSQL real, interseção vazia; o arquivo inteiro dá `6 passed in 6.77s` | `0` | ✓ verde |
| 8 | Toda mutação com traço | `pytest tests/aplicacao/test_caso_de_uso_e_span.py tests/aplicacao/test_casos_de_uso_do_grafo.py -q` | `14 passed in 0.16s` | 14 casos. A garantia não é "cada autor lembrou": o span é aberto pela **classe-base** `CasoDeUso.rodar` (`apps/api/src/toc_api/aplicacao/casos_de_uso.py`), e a recusa também é traço — o `except` marca `toc.resultado=erro` e **reergue** | `0` | ✓ verde |
| 9 | Política por tipo de ação no servidor | `scripts/check-politica.sh` | `arquivos de produção varridos: 96` · `arquivos que compõem PoliticaPorCapability: 3` · `✓ a sabotagem vive só na definição; a política real está composta.` | 96 arquivos de produção; o portão existe porque a sabotagem `lambda: True` da política é a que derruba os testes de recusa | `0` | ✓ verde |
| 10 | Sem segredo no cliente | `grep -rniE "api[_-]?key\|secret" apps/web/src/ \| wc -l` | `6` | as 6 ocorrências abertas uma a uma: são a palavra **portuguesa** "secreta" nos testes de tema (`"font-family-secreta"`, `"color-secreta"`), e as três asserções provam que o token **fora da lista de permissão é descartado** — o oposto de um segredo no cliente | `0` (grep) | ⚠ **verde no conteúdo, vermelho na letra** — ver A-05 |
| 11 | i18n sem literal solto | `grep -rln "literal" scripts/*.sh` | nenhum portão de literal; os cinco arquivos que casam usam a palavra em comentário | os 20 portões de `scripts/`; o que existe é **paridade de dicionários** (`apps/web/src/i18n/i18n.test.tsx`, 9 testes: mesmas chaves, nenhuma tradução vazia, todo código de serviço com texto nos dois idiomas) — que é outra coisa | `1` | ✗ **VERMELHO** — ver A-04 |
| 12 | Jornada viva presente | `scripts/check-jornadas.sh` | `jornadas examinadas: 4` · `capturas em disco: 36 · citações de imagem: 36 · data das capturas (manifesto): 2026-09-06` · `verificações executadas: 80` | a jornada do M1 é `docs/jornadas/002-primeiro-projeto-e-ara.md`, com capturas do build real geradas por `docs/jornadas/scripts/capturar-telas.mjs` e avaliação heurística datada (7 achados, §5.3) | `0` | ✓ verde |
| 13 | Conformidade do ciclo | `scripts/check-conformance.sh 004` | ver §4 | `cycles checked: 1` | `1` | ✗ **vermelho — duas causas, uma externa e uma nossa** |
| 14 | Caminhos e links do ciclo | `scripts/check-caminhos.sh` · `scripts/check-links.sh` | `✓ todo caminho citado entre crases existe.` (`caminhos conferidos: 1005 · isentos declarados: 330`) · `✓ every relative link resolves.` (`checked: 469`) | 125 arquivos varridos · 469 links | `0` · `0` | ✓ verde |

**Placar da DoD: 8 verdes · 1 verde com ressalva declarada · 5 vermelhas** (4 substantivas +
a de conformidade).

## 3 · Portões nomeados do roadmap (ciclo 004)

| Portão | Como se verificou | Evidência colada |
|---|---|---|
| O filtro de exclusão do defeito da linhagem tem teste-testemunha | `pytest tests/dominio/test_grafo_do_projeto.py -k "excluir" -v` | `3 passed, 12 deselected in 0.09s` |
| Domínio e aplicação sem framework (P3) | `lint-imports` | `Contracts: 3 kept, 0 broken.` sobre `Analyzed 114 files, 630 dependencies.` |
| Toda mutação do M1 atravessa o banco real | `pytest tests/integracao/test_grafo_e_ara_no_postgres.py tests/contrato/test_http_m1.py -q` | `20 passed, 2 warnings in 12.00s` (contrato HTTP) + os `6 passed` de migração e isolamento |
| Exportação canônica ida-e-volta | — | ✗ **não existe** (A-03) |

## 4 · O portão vermelho de conformidade, diagnosticado

```text
$ scripts/check-conformance.sh 004
• 004-nucleo-de-diagramas
    ✓ Constitution Check complete (8/8)
    · acceptance-criteria checkboxes: not checked below cycle 45
    ✗ data-model: declared ART:data-model=yes with no reason — a declaration without a why is silence
    ✗ contracts: declared ART:contracts=yes with no reason — a declaration without a why is silence
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

**Três causas, e elas não são a mesma coisa:**

1. **Externa, já relatada** — os pisos absolutos (`55`, `61`) do script do método, que num
   repositório que vai até o ciclo `012` são verdadeiros para sempre.
   `mensagens/002-para-maestro-pisos-absolutos-de-ciclo.md`; `GHDaru/maestro` é leitura (P1).
2. **Nossa, e é real** — as três linhas `tasks.md has no TAIL:*`. O
   `specs/004-nucleo-de-diagramas/tasks.md` **tem** a cauda, mas escrita como
   `- [ ] T-16 — \`TAIL:review\` — …`, e o portão ancora no token no **início** do item. Não
   é falso positivo: o formato do template existe para a cauda ser encontrável por máquina.
   Registrado como **A-06** e dívida **Dv-1**.
3. **Nossa, no `plan.md`** — `ART:data-model` e `ART:contracts` declarados sem o motivo
   escrito ao lado. Dívida **Dv-2**.

Nenhuma das três foi afrouxada, e nenhum piso foi apertado para o verde aparecer.

## 5 · TAIL:review — a revisão independente, com os achados numerados

### 5.1 · O achado central: o agregado com porta dos fundos

**A-01 · A raiz do agregado deixou de ser o único caminho para o estado dela.** Achado por
revisão independente e **reproduzido antes de qualquer conserto**. As ferramentas M2 (ARA) e
M3 (NC) são raízes **por composição**: contêm um `Projeto` do M1. Esse `Projeto` é a **mesma
linha de banco** que as rotas genéricas de `/toc/projetos` abrem — duas portas para o mesmo
estado, invariantes numa só. A reprodução, colada da execução de antes do conserto:

```text
nasceu: 5 entidades, 7 arestas
DELETE aresta D_D_PRIME pela rota generica -> 204
GET /toc/nc/projetos/{id} depois -> 404 {"error":{"code":"NOT_FOUND","message":"recurso não encontrado"}}
DELETE entidade A pela rota generica -> 200 {"no_id":"…","arestas_removidas":["…","…"]}
```

A nuvem **sumia da leitura** — `404` sobre um projeto que continuava no banco — e a resposta
da mutilação era `204 No Content`.

**Causa raiz**: a fronteira do agregado estava escrita em prosa e numa classe invólucra, não
no objeto que guarda o estado. `Projeto.ferramenta` era um rótulo de filtro.

**Destino — corrigido, matando a classe e não o caso**: `Projeto._exigir_raiz` recusa as
**oito** mutações de grafo quando a ferramenta não é a genérica, e a única destrava é
`Projeto.sob_a_raiz()`, usada por dentro das raízes; **fail-closed por construção** (uma
ferramenta nova nasce bloqueada mesmo sem se registrar). A mesma exposição foi procurada nas
outras invariantes e achada em cinco lugares — inclusive na **terceira porta**, que fechar as
rotas teria deixado aberta: o executor do catálogo federado
(`apps/api/src/toc_api/infra/federacao/executor.py`) montava os mesmos casos de uso genéricos,
e uma ação governada **aprovada por gate humano** mutilaria a nuvem igual.

Verificação de hoje:

```text
$ cd apps/api && pytest tests/dominio/test_raiz_do_agregado.py \
      tests/federacao/test_porta_dos_fundos_do_catalogo.py \
      tests/contrato/test_http_porta_dos_fundos.py -q
33 passed, 2 warnings in 1.29s

$ scripts/check-raiz-do-agregado.sh
✓ operação só pela raiz: 8 guardas, 6 raízes, 192 arquivos varridos.
```

### 5.2 · Os demais achados

| # | Achado | Severidade | Destino |
|---|---|---|---|
| **A-02** | **Perda de atualização silenciosa entre duas pessoas na mesma análise.** Vinte escritas concorrentes de nó respondiam vinte vezes `201 Created` e persistiam **um** nó: o adaptador gravava o *retrato* do agregado em memória e a reconciliação apagava toda linha fora dele. Causa raiz em duas metades — a escrita era incondicional **e** o agregado não guardava de que versão tinha partido (a coluna `versao` era um contador, não uma trava). Medido antes do conserto: `escritas aceitas: 20 · nós no banco depois: 1 · TRABALHO PERDIDO EM SILÊNCIO: 19 nó(s)` | **Alta** | ✅ **corrigido** (ADR 0010): `Projeto.versao_lida` + `confirmar_gravacao()`, `UPDATE … WHERE versao = :versao_lida`, `409 VERSION_CONFLICT` no §A.7, e o duplo em memória com a mesma trava. Medido depois: `concorrência M1: 20 escritas · aceitas 1 · recusadas 19 · nós no banco 1`; `concorrência HTTP: 20 requisições · 201 1 · 409 19 · outros []` |
| **A-03** | **A exportação/importação canônica (épico E1.4, tarefa T-09) não existe** — e três linhas da DoD (4, 5 e 6) dependem dela. O que existe é a ação `toc.exportar_projeto` do catálogo, que devolve **contagens** (`{"projeto_id", "nome", "nos", "arestas"}`, `apps/api/src/toc_api/infra/federacao/executor.py:219-231`), não um documento versionado que se reimporte | **Média** | ✗ **VERMELHO assumido**. Dono: **ciclo 011** (é onde a exportação canônica está alocada, e o `qa-report.md` do ciclo 008 declara a mesma pendência como P-04) |
| **A-04** | **A função de aptidão de i18n (linha 11 da DoD) não existe.** A paridade de dicionários existe e é boa (`apps/web/src/i18n/i18n.test.tsx`, 9 testes), mas ela responde "as duas línguas têm as mesmas chaves", e a pergunta do critério é outra: "há literal de interface fora do dicionário?" | Média | ✗ **VERMELHO assumido**. Dono: ciclo de interface, com a sabotagem que veja o portão reprovar |
| **A-05** | A linha 10 pede `= 0` e devolve `6`, todas a palavra portuguesa "secreta" em teste de tema. O critério, como escrito, reprova o repositório por **testar** o descarte de token não permitido | Baixa | 📝 registrado: o critério merece `--include` por extensão de produção, ou a isenção nomeada. É a mesma classe do achado A-01 do ciclo 003 e da pendência P-03 do ciclo 008 |
| **A-06** | A cauda do `specs/004-nucleo-de-diagramas/tasks.md` está escrita como `T-16 — \`TAIL:review\`` e o portão de conformidade não a encontra (§4, causa 2) | Baixa | 📝 registrado, **Dv-1**: é o `tasks.md` de outro lote; corrigir aqui seria mudança silenciosa de escopo |
| **A-07** | O nome do teste `test_o_catalogo_anonimo_e_vazio_e_o_identificado_tem_as_onze_acoes` diz **onze** e a asserção dele é `len(identificado) == 15` (`apps/api/tests/federacao/test_superficie_aph.py:245`). O teste está certo; o **nome** envelheceu quando o catálogo cresceu | Baixa | 📝 registrado — evidência envelhecida em nome de teste é a mesma classe que o `scripts/check-evidencia-colada.sh` pega em documento. Dono: ciclo 006 (é o catálogo dele) |

### 5.3 · Achados da avaliação heurística da jornada J-02 (2026-09-06)

Transcritos de `docs/jornadas/002-primeiro-projeto-e-ara.md` — a jornada que cobre o M1 e o
M2. Sete achados, dois de severidade **Alta**:

| # | Achado | Severidade | Destino |
|---|---|---|---|
| J-02/A-02 | Depois de "Reformular", a ficha continua mostrando o texto e o veredito **antigos** até ser fechada e reaberta | **Alta** | 📝 registrado — código de produção da interface, entra por ciclo com teste que falha antes (P4) |
| J-02/A-03 | A área de trabalho cresce com o painel (2 762 px numa janela de 900 px) e "Ajustar à tela" enquadra a árvore **abaixo da dobra**: o canvas visível fica vazio com 16 nós no projeto | **Alta** | 📝 registrado |
| J-02/A-01 | A rota vive no estado do React e não na URL: recarregar devolve à lista, e não há como enviar o link de uma árvore | Média | 📝 registrado |
| J-02/A-04 | Na largura padrão do painel, a coluna "Ações" fica cortada ("Exclu…", "Foca no canva…") | Média | 📝 registrado |
| J-02/A-05 | O relatório estrutural lista os 16 elos não examinados por identificador universal, que não diz a ninguém qual elo é | Média | 📝 registrado |
| J-02/A-06 | O filtro por status filtra o painel e **não** o canvas, e a assimetria não é anunciada | Baixa | 📝 registrado |
| J-02/A-07 | A leitura do elo concatena as frases sem tratar a pontuação: *"…duplicação da oferta., então…"* | Baixa | 📝 registrado |

## 6 · TAIL:security — o passe, item a item

| Item | Como se verificou | Resultado |
|---|---|---|
| Segredo no cliente | `grep -rniE "api[_-]?key\|secret" apps/web/src/` | `6` ocorrências, **0 segredos** — a palavra "secreta" em teste de tema (§2, linha 10) |
| Isolamento por inquilino | `test_isolamento_por_inquilino_no_banco_real` no PostgreSQL real | ✓ `1 passed` |
| Fail-closed da autorização | `scripts/check-politica.sh` + `test_a_sabotagem_da_politica_derruba_o_teste_de_recusa` | ✓ 96 arquivos de produção varridos; a sabotagem `lambda: True` **derruba** os testes de recusa |
| Excluir projeto de outro inquilino | `test_excluir_projeto_de_outro_inquilino_e_nao_encontrado_nunca_proibido` | ✓ responde "não encontrado", nunca "proibido" — não vaza existência |
| Fronteira do agregado (a terceira porta) | `apps/api/tests/federacao/test_porta_dos_fundos_do_catalogo.py` | ✓ dentro dos `33 passed`: nem uma ação governada aprovada por gate humano mutila a nuvem pela rota genérica |
| Escrita concorrente | `apps/api/tests/integracao/test_concorrencia_no_postgres.py` | ✓ `6 passed in 8.94s`; `concorrência HTTP: 20 requisições · 201 1 · 409 19 · outros []` |
| Dado real de pessoa em fixture/captura (ADR 0006) | `scripts/check-vazamento.sh` | ✓ `0` achados sobre `579` arquivos, `131024` linhas, `3364` registros JSON |
| Payload de importação | — | **não aplicável hoje**: a importação não existe (A-03). Quando existir, este item volta |

**Alcance declarado**: é passe medido por quem executou a bateria, não revisão independente
de segurança por terceiro em contexto fresco (Maestro II). Fica como **Dv-3**.

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

As que são **deste ciclo**, nominalmente: as três de `scripts/check-raiz-do-agregado.sh`
(chave do núcleo vazando para a aplicação, mutação sem guarda, ferramenta que não se
registra) e as oito de `scripts/check-trava-otimista.sh` (uma por peça da correção de A-02).
As duas famílias existem porque o `import-linter` **não as veria**: ele mede **direção** de
import, e `aplicacao → dominio` é o sentido permitido — uma camada de fora pegando a chave do
núcleo passa por ele em silêncio.

**O que não cobre**: mutação sobre o filtro de exclusão em cascata e sobre a validação de
importação, que é o que o `TAIL:mutation` do `tasks.md` deste ciclo pede nominalmente (T-18).
A segunda não tem como existir enquanto a importação não existir (A-03). Fica como **Dv-4**.

## 8 · TAIL:gate — NÃO marcado, e o que aguarda o Product Steward

1. **Aceitar as quatro linhas vermelhas** (4, 5, 6 e 11) como dívida com dono — ou reabrir o
   ciclo para fechá-las antes da promoção.
2. **Ratificar a ressalva da linha 10** (A-05) e decidir se o critério é reescrito na spec,
   como o ciclo 001 fez com a linha 11 dele.
3. **Decidir os quatro `[DÚVIDA]` do Clarify** que a abertura deste ciclo listava: retenção
   da lixeira, concorrência, matriz papel × ação e teto de nós. A concorrência **deixou de
   ser dúvida aberta na prática** — o achado A-02 a respondeu com um ADR (0010) —, mas a
   ratificação é humana.
4. **Aceitar as cinco dívidas do §9.**
5. **Autorizar a promoção** — o procedimento está em `docs/governance/como-fechar-um-ciclo.md`.

## 9 · Dívidas declaradas, com dono

| # | Dívida | Por quê | Dono |
|---|---|---|---|
| **Dv-1** | A cauda do `tasks.md` não é encontrável pelo portão (A-06) | É artefato de outro lote; editar `tasks.md` alheio dentro de um lote de QA é mudança silenciosa de escopo | construtor do ciclo 004, na reabertura |
| **Dv-2** | `ART:data-model` e `ART:contracts` do `plan.md` declarados sem o motivo | Idem | construtor do ciclo 004 |
| **Dv-3** | Passe de segurança em contexto fresco por **terceiro** | Maestro II: quem executa não verifica | revisor de segurança em contexto fresco |
| **Dv-4** | Mutação sobre o filtro de exclusão em cascata (T-18) | As 61 sabotagens cobrem portões; esta é sobre uma função de domínio | construtor do ciclo 004 |
| **Dv-5** | Exportação/importação canônica (E1.4, T-09) — linhas 4, 5 e 6 da DoD | Alocada ao ciclo 011; o `qa-report.md` do ciclo 008 declara a mesma pendência (P-04) | **ciclo 011** |
| **Dv-6** | Função de aptidão de i18n (linha 11) | Não existe; a paridade de dicionários responde outra pergunta | ciclo de interface |

## 10 · Cauda

- **TAIL:review** — revisão independente em contexto fresco, com **7 achados numerados**
  (A-01 a A-07, §5) e **7 achados** da avaliação heurística datada da jornada J-02 (§5.3). Os
  dois de severidade Alta do código — a porta dos fundos do agregado e a perda de atualização
  silenciosa — foram **reproduzidos antes do conserto** (`404` sobre projeto vivo;
  `TRABALHO PERDIDO EM SILÊNCIO: 19 nó(s)`) e fechados como **classe**, não como caso:
  `33 passed` nos três arquivos de teste da fronteira e
  `✓ operação só pela raiz: 8 guardas, 6 raízes, 192 arquivos varridos.` Três achados viraram
  vermelho assumido na DoD (A-03, A-04) em vez de serem maquiados.
- **TAIL:security** — passe sobre 8 itens, **7 verificados sem furo e 1 não aplicável**
  (§6): segredo no cliente (6 ocorrências, 0 segredos), isolamento no banco real,
  fail-closed com a sabotagem da política derrubando os testes de recusa, exclusão cruzada
  que responde "não encontrado" e nunca "proibido", a **terceira porta** do executor federado
  fechada, escrita concorrente com `201 1 · 409 19`, e
  `scripts/check-vazamento.sh` sobre 579 arquivos sem um achado. **Alcance declarado**:
  passe, não revisão independente por terceiro (Dv-3).
- **TAIL:mutation** — `scripts/tests/run-sabotagem.sh` saiu **0**: `portões cobertos: 10 ·
  bases válidas aceitas: 10/10` e `sabotagens declaradas: 61 · reprovadas pelo motivo certo:
  61/61`. Deste ciclo, nominalmente, as **3** de `scripts/check-raiz-do-agregado.sh` e as
  **8** de `scripts/check-trava-otimista.sh` — as duas famílias que o `import-linter` não
  veria, porque ele mede direção de import e não quem segura a chave do núcleo. O que falta
  está em §7 e é a dívida Dv-4.
- **TAIL:gate** — **NÃO marcado, de propósito.** A DoD fechou **8 verdes, 1 com ressalva e 5
  vermelhas**, quatro delas substantivas e com dono escrito. Os cinco itens que aguardam
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
| `scripts/check-conformance.sh 004` | ver o bloco de conformidade acima | `1` |

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

**Executado e medido; NÃO fechado.** O núcleo de diagramas existe, é domínio puro provado por
`Contracts: 3 kept, 0 broken.`, atravessa o PostgreSQL real, tem exclusão suave reversível e
traço de nascença em toda mutação — e **sobreviveu a dois achados de revisão independente que
teriam custado caro em produção**: um agregado com porta dos fundos e uma perda de atualização
silenciosa entre duas pessoas na mesma análise. Os dois foram reproduzidos antes do conserto e
fechados como classe, com portão e sabotagem próprios. O que **não** existe — exportação
canônica e função de aptidão de i18n — está vermelho neste relatório, com dono. O gate humano
é o próximo passo.
