// Os quatro parâmetros de admissão do §B.4 do Anexo B do Padrão APH (Aplicação ↔ Harness),
// lidos de CONFIGURAÇÃO — nunca de mensagem, nunca perguntados ao usuário (§B.4.1).
import { describe, expect, it } from "vitest";
import { OBRIGATORIOS, lerAdmissao } from "./admissao";

const COMPLETO = {
  VITE_GHD_HOST_ORIGIN: "https://fundacao.exemplo",
  VITE_GHD_HOST_BASE_URL: "https://fundacao.exemplo/api",
  VITE_GHD_APP_ID: "toc",
  VITE_GHD_EMBED_URL: "https://toc-federada.exemplo/toc/embarcado",
};

describe("admissão (§B.4)", () => {
  it("lê os quatro parâmetros obrigatórios da configuração", () => {
    const admissao = lerAdmissao(COMPLETO);
    expect(admissao.admitida).toBe(true);
    if (!admissao.admitida) return;
    expect(admissao.hostOrigin).toBe("https://fundacao.exemplo");
    expect(admissao.hostBaseUrl).toBe("https://fundacao.exemplo/api");
    expect(admissao.appId).toBe("toc");
    expect(admissao.embedUrl).toBe("https://toc-federada.exemplo/toc/embarcado");
  });

  it.each(OBRIGATORIOS)("recusa a admissão nomeando %s quando ele falta", (variavel) => {
    const parcial = { ...COMPLETO, [variavel]: "" };
    const admissao = lerAdmissao(parcial);
    expect(admissao.admitida).toBe(false);
    if (admissao.admitida) return;
    // §B.4.1: "erro categorizado que diga QUAL faltou" — dizer "configuração incompleta"
    // sem nomear é a não-conformidade que a cláusula proíbe.
    expect(admissao.faltantes).toEqual([variavel]);
    expect(admissao.motivo).toContain(variavel);
  });

  it("lista TODOS os faltantes, não só o primeiro", () => {
    const admissao = lerAdmissao({ VITE_GHD_APP_ID: "toc" });
    expect(admissao.admitida).toBe(false);
    if (admissao.admitida) return;
    expect(admissao.faltantes).toEqual([
      "VITE_GHD_HOST_ORIGIN",
      "VITE_GHD_HOST_BASE_URL",
      "VITE_GHD_EMBED_URL",
    ]);
  });

  it("ignora espaço em branco: parâmetro só com espaços conta como ausente", () => {
    const admissao = lerAdmissao({ ...COMPLETO, VITE_GHD_HOST_ORIGIN: "   " });
    expect(admissao.admitida).toBe(false);
  });

  it("recusa origem que não seja uma origem (esquema + host, sem caminho)", () => {
    const admissao = lerAdmissao({ ...COMPLETO, VITE_GHD_HOST_ORIGIN: "fundacao.exemplo" });
    expect(admissao.admitida).toBe(false);
    if (admissao.admitida) return;
    expect(admissao.motivo).toContain("VITE_GHD_HOST_ORIGIN");
  });

  it("recusa `*` como origem admitida — o curinga é o defeito, não a configuração", () => {
    const admissao = lerAdmissao({ ...COMPLETO, VITE_GHD_HOST_ORIGIN: "*" });
    expect(admissao.admitida).toBe(false);
  });
});
