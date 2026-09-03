# Spec 010 — Estratégia & Táticas (M5 — Estratégia & Táticas)

> Siglas: TOC — Teoria das Restrições · S&T — Estratégia & Táticas (*Strategy &
> Tactics*) · APR — Árvore de Pré-Requisitos · AT — Árvore de Transição · APH —
> Aplicação ↔ Harness · ADR — Architecture Decision Record (Registro de Decisão
> Arquitetural) · RF/RI/RNF/RN/INT — requisito funcional / de interface / não funcional
> / regra de negócio / integração · US — User Story (história de usuário) · DDD —
> Domain-Driven Design (Design Orientado a Domínio) · TDD — Test-Driven Development
> (desenvolvimento guiado por teste) · DoD — Definition of Done (Definição de Pronto) ·
> IA — inteligência artificial · OTel — OpenTelemetry · JSON — JavaScript Object
> Notation · i18n — internacionalização · UI — interface de usuário · CI — integração
> contínua · CRUD — Create, Read, Update, Delete (criar, ler, atualizar, excluir) ·
> VCD — Value Creating Deliverable (entregável gerador de valor, jargão da linhagem) ·
> SDK — Software Development Kit (kit de desenvolvimento)

- **Status**: Rascunho (aprovação: gate humano do ciclo 001)
- **Raia**: plena
- **Data**: 2026-09-03
- **Origem**: [`../../docs/produto/modulos.md`](../../docs/produto/modulos.md) (M5) ·
  [`../../docs/roadmap.md`](../../docs/roadmap.md) (ciclo 010) ·
  [`../../docs/produto/rounds.md`](../../docs/produto/rounds.md) (round 010)

## O quê e por quê

O M5 resgata a **única ferramenta que regrediu na linhagem** (defeito D-05). A árvore
de S&T decompõe uma meta em passos hierarquicamente numerados — 1, 1.1, 1.1.2 — onde
cada passo declara a estratégia (o quê) e a tática (como), sustentadas por **três
premissas lógicas**: a paralela (o pressuposto de contexto que sustenta o passo), a de
necessidade ao pai (por que o pai precisa deste passo) e a de suficiência dos filhos
(por que os filhos bastam). A regressão está medida: a ferramenta estava **habilitada
na 1ª e na 2ª gerações** (F-01, F-02) e foi desligada da 3ª em diante — na 4ª geração o
item da navegação carrega `disabled: true` (F-02) com o **modelo de dados completo
parado no código** (F-03): enum de status, numeração hierárquica comentada no próprio
tipo e os três campos de premissa. Funcionalidade que regride sem decisão registrada é
o que um ADR existe para impedir; este ciclo desfaz a regressão com a decisão
registrada (ADR 0005, F-13).

O que a linhagem tinha de bom entra: o modelo dos três campos de premissa existia
desde a 1ª geração (F-04) e o editor da 4ª já os oferecia em três áreas de texto
(F-06). O que tinha de defeito não atravessa: o **número do passo era digitado à mão**,
obrigatório e sem validação de formato ou unicidade — o próprio código admite em
comentário (F-05) — quando numeração hierárquica é, por definição, derivável da
posição na árvore; a estrutura reusava aresta de grafo livre "por simplicidade" (F-03),
permitindo topologias que não são árvore; e **excluir um passo descartava todos os
outros** — o filtro do serviço mantém só o nó excluído, um defeito de uma linha que
destrói o projeto inteiro (F-07). Aqui a numeração é derivada e renumera a subárvore a
cada mudança (o portão executável do roadmap, F-12), a estrutura é árvore estrita no
domínio, e a exclusão de subárvore avisa quantificado e não toca no resto.

No encadeamento TOC, a S&T é a ferramenta de comunicação do plano — a ponte natural
com APR/AT existe, mas **vínculo automático fica fora** deste ciclo por decisão do
round 010 (F-11): entra a ferramenta completa e autônoma sobre o núcleo M1, a única
dependência técnica (a posição tardia no roadmap é escolha de valor registrada, F-12).

## O que entra como dado

- **Núcleo M1** ([`../004-nucleo-de-diagramas/spec.md`](../004-nucleo-de-diagramas/spec.md)):
  projeto, organização por tenant/usuário, exclusão suave, desfazer de sessão,
  exportação/importação, vista tabular. A S&T é um **tipo de projeto** sobre esse
  núcleo — mas de **estrutura de árvore estrita** (pai único, sem aresta livre), não de
  grafo: o modelo de domínio declara a diferença, como o M3 fez com a topologia fixa.
- **Escopo do round 010** ([`../../docs/produto/rounds.md`](../../docs/produto/rounds.md)):
  E5.1 e E5.2 completos; **fora**: qualquer vínculo automático com APR/AT (candidato a
  evolução, decisão nova); **sai primeiro** o E5.2 (status — fica a estrutura);
  **nunca saem** as três premissas por nó — "S&T sem premissa é organograma, e o modelo
  de dados da linhagem já as tinha" (F-11).
- **Decisão de resgate** (ADR 0005,
  [`../../docs/adr/0005-escopo-do-dominio-v1.md`](../../docs/adr/0005-escopo-do-dominio-v1.md)):
  a S&T fica na v1 — cortá-la faria a sucessora nascer menor que o protótipo que
  aposenta; a medição de presença na linhagem (16 arquivos) está colada lá (F-13).
- **Sem ação de IA neste ciclo**: o round 010 não declara assistência para a S&T, e
  esta spec a mantém fora — nenhuma ação `toc.*` nasce aqui (INT-04). Quando entrar, é
  decisão nova sob o ADR 0007.
- **Base sintética** (ADR 0006,
  [`../../docs/adr/0006-base-sintetica-desde-o-dia-1.md`](../../docs/adr/0006-base-sintetica-desde-o-dia-1.md)):
  toda fixture e jornada usa a S&T sintética da "Instituição Horizonte".

## Épicos, features e user stories

### E5.1 — Estrutura hierárquica

**F5.1.1 — Projeto S&T com meta global** — o contêiner: meta global (o `overallGoal`
da linhagem, F-03) + a árvore de passos, herdando o ciclo de vida do M1.

- US-01 — Como Facilitadora TOC, quero criar um projeto S&T declarando a meta global,
  para que toda a árvore decomponha um objetivo explícito.
  - Dado o tenant da Instituição Horizonte, Quando crio o projeto S&T "Dobrar a
    capacidade de atendimento" com a meta global preenchida, Então o projeto nasce
    vazio de passos, com a meta visível no topo da árvore.
- US-02 — Como Gestora, quero listar, arquivar e restaurar projetos S&T como qualquer
  projeto, para governar o acervo num lugar só.
  - Dado um projeto S&T arquivado, Quando o restauro, Então ele volta com passos,
    premissas e status intactos — a herança do M1 sem exceção.

**F5.1.2 — Passos com numeração derivada** — o passo nasce como filho de outro (ou
raiz) e o número 1/1.1/1.1.2 é **calculado da posição**, nunca digitado — o
contraexemplo é o campo obrigatório digitado à mão do v3 (F-05).

- US-03 — Como Facilitadora TOC, quero adicionar um passo como filho de outro e vê-lo
  numerado automaticamente, para nunca gerir numeração à mão.
  - Dado o passo 1.1 com dois filhos, Quando adiciono um terceiro filho, Então ele
    nasce como 1.1.3 — sem campo de número em lugar nenhum do formulário.
- US-04 — Como Participante, quero mover um passo (com a subárvore dele) para outro
  pai ou outra posição entre irmãos, para reorganizar o plano sem retrabalho.
  - Dado o passo 1.2 com filhos 1.2.1 e 1.2.2, Quando o movo para debaixo do passo 2,
    Então ele vira 2.1 (ou a posição escolhida), os filhos viram 2.1.1 e 2.1.2, e os
    antigos irmãos de 1.2 renumeram sem lacuna.
- US-05 — Como Facilitadora TOC, quero excluir um passo sabendo o tamanho do que cai
  junto, para nunca perder trabalho por engano.
  - Dado o passo 1.1 com 4 descendentes, Quando o excluo, Então o sistema pede
    confirmação dizendo "5 passos serão excluídos" e, confirmado, remove exatamente a
    subárvore — os demais passos permanecem e renumeram (o contraexemplo é o defeito
    da linhagem que descartava todos os outros, F-07).

**F5.1.3 — Estratégia, tática e as três premissas** — cada passo declara o quê
(estratégia), o como (tática) e as três premissas lógicas nas posições de leitura do
método.

- US-06 — Como Facilitadora TOC, quero registrar em cada passo a estratégia e a
  tática, para que o plano diga sempre o quê e o como no mesmo lugar.
  - Dado um passo novo, Quando preencho estratégia e tática, Então ambas aparecem no
    nó da árvore (estratégia em destaque) e na ficha do passo.
- US-07 — Como Participante, quero registrar as três premissas de um passo, para que a
  lógica do plano fique auditável — e desafiável — em cada elo.
  - Dado o passo 1.1 com pai 1 e filhos 1.1.1/1.1.2, Quando abro a ficha, Então vejo
    três campos com leitura dirigida: a premissa paralela ("o que, no contexto,
    sustenta este passo"), a de necessidade lida contra o pai ("para alcançar <1>, é
    necessário <1.1> porque…") e a de suficiência lida contra os filhos ("<1.1.1> e
    <1.1.2> bastam para <1.1> porque…").
- US-08 — Como Gestora, quero ver as pendências lógicas da árvore, para saber onde o
  plano ainda é organograma e não S&T.
  - Dado 3 passos sem premissa de necessidade e 1 passo com filhos sem premissa de
    suficiência, Quando abro o painel de pendências, Então cada pendência aparece
    nomeada com salto direto para o passo — e nada me impede de salvar mesmo assim.

### E5.2 — Status e acompanhamento

**F5.2.1 — Status por passo** — os quatro valores herdados da linhagem (F-03), com
evento e autoria.

- US-09 — Como Gestora, quero marcar o status de cada passo (Nenhum, Validado, Não
  Validado, Em Execução), para acompanhar a validação e a execução do plano na própria
  árvore.
  - Dado o passo 1.1 com status Nenhum, Quando o marco Validado, Então o nó muda de
    aparência (forma e rótulo, nunca só cor) e o evento guarda autor e data.

**F5.2.2 — Painel de acompanhamento** — a árvore como instrumento de reunião:
contagens por status, filtros, progresso.

- US-10 — Como Gestora, quero ver quantos passos estão em cada status e filtrar a
  árvore por status, para conduzir a reunião de acompanhamento sem planilha paralela.
  - Dado uma árvore com 12 passos, Quando filtro por "Em Execução", Então a árvore
    destaca os passos nesse status mantendo os ancestrais visíveis para dar contexto.

## Entidades e modelo de domínio

DDD puro — domínio sem framework, sem rede, sem relógio (P3). O M5 **estende** o modelo
do M1 por composição (o documento consolidado nasce na abertura do ciclo, T-02). A
diferença estrutural para o grafo do M1: a S&T é **árvore estrita** — cada passo tem no
máximo um pai, a posição entre irmãos é ordenada, e não existe aresta como entidade
independente (o contraexemplo é o v3 reusando `AraEdge` "por simplicidade", F-03).

- **ArvoreSnT** (agregado): o Projeto do M1 com `TipoDeFerramenta = snt`. Carrega a
  **MetaGlobal** (texto — o `overallGoal` da linhagem, F-03) e os **PassosSnT** em
  estrutura de árvore com raízes ordenadas.
- **PassoSnT** (entidade do agregado): pai opcional (ausente = raiz) + **posição
  ordinal entre irmãos** + estratégia (texto) + tática (texto) + as três premissas +
  status. **Não persiste número**: o número é derivado (RN-01).
- **NumeroDoPasso** (objeto de valor derivado): calculado pela função pura de numeração
  — raízes 1..n pela ordem; filhos de X são X.1..X.m pela ordem — determinístico e sem
  lacuna. Toda mutação estrutural (inserir, mover, excluir) renumera a subárvore
  afetada por construção (RN-01; o portão do roadmap, F-12).
- **PremissasDoPasso** (objeto de valor): `paralela` + `necessidade_ao_pai` +
  `suficiencia_dos_filhos`, os três campos de texto opcionais herdados do modelo da
  linhagem (F-03, F-04) — com as regras estruturais de pendência (RN-02): raiz não tem
  premissa de necessidade; suficiência ausente só é pendência quando há filhos.
- **StatusDoPasso** (enum): `nenhum` | `validado` | `nao_validado` | `em_execucao` —
  os quatro valores da linhagem, já em linguagem ubíqua portuguesa no próprio código de
  origem (F-03: `'Nenhum'`, `'Validado'`, `'Não Validado'`, `'Em Execução'`). Mudança
  com evento e autoria (RN-03).
- **PendenciasDaArvore** (serviço de domínio, função pura): computa as pendências
  lógicas — passo não-raiz sem premissa de necessidade, passo com filhos sem premissa
  de suficiência, passo sem estratégia ou sem tática — e as contagens por status. Não
  muta nada; sem rede e sem modelo.
- **Eventos de domínio** (somente-acréscimo, além dos do M1): `ArvoreCriada`,
  `MetaGlobalEditada`, `PassoAdicionado`, `PassoEditado`, `PassoMovido`,
  `SubarvoreExcluida` (com contagem), `PremissasEditadas`, `StatusMudou`.
- **Fora do domínio**: layout e posições de tela (a árvore desenha-se da estrutura —
  as `pos_x`/`pos_y` livres da linhagem, F-03, não são portadas); a categoria da
  linhagem (`Estratégia`/`Tática`/`VCD`/`BUILD`/`LEVERAGE` — F-03) **não é portada**:
  com estratégia e tática como campos do próprio passo, a classificação perde a função
  (L-01, [DÚVIDA] 1); vínculo com APR/AT (fora do round — F-11); prompts e provedores
  (nenhuma ação de IA neste ciclo — INT-04).

## Requisitos funcionais

### Projeto S&T com meta global

RF-01: O SISTEMA DEVE permitir criar projeto do tipo S&T com meta global obrigatória,
herdando do M1 listagem, isolamento por inquilino, exclusão suave, restauração e
exportação/importação sem reimplementação. [F-03] 🟡

RF-02: O SISTEMA DEVE permitir editar a meta global com evento próprio
(`MetaGlobalEditada`). 🟡

RF-03: QUANDO um projeto S&T for excluído, O SISTEMA DEVE aplicar a exclusão suave do
M1 arquivando os passos junto; a restauração devolve a árvore inteira com premissas e
status. 🟡

### Passos com numeração derivada

RF-04: O SISTEMA DEVE permitir adicionar passo como raiz ou como filho de um passo
existente, em posição escolhida entre os irmãos (padrão: última) — e o número
hierárquico do passo DEVE ser derivado da posição pela função pura de numeração, nunca
informado pelo usuário (RN-01; o contraexemplo é o campo digitado sem validação do v3,
F-05). 🟡

RF-05: O SISTEMA DEVE apresentar a numeração no formato hierárquico da linhagem — 1,
1.1, 1.1.2 (F-03) — em todo lugar onde o passo aparece: nó, ficha, tabela, exportação. 🟡

RF-06: O SISTEMA NÃO DEVE expor, em nenhum formulário ou API de escrita, campo de
número de passo — numeração é saída, nunca entrada (RN-01). 🟡

RF-07: QUANDO um passo for inserido, movido ou excluído, O SISTEMA DEVE renumerar a
subárvore afetada de forma determinística e sem lacuna — irmãos seguintes decrementam
ou incrementam, descendentes recebem o prefixo novo (o portão executável do roadmap,
F-12). 🟡

RF-08: O SISTEMA DEVE permitir mover um passo com toda a sua subárvore para outro pai
ou outra posição entre irmãos, preservando estratégia, tática, premissas e status de
cada descendente; mover para dentro da própria subárvore é recusado no domínio
(RN-04). 🟡

RF-09: QUANDO um passo com descendentes for excluído, O SISTEMA DEVE informar a
contagem total no ato de confirmar ("N passos serão excluídos") e remover exatamente a
subárvore — nenhum passo fora dela é tocado (RN-05; o contraexemplo é o defeito de
exclusão da linhagem, F-07). 🟡

RF-10: O SISTEMA DEVE manter a estrutura como árvore estrita no domínio: cada passo
tem no máximo um pai, não existe aresta como dado independente, e ciclo é impossível
por construção (RN-04; o contraexemplo é o reuso de `AraEdge` com conexão livre do v3,
F-03). 🟡

### Estratégia, tática e premissas

RF-11: O SISTEMA DEVE manter, por passo, estratégia (o quê) e tática (como) como
campos de texto distintos e editáveis, com a estratégia obrigatória para criar o passo
e a tática podendo nascer vazia (pendência, não bloqueio). [F-03; L-01] 🟡

RF-12: O SISTEMA DEVE manter, por passo, as três premissas lógicas como campos de
texto opcionais — paralela, de necessidade ao pai, de suficiência dos filhos — os
mesmos três campos do modelo da linhagem (F-03, F-04), promovidos de opcionais
esquecidos a cidadãos com leitura dirigida e pendência visível (RN-02). 🟡

RF-13: O SISTEMA DEVE apresentar cada premissa com a leitura dirigida montada dos
textos atuais: a de necessidade contra o pai ("Para alcançar <estratégia do pai>, é
necessário <estratégia do passo> porque <premissa>") e a de suficiência contra os
filhos nomeados — a paralela lê-se sozinha, como pressuposto de contexto. 🟡

RF-14: O SISTEMA DEVE computar as pendências lógicas da árvore por função pura
(PendenciasDaArvore): passo não-raiz sem premissa de necessidade, passo com filhos sem
premissa de suficiência, passo sem tática — apresentadas como pendência com salto
direto, nunca como trava de gravação (RN-02, RN-06). 🟡

RF-15: O SISTEMA DEVE permitir editar estratégia, tática e premissas por manipulação
direta na ficha do passo e pela vista tabular, aplicando na hora com traço — os três
testes do item 8 da constituição valem. 🟡

### Status e acompanhamento

RF-16: O SISTEMA DEVE manter o status de cada passo entre os quatro valores da
linhagem — `nenhum`, `validado`, `nao_validado`, `em_execucao` (F-03) — com mudança
registrando autor e data por evento (RN-03). 🟡

RF-17: O SISTEMA DEVE apresentar o painel de acompanhamento do projeto: contagem de
passos por status, pendências lógicas (RF-14) e progresso — computados da mesma função
pura, nunca de dado paralelo. 🟡

RF-18: O SISTEMA DEVE permitir filtrar a árvore por status mantendo os ancestrais dos
passos filtrados visíveis como contexto. 🟡

### Vista tabular, desfazer e exportação

RF-19: O SISTEMA DEVE oferecer a vista tabular indentada da árvore — número,
estratégia, tática, premissas (presença), status — com paridade de edição com a ficha
do passo (o padrão de paridade do M1/M3). 🟡

RF-20: O SISTEMA DEVE cobrir toda mutação do módulo (passo, premissas, status, mover,
excluir subárvore) pelo desfazer de sessão herdado do M1, sem exceção nova — inclusive
a exclusão de subárvore inteira. 🟡

RF-21: O SISTEMA DEVE exportar e importar o projeto S&T completo pelo E1.4 do M1 —
meta global, passos com posição estrutural (pai + ordem), estratégia, tática,
premissas e status — sem perda em ida e volta; a numeração NÃO é exportada como dado:
deriva na importação, e divergência entre estrutura e numeração é impossível por
construção (RN-01). 🟡

## Requisitos de interface

RI-01: A árvore S&T desenha-se da estrutura, de cima para baixo — meta global no topo,
raízes na primeira linha, filhos abaixo dos pais — com layout calculado: o usuário
ordena e move passos, não arruma caixas (as `pos_x`/`pos_y` livres da linhagem não são
portadas — F-03). 🟡

RI-02: O nó do passo apresenta número, estratégia (truncada com título completo
acessível) e status — o status distinguível por forma e rótulo, nunca só por cor (a
paleta por status da linhagem, F-09, é referência de intenção, não de contraste). 🟡

RI-03: A ficha do passo apresenta as três premissas **nas posições de leitura**: a de
necessidade visualmente ligada ao pai (acima), a de suficiência ligada aos filhos
nomeados (abaixo), a paralela ao lado — a ficha ensina o método pela disposição
(F-06: o v3 já tinha os três campos, empilhados sem leitura). 🟡

RI-04: Adicionar passo é ação contextual do nó ("adicionar filho", "adicionar irmão
abaixo") — nunca formulário com campo de número (RF-06). 🟡

RI-05: Mover passo oferece arrastar na árvore **e** comando explícito na ficha
("mover para…"), com pré-visualização da renumeração antes de confirmar. 🟡

RI-06: A confirmação de exclusão de subárvore mostra a contagem (RF-09) e o primeiro
nível do que cai — desfazer de sessão anunciado na própria confirmação. 🟡

RI-07: O painel de acompanhamento (RF-17) apresenta contagens por status como filtros
acionáveis e as pendências lógicas com salto direto ao passo. 🟡

RI-08: A vista tabular indentada (RF-19) preserva a hierarquia visual por indentação e
mantém a numeração como primeira coluna, ordenação estrutural fixa. 🟡

RI-09: Toda superfície do módulo respeita tema do hospedeiro com fallback, modo
só-conteúdo e operação por teclado, herdados dos ciclos 002/003; textos por i18n
pt/en, inclusive os quatro status e os rótulos das três premissas. 🟡

## Requisitos não funcionais

RNF-01: A função de numeração, a renumeração por mutação estrutural, as invariantes de
árvore estrita e as PendenciasDaArvore são domínio puro testável sem rede, sem banco e
sem modelo — a suíte de domínio roda offline por construção (P3, P4). 🟡

RNF-02: A fronteira hexagonal é verificada por `import-linter`: o pacote de domínio do
M5 não importa framework, HTTP, banco nem cliente de IA — o build falha na violação. 🟡

RNF-03: Toda mutação do módulo emite traço OTel correlacionado e log estruturado
(P5). 🟡

RNF-04: Abrir uma árvore S&T de 100 passos em 5 níveis renderiza em menos de 1 segundo
no percentil 95; mover uma subárvore de 20 passos renumera e responde em menos de 500
milissegundos — medidos na jornada viva. 🟡

RNF-05: A numeração é determinística: duas execuções sobre a mesma estrutura devolvem
os mesmos números — propriedade coberta por teste (inclusive baseado em propriedades,
se a suíte do M1 já o usar). 🟡

RNF-06: A fixture de demonstração e a jornada usam exclusivamente a S&T sintética da
"Instituição Horizonte" — grep negativo de nome real de pessoa no CI (ADR 0006). 🟡

RNF-07: Nenhum prompt, chave ou cliente de provedor no repositório do produto — grep
de CI herdado dos ciclos anteriores (P7, ADR 0007); este módulo não declara nenhuma
ação de catálogo (INT-04). 🟡

RNF-08: Textos de status, rótulos de premissa e leituras dirigidas saem do mecanismo
de i18n com chave estável ligada à regra (RN-NN) — rastreabilidade spec ↔ código ↔
tela. 🟡

## Regras de negócio

RN-01: **Numeração é derivada, nunca dado**: raízes numeram 1..n pela ordem; filhos de
um passo X numeram X.1..X.m pela ordem; a função é determinística e sem lacuna, e toda
mutação estrutural renumera a subárvore afetada. Não existe campo de número editável
nem persistido como verdade. [F-05 é o contraexemplo; F-12 fixa o portão] 🟡

RN-02: As três premissas têm papel estrutural fixo: **paralela** (pressuposto de
contexto — lê-se sozinha), **necessidade ao pai** (não se aplica a raiz; pendência
quando ausente em passo não-raiz), **suficiência dos filhos** (só significa algo com
filhos; pendência quando há filhos e está ausente). São os três campos do modelo da
linhagem, com semântica agora normativa. [F-03, F-04] 🟢 (os três campos existem
verbatim em `tocbuilderv3/types.ts:293-295` e desde a 1ª geração em
`TOC-Builder/types.ts:243-245`; a semântica estrutural é 🟡)

RN-03: Status do passo é um dos quatro valores da linhagem — `nenhum`, `validado`,
`nao_validado`, `em_execucao` — com transição livre entre eles e evento com autor e
data a cada mudança (restringir transições é [DÚVIDA] 2). [F-03] 🟢 (os quatro valores
verbatim em `tocbuilderv3/types.ts:270-275`, já em português; a política de transição
é 🟡)

RN-04: A S&T é **árvore estrita**: no máximo um pai por passo, ordem explícita entre
irmãos, ciclo impossível por construção (mover para a própria subárvore é recusado no
domínio). Não existe aresta como entidade. [F-03 é o contraexemplo] 🟡

RN-05: Exclusão de passo é exclusão da subárvore inteira, com contagem informada antes
de confirmar e evento `SubarvoreExcluida` com a contagem; passos fora da subárvore são
invioláveis pela operação. [F-07 é o contraexemplo] 🟡

RN-06: Pendência lógica informa e prioriza, nunca trava: árvore sem premissa grava-se
— mas o painel diz onde ela ainda é organograma ("S&T sem premissa é organograma" —
F-11: as premissas são o "nunca sai" do round). 🟡

## Integrações

INT-01: O M5 consome do M1 (ciclo 004) projeto, tenant/usuário, exclusão suave,
desfazer de sessão, exportação/importação e vista tabular; consome da junta 003
identidade (`POST /auth/introspect`), isolamento por inquilino e OTel. Nada disso é
reimplementado — é a única dependência técnica do módulo (F-12). 🟡

INT-02: Telas deste módulo entram no registro de telas do E7.5 com identificador
estável (`toc.snt_arvore`, `toc.snt_passo`, `toc.snt_tabela`,
`toc.snt_acompanhamento`), no formato do ciclo 006; meta global, estratégia, tática e
premissas marcam `ai_visible` campo a campo para o snapshot sanitizado — texto de
usuário é sempre camada não-confiável (item 7 da constituição). 🟡

INT-03: **Importação da 4ª geração** (execução: ciclo 011, E1.4 avançado): o export
S&T do `tocbuilderv3` traz `stepNumber` digitado e arestas livres (F-03, F-05); o
importador do 011 reconstrói pai/ordem a partir de arestas e números, deriva a
numeração e **recusa com relato campo a campo** quando a estrutura não fecha
(inconsistência entre número digitado e aresta, número duplicado, ciclo). Este ciclo
entrega o modelo que torna essa reconstrução possível; o importador é do 011 (L-04). 🟡

INT-04: **Nenhuma ação `toc.*` nasce neste ciclo** — declaração explícita, não
omissão: o round 010 não inclui assistência de IA para a S&T, e vínculo automático com
APR/AT está fora (F-11). Assistência futura entra por decisão nova sob o ADR 0007 e a
FSM do ciclo 006. 🟡

## Telas e fluxos

### 6.1 Árvore S&T — Job: decompor a meta em passos numerados e acompanhar de uma
olhada · Campos: meta global, nós com número + estratégia + status, pendências ·
Ações: adicionar filho/irmão, mover (arrastar com pré-visualização de renumeração),
excluir subárvore (com contagem), abrir ficha, filtrar por status.

### 6.2 Ficha do passo — Job: declarar o quê, o como e os porquês de um passo ·
Campos: número (somente leitura), estratégia, tática, as três premissas nas posições
de leitura, status, pai e filhos nomeados · Ações: editar campos (direta), mudar
status, mover para…, adicionar filho.

### 6.3 Vista tabular — Job: revisão e edição em reunião, sem canvas · Campos: tabela
indentada — número, estratégia, tática, presença de premissas, status · Ações: as
mesmas da ficha, em tabela (paridade RF-19).

### 6.4 Painel de acompanhamento — Job: conduzir a reunião de acompanhamento ·
Campos: contagens por status, pendências lógicas com salto, progresso · Ações: filtrar
por status, saltar ao passo pendente.

## Fora de escopo

- **Qualquer vínculo automático com APR/AT** — a ponte lógica entre o plano e a
  implementação existe e está dita no "O quê e por quê", mas automatizá-la é **candidato a
  evolução, decisão nova**, pelo *Fora* do round 010
  ([`../../docs/produto/rounds.md`](../../docs/produto/rounds.md)). Este ciclo entrega a
  ferramenta completa e autônoma sobre o núcleo M1.
- **Assistência de IA sobre a árvore** — nenhuma ação `toc.*` nasce neste ciclo, e a INT-04
  declara isso explicitamente para ninguém procurar. O round 010 não pede assistência para
  a S&T; quando ela entrar, é decisão nova sob o ADR 0007
  ([`../../docs/adr/0007-ia-somente-pela-fundacao.md`](../../docs/adr/0007-ia-somente-pela-fundacao.md)).
- **Numeração digitada à mão** — não é escopo adiado, é defeito da linhagem que não
  atravessa (F-05): o número é **derivado** da posição na árvore e renumera a subárvore a
  cada mudança. Oferecer numeração manual junto seria manter vivo o defeito que este ciclo
  existe para corrigir.
- **Importação das árvores S&T da quarta geração** — a INT-03 já a delega: o adaptador de
  formato legado é o E1.4 avançado, ciclo 011
  ([`../011-fundacoes-da-aplicacao/spec.md`](../011-fundacoes-da-aplicacao/spec.md)). Aqui
  entra só o JSON canônico do núcleo.
- **Exportar a árvore para formato de apresentação** — slide, planilha, documento de texto.
  A S&T é a ferramenta de comunicação do plano e a demanda é previsível; ainda assim a
  exportação deste ciclo é o JSON canônico do M1, e cada formato novo é decisão nova, com
  o seu custo de manutenção declarado.
- **Prazo, responsável e percentual de conclusão por passo** — o E5.2 entrega os quatro
  valores de status herdados da linhagem e nada além. Acompanhar quem faz o quê e quando é
  o produto da irmã `gestaodeprioridades`, não esta v1.

## Entregáveis

- Domínio Python puro do M5: agregado ArvoreSnT, PassoSnT com posição estrutural,
  função pura de numeração com renumeração por mutação, PremissasDoPasso com regras de
  pendência, StatusDoPasso, PendenciasDaArvore — testes de domínio **sem rede e sem
  modelo** nascidos antes do código (P4), sobre fixture sintética da "Instituição
  Horizonte" com 3 níveis.
- Casos de uso + adaptadores REST; migrações Alembic com downgrade (árvore, passo,
  premissas, status).
- Interface React: árvore S&T, ficha do passo, vista tabular, painel de
  acompanhamento — sobre o `ux-design.md` do ciclo 002 (complementado se a S&T não
  tiver sido prototipada lá — ver Clarify).
- Jornada viva (P6): a S&T sintética da Instituição Horizonte com **três níveis**
  (o portão do roadmap, F-12) — criar meta, decompor, premissas nos três papéis, mover
  subárvore com renumeração, status em reunião — com captura gerada por script
  versionado do build real e avaliação heurística datada.
- Entradas de CHANGELOG; ADR novo se decisão material surgir (candidata: não portar a
  categoria da linhagem — ver Clarify).

## Critérios de aceite (DoD)

| # | Critério | Verificação executável |
|---|---|---|
| 1 | Domínio do M5 puro, offline | `pytest tests/domain/test_snt.py -p no:cacheprovider` verde com rede desabilitada + `lint-imports` código 0 |
| 2 | Numeração derivada e determinística (RN-01) | `pytest tests/domain/test_numeracao.py -v` — 1/1.1/1.1.2 pela posição; mesma estrutura → mesmos números |
| 3 | Renumeração da subárvore ao inserir/remover/mover (portão do roadmap) | `pytest tests/domain/test_numeracao.py -k "renumera" -v` — irmãos sem lacuna; descendentes com prefixo novo |
| 4 | Número nunca é entrada (RF-06) | `grep -rn "stepNumber\|numero_do_passo" backend/src/aplicacao/ frontend/src/ \| grep -i "input\|request\|form" \| wc -l` = 0 |
| 5 | As três premissas persistidas e regras de pendência (portão do roadmap) | `pytest tests/domain/test_premissas.py -v` — raiz sem necessidade não é pendência; filhos sem suficiência é; ida e volta ao banco |
| 6 | Árvore estrita: sem ciclo, um pai (RN-04) | `pytest tests/domain/test_snt.py -k "arvore_estrita" -v` — mover para a própria subárvore recusado |
| 7 | Excluir subárvore não toca no resto (RN-05) | `pytest tests/domain/test_snt.py -k "exclusao_subarvore" -v` — contagem exata; demais passos byte a byte intactos (o defeito F-07 como caso de teste) |
| 8 | Status com evento (RN-03) | `pytest tests/domain/test_status.py -v` — os 4 valores; mudança registra autor e data |
| 9 | Pendências e contagens por função pura (RF-14, RF-17) | `pytest tests/domain/test_pendencias.py -v` — a saída diz quantos passos examinou (R2) |
| 10 | Exportação sem perda; numeração deriva na importação (RF-21) | `pytest tests/application/test_export_snt.py -k "ida_e_volta"` — igualdade estrutural; nenhum número no payload |
| 11 | Toda mutação nova com traço | `pytest tests/integration/test_traco_m5.py` — falha se `PassoAdicionado`, `PassoMovido`, `SubarvoreExcluida`, `StatusMudou` não emitirem traço |
| 12 | Sem SDK, chave, prompt ou ação de catálogo no módulo | `grep -rniE "genai\|openai\|anthropic\|api[_-]?key" backend/ frontend/src/ \| wc -l` = 0 **e** `grep -rn "toc\." contracts/ \| grep -c snt` = 0 |
| 13 | Desempenho da árvore e do mover (RNF-04) | medição da jornada viva colada: p95 de abertura (100 passos) < 1 s; mover subárvore de 20 < 500 ms |
| 14 | Jornada viva de três níveis | `ls docs/jornadas/` contém a jornada do M5 com capturas geradas por script; grep negativo de nome real de pessoa |
| 15 | Conformidade do ciclo | `scripts/check-conformance.sh 010` código 0 |
| 16 | Caminhos e links | `scripts/check-caminhos.sh` e `scripts/check-links.sh` código 0 + quanto examinaram |

## Fontes

F-01: /home/user/TOC-Builder/components/Sidebar.tsx:44 — a S&T **habilitada** na 1ª
geração: `{ id: 'snt', label: 'Árvore S&T', icon: <SnTIcon />, view: 'SNT_TREE' }` —
sem flag `disabled`, ao contrário de NC/ARF/APR/AT nas linhas 45-48, todas
`disabled: true` 🟢

F-02: a regressão medida geração a geração, executada em 2026-09-03 (`grep -n "'snt'"
<geração>/components/Sidebar.tsx`): `TOC-Builder-APP/components/Sidebar.tsx:44` sem
`disabled` (2ª geração, habilitada); `TOC-Builder-V2/components/Sidebar.tsx:56` com
`disabled: true` (3ª); `tocbuilderv3/components/Sidebar.tsx:58` com `disabled: true`
(4ª) — habilitada→habilitada→desligada→desligada, sem decisão registrada em lugar
nenhum 🟢

F-03: /home/user/tocbuilderv3/types.ts:270-311 — o modelo completo parado no código:
`SnTStepStatus` com 4 valores em português (l.270-275; `sed -n '270,275p' types.ts |
grep -c "="` → `4`), `SnTStepCategory` com 6 valores (l.277-284; mesmo grep → `6`),
`stepNumber: string; // e.g., "1", "1.1", "1.1.2"` digitado como texto livre (l.288),
as **três premissas** `parallelAssumption` / `necessaryAssumptionToParent` /
`sufficiencyOfChildrenAssumption` (l.293-295), posições livres `pos_x`/`pos_y`
(l.296-297) e `SnTProject` com `overallGoal` e `edges: AraEdge[] // Reusing AraEdge
for simplicity` (l.302-311) 🟢

F-04: /home/user/TOC-Builder/types.ts:237-245 — o mesmo modelo já na **1ª geração**:
`SnTStepNodeData` com `stepNumber` (l.239) e os três campos de premissa (l.243-245) —
as três premissas não são invenção tardia, nasceram com a ferramenta 🟢

F-05: /home/user/tocbuilderv3/components/SnTStepEditorModal.tsx:56-57 — o número
digitado à mão: `if (!stepNumber.trim()) newErrors.stepNumber = "O número do passo é
obrigatório.";` seguido do comentário `// Optionally, add validation for stepNumber
format or uniqueness against existingStepNumbers` — obrigatório, texto livre, sem
validação de formato nem unicidade; o RN-01 é a resposta 🟢

F-06: /home/user/tocbuilderv3/components/SnTStepEditorModal.tsx:137-159 — as três
premissas editáveis em três áreas de texto (`grep -c 'id="snt[A-Za-z]*Assumption"'
components/SnTStepEditorModal.tsx` → `3`: `sntParallelAssumption`,
`sntNecessaryAssumption`, `sntSufficiencyAssumption`) — empilhadas, sem leitura
dirigida contra pai e filhos; o RI-03 promove a disposição 🟢

F-07: /home/user/tocbuilderv3/services/mockApiService.ts:521 — o defeito de exclusão:
`project.nodes = project.nodes.filter(n => n.id === nodeId);` — o filtro **mantém só o
nó excluído** e descarta todos os outros passos do projeto (o predicado correto seria
`!==`); excluir um passo destruía a árvore inteira. Vira o caso de teste da DoD 7 🟢

F-08: /home/user/tocbuilderv3/services/mockApiService.ts:417-580 — a superfície CRUD
da linhagem: 10 funções S&T (`grep -c "SnT.*= async" services/mockApiService.ts` →
`10` — criar/carregar/listar/excluir projeto, nó e aresta, atualizar detalhes) e
**nenhuma delas calcula, valida ou renumera** numeração — a numeração era
integralmente responsabilidade do usuário 🟢

F-09: /home/user/tocbuilderv3/constants.ts:430-449 — `SNT_NODE_COLORS`: paleta por
status (l.438-441) e por categoria (l.444-449) — a intenção visual de distinguir
status na árvore, herdada como intenção (RI-02 exige forma e rótulo, nunca só cor) 🟢

F-10: [`../../docs/produto/visao.md`](../../docs/produto/visao.md) §6, defeito D-05 —
"A S&T é a única ferramenta que regrediu", com as quatro linhas de Sidebar citadas e o
veredito: "Funcionalidade que regride sem decisão registrada é exatamente o que um ADR
existe para impedir" 🟢

F-11: [`../../docs/produto/rounds.md`](../../docs/produto/rounds.md) — Round 010:
aptidão executável (renumeração da subárvore por teste de domínio; três premissas
persistidas e exibidas; jornada com captura), **fora** (vínculo automático com
APR/AT), **sai primeiro** (E5.2), **nunca saem** (as três premissas — "S&T sem
premissa é organograma") 🟢

F-12: [`../../docs/roadmap.md`](../../docs/roadmap.md) — Ciclo 010: portões (teste de
renumeração; premissas persistidas; jornada de três níveis com captura) e a
pré-condição única ("O ciclo 004 promovido… a posição tardia é escolha de valor
registrada") 🟢

F-13: [`../../docs/adr/0005-escopo-do-dominio-v1.md`](../../docs/adr/0005-escopo-do-dominio-v1.md)
— alternativa descartada "Cortar S&T da v1": a ferramenta existe na linhagem (16
arquivos do `tocbuilderv3` citam `SnT`, medição colada lá) e cortá-la faria a
sucessora nascer menor que o protótipo que aposenta 🟢

## Lacunas e assunções

L-01: A linhagem modelava um texto por passo (`strategyText`) mais uma categoria de 6
valores (F-03); o método S&T pede estratégia **e** tática por passo. Assunção:
estratégia e tática como campos distintos, e a categoria **não portada** — com os dois
campos no passo, classificar o nó como "Estratégia" ou "Tática" perde a função, e
VCD/BUILD/LEVERAGE são jargão sem uso registrado na linhagem além do enum e das cores
(F-03, F-09). Risco **baixo** (adicionar uma classificação depois é campo opcional);
a decisão vai a ADR se o gate a confirmar ([DÚVIDA] 1).

L-02: A linhagem não restringia transições de status (nem registrava quem mudou).
Assunção: transição livre entre os 4 valores com evento (RN-03) — impor FSM (ex.:
`em_execucao` só depois de `validado`) travaria reuniões reais em que o plano executa
antes de validar formalmente. Risco **baixo**; [DÚVIDA] 2.

L-03: A linhagem não tinha ordem entre irmãos — os nós flutuavam por `pos_x`/`pos_y`
(F-03) e o número digitado carregava a ordem implícita. Assunção: ordem ordinal
explícita e persistida por irmão, fonte única da numeração (RN-01). Risco **baixo** —
é a estrutura mínima que torna a numeração derivável.

L-04: A importação dos exports S&T da 4ª geração (ciclo 011, INT-03) vai encontrar
`stepNumber` livre possivelmente inconsistente com as arestas. Assunção: o modelo
deste ciclo (pai + ordem) é reconstruível de número + aresta na maioria dos casos, e o
importador recusa com relato os demais — nunca importa estrutura ambígua em silêncio.
Risco **médio**, pago no 011; o que este ciclo deve ao 011 é só o modelo estável.

L-05: Múltiplas raízes são permitidas (numeradas 1..n), embora a prática canônica da
S&T seja uma raiz sob a meta global. Assunção: permitir e apontar pendência estilística
custaria mais que aceitar — planos reais começam por listas de frentes. Risco
**baixo**; [DÚVIDA] 3.

## Clarify

- [DÚVIDA] Categoria da linhagem (L-01): confirmar que `SnTStepCategory`
  (Estratégia/Tática/VCD/BUILD/LEVERAGE) **não** é portada, com ADR registrando — ou o
  Product Steward quer a classificação além dos campos estratégia/tática?
- [DÚVIDA] Transições de status (L-02): livres entre os 4 valores, como a spec assume,
  ou com restrição (ex.: `em_execucao` exige `validado` antes)?
- [DÚVIDA] Raízes múltiplas (L-05): permitidas como a spec assume, ou uma raiz única
  obrigatória sob a meta global?
- [DÚVIDA] Tática obrigatória: a spec exige estratégia na criação e deixa tática como
  pendência (RF-11) — o Product Steward confirma, ou tática também obrigatória?
- [DÚVIDA] Telas do M5 no ciclo 002: o protótipo cobriu RIs de M1–M3; se a árvore S&T
  não tiver desenho lá, o `ux-design.md` complementar nasce neste ciclo (mesmo arranjo
  do M6) — confirmar no gate.
