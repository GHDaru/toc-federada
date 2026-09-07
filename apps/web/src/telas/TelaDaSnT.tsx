/**
 * A tela da árvore de Estratégia & Táticas — a ferramenta que a linhagem desligou.
 *
 * Siglas, uma vez: **S&T** — Estratégia & Táticas (*Strategy & Tactics*) · **TOC** —
 * Teoria das Restrições · **RI/RF/RN** — requisito de interface / funcional / regra de
 * negócio da spec 010 · **ADR** — *Architecture Decision Record* (Registro de Decisão
 * Arquitetural).
 *
 * **Esta tela é um resgate, e o resgate está medido.** A S&T é a única ferramenta que
 * REGREDIU na linhagem: `TOC-Builder/components/Sidebar.tsx:44` a declara habilitada na
 * primeira geração, sem `disabled`; `tocbuilderv3/components/Sidebar.tsx:58` a declara
 * `disabled: true` na quarta, com o modelo de dados inteiro parado no código. O que entra
 * aqui desfaz a regressão — com a decisão registrada, que é o que faltou lá.
 *
 * Quatro decisões desta superfície:
 *
 * 1. **Nada é recalculado aqui.** Numeração, pendências, contagens por status e as
 *    leituras dirigidas das premissas chegam prontas do servidor, de função pura de
 *    domínio. Uma segunda conta na tela seria uma segunda verdade — e o defeito da
 *    linhagem era exatamente ter duas (o número digitado e a estrutura das arestas).
 * 2. **Mover pré-visualiza, excluir conta antes** (RI-05, RI-06). As duas mutações
 *    estruturais perguntam ao servidor o que aconteceria, mostram, e só então confirmam.
 *    A alternativa — fazer e desfazer — grava um fato que ninguém pediu.
 * 3. **Nenhum campo de número, em formulário nenhum** (RF-06). Adicionar é ação
 *    contextual do nó ("adicionar filho", "adicionar irmão abaixo").
 * 4. **Nenhum botão é escondido por regra de negócio.** Mover para dentro da própria
 *    subárvore continua clicável, e a recusa volta com a regra nomeada. Esconder ensina a
 *    pessoa a não ver a regra; mostrar a recusa ensina a regra.
 */
import { useCallback, useState } from "react";
import type { Cliente } from "../api/cliente";
import type {
  AcompanhamentoDaSnT,
  CategoriaDoPasso,
  FichaDoPassoSnT,
  PapelDaPremissa,
  PreviaDeExclusao,
  PreviaDeMover,
  SnT,
  StatusDoPassoSnT,
  TabelaDaSnT as TabelaDaSnTDado,
} from "../dominio/tipos";
import { Carregando, EstadoDeErro } from "../componentes/Estados";
import { mensagemDeErro } from "../componentes/mensagemDeErro";
import { ArvoreDeSnT } from "../componentes/snt/ArvoreDeSnT";
import { FichaDoPasso } from "../componentes/snt/FichaDoPasso";
import { PainelDeAcompanhamento } from "../componentes/snt/PainelDeAcompanhamento";
import { TabelaDaSnT } from "../componentes/snt/TabelaDaSnT";
import { useRecurso } from "../estado/useRecurso";
import { useI18n } from "../i18n";

export const CHAVE_DA_VISTA = "toc.snt.vista";

type Vista = "arvore" | "tabela";

interface Rascunho {
  pai_id: string | null;
  posicao: number | null;
}

function lerVistaGuardada(): Vista {
  try {
    const guardada = window.sessionStorage.getItem(CHAVE_DA_VISTA);
    if (guardada === "arvore" || guardada === "tabela") return guardada;
  } catch {
    /* sem armazenamento: a árvore é o padrão */
  }
  return "arvore";
}

function guardarVista(vista: Vista): void {
  try {
    window.sessionStorage.setItem(CHAVE_DA_VISTA, vista);
  } catch {
    /* sem armazenamento: seguir sem persistir a escolha */
  }
}

export interface TelaDaSnTProps {
  cliente: Cliente;
  projetoId: string;
  aoVoltar(): void;
}

export function TelaDaSnT({ cliente, projetoId, aoVoltar }: TelaDaSnTProps) {
  const { t } = useI18n();
  const buscar = useCallback(() => cliente.snt.abrir(projetoId), [cliente, projetoId]);
  const { dado, carregando, erro, recarregar, definir } = useRecurso<SnT>(buscar, [
    cliente,
    projetoId,
  ]);

  const [vista, setVista] = useState<Vista>(lerVistaGuardada);
  const [selecionado, setSelecionado] = useState<string | null>(null);
  const [ficha, setFicha] = useState<FichaDoPassoSnT | null>(null);
  const [acompanhamento, setAcompanhamento] = useState<AcompanhamentoDaSnT | null>(null);
  const [tabela, setTabela] = useState<TabelaDaSnTDado | null>(null);
  const [filtro, setFiltro] = useState<StatusDoPassoSnT | null>(null);
  const [rascunho, setRascunho] = useState<Rascunho | null>(null);
  const [estrategiaNova, setEstrategiaNova] = useState("");
  const [previaDeMover, setPreviaDeMover] = useState<PreviaDeMover | null>(null);
  const [destinoDoMover, setDestinoDoMover] = useState<string | null>(null);
  const [previaDeExclusao, setPreviaDeExclusao] = useState<PreviaDeExclusao | null>(null);
  const [falha, setFalha] = useState<unknown>(null);
  const [ocupado, setOcupado] = useState(false);

  if (carregando && !dado) return <Carregando />;
  if (erro && !dado) return <EstadoDeErro erro={erro} aoTentarDeNovo={() => void recarregar()} />;
  if (!dado) return null;

  const arvore = dado;

  async function recarregarTudo(noEmFoco: string | null): Promise<void> {
    const atual = await cliente.snt.abrir(projetoId);
    definir(atual);
    setAcompanhamento(await cliente.snt.acompanhamento(projetoId));
    if (vista === "tabela") setTabela(await cliente.snt.tabela(projetoId));
    const alvo = noEmFoco && atual.passos.some((p) => p.id === noEmFoco) ? noEmFoco : null;
    setSelecionado(alvo);
    setFicha(alvo ? await cliente.snt.abrirPasso(projetoId, alvo) : null);
  }

  async function agir(operacao: () => Promise<unknown>, noEmFoco = selecionado): Promise<void> {
    setOcupado(true);
    setFalha(null);
    try {
      await operacao();
      await recarregarTudo(noEmFoco);
    } catch (problema) {
      setFalha(problema);
    } finally {
      setOcupado(false);
    }
  }

  function selecionar(noId: string): void {
    setSelecionado(noId);
    setPreviaDeMover(null);
    setPreviaDeExclusao(null);
    void (async () => {
      try {
        setFicha(await cliente.snt.abrirPasso(projetoId, noId));
      } catch (problema) {
        setFalha(problema);
      }
    })();
  }

  function trocarVista(nova: Vista): void {
    setVista(nova);
    guardarVista(nova);
    if (nova === "tabela") {
      void (async () => {
        try {
          setTabela(await cliente.snt.tabela(projetoId));
        } catch (problema) {
          setFalha(problema);
        }
      })();
    }
  }

  function abrirAcompanhamento(): void {
    void (async () => {
      try {
        setAcompanhamento(await cliente.snt.acompanhamento(projetoId));
      } catch (problema) {
        setFalha(problema);
      }
    })();
  }

  // RF-18: o filtro por status manda para a árvore **só os passos que casam**. Quem
  // mantém os ancestrais em tela — apagados, como contexto — é a própria árvore: é ela
  // que conhece a hierarquia, e é lá que a regra "sem o ancestral o passo aparece sem o
  // plano que o explica" fica num lugar só.
  const visiveis = filtro
    ? arvore.passos.filter((passo) => passo.status === filtro).map((passo) => passo.id)
    : null;

  return (
    <section className="tela-da-snt">
      <header className="cabecalho-da-snt">
        <button type="button" onClick={aoVoltar}>
          {t("app.voltar")}
        </button>
        <h2>{arvore.nome}</h2>
        <p className="contagem-de-passos" role="status">
          {t("snt.passos_na_arvore", { n: arvore.passos.length })}
        </p>
        <nav className="vistas-da-snt" aria-label={t("snt.vistas")}>
          <button type="button" aria-pressed={vista === "arvore"} onClick={() => trocarVista("arvore")}>
            {t("snt.vista_arvore")}
          </button>
          <button type="button" aria-pressed={vista === "tabela"} onClick={() => trocarVista("tabela")}>
            {t("snt.vista_tabela")}
          </button>
          <button type="button" onClick={abrirAcompanhamento}>
            {t("snt.acompanhamento")}
          </button>
        </nav>
      </header>

      {falha ? (
        <p className="estado-de-erro" role="alert">
          {mensagemDeErro(falha, t)}
        </p>
      ) : null}

      {vista === "arvore" ? (
        <ArvoreDeSnT
          metaGlobal={arvore.meta_global}
          passos={arvore.passos}
          raizes={arvore.raizes}
          selecionado={selecionado}
          visiveis={visiveis}
          aoSelecionar={selecionar}
          aoAdicionarRaiz={() => setRascunho({ pai_id: null, posicao: null })}
          aoAdicionarFilho={(noId) => setRascunho({ pai_id: noId, posicao: null })}
          aoAdicionarIrmao={(noId) => {
            const alvo = arvore.passos.find((p) => p.id === noId);
            const irmaos = alvo?.pai_id
              ? arvore.passos.find((p) => p.id === alvo.pai_id)?.filhos ?? []
              : arvore.raizes;
            setRascunho({
              pai_id: alvo?.pai_id ?? null,
              posicao: irmaos.indexOf(noId) + 1,
            });
          }}
        />
      ) : (
        <TabelaDaSnT
          linhas={tabela?.linhas ?? []}
          selecionado={selecionado}
          aoSelecionar={selecionar}
        />
      )}

      {/* RI-04: adicionar é ação contextual — e o formulário NÃO tem campo de número. */}
      {rascunho ? (
        <form
          className="forma-de-passo"
          aria-label={t("snt.novo_passo")}
          onSubmit={(evento) => {
            evento.preventDefault();
            if (!estrategiaNova.trim()) return;
            void agir(async () => {
              const novo = await cliente.snt.adicionarPasso(projetoId, {
                estrategia: estrategiaNova.trim(),
                pai_id: rascunho.pai_id,
                posicao: rascunho.posicao,
              });
              setEstrategiaNova("");
              setRascunho(null);
              return novo;
            });
          }}
        >
          <label htmlFor="nova-estrategia">{t("snt.estrategia")}</label>
          <input
            id="nova-estrategia"
            value={estrategiaNova}
            placeholder={t("snt.estrategia_placeholder")}
            onChange={(evento) => setEstrategiaNova(evento.target.value)}
          />
          <button type="submit" disabled={ocupado || !estrategiaNova.trim()}>
            {t("snt.adicionar")}
          </button>
          <button type="button" onClick={() => setRascunho(null)}>
            {t("app.cancelar")}
          </button>
        </form>
      ) : null}

      {ficha ? (
        <FichaDoPasso
          key={ficha.id}
          ficha={ficha}
          ocupado={ocupado}
          aoEditar={(campos: {
            estrategia?: string;
            tatica?: string;
            categoria?: CategoriaDoPasso;
          }) => void agir(() => cliente.snt.editarPasso(projetoId, ficha.id, campos), ficha.id)}
          aoEditarPremissa={(papel: PapelDaPremissa, texto: string) =>
            void agir(
              () => cliente.snt.editarPremissas(projetoId, ficha.id, { [papel]: texto }),
              ficha.id,
            )
          }
          aoMudarStatus={(status: StatusDoPassoSnT) =>
            void agir(() => cliente.snt.mudarStatus(projetoId, ficha.id, status), ficha.id)
          }
          aoAdicionarFilho={() => setRascunho({ pai_id: ficha.id, posicao: null })}
          aoMover={() => {
            setPreviaDeExclusao(null);
            void (async () => {
              try {
                setPreviaDeMover(
                  await cliente.snt.previaDeMover(projetoId, {
                    no_id: ficha.id,
                    novo_pai_id: destinoDoMover,
                  }),
                );
              } catch (problema) {
                setFalha(problema);
              }
            })();
          }}
          aoExcluir={() => {
            setPreviaDeMover(null);
            void (async () => {
              try {
                setPreviaDeExclusao(await cliente.snt.previaDeExclusao(projetoId, ficha.id));
              } catch (problema) {
                setFalha(problema);
              }
            })();
          }}
        />
      ) : null}

      {/* RI-05: mover mostra a renumeração ANTES de confirmar. */}
      {ficha && previaDeMover ? (
        <section className="previa-de-mover" aria-labelledby="previa-mover-titulo">
          <h4 id="previa-mover-titulo">{t("snt.previa_de_mover")}</h4>
          <label htmlFor="destino-do-mover">{t("snt.novo_pai")}</label>
          <select
            id="destino-do-mover"
            value={destinoDoMover ?? ""}
            onChange={(evento) => {
              const escolhido = evento.target.value || null;
              setDestinoDoMover(escolhido);
              void (async () => {
                try {
                  setPreviaDeMover(
                    await cliente.snt.previaDeMover(projetoId, {
                      no_id: ficha.id,
                      novo_pai_id: escolhido,
                    }),
                  );
                } catch (problema) {
                  setFalha(problema);
                }
              })();
            }}
          >
            <option value="">{t("snt.como_raiz")}</option>
            {arvore.passos
              .filter((p) => p.id !== ficha.id)
              .map((p) => (
                <option key={p.id} value={p.id}>
                  {p.numero} · {p.estrategia}
                </option>
              ))}
          </select>
          <ul className="mudancas-de-numero">
            {previaDeMover.mudancas.map((mudanca) => (
              <li key={mudanca.no_id}>
                {t("snt.mudanca_de_numero", {
                  de: mudanca.numero_atual,
                  para: mudanca.numero_novo,
                })}
              </li>
            ))}
          </ul>
          <button
            type="button"
            disabled={ocupado}
            onClick={() =>
              void agir(async () => {
                const resultado = await cliente.snt.mover(projetoId, ficha.id, {
                  novo_pai_id: destinoDoMover,
                });
                setPreviaDeMover(null);
                return resultado;
              }, ficha.id)
            }
          >
            {t("snt.confirmar_mover")}
          </button>
          <button type="button" onClick={() => setPreviaDeMover(null)}>
            {t("app.cancelar")}
          </button>
        </section>
      ) : null}

      {/* RI-06: a confirmação mostra a contagem e o primeiro nível do que cai. */}
      {ficha && previaDeExclusao ? (
        <section className="previa-de-exclusao" role="alertdialog" aria-labelledby="previa-exclusao-titulo">
          <h4 id="previa-exclusao-titulo">
            {t("snt.serao_excluidos", { n: previaDeExclusao.passos })}
          </h4>
          <ul className="primeiro-nivel">
            {previaDeExclusao.primeiro_nivel.map((filho) => (
              <li key={filho.id}>
                {filho.numero} · {filho.estrategia}
              </li>
            ))}
          </ul>
          <p className="aviso-de-desfazer">{t("snt.exclusao_reversivel")}</p>
          <button
            type="button"
            className="perigo"
            disabled={ocupado}
            onClick={() =>
              void agir(async () => {
                const resultado = await cliente.snt.excluirSubarvore(projetoId, ficha.id);
                setPreviaDeExclusao(null);
                return resultado;
              }, null)
            }
          >
            {t("snt.confirmar_exclusao")}
          </button>
          <button type="button" onClick={() => setPreviaDeExclusao(null)}>
            {t("app.cancelar")}
          </button>
        </section>
      ) : null}

      {acompanhamento ? (
        <PainelDeAcompanhamento
          acompanhamento={acompanhamento}
          filtro={filtro}
          aoFiltrar={setFiltro}
          aoSaltar={(noId) => {
            trocarVista("arvore");
            selecionar(noId);
          }}
        />
      ) : null}
    </section>
  );
}
