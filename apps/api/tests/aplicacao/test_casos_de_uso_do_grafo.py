"""Casos de uso do grafo (M1) — sobre as PORTAS, com duplos. Sem banco, sem rede.

O que estes testes provam, além de "funciona":

- **P5 · traço de nascença**: todo caso de uso abre span, inclusive quando RECUSA. A
  recusa é a parte que costuma sumir do traço, e é a que interessa numa auditoria.
- **isolamento por inquilino**: através da fronteira a resposta é `NaoEncontrado`, nunca
  "proibido" — distinguir os dois vazaria a existência do projeto alheio (RNF-03).
- **nada de dado de pessoa no span**: o identificador de inquilino é opaco; título de nó
  e nome de projeto não entram em traço nem em log (ADR 0006).
"""
from datetime import datetime, timezone
from uuid import uuid4

import pytest

from toc_api.aplicacao.grafo import (
    AdicionarNo,
    EditarNo,
    ExcluirNo,
    LigarNos,
    MoverNo,
)
from toc_api.aplicacao.projetos import CriarProjeto
from toc_api.dominio.erros import ArestaInvalida, NaoEncontrado
from toc_api.dominio.identidade import DonoDoProjeto
from toc_api.dominio.valores import PosicaoNoCanvas

from .fakes import RastreadorFalso, RelogioFalso, RepositorioDeARAFalso

DONO = DonoDoProjeto(inquilino_id="inq-horizonte", usuario_id="usr-facilitadora")
INTRUSA = DonoDoProjeto(inquilino_id="inq-outra", usuario_id="usr-outra")
T0 = datetime(2026, 9, 5, 12, 0, tzinfo=timezone.utc)


@pytest.fixture()
def cenario():
    repositorio = RepositorioDeARAFalso()
    rastreador = RastreadorFalso()
    relogio = RelogioFalso(instante=T0)
    pecas = dict(rastreador=rastreador, repositorio=repositorio, relogio=relogio)
    projeto = CriarProjeto(**pecas).rodar(dono=DONO, nome="Horizonte — diagrama")
    return pecas, rastreador, projeto


def test_adicionar_no_persiste_pelo_repositorio_e_abre_span(cenario):
    pecas, rastreador, projeto = cenario
    no = AdicionarNo(**pecas).rodar(
        dono=DONO,
        projeto_id=projeto.id,
        titulo="Os formulários chegam incompletos.",
        posicao=PosicaoNoCanvas(10, 20),
    )
    guardado = pecas["repositorio"].obter(DONO.inquilino_id, projeto.id)
    assert [n.id for n in guardado.nos] == [no.id]
    assert "caso_de_uso.adicionar_no" in rastreador.nomes
    span = rastreador.spans[-1]
    assert span.atributos["toc.inquilino_id"] == "inq-horizonte"
    assert span.atributos["toc.resultado"] == "ok"


def test_nenhum_span_carrega_texto_do_usuario(cenario):
    """ADR 0006: enunciado de trabalho não entra em traço nem em log."""
    pecas, rastreador, projeto = cenario
    AdicionarNo(**pecas).rodar(
        dono=DONO, projeto_id=projeto.id, titulo="Os formulários chegam incompletos."
    )
    valores = [
        str(v) for span in rastreador.spans for v in span.atributos.values()
    ]
    assert not any("formulários" in v for v in valores)


def test_projeto_de_outro_inquilino_responde_nao_encontrado_e_o_span_marca_a_recusa(cenario):
    pecas, rastreador, projeto = cenario
    with pytest.raises(NaoEncontrado):
        AdicionarNo(**pecas).rodar(
            dono=INTRUSA, projeto_id=projeto.id, titulo="Nó da intrusa."
        )
    span = rastreador.spans[-1]
    assert span.atributos["toc.resultado"] == "erro"
    assert span.atributos["toc.erro"] == "NaoEncontrado"
    assert span.atributos["toc.inquilino_id"] == "inq-outra"


def test_ligar_nos_recusado_tambem_deixa_traco(cenario):
    """"Traço de toda ação, inclusive recusas" — brief §4, RF-26 da spec 004."""
    pecas, rastreador, projeto = cenario
    a = AdicionarNo(**pecas).rodar(dono=DONO, projeto_id=projeto.id, titulo="Nó A qualquer.")
    with pytest.raises(ArestaInvalida) as erro:
        LigarNos(**pecas).rodar(
            dono=DONO, projeto_id=projeto.id, origem_id=a.id, destino_id=a.id
        )
    assert erro.value.regra == "sem_auto_laco"
    assert rastreador.spans[-1].atributos["toc.erro"] == "ArestaInvalida"


def test_excluir_no_devolve_o_raio_e_persiste_a_cascata(cenario):
    pecas, rastreador, projeto = cenario
    adicionar, ligar = AdicionarNo(**pecas), LigarNos(**pecas)
    a = adicionar.rodar(dono=DONO, projeto_id=projeto.id, titulo="Nó A qualquer.")
    b = adicionar.rodar(dono=DONO, projeto_id=projeto.id, titulo="Nó B qualquer.")
    c = adicionar.rodar(dono=DONO, projeto_id=projeto.id, titulo="Nó C qualquer.")
    ligar.rodar(dono=DONO, projeto_id=projeto.id, origem_id=a.id, destino_id=b.id)
    ligar.rodar(dono=DONO, projeto_id=projeto.id, origem_id=b.id, destino_id=c.id)

    raio = ExcluirNo(**pecas).rodar(dono=DONO, projeto_id=projeto.id, no_id=b.id)

    assert len(raio) == 2
    guardado = pecas["repositorio"].obter(DONO.inquilino_id, projeto.id)
    assert {n.id for n in guardado.nos} == {a.id, c.id}
    assert guardado.arestas == ()
    assert rastreador.spans[-1].atributos["toc.arestas_removidas"] == 2


def test_editar_e_mover_no_persistem_o_estado_final(cenario):
    pecas, _, projeto = cenario
    no = AdicionarNo(**pecas).rodar(dono=DONO, projeto_id=projeto.id, titulo="Título antigo.")
    EditarNo(**pecas).rodar(
        dono=DONO, projeto_id=projeto.id, no_id=no.id, titulo="Título novo do nó."
    )
    MoverNo(**pecas).rodar(
        dono=DONO, projeto_id=projeto.id, no_id=no.id, posicao=PosicaoNoCanvas(7, 9)
    )
    guardado = pecas["repositorio"].obter(DONO.inquilino_id, projeto.id)
    assert guardado.no(no.id).titulo == "Título novo do nó."
    assert guardado.no(no.id).posicao == PosicaoNoCanvas(7, 9)


def test_no_de_projeto_inexistente_e_nao_encontrado(cenario):
    pecas, _, _ = cenario
    with pytest.raises(NaoEncontrado):
        AdicionarNo(**pecas).rodar(dono=DONO, projeto_id=uuid4(), titulo="Nó fantasma.")
