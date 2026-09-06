#!/usr/bin/env bash
# check-raiz-do-agregado.sh — a chave da raiz do agregado não sai do domínio.
#
# Siglas, uma vez: **DDD** — *Domain-Driven Design* (Design Orientado a Domínio) ·
# **M1** — Núcleo de Diagramas Lógicos · **ARA** — Árvore da Realidade Atual ·
# **NC** — Nuvem de Conflito · **TOC** — Teoria das Restrições.
#
# ── O defeito que este portão existe para não deixar voltar ──────────────────────────
#
# As ferramentas da TOC são raízes de agregado POR COMPOSIÇÃO: `ProjetoARA` e
# `NuvemDeConflito` contêm um `Projeto` do M1 e acrescentam as invariantes da ferramenta
# — as 5 entidades e 7 arestas que nascem juntas e não se destroem (RN-01 da spec 007), o
# exame que nasce com todo elo da ARA (RF-22 da spec 005), a ficha arquivada quando um
# Efeito Indesejável some (RF-05), o conector sem referência órfã (RN-11).
#
# Enquanto o `Projeto` contido aceitava mutação de quem o carregasse cru, havia DUAS
# portas para o mesmo estado e as invariantes moravam numa só. Criar uma nuvem por
# `POST /toc/nc/projetos` e apagar a aresta D↯D′ por `DELETE /toc/projetos/{id}/arestas/
# {id}` respondia `204 No Content`, e a nuvem sumia da leitura logo depois — 404 sobre um
# projeto que continuava no banco.
#
# A correção não foi um `if` na rota: `Projeto._exigir_raiz` recusa toda mutação de grafo
# de um projeto de ferramenta, e a ÚNICA maneira de destravá-la é o contextmanager
# `Projeto.sob_a_raiz()`, que a raiz usa por dentro. Se `sob_a_raiz` for chamado de fora
# de `apps/api/src/toc_api/dominio/`, a porta dos fundos volta a existir — com outro nome
# e a mesma consequência.
#
# ── O que ele verifica, exatamente ───────────────────────────────────────────────────
#
#   1. `sob_a_raiz` só é CHAMADO dentro de `dominio/` (o teste que o exercita é a
#      exceção declarada: teste de domínio mora em `tests/dominio/`);
#   2. `_exigir_raiz` é chamado por TODAS as oito mutações de grafo do `Projeto` —
#      um portão que não conta quantas guarda responderia verde sobre sete;
#   3. cada raiz de ferramenta se registra em `registrar_raiz_de_ferramenta`.
#
# Regra R2 do `CLAUDE.md` (portão verde diz quanto examinou): a saída imprime quantos
# arquivos foram varridos, quantas guardas foram encontradas e quantas eram esperadas.
#
# Uso: scripts/check-raiz-do-agregado.sh [raiz]   (padrão: a raiz do repositório)
# Saída: 0 conforme · 1 violação encontrada · 2 ambiente não montado.
set -uo pipefail

RAIZ="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
FONTE="$RAIZ/apps/api/src/toc_api"
DOMINIO="$FONTE/dominio"
TESTES="$RAIZ/apps/api/tests"

#: As oito mutações de grafo do `Projeto`. Escrita à mão de propósito: derivar a lista do
#: próprio arquivo faria o portão concordar com quem esquecesse a guarda.
MUTACOES=(adicionar_no editar_no mover_no recolher_no excluir_no ligar editar_aresta excluir_aresta)

echo "── Raiz do agregado: a chave não sai do domínio (DDD) ──"

if [[ ! -d "$FONTE" ]]; then
  echo "✗ $FONTE não existe — o serviço não está neste repositório." >&2
  exit 2
fi

FALHOU=0

# -- 1. quem chama `sob_a_raiz` --------------------------------------------------------
VARRIDOS="$(find "$FONTE" "$TESTES" -name '*.py' -not -path '*/__pycache__/*' | wc -l | tr -d ' ')"
echo "  arquivos Python varridos: $VARRIDOS"

FORA="$(grep -rn 'sob_a_raiz' "$FONTE" "$TESTES" \
        --include='*.py' \
        | grep -v "^$DOMINIO/" \
        | grep -v "^$TESTES/dominio/" || true)"

if [[ -n "$FORA" ]]; then
  echo "✗ \`sob_a_raiz\` alcançado fora de dominio/ — a porta dos fundos do agregado voltou:" >&2
  echo "$FORA" | sed 's/^/    /' >&2
  echo "  O caminho NÃO é destravar o núcleo: é dar à raiz da ferramenta a operação que" >&2
  echo "  falta (ex.: ProjetoARA.excluir_aresta) e chamar a raiz." >&2
  FALHOU=1
else
  DENTRO="$(grep -rc 'sob_a_raiz' "$DOMINIO" --include='*.py' | grep -v ':0$' | wc -l | tr -d ' ')"
  echo "  ✓ \`sob_a_raiz\` aparece só em dominio/ (em $DENTRO arquivo(s)) e no teste do domínio"
fi

# -- 2. toda mutação de grafo tem guarda ----------------------------------------------
PROJETO="$DOMINIO/projeto.py"
SEM_GUARDA=()
for operacao in "${MUTACOES[@]}"; do
  grep -q "_exigir_raiz(\"$operacao\")" "$PROJETO" || SEM_GUARDA+=("$operacao")
done
ENCONTRADAS=$(( ${#MUTACOES[@]} - ${#SEM_GUARDA[@]} ))
echo "  guardas \`_exigir_raiz\` encontradas: $ENCONTRADAS de ${#MUTACOES[@]} mutações de grafo"
if (( ${#SEM_GUARDA[@]} > 0 )); then
  echo "✗ mutação de grafo sem guarda de raiz: ${SEM_GUARDA[*]}" >&2
  FALHOU=1
fi

# -- 3. cada raiz de ferramenta se registra -------------------------------------------
REGISTROS="$(grep -rn 'registrar_raiz_de_ferramenta(' "$DOMINIO" --include='*.py' \
             | grep -v 'def registrar_raiz_de_ferramenta' || true)"
QUANTAS="$(printf '%s' "$REGISTROS" | grep -c . || true)"
echo "  raízes de ferramenta registradas: $QUANTAS"
printf '%s\n' "$REGISTROS" | sed 's/^/    /'
if [[ "$QUANTAS" -lt 2 ]]; then
  echo "✗ esperava ao menos duas raízes registradas (ARA e NC); achei $QUANTAS." >&2
  FALHOU=1
fi

echo
if [[ $FALHOU -ne 0 ]]; then
  echo "✗ a raiz do agregado deixou de ser o único caminho para o estado dela." >&2
  exit 1
fi
echo "✓ operação só pela raiz: $ENCONTRADAS guardas, $QUANTAS raízes, $VARRIDOS arquivos varridos."
