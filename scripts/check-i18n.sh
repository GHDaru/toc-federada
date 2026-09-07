#!/usr/bin/env bash
# check-i18n.sh — o portão de internacionalização (spec 011, E8.3: RF-07, RF-08, RF-09).
#
# Siglas, uma vez: **i18n** — internacionalização · **CI** — integração contínua ·
# **JSX** — JavaScript XML (a sintaxe de marcação do React) · **RF** — requisito funcional.
#
# ── O defeito que este portão existe para não deixar voltar ──────────────────────────
#
# A quarta geração da linhagem gastou **duas das suas cinco** especificações de
# funcionalidade traduzindo telas que já existiam
# (`tocbuilderv3/specs/feat_internationalization_full.md` e
# `feat_internationalization_final_steps.md`, as duas datadas de 2024-08-02) — e mesmo
# assim ficou com literais em português vivos no código de produção
# (`tocbuilderv3/components/SnTView.tsx:182`, `SnTStepEditorModal.tsx:92,95`) e com um
# defeito estrutural: `i18n/I18nProvider.tsx:41` fazia `let result = translation || key;`,
# renderizando a **chave crua** quando a tradução faltava.
#
# Nada daquilo era falta de disciplina. Era falta de portão: a dívida de tradução é
# invisível — a tela funciona, o texto aparece, e só quem troca de idioma descobre.
#
# ── O que ele verifica, exatamente ───────────────────────────────────────────────────
#
#   1. **literal órfão** — nenhuma cadeia visível fora do dicionário, medida com o próprio
#      compilador do TypeScript (nó de texto JSX e atributo visível), com lista de exceções
#      que exige **motivo escrito por linha** (lacuna L-05 da spec);
#   2. **paridade** — chave da língua-fonte sem tradução é pendência que reprova; chave só
#      na tradução é erro (RF-08, RN-01);
#   3. **chave ausente falha alto** — o mecanismo lança em desenvolvimento e cai para a
#      língua-fonte em produção, e **nunca** devolve a chave crua (RF-09, RF-10).
#
# Regra R2 do `CLAUDE.md` (portão verde diz quanto examinou): a saída imprime quantos
# arquivos foram varridos, quantas cadeias foram examinadas, quantas passam pelo
# dicionário e quantas chaves cada idioma tem.
#
# Uso: scripts/check-i18n.sh [raiz]   (padrão: a raiz do repositório)
# Saída: 0 conforme · 1 violação encontrada · 2 ambiente não montado.
set -uo pipefail

AQUI="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RAIZ="${1:-$(cd "$AQUI/.." && pwd)}"

if ! command -v node > /dev/null 2>&1; then
  echo "✗ node não está no PATH — a varredura usa o compilador do TypeScript." >&2
  exit 2
fi

node "$AQUI/i18n/varredura.mjs" "$RAIZ"
