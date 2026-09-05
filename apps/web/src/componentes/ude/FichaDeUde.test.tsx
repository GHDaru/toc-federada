// A ficha de validação do Efeito Indesejável (UDE) — spec 005, RI-01 a RI-04.
//
// Ela substitui o modal monolítico da 4ª geração, onde os onze critérios chegavam num
// bloco só, vindos de um modelo de linguagem chamado do navegador
// (`tocbuilderv3/services/geminiService.ts:16`). Aqui os oito decidíveis vêm de regra pura
// do servidor, com trecho apontado; os quatro de julgamento vêm com parecer e autor.
import { describe, expect, it, vi } from "vitest";
import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { FichaDeUde } from "./FichaDeUde";
import { ProvedorDeIdioma } from "../../i18n";
import type { Ude, ValidacaoFormal } from "../../dominio/tipos";

const VALIDACAO: ValidacaoFormal = {
  texto: "Os prazos das turmas são perdidos porque a coordenação demora a aprovar.",
  idioma: "pt",
  versao_do_lexico: "pt-1",
  aprovado_nos_decidiveis: false,
  vereditos: [
    { codigo: "CD-1", caracteristica: "2", nome: "criterio.frase_completa", classe: "decidivel", regra: "RN-01", enunciado: "É uma frase completa.", veredito: "atende", motivo: "", trecho: "" },
    { codigo: "CD-7", caracteristica: "10", nome: "criterio.sem_causa_embutida", classe: "decidivel", regra: "RN-03", enunciado: "Não inclui a própria causa na verbalização.", veredito: "nao_atende", motivo: "conector causal encontrado", trecho: "porque a coordenação demora a aprovar" },
    { codigo: "J-1", caracteristica: "1", nome: "criterio.queixa_continua", classe: "julgamento", regra: "RN-09", enunciado: "É queixa sobre um problema contínuo que limita o desempenho.", veredito: "indeterminado", motivo: "critério de julgamento", trecho: "" },
  ],
  reprovacoes: ["CD-7"],
  pendencias_de_julgamento: ["J-1"],
};

const UDE: Ude = {
  no_id: "n1",
  titulo: VALIDACAO.texto,
  status: "requer_refinamento",
  ficha: { area_impactada: "Coordenação de turmas" },
  validacao: VALIDACAO,
  pareceres: [
    {
      autor: "Facilitadora TOC",
      origem: "humano",
      favoravel: true,
      justificativa: "A queixa aparece em todas as turmas desde o semestre passado.",
      instante: "2026-09-01T10:00:00Z",
      criterios: ["J-1"],
    },
  ],
};

const APROVADA: ValidacaoFormal = {
  ...VALIDACAO,
  texto: "Os prazos das turmas são perdidos.",
  aprovado_nos_decidiveis: true,
  vereditos: VALIDACAO.vereditos.map((v) =>
    v.classe === "decidivel" ? { ...v, veredito: "atende" as const, motivo: "", trecho: "" } : v,
  ),
  reprovacoes: [],
};

function montar(props: Partial<React.ComponentProps<typeof FichaDeUde>> = {}) {
  const cbs = {
    aoReformular: vi.fn(async () => {}),
    aoValidarTexto: vi.fn(async () => APROVADA),
    aoRegistrarParecer: vi.fn(async () => {}),
    aoMudarStatus: vi.fn(async () => {}),
    aoFechar: vi.fn(),
  };
  const util = render(
    <ProvedorDeIdioma>
      <FichaDeUde ude={UDE} {...cbs} {...props} />
    </ProvedorDeIdioma>,
  );
  return { ...util, ...cbs };
}

describe("ficha de UDE — duas seções nomeadas (RI-02)", () => {
  it("separa decidíveis de julgamento, cada um com o seu nome", () => {
    montar();
    expect(screen.getByRole("region", { name: /Critérios decidíveis/ })).toBeInTheDocument();
    expect(screen.getByRole("region", { name: /Critérios de julgamento/ })).toBeInTheDocument();
  });

  it("traduz o critério pela chave estável do domínio, não pelo texto do servidor", () => {
    montar();
    const decidiveis = screen.getByRole("region", { name: /Critérios decidíveis/ });
    expect(within(decidiveis).getByText("Não inclui a própria causa na verbalização.")).toBeInTheDocument();
  });

  it("mostra o status por texto, nunca só por cor (RI-01)", () => {
    const { container } = montar();
    // O selo do cabeçalho: cor é classe, texto é conteúdo. (O mesmo rótulo reaparece no
    // botão de mudar status, e é por isso que a asserção olha o selo, não a página.)
    const selo = container.querySelector(".ficha-cabecalho .selo");
    expect(selo).toHaveTextContent("Requer refinamento");
  });

  it("mostra os pareceres com autor na seção de julgamento", () => {
    montar();
    const julgamento = screen.getByRole("region", { name: /Critérios de julgamento/ });
    expect(within(julgamento).getByText(/Facilitadora TOC/)).toBeInTheDocument();
  });
});

describe("ficha de UDE — o trecho apontado no próprio texto (RI-03)", () => {
  it("marca inline o trecho que reprovou, com a explicação ao lado", () => {
    montar();
    const marcado = screen.getByText("porque a coordenação demora a aprovar", { selector: "mark" });
    expect(marcado).toBeInTheDocument();
    expect(screen.getByText(/conector causal encontrado/)).toBeInTheDocument();
  });

  it("não marca nada quando nenhum critério reprova", () => {
    montar({ ude: { ...UDE, status: "validado", validacao: APROVADA } });
    expect(document.querySelector("mark")).toBeNull();
  });
});

describe("ficha de UDE — reprovar → editar → reavaliar na mesma superfície (RI-04)", () => {
  it("reavalia sem fechar a ficha e mostra o resultado novo", async () => {
    const { aoValidarTexto, aoFechar } = montar();
    const campo = screen.getByLabelText(/Texto do efeito/);
    await userEvent.clear(campo);
    await userEvent.type(campo, "Os prazos das turmas são perdidos.");
    await userEvent.click(screen.getByRole("button", { name: /Reavaliar/ }));
    await waitFor(() => expect(aoValidarTexto).toHaveBeenCalledWith("Os prazos das turmas são perdidos."));
    expect(await screen.findByText(/Aprovado nos decidíveis/)).toBeInTheDocument();
    expect(screen.getByRole("region", { name: /Critérios decidíveis/ })).toBeInTheDocument();
    expect(aoFechar).not.toHaveBeenCalled();
  });

  it("reformular grava o texto novo pelo comando do agregado", async () => {
    const { aoReformular } = montar();
    const campo = screen.getByLabelText(/Texto do efeito/);
    await userEvent.clear(campo);
    await userEvent.type(campo, "Os prazos das turmas são perdidos.");
    await userEvent.click(screen.getByRole("button", { name: /^Reformular$/ }));
    await waitFor(() => expect(aoReformular).toHaveBeenCalledWith("Os prazos das turmas são perdidos."));
  });

  it("fluxo de erro: a recusa do serviço aparece na ficha, que continua aberta", async () => {
    const { aoFechar } = montar({
      aoReformular: vi.fn(async () => {
        throw Object.assign(new Error("recusado"), { codigo: "MUTATION_REFUSED", status: 409 });
      }),
    });
    const campo = screen.getByLabelText(/Texto do efeito/);
    await userEvent.clear(campo);
    await userEvent.type(campo, "Outro texto qualquer.");
    await userEvent.click(screen.getByRole("button", { name: /^Reformular$/ }));
    expect(await screen.findByRole("alert")).toHaveTextContent(/não neste estado do projeto/i);
    expect(aoFechar).not.toHaveBeenCalled();
  });
});

describe("ficha de UDE — parecer humano (RF-16)", () => {
  it("exige justificativa antes de registrar", async () => {
    const { aoRegistrarParecer } = montar();
    await userEvent.click(screen.getByRole("button", { name: /Registrar parecer/ }));
    expect(aoRegistrarParecer).not.toHaveBeenCalled();
    expect(screen.getByRole("alert")).toHaveTextContent(/obrigatório/i);
  });

  it("registra o parecer favorável com a justificativa escrita", async () => {
    const { aoRegistrarParecer } = montar();
    await userEvent.type(
      screen.getByLabelText(/Justificativa/),
      "A queixa é contínua e limita o desempenho do curso.",
    );
    await userEvent.click(screen.getByRole("button", { name: /Registrar parecer/ }));
    await waitFor(() =>
      expect(aoRegistrarParecer).toHaveBeenCalledWith({
        favoravel: true,
        justificativa: "A queixa é contínua e limita o desempenho do curso.",
        criterios: [],
      }),
    );
  });
});
