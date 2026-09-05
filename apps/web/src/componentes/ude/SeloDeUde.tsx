/**
 * O selo do Efeito Indesejável (UDE), no canvas e na tabela.
 *
 * RI-01 da spec 005: "com o status de validação por cor **e** por texto (nunca só cor)".
 * A cor é uma classe; o texto é o conteúdo. Quem enxerga pouco contraste, quem imprime em
 * preto e branco e quem usa leitor de tela recebem a mesma informação.
 */
import type { StatusDeValidacao } from "../../dominio/tipos";
import { useI18n } from "../../i18n";

export function SeloDeUde({ status }: { status: StatusDeValidacao }) {
  const { t, tc } = useI18n();
  return (
    <span className={`selo selo-${status}`}>
      <abbr title={t("ude.selo_longo")}>{t("ude.selo")}</abbr>
      <span className="selo-status">{tc("status", status, status)}</span>
    </span>
  );
}
