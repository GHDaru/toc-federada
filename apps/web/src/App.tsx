/**
 * A casca da aplicação: federação, tema, idioma e navegação entre as ferramentas.
 *
 * Siglas, uma vez: **APH** — Aplicação ↔ Harness · **ARA** — Árvore da Realidade Atual ·
 * **NC** — Nuvem de Conflito · **CSS** — *Cascading Style Sheets* · **URL** — *Uniform
 * Resource Locator* · **API** — interface de programação de aplicações.
 *
 * Duas regras da norma moram aqui, e as duas são visíveis a olho nu na tela:
 *
 * 1. **Embarcada, só conteúdo** (§B.8.1): sem cabeçalho de navegação próprio, sem menu
 *    global, sem rodapé, sem seletor de inquilino. Quem navega é o hospedeiro, e dois
 *    menus na mesma janela é defeito de composição.
 * 2. **Sem admissão, não sobe** (§B.4.1): falta parâmetro obrigatório, a aplicação diz
 *    **qual** e não renderiza conteúdo. "Funcionar até alguém clicar" é a não-conformidade
 *    que a cláusula nomeia.
 *
 * Tudo o que toca o mundo — ambiente, URL, janela pai, função de envio, cliente da API —
 * entra por parâmetro. É o que torna esta casca testável inteira sem navegador de verdade,
 * e é o que impede a origem admitida de vir de qualquer lugar que não seja configuração.
 */
import { useEffect, useMemo, useRef, useState } from "react";
import { criarCliente, type Cliente } from "./api/cliente";
import { Carregando } from "./componentes/Estados";
import {
  deveRenderizarCasca,
  iniciarFederacao,
  type EstadoDaFederacao,
} from "./federacao/embarque";
import { variaveisCss, type Esquema } from "./federacao/tema";
import { ProvedorDeIdioma, useI18n, type Idioma } from "./i18n";
import { TelaDaAra } from "./telas/TelaDaAra";
import { TelaDaLixeira } from "./telas/TelaDaLixeira";
import { TelaDaNuvem } from "./telas/TelaDaNuvem";
import { TelaDeProjetos } from "./telas/TelaDeProjetos";
import type { ProjetoResumo } from "./dominio/tipos";

export interface AppProps {
  ambiente: Record<string, string | undefined>;
  url: string;
  pai: unknown;
  enviar: (mensagem: unknown, targetOrigin: string) => void;
  /** Injetável no teste; em produção nasce aqui, com o token da sessão de embarque. */
  cliente?: Cliente;
  esquemaPreferido?: Esquema;
}

type Rota =
  | { tela: "projetos" }
  | { tela: "lixeira" }
  | { tela: "ara"; projetoId: string }
  | { tela: "nuvem"; projetoId: string };

export function idiomaDaUrl(url: string, padrao: Idioma = "pt"): Idioma {
  try {
    const valor = new URL(url).searchParams.get("idioma");
    return valor === "en" || valor === "pt" ? valor : padrao;
  } catch {
    return padrao;
  }
}

export function App(props: AppProps) {
  return (
    <ProvedorDeIdioma idiomaInicial={idiomaDaUrl(props.url)}>
      <Aplicacao {...props} />
    </ProvedorDeIdioma>
  );
}

function Aplicacao({ ambiente, url, pai, enviar, cliente, esquemaPreferido = "claro" }: AppProps) {
  const { t, idioma, trocarIdioma } = useI18n();
  const sessao = useRef<string | null>(null);
  const [rota, setRota] = useState<Rota>({ tela: "projetos" });
  const [federacao, setFederacao] = useState<EstadoDaFederacao | null>(null);

  // O cliente é criado UMA vez e lê o token a cada chamada: o embarque troca o grant por
  // sessão depois da primeira renderização, e um cliente que capturasse o token no
  // nascimento ficaria anônimo para sempre.
  const clienteEmUso = useMemo(
    () => cliente ?? criarCliente({ obterToken: () => sessao.current }),
    [cliente],
  );

  useEffect(() => {
    const canal = iniciarFederacao({
      ambiente,
      url,
      pai,
      enviar,
      esquemaPreferido,
      trocarGrant: async (grant) => {
        const nova = await clienteEmUso.embarcar(grant);
        sessao.current = nova.token;
        return nova;
      },
      // O hospedeiro só avisa "algo mudou"; quem decide o que recarregar é a aplicação.
      aoMudarRecurso: () => setRota((atual) => ({ ...atual })),
    });
    setFederacao(canal.estado());
    const desassinar = canal.assinar(setFederacao);
    const ouvir = (evento: MessageEvent) => void canal.aoReceber(evento);
    window.addEventListener("message", ouvir);
    return () => {
      window.removeEventListener("message", ouvir);
      desassinar();
      canal.encerrar();
    };
  }, [ambiente, url, pai, enviar, esquemaPreferido, clienteEmUso]);

  if (!federacao) return <Carregando />;

  const estilo = variaveisCss(federacao.tema.resolvido) as React.CSSProperties;
  const comCasca = deveRenderizarCasca(federacao);

  if (federacao.fase === "recusada") {
    return (
      <div className="aplicacao recusada" style={estilo} data-esquema={federacao.esquema}>
        <div className="estado-de-erro" role="alert">
          <h1>{t("federacao.recusada")}</h1>
          {/* §B.4.1: o erro categorizado DIZ qual parâmetro faltou. */}
          <p>{federacao.motivo}</p>
        </div>
      </div>
    );
  }

  function abrirProjeto(projeto: ProjetoResumo) {
    setRota(
      projeto.ferramenta === "nc"
        ? { tela: "nuvem", projetoId: projeto.id }
        : { tela: "ara", projetoId: projeto.id },
    );
  }

  return (
    <div className="aplicacao" style={estilo} data-esquema={federacao.esquema}>
      {comCasca ? (
        <header className="casca-cabecalho" role="banner">
          <h1 className="marca">{t("app.titulo")}</h1>
          <p className="subtitulo">{t("app.subtitulo")}</p>
          <nav role="navigation" aria-label={t("app.titulo")}>
            <button type="button" aria-current={rota.tela === "projetos"} onClick={() => setRota({ tela: "projetos" })}>
              {t("navegacao.projetos")}
            </button>
            <button type="button" aria-current={rota.tela === "lixeira"} onClick={() => setRota({ tela: "lixeira" })}>
              {t("navegacao.lixeira")}
            </button>
          </nav>
          <div className="casca-idioma" role="group" aria-label={t("navegacao.idioma")}>
            <button type="button" aria-pressed={idioma === "pt"} onClick={() => trocarIdioma("pt")}>
              Português
            </button>
            <button type="button" aria-pressed={idioma === "en"} onClick={() => trocarIdioma("en")}>
              English
            </button>
          </div>
        </header>
      ) : null}

      {federacao.fase === "aguardando_handshake" ? (
        <p className="aviso-de-federacao" role="status">
          {t("federacao.aguardando")}
        </p>
      ) : null}

      {federacao.fase === "anonima" ? (
        <p className="aviso-de-federacao" role="status">
          {t("federacao.anonima")}
        </p>
      ) : null}

      <main className="conteudo">
        {rota.tela === "projetos" ? (
          <TelaDeProjetos cliente={clienteEmUso} aoAbrir={abrirProjeto} />
        ) : null}
        {rota.tela === "lixeira" ? <TelaDaLixeira cliente={clienteEmUso} /> : null}
        {rota.tela === "ara" ? (
          <TelaDaAra
            cliente={clienteEmUso}
            projetoId={rota.projetoId}
            aoVoltar={() => setRota({ tela: "projetos" })}
            aoAbrirNuvem={(projetoDaNuvem) => setRota({ tela: "nuvem", projetoId: projetoDaNuvem })}
          />
        ) : null}
        {rota.tela === "nuvem" ? (
          <TelaDaNuvem
            cliente={clienteEmUso}
            projetoId={rota.projetoId}
            aoVoltar={() => setRota({ tela: "projetos" })}
          />
        ) : null}
      </main>

      {comCasca ? (
        <footer className="casca-rodape" role="contentinfo">
          <p>
            {federacao.inquilino ? `${t("federacao.inquilino")}: ${federacao.inquilino.nome} · ` : ""}
            {federacao.sessao
              ? `${t("federacao.sessao_de", { nome: federacao.sessao.usuario.nome })} · `
              : ""}
            {t("federacao.modo_autonomo")}
          </p>
        </footer>
      ) : null}
    </div>
  );
}
