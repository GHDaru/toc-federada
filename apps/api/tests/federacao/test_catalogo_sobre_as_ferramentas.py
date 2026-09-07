"""A regressão que o NOSSO conserto criou: o catálogo federado ficou sem ferramenta.

Siglas, uma vez neste arquivo: **APH** — Aplicação ↔ Harness · **ARA** — Árvore da
Realidade Atual · **NC** — Nuvem de Conflito · **ARF** — Árvore da Realidade Futura ·
**APR** — Árvore de Pré-Requisitos · **AT** — Árvore de Transição · **S&T** — Estratégia
& Táticas · **UDE** — Efeito Indesejável · **IA** — inteligência artificial · **FSM** —
máquina de estados finitos · **M1** — Núcleo de Diagramas Lógicos · **RF/RN** — requisito
funcional / regra de negócio.

── O defeito ────────────────────────────────────────────────────────────────────────────

Fechar a porta dos fundos do agregado (`Projeto._exigir_raiz`) foi certo. O que ficou
errado foi o outro lado: as quatro ações mutadoras do catálogo — `toc.criar_nos`,
`toc.criar_arestas`, `toc.atualizar_no`, `toc.excluir_nos` — continuaram apontando para os
casos de uso **genéricos** do M1, anunciando `ui_route: /toc/ara`. Como a guarda recusa
comando genérico em toda ferramenta com raiz, elas passaram a falhar **para sempre** em
ara, nc, arf, apr, at e focalização.

O efeito, medido pelo crítico: criar uma ARA, propor `toc.criar_nos` com dois alvos,
aprovar no gate humano — e o desfecho voltar `failed`. A assistência da fundação, que é o
motivo de a aplicação ser federada, não conseguia tocar em NENHUMA ferramenta do produto.

── O que este arquivo prova ─────────────────────────────────────────────────────────────

1. **Cada ferramenta com raiz tem ao menos uma ação mutadora que EXECUTA** — proposta
   aprovada no gate, desfecho `executed`, e o agregado mudou de verdade (o teste lê o
   repositório depois). É a reprodução do achado, ferramenta por ferramenta.
2. **A guarda da raiz continua fechada** — a rota genérica recusa em TODAS as sete
   ferramentas, não só na nuvem que o primeiro crítico usou. As duas coisas ao mesmo
   tempo: trocar um defeito por outro não é conserto.
3. **S&T é ausência declarada, não esquecimento** — a spec 010 (INT-04) diz que nenhuma
   ação `toc.*` nasce naquele ciclo. O teste afirma a ausência para ela não virar dívida
   silenciosa.
"""
from __future__ import annotations

import json
from datetime import timedelta
from uuid import uuid4

import pytest

from toc_api.aplicacao.federacao.acoes import DecidirProposta, ProporAcao
from toc_api.aplicacao.politica import PoliticaPorCapability
from toc_api.dominio.apr import FERRAMENTA_APR, novo_projeto_apr
from toc_api.dominio.ara import FERRAMENTA_ARA, novo_projeto_ara
from toc_api.dominio.arf import FERRAMENTA_ARF, novo_projeto_arf
from toc_api.dominio.at import FERRAMENTA_AT, novo_projeto_at
from toc_api.dominio.federacao.catalogo import CATALOGO_TOC
from toc_api.dominio.federacao.principal import principal_de_introspeccao
from toc_api.dominio.federacao.proposta import Origem
from toc_api.dominio.focalizacao import (
    FERRAMENTA_FOCALIZACAO,
    SistemaAnalisado,
    nova_analise_de_focalizacao,
)
from toc_api.dominio.nuvem import FERRAMENTA_NC, novo_projeto_nc
from toc_api.dominio.projeto import RAIZ_POR_FERRAMENTA
from toc_api.dominio.snt import FERRAMENTA_SNT, nova_arvore_snt
from toc_api.infra.federacao.executor import ExecutorDoCatalogo

from ..aplicacao.fakes import RastreadorFalso, RelogioFalso
from ..aplicacao.fakes_portabilidade import RepositorioDaPortabilidadeFalso
from ..dominio.nuvem_sintetica import AGORA
from .fakes import (
    IdentificadoresFalsos,
    RelogioFixo,
    RepositorioDePropostasFalso,
    RepositorioDeTracoFalso,
)

#: Persona fictícia (ADR 0006) com o par de capacidades que o catálogo mutador exige.
PRINCIPAL = principal_de_introspeccao(
    {
        "active": True,
        "user": {"id": "u-horizonte-01"},
        "tenant_id": "instituicao-horizonte",
        "capabilities": ["toc:read", "toc:write"],
    }
)

#: As quatro ações mutadoras genéricas do M1 — as que o achado nomeia.
ACOES_GENERICAS = ("toc.criar_nos", "toc.criar_arestas", "toc.atualizar_no", "toc.excluir_nos")


def montar():
    """Um projeto de CADA ferramenta com raiz, no mesmo repositório e no mesmo executor."""
    rastreador = RastreadorFalso()
    repositorio = RepositorioDaPortabilidadeFalso()
    dono = PRINCIPAL.dono()

    ara = novo_projeto_ara(id=uuid4(), dono=dono, nome="Evasão no ciclo básico", em=AGORA)
    efeito = ara.adicionar_efeito(titulo="A evasão aumenta a cada semestre.", em=AGORA)
    repositorio.salvar_ara(ara)

    nuvem = novo_projeto_nc(id=uuid4(), dono=dono, nome="Dilema da expansão", em=AGORA)
    repositorio.salvar_nuvem(nuvem)

    arf = novo_projeto_arf(id=uuid4(), dono=dono, nome="Futuro da expansão", em=AGORA)
    injecao = arf.adicionar_injecao(titulo="faseamento orçamentário", em=AGORA)
    repositorio.salvar_arf(arf)

    apr = novo_projeto_apr(
        id=uuid4(), dono=dono, nome="Implantação",
        objetivo="O faseamento está implantado nas duas frentes", em=AGORA,
    )
    obstaculo = apr.adicionar_obstaculo(
        titulo="Há apenas uma pessoa treinada no acompanhamento", em=AGORA
    )
    repositorio.salvar_apr(apr)

    at = novo_projeto_at(id=uuid4(), dono=dono, nome="Transição", em=AGORA)
    repositorio.salvar_at(at)

    snt = nova_arvore_snt(
        id=uuid4(), dono=dono, nome="Estratégia da expansão",
        meta_global="Crescer sem perder qualidade", em=AGORA,
    )
    repositorio.salvar_snt(snt)

    analise = nova_analise_de_focalizacao(
        id=uuid4(), dono=dono, nome="Focalização do ciclo básico",
        sistema=SistemaAnalisado(nome="Oferta do ciclo básico"), em=AGORA,
    )
    repositorio.salvar_focalizacao(analise)

    executor = ExecutorDoCatalogo(
        rastreador=rastreador,
        projetos=repositorio,
        aras=repositorio,
        nuvens=repositorio,
        arvores=repositorio,
        focalizacoes=repositorio,
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
        "executor": executor,
        "repositorio": repositorio,
        "propor": ProporAcao(**comum),
        "decidir": DecidirProposta(**comum),
        "ara": ara, "efeito": efeito,
        "nuvem": nuvem,
        "arf": arf, "injecao": injecao,
        "apr": apr, "obstaculo": obstaculo,
        "at": at,
        "snt": snt,
        "analise": analise,
    }


def caso_por_ferramenta(pecas) -> dict[str, tuple[str, dict]]:
    """Para cada ferramenta com raiz: a ação mutadora do catálogo e os argumentos dela.

    Uma linha por ferramenta é o ponto do teste — a linha que falta é uma ferramenta em
    que a assistência da fundação não consegue escrever, e é exatamente isso que o achado
    reporta sobre a ARA.
    """
    ara = pecas["ara"]
    return {
        FERRAMENTA_ARA: (
            "toc.suggest_udes",
            {
                "projeto_id": str(ara.projeto.id),
                "udes": [
                    {"texto": "A evasão no primeiro semestre aumenta a cada entrada."},
                    {"texto": "A taxa de reprovação em cálculo cresce todo ano."},
                ],
            },
        ),
        FERRAMENTA_NC: (
            "toc.suggest_assumptions",
            {
                "projeto_id": str(pecas["nuvem"].projeto.id),
                "aresta": "A_B",
                "texto": "Crescer exige atender mais turmas com a mesma equipe.",
            },
        ),
        FERRAMENTA_ARF: (
            "toc.suggest_future_effects",
            {
                "projeto_id": str(pecas["arf"].projeto.id),
                "injecao_id": str(pecas["injecao"].id),
                "texto": "As duas frentes recebem verba no trimestre.",
            },
        ),
        FERRAMENTA_APR: (
            "toc.suggest_obstacles",
            {
                "projeto_id": str(pecas["apr"].projeto.id),
                "texto": "Não há hoje sala disponível no turno da noite",
            },
        ),
        FERRAMENTA_AT: (
            "toc.suggest_transition_steps",
            {
                "projeto_id": str(pecas["at"].projeto.id),
                "acao": "publicar a chamada interna de treinamento",
                "necessidade": "não há hoje candidato mapeado",
                "resultado_esperado": "lista de inscritos até sexta",
            },
        ),
        FERRAMENTA_FOCALIZACAO: (
            "toc.suggest_constraint",
            {
                "projeto_id": str(pecas["analise"].projeto.id),
                "ara_projeto_id": str(ara.projeto.id),
                "no_id": str(pecas["efeito"].id),
                "descricao": "A oferta de laboratório limita as turmas do ciclo básico",
                "tipo": "fisica",
                "justificativa": "É o nó com mais efeitos a jusante na árvore",
            },
        ),
    }


# --------------------------------------------------------------------------------------
# 1. Cada ferramenta com raiz tem uma ação mutadora que EXECUTA (a reprodução do achado)
# --------------------------------------------------------------------------------------


FERRAMENTAS_COM_RAIZ = (
    FERRAMENTA_ARA, FERRAMENTA_NC, FERRAMENTA_ARF,
    FERRAMENTA_APR, FERRAMENTA_AT, FERRAMENTA_FOCALIZACAO,
)


@pytest.mark.parametrize("ferramenta", FERRAMENTAS_COM_RAIZ)
def test_a_assistencia_da_fundacao_escreve_em_cada_ferramenta_com_raiz(ferramenta: str) -> None:
    """Proposta aprovada no gate humano sobre CADA ferramenta — desfecho `executed`."""
    pecas = montar()
    action_id, args = caso_por_ferramenta(pecas)[ferramenta]

    proposta = pecas["propor"].rodar(
        principal=PRINCIPAL, action_id=action_id, args=args, origem=Origem.IA
    ).proposta
    assert proposta.estado == "awaiting_approval", (
        f"{action_id} não parou no gate humano: {proposta.estado}"
    )

    decidida = pecas["decidir"].rodar(
        principal=PRINCIPAL, proposal_id=proposta.proposal_id, aprovado=True
    ).proposta

    desfecho = decidida.desfecho
    print(
        f"{ferramenta:12s} {action_id:32s} → {desfecho.status} "
        f"{desfecho.mensagem or [(a, s, m) for a, s, m in desfecho.outcomes]}"
    )
    assert desfecho.status == "executed", (
        f"a ferramenta {ferramenta!r} continua fora do alcance do catálogo federado: "
        f"{desfecho.mensagem or desfecho.outcomes}"
    )


def test_a_ara_ganha_os_dois_udes_que_a_proposta_em_lote_prometeu() -> None:
    """US-07 da spec 006 sobre a ferramenta de verdade: N alvos, uma confirmação."""
    pecas = montar()
    action_id, args = caso_por_ferramenta(pecas)[FERRAMENTA_ARA]
    antes = len(pecas["ara"].nos)

    proposta = pecas["propor"].rodar(
        principal=PRINCIPAL, action_id=action_id, args=args, origem=Origem.IA
    ).proposta
    assert len(proposta.alvos) == 2, proposta.alvos
    pecas["decidir"].rodar(
        principal=PRINCIPAL, proposal_id=proposta.proposal_id, aprovado=True
    )

    ara = pecas["repositorio"].obter_ara(
        PRINCIPAL.dono().inquilino_id, pecas["ara"].projeto.id
    )
    print(f"nós na ARA: {antes} antes, {len(ara.nos)} depois; UDEs marcados: {len(ara.udes)}")
    assert len(ara.nos) == antes + 2
    assert len(ara.udes) == 2, "o UDE sugerido tem de nascer MARCADO como UDE (RF-32)"


def test_a_reformulacao_sugerida_reexecuta_a_validacao_formal_do_ude() -> None:
    """RF-34 da spec 005: aplicar a reformulação REVALIDA — o veredito não fica pendurado.

    É o teste que separa `toc.suggest_reformulation` de `toc.atualizar_no`. A genérica
    chamaria `EditarNo` no núcleo e o texto mudaria com o veredito antigo colado nele; a
    da ferramenta entra pela raiz, e a raiz revalida no mesmo ato.
    """
    pecas = montar()
    projeto_id = str(pecas["ara"].projeto.id)
    # Um enunciado que a validação formal REPROVA (sem verbo causal, sem sujeito claro).
    pecas["decidir"].rodar(
        principal=PRINCIPAL,
        proposal_id=pecas["propor"].rodar(
            principal=PRINCIPAL,
            action_id="toc.suggest_udes",
            args={"projeto_id": projeto_id, "udes": [{"texto": "coisas ruins"}]},
        ).proposta.proposal_id,
        aprovado=True,
    )
    ara = pecas["repositorio"].obter_ara(PRINCIPAL.dono().inquilino_id, pecas["ara"].projeto.id)
    no_id = next(n.id for n in ara.nos if n.titulo == "coisas ruins")
    antes = ara.validacao(no_id)

    proposta = pecas["propor"].rodar(
        principal=PRINCIPAL,
        action_id="toc.suggest_reformulation",
        args={
            "projeto_id": projeto_id,
            "no_id": str(no_id),
            "texto": "A evasão no primeiro semestre aumenta a cada entrada.",
        },
    ).proposta
    desfecho = pecas["decidir"].rodar(
        principal=PRINCIPAL, proposal_id=proposta.proposal_id, aprovado=True
    ).proposta.desfecho

    ara = pecas["repositorio"].obter_ara(PRINCIPAL.dono().inquilino_id, pecas["ara"].projeto.id)
    depois = ara.validacao(no_id)
    print(
        f"toc.suggest_reformulation: {desfecho.status} — "
        f"reprovações antes={len(antes.reprovacoes)} depois={len(depois.reprovacoes)}; "
        f"status={ara.status(no_id).value}"
    )
    assert desfecho.status == "executed", desfecho.mensagem
    assert ara.projeto.no(no_id).titulo == "A evasão no primeiro semestre aumenta a cada entrada."
    assert depois is not antes, "a validação formal NÃO foi reexecutada sobre o texto novo"
    assert len(depois.reprovacoes) < len(antes.reprovacoes), (
        f"o texto melhorou e o veredito não mudou: {antes.reprovacoes} → {depois.reprovacoes}"
    )


def test_causa_com_no_alvo_inexistente_nao_deixa_no_solto_na_arvore() -> None:
    """Meia mutação é pior que recusa: sem a conferência, a causa ficava e o elo não."""
    pecas = montar()
    antes = len(pecas["ara"].nos)

    proposta = pecas["propor"].rodar(
        principal=PRINCIPAL,
        action_id="toc.suggest_causes",
        args={
            "projeto_id": str(pecas["ara"].projeto.id),
            "no_id": str(uuid4()),
            "causas": [{"texto": "Uma causa para um nó que não existe"}],
        },
    ).proposta
    desfecho = pecas["decidir"].rodar(
        principal=PRINCIPAL, proposal_id=proposta.proposal_id, aprovado=True
    ).proposta.desfecho

    ara = pecas["repositorio"].obter_ara(PRINCIPAL.dono().inquilino_id, pecas["ara"].projeto.id)
    print(
        f"toc.suggest_causes com alvo inexistente: {desfecho.status} "
        f"{[(a, st, m) for a, st, m in desfecho.outcomes]}; nós: {antes} → {len(ara.nos)}"
    )
    assert desfecho.status == "failed"
    assert len(ara.nos) == antes, "sobrou um nó solto: a mutação foi pela metade"
    assert len(ara.arestas) == 0


def test_propor_sobre_a_ara_nao_escreve_nada_antes_do_gate() -> None:
    """P2: verbo mutador nasce proposta. As quatro da ARA também, não só as do M3/M4."""
    pecas = montar()
    projeto_id = str(pecas["ara"].projeto.id)
    antes = len(pecas["ara"].nos)

    for action_id, args in (
        ("toc.suggest_udes", {"projeto_id": projeto_id, "udes": [{"texto": "Um efeito qualquer"}]}),
        (
            "toc.suggest_causes",
            {
                "projeto_id": projeto_id,
                "no_id": str(pecas["efeito"].id),
                "causas": [{"texto": "Uma causa qualquer"}],
            },
        ),
        (
            "toc.suggest_relations",
            {
                "projeto_id": projeto_id,
                "relacoes": [
                    {"origem_id": str(pecas["efeito"].id), "destino_id": str(pecas["efeito"].id)}
                ],
            },
        ),
        (
            "toc.suggest_reformulation",
            {"projeto_id": projeto_id, "no_id": str(pecas["efeito"].id), "texto": "Outro texto"},
        ),
    ):
        resultado = pecas["propor"].rodar(
            principal=PRINCIPAL, action_id=action_id, args=args, origem=Origem.IA
        )
        assert resultado.proposta.estado == "awaiting_approval", action_id
        assert [k for k, _ in resultado.eventos] == ["action_proposal"], action_id

    ara = pecas["repositorio"].obter_ara(PRINCIPAL.dono().inquilino_id, pecas["ara"].projeto.id)
    print(f"nós na ARA depois de quatro propostas NÃO decididas: {len(ara.nos)} (antes: {antes})")
    assert len(ara.nos) == antes
    assert ara.udes == frozenset()


def test_sem_capability_de_escrita_as_quatro_da_ara_nao_existem() -> None:
    """RF-37 da spec 005: ausência, nunca recusa visível (§B.7.3 do Anexo B)."""
    so_leitura = principal_de_introspeccao(
        {
            "active": True,
            "user": {"id": "u-horizonte-02"},
            "tenant_id": "instituicao-horizonte",
            "capabilities": ["toc:read"],
        }
    )
    da_ara = {"toc.suggest_udes", "toc.suggest_causes", "toc.suggest_relations",
              "toc.suggest_reformulation"}

    visiveis = {a.action_id for a in CATALOGO_TOC.compor(so_leitura)}
    print(f"visíveis só com toc:read: {len(visiveis)}; da ARA: {sorted(visiveis & da_ara)}")
    assert visiveis & da_ara == set()
    assert {a.action_id for a in CATALOGO_TOC.compor(PRINCIPAL)} >= da_ara


# --------------------------------------------------------------------------------------
# 2. A guarda da raiz continua fechada — nas SETE ferramentas, não só na nuvem
# --------------------------------------------------------------------------------------


def projetos_de_ferramenta(pecas):
    return {
        FERRAMENTA_ARA: pecas["ara"].projeto,
        FERRAMENTA_NC: pecas["nuvem"].projeto,
        FERRAMENTA_ARF: pecas["arf"].projeto,
        FERRAMENTA_APR: pecas["apr"].projeto,
        FERRAMENTA_AT: pecas["at"].projeto,
        FERRAMENTA_SNT: pecas["snt"].projeto,
        FERRAMENTA_FOCALIZACAO: pecas["analise"].projeto,
    }


@pytest.mark.parametrize("action_id", ACOES_GENERICAS)
def test_a_rota_generica_continua_recusada_em_toda_ferramenta_com_raiz(action_id: str) -> None:
    """O conserto NÃO reabre a porta dos fundos: comando genérico continua sem passar."""
    pecas = montar()
    alvos = projetos_de_ferramenta(pecas)
    assert set(alvos) == set(RAIZ_POR_FERRAMENTA), (
        "uma ferramenta se registrou e este teste não a conhece — a cobertura mentiria"
    )

    desfechos = []
    for ferramenta, projeto in alvos.items():
        no = projeto.nos[0].id if projeto.nos else uuid4()
        args = {
            "toc.criar_nos": {
                "projeto_id": str(projeto.id),
                "nos": [{"titulo": "Entrando por fora da raiz", "tipo": "ude"}],
                "__indice__": 0,
            },
            "toc.criar_arestas": {
                "projeto_id": str(projeto.id),
                "arestas": [{"origem_id": str(no), "destino_id": str(uuid4())}],
                "__indice__": 0,
            },
            "toc.atualizar_no": {
                "projeto_id": str(projeto.id), "no_id": str(no), "titulo": "Texto por fora",
            },
            "toc.excluir_nos": {
                "projeto_id": str(projeto.id), "no_ids": [str(no)], "__indice__": 0,
            },
        }[action_id]
        status, mensagem = pecas["executor"].executar(
            action_id=action_id, args=args, principal=PRINCIPAL
        )
        desfechos.append((ferramenta, status, mensagem))

    print("\n" + "\n".join(f"  {f:12s} {s} — {m}" for f, s, m in desfechos))
    for ferramenta, status, mensagem in desfechos:
        assert status == "failed", (
            f"{action_id} EXECUTOU sobre a ferramenta {ferramenta!r}: a porta dos fundos "
            f"do agregado voltou ({mensagem})"
        )


def test_as_ferramentas_continuam_intactas_depois_das_quatro_tentativas() -> None:
    """Recusa não é meia-mutação: a nuvem sai com as 5 entidades e as 7 arestas."""
    pecas = montar()
    for action_id in ACOES_GENERICAS:
        for projeto in projetos_de_ferramenta(pecas).values():
            no = projeto.nos[0].id if projeto.nos else uuid4()
            args = {
                "toc.criar_nos": {"projeto_id": str(projeto.id),
                                  "nos": [{"titulo": "x", "tipo": "ude"}], "__indice__": 0},
                "toc.criar_arestas": {"projeto_id": str(projeto.id),
                                      "arestas": [{"origem_id": str(no),
                                                   "destino_id": str(uuid4())}],
                                      "__indice__": 0},
                "toc.atualizar_no": {"projeto_id": str(projeto.id), "no_id": str(no),
                                     "titulo": "x"},
                "toc.excluir_nos": {"projeto_id": str(projeto.id), "no_ids": [str(no)],
                                    "__indice__": 0},
            }[action_id]
            pecas["executor"].executar(action_id=action_id, args=args, principal=PRINCIPAL)

    nuvem = pecas["repositorio"].obter_nuvem(
        PRINCIPAL.dono().inquilino_id, pecas["nuvem"].projeto.id
    )
    print(f"nuvem depois de 28 tentativas: {len(nuvem.entidades)} entidades, "
          f"{len(nuvem.arestas)} arestas")
    assert len(nuvem.entidades) == 5
    assert len(nuvem.arestas) == 7


def test_o_catalogo_continua_mutando_o_projeto_generico() -> None:
    """O M1 genérico não perde nada: lá o `Projeto` É a raiz do agregado."""
    from toc_api.dominio.projeto import Projeto

    pecas = montar()
    projeto = Projeto(
        id=uuid4(), dono=PRINCIPAL.dono(), nome="Rascunho livre",
        criado_em=AGORA, alterado_em=AGORA,
    )
    pecas["repositorio"].salvar(projeto)

    status, mensagem = pecas["executor"].executar(
        action_id="toc.criar_nos",
        args={"projeto_id": str(projeto.id),
              "nos": [{"titulo": "A evasão aumenta a cada semestre.", "tipo": "ude"}],
              "__indice__": 0},
        principal=PRINCIPAL,
    )
    print(f"toc.criar_nos sobre projeto genérico: {status} — {mensagem}")
    assert status == "executed"
    assert len(pecas["repositorio"].obter(
        PRINCIPAL.dono().inquilino_id, projeto.id).nos) == 1


# --------------------------------------------------------------------------------------
# 3. S&T: ausência DECLARADA (spec 010, INT-04), não esquecimento
# --------------------------------------------------------------------------------------


def test_a_snt_nao_tem_acao_de_catalogo_e_isso_esta_declarado_na_spec() -> None:
    """`grep -c "toc\\." contracts/ | grep snt` = 0 é a DoD 12 da spec 010."""
    da_snt = [a.action_id for a in CATALOGO_TOC.acoes if "snt" in a.action_id]
    print(f"ações de S&T no catálogo: {da_snt} (spec 010, INT-04: nenhuma nasce naquele ciclo)")
    assert da_snt == []
