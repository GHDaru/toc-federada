/**
 * A Árvore de Pré-Requisitos (APR) — obstáculos, objetivos intermediários e a ORDEM.
 *
 * Siglas, uma vez: **APR** — Árvore de Pré-Requisitos · **ARF** — Árvore da Realidade
 * Futura · **AT** — Árvore de Transição · **OI** — Objetivo Intermediário · **API** —
 * interface de programação de aplicações · **RI/RF/RN** — requisito de interface /
 * funcional / regra de negócio.
 *
 * A APR é uma ferramenta de **condição necessária**: "A precisa existir antes de B". Ela
 * não é uma árvore de suficiência com outro nome, e por isso esta tela **não tem exame de
 * elo** — a rota não existe no servidor (RN-05: as duas lógicas não se misturam no mesmo
 * projeto), e a garantia é a ausência da operação, não um `if` na interface.
 *
 * O sequenciamento é o primeiro bloco depois do objetivo, e isso é decisão: a ordem é a
 * informação principal desta ferramenta. Ver `componentes/apr/SequenciaDaApr.tsx`.
 */
import { useCallback, useState } from "react";
import type { Cliente } from "../api/cliente";
import type { Apr, No, PapelNaApr, Posicao, ResumoDaApr } from "../dominio/tipos";
import { Canvas } from "../componentes/canvas/Canvas";
import { Carregando, EstadoDeErro } from "../componentes/Estados";
import { mensagemDeErro } from "../componentes/mensagemDeErro";
import { ParesDaApr } from "../componentes/apr/ParesDaApr";
import { SequenciaDaApr } from "../componentes/apr/SequenciaDaApr";
import { useRecurso } from "../estado/useRecurso";
import { useI18n } from "../i18n";

/** O objetivo NÃO entra aqui: ele nasce com a árvore e não se cria um segundo (RF-14). */
const PAPEIS: readonly PapelNaApr[] = ["obstaculo", "objetivo_intermediario"];

export interface TelaDaAprProps {
  cliente: Cliente;
  projetoId: string;
  aoVoltar(): void;
  /** RF-42: a travessia se abre de DENTRO da ferramenta — ela é de uma análise. */
  aoAbrirCadeia?(projetoId: string): void;
}

interface Conteudo {
  apr: Apr;
  resumo: ResumoDaApr;
}

export function TelaDaApr({ cliente, projetoId, aoVoltar, aoAbrirCadeia }: TelaDaAprProps) {
  const { t, tc } = useI18n();
  const buscar = useCallback(async (): Promise<Conteudo> => {
    // Duas leituras, uma tela — e as duas são projeções do MESMO agregado no servidor.
    const [apr, resumo] = await Promise.all([
      cliente.apr.abrir(projetoId),
      cliente.apr.resumo(projetoId),
    ]);
    return { apr, resumo };
  }, [cliente, projetoId]);
  const { dado, carregando, erro, recarregar } = useRecurso<Conteudo>(buscar, [cliente, projetoId]);

  const [selecionado, setSelecionado] = useState<string | null>(null);
  const [papelNovo, setPapelNovo] = useState<PapelNaApr>("obstaculo");
  const [textoNovo, setTextoNovo] = useState("");
  const [parObstaculo, setParObstaculo] = useState("");
  const [parObjetivo, setParObjetivo] = useState("");
  const [erroDeAcao, setErroDeAcao] = useState<unknown>(null);
  const [ocupado, setOcupado] = useState(false);

  const escrever = useCallback(
    async (acao: () => Promise<unknown>) => {
      setErroDeAcao(null);
      setOcupado(true);
      try {
        await acao();
        await recarregar();
      } catch (falha) {
        setErroDeAcao(falha);
      } finally {
        setOcupado(false);
      }
    },
    [recarregar],
  );

  if (carregando && !dado) return <Carregando />;
  if (erro && !dado) return <EstadoDeErro erro={erro} aoTentarDeNovo={() => void recarregar()} />;
  if (!dado) return null;

  const { apr, resumo } = dado;
  const obstaculos = apr.nos.filter((no) => no.papel === "obstaculo");
  const objetivos = apr.nos.filter((no) => no.papel === "objetivo_intermediario");

  const nosDoCanvas: No[] = apr.nos.map((no) => ({
    id: no.id,
    titulo: no.titulo,
    descricao: no.descricao,
    tipo: no.papel,
    posicao: no.posicao,
    recolhido: no.recolhido,
  }));
  const arestasDoCanvas = apr.dependencias.map((d) => ({
    id: d.id,
    origem_id: d.antes_id,
    destino_id: d.depois_id,
    rotulo: "",
  }));

  return (
    <section className="tela tela-da-apr" aria-label={t("apr.titulo")}>
      <div className="cabecalho-do-projeto">
        <button type="button" onClick={aoVoltar}>
          {t("app.voltar")}
        </button>
        <h1>{apr.nome}</h1>
        {aoAbrirCadeia ? (
          <button type="button" onClick={() => aoAbrirCadeia(apr.id)}>
            {t("navegacao.cadeia")}
          </button>
        ) : null}
        {apr.origem ? (
          <p className="origem">
            {t("apr.origem")} {tc("ferramenta", apr.origem.ferramenta)}
          </p>
        ) : null}
      </div>

      {erroDeAcao ? (
        <p role="alert" className="erro">
          {mensagemDeErro(erroDeAcao, t)}
        </p>
      ) : null}

      {/* O topo da árvore. Ele NÃO é mais um nó da lista: sem objetivo, obstáculo nenhum
          tem sentido — e o domínio recusa excluí-lo (RF-14). */}
      <section className="objetivo-da-apr" role="region" aria-label={t("apr.objetivo")}>
        <h3>{t("apr.objetivo")}</h3>
        <p className="texto-do-objetivo">{apr.objetivo.titulo}</p>
        <p className="explicacao">{t("apr.objetivo_explicacao")}</p>
      </section>

      <form
        className="linha-de-criacao"
        onSubmit={(evento) => {
          evento.preventDefault();
          const titulo = textoNovo.trim();
          if (!titulo) return;
          void escrever(async () => {
            await cliente.apr.adicionarNo(projetoId, { papel: papelNovo, titulo });
            setTextoNovo("");
          });
        }}
      >
        <label htmlFor="papel-do-no-novo">{t("apr.papel")}</label>
        <select
          id="papel-do-no-novo"
          value={papelNovo}
          onChange={(evento) => setPapelNovo(evento.target.value as PapelNaApr)}
        >
          {PAPEIS.map((papel) => (
            <option key={papel} value={papel}>
              {tc("papel_na_apr", papel)}
            </option>
          ))}
        </select>
        <label htmlFor="texto-do-no-novo">{t("apr.texto_do_no")}</label>
        <input
          id="texto-do-no-novo"
          value={textoNovo}
          onChange={(evento) => setTextoNovo(evento.target.value)}
        />
        <button type="submit" disabled={ocupado || !textoNovo.trim()}>
          {t("apr.adicionar")}
        </button>
      </form>

      {/* Parear é o gesto que transforma queixa em plano: o obstáculo ganha o objetivo
          intermediário que o supera, e o teste de validade nasce com o par. */}
      <form
        className="linha-de-pareamento"
        onSubmit={(evento) => {
          evento.preventDefault();
          if (!parObstaculo || !parObjetivo) return;
          void escrever(async () => {
            await cliente.apr.parear(projetoId, parObstaculo, parObjetivo);
            setParObstaculo("");
            setParObjetivo("");
          });
        }}
      >
        <label htmlFor="par-obstaculo">{t("apr.obstaculo")}</label>
        <select
          id="par-obstaculo"
          value={parObstaculo}
          onChange={(evento) => setParObstaculo(evento.target.value)}
        >
          <option value="">—</option>
          {obstaculos.map((no) => (
            <option key={no.id} value={no.id}>
              {no.titulo}
            </option>
          ))}
        </select>
        <label htmlFor="par-objetivo">{t("apr.objetivo_intermediario")}</label>
        <select
          id="par-objetivo"
          value={parObjetivo}
          onChange={(evento) => setParObjetivo(evento.target.value)}
        >
          <option value="">—</option>
          {objetivos.map((no) => (
            <option key={no.id} value={no.id}>
              {no.titulo}
            </option>
          ))}
        </select>
        <button type="submit" disabled={ocupado || !parObstaculo || !parObjetivo}>
          {t("apr.parear")}
        </button>
      </form>

      <div className="area-de-trabalho">
        <Canvas
          nos={nosDoCanvas}
          arestas={arestasDoCanvas}
          selecionado={selecionado}
          aoSelecionar={setSelecionado}
          aoCriarNo={(posicao: Posicao) =>
            void escrever(() =>
              cliente.apr.adicionarNo(projetoId, {
                papel: "obstaculo",
                titulo: t("canvas.novo_no_titulo"),
                posicao,
              }),
            )
          }
          aoMoverNo={(id, posicao) => void escrever(() => cliente.apr.moverNo(projetoId, id, posicao))}
          aoEditarTitulo={(id, titulo) =>
            void escrever(() => cliente.apr.editarNo(projetoId, id, { titulo }))
          }
          aoExcluirNo={(id) => void escrever(() => cliente.apr.excluirNo(projetoId, id))}
          // A aresta da APR é NECESSIDADE: "antes → depois". A direção do gesto é a mesma
          // do canvas causal, e a leitura é outra — quem a monta é o servidor.
          aoLigar={(antes, depois) => void escrever(() => cliente.apr.depender(projetoId, antes, depois))}
          aoAbrirDetalhe={(id) => setSelecionado(id)}
          selo={(no) => (
            <span className="selo-da-apr" data-papel={no.tipo}>
              {tc("papel_na_apr", no.tipo)}
            </span>
          )}
        />

        <div className="painel-da-apr">
          <SequenciaDaApr
            sequenciamento={apr.sequenciamento}
            nos={apr.nos}
            pares={apr.pares}
            dependencias={apr.dependencias}
          />

          <ParesDaApr
            pares={apr.pares}
            nos={apr.nos}
            ocupado={ocupado}
            aoJulgar={(parId, valido, justificativa) =>
              // O AUTOR não vai no corpo: é o principal do servidor (RN-07).
              void escrever(() => cliente.apr.julgar(projetoId, parId, valido, justificativa))
            }
            aoDesfazerPar={(parId) => void escrever(() => cliente.apr.desfazerPar(projetoId, parId))}
          />

          <section className="resumo-da-apr">
            <h3>{t("apr.resumo")}</h3>
            <p className="explicacao">{t("apr.resumo_explicacao")}</p>
            <table aria-label={t("apr.resumo")}>
              <thead>
                <tr>
                  <th scope="col">{t("apr.camada", { n: "" }).trim()}</th>
                  <th scope="col">{t("apr.obstaculo")}</th>
                  <th scope="col">{t("apr.objetivo_intermediario")}</th>
                  <th scope="col">{t("apr.depende_de")}</th>
                  <th scope="col">{t("apr.teste_de_validade")}</th>
                </tr>
              </thead>
              <tbody>
                {resumo.linhas.map((linha, indice) => (
                  <tr key={`${linha.objetivo_intermediario_id ?? linha.obstaculo_id ?? indice}`}>
                    <td>{linha.camada === null ? "—" : linha.camada + 1}</td>
                    <td>{linha.obstaculo ?? t("apr.sem_obstaculo")}</td>
                    <td>{linha.objetivo_intermediario ?? t("apr.sem_par")}</td>
                    <td>{linha.depende_de.join(" · ") || "—"}</td>
                    <td>{linha.julgamento || "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </section>
        </div>
      </div>
    </section>
  );
}
