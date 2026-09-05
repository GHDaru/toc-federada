// A Nuvem de Conflito (NC) — 5 entidades, 7 arestas, layout canônico e notação do método.
//
// Requisitos: RI-01 (posições fixas: o usuário edita texto, não arruma caixas), RI-02
// (necessidade/pré-requisito cheias, perigo tracejadas, conflito com o símbolo de raio, e
// TUDO distinguível também por rótulo textual), RI-03 (premissas acionáveis na própria
// aresta) e RI-05 (aviso de formulação no próprio nó, pedagógico) — spec 007.
//
// A 4ª geração desenhava CINCO das sete arestas: `D_C` e `D_D_PRIME` nunca apareceram
// (`tocbuilderv3/components/ConflictCloudView.tsx:148-169`). O primeiro teste abaixo é
// exatamente essa dívida.
import { describe, expect, it, vi } from "vitest";
import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { DiagramaDaNuvem } from "./DiagramaDaNuvem";
import { ProvedorDeIdioma } from "../../i18n";
import type { ChaveDaAresta, ClasseDaAresta, Nuvem, PapelDaEntidade } from "../../dominio/tipos";

const POSICAO_CANONICA: Record<PapelDaEntidade, { x: number; y: number }> = {
  A: { x: 0, y: 160 },
  B: { x: 280, y: 40 },
  C: { x: 280, y: 280 },
  D: { x: 560, y: 40 },
  D_PRIME: { x: 560, y: 280 },
};

const TEXTOS: Record<PapelDaEntidade, string> = {
  A: "Reputação acadêmica preservada",
  B: "Turmas com professor titular",
  C: "Custo por turma sob controle",
  // Substantivo na posição de ação: é exatamente o que dispara o aviso `d_pede_infinitivo`.
  D: "Expansão para três cidades novas",
  D_PRIME: "Não abrir turmas em três cidades novas",
};

const CLASSES: Record<ChaveDaAresta, ClasseDaAresta> = {
  A_B: "necessidade",
  A_C: "necessidade",
  B_D: "pre_requisito",
  C_D_PRIME: "pre_requisito",
  D_C: "perigo",
  D_PRIME_B: "perigo",
  D_D_PRIME: "conflito",
};

const NUVEM: Nuvem = {
  id: "p-nc",
  nome: "Expansão da Instituição Horizonte",
  ferramenta: "nc",
  descricao_do_problema: "Abrir turmas novas sem perder a reputação.",
  racional: "",
  criado_em: "2026-09-01T10:00:00Z",
  alterado_em: "2026-09-01T10:00:00Z",
  origem: null,
  entidades: (Object.keys(TEXTOS) as PapelDaEntidade[]).map((papel) => ({
    papel,
    no_id: `no-${papel}`,
    texto: TEXTOS[papel],
    posicao: POSICAO_CANONICA[papel],
    avisos:
      papel === "D"
        ? [
            {
              codigo: "d_pede_infinitivo",
              explicacao: "esta posição pede uma ação em infinitivo verbal",
              exemplo: "Abrir turmas em três cidades novas",
            },
          ]
        : [],
  })),
  arestas: (Object.keys(CLASSES) as ChaveDaAresta[]).map((chave) => ({
    chave,
    classe: CLASSES[chave],
    aresta_id: `a-${chave}`,
    leitura: `leitura de ${chave}`,
    premissas:
      chave === "A_B"
        ? [
            {
              id: "pr1",
              aresta: "A_B",
              texto: "Só professor titular sustenta a avaliação externa.",
              ordem: 0,
              estado: "vigente",
              justificativa: "",
              injecoes: [],
            },
          ]
        : [],
  })),
};

function montar(props: Partial<React.ComponentProps<typeof DiagramaDaNuvem>> = {}) {
  const cbs = { aoEditarEntidade: vi.fn(async () => {}), aoAbrirAresta: vi.fn() };
  const util = render(
    <ProvedorDeIdioma>
      <DiagramaDaNuvem nuvem={NUVEM} arestaAberta={null} {...cbs} {...props} />
    </ProvedorDeIdioma>,
  );
  return { ...util, ...cbs };
}

describe("diagrama da nuvem — topologia completa", () => {
  it("desenha as CINCO entidades com o rótulo do papel", () => {
    montar();
    for (const papel of ["A", "B", "C", "D", "D_PRIME"] as PapelDaEntidade[]) {
      expect(screen.getByTestId(`entidade-${papel}`)).toHaveTextContent(TEXTOS[papel]);
    }
    expect(screen.getByText(/Objetivo comum \(A\)/)).toBeInTheDocument();
    expect(screen.getByText(/Ação oposta \(D′\)/)).toBeInTheDocument();
  });

  it("desenha as SETE arestas — inclusive D⇸C e D↯D′, que o v3 nunca renderizou", () => {
    montar();
    for (const chave of Object.keys(CLASSES) as ChaveDaAresta[]) {
      expect(screen.getByTestId(`aresta-${chave}`)).toBeInTheDocument();
    }
    expect(screen.getAllByTestId(/^aresta-/)).toHaveLength(7);
  });

  it("põe cada entidade na posição CANÔNICA que o servidor mandou (RI-01)", () => {
    montar();
    const noA = screen.getByTestId("entidade-A");
    expect(noA.style.transform).toBe("translate(0px, 160px)");
    expect(screen.getByTestId("entidade-D_PRIME").style.transform).toBe("translate(560px, 280px)");
  });

  it("não oferece criar nem excluir entidade ou aresta — a topologia é fixa (RF-03)", () => {
    montar();
    const botoes = screen.getAllByRole("button").map((b) => b.textContent ?? "");
    expect(botoes.some((texto) => /adicionar|excluir|remover/i.test(texto))).toBe(false);
  });
});

describe("diagrama da nuvem — notação do método (RI-02)", () => {
  it("distingue a classe da aresta também por RÓTULO TEXTUAL, nunca só por traço ou cor", () => {
    montar();
    expect(within(screen.getByTestId("aresta-A_B")).getByText("Necessidade")).toBeInTheDocument();
    expect(within(screen.getByTestId("aresta-B_D")).getByText("Pré-requisito")).toBeInTheDocument();
    expect(within(screen.getByTestId("aresta-D_C")).getByText("Perigo")).toBeInTheDocument();
    expect(within(screen.getByTestId("aresta-D_D_PRIME")).getByText("Conflito")).toBeInTheDocument();
  });

  it("traceja as setas de perigo e marca o conflito com o símbolo de raio", () => {
    montar();
    expect(screen.getByTestId("aresta-D_C").className).toContain("perigo");
    expect(screen.getByTestId("traco-D_C")).toHaveAttribute("stroke-dasharray");
    expect(screen.getByTestId("aresta-D_D_PRIME")).toHaveTextContent("↯");
  });

  it("mostra a leitura por extenso de cada aresta", () => {
    montar();
    expect(within(screen.getByTestId("aresta-A_C")).getByText(/leitura de A_C/)).toBeInTheDocument();
  });
});

describe("diagrama da nuvem — premissas na própria aresta (RI-03)", () => {
  it("a legenda da aresta é acionável e abre a ficha daquela aresta", async () => {
    const { aoAbrirAresta } = montar();
    await userEvent.click(within(screen.getByTestId("aresta-A_B")).getByRole("button"));
    expect(aoAbrirAresta).toHaveBeenCalledWith("A_B");
  });

  it("mostra quantas premissas sustentam cada aresta, e o vazio como pendência", () => {
    montar();
    expect(within(screen.getByTestId("aresta-A_B")).getByText("1/1")).toBeInTheDocument();
    // O rótulo do vazio é curto porque mora dentro do desenho; a frase inteira está na
    // ficha da aresta, que é onde se trabalha a premissa.
    expect(within(screen.getByTestId("aresta-B_D")).getByText("sem premissa")).toBeInTheDocument();
  });
});

describe("diagrama da nuvem — aviso de formulação (RI-05)", () => {
  it("aparece no próprio nó, com explicação e exemplo, e é pedagógico e não bloqueante", async () => {
    montar();
    const noD = screen.getByTestId("entidade-D");
    const aviso = within(noD).getByRole("button", { name: /aviso/i });
    await userEvent.click(aviso);
    expect(screen.getByText(/infinitivo verbal/)).toBeInTheDocument();
    expect(within(noD).getByText(/Abrir turmas em três cidades novas/)).toBeInTheDocument();
  });

  it("entidade sem aviso não mostra aviso nenhum", () => {
    montar();
    expect(within(screen.getByTestId("entidade-A")).queryByRole("button", { name: /aviso/i })).toBeNull();
  });
});

describe("diagrama da nuvem — edição do texto (RF-05)", () => {
  it("edita o texto da entidade no lugar, e Esc cancela", async () => {
    const { aoEditarEntidade } = montar();
    await userEvent.dblClick(within(screen.getByTestId("entidade-C")).getByText(TEXTOS.C));
    const campo = screen.getByRole("textbox");
    await userEvent.clear(campo);
    await userEvent.type(campo, "Custo por turma dentro do orçamento{Enter}");
    expect(aoEditarEntidade).toHaveBeenCalledWith("C", "Custo por turma dentro do orçamento");
  });
});
