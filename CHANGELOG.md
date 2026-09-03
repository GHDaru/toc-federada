# Changelog

Formato: [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/).
Versionamento: [SemVer](https://semver.org/lang/pt-BR/).

## [Não publicado]

### Ciclo 001 — Fundação e planejamento (em andamento)

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

### Conhecido

- **O gate humano do ciclo 001 está aberto**: constituição, ADRs e as cinco perguntas da
  visão §7 aguardam o Product Steward. Nada abaixo do ciclo 002 começa antes disso.
- **A aptidão executável de `docs/produto/rounds.md` é dívida declarada** (🔴): o
  verificador dos seis campos e da alocação D-NN não existe ainda; a revisão
  independente do ciclo 001 confere manualmente até ele entrar (candidato: fechamento do
  ciclo 002).
- **Três bloqueios externos** condicionam o ciclo 003 e dois o alcance do 006 — todos de
  fora deste repositório, todos com caminho citado em `docs/produto/rounds.md`; a regra
  é re-medir na abertura do ciclo afetado, não assumir que caíram.
