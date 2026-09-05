/**
 * A vista tabular da nuvem: aresta × premissas × injeções (RF-34 e RI-10 da spec 007).
 *
 * "Sessão de grupo flui na tabela, revisão flui no diagrama" — é o mesmo dado, e o mesmo
 * comando por trás de cada edição. A tabela não é resumo do diagrama: é a outra projeção
 * dele.
 */
import type { ChaveDaAresta, Matriz } from "../../dominio/tipos";
import { useI18n } from "../../i18n";

export function MatrizDaNuvem({
  matriz,
  aoAbrirAresta,
}: {
  matriz: Matriz;
  aoAbrirAresta(chave: ChaveDaAresta): void;
}) {
  const { t, tc } = useI18n();
  return (
    <table className="tabela matriz-da-nuvem">
      <thead>
        <tr>
          <th scope="col">{t("nuvem.leitura")}</th>
          <th scope="col">{t("nuvem.premissas")}</th>
          <th scope="col">{t("nuvem.injecoes")}</th>
          <th scope="col">{t("projetos.acoes")}</th>
        </tr>
      </thead>
      <tbody>
        {matriz.linhas.map((linha) => {
          const injecoes = linha.premissas.flatMap((premissa) => premissa.injecoes);
          return (
            <tr key={linha.chave}>
              <th scope="row">{linha.leitura}</th>
              <td>
                {linha.premissas.length === 0 ? (
                  t("nuvem.sem_premissas")
                ) : (
                  <ul>
                    {linha.premissas.map((premissa) => (
                      <li key={premissa.id}>
                        {premissa.texto}{" "}
                        <span className="estado">
                          ({tc("estado_da_premissa", premissa.estado, premissa.estado)})
                        </span>
                      </li>
                    ))}
                  </ul>
                )}
              </td>
              <td>
                {injecoes.length === 0 ? (
                  t("nuvem.sem_injecoes")
                ) : (
                  <ul>
                    {injecoes.map((injecao) => (
                      <li key={injecao.id}>{injecao.texto}</li>
                    ))}
                  </ul>
                )}
              </td>
              <td>
                <button type="button" onClick={() => aoAbrirAresta(linha.chave)}>
                  {t("nuvem.ficha_da_aresta")}
                </button>
              </td>
            </tr>
          );
        })}
      </tbody>
    </table>
  );
}
