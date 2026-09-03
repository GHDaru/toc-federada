# Plan 001 — Fundação e planejamento (ciclo documental)

> Siglas: TOC — Teoria das Restrições · APH — Aplicação ↔ Harness · ADR — Architecture
> Decision Record · DoD — Definition of Done · DoR — Definition of Ready · TDD —
> Test-Driven Development · DDD — Domain-Driven Design · YAGNI — You Aren't Gonna Need It

- **Spec**: `spec.md` · **Raia**: plena · **Data**: 2026-09-03

## Constitution Check (governance/principles.md)

| Princípio | Conformidade |
|---|---|
| I. Spec-driven | ✅ Esta especificação nasce da intenção do Product Steward e o plano só a executa. Ressalva honesta, a mesma da irmã no seu ciclo 001: spec e entrega nascem no mesmo esforço — o portão humano ainda não aprovou a spec, e é isso que `TAIL:gate` aguarda. |
| II. Human-governed orchestration | ✅ Um humano rege: as decisões estruturais são do Product Steward, registradas em ADR; os construtores redigem por lote, cada um só nos seus caminhos. A verificação independente (`TAIL:review` e o gauntlet de críticos às cegas) fica com quem não construiu, em contexto fresco. |
| III. Reversibility / risk gates | ✅ Risco de classe **escrita** em repositório novo, sem histórico a perder: tudo reversível por `git revert`. Nenhuma ação externa (P1), nenhum dado de produção, nenhuma migração. Regra R3 aplicada: nomes de arquivo e cortes editoriais são do agente; o que toca inegociável (alcance do P2, base sintética) está em ADR. |
| IV. Test-first / verifiable DoD | ✅ Não há código, logo não há teste unitário — a função de aptidão aqui é a DoD executável da spec (13 verificações com comando e valor esperado) mais os três portões novos. `TAIL:mutation` se aplica de verdade: portão criado neste ciclo é sabotado de propósito e visto recusando. |
| V. Context economy / boundary | ✅ Corte por fronteira de lote: identidade/governança, produto/roadmap, ADRs, specs de módulo, portões, site — construtores paralelos sem sobreposição de caminho, amarrados por um brief único. Documentação primeiro mantém cada ciclo dentro de uma leitura. |
| VI. Living artifacts | ✅ Todo artefato tem consumidor com função forçante: `CLAUDE.md` é lido por todo agente; a constituição alimenta o Constitution Check; os ADRs são imutáveis e indexados por script; as specs alimentam o gerador do site (cabeçalhos verbatim); os portões consomem tudo. O brief de síntese **não** entra no repositório — é partitura de construção, sem consumidor durável. |
| VII. Light governance / YAGNI | ✅ Sete princípios, oito ADRs, três portões novos — cada um com defeito real que o justifica (as regras R1–R5 já pagas pela irmã). Descartados por YAGNI: instalar o framework reversa (ADR 0004, colidiria com o Maestro), suíte de conformidade APH local (não há URL ainda), documento de arquitetura (não há código). |
| VIII. Intelligible communication | ✅ Todo documento deste lote abre siglário ou expande a sigla na primeira ocorrência; o glossário do método cobre as siglas do método. A verificação é de revisor (`TAIL:review`), não de grep — a lição da irmã é que esta linha é a mais fácil de marcar ✅ em falso, então o revisor confere por amostragem dirigida. |

### Project Constitution Check (governance/constitution.md — ADR 0001)

| Princípio | Conformidade |
|---|---|
| P1. Fronteira de escrita | ✅ Só este repositório é escrito. `maestro`, `protocolos`, `ghdaru`, `gestaodeprioridades` e `tocbuilderv3` foram **lidos** (com `arquivo:linha` nas Fontes da spec). Lacuna externa encontrada vira `mensagens/NNN-...`, e a pasta com sua convenção nasce neste ciclo. |
| P2. Federação por contrato (APH) | ✅ Nada implementado neste ciclo; o ADR 0003 fixa o contrato (Nível 2, `mode: embedded`, lado aplicação) e — lição da irmã — **declara o alcance do P2 no próprio texto**, citando o princípio por nome. A constituição nasce com o alcance escrito, sem precisar de emenda. |
| P3. Domínio puro (DDD + hexagonal) | ✅ Declarado (ADR 0002, P3); sem código, nada a violar. O `import-linter` entra no primeiro ciclo com código (003+). As regras TOC como domínio puro já estão exigidas nas specs de M2–M5. |
| P4. TDD | ✅ Não aplicável por ausência de código de produção — e é por isso que a implementação só começa no ciclo 004, quando o teste puder vir primeiro de verdade. A linhagem sem testes é o contraexemplo registrado na visão. |
| P5. Observabilidade de nascença | ✅ Declarada (ADR 0002) e amarrada no roadmap: OpenTelemetry sobe no ciclo 003 (esqueleto federado), antes de qualquer funcionalidade de produto. |
| P6. Jornada viva com prova visual | ✅ Não aplicável: não há interface neste ciclo. É a entrega central do ciclo 002, já declarada no roadmap — e toda captura futura obedece à base sintética (ADR 0006). |
| P7. Segredo nunca no cliente | ✅ Nenhum segredo escrito, lido ou versionado. O defeito que fundamenta o princípio está citado com `arquivo:linha` (F-01 da spec) e a consequência arquitetural é o ADR 0007. |

**Sem violações.** Duas "não se aplica" (P4, P6) são consequência do escopo declarado, não
dispensa: voltam obrigatórias nos ciclos 002 (P6) e 004 (P4).

## Artefatos deste ciclo (declare todos os cinco — silêncio não é decisão)

| Artefato | Declaração | Por quê |
|---|---|---|
| `research.md` | `ART:research=no` | Não há incógnita técnica a resolver por experimento: norma APH, guia da federação, linhagem e corpus da irmã existem e foram lidos direto da fonte, com `arquivo:linha` nas Fontes da spec. |
| `data-model.md` | `ART:data-model=no` | Ciclo sem código. O modelo de domínio de cada módulo vive na seção "Entidades e modelo de domínio" da spec do módulo (formato do brief §7); um `data-model.md` do ciclo 001 duplicaria essa função (Princípio VI). |
| `contracts/` | `ART:contracts=no` | Nenhuma interface é definida aqui. Os contratos APH são **externos** e imutáveis para nós — vivem em `GHDaru/protocolos`; os contratos próprios (`toc.*`) nascem no ciclo 006 com spec própria. |
| `checklist.md` | `ART:checklist=no` | Os critérios de aceite da spec já são executáveis (13 linhas com comando e valor esperado); uma lista adicional seria a mesma função servida duas vezes (Princípio VI). |
| `ux-design.md` | `ART:ux-design=no` | Nenhuma tela é tocada. É o artefato central do ciclo 002, onde deixa de ser opcional. |

## Como

1. **Ler as fontes** antes de escrever qualquer coisa: linhagem `tocbuilderv3` (domínio e
   defeitos), norma APH (nível, modo, introspecção), corpus da irmã (formato e regras
   pagas), profundidade do ECS e gerador do site — leitores dedicados, saída com
   `arquivo:linha`.
2. **Sintetizar o brief** que amarra os construtores: identidade, taxonomia (vira ADR
   0004), módulos, roadmap, formatos verbatim, regras R1/VIII/privacidade. O brief é
   partitura, não artefato do repositório.
3. **Construir em lotes paralelos, sem sobreposição de caminho** (Princípio V):
   identidade e governança (`CLAUDE.md`, constituição, `mensagens/`, licenças, este
   ciclo) · produto (`docs/produto/visao.md`, `modulos.md`, `docs/roadmap.md`) · ADRs
   0001–0008 + índices · specs 002–012 · portões (`check-caminhos.sh`,
   `check-adrs-sucessao.sh`, `check-specs.sh`) · site (`tools/product-site/` +
   `docs/product-site/`) · `CHANGELOG.md`.
4. **Rodar os portões** — os do método e os três novos — e colar as saídas no
   `qa-report.md` com o tamanho do que cada um examinou (R2).
5. **Sabotar cada portão novo** de propósito e vê-lo recusar (`TAIL:mutation`) — a suíte
   não pode ser leniente.
6. **Gauntlet**: críticos em contexto fresco comparam às cegas contra as três barras
   (corpus da irmã, spec 001 do ECS, product-site do ECS); perder uma comparação gera
   retrabalho dirigido pela maior lacuna nomeada.
7. **Gate humano**: o Product Steward aprova spec e corpus, responde os `[DÚVIDA]` do
   Clarify e autoriza o fechamento.

## Riscos e portões

| Risco | Ligado a | Mitigação |
|---|---|---|
| GATE-embarque — planejar federação que a fundação ainda não consegue receber | L-01 | O ciclo 003 é raia infra com a aptidão "a junta fecha contra a ghdaru real"; nada de produto antes dela. |
| GATE-autodeclaracao — declarar Nível 2 sem suíte executável do lado aplicação | L-02 | Toda declaração de conformidade diz o lado e a maturidade (P2); matriz de aderência auditável no ciclo 012. |
| GATE-dominio-sem-referencia — especificar ARF/AT/S&T sem implementação de referência | L-03 | Requisitos nascem 🟡 com fonte na literatura TOC e nas skills de domínio; validação nas jornadas dos ciclos 008–010. |
| GATE-vazamento — dado real da irmã escorregar para cá | RNF-03 | DoD linha 11 (grep = 0) + revisão independente com esta instrução explícita. |

## Verificação (DoD)

A tabela executável completa está na spec (§ Critérios de aceite, 13 linhas). Resumo do
que fecha o ciclo:

| Comando | Saída esperada |
|---|---|
| `scripts/check-install.sh` | código 0 (já observado em 2026-09-03: `✓ method installed and coherent: layers present, AI instructed, every skill visible.`) |
| `grep -c '^### P[1-7]\.' docs/governance/constitution.md` | `7` (executado em 2026-09-03: saiu `7`) |
| `ls docs/adr/000[1-8]-*.md \| wc -l` | `8` |
| `ls -d specs/0*/ \| wc -l` | `12` |
| `scripts/check-caminhos.sh` · `scripts/check-adrs-sucessao.sh` · `scripts/check-specs.sh` | código 0 cada um, dizendo quanto examinou (R2) |
| `scripts/check-conformance.sh 001` | código 0 |
