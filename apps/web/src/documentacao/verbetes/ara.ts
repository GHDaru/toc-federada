/**
 * Verbete de documentação embutida — Árvore da Realidade Atual (E8.4 da spec 011).
 *
 * Conteúdo **versionado no repositório**, nunca gerado em tempo de execução por modelo de
 * linguagem (RF-24, ADR 0007 — *Architecture Decision Record*). A procedência é conferida
 * por `scripts/check-documentacao.sh`: caminho citado que não resolve derruba o portão.
 */
import type { Verbete } from "../tipos";

export const verbete: Verbete = {
  ferramenta: "ara",
  procedencia: [
    "specs/005-arvore-da-realidade-atual/spec.md",
    "docs/adr/0005-escopo-do-dominio-v1.md",
  ],
  pt: {
    titulo: "Árvore da Realidade Atual",
    resposta: "O que, exatamente, está errado hoje — e por quê.",
    secoes: [
      {
        ancora: "o-que-responde",
        titulo: "O que ela responde",
        paragrafos: [
          "A Árvore da Realidade Atual (ARA) parte dos sintomas que incomodam e desce até as poucas causas que os produzem. A pergunta que ela responde é a primeira dos processos de pensamento da Teoria das Restrições: o que mudar?",
          "Ela não é um mapa mental. Cada caixa é um efeito que existe AGORA, e cada seta é uma afirmação verificável: se a origem existe, então o destino existe.",
        ],
      },
      {
        ancora: "criterios-de-ude",
        titulo: "O que faz de um efeito um Efeito Indesejável",
        paragrafos: [
          "Efeito Indesejável (UDE) é um enunciado, não um rótulo. A ferramenta confere doze critérios formais sobre o texto que você escreveu: oito são decidíveis por regra (frase completa, tempo presente, estado e não ação, sem culpa a pessoa, não é solução disfarçada, uma entidade só, sem causa embutida, factual) e quatro pedem julgamento humano (queixa contínua, esfera de influência, acionável, não é causa especulada).",
          "A validação formal não aprova nem reprova sozinha: ela mostra o que falta. Quem valida é uma pessoa, e o parecer fica registrado com autor e justificativa.",
          "“O time está desmotivado” não passa: não é factual e não diz o estado observável. “A taxa de evasão no primeiro semestre é de 22%” passa: é um estado do mundo, no presente, mensurável.",
        ],
      },
      {
        ancora: "elo-e-suficiencia",
        titulo: "O elo e o exame de suficiência",
        paragrafos: [
          "Toda seta nasce com um exame: a causa apontada é suficiente para produzir o efeito, ou falta alguma coisa? Os quatro estados são não examinado, suficiente, insuficiente e com reserva — e os dois últimos exigem a reserva escrita.",
          "Quando duas causas só produzem o efeito JUNTAS, elas entram num conector “E”: se A e B, então C. É a elipse canônica da TOC, e ela muda a leitura da árvore inteira.",
        ],
      },
      {
        ancora: "causa-raiz",
        titulo: "Causa raiz candidata",
        paragrafos: [
          "Causa raiz candidata é o nó que alcança muitos Efeitos Indesejáveis e não é efeito de ninguém. A análise estrutural as lista, e exclui do cálculo os nós que participam de um ciclo — laços de reforço são legítimos na TOC e não são raiz de nada.",
          "A ferramenta não escolhe a restrição por você: ela mostra a estrutura, e a decisão continua sendo do grupo.",
        ],
      },
    ],
    exemplo:
      "Na Instituição Horizonte, três Efeitos Indesejáveis — evasão de 22% no primeiro semestre, caixa negativo no trimestre e turmas abertas sem professor formado — sobem para uma causa comum: o acolhimento do primeiro ano não é acompanhado por ninguém.",
  },
  en: {
    titulo: "Current Reality Tree",
    resposta: "What exactly is wrong today — and why.",
    secoes: [
      {
        ancora: "o-que-responde",
        titulo: "What it answers",
        paragrafos: [
          "The Current Reality Tree (CRT) starts from the symptoms that hurt and works down to the few causes that produce them. It answers the first question of the Theory of Constraints thinking processes: what to change?",
          "It is not a mind map. Every box is an effect that exists NOW, and every arrow is a checkable claim: if the source exists, then the target exists.",
        ],
      },
      {
        ancora: "criterios-de-ude",
        titulo: "What makes an effect an Undesirable Effect",
        paragrafos: [
          "An Undesirable Effect (UDE) is a statement, not a label. The tool checks twelve formal criteria against the text you wrote: eight are decidable by rule (complete sentence, present tense, state rather than action, no blame, not a disguised solution, single entity, no embedded cause, factual) and four call for human judgement (ongoing complaint, sphere of influence, actionable, not a speculated cause).",
          "Formal validation neither approves nor rejects on its own: it shows what is missing. A person validates, and the opinion is recorded with author and rationale.",
          "“The team is demotivated” fails: not factual, no observable state. “First-semester dropout is at 22%” passes: a state of the world, in the present, measurable.",
        ],
      },
      {
        ancora: "elo-e-suficiencia",
        titulo: "The link and its sufficiency check",
        paragrafos: [
          "Every arrow is born with a check: is the stated cause sufficient to produce the effect, or is something missing? The four states are unexamined, sufficient, insufficient and reserved — and the last two require the reservation in writing.",
          "When two causes only produce the effect TOGETHER, they join an “AND” connector: if A and B, then C. It is the canonical TOC ellipse, and it changes how the whole tree reads.",
        ],
      },
      {
        ancora: "causa-raiz",
        titulo: "Candidate root cause",
        paragrafos: [
          "A candidate root cause is a node that reaches many Undesirable Effects and is nobody's effect. Structural analysis lists them, excluding nodes inside a loop — reinforcing loops are legitimate in TOC and are nobody's root.",
          "The tool does not pick the constraint for you: it shows the structure, and the decision stays with the group.",
        ],
      },
    ],
    exemplo:
      "At Horizonte Institute, three Undesirable Effects — 22% first-semester dropout, negative quarterly cash and classes opened without qualified teachers — climb to one common cause: nobody follows up on first-year onboarding.",
  },
};

export default verbete;
