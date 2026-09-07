/**
 * O painel de acompanhamento da S&T — a árvore como instrumento de reunião (RF-17, RI-07).
 *
 * Siglas, uma vez: **S&T** — Estratégia & Táticas (*Strategy & Tactics*) · **RF/RI** —
 * requisito funcional / de interface da spec 010.
 *
 * **Nada é recalculado aqui.** Contagem por status, pendências lógicas e progresso chegam
 * prontos do servidor, da mesma função pura de domínio (`pendencias_da_arvore`). Uma
 * segunda conta na tela seria uma segunda verdade, e as duas divergiriam no primeiro
 * requisito novo — é a mesma decisão do painel do M6.
 *
 * As contagens são **filtros acionáveis** (RI-07): clicar em "Em execução" filtra a
 * árvore, e o filtro mantém os ancestrais visíveis para dar contexto (RF-18).
 */
import {
  STATUS_DA_SNT,
  type AcompanhamentoDaSnT,
  type StatusDoPassoSnT,
} from "../../dominio/tipos";
import { useI18n } from "../../i18n";

export interface PainelDeAcompanhamentoProps {
  acompanhamento: AcompanhamentoDaSnT;
  filtro: StatusDoPassoSnT | null;
  aoFiltrar(status: StatusDoPassoSnT | null): void;
  aoSaltar(noId: string): void;
}

export function PainelDeAcompanhamento({
  acompanhamento,
  filtro,
  aoFiltrar,
  aoSaltar,
}: PainelDeAcompanhamentoProps) {
  const { t } = useI18n();
  const percentual = Math.round(acompanhamento.progresso * 100);

  return (
    <section className="painel-de-acompanhamento" aria-labelledby="acompanhamento-titulo">
      <h3 id="acompanhamento-titulo">{t("snt.acompanhamento")}</h3>
      <p className="progresso-da-snt" role="status">
        {t("snt.progresso", {
          validados: acompanhamento.por_status.validado ?? 0,
          total: acompanhamento.passos,
          percentual,
        })}
      </p>

      <div className="contagens-por-status" role="group" aria-label={t("snt.filtrar_por_status")}>
        {STATUS_DA_SNT.map((status) => (
          <button
            key={status}
            type="button"
            className={`contagem status-${status}`}
            aria-pressed={filtro === status}
            onClick={() => aoFiltrar(filtro === status ? null : status)}
          >
            <span className="rotulo">{t(`snt.status.${status}`)}</span>{" "}
            <span className="valor">{acompanhamento.por_status[status] ?? 0}</span>
          </button>
        ))}
        {filtro ? (
          <button type="button" className="limpar-filtro" onClick={() => aoFiltrar(null)}>
            {t("snt.limpar_filtro")}
          </button>
        ) : null}
      </div>

      <section className="pendencias-logicas" aria-labelledby="pendencias-titulo">
        <h4 id="pendencias-titulo">
          {t("snt.pendencias_de", {
            n: acompanhamento.pendencias.length,
            total: acompanhamento.passos,
          })}
        </h4>
        {acompanhamento.pendencias.length === 0 ? (
          <p className="vazio">{t("snt.sem_pendencias")}</p>
        ) : (
          <ul>
            {acompanhamento.pendencias.map((pendencia) => (
              <li key={`${pendencia.no_id}-${pendencia.tipo}`}>
                <button type="button" onClick={() => aoSaltar(pendencia.no_id)}>
                  <span className="numero-do-passo">{pendencia.numero}</span>{" "}
                  {t(`snt.pendencia.${pendencia.tipo}`)}
                </button>
              </li>
            ))}
          </ul>
        )}
        {/* RN-06: a pendência informa e prioriza, e nunca trava a gravação. */}
        <p className="aviso-de-pendencia">{t("snt.pendencia_nao_trava")}</p>
      </section>
    </section>
  );
}
