/**
 * O relatório estrutural da ARA — painel lateral com seções recolhíveis e foco por item
 * (RI-07 da spec 005).
 *
 * Siglas, uma vez: **ARA** — Árvore da Realidade Atual · **UDE** — Efeito Indesejável.
 *
 * Cada item leva a algum lugar: fragmento, entrada, elo não examinado e ciclo têm ação de
 * **focar** o nó no canvas. Um relatório que aponta um problema sem levar até ele obriga
 * quem lê a caçar o nó — e é assim que a análise vira relatório para ninguém.
 */
import type { No, RelatorioEstrutural as Relatorio } from "../../dominio/tipos";
import { useI18n } from "../../i18n";

export interface RelatorioEstruturalProps {
  relatorio: Relatorio;
  nos: readonly No[];
  aoFocar(noId: string): void;
  aoFechar(): void;
}

export function RelatorioEstrutural({ relatorio, nos, aoFocar, aoFechar }: RelatorioEstruturalProps) {
  const { t } = useI18n();
  const titulo = (id: string) => nos.find((no) => no.id === id)?.titulo ?? id;

  function Lista({ rotulo, ids }: { rotulo: string; ids: readonly string[] }) {
    return (
      <details open={ids.length > 0}>
        <summary>
          {rotulo} ({ids.length})
        </summary>
        {ids.length === 0 ? null : (
          <ul>
            {ids.map((id) => (
              <li key={id}>
                <span>{titulo(id)}</span>
                <button type="button" onClick={() => aoFocar(id)}>
                  {t("relatorio.focar")}
                </button>
              </li>
            ))}
          </ul>
        )}
      </details>
    );
  }

  return (
    <aside className="relatorio" aria-label={t("relatorio.titulo")}>
      <div className="ficha-cabecalho">
        <h2>{t("relatorio.titulo")}</h2>
        <button type="button" onClick={aoFechar}>
          {t("app.fechar")}
        </button>
      </div>

      <p className="totais">
        {t("relatorio.totais", { nos: relatorio.total_de_nos, udes: relatorio.total_de_udes })}
      </p>

      <details open>
        <summary>
          {t("relatorio.causa_raiz")} ({relatorio.causas_raiz_candidatas.length})
        </summary>
        {relatorio.causa_raiz_candidata ? (
          <p className="causa-raiz">
            <span>{titulo(relatorio.causa_raiz_candidata)}</span>
            <button type="button" onClick={() => aoFocar(relatorio.causa_raiz_candidata!)}>
              {t("relatorio.focar")}
            </button>
          </p>
        ) : (
          <p className="vazio">{t("relatorio.causa_raiz_ausente")}</p>
        )}
      </details>

      <details open={relatorio.fragmentos.length > 1}>
        <summary>
          {t("relatorio.fragmentos")} ({relatorio.fragmentos.length})
        </summary>
        <ol>
          {relatorio.fragmentos.map((fragmento, indice) => (
            <li key={indice}>{fragmento.map(titulo).join(" · ")}</li>
          ))}
        </ol>
      </details>

      <details open={relatorio.alcances.length > 0}>
        <summary>
          {t("relatorio.alcance")} ({relatorio.alcances.length})
        </summary>
        {relatorio.alcances.length === 0 ? (
          <p className="vazio">{t("relatorio.vazio")}</p>
        ) : (
          <ul>
            {relatorio.alcances.map((alcance) => (
              <li key={alcance.no_id}>
                <span>
                  {titulo(alcance.no_id)} — {Math.round(alcance.fracao * 100)}%
                </span>
                <button type="button" onClick={() => aoFocar(alcance.no_id)}>
                  {t("relatorio.focar")}
                </button>
              </li>
            ))}
          </ul>
        )}
      </details>

      <Lista rotulo={t("relatorio.entradas")} ids={relatorio.entradas} />
      <Lista rotulo={t("relatorio.udes_nao_alcancados")} ids={relatorio.udes_nao_alcancados} />
      <Lista rotulo={t("relatorio.orfaos")} ids={relatorio.orfaos} />
      <Lista rotulo={t("relatorio.ciclos")} ids={relatorio.nos_em_ciclo} />

      <details open={relatorio.elos_nao_examinados.length > 0}>
        <summary>
          {t("relatorio.elos_nao_examinados")} ({relatorio.elos_nao_examinados.length})
        </summary>
        <ul>
          {relatorio.elos_nao_examinados.map((id) => (
            <li key={id}>{id}</li>
          ))}
        </ul>
      </details>

      {relatorio.observacoes.length ? (
        <details open>
          <summary>{t("relatorio.observacoes")}</summary>
          <ul>
            {relatorio.observacoes.map((texto, indice) => (
              <li key={indice}>{texto}</li>
            ))}
          </ul>
        </details>
      ) : null}
    </aside>
  );
}
