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
import { ErroDaApi } from "../api/erros";

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

// O laço fechado (o defeito que faltava): a prévia mostrava o diff e não havia caminho
// para aceitar. Aceitar **não** é a tela escrever no estado — é criar uma proposta de ação
// que atravessa a máquina de estados no servidor e confirmá-la no gate. Depois disso a
// nuvem muda na tela porque foi **relida do serviço**, nunca porque a tela a alterou.
describe("tela da nuvem — o laço da assistência fecha pelo gate governado", () => {
  const RESULTADO = {
    versao: "1.0.0",
    racional: "O dilema entre reputação e expansão.",
    entidades: {
      A: "Reputação acadêmica sustentada",
      B: "b",
      C: "c",
      D: "d",
      D_PRIME: "d'",
    },
    arestas: { A_B: [], A_C: [], B_D: [], C_D_PRIME: [], D_C: [], D_PRIME_B: [], D_D_PRIME: [] },
  };
  const GERACAO = {
    action_id: "toc.generate_conflict_cloud",
    aviso: "nada foi aplicado",
    resultado: RESULTADO,
  };
  const PENDENTE = {
    proposal_id: "prop-9",
    action_id: "toc.generate_conflict_cloud",
    titulo: "Preencher a nuvem a partir de uma narrativa",
    risk: "confirm",
    requires_confirmation: true,
    origem: "ia",
    estado: "awaiting_approval",
    alvos: [],
    quantidade_de_alvos: 0,
    criada_em: "2026-09-06T10:00:00Z",
    vence_em: "2026-09-06T10:10:00Z",
    status: null,
    mensagem: "",
    outcomes: [],
  };

  /** A nuvem como o servidor a devolve DEPOIS de a proposta ter sido executada. */
  const NUVEM_APLICADA = {
    ...NUVEM,
    entidades: NUVEM.entidades.map((e) =>
      e.papel === "A" ? { ...e, texto: "Reputação acadêmica sustentada" } : e,
    ),
  };

  function cenario(decisao: Record<string, unknown>) {
    const base = clienteFalso();
    let leituras = 0;
    const abrirNuvem = vi.fn(async () => {
      leituras += 1;
      return leituras > 1 && decisao.status === "executed" ? NUVEM_APLICADA : NUVEM;
    });
    const criar = vi.fn(async () => PENDENTE);
    const decidir = vi.fn(async () => ({ ...PENDENTE, ...decisao }));
    const editarEntidade = vi.fn(async () => NUVEM);
    const cliente = {
      nc: { ...base.nc, gerar: vi.fn(async () => GERACAO), abrir: abrirNuvem, editarEntidade },
      propostas: { criar, decidir },
    };
    return { cliente, criar, decidir, editarEntidade, abrirNuvem };
  }

  async function gerarEAceitar(sobrescritas: Record<string, unknown>) {
    abrir(sobrescritas);
    await screen.findByTestId("entidade-A");
    await userEvent.type(screen.getByLabelText(/Narrativa do dilema/), "Crescer sem perder qualidade.");
    await userEvent.click(screen.getByRole("button", { name: /Gerar a partir da narrativa/ }));
    const previa = await screen.findByRole("region", { name: /Pré-visualização/ });
    await userEvent.click(within(previa).getByRole("button", { name: /Aceitar/ }));
  }

  it("aceitar cria a proposta governada com o resultado que a prévia mostrou", async () => {
    const { cliente, criar, editarEntidade } = cenario({ estado: "executed", status: "executed" });
    await gerarEAceitar(cliente);

    await waitFor(() => expect(criar).toHaveBeenCalledTimes(1));
    expect(criar).toHaveBeenCalledWith({
      action_id: "toc.generate_conflict_cloud",
      args: {
        projeto_id: "p-nc",
        narrativa: "Crescer sem perder qualidade.",
        resultado: RESULTADO,
      },
    });
    // A tela NÃO escreve: nenhum comando de mutação da nuvem foi chamado.
    expect(editarEntidade).not.toHaveBeenCalled();
    expect(await screen.findByRole("region", { name: /Confirmar a proposta/ })).toBeInTheDocument();
  });

  it("confirmar no gate muda a nuvem na tela — e a mudança vem do servidor", async () => {
    const { cliente, decidir, abrirNuvem } = cenario({
      estado: "executed",
      status: "executed",
      mensagem: "5 entidade(s) aplicadas",
    });
    await gerarEAceitar(cliente);
    const gate = await screen.findByRole("region", { name: /Confirmar a proposta/ });

    await userEvent.click(within(gate).getByRole("button", { name: /Confirmar/ }));

    await waitFor(() => expect(decidir).toHaveBeenCalledWith("prop-9", true));
    // A nuvem foi RELIDA (duas leituras: a de abertura e a de depois da decisão) e o texto
    // novo está na tela — a persistência é do serviço, não estado local.
    await waitFor(() => expect(abrirNuvem.mock.calls.length).toBeGreaterThan(1));
    expect(
      await within(await screen.findByTestId("entidade-A")).findByText("Reputação acadêmica sustentada"),
    ).toBeInTheDocument();
  });

  it("recusar no gate deixa a nuvem intacta e o desfecho aparece — nunca em silêncio", async () => {
    const { cliente, decidir } = cenario({
      estado: "denied",
      status: "denied",
      mensagem: "recusada por quem decide",
    });
    await gerarEAceitar(cliente);
    const gate = await screen.findByRole("region", { name: /Confirmar a proposta/ });

    await userEvent.click(within(gate).getByRole("button", { name: /Recusar/ }));

    await waitFor(() => expect(decidir).toHaveBeenCalledWith("prop-9", false));
    expect(await screen.findByRole("status")).toHaveTextContent(/Recusado. Nada foi escrito/);
    expect(within(screen.getByTestId("entidade-A")).getByText("Reputação acadêmica preservada")).toBeInTheDocument();
  });

  it("a recusa do servidor ao criar a proposta vira frase, e a prévia continua lá", async () => {
    const base = clienteFalso();
    const cliente = {
      nc: { ...base.nc, gerar: vi.fn(async () => GERACAO) },
      propostas: {
        criar: vi.fn(async () => {
          throw new ErroDaApi("ACTION_NOT_FOUND", "ação indisponível para este principal", 404);
        }),
        decidir: vi.fn(),
      },
    };
    await gerarEAceitar(cliente);

    expect(await screen.findByRole("alert")).toBeInTheDocument();
    expect(screen.getByRole("region", { name: /Pré-visualização/ })).toBeInTheDocument();
  });
});
