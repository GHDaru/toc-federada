// A superfície de confirmação (`proposta-de-acao`) — RI-01/RI-03/RI-09 da spec 006.
//
// Siglas, uma vez: **NC** — Nuvem de Conflito · **IA** — inteligência artificial ·
// **RI** — requisito de interface · **TTL** — *Time To Live* (tempo de vida).
//
// É a **uma** superfície de confirmação para toda ação `confirm`, venha de pessoa ou de
// assistência: resumo em português, contagem de afetados **antes** da decisão, confirmar e
// recusar com igual proeminência, e o desfecho visível depois — inclusive na recusa
// (RI-04: recusa silenciosa é defeito).
import { describe, expect, it, vi } from "vitest";
import { screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { SuperficieDeConfirmacao } from "./SuperficieDeConfirmacao";
import { renderComIdioma } from "../../testes/apoio";
import type { Proposta } from "../../dominio/tipos";

const PENDENTE: Proposta = {
  proposal_id: "prop-1",
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

describe("superfície de confirmação", () => {
  it("mostra a ação, a origem como DADO e o que a decisão vai afetar", () => {
    renderComIdioma(
      <SuperficieDeConfirmacao
        proposta={{ ...PENDENTE, alvos: ["Prazos são perdidos", "Retrabalho"], quantidade_de_alvos: 2 }}
        aoConfirmar={vi.fn()}
        aoRecusar={vi.fn()}
        aoFechar={vi.fn()}
      />,
    );
    const ficha = screen.getByRole("region", { name: /Confirmar a proposta/ });
    expect(within(ficha).getByText("Preencher a nuvem a partir de uma narrativa")).toBeInTheDocument();
    expect(within(ficha).getByText("toc.generate_conflict_cloud")).toBeInTheDocument();
    // RI-02: a origem é dado exibido, nunca desvio de fluxo.
    expect(within(ficha).getByText("Assistência")).toBeInTheDocument();
    // RI-03: os N alvos contados ANTES da decisão.
    expect(within(ficha).getByText("2")).toBeInTheDocument();
    expect(within(ficha).getByText(/Prazos são perdidos/)).toBeInTheDocument();
  });

  it("ação que não é lote não anuncia \"0 itens afetados\" — 0 alvos é ausência, não zero", () => {
    // A contagem de alvos é do LOTE (APH-5.9(b)). `toc.generate_conflict_cloud` não é
    // lote: ela escreve a nuvem inteira, e dizer "itens afetados: 0" a quem vai reescrever
    // cinco entidades e sete premissas seria a tela informando o contrário do que acontece.
    renderComIdioma(
      <SuperficieDeConfirmacao
        proposta={PENDENTE}
        aoConfirmar={vi.fn()}
        aoRecusar={vi.fn()}
        aoFechar={vi.fn()}
      />,
    );
    expect(screen.queryByText("Itens afetados")).toBeNull();
    expect(screen.getByText("Ação")).toBeInTheDocument();
  });

  it("oferece confirmar e recusar com o mesmo peso — e o foco abre no resumo", async () => {
    const aoConfirmar = vi.fn();
    const aoRecusar = vi.fn();
    renderComIdioma(
      <SuperficieDeConfirmacao
        proposta={PENDENTE}
        aoConfirmar={aoConfirmar}
        aoRecusar={aoRecusar}
        aoFechar={vi.fn()}
      />,
    );
    const confirmar = screen.getByRole("button", { name: /Confirmar/ });
    const recusar = screen.getByRole("button", { name: /Recusar/ });
    // Mesmo peso visual: a mesma classe de botão de decisão nos dois (RI-01, RI-06 da 007).
    expect(confirmar.className).toBe(recusar.className);
    expect(screen.getByRole("heading", { name: /Confirmar a proposta/ })).toHaveFocus();

    await userEvent.click(confirmar);
    expect(aoConfirmar).toHaveBeenCalledTimes(1);
    await userEvent.click(recusar);
    expect(aoRecusar).toHaveBeenCalledTimes(1);
  });

  it("proposta decidida mostra o desfecho e NÃO oferece decidir de novo", () => {
    renderComIdioma(
      <SuperficieDeConfirmacao
        proposta={{
          ...PENDENTE,
          estado: "executed",
          status: "executed",
          mensagem: "5 entidade(s), 7 premissa(s) e 2 injeção(ões) aplicadas",
        }}
        aoConfirmar={vi.fn()}
        aoRecusar={vi.fn()}
        aoFechar={vi.fn()}
      />,
    );
    const desfecho = screen.getByRole("status");
    expect(desfecho).toHaveTextContent("Aplicado à nuvem");
    expect(desfecho).toHaveTextContent("5 entidade(s), 7 premissa(s) e 2 injeção(ões) aplicadas");
    expect(screen.queryByRole("button", { name: /Confirmar/ })).toBeNull();
  });

  it("recusa não é silêncio: o desfecho negado aparece com todas as letras", () => {
    renderComIdioma(
      <SuperficieDeConfirmacao
        proposta={{ ...PENDENTE, estado: "denied", status: "denied", mensagem: "recusada por quem decide" }}
        aoConfirmar={vi.fn()}
        aoRecusar={vi.fn()}
        aoFechar={vi.fn()}
      />,
    );
    expect(screen.getByRole("status")).toHaveTextContent(/Recusado. Nada foi escrito/);
  });

  it("lote: o desfecho por alvo aparece item a item depois da decisão (RI-03)", () => {
    renderComIdioma(
      <SuperficieDeConfirmacao
        proposta={{
          ...PENDENTE,
          estado: "failed",
          status: "failed",
          alvos: ["um", "outro"],
          quantidade_de_alvos: 2,
          outcomes: [
            { target: "um", status: "executed", message: "" },
            { target: "outro", status: "failed", message: "título vazio" },
          ],
        }}
        aoConfirmar={vi.fn()}
        aoRecusar={vi.fn()}
        aoFechar={vi.fn()}
      />,
    );
    const itens = screen.getAllByRole("listitem");
    expect(itens.map((i) => i.textContent)).toEqual([
      expect.stringContaining("um"),
      expect.stringContaining("título vazio"),
    ]);
  });

  it("enquanto a decisão viaja, os botões não aceitam um segundo clique", async () => {
    const aoConfirmar = vi.fn();
    renderComIdioma(
      <SuperficieDeConfirmacao
        proposta={PENDENTE}
        aoConfirmar={aoConfirmar}
        aoRecusar={vi.fn()}
        aoFechar={vi.fn()}
        ocupada
      />,
    );
    await userEvent.click(screen.getByRole("button", { name: /Confirmar/ }));
    expect(aoConfirmar).not.toHaveBeenCalled();
  });
});
