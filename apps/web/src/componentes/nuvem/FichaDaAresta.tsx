/**
 * A ficha de uma aresta da Nuvem de Conflito (NC): leitura, premissas e injeções juntas.
 *
 * Siglas, uma vez: **NC** — Nuvem de Conflito · **TRIZ** — Teoria da Resolução Inventiva
 * de Problemas · **RN/RF/RI** — regra de negócio / requisito funcional / de interface.
 *
 * A injeção aparece **dentro** da premissa que ela invalida, e não numa lista à parte:
 * a RN-04 do domínio diz que não existe injeção sem premissa viva, e a tela que separa as
 * duas ensina o contrário do que a regra diz. Foi o que a 4ª geração fez, com um modal de
 * "premissa e solução" solto por aresta.
 *
 * **Sugestão não é escrita.** O que a assistência devolve entra numa bandeja de propostas,
 * com aceitar e recusar do mesmo peso visual (RI-06); recusar não custa nada porque nada
 * foi aplicado (RF-24). Quem escreve é a ação governada do catálogo `toc.*`, com gate
 * humano — nunca esta tela, e nunca um provedor de modelo chamado do navegador.
 */
import { useState } from "react";
import type {
  ArestaDaNuvem,
  Premissa,
  SeparacaoTRIZ,
  StatusDeInjecao,
  SugestaoDeInjecao,
  SugestaoDePremissa,
} from "../../dominio/tipos";
import { useI18n } from "../../i18n";
import { mensagemDeErro } from "../mensagemDeErro";

const SEPARACOES: readonly SeparacaoTRIZ[] = ["espaco", "tempo", "partes", "grau", "condicao"];
const STATUS: readonly StatusDeInjecao[] = ["candidata", "escolhida", "descartada"];

export interface FichaDaArestaProps {
  aresta: ArestaDaNuvem;
  aoRegistrarPremissa(texto: string): Promise<void>;
  aoEditarPremissa(premissaId: string, texto: string): Promise<void>;
  aoDesafiarPremissa(premissaId: string, justificativa: string): Promise<void>;
  aoRevigorarPremissa(premissaId: string): Promise<void>;
  /** Devolve QUANTAS injeções foram arquivadas junto (RF-15) — a tela diz o número. */
  aoArquivarPremissa(premissaId: string): Promise<number | void>;
  aoRegistrarInjecao(premissaId: string, texto: string, separacao: SeparacaoTRIZ | null): Promise<void>;
  aoClassificarInjecao(injecaoId: string, separacao: SeparacaoTRIZ | null): Promise<void>;
  aoMudarStatusDaInjecao(injecaoId: string, status: StatusDeInjecao, justificativa: string): Promise<void>;
  aoSugerirPremissas?(): Promise<SugestaoDePremissa[]>;
  aoSugerirInjecoes?(premissaId: string): Promise<SugestaoDeInjecao[]>;
  aoFechar?(): void;
}

export function FichaDaAresta(props: FichaDaArestaProps) {
  const { aresta } = props;
  const { t, tc } = useI18n();
  const [erro, setErro] = useState("");
  const [premissaNova, setPremissaNova] = useState("");
  const [desafiando, setDesafiando] = useState<string | null>(null);
  const [justificativa, setJustificativa] = useState("");
  const [propostas, setPropostas] = useState<SugestaoDePremissa[] | null>(null);
  const [arquivadas, setArquivadas] = useState<number | null>(null);
  const [ocupado, setOcupado] = useState(false);

  async function comTratamento(acao: () => Promise<void>) {
    setErro("");
    setOcupado(true);
    try {
      await acao();
    } catch (falha) {
      setErro(mensagemDeErro(falha, t));
    } finally {
      setOcupado(false);
    }
  }

  return (
    <section className="ficha ficha-da-aresta" aria-label={t("nuvem.ficha_da_aresta")}>
      <div className="ficha-cabecalho">
        <h2>{aresta.leitura}</h2>
        <span className={`selo classe-${aresta.classe}`}>{tc("classe", aresta.classe, aresta.classe)}</span>
        {props.aoFechar ? (
          <button type="button" onClick={props.aoFechar}>
            {t("app.fechar")}
          </button>
        ) : null}
      </div>

      {erro ? (
        <p role="alert" className="erro">
          {erro}
        </p>
      ) : null}

      {arquivadas !== null ? (
        <p role="status" className="aviso-de-proposta">
          {t("nuvem.arquivadas", { n: arquivadas })}
        </p>
      ) : null}

      <h3>{t("nuvem.premissas")}</h3>
      {aresta.premissas.length === 0 ? (
        <p className="vazio">{t("nuvem.sem_premissas")}</p>
      ) : (
        <ul className="premissas">
          {[...aresta.premissas]
            .sort((a, b) => a.ordem - b.ordem)
            .map((premissa) => (
              <ItemDePremissa
                key={premissa.id}
                premissa={premissa}
                ocupado={ocupado}
                aoDesafiar={() => {
                  setJustificativa("");
                  setDesafiando(premissa.id);
                }}
                aoRegistrarArquivamento={setArquivadas}
                {...props}
                comTratamento={comTratamento}
              />
            ))}
        </ul>
      )}

      <form
        className="linha-de-criacao"
        onSubmit={(evento) => {
          evento.preventDefault();
          const limpo = premissaNova.trim();
          if (!limpo) {
            setErro(t("app.obrigatorio"));
            return;
          }
          void comTratamento(async () => {
            await props.aoRegistrarPremissa(limpo);
            setPremissaNova("");
          });
        }}
      >
        <label htmlFor="premissa-nova">{t("nuvem.premissa_nova")}</label>
        <input
          id="premissa-nova"
          value={premissaNova}
          placeholder={t("nuvem.premissa_texto")}
          onChange={(e) => setPremissaNova(e.target.value)}
        />
        <button type="submit" disabled={ocupado}>
          {t("nuvem.premissa_nova")}
        </button>
      </form>

      {props.aoSugerirPremissas ? (
        <section className="bandeja" aria-label={t("nuvem.sugerir_premissas")}>
          <button
            type="button"
            disabled={ocupado}
            onClick={() =>
              comTratamento(async () => {
                setPropostas(await props.aoSugerirPremissas!());
              })
            }
          >
            {t("nuvem.sugerir_premissas")}
          </button>
          {propostas ? (
            <>
              <p className="aviso-de-proposta">{t("nuvem.nada_aplicado")}</p>
              <ul>
                {propostas.map((proposta, indice) => (
                  <li key={`${proposta.texto}-${indice}`} aria-label={`proposta ${indice + 1}`}>
                    <p>{proposta.texto}</p>
                    <div className="acoes iguais">
                      <button
                        type="button"
                        onClick={() =>
                          comTratamento(async () => {
                            await props.aoRegistrarPremissa(proposta.texto);
                            setPropostas((atuais) => (atuais ?? []).filter((_, i) => i !== indice));
                          })
                        }
                      >
                        {t("nuvem.aceitar")}
                      </button>
                      <button
                        type="button"
                        onClick={() =>
                          setPropostas((atuais) => (atuais ?? []).filter((_, i) => i !== indice))
                        }
                      >
                        {t("nuvem.recusar")}
                      </button>
                    </div>
                  </li>
                ))}
              </ul>
            </>
          ) : null}
        </section>
      ) : null}

      {desafiando ? (
        <div className="dialogo" role="dialog" aria-modal="true" aria-label={t("nuvem.desafiar")}>
          <label htmlFor="justificativa-do-desafio">{t("ude.justificativa")}</label>
          <textarea
            id="justificativa-do-desafio"
            rows={2}
            value={justificativa}
            onChange={(e) => setJustificativa(e.target.value)}
          />
          <div className="dialogo-acoes">
            <button type="button" onClick={() => setDesafiando(null)}>
              {t("app.cancelar")}
            </button>
            <button
              type="button"
              onClick={() => {
                const limpa = justificativa.trim();
                if (!limpa) {
                  // RF-13: desafiar sem justificativa é apagar a premissa sem dizer por quê.
                  setErro(t("app.obrigatorio"));
                  return;
                }
                const alvo = desafiando;
                setDesafiando(null);
                void comTratamento(() => props.aoDesafiarPremissa(alvo, limpa));
              }}
            >
              {t("app.confirmar")}
            </button>
          </div>
        </div>
      ) : null}
    </section>
  );
}

interface ItemProps extends FichaDaArestaProps {
  premissa: Premissa;
  ocupado: boolean;
  aoDesafiar(): void;
  aoRegistrarArquivamento(quantas: number): void;
  comTratamento(acao: () => Promise<void>): Promise<void>;
}

function ItemDePremissa({
  premissa,
  ocupado,
  aoDesafiar,
  aoRegistrarArquivamento,
  comTratamento,
  ...props
}: ItemProps) {
  const { t, tc } = useI18n();
  const [injecaoNova, setInjecaoNova] = useState("");
  const [separacao, setSeparacao] = useState<SeparacaoTRIZ | "">("");
  const [sugestoes, setSugestoes] = useState<SugestaoDeInjecao[] | null>(null);

  return (
    <li className={`premissa ${premissa.estado}`} aria-label={`premissa: ${premissa.texto}`}>
      <p className="premissa-texto">{premissa.texto}</p>
      <p className="premissa-estado">
        {tc("estado_da_premissa", premissa.estado, premissa.estado)}
        {premissa.justificativa ? <span className="justificativa"> — {premissa.justificativa}</span> : null}
      </p>

      <div className="acoes">
        {premissa.estado === "vigente" ? (
          <button type="button" disabled={ocupado} onClick={aoDesafiar}>
            {t("nuvem.desafiar")}
          </button>
        ) : (
          <button
            type="button"
            disabled={ocupado}
            onClick={() => comTratamento(() => props.aoRevigorarPremissa(premissa.id))}
          >
            {t("nuvem.revigorar")}
          </button>
        )}
        <button
          type="button"
          className="perigo"
          disabled={ocupado}
          onClick={() =>
            comTratamento(async () => {
              const quantas = await props.aoArquivarPremissa(premissa.id);
              if (typeof quantas === "number") aoRegistrarArquivamento(quantas);
            })
          }
        >
          {t("nuvem.arquivar")}
        </button>
      </div>

      <h4>{t("nuvem.injecoes")}</h4>
      {props.aoSugerirInjecoes ? (
        <div className="bandeja">
          <button
            type="button"
            disabled={ocupado}
            onClick={() =>
              comTratamento(async () => {
                setSugestoes(await props.aoSugerirInjecoes!(premissa.id));
              })
            }
          >
            {t("nuvem.sugerir_injecoes")}
          </button>
          {sugestoes ? (
            <>
              <p className="aviso-de-proposta">{t("nuvem.nada_aplicado")}</p>
              <ul>
                {sugestoes.map((sugestao, indice) => (
                  <li key={`${sugestao.texto}-${indice}`} aria-label={`proposta de injeção ${indice + 1}`}>
                    <p>{sugestao.texto}</p>
                    <div className="acoes iguais">
                      <button
                        type="button"
                        onClick={() =>
                          comTratamento(async () => {
                            await props.aoRegistrarInjecao(premissa.id, sugestao.texto, sugestao.separacao);
                            setSugestoes((atuais) => (atuais ?? []).filter((_, i) => i !== indice));
                          })
                        }
                      >
                        {t("nuvem.aceitar")}
                      </button>
                      <button
                        type="button"
                        onClick={() => setSugestoes((atuais) => (atuais ?? []).filter((_, i) => i !== indice))}
                      >
                        {t("nuvem.recusar")}
                      </button>
                    </div>
                  </li>
                ))}
              </ul>
            </>
          ) : null}
        </div>
      ) : null}
      {premissa.injecoes.length === 0 ? (
        <p className="vazio">{t("nuvem.sem_injecoes")}</p>
      ) : (
        <ul className="injecoes">
          {premissa.injecoes.map((injecao) => (
            <li key={injecao.id}>
              <p>{injecao.texto}</p>
              <p className="injecao-meta">
                {tc("separacao", injecao.separacao ?? "nenhuma", injecao.separacao ?? "")} ·{" "}
                {tc("status_da_injecao", injecao.status, injecao.status)}
              </p>
              <div className="acoes" role="group" aria-label={t("nuvem.status_da_injecao")}>
                {STATUS.filter((status) => status !== injecao.status).map((status) => (
                  <button
                    key={status}
                    type="button"
                    disabled={ocupado}
                    onClick={() =>
                      comTratamento(() => props.aoMudarStatusDaInjecao(injecao.id, status, ""))
                    }
                  >
                    {tc("status_da_injecao", status, status)}
                  </button>
                ))}
              </div>
            </li>
          ))}
        </ul>
      )}

      <form
        className="linha-de-criacao"
        onSubmit={(evento) => {
          evento.preventDefault();
          const limpo = injecaoNova.trim();
          if (!limpo) return;
          void comTratamento(async () => {
            await props.aoRegistrarInjecao(premissa.id, limpo, separacao || null);
            setInjecaoNova("");
            setSeparacao("");
          });
        }}
      >
        <label htmlFor={`injecao-${premissa.id}`}>{t("nuvem.injecao_nova")}</label>
        <input
          id={`injecao-${premissa.id}`}
          value={injecaoNova}
          placeholder={t("nuvem.injecao_texto")}
          onChange={(e) => setInjecaoNova(e.target.value)}
        />
        <label htmlFor={`separacao-${premissa.id}`}>{t("nuvem.separacao")}</label>
        <select
          id={`separacao-${premissa.id}`}
          value={separacao}
          onChange={(e) => setSeparacao(e.target.value as SeparacaoTRIZ | "")}
        >
          <option value="">{t("separacao.nenhuma")}</option>
          {SEPARACOES.map((valor) => (
            <option key={valor} value={valor}>
              {tc("separacao", valor, valor)}
            </option>
          ))}
        </select>
        <button type="submit" disabled={ocupado}>
          {t("nuvem.injecao_nova")}
        </button>
      </form>
    </li>
  );
}
