/**
 * O painel de entidades — a vista tabular do MESMO grafo do canvas.
 *
 * Siglas, uma vez: **RI** — requisito de interface · **UDE** — Efeito Indesejável.
 *
 * "Sem ser uma segunda fonte de verdade" (RI-04 da spec 002) é literal aqui: o painel
 * recebe `nos` e `arestas` — os mesmos objetos que o canvas recebe — e devolve as mesmas
 * intenções. Ele não guarda cópia, não deriva estado e não reordena por conta própria.
 *
 * O que ele acrescenta ao canvas, e é por isso que existe: entrada rápida em sessão de
 * grupo (muitos itens seguidos), e **criar aresta sem arrastar** — que é a única forma de
 * o requisito de teclado (RI-11 da spec 004) valer para quem não usa mouse.
 *
 * A largura escolhida vive na sessão (RI-07). `sessionStorage` pode simplesmente não
 * existir (janela privada, política do navegador), e por isso toda leitura e escrita está
 * embrulhada: um painel que não abre porque o armazenamento falhou é pior do que um
 * painel na largura padrão.
 */
import { useCallback, useEffect, useRef, useState } from "react";
import type { Aresta, No } from "../dominio/tipos";
import { useI18n } from "../i18n";

export const LARGURA_PADRAO_DO_PAINEL = 380;
export const LARGURA_MINIMA_DO_PAINEL = 220;
export const LARGURA_MAXIMA_DO_PAINEL = 720;
export const CHAVE_DA_LARGURA = "toc.painel.largura";

function lerLargura(): number {
  try {
    const guardada = Number(window.sessionStorage.getItem(CHAVE_DA_LARGURA));
    if (Number.isFinite(guardada) && guardada >= LARGURA_MINIMA_DO_PAINEL) return guardada;
  } catch {
    /* armazenamento indisponível: a largura padrão serve */
  }
  return LARGURA_PADRAO_DO_PAINEL;
}

function guardarLargura(largura: number): void {
  try {
    window.sessionStorage.setItem(CHAVE_DA_LARGURA, String(largura));
  } catch {
    /* idem: não guardar a largura nunca pode derrubar a tela */
  }
}

export interface PainelDeEntidadesProps {
  nos: readonly No[];
  arestas: readonly Aresta[];
  selecionado: string | null;
  aoFocar(id: string): void;
  aoSelecionar(id: string): void;
  aoEditarNo(id: string, titulo: string): void;
  aoExcluirNo(id: string): void;
  aoCriarNo(): void;
  aoLigar(origemId: string, destinoId: string): void;
  aoEditarAresta(id: string, rotulo: string): void;
  aoExcluirAresta(id: string): void;
  /** Coluna extra da ferramenta (o status do UDE, na ARA). */
  colunaExtra?: { titulo: string; conteudo(no: No): React.ReactNode };
  /** Ações extras por aresta (o exame de elo, na ARA — RI-05 da spec 005). */
  acoesDaAresta?(aresta: Aresta): React.ReactNode;
  /** Filtro da ferramenta sobre as linhas de nó (o filtro por status, na ARA). */
  filtrarNo?(no: No): boolean;
}

export function PainelDeEntidades({
  nos,
  arestas,
  selecionado,
  aoFocar,
  aoSelecionar,
  aoEditarNo,
  aoExcluirNo,
  aoCriarNo,
  aoLigar,
  aoEditarAresta,
  aoExcluirAresta,
  colunaExtra,
  acoesDaAresta,
  filtrarNo,
}: PainelDeEntidadesProps) {
  const { t } = useI18n();
  const [aba, setAba] = useState<"nos" | "arestas">("nos");
  const [largura, setLargura] = useState<number>(() => lerLargura());
  const [editandoNo, setEditandoNo] = useState<string | null>(null);
  const [editandoAresta, setEditandoAresta] = useState<string | null>(null);
  const [rascunho, setRascunho] = useState("");
  const [origemNova, setOrigemNova] = useState("");
  const [destinoNovo, setDestinoNovo] = useState("");
  const arrasto = useRef<{ inicio: number; largura: number } | null>(null);

  const titulos = new Map(nos.map((no) => [no.id, no.titulo]));
  const nosVisiveis = filtrarNo ? nos.filter(filtrarNo) : nos;

  const aoMover = useCallback((evento: MouseEvent) => {
    if (!arrasto.current) return;
    const bruta = arrasto.current.largura + (evento.clientX - arrasto.current.inicio);
    setLargura(Math.min(LARGURA_MAXIMA_DO_PAINEL, Math.max(LARGURA_MINIMA_DO_PAINEL, bruta)));
  }, []);

  const aoSoltar = useCallback(() => {
    arrasto.current = null;
    setLargura((atual) => {
      guardarLargura(atual);
      return atual;
    });
  }, []);

  useEffect(() => {
    document.addEventListener("mousemove", aoMover);
    document.addEventListener("mouseup", aoSoltar);
    return () => {
      document.removeEventListener("mousemove", aoMover);
      document.removeEventListener("mouseup", aoSoltar);
    };
  }, [aoMover, aoSoltar]);

  function ajustarPorTeclado(delta: number) {
    setLargura((atual) => {
      const nova = Math.min(LARGURA_MAXIMA_DO_PAINEL, Math.max(LARGURA_MINIMA_DO_PAINEL, atual + delta));
      guardarLargura(nova);
      return nova;
    });
  }

  function comecarEdicaoDeNo(no: No) {
    setRascunho(no.titulo);
    setEditandoNo(no.id);
  }

  return (
    <aside className="painel" style={{ width: `${largura}px` }} aria-label={t("painel.titulo")}>
      <div
        role="separator"
        aria-orientation="vertical"
        aria-label={t("painel.redimensionar")}
        aria-valuenow={largura}
        aria-valuemin={LARGURA_MINIMA_DO_PAINEL}
        aria-valuemax={LARGURA_MAXIMA_DO_PAINEL}
        aria-valuetext={t("painel.largura", { n: largura })}
        tabIndex={0}
        className="painel-alca"
        onMouseDown={(e) => {
          arrasto.current = { inicio: e.clientX, largura };
        }}
        onKeyDown={(e) => {
          if (e.key === "ArrowLeft") ajustarPorTeclado(-24);
          if (e.key === "ArrowRight") ajustarPorTeclado(24);
        }}
      />

      <div className="painel-abas" role="tablist" aria-label={t("painel.titulo")}>
        <button
          type="button"
          role="tab"
          aria-selected={aba === "nos"}
          onClick={() => setAba("nos")}
        >
          {t("painel.nos")} ({nos.length})
        </button>
        <button
          type="button"
          role="tab"
          aria-selected={aba === "arestas"}
          onClick={() => setAba("arestas")}
        >
          {t("painel.arestas")} ({arestas.length})
        </button>
      </div>

      <div className="painel-conteudo">
        {aba === "nos" ? (
          nosVisiveis.length === 0 ? (
            <div className="estado-vazio">
              <p>{t("painel.vazio_nos")}</p>
              <button type="button" onClick={aoCriarNo}>
                {t("painel.adicionar_no")}
              </button>
            </div>
          ) : (
            <table className="tabela">
              <thead className="cabecalho-fixo">
                <tr>
                  <th scope="col">{t("painel.coluna_titulo")}</th>
                  {colunaExtra ? <th scope="col">{colunaExtra.titulo}</th> : null}
                  <th scope="col">{t("painel.coluna_acoes")}</th>
                </tr>
              </thead>
              <tbody>
                {nosVisiveis.map((no) => (
                  <tr
                    key={no.id}
                    aria-selected={no.id === selecionado}
                    className={no.id === selecionado ? "selecionada" : undefined}
                    onClick={() => aoSelecionar(no.id)}
                  >
                    <td>
                      {editandoNo === no.id ? (
                        <input
                          autoFocus
                          aria-label={t("painel.coluna_titulo")}
                          value={rascunho}
                          onChange={(e) => setRascunho(e.target.value)}
                          onKeyDown={(e) => {
                            if (e.key === "Enter") {
                              const limpo = rascunho.trim();
                              setEditandoNo(null);
                              if (limpo && limpo !== no.titulo) aoEditarNo(no.id, limpo);
                            }
                            if (e.key === "Escape") setEditandoNo(null);
                          }}
                        />
                      ) : (
                        no.titulo
                      )}
                    </td>
                    {colunaExtra ? <td>{colunaExtra.conteudo(no)}</td> : null}
                    <td className="acoes">
                      <button type="button" onClick={() => aoFocar(no.id)}>
                        {t("painel.focar")}
                      </button>
                      <button type="button" onClick={() => comecarEdicaoDeNo(no)}>
                        {t("painel.editar")}
                      </button>
                      <button type="button" className="perigo" onClick={() => aoExcluirNo(no.id)}>
                        {t("painel.excluir")}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )
        ) : (
          <>
            <form
              className="linha-de-criacao"
              onSubmit={(e) => {
                e.preventDefault();
                if (origemNova && destinoNovo && origemNova !== destinoNovo) {
                  aoLigar(origemNova, destinoNovo);
                  setOrigemNova("");
                  setDestinoNovo("");
                }
              }}
            >
              <label>
                {t("painel.coluna_origem")}
                <select value={origemNova} onChange={(e) => setOrigemNova(e.target.value)}>
                  <option value="">—</option>
                  {nos.map((no) => (
                    <option key={no.id} value={no.id}>
                      {no.titulo}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                {t("painel.coluna_destino")}
                <select value={destinoNovo} onChange={(e) => setDestinoNovo(e.target.value)}>
                  <option value="">—</option>
                  {nos.map((no) => (
                    <option key={no.id} value={no.id}>
                      {no.titulo}
                    </option>
                  ))}
                </select>
              </label>
              <button type="submit">{t("painel.adicionar_aresta")}</button>
            </form>

            {arestas.length === 0 ? (
              <div className="estado-vazio">
                <p>{t("painel.vazio_arestas")}</p>
              </div>
            ) : (
              <table className="tabela">
                <thead className="cabecalho-fixo">
                  <tr>
                    <th scope="col">{t("painel.coluna_origem")}</th>
                    <th scope="col">{t("painel.coluna_destino")}</th>
                    <th scope="col">{t("painel.coluna_rotulo")}</th>
                    <th scope="col">{t("painel.coluna_acoes")}</th>
                  </tr>
                </thead>
                <tbody>
                  {arestas.map((aresta) => (
                    <tr key={aresta.id}>
                      <td>{titulos.get(aresta.origem_id) ?? "—"}</td>
                      <td>{titulos.get(aresta.destino_id) ?? "—"}</td>
                      <td>
                        {editandoAresta === aresta.id ? (
                          <input
                            autoFocus
                            aria-label={t("painel.coluna_rotulo")}
                            value={rascunho}
                            onChange={(e) => setRascunho(e.target.value)}
                            onKeyDown={(e) => {
                              if (e.key === "Enter") {
                                setEditandoAresta(null);
                                aoEditarAresta(aresta.id, rascunho.trim());
                              }
                              if (e.key === "Escape") setEditandoAresta(null);
                            }}
                          />
                        ) : (
                          aresta.rotulo || "—"
                        )}
                      </td>
                      <td className="acoes">
                        {acoesDaAresta?.(aresta)}
                        <button
                          type="button"
                          onClick={() => {
                            setRascunho(aresta.rotulo);
                            setEditandoAresta(aresta.id);
                          }}
                        >
                          {t("painel.editar")}
                        </button>
                        <button
                          type="button"
                          className="perigo"
                          onClick={() => aoExcluirAresta(aresta.id)}
                        >
                          {t("painel.excluir")}
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </>
        )}
      </div>
    </aside>
  );
}
