/**
 * O canvas — nós, arestas causais, navegação e manipulação direta.
 *
 * Siglas, uma vez: **RI** — requisito de interface · **UDE** — Efeito Indesejável ·
 * **SVG** — *Scalable Vector Graphics* · **ARA** — Árvore da Realidade Atual.
 *
 * O componente é **apresentação e gesto**; nenhuma regra de domínio mora aqui e nenhuma
 * escrita acontece aqui. Ele recebe nós e arestas prontos e devolve intenções
 * (`aoCriarNo`, `aoMoverNo`, `aoLigar`…) para quem sabe falar com o serviço. É o que
 * permite testá-lo inteiro sem rede — e é o oposto do que a 4ª geração fazia, onde a
 * tela chamava o provedor de modelo direto do navegador
 * (`tocbuilderv3/components/ConflictCloudView.tsx` → `services/geminiService.ts`).
 *
 * Uma decisão registrada: **a navegação (pan, zoom, ajustar) não avisa mudança nenhuma**.
 * O RI-03 da spec 004 diz que ela nunca entra na pilha de desfazer, e a forma mais barata
 * de garantir isso é a câmera não ter caminho até os comandos.
 */
import { useEffect, useRef, useState, type ReactNode } from "react";
import type { Aresta, No, Posicao } from "../../dominio/tipos";
import { useI18n } from "../../i18n";
import { ArestaDoCanvas } from "./ArestaDoCanvas";
import { NoDoCanvas } from "./NoDoCanvas";
import { useViewport, PASSO_DE_ZOOM } from "./useViewport";

export interface CanvasProps {
  nos: readonly No[];
  arestas: readonly Aresta[];
  selecionado: string | null;
  aoSelecionar(id: string | null): void;
  aoCriarNo(posicao: Posicao): void;
  aoMoverNo(id: string, posicao: Posicao): void;
  aoEditarTitulo(id: string, titulo: string): void;
  aoExcluirNo(id: string): void;
  aoLigar(origemId: string, destinoId: string): void;
  aoAbrirDetalhe(id: string): void;
  arestaSelecionada?: string | null;
  aoSelecionarAresta?(id: string): void;
  selo?(no: No): ReactNode;
  classeDaAresta?(aresta: Aresta): string;
  focoEm?: string | null;
  /** Barra extra da ferramenta (a ARA pendura análise; a NC não usa este canvas). */
  ferramentas?: ReactNode;
}

export function Canvas({
  nos,
  arestas,
  selecionado,
  aoSelecionar,
  aoCriarNo,
  aoMoverNo,
  aoEditarTitulo,
  aoExcluirNo,
  aoLigar,
  aoAbrirDetalhe,
  arestaSelecionada = null,
  aoSelecionarAresta,
  selo,
  classeDaAresta,
  focoEm = null,
  ferramentas,
}: CanvasProps) {
  const { t } = useI18n();
  const area = useRef<HTMLDivElement>(null);
  const { janela, daTelaParaOPlano, comecarPan, moverPan, terminarPan, aplicarZoom, ajustar, focar } =
    useViewport(area);
  const [ligando, setLigando] = useState<{ origem: string | null } | null>(null);
  const [confirmandoExclusao, setConfirmandoExclusao] = useState(false);

  const porId = new Map(nos.map((no) => [no.id, no]));
  const noSelecionado = selecionado ? porId.get(selecionado) : undefined;
  const arestasDoSelecionado = selecionado
    ? arestas.filter((a) => a.origem_id === selecionado || a.destino_id === selecionado)
    : [];

  useEffect(() => {
    if (!focoEm) return;
    const alvo = porId.get(focoEm);
    if (alvo) focar(alvo);
    // `porId` é derivado de `nos`; depender dele criaria laço a cada render.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [focoEm, nos, focar]);

  useEffect(() => {
    function aoPressionar(evento: KeyboardEvent) {
      if (evento.key === "Escape") {
        setLigando(null);
        setConfirmandoExclusao(false);
      }
    }
    document.addEventListener("keydown", aoPressionar);
    return () => document.removeEventListener("keydown", aoPressionar);
  }, []);

  function escolherNo(id: string) {
    if (!ligando) {
      aoSelecionar(id);
      return;
    }
    if (!ligando.origem) {
      setLigando({ origem: id });
      return;
    }
    if (ligando.origem !== id) aoLigar(ligando.origem, id);
    setLigando(null);
  }

  return (
    <section className="canvas" aria-label={t("canvas.titulo")}>
      <div className="canvas-barra" role="toolbar" aria-label={t("canvas.titulo")}>
        <button type="button" onClick={() => aoCriarNo({ x: 80, y: 80 })}>
          {t("canvas.novo_no")}
        </button>
        <button
          type="button"
          aria-pressed={Boolean(ligando)}
          onClick={() => setLigando(ligando ? null : { origem: null })}
        >
          {t("canvas.ligar")}
        </button>
        <button
          type="button"
          disabled={!noSelecionado}
          onClick={() => setConfirmandoExclusao(true)}
        >
          {t("canvas.excluir_no")}
        </button>
        <span className="separador" />
        <button type="button" aria-label={t("canvas.aproximar")} onClick={() => aplicarZoom(PASSO_DE_ZOOM)}>
          +
        </button>
        <button type="button" aria-label={t("canvas.afastar")} onClick={() => aplicarZoom(1 / PASSO_DE_ZOOM)}>
          −
        </button>
        <button type="button" onClick={() => ajustar(nos)}>
          {t("canvas.ajustar")}
        </button>
        {ferramentas}
      </div>

      {ligando ? (
        <p className="canvas-dica" role="status">
          {ligando.origem
            ? t("canvas.ligar_origem", { titulo: porId.get(ligando.origem)?.titulo ?? "" })
            : t("canvas.ligar_dica")}
        </p>
      ) : null}

      <div
        ref={area}
        className="canvas-area"
        data-testid="fundo-do-canvas"
        onMouseDown={(e) => {
          if (e.target === e.currentTarget) {
            aoSelecionar(null);
            comecarPan(e);
          }
        }}
        onMouseMove={moverPan}
        onMouseUp={terminarPan}
        onMouseLeave={terminarPan}
        onDoubleClick={(e) => {
          if (e.target !== e.currentTarget) return;
          aoCriarNo(daTelaParaOPlano({ x: e.clientX, y: e.clientY }));
        }}
      >
        <div
          className="canvas-plano"
          data-testid="plano-do-canvas"
          style={{ transform: `translate(${janela.x}px, ${janela.y}px) scale(${janela.zoom})` }}
        >
          <svg className="canvas-arestas" aria-hidden={false}>
            <defs>
              <marker
                id="seta-causal"
                viewBox="0 0 10 10"
                refX="9"
                refY="5"
                markerWidth="7"
                markerHeight="7"
                orient="auto-start-reverse"
              >
                <path d="M 0 0 L 10 5 L 0 10 z" fill="currentColor" />
              </marker>
            </defs>
            {arestas.map((aresta) => {
              const origem = porId.get(aresta.origem_id);
              const destino = porId.get(aresta.destino_id);
              if (!origem || !destino) return null;
              return (
                <ArestaDoCanvas
                  key={aresta.id}
                  aresta={aresta}
                  origem={origem}
                  destino={destino}
                  selecionada={aresta.id === arestaSelecionada}
                  leitura={`Se ${origem.titulo}, então ${destino.titulo}${aresta.rotulo ? ` (${aresta.rotulo})` : ""}`}
                  classe={classeDaAresta?.(aresta)}
                  aoSelecionar={(id) => aoSelecionarAresta?.(id)}
                />
              );
            })}
          </svg>
          {nos.map((no) => (
            <NoDoCanvas
              key={no.id}
              no={no}
              selecionado={no.id === selecionado}
              zoom={janela.zoom}
              selo={selo?.(no)}
              emLigacao={Boolean(ligando)}
              aoSelecionar={escolherNo}
              aoMover={aoMoverNo}
              aoEditarTitulo={aoEditarTitulo}
              aoAbrirDetalhe={aoAbrirDetalhe}
            />
          ))}
        </div>

        {nos.length === 0 ? (
          <div className="estado-vazio no-canvas">
            <h3>{t("canvas.vazio_titulo")}</h3>
            <p>{t("canvas.vazio_texto")}</p>
          </div>
        ) : null}
      </div>

      {confirmandoExclusao && noSelecionado ? (
        <div className="dialogo" role="dialog" aria-modal="true" aria-label={t("canvas.excluir_no")}>
          <p className="dialogo-titulo">{noSelecionado.titulo}</p>
          {/* RI-05: o raio aparece ANTES do clique final, no próprio controle. */}
          <p className="dialogo-raio">{t("canvas.raio_da_exclusao", { n: arestasDoSelecionado.length })}</p>
          <div className="dialogo-acoes">
            <button type="button" onClick={() => setConfirmandoExclusao(false)}>
              {t("app.cancelar")}
            </button>
            <button
              type="button"
              className="perigo"
              onClick={() => {
                setConfirmandoExclusao(false);
                aoExcluirNo(noSelecionado.id);
              }}
            >
              {t("app.confirmar")}
            </button>
          </div>
        </div>
      ) : null}
    </section>
  );
}
