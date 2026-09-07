"""A ordem em que a importação grava os agregados — defeito achado por teste ponta a ponta.

Siglas, uma vez neste arquivo: **ARA** — Árvore da Realidade Atual · **NC** — Nuvem de
Conflito · **ARF** — Árvore da Realidade Futura · **APR** — Árvore de Pré-Requisitos ·
**AT** — Árvore de Transição · **JSON** — *JavaScript Object Notation* · **RF** —
requisito funcional.

## O defeito, e como ele apareceu

A ida e volta do arquivo consolidado era exercitada sobre uma cadeia de DUAS ferramentas
(`apps/api/tests/integracao/test_portabilidade_no_postgres.py`, que promove e para na Nuvem). Com
cinco, a importação quebrava no PostgreSQL, e a saída colada era:

```
psycopg.errors.ForeignKeyViolation: insert or update on table "nc_injecao" violates
foreign key constraint "fk_nc_injecao_semeadura_projeto_id_projeto"
DETAIL:  Key (semeadura_projeto_id)=(995a47d7-…) is not present in table "projeto".
```

**Causa raiz**: a Nuvem guarda, em cada injeção escolhida, o projeto que ela semeou
(`ReferenciaDeSemeadura.projeto_destino_id`), e essa coluna tem chave estrangeira para
`projeto`. A importação gravava os agregados na ordem do arquivo — que é a ordem da cadeia,
`ara → nc → arf → …` —, então a Nuvem chegava ao banco apontando para uma Árvore da
Realidade Futura que ainda não existia. Nenhum teste pegava porque nenhum exercitava uma
cadeia longa o bastante para ter semeadura, e o duplo em memória não tem chave estrangeira
para violar.

Este arquivo testa a função pura da ordenação; o teste que reproduz o defeito de verdade,
contra o banco, é
`apps/api/tests/integracao/test_cadeia_completa_no_postgres.py::test_exportar_a_cadeia_inteira_e_reimporta_la_reproduz_as_cinco_ferramentas`.
"""
from __future__ import annotations

from uuid import uuid4

from toc_api.aplicacao.portabilidade import ordem_de_gravacao


class _ProjetoFalso:
    def __init__(self, id, ferramenta: str) -> None:
        self.id = id
        self.ferramenta = ferramenta


class _AgregadoFalso:
    """Um agregado qualquer: só o `projeto` importa para a ordenação."""

    def __init__(self, id, ferramenta: str) -> None:
        self.projeto = _ProjetoFalso(id, ferramenta)


class _NuvemFalsa(_AgregadoFalso):
    """A Nuvem é a única que aponta OUTRO projeto por chave estrangeira: a semeadura."""

    def __init__(self, id, destinos) -> None:
        super().__init__(id, "nc")
        # `NuvemDeConflito.semeaduras` é um MÉTODO no domínio, não uma propriedade — e o
        # duplo o imita exatamente por isso: um duplo que expusesse atributo faria a
        # ordenação passar aqui e falhar contra o agregado de verdade.
        refs = tuple(
            type("Ref", (), {"projeto_destino_id": d, "injecao_id": uuid4()})()
            for d in destinos
        )
        self.semeaduras = lambda: refs


def test_a_arf_semeada_e_gravada_antes_da_nuvem_que_a_aponta():
    """O defeito, na função pura: quem é apontado entra primeiro."""
    ara, nc, arf, apr, at = (uuid4() for _ in range(5))
    entrada = [
        _AgregadoFalso(ara, "ara"),
        _NuvemFalsa(nc, [arf]),
        _AgregadoFalso(arf, "arf"),
        _AgregadoFalso(apr, "apr"),
        _AgregadoFalso(at, "at"),
    ]

    ordenados = [a.projeto.id for a in ordem_de_gravacao(entrada)]

    print(f"\nordem de entrada : {[a.projeto.ferramenta for a in entrada]}")
    print(f"ordem de gravação: {[ordenados.index(i) for i in (ara, nc, arf, apr, at)]}")
    assert ordenados.index(arf) < ordenados.index(nc), (
        "a Nuvem foi gravada antes da Árvore da Realidade Futura que ela aponta — "
        "é exatamente a violação de chave estrangeira do PostgreSQL"
    )
    assert sorted(ordenados, key=str) == sorted([ara, nc, arf, apr, at], key=str), (
        "a ordenação perdeu ou duplicou agregado"
    )


def test_sem_semeadura_a_ordem_do_arquivo_e_preservada():
    """Estabilidade: onde não há restrição, nada se mexe.

    Reordenar por gosto tornaria o relato da importação (a lista `projetos_criados`)
    imprevisível de uma versão para a outra, e o cliente lê essa lista.
    """
    ids = [uuid4() for _ in range(4)]
    entrada = [_AgregadoFalso(i, f) for i, f in zip(ids, ("ara", "nc", "apr", "at"))]

    assert [a.projeto.id for a in ordem_de_gravacao(entrada)] == ids


def test_uma_nuvem_que_aponta_projeto_fora_do_arquivo_nao_derruba_a_ordenacao():
    """Exportação parcial: a semeadura pode apontar para fora do que veio no arquivo.

    O caso existe de verdade — o arquivo é da cadeia alcançável, e a coluna é anulável com
    `ON DELETE SET NULL`. A ordenação ignora o que não está aqui, em vez de estourar.
    """
    ara, nc, fora = uuid4(), uuid4(), uuid4()
    entrada = [_AgregadoFalso(ara, "ara"), _NuvemFalsa(nc, [fora, None])]

    assert [a.projeto.id for a in ordem_de_gravacao(entrada)] == [ara, nc]


def test_um_ciclo_entre_agregados_nao_trava_a_importacao():
    """Dado torto não pode virar laço infinito: a ordenação degrada para a ordem do arquivo.

    Uma leitura que trava é pior do que uma leitura que mostra o laço — a mesma regra que
    `dominio/referencia.travessia` já aplica à vista da cadeia.
    """
    a, b = uuid4(), uuid4()
    entrada = [_NuvemFalsa(a, [b]), _NuvemFalsa(b, [a])]

    ordenados = [x.projeto.id for x in ordem_de_gravacao(entrada)]

    print(f"\nciclo a↔b resolvido como: {[str(i)[:8] for i in ordenados]}")
    assert sorted(ordenados, key=str) == sorted([a, b], key=str)
