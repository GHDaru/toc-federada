#!/usr/bin/env bash
# run-sabotagem.sh — the second law of `verifiable-dod`: a check that nothing can make fail
# is not a check. Every gate of this project is run twice — once against a VALID fixture
# (it must pass) and once per declared sabotage (it must fail, and fail for the right
# reason).
#
# Por que as duas metades: um portão que reprova tudo é tão inútil quanto um que aprova
# tudo, e a irmã `gestaodeprioridades` já pagou pelas duas pontas — quatro portões verdes
# que não olhavam para o que se supunha que olhassem (regra R2), e um portão que respondia
# verde sobre 43 links enquanto o arquivo citado não existia (regra R4). Por isso aqui:
#
#   1. **Base verde** — cada fixture em `scripts/tests/sabotagem/<portão>/` é uma entrada
#      VÁLIDA mínima. Se o portão reprovar a base, ele não sabe reconhecer o certo.
#   2. **Sabotagem vermelha, e vermelha pelo motivo declarado** — cada mutação é uma linha
#      da tabela abaixo, com o **trecho que a saída tem de conter**. Só "saiu ≠ 0" não
#      basta: um portão pode reprovar por acidente (um caminho errado, um arquivo faltando)
#      e o teste passaria sem nada ter sido provado. Exigir o motivo é o que impede a suíte
#      de ser leniente.
#
# A mutação nunca toca o repositório: cada execução copia o fixture para um diretório
# temporário e sabota a cópia (`mktemp -d`, apagado no fim).
#
# Uso:  scripts/tests/run-sabotagem.sh [-v]      (-v mostra a saída de cada execução)
set -uo pipefail

RAIZ="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
FIXTURES="$RAIZ/scripts/tests/sabotagem"
VERBOSE=0
[[ "${1:-}" == "-v" ]] && VERBOSE=1

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

# ── as bases válidas ────────────────────────────────────────────────────────────
# portão · fixture (par por linha)
BASES=(
  "scripts/check-caminhos.sh"       "caminhos"
  "scripts/check-adrs-sucessao.sh"  "adrs-sucessao"
  "scripts/check-rounds.sh"         "rounds"
  "scripts/check-specs.sh"          "specs"
)

# ── as sabotagens ───────────────────────────────────────────────────────────────
# Cinco campos por sabotagem, nesta ordem:
#   portão · fixture · nome · mutação (roda com cwd = cópia) · trecho exigido na saída
SABOTAGENS=(
  # --- check-caminhos.sh (regra R4) ---
  "scripts/check-caminhos.sh" "caminhos" "caminho-nosso-inexistente"
  "sed -i 's,docs/produto/visao.md,docs/produto/inexistente.md,' docs/jornada.md"
  "caminho(s) citado(s) que não existem"

  "scripts/check-caminhos.sh" "caminhos" "isencao-nao-declarada"
  "sed -i 's,gestaodeprioridades/docs/produto/rounds.md,repo-desconhecido/docs/rounds.md,' docs/jornada.md"
  "caminho(s) citado(s) que não existem"

  # --- check-adrs-sucessao.sh (regra R5) ---
  "scripts/check-adrs-sucessao.sh" "adrs-sucessao" "antigo-sem-superseded-by"
  "sed -i 's,^- \*\*Status\*\*:.*,- **Status**: Aceita,' docs/adr/0001-decisao-base.md"
  'não declara "Superseded by" nomeando 0002'

  "scripts/check-adrs-sucessao.sh" "adrs-sucessao" "sem-campo-principios-tocados"
  "sed -i '/Princípios tocados/d' docs/adr/0002-decisao-que-sucede.md"
  'não declara o campo "- **Princípios tocados**:"'

  "scripts/check-adrs-sucessao.sh" "adrs-sucessao" "sem-campo-sucede"
  "sed -i '/^- \*\*Sucede\*\*:/d' docs/adr/0002-decisao-que-sucede.md"
  'não declara o campo "- **Sucede**:"'

  "scripts/check-adrs-sucessao.sh" "adrs-sucessao" "fora-do-registro-jsonl"
  "sed -i '/adr-0002/d' docs/records/decisoes.jsonl"
  "não tem linha em docs/records/decisoes.jsonl"

  "scripts/check-adrs-sucessao.sh" "adrs-sucessao" "fora-do-indice"
  "sed -i '/0002-decisao-que-sucede.md/d' docs/adr/README.md"
  "não tem linha em docs/adr/README.md"

  "scripts/check-adrs-sucessao.sh" "adrs-sucessao" "sucede-adr-inexistente"
  "sed -i 's,\*\*Sucede\*\*: ADR 0001,**Sucede**: ADR 0009,' docs/adr/0002-decisao-que-sucede.md"
  "declara suceder o ADR 0009, que não existe"

  # --- check-rounds.sh ---
  "scripts/check-rounds.sh" "rounds" "campo-obrigatorio-ausente"
  "sed -i '/Aptidão executável/d' docs/produto/rounds.md"
  'não declara o campo obrigatório "- **Aptidão executável**:"'

  "scripts/check-rounds.sh" "rounds" "dependencia-circular"
  "sed -i 's,\*\*Depende de\*\*: nenhum,**Depende de**: 003,' docs/produto/rounds.md"
  "ciclo de dependência entre rounds"

  "scripts/check-rounds.sh" "rounds" "dependencia-inexistente"
  "sed -i 's,\*\*Depende de\*\*: 002,**Depende de**: 099,' docs/produto/rounds.md"
  "depende do round 099, que não tem seção"

  "scripts/check-rounds.sh" "rounds" "defeito-sem-destino"
  "sed -i '/^- \*\*D-02 · /d' docs/produto/rounds.md"
  "não foi alocado a round algum"

  "scripts/check-rounds.sh" "rounds" "defeito-em-dois-destinos"
  "sed -i 's,\*\*Defeitos\*\*: nenhum,**Defeitos**: **D-01** outra vez — nenhum,' docs/produto/rounds.md"
  "está alocado em 2 lugares"

  # --- check-specs.sh ---
  "scripts/check-specs.sh" "specs" "artefato-do-ciclo-ausente"
  "rm specs/004-modulo-sintetico/qa-report.md"
  "falta qa-report.md"

  "scripts/check-specs.sh" "specs" "secao-obrigatoria-renomeada"
  "sed -i 's,^## Fontes$,## Referências,' specs/004-modulo-sintetico/spec.md"
  'falta a seção obrigatória "## Fontes"'

  "scripts/check-specs.sh" "specs" "sem-requisito-de-interface"
  "sed -i '/^RI-01:/d' specs/004-modulo-sintetico/spec.md"
  "nenhum RI- (requisito de interface)"

  "scripts/check-specs.sh" "specs" "sem-status"
  "sed -i '/^- \*\*Status\*\*:/d' specs/004-modulo-sintetico/spec.md"
  'não declara "- **Status**:"'

  "scripts/check-specs.sh" "specs" "dod-sem-coluna-de-verificacao"
  "sed -i 's,Verificação executável,Observação,' specs/004-modulo-sintetico/spec.md"
  'a DoD não tem a coluna "Verificação executável"'

  "scripts/check-specs.sh" "specs" "plano-com-uma-tabela-so"
  "sed -i 's,^### Project Constitution Check.*,### Conformidade do projeto,' specs/004-modulo-sintetico/plan.md"
  'esperava 1 cabeçalho "Project Constitution Check"'

  "scripts/check-specs.sh" "specs" "linha-de-principio-vazia"
  "sed -i 's,^. P4. TDD .*,| P4. TDD | ✅ |,' specs/004-modulo-sintetico/plan.md"
  "célula de conformidade vazia"

  "scripts/check-specs.sh" "specs" "artefato-condicional-nao-declarado"
  "sed -i 's,ART:checklist=no,decidido adiante,' specs/004-modulo-sintetico/plan.md"
  'não declara `ART:checklist='

  "scripts/check-specs.sh" "specs" "cauda-incompleta"
  "sed -i 's,TAIL:mutation,revisão por mutação,' specs/004-modulo-sintetico/tasks.md"
  'não carrega `TAIL:mutation`'
)

falhas=0
bases_ok=0
sabotagens_ok=0
n_bases=$(( ${#BASES[@]} / 2 ))
n_sabotagens=$(( ${#SABOTAGENS[@]} / 5 ))

ok()  { printf '  ✓ %s\n' "$1"; }
bad() { printf '  ✗ %s\n' "$1"; falhas=$((falhas + 1)); }

copia() {  # $1 = fixture -> imprime o caminho da cópia
  local destino="$TMP/$1.$RANDOM"
  cp -r "$FIXTURES/$1" "$destino"
  printf '%s' "$destino"
}

echo "── Primeira metade: cada portão ACEITA a base válida ──"
for ((i = 0; i < ${#BASES[@]}; i += 2)); do
  portao="${BASES[i]}"; fixture="${BASES[i+1]}"
  if [[ ! -f "$RAIZ/$portao" ]]; then
    bad "$portao não existe"
    continue
  fi
  if [[ ! -d "$FIXTURES/$fixture" ]]; then
    bad "$portao: fixture scripts/tests/sabotagem/$fixture/ não existe"
    continue
  fi
  alvo="$(copia "$fixture")"
  saida="$(cd "$RAIZ" && bash "$portao" "$alvo" 2>&1)"
  codigo=$?
  [[ $VERBOSE -eq 1 ]] && printf '%s\n' "$saida"
  if [[ $codigo -eq 0 ]]; then
    ok "$(basename "$portao") aceita a base $fixture/ (saída 0)"
    bases_ok=$((bases_ok + 1))
  else
    bad "$(basename "$portao") REPROVA a própria base válida $fixture/ (saída $codigo) — um portão que reprova tudo não prova nada"
    printf '%s\n' "$saida" | sed 's/^/      /'
  fi
done

echo
echo "── Segunda metade: cada sabotagem faz o portão REPROVAR, pelo motivo declarado ──"
for ((i = 0; i < ${#SABOTAGENS[@]}; i += 5)); do
  portao="${SABOTAGENS[i]}"
  fixture="${SABOTAGENS[i+1]}"
  nome="${SABOTAGENS[i+2]}"
  mutacao="${SABOTAGENS[i+3]}"
  esperado="${SABOTAGENS[i+4]}"

  if [[ ! -f "$RAIZ/$portao" || ! -d "$FIXTURES/$fixture" ]]; then
    bad "$nome: portão ou fixture ausente"
    continue
  fi

  alvo="$(copia "$fixture")"
  if ! ( cd "$alvo" && eval "$mutacao" ) 2>/dev/null; then
    bad "$nome: a mutação não pôde ser aplicada — a sabotagem não chegou a acontecer"
    continue
  fi

  saida="$(cd "$RAIZ" && bash "$portao" "$alvo" 2>&1)"
  codigo=$?
  [[ $VERBOSE -eq 1 ]] && printf '%s\n' "$saida"

  if [[ $codigo -eq 0 ]]; then
    bad "$nome: $(basename "$portao") saiu 0 sobre a base sabotada — o portão não vê o defeito que existe para ver"
  elif ! printf '%s' "$saida" | grep -qF -- "$esperado"; then
    bad "$nome: $(basename "$portao") reprovou (saída $codigo) mas por OUTRO motivo; esperava a saída conter: $esperado"
    printf '%s\n' "$saida" | sed 's/^/      /'
  else
    ok "$nome → $(basename "$portao") saiu $codigo pelo motivo declarado"
    sabotagens_ok=$((sabotagens_ok + 1))
  fi
done

# Regra R2: o verde diz QUANTO examinou.
echo
echo "── Sabotagem: quanto foi examinado ──"
echo "  portões cobertos: $n_bases  ·  bases válidas aceitas: $bases_ok/$n_bases"
echo "  sabotagens declaradas: $n_sabotagens  ·  reprovadas pelo motivo certo: $sabotagens_ok/$n_sabotagens"
echo "  cada sabotagem roda sobre uma cópia em $TMP — o repositório não é tocado"

if [[ $falhas -ne 0 ]]; then
  echo
  echo "✗ $falhas falha(s) na suíte de sabotagem." >&2
  exit 1
fi
echo
echo "✓ os $n_bases portões aceitam a base válida e reprovam as $n_sabotagens sabotagens,"
echo "  cada uma pelo motivo que a tabela declara."
