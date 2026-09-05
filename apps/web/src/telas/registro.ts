/**
 * O registro de telas — a mesma declaração que o serviço mantém em
 * `apps/api/src/toc_api/dominio/federacao/telas.py`, do lado da interface.
 *
 * Siglas, uma vez: **APH** — Aplicação ↔ Harness · **IA** — inteligência artificial ·
 * **DOM** — *Document Object Model* · **ARA** — Árvore da Realidade Atual · **UDE** —
 * Efeito Indesejável · **NC** — Nuvem de Conflito.
 *
 * Por que existe dos dois lados: o APH-3.1 manda que a assistência **nunca infira a
 * interface** — nada de raspar DOM, nada de ler captura de tela. Ela sabe onde a pessoa
 * está porque a tela está declarada. O serviço monta o snapshot a partir do registro
 * dele; a interface roteia a partir deste. Um teste compara os dois com o manifesto
 * publicado, que é o que impede a dupla de divergir em silêncio.
 *
 * **`aiVisivel` é declarado campo a campo, e o padrão é não visível** (RF-01 da spec 002):
 * cada `true` carrega justificativa escrita. Ausência de declaração seria "esqueci", e
 * "esqueci" é como dado sensível vaza para um modelo.
 */

export type AcaoDeIa = "READ" | "FILL_FIELDS" | "SUBMIT" | "NAVIGATE";
export type TipoDeCampo = "text" | "number" | "boolean" | "date" | "select" | "entity" | "other";

export interface CampoDeTela {
  nome: string;
  tipo: TipoDeCampo;
  rotulo: string;
  aiVisivel: boolean;
  /** Obrigatória quando `aiVisivel` é verdadeiro. Vazia quando é falso. */
  justificativa: string;
}

export interface Tela {
  id: string;
  rota: string;
  titulo: string;
  acoesDeIa: readonly AcaoDeIa[];
  campos: readonly CampoDeTela[];
  /**
   * Se esta tela está no manifesto publicado. A Nuvem de Conflito ainda **não** está: o
   * manifesto do ciclo 006 declara quatro telas, e acrescentar a quinta é mudança de
   * manifesto — que passa por gate de admissão, não por decisão de quem escreve a tela.
   * Enquanto isso, ela é rota da interface e **não** é superfície de snapshot.
   */
  declaradaNoManifesto: boolean;
}

export const REGISTRO_DE_TELAS: readonly Tela[] = [
  {
    id: "toc.projetos",
    rota: "/toc/projetos",
    titulo: "Projetos",
    acoesDeIa: ["READ", "NAVIGATE"],
    declaradaNoManifesto: true,
    campos: [
      {
        nome: "filtro_ferramenta",
        tipo: "text",
        rotulo: "Ferramenta",
        aiVisivel: true,
        justificativa: "é um filtro de navegação, sem conteúdo de análise",
      },
      {
        nome: "quantidade_de_projetos",
        tipo: "number",
        rotulo: "Projetos listados",
        aiVisivel: true,
        justificativa: "contagem agregada, sem nome nem texto de projeto",
      },
      {
        nome: "projeto_selecionado",
        tipo: "entity",
        rotulo: "Projeto selecionado",
        aiVisivel: true,
        justificativa: "referência ao projeto aberto, necessária para a ação `toc.*` saber o alvo",
      },
    ],
  },
  {
    id: "toc.ara",
    rota: "/toc/ara",
    titulo: "Arvore da Realidade Atual",
    acoesDeIa: ["READ", "FILL_FIELDS", "SUBMIT", "NAVIGATE"],
    declaradaNoManifesto: true,
    campos: [
      {
        nome: "projeto_id",
        tipo: "text",
        rotulo: "Projeto",
        aiVisivel: true,
        justificativa: "identifica o alvo das ações governadas da ARA",
      },
      {
        nome: "nos_visiveis",
        tipo: "number",
        rotulo: "Nós visíveis",
        aiVisivel: true,
        justificativa: "tamanho da árvore em tela; agregado, sem texto de nó",
      },
      {
        nome: "no_selecionado",
        tipo: "entity",
        rotulo: "Nó selecionado",
        aiVisivel: true,
        justificativa: "o que a pessoa está olhando — é o contexto da proposta",
      },
      {
        nome: "rascunho_de_parecer",
        tipo: "text",
        rotulo: "Rascunho de parecer",
        aiVisivel: false,
        justificativa: "",
      },
    ],
  },
  {
    id: "toc.lixeira",
    rota: "/toc/lixeira",
    titulo: "Lixeira",
    acoesDeIa: ["READ"],
    declaradaNoManifesto: true,
    campos: [
      {
        nome: "itens_na_lixeira",
        tipo: "number",
        rotulo: "Itens na lixeira",
        aiVisivel: true,
        justificativa: "contagem agregada, sem nome de projeto excluído",
      },
    ],
  },
  {
    id: "toc.configuracao",
    rota: "/toc/configuracao",
    titulo: "Configuracao do embarque",
    acoesDeIa: [],
    declaradaNoManifesto: true,
    campos: [
      { nome: "host_origin", tipo: "text", rotulo: "Origem do hospedeiro", aiVisivel: false, justificativa: "" },
      { nome: "app_id", tipo: "text", rotulo: "Identificador da aplicação", aiVisivel: false, justificativa: "" },
    ],
  },
  {
    // Rota da interface, ainda **fora** do manifesto (ver `declaradaNoManifesto`).
    id: "toc.nuvem",
    rota: "/toc/nuvem",
    titulo: "Nuvem de Conflito",
    acoesDeIa: [],
    declaradaNoManifesto: false,
    campos: [
      { nome: "projeto_id", tipo: "text", rotulo: "Projeto", aiVisivel: false, justificativa: "" },
    ],
  },
] as const;

export function telaPorId(id: string): Tela | undefined {
  return REGISTRO_DE_TELAS.find((tela) => tela.id === id);
}

/** §B.5.3: `ai_actions: []` marca item sensível — não entra em snapshot algum. */
export function telaSensivel(id: string): boolean {
  const tela = telaPorId(id);
  return !tela || tela.acoesDeIa.length === 0;
}

export function camposVisiveisParaIa(id: string): string[] {
  if (telaSensivel(id)) return [];
  return (telaPorId(id)?.campos ?? []).filter((c) => c.aiVisivel).map((c) => c.nome);
}
