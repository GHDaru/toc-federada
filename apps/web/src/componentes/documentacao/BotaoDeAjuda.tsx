/**
 * F8.4.2 — a ajuda contextual ancorada (spec 011, RF-20 e US-11).
 *
 * Siglas, uma vez: **UI** — interface de usuário · **NC** — Nuvem de Conflito.
 *
 * A US-11 é literal: "quero abrir 'o que faz uma premissa ser sustentada' ao lado do campo
 * que estou preenchendo, para decidir sem trocar de contexto". Este botão é isso — ele
 * declara a ferramenta e a **âncora**, e quem monta a tela não escreve texto de ajuda
 * nenhum: o texto mora no acervo versionado.
 *
 * A âncora declarada aqui é conferida pelo portão `scripts/check-documentacao.sh`: âncora
 * que não existe no verbete abriria o painel no lugar errado, em silêncio.
 */
import { useI18n } from "../../i18n";

export interface BotaoDeAjudaProps {
  ferramenta: string;
  ancora: string;
  /** Rótulo acessível — vem do dicionário, como toda cadeia visível. */
  aoAbrir: (ferramenta: string, ancora: string) => void;
}

export function BotaoDeAjuda({ ferramenta, ancora, aoAbrir }: BotaoDeAjudaProps) {
  const { t } = useI18n();
  return (
    <button
      type="button"
      className="botao-de-ajuda"
      aria-label={t("documentacao.ajuda_sobre")}
      data-ferramenta={ferramenta}
      data-ancora={ancora}
      onClick={() => aoAbrir(ferramenta, ancora)}
    >
      {t("documentacao.ajuda")}
    </button>
  );
}
