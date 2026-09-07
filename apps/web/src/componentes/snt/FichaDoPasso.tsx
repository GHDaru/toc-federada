/**
 * A ficha do passo da S&T — e a disposição dela ENSINA o método (RI-03).
 *
 * Siglas, uma vez: **S&T** — Estratégia & Táticas (*Strategy & Tactics*) · **RI/RF/RN** —
 * requisito de interface / funcional / regra de negócio da spec 010.
 *
 * A quarta geração da linhagem já tinha os três campos de premissa — e os empilhava em
 * três áreas de texto sem contexto nenhum
 * (`tocbuilderv3/components/SnTStepEditorModal.tsx:137-159`). Aqui cada premissa aparece
 * **na posição de leitura dela**: a de necessidade acima, ligada ao pai; a de suficiência
 * abaixo, ligada aos filhos nomeados; a paralela ao lado, como pressuposto de contexto. A
 * frase dirigida ("Para alcançar 1…, é necessário 1.1… porque…") vem montada do servidor,
 * onde a regra do método mora (RF-13) — regra de método que mora na tela é regra que a
 * segunda tela reescreve diferente.
 *
 * O número aparece **somente leitura**. Não existe campo de número neste formulário, e é
 * essa ausência que aposenta o defeito da linhagem (`SnTStepEditorModal.tsx:56-57`: número
 * obrigatório, texto livre, sem validação de formato nem de unicidade).
 */
import { useEffect, useState } from "react";
import {
  CATEGORIAS_DA_SNT,
  STATUS_DA_SNT,
  type CategoriaDoPasso,
  type FichaDoPassoSnT,
  type PapelDaPremissa,
  type StatusDoPassoSnT,
} from "../../dominio/tipos";
import { useI18n } from "../../i18n";

export interface FichaDoPassoProps {
  ficha: FichaDoPassoSnT;
  somenteLeitura?: boolean;
  ocupado?: boolean;
  aoEditar(campos: { estrategia?: string; tatica?: string; categoria?: CategoriaDoPasso }): void;
  aoEditarPremissa(papel: PapelDaPremissa, texto: string): void;
  aoMudarStatus(status: StatusDoPassoSnT): void;
  aoAdicionarFilho(): void;
  aoMover(): void;
  aoExcluir(): void;
}

/** A ordem em que as premissas aparecem: necessidade (pai) · paralela · suficiência (filhos). */
const ORDEM_DE_LEITURA: readonly PapelDaPremissa[] = [
  "necessidade_ao_pai",
  "paralela",
  "suficiencia_dos_filhos",
];

export function FichaDoPasso({
  ficha,
  somenteLeitura = false,
  ocupado = false,
  aoEditar,
  aoEditarPremissa,
  aoMudarStatus,
  aoAdicionarFilho,
  aoMover,
  aoExcluir,
}: FichaDoPassoProps) {
  const { t } = useI18n();
  const [estrategia, setEstrategia] = useState(ficha.estrategia);
  const [tatica, setTatica] = useState(ficha.tatica);
  const [premissas, setPremissas] = useState(ficha.premissas);

  // O passo mudou (a pessoa clicou noutro nó): os rascunhos morrem com o passo que os
  // gerou. Sem isto, o texto de 1.1 continuaria no formulário de 1.2 — o mesmo defeito
  // que a jornada viva do M6 pegou no build real.
  useEffect(() => {
    setEstrategia(ficha.estrategia);
    setTatica(ficha.tatica);
    setPremissas(ficha.premissas);
  }, [ficha.id, ficha.estrategia, ficha.tatica, ficha.premissas]);

  const porPapel = new Map(ficha.leituras.map((leitura) => [leitura.papel, leitura]));

  return (
    <section className="ficha-do-passo" aria-labelledby="ficha-titulo">
      <header>
        <h3 id="ficha-titulo">
          {/* RF-05: o número aparece onde o passo aparece — e é somente leitura. */}
          <span className="numero-do-passo" data-somente-leitura="true">
            {ficha.numero}
          </span>{" "}
          {t("snt.ficha")}
        </h3>
        <p className="status-atual">
          {t("snt.status.rotulo")}: {t(`snt.status.${ficha.status}`)}
        </p>
      </header>

      <div className="campos-do-passo">
        <label htmlFor="passo-estrategia">{t("snt.estrategia")}</label>
        <input
          id="passo-estrategia"
          value={estrategia}
          disabled={somenteLeitura}
          onChange={(evento) => setEstrategia(evento.target.value)}
          onBlur={() => {
            if (estrategia.trim() && estrategia !== ficha.estrategia) {
              aoEditar({ estrategia: estrategia.trim() });
            }
          }}
        />
        <label htmlFor="passo-tatica">{t("snt.tatica")}</label>
        <textarea
          id="passo-tatica"
          rows={2}
          value={tatica}
          disabled={somenteLeitura}
          placeholder={t("snt.tatica_placeholder")}
          onChange={(evento) => setTatica(evento.target.value)}
          onBlur={() => {
            if (tatica !== ficha.tatica) aoEditar({ tatica });
          }}
        />
        <label htmlFor="passo-categoria">{t("snt.categoria")}</label>
        <select
          id="passo-categoria"
          value={ficha.categoria}
          disabled={somenteLeitura}
          onChange={(evento) =>
            aoEditar({ categoria: evento.target.value as CategoriaDoPasso })
          }
        >
          {CATEGORIAS_DA_SNT.map((valor) => (
            <option key={valor} value={valor}>
              {t(`snt.categoria_valor.${valor}`)}
            </option>
          ))}
        </select>
      </div>

      {/* As três premissas NAS POSIÇÕES DE LEITURA (RI-03). */}
      <div className="premissas-do-passo">
        {ORDEM_DE_LEITURA.map((papel) => {
          const leitura = porPapel.get(papel);
          return (
            <section
              key={papel}
              className={`premissa premissa-${papel}${
                leitura && !leitura.aplicavel ? " nao-aplicavel" : ""
              }`}
              aria-labelledby={`premissa-${papel}-titulo`}
            >
              <h4 id={`premissa-${papel}-titulo`}>{t(`snt.premissa.${papel}`)}</h4>
              {leitura ? (
                <p className="leitura-dirigida" data-completa={leitura.completa}>
                  {leitura.texto}
                </p>
              ) : null}
              {leitura && !leitura.aplicavel ? null : (
                <textarea
                  id={`premissa-${papel}`}
                  aria-label={t(`snt.premissa.${papel}`)}
                  rows={2}
                  disabled={somenteLeitura}
                  value={premissas[papel]}
                  placeholder={t(`snt.premissa_placeholder.${papel}`)}
                  onChange={(evento) =>
                    setPremissas({ ...premissas, [papel]: evento.target.value })
                  }
                  onBlur={() => {
                    if (premissas[papel] !== ficha.premissas[papel]) {
                      aoEditarPremissa(papel, premissas[papel]);
                    }
                  }}
                />
              )}
            </section>
          );
        })}
      </div>

      {/* E5.2 — o status, com transição livre entre os quatro valores (RN-03). */}
      <section className="status-do-passo" aria-labelledby="status-titulo">
        <h4 id="status-titulo">{t("snt.status.rotulo")}</h4>
        <div role="group" aria-label={t("snt.status.rotulo")}>
          {STATUS_DA_SNT.map((valor) => (
            <button
              key={valor}
              type="button"
              aria-pressed={ficha.status === valor}
              disabled={somenteLeitura || ocupado || ficha.status === valor}
              onClick={() => aoMudarStatus(valor)}
            >
              {t(`snt.status.${valor}`)}
            </button>
          ))}
        </div>
      </section>

      {somenteLeitura ? null : (
        <p className="acoes-da-ficha">
          <button type="button" onClick={aoAdicionarFilho} disabled={ocupado}>
            {t("snt.adicionar_filho")}
          </button>
          <button type="button" onClick={aoMover} disabled={ocupado}>
            {t("snt.mover_para")}
          </button>
          <button type="button" className="perigo" onClick={aoExcluir} disabled={ocupado}>
            {t("snt.excluir_subarvore")}
          </button>
        </p>
      )}
    </section>
  );
}
