// O painel lateral do nó (RI-04 da spec 004): "descrição e campos longos abrem em painel
// lateral, **não em modal bloqueante**". Modal bloqueante tira o diagrama da vista bem na
// hora em que a pessoa está escrevendo sobre ele — foi o que a 4ª geração fez, com
// `NodeDetailModal` e `NodeEditorModal` cobrindo o canvas.
import { describe, expect, it, vi } from "vitest";
import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { PainelDoNo } from "./PainelDoNo";
import { renderComIdioma, no } from "../../testes/apoio";

const NO = { ...no("n1", "Prazos são perdidos", 40, 80), descricao: "em três de cada cinco turmas" };

describe("painel do nó", () => {
  it("não é modal: não prende o foco nem esconde o diagrama", () => {
    renderComIdioma(<PainelDoNo no={NO} aoSalvar={vi.fn()} aoFechar={vi.fn()} />);
    const painel = screen.getByRole("complementary", { name: /Detalhe do nó/ });
    expect(painel.getAttribute("aria-modal")).toBeNull();
    expect(screen.queryByRole("dialog")).toBeNull();
  });

  it("mostra título, descrição e posição do nó", () => {
    renderComIdioma(<PainelDoNo no={NO} aoSalvar={vi.fn()} aoFechar={vi.fn()} />);
    expect(screen.getByLabelText(/Título/)).toHaveValue("Prazos são perdidos");
    expect(screen.getByLabelText(/Descrição/)).toHaveValue("em três de cada cinco turmas");
    expect(screen.getByText(/40/)).toBeInTheDocument();
  });

  it("salva título e descrição juntos", async () => {
    const aoSalvar = vi.fn(async () => {});
    renderComIdioma(<PainelDoNo no={NO} aoSalvar={aoSalvar} aoFechar={vi.fn()} />);
    await userEvent.clear(screen.getByLabelText(/Descrição/));
    await userEvent.type(screen.getByLabelText(/Descrição/), "em três de cada cinco turmas do noturno");
    await userEvent.click(screen.getByRole("button", { name: /Salvar/ }));
    await waitFor(() =>
      expect(aoSalvar).toHaveBeenCalledWith({
        titulo: "Prazos são perdidos",
        descricao: "em três de cada cinco turmas do noturno",
      }),
    );
  });

  it("fluxo de erro: a recusa aparece no painel, que continua aberto", async () => {
    const aoFechar = vi.fn();
    renderComIdioma(
      <PainelDoNo
        no={NO}
        aoFechar={aoFechar}
        aoSalvar={vi.fn(async () => {
          throw Object.assign(new Error("x"), { codigo: "MUTATION_REFUSED" });
        })}
      />,
    );
    await userEvent.click(screen.getByRole("button", { name: /Salvar/ }));
    expect(await screen.findByRole("alert")).toHaveTextContent(/não neste estado/i);
    expect(aoFechar).not.toHaveBeenCalled();
  });
});
