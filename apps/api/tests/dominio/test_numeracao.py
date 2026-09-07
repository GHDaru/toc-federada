"""A numeração hierárquica da árvore de Estratégia & Táticas (S&T) — função pura.

Siglas, uma vez neste arquivo: **S&T** — Estratégia & Táticas (*Strategy & Tactics*) ·
**M5** — o módulo da S&T · **RN/RF/RNF** — regra de negócio / requisito funcional /
requisito não funcional da spec 010.

**A regra que este arquivo existe para provar é a RN-01: numeração é derivada, nunca
dado.** O contraexemplo está medido na linhagem: `tocbuilderv3/types.ts:288` declara
`stepNumber: string; // e.g., "1", "1.1", "1.1.2"` — texto livre digitado à mão —, e
`tocbuilderv3/components/SnTStepEditorModal.tsx:56-57` o exige preenchido com o comentário
`// Optionally, add validation for stepNumber format or uniqueness` logo abaixo. Nenhuma
das dez funções de serviço da geração calculava, conferia ou renumerava coisa nenhuma
(F-08 da spec 010): a numeração era, integralmente, responsabilidade do usuário.

Aqui o número é **projeção da posição na árvore**, e há duas funções:

- `numeracao` — recalcula a árvore inteira. É a definição.
- `renumerar` — recalcula só a subárvore afetada por uma mutação. É a otimização que
  mantém o alvo de desempenho do mover (RNF-04) honesto em árvores grandes.

A propriedade que sustenta a segunda é o teste mais importante do arquivo: **renumerar
localmente e recalcular tudo devolvem o mesmo mapa** (RNF-05, decisão 6 do plano). Sem
ela, a otimização é uma segunda fonte de verdade — que é exatamente o defeito de que este
módulo nasceu para se livrar.
"""
from __future__ import annotations

import random
from uuid import UUID, uuid4

from toc_api.dominio.snt import numeracao, renumerar


def ids(quantos: int) -> list[UUID]:
    """Identificadores estáveis — o teste compara mapas, e ordem aleatória atrapalha."""
    return [UUID(int=i + 1) for i in range(quantos)]


# ---------------------------------------------------------------------------------------
# RN-01 · a forma da numeração: raízes 1..n, filhos X.1..X.m
# ---------------------------------------------------------------------------------------


def test_as_raizes_numeram_um_a_n_na_ordem_declarada() -> None:
    a, b, c = ids(3)
    numeros = numeracao({None: (a, b, c)})
    print(f"raízes={[numeros[x] for x in (a, b, c)]}")
    assert [numeros[a], numeros[b], numeros[c]] == ["1", "2", "3"]


def test_os_filhos_recebem_o_prefixo_do_pai_e_a_posicao_entre_irmaos() -> None:
    raiz, filho1, filho2, neto = ids(4)
    numeros = numeracao({None: (raiz,), raiz: (filho1, filho2), filho2: (neto,)})
    print(f"numeros={ {str(k)[-1]: v for k, v in numeros.items()} }")
    assert numeros[raiz] == "1"
    assert numeros[filho1] == "1.1"
    assert numeros[filho2] == "1.2"
    # O caso do comentário da linhagem — `1.1.2` — nasce da posição, não do teclado.
    assert numeros[neto] == "1.2.1"


def test_o_terceiro_filho_de_um_no_com_dois_nasce_como_x_ponto_3() -> None:
    """US-03: "Dado o passo 1.1 com dois filhos … Então ele nasce como 1.1.3"."""
    raiz, um_um, a, b, novo = ids(5)
    estrutura = {None: (raiz,), raiz: (um_um,), um_um: (a, b, novo)}
    numeros = numeracao(estrutura)
    print(f"numero do terceiro filho de {numeros[um_um]}: {numeros[novo]}")
    assert numeros[um_um] == "1.1"
    assert numeros[novo] == "1.1.3"


def test_a_numeracao_nao_tem_lacuna_mesmo_depois_de_remover_um_irmao_do_meio() -> None:
    raiz, a, b, c = ids(4)
    depois = numeracao({None: (raiz,), raiz: (a, c)})
    print(f"sobreviventes={[depois[x] for x in (a, c)]} (o do meio, {b}, saiu)")
    assert [depois[a], depois[c]] == ["1.1", "1.2"]
    assert b not in depois


def test_a_numeracao_e_deterministica_entre_duas_execucoes(capsys) -> None:
    """RNF-05: mesma estrutura → mesmos números, sempre."""
    raiz, a, b, neto = ids(4)
    estrutura = {None: (raiz,), raiz: (a, b), a: (neto,)}
    uma = numeracao(estrutura)
    outra = numeracao(estrutura)
    print(f"execuções comparadas: 2 · passos numerados: {len(uma)}")
    assert uma == outra


def test_arvore_vazia_numera_vazio() -> None:
    assert numeracao({}) == {}
    assert numeracao({None: ()}) == {}


def test_multiplas_raizes_sao_permitidas_e_numeram_em_sequencia() -> None:
    """L-05: planos reais começam por listas de frentes — permitir custa menos que negar."""
    a, b, filho = ids(3)
    numeros = numeracao({None: (a, b), b: (filho,)})
    print(f"raízes numeradas: {numeros[a]} e {numeros[b]}; filho: {numeros[filho]}")
    assert (numeros[a], numeros[b], numeros[filho]) == ("1", "2", "2.1")


# ---------------------------------------------------------------------------------------
# RF-07 · renumeração LOCAL — e a propriedade que a torna confiável (RNF-05)
# ---------------------------------------------------------------------------------------


def test_renumerar_so_toca_a_subarvore_do_pai_afetado() -> None:
    raiz_a, raiz_b, filho_a, filho_b = ids(4)
    estrutura = {None: (raiz_a, raiz_b), raiz_a: (filho_a,), raiz_b: (filho_b,)}
    antes = numeracao(estrutura)

    novo = uuid4()
    estrutura_depois = {**estrutura, raiz_a: (novo, filho_a)}
    depois = renumerar(antes, estrutura_depois, pais_afetados={raiz_a})

    print(f"filho de A: {antes[filho_a]} → {depois[filho_a]}; filho de B intacto: {depois[raiz_b]}")
    assert depois[novo] == "1.1"
    assert depois[filho_a] == "1.2"
    # O outro ramo não foi recalculado e continua com o mesmo número — é o ponto da
    # renumeração local (decisão 6 do plano do ciclo 010).
    assert depois[raiz_b] == antes[raiz_b] == "2"
    assert depois[filho_b] == antes[filho_b] == "2.1"


def test_renumerar_do_topo_equivale_a_recalcular_a_arvore_inteira() -> None:
    """A propriedade: local == total. Sem ela, a otimização vira segunda verdade."""
    raiz, a, b, neto = ids(4)
    estrutura = {None: (raiz,), raiz: (a, b), b: (neto,)}
    total = numeracao(estrutura)
    local = renumerar({}, estrutura, pais_afetados={None})
    print(f"passos comparados: {len(total)}")
    assert local == total


def test_propriedade_local_igual_total_sobre_arvores_geradas(capsys) -> None:
    """RNF-05 em forma de propriedade: 200 árvores aleatórias, mutação e comparação.

    Semente fixa — uma propriedade que muda de corpus a cada execução não é reprodutível,
    e um vermelho que ninguém consegue repetir não é evidência.
    """
    sorteio = random.Random(20260906)
    arvores = 0
    passos_examinados = 0
    for _ in range(200):
        nos = [UUID(int=i + 1) for i in range(sorteio.randint(1, 18))]
        estrutura: dict[UUID | None, tuple[UUID, ...]] = {None: ()}
        for no in nos:
            candidatos: list[UUID | None] = [None] + [
                x for x in nos[: nos.index(no)]
            ]
            pai = sorteio.choice(candidatos)
            estrutura[pai] = estrutura.get(pai, ()) + (no,)
        antes = numeracao(estrutura)

        # A mutação: move o último nó para outro pai válido (não descendente dele).
        alvo = nos[-1]
        pai_antigo = next(p for p, fs in estrutura.items() if alvo in fs)
        possiveis = [p for p in list(estrutura) if p != alvo and p != pai_antigo]
        novo_pai = sorteio.choice(possiveis) if possiveis else None
        mutada = {
            p: tuple(x for x in fs if x != alvo) for p, fs in estrutura.items()
        }
        mutada[novo_pai] = mutada.get(novo_pai, ()) + (alvo,)

        local = renumerar(antes, mutada, pais_afetados={pai_antigo, novo_pai})
        total = numeracao(mutada)
        assert local == total, f"divergiu movendo {alvo} de {pai_antigo} para {novo_pai}"
        arvores += 1
        passos_examinados += len(total)

    with capsys.disabled():
        print(
            f"\n  propriedade local==total: {arvores} árvores geradas, "
            f"{passos_examinados} passos numerados, 0 divergências"
        )
