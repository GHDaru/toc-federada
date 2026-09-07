// E8.3 · F8.3.3 e F8.3.4 — o idioma efetivo e a chave que falta (spec 011).
//
// Siglas, uma vez neste arquivo: **i18n** — internacionalização · **UDE** — Efeito
// Indesejável · **RF** — requisito funcional da spec 011 · **CI** — integração contínua.
//
// **Os dois defeitos da linhagem que estes testes fecham**, os dois medidos:
//
// 1. `tocbuilderv3/i18n/I18nProvider.tsx:41` — `let result = translation || key;`. Chave
//    ausente **renderiza a própria chave** na tela: sem erro, sem log, sem portão. É o
//    RF-09 (falha alto em desenvolvimento) e o RF-10 (em produção cai para a língua-fonte
//    e registra) que o substituem.
// 2. `tocbuilderv3/i18n/I18nProvider.tsx:15,23-28` — a preferência vivia em
//    `localStorage` sob `toc_builder_locale`: escolha presa a um navegador. A resolução
//    do RF-12 é **função pura** com o motivo anexado, e é isso que permite a preferência
//    vir de onde quer que seja guardada — inclusive do servidor.
import { describe, expect, it, vi } from "vitest";

import { pt } from "./pt";
import {
  ChaveDeTraducaoAusente,
  resolverIdiomaEfetivo,
  traduzirCom,
  type OrigemDoIdioma,
} from "./index";

describe("idioma efetivo (RF-12, RF-14)", () => {
  it("a preferência da pessoa vence o que o embarque declarou", () => {
    const efetivo = resolverIdiomaEfetivo({ preferencia: "en", doEmbarque: "pt" });
    expect(efetivo.idioma).toBe("en");
    expect(efetivo.origem).toBe<OrigemDoIdioma>("preferencia");
  });

  it("sem preferência, vale o idioma declarado pelo embarque", () => {
    const efetivo = resolverIdiomaEfetivo({ doEmbarque: "en" });
    expect(efetivo.idioma).toBe("en");
    expect(efetivo.origem).toBe<OrigemDoIdioma>("embarque");
  });

  it("sem preferência e sem embarque, cai para a língua-fonte E registra a queda", () => {
    const registros: unknown[] = [];
    const efetivo = resolverIdiomaEfetivo({ registrar: (linha) => registros.push(linha) });

    expect(efetivo.idioma).toBe("pt");
    expect(efetivo.origem).toBe<OrigemDoIdioma>("lingua_fonte");
    expect(registros).toEqual([
      { evento: "i18n.queda_para_o_padrao", idioma: "pt", motivo: "sem preferência e sem idioma no embarque" },
    ]);
  });

  it("idioma que a aplicação não fala é ignorado como se não tivesse vindo", () => {
    // O hospedeiro é dado, nunca instrução (P2): um `locale` de valor inesperado não
    // pode escolher tela nenhuma.
    const efetivo = resolverIdiomaEfetivo({ doEmbarque: "fr" as never });
    expect(efetivo.idioma).toBe("pt");
    expect(efetivo.origem).toBe<OrigemDoIdioma>("lingua_fonte");
  });

  it("o motivo da escolha viaja junto, para o diagnóstico", () => {
    expect(resolverIdiomaEfetivo({ preferencia: "pt", doEmbarque: "en" }).motivo).toContain(
      "preferência",
    );
  });
});

describe("chave ausente (RF-09, RF-10)", () => {
  const semChave = { app: { titulo: "TOC Federada" } } as never;

  it("em desenvolvimento e em teste, lança erro visível nomeando a chave", () => {
    expect(() => traduzirCom(semChave, "projetos.titulo", {}, { modo: "estrito" })).toThrow(
      ChaveDeTraducaoAusente,
    );
    try {
      traduzirCom(semChave, "projetos.titulo", {}, { modo: "estrito", tela: "toc.projetos" });
    } catch (erro) {
      expect(String(erro)).toContain("projetos.titulo");
      expect(String(erro)).toContain("toc.projetos");
    }
  });

  it("em produção cai para a cadeia da língua-fonte — NUNCA para a chave crua", () => {
    const registrar = vi.fn();
    const texto = traduzirCom(semChave, "projetos.titulo", {}, {
      modo: "tolerante",
      fonte: pt,
      tela: "toc.projetos",
      registrar,
    });

    expect(texto).toBe(pt.projetos.titulo);
    expect(texto).not.toBe("projetos.titulo");
    expect(registrar).toHaveBeenCalledWith({
      evento: "i18n.chave_ausente",
      chave: "projetos.titulo",
      tela: "toc.projetos",
    });
  });

  it("a interpolação continua valendo na queda para a língua-fonte", () => {
    const texto = traduzirCom(semChave, "projetos.contagem", { n: 3 }, {
      modo: "tolerante",
      fonte: pt,
    });
    expect(texto).toContain("3");
  });

  it("chave ausente nos DOIS dicionários devolve vazio e registra — nunca o identificador", () => {
    // Não pode acontecer (a chave é tipada e o portão de paridade roda na CI), e por isso
    // mesmo o comportamento é declarado: um identificador técnico na tela é o defeito que
    // a US-07 nomeia — "a ferramenta não pode parecer quebrada na frente da equipe".
    const registrar = vi.fn();
    const texto = traduzirCom(semChave, "nao.existe" as never, {}, {
      modo: "tolerante",
      fonte: semChave,
      registrar,
    });
    expect(texto).toBe("");
    expect(registrar).toHaveBeenCalled();
  });

  it("o modo padrão fora de produção é o estrito", () => {
    expect(() => traduzirCom(semChave, "projetos.titulo")).toThrow(ChaveDeTraducaoAusente);
  });
});
