/**
 * A vista tabular indentada da S&T — revisão e edição em reunião, sem canvas (RF-19, RI-08).
 *
 * Siglas, uma vez: **S&T** — Estratégia & Táticas (*Strategy & Tactics*) · **RF/RI** —
 * requisito funcional / de interface da spec 010.
 *
 * A hierarquia sobrevive **por indentação**, e o número é a primeira coluna: a ordem é
 * estrutural e fixa, porque uma tabela de plano que reordena a cada abertura não se lê em
 * grupo. A presença das premissas aparece como marca — quem quer o texto abre a ficha, e
 * é a ficha que tem a leitura dirigida (RI-03).
 */
import type { LinhaDaSnT } from "../../dominio/tipos";
import { useI18n } from "../../i18n";

export interface TabelaDaSnTProps {
  linhas: readonly LinhaDaSnT[];
  selecionado: string | null;
  aoSelecionar(noId: string): void;
}

export function TabelaDaSnT({ linhas, selecionado, aoSelecionar }: TabelaDaSnTProps) {
  const { t } = useI18n();
  return (
    <table className="tabela-da-snt">
      <caption>{t("snt.tabela")}</caption>
      <thead>
        <tr>
          <th scope="col">{t("snt.coluna.numero")}</th>
          <th scope="col">{t("snt.coluna.estrategia")}</th>
          <th scope="col">{t("snt.coluna.tatica")}</th>
          <th scope="col">{t("snt.coluna.premissas")}</th>
          <th scope="col">{t("snt.coluna.status")}</th>
        </tr>
      </thead>
      <tbody>
        {linhas.map((linha) => (
          <tr
            key={linha.no_id}
            aria-selected={selecionado === linha.no_id}
            className={`nivel-${linha.nivel}`}
          >
            <th scope="row" style={{ paddingLeft: `${linha.nivel * 1.5}rem` }}>
              <button type="button" onClick={() => aoSelecionar(linha.no_id)}>
                {linha.numero}
              </button>
            </th>
            <td>{linha.estrategia}</td>
            <td className={linha.tatica ? "" : "ausente"}>
              {linha.tatica || t("snt.sem_tatica")}
            </td>
            <td className="marcas-de-premissa">
              {/* Três marcas, na ordem dos papéis: paralela · necessidade · suficiência. */}
              <span
                title={t("snt.premissa.paralela")}
                aria-label={t("snt.premissa.paralela")}
                data-presente={linha.tem_premissa_paralela}
              >
                {linha.tem_premissa_paralela ? "●" : "○"}
              </span>
              <span
                title={t("snt.premissa.necessidade_ao_pai")}
                aria-label={t("snt.premissa.necessidade_ao_pai")}
                data-presente={linha.tem_premissa_de_necessidade}
              >
                {linha.tem_premissa_de_necessidade ? "●" : "○"}
              </span>
              <span
                title={t("snt.premissa.suficiencia_dos_filhos")}
                aria-label={t("snt.premissa.suficiencia_dos_filhos")}
                data-presente={linha.tem_premissa_de_suficiencia}
              >
                {linha.tem_premissa_de_suficiencia ? "●" : "○"}
              </span>
            </td>
            <td className={`status-${linha.status}`}>{t(`snt.status.${linha.status}`)}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
