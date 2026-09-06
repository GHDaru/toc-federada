"""M4 · E4.3 — a Árvore de Transição (AT): passos com ação, necessidade e resultado.

Siglas, uma vez neste arquivo: **AT** — Árvore de Transição · **APR** — Árvore de
Pré-Requisitos · **OI** — Objetivo Intermediário · **TOC** — Teoria das Restrições ·
**M1** — Núcleo de Diagramas Lógicos · **RF/RN** — requisito funcional / regra de negócio
da spec 008.

A regra que dá sentido à ferramenta é a RN-10: **a tripla é obrigatória**. "Passo sem
necessidade explícita é o que degrada a AT a lista de tarefas" — e uma lista de tarefas
não é um Processo de Pensamento. Por isso os três campos são exigidos na criação, e não
"recomendados".

A segunda regra é a do acompanhamento: ao concluir com resultado real diferente do
esperado, **a divergência fica no evento e o esperado não é sobrescrito** (RF-30). Apagar
o esperado apagaria a pergunta que a AT existe para responder — "o passo produziu o que
devia?".

Base sintética (ADR 0006): "Instituição Horizonte", personas fictícias.
"""
from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID, uuid4

import pytest

from toc_api.dominio.at import (
    FERRAMENTA_AT,
    FichaDePasso,
    PassoInvalido,
    ProjetoAT,
    StatusDoPasso,
    TransicaoDePassoRecusada,
    novo_projeto_at,
    reidratar_at,
)
from toc_api.dominio.erros import DadoInvalido, MutacaoForaDaRaiz, MutacaoRecusada
from toc_api.dominio.eventos import PassoMudouDeStatus, PassoRegistrado
from toc_api.dominio.identidade import DonoDoProjeto
from toc_api.dominio.referencia import Ponta

AGORA = datetime(2026, 9, 6, 10, 0, tzinfo=timezone.utc)
DONO = DonoDoProjeto(inquilino_id="instituicao-horizonte", usuario_id="u-facilitadora")
ID_DA_AT = UUID("22222222-2222-4222-8222-222222222201")
ID_DA_APR = UUID("33333333-3333-4333-8333-333333333301")

ACAO = "publicar a chamada interna de treinamento"
NECESSIDADE = "não há hoje candidato mapeado"
ESPERADO = "lista de inscritos até sexta"


def at() -> ProjetoAT:
    arvore = novo_projeto_at(id=ID_DA_AT, dono=DONO, nome="Transição do treinamento", em=AGORA)
    arvore.drenar_eventos()
    return arvore


def passo(arvore: ProjetoAT, acao: str = ACAO):
    return arvore.registrar_passo(
        acao=acao, necessidade=NECESSIDADE, resultado_esperado=ESPERADO, em=AGORA
    )


# --------------------------------------------------------------------------------------
# F4.3.1 — a tripla obrigatória e a leitura corrida (RF-28, RF-29, RN-10)
# --------------------------------------------------------------------------------------


def test_a_at_nasce_vazia_com_a_ferramenta_propria() -> None:
    arvore = novo_projeto_at(id=ID_DA_AT, dono=DONO, nome="Transição", em=AGORA)
    print(f"ferramenta={arvore.projeto.ferramenta!r} passos={len(arvore.passos)}")
    assert arvore.projeto.ferramenta == FERRAMENTA_AT
    assert arvore.passos == ()


def test_o_projeto_da_at_recusa_mutacao_que_nao_venha_pela_raiz() -> None:
    arvore = at()
    with pytest.raises(MutacaoForaDaRaiz) as erro:
        arvore.projeto.adicionar_no(titulo="por fora", em=AGORA)
    print(f"recusa: raiz={erro.value.raiz!r}")
    assert erro.value.raiz == "ProjetoAT"


def test_o_passo_exige_a_tripla_inteira_na_criacao() -> None:
    """RN-10: os três campos são obrigatórios — sem exceção e sem valor padrão."""
    arvore = at()
    for faltando in ("acao", "necessidade", "resultado_esperado"):
        campos = {"acao": ACAO, "necessidade": NECESSIDADE, "resultado_esperado": ESPERADO}
        campos[faltando] = "   "
        with pytest.raises(DadoInvalido) as erro:
            arvore.registrar_passo(em=AGORA, **campos)
        print(f"sem {faltando}: {erro.value}")
        assert faltando.split("_")[0] in str(erro.value)


def test_a_ficha_do_passo_se_le_para_necessidade_acao_espero_resultado() -> None:
    arvore = at()
    novo = passo(arvore)

    leitura = arvore.leitura_do_passo(novo.id)
    print(f"leitura: {leitura}")
    assert leitura == f"Para {NECESSIDADE}, {ACAO}; espero {ESPERADO}"
    assert isinstance(arvore.projeto.eventos[-1], PassoRegistrado)
    assert arvore.ficha(novo.id).status is StatusDoPasso.PENDENTE


def test_o_titulo_do_no_acompanha_a_acao_do_passo() -> None:
    """O nó do M1 continua sendo o nó do M1: o título é a ação, e a ficha é o resto."""
    arvore = at()
    novo = passo(arvore)
    assert arvore.projeto.no(novo.id).titulo == ACAO

    arvore.editar_ficha(novo.id, acao="publicar a chamada interna e o calendário", em=AGORA)
    assert arvore.projeto.no(novo.id).titulo == "publicar a chamada interna e o calendário"
    assert arvore.ficha(novo.id).necessidade == NECESSIDADE


def test_a_precedencia_encadeia_os_passos_e_a_leitura_segue_a_ordem() -> None:
    """RF-32: a leitura da AT segue a precedência declarada."""
    arvore = at()
    primeiro = passo(arvore, acao="publicar a chamada interna de treinamento")
    segundo = passo(arvore, acao="selecionar as três pessoas inscritas")
    terceiro = passo(arvore, acao="realizar a oficina de matrícula")
    arvore.preceder(primeiro.id, segundo.id, em=AGORA)
    arvore.preceder(segundo.id, terceiro.id, em=AGORA)

    ordem = [arvore.projeto.no(i).titulo for i in arvore.ordem_de_leitura()]
    print(f"ordem: {' → '.join(ordem)}")
    assert ordem == [
        "publicar a chamada interna de treinamento",
        "selecionar as três pessoas inscritas",
        "realizar a oficina de matrícula",
    ]


def test_passo_inalcancavel_e_pendencia_e_nao_proibicao() -> None:
    """RF-32: "apontar passos inalcançáveis (sem caminho desde os passos iniciais)"."""
    arvore = at()
    primeiro = passo(arvore, acao="publicar a chamada interna")
    segundo = passo(arvore, acao="selecionar as inscritas")
    arvore.preceder(primeiro.id, segundo.id, em=AGORA)
    ilha_a = passo(arvore, acao="assinar o termo de cessão da sala")
    ilha_b = passo(arvore, acao="registrar a oficina no sistema")
    # Um par isolado com precedência circular: nenhum deles é alcançável desde um início.
    arvore.preceder(ilha_a.id, ilha_b.id, em=AGORA)
    arvore.preceder(ilha_b.id, ilha_a.id, em=AGORA)

    inalcancaveis = arvore.passos_inalcancaveis()

    print(f"inalcançáveis: {len(inalcancaveis)}")
    assert set(inalcancaveis) == {ilha_a.id, ilha_b.id}


# --------------------------------------------------------------------------------------
# F4.3.2 — acompanhamento leve de execução (RF-30, RF-31)
# --------------------------------------------------------------------------------------


def test_bloquear_exige_motivo_e_o_resumo_mostra_o_passo_bloqueado() -> None:
    arvore = at()
    novo = passo(arvore)

    with pytest.raises(TransicaoDePassoRecusada) as erro:
        arvore.mudar_status(novo.id, StatusDoPasso.BLOQUEADO, em=AGORA)
    print(f"recusa: motivo={erro.value.motivo!r}")
    assert erro.value.motivo == "motivo_obrigatorio"

    arvore.mudar_status(
        novo.id,
        StatusDoPasso.BLOQUEADO,
        motivo="a sala de oficina está em reforma até o dia 20",
        em=AGORA,
    )

    resumo = arvore.resumo_de_execucao()
    print(f"resumo: {resumo}")
    assert resumo["bloqueado"] == 1
    assert arvore.bloqueados()[0][1] == "a sala de oficina está em reforma até o dia 20"


def test_concluir_registra_o_resultado_real_e_nao_sobrescreve_o_esperado() -> None:
    """RF-30: "divergência entre esperado e real fica no evento, nunca sobrescreve"."""
    arvore = at()
    novo = passo(arvore)
    arvore.mudar_status(novo.id, StatusDoPasso.EM_EXECUCAO, em=AGORA)

    arvore.mudar_status(
        novo.id,
        StatusDoPasso.CONCLUIDO,
        resultado_real="apenas duas inscritas até sexta",
        em=AGORA,
    )

    ficha = arvore.ficha(novo.id)
    evento = arvore.projeto.eventos[-1]
    print(
        f"esperado={ficha.resultado_esperado!r} real={ficha.resultado_real!r} "
        f"divergente={evento.divergente}"
    )
    assert ficha.resultado_esperado == ESPERADO
    assert ficha.resultado_real == "apenas duas inscritas até sexta"
    assert isinstance(evento, PassoMudouDeStatus)
    assert evento.divergente is True
    assert evento.resultado_real == "apenas duas inscritas até sexta"


def test_concluir_com_o_resultado_esperado_nao_marca_divergencia() -> None:
    arvore = at()
    novo = passo(arvore)
    arvore.mudar_status(novo.id, StatusDoPasso.CONCLUIDO, resultado_real=ESPERADO, em=AGORA)
    assert arvore.projeto.eventos[-1].divergente is False


def test_concluir_exige_o_resultado_real() -> None:
    arvore = at()
    novo = passo(arvore)
    with pytest.raises(TransicaoDePassoRecusada) as erro:
        arvore.mudar_status(novo.id, StatusDoPasso.CONCLUIDO, em=AGORA)
    assert erro.value.motivo == "resultado_real_obrigatorio"


def test_mudar_para_o_mesmo_status_e_recusado() -> None:
    arvore = at()
    novo = passo(arvore)
    with pytest.raises(TransicaoDePassoRecusada) as erro:
        arvore.mudar_status(novo.id, StatusDoPasso.PENDENTE, em=AGORA)
    assert erro.value.motivo == "sem_mudanca"


def test_desbloquear_limpa_o_motivo() -> None:
    arvore = at()
    novo = passo(arvore)
    arvore.mudar_status(novo.id, StatusDoPasso.BLOQUEADO, motivo="sala em reforma", em=AGORA)

    arvore.mudar_status(novo.id, StatusDoPasso.EM_EXECUCAO, em=AGORA)

    assert arvore.ficha(novo.id).motivo_do_bloqueio == ""
    assert arvore.bloqueados() == ()


def test_o_resumo_de_execucao_conta_os_quatro_status() -> None:
    """RF-31: contagem por status no cabeçalho do projeto."""
    arvore = at()
    um, dois, tres = (passo(arvore, acao=f"passo {i}") for i in range(3))
    arvore.mudar_status(dois.id, StatusDoPasso.EM_EXECUCAO, em=AGORA)
    arvore.mudar_status(tres.id, StatusDoPasso.BLOQUEADO, motivo="sem sala", em=AGORA)

    resumo = arvore.resumo_de_execucao()

    print(f"resumo: {resumo}")
    assert resumo == {
        "pendente": 1,
        "em_execucao": 1,
        "concluido": 0,
        "bloqueado": 1,
        "passos": 3,
        "inalcancaveis": 0,
    }


# --------------------------------------------------------------------------------------
# O alvo (RF-28/RF-40) e a reidratação
# --------------------------------------------------------------------------------------


def test_a_at_derivada_carrega_o_alvo_navegavel() -> None:
    oi = uuid4()
    arvore = novo_projeto_at(
        id=ID_DA_AT,
        dono=DONO,
        nome="Transição do treinamento",
        em=AGORA,
        alvo=Ponta(
            ferramenta="apr",
            projeto_id=ID_DA_APR,
            elementos=(oi,),
            papel="objetivo_intermediario",
        ),
    )
    print(f"alvo: {arvore.alvo}")
    assert arvore.alvo.projeto_id == ID_DA_APR
    assert arvore.alvo.elementos == (oi,)


def test_excluir_o_passo_leva_a_ficha_junto() -> None:
    arvore = at()
    novo = passo(arvore)
    arvore.excluir_no(novo.id, em=AGORA)
    assert arvore.passos == ()
    with pytest.raises(MutacaoRecusada):
        arvore.ficha(novo.id)


def test_reidratar_a_at_nao_emite_evento_nenhum() -> None:
    arvore = at()
    novo = passo(arvore)

    de_volta = reidratar_at(arvore.projeto, fichas={novo.id: arvore.ficha(novo.id)})

    print(f"eventos após reidratar: {len(de_volta.projeto.eventos)}")
    assert de_volta.projeto.eventos == ()
    assert de_volta.ficha(novo.id).acao == ACAO


def test_a_ficha_e_objeto_de_valor_e_valida_a_si_mesma() -> None:
    with pytest.raises(DadoInvalido):
        FichaDePasso(acao=ACAO, necessidade=NECESSIDADE, resultado_esperado="")
    ficha = FichaDePasso(acao=ACAO, necessidade=NECESSIDADE, resultado_esperado=ESPERADO)
    assert ficha.leitura() == f"Para {NECESSIDADE}, {ACAO}; espero {ESPERADO}"
