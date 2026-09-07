#!/usr/bin/env bash
# check-versao-do-agregado.sh — toda mutação de estado próprio do agregado avança a versão.
#
# Siglas, uma vez: **ARA** — Árvore da Realidade Atual · **NC** — Nuvem de Conflito ·
# **UDE** — Efeito Indesejável (*undesirable effect*) · **M1** — Núcleo de Diagramas
# Lógicos · **M2** — Árvore da Realidade Atual · **AST** — *Abstract Syntax Tree* (árvore
# sintática abstrata) · **SQL** — *Structured Query Language* · **TOC** — Teoria das
# Restrições · **ADR** — *Architecture Decision Record* (registro de decisão arquitetural).
#
# ── O defeito que este portão existe para não deixar voltar ──────────────────────────
#
# A trava otimista do ADR 0010 tem DUAS metades, e o portão que já existia
# (`scripts/check-trava-otimista.sh`) só media uma:
#
#   * a metade do adaptador — `UPDATE … WHERE versao = :versao_lida`, o `rowcount`
#     conferido, o `ConflitoDeVersao` levantado. **Essa está medida.**
#   * a metade do domínio — **a versão só protege o que ela acompanha**. Se um agregado
#     muda estado persistido sem chamar `Projeto._avancar`, as duas escritas que leram a
#     mesma versão casam as DUAS no `WHERE`, as duas são aceitas, e a reconciliação apaga
#     do banco o retrato de quem gravou primeiro. **Essa não estava medida por nada.**
#
# A ARA passou por várias ondas dentro desse buraco. Ela é o único agregado de ferramenta
# anterior à trava que tem delegação ao núcleo que CRIA linha (`adicionar_efeito`,
# `ligar`): o teste de concorrência escrito para provar que "a ARA tem a mesma trava que o
# M1" ia verde pelo `_avancar` do NÚCLEO, sem tocar em uma linha de semântica da
# ferramenta. Marcar UDE, editar a ficha, registrar parecer, mudar status para `validado`,
# examinar elo e formar conector não avançavam versão nenhuma. Medido contra o PostgreSQL
# real, em `apps/api/tests/integracao/test_concorrencia_no_postgres.py`:
#
#   concorrência M2 (parecer da ARA): 20 escritas · aceitas 20 · recusadas 0 ·
#   pareceres no banco 1
#
# Dezenove pareceres humanos aceitos e apagados em silêncio, no módulo onde mais gente
# trabalha junto. A Nuvem de Conflito escapou por acaso de topologia: ela não tem
# delegação ao núcleo que crie linha (RN-01 da spec 007 — as 5 entidades e 7 arestas
# nascem juntas), então o teste de concorrência dela **teve** de disputar uma mutação
# própria, e o `_avancar` entrou.
#
# ── Por que ele existe em vez de "acrescentar as chamadas" ───────────────────────────
#
# Porque a trava foi aplicada agregado a agregado, à mão, e o único que ficou de fora
# passou despercebido por várias ondas. Uma lista escrita à mão neste script repetiria o
# mesmo erro com outro nome. Por isso o **denominador vem do registro do serviço**: toda
# raiz de ferramenta é obrigada a se anunciar em `registrar_raiz_de_ferramenta` para
# existir (sem isso `Projeto._exigir_raiz` bloqueia o grafo dela — fail-closed), e é essa
# lista que este portão compara com a lista das que avançam versão. Agregado novo que
# nasça fora da trava reprova no primeiro commit, sem ninguém lembrar de nada.
#
# ── O que ele verifica, exatamente ───────────────────────────────────────────────────
#
#   1. Toda raiz de ferramenta registrada existe como classe no domínio;
#   2. **todo método que escreve estado PRÓPRIO do agregado avança a versão** — por
#      `self.projeto._avancar(...)` ou delegando ao núcleo (`with self._nucleo()`), que
#      avança por dentro. Auxiliar privado é aceito quando TODO chamador dele avança;
#      método que só lê e emite evento de relatório não escreve estado e não entra;
#   3. **o inverso**: toda raiz registrada tem caminho de escrita no adaptador SQL, e todo
#      `salvar_*` que recebe uma raiz de ferramenta passa pela trava (`_gravar_projeto`) —
#      um agregado que avança versão e grava sem condição é o mesmo defeito ao contrário;
#   4. nenhum `salvar_*` grava uma raiz de ferramenta que não esteja registrada.
#
# A leitura é **estática** (AST do Python): nada é importado, nada é executado — o portão
# roda sobre um fixture tanto quanto sobre o serviço.
#
# ── Uma escolha deliberada de rigor ──────────────────────────────────────────────────
#
# Ele NÃO aceita como avanço "chamei um método irmão que avança". Aceitaria de graça o
# caso `if condicao: self.outro(...)`, em que um ramo escreve e não avança — e a
# permissividade é exatamente o que produziu o defeito que ele existe para não deixar
# voltar. O preço é um falso positivo possível no futuro; o preço é aceitável porque um
# falso positivo aqui é uma reprovação barulhenta com o nome do método na saída, enquanto
# o falso negativo é trabalho de gente apagado em silêncio. Auxiliar PRIVADO é a única
# indulgência, e ela é condicionada: só passa se tiver chamador e se TODOS os chamadores
# estiverem em dia.
#
# Regra R2 do `CLAUDE.md` (portão verde diz quanto examinou): a saída imprime quantas
# raízes foram lidas do registro, quantos métodos foram classificados, quantos escrevem
# estado próprio e quantos caminhos de escrita foram casados.
#
# Uso: scripts/check-versao-do-agregado.sh [raiz]   (padrão: a raiz do repositório)
# Saída: 0 conforme · 1 violação encontrada · 2 ambiente não montado.
set -uo pipefail

AQUI="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RAIZ="${1:-$AQUI}"
DOMINIO="$RAIZ/apps/api/src/toc_api/dominio"
REPO="$RAIZ/apps/api/src/toc_api/infra/persistencia/repositorio_projetos.py"

PY="$AQUI/apps/api/.venv/bin/python"
[[ -x "$PY" ]] || PY="$(command -v python3 || true)"

echo "── Versão do agregado: mutação de estado próprio avança a versão (ADR 0010) ──"

[[ -n "$PY" ]] || { echo "✗ nenhum interpretador Python disponível" >&2; exit 2; }
[[ -d "$DOMINIO" ]] || { echo "✗ domínio ausente: $DOMINIO" >&2; exit 2; }
[[ -f "$REPO" ]] || { echo "✗ adaptador ausente: $REPO" >&2; exit 2; }

echo "  domínio:   ${DOMINIO#$RAIZ/}"
echo "  adaptador: ${REPO#$RAIZ/}"

"$PY" - "$DOMINIO" "$REPO" <<'PYEOF'
"""Leitura estática do domínio × adaptador. Nada é importado, nada é executado."""
import ast
import pathlib
import sys

DOMINIO = pathlib.Path(sys.argv[1])
REPO = pathlib.Path(sys.argv[2])

#: Chamadas que MUTAM a coleção em que são feitas. `get`, `keys`, `values` e afins ficam
#: de fora de propósito: leitura não precisa de versão, e um portão que exigisse versão
#: de leitura seria ignorado em duas semanas.
MUTADORES = {"append", "extend", "insert", "remove", "pop", "popitem", "clear",
             "setdefault", "update", "add", "discard", "sort"}

#: Como um método avança a versão: direto (`self.projeto._avancar`), abrindo o núcleo pela
#: chave da raiz (`with self._nucleo()`), ou chamando uma mutação PÚBLICA do núcleo que
#: avança por dentro (`self.projeto.descrever_problema(...)`, por exemplo). Este último
#: caso não é indulgência: `Projeto.descrever_problema` chama `_avancar` na linha seguinte
#: à escrita, e exigir uma segunda chamada faria a versão pular de dois em dois.
AVANCO_DIRETO = "_avancar"
PORTAS_DO_NUCLEO = {"_nucleo", "sob_a_raiz"}

#: Métodos `dunder`. Ficam de fora porque rodam na CONSTRUÇÃO — inclusive na reidratação,
#: que é leitura. Um `__post_init__` que avançasse versão sujaria todo agregado lido do
#: banco, e a primeira gravação seguinte seria recusada sem que ninguém tivesse concorrido.
CONSTRUCAO = lambda nome: nome.startswith("__") and nome.endswith("__")

#: As mutações do núcleo que avançam a versão, lidas de `projeto.py` — nunca de uma lista
#: escrita à mão aqui, que envelheceria calada na primeira mutação nova do M1.
def mutacoes_do_nucleo_que_avancam(caminho):
    if not caminho.is_file():
        return set()
    arvore = ast.parse(caminho.read_text(encoding="utf-8"))
    avancam = set()
    for classe in [n for n in arvore.body if isinstance(n, ast.ClassDef)]:
        for metodo in [m for m in classe.body if isinstance(m, ast.FunctionDef)]:
            if any(isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                   and n.func.attr == "_avancar" for n in ast.walk(metodo)):
                avancam.add(metodo.name)
    return avancam


NUCLEO_AVANCA = mutacoes_do_nucleo_que_avancam(DOMINIO / "projeto.py")

falhou = False
def reprova(*linhas):
    global falhou
    falhou = True
    for linha in linhas:
        print(linha, file=sys.stderr)


# -- 1. o registro de raízes de ferramenta é o denominador -----------------------------

registros = {}   # classe -> (ferramenta, arquivo)
classes = {}     # classe -> (ast.ClassDef, arquivo)
arquivos = sorted(p for p in DOMINIO.rglob("*.py") if "__pycache__" not in str(p))

for caminho in arquivos:
    arvore = ast.parse(caminho.read_text(encoding="utf-8"))
    constantes = {}
    for no in arvore.body:
        if isinstance(no, ast.Assign) and isinstance(no.value, ast.Constant):
            for alvo in no.targets:
                if isinstance(alvo, ast.Name):
                    constantes[alvo.id] = no.value.value
        if isinstance(no, ast.ClassDef):
            classes[no.name] = (no, caminho)
    for no in ast.walk(arvore):
        if not (isinstance(no, ast.Call) and isinstance(no.func, ast.Name)):
            continue
        if no.func.id != "registrar_raiz_de_ferramenta" or len(no.args) < 2:
            continue
        bruto = no.args[0]
        ferramenta = (bruto.value if isinstance(bruto, ast.Constant)
                      else constantes.get(getattr(bruto, "id", ""), getattr(bruto, "id", "?")))
        alvo = no.args[1]
        if isinstance(alvo, ast.Constant):
            registros[alvo.value] = (ferramenta, caminho)

print(f"  arquivos de domínio varridos: {len(arquivos)}")
print(f"  raízes de ferramenta lidas do registro: {len(registros)}")
for nome, (ferramenta, caminho) in sorted(registros.items()):
    print(f"    {ferramenta:14} → {nome} ({caminho.name})")

if len(registros) < 2:
    reprova(f"✗ o registro tem {len(registros)} raiz(es) de ferramenta; esperava ao menos",
            "  duas (a ARA e a Nuvem de Conflito). Sem denominador não há portão.")

ausentes = [n for n in registros if n not in classes]
if ausentes:
    reprova(f"✗ raiz registrada sem classe no domínio: {', '.join(sorted(ausentes))}")


# -- 2. todo método que escreve estado próprio avança a versão -------------------------

def escreve_estado_proprio(metodo):
    """Assinala escrita em `self.<campo>` ou `self._<campo>`, NUNCA em `self.projeto.*`.

    `self.projeto.eventos = …` (o `_emitir` de toda raiz) é escrita no NÚCLEO, não no
    estado próprio: quem responde por ela é o `Projeto`, e evento drenado não é retrato
    reconciliado. Por isso a base do alvo tem de ser o próprio `self`.
    """
    def base_propria(no):
        while isinstance(no, ast.Subscript):
            no = no.value
        return (isinstance(no, ast.Attribute)
                and isinstance(no.value, ast.Name) and no.value.id == "self"
                and no.attr != "projeto")

    for no in ast.walk(metodo):
        if isinstance(no, (ast.Assign, ast.AugAssign, ast.AnnAssign)):
            alvos = no.targets if isinstance(no, ast.Assign) else [no.target]
            if any(base_propria(a) for a in alvos):
                return True
        if isinstance(no, ast.Delete) and any(base_propria(a) for a in no.targets):
            return True
        if (isinstance(no, ast.Call) and isinstance(no.func, ast.Attribute)
                and no.func.attr in MUTADORES and base_propria(no.func.value)):
            return True
    return False


def avanca(metodo):
    for no in ast.walk(metodo):
        if isinstance(no, ast.With):
            for item in no.items:
                ctx = item.context_expr
                if (isinstance(ctx, ast.Call) and isinstance(ctx.func, ast.Attribute)
                        and ctx.func.attr in PORTAS_DO_NUCLEO):
                    return True
        if not (isinstance(no, ast.Call) and isinstance(no.func, ast.Attribute)):
            continue
        if no.func.attr == AVANCO_DIRETO:
            return True
        alvo = no.func.value
        if (isinstance(alvo, ast.Attribute) and alvo.attr == "projeto"
                and isinstance(alvo.value, ast.Name) and alvo.value.id == "self"
                and no.func.attr in NUCLEO_AVANCA):
            return True
    return False


def chama(metodo, nome):
    return any(isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
               and isinstance(n.func.value, ast.Name) and n.func.value.id == "self"
               and n.func.attr == nome
               for n in ast.walk(metodo))


examinados = escritores = 0
for nome_da_classe in sorted(registros):
    if nome_da_classe not in classes:
        continue
    corpo, caminho = classes[nome_da_classe]
    metodos = {m.name: m for m in corpo.body if isinstance(m, ast.FunctionDef)}
    examinados += len(metodos)

    escrevem = {n: m for n, m in metodos.items()
                if escreve_estado_proprio(m) and not CONSTRUCAO(n)}
    escritores += len(escrevem)
    avanca_por_si = {n for n, m in metodos.items() if avanca(m)}

    # Auxiliar PRIVADO **carrega o avanço do chamador** quando ele TEM chamador na classe
    # e TODOS os chamadores avançam — direto, ou carregando o avanço dos deles. É o caso do
    # `_revalidar` da ARA, que muda o status e é chamado por `marcar_ude`, `editar_no` e
    # `reformular`, os três avançando.
    #
    # A condição é "o chamador AVANÇA", nunca "o chamador não deve nada": um método que não
    # escreve estado próprio nunca entraria na lista de devedores, e perdoaria o auxiliar
    # sem que versão nenhuma tivesse andado. Exigir chamador é o que impede um auxiliar
    # órfão de se perdoar sozinho.
    carregam = set()
    mudou = True
    while mudou:
        mudou = False
        for nome, metodo in metodos.items():
            if (not nome.startswith("_") or CONSTRUCAO(nome)
                    or nome in avanca_por_si or nome in carregam):
                continue
            chamadores = [n for n, m in metodos.items()
                          if n != nome and chama(m, nome) and not CONSTRUCAO(n)]
            if chamadores and all(c in avanca_por_si or c in carregam for c in chamadores):
                carregam.add(nome)
                mudou = True

    devedores = {n for n in escrevem if n not in avanca_por_si and n not in carregam}

    marca = "✓" if not devedores else "✗"
    print(f"  {marca} {nome_da_classe}: {len(metodos)} método(s), "
          f"{len(escrevem)} escreve(m) estado próprio, "
          f"{len(escrevem) - len(devedores)} avança(m) a versão")
    if devedores:
        reprova(
            f"✗ {nome_da_classe} ({caminho.name}) muta estado próprio e NÃO avança a versão:",
            *(f"    {nome_da_classe}.{d}" for d in sorted(devedores)),
            "  Sem `self.projeto._avancar(em)` a coluna `versao` não acompanha a mudança,",
            "  duas escritas que leram a MESMA versão casam as duas no `WHERE versao =`,",
            "  e a reconciliação apaga do banco o retrato de quem gravou primeiro — sem",
            "  conflito para ninguém e sem aviso para quem perdeu (ADR 0010).",
        )

print(f"  métodos classificados: {examinados} · escrevem estado próprio: {escritores}")


# -- 3 e 4. o inverso: quem avança versão tem escrita condicionada ---------------------

arvore_repo = ast.parse(REPO.read_text(encoding="utf-8"))
caminhos = {}   # nome do salvar_* -> (classe anotada, passa pela trava)
for classe in [n for n in arvore_repo.body if isinstance(n, ast.ClassDef)]:
    for metodo in [m for m in classe.body if isinstance(m, ast.FunctionDef)]:
        if not metodo.name.startswith("salvar"):
            continue
        anotada = None
        for argumento in metodo.args.args[1:]:
            if isinstance(argumento.annotation, ast.Name):
                anotada = argumento.annotation.id
        trava = any(isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                    and n.func.attr.startswith("_gravar_")
                    for n in ast.walk(metodo))
        caminhos[metodo.name] = (anotada, trava)

print(f"  caminhos de escrita no adaptador: {len(caminhos)}")

por_classe = {}
for nome, (anotada, trava) in caminhos.items():
    por_classe.setdefault(anotada, []).append((nome, trava))

casados = 0
for nome_da_classe in sorted(registros):
    entradas = por_classe.get(nome_da_classe, [])
    if not entradas:
        reprova(
            f"✗ a raiz {nome_da_classe} está registrada e não tem `salvar_*` que a receba:",
            "  ou o agregado não é persistido (e não devia estar no registro), ou grava",
            "  por um caminho que este portão não vê — que é como um agregado nasce fora",
            "  da trava sem ninguém notar.",
        )
        continue
    for nome, trava in entradas:
        if not trava:
            reprova(
                f"✗ `{nome}` grava {nome_da_classe} sem passar por `_gravar_*`: a escrita",
                "  não se condiciona à versão lida. É a perda de atualização ao contrário —",
                "  o agregado avança a versão e a grava por cima da de quem chegou antes.",
            )
        else:
            casados += 1

# Uma classe do domínio que o adaptador grava, que NÃO é o núcleo genérico e que não está
# registrada como raiz de ferramenta é exatamente "agregado novo nascido fora da trava".
NUCLEO_E_AGREGADOS_PROPRIOS = {"Projeto", "ReferenciaCruzada"}
for nome, (anotada, _) in sorted(caminhos.items()):
    if anotada is None:
        reprova(f"✗ `{nome}` não anota o agregado que recebe: sem o tipo não há como casar",
                "  o caminho de escrita com a raiz de ferramenta que ele grava.")
        continue
    if anotada in registros or anotada in NUCLEO_E_AGREGADOS_PROPRIOS:
        continue
    reprova(
        f"✗ `{nome}` grava `{anotada}`, que não está registrada como raiz de ferramenta",
        "  nem é agregado próprio declarado. Agregado novo entra no registro do domínio",
        "  no MESMO commit em que ganha caminho de escrita — é assim que a trava deixa de",
        "  ser aplicada à mão, um agregado de cada vez.",
    )

print(f"  raízes casadas com caminho de escrita condicionado: {casados} de {len(registros)}")

if falhou:
    print("\n✗ a versão do agregado deixou de acompanhar alguma mutação de estado próprio.",
          file=sys.stderr)
    sys.exit(1)
print(f"\n✓ versão íntegra: {len(registros)} raiz(es) do registro, {escritores} método(s) que "
      f"escrevem\n  estado próprio, {casados} caminho(s) de escrita condicionado(s), "
      f"{len(arquivos)} arquivo(s) varrido(s).")
PYEOF
SAIDA=$?
exit $SAIDA
