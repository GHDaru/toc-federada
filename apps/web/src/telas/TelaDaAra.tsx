/**
 * A Árvore da Realidade Atual (ARA) — a ferramenta mais madura da linhagem, agora com
 * persistência real, regra de domínio no servidor e teste em cada fluxo.
 *
 * Siglas, uma vez: **ARA** — Árvore da Realidade Atual · **UDE** — Efeito Indesejável ·
 * **RI/RF/RN** — requisito de interface / funcional / regra de negócio · **API** —
 * interface de programação de aplicações.
 *
 * Três decisões desta tela, todas com regra por trás:
 *
 * 1. **Editar o título de um UDE é REFORMULAR** (RF-10 da spec 005): o comando reexecuta a
 *    validação formal. Um `PATCH` de título silencioso deixaria o veredito velho ao lado
 *    do texto novo — que é a forma mais barata de a ficha mentir.
 * 2. **Cada escrita registra o seu inverso na pilha de desfazer**, com o nome do episódio
 *    (RI-06 da spec 004). O inverso é um comando do servidor, não um retrocesso local.
 * 3. **Exclusão não entra na pilha**: o serviço não sabe ressuscitar nó nem aresta. Em vez
 *    de prometer volta, a exclusão declara o raio antes (RI-05).
 */
import { useCallback, useEffect, useMemo, useState } from "react";
import type { Cliente } from "../api/cliente";
import type { Ara, EstadoDoExame, No, Posicao, StatusDeValidacao } from "../dominio/tipos";
import { Canvas } from "../componentes/canvas/Canvas";
import { PainelDoNo } from "../componentes/canvas/PainelDoNo";
import { PainelDeEntidades } from "../componentes/PainelDeEntidades";
import { Carregando, EstadoDeErro } from "../componentes/Estados";
import { mensagemDeErro } from "../componentes/mensagemDeErro";
import { ExameDeElo } from "../componentes/ude/ExameDeElo";
import { FichaDeUde } from "../componentes/ude/FichaDeUde";
import { RelatorioEstrutural } from "../componentes/ude/RelatorioEstrutural";
import { SeloDeUde } from "../componentes/ude/SeloDeUde";
import { useDesfazer } from "../estado/useDesfazer";
import { useRecurso } from "../estado/useRecurso";
import { useI18n } from "../i18n";
import type { RelatorioEstrutural as Relatorio } from "../dominio/tipos";

const STATUS: readonly StatusDeValidacao[] = ["pendente", "requer_refinamento", "validado", "rejeitado"];

export interface TelaDaAraProps {
  cliente: Cliente;
  projetoId: string;
  aoVoltar(): void;
  /** INT-05: derivar a Nuvem de Conflito leva para ela — o encadeamento das ferramentas. */
  aoAbrirNuvem?(projetoId: string): void;
}

export function TelaDaAra({ cliente, projetoId, aoVoltar, aoAbrirNuvem }: TelaDaAraProps) {
  const { t, tc } = useI18n();
  const buscar = useCallback(() => cliente.ara.abrir(projetoId), [cliente, projetoId]);
  const { dado, carregando, erro, recarregar } = useRecurso<Ara>(buscar, [cliente, projetoId]);
  const desfazer = useDesfazer();

  const [selecionado, setSelecionado] = useState<string | null>(null);
  const [foco, setFoco] = useState<string | null>(null);
  const [examinando, setExaminando] = useState<string | null>(null);
  const [relatorio, setRelatorio] = useState<Relatorio | null>(null);
  const [filtro, setFiltro] = useState<StatusDeValidacao | null>(null);
  const [erroDeAcao, setErroDeAcao] = useState<unknown>(null);
  //: Os UDEs escolhidos para virar o dilema da nuvem (INT-05) e as arestas escolhidas
  //: para formar um conector E (RN-11). Duas seleções, dois propósitos, nenhuma delas é
  //: "o nó selecionado" — que é outra coisa e continua sendo um só.
  const [paraDerivar, setParaDerivar] = useState<string[]>([]);
  const [paraConector, setParaConector] = useState<string[]>([]);
  //: O nó cujo painel lateral está aberto (RI-04: descrição em painel, nunca em modal).
  const [detalhando, setDetalhando] = useState<string | null>(null);

  const nos = dado?.projeto.nos ?? [];
  const arestas = dado?.projeto.arestas ?? [];
  const udePorNo = useMemo(() => new Map((dado?.udes ?? []).map((ude) => [ude.no_id, ude])), [dado]);
  const eloPorAresta = useMemo(() => new Map((dado?.elos ?? []).map((elo) => [elo.aresta_id, elo])), [dado]);
  const udeSelecionado = selecionado ? udePorNo.get(selecionado) : undefined;

  useEffect(() => {
    desfazer.limpar();
    // Trocar de projeto zera a pilha: desfazer não atravessa contexto.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [projetoId]);

  /** Roda uma escrita, recarrega o agregado e desenha a recusa sem derrubar a tela. */
  const escrever = useCallback(
    async (acao: () => Promise<void>) => {
      setErroDeAcao(null);
      try {
        await acao();
        await recarregar();
      } catch (falha) {
        setErroDeAcao(falha);
      }
    },
    [recarregar],
  );

  async function criarNo(posicao: Posicao) {
    await escrever(async () => {
      // O tipo `efeito` é decisão do SERVIDOR (F-15 da spec 005): todo nó da ARA é um
      // efeito, e "causa" é posição na cadeia, não tipo de nó.
      const criado = await cliente.ara.adicionarEfeito(projetoId, {
        titulo: t("canvas.novo_no_titulo"),
        posicao,
      });
      desfazer.registrar("criar_no", async () => {
        await cliente.ara.excluirNo(projetoId, criado.id);
        await recarregar();
      });
    });
  }

  async function moverNo(id: string, posicao: Posicao) {
    const anterior = nos.find((no) => no.id === id)?.posicao;
    await escrever(async () => {
      await cliente.ara.moverNo(projetoId, id, posicao);
      if (anterior) {
        desfazer.registrar("mover_no", async () => {
          await cliente.ara.moverNo(projetoId, id, anterior);
          await recarregar();
        });
      }
    });
  }

  async function editarTitulo(id: string, titulo: string) {
    const anterior = nos.find((no) => no.id === id);
    const eUde = udePorNo.has(id);
    await escrever(async () => {
      if (eUde) await cliente.ara.reformular(projetoId, id, titulo);
      else await cliente.ara.editarNo(projetoId, id, { titulo });
      if (anterior) {
        desfazer.registrar("editar_no", async () => {
          if (eUde) await cliente.ara.reformular(projetoId, id, anterior.titulo);
          else await cliente.ara.editarNo(projetoId, id, { titulo: anterior.titulo });
          await recarregar();
        });
      }
    });
  }

  async function ligar(origemId: string, destinoId: string) {
    await escrever(async () => {
      const aresta = await cliente.ara.ligar(projetoId, origemId, destinoId);
      desfazer.registrar("ligar", async () => {
        await cliente.ara.excluirAresta(projetoId, aresta.id);
        await recarregar();
      });
    });
  }

  function alternar(lista: string[], id: string): string[] {
    return lista.includes(id) ? lista.filter((outro) => outro !== id) : [...lista, id];
  }

  async function derivarNuvem() {
    await escrever(async () => {
      const nuvem = await cliente.nc.derivar(
        projetoId,
        paraDerivar,
        `${dado?.projeto.nome ?? ""} — nuvem`,
      );
      setParaDerivar([]);
      aoAbrirNuvem?.(nuvem.id);
    });
  }

  async function excluirNo(id: string) {
    // Sem episódio de desfazer: o serviço não ressuscita nó. O raio foi declarado antes.
    await escrever(() => cliente.ara.excluirNo(projetoId, id).then(() => undefined));
  }

  useEffect(() => {
    function atalho(evento: KeyboardEvent) {
      if ((evento.ctrlKey || evento.metaKey) && evento.key.toLowerCase() === "z") {
        evento.preventDefault();
        void desfazer.desfazer().catch(setErroDeAcao);
      }
    }
    document.addEventListener("keydown", atalho);
    return () => document.removeEventListener("keydown", atalho);
  }, [desfazer]);

  if (carregando && !dado) return <Carregando />;
  if (erro && !dado) return <EstadoDeErro erro={erro} aoTentarDeNovo={() => void recarregar()} />;
  if (!dado) return null;

  const elo = examinando ? eloPorAresta.get(examinando) : undefined;

  return (
    <section className="tela tela-da-ara" aria-label={t("navegacao.ara")}>
      <div className="cabecalho-do-projeto">
        <button type="button" onClick={aoVoltar}>
          {t("app.voltar")}
        </button>
        <h1>{dado.projeto.nome}</h1>

        <div className="resumo-de-udes" role="group" aria-label={t("ude.resumo")}>
          {STATUS.map((status) => (
            <button
              key={status}
              type="button"
              aria-pressed={filtro === status}
              // `title`, e não `aria-label`: o rótulo acessível precisa continuar sendo o
              // texto visível — que traz a CONTAGEM. Um `aria-label` "Filtrar por
              // Validado" apagaria o número para quem usa leitor de tela.
              title={t("ude.filtrar", { status: tc("status", status, status) })}
              onClick={() => setFiltro(filtro === status ? null : status)}
            >
              {tc("status", status, status)}: {dado.resumo_por_status[status] ?? 0}
            </button>
          ))}
          {filtro ? (
            <button type="button" onClick={() => setFiltro(null)}>
              {t("ude.limpar_filtro")}
            </button>
          ) : null}
        </div>

        {/* INT-05: os UDEs escolhidos viram o ponto de partida do dilema. O nome e o
            inquilino saem do agregado de origem — o cliente não os inventa. */}
        <button
          type="button"
          title={t("nuvem.derivar_dica")}
          disabled={paraDerivar.length === 0}
          onClick={() => void derivarNuvem()}
        >
          {t("nuvem.derivar")} ({paraDerivar.length})
        </button>

        <button
          type="button"
          disabled={paraConector.length < 2}
          onClick={() =>
            void escrever(async () => {
              await cliente.ara.formarConector(projetoId, paraConector);
              setParaConector([]);
            })
          }
        >
          {t("conector.formar")} ({paraConector.length})
        </button>

        <button
          type="button"
          disabled={!desfazer.ultimoEpisodio}
          onClick={() => void desfazer.desfazer().catch(setErroDeAcao)}
        >
          {desfazer.ultimoEpisodio
            ? t("canvas.desfazer", { episodio: t(`episodio.${desfazer.ultimoEpisodio}` as "episodio.criar_no") })
            : t("canvas.desfazer_vazio")}
        </button>
      </div>

      {erroDeAcao ? (
        <p role="alert" className="erro">
          {mensagemDeErro(erroDeAcao, t)}
        </p>
      ) : null}

      {dado.udes.length === 0 ? <p className="vazio">{t("ude.sem_udes")}</p> : null}

      <div className="area-de-trabalho">
        <PainelDeEntidades
          nos={nos}
          arestas={arestas}
          selecionado={selecionado}
          filtrarNo={filtro ? (no) => udePorNo.get(no.id)?.status === filtro : undefined}
          colunaExtra={{
            titulo: t("painel.coluna_status"),
            conteudo: (no) => {
              const ude = udePorNo.get(no.id);
              if (!ude) {
                return (
                  <span className="coluna-de-ude">
                    <button
                      type="button"
                      onClick={() =>
                        void escrever(async () => {
                          await cliente.ara.marcarUde(projetoId, no.id);
                        })
                      }
                    >
                      {t("ude.marcar")}
                    </button>
                    <button type="button" onClick={() => setDetalhando(no.id)}>
                      {t("canvas.detalhe")}
                    </button>
                  </span>
                );
              }
              return (
                <span className="coluna-de-ude">
                  <SeloDeUde status={ude.status} />
                  <label className="escolha">
                    <input
                      type="checkbox"
                      aria-label={`${t("nuvem.derivar")}: ${no.titulo}`}
                      checked={paraDerivar.includes(no.id)}
                      onChange={() => setParaDerivar((atual) => alternar(atual, no.id))}
                    />
                    {t("ude.derivar_selecao")}
                  </label>
                  <button
                    type="button"
                    onClick={() =>
                      void escrever(async () => {
                        await cliente.ara.desmarcarUde(projetoId, no.id);
                      })
                    }
                  >
                    {t("ude.desmarcar")}
                  </button>
                  <button type="button" onClick={() => setDetalhando(no.id)}>
                    {t("canvas.detalhe")}
                  </button>
                </span>
              );
            },
          }}
          acoesDaAresta={(aresta) => (
            <>
              <label className="escolha">
                <input
                  type="checkbox"
                  aria-label={`${t("conector.titulo")}: ${aresta.id}`}
                  checked={paraConector.includes(aresta.id)}
                  onChange={() => setParaConector((atual) => alternar(atual, aresta.id))}
                />
                {t("conector.titulo")}
              </label>
              <button type="button" onClick={() => setExaminando(aresta.id)}>
                {t("exame.examinar")}
              </button>
            </>
          )}
          aoFocar={(id) => {
            setFoco(id);
            setSelecionado(id);
          }}
          aoSelecionar={setSelecionado}
          aoEditarNo={(id, titulo) => void editarTitulo(id, titulo)}
          aoExcluirNo={(id) => void excluirNo(id)}
          aoCriarNo={() => void criarNo({ x: 80, y: 80 })}
          aoLigar={(origem, destino) => void ligar(origem, destino)}
          aoEditarAresta={(id, rotulo) =>
            void escrever(async () => {
              await cliente.ara.editarAresta(projetoId, id, rotulo);
            })
          }
          aoExcluirAresta={(id) =>
            void escrever(async () => {
              await cliente.ara.excluirAresta(projetoId, id);
            })
          }
        />

        <Canvas
          nos={nos}
          arestas={arestas}
          selecionado={selecionado}
          focoEm={foco}
          selo={(no) => {
            const ude = udePorNo.get(no.id);
            return ude ? <SeloDeUde status={ude.status} /> : null;
          }}
          aoSelecionar={setSelecionado}
          aoCriarNo={(posicao) => void criarNo(posicao)}
          aoMoverNo={(id, posicao) => void moverNo(id, posicao)}
          aoEditarTitulo={(id, titulo) => void editarTitulo(id, titulo)}
          aoExcluirNo={(id) => void excluirNo(id)}
          aoLigar={(origem, destino) => void ligar(origem, destino)}
          aoAbrirDetalhe={setDetalhando}
          aoSelecionarAresta={setExaminando}
          ferramentas={
            <button
              type="button"
              onClick={() =>
                void escrever(async () => {
                  setRelatorio(await cliente.ara.analisar(projetoId));
                })
              }
            >
              {t("relatorio.gerar")}
            </button>
          }
        />

        {detalhando && nos.find((no) => no.id === detalhando) ? (
          <PainelDoNo
            no={nos.find((no) => no.id === detalhando)!}
            aoFechar={() => setDetalhando(null)}
            aoSalvar={async (dados) => {
              await cliente.ara.editarNo(projetoId, detalhando, dados);
              await recarregar();
              setDetalhando(null);
            }}
          />
        ) : null}

        {dado.conectores.length ? (
          <section className="conectores" aria-label={t("conector.titulo")}>
            <h2>{t("conector.titulo")}</h2>
            <p className="ajuda">{t("conector.ajuda")}</p>
            <ul>
              {dado.conectores.map((conector) => (
                <li key={conector.id}>
                  <p className="leitura">{conector.leitura}</p>
                  <button
                    type="button"
                    onClick={() =>
                      void escrever(async () => {
                        await cliente.ara.desfazerConector(projetoId, conector.id);
                      })
                    }
                  >
                    {t("conector.desfazer")}
                  </button>
                </li>
              ))}
            </ul>
          </section>
        ) : null}

        {udeSelecionado ? (
          <FichaDeUde
            ude={udeSelecionado}
            aoReformular={async (texto) => {
              await cliente.ara.reformular(projetoId, udeSelecionado.no_id, texto);
              await recarregar();
            }}
            aoValidarTexto={(texto) => cliente.ara.validarTexto(texto)}
            aoRegistrarParecer={async (parecer) => {
              await cliente.ara.registrarParecer(projetoId, udeSelecionado.no_id, parecer);
              await recarregar();
            }}
            aoMudarStatus={async (status, justificativa) => {
              await cliente.ara.mudarStatus(projetoId, udeSelecionado.no_id, status, justificativa);
              await recarregar();
            }}
            aoFechar={() => setSelecionado(null)}
          />
        ) : null}

        {elo ? (
          <ExameDeElo
            leitura={elo.leitura}
            estadoAtual={elo.exame.estado as EstadoDoExame}
            reservaAtual={elo.exame.reserva}
            aoFechar={() => setExaminando(null)}
            aoRegistrar={async (estado, reserva) => {
              await escrever(async () => {
                await cliente.ara.examinarElo(projetoId, elo.aresta_id, estado, reserva);
              });
              setExaminando(null);
            }}
          />
        ) : null}

        {relatorio ? (
          <RelatorioEstrutural
            relatorio={relatorio}
            nos={nos as No[]}
            aoFocar={(id) => {
              setFoco(id);
              setSelecionado(id);
            }}
            aoFechar={() => setRelatorio(null)}
          />
        ) : null}
      </div>
    </section>
  );
}
