/**
 * O ponto de entrada. Tudo o que vem do mundo é lido AQUI e passado para dentro:
 * ambiente de configuração, URL (Uniform Resource Locator), janela pai e função de envio.
 *
 * O tema claro/escuro segue **a preferência do sistema em modo autônomo** e os tokens do
 * hospedeiro quando embarcada (RI-08 da spec 002) — nunca um seletor próprio que brigue
 * com o de quem hospeda.
 */
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { App } from "./App";
import "./estilos.css";

const raiz = document.getElementById("raiz");
if (!raiz) throw new Error("elemento #raiz ausente no index.html");

const prefereEscuro =
  typeof window.matchMedia === "function" &&
  window.matchMedia("(prefers-color-scheme: dark)").matches;

createRoot(raiz).render(
  <StrictMode>
    <App
      ambiente={import.meta.env as unknown as Record<string, string | undefined>}
      url={window.location.href}
      pai={window.parent}
      // §B.2.4: `targetOrigin` dirigido. Quem o escolhe é a configuração de admissão, e o
      // módulo de federação recusa emitir sem ela — por isso aqui só se repassa.
      enviar={(mensagem, destino) => window.parent.postMessage(mensagem, destino)}
      esquemaPreferido={prefereEscuro ? "escuro" : "claro"}
    />
  </StrictMode>,
);
