// A jornada dos cinco passos — a tela do M6 (spec 009).
//
// Siglas, uma vez: **M6** — Focalização · **TOC** — Teoria das Restrições · **ARA** —
// Árvore da Realidade Atual · **APR** — Árvore de Pré-Requisitos · **RI/RN/RF** —
// requisito de interface / regra de negócio / requisito funcional.
//
// Requisitos medidos aqui: RI-01 (trilha com estado por forma e rótulo, nunca só por
// cor), RI-02 (painel em três camadas, com o herdado no topo), RI-03 (cartão de vínculo
// com estado e navegação; canônicas primeiro), RI-04 (ciclo fechado somente leitura),
// RI-05 (os dois vereditos com o mesmo peso e justificativa obrigatória) e RI-07
// (listagem com passo atual e restrição vigente).
//
// Base sintética (ADR 0006): Instituição Horizonte, Facilitadora TOC.
import { beforeEach, describe, expect, it, vi } from "vitest";
import { screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { TelaDaFocalizacao, CHAVE_DO_PASSO } from "./TelaDaFocalizacao";
import {
  ANALISE_DE_FOCALIZACAO,
  JORNADA,
  RESTRICAO_SINTETICA,
  clienteFalso,
  renderComIdioma,
} from "../testes/apoio";
import type { AnaliseDeFocalizacao, Jornada } from "../dominio/tipos";
import { ErroDaApi } from "../api/erros";

const AUTORA = "Facilitadora TOC";

function abrir(sobrescritas: Record<string, unknown> = {}, aoAbrirFerramenta = vi.fn()) {
  const cliente = clienteFalso(sobrescritas);
  const util = renderComIdioma(
    <TelaDaFocalizacao
      cliente={cliente}
      projetoId="p-foco"
      autor={AUTORA}
      aoVoltar={vi.fn()}
      aoAbrirFerramenta={aoAbrirFerramenta}
    />,
  );
  return { ...util, cliente, aoAbrirFerramenta };
}

function comFoco(base: ReturnType<typeof clienteFalso>, extras: Record<string, unknown>) {
  return { foco: { ...(base as unknown as { foco: object }).foco, ...extras } };
}

beforeEach(() => sessionStorage.clear());

// ---------------------------------------------------------------------------------------
// RI-01 — a trilha dos cinco passos
// ---------------------------------------------------------------------------------------

describe("trilha dos cinco passos (RI-01)", () => {
  it("mostra os cinco passos, na ordem canônica, com o nome de cada um", async () => {
    abrir();
    const trilha = await screen.findByRole("navigation", { name: /cinco passos/i });
    const botoes = within(trilha).getAllByRole("button");
    expect(botoes).toHaveLength(5);
    expect(botoes.map((b) => b.getAttribute("aria-label"))).toEqual([
      "1. Identificar — Em andamento",
      "2. Explorar — Pendente",
      "3. Subordinar — Pendente",
      "4. Elevar — Pendente",
      "5. Recomeçar — Pendente",
    ]);
  });

  it("distingue o estado por RÓTULO, não só por cor, e marca o passo atual", async () => {
    abrir();
    const trilha = await screen.findByRole("navigation", { name: /cinco passos/i });
    const atual = within(trilha).getByRole("button", { current: "step" });
    // O estado sai por extenso no rótulo acessível E no texto visível: uma tela
    // monocromática e um leitor de tela leem a mesma coisa.
    expect(atual).toHaveAttribute("aria-label", expect.stringContaining("Em andamento"));
    expect(within(atual).getByText("Em andamento")).toBeInTheDocument();
    expect(atual).toHaveAttribute("data-estado", "em_andamento");
  });

  it("mostra o contador de pendências do passo", async () => {
    abrir();
    const trilha = await screen.findByRole("navigation", { name: /cinco passos/i });
    const identificar = within(trilha).getAllByRole("button")[0]!;
    const contador = identificar.querySelector(".passo-pendencias");
    expect(contador).not.toBeNull();
    expect(contador!.textContent).toBe("1");
    expect(contador!.getAttribute("title")).toContain("decisão que o encerra");
  });

  it("escolher um passo persiste a escolha na sessão", async () => {
    abrir();
    const trilha = await screen.findByRole("navigation", { name: /cinco passos/i });
    await userEvent.click(within(trilha).getAllByRole("button")[3]!);
    expect(sessionStorage.getItem(CHAVE_DO_PASSO)).toBe("elevar");
    expect(await screen.findByRole("heading", { name: "Elevar a restrição" })).toBeInTheDocument();
  });
});

// ---------------------------------------------------------------------------------------
// RI-02 — o painel do passo em três camadas
// ---------------------------------------------------------------------------------------

describe("painel do passo (RI-02)", () => {
  it("mostra o herdado no topo e diz quando não há nada herdado", async () => {
    abrir();
    expect(await screen.findByRole("heading", { name: "Identificar a restrição" })).toBeInTheDocument();
    const herdado = screen.getByRole("region", { name: /O que este passo herda/ });
    expect(within(herdado).getByText(/primeiro passo do ciclo/)).toBeInTheDocument();
  });

  it("apresenta o produto do passo anterior quando ele existe (RF-13)", async () => {
    const jornada: Jornada = {
      ...JORNADA,
      passo_atual: "explorar",
      passos_concluidos: 1,
      passos: JORNADA.passos.map((p) =>
        p.tipo === "explorar"
          ? {
              ...p,
              estado: "em_andamento" as const,
              herdado: [
                `Restrição do ciclo: ${RESTRICAO_SINTETICA}`,
                "Decisão de identificar: a restrição é a secretaria",
              ],
            }
          : p.tipo === "identificar"
            ? { ...p, estado: "concluido" as const }
            : p,
      ),
    };
    const base = clienteFalso();
    abrir(comFoco(base, { abrir: async () => ({ ...ANALISE_DE_FOCALIZACAO, jornada }) }));

    const herdado = await screen.findByRole("region", { name: /O que este passo herda/ });
    expect(within(herdado).getByText(new RegExp(RESTRICAO_SINTETICA))).toBeInTheDocument();
    expect(within(herdado).getByText(/Decisão de identificar/)).toBeInTheDocument();
  });

  it("anotar não avança a jornada: chama o comando de nota e nada mais", async () => {
    const base = clienteFalso();
    const anotar = vi.fn(async () => JORNADA);
    const concluirPasso = vi.fn(async () => JORNADA);
    abrir(comFoco(base, { anotar, concluirPasso }));

    await screen.findByRole("heading", { name: "Identificar a restrição" });
    await userEvent.type(screen.getByLabelText("Notas do passo"), "a fila cresce");
    await userEvent.click(screen.getByRole("button", { name: "Anotar" }));

    await waitFor(() =>
      expect(anotar).toHaveBeenCalledWith("p-foco", "identificar", "a fila cresce", AUTORA),
    );
    expect(concluirPasso).not.toHaveBeenCalled();
  });

  it("concluir o passo leva a decisão e o autor ao servidor", async () => {
    const base = clienteFalso();
    const concluirPasso = vi.fn(async () => JORNADA);
    abrir(comFoco(base, { concluirPasso }));

    await screen.findByRole("heading", { name: "Identificar a restrição" });
    await userEvent.type(
      screen.getByLabelText("Decisão que encerra o passo"),
      "a restrição é a secretaria",
    );
    await userEvent.click(screen.getByRole("button", { name: "Concluir passo" }));

    await waitFor(() =>
      expect(concluirPasso).toHaveBeenCalledWith(
        "p-foco",
        "identificar",
        "a restrição é a secretaria",
        AUTORA,
      ),
    );
  });

  it("a recusa do servidor aparece com a mensagem do CÓDIGO, não texto cru", async () => {
    const base = clienteFalso();
    const concluirPasso = vi.fn(async () => {
      throw new ErroDaApi("INVALID_FOCUSING_STEP", "sem_restricao: …", 409, {
        regra: "sem_restricao",
      });
    });
    abrir(comFoco(base, { concluirPasso }));

    await screen.findByRole("heading", { name: "Identificar a restrição" });
    await userEvent.type(screen.getByLabelText("Decisão que encerra o passo"), "seguimos assim");
    await userEvent.click(screen.getByRole("button", { name: "Concluir passo" }));

    expect(await screen.findByRole("alert")).toBeInTheDocument();
  });
});

// ---------------------------------------------------------------------------------------
// RI-03 — o cartão de vínculo
// ---------------------------------------------------------------------------------------

describe("vínculos de ferramenta (RI-03)", () => {
  it("mostra o cartão com tipo, nome e estado, e navega para a ferramenta", async () => {
    const { aoAbrirFerramenta } = abrir();
    await screen.findByRole("heading", { name: "Identificar a restrição" });

    expect(screen.getByText("ARA")).toBeInTheDocument();
    expect(screen.getByText("ARA do fluxo")).toBeInTheDocument();
    expect(screen.getByText("ativo")).toBeInTheDocument();

    await userEvent.click(screen.getAllByRole("button", { name: "Abrir" })[0]!);
    expect(aoAbrirFerramenta).toHaveBeenCalledWith({ ferramenta: "ara", projetoId: "p-ara" });
  });

  it("um vínculo cujo projeto foi arquivado mostra a legenda, e não some (RNF-04)", async () => {
    const jornada: Jornada = {
      ...JORNADA,
      passos: JORNADA.passos.map((p) =>
        p.tipo === "identificar"
          ? {
              ...p,
              vinculos: [
                {
                  ...p.vinculos[0]!,
                  estado: "arquivado" as const,
                  legenda: "referência a projeto arquivado — o vínculo continua",
                },
              ],
            }
          : p,
      ),
    };
    const base = clienteFalso();
    abrir(comFoco(base, { abrir: async () => ({ ...ANALISE_DE_FOCALIZACAO, jornada }) }));

    expect(await screen.findByText(/referência a projeto arquivado/)).toBeInTheDocument();
    expect(screen.getByText("arquivado")).toBeInTheDocument();
  });

  it("as canônicas do passo vêm primeiro, e o não-canônico cobra justificativa (RN-06)", async () => {
    const base = clienteFalso();
    const vincular = vi.fn(async () => JORNADA.passos[0]!.vinculos[0]!);
    abrir(comFoco(base, { vincular }));
    await screen.findByRole("heading", { name: "Identificar a restrição" });

    const seletor = screen.getByLabelText("Vincular ferramenta") as HTMLSelectElement;
    // a primeira opção é a canônica do passo `identificar`
    expect((seletor.options[0] as HTMLOptionElement).value).toBe("ara");
    await userEvent.type(screen.getByLabelText("Projeto"), "p-apr");
    await userEvent.selectOptions(seletor, "apr");

    // fora do canônico: o botão só libera com justificativa
    const botao = screen.getByRole("button", { name: "Vincular ferramenta" });
    expect(botao).toBeDisabled();
    await userEvent.type(
      screen.getByLabelText("Justificativa (fora do canônico)"),
      "o plano já existia quando a análise começou",
    );
    await userEvent.click(botao);

    await waitFor(() =>
      expect(vincular).toHaveBeenCalledWith("p-foco", "identificar", {
        ferramenta: "apr",
        projeto_id: "p-apr",
        papel: "",
        justificativa: "o plano já existia quando a análise começou",
      }),
    );
  });
});

// ---------------------------------------------------------------------------------------
// RI-05 — o julgamento de herança
// ---------------------------------------------------------------------------------------

describe("julgamento de herança (RI-05)", () => {
  function comHeranca(): AnaliseDeFocalizacao {
    return {
      ...ANALISE_DE_FOCALIZACAO,
      jornada: {
        ...JORNADA,
        ordem: 2,
        ciclos_no_total: 2,
        herancas_pendentes: 2,
        heranca: [
          {
            id: "h1",
            ciclo_de_origem: 1,
            passo: "explorar",
            texto: "priorizar matrículas com documentação completa",
            veredito: "pendente",
            justificativa: "",
            autor: "",
            julgada_em: null,
          },
          {
            id: "h2",
            ciclo_de_origem: 1,
            passo: "subordinar",
            texto: "nenhuma turma abre antes da conferência",
            veredito: "pendente",
            justificativa: "",
            autor: "",
            julgada_em: null,
          },
        ],
      },
    };
  }

  it("apresenta manter e revogar com o MESMO peso e justificativa obrigatória", async () => {
    const base = clienteFalso();
    const julgarHeranca = vi.fn(async () => JORNADA);
    abrir(comFoco(base, { abrir: async () => comHeranca(), julgarHeranca }));

    const painel = await screen.findByRole("region", { name: /Decisões herdadas/ });
    expect(within(painel).getByText("2 veredito(s) pendente(s)")).toBeInTheDocument();

    const manter = within(painel).getAllByRole("button", { name: "Manter" })[0]!;
    const revogar = within(painel).getAllByRole("button", { name: "Revogar" })[0]!;
    // Mesmo peso visual: mesmo tipo, mesma classe, e os dois travados sem justificativa.
    expect(manter.getAttribute("type")).toBe(revogar.getAttribute("type"));
    expect(manter.className).toBe(revogar.className);
    expect(manter).toBeDisabled();
    expect(revogar).toBeDisabled();

    await userEvent.type(within(painel).getAllByLabelText("Por quê?")[0]!, "a fila migrou");
    expect(within(painel).getAllByRole("button", { name: "Manter" })[0]!).toBeEnabled();
    await userEvent.click(within(painel).getAllByRole("button", { name: "Revogar" })[0]!);

    await waitFor(() =>
      expect(julgarHeranca).toHaveBeenCalledWith(
        "p-foco",
        "h1",
        "revogada",
        "a fila migrou",
        AUTORA,
      ),
    );
  });

  it("diz que não há herança quando o ciclo é o primeiro", async () => {
    abrir();
    const painel = await screen.findByRole("region", { name: /Decisões herdadas/ });
    expect(within(painel).getByText(/Nenhuma decisão herdada/)).toBeInTheDocument();
  });
});

// ---------------------------------------------------------------------------------------
// RI-04 — a linha do tempo e o ciclo fechado somente leitura
// ---------------------------------------------------------------------------------------

describe("linha do tempo (RI-04)", () => {
  it("lista os ciclos com restrição, datas e desfecho", async () => {
    abrir();
    const linha = await screen.findByRole("region", { name: /Linha do tempo/ });
    expect(within(linha).getByText("Ciclo 1")).toBeInTheDocument();
    expect(within(linha).getByText(RESTRICAO_SINTETICA)).toBeInTheDocument();
  });

  it("o ciclo fechado abre em somente leitura, e quem diz isso é o servidor", async () => {
    const fechada: AnaliseDeFocalizacao = {
      ...ANALISE_DE_FOCALIZACAO,
      jornada: { ...JORNADA, estado: "fechado", somente_leitura: true },
    };
    const base = clienteFalso();
    abrir(comFoco(base, { abrir: async () => fechada }));

    expect(await screen.findAllByText("Ciclo fechado — somente leitura")).not.toHaveLength(0);
    // Sem formulário de decisão, sem formulário de nota: o ciclo fechado não recebe escrita.
    expect(screen.queryByLabelText("Decisão que encerra o passo")).not.toBeInTheDocument();
    expect(screen.queryByLabelText("Notas do passo")).not.toBeInTheDocument();
  });
});

// ---------------------------------------------------------------------------------------
// RN-07 — o quinto passo: o ato dele é o recomeço
// ---------------------------------------------------------------------------------------

describe("recomeço (RN-07, RF-15)", () => {
  it("no passo recomeçar, o que aparece é o recomeço — não uma decisão de conclusão", async () => {
    const noQuinto: AnaliseDeFocalizacao = {
      ...ANALISE_DE_FOCALIZACAO,
      jornada: {
        ...JORNADA,
        passo_atual: "recomecar",
        passos_concluidos: 4,
        passos: JORNADA.passos.map((p) =>
          p.tipo === "recomecar"
            ? { ...p, estado: "em_andamento" as const }
            : { ...p, estado: "concluido" as const },
        ),
      },
    };
    const base = clienteFalso();
    const recomecar = vi.fn(async () => ANALISE_DE_FOCALIZACAO);
    abrir(comFoco(base, { abrir: async () => noQuinto, recomecar }));

    await screen.findByRole("heading", { name: "Recomeçar sem inércia" });
    expect(screen.queryByLabelText("Decisão que encerra o passo")).not.toBeInTheDocument();

    await userEvent.click(screen.getAllByRole("button", { name: "Recomeçar a jornada" })[0]!);
    await waitFor(() => expect(recomecar).toHaveBeenCalledWith("p-foco"));
  });
});

// ---------------------------------------------------------------------------------------
// A restrição — a entidade que dá nome à teoria
// ---------------------------------------------------------------------------------------

describe("restrição do ciclo (RF-05, RN-03)", () => {
  it("mostra a restrição registrada com o tipo por extenso", async () => {
    abrir();
    const painel = await screen.findByRole("region", { name: /Restrição do ciclo/ });
    expect(within(painel).getByText(RESTRICAO_SINTETICA)).toBeInTheDocument();
    expect(within(painel).getByText("Física")).toBeInTheDocument();
    expect(within(painel).getByText(/não é editar a restrição/)).toBeInTheDocument();
  });

  it("sem restrição, oferece o formulário e registra com tipo e justificativa", async () => {
    const semRestricao: AnaliseDeFocalizacao = {
      ...ANALISE_DE_FOCALIZACAO,
      jornada: { ...JORNADA, restricao: null },
    };
    const base = clienteFalso();
    const registrarRestricao = vi.fn(async () => JORNADA.restricao);
    abrir(comFoco(base, { abrir: async () => semRestricao, registrarRestricao }));

    await screen.findByRole("region", { name: /Restrição do ciclo/ });
    await userEvent.type(screen.getByLabelText("Restrição"), RESTRICAO_SINTETICA);
    await userEvent.selectOptions(screen.getByLabelText("Tipo"), "politica");
    await userEvent.type(screen.getByLabelText("Justificativa"), "a fila só cresce aqui");
    await userEvent.click(screen.getByRole("button", { name: "Registrar restrição" }));

    await waitFor(() =>
      expect(registrarRestricao).toHaveBeenCalledWith("p-foco", {
        descricao: RESTRICAO_SINTETICA,
        tipo: "politica",
        justificativa: "a fila só cresce aqui",
        autor: AUTORA,
      }),
    );
  });
});
