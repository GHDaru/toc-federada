/**
 * Carregar um recurso do serviço com os três estados que toda tela tem de desenhar:
 * carregando, erro e conteúdo (RI-12 da spec 004).
 *
 * Siglas, uma vez: **API** — interface de programação de aplicações.
 *
 * "Estados de carregamento, erro e recusa de autorização são telas desenhadas com próxima
 * ação clara, não texto cru de exceção" — e é por isso que o erro sai daqui como o objeto
 * de erro inteiro (com o seu `codigo`), e não como uma string já formatada: quem traduz é
 * a tela, com o idioma de quem está olhando.
 */
import { useCallback, useEffect, useRef, useState } from "react";

export interface Recurso<T> {
  dado: T | null;
  carregando: boolean;
  erro: unknown;
  recarregar: () => Promise<void>;
  definir: (dado: T) => void;
}

export function useRecurso<T>(buscar: () => Promise<T>, dependencias: unknown[] = []): Recurso<T> {
  const [dado, setDado] = useState<T | null>(null);
  const [carregando, setCarregando] = useState(true);
  const [erro, setErro] = useState<unknown>(null);
  const vivo = useRef(true);

  useEffect(() => {
    vivo.current = true;
    return () => {
      vivo.current = false;
    };
  }, []);

  const recarregar = useCallback(async () => {
    setCarregando(true);
    setErro(null);
    try {
      const resultado = await buscar();
      if (vivo.current) setDado(resultado);
    } catch (falha) {
      if (vivo.current) setErro(falha);
    } finally {
      if (vivo.current) setCarregando(false);
    }
    // `buscar` é recriada a cada render de quem chama; as dependências declaradas por
    // quem usa são a verdade sobre quando recarregar.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, dependencias);

  useEffect(() => {
    void recarregar();
  }, [recarregar]);

  return { dado, carregando, erro, recarregar, definir: setDado };
}
