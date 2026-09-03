# `tools/product-site` — o gerador do site de produto (vendorizado)

> Siglas deste documento: **TOC** — Teoria das Restrições; **ADR** — *Architecture Decision
> Record* (Registro de Decisão Arquitetural); **RF** — requisito funcional; **RI** —
> requisito de interface; **RNF** — requisito não funcional; **RN** — regra de negócio;
> **INT** — integração; **APH** — o padrão Aplicação ↔ Harness; **DDD** — *Domain-Driven
> Design* (Design Orientado a Domínio); **HTML** — *HyperText Markup Language*; **CSS** —
> *Cascading Style Sheets*; **JSON** — *JavaScript Object Notation*; **P1/P6** — princípios
> da constituição do projeto; **R1/R2** — regras herdadas de retrospectiva.

O site em `docs/product-site/` é **100% gerado** por estes dois scripts (ADR 0008). Nenhuma
página é escrita à mão: mudança no site é mudança no gerador ou nas specs que ele lê.

## Origem e atribuição

| | |
|---|---|
| Repositório de origem | `GHDaru/daruskills`, skill `spec-to-code-docs` |
| Commit lido | `da96a89c6a36fa58a33c6e7428ec780e08694d6d` (2026-09-03) |
| Arquivos vendorizados | `generate.py`, `render.py`, `templates/styles.css`, `templates/progress.html` |
| Licença | mesmo titular deste repositório (GHDaru); o clone de origem não carrega arquivo de licença próprio. Nota completa em `THIRD-PARTY-NOTICES.md`, §3 |

**A origem é leitura (P1).** Defeito encontrado nela **não se corrige lá**: relata-se em
`mensagens/`. Os sete achados desta vendorização estão em
`mensagens/001-para-daruskills-defeitos-do-gerador-de-site.md`, com evidência por
`arquivo:linha` e a saída executada colada.

## Como rodar

Duas etapas — descoberta e renderização —, com o mesmo par de comandos do gerador de origem:

```bash
python3 tools/product-site/generate.py . --output docs/product-site/data.json
python3 tools/product-site/render.py docs/product-site/data.json --output docs/product-site
```

Somente biblioteca padrão do Python; nenhuma dependência para instalar. Verificado em:

```
$ python3 --version
Python 3.11.15

$ python3 tools/product-site/generate.py . --output docs/product-site/data.json
JSON escrito em docs/product-site/data.json
  módulos=8 specs=12 adrs=8 RF=359 RI=114 RNF=105 RN=71 INT=61 fontes=176 ciclos=12

$ python3 tools/product-site/render.py docs/product-site/data.json --output docs/product-site
  docs/product-site/styles.css (6209 bytes)
  docs/product-site/index.html (47890 bytes)
  docs/product-site/modules.html (88977 bytes)
  docs/product-site/traceability.html (377476 bytes)
  docs/product-site/roadmap.html (36806 bytes)
Site renderizado em docs/product-site/
```

Regerar duas vezes seguidas produz bytes idênticos (`diff -r` vazio sobre os seis
arquivos) — é o que torna verificável o portão do ciclo 012: *"o site regenerado não diverge
do commitado"*.

## O que o gerador lê

| Insumo | O que sai dele |
|---|---|
| `specs/*/spec.md` | RF, RI, RNF, RN e INT com selo e fontes citadas; features pelos sub-cabeçalhos `###`; visão; lacunas L-NN; dúvidas do `## Clarify`; seção `## Fontes` (F-NN) |
| `specs/*/` (demais arquivos) | a cadeia *forward* do ciclo: `plan.md`, `tasks.md`, `data-model.md`, `contracts/`, `qa-report.md` |
| `docs/produto/modulos.md` | os oito módulos M1–M8, o *bounded context*, o job, os épicos e as specs que os entregam |
| `docs/roadmap.md` | os doze ciclos, com portões e o que cada um não pode começar sem |
| `docs/adr/*.md` | número, título, status, decisão e o campo "Princípios tocados" |
| `docs/governance/constitution.md` | os princípios P1–P7 e a tabela de decisões estruturais (a *stack*) |
| `skills/*/SKILL.md`, `scripts/*.sh`, `docs/jornadas/*.md` | a página de artefatos |

Isto faz do formato da spec uma **função forçante** (princípio VI do método): o gerador
depende dos cabeçalhos verbatim que o ADR 0004 fixou, e `scripts/check-specs.sh` os cobra.
Mudar um cabeçalho sem mudar o gerador quebra a página correspondente — de propósito.

## O que foi adaptado (e por quê)

O gerador de origem foi escrito para o PROJETO_ECS. Rodá-lo cru aqui produziria um site que
afirma o que não leu. As adaptações, todas na cópia — nunca no original:

1. **Requisitos de interface (RI-NN) como cidadãos de primeira classe.** A extração foi
   parametrizada por prefixo e cobre RF, RI, RNF, RN e INT, com a mesma família de expressão
   regular. Na rastreabilidade, RI é grupo próprio, com filtro. *(Sem isto, 114 requisitos de
   interface deste corpus ficariam invisíveis — achado A1 da mensagem 001.)*
2. **Extração por seção, e grupo pelo texto.** Cada tipo é lido da sua seção
   (`## Requisitos funcionais`, `## Requisitos de interface`, …) e cada requisito é atribuído
   ao **último sub-cabeçalho `###` que o precede** — não a uma fatia de tamanho médio, que na
   origem errava a fronteira de cinco das sete features da spec 004 (achado A3).
3. **Fontes de verdade, com selo.** As fontes vêm da seção `## Fontes` da spec (F-NN, com
   `arquivo:linha`, trecho e uso), e cada requisito herda as que cita entre colchetes. Fonte
   deste repositório vira link; fonte de repositório externo (linhagem, norma, fundação) vira
   marca com dica de contexto — nunca link quebrado.
4. **Vocabulário da TOC.** `DOMAIN_MAP` e `HIGH_SIGNAL_KEYWORDS` falam restrição, efeito
   indesejável, árvore, nuvem, conflito, injeção, premissa, obstáculo, objetivo intermediário,
   focalização, catálogo, proposta, manifesto, introspecção, snapshot e embarque.
5. **Workflow real, no lugar das fases de outro projeto.** As oito fases são as do Maestro
   instalado aqui — `spec → plan (Constitution Check) → tasks → implement → DoD → revisão em
   contexto fresco → gate humano → merge` —, cada uma com dono, métrica verificável, critérios
   de entrada, saídas e **aresta de falha** ("se gate vermelho → volta à fase N: ação").
6. **Taxonomia de 15 termos em 3 categorias**, escrita para este produto: Produto (o domínio
   da TOC), Engenharia (APH, DDD, hexagonal) e Metodologia (Maestro). Cada termo traz
   definição, mapeamento ao uso real com caminho, e analogia.
7. **Roadmap lido do roadmap.** Os doze ciclos, os portões e as condições de entrada saem de
   `docs/roadmap.md` como estão escritos. A origem os descartava e desenhava no lugar uma tira
   fixa `F0✓ … F5○` que ninguém executou (achado A6).
8. **Página de módulos M1–M8.** A origem só conhecia "specs" ou "módulos de código"; aqui o
   mapa de `docs/produto/modulos.md` é primeira classe, com épicos, dependências e as specs
   que o entregam — e declara quando uma spec conta em dois módulos, em vez de fingir precisão.
9. **Princípios P1–P7 fora da contagem por spec.** A origem copiava os sete princípios da
   constituição para dentro da lista de RNF de **cada** spec, inflando o total de 105 para 189
   (achado A2). Aqui eles têm página própria.
10. **Texto do repositório é escapado antes de virar HTML** (`_md()` em `render.py`), e só
    então recebe `<code>` e `<b>`. Sem isso, um requisito que cita `NNN-para-<repo>-<assunto>.md`
    perde `<repo>` no navegador (achado A5). Link markdown vira o caminho resolvido, em vez de
    chegar como `[texto](destino)` cru na página.
11. **Chamada "Barra:" em cada página**, dizendo contra o que aquela página está sendo medida.
12. **Nota de honestidade no rodapé do roadmap**, com o estado real: ciclo 001 em curso, zero
    linha de código de produção, nenhuma jornada viva.
13. **Marca "TOC Federada"** na casca (nome, sigla, subtítulo, títulos das páginas).

## O que **não** foi adaptado — e a divergência que isso deixa

`templates/styles.css` é mantido **byte a byte idêntico** ao da origem: é a régua de design
validada, e trocá-la pelo gosto seria perder a régua.

```
$ md5sum tools/product-site/templates/styles.css /home/user/daruskills/spec-to-code-docs/templates/styles.css
f23215aa36c63563b60dfb8cd7cce005  tools/product-site/templates/styles.css
f23215aa36c63563b60dfb8cd7cce005  /home/user/daruskills/spec-to-code-docs/templates/styles.css
```

**Divergência conhecida, declarada em vez de escondida**: a terceira linha desse CSS diz
`Theme key: ecs-theme`, e o renderizador daqui grava a preferência de tema em
`tocfed-theme` (marca própria). O comentário fica desatualizado **porque o arquivo não é
tocado** — corrigi-lo exigiria editar a régua. Quem lê o CSS deve confiar no `render.py`.

O `templates/progress.html` também veio idêntico e **não é usado** por este renderizador;
fica como referência do formato da origem.

## Estrutura

```
tools/product-site/
├── README.md            ← este arquivo (origem, adaptações, como rodar)
├── generate.py          ← descoberta e extração → JSON
├── render.py            ← JSON → quatro páginas HTML + CSS
└── templates/
    ├── styles.css       ← régua de design, idêntica à origem
    └── progress.html    ← template da origem, não usado aqui
```

Saída, em `docs/product-site/`: `index.html` (visão geral, taxonomia, workflow, ADRs,
princípios, artefatos, métricas), `modules.html` (M1–M8 e as doze specs),
`traceability.html` (RF + RI + RNF com fontes e cadeia), `roadmap.html` (os doze ciclos),
`styles.css` e `data.json` (o insumo intermediário, versionado para que o site seja
auditável sem rodar nada).

## Regras que este gerador obedece

- **R1 — verifique antes de afirmar**: todo número do site é **contado na geração**. Nenhum
  total é digitado. O comando imprime o que contou.
- **R2 — verde diz quanto examinou**: `generate.py` imprime módulos, specs, ADRs, requisitos
  por tipo, fontes e ciclos; `render.py` imprime cada arquivo escrito e o seu tamanho.
- **P6 — jornada viva**: o site **não** inventa jornada. Enquanto `docs/jornadas/` tiver
  apenas a convenção, a página de artefatos diz "zero — e é decisão, não atraso", com o
  motivo.
- **P1 — fronteira de escrita**: o gerador só lê este repositório. Caminho de fonte externa
  (linhagem, norma, fundação) aparece como dica de contexto, nunca como link que o navegador
  tentaria abrir.
