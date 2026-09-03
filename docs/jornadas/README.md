# Jornadas — por que esta pasta está vazia, e o que vai morar aqui

> Siglas: TOC — Teoria das Restrições · ARA — Árvore da Realidade Atual · NC — Nuvem de
> Conflito · ARF — Árvore da Realidade Futura · APR — Árvore de Pré-Requisitos · AT —
> Árvore de Transição · S&T — Árvore de Estratégia & Táticas · UDE — Undesirable Effect
> (Efeito Indesejável) · OI — Objetivo Intermediário · P6 — princípio "Jornada viva" da
> constituição do projeto · ADR — Architecture Decision Record

- **Status**: convenção do ciclo 001 · **Data**: 2026-09-03

## Por que não há jornada ainda

A Iron Law da skill `living-journey` é curta: **jornada sem captura de build real é
ficção**. Um documento de jornada só existe quando as suas capturas foram geradas do
build, por script versionado, com avaliação heurística datada — tudo no mesmo pull
request (P6). Hoje não existe build nenhum: o ciclo 001 é documental, e nenhuma linha de
código de produção nasce antes do ciclo 003
([`../roadmap.md`](../roadmap.md)).

Escrever agora "a Facilitadora abre o canvas e vê a árvore" seria repetir o vício da
linhagem TOC-Builder, que "funcionava" em descrição e nunca se soube exatamente o quê:
prosa sobre telas que ninguém capturou. **As jornadas nascem nos ciclos de
implementação**, cada uma no ciclo em que a sua ferramenta passa a existir de verdade —
e é por isso que esta pasta abre com um README e nenhuma jornada.

## Como uma jornada nasce (e o que nunca entra)

1. A ferramenta é implementada no seu ciclo, com build real.
2. Um script versionado gera as capturas desse build em `capturas/` — nunca imagem colada
   à mão, e rodar o script de novo regenera as imagens byte-idênticas.
3. O documento `NNN-<slug>.md` narra a jornada sobre essas capturas, com avaliação
   heurística **datada** e o limite declarado (quem avaliou, em que contexto).
4. Toda captura é citada por exatamente uma jornada — captura órfã é defeito.

**Nunca entra**: dado real de pessoa. Toda jornada usa a base sintética (ADR 0006 —
personas fictícias como "Facilitadora TOC" e a "Instituição Horizonte"); é essa regra que
mantém o repositório apto a ser aberto.

**Nota sobre o ciclo 002**: o protótipo descartável
([`../../specs/002-prototipo-de-interfaces/spec.md`](../../specs/002-prototipo-de-interfaces/spec.md))
também tem build — descartável, mas real — e produz **versões de protótipo** das
jornadas, com capturas geradas por script e declaradas como tal. Elas validam a forma das
telas; **não** são a jornada viva definitiva, que só existe quando a captura vem do build
de produção da ferramenta, no ciclo dela. Este README marca o estágio de cada uma.

## As jornadas planejadas

| J | Jornada | Nasce no ciclo | Estágio |
|---|---|---|---|
| J-01 | Chegada e embarque | 003 | 🟡 planejada |
| J-02 | Primeiro projeto e ARA | 004 (abre) · 005 (consolida) | 🟡 planejada |
| J-03 | Nuvem de Conflito | 007 | 🟡 planejada |
| J-04 | Da injeção ao plano (ARF → APR → AT) | 008 | 🟡 planejada |
| J-05 | Focalização | 009 | 🟡 planejada |
| J-06 | Estratégia & Táticas | 010 | 🟡 planejada |

O que cada uma vai mostrar:

- **J-01 — Chegada e embarque.** Uma pessoa entra na plataforma hospedeira, clica na
  aplicação TOC e a vê embarcada sob a identidade dela — modo só-conteúdo, tema do
  inquilino com *fallback*, projetos sintéticos listados. É a prova visual de que "a
  junta fecha contra a `ghdaru` real", capturada do build embarcado.
- **J-02 — Primeiro projeto e ARA.** A Facilitadora TOC cria o primeiro projeto, monta
  nós e arestas causais no canvas e alterna para a vista tabular; no ciclo 005 a mesma
  jornada ganha as UDEs da "Instituição Horizonte" com validação formal e a análise de
  suficiência até a causa raiz.
- **J-03 — Nuvem de Conflito.** O dilema sintético narrado vira as cinco entidades e as
  sete premissas, e a Facilitadora registra a injeção ligada à premissa que invalida.
  Inclui a geração assistida entrando como proposta governada — recusar deixa o projeto
  intacto.
- **J-04 — Da injeção ao plano.** A injeção da NC semeia a ARF; a ARF revela obstáculos;
  a APR os sequencia em OIs; a AT desce ao passo executável. É o encadeamento que
  nenhuma das quatro gerações da linhagem modelou, mostrado elo a elo.
- **J-05 — Focalização.** Uma análise sintética atravessa os cinco passos — identificar →
  explorar → subordinar → elevar → recomeçar — com captura por passo e o estado herdado
  de um passo ao seguinte; "recomeçar" reabre sem apagar histórico.
- **J-06 — Estratégia & Táticas.** Uma S&T sintética de três níveis (1, 1.1, 1.1.2), com
  as três premissas lógicas por nó e o status de acompanhamento — a ferramenta que
  regrediu na linhagem, de volta e provada por captura.

A lista cresce por decisão, não por acúmulo: jornada nova entra com ciclo que a
implemente e captura que a prove (a documentação embutida do ciclo 011 e as jornadas
consolidadas do 012 são as candidatas já conhecidas —
[`../roadmap.md`](../roadmap.md)).
