/**
 * A superfície de confirmação — `proposta-de-acao`, **uma** para toda ação `confirm`.
 *
 * Siglas, uma vez: **APH** — Aplicação ↔ Harness (o padrão da fronteira) · **IA** —
 * inteligência artificial · **NC** — Nuvem de Conflito · **TTL** — *Time To Live* (tempo
 * de vida) · **RI/RF** — requisito de interface / funcional.
 *
 * É aqui que o laço da assistência fecha, e é aqui que ele fecha **pelo caminho certo**: o
 * conteúdo assistido não vira escrita porque a tela o aplicou, e sim porque uma proposta
 * de ação atravessou a máquina de estados no servidor —
 * `proposed → awaiting_approval → confirmed → executing → executed` — e alguém decidiu.
 * Esta tela é a decisão; a escrita é do servidor.
 *
 * Quatro regras da spec 006 moram no componente, e não em prosa:
 *
 * 1. **Uma superfície, não uma por módulo** (RI-01). Ela recebe uma `Proposta` e não sabe
 *    nada da Nuvem de Conflito: geração, sugestão de premissa ou lote de nós usam esta
 *    mesma tela. Uma superfície por módulo seria N lugares onde esquecer o gate.
 * 2. **A origem é dado, nunca desvio de fluxo** (RI-02). `humano` e `ia` mudam uma
 *    palavra na tela e mais nada — nenhum `if` sobre origem decide o que aparece. No
 *    instante em que virar `if`, as duas telas divergem e a menos testada é a de mais
 *    risco.
 * 3. **Os alvos são contados ANTES da decisão** (RI-03); o desfecho por alvo aparece
 *    depois dela, com o motivo de cada um.
 * 4. **Confirmar e recusar têm o mesmo peso** (RI-01, e RI-06 da spec 007): a mesma
 *    classe, o mesmo tamanho, lado a lado. Recusar não é o botão pequeno.
 *
 * Acessibilidade (RI-09): o foco vai ao resumo quando ela abre, a decisão é operável por
 * teclado e a mudança de estado é anunciada por `aria-live` — o desfecho não é um sumiço.
 */
import { useEffect, useRef } from "react";
import type { Proposta } from "../../dominio/tipos";
import { useI18n } from "../../i18n";

export interface SuperficieDeConfirmacaoProps {
  proposta: Proposta;
  aoConfirmar(): void;
  aoRecusar(): void;
  aoFechar(): void;
  /** Uma decisão já viajando: os botões param de aceitar clique (nunca dois efeitos). */
  ocupada?: boolean;
}

/** Enquanto ela espera decisão, não há desfecho para mostrar — e vice-versa. */
function pendente(proposta: Proposta): boolean {
  return proposta.status === null || proposta.status === undefined;
}

function instante(bruto: string): string {
  const data = new Date(bruto);
  return Number.isNaN(data.getTime()) ? bruto : data.toLocaleString();
}

export function SuperficieDeConfirmacao({
  proposta,
  aoConfirmar,
  aoRecusar,
  aoFechar,
  ocupada = false,
}: SuperficieDeConfirmacaoProps) {
  const { t, tc } = useI18n();
  const resumo = useRef<HTMLHeadingElement>(null);
  const esperando = pendente(proposta);

  useEffect(() => {
    // RI-09: o foco vai ao resumo ao abrir. Quem decide precisa ler antes de decidir, e
    // quem navega por teclado não deveria ter de procurar a superfície que acabou de nascer.
    resumo.current?.focus();
  }, []);

  return (
    <section
      className="ficha superficie-de-confirmacao"
      role="region"
      aria-label={t("proposta.titulo")}
    >
      <div className="ficha-cabecalho">
        <h2 ref={resumo} tabIndex={-1}>
          {t("proposta.titulo")}
        </h2>
        {esperando ? <p className="aviso-de-proposta">{t("proposta.aguardando")}</p> : null}
      </div>

      <p className="resumo-da-proposta">{proposta.titulo}</p>
      <dl className="dados-da-proposta">
        <dt>{t("proposta.acao")}</dt>
        <dd>
          <code>{proposta.action_id}</code>
        </dd>
        <dt>{t("proposta.origem")}</dt>
        {/* Dado. Nunca desvio de fluxo (RI-02). */}
        <dd>{tc("origem_da_proposta", proposta.origem, proposta.origem)}</dd>
        {/* A contagem é do LOTE (APH-5.9(b)). Ação que não é lote tem zero alvos, e
            anunciar "itens afetados: 0" a quem vai reescrever a nuvem inteira seria a tela
            dizendo o contrário do que vai acontecer: aqui, 0 é ausência, não quantidade. */}
        {proposta.quantidade_de_alvos > 0 ? (
          <>
            <dt>{t("proposta.alvos")}</dt>
            <dd>{proposta.quantidade_de_alvos}</dd>
          </>
        ) : null}
        <dt>{t("proposta.vence_em")}</dt>
        <dd>{instante(proposta.vence_em)}</dd>
      </dl>

      {proposta.alvos.length && esperando ? (
        <ul className="alvos-da-proposta">
          {proposta.alvos.map((alvo, indice) => (
            <li key={`${alvo}-${indice}`}>{alvo}</li>
          ))}
        </ul>
      ) : null}

      {esperando ? (
        <>
          <p className="aviso-de-proposta">{t("proposta.gate")}</p>
          <div className="decisao">
            {/* Mesma classe nos dois: peso visual igual é requisito, não estética. */}
            <button
              type="button"
              className="botao-de-decisao"
              disabled={ocupada}
              onClick={() => {
                if (!ocupada) aoConfirmar();
              }}
            >
              {t("proposta.confirmar")}
            </button>
            <button
              type="button"
              className="botao-de-decisao"
              disabled={ocupada}
              onClick={() => {
                if (!ocupada) aoRecusar();
              }}
            >
              {t("proposta.recusar")}
            </button>
          </div>
          {ocupada ? <p className="decidindo">{t("proposta.decidindo")}</p> : null}
        </>
      ) : (
        <>
          {/* RI-04: o desfecho é visível SEMPRE — recusa silenciosa é defeito. */}
          <p role="status" aria-live="polite" className={`desfecho desfecho-${proposta.status}`}>
            {tc("desfecho", String(proposta.status), String(proposta.status))}
            {proposta.mensagem ? ` ${proposta.mensagem}` : ""}
          </p>
          {proposta.outcomes.length ? (
            <ul className="desfecho-por-alvo">
              {proposta.outcomes.map((desfecho, indice) => (
                <li key={`${desfecho.target}-${indice}`}>
                  <strong>{desfecho.target}</strong>{" "}
                  {tc("desfecho", desfecho.status, desfecho.status)}
                  {desfecho.message ? ` — ${desfecho.message}` : ""}
                </li>
              ))}
            </ul>
          ) : null}
          <button type="button" onClick={aoFechar}>
            {t("proposta.fechar")}
          </button>
        </>
      )}
    </section>
  );
}
