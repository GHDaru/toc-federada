/**
 * A pré-visualização de uma geração assistida — em diff, antes de qualquer escrita.
 *
 * Siglas, uma vez: **NC** — Nuvem de Conflito · **TRIZ** — Teoria da Resolução Inventiva
 * de Problemas · **IA** — inteligência artificial · **RF/RI** — requisito funcional / de
 * interface.
 *
 * **Não existe botão que aplique aqui, e a ausência é o requisito.** `POST …/geracoes`
 * devolve a nuvem proposta validada contra o esquema versionado e o `action_id` da ação
 * governada; a escrita é da proposta que atravessa a máquina de estados no servidor, com
 * gate humano (RF-21, RF-23, RF-24 da spec 007; ADR 0007). Recusar, por isso, é de graça:
 * nada foi tocado.
 *
 * O componente também não confia no formato: o resultado chega como objeto aberto e é
 * lido com verificação campo a campo. Um resultado estranho vira tela vazia com o aviso,
 * nunca uma exceção que derruba a nuvem que o grupo estava usando.
 */
import type { ChaveDaAresta, Geracao, PapelDaEntidade } from "../../dominio/tipos";
import { useI18n } from "../../i18n";

const PAPEIS: readonly PapelDaEntidade[] = ["A", "B", "C", "D", "D_PRIME"];
const CHAVES: readonly ChaveDaAresta[] = [
  "A_B",
  "A_C",
  "B_D",
  "C_D_PRIME",
  "D_C",
  "D_PRIME_B",
  "D_D_PRIME",
];

interface PremissaProposta {
  texto: string;
  injecoes: { texto: string; separacao?: string }[];
}

function objeto(valor: unknown): Record<string, unknown> {
  return valor && typeof valor === "object" && !Array.isArray(valor)
    ? (valor as Record<string, unknown>)
    : {};
}

function premissasDe(bruto: unknown): PremissaProposta[] {
  if (!Array.isArray(bruto)) return [];
  return bruto.map((item) => {
    const premissa = objeto(item);
    const injecoes = Array.isArray(premissa.injecoes) ? premissa.injecoes : [];
    return {
      texto: String(premissa.texto ?? ""),
      injecoes: injecoes.map((injecao) => {
        const dados = objeto(injecao);
        return {
          texto: String(dados.texto ?? ""),
          ...(typeof dados.separacao === "string" ? { separacao: dados.separacao } : {}),
        };
      }),
    };
  });
}

export interface PreviaDaGeracaoProps {
  geracao: Geracao;
  /** O texto que a nuvem tem HOJE, por papel — é o outro lado do diff. */
  textosAtuais: Partial<Record<PapelDaEntidade, string>>;
  aoFechar(): void;
}

export function PreviaDaGeracao({ geracao, textosAtuais, aoFechar }: PreviaDaGeracaoProps) {
  const { t, tc } = useI18n();
  const resultado = objeto(geracao.resultado);
  const entidades = objeto(resultado.entidades);
  const arestas = objeto(resultado.arestas);
  const temEntidades = PAPEIS.some((papel) => typeof entidades[papel] === "string");

  return (
    <section className="ficha previa-da-geracao" aria-label={t("nuvem.gerar_previa")}>
      <div className="ficha-cabecalho">
        <h2>{t("nuvem.gerar_previa")}</h2>
        <button type="button" onClick={aoFechar}>
          {t("nuvem.recusar")}
        </button>
      </div>

      <p className="aviso-de-proposta">{t("nuvem.nada_aplicado")}</p>
      <p className="acao-governada">
        <code>{geracao.action_id}</code>
      </p>

      {typeof resultado.racional === "string" && resultado.racional ? (
        <p className="racional">
          {t("nuvem.racional")}: {resultado.racional}
        </p>
      ) : null}

      {temEntidades ? (
        <table className="tabela">
          <thead>
            <tr>
              <th scope="col">{t("nuvem.coluna_papel")}</th>
              <th scope="col">{t("nuvem.coluna_hoje")}</th>
              <th scope="col">{t("nuvem.coluna_proposto")}</th>
            </tr>
          </thead>
          <tbody>
            {PAPEIS.map((papel) => (
              <tr key={papel}>
                <th scope="row">{tc("papel", papel, papel)}</th>
                <td className="antes">{textosAtuais[papel] || "—"}</td>
                <td className="depois">{String(entidades[papel] ?? "—")}</td>
              </tr>
            ))}
          </tbody>
        </table>
      ) : null}

      {CHAVES.map((chave) => {
        const premissas = premissasDe(arestas[chave]);
        if (!premissas.length) return null;
        return (
          <div key={chave} className="previa-da-aresta">
            <h3>{chave}</h3>
            <ul>
              {premissas.map((premissa, indice) => (
                <li key={`${chave}-${indice}`}>
                  <p>{premissa.texto}</p>
                  {premissa.injecoes.length ? (
                    <ul>
                      {premissa.injecoes.map((injecao, posicao) => (
                        <li key={`${chave}-${indice}-${posicao}`}>
                          {injecao.texto}
                          {injecao.separacao ? (
                            <span className="injecao-meta">
                              {" "}
                              · {tc("separacao", injecao.separacao, injecao.separacao)}
                            </span>
                          ) : null}
                        </li>
                      ))}
                    </ul>
                  ) : null}
                </li>
              ))}
            </ul>
          </div>
        );
      })}
    </section>
  );
}
