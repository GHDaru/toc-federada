# ADR 0004 — Taxonomia de planejamento (Módulo ⊃ Épico ⊃ Feature ⊃ Story) e absorção da metodologia reversa sem instalar o framework

- **Status**: Aceita
- **Data**: 2026-09-03 · **Ciclo**: 001
- **Decisor**: agente construtor do ciclo 001, sob a regra R3 (decisão registrada;
  confirmação no gate humano do ciclo 001)
- **Sucede**: nenhum
- **Princípios tocados**: **P1** — a alternativa descartada (instalar o framework
  `reversa`) gravaria arquivos de entrada de agente (`CLAUDE.md`/`AGENTS.md`) por cima
  dos do Maestro; a absorção por cópia de conceitos, com atribuição, é o que mantém a
  fronteira e a superfície instalável intactas.

## Contexto

Este ADR (Architecture Decision Record, registro de decisão arquitetural) fixa como o
planejamento desta aplicação é estruturado — a hierarquia, os tipos de requisito e a
régua de prontidão de especificação (DoR, *Definition of Ready*).

O método Maestro dá o fluxo (`spec → plan → tasks → implement → DoD → review → gate`),
mas não impõe taxonomia de requisitos. Duas fontes maduras estavam disponíveis:

**A profundidade do ECS** — a spec de referência daquele projeto usa numeração de
requisito por módulo com fonte por item:

```text
$ grep -c 'RF-' /home/user/ECS/specs/001-catalogo-itens/spec.md
36
```

**A metodologia reversa** (`sandeco/reversa`, clone lido em modo leitura — nas medições
abaixo, `scratchpad/reversa` abrevia o caminho do clone temporário da sessão de
construção; o clone não faz parte deste repositório). Medida, não estimada:

```text
$ ls scratchpad/reversa/agents | wc -l
72
$ find scratchpad/reversa/agents -name 'SKILL.md' | wc -l
72
$ grep -n 'Dimensão' scratchpad/reversa/agents/reversa-spec-sdd/references/evaluation_rubric.md
9:## Dimensão 1: Completude (30 pontos)
26:## Dimensão 2: Testabilidade (25 pontos)
42:## Dimensão 3: Clareza (20 pontos)
58:## Dimensão 4: Escopo (15 pontos)
74:## Dimensão 5: Edge Cases (10 pontos)
$ head -2 scratchpad/reversa/LICENSE
MIT License
Copyright (c) 2026 Sandeco
```

**72 agentes**, cada um com seu `SKILL.md`, sob licença MIT 🟢. O instalador do framework
grava arquivos de entrada de engine — *"Instala o arquivo de entrada de uma engine
(CLAUDE.md, AGENTS.md, etc.)"* (`reversa/lib/installer/writer.js:91` 🟢) — ou seja,
instalar é criar um **segundo cérebro** por cima do que o Maestro já governa.

## Decisão

1. **Hierarquia**: **Módulo (M1–M8) ⊃ Épico (E\<m\>.\<n\>) ⊃ Feature (F\<m\>.\<n\>.\<k\>)
   ⊃ User Story (US-NN por módulo)**. O mapa de módulos vive em
   `docs/produto/modulos.md`; requisitos são numerados **por spec** (a numeração reinicia
   a cada spec, como no ECS).
2. **Tipos de item**, um por linha, na forma `SIGLA-NN: texto [fonte] selo`:
   **RF** (funcional, forma EARS: *"O SISTEMA DEVE …"* / *"QUANDO \<gatilho\>, O SISTEMA
   DEVE …"*), **RI** (interface), **RNF** (não funcional), **RN** (regra de negócio da
   Teoria das Restrições — TOC), **INT** (integração de fronteira), **F** (fonte, com
   caminho e trecho), **L** (lacuna declarada com assunção e risco), **US** (user story
   com critérios Gherkin — ao menos uma por feature).
3. **Selos de confiança** em todo fato: 🟢 CONFIRMADO (com `arquivo:linha`),
   🟡 PLANEJADO/INFERIDO, 🔴 LACUNA (com L-NN). Absorvidos da reversa.
4. **Dúvida nunca se resolve em silêncio**: vira marcador `[DÚVIDA]` levado à seção
   `## Clarify` da spec (máximo 5 por spec), aberta até o gate humano. Absorvido da
   reversa (`reversa-clarify`).
5. **Régua DoR de spec**: Completude 30 / Testabilidade 25 / Clareza 20 / Escopo 15 /
   Casos-limite 10, **corte ≥ 80** — os pesos são a rubrica da reversa, colada acima 🟢.
   Verificação executável por `scripts/check-specs.sh` 🟡 PLANEJADO (nasce neste ciclo).
6. **Absorção sem instalação (opção B)**: os conceitos acima — taxonomia com selos,
   `[DÚVIDA]`, rubrica DoR, premortem de risco (do `reversa-challenger`) — entram por
   **cópia de conceito com atribuição** (`sandeco/reversa`, MIT). Nenhum agente, hook ou
   arquivo de entrada do framework é instalado.

## Alternativas consideradas — descartadas com número

- **Opção A — instalar o framework reversa.** Descartada: a instalação grava
  `CLAUDE.md`/`AGENTS.md` (`lib/installer/writer.js:91` 🟢) e traria **72 agentes** para
  usar **4 conceitos** (selos, dúvida, rubrica, premortem) — um segundo método inteiro
  colidindo com o Maestro instalado, contra o princípio VII do método (YAGNI) e criando
  risco direto ao P1.
- **Nenhuma taxonomia além do template do Maestro.** Descartada: a barra de profundidade
  do corpus é a spec 001 do ECS, que carrega **36** menções `RF-` com fonte por requisito
  em 10 seções (`grep` acima) — sem tipos e numeração declarados, esse volume vira prosa
  não verificável, e o portão de DoR não tem o que medir.
- **Numeração global única (RF-001…RF-999 do produto inteiro).** Descartada: 8 módulos em
  12 ciclos gerariam renumeração em cascata a cada spec inserida; a numeração por spec
  (reinício por documento) é a que o ECS validou com 36 requisitos num módulo só, sem
  colisão entre specs.

## Consequências

- (+) Todo construtor de spec escreve na mesma forma; o portão de DoR tem régua numérica
  com pesos de origem pública e atribuída.
- (+) Zero arquivos do framework externo no repositório: a superfície instalável continua
  sendo só a do Maestro.
- (−) **Conceito absorvido não recebe atualização**: quando a reversa evoluir a rubrica,
  nada aqui acompanha — a cópia congela em 2026-09. A mitigação é a atribuição explícita,
  que ao menos diz onde olhar.
- (−) A régua ≥ 80 é **auto-atribuída por agente** até o portão executável existir
  (`check-specs.sh` 🟡) — entre a escrita e o portão, o número da rubrica é opinião, e a
  regra R1 obriga a dizer isso.

## O que este ADR NÃO decide

- O conteúdo dos módulos M1–M8 e seus épicos — `docs/produto/modulos.md` e as specs.
- O escopo do domínio (o que entra e o que fica fora da v1) — ADR 0005.
- A forma do `plan.md` e do `tasks.md` — já governada pelo método (Constitution Check,
  cauda TAIL) e detalhada no roadmap.
- Se e quando instalar qualquer outra ferramenta da reversa — entrada futura é decisão
  nova, por ADR.

## Registro

- `docs/produto/modulos.md` — o mapa M1–M8 que esta taxonomia estrutura
- `specs/001-fundacao-e-planejamento/` — o primeiro ciclo que a usa
- `scratchpad/reversa` (clone de leitura de `sandeco/reversa`, MIT License, © 2026
  Sandeco) — origem dos conceitos absorvidos; nada dele foi instalado
- `/home/user/ECS/specs/001-catalogo-itens/spec.md` — a barra de profundidade
