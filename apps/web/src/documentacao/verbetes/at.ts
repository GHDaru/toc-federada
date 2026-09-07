/**
 * Verbete de documentação embutida — Árvore de Transição (E8.4 da spec 011).
 *
 * Conteúdo versionado no repositório, nunca gerado em tempo de execução (RF-24, ADR 0007).
 * Tradução inglesa pendente e declarada (F8.4.3).
 */
import type { Verbete } from "../tipos";

export const verbete: Verbete = {
  ferramenta: "at",
  procedencia: ["specs/008-arvores-de-futuro-e-implementacao/spec.md"],
  pt: {
    titulo: "Árvore de Transição",
    resposta: "Que passos executar, em que ordem, e como saber que cada um funcionou.",
    secoes: [
      {
        ancora: "o-que-responde",
        titulo: "O que ela responde",
        paragrafos: [
          "A Árvore de Transição (AT) é o plano de execução de um Objetivo Intermediário. É a única ferramenta da Teoria das Restrições em que a pergunta não é lógica, e sim operacional: quem faz o quê, e como se vê que deu certo.",
        ],
      },
      {
        ancora: "a-tripla-do-passo",
        titulo: "A tripla obrigatória do passo",
        paragrafos: [
          "Todo passo nasce com três campos, e a ferramenta não cria o passo sem os três: a necessidade (por que este passo existe), a ação (o que se faz) e o resultado esperado (o que passa a ser verdade quando ele termina).",
          "A tripla é o que separa um plano de uma lista de tarefas. Sem resultado esperado, ninguém consegue dizer se o passo terminou.",
        ],
      },
      {
        ancora: "status-do-passo",
        titulo: "Status, bloqueio e resultado real",
        paragrafos: [
          "Os status são pendente, em execução, concluído e bloqueado. Bloquear exige motivo escrito; concluir exige o resultado REAL.",
          "O resultado real entra em campo próprio e NÃO sobrescreve o esperado: a divergência entre os dois é insumo para revisitar a árvore — nunca para apagar a promessa.",
        ],
      },
    ],
    exemplo:
      "Instituição Horizonte: o passo “escalar três pessoas para o acompanhamento do marco” tem a necessidade (“o marco precisa de acompanhamento semanal”) e o resultado esperado (“o marco é acompanhado sem depender de uma pessoa”) escritos antes de começar.",
  },
};

export default verbete;
