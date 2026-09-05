"""As três ações governadas do M3 — geração e sugestões pelo catálogo `toc.*`.

Siglas, uma vez: **NC** — Nuvem de Conflito · **APH** — Aplicação ↔ Harness · **FSM** —
máquina de estados finitos · **IA** — inteligência artificial · **TRIZ** — Teoria da
Resolução Inventiva de Problemas · **SDK** — *Software Development Kit* · **JSON** —
*JavaScript Object Notation*.

O que este arquivo prova, e cada item corresponde a um defeito medido da 4ª geração:

1. **Verbo mutador nasce proposta** (RF-23): a geração não escreve nada até o gate humano.
2. **Recusar deixa o projeto byte a byte intacto** (RF-24) — o portão que o roadmap fixa
   para o ciclo 007. A comparação aqui é literalmente de bytes, não "parece igual".
3. **Sem `toc:write`, as três mutadoras não existem** para aquele principal (RF-27) — a
   lição que a irmã pagou e que o ciclo 006 já transformou em portão.
4. **Resultado fora do esquema é recusado antes de a proposta existir** (RF-22), e a
   recusa deixa traço (APH-5.5) — nada aplicado, nada meio-aplicado.
"""
from __future__ import annotations

import copy
import json
from datetime import timedelta
from uuid import UUID, uuid4

import pytest

from toc_api.aplicacao.federacao.acoes import DecidirProposta, ProporAcao
from toc_api.aplicacao.politica import PoliticaPorCapability
from toc_api.dominio.federacao.catalogo import CATALOGO_TOC, AcaoDesconhecida
from toc_api.dominio.federacao.esquema import ArgumentosInvalidos
from toc_api.dominio.federacao.principal import principal_de_introspeccao
from toc_api.dominio.federacao.proposta import Origem
from toc_api.dominio.nuvem import ChaveDaAresta, PapelDaEntidade, novo_projeto_nc
from toc_api.infra.federacao.executor import ExecutorDoCatalogo
from toc_api.infra.geracao.motor_local import MotorDeGeracaoLocal

from ..aplicacao.fakes import RastreadorFalso, RelogioFalso, RepositorioDeNuvemFalso
from ..dominio.nuvem_sintetica import AGORA, NARRATIVA
from ..dominio.test_resultado_de_geracao import BRUTO
from .fakes import (
    IdentificadoresFalsos,
    RelogioFixo,
    RepositorioDePropostasFalso,
    RepositorioDeTracoFalso,
)

ACOES_DO_M3 = (
    "toc.generate_conflict_cloud",
    "toc.suggest_assumptions",
    "toc.suggest_injections",
)

PRINCIPAL = principal_de_introspeccao(
    {
        "active": True,
        "user": {"id": "u-horizonte-01"},
        "tenant_id": "instituicao-horizonte",
        "capabilities": ["toc:read", "toc:write"],
    }
)
SO_LEITURA = principal_de_introspeccao(
    {
        "active": True,
        "user": {"id": "u-horizonte-02"},
        "tenant_id": "instituicao-horizonte",
        "capabilities": ["toc:read"],
    }
)


def instantaneo(nuvem) -> bytes:
    """O estado serializado da nuvem, canônico e completo — a régua do RF-24.

    Tudo o que uma proposta aceita poderia mudar entra aqui: texto de entidade, racional,
    premissas (com ordem, estado e justificativa) e injeções (com status, separação e
    arquivamento). Comparar isto antes e depois da recusa é a diferença entre "parece
    igual" e "é igual".
    """
    corpo = {
        "entidades": {p.value: nuvem.texto(p) for p in PapelDaEntidade},
        "racional": nuvem.racional,
        "premissas": sorted(
            [
                {
                    "id": str(p.id),
                    "aresta": p.aresta.value,
                    "texto": p.texto,
                    "ordem": p.ordem,
                    "estado": p.estado.value,
                    "justificativa": p.justificativa,
                    "arquivada": p.arquivada,
                }
                for p in nuvem._premissas.values()
            ],
            key=lambda d: d["id"],
        ),
        "injecoes": sorted(
            [
                {
                    "id": str(i.id),
                    "premissa_id": str(i.premissa_id),
                    "texto": i.texto,
                    "status": i.status.value,
                    "separacao": i.separacao.value if i.separacao else None,
                    "arquivada": i.arquivada,
                }
                for i in nuvem._injecoes.values()
            ],
            key=lambda d: d["id"],
        ),
    }
    return json.dumps(corpo, sort_keys=True, ensure_ascii=False).encode("utf-8")


def montar(*, principal=PRINCIPAL):
    rastreador = RastreadorFalso()
    repositorio = RepositorioDeNuvemFalso()
    nuvem = novo_projeto_nc(
        id=uuid4(), dono=principal.dono(), nome="Dilema da expansão", em=AGORA
    )
    # Conteúdo humano ANTES da geração: é ele que a recusa tem de deixar intacto.
    nuvem.editar_entidade(PapelDaEntidade.B, "Receita nova no próximo semestre", em=AGORA)
    nuvem.registrar_premissa(
        ChaveDaAresta.D_D_PRIME, "não há orçamento para as duas ações", em=AGORA
    )
    repositorio.salvar_nuvem(nuvem)

    executor = ExecutorDoCatalogo(
        rastreador=rastreador,
        projetos=repositorio,
        aras=repositorio,
        nuvens=repositorio,
        motor_de_geracao=MotorDeGeracaoLocal(),
        relogio=RelogioFalso(instante=AGORA),
    )
    propostas = RepositorioDePropostasFalso()
    tracos = RepositorioDeTracoFalso()
    comum = dict(
        rastreador=rastreador,
        catalogo=CATALOGO_TOC,
        propostas=propostas,
        tracos=tracos,
        executor=executor,
        relogio=RelogioFixo(),
        identificadores=IdentificadoresFalsos(),
        politica=PoliticaPorCapability(),
        ttl=timedelta(minutes=10),
    )
    return {
        "propor": ProporAcao(**comum),
        "decidir": DecidirProposta(**comum),
        "repositorio": repositorio,
        "tracos": tracos,
        "projeto_id": nuvem.projeto.id,
        "nuvem": lambda: repositorio.obter_nuvem(
            principal.dono().inquilino_id, nuvem.projeto.id
        ),
    }


# --------------------------------------------------------------------------------------
# O catálogo
# --------------------------------------------------------------------------------------


def test_as_tres_acoes_do_m3_estao_no_catalogo_e_sao_mutadoras() -> None:
    acoes = {a.action_id: a for a in CATALOGO_TOC.acoes}

    faltando = [a for a in ACOES_DO_M3 if a not in acoes]
    print(
        f"catálogo: {len(acoes)} ação(ões); do M3: "
        f"{[a for a in ACOES_DO_M3 if a in acoes]}"
    )
    assert faltando == [], faltando
    for action_id in ACOES_DO_M3:
        acao = acoes[action_id]
        assert acao.risk == "confirm", action_id
        assert acao.requires_confirmation, action_id
        assert acao.capability_exigida == "toc:write", action_id
        assert acao.ui_route.startswith("/toc/nc"), action_id


def test_sem_capability_de_escrita_as_tres_mutadoras_do_m3_nao_existem() -> None:
    """RF-27: ausência, nunca recusa visível — recusa revela o inventário (§B.7.3)."""
    visiveis = {a.action_id for a in CATALOGO_TOC.compor(SO_LEITURA)}

    print(f"visíveis só com toc:read: {len(visiveis)}; do M3: {visiveis & set(ACOES_DO_M3)}")
    assert visiveis & set(ACOES_DO_M3) == set()
    assert {a.action_id for a in CATALOGO_TOC.compor(PRINCIPAL)} >= set(ACOES_DO_M3)


def test_o_esquema_da_geracao_recusa_resultado_torto_antes_da_proposta() -> None:
    """RF-22: a validação é do servidor e vem ANTES de a proposta existir."""
    acao = CATALOGO_TOC.acao("toc.generate_conflict_cloud")
    torto = copy.deepcopy(BRUTO)
    torto["entidades"].pop("D_PRIME")

    acao.validar_args({"projeto_id": str(uuid4()), "resultado": copy.deepcopy(BRUTO)})
    with pytest.raises(ArgumentosInvalidos) as erro:
        acao.validar_args({"projeto_id": str(uuid4()), "resultado": torto})

    print(f"recusa do input_schema: {erro.value}")
    assert "D_PRIME" in str(erro.value)


# --------------------------------------------------------------------------------------
# A FSM: propor, recusar, aceitar
# --------------------------------------------------------------------------------------


def test_a_geracao_nasce_proposta_e_espera_o_gate_humano() -> None:
    peças = montar()
    antes = instantaneo(peças["nuvem"]())

    resultado = peças["propor"].rodar(
        principal=PRINCIPAL,
        action_id="toc.generate_conflict_cloud",
        args={
            "projeto_id": str(peças["projeto_id"]),
            "narrativa": NARRATIVA,
            "resultado": copy.deepcopy(BRUTO),
        },
        origem=Origem.IA,
    )

    print(
        f"estado da proposta: {resultado.proposta.estado}; "
        f"eventos: {[e[0] for e in resultado.eventos]}"
    )
    assert resultado.proposta.estado == "awaiting_approval"
    assert [e[0] for e in resultado.eventos] == ["action_proposal"]
    assert instantaneo(peças["nuvem"]()) == antes, "propor não pode escrever nada"


def test_recusar_a_geracao_deixa_o_projeto_byte_a_byte_intacto() -> None:
    """RF-24 e a DoD 5 — o portão executável que o roadmap fixa para este ciclo."""
    peças = montar()
    antes = instantaneo(peças["nuvem"]())

    proposta = peças["propor"].rodar(
        principal=PRINCIPAL,
        action_id="toc.generate_conflict_cloud",
        args={
            "projeto_id": str(peças["projeto_id"]),
            "narrativa": NARRATIVA,
            "resultado": copy.deepcopy(BRUTO),
        },
    ).proposta
    peças["decidir"].rodar(
        principal=PRINCIPAL, proposal_id=proposta.proposal_id, aprovado=False
    )

    depois = instantaneo(peças["nuvem"]())
    print(
        f"bytes antes: {len(antes)}; depois: {len(depois)}; iguais: {antes == depois}; "
        f"desfechos no traço: {peças['tracos'].desfechos}"
    )
    assert depois == antes
    assert "denied" in peças["tracos"].desfechos


def test_aceitar_a_geracao_aplica_de_uma_vez_com_a_proposta_nos_eventos() -> None:
    """RF-25: a mutação vinda de proposta aceita é distinguível de edição humana."""
    peças = montar()
    antes = instantaneo(peças["nuvem"]())

    proposta = peças["propor"].rodar(
        principal=PRINCIPAL,
        action_id="toc.generate_conflict_cloud",
        args={
            "projeto_id": str(peças["projeto_id"]),
            "narrativa": NARRATIVA,
            "resultado": copy.deepcopy(BRUTO),
        },
    ).proposta
    decidida = peças["decidir"].rodar(
        principal=PRINCIPAL, proposal_id=proposta.proposal_id, aprovado=True
    )

    nuvem = peças["nuvem"]()
    aplicados = [e for e in nuvem.eventos if type(e).__name__ == "GeracaoAplicada"]
    print(
        f"estado final: {decidida.proposta.estado}; "
        f"completude: {nuvem.validar().completude}; "
        f"eventos de geração: {[(e.premissas, e.injecoes) for e in aplicados]}"
    )
    assert decidida.proposta.estado == "executed"
    assert instantaneo(nuvem) != antes
    assert nuvem.texto(PapelDaEntidade.A) == BRUTO["entidades"]["A"]
    assert aplicados and aplicados[-1].proposta_id == proposta.proposal_id
    # A premissa que o grupo escreveu ANTES continua lá: a geração acumula (RN-05).
    textos = [p.texto for p in nuvem.premissas(ChaveDaAresta.D_D_PRIME)]
    assert "não há orçamento para as duas ações" in textos
    assert len(textos) == 2


def test_a_sugestao_de_premissa_e_uma_proposta_por_sugestao() -> None:
    """RF-26/US-13: aceitar duas e recusar uma exige propostas individuais."""
    peças = montar()
    sugestoes = ("as duas disputam a mesma equipe", "o calendário letivo não permite")

    propostas = [
        peças["propor"].rodar(
            principal=PRINCIPAL,
            action_id="toc.suggest_assumptions",
            args={
                "projeto_id": str(peças["projeto_id"]),
                "aresta": "D_D_PRIME",
                "texto": texto,
            },
        ).proposta
        for texto in sugestoes
    ]
    peças["decidir"].rodar(
        principal=PRINCIPAL, proposal_id=propostas[0].proposal_id, aprovado=True
    )
    peças["decidir"].rodar(
        principal=PRINCIPAL, proposal_id=propostas[1].proposal_id, aprovado=False
    )

    textos = [p.texto for p in peças["nuvem"]().premissas(ChaveDaAresta.D_D_PRIME)]
    print(f"premissas depois de aceitar uma e recusar outra: {textos}")
    assert sugestoes[0] in textos
    assert sugestoes[1] not in textos
    assert len(textos) == 2  # a humana original + a aceita


def test_a_sugestao_de_injecao_nasce_ligada_a_premissa_nomeada() -> None:
    peças = montar()
    premissa = peças["nuvem"]().premissas(ChaveDaAresta.D_D_PRIME)[0]

    proposta = peças["propor"].rodar(
        principal=PRINCIPAL,
        action_id="toc.suggest_injections",
        args={
            "projeto_id": str(peças["projeto_id"]),
            "premissa_id": str(premissa.id),
            "texto": "faseamento por marco de receita",
            "separacao": "tempo",
        },
    ).proposta
    peças["decidir"].rodar(
        principal=PRINCIPAL, proposal_id=proposta.proposal_id, aprovado=True
    )

    injecoes = peças["nuvem"]().injecoes_da_premissa(premissa.id)
    print(f"injeções ligadas à premissa: {[(i.texto, i.separacao) for i in injecoes]}")
    assert len(injecoes) == 1
    assert injecoes[0].premissa_id == premissa.id
    assert injecoes[0].separacao.value == "tempo"


def test_quem_so_le_nao_consegue_propor_as_acoes_do_m3() -> None:
    peças = montar()

    for action_id in ACOES_DO_M3:
        with pytest.raises(AcaoDesconhecida):
            peças["propor"].rodar(
                principal=SO_LEITURA,
                action_id=action_id,
                args={"projeto_id": str(peças["projeto_id"])},
            )

    print(f"recusas registradas no traço: {peças['tracos'].desfechos}")
    assert peças["tracos"].desfechos.count("denied") == len(ACOES_DO_M3)
