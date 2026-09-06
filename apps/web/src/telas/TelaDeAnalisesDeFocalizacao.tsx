/**
 * A listagem das análises de focalização (RF-03, RI-07) — e o lugar onde uma nasce.
 *
 * Siglas, uma vez: **TOC** — Teoria das Restrições · **M1** — Núcleo de Diagramas Lógicos
 * · **RI/RF/RN** — requisito de interface / funcional / regra de negócio.
 *
 * **Por que uma listagem própria, e não uma linha a mais em `/toc/projetos`.** A RI-07 pede
 * "passo atual e restrição vigente como colunas de primeira classe", e essas duas colunas
 * não existem para nenhuma outra ferramenta: a ARA não tem passo, a Nuvem não tem
 * restrição vigente. Enfiá-las na tabela genérica encheria a listagem do M1 de células
 * vazias — e a alternativa (mostrar só quando a ferramenta é `focalizacao`) é uma tabela
 * que muda de forma por linha, que é pior.
 *
 * **Por que criar aqui e não pelo formulário genérico de projeto.** Uma análise de
 * focalização nasce com o primeiro ciclo aberto e os cinco passos instanciados (RF-02);
 * criar um `Projeto` cru com `ferramenta=focalizacao` produziria uma casca sem jornada. O
 * comando é próprio porque o ato é próprio.
 */
import { useCallback, useState } from "react";
import type { Cliente } from "../api/cliente";
import type { AnaliseResumo } from "../dominio/tipos";
import { Carregando, EstadoDeErro, EstadoVazio } from "../componentes/Estados";
import { mensagemDeErro } from "../componentes/mensagemDeErro";
import { useRecurso } from "../estado/useRecurso";
import { useI18n } from "../i18n";

export interface TelaDeAnalisesDeFocalizacaoProps {
  cliente: Cliente;
  aoAbrir(projetoId: string): void;
}

export function TelaDeAnalisesDeFocalizacao({
  cliente,
  aoAbrir,
}: TelaDeAnalisesDeFocalizacaoProps) {
  const { t } = useI18n();
  const buscar = useCallback(() => cliente.foco.listar(), [cliente]);
  const { dado, carregando, erro, recarregar } = useRecurso<AnaliseResumo[]>(buscar, [cliente]);

  const [nome, setNome] = useState("");
  const [sistema, setSistema] = useState("");
  const [descricao, setDescricao] = useState("");
  const [criando, setCriando] = useState(false);
  const [falha, setFalha] = useState<unknown>(null);

  if (carregando && !dado) return <Carregando />;
  if (erro && !dado) return <EstadoDeErro erro={erro} aoTentarDeNovo={() => void recarregar()} />;

  const analises = dado ?? [];

  async function criar(): Promise<void> {
    setCriando(true);
    setFalha(null);
    try {
      const criada = await cliente.foco.criarAnalise(nome.trim(), sistema.trim(), descricao.trim());
      setNome("");
      setSistema("");
      setDescricao("");
      await recarregar();
      aoAbrir(criada.projeto.id);
    } catch (problema) {
      setFalha(problema);
    } finally {
      setCriando(false);
    }
  }

  return (
    <section className="tela-de-focalizacao">
      <header>
        <h2>{t("foco.titulo")}</h2>
        <p>{t("foco.descricao")}</p>
      </header>

      {falha ? (
        <p className="estado-de-erro" role="alert">
          {mensagemDeErro(falha, t)}
        </p>
      ) : null}

      <form
        className="forma-de-analise"
        onSubmit={(evento) => {
          evento.preventDefault();
          if (!nome.trim() || !sistema.trim()) return;
          void criar();
        }}
      >
        <label htmlFor="analise-nome">{t("projetos.nome")}</label>
        <input
          id="analise-nome"
          value={nome}
          placeholder={t("foco.sistema_placeholder")}
          onChange={(evento) => setNome(evento.target.value)}
        />
        <label htmlFor="analise-sistema">{t("foco.sistema")}</label>
        <input
          id="analise-sistema"
          value={sistema}
          placeholder={t("foco.sistema_placeholder")}
          onChange={(evento) => setSistema(evento.target.value)}
        />
        <label htmlFor="analise-descricao">{t("projetos.problema")}</label>
        <textarea
          id="analise-descricao"
          rows={2}
          value={descricao}
          onChange={(evento) => setDescricao(evento.target.value)}
        />
        <button type="submit" disabled={criando || !nome.trim() || !sistema.trim()}>
          {criando ? t("foco.criando") : t("foco.criar")}
        </button>
      </form>

      {analises.length === 0 ? (
        <EstadoVazio titulo={t("foco.vazio_titulo")} texto={t("foco.vazio_texto")} />
      ) : (
        <table className="tabela-de-analises">
          <caption>{t("foco.titulo")}</caption>
          <thead>
            <tr>
              <th scope="col">{t("projetos.nome")}</th>
              <th scope="col">{t("foco.sistema")}</th>
              {/* As duas colunas de primeira classe da RI-07. */}
              <th scope="col">{t("foco.passo.identificar").split(" ")[0]}</th>
              <th scope="col">{t("foco.restricao.titulo")}</th>
              <th scope="col">{t("projetos.acoes")}</th>
            </tr>
          </thead>
          <tbody>
            {analises.map((analise) => (
              <tr key={analise.projeto_id}>
                <td>{analise.nome}</td>
                <td>{analise.sistema}</td>
                <td data-passo={analise.passo_atual}>
                  {t(`foco.passo_curto.${analise.passo_atual}`)}
                  <span className="ciclo-da-linha"> · {t("foco.ciclo", { n: analise.ciclo })}</span>
                </td>
                <td>
                  {analise.restricao ?? (
                    <span className="sem-restricao">{t("foco.restricao.ausente")}</span>
                  )}
                  {analise.herancas_pendentes > 0 ? (
                    <span className="pendencias-da-linha">
                      {t("foco.heranca.pendentes", { n: analise.herancas_pendentes })}
                    </span>
                  ) : null}
                </td>
                <td>
                  <button type="button" onClick={() => aoAbrir(analise.projeto_id)}>
                    {t("foco.abrir")}
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  );
}
