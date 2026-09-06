/**
 * A jornada dos cinco passos de focalização — o módulo que dá à aplicação o nome da teoria.
 *
 * Siglas, uma vez: **TOC** — Teoria das Restrições · **ARA** — Árvore da Realidade Atual ·
 * **NC** — Nuvem de Conflito · **ARF** — Árvore da Realidade Futura · **APR** — Árvore de
 * Pré-Requisitos · **AT** — Árvore de Transição · **RI/RF/RN** — requisito de interface /
 * funcional / regra de negócio.
 *
 * Esta é a tela que costura o resto: até aqui a aplicação sabia desenhar seis ferramentas e
 * não sabia dizer **qual é a restrição** nem **em que passo o grupo está**. É por isso que
 * a superfície dela não é um canvas: é uma trilha (RI-01), um painel de três camadas
 * (RI-02), um julgamento de herança (RI-05) e uma linha do tempo (RI-04).
 *
 * Três decisões desta tela:
 *
 * 1. **Nada é recalculado aqui.** Pendência, aviso de vínculo não-canônico, estado de
 *    projeto vinculado e "o que este passo herda" chegam prontos do servidor, computados
 *    por função pura de domínio (RF-12). Uma segunda conta na tela seria uma segunda
 *    verdade, e as duas divergiriam no primeiro requisito novo.
 * 2. **Nenhum botão é escondido por regra de negócio.** Concluir um passo bloqueado
 *    continua clicável, e a recusa volta com a regra nomeada. Esconder ensinaria a pessoa
 *    a não ver a regra; mostrar a recusa ensina a regra.
 * 3. **A escolha de passo persiste na sessão**, como a visão da NC: quem conduz um grupo
 *    não quer reescolher a aba a cada recarga. `sessionStorage` embrulhado — armazenamento
 *    indisponível volta ao padrão em vez de derrubar a tela.
 */
import { useCallback, useState } from "react";
import type { Cliente } from "../api/cliente";
import type {
  AnaliseDeFocalizacao,
  FerramentaVinculada,
  TipoDePasso,
  TipoDeRestricao,
  VereditoDeHeranca,
} from "../dominio/tipos";
import { Carregando, EstadoDeErro } from "../componentes/Estados";
import { mensagemDeErro } from "../componentes/mensagemDeErro";
import { JulgamentoDeHeranca } from "../componentes/focalizacao/JulgamentoDeHeranca";
import { LinhaDoTempo } from "../componentes/focalizacao/LinhaDoTempo";
import { PainelDoPasso } from "../componentes/focalizacao/PainelDoPasso";
import { TrilhaDosPassos } from "../componentes/focalizacao/TrilhaDosPassos";
import { useRecurso } from "../estado/useRecurso";
import { useI18n } from "../i18n";

export const CHAVE_DO_PASSO = "toc.focalizacao.passo";

const TIPOS_DE_RESTRICAO: readonly TipoDeRestricao[] = ["fisica", "politica", "de_mercado"];

function lerPassoGuardado(): TipoDePasso | null {
  try {
    const guardado = window.sessionStorage.getItem(CHAVE_DO_PASSO);
    if (
      guardado === "identificar" ||
      guardado === "explorar" ||
      guardado === "subordinar" ||
      guardado === "elevar" ||
      guardado === "recomecar"
    ) {
      return guardado;
    }
  } catch {
    /* sem armazenamento: o passo atual serve */
  }
  return null;
}

function guardarPasso(passo: TipoDePasso): void {
  try {
    window.sessionStorage.setItem(CHAVE_DO_PASSO, passo);
  } catch {
    /* sem armazenamento: seguir sem persistir a escolha */
  }
}

export interface TelaDaFocalizacaoProps {
  cliente: Cliente;
  projetoId: string;
  /** Quem conduz a análise — vem da sessão de embarque; aqui é o autor dos registros. */
  autor: string;
  aoVoltar(): void;
  aoAbrirFerramenta?(destino: { ferramenta: FerramentaVinculada; projetoId: string }): void;
}

export function TelaDaFocalizacao({
  cliente,
  projetoId,
  autor,
  aoVoltar,
  aoAbrirFerramenta,
}: TelaDaFocalizacaoProps) {
  const { t } = useI18n();
  const buscar = useCallback(
    () => cliente.foco.abrir(projetoId),
    [cliente, projetoId],
  );
  const { dado, carregando, erro, recarregar, definir } =
    useRecurso<AnaliseDeFocalizacao>(buscar, [cliente, projetoId]);

  const [passoEscolhido, setPassoEscolhido] = useState<TipoDePasso | null>(lerPassoGuardado);
  const [cicloEmFoco, setCicloEmFoco] = useState<string | null>(null);
  const [falha, setFalha] = useState<unknown>(null);
  const [ocupado, setOcupado] = useState(false);

  // Estado do formulário de restrição (a entidade que dá nome à teoria).
  const [descricao, setDescricao] = useState("");
  const [tipo, setTipo] = useState<TipoDeRestricao>("fisica");
  const [justificativa, setJustificativa] = useState("");

  if (carregando && !dado) return <Carregando />;
  if (erro && !dado) return <EstadoDeErro erro={erro} aoTentarDeNovo={() => void recarregar()} />;
  if (!dado) return null;

  const jornada = dado.jornada;
  const somenteLeitura = jornada.somente_leitura;
  const passoAtual = jornada.passo_atual;
  const selecionado =
    jornada.passos.find((p) => p.tipo === passoEscolhido)?.tipo ?? passoAtual;
  const passo = jornada.passos.find((p) => p.tipo === selecionado) ?? jornada.passos[0];
  const anterior =
    jornada.passos[jornada.passos.findIndex((p) => p.tipo === passoAtual) - 1] ?? null;

  async function agir(operacao: () => Promise<unknown>): Promise<void> {
    setOcupado(true);
    setFalha(null);
    try {
      await operacao();
      definir(await cliente.foco.abrir(projetoId));
    } catch (problema) {
      setFalha(problema);
    } finally {
      setOcupado(false);
    }
  }

  function escolher(novo: TipoDePasso): void {
    setPassoEscolhido(novo);
    guardarPasso(novo);
  }

  return (
    <section className="tela-da-focalizacao">
      <header className="cabecalho-da-analise">
        <button type="button" onClick={aoVoltar}>
          {t("app.voltar")}
        </button>
        <h2>{dado.projeto.nome}</h2>
        <p className="sistema-analisado">
          <strong>{t("foco.sistema")}:</strong> {dado.sistema.nome}
        </p>
        {dado.sistema.descricao ? <p className="sistema-descricao">{dado.sistema.descricao}</p> : null}
        <p className="progresso-do-ciclo" role="status">
          {t("foco.ciclo_de", { n: jornada.ordem, total: jornada.ciclos_no_total })} ·{" "}
          {t("foco.progresso", {
            concluidos: jornada.passos_concluidos,
            total: jornada.passos.length,
          })}
        </p>
      </header>

      {falha ? (
        <p className="estado-de-erro" role="alert">
          {mensagemDeErro(falha, t)}
        </p>
      ) : null}

      <TrilhaDosPassos
        passos={jornada.passos}
        passoAtual={passoAtual}
        selecionado={selecionado}
        aoSelecionar={escolher}
      />

      {/* A restrição do ciclo — a entidade que o round 009 marca "nunca sai". */}
      <section className="restricao-do-ciclo" aria-labelledby="restricao-titulo">
        <h3 id="restricao-titulo">{t("foco.restricao.titulo")}</h3>
        {jornada.restricao ? (
          <div className="restricao-registrada">
            <p className="restricao-descricao">{jornada.restricao.descricao}</p>
            <p className="restricao-tipo">{t(`foco.tipo.${jornada.restricao.tipo}`)}</p>
            <p className="restricao-justificativa">{jornada.restricao.justificativa}</p>
            {jornada.restricao.origem ? (
              <p className="restricao-origem">{t("foco.restricao.origem")}</p>
            ) : null}
            <p className="restricao-aviso">{t("foco.restricao.troca_e_recomeco")}</p>
          </div>
        ) : somenteLeitura ? (
          <p className="vazio">{t("foco.restricao.ausente")}</p>
        ) : (
          <form
            className="forma-de-restricao"
            onSubmit={(evento) => {
              evento.preventDefault();
              if (!descricao.trim() || !justificativa.trim()) return;
              void agir(() =>
                cliente.foco.registrarRestricao(projetoId, {
                  descricao: descricao.trim(),
                  tipo,
                  justificativa: justificativa.trim(),
                  autor,
                }),
              ).then(() => {
                setDescricao("");
                setJustificativa("");
              });
            }}
          >
            <label htmlFor="restricao-descricao">{t("foco.restricao.descricao")}</label>
            <input
              id="restricao-descricao"
              value={descricao}
              placeholder={t("foco.restricao.descricao_placeholder")}
              onChange={(evento) => setDescricao(evento.target.value)}
            />
            <label htmlFor="restricao-tipo">{t("foco.restricao.tipo")}</label>
            <select
              id="restricao-tipo"
              value={tipo}
              onChange={(evento) => setTipo(evento.target.value as TipoDeRestricao)}
            >
              {TIPOS_DE_RESTRICAO.map((valor) => (
                <option key={valor} value={valor}>
                  {t(`foco.tipo.${valor}`)}
                </option>
              ))}
            </select>
            <label htmlFor="restricao-justificativa">{t("foco.restricao.justificativa")}</label>
            <textarea
              id="restricao-justificativa"
              rows={2}
              value={justificativa}
              placeholder={t("foco.restricao.justificativa_placeholder")}
              onChange={(evento) => setJustificativa(evento.target.value)}
            />
            <button type="submit" disabled={ocupado || !descricao.trim() || !justificativa.trim()}>
              {t("foco.restricao.registrar")}
            </button>
          </form>
        )}
      </section>

      {passo ? (
        <PainelDoPasso
          // `key` pelo tipo do passo: trocar de passo REMONTA o painel, e o rascunho de
          // nota, de decisão e de vínculo morre com o passo que o gerou. Sem isto, o
          // seletor de ferramenta continuava na canônica do passo ANTERIOR — e a captura
          // da jornada viva pegou exatamente esse defeito no build real: em `subordinar`,
          // o formulário ainda oferecia a Árvore da Realidade Atual do passo `identificar`
          // e cobrava justificativa por um vínculo que era canônico.
          key={passo.tipo}
          passo={passo}
          restricao={jornada.restricao}
          somenteLeitura={somenteLeitura}
          ehPassoAtual={passo.tipo === passoAtual}
          podeReabrir={
            !somenteLeitura && passo.tipo === passoAtual && anterior?.estado === "concluido"
          }
          aoAnotar={(texto) =>
            void agir(() => cliente.foco.anotar(projetoId, passo.tipo, texto, autor))
          }
          aoConcluir={(decisao) =>
            void agir(() => cliente.foco.concluirPasso(projetoId, passo.tipo, decisao, autor))
          }
          aoReabrir={(motivo) =>
            void agir(() => cliente.foco.reabrirAnterior(projetoId, motivo, autor))
          }
          aoVincular={(dados) =>
            void agir(() =>
              cliente.foco.vincular(projetoId, passo.tipo, {
                ferramenta: dados.ferramenta,
                projeto_id: dados.projeto_id,
                papel: dados.papel,
                justificativa: dados.justificativa,
              }),
            )
          }
          aoRemoverVinculo={(vinculoId) =>
            void agir(() => cliente.foco.removerVinculo(projetoId, passo.tipo, vinculoId))
          }
          aoAbrirVinculo={(destino) =>
            aoAbrirFerramenta?.({
              ferramenta: destino.ferramenta,
              projetoId: destino.projeto_id,
            })
          }
        />
      ) : null}

      <JulgamentoDeHeranca
        heranca={jornada.heranca}
        somenteLeitura={somenteLeitura}
        aoJulgar={(decisaoId, veredito: Exclude<VereditoDeHeranca, "pendente">, motivo) =>
          void agir(() =>
            cliente.foco.julgarHeranca(projetoId, decisaoId, veredito, motivo, autor),
          )
        }
      />

      {/* O quinto passo: o ato dele é o recomeço, não uma decisão de conclusão (RN-07). */}
      {!somenteLeitura && passoAtual === "recomecar" ? (
        <section className="recomeco">
          <h3>{t("foco.recomecar")}</h3>
          <p>{t("foco.recomecar_explicacao")}</p>
          <button
            type="button"
            disabled={ocupado}
            onClick={() => void agir(() => cliente.foco.recomecar(projetoId))}
          >
            {t("foco.recomecar")}
          </button>
        </section>
      ) : null}

      <LinhaDoTempo
        ciclos={dado.linha_do_tempo}
        cicloAberto={cicloEmFoco ?? jornada.ciclo_id}
        aoAbrirCiclo={(cicloId) => {
          setCicloEmFoco(cicloId);
          void agir(async () => {
            const outro = await cliente.foco.jornada(projetoId, cicloId);
            definir({ ...dado, jornada: outro });
          });
        }}
      />
    </section>
  );
}
