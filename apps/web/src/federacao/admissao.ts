/**
 * Admissão — os quatro parâmetros do §B.4 do Anexo B do Padrão APH (Aplicação ↔ Harness).
 *
 * Siglas, uma vez: **APH** — Aplicação ↔ Harness · **URL** — *Uniform Resource Locator* ·
 * **CSS** — *Cascading Style Sheets*.
 *
 * Por que isto é um módulo e não quatro leituras de `import.meta.env` espalhadas: o §B.4.1
 * manda **recusar subir** quando falta parâmetro obrigatório, "com erro categorizado que
 * diga QUAL faltou". Uma leitura espalhada só sabe recusar onde ela acontece — e "subir
 * pela metade, funcionar até alguém clicar" é exatamente a não-conformidade nomeada.
 *
 * A origem do hospedeiro sai daqui e de lugar nenhum mais. Ler a origem esperada do
 * `payload` da mensagem — o contraexemplo que a norma registra no §B.2.3 — é circular:
 * quem envia escolheria contra o que ser conferido.
 */

/** As variáveis de configuração, na ordem em que a norma as lista (§B.4). */
export const OBRIGATORIOS = [
  "VITE_GHD_HOST_ORIGIN",
  "VITE_GHD_HOST_BASE_URL",
  "VITE_GHD_APP_ID",
  "VITE_GHD_EMBED_URL",
] as const;

export type VariavelDeAdmissao = (typeof OBRIGATORIOS)[number];

export interface Admitida {
  admitida: true;
  hostOrigin: string;
  hostBaseUrl: string;
  appId: string;
  embedUrl: string;
}

export interface Recusada {
  admitida: false;
  faltantes: VariavelDeAdmissao[];
  motivo: string;
}

export type Admissao = Admitida | Recusada;

export type Ambiente = Record<string, string | undefined>;

function texto(ambiente: Ambiente, chave: string): string {
  return (ambiente[chave] ?? "").trim();
}

/**
 * Uma origem é `esquema://host[:porta]` e mais nada — sem caminho, sem barra final.
 * O `URL.origin` do próprio navegador é o juiz, e a comparação por igualdade que o
 * §B.2.3 exige só é confiável se o que está em configuração já for uma origem.
 */
export function origemValida(bruto: string): boolean {
  if (!bruto || bruto === "*") return false;
  try {
    const url = new URL(bruto);
    if (url.origin === "null") return false;
    return url.origin === bruto.replace(/\/$/, "");
  } catch {
    return false;
  }
}

export function lerAdmissao(ambiente: Ambiente): Admissao {
  const faltantes = OBRIGATORIOS.filter((chave) => !texto(ambiente, chave));
  if (faltantes.length) {
    return {
      admitida: false,
      faltantes: [...faltantes],
      motivo:
        "embarque recusado: faltam parâmetros de admissão (§B.4.1) — " +
        faltantes.join(", "),
    };
  }
  const hostOrigin = texto(ambiente, "VITE_GHD_HOST_ORIGIN");
  if (!origemValida(hostOrigin)) {
    return {
      admitida: false,
      faltantes: [],
      motivo:
        "embarque recusado: VITE_GHD_HOST_ORIGIN não é uma origem " +
        `(esquema://host[:porta], sem caminho e sem curinga): ${hostOrigin}`,
    };
  }
  return {
    admitida: true,
    hostOrigin,
    hostBaseUrl: texto(ambiente, "VITE_GHD_HOST_BASE_URL"),
    appId: texto(ambiente, "VITE_GHD_APP_ID"),
    embedUrl: texto(ambiente, "VITE_GHD_EMBED_URL"),
  };
}
