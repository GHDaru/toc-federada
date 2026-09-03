# Spec 004 — Núcleo de diagramas (M1 — Núcleo de Diagramas Lógicos)

> Siglas: TOC — Teoria das Restrições · APH — Aplicação ↔ Harness · ADR — Architecture
> Decision Record (Registro de Decisão Arquitetural) · RF/RI/RNF/RN/INT — requisito
> funcional / de interface / não funcional / regra de negócio / integração · US — User
> Story (história de usuário) · CRUD — criar, ler, atualizar, excluir · DDD —
> Domain-Driven Design (Design Orientado a Domínio) · TDD — Test-Driven Development
> (desenvolvimento guiado por teste) · DoD — Definition of Done (Definição de Pronto) ·
> UDE — Undesirable Effect (Efeito Indesejável) · ARA — Árvore da Realidade Atual · NC —
> Nuvem de Conflito · S&T — Árvore de Estratégia & Táticas · IA — inteligência
> artificial · OTel — OpenTelemetry · API — Application Programming Interface (interface
> de programação) · JSON — JavaScript Object Notation · UUID — Universally Unique
> Identifier (identificador único universal) · i18n — internacionalização · REST —
> Representational State Transfer · FSM — máquina de estados finitos · UI — interface de
> usuário

- **Status**: Rascunho (aprovação: gate humano do ciclo 001)
- **Raia**: plena
- **Data**: 2026-09-03
- **Origem**: [`../../docs/produto/modulos.md`](../../docs/produto/modulos.md) (M1) ·
  [`../../docs/roadmap.md`](../../docs/roadmap.md) (ciclo 004) ·
  [`../../docs/produto/rounds.md`](../../docs/produto/rounds.md) (round 004)

## O quê e por quê

O M1 é **tudo o que é comum às seis ferramentas de pensamento da TOC** — projeto, nó,
aresta causal, o canvas e a sua vista tabular equivalente — existindo **uma vez**. Na
linhagem TOC-Builder, cada ferramenta carregava a sua própria cópia de canvas, painel e
serviço de dados; o M1 é a fatoração que impede a sétima cópia. Ele não conhece nenhuma
semântica TOC (UDE, premissa, injeção — isso é M2 em diante): conhece grafos dirigidos
com nós tipáveis e arestas causais, e as operações que qualquer ferramenta faz sobre
eles.

O porquê está medido na linhagem. Toda a "persistência" do v3 era um vetor em memória
(`let projects: AraProject[] = []` — F-04); recarregar a página perdia tudo, salvo um
único autosave em `localStorage` que cobria só a sessão ARA aberta (F-09). A exclusão era
destrutiva e imediata (F-05) — e a de nó da S&T tinha o filtro invertido, apagando todos
os nós **menos** o excluído (F-06), defeito que quatro gerações sem teste nunca pegaram.
A API real foi especificada em 20 endpoints e implementada em zero (F-07). Desfazer não
existia: zero ocorrências de `undo`/`desfazer` no código (F-17). Este ciclo entrega o
contrário disso tudo, com TDD desde a primeira linha: persistência real por (inquilino,
usuário), exclusão suave reversível, desfazer de sessão, e a dupla canvas + vista tabular
que a linhagem provou ser o que torna projetos grandes utilizáveis (F-08).

No encadeamento TOC, o M1 é a fundação de M2–M6: a ARA, a NC, as árvores de futuro e a
S&T são **tipos de projeto** sobre este núcleo, cada uma acrescentando entidades e regras
próprias sem reimplementar grafo, canvas, tabela ou exportação.

## O que entra como dado

- **Stack** (ADR 0002, [`../../docs/adr/0002-stack-herdada-da-irma.md`](../../docs/adr/0002-stack-herdada-da-irma.md)):
  React+TypeScript/Vite no cliente, FastAPI/Python no serviço, PostgreSQL Neon próprio,
  OTel de nascença.
- **Federação** (ADR 0003, [`../../docs/adr/0003-federacao-aph-nivel-2-embedded.md`](../../docs/adr/0003-federacao-aph-nivel-2-embedded.md)):
  identidade por `POST /auth/introspect`; nenhum login próprio. O M1 **consome** a junta
  fechada no ciclo 003 (E7.1 identidade, E8.1 persistência) — não a constrói.
- **Alcance do P2 e item 8** (constituição própria,
  [`../../docs/governance/constitution.md`](../../docs/governance/constitution.md),
  linhas 64–96 — F-12): manipulação direta pelo titular do dado aplica na hora sob três
  testes, e paga em traço e reversibilidade; fora deles, `action_proposal`.
- **Desfazer de sessão vs reverter de domínio** (padrão pago pela irmã no ADR 0013 dela —
  F-13): pilha de sessão sem teto, episódio ≠ clique, recarregar mata a pilha, o que já
  gravou se recupera por ação de domínio nomeada, traço somente-acréscimo com evento
  compensatório.
- **Base sintética** (ADR 0006, [`../../docs/adr/0006-base-sintetica-desde-o-dia-1.md`](../../docs/adr/0006-base-sintetica-desde-o-dia-1.md)):
  toda fixture, exemplo e captura deste ciclo usa personas fictícias ("Instituição
  Horizonte", "Facilitadora TOC").
- **Escopo v1** (ADR 0005, [`../../docs/adr/0005-escopo-do-dominio-v1.md`](../../docs/adr/0005-escopo-do-dominio-v1.md)):
  nada de semântica TOC neste módulo; importação dos formatos da linhagem fica para o
  E1.4 avançado (ciclo 011).
- **Corte de apetite** (round 004,
  [`../../docs/produto/rounds.md`](../../docs/produto/rounds.md) — F-14): se o ciclo
  estourar, **sai primeiro o desfazer de sessão** (o modelo fica preparado); **nunca sai**
  a vista tabular equivalente.
- **Forma das telas**: o protótipo e o `ux-design.md` do ciclo 002
  ([`../002-prototipo-de-interfaces/spec.md`](../002-prototipo-de-interfaces/spec.md))
  decidem forma; esta spec decide comportamento.

## Épicos, features e user stories

### E1.1 — Projetos e organização

**F1.1.1 — CRUD de projetos** — criar, listar, abrir e editar metadados de projetos de
diagrama, por (inquilino, usuário), com o tipo de ferramenta declarado na criação.

- US-01 — Como Facilitadora TOC, quero criar um projeto nomeado com descrição do
  problema, para começar uma análise que não se perde ao fechar o navegador.
  - Dado que estou autenticada pela fundação, Quando crio o projeto "Atrasos na
    Instituição Horizonte" do tipo genérico, Então ele aparece na minha lista, persiste
    no servidor e reabre com o mesmo conteúdo após recarregar a página.
- US-02 — Como Gestora, quero ver a lista dos projetos do meu inquilino com data de
  última alteração, para acompanhar o que as análises produziram.
  - Dado que existem projetos de dois usuários do meu inquilino, Quando abro a lista,
    Então vejo os que minhas capacidades permitem, ordenados por última alteração, e
    nenhum projeto de outro inquilino.

**F1.1.2 — Exclusão suave e restauração** — excluir move para a lixeira; restaurar traz
de volta; nada se perde por um clique.

- US-03 — Como Facilitadora TOC, quero excluir um projeto errado e poder restaurá-lo,
  para que um engano não custe uma análise inteira.
  - Dado um projeto na minha lista, Quando o excluo, Então ele sai da lista, aparece na
    lixeira com data de exclusão, e Quando o restauro, Então volta à lista com nós e
    arestas intactos.
- US-04 — Como Administradora do tenant, quero esvaziar a lixeira com confirmação
  explícita, para liberar o que ninguém vai restaurar.
  - Dado um projeto na lixeira, Quando peço exclusão definitiva, Então o sistema exige
    confirmação nomeando o projeto (efeito irreversível — falha o 3º teste do item 8) e
    só então remove.

**F1.1.3 — Isolamento e papéis** — cada projeto pertence a um (inquilino, usuário); o
acesso responde às capacidades da introspecção, nunca a texto de modelo.

- US-05 — Como Administradora do tenant, quero que um token sem capacidade de escrita não
  consiga mutar projeto nenhum por caminho nenhum, para que a autorização não dependa da
  boa vontade da interface.
  - Dado um token cuja introspecção não devolve `toc:write`, Quando qualquer mutação é
    tentada (canvas, tabela, API direta), Então o serviço recusa com 403 e o traço
    registra a recusa.

### E1.2 — Canvas

**F1.2.1 — Nós** — criar, editar texto, mover, recolher/expandir nós no canvas.

- US-06 — Como Participante, quero adicionar um nó com título e descrição e movê-lo para
  onde faz sentido, para construir o diagrama do jeito que penso.
  - Dado um projeto aberto, Quando adiciono um nó e o arrasto, Então ele persiste com a
    posição final, e o arrasto inteiro é **um** episódio de desfazer, não um por pixel.

**F1.2.2 — Arestas causais** — ligar nós por arestas dirigidas ("Se origem, então
destino"), editar e excluir.

- US-07 — Como Facilitadora TOC, quero ligar dois nós por uma aresta causal, para
  registrar "se isto, então aquilo".
  - Dado dois nós A e B, Quando ligo A→B, Então a aresta aparece no canvas e na tabela;
    Quando tento ligar A→B de novo, Então o sistema recusa a duplicata dizendo por quê.

**F1.2.3 — Edição direta sob o item 8** — cada gesto do canvas declara sua classe: aplica
com desfazer, ou vira proposta/confirmação.

- US-08 — Como Participante, quero que editar o texto de um nó aplique na hora, sem tela
  de confirmação, para que o trabalho flua — sabendo que posso desfazer.
  - Dado um nó selecionado, Quando edito seu título inline e confirmo com Enter, Então o
    valor aplica sem diálogo (alvo único nomeado pelo gesto + valor literal no controle +
    reversível na sessão), entra na pilha de desfazer e gera traço.
- US-09 — Como Facilitadora TOC, quero que excluir um nó com arestas me mostre o raio
  antes de aplicar, para não desmontar o diagrama sem ver o custo.
  - Dado um nó com 3 arestas incidentes, Quando o excluo, Então o sistema mostra "remove
    também 3 arestas" no próprio controle e aplica com desfazer que restaura nó **e**
    arestas em um passo.

**F1.2.4 — Desfazer de sessão e reverter de domínio** — pilha por sessão de edição, sem
teto; o que já gravou se recupera por ação de domínio nomeada.

- US-10 — Como Participante, quero desfazer quantos passos eu tiver dado desde que abri o
  projeto, para experimentar sem medo.
  - Dado que fiz 10 edições na sessão, Quando aciono desfazer 10 vezes, Então volto ao
    estado de abertura, passo a passo, na ordem inversa.
- US-11 — Como Facilitadora TOC, quero reverter uma alteração feita em sessão anterior
  como ação explícita, para recuperar sem fingir que o passado não aconteceu.
  - Dado um nó cujo título mudou ontem, Quando abro seu histórico e aciono "Reverter
    título para X", Então a reversão aplica como ação de domínio nova, com evento
    compensatório correlacionado no traço — nunca apagando o evento original.

**F1.2.5 — Navegação do canvas** — pan, zoom, ajustar à tela, foco em nó.

- US-12 — Como Gestora, quero ajustar o diagrama inteiro à tela, para ver a análise de
  uma vez antes de decidir.
  - Dado um projeto com 50 nós, Quando aciono "ajustar à tela", Então todos os nós ficam
    visíveis no enquadramento, e a navegação (pan/zoom) não entra na pilha de desfazer.

### E1.3 — Vista tabular equivalente

**F1.3.1 — Painel de entidades** — tabelas de nós e arestas com contadores, ao lado do
canvas, redimensionável.

- US-13 — Como Participante, quero ver nós e arestas em tabela com contagem, para operar
  projetos grandes sem caçar caixas no canvas.
  - Dado um projeto com 40 nós e 55 arestas, Quando abro o painel, Então vejo duas abas
    com "Nós (40)" e "Arestas (55)" e cada linha com as ações de editar e excluir.

**F1.3.2 — Equivalência de operações** — toda operação de nó/aresta do canvas existe na
tabela, com o mesmo efeito, o mesmo traço e a mesma pilha de desfazer.

- US-14 — Como Facilitadora TOC, quero criar e editar nós pela tabela com o mesmo
  resultado do canvas, para escolher a vista pela tarefa, não pela funcionalidade.
  - Dado o painel aberto, Quando crio um nó pela tabela, Então ele aparece no canvas com
    posição atribuída automaticamente, e desfazer o remove — indiferente à vista onde o
    gesto nasceu.

**F1.3.3 — Foco cruzado** — da linha da tabela ao nó no canvas.

- US-15 — Como Participante, quero clicar em "focar" numa linha da tabela e ver o canvas
  centralizar aquele nó, para achar no diagrama o que achei na lista.
  - Dado um nó fora do enquadramento atual, Quando aciono focar na sua linha, Então o
    canvas centraliza e destaca o nó.

### E1.4 — Exportação/importação JSON

**F1.4.1 — Exportação canônica** — o projeto inteiro num JSON versionado, determinístico,
sem dado de outra pessoa.

- US-16 — Como Facilitadora TOC, quero exportar meu projeto para JSON, para levar a
  análise a quem não está no sistema.
  - Dado um projeto aberto, Quando exporto, Então recebo um arquivo com versão de
    esquema, metadados, nós e arestas em ordem canônica — e exportar duas vezes sem
    mudança produz bytes idênticos.

**F1.4.2 — Importação não destrutiva** — valida, relata, cria projeto novo; nunca
substitui em silêncio.

- US-17 — Como Facilitadora TOC, quero importar um JSON exportado e receber um relato do
  que entrou, para confiar no que aconteceu.
  - Dado um arquivo exportado válido, Quando importo, Então nasce um **projeto novo**
    (identificadores novos, mapeamento relatado), o original — se existir — permanece
    intocado, e o relato diz quantos nós e arestas entraram.
- US-18 — Como Participante, quero que um arquivo inválido seja recusado com a lista de
  problemas, para corrigir em vez de adivinhar.
  - Dado um JSON com aresta apontando para nó inexistente, Quando importo, Então nada é
    criado e o relato aponta a aresta e o motivo — nunca um `alert()` genérico (o
    contraexemplo é F-10).

## Entidades e modelo de domínio

DDD puro — domínio sem framework, sem entrada/saída, sem relógio (P3). Detalhamento com
atributos em [`data-model.md`](data-model.md); aqui, o essencial:

- **Projeto** (agregado raiz): identidade própria; pertence a um **DonoDoProjeto**
  (objeto de valor: inquilino + usuário); tem **TipoDeFerramenta** (genérico no M1; ARA,
  NC etc. estendem nos módulos seguintes), nome, descrição do problema, estado de ciclo
  de vida (`ativo` | `excluido`), carimbo de exclusão. Contém **Nós** e **ArestasCausais**
  — toda operação sobre eles passa pelo agregado, que garante as invariantes.
- **Nó** (entidade interna ao agregado): identidade, título, descrição, tipo extensível
  (o M1 conhece só `generico`), **PosicaoNoCanvas** (objeto de valor x,y), recolhido ou
  não.
- **ArestaCausal** (entidade interna): dirigida, origem → destino, ambos nós do mesmo
  projeto; rótulo opcional. Lê-se "Se origem, então destino".
- **EventoDeDominio** (somente-acréscimo): `ProjetoCriado`, `NoAdicionado`, `NoEditado`,
  `NoMovido`, `NoExcluido`, `ArestaLigada`, `ArestaEditada`, `ArestaExcluida`,
  `ProjetoExcluido`, `ProjetoRestaurado`, `ProjetoImportado`, além do **evento
  compensatório** de reversão, correlacionado ao evento que reverte. Nenhum evento é
  jamais apagado ou reescrito.
- **Invariantes do agregado**: aresta só liga nós existentes do próprio projeto; sem
  auto-laço; sem aresta duplicada (mesmo par origem→destino); excluir nó remove as
  arestas incidentes **no mesmo comando**, com o raio declarado no evento; projeto
  excluído não aceita mutação (só restauração).
- **Fora do domínio**: a pilha de desfazer é **estado de sessão da interface**, não
  entidade de domínio (F-13); a FSM de proposta é uma só e do servidor (item 8).

## Requisitos funcionais

### CRUD de projetos

RF-01: O SISTEMA DEVE criar projeto com nome, descrição do problema e tipo de ferramenta,
persistindo-o no banco próprio associado ao (inquilino, usuário) da introspecção. [F-04,
F-11] 🟡

RF-02: O SISTEMA DEVE listar os projetos ativos visíveis ao usuário autenticado,
ordenados por última alteração, sem jamais incluir projeto de outro inquilino. 🟡

RF-03: O SISTEMA DEVE abrir um projeto devolvendo metadados, nós e arestas num único
carregamento consistente. [F-03] 🟡

RF-04: O SISTEMA DEVE permitir editar nome e descrição do problema de um projeto
existente, registrando o evento de domínio correspondente. 🟡

RF-05: QUANDO o usuário recarregar a página, O SISTEMA DEVE reapresentar o projeto
exatamente como persistido — a correção do defeito D-07 da linhagem, cuja "persistência"
era um vetor em memória. [F-04, F-09] 🟡

### Exclusão suave e restauração

RF-06: QUANDO o usuário excluir um projeto, O SISTEMA DEVE marcá-lo `excluido` com
carimbo de data — nunca remover a linha — e retirá-lo das listagens padrão. [F-05] 🟡

RF-07: O SISTEMA DEVE listar os projetos excluídos do usuário (lixeira) com data de
exclusão e ação de restauração. 🟡

RF-08: QUANDO o usuário restaurar um projeto excluído, O SISTEMA DEVE devolvê-lo ao
estado `ativo` com nós, arestas e histórico intactos, registrando `ProjetoRestaurado`. 🟡

RF-09: QUANDO o usuário pedir exclusão definitiva, O SISTEMA DEVE exigir confirmação
explícita que nomeie o projeto (o efeito falha o 3º teste do item 8 — irreversível) antes
de remover. [F-12] 🟡

RF-10: O SISTEMA DEVE recusar qualquer mutação sobre projeto no estado `excluido`, exceto
restauração e exclusão definitiva. 🟡

### Nós no canvas

RF-11: O SISTEMA DEVE criar nó com título e descrição na posição indicada pelo gesto,
persistindo-o e registrando `NoAdicionado`. [F-01] 🟡

RF-12: O SISTEMA DEVE permitir editar título e descrição de um nó, inline no canvas e
pelo formulário, aplicando na hora sob o item 8 (alvo único nomeado pelo gesto, valor
literal no controle, reversível na sessão). [F-12] 🟡

RF-13: QUANDO o usuário arrastar um nó, O SISTEMA DEVE persistir a posição final e tratar
o arrasto inteiro como um único episódio de desfazer. [F-13] 🟡

RF-14: O SISTEMA DEVE permitir recolher e expandir um nó, persistindo o estado por
projeto. [F-01] 🟡

RF-15: QUANDO o usuário excluir um nó, O SISTEMA DEVE remover também as arestas
incidentes no mesmo comando, declarando o raio ("remove também N arestas") no controle
antes do gesto e no evento de domínio depois dele. [F-06] 🟡

RF-16: O SISTEMA DEVE garantir por teste de domínio que excluir um nó remove exatamente
aquele nó e suas arestas incidentes — o teste que teria pego o filtro invertido da
linhagem, que apagava todos os nós menos o excluído. [F-06] 🟡

### Arestas causais

RF-17: O SISTEMA DEVE criar aresta dirigida entre dois nós do projeto, pelo gesto de
ligação no canvas ou pelo formulário da tabela. [F-02] 🟡

RF-18: O SISTEMA DEVE recusar aresta duplicada (mesmo par origem→destino) e auto-laço,
com mensagem que diga a regra violada. 🟡

RF-19: O SISTEMA DEVE permitir editar o rótulo de uma aresta e excluí-la, com os eventos
correspondentes. 🟡

RF-20: O SISTEMA DEVE validar, em toda mutação de aresta, que origem e destino existem no
projeto — no domínio, não só na interface. 🟡

### Edição direta, desfazer e reverter

RF-21: O SISTEMA DEVE classificar cada tipo de ação por política declarada no servidor
(aplica-com-desfazer | exige-confirmação | nasce-proposta), resolvendo o portão **por
tipo de ação, nunca por origem alegada pelo cliente**. [F-12] 🟡

RF-22: O SISTEMA DEVE manter, por sessão de edição de projeto, uma pilha de desfazer sem
teto declarado, onde cada entrada é um episódio (arrasto = 1, edição de texto confirmada
= 1, exclusão de nó com cascata = 1). [F-13, F-17] 🟡

RF-23: QUANDO o usuário acionar desfazer, O SISTEMA DEVE aplicar a operação inversa do
último episódio como mutação nova, registrando evento compensatório correlacionado —
nunca apagando o evento original. [F-13] 🟡

RF-24: QUANDO a sessão terminar (fechar ou recarregar), O SISTEMA DEVE descartar a pilha
de desfazer — e o que já foi gravado passa a se recuperar por "reverter", ação de domínio
nomeada, nunca por um "desfazer" ressuscitado. [F-13] 🟡

RF-25: O SISTEMA DEVE oferecer, no histórico de um nó ou projeto, a ação "Reverter <campo>
para <valor>", que aplica como mutação nova com evento compensatório. [F-13] 🟡

RF-26: O SISTEMA DEVE registrar traço para **toda** mutação, em qualquer caminho (canvas,
tabela, API, desfazer, reverter) — traço ausente é defeito de aceite, não detalhe. [F-12]
🟡

### Vista tabular equivalente

RF-27: O SISTEMA DEVE apresentar painel de entidades com abas de nós e arestas, cada uma
com contagem no título da aba. [F-08] 🟡

RF-28: O SISTEMA DEVE oferecer na tabela as mesmas operações do canvas — criar, editar,
excluir nó; criar, editar, excluir aresta — com o mesmo efeito de domínio, o mesmo traço
e a mesma pilha de desfazer. [F-08] 🟡

RF-29: QUANDO um nó for criado pela tabela, O SISTEMA DEVE atribuir posição automática no
canvas que não sobreponha nós existentes. 🟡

RF-30: O SISTEMA DEVE manter canvas e tabela consistentes na mesma sessão: mutação em uma
vista aparece na outra sem recarregar. [F-08] 🟡

RF-31: O SISTEMA DEVE oferecer, em cada linha de nó, a ação de focar que centraliza e
destaca o nó no canvas. [F-08] 🟡

### Exportação e importação JSON

RF-32: O SISTEMA DEVE exportar o projeto num JSON com versão de esquema declarada,
metadados, nós e arestas — em ordem canônica, tal que duas exportações do mesmo estado
sejam byte-idênticas. [F-16] 🟡

RF-33: O SISTEMA DEVE validar o arquivo importado contra o esquema declarado — estrutura,
tipos, referências de aresta a nó — antes de criar qualquer coisa. [F-10] 🟡

RF-34: QUANDO a validação falhar, O SISTEMA DEVE recusar a importação inteira com relato
por item (o quê, onde, por quê), sem criar nem alterar nada. [F-10] 🟡

RF-35: QUANDO a validação passar, O SISTEMA DEVE criar um **projeto novo** com
identificadores novos e relatar o mapeamento e as contagens — nunca substituir projeto
existente em silêncio. [F-10] 🟡

RF-36: O SISTEMA DEVE garantir o ciclo de ida e volta: exportar um projeto e importar o
arquivo produz um projeto cujo novo export é estruturalmente idêntico (a menos de
identificadores e carimbos). 🟡

## Requisitos de interface

RI-01: A lista de projetos apresenta nome, tipo de ferramenta, data de última alteração e
ações (abrir, editar, excluir), com estado vazio que orienta a criação do primeiro
projeto. 🟡

RI-02: A lixeira é uma vista separada da lista, com data de exclusão e ações de restaurar
e excluir definitivamente — esta última com confirmação que nomeia o projeto. 🟡

RI-03: O canvas oferece pan, zoom e "ajustar à tela"; navegação nunca entra na pilha de
desfazer. 🟡

RI-04: A edição de título de nó é inline no canvas (Enter confirma, Esc cancela);
descrição e campos longos abrem em painel lateral, não em modal bloqueante. 🟡

RI-05: O controle de exclusão de nó com arestas mostra o raio ("remove também N
arestas") **antes** do clique final, no próprio controle. 🟡

RI-06: O desfazer é acessível por atalho de teclado (Ctrl/Cmd+Z) e por botão visível com
o nome do episódio que vai desfazer (ex.: "Desfazer: mover nó"). 🟡

RI-07: O painel de entidades é redimensionável por arrasto e mantém a largura escolhida
durante a sessão. [F-08] 🟡

RI-08: As tabelas de nós e arestas mostram contagem na aba, têm cabeçalho fixo ao rolar e
estado vazio com ação de criação. [F-08] 🟡

RI-09: A importação apresenta o relato de validação na própria tela — lista de problemas
com item e motivo, ou resumo do que entrou — nunca `alert()` do navegador. [F-10] 🟡

RI-10: Toda superfície do módulo respeita o tema do hospedeiro (com fallback) e o modo
só-conteúdo definidos no ciclo 002/003, funcionando de 420px de largura para cima. 🟡

RI-11: Toda ação tem rótulo textual acessível (não só ícone), foco visível e operação
completa por teclado — inclusive criar aresta sem arrastar (pela tabela). 🟡

RI-12: Estados de carregamento, erro e recusa de autorização são telas desenhadas com
próxima ação clara, não texto cru de exceção. 🟡

## Requisitos não funcionais

RNF-01: Toda mutação de domínio emite traço OTel correlacionado (requisição → caso de uso
→ repositório) e log estruturado com identificador de correlação — sem traço, a
funcionalidade não está pronta (P5). 🟡

RNF-02: O domínio e a aplicação não importam framework, banco ou HTTP; a fronteira é
verificada por `import-linter` que falha o build na violação (P3). 🟡

RNF-03: O isolamento por inquilino é imposto na camada de consulta (toda query filtra por
inquilino vindo da introspecção), coberto por teste que tenta ler através da fronteira e
falha. 🟡

RNF-04: A autorização usa exclusivamente as capacidades devolvidas pela introspecção —
nunca texto produzido por modelo (P2, item 3) — e a recusa é fail-closed. 🟡

RNF-05: Abrir um projeto com 200 nós e 300 arestas responde em menos de 2 segundos no
percentil 95, medido por teste de carga registrado no qa-report do ciclo. 🟡

RNF-06: A interação de canvas (arrasto, pan, zoom) mantém 30 quadros por segundo ou mais
com 200 nós, medida no protótipo de performance antes do aceite. 🟡

RNF-07: A importação limita o payload (tamanho máximo declarado na configuração) e
processa a validação sem bloquear o serviço para outros usuários. 🟡

RNF-08: Toda cadeia de caracteres visível ao usuário passa pelo mecanismo de i18n pt/en
desde o primeiro commit de interface (E8.3) — nenhum literal solto em componente. 🟡

RNF-09: Migrações de banco (Alembic) são reversíveis: cada migração tem downgrade
testado, e a migração da exclusão suave preserva dados existentes. 🟡

RNF-10: Nenhum segredo, chave ou credencial no cliente ou no repositório — a violação
canônica da linhagem é o contraexemplo medido (chave do provedor no navegador, D-01 da
visão). Verificação por grep no CI (P7). 🟡

## Regras de negócio

RN-01: Aresta causal é dirigida e lê-se "Se <origem>, então <destino>" — a semântica de
suficiência que todas as ferramentas TOC herdam. [F-02] 🟢 (a leitura causal está na
linhagem: `tocbuilderv3/APLICATION_PURPOSE.md:24`)

RN-02: Auto-laço (aresta de um nó para ele mesmo) é inválido em qualquer ferramenta. 🟡

RN-03: Aresta duplicada (mesmo par origem→destino) é inválida; a mesma dupla de nós pode
ter arestas nos dois sentidos (laços de reforço são legítimos na TOC e a análise deles é
de M2, não daqui). 🟡

RN-04: O núcleo não conhece semântica TOC: tipo de nó no M1 é `generico`, e módulos
M2–M5 estendem por tipo de projeto — nenhuma regra de UDE, premissa ou injeção entra
neste módulo (correção estrutural do D-08, que enterrou regra de negócio em prompt).
[F-15] 🟡

RN-05: Exclusão de projeto é sempre suave; exclusão definitiva só de projeto já na
lixeira, por confirmação explícita. 🟡

RN-06: Importação nunca muta projeto existente: o resultado é sempre projeto novo com
identificadores novos e mapeamento relatado. 🟡

## Integrações

INT-01: Identidade e autorização pela junta do ciclo 003: token da fundação →
`POST /auth/introspect` → (inquilino, usuário, capacidades). O M1 não implementa
introspecção; consome-a. (fronteira APH: E7.1) 🟡

INT-02: Nenhuma ação de IA neste ciclo: o catálogo `toc.*` e a FSM de proposta são do
ciclo 006. As telas deste módulo, porém, já nascem **registráveis** — cada tela declara
identificador estável para o registro de telas do E7.5, para que o ciclo 006 as componha
sem retrabalho. 🟡

INT-03: A política por tipo de ação (RF-21) usa o mesmo vocabulário de classes de risco
do catálogo futuro, para que as ações do M1 entrem no catálogo `toc.*` do ciclo 006 sem
renomear. 🟡

## Telas e fluxos

### 6.1 Lista de projetos — Job: escolher onde trabalhar · Campos: nome, tipo, última alteração · Ações: criar, abrir, editar metadados, excluir (suave), ir à lixeira

### 6.2 Lixeira — Job: recuperar ou liberar de vez · Campos: nome, excluído em · Ações: restaurar, excluir definitivamente (com confirmação nomeada)

### 6.3 Canvas — Job: construir o diagrama pensando · Campos: nós (título, descrição, recolhido), arestas (rótulo) · Ações: criar/editar/mover/recolher/excluir nó, ligar/editar/excluir aresta, desfazer, pan/zoom/ajustar

### 6.4 Painel de entidades — Job: operar em volume · Campos: tabelas de nós e arestas com contagens · Ações: as mesmas do canvas + focar no canvas; redimensionar painel

### 6.5 Exportar/Importar — Job: levar e trazer análises · Campos: arquivo, relato de validação · Ações: exportar JSON canônico; importar com validação e relato

### 6.6 Histórico e reverter — Job: recuperar o que já gravou · Campos: eventos por data · Ações: "Reverter <campo> para <valor>" (ação de domínio, evento compensatório)

## Entregáveis

- Domínio Python puro do agregado Projeto (nós, arestas, invariantes, eventos) com testes
  de domínio **sem rede e sem banco** — nascidos antes do código (P4).
- Casos de uso + portas (repositório, relógio, identidade) e adaptadores FastAPI/
  PostgreSQL; migrações Alembic com downgrade.
- Contrato de `import-linter` versionado no CI.
- Interface React: lista, lixeira, canvas, painel de entidades, exportar/importar,
  histórico — sobre o `ux-design.md` do ciclo 002.
- Contratos REST do módulo (ver [`contracts/rest-api.md`](contracts/rest-api.md))
  implementados e testados.
- Jornada viva (P6): jornada de construção de um diagrama sintético, captura gerada por
  script versionado do build real, avaliação heurística datada — no mesmo pull request.
- Entradas de CHANGELOG e, se decisão material surgir, ADR novo.

## Critérios de aceite (DoD)

| # | Critério | Verificação executável |
|---|---|---|
| 1 | Domínio puro, testes sem rede | `pytest tests/domain/ -p no:cacheprovider` verde + `lint-imports` código 0 |
| 2 | Teste do filtro de exclusão (F-06) existe e passa | `pytest tests/domain/test_excluir_no.py -k cascata -v` — mostra o caso "só o nó e suas arestas" |
| 3 | Exclusão suave reversível | `pytest tests/application/test_lixeira.py` — excluir → restaurar → conteúdo idêntico |
| 4 | Ida e volta do export | `pytest tests/application/test_export_import.py -k roundtrip` — export→import→export estruturalmente igual |
| 5 | Export determinístico | duas execuções do export do mesmo estado + `diff` vazio, colado no qa-report |
| 6 | Importação inválida recusa com relato | `pytest tests/application/test_import_invalido.py` — nada criado, relato por item |
| 7 | Isolamento por inquilino | `pytest tests/integration/test_isolamento.py` — leitura cruzada falha com 403/404 |
| 8 | Toda mutação com traço | `pytest tests/integration/test_traco.py` — teste falha se qualquer mutação não emitir traço |
| 9 | Política por tipo de ação no servidor | `grep -rn "politica\|policy" backend/` mostra a tabela declarada; teste de recusa fail-closed verde |
| 10 | Sem segredo no cliente | `grep -rniE "api[_-]?key|secret" frontend/src/ \| wc -l` = 0 |
| 11 | i18n sem literal solto | função de aptidão de literais em componentes, código 0 + quanto examinou |
| 12 | Jornada viva presente | `ls docs/jornadas/` contém a jornada do M1 com capturas geradas por script |
| 13 | Conformidade do ciclo | `scripts/check-conformance.sh 004` código 0 |
| 14 | Caminhos e links do ciclo | `scripts/check-caminhos.sh` e `scripts/check-links.sh` código 0 + quanto examinaram |

## Fontes

F-01: /home/user/tocbuilderv3/types.ts:9-15 — `interface Node<T>` genérico (id, position,
data, width, height) — a forma de nó que o M1 herda e tipa por módulo 🟢

F-02: /home/user/tocbuilderv3/types.ts:17-31 — `interface Edge` (source, target, handles,
estilo) — a aresta causal; a leitura "Se A... então B..." está em
`APLICATION_PURPOSE.md:24` 🟢

F-03: /home/user/tocbuilderv3/types.ts:55-65 — `AraProject` com `nodes` e `edges`
embutidos no projeto — o agregado que o M1 formaliza 🟢

F-04: /home/user/tocbuilderv3/services/mockApiService.ts:9-14 — `let projects:
AraProject[] = []` e mais dois vetores — toda a "persistência" da 4ª geração era memória
de processo; recarregar perdia tudo 🟢

F-05: /home/user/tocbuilderv3/services/mockApiService.ts:84-94 — `deleteProject` remove
por `filter` — exclusão destrutiva e imediata, sem lixeira 🟢

F-06: /home/user/tocbuilderv3/services/mockApiService.ts:521 — `project.nodes =
project.nodes.filter(n => n.id === nodeId);` — o filtro invertido: excluir um nó da S&T
mantinha **só** o nó excluído e apagava todos os outros. Verificado nesta leitura; linha
colada. É o argumento executável do TDD deste ciclo 🟢

F-07: /home/user/tocbuilderv3/api_specifications.md — 20 endpoints especificados
(`grep -c '^### \`' api_specifications.md` → `20`), 9 deles do recurso de projetos/nós/
arestas; nenhuma chamada real de rede existe no app (`grep -rn "fetch(\|axios"` sobre
`.ts/.tsx`, excluído `node_modules` → vazio, código 1) — especificado 4 vezes, construído
zero (D-03) 🟢

F-08: /home/user/tocbuilderv3/components/EntitiesPanel.tsx:34,90-114,128-154 — o painel
de entidades: abas nós/arestas com contagem (l.47), tabelas com editar/excluir, foco no
canvas (l.106), redimensionável (l.56-60) — a vista tabular que provou valor 🟢

F-09: /home/user/tocbuilderv3/App.tsx:34,96 — `AUTOSAVE_KEY` em `localStorage` — o único
paliativo de persistência da linhagem, um snapshot por navegador, só da sessão ARA
aberta (D-07) 🟢

F-10: /home/user/tocbuilderv3/components/NodeZoneView.tsx:308-322 — a importação da
linhagem: validação rasa (só `name` + dois `Array.isArray`), erro por `alert()`; o
acerto — criar projeto novo "(Importado)" — permanece no RF-35 🟢

F-11: /home/user/tocbuilderv3/constants.ts:5 — `DEFAULT_USER_ID =
'user_placeholder_001'` — não havia usuário real, logo não havia isolamento (D-02) 🟢

F-12: [`../../docs/governance/constitution.md`](../../docs/governance/constitution.md)
linhas 64-71 (alcance do P2) e 89-96 (item 8: os três testes da manipulação direta,
política por tipo de ação) 🟢

F-13: /home/user/gestaodeprioridades/docs/adr/0013-desfazer-de-sessao-reverter-de-dominio.md
— o padrão pago pela irmã: pilha de sessão sem teto (§1), episódio (§2), recarregar mata
a pilha e o que sobra chama-se reverter (§4), evento compensatório (§6) 🟢

F-14: [`../../docs/produto/rounds.md`](../../docs/produto/rounds.md) — Round 004:
apetite, aptidão executável, "sai primeiro: o desfazer de sessão", "nunca sai: a vista
tabular" 🟢

F-15: [`../../docs/produto/modulos.md`](../../docs/produto/modulos.md) — M1: o job, os
épicos E1.1–E1.4, dependências de E8.1/E7.1 🟢

F-16: /home/user/tocbuilderv3/components/Toolbar.tsx:84 — "Exportar a ARA atual para um
arquivo JSON" — a exportação existia na linhagem; o determinismo e o esquema versionado
não 🟢

F-17: /home/user/tocbuilderv3 — `grep -rni "undo\|desfazer"` sobre `.ts/.tsx`, excluído
`node_modules` → `0` ocorrências: desfazer nunca existiu na linhagem 🟢

## Lacunas e assunções

L-01: A junta do ciclo 003 (introspecção, banco, OTel) ainda não existe — assunção: o M1
programa contra as portas definidas no 003 e não abre antes de a aptidão "a junta fecha
contra a ghdaru real" passar — risco **alto** (é a dependência inteira do ciclo).

L-02: O apetite de um ciclo para 4 épicos com TDD é estimativa sem histórico próprio —
assunção: o corte declarado no round 004 (sai o desfazer primeiro, nunca a vista tabular)
absorve o estouro — risco **médio**.

L-03: O identificador estável de tela (INT-02) antecipa um contrato que o ciclo 006 ainda
vai fixar — assunção: um `data-tela-id` por tela custa quase nada e evita renomear; se o
006 decidir outro formato, a migração é mecânica — risco **baixo**.

L-04: A meta de desempenho (200 nós, RNF-05/06) vem do tamanho típico de ARA na
literatura, não de medição própria — assunção: suficiente para v1; medição real na
jornada viva — risco **baixo**.

## Clarify

- [DÚVIDA] Retenção da lixeira: projetos excluídos expiram (30/90 dias) com limpeza
  automática, ou só saem por exclusão definitiva manual? (RF-06–RF-09)
- [DÚVIDA] Concorrência v1: dois usuários no mesmo projeto — bloqueio otimista com
  detecção de conflito basta, ou o Product Steward quer colaboração em tempo real já no
  M1? A spec assume bloqueio otimista (o tempo real mudaria RNF e arquitetura).
- [DÚVIDA] Papéis na prática: Participante pode excluir projeto que não criou, ou só a
  Facilitadora/Administradora? A matriz papel×ação precisa do dono antes do RF-21
  congelar a política.
- [DÚVIDA] Limite de projeto: impomos máximo de nós por projeto (proteção de desempenho e
  de payload de importação), e qual? A spec assume 500 como teto técnico do RNF-07.
