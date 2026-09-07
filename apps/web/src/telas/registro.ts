/**
 * O registro de telas — a mesma declaração que o serviço mantém em
 * `apps/api/src/toc_api/dominio/federacao/telas.py`, do lado da interface.
 *
 * Siglas, uma vez: **APH** — Aplicação ↔ Harness · **IA** — inteligência artificial ·
 * **DOM** — *Document Object Model* · **ARA** — Árvore da Realidade Atual · **UDE** —
 * Efeito Indesejável · **NC** — Nuvem de Conflito.
 *
 * Por que existe dos dois lados: o APH-3.1 manda que a assistência **nunca infira a
 * interface** — nada de raspar DOM, nada de ler captura de tela. Ela sabe onde a pessoa
 * está porque a tela está declarada. O serviço monta o snapshot a partir do registro
 * dele; a interface roteia a partir deste. Um teste compara os dois com o manifesto
 * publicado, que é o que impede a dupla de divergir em silêncio.
 *
 * **`aiVisivel` é declarado campo a campo, e o padrão é não visível** (RF-01 da spec 002):
 * cada `true` carrega justificativa escrita. Ausência de declaração seria "esqueci", e
 * "esqueci" é como dado sensível vaza para um modelo.
 */

export type AcaoDeIa = "READ" | "FILL_FIELDS" | "SUBMIT" | "NAVIGATE";
export type TipoDeCampo = "text" | "number" | "boolean" | "date" | "select" | "entity" | "other";

export interface CampoDeTela {
  nome: string;
  tipo: TipoDeCampo;
  rotulo: string;
  aiVisivel: boolean;
  /** Obrigatória quando `aiVisivel` é verdadeiro. Vazia quando é falso. */
  justificativa: string;
}

export interface Tela {
  id: string;
  rota: string;
  titulo: string;
  acoesDeIa: readonly AcaoDeIa[];
  campos: readonly CampoDeTela[];
  /**
   * Se esta tela está no manifesto publicado. A Nuvem de Conflito ainda **não** está: o
   * manifesto do ciclo 006 declara quatro telas, e acrescentar a quinta é mudança de
   * manifesto — que passa por gate de admissão, não por decisão de quem escreve a tela.
   * Enquanto isso, ela é rota da interface e **não** é superfície de snapshot.
   */
  declaradaNoManifesto: boolean;
}

export const REGISTRO_DE_TELAS: readonly Tela[] = [
  {
    id: "toc.projetos",
    rota: "/toc/projetos",
    titulo: "Projetos",
    acoesDeIa: ["READ", "NAVIGATE"],
    declaradaNoManifesto: true,
    campos: [
      {
        nome: "filtro_ferramenta",
        tipo: "text",
        rotulo: "Ferramenta",
        aiVisivel: true,
        justificativa: "é um filtro de navegação, sem conteúdo de análise",
      },
      {
        nome: "quantidade_de_projetos",
        tipo: "number",
        rotulo: "Projetos listados",
        aiVisivel: true,
        justificativa: "contagem agregada, sem nome nem texto de projeto",
      },
      {
        nome: "projeto_selecionado",
        tipo: "entity",
        rotulo: "Projeto selecionado",
        aiVisivel: true,
        justificativa: "referência ao projeto aberto, necessária para a ação `toc.*` saber o alvo",
      },
    ],
  },
  {
    id: "toc.ara",
    rota: "/toc/ara",
    titulo: "Arvore da Realidade Atual",
    acoesDeIa: ["READ", "FILL_FIELDS", "SUBMIT", "NAVIGATE"],
    declaradaNoManifesto: true,
    campos: [
      {
        nome: "projeto_id",
        tipo: "text",
        rotulo: "Projeto",
        aiVisivel: true,
        justificativa: "identifica o alvo das ações governadas da ARA",
      },
      {
        nome: "nos_visiveis",
        tipo: "number",
        rotulo: "Nós visíveis",
        aiVisivel: true,
        justificativa: "tamanho da árvore em tela; agregado, sem texto de nó",
      },
      {
        nome: "no_selecionado",
        tipo: "entity",
        rotulo: "Nó selecionado",
        aiVisivel: true,
        justificativa: "o que a pessoa está olhando — é o contexto da proposta",
      },
      {
        nome: "rascunho_de_parecer",
        tipo: "text",
        rotulo: "Rascunho de parecer",
        aiVisivel: false,
        justificativa: "",
      },
    ],
  },
  // M4 — Árvores de Futuro e Implementação (spec 008, INT-09). As cinco telas estão no
  // manifesto publicado do ciclo 006 desde que ele nasceu — o serviço já as declarava em
  // `apps/api/src/toc_api/dominio/federacao/telas.py:150-217` e a interface não. Enquanto
  // faltaram aqui, o teste de paridade `registro.test.ts` ficava vermelho: o snapshot
  // podia nomear uma tela que a interface não sabia desenhar. O `aiVisivel` de cada campo
  // é o do serviço, campo a campo, com a justificativa que lá está em comentário.
  {
    id: "toc.arf_canvas",
    rota: "/toc/arf",
    titulo: "Arvore da Realidade Futura",
    acoesDeIa: ["READ", "FILL_FIELDS", "SUBMIT", "NAVIGATE"],
    declaradaNoManifesto: true,
    campos: [
      {
        nome: "projeto_id",
        tipo: "text",
        rotulo: "Projeto",
        aiVisivel: true,
        justificativa: "identifica o alvo das ações governadas da árvore de futuro",
      },
      {
        nome: "injecoes",
        tipo: "number",
        rotulo: "Injeções",
        aiVisivel: true,
        justificativa: "quantas injeções a árvore tem; agregado, sem o texto de nenhuma",
      },
      {
        nome: "efeitos_futuros",
        tipo: "number",
        rotulo: "Efeitos futuros",
        aiVisivel: true,
        justificativa: "tamanho da árvore em tela; agregado, sem texto de efeito",
      },
      {
        nome: "no_selecionado",
        tipo: "entity",
        rotulo: "Nó selecionado",
        aiVisivel: true,
        justificativa: "o que a pessoa está olhando — é o contexto da proposta",
      },
      {
        nome: "ramos_abertos",
        tipo: "number",
        rotulo: "Ramos negativos abertos",
        aiVisivel: true,
        justificativa: "quantos efeitos colaterais seguem sem poda nem aceite; contagem",
      },
      // A justificativa de um ramo ACEITO é a decisão de alguém de conviver com um efeito
      // colateral. É registro de responsabilidade, e mandá-la ao modelo faria da
      // assistência juíza da decisão — não é o papel dela.
      {
        nome: "justificativa_do_aceite",
        tipo: "text",
        rotulo: "Justificativa do aceite",
        aiVisivel: false,
        justificativa: "",
      },
    ],
  },
  {
    id: "toc.apr_canvas",
    rota: "/toc/apr",
    titulo: "Arvore de Pre-Requisitos",
    acoesDeIa: ["READ", "FILL_FIELDS", "SUBMIT", "NAVIGATE"],
    declaradaNoManifesto: true,
    campos: [
      {
        nome: "projeto_id",
        tipo: "text",
        rotulo: "Projeto",
        aiVisivel: true,
        justificativa: "identifica o alvo das ações governadas da árvore de pré-requisitos",
      },
      {
        nome: "objetivo",
        tipo: "text",
        rotulo: "Objetivo",
        aiVisivel: true,
        justificativa: "o topo da árvore é o enunciado do que se quer — é o contexto sem o qual obstáculo nenhum faz sentido",
      },
      {
        nome: "obstaculos",
        tipo: "number",
        rotulo: "Obstáculos",
        aiVisivel: true,
        justificativa: "quantos obstáculos foram levantados; agregado, sem o texto de nenhum",
      },
      {
        nome: "objetivos_intermediarios",
        tipo: "number",
        rotulo: "Objetivos intermediários",
        aiVisivel: true,
        justificativa: "quantos obstáculos já têm superação escrita; agregado",
      },
      {
        nome: "no_selecionado",
        tipo: "entity",
        rotulo: "Nó selecionado",
        aiVisivel: true,
        justificativa: "o que a pessoa está olhando — é o contexto da proposta",
      },
      // O julgamento do teste de validade é humano por regra (RN-07 da spec 008). Em
      // rascunho, é opinião ainda não registrada — a mesma decisão do rascunho de parecer.
      {
        nome: "rascunho_de_julgamento",
        tipo: "text",
        rotulo: "Rascunho de julgamento",
        aiVisivel: false,
        justificativa: "",
      },
    ],
  },
  {
    id: "toc.apr_sequencia",
    rota: "/toc/apr/sequencia",
    titulo: "Sequenciamento da Arvore de Pre-Requisitos",
    acoesDeIa: ["READ", "NAVIGATE"],
    declaradaNoManifesto: true,
    campos: [
      {
        nome: "projeto_id",
        tipo: "text",
        rotulo: "Projeto",
        aiVisivel: true,
        justificativa: "identifica a árvore cujo sequenciamento está em tela",
      },
      {
        nome: "camadas",
        tipo: "number",
        rotulo: "Camadas",
        aiVisivel: true,
        justificativa: "profundidade da ordem de execução; agregado",
      },
      {
        nome: "pendencias",
        tipo: "number",
        rotulo: "Pendências",
        aiVisivel: true,
        justificativa: "quantos obstáculos e objetivos seguem sem par; contagem",
      },
      {
        nome: "bloqueado",
        tipo: "boolean",
        rotulo: "Sequência bloqueada",
        aiVisivel: true,
        justificativa: "diz se há dependência circular — sim ou não, sem o ciclo em si",
      },
    ],
  },
  {
    id: "toc.at_canvas",
    rota: "/toc/at",
    titulo: "Arvore de Transicao",
    acoesDeIa: ["READ", "FILL_FIELDS", "SUBMIT", "NAVIGATE"],
    declaradaNoManifesto: true,
    campos: [
      {
        nome: "projeto_id",
        tipo: "text",
        rotulo: "Projeto",
        aiVisivel: true,
        justificativa: "identifica o alvo das ações governadas da árvore de transição",
      },
      {
        nome: "passos",
        tipo: "number",
        rotulo: "Passos",
        aiVisivel: true,
        justificativa: "tamanho do plano em tela; agregado, sem a tripla de nenhum passo",
      },
      {
        nome: "passo_selecionado",
        tipo: "entity",
        rotulo: "Passo selecionado",
        aiVisivel: true,
        justificativa: "o passo aberto — é o contexto da proposta",
      },
      {
        nome: "bloqueados",
        tipo: "number",
        rotulo: "Passos bloqueados",
        aiVisivel: true,
        justificativa: "quantos passos estão travados; contagem, sem o motivo escrito",
      },
    ],
  },
  {
    id: "toc.cadeia",
    rota: "/toc/cadeia",
    titulo: "Vista da cadeia",
    acoesDeIa: ["READ", "NAVIGATE"],
    declaradaNoManifesto: true,
    campos: [
      {
        nome: "projeto_id",
        tipo: "text",
        rotulo: "Projeto de partida",
        aiVisivel: true,
        justificativa: "de qual elemento a travessia parte",
      },
      {
        nome: "elos",
        tipo: "number",
        rotulo: "Elos",
        aiVisivel: true,
        justificativa: "tamanho da travessia; agregado, sem nome de projeto algum",
      },
      {
        nome: "elos_pendentes",
        tipo: "number",
        rotulo: "Elos pendentes",
        aiVisivel: true,
        justificativa: "quantos vínculos perderam uma das pontas; contagem",
      },
    ],
  },
  {
    id: "toc.lixeira",
    rota: "/toc/lixeira",
    titulo: "Lixeira",
    acoesDeIa: ["READ"],
    declaradaNoManifesto: true,
    campos: [
      {
        nome: "itens_na_lixeira",
        tipo: "number",
        rotulo: "Itens na lixeira",
        aiVisivel: true,
        justificativa: "contagem agregada, sem nome de projeto excluído",
      },
    ],
  },
  {
    id: "toc.configuracao",
    rota: "/toc/configuracao",
    titulo: "Configuracao do embarque",
    acoesDeIa: [],
    declaradaNoManifesto: true,
    campos: [
      { nome: "host_origin", tipo: "text", rotulo: "Origem do hospedeiro", aiVisivel: false, justificativa: "" },
      { nome: "app_id", tipo: "text", rotulo: "Identificador da aplicação", aiVisivel: false, justificativa: "" },
    ],
  },
  // M6 — Focalização (spec 009, INT-06). Três telas, declaradas no manifesto do ciclo 006
  // no mesmo commit em que nascem. O `aiVisivel` segue a regra dos módulos anteriores:
  // grandeza e vocabulário sim, texto de pessoa não — o enunciado da restrição, as notas
  // e as decisões são conteúdo do inquilino, e a assistência só os recebe quando a pessoa
  // os coloca numa ação governada, nunca por raspagem de tela (APH-3.1).
  {
    id: "toc.foco_jornada",
    rota: "/toc/focalizacao",
    titulo: "Jornada dos cinco passos",
    acoesDeIa: ["READ", "NAVIGATE"],
    declaradaNoManifesto: true,
    campos: [
      {
        nome: "projeto_id",
        tipo: "text",
        rotulo: "Análise",
        aiVisivel: true,
        justificativa: "identifica o alvo das ações governadas do módulo",
      },
      {
        nome: "ciclo",
        tipo: "number",
        rotulo: "Ciclo",
        aiVisivel: true,
        justificativa: "em que volta da jornada a análise está; número, sem conteúdo",
      },
      {
        nome: "passo_atual",
        tipo: "select",
        rotulo: "Passo atual",
        aiVisivel: true,
        justificativa: "vocabulário fechado de cinco valores — é o contexto da proposta",
      },
      {
        nome: "passos_concluidos",
        tipo: "number",
        rotulo: "Passos concluídos",
        aiVisivel: true,
        justificativa: "progresso agregado, sem texto de decisão",
      },
      {
        nome: "tipo_de_restricao",
        tipo: "select",
        rotulo: "Tipo da restrição",
        aiVisivel: true,
        justificativa: "enum fechado da TOC; diz a natureza da restrição, não o enunciado",
      },
      {
        nome: "pendencias",
        tipo: "number",
        rotulo: "Pendências",
        aiVisivel: true,
        justificativa: "contagem agregada do que falta no ciclo",
      },
      {
        nome: "herancas_pendentes",
        tipo: "number",
        rotulo: "Vereditos pendentes",
        aiVisivel: true,
        justificativa: "contagem do bloqueio anti-inércia; agregada, sem o texto das regras",
      },
      { nome: "descricao_da_restricao", tipo: "text", rotulo: "Restrição", aiVisivel: false, justificativa: "" },
    ],
  },
  {
    id: "toc.foco_passo",
    rota: "/toc/focalizacao/passo",
    titulo: "Painel do passo",
    acoesDeIa: ["READ", "NAVIGATE"],
    declaradaNoManifesto: true,
    campos: [
      {
        nome: "projeto_id",
        tipo: "text",
        rotulo: "Análise",
        aiVisivel: true,
        justificativa: "identifica o alvo das ações governadas do módulo",
      },
      {
        nome: "passo",
        tipo: "select",
        rotulo: "Passo",
        aiVisivel: true,
        justificativa: "o passo aberto; vocabulário fechado, é o contexto da proposta",
      },
      {
        nome: "estado",
        tipo: "select",
        rotulo: "Estado do passo",
        aiVisivel: true,
        justificativa: "pendente/em andamento/concluído — enum, sem conteúdo",
      },
      {
        nome: "vinculos",
        tipo: "number",
        rotulo: "Vínculos de ferramenta",
        aiVisivel: true,
        justificativa: "contagem agregada dos projetos referenciados",
      },
      {
        nome: "vinculos_nao_canonicos",
        tipo: "number",
        rotulo: "Vínculos com aviso",
        aiVisivel: true,
        justificativa: "contagem do que foge da combinação canônica do método",
      },
      { nome: "decisao_em_rascunho", tipo: "text", rotulo: "Decisão", aiVisivel: false, justificativa: "" },
      { nome: "notas", tipo: "text", rotulo: "Notas", aiVisivel: false, justificativa: "" },
    ],
  },
  {
    id: "toc.foco_linha_do_tempo",
    rota: "/toc/focalizacao/linha-do-tempo",
    titulo: "Linha do tempo dos ciclos",
    acoesDeIa: ["READ"],
    declaradaNoManifesto: true,
    campos: [
      {
        nome: "projeto_id",
        tipo: "text",
        rotulo: "Análise",
        aiVisivel: true,
        justificativa: "identifica a análise cuja história está em tela",
      },
      {
        nome: "ciclos",
        tipo: "number",
        rotulo: "Ciclos",
        aiVisivel: true,
        justificativa: "tamanho da história; agregado, sem restrição nem decisão",
      },
      {
        nome: "ciclos_fechados",
        tipo: "number",
        rotulo: "Ciclos fechados",
        aiVisivel: true,
        justificativa: "quantas voltas já se fecharam; agregado",
      },
    ],
  },
  // M5 — Estratégia & Táticas (spec 010, INT-02). Quatro telas, declaradas no manifesto
  // do ciclo 006 no mesmo commit em que nascem. O `aiVisivel` segue a regra dos módulos
  // anteriores: **grandeza e vocabulário sim, texto de pessoa não** — a meta global, a
  // estratégia, a tática e as três premissas são o que o grupo escreveu, e a assistência
  // só os recebe quando a pessoa os coloca numa ação governada (APH-3.1).
  //
  // As quatro declaram `READ` e `NAVIGATE` e nenhuma declara `SUBMIT`: este módulo não tem
  // ação de catálogo nenhuma (INT-04 da spec 010), e anunciar `SUBMIT` prometeria à
  // fundação um verbo que não existe.
  {
    id: "toc.snt_arvore",
    rota: "/toc/snt",
    titulo: "Arvore de Estrategia e Taticas",
    acoesDeIa: ["READ", "NAVIGATE"],
    declaradaNoManifesto: false,
    campos: [
      {
        nome: "projeto_id",
        tipo: "text",
        rotulo: "Projeto",
        aiVisivel: true,
        justificativa: "identifica a árvore aberta; é o contexto da navegação",
      },
      {
        nome: "passos",
        tipo: "number",
        rotulo: "Passos",
        aiVisivel: true,
        justificativa: "tamanho do plano em tela; agregado, sem texto de passo",
      },
      {
        nome: "niveis",
        tipo: "number",
        rotulo: "Níveis da árvore",
        aiVisivel: true,
        justificativa: "profundidade da decomposição; número, sem conteúdo",
      },
      {
        nome: "passo_selecionado",
        tipo: "entity",
        rotulo: "Passo selecionado",
        aiVisivel: true,
        justificativa: "o que a pessoa está olhando — é o contexto da conversa",
      },
      {
        nome: "numero_selecionado",
        tipo: "text",
        rotulo: "Número do passo",
        aiVisivel: true,
        justificativa: "a numeração é estrutura derivada, não texto de pessoa",
      },
      {
        nome: "filtro_de_status",
        tipo: "select",
        rotulo: "Filtro por status",
        aiVisivel: true,
        justificativa: "vocabulário fechado de quatro valores; diz o recorte em tela",
      },
      {
        nome: "pendencias",
        tipo: "number",
        rotulo: "Pendências lógicas",
        aiVisivel: true,
        justificativa: "contagem agregada do que falta de premissa",
      },
      { nome: "meta_global", tipo: "text", rotulo: "Meta global", aiVisivel: false, justificativa: "" },
    ],
  },
  {
    id: "toc.snt_passo",
    rota: "/toc/snt/passo",
    titulo: "Ficha do passo",
    acoesDeIa: ["READ", "NAVIGATE"],
    declaradaNoManifesto: false,
    campos: [
      {
        nome: "projeto_id",
        tipo: "text",
        rotulo: "Projeto",
        aiVisivel: true,
        justificativa: "identifica a árvore do passo aberto",
      },
      {
        nome: "numero",
        tipo: "text",
        rotulo: "Número do passo",
        aiVisivel: true,
        justificativa: "estrutura derivada da posição na árvore, não conteúdo",
      },
      {
        nome: "status",
        tipo: "select",
        rotulo: "Status do passo",
        aiVisivel: true,
        justificativa: "enum fechado de quatro valores herdado da linhagem",
      },
      {
        nome: "categoria",
        tipo: "select",
        rotulo: "Categoria do passo",
        aiVisivel: true,
        justificativa: "enum fechado de seis valores; classifica o papel, não o conteúdo",
      },
      {
        nome: "filhos",
        tipo: "number",
        rotulo: "Filhos",
        aiVisivel: true,
        justificativa: "grau do nó; agregado, sem texto",
      },
      {
        nome: "premissas_preenchidas",
        tipo: "number",
        rotulo: "Premissas preenchidas",
        aiVisivel: true,
        justificativa: "quantas das três estão escritas; contagem, sem o texto delas",
      },
      { nome: "estrategia", tipo: "text", rotulo: "Estratégia", aiVisivel: false, justificativa: "" },
      { nome: "tatica", tipo: "text", rotulo: "Tática", aiVisivel: false, justificativa: "" },
      { nome: "premissa_paralela", tipo: "text", rotulo: "Premissa paralela", aiVisivel: false, justificativa: "" },
      {
        nome: "premissa_necessidade_ao_pai",
        tipo: "text",
        rotulo: "Premissa de necessidade",
        aiVisivel: false,
        justificativa: "",
      },
      {
        nome: "premissa_suficiencia_dos_filhos",
        tipo: "text",
        rotulo: "Premissa de suficiência",
        aiVisivel: false,
        justificativa: "",
      },
    ],
  },
  {
    id: "toc.snt_tabela",
    rota: "/toc/snt/tabela",
    titulo: "Vista tabular da S&T",
    acoesDeIa: ["READ", "NAVIGATE"],
    declaradaNoManifesto: false,
    campos: [
      {
        nome: "projeto_id",
        tipo: "text",
        rotulo: "Projeto",
        aiVisivel: true,
        justificativa: "identifica a árvore em tela",
      },
      {
        nome: "linhas",
        tipo: "number",
        rotulo: "Linhas",
        aiVisivel: true,
        justificativa: "tamanho da tabela; agregado",
      },
      {
        nome: "linhas_sem_tatica",
        tipo: "number",
        rotulo: "Linhas sem tática",
        aiVisivel: true,
        justificativa: "contagem de pendência; agregada, sem o texto do passo",
      },
    ],
  },
  {
    id: "toc.snt_acompanhamento",
    rota: "/toc/snt/acompanhamento",
    titulo: "Painel de acompanhamento da S&T",
    acoesDeIa: ["READ"],
    declaradaNoManifesto: false,
    campos: [
      {
        nome: "projeto_id",
        tipo: "text",
        rotulo: "Projeto",
        aiVisivel: true,
        justificativa: "identifica a árvore acompanhada",
      },
      {
        nome: "passos",
        tipo: "number",
        rotulo: "Passos",
        aiVisivel: true,
        justificativa: "denominador das contagens; agregado",
      },
      {
        nome: "validados",
        tipo: "number",
        rotulo: "Passos validados",
        aiVisivel: true,
        justificativa: "contagem por status; agregada",
      },
      {
        nome: "em_execucao",
        tipo: "number",
        rotulo: "Passos em execução",
        aiVisivel: true,
        justificativa: "contagem por status; agregada",
      },
      {
        nome: "nao_validados",
        tipo: "number",
        rotulo: "Passos não validados",
        aiVisivel: true,
        justificativa: "contagem por status; agregada",
      },
      {
        nome: "pendencias",
        tipo: "number",
        rotulo: "Pendências lógicas",
        aiVisivel: true,
        justificativa: "contagem agregada do que falta de premissa",
      },
      {
        nome: "progresso",
        tipo: "number",
        rotulo: "Progresso",
        aiVisivel: true,
        justificativa: "fração de passos validados; número, sem conteúdo",
      },
    ],
  },
  {
    // Rota da interface, ainda **fora** do manifesto (ver `declaradaNoManifesto`).
    id: "toc.nuvem",
    rota: "/toc/nuvem",
    titulo: "Nuvem de Conflito",
    acoesDeIa: [],
    declaradaNoManifesto: false,
    campos: [
      { nome: "projeto_id", tipo: "text", rotulo: "Projeto", aiVisivel: false, justificativa: "" },
    ],
  },
] as const;

export function telaPorId(id: string): Tela | undefined {
  return REGISTRO_DE_TELAS.find((tela) => tela.id === id);
}

/** §B.5.3: `ai_actions: []` marca item sensível — não entra em snapshot algum. */
export function telaSensivel(id: string): boolean {
  const tela = telaPorId(id);
  return !tela || tela.acoesDeIa.length === 0;
}

export function camposVisiveisParaIa(id: string): string[] {
  if (telaSensivel(id)) return [];
  return (telaPorId(id)?.campos ?? []).filter((c) => c.aiVisivel).map((c) => c.nome);
}
