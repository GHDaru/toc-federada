# Jornada sintética — base válida da sabotagem de `check-caminhos.sh`

Base 100% sintética (ADR 0006 — Registro de Decisão Arquitetural nº 6): nenhum dado real
de pessoa. Persona: **Facilitadora TOC** (Teoria das Restrições) da "Instituição
Horizonte".

Este arquivo existe para dar ao portão algo verdadeiro para conferir:

- um caminho **nosso** que existe: `docs/produto/visao.md`
- um caminho **isento declarado** (outro repositório, leitura apenas): `gestaodeprioridades/docs/produto/rounds.md`
- um **molde**, que o portão ignora de propósito: `specs/NNN-slug/spec.md`
- um caminho **nosso sob `apps/`**, que é onde mora a aplicação inteira e que o portão
  precisa conferir: `apps/api/src/toc_api/http/app.py`
- um caminho da **fundação sob `apps/`**, isento declarado por prefixo próprio:
  `apps/api/src/ghdaru_api/documents/ports/storage.py`
