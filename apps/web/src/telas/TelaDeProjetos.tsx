/**
 * A lista de projetos — a porta de entrada da aplicação (RI-01 da spec 004).
 *
 * Siglas, uma vez: **ARA** — Árvore da Realidade Atual · **NC** — Nuvem de Conflito ·
 * **RI** — requisito de interface.
 *
 * A exclusão é **suave** e a confirmação **nomeia o projeto**: quem confirma "excluir?" sem
 * ver o nome confirma o projeto errado uma vez a cada tantas. O item vai para a lixeira,
 * que é uma vista separada (RI-02), e volta de lá.
 */
import { useCallback, useState } from "react";
import type { Cliente } from "../api/cliente";
import type { ProjetoResumo } from "../dominio/tipos";
import { Carregando, EstadoDeErro, EstadoVazio } from "../componentes/Estados";
import { mensagemDeErro } from "../componentes/mensagemDeErro";
import { useRecurso } from "../estado/useRecurso";
import { useI18n } from "../i18n";

export interface TelaDeProjetosProps {
  cliente: Cliente;
  aoAbrir(projeto: ProjetoResumo): void;
}

export function TelaDeProjetos({ cliente, aoAbrir }: TelaDeProjetosProps) {
  const { t, tc, idioma } = useI18n();
  const buscar = useCallback(() => cliente.projetos.listar(), [cliente]);
  const { dado, carregando, erro, recarregar } = useRecurso<ProjetoResumo[]>(buscar, [cliente]);
  const [nome, setNome] = useState("");
  const [problema, setProblema] = useState("");
  const [ferramenta, setFerramenta] = useState<"generico" | "ara" | "nc">("ara");
  const [excluindo, setExcluindo] = useState<ProjetoResumo | null>(null);
  const [erroDeAcao, setErroDeAcao] = useState<unknown>(null);
  const [ocupado, setOcupado] = useState(false);

  async function criar(evento: React.FormEvent) {
    evento.preventDefault();
    if (!nome.trim()) return;
    setOcupado(true);
    setErroDeAcao(null);
    try {
      if (ferramenta === "ara") await cliente.ara.criarProjeto(nome.trim(), problema.trim());
      else if (ferramenta === "nc") await cliente.nc.criarProjeto(nome.trim(), problema.trim());
      else await cliente.projetos.criar(nome.trim(), problema.trim());
      setNome("");
      setProblema("");
      await recarregar();
    } catch (falha) {
      setErroDeAcao(falha);
    } finally {
      setOcupado(false);
    }
  }

  async function confirmarExclusao() {
    if (!excluindo) return;
    const alvo = excluindo;
    setExcluindo(null);
    setOcupado(true);
    try {
      await cliente.projetos.excluir(alvo.id);
      await recarregar();
    } catch (falha) {
      setErroDeAcao(falha);
    } finally {
      setOcupado(false);
    }
  }

  return (
    <section className="tela tela-de-projetos">
      <div className="cabecalho-da-tela">
        <h1>{t("projetos.titulo")}</h1>
        <p>{t("projetos.descricao")}</p>
      </div>

      <form className="formulario-de-projeto" onSubmit={criar}>
        <label htmlFor="nome-do-projeto">{t("projetos.nome")}</label>
        <input
          id="nome-do-projeto"
          value={nome}
          placeholder={t("projetos.nome_placeholder")}
          onChange={(e) => setNome(e.target.value)}
        />
        <label htmlFor="problema-do-projeto">{t("projetos.problema")}</label>
        <input
          id="problema-do-projeto"
          value={problema}
          placeholder={t("projetos.problema_placeholder")}
          onChange={(e) => setProblema(e.target.value)}
        />
        <label htmlFor="ferramenta-do-projeto">{t("projetos.ferramenta")}</label>
        <select
          id="ferramenta-do-projeto"
          value={ferramenta}
          onChange={(e) => setFerramenta(e.target.value as "generico" | "ara" | "nc")}
        >
          <option value="ara">{t("ferramenta.ara")}</option>
          <option value="nc">{t("ferramenta.nc")}</option>
          <option value="generico">{t("ferramenta.generico")}</option>
        </select>
        <button type="submit" disabled={ocupado || !nome.trim()}>
          {ocupado ? t("projetos.criando") : t("projetos.criar")}
        </button>
      </form>

      {erroDeAcao ? (
        <p role="alert" className="erro">
          {mensagemDeErro(erroDeAcao, t)}
        </p>
      ) : null}

      {carregando ? <Carregando /> : null}
      {erro ? <EstadoDeErro erro={erro} aoTentarDeNovo={() => void recarregar()} /> : null}

      {!carregando && !erro && dado ? (
        dado.length === 0 ? (
          <EstadoVazio titulo={t("projetos.vazio_titulo")} texto={t("projetos.vazio_texto")} />
        ) : (
          <>
            <p className="contagem">{t("projetos.contagem", { n: dado.length })}</p>
            <table className="tabela">
              <thead>
                <tr>
                  <th scope="col">{t("projetos.nome")}</th>
                  <th scope="col">{t("projetos.ferramenta")}</th>
                  <th scope="col">{t("projetos.alterado_em")}</th>
                  <th scope="col">{t("projetos.acoes")}</th>
                </tr>
              </thead>
              <tbody>
                {dado.map((projeto) => (
                  <tr key={projeto.id}>
                    <th scope="row">{projeto.nome}</th>
                    <td>{tc("ferramenta", projeto.ferramenta, projeto.ferramenta)}</td>
                    <td>{new Date(projeto.alterado_em).toLocaleDateString(idioma)}</td>
                    <td className="acoes">
                      <button type="button" onClick={() => aoAbrir(projeto)}>
                        {t("projetos.abrir")}
                      </button>
                      <button type="button" className="perigo" onClick={() => setExcluindo(projeto)}>
                        {t("projetos.excluir")}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </>
        )
      ) : null}

      {excluindo ? (
        <div className="dialogo" role="dialog" aria-modal="true" aria-label={t("projetos.excluir")}>
          <p>{t("projetos.confirmar_exclusao", { nome: excluindo.nome })}</p>
          <div className="dialogo-acoes">
            <button type="button" onClick={() => setExcluindo(null)}>
              {t("app.cancelar")}
            </button>
            <button type="button" className="perigo" onClick={() => void confirmarExclusao()}>
              {t("app.confirmar")}
            </button>
          </div>
        </div>
      ) : null}
    </section>
  );
}
