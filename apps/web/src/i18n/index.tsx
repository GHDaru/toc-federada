/**
 * Internacionalização — português e inglês desde o primeiro dia (RI-10 da spec 005,
 * RI-11 da spec 007), e não como camada acrescentada depois.
 *
 * Siglas, uma vez: **UDE** — Efeito Indesejável · **API** — interface de programação de
 * aplicações · **ARA** — Árvore da Realidade Atual.
 *
 * Duas diferenças em relação ao `i18n/` da 4ª geração da linhagem, que é de onde a forma
 * veio (`tocbuilderv3/i18n/I18nProvider.tsx`):
 *
 * 1. **A chave é tipada.** `t("projetos.titulo")` compila; `t("projetos.titlo")` não.
 *    Lá, `t` recebia `string` e a chave errada aparecia crua na tela.
 * 2. **A tabela inglesa tem o tipo da portuguesa.** Chave faltando é erro de compilação —
 *    lá, `pt.ts` e `en.ts` divergiram em silêncio.
 *
 * O idioma também viaja para o serviço: a validação formal de UDE é feita no domínio, e o
 * léxico dela é por idioma (`POST /toc/ara/validacoes` recebe `idioma`).
 */
import { createContext, useCallback, useContext, useMemo, useState, type ReactNode } from "react";
import { pt, type Dicionario } from "./pt";
import { en } from "./en";

export type Idioma = "pt" | "en";

const TABELAS: Record<Idioma, Dicionario> = { pt, en };

/** Todos os caminhos de folha do dicionário, como união de literais. */
type Caminhos<T> = T extends string
  ? ""
  : {
      [K in keyof T & string]: Caminhos<T[K]> extends "" ? K : `${K}.${Caminhos<T[K]>}`;
    }[keyof T & string];

export type ChaveDeTraducao = Caminhos<Dicionario>;

export type Parametros = Record<string, string | number>;

/**
 * Os espaços de nome cujas chaves são **códigos vindos do servidor** (status, veredito,
 * critério, classe de aresta, separação TRIZ…). Estão listados porque `tc` traduz um
 * código que a interface não escolheu: a lista é o contrato entre as duas pontas.
 */
export type EspacoDeCodigo =
  | "criterio"
  | "aviso"
  | "status"
  | "erro"
  | "veredito"
  | "classe"
  | "papel"
  | "ferramenta"
  | "estado_do_exame"
  | "estado_da_premissa"
  | "status_da_injecao"
  | "separacao";

export function traduzirCom(
  dicionario: Dicionario,
  chave: ChaveDeTraducao,
  parametros: Parametros = {},
): string {
  let atual: unknown = dicionario;
  for (const parte of chave.split(".")) {
    if (atual && typeof atual === "object" && parte in (atual as object)) {
      atual = (atual as Record<string, unknown>)[parte];
    } else {
      // A própria chave na tela é feio e é honesto: diz o que faltou traduzir, em vez de
      // um espaço em branco que ninguém consegue diagnosticar.
      return chave;
    }
  }
  if (typeof atual !== "string") return chave;
  return atual.replace(/\{\{(\w+)\}\}/g, (bruto, nome: string) =>
    nome in parametros ? String(parametros[nome]) : bruto,
  );
}

export interface ContextoDeIdioma {
  idioma: Idioma;
  trocarIdioma: (idioma: Idioma) => void;
  t: (chave: ChaveDeTraducao, parametros?: Parametros) => string;
  /** Tradução por código vindo do servidor (critério, aviso, status, erro). */
  tc: (prefixo: EspacoDeCodigo, codigo: string, alternativa?: string) => string;
}

const Contexto = createContext<ContextoDeIdioma | undefined>(undefined);

export function ProvedorDeIdioma({
  children,
  idiomaInicial = "pt",
}: {
  children: ReactNode;
  idiomaInicial?: Idioma;
}) {
  const [idioma, setIdioma] = useState<Idioma>(idiomaInicial);

  const t = useCallback(
    (chave: ChaveDeTraducao, parametros: Parametros = {}) =>
      traduzirCom(TABELAS[idioma], chave, parametros),
    [idioma],
  );

  const tc = useCallback(
    (prefixo: EspacoDeCodigo, codigo: string, alternativa = "") => {
      // O servidor manda o código; a tela traduz. Código novo do servidor cai na
      // alternativa (o texto que ele mesmo mandou) em vez de apagar a informação.
      const chave = `${prefixo}.${codigo}` as ChaveDeTraducao;
      const traduzido = traduzirCom(TABELAS[idioma], chave);
      return traduzido === chave ? alternativa || codigo : traduzido;
    },
    [idioma],
  );

  const valor = useMemo<ContextoDeIdioma>(
    () => ({ idioma, trocarIdioma: setIdioma, t, tc }),
    [idioma, t, tc],
  );

  return <Contexto.Provider value={valor}>{children}</Contexto.Provider>;
}

export function useI18n(): ContextoDeIdioma {
  const contexto = useContext(Contexto);
  if (!contexto) throw new Error("useI18n exige <ProvedorDeIdioma> acima na árvore");
  return contexto;
}

export { pt, en };
export type { Dicionario };
