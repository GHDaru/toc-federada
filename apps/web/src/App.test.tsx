// A casca da aplicação: modo autônomo × modo embarcado, tema, idioma e navegação.
//
// Requisitos: RI-09 e RI-10 da spec 002 (embarcada renderiza APENAS o conteúdo, dentro de
// iframe real), RI-06/RI-07/RI-08 (tema próprio com os tokens do inquilino por cima) e o
// §B.4.1 do Anexo B (recusa de subir nomeando o parâmetro de admissão que faltou).
import { describe, expect, it, vi } from "vitest";
import { screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { act, render } from "@testing-library/react";
import { App } from "./App";
import { clienteFalso } from "./testes/apoio";

const ADMISSAO = {
  VITE_GHD_HOST_ORIGIN: "https://fundacao.exemplo",
  VITE_GHD_HOST_BASE_URL: "https://fundacao.exemplo/api",
  VITE_GHD_APP_ID: "toc",
  VITE_GHD_EMBED_URL: "https://toc.exemplo/toc/embarcado",
};

function montar(props: Partial<React.ComponentProps<typeof App>> = {}) {
  return render(
    <App
      cliente={clienteFalso()}
      ambiente={ADMISSAO}
      url="https://toc.exemplo/toc/projetos"
      pai={{}}
      enviar={vi.fn()}
      {...props}
    />,
  );
}

describe("modo autônomo", () => {
  it("mostra a casca própria: navegação, idioma e tema", async () => {
    montar();
    expect(screen.getByRole("banner")).toBeInTheDocument();
    expect(within(screen.getByRole("navigation")).getByRole("button", { name: /Projetos/ })).toBeInTheDocument();
    expect(await screen.findByText("Evasão no primeiro semestre")).toBeInTheDocument();
  });

  it("troca de idioma sem recarregar", async () => {
    montar();
    await screen.findByText("Evasão no primeiro semestre");
    await userEvent.click(screen.getByRole("button", { name: "English" }));
    expect(screen.getByRole("heading", { name: "Projects", level: 1 })).toBeInTheDocument();
  });

  it("navega para a lixeira e volta", async () => {
    montar();
    await userEvent.click(within(screen.getByRole("navigation")).getByRole("button", { name: /Lixeira/ }));
    expect(await screen.findByText(/Lixeira vazia/)).toBeInTheDocument();
    await userEvent.click(within(screen.getByRole("navigation")).getByRole("button", { name: /Projetos/ }));
    expect(await screen.findByText("Evasão no primeiro semestre")).toBeInTheDocument();
  });

  it("abre a ferramenta do projeto: ARA para projeto de ARA", async () => {
    montar();
    await userEvent.click(await screen.findByRole("button", { name: /Abrir/ }));
    expect(await screen.findByRole("button", { name: /Prazos são perdidos/ })).toBeInTheDocument();
  });

  it("aplica o tema próprio como variáveis CSS, mesmo sem hospedeiro", async () => {
    const { container } = montar();
    const raiz = container.querySelector(".aplicacao") as HTMLElement;
    expect(raiz.style.getPropertyValue("--toc-color-primary")).toMatch(/#/);
    expect(raiz.style.getPropertyValue("--toc-color-text")).toMatch(/#/);
  });

  it("não fala no canal quando não está embarcada", () => {
    const enviar = vi.fn();
    montar({ enviar });
    expect(enviar).not.toHaveBeenCalled();
  });
});

describe("modo embarcado (§B.8.1: só conteúdo)", () => {
  const URL_EMBARCADA = "https://toc.exemplo/toc/embarcado?embarcado=1";

  it("não renderiza cabeçalho, navegação nem rodapé próprios", async () => {
    montar({ url: URL_EMBARCADA });
    await waitFor(() => expect(screen.queryByRole("banner")).toBeNull());
    expect(screen.queryByRole("navigation")).toBeNull();
    expect(screen.queryByRole("contentinfo")).toBeNull();
    // O conteúdo continua lá: embarcada não quer dizer vazia.
    expect(await screen.findByText("Evasão no primeiro semestre")).toBeInTheDocument();
  });

  it("fala primeiro: emite ghd.ready com targetOrigin dirigido", () => {
    const enviar = vi.fn();
    montar({ url: URL_EMBARCADA, enviar });
    expect(enviar).toHaveBeenCalledTimes(1);
    expect(enviar.mock.calls[0]![0]).toEqual({
      protocol: "ghd",
      v: 1,
      type: "ghd.ready",
      payload: { app_id: "toc" },
    });
    expect(enviar.mock.calls[0]![1]).toBe("https://fundacao.exemplo");
  });

  it("recusa subir sem parâmetro de admissão, dizendo QUAL faltou (§B.4.1)", () => {
    montar({
      url: URL_EMBARCADA,
      ambiente: { ...ADMISSAO, VITE_GHD_HOST_BASE_URL: "" },
    });
    const alerta = screen.getByRole("alert");
    expect(alerta).toHaveTextContent(/VITE_GHD_HOST_BASE_URL/);
    expect(screen.queryByText("Evasão no primeiro semestre")).toBeNull();
  });

  it("veste os tokens do inquilino por cima do tema próprio quando o handshake chega", async () => {
    // `source` de um MessageEvent é somente-leitura no jsdom e só aceita uma janela real;
    // por isso a janela "pai" do teste é a própria `window`, que é o que o navegador
    // entrega em `event.source` quando o hospedeiro responde.
    const { container } = montar({ url: URL_EMBARCADA, pai: window });
    await act(async () => {
      window.dispatchEvent(
        new MessageEvent("message", {
          source: window,
          origin: "https://fundacao.exemplo",
          data: {
            protocol: "ghd",
            v: 1,
            type: "ghd.handshake",
            payload: {
              token: "ghdg_grant",
              tenant: { id: "inq-horizonte", name: "Instituição Horizonte" },
              capabilities: ["toc:read"],
              theme: { tokens: { "color-primary": "#7c3aed" } },
            },
          },
        }),
      );
    });
    const raiz = container.querySelector(".aplicacao") as HTMLElement;
    await waitFor(() => expect(raiz.style.getPropertyValue("--toc-color-primary")).toBe("#7c3aed"));
    // O que não veio continua vestido pelo fallback próprio (§B.4.3).
    expect(raiz.style.getPropertyValue("--toc-color-text")).toMatch(/#/);
  });

  it("descarta mensagem de origem estranha, sem efeito e sem resposta", async () => {
    const enviar = vi.fn();
    const { container } = montar({ url: URL_EMBARCADA, pai: window, enviar });
    enviar.mockClear();
    await act(async () => {
      window.dispatchEvent(
        new MessageEvent("message", {
          source: window,
          origin: "https://invasor.exemplo",
          data: {
            protocol: "ghd",
            v: 1,
            type: "ghd.handshake",
            payload: { token: "x", theme: { tokens: { "color-primary": "#ff0000" } } },
          },
        }),
      );
    });
    await waitFor(() => expect(enviar).not.toHaveBeenCalled());
    const raiz = container.querySelector(".aplicacao") as HTMLElement;
    expect(raiz.style.getPropertyValue("--toc-color-primary")).not.toBe("#ff0000");
  });
});

describe("idioma pela URL", () => {
  it("abre em inglês quando a URL de embarque pede inglês", async () => {
    montar({ url: "https://toc.exemplo/toc/projetos?idioma=en" });
    expect(await screen.findByRole("heading", { name: "Projects", level: 1 })).toBeInTheDocument();
  });
});
