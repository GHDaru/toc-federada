// A pré-visualização da geração assistida (RI-06 da spec 007).
//
// A regra que esta tela existe para tornar visível: **gerar não aplica**. A rota devolve a
// nuvem proposta validada por esquema e o identificador da ação governada; quem escreve é
// a proposta que atravessa a máquina de estados no servidor, com gate humano. Por isso
// recusar não custa nada — não houve escrita para desfazer (RF-24).
//
// A 4ª geração fazia o oposto: a resposta do modelo, pedida do navegador, era aplicada
// direto no estado da tela (`tocbuilderv3/components/ConflictCloudView.tsx`).
import { describe, expect, it, vi } from "vitest";
import { screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { PreviaDaGeracao } from "./PreviaDaGeracao";
import { renderComIdioma } from "../../testes/apoio";
import type { Geracao } from "../../dominio/tipos";

const GERACAO: Geracao = {
  action_id: "toc.generate_conflict_cloud",
  aviso: "nada foi aplicado: leve este resultado à ação governada do catálogo",
  resultado: {
    versao: "1.0.0",
    racional: "O dilema entre reputação e expansão.",
    entidades: {
      A: "Reputação acadêmica preservada",
      B: "Turmas com professor titular",
      C: "Custo por turma sob controle",
      D: "Abrir turmas em três cidades novas",
      D_PRIME: "Não abrir turmas em três cidades novas",
    },
    arestas: {
      A_B: [{ texto: "Só titular sustenta a avaliação externa.", injecoes: [{ texto: "Titular remoto." }] }],
      A_C: [],
      B_D: [],
      C_D_PRIME: [],
      D_C: [],
      D_PRIME_B: [],
      D_D_PRIME: [],
    },
  },
};

describe("prévia da geração", () => {
  it("mostra as cinco entidades propostas com o texto ATUAL ao lado (diff)", () => {
    renderComIdioma(
      <PreviaDaGeracao
        geracao={GERACAO}
        textosAtuais={{ A: "[A] Objetivo comum", B: "", C: "", D: "", D_PRIME: "" }}
        aoFechar={vi.fn()}
      />,
    );
    const linhaA = screen.getByRole("row", { name: /Objetivo comum \(A\)/ });
    expect(within(linhaA).getByText("[A] Objetivo comum")).toBeInTheDocument();
    expect(within(linhaA).getByText("Reputação acadêmica preservada")).toBeInTheDocument();
    expect(screen.getAllByRole("row")).toHaveLength(6); // cabeçalho + cinco entidades
  });

  it("diz, com todas as letras, que NADA foi aplicado, e nomeia a ação governada", () => {
    renderComIdioma(<PreviaDaGeracao geracao={GERACAO} textosAtuais={{}} aoFechar={vi.fn()} />);
    expect(screen.getByText(/Nada foi aplicado/)).toBeInTheDocument();
    expect(screen.getByText("toc.generate_conflict_cloud")).toBeInTheDocument();
  });

  it("lista as premissas propostas por aresta, com as injeções embaixo", () => {
    renderComIdioma(<PreviaDaGeracao geracao={GERACAO} textosAtuais={{}} aoFechar={vi.fn()} />);
    expect(screen.getByText(/Só titular sustenta a avaliação externa/)).toBeInTheDocument();
    expect(screen.getByText(/Titular remoto/)).toBeInTheDocument();
  });

  it("recusar fecha a prévia sem custo nenhum — não houve escrita para desfazer", async () => {
    const aoFechar = vi.fn();
    const aoAceitar = vi.fn();
    renderComIdioma(
      <PreviaDaGeracao
        geracao={GERACAO}
        textosAtuais={{}}
        aoFechar={aoFechar}
        aoAceitar={aoAceitar}
      />,
    );
    await userEvent.click(screen.getByRole("button", { name: /Recusar/ }));
    expect(aoFechar).toHaveBeenCalled();
    expect(aoAceitar).not.toHaveBeenCalled();
  });

  // O defeito que este teste fecha: a prévia mostrava o diff e só oferecia "Recusar". Não
  // havia, na interface, caminho para ACEITAR — a funcionalidade mais vistosa do produto
  // não concluía. Aceitar **não** escreve daqui: leva a proposta ao gate governado, que é
  // quem atravessa a máquina de estados no servidor (RF-23/RF-24 da spec 007).
  it("aceitar existe, e leva a proposta ao gate — as duas ações com o mesmo peso", async () => {
    const aoAceitar = vi.fn();
    renderComIdioma(
      <PreviaDaGeracao
        geracao={GERACAO}
        textosAtuais={{}}
        aoFechar={vi.fn()}
        aoAceitar={aoAceitar}
      />,
    );
    const aceitar = screen.getByRole("button", { name: /Aceitar/ });
    const recusar = screen.getByRole("button", { name: /Recusar/ });
    expect(aceitar.className).toBe(recusar.className); // RI-06: mesmo peso visual

    await userEvent.click(aceitar);
    expect(aoAceitar).toHaveBeenCalledTimes(1);
  });

  it("sem o caminho de aceitar (só leitura), a prévia continua honesta e só recusa", () => {
    renderComIdioma(<PreviaDaGeracao geracao={GERACAO} textosAtuais={{}} aoFechar={vi.fn()} />);
    expect(screen.queryByRole("button", { name: /Aceitar/ })).toBeNull();
    expect(screen.getByRole("button", { name: /Recusar/ })).toBeInTheDocument();
  });

  it("sobrevive a um resultado sem as chaves esperadas, sem quebrar a tela", () => {
    renderComIdioma(
      <PreviaDaGeracao
        geracao={{ ...GERACAO, resultado: {} }}
        textosAtuais={{}}
        aoFechar={vi.fn()}
      />,
    );
    expect(screen.getByText(/Nada foi aplicado/)).toBeInTheDocument();
  });
});
