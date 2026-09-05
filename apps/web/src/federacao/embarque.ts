/**
 * Embarque — a máquina do lado da aplicação: quem fala primeiro, contra o que se confere,
 * o que se renderiza e como o grant vira identidade.
 *
 * Siglas, uma vez: **APH** — Aplicação ↔ Harness (o padrão da fronteira) · **URL** —
 * *Uniform Resource Locator* · **UI** — interface de usuário.
 *
 * As regras do canal (envelope fechado, trava dupla `source`+`origin`, `targetOrigin`
 * dirigido, tema por lista de permissão) já vivem em `canal.mjs`, que é JavaScript puro
 * porque o portão `scripts/check-canal.sh` o roda com `node --test`, sem build. Este
 * módulo **usa** aquelas regras; não as reescreve. Duas implementações da mesma regra é
 * como uma delas fica para trás.
 *
 * O que este módulo acrescenta ao canal:
 *
 * - a admissão do §B.4 (recusar subir nomeando o parâmetro que faltou);
 * - a sequência do §B.6 (o grant de uso único vira sessão **imediatamente**, e o grant
 *   não é guardado — ele nunca funciona como bearer);
 * - o §B.3.1 (credencial não emitida ⇒ **modo anônimo**, não falha fatal);
 * - o §B.3.2 (silêncio do hospedeiro dentro da janela ⇒ estado honesto, não erro).
 */
import { criarCanal, modoDeEmbarque } from "./canal.mjs";
import { lerAdmissao, type Admissao, type Ambiente } from "./admissao";
import { resolverTemaDoInquilino, type Esquema, type TemaResolvido } from "./tema";

/** A janela do §B.3.2 — a mesma do laboratório da norma. */
export const JANELA_DO_HANDSHAKE_MS = 6000;

export type Modo = "embarcado" | "autonomo";

/**
 * As fases, e o que cada uma significa para a tela:
 * `autonomo` — fora de embarque, com a casca própria;
 * `aguardando_handshake` — `ghd.ready` emitido, esperando resposta;
 * `pronta` — identidade estabelecida;
 * `anonima` — embarcada e sem identidade: conteúdo sem dado de usuário (§B.3.1);
 * `recusada` — admissão incompleta: a aplicação **não sobe** (§B.4.1).
 */
export type Fase = "autonomo" | "aguardando_handshake" | "pronta" | "anonima" | "recusada";

export interface Sessao {
  token: string;
  usuario: { id: string; nome: string };
  tenantId: string;
  capabilities: string[];
  expiraEm: string | null;
}

export interface Descarte {
  motivo: string;
  origem: string;
}

export interface EstadoDaFederacao {
  modo: Modo;
  fase: Fase;
  motivo: string;
  sessao: Sessao | null;
  inquilino: { id: string; nome: string } | null;
  tema: TemaResolvido;
  esquema: Esquema;
  descartes: Descarte[];
}

export interface DependenciasDaFederacao {
  ambiente: Ambiente;
  url: string;
  /** `window.parent`. Injetado para o teste rodar sem navegador. */
  pai: unknown;
  enviar: (mensagem: unknown, targetOrigin: string) => void;
  /** Troca o grant de uso único por identidade — `POST /toc/embarque` no nosso serviço. */
  trocarGrant: (grant: string) => Promise<Sessao>;
  esquemaPreferido?: Esquema;
  aoMudarRecurso?: () => void;
  registrar?: (descarte: Descarte) => void;
}

export interface Federacao {
  estado(): EstadoDaFederacao;
  assinar(ouvinte: (estado: EstadoDaFederacao) => void): () => void;
  aoReceber(evento: { source?: unknown; origin?: string; data?: unknown }): Promise<void>;
  encerrar(): void;
}

/** §B.8.2: sinal explícito na URL. A heurística `window.parent !== window` mente nos dois sentidos. */
export function modoDeEmbarqueDaUrl(url: string): Modo {
  return modoDeEmbarque(url) as Modo;
}

/** §B.8.1: embarcada, a aplicação renderiza **apenas o conteúdo** — quem navega é o hospedeiro. */
export function deveRenderizarCasca(estado: { modo: Modo }): boolean {
  return estado.modo !== "embarcado";
}

function payloadDe(mensagem: unknown): Record<string, unknown> {
  const p = (mensagem as { payload?: unknown })?.payload;
  return p && typeof p === "object" ? (p as Record<string, unknown>) : {};
}

export function iniciarFederacao(deps: DependenciasDaFederacao): Federacao {
  const esquema: Esquema = deps.esquemaPreferido ?? "claro";
  const modo = modoDeEmbarqueDaUrl(deps.url);
  const admissao: Admissao = lerAdmissao(deps.ambiente);
  const ouvintes = new Set<(estado: EstadoDaFederacao) => void>();
  let temporizador: ReturnType<typeof setTimeout> | null = null;

  let estado: EstadoDaFederacao = {
    modo,
    fase: "autonomo",
    motivo: "",
    sessao: null,
    inquilino: null,
    tema: resolverTemaDoInquilino(null, esquema),
    esquema,
    descartes: [],
  };

  function mudar(parcial: Partial<EstadoDaFederacao>): void {
    estado = { ...estado, ...parcial };
    for (const ouvinte of ouvintes) ouvinte(estado);
  }

  // Autônoma: nada de canal. A aplicação não fala com um hospedeiro que não a embarcou.
  if (modo === "autonomo") {
    return {
      estado: () => estado,
      assinar(ouvinte) {
        ouvintes.add(ouvinte);
        return () => ouvintes.delete(ouvinte);
      },
      async aoReceber() {
        /* fora do embarque não há canal: mensagem nenhuma tem efeito */
      },
      encerrar() {
        ouvintes.clear();
      },
    };
  }

  // §B.4.1: falta parâmetro obrigatório ⇒ recusa de subir, nomeando qual. E, crucialmente,
  // **sem** emitir `ghd.ready`: sem origem admitida não há a quem endereçar, e endereçar a
  // `"*"` para "pelo menos tentar" é a violação do §B.2.4 disfarçada de resiliência.
  if (!admissao.admitida) {
    estado = { ...estado, fase: "recusada", motivo: admissao.motivo };
    return {
      estado: () => estado,
      assinar(ouvinte) {
        ouvintes.add(ouvinte);
        return () => ouvintes.delete(ouvinte);
      },
      async aoReceber() {
        /* recusada não processa mensagem */
      },
      encerrar() {
        ouvintes.clear();
      },
    };
  }

  const canal = criarCanal({
    hostOrigin: admissao.hostOrigin,
    appId: admissao.appId,
    pai: deps.pai,
    enviar: deps.enviar,
    registrar: (registro: Descarte) => {
      estado = { ...estado, descartes: [...estado.descartes, registro] };
      deps.registrar?.(registro);
    },
  });

  // §B.2.2 — a aplicação fala primeiro, e antes de qualquer outra coisa.
  canal.anunciarPronto();
  estado = { ...estado, fase: "aguardando_handshake" };

  temporizador = setTimeout(() => {
    if (estado.fase === "aguardando_handshake") {
      // §B.3.2: silêncio do hospedeiro é estado honesto — a aplicação segue anônima, com
      // conteúdo e sem dado de usuário, em vez de mostrar erro fatal a quem só quer ler.
      mudar({
        fase: "anonima",
        motivo: "o hospedeiro não respondeu na janela declarada; seguindo anônima (§B.3.2)",
      });
    }
  }, JANELA_DO_HANDSHAKE_MS);

  async function aoReceber(evento: {
    source?: unknown;
    origin?: string;
    data?: unknown;
  }): Promise<void> {
    const mensagem = canal.aoReceber(evento);
    if (!mensagem) return; // descartada: registrada, sem resposta (§B.2.3)

    const tipo = (mensagem as { type: string }).type;
    if (tipo === "ghd.resource_changed") {
      deps.aoMudarRecurso?.();
      return;
    }
    if (tipo !== "ghd.handshake") return;

    const payload = payloadDe(mensagem);
    const inquilinoBruto = (payload.tenant ?? {}) as { id?: string; name?: string };
    const temaBruto = (payload.theme ?? {}) as { tokens?: Record<string, string> };
    const tema = resolverTemaDoInquilino(temaBruto.tokens, estado.esquema);
    const inquilino = inquilinoBruto.id
      ? { id: String(inquilinoBruto.id), nome: String(inquilinoBruto.name ?? "") }
      : null;

    const grant = typeof payload.token === "string" ? payload.token : "";
    if (!grant) {
      mudar({
        fase: "anonima",
        motivo: "handshake sem grant; seguindo anônima (§B.3.1)",
        tema,
        inquilino,
      });
      return;
    }

    try {
      // §B.6: o grant é de uso único e TTL curto — troca-se imediatamente. Ele não entra
      // no estado: guardar o grant é o começo de usá-lo como bearer, que ele nunca é.
      const sessao = await deps.trocarGrant(grant);
      if (temporizador) clearTimeout(temporizador);
      mudar({ fase: "pronta", motivo: "", sessao, inquilino, tema });
    } catch (erro) {
      if (temporizador) clearTimeout(temporizador);
      mudar({
        fase: "anonima",
        sessao: null,
        inquilino,
        tema,
        motivo:
          "a identidade não pôde ser estabelecida; seguindo anônima (§B.3.1): " +
          (erro instanceof Error ? erro.message : String(erro)),
      });
    }
  }

  return {
    estado: () => estado,
    assinar(ouvinte) {
      ouvintes.add(ouvinte);
      return () => ouvintes.delete(ouvinte);
    },
    aoReceber,
    encerrar() {
      if (temporizador) clearTimeout(temporizador);
      ouvintes.clear();
    },
  };
}
