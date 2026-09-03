# Spec 012 — Jornadas e autodeclaração (ciclo transversal — fechamento da v1)

> Siglas: **TOC** — Teoria das Restrições · **APH** — Aplicação ↔ Harness · **ADR** —
> Architecture Decision Record (Registro de Decisão Arquitetural) · **RF/RI/RNF/RN/INT** —
> requisito funcional / de interface / não funcional / regra de negócio / integração ·
> **US** — User Story (história de usuário) · **DoD** — Definition of Done (Definição de
> Pronto) · **DoR** — Definition of Ready (Definição de Prontidão) · **P6** — princípio
> "Jornada viva" da constituição do projeto · **ARA** — Árvore da Realidade Atual · **NC**
> — Nuvem de Conflito · **ARF** — Árvore da Realidade Futura · **APR** — Árvore de
> Pré-Requisitos · **AT** — Árvore de Transição · **S&T** — Árvore de Estratégia &
> Táticas · **UDE** — Undesirable Effect (Efeito Indesejável) · **OI** — Objetivo
> Intermediário · **SSE** — *Server-Sent Events* (eventos enviados pelo servidor) ·
> **HTTP** — HyperText Transfer Protocol · **FSM** — máquina de estados finitos · **IA** —
> inteligência artificial · **LLM** — modelo de linguagem de grande porte (*Large Language
> Model*) · **UI** — interface de usuário · **UX** — experiência de usuário · **i18n** —
> internacionalização · **CI** — integração contínua · **OTel** — OpenTelemetry · **JSON**
> — JavaScript Object Notation · **eTLD+1** — domínio registrável efetivo mais um rótulo ·
> **KB** — kilobyte

- **Status**: Rascunho (aprovação: gate humano do ciclo 001)
- **Raia**: plena
- **Data**: 2026-09-03
- **Origem**: [`../../docs/roadmap.md`](../../docs/roadmap.md) (ciclo 012) ·
  [`../../docs/produto/rounds.md`](../../docs/produto/rounds.md) (round 012) ·
  [`../../docs/jornadas/README.md`](../../docs/jornadas/README.md) (as seis jornadas
  planejadas) · [`../../docs/integracao/aderencia-aph.md`](../../docs/integracao/aderencia-aph.md)
  (a matriz que este ciclo preenche)

## O quê e por quê

Este é o ciclo em que o projeto **prova o que afirmou** — e é o único ciclo da versão 1
que não entrega funcionalidade nenhuma. Ele fecha quatro contas abertas desde o ciclo 001:
as seis jornadas vivas, cada uma nascida no ciclo da sua ferramenta, viram um conjunto
consolidado que atravessa o produto de ponta a ponta; a matriz de aderência ao padrão APH,
hoje inteiramente planejada e com toda coluna de evidência vazia de propósito [F-01], é
preenchida linha a linha com caminho e teste; a suíte de conformidade executável do
**Nível 1 (Observador)** roda contra a aplicação real e o resultado é registrado, apto ou
não; e a **autodeclaração de Nível 2 (Operador), lado aplicação do Anexo B**, sai em ADR
novo — com evidência por requisito e com os limites ditos junto.

O motivo de a autodeclaração ser uma entrega, e não uma frase no `README.md`, está na
própria norma. O Nível 2 **não tem suíte executável**, e o lado aplicação do Anexo B
também não: o canal `postMessage` exige navegador, e a norma diz com todas as letras que
"uma suíte que fingisse cobri-lo seria pior que a sua ausência" [F-02]. A consequência é o
§B.12.1: quem declara conformidade **DEVE declarar por lado**, porque "somos conformes ao
Anexo B", sem dizer qual lado, é declaração vazia — metade das obrigações não é sua
[F-03]. Este ciclo escreve exatamente essa declaração: **lado aplicação**, com a maturidade
dos itens experimentais dita junto (§B.11.3) [F-04], e com os requisitos delegados à
fundação por desenho (ADR 0007) nomeados como delegação, não como conformidade nossa.

O que separa esta autodeclaração de uma auto-elogio é o método de prova. Onde há suíte,
ela roda: o Nível 1 tem **11 checks executáveis** e **12 itens que a caixa-preta não
alcança** e que seguem para autodeclaração com evidência — contagem executada nesta
leitura [F-05, F-06]. Onde não há suíte, a evidência é caminho de arquivo mais teste
próprio, e o **limite é declarado**, no mesmo espírito com que a norma declara os seus.
E há precedente do que acontece quando a régua é honesta: a primeira aplicação real medida
por essa suíte — a própria fundação `ghdaru` — saiu **NÃO APTA**, 8 de 11 checks, duas
falhas [F-07]. Um veredito negativo é um resultado legítimo deste ciclo; o que não é
legítimo é declarar sem medir.

As jornadas fecham o mesmo raciocínio pelo lado visual. A Iron Law da jornada viva é que
jornada sem captura de build real é ficção [F-08]; cada uma das seis nasceu no ciclo da
sua ferramenta, e aqui elas passam por duas provas que só existem no conjunto: **regeneram
do build atual** (uma captura que não regenera é uma captura obsoleta que ninguém viu
envelhecer) e **encadeiam** — a análise sintética da "Instituição Horizonte" atravessa da
narrativa do dilema até a AT, passando pela focalização, sem trocar de personagem no meio.

## O que entra como dado

- **As seis jornadas planejadas** ([`../../docs/jornadas/README.md`](../../docs/jornadas/README.md)):
  J-01 chegada e embarque (ciclo 003), J-02 primeiro projeto e ARA (004/005), J-03 Nuvem de
  Conflito (007), J-04 da injeção ao plano (008), J-05 focalização (009), J-06 Estratégia &
  Táticas (010). Este ciclo **não cria** jornada nova de ferramenta: consolida as que
  existem e acrescenta a travessia que liga as seis.
- **A matriz de aderência** ([`../../docs/integracao/aderencia-aph.md`](../../docs/integracao/aderencia-aph.md)):
  já traz o recorte do lado aplicação, a legenda de status e o registro de revisões; o que
  falta é evidência. A própria matriz declara que a autodeclaração formal é entrega deste
  ciclo [F-01].
- **A norma**: Padrão APH v0.8, Anexo A v0.5 (wire) e Anexo B v0.4 (federação), do
  `GHDaru/protocolos`. A **suíte do Nível 1** e os perfis de adaptação são de lá e rodam
  contra a nossa URL — leitura, nunca cópia (P1).
- **ADR 0003** ([`../../docs/adr/0003-federacao-aph-nivel-2-embedded.md`](../../docs/adr/0003-federacao-aph-nivel-2-embedded.md)):
  o alvo declarado — Nível 2 (Operador), `mode: embedded`, `app_id: toc`, namespace
  `toc.*`, servida de eTLD+1 distinto do hospedeiro. A autodeclaração deste ciclo é a
  prestação de contas daquele ADR.
- **ADR 0007** ([`../../docs/adr/0007-ia-somente-pela-fundacao.md`](../../docs/adr/0007-ia-somente-pela-fundacao.md)):
  os requisitos de porta de modelo (APH-8.1, APH-8.2, APH-2.3) são **delegados por
  desenho**; a autodeclaração registra a delegação com o motivo, e não os conta como
  nossos.
- **ADR 0008** ([`../../docs/adr/0008-site-de-produto-gerado-por-script.md`](../../docs/adr/0008-site-de-produto-gerado-por-script.md)):
  o site de produto é gerado por script versionado, nunca escrito à mão; este ciclo o
  regenera e prova que o commitado não diverge.
- **Corte de apetite** (round 012): **não sai nada** — este round já é só o essencial de
  fechamento; se estourar, corta-se escopo dos rounds anteriores. **Nunca sai** a
  autodeclaração com evidência.

## Épicos, features e user stories

> **Notação.** Este ciclo **não abre épico de módulo**: a taxonomia do ADR 0004 numera
> épico por módulo (`E<m>.<n>`), e um ciclo transversal não é um módulo. As features
> abaixo levam o prefixo `FT` (*feature transversal*) e cada uma declara **a que obrigação
> presta contas** — P6, um épico de M7, uma cláusula do Anexo B ou um ADR.

### Frente 1 — Jornadas vivas consolidadas *(presta contas ao P6, em M1–M6)*

**FT-01 — Regeneração de todas as capturas a partir do build atual** — cada jornada é
reexecutada pelo seu script versionado contra o build de produção do momento do
fechamento.

- US-01 — Como **Product Steward**, quero saber que nenhuma captura do repositório
  envelheceu sem ninguém ver, para a documentação visual não virar ficção retroativa.
  - Dado o conjunto de scripts de captura das seis jornadas, Quando os executo contra o
    build atual, Então todas as capturas são regeradas e a comparação com as commitadas é
    vazia — ou a diferença é apresentada como **achado**, com a jornada afetada nomeada.

**FT-02 — Travessia de ponta a ponta com uma persona só** — uma sétima jornada, de
integração, que atravessa da narrativa do dilema até a AT sem trocar de personagem.

- US-02 — Como **Facilitadora TOC**, quero ver a análise da "Instituição Horizonte"
  atravessar da NC à AT como uma história só, para conferir que as ferramentas realmente se
  encadeiam — e não que cada uma funciona sozinha.
  - Dado o projeto sintético da "Instituição Horizonte", Quando percorro a travessia
    completa (ARA → NC → ARF → APR → AT, com a focalização costurando), Então cada elo
    aparece em captura do build real, o UDE que abre a análise é o mesmo que fecha, e a
    jornada declara em que ciclo cada tela nasceu.

**FT-03 — Avaliação heurística datada do conjunto** — uma avaliação do produto inteiro, com
quem avaliou, quando, em que contexto e o que ficou de fora.

- US-03 — Como **Gestora**, quero ler uma avaliação de usabilidade do produto inteiro, e
  não seis avaliações de seis telas, para saber onde a experiência quebra entre ferramentas.
  - Dado o conjunto consolidado, Quando leio a avaliação, Então ela é datada, nomeia o
    limite (quem avaliou, em que contexto, o que não foi avaliado) e cada achado sai com
    severidade e destino: corrigido neste ciclo, ou registrado como dívida com dono.

**FT-04 — Índice de jornadas sem captura órfã** — toda captura é citada por exatamente uma
jornada; toda jornada aponta o ciclo em que nasceu.

- US-04 — Como **agente novo neste repositório**, quero um índice que diga onde está cada
  jornada e o que ela prova, para não reconstruir o mapa por leitura de diretório.
  - Dado o diretório de jornadas, Quando a função de aptidão o percorre, Então nenhuma
    captura fica sem jornada que a cite, nenhuma jornada cita captura inexistente, e as
    duas contagens aparecem na saída.

### Frente 2 — Matriz de aderência preenchida *(presta contas a E7.3–E7.6 de M7)*

**FT-05 — Evidência por linha, com caminho e teste** — cada requisito da matriz recebe
veredito e evidência; célula vazia é defeito de aceite.

- US-05 — Como **Administradora do inquilino** que precisa admitir esta aplicação, quero
  uma matriz em que cada linha diga o que foi feito e onde ver, para a admissão ser
  conferência e não confiança.
  - Dado o documento de aderência, Quando abro qualquer linha de status atendido, Então
    encontro caminho de arquivo e o teste ou a saída que a sustenta; Quando abro uma linha
    parcial, Então encontro **o que falta**, nomeado.

**FT-06 — Delegação declarada, nunca contada como conformidade** — os requisitos que a
fundação cumpre por desenho aparecem como delegação, com o motivo e o ADR.

- US-06 — Como **revisora independente**, quero distinguir "nós cumprimos" de "a fundação
  cumpre por nós", para a matriz não inflar a nossa metade.
  - Dado um requisito de porta de modelo, Quando leio a linha, Então ela diz que a
    obrigação é da fundação por desenho (ADR 0007), qual metade continua nossa, e onde
    essa metade está provada.

**FT-07 — Fora do alvo com porta de volta** — o que a versão 1 não faz é dito com a
condição que o traria de volta.

- US-07 — Como **Product Steward**, quero que cada item fora do alvo diga o que o traria de
  volta, para a decisão de escopo ser revisável em vez de esquecida.
  - Dado um requisito marcado fora do alvo, Quando o leio, Então encontro a condição de
    reentrada escrita ("volta quando houver segunda classe de ação com consequência
    distinta", por exemplo) — nunca só a marca.

### Frente 3 — Conformidade executável do Nível 1 *(presta contas a E7.6 de M7)*

**FT-08 — Execução da suíte contra a aplicação real** — a suíte de caixa-preta do
`GHDaru/protocolos` roda contra a nossa URL publicada, e o relatório inteiro é registrado.

- US-08 — Como **Product Steward**, quero o veredito de uma ferramenta que não escrevemos,
  medindo a nossa aplicação, para a conformidade do Nível 1 não depender da nossa própria
  opinião.
  - Dado o endereço publicado da aplicação, Quando a suíte roda, Então o relatório
    integral entra no repositório com data, versão da norma, alvo e revisão medida — e o
    veredito, apto ou **não apto**, entra como está.

**FT-09 — Perfil de adaptação, se e só se necessário, e sempre versionado** — o perfil
traduz endereço e vocabulário; jamais isenta.

- US-09 — Como **revisora independente**, quero que qualquer tradução aplicada pelo perfil
  esteja no relatório, para conseguir distinguir adaptação de lavagem.
  - Dado que a nossa superfície usa nomes locais, Quando a suíte roda com perfil, Então o
    perfil está versionado no repositório, o relatório lista cada tradução aplicada, e
    nenhuma operação é declarada ausente para escapar de um check — declarar ausente **faz
    o check falhar** [F-09].

**FT-10 — Os itens não observáveis de fora, autodeclarados com evidência** — o que a
caixa-preta não alcança segue para a autodeclaração, um a um.

- US-10 — Como **revisora independente**, quero ver os itens que a suíte não alcança
  listados com a evidência interna de cada um, para a diferença entre "verificado" e
  "declarado" ficar visível.
  - Dado o relatório da suíte, Quando leio a seção dos itens declarados, Então cada um tem
    caminho de arquivo e o teste próprio que o sustenta, e nenhum deles aparece contado
    como verificado.

### Frente 4 — Autodeclaração em ADR e site regenerado *(presta contas ao §B.11.3/§B.12.1 e ao ADR 0008)*

**FT-11 — ADR de autodeclaração, por lado e com maturidade** — a declaração formal de
Nível 2 (Operador), lado aplicação do Anexo B, sai como ADR com evidência por requisito.

- US-11 — Como **Product Steward**, quero assinar uma declaração que diga de qual lado ela
  fala e o que ainda é experimental, para poder mostrá-la fora do repositório sem
  ressalva verbal.
  - Dado o ADR de autodeclaração, Quando o leio, Então ele diz **lado aplicação**, cita a
    cláusula que obriga a dizer o lado, declara a maturidade dos itens experimentais que
    nos tocam, e nomeia o que não temos: suíte executável para o Nível 2 e para o lado
    aplicação do Anexo B.
- US-12 — Como **Administradora do inquilino**, quero que a declaração aponte a data e a
  revisão exatas do que foi medido, para saber quando ela envelheceu.
  - Dado o ADR, Quando comparo com o repositório meses depois, Então encontro data,
    versões da norma (padrão, Anexo A, Anexo B) e a revisão medida — e a instrução de
    refazer a medição em vez de supor.

**FT-12 — Site de produto regenerado pelo gerador versionado** — o site é saída de script;
o commitado não diverge do gerado.

- US-13 — Como **pessoa de fora do projeto**, quero um site que reflita as specs e os
  requisitos de verdade, para não ler uma versão parada no tempo.
  - Dado o corpus atualizado, Quando o gerador roda, Então o site regenerado é idêntico ao
    commitado (diferença vazia na CI) e as contagens que ele exibe são derivadas dos
    arquivos, nunca digitadas.

## Entidades e modelo de domínio

**Nenhuma entidade de domínio nasce neste ciclo, e isso é declaração, não esquecimento**:
o round 012 não entrega funcionalidade ([`../../docs/produto/rounds.md`](../../docs/produto/rounds.md),
"Fora: qualquer funcionalidade nova — round de fechamento não esconde feature"). Os objetos
manipulados aqui são **artefatos**, não agregados:

- **Jornada**: documento datado + capturas geradas por script + avaliação heurística. A
  invariante que o portão verifica: toda captura é citada por exatamente uma jornada, e
  toda jornada declara o ciclo em que nasceu.
- **Linha de aderência**: requisito da norma + veredito + evidência (caminho e teste) +
  limite quando parcial. Invariante: veredito de atendimento **exige** evidência não vazia;
  delegação exige motivo e ADR.
- **Execução de conformidade**: relatório integral da suíte, com data, versão da norma,
  alvo, revisão medida e perfil aplicado, se houver. Invariante: registro imutável —
  medição nova é registro novo, nunca reescrita do anterior.
- **Autodeclaração**: ADR com lado declarado, maturidade dos itens experimentais, evidência
  por requisito e limites. Invariante do método: ADR não se reescreve; se a declaração
  mudar, nasce ADR que sucede o anterior, com `**Sucede**` no novo e `Superseded by` no
  antigo (regra R5).

## Requisitos funcionais

### Jornadas vivas consolidadas

RF-01: O SISTEMA DE DOCUMENTAÇÃO DEVE regerar todas as capturas de todas as jornadas a
partir do build atual, por script versionado, e a regeneração DEVE ser determinística —
duas execuções sem mudança de código produzem imagens idênticas. [F-08] 🟡

RF-02: QUANDO uma captura regerada divergir da commitada, O CICLO DEVE tratar a divergência
como **achado nomeado** (qual jornada, qual captura, o que mudou), nunca como atualização
silenciosa. 🟡

RF-03: O CICLO DEVE entregar uma jornada de travessia de ponta a ponta que atravesse ARA →
NC → ARF → APR → AT com a focalização costurando, usando **uma única persona sintética** do
início ao fim. [F-10] 🟡

RF-04: A jornada de travessia DEVE declarar, elo a elo, em que ciclo a tela mostrada
nasceu, ligando cada captura à spec do módulo correspondente. 🟡

RF-05: O CICLO DEVE produzir uma **avaliação heurística datada do conjunto**, com quem
avaliou, em que contexto, o que **não** foi avaliado, e cada achado com severidade e
destino (corrigido aqui, ou dívida registrada com dono). [F-08] 🟡

RF-06: O CICLO DEVE manter um índice de jornadas em que cada entrada aponte o ciclo de
nascimento, o estágio (protótipo, viva) e as capturas que a sustentam. [F-11] 🟡

RF-07: A CI DEVE falhar quando existir captura não citada por nenhuma jornada, ou jornada
citando captura inexistente, **imprimindo as duas contagens**. 🟡

### Matriz de aderência com evidência

RF-08: O CICLO DEVE preencher a matriz de aderência ao APH de modo que **nenhuma célula de
evidência fique vazia** em linha cujo status seja atendido ou parcial. [F-01] 🟡

RF-09: Cada linha atendida DEVE citar caminho de arquivo **e** o teste, a saída de suíte ou
a captura que a sustenta — evidência é caminho, não adjetivo. 🟡

RF-10: Cada linha parcial DEVE nomear **o que falta**, e cada linha fora do alvo DEVE
declarar a **condição de reentrada**. 🟡

RF-11: Cada linha delegada à fundação DEVE declarar a delegação, o ADR que a decide e **a
metade que continua nossa**, com a evidência dessa metade. [F-12] 🟡

RF-12: O CICLO DEVE registrar a revisão da matriz no seu próprio registro de revisões (data,
o que mudou, por quem) e re-verificá-la no mesmo pull request de qualquer mudança de
fronteira. [F-01] 🟡

### Conformidade executável do Nível 1

RF-13: O CICLO DEVE executar a suíte de conformidade do Nível 1 do `GHDaru/protocolos`
contra a **URL publicada da aplicação**, e registrar o relatório integral no repositório.
[F-05] 🟡

RF-14: O registro da execução DEVE conter data, versão da norma medida, alvo (endereço),
revisão do nosso código, perfil aplicado (se houver) e o **veredito como saiu** — inclusive
quando for "não apto". [F-07] 🟡

RF-15: QUANDO a nossa superfície divergir do canônico em endereço ou vocabulário, O CICLO
DEVE usar **perfil de adaptação versionado no nosso repositório**, e o relatório DEVE listar
cada tradução aplicada. [F-09] 🟡

RF-16: O perfil NÃO DEVE declarar operação ausente para escapar de um check: declarar
ausente faz o check **falhar**, e é assim que ele deve ser usado. [F-09] 🟡

RF-17: Os itens que a caixa-preta não alcança DEVEM ser listados um a um, cada um com a
evidência interna (caminho e teste próprio), e NÃO DEVEM ser contados como verificados.
[F-06] 🟡

RF-18: QUANDO o veredito da suíte for "não apto", O CICLO DEVE registrar cada falha com a
decisão associada — corrigir neste ciclo, ou declarar a lacuna com dono e prazo —, e a
autodeclaração DEVE refletir o estado real. [F-07] 🟡

### Autodeclaração e site

RF-19: O CICLO DEVE produzir um ADR de **autodeclaração de conformidade** que declare
explicitamente o **lado aplicação** do Anexo B, citando a cláusula que obriga a declaração
por lado. [F-03] 🟡

RF-20: A autodeclaração DEVE vir acompanhada da **maturidade dos itens experimentais** que
nos tocam, na forma que a norma exige. [F-04] 🟡

RF-21: A autodeclaração DEVE nomear os limites da própria prova: não há suíte executável
para o Nível 2, nem para o lado aplicação do Anexo B — e dizer por quê (o canal exige
navegador). [F-02] 🟡

RF-22: A autodeclaração DEVE ter uma linha por requisito do alvo declarado, com veredito e
evidência, derivada da matriz de aderência — uma fonte, duas apresentações, jamais duas
verdades. 🟡

RF-23: O CICLO DEVE regerar o site de produto pelo gerador versionado e provar que o
commitado não diverge do gerado (diferença vazia na CI). [F-13] 🟡

RF-24: Toda contagem exibida no site (requisitos, specs, ciclos, jornadas) DEVE ser
derivada dos arquivos pelo gerador, nunca digitada. [F-13] 🟡

## Requisitos de interface

RI-01: O índice de jornadas apresenta as seis jornadas mais a travessia, cada uma com
ciclo de nascimento, estágio e número de capturas. 🟡

RI-02: A jornada de travessia apresenta os elos em ordem narrativa, com uma captura por
elo e o nome do ciclo em que a tela nasceu ao lado de cada captura. 🟡

RI-03: A avaliação heurística apresenta os achados em tabela — severidade, tela, achado,
destino —, com o limite da avaliação declarado antes da tabela, não em nota de rodapé. 🟡

RI-04: O site de produto oferece navegação por módulo, por ciclo e por requisito, com
rastreabilidade nos dois sentidos (do requisito à fonte e da fonte aos requisitos que a
usam). 🟡

RI-05: O site expõe uma **nota de honestidade**: o que está implementado, o que está
planejado e o que é lacuna — com a mesma legenda de selos usada nas specs. 🟡

RI-06: Nenhuma captura de jornada, e nenhuma página do site, contém dado real de pessoa: as
telas capturadas exibem exclusivamente a base sintética. 🟡

## Requisitos não funcionais

RNF-01: A regeneração das capturas roda em ambiente controlado e versionado (mesma
resolução, mesmo tema, mesma base sintética), para que a diferença detectada seja mudança
de produto e não de ambiente. 🟡

RNF-02: O relatório de execução da suíte é **registro imutável**: medição nova entra como
registro novo com data própria; o anterior não é reescrito. 🟡

RNF-03: A execução da suíte NÃO DEVE exigir credencial gravada em arquivo: quando houver
autenticação, ela vem de variável de ambiente e o token não é impresso nem versionado
(P7). [F-09] 🟡

RNF-04: A geração do site é determinística: duas execuções sobre o mesmo corpus produzem
saída byte-idêntica, o que torna o portão de divergência confiável. [F-13] 🟡

RNF-05: A verificação de captura órfã e a de célula vazia da matriz rodam na CI e **imprimem
o tamanho do que examinaram** (regra R2). 🟡

RNF-06: Nenhum dado real de pessoa em captura, fixture, relatório de execução ou página do
site — busca negativa executada na CI (ADR 0006). 🟡

RNF-07: A execução da suíte contra a URL publicada não altera dado de produção: roda contra
ambiente ou inquilino de teste com base sintética, e o registro declara contra qual. 🟡

RNF-08: Toda afirmação factual do ADR de autodeclaração — contagem de requisitos, número de
checks, veredito — é **executada e colada**, nunca transcrita (regra R1). 🟡

## Regras de negócio

RN-01: Conformidade se declara **por lado**. Uma declaração que não diga se fala do
hospedeiro, da aplicação ou dos dois é declaração vazia — metade das obrigações não é sua.
[F-03] 🟢

RN-02: Onde existe suíte, ela roda; onde não existe, a evidência é caminho mais teste
próprio **e o limite é declarado**. Nunca se declara verificado o que só foi afirmado.
[F-02, F-06] 🟢

RN-03: Perfil de adaptação é dicionário, não isenção: traduz endereço e vocabulário, e
declarar operação ausente faz o check falhar. [F-09] 🟢

RN-04: Veredito negativo é resultado legítimo e entra no repositório como saiu; o que não
é legítimo é declarar sem medir. [F-07] 🟡

RN-05: Registro de execução e ADR de autodeclaração são **história**: corrigem-se por
acréscimo (registro novo, ADR que sucede), nunca por reescrita — regra R5 e o guarda do
método. 🟡

RN-06: Jornada sem captura de build real é ficção, e captura que não regenera é captura que
envelheceu sem testemunha. [F-08] 🟢

## Integrações

INT-01: A suíte do Nível 1 é executada **de fora**, contra a URL publicada — o
`GHDaru/protocolos` permanece leitura (P1); nada dele é copiado para cá. O que fica aqui é
o **perfil** (se houver) e o **registro da execução**. 🟡

INT-02: A autodeclaração cobre o alvo do ADR 0003 — Nível 2 (Operador), `mode: embedded`,
lado aplicação do Anexo B — e nada além; o lado hospedeiro não é nosso para declarar.
[F-03] 🟡

INT-03: Lacuna encontrada na norma ou na fundação durante a medição **não se corrige lá**:
vira `mensagens/NNN-para-<repo>-<assunto>.md` com evidência por `arquivo:linha` e o commit
lido (P1: relatar e parar). 🟡

INT-04: O site de produto consome as specs, os ADRs e as jornadas como entrada do gerador
versionado (ADR 0008); a autodeclaração publicada no site é **a mesma** do ADR, gerada dele,
não redigida de novo. 🟡

## Telas e fluxos

### 6.1 Índice de jornadas — Job: achar a prova visual de qualquer ferramenta · Campos: jornada, ciclo de nascimento, estágio, número de capturas · Ações: abrir a jornada, abrir a travessia

### 6.2 Jornada de travessia — Job: ver as ferramentas se encadearem numa história só · Campos: elo, captura, ciclo em que a tela nasceu · Ações: percorrer os elos em ordem

### 6.3 Avaliação heurística do conjunto — Job: saber onde a experiência quebra entre ferramentas · Campos: limite declarado, severidade, tela, achado, destino · Ações: nenhuma (documento datado)

### 6.4 Matriz de aderência — Job: conferir a fronteira requisito a requisito · Campos: requisito, maturidade, status, evidência (caminho + teste) · Ações: seguir a evidência até o arquivo

### 6.5 Site de produto — Job: apresentar o produto para fora com rastreabilidade · Campos: módulos, ciclos, requisitos, fontes, nota de honestidade · Ações: navegar nos dois sentidos da rastreabilidade

## Entregáveis

- As seis jornadas com capturas regeradas do build atual, mais a **jornada de travessia** de
  ponta a ponta com persona única.
- Avaliação heurística datada do conjunto, com limite declarado e achados com destino.
- Função de aptidão de captura órfã (dois sentidos) e de célula vazia na matriz.
- [`../../docs/integracao/aderencia-aph.md`](../../docs/integracao/aderencia-aph.md)
  preenchida linha a linha, com o registro de revisão datado.
- Registro da execução da suíte de conformidade do Nível 1 contra a URL publicada, com o
  relatório integral, e o perfil de adaptação versionado se tiver sido necessário.
- **ADR de autodeclaração** — Nível 2 (Operador), lado aplicação do Anexo B — com evidência
  por requisito, maturidade dos itens experimentais e limites declarados; entrada no índice
  de ADRs e linha no índice de decisões por `scripts/record-decision.sh`.
- Site de produto regenerado pelo gerador versionado, com o portão de divergência na CI.
- Entradas de `CHANGELOG.md` e a retrospectiva do fechamento da versão 1.

## Critérios de aceite (DoD)

| # | Critério | Verificação executável |
|---|---|---|
| 1 | Todas as capturas regeneram do build atual | script de captura de cada jornada + `diff` das imagens: diferença vazia, **ou** achado nomeado; saída colada |
| 2 | Regeneração determinística | duas execuções seguidas do mesmo script + `diff` vazio |
| 3 | Nenhuma captura órfã, nenhuma citação quebrada | função de aptidão nos dois sentidos: código 0 e as duas contagens impressas |
| 4 | Jornada de travessia com persona única | leitura verificada: um único conjunto de personas do primeiro ao último elo; nenhum nome fora da base sintética |
| 5 | Avaliação heurística datada e limitada | o documento traz data, avaliador, contexto, o que não foi avaliado, e destino por achado |
| 6 | Matriz sem célula de evidência vazia | função de aptidão sobre a tabela: nenhuma linha atendida ou parcial com evidência vazia; contagem por status impressa |
| 7 | Evidência da matriz resolve | `scripts/check-caminhos.sh` código 0 + quanto examinou |
| 8 | Suíte do Nível 1 executada contra a URL publicada | relatório integral colado no registro, com data, alvo, versão da norma e veredito como saiu |
| 9 | Perfil (se usado) versionado e sem isenção | o perfil está no repositório; o relatório lista as traduções aplicadas; nenhuma operação declarada ausente |
| 10 | Itens não observáveis listados com evidência interna | um item por linha com caminho e teste; nenhum contado como verificado |
| 11 | ADR de autodeclaração com lado e maturidade | `grep -n "lado aplicação" docs/adr/00*autodeclaracao*.md` e leitura: cláusula citada, maturidade declarada, limites nomeados |
| 12 | Autodeclaração derivada da matriz | conferência linha a linha: todo requisito do alvo aparece nos dois, com o mesmo veredito |
| 13 | ADR no índice e no registro de decisões | `scripts/check-adr.sh` código 0; linha gravada por `scripts/record-decision.sh` |
| 14 | Site regenerado sem divergência | gerador + `diff` contra o commitado: diferença vazia, código 0 |
| 15 | Contagens do site derivadas dos arquivos | sabotagem: acrescentar um requisito a uma spec muda a contagem exibida sem edição manual |
| 16 | Sem dado real de pessoa | busca negativa em capturas, relatórios e páginas do site = 0, com o tamanho examinado |
| 17 | Conformidade, caminhos e links | `scripts/check-conformance.sh 012`, `scripts/check-caminhos.sh` e `scripts/check-links.sh` — código 0 e quanto examinaram |

## Fontes

F-01: [`../../docs/integracao/aderencia-aph.md`](../../docs/integracao/aderencia-aph.md) —
a matriz do lado aplicação, com o estado honesto declarado no cabeçalho ("Nada foi
implementado; nenhuma linha está atendida; toda coluna de evidência está vazia de
propósito"), a legenda de status, a linha `§B.11.3 / §B.12.1` marcada "planejado — ciclo
012 (autodeclaração em ADR)" e o registro de revisões — uso: RF-08..RF-12, INT-02 🟢

F-02: `/home/user/protocolos/padrao/anexo-b-federacao.md:215` — §B.12.2: o lado do
hospedeiro tem verificação executável; o **lado da aplicação não tem**, "porque o canal
exige navegador, e uma suíte que fingisse cobri-lo seria pior que a sua ausência". Reforçado
em `:193` (§B.11.2): "quem declara o lado da aplicação declara sem suíte" — uso: RF-21,
RN-02 🟢

F-03: `/home/user/protocolos/padrao/anexo-b-federacao.md:213` — §B.12.1: "Quem declara
conformidade **DEVE** declarar **por lado**, e a declaração de um lado não fala pelo outro.
'Somos conformes ao Anexo B', sem dizer qual lado, é declaração vazia: metade das obrigações
não é sua." — uso: RF-19, RN-01, INT-02 🟢

F-04: `/home/user/protocolos/padrao/anexo-b-federacao.md:199` — §B.11.3: declarar
conformidade ao Anexo B "DEVE vir acompanhada de qual lado se implementou (hospedeiro,
aplicação, ou ambos) e da maturidade dos itens 🧪 desta versão, que hoje são pelo menos o
§B.6.6 e o §B.6.7" — uso: RF-20 🟢

F-05: `/home/user/protocolos/conformidade/README.md:9-12` — como a suíte roda: `node
suite.mjs https://sua-app.exemplo.com`, caixa-preta contra uma URL, "exit 0 = apto nos itens
verificáveis" — uso: RF-13, INT-01 🟢

F-06: `/home/user/protocolos/conformidade/README.md:66-78,115` — contagem executada:
`grep -cE "^\| \`[a-z-]+\` \| " README.md` → `11` (os checks executáveis, de
`superficie-sessao` a `snapshot-fechado`); e a contagem das entradas de `DECLARADOS` em
`suite.mjs` → `12`. O README fecha a conta: "o Nível 1 completo = 11 verificados + 12
declarados" — uso: RF-17, RN-02 🟢

F-07: `/home/user/protocolos/conformidade/execucoes/2026-08-06-ghdaru.md:11` — a primeira
aplicação real medida pela suíte, a própria fundação: "**NÃO APTO ao Nível 1 (Observador)**
— 8 de 11 checks verificados, 1 aviso, **2 falhas**". O registro traz data, commit medido e
o aviso de que num commit posterior as linhas derivam — "refaça a medição em vez de supor" —
uso: RF-14, RF-18, RN-04, RNF-02 🟢

F-08: [`../../docs/jornadas/README.md`](../../docs/jornadas/README.md) — a Iron Law
("jornada sem captura de build real é ficção"), as quatro condições de nascimento de uma
jornada (build real → script versionado → documento com avaliação datada → nenhuma captura
órfã) e a proibição de dado real de pessoa — uso: RF-01, RF-05, RF-07, RN-06 🟢

F-09: `/home/user/protocolos/conformidade/README.md:16-38` — perfis de adaptação: "um perfil
é um **dicionário**, não uma isenção"; as três defesas ("Não existe campo de isenção" —
declarar `"cancelar": null` **faz o check falhar**; o mapa de nomes é validado na carga; toda
tradução aplicada aparece no relatório); "credenciais nunca entram no arquivo", só os nomes
das variáveis de ambiente; e o limite honesto declarado — uso: RF-15, RF-16, RNF-03, RN-03 🟢

F-10: [`../../docs/jornadas/README.md`](../../docs/jornadas/README.md) — a tabela das seis
jornadas planejadas (J-01 chegada e embarque · J-02 primeiro projeto e ARA · J-03 Nuvem de
Conflito · J-04 da injeção ao plano · J-05 focalização · J-06 Estratégia & Táticas), com o
ciclo em que cada uma nasce — uso: RF-03, RF-06, RI-01 🟢

F-11: [`../../docs/produto/rounds.md`](../../docs/produto/rounds.md) — Round 012: entrega,
aptidão executável ("todas as capturas de todas as jornadas regeneram do build atual"; "a
matriz tem um veredito por requisito APH com evidência por caminho, sem célula vazia"; "o
site regenerado não diverge do commitado"), "Sai primeiro: nada", "Nunca sai: a
autodeclaração em ADR — é o 'prove, não declare' aplicado ao projeto inteiro" — uso: RF-06,
RF-08, RF-23, § Corte de apetite 🟢

F-12: [`../../docs/adr/0007-ia-somente-pela-fundacao.md`](../../docs/adr/0007-ia-somente-pela-fundacao.md)
e as linhas ✦ da matriz ([F-01]) — os requisitos de porta de modelo são delegados **por
desenho**: quem fala com provedor é a fundação, e a metade "chave nunca no cliente" continua
nossa (P7) — uso: RF-11, FT-06 🟢

F-13: [`../../docs/adr/0008-site-de-produto-gerado-por-script.md`](../../docs/adr/0008-site-de-produto-gerado-por-script.md)
— o site é gerado pelo `spec-to-code-docs` vendorizado, nunca escrito à mão; contagens
derivadas dos arquivos — uso: RF-23, RF-24, RNF-04 🟢

F-14: `/home/user/protocolos/conformidade/README.md:113-116` — os limites declarados da
suíte: "**Não cobre os Níveis 2 e 3** (ações governadas, comandos de UI, federação)"; "**Não
substitui a autodeclaração**"; "**Testa o servidor, não o cliente**". É a razão de a nossa
prova de Nível 2 ser autodeclaração com evidência, e de dizermos isso junto — uso: RF-21,
RN-02, L-01 🟢

F-15: `/home/user/protocolos/padrao/anexo-b-federacao.md:209-211` — a matriz de obrigações
do anexo é **dado, não prosa**: 49 obrigações ao todo (44 do anexo mais 5 do §4.9), das
quais **25 do hospedeiro, 8 da aplicação e 16 de ambos**; 17 verificadas por suíte (4 com
cobertura parcial declarada), 6 por schema e 26 por autodeclaração com motivo — uso: RF-22,
INT-02, L-02 🟢

## Lacunas e assunções

L-01: **Não existe suíte executável para o Nível 2 nem para o lado aplicação do Anexo B**
([F-02], [F-14]) — assunção: a prova é autodeclaração com evidência por caminho mais teste
próprio, com o limite dito junto; o risco de erro de autoavaliação é **nosso** e a mitigação
é a revisão independente em contexto fresco — risco **médio**.

L-02: A matriz de obrigações do Anexo B atribui **8 cláusulas exclusivamente à aplicação e
16 a ambos os lados** ([F-15]); as 16 compartilhadas só fecham se o hospedeiro fizer a sua
metade — assunção: declaramos a nossa metade com evidência e registramos o estado da outra
como observado, nunca como nosso; divergência vira `mensagens/NNN` — risco **médio**.

L-03: A execução da suíte exige a aplicação **publicada e alcançável** por HTTP no momento
do fechamento — assunção: o ambiente de teste com base sintética está de pé e o registro
declara contra qual ambiente rodou (RNF-07); se só houver produção, a execução é adiada em
vez de ser feita contra dado real — risco **baixo**.

L-04: A avaliação heurística é feita por quem trabalha no projeto, não por pessoa externa —
assunção: o limite é **declarado no próprio documento** (quem avaliou, em que contexto, o
que não foi avaliado), que é o que a torna útil apesar do viés; avaliação externa fica como
porta de volta declarada — risco **médio**.

L-05: A regeneração determinística de capturas depende de ambiente controlado (resolução,
tema, fontes, base sintética) que ainda não existe versionado — assunção: o ciclo 003 deixa
a base do script de captura e os ciclos seguintes a mantêm; se a determinismo não se
sustentar, o portão da DoD 2 vira comparação tolerante **declarada**, nunca silenciosa —
risco **médio**.

## Clarify

- [DÚVIDA] Se a suíte do Nível 1 sair **não apta** no fechamento, o ciclo 012 corrige as
  falhas dentro dele (estourando o apetite de um ciclo) ou fecha declarando a lacuna com
  dono e prazo? O round 012 diz que nada sai deste round — o que empurra para a segunda
  opção, mas a decisão é do Product Steward.
- [DÚVIDA] A autodeclaração é publicada fora do repositório (site de produto, manifesto
  entregue à fundação) já neste ciclo, ou fica interna até uma revisão externa? É ela que
  circula, e a decisão muda o nível de escrutínio exigido antes do gate.
- [DÚVIDA] Avaliação heurística por pessoa externa ao projeto: entra na versão 1 ou é
  dívida declarada para depois? (L-04)
- [DÚVIDA] A jornada de travessia vira a **sétima** jornada permanente do índice, ou é um
  documento de fechamento datado que não se mantém a cada ciclo seguinte? A primeira opção
  acrescenta manutenção contínua; a segunda perde a prova de encadeamento nas versões
  seguintes.
- [DÚVIDA] Periodicidade de reexecução da suíte depois da versão 1: a cada ciclo que toque
  a fronteira, a cada versão da norma, ou por calendário? Sem dono e período, o registro
  envelhece exatamente como a norma avisa que envelhece.
