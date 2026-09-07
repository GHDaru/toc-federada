/**
 * A árvore de Estratégia & Táticas (S&T) desenhada **da estrutura** (RI-01).
 *
 * Siglas, uma vez: **S&T** — Estratégia & Táticas (*Strategy & Tactics*) · **RI/RF/RN** —
 * requisito de interface / funcional / regra de negócio da spec 010 · **TOC** — Teoria
 * das Restrições.
 *
 * Três decisões desta superfície, e as três respondem a um defeito medido da linhagem:
 *
 * 1. **O usuário não arruma caixas.** A quarta geração guardava `pos_x`/`pos_y` por passo
 *    (`tocbuilderv3/types.ts:296-297`) e deixava a arrumação para quem usava; aqui o
 *    layout é calculado da hierarquia — meta global no topo, raízes na primeira linha,
 *    filhos abaixo do pai —, e o que a pessoa move é a **posição na árvore**, não o
 *    retângulo na tela.
 * 2. **O status distingue por forma e rótulo, nunca só por cor** (RI-02). A paleta da
 *    linhagem (`tocbuilderv3/constants.ts:438-441`) é herdada como intenção: quem não
 *    distingue as cores continua lendo o status escrito no nó.
 * 3. **O número é lido, nunca digitado** (RF-06). Ele vem do servidor calculado da
 *    posição, e não há campo de número em lugar nenhum desta árvore.
 */
import type { PassoDaSnT, StatusDoPassoSnT } from "../../dominio/tipos";
import { useI18n } from "../../i18n";

/** A forma que acompanha a cor — RI-02: cor sozinha não distingue nada para quem não a vê. */
const FORMA_POR_STATUS: Record<StatusDoPassoSnT, string> = {
  nenhum: "○",
  validado: "✓",
  nao_validado: "✗",
  em_execucao: "▶",
};

export interface ArvoreDeSnTProps {
  metaGlobal: string;
  passos: readonly PassoDaSnT[];
  raizes: readonly string[];
  selecionado: string | null;
  /** Quais passos ficam visíveis; `null` = todos (o filtro por status é do painel). */
  visiveis: readonly string[] | null;
  aoSelecionar(noId: string): void;
  aoAdicionarFilho(noId: string): void;
  aoAdicionarIrmao(noId: string): void;
  aoAdicionarRaiz(): void;
  somenteLeitura?: boolean;
}

export function ArvoreDeSnT({
  metaGlobal,
  passos,
  raizes,
  selecionado,
  visiveis,
  aoSelecionar,
  aoAdicionarFilho,
  aoAdicionarIrmao,
  aoAdicionarRaiz,
  somenteLeitura = false,
}: ArvoreDeSnTProps) {
  const { t } = useI18n();
  const porId = new Map(passos.map((passo) => [passo.id, passo]));
  const filtro = visiveis === null ? null : new Set(visiveis);

  function ramo(noId: string): JSX.Element | null {
    const passo = porId.get(noId);
    if (!passo) return null;
    // O filtro esconde o passo, mas o ramo continua descendo: um ancestral fora do filtro
    // ainda precisa aparecer para dar contexto ao descendente filtrado (RF-18).
    const escondido = filtro !== null && !filtro.has(noId);
    const filhos = passo.filhos.map((filho) => ramo(filho)).filter(Boolean);
    if (escondido && filhos.length === 0) return null;
    return (
      <li key={noId} className="ramo-da-snt">
        <article
          className={`no-da-snt status-${passo.status}${
            selecionado === noId ? " selecionado" : ""
          }${escondido ? " fora-do-filtro" : ""}`}
          aria-current={selecionado === noId}
        >
          <button
            type="button"
            className="abrir-passo"
            onClick={() => aoSelecionar(noId)}
            title={passo.estrategia}
          >
            <span className="numero-do-passo">{passo.numero}</span>{" "}
            <span className="estrategia-do-passo">{passo.estrategia}</span>
          </button>
          <p className="status-do-passo">
            <span aria-hidden="true" className="forma-do-status">
              {FORMA_POR_STATUS[passo.status]}
            </span>{" "}
            {t(`snt.status.${passo.status}`)}
          </p>
          {somenteLeitura ? null : (
            <p className="acoes-do-no">
              <button type="button" onClick={() => aoAdicionarFilho(noId)}>
                {t("snt.adicionar_filho")}
              </button>
              <button type="button" onClick={() => aoAdicionarIrmao(noId)}>
                {t("snt.adicionar_irmao")}
              </button>
            </p>
          )}
        </article>
        {filhos.length ? <ul className="filhos-da-snt">{filhos}</ul> : null}
      </li>
    );
  }

  return (
    <section className="arvore-da-snt" aria-label={t("snt.arvore")}>
      <header className="meta-global" aria-labelledby="meta-global-titulo">
        <h3 id="meta-global-titulo">{t("snt.meta_global")}</h3>
        <p className="meta-global-texto">{metaGlobal}</p>
      </header>
      {passos.length === 0 ? (
        <p className="vazio">{t("snt.arvore_vazia")}</p>
      ) : (
        <ul className="raizes-da-snt">{raizes.map((raiz) => ramo(raiz))}</ul>
      )}
      {somenteLeitura ? null : (
        <button type="button" className="adicionar-raiz" onClick={aoAdicionarRaiz}>
          {t("snt.adicionar_raiz")}
        </button>
      )}
    </section>
  );
}
