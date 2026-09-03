# Spec 009 — Focalização (M6 — Focalização)

> Siglas: TOC — Teoria das Restrições · ARA — Árvore da Realidade Atual · UDE — Efeito
> Indesejável (*Undesirable Effect*) · NC — Nuvem de Conflito · ARF — Árvore da
> Realidade Futura · APR — Árvore de Pré-Requisitos · AT — Árvore de Transição · OI —
> Objetivo Intermediário · S&T — Estratégia & Táticas (*Strategy & Tactics*) · APH —
> Aplicação ↔ Harness · ADR — Architecture Decision Record (Registro de Decisão
> Arquitetural) · RF/RI/RNF/RN/INT — requisito funcional / de interface / não funcional
> / regra de negócio / integração · US — User Story (história de usuário) · DDD —
> Domain-Driven Design (Design Orientado a Domínio) · TDD — Test-Driven Development
> (desenvolvimento guiado por teste) · DoD — Definition of Done (Definição de Pronto) ·
> DBR — tambor-pulmão-corda (*Drum-Buffer-Rope*) · IA — inteligência artificial · FSM —
> máquina de estados finitos · OTel — OpenTelemetry · JSON — JavaScript Object Notation
> · i18n — internacionalização · UI — interface de usuário · CI — integração contínua

- **Status**: Rascunho (aprovação: gate humano do ciclo 001)
- **Raia**: plena
- **Data**: 2026-09-03
- **Origem**: [`../../docs/produto/modulos.md`](../../docs/produto/modulos.md) (M6) ·
  [`../../docs/roadmap.md`](../../docs/roadmap.md) (ciclo 009) ·
  [`../../docs/produto/rounds.md`](../../docs/produto/rounds.md) (round 009)

## O quê e por quê

O M6 é o módulo que dá à aplicação o nome da teoria. Os **cinco passos de focalização**
— identificar a restrição → explorar a restrição → subordinar tudo o mais → elevar a
restrição → recomeçar sem deixar a inércia virar a restrição — são o algoritmo central
da TOC, e as árvores lógicas dos módulos M2–M5 são as ferramentas que cada passo usa.
Sem os cinco passos, seis ferramentas são seis editores desconexos; com eles, viram uma
jornada com começo, direção e critério de recomeço.

Este módulo é **inteiramente novo**: em quatro gerações de linhagem TOC-Builder, a
palavra focalização nunca apareceu — o grep sobre as quatro gerações devolve **0
ocorrências** (F-01, saída colada; o defeito está catalogado como D-09 na
[`../../docs/produto/visao.md`](../../docs/produto/visao.md) §6, e a decisão de
incluí-lo na v1 é o ADR 0005, F-02). Não há modelo de dados a herdar nem defeito de
implementação a corrigir: as fontes deste módulo são a decisão de escopo, o round 009 e
o método da TOC — por isso quase tudo abaixo é 🟡 PLANEJADO, e os 🟢 apontam para as
decisões registradas deste corpus, não para código de linhagem.

O que o ciclo entrega: a **restrição como entidade de primeira classe** — registrada por
análise, com o passo atual explícito (E6.1) — e a **jornada guiada** que conduz cada
passo à ferramenta certa com o estado herdado do passo anterior: identificar usa a ARA
(M2), conflitos de exploração e subordinação viram NC (M3), a elevação planeja com
APR/AT (M4), e recomeçar abre um novo ciclo de focalização apontando a nova restrição
**sem apagar** o anterior (E6.2). Métricas de desempenho da restrição, DBR e
contabilidade de ganho ficam fora, por decisão com medição colada (ADR 0005).

## O que entra como dado

- **Escopo v1** (ADR 0005,
  [`../../docs/adr/0005-escopo-do-dominio-v1.md`](../../docs/adr/0005-escopo-do-dominio-v1.md)):
  a focalização entra como módulo novo; DBR, gestão de pulmões e contabilidade de ganho
  ficam fora — o grep da linhagem com **0 ocorrências** está colado no próprio ADR. O
  roadmap fixa como pré-condição do ciclo 009 que este ADR esteja **inalterado** (F-06).
- **Núcleo M1** ([`../004-nucleo-de-diagramas/spec.md`](../004-nucleo-de-diagramas/spec.md)):
  a análise de focalização é um tipo de projeto sobre o núcleo — listagem, isolamento
  por inquilino, exclusão suave, exportação/importação — sem canvas de grafo livre: a
  sua superfície é jornada e linha do tempo, não diagrama.
- **Ferramentas construídas** — ARA
  ([`../005-arvore-da-realidade-atual/spec.md`](../005-arvore-da-realidade-atual/spec.md)),
  NC ([`../007-nuvem-de-conflito/spec.md`](../007-nuvem-de-conflito/spec.md)) e
  ARF/APR/AT
  ([`../008-arvores-de-futuro-e-implementacao/spec.md`](../008-arvores-de-futuro-e-implementacao/spec.md)):
  a jornada **referencia** projetos dessas ferramentas, nunca os reimplementa. Por isso
  o ciclo 009 vem depois do 008 — a jornada aponta para ferramentas que precisam
  existir (F-06).
- **Escopo do round 009** ([`../../docs/produto/rounds.md`](../../docs/produto/rounds.md)):
  E6.1 e E6.2 completos; **sai primeiro** a sugestão assistida de qual ferramenta usar
  no passo (fica a jornada guiada estática); **nunca sai** o registro da restrição — "é
  a entidade que dá nome à teoria, e o produto sem ela é um editor de diagramas" (F-04).
- **IA somente pela fundação** (ADR 0007,
  [`../../docs/adr/0007-ia-somente-pela-fundacao.md`](../../docs/adr/0007-ia-somente-pela-fundacao.md))
  e a FSM de proposta do ciclo 006
  ([`../006-acoes-governadas-e-snapshot/spec.md`](../006-acoes-governadas-e-snapshot/spec.md)):
  a única assistência deste módulo (sugestão de restrição a partir da ARA) nasce
  `action_proposal` — e é exatamente o item que o corte de apetite solta primeiro.
- **Base sintética** (ADR 0006,
  [`../../docs/adr/0006-base-sintetica-desde-o-dia-1.md`](../../docs/adr/0006-base-sintetica-desde-o-dia-1.md)):
  a análise de demonstração é a da "Instituição Horizonte", com personas fictícias.

## Épicos, features e user stories

### E6.1 — Registro da restrição e do passo atual

**F6.1.1 — Análise de focalização** — o contêiner da jornada: um sistema analisado
(nome + descrição), ciclos de focalização, herança completa do ciclo de vida do M1.

- US-01 — Como Facilitadora TOC, quero criar uma análise de focalização para um sistema
  analisado, para que a jornada dos cinco passos tenha um lugar com dono e histórico.
  - Dado o tenant da Instituição Horizonte, Quando crio a análise "Fluxo de matrículas"
    com a descrição do sistema, Então ela nasce com o primeiro ciclo de focalização
    aberto no passo **identificar**, sem restrição registrada ainda.
- US-02 — Como Gestora, quero listar, arquivar e restaurar análises como qualquer
  projeto, para governar o acervo num lugar só.
  - Dado uma análise arquivada, Quando a restauro, Então ela volta com ciclos, passos,
    restrições e vínculos intactos — a herança do M1 sem exceção.

**F6.1.2 — Registro da restrição** — a restrição como entidade de primeira classe:
descrição, tipo e origem — declarada à mão ou vinculada à causa raiz de uma ARA.

- US-03 — Como Facilitadora TOC, quero registrar a restrição identificada com tipo e
  justificativa, para que a análise inteira aponte para um alvo explícito.
  - Dado o ciclo aberto no passo identificar, Quando registro a restrição "capacidade
    da secretaria acadêmica" com tipo `física` e justificativa, Então ela vira a
    restrição vigente do ciclo e o passo identificar pode ser concluído.
- US-04 — Como Participante, quero vincular a restrição à causa raiz da ARA que a
  revelou, para que a conclusão carregue a evidência que a sustenta.
  - Dado uma ARA da mesma análise com causa raiz marcada, Quando registro a restrição
    a partir dela, Então a restrição nasce com a referência ao nó de origem — e abrir a
    referência navega à ARA.

**F6.1.3 — Passo atual e avanço** — o ciclo sabe em que passo está; avançar é ato
explícito com decisão registrada, nunca efeito colateral.

- US-05 — Como Facilitadora TOC, quero concluir o passo atual registrando a decisão que
  o encerra, para que o avanço da jornada seja um fato com autor e data.
  - Dado o passo explorar em andamento, Quando o concluo com a decisão "priorizar
    matrículas com documentação completa", Então o ciclo avança para subordinar e o
    evento guarda autor, data e a decisão.
- US-06 — Como Gestora, quero ver o passo atual de cada análise na listagem, para
  acompanhar várias jornadas sem abrir uma a uma.
  - Dado três análises em passos diferentes, Quando abro a listagem, Então cada linha
    mostra o passo atual e a restrição vigente do ciclo aberto.

### E6.2 — Jornada guiada pelos cinco passos

**F6.2.1 — Mapa da jornada** — os cinco passos como superfície de navegação: estado de
cada um, o produto que cada um herda do anterior, a ferramenta que cada um usa.

- US-07 — Como Participante, quero ver os cinco passos com o estado de cada um, para
  saber onde a análise está e o que falta.
  - Dado um ciclo com identificar concluído e explorar em andamento, Quando abro o mapa
    da jornada, Então vejo os cinco passos em sequência — concluído, em andamento,
    pendentes — cada um com sua decisão registrada ou sua pendência.
- US-08 — Como Facilitadora TOC, quero que cada passo me apresente o produto do passo
  anterior, para nunca decidir no vácuo.
  - Dado o passo subordinar aberto, Quando o abro, Então vejo a restrição registrada
    (identificar) e as decisões de exploração (explorar) herdadas no topo do painel.

**F6.2.2 — Cada passo aponta a ferramenta certa** — os vínculos com M2, M3 e M4 como
dado de primeira classe: identificar usa ARA; explorar e subordinar registram decisões
e transformam conflitos em NC; elevar planeja com APR/AT.

- US-09 — Como Facilitadora TOC, quero criar ou vincular uma ARA a partir do passo
  identificar, para que a busca da restrição use a ferramenta feita para isso.
  - Dado o passo identificar aberto, Quando escolho "analisar com ARA", Então crio (ou
    vinculo) um projeto ARA da mesma análise e o vínculo aparece no passo — com o
    estado do projeto ARA visível de lá.
- US-10 — Como Participante, quero transformar um conflito de subordinação em NC, para
  que a resistência ao "subordinar tudo o mais" seja tratada com método, não vencida no
  grito.
  - Dado o passo subordinar com a regra "toda turma abre só com a secretaria pronta"
    contestada, Quando escolho "modelar o conflito", Então nasce um projeto NC vinculado
    ao passo, com o vínculo navegável nos dois sentidos.
- US-11 — Como Facilitadora TOC, quero planejar a elevação com APR e AT, para que
  "elevar a restrição" saia como plano sequenciado de obstáculos e OIs, não como desejo.
  - Dado o passo elevar aberto, Quando vinculo a APR "ampliar a secretaria" (e, dela, a
    AT), Então o passo lista os vínculos e mostra o andamento dos planos vinculados.

**F6.2.3 — Recomeçar sem inércia** — o quinto passo fecha o ciclo, abre o próximo
apontando a nova restrição e obriga a revisão explícita do que o ciclo anterior
subordinou — histórico é apêndice, nunca sobrescrita.

- US-12 — Como Facilitadora TOC, quero recomeçar a jornada quando a restrição for
  quebrada, para que a análise siga a nova restrição sem perder a memória da anterior.
  - Dado o passo elevar concluído com a restrição quebrada, Quando recomeço, Então o
    ciclo atual fecha (somente leitura), um novo ciclo abre no passo identificar, e a
    linha do tempo mostra os dois — nada foi apagado.
- US-13 — Como Participante, quero ser confrontado com as decisões do ciclo anterior ao
  recomeçar, para que nenhuma regra antiga sobreviva por inércia.
  - Dado o recomeço com 3 decisões de subordinação no ciclo anterior, Quando o novo
    ciclo abre, Então cada decisão herdada exige veredito explícito — `mantida` ou
    `revogada`, com justificativa — antes de o passo subordinar do novo ciclo poder
    concluir.

## Entidades e modelo de domínio

DDD puro — domínio sem framework, sem rede, sem relógio (P3). O M6 **estende** o modelo
do M1 por composição (o documento consolidado nasce na abertura do ciclo, T-02). A
diferença estrutural para os módulos de ferramenta: a análise de focalização **não é
diagrama** — é jornada com estado, e as árvores entram por referência.

- **AnaliseDeFocalizacao** (agregado): o Projeto do M1 com `TipoDeFerramenta =
  focalizacao`. Carrega o **SistemaAnalisado** (nome + descrição do sistema cuja meta a
  análise serve) e a lista ordenada de **CiclosDeFocalizacao** — no máximo um aberto
  (RN-02).
- **CicloDeFocalizacao** (entidade do agregado): uma volta completa dos cinco passos.
  Estado: `aberto` | `fechado`. Carrega a **Restricao** vigente (no máximo uma — RN-03),
  os cinco **PassosDeFocalizacao** e as **DecisoesHerdadas** do ciclo anterior
  (RN-05). Fechar um ciclo o torna somente leitura — histórico é apêndice (RN-04).
- **Restricao** (entidade): descrição + `tipo` (`fisica` | `politica` | `de_mercado`) +
  justificativa + **ReferenciaDeOrigem** opcional (o nó de causa raiz da ARA que a
  revelou — INT-02) + autoria por evento. É a entidade que dá nome à teoria; o round
  009 a marca "nunca sai" (F-04).
- **PassoDeFocalizacao** (entidade do ciclo): `tipo` fixo e ordenado — `identificar` |
  `explorar` | `subordinar` | `elevar` | `recomecar` (RN-01) — + estado (`pendente` |
  `em_andamento` | `concluido`) + **DecisaoDePasso** (texto que encerra o passo, com
  autor e data) + lista de **VinculosDeFerramenta** + notas.
- **VinculoDeFerramenta** (objeto de valor): referência tipada a um projeto de outra
  ferramenta — `ara` | `nc` | `arf` | `apr` | `at` — com o papel do vínculo no passo.
  Combinações canônicas por passo (RN-06): identificar→ARA; explorar→NC/ARF;
  subordinar→NC; elevar→APR/AT. Fora do canônico exige justificativa — aviso, não
  bloqueio. O vínculo é referência, nunca cópia (INT-02..INT-04).
- **DecisaoHerdada** (objeto de valor do ciclo): uma decisão de subordinação ou de
  exploração do ciclo anterior + veredito (`pendente` | `mantida` | `revogada`) +
  justificativa. É o mecanismo anti-inércia (RN-05): o quinto passo do método existe
  para ela.
- **JornadaDaAnalise** (serviço de domínio, função pura): dado o agregado, computa o
  mapa da jornada — passo atual, pendências por passo (restrição ausente, decisão
  ausente, herança sem veredito), progresso do ciclo. Não muta nada; sem rede e sem
  modelo.
- **Eventos de domínio** (somente-acréscimo, além dos do M1): `AnaliseCriada`,
  `CicloAberto`, `RestricaoRegistrada`, `RestricaoEditada`, `PassoIniciado`,
  `PassoConcluido`, `PassoReaberto`, `VinculoCriado`, `VinculoRemovido`,
  `DecisaoHerdadaJulgada`, `CicloFechado`.
- **Fora do domínio**: os agregados das ferramentas vinculadas (M2–M5 — o vínculo
  carrega identificador e leitura, nunca o dado); a FSM de `action_proposal` (uma só e
  do servidor — ciclo 006); métricas de desempenho da restrição (fora da v1 — ADR
  0005).

## Requisitos funcionais

### Análise de focalização

RF-01: O SISTEMA DEVE permitir criar análise de focalização — sistema analisado (nome,
descrição) — herdando do M1 listagem, isolamento por inquilino, exclusão suave,
restauração e exportação/importação sem reimplementação. 🟡

RF-02: QUANDO uma análise for criada, O SISTEMA DEVE abrir o primeiro ciclo de
focalização no passo `identificar`, com os cinco passos instanciados em sequência
canônica — não existe ciclo sem os cinco passos (RN-01). 🟡

RF-03: O SISTEMA DEVE apresentar na listagem de análises o passo atual e a restrição
vigente do ciclo aberto de cada uma. 🟡

RF-04: QUANDO uma análise for excluída, O SISTEMA DEVE aplicar a exclusão suave do M1
arquivando ciclos, passos, restrições e vínculos juntos; a restauração devolve tudo. 🟡

### Registro da restrição

RF-05: O SISTEMA DEVE permitir registrar a restrição do ciclo aberto — descrição, tipo
(`fisica` | `politica` | `de_mercado`), justificativa — com autoria por evento; no
máximo uma restrição vigente por ciclo (RN-03). [F-04] 🟡

RF-06: O SISTEMA DEVE permitir registrar a restrição a partir de um nó de causa raiz de
uma ARA vinculada, preenchendo a referência de origem — e DEVE permitir registrá-la
manualmente, sem ARA nenhuma: a ferramenta ajuda, nunca condiciona (INT-02). 🟡

RF-07: O SISTEMA DEVE permitir editar a descrição e a justificativa da restrição do
ciclo aberto com evento; trocar a restrição de alvo não é edição — é recomeço (RN-03,
RF-15). 🟡

RF-08: O SISTEMA DEVE recusar, no domínio, a conclusão do passo `identificar` sem
restrição registrada — os demais passos concluem com decisão registrada (RF-09). 🟡

### Passo atual e avanço

RF-09: O SISTEMA DEVE permitir concluir o passo em andamento registrando a decisão que
o encerra (texto, autor, data por evento); a conclusão move o ciclo ao passo seguinte
na ordem canônica — avanço é ato explícito, nunca efeito colateral (RN-01). 🟡

RF-10: O SISTEMA DEVE permitir reabrir o passo imediatamente anterior do ciclo aberto
mediante justificativa, com evento `PassoReaberto` — sem apagar a decisão que o havia
concluído (o histórico de decisões é somente-acréscimo). 🟡

RF-11: O SISTEMA DEVE manter notas por passo — texto livre acumulável, com autoria —
distintas da decisão de conclusão. 🟡

### Jornada guiada e vínculos de ferramenta

RF-12: O SISTEMA DEVE apresentar o mapa da jornada do ciclo aberto: os cinco passos em
sequência com estado, decisão registrada ou pendência de cada um, e os vínculos de
ferramenta de cada passo — computado por função pura de domínio (JornadaDaAnalise). 🟡

RF-13: QUANDO um passo for aberto, O SISTEMA DEVE apresentar o produto herdado dos
passos anteriores do mesmo ciclo — a restrição (de identificar) e as decisões já
registradas — no topo do painel do passo (F-04: "estado herdado do anterior"). 🟡

RF-14: O SISTEMA DEVE permitir criar ou vincular, a partir de um passo, um projeto de
outra ferramenta do mesmo tenant — as combinações canônicas por passo (RN-06):
`identificar`→ARA, `explorar`→NC ou ARF, `subordinar`→NC, `elevar`→APR ou AT; vínculo
fora do canônico exige justificativa e fica com aviso, nunca bloqueado. O vínculo é
navegável nos dois sentidos e mostra o estado do projeto vinculado. 🟡

### Recomeçar sem inércia

RF-15: O SISTEMA DEVE permitir recomeçar a partir do passo `recomecar`: o ciclo atual
fecha (somente leitura), um novo ciclo abre no passo `identificar` sem restrição — e
nada do ciclo anterior é apagado ou sobrescrito (RN-04; o portão executável do roadmap,
F-06). 🟡

RF-16: QUANDO um novo ciclo abrir por recomeço, O SISTEMA DEVE herdar as decisões de
exploração e subordinação do ciclo anterior como DecisoesHerdadas com veredito
`pendente`; o passo `subordinar` do novo ciclo não conclui enquanto houver veredito
pendente — cada uma exige `mantida` ou `revogada` com justificativa (RN-05). 🟡

RF-17: O SISTEMA DEVE apresentar a linha do tempo da análise: os ciclos em ordem, cada
um com restrição, datas de abertura/fechamento e decisões — o ciclo fechado abre em
modo somente leitura. 🟡

RF-18: O SISTEMA DEVE exportar e importar a análise completa pelo E1.4 do M1 — ciclos,
passos, restrições, decisões, vínculos (como referências) e vereditos de herança — sem
perda em ida e volta; vínculo cujo projeto não exista no destino importa como referência
pendente declarada, nunca falha silenciosa. 🟡

### Assistência via catálogo (corte de apetite: sai primeiro)

RF-19: O SISTEMA DEVE expor `toc.suggest_constraint` no catálogo governado: entrada é o
estado da ARA vinculada ao passo identificar; saída são candidatas a restrição (nó +
racional), cada uma nascendo `action_proposal` — aceitar registra a restrição com
referência de origem; recusar deixa a análise intacta (ADR 0007; FSM do ciclo 006).
[F-05] 🟡

RF-20: O SISTEMA DEVE funcionar por inteiro — E6.1 e E6.2 — com o catálogo ausente ou
desligado: a jornada guiada é estática e completa por construção; a sugestão é
aceleradora, nunca dependência (o round 009 a solta primeiro no corte de apetite,
F-04). 🟡

RF-21: QUANDO a capability de escrita não estiver presente na introspecção, O SISTEMA
DEVE omitir do catálogo a ação mutadora deste módulo, mantendo o restante da jornada
funcional. 🟡

## Requisitos de interface

RI-01: O mapa da jornada apresenta os cinco passos como trilha sequencial nomeada —
identificar, explorar, subordinar, elevar, recomeçar — com estado distinguível por
forma e rótulo, nunca só por cor; o passo atual é o foco visual da tela. 🟡

RI-02: O painel do passo tem três camadas na mesma superfície: o herdado (topo,
somente leitura), o trabalho do passo (notas, vínculos), e a decisão de conclusão
(rodapé, ação explícita). 🟡

RI-03: O vínculo de ferramenta aparece como cartão com tipo, nome do projeto, estado e
navegação direta; criar vínculo oferece primeiro as combinações canônicas do passo
(RN-06), com o caminho não-canônico visível mas de segundo nível. 🟡

RI-04: A linha do tempo dos ciclos (RF-17) apresenta os ciclos em ordem cronológica com
restrição e desfecho; ciclo fechado é visualmente distinto e abre somente leitura. 🟡

RI-05: O julgamento das decisões herdadas (RF-16) apresenta cada decisão do ciclo
anterior com os dois vereditos de mesmo peso visual — `mantida` e `revogada` — e
justificativa obrigatória; o contador de pendências é visível do mapa da jornada. 🟡

RI-06: A proposta de `toc.suggest_constraint` (RF-19) apresenta as candidatas com o nó
de origem e o racional em pré-visualização; aceitar e recusar têm o mesmo peso visual;
a bandeja de propostas é a do ciclo 006, nunca uma própria. 🟡

RI-07: A listagem de análises (RF-03) mostra passo atual e restrição vigente como
colunas de primeira classe, ordenáveis. 🟡

RI-08: Toda superfície do módulo respeita tema do hospedeiro com fallback, modo
só-conteúdo e operação por teclado, herdados dos ciclos 002/003; textos por i18n pt/en,
inclusive os nomes canônicos dos cinco passos e dos tipos de restrição. 🟡

## Requisitos não funcionais

RNF-01: A ordem canônica dos passos, a unicidade de restrição e ciclo aberto, a
imutabilidade de ciclo fechado e o bloqueio por herança pendente são domínio puro
testável sem rede, sem banco e sem modelo — a suíte de domínio roda offline por
construção (P3, P4). 🟡

RNF-02: A fronteira hexagonal é verificada por `import-linter`: o pacote de domínio do
M6 não importa framework, HTTP, banco nem cliente de IA — o build falha na violação. 🟡

RNF-03: Toda mutação do módulo emite traço OTel correlacionado e log estruturado;
mutações originadas de proposta aceita carregam o identificador da proposta (P5). 🟡

RNF-04: O vínculo de ferramenta valida existência e tenant do projeto referenciado **no
servidor** ao ser criado; vínculo cujo destino foi depois arquivado degrada para
"referência a projeto arquivado" legível — nunca erro opaco, nunca dado órfão
silencioso. 🟡

RNF-05: Abrir o mapa da jornada de uma análise com 5 ciclos e 30 vínculos renderiza em
menos de 1 segundo no percentil 95, medido na jornada viva. 🟡

RNF-06: A fixture de demonstração e a jornada usam exclusivamente a análise sintética
da "Instituição Horizonte" — grep negativo de nome real de pessoa no CI (ADR 0006). 🟡

RNF-07: Nenhum prompt, chave ou cliente de provedor no repositório do produto — grep de
CI herdado dos ciclos anteriores (P7, ADR 0007). 🟡

RNF-08: Textos dos passos, tipos de restrição, vereditos e avisos saem do mecanismo de
i18n com chave estável ligada à regra (RN-NN) — rastreabilidade spec ↔ código ↔ tela. 🟡

## Regras de negócio

RN-01: Os cinco passos são fixos, nomeados e ordenados — `identificar` → `explorar` →
`subordinar` → `elevar` → `recomecar` — e todo ciclo os instancia todos, na criação;
não se cria, exclui nem reordena passo. A conclusão avança um passo por vez. [F-02,
F-04] 🟡

RN-02: Uma análise tem no máximo **um ciclo aberto**; abrir ciclo novo exige fechar o
atual pelo recomeço (RF-15) — não existe "fechar sem recomeçar" nem dois ciclos
correndo. 🟡

RN-03: Um ciclo tem no máximo **uma restrição vigente**. Mudar o alvo da análise não é
editar a restrição — é evidência de que a restrição anterior quebrou ou foi mal
identificada, e o caminho é o recomeço, que preserva a anterior no ciclo fechado. 🟡

RN-04: **Histórico é apêndice, nunca sobrescrita**: ciclo fechado é somente leitura no
domínio; decisões de passo não se apagam (reabrir registra novo evento, RF-10); a
linha do tempo cresce, nunca encolhe. É o portão executável do roadmap: "'recomeçar'
reabre sem apagar histórico" (F-06). 🟡

RN-05: **A inércia não pode virar a restrição**: no recomeço, toda decisão de
exploração e subordinação do ciclo anterior herda com veredito `pendente`, e o passo
`subordinar` do novo ciclo não conclui com pendência — manter é decisão tão explícita
quanto revogar, com justificativa (RF-16). [F-04] 🟡

RN-06: As combinações canônicas passo × ferramenta são: `identificar`→ARA;
`explorar`→NC, ARF; `subordinar`→NC; `elevar`→APR, AT. Fora delas o vínculo exige
justificativa e carrega aviso — o método educa, o dado obedece ao grupo (o mesmo
desenho de aviso não bloqueante dos módulos M2/M3). 🟡

RN-07: O passo `recomecar` não tem decisão de conclusão própria: o seu ato é o recomeço
(RF-15) ou o encerramento declarado da análise (a restrição não limita mais e não há
nova — a análise arquiva-se pelo M1). 🟡

## Integrações

INT-01: O M6 consome do M1 (ciclo 004) projeto, tenant/usuário, exclusão suave,
exportação/importação e listagem; consome da junta 003 identidade
(`POST /auth/introspect`), isolamento por inquilino e OTel. Nada disso é
reimplementado. 🟡

INT-02: **Vínculo com o M2 (ARA)**: o passo `identificar` cria/vincula projetos ARA; a
restrição pode nascer de um nó de causa raiz com referência de origem (RF-06). A ARA
não conhece o M6 — a referência vive na análise, e a navegação de volta resolve por
consulta, não por acoplamento no agregado da ARA. 🟡

INT-03: **Vínculo com o M3 (NC)**: os passos `explorar` e `subordinar` criam/vinculam
projetos NC para os conflitos que emergem (RF-14) — reusando a criação de NC do ciclo
007 tal como está; nenhum campo novo no M3. 🟡

INT-04: **Vínculo com o M4 (ARF/APR/AT)**: o passo `explorar` pode vincular ARF; o
passo `elevar` cria/vincula APR e AT (RF-14), mostrando o andamento dos planos
(obstáculos → OIs) do jeito que o M4 os expõe. 🟡

INT-05: `toc.suggest_constraint` — catálogo `toc.*`, mutadora (registra restrição);
entrada: identificador da ARA vinculada; saída: candidatas a restrição (nó + racional),
uma `action_proposal` por candidata na FSM do ciclo 006 (RF-19); capability ausente a
omite (RF-21). 🟡

INT-06: Telas deste módulo entram no registro de telas do E7.5 com identificador
estável (`toc.foco_jornada`, `toc.foco_passo`, `toc.foco_linha_do_tempo`), no formato
do ciclo 006; descrição do sistema, notas e decisões marcam `ai_visible` campo a campo
para o snapshot sanitizado — texto de usuário é sempre camada não-confiável (item 7 da
constituição). 🟡

## Telas e fluxos

### 6.1 Mapa da jornada — Job: saber onde a análise está e o que falta · Campos: trilha
dos cinco passos com estado, restrição vigente, pendências (inclusive vereditos de
herança), vínculos por passo · Ações: abrir passo, registrar restrição, recomeçar,
abrir linha do tempo.

### 6.2 Painel do passo — Job: trabalhar um passo com o contexto herdado à vista ·
Campos: herdado (restrição + decisões anteriores), notas, vínculos de ferramenta,
decisão de conclusão · Ações: anotar, criar/vincular ferramenta (canônicas primeiro),
concluir com decisão, reabrir anterior.

### 6.3 Julgamento de herança — Job: impedir que a inércia atravesse o recomeço ·
Campos: decisões do ciclo anterior com origem e passo, veredito, justificativa ·
Ações: manter, revogar — cada uma com justificativa; concluir quando zerar pendência.

### 6.4 Linha do tempo — Job: contar a história da análise · Campos: ciclos em ordem
com restrição, datas e desfecho; ciclo fechado somente leitura · Ações: abrir ciclo
fechado, comparar restrições entre ciclos.

## Entregáveis

- Domínio Python puro do M6: agregado AnaliseDeFocalizacao, CicloDeFocalizacao com os
  cinco passos fixos, Restricao, VinculoDeFerramenta, DecisaoHerdada, JornadaDaAnalise
  — testes de domínio **sem rede e sem modelo** nascidos antes do código (P4), sobre
  fixture sintética da "Instituição Horizonte".
- Declaração da ação `toc.suggest_constraint` no formato do catálogo do ciclo 006
  (`contracts/`), com schema de entrada/saída.
- Casos de uso + adaptadores REST; validação de vínculo no servidor; migrações Alembic
  com downgrade (análise, ciclo, passo, restrição, vínculo, herança).
- Interface React: mapa da jornada, painel do passo, julgamento de herança, linha do
  tempo — sobre o `ux-design.md` do ciclo 002 (complementado neste ciclo se as telas de
  jornada não tiverem sido desenhadas lá — ver Clarify).
- Jornada viva (P6): a análise sintética da Instituição Horizonte atravessando
  identificar → explorar → subordinar → elevar → recomeçar — com vínculo de ARA, NC e
  APR reais e o julgamento de herança no recomeço — captura por passo gerada por script
  versionado do build real e avaliação heurística datada (o portão de jornada do
  roadmap, F-06).
- Entradas de CHANGELOG; ADR novo se decisão material surgir (candidata: taxonomia de
  tipos de restrição — ver Clarify).

## Critérios de aceite (DoD)

| # | Critério | Verificação executável |
|---|---|---|
| 1 | Domínio do M6 puro, offline | `pytest tests/domain/test_focalizacao.py -p no:cacheprovider` verde com rede desabilitada + `lint-imports` código 0 |
| 2 | Cinco passos fixos e ordenados (RN-01) | `pytest tests/domain/test_focalizacao.py -k "ordem_canonica" -v` — criar/excluir/reordenar passo recusado; avanço um a um |
| 3 | Teste percorre os cinco passos com estado herdado (portão do roadmap) | `pytest tests/domain/test_jornada_completa.py -v` — identificar→…→recomeçar numa análise sintética; cada passo lê o produto do anterior |
| 4 | Recomeçar reabre sem apagar histórico (RN-04, portão do roadmap) | `pytest tests/domain/test_jornada_completa.py -k recomeco -v` — ciclo anterior fechado e íntegro byte a byte; novo ciclo aberto em identificar |
| 5 | Inércia bloqueada (RN-05) | `pytest tests/domain/test_heranca.py -v` — subordinar do novo ciclo não conclui com veredito pendente; manter e revogar exigem justificativa |
| 6 | Uma restrição vigente, um ciclo aberto (RN-02, RN-03) | `pytest tests/domain/test_focalizacao.py -k "unicidade" -v` |
| 7 | Vínculo canônico e não-canônico (RN-06) | `pytest tests/domain/test_vinculos.py -v` — canônico direto; fora do canônico exige justificativa e marca aviso |
| 8 | Vínculo validado no servidor (RNF-04) | `pytest tests/application/test_vinculos_borda.py -v` — projeto inexistente ou de outro tenant recusado; arquivado degrada legível |
| 9 | Sugestão de restrição nasce proposta; recusar deixa intacto (RF-19) | `pytest tests/application/test_suggest_constraint.py -k recusa -v` — estado serializado idêntico antes/depois da recusa |
| 10 | Capability ausente esconde a mutadora (RF-21) | `pytest tests/integration/test_catalogo_m6.py -k capability -v` |
| 11 | Exportação sem perda (RF-18) | `pytest tests/application/test_export_focalizacao.py -k "ida_e_volta"` — export → import → igualdade estrutural; vínculo sem destino vira pendência declarada |
| 12 | Toda mutação nova com traço | `pytest tests/integration/test_traco_m6.py` — falha se `RestricaoRegistrada`, `PassoConcluido`, `CicloFechado` não emitirem traço |
| 13 | Sem SDK, chave ou prompt no produto | `grep -rniE "genai\|openai\|anthropic\|api[_-]?key" backend/ frontend/src/ \| wc -l` = 0 |
| 14 | Jornada viva com captura por passo | `ls docs/jornadas/` contém a jornada do M6 com uma captura por passo; grep negativo de nome real de pessoa |
| 15 | Conformidade do ciclo | `scripts/check-conformance.sh 009` código 0 |
| 16 | Caminhos e links | `scripts/check-caminhos.sh` e `scripts/check-links.sh` código 0 + quanto examinaram |

## Fontes

F-01: linhagem TOC-Builder (4 gerações) — prova de ausência, executada em 2026-09-03:
`grep -rniE "focaliza|five focusing|cinco passos" TOC-Builder TOC-Builder-APP
TOC-Builder-V2 tocbuilderv3 --include="*.ts" --include="*.tsx" --include="*.md" |
wc -l` → `0` — os cinco passos nunca existiram na linhagem, nem a palavra; este módulo
não tem código-fonte de origem 🟢

F-02: [`../../docs/adr/0005-escopo-do-dominio-v1.md`](../../docs/adr/0005-escopo-do-dominio-v1.md)
— decisão 2: a focalização entra na v1 como módulo novo, "é o que transforma um editor
de diagramas em uma aplicação de TOC"; o grep de 9 diretórios com saída `0` está colado
no próprio ADR; DBR e contabilidade de ganho fora (decisão 3) 🟢

F-03: [`../../docs/produto/visao.md`](../../docs/produto/visao.md) §6, defeito D-09 —
"Os cinco passos de focalização não existem na linhagem — nem a palavra", com o console
da medição colado 🟢

F-04: [`../../docs/produto/rounds.md`](../../docs/produto/rounds.md) — Round 009:
aptidão executável (cinco passos com estado herdado; recomeçar reabre apontando a nova
restrição "sem apagar a jornada anterior (histórico é apêndice, não sobrescrita)");
**sai primeiro** a sugestão assistida; **nunca sai** o registro da restrição 🟢

F-05: [`../../docs/governance/constitution.md`](../../docs/governance/constitution.md)
itens 4 (verbo mutador nasce proposta), 7 (tela é dado) e 8 (manipulação direta sob
três testes; FSM uma só e do servidor) — a moldura da única ação assistida do módulo 🟢

F-06: [`../../docs/roadmap.md`](../../docs/roadmap.md) — Ciclo 009: os dois portões
(teste dos cinco passos com estado herdado; jornada sintética com captura por passo) e
as duas pré-condições ("O ciclo 008 promovido"; "ADR 0005 inalterado") 🟢

F-07: [`../../docs/produto/modulos.md`](../../docs/produto/modulos.md) — M6: épicos
E6.1/E6.2, dependências (jornada de M2 e M4; registro só de M1) 🟢

## Lacunas e assunções

L-01: A taxonomia de tipos de restrição (`fisica` | `politica` | `de_mercado`) não tem
precedente na linhagem (que nunca teve restrição) nem norma no corpus. Assunção: os
três tipos clássicos da literatura TOC bastam para a v1, como enum fechado com evento —
ampliar é migração aditiva pequena; risco **baixo**.

L-02: O desenho das DecisoesHerdadas assume que as decisões "de exploração e
subordinação" são as que geram inércia — as de identificar e elevar morrem com o ciclo.
Assunção: é a leitura direta do quinto passo do método ("não deixe a inércia virar a
restrição do sistema": o que sobrevive por inércia são regras de operação); risco
**baixo** (incluir os demais passos na herança é mudança de filtro, não de modelo).

L-03: A navegação de volta (da ARA/NC/APR para a análise que a vinculou) resolve por
consulta ao M6, sem campo novo nos módulos M2–M4. Assunção: consulta indexada basta
para a escala da v1 e evita acoplamento reverso; se o custo aparecer, um índice
materializado resolve sem tocar nos agregados das ferramentas; risco **baixo**.

L-04: `toc.suggest_constraint` não tem precedente em nenhuma geração (a linhagem não
tinha restrição para sugerir). Assunção: candidatas derivadas dos nós de causa raiz da
ARA são um primeiro recorte útil; o round já a marca "sai primeiro" — o risco de errar
o desenho é pago com o corte, não com o ciclo; risco **baixo**.

L-05: O ciclo 002 (protótipo de interfaces) cobriu RIs de M1–M3; as telas de jornada do
M6 podem não ter `ux-design.md` prévio. Assunção: o desenho nasce neste ciclo sob o
mesmo processo (papel semântico → ux-design → jornada viva), no mesmo pull request;
risco **médio** — é o único módulo de superfície nova sem protótipo anterior, e o
apetite do ciclo paga esse desenho.

## Clarify

- [DÚVIDA] Tipos de restrição (L-01): o Product Steward confirma o enum fechado
  `fisica` | `politica` | `de_mercado`, ou prefere tipo livre com sugestões?
- [DÚVIDA] Herança anti-inércia (L-02): herdar só decisões de explorar e subordinar,
  como a spec assume, ou todas as decisões do ciclo anterior?
- [DÚVIDA] Reabrir passo (RF-10): limitado ao passo imediatamente anterior, como a spec
  assume, ou até qualquer passo já concluído do ciclo aberto?
- [DÚVIDA] Encerrar análise sem recomeçar (RN-07): arquivar pelo M1 basta, ou o Product
  Steward quer um desfecho de primeira classe ("meta atingida / análise encerrada") na
  linha do tempo?
- [DÚVIDA] Telas do M6 (L-05): desenhar o ux-design da jornada dentro do ciclo 009,
  como a spec assume, ou antecipar um adendo ao protótipo do ciclo 002 antes de abrir?
