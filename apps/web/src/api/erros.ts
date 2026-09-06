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
  /** Outra pessoa gravou antes: `details.versao_atual` é a versão a recarregar. */
  CONFLITO_DE_VERSAO: "VERSION_CONFLICT",
  TOPOLOGIA_FIXA: "FIXED_TOPOLOGY",
  /** O estado é de uma ferramenta e a chamada não veio pela raiz do agregado dela. */
  EXIGE_RAIZ_DO_AGREGADO: "AGGREGATE_ROOT_REQUIRED",
  PREMISSA_INVALIDA: "INVALID_ASSUMPTION",
  INJECAO_INVALIDA: "INVALID_INJECTION",
  DERIVACAO_INVALIDA: "INVALID_DERIVATION",
  GERACAO_INVALIDA: "INVALID_GENERATION_RESULT",
  /* Os quatro da governança: a ação some do catálogo de quem não pode (§B.7.3), a
     proposta é de outro inquilino, ela venceu, ou a tela mudou entre propor e confirmar. */
  ACAO_INDISPONIVEL: "ACTION_NOT_FOUND",
  PROPOSTA_INEXISTENTE: "PROPOSAL_NOT_FOUND",
  PROPOSTA_VENCIDA: "PROPOSAL_EXPIRED",
  CONTEXTO_DEFASADO: "PROPOSAL_CONTEXT_STALE",
  /**
   * A chave de idempotência já produziu uma execução em OUTRA proposta deste inquilino
   * (APH-5.3). Tem tratamento próprio porque a saída é diferente da de `INVALID_TRANSITION`:
   * ali a pessoa recarrega a proposta; aqui ela sorteia outra chave e tenta de novo.
   */
  CHAVE_REAPROVEITADA: "IDEMPOTENCY_KEY_REUSED",
  DOMINIO_RECUSOU: "DOMAIN_REFUSED",
  /** Nossos, do cliente: a rede e a resposta ilegível também precisam de nome. */
  REDE_INDISPONIVEL: "REDE_INDISPONIVEL",
  RESPOSTA_INVALIDA: "RESPOSTA_INVALIDA",
} as const;
