#!/usr/bin/env bash
# ensaio-de-restauracao.sh — a unidade de restauração, ENSAIADA (spec 011, F8.1.3).
#
# Siglas, uma vez: **RPO** — *Recovery Point Objective* (objetivo de ponto de recuperação:
# quanto trabalho se aceita perder) · **RTO** — *Recovery Time Objective* (objetivo de
# tempo de recuperação: quanto tempo se aceita ficar fora do ar) · **PITR** —
# *Point-In-Time Recovery* (recuperação a um ponto no tempo) · **ARA** — Árvore da
# Realidade Atual · **NC** — Nuvem de Conflito · **HTTP** — *HyperText Transfer Protocol*
# · **ADR** — *Architecture Decision Record* · **S3** — o protocolo de armazenamento de
# objetos.
#
# ── Por que este script existe ───────────────────────────────────────────────────────
#
# A constituição da fundação (`GHDaru/ghdaru/.specify/memory/constitution.md:253-261`,
# Princípio XII) diz a frase que este arquivo executa: **"backup é o que já foi restaurado
# com sucesso em outro lugar; cópia no mesmo armazenamento e na mesma conta é
# conveniência, não apólice"**. E a medição do ciclo 003 mostrou o buraco:
# `grep -rniE "backup|restaura|point-in-time" specs/003-esqueleto-federado/` devolve DUAS
# linhas, e nenhuma das duas é restauração de banco ensaiada — uma é rollback de
# implantação, a outra é "branch Neon criado antes de aplicar".
#
# Uma cópia que ninguém restaurou é uma hipótese. Este script transforma a hipótese em
# fato, e imprime o fato.
#
# ── O que ele faz, em ordem ──────────────────────────────────────────────────────────
#
#   1. **semeia** uma base sintética num esquema próprio do banco de origem, PELA API
#      (comando explícito — RF-05, nunca efeito colateral de tabela vazia);
#   2. **marca o instante alvo** — o ponto no tempo a que a restauração devolve;
#   3. **despeja** com `pg_dump`, formato `custom`;
#   4. **restaura num banco NOVO** (`pg_restore`), que é o "outro lugar" da frase;
#   5. **compara** tabela a tabela: contagem de linhas e resumo `md5` do conteúdo dos
#      projetos e dos nós — porque contagem igual com conteúdo trocado passaria despercebida;
#   6. **sobe a aplicação de verdade** (`uvicorn --factory`, com a admissão do §B.4
#      completa) contra o destino restaurado e pede `GET /toc/projetos`;
#   7. **imprime o relatório**: instante alvo, durações, tamanho, e **o que NÃO volta**.
#
# Nenhuma credencial entra na saída (P7, RNF-10): o cluster local autentica por socket
# confiado e a cadeia impressa é redigida.
#
# Uso:
#   scripts/ensaio-de-restauracao.sh                 # ensaio completo, limpa no fim
#   scripts/ensaio-de-restauracao.sh --manter        # deixa o banco restaurado de pé
#   PROJETOS=10 scripts/ensaio-de-restauracao.sh     # semeia mais
#
# Saída: 0 restauração conferida · 1 divergência · 2 ambiente não montado.
set -uo pipefail

RAIZ="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
API="$RAIZ/apps/api"
VENV="$API/.venv/bin"
MANTER=0
[[ "${1:-}" == "--manter" ]] && MANTER=1
PROJETOS="${PROJETOS:-3}"

URL_PADRAO="postgresql+psycopg://toc@/toc_federada?host=/var/run/postgresql&port=5433"
URL="${DATABASE_URL:-$URL_PADRAO}"

# A cadeia do SQLAlchemy não serve para `psql`: extraem-se as partes.
USUARIO="$(printf '%s' "$URL" | sed -n 's|.*://\([^:@/]*\).*|\1|p')"
BANCO_ORIGEM="$(printf '%s' "$URL" | sed -n 's|.*/\([^/?]*\)?.*|\1|p')"
SOCKET="$(printf '%s' "$URL" | sed -n 's|.*host=\([^&]*\).*|\1|p')"
PORTA="$(printf '%s' "$URL" | sed -n 's|.*port=\([0-9]*\).*|\1|p')"
PSQL=(psql -h "$SOCKET" -p "$PORTA" -U "$USUARIO" -X -q -A -t)

CARIMBO="$(date -u +%Y%m%d%H%M%S)"
ESQUEMA="ensaio_$CARIMBO"
BANCO_DESTINO="toc_ensaio_$CARIMBO"
DESPEJO="$(mktemp -d)/toc_${CARIMBO}.dump"
PORTA_HTTP="${PORTA_HTTP:-8123}"

echo "── Ensaio de restauração — unidade de restauração da aplicação (F8.1.3) ──"
echo "  banco de origem: $BANCO_ORIGEM · esquema semeado: $ESQUEMA"
echo "  destino da restauração: $BANCO_DESTINO (banco NOVO, criado agora)"
echo

for ferramenta in psql pg_dump pg_restore createdb dropdb; do
  command -v "$ferramenta" > /dev/null 2>&1 || {
    echo "✗ $ferramenta não está no PATH — sem cliente do PostgreSQL não há ensaio." >&2
    exit 2
  }
done
[[ -x "$VENV/python" ]] || { echo "✗ ambiente Python do serviço ausente em $VENV" >&2; exit 2; }

limpar() {
  if [[ $MANTER -eq 1 ]]; then
    echo
    echo "  (--manter) o banco $BANCO_DESTINO e o esquema $ESQUEMA continuam de pé."
    return
  fi
  dropdb -h "$SOCKET" -p "$PORTA" -U "$USUARIO" --if-exists "$BANCO_DESTINO" > /dev/null 2>&1
  "${PSQL[@]}" -d "$BANCO_ORIGEM" -c "DROP SCHEMA IF EXISTS \"$ESQUEMA\" CASCADE" > /dev/null 2>&1
  rm -rf "$(dirname "$DESPEJO")"
}
trap limpar EXIT

# ── 1. semeadura (comando explícito — RF-05) ────────────────────────────────────────
echo "[1/7] migrando e semeando a base sintética no esquema de origem…"
INICIO_SEMEADURA="$(date +%s%3N)"
(
  cd "$API" && DATABASE_URL="$URL" TOC_DB_SCHEMA="$ESQUEMA" PATH="$VENV:$PATH" \
    alembic upgrade head
) > /tmp/ensaio-alembic.log 2>&1 || {
  echo "✗ a migração falhou; últimas linhas:" >&2
  tail -5 /tmp/ensaio-alembic.log >&2
  exit 1
}
SEMEADO="$(DATABASE_URL="$URL" TOC_DB_SCHEMA="$ESQUEMA" "$VENV/python" "$RAIZ/scripts/ensaio/semear.py" "$PROJETOS")" || {
  echo "✗ a semeadura falhou." >&2
  exit 1
}
FIM_SEMEADURA="$(date +%s%3N)"
echo "  $SEMEADO"
TOKEN_DO_ENSAIO="$(printf '%s' "$SEMEADO" | "$VENV/python" -c 'import json,sys; print(json.load(sys.stdin)["token"])')"
NOMES_NA_ORIGEM="$(printf '%s' "$SEMEADO" | "$VENV/python" -c 'import json,sys; print("\n".join(json.load(sys.stdin)["nomes"]))')"

# ── 2. o instante alvo ──────────────────────────────────────────────────────────────
INSTANTE_ALVO="$("${PSQL[@]}" -d "$BANCO_ORIGEM" -c "SELECT now() AT TIME ZONE 'UTC'")"
echo "[2/7] instante alvo da restauração (o ponto no tempo a que ela devolve): ${INSTANTE_ALVO}Z"

# ── 3. despejo ──────────────────────────────────────────────────────────────────────
echo "[3/7] despejando o banco de origem…"
INICIO_DESPEJO="$(date +%s%3N)"
pg_dump -h "$SOCKET" -p "$PORTA" -U "$USUARIO" -Fc -d "$BANCO_ORIGEM" -f "$DESPEJO" || {
  echo "✗ pg_dump falhou." >&2
  exit 1
}
FIM_DESPEJO="$(date +%s%3N)"
TAMANHO="$(du -h "$DESPEJO" | cut -f1)"
echo "  despejo: $TAMANHO em $(( FIM_DESPEJO - INICIO_DESPEJO )) ms"

# ── 4. restauração num destino separado ─────────────────────────────────────────────
echo "[4/7] restaurando em $BANCO_DESTINO…"
INICIO_RESTAURACAO="$(date +%s%3N)"
createdb -h "$SOCKET" -p "$PORTA" -U "$USUARIO" "$BANCO_DESTINO" || {
  echo "✗ não consegui criar o banco de destino." >&2
  exit 1
}
pg_restore -h "$SOCKET" -p "$PORTA" -U "$USUARIO" -d "$BANCO_DESTINO" "$DESPEJO" \
  > /tmp/ensaio-restore.log 2>&1
CODIGO_RESTORE=$?
FIM_RESTAURACAO="$(date +%s%3N)"
if [[ $CODIGO_RESTORE -ne 0 ]]; then
  echo "  pg_restore saiu $CODIGO_RESTORE; avisos:" >&2
  tail -5 /tmp/ensaio-restore.log >&2
fi
echo "  restauração: $(( FIM_RESTAURACAO - INICIO_RESTAURACAO )) ms"

# ── 5. o conteúdo bate? ─────────────────────────────────────────────────────────────
echo "[5/7] conferindo o conteúdo tabela a tabela…"
TABELAS="$("${PSQL[@]}" -d "$BANCO_ORIGEM" -c \
  "SELECT table_name FROM information_schema.tables WHERE table_schema='$ESQUEMA' ORDER BY table_name")"
DIVERGENTES=0
CONFERIDAS=0
LINHAS_TOTAIS=0
for tabela in $TABELAS; do
  origem="$("${PSQL[@]}" -d "$BANCO_ORIGEM" -c "SELECT count(*) FROM \"$ESQUEMA\".\"$tabela\"")"
  destino="$("${PSQL[@]}" -d "$BANCO_DESTINO" -c "SELECT count(*) FROM \"$ESQUEMA\".\"$tabela\"")"
  CONFERIDAS=$((CONFERIDAS + 1))
  LINHAS_TOTAIS=$((LINHAS_TOTAIS + origem))
  if [[ "$origem" != "$destino" ]]; then
    echo "  ✗ $tabela: origem $origem × destino $destino"
    DIVERGENTES=$((DIVERGENTES + 1))
  fi
done
echo "  tabelas conferidas: $CONFERIDAS · linhas na origem: $LINHAS_TOTAIS · divergências de contagem: $DIVERGENTES"

# Contagem igual com conteúdo trocado passaria despercebida: o resumo compara o TEXTO.
resumo() {  # $1 = banco
  "${PSQL[@]}" -d "$1" -c "
    SELECT md5(string_agg(linha, '|' ORDER BY linha)) FROM (
      SELECT p.id::text || ':' || p.nome || ':' || p.ferramenta || ':' ||
             coalesce(string_agg(n.titulo, ';' ORDER BY n.titulo), '') AS linha
      FROM \"$ESQUEMA\".projeto p
      LEFT JOIN \"$ESQUEMA\".no n ON n.projeto_id = p.id
      GROUP BY p.id, p.nome, p.ferramenta
    ) AS conteudo"
}
RESUMO_ORIGEM="$(resumo "$BANCO_ORIGEM")"
RESUMO_DESTINO="$(resumo "$BANCO_DESTINO")"
echo "  resumo md5 de projetos+nós — origem: ${RESUMO_ORIGEM:-vazio}"
echo "                              destino: ${RESUMO_DESTINO:-vazio}"
if [[ "$RESUMO_ORIGEM" != "$RESUMO_DESTINO" ]]; then
  echo "  ✗ o conteúdo de projetos e nós NÃO bate entre origem e destino." >&2
  DIVERGENTES=$((DIVERGENTES + 1))
fi

# ── 6. a aplicação de pé contra o destino restaurado ────────────────────────────────
# A aplicação sobe pela fábrica de PRODUÇÃO (`toc_api.http.arranque:aplicacao`), que
# verifica a admissão do §B.4 antes de abrir porta nenhuma. Duas notas sobre o ambiente
# passado abaixo, e as duas são deliberadas:
#
#   · `TOC_AMBIENTE=teste` e não um nome novo: só `desenvolvimento` e `teste` admitem
#     identidade de mentira (`apps/api/src/toc_api/infra/identidade/falso.py:35`), e
#     inventar um terceiro nome para o ensaio caber seria alargar uma trava de segurança
#     pelo motivo errado. O ensaio roda num banco descartável; ele é teste.
#   · `TOC_APP_CREDENTIAL` é obrigatória na admissão e é SEGREDO DE SERVIDOR (P7): o valor
#     é sintético, vive só dentro deste processo, e **não é impresso em lugar nenhum** —
#     a RNF-10 diz literalmente que as credenciais do ensaio "não são impressas na saída
#     colada".
echo "[6/7] subindo a aplicação contra o destino restaurado…"
URL_DESTINO="postgresql+psycopg://$USUARIO@/$BANCO_DESTINO?host=$SOCKET&port=$PORTA"
IDENTIDADES="{\"$TOKEN_DO_ENSAIO\":{\"inquilino_id\":\"instituicao-horizonte\",\"usuario_id\":\"papel-facilitadora\",\"capabilities\":[\"toc:read\",\"toc:write\"]}}"
INICIO_SUBIDA="$(date +%s%3N)"
(
  cd "$API" && \
  DATABASE_URL="$URL_DESTINO" \
  TOC_DB_SCHEMA="$ESQUEMA" \
  TOC_AMBIENTE="teste" \
  TOC_IDENTIDADES_FALSAS="$IDENTIDADES" \
  HOST_ORIGIN="https://hospedeiro.exemplo" \
  HOST_BASE_URL="https://hospedeiro.exemplo/api" \
  APP_ID="toc" \
  EMBED_URL="https://toc.exemplo/embed" \
  TOC_APP_CREDENTIAL="${TOC_APP_CREDENTIAL:-credencial-sintetica-do-ensaio}" \
  "$VENV/uvicorn" --factory toc_api.http.arranque:aplicacao \
    --host 127.0.0.1 --port "$PORTA_HTTP" --log-level warning
) > /tmp/ensaio-uvicorn.log 2>&1 &
PID_APP=$!

DE_PE=0
for _ in $(seq 1 40); do
  if curl -sf "http://127.0.0.1:$PORTA_HTTP/saude" > /tmp/ensaio-saude.json 2>/dev/null; then
    DE_PE=1
    break
  fi
  sleep 0.25
done
FIM_SUBIDA="$(date +%s%3N)"

if [[ $DE_PE -eq 0 ]]; then
  echo "  ✗ a aplicação NÃO subiu contra o destino restaurado. Últimas linhas:" >&2
  tail -10 /tmp/ensaio-uvicorn.log >&2
  kill "$PID_APP" 2> /dev/null
  DIVERGENTES=$((DIVERGENTES + 1))
else
  echo "  de pé em $(( FIM_SUBIDA - INICIO_SUBIDA )) ms · /saude: $(cat /tmp/ensaio-saude.json)"
  LISTA="$(curl -sf -H "Authorization: Bearer $TOKEN_DO_ENSAIO" \
    "http://127.0.0.1:$PORTA_HTTP/toc/projetos")"
  NOMES_NO_DESTINO="$(printf '%s' "$LISTA" | "$VENV/python" -c \
    'import json,sys; print("\n".join(sorted(p["nome"] for p in json.load(sys.stdin))))')"
  echo "  projetos lidos do destino restaurado: $(printf '%s' "$NOMES_NO_DESTINO" | grep -c .)"
  if [[ "$NOMES_NO_DESTINO" == "$NOMES_NA_ORIGEM" ]]; then
    echo "  ✓ a lista de projetos sintéticos aparece ÍNTEGRA (US-01)"
  else
    echo "  ✗ a lista de projetos diverge da origem:" >&2
    diff <(printf '%s' "$NOMES_NA_ORIGEM") <(printf '%s' "$NOMES_NO_DESTINO") >&2
    DIVERGENTES=$((DIVERGENTES + 1))
  fi
  kill "$PID_APP" 2> /dev/null
  wait "$PID_APP" 2> /dev/null
fi

# ── 7. o relatório ──────────────────────────────────────────────────────────────────
DURACAO_TOTAL=$(( FIM_RESTAURACAO - INICIO_DESPEJO ))
echo
echo "[7/7] relatório do ensaio"
echo "  instante alvo (ponto de recuperação): ${INSTANTE_ALVO}Z"
echo "  despejo: $(( FIM_DESPEJO - INICIO_DESPEJO )) ms · restauração: $(( FIM_RESTAURACAO - INICIO_RESTAURACAO )) ms"
echo "  duração medida do ciclo despejo→restauração: $DURACAO_TOTAL ms"
echo "  semeadura (preparo do ensaio, fora da conta acima): $(( FIM_SEMEADURA - INICIO_SEMEADURA )) ms"
echo "  tamanho do despejo: $TAMANHO"
echo
echo "  O QUE NÃO VOLTA COM O BANCO (declarado, não medido — RF-03):"
echo "    · arquivos em armazenamento compatível com S3 (anexos e capturas), que vivem"
echo "      fora do banco e têm apólice própria;"
echo "    · o que foi escrito DEPOIS do instante alvo — é o objetivo de ponto de"
echo "      recuperação em pessoa, e nenhuma restauração o inventa;"
echo "    · índices e estatísticas são RECONSTRUÍDOS pelo restore (não copiados): o"
echo "      primeiro acesso depois da restauração é mais lento até o \`ANALYZE\`;"
echo "    · sessões de embarque em curso (o grant é de uso único e TTL curto): quem"
echo "      estava dentro refaz o handshake."
echo
echo "  OBJETIVOS DECLARADOS (política do produto, a confirmar pelo Product Steward):"
echo "    · objetivo de ponto de recuperação (RPO): 5 minutos — o intervalo máximo de"
echo "      trabalho que se aceita perder;"
echo "    · objetivo de tempo de recuperação (RTO): 60 minutos — da decisão de restaurar"
echo "      até a aplicação de pé, com o ensaio acima como piso medido."
echo
echo "  UNIDADE DE RESTAURAÇÃO: esta aplicação tem banco PRÓPRIO (ADR 0002), e restaurá-la"
echo "  não rebobina nenhum outro produto da plataforma — foi por isso que o ensaio"
echo "  restaurou num banco NOVO e a aplicação subiu contra ELE, e não sobre a origem."

echo
if [[ $DIVERGENTES -ne 0 ]]; then
  echo "✗ ensaio de restauração com $DIVERGENTES divergência(s) — a cópia NÃO é apólice." >&2
  exit 1
fi
echo "✓ restauração ensaiada: $CONFERIDAS tabelas, $LINHAS_TOTAIS linhas, resumo de conteúdo idêntico,"
echo "  e a aplicação de pé contra o destino restaurado lendo a base sintética íntegra."
