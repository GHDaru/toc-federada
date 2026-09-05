/**
 * Os três estados que toda tela desenha: carregando, erro (com próxima ação) e vazio.
 *
 * RI-12 da spec 004: "estados de carregamento, erro e recusa de autorização são telas
 * desenhadas com próxima ação clara, não texto cru de exceção". A mensagem vem do
 * **código** da recusa; o texto do servidor nunca é jogado na tela — ele fala de operação
 * e de capability, não da próxima coisa que a pessoa deve fazer.
 */
import type { ReactNode } from "react";
import { useI18n } from "../i18n";
import { mensagemDeErro } from "./mensagemDeErro";

export function Carregando({ rotulo }: { rotulo?: string }) {
  const { t } = useI18n();
  return (
    <p className="carregando" role="status">
      {rotulo ?? t("app.carregando")}
    </p>
  );
}

export function EstadoDeErro({ erro, aoTentarDeNovo }: { erro: unknown; aoTentarDeNovo?: () => void }) {
  const { t } = useI18n();
  return (
    <div className="estado-de-erro" role="alert">
      <h3>{t("app.erro_titulo")}</h3>
      <p>{mensagemDeErro(erro, t)}</p>
      {aoTentarDeNovo ? (
        <button type="button" onClick={aoTentarDeNovo}>
          {t("app.tentar_de_novo")}
        </button>
      ) : null}
    </div>
  );
}

export function EstadoVazio({
  titulo,
  texto,
  acao,
}: {
  titulo: string;
  texto: string;
  acao?: ReactNode;
}) {
  return (
    <div className="estado-vazio">
      <h3>{titulo}</h3>
      <p>{texto}</p>
      {acao}
    </div>
  );
}
