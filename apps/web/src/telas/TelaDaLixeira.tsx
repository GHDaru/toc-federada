/**
 * A lixeira — vista separada da lista, com data de exclusão e restauração (RI-02, spec 004).
 *
 * Não existe "excluir definitivamente" nesta versão, e a ausência é deliberada: o serviço
 * publica exclusão **suave** e restauração, e mais nada. Um botão que promete apagar de
 * vez e chama outra coisa é pior do que a ausência do botão.
 */
import { useCallback, useState } from "react";
import type { Cliente } from "../api/cliente";
import type { ProjetoResumo } from "../dominio/tipos";
import { Carregando, EstadoDeErro, EstadoVazio } from "../componentes/Estados";
import { mensagemDeErro } from "../componentes/mensagemDeErro";
import { useRecurso } from "../estado/useRecurso";
import { useI18n } from "../i18n";

export function TelaDaLixeira({ cliente }: { cliente: Cliente }) {
  const { t, idioma } = useI18n();
  const buscar = useCallback(() => cliente.projetos.lixeira(), [cliente]);
  const { dado, carregando, erro, recarregar } = useRecurso<ProjetoResumo[]>(buscar, [cliente]);
  const [erroDeAcao, setErroDeAcao] = useState<unknown>(null);

  async function restaurar(projeto: ProjetoResumo) {
    setErroDeAcao(null);
    try {
      await cliente.projetos.restaurar(projeto.id);
      await recarregar();
    } catch (falha) {
      setErroDeAcao(falha);
    }
  }

  return (
    <section className="tela tela-da-lixeira">
      <div className="cabecalho-da-tela">
        <h1>{t("lixeira.titulo")}</h1>
        <p>{t("lixeira.descricao")}</p>
      </div>

      {erroDeAcao ? (
        <p role="alert" className="erro">
          {mensagemDeErro(erroDeAcao, t)}
        </p>
      ) : null}

      {carregando ? <Carregando /> : null}
      {erro ? <EstadoDeErro erro={erro} aoTentarDeNovo={() => void recarregar()} /> : null}

      {!carregando && !erro && dado ? (
        dado.length === 0 ? (
          <EstadoVazio titulo={t("lixeira.vazio_titulo")} texto={t("lixeira.vazio_texto")} />
        ) : (
          <table className="tabela">
            <thead>
              <tr>
                <th scope="col">{t("projetos.nome")}</th>
                <th scope="col">{t("lixeira.excluido_em")}</th>
                <th scope="col">{t("projetos.acoes")}</th>
              </tr>
            </thead>
            <tbody>
              {dado.map((projeto) => (
                <tr key={projeto.id}>
                  <th scope="row">{projeto.nome}</th>
                  <td>
                    {projeto.excluido_em
                      ? new Date(projeto.excluido_em).toLocaleDateString(idioma)
                      : "—"}
                  </td>
                  <td className="acoes">
                    <button type="button" onClick={() => void restaurar(projeto)}>
                      {t("lixeira.restaurar")}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )
      ) : null}
    </section>
  );
}
