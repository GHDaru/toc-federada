/**
 * Verbete de documentação embutida — Estratégia & Táticas (E8.4 da spec 011).
 *
 * Conteúdo versionado no repositório, nunca gerado em tempo de execução (RF-24, ADR 0007).
 * Tradução inglesa pendente e declarada (F8.4.3).
 */
import type { Verbete } from "../tipos";

export const verbete: Verbete = {
  ferramenta: "snt",
  procedencia: [
    "specs/010-estrategia-e-taticas/spec.md",
    "docs/adr/0014-categoria-portada-e-transicao-de-status-livre-na-snt.md",
  ],
  pt: {
    titulo: "Árvore de Estratégia & Táticas",
    resposta: "Como o plano inteiro se sustenta, do topo até o passo mais concreto.",
    secoes: [
      {
        ancora: "o-que-responde",
        titulo: "O que ela responde",
        paragrafos: [
          "A árvore de Estratégia & Táticas (S&T) decompõe a meta global em passos hierárquicos. Cada passo diz O QUE se quer (estratégia) e COMO se consegue (tática).",
          "É a única ferramenta desta linhagem que regrediu entre gerações — e por isso volta com a estrutura estrita: pai único, ordem explícita, ciclo impossível por construção.",
        ],
      },
      {
        ancora: "as-tres-premissas",
        titulo: "As três premissas lógicas",
        paragrafos: [
          "Cada passo carrega três premissas, e cada uma responde a uma pergunta diferente: a premissa paralela (por que esta estratégia é necessária agora), a premissa de necessidade ao pai (por que o pai precisa deste filho) e a premissa de suficiência dos filhos (por que estes filhos bastam para o pai).",
          "Passo sem tática, sem premissa de necessidade ou sem premissa de suficiência aparece na lista de pendências lógicas — não é bloqueio, é dívida visível.",
        ],
      },
      {
        ancora: "numeracao",
        titulo: "Numeração derivada",
        paragrafos: [
          "O número de um passo (1, 1.1, 1.1.2) NÃO é digitado: ele é derivado da posição na árvore. Mover uma subárvore renumera tudo o que desceu junto, e a prévia mostra o resultado antes de confirmar.",
          "Número digitado e estrutura são duas fontes de verdade que discordam na primeira edição — é exatamente o que este desenho torna impossível.",
        ],
      },
      {
        ancora: "status",
        titulo: "Status do passo",
        paragrafos: [
          "Os quatro status — nenhum, validado, em execução, não validado — descrevem o andamento, e a transição entre eles é livre: o plano volta atrás, e um fluxo rígido só ensinaria a mentir para a ferramenta.",
        ],
      },
    ],
    exemplo:
      "Instituição Horizonte: a meta global “atender o dobro de pessoas com a estrutura atual” decompõe em 1. “reduzir o tempo de espera pela metade”, que por sua vez tem 1.1 “enxergar a fila em tempo real” e 1.2 “eliminar a espera por conferência”.",
  },
};

export default verbete;
