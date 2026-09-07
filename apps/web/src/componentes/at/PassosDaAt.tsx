/**
 * Os passos da Árvore de Transição (AT), na ordem de execução.
 *
 * Siglas, uma vez: **AT** — Árvore de Transição · **RF/RN** — requisito funcional / regra
 * de negócio.
 *
 * **A tripla é obrigatória e é visível.** Necessidade, ação e resultado esperado saem
 * rotulados em cada passo (RN-10): uma tela que mostrasse só a ação transformaria a árvore
 * numa lista de tarefas, que é precisamente o que a AT não é — cada passo existe *porque*
 * alguma coisa falta, e promete um resultado que depois se confere.
 *
 * Duas decisões:
 *
 * 1. **A ordem vem do servidor** (`ordem_de_leitura`), reprodutível por construção. Um
 *    plano que se lê em ordem diferente a cada abertura não se leva a lugar nenhum.
 * 2. **O resultado real não apaga o esperado** (RF-30). Quando divergem, os dois ficam na
 *    tela com a divergência dita por extenso — é a diferença entre aprender com o plano e
 *    reescrever a história dele.
 */
import { useState } from "react";
import type { PassoDaAt, StatusDoPasso } from "../../dominio/tipos";
import { useI18n } from "../../i18n";

const STATUS: readonly StatusDoPasso[] = ["pendente", "em_execucao", "concluido", "bloqueado"];

export interface PassosDaAtProps {
  passos: readonly PassoDaAt[];
  ordem: readonly string[];
  inalcancaveis: readonly string[];
  ocupado?: boolean;
  aoMudarStatus(
    passoId: string,
    dados: { status: StatusDoPasso; motivo: string; resultado_real: string },
  ): void;
  aoExcluir(passoId: string): void;
}

export function PassosDaAt({
  passos,
  ordem,
  inalcancaveis,
  ocupado = false,
  aoMudarStatus,
  aoExcluir,
}: PassosDaAtProps) {
  const { t } = useI18n();
  const porId = new Map(passos.map((p) => [p.id, p]));
  // A ordem é a do servidor; um passo que não estiver nela (nunca deveria) entra no fim,
  // visível — sumir com ele seria esconder exatamente o caso estranho.
  const ordenados = [
    ...ordem.map((id) => porId.get(id)).filter((p): p is PassoDaAt => Boolean(p)),
    ...passos.filter((p) => !ordem.includes(p.id)),
  ];

  return (
    <section className="passos-da-at" role="region" aria-label={t("at.passos")}>
      <h3>{t("at.passos")}</h3>
      <p className="explicacao">{t("at.passos_explicacao")}</p>
      {ordenados.length === 0 ? (
        <p className="vazio">{t("at.vazio")}</p>
      ) : (
        <ol className="lista-de-passos">
          {ordenados.map((passo) => (
            <FichaDoPasso
              key={passo.id}
              passo={passo}
              inalcancavel={inalcancaveis.includes(passo.id)}
              ocupado={ocupado}
              aoMudarStatus={aoMudarStatus}
              aoExcluir={aoExcluir}
            />
          ))}
        </ol>
      )}
    </section>
  );
}

function FichaDoPasso({
  passo,
  inalcancavel,
  ocupado,
  aoMudarStatus,
  aoExcluir,
}: {
  passo: PassoDaAt;
  inalcancavel: boolean;
  ocupado: boolean;
  aoMudarStatus(
    passoId: string,
    dados: { status: StatusDoPasso; motivo: string; resultado_real: string },
  ): void;
  aoExcluir(passoId: string): void;
}) {
  const { t, tc } = useI18n();
  const [status, setStatus] = useState<StatusDoPasso>(passo.status);
  const [motivo, setMotivo] = useState("");
  const [real, setReal] = useState("");

  return (
    <li
      className="ficha-do-passo"
      aria-label={passo.leitura}
      data-passo={passo.id}
      data-status={passo.status}
    >
      <p className="leitura-corrida">{passo.leitura}</p>

      <p className="rotulo">{t("at.necessidade")}</p>
      <p className="necessidade">{passo.necessidade}</p>
      <p className="rotulo">{t("at.acao")}</p>
      <p className="acao">{passo.acao}</p>
      <p className="rotulo">{t("at.resultado_esperado")}</p>
      <p className="resultado-esperado">{passo.resultado_esperado}</p>

      <p className="status-atual">{tc("status_do_passo", passo.status)}</p>
      {passo.motivo_do_bloqueio ? (
        <p className="motivo-do-bloqueio">
          <span className="rotulo">{t("at.motivo")}</span> {passo.motivo_do_bloqueio}
        </p>
      ) : null}
      {passo.resultado_real ? (
        <>
          <p className="rotulo">{t("at.resultado_real")}</p>
          <p className="resultado-real">{passo.resultado_real}</p>
        </>
      ) : null}
      {passo.divergente ? <p className="divergencia">{t("at.divergente")}</p> : null}
      {inalcancavel ? <p className="inalcancavel">{t("at.inalcancavel")}</p> : null}

      <label htmlFor={`status-${passo.id}`}>{t("at.status")}</label>
      <select
        id={`status-${passo.id}`}
        value={status}
        onChange={(evento) => setStatus(evento.target.value as StatusDoPasso)}
      >
        {STATUS.map((valor) => (
          <option key={valor} value={valor}>
            {tc("status_do_passo", valor)}
          </option>
        ))}
      </select>

      {/* Os dois campos ficam sempre à mão, e o botão continua clicável: bloquear sem
          motivo e concluir sem resultado real são recusas do SERVIDOR, com a regra
          nomeada — esconder o botão ensinaria a pessoa a não ver a regra. */}
      <label htmlFor={`motivo-${passo.id}`}>{t("at.motivo")}</label>
      <input
        id={`motivo-${passo.id}`}
        value={motivo}
        onChange={(evento) => setMotivo(evento.target.value)}
      />
      <label htmlFor={`real-${passo.id}`}>{t("at.resultado_real")}</label>
      <input
        id={`real-${passo.id}`}
        value={real}
        onChange={(evento) => setReal(evento.target.value)}
      />

      <div className="acoes-do-passo">
        <button
          type="button"
          disabled={ocupado}
          onClick={() =>
            aoMudarStatus(passo.id, {
              status,
              motivo: motivo.trim(),
              resultado_real: real.trim(),
            })
          }
        >
          {t("at.mudar_status")}
        </button>
        <button type="button" disabled={ocupado} onClick={() => aoExcluir(passo.id)}>
          {t("at.excluir")}
        </button>
      </div>
    </li>
  );
}
