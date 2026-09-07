/**
 * Verbete de documentação embutida — Árvore da Realidade Futura (E8.4 da spec 011).
 *
 * Conteúdo versionado no repositório, nunca gerado em tempo de execução por modelo de
 * linguagem (RF-24, ADR 0007 — *Architecture Decision Record*).
 *
 * **Sem tradução inglesa por enquanto**, e a ausência é declarada: a F8.4.3 manda mostrar
 * a língua-fonte com aviso de tradução pendente, e o portão de cobertura conta a pendência
 * — em vez de ela virar uma tela vazia, que é o que a linhagem entregava.
 */
import type { Verbete } from "../tipos";

export const verbete: Verbete = {
  ferramenta: "arf",
  procedencia: [
    "specs/008-arvores-de-futuro-e-implementacao/spec.md",
    "docs/adr/0012-modulo-m4-suficiencia-compartilhada-e-referencia-como-agregado.md",
  ],
  pt: {
    titulo: "Árvore da Realidade Futura",
    resposta: "Se a mudança acontecer, o que passa a ser verdade — e o que pode piorar.",
    secoes: [
      {
        ancora: "o-que-responde",
        titulo: "O que ela responde",
        paragrafos: [
          "A Árvore da Realidade Futura (ARF) responde a segunda pergunta dos processos de pensamento: para o que mudar? Ela parte da injeção escolhida na Nuvem de Conflito e desce a cadeia de efeitos desejáveis que ela produz.",
          "A prova de que a mudança serve é o espelho: cada Efeito Indesejável da Árvore da Realidade Atual tem de aparecer aqui invertido. Efeito Indesejável sem espelho é sintoma que a mudança não resolve — e isso é informação, não defeito.",
        ],
      },
      {
        ancora: "injecao-e-efeito-futuro",
        titulo: "Injeção, efeito futuro e suficiência",
        paragrafos: [
          "O nó semente é a injeção. Dela saem os efeitos futuros, e cada elo passa pelo mesmo exame de suficiência da Árvore da Realidade Atual — o exame não é de outra ferramenta, é o mesmo.",
          "Um efeito futuro sem caminho até a injeção é promessa sem lastro: a verificação da árvore os lista.",
        ],
      },
      {
        ancora: "ramo-negativo",
        titulo: "Ramo negativo",
        paragrafos: [
          "Ramo negativo é o efeito colateral ruim que a mudança também produz. Declará-lo não é pessimismo: é a diferença entre um plano e um anúncio.",
          "Cada ramo tem três saídas: podar (uma injeção nova o corta), aceitar (com justificativa e autor registrados — é decisão de responsabilidade) ou reabrir. Ramo aberto aparece na verificação da árvore.",
        ],
      },
      {
        ancora: "cobertura",
        titulo: "Cobertura dos sintomas de hoje",
        paragrafos: [
          "A cobertura compara os Efeitos Indesejáveis que vieram na cadeia com os que a árvore espelha e alcança. Ela responde à pergunta que decide a mudança: quantos dos meus problemas de hoje esta injeção resolve?",
        ],
      },
    ],
    exemplo:
      "Instituição Horizonte: a injeção do faseamento orçamentário produz “as duas frentes recebem verba no trimestre”, que espelha o caixa negativo. O ramo negativo declarado — “a equipe de matrícula fica sobrecarregada” — segue aberto até alguém podá-lo ou aceitá-lo por escrito.",
  },
};

export default verbete;
