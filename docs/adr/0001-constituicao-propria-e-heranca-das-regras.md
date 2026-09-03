# ADR 0001 — Constituição própria do projeto (P1–P7), ao lado da do método, e herança das regras R1–R5 da irmã

- **Status**: Aceita
- **Data**: 2026-09-03 · **Ciclo**: 001
- **Decisor**: Product Steward (matéria constitutiva — fora do alcance da R3)
- **Sucede**: nenhum
- **Princípios tocados**: **todos (P1–P7)** — este ADR (Architecture Decision Record,
  registro de decisão arquitetural) é constitutivo: os sete princípios do projeto nascem
  aqui. Ele **não** emenda a constituição do método (Maestro, princípios I–VIII).

## Contexto

O método Maestro chega instalado com a sua própria constituição
(`docs/governance/principles.md`, princípios I–VIII). Ela governa **como se trabalha** —
especificação como fonte de verdade, portões humanos, prova em vez de alegação — e, por
desenho, não diz nada sobre **este produto**: não decide fronteira de escrita, não decide
federação, não decide domínio. Verificado, não presumido:

```text
$ grep -c '^### ' docs/governance/principles.md
8
$ grep -ci 'federa\|APH' docs/governance/principles.md
0
```

Oito princípios do método, **zero** menções a federação ou ao padrão APH (Aplicação ↔
Harness). O que é do produto precisa de casa própria.

A irmã `gestaodeprioridades` — primeira aplicação candidata à federação — já resolveu esse
mesmo problema e pagou para aprender o que dá errado:

```text
$ grep -c '^### P' /home/user/gestaodeprioridades/docs/governance/constitution.md
7
$ sed -n '8p' /home/user/gestaodeprioridades/docs/governance/constitution.md
> **Versão**: 1.1.0 · **Ratificada**: 2026-08-10 · **Emendas**: 2026-08-11 (ADR 0004 —
$ grep -c '^- \*\*R[1-5]' /home/user/gestaodeprioridades/CLAUDE.md
5
$ ls /home/user/gestaodeprioridades/docs/adr/*.md | grep -v README | wc -l
19
```

Sete princípios, já na versão 1.1.0 porque **duas emendas foram necessárias** (o alcance
do nível APH, ADR 0004 de lá; o alcance do P2, ADR 0016 de lá), cinco regras de
retrospectiva e dezenove ADRs de lições pagas em dois ciclos.

## Decisão

1. **Este projeto tem constituição própria**: `docs/governance/constitution.md`, versão
   1.0.0, ratificada em 2026-09-03, com os princípios **P1–P7** 🟢. Ela convive com a do
   método e declara a regra de precedência no próprio texto: em conflito aparente, vale a
   leitura que satisfaz as duas; não havendo, o Maestro prevalece e a divergência vira ADR.
2. **P1–P7 são herdados da constituição da irmã (versão 1.1.0), já com as emendas
   incorporadas ao texto de nascimento** — em particular, o alcance do P2 nasce declarado
   dentro do princípio, em vez de esperar a emenda que lá custou o ciclo do ADR 0011→0016.
   Adaptações desta aplicação: P1 amplia a lista de repositórios somente-leitura
   (linhagem TOC-Builder e a própria irmã); P2 aponta o ADR 0003 daqui; P7 cita a violação
   canônica da própria linhagem (`tocbuilderv3/services/geminiService.ts:16` 🟢 — ver
   ADR 0007).
3. **As cinco regras de retrospectiva R1–R5 da irmã são herdadas prontas**, como regras
   operacionais no `CLAUDE.md` deste repositório, com a origem declarada (irmã, ciclos
   001 e 002). Herdá-las é o motivo de ter uma irmã mais velha; reaprendê-las seria pagar
   duas vezes o mesmo achado.
4. **Todo ADR deste projeto declara o campo "Princípios tocados"**, com `nenhum` escrito
   por extenso quando for o caso — a forma executável da quarta condição da R3, nascida do
   defeito do ADR 0011 da irmã (decidiu matéria de princípio inegociável sem citá-lo).

## Alternativas consideradas — descartadas com número

- **Usar só a constituição do método.** Descartada: o `grep` acima devolve **0** menções a
  federação ou APH nos **8** princípios do Maestro — a matéria do produto simplesmente não
  tem onde morar lá, e escrevê-la lá corromperia o método para todo repositório que o
  instala (a superfície é reinstalável pelo instalador oficial e conferida por
  `scripts/check-install.sh`).
- **Escrever P1–P7 do zero, sem herdar.** Descartada: a irmã acumulou **19 ADRs** e **5
  regras de retrospectiva** em dois ciclos, incluindo **2 emendas constitucionais**
  (versão 1.0.0 → 1.1.0) que existem porque a primeira redação estava errada. Partir do
  zero é assinar para redescobrir esses mesmos defeitos — o ciclo 001 dela registrou *"o
  mesmo defeito em cinco disfarces"* (`gestaodeprioridades/CLAUDE.md`, regra R1 🟢).
- **Fundir tudo numa constituição só.** Descartada: `docs/governance/principles.md` é
  superfície **instalável** do método, em inglês (ADR 0014 do método), sobrescrita a cada
  reinstalação — o que fosse fundido ali seria apagado pelo instalador. As duas
  constituições têm ciclos de vida distintos e donos distintos.

## Consequências

- (+) A matéria do produto tem casa própria, versionada e emendável por ADR, sem tocar a
  superfície instalável do método.
- (+) O alcance do P2 nasce declarado — a armadilha que custou à irmã uma emenda
  constitucional não é herdada.
- (−) **Duas constituições são duas leituras obrigatórias antes de qualquer trabalho**, e
  a ordem de leitura (método → projeto → modelo operacional) precisa ser mantida à mão no
  `CLAUDE.md` — não há portão que a verifique.
- (−) Regras herdadas prontas correm o risco de virar **letra morta**: quem não viveu o
  defeito que gerou a R4 pode obedecê-la sem entendê-la. A mitigação é cada regra carregar
  a história do defeito no próprio texto.

## O que este ADR NÃO decide

- O conteúdo técnico de cada princípio além da herança (stack é o ADR 0002; federação é o
  ADR 0003; escopo do domínio é o ADR 0005; base sintética é o ADR 0006).
- Emendas futuras à constituição — cada uma exige ADR próprio e incremento de versão.
- Os portões executáveis que verificam as regras herdadas (`check-caminhos`, DoR de spec)
  🟡 PLANEJADO — nascem com o ciclo que os usa.

## Registro

- `docs/governance/constitution.md` — a constituição criada, versão 1.0.0
- `docs/governance/principles.md` — a constituição do método, que esta não substitui
- `/home/user/gestaodeprioridades/docs/governance/constitution.md` — a origem da herança
  (versão 1.1.0)
- `CLAUDE.md` — o resumo operacional de P1–P7 e as regras R1–R5 herdadas
