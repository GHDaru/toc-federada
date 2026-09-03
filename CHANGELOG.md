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
