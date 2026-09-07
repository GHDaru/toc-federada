// A Árvore da Realidade Futura — a tela do M4 · E4.1 (spec 008).
//
// Siglas, uma vez: **M4** — Árvores de Futuro e Implementação · **ARF** — Árvore da
// Realidade Futura · **ARA** — Árvore da Realidade Atual · **UDE** — Efeito Indesejável ·
// **ED** — Efeito Desejável · **NC** — Nuvem de Conflito · **RI/RF/RN** — requisito de
// interface / funcional / regra de negócio.
//
// O que esta tela tem de provar, e por quê: nas quatro gerações da linhagem a ARF foi um
// **botão cinza** (`tocbuilderv3/components/Sidebar.tsx:55` — `view: 'ARF', disabled:
// true`). O domínio dela nasceu no ciclo 008 e ficou sem interface: árvore invisível é
// meia árvore. Os testes abaixo medem as três coisas que fazem esta tela existir —
// a injeção como PONTO DE PARTIDA, os efeitos desejáveis encadeados a partir dela, e o
// **ramo negativo com a poda**, que é o que separa uma árvore de futuro séria de uma
// lista de desejos.
//
// Base sintética (ADR 0006): Instituição Horizonte, Facilitadora TOC.
import { describe, expect, it, vi } from "vitest";
import { screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { TelaDaArf } from "./TelaDaArf";
import { ARF, clienteFalso, renderComIdioma } from "../testes/apoio";
import type { Arf } from "../dominio/tipos";
import { ErroDaApi } from "../api/erros";

function abrir(sobrescritas: Record<string, unknown> = {}, idioma: "pt" | "en" = "pt") {
  const cliente = clienteFalso(sobrescritas);
  const util = renderComIdioma(
    <TelaDaArf cliente={cliente} projetoId="p-arf" aoVoltar={vi.fn()} />,
    idioma,
  );
  return { ...util, cliente };
}

function comArf(base: ReturnType<typeof clienteFalso>, extras: Record<string, unknown>) {
  return { arf: { ...(base as unknown as { arf: object }).arf, ...extras } };
}

// ---------------------------------------------------------------------------------------
// A injeção como ponto de partida (RF-02)
// ---------------------------------------------------------------------------------------

describe("a injeção é o ponto de partida", () => {
  it("separa injeções de efeitos futuros e diz qual é o papel de cada nó", async () => {
    abrir();
    const partida = await screen.findByRole("region", { name: /Ponto de partida/ });
    expect(within(partida).getByText(ARF.nos[0]!.titulo)).toBeInTheDocument();
    // O efeito futuro NÃO é ponto de partida: ele é consequência, e a tela não os mistura.
    expect(within(partida).queryByText(ARF.nos[1]!.titulo)).toBeNull();
  });

  it("marca o efeito futuro que espelha um Efeito Indesejável como Efeito Desejável", async () => {
    abrir();
    const cadeia = await screen.findByRole("region", { name: /Efeitos desejáveis/ });
    const linha = within(cadeia).getByRole("listitem", { name: new RegExp(ARF.nos[1]!.titulo) });
    expect(within(linha).getByText("Efeito Desejável")).toBeInTheDocument();
  });

  it("mostra a leitura de suficiência montada pelo servidor, nunca remontada aqui", async () => {
    abrir();
    expect(await screen.findByText(ARF.elos[0]!.leitura)).toBeInTheDocument();
  });
});

// ---------------------------------------------------------------------------------------
// O ramo negativo e a poda (RF-08, RF-09, RN-04) — o coração desta tela
// ---------------------------------------------------------------------------------------

describe("ramo negativo com a poda", () => {
  it("desenha o ramo negativo em região PRÓPRIA, com estado por extenso", async () => {
    abrir();
    const ramos = await screen.findByRole("region", { name: /Ramos negativos/ });
    const ramo = within(ramos).getByRole("listitem", { name: new RegExp(ARF.nos[3]!.titulo) });
    // Nem só cor, nem só ícone: o estado sai por extenso e como dado no elemento.
    expect(ramo).toHaveAttribute("data-estado", "aberto");
    expect(within(ramo).getByText("Aberto")).toBeInTheDocument();
  });

  it("o nó raiz do ramo negativo não se confunde com um efeito desejável", async () => {
    abrir();
    const cadeia = await screen.findByRole("region", { name: /Efeitos desejáveis/ });
    const linha = within(cadeia).getByRole("listitem", { name: new RegExp(ARF.nos[3]!.titulo) });
    expect(linha).toHaveAttribute("data-ramo-negativo", "sim");
    expect(within(linha).queryByText("Efeito Desejável")).toBeNull();
  });

  it("podar exige a injeção que corta, e a tela só oferece injeções", async () => {
    const { cliente } = abrir();
    const ramos = await screen.findByRole("region", { name: /Ramos negativos/ });
    const seletor = within(ramos).getByLabelText("Injeção que corta o ramo");
    const opcoes = within(seletor).getAllByRole("option").map((o) => o.textContent);
    // O convite mais as DUAS injeções da árvore, e nenhum efeito futuro: um ramo negativo
    // é cortado por injeção adicional, nunca por um efeito (RN-04).
    expect(opcoes).toEqual(["escolha a injeção", ARF.nos[0]!.titulo, ARF.nos[4]!.titulo]);

    const espiao = vi.spyOn(cliente.arf, "mudarRamo");
    await userEvent.selectOptions(seletor, ARF.nos[4]!.id);
    await userEvent.click(within(ramos).getByRole("button", { name: "Podar com esta injeção" }));
    await waitFor(() =>
      expect(espiao).toHaveBeenCalledWith("p-arf", "r1", {
        estado: "tratado",
        injecao_de_corte_id: ARF.nos[4]!.id,
      }),
    );
  });

  it("aceitar um ramo exige justificativa — o botão não arma sem ela", async () => {
    const { cliente } = abrir();
    const ramos = await screen.findByRole("region", { name: /Ramos negativos/ });
    const aceitar = within(ramos).getByRole("button", { name: "Aceitar o efeito colateral" });
    expect(aceitar).toBeDisabled();

    const espiao = vi.spyOn(cliente.arf, "mudarRamo");
    await userEvent.type(
      within(ramos).getByLabelText("Por que este efeito colateral é aceitável?"),
      "A leitura fina fica com a coordenação, que já a faz hoje.",
    );
    expect(aceitar).toBeEnabled();
    await userEvent.click(aceitar);
    await waitFor(() =>
      expect(espiao).toHaveBeenCalledWith("p-arf", "r1", {
        estado: "aceito",
        justificativa: "A leitura fina fica com a coordenação, que já a faz hoje.",
      }),
    );
  });

  it("um ramo tratado mostra a poda que o corta e o caminho de volta", async () => {
    const tratada: Arf = {
      ...ARF,
      ramos: [{ ...ARF.ramos[0]!, estado: "tratado", injecao_de_corte_id: ARF.nos[4]!.id }],
      verificacao: { ...ARF.verificacao, ramos_abertos: [] },
    };
    const base = clienteFalso();
    abrir(comArf(base, { abrir: async () => tratada }));
    const ramos = await screen.findByRole("region", { name: /Ramos negativos/ });
    const ramo = within(ramos).getByRole("listitem", { name: new RegExp(ARF.nos[3]!.titulo) });
    expect(ramo).toHaveAttribute("data-estado", "tratado");
    expect(within(ramo).getByText(new RegExp(ARF.nos[4]!.titulo))).toBeInTheDocument();
    expect(within(ramo).getByRole("button", { name: "Reabrir o ramo" })).toBeInTheDocument();
  });

  it("sem ramo marcado a região DIZ o que falta, em vez de sumir", async () => {
    const base = clienteFalso();
    abrir(
      comArf(base, {
        abrir: async (): Promise<Arf> => ({
          ...ARF,
          ramos: [],
          verificacao: { ...ARF.verificacao, ramos_abertos: [] },
        }),
      }),
    );
    const ramos = await screen.findByRole("region", { name: /Ramos negativos/ });
    expect(
      within(ramos).getByText(/Nenhum ramo negativo marcado/),
    ).toBeInTheDocument();
  });
});

// ---------------------------------------------------------------------------------------
// A verificação estrutural (RF-11) — leitura, nunca veto
// ---------------------------------------------------------------------------------------

describe("verificação estrutural", () => {
  it("lista as pendências que o servidor apurou, sem recontar nada aqui", async () => {
    abrir();
    const painel = await screen.findByRole("region", { name: /Verificação/ });
    expect(within(painel).getByText(/1 injeção\(ões\) sem efeito/)).toBeInTheDocument();
    expect(within(painel).getByText(/1 ramo\(s\) negativo\(s\) aberto\(s\)/)).toBeInTheDocument();
    expect(within(painel).getByText(/Ainda não está pronta/)).toBeInTheDocument();
  });

  it("declara `sem origem vinculada` em vez de inventar cobertura (RF-07)", async () => {
    const base = clienteFalso();
    abrir(
      comArf(base, {
        abrir: async (): Promise<Arf> => ({
          ...ARF,
          origem: null,
          udes_da_cadeia: [],
          espelhos: [],
          verificacao: { ...ARF.verificacao, cobertura: [], sem_origem_vinculada: true },
        }),
      }),
    );
    const painel = await screen.findByRole("region", { name: /Verificação/ });
    expect(within(painel).getByText(/sem origem vinculada/i)).toBeInTheDocument();
  });
});

// ---------------------------------------------------------------------------------------
// Fluxo de erro — a recusa aparece com a próxima ação, e a tela não cai
// ---------------------------------------------------------------------------------------

describe("fluxo de erro", () => {
  it("desenha a recusa do servidor ao podar com um nó que não é injeção", async () => {
    const base = clienteFalso();
    const { cliente } = abrir(
      comArf(base, {
        mudarRamo: async () => {
          throw new ErroDaApi("MUTATION_REFUSED", "corte_nao_e_injecao", 409);
        },
      }),
    );
    const ramos = await screen.findByRole("region", { name: /Ramos negativos/ });
    await userEvent.selectOptions(
      within(ramos).getByLabelText("Injeção que corta o ramo"),
      ARF.nos[4]!.id,
    );
    await userEvent.click(within(ramos).getByRole("button", { name: "Podar com esta injeção" }));
    const alerta = await screen.findByRole("alert");
    expect(alerta).toHaveTextContent("A operação é válida, mas não neste estado do projeto.");
    // A árvore continua em tela: recusa de escrita não derruba leitura.
    expect(screen.getByRole("region", { name: /Ponto de partida/ })).toBeInTheDocument();
    expect(screen.getAllByText(ARF.nos[0]!.titulo).length).toBeGreaterThan(0);
    expect(cliente).toBeTruthy();
  });

  it("erro de carga desenha a tela de erro com a próxima ação", async () => {
    const base = clienteFalso();
    abrir(
      comArf(base, {
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
// Internacionalização (RI-10 da spec 005) — a tela nasce nos dois idiomas
// ---------------------------------------------------------------------------------------

describe("internacionalização", () => {
  it("desenha a mesma tela em inglês, com o vocabulário da TOC traduzido", async () => {
    abrir({}, "en");
    expect(await screen.findByRole("region", { name: /Starting point/ })).toBeInTheDocument();
    expect(screen.getByRole("region", { name: /Negative branches/ })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Prune with this injection" })).toBeInTheDocument();
  });
});
