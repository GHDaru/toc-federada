"""P5 — observabilidade de nascença: um span por caso de uso, no esqueleto.

Este é o contrato que os outros construtores vão herdar. Se o span nascer depois, ele
nasce esquecido; a spec 011 (RNF-01) diz "sem traço, não está pronta" e o lugar de provar
isso é aqui, sem OpenTelemetry instalado no caminho do teste.
"""
from datetime import datetime, timezone
from uuid import uuid4

import pytest

from toc_api.aplicacao.casos_de_uso import CasoDeUso
from toc_api.aplicacao.projetos import (
    CriarProjeto,
    ExcluirProjeto,
    ListarProjetos,
    RestaurarProjeto,
)
from toc_api.dominio.erros import MutacaoRecusada, NaoEncontrado
from toc_api.dominio.identidade import DonoDoProjeto

from .fakes import RelogioFalso, RepositorioDeProjetosFalso, RastreadorFalso

HORIZONTE = DonoDoProjeto(inquilino_id="inq-horizonte", usuario_id="usr-facilitadora")
ALVORADA = DonoDoProjeto(inquilino_id="inq-alvorada", usuario_id="usr-consultor")
AGORA = datetime(2026, 9, 5, 12, 0, tzinfo=timezone.utc)


def montar():
    return RepositorioDeProjetosFalso(), RastreadorFalso(), RelogioFalso(AGORA)


def test_caso_de_uso_abre_exatamente_um_span_com_o_nome_declarado():
    repo, rastro, relogio = montar()
    caso = CriarProjeto(rastreador=rastro, repositorio=repo, relogio=relogio)

    caso.rodar(dono=HORIZONTE, nome="Instituição Horizonte — ARA da evasão")

    assert rastro.nomes == ["caso_de_uso.criar_projeto"]
    assert rastro.spans[0].encerrado is True
    assert rastro.spans[0].atributos["toc.resultado"] == "ok"
    assert rastro.spans[0].atributos["toc.inquilino_id"] == "inq-horizonte"


def test_span_registra_a_falha_e_reergue_a_excecao():
    """Recusa também é traço (brief §4: 'traço de toda ação, inclusive recusas')."""
    repo, rastro, relogio = montar()
    caso = ExcluirProjeto(rastreador=rastro, repositorio=repo, relogio=relogio)

    with pytest.raises(NaoEncontrado):
        caso.rodar(dono=HORIZONTE, projeto_id=uuid4())

    assert rastro.nomes == ["caso_de_uso.excluir_projeto"]
    assert rastro.spans[0].atributos["toc.resultado"] == "erro"
    assert rastro.spans[0].atributos["toc.erro"] == "NaoEncontrado"
    assert rastro.spans[0].encerrado is True


def test_todo_caso_de_uso_declara_nome_e_e_um_caso_de_uso():
    for classe in (CriarProjeto, ListarProjetos, ExcluirProjeto, RestaurarProjeto):
        assert issubclass(classe, CasoDeUso)
        assert isinstance(classe.nome, str) and classe.nome


def test_listar_nao_atravessa_a_fronteira_do_inquilino():
    """RNF-03: o teste que tenta ler através da fronteira."""
    repo, rastro, relogio = montar()
    criar = CriarProjeto(rastreador=rastro, repositorio=repo, relogio=relogio)
    criar.rodar(dono=HORIZONTE, nome="ARA da evasão")
    criar.rodar(dono=ALVORADA, nome="ARA do atraso de entrega")

    listar = ListarProjetos(rastreador=rastro, repositorio=repo)
    meus = listar.rodar(dono=HORIZONTE)

    assert [p.nome for p in meus] == ["ARA da evasão"]


def test_excluir_e_restaurar_pela_aplicacao():
    repo, rastro, relogio = montar()
    criado = CriarProjeto(rastreador=rastro, repositorio=repo, relogio=relogio).rodar(
        dono=HORIZONTE, nome="ARA da evasão"
    )

    ExcluirProjeto(rastreador=rastro, repositorio=repo, relogio=relogio).rodar(
        dono=HORIZONTE, projeto_id=criado.id
    )
    assert ListarProjetos(rastreador=rastro, repositorio=repo).rodar(dono=HORIZONTE) == []

    RestaurarProjeto(rastreador=rastro, repositorio=repo, relogio=relogio).rodar(
        dono=HORIZONTE, projeto_id=criado.id
    )
    voltou = ListarProjetos(rastreador=rastro, repositorio=repo).rodar(dono=HORIZONTE)
    assert [p.nome for p in voltou] == ["ARA da evasão"]


def test_excluir_projeto_de_outro_inquilino_e_nao_encontrado_nunca_proibido():
    """Não vazar existência: através da fronteira, o projeto simplesmente não existe."""
    repo, rastro, relogio = montar()
    alheio = CriarProjeto(rastreador=rastro, repositorio=repo, relogio=relogio).rodar(
        dono=ALVORADA, nome="ARA do atraso de entrega"
    )

    with pytest.raises(NaoEncontrado):
        ExcluirProjeto(rastreador=rastro, repositorio=repo, relogio=relogio).rodar(
            dono=HORIZONTE, projeto_id=alheio.id
        )


def test_restaurar_projeto_ativo_sobe_recusa_de_dominio():
    repo, rastro, relogio = montar()
    criado = CriarProjeto(rastreador=rastro, repositorio=repo, relogio=relogio).rodar(
        dono=HORIZONTE, nome="ARA da evasão"
    )
    with pytest.raises(MutacaoRecusada):
        RestaurarProjeto(rastreador=rastro, repositorio=repo, relogio=relogio).rodar(
            dono=HORIZONTE, projeto_id=criado.id
        )
