/// <reference types="vitest/config" />
import process from "node:process";
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// O destino do serviço em desenvolvimento. Fica em variável de ambiente do BUILD, nunca
// em segredo no cliente (P7): é uma URL (Uniform Resource Locator) pública, e a única
// coisa que o navegador precisa saber para falar com a nossa própria interface de
// programação de aplicações (API).
const SERVICO = process.env.TOC_API_URL || "http://127.0.0.1:8000";

/**
 * Identidade de DESENVOLVIMENTO, e ela nunca entra no pacote (P7).
 *
 * O serviço exige `Authorization: Bearer <sessão>` em toda rota de conteúdo; a sessão real
 * nasce do handshake do hospedeiro (`POST /toc/embarque`). Fora do embarque não há
 * hospedeiro, e a alternativa preguiçosa — pôr um token no `.env` da interface — seria
 * credencial no cliente, que é exatamente o que o P7 proíbe e o que a linhagem fazia
 * (`tocbuilderv3/services/geminiService.ts:16`).
 *
 * A saída é o token viver **no processo do servidor de desenvolvimento** e ser injetado
 * pelo proxy: ele não é servido ao navegador, não entra em `import.meta.env` (nem tem
 * prefixo `VITE_`) e não existe no `vite build`. A persona é fictícia (ADR 0006).
 */
const TOKEN_DE_DESENVOLVIMENTO = process.env.TOC_TOKEN_DEV || "";

function injetarIdentidadeDeDesenvolvimento(proxy: {
  on(evento: "proxyReq", ouvinte: (pedido: { setHeader(nome: string, valor: string): void }) => void): void;
}) {
  if (!TOKEN_DE_DESENVOLVIMENTO) return;
  proxy.on("proxyReq", (pedido) => {
    pedido.setHeader("authorization", `Bearer ${TOKEN_DE_DESENVOLVIMENTO}`);
  });
}

export default defineConfig({
  plugins: [react()],
  server: {
    // As três raízes do serviço atravessam o servidor de desenvolvimento por proxy, para
    // a interface falar com a MESMA origem em desenvolvimento e em produção — o que
    // remove a classe inteira de bug "funciona no dev, quebra no build" por CORS
    // (Cross-Origin Resource Sharing).
    proxy: {
      "/toc": { target: SERVICO, changeOrigin: true, configure: injetarIdentidadeDeDesenvolvimento },
      "/aph": { target: SERVICO, changeOrigin: true, configure: injetarIdentidadeDeDesenvolvimento },
      "/saude": { target: SERVICO, changeOrigin: true },
    },
  },
  test: {
    globals: true,
    environment: "jsdom",
    setupFiles: ["./vitest.setup.ts"],
    // `canal.mjs` é testado por `node --test` (scripts/check-canal.sh) e usa `node:test`.
    // Incluí-lo aqui faria o Vitest tentar rodar um arquivo que não é dele — e um portão
    // que quebra por colisão de corredor é ruído, não evidência.
    include: ["src/**/*.test.ts", "src/**/*.test.tsx"],
    coverage: { include: ["src/**/*.{ts,tsx}"], exclude: ["src/**/*.test.*"] },
  },
});
