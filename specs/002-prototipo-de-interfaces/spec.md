# Spec 002 — Protótipo de interfaces (ciclo planejado)

> Siglas: TOC — Teoria das Restrições · APH — Aplicação ↔ Harness · ADR — Architecture
> Decision Record (Registro de Decisão Arquitetural) · RF/RI/RNF/RN/INT — requisito
> funcional / de interface / não funcional / regra de negócio / integração · UDE —
> Undesirable Effect (Efeito Indesejável) · ARA — Árvore da Realidade Atual · NC — Nuvem
> de Conflito · US — User Story · DoD — Definition of Done (Definição de Pronto) · IA —
> inteligência artificial · CSS — Cascading Style Sheets · JSON — JavaScript Object
> Notation · ARF — Árvore da Realidade Futura · APR — Árvore de Pré-Requisitos · AT —
> Árvore de Transição · S&T — Árvore de Estratégia & Táticas · P1/P6/P7 — princípios da
> constituição do projeto

- **Status**: Rascunho — ciclo **planejado, não executado** (abre após o gate humano do
  ciclo 001)
- **Raia**: plena
- **Data**: 2026-09-03
- **Origem**: [`../../docs/roadmap.md`](../../docs/roadmap.md) ciclo 002 ·
  [`../../docs/produto/rounds.md`](../../docs/produto/rounds.md) round 002 ·
  [`../../docs/produto/modulos.md`](../../docs/produto/modulos.md) (M1–M3)

## O quê e por quê

O ciclo 001 escreveu **o que o produto é**. Nenhuma linha diz ainda **como ele se parece**
— e a linhagem TOC-Builder prova que essa pergunta não se responde no papel: quatro
gerações redesenharam canvas, painéis e temas sem nunca registrar o que foi visto e
decidido. Este ciclo produz um **protótipo descartável** das telas de M1–M3 (canvas,
vista tabular, ARA, NC) para que os requisitos de interface das specs de módulo saiam
validados por olho humano antes de qualquer código de produção — que só nasce no
ciclo 004.

"Descartável" aqui não é adjetivo, é contrato: o protótipo satisfaz as **quatro condições
cumulativas** que a irmã `gestaodeprioridades` fixou no ADR 0005 dela [F-01] — vive fora
do diretório da aplicação, não implementa regra de domínio, não persiste dado real nem
fala com a fundação, e é apagado ou reescrito quando o round correspondente for
implementado. A definição é herdada; se contestada, vira ADR próprio
([`../../docs/produto/rounds.md`](../../docs/produto/rounds.md), round 002).

Esta spec cobre os **requisitos de interface transversais** das ferramentas M1–M3 em
nível de protótipo: o canvas, a vista tabular equivalente, o tema claro/escuro herdado do
hospedeiro com *fallback*, e o modo embarcado só-conteúdo. Os requisitos definitivos de
cada ferramenta vivem nas specs dos módulos (`specs/004-nucleo-de-diagramas/`,
`specs/005-arvore-da-realidade-atual/`, `specs/007-nuvem-de-conflito/`); o que sai daqui
é a **forma validada** que essas specs consomem.

## O que entra como dado

- As quatro condições do protótipo descartável, herdadas da decisão análoga da irmã
  [F-01] — não se rediscute aqui o que é código de produção.
- **Base sintética desde o dia 1** (ADR 0006): toda fixture, captura e exemplo usa
  personas fictícias ("Instituição Horizonte", "Facilitadora TOC") — nenhum dado real de
  pessoa, nunca.
- **IA somente pela fundação** (ADR 0007): o protótipo não tem painel de conversa próprio
  nem chamada a provedor de modelo — a violação canônica que isso proíbe está medida em
  [F-08].
- O escopo v1 (ADR 0005 deste projeto): prototipa-se só o que os rounds 004–007
  implementam; ARF, APR, AT, S&T e focalização ficam fora (rounds 008–010 — prototipá-los
  agora seria estoque).
- A resposta do Product Steward à pergunta 1 da
  [`../../docs/produto/visao.md`](../../docs/produto/visao.md) §7 (colaboração por
  projeto ou isolamento por usuário) — **precondição declarada no roadmap**: ela muda as
  telas de projeto do E1.1.

## Épicos, features e user stories

Este ciclo **não cria features próprias**: ele prototipa fatias dos épicos E1.2 (canvas),
E1.3 (vista tabular), E2.1–E2.2 (ARA), E3.1–E3.2 e E3.4 (NC) e a face visual do E7.2
(tema e modo embarcado). As features definitivas, com seus números F<m>.<n>.<k>, vivem
nas specs dos módulos. O trabalho organiza-se em quatro frentes, cada uma com ao menos
uma US.

### Frente 1 — Semântica antes de pixel

**`ux-design.md` primeiro** — papel semântico e `ai_visible` de cada objeto de tela,
declarados **antes** de qualquer componente existir.

- US-01 — Como **Agente de IA da fundação** (persona de contrato), quero que cada objeto
  de tela declare se sou autorizado a vê-lo, para que o snapshot futuro nasça por lista
  de permissão e não por esquecimento.
  - Dado o `ux-design.md` entregue, Quando um objeto de tela não declara `ai_visible`,
    Então o padrão é **não visível** — e cada `sim` carrega justificativa escrita.

### Frente 2 — Canvas e vista tabular (M1)

**A dupla que a linhagem acertou** [F-02]: diagrama manipulável e a mesma informação como
tabela de edição rápida.

- US-02 — Como **Facilitadora TOC**, quero montar nós e arestas causais no canvas, para a
  lógica da análise tomar forma diante do grupo.
  - Dado um projeto sintético aberto, Quando crio dois nós e os ligo por uma aresta
    causal, Então a aresta aparece direcionada (causa → efeito) e os três objetos são
    editáveis por manipulação direta.
- US-03 — Como **Participante**, quero contribuir UDEs numa vista tabular, para inserir
  muitos itens sem manipular o diagrama.
  - Dado o mesmo projeto, Quando alterno do canvas para a vista tabular, Então vejo os
    mesmos nós e arestas como linhas editáveis — e a alternância não perde a edição em
    curso.

### Frente 3 — ARA e NC com forma canônica (M2, M3)

As duas ferramentas mais maduras da linhagem, prototipadas com os estados que as specs de
módulo vão exigir — os **resultados** de validação vêm de fixture, nunca de cálculo
próprio (condição 2 do descartável).

- US-04 — Como **Facilitadora TOC**, quero ver a NC com as cinco entidades e as sete
  premissas no lugar canônico [F-03], para conduzir a leitura do conflito sem explicar o
  diagrama antes do dilema.
  - Dado o dilema sintético da "Instituição Horizonte" carregado da fixture, Quando abro
    a tela da NC, Então vejo A, B, C, D e D′ posicionadas e cada uma das sete arestas dá
    acesso às suas premissas.

### Frente 4 — Tema, embarque e prova (E7.2 + P6)

O protótipo é visto **como será usado**: embarcado, com o tema de quem hospeda, provado
por captura gerada de build.

- US-05 — Como **Gestora**, quero a aplicação com a cara da plataforma onde está
  embarcada, para ela não parecer um sistema de terceiro colado por iframe.
  - Dado o adaptador falso entregando `theme.tokens` do inquilino, Quando a mesma tela é
    renderizada em modo autônomo e em modo embarcado, Então a embarcada veste os tokens
    recebidos e todo token ausente cai no *fallback* próprio — sem buraco sem cor.

## Entidades e modelo de domínio

**Não há agregados neste ciclo** — condição 2 do protótipo descartável [F-01]. O que se
modela são **objetos semânticos de tela**, cuja declaração campo a campo (papel,
`ai_visible`, estados obrigatórios) é a entrega do `ux-design.md` previsto. A lista
mínima que o protótipo materializa:

| Objeto semântico | Papel | Origem |
|---|---|---|
| `projeto-resumo` | identificar a análise aberta (nome, ferramenta, atualização) | E1.1 🟡 |
| `no-diagrama` | um nó lógico no canvas (UDE, causa, entidade da nuvem) | [F-02] 🟢 na forma, 🟡 no protótipo |
| `aresta-causal` | relação causa → efeito direcionada | [F-02] 🟢/🟡 |
| `vista-tabular` | projeção dos mesmos nós/arestas como linhas editáveis | [F-02] 🟢/🟡 |
| `ude-com-validacao` | UDE com estado formal (válida / pendente / recusada) vindo da fixture | modulos.md M2 🟡 |
| `nuvem-entidades` | A, B, C, D, D′ em posição canônica | [F-03] 🟢/🟡 |
| `premissa-de-aresta` | premissa acessível por aresta da nuvem (7 arestas) | [F-03] 🟢/🟡 |
| `tokens-de-tema` | conjunto claro/escuro próprio + camada do inquilino | [F-04] 🟢/🟡 |

## Requisitos funcionais

### Semântica e prova

RF-01: O SISTEMA DEVE entregar `ux-design.md` declarando, para **cada** objeto de tela, o
papel semântico, os estados obrigatórios e o `ai_visible` — com padrão **não visível** e
justificativa escrita em cada `sim` — antes de qualquer componente existir. 🟡

RF-02: O SISTEMA DEVE entregar um protótipo navegável que satisfaça as **quatro condições
cumulativas** do protótipo descartável [F-01]: fora do diretório da aplicação (em
`prototipo/`), sem regra de domínio, sem persistência de dado real nem fala com a
fundação, apagado ou reescrito no round implementado. 🟡

RF-03: QUANDO o protótipo estiver construído, O SISTEMA DEVE gerar as capturas a partir
do **build real do protótipo**, por script versionado — nunca coladas à mão (P6); rodar o
script de novo sobre o mesmo build DEVE regenerar as imagens byte-idênticas. 🟡

RF-04: O SISTEMA DEVE entregar um documento por jornada prototipada, com avaliação
heurística **datada**, e nenhuma captura órfã — toda imagem citada por exatamente uma
jornada (aptidão do round 002). 🟡

RF-05: O SISTEMA DEVE atualizar `docs/jornadas/README.md` marcando quais jornadas
planejadas (J-01..J-06) ganharam versão de protótipo — sem promovê-las a jornada viva,
que exige build de produção. 🟡

### Conteúdo prototipado

RF-06: O SISTEMA DEVE carregar o protótipo exclusivamente de fixture sintética versionada
(personas fictícias, "Instituição Horizonte") — nenhum dado real de pessoa (ADR 0006). 🟡

RF-07: O SISTEMA DEVE prototipar as telas de M1–M3: lista de projetos, canvas com vista
tabular, ARA com UDEs e estado de validação, NC com cinco entidades, sete premissas e uma
injeção — e nada dos módulos M4–M6 (rounds 008–010). 🟡

RF-08: QUANDO a mesma tela existir em modo autônomo e em modo embarcado, O SISTEMA DEVE
demonstrá-la **nas duas larguras** — mesa e iframe estreito — com os mesmos dados. 🟡

RF-09: O SISTEMA DEVE consumir identidade de exibição e tema por **adaptador falso** que
devolva o envelope do handshake conforme o guia da fundação [F-05], para que a troca pelo
ambiente real no ciclo 003 seja configuração, não reescrita. 🟡

## Requisitos de interface

### Canvas (E1.2)

RI-01: O canvas DEVE permitir criar, mover, editar e excluir nós por manipulação direta,
e desenhar arestas causais entre eles — a forma que a linhagem provou [F-02]. 🟡

RI-02: Toda aresta causal DEVE ser lida como "se causa, então efeito": direcionada, com a
seleção revelando origem e destino. 🟡

RI-03: O canvas DEVE degradar com dignidade em iframe estreito — largura de referência
**420px**, herdada da prova da irmã [F-06] até medição própria no ciclo 003 (L-01):
navegação por pan/zoom no lugar de barra de rolagem dupla, ações primárias alcançáveis. 🟡

### Vista tabular equivalente (E1.3)

RI-04: A vista tabular DEVE projetar **os mesmos** nós e arestas do canvas como linhas de
edição rápida — o "Painel de Entidades" que a linhagem acertou [F-02] — sem ser uma
segunda fonte de verdade. 🟡

RI-05: A alternância canvas ⇄ vista tabular DEVE preservar seleção e edição em curso da
sessão; no iframe estreito, a vista tabular é a projeção primária. 🟡

### Tema claro/escuro herdado do hospedeiro, com fallback

RI-06: A aplicação DEVE ter tema próprio claro **e** escuro como conjuntos de variáveis
CSS (*tokens*) — o padrão e a identidade em modo autônomo. A linhagem não tem tema algum
para herdar: a medição deu **zero** ocorrências [F-07], então este requisito nasce sem
referência, por decisão. 🟡

RI-07: QUANDO embarcada, a aplicação DEVE aplicar os `theme.tokens` recebidos do
hospedeiro **por cima** do tema próprio; o conjunto é **parcial por design** e o
*fallback* próprio cobre obrigatoriamente todo token ausente [F-04]. 🟢 na norma, 🟡 no
protótipo.

RI-08: A escolha claro/escuro DEVE seguir o hospedeiro quando embarcada e a preferência
do sistema quando autônoma — nunca um seletor próprio que brigue com o de quem hospeda. 🟡

### Modo embarcado só-conteúdo

RI-09: Embarcada, a aplicação DEVE renderizar **apenas o conteúdo**: sem cabeçalho de
navegação próprio, menu global, rodapé ou seletor de inquilino — quem navega é o
hospedeiro [F-05][F-09]. 🟢 na norma, 🟡 no protótipo.

RI-10: O protótipo DEVE demonstrar o modo só-conteúdo dentro de um iframe real (casca de
hospedeiro simulada localmente), não apenas como página estreita. 🟡

### ARA e NC (M2, M3)

RI-11: A tela da ARA DEVE mostrar cada UDE com seu estado de validação formal — válida,
pendente ou recusada — com os estados vindos da fixture, nunca de cálculo do protótipo
(condição 2 de [F-01]). 🟡

RI-12: A tela da NC DEVE posicionar as cinco entidades (A, B, C, D, D′) na forma canônica
e dar acesso às premissas por cada uma das sete arestas [F-03]; uma injeção DEVE aparecer
ligada à premissa que invalida. 🟡

RI-13: A visão conflito+solução (E3.4, os dois diagramas lado a lado) é prototipada **se
o apetite couber** — é o "sai primeiro" declarado do round 002; cortá-la não reprova o
ciclo, escondê-la sim. 🟡

### Acessibilidade mínima do protótipo

RI-14: As ações primárias DEVEM ser alcançáveis por teclado com foco visível, e o
contraste dos dois temas DEVE passar o mínimo do checklist de interface — protótipo
inacessível valida a forma errada. 🟡

## Requisitos não funcionais

RNF-01: Nenhum dado real de pessoa em fixture, captura, jornada ou exemplo — base
sintética integral (ADR 0006), verificável por inspeção da fixture e grep de nomes. 🟡

RNF-02: Nenhum segredo no cliente e nenhuma chamada a provedor de modelo a partir do
navegador (P7; ADR 0007) — a violação canônica que isto proíbe está em [F-08]. 🟡

RNF-03: As capturas DEVEM ser determinísticas: dados fixos, relógio congelado no build de
captura, mesma viewport — é o que torna "regenera byte-idêntica" possível. 🟡

RNF-04: O protótipo DEVE ser leve o bastante para buildar e capturar em máquina local sem
serviço externo — sem banco, sem rede, sem fila. 🟡

RNF-05: Interface do protótipo em português (língua-fonte da linguagem ubíqua); a
internacionalização real é E8.3, ciclo 011. 🟡

## Regras de negócio

**Nenhuma — por decisão, não por esquecimento.** A condição 2 do protótipo descartável
[F-01] proíbe regra de domínio aqui: critérios de validação de UDE, suficiência causal e
qualquer cálculo vêm **prontos da fixture**. As regras de negócio da TOC nascem como
regra de domínio pura nas specs dos módulos (RN-NN de
`specs/005-arvore-da-realidade-atual/` em diante), sob TDD (Test-Driven Development), no
ciclo de implementação de cada uma.

## Integrações

INT-01: **Nenhuma integração real neste ciclo.** Identidade de exibição, tema e handshake
vêm de adaptador falso que devolve o envelope `ghd.handshake` no formato do guia da
fundação [F-05] — mesmo corpo, origem local. A troca pelo hospedeiro real é o ciclo 003. 🟡

INT-02: Nada de introspecção, manifesto, catálogo `toc.*` ou `action_proposal` — ciclos
003 e 006. O protótipo não mostra o ciclo propor → confirmar → executar porque o catálogo
que o governa ainda não tem spec executada (L-03); a irmã prototipou o dela no ciclo
equivalente porque o catálogo dela nascia no mesmo ciclo — o nosso nasce no 006. 🟡

## Telas e fluxos

### 6.1 Lista de projetos — Job: escolher a análise · Campos: nome, ferramenta, última atualização · Ações: abrir, criar (protótipo: sem excluir — soft delete é regra do E1.1)

### 6.2 Canvas + vista tabular — Job: construir o diagrama · Campos: nós (título, descrição), arestas (origem, destino) · Ações: criar/mover/editar nó, ligar aresta, alternar para tabela

### 6.3 ARA — Job: dos sintomas à causa · Campos: UDEs com estado de validação (da fixture) · Ações: navegar a árvore, abrir detalhe de UDE

### 6.4 NC — Job: ler o conflito · Campos: A, B, C, D, D′, premissas por aresta, injeção · Ações: abrir premissas de uma aresta, ver a injeção ligada à premissa

### 6.5 Embarque simulado — Job: ver a aplicação como será usada · Campos: casca de hospedeiro local com iframe, tokens do inquilino falso · Ações: alternar autônomo/embarcado, claro/escuro, mesa/estreito

## Fora de escopo

- Qualquer código de produção: domínio, casos de uso, portas, adaptadores reais, rotas,
  persistência, banco (ciclos 003+; a definição da fronteira é [F-01]).
- ARF, APR, AT, S&T e focalização — prototipar o que só entra nos rounds 008–010 seria
  estoque ([`../../docs/produto/rounds.md`](../../docs/produto/rounds.md), round 002).
- O ciclo propor → confirmar → executar em tela e qualquer assistência de IA — dependem
  do catálogo `toc.*` (ciclo 006; INT-02, L-03).
- Integração real com a fundação: handshake, introspecção, manifesto (ciclo 003).
- Exportação/importação JSON (E1.4) — regra de aceitação/recusa é domínio, ciclo 004.
- Escrever em `maestro`, `protocolos`, `ghdaru`, `gestaodeprioridades` ou na linhagem
  (P1).

## Entregáveis

- `specs/002-prototipo-de-interfaces/ux-design.md` — papel semântico e `ai_visible` de
  cada objeto de tela (previsto; nasce na execução do ciclo, não neste planejamento).
- `prototipo/` — o protótipo descartável, com fixture sintética em `prototipo/dados/` e
  os tokens dos dois temas.
- Script versionado de captura (em `prototipo/scripts/`) e as capturas em
  `docs/jornadas/capturas/`.
- Documentos de jornada em versão de protótipo em `docs/jornadas/`, cada um com avaliação
  heurística datada; `docs/jornadas/README.md` atualizado.
- Entrada no `CHANGELOG.md` citando o ciclo 002.

## Critérios de aceite (DoD)

Planejados — executam no fechamento do ciclo 002, com saída colada no `qa-report.md`
(regras R1/R2).

| # | Critério | Verificação executável |
|---|---|---|
| 1 | `ux-design.md` existe e todo objeto declara `ai_visible` | `test -f specs/002-prototipo-de-interfaces/ux-design.md && grep -c 'ai_visible' specs/002-prototipo-de-interfaces/ux-design.md` ≥ nº de objetos declarados |
| 2 | Protótipo fora da aplicação (condição 1) | `test -d prototipo && grep -rn "prototipo/" apps/ 2>/dev/null \| wc -l` → `0` (enquanto `apps/` não existir, dizer que o zero é vácuo — R2) |
| 3 | Estados de validação vêm de fixture (condição 2) | `grep -rn "estado" prototipo/dados/*.json \| wc -l` ≥ 1 **e** revisão independente confirma ausência de cálculo (TAIL:review) |
| 4 | Base 100% sintética | fixture inspecionada + `grep -rn "gestaodeprioridades/protot[i]po" --include='*.md' . \| wc -l` → `0` |
| 5 | Capturas regeneram byte-idênticas | rodar o script de captura duas vezes sobre o mesmo build e comparar (`diff -r` limpo entre as duas saídas) |
| 6 | Nenhuma captura órfã | toda imagem de `docs/jornadas/capturas/` citada por exatamente uma jornada (script de conferência com contagem na saída) |
| 7 | Dois temas × duas larguras | capturas presentes para claro/escuro × mesa/estreito da mesma tela com os mesmos dados |
| 8 | Modo só-conteúdo demonstrado | captura do embarque simulado sem cabeçalho/menu/rodapé próprios |
| 9 | Nenhum provedor de modelo no cliente | `grep -rniE "GoogleGenAI\|api_key\|apiKey" prototipo/ \| wc -l` → `0` |
| 10 | Caminhos das jornadas resolvem | `scripts/check-caminhos.sh` → código 0, dizendo quantos conferiu (R2) |
| 11 | Conformidade do ciclo | `scripts/check-conformance.sh 002` → código 0 |

## Fontes

F-01: `/home/user/gestaodeprioridades/docs/adr/0005-codigo-de-producao-versus-prototipo.md:29-34`
— as quatro condições cumulativas do protótipo descartável ("vive em `prototipo/` … não
implementa regra de domínio … não persiste dado real … é apagado ou reescrito") — a
fronteira herdada que o RF-02 executa. 🟢

F-02: `/home/user/tocbuilderv3/APLICATION_PURPOSE.md:22-25` — "Canvas Visual Interativo …
Painel de Entidades: uma visão alternativa em formato de 'datatable'" — a dupla
canvas+tabela que funciona na linhagem; fundamenta RI-01, RI-04. 🟢

F-03: `/home/user/tocbuilderv3/types.ts:69` (`id: 'A' | 'B' | 'C' | 'D' | 'D_PRIME'`) e
`:73` (`id: 'A_B' | 'A_C' | 'B_D' | 'C_D_PRIME' | 'D_C' | 'D_PRIME_B' | 'D_D_PRIME'`) —
as cinco entidades e as sete arestas com premissa da NC; fundamenta RI-12. 🟢

F-04: `/home/user/ghdaru/docs/integration/guia-desenvolvedor-app-federada.md:200-202` —
"`theme.tokens` traz `nome → cor` … é **parcial por design**, seu `fallback` obrigatório
cobre o resto" — fundamenta RI-07. 🟢

F-05: `/home/user/ghdaru/docs/integration/guia-desenvolvedor-app-federada.md:187-204` — o
handshake `ghd.ready`/`ghd.handshake` com `targetOrigin` dirigido e tema no payload — o
envelope que o adaptador falso do RF-09 reproduz. 🟢

F-06: `/home/user/gestaodeprioridades/specs/002-prototipo-de-interfaces/tasks.md:29-30` —
"a tabela … Provada em 420px" — a largura de iframe estreito que a irmã provou; herdada
como referência do RI-03 até medição própria (L-01). 🟢

F-07: medição executada em 2026-09-03 na linhagem:
`cd /home/user/tocbuilderv3 && grep -rn -i -E "theme|darkMode|dark-mode" --include='*.ts'
--include='*.tsx' --include='*.html' . | wc -l` → saída: `0` — a linhagem não tem tema
algum; o RI-06 nasce sem referência. 🟢

F-08: `/home/user/tocbuilderv3/services/geminiService.ts:16` — cliente de provedor de
modelo inicializado no navegador — a violação canônica que o RNF-02 proíbe (mesma fonte
F-01 da spec 001). 🟢

F-09: `/home/user/protocolos/padrao/anexo-b-federacao.md:159` — "**B.8.1** Embarcada, a
aplicação **DEVE** renderizar **apenas o conteúdo**: sem o seu próprio cabeçalho de
navegação…" — a norma do modo só-conteúdo; fundamenta RI-09. 🟢

## Lacunas e assunções

L-01: Não medimos a largura real do iframe na fundação — os 420px são a prova da irmã
[F-06], não a nossa. **Assunção**: 420px como referência de estreito até o embarque real
do ciclo 003 medir; se divergir, as capturas estreitas regeneram (são de protótipo).
Risco **baixo**.

L-02: A lista de `theme.tokens` que um inquilino da fundação realmente define não é
conhecida — a interseção depende do `theme.tokens_used` do nosso manifesto, que só existe
no ciclo 003. **Assunção**: o adaptador falso entrega um conjunto mínimo plausível e o
*fallback* cobre o resto, como a norma manda [F-04]. Risco **baixo**.

L-03: O catálogo `toc.*` não existe ainda (ciclo 006), então o protótipo não valida a
interface do ciclo propor → confirmar → executar — que a irmã validou cedo no protótipo
dela. **Assunção**: a forma dessa interface é prototipável no próprio ciclo 006, sobre
build real, com o custo de uma rodada de ajuste a mais. Risco **médio**.

## Clarify

- [DÚVIDA] A pergunta 1 da [`../../docs/produto/visao.md`](../../docs/produto/visao.md)
  §7 (colaboração por projeto × isolamento por usuário) é precondição deste ciclo: o
  protótipo assume a proposta (projeto compartilhável com papéis dentro do inquilino) —
  confirma antes de abrir o ciclo?
- [DÚVIDA] Existe ambiente da fundação de onde colher valores reais de `theme.tokens` de
  um inquilino de teste para o adaptador falso, ou seguimos com tokens inventados (L-02)?
- [DÚVIDA] A visão conflito+solução (RI-13) entra no apetite ou já nasce cortada? O round
  002 a declara "sai primeiro"; decidir antes evita cortá-la no meio da execução.
