/**
 * Tema — o próprio, completo, e a camada parcial que o inquilino manda no handshake.
 *
 * Siglas, uma vez: **CSS** — *Cascading Style Sheets* · **APH** — Aplicação ↔ Harness.
 *
 * Duas regras, e as duas são de norma, não de gosto:
 *
 * 1. **Lista de permissão** — os tokens consumidos são exatamente os declarados em
 *    `theme.tokens_used` do nosso manifesto
 *    (`specs/006-acoes-governadas-e-snapshot/contracts/manifesto.json`). Token fora da
 *    lista é ignorado: quem embarca não pinta o que não combinou pintar.
 * 2. **Fallback obrigatório** (§B.4.3) — o conjunto que chega é "parcial por desenho", e
 *    elemento sem cor definida é defeito **nosso**. Por isso o tema próprio cobre os
 *    quatro tokens nos dois esquemas, e um teste percorre token a token.
 *
 * A linhagem que sucedemos não tinha tema algum para herdar: a medição do ciclo 001 deu
 * zero ocorrências de `theme|darkMode|dark-mode` em `tocbuilderv3` (spec 002, fonte F-07).
 * Este arquivo nasce sem referência, por decisão.
 */

export const TOKENS_CONSUMIDOS = [
  "color-primary",
  "color-surface",
  "color-text",
  "color-danger",
] as const;

export type TokenConsumido = (typeof TOKENS_CONSUMIDOS)[number];
export type Esquema = "claro" | "escuro";
export type Tema = Record<TokenConsumido, string>;

const CLARO: Tema = {
  "color-primary": "#1d4ed8",
  "color-surface": "#ffffff",
  "color-text": "#0f172a",
  "color-danger": "#b91c1c",
};

const ESCURO: Tema = {
  "color-primary": "#93c5fd",
  "color-surface": "#0f172a",
  "color-text": "#e2e8f0",
  "color-danger": "#fca5a5",
};

export function temaProprio(esquema: Esquema): Tema {
  return { ...(esquema === "escuro" ? ESCURO : CLARO) };
}

export interface TemaResolvido {
  resolvido: Tema;
  /** Tokens que vieram do inquilino e foram vestidos. */
  usados: TokenConsumido[];
  /** Tokens que o inquilino mandou e que não estão na lista de permissão. */
  ignorados: string[];
}

export function resolverTemaDoInquilino(
  recebidos: Record<string, string> | undefined | null,
  esquema: Esquema,
): TemaResolvido {
  const proprio = temaProprio(esquema);
  const resolvido = { ...proprio };
  const usados: TokenConsumido[] = [];
  const ignorados: string[] = [];

  for (const token of TOKENS_CONSUMIDOS) {
    const doInquilino = recebidos && typeof recebidos === "object" ? recebidos[token] : undefined;
    if (typeof doInquilino === "string" && doInquilino.trim()) {
      resolvido[token] = doInquilino;
      usados.push(token);
    }
  }
  for (const nome of Object.keys(recebidos ?? {})) {
    if (!(TOKENS_CONSUMIDOS as readonly string[]).includes(nome)) ignorados.push(nome);
  }
  return { resolvido, usados, ignorados };
}

/** `color-primary` → `--toc-color-primary`. O prefixo evita colisão com o hospedeiro. */
export function variaveisCss(tema: Record<string, string>): Record<string, string> {
  const saida: Record<string, string> = {};
  for (const [nome, valor] of Object.entries(tema)) saida[`--toc-${nome}`] = valor;
  return saida;
}

/** Aplica as variáveis no elemento raiz. Efeito de borda isolado, para o teste não precisar dele. */
export function aplicarTema(elemento: HTMLElement, tema: Record<string, string>, esquema: Esquema): void {
  for (const [nome, valor] of Object.entries(variaveisCss(tema))) {
    elemento.style.setProperty(nome, valor);
  }
  elemento.dataset.esquema = esquema;
}
