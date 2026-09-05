/**
 * A visão de solução — as SETE posições da nuvem com as injeções que as evaporam.
 *
 * Siglas, uma vez: **NC** — Nuvem de Conflito · **TRIZ** — Teoria da Resolução Inventiva
 * de Problemas · **RF/RI** — requisito funcional / de interface.
 *
 * "As sete posições, incluindo D⇸C e D↯D′ — as que o v3 nunca renderizou" (RF-31 da spec
 * 007). A pendência de injeção tem representação própria e **textual**: uma posição sem
 * injeção é uma parte do conflito que ninguém atacou ainda, e some do olho se for só uma
 * caixa mais clara.
 */
import type { Solucao } from "../../dominio/tipos";
import { useI18n } from "../../i18n";

export function VisaoDeSolucao({ solucao, titulo }: { solucao: Solucao; titulo?: string }) {
  const { t, tc } = useI18n();
  return (
    <section className="visao-de-solucao" aria-label={titulo ?? t("nuvem.solucao")}>
      <ul className="posicoes">
        {solucao.posicoes.map((posicao) => (
          <li key={posicao.chave} className={`posicao ${posicao.classe}${posicao.pendente ? " pendente" : ""}`}>
            <p className="classe">{tc("classe", posicao.classe, posicao.classe)}</p>
            <p className="leitura">{posicao.leitura}</p>
            {posicao.injecoes.length === 0 ? (
              <p className="pendencia">{t("nuvem.pendente_de_injecao")}</p>
            ) : (
              <ul className="injecoes">
                {posicao.injecoes.map((injecao) => (
                  <li key={injecao.id}>
                    <span>{injecao.texto}</span>
                    <span className="injecao-meta">
                      {tc("separacao", injecao.separacao ?? "nenhuma", injecao.separacao ?? "")} ·{" "}
                      {tc("status_da_injecao", injecao.status, injecao.status)}
                    </span>
                  </li>
                ))}
              </ul>
            )}
          </li>
        ))}
      </ul>
    </section>
  );
}
