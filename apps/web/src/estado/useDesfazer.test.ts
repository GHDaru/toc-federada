// O desfazer por EPISÓDIO (RI-06 da spec 004): o botão diz o nome do que vai desfazer, e
// o atalho Ctrl/Cmd+Z faz o mesmo. Navegação (pan, zoom, ajustar) nunca entra na pilha.
import { describe, expect, it, vi } from "vitest";
import { act, renderHook } from "@testing-library/react";
import { useDesfazer } from "./useDesfazer";

describe("pilha de desfazer", () => {
  it("nasce vazia e diz que não há o que desfazer", () => {
    const { result } = renderHook(() => useDesfazer());
    expect(result.current.ultimoEpisodio).toBeNull();
  });

  it("desfaz o último episódio primeiro (pilha, não fila)", async () => {
    const primeiro = vi.fn(async () => {});
    const segundo = vi.fn(async () => {});
    const { result } = renderHook(() => useDesfazer());

    act(() => {
      result.current.registrar("criar_no", primeiro);
      result.current.registrar("mover_no", segundo);
    });
    expect(result.current.ultimoEpisodio).toBe("mover_no");

    await act(async () => {
      await result.current.desfazer();
    });
    expect(segundo).toHaveBeenCalledTimes(1);
    expect(primeiro).not.toHaveBeenCalled();
    expect(result.current.ultimoEpisodio).toBe("criar_no");
  });

  it("desfazer com a pilha vazia é operação silenciosa, não erro", async () => {
    const { result } = renderHook(() => useDesfazer());
    await act(async () => {
      await result.current.desfazer();
    });
    expect(result.current.ultimoEpisodio).toBeNull();
  });

  it("episódio que falha ao desfazer sai da pilha e devolve o erro para a tela", async () => {
    const { result } = renderHook(() => useDesfazer());
    act(() => {
      result.current.registrar("mover_no", async () => {
        throw new Error("o serviço recusou");
      });
    });
    let capturado: unknown = null;
    await act(async () => {
      capturado = await result.current.desfazer().catch((erro) => erro);
    });
    expect((capturado as Error).message).toContain("recusou");
    expect(result.current.ultimoEpisodio).toBeNull();
  });

  it("limpa a pilha ao trocar de projeto — desfazer não atravessa contexto", () => {
    const { result } = renderHook(() => useDesfazer());
    act(() => {
      result.current.registrar("criar_no", async () => {});
      result.current.limpar();
    });
    expect(result.current.ultimoEpisodio).toBeNull();
  });

  it("guarda no máximo os últimos episódios — a pilha não cresce sem fim", () => {
    const { result } = renderHook(() => useDesfazer(2));
    act(() => {
      result.current.registrar("criar_no", async () => {});
      result.current.registrar("mover_no", async () => {});
      result.current.registrar("editar_no", async () => {});
    });
    expect(result.current.tamanho).toBe(2);
  });
});
