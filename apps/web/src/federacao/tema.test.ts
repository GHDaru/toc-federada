// Tema: os tokens do inquilino entram por LISTA DE PERMISSÃO e o fallback próprio cobre
// obrigatoriamente o que faltar (§B.4.3, RI-06/RI-07 da spec 002).
import { describe, expect, it } from "vitest";
import { TOKENS_CONSUMIDOS, temaProprio, resolverTemaDoInquilino, variaveisCss } from "./tema";

describe("tema (§B.4.3)", () => {
  it("consome exatamente os tokens que o manifesto declara em theme.tokens_used", () => {
    // A lista não é escolha de gosto: é o contrato publicado no manifesto da aplicação.
    expect([...TOKENS_CONSUMIDOS].sort()).toEqual([
      "color-danger",
      "color-primary",
      "color-surface",
      "color-text",
    ]);
  });

  it("tem tema próprio COMPLETO nos dois esquemas — nenhum token sem cor", () => {
    for (const esquema of ["claro", "escuro"] as const) {
      const proprio = temaProprio(esquema);
      for (const token of TOKENS_CONSUMIDOS) {
        expect(proprio[token], `${esquema}/${token}`).toMatch(/\S/);
      }
    }
  });

  it("veste o token do inquilino e cobre o ausente com o fallback próprio", () => {
    const { resolvido, usados, ignorados } = resolverTemaDoInquilino(
      { "color-primary": "#7c3aed" },
      "claro",
    );
    expect(resolvido["color-primary"]).toBe("#7c3aed");
    expect(resolvido["color-text"]).toBe(temaProprio("claro")["color-text"]);
    expect(usados).toEqual(["color-primary"]);
    expect(ignorados).toEqual([]);
  });

  it("ignora token fora da lista de permissão, sem quebrar", () => {
    const { resolvido, ignorados } = resolverTemaDoInquilino(
      { "color-primary": "#7c3aed", "color-secreta": "#000" },
      "claro",
    );
    expect(resolvido).not.toHaveProperty("color-secreta");
    expect(ignorados).toEqual(["color-secreta"]);
  });

  it("ignora valor vazio ou não-texto do inquilino — buraco sem cor é defeito nosso", () => {
    const { resolvido, usados } = resolverTemaDoInquilino(
      { "color-primary": "   ", "color-text": 42 as unknown as string },
      "escuro",
    );
    expect(resolvido["color-primary"]).toBe(temaProprio("escuro")["color-primary"]);
    expect(resolvido["color-text"]).toBe(temaProprio("escuro")["color-text"]);
    expect(usados).toEqual([]);
  });

  it("sobrevive a `theme` ausente no handshake (payload parcial por desenho)", () => {
    const { resolvido } = resolverTemaDoInquilino(undefined, "claro");
    expect(Object.keys(resolvido).sort()).toEqual([...TOKENS_CONSUMIDOS].sort());
  });

  it("projeta os tokens como variáveis CSS com o prefixo da aplicação", () => {
    const css = variaveisCss({ "color-primary": "#123456" } as Record<string, string>);
    expect(css["--toc-color-primary"]).toBe("#123456");
  });
});
