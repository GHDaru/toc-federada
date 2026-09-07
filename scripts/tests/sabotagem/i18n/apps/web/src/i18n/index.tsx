// O mecanismo mínimo, com as duas regras que o portão confere (RF-09, RF-10).
import { pt, type Dicionario } from "./pt";

export class ChaveDeTraducaoAusente extends Error {}

export function traduzirCom(
  dicionario: Dicionario,
  chave: string,
  parametros: Record<string, string | number> = {},
  opcoes: { modo?: "estrito" | "tolerante"; fonte?: Dicionario; registrar?: (l: unknown) => void } = {},
): string {
  const achado = buscar(dicionario, chave);
  if (achado !== undefined) return interpolar(achado, parametros);
  if ((opcoes.modo ?? "estrito") === "estrito") throw new ChaveDeTraducaoAusente(chave);
  opcoes.registrar?.({ evento: "i18n.chave_ausente", chave });
  const daFonte = buscar(opcoes.fonte ?? pt, chave);
  return daFonte === undefined ? "" : interpolar(daFonte, parametros);
}

function buscar(dicionario: Dicionario | undefined, chave: string): string | undefined {
  let atual: unknown = dicionario;
  for (const parte of chave.split(".")) {
    if (atual && typeof atual === "object" && parte in (atual as object)) {
      atual = (atual as Record<string, unknown>)[parte];
    } else {
      return undefined;
    }
  }
  return typeof atual === "string" ? atual : undefined;
}

function interpolar(texto: string, parametros: Record<string, string | number>): string {
  return texto.replace(/\{\{(\w+)\}\}/g, (bruto, nome: string) =>
    nome in parametros ? String(parametros[nome]) : bruto,
  );
}
