// varredura.mjs — os dois números do portão de internacionalização (spec 011, E8.3).
//
// Siglas, uma vez neste arquivo: **i18n** — internacionalização · **JSX** — JavaScript
// XML (a sintaxe de marcação do React) · **TS** — TypeScript · **RF** — requisito
// funcional da spec 011 · **CI** — integração contínua.
//
// ── O defeito que este arquivo existe para não deixar voltar ────────────────────────
//
// A quarta geração da linhagem gastou DUAS das suas cinco especificações de
// funcionalidade traduzindo telas que já existiam
// (`tocbuilderv3/specs/feat_internationalization_full.md` e
// `feat_internationalization_final_steps.md`, ambas de 2024-08-02) — e mesmo assim ficou
// com literais em português vivos no código de produção:
// `tocbuilderv3/components/SnTView.tsx:182` (`Criar Novo Projeto S&T`) e
// `SnTStepEditorModal.tsx:92,95` (`Cancelar`, `Salvar`). Vinte e cinco dos cinquenta e um
// arquivos `.tsx` daquela geração nunca importaram o mecanismo de i18n.
//
// Não faltava disciplina: faltava **portão**. A dívida de tradução é invisível — a tela
// funciona, o texto aparece, e só quem troca o idioma descobre. É por isso que ela cresce
// em silêncio, e é por isso que este arquivo mede duas coisas e imprime os dois
// denominadores (regra R2 do `CLAUDE.md`).
//
// ── Como ele mede, e por que com o compilador e não com `grep` ──────────────────────
//
// Um `grep` por texto entre `>` e `<` acha `Promise<unknown>` e não acha
// `title={"Salvar"}`. Aqui a varredura usa o **próprio compilador do TypeScript** (já
// instalado em `apps/web/node_modules`): o arquivo é analisado, e o que conta como cadeia
// visível é o nó de texto JSX e o literal em atributo que o navegador mostra
// (`title`, `placeholder`, `alt`, `aria-label`…). Zero falso positivo por generic, zero
// falso negativo por atributo.
//
// Uso:  node scripts/i18n/varredura.mjs [raiz]
// Saída: relatório em texto. Código: 0 conforme · 1 violação · 2 ambiente não montado.

import { readFileSync, existsSync, readdirSync, statSync } from "node:fs";
import { join, relative, dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { createRequire } from "node:module";

const AQUI = dirname(fileURLToPath(import.meta.url));
const RAIZ_DO_REPO = resolve(AQUI, "..", "..");
const RAIZ = resolve(process.argv[2] ?? RAIZ_DO_REPO);

// O compilador vem SEMPRE do repositório de verdade, nunca da árvore examinada: a
// sabotagem copia uma cópia mínima do repositório para um diretório temporário, e ela não
// tem `node_modules`. Um portão que só roda dentro do próprio repositório não pode ser
// sabotado — e portão que não pode ser sabotado não é portão.
const require = createRequire(join(RAIZ_DO_REPO, "scripts", "i18n", "varredura.mjs"));
let ts;
try {
  ts = require(join(RAIZ_DO_REPO, "apps", "web", "node_modules", "typescript"));
} catch (erro) {
  console.error(`✗ TypeScript não encontrado em apps/web/node_modules: ${erro.message}`);
  process.exit(2);
}

const FONTE = join(RAIZ, "apps", "web", "src");
const DICIONARIOS = { pt: join(FONTE, "i18n", "pt.ts"), en: join(FONTE, "i18n", "en.ts") };
const MECANISMO = join(FONTE, "i18n", "index.tsx");
const EXCECOES = join(RAIZ, "scripts", "i18n", "excecoes.txt");

/** Atributos cujo valor o navegador MOSTRA (ou lê em voz alta) para a pessoa. */
const ATRIBUTOS_VISIVEIS = new Set([
  "title",
  "placeholder",
  "alt",
  "label",
  "aria-label",
  "aria-description",
  "aria-placeholder",
  "aria-valuetext",
  "aria-roledescription",
]);

/** Cadeia que não é texto de gente: só pontuação, só número, só símbolo. */
function pareceTextoDeGente(texto) {
  const limpo = texto.trim();
  if (limpo.length < 2) return false;
  // Precisa de ao menos duas letras seguidas — "×", "3", "…", "R$" não são frase.
  return /\p{L}{2}/u.test(limpo);
}

function arquivos(diretorio, achados = []) {
  if (!existsSync(diretorio)) return achados;
  for (const nome of readdirSync(diretorio).sort()) {
    const caminho = join(diretorio, nome);
    if (statSync(caminho).isDirectory()) {
      if (nome === "node_modules" || nome === "testes") continue;
      arquivos(caminho, achados);
      continue;
    }
    if (!nome.endsWith(".tsx")) continue;
    if (nome.includes(".test.")) continue;
    achados.push(caminho);
  }
  return achados;
}

function lerExcecoes() {
  if (!existsSync(EXCECOES)) return { entradas: [], semMotivo: [] };
  const entradas = [];
  const semMotivo = [];
  const linhas = readFileSync(EXCECOES, "utf8").split("\n");
  linhas.forEach((linha, indice) => {
    const cru = linha.trim();
    if (!cru || cru.startsWith("#")) return;
    const [alvo, motivo] = cru.split(/\s+#\s+/);
    const [arquivo, texto] = (alvo ?? "").split("::");
    if (!arquivo || texto === undefined || !motivo || motivo.trim().length < 15) {
      semMotivo.push({ linha: indice + 1, cru });
      return;
    }
    entradas.push({ arquivo: arquivo.trim(), texto: texto.trim(), motivo: motivo.trim() });
  });
  return { entradas, semMotivo };
}

function varrerLiterais() {
  const alvos = arquivos(FONTE);
  const { entradas, semMotivo } = lerExcecoes();
  const achados = [];
  const usadas = new Set();
  let cadeias = 0;
  let pelaTraducao = 0;

  for (const caminho of alvos) {
    const codigo = readFileSync(caminho, "utf8");
    const fonte = ts.createSourceFile(caminho, codigo, ts.ScriptTarget.Latest, true, ts.ScriptKind.TSX);
    const curto = relative(RAIZ, caminho);

    const registrar = (texto, no, motivo) => {
      cadeias += 1;
      if (!pareceTextoDeGente(texto)) return;
      const excecao = entradas.find((e) => e.arquivo === curto && e.texto === texto.trim());
      if (excecao) {
        usadas.add(`${excecao.arquivo}::${excecao.texto}`);
        return;
      }
      const { line } = fonte.getLineAndCharacterOfPosition(no.getStart(fonte));
      achados.push({ arquivo: curto, linha: line + 1, texto: texto.trim(), motivo });
    };

    const visitar = (no) => {
      // As chamadas ao dicionário entram no denominador: sem elas, "64 cadeias
      // examinadas" não diz se a tela tem 64 textos ou 600. O número que interessa a quem
      // lê o portão é a RAZÃO entre o que passa pelo dicionário e o que ficou solto.
      if (
        ts.isCallExpression(no) &&
        ts.isIdentifier(no.expression) &&
        (no.expression.text === "t" || no.expression.text === "tc")
      ) {
        pelaTraducao += 1;
      }
      if (ts.isJsxText(no)) {
        if (no.text.trim()) registrar(no.text, no, "texto solto dentro do JSX");
      } else if (ts.isJsxAttribute(no) && ATRIBUTOS_VISIVEIS.has(no.name.getText(fonte))) {
        const valor = no.initializer;
        if (valor && ts.isStringLiteral(valor)) {
          registrar(valor.text, valor, `atributo visível \`${no.name.getText(fonte)}\``);
        } else if (
          valor &&
          ts.isJsxExpression(valor) &&
          valor.expression &&
          ts.isStringLiteral(valor.expression)
        ) {
          registrar(
            valor.expression.text,
            valor.expression,
            `atributo visível \`${no.name.getText(fonte)}\``,
          );
        }
      }
      ts.forEachChild(no, visitar);
    };
    visitar(fonte);
  }

  const orfas = entradas.filter((e) => !usadas.has(`${e.arquivo}::${e.texto}`));
  return { alvos, cadeias, pelaTraducao, achados, entradas, semMotivo, orfas };
}

/** As folhas de um dicionário TypeScript, lidas do próprio código-fonte. */
function chavesDoDicionario(caminho) {
  const codigo = readFileSync(caminho, "utf8");
  const fonte = ts.createSourceFile(caminho, codigo, ts.ScriptTarget.Latest, true, ts.ScriptKind.TS);
  const chaves = [];
  const vazias = [];

  const nomeDa = (propriedade) => {
    const nome = propriedade.name;
    if (ts.isIdentifier(nome) || ts.isStringLiteral(nome)) return nome.text;
    return null;
  };

  const descer = (objeto, prefixo) => {
    for (const propriedade of objeto.properties) {
      if (!ts.isPropertyAssignment(propriedade)) continue;
      const nome = nomeDa(propriedade);
      if (nome === null) continue;
      const caminhoDaChave = prefixo ? `${prefixo}.${nome}` : nome;
      const valor = propriedade.initializer;
      if (ts.isObjectLiteralExpression(valor)) {
        descer(valor, caminhoDaChave);
      } else if (ts.isStringLiteral(valor) || ts.isNoSubstitutionTemplateLiteral(valor)) {
        chaves.push(caminhoDaChave);
        if (!valor.text.trim()) vazias.push(caminhoDaChave);
      } else {
        chaves.push(caminhoDaChave);
      }
    }
  };

  let raiz = null;
  const visitar = (no) => {
    if (ts.isVariableDeclaration(no) && no.initializer) {
      let valor = no.initializer;
      if (ts.isAsExpression(valor) || ts.isSatisfiesExpression?.(valor)) valor = valor.expression;
      if (ts.isObjectLiteralExpression(valor) && raiz === null) raiz = valor;
    }
    ts.forEachChild(no, visitar);
  };
  visitar(fonte);
  if (raiz === null) return { chaves: [], vazias: [] };
  descer(raiz, "");
  return { chaves, vazias };
}

function conferirMecanismo() {
  if (!existsSync(MECANISMO)) return ["o mecanismo de i18n não existe em apps/web/src/i18n/"];
  const codigo = readFileSync(MECANISMO, "utf8");
  const faltando = [];
  if (!/throw new ChaveDeTraducaoAusente/.test(codigo)) {
    faltando.push(
      "o mecanismo não LANÇA em chave ausente (RF-09) — é o `translation || key` da linhagem de volta",
    );
  }
  if (!/opcoes\.fonte|fonte:/.test(codigo) || !/i18n\.chave_ausente/.test(codigo)) {
    faltando.push(
      "o mecanismo não cai para a língua-fonte com registro em produção (RF-10)",
    );
  }
  if (/return chave;/.test(codigo)) {
    faltando.push("o mecanismo devolve a CHAVE CRUA em algum caminho (RF-09, defeito F-12)");
  }
  return faltando;
}

// ── execução ────────────────────────────────────────────────────────────────────────
if (!existsSync(FONTE)) {
  console.error(`✗ ${relative(RAIZ, FONTE)} não existe — a interface não está neste repositório.`);
  process.exit(2);
}
for (const [idioma, caminho] of Object.entries(DICIONARIOS)) {
  if (!existsSync(caminho)) {
    console.error(`✗ dicionário ${idioma} ausente: ${relative(RAIZ, caminho)}`);
    process.exit(2);
  }
}

let falhou = 0;
console.log("── Internacionalização: paridade e literal órfão (E8.3, spec 011) ──");

// 1. literal órfão
const literais = varrerLiterais();
console.log(`  arquivos .tsx varridos: ${literais.alvos.length}`);
console.log(`  cadeias examinadas: ${literais.cadeias} candidatas a literal solto`);
console.log(`  cadeias pelo dicionário: ${literais.pelaTraducao} chamadas a t()/tc()`);
console.log(`  exceções declaradas: ${literais.entradas.length} (todas exigem motivo escrito)`);
if (literais.semMotivo.length) {
  falhou = 1;
  console.error("✗ exceção sem motivo no scripts/i18n/excecoes.txt:");
  for (const { linha, cru } of literais.semMotivo) {
    console.error(`    linha ${linha}: ${cru}`);
  }
  console.error(
    "  Formato: `<caminho>::<texto> # <motivo com ao menos 15 caracteres>`. Uma lista de",
  );
  console.error("  exceções sem motivo é exatamente como um portão passa a mentir.");
}
if (literais.orfas.length) {
  falhou = 1;
  console.error("✗ exceção que não corresponde a literal nenhum (limpe a lista):");
  for (const e of literais.orfas) console.error(`    ${e.arquivo}::${e.texto}`);
}
if (literais.achados.length) {
  falhou = 1;
  console.error(`✗ ${literais.achados.length} literal(is) visível(is) fora do dicionário:`);
  for (const a of literais.achados) {
    console.error(`    ${a.arquivo}:${a.linha}  ${JSON.stringify(a.texto)}  (${a.motivo})`);
  }
  console.error("  O caminho é `t(\"<chave>\")` com a chave nos DOIS dicionários.");
} else {
  console.log("  ✓ nenhuma cadeia visível fora do dicionário");
}

// 2. paridade dos dicionários
const pt = chavesDoDicionario(DICIONARIOS.pt);
const en = chavesDoDicionario(DICIONARIOS.en);
const conjuntoPt = new Set(pt.chaves);
const conjuntoEn = new Set(en.chaves);
const pendencias = pt.chaves.filter((c) => !conjuntoEn.has(c)).sort();
const orfas = en.chaves.filter((c) => !conjuntoPt.has(c)).sort();
console.log(`  chaves em pt (língua-fonte): ${pt.chaves.length}`);
console.log(`  chaves em en (tradução): ${en.chaves.length}`);
console.log(`  pendências de tradução (só em pt): ${pendencias.length}`);
console.log(`  chaves órfãs (só em en): ${orfas.length}`);
console.log(`  traduções vazias: ${pt.vazias.length + en.vazias.length}`);

if (pendencias.length) {
  falhou = 1;
  console.error("✗ chave da língua-fonte sem tradução (RF-08 — pendência não declarada):");
  for (const c of pendencias) console.error(`    ${c}`);
}
if (orfas.length) {
  falhou = 1;
  console.error("✗ chave só na tradução — é ERRO, não pendência (RF-08):");
  for (const c of orfas) console.error(`    ${c}`);
  console.error("  A língua-fonte é o português: toda chave existe primeiro nela (RN-01).");
}
if (pt.vazias.length + en.vazias.length) {
  falhou = 1;
  console.error(`✗ tradução vazia: ${[...pt.vazias, ...en.vazias].join(", ")}`);
}

// 3. a chave ausente falha alto
const faltando = conferirMecanismo();
if (faltando.length) {
  falhou = 1;
  console.error("✗ o mecanismo de i18n não cumpre o RF-09/RF-10:");
  for (const f of faltando) console.error(`    ${f}`);
} else {
  console.log("  ✓ chave ausente lança em desenvolvimento e cai para a língua-fonte em produção");
}

console.log("");
if (falhou) {
  console.error("✗ portão de internacionalização vermelho.");
  process.exit(1);
}
console.log(
  `✓ i18n conforme: ${literais.alvos.length} arquivos, ${literais.cadeias} cadeias examinadas ` +
    `(${literais.pelaTraducao} pelo dicionário), ` +
    `${pt.chaves.length} chaves pt × ${en.chaves.length} chaves en, 0 pendência, 0 órfã.`,
);
