/**
 * Os ramos negativos e a **poda** — a superfície que separa uma árvore de futuro séria de
 * uma lista de desejos.
 *
 * Siglas, uma vez: **ARF** — Árvore da Realidade Futura · **RN/RF** — regra de negócio /
 * requisito funcional.
 *
 * Três decisões deste componente, cada uma com regra por trás:
 *
 * 1. **Região própria, não mais um nó.** O ramo negativo é o efeito indevido que a
 *    própria injeção traz. Desenhá-lo como um efeito qualquer da árvore é dizer que ele é
 *    mais uma consequência boa — que é exatamente o erro que a ferramenta existe para
 *    impedir. Aqui ele tem lugar, estado e ação próprios.
 * 2. **O seletor da poda só oferece INJEÇÃO** (RN-04): um ramo negativo é cortado por
 *    injeção adicional, nunca por um efeito. A recusa continua existindo no servidor — a
 *    tela não a substitui, só evita oferecer o que já se sabe recusado.
 * 3. **Aceitar exige justificativa escrita, e o botão não arma sem ela.** O autor não é
 *    pedido em campo nenhum: ele vem do principal no servidor, como o parecer do M2 —
 *    "quem aceitou" não é texto que alguém digita.
 */
import { useState } from "react";
import type { NoDaArvore, RamoNegativo } from "../../dominio/tipos";
import { useI18n } from "../../i18n";

export interface RamosNegativosProps {
  ramos: readonly RamoNegativo[];
  nos: readonly NoDaArvore[];
  ocupado?: boolean;
  aoPodar(ramoId: string, injecaoId: string): void;
  aoAceitar(ramoId: string, justificativa: string): void;
  aoReabrir(ramoId: string): void;
}

export function RamosNegativos({
  ramos,
  nos,
  ocupado = false,
  aoPodar,
  aoAceitar,
  aoReabrir,
}: RamosNegativosProps) {
  const { t, tc } = useI18n();
  const injecoes = nos.filter((no) => no.papel === "injecao");
  const titulo = (id: string | null) => nos.find((no) => no.id === id)?.titulo ?? "";

  return (
    <section className="ramos-negativos" role="region" aria-label={t("arf.ramo.titulo")}>
      <h3>{t("arf.ramo.titulo")}</h3>
      <p className="explicacao">{t("arf.ramo.explicacao")}</p>
      {ramos.length === 0 ? (
        <p className="vazio">{t("arf.ramo.vazio")}</p>
      ) : (
        <ul className="lista-de-ramos">
          {ramos.map((ramo) => (
            <FichaDoRamo
              key={ramo.id}
              ramo={ramo}
              raiz={titulo(ramo.raiz_id)}
              corte={titulo(ramo.injecao_de_corte_id)}
              injecoes={injecoes}
              ocupado={ocupado}
              aoPodar={aoPodar}
              aoAceitar={aoAceitar}
              aoReabrir={aoReabrir}
              t={t}
              tc={tc}
            />
          ))}
        </ul>
      )}
    </section>
  );
}

type Traducao = ReturnType<typeof useI18n>;

function FichaDoRamo({
  ramo,
  raiz,
  corte,
  injecoes,
  ocupado,
  aoPodar,
  aoAceitar,
  aoReabrir,
  t,
  tc,
}: {
  ramo: RamoNegativo;
  raiz: string;
  corte: string;
  injecoes: readonly NoDaArvore[];
  ocupado: boolean;
  aoPodar(ramoId: string, injecaoId: string): void;
  aoAceitar(ramoId: string, justificativa: string): void;
  aoReabrir(ramoId: string): void;
  t: Traducao["t"];
  tc: Traducao["tc"];
}) {
  const [injecao, setInjecao] = useState("");
  const [justificativa, setJustificativa] = useState("");
  const aberto = ramo.estado === "aberto";

  return (
    <li className="ficha-do-ramo" aria-label={raiz} data-estado={ramo.estado}>
      <p className="rotulo-do-ramo">{t("arf.ramo.raiz")}</p>
      <p className="texto-da-raiz">{raiz}</p>
      {/* Estado por extenso, e como dado no elemento: uma tela monocromática e um leitor
          de tela leem a mesma coisa (a regra de rótulo do M6). */}
      <p className="estado-do-ramo">{tc("estado_do_ramo", ramo.estado)}</p>

      {aberto ? (
        <div className="acoes-do-ramo">
          <div className="poda">
            <label htmlFor={`poda-${ramo.id}`}>{t("arf.ramo.injecao_de_corte")}</label>
            <select
              id={`poda-${ramo.id}`}
              value={injecao}
              onChange={(evento) => setInjecao(evento.target.value)}
            >
              <option value="">{t("arf.ramo.escolha_a_injecao")}</option>
              {injecoes.map((no) => (
                <option key={no.id} value={no.id}>
                  {no.titulo}
                </option>
              ))}
            </select>
            <button
              type="button"
              disabled={ocupado || !injecao}
              onClick={() => aoPodar(ramo.id, injecao)}
            >
              {t("arf.ramo.podar")}
            </button>
          </div>
          <div className="aceite">
            <label htmlFor={`aceite-${ramo.id}`}>{t("arf.ramo.justificativa")}</label>
            <textarea
              id={`aceite-${ramo.id}`}
              rows={2}
              value={justificativa}
              onChange={(evento) => setJustificativa(evento.target.value)}
            />
            <button
              type="button"
              disabled={ocupado || !justificativa.trim()}
              onClick={() => aoAceitar(ramo.id, justificativa.trim())}
            >
              {t("arf.ramo.aceitar")}
            </button>
          </div>
        </div>
      ) : (
        <div className="desfecho-do-ramo">
          {ramo.estado === "tratado" ? (
            <p className="poda-aplicada">
              {t("arf.ramo.poda")}: <strong>{corte}</strong>
            </p>
          ) : (
            <>
              <p className="justificativa-do-aceite">{ramo.justificativa}</p>
              <p className="autor-do-aceite">{t("arf.ramo.aceito_por", { autor: ramo.autor })}</p>
            </>
          )}
          <button type="button" disabled={ocupado} onClick={() => aoReabrir(ramo.id)}>
            {t("arf.ramo.reabrir")}
          </button>
        </div>
      )}
    </li>
  );
}
