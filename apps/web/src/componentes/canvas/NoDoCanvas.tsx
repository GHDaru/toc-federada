/**
 * Um nó no canvas: manipulação direta (arrastar, clicar, editar o título inline).
 *
 * Siglas, uma vez: **UDE** — Efeito Indesejável · **RI** — requisito de interface.
 *
 * O nó é um `button`: é o que dá foco, tecla e nome acessível de graça. A linhagem usava
 * `div` com `onMouseDown` (`tocbuilderv3/components/canvas/CanvasNode.tsx`), o que deixa
 * a árvore inteira inalcançável por teclado — e RI-11 da spec 004 exige o contrário.
 */
import { useEffect, useRef, useState, type ReactNode } from "react";
import type { No, Posicao } from "../../dominio/tipos";
import { useI18n } from "../../i18n";
import { ALTURA_DO_NO, LARGURA_DO_NO } from "./useViewport";

/** Passo do movimento por teclado (fino) e com Shift (grosso). */
const PASSO_FINO = 20;
const PASSO_GROSSO = 100;

export interface NoDoCanvasProps {
  no: No;
  selecionado: boolean;
  zoom: number;
  /** Enfeite semântico pendurado pela ferramenta (o selo de UDE, na ARA). */
  selo?: ReactNode;
  aoSelecionar(id: string): void;
  aoMover(id: string, posicao: Posicao): void;
  aoEditarTitulo(id: string, titulo: string): void;
  aoAbrirDetalhe(id: string): void;
  /** Em modo de ligação o clique escolhe causa/efeito em vez de selecionar. */
  emLigacao: boolean;
}

export function NoDoCanvas({
  no,
  selecionado,
  zoom,
  selo,
  aoSelecionar,
  aoMover,
  aoEditarTitulo,
  aoAbrirDetalhe,
  emLigacao,
}: NoDoCanvasProps) {
  const { t } = useI18n();
  const [editando, setEditando] = useState(false);
  const [rascunho, setRascunho] = useState(no.titulo);
  const campo = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (editando) campo.current?.select();
  }, [editando]);

  function comecarEdicao() {
    setRascunho(no.titulo);
    setEditando(true);
  }

  function confirmar() {
    const limpo = rascunho.trim();
    setEditando(false);
    if (limpo && limpo !== no.titulo) aoEditarTitulo(no.id, limpo);
  }

  function aoPressionarNaEdicao(evento: React.KeyboardEvent<HTMLInputElement>) {
    if (evento.key === "Enter") {
      evento.preventDefault();
      evento.stopPropagation();
      confirmar();
    }
    if (evento.key === "Escape") {
      evento.preventDefault();
      evento.stopPropagation();
      setEditando(false);
    }
  }

  function arrastar(evento: React.MouseEvent) {
    if (emLigacao || editando) return;
    evento.stopPropagation();
    const inicio = { x: evento.clientX, y: evento.clientY };
    const origem = { ...no.posicao };
    let mexeu = false;

    const mover = (e: MouseEvent) => {
      const dx = (e.clientX - inicio.x) / zoom;
      const dy = (e.clientY - inicio.y) / zoom;
      if (Math.abs(dx) > 2 || Math.abs(dy) > 2) mexeu = true;
    };
    const soltar = (e: MouseEvent) => {
      document.removeEventListener("mousemove", mover);
      document.removeEventListener("mouseup", soltar);
      if (!mexeu) return;
      // Um comando por gesto **terminado**: o servidor recebe `mover nó` uma vez, e o
      // desfazer tem um episódio, não trinta.
      aoMover(no.id, {
        x: Math.round(origem.x + (e.clientX - inicio.x) / zoom),
        y: Math.round(origem.y + (e.clientY - inicio.y) / zoom),
      });
    };
    document.addEventListener("mousemove", mover);
    document.addEventListener("mouseup", soltar);
  }

  return (
    <div
      className={`no-do-canvas${selecionado ? " selecionado" : ""}`}
      style={{
        transform: `translate(${no.posicao.x}px, ${no.posicao.y}px)`,
        width: LARGURA_DO_NO,
        minHeight: ALTURA_DO_NO,
      }}
      data-no-id={no.id}
    >
      {editando ? (
        <input
          ref={campo}
          className="no-titulo-edicao"
          value={rascunho}
          aria-label={t("canvas.editar_no")}
          onChange={(e) => setRascunho(e.target.value)}
          onKeyDown={aoPressionarNaEdicao}
          onBlur={() => setEditando(false)}
        />
      ) : (
        <button
          type="button"
          className="no-corpo"
          aria-pressed={selecionado}
          aria-label={`${no.titulo}${no.descricao ? ` — ${no.descricao}` : ""}`}
          onMouseDown={arrastar}
          onClick={(e) => {
            e.stopPropagation();
            aoSelecionar(no.id);
          }}
          onDoubleClick={(e) => {
            e.stopPropagation();
            comecarEdicao();
          }}
          onKeyDown={(e) => {
            if (e.key === "F2") {
              e.preventDefault();
              comecarEdicao();
            }
            if (e.key === "Enter" && e.ctrlKey) aoAbrirDetalhe(no.id);
            // Mover por teclado: sem isto, "arrastar" seria a única forma de posicionar
            // um nó — e a árvore inteira ficaria fora do alcance de quem não usa mouse
            // (RI-11 da spec 004). O passo é o mesmo do grid do canvas.
            const passo = e.shiftKey ? PASSO_GROSSO : PASSO_FINO;
            const deslocamento: Record<string, [number, number]> = {
              ArrowLeft: [-passo, 0],
              ArrowRight: [passo, 0],
              ArrowUp: [0, -passo],
              ArrowDown: [0, passo],
            };
            const delta = deslocamento[e.key];
            if (delta) {
              e.preventDefault();
              aoMover(no.id, { x: no.posicao.x + delta[0], y: no.posicao.y + delta[1] });
            }
          }}
        >
          {selo}
          <span className="no-titulo">{no.titulo}</span>
          {no.descricao ? <span className="no-descricao">{no.descricao}</span> : null}
        </button>
      )}
      {editando ? <p className="dica-inline">{t("canvas.editar_dica")}</p> : null}
    </div>
  );
}
