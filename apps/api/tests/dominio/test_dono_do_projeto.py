"""Objeto de valor DonoDoProjeto — a chave do isolamento (spec 004, RNF-03).

Por que estes testes existem antes do código (P4): o defeito D-02 da linhagem, citado na
`specs/003-esqueleto-federado/spec.md`, foi um `'user_placeholder_001'` — não havia usuário
real, logo não havia isolamento. Um objeto de valor que aceita vazio reproduz esse defeito
com outro nome; estes testes o proíbem por construção.
"""
import pytest

from toc_api.dominio.erros import DadoInvalido
from toc_api.dominio.identidade import DonoDoProjeto


def test_dono_e_igual_por_valor():
    a = DonoDoProjeto(inquilino_id="inq-horizonte", usuario_id="usr-facilitadora")
    b = DonoDoProjeto(inquilino_id="inq-horizonte", usuario_id="usr-facilitadora")
    assert a == b
    assert {a, b} == {a}


def test_dono_e_imutavel():
    dono = DonoDoProjeto(inquilino_id="inq-horizonte", usuario_id="usr-facilitadora")
    with pytest.raises(Exception):
        dono.inquilino_id = "inq-outro"  # type: ignore[misc]


@pytest.mark.parametrize(
    ("inquilino", "usuario"),
    [
        ("", "usr-facilitadora"),
        ("   ", "usr-facilitadora"),
        ("inq-horizonte", ""),
        ("inq-horizonte", "\t"),
    ],
)
def test_dono_recusa_identificador_vazio(inquilino, usuario):
    with pytest.raises(DadoInvalido):
        DonoDoProjeto(inquilino_id=inquilino, usuario_id=usuario)
