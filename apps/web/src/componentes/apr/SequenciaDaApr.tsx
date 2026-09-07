/**
 * O sequenciamento da Árvore de Pré-Requisitos (APR) — camadas, ciclos e pendências.
 *
 * Siglas, uma vez: **APR** — Árvore de Pré-Requisitos · **OI** — Objetivo Intermediário ·
 * **RF/RN** — requisito funcional / regra de negócio.
 *
 * **A ordem é a informação principal desta ferramenta.** Uma APR que mostra obstáculos sem
 * dizer o que vem antes de quê é uma lista de queixas com nome bonito. Por isso as camadas
 * são o primeiro bloco da tela, numeradas, com o que cada uma exige antes de si.
 *
 * Duas coisas que este componente **não** faz:
 *
 * 1. **Não ordena nada.** As camadas, os ramos paralelos e os ciclos vêm calculados por
 *    função pura no servidor (`ProjetoAPR.sequenciar`). Uma ordenação aqui seria uma
 *    segunda topologia, e as duas divergiriam no primeiro caso difícil.
 * 2. **Não esconde o ciclo.** Dependência circular é pendência BLOQUEANTE na APR (RN-06,
 *    diferente da Árvore da Realidade Atual): a tela nomeia os nós do ciclo, porque é isso
 *    que a pessoa precisa para desfazer o laço.
 *
 * A camada 0 do servidor vira "Camada 1" na tela: índice é coisa de máquina.
 */
import type { NoDaArvore, ParObstaculoOi, Sequenciamento } from "../../dominio/tipos";
import { useI18n } from "../../i18n";

export interface SequenciaDaAprProps {
  sequenciamento: Sequenciamento;
  nos: readonly NoDaArvore[];
  pares: readonly ParObstaculoOi[];
  dependencias: readonly { id: string; leitura: string }[];
}

export function SequenciaDaApr({
  sequenciamento,
  nos,
  pares,
  dependencias,
}: SequenciaDaAprProps) {
  const { t } = useI18n();
  const titulo = (id: string) => nos.find((no) => no.id === id)?.titulo ?? id;
  const obstaculoDe = (oiId: string) => {
    const par = pares.find((p) => p.objetivo_intermediario_id === oiId);
    return par ? titulo(par.obstaculo_id) : null;
  };

  return (
    <section className="sequencia-da-apr" role="region" aria-label={t("apr.sequencia")}>
      <h3>{t("apr.sequencia")}</h3>
      <p className="explicacao">{t("apr.sequencia_explicacao")}</p>

      <p className="veredito" data-bloqueado={sequenciamento.bloqueado ? "sim" : "nao"}>
        {sequenciamento.bloqueado
          ? t("apr.bloqueado")
          : sequenciamento.completo
            ? t("apr.completo")
            : t("apr.incompleto")}
      </p>

      {sequenciamento.ciclos.length > 0 ? (
        <ul className="ciclos">
          {sequenciamento.ciclos.map((ciclo) => (
            <li key={ciclo.join("-")}>
              {t("apr.ciclo", { lista: ciclo.map(titulo).join(" → ") })}
            </li>
          ))}
        </ul>
      ) : null}

      {sequenciamento.camadas.length === 0 ? (
        <p className="vazio">{t("apr.camada_vazia")}</p>
      ) : (
        <ol className="camadas">
          {sequenciamento.camadas.map((camada, indice) => (
            <li key={indice} aria-label={t("apr.camada", { n: indice + 1 })} data-camada={indice}>
              <h4>{t("apr.camada", { n: indice + 1 })}</h4>
              <ul>
                {camada.map((oiId) => (
                  <li key={oiId}>
                    <span className="oi">{titulo(oiId)}</span>
                    {obstaculoDe(oiId) ? (
                      <span className="obstaculo-vencido">
                        {" "}
                        · {t("apr.obstaculo")}: {obstaculoDe(oiId)}
                      </span>
                    ) : (
                      <span className="sem-obstaculo"> · {t("apr.sem_obstaculo")}</span>
                    )}
                  </li>
                ))}
              </ul>
            </li>
          ))}
        </ol>
      )}

      {sequenciamento.ramos_paralelos.length > 1 ? (
        <p className="ramos-paralelos">
          {t("apr.ramos_paralelos", { n: sequenciamento.ramos_paralelos.length })}
        </p>
      ) : null}

      {/* A lista das dependências declaradas tem vazio PRÓPRIO. Repetir aqui a frase das
          camadas ("declare a primeira dependência") dizia a mesma coisa duas vezes na
          mesma tela, uma delas no lugar errado — achado da captura do build real. */}
      <h4>{t("apr.dependencias_declaradas")}</h4>
      {dependencias.length === 0 ? (
        <p className="vazio">{t("apr.sem_dependencia")}</p>
      ) : (
        <ul className="dependencias">
          {dependencias.map((d) => (
            <li key={d.id}>{d.leitura}</li>
          ))}
        </ul>
      )}

      {sequenciamento.obstaculos_sem_oi.length > 0 ||
      sequenciamento.objetivos_sem_obstaculo.length > 0 ? (
        <div className="pendencias-do-sequenciamento">
          <h4>{t("apr.pendencias")}</h4>
          <ul>
            {sequenciamento.obstaculos_sem_oi.length > 0 ? (
              <li>
                {t("apr.obstaculos_sem_oi", { n: sequenciamento.obstaculos_sem_oi.length })}
                <ul>
                  {sequenciamento.obstaculos_sem_oi.map((id) => (
                    <li key={id}>{titulo(id)}</li>
                  ))}
                </ul>
              </li>
            ) : null}
            {sequenciamento.objetivos_sem_obstaculo.length > 0 ? (
              <li>
                {t("apr.objetivos_sem_obstaculo", {
                  n: sequenciamento.objetivos_sem_obstaculo.length,
                })}
                <ul>
                  {sequenciamento.objetivos_sem_obstaculo.map((id) => (
                    <li key={id}>{titulo(id)}</li>
                  ))}
                </ul>
              </li>
            ) : null}
          </ul>
        </div>
      ) : null}
    </section>
  );
}
