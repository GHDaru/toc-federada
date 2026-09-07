// E8.4 — o acervo e o painel de documentação embutida (spec 011).
//
// Siglas, uma vez neste arquivo: **ARA** — Árvore da Realidade Atual · **NC** — Nuvem de
// Conflito · **ARF** — Árvore da Realidade Futura · **APR** — Árvore de Pré-Requisitos ·
// **AT** — Árvore de Transição · **S&T** — Estratégia & Táticas · **RF/RI/RN** —
// requisito funcional / de interface / regra de negócio da spec 011 · **ADR** —
// *Architecture Decision Record*.
//
// **O precedente que estes testes sucedem, medido:** a quarta geração da linhagem tinha
// um `DocsView` com quatro tópicos (`tocbuilderv3/components/DocsView.tsx:21-26`) para
// seis ferramentas declaradas (`types.ts:249-258`) — e as outras quatro respondiam
// `"Esta ferramenta ainda não foi implementada."` (`locales/pt.ts:424`).
//
// Aqui a cobertura é regra (RN-04) e tem portão. Este arquivo cobre o lado da interface;
// `scripts/check-documentacao.sh` cobre o lado que importa mais — a lista de ferramentas
// vem do REGISTRO do serviço, não de uma segunda lista que se confere a si mesma.
import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { PainelDeDocumentacao } from "../componentes/documentacao/PainelDeDocumentacao";
import { BotaoDeAjuda } from "../componentes/documentacao/BotaoDeAjuda";
import { ProvedorDeIdioma } from "../i18n";
import { INDICE, VerbeteAusente, carregarVerbete, ferramentasCobertas, temVerbete } from "./acervo";
import { ancorasDe, apresentar } from "./tipos";

function comIdioma(no: React.ReactNode, idioma: "pt" | "en" = "pt") {
  return render(<ProvedorDeIdioma idiomaInicial={idioma}>{no}</ProvedorDeIdioma>);
}

describe("acervo (RF-18, RN-04)", () => {
  it("as sete ferramentas do escopo v1 têm verbete", async () => {
    // As mesmas sete que o domínio do serviço registra em `registrar_raiz_de_ferramenta`.
    const esperadas = ["apr", "ara", "arf", "at", "focalizacao", "nc", "snt"];
    expect(ferramentasCobertas()).toEqual(esperadas);
    expect(INDICE.map((e) => e.ferramenta).sort()).toEqual(esperadas);
  });

  it("cada verbete carrega, declara a ferramenta certa e cita procedência", async () => {
    for (const ferramenta of ferramentasCobertas()) {
      const verbete = await carregarVerbete(ferramenta);
      expect(verbete.ferramenta, ferramenta).toBe(ferramenta);
      expect(verbete.procedencia.length, ferramenta).toBeGreaterThan(0);
      for (const caminho of verbete.procedencia) {
        expect(caminho, ferramenta).toMatch(/^(specs|docs)\//);
      }
    }
  });

  it("cada verbete diz o que a ferramenta responde, tem seções com âncora e exemplo", async () => {
    for (const ferramenta of ferramentasCobertas()) {
      const verbete = await carregarVerbete(ferramenta);
      expect(verbete.pt.resposta.length, ferramenta).toBeGreaterThan(20);
      expect(verbete.pt.secoes.length, ferramenta).toBeGreaterThanOrEqual(2);
      expect(new Set(ancorasDe(verbete)).size, ferramenta).toBe(ancorasDe(verbete).length);
      // RI-06: o exemplo é sintético e da persona fictícia (ADR 0006).
      expect(verbete.pt.exemplo, ferramenta).toContain("Horizonte");
      for (const secao of verbete.pt.secoes) {
        expect(secao.ancora, `${ferramenta}/${secao.ancora}`).toMatch(/^[a-z0-9-]+$/);
        expect(secao.paragrafos.length, `${ferramenta}/${secao.ancora}`).toBeGreaterThan(0);
      }
    }
  });

  it("ferramenta sem verbete falha alto em vez de devolver uma tela vazia", async () => {
    expect(temVerbete("inventada")).toBe(false);
    await expect(carregarVerbete("inventada")).rejects.toBeInstanceOf(VerbeteAusente);
  });

  it("nenhum verbete cita geração por modelo em tempo de execução (ADR 0007)", async () => {
    for (const ferramenta of ferramentasCobertas()) {
      const verbete = await carregarVerbete(ferramenta);
      const bruto = JSON.stringify(verbete);
      expect(bruto, ferramenta).not.toMatch(/gemini|openai|anthropic|api[_-]?key/i);
    }
  });
});

describe("fallback bilíngue declarado (F8.4.3, RF-21)", () => {
  it("verbete traduzido aparece no idioma efetivo, sem aviso", async () => {
    const nc = await carregarVerbete("nc");
    const apresentado = apresentar(nc, "en");
    expect(apresentado.idioma).toBe("en");
    expect(apresentado.traducaoPendente).toBe(false);
    expect(apresentado.conteudo.titulo).toBe("Conflict Cloud");
  });

  it("verbete só em português aparece na língua-fonte COM aviso de pendência", async () => {
    const at = await carregarVerbete("at");
    const apresentado = apresentar(at, "en");
    expect(apresentado.idioma).toBe("pt");
    expect(apresentado.traducaoPendente).toBe(true);
    expect(apresentado.conteudo.titulo).toBe("Árvore de Transição");
  });
});

describe("painel de documentação (RI-04, RI-05, RF-19, RF-20)", () => {
  it("abre com índice à esquerda e o verbete da ferramenta à direita", async () => {
    comIdioma(<PainelDeDocumentacao ferramenta="ara" aoFechar={() => {}} />);

    expect(await screen.findByRole("heading", { name: "Árvore da Realidade Atual", level: 3 }))
      .toBeInTheDocument();
    const indice = screen.getByRole("navigation", { name: "Ferramentas" });
    expect(indice.querySelectorAll("li")).toHaveLength(7);
    expect(screen.getByRole("heading", { name: /Efeito Indesejável/ })).toBeInTheDocument();
  });

  it("navega entre tópicos sem fechar o painel", async () => {
    const usuario = userEvent.setup();
    comIdioma(<PainelDeDocumentacao ferramenta="ara" aoFechar={() => {}} />);
    await screen.findByRole("heading", { name: "Árvore da Realidade Atual", level: 3 });

    await usuario.click(screen.getByRole("button", { name: "Nuvem de Conflito" }));

    expect(await screen.findByRole("heading", { name: "Nuvem de Conflito", level: 3 }))
      .toBeInTheDocument();
    expect(screen.getByRole("complementary", { name: "Documentação" })).toBeInTheDocument();
  });

  it("abre no trecho ancorado quando a ajuda vem de um campo (RF-20)", async () => {
    const { container } = comIdioma(
      <PainelDeDocumentacao ferramenta="nc" ancora="premissa-sustentada" aoFechar={() => {}} />,
    );
    await screen.findByRole("heading", { name: "Nuvem de Conflito", level: 3 });

    const alvo = container.querySelector("#verbete-premissa-sustentada");
    expect(alvo).not.toBeNull();
    expect(alvo?.textContent).toContain("premissa");
  });

  it("fecha por botão e devolve o foco ao controle de origem (RI-05)", async () => {
    const usuario = userEvent.setup();
    const aoFechar = vi.fn();
    const origem = document.createElement("button");
    origem.textContent = "abrir ajuda";
    document.body.appendChild(origem);
    origem.focus();

    comIdioma(<PainelDeDocumentacao ferramenta="ara" aoFechar={aoFechar} />);
    await screen.findByRole("heading", { name: "Árvore da Realidade Atual", level: 3 });

    await usuario.click(screen.getByRole("button", { name: "Fechar a documentação" }));

    expect(aoFechar).toHaveBeenCalled();
    expect(document.activeElement).toBe(origem);
    origem.remove();
  });

  it("Escape fecha o painel — ele é operável inteiramente por teclado", async () => {
    const usuario = userEvent.setup();
    const aoFechar = vi.fn();
    comIdioma(<PainelDeDocumentacao ferramenta="ara" aoFechar={aoFechar} />);
    await screen.findByRole("heading", { name: "Árvore da Realidade Atual", level: 3 });

    await usuario.keyboard("{Escape}");

    expect(aoFechar).toHaveBeenCalled();
  });

  it("mostra o aviso de tradução pendente em inglês, com o conteúdo da língua-fonte", async () => {
    comIdioma(<PainelDeDocumentacao ferramenta="at" aoFechar={() => {}} />, "en");

    expect(await screen.findByRole("note")).toHaveTextContent(/English translation pending/);
    expect(screen.getByRole("heading", { name: "Árvore de Transição", level: 3 }))
      .toBeInTheDocument();
  });

  it("oferece a chamada para a ferramenta descrita (RI-06)", async () => {
    const usuario = userEvent.setup();
    const ir = vi.fn();
    comIdioma(<PainelDeDocumentacao ferramenta="apr" aoFechar={() => {}} aoIrParaFerramenta={ir} />);
    await screen.findByRole("heading", { name: "Árvore de Pré-Requisitos", level: 3 });

    await usuario.click(screen.getByRole("button", { name: "Ir para a ferramenta" }));

    expect(ir).toHaveBeenCalledWith("apr");
  });

  it("ferramenta sem verbete mostra recusa, e não uma tela em branco", async () => {
    comIdioma(<PainelDeDocumentacao ferramenta="inventada" aoFechar={() => {}} />);
    expect(await screen.findByRole("alert")).toHaveTextContent(/verbete/);
  });
});

describe("botão de ajuda ancorado (F8.4.2)", () => {
  it("declara ferramenta e âncora, e as entrega a quem abre o painel", async () => {
    const usuario = userEvent.setup();
    const abrir = vi.fn();
    comIdioma(<BotaoDeAjuda ferramenta="nc" ancora="premissa-sustentada" aoAbrir={abrir} />);

    await usuario.click(screen.getByRole("button", { name: "Abrir a ajuda sobre este campo" }));

    expect(abrir).toHaveBeenCalledWith("nc", "premissa-sustentada");
  });

  it("toda âncora que a interface declara existe no verbete correspondente", async () => {
    // O mesmo que o portão confere sobre o repositório inteiro — aqui sobre o uso real.
    const nc = await carregarVerbete("nc");
    expect(ancorasDe(nc)).toContain("premissa-sustentada");
  });
});
