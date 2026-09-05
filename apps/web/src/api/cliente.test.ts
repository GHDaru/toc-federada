// O cliente da interface de programação de aplicações (API) do serviço.
//
// Persistência REAL: esta é a diferença mais crua entre esta interface e a 4ª geração da
// linhagem, cujo `saveProjectState` gravava o projeto inteiro num mapa em memória do
// navegador (`tocbuilderv3/services/mockApiService.ts`). Aqui cada comando é uma rota
// nomeada do agregado, e quem guarda é o PostgreSQL do serviço.
import { describe, expect, it, vi } from "vitest";
import { criarCliente } from "./cliente";
import { ErroDaApi } from "./erros";

function respostaJson(corpo: unknown, status = 200) {
  return new Response(JSON.stringify(corpo), {
    status,
    headers: { "content-type": "application/json" },
  });
}

function clienteCom(buscar: typeof fetch, token: string | null = "ses-abc") {
  return criarCliente({ base: "", obterToken: () => token, buscar });
}

describe("cliente da API", () => {
  it("apresenta a identidade por Bearer no cabeçalho Authorization", async () => {
    const buscar = vi.fn(async () => respostaJson([]));
    await clienteCom(buscar as unknown as typeof fetch).projetos.listar();
    const [url, opcoes] = buscar.mock.calls[0] as unknown as [string, RequestInit];
    expect(url).toBe("/toc/projetos");
    expect(new Headers(opcoes.headers).get("authorization")).toBe("Bearer ses-abc");
  });

  it("omite o cabeçalho quando não há sessão — 401 é resposta, não exceção nossa", async () => {
    const buscar = vi.fn(async () => respostaJson([]));
    await clienteCom(buscar as unknown as typeof fetch, null).projetos.listar();
    const [, opcoes] = buscar.mock.calls[0] as unknown as [string, RequestInit];
    expect(new Headers(opcoes.headers).has("authorization")).toBe(false);
  });

  it("traduz o envelope de erro do Anexo A pelo CÓDIGO, nunca pela mensagem", async () => {
    const buscar = vi.fn(async () =>
      respostaJson(
        {
          error: {
            code: "UNAUTHORIZED",
            message: "a operação AdicionarNo exige a capability toc:write",
            details: { capacidade: "toc:write", operacao: "AdicionarNo" },
          },
        },
        403,
      ),
    );
    const cliente = clienteCom(buscar as unknown as typeof fetch);
    const erro = await cliente.projetos.listar().catch((e) => e);
    expect(erro).toBeInstanceOf(ErroDaApi);
    expect(erro.codigo).toBe("UNAUTHORIZED");
    expect(erro.status).toBe(403);
    expect(erro.detalhes).toEqual({ capacidade: "toc:write", operacao: "AdicionarNo" });
  });

  it("dá código próprio quando a rede cai — o fluxo de erro tem de ter nome", async () => {
    const buscar = vi.fn(async () => {
      throw new TypeError("Failed to fetch");
    });
    const erro = await clienteCom(buscar as unknown as typeof fetch)
      .projetos.listar()
      .catch((e) => e);
    expect(erro).toBeInstanceOf(ErroDaApi);
    expect(erro.codigo).toBe("REDE_INDISPONIVEL");
  });

  it("dá código próprio quando a resposta não é o envelope esperado", async () => {
    const buscar = vi.fn(
      async () => new Response("<html>502</html>", { status: 502, headers: { "content-type": "text/html" } }),
    );
    const erro = await clienteCom(buscar as unknown as typeof fetch)
      .projetos.listar()
      .catch((e) => e);
    expect(erro.codigo).toBe("RESPOSTA_INVALIDA");
    expect(erro.status).toBe(502);
  });

  it("aceita 204 sem corpo sem tentar interpretar JSON", async () => {
    const buscar = vi.fn(async () => new Response(null, { status: 204 }));
    await expect(
      clienteCom(buscar as unknown as typeof fetch).grafo.excluirAresta("p1", "a1"),
    ).resolves.toBeUndefined();
  });

  it("monta cada comando na sua rota e no seu verbo", async () => {
    const buscar = vi.fn(async () => respostaJson({}));
    const cliente = clienteCom(buscar as unknown as typeof fetch);
    await cliente.grafo.criarNo("p1", { titulo: "Entrega atrasa" });
    await cliente.grafo.moverNo("p1", "n1", { x: 10, y: 20 });
    await cliente.grafo.excluirNo("p1", "n1");
    await cliente.ara.validarTexto("O prazo é perdido.", "pt");
    await cliente.nc.editarEntidade("p2", "D", "reter o especialista");
    const chamadas = buscar.mock.calls.map((c) => [
      (c as unknown as [string, RequestInit])[0],
      ((c as unknown as [string, RequestInit])[1].method ?? "GET"),
    ]);
    expect(chamadas).toEqual([
      ["/toc/projetos/p1/nos", "POST"],
      ["/toc/projetos/p1/nos/n1", "PATCH"],
      ["/toc/projetos/p1/nos/n1", "DELETE"],
      ["/toc/ara/validacoes", "POST"],
      ["/toc/nc/projetos/p2/entidades/D", "PUT"],
    ]);
  });

  it("troca o grant por sessão em POST /toc/embarque e devolve a identidade", async () => {
    const buscar = vi.fn(async () =>
      respostaJson(
        {
          sessao: "ses-nova",
          usuario: { id: "usr-facilitadora", nome: "Facilitadora TOC" },
          tenant_id: "inq-horizonte",
          capabilities: ["toc:read"],
          expira_em: null,
        },
        201,
      ),
    );
    const sessao = await clienteCom(buscar as unknown as typeof fetch, null).embarcar("ghdg_x");
    const [url, opcoes] = buscar.mock.calls[0] as unknown as [string, RequestInit];
    expect(url).toBe("/toc/embarque");
    expect(JSON.parse(String(opcoes.body))).toEqual({ token: "ghdg_x" });
    expect(sessao).toEqual({
      token: "ses-nova",
      usuario: { id: "usr-facilitadora", nome: "Facilitadora TOC" },
      tenantId: "inq-horizonte",
      capabilities: ["toc:read"],
      expiraEm: null,
    });
  });

  it("codifica o caminho: identificador com barra não vira rota nova", async () => {
    const buscar = vi.fn(async () => respostaJson({}));
    await clienteCom(buscar as unknown as typeof fetch).projetos.abrir("p1/../admin");
    const [url] = buscar.mock.calls[0] as unknown as [string];
    expect(url).toBe("/toc/projetos/p1%2F..%2Fadmin");
  });

  it("não guarda segredo nenhum: o token vem de fora a cada chamada", async () => {
    let atual: string | null = "ses-1";
    const buscar = vi.fn(async () => respostaJson([]));
    const cliente = criarCliente({
      base: "",
      obterToken: () => atual,
      buscar: buscar as unknown as typeof fetch,
    });
    await cliente.projetos.listar();
    atual = "ses-2";
    await cliente.projetos.listar();
    const cabecalhos = buscar.mock.calls.map((c) =>
      new Headers((c as unknown as [string, RequestInit])[1].headers).get("authorization"),
    );
    expect(cabecalhos).toEqual(["Bearer ses-1", "Bearer ses-2"]);
  });
});
