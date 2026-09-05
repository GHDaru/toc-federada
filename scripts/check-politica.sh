#!/usr/bin/env bash
# check-politica.sh — a política sempre-verdadeira nunca é composta em produção.
#
# Siglas, uma vez: APH — Aplicação ↔ Harness · IA — inteligência artificial.
#
# O APH-7.2 nomeia a política que devolve verdadeiro para tudo como o contraexemplo da
# autorização fora do modelo, e a RF-20 da spec 006 manda tê-la na suíte como **sabotagem**
# — o valor dela é medir os testes de recusa, não autorizar ninguém.
#
# O risco é o de sempre com sabotagem que vive no código: alguém a injeta "só para
# destravar" e ela fica. Este portão é a trava: `PoliticaSempreVerdadeira` só pode ser
# NOMEADA no arquivo que a define e em testes. Composição de produção que a mencione
# reprova.
#
# Uso: scripts/check-politica.sh [raiz]
# Saída: 0 limpo · 1 a sabotagem escapou para o código de produção
set -uo pipefail

RAIZ="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
FONTE="$RAIZ/apps/api/src"
DEFINICAO="toc_api/aplicacao/politica.py"

echo "── Política de autorização: a sabotagem do APH-7.2 não vaza para produção ──"

if [[ ! -d "$FONTE" ]]; then
  echo "✗ $FONTE não existe" >&2
  exit 1
fi

ARQUIVOS="$(find "$FONTE" -name '*.py' | wc -l)"
echo "  arquivos de produção varridos: $ARQUIVOS"

# O padrão procura USO, não menção: `import ... PoliticaSempreVerdadeira` e
# `PoliticaSempreVerdadeira(...)`. Citá-la numa docstring — para explicar por que os testes
# de recusa existem — é documentação, e proibir documentação seria portão punindo a
# explicação em vez do defeito.
ACHADOS="$(grep -rnE 'PoliticaSempreVerdadeira[[:space:]]*\(|^[[:space:]]*(from|import)[^#]*PoliticaSempreVerdadeira' "$FONTE" --include='*.py' | grep -v "$DEFINICAO" || true)"

if [[ -n "$ACHADOS" ]]; then
  echo "✗ a política sempre-verdadeira é mencionada fora da própria definição:" >&2
  echo "$ACHADOS" >&2
  echo "  Ela é sabotagem de teste (RF-20), nunca composição. Use PoliticaPorCapability." >&2
  exit 1
fi

# E a política de verdade tem de estar composta em algum lugar: ausência das duas seria
# "sem autorização nenhuma", que passaria neste portão pelo motivo errado.
COMPOSTA="$(grep -rln 'PoliticaPorCapability' "$FONTE" --include='*.py' | wc -l)"
echo "  arquivos que compõem PoliticaPorCapability: $COMPOSTA"
if [[ "$COMPOSTA" -lt 1 ]]; then
  echo "✗ nenhuma composição usa PoliticaPorCapability — autorização ausente é pior que errada." >&2
  exit 1
fi

echo "✓ a sabotagem vive só na definição; a política real está composta."
