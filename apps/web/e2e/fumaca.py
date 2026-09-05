#!/usr/bin/env python3
"""Prova de fumaça da interface contra o serviço REAL — não contra um duplo.

Siglas, uma vez: **ARA** — Árvore da Realidade Atual · **API** — interface de programação
de aplicações · **UDE** — Efeito Indesejável.

Por que existe: a suíte de Vitest exercita a interface com um cliente falso, o que prova a
lógica da tela e nada sobre a junta. Este roteiro sobe o navegador de verdade contra a
interface de verdade falando com o `toc-api` de verdade sobre o PostgreSQL de verdade — e
a asserção que importa é a que a 4ª geração da linhagem nunca pôde fazer: **o que foi
criado continua lá depois de recarregar a página**, porque quem guarda é o banco, e não um
mapa em memória do navegador (`tocbuilderv3/services/mockApiService.ts`).

Como rodar (o navegador já está instalado; NÃO rode `playwright install`):

    # 1. serviço
    cd apps/api && DATABASE_URL=... TOC_AMBIENTE=desenvolvimento \
        .venv/bin/uvicorn --factory toc_api.http.app:criar_app --port 8000 &
    # 2. interface. O token de desenvolvimento fica no PROCESSO do servidor de
    #    desenvolvimento (nunca no pacote, P7); os quatro parametros de admissao do §B.4
    #    sao configuracao publica e so sao exigidos no modo embarcado.
    cd apps/web && TOC_TOKEN_DEV=tok-desenvolvimento-facilitadora \
        VITE_GHD_HOST_ORIGIN=https://fundacao.exemplo \
        VITE_GHD_HOST_BASE_URL=https://fundacao.exemplo/api \
        VITE_GHD_APP_ID=toc VITE_GHD_EMBED_URL=https://toc-federada.exemplo/toc/embarcado \
        npx vite --port 5173 &
    # 3. prova
    PLAYWRIGHT_BROWSERS_PATH=/opt/pw-browsers python3 apps/web/e2e/fumaca.py

Saída: uma linha por asserção e código de saída 0/1. As capturas vão para `e2e/saida/`.
"""
from __future__ import annotations

import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from playwright.sync_api import expect, sync_playwright

BASE = os.environ.get("TOC_WEB_URL", "http://127.0.0.1:5173")
SAIDA = Path(__file__).parent / "saida"
# Persona e instituição FICTÍCIAS (ADR 0006): nenhum dado real de pessoa entra aqui.
NOME_DO_PROJETO = f"Evasão na Instituição Horizonte {datetime.now(timezone.utc):%H%M%S}"

passos: list[tuple[str, bool]] = []


def registrar(descricao: str, condicao: bool) -> None:
    passos.append((descricao, condicao))
    print(("  ok  " if condicao else " FALHA ") + descricao)


def main() -> int:
    SAIDA.mkdir(exist_ok=True)
    with sync_playwright() as p:
        navegador = p.chromium.launch()
        pagina = navegador.new_page(viewport={"width": 1280, "height": 860})
        pagina.goto(BASE, wait_until="networkidle")

        registrar("a lista de projetos abre em modo autônomo", pagina.get_by_role("banner").is_visible())

        # -- criar um projeto de ARA, que nasce pela rota da ARA --------------------
        pagina.get_by_label("Nome", exact=False).first.fill(NOME_DO_PROJETO)
        pagina.get_by_role("button", name="Criar projeto").click()
        linha = pagina.get_by_role("row", name=NOME_DO_PROJETO)
        expect(linha).to_be_visible(timeout=10_000)
        registrar("o projeto criado aparece na lista", linha.is_visible())
        pagina.screenshot(path=str(SAIDA / "01-projetos.png"), full_page=True)

        # -- abrir a árvore e criar um efeito ---------------------------------------
        linha.get_by_role("button", name="Abrir").click()
        expect(pagina.get_by_role("tab", name="Nós (0)")).to_be_visible(timeout=10_000)
        pagina.get_by_role("button", name="Novo nó", exact=True).click()
        expect(pagina.get_by_role("tab", name="Nós (1)")).to_be_visible(timeout=10_000)
        registrar("o efeito novo entra no painel e no canvas", True)
        pagina.screenshot(path=str(SAIDA / "02-ara.png"), full_page=True)

        # -- a prova que a linhagem não podia fazer: recarregar e continuar lá -------
        pagina.reload(wait_until="networkidle")
        linha = pagina.get_by_role("row", name=NOME_DO_PROJETO)
        linha.get_by_role("button", name="Abrir").click()
        expect(pagina.get_by_role("tab", name="Nós (1)")).to_be_visible(timeout=10_000)
        registrar("PERSISTÊNCIA REAL: o nó sobrevive à recarga da página", True)

        # -- a nuvem de conflito, com as sete arestas --------------------------------
        pagina.get_by_role("button", name="Voltar").click()
        pagina.get_by_label("Nome", exact=False).first.fill(f"Expansão {NOME_DO_PROJETO}")
        pagina.get_by_label("Ferramenta").select_option("nc")
        pagina.get_by_role("button", name="Criar projeto").click()
        linha_nc = pagina.get_by_role("row", name=f"Expansão {NOME_DO_PROJETO}")
        expect(linha_nc).to_be_visible(timeout=10_000)
        linha_nc.get_by_role("button", name="Abrir").click()
        expect(pagina.get_by_test_id("entidade-A")).to_be_visible(timeout=10_000)
        arestas = pagina.locator("[data-testid^='aresta-']").count()
        registrar(f"a nuvem desenha as sete arestas (contadas: {arestas})", arestas == 7)
        pagina.screenshot(path=str(SAIDA / "03-nuvem.png"), full_page=True)

        # -- iframe estreito: 420px, só conteúdo -------------------------------------
        estreita = navegador.new_page(viewport={"width": 420, "height": 800})
        estreita.goto(f"{BASE}/?embarcado=1", wait_until="networkidle")
        sem_casca = estreita.get_by_role("banner").count() == 0
        registrar("embarcada em 420px: nenhuma casca própria (§B.8.1)", sem_casca)
        # E o conteúdo continua lá: embarcada não quer dizer vazia. Na largura de
        # referência de 420px a vista tabular é a projeção primária (RI-05 da spec 002).
        estreita.wait_for_timeout(500)
        conteudo = estreita.get_by_role("heading", name="Projetos").count() > 0
        registrar("embarcada em 420px: o conteúdo é renderizado", conteudo)
        estreita.screenshot(path=str(SAIDA / "04-embarcada-420.png"), full_page=True)

        navegador.close()

    falhas = [d for d, ok in passos if not ok]
    print(f"\n{len(passos) - len(falhas)}/{len(passos)} asserções passaram · capturas em {SAIDA}")
    return 1 if falhas else 0


if __name__ == "__main__":
    sys.exit(main())
