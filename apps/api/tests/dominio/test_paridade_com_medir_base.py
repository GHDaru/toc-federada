"""Paridade: o domínio decide o MESMO que `docs/produto/dados/medir-base.py`.

Por que este teste existe, e por que ele importa o script em vez de recopiar números:
o script foi o trabalho já feito — ele traduziu sete das onze características de UDE
(Efeito Indesejável) de `tocbuilderv3/constants.ts:122-133` em oito checagens puras, e a
saída dele está **publicada** em `docs/produto/visao.md` §6 e em
`docs/produto/dados/README.md`. O domínio do ciclo 005 traz essa lógica para dentro do
serviço; se ele decidisse diferente, um dos dois estaria errado e ninguém saberia qual.

A regra R1 do `CLAUDE.md` proíbe transcrever número: este teste **executa** o script e
compara veredito a veredito.

**A única divergência permitida é o K-03** — o falso negativo que o conjunto de controle
encontrou (`visao.md` §6, defeito D-12): a fonte rotula "Falta de treinamento causa
erros." como Exemplo Ruim, e a CD-7 do script aprova porque procura conectivo e não verbo
causal. O domínio o reprova. Qualquer OUTRA divergência derruba este teste — é assim que
"trazer a lógica, não reinventá-la" vira um fato verificável em vez de uma promessa.

O script é biblioteca padrão pura: importá-lo não traz rede, banco nem framework.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

from toc_api.dominio.criterios_ude import Veredito, validar_formalmente

RAIZ = Path(__file__).resolve().parents[4]
SCRIPT = RAIZ / "docs" / "produto" / "dados" / "medir-base.py"
BASE = RAIZ / "docs" / "produto" / "dados" / "analise-horizonte.json"

#: A divergência declarada, com a sua fonte. Fechar o falso negativo é o objetivo do
#: ciclo; ampliar esta lista sem ADR seria afrouxar o portão.
DIVERGENCIA_ESPERADA = {"K-03"}


def carregar_script():
    if not SCRIPT.exists():  # pragma: no cover - o script é versionado
        pytest.skip(f"{SCRIPT} não existe neste checkout")
    spec = importlib.util.spec_from_file_location("medir_base", SCRIPT)
    modulo = importlib.util.module_from_spec(spec)
    sys.modules["medir_base"] = modulo
    # Importar não pode SUJAR o repositório: sem esta guarda, o CPython grava
    # `docs/produto/dados/__pycache__/medir-base.cpython-311.pyc`, que é versionado, e o
    # teste apareceria como alteração de arquivo binário em toda execução.
    escrevia = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    try:
        spec.loader.exec_module(modulo)
    finally:
        sys.dont_write_bytecode = escrevia
    return modulo


@pytest.fixture(scope="module")
def script():
    return carregar_script()


def codigos_do_script(motivos: list[str]) -> set[str]:
    """Os motivos do script vêm como `"CD-7 traz a própria causa: ..."`."""
    return {m.split(" ", 1)[0] for m in motivos}


def codigos_do_dominio(texto: str) -> set[str]:
    return {
        v.criterio.codigo
        for v in validar_formalmente(texto).vereditos
        if v.veredito is Veredito.NAO_ATENDE
    }


def test_o_script_e_o_dominio_traduzem_as_mesmas_caracteristicas(script):
    from toc_api.dominio.criterios_ude import CRITERIOS_DECIDIVEIS, CRITERIOS_DE_JULGAMENTO

    assert len(script.CRITERIOS) == len(CRITERIOS_DECIDIVEIS) == 8
    assert [c[0] for c in script.CRITERIOS] == [c.codigo for c in CRITERIOS_DECIDIVEIS]
    # a característica de origem de cada checagem tem de bater sigla a sigla
    assert [c[2] for c in script.CRITERIOS] == [
        c.caracteristica for c in CRITERIOS_DECIDIVEIS
    ]
    assert {n for n, _ in script.INDECIDIVEIS} == {
        c.caracteristica for c in CRITERIOS_DE_JULGAMENTO
    }


def test_os_doze_udes_da_base_autoral_decidem_igual(script, capsys):
    """Base sintética da Instituição Horizonte (ADR 0006) — 12 UDEs, 9 reprovados."""
    base = json.loads(BASE.read_text(encoding="utf-8"))
    udes = [n for n in base["ara"]["nos"] if n["tipo"] == "ude"]
    assert len(udes) == 12, "a base mudou de tamanho: reveja o número publicado na visão"

    divergentes = []
    reprovados = []
    for ude in udes:
        passou_script, motivos = script.avalia(ude["texto"])
        do_script = codigos_do_script(motivos)
        do_dominio = codigos_do_dominio(ude["texto"])
        if do_script != do_dominio:
            divergentes.append((ude["id"], sorted(do_script), sorted(do_dominio)))
        if do_dominio:
            reprovados.append(ude["id"])
        assert passou_script is (not do_dominio), ude["id"]

    with capsys.disabled():
        print(
            f"\n  paridade autoral: {len(udes)} UDEs examinados · "
            f"reprovados pelo domínio: {len(reprovados)} ({', '.join(reprovados)}) · "
            f"divergências com medir-base.py: {len(divergentes)}"
        )
    assert divergentes == []
    assert len(reprovados) == 9


def test_o_conjunto_de_controle_diverge_apenas_no_falso_negativo(script, capsys):
    """Nove enunciados escritos ANTES e FORA daqui, rotulados pela própria linhagem."""
    assert len(script.CONTROLE) == 9

    divergentes = {}
    for item in script.CONTROLE:
        texto = script.normaliza_pontuacao(item["texto"])
        passou_script, _ = script.avalia(texto)
        passou_dominio = not codigos_do_dominio(texto)
        if passou_script != passou_dominio:
            divergentes[item["id"]] = (passou_script, passou_dominio)

    with capsys.disabled():
        print(
            f"  paridade de controle: {len(script.CONTROLE)} enunciados examinados · "
            f"divergências: {sorted(divergentes)} (esperada: "
            f"{sorted(DIVERGENCIA_ESPERADA)})"
        )
    assert set(divergentes) == DIVERGENCIA_ESPERADA
    # e a divergência é na direção certa: o script aprovava, o domínio reprova.
    assert divergentes["K-03"] == (True, False)


def test_nenhum_falso_negativo_sobra_contra_o_rotulo_da_fonte(script, capsys):
    """O número que o ciclo 005 tem de mover: falsos negativos 1 → 0.

    O rótulo é o da FONTE (`tocbuilderv3/constants.ts`), nunca nosso — é o que impede
    ajustar o gabarito até ficar verde.
    """
    falsos_negativos, falsos_positivos, rotulados = [], [], 0
    for item in script.CONTROLE:
        if item["rotulo"] not in ("bom", "ruim"):
            continue
        rotulados += 1
        passou = not codigos_do_dominio(script.normaliza_pontuacao(item["texto"]))
        if item["rotulo"] == "ruim" and passou:
            falsos_negativos.append(item["id"])
        if item["rotulo"] == "bom" and not passou:
            falsos_positivos.append(item["id"])

    with capsys.disabled():
        print(
            f"  controle rotulado pela fonte: {rotulados} enunciados · "
            f"falso positivo: {len(falsos_positivos)} · "
            f"falso negativo: {len(falsos_negativos)}"
        )
    assert rotulados == 6
    assert falsos_positivos == []
    assert falsos_negativos == []
