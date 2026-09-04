# Changelog

Formato: [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/).
Versionamento: [SemVer](https://semver.org/lang/pt-BR/).

## [Não publicado]

### Ciclo 001 — Fundação e planejamento (entregue, aguardando gate humano)

- **Método Maestro instalado** pelo instalador oficial (`bin/maestro init` do canônico)
  antes de qualquer artefato: agentes, skills, scripts do ritual, comandos e a governança
  do método (`docs/governance/`), verificados por `scripts/check-install.sh`.
- **Visão do produto** (`docs/produto/visao.md`): o problema (dilemas e conflitos
  organizacionais analisados sem método), o que a Teoria das Restrições (TOC) oferece, e
  a **linhagem medida** — quatro gerações de TOC-Builder e cinco repositórios natimortos
  contados por `ls` com a saída colada, onze defeitos D-01..D-11 cada um com o comando
  executado (a chave do provedor no navegador nas quatro gerações; a especificação de API
  byte-idêntica quatro vezes e nunca implementada; zero testes; metade das ferramentas
  quatro gerações desabilitada; a Estratégia & Táticas que regrediu), e as cinco
  perguntas ao Product Steward mantidas abertas com resposta proposta.
- **Mapa de módulos** (`docs/produto/modulos.md`): M1–M8 como *bounded contexts*, épicos
  por módulo, dependências e o grafo de ordem de construção — cada módulo amarrado ao
  defeito de linhagem que corrige ou à lacuna que preenche.
- **Rounds** (`docs/produto/rounds.md`): onze rounds mapeando os ciclos 002–012, cada um
  com os seis campos obrigatórios (Apetite · Entrega · Fora · Aptidão executável ·
  Depende de · Sai primeiro/Nunca sai), a aptidão do 003 fixada em **"a junta fecha
  contra a `ghdaru` real"**, alocação exaustiva dos onze defeitos (nove em rounds, dois
  não-corrigidos com motivo declarado), e os **bloqueios externos declarados** com
  caminho — os schemas de manifesto mutuamente exclusivos e os grants em memória
  (medições da irmã `gestaodeprioridades`, mensagem 005), e a ação federada sem
  credencial com F7 pendente (ADR 0023 do `ghdaru`).
- **Roadmap de ciclos** (`docs/roadmap.md`): os doze ciclos com raia, portões em bullets
  e a pré-condição explícita de cada um ("o que o ciclo NNN não pode começar sem");
  nenhuma linha de código de produção antes do ciclo 003.
- **Decisões estruturais** em Registro de Decisão Arquitetural (ADR), 0001–0008
  (`docs/adr/`): constituição própria e herança das regras R1–R5 da irmã; stack; a
  federação APH (Aplicação ↔ Harness) Nível 2 `mode: embedded`; taxonomia de
  planejamento com selos de confiança; escopo v1 (tambor-pulmão-corda fora, com a
  contagem zero colada); base sintética desde o dia 1; inteligência artificial somente
  pela fundação; site de produto gerado por script.
- **12 specs** (`specs/001-fundacao-e-planejamento/` a
  `specs/012-jornadas-e-autodeclaracao/`): a do próprio ciclo e as onze de planejamento
  dos módulos e fatias, no formato do ADR 0004 — requisitos com fonte e selo, lacunas
  L-NN e `## Clarify` limitado a cinco dúvidas por spec.
- **Gerador do site de produto vendorizado** (`tools/product-site/`, ADR 0008): o
  `spec-to-code-docs` de `GHDaru/daruskills` copiado com atribuição e **adaptado** ao
  vocabulário deste corpus — requisitos de interface (RI-NN) como tipo próprio ao lado de
  RF, RNF, RN e INT; agrupamento pelos sub-cabeçalhos que o autor escreveu; fontes lidas da
  seção `## Fontes` (F-NN com `arquivo:linha`); vocabulário da Teoria das Restrições; as
  oito fases reais do Maestro com dono, métrica e aresta de falha; taxonomia de 15 termos em
  três categorias. O `tools/product-site/templates/styles.css` fica **byte a byte idêntico** à origem (mesma
  soma `md5`), porque a régua de design não se troca por gosto.
- **Site de produto gerado** (`docs/product-site/`): quatro páginas — visão geral com
  taxonomia, workflow, ADRs, princípios, artefatos e métricas; os módulos M1–M8 com épicos
  e as doze specs; a matriz de rastreabilidade com 359 RF, 114 RI e 105 RNF, cada um com
  selo e fonte; e o roadmap dos doze ciclos com os portões reais e a **nota de honestidade**
  (ciclo 001 em curso, zero linha de código de produção, nenhuma jornada viva). Todo número
  é contado na geração (regra R1), e regerar duas vezes produz bytes idênticos.
- **Primeira mensagem externa** (`mensagens/001-para-daruskills-defeitos-do-gerador-de-site.md`):
  sete achados no gerador de origem, reproduzidos rodando-o cru contra este repositório —
  entre eles, os princípios da constituição contados como requisito não funcional em todas
  as specs (189 contra 105 reais), a fronteira de feature dividida por média (cinco das sete
  features da spec 004 com intervalo errado) e os portões do roadmap descartados em favor de
  uma tira fixa. Relatada e parada, como manda o P1.

- **Base sintética da "Instituição Horizonte"** (`docs/produto/dados/`, ADR 0006): a
  primeira base de dados do projeto nasce **sintética e declarada como tal no próprio
  arquivo** (`sintetica: True`) — uma instituição de ensino técnico fictícia, três
  personas que são **papéis** e não pessoas ("Facilitadora TOC", "Participante",
  "Gestora"), uma Árvore da Realidade Atual (ARA) de 16 nós (12 Efeitos Indesejáveis —
  UDE — e 4 causas) com 16 arestas causais, e uma Nuvem de Conflito de 5 entidades, 7
  arestas com premissa e 2 injeções. O medidor `docs/produto/dados/medir-base.py` valida
  a estrutura e roda as checagens: `validação estrutural: 0 falha(s)`, código de saída 0.
  A dívida que obriga a irmã `gestaodeprioridades` a ser um repositório privado **não
  nasceu aqui**, e passou a ser verificável em vez de prometida.
- **Defeito D-12 — os critérios de UDE nunca foram medidos** (`docs/produto/visao.md:406`,
  alocado ao round 005 em `docs/produto/rounds.md:322`): as quatro gerações da linhagem
  TOC-Builder carregam onze características de UDE **apenas como texto de prompt**, sem
  nenhuma jamais ter sido executada. O ciclo mediu: das 11 características, **8 checagens
  cobrindo 7 são decidíveis por função pura** e **4 exigem julgamento** e ficam fora do
  alcance de qualquer função. Sobre os 12 UDEs autorais, 3 passam e 9 reprovam, cada
  reprovação nomeando a checagem (CD-1 a CD-8). D-12 vira critério de aceite do épico
  E2.1 no ciclo 005 — a regra de domínio pura que o P3 exige, testável sem rede e sem
  modelo.
- **A circularidade do D-12 foi atacada com um conjunto de controle externo** — a
  pendência declarada pelo construtor da visão e o achado que custou a única derrota do
  gauntlet: a base autoral foi escrita pelo mesmo autor das checagens e *para* trazer as
  patologias que elas procuram, logo "3 de 12" mede acordo do autor consigo mesmo. O
  retrabalho colheu **9 enunciados da própria linhagem**, escritos antes das checagens e
  por outra mão (`tocbuilderv3/constants.ts` e `components/CanvasWelcome.tsx`, os oito de
  `constants.ts` idênticos nas quatro gerações), e mediu: **0 falso positivo, 1 falso
  negativo (K-03)**. Um defeito real nas checagens, achado por um conjunto que não foi
  escrito para elas.
- **Suíte de sabotagem** (`scripts/tests/run-sabotagem.sh`): os cinco portões deste
  projeto provados **não lenientes** — `portões cobertos: 5 · bases válidas aceitas: 5/5`
  e `sabotagens declaradas: 27 · reprovadas pelo motivo certo: 27/27`, cada sabotagem
  sobre uma cópia em `/tmp`, sem tocar o repositório. Código de saída 0. As quatro últimas
  são as do `scripts/check-vazamento.sh`, o portão que substituiu a linha 11 da DoD.
- **Agregador de evidência** (`scripts/evidencia.sh`): roda a bateria e emite a tabela com
  comando, código de saída e **denominador** de cada portão (regra R2) —
  `Portões executados: 6 · verdes: 6 · vermelhos: 0`.
- **`qa-report.md` do ciclo 001 preenchido com evidência real**
  (`specs/001-fundacao-e-planejamento/qa-report.md`): **18 verificações distintas, 17
  verdes e 1 vermelha**, toda saída colada literalmente; o veredito do gauntlet (10 peças
  julgadas às cegas contra o corpus da irmã `gestaodeprioridades` e o PROJETO_ECS — 9
  vitórias na primeira rodada, a visão de produto derrotada, retrabalhada e vencedora no
  rejulgamento, fechando 10/10); e a cauda com `TAIL:review`, `TAIL:security` e
  `TAIL:mutation` escritos. `TAIL:gate` fica **em branco de propósito**: o gate humano é
  do Product Steward e é indelegável.
- **Critério 11 da DoD reescrito, e provado por sabotagem** (`scripts/check-vazamento.sh`):
  ele media a *string do caminho* da base da irmã `gestaodeprioridades` quando dizia medir
  **vazamento de dado real de pessoa**, e por isso reprovava a própria evidência do ADR
  0006 — um comando que imprime só contagens. O critério novo mede **conteúdo**, em três
  sinais: nome próprio em campo de pessoa, registro no formato do esquema da irmã (quatro
  ou mais chaves no mesmo registro) e base real lida por código que não é `*.md`. Ele varre
  `arquivos varridos: 195 · linhas varridas: 51485 · registros JSON inspecionados: 2557` e
  sai 0; e **reprova quatro sabotagens** que plantam vazamento fictício. A troca está
  declarada na `specs/001-fundacao-e-planejamento/spec.md`. Não é afrouxamento: o critério
  novo é **mais largo** que o antigo — pega três classes que o antigo não via.
- **Verificador executável dos rounds** (`scripts/check-rounds.sh`): os sete campos
  obrigatórios por round, o grafo de dependências e a alocação exaustiva dos defeitos
  D-NN passaram a ser conferidos por máquina — `rounds examinados: 11 · conferências de
  campo: 77 · arestas de dependência: 15 · ciclos encontrados: 0 · defeitos medidos: 12 ·
  alocados a round: 10 · declarados sem round: 2`, código de saída 0, e cinco sabotagens
  provando que ele reprova. Era a dívida declarada em "Conhecido" deste mesmo ciclo.
- **Procedimento de fechamento de ciclo** (`docs/governance/como-fechar-um-ciclo.md`): o
  que o Product Steward confere antes de assinar (os sete itens do §8 do `qa-report.md`),
  o estado real das branches deste repositório (a branch de trabalho **não** se chama
  `dev` e a `main` local **não existe** — as duas medidas com `git rev-parse`), o comando
  exato de promoção com `MAESTRO_DEV_BRANCH`, o que o `scripts/promote-main.sh` grava em
  `docs/records/decisoes.jsonl`, e como reverter. O comportamento do script foi **medido
  num clone temporário com repositório remoto falso**, não descrito de memória: ele aborta
  hoje no portão de conformidade, e a rota manual que o próprio script autoriza está
  escrita. Nenhum agente executou a promoção — aprovar merge é portão humano inegociável, e
  quem executou não aprova o que executou.

### Conhecido

- **O gate humano do ciclo 001 está aberto**: são sete itens, tabelados no §8 de
  `specs/001-fundacao-e-planejamento/qa-report.md` — ratificar a constituição e os oito
  ADRs; responder as cinco perguntas da visão §7 e as três dúvidas do `## Clarify`;
  ratificar o critério 11 reescrito; autorizar a entrega da mensagem 002 ao método;
  aceitar ou recusar as sete dívidas do §9; e autorizar a promoção. O procedimento está
  em `docs/governance/como-fechar-um-ciclo.md`. Nada abaixo do ciclo 002 começa antes
  disso, e **nenhum agente executou a promoção**.
- **A promoção não roda pelo caminho feliz hoje**: o `scripts/promote-main.sh` chama
  `scripts/check-conformance.sh` sem argumento no seu passo 3 e aborta, porque o portão do
  método sai 1 (`✗ no cycle in range (floor 42) — the gate checked nothing.`). O próprio
  script prevê o caso e autoriza a rota manual quando a dívida está decidida e registrada
  — ela está (Dv-3 do §9). Some-se a isso que a branch de trabalho não se chama `dev` e a
  `main` local não existe neste clone: as duas coisas exigem uma variável de ambiente e um
  `git branch` antes de promover. Tudo medido e escrito em
  `docs/governance/como-fechar-um-ciclo.md`.
- **Um portão vermelho, diagnosticado e não afrouxado** (detalhe em
  `specs/001-fundacao-e-planejamento/qa-report.md` §4):
  - `scripts/check-conformance.sh 001` sai **1** por causa **externa**: os pisos do script
    são números **absolutos** de ciclo da história do repositório canônico do método
    (`FLOOR=42` na linha 52, `CRIT_FLOOR=45` na 54, `ABSENCE_FLOOR=61` na 77,
    `MUT_FLOOR=55` na 91). Num repositório que começa no ciclo 001, o ciclo mais novo é
    `012` por construção, logo `55 > 12` e `61 > 12` são verdadeiros para sempre e os
    blocos de sanidade do fecho (linhas 468-475) reprovam independentemente do que este
    repositório escreva. O arquivo é a superfície instalável do método e `GHDaru/maestro`
    é **leitura** (P1): **relatado e parado**, pendente a mensagem externa. Apertando os
    pisos para 1 — o que o próprio script permite, porque seus knobs só admitem apertar —
    o veredito substantivo aparece e é sobre o conteúdo, não sobre o piso.
  - O **segundo vermelho deixou de existir**: a linha 11 da DoD contava `1` onde a spec
    esperava `0`, e a única ocorrência era o **caminho** citado no bloco de evidência do
    ADR 0006 — um comando que imprime só contagens (`tarefas: 114`) e nunca conteúdo.
    Corpo de ADR committado não se reescreve e portão não se afrouxa; sobrou a rota certa,
    que era reescrever o **critério** para medir o que ele dizia medir. Feito, declarado na
    spec e provado por quatro sabotagens. **O que aguarda o Product Steward é a
    ratificação da troca de critério, não a execução dela.**
- **Sete dívidas declaradas com dono e ciclo**, tabeladas no §9 de
  `specs/001-fundacao-e-planejamento/qa-report.md`. As que mudam o próximo ciclo:
  - **RNF-01 (português no projeto, inglês na superfície instalável) não tem portão
    executável** — hoje é verificado por leitura. Dono: construtor do ciclo 002.
  - **`docs/produto/rounds.md:18` ainda declara que o verificador executável dos rounds
    "ainda não existe"** — e ele existe, passou com 77 conferências de campo e foi
    sabotado cinco vezes. O arquivo ficou fora dos lotes do fechamento; corrigir é uma
    linha, na abertura do ciclo 002. (Esta entrada do `CHANGELOG.md`, que carregava a
    mesma afirmação vencida, **foi corrigida acima**.)
  - **A seção "Fora de escopo" é pontuada e não bloqueante** no `scripts/check-specs.sh`:
    perdê-la custa 8 dos 15 pontos de Escopo e a spec continua passando no corte ≥ 80.
    Apertar exige a sabotagem que veja o portão reprovar — trabalho de ciclo.
  - **A circularidade da base autoral está mitigada, não resolvida** (9 enunciados de
    controle externos, 4 das 11 características de UDE indecidíveis por função pura).
    Fecha só com corpus de oficina real, e isso esbarra no ADR 0006 — vai para o ciclo 005.
- **Três bloqueios externos** condicionam o ciclo 003 e dois o alcance do 006 — todos de
  fora deste repositório, todos com caminho citado em `docs/produto/rounds.md`; a regra
  é re-medir na abertura do ciclo afetado, não assumir que caíram.
