"""O pacote de suficiência causal — extraído do M2, reusado pelo M4 (spec 008, RF-03).

Siglas, uma vez neste arquivo: **M2** — Árvore da Realidade Atual (ARA) · **M4** —
Árvores de Futuro e Implementação · **ARF** — Árvore da Realidade Futura · **TOC** —
Teoria das Restrições · **RF** — requisito funcional.

A spec 008 (RF-03) exige que a ARF ofereça "o exame de elo e o conector E do pacote de
suficiência causal compartilhado com a ARA, **sem duplicação de regra**", e a decisão 1 do
`plan.md` do ciclo é explícita: "pacote extraído, nunca copiado".

O que "sem duplicação" quer dizer aqui é verificável, e é o que estes testes fixam: as
duas ferramentas usam **o mesmo objeto** — a mesma classe de estado, o mesmo erro, a
mesma função que recusa exame sem reserva e a mesma que forma a conjunção. Um teste que
só comparasse comportamento passaria sobre duas cópias que ainda não divergiram; comparar
identidade (`is`) passa somente enquanto houver **uma** implementação.
"""
from __future__ import annotations

from uuid import UUID, uuid4

import pytest

from toc_api.dominio import ara as m2
from toc_api.dominio import suficiencia as compartilhado
from toc_api.dominio.erros import MutacaoRecusada
from toc_api.dominio.grafo import ArestaCausal

DESTINO = UUID("aaaaaaaa-0000-4000-8000-000000000001")
OUTRO_DESTINO = UUID("aaaaaaaa-0000-4000-8000-000000000002")


def _aresta(destino: UUID) -> ArestaCausal:
    return ArestaCausal(id=uuid4(), origem_id=uuid4(), destino_id=destino)


# --------------------------------------------------------------------------------------
# Uma implementação, não duas: identidade, e não semelhança
# --------------------------------------------------------------------------------------


@pytest.mark.parametrize(
    "nome", ["EstadoDoExame", "Exame", "ConectorE", "ConectorInvalido", "EXIGEM_RESERVA"]
)
def test_a_ara_expoe_exatamente_o_objeto_do_pacote_compartilhado(nome: str) -> None:
    do_m2 = getattr(m2, nome)
    do_pacote = getattr(compartilhado, nome)
    print(f"{nome}: ara → {do_m2!r} · suficiencia → {do_pacote!r}")
    assert do_m2 is do_pacote


# --------------------------------------------------------------------------------------
# A regra do exame mora no pacote — e recusa antes de qualquer agregado existir
# --------------------------------------------------------------------------------------


@pytest.mark.parametrize(
    "estado",
    [compartilhado.EstadoDoExame.INSUFICIENTE, compartilhado.EstadoDoExame.COM_RESERVA],
)
def test_exame_sem_reserva_e_recusado_pela_funcao_pura(estado) -> None:
    with pytest.raises(MutacaoRecusada) as erro:
        compartilhado.exame_de(estado, reserva="   ")
    print(f"{estado.value} sem reserva → {erro.value}")
    assert "reserva" in str(erro.value)


def test_exame_suficiente_dispensa_reserva_e_normaliza_o_texto() -> None:
    exame = compartilhado.exame_de(
        compartilhado.EstadoDoExame.COM_RESERVA, reserva="  falta a condição de volume  "
    )
    assert exame.reserva == "falta a condição de volume"
    assert compartilhado.exame_de(compartilhado.EstadoDoExame.SUFICIENTE).reserva == ""


# --------------------------------------------------------------------------------------
# O conector E: as três regras nomeadas, em função pura sobre um dicionário
# --------------------------------------------------------------------------------------


def test_conjuncao_com_uma_aresta_so_nao_e_conjuncao() -> None:
    uma = _aresta(DESTINO)
    with pytest.raises(compartilhado.ConectorInvalido) as erro:
        compartilhado.formar_conector({}, (uma.id,), aresta_de={uma.id: uma}.__getitem__)
    assert erro.value.regra == "minimo_duas_arestas"


def test_conjuncao_exige_destino_unico() -> None:
    uma, outra = _aresta(DESTINO), _aresta(OUTRO_DESTINO)
    mapa = {uma.id: uma, outra.id: outra}
    with pytest.raises(compartilhado.ConectorInvalido) as erro:
        compartilhado.formar_conector({}, (uma.id, outra.id), aresta_de=mapa.__getitem__)
    assert erro.value.regra == "destino_unico"


def test_aresta_pertence_a_no_maximo_um_conector() -> None:
    uma, outra, terceira = _aresta(DESTINO), _aresta(DESTINO), _aresta(DESTINO)
    mapa = {a.id: a for a in (uma, outra, terceira)}
    conectores: dict[UUID, compartilhado.ConectorE] = {}
    primeiro = compartilhado.formar_conector(
        conectores, (uma.id, outra.id), aresta_de=mapa.__getitem__
    )
    conectores[primeiro.id] = primeiro

    with pytest.raises(compartilhado.ConectorInvalido) as erro:
        compartilhado.formar_conector(
            conectores, (uma.id, terceira.id), aresta_de=mapa.__getitem__
        )
    assert erro.value.regra == "aresta_ja_conectada"


def test_aresta_que_some_leva_junto_a_citacao_e_dissolve_conector_de_duas() -> None:
    """RN-11: nunca deixa referência órfã — a regra que o M4 herda inteira."""
    uma, outra, terceira = _aresta(DESTINO), _aresta(DESTINO), _aresta(DESTINO)
    mapa = {a.id: a for a in (uma, outra, terceira)}
    conectores: dict[UUID, compartilhado.ConectorE] = {}
    de_tres = compartilhado.formar_conector(
        conectores, (uma.id, outra.id, terceira.id), aresta_de=mapa.__getitem__
    )
    conectores[de_tres.id] = de_tres

    compartilhado.soltar_das_conjuncoes(conectores, terceira.id)
    assert conectores[de_tres.id].arestas == (uma.id, outra.id)

    compartilhado.soltar_das_conjuncoes(conectores, outra.id)
    print(f"conectores após dissolver: {conectores}")
    assert conectores == {}


# --------------------------------------------------------------------------------------
# As leituras: montadas dos textos ATUAIS, nunca de cópia congelada
# --------------------------------------------------------------------------------------


def test_a_leitura_de_suficiencia_e_a_mesma_frase_das_duas_ferramentas() -> None:
    assert (
        compartilhado.leitura_de_suficiencia("a matrícula demora", "a família desiste")
        == "Se a matrícula demora, então a família desiste"
    )
    assert (
        compartilhado.leitura_de_conjuncao(
            ("há verba", "há equipe"), "a frente entrega no trimestre"
        )
        == "Se há verba e há equipe, então a frente entrega no trimestre"
    )
