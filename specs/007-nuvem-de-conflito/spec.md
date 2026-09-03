# Spec 007 — Nuvem de Conflito (M3 — Nuvem de Conflito)

> Siglas: TOC — Teoria das Restrições · NC — Nuvem de Conflito (EC — *Evaporating
> Cloud*, "nuvem que evapora") · ARA — Árvore da Realidade Atual · UDE — Efeito
> Indesejável (*Undesirable Effect*) · ARF — Árvore da Realidade Futura · APH —
> Aplicação ↔ Harness · ADR — Architecture Decision Record (Registro de Decisão
> Arquitetural) · RF/RI/RNF/RN/INT — requisito funcional / de interface / não funcional
> / regra de negócio / integração · US — User Story (história de usuário) · DDD —
> Domain-Driven Design (Design Orientado a Domínio) · TDD — Test-Driven Development
> (desenvolvimento guiado por teste) · DoD — Definition of Done (Definição de Pronto) ·
> IA — inteligência artificial · FSM — máquina de estados finitos · OTel —
> OpenTelemetry · JSON — JavaScript Object Notation · i18n — internacionalização · UI —
> interface de usuário · TRIZ — Teoria da Resolução Inventiva de Problemas (do russo
> *Teoriya Resheniya Izobretatelskikh Zadach*) · SDK — Software Development Kit (kit de
> desenvolvimento) · API — Application Programming Interface (interface de programação)

- **Status**: Rascunho (aprovação: gate humano do ciclo 001)
- **Raia**: plena
- **Data**: 2026-09-03
- **Origem**: [`../../docs/produto/modulos.md`](../../docs/produto/modulos.md) (M3) ·
  [`../../docs/roadmap.md`](../../docs/roadmap.md) (ciclo 007) ·
  [`../../docs/produto/rounds.md`](../../docs/produto/rounds.md) (round 007)

## O quê e por quê

O M3 é a ferramenta TOC do **dilema**: a Nuvem de Conflito modela um conflito em 5
entidades — objetivo comum (A), duas necessidades (B e C) e duas ações mutuamente
exclusivas (D e D′) — ligadas por 7 arestas, cada aresta sustentada por **premissas**
explícitas, e as **injeções** que invalidam premissas são o que "evapora" o conflito. É
a única ferramenta em que a linhagem TOC-Builder entregou algo próximo do método
completo: a 3ª/4ª gerações tinham as 5 entidades e as 7 premissas como estrutura de dado
(F-01), a nuvem nascia inteira e nunca parcial (F-02), e a visão espelhada
conflito+solução existia (F-07).

O que justifica refazer está medido em três defeitos da mesma geração. Primeiro, **a
estrutura vinha de parse de markdown por expressão regular**: o modelo respondia texto
livre (F-04), e um parser com 5 extrações de entidade e 7 pares premissa/solução por
regex devolvia `null` inteiro a qualquer variação de formato (F-03) — o melhor recurso
da ferramenta quebrava pela forma da resposta, não pelo conteúdo. Segundo, a regra
inteira vivia num prompt de 75 linhas **no cliente** (F-05), servido pelo SDK com a
chave no navegador — o defeito D-01 que o ADR 0007 mata. Terceiro, a visão de solução
renderizava só 5 das 7 injeções: as das arestas D⇸C e D↯D′ — justamente a do conflito
central — nunca apareciam no diagrama (F-07).

Este ciclo entrega a NC com **modelagem manual completa e autônoma** (a nuvem funciona
inteira sem IA), geração assistida a partir de narrativa **pela fundação** — resultado
estruturado validado por schema, nascendo `action_proposal`, nunca parse de markdown — e
a visão conflito+solução com as 7 injeções cidadãs do modelo. No encadeamento TOC, a NC
recebe da ARA (M2) o dilema por trás de UDEs validados e entrega ao M4 a injeção que
semeia a ARF — as duas costuras nascem aqui como referência de primeira classe no
modelo e executam no ciclo 008 (INT-05, INT-06).

## O que entra como dado

- **Núcleo M1** ([`../004-nucleo-de-diagramas/spec.md`](../004-nucleo-de-diagramas/spec.md)):
  projeto, organização por tenant/usuário, exclusão suave, desfazer de sessão,
  exportação/importação. A NC é um **tipo de projeto** sobre esse núcleo — mas de
  **topologia fixa** (5 entidades, 7 arestas), não de grafo livre; o modelo de domínio
  declara a diferença. Extensão do
  [`../004-nucleo-de-diagramas/data-model.md`](../004-nucleo-de-diagramas/data-model.md).
- **Catálogo e FSM do ciclo 006**
  ([`../006-acoes-governadas-e-snapshot/spec.md`](../006-acoes-governadas-e-snapshot/spec.md)):
  o M3 vem **depois** do catálogo de propósito (decisão registrada em
  [`../../docs/produto/modulos.md`](../../docs/produto/modulos.md)) — entregar a geração
  assistida sem catálogo forçaria um SDK provisório (repetiria D-01) ou uma NC amputada.
  A FSM de proposta é **uma só e do servidor** (constituição, item 8 — F-12); este
  módulo é cliente dela, nunca dono.
- **Escopo do round 007** ([`../../docs/produto/rounds.md`](../../docs/produto/rounds.md)):
  E3.1–E3.4 completos; **fora**: semear a ARF a partir da injeção (encadeamento —
  round 008). Corte de apetite: sai primeiro a visão conflito+solução (fica a lista de
  injeções sobre o diagrama do conflito); **nunca saem** as premissas por aresta — nuvem
  sem premissa explícita é desenho de opinião.
- **IA somente pela fundação** (ADR 0007,
  [`../../docs/adr/0007-ia-somente-pela-fundacao.md`](../../docs/adr/0007-ia-somente-pela-fundacao.md)):
  nenhum SDK de provedor no produto; prompts versionados no servidor; toda assistência é
  ação do catálogo governado.
- **Método da ferramenta** (skill `toc-evaporating-cloud` — F-10): as regras de
  formulação (A ⊇ C ⊇ B; A, B, C como substantivos; D como infinitivo verbal; D′ como
  negação de D), a tabela de 7 premissas e as 5 separações TRIZ para o conflito D↯D′. A
  skill é a fonte técnica; **esta spec é a norma**.
- **Base sintética** (ADR 0006,
  [`../../docs/adr/0006-base-sintetica-desde-o-dia-1.md`](../../docs/adr/0006-base-sintetica-desde-o-dia-1.md)):
  todo exemplo usa a "Instituição Horizonte" e as personas fictícias.

## Épicos, features e user stories

### E3.1 — Modelagem do conflito (A, B, C, D, D′)

**F3.1.1 — Projeto NC de topologia fixa** — a nuvem nasce inteira: 5 entidades com
papéis nomeados e 7 arestas tipadas, desde o primeiro segundo (o acerto do v3 — F-02).

- US-01 — Como Facilitadora TOC, quero criar um projeto de Nuvem de Conflito e
  encontrar a estrutura completa esperando texto, para nunca montar topologia à mão.
  - Dado que crio o projeto NC "Dilema da expansão" na Instituição Horizonte, Quando o
    abro, Então vejo as 5 entidades com rótulo de papel (Objetivo Comum, Necessidade 1,
    Necessidade 2, Ação 1, Ação 2) e as 7 arestas na notação canônica — nenhuma entidade
    ou aresta pode ser criada nem excluída, só preenchida.
- US-02 — Como Gestora, quero listar, arquivar e restaurar projetos NC como qualquer
  projeto, para governar o acervo num lugar só.
  - Dado um projeto NC arquivado, Quando o restauro, Então volta com entidades,
    premissas e injeções intactas — a herança do M1 sem exceção.

**F3.1.2 — Edição direta e leitura por extenso** — cada entidade editável no próprio
diagrama (manipulação direta, item 8 da constituição); cada aresta legível em frase.

- US-03 — Como Participante, quero editar o texto de uma entidade clicando nela, para
  que a sessão de modelagem flua sem formulário no caminho.
  - Dado o nó B com o texto de exemplo, Quando o edito para "Receita nova no próximo
    semestre" e confirmo no próprio controle, Então aplica na hora com traço — alvo
    único e nomeado pelo gesto, valor no controle tocado, reversível na sessão.
- US-04 — Como Facilitadora TOC, quero ler cada aresta como frase ("Para ter A,
  precisamos de B"), para validar a lógica falando, do jeito que o método manda.
  - Dado a nuvem preenchida, Quando abro a ficha da aresta D′→C, Então leio "Para
    ter <texto de C>, devemos <texto de D′>" montada dos textos atuais.

**F3.1.3 — Apoio à boa formulação** — as regras da skill (substantivo em A/B/C,
infinitivo em D/D′, D′ nega D) como aviso heurístico não bloqueante.

- US-05 — Como Participante, quero um aviso quando formulo uma entidade fora da forma
  canônica, para aprender o método enquanto uso — sem ser travado por ele.
  - Dado que escrevo em D o texto "Qualidade" (substantivo, não ação), Quando salvo,
    Então o nó exibe o aviso "D pede uma ação (infinitivo verbal)" com exemplo — e o
    texto fica salvo mesmo assim.

### E3.2 — Premissas (7 arestas) e injeções

**F3.2.1 — Premissas por aresta** — toda aresta carrega as premissas que a sustentam;
premissa é dado de primeira classe, editável, nunca legenda decorativa.

- US-06 — Como Facilitadora TOC, quero registrar mais de uma premissa numa mesma
  aresta, para capturar tudo que o grupo acredita estar por trás dela.
  - Dado a aresta D↯D′, Quando adiciono as premissas "não há orçamento para as duas
    ações" e "as duas disputam a mesma equipe", Então as duas aparecem ordenadas na
    ficha da aresta e cada uma pode receber injeções próprias.
- US-07 — Como Participante, quero marcar uma premissa como desafiada com justificativa,
  para registrar onde o grupo já não acredita no que escreveu.
  - Dado uma premissa registrada, Quando a marco desafiada com o motivo, Então ela muda
    de aparência no diagrama e o evento guarda autor e justificativa.

**F3.2.2 — Injeções ligadas a premissas** — injeção referencia a premissa que invalida;
para o conflito D↯D′, as 5 separações TRIZ como classificação opcional.

- US-08 — Como Facilitadora TOC, quero criar uma injeção apontando a premissa que ela
  quebra, para que cada solução declare por que funciona.
  - Dado a premissa "não há orçamento para as duas ações", Quando registro a injeção
    "faseamento orçamentário condicionado a marco de receita", Então a injeção nasce
    ligada àquela premissa — e não existe caminho para injeção sem premissa.
- US-09 — Como Facilitadora TOC, quero classificar as injeções do conflito central por
  separação TRIZ (espaço, tempo, partes, grau, condição), para varrer o espaço de
  solução com método em vez de brainstorm solto.
  - Dado três injeções sobre premissas de D↯D′, Quando classifico uma como "separação no
    tempo", Então a visão de solução agrupa por separação e mostra quais das 5 ainda
    não foram tentadas.
- US-10 — Como Gestora, quero eleger a injeção que o grupo vai levar adiante, para que
  a decisão fique registrada e a ARF do ciclo 008 saiba de onde partir.
  - Dado injeções candidatas, Quando marco uma como escolhida com justificativa, Então
    o status muda com evento (autor, data) e a referência de semeadura fica pronta
    para o encadeamento (INT-06) — sem criar ARF nenhuma neste ciclo.

### E3.3 — Geração assistida a partir de narrativa

**F3.3.1 — `toc.generate_conflict_cloud` estruturada** — narrativa → nuvem completa
como resultado estruturado validado por schema, nascendo `action_proposal`. O
contraexemplo é o parser por regex do v3 (F-03): aqui a estrutura vem do contrato do
catálogo, não da forma do texto.

- US-11 — Como Facilitadora TOC, quero colar a narrativa de um dilema e receber a nuvem
  proposta inteira — entidades, premissas por aresta, injeções e racional — para
  revisar e aceitar, nunca para "acontecer".
  - Dado um projeto NC vazio e a capability de escrita presente, Quando envio a
    narrativa sintética do dilema da Instituição Horizonte por
    `toc.generate_conflict_cloud`, Então recebo **uma proposta pendente** com a nuvem
    completa em pré-visualização — nada aplicado —, e Quando aceito, Então o preenchimento
    aplica de uma vez com traço correlacionado à proposta.
- US-12 — Como Participante, quero recusar a proposta e ficar exatamente onde estava,
  para confiar que pedir ajuda não custa nada.
  - Dado a proposta pendente sobre um projeto com conteúdo manual, Quando recuso, Então
    o projeto permanece byte a byte intacto — o teste que o roadmap fixa como portão.

**F3.3.2 — Regeneração granular** — refinar uma parte (premissas de uma aresta,
injeções de uma premissa) sem tocar no resto.

- US-13 — Como Facilitadora TOC, quero pedir novas premissas só para a aresta D↯D′,
  para aprofundar o conflito central sem regenerar a nuvem que o grupo já validou.
  - Dado a nuvem preenchida, Quando aciono `toc.suggest_assumptions` sobre D↯D′, Então
    cada premissa sugerida chega como proposta individual — aceito duas, recuso uma, e
    as premissas existentes não mudam.

### E3.4 — Visão conflito+solução

**F3.4.1 — Visão espelhada** — o diagrama do conflito (premissas nas arestas) e o
diagrama de solução (injeções no lugar das premissas), mesma topologia, lado a lado ou
alternável — a boa ideia do v3 (F-07, F-09) sem o defeito das injeções invisíveis.

- US-14 — Como Gestora, quero ver problema e solução na mesma estrutura, para levar à
  reunião uma página que explica o dilema e o caminho de uma vez.
  - Dado a nuvem com injeções em todas as arestas, Quando abro a visão
    conflito+solução, Então as **7** posições do diagrama de solução mostram as
    injeções — inclusive D⇸C e D↯D′, as que o v3 nunca renderizou —, e clicar numa
    injeção foca a premissa correspondente no diagrama do conflito.
- US-15 — Como Facilitadora TOC, quero ver, na visão de solução, quais arestas ainda
  não têm injeção, para saber onde a análise ainda não terminou.
  - Dado 4 arestas com injeção e 3 sem, Quando abro a visão de solução, Então as 3
    posições vazias aparecem como pendência explícita, não como buraco.

## Entidades e modelo de domínio

DDD puro — domínio sem framework, sem rede, sem relógio (P3). O M3 **estende** o modelo
do M1 ([`../004-nucleo-de-diagramas/data-model.md`](../004-nucleo-de-diagramas/data-model.md))
por composição; o documento consolidado nasce na abertura do ciclo (T-02). A diferença
estrutural para a ARA: a NC **não é grafo livre** — é topologia fixa com papéis.

- **NuvemDeConflito** (agregado): o Projeto do M1 com `TipoDeFerramenta = nc` e a
  invariante central — **exatamente 5 entidades e 7 arestas, criadas na origem e
  indestrutíveis** (RN-01; o precedente é o helper do v3 — F-02). Carrega o **Racional**
  (texto livre que fundamenta por que B e C emergem da narrativa e por que A ⊇ C ⊇ B).
- **EntidadeDaNuvem** (entidade do agregado): `papel` fixo (`A` | `B` | `C` | `D` |
  `D_PRIME` — grafado `D_PRIME` no dado, `D′` na UI) + texto editável + avisos de
  formulação (resultado da heurística, RN-06). O papel nunca muda; o texto sim.
- **ArestaDaNuvem** (entidade do agregado): uma por chave — `A_B`, `A_C`, `B_D`,
  `C_D_PRIME`, `D_C`, `D_PRIME_B`, `D_D_PRIME` (F-01) — com `classe` derivada da chave:
  **necessidade** (B→A, C→A), **pré-requisito** (D→B, D′→C), **perigo** (D⇸C, D′⇸B),
  **conflito** (D↯D′). Carrega a lista ordenada de Premissas e a leitura por extenso.
- **Premissa** (entidade, dentro da aresta): texto + ordem + estado (`vigente` |
  `desafiada`, com justificativa) + autoria por evento. Premissas se acumulam e se
  editam; a geração assistida nunca as sobrescreve fora de proposta aceita (RN-05).
- **Injecao** (entidade do agregado): texto + **referência obrigatória a uma Premissa
  existente** (RN-04) + status (`candidata` | `escolhida` | `descartada`, FSM RN-08) +
  classificação TRIZ opcional (`espaco` | `tempo` | `partes` | `grau` | `condicao`) —
  válida para qualquer injeção, esperada nas do conflito D↯D′ (RN-07).
- **ReferenciaDeOrigem** (objeto de valor): a costura com o M2 — identificadores dos
  UDEs da ARA que motivaram esta nuvem (preenchida pela promoção do ciclo 008, INT-05;
  o campo existe desde já para o dado não nascer sem lugar).
- **ReferenciaDeSemeadura** (objeto de valor): a costura com o M4 — injeção `escolhida`
  + identificador da ARF semeada (preenchido no 008, INT-06).
- **ValidacaoDaNuvem** (serviço de domínio, função pura): completude (arestas com ≥ 1
  premissa vigente), avisos de formulação por entidade, pendências da visão de solução
  (arestas sem injeção). Não muta nada; sem rede e sem modelo.
- **ResultadoDeGeracao** (objeto de valor na borda da aplicação): a forma estruturada
  que `toc.generate_conflict_cloud` devolve — 5 textos de entidade, racional, premissas
  por chave de aresta, injeções por premissa — validada por schema JSON versionado
  (`contracts/`) **antes** de virar proposta. Nunca markdown, nunca regex (F-03).
- **Eventos de domínio** (somente-acréscimo, além dos do M1): `NuvemCriada`,
  `EntidadeEditada`, `RacionalEditado`, `PremissaRegistrada`, `PremissaEditada`,
  `PremissaDesafiada`, `PremissaArquivada`, `InjecaoRegistrada`, `InjecaoEditada`,
  `InjecaoReclassificada`, `StatusDeInjecaoMudou`, `GeracaoProposta`, `GeracaoAplicada`,
  `GeracaoRecusada`.
- **Fora do domínio**: prompts e provedores (servidor da fundação — ADR 0007); a FSM de
  `action_proposal` (uma só e do servidor — ciclo 006); o layout do diagrama
  (posições canônicas são preocupação da UI, RI-01).

## Requisitos funcionais

### Projeto NC de topologia fixa

RF-01: O SISTEMA DEVE permitir criar projeto do tipo NC, herdando do M1 listagem,
tenant/usuário, exclusão suave, restauração e exportação/importação sem
reimplementação. 🟡

RF-02: QUANDO um projeto NC for criado, O SISTEMA DEVE instanciar a nuvem completa — 5
entidades com papel fixo e texto de exemplo neutro, 7 arestas tipadas, racional vazio —
num único ato atômico; não existe nuvem parcial. [F-01, F-02] 🟡

RF-03: O SISTEMA DEVE recusar, no domínio, qualquer operação que crie ou exclua
entidade ou aresta da nuvem — o vocabulário de mutação é: editar texto, gerir premissa,
gerir injeção, editar racional (RN-01). 🟡

RF-04: QUANDO um projeto NC for excluído, O SISTEMA DEVE aplicar a exclusão suave do M1
arquivando premissas e injeções junto; a restauração devolve tudo. 🟡

### Edição direta e leitura por extenso

RF-05: O SISTEMA DEVE permitir editar o texto de cada entidade por manipulação direta
no diagrama e pela vista tabular, aplicando na hora com traço — os três testes do item
8 da constituição valem (alvo único nomeado pelo gesto, valor no controle tocado,
reversível na sessão). [F-12] 🟡

RF-06: O SISTEMA DEVE manter o racional do conflito como texto editável do agregado,
com evento próprio (`RacionalEditado`). [F-01] 🟡

RF-07: O SISTEMA DEVE apresentar a leitura por extenso de cada aresta, montada dos
textos atuais das entidades: necessidade ("Para ter <A>, precisamos de <B>"),
pré-requisito ("Para ter <B>, devemos <D>"), perigo ("<D> ameaça <C>") e conflito
("<D> e <D′> não podem coexistir"). [F-10] 🟡

RF-08: O SISTEMA DEVE cobrir a edição de entidade, premissa e injeção pelo desfazer de
sessão herdado do M1, sem exceção nova. 🟡

### Apoio à boa formulação

RF-09: O SISTEMA DEVE avaliar, por heurística pura de domínio (sem rede e sem modelo),
a forma canônica de cada entidade — A, B, C como substantivo (adjetivo opcional); D e
D′ como infinitivo verbal — devolvendo aviso com explicação e exemplo, nunca bloqueio
(RN-06). [F-10] 🟡

RF-10: O SISTEMA DEVE avaliar, por heurística, se D′ nega ou exclui D (marcadores de
negação e antonímia simples), devolvendo `indeterminado` honesto quando não alcançar o
caso — indeterminado não gera aviso. [F-10] 🟡

RF-11: O SISTEMA DEVE manter o léxico dessas heurísticas como dado versionado por
idioma (pt/en), compartilhando o mecanismo do léxico do M2 — nunca literal espalhado no
código. 🟡

### Premissas por aresta

RF-12: O SISTEMA DEVE permitir registrar, editar, reordenar e arquivar premissas em
qualquer uma das 7 arestas — zero ou mais por aresta, ordenadas —, cada mutação com
evento e autor. [F-01, F-10] 🟡

RF-13: O SISTEMA DEVE permitir marcar uma premissa como `desafiada` com justificativa
obrigatória, e reverter para `vigente` — os dois sentidos com evento. 🟡

RF-14: O SISTEMA DEVE computar a completude da nuvem por função pura: quantas das 7
arestas têm ≥ 1 premissa vigente — e apresentar o resultado como progresso, não como
trava (RN-03). 🟡

RF-15: QUANDO uma premissa for arquivada, O SISTEMA DEVE arquivar junto as injeções que
a referenciam, dizendo quantas no ato de confirmar — nunca deixar injeção órfã nem
apagar em silêncio (RN-04). 🟡

### Injeções ligadas a premissas

RF-16: O SISTEMA DEVE exigir, no domínio, que toda injeção referencie exatamente uma
premissa existente e não arquivada do mesmo projeto — não existe construtor de injeção
sem premissa (RN-04). [F-01] 🟡

RF-17: O SISTEMA DEVE manter o status da injeção na FSM `candidata → escolhida |
descartada`, com retorno explícito a `candidata` mediante justificativa (RN-08); a
mudança registra autor e data por evento. 🟡

RF-18: O SISTEMA DEVE permitir classificar qualquer injeção por separação TRIZ
(`espaco` | `tempo` | `partes` | `grau` | `condicao`), e DEVE apresentar, para o
conflito D↯D′, quais das 5 separações ainda não têm injeção (RN-07). [F-10] 🟡

RF-19: O SISTEMA DEVE listar injeções por aresta e por premissa, com filtro por status
e por separação TRIZ, no diagrama e na vista tabular. 🟡

RF-20: QUANDO uma injeção for marcada `escolhida`, O SISTEMA DEVE registrar a
ReferenciaDeSemeadura vazia de destino — pronta para a ARF do ciclo 008 preencher
(INT-06) — sem criar nenhuma árvore neste ciclo. 🟡

### Geração assistida a partir de narrativa

RF-21: O SISTEMA DEVE expor `toc.generate_conflict_cloud` no catálogo governado:
entrada é a narrativa (texto livre) mais o estado atual da nuvem; saída é
ResultadoDeGeracao **estruturado e validado por schema JSON versionado** — nunca
markdown interpretado por parser (o contraexemplo: F-03, F-04). [F-05, F-06] 🟡

RF-22: QUANDO o resultado da geração chegar, O SISTEMA DEVE validá-lo contra o schema
**antes** de criar a proposta; resultado que não valida é recusado em falha fechada com
erro legível e identificador de traço — nada aplicado, nada meio-aplicado (RN-05). 🟡

RF-23: O SISTEMA DEVE fazer toda aplicação de geração nascer `action_proposal` na FSM
do servidor (ciclo 006): sobre nuvem vazia, uma proposta de preenchimento completo;
sobre nuvem com conteúdo, propostas granulares por seção — nunca sobrescrita direta.
[F-12] 🟡

RF-24: O SISTEMA DEVE garantir que recusar uma proposta de geração deixa o projeto
byte a byte intacto — provado por teste que compara o estado serializado antes e depois
da recusa (o portão executável do roadmap, ciclo 007). 🟡

RF-25: QUANDO uma proposta de geração for aceita, O SISTEMA DEVE aplicar as mutações
com traço correlacionado ao identificador da proposta, e os eventos resultantes DEVEM
declarar a origem (`geracao`, com a proposta) — distinguível de edição humana para
sempre. 🟡

RF-26: O SISTEMA DEVE expor `toc.suggest_assumptions` (premissas para uma aresta
nomeada) e `toc.suggest_injections` (injeções para uma premissa nomeada) como ações de
regeneração granular, cada sugestão nascendo proposta individual. 🟡

RF-27: QUANDO a capability de escrita não estiver presente na introspecção, O SISTEMA
DEVE omitir do catálogo as três ações mutadoras deste módulo, mantendo o restante da
NC funcional — a lição paga pela irmã, já portão do ciclo 006. 🟡

RF-28: O SISTEMA DEVE funcionar por inteiro nos épicos E3.1, E3.2 e E3.4 com o catálogo
ausente ou desligado — a modelagem manual é completa e a assistência é aceleradora,
nunca dependência. 🟡

RF-29: O SISTEMA DEVE versionar o schema do ResultadoDeGeracao em `contracts/` e
recusar resultado de versão desconhecida — a evolução do schema é mudança de contrato,
com teste, nunca afrouxamento do parse. 🟡

### Visão conflito+solução

RF-30: O SISTEMA DEVE apresentar a visão espelhada: diagrama do conflito (premissas por
aresta) e diagrama de solução (injeções por aresta) sobre a mesma topologia, alternável
e lado a lado. [F-07, F-09] 🟡

RF-31: O SISTEMA DEVE representar, na visão de solução, **as 7 posições de aresta** —
com as injeções existentes ou a pendência explícita — incluindo D⇸C e D↯D′, as duas que
o v3 nunca renderizou (F-07). 🟡

RF-32: O SISTEMA DEVE oferecer foco cruzado: selecionar uma injeção na visão de solução
foca a premissa referenciada no diagrama do conflito, e vice-versa. 🟡

RF-33: O SISTEMA DEVE exportar e importar o projeto NC completo pelo E1.4 do M1 —
entidades, arestas, premissas (com estado), injeções (com status, TRIZ e referências),
racional e referências de origem/semeadura — sem perda em ida e volta. 🟡

RF-34: O SISTEMA DEVE apresentar na vista tabular do projeto a matriz aresta × premissas
× injeções — a "tabela de premissas" e a "tabela de soluções" do método (F-10) como
projeções do mesmo dado do diagrama, nunca de dado paralelo. 🟡

## Requisitos de interface

RI-01: O diagrama da NC usa o layout canônico da ferramenta — A à esquerda, B/C ao
centro, D/D′ à direita, conflito marcado entre D e D′ — com posições fixas: o usuário
edita texto, não arruma caixas. [F-08] 🟡

RI-02: A notação das arestas segue o método: setas de necessidade/pré-requisito
cheias, setas de perigo (D⇸C, D′⇸B) tracejadas e distinguíveis também por rótulo textual
(nunca só cor ou só traço), e o conflito D↯D′ com o símbolo de raio. [F-03, F-10] 🟡

RI-03: As premissas de uma aresta são acionáveis na própria aresta (legenda clicável —
o acerto do v3, F-08) e abrem a ficha da aresta com premissas e injeções juntas. 🟡

RI-04: A ficha da aresta apresenta a leitura por extenso (RF-07) no topo, as premissas
ordenadas com estado, e as injeções agrupadas por premissa — uma superfície, três
camadas. 🟡

RI-05: O aviso de formulação (RF-09, RF-10) aparece no próprio nó, com explicação e
exemplo ao abrir — pedagógico, não punitivo; some quando o texto muda para forma
canônica. 🟡

RI-06: A proposta de geração apresenta pré-visualização completa em diff — o que cada
entidade/aresta ganha — antes de aceitar; aceitar e recusar são ações de mesmo peso
visual. 🟡

RI-07: A bandeja de propostas é a mesma do ciclo 006 (uma bandeja por aplicação, nunca
uma por módulo), dizendo de qual ação e proposta cada item veio. 🟡

RI-08: A visão conflito+solução alterna por controle persistente na sessão; em tela
larga, lado a lado com rolagem sincronizada; a pendência de injeção (RF-31) tem
representação própria acessível. 🟡

RI-09: O progresso de completude (RF-14) aparece no cabeçalho do projeto — "5 de 7
arestas com premissa" — com salto direto para as arestas pendentes. 🟡

RI-10: A vista tabular (RF-34) permite edição das premissas e injeções com paridade de
capacidade com o diagrama — sessão de grupo flui na tabela, revisão flui no diagrama. 🟡

RI-11: Toda superfície do módulo respeita tema do hospedeiro com fallback, modo
só-conteúdo e operação por teclado, herdados dos ciclos 002/003; textos por i18n pt/en,
inclusive rótulos de papel, avisos de formulação e nomes das separações TRIZ. 🟡

## Requisitos não funcionais

RNF-01: As invariantes da nuvem (5 entidades, 7 arestas, injeção referencia premissa) e
a ValidacaoDaNuvem são domínio puro testável sem rede, sem banco e sem modelo — a suíte
de domínio roda offline por construção (P3, P4; aptidão do round 007). 🟡

RNF-02: A fronteira hexagonal é verificada por `import-linter`: o pacote de domínio do
M3 não importa framework, HTTP, banco nem cliente de IA — o build falha na violação. 🟡

RNF-03: Toda mutação do módulo emite traço OTel correlacionado e log estruturado;
mutações originadas de proposta aceita carregam o identificador da proposta (P5,
RF-25). 🟡

RNF-04: O schema do ResultadoDeGeracao é validado no **servidor** da aplicação antes da
criação da proposta; o cliente nunca é a única linha de validação (P7). 🟡

RNF-05: Abrir um projeto NC completo (7 arestas, até 30 premissas e 50 injeções)
renderiza em menos de 1 segundo no percentil 95, medido na jornada viva. 🟡

RNF-06: A recusa de proposta responde em menos de 500 milissegundos e não gera nenhuma
escrita no agregado — só o evento `GeracaoRecusada` no registro de propostas. 🟡

RNF-07: Nenhum prompt, chave ou cliente de provedor no repositório do produto — grep de
CI herdado dos ciclos anteriores cobrindo também os padrões do v3
(`CONFLICT_CLOUD_PROMPT`, `GoogleGenAI`) (P7, ADR 0007; contraexemplos: F-04, F-05). 🟡

RNF-08: O léxico das heurísticas de formulação (RF-11) tem corpus sintético próprio de
entidades bem e mal formuladas, versionado pt/en — ampliar heurística exige ampliar
corpus (o mecanismo do M2, reusado). 🟡

RNF-09: Textos de papel, aviso, separação TRIZ e leitura por extenso saem do mecanismo
de i18n com chave estável ligada à regra (RN-NN) — rastreabilidade spec ↔ código ↔
tela. 🟡

RNF-10: A fixture de demonstração e a jornada usam exclusivamente o dilema sintético da
"Instituição Horizonte" — grep negativo de nome real de pessoa no CI (ADR 0006). 🟡

## Regras de negócio

RN-01: A nuvem tem **exatamente** 5 entidades (A, B, C, D, D′) e 7 arestas (A_B, A_C,
B_D, C_D_PRIME, D_C, D_PRIME_B, D_D_PRIME); nascem juntas e não se criam nem se
destroem — só se preenchem. [F-01, F-02] 🟢 (estrutura verbatim em `types.ts:69` e
`types.ts:73`; criação atômica em `mockApiService.ts:17-41`)

RN-02: As arestas têm classe derivada da chave: necessidade (B→A, C→A), pré-requisito
(D→B, D′→C), perigo (D⇸C, D′⇸B), conflito (D↯D′) — e a leitura por extenso de cada
classe é fixa (RF-07). [F-03, F-10] 🟢 (a notação ⇸ e ↯ está na linhagem:
`parserService.ts:51-53`; a semântica é do método — skill, 🟡 na heurística)

RN-03: Nuvem **modelada** é nuvem com as 7 arestas sustentadas por ≥ 1 premissa
vigente; a completude informa e prioriza, nunca trava a edição — nuvem sem premissa
explícita é desenho de opinião (round 007: "nunca sai"). [F-11] 🟡

RN-04: Injeção sem premissa não existe: toda injeção referencia exatamente uma premissa
existente e não arquivada do mesmo projeto; arquivar a premissa arquiva as injeções
junto, com aviso quantificado. [F-01] 🟢 (o dado da linhagem já pareava premissa e
solução por aresta: `types.ts:72-76`; a referência explícita e o arquivamento são 🟡)

RN-05: Conteúdo produzido por modelo só entra no agregado por proposta aceita na FSM do
servidor; resultado que não valida contra o schema é recusado em falha fechada antes de
virar proposta. [F-12] 🟡

RN-06: A forma canônica das entidades — A, B, C substantivo com adjetivo opcional; D e
D′ infinitivo verbal; D′ nega ou exclui D — é **aviso** heurístico, nunca bloqueio: o
método educa, o dado obedece ao grupo. [F-10] 🟡

RN-07: As 5 separações TRIZ (espaço, tempo, partes, grau, condição) são o mapa de
cobertura do conflito D↯D′: o sistema mostra quais faltam, o humano decide se importa.
[F-10] 🟡

RN-08: Status de injeção segue a FSM `candidata → escolhida | descartada`, com retorno
a `candidata` mediante justificativa; `escolhida` é a única que semeia ARF (ciclo 008),
e mais de uma injeção pode ser `escolhida`. 🟡

## Integrações

INT-01: O M3 consome do M1 (ciclo 004) projeto, tenant/usuário, exclusão suave,
desfazer, exportação/importação e vista tabular; consome da junta 003 identidade
(`POST /auth/introspect`), isolamento por inquilino e OTel. Nada disso é
reimplementado. 🟡

INT-02: `toc.generate_conflict_cloud` — catálogo `toc.*`, mutadora (preenche a nuvem);
entrada: narrativa + estado atual da nuvem; saída: ResultadoDeGeracao validado por
schema (RF-21..RF-25); toda aplicação nasce `action_proposal` na FSM do ciclo 006.
[F-05, F-06] 🟡

INT-03: `toc.suggest_assumptions` — mutadora granular; entrada: chave da aresta +
contexto da nuvem; saída: propostas de premissa, uma `action_proposal` por sugestão
(RF-26). 🟡

INT-04: `toc.suggest_injections` — mutadora granular; entrada: identificador da
premissa + contexto; saída: propostas de injeção ligadas àquela premissa, com separação
TRIZ sugerida quando couber (RF-26). 🟡

INT-05: **Costura com o M2** (execução: ciclo 008, E4.4): promover o dilema por trás de
UDEs validados da ARA para um projeto NC novo, preenchendo a ReferenciaDeOrigem. Este
ciclo entrega o campo e a leitura ("origem: UDEs …" quando houver); a ação de promover
é do 008. [ver `../../docs/produto/rounds.md`, round 008] 🟡

INT-06: **Costura com o M4** (execução: ciclo 008, E4.4): a injeção `escolhida` semeia
a ARF, preenchendo a ReferenciaDeSemeadura. Este ciclo entrega o status `escolhida`
(RF-20) e o campo de referência; criar ARF é do 008. 🟡

INT-07: Telas deste módulo entram no registro de telas do E7.5 com identificador
estável (`toc.nc_canvas`, `toc.nc_aresta`, `toc.nc_solucao`, `toc.nc_tabela`), no
formato do ciclo 006; texto de entidade, premissa, injeção e racional marcam
`ai_visible` campo a campo para o snapshot sanitizado — narrativa colada pelo usuário é
sempre camada não-confiável (item 7 da constituição). 🟡

INT-08: Os prompts das três ações são versionados **no servidor** e nunca circulam no
cliente nem no snapshot (ADR 0007); o prompt de 75 linhas do cliente do v3 (F-05) **não
é portado** — a lógica dele vira contrato de schema e regra desta spec. 🟡

## Telas e fluxos

### 6.1 Canvas da NC — Job: preencher o dilema na estrutura canônica · Campos: 5
entidades com papel e aviso de formulação, 7 arestas com notação e contagem de
premissas, racional · Ações: editar entidade (direta), editar racional, abrir ficha de
aresta, alternar para visão de solução.

### 6.2 Ficha de aresta — Job: sustentar a aresta com premissas e atacá-las com
injeções · Campos: leitura por extenso, premissas ordenadas com estado, injeções por
premissa com status e TRIZ · Ações: registrar/editar/reordenar/arquivar premissa,
desafiar premissa, registrar injeção, mudar status, classificar TRIZ.

### 6.3 Geração a partir de narrativa — Job: transformar a história do dilema em nuvem
proposta · Campos: narrativa, pré-visualização em diff da proposta · Ações: gerar
(`toc.generate_conflict_cloud`), aceitar, recusar, regenerar seção
(`toc.suggest_assumptions`, `toc.suggest_injections`).

### 6.4 Visão conflito+solução — Job: ver problema e caminho na mesma estrutura ·
Campos: os dois diagramas espelhados, 7 posições de injeção (com pendência explícita),
cobertura TRIZ do conflito · Ações: alternar/lado a lado, foco cruzado
injeção ↔ premissa, filtrar por status.

### 6.5 Vista tabular — Job: sessão de grupo sem canvas · Campos: matriz aresta ×
premissas × injeções, progresso de completude · Ações: as mesmas da ficha de aresta,
em tabela (paridade RI-10).

## Fora de escopo

- **Semear a ARF a partir da injeção escolhida** — a costura existe como dado nesta spec
  (INT-06, com ReferenciaDeSemeadura criada vazia), mas a **execução é do ciclo 008**,
  no épico do encadeamento; o mesmo vale para promover o UDE da ARA para cá (INT-05). O
  *Fora* do round 007 diz exatamente isto
  ([`../../docs/produto/rounds.md`](../../docs/produto/rounds.md)).
- **Gerar a nuvem a partir de áudio ou transcrição de reunião** — a entrada da geração
  assistida deste ciclo é **narrativa em texto**. Áudio traria captura, transcrição e
  consentimento de gravação, que são um módulo, não um parâmetro: decisão nova.
- **Montar a nuvem por análise de texto livre da resposta do modelo** — não é corte de
  apetite, é defeito medido que não atravessa: o parser por expressão regular da linhagem
  devolvia `null` inteiro a qualquer variação de formato (F-03, F-04). Aqui a ação devolve
  resultado estruturado validado por schema, ou recusa.
- **Biblioteca de nuvens prontas ou catálogo de conflitos genéricos** — nenhuma geração da
  linhagem esboçou isso e não há demanda medida; incluir modelos de conflito é decisão
  nova, e ela colide com a regra de que a nuvem é do dilema de quem a escreve.
- **Derivar injeções automaticamente das cinco separações TRIZ** — a skill
  `toc-evaporating-cloud` é fonte técnica de **apoio à formulação** (F-10), e é assim que
  entra: as separações orientam a pessoa. Transformá-las em gerador é decisão nova.
- **Qualquer chamada a provedor de modelo a partir do navegador** — o prompt de 75 linhas
  no cliente, servido pelo SDK com a chave no navegador, é o defeito D-01 que o ADR 0007
  mata ([`../../docs/adr/0007-ia-somente-pela-fundacao.md`](../../docs/adr/0007-ia-somente-pela-fundacao.md));
  a geração assistida passa pelo catálogo do ciclo 006.

## Entregáveis

- Domínio Python puro do M3: agregado NuvemDeConflito com topologia fixa, Premissa,
  Injecao com FSM de status, ValidacaoDaNuvem, heurísticas de formulação com léxico
  pt/en — testes de domínio **sem rede e sem modelo** nascidos antes do código (P4),
  sobre fixture sintética da "Instituição Horizonte".
- Schema JSON versionado do ResultadoDeGeracao + declaração das 3 ações `toc.*` deste
  módulo no formato do catálogo do ciclo 006 (`contracts/`).
- Casos de uso + adaptadores REST; integração com a FSM de proposta do 006 (cliente,
  nunca dono); migrações Alembic com downgrade (nuvem, premissa, injeção, referências).
- Interface React: canvas da NC, ficha de aresta, fluxo de geração com diff, visão
  conflito+solução, vista tabular — sobre o `ux-design.md` do ciclo 002.
- Jornada viva (P6): o dilema sintético da Instituição Horizonte de ponta a ponta —
  narrativa → proposta → recusa → nova proposta → aceite → premissas desafiadas →
  injeções TRIZ → injeção escolhida — com captura gerada por script versionado do build
  real e avaliação heurística datada.
- Entradas de CHANGELOG; ADR novo se decisão material surgir (candidata: granularidade
  da proposta de geração — ver Clarify).

## Critérios de aceite (DoD)

| # | Critério | Verificação executável |
|---|---|---|
| 1 | Invariantes da nuvem no domínio puro, offline | `pytest tests/domain/test_nuvem_invariantes.py -p no:cacheprovider` verde com rede desabilitada + `lint-imports` código 0 |
| 2 | 5 entidades e 7 arestas indestrutíveis (RN-01) | `pytest tests/domain/test_nuvem_invariantes.py -k "topologia" -v` — criação atômica; criar/excluir entidade ou aresta recusado |
| 3 | Injeção sempre referencia premissa (RN-04) | `pytest tests/domain/test_injecao.py -v` — sem premissa recusa; arquivar premissa arquiva injeções com contagem |
| 4 | FSM de status de injeção (RN-08) | `pytest tests/domain/test_injecao.py -k fsm` — retorno a candidata exige justificativa |
| 5 | Recusar geração deixa o projeto intacto (RF-24) | `pytest tests/application/test_geracao_proposta.py -k recusa -v` — estado serializado idêntico byte a byte antes/depois |
| 6 | Resultado fora do schema é recusado em falha fechada (RF-22) | `pytest tests/application/test_geracao_proposta.py -k schema -v` — casos: campo faltante, aresta desconhecida, versão desconhecida |
| 7 | Nenhum parse de markdown no caminho da geração | `grep -rn "parseConflictCloudMarkdown\|markdown" backend/src/dominio/ backend/src/aplicacao/ \| wc -l` = 0 |
| 8 | Heurísticas de formulação com corpus | `pytest tests/domain/test_formulacao.py -v` — a saída diz quantos casos bons/maus examinou (R2) |
| 9 | Visão de solução cobre as 7 arestas (RF-31) | `pytest tests/ui/test_visao_solucao.py -v` — 7 posições renderizadas, incluindo D_C e D_D_PRIME (o defeito do v3 como caso de teste) |
| 10 | Exportação sem perda (RF-33) | `pytest tests/application/test_export_nc.py -k "ida_e_volta"` — export → import → igualdade estrutural |
| 11 | Toda mutação nova com traço | `pytest tests/integration/test_traco_m3.py` — falha se `PremissaRegistrada`, `InjecaoRegistrada`, `GeracaoAplicada` não emitirem traço |
| 12 | Sem SDK, chave ou prompt no produto | `grep -rniE "genai\|openai\|anthropic\|api[_-]?key\|CONFLICT_CLOUD_PROMPT" backend/ frontend/src/ \| wc -l` = 0 |
| 13 | Capability ausente esconde as 3 mutadoras (RF-27) | `pytest tests/integration/test_catalogo_m3.py -k capability -v` |
| 14 | Jornada viva do dilema sintético | `ls docs/jornadas/` contém a jornada do M3 com capturas geradas por script; grep negativo de nome real de pessoa |
| 15 | Conformidade do ciclo | `scripts/check-conformance.sh 007` código 0 |
| 16 | Caminhos e links | `scripts/check-caminhos.sh` e `scripts/check-links.sh` código 0 + quanto examinaram |

## Fontes

F-01: /home/user/tocbuilderv3/types.ts:68-93 — a estrutura da NC na linhagem: 5
entidades (`sed -n 69p types.ts | grep -o "'[A-Z_']*'" | wc -l` → `5`: `'A' | 'B' |
'C' | 'D' | 'D_PRIME'`), 7 chaves de premissa (`sed -n 73p types.ts | grep -o
"'[A-Z_']*'" | wc -l` → `7`: `'A_B' | 'A_C' | 'B_D' | 'C_D_PRIME' | 'D_C' |
'D_PRIME_B' | 'D_D_PRIME'`), premissa e solução pareadas por aresta (l.72-76), racional
opcional (l.92) 🟢

F-02: /home/user/tocbuilderv3/services/mockApiService.ts:17-41 — o helper
`createEmptyConflictCloudData` cria a nuvem **inteira** na origem: 5 entidades com
texto de exemplo e as 7 premissas vazias (`sed -n '31,39p' services/mockApiService.ts |
grep -c "emptyAssumption("` → `7`) — o acerto que a RN-01 formaliza 🟢

F-03: /home/user/tocbuilderv3/services/parserService.ts — o contraexemplo da geração: 5
extrações de entidade (`grep -c "getEntity(" services/parserService.ts` → `5`) e 7
pares premissa/solução (`grep -c "getAssumptionAndSolution('" services/parserService.ts`
→ `7`) arrancados de markdown por regex; qualquer variação de formato devolve `null`
inteiro (l.67) — a estrutura dependia da **forma** do texto do modelo; a notação ⇸/↯
das arestas de perigo e conflito está nas l.51-53 🟢

F-04: /home/user/tocbuilderv3/services/geminiService.ts:173 — `if (request.type ===
'generate_conflict_cloud') return { markdown: textResponse };` — a geração devolvia
markdown cru, sem contrato; e a l.16 inicializa o SDK com a chave **no navegador**
(`const ai = new GoogleGenAI({ apiKey: process.env.API_KEY });`) — os dois defeitos que
RF-21/RF-22 e o ADR 0007 matam 🟢

F-05: /home/user/tocbuilderv3/constants.ts:264-338 — `CONFLICT_CLOUD_PROMPT_TEXT`: 75
linhas (`expr 338 - 264 + 1` → `75`) de regra da ferramenta — papéis, premissas,
separações TRIZ — vivendo como prompt no cliente; a lógica vira contrato e regra desta
spec, o texto que sobrar é insumo do servidor (INT-08) 🟢

F-06: /home/user/tocbuilderv3/types.ts:137 — `'generate_conflict_cloud'` é a 7ª
operação do tipo-união de assistência da linhagem (as outras 6 são da ARA — spec 005,
F-03 de lá); vira a INT-02 governada 🟢

F-07: /home/user/tocbuilderv3/components/ConflictCloudView.tsx:40,159-169 — a visão
espelhada existia (`Y_OFFSET_SOLUTION = 950`, l.40; nós `SolNode*` l.159-163), mas o
diagrama de solução renderizava só **5** nós de injeção (`sed -n '164,185p'
components/ConflictCloudView.tsx | grep -c "Injection"` → `5`) e `D_C.solution` /
`D_D_PRIME.solution` não são renderizadas em lugar nenhum (`grep -n
"D_D_PRIME.solution\|D_C.solution" components/ConflictCloudView.tsx` → vazio) — o
defeito que o RF-31 e a DoD 9 transformam em caso de teste 🟢

F-08: /home/user/tocbuilderv3/specs/feat_conflict_cloud.md:15-25 — os 10 critérios de
aceitação da 4ª geração (`sed -n '15,26p' specs/feat_conflict_cloud.md | grep -c
'^[0-9]'` → `10`): layout fixo, legendas de premissa clicáveis, símbolo de conflito —
os acertos de UI que RI-01..RI-03 herdam 🟢

F-09: /home/user/tocbuilderv3/specs/feat_conflict_cloud_refactor.md:20-23 — a visão
dupla (diagrama do conflito com arestas de perigo + diagrama de solução com injeções) e
a persistência por projeto — o desenho que o E3.4 refaz por cima de dado íntegro 🟢

F-10: skill `toc-evaporating-cloud` (sessão local) — o método da ferramenta: regras de
formulação (A ⊇ C ⊇ B; A, B, C substantivo único com adjetivo opcional; D infinitivo
verbal; D′ = "Não {D}"), a tabela das 7 premissas com a leitura de cada seta, e as 5
separações TRIZ (espaço, tempo, partes, grau, condição) para D↯D′ — fonte técnica; a
norma é esta spec 🟢

F-11: [`../../docs/produto/rounds.md`](../../docs/produto/rounds.md) — Round 007:
aptidão executável (invariantes por teste de domínio; recusa deixa intacto; jornada
sintética), fora (semear ARF — round 008), corte de apetite ("sai primeiro" E3.4,
"nunca saem" as premissas) 🟢

F-12: [`../../docs/governance/constitution.md`](../../docs/governance/constitution.md)
linhas 73-94 — itens 4 (verbo mutador nasce proposta, fail-closed), 7 (tela é dado) e 8
(manipulação direta aplica na hora sob três testes; intenção inferida nasce proposta;
FSM uma só e do servidor) 🟢

## Lacunas e assunções

L-01: A multiplicidade de premissas por aresta não tem precedente na linhagem (o v3
fixava exatamente 1 — F-01) nem na skill (que pede 1 por seta). Assunção: zero ou mais,
ordenadas, com a completude medindo ≥ 1 vigente (RN-03) — a prática de grupo produz
várias crenças por seta e achatá-las perderia informação; risco **baixo** (voltar a 1 é
restrição de dado, não migração).

L-02: A granularidade da proposta de geração (RF-23: completa sobre nuvem vazia,
granular sobre nuvem preenchida) é desenho nosso sem precedente — o v3 sempre
sobrescrevia tudo. Assunção: o corte "vazia × preenchida" cobre os dois usos reais
(começar e refinar); o caso híbrido resolve-se com as ações granulares (INT-03,
INT-04) — risco **médio**.

L-03: O contrato das 3 ações e do schema antecipa o formato que o ciclo 006 fixa para o
catálogo. Assunção: declarar com schema versionado custa pouco e dá ao 006 um segundo
cliente concreto; divergência custa migração de contrato, não de domínio — risco
**baixo**.

L-04: As heurísticas de formulação (RF-09, RF-10) não têm precedente medido — a
linhagem mandava tudo ao modelo. Assunção: aviso não bloqueante com `indeterminado`
honesto não pode causar dano de fluxo (o pior caso é silêncio); o corpus sintético
(RNF-08) mede o acerto — risco **baixo**.

L-05: Os campos ReferenciaDeOrigem e ReferenciaDeSemeadura nascem aqui mas só são
preenchidos pelo encadeamento do ciclo 008 — desenho antecipado sem consumidor
imediato. Assunção: criar o lugar do dado agora evita migração no 008 e custa duas
colunas anuláveis; se o desenho do encadeamento divergir, a migração é pequena e o
dado ainda é nulo — risco **baixo**.

## Clarify

- [DÚVIDA] Premissas por aresta (L-01): o Product Steward confirma múltiplas premissas
  ordenadas por aresta, ou prefere a forma estrita da skill (exatamente 1 por seta, com
  as demais como anotações)?
- [DÚVIDA] Geração sobre nuvem preenchida (L-02): recusar `toc.generate_conflict_cloud`
  e apontar para as ações granulares, ou aceitar e propor por seção como a spec assume
  (RF-23)?
- [DÚVIDA] Classificação TRIZ (RF-18): opcional em toda injeção como a spec assume, ou
  obrigatória nas injeções do conflito D↯D′?
- [DÚVIDA] Múltiplas injeções `escolhida` (RN-08): a spec permite mais de uma escolhida
  por nuvem (cada uma pode semear ARF própria no 008) — ou uma só por vez?
- [DÚVIDA] Aviso de formulação (RN-06): apenas informativo como a spec assume, ou o
  Product Steward quer um modo "estrito" opcional por projeto que exige forma canônica
  antes de marcar a nuvem como modelada?
