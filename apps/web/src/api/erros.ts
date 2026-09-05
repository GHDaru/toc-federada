/**
 * A recusa do serviço, do lado do cliente — discriminada por CÓDIGO, nunca por mensagem.
 *
 * Siglas, uma vez: **API** — interface de programação de aplicações · **HTTP** —
 * *HyperText Transfer Protocol* · **APH** — Aplicação ↔ Harness · **UDE** — Efeito
 * Indesejável.
 *
 * O serviço responde `{"error": {code, message, details?}}` (Anexo A §A.7 do Padrão APH),
 * com `code` em caixa alta e estável. A mensagem é para gente; o código é para máquina.
 * Uma interface que decide o que mostrar lendo a mensagem quebra na primeira revisão de
 * texto — e é assim que se perde compatibilidade sem mudar uma linha de contrato.
 */

export class ErroDaApi extends Error {
  readonly codigo: string;
  readonly status: number;
  readonly detalhes: Record<string, unknown> | undefined;

  constructor(
    codigo: string,
    mensagem: string,
    status: number,
    detalhes?: Record<string, unknown>,
  ) {
    super(mensagem);
    this.name = "ErroDaApi";
    this.codigo = codigo;
    this.status = status;
    this.detalhes = detalhes;
  }
}

export function ehErroDaApi(erro: unknown): erro is ErroDaApi {
  return erro instanceof ErroDaApi;
}

/**
 * Os códigos que a interface trata de forma diferente. Código fora desta lista cai no
 * tratamento genérico — e isso é de propósito: código novo do serviço não pode quebrar a
 * tela, só deixar de ter tratamento especial.
 */
export const CODIGOS = {
  NAO_AUTENTICADO: "UNAUTHENTICATED",
  SEM_CAPACIDADE: "UNAUTHORIZED",
  NAO_ENCONTRADO: "NOT_FOUND",
  ARGUMENTO_INVALIDO: "INVALID_ARGUMENT",
  ARESTA_INVALIDA: "INVALID_EDGE",
  CONECTOR_INVALIDO: "INVALID_CONNECTOR",
  TRANSICAO_INVALIDA: "INVALID_TRANSITION",
  MUTACAO_RECUSADA: "MUTATION_REFUSED",
  TOPOLOGIA_FIXA: "FIXED_TOPOLOGY",
  PREMISSA_INVALIDA: "INVALID_ASSUMPTION",
  INJECAO_INVALIDA: "INVALID_INJECTION",
  DERIVACAO_INVALIDA: "INVALID_DERIVATION",
  GERACAO_INVALIDA: "INVALID_GENERATION_RESULT",
  DOMINIO_RECUSOU: "DOMAIN_REFUSED",
  /** Nossos, do cliente: a rede e a resposta ilegível também precisam de nome. */
  REDE_INDISPONIVEL: "REDE_INDISPONIVEL",
  RESPOSTA_INVALIDA: "RESPOSTA_INVALIDA",
} as const;
