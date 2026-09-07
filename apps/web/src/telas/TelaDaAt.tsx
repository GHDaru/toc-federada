/**
 * A Árvore de Transição (AT) — os passos entre hoje e o objetivo intermediário.
 *
 * Siglas, uma vez: **AT** — Árvore de Transição · **APR** — Árvore de Pré-Requisitos ·
 * **API** — interface de programação de aplicações · **RF/RN** — requisito funcional /
 * regra de negócio.
 *
 * A AT fecha o percurso: a Árvore de Pré-Requisitos diz **o que** precisa existir, e a de
 * Transição diz **como se chega lá**, passo a passo. Cada passo carrega a tripla
 * obrigatória — necessidade, ação, resultado esperado (RN-10) —, e é essa tripla que
 * separa um plano de uma lista de tarefas.
 *
 * O formulário desta tela é o único da aplicação que **não arma sem três campos**, e isso
 * é deliberado: o domínio recusa a ficha incompleta antes de criar nó nenhum, e um
 * formulário que deixasse enviar dois de três geraria uma recusa que a pessoa já podia ter
 * evitado. A recusa continua lá, para quem chegar pela interface de programação.
 */
import { useCallback, useState } from "react";
import type { At, StatusDoPasso } from "../dominio/tipos";
import type { Cliente } from "../api/cliente";
import { Carregando, EstadoDeErro } from "../componentes/Estados";
import { mensagemDeErro } from "../componentes/mensagemDeErro";
import { PassosDaAt } from "../componentes/at/PassosDaAt";
import { useRecurso } from "../estado/useRecurso";
import { useI18n } from "../i18n";

export interface TelaDaAtProps {
  cliente: Cliente;
  projetoId: string;
  aoVoltar(): void;
  /** RF-42: a travessia se abre de DENTRO da ferramenta — ela é de uma análise. */
  aoAbrirCadeia?(projetoId: string): void;
}

export function TelaDaAt({ cliente, projetoId, aoVoltar, aoAbrirCadeia }: TelaDaAtProps) {
  const { t, tc } = useI18n();
  const buscar = useCallback(() => cliente.at.abrir(projetoId), [cliente, projetoId]);
  const { dado, carregando, erro, recarregar } = useRecurso<At>(buscar, [cliente, projetoId]);

  const [necessidade, setNecessidade] = useState("");
  const [acao, setAcao] = useState("");
  const [resultado, setResultado] = useState("");
  const [antes, setAntes] = useState("");
  const [depois, setDepois] = useState("");
  const [erroDeAcao, setErroDeAcao] = useState<unknown>(null);
  const [ocupado, setOcupado] = useState(false);

  const escrever = useCallback(
    async (acaoAsync: () => Promise<unknown>) => {
      setErroDeAcao(null);
      setOcupado(true);
      try {
        await acaoAsync();
        await recarregar();
      } catch (falha) {
        setErroDeAcao(falha);
      } finally {
        setOcupado(false);
      }
    },
    [recarregar],
  );

  if (carregando && !dado) return <Carregando />;
  if (erro && !dado) return <EstadoDeErro erro={erro} aoTentarDeNovo={() => void recarregar()} />;
  if (!dado) return null;

  const at = dado;
  const tripla = necessidade.trim() && acao.trim() && resultado.trim();
  const concluidos = at.resumo.concluido ?? 0;
  const total = at.resumo.passos ?? at.passos.length;
  const bloqueados = at.resumo.bloqueado ?? 0;

  return (
    <section className="tela tela-da-at" aria-label={t("at.titulo")}>
      <div className="cabecalho-do-projeto">
        <button type="button" onClick={aoVoltar}>
          {t("app.voltar")}
        </button>
        <h1>{at.nome}</h1>
        {aoAbrirCadeia ? (
          <button type="button" onClick={() => aoAbrirCadeia(at.id)}>
            {t("navegacao.cadeia")}
          </button>
        ) : null}
        {at.alvo ? (
          <p className="origem">
            {t("at.alvo")} {tc("ferramenta", at.alvo.ferramenta)}
          </p>
        ) : null}
        <p className="progresso" role="status">
          {t("at.progresso", { concluidos, total })}
        </p>
        {bloqueados > 0 ? (
          <p className="bloqueados">{t("at.bloqueados", { n: bloqueados })}</p>
        ) : null}
      </div>

      {erroDeAcao ? (
        <p role="alert" className="erro">
          {mensagemDeErro(erroDeAcao, t)}
        </p>
      ) : null}

      <form
        className="linha-de-criacao forma-do-passo"
        onSubmit={(evento) => {
          evento.preventDefault();
          if (!tripla) return;
          void escrever(async () => {
            await cliente.at.registrarPasso(projetoId, {
              necessidade: necessidade.trim(),
              acao: acao.trim(),
              resultado_esperado: resultado.trim(),
            });
            setNecessidade("");
            setAcao("");
            setResultado("");
          });
        }}
      >
        <label htmlFor="necessidade-do-passo">{t("at.necessidade")}</label>
        <input
          id="necessidade-do-passo"
          value={necessidade}
          onChange={(evento) => setNecessidade(evento.target.value)}
        />
        <label htmlFor="acao-do-passo">{t("at.acao")}</label>
        <input id="acao-do-passo" value={acao} onChange={(evento) => setAcao(evento.target.value)} />
        <label htmlFor="resultado-do-passo">{t("at.resultado_esperado")}</label>
        <input
          id="resultado-do-passo"
          value={resultado}
          onChange={(evento) => setResultado(evento.target.value)}
        />
        <button type="submit" disabled={ocupado || !tripla}>
          {t("at.registrar")}
        </button>
      </form>

      <PassosDaAt
        passos={at.passos}
        ordem={at.ordem_de_leitura}
        inalcancaveis={at.inalcancaveis}
        ocupado={ocupado}
        aoMudarStatus={(passoId, dados: { status: StatusDoPasso; motivo: string; resultado_real: string }) =>
          void escrever(() => cliente.at.mudarStatus(projetoId, passoId, dados))
        }
        aoExcluir={(passoId) => void escrever(() => cliente.at.excluirPasso(projetoId, passoId))}
      />

      {/* A precedência é o que dá ORDEM ao plano; sem ela a árvore é um monte de passos. */}
      <form
        className="linha-de-precedencia"
        onSubmit={(evento) => {
          evento.preventDefault();
          if (!antes || !depois) return;
          void escrever(async () => {
            await cliente.at.preceder(projetoId, antes, depois);
            setAntes("");
            setDepois("");
          });
        }}
      >
        <label htmlFor="passo-antes">{t("at.antes")}</label>
        <select id="passo-antes" value={antes} onChange={(evento) => setAntes(evento.target.value)}>
          <option value="">—</option>
          {at.passos.map((passo) => (
            <option key={passo.id} value={passo.id}>
              {passo.acao}
            </option>
          ))}
        </select>
        <label htmlFor="passo-depois">{t("at.depois")}</label>
        <select
          id="passo-depois"
          value={depois}
          onChange={(evento) => setDepois(evento.target.value)}
        >
          <option value="">—</option>
          {at.passos.map((passo) => (
            <option key={passo.id} value={passo.id}>
              {passo.acao}
            </option>
          ))}
        </select>
        <button type="submit" disabled={ocupado || !antes || !depois}>
          {t("at.preceder")}
        </button>
      </form>
    </section>
  );
}
