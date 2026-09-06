/**
 * A linha do tempo dos ciclos — a história da análise (RI-04, RF-17).
 *
 * Siglas, uma vez: **TOC** — Teoria das Restrições · **RI/RF/RN** — requisito de interface
 * / funcional / regra de negócio.
 *
 * O que esta lista mostra, e que é o argumento inteiro do quinto passo: **ela cresce e
 * nunca encolhe** (RN-04). Um ciclo fechado continua aqui com a restrição que ele
 * perseguiu, as datas e o número de decisões — é o que permite comparar a restrição de
 * hoje com a de dois ciclos atrás e perceber que ela migrou de etapa.
 *
 * O ciclo fechado é **visualmente distinto** e abre em somente leitura. E quem diz que é
 * somente leitura é o servidor (`somente_leitura` na resposta da jornada), não um `if`
 * desta tela: a regra vive no domínio, e a interface a exibe.
 */
import type { CicloNaLinha } from "../../dominio/tipos";
import { useI18n } from "../../i18n";

export interface LinhaDoTempoProps {
  ciclos: readonly CicloNaLinha[];
  cicloAberto: string;
  aoAbrirCiclo(cicloId: string): void;
}

function data(bruta: string | null): string {
  if (!bruta) return "—";
  const quando = new Date(bruta);
  return Number.isNaN(quando.getTime()) ? bruta : quando.toLocaleDateString();
}

export function LinhaDoTempo({ ciclos, cicloAberto, aoAbrirCiclo }: LinhaDoTempoProps) {
  const { t } = useI18n();

  return (
    <section className="linha-do-tempo" aria-labelledby="linha-do-tempo-titulo">
      <h3 id="linha-do-tempo-titulo">{t("foco.linha_do_tempo.titulo")}</h3>
      <ol>
        {ciclos.map((ciclo) => (
          <li
            key={ciclo.ciclo_id}
            data-estado={ciclo.estado}
            data-selecionado={ciclo.ciclo_id === cicloAberto}
          >
            <button type="button" onClick={() => aoAbrirCiclo(ciclo.ciclo_id)}>
              <span className="ciclo-ordem">{t("foco.ciclo", { n: ciclo.ordem })}</span>
              <span className="ciclo-restricao">
                {ciclo.restricao ?? t("foco.linha_do_tempo.sem_restricao")}
              </span>
              {/* Estado por rótulo, nunca só por cor — a mesma regra da trilha (RI-01). */}
              <span className="ciclo-estado">
                {ciclo.estado === "fechado"
                  ? t("foco.somente_leitura")
                  : t(`foco.passo_curto.${ciclo.passo_atual}`)}
              </span>
              <span className="ciclo-datas">
                {t("foco.linha_do_tempo.aberto_em")}: {data(ciclo.aberto_em)}
                {ciclo.fechado_em
                  ? ` · ${t("foco.linha_do_tempo.fechado_em")}: ${data(ciclo.fechado_em)}`
                  : ""}
              </span>
              <span className="ciclo-decisoes">
                {t("foco.linha_do_tempo.decisoes", { n: ciclo.decisoes })}
              </span>
              {ciclo.herancas_pendentes > 0 ? (
                <span className="ciclo-pendencias">
                  {t("foco.heranca.pendentes", { n: ciclo.herancas_pendentes })}
                </span>
              ) : null}
            </button>
          </li>
        ))}
      </ol>
    </section>
  );
}
