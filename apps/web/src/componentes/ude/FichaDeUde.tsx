/**
 * A ficha de validação de um Efeito Indesejável (UDE).
 *
 * Siglas, uma vez: **UDE** — Efeito Indesejável · **ARA** — Árvore da Realidade Atual ·
 * **RI/RF/RN** — requisito de interface / funcional / regra de negócio.
 *
 * **Uma superfície, quatro camadas**: o texto (com o trecho reprovado marcado), os
 * critérios decidíveis, os critérios de julgamento com os pareceres, e o status. O modal
 * monolítico da 4ª geração misturava as quatro num bloco de saída de modelo de linguagem;
 * a separação por classe de critério é o que torna a ficha ensinável — e é RI-02.
 *
 * **Nenhuma regra é decidida aqui.** `aoValidarTexto` chama `POST /toc/ara/validacoes`,
 * que é função pura do domínio do serviço. A ficha só apresenta o veredito e marca o
 * trecho que o servidor apontou.
 */
import { useState } from "react";
import type { Ude, ValidacaoFormal, VereditoDeCriterio } from "../../dominio/tipos";
import { useI18n } from "../../i18n";
import { mensagemDeErro } from "../mensagemDeErro";
import { TextoComTrecho } from "./TextoComTrecho";

export interface FichaDeUdeProps {
  ude: Ude;
  aoReformular(texto: string): Promise<void>;
  aoValidarTexto(texto: string): Promise<ValidacaoFormal>;
  aoRegistrarParecer(parecer: {
    favoravel: boolean;
    justificativa: string;
    criterios: string[];
  }): Promise<void>;
  aoMudarStatus(status: Ude["status"], justificativa: string): Promise<void>;
  aoFechar?(): void;
}

function separar(vereditos: readonly VereditoDeCriterio[]) {
  return {
    decidiveis: vereditos.filter((v) => v.classe === "decidivel"),
    julgamento: vereditos.filter((v) => v.classe === "julgamento"),
  };
}

export function FichaDeUde({
  ude,
  aoReformular,
  aoValidarTexto,
  aoRegistrarParecer,
  aoMudarStatus,
  aoFechar,
}: FichaDeUdeProps) {
  const { t, tc } = useI18n();
  const [texto, setTexto] = useState(ude.titulo);
  const [validacao, setValidacao] = useState<ValidacaoFormal>(ude.validacao);
  const [erro, setErro] = useState<string>("");
  const [ocupado, setOcupado] = useState(false);
  const [favoravel, setFavoravel] = useState(true);
  const [justificativa, setJustificativa] = useState("");

  const { decidiveis, julgamento } = separar(validacao.vereditos);
  const marcas = decidiveis
    .filter((v) => v.veredito === "nao_atende" && v.trecho)
    .map((v) => ({ trecho: v.trecho, codigo: v.codigo }));

  async function comTratamento(acao: () => Promise<void>) {
    setErro("");
    setOcupado(true);
    try {
      await acao();
    } catch (falha) {
      // A ficha NÃO fecha no erro (RI-04): fechar apagaria a edição em curso, que é
      // justamente o que a pessoa acabou de escrever.
      setErro(mensagemDeErro(falha, t));
    } finally {
      setOcupado(false);
    }
  }

  return (
    <section className="ficha" aria-label={t("ude.ficha")}>
      <div className="ficha-cabecalho">
        <h2>{t("ude.ficha")}</h2>
        <span className={`selo selo-${ude.status}`}>{tc("status", ude.status, ude.status)}</span>
        {aoFechar ? (
          <button type="button" onClick={aoFechar}>
            {t("app.fechar")}
          </button>
        ) : null}
      </div>

      <div className="ficha-texto">
        <TextoComTrecho texto={validacao.texto || ude.titulo} marcas={marcas} />
        <p className={validacao.aprovado_nos_decidiveis ? "veredito-bom" : "veredito-ruim"}>
          {validacao.aprovado_nos_decidiveis
            ? t("ude.aprovado")
            : t("ude.reprovado", { n: validacao.reprovacoes.length })}
        </p>
      </div>

      <div className="ficha-edicao">
        <label htmlFor="texto-do-ude">{t("ude.texto")}</label>
        <textarea
          id="texto-do-ude"
          value={texto}
          rows={3}
          onChange={(evento) => setTexto(evento.target.value)}
        />
        <p className="dica">{t("ude.reformular_dica")}</p>
        <div className="acoes">
          <button
            type="button"
            disabled={ocupado}
            onClick={() =>
              comTratamento(async () => {
                setValidacao(await aoValidarTexto(texto.trim()));
              })
            }
          >
            {t("ude.reavaliar")}
          </button>
          <button
            type="button"
            disabled={ocupado}
            onClick={() => comTratamento(() => aoReformular(texto.trim()))}
          >
            {t("ude.reformular")}
          </button>
        </div>
      </div>

      {erro ? (
        <p role="alert" className="erro">
          {erro}
        </p>
      ) : null}

      <section className="ficha-secao" aria-label={t("ude.decidiveis")}>
        <h3>{t("ude.decidiveis")}</h3>
        <p className="ajuda">{t("ude.decidiveis_ajuda")}</p>
        <ul className="criterios">
          {decidiveis.map((veredito) => (
            <li key={veredito.codigo} className={`criterio ${veredito.veredito}`}>
              <span className="criterio-codigo">{veredito.codigo}</span>
              <span className="criterio-enunciado">
                {tc("criterio", veredito.nome.replace(/^criterio\./, ""), veredito.enunciado)}
              </span>
              <span className="criterio-veredito">{tc("veredito", veredito.veredito, veredito.veredito)}</span>
              {veredito.motivo ? (
                <p className="criterio-motivo">
                  {t("ude.motivo")}: {veredito.motivo}
                </p>
              ) : null}
              {veredito.trecho ? (
                <p className="criterio-trecho">
                  {t("ude.trecho")}: <q>{veredito.trecho}</q>
                </p>
              ) : null}
            </li>
          ))}
        </ul>
      </section>

      <section className="ficha-secao" aria-label={t("ude.julgamento")}>
        <h3>{t("ude.julgamento")}</h3>
        <p className="ajuda">{t("ude.julgamento_ajuda")}</p>
        <ul className="criterios">
          {julgamento.map((veredito) => (
            <li key={veredito.codigo} className="criterio julgamento">
              <span className="criterio-codigo">{veredito.codigo}</span>
              <span className="criterio-enunciado">
                {tc("criterio", veredito.nome.replace(/^criterio\./, ""), veredito.enunciado)}
              </span>
            </li>
          ))}
        </ul>

        <h4>{t("ude.parecer_titulo")}</h4>
        {ude.pareceres.length === 0 ? (
          <p className="vazio">{t("ude.parecer_vazio")}</p>
        ) : (
          <ul className="pareceres">
            {ude.pareceres.map((parecer, indice) => (
              <li key={`${parecer.autor}-${indice}`}>
                <strong>{parecer.autor}</strong>{" "}
                <span>{parecer.favoravel ? t("ude.parecer_favoravel") : t("ude.parecer_contrario")}</span>
                <p>{parecer.justificativa}</p>
              </li>
            ))}
          </ul>
        )}

        <form
          className="formulario-de-parecer"
          onSubmit={(evento) => {
            evento.preventDefault();
            if (!justificativa.trim()) {
              // RF-13/RF-16: parecer sem justificativa é opinião sem rastro.
              setErro(t("app.obrigatorio"));
              return;
            }
            void comTratamento(async () => {
              await aoRegistrarParecer({
                favoravel,
                justificativa: justificativa.trim(),
                criterios: [],
              });
              setJustificativa("");
            });
          }}
        >
          <fieldset>
            <legend>{t("ude.parecer_registrar")}</legend>
            <label>
              <input
                type="radio"
                name="favoravel"
                checked={favoravel}
                onChange={() => setFavoravel(true)}
              />
              {t("ude.parecer_favoravel")}
            </label>
            <label>
              <input
                type="radio"
                name="favoravel"
                checked={!favoravel}
                onChange={() => setFavoravel(false)}
              />
              {t("ude.parecer_contrario")}
            </label>
          </fieldset>
          <label htmlFor="justificativa-do-parecer">{t("ude.parecer_justificativa")}</label>
          <textarea
            id="justificativa-do-parecer"
            value={justificativa}
            rows={2}
            onChange={(evento) => setJustificativa(evento.target.value)}
          />
          <button type="submit" disabled={ocupado}>
            {t("ude.parecer_registrar")}
          </button>
        </form>
      </section>

      <section className="ficha-secao" aria-label={t("ude.mudar_status")}>
        <h3>{t("ude.mudar_status")}</h3>
        <div className="acoes">
          {(["pendente", "requer_refinamento", "validado", "rejeitado"] as const).map((status) => (
            <button
              key={status}
              type="button"
              disabled={ocupado || status === ude.status}
              onClick={() => comTratamento(() => aoMudarStatus(status, justificativa.trim()))}
            >
              {tc("status", status, status)}
            </button>
          ))}
        </div>
      </section>
    </section>
  );
}
