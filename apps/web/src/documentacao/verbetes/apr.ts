/**
 * Verbete de documentação embutida — Árvore de Pré-Requisitos (E8.4 da spec 011).
 *
 * Conteúdo versionado no repositório, nunca gerado em tempo de execução (RF-24, ADR 0007).
 * Tradução inglesa pendente e declarada (F8.4.3).
 */
import type { Verbete } from "../tipos";

export const verbete: Verbete = {
  ferramenta: "apr",
  procedencia: ["specs/008-arvores-de-futuro-e-implementacao/spec.md"],
  pt: {
    titulo: "Árvore de Pré-Requisitos",
    resposta: "O que impede a mudança de acontecer — e em que ordem remover.",
    secoes: [
      {
        ancora: "o-que-responde",
        titulo: "O que ela responde",
        paragrafos: [
          "A Árvore de Pré-Requisitos (APR) responde a terceira pergunta: como causar a mudança? Ela começa pelo objetivo e levanta os obstáculos reais entre hoje e ele.",
          "Obstáculo genérico não serve. “Falta de recursos” não é obstáculo: é desculpa. “Há apenas uma pessoa treinada no acompanhamento do marco” é obstáculo — dá para ver quando ele deixou de existir.",
        ],
      },
      {
        ancora: "obstaculo-e-oi",
        titulo: "Obstáculo e Objetivo Intermediário",
        paragrafos: [
          "Cada obstáculo ganha um Objetivo Intermediário (OI): o estado que, existindo, faz aquele obstáculo deixar de impedir. O OI é um estado, não uma tarefa.",
          "Um Objetivo Intermediário pode superar vários obstáculos; um obstáculo tem uma resposta só. A ferramenta recusa parear duas vezes o mesmo obstáculo.",
        ],
      },
      {
        ancora: "teste-de-validade",
        titulo: "Teste de validade",
        paragrafos: [
          "A leitura do teste é sempre a mesma frase: se <objetivo intermediário>, então <obstáculo> não impede mais <objetivo>. Ler em voz alta é o teste.",
          "O julgamento é humano por regra, com autor e justificativa registrados. A ferramenta monta a frase dos textos ATUAIS — nunca de uma cópia congelada.",
        ],
      },
      {
        ancora: "sequenciamento",
        titulo: "Sequenciamento",
        paragrafos: [
          "As dependências entre Objetivos Intermediários produzem camadas: o que pode começar já, o que espera. A ferramenta calcula as camadas, mostra os ramos paralelos e BLOQUEIA quando encontra dependência circular — dizendo qual é o ciclo.",
          "A elipse de simultaneidade marca os objetivos que só valem juntos.",
        ],
      },
    ],
    exemplo:
      "Instituição Horizonte: o obstáculo “há apenas uma pessoa treinada no acompanhamento do marco” é superado pelo objetivo intermediário “existem três pessoas treinadas e escaladas”, julgado válido pela gestora com a justificativa registrada.",
  },
};

export default verbete;
