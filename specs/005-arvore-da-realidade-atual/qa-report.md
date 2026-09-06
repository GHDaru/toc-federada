# QA report 005 — Árvore da Realidade Atual (M2)

> Siglas deste documento: **QA** — *Quality Assurance* (garantia de qualidade) · **DoD** —
> *Definition of Done* (Definição de Pronto) · **UDE** — Efeito Indesejável (*Undesirable
> Effect*) · **ARA** — Árvore da Realidade Atual · **NC** — Nuvem de Conflito · **M1** —
> Núcleo de Diagramas Lógicos · **M2** — a ARA · **FSM** — máquina de estados finitos ·
> **IA** — inteligência artificial · **SDK** — *Software Development Kit* · **ADR** —
> *Architecture Decision Record* (Registro de Decisão Arquitetural) · **APH** — Aplicação ↔
> Harness · **RF/RN/RNF** — requisito funcional / regra de negócio / não funcional ·
> **AST** — árvore sintática abstrata · **p95** — percentil 95.

- **Data da bateria**: 2026-09-06 · **Raia**: plena
- **Veredito atual**: **executado e medido; NÃO fechado.** Das 14 linhas da DoD, **10 estão
  verdes com saída colada**, **2 verdes com ressalva declarada**, **1 VERMELHA** (linha 10 —
  as ações `toc.*` do M2 **executam** desde o ciclo 006, e a mudança de escopo nunca foi
  declarada onde devia) e **1 vermelha por causa externa já relatada** (conformidade).
- **O que este ciclo fechou e vale dizer primeiro**: o **defeito D-12 da linhagem** — os onze
  critérios de UDE que quatro gerações do TOC-Builder carregaram **apenas como texto de
  prompt**, sem nenhum jamais ter sido executado — virou regra de domínio pura, testável sem
  rede e sem modelo. E o **falso negativo K-03**, o único defeito que o conjunto de controle
  externo do ciclo 001 achou nas checagens, **está fechado** com o teste que nasceu vermelho
  (§5.1).

> **R1 e R2 aplicadas linha a linha.** Toda saída foi executada em **2026-09-06**, entre
> 04:50Z e 05:35Z, e está **colada**.
>
> **Ressalva de medição.** O repositório **estava sendo construído enquanto era medido** (o
> lote do M6, spec 009). O mesmo comando de suíte devolveu `1201 passed` às 05:07Z e
> `1219 passed` às 05:19Z; `apps/api/src/toc_api/dominio/ara.py` tem mtime 03:51Z e o
> adaptador de persistência mudou às 05:06Z. Os números abaixo são os da medição mais
> recente, com a volatilidade dita ao lado.

## 0 · Histórico de veredito — os estados por que este ciclo passou

| # | Data | Estado | O que aconteceu | Evidência |
|---|---|---|---|---|
| **V1** | 2026-09-05/06 | **construído** | Validação formal como oito checagens puras (CD-1 a CD-8), corpus sintético versionado, FSM de status com a RN-10, `ProjetoARA` como raiz por composição sobre o M1, conector E, análise estrutural pura, migração `0003`, rotas `/toc/ara` e a interface da ficha e do canvas. | `apps/api/src/toc_api/dominio/criterios_ude.py`, `apps/api/src/toc_api/dominio/ara.py`, `apps/api/src/toc_api/alembic/versions/0003_m2_ude_exame_e_conector.py` |
| **V2** | 2026-09-06 | **teste vermelho do lote fechado** | O falso negativo **K-03** herdado do ciclo 001 (a checagem CD-7 aprovava "Falta de treinamento causa erros." porque procurava conectivos e não o **verbo causal**) passou a reprovar, com o trecho apontado. | §5.1 |
| **V3** | 2026-09-06 | **REPROVADO — a ARA tinha quatro exposições pela porta dos fundos** | A revisão independente que achou a porta dos fundos do agregado (ciclo 004) procurou a mesma exposição nas invariantes da ARA e **achou quatro**: elo sem exame de suficiência, UDE órfão, conector E com aresta fantasma e UDE reescrito sem revalidar. | §5.2, achado **A-01** |
| **V4** | 2026-09-06 | **corrigido** | Oito casos de uso do grafo da ARA **pela raiz** e as rotas `POST/PATCH/DELETE /toc/ara/projetos/{id}/nos\|arestas`; a rota de efeitos deixou de rodar o caso de uso genérico. | §5.2 |
| **V5** | 2026-09-06 | **medido** | Esta bateria: 14 linhas com comando, saída colada e denominador; e as três métricas de RNF **medidas**, não estimadas (§4). | §2, §4 |
| **V6** | — | **aguardando gate humano** | `TAIL:gate` **não marcado**. | §8 |

## 1 · Bateria de portões (denominador colado — regra R2)

`scripts/evidencia.sh` saiu **0** com `Portões executados: 17 · verdes: 17 · vermelhos: 0.`

| # | Portão | Código | Denominador — a linha do próprio portão |
|---|---|---|---|
| G1 | `scripts/check-arquitetura.sh` (P3) | **0** ✓ | `contratos declarados no pyproject.toml: 3` · `Analyzed 114 files, 629 dependencies.` |
| G2 | `scripts/check-raiz-do-agregado.sh` | **0** ✓ | `operação só pela raiz: 8 guardas, 6 raízes, 192 arquivos varridos.` |
| G3 | `scripts/check-trava-otimista.sh` | **0** ✓ | `caminhos de escrita conferidos: 8 declarados · 8 encontrados no adaptador` |
| G4 | `scripts/check-vazamento.sh` (ADR 0006) | **0** ✓ | `arquivos varridos: 579 · linhas varridas: 131024 · registros JSON inspecionados: 3364` |
| G5 | `scripts/check-jornadas.sh` (P6) | **0** ✓ | `jornadas examinadas: 4 · capturas em disco: 36 · citações de imagem: 36` · `verificações executadas: 80` |
| G6 | `scripts/check-politica.sh` | **0** ✓ | `arquivos de produção varridos: 96` |
| G7 | `scripts/check-caminhos.sh` · `scripts/check-links.sh` | **0** ✓ | `caminhos conferidos: 1005 · isentos declarados: 330` · `checked: 469` |
| G8 | `scripts/check-conformance.sh 005` | **1** ✗ | `cycles checked: 1` — diagnóstico em §4.1 |

## 2 · DoD — as 14 linhas da spec, com comando, saída colada e veredito

> **Ajuste de caminho declarado.** A spec cita três arquivos de teste que não existem com
> aquele nome — um de status de validação, um de conector E e um de traço do M2, todos sob
> as árvores de teste em inglês que o planejamento supunha (os caminhos exatos estão na
> spec, §Critérios de aceite). A árvore real é
> `apps/api/tests/dominio/…` e os testes de FSM e de conector E vivem em
> `apps/api/tests/dominio/test_ara.py`, junto do agregado que eles guardam — o critério é o
> mesmo, o arquivo é outro, e dizê-lo é o mínimo. Todos os comandos rodam de `apps/api`.

| # | Critério | Comando | Saída (colada) | Examinou | Código | Veredito |
|---|---|---|---|---|---|---|
| 1 | Validação formal é domínio puro, offline | `pytest tests/dominio/test_validacao_formal.py -p no:cacheprovider -q` + `lint-imports` | `24 passed in 0.04s` · `Contracts: 3 kept, 0 broken.` | 24 casos sem rede e sem banco; 3 contratos de arquitetura sobre 114 arquivos | `0` · `0` | ✓ verde |
| 2 | Os casos canônicos da linhagem decidem certo (RF-12) | `pytest tests/dominio/test_validacao_formal.py -k canonic -v` | `4 passed, 20 deselected in 0.03s` — e a saída **nomeia cada caso**: `[Falta de treinamento causa erros.-False-CD-7]`, `[A taxa de erros no processo X é de 15%.-True-None]`, `[Precisamos de um novo software para gerenciar tarefas.-False-CD-5]`, `[Tarefas frequentemente ultrapassam o prazo.-True-None]` | 4 enunciados canônicos, cada um com o veredito **e a checagem** que o reprova | `0` | ✓ verde |
| 3 | Nenhum critério decidível depende de prompt | `grep -rn "promptText\|system_prompt" apps/api/src/toc_api/dominio/ apps/web/src/ \| wc -l` | `0` | o domínio inteiro do serviço e a árvore de interface inteira | `0` | ✓ verde |
| 4 | Corpus sintético cobre o léxico | `pytest tests/dominio/test_corpus_udes.py -q -s` | `corpus sintético v1.1.0: 66 enunciados maus · 8 bons · marcadores lexicais cobertos: 63/63` · `76 passed in 0.07s` | 74 enunciados do corpus + 63 marcadores lexicais, **todos** cobertos; a regra é "ampliar a heurística exige ampliar o corpus" | `0` | ✓ verde |
| 5 | FSM de status guarda a RN-10 | `pytest tests/dominio/test_ara.py -k "status or validado" -v` | `6 passed, 18 deselected in 0.12s`, com `test_validado_e_recusado_enquanto_houver_criterio_decidivel_vermelho PASSED`, `test_validado_e_recusado_sem_parecer_humano_confirmado PASSED` e `test_parecer_de_ia_sozinho_nunca_fecha_o_status PASSED` | 6 casos. O terceiro é o que importa para o P2: **parecer de IA sozinho nunca fecha o status** | `0` | ✓ verde |
| 6 | Conector E validado no domínio | `pytest tests/dominio/test_ara.py -k "conector or conjun" -v` | `5 passed, 19 deselected in 0.11s`: destino único, mínimo de duas arestas, uma aresta em no máximo um conector por destino, leitura em conjunção e desfazer que solta as arestas | 5 casos | `0` | ✓ verde |
| 7 | Análise estrutural pura e correta | `pytest tests/dominio/test_analise_estrutural.py -q` | `11 passed in 0.11s` | 11 casos sobre grafos de fixture: fragmentos, entradas, alcance transitivo, UDEs não alcançados, elos não examinados, órfãos, ciclos e causa raiz candidata | `0` | ✓ verde |
| 8 | Ciclos fora da causa raiz candidata (RF-29) | `pytest tests/dominio/test_analise_estrutural.py -k ciclo -v` | `1 passed, 10 deselected in 0.10s`: `test_ciclo_e_listado_e_seus_nos_ficam_fora_da_causa_raiz_candidata PASSED` | o caso exato da RF-29 | `0` | ✓ verde |
| 9 | Toda mutação nova com traço | `pytest tests/aplicacao/test_casos_de_uso_da_ara.py -q` | `7 passed in 0.14s` | 7 casos de uso do M2. A garantia é estrutural: o span é aberto pela classe-base `CasoDeUso.rodar`, e a recusa também deixa span (`toc.resultado=erro`) antes de reerguer | `0` | ✓ verde |
| 10 | Ações `toc.*` declaradas sem executar | `ls specs/005-arvore-da-realidade-atual/` | `arvores  plan.md  qa-report.md  spec.md  tasks.md` — **não há diretório de contratos** | as duas metades do critério: o arquivo de declaração das 5 ações **não existe**, e a segunda metade ("nenhuma rota de execução") **foi deliberadamente revogada** pelo ciclo 006, que fez as ações executarem pela FSM do servidor | `2` | ✗ **VERMELHO** — ver A-03 |
| 11 | Sem SDK, chave ou prompt no produto | `grep -rniE "genai\|openai\|anthropic\|api[_-]?key" apps/api/src/ apps/web/src/` | `3`, e as três são `apps/api/src/toc_api/dominio/federacao/snapshot.py:46`, `:58` e `:59` — a **denylist de segredos** do snapshot (`"api_key"`, `"apikey"` e o comentário que as explica) | as duas árvores de código-fonte | `0` (grep) | ⚠ **verde no conteúdo, vermelho na letra** — ver A-04 |
| 12 | Jornada viva da ARA sintética | `scripts/check-jornadas.sh` | `jornadas examinadas: 4 · capturas em disco: 36 · citações de imagem: 36 · data das capturas (manifesto): 2026-09-06` · `verificações executadas: 80` | `docs/jornadas/002-primeiro-projeto-e-ara.md` (a ARA da "Instituição Horizonte", 16 nós) e `docs/jornadas/007-a-travessia.md` (o encadeamento ARA → NC), as duas com captura do build real e heurística datada; o grep negativo de nome real é o portão de vazamento (G4) | `0` | ✓ verde |
| 13 | Conformidade do ciclo | `scripts/check-conformance.sh 005` | ver §4.1 | `cycles checked: 1` | `1` | ✗ **vermelho — duas causas, uma externa** |
| 14 | Caminhos e links | `scripts/check-caminhos.sh` · `scripts/check-links.sh` | `✓ todo caminho citado entre crases existe.` (`caminhos conferidos: 1005 · isentos declarados: 330`) · `✓ every relative link resolves.` (`checked: 469`) | 125 arquivos · 469 links | `0` · `0` | ✓ verde |

**Placar da DoD: 10 verdes · 2 verdes com ressalva declarada · 2 vermelhas** (1 substantiva +
a de conformidade).

## 3 · Portão nomeado do roadmap (ciclo 005)

| Portão | Como se verificou | Evidência colada |
|---|---|---|
| Nenhum critério de UDE ficou dependente de prompt (revisão independente + grep) | grep sobre domínio e interface (linha 3 da DoD) **e** a paridade executável com o medidor do ciclo 001 | `0` no grep; e `paridade autoral: 12 UDEs examinados · reprovados pelo domínio: 9 (U-04 … U-12) · divergências com medir-base.py: 0` |
| O falso negativo K-03 do conjunto de controle fecha | `pytest tests/dominio/test_validacao_formal.py -k k03 -v` | `1 passed, 23 deselected in 0.02s` — `test_falso_negativo_do_conjunto_de_controle_k03_esta_fechado PASSED` |
| O conjunto de controle externo não ganhou falso positivo nem falso negativo novo | `pytest tests/dominio/test_paridade_com_medir_base.py -q -s` | `paridade de controle: 9 enunciados examinados · divergências: ['K-03'] (esperada: ['K-03'])` · `controle rotulado pela fonte: 6 enunciados · falso positivo: 0 · falso negativo: 0` |

## 4 · Medições registradas (RNF-04 / RNF-05 / RNF-06)

| Métrica | Alvo | Valor medido | Fonte |
|---|---|---|---|
| Validação formal de texto ≤ 500 caracteres | < 100 ms | **0,474 ms** — `RNF-04 (005) validacao formal: texto de 498 caracteres · p95 = 0.474 ms (teto 100 ms) · 200 execucoes` | medição sobre o domínio puro, 200 execuções, 2026-09-06 |
| Análise estrutural com 200 nós / 300 arestas (p95) | < 2 s | **20,123 ms** — `RNF-06 (005) analise estrutural: 200 nos, 299 arestas · p95 = 20.123 ms (teto 2000 ms) · 20 execucoes` | idem, 20 execuções (299 e não 300 porque um par sorteado seria auto-laço, que o domínio recusa — e o número dito é o medido) |
| Ciclo editar → reavaliar na ficha (p95) | < 1 s | — | ✗ **não medido**: é tempo de interface e exige o build real instrumentado. Dívida **Dv-5** |

**Alcance declarado, e ele importa**: as duas medições acima são de uma execução **ad-hoc**,
não de um script versionado no repositório. O número é real e foi produzido agora; a
*reprodutibilidade* dele por terceiro ainda não é. Isso é dívida (**Dv-6**), e escondê-la
seria trocar um defeito de honestidade por outro.

### 4.1 · O portão vermelho de conformidade

```text
$ scripts/check-conformance.sh 005
• 005-arvore-da-realidade-atual
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

Três causas: **(a)** os pisos absolutos do script do método, externos e já relatados em
`mensagens/002-para-maestro-pisos-absolutos-de-ciclo.md` (P1 — relatar e parar); **(b)** as
três linhas `TAIL:*`, que eram verdadeiras e que este documento fecha em §10; **(c)** a linha
`contracts: declared ART:contracts=yes but no contracts.md in the cycle` — que é **o mesmo
fato** da linha 10 da DoD, visto por outro portão (Dv-1).

## 5 · TAIL:review — a revisão independente, com os achados numerados

### 5.1 · O achado herdado do ciclo 001 que este ciclo fechou

**A ancestralidade do defeito importa.** O ciclo 001 mediu o **D-12** — os onze critérios de
UDE que a linhagem carregava só como prompt — e concluiu que **8 checagens cobrindo 7
características são decidíveis por função pura** e **4 exigem julgamento**. O gauntlet daquele
ciclo derrotou a visão de produto por **circularidade**: a base autoral fora escrita pelo
mesmo autor das checagens. O retrabalho colheu **9 enunciados de controle** da própria
linhagem, escritos antes das checagens e por outra mão, e mediu **1 falso negativo (K-03)** —
um defeito real, achado por um conjunto que não foi escrito para as checagens.

Este ciclo tinha o teste que nasce vermelho e a obrigação de fechá-lo:

```text
$ cd apps/api && pytest tests/dominio/test_validacao_formal.py -k k03 -v
tests/dominio/test_validacao_formal.py::test_falso_negativo_do_conjunto_de_controle_k03_esta_fechado PASSED [100%]
1 passed, 23 deselected in 0.02s
```

A causa era precisa e está escrita no próprio teste: a CD-7 procurava **conectivos**
("porque", "devido a", "já que") e não o **verbo causal** ("causa", "leva a", "resulta em"),
então aprovava "Falta de treinamento causa erros." — que a fonte rotula como exemplo ruim. Hoje
reprova, e a reprovação aponta o trecho: `reprovacao.trecho == "causa"`.

E a paridade com o medidor do ciclo 001 é **portão**, não promessa:

```text
$ cd apps/api && pytest tests/dominio/test_paridade_com_medir_base.py -q -s
  paridade autoral: 12 UDEs examinados · reprovados pelo domínio: 9 (U-04, U-05, U-06, U-07, U-08, U-09, U-10, U-11, U-12) · divergências com medir-base.py: 0
  paridade de controle: 9 enunciados examinados · divergências: ['K-03'] (esperada: ['K-03'])
  controle rotulado pela fonte: 6 enunciados · falso positivo: 0 · falso negativo: 0
4 passed in 0.03s
```

### 5.2 · A ARA pela porta dos fundos — quatro exposições, achadas porque foram procuradas

**A-01 · As invariantes da ARA eram alcançáveis pelas rotas genéricas do M1.** O achado da
porta dos fundos do agregado (relatado no `qa-report.md` do ciclo 004) não parou na Nuvem: a
revisão procurou a **mesma classe** nas invariantes da ARA e achou quatro, cada uma com o
requisito que ela viola:

| Exposição | Requisito ferido | O que acontecia |
|---|---|---|
| **Elo da ARA sem exame de suficiência** | RF-22 | `ProjetoARA.ligar` cria o `Exame`; `Projeto.ligar` não sabe que exame existe — e a ARA **não tinha rota de aresta**, então a própria tela do produto ligava pela rota genérica |
| **UDE órfão** | RF-05 | Pela rota genérica o nó sumia e a ficha ficava pendurada num identificador que não existe mais, sem `UdeArquivado` |
| **Conector E com aresta fantasma** | RN-11 | `_soltar_das_conjuncoes` só rodava dentro de `excluir_no`; **não havia** `ProjetoARA.excluir_aresta`, e o produto apagava pela rota genérica deixando o conector apontando para o vazio |
| **UDE reescrito sem revalidar** | RF-10 | `PATCH` genérico trocava o texto e o veredito formal anterior ficava pendurado |

**Destino — corrigido**: oito casos de uso do grafo da ARA pela raiz (`AdicionarEfeito`,
`EditarNoDaARA`, `MoverNoDaARA`, `RecolherNoDaARA`, `ExcluirNoDaARA`, `LigarNaARA`,
`EditarArestaDaARA`, `ExcluirArestaDaARA`), todos na política de capacidades, com as rotas
`POST/PATCH/DELETE /toc/ara/projetos/{id}/nos|arestas`; `ProjetoARA.editar_no` revalida no
mesmo ato; e a rota de efeitos deixou de rodar o caso de uso genérico. Verificação de hoje:

```text
$ cd apps/api && pytest tests/contrato/test_http_ara.py -q
22 passed, 2 warnings in 13.31s

$ scripts/check-raiz-do-agregado.sh
✓ operação só pela raiz: 8 guardas, 6 raízes, 192 arquivos varridos.
```

### 5.3 · Os demais achados

| # | Achado | Severidade | Destino |
|---|---|---|---|
| **A-02** | A linha 5 e a linha 6 da DoD citam arquivos de teste que **não existem com aquele nome** (`test_status_validacao.py`, `test_conector_e.py`): os casos vivem em `apps/api/tests/dominio/test_ara.py`. O critério é cumprido; a **verificação executável escrita na spec** não roda como está | Baixa | 📝 registrado: a spec deve citar o arquivo real, ou o relatório declarar o ajuste — este declara (§2) |
| **A-03** | **A linha 10 está vermelha por duas razões independentes.** (i) O `contracts/acoes-catalogo.md` das 5 ações `toc.*` do M2 **nunca foi escrito** — e o portão de conformidade vê o mesmo buraco por outro ângulo (`ART:contracts=yes but no contracts.md`). (ii) A segunda metade do critério ("nenhuma rota de execução no serviço") foi **deliberadamente revogada** pelo ciclo 006, que fez as ações executarem pela FSM do servidor: hoje o catálogo tem `toc.sugerir_udes` e `toc.analisar_suficiencia` executáveis por proposta governada. A decisão é defensável; **a mudança de escopo não foi declarada na spec do 005**, e "sem escopo mudado em silêncio" é regra de casa | **Média** | ✗ **VERMELHO assumido**. Dono: gate humano — ratificar a revogação e escrever a declaração na spec, ou escrever o contrato que falta |
| **A-04** | A linha 11 pede `= 0` e devolve `3`; as três são a **denylist** de segredos do snapshot. O critério não distingue "cita o nome do segredo para bloqueá-lo" de "usa o segredo" | Baixa | 📝 registrado. É literalmente a mesma pendência P-03 do ciclo 008 e o achado A-05 do ciclo 004 — três ciclos tropeçando no mesmo critério mal escrito é sinal de que ele merece ser reescrito uma vez |
| **A-05** | **A circularidade da base autoral continua mitigada, não resolvida.** O conjunto de controle externo tem **9 enunciados**, e **4 das 11 características de UDE** continuam fora do alcance de qualquer função pura. A dívida foi herdada do §9 do ciclo 001 com destino "ciclo 005" | Média | 📝 **registrado e NÃO fechado**: fechar exige corpus de oficina real, o que esbarra no ADR 0006 (base sintética). Dono: gate humano, que decide se a v1 vive com a mitigação |

### 5.4 · Achados da avaliação heurística da jornada J-02 que são do M2

Transcritos de `docs/jornadas/002-primeiro-projeto-e-ara.md` (2026-09-06):

| # | Achado | Severidade | Destino |
|---|---|---|---|
| J-02/A-02 | Depois de "Reformular", a ficha continua mostrando o texto e o **veredito antigos** até ser fechada e reaberta — o veredito velho ao lado do texto novo | **Alta** | 📝 registrado — o domínio revalida no mesmo ato (correção de A-01); é a **tela** que não relê |
| J-02/A-03 | "Ajustar à tela" enquadra a árvore **abaixo da dobra** (2 762 px numa janela de 900 px): o canvas visível fica vazio com 16 nós no projeto | **Alta** | 📝 registrado |
| J-02/A-05 | O relatório estrutural lista os 16 elos não examinados por identificador universal, que não diz a ninguém qual elo é | Média | 📝 registrado |
| J-02/A-06 | O filtro por status filtra o painel e **não** o canvas; a assimetria não é anunciada | Baixa | 📝 registrado |
| J-02/A-07 | A leitura do elo concatena as frases sem tratar a pontuação | Baixa | 📝 registrado |

## 6 · TAIL:security — o passe, item a item

| Item | Como se verificou | Resultado |
|---|---|---|
| Nenhuma rota de execução de assistência no M2 sem gate | `pytest tests/federacao/test_casos_de_uso_da_federacao.py -k "intocado or nasce_proposta"` | ✓ `test_acao_mutadora_nasce_proposta_e_o_dominio_fica_intocado PASSED` — a ação nasce proposta, o domínio fica intocado até a decisão |
| Sem SDK, chave ou prompt de provedor no produto (ADR 0007) | grep sobre `apps/api/src/` e `apps/web/src/` | ✓ `3` ocorrências, as três a denylist do snapshot (§2, linha 11) |
| Nenhum critério decidível dependendo de prompt | grep `promptText\|system_prompt` | ✓ `0` |
| Parecer de IA não fecha status sozinho (RN-10) | `test_parecer_de_ia_sozinho_nunca_fecha_o_status` | ✓ dentro dos `6 passed` |
| Fronteira do agregado da ARA | `apps/api/tests/dominio/test_raiz_do_agregado.py` + `apps/api/tests/contrato/test_http_porta_dos_fundos.py` | ✓ dentro dos `33 passed`: a mutação genérica sobre projeto de ferramenta responde `409 AGGREGATE_ROOT_REQUIRED` |
| Isolamento por inquilino na ARA | `pytest tests/integracao/test_grafo_e_ara_no_postgres.py -q` (dentro da suíte verde) | ✓ |
| Dado real de pessoa no corpus e nas capturas (ADR 0006) | `scripts/check-vazamento.sh` | ✓ `0` achados sobre `579` arquivos e `3364` registros JSON — e o corpus de UDEs é **sintético e versionado** (`apps/api/tests/dominio/corpus_udes.json`) |

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

**O que é deste ciclo, e é a parte mais forte**: a validação formal tem uma mutação
*embutida na suíte*, e ela não é de portão — é de **corpus**. O
`apps/api/tests/dominio/test_corpus_udes.py` mede `marcadores lexicais cobertos: 63/63`:
remover um marcador do léxico **derruba** a suíte, porque todo marcador tem caso no corpus. É
a regra "ampliar a heurística exige ampliar o corpus" (RNF-08) virada função de aptidão. E o
`apps/api/tests/dominio/test_paridade_com_medir_base.py` fixa a divergência esperada num
conjunto literal (`DIVERGENCIA_ESPERADA = {"K-03"}`): fechar K-03 sem atualizar o conjunto
derruba o teste, e **abrir** um falso negativo novo também.

**O que não cobre**: mutação sobre os vereditos da FSM de status e sobre a análise
estrutural, que é o que o `TAIL:mutation` do `tasks.md` deste ciclo pede nominalmente.
Dívida **Dv-3**.

## 8 · TAIL:gate — NÃO marcado, e o que aguarda o Product Steward

1. **Decidir a linha 10** (A-03): ratificar que as ações do M2 passaram a executar pela FSM
   do ciclo 006 — e mandar declarar a mudança na spec do 005 —, ou exigir o
   `contracts/acoes-catalogo.md` que nunca foi escrito.
2. **Ratificar a ressalva da linha 11** (A-04) — e, de preferência, mandar reescrever o
   critério **uma vez** para os ciclos 005, 006, 007 e 008, que tropeçam no mesmo.
3. **Decidir o destino da circularidade** (A-05): a v1 vive com 9 enunciados de controle e 4
   características indecidíveis, ou o ADR 0006 é revisitado?
4. **Responder os cinco `[DÚVIDA]` do Clarify** que a abertura do ciclo listava.
5. **Aceitar as seis dívidas do §9.**
6. **Autorizar a promoção** (`docs/governance/como-fechar-um-ciclo.md`).

## 9 · Dívidas declaradas, com dono

| # | Dívida | Por quê | Dono |
|---|---|---|---|
| **Dv-1** | `ART:contracts=yes` sem `contracts/` no ciclo, e `ART:data-model` sem motivo | É defeito do `specs/005-arvore-da-realidade-atual/plan.md`; é o mesmo fato da linha 10 visto por outro portão | construtor do ciclo 005 |
| **Dv-2** | A declaração das 5 ações `toc.*` do M2 (T-03) nunca foi escrita | O catálogo executável existe e é fonte única; o **contrato legível** que a spec pedia, não | construtor do ciclo 005 ou o gate, se revogar o item |
| **Dv-3** | Mutação sobre a FSM de status e sobre a análise estrutural (T-15) | As 61 sabotagens cobrem portões; estas são sobre funções de domínio | construtor do ciclo 005 |
| **Dv-4** | Passe de segurança em contexto fresco por **terceiro** | Maestro II: quem executa não verifica | revisor de segurança em contexto fresco |
| **Dv-5** | RNF-05 (ciclo editar → reavaliar na ficha) não medido | É tempo de interface; exige o build real instrumentado | ciclo de interface / jornada |
| **Dv-6** | As duas medições de RNF do §4 são **ad-hoc**, não script versionado | O número é real; a reprodutibilidade por terceiro não está garantida | construtor do ciclo 005 — vira `scripts/` ou teste marcado |
| **Dv-7** | A circularidade da base autoral (A-05) continua mitigada | Herdada do §9 do ciclo 001; fechar esbarra no ADR 0006 | gate humano |

## 10 · Cauda

- **TAIL:review** — revisão independente em contexto fresco, com **5 achados numerados**
  (A-01 a A-05, §5.2 e §5.3) e **5 achados** da avaliação heurística datada da jornada J-02
  (§5.4). O achado central, **A-01**, é a ARA alcançável pelas rotas genéricas do M1 em
  **quatro** invariantes distintas — elo sem exame (RF-22), UDE órfão (RF-05), conector E com
  aresta fantasma (RN-11) e UDE reescrito sem revalidar (RF-10) —, corrigido pela raiz e
  verificado hoje com `22 passed, 2 warnings in 13.31s` no contrato HTTP da ARA e
  `✓ operação só pela raiz: 8 guardas, 6 raízes, 192 arquivos varridos.` Um achado virou
  vermelho assumido na DoD (A-03) em vez de ser maquiado, e a dívida de circularidade herdada
  do ciclo 001 (A-05) está **declarada em aberto**, não fechada por conveniência.
- **TAIL:security** — passe sobre 7 itens, **7 sem furo** (§6): a ação mutadora nasce
  proposta e o domínio fica intocado até a decisão; `0` ocorrência de prompt no domínio; `3`
  ocorrências de segredo que são a denylist; parecer de IA que nunca fecha status sozinho;
  a fronteira do agregado respondendo `409 AGGREGATE_ROOT_REQUIRED`; isolamento por inquilino
  no banco real; e `scripts/check-vazamento.sh` sobre `579` arquivos e `3364` registros JSON
  sem um achado, com o corpus de UDEs sintético e versionado. **Alcance declarado**: passe,
  não revisão independente por terceiro (Dv-4).
- **TAIL:mutation** — `scripts/tests/run-sabotagem.sh` saiu **0**: `portões cobertos: 10 ·
  bases válidas aceitas: 10/10` e `sabotagens declaradas: 61 · reprovadas pelo motivo certo:
  61/61`. Deste ciclo, a mutação que mais vale é a **de corpus**: `marcadores lexicais
  cobertos: 63/63` derruba a suíte se um marcador sumir do léxico, e
  `DIVERGENCIA_ESPERADA = {"K-03"}` derruba se um falso negativo novo aparecer. O que falta
  está em §7 e é a dívida Dv-3.
- **TAIL:gate** — **NÃO marcado, de propósito.** A DoD fechou **10 verdes, 2 com ressalva e
  2 vermelhas**. Os seis itens que aguardam assinatura estão em §8. Quem executou não aprova
  o que executou (Maestro II).

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
| `scripts/check-conformance.sh 005` | ver o bloco de conformidade acima | `1` |

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

**Executado e medido; NÃO fechado.** A Árvore da Realidade Atual existe como **regra de
domínio pura**: os critérios de UDE que quatro gerações da linhagem carregaram apenas como
texto de prompt hoje decidem, offline, com o trecho apontado — e o único falso negativo que um
conjunto de controle externo achou nelas **está fechado pelo teste que nasceu vermelho**. A
análise estrutural que a linhagem pedia a um modelo é função pura de 20 ms sobre 200 nós. O
que está vermelho — a declaração das ações `toc.*` e a mudança de escopo não declarada — está
vermelho aqui, com dono, e não escondido. O gate humano é o próximo passo.
