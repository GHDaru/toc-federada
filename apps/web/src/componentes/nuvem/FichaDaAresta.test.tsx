// A ficha da aresta — "uma superfície, três camadas" (RI-04 da spec 007): a leitura por
// extenso no topo, as premissas ordenadas com estado, e as injeções agrupadas por
// premissa. A 4ª geração mostrava premissa e solução num modal de duas linhas
// (`tocbuilderv3/components/AssumptionSolutionModal.tsx`, 48 linhas) e não tinha estado,
// ordem, classificação TRIZ nem arquivamento.
import { describe, expect, it, vi } from "vitest";
import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { FichaDaAresta } from "./FichaDaAresta";
import { ProvedorDeIdioma } from "../../i18n";
import type { ArestaDaNuvem } from "../../dominio/tipos";

const ARESTA: ArestaDaNuvem = {
  chave: "B_D",
  classe: "pre_requisito",
  aresta_id: "a-B_D",
  leitura: "Para ter Turmas com professor titular, devemos Abrir turmas em três cidades novas",
  premissas: [
    {
      id: "pr1",
      aresta: "B_D",
      texto: "Só há professor titular disponível em cidade nova.",
      ordem: 0,
      estado: "vigente",
      justificativa: "",
      injecoes: [
        {
          id: "in1",
          premissa_id: "pr1",
          texto: "Contratar titular remoto com carga presencial mensal.",
          status: "candidata",
          separacao: "espaco",
          semeadura: null,
        },
      ],
    },
    {
      id: "pr2",
      aresta: "B_D",
      texto: "A avaliação externa exige titular em toda turma.",
      ordem: 1,
      estado: "desafiada",
      justificativa: "A norma mudou em 2026.",
      injecoes: [],
    },
  ],
};

function montar(props: Partial<React.ComponentProps<typeof FichaDaAresta>> = {}) {
  const cbs = {
    aoRegistrarPremissa: vi.fn(async () => {}),
    aoEditarPremissa: vi.fn(async () => {}),
    aoDesafiarPremissa: vi.fn(async () => {}),
    aoRevigorarPremissa: vi.fn(async () => {}),
    aoArquivarPremissa: vi.fn(async () => {}),
    aoRegistrarInjecao: vi.fn(async () => {}),
    aoClassificarInjecao: vi.fn(async () => {}),
    aoMudarStatusDaInjecao: vi.fn(async () => {}),
    aoFechar: vi.fn(),
  };
  const util = render(
    <ProvedorDeIdioma>
      <FichaDaAresta aresta={ARESTA} {...cbs} {...props} />
    </ProvedorDeIdioma>,
  );
  return { ...util, ...cbs };
}

describe("ficha da aresta — as três camadas (RI-04)", () => {
  it("abre pela leitura por extenso", () => {
    montar();
    expect(screen.getByRole("heading", { level: 2 })).toHaveTextContent(ARESTA.leitura);
  });

  it("lista as premissas na ordem, com o estado por texto", () => {
    montar();
    const premissas = screen.getAllByRole("listitem", { name: /premissa/i });
    expect(premissas).toHaveLength(2);
    expect(premissas[0]).toHaveTextContent("Só há professor titular disponível em cidade nova.");
    expect(premissas[0]).toHaveTextContent("Vigente");
    expect(premissas[1]).toHaveTextContent("Desafiada");
    expect(premissas[1]).toHaveTextContent("A norma mudou em 2026.");
  });

  it("agrupa a injeção DENTRO da premissa que ela invalida (RN-04)", () => {
    montar();
    const primeira = screen.getAllByRole("listitem", { name: /premissa/i })[0]!;
    expect(within(primeira).getByText(/Contratar titular remoto/)).toBeInTheDocument();
    // A classificação TRIZ aparece na linha da injeção. (O mesmo rótulo existe como
    // opção do seletor de separação, e é por isso que a asserção olha a linha.)
    expect(primeira.querySelector(".injecao-meta")).toHaveTextContent("Separação no espaço");
    const segunda = screen.getAllByRole("listitem", { name: /premissa/i })[1]!;
    expect(within(segunda).getByText(/Nenhuma injeção/)).toBeInTheDocument();
  });
});

describe("ficha da aresta — escrita", () => {
  it("registra premissa nova (fluxo feliz)", async () => {
    const { aoRegistrarPremissa } = montar();
    await userEvent.type(screen.getByLabelText(/Nova premissa/), "Titular exige dedicação exclusiva.");
    await userEvent.click(screen.getByRole("button", { name: /^Nova premissa$/ }));
    await waitFor(() =>
      expect(aoRegistrarPremissa).toHaveBeenCalledWith("Titular exige dedicação exclusiva."),
    );
  });

  it("fluxo de erro: a recusa do domínio vira frase com próxima ação", async () => {
    montar({
      aoRegistrarPremissa: vi.fn(async () => {
        throw Object.assign(new Error("x"), { codigo: "INVALID_ASSUMPTION", status: 409 });
      }),
    });
    await userEvent.type(screen.getByLabelText(/Nova premissa/), "   texto   ");
    await userEvent.click(screen.getByRole("button", { name: /^Nova premissa$/ }));
    expect(await screen.findByRole("alert")).toHaveTextContent(/premissa foi recusada/i);
  });

  it("desafiar exige justificativa escrita (RF-13)", async () => {
    const { aoDesafiarPremissa } = montar();
    const primeira = screen.getAllByRole("listitem", { name: /premissa/i })[0]!;
    await userEvent.click(within(primeira).getByRole("button", { name: /Desafiar/ }));
    await userEvent.click(screen.getByRole("button", { name: /Confirmar/ }));
    expect(aoDesafiarPremissa).not.toHaveBeenCalled();
    expect(screen.getByRole("alert")).toHaveTextContent(/obrigatório/i);
    await userEvent.type(screen.getByLabelText(/Justificativa/), "A norma mudou.");
    await userEvent.click(screen.getByRole("button", { name: /Confirmar/ }));
    await waitFor(() => expect(aoDesafiarPremissa).toHaveBeenCalledWith("pr1", "A norma mudou."));
  });

  it("revigorar é o caminho de volta da premissa desafiada", async () => {
    const { aoRevigorarPremissa } = montar();
    const segunda = screen.getAllByRole("listitem", { name: /premissa/i })[1]!;
    await userEvent.click(within(segunda).getByRole("button", { name: /Revigorar/ }));
    await waitFor(() => expect(aoRevigorarPremissa).toHaveBeenCalledWith("pr2"));
  });

  it("registra injeção sob a premissa, com a separação TRIZ escolhida", async () => {
    const { aoRegistrarInjecao } = montar();
    const primeira = screen.getAllByRole("listitem", { name: /premissa/i })[0]!;
    await userEvent.type(within(primeira).getByLabelText(/Nova injeção/), "Convênio com universidade local.");
    await userEvent.selectOptions(within(primeira).getByLabelText(/Separação TRIZ/), "tempo");
    await userEvent.click(within(primeira).getByRole("button", { name: /^Nova injeção$/ }));
    await waitFor(() =>
      expect(aoRegistrarInjecao).toHaveBeenCalledWith("pr1", "Convênio com universidade local.", "tempo"),
    );
  });

  it("muda o status da injeção pela máquina de estados do servidor", async () => {
    const { aoMudarStatusDaInjecao } = montar();
    await userEvent.click(screen.getByRole("button", { name: /Escolhida/ }));
    await waitFor(() => expect(aoMudarStatusDaInjecao).toHaveBeenCalledWith("in1", "escolhida", ""));
  });
});

describe("ficha da aresta — sugestões nascem propostas", () => {
  it("mostra o aviso de que NADA foi aplicado, e aceitar/recusar têm o mesmo peso", async () => {
    const aoSugerirPremissas = vi.fn(async () => [
      { texto: "O titular precisa morar na cidade.", injecoes: [] },
    ]);
    const { aoRegistrarPremissa } = montar({ aoSugerirPremissas });
    await userEvent.click(screen.getByRole("button", { name: /Sugerir premissas/ }));
    expect(await screen.findByText(/Nada foi aplicado/)).toBeInTheDocument();
    const proposta = screen.getByRole("listitem", { name: /proposta/i });
    expect(within(proposta).getByRole("button", { name: /Aceitar/ })).toBeInTheDocument();
    expect(within(proposta).getByRole("button", { name: /Recusar/ })).toBeInTheDocument();
    await userEvent.click(within(proposta).getByRole("button", { name: /Aceitar/ }));
    await waitFor(() =>
      expect(aoRegistrarPremissa).toHaveBeenCalledWith("O titular precisa morar na cidade."),
    );
  });

  it("recusar não custa nada: some da bandeja sem chamar escrita nenhuma", async () => {
    const aoSugerirPremissas = vi.fn(async () => [
      { texto: "O titular precisa morar na cidade.", injecoes: [] },
    ]);
    const { aoRegistrarPremissa } = montar({ aoSugerirPremissas });
    await userEvent.click(screen.getByRole("button", { name: /Sugerir premissas/ }));
    await userEvent.click(
      within(await screen.findByRole("listitem", { name: /proposta/i })).getByRole("button", { name: /Recusar/ }),
    );
    expect(screen.queryByRole("listitem", { name: /proposta/i })).toBeNull();
    expect(aoRegistrarPremissa).not.toHaveBeenCalled();
  });
});
