#!/usr/bin/env bash
# check-conformidade-aph.sh — sobe o serviço e roda a suíte de conformidade do Padrão APH.
#
# Siglas, uma vez: APH — Aplicação ↔ Harness (o padrão da fronteira) · SSE — Server-Sent
# Events · HTTP — HyperText Transfer Protocol · URL — Uniform Resource Locator · IA —
# inteligência artificial · ADR — Architecture Decision Record (registro de decisão).
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
# ── POR QUE ESTE PORTÃO DECLARA O QUE MEDIU (regra R2) ────────────────────────────────
# Ele herdava o ambiente do shell e subia o serviço com o que estivesse lá. Sem
# `DATABASE_URL` exportada, o serviço cai em `persistencia: memoria` (é o que a fábrica faz,
# `apps/api/src/toc_api/infra/persistencia/fabrica.py`) e a suíte devolve **11/11 do mesmo
# jeito** — porque ela é caixa-preta e mede o fio, não o que está atrás dele. Foi o que
# aconteceu na corrida de uma revisão independente: verde legítimo, alvo errado, e a saída
# não dizia nem uma coisa nem outra. Um verde que não declara o que examinou não é
# evidência; é a regra R2 do CLAUDE.md deste projeto, e ela vale para os nossos portões
# antes de valer para os dos outros.
#
# Portanto, agora: o alvo é montado com ambiente EXPLÍCITO, o banco é sondado ANTES de
# subir o serviço, o `/saude` é lido e DECLARADO campo a campo, e medir contra memória
# **recusa** — a não ser que quem chama peça `--permitir-memoria`, e aí o veredito sai
# carimbado como o que é.
#
# Uso: scripts/check-conformidade-aph.sh [porta] [--permitir-memoria]
# Saída: 0 apto (11/11 contra o banco) · 1 não apto · 2 ambiente incompleto
#        3 alvo recusado (mediria memória em vez do banco)
set -uo pipefail

RAIZ="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
API="$RAIZ/apps/api"
SUITE="$RAIZ/tools/aph"

# A cadeia medida no ambiente de desenvolvimento (brief §1), a MESMA que a suíte de
# integração usa como padrão (`apps/api/tests/integracao/conftest.py`, URL_PADRAO).
# Sem credencial: o cluster local autentica por socket confiado (P7).
URL_PADRAO="postgresql+psycopg://toc@/toc_federada?host=/var/run/postgresql&port=5433"

PORTA=8099
PERMITIR_MEMORIA=0
for arg in "$@"; do
  case "$arg" in
    --permitir-memoria) PERMITIR_MEMORIA=1 ;;
    ''|*[!0-9]*) echo "✗ argumento não reconhecido: $arg (uso: [porta] [--permitir-memoria])" >&2; exit 2 ;;
    *) PORTA="$arg" ;;
  esac
done

echo "── Conformidade APH — Nível 1 (Observador), 11 checks executáveis ──"

[[ -x "$API/.venv/bin/uvicorn" ]] || { echo "✗ ambiente do serviço não montado (cd apps/api && uv sync)" >&2; exit 2; }
[[ -d "$SUITE/node_modules/ajv" ]] || { echo "✗ ajv ausente em tools/aph (cd tools/aph && npm install)" >&2; exit 2; }
[[ -e "$SUITE/conformidade/suite.mjs" ]] || { echo "✗ suíte ausente: $SUITE/conformidade/suite.mjs" >&2; exit 2; }
command -v node >/dev/null 2>&1 || { echo "✗ node não encontrado" >&2; exit 2; }

# ── 1. de onde vem a cadeia do banco, dito em voz alta ────────────────────────────────
if [[ -n "${DATABASE_URL:-}" ]]; then
  URL_DO_BANCO="$DATABASE_URL"
  ORIGEM_DA_URL="DATABASE_URL do ambiente"
else
  URL_DO_BANCO="$URL_PADRAO"
  ORIGEM_DA_URL="padrão de desenvolvimento deste repositório (não havia DATABASE_URL no ambiente)"
fi

# ── 2. sondagem do banco ANTES de subir o serviço ─────────────────────────────────────
# Sem isto o serviço subiria com a cadeia e só o `/saude` diria "postgres", mesmo com o
# cluster fora do ar — porque o motor do SQLAlchemy é preguiçoso. A sondagem também colhe
# a revisão da migração, que é o segundo "quanto ele examinou?" deste portão.
SONDAGEM="$("$API/.venv/bin/python" - "$URL_DO_BANCO" <<'PY' 2>&1
import sys
from sqlalchemy import create_engine, text
try:
    motor = create_engine(sys.argv[1])
    with motor.connect() as conexao:
        versao = conexao.execute(text("select version()")).scalar() or ""
        try:
            revisao = conexao.execute(text("select version_num from alembic_version")).scalar()
        except Exception:
            revisao = None
    motor.dispose()
except Exception as erro:  # cluster fora do ar, cadeia inválida, banco inexistente
    print(f"FORA|{type(erro).__name__}: {str(erro).splitlines()[0][:160]}")
else:
    print(f"DE_PE|{versao.split(' on ')[0]}|{revisao or '(sem tabela alembic_version)'}")
PY
)"
ESTADO_DO_BANCO="${SONDAGEM%%|*}"

if [[ "$ESTADO_DO_BANCO" != "DE_PE" ]]; then
  MOTIVO="${SONDAGEM#*|}"
  echo
  echo "✗ RECUSADO — o banco não respondeu, logo o alvo mediria em MEMÓRIA." >&2
  echo "  cadeia ....... $URL_DO_BANCO ($ORIGEM_DA_URL)" >&2
  echo "  resposta ..... $MOTIVO" >&2
  echo >&2
  echo "  Um 11/11 medido em memória diz que o transporte responde; NÃO diz que o serviço" >&2
  echo "  que respondeu é o que grava. Suba o cluster local ou aponte para o seu:" >&2
  echo "    su postgres -c \"/usr/lib/postgresql/16/bin/pg_ctl -D /var/lib/postgresql/tocdata \\" >&2
  echo "      -o '-p 5433 -k /var/run/postgresql' -l /tmp/pg.log start\"" >&2
  echo "    export DATABASE_URL='$URL_PADRAO'" >&2
  if [[ $PERMITIR_MEMORIA -eq 0 ]]; then
    echo >&2
    echo "  Para medir o transporte DE PROPÓSITO sem banco, e receber o veredito carimbado" >&2
    echo "  como tal: scripts/check-conformidade-aph.sh $PORTA --permitir-memoria" >&2
    exit 3
  fi
  echo >&2
  echo "  ⚠ --permitir-memoria em vigor: seguindo contra alvo EM MEMÓRIA." >&2
  URL_DO_BANCO=""
  ORIGEM_DA_URL="nenhuma — medição em memória pedida explicitamente"
else
  SERVIDOR="$(printf '%s' "$SONDAGEM" | cut -d'|' -f2)"
  REVISAO="$(printf '%s' "$SONDAGEM" | cut -d'|' -f3)"
fi

# ── 3. sobe o serviço com ambiente EXPLÍCITO (não herdado) ────────────────────────────
REGISTRO="$(mktemp)"
env -u DATABASE_URL -u TOC_DB_SCHEMA \
  ${URL_DO_BANCO:+DATABASE_URL="$URL_DO_BANCO"} \
  PATH="$PATH" HOME="${HOME:-/root}" \
  "$API/.venv/bin/uvicorn" --factory toc_api.http.app:criar_app \
  --port "$PORTA" --log-level warning > "$REGISTRO" 2>&1 &
SERVICO=$!
trap 'kill "$SERVICO" 2>/dev/null; rm -f "$REGISTRO"' EXIT

for _ in $(seq 1 40); do
  if curl -sf "http://localhost:$PORTA/saude" > /dev/null 2>&1; then break; fi
  sleep 0.25
done
SAUDE="$(curl -s "http://localhost:$PORTA/saude" 2>/dev/null)"
if [[ -z "$SAUDE" ]]; then
  echo "✗ o serviço não subiu na porta $PORTA:" >&2
  cat "$REGISTRO" >&2
  exit 2
fi

campo() { printf '%s' "$SAUDE" | node -e '
  let bruto=""; process.stdin.on("data",d=>bruto+=d).on("end",()=>{
    try { const s=JSON.parse(bruto); const v=s[process.argv[1]]; console.log(v===null||v===undefined?"(ausente)":String(v)); }
    catch { console.log("(saude ilegível)"); }
  });' "$1"; }

PERSISTENCIA="$(campo persistencia)"
IDENTIDADE="$(campo identidade)"
GERACAO="$(campo geracao)"
ADMISSAO="$(campo admissao)"
AMBIENTE="$(campo ambiente)"
BANCO="$(campo banco)"

# ── 4. a declaração: o que este verde examinou, antes de haver verde ──────────────────
echo
echo "O QUE ESTE PORTÃO MEDIU (regra R2 — verde que não declara o alvo não é evidência):"
echo "  · alvo ................. http://localhost:$PORTA  (serviço subido por este script)"
echo "  · persistência ......... $PERSISTENCIA            (exigida: postgres)"
echo "  · banco ................ $BANCO"
echo "  · cadeia ............... $ORIGEM_DA_URL"
if [[ "$ESTADO_DO_BANCO" == "DE_PE" ]]; then
echo "  · servidor ............. $SERVIDOR"
echo "  · migração (alembic) ... $REVISAO"
fi
echo "  · identidade ........... $IDENTIDADE"
echo "  · admissão ............. $ADMISSAO"
echo "  · ambiente ............. $AMBIENTE"
echo "  · geração .............. $GERACAO"
echo "  · natureza do turno .... ENLATADO E DETERMINÍSTICO — não há provedor de modelo"
echo "      Este produto não chama provedor de inteligência artificial nenhum: a decisão é o"
echo "      ADR 0007 (assistência só pela fundação, por catálogo de ações governadas). O turno"
echo "      que a suíte mede é produzido por passos declarados no serviço, e o roteamento é"
echo "      busca por palavra do catálogo — não é classificação por modelo."
echo "      A suíte também é caixa-preta e roda SEM grant: o principal é anônimo, o catálogo"
echo "      composto é vazio e nenhum caso de uso do domínio é construído no turno medido."
echo "      Logo estes 11 checks medem o FIO (enquadramento SSE, seq, replay, cancelamento,"
echo "      envelope de erro, snapshot) — nunca a qualidade de uma resposta gerada, nem a"
echo "      persistência dos agregados, que quem mede é a suíte de integração (pytest -m"
echo "      integracao, contra o mesmo PostgreSQL)."
echo
echo "  /saude na íntegra: $SAUDE"
echo

# ── 5. o portão recusa alvo em memória ────────────────────────────────────────────────
if [[ "$PERSISTENCIA" != "postgres" ]]; then
  if [[ $PERMITIR_MEMORIA -eq 0 ]]; then
    echo "✗ RECUSADO — alvo com persistência \`$PERSISTENCIA\`, e o exigido é \`postgres\`." >&2
    echo "  A suíte devolveria 11/11 assim mesmo, e é justamente por isso que o portão para:" >&2
    echo "  um verde de transporte contra um alvo em memória se lê, no relatório, como se o" >&2
    echo "  serviço inteiro tivesse sido medido. Rode com o banco de pé (veja acima) ou peça" >&2
    echo "  --permitir-memoria para receber o veredito carimbado." >&2
    exit 3
  fi
  echo "⚠⚠ AVISO — MEDINDO ALVO EM MEMÓRIA (\`persistencia: $PERSISTENCIA\`), a pedido de"
  echo "   --permitir-memoria. O que sair daqui é evidência sobre o FIO e sobre mais nada."
  echo "   NÃO cole este resultado num qa-report.md como conformidade do serviço."
  echo
fi

cd "$SUITE" || exit 2
node --preserve-symlinks --preserve-symlinks-main conformidade/suite.mjs "http://localhost:$PORTA"
CODIGO=$?

echo
if [[ $CODIGO -ne 0 ]]; then
  echo "✗ NÃO APTO — leia o veredito acima; nenhum check foi pulado." >&2
  exit 1
fi
if [[ "$PERSISTENCIA" != "postgres" ]]; then
  echo "⚠ APTO nos 11 checks executáveis — MAS contra alvo em memória: vale para o fio, não"
  echo "  para o serviço. Um 11/11 assim não fecha ciclo."
  exit 1
fi
echo "✓ APTO nos 11 checks executáveis, sem perfil de adaptação —"
echo "  contra alvo com persistencia=$PERSISTENCIA, banco=$BANCO, migração $REVISAO,"
echo "  identidade=$IDENTIDADE, turno enlatado e determinístico (sem provedor de modelo)."
