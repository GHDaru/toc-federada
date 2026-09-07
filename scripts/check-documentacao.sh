#!/usr/bin/env bash
# check-documentacao.sh — cobertura ferramenta × verbete (spec 011, E8.4: RF-18, RF-22, RF-23).
#
# Siglas, uma vez: **ARA** — Árvore da Realidade Atual · **NC** — Nuvem de Conflito ·
# **ARF** — Árvore da Realidade Futura · **APR** — Árvore de Pré-Requisitos · **AT** —
# Árvore de Transição · **S&T** — Estratégia & Táticas · **TOC** — Teoria das Restrições ·
# **IA** — inteligência artificial · **CI** — integração contínua · **RF/RN** — requisito
# funcional / regra de negócio · **ADR** — *Architecture Decision Record*.
#
# ── O defeito que este portão existe para não deixar voltar ──────────────────────────
#
# A quarta geração da linhagem **acertou a forma** da documentação embutida e errou a
# cobertura: `tocbuilderv3/components/DocsView.tsx:21-26` declarava quatro tópicos
# (`intro`, `ara`, `nc`, `ai`) para as seis ferramentas de `types.ts:249-258`, e as outras
# quatro respondiam com a cadeia `"Esta ferramenta ainda não foi implementada."`
# (`locales/pt.ts:424`). Duas ferramentas documentadas de seis.
#
# Aqui a cobertura é regra (RN-04: "uma ferramenta só é considerada entregue quando tem
# verbete"), e regra sem portão é intenção.
#
# ── De onde vem o denominador, e por que isso é o coração do portão ─────────────────
#
# A lista de ferramentas **não** é digitada aqui nem lida do próprio acervo: ela é
# derivada do REGISTRO do serviço — as chamadas a `registrar_raiz_de_ferramenta(...)` no
# domínio (`apps/api/src/toc_api/dominio/`), que é a mesma declaração que faz o agregado
# recusar mutação fora da raiz. Uma ferramenta nova que se registre lá e não escreva
# verbete **derruba este portão sem ninguém precisar lembrar de atualizar uma lista**.
#
# Um portão que conferisse o acervo contra uma segunda lista responderia verde sobre duas
# ferramentas de seis — que é exatamente o que a linhagem fez.
#
# ── O que ele verifica ───────────────────────────────────────────────────────────────
#
#   1. **cobertura**: toda ferramenta registrada tem verbete, e todo verbete tem
#      ferramenta (verbete órfão também reprova), com AS DUAS CONTAGENS impressas (RF-23);
#   2. **procedência**: todo caminho citado por um verbete existe no repositório (RF-22) —
#      a mesma regra R4 do `CLAUDE.md`, aplicada ao acervo;
#   3. **âncora**: toda âncora que um componente declara (`ancora="…"`) existe no verbete
#      da ferramenta que ele nomeia (RF-20) — âncora torta abre o painel no lugar errado,
#      em silêncio;
#   4. **conteúdo revisado, não gerado**: nenhum verbete traz chamada a modelo de
#      linguagem em tempo de execução (RF-24, ADR 0007);
#   5. **exemplo sintético**: todo verbete traz o exemplo da persona fictícia (RI-06,
#      ADR 0006).
#
# Regra R2 do `CLAUDE.md`: a saída imprime as duas contagens, quantos caminhos de
# procedência foram conferidos e quantas âncoras foram casadas.
#
# Uso: scripts/check-documentacao.sh [raiz]   (padrão: a raiz do repositório)
# Saída: 0 conforme · 1 violação encontrada · 2 ambiente não montado.
set -uo pipefail

RAIZ="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
DOMINIO="$RAIZ/apps/api/src/toc_api/dominio"
ACERVO="$RAIZ/apps/web/src/documentacao/verbetes"
INTERFACE="$RAIZ/apps/web/src"

echo "── Documentação embutida: cobertura ferramenta × verbete (E8.4) ──"

if [[ ! -d "$DOMINIO" ]]; then
  echo "✗ $DOMINIO não existe — o serviço não está neste repositório." >&2
  exit 2
fi
if [[ ! -d "$ACERVO" ]]; then
  echo "✗ $ACERVO não existe — o acervo de documentação não está neste repositório." >&2
  exit 2
fi

FALHOU=0

# -- 1. cobertura: registro do serviço × arquivos do acervo ---------------------------
FERRAMENTAS="$(grep -rhoE 'registrar_raiz_de_ferramenta\(FERRAMENTA_[A-Z_]+' "$DOMINIO" --include='*.py' \
               | sed 's/.*FERRAMENTA_//' | tr 'A-Z' 'a-z' | sort -u)"
# O nome da constante não é o valor: `FERRAMENTA_SNT = "snt"`, `FERRAMENTA_FOCALIZACAO =
# "focalizacao"`. Traduz-se pelo VALOR declarado, para o portão medir o que o serviço
# publica e não o que o Python chama.
REGISTRADAS=()
while read -r constante; do
  [[ -z "$constante" ]] && continue
  valor="$(grep -rhoE "FERRAMENTA_$(echo "$constante" | tr 'a-z' 'A-Z') = \"[a-z_]+\"" "$DOMINIO" --include='*.py' \
           | head -1 | sed 's/.*= "//; s/"//')"
  REGISTRADAS+=("${valor:-$constante}")
done <<< "$FERRAMENTAS"

VERBETES=()
while read -r arquivo; do
  [[ -z "$arquivo" ]] && continue
  VERBETES+=("$(basename "$arquivo" .ts)")
done <<< "$(find "$ACERVO" -maxdepth 1 -name '*.ts' -not -name '*.test.ts' | sort)"

echo "  ferramentas registradas pelo serviço: ${#REGISTRADAS[@]} (${REGISTRADAS[*]})"
echo "  verbetes no acervo: ${#VERBETES[@]} (${VERBETES[*]})"

SEM_VERBETE=()
for ferramenta in "${REGISTRADAS[@]}"; do
  achou=0
  for verbete in "${VERBETES[@]}"; do [[ "$verbete" == "$ferramenta" ]] && achou=1; done
  [[ $achou -eq 0 ]] && SEM_VERBETE+=("$ferramenta")
done
ORFAOS=()
for verbete in "${VERBETES[@]}"; do
  achou=0
  for ferramenta in "${REGISTRADAS[@]}"; do [[ "$verbete" == "$ferramenta" ]] && achou=1; done
  [[ $achou -eq 0 ]] && ORFAOS+=("$verbete")
done

if (( ${#SEM_VERBETE[@]} > 0 )); then
  FALHOU=1
  echo "✗ ferramenta registrada SEM verbete: ${SEM_VERBETE[*]}" >&2
  echo "  RN-04: uma ferramenta só é considerada entregue quando tem verbete." >&2
fi
if (( ${#ORFAOS[@]} > 0 )); then
  FALHOU=1
  echo "✗ verbete órfão, sem ferramenta registrada: ${ORFAOS[*]}" >&2
  echo "  Verbete de ferramenta que não existe documenta uma tela que ninguém abre." >&2
fi
[[ $FALHOU -eq 0 ]] && echo "  ✓ cobertura completa: ${#REGISTRADAS[@]} de ${#REGISTRADAS[@]} ferramentas com verbete"

# -- 2. procedência: todo caminho citado existe (RF-22) -------------------------------
CAMINHOS=0
QUEBRADOS=()
for verbete in "${VERBETES[@]}"; do
  arquivo="$ACERVO/$verbete.ts"
  # O bloco `procedencia: [...]` é a única lista de caminhos do verbete. A extração é com
  # `awk`, e não com `sed -n '/a/,/b/p'`: o intervalo do `sed` exige que o fim venha numa
  # linha POSTERIOR, e um `procedencia: ["a", "b"],` de uma linha só engolia o arquivo
  # inteiro — o portão reprovava frases do verbete como se fossem caminhos.
  while read -r caminho; do
    [[ -z "$caminho" ]] && continue
    CAMINHOS=$((CAMINHOS + 1))
    [[ -e "$RAIZ/$caminho" ]] || QUEBRADOS+=("$verbete → $caminho")
  done <<< "$(awk '/procedencia: \[/{dentro=1} dentro{print} dentro && /\]/{dentro=0}' "$arquivo" \
              | grep -oE '"[^"]+"' | tr -d '"')"
done
echo "  caminhos de procedência conferidos: $CAMINHOS"
if (( ${#QUEBRADOS[@]} > 0 )); then
  FALHOU=1
  echo "✗ procedência que não resolve (RF-22):" >&2
  printf '    %s\n' "${QUEBRADOS[@]}" >&2
fi

# -- 3. verbete sem procedência nenhuma é opinião -------------------------------------
SEM_PROCEDENCIA=()
for verbete in "${VERBETES[@]}"; do
  grep -q 'procedencia: \[' "$ACERVO/$verbete.ts" || SEM_PROCEDENCIA+=("$verbete")
done
if (( ${#SEM_PROCEDENCIA[@]} > 0 )); then
  FALHOU=1
  echo "✗ verbete sem campo \`procedencia\`: ${SEM_PROCEDENCIA[*]} — verbete que não cita de onde a regra vem é opinião (RF-22)." >&2
fi

# -- 4. âncoras declaradas pela interface existem no verbete (RF-20) ------------------
ANCORAS=0
ANCORAS_TORTAS=()
while read -r linha; do
  [[ -z "$linha" ]] && continue
  arquivo="${linha%%:*}"
  ferramenta="$(printf '%s' "$linha" | grep -oE 'ferramenta="[a-z_]+"' | head -1 | sed 's/.*="//; s/"//')"
  ancora="$(printf '%s' "$linha" | grep -oE 'ancora="[a-z0-9-]+"' | head -1 | sed 's/.*="//; s/"//')"
  [[ -z "$ferramenta" || -z "$ancora" ]] && continue
  ANCORAS=$((ANCORAS + 1))
  alvo="$ACERVO/$ferramenta.ts"
  if [[ ! -f "$alvo" ]]; then
    ANCORAS_TORTAS+=("$(basename "$arquivo"): ferramenta $ferramenta sem verbete")
  elif ! grep -q "ancora: \"$ancora\"" "$alvo"; then
    ANCORAS_TORTAS+=("$(basename "$arquivo"): $ferramenta#$ancora não existe no verbete")
  fi
done <<< "$(grep -rn 'ancora="' "$INTERFACE" --include='*.tsx' | grep -v '\.test\.' || true)"
echo "  âncoras declaradas pela interface: $ANCORAS"
if (( ${#ANCORAS_TORTAS[@]} > 0 )); then
  FALHOU=1
  echo "✗ âncora de ajuda que não existe no verbete (RF-20):" >&2
  printf '    %s\n' "${ANCORAS_TORTAS[@]}" >&2
  echo "  Uma âncora torta abre o painel no lugar errado, sem erro nenhum." >&2
fi

# -- 5. conteúdo revisado, nunca gerado em tempo de execução (RF-24, ADR 0007) --------
GERADO="$(grep -rniE 'gemini|openai|anthropic|generateContent|fetch\(' "$ACERVO" --include='*.ts' || true)"
if [[ -n "$GERADO" ]]; then
  FALHOU=1
  echo "✗ o acervo chama modelo de linguagem em tempo de execução (RF-24, ADR 0007):" >&2
  printf '%s\n' "$GERADO" | sed 's/^/    /' >&2
fi

# -- 6. exemplo sintético da persona fictícia (RI-06, ADR 0006) ----------------------
SEM_EXEMPLO=()
for verbete in "${VERBETES[@]}"; do
  grep -q 'exemplo:' "$ACERVO/$verbete.ts" || SEM_EXEMPLO+=("$verbete")
done
if (( ${#SEM_EXEMPLO[@]} > 0 )); then
  FALHOU=1
  echo "✗ verbete sem exemplo sintético: ${SEM_EXEMPLO[*]} (RI-06)." >&2
fi

echo
if [[ $FALHOU -ne 0 ]]; then
  echo "✗ a documentação embutida não cobre o que a aplicação entrega." >&2
  exit 1
fi
echo "✓ documentação conforme: ${#REGISTRADAS[@]} ferramentas registradas × ${#VERBETES[@]} verbetes, $CAMINHOS procedências conferidas, $ANCORAS âncoras casadas."
