// A Árvore da Realidade Atual (ARA) inteira — canvas, painel, ficha, exame de elo,
// conector E e relatório estrutural, falando com o serviço de verdade (aqui, um duplo).
//
// Requisitos: RI-01 (selo com status por cor E texto), RI-05 (exame acionável na aresta e
// na linha), RI-07 (relatório em painel com foco), RI-09 (resumo por status no cabeçalho
// com filtro de um clique) da spec 005; RI-06 (desfazer nomeando o episódio) da spec 004.
import { describe, expect, it, vi } from "vitest";
import { screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { TelaDaAra } from "./TelaDaAra";
import { ARA, NUVEM, PROJETO_RESUMO, UDE, clienteFalso, renderComIdioma } from "../testes/apoio";

function abrir(sobrescritas: Record<string, unknown> = {}) {
  const cliente = clienteFalso(sobrescritas);
  const util = renderComIdioma(<TelaDaAra cliente={cliente} projetoId="p1" aoVoltar={vi.fn()} />);
  return { ...util, cliente };
}

describe("tela da ARA — fluxo feliz", () => {
  it("abre o projeto e desenha nós, arestas e painel", async () => {
    abrir();
    expect(await screen.findByRole("button", { name: /Prazos são perdidos/ })).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: /Nós \(2\)/ })).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: /Arestas \(1\)/ })).toBeInTheDocument();
  });

  it("mostra o resumo de UDEs por status no cabeçalho (RI-09)", async () => {
    abrir();
    const resumo = await screen.findByRole("group", { name: /UDEs por status/ });
    expect(within(resumo).getByRole("button", { name: /Pendente.*1/ })).toBeInTheDocument();
  });

  it("filtra a vista tabular por status com um clique (RI-09)", async () => {
    const base = clienteFalso();
    const comDois = {
      ...ARA,
      udes: [UDE, { ...UDE, no_id: "n2", titulo: "Retrabalho consome a equipe", status: "validado" as const }],
      resumo_por_status: { pendente: 1, requer_refinamento: 0, validado: 1, rejeitado: 0 },
    };
    abrir({ ara: { ...base.ara, abrir: async () => comDois } });
    const resumo = await screen.findByRole("group", { name: /UDEs por status/ });
    await userEvent.click(within(resumo).getByRole("button", { name: /Validado.*1/ }));
    const linhas = screen.getAllByRole("row").slice(1);
    expect(linhas).toHaveLength(1);
    expect(linhas[0]).toHaveTextContent("Retrabalho consome a equipe");
  });

  it("o selo do UDE mostra o status por texto, não só por cor (RI-01)", async () => {
    abrir();
    await screen.findByRole("button", { name: /Prazos são perdidos/ });
    const selos = screen.getAllByText("Pendente");
    expect(selos.length).toBeGreaterThan(0);
  });

  it("cria efeito pela rota da ARA — o tipo é decisão do servidor", async () => {
    const base = clienteFalso();
    const adicionarEfeito = vi.fn(async () => ({
      id: "n9",
      titulo: "Novo efeito",
      descricao: "",
      tipo: "efeito",
      posicao: { x: 80, y: 80 },
      recolhido: false,
    }));
    abrir({ ara: { ...base.ara, adicionarEfeito } });
    await screen.findByRole("button", { name: /Prazos são perdidos/ });
    await userEvent.click(screen.getByRole("button", { name: /^Novo nó$/ }));
    await waitFor(() => expect(adicionarEfeito).toHaveBeenCalled());
  });

  it("editar o título de um UDE REFORMULA (reexecuta a validação), não é edição crua", async () => {
    const base = clienteFalso();
    const reformular = vi.fn(async () => ARA.projeto.nos[0]!);
    const editarNo = vi.fn(async () => ARA.projeto.nos[0]!);
    abrir({
      ara: { ...base.ara, reformular },
      grafo: { ...base.grafo, editarNo },
    });
    await userEvent.dblClick(await screen.findByRole("button", { name: /Prazos são perdidos/ }));
    // O campo do canvas, e não o da ficha: selecionar o nó abre a ficha do UDE junto.
    const campo = screen.getByLabelText("Editar nó");
    await userEvent.clear(campo);
    await userEvent.type(campo, "Prazos combinados são perdidos{Enter}");
    await waitFor(() => expect(reformular).toHaveBeenCalledWith("p1", "n1", "Prazos combinados são perdidos"));
    expect(editarNo).not.toHaveBeenCalled();
  });
});

describe("tela da ARA — desfazer por episódio (RI-06 da spec 004)", () => {
  it("o botão nomeia o episódio e o desfazer devolve a posição anterior", async () => {
    const base = clienteFalso();
    const moverNo = vi.fn(async (_projeto: string, _no: string, _posicao: { x: number; y: number }) =>
      ARA.projeto.nos[0]!);
    abrir({ grafo: { ...base.grafo, moverNo } });
    await screen.findByRole("button", { name: /Prazos são perdidos/ });

    // A linha do painel move o nó por teclado: é o caminho que não exige arrastar.
    await userEvent.click(screen.getAllByRole("button", { name: /Focar/ })[0]!);
    const no = screen.getByRole("button", { name: /Prazos são perdidos/ });
    no.focus();
    await userEvent.keyboard("{ArrowRight}");
    await waitFor(() => expect(moverNo).toHaveBeenCalledTimes(1));

    const desfazer = await screen.findByRole("button", { name: /Desfazer: mover nó/ });
    await userEvent.click(desfazer);
    await waitFor(() => expect(moverNo).toHaveBeenCalledTimes(2));
    expect(moverNo.mock.calls[1]![2]).toEqual({ x: 0, y: 0 });
  });

  it("sem episódio, o botão de desfazer não promete nada", async () => {
    abrir();
    await screen.findByRole("button", { name: /Prazos são perdidos/ });
    expect(screen.getByRole("button", { name: /Nada a desfazer/ })).toBeDisabled();
  });
});

describe("tela da ARA — ficha, exame e relatório", () => {
  it("abre a ficha de validação do UDE selecionado, com as duas seções", async () => {
    abrir();
    await userEvent.click(await screen.findByRole("button", { name: /Prazos são perdidos/ }));
    expect(await screen.findByRole("region", { name: /Critérios decidíveis/ })).toBeInTheDocument();
    expect(screen.getByRole("region", { name: /Critérios de julgamento/ })).toBeInTheDocument();
  });

  it("examina o elo pela linha da aresta, e a reserva é exigida no estado que a pede", async () => {
    const base = clienteFalso();
    const examinarElo = vi.fn(async () => ({ aresta_id: "a1", estado: "com_reserva" as const, reserva: "só com fila" }));
    abrir({ ara: { ...base.ara, examinarElo } });
    await screen.findByRole("button", { name: /Prazos são perdidos/ });
    await userEvent.click(screen.getByRole("tab", { name: /Arestas/ }));
    await userEvent.click(screen.getByRole("button", { name: /Examinar elo/ }));
    await userEvent.selectOptions(screen.getByLabelText(/Estado do exame/), "com_reserva");
    await userEvent.click(screen.getByRole("button", { name: /Registrar exame/ }));
    expect(screen.getByRole("alert")).toHaveTextContent(/reserva escrita/i);
    expect(examinarElo).not.toHaveBeenCalled();
    await userEvent.type(screen.getByLabelText(/^Reserva/), "só com fila");
    await userEvent.click(screen.getByRole("button", { name: /Registrar exame/ }));
    await waitFor(() =>
      expect(examinarElo).toHaveBeenCalledWith("p1", "a1", "com_reserva", "só com fila"),
    );
  });

  it("roda a análise estrutural e mostra o relatório com foco por item (RI-07)", async () => {
    abrir();
    await screen.findByRole("button", { name: /Prazos são perdidos/ });
    await userEvent.click(screen.getByRole("button", { name: /Analisar árvore/ }));
    const relatorio = await screen.findByRole("complementary", { name: /Relatório estrutural/ });
    expect(within(relatorio).getByText(/Causa raiz candidata/)).toBeInTheDocument();
    expect(within(relatorio).getAllByRole("button", { name: /Focar/ }).length).toBeGreaterThan(0);
  });
});

describe("tela da ARA — fluxo de erro", () => {
  it("falha ao abrir vira tela desenhada com tentar de novo", async () => {
    const base = clienteFalso();
    let falhas = 1;
    const abrirAra = vi.fn(async () => {
      if (falhas-- > 0) throw Object.assign(new Error("x"), { codigo: "NOT_FOUND", status: 404 });
      return ARA;
    });
    abrir({ ara: { ...base.ara, abrir: abrirAra } });
    expect(await screen.findByRole("alert")).toHaveTextContent(/não existe/i);
    await userEvent.click(screen.getByRole("button", { name: /Tentar de novo/ }));
    expect(await screen.findByRole("button", { name: /Prazos são perdidos/ })).toBeInTheDocument();
  });

  it("recusa de escrita não derruba a tela: a árvore continua lá, com o aviso", async () => {
    const base = clienteFalso();
    abrir({
      ara: {
        ...base.ara,
        adicionarEfeito: async () => {
          throw Object.assign(new Error("x"), { codigo: "UNAUTHORIZED", status: 403 });
        },
      },
    });
    await screen.findByRole("button", { name: /Prazos são perdidos/ });
    await userEvent.click(screen.getByRole("button", { name: /^Novo nó$/ }));
    expect(await screen.findByRole("alert")).toHaveTextContent(/permissão/i);
    expect(screen.getByRole("button", { name: /Prazos são perdidos/ })).toBeInTheDocument();
  });
});

describe("tela da ARA — projeto no cabeçalho", () => {
  it("mostra o nome do projeto e o caminho de volta", async () => {
    const aoVoltar = vi.fn();
    const cliente = clienteFalso();
    renderComIdioma(<TelaDaAra cliente={cliente} projetoId="p1" aoVoltar={aoVoltar} />);
    expect(await screen.findByRole("heading", { name: PROJETO_RESUMO.nome })).toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: /Voltar/ }));
    expect(aoVoltar).toHaveBeenCalled();
  });
});

describe("tela da ARA — marcar Efeito Indesejável e derivar a nuvem", () => {
  it("marca um nó como UDE pelo painel, e o selo passa a aparecer", async () => {
    const base = clienteFalso();
    const marcarUde = vi.fn(async () => ({}));
    abrir({ ara: { ...base.ara, marcarUde } });
    await screen.findByRole("button", { name: /Prazos são perdidos/ });
    // `n2` ainda não é UDE no duplo: é a linha dele que oferece a marcação.
    const linha = screen.getByRole("row", { name: /Retrabalho consome a equipe/ });
    await userEvent.click(within(linha).getByRole("button", { name: /Marcar como Efeito Indesejável/ }));
    await waitFor(() => expect(marcarUde).toHaveBeenCalledWith("p1", "n2"));
  });

  it("desmarca o UDE existente", async () => {
    const base = clienteFalso();
    const desmarcarUde = vi.fn(async () => undefined);
    abrir({ ara: { ...base.ara, desmarcarUde } });
    const linha = await screen.findByRole("row", { name: /Prazos são perdidos/ });
    await userEvent.click(within(linha).getByRole("button", { name: /Desmarcar/ }));
    await waitFor(() => expect(desmarcarUde).toHaveBeenCalledWith("p1", "n1"));
  });

  it("deriva a Nuvem de Conflito dos UDEs escolhidos — o encadeamento entre as ferramentas", async () => {
    const base = clienteFalso();
    const derivar = vi.fn(async () => ({ ...NUVEM, id: "p-nc-novo" }));
    const aoAbrirNuvem = vi.fn();
    const cliente = clienteFalso({ nc: { ...base.nc, derivar } });
    renderComIdioma(
      <TelaDaAra cliente={cliente} projetoId="p1" aoVoltar={vi.fn()} aoAbrirNuvem={aoAbrirNuvem} />,
    );
    const linha = await screen.findByRole("row", { name: /Prazos são perdidos/ });
    await userEvent.click(within(linha).getByRole("checkbox", { name: /Derivar/ }));
    await userEvent.click(screen.getByRole("button", { name: /Derivar da ARA \(1\)/ }));
    await waitFor(() => expect(derivar).toHaveBeenCalledWith("p1", ["n1"], expect.stringContaining("Evasão")));
    expect(aoAbrirNuvem).toHaveBeenCalledWith("p-nc-novo");
  });

  it("sem UDE escolhido, derivar não é oferecido", async () => {
    abrir();
    await screen.findByRole("button", { name: /Prazos são perdidos/ });
    expect(screen.getByRole("button", { name: /Derivar da ARA \(0\)/ })).toBeDisabled();
  });

  it("forma o conector E com as arestas escolhidas (RI-06 da spec 005)", async () => {
    // Conector E é leitura CONJUNTA: exige duas ou mais causas que só produzem o efeito
    // juntas (RN-11). Por isso a árvore deste teste tem duas arestas no mesmo destino, e
    // por isso o botão só se oferece a partir da segunda escolha.
    const base = clienteFalso();
    const comDuasArestas = {
      ...ARA,
      projeto: {
        ...ARA.projeto,
        nos: [...ARA.projeto.nos, { ...ARA.projeto.nos[0]!, id: "n3", titulo: "Escopo muda no meio" }],
        arestas: [
          ...ARA.projeto.arestas,
          { id: "a2", origem_id: "n3", destino_id: "n2", rotulo: "" },
        ],
      },
    };
    const formarConector = vi.fn(async () => ({
      id: "c1",
      destino_id: "n2",
      arestas: ["a1", "a2"],
      leitura: "",
    }));
    abrir({ ara: { ...base.ara, abrir: async () => comDuasArestas, formarConector } });
    await screen.findByRole("button", { name: /Prazos são perdidos/ });
    await userEvent.click(screen.getByRole("tab", { name: /Arestas/ }));
    const escolhas = screen.getAllByRole("checkbox", { name: /Conector E/ });
    await userEvent.click(escolhas[0]!);
    expect(screen.getByRole("button", { name: /Formar conector E \(1\)/ })).toBeDisabled();
    await userEvent.click(escolhas[1]!);
    await userEvent.click(screen.getByRole("button", { name: /Formar conector E \(2\)/ }));
    await waitFor(() => expect(formarConector).toHaveBeenCalledWith("p1", ["a1", "a2"]));
  });
});

describe("tela da ARA — painel do nó e conectores E", () => {
  it("abre o painel lateral do nó (não modal) e salva a descrição", async () => {
    const base = clienteFalso();
    const editarNo = vi.fn(async () => ARA.projeto.nos[1]!);
    abrir({ grafo: { ...base.grafo, editarNo } });
    await screen.findByRole("button", { name: /Prazos são perdidos/ });
    // `n2` não é UDE: editar o texto dele é edição crua, e a descrição vive no painel.
    const linha = screen.getByRole("row", { name: /Retrabalho consome a equipe/ });
    await userEvent.click(within(linha).getByRole("button", { name: /Detalhe/ }));
    const painel = await screen.findByRole("complementary", { name: /Detalhe do nó/ });
    await userEvent.type(within(painel).getByLabelText(/Descrição/), "duas pessoas por sprint");
    await userEvent.click(within(painel).getByRole("button", { name: /Salvar/ }));
    await waitFor(() =>
      expect(editarNo).toHaveBeenCalledWith("p1", "n2", {
        titulo: "Retrabalho consome a equipe",
        descricao: "duas pessoas por sprint",
      }),
    );
  });

  it("lista os conectores E com a leitura conjunta e permite desfazê-los", async () => {
    const base = clienteFalso();
    const desfazerConector = vi.fn(async () => undefined);
    const comConector = {
      ...ARA,
      conectores: [
        {
          id: "c1",
          destino_id: "n2",
          arestas: ["a1"],
          leitura: "Prazos são perdidos E Escopo muda no meio ⇒ Retrabalho consome a equipe",
        },
      ],
    };
    abrir({ ara: { ...base.ara, abrir: async () => comConector, desfazerConector } });
    const conectores = await screen.findByRole("region", { name: /Conector E/ });
    expect(within(conectores).getByText(/Prazos são perdidos E Escopo muda no meio/)).toBeInTheDocument();
    await userEvent.click(within(conectores).getByRole("button", { name: /Desfazer conector/ }));
    await waitFor(() => expect(desfazerConector).toHaveBeenCalledWith("p1", "c1"));
  });
});
