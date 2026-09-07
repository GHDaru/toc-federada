// A Árvore de Pré-Requisitos — a tela do M4 · E4.2 (spec 008).
//
// Siglas, uma vez: **M4** — Árvores de Futuro e Implementação · **APR** — Árvore de
// Pré-Requisitos · **OI** — Objetivo Intermediário · **RF/RN/RI** — requisito funcional /
// regra de negócio / requisito de interface.
//
// O que esta tela tem de provar: **a ordem é a informação principal**. Uma APR que
// desenha obstáculos sem dizer o que vem antes de quê é uma lista de queixas com nome
// bonito. Por isso os testes abaixo medem o sequenciamento em camadas, a dependência que
// as gera, e o par obstáculo → objetivo intermediário com o teste de validade que o
// sustenta.
//
// Base sintética (ADR 0006): Instituição Horizonte, Facilitadora TOC.
import { describe, expect, it, vi } from "vitest";
import { screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { TelaDaApr } from "./TelaDaApr";
import { APR, RESUMO_DA_APR, clienteFalso, renderComIdioma } from "../testes/apoio";
import type { Apr } from "../dominio/tipos";
import { ErroDaApi } from "../api/erros";

function abrir(sobrescritas: Record<string, unknown> = {}, idioma: "pt" | "en" = "pt") {
  const cliente = clienteFalso(sobrescritas);
  const util = renderComIdioma(
    <TelaDaApr cliente={cliente} projetoId="p-apr" aoVoltar={vi.fn()} />,
    idioma,
  );
  return { ...util, cliente };
}

function comApr(base: ReturnType<typeof clienteFalso>, extras: Record<string, unknown>) {
  return { apr: { ...(base as unknown as { apr: object }).apr, ...extras } };
}

// ---------------------------------------------------------------------------------------
// O objetivo — o topo, que nunca sai (RF-14)
// ---------------------------------------------------------------------------------------

describe("o objetivo", () => {
  it("mostra o objetivo como topo da árvore, e não como mais um nó", async () => {
    abrir();
    const topo = await screen.findByRole("region", { name: /Objetivo/ });
    expect(within(topo).getByText(APR.objetivo.titulo)).toBeInTheDocument();
  });
});

// ---------------------------------------------------------------------------------------
// O sequenciamento — a informação principal desta ferramenta (RF-23, RN-06)
// ---------------------------------------------------------------------------------------

describe("sequenciamento por dependência", () => {
  it("desenha as camadas NA ORDEM, numeradas para gente (a camada 0 do servidor é a 1)", async () => {
    abrir();
    const sequencia = await screen.findByRole("region", { name: /Sequenciamento/ });
    const camadas = within(sequencia).getAllByRole("listitem", { name: /^Camada/ });
    expect(camadas.map((c) => c.getAttribute("aria-label"))).toEqual(["Camada 1", "Camada 2"]);
    // A camada 1 traz o que precisa existir ANTES; a 2, o que depende dela.
    expect(within(camadas[0]!).getByText(APR.nos[4]!.titulo)).toBeInTheDocument();
    expect(within(camadas[1]!).getByText(APR.nos[2]!.titulo)).toBeInTheDocument();
  });

  it("mostra a leitura da dependência montada pelo servidor", async () => {
    abrir();
    expect(await screen.findByText(APR.dependencias[0]!.leitura)).toBeInTheDocument();
  });

  it("declara o sequenciamento completo quando todo obstáculo tem objetivo intermediário", async () => {
    abrir();
    const sequencia = await screen.findByRole("region", { name: /Sequenciamento/ });
    expect(within(sequencia).getByText(/Sequenciamento completo/)).toBeInTheDocument();
  });

  it("dependência circular BLOQUEIA, e a tela nomeia o ciclo (RN-06)", async () => {
    const base = clienteFalso();
    abrir(
      comApr(base, {
        abrir: async (): Promise<Apr> => ({
          ...APR,
          sequenciamento: {
            ...APR.sequenciamento,
            camadas: [],
            ciclos: [["oi1", "oi2"]],
            bloqueado: true,
            completo: false,
          },
        }),
      }),
    );
    const sequencia = await screen.findByRole("region", { name: /Sequenciamento/ });
    expect(within(sequencia).getByText(/Sequência bloqueada/)).toBeInTheDocument();
    // O ciclo é NOMEADO — os nós do laço, na ordem —, porque é isso que a pessoa precisa
    // para desfazê-lo. O prefixo "Ciclo:" distingue a linha da leitura da dependência.
    expect(
      within(sequencia).getByText(new RegExp(`Ciclo: .*${APR.nos[2]!.titulo}`)),
    ).toBeInTheDocument();
  });

  it("lista as pendências de pareamento com número, sem recontar nada aqui", async () => {
    const base = clienteFalso();
    abrir(
      comApr(base, {
        abrir: async (): Promise<Apr> => ({
          ...APR,
          sequenciamento: {
            ...APR.sequenciamento,
            obstaculos_sem_oi: ["ob1"],
            objetivos_sem_obstaculo: [],
            completo: false,
          },
        }),
      }),
    );
    const sequencia = await screen.findByRole("region", { name: /Sequenciamento/ });
    expect(
      within(sequencia).getByText(/1 obstáculo\(s\) sem objetivo intermediário/),
    ).toBeInTheDocument();
  });
});

// ---------------------------------------------------------------------------------------
// Obstáculo → objetivo intermediário, com o teste de validade (RF-17, RN-07)
// ---------------------------------------------------------------------------------------

describe("obstáculos e objetivos intermediários", () => {
  it("apresenta cada par com o teste de validade montado pelo servidor", async () => {
    abrir();
    const pares = await screen.findByRole("region", { name: /Obstáculos/ });
    const par = within(pares).getByRole("listitem", { name: new RegExp(APR.nos[1]!.titulo) });
    expect(within(par).getByText(APR.pares[0]!.teste_de_validade)).toBeInTheDocument();
  });

  it("julgar exige justificativa e manda o veredito ao servidor — o autor não vai no corpo", async () => {
    const { cliente } = abrir();
    const pares = await screen.findByRole("region", { name: /Obstáculos/ });
    const par = within(pares).getByRole("listitem", { name: new RegExp(APR.nos[1]!.titulo) });
    const valido = within(par).getByRole("button", { name: "Julgar válido" });
    expect(valido).toBeDisabled();

    const espiao = vi.spyOn(cliente.apr, "julgar");
    await userEvent.type(
      within(par).getByLabelText("Justificativa do julgamento"),
      "O posto no ato remove a fila que o obstáculo cria.",
    );
    expect(valido).toBeEnabled();
    await userEvent.click(valido);
    await waitFor(() =>
      expect(espiao).toHaveBeenCalledWith(
        "p-apr",
        "par1",
        true,
        "O posto no ato remove a fila que o obstáculo cria.",
      ),
    );
  });

  it("os julgamentos ACUMULAM e a tela diz que nenhum é apagado (RN-07)", async () => {
    abrir();
    const pares = await screen.findByRole("region", { name: /Obstáculos/ });
    const par = within(pares).getByRole("listitem", { name: new RegExp(APR.nos[3]!.titulo) });
    expect(within(par).getByText(/1 julgamento\(s\) — nenhum é apagado/)).toBeInTheDocument();
  });
});

// ---------------------------------------------------------------------------------------
// A tabela do resumo (RF-25) — a que vai à reunião
// ---------------------------------------------------------------------------------------

describe("tabela do resumo", () => {
  it("traz as linhas na ordem das camadas, com de quem cada uma depende", async () => {
    abrir();
    const tabela = await screen.findByRole("table", { name: /Tabela do resumo/ });
    const linhas = within(tabela).getAllByRole("row").slice(1);
    expect(linhas).toHaveLength(RESUMO_DA_APR.linhas.length);
    expect(linhas[0]!).toHaveTextContent(RESUMO_DA_APR.linhas[0]!.obstaculo!);
    expect(linhas[1]!).toHaveTextContent(RESUMO_DA_APR.linhas[1]!.depende_de[0]!);
  });
});

// ---------------------------------------------------------------------------------------
// Fluxo de erro
// ---------------------------------------------------------------------------------------

describe("fluxo de erro", () => {
  it("desenha a recusa do servidor ao parear um nó que não é obstáculo", async () => {
    const base = clienteFalso();
    abrir(
      comApr(base, {
        julgar: async () => {
          throw new ErroDaApi("MUTATION_REFUSED", "par_invalido", 409);
        },
      }),
    );
    const pares = await screen.findByRole("region", { name: /Obstáculos/ });
    const par = within(pares).getByRole("listitem", { name: new RegExp(APR.nos[1]!.titulo) });
    await userEvent.type(
      within(par).getByLabelText("Justificativa do julgamento"),
      "não vai passar",
    );
    await userEvent.click(within(par).getByRole("button", { name: "Julgar válido" }));
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "A operação é válida, mas não neste estado do projeto.",
    );
    // A árvore continua legível: recusa de escrita não derruba leitura.
    expect(screen.getByRole("region", { name: /Sequenciamento/ })).toBeInTheDocument();
  });

  it("erro de carga desenha a tela de erro com a próxima ação", async () => {
    const base = clienteFalso();
    abrir(
      comApr(base, {
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
    expect(await screen.findByRole("region", { name: /Sequencing by dependency/ })).toBeInTheDocument();
    const sequencia = screen.getByRole("region", { name: /Sequencing by dependency/ });
    expect(within(sequencia).getAllByRole("listitem", { name: /^Layer/ })).toHaveLength(2);
  });
});
