#!/usr/bin/env bash
# check-arquitetura.sh — a função de aptidão do P3 (DDD + hexagonal), executável.
#
# Por que existe: o P3 do `CLAUDE.md` diz "domínio e aplicação puros; efeito só por porta;
# adaptador na borda; `import-linter` como função de aptidão". Enquanto ninguém RODA o
# import-linter, essa frase é uma intenção — e intenção não é portão. Este script é o
# portão: ele roda os contratos declarados no `apps/api/pyproject.toml` e devolve código de
# saída, para a CI (integração contínua) e para o `scripts/evidencia.sh` o consumirem.
#
# O que os contratos proíbem, e por que cada um existe:
#   P3-1  `toc_api.dominio` não importa NADA de fora de si — nem outra camada nossa, nem
#         SQLAlchemy, FastAPI, Pydantic, httpx ou OpenTelemetry. É o que torna a regra da
#         TOC (Teoria das Restrições) testável sem rede e sem banco.
#   P3-2  `toc_api.aplicacao` não importa `infra` nem `http` nem framework — o caso de uso
#         fala com portas (`typing.Protocol`), nunca com adaptador.
#   P3-3  A dependência aponta para dentro: http → infra → aplicacao → dominio.
#
# Um detalhe que NÃO é acidente: os contratos P3-1 e P3-2 são do tipo `forbidden` com
# `include_external_packages = true`, e não só um contrato de camadas. Um contrato de
# camadas ordena os módulos do pacote entre si — e o domínio passaria verde importando
# SQLAlchemy, que é exatamente a violação que o P3 proíbe. O portão que não vê a violação
# que existe para ver é o defeito que a regra R2 do `CLAUDE.md` nomeia.
#
# Regra R2 (portão verde exige "quanto ele examinou?"): a saída do import-linter já imprime
# "Analyzed N files, M dependencies" e o veredito contrato a contrato. Este script **cola**
# essas linhas, nunca as reescreve (regra R1).
#
# Uso: scripts/check-arquitetura.sh [raiz]     (padrão: a raiz do repositório)
# Saída: 0 se todos os contratos estão mantidos; 1 se algum foi quebrado; 2 se o ambiente
# do serviço não está montado (que é falha de portão, não ausência de defeito).
set -uo pipefail

RAIZ="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
API="$RAIZ/apps/api"

echo "── Arquitetura hexagonal: contratos do import-linter (P3) ──"

if [[ ! -f "$API/pyproject.toml" ]]; then
  echo "✗ $API/pyproject.toml não existe — o serviço não está neste repositório." >&2
  exit 2
fi

# Quantos contratos o portão se propõe a verificar. Impresso ANTES de rodar, para o
# denominador não depender de o comando ter terminado bem.
DECLARADOS="$(grep -c '^\[\[tool\.importlinter\.contracts\]\]' "$API/pyproject.toml")"
echo "  contratos declarados no pyproject.toml: $DECLARADOS"

if [[ "$DECLARADOS" -eq 0 ]]; then
  echo "✗ nenhum contrato declarado: um import-linter sem contrato responde verde sobre nada." >&2
  exit 1
fi

# O executável: o do ambiente do projeto quando existe, senão o do PATH.
if [[ -x "$API/.venv/bin/lint-imports" ]]; then
  EXECUTAVEL=("$API/.venv/bin/lint-imports")
elif command -v lint-imports >/dev/null 2>&1; then
  EXECUTAVEL=(lint-imports)
elif command -v uv >/dev/null 2>&1; then
  EXECUTAVEL=(uv run --project "$API" lint-imports)
else
  echo "✗ lint-imports não encontrado. Monte o ambiente: (cd apps/api && uv sync)" >&2
  exit 2
fi

SAIDA="$(cd "$API" && "${EXECUTAVEL[@]}" 2>&1)"
CODIGO=$?

# O desenho ASCII do banner do import-linter não é evidência de nada; o resto é.
echo "$SAIDA" | sed -n '/^Analyzed/,$p'

if [[ $CODIGO -ne 0 ]]; then
  echo
  echo "✗ contrato de arquitetura quebrado (código $CODIGO)." >&2
  echo "  O caminho NÃO é afrouxar o contrato: é mover o import para a borda —" >&2
  echo "  efeito entra por porta (\`typing.Protocol\` em toc_api/dominio/portas.py)," >&2
  echo "  adaptador mora em toc_api/infra/." >&2
  exit 1
fi

echo
echo "✓ os $DECLARADOS contratos de arquitetura estão mantidos."
