# Spec 008 — Árvores de Futuro e Implementação (M4 — Árvores de Futuro e Implementação)

> Siglas: TOC — Teoria das Restrições · ARA — Árvore da Realidade Atual (CRT — *Current
> Reality Tree*) · UDE — Efeito Indesejável (*Undesirable Effect*) · NC — Nuvem de
> Conflito (EC — *Evaporating Cloud*) · ARF — Árvore da Realidade Futura (FRT — *Future
> Reality Tree*) · APR — Árvore de Pré-Requisitos (PRT — *Prerequisite Tree*) · AT —
> Árvore de Transição (TT — *Transition Tree*) · OI — Objetivo Intermediário
> (*Intermediate Objective*) · ED — Efeito Desejável (*Desirable Effect*) · APH —
> Aplicação ↔ Harness · ADR — Architecture Decision Record (Registro de Decisão
> Arquitetural) · RF/RI/RNF/RN/INT — requisito funcional / de interface / não funcional /
> regra de negócio / integração · US — User Story (história de usuário) · DDD —
> Domain-Driven Design (Design Orientado a Domínio) · TDD — Test-Driven Development
> (desenvolvimento guiado por teste) · DoD — Definition of Done (Definição de Pronto) ·
> IA — inteligência artificial · FSM — máquina de estados finitos · OTel — OpenTelemetry
> · JSON — JavaScript Object Notation · i18n — internacionalização · UI — interface de
> usuário · SDK — Software Development Kit (kit de desenvolvimento) · CI — integração
> contínua · REST — Representational State Transfer

- **Status**: Rascunho (aprovação: gate humano do ciclo 001)
- **Raia**: plena
- **Data**: 2026-09-03
- **Origem**: [`../../docs/produto/modulos.md`](../../docs/produto/modulos.md) (M4) ·
  [`../../docs/roadmap.md`](../../docs/roadmap.md) (ciclo 008) ·
  [`../../docs/produto/rounds.md`](../../docs/produto/rounds.md) (round 008)

## O quê e por quê

O M4 é o módulo que faz o toc-federada **suceder a linhagem de fato**, e não apenas
refazê-la melhor. Nas quatro gerações do TOC-Builder, as três ferramentas deste módulo —
ARF, APR e AT — só existiram como **item desabilitado de menu**: o botão cinza está em
`tocbuilderv3/components/Sidebar.tsx:55-57` (F-01), o tipo de navegação em
`tocbuilderv3/types.ts:249-258` (F-02), os rótulos traduzidos em `locales/pt.ts:68-70`
(F-04) — e **nada mais**: zero componentes (F-05), zero prompts (F-06), zero linhas de
domínio (F-07). É o defeito D-04 da visão. A linhagem chegou a **declarar a intenção** de
encadeá-las — `Sidebar.tsx:86` condiciona as três à existência de um projeto ARA
carregado (F-03) — mas nenhum modelo de dados jamais carregou uma referência entre
projetos: a contagem de referências cruzadas na 4ª geração é zero (D-11, F-08).

As três ferramentas são a metade **prescritiva** dos Processos de Pensamento: a ARA (M2)
e a NC (M3) respondem "o que mudar"; a ARF responde "**para o que** mudar" — projeta a
realidade com as injeções da NC aplicadas e verifica, por suficiência causal, que os UDEs
viram EDs sem criar efeitos negativos novos; a APR responde "**como causar** a mudança" —
levanta os obstáculos que a realidade atual opõe à implementação e os supera com OIs
sequenciados por dependência (lógica de condição necessária — F-09); e a AT desce ao chão
— cada passo com sua ação, sua necessidade e seu resultado esperado.

O épico diferencial é o **E4.4, o encadeamento**: UDE validado da ARA alimenta a NC;
injeção escolhida da NC semeia a ARF; a ARF gera os obstáculos que a APR sequencia; o OI
vira alvo de uma AT. A spec do M3 já criou o lugar do dado (ReferenciaDeOrigem e
ReferenciaDeSemeadura — F-10) e delegou a execução a este ciclo (INT-05 e INT-06 de lá).
Sem o E4.4, este módulo entregaria três ilhas novas — exatamente o D-11 com mais
ferramentas. Com ele, a referência cruzada vira **cidadã do modelo**, com origem e
destino tipados, e a análise inteira passa a ser percorrível de ponta a ponta.

## O que entra como dado

- **Núcleo M1** ([`../004-nucleo-de-diagramas/spec.md`](../004-nucleo-de-diagramas/spec.md)):
  projeto, nó, aresta causal, canvas, vista tabular, desfazer, exclusão suave,
  exportação. ARF, APR e AT são **tipos de projeto** sobre esse núcleo (RN-04 de lá: o
  núcleo não conhece semântica TOC; estende-se por composição), como a ARA e a NC.
- **ARA promovida (ciclo 005)** ([`../005-arvore-da-realidade-atual/spec.md`](../005-arvore-da-realidade-atual/spec.md)):
  UDE validado (a origem da cadeia), exame de elo e conector E — a lógica de suficiência
  que a ARF **reusa** (F-11; decisão de arquitetura no plan: pacote comum, nunca cópia).
- **NC promovida (ciclo 007)** ([`../007-nuvem-de-conflito/spec.md`](../007-nuvem-de-conflito/spec.md)):
  injeção com status `escolhida` e os campos ReferenciaDeOrigem/ReferenciaDeSemeadura já
  criados vazios — os INT-05 e INT-06 de lá são **executados aqui** (F-10).
- **Junta 003 + ciclo 006**: identidade por introspecção, isolamento por inquilino, OTel;
  catálogo `toc.*`, FSM de proposta (uma só e do servidor), registro de telas e snapshot
  sanitizado. Diferença para o M2: quando este ciclo abrir, a FSM **existe** — as ações
  assistidas do M4 executam neste ciclo, não ficam em contrato.
- **Round 008** ([`../../docs/produto/rounds.md`](../../docs/produto/rounds.md)):
  apetite de um ciclo; **fora**: tratamento assistido de ramos negativos (fica a marcação
  manual — pré-condição do roadmap, F-13); corte: **sai primeiro a AT (E4.3)**; **nunca
  sai o encadeamento (E4.4)** — sem ele o round entrega o próprio D-11.
- **IA somente pela fundação** (ADR 0007,
  [`../../docs/adr/0007-ia-somente-pela-fundacao.md`](../../docs/adr/0007-ia-somente-pela-fundacao.md)):
  sugestão de modelo nasce `action_proposal`; prompts versionados no servidor.
- **Alcance do P2 e item 8** (constituição própria,
  [`../../docs/governance/constitution.md`](../../docs/governance/constitution.md),
  linhas 64-71 e 87-94 — F-15): promover, semear e derivar são **manipulação direta do
  titular** — aplicam na hora, com traço e reversibilidade; sugestões inferidas por
  modelo nascem proposta.
- **Base sintética** (ADR 0006,
  [`../../docs/adr/0006-base-sintetica-desde-o-dia-1.md`](../../docs/adr/0006-base-sintetica-desde-o-dia-1.md)):
  toda fixture e exemplo usa a "Instituição Horizonte" e personas fictícias.

## Épicos, features e user stories

### E4.1 — ARF (injeções → efeitos futuros)

**F4.1.1 — Projeto ARF sobre o núcleo** — tipo de projeto `arf` com nós tipados por
papel (injeção · efeito futuro) e arestas de suficiência com o exame herdado da ARA.

- US-01 — Como Facilitadora TOC, quero construir a realidade futura partindo de
  injeções e descendo por "se… então…", para verificar que a solução escolhida produz
  os efeitos que promete.
  - Dado um projeto ARF da Instituição Horizonte com a injeção "faseamento orçamentário
    condicionado a marco de receita", Quando ligo a injeção ao efeito futuro "as duas
    frentes recebem verba no trimestre", Então a aresta se lê "Se a injeção, então o
    efeito" na ficha do elo, e o exame de suficiência fica disponível como na ARA.

**F4.1.2 — Efeitos desejáveis espelhando UDEs** — marcar um efeito futuro como ED que
converte um UDE específico da análise; o espelho UDE → ED é a medida de completude da
ARF.

- US-02 — Como Gestora, quero ver quais UDEs da análise já têm ED correspondente
  alcançado na ARF, para saber se a solução cobre a dor que motivou tudo.
  - Dado uma ARF semeada de uma NC cuja origem aponta 5 UDEs, Quando abro o resumo de
    cobertura, Então vejo, por UDE, se existe ED espelhado e se há caminho de alguma
    injeção até ele — e os descobertos ficam listados como pendência.

**F4.1.3 — Ramos negativos com tratamento manual** — marcar um sub-ramo como
consequência negativa de uma injeção, com estado `aberto → tratado | aceito`; o
tratamento assistido está fora do round (F-12).

- US-03 — Como Facilitadora TOC, quero marcar um ramo da ARF como negativo e registrá-lo
  como tratado quando uma injeção adicional o cortar, para que a solução não esconda
  seus efeitos colaterais.
  - Dado o efeito futuro "a equipe da Secretaria acumula dupla jornada" derivado de uma
    injeção, Quando o marco como ramo negativo, Então ele entra na lista de ramos
    abertos; e Quando adiciono a injeção "contratação temporária no pico" ligada a ele e
    o marco `tratado`, Então a lista o move para tratados com a injeção referenciada.
- US-04 — Como Participante, quero ver os ramos negativos abertos de uma ARF, para
  levantar objeções enquanto elas ainda são baratas.
  - Dado uma ARF com 2 ramos abertos e 1 aceito, Quando abro o painel de ramos, Então
    vejo os 2 abertos com seus nós, e o aceito com a justificativa de quem o aceitou.

**F4.1.4 — Verificação estrutural da ARF** — função pura sobre o grafo: EDs sem caminho
desde injeção, injeções sem efeito, ramos negativos abertos, cobertura do espelho UDE →
ED.

- US-05 — Como Facilitadora TOC, quero um relatório estrutural antes de dar a ARF por
  pronta, para não declarar futuro o que a lógica ainda não sustenta.
  - Dado uma ARF com 1 ED sem caminho e 1 ramo negativo aberto, Quando gero o relatório,
    Então os dois aparecem como pendências com ação de foco no canvas, e a cobertura diz
    quantos UDEs referenciados têm ED alcançado.

### E4.2 — APR (obstáculos → objetivos intermediários, sequenciamento)

**F4.2.1 — Projeto APR com papéis e lógica de necessidade** — tipo `apr` com objetivo,
obstáculos e OIs como nós tipados; a aresta é dependência ("A precisa existir antes de
B"), não suficiência (F-09).

- US-06 — Como Facilitadora TOC, quero criar uma APR com o objetivo verbalizado no
  presente e os elementos tipados, para planejar a implementação com a lógica certa —
  necessidade, não causa.
  - Dado um projeto APR com objetivo "O processo de matrícula responde em 2 dias",
    Quando adiciono um obstáculo e um OI, Então cada um nasce com o papel visível e a
    aresta entre OIs se lê "precisa existir antes de", nunca "se… então…".

**F4.2.2 — Pareamento obstáculo ↔ OI** — cada obstáculo pareado com o OI que o supera
ou torna irrelevante; o teste de validade do par é julgamento registrado (F-09).

- US-07 — Como Facilitadora TOC, quero registrar, para cada obstáculo, o OI que o
  supera, e registrar meu julgamento do teste de validade, para que a árvore não carregue
  OI órfão nem obstáculo sem resposta.
  - Dado o obstáculo "há apenas uma pessoa treinada no sistema de matrículas", Quando o
    pareio com o OI "existem três pessoas treinadas e escaladas", Então o par aparece na
    tabela resumo; e Quando registro o julgamento "Se o OI, então o obstáculo não impede
    mais o objetivo — válido", Então o parecer fica no par com autor e data.
- US-08 — Como Participante, quero contribuir obstáculos numa sessão de "sim, mas…" pela
  vista tabular, para que o levantamento em grupo flua sem disputa de canvas.
  - Dado o painel de entidades aberto, Quando adiciono um obstáculo pela tabela, Então
    ele aparece no canvas sem par ainda — e entra na lista de obstáculos sem OI.

**F4.2.3 — Verbalização avaliada** — heurística decidível de domínio (sem rede, sem
modelo) sobre a forma: obstáculo é condição presente, não tarefa nem previsão; OI é
estado conquistado, não ação — o mesmo padrão da validação formal do M2.

- US-09 — Como Participante, quero um aviso na hora quando escrevo um obstáculo como
  tarefa disfarçada, para corrigir a formulação enquanto ainda lembro o que quis dizer.
  - Dado o texto "Precisamos criar a conversão de dados", Quando o registro como
    obstáculo, Então recebo o aviso "verbo de ação: obstáculo descreve condição que
    existe hoje" com a sugestão de reformular — offline, em menos de um segundo, e o
    registro não é bloqueado (aviso, não veto — RN-08).

**F4.2.4 — Sequenciamento por dependência** — grafo de OIs acíclico organizado em
camadas de implementação; ramos paralelos identificados; elipse de simultaneidade para
pré-requisitos conjuntos; tabela resumo obstáculo ↔ OI ↔ depende de.

- US-10 — Como Facilitadora TOC, quero sequenciar os OIs por dependência e ver as
  camadas de implementação, para saber o que pode andar em paralelo e o que espera.
  - Dado 6 OIs com dependências declaradas, Quando gero o sequenciamento, Então vejo as
    camadas (o que não depende de nada primeiro), os ramos paralelos e as elipses de
    simultaneidade — e uma dependência circular é apontada como pendência bloqueante.
- US-11 — Como Gestora, quero a tabela resumo — obstáculo, OI que o supera, de quem
  depende — para levar o plano à reunião sem exigir leitura de diagrama.
  - Dado uma APR sequenciada, Quando abro a tabela resumo, Então cada linha traz
    obstáculo, OI e dependências, na ordem das camadas, exportável com o projeto.

### E4.3 — AT (passos de transição)

**F4.3.1 — Passo com a tripla ação · necessidade · resultado esperado** — a AT desce um
OI (ou o objetivo) a passos encadeados por precedência, cada um com a sua lógica.

- US-12 — Como Facilitadora TOC, quero montar a AT de um OI com passos que digam por que
  existem e o que devem produzir, para que o plano seja auditável passo a passo.
  - Dado o OI "existem três pessoas treinadas e escaladas", Quando adiciono o passo com
    ação "publicar a chamada interna de treinamento", necessidade "não há hoje candidato
    mapeado" e resultado esperado "lista de inscritos até sexta", Então o passo se lê
    "Para <necessidade>, <ação>; espero <resultado>" na ficha, e a aresta o encadeia ao
    passo seguinte.

**F4.3.2 — Acompanhamento de execução** — status por passo (`pendente · em_execucao ·
concluido · bloqueado`), com o resultado real registrado ao concluir — acompanhamento
leve, não gestor de projetos.

- US-13 — Como Gestora, quero ver quais passos da AT estão concluídos e quais estão
  bloqueados, para agir onde a implementação emperrou.
  - Dado uma AT com 5 passos, Quando um é marcado `bloqueado` com o motivo, Então o
    resumo mostra a contagem por status e o passo bloqueado com seu motivo; e Quando um
    é concluído com resultado real divergente do esperado, Então a divergência fica
    registrada no evento — insumo para revisitar a árvore, não para apagar o esperado.

### E4.4 — Encadeamento (a razão de ser do módulo)

**F4.4.1 — Referência cruzada tipada como cidadã do modelo** — origem e destino tipados
(projeto + elemento + papel), criada somente por ação nomeada, com estado que sobrevive
a exclusão suave — a correção estrutural do D-11.

- US-14 — Como Participante, quero ver em qualquer elemento encadeado de onde ele veio e
  o que ele gerou, para nunca perder o fio da análise entre ferramentas.
  - Dado um obstáculo derivado de uma ARF, Quando abro sua ficha, Então vejo "origem:
    ARF <nome>, efeito <texto>" com ação de ir até lá; e na ARF, o efeito mostra
    "derivou: obstáculo na APR <nome>".

**F4.4.2 — Promoção UDE → NC** — executa o INT-05 da spec 007: promover o dilema por
trás de UDEs validados para uma NC nova, preenchendo a ReferenciaDeOrigem de lá.

- US-15 — Como Facilitadora TOC, quero promover UDEs validados da ARA para uma Nuvem de
  Conflito, para modelar o dilema que os sustenta sem redigitar nada.
  - Dado 2 UDEs `Validado` selecionados na ARA, Quando aciono "promover para NC", Então
    nasce uma NC com a ReferenciaDeOrigem apontando os 2 UDEs, a leitura "origem:
    UDEs …" ativa do lado da NC, e a referência cruzada registrada com evento — sem
    tela de confirmação (alvo nomeado pelo gesto, reversível por exclusão suave), com
    traço.

**F4.4.3 — Semeadura injeção → ARF** — executa o INT-06 da spec 007: a injeção
`escolhida` semeia uma ARF nova com a injeção como primeiro nó, preenchendo a
ReferenciaDeSemeadura de lá.

- US-16 — Como Facilitadora TOC, quero semear a ARF a partir da injeção escolhida da
  nuvem, para que a árvore de futuro nasça do compromisso do grupo, não de uma folha em
  branco.
  - Dado uma injeção com status `escolhida`, Quando aciono "semear ARF", Então nasce um
    projeto ARF com a injeção como nó semente, a ReferenciaDeSemeadura da NC preenchida
    com o identificador da ARF, e a cadeia UDE → NC → injeção → ARF percorrível nos dois
    sentidos.

**F4.4.4 — Derivação ARF → APR e OI → AT** — do lado de baixo da cadeia: derivar
obstáculos da APR a partir da ARF (a injeção a implementar, o efeito a causar) e criar a
AT de um OI, sempre com referência registrada.

- US-17 — Como Facilitadora TOC, quero derivar da ARF a APR de implementação e de um OI
  a sua AT, para que cada ferramenta continue exatamente de onde a anterior parou.
  - Dado uma ARF verificada, Quando aciono "derivar APR", Então nasce uma APR com o
    objetivo proposto a partir do texto da injeção/efeito escolhido e a referência de
    origem registrada; e Dado um OI sequenciado, Quando aciono "criar AT deste OI",
    Então nasce a AT com o OI como alvo e a referência registrada.

**F4.4.5 — Vista da cadeia** — a travessia completa: UDE → NC → injeção → ARF →
obstáculo → OI → passo, computada por função pura sobre as referências, navegável com
foco em cada ferramenta.

- US-18 — Como Gestora, quero percorrer a cadeia inteira de uma análise, para apresentar
  em uma tela o caminho do sintoma ao plano de execução.
  - Dado a análise sintética completa da Instituição Horizonte, Quando abro a vista da
    cadeia a partir de um UDE, Então vejo os elos até o passo da AT, cada um com nome,
    ferramenta e estado; um elo com ponta excluída aparece `pendente` (nunca some em
    silêncio), e clicar num elo abre a ferramenta com o elemento focado.

## Entidades e modelo de domínio

DDD puro — domínio sem framework, sem rede, sem relógio (P3). Os três tipos de projeto
**estendem** o modelo do M1
([`../004-nucleo-de-diagramas/data-model.md`](../004-nucleo-de-diagramas/data-model.md))
por composição, como M2 e M3; o documento consolidado nasce na abertura do ciclo (T-02).

- **ProjetoARF**: o agregado Projeto do M1 com `tipo_de_ferramenta = arf`. Nós com
  **PapelNaARF** (`injecao` | `efeito_futuro`); arestas de **suficiência** com o exame
  de elo e o conector E **reusados do pacote de suficiência causal** extraído do M2
  (decisão de arquitetura no plan — nunca cópia).
- **EspelhoDeUde** (objeto de valor no nó de efeito futuro): a marca de ED — referência
  ao identificador do UDE que este efeito converte (RN-03). Um UDE tem no máximo um ED
  espelhado por ARF.
- **RamoNegativo** (entidade do agregado ARF): raiz do sub-ramo (nó) + estado (`aberto`
  | `tratado` | `aceito`) + justificativa (obrigatória em `aceito`) + referência à
  injeção que o trata (obrigatória em `tratado`) (RN-04).
- **VerificacaoDaARF** (serviço de domínio, função pura): EDs sem caminho desde injeção,
  injeções sem efeito ligado, ramos negativos abertos, cobertura do espelho UDE → ED.
  Não muta nada; sem rede e sem modelo.
- **ProjetoAPR**: Projeto com `tipo_de_ferramenta = apr`. Nós com **PapelNaAPR**
  (`objetivo` — exatamente um — | `obstaculo` | `objetivo_intermediario`); arestas de
  **dependência** entre OIs ("precisa existir antes de" — RN-05), sem leitura de
  suficiência.
- **ParObstaculoOI** (entidade do agregado APR): obstáculo ↔ OI que o supera, com o
  julgamento do teste de validade (parecer com autor e data — RN-07); um OI pode superar
  mais de um obstáculo; obstáculo sem par e OI sem par são **pendências**, não
  proibições (RN-09).
- **ElipseDeSimultaneidade** (entidade do agregado APR): conjunto de ≥ 2 dependências
  com o mesmo OI de destino, lidas em conjunção — a contraparte de necessidade do
  conector E (F-09).
- **VerbalizacaoAvaliada** (objeto de valor, resultado de função pura): avisos por
  heurística — verbo de ação em obstáculo/OI, previsão futura em obstáculo, ausência
  genérica — com o trecho apontado e veredito `atende` | `aviso` | `indeterminado`;
  determinística, sobre léxico versionado por idioma (reuso da infraestrutura do M2).
- **Sequenciamento** (serviço de domínio, função pura): camadas topológicas dos OIs,
  ramos paralelos, elipses, ciclos como pendência bloqueante (RN-06). Não muta nada.
- **ProjetoAT**: Projeto com `tipo_de_ferramenta = at` + **alvo** (referência ao OI ou
  objetivo de origem, quando derivado). Nós são passos; arestas são precedência.
- **FichaDePasso** (objeto de valor no nó da AT): `acao` + `necessidade` +
  `resultado_esperado` (os três obrigatórios — RN-10) + `status` (`pendente` |
  `em_execucao` | `concluido` | `bloqueado`) + `motivo_do_bloqueio` | `resultado_real`
  conforme o status.
- **ReferenciaCruzada** (agregado próprio, fora dos projetos): `tipo`
  (`promocao_ude_nc` | `semeadura_injecao_arf` | `derivacao_arf_apr` |
  `derivacao_oi_at`) + origem (projeto, elemento, papel) + destino (projeto, elemento) +
  estado (`ativa` | `pendente`) + evento de criação. Criada **somente** por ação nomeada
  (RN-11); exclusão suave de qualquer ponta a torna `pendente`, restauração reativa
  (RN-12). Os campos ReferenciaDeOrigem/ReferenciaDeSemeadura da NC (F-10) são
  preenchidos na mesma transação, como projeção local de leitura.
- **VistaDaCadeia** (serviço de domínio, função pura sobre as referências): a travessia
  UDE → NC → injeção → ARF → obstáculo → OI → passo, com estado por elo. Não muta nada.
- **Eventos de domínio** (somente-acréscimo, além dos do M1): `EfeitoEspelhouUde`,
  `RamoNegativoMarcado`, `RamoNegativoTratado`, `RamoNegativoAceito`,
  `VerificacaoDaArfGerada`, `ObstaculoPareado`, `TesteDeValidadeJulgado`,
  `SequenciamentoGerado`, `ElipseFormada`, `ElipseDesfeita`, `PassoMudouDeStatus`,
  `UdePromovidoParaNc`, `InjecaoSemeouArf`, `ArfDerivouApr`, `OiDerivouAt`,
  `ReferenciaCriada`, `ReferenciaSuspensa`, `ReferenciaReativada`.
- **Fora do domínio**: prompts e provedores (servidor da fundação — ADR 0007); a FSM de
  `action_proposal` (uma só e do servidor — ciclo 006); o layout dos três canvas.

## Requisitos funcionais

### Projeto ARF e efeitos futuros

RF-01: O SISTEMA DEVE permitir criar projeto do tipo ARF, herdando do M1 canvas, vista
tabular, desfazer de sessão, exclusão suave e exportação sem reimplementação. [F-01,
F-02] 🟡

RF-02: O SISTEMA DEVE tipar cada nó da ARF com o papel `injecao` ou `efeito_futuro`,
distintos visualmente, e permitir mudar o papel enquanto o nó não tiver vínculo que o
proíba (injeção referenciada por ramo tratado não vira efeito). 🟡

RF-03: O SISTEMA DEVE apresentar a leitura de suficiência de cada aresta da ARF — "Se
<origem>, então <destino>" — e oferecer o exame de elo e o conector E do pacote de
suficiência causal compartilhado com a ARA, sem duplicação de regra. [F-11] 🟡

RF-04: O SISTEMA DEVE permitir marcar um efeito futuro como ED espelhando um UDE
referenciado pela cadeia da análise (RN-03), e DEVE recusar espelhar o mesmo UDE em dois
EDs da mesma ARF. 🟡

RF-05: O SISTEMA DEVE apresentar o resumo de cobertura da ARF: por UDE referenciado, se
existe ED espelhado e se há caminho de alguma injeção até ele. 🟡

RF-06: QUANDO uma ARF nascer por semeadura (RF-38), O SISTEMA DEVE criar a injeção
semente como nó do papel `injecao` com o texto da injeção de origem — editável dali em
diante sem quebrar a referência. 🟡

RF-07: O SISTEMA DEVE permitir ARF criada do zero (sem semeadura), com o espelho de UDE
disponível apenas quando houver cadeia que forneça UDEs referenciáveis — sem cadeia, a
cobertura declara "sem origem vinculada". 🟡

### Ramos negativos

RF-08: O SISTEMA DEVE permitir marcar um nó da ARF como raiz de ramo negativo, com
estado inicial `aberto`, e listar os ramos por estado no painel da ARF. [F-12] 🟡

RF-09: O SISTEMA DEVE permitir transicionar um ramo negativo para `tratado` somente com
referência a uma injeção que o corta, e para `aceito` somente com justificativa —
registrando o evento correspondente com autor (RN-04). 🟡

RF-10: O SISTEMA NÃO DEVE oferecer, neste ciclo, nenhuma rota assistida de identificação
ou tratamento de ramos negativos — a marcação é manual por decisão de round (F-12,
F-13); a prova é negativa (DoD 8). 🟡

### Verificação estrutural da ARF

RF-11: O SISTEMA DEVE computar por função pura de domínio, sem rede e sem modelo, a
verificação da ARF: EDs sem caminho desde injeção, injeções sem efeito ligado, ramos
negativos abertos e cobertura do espelho UDE → ED. 🟡

RF-12: O SISTEMA DEVE oferecer, em cada item da verificação, ação de foco que centraliza
o elemento no canvas (mesmo mecanismo do M1 e do relatório do M2). 🟡

RF-13: O SISTEMA DEVE registrar `VerificacaoDaArfGerada` com o resumo quantitativo
(contagens por seção), para a jornada e o traço mostrarem a maturação da árvore. 🟡

### Projeto APR: obstáculos e objetivos intermediários

RF-14: O SISTEMA DEVE permitir criar projeto do tipo APR com exatamente um nó de papel
`objetivo`, criado na origem e indestrutível enquanto o projeto viver — texto editável,
papel não. 🟡

RF-15: O SISTEMA DEVE tipar os demais nós da APR como `obstaculo` ou
`objetivo_intermediario`, com criação disponível no canvas e na vista tabular. [F-09] 🟡

RF-16: O SISTEMA DEVE tratar a aresta da APR como dependência entre OIs (ou OI →
objetivo), lida "precisa existir antes de" — e NÃO DEVE apresentar leitura de
suficiência nem exame de elo nesse tipo de projeto (RN-05). [F-09] 🟡

RF-17: O SISTEMA DEVE permitir parear cada obstáculo com o OI que o supera (um OI pode
superar vários obstáculos), listando como pendência os obstáculos sem OI e os OIs sem
obstáculo (RN-09). [F-09] 🟡

RF-18: O SISTEMA DEVE registrar o julgamento do teste de validade de cada par — "Se
<OI>, então <obstáculo> não impede mais <objetivo>" — como parecer com autor e data,
acumulável e nunca sobrescrito (RN-07; o padrão de parecer do M2). [F-09] 🟡

RF-19: O SISTEMA DEVE permitir agrupar duas ou mais dependências com o mesmo OI de
destino numa elipse de simultaneidade, com a leitura conjunta "A **e** B precisam
existir antes de C", e desfazê-la (RN-06). [F-09] 🟡

### Verbalização avaliada

RF-20: O SISTEMA DEVE avaliar a verbalização de obstáculo e de OI por função pura de
domínio, sem rede e sem modelo, devolvendo avisos com o trecho apontado: verbo de ação
(tarefa disfarçada), previsão futura em obstáculo, ausência genérica em vez de condição
específica (RN-08). [F-09] 🟡

RF-21: O SISTEMA DEVE tratar o aviso de verbalização como orientação, nunca veto: o
registro procede, o aviso persiste visível até o texto mudar, e a reavaliação é
automática na edição (RN-08). 🟡

RF-22: O SISTEMA DEVE manter o léxico das heurísticas de verbalização como dado
versionado por idioma sobre a mesma infraestrutura do léxico do M2, com corpus sintético
próprio de obstáculos e OIs bons e maus — devolvendo `indeterminado` quando a heurística
não alcançar o caso. 🟡

### Sequenciamento por dependência

RF-23: O SISTEMA DEVE computar por função pura de domínio o sequenciamento da APR:
camadas topológicas dos OIs (quem não depende de nada primeiro), ramos paralelos e
elipses de simultaneidade. [F-09] 🟡

RF-24: QUANDO houver dependência circular entre OIs, O SISTEMA DEVE apontá-la como
pendência bloqueante do sequenciamento, listando o ciclo com seus nós — diferente da
ARA, onde ciclo é legítimo (RN-06 aqui; RF-29 do M2 lá). 🟡

RF-25: O SISTEMA DEVE gerar a tabela resumo — obstáculo, OI que o supera, dependências —
na ordem das camadas, exibível na vista tabular e incluída na exportação do projeto.
[F-09] 🟡

RF-26: O SISTEMA DEVE registrar `SequenciamentoGerado` com o resumo quantitativo
(camadas, OIs por camada, pendências). 🟡

RF-27: O SISTEMA DEVE recalcular pendências de pareamento e de sequenciamento a cada
mutação relevante (nó, aresta, par, elipse), sem exigir regeneração manual para os
contadores do cabeçalho. 🟡

### Árvore de transição

RF-28: O SISTEMA DEVE permitir criar projeto do tipo AT, do zero ou derivado de um OI
(RF-40), com nós-passo e arestas de precedência herdando canvas e tabela do M1. 🟡

RF-29: O SISTEMA DEVE exigir em cada passo a tripla ação, necessidade e resultado
esperado, e apresentar a leitura "Para <necessidade>, <ação>; espero <resultado>" na
ficha do passo (RN-10). 🟡

RF-30: O SISTEMA DEVE manter o status de cada passo (`pendente` | `em_execucao` |
`concluido` | `bloqueado`), exigindo motivo no bloqueio e registrando o resultado real
na conclusão — divergência entre esperado e real fica no evento, nunca sobrescreve o
esperado. 🟡

RF-31: O SISTEMA DEVE apresentar o resumo de execução da AT (contagem por status,
passos bloqueados com motivo) no cabeçalho do projeto. 🟡

RF-32: O SISTEMA DEVE ordenar a leitura da AT pela precedência declarada e apontar
passos inalcançáveis (sem caminho desde os passos iniciais) como pendência. 🟡

### Referências cruzadas e promoções

RF-33: O SISTEMA DEVE manter a referência cruzada como agregado próprio com origem e
destino tipados (projeto, elemento, papel) e tipo do vínculo (`promocao_ude_nc` |
`semeadura_injecao_arf` | `derivacao_arf_apr` | `derivacao_oi_at`), criada somente por
ação nomeada com evento (RN-11). [F-08] 🟡

RF-34: O SISTEMA DEVE exibir, na ficha de qualquer elemento encadeado, suas referências
de origem e de destino com ação de navegar até a outra ponta. 🟡

RF-35: QUANDO qualquer ponta de uma referência sofrer exclusão suave, O SISTEMA DEVE
marcar a referência `pendente` — visível como tal na vista da cadeia — e reativá-la na
restauração; referência nunca é apagada por efeito colateral (RN-12). 🟡

RF-36: O SISTEMA DEVE permitir promover um ou mais UDEs `Validado` de uma ARA para uma
NC nova, preenchendo a ReferenciaDeOrigem da NC (INT-05 da spec 007) e registrando
`UdePromovidoParaNc` — aplicação direta sob o item 8, com traço. [F-10] 🟡

RF-37: O SISTEMA DEVE recusar a promoção de UDE que não esteja no status `Validado` —
a cadeia nasce de sintoma auditado, não de rascunho (RN-13). 🟡

RF-38: O SISTEMA DEVE permitir semear uma ARF a partir de uma injeção `escolhida`,
criando o nó semente (RF-06), preenchendo a ReferenciaDeSemeadura da NC (INT-06 da spec
007) e registrando `InjecaoSemeouArf`; injeção `candidata` ou `descartada` não semeia.
[F-10] 🟡

RF-39: O SISTEMA DEVE permitir derivar de uma ARF uma APR nova — objetivo proposto do
texto do efeito ou injeção escolhido pelo gesto, editável — registrando `ArfDerivouApr`
com a referência. 🟡

RF-40: O SISTEMA DEVE permitir criar uma AT a partir de um OI da APR, com o OI como alvo
e `OiDerivouAt` registrado; o alvo aparece na AT com a referência navegável. 🟡

### Vista da cadeia

RF-41: O SISTEMA DEVE computar por função pura, sobre as referências cruzadas, a
travessia completa de uma análise — UDE → NC → injeção → ARF → obstáculo → OI → passo —
com estado por elo (`ativa` | `pendente`) e nos dois sentidos. [F-08] 🟡

RF-42: O SISTEMA DEVE oferecer a vista da cadeia navegável a partir de qualquer elemento
encadeado, com ação de abrir a ferramenta da outra ponta com o elemento focado. 🟡

### Assistência via catálogo (executa neste ciclo — a FSM do 006 existe)

RF-43: O SISTEMA DEVE expor as ações `toc.suggest_future_effects`,
`toc.suggest_obstacles`, `toc.suggest_intermediate_objectives` e
`toc.suggest_transition_steps` no catálogo governado, cada sugestão mutadora nascendo
`action_proposal` individual — aceitar cria o elemento com traço correlacionado à
proposta; recusar não toca o projeto. [F-14] 🟡

RF-44: O SISTEMA DEVE anexar às entradas das ações o contexto de domínio já computado —
verificação da ARF, pendências de pareamento, sequenciamento — e nunca pedir ao modelo o
que a função pura já decide (o padrão fixado pelo RF-33 do M2). 🟡

RF-45: QUANDO a capability de escrita não estiver presente na introspecção, O SISTEMA
DEVE omitir do catálogo as ações mutadoras do M4, mantendo o módulo inteiro funcional
sem assistência — a assistência é aceleradora, nunca dependência. 🟡

## Requisitos de interface

RI-01: Os papéis dos nós — injeção e efeito futuro na ARF; objetivo, obstáculo e OI na
APR; passo na AT — têm representação visual distinta por forma **e** por texto, nunca só
cor. 🟡

RI-02: O ED exibe o selo de espelho com o UDE referenciado; o resumo de cobertura fica
no cabeçalho da ARF com ação de listar UDEs descobertos. 🟡

RI-03: Ramos negativos são visíveis no canvas (marcação na raiz e no sub-ramo) e num
painel lateral por estado, com a justificativa de `aceito` e a injeção de `tratado` a um
clique. 🟡

RI-04: O canvas da APR lê de baixo para cima — camadas de base embaixo, objetivo no topo
— e o obstáculo é anotado junto à dependência que ele motiva, a notação canônica da
ferramenta (F-09). 🟡

RI-05: Os avisos de verbalização aparecem inline no texto do obstáculo/OI com o trecho
apontado, no mesmo padrão da ficha de validação do M2 (RI-03 de lá). 🟡

RI-06: O sequenciamento apresenta as camadas como faixas visuais no canvas e como
seções na tabela resumo; dependência circular é destacada como pendência bloqueante nos
dois lugares. 🟡

RI-07: A elipse de simultaneidade usa a mesma notação visual do conector E (elipse sobre
as arestas), com legenda própria — conjunção de necessidade, não de suficiência. 🟡

RI-08: A ficha do passo da AT apresenta a tripla como leitura corrida ("Para …, …;
espero …") e como campos editáveis; o status é mudável na ficha e na tabela. 🟡

RI-09: Todo elemento encadeado exibe selos discretos de origem e destino (ex.: "de:
NC · para: APR") que abrem a vista da cadeia; elo `pendente` aparece esmaecido com o
motivo, nunca oculto. 🟡

RI-10: A vista da cadeia é uma superfície própria: os elos em sequência com ferramenta,
nome e estado, navegável por teclado, com ação de foco que abre a ferramenta da ponta. 🟡

RI-11: As ações de promover, semear e derivar aparecem no contexto do elemento de origem
(UDE validado, injeção escolhida, efeito da ARF, OI) — nunca num menu global sem alvo. 🟡

RI-12: As propostas das ações assistidas do M4 entram na bandeja de propostas do ciclo
006, com aceitar/recusar por item e a ação de origem declarada. 🟡

RI-13: Toda superfície do módulo respeita tema do hospedeiro com fallback, modo
só-conteúdo e operação por teclado, herdados dos ciclos 002/003; textos por i18n pt/en,
inclusive avisos de verbalização e leituras de aresta. 🟡

## Requisitos não funcionais

RNF-01: A verificação da ARF, o sequenciamento da APR, a verbalização avaliada e a vista
da cadeia são funções puras testáveis sem rede, sem banco e sem modelo — a suíte de
domínio do módulo roda offline por construção (P3, P4). 🟡

RNF-02: A fronteira hexagonal é verificada por `import-linter`: o pacote de domínio do
M4 não importa framework, HTTP, banco nem cliente de IA — o build falha na violação. 🟡

RNF-03: Toda mutação do módulo emite traço OTel correlacionado e log estruturado (P5);
promoções, semeaduras e derivações carregam no traço o identificador da referência
criada — a linha auditável do encadeamento. 🟡

RNF-04: O sequenciamento de uma APR com 100 OIs e 200 dependências computa em menos de
2 segundos no percentil 95 (o teto herdado do M1). 🟡

RNF-05: A vista da cadeia de uma análise com até 50 referências resolve em menos de 1
segundo no percentil 95, medida na jornada viva. 🟡

RNF-06: A verbalização avaliada responde em menos de 100 milissegundos para textos de
até 500 caracteres, no mesmo regime da validação formal do M2 (RNF-04 de lá). 🟡

RNF-07: O corpus sintético de obstáculos e OIs é versionado com a mesma função forçante
do M2: heurística nova sem caso novo no corpus não entra (RNF-07 de lá). 🟡

RNF-08: Nenhum prompt, chave ou cliente de provedor no repositório do produto — o grep
de CI herdado dos ciclos anteriores cobre também os diretórios novos deste módulo (P7,
ADR 0007). 🟡

RNF-09: A integridade das referências cruzadas é coberta por teste de propriedade:
qualquer sequência de exclusões suaves e restaurações termina com toda referência
`ativa` ou `pendente` — nunca apontando para elemento inexistente sem estado que o
diga. 🟡

RNF-10: A exportação JSON dos três tipos de projeto inclui papéis, fichas, pares,
elipses e referências cruzadas, mantendo o determinismo do E1.4 (duas exportações do
mesmo estado são idênticas byte a byte — RF-32 do M1). 🟡

## Regras de negócio

RN-01: A ARF usa lógica de **suficiência causal** — a mesma da ARA: "se <causa>, então
<efeito>" (a distinção suficiência × necessidade está na fonte técnica — F-09). 🟡

RN-02: Injeção é entidade que **não existe ainda** na realidade — o contraste com o
obstáculo da APR, que **existe hoje**; os papéis não se confundem nem se convertem entre
ferramentas (F-09). 🟡

RN-03: ED é efeito futuro que espelha um UDE referenciado pela cadeia; um UDE tem no
máximo um ED por ARF; a cobertura da ARF mede UDEs espelhados **e alcançados** por
injeção. 🟡

RN-04: Ramo negativo transiciona `aberto → tratado` somente com injeção de corte
referenciada, e `aberto → aceito` somente com justificativa e autor; `tratado` e
`aceito` reabrem por ação explícita. 🟡

RN-05: A APR usa lógica de **condição necessária**: a aresta lê "precisa existir antes
de", nunca "se… então…" — as duas lógicas não se misturam no mesmo projeto (F-09). 🟡

RN-06: O grafo de dependência dos OIs é acíclico: dependência circular é pendência
bloqueante do sequenciamento (F-09 — "sequência inválida"); a elipse de simultaneidade
agrupa ≥ 2 dependências com o mesmo destino. 🟡

RN-07: O teste de validade do par obstáculo ↔ OI — "Se <OI>, então <obstáculo> não
impede mais <objetivo>" — é **julgamento** registrado como parecer com autor, nunca
campo calculado (F-09). 🟡

RN-08: A verbalização avaliada **avisa, não veta**: obstáculo verbalizado como tarefa ou
previsão, e OI verbalizado como ação, geram aviso com trecho apontado; o registro
procede e o aviso persiste até o texto mudar (F-09 — regras de Dettmer/Scheinkopf como
heurística decidível parcial). 🟡

RN-09: Obstáculo sem OI e OI sem obstáculo são **pendências** listadas, não proibições
de gravação — o levantamento em grupo precisa registrar antes de parear; o
sequenciamento só se declara completo com pareamento total (F-09). 🟡

RN-10: Todo passo da AT carrega a tripla ação · necessidade · resultado esperado; passo
sem necessidade explícita é o que degrada a AT a lista de tarefas — os três campos são
obrigatórios na criação. 🟡

RN-11: Referência cruzada nasce **somente** por ação nomeada do titular (promover,
semear, derivar) ou por proposta aceita — nunca por inferência silenciosa de sistema ou
modelo; toda criação tem evento com autor (item 8 da constituição — F-15). 🟡

RN-12: Exclusão suave de qualquer ponta **suspende** a referência (`pendente`) e
restauração a **reativa**; nenhuma operação do módulo apaga referência como efeito
colateral — apagar referência é ação própria, com evento. 🟡

RN-13: A promoção UDE → NC exige UDE em status `Validado` (FSM do M2); a semeadura
NC → ARF exige injeção em status `escolhida` (FSM do M3) — a cadeia só avança sobre
material auditado. [F-10, F-11] 🟡

## Integrações

INT-01: O M4 consome do M1 o núcleo (projeto, nó, aresta, canvas, tabela, desfazer,
exportação); do M2, o UDE validado e o pacote de suficiência causal (exame de elo,
conector E); do M3, a injeção `escolhida` e os campos de referência; da junta 003,
identidade, isolamento por inquilino e OTel; do ciclo 006, a FSM de proposta, o catálogo
e o registro de telas. Nenhuma dessas peças é reimplementada aqui. 🟡

INT-02: **Execução do INT-05 da spec 007** ([`../007-nuvem-de-conflito/spec.md`](../007-nuvem-de-conflito/spec.md)):
a promoção UDE → NC (RF-36) preenche a ReferenciaDeOrigem da NC na mesma transação que
cria a ReferenciaCruzada — a ação prometida lá nasce aqui. [F-10] 🟡

INT-03: **Execução do INT-06 da spec 007**: a semeadura injeção → ARF (RF-38) preenche a
ReferenciaDeSemeadura da NC e cria o projeto ARF com o nó semente. [F-10] 🟡

INT-04: As derivações ARF → APR (RF-39) e OI → AT (RF-40) seguem o mesmo regime das
promoções: ação direta do titular sob o item 8 — alvo nomeado pelo gesto, reversível por
exclusão suave, traço obrigatório — sem tela de confirmação e sem FSM de proposta.
[F-15] 🟡

INT-05: `toc.suggest_future_effects` — catálogo `toc.*`, mutadora (cria nós/arestas na
ARF); entrada: injeção + grafo + verificação (RF-11) como contexto; saída: propostas de
efeito futuro ligado, uma `action_proposal` por sugestão. Executa neste ciclo pela FSM
do 006. [F-14] 🟡

INT-06: `toc.suggest_obstacles` — mutadora (cria obstáculos na APR); entrada: objetivo +
elementos existentes + referência da ARF de origem quando houver; saída: propostas de
obstáculo, uma a uma. 🟡

INT-07: `toc.suggest_intermediate_objectives` — mutadora (cria OI pareado); entrada: um
obstáculo + contexto; saída: propostas de OI com o par pré-preenchido — o julgamento do
teste de validade permanece humano (RN-07), nunca vem preenchido pela ação. 🟡

INT-08: `toc.suggest_transition_steps` — mutadora (cria passos na AT); entrada: OI alvo
+ passos existentes; saída: propostas de passo com a tripla completa — proposta sem os
três campos é recusada pela validação de schema antes de virar `action_proposal`. 🟡

INT-09: Telas deste módulo entram no registro de telas do E7.5 com identificador estável
(`toc.arf_canvas`, `toc.apr_canvas`, `toc.apr_sequencia`, `toc.at_canvas`,
`toc.cadeia`), no formato do ciclo 006; textos de efeito, obstáculo, OI, passo e
justificativa marcam `ai_visible` campo a campo para o snapshot sanitizado. 🟡

INT-10: A exportação/importação do E1.4 cobre os três tipos de projeto com seus dados
anexos **e as referências cruzadas** (RNF-10) — o portão executável do round 008
([`../../docs/roadmap.md`](../../docs/roadmap.md)); importar um projeto cujas
referências apontam para fora do arquivo relata os elos como `pendente`, nunca os
descarta em silêncio. [F-13] 🟡

INT-11: Os prompts das quatro ações do catálogo são versionados **no servidor** e nunca
circulam no cliente nem no snapshot (ADR 0007); ramo negativo não tem ação de catálogo
neste ciclo (RF-10). [F-14] 🟡

## Telas e fluxos

### 6.1 Canvas ARF — Job: projetar a realidade com as injeções aplicadas · Campos: nós
(injeção · efeito futuro · selo ED), arestas com exame, conector E, ramos negativos ·
Ações: as do M1 + tipar papel, espelhar UDE, marcar/tratar/aceitar ramo, verificar.

### 6.2 Painel de ramos negativos — Job: encarar os efeitos colaterais da solução ·
Campos: ramos por estado, injeção de corte, justificativa de aceite · Ações: marcar,
tratar com injeção, aceitar com justificativa, reabrir, focar no canvas.

### 6.3 Canvas APR — Job: transformar obstáculos em plano sequenciado · Campos: objetivo
no topo, OIs em camadas, obstáculos anotados nas dependências, elipses de
simultaneidade · Ações: tipar papel, parear obstáculo ↔ OI, julgar validade, declarar
dependência, agrupar elipse, sequenciar.

### 6.4 Tabela resumo da APR — Job: levar o plano à reunião sem diagrama · Campos:
obstáculo · OI que o supera · depende de, na ordem das camadas; pendências de pareamento
· Ações: filtrar, exportar com o projeto, focar no canvas.

### 6.5 Canvas AT — Job: descer o OI a passos auditáveis · Campos: passos com a tripla,
precedência, status com motivo/resultado real · Ações: criar passo, encadear, mudar
status, ver resumo de execução.

### 6.6 Vista da cadeia — Job: percorrer do sintoma ao plano numa tela · Campos: elos
UDE → NC → injeção → ARF → obstáculo → OI → passo, com ferramenta, nome e estado por
elo · Ações: abrir a partir de qualquer elemento, focar a outra ponta, ver motivo de
elo pendente.

### 6.7 Bandeja de propostas (herdada do 006) — Job: aceitar ajuda sem perder a
autoria · Campos: propostas pendentes por ação de origem · Ações: aceitar/recusar por
item.

## Fora de escopo

- **Tratamento assistido de ramos negativos da ARF** — fica a **marcação manual** (F4.1.3),
  por pré-condição do roadmap e pelo *Fora* do round 008
  ([`../../docs/produto/rounds.md`](../../docs/produto/rounds.md)); poda assistida é
  decisão nova, com o seu próprio contrato de ação.
- **Estratégia & Táticas** — é o módulo M5, ciclo 010
  ([`../010-estrategia-e-taticas/spec.md`](../010-estrategia-e-taticas/spec.md)). A APR e a
  AT terminam no passo de transição; comunicar o plano em árvore hierárquica é a outra
  ferramenta, e o vínculo automático entre as duas está fora **também lá**.
- **A jornada dos cinco passos de focalização** — é o M6, ciclo 009
  ([`../009-focalizacao/spec.md`](../009-focalizacao/spec.md)). Este ciclo entrega as
  ferramentas que aquela jornada costura; a costura em si, não.
- **Gestão de execução a partir da AT** — prazo, responsável, calendário, percentual de
  conclusão. A AT registra a tripla ação · necessidade · resultado esperado e o status por
  passo; priorizar e acompanhar o trabalho de pessoas é o produto da irmã
  `gestaodeprioridades`, não esta v1. Entrada aqui seria escopo novo por ADR.
- **Tambor-pulmão-corda e gestão de pulmões sobre os objetivos intermediários da APR** —
  fora da v1 inteira por decisão com medição colada: o grep de
  `tambor|drum|pulmão|buffer|focaliza|throughput` sobre os nove diretórios da linhagem
  devolve **0** em todos os nove
  ([`../../docs/adr/0005-escopo-do-dominio-v1.md`](../../docs/adr/0005-escopo-do-dominio-v1.md)).
  Entrada futura exige ADR que suceda o 0005.
- **Importação de ARF, APR ou AT da linhagem** — não existe formato legado a ler: as
  quatro gerações entregaram item de menu desabilitado, zero componentes, zero prompts e
  zero linhas de domínio (F-01, F-05, F-06, F-07). O E1.4 avançado do ciclo 011 lê o que a
  linhagem de fato produziu, que não inclui estas três árvores.

## Entregáveis

- Domínio Python puro do M4: extensões ARF/APR/AT do agregado Projeto, EspelhoDeUde,
  RamoNegativo, ParObstaculoOI, ElipseDeSimultaneidade, VerbalizacaoAvaliada (léxico
  versionado pt/en + corpus sintético), Sequenciamento, FichaDePasso, ReferenciaCruzada,
  VistaDaCadeia — com testes de domínio **sem rede e sem modelo**, nascidos antes do
  código (P4), incluindo o teste da cadeia inteira (aptidão do round 008).
- Extração do pacote de suficiência causal (exame de elo + conector E) do M2 para módulo
  compartilhado, com a suíte do 005 continuando verde — refatoração coberta, não cópia.
- Casos de uso + adaptadores REST das promoções, semeaduras, derivações e dos três tipos
  de projeto; migrações Alembic com downgrade (papéis, fichas, pares, elipses, ramos,
  referências).
- Declaração e execução das 4 ações `toc.*` deste módulo (INT-05..INT-08) pela FSM do
  006, com prompts versionados no servidor.
- Interface React: canvas ARF/APR/AT, painel de ramos, tabela resumo, vista da cadeia —
  sobre o `ux-design.md` deste ciclo (as telas do M4 não estavam no protótipo do 002; o
  artefato nasce na abertura — plan, `ART:ux-design=yes`).
- Jornada viva (P6): a análise sintética completa da "Instituição Horizonte" — do UDE
  validado na ARA, pela promoção à NC e a injeção escolhida, à ARF com ramo negativo
  tratado, à APR sequenciada e à AT com o primeiro passo concluído — com captura gerada
  por script versionado do build real e avaliação heurística datada.
- Entradas de CHANGELOG; ADR novo se decisão material surgir (candidata: a extração do
  pacote de suficiência causal, se mudar contrato do M2).

## Critérios de aceite (DoD)

| # | Critério | Verificação executável |
|---|---|---|
| 1 | A cadeia inteira é percorrida por teste de domínio com dados sintéticos — UDE → NC → injeção → ARF → obstáculo → OI → passo — provando a referência de origem em cada elo (aptidão do round 008) | `pytest tests/domain/test_encadeamento.py -k cadeia_completa -v` — a saída nomeia os 6 elos e as referências conferidas |
| 2 | Referência cruzada só nasce por ação nomeada e sobrevive a exclusão suave como `pendente` | `pytest tests/domain/test_referencia_cruzada.py -v` — inclui o teste de propriedade da RNF-09 |
| 3 | Promoção exige UDE `Validado`; semeadura exige injeção `escolhida` | `pytest tests/domain/test_encadeamento.py -k "recusa" -v` — os dois casos de recusa mostrados |
| 4 | As três árvores exportam e importam ida-e-volta com referências (portão do round) | `pytest tests/integration/test_export_m4.py -v` — roundtrip para `arf`, `apr` e `at`, byte a byte no export duplo |
| 5 | Sequenciamento acíclico, em camadas, com elipses | `pytest tests/domain/test_sequenciamento.py -v` — inclui `-k ciclo` apontando dependência circular como bloqueante |
| 6 | Verificação da ARF pura e correta (cobertura, ED sem caminho, ramos abertos) | `pytest tests/domain/test_verificacao_arf.py -v` com rede desabilitada + `lint-imports` código 0 |
| 7 | Verbalização avaliada offline sobre corpus versionado | `pytest tests/domain/test_verbalizacao.py tests/domain/test_corpus_verbalizacao.py -v` — a saída diz quantos casos bons/maus examinou (R2) |
| 8 | Ramo negativo sem rota assistida (decisão do round) | `grep -rn "suggest_negative\|negative_branch" backend/src/ frontend/src/ \| wc -l` = 0 |
| 9 | Tripla do passo obrigatória; divergência esperado × real preservada | `pytest tests/domain/test_passo_transicao.py -v` |
| 10 | As 4 ações do M4 só mutam por `action_proposal` (fail-closed) | `pytest tests/integration/test_acoes_m4.py -v` — mutação direta recusada; aceite cria com traço correlacionado |
| 11 | Sem SDK, chave ou prompt no produto | `grep -rniE "genai\|openai\|anthropic\|api[_-]?key\|promptText\|system_prompt" backend/src/dominio/ frontend/src/ \| wc -l` = 0 |
| 12 | Telas do módulo registradas | `grep -c "toc\.arf_canvas\|toc\.apr_canvas\|toc\.apr_sequencia\|toc\.at_canvas\|toc\.cadeia" <registro de telas>` = 5 |
| 13 | Toda mutação nova com traço | `pytest tests/integration/test_traco_m4.py -v` — falha se `ReferenciaCriada`, `RamoNegativoTratado` ou `SequenciamentoGerado` não emitirem traço |
| 14 | Jornada viva da cadeia sintética | `ls docs/jornadas/` contém a jornada do M4 com capturas geradas por script; grep negativo de nome real de pessoa |
| 15 | Conformidade do ciclo | `scripts/check-conformance.sh 008` código 0 |
| 16 | Caminhos e links | `scripts/check-caminhos.sh` e `scripts/check-links.sh` código 0 + quanto examinaram |

## Fontes

F-01: /home/user/tocbuilderv3/components/Sidebar.tsx:55-58 — as três ferramentas como
botão cinza na 4ª geração (`grep -n "disabled: true" components/Sidebar.tsx` →
`55: … view: 'ARF', disabled: true },` · `56: … view: 'APR', disabled: true },` ·
`57: … view: 'AT', disabled: true },` · `58: … view: 'SNT_TREE', disabled: true },` — a
58 é a S&T, módulo M5) — o D-04 na fonte 🟢

F-02: /home/user/tocbuilderv3/types.ts:249-258 — o tipo-união `TocTool` inclui `'ARF' |
'APR' | 'AT'`: o **tipo de navegação** existia; nenhum tipo de dado, componente ou
prompt existiu para as três (ver F-05..F-07) 🟢

F-03: /home/user/tocbuilderv3/components/Sidebar.tsx:86-88 — `const
araProjectDependentViews: TocTool[] = ['ARF', 'APR', 'AT'];` seguido de
`itemIsDisabled = itemIsDisabled || !isProjectLoaded;` — a linhagem **declarou na
navegação** que as três dependem de uma ARA carregada, a intenção de encadeamento que
nunca chegou ao modelo de dados (F-08) 🟢

F-04: /home/user/tocbuilderv3/locales/pt.ts:68-70 e locales/en.ts:70-72 — os nomes:
"Árvore Realidade Futura (ARF)" / "Future Reality Tree (FRT)", "Árvore de Pré-Requisitos
(APR)" / "Prerequisite Tree (PRT)", "Árvore de Transição (AT)" / "Transition Tree (TT)"
— o vocabulário bilíngue desta spec vem da linhagem 🟢

F-05: /home/user/tocbuilderv3/components/ — zero componentes das três ferramentas:
`ls components/ | grep -icE "arf|apr|prereq|future|transition"` → `0` 🟢

F-06: /home/user/tocbuilderv3/constants.ts — nenhum dos 8 prompts da linhagem menciona
as três ferramentas: `grep -n "ARF" constants.ts` → 3 linhas (417, 422, 427), todas
listas de permissão de perfil (`permissions: ['ARA', 'SNT_TREE', 'NC', 'ARF', 'APR',
'AT', …]`) 🟢

F-07: /home/user/tocbuilderv3 — o domínio da APR e do ramo negativo tem **zero**
precedente: `grep -rniE "obstác|obstacle|objetivo intermediário|intermediate
objective|negative branch|ramo negativo" --include="*.ts" --include="*.tsx" . | grep -v
node_modules | wc -l` → `0` — tudo neste módulo é 🟡 por construção 🟢

F-08: [`../../docs/produto/visao.md`](../../docs/produto/visao.md) §6, D-04 e D-11 — e a
contagem reexecutada nesta spec: `grep -c
"araProjectId\|sourceUdeId\|linkedProject\|crossTool" types.ts` → `0` — nenhuma
referência cruzada entre projetos no modelo da 4ª geração; o E4.4 é a correção 🟢

F-09: skill toc-prt (sessão local), arquivo de referência prt-methodology.md — a fonte
técnica da APR: lógica de condição necessária, distinta da causa suficiente das árvores
de realidade (l.21); obstáculo como condição presente, não tarefa nem previsão
(l.36-42); OI como estado conquistado (l.53-60); teste IO-Obstáculo (l.72-79); elipses
de simultaneidade (l.111); construção em 10 passos de Dettmer e 4 de Scheinkopf
(l.83-101). Autoridades citadas pela skill: Dettmer, *The Logical Thinking Process*
(2007), cap. 7; Scheinkopf, *Thinking for a Change* (1999), cap. 10. A skill é a fonte
técnica; **esta spec é a norma** 🟢

F-10: [`../007-nuvem-de-conflito/spec.md`](../007-nuvem-de-conflito/spec.md) —
ReferenciaDeOrigem e ReferenciaDeSemeadura (§ Entidades e modelo de domínio) criadas
vazias no ciclo 007, e os INT-05/INT-06 de lá delegando a execução — promoção e
semeadura — a este ciclo; o status `escolhida` como o único que semeia (RN-08 de lá) 🟢

F-11: [`../005-arvore-da-realidade-atual/spec.md`](../005-arvore-da-realidade-atual/spec.md)
— o UDE `Validado` (FSM, RN-10 de lá) que a promoção exige, e o exame de elo + conector
E (E2.2) que a ARF reusa como pacote de suficiência causal; o Clarify 3 de lá já
antecipava que o ciclo 008 exigiria o conector E de qualquer forma 🟢

F-12: [`../../docs/produto/rounds.md`](../../docs/produto/rounds.md) — Round 008:
aptidão executável (teste de domínio que percorre a cadeia inteira e prova a referência
de origem em cada elo; as três árvores exportáveis pelo E1.4), fora (ramos negativos
assistidos), corte ("sai primeiro" a AT; "nunca sai" o encadeamento), defeitos D-04 e
D-11 🟢

F-13: [`../../docs/roadmap.md`](../../docs/roadmap.md) — Ciclo 008: os três portões
(cadeia, exportação, jornada) e as pré-condições — ciclos 005 e 007 promovidos, decisão
registrada sobre ramos negativos manuais nesta v1 🟢

F-14: [`../../docs/adr/0007-ia-somente-pela-fundacao.md`](../../docs/adr/0007-ia-somente-pela-fundacao.md)
— toda assistência via catálogo de ações governadas; prompts versionados no servidor 🟢

F-15: [`../../docs/governance/constitution.md`](../../docs/governance/constitution.md)
linhas 64-71 (alcance do P2) e 87-94 (item 8: manipulação direta aplica na hora sob três
testes; intenção inferida nasce proposta; FSM uma só e do servidor) 🟢

## Lacunas e assunções

L-01: As três ferramentas não têm **nenhum** precedente de implementação na linhagem
(F-05..F-07) — nem tela, nem tipo, nem prompt. Assunção: o método TOC via fonte técnica
(F-09) e a analogia estrutural com M2/M3 (nó tipado + ficha + função pura) bastam para a
primeira versão; onde o método admite variação, esta spec decide e declara — risco
**médio**.

L-02: As heurísticas de verbalização de obstáculo/OI (RF-20) não têm corpus prévio.
Assunção: a infraestrutura do M2 (léxico versionado + `indeterminado` honesto + corpus
sintético como função forçante) transfere para o vocabulário da APR; como aqui o aviso
não veta (RN-08), o custo do erro é menor que no M2 — risco **baixo**.

L-03: O apetite — três ferramentas novas + encadeamento + extração do pacote de
suficiência em um ciclo — é a maior aposta do roadmap depois do 003. Assunção: o corte
do round (sai primeiro a AT, que é o diagrama de menor risco; nunca sai o encadeamento)
absorve o estouro; se a AT sair, as derivações OI → AT (RF-40) saem junto e o RF-33
perde um tipo de vínculo — risco **alto**.

L-04: A extração do exame de elo + conector E do M2 para pacote compartilhado (RF-03)
refatora código promovido no ciclo 005. Assunção: a suíte do 005 é a rede de proteção
(entregável explícito: ela continua verde); se a extração ameaçar o apetite, a ARF
duplica temporariamente com dívida declarada em ADR — risco **médio**.

L-05: A vista da cadeia (RF-41) assume travessia linear UDE → … → passo, mas análises
reais podem ramificar (uma NC com duas injeções escolhidas semeando duas ARFs). Assunção:
a v1 apresenta a cadeia como grafo percorrido a partir do elemento de entrada, mostrando
ramificações como listas no elo — sem layout de grafo novo; se a jornada mostrar que não
basta, a evolução é de UI, não de modelo — risco **baixo**.

## Clarify

- [DÚVIDA] Semeadura (RF-38): uma injeção `escolhida` semeia no máximo **uma** ARF, ou o
  Product Steward quer permitir re-semear (cenários alternativos a partir da mesma
  injeção)? A spec assume uma por injeção, com re-semeadura exigindo nova escolha na NC.
- [DÚVIDA] Promoção (RF-36): a NC promovida aceita UDEs de **ARAs diferentes** do mesmo
  inquilino, ou a promoção é sempre de uma ARA só? A spec assume uma ARA por promoção —
  o dilema nasce de uma análise — mas o modelo de referência suportaria o contrário.
- [DÚVIDA] AT autônoma (RF-28): a AT pode nascer solta (sem OI de origem), ou toda AT
  deriva de uma APR? A spec assume que pode nascer solta — o método admite usá-la
  isolada — mas a Facilitadora pode preferir forçar a disciplina da cadeia.
- [DÚVIDA] Aceite de ramo negativo (RN-04): quem pode aceitar um ramo negativo — só a
  Gestora (é ela quem convive com o efeito colateral), ou também a Facilitadora TOC? A
  spec deixa a matriz papel × ação para o gate, junto com a herança do Clarify 5 do M2.
- [DÚVIDA] Objetivo da APR derivada (RF-39): o texto proposto vem do efeito/injeção
  escolhido pelo gesto — o Product Steward prefere que venha sempre vazio (forçar
  verbalização própria no presente), aceitando o risco de retrabalho de digitação?
