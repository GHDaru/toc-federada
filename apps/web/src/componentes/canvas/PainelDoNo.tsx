/**
 * O painel lateral de um nó — título, descrição e posição.
 *
 * Siglas, uma vez: **RI** — requisito de interface · **UDE** — Efeito Indesejável.
 *
 * RI-04 da spec 004: "a edição de título é inline no canvas; **descrição e campos longos
 * abrem em painel lateral, não em modal bloqueante**". A diferença não é estética: o modal
 * esconde o diagrama justamente enquanto se escreve sobre ele, e obriga a fechar para
 * conferir. Por isso este componente é um `aside`, sem `aria-modal` e sem armadilha de
 * foco — e há teste que reprova se ele virar diálogo.
 */
import { useState } from "react";
import type { No } from "../../dominio/tipos";
import { useI18n } from "../../i18n";
import { mensagemDeErro } from "../mensagemDeErro";

export interface PainelDoNoProps {
  no: No;
  aoSalvar(dados: { titulo: string; descricao: string }): Promise<void>;
  aoFechar(): void;
}

export function PainelDoNo({ no, aoSalvar, aoFechar }: PainelDoNoProps) {
  const { t } = useI18n();
  const [titulo, setTitulo] = useState(no.titulo);
  const [descricao, setDescricao] = useState(no.descricao);
  const [erro, setErro] = useState("");
  const [ocupado, setOcupado] = useState(false);

  return (
    <aside className="painel-do-no" aria-label={t("canvas.detalhe")}>
      <div className="ficha-cabecalho">
        <h2>{t("canvas.detalhe")}</h2>
        <button type="button" onClick={aoFechar}>
          {t("app.fechar")}
        </button>
      </div>

      <label htmlFor="titulo-do-no">{t("painel.coluna_titulo")}</label>
      <input id="titulo-do-no" value={titulo} onChange={(e) => setTitulo(e.target.value)} />

      <label htmlFor="descricao-do-no">{t("canvas.descricao")}</label>
      <textarea
        id="descricao-do-no"
        rows={4}
        value={descricao}
        onChange={(e) => setDescricao(e.target.value)}
      />

      <p className="posicao">
        {t("canvas.posicao")}: {Math.round(no.posicao.x)}, {Math.round(no.posicao.y)}
      </p>

      {erro ? (
        <p role="alert" className="erro">
          {erro}
        </p>
      ) : null}

      <button
        type="button"
        disabled={ocupado}
        onClick={async () => {
          setErro("");
          setOcupado(true);
          try {
            await aoSalvar({ titulo: titulo.trim(), descricao: descricao.trim() });
          } catch (falha) {
            setErro(mensagemDeErro(falha, t));
          } finally {
            setOcupado(false);
          }
        }}
      >
        {t("app.salvar")}
      </button>
    </aside>
  );
}
