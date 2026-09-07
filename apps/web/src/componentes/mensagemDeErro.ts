/**
 * Traduz uma recusa em frase com PRÓXIMA AÇÃO — nunca texto cru de exceção (RI-12 da
 * spec 004).
 *
 * Siglas, uma vez: **API** — interface de programação de aplicações.
 *
 * A discriminação é pelo **código** (`erro.codigo`), que é estável, e não pela mensagem,
 * que é escrita para gente e muda com revisão de texto.
 */
import { CODIGOS } from "../api/erros";
import type { ChaveDeTraducao, Parametros } from "../i18n";

/**
 * Os códigos com texto próprio no dicionário. É a MESMA lista que a interface discrimina
 * (`api/erros.ts`), e o teste de paridade exige que cada um tenha entrada em `pt.erro` e
 * em `en.erro`.
 *
 * Por que a lista existe aqui, e não um `try` em volta da tradução: desde o ciclo 011 a
 * chave ausente **lança** em desenvolvimento (RF-09 da spec 011), e montar
 * `erro.${codigo}` com um código que o serviço acabou de publicar derrubaria a tela em
 * cima de uma recusa que o próprio serviço já explicou. Conferir a lista antes mantém as
 * duas coisas: chave de tela é vocabulário fechado (falha alto), código de servidor é
 * vocabulário aberto (cai no genérico).
 */
const COM_TEXTO_PROPRIO: ReadonlySet<string> = new Set(Object.values(CODIGOS));

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
  // Código que a interface ainda não conhece cai no genérico — e o serviço pode publicar
  // código novo sem quebrar tela nenhuma.
  if (!COM_TEXTO_PROPRIO.has(codigo)) return t("erro.generico");
  return t(`erro.${codigo}` as ChaveDeTraducao);
}
