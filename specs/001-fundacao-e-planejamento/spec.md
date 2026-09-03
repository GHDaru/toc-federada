# Spec 001 — Fundação e planejamento (ciclo documental)

> Siglas: TOC — Teoria das Restrições · APH — Aplicação ↔ Harness · ADR — Architecture
> Decision Record (Registro de Decisão Arquitetural) · RF/RI/RNF/RN/INT — requisito
> funcional / de interface / não funcional / regra de negócio / integração · UDE —
> Undesirable Effect (Efeito Indesejável) · DoD — Definition of Done (Definição de
> Pronto) · DoR — Definition of Ready (Definição de Prontidão) · EARS — Easy Approach to
> Requirements Syntax · TDD — Test-Driven Development · DDD — Domain-Driven Design ·
> IA — inteligência artificial

- **Status**: Rascunho (aprovação: gate humano do ciclo 001)
- **Raia**: plena
- **Data**: 2026-09-03
- **Origem**: decisão do Product Steward ao abrir o projeto: fundar a sucessora da
  linhagem TOC-Builder já sob o método Maestro completo, com todo o planejamento escrito
  **antes** de qualquer código.

## O quê e por quê

O repositório nasceu com o método Maestro instalado pelo instalador oficial
(`scripts/check-install.sh` sai com código 0 — F-06) e **nada mais**. Falta tudo o que o
método não traz: o que este produto é, sob quais regras se constrói, em que ordem, e como
alguém de fora acompanha.

A linhagem que este projeto sucede — quatro gerações de protótipo frontend e cinco
repositórios natimortos — falhou sempre do mesmo jeito: código antes de decisão, decisão
em nenhum lugar, segredo no cliente, zero testes. O valor deste ciclo é **tornar essa
falha impossível de repetir por acidente**: transformar as decisões faladas em registro
imutável (8 ADRs), o produto em specs verificáveis (12 pastas de spec), a sequência em
roadmap com portões, e a rastreabilidade em site gerado por script — antes da primeira
linha de código de produção, que só nasce no ciclo 004.

Este ciclo é documental: a spec descreve **o corpus, o site e os portões** — não telas nem
serviço. Por isso o formato de spec de módulo (brief §7) é adaptado: sem seções de
entidades de domínio, telas ou integrações, que aqui não existem.

## O que entra como dado

- O método Maestro **instalado e verificado** (F-06) — não se reinstala nem se edita.
- A herança da irmã `gestaodeprioridades`: constituição P1–P7 e regras R1–R5 de
  retrospectiva (F-05), incorporadas por decisão (ADR 0001) e não por cópia cega.
- A norma APH: Nível 2 (Operador) como alvo (F-02), `mode: embedded` (F-03), identidade
  por introspecção (F-04).
- A linhagem TOC-Builder como fonte de domínio e como catálogo de defeitos (F-01).

## Requisitos funcionais

### Identidade e governança

RF-01: O SISTEMA DEVE apresentar no `CLAUDE.md`, antes do bloco instalado do método, a
identidade do produto, a ordem de leitura das duas constituições, o resumo P1–P7, as
regras R1–R5 herdadas, a stack e a nota de base sintética — preservando intacto o bloco
`## Method: Maestro` gerado pelo instalador. [F-05, F-06] 🟡

RF-02: O SISTEMA DEVE ter constituição de projeto versionada (v1.0.0) com exatamente sete
princípios `P1.`–`P7.`, marcando como INEGOCIÁVEL a fronteira de escrita, a federação por
contrato e o segredo fora do cliente, e declarando o **alcance** do P2 no próprio texto.
[F-02, F-03, F-04] 🟡

RF-03: O SISTEMA DEVE ter a convenção de mensagens externas (`mensagens/README.md`) com o
formato `NNN-para-<repo>-<assunto>.md`, para que o P1 tenha caminho de saída que não seja
o chat. 🟡

RF-04: O SISTEMA DEVE ter licença MIT (copyright 2026 GHDaru) e avisos de terceiros
cobrindo o método Maestro, a taxonomia absorvida de `sandeco/reversa` e o gerador do site
de `GHDaru/daruskills`. 🟡

### Registro de decisões

RF-05: Toda decisão estrutural desta fundação DEVE existir como ADR — 0001 a 0008 — com
Status/Data/Ciclo/Decisor, campo **"Princípios tocados"** (com `nenhum` por extenso quando
for o caso), alternativas descartadas com número executado (R1), ao menos uma
consequência negativa e a seção "O que este ADR NÃO decide". 🟡

RF-06: QUANDO um ADR for aceito, O SISTEMA DEVE tê-lo no índice `docs/adr/README.md` e no
índice `docs/records/decisoes.jsonl` (via `scripts/record-decision.sh`, nunca à mão). 🟡

### Produto e planejamento

RF-07: O SISTEMA DEVE registrar em `docs/produto/visao.md` o que o produto é, extraído da
linhagem com evidência por `arquivo:linha`, incluindo os defeitos que os princípios
existem para impedir. [F-01] 🟡

RF-08: O SISTEMA DEVE mapear os oito módulos M1–M8 em `docs/produto/modulos.md`, cada um
com bounded context e origem (linhagem 🟢, planejado 🟡, lacuna 🔴). 🟡

RF-09: O SISTEMA DEVE declarar em `docs/roadmap.md` os ciclos 001–012, com raia, entrega,
portões por ciclo e a seção "O que o ciclo NNN não pode começar sem" — nenhum código de
produção antes do ciclo 004. 🟡

RF-10: O SISTEMA DEVE ter as doze pastas `specs/001` a `specs/012`, cada uma com
`spec.md`, `plan.md`, `tasks.md` e `qa-report.md`; as specs de módulo seguem o formato do
brief §7 (taxonomia Módulo⊃Épico⊃Feature⊃Story, famílias RF/RI/RNF/RN/INT/F/L, EARS,
selos, Clarify ≤ 5) e todo plano carrega **duas** tabelas de Constitution Check. 🟡

### Portões e site

RF-11: O SISTEMA DEVE ter os portões deste projeto executáveis e não lenientes:
`scripts/check-caminhos.sh` (regra R4 — caminho citado entre crases existe),
`scripts/check-adrs-sucessao.sh` (regra R5 — sucessão declarada nos dois ADRs + índices) e
`scripts/check-specs.sh` (régua DoR ≥ 80). 🟡

RF-12: O SISTEMA DEVE gerar `docs/product-site/` exclusivamente pelo gerador vendorizado
em `tools/product-site/` (ADR 0008) — nunca HTML escrito à mão — com navegação por
módulos, rastreabilidade e roadmap. 🟡

## Requisitos não funcionais

RNF-01: Toda a documentação do projeto DEVE estar em português; a superfície instalável do
Maestro permanece em inglês e intocada. 🟡

RNF-02: Em cada documento, a primeira ocorrência de cada sigla DEVE vir por extenso
(Princípio VIII do método). 🟡

RNF-03: Nenhum arquivo DEVE conter dado real de pessoa; toda persona e toda base de
exemplo é sintética (ADR 0006), o que mantém o repositório apto a ser aberto. 🟡

RNF-04: Todo caminho relativo citado DEVE resolver — verificado por
`scripts/check-links.sh` **e** `scripts/check-caminhos.sh` (a segunda cobre o que a
primeira apaga: caminhos entre crases). 🟡

RNF-05: Todo número afirmado em documento DEVE ter sido executado, com a saída colada
(regra R1). 🟡

## Fora de escopo

- Qualquer código de produção — interface, serviço, banco, infraestrutura (ciclos 003+).
- Protótipo de telas, `ux-design.md` e jornadas com captura (ciclo 002).
- Embarque real na fundação, manifesto servido, introspecção chamada (ciclo 003).
- Tambor-Pulmão-Corda (DBR), gestão de pulmões e contabilidade de ganho — fora da v1
  inteira (ADR 0005).
- Corrigir qualquer coisa em `maestro`, `protocolos`, `ghdaru`, `gestaodeprioridades` ou
  na linhagem (P1): lacuna encontrada lá fora vira `mensagens/NNN-...`, não commit.

## Critérios de aceite (DoD)

| # | Critério | Verificação executável |
|---|---|---|
| 1 | Constituição com os sete princípios | `grep -c '^### P[1-7]\.' docs/governance/constitution.md` → `7` |
| 2 | CLAUDE.md preserva o bloco do instalador | `grep -c '^## Method: Maestro' CLAUDE.md` → `1` |
| 3 | Oito ADRs presentes | `ls docs/adr/000[1-8]-*.md \| wc -l` → `8` |
| 4 | Todo ADR aceito indexado no jsonl | `scripts/check-adrs-sucessao.sh` → código 0 |
| 5 | Doze pastas de spec, quatro arquivos cada | `ls -d specs/0*/ \| wc -l` → `12` e `ls specs/0*/spec.md specs/0*/plan.md specs/0*/tasks.md specs/0*/qa-report.md \| wc -l` → `48` |
| 6 | Roadmap declara os doze ciclos | `grep -c '^| \*\*0[0-9][0-9]\*\*' docs/roadmap.md` → `12` |
| 7 | Régua DoR das specs ≥ 80 | `scripts/check-specs.sh` → código 0 |
| 8 | Caminhos entre crases resolvem | `scripts/check-caminhos.sh` → código 0, dizendo **quantos** conferiu (R2) |
| 9 | Links relativos resolvem | `scripts/check-links.sh` → código 0 |
| 10 | Site gerado por script, não à mão | `test -f docs/product-site/index.html && test -f tools/product-site/generate.py` → código 0 |
| 11 | Nenhum vazamento da base real da irmã | `grep -rn "gestaodeprioridades/protot[i]po" --include='*.md' . \| wc -l` → `0` (a classe `[i]` impede o comando de contar a si mesmo) |
| 12 | Método segue instalado e coerente | `scripts/check-install.sh` → código 0 |
| 13 | Conformidade do ciclo | `scripts/check-conformance.sh 001` → código 0 |

## Fontes

F-01: `/home/user/tocbuilderv3/services/geminiService.ts:16` — `const ai = new
GoogleGenAI({ apiKey: process.env.API_KEY });` — a violação canônica de segredo no
cliente; fundamenta P7 e o ADR 0007. 🟢

F-02: `/home/user/protocolos/padrao/padrao-aph.md:53` — `| **Nível 2** | Operador | age
sobre a aplicação com governança | ...` — o nível-alvo da federação (ADR 0003). 🟢

F-03: `/home/user/protocolos/padrao/anexo-b-federacao.md:107` — o manifesto declara
**modo de integração** `internal`/`embedded`/`headless`, sem números — fundamenta
`mode: embedded`. 🟢

F-04: `/home/user/protocolos/padrao/anexo-b-federacao.md:111` — `endpoints.validate_token`
→ **`endpoints.introspect`** — fundamenta identidade por introspecção, nunca validação
booleana. 🟢

F-05: `/home/user/gestaodeprioridades/CLAUDE.md:48` (R1) a `:84` (R5) — as cinco regras de
retrospectiva herdadas pelo ADR 0001. 🟢

F-06: saída de `scripts/check-install.sh` neste repositório, 2026-09-03 — `✓ method
installed and coherent: layers present, AI instructed, every skill visible.` — código de
saída 0. 🟢

## Lacunas e assunções

L-01: A fundação ainda não embarcou nenhuma aplicação federada de ponta a ponta (a irmã
relatou bloqueio nos schemas de manifesto em `mensagens/005` de lá) — **assunção**: o
embarque real acontece no ciclo 003 contra a ghdaru real, e o roadmap o trata como a
aptidão mais importante ("a junta fecha") — risco **médio**.

L-02: O lado aplicação do APH Nível 2 não tem suíte de conformidade executável (a norma o
declara: `padrao-aph.md:17`) — **assunção**: nossa conformidade será autodeclaração
auditável por matriz de aderência (ciclo 012), dita como tal — risco **médio**.

L-03: ARF, AT e S&T nunca foram entregues em nenhuma geração da linhagem: não há
implementação de referência a extrair, só as skills de domínio e a literatura TOC —
**assunção**: as specs de M4/M5 nascem 🟡 PLANEJADO com regras de negócio derivadas da
literatura, validadas pela Facilitadora TOC sintética nas jornadas — risco **médio**.

## Clarify

- [DÚVIDA] O nome público do produto para o site é "TOC Federada" (nome do repositório) ou
  outro nome de marca? (bloqueia o cabeçalho do site, não bloqueia o corpus)
- [DÚVIDA] O repositório abre ao público já no fechamento deste ciclo — o ADR 0006
  garante a condição — ou o Product Steward prefere abrir só após o ciclo 003?
- [DÚVIDA] O `app_id: toc` e o namespace `toc.*` estão reservados na fundação, ou há risco
  de colisão a resolver antes do ciclo 003?
