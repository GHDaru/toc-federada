/**
 * A Nuvem de Conflito (NC) — cinco entidades, sete arestas, premissas, injeções, e a
 * visão conflito+solução que nenhuma geração da linhagem chegou a entregar inteira.
 *
 * Siglas, uma vez: **NC** — Nuvem de Conflito · **ARA** — Árvore da Realidade Atual ·
 * **TRIZ** — Teoria da Resolução Inventiva de Problemas · **RI/RF/RN** — requisito de
 * interface / funcional / regra de negócio.
 *
 * A escolha de visão (conflito, solução, lado a lado, tabela) **persiste na sessão**
 * (RI-08): quem está conduzindo um grupo não quer reescolher a visão a cada recarga.
 * Ela vive no `sessionStorage`, com leitura e escrita embrulhadas — armazenamento
 * indisponível volta ao padrão em vez de derrubar a tela.
 */
import { useCallback, useState } from "react";
import type { Cliente } from "../api/cliente";
import type {
  ChaveDaAresta,
  Geracao,
  Matriz,
  Nuvem,
  PapelDaEntidade,
  SeparacaoTRIZ,
  Solucao,
  StatusDeInjecao,
  ValidacaoDaNuvem,
} from "../dominio/tipos";
import { Carregando, EstadoDeErro } from "../componentes/Estados";
import { mensagemDeErro } from "../componentes/mensagemDeErro";
import { DiagramaDaNuvem } from "../componentes/nuvem/DiagramaDaNuvem";
import { FichaDaAresta } from "../componentes/nuvem/FichaDaAresta";
import { MatrizDaNuvem } from "../componentes/nuvem/MatrizDaNuvem";
import { PreviaDaGeracao } from "../componentes/nuvem/PreviaDaGeracao";
import { VisaoDeSolucao } from "../componentes/nuvem/VisaoDeSolucao";
import { useRecurso } from "../estado/useRecurso";
import { useI18n } from "../i18n";

export const CHAVE_DA_VISAO = "toc.nuvem.visao";

type Visao = "conflito" | "solucao" | "lado_a_lado" | "tabela";

function lerVisao(): Visao {
  try {
    const guardada = window.sessionStorage.getItem(CHAVE_DA_VISAO);
    if (guardada === "conflito" || guardada === "solucao" || guardada === "lado_a_lado" || guardada === "tabela") {
      return guardada;
    }
  } catch {
    /* sem armazenamento: o padrão serve */
  }
  return "conflito";
}

export interface TelaDaNuvemProps {
  cliente: Cliente;
  projetoId: string;
  aoVoltar(): void;
}

interface Conteudo {
  nuvem: Nuvem;
  validacao: ValidacaoDaNuvem;
  solucao: Solucao;
  matriz: Matriz;
}

export function TelaDaNuvem({ cliente, projetoId, aoVoltar }: TelaDaNuvemProps) {
  const { t } = useI18n();
  const buscar = useCallback(async (): Promise<Conteudo> => {
    // Quatro leituras, uma tela: a nuvem, a completude, o espelho da solução e a matriz.
    // Todas são projeções do MESMO agregado no servidor — nenhuma é calculada aqui.
    const [nuvem, validacao, solucao, matriz] = await Promise.all([
      cliente.nc.abrir(projetoId),
      cliente.nc.validacao(projetoId),
      cliente.nc.solucao(projetoId),
      cliente.nc.matriz(projetoId),
    ]);
    return { nuvem, validacao, solucao, matriz };
  }, [cliente, projetoId]);

  const { dado, carregando, erro, recarregar } = useRecurso<Conteudo>(buscar, [cliente, projetoId]);
  const [visao, setVisao] = useState<Visao>(() => lerVisao());
  const [arestaAberta, setArestaAberta] = useState<ChaveDaAresta | null>(null);
  const [erroDeAcao, setErroDeAcao] = useState<unknown>(null);
  const [narrativa, setNarrativa] = useState("");
  const [previa, setPrevia] = useState<Geracao | null>(null);

  function escolherVisao(nova: Visao) {
    setVisao(nova);
    try {
      window.sessionStorage.setItem(CHAVE_DA_VISAO, nova);
    } catch {
      /* idem */
    }
  }

  const escrever = useCallback(
    async (acao: () => Promise<void>) => {
      setErroDeAcao(null);
      try {
        await acao();
        await recarregar();
      } catch (falha) {
        setErroDeAcao(falha);
        throw falha;
      }
    },
    [recarregar],
  );

  if (carregando && !dado) return <Carregando />;
  if (erro && !dado) return <EstadoDeErro erro={erro} aoTentarDeNovo={() => void recarregar()} />;
  if (!dado) return null;

  const { nuvem, validacao, solucao, matriz } = dado;
  const aresta = arestaAberta ? nuvem.arestas.find((a) => a.chave === arestaAberta) : undefined;
  const pendentes = validacao.arestas_sem_premissa;

  const diagrama = (
    <DiagramaDaNuvem
      nuvem={nuvem}
      arestaAberta={arestaAberta}
      titulo={t("nuvem.conflito")}
      aoAbrirAresta={setArestaAberta}
      aoEditarEntidade={(papel: PapelDaEntidade, texto: string) =>
        escrever(async () => {
          await cliente.nc.editarEntidade(projetoId, papel, texto);
        }).catch(() => undefined)
      }
    />
  );

  return (
    <section className="tela tela-da-nuvem" aria-label={t("navegacao.nuvem")}>
      <div className="cabecalho-do-projeto">
        <button type="button" onClick={aoVoltar}>
          {t("app.voltar")}
        </button>
        <h1>{nuvem.nome}</h1>

        {/* RI-09: a completude no cabeçalho, com salto direto para as pendentes. */}
        <p className="completude">
          {t("nuvem.completude", {
            n: validacao.completude.sustentadas,
            total: validacao.completude.total,
          })}
        </p>
        <button
          type="button"
          disabled={pendentes.length === 0}
          onClick={() => setArestaAberta(pendentes[0] ?? null)}
        >
          {t("nuvem.pendentes")} ({pendentes.length})
        </button>

        <div className="seletor-de-visao" role="radiogroup" aria-label={t("nuvem.visao")}>
          {(["conflito", "solucao", "lado_a_lado", "tabela"] as const).map((valor) => (
            <button
              key={valor}
              type="button"
              role="radio"
              aria-checked={visao === valor}
              onClick={() => escolherVisao(valor)}
            >
              {valor === "conflito"
                ? t("nuvem.conflito")
                : valor === "solucao"
                  ? t("nuvem.solucao")
                  : valor === "lado_a_lado"
                    ? t("nuvem.lado_a_lado")
                    : t("nuvem.matriz")}
            </button>
          ))}
        </div>
      </div>

      {nuvem.origem ? <p className="origem">{t("nuvem.origem")}: {nuvem.origem.leitura}</p> : null}

      {/* Gerar NÃO aplica: a rota devolve pré-visualização e o identificador da ação
          governada. Quem escreve é a proposta, com gate humano (RF-21/RF-24). */}
      <form
        className="linha-de-criacao"
        onSubmit={(evento) => {
          evento.preventDefault();
          setErroDeAcao(null);
          cliente.nc
            .gerar(projetoId, narrativa.trim())
            .then(setPrevia)
            .catch(setErroDeAcao);
        }}
      >
        <label htmlFor="narrativa-do-dilema">{t("nuvem.gerar_narrativa")}</label>
        <input
          id="narrativa-do-dilema"
          value={narrativa}
          onChange={(evento) => setNarrativa(evento.target.value)}
        />
        <button type="submit">{t("nuvem.gerar")}</button>
      </form>

      {previa ? (
        <PreviaDaGeracao
          geracao={previa}
          textosAtuais={Object.fromEntries(nuvem.entidades.map((e) => [e.papel, e.texto]))}
          aoFechar={() => setPrevia(null)}
        />
      ) : null}

      {erroDeAcao ? (
        <p role="alert" className="erro">
          {mensagemDeErro(erroDeAcao, t)}
        </p>
      ) : null}

      <div className={`area-da-nuvem visao-${visao}`}>
        {visao === "conflito" || visao === "lado_a_lado" ? diagrama : null}
        {visao === "solucao" || visao === "lado_a_lado" ? <VisaoDeSolucao solucao={solucao} /> : null}
        {visao === "tabela" ? <MatrizDaNuvem matriz={matriz} aoAbrirAresta={setArestaAberta} /> : null}

        {aresta ? (
          <FichaDaAresta
            aresta={aresta}
            aoFechar={() => setArestaAberta(null)}
            aoRegistrarPremissa={(texto) =>
              escrever(async () => {
                await cliente.nc.registrarPremissa(projetoId, aresta.chave, texto);
              })
            }
            aoEditarPremissa={(premissaId, texto) =>
              escrever(async () => {
                await cliente.nc.editarPremissa(projetoId, premissaId, texto);
              })
            }
            aoDesafiarPremissa={(premissaId, justificativa) =>
              escrever(async () => {
                await cliente.nc.mudarEstadoDaPremissa(projetoId, premissaId, "desafiada", justificativa);
              })
            }
            aoRevigorarPremissa={(premissaId) =>
              escrever(async () => {
                await cliente.nc.mudarEstadoDaPremissa(projetoId, premissaId, "vigente");
              })
            }
            aoArquivarPremissa={async (premissaId) => {
              let quantas = 0;
              await escrever(async () => {
                quantas = (await cliente.nc.arquivarPremissa(projetoId, premissaId)).injecoes_arquivadas;
              });
              return quantas;
            }}
            aoRegistrarInjecao={(premissaId, texto, separacao: SeparacaoTRIZ | null) =>
              escrever(async () => {
                await cliente.nc.registrarInjecao(projetoId, premissaId, texto, separacao);
              })
            }
            aoClassificarInjecao={(injecaoId, separacao) =>
              escrever(async () => {
                await cliente.nc.classificarInjecao(projetoId, injecaoId, separacao);
              })
            }
            aoMudarStatusDaInjecao={(injecaoId, status: StatusDeInjecao, justificativa) =>
              escrever(async () => {
                await cliente.nc.mudarStatusDaInjecao(projetoId, injecaoId, status, justificativa);
              })
            }
            aoSugerirInjecoes={async (premissaId) => {
              const resposta = await cliente.nc.sugerirInjecoes(projetoId, premissaId);
              return resposta.sugestoes;
            }}
            aoSugerirPremissas={async () => {
              // Sugerir NÃO escreve: a resposta é pré-visualização, e a escrita é da ação
              // governada com gate humano (RF-21/RF-24). Recusar aqui não custa nada.
              const resposta = await cliente.nc.sugerirPremissas(projetoId, aresta.chave);
              return resposta.sugestoes;
            }}
          />
        ) : null}
      </div>
    </section>
  );
}
