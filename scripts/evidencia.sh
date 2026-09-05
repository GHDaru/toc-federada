#!/usr/bin/env bash
# evidencia.sh — runs every gate of this project and prints the evidence block, ready to
# paste into a cycle's `qa-report.md`.
#
# Por que existe: a regra R2 do `CLAUDE.md` diz que portão verde exige "quanto ele
# examinou?", e que a resposta vai para o `qa-report.md` **junto com o código de saída**.
# Fazer isso à mão é copiar seis saídas em seis passos, e foi assim que a irmã
# `gestaodeprioridades` acabou com quatro portões verdes que não tinham olhado para o que se
# supunha que olhassem: quem transcreve um "✓" não vê o denominador. Este script tira o
# passo mecânico da frente e deixa a **leitura** — que é a parte humana — com quem revisa.
#
# O que ele NÃO faz: julgar. Ele não decide se o número é suficiente, não conserta nada e
# não esconde falha. Um portão vermelho aparece vermelho, com as linhas que ele imprimiu.
#
# Saída: um bloco Markdown no stdout. Código de saída: 0 se todos os portões passaram,
# 1 se pelo menos um falhou — assim ele serve de portão único na CI (integração contínua),
# além de gerar a prova.
#
# Uso:
#   scripts/evidencia.sh                 # bloco Markdown no stdout
#   scripts/evidencia.sh > /tmp/ev.md    # para colar no qa-report.md do ciclo
set -uo pipefail

RAIZ="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$RAIZ" || exit 2

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

# Portão | rótulo | padrão (ERE) das linhas que respondem "quanto examinou?"
# O padrão é declarado aqui, por portão, e não adivinhado: cada portão diz o seu
# denominador com as suas palavras, e este script **cola** as linhas dele — nunca as
# reescreve (regra R1: nunca transcreva um "✓"; copie a linha que o script imprimiu).
PORTOES=(
  "scripts/check-caminhos.sh|caminhos citados entre crases (R4)|arquivos varridos|caminhos conferidos"
  "scripts/check-adrs-sucessao.sh|ADRs: índice, registro e sucessão (R5)|ADRs examinados|verificações executadas"
  "scripts/check-rounds.sh|rounds: campos, dependências e defeitos|rounds examinados|conferências de campo|defeitos medidos"
  "scripts/check-specs.sh|specs: artefatos, seções, taxonomia e cauda|ciclos examinados|verificações:"
  "scripts/check-links.sh|links relativos do repositório|checked:"
  "scripts/check-install.sh|método Maestro instalado e coerente|checked:|^  ok:"
  "scripts/check-vazamento.sh|vazamento de dado real de pessoa (RNF-03 · ADR 0006)|arquivos varridos|sinais aplicados|campos de pessoa vigiados"
  # Entrou quando o serviço nasceu: sem esta linha o agregador diria "todos os portões
  # verdes" enquanto NADA teria olhado para a fronteira entre domínio e adaptador (P3) —
  # que é exatamente o defeito que a regra R2 nomeia.
  "scripts/check-arquitetura.sh|arquitetura hexagonal: contratos do import-linter (P3)|contratos declarados|^Analyzed"
  # Os quatro da federação (specs 003 e 006). Entraram com o módulo M7, pelo mesmo motivo
  # do de arquitetura: sem eles o agregador diria "todos os portões verdes" enquanto NADA
  # teria olhado para a fronteira — nem para o manifesto que circula na admissão, nem para
  # a sabotagem que o APH-7.2 (Aplicação ↔ Harness) nomeia, nem para os três defeitos de
  # canal que a norma registrou, nem para os 11 checks executáveis do Nível 1.
  "scripts/check-manifesto.sh|manifesto × schema normativo do Anexo B + sabotagens|telas declaradas|sabotagens aplicadas"
  "scripts/check-politica.sh|política de autorização: a sabotagem do APH-7.2 não vaza|arquivos de produção varridos|arquivos que compõem"
  "scripts/check-canal.sh|canal ghd.* (§B.2): envelope, trava dupla, targetOrigin|arquivos de teste encontrados|^# (tests|pass|fail)"
  "scripts/check-conformidade-aph.sh|conformidade APH Nível 1 (11 checks, caixa-preta)|serviço de pé|^Veredito:"
)

falhados=0
executados=0
linhas_tabela=()
blocos=()

for entrada in "${PORTOES[@]}"; do
  IFS='|' read -r -a partes <<< "$entrada"
  cmd="${partes[0]}"
  rotulo="${partes[1]}"
  padrao="$(printf '%s|' "${partes[@]:2}")"; padrao="${padrao%|}"

  nome="$(basename "$cmd")"
  saida="$TMP/$nome.txt"

  if [[ ! -f "$cmd" ]]; then
    linhas_tabela+=("| \`$nome\` | \`$cmd\` | — | **ausente** | portão não existe neste repositório |")
    blocos+=("### \`$nome\` — ausente"$'\n\n'"O arquivo \`$cmd\` não existe. Um portão citado e inexistente é pior que nenhum: quem lê o relatório supõe que algo olhou.")
    falhados=$((falhados + 1))
    continue
  fi

  executados=$((executados + 1))
  bash "$cmd" > "$saida" 2>&1
  codigo=$?
  [[ $codigo -eq 0 ]] || falhados=$((falhados + 1))

  denominador="$(grep -E "$padrao" "$saida" | sed 's/^[[:space:]]*//' | head -8)"
  [[ -n "$denominador" ]] || denominador="(o portão não imprimiu denominador — regra R2 não satisfeita)"

  # O resumo é recorte da saída do portão; o total de linhas é contado aqui e rotulado
  # como contado aqui, para ninguém o ler como se o portão o tivesse dito.
  nlinhas="$(wc -l < "$saida" | tr -d ' ')"
  resumo="$(printf '%s' "$denominador" | tr '\n' ' ' | sed 's/  */ /g; s/|/·/g' | cut -c1-260)"
  resumo="$resumo <br>· saída completa: $nlinhas linhas (contadas por este script)"
  veredito=$([[ $codigo -eq 0 ]] && echo "✓ verde" || echo "✗ vermelho")

  linhas_tabela+=("| \`$nome\` | \`$cmd\` | \`$codigo\` | $veredito | $resumo |")

  bloco="### \`$nome\` — $rotulo"$'\n\n'
  bloco+="\`\`\`text"$'\n'
  bloco+="\$ $cmd"$'\n'
  bloco+="$(cat "$saida")"$'\n'
  bloco+="\$ echo \$?"$'\n'
  bloco+="$codigo"$'\n'
  bloco+="\`\`\`"
  blocos+=("$bloco")
done

hoje="$(date +%Y-%m-%d)"

echo "<!-- gerado por scripts/evidencia.sh em $hoje — não editar à mão: rode de novo -->"
echo
echo "## Evidência dos portões — $hoje"
echo
echo "Portões executados: **$executados** · verdes: **$((executados - falhados))** · vermelhos: **$falhados**."
echo "Cada linha traz o código de saída e o denominador que o próprio portão imprimiu"
echo "(regra R2: verde sem \"quanto examinou?\" não é evidência; regra R1: as linhas abaixo"
echo "são coladas da execução, não transcritas)."
echo
echo "| Portão | Comando | Saída | Veredito | Denominador (linha do próprio portão) |"
echo "|---|---|---|---|---|"
printf '%s\n' "${linhas_tabela[@]}"
echo
echo "### Saídas completas"
echo
for b in "${blocos[@]}"; do
  printf '%s\n\n' "$b"
done

echo "> **Estes números dizem que os portões rodaram, não que sabem reprovar.** A prova de"
echo "> que cada um reprova o defeito que existe para ver é outra, e roda separada:"
echo "> \`scripts/tests/run-sabotagem.sh\` (base válida aceita + uma mutação por invariante,"
echo "> cada uma exigindo o motivo declarado na saída)."

if [[ $falhados -ne 0 ]]; then
  echo "> **$falhados portão(ões) vermelho(s).** O bloco acima é a evidência do vermelho," >&2
  echo "> não um relatório de fechamento: ciclo não fecha com portão vermelho." >&2
  exit 1
fi
exit 0
