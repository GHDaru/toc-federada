/**
 * Uma aresta causal: direcionada, e lida por extenso — "se causa, então efeito" (RI-02).
 *
 * O `role="img"` com `aria-label` não é enfeite de acessibilidade: uma seta desenhada em
 * SVG (*Scalable Vector Graphics*) é invisível para quem usa leitor de tela, e a leitura
 * causal É o conteúdo do diagrama. Quem não vê a curva precisa ler a frase.
 */
import type { Aresta, No } from "../../dominio/tipos";
import { ALTURA_DO_NO, LARGURA_DO_NO } from "./useViewport";

export interface ArestaDoCanvasProps {
  aresta: Aresta;
  origem: No;
  destino: No;
  selecionada: boolean;
  leitura: string;
  classe?: string;
  aoSelecionar(id: string): void;
}

export function caminhoEntre(origem: No, destino: No): string {
  const x1 = origem.posicao.x + LARGURA_DO_NO / 2;
  const y1 = origem.posicao.y + ALTURA_DO_NO;
  const x2 = destino.posicao.x + LARGURA_DO_NO / 2;
  const y2 = destino.posicao.y;
  const curva = Math.max(40, Math.abs(y2 - y1) / 2);
  return `M ${x1},${y1} C ${x1},${y1 + curva} ${x2},${y2 - curva} ${x2},${y2}`;
}

export function ArestaDoCanvas({
  aresta,
  origem,
  destino,
  selecionada,
  leitura,
  classe,
  aoSelecionar,
}: ArestaDoCanvasProps) {
  const d = caminhoEntre(origem, destino);
  return (
    <g
      role="img"
      aria-label={leitura}
      className={`aresta${selecionada ? " selecionada" : ""}${classe ? ` ${classe}` : ""}`}
      onClick={(e) => {
        e.stopPropagation();
        aoSelecionar(aresta.id);
      }}
    >
      {/* Traço largo e invisível: alvo de clique honesto para quem usa mouse. */}
      <path d={d} stroke="transparent" strokeWidth={14} fill="none" />
      <path d={d} className="aresta-traco" markerEnd="url(#seta-causal)" fill="none" />
      {aresta.rotulo ? (
        <text className="aresta-rotulo" x={(origem.posicao.x + destino.posicao.x) / 2 + LARGURA_DO_NO / 2} y={(origem.posicao.y + destino.posicao.y) / 2 + ALTURA_DO_NO / 2}>
          {aresta.rotulo}
        </text>
      ) : null}
    </g>
  );
}
