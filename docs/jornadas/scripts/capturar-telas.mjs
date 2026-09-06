/**
 * capturar-telas.mjs — o gerador das capturas das jornadas vivas.
 *
 * Siglas, uma vez: **TOC** — Teoria das Restrições · **ARA** — Árvore da Realidade Atual ·
 * **NC** — Nuvem de Conflito · **UDE** — Efeito Indesejável (*Undesirable Effect*) ·
 * **APH** — Aplicação ↔ Harness (o padrão da fronteira) · **API** — interface de
 * programação de aplicações · **URL** — *Uniform Resource Locator* · **SHA** — *Secure
 * Hash Algorithm* · **P6** — o princípio "Jornada viva" da constituição do projeto ·
 * **RI/RF/RN/INT** — requisito de interface / funcional / regra de negócio / integração.
 *
 * ## Por que este arquivo existe
 *
 * A Iron Law da skill `living-journey` é curta: **jornada sem captura do build real é
 * ficção**. Captura colada à mão não regenera, e por isso apodrece na primeira mudança de
 * tela. Este script é a alternativa: ele sobe a interface de verdade, fala com o
 * `toc-api` de verdade sobre o PostgreSQL de verdade, percorre a aplicação com um
 * navegador de verdade e grava as imagens que os documentos de `docs/jornadas/` citam.
 *
 * ## O que ele NÃO faz
 *
 * Ele não desenha tela nenhuma, não usa duplo de cliente e não tem mock. Se uma cena não
 * puder ser capturada, a captura **falha e o script sai diferente de zero** — a jornada
 * correspondente fica sem a imagem e isso tem de aparecer, e não ser contornado com uma
 * figura de outro dia.
 *
 * ## Pré-requisito único: o PostgreSQL de desenvolvimento de pé
 *
 *     su postgres -c "/usr/lib/postgresql/16/bin/pg_ctl -D /var/lib/postgresql/tocdata \
 *       -o '-p 5433 -k /var/run/postgresql' -l /tmp/pg.log start"
 *
 * O resto — o serviço `toc-api`, as TRÊS instâncias da interface e o hospedeiro de
 * bancada — este script sobe e derruba sozinho, porque cada jornada precisa de um
 * ambiente diferente e um ambiente só não prova as três coisas:
 *
 * | Processo | Porta | Para quê |
 * |---|---|---|
 * | `toc-api` | 8000 | o serviço, com os seis parâmetros de admissão do §B.4 preenchidos |
 * | interface autônoma | 5273 | J-02, J-03 e a travessia: a aplicação com casca própria |
 * | interface embarcada | 5274 | J-01: `?embarcado=1`, **sem token no proxy** — a identidade tem de vir do handshake |
 * | interface recusada | 5276 | J-01: falta `VITE_GHD_EMBED_URL`; §B.4.1 manda **não subir** |
 * | hospedeiro de bancada | 5275 | J-01: embarca a aplicação, fala `ghd.*` e responde `POST /auth/introspect` |
 *
 * ## O hospedeiro de bancada é declarado, não disfarçado
 *
 * A bancada **não é a `ghdaru`**. É um servidor de uma página que fala o `ghd.*` do Anexo
 * B (recebe `ghd.ready`, responde `ghd.handshake` com inquilino, tema e grant de uso
 * único) e que expõe `POST /auth/introspect` devolvendo a persona fictícia do §B.6. O que
 * ela prova é o lado **da aplicação** da junta, que é o lado que este repositório escreve;
 * o que ela não prova é o lado do hospedeiro real, e isso está dito com todas as letras
 * na jornada J-01.
 *
 * ## Rodar
 *
 *     PLAYWRIGHT_BROWSERS_PATH=/opt/pw-browsers node docs/jornadas/scripts/capturar-telas.mjs
 *
 * Opções: `--jornada J-02` (só uma), `--sem-zerar` (não trunca o banco de
 * desenvolvimento), `--verboso` (imprime cada pedido que chega ao hospedeiro de bancada).
 *
 * O Chromium já está instalado em `/opt/pw-browsers` — **nunca** rode `playwright install`.
 * O pacote `playwright` é resolvido localmente e, se não estiver, na instalação global do
 * Node (`npm root -g`), que é onde ele vive nesta máquina.
 *
 * ## Base sintética (ADR 0006)
 *
 * Todo o conteúdo capturado vem de `docs/produto/dados/analise-horizonte.json`: a
 * Instituição Horizonte é fictícia e as personas são papéis ("Facilitadora TOC"), não
 * pessoas. Nenhum dado real de pessoa entra em captura — é o que mantém este repositório
 * apto a ser aberto, e `scripts/check-vazamento.sh` é o portão.
 */
import { createHash } from "node:crypto";
import { spawn, execSync } from "node:child_process";
import { createRequire } from "node:module";
import { createServer } from "node:http";
import { mkdirSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const AQUI = dirname(fileURLToPath(import.meta.url));
const RAIZ = resolve(AQUI, "..", "..", "..");
const CAPTURAS = join(RAIZ, "docs", "jornadas", "capturas");
const WEB = join(RAIZ, "apps", "web");

const API = process.env.TOC_API_URL ?? "http://127.0.0.1:8000";
/** Identidade FICTÍCIA de desenvolvimento (`apps/api/.../infra/identidade/falso.py:39`).
 *  Não é segredo: é o registro fechado que só responde em `TOC_AMBIENTE=desenvolvimento`. */
const TOKEN_DEV = process.env.TOC_TOKEN_DEV ?? "tok-desenvolvimento-facilitadora";
/** A cadeia do cluster local de desenvolvimento (`docs/governance/como-fechar-um-ciclo.md`). */
const BANCO =
  process.env.DATABASE_URL ??
  "postgresql+psycopg://toc@/toc_federada?host=/var/run/postgresql&port=5433";

const PORTA_API = 8000;
const PORTA_AUTONOMA = 5273;
const PORTA_EMBARCADA = 5274;
const PORTA_HOSPEDEIRO = 5275;
const PORTA_RECUSADA = 5276;

const URL_AUTONOMA = `http://127.0.0.1:${PORTA_AUTONOMA}`;
const URL_EMBARCADA = `http://127.0.0.1:${PORTA_EMBARCADA}`;
const URL_HOSPEDEIRO = `http://127.0.0.1:${PORTA_HOSPEDEIRO}`;
const URL_RECUSADA = `http://127.0.0.1:${PORTA_RECUSADA}`;

const VIEWPORT = { width: 1440, height: 900 };
const VIEWPORT_ESTREITO = { width: 420, height: 820 };

const argumentos = process.argv.slice(2);
const SO_A_JORNADA = valorDe("--jornada");
const ZERAR = !argumentos.includes("--sem-zerar");
const VERBOSO = argumentos.includes("--verboso");

function valorDe(bandeira) {
  const i = argumentos.indexOf(bandeira);
  return i >= 0 ? argumentos[i + 1] : null;
}

// -- registro do que foi capturado ------------------------------------------------------

/** Cada captura vira uma linha aqui; o manifesto é a evidência (regras R1 e R2). */
const registro = [];
const falhas = [];
/** Números medidos durante a corrida — o que a imagem não consegue dizer sozinha. */
const medidas = {};

function log(texto) {
  process.stdout.write(`${texto}\n`);
}

// -- resolução do Playwright ------------------------------------------------------------

async function carregarPlaywright() {
  const require = createRequire(import.meta.url);
  try {
    return require("playwright");
  } catch {
    const global = execSync("npm root -g", { encoding: "utf8" }).trim();
    return require(join(global, "playwright"));
  }
}

// -- a base sintética -------------------------------------------------------------------

const BASE = JSON.parse(
  readFileSync(join(RAIZ, "docs", "produto", "dados", "analise-horizonte.json"), "utf8"),
);

if (BASE.sintetica !== true) {
  throw new Error(
    "a base de captura não está marcada como sintética — ADR 0006 proíbe capturar outra coisa",
  );
}

/**
 * Posição de cada nó no canvas. Três faixas, de baixo para cima na leitura causal:
 * a causa raiz embaixo, as causas intermediárias no meio, os efeitos em cima.
 * O nó tem 240×92 (`apps/web/src/componentes/canvas/useViewport.ts:27`), daí o passo.
 */
function posicoes() {
  const mapa = new Map();
  const udes = BASE.ara.nos.filter((n) => n.tipo === "ude");
  const causas = BASE.ara.nos.filter((n) => n.tipo === "causa");
  const raiz = BASE.ara.nos.filter((n) => n.tipo === "causa_raiz");
  udes.forEach((n, i) => mapa.set(n.id, { x: 60 + (i % 6) * 280, y: 60 + Math.floor(i / 6) * 150 }));
  causas.forEach((n, i) => mapa.set(n.id, { x: 200 + i * 420, y: 520 }));
  raiz.forEach((n) => mapa.set(n.id, { x: 620, y: 700 }));
  return mapa;
}

// -- cliente da API (o MESMO serviço que a interface chama) ------------------------------

async function api(caminho, { metodo = "GET", corpo } = {}) {
  const resposta = await fetch(`${API}${caminho}`, {
    method: metodo,
    headers: {
      authorization: `Bearer ${TOKEN_DEV}`,
      ...(corpo === undefined ? {} : { "content-type": "application/json" }),
    },
    body: corpo === undefined ? undefined : JSON.stringify(corpo),
  });
  if (!resposta.ok) {
    const texto = await resposta.text();
    throw new Error(`${metodo} ${caminho} → ${resposta.status} ${texto.slice(0, 400)}`);
  }
  return resposta.status === 204 ? null : resposta.json();
}

// -- infraestrutura da captura ----------------------------------------------------------

async function esperarPorta(url, rotulo, tentativas = 120) {
  for (let i = 0; i < tentativas; i += 1) {
    try {
      const r = await fetch(url, { redirect: "manual" });
      if (r.status < 500) return;
    } catch {
      /* ainda não subiu */
    }
    await new Promise((ok) => setTimeout(ok, 500));
  }
  throw new Error(`${rotulo} não respondeu em ${url} depois de ${tentativas / 2}s`);
}

const processos = [];

function subirVite(porta, ambiente, rotulo) {
  const filho = spawn(
    "npx",
    ["vite", "--port", String(porta), "--strictPort", "--host", "127.0.0.1"],
    { cwd: WEB, env: { ...process.env, ...ambiente }, stdio: ["ignore", "pipe", "pipe"] },
  );
  filho.rotulo = rotulo;
  filho.saida = [];
  filho.stdout.on("data", (d) => filho.saida.push(String(d)));
  filho.stderr.on("data", (d) => filho.saida.push(String(d)));
  processos.push(filho);
  return filho;
}

/** O serviço `toc-api`, com os seis parâmetros de admissão do §B.4 preenchidos. */
function subirServico() {
  const filho = spawn(
    ".venv/bin/uvicorn",
    ["--factory", "toc_api.http.app:criar_app", "--host", "127.0.0.1", "--port", String(PORTA_API)],
    {
      cwd: join(RAIZ, "apps", "api"),
      env: {
        ...process.env,
        DATABASE_URL: BANCO,
        TOC_AMBIENTE: "desenvolvimento",
        // Os quatro do Anexo B mais os dois nossos (`admissao.py:68-107`). A `EMBED_URL`
        // é `https` por exigência do schema do manifesto — é o ponto de montagem
        // DECLARADO, não uma URL que alguém busca aqui.
        HOST_ORIGIN: URL_HOSPEDEIRO,
        HOST_BASE_URL: `${URL_HOSPEDEIRO}/api`,
        APP_ID: "toc-federada",
        EMBED_URL: "https://toc-federada.exemplo/toc/embarcado",
        // Fictícia e **ASCII de propósito**: um caractere fora de ASCII aqui vira
        // `UnicodeEncodeError` ao montar o cabeçalho `Authorization` do httpx, e o
        // serviço traduz isso para `FUNDACAO_INDISPONIVEL` (503) — medido nesta bancada.
        TOC_APP_CREDENTIAL: "credencial-de-bancada-ficticia",
      },
      stdio: ["ignore", "pipe", "pipe"],
    },
  );
  filho.rotulo = "toc-api";
  filho.saida = [];
  filho.stdout.on("data", (d) => filho.saida.push(String(d)));
  filho.stderr.on("data", (d) => filho.saida.push(String(d)));
  processos.push(filho);
  return filho;
}

/**
 * O hospedeiro de bancada: a página que embarca a aplicação **e** o `POST /auth/introspect`
 * do §B.6, que é o que faz o grant do handshake virar identidade de verdade.
 */
function subirHospedeiro() {
  const html = paginaDoHospedeiro();
  const servidor = createServer((pedido, resposta) => {
    medidas.pedidosAoHospedeiro = (medidas.pedidosAoHospedeiro ?? 0) + 1;
    if (VERBOSO) log(`  [hospedeiro] ${pedido.method} ${pedido.url}`);
    if (pedido.method === "POST" && pedido.url.startsWith("/api/auth/introspect")) {
      let bruto = "";
      pedido.on("data", (pedaco) => {
        bruto += pedaco;
      });
      pedido.on("end", () => {
        let grant = "";
        try {
          grant = JSON.parse(bruto || "{}").token ?? "";
        } catch {
          grant = "";
        }
        // §B.6.3: as três respostas são de SUCESSO; quem não é reconhecido volta
        // `active: false`, e não um 4xx que serviria de oráculo.
        const corpo =
          grant === TOKEN_DEV
            ? {
                active: true,
                user: { id: "usr-facilitadora", name: "Facilitadora TOC" },
                tenant_id: "inq-horizonte",
                capabilities: ["toc:read", "toc:write"],
                app_id: "toc-federada",
              }
            : { active: false };
        resposta.writeHead(200, { "content-type": "application/json" });
        resposta.end(JSON.stringify(corpo));
      });
      return;
    }
    resposta.writeHead(200, { "content-type": "text/html; charset=utf-8" });
    resposta.end(html);
  });
  servidor.listen(PORTA_HOSPEDEIRO, "127.0.0.1");
  processos.push({ servidorHttp: servidor, rotulo: "hospedeiro" });
  return servidor;
}

function derrubarTudo() {
  for (const p of processos) {
    try {
      if (p.servidorHttp) p.servidorHttp.close();
      else p.kill("SIGTERM");
    } catch {
      /* já morreu */
    }
  }
}

function zerarBanco() {
  const tabelas = [
    "projeto",
    "no",
    "aresta_causal",
    "ude",
    "ude_parecer",
    "elo_exame",
    "conector_e",
    "conector_e_aresta",
    "nc_nuvem",
    "nc_premissa",
    "nc_injecao",
    "proposta_de_acao",
    "traco_de_execucao",
  ];
  execSync(
    `psql -h /var/run/postgresql -p 5433 -U toc -d toc_federada -v ON_ERROR_STOP=1 ` +
      `-c "TRUNCATE ${tabelas.join(", ")} CASCADE;"`,
    { stdio: "pipe" },
  );
}

/**
 * Grava uma captura e registra o que ela pesa. `alvo` pode ser a página inteira ou um
 * localizador — capturar só a ficha, quando é a ficha que a jornada narra, é o que evita
 * uma imagem de 1440px onde o leitor tem de procurar onde olhar.
 */
async function capturar(jornada, nome, alvo, { paginaInteira = true } = {}) {
  const pasta = join(CAPTURAS, jornada);
  mkdirSync(pasta, { recursive: true });
  const arquivo = join(pasta, `${nome}.png`);
  try {
    if (typeof alvo.screenshot !== "function") throw new Error("alvo sem screenshot()");
    // `goto` só existe na página; num localizador `fullPage` nem é opção válida.
    const ehPagina = typeof alvo.goto === "function";
    await alvo.screenshot(ehPagina ? { path: arquivo, fullPage: paginaInteira } : { path: arquivo });
    const bytes = readFileSync(arquivo);
    const linha = {
      jornada,
      captura: `${jornada}/${nome}.png`,
      bytes: bytes.length,
      sha256: createHash("sha256").update(bytes).digest("hex"),
    };
    registro.push(linha);
    log(`  ok   ${linha.captura}  ${linha.bytes} bytes`);
  } catch (erro) {
    falhas.push({ jornada, captura: `${jornada}/${nome}.png`, erro: String(erro && erro.message) });
    log(`  FALHA ${jornada}/${nome}.png — ${erro && erro.message}`);
  }
}

// -- a página do hospedeiro de bancada ---------------------------------------------------

function paginaDoHospedeiro() {
  return `<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8"><title>Fundação Horizonte — bancada</title>
<style>
 :root{--casca:#0b1220;--linha:#1e293b;--texto:#e2e8f0;--realce:#7c3aed}
 *{box-sizing:border-box} body{margin:0;font:14px/1.5 system-ui,sans-serif;background:var(--casca);color:var(--texto)}
 header{padding:14px 20px;border-bottom:1px solid var(--linha);display:flex;gap:16px;align-items:baseline}
 header b{font-size:16px;color:var(--realce)}
 .corpo{display:grid;grid-template-columns:220px 1fr 300px;gap:0;height:calc(100vh - 56px)}
 nav{border-right:1px solid var(--linha);padding:16px}
 nav a{display:block;padding:8px 10px;border-radius:6px;color:var(--texto);text-decoration:none}
 nav a.ativo{background:var(--realce);color:#fff}
 iframe{width:100%;height:100%;border:0;background:#fff}
 aside{border-left:1px solid var(--linha);padding:16px;font-family:ui-monospace,monospace;font-size:12px;overflow:auto}
 aside h2{font-size:12px;text-transform:uppercase;letter-spacing:.08em;color:#94a3b8}
 li{margin-bottom:6px;word-break:break-all}
</style></head><body>
<header><b>Fundação Horizonte</b><span>plataforma hospedeira (bancada do Anexo B)</span>
 <span style="margin-left:auto">Facilitadora TOC · inq-horizonte</span></header>
<div class="corpo">
 <nav><a href="#">Painel</a><a href="#" class="ativo">Análise TOC</a><a href="#">Documentos</a><a href="#">Relatórios</a></nav>
 <iframe id="app" title="Aplicação TOC embarcada" src="${URL_EMBARCADA}/?embarcado=1"></iframe>
 <aside><h2>Canal ghd.*</h2><ol id="registro"></ol></aside>
</div>
<script>
 const ORIGEM_DA_APP = ${JSON.stringify(URL_EMBARCADA)};
 const registro = document.getElementById("registro");
 function anotar(t){ const li=document.createElement("li"); li.textContent=t; registro.appendChild(li); }
 window.addEventListener("message", (ev) => {
   if (ev.origin !== ORIGEM_DA_APP) return;
   const m = ev.data;
   if (!m || m.protocol !== "ghd" || m.v !== 1) return;
   anotar("recebido " + m.type + " " + JSON.stringify(m.payload));
   if (m.type === "ghd.ready") {
     const handshake = { protocol:"ghd", v:1, type:"ghd.handshake", payload:{
       token: ${JSON.stringify(TOKEN_DEV)},
       tenant: { id:"inq-horizonte", name:"Instituição Horizonte" },
       theme: { tokens: { "color-primary":"#7c3aed", "color-surface":"#ffffff",
                          "color-text":"#1e1b4b", "color-danger":"#be123c" } }
     }};
     ev.source.postMessage(handshake, ORIGEM_DA_APP);
     anotar("enviado ghd.handshake (grant de uso único, tema do inquilino)");
   }
 });
</script></body></html>`;
}

// -- semeadura da Instituição Horizonte ---------------------------------------------------

/** Cria a ARA inteira da base pela MESMA API que a interface usa. Devolve o mapa id→uuid. */
async function semearAra(projetoId) {
  const pos = posicoes();
  const porId = new Map();
  for (const no of BASE.ara.nos) {
    const criado = await api(`/toc/ara/projetos/${projetoId}/efeitos`, {
      metodo: "POST",
      corpo: { titulo: no.texto, descricao: `${no.id} · autor ${no.autor ?? "—"}`, posicao: pos.get(no.id) },
    });
    porId.set(no.id, criado.id);
  }
  for (const aresta of BASE.ara.arestas) {
    // Pela rota da ARA, e não pela genérica do M1: desde a correção da porta dos fundos do
    // agregado, o grafo de um projeto de ferramenta só muda pela raiz dele — a genérica
    // responde `409 AGGREGATE_ROOT_REQUIRED`, e é o elo com exame de suficiência que se
    // ganha aqui (RF-22 da spec 005).
    await api(`/toc/ara/projetos/${projetoId}/arestas`, {
      metodo: "POST",
      corpo: { origem_id: porId.get(aresta.de), destino_id: porId.get(aresta.para), rotulo: "" },
    });
  }
  // Só os doze UDEs viram Efeito Indesejável; causa e causa raiz são posição na cadeia,
  // não efeito marcado (F-15 da spec 005).
  for (const no of BASE.ara.nos.filter((n) => n.tipo === "ude")) {
    await api(`/toc/ara/projetos/${projetoId}/nos/${porId.get(no.id)}/ude`, {
      metodo: "POST",
      corpo: {},
    });
  }
  return porId;
}

// =======================================================================================
// J-01 — Chegada e embarque
// =======================================================================================

/**
 * Mede a cadeia do §B.6 fora do navegador, com o mesmo serviço: grant → sessão → uso.
 * Existe porque uma captura mostra o resultado e não mostra o código de estado — e é o
 * código de estado que diz onde a cadeia fecha e onde ela não fecha (regra R1).
 */
async function medirCadeiaDeEmbarque() {
  const troca = await fetch(`${API}/toc/embarque`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ token: TOKEN_DEV }),
  });
  const corpo = await troca.json();
  log(`  · POST /toc/embarque → HTTP ${troca.status} ${JSON.stringify(corpo).slice(0, 200)}`);
  if (!troca.ok) return { embarque: troca.status, conteudo: null, catalogo: null };
  const sessao = corpo.sessao;
  const conteudo = await fetch(`${API}/toc/projetos`, {
    headers: { authorization: `Bearer ${sessao}` },
  });
  const catalogo = await fetch(`${API}/aph/catalog`, {
    headers: { authorization: `Bearer ${sessao}` },
  });
  log(`  · GET /toc/projetos  com a sessão do embarque → HTTP ${conteudo.status}`);
  log(`  · GET /aph/catalog   com a sessão do embarque → HTTP ${catalogo.status}`);
  return { embarque: troca.status, conteudo: conteudo.status, catalogo: catalogo.status };
}

async function jornadaChegadaEEmbarque(navegador) {
  log("J-01 · chegada e embarque");
  const jornada = "001-chegada-e-embarque";

  const medida = await medirCadeiaDeEmbarque();
  medidas.embarque = medida;

  // 1. §B.4.1 — falta parâmetro de admissão: a aplicação NÃO sobe e diz qual faltou.
  const recusada = await navegador.newPage({ viewport: VIEWPORT });
  await recusada.goto(`${URL_RECUSADA}/?embarcado=1`, { waitUntil: "networkidle" });
  await recusada.getByRole("alert").waitFor({ timeout: 15000 });
  await capturar(jornada, "01-admissao-recusada", recusada);
  await recusada.close();

  // 2. o hospedeiro de bancada com a aplicação embarcada: o handshake acontece de
  //    verdade (o painel do canal registra os dois lados) e o grant é trocado por sessão
  //    de verdade. O que a captura mostra do CONTEÚDO é o que o serviço devolveu — e hoje
  //    ele devolve 401 nas rotas `/toc/*` para a sessão nascida do embarque. A captura
  //    registra isso em vez de escondê-lo com o token do proxy.
  const hospedeiro = await navegador.newPage({ viewport: VIEWPORT });
  await hospedeiro.goto(URL_HOSPEDEIRO, { waitUntil: "networkidle" });
  await hospedeiro.locator("#registro li").nth(1).waitFor({ timeout: 25000 });
  await hospedeiro.waitForTimeout(2500);
  await capturar(jornada, "02-hospedeiro-com-a-aplicacao", hospedeiro, { paginaInteira: false });
  await capturar(jornada, "03-canal-ghd-no-hospedeiro", hospedeiro.locator("aside"));
  const linhasDoCanal = await hospedeiro.locator("#registro li").allInnerTexts();
  medidas.canal = linhasDoCanal;
  for (const linha of linhasDoCanal) log(`  · canal: ${linha.slice(0, 140)}`);
  await hospedeiro.close();

  // 3. embarcada em 420px: §B.8.1 — só conteúdo, nenhuma casca própria. Aqui a instância
  //    é a autônoma com `?embarcado=1`: sem hospedeiro que responda, o §B.3.2 manda seguir
  //    ANÔNIMA em vez de mostrar erro fatal, e o conteúdo continua renderizando.
  const estreita = await navegador.newPage({ viewport: VIEWPORT_ESTREITO });
  await estreita.goto(`${URL_AUTONOMA}/?embarcado=1`, { waitUntil: "networkidle" });
  await estreita.getByRole("heading", { name: "Projetos" }).waitFor({ timeout: 20000 });
  const cascas = await estreita.getByRole("banner").count();
  medidas.cascaEmbarcada = cascas;
  log(`  · casca própria no modo embarcado (§B.8.1, esperado 0): ${cascas}`);
  if (cascas !== 0) falhas.push({ jornada, captura: "—", erro: `casca própria embarcada: ${cascas}` });
  await estreita.waitForTimeout(7000); // além da janela de 6s do §B.3.2
  await capturar(jornada, "04-embarcada-420px", estreita);
  await estreita.close();

  // 4. autônoma: a MESMA aplicação com casca própria, para o contraste ser visível.
  const autonoma = await navegador.newPage({ viewport: VIEWPORT });
  await autonoma.goto(URL_AUTONOMA, { waitUntil: "networkidle" });
  await autonoma.getByRole("banner").waitFor({ timeout: 20000 });
  await capturar(jornada, "05-autonoma-com-casca", autonoma);
  await autonoma.close();
}

// =======================================================================================
// J-02 — Primeiro projeto e a Árvore da Realidade Atual
// =======================================================================================

const NOME_DA_ARA = "Evasão na Instituição Horizonte";

async function jornadaAra(navegador) {
  log("J-02 · primeiro projeto e ARA");
  const jornada = "002-primeiro-projeto-e-ara";
  const pagina = await navegador.newPage({ viewport: VIEWPORT });
  await pagina.goto(URL_AUTONOMA, { waitUntil: "networkidle" });

  // 1. a lista, ainda vazia.
  await pagina.getByRole("heading", { name: "Projetos" }).waitFor({ timeout: 20000 });
  await capturar(jornada, "01-lista-vazia", pagina);

  // 2. a Facilitadora cria o projeto pela tela.
  await pagina.getByLabel("Nome", { exact: true }).fill(NOME_DA_ARA);
  await pagina
    .getByLabel("Descrição do problema")
    .fill("Turmas abrem cheias e terminam vazias; metade não conclui o curso.");
  await pagina.getByLabel("Ferramenta").selectOption("ara");
  await pagina.getByRole("button", { name: "Criar projeto" }).click();
  const linha = pagina.getByRole("row", { name: new RegExp(NOME_DA_ARA) });
  await linha.waitFor({ timeout: 20000 });
  await capturar(jornada, "02-projeto-criado", pagina);

  // 3. a árvore recém-aberta, ainda sem nó nenhum.
  await linha.getByRole("button", { name: "Abrir" }).click();
  await pagina.getByRole("tab", { name: "Nós (0)" }).waitFor({ timeout: 20000 });
  await capturar(jornada, "03-ara-vazia", pagina);

  // 4. a análise da Instituição Horizonte entra pela API — o mesmo serviço da tela.
  const projetos = await api("/toc/projetos");
  const projeto = projetos.find((p) => p.nome === NOME_DA_ARA);
  if (!projeto) throw new Error("o projeto criado pela tela não voltou na listagem da API");
  const porId = await semearAra(projeto.id);
  /** `U-08` (a chave da base) → o identificador que o serviço deu ao nó. */
  const porIdDoUde = (chave) => porId.get(chave);

  // Recarregar volta para a lista: a rota vive no estado do React e NÃO na URL — está
  // registrado como achado da avaliação heurística desta jornada, não é acidente da
  // captura. Por isso o projeto é reaberto pela tela, como a pessoa faria.
  await pagina.reload({ waitUntil: "networkidle" });
  await linhaDoProjeto(pagina, NOME_DA_ARA, { semNuvem: true })
    .getByRole("button", { name: "Abrir" })
    .click();
  await pagina.getByRole("tab", { name: `Nós (${BASE.ara.nos.length})` }).waitFor({ timeout: 20000 });
  await pagina.getByRole("button", { name: "Ajustar à tela" }).click();
  await pagina.waitForTimeout(400);
  // Duas capturas, e a segunda é um ACHADO, não um enfeite:
  //  · a página inteira mostra a árvore — é o que a pessoa vê DEPOIS de rolar;
  //  · a janela de 1440×900 mostra o que ela vê ANTES de rolar: canvas vazio.
  // A medida abaixo explica por quê, e é ela que entra na avaliação heurística (A-03).
  await capturar(jornada, "04-arvore-da-horizonte", pagina);
  await capturar(jornada, "05-canvas-abaixo-da-dobra", pagina, { paginaInteira: false });

  medidas.canvas = await pagina.evaluate(() => {
    const area = document.querySelector(".canvas-area");
    const plano = document.querySelector(".canvas-plano");
    const no = document.querySelector(".no-do-canvas");
    return {
      altura_da_janela: window.innerHeight,
      altura_da_area_do_canvas: area ? Math.round(area.getBoundingClientRect().height) : null,
      transformacao_do_plano: plano ? plano.style.transform : null,
      topo_do_primeiro_no: no ? Math.round(no.getBoundingClientRect().top) : null,
    };
  });
  log(
    `  · canvas: janela ${medidas.canvas.altura_da_janela}px · área do canvas ` +
      `${medidas.canvas.altura_da_area_do_canvas}px · ${medidas.canvas.transformacao_do_plano} ` +
      `· topo do 1º nó em ${medidas.canvas.topo_do_primeiro_no}px`,
  );

  const ara = await api(`/toc/ara/projetos/${projeto.id}`);
  medidas.resumo_por_status = ara.resumo_por_status;
  medidas.udes = ara.udes.length;
  log(
    `  · ${ara.udes.length} UDEs marcados · resumo por status: ` +
      Object.entries(ara.resumo_por_status)
        .map(([k, v]) => `${k}=${v}`)
        .join(" "),
  );

  // 5. a mesma árvore na vista tabular, aba de arestas.
  await pagina.getByRole("tab", { name: `Arestas (${BASE.ara.arestas.length})` }).click();
  await pagina.waitForTimeout(200);
  await capturar(jornada, "06-painel-de-arestas", pagina.locator("aside.painel"));
  await pagina.getByRole("tab", { name: `Nós (${BASE.ara.nos.length})` }).click();

  // 6. a ficha de um UDE REPROVADO — U-08, "O atendimento ao aluno é péssimo."
  await abrirFicha(pagina, "O atendimento ao aluno é péssimo.");
  await capturar(jornada, "07-ficha-de-ude-reprovado", pagina.locator("section.ficha"));

  // 7. reformular é reexecutar a validação (RF-10): o SERVIDOR revalida com o texto novo.
  //    A ficha, porém, não redesenha o veredito sem ser reaberta — o achado A-02 da
  //    avaliação heurística desta jornada. A captura mostra a ficha logo depois do
  //    clique, e a medida abaixo mostra o que o serviço tem de verdade.
  const noReformulado = porIdDoUde("U-08");
  await pagina
    .getByLabel("Texto do efeito")
    .fill("A instituição responde 31% das mensagens de aluno em até cinco dias úteis.");
  await pagina.getByRole("button", { name: "Reformular" }).click();
  await pagina.waitForTimeout(1500);
  await capturar(jornada, "08-ficha-logo-apos-reformular", pagina.locator("section.ficha"));

  const depoisDaReformulacao = await api(`/toc/ara/projetos/${projeto.id}`);
  const udeReformulado = depoisDaReformulacao.udes.find((u) => u.no_id === noReformulado);
  medidas.reformulacao = {
    titulo_no_servidor: depoisDaReformulacao.projeto.nos.find((n) => n.id === noReformulado).titulo,
    aprovado_nos_decidiveis: udeReformulado.validacao.aprovado_nos_decidiveis,
    reprovacoes: udeReformulado.validacao.reprovacoes.length,
  };
  log(
    `  · reformulação no servidor: "${medidas.reformulacao.titulo_no_servidor.slice(0, 60)}…" ` +
      `· aprovado nos decidíveis: ${medidas.reformulacao.aprovado_nos_decidiveis} ` +
      `· reprovações: ${medidas.reformulacao.reprovacoes}`,
  );

  // 8. fechar e reabrir a MESMA ficha: agora o veredito acompanha o texto.
  await pagina.getByRole("button", { name: "Fechar" }).first().click();
  await pagina.waitForTimeout(300);
  await abrirFicha(pagina, "A instituição responde 31% das mensagens de aluno");
  await capturar(jornada, "09-ficha-reaberta-com-veredito-novo", pagina.locator("section.ficha"));
  await pagina.getByRole("button", { name: "Fechar" }).first().click();
  await pagina.waitForTimeout(300);

  // 9. um UDE que já nasce aprovado nos decidíveis — U-01 —, o parecer humano e o status.
  //    Quem valida é a pessoa, não o modelo (RF-16): o autor vem do principal.
  await abrirFicha(pagina, "O intervalo médio da matrícula até a primeira aula");
  await capturar(jornada, "10-ficha-de-ude-aprovado", pagina.locator("section.ficha"));
  await pagina
    .locator("#justificativa-do-parecer")
    .fill("Medido no relatório de matrículas do semestre corrente; o grupo confirmou o número.");
  await pagina.getByRole("button", { name: "Registrar parecer" }).click();
  await pagina.waitForTimeout(1000);
  await pagina
    .locator("section.ficha")
    .getByRole("button", { name: "Validado", exact: true })
    .click();
  await pagina.waitForTimeout(1000);
  await abrirFicha(pagina, "O intervalo médio da matrícula até a primeira aula");
  await capturar(jornada, "11-parecer-e-status-validado", pagina.locator("section.ficha"));
  await pagina.getByRole("button", { name: "Fechar" }).first().click();

  // 10. o resumo por status no cabeçalho, com o filtro aplicado.
  await pagina.getByRole("button", { name: "Ajustar à tela" }).click();
  await pagina.getByRole("button", { name: /^Pendente: / }).click();
  await pagina.waitForTimeout(600);
  await capturar(jornada, "12-resumo-por-status-filtrado", pagina, { paginaInteira: false });
  await pagina.getByRole("button", { name: "Limpar filtro" }).click();

  // 11. o exame de suficiência de um elo.
  await pagina.getByRole("tab", { name: `Arestas (${BASE.ara.arestas.length})` }).click();
  await pagina.getByRole("button", { name: "Examinar elo" }).first().click();
  await pagina.waitForTimeout(400);
  await capturar(jornada, "13-exame-de-elo", pagina.locator("section.ficha").first());
  const fechar = pagina.getByRole("button", { name: "Fechar" }).first();
  if (await fechar.count()) await fechar.click();

  // 12. o relatório estrutural: cobertura, elos não examinados e causa raiz candidata.
  await pagina.getByRole("button", { name: "Analisar árvore" }).click();
  await pagina.waitForTimeout(900);
  await capturar(jornada, "14-relatorio-estrutural", pagina, { paginaInteira: false });

  await pagina.close();
  return { projetoId: projeto.id, porId };
}

/**
 * Abre a ficha de validação de um UDE pelo texto dele, na vista tabular.
 *
 * Clica na **primeira célula** e não no centro da linha: o centro cai na coluna de status,
 * que tem caixa de seleção e botões — clicar ali seleciona o nó E mexe em outra coisa.
 */
async function abrirFicha(pagina, texto) {
  const linha = pagina.getByRole("row", { name: new RegExp(escapar(texto)) }).first();
  await linha.waitFor({ timeout: 15000 });
  await linha.locator("td").first().click();
  await pagina.locator("section.ficha").waitFor({ timeout: 15000 });
  await pagina.waitForTimeout(400);
}

/** A linha de um projeto na lista, opcionalmente excluindo a nuvem derivada dele. */
function linhaDoProjeto(pagina, nome, { semNuvem = false } = {}) {
  const linhas = pagina.getByRole("row").filter({ hasText: nome });
  return (semNuvem ? linhas.filter({ hasNotText: "nuvem" }) : linhas).first();
}

function escapar(texto) {
  return texto.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

// =======================================================================================
// J-07 — A travessia: da ARA à Nuvem de Conflito
// =======================================================================================

/** Os dois UDEs que sustentam o dilema: volume de turmas × conclusão. */
const UDES_DA_TRAVESSIA = ["U-02", "U-03"];

async function jornadaTravessia(navegador, { projetoId, porId }) {
  log("J-07 · a travessia (ARA → NC)");
  const jornada = "007-a-travessia";
  const pagina = await navegador.newPage({ viewport: VIEWPORT });
  await pagina.goto(URL_AUTONOMA, { waitUntil: "networkidle" });
  await linhaDoProjeto(pagina, NOME_DA_ARA, { semNuvem: true })
    .getByRole("button", { name: "Abrir" })
    .click();
  await pagina.getByRole("tab", { name: `Nós (${BASE.ara.nos.length})` }).waitFor({ timeout: 20000 });

  // 1. a Facilitadora marca os dois efeitos que sustentam o dilema.
  for (const chave of UDES_DA_TRAVESSIA) {
    const texto = BASE.ara.nos.find((n) => n.id === chave).texto;
    await pagina.getByRole("checkbox", { name: `Derivar da ARA: ${texto}` }).check();
  }
  await pagina.waitForTimeout(300);
  await capturar(jornada, "01-udes-escolhidos-na-ara", pagina);
  await capturar(
    jornada,
    "02-botao-derivar-armado",
    pagina.locator("div.cabecalho-do-projeto").first(),
  );

  // 2. derivar leva à Nuvem — o encadeamento INT-05, em um clique.
  await pagina.getByRole("button", { name: /^Derivar da ARA \(2\)$/ }).click();
  await pagina.getByRole("heading", { name: new RegExp(`${escapar(NOME_DA_ARA)} — nuvem`) }).waitFor({
    timeout: 25000,
  });
  await pagina.waitForTimeout(600);
  await capturar(jornada, "03-nuvem-derivada", pagina);

  // 3. a rastreabilidade: a nuvem DIZ de onde veio, com o enunciado dos UDEs de origem.
  await capturar(jornada, "04-linha-de-origem", pagina.locator("p.origem"));

  const nuvens = await api("/toc/projetos");
  const nuvem = nuvens.find((p) => p.ferramenta === "nc" && p.nome.includes("nuvem"));
  if (!nuvem) throw new Error("a nuvem derivada não apareceu na listagem");
  const detalhe = await api(`/toc/nc/projetos/${nuvem.id}`);
  if (!detalhe.origem) throw new Error("a nuvem derivada voltou SEM referência de origem");
  const esperados = UDES_DA_TRAVESSIA.map((c) => porId.get(c)).sort();
  const vieram = [...detalhe.origem.nos].sort();
  if (JSON.stringify(esperados) !== JSON.stringify(vieram)) {
    throw new Error(
      `a origem aponta para nós diferentes dos escolhidos: ${JSON.stringify(vieram)}`,
    );
  }
  log(`  · origem: projeto ${detalhe.origem.projeto_id}, ${detalhe.origem.nos.length} nós`);
  log(`  · leitura: ${detalhe.origem.leitura.slice(0, 160)}`);

  // 4. de volta à ARA: a árvore de origem continua intacta — derivar lê, não escreve.
  await pagina.getByRole("button", { name: "Voltar" }).click();
  // A lista tem AS DUAS agora — a árvore e a nuvem derivada dela. A linha da árvore é a
  // que NÃO diz "nuvem"; ancorar por fim de texto não serve, porque o nome acessível da
  // linha carrega ferramenta, data e os botões de ação.
  await linhaDoProjeto(pagina, NOME_DA_ARA, { semNuvem: true })
    .getByRole("button", { name: "Abrir" })
    .click();
  await pagina.getByRole("tab", { name: `Nós (${BASE.ara.nos.length})` }).waitFor({ timeout: 20000 });
  await capturar(jornada, "05-ara-intacta-depois-da-derivacao", pagina);

  await pagina.close();
  return { nuvemId: nuvem.id, origem: detalhe.origem };
}

// =======================================================================================
// J-03 — A Nuvem de Conflito modelada
// =======================================================================================

const PAPEL_POR_ID = { A: "A", B: "B", C: "C", D: "D", "D-linha": "D_PRIME" };
/**
 * A base escreve a aresta na direção da LEITURA causal ("B exige A"); o domínio nomeia a
 * chave pela POSIÇÃO no diagrama canônico (`A_B` é a aresta entre A e B). As sete chaves
 * são fechadas e o serviço as recusa por nome — a lista veio da própria recusa:
 * `esperado uma de ['A_B','A_C','B_D','C_D_PRIME','D_C','D_PRIME_B','D_D_PRIME']`.
 */
const CHAVE_POR_ARESTA = {
  "B->A": "A_B",
  "C->A": "A_C",
  "D->B": "B_D",
  "D-linha->C": "C_D_PRIME",
  "D->D-linha": "D_D_PRIME",
  "D->C": "D_C",
  "D-linha->B": "D_PRIME_B",
};

/** Abre a nuvem derivada a partir da lista de projetos e espera o diagrama desenhar. */
async function abrirNuvem(pagina) {
  await pagina
    .getByRole("row")
    .filter({ hasText: "nuvem" })
    .first()
    .getByRole("button", { name: "Abrir" })
    .click();
  await pagina.getByTestId("entidade-A").waitFor({ timeout: 25000 });
  await pagina.waitForTimeout(500);
}

async function jornadaNuvem(navegador, { nuvemId }) {
  log("J-03 · a Nuvem de Conflito");
  const jornada = "003-nuvem-de-conflito";

  // As cinco entidades e as sete premissas da base entram pelo serviço.
  for (const entidade of BASE.nuvem.entidades) {
    await api(`/toc/nc/projetos/${nuvemId}/entidades/${PAPEL_POR_ID[entidade.id]}`, {
      metodo: "PUT",
      corpo: { texto: entidade.texto },
    });
  }
  const premissaPorAresta = new Map();
  for (const aresta of BASE.nuvem.arestas) {
    const chave = CHAVE_POR_ARESTA[`${aresta.de}->${aresta.para}`];
    if (!chave) throw new Error(`aresta da base sem chave conhecida: ${aresta.de}->${aresta.para}`);
    const premissa = await api(`/toc/nc/projetos/${nuvemId}/arestas/${chave}/premissas`, {
      metodo: "POST",
      corpo: { texto: aresta.premissa },
    });
    premissaPorAresta.set(`${aresta.de}->${aresta.para}`, premissa.id);
  }

  const pagina = await navegador.newPage({ viewport: VIEWPORT });
  await pagina.goto(URL_AUTONOMA, { waitUntil: "networkidle" });
  await abrirNuvem(pagina);
  await pagina.waitForTimeout(500);

  // 1. o diagrama canônico: cinco entidades, SETE arestas.
  const arestas = await pagina.locator("[data-testid^='aresta-']").count();
  if (arestas !== 7) falhas.push({ jornada, captura: "—", erro: `arestas desenhadas: ${arestas}` });
  log(`  · arestas desenhadas no diagrama: ${arestas}`);
  await capturar(jornada, "01-diagrama-do-conflito", pagina);

  // 2. a ficha de uma aresta, com a premissa que a sustenta.
  await pagina.getByTestId("aresta-D_D_PRIME").click();
  await pagina.locator("section.ficha-da-aresta").waitFor({ timeout: 15000 });
  await capturar(jornada, "02-ficha-da-aresta-com-premissa", pagina.locator("section.ficha-da-aresta"));

  // 3. a injeção nasce LIGADA à premissa que invalida (RF-13).
  const injecoes = [];
  for (const injecao of BASE.nuvem.injecoes) {
    const premissaId = premissaPorAresta.get(injecao.ataca);
    if (!premissaId) throw new Error(`injeção da base sem premissa alvo: ${injecao.ataca}`);
    injecoes.push(
      await api(`/toc/nc/projetos/${nuvemId}/premissas/${premissaId}/injecoes`, {
        metodo: "POST",
        corpo: { texto: injecao.texto, separacao: "tempo" },
      }),
    );
  }
  // Recarregar volta à lista (a rota não está na URL — achado A-01 da J-02): a nuvem é
  // reaberta pela tela, como quem usa faria.
  await pagina.reload({ waitUntil: "networkidle" });
  await abrirNuvem(pagina);
  await pagina.getByTestId("aresta-D_D_PRIME").click();
  await pagina.locator("section.ficha-da-aresta").waitFor({ timeout: 15000 });
  await capturar(jornada, "03-injecao-ligada-a-premissa", pagina.locator("section.ficha-da-aresta"));
  await pagina.getByRole("button", { name: "Fechar" }).first().click();

  // 4. a visão de solução — o espelho das sete posições.
  await pagina.getByRole("radio", { name: "Solução" }).click();
  await pagina.waitForTimeout(500);
  await capturar(jornada, "04-visao-de-solucao", pagina);

  // 5. conflito e solução lado a lado.
  await pagina.getByRole("radio", { name: "Lado a lado" }).click();
  await pagina.waitForTimeout(500);
  await capturar(jornada, "05-lado-a-lado", pagina);

  // 6. a vista tabular: aresta × premissas × injeções.
  await pagina.getByRole("radio", { name: "Vista tabular" }).click();
  await pagina.waitForTimeout(500);
  await capturar(jornada, "06-vista-tabular", pagina);

  // 7. gerar NÃO aplica: a pré-visualização traz o diff e o identificador da ação.
  await pagina.getByRole("radio", { name: "Conflito" }).click();
  await pagina
    .getByLabel("Narrativa do dilema")
    .fill(
      "A coordenação precisa abrir turma para garantir receita, mas abrir sem docente titular " +
        "derruba a conclusão do semestre.",
    );
  await pagina.getByRole("button", { name: "Gerar a partir da narrativa" }).click();
  await pagina.waitForTimeout(1200);
  await capturar(jornada, "07-previa-da-geracao", pagina);

  // 8. **aceitar leva ao gate, não à escrita**: a proposta nasce no servidor e ESPERA.
  //    Medimos o estado da nuvem antes e depois para a jornada não afirmar de memória.
  const antesDaProposta = await api(`/toc/nc/projetos/${nuvemId}`);
  await pagina.getByRole("button", { name: "Aceitar" }).click();
  await pagina.locator("section.superficie-de-confirmacao").waitFor({ timeout: 20000 });
  const noGate = await api(`/toc/nc/projetos/${nuvemId}`);
  medidas.propostaNaoEscreve =
    JSON.stringify(noGate) === JSON.stringify(antesDaProposta);
  const pendente = (await api("/aph/traco")).length;
  await capturar(jornada, "08-gate-da-proposta", pagina);
  log(
    `  · proposta criada e aguardando decisão · nuvem intacta enquanto espera: ` +
      `${medidas.propostaNaoEscreve} · linhas de traço antes da decisão: ${pendente}`,
  );

  // 9. **confirmar aplica** — e a tela mostra o que releu do serviço, nunca o que ela
  //    guardou. É o laço que a 4ª geração nunca fechou pelo caminho certo.
  await pagina.getByRole("button", { name: "Confirmar e aplicar" }).click();
  await pagina.locator("p.desfecho").waitFor({ timeout: 20000 });
  await pagina.waitForTimeout(600);
  await capturar(jornada, "09-nuvem-depois-da-confirmacao", pagina);
  const depoisDaConfirmacao = await api(`/toc/nc/projetos/${nuvemId}`);
  const traco = await api("/aph/traco");
  const daGeracao = traco.filter((t) => t.action_id === "toc.generate_conflict_cloud");
  medidas.geracaoAplicada = {
    entidades_reescritas: depoisDaConfirmacao.entidades.filter(
      (e, i) => e.texto !== antesDaProposta.entidades[i].texto,
    ).length,
    premissas_antes: antesDaProposta.arestas.reduce((n, a) => n + a.premissas.length, 0),
    premissas_depois: depoisDaConfirmacao.arestas.reduce((n, a) => n + a.premissas.length, 0),
    traco: daGeracao.map((t) => t.desfecho),
  };
  log(
    `  · confirmada: ${medidas.geracaoAplicada.entidades_reescritas} de 5 entidades reescritas` +
      ` · premissas ${medidas.geracaoAplicada.premissas_antes} → ${medidas.geracaoAplicada.premissas_depois}` +
      ` · traço da ação: ${JSON.stringify(medidas.geracaoAplicada.traco)}`,
  );
  if (medidas.geracaoAplicada.entidades_reescritas === 0) {
    falhas.push({ jornada, captura: "09", erro: "confirmar não mudou a nuvem" });
  }

  // 10. e a mudança **sobrevive à recarga**: a tela é recarregada e a nuvem é reaberta do
  //     serviço, sem estado de tela nenhum atravessando a fronteira.
  await pagina.reload({ waitUntil: "networkidle" });
  await abrirNuvem(pagina);
  await capturar(jornada, "10-sobrevive-a-recarga", pagina);

  const validacao = await api(`/toc/nc/projetos/${nuvemId}/validacao`);
  log(
    `  · completude: ${validacao.completude.sustentadas} de ${validacao.completude.total} arestas com premissa` +
      ` · injeções criadas: ${injecoes.length}`,
  );

  await pagina.close();
}

// =======================================================================================
// J-02b — a exclusão reversível e a lixeira (fecha a jornada do projeto)
// =======================================================================================

async function jornadaLixeira(navegador) {
  log("J-02 · exclusão reversível e lixeira");
  const jornada = "002-primeiro-projeto-e-ara";
  const pagina = await navegador.newPage({ viewport: VIEWPORT });
  await pagina.goto(URL_AUTONOMA, { waitUntil: "networkidle" });

  // O projeto descartável existe para a exclusão ser narrada sem destruir a análise.
  await pagina.getByLabel("Nome", { exact: true }).fill("Rascunho descartável da oficina");
  await pagina.getByRole("button", { name: "Criar projeto" }).click();
  const linha = pagina.getByRole("row", { name: /Rascunho descartável da oficina/ });
  await linha.waitFor({ timeout: 20000 });
  await linha.getByRole("button", { name: "Excluir" }).click();
  await pagina.getByRole("dialog").waitFor({ timeout: 10000 });
  await capturar(jornada, "15-exclusao-nomeia-o-projeto", pagina);
  await pagina.getByRole("button", { name: "Confirmar" }).click();
  await pagina.waitForTimeout(800);

  await pagina.getByRole("button", { name: "Lixeira" }).click();
  await pagina.getByRole("heading", { name: "Lixeira" }).waitFor({ timeout: 15000 });
  await pagina.waitForTimeout(400);
  await capturar(jornada, "16-lixeira-com-restaurar", pagina);
  await pagina.close();
}

// =======================================================================================

async function principal() {
  const inicio = Date.now();
  log(`capturar-telas.mjs · ${new Date().toISOString()}`);
  log(`  serviço: ${API} · base sintética: analise-horizonte.json v${BASE.versao}`);

  const comum = {
    VITE_GHD_HOST_BASE_URL: `${URL_HOSPEDEIRO}/api`,
    VITE_GHD_APP_ID: "toc-federada",
  };
  // O hospedeiro sobe PRIMEIRO: é ele quem responde a introspecção que o serviço chama.
  subirHospedeiro();
  subirServico();
  await esperarPorta(URL_HOSPEDEIRO, "o hospedeiro de bancada");
  await esperarPorta(`${API}/saude`, "o serviço toc-api", 60);
  const saude = await (await fetch(`${API}/saude`)).json();
  log(`  /saude: admissão ${saude.admissao} · persistência ${saude.persistencia} · identidade ${saude.identidade}`);
  medidas.saude = saude;
  if (saude.admissao !== "admitida") {
    throw new Error(`o serviço subiu sem admissão (${saude.admissao}); J-01 não teria o que capturar`);
  }

  if (ZERAR) {
    zerarBanco();
    log("  banco de desenvolvimento zerado (TRUNCATE … CASCADE)");
  }

  // A limpeza é TOTAL só na corrida total. Com `--jornada`, apagar a pasta inteira levaria
  // junto as capturas das jornadas que esta corrida não vai gerar, e o `check-jornadas.sh`
  // reprovaria por imagem citada e inexistente — que foi exatamente o que aconteceu na
  // primeira tentativa de regenerar a J-03 sozinha. Numa corrida parcial, as capturas são
  // sobrescritas pelo nome; captura órfã que sobre é justamente o que a invariante J1 pega.
  if (!SO_A_JORNADA) {
    rmSync(CAPTURAS, { recursive: true, force: true });
  }
  mkdirSync(CAPTURAS, { recursive: true });

  subirVite(
    PORTA_AUTONOMA,
    {
      ...comum,
      TOC_TOKEN_DEV: TOKEN_DEV,
      VITE_GHD_HOST_ORIGIN: URL_HOSPEDEIRO,
      VITE_GHD_EMBED_URL: `${URL_AUTONOMA}/?embarcado=1`,
    },
    "autônoma",
  );
  // A embarcada NÃO recebe `TOC_TOKEN_DEV`: a identidade dela tem de vir do handshake.
  subirVite(
    PORTA_EMBARCADA,
    { ...comum, VITE_GHD_HOST_ORIGIN: URL_HOSPEDEIRO, VITE_GHD_EMBED_URL: `${URL_EMBARCADA}/?embarcado=1` },
    "embarcada",
  );
  // A recusada tem três dos quatro parâmetros: falta `VITE_GHD_EMBED_URL` (§B.4.1).
  subirVite(PORTA_RECUSADA, { ...comum, VITE_GHD_HOST_ORIGIN: URL_HOSPEDEIRO }, "recusada");

  await esperarPorta(URL_AUTONOMA, "a interface autônoma");
  await esperarPorta(URL_EMBARCADA, "a interface embarcada");
  await esperarPorta(URL_RECUSADA, "a interface sem admissão");

  const { chromium } = await carregarPlaywright();
  const navegador = await chromium.launch();

  try {
    const quer = (j) => !SO_A_JORNADA || SO_A_JORNADA === j;
    if (quer("J-01")) await jornadaChegadaEEmbarque(navegador);

    // J-02 → J-07 → J-03 correm em sequência DE PROPÓSITO: é a mesma pessoa, na mesma
    // sessão, e a nuvem da J-03 é a que a travessia derivou. Pedir uma delas sozinha
    // (`--jornada J-03`) não funciona sem a anterior, e isso é a costura, não um defeito.
    if (quer("J-02") || quer("J-07") || quer("J-03")) {
      const ara = await jornadaAra(navegador);
      const travessia = await jornadaTravessia(navegador, ara);
      await jornadaNuvem(navegador, travessia);
      await jornadaLixeira(navegador);
    }
  } finally {
    await navegador.close();
    derrubarTudo();
  }

  const manifesto = {
    gerado_em: new Date().toISOString(),
    script: "docs/jornadas/scripts/capturar-telas.mjs",
    base_sintetica: `docs/produto/dados/analise-horizonte.json v${BASE.versao}`,
    capturas: registro.length,
    bytes: registro.reduce((s, r) => s + r.bytes, 0),
    medidas,
    falhas,
    itens: registro,
  };
  writeFileSync(join(CAPTURAS, "manifesto.json"), `${JSON.stringify(manifesto, null, 2)}\n`);

  const segundos = ((Date.now() - inicio) / 1000).toFixed(1);
  log("");
  log(`${registro.length} captura(s), ${manifesto.bytes} bytes, ${falhas.length} falha(s), ${segundos}s`);
  for (const f of falhas) log(`  FALHA ${f.jornada} ${f.captura}: ${f.erro}`);
  return falhas.length === 0 ? 0 : 1;
}

principal()
  .then((codigo) => process.exit(codigo))
  .catch((erro) => {
    derrubarTudo();
    log(`ERRO FATAL: ${erro && erro.stack ? erro.stack : erro}`);
    process.exit(2);
  });
