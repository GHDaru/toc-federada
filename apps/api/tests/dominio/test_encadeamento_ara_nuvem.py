"""O encadeamento M2 → M3: a nuvem derivada de um Efeito Indesejável da ARA.

Siglas, uma vez: **ARA** — Árvore da Realidade Atual · **UDE** — Efeito Indesejável ·
**NC** — Nuvem de Conflito · **TOC** — Teoria das Restrições · **ARF** — Árvore da
Realidade Futura.

**Esta é a costura que nenhuma geração da linhagem fez.** Na 4ª geração
(`/home/user/tocbuilderv3`) a Árvore da Realidade Atual e a Nuvem de Conflito eram dois
bancos simulados sem uma referência entre si — `projects` e `conflictCloudProjects`, em
`services/mockApiService.ts:10-14` —, e não havia caminho de dado do efeito indesejável
para o dilema por trás dele. Aqui a ligação é **tipada** (`ReferenciaDeOrigem`): quem veio
de onde é dado do agregado, não convenção de nome nem texto colado.

O que os testes fixam: a derivação exige UDEs de verdade, atravessa o inquilino nenhuma
vez, não muta a ARA de origem, e deixa nos dois lados a evidência de que a nuvem nasceu
dali.
"""
from __future__ import annotations

from uuid import UUID, uuid4

import pytest

from toc_api.dominio.ara import (
    FERRAMENTA_ARA,
    OrigemDoParecer,
    ParecerDeJulgamento,
    ProjetoARA,
    StatusDeValidacao,
    novo_projeto_ara,
)
from toc_api.dominio.erros import MutacaoRecusada, NaoEncontrado
from toc_api.dominio.nuvem import (
    FERRAMENTA_NC,
    ChaveDaAresta,
    DerivacaoInvalida,
    PapelDaEntidade,
    ReferenciaDeOrigem,
    derivar_nuvem_de_udes,
)

from .nuvem_sintetica import AGORA, DONO, ID_DA_NUVEM, OUTRO_DONO, UDES_SINTETICOS

ID_DA_ARA = UUID("55555555-5555-4555-8555-555555555551")


def ara_com_udes(dono=DONO) -> tuple[ProjetoARA, list[UUID]]:
    ara = novo_projeto_ara(
        id=ID_DA_ARA, dono=dono, nome="Realidade atual da Instituição Horizonte", em=AGORA
    )
    ids: list[UUID] = []
    for enunciado in UDES_SINTETICOS:
        no = ara.adicionar_efeito(titulo=enunciado, em=AGORA)
        ara.marcar_ude(no.id, em=AGORA)
        ids.append(no.id)
    ara.drenar_eventos()
    return ara, ids


# --------------------------------------------------------------------------------------
# O caminho feliz: o efeito indesejável vira o ponto de partida do conflito
# --------------------------------------------------------------------------------------


def test_a_nuvem_derivada_nasce_completa_e_com_referencia_tipada_de_origem() -> None:
    ara, udes = ara_com_udes()

    nuvem = derivar_nuvem_de_udes(
        ara, no_ids=tuple(udes), id=ID_DA_NUVEM, nome="Dilema da expansão", em=AGORA
    )

    print(
        f"origem: {type(nuvem.origem).__name__}(ferramenta={nuvem.origem.ferramenta!r}, "
        f"projeto={nuvem.origem.projeto_id}, nos={len(nuvem.origem.nos)})"
    )
    assert isinstance(nuvem.origem, ReferenciaDeOrigem)
    assert nuvem.origem.ferramenta == FERRAMENTA_ARA
    assert nuvem.origem.projeto_id == ara.projeto.id
    assert nuvem.origem.nos == tuple(udes)
    assert nuvem.projeto.ferramenta == FERRAMENTA_NC
    assert (len(nuvem.entidades), len(nuvem.arestas)) == (5, 7)


def test_a_nuvem_derivada_carrega_o_enunciado_do_efeito_como_ponto_de_partida() -> None:
    ara, udes = ara_com_udes()

    nuvem = derivar_nuvem_de_udes(
        ara, no_ids=tuple(udes), id=ID_DA_NUVEM, nome="Dilema da expansão", em=AGORA
    )

    print(f"descrição do problema derivada: {nuvem.projeto.descricao_do_problema!r}")
    for enunciado in UDES_SINTETICOS:
        assert enunciado in nuvem.projeto.descricao_do_problema
    # E as entidades continuam com texto de exemplo: derivar dá o PONTO DE PARTIDA, não
    # inventa o conflito — quem escreve A, B, C, D e D′ é o grupo (ou a geração assistida,
    # por proposta aceita).
    assert nuvem.texto(PapelDaEntidade.A) != UDES_SINTETICOS[0]


def test_a_derivacao_emite_evento_com_a_origem_e_nao_muta_a_ara() -> None:
    ara, udes = ara_com_udes()

    nuvem = derivar_nuvem_de_udes(
        ara, no_ids=tuple(udes), id=ID_DA_NUVEM, nome="Dilema da expansão", em=AGORA
    )

    tipos = [type(e).__name__ for e in nuvem.eventos]
    print(f"eventos da nuvem derivada: {tipos}; eventos da ARA: {len(ara.eventos)}")
    assert "NuvemDerivadaDeUde" in tipos
    derivada = [e for e in nuvem.eventos if type(e).__name__ == "NuvemDerivadaDeUde"][0]
    assert derivada.origem_projeto_id == ara.projeto.id
    assert derivada.udes == tuple(udes)
    # A ARA é LIDA, nunca escrita: derivar não é mutação do M2.
    assert ara.eventos == ()


def test_a_leitura_da_origem_diz_de_onde_a_nuvem_veio() -> None:
    """INT-05: este ciclo entrega o campo e a leitura ('origem: UDEs …' quando houver)."""
    ara, udes = ara_com_udes()
    nuvem = derivar_nuvem_de_udes(
        ara, no_ids=tuple(udes), id=ID_DA_NUVEM, nome="Dilema da expansão", em=AGORA
    )

    leitura = nuvem.leitura_da_origem()
    print(f"leitura da origem: {leitura}")
    assert str(len(udes)) in leitura
    assert "Árvore da Realidade Atual" in leitura
    assert str(ara.projeto.id) in leitura


def test_nuvem_sem_origem_nao_inventa_leitura() -> None:
    from toc_api.dominio.nuvem import novo_projeto_nc

    nuvem = novo_projeto_nc(id=ID_DA_NUVEM, dono=DONO, nome="Dilema autônomo", em=AGORA)

    assert nuvem.origem is None
    assert nuvem.leitura_da_origem() == ""


# --------------------------------------------------------------------------------------
# As recusas — cada uma com a regra nomeada
# --------------------------------------------------------------------------------------


def test_derivar_sem_nenhum_ude_e_recusado() -> None:
    ara, _ = ara_com_udes()

    with pytest.raises(DerivacaoInvalida) as erro:
        derivar_nuvem_de_udes(ara, no_ids=(), id=ID_DA_NUVEM, nome="Dilema", em=AGORA)
    print(f"regra: {erro.value.regra}")
    assert erro.value.regra == "sem_ude"


def test_derivar_de_no_que_nao_e_ude_e_recusado() -> None:
    """O efeito tem de estar MARCADO: derivar de nó qualquer seria nuvem sem dilema."""
    ara, udes = ara_com_udes()
    solto = ara.adicionar_efeito(titulo="O estacionamento vive cheio.", em=AGORA)

    with pytest.raises(DerivacaoInvalida) as erro:
        derivar_nuvem_de_udes(
            ara, no_ids=(udes[0], solto.id), id=ID_DA_NUVEM, nome="Dilema", em=AGORA
        )
    assert erro.value.regra == "no_nao_e_ude"


def test_derivar_de_no_inexistente_e_nao_encontrado() -> None:
    ara, _ = ara_com_udes()

    with pytest.raises(NaoEncontrado):
        derivar_nuvem_de_udes(ara, no_ids=(uuid4(),), id=ID_DA_NUVEM, nome="Dilema", em=AGORA)


def test_derivar_de_ude_rejeitado_e_recusado() -> None:
    ara, udes = ara_com_udes()
    ara.mudar_status(udes[0], StatusDeValidacao.REJEITADO, em=AGORA)

    with pytest.raises(DerivacaoInvalida) as erro:
        derivar_nuvem_de_udes(ara, no_ids=(udes[0],), id=ID_DA_NUVEM, nome="Dilema", em=AGORA)
    assert erro.value.regra == "ude_rejeitado"


def test_derivar_de_ude_validado_passa() -> None:
    """O caso que INT-05 descreve: UDE com decidíveis verdes e parecer humano favorável."""
    ara, udes = ara_com_udes()
    ara.registrar_parecer(
        udes[0],
        ParecerDeJulgamento(
            autor="u-horizonte-01",
            origem=OrigemDoParecer.HUMANO,
            favoravel=True,
            justificativa="a evasão está medida e documentada",
            instante=AGORA,
        ),
        em=AGORA,
    )
    ara.mudar_status(udes[0], StatusDeValidacao.VALIDADO, em=AGORA)

    nuvem = derivar_nuvem_de_udes(
        ara, no_ids=(udes[0],), id=ID_DA_NUVEM, nome="Dilema", em=AGORA
    )
    assert nuvem.origem.nos == (udes[0],)


def test_derivar_de_ara_excluida_e_recusado() -> None:
    ara, udes = ara_com_udes()
    ara.projeto.excluir(em=AGORA)

    with pytest.raises(MutacaoRecusada):
        derivar_nuvem_de_udes(ara, no_ids=tuple(udes), id=ID_DA_NUVEM, nome="Dilema", em=AGORA)


def test_a_nuvem_derivada_herda_o_dono_da_ara_e_nao_atravessa_o_inquilino() -> None:
    """O isolamento não é escolha do chamador: o dono vem do agregado de origem."""
    ara, udes = ara_com_udes(dono=OUTRO_DONO)

    nuvem = derivar_nuvem_de_udes(
        ara, no_ids=tuple(udes), id=ID_DA_NUVEM, nome="Dilema", em=AGORA
    )

    print(f"dono da ARA: {ara.projeto.dono}; dono da nuvem: {nuvem.projeto.dono}")
    assert nuvem.projeto.dono == ara.projeto.dono
    assert nuvem.projeto.dono.inquilino_id == OUTRO_DONO.inquilino_id


def test_a_referencia_de_origem_recusa_ser_construida_torta() -> None:
    """Tipada quer dizer isto: origem sem ferramenta, sem projeto ou sem nó não existe."""
    from toc_api.dominio.erros import DadoInvalido

    with pytest.raises(DadoInvalido):
        ReferenciaDeOrigem(ferramenta="", projeto_id=ID_DA_ARA, nos=(uuid4(),))
    with pytest.raises(DadoInvalido):
        ReferenciaDeOrigem(ferramenta=FERRAMENTA_ARA, projeto_id=ID_DA_ARA, nos=())


def test_a_nuvem_derivada_continua_editavel_como_qualquer_nuvem() -> None:
    """Derivar é o começo do trabalho, não um artefato só de leitura."""
    ara, udes = ara_com_udes()
    nuvem = derivar_nuvem_de_udes(
        ara, no_ids=tuple(udes), id=ID_DA_NUVEM, nome="Dilema", em=AGORA
    )

    nuvem.editar_entidade(PapelDaEntidade.B, "Receita nova no próximo semestre", em=AGORA)
    premissa = nuvem.registrar_premissa(
        ChaveDaAresta.A_B, "sem receita nova não há sustentabilidade", em=AGORA
    )
    nuvem.registrar_injecao(premissa.id, "convênio de bolsas com o município", em=AGORA)

    assert nuvem.validar().completude == (1, 7)
    assert nuvem.origem is not None
