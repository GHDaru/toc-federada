// A Árvore de Transição — a tela do M4 · E4.3 (spec 008).
//
// Siglas, uma vez: **M4** — Árvores de Futuro e Implementação · **AT** — Árvore de
// Transição · **APR** — Árvore de Pré-Requisitos · **RF/RN** — requisito funcional / regra
// de negócio.
//
// O que esta tela tem de provar: **a tripla é obrigatória e visível**. Um passo da AT diz
// três coisas — a necessidade que o justifica, a ação que se executa e o resultado que se
// espera —, e uma tela que mostrasse só a ação transformaria a árvore numa lista de
// tarefas. É por isso que os três campos aparecem rotulados em cada passo, e é por isso
// que o formulário não arma sem os três.
//
// Base sintética (ADR 0006): Instituição Horizonte, Facilitadora TOC.
import { describe, expect, it, vi } from "vitest";
import { screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { TelaDaAt } from "./TelaDaAt";
import { AT, clienteFalso, renderComIdioma } from "../testes/apoio";
import type { At } from "../dominio/tipos";
import { ErroDaApi } from "../api/erros";

function abrir(sobrescritas: Record<string, unknown> = {}, idioma: "pt" | "en" = "pt") {
  const cliente = clienteFalso(sobrescritas);
  const util = renderComIdioma(
    <TelaDaAt cliente={cliente} projetoId="p-at" aoVoltar={vi.fn()} />,
    idioma,
  );
  return { ...util, cliente };
}

function comAt(base: ReturnType<typeof clienteFalso>, extras: Record<string, unknown>) {
  return { at: { ...(base as unknown as { at: object }).at, ...extras } };
}

// ---------------------------------------------------------------------------------------
// Os passos, na ordem de execução (RF-32) — e a tripla de cada um (RN-10)
// ---------------------------------------------------------------------------------------

describe("os passos e a tripla", () => {
  it("lista os passos na ordem de leitura que o servidor calculou", async () => {
    abrir();
    const lista = await screen.findByRole("region", { name: /Passos/ });
    const passos = within(lista).getAllByRole("listitem", { name: /^Para / });
    expect(passos.map((p) => p.getAttribute("data-passo"))).toEqual(AT.ordem_de_leitura);
  });

  it("mostra necessidade, ação e resultado esperado ROTULADOS em cada passo", async () => {
    abrir();
    const lista = await screen.findByRole("region", { name: /Passos/ });
    const passo = within(lista).getAllByRole("listitem", { name: /^Para / })[0]!;
    // Os três rótulos, e os três textos NO CAMPO CERTO. A consulta é por classe porque o
    // passo p1 concluiu sem divergência: o resultado obtido é igual ao esperado, e uma
    // busca por texto acharia os dois — que é justamente o que se quer que aconteça.
    expect(within(passo).getByText("Necessidade")).toBeInTheDocument();
    expect(within(passo).getByText("Ação")).toBeInTheDocument();
    expect(within(passo).getByText("Resultado esperado")).toBeInTheDocument();
    expect(passo.querySelector("p.necessidade")).toHaveTextContent(AT.passos[0]!.necessidade);
    expect(passo.querySelector("p.acao")).toHaveTextContent(AT.passos[0]!.acao);
    expect(passo.querySelector("p.resultado-esperado")).toHaveTextContent(
      AT.passos[0]!.resultado_esperado,
    );
  });

  it("carrega o status por extenso e o motivo do bloqueio quando existe (RF-30)", async () => {
    abrir();
    const lista = await screen.findByRole("region", { name: /Passos/ });
    const bloqueado = within(lista).getAllByRole("listitem", { name: /^Para / })[2]!;
    expect(bloqueado).toHaveAttribute("data-status", "bloqueado");
    // O estado sai por extenso no parágrafo do passo — e não só como opção do seletor,
    // que é o outro lugar onde a palavra aparece.
    expect(bloqueado.querySelector("p.status-atual")).toHaveTextContent("Bloqueado");
    expect(within(bloqueado).getByText(AT.passos[2]!.motivo_do_bloqueio)).toBeInTheDocument();
  });

  it("publica o progresso do plano a partir do resumo do servidor", async () => {
    abrir();
    expect(await screen.findByText("1 de 3 passo(s) concluído(s)")).toBeInTheDocument();
    expect(screen.getByText("1 passo(s) bloqueado(s)")).toBeInTheDocument();
  });

  it("um resultado divergente aparece SEM apagar o esperado", async () => {
    const divergente: At = {
      ...AT,
      passos: AT.passos.map((p) =>
        p.id === "p2"
          ? {
              ...p,
              status: "concluido" as const,
              resultado_real: "a recepção ainda consulta a secretaria em casos raros",
              divergente: true,
            }
          : p,
      ),
    };
    const base = clienteFalso();
    abrir(comAt(base, { abrir: async () => divergente }));
    const lista = await screen.findByRole("region", { name: /Passos/ });
    const passo = within(lista).getAllByRole("listitem", { name: /^Para / })[1]!;
    expect(within(passo).getByText(/O resultado obtido difere do esperado/)).toBeInTheDocument();
    expect(within(passo).getByText(AT.passos[1]!.resultado_esperado)).toBeInTheDocument();
    expect(
      within(passo).getByText("a recepção ainda consulta a secretaria em casos raros"),
    ).toBeInTheDocument();
  });
});

// ---------------------------------------------------------------------------------------
// Registrar um passo — a tripla é obrigatória, sem exceção (RN-10)
// ---------------------------------------------------------------------------------------

describe("registrar passo", () => {
  it("não arma o botão sem os três campos, e manda os três quando arma", async () => {
    const { cliente } = abrir();
    const registrar = await screen.findByRole("button", { name: "Registrar passo" });
    expect(registrar).toBeDisabled();

    await userEvent.type(screen.getByLabelText("Necessidade"), "a recepção não tem sala");
    expect(registrar).toBeDisabled();
    await userEvent.type(screen.getByLabelText("Ação"), "reservar a sala 2 para o posto");
    expect(registrar).toBeDisabled();
    await userEvent.type(screen.getByLabelText("Resultado esperado"), "a sala 2 é do posto");

    const espiao = vi.spyOn(cliente.at, "registrarPasso");
    expect(registrar).toBeEnabled();
    await userEvent.click(registrar);
    await waitFor(() =>
      expect(espiao).toHaveBeenCalledWith("p-at", {
        necessidade: "a recepção não tem sala",
        acao: "reservar a sala 2 para o posto",
        resultado_esperado: "a sala 2 é do posto",
      }),
    );
  });
});

// ---------------------------------------------------------------------------------------
// Mudar o status (RF-30) — bloquear exige motivo, concluir exige o resultado real
// ---------------------------------------------------------------------------------------

describe("mudar o status de um passo", () => {
  it("concluir manda o resultado real junto, e o esperado não é tocado", async () => {
    const { cliente } = abrir();
    const lista = await screen.findByRole("region", { name: /Passos/ });
    const passo = within(lista).getAllByRole("listitem", { name: /^Para / })[1]!;

    const espiao = vi.spyOn(cliente.at, "mudarStatus");
    await userEvent.selectOptions(within(passo).getByLabelText("Status"), "concluido");
    await userEvent.type(
      within(passo).getByLabelText("Resultado obtido"),
      "a recepção confere sozinha",
    );
    await userEvent.click(within(passo).getByRole("button", { name: "Mudar o status" }));
    await waitFor(() =>
      expect(espiao).toHaveBeenCalledWith("p-at", "p2", {
        status: "concluido",
        motivo: "",
        resultado_real: "a recepção confere sozinha",
      }),
    );
  });
});

// ---------------------------------------------------------------------------------------
// Fluxo de erro
// ---------------------------------------------------------------------------------------

describe("fluxo de erro", () => {
  it("a recusa do servidor a uma transição inválida vira texto na tela", async () => {
    const base = clienteFalso();
    abrir(
      comAt(base, {
        mudarStatus: async () => {
          throw new ErroDaApi("INVALID_TRANSITION", "resultado_real_obrigatorio", 409);
        },
      }),
    );
    const lista = await screen.findByRole("region", { name: /Passos/ });
    const passo = within(lista).getAllByRole("listitem", { name: /^Para / })[1]!;
    await userEvent.selectOptions(within(passo).getByLabelText("Status"), "concluido");
    await userEvent.click(within(passo).getByRole("button", { name: "Mudar o status" }));
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Esta mudança de status não é permitida a partir do estado atual.",
    );
    expect(screen.getByRole("region", { name: /Passos/ })).toBeInTheDocument();
  });

  it("erro de carga desenha a tela de erro com a próxima ação", async () => {
    const base = clienteFalso();
    abrir(
      comAt(base, {
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
  it("desenha a mesma tela em inglês", async () => {
    abrir({}, "en");
    expect(await screen.findByRole("region", { name: /Steps, in execution order/ })).toBeInTheDocument();
    expect(screen.getByText("1 of 3 step(s) completed")).toBeInTheDocument();
  });
});
