// O registro de telas é FONTE DE VERDADE COMPARTILHADA entre interface e serviço (APH-3.1
// — Aplicação ↔ Harness). A inteligência artificial nunca infere a interface: não raspa
// DOM (Document Object Model) nem lê captura de tela. Ela sabe em que tela a pessoa está
// porque a tela está declarada — dos dois lados, com os mesmos identificadores.
//
// Este teste é a função de aptidão dessa paridade: ele lê o manifesto publicado no
// repositório e compara, campo a campo, com o que a interface declara.
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";
import { REGISTRO_DE_TELAS, telaPorId, telaSensivel, camposVisiveisParaIa } from "./registro";

// O caminho parte da raiz do pacote (`apps/web`), que é o diretório de trabalho do
// Vitest — e não de `import.meta.url`, que em ambiente jsdom é uma URL http, não file.
const CAMINHO_DO_MANIFESTO = resolve(
  process.cwd(),
  "../../specs/006-acoes-governadas-e-snapshot/contracts/manifesto.json",
);

const manifesto = JSON.parse(readFileSync(CAMINHO_DO_MANIFESTO, "utf8")) as { screens: { id: string; route: string; title: string; ai_actions: string[] }[] };

describe("registro de telas × manifesto publicado", () => {
  it("declara exatamente as telas do manifesto, com rota, título e ações iguais", () => {
    const daInterface = REGISTRO_DE_TELAS.filter((t) => t.declaradaNoManifesto)
      .map((t) => ({ id: t.id, route: t.rota, title: t.titulo, ai_actions: [...t.acoesDeIa] }))
      .sort((a, b) => a.id.localeCompare(b.id));
    const doManifesto = manifesto.screens
      .map((t) => ({ id: t.id, route: t.route, title: t.title, ai_actions: t.ai_actions }))
      .sort((a, b) => a.id.localeCompare(b.id));
    expect(daInterface).toEqual(doManifesto);
  });

  it("toda tela tem identificador sob o prefixo `toc.` e rota sob `/toc/`", () => {
    for (const tela of REGISTRO_DE_TELAS) {
      expect(tela.id).toMatch(/^toc\.[a-z][a-z0-9_]*$/);
      expect(tela.rota).toMatch(/^\/toc\/[a-z0-9/_-]+$/);
      expect(tela.rota.endsWith("/")).toBe(false);
    }
  });

  it("todo campo DECLARA `ai_visible` — o padrão é não visível, nunca esquecimento", () => {
    for (const tela of REGISTRO_DE_TELAS) {
      for (const campo of tela.campos) {
        expect(Object.prototype.hasOwnProperty.call(campo, "aiVisivel"), `${tela.id}.${campo.nome}`).toBe(true);
        if (campo.aiVisivel) {
          // RF-01 da spec 002: cada `sim` carrega justificativa escrita.
          expect(campo.justificativa, `${tela.id}.${campo.nome}`).toMatch(/\S/);
        }
      }
    }
  });

  it("tela com `ai_actions` vazio é sensível e não entra em snapshot (§B.5.3)", () => {
    expect(telaSensivel("toc.configuracao")).toBe(true);
    expect(telaSensivel("toc.projetos")).toBe(false);
  });

  it("os campos da tela de configuração do embarque não vão para modelo nenhum", () => {
    expect(camposVisiveisParaIa("toc.configuracao")).toEqual([]);
  });

  it("o rascunho de parecer da ARA é invisível para a IA", () => {
    const visiveis = camposVisiveisParaIa("toc.ara");
    expect(visiveis).not.toContain("rascunho_de_parecer");
    expect(visiveis).toContain("nos_visiveis");
  });

  it("telaPorId devolve `undefined` para tela desconhecida, sem lançar", () => {
    expect(telaPorId("toc.inventada")).toBeUndefined();
  });
});
