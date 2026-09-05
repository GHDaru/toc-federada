"""As portas são contrato: quem as implementa satisfaz a MESMA forma, fake ou adaptador.

Por que este teste existe: um duplo que diverge da porta faz a suíte de aplicação ficar
verde enquanto o adaptador real quebra em produção. Aqui os dois lados são medidos contra
a mesma `typing.Protocol`.
"""
from toc_api.dominio import portas
from toc_api.infra.observabilidade.otel import RastreadorNulo
from toc_api.infra.persistencia.memoria import RepositorioDeProjetosEmMemoria
from toc_api.infra.persistencia.repositorio_projetos import RepositorioDeProjetosSQL
from toc_api.infra.relogio import RelogioDoSistema

from tests.aplicacao.fakes import (
    RastreadorFalso,
    RelogioFalso,
    RepositorioDeARAFalso,
    RepositorioDeProjetosFalso,
)


def test_toda_porta_e_um_protocolo_verificavel_em_execucao():
    for porta in (
        portas.Relogio,
        portas.Rastreador,
        portas.RepositorioDeProjetos,
        portas.RepositorioDeARA,
    ):
        assert getattr(porta, "_is_runtime_protocol", False), (
            f"{porta.__name__} precisa de @runtime_checkable para o contrato ser medível"
        )


def test_os_duplos_dos_testes_satisfazem_as_portas():
    assert isinstance(RastreadorFalso(), portas.Rastreador)
    assert isinstance(RepositorioDeProjetosFalso(), portas.RepositorioDeProjetos)
    assert isinstance(RepositorioDeARAFalso(), portas.RepositorioDeARA)
    assert isinstance(RelogioFalso.__new__(RelogioFalso), portas.Relogio)


def test_os_adaptadores_de_infra_satisfazem_as_mesmas_portas():
    assert isinstance(RastreadorNulo(), portas.Rastreador)
    assert isinstance(RepositorioDeProjetosEmMemoria(), portas.RepositorioDeProjetos)
    assert isinstance(RelogioDoSistema(), portas.Relogio)
    # O adaptador SQL exige uma fábrica de sessão; a conformidade é medida na classe.
    assert isinstance(RepositorioDeProjetosEmMemoria(), portas.RepositorioDeARA)
    # O adaptador SQL exige uma fábrica de sessão; a conformidade é medida na classe.
    for porta in (portas.RepositorioDeProjetos, portas.RepositorioDeARA):
        assert isinstance(
            RepositorioDeProjetosSQL.__new__(RepositorioDeProjetosSQL), porta
        ), f"o adaptador SQL não satisfaz {porta.__name__}"
