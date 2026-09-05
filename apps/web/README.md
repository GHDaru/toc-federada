# `apps/web` — a interface da toc-federada

> Siglas, uma vez: **TOC** — Teoria das Restrições · **ARA** — Árvore da Realidade Atual ·
> **NC** — Nuvem de Conflito · **UDE** — Efeito Indesejável (*Undesirable Effect*) ·
> **APH** — Aplicação ↔ Harness (o padrão da fronteira) · **API** — interface de
> programação de aplicações · **URL** — *Uniform Resource Locator* · **CSS** — *Cascading
> Style Sheets* · **TRIZ** — Teoria da Resolução Inventiva de Problemas.

React + TypeScript + Vite. É a sucessora da 4ª geração da linhagem TOC-Builder, e a
diferença entre as duas cabe em três frases:

1. **A persistência é real.** Cada comando é uma rota nomeada do agregado no serviço
   (`apps/api`), que grava no PostgreSQL. Lá, `saveProjectState` substituía o projeto
   inteiro num mapa em memória do navegador.
2. **Nenhum segredo mora aqui.** Não existe cliente de provedor de modelo nesta interface;
   a assistência é do servidor, por ação governada. A violação canônica que isto sucede
   está em `/home/user/tocbuilderv3/services/geminiService.ts` (leitura apenas).
3. **Tem teste.** A lógica de federação, os componentes com regra e o fluxo feliz **e** o
   de erro de cada tela.

## Como rodar

```bash
# serviço (noutro terminal), com o PostgreSQL de desenvolvimento de pé
cd apps/api && DATABASE_URL='postgresql+psycopg://toc@/toc_federada?host=/var/run/postgresql&port=5433' \
  TOC_AMBIENTE=desenvolvimento .venv/bin/uvicorn --factory toc_api.http.app:criar_app --port 8000

# interface
cd apps/web
npm install
TOC_TOKEN_DEV=tok-desenvolvimento-facilitadora npm run dev
```

`TOC_TOKEN_DEV` **não tem prefixo `VITE_` de propósito**: ele fica no processo do servidor
de desenvolvimento e é injetado pelo proxy (`vite.config.ts`), nunca servido ao navegador
e nunca presente em `npm run build`. Sem ele, a interface em modo autônomo fala com o
serviço sem identidade e recebe `401` — que é o fluxo de erro desenhado, não um defeito.

Os quatro parâmetros de admissão do §B.4 do Anexo B (`VITE_GHD_HOST_ORIGIN`,
`VITE_GHD_HOST_BASE_URL`, `VITE_GHD_APP_ID`, `VITE_GHD_EMBED_URL`) só são exigidos no
**modo embarcado**; o modelo está em `.env.example`.

## Portões

```bash
npm test          # Vitest: federação, componentes com regra, telas (feliz + erro)
npm run typecheck # TypeScript estrito
npm run build     # tsc --noEmit && vite build
npm run test:canal        # node --test sobre o canal ghd.* (o mesmo do scripts/check-canal.sh)
PLAYWRIGHT_BROWSERS_PATH=/opt/pw-browsers python3 e2e/fumaca.py   # navegador real × serviço real
```

## Mapa

| Caminho | O que é |
|---|---|
| `src/federacao/canal.mjs` | o canal `ghd.*` em JavaScript puro — envelope fechado, trava dupla `source`+`origin`, `targetOrigin` dirigido. Rodado por `scripts/check-canal.sh` com `node --test`, sem build |
| `src/federacao/admissao.ts` | os quatro parâmetros do §B.4; falta um, a aplicação embarcada **recusa subir** dizendo qual |
| `src/federacao/tema.ts` | os quatro tokens que o manifesto declara consumir, com *fallback* próprio completo nos dois esquemas |
| `src/federacao/embarque.ts` | a sequência: `ghd.ready` primeiro, handshake conferido, grant trocado por sessão **imediatamente**, modo anônimo quando não há identidade |
| `src/api/cliente.ts` | um método por comando do agregado; o token entra por função, nunca é guardado |
| `src/dominio/tipos.ts` | espelho dos tipos do serviço — **sem regra duplicada**: validação de UDE, topologia da nuvem e transições são do domínio do servidor |
| `src/telas/registro.ts` | o registro de telas, com paridade testada contra `specs/006-acoes-governadas-e-snapshot/contracts/manifesto.json` |
| `src/componentes/canvas/` | canvas com pan, zoom, ajustar, edição inline, raio de exclusão declarado e movimento por teclado |
| `src/componentes/PainelDeEntidades.tsx` | a vista tabular do mesmo grafo: contagem por aba, cabeçalho fixo, largura redimensionável e criação de aresta sem arrastar |
| `src/componentes/ude/` | ficha de validação em duas seções, trecho reprovado marcado no texto, exame de elo e relatório estrutural |
| `src/componentes/nuvem/` | diagrama canônico (5 entidades, **7** arestas), ficha da aresta, visão de solução, vista tabular e a pré-visualização da geração |
| `src/i18n/` | português e inglês desde o primeiro dia, com chave tipada e paridade verificada por teste |
| `e2e/fumaca.py` | a prova de fumaça em navegador real contra o serviço real |

## Decisões que valem estar escritas

- **A posição das entidades da nuvem vem do servidor.** A topologia é fixa (RN-01): quem
  usa edita texto, não arruma caixas — e por isso não existe arrastar no diagrama da NC.
- **Editar o título de um UDE é reformular**, o que reexecuta a validação formal no mesmo
  comando. Um `PATCH` silencioso deixaria o veredito velho ao lado do texto novo.
- **Desfazer cobre criar, mover, editar e ligar**, com o nome do episódio no botão. Não
  cobre exclusão, porque o serviço não ressuscita nó nem aresta: em vez de prometer volta,
  a exclusão declara o raio antes ("remove também N arestas").
- **Gerar não aplica.** A pré-visualização mostra o diff e o `action_id`; quem escreve é a
  proposta governada, com gate humano.
