// Internacionalização desde o primeiro dia (RI-10 da spec 005, RI-11 da spec 007).
//
// A linhagem que sucedemos acertou aqui — `tocbuilderv3/i18n/` com `pt.ts` e `en.ts` — e
// o que ela não tinha era teste: as duas tabelas dela divergiram em silêncio (`pt.ts` tem
// 465 linhas, `en.ts` tem 464). A paridade abaixo é a função de aptidão dessa dívida.
import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { CODIGOS } from "../api/erros";
import { pt } from "./pt";
import { en } from "./en";
import { ProvedorDeIdioma, traduzirCom, useI18n } from "./index";

function folhas(objeto: unknown, prefixo = ""): string[] {
  if (typeof objeto === "string") return [prefixo];
  return Object.entries(objeto as Record<string, unknown>).flatMap(([chave, valor]) =>
    folhas(valor, prefixo ? `${prefixo}.${chave}` : chave),
  );
}

describe("dicionários", () => {
  it("português e inglês têm exatamente as mesmas chaves", () => {
    expect(folhas(en).sort()).toEqual(folhas(pt).sort());
  });

  it("nenhuma tradução está vazia", () => {
    for (const dicionario of [pt, en]) {
      for (const chave of folhas(dicionario)) {
        expect(traduzirCom(dicionario, chave as never), chave).toMatch(/\S/);
      }
    }
  });

  it("traduz os doze critérios de validação de UDE pela chave estável do domínio", () => {
    // As chaves são as do catálogo do serviço (`apps/api/src/toc_api/dominio/
    // criterios_ude.py`): oito decidíveis e quatro de julgamento. A chave do critério é a
    // mesma da regra de domínio, "para a rastreabilidade spec ↔ código ↔ tela" (RNF-09).
    const esperadas = [
      "frase_completa",
      "tempo_presente",
      "estado_nao_acao",
      "nao_culpa",
      "nao_e_solucao",
      "uma_entidade",
      "sem_causa_embutida",
      "factual",
      "queixa_continua",
      "esfera_de_influencia",
      "acionavel",
      "nao_e_causa_especulada",
    ];
    expect(Object.keys(pt.criterio).sort()).toEqual([...esperadas].sort());
    expect(Object.keys(en.criterio).sort()).toEqual([...esperadas].sort());
  });

  it("todo código que a interface trata de forma diferente tem texto nos dois idiomas", () => {
    // A lista de `CODIGOS` é o que a tela discrimina; sem texto, o código cai no genérico
    // e a pessoa lê "o serviço recusou a operação" sobre um caso que tem saída própria.
    // Foi assim que `IDEMPOTENCY_KEY_REUSED` entrou: código novo do serviço não quebra a
    // tela, mas passa despercebido até alguém conferir.
    const doServico = Object.values(CODIGOS).filter((c) => /^[A-Z][A-Z0-9_]*$/.test(c));
    for (const codigo of doServico) {
      expect(Object.keys(pt.erro), `pt.erro.${codigo}`).toContain(codigo);
      expect(Object.keys(en.erro), `en.erro.${codigo}`).toContain(codigo);
    }
  });

  it("traduz os três avisos de formulação da nuvem pelo código do domínio", () => {
    expect(Object.keys(pt.aviso).sort()).toEqual([
      "d_linha_nao_nega_d",
      "d_pede_infinitivo",
      "pede_substantivo",
    ]);
  });

  it("interpola parâmetros", () => {
    expect(traduzirCom(pt, "canvas.raio_da_exclusao", { n: 3 })).toContain("3");
  });

  it("devolve a própria chave quando ela não existe — nunca `undefined` na tela", () => {
    expect(traduzirCom(pt, "nao.existe" as never)).toBe("nao.existe");
  });
});

function Amostra() {
  const { t, idioma, trocarIdioma } = useI18n();
  return (
    <div>
      <p>{t("projetos.titulo")}</p>
      <p data-testid="idioma">{idioma}</p>
      <button onClick={() => trocarIdioma(idioma === "pt" ? "en" : "pt")}>trocar</button>
    </div>
  );
}

describe("provedor de idioma", () => {
  it("nasce em português e troca para inglês sem recarregar", async () => {
    render(
      <ProvedorDeIdioma>
        <Amostra />
      </ProvedorDeIdioma>,
    );
    expect(screen.getByText(pt.projetos.titulo)).toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: "trocar" }));
    expect(screen.getByTestId("idioma")).toHaveTextContent("en");
    expect(screen.getByText(en.projetos.titulo)).toBeInTheDocument();
  });

  it("respeita o idioma inicial recebido do hospedeiro", () => {
    render(
      <ProvedorDeIdioma idiomaInicial="en">
        <Amostra />
      </ProvedorDeIdioma>,
    );
    expect(screen.getByTestId("idioma")).toHaveTextContent("en");
  });
});
