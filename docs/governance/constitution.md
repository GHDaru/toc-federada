# Constituição do projeto TOC Federada

> Fonte de verdade **deste projeto**. Prevalece sobre qualquer outra prática daqui.
> **Todo agente e todo humano deve ler este documento antes de qualquer trabalho.**
> Emendas passam por um Registro de Decisão Arquitetural (ADR, do inglês *Architecture
> Decision Record*) mais um incremento de versão.
>
> **Versão**: 1.0.0 · **Ratificada**: 2026-09-03 · **Emendas**: nenhuma ainda — toda
> emenda futura entra por ADR que declare o princípio tocado e incremente esta versão ·
> **Registro**: ADR 0001
>
> Esta constituição **não substitui** a do método. A constituição do Maestro
> ([`principles.md`](principles.md), princípios I–VIII) continua valendo integralmente e é
> lida primeiro; esta acrescenta o que é próprio desta aplicação. Em conflito aparente,
> vale a leitura que satisfaz as duas — e, se não houver, o Maestro prevalece e a
> divergência vira ADR.

## Por que existe uma segunda constituição

O Maestro governa **como se trabalha** (especificação como fonte de verdade, portões
humanos, prova em vez de alegação). Ele não diz — nem deveria dizer — que esta aplicação
é federada, que o domínio da Teoria das Restrições (TOC) é puro, que a base de dados é
sintética, que a telemetria nasce junto com a funcionalidade. Essas são decisões **deste
produto**. Misturá-las na constituição do método corromperia o método para todo
repositório que o instala; separá-las mantém as duas verdadeiras.

Os princípios abaixo não foram deduzidos em abstrato: P1–P7 são herança direta da
constituição da irmã `gestaodeprioridades` (a primeira aplicação candidata à federação),
já com as emendas que ela pagou para aprender incorporadas ao texto — em particular o
alcance declarado do P2, que lá exigiu emenda constitucional (ADR 0011→0016 de lá) e aqui
nasce escrito. A herança e suas adaptações estão registradas no ADR 0001.

## Princípios

### P1. Fronteira de escrita única (INEGOCIÁVEL)

O agente escreve **somente** no repositório `GHDaru/toc-federada`. Os repositórios
`GHDaru/maestro`, `GHDaru/protocolos`, `GHDaru/ghdaru`, `GHDaru/gestaodeprioridades`, a
linhagem TOC-Builder e qualquer outro são **fonte de leitura**, nunca destino de escrita.

Quando o trabalho parecer exigir uma alteração fora daqui — corrigir uma lacuna no
instalador do Maestro, ajustar um schema do protocolo, apontar um defeito na fundação — o
agente **relata a lacuna e para**: o relato vira artefato versionado em
`mensagens/NNN-para-<repo>-<assunto>.md` (convenção em `../../mensagens/README.md`), com
evidência por `arquivo:linha` e o commit lido. A alteração externa só acontece com
**aprovação humana explícita e por escrito**, para aquele repositório e aquela mudança;
uma aprovação não se estende à seguinte.

Violar a letra viola o espírito. Não são desculpas: "é uma correção óbvia" · "é só um
arquivo" · "o outro repositório está errado" (pode estar — relate).

### P2. Federada por contrato, nunca por atalho (INEGOCIÁVEL)

Esta aplicação é a **segunda aplicação candidata à federação** da plataforma `ghdaru`.
Pelo padrão **APH — Aplicação ↔ Harness** construímos para o **Nível 2 (Operador)** em
repositório, serviço e banco próprios, `mode: embedded`, do **lado aplicação** do Anexo B
— Federação (ADR 0003).

> Ao declarar conformidade, **diga de qual lado**: hospedeiro, aplicação, ou ambos — e
> declare a maturidade do que depende do outro lado. O lado da aplicação não tem
> verificação executável completa (o canal `postMessage` exige navegador); nossa
> declaração é autodeclaração, e isso se diz junto com ela.

**Alcance destas consequências.** Elas governam a **superfície APH** — o que atravessa o
envelope, nas duas direções: modelo → aplicação e aplicação ↔ hospedeiro. Elas **não**
governam a manipulação direta feita pelo titular do dado na própria interface, que não
atravessa fronteira nenhuma; essa manipulação responde ao item 8, que diz o que ela deve
em lugar da confirmação. Este alcance está no texto desde a versão 1.0.0 porque a irmã
precisou de emenda constitucional para acrescentá-lo depois — a omissão do alcance foi o
defeito, não uma afirmação errada.

Consequências que não se negociam:

1. **Não se inventa um segundo protocolo.** Tudo o que a inteligência artificial da
   fundação faz com um módulo interno — instantâneo de contexto (*snapshot*), catálogo de
   ações, ações governadas, traço — esta aplicação faz **pelo mesmo contrato**.
2. **Sem login próprio.** A identidade vem por introspecção (`POST /auth/introspect`) do
   token da fundação. O token **nunca é confiado**; é validado.
3. **Autorização fora do modelo de linguagem.** A decisão de acesso usa as capacidades
   (*capabilities*) devolvidas pela introspecção, jamais o texto que o modelo produziu.
4. **Verbo mutador nasce proposta.** Ação que altera estado nasce como `action_proposal`
   e atravessa a máquina de estados (proposta → confirmação → execução → traço). O
   executor recusa em falha fechada (*fail-closed*) qualquer atalho a essa máquina.
5. **A aplicação se declara por manifesto validável**, não editando o hospedeiro.
6. **Interface embarcada em iframe isolado** (*sandbox*), comunicação por `postMessage`
   com envelope tipado e `origin` **verificado dos dois lados**.
7. **Tela é dado, nunca instrução.** Conteúdo de usuário, anexo e resultado de ferramenta
   entram como camada **explicitamente demarcada como não-confiável**.
8. **Manipulação direta aplica na hora, e paga em traço e em reversibilidade.** O que o
   titular do dado faz na própria interface aplica **sem tela de confirmação se e somente
   se** o alvo é único e nomeado pelo próprio gesto, o valor está literalmente no controle
   tocado e o efeito é reversível na sessão. Fora disso, e sempre que a intenção for
   **inferida** (pelo sistema ou pelo modelo), vale o item 4. Em qualquer caminho o traço
   é obrigatório, a máquina de estados é uma só e do servidor, e o portão se resolve por
   política declarada por tipo de ação — nunca por origem alegada pelo cliente.

Referência normativa: `GHDaru/protocolos` (padrão APH: `padrao/padrao-aph.md`, Anexos A e
B) e o guia do desenvolvedor de aplicação federada em `GHDaru/ghdaru`
(`docs/integration/guia-desenvolvedor-app-federada.md`).

### P3. Domínio puro, efeitos na borda (DDD + Hexagonal)

Modelagem por Design Orientado a Domínio (DDD, do inglês *Domain-Driven Design*) sobre
arquitetura hexagonal: domínio e aplicação **puros** (sem entrada e saída, sem framework,
sem relógio); todo efeito entra por **porta** e é servido por **adaptador** na borda.

As regras da TOC são a razão de este princípio importar aqui: os critérios formais de
Efeito Indesejável (UDE, do inglês *Undesirable Effect*), a suficiência causal da Árvore
da Realidade Atual, as sete premissas da Nuvem de Conflito são **regra de domínio pura**
— testáveis sem rede, sem banco, sem modelo de linguagem. O isolamento entre contextos
delimitados é **executável** — `import-linter` como função de aptidão na integração
contínua —, não disciplina de revisor.

### P4. Desenvolvimento guiado por teste (TDD)

Ciclo vermelho → verde → refatorar. **Nenhuma linha de código de produção nasce sem um
teste que falhe antes dela.** Correção de defeito começa pelo teste que o reproduz.

Isto **estreita** o Princípio IV do Maestro ("teste primeiro"): aqui o teste não é apenas
anterior à conclusão, é anterior ao código. A linhagem TOC-Builder chegou à quarta geração
de protótipo **sem um teste sequer** — este princípio é o que impede a quinta.

### P5. Observabilidade de nascença

Telemetria não é fase posterior. Toda funcionalidade nasce com:

- **traço distribuído** (OpenTelemetry) atravessando fronteira de rede e porta — inclusive
  a fronteira APH, onde o traço é exigência do contrato de ações governadas;
- **log estruturado** correlacionado por identificador de requisição e de inquilino
  (*tenant*);
- **métrica** do que o negócio precisa saber (latência, erro, uso).

Funcionalidade sem traço **não está pronta** — a Definição de Pronto (DoD, do inglês
*Definition of Done*) a recusa.

### P6. Jornada viva com prova visual

Toda interface entrega **jornada documentada** no mesmo pull request: um documento por
jornada, capturas de tela **geradas do build real por script versionado** (nunca coladas
à mão) e avaliação heurística datada. Operacionalizado pela skill `living-journey`.

As capturas obedecem ao ADR 0006: **toda** captura usa a base sintética — uma captura com
dado real de pessoa reprova a jornada inteira, porque compromete a possibilidade de o
repositório ser aberto.

### P7. Segredo nunca no cliente (INEGOCIÁVEL)

Chave de provedor, credencial de banco, segredo de armazenamento e token de serviço vivem
**só no servidor**, por variável de ambiente. Nunca no código, nunca no repositório, nunca
no pacote entregue ao navegador.

A violação canônica está na própria linhagem deste produto:
`tocbuilderv3/services/geminiService.ts:16` inicializa o cliente do provedor de modelo
**no navegador** (`const ai = new GoogleGenAI({ apiKey: process.env.API_KEY });`). É
exatamente o defeito que este princípio proíbe, e o motivo de ele ser um princípio e não
uma nota de rodapé. A consequência arquitetural — assistência de inteligência artificial
**somente pela fundação**, via catálogo de ações governadas, sem SDK de provedor no
produto — está registrada no ADR 0007.

## Decisões estruturais vigentes

A constituição fixa o inegociável; a **escolha tecnológica** é decisão registrada,
revisável por novo ADR:

| Camada | Decisão | Registro |
|---|---|---|
| Interface | React + TypeScript (Vite) | ADR 0002 |
| Serviço | FastAPI (Python) | ADR 0002 |
| Banco | PostgreSQL gerenciado (Neon), projeto próprio | ADR 0002 |
| Armazenamento de objetos | Compatível com S3, atrás de porta | ADR 0002 |
| Telemetria | OpenTelemetry | ADR 0002 |
| Deploy | Vercel (interface) + Railway (serviço), eTLD+1 distinto do hospedeiro | ADR 0002 · ADR 0003 |
| Federação | APH Nível 2 (Operador), repositório próprio, `mode: embedded`, `app_id: toc`, lado aplicação do Anexo B | ADR 0003 |
| Base de dados de exemplo | Sintética desde o dia 1 | ADR 0006 |

Trocar qualquer linha desta tabela exige ADR novo que **suceda** o anterior — declarado
nos dois textos e verificado por `scripts/check-adrs-sucessao.sh` (regra R5).

## Idioma

A documentação **deste projeto** é escrita em **português**: constituição,
especificações, jornadas, ADRs e o registro do produto. A superfície instalável do
Maestro (agentes, skills, scripts do método, comandos, templates e
`docs/governance/principles.md`) permanece em **inglês**, como manda o ADR 0014 do método
— ela é lida por agentes em qualquer repositório.

Código, identificador e mensagem de commit seguem a linguagem ubíqua do domínio, que é
portuguesa (`projeto`, `nó`, `aresta causal`, `efeito indesejável`, `premissa`,
`injeção`, `restrição`, `obstáculo`, `objetivo intermediário`), com termos técnicos
consagrados em inglês quando traduzi-los criaria ambiguidade.

## Governança

Esta constituição prevalece neste repositório. Emendas incrementam a versão semântica
(MAIOR: remoção ou redefinição; MENOR: princípio novo ou ampliação; CORREÇÃO:
esclarecimento) e são registradas em ADR — que, por herança da regra R3 da irmã, declara
o campo **"Princípios tocados"**, com `nenhum` por extenso quando for o caso.

A verificação de conformidade é a mesma do método: `scripts/check-conformance.sh <NNN>`.
Perguntado "você está seguindo o método?", o agente **roda o script e lê o resultado** —
memória relata intenção, não fato.
