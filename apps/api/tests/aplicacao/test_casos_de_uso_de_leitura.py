"""Os três casos de uso de LEITURA que a superfície HTTP precisa — e por que existem.

Antes deste arquivo, a camada de aplicação sabia criar, mutar e excluir, mas **abrir** um
projeto não era um caso de uso: o único caminho de leitura era o `_carregar` privado de
`_ComRepositorio`. Uma rota `GET` teria de falar com o repositório direto, e aí a leitura
passaria por fora do único ponto onde a capacidade é verificada — que é exatamente o
buraco que o §B.7.2 do Anexo B do Padrão APH (Aplicação ↔ Harness) descreve. Ler também é
operação governada: exige `toc:read`, e por isso precisa de caso de uso.

- `AbrirProjeto` — RF-03 da spec 004: metadados, nós e arestas num carregamento só.
- `ListarLixeira` — RF-07 da spec 004: só os excluídos, com a data de exclusão.
- `AbrirProjetoARA` — a leitura equivalente do M2 (ficha, status, parecer, exame,
  conector), pela porta separada `RepositorioDeARA`.

Sem banco e sem rede: duplos das portas (brief §0.2).
"""
from datetime import datetime, timezone
from uuid import uuid4

import pytest

from toc_api.aplicacao.ara import (
    AbrirProjetoARA,
    AdicionarEfeito,
    CriarProjetoARA,
    MarcarUde,
)
from toc_api.aplicacao.grafo import AdicionarNo, LigarNos
from toc_api.aplicacao.projetos import (
    AbrirProjeto,
    CriarProjeto,
    ExcluirProjeto,
    ListarLixeira,
)
from toc_api.dominio.erros import NaoEncontrado
from toc_api.dominio.identidade import DonoDoProjeto

from .fakes import RastreadorFalso, RelogioFalso, RepositorioDeARAFalso

DONA = DonoDoProjeto(inquilino_id="inq-horizonte", usuario_id="usr-facilitadora")
INTRUSA = DonoDoProjeto(inquilino_id="inq-outra", usuario_id="usr-outra")
T0 = datetime(2026, 9, 5, 12, 0, tzinfo=timezone.utc)


@pytest.fixture()
def pecas():
    return dict(
        rastreador=RastreadorFalso(),
        repositorio=RepositorioDeARAFalso(),
        relogio=RelogioFalso(instante=T0),
    )


def test_abrir_projeto_devolve_metadados_nos_e_arestas_num_carregamento_so(pecas):
    """Projeto GENÉRICO: aqui o `Projeto` é a própria raiz, e a porta do M1 é a certa."""
    projeto = CriarProjeto(**pecas).rodar(dono=DONA, nome="Horizonte — diagrama")
    a = AdicionarNo(**pecas).rodar(
        dono=DONA, projeto_id=projeto.id, titulo="Os formulários chegam incompletos."
    )
    b = AdicionarNo(**pecas).rodar(
        dono=DONA, projeto_id=projeto.id, titulo="O retrabalho consome a equipe."
    )
    LigarNos(**pecas).rodar(
        dono=DONA, projeto_id=projeto.id, origem_id=a.id, destino_id=b.id
    )

    aberto = AbrirProjeto(**pecas).rodar(dono=DONA, projeto_id=projeto.id)

    assert aberto.id == projeto.id
    assert {n.id for n in aberto.nos} == {a.id, b.id}
    assert [(e.origem_id, e.destino_id) for e in aberto.arestas] == [(a.id, b.id)]


def test_abrir_projeto_de_outro_inquilino_e_nao_encontrado_nunca_proibido(pecas):
    projeto = CriarProjeto(**pecas).rodar(dono=DONA, nome="Horizonte — diagrama")
    with pytest.raises(NaoEncontrado):
        AbrirProjeto(**pecas).rodar(dono=INTRUSA, projeto_id=projeto.id)


def test_abrir_projeto_inexistente_e_nao_encontrado(pecas):
    with pytest.raises(NaoEncontrado):
        AbrirProjeto(**pecas).rodar(dono=DONA, projeto_id=uuid4())


def test_abrir_projeto_abre_span_de_leitura(pecas):
    projeto = CriarProjeto(**pecas).rodar(dono=DONA, nome="Horizonte — diagrama")
    AbrirProjeto(**pecas).rodar(dono=DONA, projeto_id=projeto.id)
    assert "caso_de_uso.abrir_projeto" in pecas["rastreador"].nomes


def test_listar_lixeira_traz_so_os_excluidos(pecas):
    vivo = CriarProjeto(**pecas).rodar(dono=DONA, nome="Continua em uso")
    morto = CriarProjeto(**pecas).rodar(dono=DONA, nome="Foi para a lixeira")
    ExcluirProjeto(**pecas).rodar(dono=DONA, projeto_id=morto.id)

    lixeira = ListarLixeira(**pecas).rodar(dono=DONA)

    assert [p.id for p in lixeira] == [morto.id]
    assert lixeira[0].excluido_em == T0
    assert vivo.id not in {p.id for p in lixeira}


def test_listar_lixeira_de_outro_inquilino_nao_atravessa(pecas):
    morto = CriarProjeto(**pecas).rodar(dono=DONA, nome="Foi para a lixeira")
    ExcluirProjeto(**pecas).rodar(dono=DONA, projeto_id=morto.id)
    assert ListarLixeira(**pecas).rodar(dono=INTRUSA) == []


def test_abrir_projeto_ara_devolve_a_semantica_do_m2_junto(pecas):
    projeto = CriarProjetoARA(**pecas).rodar(dono=DONA, nome="Horizonte — ARA")
    no = AdicionarEfeito(**pecas).rodar(
        dono=DONA, projeto_id=projeto.id, titulo="A taxa de erros no processo X é de 15%."
    )
    MarcarUde(**pecas).rodar(dono=DONA, projeto_id=projeto.id, no_id=no.id)

    ara = AbrirProjetoARA(**pecas).rodar(dono=DONA, projeto_id=projeto.id)

    assert ara.projeto.id == projeto.id
    assert ara.udes == frozenset({no.id})
    assert ara.validacao(no.id).aprovado_nos_decidiveis is True


def test_abrir_projeto_ara_de_outro_inquilino_e_nao_encontrado(pecas):
    projeto = CriarProjetoARA(**pecas).rodar(dono=DONA, nome="Horizonte — ARA")
    with pytest.raises(NaoEncontrado):
        AbrirProjetoARA(**pecas).rodar(dono=INTRUSA, projeto_id=projeto.id)


def test_abrir_nao_grava_nada_leitura_nao_muta(pecas):
    """Ler não incrementa versão nem emite evento — se emitisse, abrir escreveria história."""
    projeto = CriarProjeto(**pecas).rodar(dono=DONA, nome="Horizonte — diagrama")
    versao_antes = projeto.versao
    projeto.drenar_eventos()

    aberto = AbrirProjeto(**pecas).rodar(dono=DONA, projeto_id=projeto.id)

    assert aberto.versao == versao_antes
    assert aberto.eventos == ()
