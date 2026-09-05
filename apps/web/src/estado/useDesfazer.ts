/**
 * A pilha de desfazer, por **episódio** — o nome do que se desfaz, e a ação que o desfaz.
 *
 * Siglas, uma vez: **RI** — requisito de interface · **API** — interface de programação de
 * aplicações.
 *
 * O RI-06 da spec 004 pede um botão "com o nome do episódio que vai desfazer (ex.:
 * 'Desfazer: mover nó')". Por isso a pilha guarda um par: rótulo e ação. E a ação é um
 * **comando do agregado no servidor** (mover de volta, editar de volta, excluir a aresta
 * recém-criada), nunca uma cópia local do estado: um desfazer que só mexe na tela mente
 * assim que outra pessoa abre o mesmo projeto.
 *
 * O que NÃO entra aqui: navegação (pan, zoom, ajustar à tela), que o mesmo RI-06 exclui, e
 * exclusão de nó ou aresta, que o serviço não sabe reverter — por isso a exclusão pede
 * confirmação com o raio declarado (RI-05) em vez de prometer volta.
 */
import { useCallback, useRef, useState } from "react";

export type NomeDeEpisodio =
  | "criar_no"
  | "mover_no"
  | "editar_no"
  | "ligar"
  | "editar_aresta";

interface Episodio {
  nome: NomeDeEpisodio;
  desfazer: () => Promise<void>;
}

const LIMITE_PADRAO = 30;

export function useDesfazer(limite: number = LIMITE_PADRAO) {
  const pilha = useRef<Episodio[]>([]);
  const [ultimoEpisodio, setUltimo] = useState<NomeDeEpisodio | null>(null);

  const sincronizar = useCallback(() => {
    setUltimo(pilha.current[pilha.current.length - 1]?.nome ?? null);
  }, []);

  const registrar = useCallback(
    (nome: NomeDeEpisodio, desfazer: () => Promise<void>) => {
      pilha.current = [...pilha.current, { nome, desfazer }].slice(-limite);
      sincronizar();
    },
    [limite, sincronizar],
  );

  const desfazer = useCallback(async () => {
    const episodio = pilha.current[pilha.current.length - 1];
    if (!episodio) return;
    // Sai da pilha ANTES de rodar: um desfazer que falha e fica na pilha faz a pessoa
    // tentar de novo para sempre, e o erro real some atrás da repetição.
    pilha.current = pilha.current.slice(0, -1);
    sincronizar();
    await episodio.desfazer();
  }, [sincronizar]);

  const limpar = useCallback(() => {
    pilha.current = [];
    sincronizar();
  }, [sincronizar]);

  return {
    registrar,
    desfazer,
    limpar,
    ultimoEpisodio,
    get tamanho() {
      return pilha.current.length;
    },
  };
}
