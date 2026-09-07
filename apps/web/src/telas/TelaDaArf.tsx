/**
 * A Árvore da Realidade Futura (ARF) — a ferramenta que a linhagem nunca entregou.
 *
 * Siglas, uma vez: **ARF** — Árvore da Realidade Futura · **ARA** — Árvore da Realidade
 * Atual · **NC** — Nuvem de Conflito · **UDE** — Efeito Indesejável · **ED** — Efeito
 * Desejável · **API** — interface de programação de aplicações · **RI/RF/RN** — requisito
 * de interface / funcional / regra de negócio.
 *
 * Nas quatro gerações do TOC-Builder a ARF foi um **botão cinza**
 * (`tocbuilderv3/components/Sidebar.tsx:55` — `view: 'ARF', disabled: true`): zero
 * componentes, zero prompts, zero domínio. O domínio nasceu no ciclo 008
 * (`apps/api/src/toc_api/dominio/arf.py`) e ficou sem tela — domínio sem tela é metade do
 * trabalho, e é a crítica que fazemos às gerações anteriores.
 *
 * Três decisões desta tela:
 *
 * 1. **O ramo negativo tem superfície própria** (`RamosNegativos`), e não é mais um nó da
 *    lista. Ele é o efeito indevido que a própria injeção traz; desenhá-lo como um efeito
 *    qualquer é dizer que ele é mais uma consequência boa — que é o erro que a ferramenta
 *    existe para impedir.
 * 2. **Nada é recalculado aqui.** A leitura de suficiência, o espelho UDE → ED e a
 *    verificação estrutural chegam prontos do servidor, computados por função pura de
 *    domínio. Uma segunda conta na tela seria uma segunda verdade.
 * 3. **Nenhum botão é escondido por regra de negócio** — a recusa volta com a regra
 *    nomeada e vira texto na tela. Esconder ensina a pessoa a não ver a regra; mostrar a
 *    recusa ensina a regra. A única exceção é o seletor da poda, que só lista injeções
 *    porque oferecer um efeito ali seria oferecer o que já se sabe recusado (RN-04).
 */
import { useCallback, useState } from "react";
import type { Cliente } from "../api/cliente";
import type { Arf, No, PapelNaArf, Posicao } from "../dominio/tipos";
import { Canvas } from "../componentes/canvas/Canvas";
import { Carregando, EstadoDeErro } from "../componentes/Estados";
import { mensagemDeErro } from "../componentes/mensagemDeErro";
import { CadeiaDeEfeitos } from "../componentes/arf/CadeiaDeEfeitos";
import { RamosNegativos } from "../componentes/arf/RamosNegativos";
import { VerificacaoDaArf } from "../componentes/arf/VerificacaoDaArf";
import { useRecurso } from "../estado/useRecurso";
import { useI18n } from "../i18n";

const PAPEIS: readonly PapelNaArf[] = ["injecao", "efeito_futuro"];

export interface TelaDaArfProps {
  cliente: Cliente;
  projetoId: string;
  aoVoltar(): void;
  /** RF-42: a travessia se abre de DENTRO da ferramenta — ela é de uma análise. */
  aoAbrirCadeia?(projetoId: string): void;
}

export function TelaDaArf({ cliente, projetoId, aoVoltar, aoAbrirCadeia }: TelaDaArfProps) {
  const { t, tc } = useI18n();
  const buscar = useCallback(() => cliente.arf.abrir(projetoId), [cliente, projetoId]);
  const { dado, carregando, erro, recarregar } = useRecurso<Arf>(buscar, [cliente, projetoId]);

  const [selecionado, setSelecionado] = useState<string | null>(null);
  const [foco, setFoco] = useState<string | null>(null);
  const [papelNovo, setPapelNovo] = useState<PapelNaArf>("efeito_futuro");
  const [textoNovo, setTextoNovo] = useState("");
  const [udeEscolhido, setUdeEscolhido] = useState("");
  const [erroDeAcao, setErroDeAcao] = useState<unknown>(null);
  const [ocupado, setOcupado] = useState(false);

  const escrever = useCallback(
    async (acao: () => Promise<unknown>) => {
      setErroDeAcao(null);
      setOcupado(true);
      try {
        await acao();
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

  const arf = dado;
  const noSelecionado = arf.nos.find((no) => no.id === selecionado) ?? null;
  const espelhoDoSelecionado = arf.espelhos.find((e) => e.no_id === selecionado) ?? null;
  const ehRaizDeRamo = arf.ramos.some((r) => r.raiz_id === selecionado);
  const udesLivres = arf.udes_da_cadeia.filter(
    (ude) => !arf.espelhos.some((e) => e.ude_id === ude && e.no_id !== selecionado),
  );

  // O canvas do M1 fala `No`; o M4 fala nó COM papel. A conversão é de apresentação e mora
  // aqui, num lugar só: o `tipo` do nó carrega o papel, que é como ele já viaja no banco.
  const nosDoCanvas: No[] = arf.nos.map((no) => ({
    id: no.id,
    titulo: no.titulo,
    descricao: no.descricao,
    tipo: no.papel,
    posicao: no.posicao,
    recolhido: no.recolhido,
  }));
  const arestasDoCanvas = arf.elos.map((elo) => ({
    id: elo.id,
    origem_id: elo.origem_id,
    destino_id: elo.destino_id,
    rotulo: elo.rotulo,
  }));
  const raizesDeRamo = new Set(arf.ramos.map((r) => r.raiz_id));

  return (
    <section className="tela tela-da-arf" aria-label={t("arf.titulo")}>
      <div className="cabecalho-do-projeto">
        <button type="button" onClick={aoVoltar}>
          {t("app.voltar")}
        </button>
        <h1>{arf.nome}</h1>
        {aoAbrirCadeia ? (
          <button type="button" onClick={() => aoAbrirCadeia(arf.id)}>
            {t("navegacao.cadeia")}
          </button>
        ) : null}
        {arf.origem ? (
          <p className="origem">
            {t("arf.origem")} {tc("ferramenta", arf.origem.ferramenta)}
          </p>
        ) : null}
      </div>

      {erroDeAcao ? (
        <p role="alert" className="erro">
          {mensagemDeErro(erroDeAcao, t)}
        </p>
      ) : null}

      <form
        className="linha-de-criacao"
        onSubmit={(evento) => {
          evento.preventDefault();
          const titulo = textoNovo.trim();
          if (!titulo) return;
          void escrever(async () => {
            await cliente.arf.adicionarNo(projetoId, { papel: papelNovo, titulo });
            setTextoNovo("");
          });
        }}
      >
        <label htmlFor="papel-do-no-novo">{t("arf.papel")}</label>
        <select
          id="papel-do-no-novo"
          value={papelNovo}
          onChange={(evento) => setPapelNovo(evento.target.value as PapelNaArf)}
        >
          {PAPEIS.map((papel) => (
            <option key={papel} value={papel}>
              {tc("papel_na_arf", papel)}
            </option>
          ))}
        </select>
        <label htmlFor="texto-do-no-novo">{t("arf.texto_do_no")}</label>
        <input
          id="texto-do-no-novo"
          value={textoNovo}
          onChange={(evento) => setTextoNovo(evento.target.value)}
        />
        <button type="submit" disabled={ocupado || !textoNovo.trim()}>
          {t("arf.adicionar")}
        </button>
      </form>

      <div className="area-de-trabalho">
        <Canvas
          nos={nosDoCanvas}
          arestas={arestasDoCanvas}
          selecionado={selecionado}
          focoEm={foco}
          aoSelecionar={(id) => {
            setSelecionado(id);
            setUdeEscolhido("");
          }}
          aoCriarNo={(posicao: Posicao) =>
            void escrever(() =>
              cliente.arf.adicionarNo(projetoId, {
                papel: "efeito_futuro",
                titulo: t("canvas.novo_no_titulo"),
                posicao,
              }),
            )
          }
          aoMoverNo={(id, posicao) =>
            void escrever(() => cliente.arf.moverNo(projetoId, id, posicao))
          }
          aoEditarTitulo={(id, titulo) =>
            void escrever(() => cliente.arf.editarNo(projetoId, id, { titulo }))
          }
          aoExcluirNo={(id) => void escrever(() => cliente.arf.excluirNo(projetoId, id))}
          aoLigar={(origemId, destinoId) =>
            void escrever(() => cliente.arf.ligar(projetoId, origemId, destinoId))
          }
          aoAbrirDetalhe={(id) => setSelecionado(id)}
          classeDaAresta={(aresta) =>
            // A aresta que SAI de uma raiz de ramo negativo é o que o ramo arrasta: ela
            // não é uma consequência desejada, e a folha de estilo a desenha diferente.
            raizesDeRamo.has(aresta.origem_id) ? "aresta-do-ramo-negativo" : ""
          }
          selo={(no) => (
            <span className="selo-da-arf" data-papel={no.tipo}>
              {tc("papel_na_arf", no.tipo)}
              {arf.espelhos.some((e) => e.no_id === no.id) && !raizesDeRamo.has(no.id)
                ? ` · ${t("arf.efeito_desejavel")}`
                : ""}
              {raizesDeRamo.has(no.id) ? ` · ${t("arf.ramo.raiz")}` : ""}
            </span>
          )}
        />

        <div className="painel-da-arf">
          {noSelecionado ? (
            <aside className="ficha-do-no-da-arf" aria-label={noSelecionado.titulo}>
              <h3>{noSelecionado.titulo}</h3>
              <p className="papel-do-no">{tc("papel_na_arf", noSelecionado.papel)}</p>

              <label htmlFor="papel-do-selecionado">{t("arf.papel")}</label>
              <select
                id="papel-do-selecionado"
                value={noSelecionado.papel}
                onChange={(evento) =>
                  void escrever(() =>
                    cliente.arf.mudarPapel(
                      projetoId,
                      noSelecionado.id,
                      evento.target.value as PapelNaArf,
                    ),
                  )
                }
              >
                {PAPEIS.map((papel) => (
                  <option key={papel} value={papel}>
                    {tc("papel_na_arf", papel)}
                  </option>
                ))}
              </select>

              {/* O espelho UDE → ED só existe com cadeia vinculada (RF-07): sem ela a tela
                  DIZ o que falta, em vez de oferecer um seletor vazio. */}
              {noSelecionado.papel === "efeito_futuro" ? (
                arf.udes_da_cadeia.length === 0 ? (
                  <p className="sem-cadeia">{t("arf.sem_cadeia")}</p>
                ) : espelhoDoSelecionado ? (
                  <div className="espelho">
                    <p>
                      {t("arf.efeito_desejavel")}: {espelhoDoSelecionado.ude_id}
                    </p>
                    <button
                      type="button"
                      disabled={ocupado}
                      onClick={() =>
                        void escrever(() =>
                          cliente.arf.desfazerEspelho(projetoId, noSelecionado.id),
                        )
                      }
                    >
                      {t("arf.desfazer_espelho")}
                    </button>
                  </div>
                ) : (
                  <div className="espelho">
                    <label htmlFor="ude-de-origem">{t("arf.ude_de_origem")}</label>
                    <select
                      id="ude-de-origem"
                      value={udeEscolhido}
                      onChange={(evento) => setUdeEscolhido(evento.target.value)}
                    >
                      <option value="">{t("arf.escolha_o_ude")}</option>
                      {udesLivres.map((ude) => (
                        <option key={ude} value={ude}>
                          {ude}
                        </option>
                      ))}
                    </select>
                    <button
                      type="button"
                      disabled={ocupado || !udeEscolhido}
                      onClick={() =>
                        void escrever(() =>
                          cliente.arf.espelhar(
                            projetoId,
                            noSelecionado.id,
                            udeEscolhido,
                            arf.origem?.projeto_id ?? null,
                          ),
                        )
                      }
                    >
                      {t("arf.espelhar")}
                    </button>
                  </div>
                )
              ) : null}

              {/* RF-08/RF-10: marcar é MANUAL. Não existe — e não deve existir — rota de
                  sugestão de ramo negativo; a decisão do round 008 é essa ausência. */}
              <button
                type="button"
                disabled={ocupado || ehRaizDeRamo}
                onClick={() =>
                  void escrever(() => cliente.arf.marcarRamo(projetoId, noSelecionado.id))
                }
              >
                {t("arf.marcar_ramo")}
              </button>
            </aside>
          ) : null}

          <CadeiaDeEfeitos
            nos={arf.nos}
            elos={arf.elos}
            espelhos={arf.espelhos}
            ramos={arf.ramos}
            selecionado={selecionado}
            aoSelecionar={setSelecionado}
          />

          <RamosNegativos
            ramos={arf.ramos}
            nos={arf.nos}
            ocupado={ocupado}
            aoPodar={(ramoId, injecaoId) =>
              void escrever(() =>
                cliente.arf.mudarRamo(projetoId, ramoId, {
                  estado: "tratado",
                  injecao_de_corte_id: injecaoId,
                }),
              )
            }
            aoAceitar={(ramoId, justificativa) =>
              void escrever(() =>
                // O AUTOR não vai no corpo: ele é o principal do servidor (RN-04).
                cliente.arf.mudarRamo(projetoId, ramoId, { estado: "aceito", justificativa }),
              )
            }
            aoReabrir={(ramoId) =>
              void escrever(() =>
                cliente.arf.mudarRamo(projetoId, ramoId, { estado: "aberto" }),
              )
            }
          />

          <VerificacaoDaArf
            verificacao={arf.verificacao}
            nos={arf.nos}
            aoFocar={(id) => {
              setSelecionado(id);
              setFoco(id);
            }}
          />
        </div>
      </div>
    </section>
  );
}
