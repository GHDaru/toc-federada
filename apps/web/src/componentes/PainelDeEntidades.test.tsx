// O "Painel de Entidades" — a vista tabular que a linhagem acertou
// (`tocbuilderv3/components/EntitiesPanel.tsx`) e que aqui ganha teste, contagem por aba,
// cabeçalho fixo, criação de aresta sem arrastar e largura que sobrevive à sessão.
//
// Requisitos: RI-04/RI-05 da spec 002 (mesma informação do canvas, sem segunda fonte de
// verdade) e RI-07/RI-08/RI-11 da spec 004.
import { beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { PainelDeEntidades, LARGURA_PADRAO_DO_PAINEL, CHAVE_DA_LARGURA } from "./PainelDeEntidades";
import { ProvedorDeIdioma } from "../i18n";
import type { Aresta, No } from "../dominio/tipos";

const NOS: No[] = [
  { id: "n1", titulo: "Prazos são perdidos", descricao: "em três de cada cinco turmas", tipo: "efeito", posicao: { x: 0, y: 0 }, recolhido: false },
  { id: "n2", titulo: "Retrabalho consome a equipe", descricao: "", tipo: "efeito", posicao: { x: 0, y: 0 }, recolhido: false },
];
const ARESTAS: Aresta[] = [{ id: "a1", origem_id: "n1", destino_id: "n2", rotulo: "" }];

function montar(props: Partial<React.ComponentProps<typeof PainelDeEntidades>> = {}) {
  const cbs = {
    aoFocar: vi.fn(),
    aoSelecionar: vi.fn(),
    aoEditarNo: vi.fn(),
    aoExcluirNo: vi.fn(),
    aoCriarNo: vi.fn(),
    aoLigar: vi.fn(),
    aoEditarAresta: vi.fn(),
    aoExcluirAresta: vi.fn(),
  };
  const util = render(
    <ProvedorDeIdioma>
      <PainelDeEntidades nos={NOS} arestas={ARESTAS} selecionado={null} {...cbs} {...props} />
    </ProvedorDeIdioma>,
  );
  return { ...util, ...cbs };
}

beforeEach(() => sessionStorage.clear());

describe("painel de entidades", () => {
  it("mostra a contagem na aba (RI-08)", () => {
    montar();
    expect(screen.getByRole("tab", { name: /Nós \(2\)/ })).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: /Arestas \(1\)/ })).toBeInTheDocument();
  });

  it("projeta os MESMOS nós do canvas como linhas", () => {
    montar();
    expect(screen.getByRole("cell", { name: "Prazos são perdidos" })).toBeInTheDocument();
    expect(screen.getByRole("cell", { name: "Retrabalho consome a equipe" })).toBeInTheDocument();
  });

  it("mostra a aresta pelos TÍTULOS de causa e efeito, nunca por identificador cru", async () => {
    montar();
    await userEvent.click(screen.getByRole("tab", { name: /Arestas/ }));
    const linha = screen.getAllByRole("row")[1]!;
    expect(within(linha).getByText("Prazos são perdidos")).toBeInTheDocument();
    expect(within(linha).getByText("Retrabalho consome a equipe")).toBeInTheDocument();
    expect(linha.textContent).not.toContain("n1");
  });

  it("edita o título na própria linha — edição rápida é o ponto da vista tabular", async () => {
    const { aoEditarNo } = montar();
    await userEvent.click(screen.getAllByRole("button", { name: /Editar/ })[0]!);
    const campo = screen.getByRole("textbox");
    await userEvent.clear(campo);
    await userEvent.type(campo, "Prazos combinados são perdidos{Enter}");
    expect(aoEditarNo).toHaveBeenCalledWith("n1", "Prazos combinados são perdidos");
  });

  it("cria aresta SEM arrastar: dois seletores e um botão (RI-11)", async () => {
    const { aoLigar } = montar();
    await userEvent.click(screen.getByRole("tab", { name: /Arestas/ }));
    await userEvent.selectOptions(screen.getByLabelText(/Causa/), "n2");
    await userEvent.selectOptions(screen.getByLabelText(/Efeito/), "n1");
    await userEvent.click(screen.getByRole("button", { name: /Adicionar aresta/ }));
    expect(aoLigar).toHaveBeenCalledWith("n2", "n1");
  });

  it("foca o nó no canvas a partir da linha", async () => {
    const { aoFocar } = montar();
    await userEvent.click(screen.getAllByRole("button", { name: /Focar/ })[0]!);
    expect(aoFocar).toHaveBeenCalledWith("n1");
  });

  it("tem estado vazio com ação de criação nas duas abas (RI-08)", async () => {
    montar({ nos: [], arestas: [] });
    expect(screen.getByText(/Nenhum nó ainda/)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Adicionar nó/ })).toBeInTheDocument();
    await userEvent.click(screen.getByRole("tab", { name: /Arestas/ }));
    expect(screen.getByText(/Nenhuma aresta ainda/)).toBeInTheDocument();
  });

  it("mantém a seleção ao alternar de aba (RI-05 da spec 002)", async () => {
    const { aoSelecionar } = montar({ selecionado: "n1" });
    expect(screen.getByRole("row", { selected: true })).toBeInTheDocument();
    await userEvent.click(screen.getByRole("tab", { name: /Arestas/ }));
    await userEvent.click(screen.getByRole("tab", { name: /Nós/ }));
    expect(screen.getByRole("row", { selected: true })).toBeInTheDocument();
    expect(aoSelecionar).not.toHaveBeenCalled();
  });

  it("é redimensionável por arrasto e guarda a largura da sessão (RI-07)", () => {
    const { unmount } = montar();
    const painel = screen.getByRole("complementary");
    expect(painel).toHaveStyle({ width: `${LARGURA_PADRAO_DO_PAINEL}px` });
    const alca = screen.getByRole("separator");
    fireEvent.mouseDown(alca, { clientX: LARGURA_PADRAO_DO_PAINEL });
    fireEvent.mouseMove(document, { clientX: LARGURA_PADRAO_DO_PAINEL + 90 });
    fireEvent.mouseUp(document);
    expect(painel).toHaveStyle({ width: `${LARGURA_PADRAO_DO_PAINEL + 90}px` });
    expect(sessionStorage.getItem(CHAVE_DA_LARGURA)).toBe(String(LARGURA_PADRAO_DO_PAINEL + 90));

    unmount();
    montar();
    expect(screen.getByRole("complementary")).toHaveStyle({
      width: `${LARGURA_PADRAO_DO_PAINEL + 90}px`,
    });
  });

  it("respeita um mínimo: o painel não some por arrasto", () => {
    montar();
    const alca = screen.getByRole("separator");
    fireEvent.mouseDown(alca, { clientX: LARGURA_PADRAO_DO_PAINEL });
    fireEvent.mouseMove(document, { clientX: 10 });
    fireEvent.mouseUp(document);
    const largura = Number(screen.getByRole("complementary").style.width.replace("px", ""));
    expect(largura).toBeGreaterThanOrEqual(220);
  });

  it("sobrevive a um armazenamento de sessão indisponível", () => {
    const original = Object.getOwnPropertyDescriptor(window, "sessionStorage");
    Object.defineProperty(window, "sessionStorage", {
      configurable: true,
      get() {
        throw new Error("bloqueado pelo navegador");
      },
    });
    expect(() => montar()).not.toThrow();
    if (original) Object.defineProperty(window, "sessionStorage", original);
  });
});
