/**
 * E8.4 — o acervo: quais ferramentas têm verbete, e como cada um é carregado.
 *
 * Siglas, uma vez: **ARA** — Árvore da Realidade Atual · **NC** — Nuvem de Conflito ·
 * **ARF** — Árvore da Realidade Futura · **APR** — Árvore de Pré-Requisitos · **AT** —
 * Árvore de Transição · **S&T** — Estratégia & Táticas · **IA** — inteligência artificial.
 *
 * **Carregamento sob demanda** (RNF-09): o corpo de cada verbete entra por `import()`
 * dinâmico, e por isso abrir a documentação não engorda o pacote inicial da aplicação —
 * só o pedaço do verbete aberto viaja. O índice (título e ferramenta) é estático, porque
 * ele aparece antes de qualquer escolha.
 *
 * **A lista de ferramentas é a do serviço.** As sete abaixo são as que o domínio registra
 * em `registrar_raiz_de_ferramenta` (`apps/api/src/toc_api/dominio/`), e é dessa
 * declaração que `scripts/check-documentacao.sh` deriva o denominador da cobertura — não
 * desta lista. Uma segunda lista que se conferisse a si mesma responderia verde sobre
 * duas ferramentas de seis, que foi exatamente o que a quarta geração fez
 * (`tocbuilderv3/components/DocsView.tsx:21-26`).
 */
import type { Verbete } from "./tipos";

export interface EntradaDoIndice {
  ferramenta: string;
  /** A chave de tradução do nome da ferramenta — o índice também é bilíngue. */
  chaveDoTitulo: string;
}

export const INDICE: readonly EntradaDoIndice[] = [
  { ferramenta: "ara", chaveDoTitulo: "ferramenta.ara" },
  { ferramenta: "nc", chaveDoTitulo: "ferramenta.nc" },
  { ferramenta: "arf", chaveDoTitulo: "ferramenta.arf" },
  { ferramenta: "apr", chaveDoTitulo: "ferramenta.apr" },
  { ferramenta: "at", chaveDoTitulo: "ferramenta.at" },
  { ferramenta: "snt", chaveDoTitulo: "ferramenta.snt" },
  { ferramenta: "focalizacao", chaveDoTitulo: "ferramenta.focalizacao" },
] as const;

/**
 * Os carregadores, um por ferramenta. Escritos à mão e não por caminho montado em
 * tempo de execução (`import(\`./verbetes/${f}.ts\`)`) porque um caminho dinâmico faz o
 * empacotador incluir TUDO o que casa com o padrão — e a economia do RNF-09 morreria
 * calada.
 */
const CARREGADORES: Record<string, () => Promise<{ verbete: Verbete }>> = {
  ara: () => import("./verbetes/ara"),
  nc: () => import("./verbetes/nc"),
  arf: () => import("./verbetes/arf"),
  apr: () => import("./verbetes/apr"),
  at: () => import("./verbetes/at"),
  snt: () => import("./verbetes/snt"),
  focalizacao: () => import("./verbetes/focalizacao"),
};

export class VerbeteAusente extends Error {
  constructor(readonly ferramenta: string) {
    super(
      `nenhum verbete de documentação para a ferramenta "${ferramenta}" — ` +
        "ferramenta sem verbete é defeito de aceite (RN-04 da spec 011)",
    );
    this.name = "VerbeteAusente";
  }
}

export function temVerbete(ferramenta: string): boolean {
  return ferramenta in CARREGADORES;
}

export async function carregarVerbete(ferramenta: string): Promise<Verbete> {
  const carregar = CARREGADORES[ferramenta];
  if (!carregar) throw new VerbeteAusente(ferramenta);
  const modulo = await carregar();
  return modulo.verbete;
}

/** As ferramentas cobertas pelo acervo — usado pelo teste de cobertura da interface. */
export function ferramentasCobertas(): string[] {
  return Object.keys(CARREGADORES).sort();
}
