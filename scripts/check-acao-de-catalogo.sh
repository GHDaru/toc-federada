#!/usr/bin/env bash
# check-acao-de-catalogo.sh — a ação do catálogo despacha para a raiz da ferramenta dela.
#
# Siglas, uma vez: **APH** — Aplicação ↔ Harness (o padrão da fronteira) · **M1** —
# Núcleo de Diagramas Lógicos (o núcleo genérico de projeto, nó e aresta) · **ARA** —
# Árvore da Realidade Atual · **DDD** — *Domain-Driven Design* (Design Orientado a
# Domínio) · **AST** — *Abstract Syntax Tree* (árvore sintática abstrata) · **IA** —
# inteligência artificial · **TOC** — Teoria das Restrições.
#
# ── O defeito que este portão existe para não deixar voltar ──────────────────────────
#
# O ciclo 006 ligou as quatro ações mutadoras do catálogo — `toc.criar_nos`,
# `toc.criar_arestas`, `toc.atualizar_no`, `toc.excluir_nos` — aos casos de uso
# **genéricos** do M1 (`AdicionarNo`, `LigarNos`, `EditarNo`, `ExcluirNo`), anunciando
# `ui_route: /toc/ara`. Enquanto o `Projeto` aceitava mutação crua, isso MUTILAVA a
# ferramenta por fora das invariantes dela. Quando `Projeto._exigir_raiz` fechou essa
# porta, o mesmo despacho passou a falhar **para sempre** em ara, nc, arf, apr, at e
# focalização: a assistência da fundação — o motivo de a aplicação ser federada — deixou
# de alcançar qualquer ferramenta do produto. Um defeito virou o outro, e nenhum portão
# viu, porque nenhum portão olhava para a LIGAÇÃO entre a ação e o caso de uso.
#
# Este é esse portão. Decisão: `docs/adr/0015-acao-de-catalogo-pela-raiz-da-ferramenta.md`.
#
# ── O que ele verifica, exatamente ───────────────────────────────────────────────────
#
#   1. Toda ação `risk: confirm` do catálogo declara `ferramenta` — sem ela não há como
#      saber por qual raiz de agregado a ação escreve;
#   2. ação de ferramenta COM RAIZ **não** aciona caso de uso do módulo genérico
#      (`aplicacao.grafo`) — é a regressão em pessoa;
#   3. ação declarada `generico` **não** aciona caso de uso de ferramenta — o inverso,
#      que produziria o mesmo desencontro com os papéis trocados;
#   4. toda ação mutadora do catálogo tem entrada no despacho do executor, e toda entrada
#      do despacho é uma ação do catálogo (declarada e inexecutável é dívida silenciosa);
#   5. toda ação mutadora resolve ao menos um caso de uso — mão que não chama nada não
#      escreve nada, e o desfecho `executed` seria mentira.
#
# A leitura é **estática** (AST do Python), sobre dois arquivos: o catálogo do domínio e
# o executor da infraestrutura. Nada é importado, nada é executado — o portão roda sobre
# um fixture tanto quanto sobre o serviço.
#
# Regra R2 do `CLAUDE.md` (portão verde diz quanto examinou): a saída imprime quantas
# ações foram lidas, quantas entradas de despacho, quantas ligações ação→caso de uso
# foram resolvidas e quantos casos de uso genéricos ele conhece.
#
# Uso: scripts/check-acao-de-catalogo.sh [raiz]   (padrão: a raiz do repositório)
# Saída: 0 conforme · 1 violação encontrada · 2 ambiente não montado.
set -uo pipefail

AQUI="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RAIZ="${1:-$AQUI}"
CATALOGO="$RAIZ/apps/api/src/toc_api/dominio/federacao/catalogo.py"
EXECUTOR="$RAIZ/apps/api/src/toc_api/infra/federacao/executor.py"

PY="$AQUI/apps/api/.venv/bin/python"
[[ -x "$PY" ]] || PY="$(command -v python3 || true)"

echo "── Ação do catálogo × raiz da ferramenta (ADR 0015) ──"

[[ -n "$PY" ]] || { echo "✗ nenhum interpretador Python disponível" >&2; exit 2; }
[[ -f "$CATALOGO" ]] || { echo "✗ catálogo ausente: $CATALOGO" >&2; exit 2; }
[[ -f "$EXECUTOR" ]] || { echo "✗ executor ausente: $EXECUTOR" >&2; exit 2; }

echo "  catálogo: ${CATALOGO#$RAIZ/}"
echo "  executor: ${EXECUTOR#$RAIZ/}"

"$PY" - "$CATALOGO" "$EXECUTOR" <<'PYEOF'
"""Leitura estática do par catálogo × executor. Nada é importado, nada é executado."""
import ast
import sys

catalogo_py, executor_py = sys.argv[1], sys.argv[2]

# ── 1. o catálogo: action_id → (risco, token da ferramenta) ────────────────────────
#
# A ferramenta é lida como TOKEN (`FERRAMENTA_ARA`, `FERRAMENTA_GENERICA`), não como
# string: o portão não precisa saber o valor, só precisa distinguir "genérica" de
# "alguma ferramenta com raiz". Ler o token evita resolver import entre módulos e é o que
# permite este portão rodar sobre um fixture de dois arquivos.
GENERICA = "FERRAMENTA_GENERICA"
acoes = {}
for no in ast.walk(ast.parse(open(catalogo_py, encoding="utf-8").read(), catalogo_py)):
    if not (isinstance(no, ast.Call) and getattr(no.func, "id", "") == "AcaoDoCatalogo"):
        continue
    campos = {}
    for chave in no.keywords:
        if isinstance(chave.value, ast.Constant):
            campos[chave.arg] = chave.value.value
        elif isinstance(chave.value, ast.Name):
            campos[chave.arg] = chave.value.id
    action_id = campos.get("action_id")
    if action_id:
        acoes[action_id] = (campos.get("risk"), campos.get("ferramenta"))

# ── 2. o executor: imports, ligações do construtor, despacho e corpo das mãos ──────
arvore = ast.parse(open(executor_py, encoding="utf-8").read(), executor_py)

#: Classe de caso de uso → módulo de origem, pelos imports do próprio arquivo.
modulo_da_classe = {}
for no in ast.walk(arvore):
    if isinstance(no, ast.ImportFrom) and no.module:
        for apelido in no.names:
            modulo_da_classe[apelido.asname or apelido.name] = no.module

def e_generico(classe: str) -> bool:
    """Caso de uso do M1 genérico: o módulo `aplicacao.grafo` e o `aplicacao.projetos`.

    São os dois módulos que operam o `Projeto` cru, sem raiz de ferramenta acima. É deles
    que veio a regressão, e é a fronteira que este portão guarda.
    """
    modulo = modulo_da_classe.get(classe, "")
    return modulo.endswith("aplicacao.grafo") or modulo.endswith("aplicacao.projetos")

classe_da_classe = classe = None
classes = [n for n in arvore.body if isinstance(n, ast.ClassDef) and n.name == "ExecutorDoCatalogo"]
if not classes:
    print("✗ `ExecutorDoCatalogo` não encontrado no executor", file=sys.stderr)
    sys.exit(1)
corpo = classes[0]

#: `self._atributo` → classe do caso de uso montada nele, no `__init__`.
caso_de_uso_do_atributo = {}
#: action_id → nome do método que o executa (a tabela `self._despacho`).
despacho = {}
#: nome do método → atributos `self._x` em que ele chama `.rodar(...)`.
usados_pelo_metodo = {}

def _classe_chamada(valor):
    """A classe construída num `self._x = Classe(...)`, inclusive dentro de ternário."""
    if isinstance(valor, ast.IfExp):
        for ramo in (valor.body, valor.orelse):
            achada = _classe_chamada(ramo)
            if achada:
                return achada
        return None
    if isinstance(valor, ast.Call) and isinstance(valor.func, ast.Name):
        return valor.func.id
    return None

for metodo in corpo.body:
    if not isinstance(metodo, ast.FunctionDef):
        continue
    if metodo.name == "__init__":
        for no in ast.walk(metodo):
            # `self._x = ...` e `self._x: T = ...` — a tabela de despacho real é anotada,
            # e um portão que só lesse `ast.Assign` responderia verde sobre zero entradas.
            if isinstance(no, (ast.Assign, ast.AnnAssign)):
                alvos = no.targets if isinstance(no, ast.Assign) else [no.target]
                if len(alvos) != 1 or no.value is None:
                    continue
                alvo = alvos[0]
                if (
                    isinstance(alvo, ast.Attribute)
                    and isinstance(alvo.value, ast.Name)
                    and alvo.value.id == "self"
                ):
                    achada = _classe_chamada(no.value)
                    if achada:
                        caso_de_uso_do_atributo[alvo.attr] = achada
                    elif isinstance(no.value, ast.Dict):
                        for chave, valor in zip(no.value.keys, no.value.values):
                            if (
                                isinstance(chave, ast.Constant)
                                and isinstance(valor, ast.Attribute)
                                and isinstance(valor.value, ast.Name)
                                and valor.value.id == "self"
                            ):
                                despacho[chave.value] = valor.attr
    usados = set()
    for no in ast.walk(metodo):
        if (
            isinstance(no, ast.Call)
            and isinstance(no.func, ast.Attribute)
            and no.func.attr == "rodar"
            and isinstance(no.func.value, ast.Attribute)
            and isinstance(no.func.value.value, ast.Name)
            and no.func.value.value.id == "self"
        ):
            usados.add(no.func.value.attr)
    usados_pelo_metodo[metodo.name] = usados

genericos = sorted(c for c in caso_de_uso_do_atributo.values() if e_generico(c))
ligacoes = 0
falhas = []

# ── 3. as cinco verificações ───────────────────────────────────────────────────────
mutadoras = {a for a, (risco, _) in acoes.items() if risco == "confirm"}

for action_id in sorted(mutadoras):
    _, ferramenta = acoes[action_id]
    if not ferramenta:
        falhas.append(
            f"{action_id}: ação mutadora sem `ferramenta` declarada — não há como saber "
            "por qual raiz de agregado ela escreve"
        )

sem_despacho = sorted(mutadoras - set(despacho))
if sem_despacho:
    falhas.append(
        "ação mutadora do catálogo sem execução declarada no despacho: "
        + ", ".join(sem_despacho)
    )
fora_do_catalogo = sorted(set(despacho) - set(acoes))
if fora_do_catalogo:
    falhas.append(
        "entrada de despacho sem ação correspondente no catálogo: "
        + ", ".join(fora_do_catalogo)
    )

for action_id, metodo in sorted(despacho.items()):
    risco, ferramenta = acoes.get(action_id, (None, None))
    if ferramenta is None:
        continue
    classes_usadas = sorted(
        caso_de_uso_do_atributo[a]
        for a in usados_pelo_metodo.get(metodo, set())
        if a in caso_de_uso_do_atributo
    )
    ligacoes += len(classes_usadas)
    if risco == "confirm" and not classes_usadas:
        falhas.append(
            f"{action_id}: ação mutadora que não aciona caso de uso nenhum — "
            f"`{metodo}` não chama `.rodar(` em atributo montado no construtor"
        )
    if ferramenta != GENERICA:
        intrusos = [c for c in classes_usadas if e_generico(c)]
        if intrusos:
            falhas.append(
                f"{action_id}: ferramenta com raiz acionando caso de uso genérico do M1 "
                f"({', '.join(intrusos)}) — a ferramenta {ferramenta} tem raiz própria e "
                "o grafo dela só muda por dentro dela (ADR 0015)"
            )
    else:
        intrusos = [c for c in classes_usadas if not e_generico(c)]
        if intrusos:
            falhas.append(
                f"{action_id}: ação genérica acionando caso de uso de ferramenta "
                f"({', '.join(intrusos)}) — o desencontro é o mesmo, com os papéis trocados"
            )

print(f"  ações lidas do catálogo: {len(acoes)} (mutadoras: {len(mutadoras)})")
print(f"  entradas no despacho do executor: {len(despacho)}")
print(f"  ligações ação → caso de uso resolvidas: {ligacoes}")
print(f"  casos de uso genéricos do M1 conhecidos: {len(genericos)} ({', '.join(genericos)})")
por_ferramenta = {}
for action_id in sorted(mutadoras):
    por_ferramenta.setdefault(acoes[action_id][1] or "(não declarada)", []).append(action_id)
for ferramenta, lista in sorted(por_ferramenta.items()):
    print(f"    {ferramenta}: {len(lista)} ação(ões) mutadora(s)")

if falhas:
    print()
    for falha in falhas:
        print(f"✗ {falha}", file=sys.stderr)
    sys.exit(1)
PYEOF

CODIGO=$?
echo
if [[ $CODIGO -ne 0 ]]; then
  echo "✗ há ação de catálogo despachando para a camada errada." >&2
  echo "  O caminho NÃO é destravar o núcleo nem afrouxar a guarda da raiz: é dar à" >&2
  echo "  ferramenta a ação DELA e despachá-la para os casos de uso da raiz dela." >&2
  exit $CODIGO
fi
echo "✓ toda ação mutadora declara a ferramenta e despacha pela raiz dela."
