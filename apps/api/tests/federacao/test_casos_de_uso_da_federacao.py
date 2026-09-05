"""Casos de uso da federação — identidade, catálogo, proposta, decisão, lote e traço.

Siglas: **APH** — Aplicação ↔ Harness · **FSM** — máquina de estados finitos · **TTL** —
*Time To Live* (tempo de vida) · **UDE** — Efeito Indesejável · **HTTP** — *HyperText
Transfer Protocol*.

Tudo aqui roda **sem rede e sem banco** (P3/P4): as portas entram como duplos. O que estes
testes protegem são os requisitos que nenhum teste de domínio alcança sozinho — a ordem das
verificações, o traço que acompanha cada desfecho, e a autorização **no caso de uso**, que é
a armadilha do §B.7.2 (auditar `Depends(...)` na rota produz falso positivo sistemático, e
três equipes caíram nela).
"""
from __future__ import annotations

from datetime import timedelta

import pytest

from toc_api.aplicacao.federacao.acoes import DecidirProposta, ProporAcao
from toc_api.aplicacao.federacao.catalogo import ComporCatalogo
from toc_api.aplicacao.federacao.identidade import EstabelecerIdentidade
from toc_api.aplicacao.politica import PoliticaPorCapability, PoliticaSempreVerdadeira
from toc_api.dominio.federacao.catalogo import CATALOGO_TOC, AcaoDesconhecida
from toc_api.dominio.federacao.esquema import ArgumentosInvalidos
from toc_api.dominio.federacao.principal import (
    IntrospeccaoInvalida,
    principal_anonimo,
    principal_de_introspeccao,
)
from toc_api.dominio.federacao.proposta import Origem, TransicaoInvalida
from toc_api.dominio.federacao.traco import AcaoSemTraco

from .fakes import (
    AGORA,
    RESPOSTA_ATIVA,
    ExecutorFalso,
    FundacaoIndisponivel,
    IdentificadoresFalsos,
    IntrospeccaoFalsa,
    MotorFalso,
    RelogioFixo,
    RepositorioDePropostasFalso,
    RepositorioDeSessoesFalso,
    RepositorioDeTracoFalso,
)

from ..aplicacao.fakes import RastreadorFalso

PRINCIPAL = principal_de_introspeccao(RESPOSTA_ATIVA)
SO_LEITURA = principal_de_introspeccao({**RESPOSTA_ATIVA, "capabilities": ["toc:read"]})
UUID_SINTETICO = "11111111-1111-4111-8111-111111111111"


def _montar(
    *,
    politica=None,
    executor: ExecutorFalso | None = None,
    tracos: RepositorioDeTracoFalso | None = None,
    relogio: RelogioFixo | None = None,
):
    rastreador = RastreadorFalso()
    propostas = RepositorioDePropostasFalso()
    tracos = tracos if tracos is not None else RepositorioDeTracoFalso()
    executor = executor or ExecutorFalso()
    comum = dict(
        rastreador=rastreador,
        catalogo=CATALOGO_TOC,
        propostas=propostas,
        tracos=tracos,
        executor=executor,
        relogio=relogio or RelogioFixo(),
        identificadores=IdentificadoresFalsos(),
        politica=politica or PoliticaPorCapability(),
        ttl=timedelta(minutes=10),
    )
    return {
        "propor": ProporAcao(**comum),
        "decidir": DecidirProposta(**comum),
        "propostas": propostas,
        "tracos": tracos,
        "executor": executor,
        "rastreador": rastreador,
    }


# --------------------------------------------------------------------------------------
# Identidade (spec 003, RF-06..RF-13)
# --------------------------------------------------------------------------------------


def test_o_grant_e_trocado_uma_vez_e_descartado() -> None:
    """DoD 3 da spec 003: introspecção chamada 1×; o grant não fica em lugar nenhum."""
    porta = IntrospeccaoFalsa()
    caso = EstabelecerIdentidade(rastreador=RastreadorFalso(), introspeccao=porta, relogio=RelogioFixo())

    principal = caso.rodar(grant="ghdg_grant_sintetico")

    assert porta.chamadas == ["ghdg_grant_sintetico"]
    assert principal.inquilino_id == "instituicao-horizonte"
    assert "ghdg_" not in repr(principal)


def test_a_fundacao_fora_do_ar_falha_fechada() -> None:
    """RF-10: 5xx ou timeout ⇒ negação, zero dado — nunca presumir o grant válido."""
    porta = IntrospeccaoFalsa(indisponivel=True)
    caso = EstabelecerIdentidade(rastreador=RastreadorFalso(), introspeccao=porta, relogio=RelogioFixo())

    with pytest.raises(FundacaoIndisponivel):
        caso.rodar(grant="ghdg_x")


def test_grant_inativo_nao_produz_identidade() -> None:
    porta = IntrospeccaoFalsa(resposta={"active": False})
    caso = EstabelecerIdentidade(rastreador=RastreadorFalso(), introspeccao=porta, relogio=RelogioFixo())

    with pytest.raises(IntrospeccaoInvalida) as erro:
        caso.rodar(grant="ghdg_x")

    assert erro.value.codigo == "GRANT_INATIVO"


def test_principal_com_expires_at_vencido_e_recusado() -> None:
    """RF-13: sessão vencida exige novo embarque; nunca renovamos por conta própria."""
    porta = IntrospeccaoFalsa()
    caso = EstabelecerIdentidade(
        rastreador=RastreadorFalso(),
        introspeccao=porta,
        relogio=RelogioFixo(AGORA + timedelta(hours=2)),
    )

    with pytest.raises(IntrospeccaoInvalida) as erro:
        caso.rodar(grant="ghdg_x")

    assert erro.value.codigo == "SESSAO_EXPIRADA"


def test_o_span_do_embarque_cobre_a_introspeccao() -> None:
    """RF-33/P5: a chamada de introspecção tem span próprio, no traço do embarque."""
    rastreador = RastreadorFalso()
    caso = EstabelecerIdentidade(rastreador=rastreador, introspeccao=IntrospeccaoFalsa(), relogio=RelogioFixo())

    caso.rodar(grant="ghdg_x")

    assert "caso_de_uso.estabelecer_identidade" in rastreador.nomes


# --------------------------------------------------------------------------------------
# Catálogo composto
# --------------------------------------------------------------------------------------


def test_compor_catalogo_devolve_so_o_que_o_principal_pode() -> None:
    caso = ComporCatalogo(rastreador=RastreadorFalso(), catalogo=CATALOGO_TOC)

    completo = caso.rodar(principal=PRINCIPAL)
    leitura = caso.rodar(principal=SO_LEITURA)
    anonimo = caso.rodar(principal=principal_anonimo())

    assert len(completo) == 11
    assert len(leitura) == 4
    assert anonimo == []


# --------------------------------------------------------------------------------------
# Proposta: nada executa na menção (RF-10, DoD 2)
# --------------------------------------------------------------------------------------


def test_acao_mutadora_nasce_proposta_e_o_dominio_fica_intocado() -> None:
    m = _montar()

    resultado = m["propor"].rodar(
        principal=PRINCIPAL,
        action_id="toc.criar_nos",
        args={"projeto_id": UUID_SINTETICO, "nos": [{"titulo": "Entregas atrasam", "tipo": "ude"}]},
        origem=Origem.IA,
    )

    assert resultado.proposta.estado == "awaiting_approval"
    assert m["executor"].executados == [], "o domínio não pode ter sido tocado antes da decisão"
    assert [k for k, _ in resultado.eventos] == ["action_proposal"]


def test_acao_de_leitura_executa_direto_sem_gate() -> None:
    """RF-12: `read` executa direto; a proposta existe para o traço, e não para."""
    m = _montar()

    resultado = m["propor"].rodar(
        principal=PRINCIPAL, action_id="toc.listar_projetos", args={}, origem=Origem.IA
    )

    assert resultado.proposta.estado == "executed"
    assert [k for k, _ in resultado.eventos] == ["action_proposal", "action_result"]
    assert m["tracos"].desfechos == ["executed"]


def test_proposta_com_action_id_fora_do_catalogo_do_principal_e_recusada_com_traco() -> None:
    """RF-09: recusada com traço, sem executar nada."""
    m = _montar()

    with pytest.raises(AcaoDesconhecida):
        m["propor"].rodar(
            principal=SO_LEITURA,
            action_id="toc.criar_nos",
            args={"projeto_id": UUID_SINTETICO, "nos": [{"titulo": "t", "tipo": "ude"}]},
            origem=Origem.IA,
        )

    assert m["tracos"].desfechos == ["denied"]
    assert m["executor"].executados == []


def test_proposta_com_action_id_inexistente_e_recusada() -> None:
    m = _montar()

    with pytest.raises(AcaoDesconhecida):
        m["propor"].rodar(principal=PRINCIPAL, action_id="toc.apagar_tudo", args={}, origem=Origem.IA)


def test_args_invalidos_sao_recusados_com_traco_e_sem_execucao_parcial() -> None:
    """RF-31: parâmetro inválido é recusa com traço, nunca execução parcial."""
    m = _montar()

    with pytest.raises(ArgumentosInvalidos):
        m["propor"].rodar(
            principal=PRINCIPAL,
            action_id="toc.criar_nos",
            args={"projeto_id": UUID_SINTETICO, "nos": []},
            origem=Origem.IA,
        )

    assert m["tracos"].desfechos == ["denied"]
    assert m["executor"].executados == []


def test_principal_anonimo_nao_propoe_nada() -> None:
    m = _montar()

    with pytest.raises(IntrospeccaoInvalida):
        m["propor"].rodar(
            principal=principal_anonimo(), action_id="toc.listar_projetos", args={}, origem=Origem.IA
        )


# --------------------------------------------------------------------------------------
# Autorização NO CASO DE USO (RF-17) e a sabotagem da política (RF-20, DoD 4)
# --------------------------------------------------------------------------------------


def test_a_recusa_por_capability_acontece_no_caso_de_uso_sem_http() -> None:
    """§B.7.2: a verificação vive onde a ação acontece — e este teste prova isso sem rota.

    Nenhum `TestClient`, nenhum `Depends`. Se a autorização morasse na camada de rota,
    este teste passaria com a recusa **não** acontecendo, e a auditoria por `Depends(...)`
    diria que está tudo bem: é exatamente o falso positivo que a norma registrou.
    """
    m = _montar()

    with pytest.raises(AcaoDesconhecida):
        m["propor"].rodar(
            principal=SO_LEITURA,
            action_id="toc.excluir_nos",
            args={"projeto_id": UUID_SINTETICO, "no_ids": ["n1"]},
            origem=Origem.IA,
        )


def test_a_sabotagem_da_politica_derruba_o_teste_de_recusa() -> None:
    """RF-20 / DoD 4: a política sempre-verdadeira é não-conformidade declarada (APH-7.2).

    O teste não afirma que a sabotagem é boa: ele prova que os testes de recusa **veem**
    a política. Com `PoliticaSempreVerdadeira`, a recusa acima deixa de acontecer — e é
    isso que mostra que o teste anterior não passa por acaso.
    """
    m = _montar(politica=PoliticaSempreVerdadeira())

    resultado = m["propor"].rodar(
        principal=SO_LEITURA,
        action_id="toc.excluir_nos",
        args={"projeto_id": UUID_SINTETICO, "no_ids": ["n1"]},
        origem=Origem.IA,
    )

    assert resultado.proposta.estado == "awaiting_approval", (
        "com a política sabotada a recusa some — o que prova que o teste de recusa mede a política"
    )


def test_sem_repositorio_de_traco_a_execucao_e_rejeitada_antes_do_efeito() -> None:
    """DoD 5 / APH-5.5: "ação sem traço é ação não governada, e DEVE ser rejeitada"."""
    m = _montar(tracos=None)
    m = _montar()
    m["propor"]._tracos = None  # a sabotagem: some com o sumidouro de traço

    with pytest.raises(AcaoSemTraco):
        m["propor"].rodar(principal=PRINCIPAL, action_id="toc.listar_projetos", args={}, origem=Origem.IA)

    assert m["executor"].executados == [], "nada pode ter sido executado sem traço"


# --------------------------------------------------------------------------------------
# Decisão (RF-14..RF-16)
# --------------------------------------------------------------------------------------


def _propor_lote(m, alvos: int = 8):
    return m["propor"].rodar(
        principal=PRINCIPAL,
        action_id="toc.criar_nos",
        args={
            "projeto_id": UUID_SINTETICO,
            "nos": [{"titulo": f"UDE {i}", "tipo": "ude"} for i in range(1, alvos + 1)],
        },
        origem=Origem.IA,
        # A proposta nasce carimbada com o snapshot que a originou; sem o carimbo, a
        # comparação do APH-5.4 não teria contra o que comparar.
        contexto_hash="0123456789abcdef",
    ).proposta


def test_confirmar_executa_e_deixa_traco() -> None:
    m = _montar()
    proposta = _propor_lote(m, alvos=1)

    resultado = m["decidir"].rodar(
        principal=PRINCIPAL, proposal_id=proposta.proposal_id, aprovado=True
    )

    assert resultado.proposta.estado == "executed"
    assert m["tracos"].desfechos == ["executed"]
    assert [k for k, _ in resultado.eventos] == ["action_result"]


def test_negar_encerra_em_denied_com_traco() -> None:
    """RF-14: `approved: false` encerra em `denied` **com traço**."""
    m = _montar()
    proposta = _propor_lote(m, alvos=1)

    resultado = m["decidir"].rodar(
        principal=PRINCIPAL, proposal_id=proposta.proposal_id, aprovado=False
    )

    assert resultado.proposta.estado == "denied"
    assert m["tracos"].desfechos == ["denied"]
    assert m["executor"].executados == []


def test_confirmar_duas_vezes_nao_reexecuta() -> None:
    """RF-16: a segunda confirmação recebe o mesmo resultado, sem novo efeito."""
    m = _montar()
    proposta = _propor_lote(m, alvos=1)
    m["decidir"].rodar(principal=PRINCIPAL, proposal_id=proposta.proposal_id, aprovado=True)
    executados = list(m["executor"].executados)

    de_novo = m["decidir"].rodar(principal=PRINCIPAL, proposal_id=proposta.proposal_id, aprovado=True)

    assert m["executor"].executados == executados
    assert de_novo.proposta.desfecho.status == "executed"
    assert de_novo.proposta.execucoes == 1
    assert m["tracos"].desfechos == ["executed"], "o traço não duplica numa decisão repetida"


def test_confirmar_com_context_hash_divergente_recusa_com_traco() -> None:
    """RF-15: `PROPOSAL_CONTEXT_STALE`, sem executar."""
    m = _montar()
    proposta = _propor_lote(m, alvos=1)

    with pytest.raises(TransicaoInvalida) as erro:
        m["decidir"].rodar(
            principal=PRINCIPAL,
            proposal_id=proposta.proposal_id,
            aprovado=True,
            contexto_hash="ffffffffffffffff",
        )

    assert erro.value.codigo == "PROPOSAL_CONTEXT_STALE"
    assert m["executor"].executados == []
    assert m["tracos"].desfechos == ["cancelled"]


def test_decisao_apos_o_ttl_expira_com_traco() -> None:
    """RF-13: vencida é desfecho — e desfecho deixa traço (RF-21)."""
    relogio = RelogioFixo()
    m = _montar(relogio=relogio)
    proposta = _propor_lote(m, alvos=1)
    relogio.instante = AGORA + timedelta(minutes=11)

    with pytest.raises(TransicaoInvalida) as erro:
        m["decidir"].rodar(principal=PRINCIPAL, proposal_id=proposta.proposal_id, aprovado=True)

    assert erro.value.codigo == "PROPOSAL_EXPIRED"
    assert m["tracos"].desfechos == ["expired"]
    assert m["executor"].executados == []


def test_proposta_de_outro_inquilino_nao_e_alcancavel() -> None:
    m = _montar()
    proposta = _propor_lote(m, alvos=1)
    de_outro = principal_de_introspeccao({**RESPOSTA_ATIVA, "tenant_id": "outra-instituicao"})

    with pytest.raises(AcaoDesconhecida):
        m["decidir"].rodar(principal=de_outro, proposal_id=proposta.proposal_id, aprovado=True)


# --------------------------------------------------------------------------------------
# Lote (RF-24..RF-29, DoD 6)
# --------------------------------------------------------------------------------------


def test_lote_de_oito_e_uma_proposta_com_a_contagem_antes_da_decisao() -> None:
    m = _montar()

    proposta = _propor_lote(m, alvos=8)

    assert proposta.quantidade_de_alvos == 8
    assert len(m["propostas"].itens) == 1, "oito alvos, UMA proposta (APH-5.9)"


def test_lote_com_uma_falha_nao_termina_em_executed() -> None:
    """DoD 6 e o fluxo 6.4 da spec: o item 7 falha e o `status` não mente."""
    executor = ExecutorFalso(falhar_em={"UDE 7"})
    m = _montar(executor=executor)
    proposta = _propor_lote(m, alvos=8)

    resultado = m["decidir"].rodar(
        principal=PRINCIPAL, proposal_id=proposta.proposal_id, aprovado=True
    )

    desfecho = resultado.proposta.desfecho
    assert resultado.proposta.estado == "failed"
    assert desfecho.status == "failed"
    assert len(desfecho.outcomes) == 8
    assert sum(1 for _, s, _ in desfecho.outcomes if s == "executed") == 7
    assert [a for a, s, _ in desfecho.outcomes if s == "failed"] == ["UDE 7"]


def test_o_traco_de_lote_discrimina_o_desfecho_por_alvo() -> None:
    """RF-26: `outcomes[]` no traço, não só no evento."""
    m = _montar(executor=ExecutorFalso(falhar_em={"UDE 2"}))
    proposta = _propor_lote(m, alvos=3)

    m["decidir"].rodar(principal=PRINCIPAL, proposal_id=proposta.proposal_id, aprovado=True)

    linha = m["tracos"].linhas[-1]
    assert len(linha.outcomes) == 3
    assert dict((a, s) for a, s, _ in linha.outcomes)["UDE 2"] == "failed"


def test_o_evento_de_resultado_de_lote_valida_a_invariante_do_status() -> None:
    m = _montar(executor=ExecutorFalso(falhar_em={"UDE 1"}))
    proposta = _propor_lote(m, alvos=2)

    resultado = m["decidir"].rodar(
        principal=PRINCIPAL, proposal_id=proposta.proposal_id, aprovado=True
    )

    payload = dict(resultado.eventos[0][1])
    assert payload["status"] != "executed"
    assert {o["target"] for o in payload["outcomes"]} == {"UDE 1", "UDE 2"}


def test_lote_sobre_acao_nao_desenhada_para_lote_e_recusado() -> None:
    """RF-28: ação sem `batch_atomicity` não aceita proposta em lote."""
    m = _montar()

    resultado = m["propor"].rodar(
        principal=PRINCIPAL,
        action_id="toc.atualizar_no",
        args={"projeto_id": UUID_SINTETICO, "no_id": "n1", "titulo": "novo"},
        origem=Origem.IA,
    )

    assert resultado.proposta.quantidade_de_alvos == 0, (
        "ação sem batch_atomicity não tem alvos de lote — ausente nunca significa per_item"
    )


# --------------------------------------------------------------------------------------
# Traço de 100% (RF-21, DoD 5) e escopo (RF-22)
# --------------------------------------------------------------------------------------


def test_todo_desfecho_deixa_traco_inclusive_os_que_nao_executaram() -> None:
    """US-06: "o que a IA fez neste projeto" tem resposta completa — inclusive as negadas."""
    relogio = RelogioFixo()
    m = _montar(relogio=relogio)

    # executada
    m["propor"].rodar(principal=PRINCIPAL, action_id="toc.listar_projetos", args={}, origem=Origem.IA)
    # negada
    negada = _propor_lote(m, alvos=1)
    m["decidir"].rodar(principal=PRINCIPAL, proposal_id=negada.proposal_id, aprovado=False)
    # recusada por política
    with pytest.raises(AcaoDesconhecida):
        m["propor"].rodar(
            principal=SO_LEITURA,
            action_id="toc.criar_nos",
            args={"projeto_id": UUID_SINTETICO, "nos": [{"titulo": "t", "tipo": "ude"}]},
            origem=Origem.IA,
        )
    # expirada
    expirada = _propor_lote(m, alvos=1)
    relogio.instante = AGORA + timedelta(minutes=11)
    with pytest.raises(TransicaoInvalida):
        m["decidir"].rodar(principal=PRINCIPAL, proposal_id=expirada.proposal_id, aprovado=True)

    assert m["tracos"].desfechos == ["executed", "denied", "denied", "expired"]


def test_o_traco_e_escopado_por_inquilino_e_usuario() -> None:
    """RF-22 / APH-7.4."""
    m = _montar()
    m["propor"].rodar(principal=PRINCIPAL, action_id="toc.listar_projetos", args={}, origem=Origem.IA)

    assert m["tracos"].listar("instituicao-horizonte") != []
    assert m["tracos"].listar("outra-instituicao") == []
    assert m["tracos"].listar("instituicao-horizonte", usuario_id="outro") == []


def test_o_span_da_proposta_carrega_o_inquilino_e_nunca_o_texto() -> None:
    """P5 + ADR 0006: grandeza no span, nunca enunciado de pessoa."""
    m = _montar()

    m["propor"].rodar(
        principal=PRINCIPAL,
        action_id="toc.criar_nos",
        args={"projeto_id": UUID_SINTETICO, "nos": [{"titulo": "Entregas atrasam", "tipo": "ude"}]},
        origem=Origem.IA,
    )

    span = m["rastreador"].spans[-1]
    assert span.atributos["toc.inquilino_id"] == "instituicao-horizonte"
    assert "Entregas atrasam" not in str(span.atributos)


def test_a_origem_entra_no_traco_como_dado() -> None:
    m = _montar()

    m["propor"].rodar(
        principal=PRINCIPAL, action_id="toc.listar_projetos", args={}, origem=Origem.HUMANO
    )

    assert m["tracos"].linhas[-1].origem == Origem.HUMANO
