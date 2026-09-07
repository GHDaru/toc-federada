/**
 * O percurso da análise — a travessia inteira, elo a elo.
 *
 * Siglas, uma vez: **ARA** — Árvore da Realidade Atual · **UDE** — Efeito Indesejável ·
 * **NC** — Nuvem de Conflito · **ARF** — Árvore da Realidade Futura · **APR** — Árvore de
 * Pré-Requisitos · **AT** — Árvore de Transição · **RF** — requisito funcional.
 *
 * Cada etapa é um vínculo com duas pontas tipadas: de onde saiu (ferramenta, projeto,
 * papel) e onde chegou. A ordem é a que o servidor devolveu — canônica por construção,
 * porque uma cadeia que se lê diferente a cada abertura não se confere.
 *
 * **O elo pendente fica.** Quando o projeto de destino é excluído, o vínculo não some: ele
 * aparece com o estado `pendente` e o motivo escrito (RF-35, US-18). Esconder o vínculo
 * que perdeu uma ponta é esconder exatamente o que a pessoa precisa consertar — e é o que
 * uma lista "só do que funciona" faria.
 */
import type { EloDaCadeia } from "../../dominio/tipos";
import { useI18n } from "../../i18n";

export interface PercursoDaCadeiaProps {
  elos: readonly EloDaCadeia[];
  aoAbrirProjeto?(destino: { ferramenta: string; projetoId: string }): void;
}

export function PercursoDaCadeia({ elos, aoAbrirProjeto }: PercursoDaCadeiaProps) {
  const { t, tc } = useI18n();

  return (
    <section className="percurso-da-cadeia" role="region" aria-label={t("cadeia.percurso")}>
      <h3>{t("cadeia.percurso")}</h3>
      {elos.length === 0 ? (
        <p className="vazio">{t("cadeia.vazio")}</p>
      ) : (
        <ol className="etapas">
          {elos.map((elo, indice) => (
            <li
              key={elo.referencia_id}
              aria-label={t("cadeia.etapa", { n: indice + 1 })}
              data-tipo={elo.tipo}
              data-estado={elo.estado}
            >
              <h4>{t("cadeia.etapa", { n: indice + 1 })}</h4>
              <p className="costura">{tc("tipo_de_referencia", elo.tipo)}</p>

              <div className="pontas">
                <Ponta
                  rotulo={t("cadeia.de")}
                  ferramenta={elo.origem.ferramenta}
                  projetoId={elo.origem.projeto_id}
                  elementos={elo.origem.elementos.length}
                  // A origem de um elo pendente continua existindo: o que sumiu foi o
                  // destino. Por isso ela segue navegável.
                  navegavel
                  aoAbrirProjeto={aoAbrirProjeto}
                />
                <Ponta
                  rotulo={t("cadeia.para")}
                  ferramenta={elo.destino.ferramenta}
                  projetoId={elo.destino.projeto_id}
                  elementos={elo.destino.elementos.length}
                  navegavel={elo.estado === "ativa"}
                  aoAbrirProjeto={aoAbrirProjeto}
                />
              </div>

              <p className="estado-do-elo">{tc("estado_da_referencia", elo.estado)}</p>
              {elo.motivo ? (
                <p className="motivo-do-elo">
                  {t("cadeia.motivo")}: {elo.motivo}
                </p>
              ) : null}
            </li>
          ))}
        </ol>
      )}
    </section>
  );
}

function Ponta({
  rotulo,
  ferramenta,
  projetoId,
  elementos,
  navegavel,
  aoAbrirProjeto,
}: {
  rotulo: string;
  ferramenta: string;
  projetoId: string;
  elementos: number;
  navegavel: boolean;
  aoAbrirProjeto?(destino: { ferramenta: string; projetoId: string }): void;
}) {
  const { t, tc } = useI18n();
  const nome = tc("ferramenta", ferramenta);
  return (
    <div className="ponta" data-ferramenta={ferramenta}>
      <span className="rotulo">{rotulo}</span>
      <span className="ferramenta">{nome}</span>
      {elementos > 0 ? (
        <span className="elementos">{t("cadeia.elementos", { n: elementos })}</span>
      ) : null}
      {navegavel && aoAbrirProjeto ? (
        <button
          type="button"
          onClick={() => aoAbrirProjeto({ ferramenta, projetoId })}
          aria-label={`${t("cadeia.abrir")} ${nome}`}
        >
          {t("cadeia.abrir")}
        </button>
      ) : null}
    </div>
  );
}
