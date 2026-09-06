/**
 * O cliente da interface de programação de aplicações (API) do serviço `toc-api`.
 *
 * Siglas, uma vez: **API** — interface de programação de aplicações · **ARA** — Árvore da
 * Realidade Atual · **NC** — Nuvem de Conflito · **UDE** — Efeito Indesejável · **JSON** —
 * *JavaScript Object Notation* · **TRIZ** — Teoria da Resolução Inventiva de Problemas.
 *
 * Três decisões que valem estar escritas:
 *
 * 1. **Um método por comando do agregado.** Não existe `salvarProjeto(estadoInteiro)`. O
 *    `saveProjectState` da 4ª geração (`tocbuilderv3/services/mockApiService.ts:286-301`)
 *    fazia de toda escrita uma substituição cega, e é ele que esta forma aposenta.
 * 2. **Nenhum segredo mora aqui.** O cliente recebe `obterToken()` e o chama a cada
 *    pedido; ele não guarda credencial, não a persiste e não a imprime. A chave de
 *    provedor de modelo que a linhagem inicializava no navegador
 *    (`tocbuilderv3/services/geminiService.ts:16`) não tem equivalente nesta interface, e
 *    não pode ter: a assistência é do servidor, por ação governada (P7 e ADR 0007).
 * 3. **`fetch` entra por parâmetro.** É o que torna o cliente testável sem rede — e o que
 *    permite ao teste provar o cabeçalho, o verbo e a rota de cada comando.
 */
import type {
  AnaliseDeFocalizacao,
  AnaliseResumo,
  Ara,
  ChaveDaAresta,
  EstadoDaPremissa,
  EstadoDoExame,
  Exame,
  ExclusaoDeNo,
  FichaDeUde,
  Geracao,
  Injecao,
  Matriz,
  No,
  Nuvem,
  PapelDaEntidade,
  PedidoDeProposta,
  Posicao,
  Premissa,
  Projeto,
  Proposta,
  ProjetoResumo,
  RelatorioEstrutural,
  Restricao,
  SeparacaoTRIZ,
  Solucao,
  StatusDeInjecao,
  StatusDeValidacao,
  SugestoesDeInjecao,
  SugestoesDePremissa,
  ValidacaoDaNuvem,
  ValidacaoFormal,
  Aresta,
  ConectorLido,
  CicloNaLinha,
  FerramentaVinculada,
  Jornada,
  SugestaoDeRestricao,
  TipoDePasso,
  TipoDeRestricao,
  VereditoDeHeranca,
  VinculoDeFerramenta,
} from "../dominio/tipos";
import type { Sessao } from "../federacao/embarque";
import { ErroDaApi } from "./erros";

export interface OpcoesDoCliente {
  /** Prefixo das rotas. Vazio = mesma origem (o servidor de desenvolvimento faz proxy). */
  base?: string;
  obterToken: () => string | null;
  buscar?: typeof fetch;
}

interface Pedido {
  metodo?: "GET" | "POST" | "PUT" | "PATCH" | "DELETE";
  corpo?: unknown;
}

const seg = (valor: string): string => encodeURIComponent(valor);

export function criarCliente(opcoes: OpcoesDoCliente) {
  const base = opcoes.base ?? "";
  const buscar = opcoes.buscar ?? globalThis.fetch.bind(globalThis);

  async function pedir<T>(caminho: string, pedido: Pedido = {}): Promise<T> {
    const cabecalhos = new Headers({ accept: "application/json" });
    const token = opcoes.obterToken();
    if (token) cabecalhos.set("authorization", `Bearer ${token}`);
    if (pedido.corpo !== undefined) cabecalhos.set("content-type", "application/json");

    let resposta: Response;
    try {
      resposta = await buscar(`${base}${caminho}`, {
        method: pedido.metodo ?? "GET",
        headers: cabecalhos,
        ...(pedido.corpo !== undefined ? { body: JSON.stringify(pedido.corpo) } : {}),
      });
    } catch (erro) {
      // A rede caiu, o serviço não está de pé, o navegador bloqueou. É um fluxo de erro
      // com nome próprio, e a tela precisa desse nome para dizer a próxima ação.
      throw new ErroDaApi(
        "REDE_INDISPONIVEL",
        erro instanceof Error ? erro.message : "falha de rede",
        0,
      );
    }

    if (resposta.status === 204 || resposta.status === 205) return undefined as T;

    const texto = await resposta.text();
    let corpo: unknown = undefined;
    if (texto) {
      try {
        corpo = JSON.parse(texto);
      } catch {
        throw new ErroDaApi(
          "RESPOSTA_INVALIDA",
          `resposta ilegível do serviço (${resposta.status})`,
          resposta.status,
        );
      }
    }

    if (!resposta.ok) {
      const envelope = (corpo as { error?: { code?: string; message?: string; details?: Record<string, unknown> } })?.error;
      if (!envelope?.code) {
        throw new ErroDaApi(
          "RESPOSTA_INVALIDA",
          `o serviço recusou sem o envelope de erro do Anexo A (${resposta.status})`,
          resposta.status,
        );
      }
      throw new ErroDaApi(
        envelope.code,
        envelope.message ?? "",
        resposta.status,
        envelope.details,
      );
    }
    return corpo as T;
  }

  return {
    pedir,

    /** §B.6: o grant de uso único vira sessão. O grant nunca é usado como bearer. */
    async embarcar(grant: string): Promise<Sessao> {
      const bruto = await pedir<{
        sessao: string;
        usuario: { id: string; nome: string };
        tenant_id: string;
        capabilities: string[];
        expira_em: string | null;
      }>("/toc/embarque", { metodo: "POST", corpo: { token: grant } });
      return {
        token: bruto.sessao,
        usuario: bruto.usuario,
        tenantId: bruto.tenant_id,
        capabilities: bruto.capabilities,
        expiraEm: bruto.expira_em,
      };
    },

    saude: () => pedir<Record<string, unknown>>("/saude"),

    projetos: {
      listar: () => pedir<ProjetoResumo[]>("/toc/projetos"),
      lixeira: () => pedir<ProjetoResumo[]>("/toc/projetos/lixeira"),
      abrir: (id: string) => pedir<Projeto>(`/toc/projetos/${seg(id)}`),
      criar: (nome: string, descricao_do_problema = "") =>
        pedir<Projeto>("/toc/projetos", {
          metodo: "POST",
          corpo: { nome, descricao_do_problema },
        }),
      /** Exclusão SUAVE: a linha fica, o estado muda, e a lixeira a mostra (RF-06). */
      excluir: (id: string) =>
        pedir<ProjetoResumo>(`/toc/projetos/${seg(id)}`, { metodo: "DELETE" }),
      restaurar: (id: string) =>
        pedir<ProjetoResumo>(`/toc/projetos/${seg(id)}/restaurar`, { metodo: "POST" }),
    },

    grafo: {
      criarNo: (projeto: string, dados: { titulo: string; descricao?: string; posicao?: Posicao }) =>
        pedir<No>(`/toc/projetos/${seg(projeto)}/nos`, { metodo: "POST", corpo: dados }),
      editarNo: (projeto: string, no: string, dados: { titulo?: string; descricao?: string }) =>
        pedir<No>(`/toc/projetos/${seg(projeto)}/nos/${seg(no)}`, { metodo: "PATCH", corpo: dados }),
      moverNo: (projeto: string, no: string, posicao: Posicao) =>
        pedir<No>(`/toc/projetos/${seg(projeto)}/nos/${seg(no)}`, {
          metodo: "PATCH",
          corpo: { posicao },
        }),
      recolherNo: (projeto: string, no: string, recolhido: boolean) =>
        pedir<No>(`/toc/projetos/${seg(projeto)}/nos/${seg(no)}`, {
          metodo: "PATCH",
          corpo: { recolhido },
        }),
      /** Devolve o RAIO da exclusão: quais arestas saíram junto (RF-15/RI-05). */
      excluirNo: (projeto: string, no: string) =>
        pedir<ExclusaoDeNo>(`/toc/projetos/${seg(projeto)}/nos/${seg(no)}`, { metodo: "DELETE" }),
      ligar: (projeto: string, origem_id: string, destino_id: string, rotulo = "") =>
        pedir<Aresta>(`/toc/projetos/${seg(projeto)}/arestas`, {
          metodo: "POST",
          corpo: { origem_id, destino_id, rotulo },
        }),
      editarAresta: (projeto: string, aresta: string, rotulo: string) =>
        pedir<Aresta>(`/toc/projetos/${seg(projeto)}/arestas/${seg(aresta)}`, {
          metodo: "PATCH",
          corpo: { rotulo },
        }),
      excluirAresta: (projeto: string, aresta: string) =>
        pedir<void>(`/toc/projetos/${seg(projeto)}/arestas/${seg(aresta)}`, { metodo: "DELETE" }),
    },

    ara: {
      /** Função pura do servidor: valida a formulação sem tocar projeto nenhum (RF-06). */
      validarTexto: (texto: string, idioma = "pt") =>
        pedir<ValidacaoFormal>("/toc/ara/validacoes", {
          metodo: "POST",
          corpo: { texto, idioma },
        }),
      criarProjeto: (nome: string, descricao_do_problema = "") =>
        pedir<Projeto>("/toc/ara/projetos", {
          metodo: "POST",
          corpo: { nome, descricao_do_problema },
        }),
      abrir: (projeto: string) => pedir<Ara>(`/toc/ara/projetos/${seg(projeto)}`),
      adicionarEfeito: (
        projeto: string,
        dados: { titulo: string; descricao?: string; posicao?: Posicao },
      ) =>
        pedir<No>(`/toc/ara/projetos/${seg(projeto)}/efeitos`, { metodo: "POST", corpo: dados }),
      /**
       * O grafo da Árvore da Realidade Atual (ARA), pela RAIZ do agregado.
       *
       * Estas seis existem porque a tela chamava `cliente.grafo.*` — as rotas genéricas
       * do Núcleo de Diagramas Lógicos (M1) — para mover, editar, ligar, rotular e
       * apagar dentro de uma ARA. Cada uma dessas chamadas carregava o `Projeto` cru e
       * passava por fora das invariantes do módulo M2: o elo nascia sem exame de
       * suficiência, o Efeito Indesejável sumia sem a ficha ser arquivada, e o conector E
       * ficava apontando para uma aresta que não existia mais. Hoje o servidor recusa
       * essas rotas sobre projeto de ferramenta (`AGGREGATE_ROOT_REQUIRED`), e estas são
       * a porta certa.
       */
      editarNo: (projeto: string, no: string, dados: { titulo?: string; descricao?: string }) =>
        pedir<No>(`/toc/ara/projetos/${seg(projeto)}/nos/${seg(no)}`, {
          metodo: "PATCH",
          corpo: dados,
        }),
      moverNo: (projeto: string, no: string, posicao: Posicao) =>
        pedir<No>(`/toc/ara/projetos/${seg(projeto)}/nos/${seg(no)}`, {
          metodo: "PATCH",
          corpo: { posicao },
        }),
      recolherNo: (projeto: string, no: string, recolhido: boolean) =>
        pedir<No>(`/toc/ara/projetos/${seg(projeto)}/nos/${seg(no)}`, {
          metodo: "PATCH",
          corpo: { recolhido },
        }),
      /** Devolve o RAIO da exclusão: quais arestas saíram junto (RF-15/RI-05). */
      excluirNo: (projeto: string, no: string) =>
        pedir<ExclusaoDeNo>(`/toc/ara/projetos/${seg(projeto)}/nos/${seg(no)}`, {
          metodo: "DELETE",
        }),
      /** O elo nasce COM exame (`nao_examinado`) — é o que faz a suficiência ser dado. */
      ligar: (projeto: string, origem_id: string, destino_id: string, rotulo = "") =>
        pedir<Aresta>(`/toc/ara/projetos/${seg(projeto)}/arestas`, {
          metodo: "POST",
          corpo: { origem_id, destino_id, rotulo },
        }),
      editarAresta: (projeto: string, aresta: string, rotulo: string) =>
        pedir<Aresta>(`/toc/ara/projetos/${seg(projeto)}/arestas/${seg(aresta)}`, {
          metodo: "PATCH",
          corpo: { rotulo },
        }),
      /** Leva junto o exame do elo e a citação dele em conector E (RN-11). */
      excluirAresta: (projeto: string, aresta: string) =>
        pedir<void>(`/toc/ara/projetos/${seg(projeto)}/arestas/${seg(aresta)}`, {
          metodo: "DELETE",
        }),
      marcarUde: (projeto: string, no: string, ficha?: FichaDeUde) =>
        pedir<FichaDeUde>(`/toc/ara/projetos/${seg(projeto)}/nos/${seg(no)}/ude`, {
          metodo: "POST",
          corpo: { ficha: ficha ?? null },
        }),
      desmarcarUde: (projeto: string, no: string) =>
        pedir<void>(`/toc/ara/projetos/${seg(projeto)}/nos/${seg(no)}/ude`, { metodo: "DELETE" }),
      editarFicha: (projeto: string, no: string, ficha: FichaDeUde) =>
        pedir<FichaDeUde>(`/toc/ara/projetos/${seg(projeto)}/nos/${seg(no)}/ficha`, {
          metodo: "PUT",
          corpo: ficha,
        }),
      /** Editar o texto REEXECUTA a validação formal no mesmo comando (RF-10). */
      reformular: (projeto: string, no: string, texto: string) =>
        pedir<No>(`/toc/ara/projetos/${seg(projeto)}/nos/${seg(no)}/reformulacoes`, {
          metodo: "POST",
          corpo: { texto },
        }),
      /** O autor é o principal do servidor — nunca vem daqui (RF-16). */
      registrarParecer: (
        projeto: string,
        no: string,
        parecer: { favoravel: boolean; justificativa: string; criterios?: string[] },
      ) =>
        pedir<void>(`/toc/ara/projetos/${seg(projeto)}/nos/${seg(no)}/pareceres`, {
          metodo: "POST",
          corpo: parecer,
        }),
      mudarStatus: (projeto: string, no: string, status: StatusDeValidacao, justificativa = "") =>
        pedir<{ no_id: string; status: StatusDeValidacao }>(
          `/toc/ara/projetos/${seg(projeto)}/nos/${seg(no)}/status`,
          { metodo: "PUT", corpo: { status, justificativa } },
        ),
      examinarElo: (projeto: string, aresta: string, estado: EstadoDoExame, reserva = "") =>
        pedir<Exame>(`/toc/ara/projetos/${seg(projeto)}/arestas/${seg(aresta)}/exame`, {
          metodo: "PUT",
          corpo: { estado, reserva },
        }),
      formarConector: (projeto: string, arestas: string[]) =>
        pedir<ConectorLido>(`/toc/ara/projetos/${seg(projeto)}/conectores`, {
          metodo: "POST",
          corpo: { arestas },
        }),
      desfazerConector: (projeto: string, conector: string) =>
        pedir<void>(`/toc/ara/projetos/${seg(projeto)}/conectores/${seg(conector)}`, {
          metodo: "DELETE",
        }),
      analisar: (projeto: string) =>
        pedir<RelatorioEstrutural>(`/toc/ara/projetos/${seg(projeto)}/analises`, {
          metodo: "POST",
        }),
    },

    /**
     * O gate humano, do lado da interface (spec 006, RI-01).
     *
     * **Aceitar não escreve.** Quem escreve é a proposta de ação que atravessa a máquina
     * de estados no servidor; estes dois métodos são a porta dela para esta tela — criar
     * (a proposta nasce e espera) e decidir (confirmar executa, recusar encerra). As duas
     * deixam traço, inclusive a recusa.
     *
     * Não existe aqui um `aplicarGeracao(...)` que grave direto, e a ausência é o
     * requisito: era assim que a 4ª geração da linhagem fazia — a resposta do modelo,
     * pedida do navegador, ia direto para o estado da tela.
     */
    propostas: {
      criar: (pedido: PedidoDeProposta) =>
        pedir<Proposta>("/toc/propostas", {
          metodo: "POST",
          corpo: {
            action_id: pedido.action_id,
            args: pedido.args,
            // `origem` é DADO sobre a procedência do conteúdo (APH-5.9), nunca desvio de
            // fluxo: o padrão é `ia` porque esta porta existe para o conteúdo assistido.
            origem: pedido.origem ?? "ia",
            ...(pedido.contexto_hash ? { contexto_hash: pedido.contexto_hash } : {}),
          },
        }),
      decidir: (proposta: string, aprovado: boolean) =>
        pedir<Proposta>(`/toc/propostas/${seg(proposta)}/decisao`, {
          metodo: "POST",
          corpo: { aprovado },
        }),
    },

    nc: {
      criarProjeto: (nome: string, descricao_do_problema = "") =>
        pedir<Nuvem>("/toc/nc/projetos", {
          metodo: "POST",
          corpo: { nome, descricao_do_problema },
        }),
      /** O encadeamento que nenhuma geração da linhagem teve: UDEs da ARA viram dilema. */
      derivar: (ara_projeto_id: string, no_ids: string[], nome: string) =>
        pedir<Nuvem>("/toc/nc/derivacoes", {
          metodo: "POST",
          corpo: { ara_projeto_id, no_ids, nome },
        }),
      abrir: (projeto: string) => pedir<Nuvem>(`/toc/nc/projetos/${seg(projeto)}`),
      validacao: (projeto: string) =>
        pedir<ValidacaoDaNuvem>(`/toc/nc/projetos/${seg(projeto)}/validacao`),
      solucao: (projeto: string) => pedir<Solucao>(`/toc/nc/projetos/${seg(projeto)}/solucao`),
      matriz: (projeto: string) => pedir<Matriz>(`/toc/nc/projetos/${seg(projeto)}/matriz`),
      editarEntidade: (projeto: string, papel: PapelDaEntidade, texto: string) =>
        pedir<Nuvem>(`/toc/nc/projetos/${seg(projeto)}/entidades/${seg(papel)}`, {
          metodo: "PUT",
          corpo: { texto },
        }),
      editarRacional: (projeto: string, racional: string) =>
        pedir<Nuvem>(`/toc/nc/projetos/${seg(projeto)}/racional`, {
          metodo: "PUT",
          corpo: { racional },
        }),
      registrarPremissa: (projeto: string, chave: ChaveDaAresta, texto: string) =>
        pedir<Premissa>(`/toc/nc/projetos/${seg(projeto)}/arestas/${seg(chave)}/premissas`, {
          metodo: "POST",
          corpo: { texto },
        }),
      editarPremissa: (projeto: string, premissa: string, texto: string) =>
        pedir<Premissa>(`/toc/nc/projetos/${seg(projeto)}/premissas/${seg(premissa)}`, {
          metodo: "PUT",
          corpo: { texto },
        }),
      reordenarPremissas: (projeto: string, chave: ChaveDaAresta, ordem: string[]) =>
        pedir<Premissa[]>(
          `/toc/nc/projetos/${seg(projeto)}/arestas/${seg(chave)}/premissas/ordem`,
          { metodo: "PUT", corpo: { ordem } },
        ),
      /** Desafiar exige justificativa; revigorar é o caminho de volta (RF-13). */
      mudarEstadoDaPremissa: (
        projeto: string,
        premissa: string,
        estado: EstadoDaPremissa,
        justificativa = "",
      ) =>
        pedir<Premissa>(`/toc/nc/projetos/${seg(projeto)}/premissas/${seg(premissa)}/estado`, {
          metodo: "PUT",
          corpo: { estado, justificativa },
        }),
      arquivarPremissa: (projeto: string, premissa: string) =>
        pedir<{ premissa_id: string; injecoes_arquivadas: number }>(
          `/toc/nc/projetos/${seg(projeto)}/premissas/${seg(premissa)}`,
          { metodo: "DELETE" },
        ),
      registrarInjecao: (
        projeto: string,
        premissa: string,
        texto: string,
        separacao: SeparacaoTRIZ | null = null,
      ) =>
        pedir<Injecao>(`/toc/nc/projetos/${seg(projeto)}/premissas/${seg(premissa)}/injecoes`, {
          metodo: "POST",
          corpo: { texto, separacao },
        }),
      editarInjecao: (projeto: string, injecao: string, texto: string) =>
        pedir<Injecao>(`/toc/nc/projetos/${seg(projeto)}/injecoes/${seg(injecao)}`, {
          metodo: "PUT",
          corpo: { texto },
        }),
      classificarInjecao: (projeto: string, injecao: string, separacao: SeparacaoTRIZ | null) =>
        pedir<Injecao>(`/toc/nc/projetos/${seg(projeto)}/injecoes/${seg(injecao)}/separacao`, {
          metodo: "PUT",
          corpo: { separacao },
        }),
      mudarStatusDaInjecao: (
        projeto: string,
        injecao: string,
        status: StatusDeInjecao,
        justificativa = "",
      ) =>
        pedir<Injecao>(`/toc/nc/projetos/${seg(projeto)}/injecoes/${seg(injecao)}/status`, {
          metodo: "PUT",
          corpo: { status, justificativa },
        }),
      /** Gerar NÃO aplica: devolve pré-visualização e o `action_id` da ação governada. */
      gerar: (projeto: string, narrativa: string) =>
        pedir<Geracao>(`/toc/nc/projetos/${seg(projeto)}/geracoes`, {
          metodo: "POST",
          corpo: { narrativa },
        }),
      sugerirPremissas: (projeto: string, chave: ChaveDaAresta, narrativa = "") =>
        pedir<SugestoesDePremissa>(
          `/toc/nc/projetos/${seg(projeto)}/arestas/${seg(chave)}/sugestoes/premissas`,
          { metodo: "POST", corpo: { narrativa } },
        ),
      sugerirInjecoes: (projeto: string, premissa: string) =>
        pedir<SugestoesDeInjecao>(
          `/toc/nc/projetos/${seg(projeto)}/premissas/${seg(premissa)}/sugestoes/injecoes`,
          { metodo: "POST" },
        ),
    },

    /**
     * M6 — a jornada dos cinco passos de focalização (spec 009).
     *
     * Um método por comando do agregado, como no resto deste cliente: não existe
     * `salvarJornada(estadoInteiro)`. Concluir um passo é `POST …/conclusao`; anotar é
     * `POST …/notas`; recomeçar é `POST …/recomecos`. A diferença não é estética — é o
     * que faz o servidor recusar o que tem de recusar, com a regra nomeada, em vez de
     * receber um retrato e gravá-lo.
     */
    foco: {
      criarAnalise: (nome: string, sistema: string, descricao_do_sistema = "") =>
        pedir<AnaliseDeFocalizacao>("/toc/focalizacao/analises", {
          metodo: "POST",
          corpo: { nome, sistema, descricao_do_sistema },
        }),
      listar: () => pedir<AnaliseResumo[]>("/toc/focalizacao/analises"),
      abrir: (projeto: string) =>
        pedir<AnaliseDeFocalizacao>(`/toc/focalizacao/analises/${seg(projeto)}`),
      excluir: (projeto: string) =>
        pedir<AnaliseDeFocalizacao>(`/toc/focalizacao/analises/${seg(projeto)}`, {
          metodo: "DELETE",
        }),
      restaurar: (projeto: string) =>
        pedir<AnaliseDeFocalizacao>(`/toc/focalizacao/analises/${seg(projeto)}/restauracao`, {
          metodo: "POST",
        }),
      /** O ciclo FECHADO abre por aqui, e o servidor é quem diz que é somente leitura. */
      jornada: (projeto: string, ciclo?: string) =>
        pedir<Jornada>(
          `/toc/focalizacao/analises/${seg(projeto)}/jornada` +
            (ciclo ? `?ciclo_id=${seg(ciclo)}` : ""),
        ),
      linhaDoTempo: (projeto: string) =>
        pedir<CicloNaLinha[]>(`/toc/focalizacao/analises/${seg(projeto)}/linha-do-tempo`),
      registrarRestricao: (
        projeto: string,
        corpo: {
          descricao: string;
          tipo: TipoDeRestricao;
          justificativa: string;
          autor: string;
          origem?: { ferramenta: string; projeto_id: string; no_id: string } | null;
        },
      ) =>
        pedir<Restricao>(`/toc/focalizacao/analises/${seg(projeto)}/restricao`, {
          metodo: "POST",
          corpo,
        }),
      /** RF-07: **sem `tipo`** — trocar o alvo da análise é recomeçar, não editar (RN-03). */
      editarRestricao: (
        projeto: string,
        campos: { descricao?: string; justificativa?: string },
      ) =>
        pedir<Restricao>(`/toc/focalizacao/analises/${seg(projeto)}/restricao`, {
          metodo: "PUT",
          corpo: campos,
        }),
      concluirPasso: (projeto: string, passo: TipoDePasso, decisao: string, autor: string) =>
        pedir<Jornada>(
          `/toc/focalizacao/analises/${seg(projeto)}/passos/${seg(passo)}/conclusao`,
          { metodo: "POST", corpo: { decisao, autor } },
        ),
      reabrirAnterior: (projeto: string, justificativa: string, autor: string) =>
        pedir<Jornada>(`/toc/focalizacao/analises/${seg(projeto)}/reaberturas`, {
          metodo: "POST",
          corpo: { justificativa, autor },
        }),
      anotar: (projeto: string, passo: TipoDePasso, texto: string, autor: string) =>
        pedir<Jornada>(`/toc/focalizacao/analises/${seg(projeto)}/passos/${seg(passo)}/notas`, {
          metodo: "POST",
          corpo: { texto, autor },
        }),
      vincular: (
        projeto: string,
        passo: TipoDePasso,
        corpo: {
          ferramenta: FerramentaVinculada;
          projeto_id: string;
          papel?: string;
          justificativa?: string;
        },
      ) =>
        pedir<VinculoDeFerramenta>(
          `/toc/focalizacao/analises/${seg(projeto)}/passos/${seg(passo)}/vinculos`,
          { metodo: "POST", corpo },
        ),
      removerVinculo: (projeto: string, passo: TipoDePasso, vinculo: string) =>
        pedir<Jornada>(
          `/toc/focalizacao/analises/${seg(projeto)}/passos/${seg(passo)}/vinculos/${seg(vinculo)}`,
          { metodo: "DELETE" },
        ),
      /** RN-05: `mantida` e `revogada`, as duas com justificativa. `pendente` não entra. */
      julgarHeranca: (
        projeto: string,
        decisao: string,
        veredito: Exclude<VereditoDeHeranca, "pendente">,
        justificativa: string,
        autor: string,
      ) =>
        pedir<Jornada>(
          `/toc/focalizacao/analises/${seg(projeto)}/heranca/${seg(decisao)}/veredito`,
          { metodo: "POST", corpo: { veredito, justificativa, autor } },
        ),
      recomecar: (projeto: string) =>
        pedir<AnaliseDeFocalizacao>(`/toc/focalizacao/analises/${seg(projeto)}/recomecos`, {
          metodo: "POST",
        }),
      /** Sugerir NÃO aplica: devolve as candidatas e o `action_id` da ação governada. */
      sugerirRestricao: (projeto: string) =>
        pedir<SugestaoDeRestricao>(
          `/toc/focalizacao/analises/${seg(projeto)}/sugestoes-de-restricao`,
          { metodo: "POST" },
        ),
    },
  };
}

export type Cliente = ReturnType<typeof criarCliente>;
