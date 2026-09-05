// canal.mjs — o canal `ghd.*` do lado da aplicação (Anexo B §B.2, spec 003 E7.2).
//
// Siglas, uma vez: APH — Aplicação ↔ Harness (o padrão da fronteira) · URL — Uniform
// Resource Locator · CSS — Cascading Style Sheets · DOM — Document Object Model.
//
// POR QUE ISTO É JAVASCRIPT PURO, SEM FRAMEWORK E SEM BUILD
// --------------------------------------------------------
// As três regras que este arquivo implementa são as que a norma registrou como DEFEITO
// MEDIDO no protótipo da aplicação irmã `gestaodeprioridades`:
//
//   [F-02] envelope `{tipo, versao, payload}` em vez de `{protocol, v, type, payload}`
//          — "hoje a junta não fecharia" (anexo-b-federacao.md:52);
//   [F-04] `parent.postMessage(pronto, "*")` tendo `HOST_ORIGIN` em mãos (linha 62);
//   [F-05] `ev.source === parent` **não existe** lá (linha 23).
//
// Regra que se prova com teste vale mais do que regra que se lembra — e um módulo sem
// dependência de framework é testável por `node --test` sem instalar nada, o que faz o
// portão rodar em qualquer máquina e em qualquer ordem de construção da interface. Quem
// montar o React em volta liga `criarCanal` a `window.addEventListener("message", …)`; as
// regras não mudam de lugar quando a interface mudar de biblioteca.

/** O envelope canônico do §B.2.1 — exatamente quatro campos, nesta ordem de leitura. */
export const PROTOCOLO = "ghd";
export const VERSAO = 1;

/** Motivos de descarte. Viram log estruturado e métrica (RF-23), nunca resposta. */
export const DESCARTES = Object.freeze({
  FONTE_NAO_ADMITIDA: "FONTE_NAO_ADMITIDA",
  ORIGEM_NAO_ADMITIDA: "ORIGEM_NAO_ADMITIDA",
  ENVELOPE_INVALIDO: "ENVELOPE_INVALIDO",
  TIPO_DESCONHECIDO: "TIPO_DESCONHECIDO",
});

/** Vocabulário consumido nos ciclos 003 e 006 (§B.3). `type` fora daqui é ignorado. */
export const TIPOS_ACEITOS = Object.freeze(["ghd.handshake", "ghd.resource_changed"]);

/** Janela de espera do handshake — a mesma do laboratório (§B.3.2). */
export const JANELA_DO_HANDSHAKE_MS = 6000;

/**
 * Monta um envelope do §B.2.1. Exatamente quatro campos: nem um a mais.
 * @param {string} type
 * @param {object} payload
 */
export function envelope(type, payload = {}) {
  return { protocol: PROTOCOLO, v: VERSAO, type, payload };
}

/**
 * O envelope é FECHADO (§B.2.5): quatro campos, `protocol` constante, `v` inteiro.
 * O `payload` é aberto — campo novo nele é mudança compatível.
 */
export function envelopeValido(mensagem) {
  if (mensagem === null || typeof mensagem !== "object" || Array.isArray(mensagem)) return false;
  const chaves = Object.keys(mensagem).sort();
  if (chaves.length !== 4) return false;
  if (chaves.join(",") !== "payload,protocol,type,v") return false;
  if (mensagem.protocol !== PROTOCOLO) return false;
  if (typeof mensagem.v !== "number" || !Number.isInteger(mensagem.v) || mensagem.v !== VERSAO) return false;
  if (typeof mensagem.type !== "string" || !mensagem.type) return false;
  const p = mensagem.payload;
  return p !== null && typeof p === "object" && !Array.isArray(p);
}

/**
 * A trava dupla do §B.2.3, **nesta ordem**: (1) `event.source`, (2) `event.origin` por
 * igualdade com a origem de CONFIGURAÇÃO, (3) só então o conteúdo.
 *
 * A ordem não é estética. Olhar o conteúdo antes já é processar dado de terceiro; e ler a
 * origem esperada do próprio payload — o contraexemplo `payload.host_origin` registrado na
 * norma — é circular, porque quem envia escolheria contra o que ser conferido.
 *
 * @returns {{admitida: true, mensagem: object} | {admitida: false, motivo: string}}
 */
export function avaliarMensagem(evento, { hostOrigin, pai }) {
  if (!hostOrigin) {
    // Sem origem admitida não há o que conferir — e conferir contra `undefined` passaria.
    return { admitida: false, motivo: DESCARTES.ORIGEM_NAO_ADMITIDA };
  }
  if (evento.source !== pai) {
    return { admitida: false, motivo: DESCARTES.FONTE_NAO_ADMITIDA };
  }
  // `"null"` é a origem de qualquer documento opaco (sandbox sem `allow-same-origin`,
  // `data:`, `srcdoc`): nunca admitida, em caso nenhum (§B.2.3).
  if (evento.origin === "null" || evento.origin !== hostOrigin) {
    return { admitida: false, motivo: DESCARTES.ORIGEM_NAO_ADMITIDA };
  }
  if (!envelopeValido(evento.data)) {
    return { admitida: false, motivo: DESCARTES.ENVELOPE_INVALIDO };
  }
  if (!TIPOS_ACEITOS.includes(evento.data.type)) {
    // Evolução aditiva (§B.2.5): `type` desconhecido é IGNORADO, sem efeito e sem
    // resposta. Quebrar por mensagem nova é defeito, não rigor.
    return { admitida: false, motivo: DESCARTES.TIPO_DESCONHECIDO };
  }
  return { admitida: true, mensagem: evento.data };
}

/**
 * Aplica `theme.tokens` por LISTA DE PERMISSÃO e cobre o que faltar com o tema próprio.
 * Tokens são parciais por desenho (§B.4.3): elemento sem cor definida é defeito nosso,
 * não do inquilino.
 *
 * @param {object} tokensRecebidos  o que veio no handshake
 * @param {string[]} permitidos     os tokens que o manifesto declara consumir
 * @param {object} temaProprio      o fallback completo
 */
export function resolverTema(tokensRecebidos, permitidos, temaProprio) {
  const resolvido = {};
  const usados = [];
  const ignorados = [];
  for (const nome of permitidos) {
    const doInquilino = tokensRecebidos && typeof tokensRecebidos === "object"
      ? tokensRecebidos[nome]
      : undefined;
    if (typeof doInquilino === "string" && doInquilino.trim()) {
      resolvido[nome] = doInquilino;
      usados.push(nome);
    } else {
      resolvido[nome] = temaProprio[nome];
    }
  }
  for (const nome of Object.keys(tokensRecebidos || {})) {
    if (!permitidos.includes(nome)) ignorados.push(nome);
  }
  const semCor = permitidos.filter((n) => resolvido[n] === undefined);
  if (semCor.length) {
    throw new Error(
      `tema próprio incompleto: sem valor de fallback para ${semCor.join(", ")} — ` +
        "token ausente do inquilino nunca pode deixar elemento sem cor definida (§B.4.3)",
    );
  }
  return { resolvido, usados, ignorados };
}

/**
 * Modo embarcado por SINAL EXPLÍCITO na URL (§B.8.2), nunca por heurística de
 * `window.parent !== window`. A heurística mente em dois sentidos: um iframe de
 * desenvolvimento parece embarque, e um embarque de janela única parece autônomo.
 */
export function modoDeEmbarque(url, { parametro = "embarcado" } = {}) {
  try {
    const valor = new URL(url).searchParams.get(parametro);
    return valor === "1" || valor === "true" ? "embarcado" : "autonomo";
  } catch {
    return "autonomo";
  }
}

/**
 * O canal. Recebe TUDO por injeção — origem, janela pai, função de envio e sumidouro de
 * log — para o teste rodar sem DOM e para a origem NUNCA vir de mensagem.
 */
export function criarCanal({ hostOrigin, appId, pai, enviar, registrar = () => {} }) {
  const descartes = [];

  function postar(type, payload = {}) {
    // §B.2.4: `targetOrigin` dirigido, sempre. `"*"` revelaria a qualquer embarcador que
    // a aplicação está ali e em que estado — inclusive numa mensagem sem segredo.
    enviar(envelope(type, payload), hostOrigin);
  }

  return {
    /** §B.2.2: a aplicação fala primeiro, com `{app_id}` (snake_case, §B.2.1). */
    anunciarPronto() {
      postar("ghd.ready", { app_id: appId });
    },
    aoReceber(evento) {
      const veredito = avaliarMensagem(evento, { hostOrigin, pai });
      if (!veredito.admitida) {
        // RF-23: registra (origem ofensora truncada, SEM payload) e conta em métrica —
        // e **não responde**, porque responder já confirma presença (§B.2.1).
        const registro = {
          motivo: veredito.motivo,
          origem: String(evento.origin ?? "").slice(0, 64),
        };
        descartes.push(registro);
        registrar(registro);
        return null;
      }
      return veredito.mensagem;
    },
    postar,
    get descartes() {
      return descartes.slice();
    },
  };
}
