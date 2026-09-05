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
