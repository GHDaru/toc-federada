/**
 * E8.4 — o acervo de documentação embutida: os tipos e as regras (spec 011).
 *
 * Siglas, uma vez: **ARA** — Árvore da Realidade Atual · **NC** — Nuvem de Conflito ·
 * **ARF** — Árvore da Realidade Futura · **APR** — Árvore de Pré-Requisitos · **AT** —
 * Árvore de Transição · **S&T** — Estratégia & Táticas · **UDE** — Efeito Indesejável ·
 * **TOC** — Teoria das Restrições · **IA** — inteligência artificial · **ADR** —
 * *Architecture Decision Record* (Registro de Decisão Arquitetural).
 *
 * **O precedente, e o que ele acertou e errou.** A quarta geração da linhagem tinha um
 * `DocsView` de 125 linhas (`tocbuilderv3/components/DocsView.tsx:17-33`) com índice por
 * tópico à esquerda, corpo à direita e um botão que levava à ferramenta descrita. A
 * **forma estava certa** e é a que este módulo sucede. O que estava errado era a
 * cobertura: quatro tópicos (`intro`, `ara`, `nc`, `ai`) para seis ferramentas
 * declaradas em `types.ts:249-258`, e as outras quatro respondiam com a cadeia
 * `"Esta ferramenta ainda não foi implementada."` (`locales/pt.ts:424`).
 *
 * Aqui as sete existem quando o ciclo abre, e por isso a cobertura é **portão**:
 * `scripts/check-documentacao.sh` deriva a lista de ferramentas do REGISTRO do serviço
 * (`registrar_raiz_de_ferramenta`, no domínio) e reprova ferramenta sem verbete — RN-04:
 * "uma ferramenta só é considerada entregue quando tem verbete".
 *
 * **O conteúdo é versionado no repositório, nunca gerado em tempo de execução** (RF-24,
 * ADR 0007): se um dia houver ajuda gerada, ela nasce ação de catálogo com proposta — não
 * um `<div>` com saída de modelo de linguagem.
 */
import type { Idioma } from "../i18n";

/** Um trecho do verbete, endereçável por âncora (RF-20). */
export interface SecaoDoVerbete {
  /** Identificador estável, usado pela ajuda contextual da tela. */
  ancora: string;
  titulo: string;
  /** Parágrafos. Texto puro: o acervo não interpreta marcação nem executa nada. */
  paragrafos: string[];
}

export interface ConteudoDoVerbete {
  titulo: string;
  /** Uma frase: o que esta ferramenta responde. */
  resposta: string;
  secoes: SecaoDoVerbete[];
  /** O exemplo sintético da "Instituição Horizonte" (RI-06, ADR 0006). */
  exemplo: string;
}

export interface Verbete {
  /** A ferramenta a que o verbete pertence — o mesmo código do serviço (`ara`, `nc`…). */
  ferramenta: string;
  /**
   * De onde vem a regra que o verbete descreve (RF-22): caminhos relativos à raiz do
   * repositório, conferidos pelo portão. Verbete que não cita procedência é opinião.
   */
  procedencia: string[];
  /** A língua-fonte é obrigatória (RN-01); a tradução é opcional e vira pendência. */
  pt: ConteudoDoVerbete;
  en?: ConteudoDoVerbete;
}

/**
 * F8.4.3 — verbete sem tradução aparece na língua-fonte, **dizendo que é o caso**.
 *
 * A alternativa que a linhagem não tinha é uma tela vazia; a que este produto recusa é
 * fingir que o conteúdo em português é a versão inglesa.
 */
export interface VerbeteApresentado {
  conteudo: ConteudoDoVerbete;
  idioma: Idioma;
  /** Verdadeiro quando o idioma efetivo não é o do conteúdo mostrado. */
  traducaoPendente: boolean;
}

export function apresentar(verbete: Verbete, idioma: Idioma): VerbeteApresentado {
  if (idioma === "en" && verbete.en) {
    return { conteudo: verbete.en, idioma: "en", traducaoPendente: false };
  }
  return {
    conteudo: verbete.pt,
    idioma: "pt",
    traducaoPendente: idioma !== "pt",
  };
}

/** As âncoras que um verbete oferece — o contrato da ajuda contextual. */
export function ancorasDe(verbete: Verbete): string[] {
  const das = (conteudo?: ConteudoDoVerbete) => (conteudo?.secoes ?? []).map((s) => s.ancora);
  return Array.from(new Set([...das(verbete.pt), ...das(verbete.en)]));
}
