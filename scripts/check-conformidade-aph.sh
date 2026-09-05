#!/usr/bin/env bash
# check-conformidade-aph.sh — sobe o serviço e roda a suíte de conformidade do Padrão APH.
#
# Siglas, uma vez: APH — Aplicação ↔ Harness (o padrão da fronteira) · SSE — Server-Sent
# Events · HTTP — HyperText Transfer Protocol · URL — Uniform Resource Locator.
#
# A suíte vive em `GHDaru/protocolos`, que é SOMENTE LEITURA (P1) — e ela precisa das
# bibliotecas `ajv`/`ajv-formats`, que não estão instaladas lá. Instalar seria escrever num
# repositório alheio, então o ambiente de execução mora AQUI, em `tools/aph/`: dois
# símbolicos (`conformidade` e `padrao`) apontam para o original e o `node_modules` é
# nosso. O `--preserve-symlinks` faz o Node resolver os módulos pelo caminho do símbolico,
# e é isso que fecha o arranjo sem tocar em nada de fora.
#
# O alvo é 11 de 11 nos checks executáveis, e SEM perfil de adaptação — o perfil é
# dicionário legítimo (§A.0/§A.8), mas usá-lo quando a aplicação já fala o canônico seria
# esconder o que não precisa ser escondido.
#
# Uso: scripts/check-conformidade-aph.sh [porta]
# Saída: 0 apto (11/11) · 1 não apto · 2 ambiente incompleto
set -uo pipefail

RAIZ="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PORTA="${1:-8099}"
API="$RAIZ/apps/api"
SUITE="$RAIZ/tools/aph"

echo "── Conformidade APH — Nível 1 (Observador), 11 checks executáveis ──"

[[ -x "$API/.venv/bin/uvicorn" ]] || { echo "✗ ambiente do serviço não montado (cd apps/api && uv sync)" >&2; exit 2; }
[[ -d "$SUITE/node_modules/ajv" ]] || { echo "✗ ajv ausente em tools/aph (cd tools/aph && npm install)" >&2; exit 2; }
[[ -e "$SUITE/conformidade/suite.mjs" ]] || { echo "✗ suíte ausente: $SUITE/conformidade/suite.mjs" >&2; exit 2; }
command -v node >/dev/null 2>&1 || { echo "✗ node não encontrado" >&2; exit 2; }

REGISTRO="$(mktemp)"
"$API/.venv/bin/uvicorn" --factory toc_api.http.app:criar_app \
  --port "$PORTA" --log-level warning > "$REGISTRO" 2>&1 &
SERVICO=$!
trap 'kill "$SERVICO" 2>/dev/null; rm -f "$REGISTRO"' EXIT

for _ in $(seq 1 40); do
  if curl -sf "http://localhost:$PORTA/saude" > /dev/null 2>&1; then break; fi
  sleep 0.25
done
if ! curl -sf "http://localhost:$PORTA/saude" > /dev/null 2>&1; then
  echo "✗ o serviço não subiu na porta $PORTA:" >&2
  cat "$REGISTRO" >&2
  exit 2
fi
echo "  serviço de pé: $(curl -s "http://localhost:$PORTA/saude")"
echo

cd "$SUITE" || exit 2
node --preserve-symlinks --preserve-symlinks-main conformidade/suite.mjs "http://localhost:$PORTA"
CODIGO=$?

echo
if [[ $CODIGO -ne 0 ]]; then
  echo "✗ NÃO APTO — leia o veredito acima; nenhum check foi pulado." >&2
  exit 1
fi
echo "✓ APTO nos 11 checks executáveis, sem perfil de adaptação."
