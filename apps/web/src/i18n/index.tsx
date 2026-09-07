/**
 * Internacionalização — português e inglês desde o primeiro dia (RI-10 da spec 005,
 * RI-11 da spec 007), e não como camada acrescentada depois.
 *
 * Siglas, uma vez: **UDE** — Efeito Indesejável · **API** — interface de programação de
 * aplicações · **ARA** — Árvore da Realidade Atual.
 *
 * Duas diferenças em relação ao `i18n/` da 4ª geração da linhagem, que é de onde a forma
 * veio (`tocbuilderv3/i18n/I18nProvider.tsx`):
 *
 * 1. **A chave é tipada.** `t("projetos.titulo")` compila; `t("projetos.titlo")` não.
 *    Lá, `t` recebia `string` e a chave errada aparecia crua na tela.
 * 2. **A tabela inglesa tem o tipo da portuguesa.** Chave faltando é erro de compilação —
 *    lá, `pt.ts` e `en.ts` divergiram em silêncio.
 *
 * O idioma também viaja para o serviço: a validação formal de UDE é feita no domínio, e o
 * léxico dela é por idioma (`POST /toc/ara/validacoes` recebe `idioma`).
 */
import { createContext, useCallback, useContext, useMemo, useState, type ReactNode } from "react";
import { pt, type Dicionario } from "./pt";
import { en } from "./en";

export type Idioma = "pt" | "en";

const TABELAS: Record<Idioma, Dicionario> = { pt, en };

/** Todos os caminhos de folha do dicionário, como união de literais. */
type Caminhos<T> = T extends string
  ? ""
  : {
      [K in keyof T & string]: Caminhos<T[K]> extends "" ? K : `${K}.${Caminhos<T[K]>}`;
    }[keyof T & string];

export type ChaveDeTraducao = Caminhos<Dicionario>;

export type Parametros = Record<string, string | number>;

/**
 * Os espaços de nome cujas chaves são **códigos vindos do servidor** (status, veredito,
 * critério, classe de aresta, separação TRIZ…). Estão listados porque `tc` traduz um
 * código que a interface não escolheu: a lista é o contrato entre as duas pontas.
 */
export type EspacoDeCodigo =
  | "criterio"
  | "aviso"
  | "status"
  | "erro"
  | "veredito"
  | "classe"
  | "papel"
  | "ferramenta"
  | "estado_do_exame"
  | "estado_da_premissa"
  | "status_da_injecao"
  | "separacao"
  // Os dois da governança: `origem` (`humano` | `ia`) e o desfecho do §A.3 do Anexo A —
  // os dois chegam do servidor como código fechado, e a tela nunca os inventa.
  | "origem_da_proposta"
  | "desfecho"
  // M6 — a regra da pendência de um passo da jornada de focalização (spec 009, RF-12).
  // Ela chega do servidor como código estável (`sem_restricao`, `decisao_ausente`,
  // `heranca_pendente`), e a tela traduz por código — nunca por texto da mensagem.
  | "pendencia_da_focalizacao"
  // M4 — Árvores de Futuro e Implementação (spec 008). Sete vocabulários fechados que o
  // serviço publica e a interface NUNCA inventa: o papel do nó nas duas árvores, o estado
  // do ramo negativo, o status do passo, o tipo e o estado de uma referência da cadeia, e
  // o aviso de verbalização de obstáculo.
  | "papel_na_arf"
  | "estado_do_ramo"
  | "papel_na_apr"
  | "status_do_passo"
  | "tipo_de_referencia"
  | "estado_da_referencia"
  | "aviso_de_verbalizacao";

/** De onde o idioma efetivo veio — e a ordem é a do RF-12, nesta sequência. */
export type OrigemDoIdioma = "preferencia" | "embarque" | "lingua_fonte";

/** A língua-fonte do produto (RN-01): toda chave existe primeiro nela. */
export const LINGUA_FONTE: Idioma = "pt";

export interface IdiomaEfetivo {
  idioma: Idioma;
  origem: OrigemDoIdioma;
  /** O motivo por extenso, para diagnóstico — não é texto de tela. */
  motivo: string;
}

/** Uma linha de log estruturado. Sai por `registrar`, nunca por `console` direto. */
export type LinhaDeDiagnostico = Record<string, string>;

export interface EntradaDoIdioma {
  /** O que a pessoa escolheu, quando escolheu (persistida por (inquilino, usuário)). */
  preferencia?: Idioma | string | null;
  /** O que o embarque declarou no envelope `ghd.*` — lido como DADO (INT-01). */
  doEmbarque?: Idioma | string | null;
  registrar?: (linha: LinhaDeDiagnostico) => void;
}

function idiomaValido(valor: unknown): valor is Idioma {
  return valor === "pt" || valor === "en";
}

/**
 * RF-12 — `preferência da pessoa → idioma do embarque → língua-fonte`, com o MOTIVO junto.
 *
 * Função pura, e é isso que importa: a preferência entra por argumento, venha ela do
 * servidor, do embarque ou de um teste. Na linhagem a mesma decisão vivia dentro do
 * provedor, lendo `localStorage` na hora (`tocbuilderv3/i18n/I18nProvider.tsx:15`) — e por
 * isso a escolha morria com o dispositivo e não havia como testá-la sem navegador.
 *
 * Valor que a aplicação não fala é tratado como se não tivesse vindo: o hospedeiro é dado,
 * nunca instrução (P2), e um `locale` inesperado não escolhe tela nenhuma.
 */
export function resolverIdiomaEfetivo(entrada: EntradaDoIdioma = {}): IdiomaEfetivo {
  if (idiomaValido(entrada.preferencia)) {
    return {
      idioma: entrada.preferencia,
      origem: "preferencia",
      motivo: "preferência de idioma da pessoa",
    };
  }
  if (idiomaValido(entrada.doEmbarque)) {
    return {
      idioma: entrada.doEmbarque,
      origem: "embarque",
      motivo: "idioma declarado pelo embarque do hospedeiro",
    };
  }
  // RF-14: a queda para o padrão é REGISTRADA. Sem esta linha, "por que abriu em
  // português?" só se responde relendo o código.
  entrada.registrar?.({
    evento: "i18n.queda_para_o_padrao",
    idioma: LINGUA_FONTE,
    motivo: "sem preferência e sem idioma no embarque",
  });
  return {
    idioma: LINGUA_FONTE,
    origem: "lingua_fonte",
    motivo: "sem preferência e sem idioma no embarque",
  };
}

/**
 * RF-09/RF-10 — a chave que falta **falha alto**, e nunca vira texto de tela.
 *
 * O defeito que esta classe substitui está medido: `tocbuilderv3/i18n/I18nProvider.tsx:41`
 * fazia `let result = translation || key;`, e a chave crua ia para a tela sem erro, sem log
 * e sem portão. A US-07 diz o custo em uma linha: "quero nunca ver um identificador
 * técnico no lugar de um rótulo, para a ferramenta não parecer quebrada na frente da
 * minha equipe".
 */
export class ChaveDeTraducaoAusente extends Error {
  constructor(readonly chave: string, readonly tela: string = "") {
    super(
      `tradução ausente para a chave "${chave}"` +
        (tela ? ` (tela ${tela})` : "") +
        " — a chave existe na língua-fonte e falta na tradução, ou não existe em nenhuma",
    );
    this.name = "ChaveDeTraducaoAusente";
  }
}

/**
 * `estrito` — desenvolvimento, teste e integração contínua: chave ausente LANÇA.
 * `tolerante` — produção: cai para a língua-fonte e registra (RF-10).
 */
export type ModoDeTraducao = "estrito" | "tolerante";

export interface OpcoesDeTraducao {
  modo?: ModoDeTraducao;
  /** O dicionário da língua-fonte, para a queda do modo tolerante. */
  fonte?: Dicionario;
  /** Identificador da tela, do registro de telas — entra no log, não na mensagem. */
  tela?: string;
  registrar?: (linha: LinhaDeDiagnostico) => void;
}

/** Produção é tolerante; todo o resto é estrito. A CI roda no estrito, e é o ponto. */
export function modoPadrao(): ModoDeTraducao {
  const ambiente = (import.meta as { env?: { PROD?: boolean } }).env;
  return ambiente?.PROD ? "tolerante" : "estrito";
}

function buscar(dicionario: Dicionario | undefined, chave: string): string | undefined {
  let atual: unknown = dicionario;
  for (const parte of chave.split(".")) {
    if (atual && typeof atual === "object" && parte in (atual as object)) {
      atual = (atual as Record<string, unknown>)[parte];
    } else {
      return undefined;
    }
  }
  return typeof atual === "string" ? atual : undefined;
}

function interpolar(texto: string, parametros: Parametros): string {
  return texto.replace(/\{\{(\w+)\}\}/g, (bruto, nome: string) =>
    nome in parametros ? String(parametros[nome]) : bruto,
  );
}

/**
 * Tradução de CÓDIGO vindo do servidor — e ela é tolerante de propósito, sempre.
 *
 * A diferença para `traduzirCom` é o vocabulário: a chave de tela é **fechada e tipada**
 * (chave errada não compila, chave sem tradução é pendência que o portão pega), enquanto
 * o código do servidor é **aberto** — o serviço pode publicar um código novo antes de a
 * interface conhecê-lo. Falhar alto aqui derrubaria a tela por causa de uma recusa que o
 * servidor já explicou em texto; por isso o caminho é a alternativa que ele mandou, e é
 * por isso que o teste de paridade cobre `CODIGOS` separadamente (foi assim que
 * `IDEMPOTENCY_KEY_REUSED` foi encontrado sem tradução).
 */
export function traduzirCodigo(
  dicionario: Dicionario,
  prefixo: string,
  codigo: string,
  alternativa = "",
): string {
  const achado = buscar(dicionario, `${prefixo}.${codigo}`);
  return achado ?? (alternativa || codigo);
}

export function traduzirCom(
  dicionario: Dicionario,
  chave: ChaveDeTraducao,
  parametros: Parametros = {},
  opcoes: OpcoesDeTraducao = {},
): string {
  const achado = buscar(dicionario, chave);
  if (achado !== undefined) return interpolar(achado, parametros);

  const modo = opcoes.modo ?? modoPadrao();
  if (modo === "estrito") throw new ChaveDeTraducaoAusente(chave, opcoes.tela);

  opcoes.registrar?.({ evento: "i18n.chave_ausente", chave, tela: opcoes.tela ?? "" });
  const daFonte = buscar(opcoes.fonte, chave);
  // Vazio, e não a chave: um rótulo em branco é um defeito de tradução; um identificador
  // técnico na tela é a aplicação parecendo quebrada. A chave é tipada e o portão de
  // paridade roda na integração contínua — este caminho é rede, não desenho.
  return daFonte === undefined ? "" : interpolar(daFonte, parametros);
}

export interface ContextoDeIdioma {
  idioma: Idioma;
  trocarIdioma: (idioma: Idioma) => void;
  t: (chave: ChaveDeTraducao, parametros?: Parametros) => string;
  /** Tradução por código vindo do servidor (critério, aviso, status, erro). */
  tc: (prefixo: EspacoDeCodigo, codigo: string, alternativa?: string) => string;
}

const Contexto = createContext<ContextoDeIdioma | undefined>(undefined);

export function ProvedorDeIdioma({
  children,
  idiomaInicial = "pt",
}: {
  children: ReactNode;
  idiomaInicial?: Idioma;
}) {
  const [idioma, setIdioma] = useState<Idioma>(idiomaInicial);

  const t = useCallback(
    (chave: ChaveDeTraducao, parametros: Parametros = {}) =>
      traduzirCom(TABELAS[idioma], chave, parametros),
    [idioma],
  );

  const tc = useCallback(
    (prefixo: EspacoDeCodigo, codigo: string, alternativa = "") =>
      traduzirCodigo(TABELAS[idioma], prefixo, codigo, alternativa),
    [idioma],
  );

  const valor = useMemo<ContextoDeIdioma>(
    () => ({ idioma, trocarIdioma: setIdioma, t, tc }),
    [idioma, t, tc],
  );

  return <Contexto.Provider value={valor}>{children}</Contexto.Provider>;
}

export function useI18n(): ContextoDeIdioma {
  const contexto = useContext(Contexto);
  if (!contexto) throw new Error("useI18n exige <ProvedorDeIdioma> acima na árvore");
  return contexto;
}

export { pt, en };
export type { Dicionario };
