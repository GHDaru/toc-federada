# Avisos de terceiros (Third-Party Notices)

Este repositório é licenciado sob MIT (ver [`LICENSE`](LICENSE)). Ele incorpora, absorve
ou adapta material de terceiros listado abaixo. A regra é a do método: **atribuição
explícita, nunca cópia silenciosa** — cada item diz o que veio, de onde, sob qual licença
e em que forma vive aqui.

## 1. Método Maestro — `GHDaru/maestro`

- **O quê**: a superfície instalável do método — agentes (`.claude/agents/`), skills
  (`skills/`), comandos (`.claude/commands/`), templates (`.specify/templates/`), scripts
  do ritual (`scripts/*.sh` instalados) e os documentos de governança do método
  (`docs/governance/principles.md`, `operating-model.md`, `axioms.md`, `glossary.md`,
  `artifacts.md`).
- **Como chegou**: instalada pelo instalador oficial do Maestro (`bin/maestro init`),
  verificável por `scripts/check-install.sh`.
- **Licença**: MIT — Copyright (c) 2026 GHDaru. A cópia da licença viaja com a instalação
  em [`docs/governance/MAESTRO-LICENSE`](docs/governance/MAESTRO-LICENSE); os avisos de
  terceiros do próprio método estão em
  [`docs/governance/MAESTRO-THIRD-PARTY-NOTICES.md`](docs/governance/MAESTRO-THIRD-PARTY-NOTICES.md).
- **Forma**: instalação derivada do canônico; o canônico permanece em `GHDaru/maestro` e
  as cópias locais não são editadas aqui (princípio P1 e regra de idioma do ADR 0014 do
  método).

## 2. Metodologia reversa — `sandeco/reversa`

- **O quê**: a **taxonomia de planejamento absorvida** — hierarquia
  Módulo ⊃ Épico ⊃ Feature ⊃ User Story; famílias de requisito RF/RI/RNF/RN/INT/F/L;
  forma EARS (*Easy Approach to Requirements Syntax*); selos de confiança 🟢/🟡/🔴;
  marcador `[DÚVIDA]`; premortem; régua de prontidão de spec.
- **Como chegou**: **absorção conceitual, sem instalar o framework** — instalar criaria um
  segundo `CLAUDE.md` e colidiria com o Maestro. A decisão, com a alternativa de
  instalação descartada, é o ADR 0004 (`docs/adr/0004-*.md`).
- **Licença**: MIT, conforme declarado no repositório de origem (citado no ADR 0004).
- **Forma**: nenhum arquivo do repositório de origem vive aqui; o que vive é a taxonomia,
  reescrita para o vocabulário deste projeto, com esta atribuição.

## 3. Gerador do site de produto — `GHDaru/daruskills` (`spec-to-code-docs`)

- **O quê**: o gerador de site estático de documentação de produto (`generate.py`,
  `render.py`, `templates/`, `styles.css`) que produz `docs/product-site/` a partir das
  specs.
- **Como chegou**: **vendorizado** em `tools/product-site/`, adaptado para as famílias de
  requisito deste projeto (inclusive RI) e para o vocabulário da Teoria das Restrições
  (TOC). A decisão é o ADR 0008 (`docs/adr/0008-*.md`).
- **Licença**: mesmo titular deste repositório (GHDaru); o clone de origem lido em
  2026-09-03 não carrega arquivo de licença próprio — o uso aqui é do titular, sob a MIT
  deste repositório, com a origem citada nesta nota e no cabeçalho do código vendorizado.
- **Forma**: cópia adaptada; correção de defeito de interesse geral é **relatada** à
  origem (`mensagens/`, regra P1), nunca corrigida só aqui em silêncio.

---

Nenhum outro material de terceiros é incorporado por este repositório na presente
entrega. Dependências de código (npm, PyPI) declaram suas licenças nos próprios
manifestos (`package.json`, `pyproject.toml`) quando os ciclos de implementação as
introduzirem.
