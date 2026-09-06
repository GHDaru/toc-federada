/**
 * A pré-visualização de uma geração assistida — em diff, antes de qualquer escrita.
 *
 * Siglas, uma vez: **NC** — Nuvem de Conflito · **TRIZ** — Teoria da Resolução Inventiva
 * de Problemas · **IA** — inteligência artificial · **RF/RI** — requisito funcional / de
 * interface.
 *
 * **Nenhum botão daqui escreve na nuvem, e isso continua sendo o requisito** —
 * `POST …/geracoes` devolve a nuvem proposta validada contra o esquema versionado e o
 * `action_id` da ação governada, e a escrita é da proposta que atravessa a máquina de
 * estados no servidor (RF-21, RF-23, RF-25 da spec 007; ADR 0007).
 *
 * **O que mudou:** havia só "Recusar". A pessoa via o diff e não tinha como aceitá-lo — a
 * regra estava certa e a interface era um beco sem saída, com a funcionalidade mais
 * vistosa do produto sem conclusão. Agora "Aceitar" existe e faz o que a spec manda:
 * **leva a proposta ao gate governado** (`aoAceitar`), que a cria no servidor e a submete
 * à superfície de confirmação. Aceitar aqui não é aplicar; é pedir para decidir. Recusar
 * continua de graça, porque continua não havendo escrita para desfazer (RF-24).
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
  /**
   * Leva este resultado ao gate: cria a proposta de ação no servidor. **Opcional de
   * propósito** — quem não pode escrever não recebe a função, e a prévia continua honesta
   * mostrando só "Recusar" em vez de oferecer um caminho que o servidor recusaria (RF-27:
   * sem a capacidade de escrita, a ação mutadora nem existe no catálogo).
   */
  aoAceitar?(): void;
  /** Uma proposta já viajando: o botão para de aceitar clique. */
  ocupada?: boolean;
}

export function PreviaDaGeracao({
  geracao,
  textosAtuais,
  aoFechar,
  aoAceitar,
  ocupada = false,
}: PreviaDaGeracaoProps) {
  const { t, tc } = useI18n();
  const resultado = objeto(geracao.resultado);
  const entidades = objeto(resultado.entidades);
  const arestas = objeto(resultado.arestas);
  const temEntidades = PAPEIS.some((papel) => typeof entidades[papel] === "string");

  return (
    <section className="ficha previa-da-geracao" aria-label={t("nuvem.gerar_previa")}>
      <div className="ficha-cabecalho">
        <h2>{t("nuvem.gerar_previa")}</h2>
        {/* Aceitar e recusar, mesma classe e lado a lado: peso visual igual (RI-06). */}
        <div className="decisao">
          {aoAceitar ? (
            <button
              type="button"
              className="botao-de-decisao"
              disabled={ocupada}
              onClick={() => {
                if (!ocupada) aoAceitar();
              }}
            >
              {t("nuvem.aceitar")}
            </button>
          ) : null}
          <button type="button" className="botao-de-decisao" onClick={aoFechar}>
            {t("nuvem.recusar")}
          </button>
        </div>
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
