# Spec 005 — Árvore da Realidade Atual (M2 — Árvore da Realidade Atual)

> Siglas: TOC — Teoria das Restrições · ARA — Árvore da Realidade Atual (CRT — *Current
> Reality Tree*) · UDE — Efeito Indesejável (*Undesirable Effect*) · APH — Aplicação ↔
> Harness · ADR — Architecture Decision Record (Registro de Decisão Arquitetural) ·
> RF/RI/RNF/RN/INT — requisito funcional / de interface / não funcional / regra de
> negócio / integração · US — User Story (história de usuário) · DDD — Domain-Driven
> Design (Design Orientado a Domínio) · TDD — Test-Driven Development (desenvolvimento
> guiado por teste) · DoD — Definition of Done (Definição de Pronto) · IA — inteligência
> artificial · FSM — máquina de estados finitos · NC — Nuvem de Conflito · OTel —
> OpenTelemetry · JSON — JavaScript Object Notation · i18n — internacionalização · UI —
> interface de usuário · CLR — Categorias de Reserva Legítima (*Categories of Legitimate
> Reservation*) · API — Application Programming Interface (interface de programação)

- **Status**: Rascunho (aprovação: gate humano do ciclo 001)
- **Raia**: plena
- **Data**: 2026-09-03
- **Origem**: [`../../docs/produto/modulos.md`](../../docs/produto/modulos.md) (M2) ·
  [`../../docs/roadmap.md`](../../docs/roadmap.md) (ciclo 005) ·
  [`../../docs/produto/rounds.md`](../../docs/produto/rounds.md) (rounds 005 e 006)

## O quê e por quê

O M2 é a primeira ferramenta TOC de verdade sobre o núcleo do M1: a **Árvore da Realidade
Atual**, que parte dos sintomas percebidos (os UDEs) e desce, por relações de
suficiência causal ("se isto, então aquilo"), até as poucas causas que explicam a
maioria deles. É a ferramenta mais madura da linhagem TOC-Builder — quatro gerações a
construíram, e a 4ª chegou a ter canvas, painel tabular, validação de UDE e análise de
árvore funcionando (F-01).

A diferença que justifica refazê-la está medida na linhagem: **toda a regra de negócio
da ARA vivia dentro de prompts de IA no cliente**. Os critérios formais de um UDE bem
formulado — 11 características, enumeradas verbatim em `constants.ts:123-133` (F-02) —
só existiam como texto interpolado numa chamada ao provedor; os 8 prompts eram dado do
navegador, editáveis por uma tela de administração (F-07), e a chave do provedor era
inicializada no próprio cliente (F-08). Validar um UDE custava uma chamada de rede, o
resultado variava com o modelo, e nenhum teste jamais cobriu a regra — é o defeito
**D-08** da visão. Este ciclo inverte isso: **o que é decidível vira regra de domínio
pura**, testável sem rede e sem modelo (a aptidão do round 005), e **o que é julgamento
fica declarado como julgamento** — do humano, ou da IA da fundação via catálogo de
ações governadas (E2.3), nunca de um SDK embutido (ADR 0007).

No encadeamento TOC, a ARA é a porta de entrada da análise: os UDEs validados aqui
alimentam a Nuvem de Conflito (M3), e a causa raiz encontrada aqui é o problema que a
injeção da NC ataca e que a Árvore da Realidade Futura (M4) projeta resolvido. Sem uma
ARA com UDEs bem formulados, todo o resto do encadeamento herda lixo — por isso a
validação formal é o coração deste módulo, não um acessório.

## O que entra como dado

- **Núcleo M1** ([`../004-nucleo-de-diagramas/spec.md`](../004-nucleo-de-diagramas/spec.md)):
  projeto, nó, aresta causal, canvas, vista tabular, desfazer de sessão, exportação. A
  ARA é um **tipo de projeto** sobre esse núcleo (RN-04 de lá: o núcleo não conhece
  semântica TOC; M2 estende por composição). O modelo de domínio estende o
  [`../004-nucleo-de-diagramas/data-model.md`](../004-nucleo-de-diagramas/data-model.md).
- **Escopo do round 005** ([`../../docs/produto/rounds.md`](../../docs/produto/rounds.md)):
  E2.1 e E2.2 executam neste ciclo **sem assistência**; **E2.3 executa no ciclo 006**,
  quando o catálogo `toc.*` e a FSM de proposta existirem — esta spec define o contrato
  das ações (INT-02..INT-06) que o 006 consome como primeiro cliente.
- **IA somente pela fundação** (ADR 0007,
  [`../../docs/adr/0007-ia-somente-pela-fundacao.md`](../../docs/adr/0007-ia-somente-pela-fundacao.md)):
  nenhum SDK de provedor no produto; prompts versionados no servidor; toda assistência é
  ação do catálogo governado. A **lógica** dos prompts da linhagem vira regra de domínio
  aqui; o texto de prompt que sobrar é insumo do servidor, nunca do cliente.
- **Alcance do P2 e item 8** (constituição própria,
  [`../../docs/governance/constitution.md`](../../docs/governance/constitution.md),
  linhas 64-71 e 87-94 — F-13): manipulação direta pelo titular aplica na hora sob três
  testes; intenção inferida (por sistema ou modelo) nasce `action_proposal`.
- **Base sintética** (ADR 0006,
  [`../../docs/adr/0006-base-sintetica-desde-o-dia-1.md`](../../docs/adr/0006-base-sintetica-desde-o-dia-1.md)):
  toda fixture e exemplo usa a "Instituição Horizonte" e personas fictícias.
- **Corte de apetite** (round 005 — F-11): estourou → **sai primeiro** o relatório de
  análise estrutural (fica a marcação manual de elos); **nunca sai** a validação formal
  de UDE como domínio puro — é a correção do D-08 e a razão de este round existir.

## Épicos, features e user stories

### E2.1 — UDEs e validação formal

**F2.1.1 — UDE como nó tipado da ARA** — todo nó da ARA é um efeito; o marcador UDE
distingue os sintomas percebidos que ancoram a análise, com os campos da ficha TOC.

- US-01 — Como Facilitadora TOC, quero marcar um nó como UDE com área impactada e
  evidências observáveis, para ancorar a análise nos sintomas que o grupo percebe.
  - Dado um projeto ARA da Instituição Horizonte com um nó "O prazo médio de resposta a
    matrículas é de 9 dias", Quando o marco como UDE e preencho área impactada
    ("Secretaria") e uma evidência, Então o nó exibe o selo UDE no canvas e na tabela, e
    a ficha persiste com o evento de domínio correspondente.
- US-02 — Como Participante, quero contribuir UDEs pela vista tabular sem mexer no
  canvas, para que uma sessão de levantamento em grupo flua.
  - Dado o painel de entidades aberto, Quando adiciono um nó já marcado UDE pela tabela,
    Então ele aparece no canvas com posição automática e entra na contagem de UDEs.

**F2.1.2 — Validação formal decidível** — os critérios decidíveis dos 11 da linhagem
avaliados por função pura de domínio: sem rede, sem modelo, com veredito por critério.

- US-03 — Como Facilitadora TOC, quero que o sistema avalie a formulação de um UDE na
  hora, sem chamar IA nenhuma, para ter o primeiro filtro de qualidade de graça.
  - Dado o texto "Falta de treinamento da equipe", Quando aciono a validação formal,
    Então recebo, em menos de um segundo e offline, o veredito por critério: reprova em
    "estado, não ação" (substantivação de falta) e em "efeito, não causa embutida", com
    a explicação de cada reprovação apontando o trecho.
- US-04 — Como Participante, quero ver quais critérios são decidíveis e quais são
  julgamento, para saber o que a máquina conferiu e o que ainda depende de gente.
  - Dado um UDE avaliado, Quando abro a ficha de validação, Então cada critério exibe
    sua classe (decidível · julgamento) e sua origem (função de domínio · parecer), sem
    misturar as duas.

**F2.1.3 — Ficha, status e parecer de julgamento** — o relatório de validação da
linhagem (F-06) refeito como dado de domínio: status com FSM própria, parecer com autor.

- US-05 — Como Facilitadora TOC, quero registrar meu julgamento sobre os critérios não
  decidíveis e fechar o status do UDE, para que "Validado" signifique algo auditável.
  - Dado um UDE com todos os critérios decidíveis verdes, Quando registro parecer de
    julgamento favorável e confirmo, Então o status muda para "Validado" com meu papel e
    data no evento; Dado um critério decidível vermelho, Quando tento validar, Então o
    sistema recusa e aponta o critério pendente.
- US-06 — Como Gestora, quero ver quantos UDEs do projeto estão em cada status, para
  saber se a base da análise está madura antes de decidir sobre ela.
  - Dado um projeto com 12 UDEs, Quando abro o resumo, Então vejo a contagem por status
    (Pendente / Requer Refinamento / Validado / Rejeitado) e a lista filtrável.

### E2.2 — Construção da árvore

**F2.2.1 — Projeto ARA sobre o núcleo** — tipo de projeto `ara` que herda canvas,
tabela, desfazer e exportação do M1, acrescentando a semântica de efeito e UDE.

- US-07 — Como Facilitadora TOC, quero criar um projeto do tipo ARA e ganhar tudo que o
  núcleo já dá, para começar a análise sem reaprender ferramenta.
  - Dado o M1 promovido, Quando crio um projeto ARA, Então canvas, painel de entidades,
    desfazer e exportação funcionam como no projeto genérico, e os nós nascem como
    efeitos com o marcador UDE disponível.

**F2.2.2 — Causas e relações de suficiência** — ligar causa a efeito lendo "se causa,
então efeito"; na ARA, causa é posição na cadeia, não tipo de nó (F-15).

- US-08 — Como Participante, quero adicionar uma causa a um UDE e ligá-la, para
  aprofundar a árvore um degrau por vez.
  - Dado o UDE "O prazo médio de resposta é de 9 dias", Quando adiciono o nó "Os
    formulários chegam incompletos" e ligo causa → efeito, Então a aresta se lê "Se os
    formulários chegam incompletos, então o prazo médio de resposta é de 9 dias" na
    ficha do elo.

**F2.2.3 — Exame de suficiência dos elos** — cada aresta pode ser examinada e marcada
(suficiente · insuficiente · com reserva), com o conector E para causas conjuntas.

- US-09 — Como Facilitadora TOC, quero marcar um elo como insuficiente com a reserva
  escrita, para que a árvore registre onde a lógica ainda não fecha.
  - Dado um elo causa → efeito, Quando o marco "insuficiente" com a reserva "a causa
    sozinha não produz o efeito; falta a condição de volume", Então o elo muda de
    aparência no canvas e a reserva aparece na ficha e no relatório.
- US-10 — Como Facilitadora TOC, quero agrupar duas causas num conector E, para dizer
  que só juntas elas produzem o efeito.
  - Dado dois elos chegando ao mesmo efeito, Quando os agrupo num conector E, Então o
    canvas desenha a elipse sobre os dois e a leitura vira "Se A **e** B, então C".

**F2.2.4 — Análise estrutural da árvore** — leitura pura do grafo: fragmentos, entradas,
cobertura de UDEs, ciclos, causa raiz candidata — o que o prompt de análise da linhagem
pedia à IA (F-05) e é computável sem ela.

- US-11 — Como Facilitadora TOC, quero um relatório estrutural da árvore, para ver de
  uma vez o que está solto, o que não leva a UDE nenhum e qual causa alcança mais
  sintomas.
  - Dado um projeto com 2 fragmentos e 8 UDEs, Quando gero o relatório, Então ele lista
    os fragmentos com seus nós, os nós de entrada, a fração de UDEs alcançada por cada
    entrada, os elos não examinados e os ciclos — e cada item tem ação de foco no canvas.

### E2.3 — Assistência via catálogo *(contrato definido aqui; execução no ciclo 006)*

**F2.3.1 — Sugestões governadas** — sugerir UDEs, causas e relações pela fundação; cada
sugestão que muta estado nasce `action_proposal`.

- US-12 — Como Facilitadora TOC, quero pedir sugestões de causas para um UDE e escolher
  quais aceito, para que a IA amplie a análise sem escrever nela por conta própria.
  - Dado um UDE selecionado e a capability de escrita presente, Quando aciono "sugerir
    causas" (`toc.suggest_causes`), Então recebo propostas pendentes — nenhum nó criado
    ainda —, e Quando aceito duas, Então só essas duas viram nós ligados, cada uma com
    traço correlacionado à proposta.

**F2.3.2 — Validação assistida (julgamento)** — a IA opina só nos critérios de
julgamento; aplicar o parecer ou a reformulação sugerida é proposta.

- US-13 — Como Participante, quero um parecer de IA sobre os critérios de julgamento do
  meu UDE, para ter um segundo olhar antes do da Facilitadora.
  - Dado um UDE formalmente verde, Quando aciono `toc.validate_ude`, Então recebo
    parecer sobre os critérios de julgamento e, se houver reformulação sugerida, ela
    chega como proposta que só aplica com meu aceite — o veredito decidível continua o
    da função de domínio, byte a byte.

**F2.3.3 — Análise assistida da árvore** — leitura interpretativa (elos fracos,
redundâncias prováveis) por cima do relatório estrutural; conexões sugeridas viram
propostas.

- US-14 — Como Gestora, quero a leitura interpretativa da IA sobre a árvore pronta, para
  levar à reunião os pontos fracos que a estrutura sozinha não mostra.
  - Dado o relatório estrutural gerado, Quando aciono `toc.analyze_tree`, Então recebo a
    análise textual referenciando nós por identificador, e cada conexão sugerida aparece
    como proposta individual aceitável/recusável — nunca aplicada em silêncio.

## Entidades e modelo de domínio

DDD puro — domínio sem framework, sem rede, sem relógio (P3). O M2 **estende** o modelo
do M1 ([`../004-nucleo-de-diagramas/data-model.md`](../004-nucleo-de-diagramas/data-model.md))
por composição; o documento consolidado deste módulo nasce na abertura do ciclo (T-02).

- **ProjetoARA**: o agregado Projeto do M1 com `TipoDeFerramenta = ara`. Todo nó seu é um
  **Efeito** (na ARA, "causa" é posição na cadeia, não tipo — F-15); nós marcados
  **UDE** carregam a **FichaDeUde**.
- **FichaDeUde** (objeto de valor no nó): área impactada, objetivo do sistema afetado,
  evidências observáveis, frequência, impactos estimados — os campos da ficha da
  linhagem (F-04), sem os campos de auditoria (que viram eventos).
- **ValidacaoFormal** (objeto de valor, resultado de função pura): por critério
  decidível — `atende` | `nao_atende` | `indeterminado` — com o trecho do texto que
  motivou o veredito. Determinística: mesmo texto, mesmo resultado.
- **ParecerDeJulgamento** (entidade): critérios de julgamento avaliados + justificativa +
  **autor** (papel humano, ou ação de catálogo com identificador de proposta). Um UDE
  acumula pareceres; o status responde ao último parecer humano confirmado.
- **StatusDeValidacao** (FSM de domínio): `Pendente → Requer Refinamento → Validado |
  Rejeitado` (os estados da linhagem — F-04, `types.ts:207`), com as transições guardadas
  pela RN-10.
- **ExameDeElo** (objeto de valor na aresta): `nao_examinado` | `suficiente` |
  `insuficiente` | `com_reserva`, com texto da reserva quando houver.
- **ConectorE** (entidade do agregado): conjunto de ≥ 2 arestas com o mesmo destino,
  lidas em conjunção; uma aresta pertence a no máximo um conector por destino.
- **AnaliseEstrutural** (serviço de domínio, função pura sobre o grafo): fragmentos, nós
  de entrada, alcance transitivo entrada → UDEs, elos não examinados, ciclos, causa raiz
  candidata (RN-12). Não muta nada.
- **Eventos de domínio** (somente-acréscimo, além dos do M1): `UdeMarcado`,
  `UdeDesmarcado`, `FichaDeUdeEditada`, `ValidacaoFormalExecutada`, `ParecerRegistrado`,
  `StatusDeValidacaoMudou`, `EloExaminado`, `ConectorEFormado`, `ConectorEDesfeito`,
  `AnaliseEstruturalGerada`.
- **Fora do domínio**: prompts e provedores (servidor da fundação — ADR 0007); a FSM de
  `action_proposal` (uma só e do servidor — item 8; entra no ciclo 006); a renderização
  do conector E.

## Requisitos funcionais

### UDE como nó tipado da ARA

RF-01: O SISTEMA DEVE permitir criar projeto do tipo ARA, herdando do M1 canvas, vista
tabular, desfazer de sessão, exclusão suave e exportação sem reimplementação. [F-10] 🟡

RF-02: O SISTEMA DEVE permitir marcar e desmarcar qualquer nó de projeto ARA como UDE,
registrando `UdeMarcado`/`UdeDesmarcado`. [F-16] 🟡

RF-03: O SISTEMA DEVE manter, por nó marcado UDE, a FichaDeUde com área impactada,
objetivo afetado, evidências observáveis, frequência e impactos estimados — todos
opcionais exceto a descrição do próprio nó. [F-04] 🟡

RF-04: O SISTEMA DEVE exibir a contagem de UDEs por status de validação no resumo do
projeto, com filtro por status na vista tabular. 🟡

RF-05: QUANDO um nó marcado UDE for excluído, O SISTEMA DEVE arquivar a ficha e os
pareceres junto ao evento de exclusão — a restauração (M1) devolve tudo. 🟡

### Validação formal decidível

RF-06: O SISTEMA DEVE avaliar a formulação de um texto de UDE por função pura de
domínio, executável **sem rede e sem modelo**, devolvendo veredito por critério
decidível com o trecho que o motivou. [F-01, F-02, F-11] 🟡

RF-07: O SISTEMA DEVE avaliar como critérios decidíveis, no mínimo: frase completa no
tempo presente (RN-01), estado e não ação (RN-02), sem causa embutida por marcador
lexical (RN-03), sem solução embutida por marcador lexical (RN-04), neutralidade — sem
culpar pessoa ou grupo (RN-05), entidade única (RN-06). [F-02] 🟡

RF-08: O SISTEMA DEVE devolver `indeterminado` — nunca um chute — quando a heurística de
um critério decidível não alcançar o caso, e o critério indeterminado DEVE contar como
pendência de julgamento, não como reprovação. 🟡

RF-09: O SISTEMA DEVE declarar, em dado versionado do domínio (não em prompt), a
classificação de cada um dos 11 critérios da linhagem em decidível × julgamento, e a
ficha DEVE exibir essa classe por critério. [F-02, F-11] 🟡

RF-10: O SISTEMA DEVE reexecutar a validação formal automaticamente quando o texto do
nó mudar, invalidando o veredito anterior (o evento guarda os dois). 🟡

RF-11: O SISTEMA DEVE manter o léxico das heurísticas (marcadores de causa, de solução,
de culpa, verbos de ação) como dado versionado por idioma, testável em isolamento —
nunca literal espalhado no código. 🟡

RF-12: O SISTEMA DEVE garantir por teste de domínio que os casos canônicos da linhagem
decidem como o método manda: "Falta de treinamento causa erros" reprova (causa
embutida); "Precisamos de um novo software" reprova (solução embutida); "A taxa de
erros no processo X é de 15%" aprova nos critérios decidíveis. [F-02] 🟡

### Ficha, status e parecer de julgamento

RF-13: O SISTEMA DEVE registrar parecer de julgamento sobre os critérios não decidíveis,
com autor (papel humano, ou ação de catálogo com identificador de proposta),
justificativa e data — pareceres se acumulam, nunca se sobrescrevem. [F-04] 🟡

RF-14: O SISTEMA DEVE manter o status de validação do UDE na FSM `Pendente → Requer
Refinamento → Validado | Rejeitado`, recusando transição para `Validado` enquanto
qualquer critério decidível estiver reprovado ou sem parecer humano confirmado
(RN-10). [F-04] 🟡

RF-15: QUANDO a validação formal reprovar um critério, O SISTEMA DEVE apresentar a
explicação e o trecho apontado, e DEVE permitir editar o texto e reavaliar no mesmo
fluxo, sem perder a ficha. [F-06] 🟡

RF-16: O SISTEMA DEVE registrar quem validou e quando em evento de domínio — nunca em
campo editável da ficha (o contraste com a linhagem, onde `validado_por` era texto
devolvido pelo modelo — F-04). 🟡

RF-17: O SISTEMA DEVE permitir reabrir um UDE `Validado` para `Requer Refinamento` por
ação explícita com justificativa, registrando `StatusDeValidacaoMudou` com o motivo. 🟡

### Causas e relações de suficiência

RF-18: O SISTEMA DEVE permitir adicionar um nó causa já ligado a um efeito existente num
único gesto ("adicionar causa a este nó"), no canvas e na tabela. [F-15] 🟡

RF-19: O SISTEMA DEVE apresentar a leitura de suficiência de cada aresta — "Se
<origem>, então <destino>" — na ficha do elo, montada dos textos atuais dos nós. [F-10]
🟡

RF-20: O SISTEMA DEVE herdar do M1 as invariantes de aresta (sem auto-laço, sem
duplicata, nós do mesmo projeto) sem exceção nova para a ARA. 🟡

RF-21: O SISTEMA DEVE permitir que um mesmo nó seja causa de vários efeitos e efeito de
várias causas — a ARA é grafo dirigido, não árvore estrita, e o nome não cria
invariante falsa. 🟡

### Exame de suficiência dos elos

RF-22: O SISTEMA DEVE permitir marcar cada aresta com o exame `suficiente` |
`insuficiente` | `com_reserva`, com texto de reserva obrigatório nos dois últimos,
registrando `EloExaminado`. 🟡

RF-23: O SISTEMA DEVE permitir agrupar duas ou mais arestas com o mesmo destino num
conector E (conjunção), desenhado como elipse sobre os elos, e desfazê-lo — validando
que toda aresta do conector aponta para o mesmo destino (RN-11). 🟡

RF-24: O SISTEMA DEVE apresentar a leitura conjunta do conector E — "Se A **e** B,
então C" — na ficha do destino. 🟡

RF-25: O SISTEMA DEVE distinguir visualmente, no canvas e na tabela, elo não examinado,
suficiente, insuficiente e com reserva — o estado do exame é dado de primeira classe,
não anotação solta. 🟡

### Análise estrutural da árvore

RF-26: O SISTEMA DEVE computar por função pura de domínio, sem rede e sem modelo, o
relatório estrutural: fragmentos (componentes desconexos), nós de entrada (sem
antecessor), alcance transitivo de cada entrada sobre os UDEs, elos não examinados e
ciclos. [F-05, F-09] 🟡

RF-27: O SISTEMA DEVE apontar a causa raiz candidata — a entrada que alcança a maior
fração dos UDEs marcados — como sugestão nomeada, nunca como conclusão automática
(RN-12). 🟡

RF-28: O SISTEMA DEVE listar no relatório os UDEs não alcançados por nenhuma entrada
examinada — a medida de quanto da dor percebida a árvore ainda não explica. 🟡

RF-29: QUANDO houver ciclo, O SISTEMA DEVE listá-lo com seus nós — laços de reforço são
legítimos na TOC — e DEVE excluí-los do cálculo de causa raiz candidata, dizendo isso
no próprio relatório. 🟡

RF-30: O SISTEMA DEVE oferecer, em cada item do relatório, ação de foco que centraliza o
elemento no canvas (mesmo mecanismo do M1). 🟡

RF-31: O SISTEMA DEVE registrar `AnaliseEstruturalGerada` com o resumo quantitativo
(contagens por seção), para que a jornada e o traço mostrem a evolução da árvore. 🟡

### Assistência via catálogo (contrato — execução no ciclo 006)

RF-32: O SISTEMA DEVE expor as ações `toc.suggest_udes`, `toc.suggest_causes` e
`toc.suggest_relations` no catálogo governado, cada sugestão mutadora nascendo
`action_proposal` individual — aceitar cria o nó/aresta com traço correlacionado à
proposta; recusar não toca o projeto. [F-03, F-12] 🟡

RF-33: O SISTEMA DEVE expor `toc.validate_ude` como ação de leitura que devolve parecer
**apenas sobre os critérios de julgamento**; o veredito dos critérios decidíveis é
sempre o da função de domínio, anexado pela aplicação — nunca recalculado pelo modelo.
[F-03, F-04] 🟡

RF-34: QUANDO `toc.validate_ude` sugerir reformulação do texto, O SISTEMA DEVE
apresentá-la como `action_proposal` de edição do nó — aplicar reexecuta a validação
formal (RF-10) sobre o texto novo. 🟡

RF-35: O SISTEMA DEVE expor `toc.analyze_tree` como ação de leitura que recebe o grafo
e o relatório estrutural (RF-26) como contexto e devolve análise interpretativa;
conexão sugerida no corpo da análise vira `action_proposal` de aresta, uma a uma.
[F-03, F-05] 🟡

RF-36: O SISTEMA DEVE recusar, em falha fechada, qualquer caminho em que texto produzido
por modelo mute o projeto sem passar pela FSM de proposta — inclusive o "aceitar tudo",
que é lote de propostas, não atalho. [F-13] 🟡

RF-37: QUANDO a capability de escrita não estiver presente na introspecção, O SISTEMA
DEVE omitir do catálogo as ações mutadoras (`toc.suggest_*`), mantendo as de leitura —
a lição paga pela irmã, já fixada como portão do ciclo 006. 🟡

RF-38: O SISTEMA DEVE funcionar por inteiro nos épicos E2.1 e E2.2 com o catálogo
ausente ou desligado — a assistência é aceleradora, nunca dependência (é o que permite
ao round 005 entregar a ARA antes do 006). 🟡

## Requisitos de interface

RI-01: O nó marcado UDE exibe selo distinto no canvas e na tabela, com o status de
validação por cor **e** por texto (nunca só cor). 🟡

RI-02: A ficha de validação apresenta os critérios em duas seções nomeadas — decidíveis
(com veredito e trecho apontado) e julgamento (com pareceres e autores) — substituindo o
modal monolítico da linhagem (F-06). 🟡

RI-03: A reprovação de critério decidível aponta o trecho no próprio texto do UDE
(marcação inline), com a explicação ao lado — não em janela separada. 🟡

RI-04: O fluxo reprovar → editar → reavaliar acontece na mesma superfície, sem fechar a
ficha; a reavaliação responde em menos de 1 segundo (RNF-05). 🟡

RI-05: O exame de elo é acionável na própria aresta (canvas) e na linha (tabela); os
quatro estados do exame têm representação visual distinta e acessível. 🟡

RI-06: O conector E é desenhado como elipse sobre as arestas agrupadas — a notação
canônica da TOC — e a ficha do destino mostra a leitura conjunta. 🟡

RI-07: O relatório estrutural é um painel lateral com seções recolhíveis (fragmentos,
entradas, cobertura, elos não examinados, ciclos), cada item com ação de foco. 🟡

RI-08: As propostas de assistência (E2.3) aparecem numa bandeja de propostas pendentes
com aceitar/recusar por item — nunca aplicação silenciosa; a bandeja diz de qual ação e
de qual proposta cada item veio. 🟡

RI-09: O resumo de UDEs por status aparece no cabeçalho do projeto ARA, com filtro de um
clique na vista tabular. 🟡

RI-10: Toda superfície do módulo respeita tema do hospedeiro com fallback, modo
só-conteúdo e operação por teclado, herdados dos ciclos 002/003; textos por i18n pt/en
(E8.3), inclusive as explicações de critério. 🟡

## Requisitos não funcionais

RNF-01: A validação formal e a análise estrutural são funções puras testáveis sem rede,
sem banco e sem modelo — a suíte de domínio deste módulo roda offline por construção
(P3, P4; aptidão do round 005). [F-11] 🟡

RNF-02: A fronteira hexagonal é verificada por `import-linter`: o pacote de domínio do
M2 não importa framework, HTTP, banco nem cliente de IA — o build falha na violação. 🟡

RNF-03: Toda mutação do módulo emite traço OTel correlacionado e log estruturado;
pareceres e propostas aceitas carregam no traço o identificador da proposta de origem
(P5). 🟡

RNF-04: A validação formal de um texto de até 500 caracteres responde em menos de 100
milissegundos no servidor e é utilizável offline no cliente (mesma regra portada ou
chamada local — decisão de arquitetura no plan). 🟡

RNF-05: O ciclo editar → reavaliar na ficha responde em menos de 1 segundo no percentil
95, medido na jornada viva. 🟡

RNF-06: A análise estrutural de um projeto com 200 nós e 300 arestas computa em menos de
2 segundos no percentil 95 (o teto herdado do M1, RNF-05 de lá). 🟡

RNF-07: O léxico heurístico por idioma (RF-11) tem cobertura de teste própria com corpus
sintético versionado de UDEs bons e maus — ampliar o léxico exige ampliar o corpus. 🟡

RNF-08: Nenhum prompt, chave ou cliente de provedor no repositório do produto — grep de
CI herdado do M1 estendido aos padrões de prompt (`system_prompt`, `promptText`) (P7,
ADR 0007; o contraexemplo é F-07/F-08). 🟡

RNF-09: Os textos de critério, explicação e relatório saem do mecanismo de i18n com
chave estável — a chave do critério é a mesma da regra de domínio (RN-NN), para a
rastreabilidade spec ↔ código ↔ tela. 🟡

## Regras de negócio

RN-01: UDE é frase completa no tempo presente. [F-02, característica 2] 🟢 (critério na
linhagem: `constants.ts:124`; heurística decidível: sujeito + verbo finito no presente,
sem forma imperativa/infinitiva inicial — 🟡)

RN-02: UDE descreve um **estado** do sistema, não uma ação nem a falta de uma. [F-02,
característica 3] 🟢 (`constants.ts:125`; heurística: substantivações de ausência
— "falta de", "ausência de" — e verbos de ação sem sujeito-sistema reprovam — 🟡)

RN-03: UDE é **efeito**: não é causa especulada nem embute a própria causa na
verbalização. [F-02, características 7 e 10] 🟢 (`constants.ts:129,132`; decidível por
marcador lexical — "porque", "devido a", "causa", "por falta de" — e julgamento no
resto — 🟡)

RN-04: UDE não é solução oculta. [F-02, característica 8] 🟢 (`constants.ts:130`;
marcadores: "precisamos", "deveria", "falta implantar" — 🟡)

RN-05: UDE não culpa pessoa nem grupo (neutralidade). [F-02, característica 6] 🟢
(`constants.ts:128`; marcadores: nome de papel/pessoa como sujeito de verbo de falha —
🟡)

RN-06: UDE contém uma única entidade (ideia/fato). [F-02, característica 9] 🟢
(`constants.ts:131`; heurística: coordenação de orações independentes reprova — 🟡)

RN-07: UDE é factual e não subjetivo — **julgamento**, com parecer. [F-02,
característica 11] 🟢 (`constants.ts:133`)

RN-08: UDE está na esfera de influência e algo pode ser feito a respeito —
**julgamento**, com parecer. [F-02, características 4 e 5] 🟢 (`constants.ts:126-127`)

RN-09: UDE de "existência de lacuna" é preferível a UDE de "dificuldade em fechar a
lacuna" — **julgamento**; a ficha registra a distinção. [F-02] 🟢 (`constants.ts:135-137`)

RN-10: `Validado` exige todos os critérios decidíveis em `atende` **e** parecer humano
confirmado cobrindo os critérios de julgamento e os `indeterminado`; parecer de IA
nunca fecha status sozinho. 🟡

RN-11: Aresta da ARA é relação de **suficiência** ("se causa, então efeito"); causas que
só em conjunto produzem o efeito agrupam-se em conector E, e toda aresta de um conector
aponta para o mesmo destino. [F-10] 🟢 (a leitura causal está na linhagem:
`APLICATION_PURPOSE.md:24`; o conector E é do método TOC, sem precedente na linhagem —
🟡, ver F-09)

RN-12: Causa raiz candidata é a entrada (nó sem antecessor, fora de ciclo) com maior
alcance transitivo sobre os UDEs marcados; o sistema **aponta**, o humano **conclui** —
a conclusão é parecer, não campo calculado. 🟡

## Integrações

INT-01: O M2 consome do M1 (ciclo 004) o agregado Projeto, nó, aresta, canvas, tabela,
desfazer e exportação; consome da junta 003 identidade (`POST /auth/introspect`),
isolamento por inquilino e OTel. Nenhuma dessas peças é reimplementada aqui. 🟡

INT-02: `toc.suggest_udes` — catálogo `toc.*`, mutadora (risco: cria nós), entrada:
descrição do problema + UDEs existentes; saída: propostas de nó UDE, uma
`action_proposal` por sugestão. Execução: ciclo 006 (FSM). [F-03] 🟡

INT-03: `toc.suggest_causes` — mutadora (cria nó + aresta), entrada: nó alvo + contexto
do grafo; saída: propostas de causa ligada. [F-03, F-15] 🟡

INT-04: `toc.suggest_relations` — mutadora (cria arestas), entrada: nós e arestas
existentes; saída: propostas de aresta com justificativa. [F-03] 🟡

INT-05: `toc.validate_ude` — leitura com parecer (não muta); a reformulação sugerida
chega como `action_proposal` de edição (RF-34). [F-03, F-04] 🟡

INT-06: `toc.analyze_tree` — leitura; recebe grafo + relatório estrutural; conexões
sugeridas viram propostas de aresta individuais (RF-35). [F-03, F-05] 🟡

INT-07: Telas deste módulo entram no registro de telas do E7.5 com identificador
estável (`toc.ara_canvas`, `toc.ude_ficha`, `toc.ara_relatorio`, `toc.propostas`),
no formato herdado do M1 (INT-02 de lá); campos da ficha marcam `ai_visible` campo a
campo para o snapshot sanitizado do ciclo 006. 🟡

INT-08: Os prompts que as ações do catálogo usarem são versionados **no servidor** e
nunca circulam no cliente nem no snapshot (ADR 0007); a tela de administração de
prompts da linhagem (F-07) **não é portada**. 🟡

## Telas e fluxos

### 6.1 Canvas ARA — Job: construir a árvore dos sintomas às causas · Campos: nós
(efeito, selo UDE, status), arestas (exame do elo), conectores E · Ações: as do M1 +
marcar UDE, adicionar causa, examinar elo, agrupar em conector E.

### 6.2 Ficha de UDE e validação — Job: transformar queixa em UDE bem formulado ·
Campos: texto, ficha TOC, critérios decidíveis (veredito + trecho), critérios de
julgamento (pareceres) · Ações: validar formalmente, editar e reavaliar, registrar
parecer, mudar status, reabrir.

### 6.3 Exame de elo — Job: dizer onde a lógica fecha e onde não · Campos: leitura "se…
então…", estado do exame, reserva · Ações: marcar suficiente/insuficiente/com reserva,
agrupar/desfazer conector E.

### 6.4 Relatório estrutural — Job: ver a árvore como um todo antes de concluir ·
Campos: fragmentos, entradas, cobertura de UDEs, elos não examinados, ciclos, causa
raiz candidata · Ações: gerar, focar item no canvas, exportar com o projeto.

### 6.5 Bandeja de propostas (ciclo 006) — Job: aceitar ajuda sem perder a autoria ·
Campos: propostas pendentes por ação de origem · Ações: aceitar/recusar por item,
aceitar em lote (lote de propostas, não atalho).

## Fora de escopo

- **O épico E2.3 inteiro — assistência via catálogo** (sugerir UDEs, causas e relações,
  validação assistida de julgamento, análise interpretativa da árvore). É a decisão 4 dos
  rounds: nenhuma ferramenta ganha assistência antes de o catálogo `toc.*` e a FSM de
  proposta existirem, o que acontece no ciclo 006
  ([`../006-acoes-governadas-e-snapshot/spec.md`](../006-acoes-governadas-e-snapshot/spec.md)).
  Aqui ficam os **contratos** INT-02..INT-06, que aquele ciclo consome como primeiro
  cliente — nenhuma linha de execução.
- **Transformar em função de domínio os critérios de UDE que são julgamento** — das 11
  características da linhagem, as indecidíveis ficam declaradas como parecer (do humano ou
  da fundação), nunca como regra que aprova ou reprova. É o que o D-12 mede e o que separa
  esta ARA do prompt que ela aposenta.
- **Promover o UDE para a Nuvem de Conflito e semear a árvore de futuro** — o encadeamento
  é do ciclo 008 (E4.4); esta spec produz UDEs validados e para aí
  ([`../008-arvores-de-futuro-e-implementacao/spec.md`](../008-arvores-de-futuro-e-implementacao/spec.md)).
- **Relatório de análise assistida da árvore** (elos fracos, causa raiz sugerida) — é o
  item que o corte de apetite do round 005 solta primeiro; fica a análise **estrutural**,
  que é leitura pura do grafo, e a marcação manual dos elos
  ([`../../docs/produto/rounds.md`](../../docs/produto/rounds.md), round 005).
- **Importação das árvores da linhagem TOC-Builder** — ciclo 011, E1.4 avançado; a base
  deste ciclo é sintética, da "Instituição Horizonte"
  ([`../../docs/adr/0006-base-sintetica-desde-o-dia-1.md`](../../docs/adr/0006-base-sintetica-desde-o-dia-1.md)).
- **Qualquer chamada a provedor de modelo a partir do cliente** — os 8 prompts eram dado
  do navegador e a chave era inicializada lá; o ADR 0007 fecha essa porta. O texto de
  prompt que sobrar é insumo do servidor, nunca do cliente
  ([`../../docs/adr/0007-ia-somente-pela-fundacao.md`](../../docs/adr/0007-ia-somente-pela-fundacao.md)).

## Entregáveis

- Domínio Python puro do M2: extensão ARA do agregado, ValidacaoFormal (função pura +
  léxico versionado pt/en), FSM de status, ExameDeElo, ConectorE, AnaliseEstrutural —
  com testes de domínio **sem rede e sem modelo**, nascidos antes do código (P4), sobre
  corpus sintético de UDEs versionado.
- Casos de uso + adaptadores REST estendendo os contratos do M1; migrações Alembic com
  downgrade (ficha, pareceres, exame, conector).
- Interface React: canvas ARA, ficha de validação, exame de elo, relatório estrutural —
  sobre o `ux-design.md` do ciclo 002; bandeja de propostas fica como tela especificada
  para o 006.
- Declaração das ações `toc.*` deste módulo (INT-02..INT-06) no formato do catálogo,
  pronta para o manifesto do ciclo 006.
- Jornada viva (P6): construção de uma ARA sintética completa da "Instituição
  Horizonte" — do primeiro UDE reprovado e reformulado até a causa raiz candidata — com
  captura gerada por script versionado do build real e avaliação heurística datada.
- Entradas de CHANGELOG; ADR novo se decisão material surgir (candidata: escopo do
  léxico heurístico — ver Clarify).

## Critérios de aceite (DoD)

| # | Critério | Verificação executável |
|---|---|---|
| 1 | Validação formal é domínio puro, offline | `pytest tests/domain/test_validacao_formal.py -p no:cacheprovider` verde com rede desabilitada + `lint-imports` código 0 |
| 2 | Os casos canônicos da linhagem decidem certo (RF-12) | `pytest tests/domain/test_validacao_formal.py -k canonicos -v` — mostra os 3 casos |
| 3 | Nenhum critério decidível depende de prompt | `grep -rn "promptText\|system_prompt" backend/src/dominio/ frontend/src/ \| wc -l` = 0 |
| 4 | Corpus sintético cobre o léxico | `pytest tests/domain/test_corpus_udes.py -v` — a saída diz quantos casos bons/maus examinou (R2) |
| 5 | FSM de status guarda a RN-10 | `pytest tests/domain/test_status_validacao.py` — `Validado` recusado com decidível vermelho ou sem parecer humano |
| 6 | Conector E validado no domínio | `pytest tests/domain/test_conector_e.py` — destino único, ≥2 arestas, leitura conjunta |
| 7 | Análise estrutural pura e correta | `pytest tests/domain/test_analise_estrutural.py` — fragmentos, entradas, alcance, ciclos sobre grafos de fixture |
| 8 | Ciclos fora da causa raiz candidata (RF-29) | `pytest tests/domain/test_analise_estrutural.py -k ciclo -v` |
| 9 | Toda mutação nova com traço | `pytest tests/integration/test_traco_m2.py` — falha se `UdeMarcado`, `ParecerRegistrado`, `EloExaminado` não emitirem traço |
| 10 | Ações `toc.*` declaradas sem executar | `ls contracts/` contém a declaração das 5 ações; `grep -c "toc\." contracts/acoes-catalogo.md` ≥ 5; nenhuma rota de execução no serviço (`grep -rn "suggest_\|analyze_tree" backend/src/adaptadores/rest/ \| wc -l` = 0) |
| 11 | Sem SDK, chave ou prompt no produto | `grep -rniE "genai\|openai\|anthropic\|api[_-]?key" backend/ frontend/src/ \| wc -l` = 0 |
| 12 | Jornada viva da ARA sintética | `ls docs/jornadas/` contém a jornada do M2 com capturas geradas por script; grep negativo de nome real |
| 13 | Conformidade do ciclo | `scripts/check-conformance.sh 005` código 0 |
| 14 | Caminhos e links | `scripts/check-caminhos.sh` e `scripts/check-links.sh` código 0 + quanto examinaram |

## Fontes

F-01: /home/user/tocbuilderv3/APLICATION_PURPOSE.md:52-60 — §3.2 "Validação e Análise
Crítica": estrutura (frase completa, presente), conteúdo (estado, não ação), foco
(efeito, não causa/solução), neutralidade (não culpar), relatório completo e análise da
árvore — o mapa dos critérios que esta spec transforma em regra 🟢

F-02: /home/user/tocbuilderv3/constants.ts:109-240 — `VALIDATE_UDE_DETAILED_PROMPT_TEXT`:
as 11 características do UDE bem articulado em `constants.ts:123-133` (contadas:
`sed -n '123,133p' constants.ts | grep -c '^[0-9]'` → `11`), os tipos lacuna ×
dificuldade (l.135-137) e os exemplos canônicos (l.162-163) — a regra de negócio inteira
dentro de um prompt: o defeito D-08 na fonte 🟢

F-03: /home/user/tocbuilderv3/types.ts:137 — o tipo-união das operações de assistência:
`'validate_ei' | 'suggest_eis' | 'suggest_relations' | 'analyze_tree' |
'validate_ude_structured' | 'suggest_causes_for_ei' | 'generate_conflict_cloud'` — 7
operações (`sed -n 137p types.ts | grep -o "'[a-z_]*'" | wc -l` → `7`), 6 da ARA (a 7ª
é da NC, M3); viram as 5 ações INT-02..INT-06 (validação simples e detalhada fundem-se
em `toc.validate_ude`) 🟢

F-04: /home/user/tocbuilderv3/types.ts:171-213 — `GeminiUdeValidationResponse`: 13
sub-critérios booleanos (`sed -n '178,201p' types.ts | grep -c boolean` → `13`), status
final em `types.ts:207` (`'Pendente' | 'Validado' | 'Rejeitado' | 'Requer Refinamento'`),
ficha (área impactada, evidências, frequência, impactos) e `validado_por` como texto do
modelo — a estrutura que vira FichaDeUde + ValidacaoFormal + ParecerDeJulgamento + FSM 🟢

F-05: /home/user/tocbuilderv3/constants.ts:83-107 — `ANALYZE_TREE_PROMPT_TEXT`: pedia à
IA fragmentação, redundância, clareza e completude (l.93-96) e sugestões de conexão em
formato `CONNECT|fromId=...` parseado do texto (l.100-106) — o estrutural vira o RF-26
(função pura); o que é interpretativo vira `toc.analyze_tree` (INT-06) 🟢

F-06: /home/user/tocbuilderv3/components/UdeValidationModal.tsx — o relatório de
validação da linhagem, 206 linhas (`wc -l` → `206 components/UdeValidationModal.tsx`) —
a UI existia e provou valor; refeita como ficha com duas seções (RI-02) 🟢

F-07: /home/user/tocbuilderv3/constants.ts:341-405 — `INITIAL_SYSTEM_PROMPTS`: 8 prompts
como dado do cliente (`grep -c "promptText:" constants.ts` → `8`), editáveis pela tela
`PROMPT_ADMIN` — regra de negócio editável em produção, sem teste; o contraexemplo que
motiva RF-09 e INT-08 🟢

F-08: /home/user/tocbuilderv3/services/geminiService.ts:16 — `const ai = new
GoogleGenAI({ apiKey: process.env.API_KEY });` no código do navegador — a violação
canônica do P7 que o ADR 0007 mata 🟢

F-09: /home/user/tocbuilderv3 — `grep -rni "sufici" --include="*.ts" --include="*.tsx"
--include="*.md" . | grep -v node_modules | wc -l` → `4`, e **nenhuma** das 4 é análise
de suficiência da ARA (uma é o campo de suficiência dos filhos da S&T, duas são usos
casuais de "suficiente", uma é o critério "específico o suficiente" do prompt simples) —
o exame de elos e o relatório estrutural (E2.2) não têm precedente na linhagem: são
método TOC aplicado, 🟡 por construção 🟢

F-10: /home/user/tocbuilderv3/APLICATION_PURPOSE.md:20-25 — §2.1: a ARA como coração da
aplicação; a leitura causal "Se A... então B..." (l.24); canvas + painel de entidades 🟢

F-11: [`../../docs/produto/rounds.md`](../../docs/produto/rounds.md) — Round 005:
aptidão executável ("critérios decidíveis avaliados por teste de domínio sem rede e sem
modelo"), E2.3 fora (decisão 4, para o round 006), corte de apetite, defeito D-08 🟢

F-12: [`../../docs/adr/0007-ia-somente-pela-fundacao.md`](../../docs/adr/0007-ia-somente-pela-fundacao.md)
— toda assistência via catálogo de ações governadas; prompts versionados no servidor 🟢

F-13: [`../../docs/governance/constitution.md`](../../docs/governance/constitution.md)
linhas 64-71 (alcance do P2) e 87-94 (item 8: manipulação direta, intenção inferida
nasce proposta, FSM uma só e do servidor) 🟢

F-14: /home/user/tocbuilderv3/constants.ts:19-36 — `VALIDATE_EI_PROMPT_TEXT`: a validação
"simples" usava **outros** critérios (clareza, especificidade, foco, realidade atual) —
duas validações inconsistentes conviviam na mesma geração; o argumento para uma regra
única de domínio (RF-06) e uma única ação (`toc.validate_ude`, INT-05) 🟢

F-15: /home/user/tocbuilderv3/constants.ts:242-262 — `SUGGEST_CAUSES_FOR_EI_PROMPT_TEXT`:
"uma 'causa' também é um Efeito Indesejável (EI) que simplesmente está em uma posição
anterior na cadeia causal" (l.247) — causa é posição, não tipo (modelo de domínio) 🟢

F-16: /home/user/tocbuilderv3/types.ts:34-36 — `enum NodeType { EI = 'EI' }`: a linhagem
só tinha um tipo de nó; o marcador UDE desta spec formaliza a distinção que lá era
implícita 🟢

## Lacunas e assunções

L-01: As heurísticas lexicais dos critérios decidíveis (RN-01..RN-06) não têm precedente
medido — a linhagem decidia tudo por modelo. Assunção: heurística conservadora com
`indeterminado` honesto (RF-08) + corpus sintético versionado (RNF-07) bastam para o
v1; falso `indeterminado` degrada para julgamento, nunca para veredito errado — risco
**médio**.

L-02: O exame de suficiência e o relatório estrutural não existem na linhagem (F-09) —
são método TOC sem contraparte medida; as CLR completas (reserva de causalidade, de
entidade, de tautologia…) ficam fora do v1. Assunção: o subconjunto elo examinado +
conector E + relatório estrutural cobre a prática; ampliar para as CLR completas é
decisão nova por ADR — risco **médio**.

L-03: O contrato das ações `toc.*` (INT-02..INT-06) antecipa o catálogo que o ciclo 006
fixa. Assunção: declarar sem executar (DoD 10) custa pouco e dá ao 006 um primeiro
cliente concreto; se o formato do catálogo divergir, a migração é da declaração, não do
domínio — risco **baixo**.

L-04: O apetite de um ciclo para E2.1 + E2.2 com TDD e léxico bilíngue é estimativa sem
histórico próprio. Assunção: o corte do round 005 (sai o relatório estrutural primeiro,
nunca a validação formal) absorve o estouro — risco **médio**.

L-05: A distinção decidível × julgamento do RF-09 é decisão nossa sobre os 11 critérios
— a linhagem não a fazia (mandava tudo ao modelo). Assunção: a partição desta spec
(6 decidíveis com heurística, 5 de julgamento) é o ponto de partida; ela é dado
versionado (RF-09), então mover um critério de classe é mudança de dado com teste, não
de arquitetura — risco **baixo**.

## Clarify

- [DÚVIDA] RN-10: `Validado` sempre exige parecer humano, ou o Product Steward aceita um
  "Validado (formal)" intermediário quando só os decidíveis passaram — útil em sessão de
  levantamento rápido — com o julgamento vindo depois?
- [DÚVIDA] Léxico heurístico (RF-11): pt e en desde o v1 (coerente com E8.3), ou pt
  primeiro e en quando a i18n consolidar no ciclo 011? A spec assume pt+en mínimos.
- [DÚVIDA] Conector E (RF-23): entra no v1 do exame de elos, ou fica para o ciclo 008
  (onde a ARF o exige de qualquer forma)? A spec assume que entra — é a notação que a
  Facilitadora espera — mas ele é candidato natural de corte atrás do relatório.
- [DÚVIDA] `toc.suggest_udes` (INT-02) propõe a partir da descrição do problema do
  projeto; o Product Steward quer também o modo "a partir de narrativa colada" (texto
  livre trazido de fora), ou isso é exclusivo da NC (M3/E3.3)?
- [DÚVIDA] Reabertura (RF-17): quem pode reabrir um UDE `Validado` — só a Facilitadora
  TOC e a Administradora do tenant, ou qualquer Participante? A matriz papel × ação do
  Clarify 3 do M1 decide junto.
