/**
 * Os pares obstáculo → objetivo intermediário, com o teste de validade e o julgamento.
 *
 * Siglas, uma vez: **APR** — Árvore de Pré-Requisitos · **OI** — Objetivo Intermediário ·
 * **RN/RF** — regra de negócio / requisito funcional.
 *
 * Duas regras da spec 008 aparecem a olho nu aqui:
 *
 * 1. **O teste de validade vem montado do servidor** ("Se <OI>, então <obstáculo> deixa de
 *    impedir o objetivo"). A tela não o remonta: ele é leitura do agregado, dos textos
 *    atuais dos dois nós, e remontá-lo aqui faria a frase envelhecer sozinha.
 * 2. **O julgamento ACUMULA e nunca sobrescreve** (RN-07), e o **autor vem do principal**
 *    no servidor — não há campo de autor neste formulário, e a ausência é o requisito:
 *    "quem julgou" não é texto que alguém digita.
 */
import { useState } from "react";
import type { NoDaArvore, ParObstaculoOi } from "../../dominio/tipos";
import { useI18n } from "../../i18n";

export interface ParesDaAprProps {
  pares: readonly ParObstaculoOi[];
  nos: readonly NoDaArvore[];
  ocupado?: boolean;
  aoJulgar(parId: string, valido: boolean, justificativa: string): void;
  aoDesfazerPar(parId: string): void;
}

export function ParesDaApr({ pares, nos, ocupado = false, aoJulgar, aoDesfazerPar }: ParesDaAprProps) {
  const { t } = useI18n();
  const titulo = (id: string) => nos.find((no) => no.id === id)?.titulo ?? id;

  return (
    <section className="pares-da-apr" role="region" aria-label={t("apr.obstaculos")}>
      <h3>{t("apr.obstaculos")}</h3>
      <p className="explicacao">{t("apr.obstaculos_explicacao")}</p>
      {pares.length === 0 ? (
        <p className="vazio">{t("apr.vazio")}</p>
      ) : (
        <ul className="lista-de-pares">
          {pares.map((par) => (
            <FichaDoPar
              key={par.id}
              par={par}
              obstaculo={titulo(par.obstaculo_id)}
              oi={titulo(par.objetivo_intermediario_id)}
              ocupado={ocupado}
              aoJulgar={aoJulgar}
              aoDesfazerPar={aoDesfazerPar}
            />
          ))}
        </ul>
      )}
    </section>
  );
}

function FichaDoPar({
  par,
  obstaculo,
  oi,
  ocupado,
  aoJulgar,
  aoDesfazerPar,
}: {
  par: ParObstaculoOi;
  obstaculo: string;
  oi: string;
  ocupado: boolean;
  aoJulgar(parId: string, valido: boolean, justificativa: string): void;
  aoDesfazerPar(parId: string): void;
}) {
  const { t } = useI18n();
  const [justificativa, setJustificativa] = useState("");
  const armado = Boolean(justificativa.trim()) && !ocupado;

  return (
    <li className="ficha-do-par" aria-label={obstaculo}>
      <p className="rotulo">{t("apr.obstaculo")}</p>
      <p className="texto-do-obstaculo">{obstaculo}</p>
      <p className="rotulo">{t("apr.objetivo_intermediario")}</p>
      <p className="texto-do-oi">{oi}</p>

      <p className="rotulo">{t("apr.teste_de_validade")}</p>
      <p className="teste-de-validade">{par.teste_de_validade}</p>

      {par.julgamentos.length > 0 ? (
        <div className="julgamentos">
          <p>{t("apr.julgamentos", { n: par.julgamentos.length })}</p>
          <ul>
            {par.julgamentos.map((j, indice) => (
              <li key={`${j.autor}-${indice}`} data-valido={j.valido ? "sim" : "nao"}>
                {j.valido ? t("apr.julgado_valido") : t("apr.julgado_invalido")} · {j.autor} ·{" "}
                {j.justificativa}
              </li>
            ))}
          </ul>
        </div>
      ) : null}

      <label htmlFor={`julgamento-${par.id}`}>{t("apr.justificativa")}</label>
      <textarea
        id={`julgamento-${par.id}`}
        rows={2}
        value={justificativa}
        onChange={(evento) => setJustificativa(evento.target.value)}
      />
      {/* Válido e inválido têm o MESMO peso na tela: julgar contra é decisão tão legítima
          quanto julgar a favor, e uma interface que destaca só o "sim" empurra o veredito. */}
      <div className="vereditos">
        <button
          type="button"
          disabled={!armado}
          onClick={() => aoJulgar(par.id, true, justificativa.trim())}
        >
          {t("apr.julgar_valido")}
        </button>
        <button
          type="button"
          disabled={!armado}
          onClick={() => aoJulgar(par.id, false, justificativa.trim())}
        >
          {t("apr.julgar_invalido")}
        </button>
        <button type="button" disabled={ocupado} onClick={() => aoDesfazerPar(par.id)}>
          {t("apr.desfazer_par")}
        </button>
      </div>
    </li>
  );
}
