/**
 * Verbete de documentação embutida — Nuvem de Conflito (E8.4 da spec 011).
 *
 * Conteúdo versionado no repositório, nunca gerado em tempo de execução por modelo de
 * linguagem (RF-24, ADR 0007 — *Architecture Decision Record*).
 */
import type { Verbete } from "../tipos";

export const verbete: Verbete = {
  ferramenta: "nc",
  procedencia: ["specs/007-nuvem-de-conflito/spec.md", "docs/adr/0005-escopo-do-dominio-v1.md"],
  pt: {
    titulo: "Nuvem de Conflito",
    resposta: "Por que o problema não se resolve sozinho — e qual premissa quebrar.",
    secoes: [
      {
        ancora: "o-que-responde",
        titulo: "O que ela responde",
        paragrafos: [
          "A Nuvem de Conflito (NC) mostra que o impasse não é falta de vontade: é um conflito real entre duas ações que servem a duas necessidades legítimas do mesmo objetivo.",
          "Ela não busca acordo no meio do caminho. Busca a premissa errada que faz as duas parecerem incompatíveis — e a injeção que a evapora.",
        ],
      },
      {
        ancora: "as-cinco-entidades",
        titulo: "As cinco entidades e as sete arestas",
        paragrafos: [
          "A é o objetivo comum. B e C são as necessidades que o sustentam. D e D′ são as ações em conflito — D′ nega D, literalmente.",
          "As sete arestas nascem juntas e não se criam nem se destroem: A←B, A←C, B←D, C←D′, mais as três de tensão (D contra C, D′ contra B, D contra D′). A topologia é fixa por regra do domínio; o que muda é o texto delas.",
          "A, B e C são substantivos (estados desejados); D e D′ são verbos no infinitivo (ações).",
        ],
      },
      {
        ancora: "premissa-sustentada",
        titulo: "O que faz uma premissa ser sustentada",
        paragrafos: [
          "Cada aresta carrega ao menos uma premissa escrita: a crença que faz aquela seta parecer necessária. Uma aresta sem premissa não é um conflito examinado — é um conflito repetido.",
          "Uma premissa está sustentada quando alguém escreveu por que ela vale AQUI, neste contexto. Desafiar uma premissa exige justificativa: “discordo” não é exame.",
          "A premissa mais fértil costuma ser a da aresta D↯D′ — a que afirma que as duas ações disputam o mesmo recurso.",
        ],
      },
      {
        ancora: "injecao",
        titulo: "A injeção",
        paragrafos: [
          "Injeção é a mudança que faz a premissa deixar de valer. Ela nasce ligada a UMA premissa: injeção solta é palpite.",
          "Os estados são candidata, escolhida e descartada. Só a injeção escolhida semeia a Árvore da Realidade Futura — a cadeia só avança sobre material auditado.",
        ],
      },
    ],
    exemplo:
      "Instituição Horizonte: para se sustentar (A), ela precisa de receita nova (B) e de reputação acadêmica preservada (C). Abrir turmas em três cidades (D) traz receita; não abrir (D′) preserva a reputação. A premissa de D↯D′ — “o orçamento é indivisível dentro do exercício” — cai com a injeção do faseamento orçamentário condicionado a marco de receita.",
  },
  en: {
    titulo: "Conflict Cloud",
    resposta: "Why the problem will not resolve itself — and which assumption to break.",
    secoes: [
      {
        ancora: "o-que-responde",
        titulo: "What it answers",
        paragrafos: [
          "The Conflict Cloud shows that the deadlock is not a lack of goodwill: it is a real conflict between two actions serving two legitimate needs of the same objective.",
          "It does not look for a compromise halfway. It looks for the wrong assumption that makes the two look incompatible — and for the injection that evaporates it.",
        ],
      },
      {
        ancora: "as-cinco-entidades",
        titulo: "Five entities, seven edges",
        paragrafos: [
          "A is the common objective. B and C are the needs that support it. D and D′ are the conflicting actions — D′ literally negates D.",
          "The seven edges are born together and are never created or destroyed: A←B, A←C, B←D, C←D′, plus the three tension edges (D against C, D′ against B, D against D′). The topology is fixed by a domain rule; what changes is their wording.",
          "A, B and C are nouns (desired states); D and D′ are verbs in the infinitive (actions).",
        ],
      },
      {
        ancora: "premissa-sustentada",
        titulo: "What makes an assumption supported",
        paragrafos: [
          "Every edge carries at least one written assumption: the belief that makes that arrow look necessary. An edge with no assumption is not an examined conflict — it is a repeated one.",
          "An assumption is supported when someone wrote down why it holds HERE, in this context. Challenging one requires a rationale: “I disagree” is not an examination.",
          "The most fertile assumption is usually the one on the D↯D′ edge — the claim that both actions compete for the same resource.",
        ],
      },
      {
        ancora: "injecao",
        titulo: "The injection",
        paragrafos: [
          "An injection is the change that makes the assumption stop holding. It is born attached to ONE assumption: a loose injection is a guess.",
          "Its states are candidate, chosen and discarded. Only a chosen injection seeds the Future Reality Tree — the chain only advances over audited material.",
        ],
      },
    ],
    exemplo:
      "Horizonte Institute: to sustain itself (A) it needs new revenue (B) and preserved academic reputation (C). Opening classes in three cities (D) brings revenue; not opening (D′) preserves reputation. The D↯D′ assumption — “the budget is indivisible within the fiscal year” — falls to the injection of milestone-gated budget phasing.",
  },
};

export default verbete;
