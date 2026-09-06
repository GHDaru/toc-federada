"""As quatro ações governadas do M4 — sugerir efeito, obstáculo, objetivo e passo.

Siglas, uma vez neste arquivo: **M4** — Árvores de Futuro e Implementação · **ARF** —
Árvore da Realidade Futura · **APR** — Árvore de Pré-Requisitos · **AT** — Árvore de
Transição · **OI** — Objetivo Intermediário · **APH** — Aplicação ↔ Harness · **FSM** —
máquina de estados finitos · **IA** — inteligência artificial · **JSON** — *JavaScript
Object Notation* · **RF/RN/RNF** — requisito funcional / regra de negócio / requisito não
funcional da spec 008.

**A diferença deste ciclo para o M2 e o M3**: aqui as ações **executam**. A máquina de
estados do ciclo 006 existe, e o P2 deixa de ser prova negativa ("nada muta") e passa a
ser prova positiva: mutação direta **recusada**, aceite **cria com traço correlacionado à
proposta** (DoD 10 da spec 008).

O que este arquivo prova, item a item:

1. **Verbo mutador nasce proposta** (RF-43): propor não escreve nada.
2. **Recusar deixa a árvore byte a byte intacta** — comparação de bytes, não "parece igual".
3. **Sem `toc:write`, as quatro não existem** para aquele principal (RF-45) — ausência,
   nunca recusa visível (§B.7.3 do Anexo B).
4. **A tripla do passo é conferida ANTES de a proposta existir** (INT-08): argumento
   incompleto é recusado pelo `input_schema`, com traço da recusa (APH-5.5).
5. **Não existe ação de ramo negativo** (RF-10) — a prova negativa da DoD 8.
"""
from __future__ import annotations

import json
from datetime import timedelta
from uuid import uuid4

import pytest

from toc_api.aplicacao.federacao.acoes import DecidirProposta, ProporAcao
from toc_api.aplicacao.politica import PoliticaPorCapability
from toc_api.dominio.apr import PapelNaAPR, novo_projeto_apr
from toc_api.dominio.arf import PapelNaARF, novo_projeto_arf
from toc_api.dominio.at import novo_projeto_at
from toc_api.dominio.federacao.catalogo import CATALOGO_TOC, AcaoDesconhecida
from toc_api.dominio.federacao.esquema import ArgumentosInvalidos
from toc_api.dominio.federacao.principal import principal_de_introspeccao
from toc_api.dominio.federacao.proposta import Origem
from toc_api.infra.federacao.executor import ExecutorDoCatalogo

from ..aplicacao.fakes import RastreadorFalso, RelogioFalso
from ..aplicacao.fakes_m4 import RepositorioDoM4Falso
from ..dominio.nuvem_sintetica import AGORA
from .fakes import (
    IdentificadoresFalsos,
    RelogioFixo,
    RepositorioDePropostasFalso,
    RepositorioDeTracoFalso,
)

ACOES_DO_M4 = (
    "toc.suggest_future_effects",
    "toc.suggest_obstacles",
    "toc.suggest_intermediate_objectives",
    "toc.suggest_transition_steps",
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

INJECAO = "faseamento orçamentário condicionado a marco de receita"
OBSTACULO = "Há apenas uma pessoa treinada no acompanhamento do marco"


def instantaneo(arvore) -> bytes:
    """O estado serializado de uma árvore — a régua de "byte a byte intacta"."""
    corpo = {
        "nos": sorted(
            [{"id": str(n.id), "tipo": n.tipo, "titulo": n.titulo} for n in arvore.projeto.nos],
            key=lambda d: d["id"],
        ),
        "arestas": sorted(
            [
                {"id": str(a.id), "origem": str(a.origem_id), "destino": str(a.destino_id)}
                for a in arvore.projeto.arestas
            ],
            key=lambda d: d["id"],
        ),
        "versao": arvore.projeto.versao,
    }
    return json.dumps(corpo, sort_keys=True, ensure_ascii=False).encode("utf-8")


def montar(*, principal=PRINCIPAL):
    """Uma ARF semeada, uma APR com obstáculo e uma AT — o cenário das quatro ações."""
    rastreador = RastreadorFalso()
    repositorio = RepositorioDoM4Falso()

    arf = novo_projeto_arf(
        id=uuid4(), dono=principal.dono(), nome="Futuro da expansão", em=AGORA
    )
    injecao = arf.adicionar_injecao(titulo=INJECAO, em=AGORA)
    repositorio.salvar_arf(arf)

    apr = novo_projeto_apr(
        id=uuid4(),
        dono=principal.dono(),
        nome="Implantação",
        objetivo="O faseamento está implantado nas duas frentes",
        em=AGORA,
    )
    obstaculo = apr.adicionar_obstaculo(titulo=OBSTACULO, em=AGORA)
    repositorio.salvar_apr(apr)

    at = novo_projeto_at(id=uuid4(), dono=principal.dono(), nome="Transição", em=AGORA)
    repositorio.salvar_at(at)

    executor = ExecutorDoCatalogo(
        rastreador=rastreador,
        projetos=repositorio,
        aras=repositorio,
        nuvens=repositorio,
        arvores=repositorio,
        relogio=RelogioFalso(instante=AGORA),
    )
    comum = dict(
        rastreador=rastreador,
        catalogo=CATALOGO_TOC,
        propostas=RepositorioDePropostasFalso(),
        tracos=RepositorioDeTracoFalso(),
        executor=executor,
        relogio=RelogioFixo(),
        identificadores=IdentificadoresFalsos(),
        politica=PoliticaPorCapability(),
        ttl=timedelta(minutes=10),
    )
    return {
        "propor": ProporAcao(**comum),
        "decidir": DecidirProposta(**comum),
        "tracos": comum["tracos"],
        "repositorio": repositorio,
        "arf_id": arf.projeto.id,
        "injecao_id": injecao.id,
        "apr_id": apr.projeto.id,
        "obstaculo_id": obstaculo.id,
        "at_id": at.projeto.id,
        "arf": lambda: repositorio.obter_arf(principal.dono().inquilino_id, arf.projeto.id),
        "apr": lambda: repositorio.obter_apr(principal.dono().inquilino_id, apr.projeto.id),
        "at": lambda: repositorio.obter_at(principal.dono().inquilino_id, at.projeto.id),
    }


# --------------------------------------------------------------------------------------
# O catálogo
# --------------------------------------------------------------------------------------


def test_as_quatro_acoes_do_m4_estao_no_catalogo_e_sao_mutadoras() -> None:
    acoes = {a.action_id: a for a in CATALOGO_TOC.acoes}

    faltando = [a for a in ACOES_DO_M4 if a not in acoes]
    print(f"catálogo: {len(acoes)} ação(ões); do M4: {[a for a in ACOES_DO_M4 if a in acoes]}")
    assert faltando == [], faltando
    for action_id in ACOES_DO_M4:
        acao = acoes[action_id]
        assert acao.risk == "confirm", action_id
        assert acao.requires_confirmation, action_id
        assert acao.capability_exigida == "toc:write", action_id
        assert acao.reversible is True, action_id


def test_sem_capability_de_escrita_as_quatro_do_m4_nao_existem(  ) -> None:
    """RF-45: "o módulo inteiro funcional sem assistência — a assistência é aceleradora"."""
    visiveis = {a.action_id for a in CATALOGO_TOC.compor(SO_LEITURA)}
    print(f"visíveis só com toc:read: {len(visiveis)}; do M4: {visiveis & set(ACOES_DO_M4)}")
    assert visiveis & set(ACOES_DO_M4) == set()
    assert {a.action_id for a in CATALOGO_TOC.compor(PRINCIPAL)} >= set(ACOES_DO_M4)


def test_nao_existe_acao_de_ramo_negativo_no_catalogo() -> None:
    """RF-10/DoD 8: a marcação é manual nesta v1 — a prova é NEGATIVA."""
    suspeitas = [
        a.action_id
        for a in CATALOGO_TOC.acoes
        if "negative" in a.action_id or "ramo" in a.action_id
    ]
    print(f"ações de ramo negativo no catálogo: {suspeitas}")
    assert suspeitas == []


# --------------------------------------------------------------------------------------
# Propor não escreve; aceitar escreve; recusar deixa intacto
# --------------------------------------------------------------------------------------


@pytest.mark.parametrize("action_id", ACOES_DO_M4)
def test_propor_nao_escreve_nada_e_a_proposta_espera_o_gate(action_id: str) -> None:
    pecas = montar()
    argumentos = {
        "toc.suggest_future_effects": {
            "projeto_id": str(pecas["arf_id"]),
            "injecao_id": str(pecas["injecao_id"]),
            "texto": "as duas frentes recebem verba no trimestre",
        },
        "toc.suggest_obstacles": {"projeto_id": str(pecas["apr_id"]), "texto": OBSTACULO},
        "toc.suggest_intermediate_objectives": {
            "projeto_id": str(pecas["apr_id"]),
            "obstaculo_id": str(pecas["obstaculo_id"]),
            "texto": "Existem três pessoas treinadas e escaladas",
        },
        "toc.suggest_transition_steps": {
            "projeto_id": str(pecas["at_id"]),
            "acao": "publicar a chamada interna de treinamento",
            "necessidade": "não há hoje candidato mapeado",
            "resultado_esperado": "lista de inscritos até sexta",
        },
    }[action_id]
    alvo = {"toc.suggest_future_effects": "arf", "toc.suggest_obstacles": "apr",
            "toc.suggest_intermediate_objectives": "apr",
            "toc.suggest_transition_steps": "at"}[action_id]
    antes = instantaneo(pecas[alvo]())

    resultado = pecas["propor"].rodar(
        principal=PRINCIPAL, action_id=action_id, args=argumentos, origem=Origem.IA
    )

    print(
        f"{action_id}: estado={resultado.proposta.estado} "
        f"eventos={[k for k, _ in resultado.eventos]}"
    )
    assert resultado.proposta.estado == "awaiting_approval"
    assert [k for k, _ in resultado.eventos] == ["action_proposal"]
    assert instantaneo(pecas[alvo]()) == antes


def test_aceitar_cria_o_efeito_futuro_LIGADO_a_injecao() -> None:
    """INT-05: a sugestão nunca fica solta — ela nasce ligada à injeção indicada."""
    pecas = montar()
    proposta = pecas["propor"].rodar(
        principal=PRINCIPAL,
        action_id="toc.suggest_future_effects",
        args={
            "projeto_id": str(pecas["arf_id"]),
            "injecao_id": str(pecas["injecao_id"]),
            "texto": "as duas frentes recebem verba no trimestre",
        },
    ).proposta

    pecas["decidir"].rodar(
        principal=PRINCIPAL, proposal_id=proposta.proposal_id, aprovado=True
    )

    arf = pecas["arf"]()
    print(
        f"ARF depois do aceite: {len(arf.nos)} nó(s), {len(arf.arestas)} aresta(s); "
        f"papéis={[arf.papel_do_no(n.id).value for n in arf.nos]}"
    )
    assert len(arf.efeitos_futuros) == 1
    assert len(arf.arestas) == 1
    assert arf.arestas[0].origem_id == pecas["injecao_id"]


def test_aceitar_cria_o_objetivo_intermediario_JA_pareado_e_sem_julgamento() -> None:
    """INT-07: o par vem pré-preenchido; o julgamento **não** — ele é humano (RN-07)."""
    pecas = montar()
    proposta = pecas["propor"].rodar(
        principal=PRINCIPAL,
        action_id="toc.suggest_intermediate_objectives",
        args={
            "projeto_id": str(pecas["apr_id"]),
            "obstaculo_id": str(pecas["obstaculo_id"]),
            "texto": "Existem três pessoas treinadas e escaladas",
        },
    ).proposta

    pecas["decidir"].rodar(
        principal=PRINCIPAL, proposal_id=proposta.proposal_id, aprovado=True
    )

    apr = pecas["apr"]()
    par = apr.pares()[0]
    print(f"par criado: obstáculo={par.obstaculo_id} · julgamentos={len(par.julgamentos)}")
    assert par.obstaculo_id == pecas["obstaculo_id"]
    assert par.julgamentos == (), "o julgamento do teste de validade é humano (RN-07)"


def test_recusar_deixa_a_arvore_byte_a_byte_intacta_e_deixa_traco() -> None:
    pecas = montar()
    antes = instantaneo(pecas["apr"]())
    proposta = pecas["propor"].rodar(
        principal=PRINCIPAL,
        action_id="toc.suggest_obstacles",
        args={"projeto_id": str(pecas["apr_id"]), "texto": "A fila tem trinta pessoas"},
    ).proposta

    pecas["decidir"].rodar(
        principal=PRINCIPAL, proposal_id=proposta.proposal_id, aprovado=False
    )

    depois = instantaneo(pecas["apr"]())
    tracos = pecas["tracos"].linhas
    print(f"iguais byte a byte: {antes == depois} · traços: {[t.desfecho for t in tracos]}")
    assert depois == antes
    assert [t.desfecho for t in tracos] == ["denied"]


def test_a_tripla_incompleta_e_recusada_ANTES_de_a_proposta_existir() -> None:
    """INT-08: "proposta sem os três campos é recusada pela validação de schema"."""
    pecas = montar()
    antes = instantaneo(pecas["at"]())

    with pytest.raises(ArgumentosInvalidos):
        pecas["propor"].rodar(
            principal=PRINCIPAL,
            action_id="toc.suggest_transition_steps",
            args={
                "projeto_id": str(pecas["at_id"]),
                "acao": "publicar a chamada interna",
                "resultado_esperado": "lista de inscritos até sexta",
            },
        )

    tracos = pecas["tracos"].linhas
    print(f"traços da recusa: {[(t.desfecho, t.motivo[:40]) for t in tracos]}")
    assert instantaneo(pecas["at"]()) == antes
    # APH-5.5: a recusa também deixa traço — o que a IA tentou fazer não some.
    assert [t.desfecho for t in tracos] == ["denied"]


def test_o_passo_aceito_nasce_com_a_tripla_inteira() -> None:
    pecas = montar()
    proposta = pecas["propor"].rodar(
        principal=PRINCIPAL,
        action_id="toc.suggest_transition_steps",
        args={
            "projeto_id": str(pecas["at_id"]),
            "acao": "publicar a chamada interna de treinamento",
            "necessidade": "não há hoje candidato mapeado",
            "resultado_esperado": "lista de inscritos até sexta",
        },
    ).proposta

    pecas["decidir"].rodar(
        principal=PRINCIPAL, proposal_id=proposta.proposal_id, aprovado=True
    )

    at = pecas["at"]()
    no_id, ficha = at.fichas()[0]
    print(f"passo criado: {ficha.leitura()}")
    assert ficha.necessidade == "não há hoje candidato mapeado"
    assert ficha.resultado_esperado == "lista de inscritos até sexta"


def test_o_principal_so_leitura_nao_alcanca_as_quatro_e_a_recusa_deixa_traco() -> None:
    pecas = montar()
    with pytest.raises(AcaoDesconhecida):
        pecas["propor"].rodar(
            principal=SO_LEITURA,
            action_id="toc.suggest_obstacles",
            args={"projeto_id": str(pecas["apr_id"]), "texto": OBSTACULO},
        )
    tracos = pecas["tracos"].linhas
    print(f"traço da recusa por permissão: {[(t.desfecho, t.action_id) for t in tracos]}")
    assert [t.desfecho for t in tracos] == ["denied"]


def test_sem_repositorio_de_arvores_a_acao_falha_alto_e_nao_finge() -> None:
    """A ausência de composição é desfecho declarado, nunca `AttributeError` disfarçado."""
    executor = ExecutorDoCatalogo(
        rastreador=RastreadorFalso(),
        projetos=RepositorioDoM4Falso(),
        aras=None,
        relogio=RelogioFalso(instante=AGORA),
    )
    status, mensagem = executor.executar(
        action_id="toc.suggest_obstacles",
        args={"projeto_id": str(uuid4()), "texto": OBSTACULO, "__proposta__": "prop-1"},
        principal=PRINCIPAL,
    )
    print(f"{status}: {mensagem}")
    assert status == "failed"
    assert "não composto" in mensagem


def test_aplicar_conteudo_de_modelo_sem_proposta_e_falha_fechada() -> None:
    """RN-11: conteúdo assistido sem identificador de proposta não entra — nem meio."""
    pecas = montar()
    executor = ExecutorDoCatalogo(
        rastreador=RastreadorFalso(),
        projetos=pecas["repositorio"],
        aras=pecas["repositorio"],
        arvores=pecas["repositorio"],
        relogio=RelogioFalso(instante=AGORA),
    )
    antes = instantaneo(pecas["apr"]())

    status, mensagem = executor.executar(
        action_id="toc.suggest_obstacles",
        args={"projeto_id": str(pecas["apr_id"]), "texto": OBSTACULO},
        principal=PRINCIPAL,
    )

    print(f"{status}: {mensagem}")
    assert status == "failed"
    assert instantaneo(pecas["apr"]()) == antes


# --------------------------------------------------------------------------------------
# INT-09 — as cinco telas do módulo no registro (DoD 12)
# --------------------------------------------------------------------------------------


def test_as_cinco_telas_do_m4_estao_no_registro_com_identificador_estavel() -> None:
    """INT-09: `toc.arf_canvas`, `toc.apr_canvas`, `toc.apr_sequencia`, `toc.at_canvas`,
    `toc.cadeia` — a inteligência artificial nunca infere a interface (APH-3.1)."""
    from toc_api.dominio.federacao.telas import REGISTRO_DE_TELAS

    esperadas = {
        "toc.arf_canvas",
        "toc.apr_canvas",
        "toc.apr_sequencia",
        "toc.at_canvas",
        "toc.cadeia",
    }
    declaradas = {t.id for t in REGISTRO_DE_TELAS.telas}
    print(
        f"registro: {len(declaradas)} tela(s); do M4: {sorted(declaradas & esperadas)}"
    )
    assert esperadas <= declaradas
    for tela in REGISTRO_DE_TELAS.telas:
        if tela.id in esperadas:
            assert tela.route.startswith("/toc/"), tela.id
            assert tela.ai_actions, f"{tela.id} sem ai_actions seria item sensível (§B.5.3)"


def test_o_campo_sensivel_das_telas_do_m4_e_omitido_do_snapshot() -> None:
    """A justificativa de um ramo aceito e o rascunho de julgamento não vão ao modelo."""
    from toc_api.dominio.federacao.telas import REGISTRO_DE_TELAS

    invisiveis = {
        (tela.id, campo.name)
        for tela in REGISTRO_DE_TELAS.telas
        for campo in tela.campos
        if not campo.ai_visible
    }
    print(f"campos declarados invisíveis à IA: {sorted(invisiveis)}")
    assert ("toc.arf_canvas", "justificativa_do_aceite") in invisiveis
    assert ("toc.apr_canvas", "rascunho_de_julgamento") in invisiveis
