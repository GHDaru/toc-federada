// O embarque: quem fala primeiro, contra o que se confere, o que se renderiza.
//
// Cada teste deste arquivo é um DEFEITO MEDIDO no protótipo da aplicação irmã
// `gestaodeprioridades` e registrado no Anexo B do Padrão APH (Aplicação ↔ Harness):
// envelope `{tipo, versao}` [F-02], `postMessage(..., "*")` [F-04], `event.source` nunca
// conferido [F-05], modo embarcado por heurística de `window.parent` [B.8.2].
import { afterEach, describe, expect, it, vi } from "vitest";
import { iniciarFederacao, modoDeEmbarqueDaUrl, deveRenderizarCasca, JANELA_DO_HANDSHAKE_MS } from "./embarque";
import type { Sessao } from "./embarque";

const AMBIENTE = {
  VITE_GHD_HOST_ORIGIN: "https://fundacao.exemplo",
  VITE_GHD_HOST_BASE_URL: "https://fundacao.exemplo/api",
  VITE_GHD_APP_ID: "toc",
  VITE_GHD_EMBED_URL: "https://toc.exemplo/toc/embarcado",
};

const URL_EMBARCADA = "https://toc.exemplo/toc/embarcado?embarcado=1";
const URL_AUTONOMA = "https://toc.exemplo/toc/projetos";

const SESSAO: Sessao = {
  token: "ses-abc",
  usuario: { id: "usr-facilitadora", nome: "Facilitadora TOC" },
  tenantId: "inq-horizonte",
  capabilities: ["toc:read", "toc:write"],
  expiraEm: null,
};

const PAI = { nome: "janela-do-hospedeiro" };

function handshake(payload: Record<string, unknown> = {}) {
  return {
    source: PAI,
    origin: "https://fundacao.exemplo",
    data: {
      protocol: "ghd",
      v: 1,
      type: "ghd.handshake",
      payload: {
        token: "ghdg_grant_de_uso_unico",
        tenant: { id: "inq-horizonte", name: "Instituição Horizonte" },
        capabilities: ["toc:read", "toc:write"],
        theme: { tokens: { "color-primary": "#7c3aed" } },
        ...payload,
      },
    },
  };
}

function montar(opcoes: Partial<Parameters<typeof iniciarFederacao>[0]> = {}) {
  const enviar = vi.fn();
  const trocarGrant = vi.fn(async () => SESSAO);
  const federacao = iniciarFederacao({
    ambiente: AMBIENTE,
    url: URL_EMBARCADA,
    pai: PAI,
    enviar,
    trocarGrant,
    esquemaPreferido: "claro",
    ...opcoes,
  });
  return { federacao, enviar, trocarGrant };
}

afterEach(() => vi.useRealTimers());

describe("modo embarcado (§B.8.2)", () => {
  it("é decidido por sinal explícito na URL", () => {
    expect(modoDeEmbarqueDaUrl(URL_EMBARCADA)).toBe("embarcado");
    expect(modoDeEmbarqueDaUrl("https://toc.exemplo/x?embarcado=true")).toBe("embarcado");
    expect(modoDeEmbarqueDaUrl(URL_AUTONOMA)).toBe("autonomo");
  });

  it("NUNCA por heurística de janela: pai diferente de si não embarca nada", () => {
    const { federacao, enviar } = montar({ url: URL_AUTONOMA, pai: PAI });
    expect(federacao.estado().modo).toBe("autonomo");
    expect(federacao.estado().fase).toBe("autonomo");
    // Autônoma não fala no canal: `postMessage` sem embarque é ruído endereçado a um
    // hospedeiro que não pediu nada.
    expect(enviar).not.toHaveBeenCalled();
  });

  it("renderiza a casca própria só fora do embarque (§B.8.1)", () => {
    expect(deveRenderizarCasca({ modo: "autonomo" })).toBe(true);
    expect(deveRenderizarCasca({ modo: "embarcado" })).toBe(false);
  });
});

describe("a aplicação fala primeiro (§B.2.2)", () => {
  it("emite ghd.ready ao montar, com o envelope fechado e o app_id em snake_case", () => {
    const { enviar } = montar();
    expect(enviar).toHaveBeenCalledTimes(1);
    const [mensagem, destino] = enviar.mock.calls[0]!;
    expect(mensagem).toEqual({
      protocol: "ghd",
      v: 1,
      type: "ghd.ready",
      payload: { app_id: "toc" },
    });
    expect(Object.keys(mensagem as object)).toHaveLength(4);
    expect(destino).toBe("https://fundacao.exemplo");
  });

  it("endereça o targetOrigin, nunca `*` — em nenhuma mensagem do fluxo inteiro", async () => {
    const { federacao, enviar } = montar();
    await federacao.aoReceber(handshake());
    for (const [, destino] of enviar.mock.calls) {
      expect(destino).not.toBe("*");
      expect(destino).toBe("https://fundacao.exemplo");
    }
  });

  it("recusa subir embarcada sem os parâmetros de admissão, e não fala no canal", () => {
    const { federacao, enviar } = montar({
      ambiente: { ...AMBIENTE, VITE_GHD_HOST_ORIGIN: "" },
    });
    expect(federacao.estado().fase).toBe("recusada");
    expect(federacao.estado().motivo).toContain("VITE_GHD_HOST_ORIGIN");
    expect(enviar).not.toHaveBeenCalled();
  });
});

describe("a trava dupla antes de qualquer efeito (§B.2.3)", () => {
  it("descarta handshake de origem não admitida, sem trocar grant e sem responder", async () => {
    const { federacao, enviar, trocarGrant } = montar();
    enviar.mockClear();
    const intruso = { ...handshake(), origin: "https://invasor.exemplo" };
    await federacao.aoReceber(intruso);
    expect(trocarGrant).not.toHaveBeenCalled();
    expect(enviar).not.toHaveBeenCalled();
    expect(federacao.estado().fase).toBe("aguardando_handshake");
    expect(federacao.estado().descartes[0]?.motivo).toBe("ORIGEM_NAO_ADMITIDA");
  });

  it("descarta handshake de outra janela mesmo com a origem certa", async () => {
    const { federacao, trocarGrant } = montar();
    await federacao.aoReceber({ ...handshake(), source: { outra: true } });
    expect(trocarGrant).not.toHaveBeenCalled();
    expect(federacao.estado().descartes[0]?.motivo).toBe("FONTE_NAO_ADMITIDA");
  });

  it("descarta o envelope da linhagem irmã — {tipo, versao, payload}", async () => {
    const { federacao, trocarGrant } = montar();
    await federacao.aoReceber({
      source: PAI,
      origin: "https://fundacao.exemplo",
      data: { tipo: "ghd.handshake", versao: 1, payload: { token: "x" } },
    });
    expect(trocarGrant).not.toHaveBeenCalled();
    expect(federacao.estado().descartes[0]?.motivo).toBe("ENVELOPE_INVALIDO");
  });

  it("ignora `type` desconhecido sem quebrar (evolução aditiva §B.2.5)", async () => {
    const { federacao } = montar();
    await federacao.aoReceber({
      source: PAI,
      origin: "https://fundacao.exemplo",
      data: { protocol: "ghd", v: 1, type: "ghd.inventado", payload: {} },
    });
    expect(federacao.estado().fase).toBe("aguardando_handshake");
    expect(federacao.estado().descartes[0]?.motivo).toBe("TIPO_DESCONHECIDO");
  });

  it("nunca lê a origem esperada do payload — origem vem de configuração", async () => {
    const { federacao, trocarGrant } = montar();
    await federacao.aoReceber({
      source: PAI,
      origin: "https://invasor.exemplo",
      data: {
        protocol: "ghd",
        v: 1,
        type: "ghd.handshake",
        payload: { token: "x", host_origin: "https://invasor.exemplo" },
      },
    });
    expect(trocarGrant).not.toHaveBeenCalled();
  });
});

describe("o grant vira identidade (§B.6)", () => {
  it("troca o grant imediatamente e guarda a SESSÃO, nunca o grant", async () => {
    const { federacao, trocarGrant } = montar();
    await federacao.aoReceber(handshake());
    expect(trocarGrant).toHaveBeenCalledWith("ghdg_grant_de_uso_unico");
    const estado = federacao.estado();
    expect(estado.fase).toBe("pronta");
    expect(estado.sessao?.token).toBe("ses-abc");
    expect(JSON.stringify(estado)).not.toContain("ghdg_grant_de_uso_unico");
    expect(estado.inquilino).toEqual({ id: "inq-horizonte", nome: "Instituição Horizonte" });
  });

  it("veste o tema do inquilino com fallback próprio no que não veio", async () => {
    const { federacao } = montar();
    await federacao.aoReceber(handshake());
    const { tema } = federacao.estado();
    expect(tema.resolvido["color-primary"]).toBe("#7c3aed");
    expect(tema.resolvido["color-text"]).toMatch(/\S/);
    expect(tema.usados).toEqual(["color-primary"]);
  });

  it("segue em modo ANÔNIMO quando a introspecção recusa (§B.3.1), sem falhar", async () => {
    const { federacao } = montar({
      trocarGrant: vi.fn(async () => {
        throw new Error("introspecção recusou");
      }),
    });
    await federacao.aoReceber(handshake());
    const estado = federacao.estado();
    expect(estado.fase).toBe("anonima");
    expect(estado.sessao).toBeNull();
    expect(estado.motivo).toMatch(/an[oô]nim/i);
  });

  it("passa a anônima quando o handshake não chega na janela declarada (§B.3.2)", () => {
    vi.useFakeTimers();
    const { federacao } = montar();
    expect(federacao.estado().fase).toBe("aguardando_handshake");
    vi.advanceTimersByTime(JANELA_DO_HANDSHAKE_MS + 1);
    expect(federacao.estado().fase).toBe("anonima");
  });

  it("avisa quem escuta a cada mudança de estado", async () => {
    const { federacao } = montar();
    const ouvinte = vi.fn();
    federacao.assinar(ouvinte);
    await federacao.aoReceber(handshake());
    expect(ouvinte).toHaveBeenCalled();
    expect(ouvinte.mock.lastCall?.[0].fase).toBe("pronta");
  });

  it("trata ghd.resource_changed como pedido de recarga, não como comando", async () => {
    const recarregar = vi.fn();
    const { federacao } = montar({ aoMudarRecurso: recarregar });
    await federacao.aoReceber({
      source: PAI,
      origin: "https://fundacao.exemplo",
      data: { protocol: "ghd", v: 1, type: "ghd.resource_changed", payload: {} },
    });
    expect(recarregar).toHaveBeenCalledTimes(1);
  });
});
