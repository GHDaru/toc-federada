// Um componente conforme: toda cadeia visível vem do dicionário.
import { traduzirCom } from "../i18n";
import { pt } from "../i18n/pt";

const t = (chave: string) => traduzirCom(pt, chave);

export function Barra({ n }: { n: number }) {
  return (
    <header aria-label={t("app.titulo")}>
      <h1>{t("projetos.titulo")}</h1>
      <p title={t("projetos.contagem")}>{t("projetos.contagem")}</p>
      <button type="button">{t("app.salvar")}</button>
      <button type="button">{t("app.cancelar")}</button>
      {/* Um símbolo solto NÃO é literal de tradução — e o portão sabe disso. */}
      <span>×</span>
    </header>
  );
}
