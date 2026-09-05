#!/usr/bin/env bash
# check-canal.sh — o canal `ghd.*` recusa os três defeitos que a norma registrou.
#
# Siglas, uma vez: APH — Aplicação ↔ Harness · URL — Uniform Resource Locator.
#
# Roda `node --test` sobre `apps/web/src/federacao/`, que é JavaScript puro e sem
# dependência — o portão funciona antes de existir build de interface, e continua
# funcionando depois. Os três defeitos, todos medidos no protótipo da aplicação irmã e
# registrados no Anexo B: envelope `{tipo, versao}` (§B.2, linha 52), `targetOrigin: "*"`
# (linha 62) e `ev.source === parent` inexistente (linha 23).
#
# Uso: scripts/check-canal.sh [raiz]
# Saída: 0 verde · 1 vermelho · 2 ambiente incompleto
set -uo pipefail

RAIZ="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
DIR="$RAIZ/apps/web/src/federacao"

echo "── Canal ghd.* (Anexo B §B.2): envelope, trava dupla, targetOrigin e tema ──"

command -v node >/dev/null 2>&1 || { echo "✗ node não encontrado" >&2; exit 2; }
[[ -f "$DIR/canal.mjs" ]] || { echo "✗ $DIR/canal.mjs não existe" >&2; exit 2; }

TESTES="$(find "$DIR" -name '*.test.mjs' | wc -l)"
echo "  arquivos de teste encontrados: $TESTES"
[[ "$TESTES" -ge 1 ]] || { echo "✗ nenhum teste do canal — um módulo sem teste não é portão." >&2; exit 1; }

SAIDA="$(cd "$RAIZ" && node --test "$DIR"/*.test.mjs 2>&1)"
CODIGO=$?
echo "$SAIDA" | grep -E '^# (tests|pass|fail|duration_ms)' || echo "$SAIDA" | tail -20

if [[ $CODIGO -ne 0 ]]; then
  echo "$SAIDA" | grep -E '^not ok' >&2
  echo "✗ o canal falhou — leia acima." >&2
  exit 1
fi
echo "✓ canal conforme ao §B.2."
