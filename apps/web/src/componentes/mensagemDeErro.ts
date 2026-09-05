/**
 * Traduz uma recusa em frase com PRÓXIMA AÇÃO — nunca texto cru de exceção (RI-12 da
 * spec 004).
 *
 * Siglas, uma vez: **API** — interface de programação de aplicações.
 *
 * A discriminação é pelo **código** (`erro.codigo`), que é estável, e não pela mensagem,
 * que é escrita para gente e muda com revisão de texto.
 */
import type { ChaveDeTraducao, Parametros } from "../i18n";

export interface ComCodigo {
  codigo?: string;
  message?: string;
}

export function codigoDoErro(erro: unknown): string {
  const codigo = (erro as ComCodigo)?.codigo;
  return typeof codigo === "string" && codigo ? codigo : "generico";
}

export function mensagemDeErro(
  erro: unknown,
  t: (chave: ChaveDeTraducao, parametros?: Parametros) => string,
): string {
  const codigo = codigoDoErro(erro);
  const chave = `erro.${codigo}` as ChaveDeTraducao;
  const traduzida = t(chave);
  // Código que a interface ainda não conhece cai no genérico — e o serviço pode publicar
  // código novo sem quebrar tela nenhuma.
  return traduzida === chave ? t("erro.generico") : traduzida;
}
