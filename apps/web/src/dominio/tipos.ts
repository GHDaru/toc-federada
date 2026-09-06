/**
 * Os tipos do domínio, **espelhados** da superfície HTTP do serviço — sem regra duplicada.
 *
 * Siglas, uma vez: **ARA** — Árvore da Realidade Atual · **NC** — Nuvem de Conflito ·
 * **UDE** — Efeito Indesejável (*Undesirable Effect*) · **TOC** — Teoria das Restrições ·
 * **TRIZ** — Teoria da Resolução Inventiva de Problemas · **API** — interface de
 * programação de aplicações · **HTTP** — *HyperText Transfer Protocol*.
 *
 * **Este arquivo não decide nada.** Validação de UDE, suficiência causal, topologia da
 * nuvem, transição de status: tudo isso é regra de domínio do serviço
 * (`apps/api/src/toc_api/dominio/`), testada lá sem rede e sem banco. Repetir a regra aqui
 * criaria uma segunda fonte de verdade que divergiria no primeiro ajuste — que é
 * exatamente o defeito que a 4ª geração da linhagem tinha, com a validação de UDE morando
 * num prompt do cliente (`tocbuilderv3/constants.ts`) e a chave do provedor no navegador
 * (`tocbuilderv3/services/geminiService.ts:16`).
 *
 * O que a interface faz com estes tipos é **apresentar**: cor, ícone, ordem, tradução.
 */

// -- M1: projeto, nó, aresta --------------------------------------------------------

export type Ferramenta = "generico" | "ara" | "nc" | (string & {});
export type EstadoDoProjeto = "ativo" | "excluido";

export interface Posicao {
  x: number;
  y: number;
}

export interface ProjetoResumo {
  id: string;
  nome: string;
  ferramenta: Ferramenta;
  descricao_do_problema: string;
  estado: EstadoDoProjeto;
  versao: number;
  criado_em: string;
  alterado_em: string;
  excluido_em?: string | null;
}

export interface No {
  id: string;
  titulo: string;
  descricao: string;
  tipo: string;
  posicao: Posicao;
  recolhido: boolean;
}

export interface Aresta {
  id: string;
  origem_id: string;
  destino_id: string;
  rotulo: string;
}

export interface Projeto extends ProjetoResumo {
  nos: No[];
  arestas: Aresta[];
}

export interface ExclusaoDeNo {
  no_id: string;
  arestas_removidas: string[];
}

// -- M2: ARA ------------------------------------------------------------------------

export type StatusDeValidacao = "pendente" | "requer_refinamento" | "validado" | "rejeitado";
export type EstadoDoExame = "nao_examinado" | "suficiente" | "insuficiente" | "com_reserva";
export type ClasseDeCriterio = "decidivel" | "julgamento";
export type Veredito = "atende" | "nao_atende" | "indeterminado";

export interface VereditoDeCriterio {
  codigo: string;
  caracteristica: string;
  /** Chave de i18n estável — a mesma da regra de domínio (RNF-09 da spec 005). */
  nome: string;
  classe: ClasseDeCriterio;
  regra: string;
  enunciado: string;
  veredito: Veredito;
  motivo: string;
  /** O trecho do texto que motivou o veredito — o que a ficha marca inline (RI-03). */
  trecho: string;
}

export interface ValidacaoFormal {
  texto: string;
  idioma: string;
  versao_do_lexico: string;
  aprovado_nos_decidiveis: boolean;
  vereditos: VereditoDeCriterio[];
  reprovacoes: string[];
  pendencias_de_julgamento: string[];
}

export interface FichaDeUde {
  area_impactada?: string;
  objetivo_afetado?: string;
  evidencias?: string[];
  frequencia?: string;
  impactos_estimados?: string;
}

export interface Parecer {
  autor: string;
  origem: "humano" | "catalogo";
  favoravel: boolean;
  justificativa: string;
  instante: string;
  proposta_id?: string | null;
  criterios?: string[];
}

export interface Ude {
  no_id: string;
  titulo: string;
  status: StatusDeValidacao;
  ficha: FichaDeUde;
  validacao: ValidacaoFormal;
  pareceres: Parecer[];
}

export interface Exame {
  aresta_id: string;
  estado: EstadoDoExame;
  reserva: string;
}

export interface Elo {
  aresta_id: string;
  leitura: string;
  exame: Exame;
}

export interface ConectorLido {
  id: string;
  destino_id: string;
  arestas: string[];
  leitura: string;
}

export interface Ara {
  projeto: Projeto;
  udes: Ude[];
  elos: Elo[];
  conectores: ConectorLido[];
  resumo_por_status: Record<string, number>;
}

export interface Alcance {
  no_id: string;
  udes_alcancados: string[];
  fracao: number;
}

export interface RelatorioEstrutural {
  fragmentos: string[][];
  entradas: string[];
  alcances: Alcance[];
  udes_nao_alcancados: string[];
  elos_nao_examinados: string[];
  orfaos: string[];
  ciclos: string[][];
  nos_em_ciclo: string[];
  causas_raiz_candidatas: string[];
  causa_raiz_candidata?: string | null;
  observacoes: string[];
  total_de_nos: number;
  total_de_udes: number;
  resumo: Record<string, number>;
}

// -- M3: Nuvem de Conflito ----------------------------------------------------------

export type PapelDaEntidade = "A" | "B" | "C" | "D" | "D_PRIME";
export type ChaveDaAresta = "A_B" | "A_C" | "B_D" | "C_D_PRIME" | "D_C" | "D_PRIME_B" | "D_D_PRIME";
export type ClasseDaAresta = "necessidade" | "pre_requisito" | "perigo" | "conflito";
export type EstadoDaPremissa = "vigente" | "desafiada";
export type StatusDeInjecao = "candidata" | "escolhida" | "descartada";
export type SeparacaoTRIZ = "espaco" | "tempo" | "partes" | "grau" | "condicao";

export interface AvisoDeFormulacao {
  codigo: string;
  explicacao: string;
  exemplo: string;
}

export interface Semeadura {
  injecao_id: string;
  projeto_destino_id: string | null;
}

export interface Injecao {
  id: string;
  premissa_id: string;
  texto: string;
  status: StatusDeInjecao;
  separacao: SeparacaoTRIZ | null;
  semeadura: Semeadura | null;
}

export interface Premissa {
  id: string;
  aresta: ChaveDaAresta;
  texto: string;
  ordem: number;
  estado: EstadoDaPremissa;
  justificativa: string;
  injecoes: Injecao[];
}

export interface EntidadeDaNuvem {
  papel: PapelDaEntidade;
  no_id: string;
  texto: string;
  /** A posição CANÔNICA vem do servidor (RI-01/RN-01): o usuário edita texto, não caixa. */
  posicao: Posicao;
  avisos: AvisoDeFormulacao[];
}

export interface ArestaDaNuvem {
  chave: ChaveDaAresta;
  classe: ClasseDaAresta;
  aresta_id: string;
  /** A leitura por extenso, montada dos textos ATUAIS das entidades (RF-07). */
  leitura: string;
  premissas: Premissa[];
}

export interface OrigemDaNuvem {
  ferramenta: string;
  projeto_id: string;
  nos: string[];
  leitura: string;
}

export interface Nuvem {
  id: string;
  nome: string;
  ferramenta: Ferramenta;
  descricao_do_problema: string;
  racional: string;
  criado_em: string;
  alterado_em: string;
  origem: OrigemDaNuvem | null;
  entidades: EntidadeDaNuvem[];
  arestas: ArestaDaNuvem[];
}

export interface AvisosDaEntidade {
  papel: PapelDaEntidade;
  avisos: AvisoDeFormulacao[];
}

export interface ValidacaoDaNuvem {
  completude: { sustentadas: number; total: number };
  modelada: boolean;
  arestas_sem_premissa: ChaveDaAresta[];
  arestas_sem_injecao: ChaveDaAresta[];
  separacoes_ausentes: string[];
  avisos: AvisosDaEntidade[];
}

export interface PosicaoDeSolucao {
  chave: ChaveDaAresta;
  classe: ClasseDaAresta;
  leitura: string;
  pendente: boolean;
  injecoes: Injecao[];
}

export interface Solucao {
  posicoes: PosicaoDeSolucao[];
}

export interface LinhaDaMatriz {
  chave: ChaveDaAresta;
  leitura: string;
  premissas: Premissa[];
}

export interface Matriz {
  linhas: LinhaDaMatriz[];
}

export interface SugestaoDeInjecao {
  texto: string;
  separacao: SeparacaoTRIZ | null;
}

export interface SugestaoDePremissa {
  texto: string;
  injecoes: SugestaoDeInjecao[];
}

/**
 * O resultado de uma geração assistida. **Nada foi aplicado**: quem escreve é a proposta
 * governada do catálogo `toc.*`, que nasce `action_proposal` e atravessa a máquina de
 * estados do servidor. Por isso recusar não custa nada (RF-24 da spec 007).
 */
export interface Geracao {
  action_id: string;
  resultado: Record<string, unknown>;
  aviso: string;
}

export interface SugestoesDePremissa {
  action_id: string;
  aresta: ChaveDaAresta;
  sugestoes: SugestaoDePremissa[];
  aviso: string;
}

export interface SugestoesDeInjecao {
  action_id: string;
  premissa_id: string;
  sugestoes: SugestaoDeInjecao[];
  aviso: string;
}

/**
 * O desfecho de UM alvo de um lote (APH-5.9(b) do Padrão APH — Aplicação ↔ Harness).
 * Sete executaram e um não é **dado**, não prosa: é o que a superfície mostra item a item.
 */
export interface DesfechoDeAlvo {
  target: string;
  status: string;
  message: string;
}

/**
 * A proposta de ação — o objeto do gate humano (spec 006).
 *
 * Ela é o que torna "aceitar a geração" diferente de "a tela escreveu": o conteúdo
 * assistido nasce proposta no servidor, atravessa a máquina de estados
 * (`proposed → awaiting_approval → confirmed → executing → executed`) e só então vira
 * escrita — com traço, inclusive quando é recusada.
 *
 * `estado` é onde ela está na máquina; `status` é o desfecho do §A.3 do Anexo A (vazio
 * enquanto ela espera). Os dois viajam porque respondem perguntas diferentes.
 * `origem` (`humano` | `ia`) é **dado exibido, nunca desvio de fluxo** (RI-02).
 */
export interface Proposta {
  proposal_id: string;
  action_id: string;
  titulo: string;
  risk: string;
  requires_confirmation: boolean;
  origem: string;
  estado: string;
  alvos: string[];
  quantidade_de_alvos: number;
  criada_em: string;
  vence_em: string;
  status: string | null;
  mensagem: string;
  outcomes: DesfechoDeAlvo[];
}

/** O corpo de `POST /toc/propostas` — o que a interface leva ao gate. */
export interface PedidoDeProposta {
  action_id: string;
  args: Record<string, unknown>;
  origem?: "humano" | "ia";
  contexto_hash?: string | null;
}

// ---------------------------------------------------------------------------------------
// M6 · Focalização (spec 009) — a jornada dos cinco passos
//
// Estes tipos são **espelho** do que o serviço publica, nunca uma segunda fonte de regra
// (é a mesma disciplina do resto deste arquivo): nada aqui recomputa pendência, aviso ou
// estado de vínculo. Quem os computa é o domínio, no servidor, por função pura — e a
// interface desenha o que recebeu.
// ---------------------------------------------------------------------------------------

/** RN-01: os cinco, nomeados e ordenados. Não se cria, não se exclui, não se reordena. */
export type TipoDePasso = "identificar" | "explorar" | "subordinar" | "elevar" | "recomecar";

export const PASSOS_DA_FOCALIZACAO: readonly TipoDePasso[] = [
  "identificar",
  "explorar",
  "subordinar",
  "elevar",
  "recomecar",
] as const;

export type EstadoDoPasso = "pendente" | "em_andamento" | "concluido";
export type EstadoDoCiclo = "aberto" | "fechado";
export type TipoDeRestricao = "fisica" | "politica" | "de_mercado";
export type VereditoDeHeranca = "pendente" | "mantida" | "revogada";
export type FerramentaVinculada = "ara" | "nc" | "arf" | "apr" | "at";
export type EstadoDoVinculo = "ativo" | "arquivado" | "ausente";

export interface OrigemDaRestricao {
  ferramenta: string;
  projeto_id: string;
  no_id: string;
}

export interface Restricao {
  id: string;
  descricao: string;
  tipo: TipoDeRestricao;
  justificativa: string;
  autor: string;
  registrada_em: string;
  origem: OrigemDaRestricao | null;
}

export interface DecisaoDePasso {
  texto: string;
  autor: string;
  instante: string;
}

export interface NotaDePasso {
  id: string;
  texto: string;
  autor: string;
  instante: string;
}

export interface ReaberturaDePasso {
  justificativa: string;
  autor: string;
  instante: string;
}

/** RI-03: o cartão do vínculo — tipo, projeto, estado e navegação. Nunca o conteúdo. */
export interface VinculoDeFerramenta {
  id: string;
  ferramenta: FerramentaVinculada;
  projeto_id: string;
  papel: string;
  justificativa: string;
  canonico: boolean;
  estado: EstadoDoVinculo;
  nome: string;
  legenda: string;
}

export interface PendenciaDoPasso {
  passo: string;
  regra: string;
  detalhe: string;
}

export interface PassoNaJornada {
  tipo: TipoDePasso;
  estado: EstadoDoPasso;
  decisao: string;
  autor_da_decisao: string;
  decisoes: DecisaoDePasso[];
  notas: NotaDePasso[];
  reaberturas: ReaberturaDePasso[];
  vinculos: VinculoDeFerramenta[];
  canonicas: FerramentaVinculada[];
  avisos: string[];
  /** RF-13: o produto dos passos ANTERIORES do mesmo ciclo — para ninguém decidir no vácuo. */
  herdado: string[];
  pendencias: PendenciaDoPasso[];
}

export interface DecisaoHerdada {
  id: string;
  ciclo_de_origem: number;
  passo: string;
  texto: string;
  veredito: VereditoDeHeranca;
  justificativa: string;
  autor: string;
  julgada_em: string | null;
}

export interface Jornada {
  ciclo_id: string;
  ordem: number;
  estado: EstadoDoCiclo;
  somente_leitura: boolean;
  passo_atual: TipoDePasso;
  restricao: Restricao | null;
  passos: PassoNaJornada[];
  heranca: DecisaoHerdada[];
  herancas_pendentes: number;
  ciclos_no_total: number;
  passos_concluidos: number;
}

export interface CicloNaLinha {
  ciclo_id: string;
  ordem: number;
  estado: EstadoDoCiclo;
  restricao: string | null;
  tipo_de_restricao: TipoDeRestricao | null;
  aberto_em: string;
  fechado_em: string | null;
  decisoes: number;
  vinculos: number;
  herancas: number;
  herancas_pendentes: number;
  passo_atual: TipoDePasso;
}

export interface SistemaAnalisado {
  nome: string;
  descricao: string;
}

export interface AnaliseDeFocalizacao {
  projeto: ProjetoResumo;
  sistema: SistemaAnalisado;
  jornada: Jornada;
  linha_do_tempo: CicloNaLinha[];
}

/** RF-03/RI-07: passo atual e restrição vigente como colunas de primeira classe. */
export interface AnaliseResumo {
  projeto_id: string;
  nome: string;
  sistema: string;
  ciclo: number;
  passo_atual: TipoDePasso;
  restricao: string | null;
  tipo_de_restricao: TipoDeRestricao | null;
  pendencias: number;
  herancas_pendentes: number;
  alterado_em: string;
}

export interface CandidataARestricao {
  no_id: string;
  titulo: string;
  racional: string;
  udes_alcancados: number;
  fracao: number;
}

/** RF-19: sugerir NÃO aplica — devolve as candidatas e o `action_id` da ação governada. */
export interface SugestaoDeRestricao {
  ara_projeto_id: string;
  action_id: string;
  aviso: string;
  candidatas: CandidataARestricao[];
}
