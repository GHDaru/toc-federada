/**
 * A janela de visão do canvas: deslocamento (pan), aproximação (zoom) e "ajustar à tela".
 *
 * Siglas, uma vez: **RI** — requisito de interface · **ARA** — Árvore da Realidade Atual.
 *
 * **Navegação não entra na pilha de desfazer** (RI-03 da spec 004). Por isso a janela de
 * visão vive aqui, em estado local, e não passa por comando nenhum do agregado: mover a
 * câmera não é mover o nó, e um desfazer que devolvesse o zoom faria a pessoa perder a
 * edição que ela queria desfazer.
 */
import { useCallback, useRef, useState, type RefObject } from "react";
import type { No, Posicao } from "../../dominio/tipos";

export interface JanelaDeVisao {
  x: number;
  y: number;
  zoom: number;
}

export const ZOOM_MINIMO = 0.2;
export const ZOOM_MAXIMO = 2;
export const PASSO_DE_ZOOM = 1.2;

/** Tamanho de referência quando o navegador ainda não mediu o elemento (e nos testes). */
const LARGURA_PADRAO = 900;
const ALTURA_PADRAO = 600;
export const LARGURA_DO_NO = 240;
export const ALTURA_DO_NO = 92;

function medir(elemento: HTMLElement | null): { largura: number; altura: number } {
  const retangulo = elemento?.getBoundingClientRect();
  return {
    largura: retangulo && retangulo.width > 0 ? retangulo.width : LARGURA_PADRAO,
    altura: retangulo && retangulo.height > 0 ? retangulo.height : ALTURA_PADRAO,
  };
}

export function useViewport(referencia: RefObject<HTMLElement | null>) {
  const [janela, setJanela] = useState<JanelaDeVisao>({ x: 40, y: 40, zoom: 1 });
  const arrastando = useRef(false);
  const ultimo = useRef<Posicao>({ x: 0, y: 0 });

  const daTelaParaOPlano = useCallback(
    (posicao: Posicao): Posicao => {
      const retangulo = referencia.current?.getBoundingClientRect();
      const esquerda = retangulo?.left ?? 0;
      const topo = retangulo?.top ?? 0;
      return {
        x: (posicao.x - esquerda - janela.x) / janela.zoom,
        y: (posicao.y - topo - janela.y) / janela.zoom,
      };
    },
    [janela, referencia],
  );

  const comecarPan = useCallback((evento: { button: number; clientX: number; clientY: number }) => {
    if (evento.button !== 0) return;
    arrastando.current = true;
    ultimo.current = { x: evento.clientX, y: evento.clientY };
  }, []);

  const moverPan = useCallback((evento: { clientX: number; clientY: number }) => {
    if (!arrastando.current) return;
    const dx = evento.clientX - ultimo.current.x;
    const dy = evento.clientY - ultimo.current.y;
    ultimo.current = { x: evento.clientX, y: evento.clientY };
    setJanela((atual) => ({ ...atual, x: atual.x + dx, y: atual.y + dy }));
  }, []);

  const terminarPan = useCallback(() => {
    arrastando.current = false;
  }, []);

  const aplicarZoom = useCallback(
    (fator: number, centro?: Posicao) => {
      setJanela((atual) => {
        const novo = Math.min(ZOOM_MAXIMO, Math.max(ZOOM_MINIMO, atual.zoom * fator));
        const { largura, altura } = medir(referencia.current);
        const alvo = centro ?? { x: largura / 2, y: altura / 2 };
        return {
          zoom: novo,
          x: alvo.x - (alvo.x - atual.x) * (novo / atual.zoom),
          y: alvo.y - (alvo.y - atual.y) * (novo / atual.zoom),
        };
      });
    },
    [referencia],
  );

  const aoGirarRoda = useCallback(
    (evento: { deltaY: number; clientX: number; clientY: number; preventDefault(): void }) => {
      evento.preventDefault();
      const retangulo = referencia.current?.getBoundingClientRect();
      aplicarZoom(Math.pow(1 - 0.001, evento.deltaY), {
        x: evento.clientX - (retangulo?.left ?? 0),
        y: evento.clientY - (retangulo?.top ?? 0),
      });
    },
    [aplicarZoom, referencia],
  );

  /** "Ajustar à tela": enquadra todos os nós com uma margem. Sem nó, volta ao começo. */
  const ajustar = useCallback(
    (nos: readonly No[]) => {
      const { largura, altura } = medir(referencia.current);
      if (!nos.length) {
        setJanela({ x: 40, y: 40, zoom: 1 });
        return;
      }
      const xs = nos.map((n) => n.posicao.x);
      const ys = nos.map((n) => n.posicao.y);
      const minX = Math.min(...xs);
      const minY = Math.min(...ys);
      const maxX = Math.max(...xs) + LARGURA_DO_NO;
      const maxY = Math.max(...ys) + ALTURA_DO_NO;
      const margem = 48;
      const zoom = Math.min(
        ZOOM_MAXIMO,
        Math.max(
          ZOOM_MINIMO,
          Math.min((largura - margem * 2) / (maxX - minX), (altura - margem * 2) / (maxY - minY)),
        ),
      );
      setJanela({
        zoom,
        x: margem - minX * zoom + (largura - margem * 2 - (maxX - minX) * zoom) / 2,
        y: margem - minY * zoom + (altura - margem * 2 - (maxY - minY) * zoom) / 2,
      });
    },
    [referencia],
  );

  const focar = useCallback(
    (no: No) => {
      const { largura, altura } = medir(referencia.current);
      setJanela((atual) => ({
        zoom: atual.zoom,
        x: largura / 2 - (no.posicao.x + LARGURA_DO_NO / 2) * atual.zoom,
        y: altura / 2 - (no.posicao.y + ALTURA_DO_NO / 2) * atual.zoom,
      }));
    },
    [referencia],
  );

  return {
    janela,
    daTelaParaOPlano,
    comecarPan,
    moverPan,
    terminarPan,
    aplicarZoom,
    aoGirarRoda,
    ajustar,
    focar,
  };
}
