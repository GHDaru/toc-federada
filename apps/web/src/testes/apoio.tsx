/**
 * Apoio de teste — o cliente falso e a renderização com idioma.
 *
 * Este módulo é consumido **apenas por testes**; nenhum arquivo de produção o importa, e
 * por isso ele não entra no pacote publicado. A base é sintética por regra (ADR 0006):
 * "Instituição Horizonte", "Facilitadora TOC" — nenhum dado real de pessoa, em nenhuma
 * fixture, nunca.
 */
import { render } from "@testing-library/react";
import type { ReactElement } from "react";
import { ProvedorDeIdioma, type Idioma } from "../i18n";
import type { Cliente } from "../api/cliente";
import type {
  AnaliseDeFocalizacao,
  Ara,
  Jornada,
  No,
  Nuvem,
  Projeto,
  ProjetoResumo,
  Proposta,
  Ude,
  ValidacaoFormal,
} from "../dominio/tipos";

export function renderComIdioma(elemento: ReactElement, idioma: Idioma = "pt") {
  return render(<ProvedorDeIdioma idiomaInicial={idioma}>{elemento}</ProvedorDeIdioma>);
}

export const PROJETO_RESUMO: ProjetoResumo = {
  id: "p1",
  nome: "Evasão no primeiro semestre",
  ferramenta: "ara",
  descricao_do_problema: "Turmas perdem alunos antes da terceira semana.",
  estado: "ativo",
  versao: 3,
  criado_em: "2026-08-01T09:00:00Z",
  alterado_em: "2026-09-01T09:00:00Z",
  excluido_em: null,
};

export function no(id: string, titulo: string, x = 0, y = 0): No {
  return { id, titulo, descricao: "", tipo: "efeito", posicao: { x, y }, recolhido: false };
}

export const PROJETO: Projeto = {
  ...PROJETO_RESUMO,
  nos: [no("n1", "Prazos são perdidos", 0, 0), no("n2", "Retrabalho consome a equipe", 300, 200)],
  arestas: [{ id: "a1", origem_id: "n1", destino_id: "n2", rotulo: "" }],
};

export const VALIDACAO_APROVADA: ValidacaoFormal = {
  texto: "Prazos são perdidos",
  idioma: "pt",
  versao_do_lexico: "pt-1",
  aprovado_nos_decidiveis: true,
  vereditos: [
    {
      codigo: "CD-1",
      caracteristica: "2",
      nome: "criterio.frase_completa",
      classe: "decidivel",
      regra: "RN-01",
      enunciado: "É uma frase completa.",
      veredito: "atende",
      motivo: "",
      trecho: "",
    },
  ],
  reprovacoes: [],
  pendencias_de_julgamento: [],
};

export const UDE: Ude = {
  no_id: "n1",
  titulo: "Prazos são perdidos",
  status: "pendente",
  ficha: {},
  validacao: VALIDACAO_APROVADA,
  pareceres: [],
};

export const ARA: Ara = {
  projeto: PROJETO,
  udes: [UDE],
  elos: [
    {
      aresta_id: "a1",
      leitura: "Se Prazos são perdidos, então Retrabalho consome a equipe",
      exame: { aresta_id: "a1", estado: "nao_examinado", reserva: "" },
    },
  ],
  conectores: [],
  resumo_por_status: { pendente: 1, requer_refinamento: 0, validado: 0, rejeitado: 0 },
};

export const NUVEM: Nuvem = {
  id: "p-nc",
  nome: "Expansão da Instituição Horizonte",
  ferramenta: "nc",
  descricao_do_problema: "Abrir turmas novas sem perder a reputação.",
  racional: "",
  criado_em: "2026-09-01T10:00:00Z",
  alterado_em: "2026-09-01T10:00:00Z",
  origem: null,
  entidades: [
    { papel: "A", no_id: "na", texto: "Reputação acadêmica preservada", posicao: { x: 0, y: 160 }, avisos: [] },
    { papel: "B", no_id: "nb", texto: "Turmas com professor titular", posicao: { x: 280, y: 40 }, avisos: [] },
    { papel: "C", no_id: "nc", texto: "Custo por turma sob controle", posicao: { x: 280, y: 280 }, avisos: [] },
    { papel: "D", no_id: "nd", texto: "Abrir turmas em três cidades novas", posicao: { x: 560, y: 40 }, avisos: [] },
    { papel: "D_PRIME", no_id: "ndl", texto: "Não abrir turmas em três cidades novas", posicao: { x: 560, y: 280 }, avisos: [] },
  ],
  arestas: [
    { chave: "A_B", classe: "necessidade", aresta_id: "e1", leitura: "Para ter B, precisamos de A", premissas: [] },
    { chave: "A_C", classe: "necessidade", aresta_id: "e2", leitura: "Para ter C, precisamos de A", premissas: [] },
    { chave: "B_D", classe: "pre_requisito", aresta_id: "e3", leitura: "Para ter B, devemos D", premissas: [] },
    { chave: "C_D_PRIME", classe: "pre_requisito", aresta_id: "e4", leitura: "Para ter C, devemos D′", premissas: [] },
    { chave: "D_C", classe: "perigo", aresta_id: "e5", leitura: "D ameaça C", premissas: [] },
    { chave: "D_PRIME_B", classe: "perigo", aresta_id: "e6", leitura: "D′ ameaça B", premissas: [] },
    { chave: "D_D_PRIME", classe: "conflito", aresta_id: "e7", leitura: "D e D′ não podem coexistir", premissas: [] },
  ],
};

/** Uma proposta de ação esperando o gate humano — a forma que o servidor devolve. */
export const PROPOSTA_PENDENTE: Proposta = {
  proposal_id: "prop-1",
  action_id: "toc.generate_conflict_cloud",
  titulo: "Preencher a nuvem a partir de uma narrativa",
  risk: "confirm",
  requires_confirmation: true,
  origem: "ia",
  estado: "awaiting_approval",
  alvos: [],
  quantidade_de_alvos: 0,
  criada_em: "2026-09-06T10:00:00Z",
  vence_em: "2026-09-06T10:10:00Z",
  status: null,
  mensagem: "",
  outcomes: [],
};

// ---------------------------------------------------------------------------------------
// M6 · Focalização (spec 009) — a análise sintética da Instituição Horizonte
//
// Base sintética por regra (ADR 0006): a instituição é fictícia, as personas são papéis
// ("Facilitadora TOC"), e o fluxo de matrículas é inventado para o teste.
// ---------------------------------------------------------------------------------------

export const RESTRICAO_SINTETICA = "Capacidade de conferência da secretaria acadêmica";

function passo(
  tipo: Jornada["passos"][number]["tipo"],
  estado: Jornada["passos"][number]["estado"],
  extra: Partial<Jornada["passos"][number]> = {},
): Jornada["passos"][number] {
  return {
    tipo,
    estado,
    decisao: "",
    autor_da_decisao: "",
    decisoes: [],
    notas: [],
    reaberturas: [],
    vinculos: [],
    canonicas: [],
    avisos: [],
    herdado: [],
    pendencias: [],
    ...extra,
  };
}

/** Uma jornada no passo `identificar`, com a restrição já registrada. */
export const JORNADA: Jornada = {
  ciclo_id: "c1",
  ordem: 1,
  estado: "aberto",
  somente_leitura: false,
  passo_atual: "identificar",
  restricao: {
    id: "r1",
    descricao: RESTRICAO_SINTETICA,
    tipo: "fisica",
    justificativa: "a fila de matrículas só cresce nesta etapa",
    autor: "Facilitadora TOC",
    registrada_em: "2026-09-06T09:05:00Z",
    origem: null,
  },
  passos: [
    passo("identificar", "em_andamento", {
      canonicas: ["ara"],
      vinculos: [
        {
          id: "v1",
          ferramenta: "ara",
          projeto_id: "p-ara",
          papel: "causa raiz",
          justificativa: "",
          canonico: true,
          estado: "ativo",
          nome: "ARA do fluxo",
          legenda: "projeto ativo",
        },
      ],
      pendencias: [
        {
          passo: "identificar",
          regra: "decisao_ausente",
          detalhe: "o passo se encerra com a decisão que o encerra (RF-09)",
        },
      ],
    }),
    passo("explorar", "pendente", { canonicas: ["arf", "nc"] }),
    passo("subordinar", "pendente", { canonicas: ["nc"] }),
    passo("elevar", "pendente", { canonicas: ["apr", "at"] }),
    passo("recomecar", "pendente"),
  ],
  heranca: [],
  herancas_pendentes: 0,
  ciclos_no_total: 1,
  passos_concluidos: 0,
};

export const ANALISE_DE_FOCALIZACAO: AnaliseDeFocalizacao = {
  projeto: {
    id: "p-foco",
    nome: "Fluxo de matrículas",
    ferramenta: "focalizacao",
    descricao_do_problema: "Da inscrição do candidato à primeira aula assistida.",
    estado: "ativo",
    versao: 7,
    criado_em: "2026-09-06T09:00:00Z",
    alterado_em: "2026-09-06T09:05:00Z",
    excluido_em: null,
  },
  sistema: {
    nome: "Da inscrição do candidato à primeira aula assistida",
    descricao: "O fluxo de matrículas da Instituição Horizonte.",
  },
  jornada: JORNADA,
  linha_do_tempo: [
    {
      ciclo_id: "c1",
      ordem: 1,
      estado: "aberto",
      restricao: RESTRICAO_SINTETICA,
      tipo_de_restricao: "fisica",
      aberto_em: "2026-09-06T09:00:00Z",
      fechado_em: null,
      decisoes: 0,
      vinculos: 1,
      herancas: 0,
      herancas_pendentes: 0,
      passo_atual: "identificar",
    },
  ],
};

/**
 * Um cliente com todos os métodos espiáveis. Cada teste sobrescreve o que lhe interessa —
 * o resto responde vazio, para a tela nunca quebrar por método não previsto.
 */
export function clienteFalso(sobrescritas: Record<string, unknown> = {}): Cliente {
  const base = {
    pedir: async () => ({}),
    embarcar: async () => ({
      token: "ses",
      usuario: { id: "usr-facilitadora", nome: "Facilitadora TOC" },
      tenantId: "inq-horizonte",
      capabilities: ["toc:read", "toc:write"],
      expiraEm: null,
    }),
    saude: async () => ({}),
    projetos: {
      listar: async () => [PROJETO_RESUMO],
      lixeira: async () => [],
      abrir: async () => PROJETO,
      criar: async () => PROJETO,
      excluir: async () => ({ ...PROJETO_RESUMO, estado: "excluido" as const }),
      restaurar: async () => PROJETO_RESUMO,
    },
    grafo: {
      criarNo: async () => no("n9", "Novo efeito"),
      editarNo: async () => no("n1", "Prazos são perdidos"),
      moverNo: async () => no("n1", "Prazos são perdidos"),
      recolherNo: async () => no("n1", "Prazos são perdidos"),
      excluirNo: async () => ({ no_id: "n1", arestas_removidas: ["a1"] }),
      ligar: async () => ({ id: "a2", origem_id: "n1", destino_id: "n2", rotulo: "" }),
      editarAresta: async () => ({ id: "a1", origem_id: "n1", destino_id: "n2", rotulo: "" }),
      excluirAresta: async () => undefined,
    },
    ara: {
      validarTexto: async () => VALIDACAO_APROVADA,
      criarProjeto: async () => PROJETO,
      abrir: async () => ARA,
      adicionarEfeito: async () => no("n9", "Novo efeito"),
      marcarUde: async () => ({}),
      desmarcarUde: async () => undefined,
      editarFicha: async () => ({}),
      reformular: async () => no("n1", "Prazos são perdidos"),
      registrarParecer: async () => undefined,
      mudarStatus: async () => ({ no_id: "n1", status: "validado" as const }),
      examinarElo: async () => ({ aresta_id: "a1", estado: "suficiente" as const, reserva: "" }),
      formarConector: async () => ({ id: "c1", destino_id: "n2", arestas: ["a1"], leitura: "" }),
      desfazerConector: async () => undefined,
      analisar: async () => ({
        fragmentos: [["n1", "n2"]],
        entradas: ["n1"],
        alcances: [{ no_id: "n1", udes_alcancados: ["n1"], fracao: 1 }],
        udes_nao_alcancados: [],
        elos_nao_examinados: ["a1"],
        orfaos: [],
        ciclos: [],
        nos_em_ciclo: [],
        causas_raiz_candidatas: ["n1"],
        causa_raiz_candidata: "n1",
        observacoes: [],
        total_de_nos: 2,
        total_de_udes: 1,
        resumo: { fragmentos: 1 },
      }),
    },
    /**
     * O gate governado. O padrão devolve uma proposta esperando decisão: nenhum teste
     * ganha escrita de graça, e quem quiser o desfecho sobrescreve `decidir`.
     */
    propostas: {
      criar: async () => PROPOSTA_PENDENTE,
      decidir: async () => ({ ...PROPOSTA_PENDENTE, estado: "denied", status: "denied" }),
    },
    nc: {
      criarProjeto: async () => NUVEM,
      derivar: async () => NUVEM,
      abrir: async () => NUVEM,
      validacao: async () => ({
        completude: { sustentadas: 0, total: 7 },
        modelada: false,
        arestas_sem_premissa: NUVEM.arestas.map((a) => a.chave),
        arestas_sem_injecao: [],
        separacoes_ausentes: [],
        avisos: [],
      }),
      solucao: async () => ({
        posicoes: NUVEM.arestas.map((a) => ({
          chave: a.chave,
          classe: a.classe,
          leitura: a.leitura,
          pendente: true,
          injecoes: [],
        })),
      }),
      matriz: async () => ({
        linhas: NUVEM.arestas.map((a) => ({ chave: a.chave, leitura: a.leitura, premissas: [] })),
      }),
      editarEntidade: async () => NUVEM,
      editarRacional: async () => NUVEM,
      registrarPremissa: async () => ({
        id: "pr1",
        aresta: "A_B" as const,
        texto: "",
        ordem: 0,
        estado: "vigente" as const,
        justificativa: "",
        injecoes: [],
      }),
      editarPremissa: async () => ({
        id: "pr1",
        aresta: "A_B" as const,
        texto: "",
        ordem: 0,
        estado: "vigente" as const,
        justificativa: "",
        injecoes: [],
      }),
      reordenarPremissas: async () => [],
      mudarEstadoDaPremissa: async () => ({
        id: "pr1",
        aresta: "A_B" as const,
        texto: "",
        ordem: 0,
        estado: "desafiada" as const,
        justificativa: "",
        injecoes: [],
      }),
      arquivarPremissa: async () => ({ premissa_id: "pr1", injecoes_arquivadas: 0 }),
      registrarInjecao: async () => ({
        id: "in1",
        premissa_id: "pr1",
        texto: "",
        status: "candidata" as const,
        separacao: null,
        semeadura: null,
      }),
      editarInjecao: async () => ({
        id: "in1",
        premissa_id: "pr1",
        texto: "",
        status: "candidata" as const,
        separacao: null,
        semeadura: null,
      }),
      classificarInjecao: async () => ({
        id: "in1",
        premissa_id: "pr1",
        texto: "",
        status: "candidata" as const,
        separacao: null,
        semeadura: null,
      }),
      mudarStatusDaInjecao: async () => ({
        id: "in1",
        premissa_id: "pr1",
        texto: "",
        status: "escolhida" as const,
        separacao: null,
        semeadura: null,
      }),
      gerar: async () => ({ action_id: "toc.generate_conflict_cloud", resultado: {}, aviso: "" }),
      sugerirPremissas: async () => ({
        action_id: "toc.suggest_assumptions",
        aresta: "A_B" as const,
        sugestoes: [],
        aviso: "",
      }),
      sugerirInjecoes: async () => ({
        action_id: "toc.suggest_injections",
        premissa_id: "pr1",
        sugestoes: [],
        aviso: "",
      }),
    },
    foco: {
      criarAnalise: async () => ANALISE_DE_FOCALIZACAO,
      listar: async () => [
        {
          projeto_id: "p-foco",
          nome: "Fluxo de matrículas",
          sistema: "Da inscrição do candidato à primeira aula assistida",
          ciclo: 1,
          passo_atual: "identificar" as const,
          restricao: RESTRICAO_SINTETICA,
          tipo_de_restricao: "fisica" as const,
          pendencias: 1,
          herancas_pendentes: 0,
          alterado_em: "2026-09-06T09:05:00Z",
        },
      ],
      abrir: async () => ANALISE_DE_FOCALIZACAO,
      excluir: async () => ANALISE_DE_FOCALIZACAO,
      restaurar: async () => ANALISE_DE_FOCALIZACAO,
      jornada: async () => JORNADA,
      linhaDoTempo: async () => ANALISE_DE_FOCALIZACAO.linha_do_tempo,
      registrarRestricao: async () => JORNADA.restricao,
      editarRestricao: async () => JORNADA.restricao,
      concluirPasso: async () => JORNADA,
      reabrirAnterior: async () => JORNADA,
      anotar: async () => JORNADA,
      vincular: async () => JORNADA.passos[0]!.vinculos[0]!,
      removerVinculo: async () => JORNADA,
      julgarHeranca: async () => JORNADA,
      recomecar: async () => ANALISE_DE_FOCALIZACAO,
      sugerirRestricao: async () => ({
        ara_projeto_id: "p-ara",
        action_id: "toc.suggest_constraint",
        aviso: "nada foi aplicado",
        candidatas: [],
      }),
    },
  };
  return { ...base, ...sobrescritas } as unknown as Cliente;
}
