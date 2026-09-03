# ADR 0007 — Inteligência artificial somente pela fundação: sem SDK de provedor no produto, chave nunca no cliente, prompts versionados no servidor

- **Status**: Aceita
- **Data**: 2026-09-03 · **Ciclo**: 001
- **Decisor**: Product Steward (toca dois princípios INEGOCIÁVEIS — quarta condição da R3)
- **Sucede**: nenhum
- **Princípios tocados**: **P2 (INEGOCIÁVEL)** — toda assistência passa pelo catálogo de
  ações governadas da fronteira APH (Aplicação ↔ Harness), nunca por um segundo caminho —
  e **P7 (INEGOCIÁVEL)** — a violação canônica que o P7 cita por nome é a que este ADR
  (Architecture Decision Record, registro de decisão arquitetural) aposenta. Nenhum dos
  dois é emendado.

## Contexto

A geração anterior desta aplicação — `tocbuilderv3`, a quarta da linhagem TOC-Builder —
fala com o provedor de modelo **diretamente do navegador**. Lido, não lembrado:

```text
$ sed -n '16p' tocbuilderv3/services/geminiService.ts
const ai = new GoogleGenAI({ apiKey: process.env.API_KEY });
$ sed -n '14,15p' tocbuilderv3/vite.config.ts
        'process.env.API_KEY': JSON.stringify(env.GEMINI_API_KEY),
        'process.env.GEMINI_API_KEY': JSON.stringify(env.GEMINI_API_KEY)
$ grep -n 'INITIAL_SYSTEM_PROMPTS' tocbuilderv3/constants.ts | head -1
341:export const INITIAL_SYSTEM_PROMPTS: SystemPrompt[] = [
$ wc -l tocbuilderv3/services/geminiService.ts tocbuilderv3/constants.ts
  184 tocbuilderv3/services/geminiService.ts
  450 tocbuilderv3/constants.ts
  634 total
```

Três defeitos encadeados 🟢: o SDK do provedor é inicializado no cliente
(`tocbuilderv3/services/geminiService.ts:16`); o `define` do Vite **injeta a chave da API
no bundle servido** (`tocbuilderv3/vite.config.ts:14`) — qualquer visitante que abra o
DevTools lê a credencial; e os prompts de sistema vivem em `constants.ts:341`, no mesmo
bundle — o usuário pode ler e, pior, a aplicação não pode evoluí-los sem redeployar o
cliente. São **634 linhas** de integração de IA (inteligência artificial) inteiras do
lado errado da fronteira.

Do outro lado, a norma APH já resolve o problema por contrato: o checklist do Nível 2
exige *"catálogo como única superfície"* e *"porta única de LLM com `usage`"*
(`protocolos/padrao/padrao-aph.md:194` 🟢) — e essa porta é da **fundação**, não da
aplicação.

## Decisão

1. **Nenhum SDK de provedor de modelo no produto** — nem no cliente, nem no serviço.
   Zero dependência `@google/genai`, `openai`, `anthropic` ou equivalente nos manifestos
   de dependência desta aplicação. Função de aptidão: um grep de CI sobre
   `package.json`/`pyproject.toml` 🟡 PLANEJADO (ciclo 003).
2. **Toda assistência de IA opera pela fundação, via catálogo de ações governadas**
   (`toc.*`, ADR 0003): a aplicação expõe ações e telas; quem conversa com o modelo é o
   harness. Sugerir Efeitos Indesejáveis (UDEs), validar formalmente uma UDE, analisar
   suficiência causal, gerar nuvem a partir de narrativa — tudo é ação de catálogo, e
   todo verbo mutador nasce `action_proposal` (P2).
3. **Chave e credencial só no servidor, por variável de ambiente** (P7). No cliente,
   nunca — nem "temporariamente", nem em protótipo que renderize dado real de tenant.
4. **Prompts versionados no servidor**: o conhecimento de domínio que hoje está em
   `constants.ts` do cliente (critérios de UDE, categorias de causa) migra para regra de
   domínio pura e testável (P3) e para prompts versionados no repositório, do lado do
   serviço — evoluíveis por pull request, invisíveis ao navegador.

## Alternativas consideradas — descartadas com número

- **Manter o padrão do v3 (SDK e chave no cliente).** Descartada: a chave está no bundle
  público (`vite.config.ts:14` 🟢, colado acima) — não é risco teórico, é credencial
  servida a qualquer visitante. É a violação canônica que o P7 da constituição cita por
  nome.
- **SDK de provedor no nosso servidor (proxy próprio de IA).** Descartada: criaria uma
  **segunda porta de LLM** fora da fundação, contra o item *"porta única de LLM com
  `usage`"* do checklist Nível 2 (`padrao-aph.md:194` 🟢), duplicando billing,
  observabilidade e política de autorização — e reescrevendo, do nosso lado, as **184
  linhas** de `geminiService.ts` que a fundação já torna desnecessárias.
- **Portar as 634 linhas do v3 para trás de uma rota nossa.** Descartada: mover a
  violação de lugar não a remove — os prompts continuariam acoplados a um provedor
  específico e a autorização continuaria dentro do modelo, contra o P2 (*"autorização
  fora do modelo de linguagem"*). O v3 é fonte de **requisito** (o que a assistência deve
  fazer), nunca de **código**.

## Consequências

- (+) Sem segredo no cliente por construção — não há o que vazar.
- (+) Troca de provedor de modelo, billing e limites viram problema da fundação,
  resolvido uma vez para todas as aplicações federadas.
- (−) **Acoplamento duro à disponibilidade da fundação**: sem harness, a assistência de
  IA desta aplicação **não existe** — não há modo degradado com chave própria, e este ADR
  proíbe criá-lo. As ferramentas continuam utilizáveis manualmente; a assistência, não.
- (−) Latência e capacidade passam por um intermediário que não controlamos; o traço
  OpenTelemetry (P5) precisa atravessar a fronteira para o defeito ser localizável — e
  isso vira requisito de integração (INT-NN) das specs do M7, não um desejo.

## O que este ADR NÃO decide

- Quais ações de assistência existem e com que risco/`input_schema` — catálogo `toc.*`,
  spec do ciclo 006.
- O conteúdo dos prompts de domínio — specs de M2–M4, com os critérios TOC (Teoria das
  Restrições) como regra de domínio testável antes de qualquer prompt.
- O modelo, provedor ou preço usados pela fundação — decisão do harness, fora da nossa
  fronteira de escrita (P1).

## Registro

- `docs/governance/constitution.md` — P2 e P7, que esta decisão implementa
- `tocbuilderv3/services/geminiService.ts`, `tocbuilderv3/vite.config.ts`,
  `tocbuilderv3/constants.ts` — a violação canônica, citada por linha (leitura)
- `protocolos/padrao/padrao-aph.md` — o checklist do Nível 2, linha 194
- `docs/produto/modulos.md` — M7, onde o catálogo vive
