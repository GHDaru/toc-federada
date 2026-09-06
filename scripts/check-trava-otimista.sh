#!/usr/bin/env bash
# check-trava-otimista.sh — nenhuma escrita de agregado sai sem a trava de versão.
#
# Siglas, uma vez: **M1** — Núcleo de Diagramas Lógicos · **M2** — Árvore da Realidade
# Atual (ARA) · **M3** — Nuvem de Conflito (NC) · **APH** — Aplicação ↔ Harness ·
# **HTTP** — *HyperText Transfer Protocol* · **SQL** — *Structured Query Language*.
#
# ── O defeito que este portão existe para não deixar voltar ──────────────────────────
#
# `RepositorioDeProjetosSQL` grava o RETRATO do agregado que está em memória, e a
# reconciliação apaga do banco toda linha que ficou fora desse retrato
# (`delete(... id.notin_(ids))`). Isso é correto com um retrato por vez e catastrófico com
# dois: duas facilitadoras abrem a mesma análise, leem a versão 7, cada uma acrescenta o
# seu nó, e a segunda gravação **apaga o nó da primeira** — sem exceção, sem código de
# erro, sem aviso.
#
# A coluna `versao` existia, e era incrementada a cada mutação, e não protegia nada:
# ela nunca aparecia num `WHERE`. Medida da reprodução, contra o PostgreSQL real:
# **20 escritas concorrentes de nó · 20 aceitas · 1 nó no banco · 19 perdidos em silêncio.**
#
# A correção tem quatro peças, e este portão confere as quatro, porque qualquer uma que
# saia sozinha devolve a perda de atualização inteira:
#
#   1. o agregado sai do banco sabendo **de que versão partiu** (`versao_lida`);
#   2. a escrita se condiciona a ela (`UPDATE … WHERE versao = :versao_lida`) e quem não
#      casa recebe `ConflitoDeVersao` com os dois números — nunca `rowcount` ignorado;
#   3. **todo** caminho de escrita passa pela trava (M1, M2 e M3 gravam pelo MESMO
#      adaptador: fechar um e deixar dois é fechar o caso e não a classe);
#   4. o duplo em memória tem a mesma trava — senão a suíte de contrato fica verde sobre
#      uma perda de atualização que o banco de verdade recusa.
#
# E confere a quinta, que é o que faz a recusa ser audível: o código `VERSION_CONFLICT`
# está no registro único do §A.7 do Anexo A do Padrão APH, com motivo declarado, e a
# borda HTTP o emite. Perder a corrida é legítimo; perder sem saber, não.
#
# Regra R2 do `CLAUDE.md` (portão verde diz quanto examinou): a saída imprime quantos
# arquivos foram varridos, quantos caminhos de escrita foram conferidos e quantas guardas
# foram encontradas de quantas esperadas.
#
# Uso: scripts/check-trava-otimista.sh [raiz]   (padrão: a raiz do repositório)
# Saída: 0 conforme · 1 violação encontrada · 2 ambiente não montado.
set -uo pipefail

RAIZ="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
FONTE="$RAIZ/apps/api/src/toc_api"
REPO="$FONTE/infra/persistencia/repositorio_projetos.py"
MEMORIA="$FONTE/infra/persistencia/memoria.py"
PROJETO="$FONTE/dominio/projeto.py"
WIRE="$FONTE/dominio/federacao/wire.py"
BORDA="$FONTE/http/erros.py"

#: As três portas de escrita do agregado. Escrita à mão de propósito, como as oito
#: mutações do `check-raiz-do-agregado.sh`: derivar a lista do próprio arquivo faria o
#: portão concordar com quem esquecesse a trava numa delas.
ESCRITAS=(salvar salvar_ara salvar_nuvem)

echo "── Trava otimista: nenhuma escrita de agregado sem a versão lida ──"

FALTANDO=()
for arquivo in "$REPO" "$MEMORIA" "$PROJETO" "$WIRE" "$BORDA"; do
  [[ -f "$arquivo" ]] || FALTANDO+=("$arquivo")
done
if (( ${#FALTANDO[@]} > 0 )); then
  printf '✗ arquivo do serviço ausente: %s\n' "${FALTANDO[@]}" >&2
  exit 2
fi

VARRIDOS=5
echo "  arquivos varridos: $VARRIDOS (adaptador SQL, duplo em memória, agregado, registro §A.7, borda HTTP)"

FALHOU=0

corpo_do_metodo() {  # $1 = arquivo · $2 = nome do método (recuado em 4)
  awk -v alvo="    def $2(" '
    index($0, alvo) == 1 { dentro = 1; next }
    dentro && /^    def / { exit }
    dentro && /^class / { exit }
    dentro { print }
  ' "$1"
}

# -- 1. o agregado sai do banco sabendo de que versão partiu ---------------------------
if grep -q "versao_lida: int = field(" "$PROJETO" && grep -q "def confirmar_gravacao" "$PROJETO"; then
  echo "  ✓ o agregado declara \`versao_lida\` e \`confirmar_gravacao\`"
else
  echo "✗ o agregado não guarda a versão lida: sem ela não há contra o que condicionar a" >&2
  echo "  escrita, e \`versao\` volta a ser um contador em memória." >&2
  FALHOU=1
fi

if grep -q "projeto.versao_lida = linha.versao" "$REPO"; then
  echo "  ✓ a reidratação preenche \`versao_lida\` a partir da coluna"
else
  echo "✗ reidratação sem \`versao_lida\`: o agregado sai do banco sem saber de que versão" >&2
  echo "  partiu, e toda gravação vira inserção cega ou atualização sem trava." >&2
  FALHOU=1
fi

# -- 2. a escrita se condiciona à versão lida, e a recusa é explícita -------------------
GRAVAR="$(corpo_do_metodo "$REPO" _gravar_projeto)"
if printf '%s' "$GRAVAR" | grep -q "tabela_projeto.c.versao == projeto.versao_lida"; then
  echo "  ✓ o \`UPDATE\` carrega \`WHERE versao = :versao_lida\`"
else
  echo "✗ \`_gravar_projeto\` grava sem condicionar à versão lida — é a perda de" >&2
  echo "  atualização de volta: quem leu a versão velha apaga o trabalho de quem gravou." >&2
  FALHOU=1
fi

if printf '%s' "$GRAVAR" | grep -q "rowcount == 0" \
   && printf '%s' "$GRAVAR" | grep -q "raise ConflitoDeVersao"; then
  echo "  ✓ \`rowcount == 0\` levanta \`ConflitoDeVersao\` — a recusa não é silenciosa"
else
  echo "✗ a escrita não confere o \`rowcount\` ou não levanta \`ConflitoDeVersao\`: uma" >&2
  echo "  atualização que não casou e não reclama é exatamente o silêncio que o defeito tinha." >&2
  FALHOU=1
fi

# -- 3. TODO caminho de escrita passa pela trava (a classe, não o caso) ----------------
DECLARADAS="$(grep -c '^    def salvar' "$REPO" || true)"
echo "  caminhos de escrita conferidos: ${#ESCRITAS[@]} declarados · $DECLARADAS encontrados no adaptador"
if [[ "$DECLARADAS" != "${#ESCRITAS[@]}" ]]; then
  echo "✗ o adaptador tem $DECLARADAS método(s) \`salvar*\` e este portão conhece" >&2
  echo "  ${#ESCRITAS[@]}: um caminho de escrita novo entrou sem entrar na lista deste portão." >&2
  grep -n '^    def salvar' "$REPO" | sed 's/^/    /' >&2
  FALHOU=1
fi

SEM_TRAVA=()
SEM_CONFIRMACAO=()
for porta in "${ESCRITAS[@]}"; do
  corpo="$(corpo_do_metodo "$REPO" "$porta")"
  printf '%s' "$corpo" | grep -q "_gravar_projeto(" || SEM_TRAVA+=("$porta")
  printf '%s' "$corpo" | grep -q "confirmar_gravacao()" || SEM_CONFIRMACAO+=("$porta")
done
GUARDAS=$(( ${#ESCRITAS[@]} - ${#SEM_TRAVA[@]} ))
echo "  guardas \`_gravar_projeto\` encontradas: $GUARDAS de ${#ESCRITAS[@]} caminhos de escrita"
if (( ${#SEM_TRAVA[@]} > 0 )); then
  echo "✗ caminho de escrita que não passa pela trava: ${SEM_TRAVA[*]}" >&2
  echo "  M1, M2 e M3 gravam pelo MESMO adaptador — deixar um de fora reabre a classe inteira." >&2
  FALHOU=1
fi
if (( ${#SEM_CONFIRMACAO[@]} > 0 )); then
  echo "✗ caminho de escrita que não confirma a gravação: ${SEM_CONFIRMACAO[*]}" >&2
  echo "  Sem \`confirmar_gravacao()\` depois do commit, a segunda gravação do mesmo pedido" >&2
  echo "  parte de uma versão velha e é recusada sem que ninguém tenha concorrido." >&2
  FALHOU=1
fi

# -- 4. o duplo em memória tem a MESMA trava -------------------------------------------
SEM_TRAVA_NO_DUPLO=()
for porta in "${ESCRITAS[@]}"; do
  corpo="$(corpo_do_metodo "$MEMORIA" "$porta")"
  printf '%s' "$corpo" | grep -q "_exigir_versao_lida(" || SEM_TRAVA_NO_DUPLO+=("$porta")
done
if grep -q "raise ConflitoDeVersao" "$MEMORIA" && (( ${#SEM_TRAVA_NO_DUPLO[@]} == 0 )); then
  echo "  ✓ o duplo em memória recusa a mesma escrita nos ${#ESCRITAS[@]} caminhos"
else
  echo "✗ o duplo em memória é mais permissivo que o adaptador real: ${SEM_TRAVA_NO_DUPLO[*]:-sem ConflitoDeVersao}" >&2
  echo "  A suíte de contrato roda sobre ele; verde ali sobre perda de atualização é verde" >&2
  echo "  sobre um defeito que o banco de verdade recusa." >&2
  FALHOU=1
fi

# -- 5. a recusa é audível: código estável no registro único, emitido pela borda --------
if grep -q '"VERSION_CONFLICT": (' "$WIRE" && grep -q "VERSION_CONFLICT" "$BORDA"; then
  echo "  ✓ \`VERSION_CONFLICT\` declarado no registro do §A.7 e emitido pela borda HTTP"
else
  echo "✗ \`VERSION_CONFLICT\` fora do registro único (\`dominio/federacao/wire.py\`) ou não" >&2
  echo "  emitido pela borda: o cliente discrimina por código, e um código não declarado" >&2
  echo "  não sai do serviço — ou sai como \`DOMAIN_REFUSED\`, que manda corrigir o pedido" >&2
  echo "  em vez de recarregar." >&2
  FALHOU=1
fi
for campo in versao_lida versao_atual; do
  grep -q "\"$campo\": erro.$campo" "$BORDA" || {
    echo "✗ a resposta 409 não carrega \`details.$campo\`: sem os dois números o cliente" >&2
    echo "  não tem como recarregar e refazer sozinho, e volta a ler a mensagem." >&2
    FALHOU=1
  }
done

echo
if [[ $FALHOU -ne 0 ]]; then
  echo "✗ a trava otimista deixou de proteger algum caminho de escrita do agregado." >&2
  exit 1
fi
echo "✓ trava otimista íntegra: $GUARDAS de ${#ESCRITAS[@]} caminhos de escrita conferidos em"
echo "  $VARRIDOS arquivos, com recusa explícita e código estável do §A.7."
