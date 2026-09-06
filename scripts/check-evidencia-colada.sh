#!/usr/bin/env bash
# check-evidencia-colada.sh — a regra R1 virada portão executável.
#
# R1 diz: "nunca transcreva um ✓: copie a linha que o script imprimiu". Ela protege o
# momento em que o número ENTRA no documento — e não protege nada depois disso. Um número
# colado com honestidade em março é uma afirmação falsa em setembro se o artefato que ele
# conta cresceu, e o documento continua parecendo evidência: tem bloco de código, tem
# cifrão, tem saída. É a pior espécie de mentira num repositório que promete "prove, não
# declare", porque veste a roupa da prova.
#
# Três achados de um crítico independente, todos deste tipo, motivaram este portão:
#
#   1. `apps/api/README.md` colava `40 passed, 786 deselected` — o mesmo comando devolve
#      hoje `42 passed, 797 deselected`;
#   2. o CHANGELOG anunciava `33 capturas` — `find docs/jornadas/capturas -name '*.png'`
#      devolve 36;
#   3. `docs/produto/visao.md` colava `0` para quatro buscas na linhagem TOC-Builder —
#      hoje devolvem 122, 212, 33 e 53, porque `tocbuilderv3/node_modules/` passou a
#      existir na máquina e as buscas não o excluíam. Aqui a AFIRMAÇÃO continuava certa
#      (a linhagem não tem instrumentação) e o COMANDO tinha deixado de ser a testemunha
#      dela — que é o caso mais traiçoeiro dos três.
#
# ## O que ele mede
#
# `scripts/evidencia-colada.json` é um registro de afirmações. Cada afirmação tem um
# COMANDO que produz um valor e a lista dos lugares onde esse valor está colado, com o
# MOLDE literal em que ele aparece. O portão roda o comando e exige o molde, já preenchido,
# dentro do arquivo. Número que saiu do lugar derruba o portão.
#
# ## O que ele NÃO mede — limite declarado, não escondido
#
# Ele não varre o repositório atrás de números; ele confere os que o registro declara.
# Um número não registrado não é conferido, e o portão diz quantos registrou — quem lê
# sabe o tamanho do que foi examinado (regra R2). Saída cara ou instável (uma suíte de
# 839 testes, um tempo em segundos, um identificador universal sorteado a cada corrida)
# fica de fora de propósito: o registro é para o que é reproduzível e barato, e o que
# muda a cada execução tem de estar DITO ao lado da saída, no documento.
#
# Uso:  scripts/check-evidencia-colada.sh [raiz]     (padrão: a raiz do repositório)
# Prova de que reprova: as sabotagens de `scripts/tests/run-sabotagem.sh`.
set -uo pipefail
RAIZ="${1:-$(cd "$(dirname "$0")/.." && pwd)}"
cd "$RAIZ" || { echo "✗ raiz inexistente: $RAIZ" >&2; exit 2; }

python3 - <<'PY'
import json
import os
import subprocess
import sys

REGISTRO = "scripts/evidencia-colada.json"

print("── Evidência colada: o comando ainda devolve o número que o documento afirma (R1) ──")

if not os.path.exists(REGISTRO):
    print(f"\n✗ {REGISTRO} não existe — sem registro o portão não examinaria nada.")
    sys.exit(1)

try:
    registro = json.load(open(REGISTRO, encoding="utf-8"))
except json.JSONDecodeError as erro:
    print(f"\n✗ {REGISTRO} não é JSON válido: {erro}")
    sys.exit(1)

afirmacoes = registro.get("afirmacoes")
if not isinstance(afirmacoes, list) or not afirmacoes:
    print(f"\n✗ {REGISTRO} não declara nenhuma afirmação — um portão sem entrada é um portão desligado.")
    sys.exit(1)

problemas = []
ocorrencias = 0
comandos_ok = 0
arquivos = set()
vistos = set()

for i, af in enumerate(afirmacoes):
    ident = af.get("id") or f"(afirmação #{i + 1} sem id)"
    if ident in vistos:
        problemas.append(f"{ident}: id repetido — dois registros com o mesmo nome escondem qual falhou")
    vistos.add(ident)

    comando = af.get("comando")
    esperado = af.get("esperado")
    if not comando:
        problemas.append(f"{ident}: sem `comando` — afirmação sem comando não é evidência, é declaração")
        continue
    if not isinstance(esperado, list) or not esperado:
        problemas.append(
            f"{ident}: sem `esperado` — um registro que não aponta nenhum documento passaria "
            "sempre, e um portão que passa sempre não é portão"
        )
        continue

    processo = subprocess.run(
        ["bash", "-c", comando], capture_output=True, text=True
    )
    if processo.returncode != 0:
        problemas.append(
            f"{ident}: o comando saiu {processo.returncode} — "
            f"`{comando}`\n      {processo.stderr.strip()[:200]}"
        )
        continue
    valor = processo.stdout.strip()
    if valor == "":
        problemas.append(f"{ident}: o comando não imprimiu nada — `{comando}`")
        continue
    comandos_ok += 1

    for alvo in esperado:
        arquivo = alvo.get("arquivo")
        molde = alvo.get("molde")
        if not arquivo or molde is None:
            problemas.append(f"{ident}: entrada de `esperado` sem `arquivo` ou `molde`")
            continue
        if "{v}" not in molde:
            problemas.append(
                f"{ident} → {arquivo}: o molde não contém `{{v}}` — um molde sem o valor "
                "casaria mesmo com o número errado"
            )
            continue
        if not os.path.exists(arquivo):
            problemas.append(f"{ident} → {arquivo}: o arquivo citado não existe")
            continue
        arquivos.add(arquivo)
        ocorrencias += 1
        texto = open(arquivo, encoding="utf-8").read()
        procurado = molde.replace("{v}", valor)
        if procurado not in texto:
            # Diz o que o documento traz no lugar, quando dá para saber: o molde com
            # qualquer outro valor é a pista mais útil que este portão pode dar.
            prefixo, _, sufixo = molde.partition("{v}")
            achado = ""
            if prefixo and prefixo in texto:
                inicio = texto.index(prefixo) + len(prefixo)
                fim = texto.find(sufixo, inicio) if sufixo else inicio + 40
                if fim > inicio:
                    achado = f" — o documento traz {texto[inicio:fim][:60]!r}"
            problemas.append(
                f"{ident} → {arquivo}: o comando devolve {valor!r} e o documento não traz "
                f"o molde preenchido com ele{achado}\n"
                f"      comando: {comando}\n"
                f"      molde:   {molde!r}"
            )

print(f"  afirmações registradas: {len(afirmacoes)}  ·  comandos executados com sucesso: {comandos_ok}/{len(afirmacoes)}")
print(f"  ocorrências conferidas: {ocorrencias}  ·  arquivos alcançados: {len(arquivos)}")
print("  limite declarado: confere o que o registro declara; número não registrado não é conferido")

if problemas:
    print()
    for p in problemas:
        print(f"  ✗ {p}")
    print(f"\n✗ {len(problemas)} problema(s): saída colada que o comando não reproduz mais.")
    sys.exit(1)

print(
    f"\n✓ as {len(afirmacoes)} afirmações do registro foram re-executadas e as {ocorrencias}"
    "\n  ocorrências coladas nos documentos batem com o que os comandos devolvem hoje."
)
PY
