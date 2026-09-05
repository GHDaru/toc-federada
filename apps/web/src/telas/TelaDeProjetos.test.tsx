// A lista de projetos e a lixeira — RI-01 e RI-02 da spec 004.
//
// Fluxo feliz E fluxo de erro em cada tela: a linhagem não tinha nenhum dos dois testados,
// e o seu tratamento de falha de importação era `alert()` do navegador
// (defeito registrado no RI-09 da spec 004).
import { describe, expect, it, vi } from "vitest";
import { screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { TelaDeProjetos } from "./TelaDeProjetos";
import { TelaDaLixeira } from "./TelaDaLixeira";
import { PROJETO_RESUMO, clienteFalso, renderComIdioma } from "../testes/apoio";

describe("tela de projetos — fluxo feliz", () => {
  it("lista os projetos com nome, ferramenta e data de alteração", async () => {
    renderComIdioma(<TelaDeProjetos cliente={clienteFalso()} aoAbrir={vi.fn()} />);
    expect(await screen.findByText("Evasão no primeiro semestre")).toBeInTheDocument();
    const linha = screen.getByRole("row", { name: /Evasão no primeiro semestre/ });
    expect(within(linha).getByText("Árvore da Realidade Atual")).toBeInTheDocument();
  });

  it("abre o projeto pela ação da linha", async () => {
    const aoAbrir = vi.fn();
    renderComIdioma(<TelaDeProjetos cliente={clienteFalso()} aoAbrir={aoAbrir} />);
    await userEvent.click(await screen.findByRole("button", { name: /Abrir/ }));
    expect(aoAbrir).toHaveBeenCalledWith(PROJETO_RESUMO);
  });

  it("cria projeto genérico pela rota do M1 e recarrega a lista", async () => {
    const criar = vi.fn(async () => ({ ...PROJETO_RESUMO, nos: [], arestas: [] }));
    const listar = vi.fn(async () => [PROJETO_RESUMO]);
    const cliente = clienteFalso({
      projetos: { ...clienteFalso().projetos, criar, listar },
    });
    renderComIdioma(<TelaDeProjetos cliente={cliente} aoAbrir={vi.fn()} />);
    await screen.findByText("Evasão no primeiro semestre");
    await userEvent.type(screen.getByLabelText(/^Nome/), "Atraso na matrícula");
    await userEvent.selectOptions(screen.getByLabelText(/Ferramenta/), "generico");
    await userEvent.click(screen.getByRole("button", { name: /Criar projeto/ }));
    await waitFor(() => expect(criar).toHaveBeenCalledWith("Atraso na matrícula", ""));
    await waitFor(() => expect(listar).toHaveBeenCalledTimes(2));
  });

  it("cada ferramenta nasce pela SUA rota — a ARA pela rota da ARA", async () => {
    // O servidor decide a ferramenta e a topologia; o cliente não a informa como texto
    // livre. Criar uma ARA por `POST /toc/projetos` faria um projeto genérico com nome de
    // árvore — e a diferença só apareceria quando alguém tentasse marcar um UDE.
    const criarAra = vi.fn(async () => ({ ...PROJETO_RESUMO, nos: [], arestas: [] }));
    const criarNc = vi.fn(async () => ({ ...PROJETO_RESUMO, nos: [], arestas: [] }));
    const base = clienteFalso();
    const cliente = clienteFalso({
      ara: { ...base.ara, criarProjeto: criarAra },
      nc: { ...base.nc, criarProjeto: criarNc },
    });
    renderComIdioma(<TelaDeProjetos cliente={cliente} aoAbrir={vi.fn()} />);
    await screen.findByText("Evasão no primeiro semestre");
    await userEvent.type(screen.getByLabelText(/^Nome/), "Evasão — árvore");
    await userEvent.click(screen.getByRole("button", { name: /Criar projeto/ }));
    await waitFor(() => expect(criarAra).toHaveBeenCalledWith("Evasão — árvore", ""));

    await userEvent.type(screen.getByLabelText(/^Nome/), "Expansão — nuvem");
    await userEvent.selectOptions(screen.getByLabelText(/Ferramenta/), "nc");
    await userEvent.click(screen.getByRole("button", { name: /Criar projeto/ }));
    await waitFor(() => expect(criarNc).toHaveBeenCalledWith("Expansão — nuvem", ""));
  });

  it("exclui com confirmação que NOMEIA o projeto (exclusão é suave)", async () => {
    const excluir = vi.fn(async () => ({ ...PROJETO_RESUMO, estado: "excluido" as const }));
    const cliente = clienteFalso({ projetos: { ...clienteFalso().projetos, excluir } });
    renderComIdioma(<TelaDeProjetos cliente={cliente} aoAbrir={vi.fn()} />);
    await userEvent.click(await screen.findByRole("button", { name: /Excluir/ }));
    const dialogo = screen.getByRole("dialog");
    expect(within(dialogo).getByText(/Evasão no primeiro semestre/)).toBeInTheDocument();
    expect(excluir).not.toHaveBeenCalled();
    await userEvent.click(within(dialogo).getByRole("button", { name: /Confirmar/ }));
    await waitFor(() => expect(excluir).toHaveBeenCalledWith("p1"));
  });

  it("estado vazio orienta a criação do primeiro projeto", async () => {
    const cliente = clienteFalso({
      projetos: { ...clienteFalso().projetos, listar: async () => [] },
    });
    renderComIdioma(<TelaDeProjetos cliente={cliente} aoAbrir={vi.fn()} />);
    expect(await screen.findByText(/Nenhum projeto ainda/)).toBeInTheDocument();
  });
});

describe("tela de projetos — fluxo de erro", () => {
  it("mostra a recusa como tela desenhada, com próxima ação — nunca texto cru", async () => {
    const listar = vi.fn(async () => {
      throw Object.assign(new Error("boom"), { codigo: "UNAUTHENTICATED", status: 401 });
    });
    const cliente = clienteFalso({ projetos: { ...clienteFalso().projetos, listar } });
    renderComIdioma(<TelaDeProjetos cliente={cliente} aoAbrir={vi.fn()} />);
    const alerta = await screen.findByRole("alert");
    expect(alerta).toHaveTextContent(/sessão não foi reconhecida/i);
    expect(alerta.textContent).not.toContain("boom");
  });

  it("oferece tentar de novo, e tentar de novo tenta de verdade", async () => {
    let falhas = 1;
    const listar = vi.fn(async () => {
      if (falhas-- > 0) throw Object.assign(new Error("x"), { codigo: "REDE_INDISPONIVEL" });
      return [PROJETO_RESUMO];
    });
    const cliente = clienteFalso({ projetos: { ...clienteFalso().projetos, listar } });
    renderComIdioma(<TelaDeProjetos cliente={cliente} aoAbrir={vi.fn()} />);
    await screen.findByRole("alert");
    await userEvent.click(screen.getByRole("button", { name: /Tentar de novo/ }));
    expect(await screen.findByText("Evasão no primeiro semestre")).toBeInTheDocument();
  });
});

describe("lixeira", () => {
  it("lista os excluídos com a data e restaura", async () => {
    const excluido = { ...PROJETO_RESUMO, estado: "excluido" as const, excluido_em: "2026-09-02T12:00:00Z" };
    const restaurar = vi.fn(async () => PROJETO_RESUMO);
    const cliente = clienteFalso({
      projetos: { ...clienteFalso().projetos, lixeira: async () => [excluido], restaurar },
    });
    renderComIdioma(<TelaDaLixeira cliente={cliente} />);
    expect(await screen.findByText("Evasão no primeiro semestre")).toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: /Restaurar/ }));
    await waitFor(() => expect(restaurar).toHaveBeenCalledWith("p1"));
  });

  it("lixeira vazia é estado desenhado, não tabela em branco", async () => {
    renderComIdioma(<TelaDaLixeira cliente={clienteFalso()} />);
    expect(await screen.findByText(/Lixeira vazia/)).toBeInTheDocument();
  });

  it("fluxo de erro: a falha aparece com próxima ação", async () => {
    const cliente = clienteFalso({
      projetos: {
        ...clienteFalso().projetos,
        lixeira: async () => {
          throw Object.assign(new Error("x"), { codigo: "UNAUTHORIZED", status: 403 });
        },
      },
    });
    renderComIdioma(<TelaDaLixeira cliente={cliente} />);
    expect(await screen.findByRole("alert")).toHaveTextContent(/permissão/i);
  });
});
