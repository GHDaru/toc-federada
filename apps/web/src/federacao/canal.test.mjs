// Testes do canal `ghd.*` — os três defeitos que a norma registrou, cada um recusado.
//
// Siglas, uma vez: APH — Aplicação ↔ Harness · URL — Uniform Resource Locator ·
// CSS — Cascading Style Sheets.
//
// Rodam com `node --test`, sem instalar nada: `node --test apps/web/src/federacao/`.
// O portão é `scripts/check-canal.sh`.

import { test } from "node:test";
import assert from "node:assert/strict";

import {
  DESCARTES,
  JANELA_DO_HANDSHAKE_MS,
  avaliarMensagem,
  criarCanal,
  envelope,
  envelopeValido,
  modoDeEmbarque,
  resolverTema,
} from "./canal.mjs";

const HOST = "https://plataforma.exemplo";
const PAI = { nome: "janela-pai" };

const evento = (extra = {}) => ({
  source: PAI,
  origin: HOST,
  data: envelope("ghd.handshake", { token: "ghdg_sintetico" }),
  ...extra,
});

// -- envelope (§B.2.1, RF-14..RF-17) ---------------------------------------------------

test("o envelope emitido tem exatamente os quatro campos canônicos", () => {
  const e = envelope("ghd.ready", { app_id: "toc" });
  assert.deepEqual(Object.keys(e).sort(), ["payload", "protocol", "type", "v"]);
  assert.equal(e.protocol, "ghd");
  assert.equal(e.v, 1);
});

test("o envelope da aplicação irmã é recusado — é o contraexemplo [F-02] da norma", () => {
  // `prototipo/adaptadores.js:129` da `gestaodeprioridades`: {tipo, versao, payload}.
  assert.equal(envelopeValido({ tipo: "ghd.ready", versao: 1, payload: {} }), false);
});

test("campo a mais no envelope é recusado; campo a mais no payload é aceito", () => {
  assert.equal(envelopeValido({ ...envelope("ghd.handshake"), extra: 1 }), false);
  assert.equal(envelopeValido(envelope("ghd.handshake", { token: "x", novidade: 1 })), true);
});

test("versão de canal como texto não passa — `v` é inteiro e ordena", () => {
  assert.equal(envelopeValido({ protocol: "ghd", v: "1", type: "ghd.handshake", payload: {} }), false);
});

// -- trava dupla (§B.2.3, RF-20..RF-22) ------------------------------------------------

test("mensagem do pai admitido com a origem admitida é aceita", () => {
  const r = avaliarMensagem(evento(), { hostOrigin: HOST, pai: PAI });
  assert.equal(r.admitida, true);
  assert.equal(r.mensagem.type, "ghd.handshake");
});

test("fonte diferente de window.parent é descartada — o defeito [F-05], que não existia lá", () => {
  const r = avaliarMensagem(evento({ source: { outro: true } }), { hostOrigin: HOST, pai: PAI });
  assert.equal(r.admitida, false);
  assert.equal(r.motivo, DESCARTES.FONTE_NAO_ADMITIDA);
});

test("origem diferente da configurada é descartada", () => {
  const r = avaliarMensagem(evento({ origin: "https://atacante.exemplo" }), { hostOrigin: HOST, pai: PAI });
  assert.equal(r.motivo, DESCARTES.ORIGEM_NAO_ADMITIDA);
});

test('origem "null" nunca é admitida, nem quando a configurada também é "null"', () => {
  assert.equal(
    avaliarMensagem(evento({ origin: "null" }), { hostOrigin: HOST, pai: PAI }).motivo,
    DESCARTES.ORIGEM_NAO_ADMITIDA,
  );
  assert.equal(
    avaliarMensagem(evento({ origin: "null" }), { hostOrigin: "null", pai: PAI }).motivo,
    DESCARTES.ORIGEM_NAO_ADMITIDA,
  );
});

test("a origem esperada nunca sai do payload — o contraexemplo circular [F-06]", () => {
  const hostil = evento({
    origin: "https://atacante.exemplo",
    data: envelope("ghd.handshake", { host_origin: "https://atacante.exemplo" }),
  });
  assert.equal(avaliarMensagem(hostil, { hostOrigin: HOST, pai: PAI }).admitida, false);
});

test("sem origem configurada nada é admitido — conferir contra undefined passaria", () => {
  assert.equal(avaliarMensagem(evento(), { hostOrigin: undefined, pai: PAI }).admitida, false);
});

test("a fonte é conferida ANTES da origem — a ordem do §B.2.3", () => {
  const errado = evento({ source: { outro: true }, origin: "https://atacante.exemplo" });
  assert.equal(avaliarMensagem(errado, { hostOrigin: HOST, pai: PAI }).motivo, DESCARTES.FONTE_NAO_ADMITIDA);
});

test("tipo desconhecido em envelope válido é ignorado, sem efeito", () => {
  const novo = evento({ data: envelope("ghd.tipo_do_futuro", {}) });
  assert.equal(avaliarMensagem(novo, { hostOrigin: HOST, pai: PAI }).motivo, DESCARTES.TIPO_DESCONHECIDO);
});

// -- o canal: fala primeiro, dirigido, e não responde ao descarte -----------------------

test("ghd.ready é o primeiro, com {app_id}, e com targetOrigin dirigido — nunca `*`", () => {
  const enviados = [];
  const canal = criarCanal({
    hostOrigin: HOST,
    appId: "toc",
    pai: PAI,
    enviar: (msg, alvo) => enviados.push([msg, alvo]),
  });

  canal.anunciarPronto();

  assert.equal(enviados.length, 1);
  const [mensagem, alvo] = enviados[0];
  assert.equal(mensagem.type, "ghd.ready");
  assert.deepEqual(mensagem.payload, { app_id: "toc" });
  assert.equal(alvo, HOST);
  assert.notEqual(alvo, "*"); // o defeito [F-04] da irmã, recusado por teste
});

test("mensagem descartada não gera resposta e vira registro sem payload", () => {
  const enviados = [];
  const registrados = [];
  const canal = criarCanal({
    hostOrigin: HOST,
    appId: "toc",
    pai: PAI,
    enviar: (msg, alvo) => enviados.push([msg, alvo]),
    registrar: (r) => registrados.push(r),
  });

  const resultado = canal.aoReceber(evento({ origin: "https://atacante.exemplo" }));

  assert.equal(resultado, null);
  assert.equal(enviados.length, 0, "responder já confirma presença (§B.2.1)");
  assert.equal(registrados.length, 1);
  assert.equal(registrados[0].motivo, DESCARTES.ORIGEM_NAO_ADMITIDA);
  assert.equal("payload" in registrados[0], false, "o payload do descarte nunca é registrado");
  assert.equal(canal.descartes.length, 1);
});

test("o handshake admitido volta como dado, e é só isso que ele é", () => {
  const canal = criarCanal({ hostOrigin: HOST, appId: "toc", pai: PAI, enviar: () => {} });
  const mensagem = canal.aoReceber(evento());
  assert.equal(mensagem.type, "ghd.handshake");
  assert.equal(mensagem.payload.token, "ghdg_sintetico");
});

// -- tema (§B.4.3, RF-26) ---------------------------------------------------------------

const PERMITIDOS = ["color-primary", "color-surface", "color-text", "color-danger"];
const PROPRIO = {
  "color-primary": "#1d4ed8",
  "color-surface": "#ffffff",
  "color-text": "#111827",
  "color-danger": "#b91c1c",
};

test("token parcial do inquilino é aplicado e o resto cai no tema próprio", () => {
  const { resolvido, usados } = resolverTema({ "color-primary": "#008060" }, PERMITIDOS, PROPRIO);
  assert.equal(resolvido["color-primary"], "#008060");
  assert.equal(resolvido["color-surface"], PROPRIO["color-surface"]);
  assert.deepEqual(usados, ["color-primary"]);
  for (const nome of PERMITIDOS) assert.ok(resolvido[nome], `${nome} sem cor definida`);
});

test("token fora da lista de permissão é ignorado e declarado", () => {
  const { resolvido, ignorados } = resolverTema(
    { "color-primary": "#008060", "font-family-secreta": "x" },
    PERMITIDOS,
    PROPRIO,
  );
  assert.equal("font-family-secreta" in resolvido, false);
  assert.deepEqual(ignorados, ["font-family-secreta"]);
});

test("tema sem handshake nenhum ainda cobre todos os tokens", () => {
  const { resolvido, usados } = resolverTema(undefined, PERMITIDOS, PROPRIO);
  assert.deepEqual(usados, []);
  for (const nome of PERMITIDOS) assert.ok(resolvido[nome]);
});

test("fallback incompleto é erro de construção, não elemento sem cor em produção", () => {
  assert.throws(() => resolverTema({}, PERMITIDOS, { "color-primary": "#000" }), /fallback/);
});

// -- modo embarcado (§B.8.2, RF-24) -----------------------------------------------------

test("o modo vem do sinal explícito da URL, nunca de heurística de window.parent", () => {
  assert.equal(modoDeEmbarque("https://toc.exemplo/toc/embarcado?embarcado=1"), "embarcado");
  assert.equal(modoDeEmbarque("https://toc.exemplo/toc/embarcado"), "autonomo");
  assert.equal(modoDeEmbarque("nao-e-url"), "autonomo");
});

test("a janela do handshake é a do laboratório (§B.3.2)", () => {
  assert.equal(JANELA_DO_HANDSHAKE_MS, 6000);
});
