/**
 * O painel do passo, em três camadas na mesma superfície (RI-02).
 *
 * Siglas, uma vez: **TOC** — Teoria das Restrições · **ARA** — Árvore da Realidade Atual ·
 * **NC** — Nuvem de Conflito · **ARF** — Árvore da Realidade Futura · **APR** — Árvore de
 * Pré-Requisitos · **AT** — Árvore de Transição · **RI/RF/RN/RNF** — requisito de
 * interface / funcional / regra de negócio / requisito não funcional.
 *
 * As três camadas são as da RI-02, nesta ordem, e a ordem é o argumento:
 *
 * 1. **O herdado** (topo, somente leitura) — a restrição e as decisões dos passos
 *    anteriores do mesmo ciclo. É o RF-13: ninguém decide no vácuo, e a maneira de
 *    garantir isso não é um lembrete, é pôr o produto do passo anterior na frente de quem
 *    vai decidir.
 * 2. **O trabalho do passo** — notas e vínculos de ferramenta. É aqui que a jornada
 *    aponta para o resto da aplicação: o cartão de vínculo leva à ARA, à NC, à APR.
 * 3. **A decisão de conclusão** (rodapé, ação explícita) — porque avançar é ato, nunca
 *    efeito colateral de ter anotado alguma coisa (RN-01).
 *
 * O que este componente **não** faz: decidir se o passo pode concluir. Quem recusa é o
 * domínio, no servidor; a tela mostra a pendência que o mapa computou e deixa o botão
 * disponível — apagar o botão esconderia a regra em vez de ensiná-la, e a recusa que volta
 * traz a regra nomeada.
 */
import { useState } from "react";
import type {
  FerramentaVinculada,
  PassoNaJornada,
  Restricao,
} from "../../dominio/tipos";
import { useI18n } from "../../i18n";

export interface PainelDoPassoProps {
  passo: PassoNaJornada;
  /** Contexto do painel. A restrição é EXIBIDA pela camada herdada, computada pelo
   *  servidor (RF-13); esta prop existe para o painel saber que o ciclo tem alvo. */
  restricao: Restricao | null;
  somenteLeitura: boolean;
  ehPassoAtual: boolean;
  podeReabrir: boolean;
  aoAnotar(texto: string): void;
  aoConcluir(decisao: string): void;
  aoReabrir(justificativa: string): void;
  aoVincular(dados: {
    ferramenta: FerramentaVinculada;
    projeto_id: string;
    papel: string;
    justificativa: string;
  }): void;
  aoRemoverVinculo(vinculoId: string): void;
  aoAbrirVinculo(vinculo: { ferramenta: FerramentaVinculada; projeto_id: string }): void;
}

const FERRAMENTAS: readonly FerramentaVinculada[] = ["ara", "nc", "arf", "apr", "at"];

export function PainelDoPasso({
  passo,
  restricao: _restricao,
  somenteLeitura,
  ehPassoAtual,
  podeReabrir,
  aoAnotar,
  aoConcluir,
  aoReabrir,
  aoVincular,
  aoRemoverVinculo,
  aoAbrirVinculo,
}: PainelDoPassoProps) {
  const { t, tc } = useI18n();
  const [nota, setNota] = useState("");
  const [decisao, setDecisao] = useState("");
  const [justificativaDeReabertura, setJustificativaDeReabertura] = useState("");
  const [ferramenta, setFerramenta] = useState<FerramentaVinculada>(
    passo.canonicas[0] ?? "ara",
  );
  const [alvo, setAlvo] = useState("");
  const [papel, setPapel] = useState("");
  const [motivoDoVinculo, setMotivoDoVinculo] = useState("");

  const foraDoCanonico = !passo.canonicas.includes(ferramenta);
  const editavel = !somenteLeitura;

  return (
    <section className="painel-do-passo" aria-labelledby={`passo-${passo.tipo}`}>
      <header>
        <h3 id={`passo-${passo.tipo}`}>{t(`foco.passo.${passo.tipo}`)}</h3>
        <p className="passo-estado-legenda">{t(`foco.estado.${passo.estado}`)}</p>
        {somenteLeitura ? (
          <p className="aviso-somente-leitura" role="status">
            {t("foco.somente_leitura")}
          </p>
        ) : null}
      </header>

      {/* Camada 1 — o herdado. Somente leitura, sempre no topo (RF-13, US-08). */}
      <section className="camada-herdado" aria-label={t("foco.herdado")}>
        <h4>{t("foco.herdado")}</h4>
        {passo.herdado.length === 0 ? (
          <p className="vazio">{t("foco.herdado_vazio")}</p>
        ) : (
          <ul>
            {passo.herdado.map((linha) => (
              <li key={linha}>{linha}</li>
            ))}
          </ul>
        )}
        {/* A restrição NÃO é repetida aqui: ela já é a primeira linha do `herdado` que o
            servidor computou (RF-13). Um segundo lugar dizendo a mesma coisa no mesmo
            painel é duas fontes para uma frase só — e é sempre a segunda que envelhece. */}
      </section>

      {passo.pendencias.length > 0 ? (
        <ul className="pendencias-do-passo" aria-label={t("foco.pendencias_do_passo")}>
          {passo.pendencias.map((pendencia) => (
            <li key={pendencia.regra} data-regra={pendencia.regra}>
              {/* A regra vem do servidor como código estável (§A.7): traduzimos por
                  código, e o detalhe que ele mesmo mandou é a alternativa — código novo
                  do servidor nunca apaga a informação da tela. */}
              {tc("pendencia_da_focalizacao", pendencia.regra, pendencia.detalhe)}
            </li>
          ))}
        </ul>
      ) : null}

      {/* Camada 2 — o trabalho do passo: notas e vínculos de ferramenta. */}
      <section className="camada-trabalho">
        <h4>{t("foco.notas")}</h4>
        {passo.notas.length === 0 ? null : (
          <ul className="notas-do-passo">
            {passo.notas.map((n) => (
              <li key={n.id}>
                <span className="nota-texto">{n.texto}</span>
                <span className="nota-autor">{n.autor}</span>
              </li>
            ))}
          </ul>
        )}
        {editavel ? (
          <form
            className="forma-de-nota"
            onSubmit={(evento) => {
              evento.preventDefault();
              if (!nota.trim()) return;
              aoAnotar(nota.trim());
              setNota("");
            }}
          >
            <label htmlFor={`nota-${passo.tipo}`}>{t("foco.notas")}</label>
            <textarea
              id={`nota-${passo.tipo}`}
              value={nota}
              rows={2}
              placeholder={t("foco.nota_placeholder")}
              onChange={(evento) => setNota(evento.target.value)}
            />
            <button type="submit" disabled={!nota.trim()}>
              {t("foco.anotar")}
            </button>
          </form>
        ) : null}

        <h4>{t("foco.vinculos")}</h4>
        <p className="canonicas-do-passo">
          {passo.canonicas.length
            ? t("foco.vinculo_canonicas", {
                lista: passo.canonicas.map((f) => tc("ferramenta", f, f)).join(", "),
              })
            : t("foco.vinculo_nenhuma_canonica")}
        </p>
        {passo.vinculos.length === 0 ? (
          <p className="vazio">{t("foco.vinculos_vazio")}</p>
        ) : (
          <ul className="cartoes-de-vinculo">
            {passo.vinculos.map((vinculo) => (
              <li key={vinculo.id} data-estado={vinculo.estado} data-canonico={vinculo.canonico}>
                <span className="vinculo-ferramenta">{vinculo.ferramenta.toUpperCase()}</span>
                <span className="vinculo-nome">{vinculo.nome || vinculo.projeto_id}</span>
                <span className="vinculo-estado">
                  {t(`foco.vinculo_estado.${vinculo.estado}`)}
                </span>
                {vinculo.papel ? <span className="vinculo-papel">{vinculo.papel}</span> : null}
                {vinculo.estado !== "ativo" ? (
                  <span className="vinculo-legenda" role="status">
                    {vinculo.legenda}
                  </span>
                ) : null}
                <button
                  type="button"
                  onClick={() =>
                    aoAbrirVinculo({
                      ferramenta: vinculo.ferramenta,
                      projeto_id: vinculo.projeto_id,
                    })
                  }
                  disabled={vinculo.estado === "ausente"}
                >
                  {t("foco.abrir")}
                </button>
                {editavel ? (
                  <button type="button" onClick={() => aoRemoverVinculo(vinculo.id)}>
                    {t("foco.vinculo_remover")}
                  </button>
                ) : null}
              </li>
            ))}
          </ul>
        )}
        {passo.avisos.length > 0 ? (
          <ul className="avisos-do-passo" role="status">
            {passo.avisos.map((aviso) => (
              <li key={aviso}>{aviso}</li>
            ))}
          </ul>
        ) : null}

        {editavel ? (
          <form
            className="forma-de-vinculo"
            onSubmit={(evento) => {
              evento.preventDefault();
              if (!alvo.trim()) return;
              aoVincular({
                ferramenta,
                projeto_id: alvo.trim(),
                papel: papel.trim(),
                justificativa: motivoDoVinculo.trim(),
              });
              setAlvo("");
              setPapel("");
              setMotivoDoVinculo("");
            }}
          >
            <label htmlFor={`vinculo-ferramenta-${passo.tipo}`}>{t("foco.vincular")}</label>
            {/* RI-03: as canônicas do passo vêm primeiro; o caminho não-canônico existe,
                visível, e cobra a justificativa que a RN-06 exige. */}
            <select
              id={`vinculo-ferramenta-${passo.tipo}`}
              value={ferramenta}
              onChange={(evento) => setFerramenta(evento.target.value as FerramentaVinculada)}
            >
              <optgroup label={t("foco.vinculo_canonicas", { lista: "" })}>
                {passo.canonicas.map((f) => (
                  <option key={f} value={f}>
                    {tc("ferramenta", f, f.toUpperCase())}
                  </option>
                ))}
              </optgroup>
              <optgroup label={t("foco.vinculo_justificativa")}>
                {FERRAMENTAS.filter((f) => !passo.canonicas.includes(f)).map((f) => (
                  <option key={f} value={f}>
                    {tc("ferramenta", f, f.toUpperCase())}
                  </option>
                ))}
              </optgroup>
            </select>
            <label htmlFor={`vinculo-alvo-${passo.tipo}`}>{t("foco.vinculo_projeto")}</label>
            <input
              id={`vinculo-alvo-${passo.tipo}`}
              value={alvo}
              onChange={(evento) => setAlvo(evento.target.value)}
            />
            <label htmlFor={`vinculo-papel-${passo.tipo}`}>{t("foco.vinculo_papel")}</label>
            <input
              id={`vinculo-papel-${passo.tipo}`}
              value={papel}
              onChange={(evento) => setPapel(evento.target.value)}
            />
            {foraDoCanonico ? (
              <>
                <label htmlFor={`vinculo-motivo-${passo.tipo}`}>
                  {t("foco.vinculo_justificativa")}
                </label>
                <textarea
                  id={`vinculo-motivo-${passo.tipo}`}
                  rows={2}
                  value={motivoDoVinculo}
                  onChange={(evento) => setMotivoDoVinculo(evento.target.value)}
                />
              </>
            ) : null}
            <button
              type="submit"
              disabled={!alvo.trim() || (foraDoCanonico && !motivoDoVinculo.trim())}
            >
              {t("foco.vincular")}
            </button>
          </form>
        ) : null}
      </section>

      {/* Camada 3 — a decisão de conclusão. Ação explícita, no rodapé (RI-02, RN-01). */}
      <footer className="camada-decisao">
        {passo.decisoes.length > 0 ? (
          <div className="historico-de-decisoes">
            <p>{t("foco.decisoes_no_historico", { n: passo.decisoes.length })}</p>
            <ul>
              {passo.decisoes.map((d) => (
                <li key={`${d.instante}-${d.texto}`}>
                  <span className="decisao-texto">{d.texto}</span>
                  <span className="decisao-autor">{d.autor}</span>
                </li>
              ))}
            </ul>
          </div>
        ) : null}

        {editavel && ehPassoAtual && passo.tipo !== "recomecar" ? (
          <form
            className="forma-de-decisao"
            onSubmit={(evento) => {
              evento.preventDefault();
              if (!decisao.trim()) return;
              aoConcluir(decisao.trim());
              setDecisao("");
            }}
          >
            <label htmlFor={`decisao-${passo.tipo}`}>{t("foco.decisao")}</label>
            <textarea
              id={`decisao-${passo.tipo}`}
              rows={2}
              value={decisao}
              placeholder={t("foco.decisao_placeholder")}
              onChange={(evento) => setDecisao(evento.target.value)}
            />
            <button type="submit" disabled={!decisao.trim()}>
              {t("foco.concluir")}
            </button>
          </form>
        ) : null}

        {editavel && podeReabrir ? (
          <form
            className="forma-de-reabertura"
            onSubmit={(evento) => {
              evento.preventDefault();
              if (!justificativaDeReabertura.trim()) return;
              aoReabrir(justificativaDeReabertura.trim());
              setJustificativaDeReabertura("");
            }}
          >
            <label htmlFor={`reabrir-${passo.tipo}`}>{t("foco.reabrir_justificativa")}</label>
            <input
              id={`reabrir-${passo.tipo}`}
              value={justificativaDeReabertura}
              onChange={(evento) => setJustificativaDeReabertura(evento.target.value)}
            />
            <button type="submit" disabled={!justificativaDeReabertura.trim()}>
              {t("foco.reabrir")}
            </button>
          </form>
        ) : null}
      </footer>
    </section>
  );
}
