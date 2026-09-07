#!/usr/bin/env bash
# mutacao-m5.sh — TAIL:mutation do ciclo 010: a suíte do M5 sabe reprovar?
#
# Siglas, uma vez: **M5** — Estratégia & Táticas · **S&T** — Estratégia & Táticas
# (*Strategy & Tactics*) · **RN/RF** — regra de negócio / requisito funcional da spec 010.
#
# ── Por que este script existe ────────────────────────────────────────────────────────
#
# Um teste verde não prova que ele sabe ficar vermelho. A `tasks.md` do ciclo 010 cobra
# mutação exatamente sobre as quatro funções **cuja falha silenciosa reintroduz os defeitos
# medidos da linhagem**:
#
#   1. a numeração (`numeracao`) — o defeito F-05: número digitado à mão, sem validação;
#   2. a renumeração local (`renumerar`) — o portão executável do roadmap;
#   3. a invariante de árvore estrita (`mover_passo`) — o defeito F-03: aresta livre;
#   4. o recorte da exclusão (`excluir_subarvore`) — o defeito F-07, que descartava todos
#      os passos MENOS o excluído (`tocbuilderv3/services/mockApiService.ts:521`).
#
# Cada mutação abaixo é uma versão plausível-e-errada dessas funções. A suíte de domínio do
# M5 tem de **ficar vermelha** em todas. Uma mutação sobrevivente é um buraco de cobertura
# com nome e endereço, e o script diz qual é.
#
# ── Como ele não estraga o repositório ────────────────────────────────────────────────
#
# O arquivo é copiado para um `mktemp -d` ANTES de qualquer mutação, e restaurado por
# `trap` em toda saída — inclusive interrupção. No fim, o `sha256` do arquivo é comparado
# com o de antes, e o script sai diferente de zero se a restauração não bater.
#
# Uso: scripts/tests/mutacao-m5.sh
# Saída: 0 = todas as mutações mortas · 1 = alguma sobreviveu · 2 = ambiente não montado.
set -uo pipefail

RAIZ="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
API="$RAIZ/apps/api"
ALVO="$API/src/toc_api/dominio/snt.py"
SUITE=(tests/dominio/test_numeracao.py tests/dominio/test_snt.py
       tests/dominio/test_premissas_do_passo.py tests/dominio/test_status_do_passo.py
       tests/dominio/test_pendencias.py)

[[ -f "$ALVO" ]] || { echo "✗ $ALVO não existe — o M5 não está neste repositório." >&2; exit 2; }
[[ -x "$API/.venv/bin/python" ]] || { echo "✗ ambiente Python do serviço ausente." >&2; exit 2; }

TMP="$(mktemp -d)"
cp "$ALVO" "$TMP/original.py"
ANTES="$(sha256sum "$ALVO" | cut -d' ' -f1)"
restaurar() { cp "$TMP/original.py" "$ALVO"; }
trap 'restaurar; rm -rf "$TMP"' EXIT

echo "── Mutação do M5: a suíte da árvore de Estratégia & Táticas sabe reprovar? ──"
echo "  alvo: apps/api/src/toc_api/dominio/snt.py"
echo "  suíte: ${#SUITE[@]} arquivos de teste de domínio"

# nome · função tocada · comando `sed` da mutação (sobre o arquivo real, já copiado)
MUTACOES=(
  "numeracao-comeca-em-zero|numeracao|s/for indice, filho in enumerate(estrutura.get(pai, ()), start=1):/for indice, filho in enumerate(estrutura.get(pai, ()), start=0):/"
  "numeracao-sem-prefixo-do-pai|numeracao|s|numero = f\"{prefixo}{SEPARADOR}{indice}\" if prefixo else str(indice)|numero = str(indice)|"
  "numeracao-nao-desce-para-os-filhos|numeracao|s/^        _numerar_sob(estrutura, pai=filho, prefixo=numero, numeros=numeros)$/        pass/"
  "renumerar-ignora-o-pai-afetado|renumerar|s/^        _numerar_sob(estrutura, pai=pai, prefixo=novos\\[pai\\], numeros=novos)$/        pass/"
  "renumerar-nao-descarta-o-que-saiu|renumerar|s/^    novos = {k: v for k, v in numeros.items() if k in _todos_os_nos(estrutura)}$/    novos = dict(numeros)/"
  "mover-aceita-a-propria-subarvore|mover_passo|s/^        if novo_pai_id is not None and novo_pai_id in self.subarvore(no_id):$/        if False:/"
  "exclusao-tira-so-o-passo|excluir_subarvore|s/^        alvos = self.subarvore(no_id)$/        alvos = (no_id,)/"
  "exclusao-mantem-so-o-excluido|excluir_subarvore|s/^        self._estrutura\\[pai\\] = tuple(x for x in self._estrutura.get(pai, ()) if x != no_id)$/        self._estrutura[pai] = tuple(x for x in self._estrutura.get(pai, ()) if x == no_id)/"
)

mortas=0
sobreviventes=()

for entrada in "${MUTACOES[@]}"; do
  IFS='|' read -r nome funcao _ <<< "$entrada"
  expressao="${entrada#*|*|}"
  restaurar
  if ! sed -i "$expressao" "$ALVO"; then
    echo "  ✗ $nome — a mutação não pôde ser aplicada (a linha alvo mudou de forma?)" >&2
    sobreviventes+=("$nome (não aplicada)")
    continue
  fi
  if cmp -s "$ALVO" "$TMP/original.py"; then
    echo "  ✗ $nome — o \`sed\` não mudou nada: a mutação não existe, e o verde é vazio" >&2
    sobreviventes+=("$nome (sem efeito)")
    continue
  fi
  saida="$(cd "$API" && PATH="$API/.venv/bin:$PATH" python -m pytest -q -p no:cacheprovider \
           "${SUITE[@]}" 2>&1)"
  codigo=$?
  if [[ $codigo -eq 0 ]]; then
    echo "  ✗ SOBREVIVEU  $nome  (função: $funcao) — a suíte passou com o defeito dentro" >&2
    sobreviventes+=("$nome")
  else
    quantos="$(printf '%s' "$saida" | grep -Eo '[0-9]+ failed' | head -1)"
    echo "  ✓ morta      $nome  (função: $funcao) — ${quantos:-suíte vermelha}"
    mortas=$((mortas + 1))
  fi
done

restaurar
DEPOIS="$(sha256sum "$ALVO" | cut -d' ' -f1)"

echo
echo "  mutações aplicadas: ${#MUTACOES[@]}  ·  mortas: $mortas  ·  sobreviventes: ${#sobreviventes[@]}"
echo "  funções cobertas: numeracao · renumerar · mover_passo · excluir_subarvore"
if [[ "$ANTES" != "$DEPOIS" ]]; then
  echo "✗ o arquivo NÃO voltou ao estado original (sha256 $ANTES → $DEPOIS)." >&2
  exit 1
fi
echo "  arquivo restaurado: sha256 confere ($ANTES)"

if (( ${#sobreviventes[@]} > 0 )); then
  printf '✗ mutação sobrevivente: %s\n' "${sobreviventes[@]}" >&2
  exit 1
fi
echo
echo "✓ as ${#MUTACOES[@]} mutações morreram: a suíte do M5 reprova cada defeito que ela existe para ver."
