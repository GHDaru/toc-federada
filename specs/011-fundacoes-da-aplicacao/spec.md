# Spec 011 — Fundações da aplicação (M8 — Fundações da Aplicação)

> Siglas: **TOC** — Teoria das Restrições · **APH** — Aplicação ↔ Harness · **ADR** —
> Architecture Decision Record (Registro de Decisão Arquitetural) · **RF/RI/RNF/RN/INT**
> — requisito funcional / de interface / não funcional / regra de negócio / integração ·
> **US** — User Story (história de usuário) · **DoD** — Definition of Done (Definição de
> Pronto) · **DoR** — Definition of Ready (Definição de Prontidão) · **TDD** —
> Test-Driven Development (desenvolvimento guiado por teste) · **DDD** — Domain-Driven
> Design (Design Orientado a Domínio) · **i18n** — internacionalização · **l10n** —
> localização · **UI** — interface de usuário · **UX** — experiência de usuário ·
> **OTel** — OpenTelemetry · **CI** — integração contínua · **JSON** — JavaScript Object
> Notation · **REST** — Representational State Transfer · **UDE** — Undesirable Effect
> (Efeito Indesejável) · **ARA** — Árvore da Realidade Atual · **NC** — Nuvem de
> Conflito · **ARF** — Árvore da Realidade Futura · **APR** — Árvore de Pré-Requisitos ·
> **AT** — Árvore de Transição · **S&T** — Árvore de Estratégia & Táticas · **IA** —
> inteligência artificial · **LLM** — modelo de linguagem de grande porte (*Large
> Language Model*) · **SDK** — Software Development Kit (kit de desenvolvimento) ·
> **DDL** — Data Definition Language (linguagem de definição de dados) · **PITR** —
> Point-In-Time Recovery (recuperação a um ponto no tempo) · **RPO/RTO** — Recovery
> Point / Time Objective (objetivo de ponto / tempo de recuperação) · **KB** — kilobyte
> · **eTLD+1** — domínio registrável efetivo mais um rótulo

- **Status**: Rascunho (aprovação: gate humano do ciclo 001)
- **Raia**: plena
- **Data**: 2026-09-03
- **Origem**: [`../../docs/produto/modulos.md`](../../docs/produto/modulos.md) (M8) ·
  [`../../docs/roadmap.md`](../../docs/roadmap.md) (ciclo 011) ·
  [`../../docs/produto/rounds.md`](../../docs/produto/rounds.md) (round 011)

## O quê e por quê

O M8 é a **fundação de infraestrutura da aplicação**: o que nenhuma ferramenta da TOC vê,
e sem o que nenhuma delas existe. Metade dele já nasceu — o ciclo 003 entregou o banco
próprio, a observabilidade e o endereço publicado ([`../003-esqueleto-federado/spec.md`](../003-esqueleto-federado/spec.md)).
Este ciclo fecha a outra metade, e ela não é sobra de escopo: é o conjunto de coisas que
**custa dez vezes mais depois** do que agora — internacionalização, documentação embutida,
e a leitura e escrita de arquivos que atravessam a fronteira do produto.

O argumento da i18n é da própria linhagem, e está medido. A quarta geração do TOC-Builder
escreveu **cinco** especificações de funcionalidade; **duas delas** são retrofit de
internacionalização — a funcionalidade completa e depois a "conclusão da Fase 1", ambas
datadas de 2024-08-02 [F-01, F-02]:

```
$ ls /home/user/tocbuilderv3/specs/
feat_conflict_cloud.md
feat_conflict_cloud_refactor.md
feat_direct_ara_flow.md
feat_internationalization_final_steps.md
feat_internationalization_full.md
```

Duas das cinco specs de uma geração inteira gastas para traduzir telas que já existiam — e
mesmo assim **25 dos 51 arquivos `.tsx` da geração jamais importaram o mecanismo de i18n**,
com literais em português vivos no código de produção até hoje [F-03, F-04]. É o preço
exato do adiamento, e é por isso que o E8.3 é o item que **nunca sai** deste round mesmo se
o apetite estourar ([`../../docs/produto/rounds.md`](../../docs/produto/rounds.md), round
011).

A documentação embutida tem o precedente inverso — a linhagem **acertou** a forma e errou a
cobertura: o `DocsView` da quarta geração é uma tela real, bilíngue, com navegação por
tópico e chamada para a ferramenta descrita [F-05]. Só que ela documentava **duas** das
seis ferramentas dos processos de pensamento, porque as outras quatro nunca existiram
[F-06, F-07]. Aqui as seis existem quando este ciclo abre, e a documentação embutida nasce
com portão de cobertura: ferramenta sem verbete é defeito de aceite.

Fecha o ciclo o **E1.4 avançado**: o núcleo de diagramas (M1, ciclo 004) já exporta e
importa o formato canônico próprio; falta ler o que a linhagem produziu, com validação
campo a campo — e **descartando o histórico de conversa com o modelo que aquele formato
carrega junto** [F-08, F-09]. E fecha também a única obrigação de fundação que o ciclo 003
não cobriu: a **unidade de restauração**. O 003 ensaiou o rollback de implantação e criou
um ramo do banco antes de migrar; nenhuma das duas coisas é uma restauração ensaiada
[F-10]. Na constituição da fundação isso tem nome: cópia no mesmo armazenamento e na mesma
conta é conveniência, não apólice [F-11].

## O que entra como dado

- **Stack** (ADR 0002, [`../../docs/adr/0002-stack-herdada-da-irma.md`](../../docs/adr/0002-stack-herdada-da-irma.md)):
  React + TypeScript/Vite no cliente, FastAPI/Python no serviço, PostgreSQL Neon em
  projeto próprio, implantação em eTLD+1 distinto do hospedeiro.
- **A junta do ciclo 003** ([`../003-esqueleto-federado/spec.md`](../003-esqueleto-federado/spec.md)):
  E8.1 (banco e migrações próprios, isolamento por inquilino), E8.2 (traço de nascença) e
  E8.5 (implantação e CI) **saem lá** — nenhum requisito deles se repete aqui. Deste ciclo
  para trás só há consumo; a única exceção declarada é a F8.1.3 abaixo, e ela existe
  porque a restauração **não estava** na DoD do 003 (medição em [F-10]).
- **O arquivo de mensagens do ciclo 003** (RF/RI-06 de lá: toda cadeia visível vive em
  arquivo de mensagens, português como língua-fonte). Este ciclo **consolida** aquela
  preparação em mecanismo com portão; não a reinventa.
- **O núcleo de exportação do ciclo 004**
  ([`../004-nucleo-de-diagramas/spec.md`](../004-nucleo-de-diagramas/spec.md), RF-32..RF-36):
  JSON canônico versionado, determinístico, e importação que sempre cria projeto novo. O
  E1.4 avançado é um **adaptador de formato legado** para dentro daquele caminho — não uma
  segunda importação.
- **Escopo v1** (ADR 0005, [`../../docs/adr/0005-escopo-do-dominio-v1.md`](../../docs/adr/0005-escopo-do-dominio-v1.md)):
  as seis ferramentas dos processos de pensamento mais a focalização. A documentação
  embutida cobre exatamente esse conjunto — nada a mais, nada a menos.
- **IA somente pela fundação** (ADR 0007, [`../../docs/adr/0007-ia-somente-pela-fundacao.md`](../../docs/adr/0007-ia-somente-pela-fundacao.md)):
  a documentação embutida é **conteúdo versionado no repositório**, jamais texto gerado em
  tempo de execução por modelo. Se um dia houver ajuda gerada, ela nasce ação de catálogo
  com proposta — não um `<div>` com saída de LLM.
- **Base sintética** (ADR 0006, [`../../docs/adr/0006-base-sintetica-desde-o-dia-1.md`](../../docs/adr/0006-base-sintetica-desde-o-dia-1.md)):
  os arquivos de importação usados como fixture são gerados por script a partir de
  personas fictícias ("Instituição Horizonte", "Facilitadora TOC"); nenhum export real de
  pessoa entra no repositório, nem como caso de teste.
- **Corte de apetite** (round 011): estourou → **sai primeiro** o E1.4 avançado (a
  importação da linhagem); **nunca sai** o portão de i18n.

## Épicos, features e user stories

### E8.1 — Persistência própria · E8.2 — Observabilidade OTel · E8.5 — Implantação *(saem no ciclo 003)*

Entregues por [`../003-esqueleto-federado/spec.md`](../003-esqueleto-federado/spec.md)
(RF-28..RF-39 de lá): banco Neon em projeto próprio, migrações Alembic com `downgrade`
testado, isolamento por inquilino na consulta, traço em todo endpoint, log estruturado com
`trace_id`, publicação em eTLD+1 distinto e CI com as funções de aptidão. Aqui só a
dependência: este ciclo **usa** as migrações, o traço e a CI, e não redefine nenhum deles.

**F8.1.3 — Unidade de restauração ensaiada** *(delta declarado)* — o projeto Neon próprio
é a unidade que o provedor restaura como um todo, e restaurar esta aplicação nunca pode
rebobinar outro produto; o ensaio prova isso uma vez, dentro do ciclo.

- US-01 — Como **Administradora do inquilino**, quero que a restauração desta aplicação
  seja ensaiada e datada, para "temos backup" ser um fato verificado e não uma esperança.
  - Dado o projeto Neon da aplicação, Quando o ensaio restaura uma cópia num destino
    separado e a aplicação sobe contra ela, Então a lista de projetos sintéticos aparece
    íntegra, e o relatório registra o instante alvo, a duração e o que **não** voltou
    (arquivos fora do banco, índices reconstruídos).
- US-02 — Como **Product Steward**, quero saber por escrito o que a restauração deste
  produto rebobina e o que ela não rebobina, para decidir com o custo à vista.
  - Dado o relatório do ensaio, Quando o leio, Então encontro o objetivo de ponto de
    recuperação e o de tempo declarados, e a afirmação explícita de que nenhum outro
    produto da plataforma compartilha esta unidade de restauração.

### E8.3 — Internacionalização pt/en

**F8.3.1 — Dicionário único e língua-fonte** — toda cadeia visível vive num dicionário
versionado; o português é a língua-fonte; o inglês é tradução de **interface**, nunca de
conceito de domínio.

- US-03 — Como **Facilitadora TOC**, quero conduzir uma análise com uma participante que
  só lê inglês sem que a ferramenta mude de vocabulário técnico, para "Efeito Indesejável"
  e *Undesirable Effect* serem o mesmo conceito e não dois.
  - Dado um projeto com UDEs, Quando troco a interface para inglês, Então rótulos, botões
    e mensagens mudam de idioma, o **conteúdo escrito pelas pessoas não muda**, e o termo
    de domínio aparece com o par declarado no glossário do produto.

**F8.3.2 — Portão de literal órfão** — nenhuma cadeia visível nasce fora do dicionário, e
quem tentar não passa da integração contínua.

- US-04 — Como **desenvolvedora do produto** (papel de contrato, não persona de produto),
  quero que um literal esquecido num componente derrube o build, para a dívida de tradução
  não crescer em silêncio como cresceu na linhagem.
  - Dado um componente novo com o texto `"Salvar"` embutido, Quando abro o pull request,
    Então a função de aptidão falha nomeando arquivo e linha — e a saída diz **quantos
    arquivos e quantas cadeias** examinou.

**F8.3.3 — Idioma efetivo: do hospedeiro, com preferência da pessoa** — embarcada, a
aplicação não inventa idioma: usa o que o embarque declarou, permite trocar, e lembra.

- US-05 — Como **Participante**, quero que a ferramenta abra no idioma da plataforma em
  que já estou trabalhando, para não ter de configurar nada duas vezes.
  - Dado um embarque cujo *handshake* declara `en`, Quando a aplicação carrega, Então ela
    renderiza em inglês; Quando eu troco para português, Então a escolha vale para as
    próximas sessões daquele meu identificador, sem afetar outra pessoa do mesmo inquilino.
- US-06 — Como **Administradora do inquilino**, quero um comportamento previsível quando o
  hospedeiro não declara idioma, para não haver tela em dois idiomas ao mesmo tempo.
  - Dado um embarque sem idioma declarado e sem preferência salva, Quando a aplicação
    carrega, Então ela usa o português (língua-fonte) e **registra a queda para o padrão**
    em log estruturado — nunca mistura idiomas na mesma tela.

**F8.3.4 — Chave ausente falha alto** — uma tradução que falta é defeito visível em
desenvolvimento e em CI, e degradação declarada em produção.

- US-07 — Como **Gestora**, quero nunca ver um identificador técnico no lugar de um rótulo,
  para a ferramenta não parecer quebrada na frente da minha equipe.
  - Dado um dicionário a que falta uma chave, Quando a tela renderiza em desenvolvimento,
    Então o mecanismo lança erro visível; Quando a mesma falta chega à CI, Então a
    verificação de paridade entre os dois dicionários falha antes do merge; Quando (só
    então) acontece em produção, Então cai para a cadeia da língua-fonte, nunca para a
    chave crua — o contrário do que a linhagem fazia [F-12].

**F8.3.5 — Localização de formato** — data, hora, número e ordenação seguem o idioma
efetivo; identificador e conteúdo de pessoa, nunca.

- US-08 — Como **Gestora**, quero ver datas e números no formato do meu idioma, para ler
  a lista de projetos sem traduzir de cabeça.
  - Dado o idioma efetivo `en`, Quando abro a lista de projetos, Então as datas seguem o
    formato daquele idioma e a ordenação alfabética usa a colação correspondente; Quando
    volto ao português, Então o mesmo conjunto reordena — e nenhum identificador,
    nenhum título escrito por pessoa muda em nenhum dos dois.

### E8.4 — Documentação embutida por ferramenta

**F8.4.1 — Acervo versionado, uma entrada por ferramenta** — o conteúdo é arquivo do
repositório, bilíngue, com cobertura conferida por portão.

- US-09 — Como **Participante** que nunca usou a TOC, quero abrir a documentação de uma
  ferramenta dentro da própria ferramenta, para aprender no momento em que preciso.
  - Dado que estou na Nuvem de Conflito, Quando abro a documentação embutida, Então leio o
    verbete daquela ferramenta — o que ela responde, as entidades, um exemplo sintético —
    no meu idioma efetivo, sem sair da tela.
- US-10 — Como **Product Steward**, quero que uma ferramenta nova não possa ser entregue
  sem verbete, para não repetir a documentação que cobria duas ferramentas de seis.
  - Dado o conjunto de ferramentas registradas, Quando a CI roda, Então a verificação de
    cobertura compara ferramentas × verbetes e falha nomeando a que falta — com a contagem
    dos dois lados na saída.

**F8.4.2 — Ajuda contextual ancorada** — de dentro da ferramenta, o mesmo acervo abre no
ponto certo, sem perder o trabalho em andamento.

- US-11 — Como **Facilitadora TOC**, quero abrir "o que faz uma premissa ser sustentada"
  ao lado do campo que estou preenchendo, para decidir sem trocar de contexto.
  - Dado um campo com âncora de ajuda, Quando aciono a ajuda, Então o painel abre no
    trecho ancorado, o diagrama continua carregado e fechar o painel devolve o foco ao
    campo de onde saí.

**F8.4.3 — Conteúdo bilíngue com fallback declarado** — verbete sem tradução aparece na
língua-fonte, dizendo que é o caso.

- US-12 — Como **Participante** em inglês, quero ler o verbete mesmo quando a tradução não
  existe, para não bater numa tela vazia.
  - Dado um verbete só em português e idioma efetivo `en`, Quando o abro, Então vejo o
    conteúdo em português com um aviso de que a tradução está pendente — e a mesma
    pendência aparece na contagem do portão de cobertura, como pendência declarada.

**F8.4.4 — Rastreabilidade do verbete à decisão** — cada verbete cita a spec e o ADR de
onde a regra que ele descreve vem.

- US-13 — Como **Facilitadora TOC**, quero saber por que a ferramenta exige o que exige,
  para confiar na regra em vez de contorná-la.
  - Dado o verbete da ARA, Quando leio o trecho sobre os critérios de UDE, Então encontro a
    referência à spec do módulo que os define, e o portão de caminhos confirma que essa
    referência resolve.

### E1.4 (M1) — Exportação e importação consolidadas

**F1.4.3 — Adaptador de formato legado** — os arquivos exportados pela quarta geração
entram, convertidos e validados, pelo mesmo caminho de importação do M1.

- US-14 — Como **Facilitadora TOC** com análises presas na geração antiga, quero importar
  o arquivo que exportei de lá, para não recomeçar do zero.
  - Dado um arquivo `<nome>_ARA_Export.json` da quarta geração, Quando o importo, Então
    nasce um projeto novo com nós e arestas convertidos para o modelo do M1, e o relato diz
    quantos entraram e o que foi descartado.

**F1.4.4 — Relato de recusa campo a campo** — arquivo inválido não cria nada e explica o
que está errado, item por item.

- US-15 — Como **Participante**, quero saber exatamente qual campo está errado no arquivo
  recusado, para corrigir em vez de adivinhar.
  - Dado um arquivo legado com uma aresta apontando para nó inexistente e um nó sem título,
    Quando o importo, Então nada é criado e o relato lista os **dois** problemas com
    caminho do campo e motivo — nunca uma caixa de alerta genérica, que é o que a linhagem
    fazia [F-09].

**F1.4.5 — Descarte declarado do histórico de conversa** — o formato legado carrega o
diálogo com o modelo dentro do arquivo do projeto; ele não entra.

- US-16 — Como **Administradora do inquilino**, quero que a importação não traga o
  histórico de conversa embutido no arquivo antigo, para não introduzir dado de conversa
  no banco desta aplicação sem decisão.
  - Dado um arquivo legado com `chatHistory` preenchido, Quando o importo, Então o campo é
    descartado, o relato declara "histórico de conversa descartado: N mensagens", e nada
    daquele conteúdo é persistido nem enviado a lugar nenhum.

**F1.4.6 — Exportação consolidada do projeto multi-ferramenta** — um projeto que
atravessou ARA → NC → ARF → APR → AT exporta inteiro, com os vínculos entre ferramentas.

- US-17 — Como **Gestora**, quero exportar a análise completa, e não seis arquivos soltos,
  para levar a cadeia inteira a quem vai decidir.
  - Dado um projeto com as cinco ferramentas encadeadas, Quando exporto, Então recebo um
    arquivo único com as seções por ferramenta **e** os vínculos entre elas; Quando o
    importo de volta, Então os vínculos são recriados e o relato os conta.

## Entidades e modelo de domínio

Este ciclo é predominantemente de **fundação e adaptadores**; o domínio novo é pequeno e
puro, e nenhuma entidade das ferramentas muda (P3 — domínio sem entrada e saída, sem
framework, sem relógio):

- **IdiomaEfetivo** (objeto de valor): resultado da resolução `preferência da pessoa →
  idioma do embarque → língua-fonte`, com o **motivo** da escolha guardado junto. Ele é
  valor derivado, não configuração persistida solta: a preferência é que se persiste, por
  (inquilino, usuário).
- **ChaveDeMensagem** (objeto de valor): identificador estável de uma cadeia visível.
  Invariante: existe na língua-fonte; a ausência na língua traduzida é **pendência
  declarada**, nunca silêncio.
- **Verbete** (agregado pequeno): identidade estável, ferramenta a que pertence, âncoras,
  corpo por idioma, referências de procedência (spec/ADR). Invariantes: uma ferramenta
  registrada tem ao menos um verbete; toda âncora citada por uma tela existe no corpo.
- **RelatoDeImportacao** (objeto de valor): resultado puro da validação — contagens por
  tipo de entidade, lista de problemas (caminho do campo + motivo) e lista de **descartes
  declarados**. Função pura: validar **antes** de qualquer efeito; sem relato não há
  escrita.
- **PlanoDeConversao** (serviço de domínio puro): mapeia o formato legado no modelo do M1
  — nó, aresta causal, metadados —, e é a única peça que conhece o formato antigo. Trocar
  ou aposentar o formato legado é trocar este serviço, não a importação.
- **Fora do domínio**: o mecanismo de i18n do cliente (adaptador de interface), o acervo
  de documentação (conteúdo versionado), a rotina de restauração (operação, verificada por
  ensaio) — nenhum deles é entidade.

## Requisitos funcionais

### Unidade de restauração (F8.1.3)

RF-01: O SISTEMA DEVE manter o dado desta aplicação em projeto PostgreSQL Neon **próprio**,
que não compartilha unidade de restauração com nenhum outro produto da plataforma —
restaurar esta aplicação NÃO DEVE rebobinar outro. [F-11] 🟡

RF-02: O ciclo DEVE executar **um ensaio de restauração** a partir da cópia do provedor
para um destino separado, subir a aplicação contra o destino restaurado e registrar a
saída no `qa-report.md` — cópia não ensaiada não conta como apólice. [F-11] 🟡

RF-03: O relatório do ensaio DEVE declarar o objetivo de ponto de recuperação e o de tempo
de recuperação, o instante alvo, a duração medida e **o que não volta com o banco**
(arquivos em armazenamento compatível com S3, índices reconstruídos). [F-11] 🟡

RF-04: O SISTEMA NÃO DEVE emitir DDL em nenhum caminho de execução — nem no arranque, nem
sob condição; encontrando esquema incompatível, DEVE falhar no arranque **imprimindo a
diferença**. [F-13] 🟡

RF-05: A semeadura da base sintética DEVE ser comando explícito, jamais efeito colateral de
tabela vazia, e NÃO DEVE existir caminho de execução que a dispare em produção. [F-14] 🟡

### Dicionário, língua-fonte e paridade (F8.3.1, F8.3.2, F8.3.4)

RF-06: O SISTEMA DEVE manter toda cadeia visível ao usuário em dicionários versionados por
idioma (`pt`, `en`), com o português como língua-fonte de toda chave. [F-01, F-03] 🟡

RF-07: O SISTEMA NÃO DEVE conter literal visível fora do dicionário em componente,
serviço ou mensagem de erro de interface; a verificação é função de aptidão da CI e
**imprime quantos arquivos e quantas cadeias examinou** (regra R2). [F-03, F-04] 🟡

RF-08: A CI DEVE verificar **paridade de chaves** entre os dicionários: chave presente na
língua-fonte e ausente na tradução é pendência declarada e listada; chave presente só na
tradução é erro. [F-15] 🟡

RF-09: QUANDO uma chave não for encontrada em desenvolvimento ou em teste, O SISTEMA DEVE
lançar erro visível — nunca renderizar a chave crua na tela, que é o comportamento
herdado que este requisito proíbe. [F-12] 🟡

RF-10: QUANDO uma chave não for encontrada em produção, O SISTEMA DEVE cair para a cadeia
da língua-fonte e registrar a ocorrência em log estruturado com a chave e a tela. [F-12] 🟡

RF-11: O SISTEMA DEVE tratar termo de domínio da TOC como **conceito com par declarado**
(por exemplo, Efeito Indesejável ↔ *Undesirable Effect*), publicado no glossário do
produto — tradução de interface NÃO DEVE renomear conceito. 🟡

### Idioma efetivo e localização (F8.3.3, F8.3.5)

RF-12: O SISTEMA DEVE resolver o idioma efetivo na ordem **preferência da pessoa → idioma
declarado pelo embarque → língua-fonte**, e DEVE guardar o motivo da escolha para
diagnóstico. 🟡

RF-13: O SISTEMA DEVE persistir a preferência de idioma por (inquilino, usuário) no banco
próprio — NÃO DEVE guardá-la apenas no navegador, como fazia a linhagem, onde a escolha
morria com o dispositivo. [F-16] 🟡

RF-14: QUANDO o embarque não declarar idioma e não houver preferência salva, O SISTEMA DEVE
usar a língua-fonte e registrar a queda para o padrão em log estruturado. 🟡

RF-15: O SISTEMA DEVE aplicar o idioma efetivo a **toda** a superfície — telas, mensagens
de erro, textos de estado vazio, rótulos acessíveis e documentação embutida —, sem tela
mista. 🟡

RF-16: O SISTEMA DEVE formatar data, hora e número segundo o idioma efetivo, e ordenar
listas alfabéticas pela colação correspondente. 🟡

RF-17: O SISTEMA NÃO DEVE traduzir, reformatar ou reordenar conteúdo escrito por pessoa
(título de nó, enunciado de UDE, premissa) nem identificador técnico. 🟡

### Documentação embutida (E8.4)

RF-18: O SISTEMA DEVE servir um acervo de documentação **versionado no repositório**, com
ao menos um verbete por ferramenta registrada — ARA, NC, ARF, APR, AT e S&T — mais o
verbete da jornada de focalização. [F-06, F-07] 🟡

RF-19: O SISTEMA DEVE oferecer, de dentro de cada ferramenta, acesso ao verbete daquela
ferramenta sem descarregar o trabalho em andamento. [F-05] 🟡

RF-20: O SISTEMA DEVE suportar **âncoras**: um controle de tela pode abrir a documentação
diretamente no trecho correspondente. 🟡

RF-21: QUANDO o verbete não tiver tradução no idioma efetivo, O SISTEMA DEVE apresentá-lo
na língua-fonte com aviso explícito de tradução pendente. 🟡

RF-22: Cada verbete DEVE citar a procedência da regra que descreve (spec do módulo e, quando
houver, ADR), e as citações DEVEM resolver — conferido por função de aptidão. 🟡

RF-23: A CI DEVE falhar quando existir ferramenta registrada sem verbete, ou verbete órfão
sem ferramenta, imprimindo as duas contagens. [F-06] 🟡

RF-24: O SISTEMA NÃO DEVE gerar texto de documentação em tempo de execução por modelo de
linguagem: o acervo é conteúdo revisado e versionado (ADR 0007). 🟡

### Importação do formato legado e exportação consolidada (E1.4)

RF-25: O SISTEMA DEVE aceitar, no fluxo de importação do M1, arquivos no formato exportado
pela quarta geração da linhagem, reconhecendo-os por assinatura de conteúdo — nunca pelo
nome do arquivo. [F-08] 🟡

RF-26: O SISTEMA DEVE converter o formato legado para o modelo canônico do M1 por serviço
de domínio puro, testável sem rede e sem banco. 🟡

RF-27: O SISTEMA DEVE validar o arquivo legado **inteiro antes de qualquer efeito** e, na
falha, recusar a importação completa com relato **campo a campo** (caminho do campo +
motivo), sem criar nem alterar nada. [F-09] 🟡

RF-28: QUANDO a validação passar, O SISTEMA DEVE criar um **projeto novo** com
identificadores novos e apresentar o relato com contagens por tipo de entidade — nunca
substituir projeto existente. 🟡

RF-29: O SISTEMA DEVE **descartar** o histórico de conversa (`chatHistory`) presente no
arquivo legado e declarar o descarte no relato, com a contagem de mensagens descartadas.
[F-08] 🟡

RF-30: O SISTEMA DEVE recusar arquivo acima do teto de tamanho declarado em configuração,
com código de erro categorizado, sem carregar o conteúdo na memória do serviço. 🟡

RF-31: O SISTEMA DEVE exportar um projeto multi-ferramenta num arquivo único, com seções
por ferramenta e os vínculos de encadeamento entre elas, em ordem canônica e
determinística. 🟡

RF-32: O SISTEMA DEVE garantir a ida e volta do formato consolidado: exportar, importar e
exportar de novo produz arquivo estruturalmente idêntico, a menos de identificadores e
carimbos de tempo — inclusive os vínculos entre ferramentas. 🟡

## Requisitos de interface

RI-01: O seletor de idioma é visível na superfície da aplicação, mostra o idioma efetivo e
diz de onde ele veio (do embarque ou da minha escolha). 🟡

RI-02: Trocar de idioma **não** recarrega a página nem perde trabalho em andamento; o
diagrama aberto permanece aberto. 🟡

RI-03: Nenhuma tela mistura idiomas: se o idioma efetivo é `en`, todo rótulo, estado vazio
e mensagem de erro está em `en` — conferido por captura nos dois idiomas na jornada viva. 🟡

RI-04: A documentação embutida abre em painel lateral sobre a ferramenta (não em nova
janela nem em modal bloqueante), com índice por tópico à esquerda e conteúdo à direita —
a forma que a linhagem acertou. [F-05] 🟡

RI-05: O painel de documentação tem ação explícita de fechar, devolve o foco ao controle de
origem e é operável inteiramente por teclado. 🟡

RI-06: O verbete apresenta, além do texto, ao menos um exemplo sintético da "Instituição
Horizonte" e a chamada para a ferramenta descrita quando a pessoa ainda não está nela. 🟡

RI-07: A tela de importação apresenta o relato **na própria tela**, com uma linha por
problema (campo e motivo) ou o resumo do que entrou, incluindo a linha de descarte do
histórico de conversa. 🟡

RI-08: A importação declara o formato reconhecido antes de aplicar ("arquivo da geração
anterior — será convertido"), para a pessoa saber o que vai acontecer. 🟡

RI-09: A exportação consolidada mostra o que está sendo levado (ferramentas incluídas e
número de vínculos) antes de gerar o arquivo. 🟡

RI-10: Toda superfície nova respeita o tema do hospedeiro com *fallback* e o modo
só-conteúdo do ciclo 003, e funciona de 420 pixels de largura para cima. 🟡

RI-11: Datas, horas e números aparecem formatados pelo idioma efetivo em toda tela —
inclusive nas listas e nos relatos de importação. 🟡

## Requisitos não funcionais

RNF-01: Toda mutação nova (preferência de idioma, importação) emite traço OTel
correlacionado e log estruturado com identificador de correlação — sem traço, não está
pronta (P5). 🟡

RNF-02: O domínio e a aplicação continuam sem framework, banco ou HTTP; o serviço de
conversão do formato legado é domínio puro, e `import-linter` falha o build na violação
(P3). 🟡

RNF-03: A verificação de literal órfão e a de paridade de dicionários rodam na CI de todo
pull request, e **cada uma imprime o tamanho do que examinou** (regra R2). 🟡

RNF-04: A restauração ensaiada (RF-02) é executada **uma vez dentro do ciclo**, com saída
colada; sem essa saída o ciclo não fecha — reversibilidade é entrega, não intenção. 🟡

RNF-05: Estrutura e dado evoluem em revisões separadas: nenhuma migração deste ciclo muda
esquema e linhas ao mesmo tempo, e DDL destrutivo não viaja com o seu substituto —
expandir → preencher → alternar leitura → parar de escrever → contrair. [F-13] 🟡

RNF-06: Toda migração deste ciclo tem `downgrade` testado em banco limpo, sem resíduo — o
mesmo portão do ciclo 003. 🟡

RNF-07: A importação de arquivo legado processa a validação sem bloquear o serviço para
outros usuários e respeita o teto de tamanho configurado (RF-30). 🟡

RNF-08: Importar um arquivo legado de 200 nós e 300 arestas responde em menos de 5 segundos
no percentil 95, medido no ciclo e registrado no `qa-report.md`. 🟡

RNF-09: O acervo de documentação é servido com carregamento sob demanda por verbete, de
modo que abri-lo não aumente o pacote inicial da aplicação em mais que o teto declarado
em configuração. 🟡

RNF-10: Nenhum segredo, chave ou credencial no cliente ou no repositório; as credenciais do
ensaio de restauração vêm de variável de ambiente e **não** são impressas na saída colada
(P7). 🟡

RNF-11: Nenhum dado real de pessoa entra em fixture de importação, verbete de documentação
ou captura de jornada — as fixtures são geradas por script a partir de personas fictícias
(ADR 0006), e a CI roda a busca negativa. 🟡

RNF-12: A cobertura de testes do domínio novo (conversão e validação do formato legado,
resolução de idioma efetivo) é de no mínimo 85%, com os testes nascendo antes do código
(P4). 🟡

## Regras de negócio

RN-01: A língua-fonte do produto é o **português**; toda chave existe primeiro nela, e a
tradução é derivada — nunca o contrário. [F-01] 🟡

RN-02: Termo de domínio da TOC é conceito, não rótulo: o par pt/en é declarado no glossário
do produto e a interface usa o par, jamais uma tradução livre por tela. 🟡

RN-03: Conteúdo escrito por pessoa nunca é traduzido, reformatado ou reordenado pelo
sistema. 🟡

RN-04: Uma ferramenta só é considerada entregue quando tem verbete de documentação embutida
— cobertura é regra, não meta. [F-06] 🟡

RN-05: Importação nunca muta projeto existente: o resultado é sempre projeto novo, com
identificadores novos e mapeamento relatado (regra herdada do M1, ciclo 004, RF-35). 🟡

RN-06: Todo descarte feito pela importação é **declarado no relato** — descarte silencioso é
defeito, mesmo quando é a decisão certa (é o caso do histórico de conversa). [F-08] 🟡

RN-07: Cópia gerenciada pelo provedor no mesmo armazenamento e na mesma conta é
conveniência; **backup é o que já foi restaurado com sucesso em outro lugar**. [F-11] 🟢

## Integrações

INT-01: O idioma declarado pelo embarque chega pelo envelope `ghd.*` do ciclo 003
([`../003-esqueleto-federado/spec.md`](../003-esqueleto-federado/spec.md)) — a aplicação
o **lê como dado**, nunca como instrução, e continua funcionando quando ele falta (RF-14).
🟡

INT-02: As telas novas deste ciclo (painel de documentação, tela de importação) entram no
registro de telas do ciclo 006 com identificador estável, para o *snapshot* sanitizado
compô-las sem retrabalho. 🟡

INT-03: Nenhuma ação de catálogo `toc.*` nasce neste ciclo. Trocar idioma é preferência do
titular sobre a própria interface — cabe no item 8 da constituição do projeto (alvo único
nomeado pelo gesto, valor literal no controle, reversível na sessão); importar arquivo é
mutação de projeto e segue a política por tipo de ação do ciclo 004. 🟡

INT-04: A matriz de aderência ao APH
([`../../docs/integracao/aderencia-aph.md`](../../docs/integracao/aderencia-aph.md)) é
re-verificada no pull request deste ciclo: as linhas que ele toca são a do preenchimento
estruturado de argumentos (candidata declarada ao ciclo 011) e o registro de telas, e
qualquer mudança de estado sai com evidência por caminho. 🟡

## Telas e fluxos

### 6.1 Seletor de idioma — Job: trabalhar no meu idioma sem reconfigurar · Campos: idioma efetivo, origem da escolha · Ações: trocar idioma (aplica na hora, sem recarregar)

### 6.2 Painel de documentação embutida — Job: aprender no momento da dúvida · Campos: índice por tópico, corpo do verbete, exemplo sintético, procedência · Ações: abrir por âncora, navegar entre tópicos, ir para a ferramenta, fechar devolvendo o foco

### 6.3 Importar arquivo — Job: trazer análise de fora · Campos: arquivo, formato reconhecido, relato (entradas, problemas campo a campo, descartes) · Ações: escolher arquivo, confirmar importação, abrir o projeto criado

### 6.4 Exportar consolidado — Job: levar a cadeia inteira · Campos: ferramentas incluídas, número de vínculos · Ações: exportar arquivo único determinístico

### 6.5 Estado de tradução pendente — Job: não bater em tela vazia · Campos: conteúdo na língua-fonte, aviso de pendência · Ações: continuar lendo, trocar de idioma

### 6.6 Diagnóstico de fundação (interno) — Job: provar a restauração · Campos: instante alvo, duração, o que não volta · Ações: nenhuma na interface — é relatório de ensaio anexado ao `qa-report.md`

## Entregáveis

- Mecanismo de i18n no cliente com resolução de idioma efetivo, dicionários `pt`/`en`
  versionados e persistência da preferência por (inquilino, usuário) no banco próprio.
- Duas funções de aptidão novas na CI: literal órfão e paridade de dicionários, ambas
  imprimindo o tamanho examinado.
- Acervo de documentação embutida (verbete por ferramenta, bilíngue, com âncoras e
  procedência) + função de aptidão de cobertura ferramenta × verbete.
- Serviço de domínio puro de conversão do formato legado + validação com relato campo a
  campo, com testes nascidos antes do código.
- Exportação consolidada determinística de projeto multi-ferramenta e a sua ida e volta.
- Migração Alembic (preferência de idioma) com `downgrade` testado.
- Relatório do ensaio de restauração, com objetivo de ponto e de tempo de recuperação
  declarados e o que não volta com o banco.
- Jornada viva (P6): a jornada de documentação e idioma, com captura gerada por script
  versionado do build real nos dois idiomas, e avaliação heurística datada.
- Entradas de `CHANGELOG.md`; ADR novo se a decisão de idioma padrão ou de retenção de
  formato legado for material.

## Critérios de aceite (DoD)

| # | Critério | Verificação executável |
|---|---|---|
| 1 | Domínio novo puro, testes sem rede | `pytest tests/domain/ -p no:cacheprovider` verde + `lint-imports` código 0 |
| 2 | Zero literal órfão | função de aptidão de literais: código 0 **e** a linha "N arquivos, M cadeias examinadas" colada (R2) |
| 3 | Paridade de dicionários | verificação de chaves `pt` × `en`: código 0; pendências listadas com contagem |
| 4 | Chave ausente falha alto | teste que remove uma chave: erro em desenvolvimento, CI vermelha, produção cai para a língua-fonte — nunca a chave crua |
| 5 | Idioma efetivo pela ordem declarada | teste dos três caminhos (preferência, embarque, padrão), com o motivo registrado em cada um |
| 6 | Preferência persiste no servidor | teste de integração: trocar idioma, limpar o navegador, reabrir — idioma mantido |
| 7 | Formatação localizada | teste de data/número/colação nos dois idiomas; identificador e conteúdo de pessoa inalterados |
| 8 | Cobertura de documentação | verificação ferramenta × verbete: código 0 com as duas contagens impressas; remover um verbete derruba (`TAIL:mutation`) |
| 9 | Procedência dos verbetes resolve | `scripts/check-caminhos.sh` código 0 sobre o acervo + quanto examinou |
| 10 | Conversão do formato legado | `pytest tests/domain/test_conversao_legado.py` — nó, aresta e metadados convertidos; teste nasce antes do serviço |
| 11 | Recusa campo a campo | `pytest tests/application/test_import_legado_invalido.py` — dois problemas, dois itens no relato, nada criado |
| 12 | Histórico de conversa descartado | `pytest tests/application/test_import_legado.py -k chat` — `chatHistory` não persistido; relato declara a contagem |
| 13 | Ida e volta do consolidado | `pytest tests/application/test_export_consolidado.py -k roundtrip` — vínculos recriados e contados |
| 14 | Restauração ensaiada | saída do ensaio colada no `qa-report.md`: instante alvo, duração, aplicação de pé contra o destino restaurado, o que não voltou |
| 15 | Migração reversível | `alembic upgrade head && alembic downgrade base` em banco limpo, sem resíduo, saída colada |
| 16 | Sem segredo e sem dado real | `grep -rniE "api[_-]?key\|secret" frontend/src/ \| wc -l` = 0 **e** busca negativa de nome real em fixtures/capturas = 0 |
| 17 | Jornada viva presente | `ls docs/jornadas/` contém a jornada deste ciclo com capturas nos dois idiomas |
| 18 | Conformidade, caminhos e links | `scripts/check-conformance.sh 011`, `scripts/check-caminhos.sh` e `scripts/check-links.sh` — código 0 e quanto examinaram |

## Fontes

F-01: `/home/user/tocbuilderv3/specs/feat_internationalization_full.md:1-6` — "Especificação
da Funcionalidade: Internacionalização (i18n)", data 2024-08-02, status "Em Andamento";
objetivo declarado "Traduzir 100% dos textos estáticos da interface" — a primeira das duas
specs de retrofit — uso: motivação do E8.3, RN-01 🟢

F-02: `/home/user/tocbuilderv3/specs/feat_internationalization_final_steps.md:1-4` —
"Conclusão da Internacionalização (Fase 1)", mesma data — a segunda spec, necessária porque
a primeira não terminou. Contagem executada: `ls /home/user/tocbuilderv3/specs/` devolve
**5** arquivos, **2** deles de i18n (saída colada em § O quê e por quê) — uso: argumento do
"desde o início" 🟢

F-03: `/home/user/tocbuilderv3` — medição executada:
`find . -name "*.tsx" -not -path "./node_modules/*" | wc -l` → `51`;
`grep -rL "useI18n" --include="*.tsx" . | grep -v node_modules | wc -l` → `25`. Vinte e
cinco dos cinquenta e um arquivos de componente nunca importaram o mecanismo, duas specs
depois — uso: RF-06, RF-07 🟢

F-04: `/home/user/tocbuilderv3/components/SnTView.tsx:182` (`Criar Novo Projeto S&T`) e
`/home/user/tocbuilderv3/components/SnTStepEditorModal.tsx:92,95` (`Cancelar`, `Salvar`) —
literais em português vivos no código depois das duas specs de i18n. É o defeito exato que
o portão do RF-07 existe para impedir — uso: RF-07, F8.3.2 🟢

F-05: `/home/user/tocbuilderv3/components/DocsView.tsx:17-33` — a documentação embutida da
linhagem: índice por tópico à esquerda, corpo em Markdown à direita, botão que leva à
ferramenta descrita (`handleCtaClick`), tudo pelo mecanismo de i18n. **125 linhas**
(`wc -l` executado). A forma está certa e é o precedente que este ciclo sucede — uso:
RF-19, RI-04, RI-06 🟢

F-06: `/home/user/tocbuilderv3/components/DocsView.tsx:21-26` e
`/home/user/tocbuilderv3/locales/pt.ts:426-433` — o acervo tinha **quatro** tópicos:
`intro`, `ara`, `nc`, `ai`. Duas ferramentas documentadas de seis — uso: RF-18, RF-23,
RN-04 🟢

F-07: `/home/user/tocbuilderv3/types.ts:249-258` — `TocTool` declara `ARA`, `SNT_TREE`,
`NC`, `ARF`, `APR`, `AT` (mais `USER_ADMIN`, `PROMPT_ADMIN`, `DOCS`); e
`/home/user/tocbuilderv3/locales/pt.ts:424` — a cadeia "Esta ferramenta ainda não foi
implementada." Seis ferramentas declaradas, quatro respondendo com essa frase: a razão de a
documentação cobrir duas — uso: RF-18 🟢

F-08: `/home/user/tocbuilderv3/components/NodeZoneView.tsx:187-188` — a exportação da
linhagem escreve `{ ...project, chatHistory: chatMessages }`: o **diálogo com o modelo
viaja dentro do arquivo do projeto**; o nome do arquivo é `<nome>_ARA_Export.json`
(linha 192) — uso: RF-25, RF-29, RN-06 🟢

F-09: `/home/user/tocbuilderv3/components/NodeZoneView.tsx:314-317` — a importação da
linhagem: validação rasa (`!data.name || !Array.isArray(data.nodes) ||
!Array.isArray(data.edges)`), erro por caixa de alerta do navegador, e
`chatHistory: data.chatHistory || []` reintroduzido no projeto criado — os três defeitos que
os RF-27, RF-29 e RI-07 corrigem — uso: RF-27, RF-29, RI-07 🟢

F-10: `specs/003-esqueleto-federado/` — medição executada:
`grep -rniE "backup|restaura|point-in-time" specs/003-esqueleto-federado/` devolve **duas**
linhas — `spec.md:546` ("Rollback ensaiado", que é de implantação) e `plan.md:75` ("Branch
Neon criado antes de aplicar (backup por cópia)"). Nenhuma é restauração de banco ensaiada:
é o delta que a F8.1.3 assume — uso: RF-01..RF-03, L-01 🟢

F-11: `/home/user/ghdaru/.specify/memory/constitution.md:253-261` — Princípio XII, "Um
produto é uma unidade de restauração": produtos distintos não compartilham a unidade que o
provedor restaura; "restaurar um produto nunca pode rebobinar outro"; "backup é o que já foi
restaurado com sucesso em outro lugar; cópia no mesmo armazenamento e na mesma conta é
conveniência, não apólice"; e "restauração de banco não devolve o mundo" — uso: RF-01,
RF-02, RF-03, RN-07 🟢

F-12: `/home/user/tocbuilderv3/i18n/I18nProvider.tsx:41` — `let result = translation ||
key;`: chave ausente **renderiza a própria chave** na tela, sem erro, sem log, sem portão. É
o comportamento que os RF-09 e RF-10 substituem — uso: RF-09, RF-10 🟢

F-13: `/home/user/ghdaru/.specify/memory/constitution.md:215-223` (Princípio VIII — o
esquema nasce de migração, nunca do processo; a aplicação que encontra esquema incompatível
falha no arranque com a diferença impressa), `:225-232` (IX — migração é código congelado),
`:234-241` (X — estrutura e dado em revisões separadas, expandir → contrair) e `:243-251`
(XI — o objeto é qualificado no código) — uso: RF-04, RNF-05, RNF-06 🟢

F-14: `/home/user/ghdaru/.specify/memory/constitution.md:263-268` — Princípio XIII: semente
é comando explícito que um humano digita, nunca efeito colateral de tabela vazia — uso:
RF-05 🟢

F-15: `/home/user/tocbuilderv3/locales/` — medição executada sobre as folhas de tradução
(`^\s*chave\s*:\s*"`): `/home/user/tocbuilderv3/locales/pt.ts` → `279`,
`/home/user/tocbuilderv3/locales/en.ts` → `279`. A paridade existe e
**nenhum portão a garante** — é disciplina, não invariante; os arquivos `en.json` e
`pt.json` do mesmo diretório têm `0` bytes (`wc -c` executado), restos de uma abordagem
abandonada — uso: RF-08 🟢

F-16: `/home/user/tocbuilderv3/i18n/I18nProvider.tsx:15,23-28` — a preferência de idioma
vive em `localStorage` sob a chave `toc_builder_locale`: escolha presa a um navegador, o
mesmo vício do dado (defeito D-07 da visão) aplicado à configuração — uso: RF-13 🟢

F-17: [`../../docs/produto/rounds.md`](../../docs/produto/rounds.md) — Round 011: apetite de
um ciclo, aptidão executável (nenhuma cadeia fora do dicionário, com contagem; rota de
documentação por ferramenta; import legado cria ou recusa campo a campo), "sai primeiro: o
E1.4 avançado", "nunca sai: o portão de i18n" — uso: § O que entra como dado, corte de
apetite 🟢

F-18: [`../../docs/produto/visao.md`](../../docs/produto/visao.md) §7, pergunta 5 —
"Português primeiro, com inglês desde o início — confirma?", com a proposta de manter pt/en
desde o início e o português como língua-fonte da linguagem ubíqua; e a pergunta 2, que
propõe **não** migrar nada automaticamente da linhagem: quem quiser, exporta e importa pelo
E1.4 — uso: RN-01, RN-02, RF-25 🟢

## Lacunas e assunções

L-01: A restauração ensaiada depende de recursos do provedor (cópia gerenciada e recuperação
a um ponto no tempo) cujo plano contratado não está declarado em lugar nenhum deste
repositório — assunção: o plano do projeto Neon próprio permite restaurar para um destino
separado dentro da janela declarada; se não permitir, o ensaio vira o ADR que decide a
alternativa — risco **alto** (é a diferença entre ter e não ter apólice).

L-02: O idioma declarado pelo embarque depende de o hospedeiro enviá-lo no envelope
`ghd.*`; a spec 003 não o inclui entre os quatro parâmetros de admissão — assunção: quando
ausente, a ordem do RF-12 resolve sem erro (preferência → padrão) e a lacuna vira mensagem
ao hospedeiro por `mensagens/NNN` (P1: relatar e parar) — risco **médio**.

L-03: O formato exportado pela quarta geração está medido só nas duas ferramentas que
exportavam (ARA e, por composição, a NC); ferramentas que nunca existiram nunca exportaram —
assunção: o adaptador cobre o que existe e recusa o resto com relato, em vez de fingir
converter — risco **baixo**.

L-04: O teto de crescimento do pacote inicial pela documentação embutida (RNF-09) é número a
fixar na abertura; não há medição própria ainda — assunção: carregamento sob demanda por
verbete mantém o custo marginal, e a medição real entra na jornada viva — risco **baixo**.

L-05: A função de aptidão de literal órfão tem falso positivo conhecido (cadeias de
diagnóstico, atributos técnicos) — assunção: a verificação usa lista de exceções
**declarada com motivo por linha**, no mesmo padrão do `scripts/check-caminhos.sh`, e
exceção sem motivo falha o portão — risco **médio** (uma lista de exceções sem motivo é
exatamente como um portão passa a mentir).

## Clarify

- [DÚVIDA] Idioma padrão quando o embarque não declara: português (língua-fonte, proposta
  desta spec) ou o idioma do navegador? A segunda opção agrada mais e torna a tela
  imprevisível para quem depura — o Product Steward decide antes do RF-12 congelar.
- [DÚVIDA] Retenção do formato legado: o adaptador de importação da quarta geração é
  permanente ou tem data de aposentadoria declarada (por exemplo, doze meses após a
  promoção do ciclo 011)? Sem data, ele vira dependência da linhagem — o que a visão §7
  pergunta 2 propõe evitar.
- [DÚVIDA] Verbete por ferramenta é suficiente, ou o Product Steward quer também um verbete
  de "por onde começar" que atravesse as seis ferramentas pela jornada dos cinco passos? O
  segundo custa um verbete a mais e duplica manutenção com a jornada viva do ciclo 009.
- [DÚVIDA] A preferência de idioma é por pessoa (proposta) ou por inquilino, com a
  Administradora podendo fixá-la para toda a organização? A segunda opção acrescenta uma
  regra de precedência à ordem do RF-12.
- [DÚVIDA] O ensaio de restauração é anual, por ciclo de infraestrutura, ou uma vez e
  registrado? Esta spec exige **uma vez dentro do ciclo**; a periodicidade seguinte é
  política operacional e precisa de dono.
