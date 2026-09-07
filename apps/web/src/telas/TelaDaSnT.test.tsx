/**
 * A tela da árvore de Estratégia & Táticas (S&T) — o resgate, medido na interface.
 *
 * Siglas, uma vez: **S&T** — Estratégia & Táticas (*Strategy & Tactics*) · **RI/RF/RN** —
 * requisito de interface / funcional / regra de negócio da spec 010 · **DOM** — *Document
 * Object Model*.
 *
 * O que estes testes protegem, e cada um responde a um defeito medido da linhagem:
 *
 * 1. **Não existe campo de número em formulário nenhum** (RF-06). A quarta geração o
 *    exigia digitado (`tocbuilderv3/components/SnTStepEditorModal.tsx:56-57`); aqui o teste
 *    varre o DOM inteiro procurando um campo de número e exige zero.
 * 2. **As três premissas aparecem nas posições de leitura** (RI-03), com a frase dirigida
 *    montada contra pai e filhos — a linhagem as empilhava sem contexto (`:137-159`).
 * 3. **Excluir avisa a contagem antes** (RI-06) — o contraexemplo é o defeito que apagava
 *    todos os passos menos o excluído (`tocbuilderv3/services/mockApiService.ts:521`).
 * 4. **Mover pré-visualiza a renumeração** (RI-05) antes de confirmar.
 * 5. **O status distingue por forma e rótulo, nunca só por cor** (RI-02).
 *
 * Base sintética (ADR 0006): "Instituição Horizonte", personas fictícias.
 */
import { beforeEach, describe, expect, it, vi } from "vitest";
import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { TelaDaSnT } from "./TelaDaSnT";
import { clienteFalso, renderComIdioma, SNT, FICHA_DO_PASSO } from "../testes/apoio";

/**
 * `clienteFalso` funde no PRIMEIRO nível; o bloco `snt` é sobrescrito inteiro. Aqui a
 * fusão é feita campo a campo para o teste trocar um método sem perder os outros doze.
 */
function abrir(metodosDaSnT: Record<string, unknown> = {}) {
  const base = clienteFalso();
  const cliente = clienteFalso({ snt: { ...base.snt, ...metodosDaSnT } });
  renderComIdioma(<TelaDaSnT cliente={cliente} projetoId="p-snt" aoVoltar={() => {}} />);
  return cliente;
}

describe("TelaDaSnT", () => {
  // A escolha de vista persiste na sessão (é o desenho: quem conduz um grupo não quer
  // reescolher a aba a cada recarga). Num arquivo de teste, isso vaza de um caso para o
  // seguinte — então cada caso começa do padrão.
  beforeEach(() => {
    try {
      window.sessionStorage.clear();
    } catch {
      /* sem armazenamento: o padrão já é a árvore */
    }
  });

  it("desenha a árvore da estrutura, com a meta global no topo e a numeração derivada", async () => {
    abrir();
    expect(await screen.findByText(SNT.meta_global)).toBeInTheDocument();
    for (const passo of SNT.passos) {
      expect(screen.getByText(passo.numero)).toBeInTheDocument();
    }
    // Três níveis: o portão do roadmap para o ciclo 010.
    expect(SNT.passos.map((p) => p.numero)).toContain("1.1.2");
  });

  it("não oferece campo de número em formulário nenhum (RF-06)", async () => {
    abrir();
    await screen.findByText(SNT.meta_global);
    const usuario = userEvent.setup();
    await usuario.click(screen.getAllByRole("button", { name: /Adicionar filho/i })[0]!);

    const campos = [
      ...screen.queryAllByRole("textbox"),
      ...screen.queryAllByRole("spinbutton"),
      ...screen.queryAllByRole("combobox"),
    ];
    const suspeitos = campos.filter((campo) => {
      const rotulo = `${campo.getAttribute("id") ?? ""} ${campo.getAttribute("aria-label") ?? ""}`;
      return /numero|número|step/i.test(rotulo);
    });
    // eslint-disable-next-line no-console
    console.log(`campos de entrada examinados: ${campos.length} · de número: ${suspeitos.length}`);
    expect(suspeitos).toEqual([]);
  });

  it("mostra as três premissas nas posições de leitura, com a frase dirigida (RI-03)", async () => {
    abrir();
    const usuario = userEvent.setup();
    await usuario.click(await screen.findByRole("button", { name: /1\.1 Reduzir/ }));

    const ficha = await screen.findByRole("region", { name: /Ficha do passo/i });
    expect(ficha).toBeInTheDocument();
    for (const leitura of FICHA_DO_PASSO.leituras) {
      expect(await screen.findByText(leitura.texto)).toBeInTheDocument();
    }
    // A de necessidade vem ANTES da paralela, e a de suficiência depois: é a disposição
    // que ensina o método (RI-03).
    const titulos = [...ficha.querySelectorAll("h4")].map((h) => h.textContent ?? "");
    expect(titulos[0]).toMatch(/necessidade/i);
    expect(titulos[1]).toMatch(/paralela/i);
    expect(titulos[2]).toMatch(/suficiência/i);
  });

  it("mostra a contagem antes de excluir a subárvore (RI-06)", async () => {
    const previaDeExclusao = vi.fn(async () => ({
      no_id: "s2",
      numero: "1.1",
      passos: 3,
      primeiro_nivel: SNT.passos.filter((p) => p.pai_id === "s2"),
    }));
    const excluirSubarvore = vi.fn(async () => SNT);
    abrir({ previaDeExclusao, excluirSubarvore });

    const usuario = userEvent.setup();
    await usuario.click(await screen.findByRole("button", { name: /1\.1 Reduzir/ }));
    await usuario.click(await screen.findByRole("button", { name: /Excluir subárvore/i }));

    expect(await screen.findByText(/3 passo\(s\) serão excluídos/)).toBeInTheDocument();
    expect(excluirSubarvore).not.toHaveBeenCalled();

    await usuario.click(screen.getByRole("button", { name: /Excluir mesmo assim/i }));
    await waitFor(() => expect(excluirSubarvore).toHaveBeenCalledWith("p-snt", "s2"));
  });

  it("pré-visualiza a renumeração antes de confirmar o movimento (RI-05)", async () => {
    const previaDeMover = vi.fn(async () => ({
      mudancas: [
        { no_id: "s2", numero_atual: "1.1", numero_novo: "2" },
        { no_id: "s3", numero_atual: "1.1.1", numero_novo: "2.1" },
      ],
    }));
    const mover = vi.fn(async () => SNT);
    abrir({ previaDeMover, mover });

    const usuario = userEvent.setup();
    await usuario.click(await screen.findByRole("button", { name: /1\.1 Reduzir/ }));
    await usuario.click(await screen.findByRole("button", { name: /Mover para/i }));

    expect(await screen.findByText("1.1 passa a ser 2")).toBeInTheDocument();
    expect(mover).not.toHaveBeenCalled();

    await usuario.click(screen.getByRole("button", { name: /Confirmar o movimento/i }));
    await waitFor(() => expect(mover).toHaveBeenCalled());
  });

  it("distingue o status por rótulo escrito, e não só por cor (RI-02)", async () => {
    abrir();
    await screen.findByText(SNT.meta_global);
    // O passo `1.1` da fixture está em execução: o rótulo aparece escrito no nó.
    expect(screen.getAllByText(/Em Execução/).length).toBeGreaterThan(0);
  });

  it("muda o status pelo botão e o autor NÃO vai no pedido (RN-03)", async () => {
    const mudarStatus = vi.fn(async () => FICHA_DO_PASSO);
    abrir({ mudarStatus });
    const usuario = userEvent.setup();
    await usuario.click(await screen.findByRole("button", { name: /1\.1 Reduzir/ }));
    await usuario.click(await screen.findByRole("button", { name: "Validado" }));
    await waitFor(() => expect(mudarStatus).toHaveBeenCalledWith("p-snt", "s2", "validado"));
    // Três argumentos: projeto, passo e status. Quem mudou vem do token, no servidor.
    expect(mudarStatus.mock.calls[0]).toHaveLength(3);
  });

  it("o painel de acompanhamento filtra por status e mantém os ancestrais visíveis (RF-18)", async () => {
    abrir();
    const usuario = userEvent.setup();
    await usuario.click(await screen.findByRole("button", { name: /Acompanhamento/i }));
    await usuario.click(await screen.findByRole("button", { name: /Em Execução\s*1/ }));

    // `1.1` está em execução; `1` é ancestral e continua visível **como contexto**
    // (apagado, marcado `fora-do-filtro`); `1.2` e as folhas saem da árvore.
    await waitFor(() => {
      expect(document.querySelectorAll(".no-da-snt.fora-do-filtro").length).toBe(1);
    });
    const numeros = [...document.querySelectorAll(".arvore-da-snt .numero-do-passo")].map(
      (elemento) => elemento.textContent,
    );
    // eslint-disable-next-line no-console
    console.log(`passos em tela com o filtro "em execução": ${numeros.join(", ")}`);
    expect(numeros).toEqual(["1", "1.1"]);
  });

  it("as pendências lógicas saltam para o passo e não travam nada (RN-06)", async () => {
    abrir();
    const usuario = userEvent.setup();
    await usuario.click(await screen.findByRole("button", { name: /Acompanhamento/i }));
    expect(
      await screen.findByText(/pendência\(s\) lógica\(s\)/),
    ).toBeInTheDocument();
    expect(screen.getByText(/nunca impede gravar/i)).toBeInTheDocument();

    await usuario.click(screen.getAllByRole("button", { name: /sem premissa de necessidade/ })[0]!);
    expect(await screen.findByRole("region", { name: /Ficha do passo/i })).toBeInTheDocument();
  });

  it("a vista tabular sai indentada e em ordem estrutural (RI-08)", async () => {
    abrir();
    const usuario = userEvent.setup();
    await usuario.click(await screen.findByRole("button", { name: "Tabela" }));
    const linhas = await screen.findAllByRole("row");
    // Cabeçalho + uma linha por passo, na ordem estrutural da fixture.
    const numeros = linhas.slice(1).map((linha) => linha.querySelector("th button")?.textContent);
    expect(numeros).toEqual(SNT.passos.map((p) => p.numero));
  });

  it("a recusa do servidor aparece na tela em vez de esconder o botão", async () => {
    const { ErroDaApi } = await import("../api/erros");
    const mover = vi.fn(async () => {
      throw new ErroDaApi("INVALID_MOVE", "para_a_propria_subarvore", 409, {
        motivo: "para_a_propria_subarvore",
      });
    });
    abrir({ mover });
    const usuario = userEvent.setup();
    await usuario.click(await screen.findByRole("button", { name: /1\.1 Reduzir/ }));
    await usuario.click(await screen.findByRole("button", { name: /Mover para/i }));
    await usuario.click(await screen.findByRole("button", { name: /Confirmar o movimento/i }));
    expect(await screen.findByRole("alert")).toBeInTheDocument();
  });
});
