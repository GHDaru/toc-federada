/**
 * A cadeia da análise — o percurso completo da Teoria das Restrições (TOC) numa tela só.
 *
 * Siglas, uma vez: **TOC** — Teoria das Restrições · **ARA** — Árvore da Realidade Atual ·
 * **UDE** — Efeito Indesejável · **NC** — Nuvem de Conflito · **ARF** — Árvore da Realidade
 * Futura · **APR** — Árvore de Pré-Requisitos · **AT** — Árvore de Transição · **OI** —
 * Objetivo Intermediário · **API** — interface de programação de aplicações.
 *
 * **É esta tela que nenhuma das quatro gerações da linhagem chegou perto de ter.** Elas
 * desenhavam ferramentas isoladas — uma Árvore da Realidade Atual aqui, uma Nuvem de
 * Conflito ali —, e o que faltava era o fio: que o Efeito Indesejável validado de hoje é o
 * dilema de amanhã, que a injeção escolhida semeia a árvore de futuro, que o efeito futuro
 * deriva os pré-requisitos e que o objetivo intermediário vira o plano de transição. Sem
 * esse fio, a Teoria das Restrições vira seis diagramas bonitos e nenhuma análise.
 *
 * A tela é **leitura pura**: nenhuma escrita acontece aqui. Promover, semear e derivar são
 * gestos das telas de origem, onde a pessoa escolhe o elemento — aqui ela confere o
 * percurso e navega por ele.
 */
import { useCallback } from "react";
import type { Cliente } from "../api/cliente";
import type { Cadeia } from "../dominio/tipos";
import { Carregando, EstadoDeErro } from "../componentes/Estados";
import { PercursoDaCadeia } from "../componentes/cadeia/PercursoDaCadeia";
import { useRecurso } from "../estado/useRecurso";
import { useI18n } from "../i18n";

export interface TelaDaCadeiaProps {
  cliente: Cliente;
  /** Qualquer elemento encadeado serve de porta de entrada — a travessia é nos dois sentidos. */
  projetoId: string;
  aoVoltar(): void;
  aoAbrirProjeto?(destino: { ferramenta: string; projetoId: string }): void;
}

export function TelaDaCadeia({
  cliente,
  projetoId,
  aoVoltar,
  aoAbrirProjeto,
}: TelaDaCadeiaProps) {
  const { t, tc } = useI18n();
  const buscar = useCallback(() => cliente.cadeia.abrir(projetoId), [cliente, projetoId]);
  const { dado, carregando, erro, recarregar } = useRecurso<Cadeia>(buscar, [cliente, projetoId]);

  if (carregando && !dado) return <Carregando />;
  if (erro && !dado) return <EstadoDeErro erro={erro} aoTentarDeNovo={() => void recarregar()} />;
  if (!dado) return null;

  const cadeia = dado;
  const pendentes = cadeia.resumo.elos_pendentes ?? 0;

  return (
    <section className="tela tela-da-cadeia" aria-label={t("cadeia.titulo")}>
      <div className="cabecalho-do-projeto">
        <button type="button" onClick={aoVoltar}>
          {t("app.voltar")}
        </button>
        <h1>{t("cadeia.titulo")}</h1>
        <p className="explicacao">{t("cadeia.explicacao")}</p>
        <p className="resumo-da-cadeia" role="status">
          {t("cadeia.resumo", {
            elos: cadeia.resumo.elos ?? cadeia.elos.length,
            ferramentas: cadeia.resumo.ferramentas ?? cadeia.ferramentas.length,
            projetos: cadeia.resumo.projetos ?? 0,
          })}
        </p>
        {/* A contagem de pendentes fica no cabeçalho de propósito: o aviso não pode
            depender de a pessoa rolar até o fim da lista para descobrir que há um vínculo
            quebrado. */}
        <p className="pendentes-da-cadeia">
          {pendentes > 0 ? t("cadeia.pendentes", { n: pendentes }) : t("cadeia.sem_pendentes")}
        </p>
      </div>

      {cadeia.ferramentas.length > 0 ? (
        <ol className="trilha-de-ferramentas" aria-label={t("cadeia.ferramentas")}>
          {cadeia.ferramentas.map((ferramenta) => (
            <li key={ferramenta} data-ferramenta={ferramenta}>
              {tc("ferramenta", ferramenta)}
            </li>
          ))}
        </ol>
      ) : null}

      <PercursoDaCadeia elos={cadeia.elos} aoAbrirProjeto={aoAbrirProjeto} />
    </section>
  );
}
