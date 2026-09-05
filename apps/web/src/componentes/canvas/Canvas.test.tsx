// O canvas: a forma que a linhagem provou (`tocbuilderv3/APLICATION_PURPOSE.md:22-25`,
// "Canvas Visual Interativo"), com o que ela não tinha — teste.
//
// Requisitos exercitados: RI-01 (criar, mover, editar e excluir por manipulação direta),
// RI-02 (aresta direcionada, lida como "se causa, então efeito"), RI-03 (pan, zoom e
// ajustar à tela), RI-04 (edição de título inline, Enter confirma e Esc cancela), RI-05
// (o raio da exclusão aparece ANTES do clique final) e RI-06 (desfazer com o nome do
// episódio) — todos da spec 004.
import { describe, expect, it, vi } from "vitest";
import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { Canvas } from "./Canvas";
import { ProvedorDeIdioma } from "../../i18n";
import type { Aresta, No } from "../../dominio/tipos";

const NOS: No[] = [
  { id: "n1", titulo: "Prazos são perdidos", descricao: "", tipo: "efeito", posicao: { x: 0, y: 0 }, recolhido: false },
  { id: "n2", titulo: "Retrabalho consome a equipe", descricao: "", tipo: "efeito", posicao: { x: 300, y: 200 }, recolhido: false },
  { id: "n3", titulo: "Escopo muda no meio", descricao: "", tipo: "efeito", posicao: { x: 600, y: 0 }, recolhido: false },
];

const ARESTAS: Aresta[] = [
  { id: "a1", origem_id: "n1", destino_id: "n2", rotulo: "" },
  { id: "a2", origem_id: "n3", destino_id: "n2", rotulo: "" },
];

function montar(props: Partial<React.ComponentProps<typeof Canvas>> = {}) {
  const cbs = {
    aoSelecionar: vi.fn(),
    aoCriarNo: vi.fn(),
    aoMoverNo: vi.fn(),
    aoEditarTitulo: vi.fn(),
    aoExcluirNo: vi.fn(),
    aoLigar: vi.fn(),
    aoAbrirDetalhe: vi.fn(),
  };
  const util = render(
    <ProvedorDeIdioma>
      <Canvas nos={NOS} arestas={ARESTAS} selecionado={null} {...cbs} {...props} />
    </ProvedorDeIdioma>,
  );
  return { ...util, ...cbs };
}

describe("canvas — nós e arestas", () => {
  it("desenha cada nó com o seu título e cada aresta como ligação direcionada", () => {
    montar();
    for (const no of NOS) expect(screen.getByRole("button", { name: new RegExp(no.titulo) })).toBeInTheDocument();
    // RI-02: a aresta é lida como "se causa, então efeito" — e a leitura é textual,
    // não só uma seta que quem usa leitor de tela nunca vê.
    const arestas = screen.getAllByRole("img");
    expect(arestas).toHaveLength(2);
    expect(arestas[0]!).toHaveAccessibleName(/Prazos são perdidos.*Retrabalho consome a equipe/);
  });

  it("cria nó por manipulação direta, na posição do clique duplo no fundo", async () => {
    const { aoCriarNo } = montar();
    await userEvent.dblClick(screen.getByTestId("fundo-do-canvas"));
    expect(aoCriarNo).toHaveBeenCalledTimes(1);
    expect(aoCriarNo.mock.calls[0]![0]).toHaveProperty("x");
  });

  it("seleciona o nó ao clicar", async () => {
    const { aoSelecionar } = montar();
    await userEvent.click(screen.getByRole("button", { name: /Prazos são perdidos/ }));
    expect(aoSelecionar).toHaveBeenCalledWith("n1");
  });
});

describe("canvas — edição inline do título (RI-04)", () => {
  it("Enter confirma a edição", async () => {
    const { aoEditarTitulo } = montar();
    await userEvent.dblClick(screen.getByRole("button", { name: /Prazos são perdidos/ }));
    const campo = screen.getByRole("textbox");
    await userEvent.clear(campo);
    await userEvent.type(campo, "Prazos combinados são perdidos{Enter}");
    expect(aoEditarTitulo).toHaveBeenCalledWith("n1", "Prazos combinados são perdidos");
    expect(screen.queryByRole("textbox")).not.toBeInTheDocument();
  });

  it("Esc cancela sem salvar", async () => {
    const { aoEditarTitulo } = montar();
    await userEvent.dblClick(screen.getByRole("button", { name: /Prazos são perdidos/ }));
    await userEvent.type(screen.getByRole("textbox"), "lixo{Escape}");
    expect(aoEditarTitulo).not.toHaveBeenCalled();
    expect(screen.queryByRole("textbox")).not.toBeInTheDocument();
  });

  it("abre a edição pelo teclado, com o nó focado (F2)", async () => {
    montar();
    const no = screen.getByRole("button", { name: /Escopo muda no meio/ });
    no.focus();
    await userEvent.keyboard("{F2}");
    expect(screen.getByRole("textbox")).toHaveValue("Escopo muda no meio");
  });
});

describe("canvas — exclusão com raio declarado (RI-05)", () => {
  it("mostra quantas arestas saem junto ANTES do clique final", async () => {
    const { aoExcluirNo } = montar({ selecionado: "n2" });
    await userEvent.click(screen.getByRole("button", { name: /Excluir nó/ }));
    // n2 é destino de duas arestas: o raio aparece no próprio controle, antes de confirmar.
    const confirmacao = screen.getByRole("dialog");
    expect(within(confirmacao).getByText(/2 aresta/)).toBeInTheDocument();
    expect(aoExcluirNo).not.toHaveBeenCalled();
    await userEvent.click(within(confirmacao).getByRole("button", { name: /Confirmar/ }));
    expect(aoExcluirNo).toHaveBeenCalledWith("n2");
  });

  it("cancelar fecha a confirmação sem excluir", async () => {
    const { aoExcluirNo } = montar({ selecionado: "n1" });
    await userEvent.click(screen.getByRole("button", { name: /Excluir nó/ }));
    await userEvent.click(within(screen.getByRole("dialog")).getByRole("button", { name: /Cancelar/ }));
    expect(aoExcluirNo).not.toHaveBeenCalled();
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
  });
});

describe("canvas — ligar sem arrastar (RI-11 da spec 004: teclado alcança tudo)", () => {
  it("ligar: escolhe causa e efeito por clique, e a segunda escolha fecha a aresta", async () => {
    const { aoLigar } = montar();
    await userEvent.click(screen.getByRole("button", { name: /Ligar nós/ }));
    await userEvent.click(screen.getByRole("button", { name: /Prazos são perdidos/ }));
    expect(screen.getByText(/Causa: Prazos são perdidos/)).toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: /Escopo muda no meio/ }));
    expect(aoLigar).toHaveBeenCalledWith("n1", "n3");
  });

  it("Esc cancela o modo de ligação", async () => {
    const { aoLigar } = montar();
    await userEvent.click(screen.getByRole("button", { name: /Ligar nós/ }));
    await userEvent.keyboard("{Escape}");
    await userEvent.click(screen.getByRole("button", { name: /Prazos são perdidos/ }));
    expect(aoLigar).not.toHaveBeenCalled();
  });
});

describe("canvas — navegação (RI-03)", () => {
  it("aproximar, afastar e ajustar mudam a transformação do plano", async () => {
    montar();
    const plano = screen.getByTestId("plano-do-canvas");
    const inicial = plano.style.transform;
    await userEvent.click(screen.getByRole("button", { name: /Aproximar/ }));
    const depoisDeAproximar = plano.style.transform;
    expect(depoisDeAproximar).not.toBe(inicial);
    await userEvent.click(screen.getByRole("button", { name: /Ajustar à tela/ }));
    expect(plano.style.transform).not.toBe(depoisDeAproximar);
  });

  it("a navegação NUNCA entra na pilha de desfazer: ela não avisa mudança nenhuma", async () => {
    const aoMoverNo = vi.fn();
    montar({ aoMoverNo });
    await userEvent.click(screen.getByRole("button", { name: /Aproximar/ }));
    await userEvent.click(screen.getByRole("button", { name: /Ajustar à tela/ }));
    expect(aoMoverNo).not.toHaveBeenCalled();
  });
});

describe("canvas — estado vazio", () => {
  it("orienta a criação do primeiro nó", () => {
    render(
      <ProvedorDeIdioma>
        <Canvas
          nos={[]}
          arestas={[]}
          selecionado={null}
          aoSelecionar={vi.fn()}
          aoCriarNo={vi.fn()}
          aoMoverNo={vi.fn()}
          aoEditarTitulo={vi.fn()}
          aoExcluirNo={vi.fn()}
          aoLigar={vi.fn()}
          aoAbrirDetalhe={vi.fn()}
        />
      </ProvedorDeIdioma>,
    );
    expect(screen.getByText(/Canvas vazio/)).toBeInTheDocument();
  });
});
