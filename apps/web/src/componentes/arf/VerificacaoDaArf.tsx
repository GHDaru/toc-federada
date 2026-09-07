/**
 * A verificação estrutural da Árvore da Realidade Futura (ARF) — leitura, nunca veto.
 *
 * Siglas, uma vez: **ARF** — Árvore da Realidade Futura · **UDE** — Efeito Indesejável ·
 * **ED** — Efeito Desejável · **RF** — requisito funcional.
 *
 * `pronta` não é um portão: a árvore continua editável com pendência (RF-11). O que a
 * verificação impede é alguém **declarar** a árvore pronta sem olhar. Tudo o que aparece
 * aqui foi computado por função pura no servidor; a interface não reconta nada — uma
 * segunda conta seria uma segunda verdade.
 *
 * A cobertura merece a linha que tem: quando a ARF **não** tem cadeia vinculada, ela diz
 * "sem origem vinculada" em vez de mostrar 0 de 0 (RF-07). Zero por cento e "não se
 * aplica" são coisas diferentes, e confundi-las é como uma ferramenta passa a mentir.
 */
import type { NoDaArvore, VerificacaoDaArf as Verificacao } from "../../dominio/tipos";
import { useI18n } from "../../i18n";

export interface VerificacaoDaArfProps {
  verificacao: Verificacao;
  nos: readonly NoDaArvore[];
  aoFocar?(noId: string): void;
}

export function VerificacaoDaArf({ verificacao, nos, aoFocar }: VerificacaoDaArfProps) {
  const { t } = useI18n();
  const titulo = (id: string) => nos.find((no) => no.id === id)?.titulo ?? id;

  return (
    <section className="verificacao-da-arf" role="region" aria-label={t("arf.verificacao.titulo")}>
      <h3>{t("arf.verificacao.titulo")}</h3>
      <p className="explicacao">{t("arf.verificacao.explicacao")}</p>
      <p className="veredito" data-pronta={verificacao.pronta ? "sim" : "nao"}>
        {verificacao.pronta ? t("arf.verificacao.pronta") : t("arf.verificacao.nao_pronta")}
      </p>

      <ul className="pendencias">
        {verificacao.eds_sem_caminho.length > 0 ? (
          <li>
            {t("arf.verificacao.eds_sem_caminho", { n: verificacao.eds_sem_caminho.length })}
            <ul>
              {verificacao.eds_sem_caminho.map((id) => (
                <li key={id}>
                  <button type="button" onClick={() => aoFocar?.(id)}>
                    {titulo(id)}
                  </button>
                </li>
              ))}
            </ul>
          </li>
        ) : null}
        {verificacao.injecoes_sem_efeito > 0 ? (
          <li>
            {t("arf.verificacao.injecoes_sem_efeito", { n: verificacao.injecoes_sem_efeito })}
            <ul>
              {verificacao.injecoes_sem_efeito_ids.map((id) => (
                <li key={id}>
                  <button type="button" onClick={() => aoFocar?.(id)}>
                    {titulo(id)}
                  </button>
                </li>
              ))}
            </ul>
          </li>
        ) : null}
        {verificacao.ramos_abertos.length > 0 ? (
          <li>{t("arf.verificacao.ramos_abertos", { n: verificacao.ramos_abertos.length })}</li>
        ) : null}
      </ul>

      <h4>{t("arf.verificacao.cobertura")}</h4>
      {verificacao.sem_origem_vinculada ? (
        <p className="sem-origem">{t("arf.verificacao.sem_origem_vinculada")}</p>
      ) : (
        <ul className="cobertura">
          {verificacao.cobertura.map((linha) => (
            <li key={linha.ude_id} data-coberto={linha.alcancado ? "sim" : "nao"}>
              <span className="ude">{linha.ude_id}</span>{" "}
              <span className="estado">
                {!linha.espelhado_por
                  ? t("arf.verificacao.sem_espelho")
                  : linha.alcancado
                    ? t("arf.verificacao.coberto")
                    : t("arf.verificacao.nao_coberto")}
              </span>
              {linha.espelhado_por ? (
                <span className="ed"> · {titulo(linha.espelhado_por)}</span>
              ) : null}
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
