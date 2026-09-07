/**
 * Verbete de documentação embutida — os cinco passos de focalização (E8.4 da spec 011).
 *
 * Conteúdo versionado no repositório, nunca gerado em tempo de execução (RF-24, ADR 0007).
 * Tradução inglesa pendente e declarada (F8.4.3).
 */
import type { Verbete } from "../tipos";

export const verbete: Verbete = {
  ferramenta: "focalizacao",
  procedencia: [
    "specs/009-focalizacao/spec.md",
    "docs/adr/0013-taxonomia-fechada-da-restricao-e-heranca-que-volta-a-mesa.md",
  ],
  pt: {
    titulo: "Os cinco passos de focalização",
    resposta: "Onde está a restrição do sistema, e o que fazer com ela — em ciclos.",
    secoes: [
      {
        ancora: "o-que-responde",
        titulo: "O que ela responde",
        paragrafos: [
          "A jornada dos cinco passos é o que costura as outras ferramentas. Ela não desenha diagrama nenhum: registra a restrição do sistema e conduz o ciclo de melhoria em volta dela.",
          "Sem esta jornada, as seis ferramentas seriam seis ilhas — que é exatamente o que a linhagem entregou em quatro gerações.",
        ],
      },
      {
        ancora: "os-cinco-passos",
        titulo: "Os cinco passos",
        paragrafos: [
          "1. Identificar a restrição do sistema. 2. Decidir como explorá-la. 3. Subordinar tudo o mais a essa decisão. 4. Elevar a restrição. 5. Se a restrição foi quebrada, voltar ao passo 1 — e não deixar a inércia virar a restrição.",
          "Cada passo guarda decisões, notas e vínculos com projetos das outras ferramentas. Concluir um passo exige que o anterior esteja concluído; reabrir um passo anterior exige justificativa escrita.",
        ],
      },
      {
        ancora: "tipo-de-restricao",
        titulo: "O tipo da restrição",
        paragrafos: [
          "O tipo vem de um vocabulário fechado — física, de política, de mercado, de fornecedor, de capacidade —, e o vocabulário é fechado de propósito: “restrição de tipo outro” é como uma restrição de política vira um problema de máquina e ninguém percebe.",
        ],
      },
      {
        ancora: "heranca",
        titulo: "A herança que volta à mesa",
        paragrafos: [
          "Ao abrir um ciclo novo, as decisões do ciclo anterior voltam para julgamento: manter, revogar ou substituir. Manter e revogar exigem justificativa.",
          "É o quinto passo em forma de mecanismo: a regra que foi criada para a restrição antiga é a inércia que se torna a próxima restrição.",
        ],
      },
    ],
    exemplo:
      "Instituição Horizonte: no ciclo 1, a restrição é de política — “o orçamento é aprovado uma vez por exercício”. No ciclo 2, com o faseamento implantado, essa política deixa de ser a restrição, e a decisão de subordinação criada para ela volta à mesa para ser revogada.",
  },
};

export default verbete;
