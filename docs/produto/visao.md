# O que é TOC Federada

> Siglas deste documento: **TOC** — Teoria das Restrições (*Theory of Constraints*);
> **ARA/CRT** — Árvore da Realidade Atual (*Current Reality Tree*); **UDE** — Efeito
> Indesejável (*Undesirable Effect*); **NC/EC** — Nuvem de Conflito (*Evaporating Cloud*);
> **ARF/FRT** — Árvore da Realidade Futura (*Future Reality Tree*); **APR/PRT** — Árvore de
> Pré-Requisitos (*Prerequisite Tree*); **AT/TT** — Árvore de Transição (*Transition Tree*);
> **S&T** — Árvore de Estratégia & Táticas; **OI** — Objetivo Intermediário; **APH** — o
> padrão Aplicação ↔ Harness; **ADR** — Registro de Decisão Arquitetural; **IA** —
> inteligência artificial; **SDK** — kit de desenvolvimento de software; **API** — interface
> de programação de aplicações; **DBR** — tambor-pulmão-corda (*Drum-Buffer-Rope*).

- **Status**: rascunho do ciclo 001 (aprovação: gate humano do ciclo)
- **Data**: 2026-09-03 · **Decisor**: Product Steward (ghdaru)
- **Origem**: leitura da linhagem TOC-Builder (quatro gerações + cinco repositórios
  natimortos, todos nesta sessão, somente leitura) e das skills de domínio
  `toc-evaporating-cloud` e `toc-prt`
- **Selo de confiança**: 🟢 CONFIRMADO com `arquivo:linha` · 🟡 PLANEJADO/INFERIDO ·
  🔴 LACUNA

Este documento é a **leitura da linhagem**, não o plano do produto: descreve o problema que
a aplicação existe para resolver, o que quatro gerações de protótipo entregaram e o que
nunca saiu delas, os defeitos medidos que viram requisito ou decisão, e as perguntas que só
o humano responde. O mapa de módulos está em [`modulos.md`](modulos.md); a ordem de
construção em [`rounds.md`](rounds.md) e [`../roadmap.md`](../roadmap.md). Os números
sobre o **domínio** — e não sobre a linhagem — saem da base sintética da Instituição
Horizonte, em [`dados/README.md`](dados/README.md), medida pelo script
[`dados/medir-base.py`](dados/medir-base.py) (ADR 0006).

## 1. O problema

Organizações não sofrem por falta de problemas conhecidos — sofrem por **analisá-los sem
método**. O dilema recorrente ("centralizar ou descentralizar", "qualidade ou prazo",
"contratar ou segurar custo") é discutido em reunião como queda de braço entre posições,
quando é, quase sempre, um **conflito entre duas necessidades legítimas do mesmo
objetivo** — e o que o sustenta são premissas que ninguém escreveu, logo ninguém pode
contestar. O mesmo vale para o problema crônico: cada área enxerga o seu sintoma, trata o
seu sintoma, e a causa raiz — que é uma, e liga todos os sintomas — segue intacta.

O resultado é conhecido: planos de ação que atacam efeitos, conflitos "resolvidos" por
cabo de guerra ou por chefia (alguém cede, a necessidade cedida volta a doer), e a mesma
pauta reaparecendo a cada trimestre com outro nome.

**TOC Federada** existe para que essa análise deixe de ser opinião e vire **artefato
lógico auditável**: o sintoma vira UDE validado por critérios formais, a discussão vira
árvore de causa e efeito, o dilema vira nuvem com premissas explícitas que se pode atacar
uma a uma, e a solução vira plano com obstáculos e objetivos intermediários sequenciados —
tudo multiusuário, dentro da plataforma onde o trabalho já acontece.

### 1.1 O que conta como resultado aceitável — e como isso se mede

O problema acima é fácil de descrever e difícil de medir, e é aí que quatro gerações
pararam: nenhuma delas definiu **o que é uma análise boa**. Esta define, e a definição é
executável antes de existir uma linha de produto. Uma análise TOC é aceitável quando as
quatro condições abaixo valem ao mesmo tempo — as quatro são verificadas hoje, por função
pura, sobre a base sintética da Instituição Horizonte e, a primeira delas, também sobre um
conjunto de controle que não escrevemos ([`dados/README.md`](dados/README.md)):

1. **Todo UDE passa nos critérios formais decidíveis** — frase completa, tempo presente,
   estado e não ação, sem culpar pessoa, sem solução disfarçada, uma entidade só, sem a
   causa embutida, factual. São oito checagens que traduzem sete das onze características
   que a linhagem deixou dentro de um prompt (`tocbuilderv3/constants.ts:122-133`).
2. **A árvore de causa e efeito não tem ciclo** — se A causa B e B causa A, não é
   diagnóstico, é opinião circular.
3. **Toda aresta da nuvem carrega a premissa escrita** — a nuvem sem premissas é um
   desenho bonito: o que se ataca é a premissa, não a posição.
4. **Cada efeito indesejável está ligado à árvore** — UDE órfão é queixa solta, não
   sintoma de nada.

E a régua tem números de partida, medidos e não declarados — **dois**, que não medem a
mesma coisa e por isso nunca aparecem juntos como se fossem um só (§6, D-12):

- **número autoral — 3 de 12.** Dos doze UDEs da base sintética da Instituição Horizonte,
  escritos como um facilitador humano os escreve, três passam nas oito checagens. Ele
  prova que as checagens **disparam**; não prova que estão certas, porque quem escreveu os
  enunciados escreveu as checagens.
- **número de controle — 8 de 9, com 1 falso negativo.** As mesmas oito checagens
  aplicadas a nove enunciados de UDE que a linhagem TOC-Builder escreveu quatro gerações
  antes delas, **rotulados pela própria linhagem** como bons ou ruins. Aí as checagens
  podem errar — e erram uma: aprovam um enunciado que a fonte rotula como ruim.

É o segundo que vira critério de aceite do módulo M2 na spec 005, em vez de "a validação
funciona bem": o caso que hoje falha (K-03) entra como teste que precisa passar. O
primeiro segue como conjunto de exercício, com o nome correto.

## 2. O que a Teoria das Restrições oferece — os processos de pensamento

A TOC parte de uma premissa dura: em qualquer sistema, **pouquíssimas coisas — geralmente
uma — limitam o desempenho do todo** (a restrição). Os **processos de pensamento** são o
conjunto de ferramentas lógicas que a TOC oferece para responder, com rigor de causa e
efeito, às três perguntas da mudança:

| Pergunta | Ferramenta | O que produz |
|---|---|---|
| **O que mudar?** | ARA/CRT | dos sintomas (UDEs) à causa raiz, por relações de suficiência |
| **O que mudar?** (o conflito) | NC/EC | o dilema em 5 entidades, as premissas que o sustentam, as injeções que o evaporam |
| **Para o que mudar?** | ARF/FRT | as injeções projetadas em efeitos futuros desejáveis (e ramos negativos a tratar) |
| **Como causar a mudança?** | APR/PRT | obstáculos à injeção → objetivos intermediários sequenciados |
| **Como causar a mudança?** (o passo a passo) | AT/TT | o plano de transição, passo a passo, com a lógica de cada passo |
| **Como sustentar?** | S&T | a estratégia decomposta em táticas numeradas (1, 1.1, 1.1.2), cada nó com suas premissas lógicas |

Costurando tudo, os **cinco passos de focalização**: identificar a restrição → explorá-la
→ subordinar o resto a ela → elevá-la → recomeçar (sem deixar a inércia virar a
restrição). É a jornada que dá ordem às ferramentas — e é exatamente o que **nenhuma
geração da linhagem tentou** (§6, D-09).

O encadeamento entre as ferramentas é o valor que nenhuma delas tem sozinha: o UDE da ARA
alimenta a NC; a injeção da NC semeia a ARF; a ARF revela os obstáculos que a APR
sequencia. A linhagem tratou cada ferramenta como um projeto isolado (§6, D-11); esta
aplicação nasce com o encadeamento como módulo (M4 em [`modulos.md`](modulos.md)).

## 3. A linhagem: quatro gerações e cinco natimortos

Esta aplicação não nasce do zero — nasce de **nove tentativas**. A contagem, executada
(regra R1):

```console
$ cd /home/user && ls -d TOC-Builder TOC-Builder-APP TOC-Builder-V2 tocbuilderv3
TOC-Builder
TOC-Builder-APP
TOC-Builder-V2
tocbuilderv3
$ for d in toc_backend toc_frontend tocbackend tocfrontend tocmaterials; do \
    echo "$d: $(ls $d | wc -l) arquivo(s) [$(ls -m $d)]"; done
toc_backend: 1 arquivo(s) [LICENSE]
toc_frontend: 1 arquivo(s) [LICENSE]
tocbackend: 0 arquivo(s) []
tocfrontend: 1 arquivo(s) [LICENSE]
tocmaterials: 0 arquivo(s) []
```

**Quatro gerações** de protótipo frontend (`TOC-Builder` → `TOC-Builder-APP` →
`TOC-Builder-V2` → `tocbuilderv3`) e **cinco repositórios natimortos** — dois vazios, três
contendo apenas um arquivo `LICENSE`. Os natimortos são a segunda lição antes mesmo da
primeira: **duas vezes** se tentou separar frontend e backend
(`toc_frontend`/`toc_backend`, `tocfrontend`/`tocbackend`) e nenhuma das quatro pontas
passou da licença. O backend da linhagem nunca existiu de nenhuma forma (§6, D-03).

### 3.1 O que cada geração entregou — e o que nunca saiu

**1ª geração — `TOC-Builder`** (15 arquivos na raiz). Entregou a ARA com canvas
interativo, painel de entidades e sugestões de IA, e — única vez na linhagem — a **S&T
ativa na navegação** (`TOC-Builder/components/Sidebar.tsx:44`, item sem `disabled` 🟢),
com editor de passos e premissas. Nunca saiu: NC, ARF, APR e AT, todas presentes na
navegação e todas desabilitadas (`TOC-Builder/components/Sidebar.tsx:45-48`,
`disabled: true` nas quatro 🟢).

**2ª geração — `TOC-Builder-APP`** (16 arquivos). Mesma navegação, mesmos quatro
desabilitados (`TOC-Builder-APP/components/Sidebar.tsx:44-48` 🟢); o serviço de API
simulada cresceu de 377 para 473 linhas (medição em §6, D-03). Uma geração inteira gasta
em refatoração interna, sem ferramenta nova chegando ao usuário.

**3ª geração — `TOC-Builder-V2`** (20 arquivos). Entregou a **NC completa** — geração
assistida a partir de narrativa, visão conflito+solução — e internacionalização
(`TOC-Builder-V2/i18n/`, `locales/` 🟢). E **regrediu**: a S&T, ativa nas duas primeiras
gerações, foi desligada (`TOC-Builder-V2/components/Sidebar.tsx:56`, `disabled: true` 🟢)
e nunca mais voltou. ARF, APR e AT continuaram desabilitadas
(`TOC-Builder-V2/components/Sidebar.tsx:53-55` 🟢).

**4ª geração — `tocbuilderv3`** (27 arquivos). A mais completa: documento de propósito
(`tocbuilderv3/APLICATION_PURPOSE.md` 🟢), validação formal de UDE com relatório
(`tocbuilderv3/APLICATION_PURPOSE.md:53-58`, `components/UdeValidationModal.tsx` 🟢),
documentação embutida (`components/DocsView.tsx` 🟢), tela de entrada e login simulado
(`components/LandingPage.tsx`, `LoginScreen.tsx`, `services/authService.ts:7-22` 🟢),
empacotamento Docker/nginx. A ambição está declarada no código: o tipo de navegação lista
**as seis ferramentas** mais administração e docs (`tocbuilderv3/types.ts:249-258` 🟢).
A realidade está quatro linhas abaixo na navegação: ARF, APR, AT e S&T desabilitadas
(`tocbuilderv3/components/Sidebar.tsx:55-58` 🟢). Em quatro gerações, **metade das
ferramentas dos processos de pensamento nunca chegou a um usuário**.

### 3.2 A leitura em uma frase

A linhagem provou o **valor** (a ARA e a NC funcionam e a assistência de inteligência
artificial neles é genuinamente útil — `tocbuilderv3/APLICATION_PURPOSE.md:29` descreve a
NC gerada de narrativa em linguagem natural 🟢) e provou o **teto**: protótipo frontend
sem backend, sem teste, sem identidade real e com a chave do provedor no navegador não
atravessa a linha de produto, não importa quantas vezes recomece. As nove tentativas são o
argumento empírico do método: o que faltou nunca foi ideia — foi fundação, portão e
sequência.

Uma ressalva atravessa o parágrafo inteiro e está declarada como lacuna 🔴 **L-01**: esse
"valor" é **julgado por quem construiu, nunca medido em uso**. Em quatro gerações não há
uma linha de instrumentação:

```console
$ grep -rniE "analytics|telemetr|mixpanel|amplitude|posthog|gtag|sentry|opentelemetry" \
    TOC-Builder TOC-Builder-APP TOC-Builder-V2 tocbuilderv3 --include="*.ts" \
    --include="*.tsx" --include="*.md" --include="*.json" --include="*.html" | wc -l
0
```

Zero ocorrências 🟢 — nenhuma sessão registrada, nenhuma análise concluída contada,
nenhum usuário fora dos autores. Tudo o que este documento afirma sobre utilidade é
inferência a partir de código, e a correção não é retórica: é o princípio P5
(observabilidade de nascença) valendo do ciclo 003 em diante.

## 4. Por que federada

**TOC Federada** é a **segunda aplicação candidata à federação** da plataforma
`GHDaru/ghdaru` — irmã da `gestaodeprioridades`, a primeira —, mirando o **Nível 2
(Operador)** do padrão APH, `mode: embedded`, em repositório, serviço e banco próprios,
embutida no aplicativo hospedeiro por iframe (ADR 0003, em
[`../adr/README.md`](../adr/README.md)).

O pretexto é honesto e declarado, como foi na irmã: a plataforma precisa de uma **segunda
junta real** para provar que a federação é padrão, e não acoplamento sob medida — duas
aplicações independentes fechando contra o mesmo contrato é o teste que uma sozinha não
faz. E a aplicação escolhida tem valor próprio suficiente para o teste não ser
demonstração: quatro gerações e cinco natimortos provam que a demanda existe e que o
caminho artesanal não a entrega.

A federação também resolve, por contrato, três defeitos crônicos da linhagem de uma vez:
a identidade vem de `POST /auth/introspect` (nunca mais login simulado — D-02), a IA vem
da fundação pelo catálogo de ações governadas (nunca mais SDK no cliente — D-01), e toda
mutação proposta por modelo nasce `action_proposal` com gate humano (o que a linhagem
fazia por convenção de tela, sem garantia nenhuma).

O que muda em relação à irmã: aqui a base é **sintética desde o dia 1** (ADR 0006) — a
linhagem não traz dado de pessoa que precise ser protegido, e nenhum entra. É o que
permite este repositório ser aberto sem a dívida de anonimização que a irmã carrega.

## 5. Linguagem ubíqua da TOC

Os termos do domínio, em português, como a constituição exige. "Onde aparece" cita a
linhagem quando o termo já existe nela (🟢) e o módulo de destino quando é novo (🟡 —
mapa em [`modulos.md`](modulos.md)).

| Termo | O que é | Onde aparece |
|---|---|---|
| **Restrição** | O fator que limita o sistema de atingir mais da sua meta; o ponto de alavanca de toda a análise | novo — registro da restrição no M6 🟡; zero ocorrências na linhagem (§6, D-09) |
| **Efeito Indesejável (UDE)** | Sintoma negativo da realidade atual, definido em relação ao objetivo do sistema; **estado**, não ação, não causa, não solução disfarçada | definição e critérios em `tocbuilderv3/constants.ts:120-137` 🟢; nó da ARA (M2) |
| **Árvore da Realidade Atual (ARA)** | Diagrama de causa e efeito que liga os UDEs à causa raiz por relações de suficiência ("se A, então B") | `tocbuilderv3/APLICATION_PURPOSE.md:20-25` 🟢; M2 |
| **Nuvem de Conflito (NC)** | O dilema em 5 entidades: objetivo comum (A), duas necessidades (B, C) e duas ações em conflito (D, D′) | `tocbuilderv3/types.ts:77-82` — campos `objective`, `wantD`, `wantDPrime` 🟢; M3 |
| **Premissa** | Suposição que sustenta uma aresta da nuvem (7 arestas, 7 conjuntos de premissas); é o que se ataca, não as posições | `tocbuilderv3/types.ts:72-74` (`assumption`) 🟢; M3 |
| **Injeção** | Condição nova que invalida uma premissa e evapora o conflito; semente da ARF | `tocbuilderv3/types.ts:107` (tipo de nó `'injection'`) 🟢; M3 → M4 |
| **Árvore da Realidade Futura (ARF)** | As injeções projetadas em efeitos futuros desejáveis, com ramos negativos identificados e tratados | apenas tipo e navegação desabilitada na linhagem (`tocbuilderv3/components/Sidebar.tsx:55`) 🟢; entregue no M4 🟡 |
| **Obstáculo** | O que impede uma injeção de acontecer; entrada da APR | novo — M4 🟡; conteúdo técnico na skill `toc-prt` |
| **Objetivo Intermediário (OI)** | Condição que, alcançada, supera um obstáculo; os OIs sequenciados são o esqueleto do plano | novo — M4 🟡; conteúdo técnico na skill `toc-prt` |
| **Árvore de Pré-Requisitos (APR)** | Obstáculos → OIs com ordem de dependência | navegação desabilitada na linhagem (`tocbuilderv3/components/Sidebar.tsx:56`) 🟢; entregue no M4 🟡 |
| **Árvore de Transição (AT)** | O passo a passo da implementação, cada passo com a sua lógica de suficiência | navegação desabilitada na linhagem (`tocbuilderv3/components/Sidebar.tsx:57`) 🟢; entregue no M4 🟡 |
| **Estratégia & Táticas (S&T)** | Decomposição hierárquica (1, 1.1, 1.1.2) da estratégia em táticas, cada nó com premissas de paralelismo, necessidade e suficiência | `tocbuilderv3/types.ts:286-295` (`stepNumber`, três campos de premissa) 🟢; M5 |
| **Os cinco passos de focalização** | identificar → explorar → subordinar → elevar → recomeçar; a jornada que costura as ferramentas | novo — M6 🟡; zero ocorrências na linhagem (§6, D-09) |

## 6. Defeitos e lições da linhagem — medidos

Cada item abaixo foi **executado, com a saída colada** (regra R1), e tem destino declarado
em [`rounds.md`](rounds.md): cada D-NN pertence a exatamente um round, ou à lista de
não-corrigidos com motivo.

**D-01 · A chave do provedor de IA vive no navegador — nas quatro gerações.**

```console
$ for d in TOC-Builder TOC-Builder-APP TOC-Builder-V2 tocbuilderv3; do \
    grep -n "new GoogleGenAI" $d/services/geminiService.ts; done
16:const ai = new GoogleGenAI({ apiKey: process.env.API_KEY });
16:const ai = new GoogleGenAI({ apiKey: process.env.API_KEY });
16:const ai = new GoogleGenAI({ apiKey: process.env.API_KEY });
16:const ai = new GoogleGenAI({ apiKey: process.env.API_KEY });
```

A mesma linha, no mesmo número de linha, quatro vezes 🟢. Num build Vite a variável é
embutida no bundle servido ao cliente. É a violação canônica do princípio P7 e o motivo
do ADR 0007 (IA somente pela fundação).

**D-02 · O login é simulado, com senhas em texto claro no código.**
`tocbuilderv3/services/authService.ts:7-13` define os usuários num array em memória e
`:16-22` as senhas em claro (`'user': 'user_password'`, …) 🟢; a "sessão" é o objeto do
usuário gravado em `localStorage` (`:31`). Quatro gerações de perfis
(USER/ADMINISTRATOR/SUPERUSER, `tocbuilderv3/types.ts:234` 🟢) sobre uma identidade que
não existe. A federação substitui isso por inteiro: identidade por `POST /auth/introspect`
(P2), nenhum login próprio.

**D-03 · O backend foi especificado quatro vezes e construído zero.**

```console
$ md5sum */api_specifications.md   # nas quatro gerações
ae5b3c3a6d153fb82fa9256e2b45e96a  TOC-Builder-APP/api_specifications.md
ae5b3c3a6d153fb82fa9256e2b45e96a  TOC-Builder-V2/api_specifications.md
ae5b3c3a6d153fb82fa9256e2b45e96a  TOC-Builder/api_specifications.md
ae5b3c3a6d153fb82fa9256e2b45e96a  tocbuilderv3/api_specifications.md
$ for d in TOC-Builder TOC-Builder-APP TOC-Builder-V2 tocbuilderv3; do \
    echo "$d: mockApiService.ts $(wc -l < $d/services/mockApiService.ts) linhas"; done
TOC-Builder: mockApiService.ts 377 linhas
TOC-Builder-APP: mockApiService.ts 473 linhas
TOC-Builder-V2: mockApiService.ts 565 linhas
tocbuilderv3: mockApiService.ts 594 linhas
```

A especificação da API (435 linhas) é **byte-idêntica nas quatro gerações** — nunca
avançou um caractere 🟢 —, enquanto o serviço **simulado** cresceu 377 → 594 linhas. O
investimento foi todo em fingir o backend, nunca em construí-lo. Somado aos cinco
natimortos (§3), é a lição mais cara da linhagem: **fundação primeiro** — e é por isso
que o ciclo 003 (esqueleto federado, banco próprio) vem antes de qualquer ferramenta.

**D-04 · ARF, APR e AT nunca saíram — em nenhuma geração.** 🔴 L-02

```console
$ for d in TOC-Builder TOC-Builder-APP TOC-Builder-V2 tocbuilderv3; do \
    echo "== $d"; grep -n "disabled: true" $d/components/Sidebar.tsx; done
== TOC-Builder
45:    { id: 'nc', label: 'Nuvem de Conflito (NC)', icon: <CloudIcon />, view: 'NC', disabled: true },
46:    { id: 'arf', label: 'Árvore Realidade Futura (ARF)', icon: <FutureTreeIcon />, view: 'ARF', disabled: true },
47:    { id: 'apr', label: 'Árvore de Pré-Requisitos (APR)', icon: <PrereqIcon />, view: 'APR', disabled: true },
48:    { id: 'at', label: 'Árvore de Transição (AT)', icon: <TransitionIcon />, view: 'AT', disabled: true },
== TOC-Builder-APP
45:    { id: 'nc', label: 'Nuvem de Conflito (NC)', icon: <CloudIcon />, view: 'NC', disabled: true },
46:    { id: 'arf', label: 'Árvore Realidade Futura (ARF)', icon: <FutureTreeIcon />, view: 'ARF', disabled: true },
47:    { id: 'apr', label: 'Árvore de Pré-Requisitos (APR)', icon: <PrereqIcon />, view: 'APR', disabled: true },
48:    { id: 'at', label: 'Árvore de Transição (AT)', icon: <TransitionIcon />, view: 'AT', disabled: true },
== TOC-Builder-V2
53:    { id: 'arf', label: t('sidebar.nav.arf'), icon: <FutureTreeIcon />, view: 'ARF', disabled: true },
54:    { id: 'apr', label: t('sidebar.nav.apr'), icon: <PrereqIcon />, view: 'APR', disabled: true },
55:    { id: 'at', label: t('sidebar.nav.at'), icon: <TransitionIcon />, view: 'AT', disabled: true },
56:    { id: 'snt', label: t('sidebar.nav.snt'), icon: <SnTIcon />, view: 'SNT_TREE', disabled: true },
== tocbuilderv3
55:    { id: 'arf', label: t('sidebar.nav.arf'), icon: <FutureTreeIcon />, view: 'ARF', disabled: true },
56:    { id: 'apr', label: t('sidebar.nav.apr'), icon: <PrereqIcon />, view: 'APR', disabled: true },
57:    { id: 'at', label: t('sidebar.nav.at'), icon: <TransitionIcon />, view: 'AT', disabled: true },
58:    { id: 'snt', label: t('sidebar.nav.snt'), icon: <SnTIcon />, view: 'SNT_TREE', disabled: true },
```

Saída literal, sem abreviação 🟢. As árvores de futuro e de implementação — a metade
"para o que mudar / como mudar" da TOC — ficaram quatro gerações como botão cinza. São o
módulo M4, com round próprio. **A lacuna L-02 é consequência disto**: para ARF, APR e AT
não existe nem tela anterior a herdar, nem modelo de dados, nem vocabulário de interface
— o M4 é o único módulo que nasce sem nenhuma linha de linhagem atrás dele, e o risco de
estimativa ali é alto (§8, L-02).

**D-05 · A S&T é a única ferramenta que regrediu.** Ativa na 1ª e na 2ª geração
(`TOC-Builder/components/Sidebar.tsx:44` e `TOC-Builder-APP/components/Sidebar.tsx:44`,
sem `disabled` 🟢), desabilitada da 3ª em diante (`TOC-Builder-V2/components/Sidebar.tsx:56`,
`tocbuilderv3/components/Sidebar.tsx:58` 🟢) — com o modelo de dados completo parado no
código (`tocbuilderv3/types.ts:286-295`: numeração hierárquica e as três premissas 🟢).
Funcionalidade que regride sem decisão registrada é exatamente o que um ADR existe para
impedir.

**D-06 · Zero testes em quatro gerações.**

```console
$ find TOC-Builder TOC-Builder-APP TOC-Builder-V2 tocbuilderv3 \
    -iname "*test*" -o -iname "*.spec.*" | wc -l
0
```

Nem do critério de validação de UDE, que é a regra de negócio central 🟢. Nenhum round
corrige isso isoladamente: o princípio P4 (teste antes do código) vale em **todos** os
ciclos de implementação — ver "não corrigidos" em [`rounds.md`](rounds.md).

**D-07 · O dado vive preso a um navegador.**

```console
$ grep -rn "localStorage" tocbuilderv3 --include="*.ts" --include="*.tsx" | wc -l
16
```

16 ocorrências em 5 arquivos (`App.tsx`, `authService.ts`, `I18nProvider.tsx`,
`NodeZoneView.tsx`, `NodeZoneVew.tsx`) 🟢 — sem sincronização, sem cópia de segurança,
sem multiusuário, sem inquilino. Análises TOC são colaborativas por natureza; presas a um
navegador, não são nem duráveis.

**D-08 · A regra de negócio central vive num prompt, não no domínio.** Os critérios
formais de validação de UDE — estado e não ação, efeito e não causa, presente, sem culpar
pessoas — existem apenas como texto de prompt
(`tocbuilderv3/constants.ts:109-137`, dentro de `VALIDATE_UDE_DETAILED_PROMPT_TEXT` 🟢).
A parte **decidível** desses critérios (frase completa, tempo presente, formato) depende
de chamada de rede a um modelo para ser avaliada — não é testável, não funciona sem
conexão, e muda quando o provedor muda. No M2 esses critérios viram **regra de domínio
pura** (E2.1), com o modelo reservado ao que é genuinamente julgamento.

**D-09 · Os cinco passos de focalização não existem na linhagem — nem a palavra.**

```console
$ grep -rniE "focaliza|five focusing|cinco passos" TOC-Builder TOC-Builder-APP \
    TOC-Builder-V2 tocbuilderv3 --include="*.ts" --include="*.tsx" --include="*.md" | wc -l
0
$ grep -rniE "drum|buffer.rope|tambor|pulm[aã]o|corda|throughput" TOC-Builder \
    TOC-Builder-APP TOC-Builder-V2 tocbuilderv3 --include="*.ts" --include="*.tsx" \
    --include="*.md" | wc -l
0
```

Zero ocorrências 🟢. A linhagem construiu ferramentas soltas sem a jornada que lhes dá
ordem — o M6 (Focalização) é a resposta. A segunda contagem (DBR e contabilidade de
ganho, também zero) fundamenta o corte de escopo do ADR 0005: o que nunca foi tentado em
nove repositórios não entra na v1 por inércia; entrada futura é decisão nova.

**D-10 · Recomeçar sem herdar custou cinco repositórios.** Os natimortos do §3 (saída
colada lá 🟢): duas tentativas de separar frontend/backend abandonadas na licença, um
repositório de materiais vazio. Cada geração recomeçou copiando o frontend anterior e
reescrevendo por cima — sem ADR, sem changelog, sem registro do que se aprendeu. Este
corpus — visão, módulos, rounds, ADRs com alternativas numeradas — é a correção: o
recomeço agora **herda por escrito**.

**D-11 · As ferramentas não se encadeiam.**

```console
$ grep -c "araProjectId\|sourceUdeId\|linkedProject\|crossTool" tocbuilderv3/types.ts
0
```

Nenhuma referência cruzada entre projetos de ferramentas diferentes no modelo de dados
🟢: `AraProject` e `ConflictCloudProject` são ilhas — um UDE da ARA não alimenta a NC, uma
injeção da NC não semeia nada. O encadeamento, que é o valor central dos processos de
pensamento (§2), é o épico E4.4 do M4.

**D-12 · Os critérios de UDE só existem como texto de prompt porque nunca foram medidos.
Medidos agora, em dois conjuntos: reprovam 9 dos 12 UDEs da base autoral (exercício) e,
contra nove enunciados rotulados pela própria linhagem (controle), acertam 5 dos 6 casos
com gabarito — o sexto é um falso negativo com causa nomeada.** 🟢

O D-08 diz *onde* a regra de negócio mora (num prompt). Faltava o número que transforma
isso em critério de aceite. A base sintética da Instituição Horizonte
([`dados/README.md`](dados/README.md), exigida pelo ADR 0006) foi construída para
responder — doze UDEs redigidos com as patologias típicas de oficina (ação em vez de
estado, causa embutida, solução disfarçada, juízo sobre pessoas) — e o script mede:

```console
$ python3 docs/produto/dados/medir-base.py | grep -E "^  (ARA:|Nuvem|características|NÚMERO AUTORAL|validação)"
  ARA: 16 nós (12 UDEs, 4 causas) · 16 arestas causais
  Nuvem de Conflito: 5 entidades · 7 arestas com premissa · 2 injeções
  validação estrutural: 0 falha(s)
  características do prompt: 11  ·  decidíveis por função pura: 8 checagens cobrindo 7  ·  dependentes de julgamento: 4
  NÚMERO AUTORAL — UDEs medidos: 12  ·  passam nos 8 critérios decidíveis: 3 (U-01, U-02, U-03)  ·  reprovam: 9
```

Três de doze 🟢 — e este é o **número autoral**, que prova menos do que parece. A base
foi escrita pelo mesmo autor das checagens e escrita *para* trazer as patologias que elas
procuram; a linha "divergências entre o esperado na base e o medido: 0" só diz que o
esperado e o medido coincidem, o que é tautologia. Uma base autoral **demonstra** as
checagens, não as **valida**: erro de checagem e erro de enunciado se cancelam sem deixar
rastro. O apontamento é da revisão independente do ciclo 001.

O que valida é um **conjunto de controle**: enunciados de UDE que existiam antes e fora
deste repositório, com rótulo escrito por outra pessoa. A linhagem TOC-Builder deixou
nove — oito dentro do próprio texto de prompt, repetidos nas quatro gerações, e um na tela
de boas-vindas —, e o prompt diz com todas as letras quais são "Bom UDE" e quais são
"Exemplo Ruim". Nenhum foi redigido, corrigido ou parafraseado aqui, e nenhum declara
resultado esperado:

```console
$ python3 docs/produto/dados/medir-base.py | grep -E "^  (NÚMERO DE CONTROLE|rotulados|FALSO|sem veredito)"
  NÚMERO DE CONTROLE — enunciados: 9  ·  passam (texto normalizado): 8  ·  passam (texto literal, como citado): 6
  rotulados pela fonte como bom/ruim: 6  ·  concordância: 5 (K-01, K-04, K-05, K-06, K-07)
  FALSO POSITIVO (a fonte diz bom, a checagem reprova): 0 (—)
  FALSO NEGATIVO (a fonte diz ruim, a checagem aprova): 1 (K-03)
  sem veredito possível (a fonte não rotula bom/ruim): 3 (K-02, K-08, K-09)
```

**Zero falso positivo e um falso negativo** 🟢, com causa raiz nomeada: a fonte rotula
"Falta de treinamento causa erros." (`tocbuilderv3/constants.ts:162`) como Exemplo Ruim
porque o enunciado traz a própria causa (característica 10), e a checagem CD-7 aprova
porque procura **conectivos** (`porque`, `devido a`, `já que`) e não procura o **verbo
causal** (`causa`, `leva a`, `resulta em`). A base autoral não continha um só enunciado
com verbo causal — quem a escreveu tinha na cabeça a mesma lista da CD-7. É exatamente o
tipo de buraco que só um gabarito alheio encontra. O detalhe das três divergências,
inclusive a dependência da CD-1 de pontuação, está em
[`dados/README.md`](dados/README.md).

As oito checagens traduzem **sete** das onze características de
`tocbuilderv3/constants.ts:122-133` (a característica 2 vira duas: frase completa e tempo
presente); as quatro restantes — 1 (queixa sobre problema contínuo), 4 (área de
responsabilidade), 5 (algo pode ser feito) e 7 (não é causa especulada) — dependem de
julgamento sobre o sistema analisado e **nenhuma função pura as decide** 🔴 L-03. O
controle confirma a fronteira em vez de a contradizer: os três enunciados sem veredito são
justamente os que a fonte separa por "lacuna × dificuldade", distinção que mora na
característica 1.

É essa divisão que o épico E2.1 (spec 005) implementa, e os dois números são o critério de
aceite, com papéis distintos: o domínio puro, sem rede e sem modelo, tem de devolver os
mesmos 9 reprovados da base autoral com o mesmo motivo por UDE **e** tem de fechar o falso
negativo K-03 — que hoje falha e é o caso de teste que nasce vermelho (P4). Destino
declarado em [`rounds.md`](rounds.md), round 005.

## 7. Perguntas ao Product Steward — mantidas, com resposta proposta

Perguntas que só o humano responde. Ficam **abertas até o gate do ciclo 001**; a resposta
proposta existe para a decisão ser sim/não/ajuste, não redação. Nenhuma foi resolvida em
silêncio.

1. **[DÚVIDA] Análises são colaborativas ou isoladas por usuário?** A irmã decidiu
   isolamento por usuário (ADR 0006 de lá), mas o domínio dela é lista pessoal de
   tarefas. Aqui o domínio é o oposto: uma NC entre duas áreas só faz sentido com
   Facilitadora e Participantes no mesmo projeto. **Proposta**: projeto compartilhável
   dentro do inquilino, com papéis (Facilitadora conduz, Participante contribui), e o
   isolamento continua valendo **entre** inquilinos. Impacta M1 (E1.1) e o modelo de
   permissões — por isso precisa de decisão antes da spec do M1 congelar.
2. **[DÚVIDA] O que fazemos com as quatro gerações depois do gate?** **Proposta**:
   arquivá-las como leitura (são a fonte 🟢 deste corpus), migrar **nada**
   automaticamente; quem tiver projeto relevante no v3 exporta o JSON e importa pelo
   E1.4, que valida em vez de aceitar às cegas. A linhagem não vira dependência.
3. **[DÚVIDA] Os perfis próprios da linhagem (USER/ADMINISTRATOR/SUPERUSER) têm algum
   sucessor?** **Proposta**: não. Papel e permissão derivam da identidade introspectada e
   das capabilities do embarque (P2); a Administradora do tenant governa acesso na
   fundação, não numa tela nossa de administração de usuários. As telas `USER_ADMIN` e
   `PROMPT_ADMIN` do v3 (`tocbuilderv3/types.ts:256-257` 🟢) morrem sem sucessora — a
   primeira substituída pela fundação, a segunda pelo ADR 0007 (prompts versionados no
   servidor).
4. **[DÚVIDA] Existe uso fora do iframe?** A linhagem era standalone; a aplicação mira
   `mode: embedded`. **Proposta**: o site próprio (eTLD+1 distinto — o "site" no sentido
   do navegador) serve página de produto e uma demonstração com base sintética, **sem
   identidade e sem persistência de escrita**; uso real, somente embarcado. Evita
   reconstruir login (D-02) pela porta dos fundos.
5. **[DÚVIDA] Português primeiro, com inglês desde o início — confirma?** A linhagem
   entregou i18n pt/en na 3ª geração (`TOC-Builder-V2/i18n/` 🟢). **Proposta**: manter
   pt/en desde o início (E8.3), com o português como língua-fonte da linguagem ubíqua e
   dos exemplos sintéticos, e o inglês como tradução de interface — nunca de conceito de
   domínio.

## 8. Lacunas declaradas

O selo 🔴 deste documento não é decorativo: as três lacunas abaixo são o que **não se sabe**
depois de ler nove repositórios e construir uma base sintética. Cada uma traz a assunção
que vale enquanto ela durar, o risco e o ciclo onde ela fecha ou deixa de importar. Nenhuma
delas foi resolvida em silêncio, e nenhuma vira requisito por decreto: viram entrada da
spec do ciclo que as fecha.

| # | Lacuna | Assunção enquanto durar | Risco | Onde fecha |
|---|---|---|---|---|
| 🔴 **L-01** | **Nenhum usuário real foi medido em quatro gerações.** Zero instrumentação (§3.2, saída colada) — nenhuma sessão, nenhuma análise concluída, nenhum abandono contado. Tudo o que se afirma sobre utilidade é inferência a partir de código. | O valor da ARA e da NC observado no código e no `tocbuilderv3/APLICATION_PURPOSE.md` se sustenta em uso real. | médio | ciclo 003 (observabilidade de nascença, P5) mede a primeira sessão; ciclo 012 fecha com jornada avaliada. |
| 🔴 **L-02** | **ARF, APR e AT nunca tiveram nem tela para herdar.** Quatro gerações de botão cinza (§6, D-04): não há componente anterior, modelo de dados, vocabulário de interface nem exemplo de uso — só a navegação desabilitada. | O conteúdo técnico das skills de domínio (`toc-prt` para a APR) e a literatura da TOC bastam para especificar o M4 sem protótipo prévio. | **alto** — é o único módulo sem nenhuma linha de linhagem atrás dele | ciclo 002 (protótipo de interfaces) tira a primeira tela do papel; round 008 entrega o módulo. |
| 🔴 **L-03** | **Uma base autoral demonstra as checagens; não as valida.** A base da Instituição Horizonte ([`dados/README.md`](dados/README.md)) foi escrita pelo mesmo autor das oito checagens e escrita *para* trazer as patologias que elas procuram — o 3 de 12 mede o acordo do autor consigo mesmo, e "divergências: 0" é tautologia. O conjunto de controle da linhagem tira a circularidade da conta e já pegou um falso negativo (K-03, §6 D-12), mas **são nove enunciados, seis com rótulo**: amostra pequena demais para estimar taxa de erro, e didática, não colhida de oficina. Sobre qualquer um dos dois conjuntos, 4 das 11 características seguem indecidíveis por função pura. | O controle de nove enunciados basta para **encontrar** defeito nas checagens (encontrou um), e não se assume que baste para **descartar** a existência de outros: um único caso a mais move a taxa em mais de dez pontos. | médio | **Não fecha neste projeto, e a visão declara isso em vez de datar um fechamento falso.** O que fecharia de verdade é um corpus de efeitos indesejáveis colhidos de oficina real, escritos por facilitador humano e rotulados por outro facilitador — que **não existe e não pode existir aqui**: enunciado de trabalho de pessoa real é dado de pessoa real, e o ADR 0006 o proíbe em fixture, spec e exemplo sem consentimento, que este repositório aberto não tem como obter. O ciclo 005 avança o que é possível — amplia o controle se a linhagem ou a literatura pública derem mais enunciados rotulados por terceiros, e transforma cada divergência em teste. |

Três lacunas, três destinos. O que **não** é lacuna, e por isso não aparece aqui: tudo que
o §6 mede com saída colada (é fato, não incerteza) e tudo que o §7 pergunta ao Product
Steward (é decisão pendente, não desconhecimento).

Legenda que declara nível e nunca o usa é legenda mentindo. A contagem dos três selos
neste documento, medida e não declarada (o comando não escreve os selos, por isso contá-lo
não muda a conta):

```console
$ python3 -c "t=open('docs/produto/visao.md',encoding='utf-8').read(); \
print(' · '.join(f'{n}: {t.count(chr(c))}' for n,c in \
(('CONFIRMADO',0x1F7E2),('PLANEJADO',0x1F7E1),('LACUNA',0x1F534))))"
CONFIRMADO: 45 · PLANEJADO: 9 · LACUNA: 8
```

Os três níveis da legenda aparecem no corpo. As três lacunas estão marcadas onde nascem —
L-01 no §3.2, L-02 no §6 (D-04), L-03 no §6 (D-12) — e reunidas na tabela acima, cada uma
com assunção, risco e ciclo de fechamento.

