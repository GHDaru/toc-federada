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
  Apr,
  Ara,
  Arf,
  At,
  Cadeia,
  Jornada,
  No,
  Nuvem,
  Projeto,
  ProjetoResumo,
  Proposta,
  Ude,
  ValidacaoFormal,
  AcompanhamentoDaSnT,
  FichaDoPassoSnT,
  PassoDaSnT,
  SnT,
  TabelaDaSnT,
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

// ---------------------------------------------------------------------------------------
// M4 · Árvores de Futuro e Implementação (spec 008) — a análise sintética da Horizonte
//
// A árvore de futuro abaixo é a continuação do MESMO caso: a restrição é a conferência
// documental da secretaria, a injeção é o checklist no ato da inscrição, e o ramo negativo
// é o que essa injeção piora — a leitura fina do documento raro. É de propósito que ela
// tenha um ramo negativo ABERTO e uma injeção SEM efeito: uma árvore sem pendência não
// prova que a verificação estrutural vê alguma coisa.
//
// Base sintética por regra (ADR 0006): a instituição é fictícia e as personas são papéis.
// ---------------------------------------------------------------------------------------

function noDaArvore(
  id: string,
  papel: string,
  titulo: string,
  x = 0,
  y = 0,
): Arf["nos"][number] {
  return { id, papel, titulo, descricao: "", posicao: { x, y }, recolhido: false };
}

export const ARF: Arf = {
  id: "p-arf",
  nome: "Futuro da conferência documental",
  ferramenta: "arf",
  descricao_do_problema: "O que passa a ser verdade quando a conferência sai da fila.",
  versao: 5,
  origem: {
    ferramenta: "nc",
    projeto_id: "p-nc",
    elementos: ["in1"],
    papel: "injecao",
  },
  udes_da_cadeia: ["u1"],
  nos: [
    noDaArvore("i1", "injecao", "Conferência documental feita na inscrição, por checklist automático", 60, 420),
    noDaArvore("e1", "efeito_futuro", "A fila de conferência deixa de crescer", 60, 260),
    noDaArvore("e2", "efeito_futuro", "O candidato recebe a matrícula na semana em que se inscreve", 60, 100),
    noDaArvore("e3", "efeito_futuro", "A secretaria perde a leitura fina do documento raro", 380, 260),
    noDaArvore("i2", "injecao", "Fila de exceção com conferência humana para documento raro", 700, 420),
  ],
  elos: [
    {
      id: "a1",
      origem_id: "i1",
      destino_id: "e1",
      rotulo: "",
      leitura:
        "Se Conferência documental feita na inscrição, por checklist automático, então A fila de conferência deixa de crescer",
      exame: { estado: "suficiente", reserva: "" },
    },
    {
      id: "a2",
      origem_id: "e1",
      destino_id: "e2",
      rotulo: "",
      leitura:
        "Se A fila de conferência deixa de crescer, então O candidato recebe a matrícula na semana em que se inscreve",
      exame: { estado: "nao_examinado", reserva: "" },
    },
    {
      id: "a3",
      origem_id: "i1",
      destino_id: "e3",
      rotulo: "",
      leitura:
        "Se Conferência documental feita na inscrição, por checklist automático, então A secretaria perde a leitura fina do documento raro",
      exame: { estado: "com_reserva", reserva: "vale só para o documento fora do padrão" },
    },
  ],
  conectores: [],
  espelhos: [{ no_id: "e1", ude_id: "u1", projeto_de_origem_id: "p-ara" }],
  ramos: [
    {
      id: "r1",
      raiz_id: "e3",
      estado: "aberto",
      injecao_de_corte_id: null,
      justificativa: "",
      autor: "",
    },
  ],
  verificacao: {
    eds_sem_caminho: [],
    injecoes_sem_efeito: 1,
    injecoes_sem_efeito_ids: ["i2"],
    ramos_abertos: ["r1"],
    cobertura: [{ ude_id: "u1", espelhado_por: "e1", alcancado: true }],
    sem_origem_vinculada: false,
    pronta: false,
  },
};

export const APR: Apr = {
  id: "p-apr",
  nome: "Ampliar a secretaria acadêmica",
  ferramenta: "apr",
  descricao_do_problema: "O que precisa existir para a fila deixar de acumular.",
  versao: 3,
  origem: { ferramenta: "arf", projeto_id: "p-arf", elementos: ["e1"], papel: "efeito_futuro" },
  objetivo: noDaArvore("o1", "objetivo", "A conferência documental deixa de acumular fila", 400, 60),
  nos: [
    noDaArvore("o1", "objetivo", "A conferência documental deixa de acumular fila", 400, 60),
    noDaArvore("ob1", "obstaculo", "Ninguém confere documento no ato da inscrição", 120, 300),
    noDaArvore("oi1", "objetivo_intermediario", "Há um posto de conferência no ato da inscrição", 120, 460),
    noDaArvore("ob2", "obstaculo", "O checklist de documentos não existe", 620, 300),
    noDaArvore("oi2", "objetivo_intermediario", "O checklist de documentos está publicado e em uso", 620, 460),
  ],
  dependencias: [
    {
      id: "d1",
      antes_id: "oi2",
      depois_id: "oi1",
      leitura:
        "O checklist de documentos está publicado e em uso precisa existir antes de Há um posto de conferência no ato da inscrição",
    },
  ],
  pares: [
    {
      id: "par1",
      obstaculo_id: "ob1",
      objetivo_intermediario_id: "oi1",
      teste_de_validade:
        "Se Há um posto de conferência no ato da inscrição, então Ninguém confere documento no ato da inscrição deixa de impedir o objetivo",
      julgamentos: [],
    },
    {
      id: "par2",
      obstaculo_id: "ob2",
      objetivo_intermediario_id: "oi2",
      teste_de_validade:
        "Se O checklist de documentos está publicado e em uso, então O checklist de documentos não existe deixa de impedir o objetivo",
      julgamentos: [
        {
          autor: "usr-facilitadora",
          valido: true,
          justificativa: "O checklist é condição de qualquer conferência no ato.",
          instante: "2026-09-06T11:00:00Z",
        },
      ],
    },
  ],
  elipses: [],
  sequenciamento: {
    camadas: [["oi2"], ["oi1"]],
    ramos_paralelos: [["oi2", "oi1"]],
    elipses: [],
    ciclos: [],
    obstaculos_sem_oi: [],
    objetivos_sem_obstaculo: [],
    bloqueado: false,
    completo: true,
  },
};

export const RESUMO_DA_APR = {
  linhas: [
    {
      camada: 0,
      objetivo_intermediario: "O checklist de documentos está publicado e em uso",
      objetivo_intermediario_id: "oi2",
      obstaculo: "O checklist de documentos não existe",
      obstaculo_id: "ob2",
      depende_de: [] as string[],
      julgamento: "valido",
    },
    {
      camada: 1,
      objetivo_intermediario: "Há um posto de conferência no ato da inscrição",
      objetivo_intermediario_id: "oi1",
      obstaculo: "Ninguém confere documento no ato da inscrição",
      obstaculo_id: "ob1",
      depende_de: ["O checklist de documentos está publicado e em uso"],
      julgamento: "",
    },
  ],
};

export const AT: At = {
  id: "p-at",
  nome: "Implantar o posto de conferência",
  ferramenta: "at",
  descricao_do_problema: "Os passos entre hoje e o posto de conferência funcionando.",
  versao: 4,
  alvo: {
    ferramenta: "apr",
    projeto_id: "p-apr",
    elementos: ["oi1"],
    papel: "objetivo_intermediario",
  },
  passos: [
    {
      id: "p1",
      necessidade: "não existe lista do que se confere",
      acao: "publicar o checklist de documentos exigidos",
      resultado_esperado: "o checklist está no portal e na recepção",
      status: "concluido",
      motivo_do_bloqueio: "",
      resultado_real: "o checklist está no portal e na recepção",
      divergente: false,
      leitura:
        "Para não existe lista do que se confere, publicar o checklist de documentos exigidos; espero o checklist está no portal e na recepção",
    },
    {
      id: "p2",
      necessidade: "a recepção não sabe conferir",
      acao: "treinar a recepção no checklist",
      resultado_esperado: "a recepção confere sem consultar a secretaria",
      status: "em_execucao",
      motivo_do_bloqueio: "",
      resultado_real: "",
      divergente: false,
      leitura:
        "Para a recepção não sabe conferir, treinar a recepção no checklist; espero a recepção confere sem consultar a secretaria",
    },
    {
      id: "p3",
      necessidade: "não há posto físico na entrada",
      acao: "montar o posto de conferência na recepção",
      resultado_esperado: "o posto atende no horário de inscrição",
      status: "bloqueado",
      motivo_do_bloqueio: "a reforma da recepção não tem data",
      resultado_real: "",
      divergente: false,
      leitura:
        "Para não há posto físico na entrada, montar o posto de conferência na recepção; espero o posto atende no horário de inscrição",
    },
  ],
  precedencias: [
    { id: "pr1", antes_id: "p1", depois_id: "p2" },
    { id: "pr2", antes_id: "p2", depois_id: "p3" },
  ],
  ordem_de_leitura: ["p1", "p2", "p3"],
  inalcancaveis: [],
  resumo: {
    pendente: 0,
    em_execucao: 1,
    concluido: 1,
    bloqueado: 1,
    passos: 3,
    inalcancaveis: 0,
  },
};

/**
 * A travessia inteira, com um elo PENDENTE de propósito: o elo que perdeu uma ponta
 * continua à vista (RF-35, US-18). Omiti-lo seria esconder justamente o que a pessoa
 * precisa consertar.
 */
export const CADEIA: Cadeia = {
  elos: [
    {
      referencia_id: "ref1",
      tipo: "promocao_ude_nc",
      origem: { ferramenta: "ara", projeto_id: "p-ara", elementos: ["u1", "u2"], papel: "ude" },
      destino: { ferramenta: "nc", projeto_id: "p-nc", elementos: [], papel: "" },
      estado: "ativa",
      motivo: "",
    },
    {
      referencia_id: "ref2",
      tipo: "semeadura_injecao_arf",
      origem: { ferramenta: "nc", projeto_id: "p-nc", elementos: ["in1"], papel: "injecao" },
      destino: { ferramenta: "arf", projeto_id: "p-arf", elementos: ["i1"], papel: "injecao" },
      estado: "ativa",
      motivo: "",
    },
    {
      referencia_id: "ref3",
      tipo: "derivacao_arf_apr",
      origem: { ferramenta: "arf", projeto_id: "p-arf", elementos: ["e1"], papel: "efeito_futuro" },
      destino: { ferramenta: "apr", projeto_id: "p-apr", elementos: ["o1"], papel: "objetivo" },
      estado: "ativa",
      motivo: "",
    },
    {
      referencia_id: "ref4",
      tipo: "derivacao_oi_at",
      origem: {
        ferramenta: "apr",
        projeto_id: "p-apr",
        elementos: ["oi1"],
        papel: "objetivo_intermediario",
      },
      destino: { ferramenta: "at", projeto_id: "p-at", elementos: [], papel: "" },
      estado: "pendente",
      motivo: "o projeto de destino foi excluído",
    },
  ],
  ferramentas: ["ara", "nc", "arf", "apr", "at"],
  resumo: { elos: 4, elos_pendentes: 1, ferramentas: 5, projetos: 5 },
};

/**
 * Um cliente com todos os métodos espiáveis. Cada teste sobrescreve o que lhe interessa —
 * o resto responde vazio, para a tela nunca quebrar por método não previsto.
 */
/**
 * A árvore de Estratégia & Táticas sintética da "Instituição Horizonte" — TRÊS níveis,
 * que é o portão do roadmap para o ciclo 010 (ADR 0006: nenhum dado real de pessoa).
 *
 * Os números **não são digitados**: eles são o que o servidor calcula da posição na
 * árvore (RN-01), e a fixture os carrega já calculados porque é assim que eles chegam à
 * interface. Na quarta geração da linhagem eram texto livre digitado à mão
 * (`tocbuilderv3/types.ts:288`), e é essa a regressão que o módulo desfaz.
 */
function passoDaSnT(
  id: string,
  numero: string,
  nivel: number,
  pai_id: string | null,
  estrategia: string,
  tatica: string,
  filhos: string[] = [],
  status: PassoDaSnT["status"] = "nenhum",
): PassoDaSnT {
  return {
    id,
    numero,
    nivel,
    pai_id,
    estrategia,
    tatica,
    categoria: "nenhuma",
    status,
    premissas: { paralela: "", necessidade_ao_pai: "", suficiencia_dos_filhos: "" },
    filhos,
  };
}

export const PASSOS_DA_SNT: PassoDaSnT[] = [
  passoDaSnT("s1", "1", 0, null, "Atender o dobro de pessoas com a estrutura atual", "Três frentes por trimestre", ["s2", "s5"]),
  passoDaSnT("s2", "1.1", 1, "s1", "Reduzir o tempo de espera pela metade", "Medir a fila semanalmente", ["s3", "s4"], "em_execucao"),
  passoDaSnT("s3", "1.1.1", 2, "s2", "Enxergar a fila em tempo real", "Publicar um painel de fila", [], "validado"),
  passoDaSnT("s4", "1.1.2", 2, "s2", "Eliminar a espera por conferência", "Conferir na entrada", [], "nao_validado"),
  passoDaSnT("s5", "1.2", 1, "s1", "Formar a equipe necessária", "", []),
];

export const SNT: SnT = {
  id: "p-snt",
  nome: "Dobrar a capacidade de atendimento",
  ferramenta: "snt",
  descricao_do_problema: "",
  versao: 8,
  meta_global:
    "Dobrar a capacidade de atendimento da Instituição Horizonte em doze meses sem perder a qualidade acadêmica.",
  passos: PASSOS_DA_SNT,
  raizes: ["s1"],
};

/** A ficha do passo `1.1`, com as três leituras dirigidas montadas no servidor (RF-13). */
export const FICHA_DO_PASSO: FichaDoPassoSnT = {
  ...PASSOS_DA_SNT[1]!,
  leituras: [
    {
      papel: "paralela",
      texto: "No contexto de <1.1> Reduzir o tempo de espera pela metade, …",
      aplicavel: true,
      completa: false,
    },
    {
      papel: "necessidade_ao_pai",
      texto:
        "Para alcançar <1> Atender o dobro de pessoas com a estrutura atual, é necessário <1.1> Reduzir o tempo de espera pela metade porque …",
      aplicavel: true,
      completa: false,
    },
    {
      papel: "suficiencia_dos_filhos",
      texto:
        "<1.1.1> Enxergar a fila em tempo real e <1.1.2> Eliminar a espera por conferência bastam para <1.1> Reduzir o tempo de espera pela metade porque …",
      aplicavel: true,
      completa: false,
    },
  ],
};

export const ACOMPANHAMENTO_DA_SNT: AcompanhamentoDaSnT = {
  passos: 5,
  por_status: { nenhum: 2, validado: 1, nao_validado: 1, em_execucao: 1 },
  progresso: 0.2,
  pendencias: [
    { no_id: "s2", numero: "1.1", tipo: "sem_premissa_de_necessidade" },
    { no_id: "s2", numero: "1.1", tipo: "sem_premissa_de_suficiencia" },
    { no_id: "s5", numero: "1.2", tipo: "sem_tatica" },
  ],
};

export const TABELA_DA_SNT: TabelaDaSnT = {
  linhas: PASSOS_DA_SNT.map((passo) => ({
    no_id: passo.id,
    numero: passo.numero,
    nivel: passo.nivel,
    pai_id: passo.pai_id,
    estrategia: passo.estrategia,
    tatica: passo.tatica,
    categoria: passo.categoria,
    status: passo.status,
    filhos: passo.filhos.length,
    tem_premissa_paralela: false,
    tem_premissa_de_necessidade: false,
    tem_premissa_de_suficiencia: false,
  })),
};


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
    arf: {
      criarProjeto: async () => ARF,
      abrir: async () => ARF,
      adicionarNo: async () => ARF.nos[1]!,
      editarNo: async () => ARF.nos[1]!,
      moverNo: async () => ARF.nos[1]!,
      mudarPapel: async () => ARF.nos[1]!,
      excluirNo: async () => undefined,
      ligar: async () => ARF.elos[0]!,
      excluirAresta: async () => undefined,
      examinarElo: async () => ARF.elos[0]!,
      formarConector: async () => ARF,
      desfazerConector: async () => undefined,
      espelhar: async () => ARF.espelhos[0]!,
      desfazerEspelho: async () => undefined,
      marcarRamo: async () => ARF.ramos[0]!,
      mudarRamo: async () => ARF.ramos[0]!,
      verificar: async () => ARF.verificacao,
    },
    apr: {
      criarProjeto: async () => APR,
      abrir: async () => APR,
      adicionarNo: async () => APR.nos[1]!,
      editarNo: async () => APR.nos[1]!,
      moverNo: async () => APR.nos[1]!,
      mudarPapel: async () => APR.nos[1]!,
      excluirNo: async () => undefined,
      verbalizacao: async () => ({
        papel: "obstaculo" as const,
        veredito: "atende" as const,
        avisos: [],
        versao_do_lexico: "pt-1",
      }),
      depender: async () => APR.dependencias[0]!,
      excluirDependencia: async () => undefined,
      parear: async () => APR.pares[0]!,
      desfazerPar: async () => undefined,
      julgar: async () => APR.pares[0]!,
      formarElipse: async () => ({ id: "el1", destino_id: "oi1", dependencias: ["d1"], leitura: "" }),
      desfazerElipse: async () => undefined,
      sequenciar: async () => APR.sequenciamento,
      resumo: async () => RESUMO_DA_APR,
    },
    at: {
      criarProjeto: async () => AT,
      abrir: async () => AT,
      registrarPasso: async () => AT.passos[0]!,
      editarPasso: async () => AT.passos[0]!,
      excluirPasso: async () => undefined,
      mudarStatus: async () => AT.passos[1]!,
      preceder: async () => AT.precedencias[0]!,
      excluirPrecedencia: async () => undefined,
    },
    /**
     * M5 — a árvore de Estratégia & Táticas. Nenhum método aceita número de passo: o
     * número é calculado no servidor e chega pronto (RN-01).
     */
    snt: {
      criarProjeto: async () => SNT,
      abrir: async () => SNT,
      editarMetaGlobal: async () => SNT,
      adicionarPasso: async () => PASSOS_DA_SNT[4]!,
      abrirPasso: async () => FICHA_DO_PASSO,
      editarPasso: async () => FICHA_DO_PASSO,
      editarPremissas: async () => FICHA_DO_PASSO,
      previaDeMover: async () => ({
        mudancas: [{ no_id: "s2", numero_atual: "1.1", numero_novo: "2" }],
      }),
      mover: async () => SNT,
      previaDeExclusao: async () => ({
        no_id: "s2",
        numero: "1.1",
        passos: 3,
        primeiro_nivel: PASSOS_DA_SNT.filter((p) => p.pai_id === "s2"),
      }),
      excluirSubarvore: async () => SNT,
      mudarStatus: async () => FICHA_DO_PASSO,
      acompanhamento: async () => ACOMPANHAMENTO_DA_SNT,
      tabela: async () => TABELA_DA_SNT,
    },
    cadeia: {
      promover: async () => NUVEM,
      semear: async () => ARF,
      derivarApr: async () => APR,
      derivarAt: async () => AT,
      abrir: async () => CADEIA,
      referencias: async () =>
        CADEIA.elos.map((e) => ({
          id: e.referencia_id,
          tipo: e.tipo,
          origem: e.origem,
          destino: e.destino,
          estado: e.estado,
          motivo: e.motivo,
        })),
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
