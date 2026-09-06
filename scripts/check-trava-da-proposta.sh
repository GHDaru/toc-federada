#!/usr/bin/env bash
# check-trava-da-proposta.sh — nenhuma decisão sobre proposta executa duas vezes.
#
# Siglas, uma vez neste arquivo: **APH** — Aplicação ↔ Harness · **FSM** — máquina de
# estados finitos · **SQL** — *Structured Query Language* · **HTTP** — *HyperText Transfer
# Protocol* · **TTL** — *Time To Live* (tempo de vida) · **M1** — Núcleo de Diagramas
# Lógicos.
#
# ── O defeito que este portão existe para não deixar voltar ──────────────────────────
#
# A proposta de ação era o ÚNICO agregado persistido sem trava, e uma aprovação humana
# executava N vezes. Reprodução contra o PostgreSQL real, medida antes do conserto:
#
#   proposta `toc.criar_nos` com 30 alvos em `awaiting_approval`; oito confirmações
#   simultâneas do MESMO `proposal_id` com a MESMA chave de idempotência devolveram
#   `{200: 8}`, gravaram 50 nós para 30 pedidos, com 22 títulos repetidos, e deixaram
#   OITO linhas de traço para uma proposta só. Oito recusas simultâneas deixaram cinco.
#
# É grave por dois motivos somados: quebra a deduplicação que o próprio padrão exige
# (APH-5.3 — `idempotency_key` com deduplicação REAL) e multiplica por uma corrida o portão
# humano, que o método trata como inegociável.
#
# ── Por que a FSM não impediu, que é o que decide o conserto ─────────────────────────
#
# A FSM guardava o **objeto**, não a linha. `obter` reidrata um `PropostaDeAcao` NOVO a
# cada chamada, e `transicionar` consulta `self.estado`, que é atributo de memória: oito
# confirmações liam oito agregados em `awaiting_approval` e as oito transições eram
# legítimas, cada uma no seu objeto. E a gravação (`INSERT … ON CONFLICT DO UPDATE`
# incondicional) vinha **depois** do efeito — logo nem uma escrita condicionada ali
# adiantaria: os 30 nós já estariam no banco.
#
# A transição `confirmed → executing` É a serialização natural do APH-5.1, mas só quando
# ela existe **no banco e antes do efeito**. Este portão confere as seis peças que fazem
# isso ser verdade, porque qualquer uma que saia sozinha devolve a execução múltipla:
#
#   1. o agregado sai do banco sabendo de que estado partiu (`estado_lido`);
#   2. a escrita se condiciona a ele (`UPDATE … WHERE estado = :estado_lido`) e o
#      `rowcount` 0 vira `CorridaDeDecisao` — nunca silêncio;
#   3. **a reserva acontece ANTES do efeito** (a peça que o ordenamento sozinho garante);
#   4. o duplo em memória tem a mesma trava e devolve CÓPIA — um duplo que entrega o
#      objeto guardado esconde a corrida inteira da suíte de contrato;
#   5. a `idempotency_key` deduplica de verdade: índice único por (inquilino, chave) e
#      leitura da chave na aplicação. Antes ela era gravada em toda confirmação e lida em
#      lugar nenhum;
#   6. a recusa é audível — código estável no registro do §A.7 — e o traço continua
#      somente-acréscimo.
#
# E confere a sétima, que é o que separa fechar a CLASSE de fechar o caso: **todo** caminho
# de escrita persistente dos dois adaptadores está declarado aqui, com a trava que lhe
# cabe. Um caminho novo que entre sem entrar nesta lista reprova.
#
# Regra R2 do `CLAUDE.md` (portão verde diz quanto examinou): a saída imprime quantos
# arquivos foram varridos, quantos caminhos de escrita foram classificados e quantas
# verificações passaram de quantas.
#
# Uso: scripts/check-trava-da-proposta.sh [raiz]   (padrão: a raiz do repositório)
# Saída: 0 conforme · 1 violação encontrada · 2 ambiente não montado.
set -uo pipefail

RAIZ="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
FONTE="$RAIZ/apps/api/src/toc_api"
PROPOSTA="$FONTE/dominio/federacao/proposta.py"
WIRE="$FONTE/dominio/federacao/wire.py"
REPO_SQL="$FONTE/infra/federacao/repositorio_sql.py"
MEMORIA="$FONTE/infra/federacao/memoria.py"
ACOES="$FONTE/aplicacao/federacao/acoes.py"
TABELAS="$FONTE/infra/persistencia/tabelas.py"
REPO_PROJETOS="$FONTE/infra/persistencia/repositorio_projetos.py"

#: A CLASSE inteira: todo método que escreve estado persistente, e a trava que lhe cabe.
#: Escrita à mão de propósito — derivar a lista do próprio código faria o portão concordar
#: com quem esquecesse a trava num caminho novo. Formato: `arquivo|método|trava`.
#:
#: `retrato` = grava o retrato do agregado e precisa de trava por versão/estado lido.
#: `acrescimo` = só insere linha nova; não há retrato a perder (traço, APH-5.5).
#: `identidade` = apaga por identidade e devolve `rowcount`; idempotente por construção.
ESCRITAS=(
  "infra/persistencia/repositorio_projetos.py|salvar|retrato"
  "infra/persistencia/repositorio_projetos.py|salvar_ara|retrato"
  "infra/persistencia/repositorio_projetos.py|salvar_nuvem|retrato"
  "infra/persistencia/repositorio_projetos.py|salvar_arf|retrato"
  "infra/persistencia/repositorio_projetos.py|salvar_apr|retrato"
  "infra/persistencia/repositorio_projetos.py|salvar_at|retrato"
  "infra/persistencia/repositorio_projetos.py|salvar_focalizacao|retrato"
  "infra/persistencia/repositorio_projetos.py|salvar_referencia|retrato"
  "infra/persistencia/repositorio_projetos.py|excluir_definitivamente|identidade"
  "infra/federacao/repositorio_sql.py|salvar|retrato"
  "infra/federacao/repositorio_sql.py|registrar|acrescimo"
)

#: As funções que APLICAM a trava. Nomeadas à mão, e não por molde `_gravar_*`, porque um
#: molde aprovaria um `_gravar_qualquercoisa` que não condiciona nada — que é a diferença
#: entre conferir o nome e conferir o fato.
GUARDAS_DE_TRAVA='_gravar_projeto\(|_gravar_referencia\(|estado_lido|_exigir_estado_lido'

echo "── Trava da proposta: uma aprovação humana, uma execução ──"

FALTANDO=()
for arquivo in "$PROPOSTA" "$WIRE" "$REPO_SQL" "$MEMORIA" "$ACOES" "$TABELAS" "$REPO_PROJETOS"; do
  [[ -f "$arquivo" ]] || FALTANDO+=("$arquivo")
done
if (( ${#FALTANDO[@]} > 0 )); then
  printf '✗ arquivo do serviço ausente: %s\n' "${FALTANDO[@]}" >&2
  exit 2
fi

VARRIDOS=7
echo "  arquivos varridos: $VARRIDOS (agregado, registro §A.7, adaptador SQL, duplo em"
echo "  memória, caso de uso, tabelas, adaptador do núcleo)"

FALHOU=0
PASSOU=0
TOTAL=0

ok()   { echo "  ✓ $1"; PASSOU=$((PASSOU + 1)); TOTAL=$((TOTAL + 1)); }
bad()  { echo "✗ $1" >&2; shift; printf '  %s\n' "$@" >&2; FALHOU=1; TOTAL=$((TOTAL + 1)); }

# -- 1. o agregado sai do banco sabendo de que estado partiu ----------------------------
if grep -q "estado_lido: str = field(" "$PROPOSTA" && grep -q "def confirmar_gravacao" "$PROPOSTA"; then
  ok "o agregado declara \`estado_lido\` e \`confirmar_gravacao\`"
else
  bad "o agregado da proposta não guarda o estado lido" \
      "Sem ele não há contra o que condicionar a escrita, e a máquina de estados finitos" \
      "volta a guardar o objeto em vez da linha: N leituras, N transições legítimas, N" \
      "execuções."
fi

if grep -q "proposta.estado_lido = proposta.estado" "$REPO_SQL"; then
  ok "a reidratação SQL preenche \`estado_lido\` a partir da coluna"
else
  bad "reidratação sem \`estado_lido\` no adaptador SQL" \
      "O agregado sai do banco sem saber de que estado partiu, e toda gravação vira" \
      "inserção cega ou atualização sem trava."
fi

if grep -q "copia.estado_lido = copia.estado" "$MEMORIA"; then
  ok "a leitura do duplo em memória preenche \`estado_lido\`"
else
  bad "o duplo em memória lê sem \`estado_lido\`" \
      "A suíte de contrato roda quase toda sobre ele: verde ali sobre execução múltipla é" \
      "verde sobre um defeito que o banco de verdade recusa."
fi

# -- 2. a escrita se condiciona ao estado lido, e a recusa é explícita ------------------
if grep -q "proposta_de_acao.c.estado == proposta.estado_lido" "$REPO_SQL"; then
  ok "o \`UPDATE\` da proposta carrega \`WHERE estado = :estado_lido\`"
else
  bad "\`salvar\` grava a proposta sem condicionar ao estado lido" \
      "É a execução múltipla de volta: oito confirmações simultâneas gravam as oito, e o" \
      "gate humano — inegociável — passa a ser multiplicável por uma corrida."
fi

if grep -q "resultado.rowcount == 0" "$REPO_SQL" && grep -q "raise CorridaDeDecisao" "$REPO_SQL"; then
  ok "\`rowcount == 0\` levanta \`CorridaDeDecisao\` — a recusa não é silenciosa"
else
  bad "a escrita da proposta não confere o \`rowcount\` ou não levanta \`CorridaDeDecisao\`" \
      "Uma atualização que não casou e não reclama é exatamente o silêncio que o defeito" \
      "tinha: quem perdeu a corrida recebia 200 e achava que tinha decidido."
fi

# -- 3. A PEÇA CENTRAL: a reserva acontece ANTES do efeito ------------------------------
LINHA_RESERVA="$(grep -n "self._reservar(proposta, principal)" "$ACOES" | head -1 | cut -d: -f1)"
LINHA_EFEITO="$(grep -n "self._executor.executar(" "$ACOES" | head -1 | cut -d: -f1)"
if [[ -z "$LINHA_RESERVA" ]]; then
  bad "o caso de uso não reserva a proposta antes de executar" \
      "A transição \`confirmed → executing\` é a serialização natural do APH-5.1 — e só" \
      "vale quando existe NO BANCO. Sem a reserva, a trava do adaptador chega tarde: os" \
      "alvos já foram escritos."
elif [[ -z "$LINHA_EFEITO" ]]; then
  bad "o caso de uso não chama o executor: este portão não sabe mais onde é o efeito" \
      "A varredura de ordem depende de achar as duas linhas; sem uma delas, o portão" \
      "responderia verde sem ter olhado para a ordem."
elif (( LINHA_RESERVA < LINHA_EFEITO )); then
  ok "a reserva (linha $LINHA_RESERVA) acontece ANTES do efeito (linha $LINHA_EFEITO)"
else
  bad "a reserva acontece DEPOIS do efeito (linha $LINHA_RESERVA contra $LINHA_EFEITO)" \
      "Era exatamente o defeito: \`salvar\` só rodava depois de executar, então nem uma" \
      "escrita condicionada adiantava — os 30 nós já estavam no banco quando a corrida se" \
      "resolvia."
fi

if grep -q "def _reservar" "$ACOES" && \
   awk '/def _reservar/{d=1} d && /_propostas.salvar\(/{print; exit}' "$ACOES" | grep -q "salvar"; then
  ok "\`_reservar\` grava pelo repositório (é a trava, não um comentário)"
else
  bad "\`_reservar\` não grava pelo repositório" \
      "Uma reserva que não escreve no banco não serializa nada: a corrida continua toda" \
      "em memória, que é onde ela nunca foi vista."
fi

# -- 4. o duplo em memória tem a MESMA trava, e devolve cópia ---------------------------
if grep -q "def _exigir_estado_lido" "$MEMORIA" && grep -q "raise CorridaDeDecisao" "$MEMORIA"; then
  ok "o duplo em memória recusa a segunda decisão da mesma leitura"
else
  bad "o duplo em memória é mais permissivo que o adaptador real" \
      "É a lição já paga no duplo do núcleo: enquanto o banco recusa e o duplo aceita, a" \
      "suíte de contrato fica verde sobre a corrida."
fi

if awk '/def obter\(self, inquilino_id: str, proposal_id/{d=1} d && /deepcopy\(/{print; exit}' \
     "$MEMORIA" | grep -q "deepcopy"; then
  ok "o duplo em memória devolve CÓPIA na leitura"
else
  bad "o duplo em memória devolve o objeto guardado na leitura" \
      "Dois leitores recebem o MESMO agregado, a segunda transição encontra o estado que a" \
      "primeira já mudou, e a corrida fica invisível — o duplo mente para melhor."
fi

# -- 5. a deduplicação do APH-5.3 é REAL: índice único e chave consultada ---------------
if grep -q "uq_proposta_de_acao_tenant_id_idempotency_key" "$TABELAS"; then
  ok "a \`idempotency_key\` tem índice único por inquilino no modelo declarado"
else
  bad "sem índice único de (tenant_id, idempotency_key)" \
      "O APH-5.3 pede deduplicação REAL. Sem a unicidade no banco, a chave volta a ser uma" \
      "coluna que se grava e ninguém consulta — que é como ela estava."
fi

MIGRACOES="$(grep -rl --include='*.py' "uq_proposta_de_acao_tenant_id_idempotency_key" \
  "$FONTE/alembic/versions" 2>/dev/null | wc -l)"
if (( MIGRACOES >= 1 )); then
  ok "o índice único nasce de migração Alembic ($MIGRACOES arquivo(s))"
else
  bad "o índice único não está em migração nenhuma" \
      "Índice que só existe no modelo declarado não existe no banco de produção: o esquema" \
      "migrado deriva do modelo, e o teste de deriva é quem cobra."
fi

if grep -q "mesma_chave(idempotency_key)" "$ACOES"; then
  ok "a aplicação CONSULTA a chave de idempotência"
else
  bad "a chave de idempotência não é consultada em lugar nenhum" \
      "Era o defeito literal: \`grep -rn idempotency_key\` mostrava só escritas. Uma coluna" \
      "que ninguém lê não deduplica nada, e o APH-5.3 é sobre deduplicar de verdade."
fi

if grep -q "def aguardar_desfecho" "$REPO_SQL" && grep -q "def aguardar_desfecho" "$MEMORIA"; then
  ok "os dois adaptadores sabem esperar o desfecho de quem venceu a corrida"
else
  bad "falta \`aguardar_desfecho\` em algum adaptador" \
      "A segunda metade do APH-5.3 é \"quantas respostas idênticas forem pedidas\": sem a" \
      "espera, quem perde a corrida com a mesma chave recebe recusa em vez do resultado."
fi

# -- 6. a recusa é audível, e o traço continua somente-acréscimo ------------------------
if grep -q '"IDEMPOTENCY_KEY_REUSED": (' "$WIRE"; then
  ok "\`IDEMPOTENCY_KEY_REUSED\` declarado no registro único do §A.7"
else
  bad "\`IDEMPOTENCY_KEY_REUSED\` fora do registro único (\`dominio/federacao/wire.py\`)" \
      "O §A.7 permite código próprio, mas só documentado — e \`ErroDoFio\` recusa o que não" \
      "está no registro. O cliente discrimina por código, nunca por mensagem."
fi

RESCRITA_DO_TRACO="$(grep -cE "update\(traco_de_execucao|delete\(traco_de_execucao" "$REPO_SQL")"
if [[ "$RESCRITA_DO_TRACO" == "0" ]]; then
  ok "o traço continua somente-acréscimo (0 \`UPDATE\`/\`DELETE\` sobre ele)"
else
  bad "o traço deixou de ser somente-acréscimo ($RESCRITA_DO_TRACO ocorrência(s))" \
      "APH-5.5: o que aconteceu não se reescreve. Um traço editável é uma auditoria que" \
      "concorda com quem a edita."
fi

# -- 7. a CLASSE: todo caminho de escrita persistente está declarado --------------------
echo "  caminhos de escrita classificados: ${#ESCRITAS[@]}"
DECLARADOS=()
for entrada in "${ESCRITAS[@]}"; do
  IFS='|' read -r relativo metodo trava <<< "$entrada"
  arquivo="$FONTE/$relativo"
  if ! grep -q "^    def $metodo(" "$arquivo" 2>/dev/null; then
    bad "caminho de escrita declarado que não existe: $relativo::$metodo" \
        "A lista deste portão envelheceu em relação ao código; um portão que confere uma" \
        "lista que não existe mais responde verde sobre nada."
    continue
  fi
  DECLARADOS+=("$relativo::$metodo")
  case "$trava" in
    retrato)
      corpo="$(awk -v alvo="    def $metodo(" '
        index($0, alvo) == 1 { d = 1; next }
        d && /^    def / { exit }
        d && /^class / { exit }
        d { print }' "$arquivo")"
      if printf '%s' "$corpo" | grep -qE "$GUARDAS_DE_TRAVA"; then
        ok "$relativo::$metodo grava retrato SOB trava"
      else
        bad "$relativo::$metodo grava o retrato do agregado SEM trava" \
            "Um caminho de escrita fora da trava reabre a classe inteira: foi assim que a" \
            "proposta ficou de fora quando o projeto foi consertado."
      fi
      ;;
    acrescimo)
      ok "$relativo::$metodo é somente-acréscimo (não há retrato a perder)"
      ;;
    identidade)
      ok "$relativo::$metodo apaga por identidade e devolve \`rowcount\`"
      ;;
  esac
done

# O complemento: um método `salvar*` novo em qualquer dos dois adaptadores tem de entrar
# na lista acima. Contar é o que impede o portão de concordar com quem esquecer.
ENCONTRADOS="$(grep -hc '^    def salvar' "$REPO_SQL" "$REPO_PROJETOS" | paste -sd+ | bc)"
ESPERADOS=9  # salvar (proposta) + os oito `salvar*` do núcleo (M1 a M4, M6 e a referência)
if [[ "$ENCONTRADOS" == "$ESPERADOS" ]]; then
  ok "os dois adaptadores têm $ENCONTRADOS método(s) \`salvar*\`, todos na lista"
else
  bad "os adaptadores têm $ENCONTRADOS método(s) \`salvar*\` e este portão conhece $ESPERADOS" \
      "Um caminho de escrita novo entrou sem entrar na lista deste portão — e um caminho" \
      "fora da lista é um caminho que ninguém conferiu."
  grep -n '^    def salvar' "$REPO_SQL" "$REPO_PROJETOS" | sed 's/^/    /' >&2
fi

echo
if [[ $FALHOU -ne 0 ]]; then
  echo "✗ a trava da proposta deixou de proteger algum caminho — verificações: $PASSOU de $TOTAL." >&2
  exit 1
fi
echo "✓ trava da proposta íntegra: $PASSOU de $TOTAL verificações em $VARRIDOS arquivos,"
echo "  com ${#DECLARADOS[@]} caminho(s) de escrita persistente classificado(s) e a reserva"
echo "  provadamente ANTES do efeito."
