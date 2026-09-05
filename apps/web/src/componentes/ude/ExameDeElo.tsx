/**
 * O exame de suficiência de um elo (RF-22 e RI-05 da spec 005).
 *
 * Siglas, uma vez: **ARA** — Árvore da Realidade Atual · **RI/RF** — requisito de
 * interface / funcional.
 *
 * Os quatro estados têm representação **textual** distinta, e dois deles — `insuficiente` e
 * `com_reserva` — exigem a reserva escrita. Quem cobra de verdade é o domínio do serviço;
 * a tela cobra antes só para não gastar uma ida à rede e para dizer o porquê no lugar
 * onde a pessoa está escrevendo.
 */
import { useState } from "react";
import type { EstadoDoExame } from "../../dominio/tipos";
import { useI18n } from "../../i18n";

const ESTADOS: readonly EstadoDoExame[] = [
  "nao_examinado",
  "suficiente",
  "insuficiente",
  "com_reserva",
];

const EXIGEM_RESERVA: readonly EstadoDoExame[] = ["insuficiente", "com_reserva"];

export interface ExameDeEloProps {
  leitura: string;
  estadoAtual: EstadoDoExame;
  reservaAtual: string;
  aoRegistrar(estado: EstadoDoExame, reserva: string): Promise<void>;
  aoFechar(): void;
}

export function ExameDeElo({ leitura, estadoAtual, reservaAtual, aoRegistrar, aoFechar }: ExameDeEloProps) {
  const { t, tc } = useI18n();
  const [estado, setEstado] = useState<EstadoDoExame>(estadoAtual);
  const [reserva, setReserva] = useState(reservaAtual);
  const [erro, setErro] = useState("");

  return (
    <section className="ficha ficha-do-exame" aria-label={t("exame.titulo")}>
      <div className="ficha-cabecalho">
        <h2>{t("exame.titulo")}</h2>
        <button type="button" onClick={aoFechar}>
          {t("app.fechar")}
        </button>
      </div>
      <p className="leitura">
        <span className="rotulo">{t("exame.leitura")}: </span>
        {leitura}
      </p>

      <label htmlFor="estado-do-exame">{t("exame.estado")}</label>
      <select
        id="estado-do-exame"
        value={estado}
        onChange={(e) => setEstado(e.target.value as EstadoDoExame)}
      >
        {ESTADOS.map((valor) => (
          <option key={valor} value={valor}>
            {tc("estado_do_exame", valor, valor)}
          </option>
        ))}
      </select>

      <label htmlFor="reserva-do-exame">{t("exame.reserva")}</label>
      <textarea
        id="reserva-do-exame"
        rows={2}
        value={reserva}
        onChange={(e) => setReserva(e.target.value)}
      />

      {erro ? (
        <p role="alert" className="erro">
          {erro}
        </p>
      ) : null}

      <button
        type="button"
        onClick={() => {
          if (EXIGEM_RESERVA.includes(estado) && !reserva.trim()) {
            setErro(t("exame.reserva_obrigatoria"));
            return;
          }
          setErro("");
          void aoRegistrar(estado, reserva.trim()).catch(() => {
            /* o erro sobe para a tela, que já o desenha */
          });
        }}
      >
        {t("exame.salvar")}
      </button>
    </section>
  );
}
