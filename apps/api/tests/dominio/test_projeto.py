"""Agregado Projeto — esqueleto do M1 (spec 004, `data-model.md`).

Cobre as invariantes que este lote precisa provar: exclusão reversível de verdade
(invariante 4 e 5 do `data-model.md`) e relógio-porta (o domínio nunca chama
`datetime.now()`; o instante entra como argumento).
"""
from datetime import datetime, timezone
from uuid import uuid4

import pytest

from toc_api.dominio.erros import DadoInvalido, MutacaoRecusada
from toc_api.dominio.identidade import DonoDoProjeto
from toc_api.dominio.projeto import EstadoDoProjeto, Projeto

DONO = DonoDoProjeto(inquilino_id="inq-horizonte", usuario_id="usr-facilitadora")
T0 = datetime(2026, 9, 5, 12, 0, tzinfo=timezone.utc)
T1 = datetime(2026, 9, 5, 13, 0, tzinfo=timezone.utc)
T2 = datetime(2026, 9, 5, 14, 0, tzinfo=timezone.utc)


def novo_projeto(**kw) -> Projeto:
    base = dict(
        id=uuid4(),
        dono=DONO,
        nome="Instituição Horizonte — ARA da evasão",
        ferramenta="generico",
        criado_em=T0,
        alterado_em=T0,
    )
    base.update(kw)
    return Projeto(**base)  # type: ignore[arg-type]


def test_projeto_nasce_ativo():
    p = novo_projeto()
    assert p.estado is EstadoDoProjeto.ATIVO
    assert p.excluido_em is None
    assert p.versao == 1


def test_projeto_recusa_nome_vazio():
    with pytest.raises(DadoInvalido):
        novo_projeto(nome="   ")


def test_projeto_recusa_nome_acima_de_200():
    with pytest.raises(DadoInvalido):
        novo_projeto(nome="a" * 201)


def test_exclusao_e_reversivel_e_preserva_o_conteudo():
    """Invariante 5: restaurar devolve o conteúdo idêntico ao momento da exclusão."""
    p = novo_projeto()
    p.renomear("Instituição Horizonte — ARA revisada", em=T1)
    antes = p.nome

    p.excluir(em=T2)
    assert p.estado is EstadoDoProjeto.EXCLUIDO
    assert p.excluido_em == T2

    p.restaurar(em=T2)
    assert p.estado is EstadoDoProjeto.ATIVO
    assert p.excluido_em is None
    assert p.nome == antes


def test_projeto_excluido_recusa_mutacao_que_nao_seja_restauracao():
    """Invariante 4 do `data-model.md`."""
    p = novo_projeto()
    p.excluir(em=T1)
    with pytest.raises(MutacaoRecusada):
        p.renomear("outro nome", em=T2)


def test_excluir_duas_vezes_e_recusado():
    p = novo_projeto()
    p.excluir(em=T1)
    with pytest.raises(MutacaoRecusada):
        p.excluir(em=T2)


def test_restaurar_projeto_ativo_e_recusado():
    p = novo_projeto()
    with pytest.raises(MutacaoRecusada):
        p.restaurar(em=T1)


def test_toda_mutacao_avanca_a_versao_e_o_instante():
    """Bloqueio otimista (Clarify 2 da spec 004): a versão é do agregado, não do banco."""
    p = novo_projeto()
    assert (p.versao, p.alterado_em) == (1, T0)
    p.renomear("outro nome", em=T1)
    assert (p.versao, p.alterado_em) == (2, T1)
    p.excluir(em=T2)
    assert (p.versao, p.alterado_em) == (3, T2)


def test_dominio_nao_le_o_relogio_do_sistema():
    """O instante entra como argumento — chamar o relógio no domínio é proibido.

    A checagem é por árvore sintática, não por `in` sobre o texto: a primeira versão
    procurava a cadeia `datetime.now(` no fonte e reprovou a **docstring** que explica a
    regra. Um portão que reprova a explicação da regra ensina a apagar a explicação. Aqui
    o que é medido é o que importa — uma CHAMADA de `now`/`utcnow`/`today` —, e um
    `datetime.now()` de verdade continua reprovando.
    """
    import ast
    import pathlib

    import toc_api.dominio as pacote

    proibidas = {"now", "utcnow", "today", "time", "monotonic"}
    ofensores = []
    for arquivo in pathlib.Path(pacote.__file__).parent.glob("*.py"):
        for no in ast.walk(ast.parse(arquivo.read_text(encoding="utf-8"))):
            if not isinstance(no, ast.Call):
                continue
            alvo = no.func
            nome = alvo.attr if isinstance(alvo, ast.Attribute) else getattr(alvo, "id", "")
            if nome in proibidas:
                ofensores.append(f"{arquivo.name}:{no.lineno} {nome}()")

    assert ofensores == [], f"o domínio leu o relógio: {ofensores}"
