/**
 * Tipos do `canal.mjs`.
 *
 * O canal é JavaScript puro **de propósito**: o portão `scripts/check-canal.sh` o roda com
 * `node --test`, sem build e sem instalar nada, e continua rodando quando a interface
 * mudar de biblioteca. Esta declaração é a ponte para o TypeScript — ela descreve o que
 * o módulo já faz, e não acrescenta comportamento nenhum.
 */
export const PROTOCOLO: "ghd";
export const VERSAO: 1;
export const DESCARTES: Readonly<{
  FONTE_NAO_ADMITIDA: "FONTE_NAO_ADMITIDA";
  ORIGEM_NAO_ADMITIDA: "ORIGEM_NAO_ADMITIDA";
  ENVELOPE_INVALIDO: "ENVELOPE_INVALIDO";
  TIPO_DESCONHECIDO: "TIPO_DESCONHECIDO";
}>;
export const TIPOS_ACEITOS: readonly string[];
export const JANELA_DO_HANDSHAKE_MS: number;

export interface EnvelopeGhd {
  protocol: "ghd";
  v: 1;
  type: string;
  payload: Record<string, unknown>;
}

export interface EventoDeMensagem {
  source?: unknown;
  origin?: string;
  data?: unknown;
}

export interface RegistroDeDescarte {
  motivo: string;
  origem: string;
}

export function envelope(type: string, payload?: Record<string, unknown>): EnvelopeGhd;
export function envelopeValido(mensagem: unknown): boolean;
export function avaliarMensagem(
  evento: EventoDeMensagem,
  opcoes: { hostOrigin: string; pai: unknown },
): { admitida: true; mensagem: EnvelopeGhd } | { admitida: false; motivo: string };
export function resolverTema(
  tokensRecebidos: Record<string, string> | null | undefined,
  permitidos: readonly string[],
  temaProprio: Record<string, string>,
): { resolvido: Record<string, string>; usados: string[]; ignorados: string[] };
export function modoDeEmbarque(url: string, opcoes?: { parametro?: string }): "embarcado" | "autonomo";
export function criarCanal(opcoes: {
  hostOrigin: string;
  appId: string;
  pai: unknown;
  enviar: (mensagem: EnvelopeGhd, targetOrigin: string) => void;
  registrar?: (registro: RegistroDeDescarte) => void;
}): {
  anunciarPronto(): void;
  aoReceber(evento: EventoDeMensagem): EnvelopeGhd | null;
  postar(type: string, payload?: Record<string, unknown>): void;
  readonly descartes: RegistroDeDescarte[];
};
