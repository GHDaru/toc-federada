// A Nuvem de Conflito (NC) inteira — spec 007.
//
// Requisitos: RI-08 (visão conflito+solução por controle persistente na sessão, lado a
// lado em tela larga), RI-09 (completude no cabeçalho com salto para as pendentes) e
// RI-10 (vista tabular com paridade de capacidade com o diagrama).
import { beforeEach, describe, expect, it, vi } from "vitest";
import { screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { TelaDaNuvem, CHAVE_DA_VISAO } from "./TelaDaNuvem";
import { NUVEM, clienteFalso, renderComIdioma } from "../testes/apoio";

function abrir(sobrescritas: Record<string, unknown> = {}) {
  const cliente = clienteFalso(sobrescritas);
  const util = renderComIdioma(<TelaDaNuvem cliente={cliente} projetoId="p-nc" aoVoltar={vi.fn()} />);
  return { ...util, cliente };
}

beforeEach(() => sessionStorage.clear());

describe("tela da nuvem — fluxo feliz", () => {
  it("abre a nuvem com as cinco entidades e as sete arestas", async () => {
    abrir();
    expect(await screen.findByTestId("entidade-A")).toBeInTheDocument();
    expect(screen.getAllByTestId(/^aresta-/)).toHaveLength(7);
    expect(screen.getByRole("heading", { name: NUVEM.nome })).toBeInTheDocument();
  });

  it("mostra a completude no cabeçalho e salta para uma aresta pendente (RI-09)", async () => {
    abrir();
    expect(await screen.findByText(/0 de 7 arestas com premissa/)).toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: /Arestas pendentes/ }));
    expect(await screen.findByRole("region", { name: /Ficha da aresta/ })).toBeInTheDocument();
  });

  it("abre a ficha pela legenda da aresta e registra premissa (RI-03)", async () => {
    const base = clienteFalso();
    const registrarPremissa = vi.fn(async () => ({
      id: "pr1",
      aresta: "A_B" as const,
      texto: "x",
      ordem: 0,
      estado: "vigente" as const,
      justificativa: "",
      injecoes: [],
    }));
    abrir({ nc: { ...base.nc, registrarPremissa } });
    await screen.findByTestId("entidade-A");
    await userEvent.click(within(screen.getByTestId("aresta-A_B")).getByRole("button"));
    const ficha = await screen.findByRole("region", { name: /Ficha da aresta/ });
    await userEvent.type(within(ficha).getByLabelText(/Nova premissa/), "Titular sustenta a avaliação.");
    await userEvent.click(within(ficha).getByRole("button", { name: /^Nova premissa$/ }));
    await waitFor(() =>
      expect(registrarPremissa).toHaveBeenCalledWith("p-nc", "A_B", "Titular sustenta a avaliação."),
    );
  });

  it("edita o texto de uma entidade pelo comando do servidor", async () => {
    const base = clienteFalso();
    const editarEntidade = vi.fn(async () => NUVEM);
    abrir({ nc: { ...base.nc, editarEntidade } });
    const entidade = await screen.findByTestId("entidade-D");
    await userEvent.dblClick(within(entidade).getByText(/Abrir turmas/));
    const campo = screen.getByLabelText("Editar D");
    await userEvent.clear(campo);
    await userEvent.type(campo, "Abrir turmas em duas cidades novas{Enter}");
    await waitFor(() =>
      expect(editarEntidade).toHaveBeenCalledWith("p-nc", "D", "Abrir turmas em duas cidades novas"),
    );
  });
});

describe("tela da nuvem — visão conflito + solução (RI-08)", () => {
  it("alterna para a solução e mostra as SETE posições, com a pendência marcada", async () => {
    abrir();
    await screen.findByTestId("entidade-A");
    await userEvent.click(screen.getByRole("radio", { name: /^Solução$/ }));
    const solucao = await screen.findByRole("region", { name: "Solução" });
    expect(within(solucao).getAllByRole("listitem")).toHaveLength(7);
    expect(within(solucao).getAllByText(/Sem injeção/)).toHaveLength(7);
  });

  it("mostra os dois diagramas lado a lado e guarda a escolha na sessão", async () => {
    const { unmount } = abrir();
    await screen.findByTestId("entidade-A");
    await userEvent.click(screen.getByRole("radio", { name: /Lado a lado/ }));
    // Nomes exatos: a tela inteira é uma região chamada "Nuvem de Conflito", e os dois
    // diagramas são regiões chamadas "Conflito" e "Solução".
    expect(await screen.findByRole("region", { name: "Conflito" })).toBeInTheDocument();
    expect(screen.getByRole("region", { name: "Solução" })).toBeInTheDocument();
    expect(sessionStorage.getItem(CHAVE_DA_VISAO)).toBe("lado_a_lado");

    unmount();
    abrir();
    expect(await screen.findByRole("region", { name: "Solução" })).toBeInTheDocument();
  });
});

describe("tela da nuvem — vista tabular (RI-10)", () => {
  it("mostra as sete arestas como linhas, com a leitura por extenso", async () => {
    abrir();
    await screen.findByTestId("entidade-A");
    await userEvent.click(screen.getByRole("radio", { name: /Vista tabular/ }));
    const linhas = screen.getAllByRole("row").slice(1);
    expect(linhas).toHaveLength(7);
    expect(linhas[0]).toHaveTextContent("Para ter B, precisamos de A");
  });
});

describe("tela da nuvem — fluxo de erro", () => {
  it("falha ao abrir vira tela desenhada com tentar de novo", async () => {
    const base = clienteFalso();
    let falhas = 1;
    abrir({
      nc: {
        ...base.nc,
        abrir: async () => {
          if (falhas-- > 0) throw Object.assign(new Error("x"), { codigo: "NOT_FOUND", status: 404 });
          return NUVEM;
        },
      },
    });
    expect(await screen.findByRole("alert")).toHaveTextContent(/não existe/i);
    await userEvent.click(screen.getByRole("button", { name: /Tentar de novo/ }));
    expect(await screen.findByTestId("entidade-A")).toBeInTheDocument();
  });

  it("a topologia fixa recusada pelo servidor vira frase, e a nuvem continua na tela", async () => {
    const base = clienteFalso();
    abrir({
      nc: {
        ...base.nc,
        editarEntidade: async () => {
          throw Object.assign(new Error("x"), { codigo: "FIXED_TOPOLOGY", status: 409 });
        },
      },
    });
    const entidade = await screen.findByTestId("entidade-C");
    await userEvent.dblClick(within(entidade).getByText(/Custo por turma/));
    const campo = screen.getByLabelText("Editar C");
    await userEvent.clear(campo);
    await userEvent.type(campo, "Custo sob controle{Enter}");
    expect(await screen.findByRole("alert")).toHaveTextContent(/topologia fixa/i);
    expect(screen.getByTestId("entidade-C")).toBeInTheDocument();
  });
});

describe("tela da nuvem — geração assistida não escreve (RF-21/RF-24)", () => {
  it("mostra a pré-visualização e o aviso de que nada foi aplicado", async () => {
    const base = clienteFalso();
    const gerar = vi.fn(async () => ({
      action_id: "toc.generate_conflict_cloud",
      aviso: "nada foi aplicado",
      resultado: {
        versao: "1.0.0",
        entidades: {
          A: "Reputação acadêmica sustentada",
          B: "b",
          C: "c",
          D: "d",
          D_PRIME: "d'",
        },
        arestas: { A_B: [], A_C: [], B_D: [], C_D_PRIME: [], D_C: [], D_PRIME_B: [], D_D_PRIME: [] },
      },
    }));
    const editarEntidade = vi.fn(async () => NUVEM);
    abrir({ nc: { ...base.nc, gerar, editarEntidade } });
    await screen.findByTestId("entidade-A");
    await userEvent.type(screen.getByLabelText(/Narrativa do dilema/), "Queremos crescer sem perder qualidade.");
    await userEvent.click(screen.getByRole("button", { name: /Gerar a partir da narrativa/ }));
    const previa = await screen.findByRole("region", { name: /Pré-visualização/ });
    expect(within(previa).getByText(/Nada foi aplicado/)).toBeInTheDocument();
    expect(within(previa).getByText("Reputação acadêmica sustentada")).toBeInTheDocument();
    // E o texto de hoje aparece ao lado: a prévia é um diff, não uma substituição cega.
    expect(within(previa).getByText("Reputação acadêmica preservada")).toBeInTheDocument();
    // Nenhuma escrita aconteceu: a nuvem no servidor está intacta.
    expect(editarEntidade).not.toHaveBeenCalled();
  });
});
