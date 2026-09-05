#!/usr/bin/env bash
# check-manifesto.sh — o manifesto valida contra o schema NORMATIVO do Padrão APH.
#
# Siglas, uma vez: APH — Aplicação ↔ Harness (o padrão da fronteira) · JSON — JavaScript
# Object Notation · ADR — Architecture Decision Record (Registro de Decisão Arquitetural).
#
# Por que este portão existe: a DoD 11 da spec 006 pede "script de validação (jsonschema
# draft 2020-12) com saída colada; sabotagens (sem `theme.fallback`, capability curinga)
# rejeitadas". A segunda metade é a que importa — um validador que aprova tudo também
# aprovaria o nosso manifesto, e o verde não valeria nada. Por isso ele roda o manifesto
# **e** as sabotagens, e falha se qualquer sabotagem passar (regra R2: portão verde exige
# "quanto ele examinou?", e aqui a resposta inclui quantos ataques foram repelidos).
#
# O schema é lido do repositório `GHDaru/protocolos`, que é SOMENTE LEITURA (P1). Se ele
# não estiver clonado ao lado, o portão sai com código 2 — ausência de ambiente é falha de
# portão, não ausência de defeito.
#
# Uso: scripts/check-manifesto.sh [raiz]
# Saída: 0 manifesto válido e sabotagens repelidas · 1 defeito · 2 ambiente incompleto
set -uo pipefail

RAIZ="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
MANIFESTO="$RAIZ/specs/006-acoes-governadas-e-snapshot/contracts/manifesto.json"
SCHEMA="${TOC_SCHEMA_MANIFESTO:-$(cd "$RAIZ/.." && pwd)/protocolos/padrao/schemas/federacao-manifesto.schema.json}"
PY="$RAIZ/apps/api/.venv/bin/python"

echo "── Manifesto da aplicação × schema normativo do Anexo B ──"

[[ -f "$MANIFESTO" ]] || { echo "✗ manifesto ausente: $MANIFESTO" >&2; exit 2; }
[[ -f "$SCHEMA" ]] || { echo "✗ schema normativo ausente: $SCHEMA" >&2; exit 2; }
[[ -x "$PY" ]] || { echo "✗ ambiente do serviço não montado (cd apps/api && uv sync)" >&2; exit 2; }

echo "  manifesto: $MANIFESTO"
echo "  schema:    $SCHEMA"

"$PY" - "$MANIFESTO" "$SCHEMA" <<'PYEOF'
import copy, json, pathlib, sys
import jsonschema
from referencing import Registry, Resource
from referencing.jsonschema import DRAFT202012

manifesto = json.load(open(sys.argv[1], encoding="utf-8"))
caminho_do_schema = pathlib.Path(sys.argv[2])
schema = json.loads(caminho_do_schema.read_text(encoding="utf-8"))

# O schema normativo referencia os irmãos pelo NOME DO ARQUIVO
# (`$ref: federacao-capability.schema.json`). Sem registrá-los, a biblioteca tentaria
# buscar por rede — e um portão que depende de rede é um portão que um dia responde verde
# porque a rede caiu. Aqui todos os irmãos entram do disco, do repositório `protocolos`.
recursos = []
for irmao in sorted(caminho_do_schema.parent.glob("*.schema.json")):
    corpo = json.loads(irmao.read_text(encoding="utf-8"))
    recurso = Resource.from_contents(corpo, default_specification=DRAFT202012)
    recursos.append((irmao.name, recurso))
    if "$id" in corpo:
        recursos.append((corpo["$id"], recurso))
registro = Registry().with_resources(recursos)
print(f"  schemas irmãos registrados do disco: {len(set(n for n, _ in recursos))}")
validador = jsonschema.Draft202012Validator(schema, registry=registro)

erros = sorted(validador.iter_errors(manifesto), key=lambda e: list(e.path))
print(f"  telas declaradas: {len(manifesto.get('screens', []))}  "
      f"ações declaradas: {len(manifesto.get('actions', []))}")
if erros:
    print(f"\n✗ manifesto REJEITADO — {len(erros)} erro(s):")
    for erro in erros:
        print(f"    · {'/'.join(str(p) for p in erro.path) or '(raiz)'}: {erro.message}")
    sys.exit(1)
print("  ✓ manifesto aceito pelo schema normativo — 0 erro")

# --- sabotagens: o validador tem de RECUSAR cada uma ----------------------------------
def sem_theme_fallback(m):
    m["theme"].pop("fallback", None)
    return m

def capability_curinga(m):
    m["capabilities_required"] = ["toc:*"]
    return m

def modo_inventado(m):
    m["mode"] = "federated"
    return m

def acao_sem_risco(m):
    m["actions"][0].pop("risk", None)
    return m

def tela_sem_namespace(m):
    m["screens"][0]["id"] = "projetos"
    return m

def url_sem_https(m):
    m["url"] = "http://toc-federada.example/toc/embarcado"
    return m

def batch_atomicity_no_manifesto(m):
    # L-02 da spec 006: o campo NÃO existe no schema do manifesto (só no do catálogo,
    # §A.5). Este ataque é o que mantém a decisão declarada em vez de esquecida.
    m["actions"][3]["batch_atomicity"] = "per_item"
    return m

SABOTAGENS = [
    ("theme.fallback removido", sem_theme_fallback),
    ("capability curinga toc:*", capability_curinga),
    ("mode fora do enum do Anexo B", modo_inventado),
    ("ação sem `risk`", acao_sem_risco),
    ("tela sem namespace <ns>.<id>", tela_sem_namespace),
    ("url sem https", url_sem_https),
    ("batch_atomicity no manifesto (L-02)", batch_atomicity_no_manifesto),
]

passaram = []
for nome, ataque in SABOTAGENS:
    alvo = ataque(copy.deepcopy(manifesto))
    quantos = len(list(validador.iter_errors(alvo)))
    marca = "repelida" if quantos else "PASSOU"
    print(f"  sabotagem [{marca}] {nome} — {quantos} erro(s)")
    if not quantos:
        passaram.append(nome)

print(f"\n  sabotagens aplicadas: {len(SABOTAGENS)}; repelidas: {len(SABOTAGENS) - len(passaram)}")
if passaram:
    print(f"✗ o validador aceitou manifesto sabotado: {passaram}", file=sys.stderr)
    sys.exit(1)
print("✓ manifesto válido e as 7 sabotagens recusadas.")
PYEOF
