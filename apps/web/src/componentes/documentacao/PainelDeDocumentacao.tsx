/**
 * E8.4 — o painel lateral de documentação embutida (spec 011, RI-04 e RI-05).
 *
 * Siglas, uma vez: **UI** — interface de usuário · **ARA** — Árvore da Realidade Atual ·
 * **NC** — Nuvem de Conflito · **IA** — inteligência artificial.
 *
 * **A forma vem da linhagem, e ela acertou aqui**: `tocbuilderv3/components/DocsView.tsx`
 * tinha índice por tópico à esquerda, corpo à direita e um botão que levava à ferramenta
 * descrita. O que muda é tudo o que estava em volta:
 *
 * - **painel lateral, não modal bloqueante** (RI-04): o diagrama continua carregado
 *   atrás, e fechar devolve a pessoa exatamente onde ela estava;
 * - **âncora** (RF-20): a ajuda de um campo abre o painel NO TRECHO daquele campo, e não
 *   no começo do verbete;
 * - **foco devolvido ao controle de origem** (RI-05), com `Escape` fechando e o foco
 *   entrando no painel ao abrir — painel que rouba o foco e não o devolve é armadilha de
 *   teclado;
 * - **carregamento sob demanda** (RNF-09): o corpo do verbete chega por `import()`.
 *
 * Nada aqui é gerado por modelo em tempo de execução (RF-24, ADR 0007 — *Architecture
 * Decision Record*): o conteúdo é arquivo do repositório.
 */
import { useCallback, useEffect, useRef, useState } from "react";

import { INDICE, carregarVerbete } from "../../documentacao/acervo";
import { apresentar, type VerbeteApresentado } from "../../documentacao/tipos";
import { useI18n, type ChaveDeTraducao } from "../../i18n";

export interface PainelDeDocumentacaoProps {
  /** A ferramenta cujo verbete abre primeiro. */
  ferramenta: string;
  /** A âncora em que o painel abre — o trecho ligado ao campo de origem (RF-20). */
  ancora?: string;
  aoFechar: () => void;
  /** Leva à ferramenta descrita, quando a pessoa ainda não está nela (RI-06). */
  aoIrParaFerramenta?: (ferramenta: string) => void;
}

export function PainelDeDocumentacao({
  ferramenta,
  ancora,
  aoFechar,
  aoIrParaFerramenta,
}: PainelDeDocumentacaoProps) {
  const { t, idioma } = useI18n();
  const [aberto, setAberto] = useState(ferramenta);
  const [apresentado, setApresentado] = useState<VerbeteApresentado | null>(null);
  const [falhou, setFalhou] = useState(false);
  const painel = useRef<HTMLElement | null>(null);
  // O elemento que tinha o foco quando o painel abriu. É para ele que o foco volta —
  // guardar isto no primeiro render é o que torna a devolução possível (RI-05).
  const origemDoFoco = useRef<Element | null>(
    typeof document === "undefined" ? null : document.activeElement,
  );

  useEffect(() => {
    let ativo = true;
    setApresentado(null);
    setFalhou(false);
    carregarVerbete(aberto)
      .then((verbete) => {
        if (ativo) setApresentado(apresentar(verbete, idioma));
      })
      .catch(() => {
        if (ativo) setFalhou(true);
      });
    return () => {
      ativo = false;
    };
  }, [aberto, idioma]);

  const fechar = useCallback(() => {
    const origem = origemDoFoco.current;
    aoFechar();
    if (origem instanceof HTMLElement) origem.focus();
  }, [aoFechar]);

  useEffect(() => {
    painel.current?.focus();
  }, []);

  useEffect(() => {
    function aoTeclar(evento: KeyboardEvent) {
      if (evento.key === "Escape") fechar();
    }
    document.addEventListener("keydown", aoTeclar);
    return () => document.removeEventListener("keydown", aoTeclar);
  }, [fechar]);

  // A âncora só vale para o verbete com que o painel abriu: navegar para outro tópico
  // recomeça do início dele, que é o que a pessoa espera ao trocar de assunto.
  const ancoraEmUso = aberto === ferramenta ? ancora : undefined;
  useEffect(() => {
    if (!apresentado || !ancoraEmUso) return;
    const alvo = painel.current?.querySelector(`#verbete-${ancoraEmUso}`);
    if (!(alvo instanceof HTMLElement)) return;
    // O foco vai para a seção ancorada, e não só a rolagem: quem chegou aqui por teclado
    // continua no teclado, e um leitor de tela anuncia o trecho certo (RI-05). A rolagem
    // é o complemento visual, e é chamada com guarda porque nem todo ambiente a
    // implementa — um painel que estoura por causa dela seria pior que um sem rolagem.
    alvo.focus();
    alvo.scrollIntoView?.();
  }, [apresentado, ancoraEmUso]);

  return (
    <aside
      className="painel-de-documentacao"
      role="complementary"
      aria-label={t("documentacao.titulo")}
      tabIndex={-1}
      ref={painel}
    >
      <header className="painel-de-documentacao-cabecalho">
        <h2>{t("documentacao.titulo")}</h2>
        <button type="button" onClick={fechar} aria-label={t("documentacao.fechar")}>
          {t("app.fechar")}
        </button>
      </header>

      <div className="painel-de-documentacao-corpo">
        <nav aria-label={t("documentacao.indice")}>
          <ul>
            {INDICE.map((entrada) => (
              <li key={entrada.ferramenta}>
                <button
                  type="button"
                  aria-current={entrada.ferramenta === aberto}
                  onClick={() => setAberto(entrada.ferramenta)}
                >
                  {t(entrada.chaveDoTitulo as ChaveDeTraducao)}
                </button>
              </li>
            ))}
          </ul>
        </nav>

        <article>
          {falhou ? <p role="alert">{t("documentacao.sem_verbete")}</p> : null}
          {!apresentado && !falhou ? <p role="status">{t("app.carregando")}</p> : null}
          {apresentado ? (
            <>
              <h3>{apresentado.conteudo.titulo}</h3>
              {apresentado.traducaoPendente ? (
                // F8.4.3: conteúdo na língua-fonte COM aviso — nunca uma tela vazia.
                <p className="aviso-de-traducao" role="note">
                  {t("documentacao.traducao_pendente")}
                </p>
              ) : null}
              <p className="verbete-resposta">{apresentado.conteudo.resposta}</p>

              {apresentado.conteudo.secoes.map((secao) => (
                <section key={secao.ancora} id={`verbete-${secao.ancora}`} tabIndex={-1}>
                  <h4>{secao.titulo}</h4>
                  {secao.paragrafos.map((paragrafo, indice) => (
                    <p key={indice}>{paragrafo}</p>
                  ))}
                </section>
              ))}

              <section className="verbete-exemplo">
                <h4>{t("documentacao.exemplo")}</h4>
                <p>{apresentado.conteudo.exemplo}</p>
              </section>

              {aoIrParaFerramenta ? (
                <button type="button" onClick={() => aoIrParaFerramenta(aberto)}>
                  {t("documentacao.ir_para_a_ferramenta")}
                </button>
              ) : null}
            </>
          ) : null}
        </article>
      </div>
    </aside>
  );
}
