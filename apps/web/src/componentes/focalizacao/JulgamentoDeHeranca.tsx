/**
 * O julgamento das decisões herdadas — a tela onde a inércia é confrontada (RI-05).
 *
 * Siglas, uma vez: **TOC** — Teoria das Restrições · **RI/RN/RF** — requisito de interface
 * / regra de negócio / requisito funcional.
 *
 * A RI-05 pede uma coisa que é fácil de escrever e fácil de trair: **os dois vereditos com
 * o mesmo peso visual**. Manter e revogar são dois botões `type="submit"` iguais, na mesma
 * linha, com a mesma justificativa obrigatória — nenhum deles é o "principal", nenhum é
 * link discreto. É a tradução da RN-05 para pixels: se manter fosse mais barato do que
 * revogar, a interface estaria empurrando a inércia de volta, que é exatamente o que o
 * quinto passo do método existe para impedir.
 *
 * A justificativa é obrigatória nos dois caminhos, e o botão fica desabilitado sem ela: a
 * recusa do domínio existe e é a garantia real, mas fazer a pessoa descobrir a regra por
 * um erro de servidor seria ensinar mal uma regra que é o coração do módulo.
 */
import { useState } from "react";
import type { DecisaoHerdada, VereditoDeHeranca } from "../../dominio/tipos";
import { useI18n } from "../../i18n";

export interface JulgamentoDeHerancaProps {
  heranca: readonly DecisaoHerdada[];
  somenteLeitura: boolean;
  aoJulgar(
    decisaoId: string,
    veredito: Exclude<VereditoDeHeranca, "pendente">,
    justificativa: string,
  ): void;
}

export function JulgamentoDeHeranca({
  heranca,
  somenteLeitura,
  aoJulgar,
}: JulgamentoDeHerancaProps) {
  const { t } = useI18n();
  const [motivos, setMotivos] = useState<Record<string, string>>({});
  const pendentes = heranca.filter((h) => h.veredito === "pendente");

  if (heranca.length === 0) {
    return (
      <section className="julgamento-de-heranca" aria-labelledby="heranca-titulo">
        <h3 id="heranca-titulo">{t("foco.heranca.titulo")}</h3>
        <p className="vazio">{t("foco.heranca.nenhuma")}</p>
      </section>
    );
  }

  return (
    <section className="julgamento-de-heranca" aria-labelledby="heranca-titulo">
      <h3 id="heranca-titulo">{t("foco.heranca.titulo")}</h3>
      <p className="heranca-explicacao">{t("foco.heranca.explicacao")}</p>
      <p className="heranca-contador" role="status" data-pendentes={pendentes.length}>
        {t("foco.heranca.pendentes", { n: pendentes.length })}
      </p>

      <ul className="decisoes-herdadas">
        {heranca.map((decisao) => {
          const motivo = motivos[decisao.id] ?? "";
          const julgada = decisao.veredito !== "pendente";
          return (
            <li key={decisao.id} data-veredito={decisao.veredito}>
              <p className="heranca-origem">
                {t("foco.heranca.origem", {
                  ciclo: decisao.ciclo_de_origem,
                  passo: t(`foco.passo_curto.${decisao.passo}` as never),
                })}
              </p>
              <p className="heranca-texto">{decisao.texto}</p>

              {julgada ? (
                <p className="heranca-julgada">
                  {t("foco.heranca.julgada", {
                    veredito: t(`foco.heranca.veredito.${decisao.veredito}`),
                    autor: decisao.autor,
                  })}
                  {decisao.justificativa ? ` — ${decisao.justificativa}` : ""}
                </p>
              ) : null}

              {!julgada && !somenteLeitura ? (
                <form
                  className="forma-de-veredito"
                  onSubmit={(evento) => evento.preventDefault()}
                >
                  <label htmlFor={`motivo-${decisao.id}`}>
                    {t("foco.heranca.justificativa")}
                  </label>
                  <input
                    id={`motivo-${decisao.id}`}
                    value={motivo}
                    onChange={(evento) =>
                      setMotivos((atual) => ({ ...atual, [decisao.id]: evento.target.value }))
                    }
                  />
                  {/* Mesmo peso visual: dois `submit`, mesma classe, mesma exigência. */}
                  <div className="vereditos" role="group" aria-label={t("foco.heranca.titulo")}>
                    <button
                      type="submit"
                      className="veredito"
                      disabled={!motivo.trim()}
                      onClick={() => aoJulgar(decisao.id, "mantida", motivo.trim())}
                    >
                      {t("foco.heranca.manter")}
                    </button>
                    <button
                      type="submit"
                      className="veredito"
                      disabled={!motivo.trim()}
                      onClick={() => aoJulgar(decisao.id, "revogada", motivo.trim())}
                    >
                      {t("foco.heranca.revogar")}
                    </button>
                  </div>
                </form>
              ) : null}
            </li>
          );
        })}
      </ul>
    </section>
  );
}
