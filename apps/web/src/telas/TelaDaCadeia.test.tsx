// A cadeia — a tela do M4 · E4.4 (spec 008).
//
// Siglas, uma vez: **M4** — Árvores de Futuro e Implementação · **ARA** — Árvore da
// Realidade Atual · **UDE** — Efeito Indesejável · **NC** — Nuvem de Conflito · **ARF** —
// Árvore da Realidade Futura · **APR** — Árvore de Pré-Requisitos · **AT** — Árvore de
// Transição · **OI** — Objetivo Intermediário · **RF** — requisito funcional.
//
// Esta é a tela que **nenhuma das quatro gerações da linhagem chegou perto de ter**: o
// percurso completo da Teoria das Restrições numa tela só. As gerações anteriores
// desenhavam ferramentas isoladas; o que faltava era dizer que o Efeito Indesejável da
// árvore de hoje é o dilema de amanhã, e que a injeção escolhida vira a árvore de futuro.
//
// Duas invariantes que os testes medem: a travessia sai **na ordem canônica** (uma cadeia
// que se lê diferente a cada abertura não se confere), e o **elo pendente NUNCA some**
// (RF-35, US-18) — esconder o vínculo que perdeu uma ponta é esconder o que a pessoa
// precisa consertar.
//
// Base sintética (ADR 0006): Instituição Horizonte, Facilitadora TOC.
import { describe, expect, it, vi } from "vitest";
import { screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { TelaDaCadeia } from "./TelaDaCadeia";
import { clienteFalso, renderComIdioma } from "../testes/apoio";
import type { Cadeia } from "../dominio/tipos";
import { ErroDaApi } from "../api/erros";

function abrir(sobrescritas: Record<string, unknown> = {}, idioma: "pt" | "en" = "pt") {
  const cliente = clienteFalso(sobrescritas);
  const aoAbrirProjeto = vi.fn();
  const util = renderComIdioma(
    <TelaDaCadeia
      cliente={cliente}
      projetoId="p-ara"
      aoVoltar={vi.fn()}
      aoAbrirProjeto={aoAbrirProjeto}
    />,
    idioma,
  );
  return { ...util, cliente, aoAbrirProjeto };
}

function comCadeia(base: ReturnType<typeof clienteFalso>, extras: Record<string, unknown>) {
  return { cadeia: { ...(base as unknown as { cadeia: object }).cadeia, ...extras } };
}

// ---------------------------------------------------------------------------------------
// A travessia inteira (RF-41, RF-42)
// ---------------------------------------------------------------------------------------

describe("o percurso completo", () => {
  it("desenha os quatro elos na ordem canônica da análise", async () => {
    abrir();
    const percurso = await screen.findByRole("region", { name: /Percurso da análise/ });
    const etapas = within(percurso).getAllByRole("listitem", { name: /^Etapa/ });
    expect(etapas.map((e) => e.getAttribute("data-tipo"))).toEqual([
      "promocao_ude_nc",
      "semeadura_injecao_arf",
      "derivacao_arf_apr",
      "derivacao_oi_at",
    ]);
  });

  it("nomeia cada costura por extenso, e não pelo código do servidor", async () => {
    abrir();
    const percurso = await screen.findByRole("region", { name: /Percurso da análise/ });
    const primeira = within(percurso).getAllByRole("listitem", { name: /^Etapa/ })[0]!;
    expect(
      within(primeira).getByText("Efeito Indesejável promovido a dilema"),
    ).toBeInTheDocument();
    // As duas pontas com o nome da ferramenta, não com o identificador do projeto.
    expect(within(primeira).getByText(/Árvore da Realidade Atual/)).toBeInTheDocument();
    expect(within(primeira).getByText(/Nuvem de Conflito/)).toBeInTheDocument();
  });

  it("lista as ferramentas que a análise atravessa, na ordem da travessia", async () => {
    abrir();
    const trilha = await screen.findByRole("list", { name: /Ferramentas/ });
    expect(within(trilha).getAllByRole("listitem").map((i) => i.textContent)).toEqual([
      "Árvore da Realidade Atual",
      "Nuvem de Conflito",
      "Árvore da Realidade Futura",
      "Árvore de Pré-Requisitos",
      "Árvore de Transição",
    ]);
  });

  it("publica o resumo que o servidor contou — a tela não reconta nada", async () => {
    abrir();
    expect(
      await screen.findByText("4 elo(s) · 5 ferramenta(s) · 5 projeto(s)"),
    ).toBeInTheDocument();
  });
});

// ---------------------------------------------------------------------------------------
// O elo pendente (RF-35, US-18) — o que perdeu uma ponta continua à vista
// ---------------------------------------------------------------------------------------

describe("elo pendente", () => {
  it("mostra o elo pendente COM o motivo, em vez de omiti-lo", async () => {
    abrir();
    const percurso = await screen.findByRole("region", { name: /Percurso da análise/ });
    const ultima = within(percurso).getAllByRole("listitem", { name: /^Etapa/ })[3]!;
    expect(ultima).toHaveAttribute("data-estado", "pendente");
    expect(within(ultima).getByText("Pendente")).toBeInTheDocument();
    expect(within(ultima).getByText(/o projeto de destino foi excluído/)).toBeInTheDocument();
  });

  it("conta os pendentes no cabeçalho, para o aviso não depender de rolar a lista", async () => {
    abrir();
    expect(
      await screen.findByText(/1 elo\(s\) pendente\(s\)/),
    ).toBeInTheDocument();
  });
});

// ---------------------------------------------------------------------------------------
// Navegar pela cadeia — é para isso que ela serve
// ---------------------------------------------------------------------------------------

describe("navegação", () => {
  it("abrir uma ponta leva à ferramenta certa, com o projeto certo", async () => {
    const { aoAbrirProjeto } = abrir();
    const percurso = await screen.findByRole("region", { name: /Percurso da análise/ });
    const segunda = within(percurso).getAllByRole("listitem", { name: /^Etapa/ })[1]!;
    await userEvent.click(
      within(segunda).getByRole("button", { name: "Abrir Árvore da Realidade Futura" }),
    );
    expect(aoAbrirProjeto).toHaveBeenCalledWith({ ferramenta: "arf", projetoId: "p-arf" });
  });

  it("a ponta de um elo PENDENTE não oferece botão de abrir — não há o que abrir", async () => {
    abrir();
    const percurso = await screen.findByRole("region", { name: /Percurso da análise/ });
    const ultima = within(percurso).getAllByRole("listitem", { name: /^Etapa/ })[3]!;
    expect(
      within(ultima).queryByRole("button", { name: /Abrir Árvore de Transição/ }),
    ).toBeNull();
  });
});

// ---------------------------------------------------------------------------------------
// Vazio e erro
// ---------------------------------------------------------------------------------------

describe("vazio e erro", () => {
  it("projeto ainda não encadeado DIZ como a cadeia começa", async () => {
    const base = clienteFalso();
    abrir(
      comCadeia(base, {
        abrir: async (): Promise<Cadeia> => ({
          elos: [],
          ferramentas: [],
          resumo: { elos: 0, elos_pendentes: 0, ferramentas: 0, projetos: 0 },
        }),
      }),
    );
    expect(
      await screen.findByText(/A cadeia começa promovendo um Efeito Indesejável validado/),
    ).toBeInTheDocument();
  });

  it("erro de carga desenha a tela de erro com a próxima ação", async () => {
    const base = clienteFalso();
    abrir(
      comCadeia(base, {
        abrir: async () => {
          throw new ErroDaApi("REDE_INDISPONIVEL", "sem rede", 0);
        },
      }),
    );
    expect(await screen.findByRole("alert")).toHaveTextContent(/O serviço não respondeu/);
    expect(screen.getByRole("button", { name: "Tentar de novo" })).toBeInTheDocument();
  });
});

// ---------------------------------------------------------------------------------------
// Internacionalização
// ---------------------------------------------------------------------------------------

describe("internacionalização", () => {
  it("desenha o mesmo percurso em inglês", async () => {
    abrir({}, "en");
    const percurso = await screen.findByRole("region", { name: /Path of the analysis/ });
    expect(
      within(percurso).getByText("Undesirable Effect promoted into a dilemma"),
    ).toBeInTheDocument();
    expect(within(percurso).getAllByRole("listitem", { name: /^Step/ })).toHaveLength(4);
  });
});
