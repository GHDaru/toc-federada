/**
 * O diagrama da Nuvem de Conflito (NC) — cinco entidades, sete arestas, layout canônico.
 *
 * Siglas, uma vez: **NC** — Nuvem de Conflito · **TOC** — Teoria das Restrições · **RI** —
 * requisito de interface · **SVG** — *Scalable Vector Graphics*.
 *
 * Três coisas que este componente faz e que a 4ª geração da linhagem não fazia:
 *
 * 1. **Desenha as sete arestas.** Lá, `D_C` e `D_D_PRIME` existiam no tipo
 *    (`tocbuilderv3/types.ts:73`) e nunca chegavam à tela
 *    (`components/ConflictCloudView.tsx:148-169` monta cinco). Perigo e conflito são
 *    justamente onde o método morde.
 * 2. **A classe da aresta é dita por escrito.** Traço cheio, traço tracejado e cor são
 *    reforço; o rótulo textual é a informação (RI-02).
 * 3. **A posição vem do servidor.** `RN-01` fixa a topologia e as posições canônicas: o
 *    usuário edita texto, não arruma caixas — e por isso não existe arrastar aqui.
 */
import { useState } from "react";
import type { ArestaDaNuvem, ChaveDaAresta, EntidadeDaNuvem, Nuvem, PapelDaEntidade } from "../../dominio/tipos";
import { useI18n } from "../../i18n";

const LARGURA = 240;
const ALTURA = 96;

/** O plano tem tamanho fixo: as posições das entidades são canônicas e vêm do servidor. */
const LARGURA_DO_PLANO = 1020;
const ALTURA_DO_PLANO = 470;

/**
 * Onde a legenda de cada aresta descansa. As entidades ocupam faixas conhecidas — A em
 * (0,160), B em (280,40), C em (280,280), D em (560,40) e D′ em (560,280), com 240×96 cada
 * —, e cada legenda cai numa **faixa livre** entre elas. Escrever isto como tabela, e não
 * como cálculo esperto, é o que permite olhar a tela e conferir.
 */
const CENTRO_DA_LEGENDA: Record<ChaveDaAresta, { x: number; y: number }> = {
  A_B: { x: 30, y: 104 },         // corredor acima de A, à esquerda de B
  A_C: { x: 30, y: 292 },         // corredor abaixo de A, à esquerda de C
  B_D: { x: 450, y: 2 },          // faixa acima de B e D
  C_D_PRIME: { x: 450, y: 400 },  // faixa abaixo de C e D′
  D_C: { x: 600, y: 152 },        // corredor entre as duas faixas (perigo de D)
  D_PRIME_B: { x: 600, y: 218 },  // corredor entre as duas faixas (perigo de D′)
  D_D_PRIME: { x: 840, y: 196 },  // à direita do par em conflito
};

const PARES: Record<ChaveDaAresta, [PapelDaEntidade, PapelDaEntidade]> = {
  A_B: ["A", "B"],
  A_C: ["A", "C"],
  B_D: ["B", "D"],
  C_D_PRIME: ["C", "D_PRIME"],
  D_C: ["D", "C"],
  D_PRIME_B: ["D_PRIME", "B"],
  D_D_PRIME: ["D", "D_PRIME"],
};

/**
 * O ponto onde a linha toca a BORDA da caixa, e não o centro dela. Sem isto, a ponta da
 * seta fica escondida atrás do nó de destino — que foi o que a 4ª geração entregou, com o
 * conflito e o perigo desenhados como duas linhas sem direção legível.
 */
function naBorda(
  centro: { x: number; y: number },
  alvo: { x: number; y: number },
  folga = 10,
): { x: number; y: number } {
  const dx = alvo.x - centro.x;
  const dy = alvo.y - centro.y;
  if (!dx && !dy) return centro;
  const escala = Math.min(
    Math.abs(dx) > 0.01 ? LARGURA / 2 / Math.abs(dx) : Number.POSITIVE_INFINITY,
    Math.abs(dy) > 0.01 ? ALTURA / 2 / Math.abs(dy) : Number.POSITIVE_INFINITY,
  );
  const comprimento = Math.hypot(dx, dy);
  const extra = folga / comprimento;
  return { x: centro.x + dx * (escala + extra), y: centro.y + dy * (escala + extra) };
}

export interface DiagramaDaNuvemProps {
  nuvem: Nuvem;
  arestaAberta: ChaveDaAresta | null;
  aoAbrirAresta(chave: ChaveDaAresta): void;
  aoEditarEntidade(papel: PapelDaEntidade, texto: string): Promise<void>;
  /** Rótulo alternativo da posição (a visão de solução mostra injeções no lugar). */
  conteudoDaAresta?(aresta: ArestaDaNuvem): React.ReactNode;
  titulo?: string;
}

function EntidadeNoDiagrama({
  entidade,
  aoEditar,
}: {
  entidade: EntidadeDaNuvem;
  aoEditar(papel: PapelDaEntidade, texto: string): Promise<void>;
}) {
  const { t, tc } = useI18n();
  const [editando, setEditando] = useState(false);
  const [rascunho, setRascunho] = useState(entidade.texto);
  const [avisoAberto, setAvisoAberto] = useState(false);

  return (
    <div
      className={`entidade entidade-${entidade.papel}`}
      data-testid={`entidade-${entidade.papel}`}
      style={{
        transform: `translate(${entidade.posicao.x}px, ${entidade.posicao.y}px)`,
        width: LARGURA,
        minHeight: ALTURA,
      }}
    >
      <p className="entidade-papel">{t(`papel.${entidade.papel}` as "papel.A")}</p>
      {editando ? (
        <input
          autoFocus
          aria-label={t("nuvem.editar_entidade", { papel: entidade.papel })}
          value={rascunho}
          onChange={(e) => setRascunho(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") {
              const limpo = rascunho.trim();
              setEditando(false);
              if (limpo && limpo !== entidade.texto) void aoEditar(entidade.papel, limpo);
            }
            if (e.key === "Escape") {
              setRascunho(entidade.texto);
              setEditando(false);
            }
          }}
        />
      ) : (
        <p
          className="entidade-texto"
          tabIndex={0}
          onDoubleClick={() => {
            setRascunho(entidade.texto);
            setEditando(true);
          }}
          onKeyDown={(e) => {
            if (e.key === "F2" || e.key === "Enter") {
              setRascunho(entidade.texto);
              setEditando(true);
            }
          }}
        >
          {entidade.texto}
        </p>
      )}

      {entidade.avisos.length > 0 ? (
        <div className="entidade-aviso">
          <button
            type="button"
            className="aviso-gatilho"
            aria-label={`${entidade.avisos.length} aviso(s) de formulação`}
            aria-expanded={avisoAberto}
            onClick={() => setAvisoAberto((aberto) => !aberto)}
          >
            ⚠
          </button>
          {avisoAberto ? (
            <ul className="aviso-detalhe">
              {entidade.avisos.map((aviso) => (
                <li key={aviso.codigo}>
                  {/* Traduzido pelo CÓDIGO; o texto do servidor é a alternativa. */}
                  <p>{tc("aviso", aviso.codigo, aviso.explicacao)}</p>
                  <p className="aviso-exemplo">
                    <q>{aviso.exemplo}</q>
                  </p>
                </li>
              ))}
            </ul>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}

export function DiagramaDaNuvem({
  nuvem,
  arestaAberta,
  aoAbrirAresta,
  aoEditarEntidade,
  conteudoDaAresta,
  titulo,
}: DiagramaDaNuvemProps) {
  const { t, tc } = useI18n();
  const porPapel = new Map(nuvem.entidades.map((e) => [e.papel, e]));

  function centro(papel: PapelDaEntidade) {
    const entidade = porPapel.get(papel);
    return {
      x: (entidade?.posicao.x ?? 0) + LARGURA / 2,
      y: (entidade?.posicao.y ?? 0) + ALTURA / 2,
    };
  }

  return (
    <section className="diagrama-da-nuvem" aria-label={titulo ?? t("nuvem.diagrama")}>
      <div
        className="nuvem-plano"
        style={{ width: LARGURA_DO_PLANO, height: ALTURA_DO_PLANO }}
      >
      <svg
        className="nuvem-arestas"
        width={LARGURA_DO_PLANO}
        height={ALTURA_DO_PLANO}
        role="presentation"
      >
        <defs>
          <marker
            id="seta-nuvem"
            viewBox="0 0 10 10"
            refX="9"
            refY="5"
            markerWidth="7"
            markerHeight="7"
            orient="auto-start-reverse"
          >
            <path d="M 0 0 L 10 5 L 0 10 z" fill="currentColor" />
          </marker>
        </defs>
        {nuvem.arestas.map((aresta) => {
          const [origem, destino] = PARES[aresta.chave];
          const centroDaOrigem = centro(origem);
          const centroDoDestino = centro(destino);
          const de = naBorda(centroDaOrigem, centroDoDestino, 2);
          const para = naBorda(centroDoDestino, centroDaOrigem, 10);
          return (
            <path
              key={aresta.chave}
              data-testid={`traco-${aresta.chave}`}
              className={`traco traco-${aresta.classe}`}
              d={`M ${de.x},${de.y} L ${para.x},${para.y}`}
              markerEnd="url(#seta-nuvem)"
              fill="none"
              // Perigo e conflito são tracejados — reforço visual da diferença que o
              // rótulo textual já diz. Nunca é o único sinal.
              {...(aresta.classe === "perigo" || aresta.classe === "conflito"
                ? { strokeDasharray: "8 6" }
                : {})}
            />
          );
        })}
      </svg>

        {nuvem.entidades.map((entidade) => (
          <EntidadeNoDiagrama key={entidade.papel} entidade={entidade} aoEditar={aoEditarEntidade} />
        ))}

        {nuvem.arestas.map((aresta) => {
          const posicao = CENTRO_DA_LEGENDA[aresta.chave];
          const vivas = aresta.premissas.filter((p) => p.estado !== "desafiada");
          return (
            <div
              key={aresta.chave}
              data-testid={`aresta-${aresta.chave}`}
              className={`legenda-da-aresta ${aresta.classe}${arestaAberta === aresta.chave ? " aberta" : ""}`}
              style={{ transform: `translate(${posicao.x}px, ${posicao.y}px)` }}
            >
              <button
                type="button"
                title={aresta.leitura}
                onClick={() => aoAbrirAresta(aresta.chave)}
              >
                {/* O raio é um símbolo à parte, e não um prefixo grudado no rótulo: o
                    rótulo textual precisa ser legível como texto próprio. */}
                {aresta.classe === "conflito" ? <span aria-hidden="true" className="raio">↯</span> : null}
                <span className="classe">{tc("classe", aresta.classe, aresta.classe)}</span>
                {conteudoDaAresta ? (
                  conteudoDaAresta(aresta)
                ) : (
                  <span className="contagem">
                    {aresta.premissas.length === 0
                      ? t("nuvem.sem_premissa_curta")
                      : `${vivas.length}/${aresta.premissas.length}`}
                  </span>
                )}
                {/* A leitura por extenso continua no documento — leitor de tela a lê, o
                    `title` a mostra ao passar o ponteiro e a ficha da aresta a abre. Ela
                    sai do desenho porque sete leituras completas cobrem as cinco
                    entidades, que são o que a nuvem existe para mostrar. */}
                <span className="leitura visualmente-oculto">{aresta.leitura}</span>
              </button>
            </div>
          );
        })}
      </div>
    </section>
  );
}
