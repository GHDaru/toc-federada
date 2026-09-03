# Sequência de ciclos

> Siglas deste documento: **TOC** — Teoria das Restrições; **APH** — o padrão Aplicação ↔
> Harness; **ADR** — Registro de Decisão Arquitetural; **TDD** — desenvolvimento guiado por
> teste; **CI** — integração contínua; **OTel** — OpenTelemetry; **FSM** — máquina de
> estados finitos; **UDE** — Efeito Indesejável; **ARA** — Árvore da Realidade Atual;
> **NC** — Nuvem de Conflito; **ARF** — Árvore da Realidade Futura; **APR** — Árvore de
> Pré-Requisitos; **AT** — Árvore de Transição; **S&T** — Árvore de Estratégia & Táticas;
> **i18n** — internacionalização; **SSE** — *Server-Sent Events*; **eTLD+1** — o "site" no
> sentido do navegador.
>
> Proposta ao Product Steward em 2026-09-03, ciclo 001. **Nenhuma linha de código de
> produção nasce antes do ciclo 003** — e o protótipo do ciclo 002 é descartável por
> decisão, não promessa. A ordem existe para que a implementação comece sabendo o que
> construir, com que interface e em que ordem; o conteúdo de cada ciclo (entrega, fora,
> sai primeiro) está em [`produto/rounds.md`](produto/rounds.md), round de mesmo número.
> Apetite: um ciclo por linha — estourou, perde escopo, não ganha ciclo.

| Ciclo | Nome | Entrega | Raia |
|---|---|---|---|
| **001** | Fundação e planejamento | este corpus: método instalado, constituição, visão medida da linhagem, 8 ADRs, 12 specs, roadmap, site de produto | plena |
| **002** | Protótipo de interfaces | protótipo descartável + `ux-design.md` + jornadas com capturas geradas por script | plena |
| **003** | Esqueleto federado | a junta fecha contra a `ghdaru` real: admissão, introspecção, manifesto, embarque, banco próprio, OTel, CI | infra |
| **004** | Núcleo de diagramas | M1 completo com TDD | plena |
| **005** | Árvore da Realidade Atual | M2 completo, sem assistência (E2.3 entra no 006) | plena |
| **006** | Ações governadas e snapshot | catálogo `toc.*`, FSM de proposta, registro de telas, snapshot, wire Nível 1 | plena |
| **007** | Nuvem de Conflito | M3 completo | plena |
| **008** | Árvores de futuro e implementação | M4 completo (ARF, APR, AT, encadeamento) | plena |
| **009** | Focalização | M6 completo | plena |
| **010** | Estratégia & Táticas | M5 completo | plena |
| **011** | Fundações da aplicação | E8.3 consolidada, E8.4, E1.4 avançado | plena |
| **012** | Jornadas e autodeclaração | jornadas consolidadas, matriz de aderência APH, autodeclaração Nível 2 em ADR, site atualizado | plena |

## Ciclo 001 — Fundação e planejamento (entregue — aguardando o gate humano)

Acertar a herança antes de qualquer outra coisa: a linhagem lida e **medida** (não
lembrada), a constituição do projeto, as decisões estruturais em ADR com alternativas
numeradas, o mapa de módulos, os rounds e as 12 specs — para que nenhuma geração 5ª
comece do zero de novo (defeito D-10 da [`produto/visao.md`](produto/visao.md)).

**Estado em 2026-09-03: o corpus está entregue e os portões rodaram; a aprovação não
existe ainda.** A evidência completa — comando, código de saída e denominador de cada
portão — está em
[`../specs/001-fundacao-e-planejamento/qa-report.md`](../specs/001-fundacao-e-planejamento/qa-report.md).
Foram **17 verificações distintas: 15 verdes e 2 vermelhas**, as duas diagnosticadas com
causa raiz e **nenhuma afrouxada**. O ciclo **não está promovido**: enquanto o Product
Steward não assinar, ele está entregue, não aprovado — e nada do ciclo 002 começa.

- Portão humano — **ABERTO, indelegável**: o Product Steward ratifica a constituição, os
  8 ADRs e as respostas às cinco perguntas da
  [`produto/visao.md`](produto/visao.md) §7 (ou o adiamento explícito de cada uma), decide
  os dois achados vermelhos e autoriza a promoção `dev` → `main`.
- Portão de revisão — **cumprido**: a revisão independente foi um **gauntlet de crítica às
  cegas**, 10 peças julgadas por críticos em contexto fresco contra dois corpora externos
  (o da irmã `gestaodeprioridades` e o do PROJETO_ECS). Placar: 9 vitórias na primeira
  rodada, **uma derrota real** — a visão de produto, por circularidade da base autoral —,
  retrabalho dirigido pela lacuna nomeada e vitória no rejulgamento: **10/10**. Os achados
  que ficaram abertos estão listados no `qa-report.md` §5, não foram apagados.
- Portões executáveis — **verdes, com o denominador na saída** (regra R2):
  `scripts/check-install.sh` (7 camadas, 6 skills) · `scripts/check-links.sh`
  (`checked: 337`) · `scripts/check-caminhos.sh` (74 arquivos, 572 caminhos) ·
  `scripts/check-specs.sh` (12 ciclos, 628 verificações) · `scripts/check-rounds.sh`
  (11 rounds, 77 conferências) · `scripts/check-adrs-sucessao.sh` (8 ADRs, 32
  verificações) · `scripts/tests/run-sabotagem.sh` (4 bases aceitas, 23 sabotagens
  reprovadas) · `python3 docs/produto/dados/medir-base.py` (base sintética válida).
- Portões executáveis — **vermelhos, declarados em vez de contornados**:
  `scripts/check-conformance.sh 001` sai 1 por causa **externa** (os pisos do script são
  números absolutos de ciclo do repositório canônico do método, e um repositório que
  começa em 001 nunca os alcança — P1 impede consertar lá, então foi relatado e parado);
  e a **linha 11 da DoD** conta 1 onde espera 0, porque casa o *caminho* citado no bloco
  de evidência do ADR 0006 — um comando que imprime só contagens — e não conteúdo
  vazado. Os dois aguardam decisão no gate humano.
- Portão de honestidade — **cumprido**: nenhum selo 🟢 sem `arquivo:linha`; nenhuma
  contagem sem a saída colada; nenhuma caixa marcada sem a evidência escrita ao lado.

### O que o ciclo 001 não pode começar sem

- O método Maestro instalado pelo instalador oficial e verificado
  (`scripts/check-install.sh`) — **feito**, é a condição em que este repositório nasceu.
- A linhagem inteira legível na sessão (as quatro gerações e os cinco natimortos) —
  **feito**, contagem colada na [`produto/visao.md`](produto/visao.md) §3.

## Ciclo 002 — Protótipo de interfaces

Prototipar as telas de M1–M3 com prova visual: papel semântico e `ai_visible` campo a
campo **antes** de componente, jornada com captura gerada do build por script versionado
e avaliação heurística datada (princípio P6). O protótipo é descartável — reduz risco de
interface, não vira produção.

- Portão humano: o Product Steward aprova o corte de telas (o que da densidade do canvas
  + vista tabular sobrevive num iframe estreito).
- Portão executável: capturas regeneram byte-idênticas ao rodar o script de novo;
  `scripts/check-caminhos.sh` verde sobre as jornadas.
- Portão de revisão: avaliação heurística datada por jornada, no mesmo pull request.

### O que o ciclo 002 não pode começar sem

- O gate humano do ciclo 001 fechado — em particular a **pergunta 1** da
  [`produto/visao.md`](produto/visao.md) §7 (colaboração por projeto ou isolamento por
  usuário) respondida, porque ela muda as telas de projeto do E1.1.
- As specs dos módulos M1–M3 aprovadas ao menos em rascunho ratificado (os requisitos de
  interface saem delas).

## Ciclo 003 — Esqueleto federado

O primeiro corte: a aplicação existe, embarcada, com identidade real e banco próprio —
ainda sem ferramenta TOC. Raia **infra**: reversibilidade explícita (migração com
downgrade, deploy com rollback documentado) é parte da entrega.

- Portão executável (a aptidão mais importante do roadmap): **"a junta fecha contra a
  `ghdaru` real"** — manifesto aceito pela rota de administração real, grant trocado por
  identidade em `POST /auth/introspect` servidor a servidor, `ev.source` e `origin`
  verificados, falha fechada com a fundação indisponível, traço OTel de ponta a ponta.
  Nada disso contra shell simulado.
- Portão executável: migração Alembic aplicada num Neon limpo e revertida sem resíduo.
- Portão de segurança: passagem de segurança em contexto fresco sobre a admissão e o
  embarque (a irmã achou quatro furos na dela; assumir que não temos seria vaidade).
- Portão humano: aprovação do endereço publicado (eTLD+1 distinto do hospedeiro) — é
  irreversível na prática, porque entra no manifesto que circula.

### O que o ciclo 003 não pode começar sem

- A re-medição dos **três bloqueios externos** declarados no round 003 de
  [`produto/rounds.md`](produto/rounds.md): o alinhamento dos schemas de manifesto
  (quando a irmã mediu, 4 erros — mutuamente exclusivos), a fatia de federação ligada no
  hospedeiro, e o estado dos grants em memória. Se o primeiro persistir, o ciclo entra
  mesmo assim e entrega tudo menos o registro do manifesto — com mensagem nossa
  referenciando a da irmã.
- ADR 0002 (stack) e ADR 0003 (federação) ratificados — o ciclo é a execução deles.

## Ciclo 004 — Núcleo de diagramas

M1 completo com TDD: projetos com *soft delete*, canvas, vista tabular equivalente,
exportação/importação não destrutiva. Primeira funcionalidade atravessando a junta.

- Portão executável: suíte de domínio verde e sem rede; contrato de `import-linter` que
  falha o build se o domínio importar framework (P3).
- Portão executável: exportar → reimportar devolve JSON idêntico; importação inválida
  recusa com relato.
- Portão de jornada: jornada viva do primeiro projeto sintético com captura do build (P6).

### O que o ciclo 004 não pode começar sem

- O ciclo 003 promovido — sem junta, o M1 seria a 5ª geração standalone.
- A spec do M1 (`specs/004-nucleo-de-diagramas/`) com o `## Clarify` respondido.

## Ciclo 005 — Árvore da Realidade Atual

M2 sem assistência: validação formal de UDE como regra de domínio pura (correção do
D-08), construção da árvore com análise de suficiência.

- Portão executável: os critérios decidíveis de UDE avaliados por teste **sem rede e sem
  modelo**.
- Portão de jornada: construção de uma ARA sintética completa, com captura do build.
- Portão de revisão: revisão independente confere que nenhum critério de UDE ficou
  dependente de prompt.

### O que o ciclo 005 não pode começar sem

- O ciclo 004 promovido (a ARA é feita de nós e arestas do M1).
- Os critérios formais de UDE transcritos do prompt do v3
  (`tocbuilderv3/constants.ts:109-137`) para a spec do M2, com a separação
  decidível × julgamento marcada requisito a requisito.

## Ciclo 006 — Ações governadas e snapshot

O catálogo `toc.*`, a FSM de proposta no servidor, tela como dado (registro + snapshot
sanitizado), wire APH Nível 1 (SSE, `seq`, replay, cancelamento). Primeiro consumidor:
a assistência da ARA (E2.3).

- Portão executável: sem capability de escrita, as ações mutadoras **somem do catálogo**
  (teste, com a contagem antes/depois na saída).
- Portão executável: nenhuma mutação proposta por modelo aplica fora da FSM; snapshot
  sem campo `ai_visible: false`; replay por `seq` testado.
- Portão humano: o catálogo `toc.*` aprovado ação a ação (nomes, riscos, capabilities) —
  é contrato que circula no manifesto.

### O que o ciclo 006 não pode começar sem

- O ciclo 005 promovido (as primeiras ações operam sobre a ARA).
- Os dois bloqueios externos do round 006 re-medidos e **aceitos como limite de
  alcance** ([`produto/rounds.md`](produto/rounds.md)): ação federada sem credencial do
  lado do host (F7 pendente — `ghdaru/docs/adr/0023-acoes-federadas-por-adapter-remoto.md`)
  e grant sem interseção com o usuário. A nossa borda nasce recusando chamada não
  autenticada; o que fica limitado é a execução disparada do harness, não a FSM.

## Ciclo 007 — Nuvem de Conflito

M3 completo: 5 entidades, 7 premissas, injeções, geração assistida pela fundação, visão
conflito+solução.

- Portão executável: invariantes da nuvem por teste de domínio (5 entidades, 7 arestas,
  injeção referencia premissa).
- Portão executável: a geração a partir de narrativa entra como `action_proposal`;
  recusar deixa o projeto intacto (teste).
- Portão de jornada: o dilema sintético da "Instituição Horizonte" de ponta a ponta, com
  captura.

### O que o ciclo 007 não pode começar sem

- Os ciclos 004 e 006 promovidos.
- A spec do M3 com as 7 premissas modeladas (a skill `toc-evaporating-cloud` é a fonte
  técnica; a spec é a norma).

## Ciclo 008 — Árvores de futuro e implementação

M4 completo: ARF, APR (obstáculos → objetivos intermediários), AT — e o encadeamento
UDE → NC → injeção → ARF → obstáculos → APR, que nenhuma geração modelou (D-11).

- Portão executável: teste de domínio percorre a cadeia inteira e prova a referência de
  origem em cada elo.
- Portão executável: as três árvores exportáveis/importáveis pelo E1.4.
- Portão de jornada: da injeção à APR sequenciada, com captura.

### O que o ciclo 008 não pode começar sem

- Os ciclos 005 e 007 promovidos (o encadeamento parte do que eles produzem).
- Decisão registrada sobre o corte de ramos negativos da ARF (fica manual nesta v1 —
  proposta no round 008).

## Ciclo 009 — Focalização

M6 completo: registro da restrição e jornada guiada pelos cinco passos, costurando as
ferramentas.

- Portão executável: teste percorre os cinco passos com estado herdado entre eles;
  "recomeçar" reabre sem apagar histórico.
- Portão de jornada: uma análise sintética atravessa identificar → explorar → subordinar
  → elevar → recomeçar, com captura por passo.

### O que o ciclo 009 não pode começar sem

- O ciclo 008 promovido (a jornada aponta para ferramentas que precisam existir).
- ADR 0005 (escopo v1) inalterado — se DBR entrar, é decisão nova antes, não durante.

## Ciclo 010 — Estratégia & Táticas

M5 completo: a ferramenta que regrediu na 3ª geração (D-05), de volta — hierarquia
numerada e as três premissas lógicas por nó.

- Portão executável: teste de renumeração da subárvore; as três premissas persistidas.
- Portão de jornada: uma S&T sintética de três níveis, com captura.

### O que o ciclo 010 não pode começar sem

- O ciclo 004 promovido (é a única dependência técnica; a posição tardia é escolha de
  valor registrada em [`produto/rounds.md`](produto/rounds.md)).

## Ciclo 011 — Fundações da aplicação

M8 restante: i18n pt/en consolidada, documentação embutida por ferramenta, importação
dos exports da 4ª geração (E1.4 avançado).

- Portão executável: nenhuma string de interface fora do dicionário de i18n (grep em CI,
  contagem na saída — regra R2).
- Portão executável: importar um export sintético do `tocbuilderv3` cria o projeto ou
  recusa com relato campo a campo.
- Portão de jornada: a documentação embutida acessível de cada ferramenta.

### O que o ciclo 011 não pode começar sem

- O ciclo 008 promovido (a documentação embutida cobre as ferramentas existentes).

## Ciclo 012 — Jornadas e autodeclaração

Fechamento: jornadas consolidadas de ponta a ponta, matriz de aderência ao APH
re-verificada, **autodeclaração de Nível 2 (Operador) em ADR** com evidência por
requisito, site de produto atualizado pelo gerador.

- Portão executável: todas as capturas regeneram do build atual; o site regenerado não
  diverge do commitado (diff vazio em CI).
- Portão de revisão: a matriz de aderência com um veredito por requisito APH, cada um
  com evidência por caminho — revisada em contexto fresco.
- Portão humano: o Product Steward assina a autodeclaração — é ela que circula para fora
  do repositório.

### O que o ciclo 012 não pode começar sem

- Os ciclos 009, 010 e 011 promovidos — autodeclarar antes seria declarar sem provar,
  que é o anti-padrão que este projeto existe para não repetir.
