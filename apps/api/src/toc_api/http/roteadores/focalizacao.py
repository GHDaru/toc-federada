"""A superfície HTTP do M6 — a jornada dos cinco passos, sob `/toc/focalizacao`.

Siglas, uma vez neste arquivo: **M6** — Focalização · **M1** — Núcleo de Diagramas
Lógicos · **TOC** — Teoria das Restrições · **ARA** — Árvore da Realidade Atual · **NC** —
Nuvem de Conflito · **APR** — Árvore de Pré-Requisitos · **AT** — Árvore de Transição ·
**HTTP** — *HyperText Transfer Protocol* · **RF/RN/RNF** — requisito funcional / regra de
negócio / requisito não funcional.

Cinco decisões desta borda, cada uma fechando uma linha da spec:

1. **Não existe rota que crie, exclua ou reordene passo** (RN-01). A ausência da rota é a
   forma mais barata de garantir a ordem canônica — um teste conta as rotas publicadas e
   reprova qualquer verbo sobre passo que não seja anotar, vincular, concluir ou reabrir.
2. **Editar a restrição não aceita `tipo`** (RN-03). O esquema de entrada é fechado
   (`extra="forbid"`), então trocar o alvo pela rota de edição devolve `422` na borda,
   antes de qualquer caso de uso ser montado. Trocar o alvo é **recomeçar**.
3. **Sugerir não aplica.** `POST …/sugestoes-de-restricao` devolve as candidatas e o
   `action_id` da ação governada; quem escreve é a proposta aceita na máquina de estados
   do servidor (ciclo 006), nunca esta rota. Recusar, portanto, é de graça (RF-19).
4. **O passo e o tipo de restrição chegam como texto e são convertidos AQUI.** Nome errado
   vira `422` com a lista do que era esperado — nunca `KeyError` lá dentro.
5. **A leitura resolve o estado dos vínculos** (RNF-04). A resposta do mapa já traz, por
   vínculo, se o projeto de destino está ativo, arquivado ou ausente — com a legenda que
   a tela mostra. Sem isso, "o vínculo é navegável" seria promessa, e o cartão de um
   projeto apagado seria um botão que leva a lugar nenhum.
"""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, status

from ...aplicacao.focalizacao import (
    AbrirAnaliseDeFocalizacao,
    AnotarPasso,
    ConcluirPasso,
    CriarAnaliseDeFocalizacao,
    EditarRestricao,
    ExcluirAnaliseDeFocalizacao,
    JulgarDecisaoHerdada,
    LinhaDoTempoDaAnalise,
    ListarAnalisesDeFocalizacao,
    MapaDaJornadaDaAnalise,
    ReabrirPassoAnterior,
    Recomecar,
    ReferenciasDaFerramenta,
    RegistrarRestricao,
    RemoverVinculo,
    ResolverVinculos,
    RestaurarAnaliseDeFocalizacao,
    SugerirRestricao,
    VincularFerramenta,
)
from ...dominio.erros import DadoInvalido
from ...dominio.focalizacao import (
    ReferenciaDeOrigemDaRestricao,
    TipoDePasso,
    TipoDeRestricao,
    VereditoDeHeranca,
)
from ..dependencias import ExecutorDependente
from ..esquemas import (
    AnaliseOut,
    AnaliseResumoOut,
    CandidataARestricaoOut,
    CicloNaLinhaOut,
    ConclusaoDePassoIn,
    CriarAnaliseIn,
    EditarRestricaoIn,
    JornadaOut,
    NotaIn,
    ReaberturaIn,
    ReferenciaReversaOut,
    RestricaoIn,
    RestricaoOut,
    SugestaoDeRestricaoOut,
    VeredictoIn,
    VinculoIn,
    VinculoOut,
)

roteador = APIRouter(prefix="/toc/focalizacao", tags=["focalizacao"])

#: O identificador da ação governada que este módulo declara no catálogo `toc.*` (INT-05).
#: A rota de sugestão o devolve ao cliente para que a interface saiba por onde a aplicação
#: passa — e para que ninguém invente um caminho de escrita direto.
ACAO_DE_SUGESTAO = "toc.suggest_constraint"

AVISO_DE_PROPOSTA = (
    "nada foi aplicado: leve a candidata escolhida à ação governada do catálogo, que "
    "nasce action_proposal e espera o gate humano"
)


def _passo(bruto: str) -> TipoDePasso:
    try:
        return TipoDePasso(bruto)
    except ValueError as erro:
        raise DadoInvalido(
            f"passo desconhecido: {bruto!r}; esperado um de "
            f"{[p.value for p in TipoDePasso]}"
        ) from erro


def _tipo_de_restricao(bruto: str) -> TipoDeRestricao:
    try:
        return TipoDeRestricao(bruto)
    except ValueError as erro:  # pragma: no cover - o `Literal` do esquema já recusa
        raise DadoInvalido(
            f"tipo de restrição desconhecido: {bruto!r}; esperado um de "
            f"{[t.value for t in TipoDeRestricao]}"
        ) from erro


def _analise_completa(executor: ExecutorDependente, projeto_id: UUID) -> AnaliseOut:
    """A leitura que a tela consome: agregado + mapa + vínculos resolvidos.

    Três casos de uso e não um, porque três são governados separadamente e cada um tem o
    seu span (P5). Compor aqui é papel da borda; nenhum deles conhece o outro.
    """
    analise = executor.rodar(AbrirAnaliseDeFocalizacao, projeto_id=projeto_id)
    mapa = executor.rodar(MapaDaJornadaDaAnalise, projeto_id=projeto_id)
    resolvidos = executor.rodar(ResolverVinculos, projeto_id=projeto_id)
    return AnaliseOut.de(analise, mapa, resolvidos=resolvidos)


# -- análise ------------------------------------------------------------------------------


@roteador.post("/analises", status_code=status.HTTP_201_CREATED, response_model=AnaliseOut)
def criar_analise(corpo: CriarAnaliseIn, executor: ExecutorDependente) -> AnaliseOut:
    """RF-01/RF-02: uma chamada, a jornada inteira — ciclo aberto e os cinco passos."""
    projeto = executor.rodar(
        CriarAnaliseDeFocalizacao,
        nome=corpo.nome,
        sistema=corpo.sistema,
        descricao_do_sistema=corpo.descricao_do_sistema,
    )
    return _analise_completa(executor, projeto.id)


@roteador.get("/analises", response_model=list[AnaliseResumoOut])
def listar_analises(executor: ExecutorDependente) -> list[AnaliseResumoOut]:
    """RF-03/RI-07: passo atual e restrição vigente como colunas de primeira classe."""
    return [
        AnaliseResumoOut.de(linha)
        for linha in executor.rodar(ListarAnalisesDeFocalizacao)
    ]


@roteador.get("/analises/{projeto_id}", response_model=AnaliseOut)
def abrir_analise(projeto_id: UUID, executor: ExecutorDependente) -> AnaliseOut:
    return _analise_completa(executor, projeto_id)


@roteador.delete("/analises/{projeto_id}", response_model=AnaliseOut)
def excluir_analise(projeto_id: UUID, executor: ExecutorDependente) -> AnaliseOut:
    """RF-04: exclusão SUAVE — ciclos, passos, restrições e vínculos vão juntos e voltam."""
    executor.rodar(ExcluirAnaliseDeFocalizacao, projeto_id=projeto_id)
    return _analise_completa(executor, projeto_id)


@roteador.post("/analises/{projeto_id}/restauracao", response_model=AnaliseOut)
def restaurar_analise(projeto_id: UUID, executor: ExecutorDependente) -> AnaliseOut:
    executor.rodar(RestaurarAnaliseDeFocalizacao, projeto_id=projeto_id)
    return _analise_completa(executor, projeto_id)


# -- o mapa e a linha do tempo -------------------------------------------------------------


@roteador.get("/analises/{projeto_id}/jornada", response_model=JornadaOut)
def jornada(
    projeto_id: UUID, executor: ExecutorDependente, ciclo_id: UUID | None = None
) -> JornadaOut:
    """RF-12: o mapa do ciclo aberto — ou de um ciclo FECHADO, em somente leitura (RF-17)."""
    analise = executor.rodar(AbrirAnaliseDeFocalizacao, projeto_id=projeto_id)
    mapa = executor.rodar(MapaDaJornadaDaAnalise, projeto_id=projeto_id, ciclo_id=ciclo_id)
    resolvidos = executor.rodar(ResolverVinculos, projeto_id=projeto_id)
    return JornadaOut.de(mapa, analise.ciclo(mapa.ciclo_id), resolvidos=resolvidos)


@roteador.get(
    "/analises/{projeto_id}/linha-do-tempo", response_model=list[CicloNaLinhaOut]
)
def linha_do_tempo(
    projeto_id: UUID, executor: ExecutorDependente
) -> list[CicloNaLinhaOut]:
    """RF-17: a história da análise — os ciclos em ordem, com restrição e desfecho."""
    return [
        CicloNaLinhaOut.de(entrada)
        for entrada in executor.rodar(LinhaDoTempoDaAnalise, projeto_id=projeto_id)
    ]


# -- a restrição ---------------------------------------------------------------------------


@roteador.post(
    "/analises/{projeto_id}/restricao",
    status_code=status.HTTP_201_CREATED,
    response_model=RestricaoOut,
)
def registrar_restricao(
    projeto_id: UUID, corpo: RestricaoIn, executor: ExecutorDependente
) -> RestricaoOut:
    """RF-05/RF-06: com ou sem origem — a ferramenta ajuda, nunca condiciona."""
    restricao = executor.rodar(
        RegistrarRestricao,
        projeto_id=projeto_id,
        descricao=corpo.descricao,
        tipo=_tipo_de_restricao(corpo.tipo),
        justificativa=corpo.justificativa,
        autor=corpo.autor,
        origem=None
        if corpo.origem is None
        else ReferenciaDeOrigemDaRestricao(
            ferramenta=corpo.origem.ferramenta,
            projeto_id=corpo.origem.projeto_id,
            no_id=corpo.origem.no_id,
        ),
    )
    return RestricaoOut.de(restricao)


@roteador.put("/analises/{projeto_id}/restricao", response_model=RestricaoOut)
def editar_restricao(
    projeto_id: UUID, corpo: EditarRestricaoIn, executor: ExecutorDependente
) -> RestricaoOut:
    """RF-07: descrição e justificativa. `tipo` no corpo é `422` — trocar alvo é recomeçar."""
    return RestricaoOut.de(
        executor.rodar(
            EditarRestricao,
            projeto_id=projeto_id,
            descricao=corpo.descricao,
            justificativa=corpo.justificativa,
        )
    )


# -- os passos -----------------------------------------------------------------------------


@roteador.post("/analises/{projeto_id}/passos/{passo}/conclusao", response_model=JornadaOut)
def concluir_passo(
    projeto_id: UUID, passo: str, corpo: ConclusaoDePassoIn, executor: ExecutorDependente
) -> JornadaOut:
    """RF-09: o avanço é ato explícito — e a resposta já é o mapa depois dele."""
    executor.rodar(
        ConcluirPasso,
        projeto_id=projeto_id,
        passo=_passo(passo),
        decisao=corpo.decisao,
        autor=corpo.autor,
    )
    return jornada(projeto_id, executor)


@roteador.post("/analises/{projeto_id}/reaberturas", response_model=JornadaOut)
def reabrir_passo_anterior(
    projeto_id: UUID, corpo: ReaberturaIn, executor: ExecutorDependente
) -> JornadaOut:
    """RF-10: reabre o passo imediatamente anterior, **sem apagar** a decisão dele."""
    executor.rodar(
        ReabrirPassoAnterior,
        projeto_id=projeto_id,
        justificativa=corpo.justificativa,
        autor=corpo.autor,
    )
    return jornada(projeto_id, executor)


@roteador.post(
    "/analises/{projeto_id}/passos/{passo}/notas",
    status_code=status.HTTP_201_CREATED,
    response_model=JornadaOut,
)
def anotar_passo(
    projeto_id: UUID, passo: str, corpo: NotaIn, executor: ExecutorDependente
) -> JornadaOut:
    """RF-11: nota acumulável — e anotar NÃO avança a jornada (RN-01)."""
    executor.rodar(
        AnotarPasso,
        projeto_id=projeto_id,
        passo=_passo(passo),
        texto=corpo.texto,
        autor=corpo.autor,
    )
    return jornada(projeto_id, executor)


# -- os vínculos de ferramenta ---------------------------------------------------------------


@roteador.post(
    "/analises/{projeto_id}/passos/{passo}/vinculos",
    status_code=status.HTTP_201_CREATED,
    response_model=VinculoOut,
)
def vincular_ferramenta(
    projeto_id: UUID, passo: str, corpo: VinculoIn, executor: ExecutorDependente
) -> VinculoOut:
    """RF-14 + RNF-04: existência, inquilino, ferramenta e estado conferidos no servidor."""
    vinculo = executor.rodar(
        VincularFerramenta,
        projeto_id=projeto_id,
        passo=_passo(passo),
        tipo=corpo.ferramenta,
        alvo_id=corpo.projeto_id,
        papel=corpo.papel,
        justificativa=corpo.justificativa,
    )
    resolvidos = {r.vinculo_id: r for r in executor.rodar(ResolverVinculos, projeto_id=projeto_id)}
    return VinculoOut.de(vinculo, resolvidos.get(vinculo.id))


@roteador.delete(
    "/analises/{projeto_id}/passos/{passo}/vinculos/{vinculo_id}",
    response_model=JornadaOut,
)
def remover_vinculo(
    projeto_id: UUID, passo: str, vinculo_id: UUID, executor: ExecutorDependente
) -> JornadaOut:
    executor.rodar(
        RemoverVinculo, projeto_id=projeto_id, passo=_passo(passo), vinculo_id=vinculo_id
    )
    return jornada(projeto_id, executor)


@roteador.get("/ferramentas/{alvo_id}/analises", response_model=list[ReferenciaReversaOut])
def analises_que_citam(
    alvo_id: UUID, executor: ExecutorDependente
) -> list[ReferenciaReversaOut]:
    """L-03: a navegação de volta — sem campo novo em M2, M3 ou M4.

    Quem quiser, de dentro de uma Árvore da Realidade Atual, saber que jornadas a citam,
    pergunta AQUI. A alternativa seria um campo na ARA apontando para a análise, e o
    acoplamento reverso obrigaria o M2 a saber que o M6 existe.
    """
    return [
        ReferenciaReversaOut(
            analise_id=projeto.id,
            analise_nome=projeto.nome,
            passo=passo.value,
            vinculo=VinculoOut.de(vinculo),
        )
        for projeto, passo, vinculo in executor.rodar(
            ReferenciasDaFerramenta, alvo_id=alvo_id
        )
    ]


# -- a herança e o recomeço ------------------------------------------------------------------


@roteador.post(
    "/analises/{projeto_id}/heranca/{decisao_id}/veredito", response_model=JornadaOut
)
def julgar_heranca(
    projeto_id: UUID, decisao_id: UUID, corpo: VeredictoIn, executor: ExecutorDependente
) -> JornadaOut:
    """RN-05: `mantida` e `revogada` têm o mesmo peso — e as duas exigem justificativa.

    O `Literal` do esquema de entrada não aceita `pendente`: voltar a pendente apagaria um
    julgamento, e histórico é apêndice (RN-04). A recusa acontece na borda **e** no
    domínio; nenhuma das duas basta sozinha, porque o fio conversacional não passa por
    aqui.
    """
    executor.rodar(
        JulgarDecisaoHerdada,
        projeto_id=projeto_id,
        decisao_id=decisao_id,
        veredito=VereditoDeHeranca(corpo.veredito),
        justificativa=corpo.justificativa,
        autor=corpo.autor,
    )
    return jornada(projeto_id, executor)


@roteador.post(
    "/analises/{projeto_id}/recomecos",
    status_code=status.HTTP_201_CREATED,
    response_model=AnaliseOut,
)
def recomecar(projeto_id: UUID, executor: ExecutorDependente) -> AnaliseOut:
    """RF-15/RF-16: fecha o ciclo, abre o próximo e herda o que pode virar inércia."""
    executor.rodar(Recomecar, projeto_id=projeto_id)
    return _analise_completa(executor, projeto_id)


# -- a assistência: sugerir NÃO aplica (RF-19) -------------------------------------------------


@roteador.post(
    "/analises/{projeto_id}/sugestoes-de-restricao", response_model=SugestaoDeRestricaoOut
)
def sugerir_restricao(
    projeto_id: UUID, executor: ExecutorDependente, ara_projeto_id: UUID | None = None
) -> SugestaoDeRestricaoOut:
    """RF-19: candidatas + o `action_id`. **Esta rota não escreve nada.**

    Quem escreve é a proposta aceita na máquina de estados do ciclo 006 — e é por isso que
    recusar é de graça: nada foi tocado. Sem ARA vinculada ao passo `identificar`, a lista
    volta vazia e a jornada segue: a sugestão é aceleradora, nunca dependência (RF-20).
    """
    candidatas = executor.rodar(
        SugerirRestricao, projeto_id=projeto_id, ara_projeto_id=ara_projeto_id
    )
    analise = executor.rodar(AbrirAnaliseDeFocalizacao, projeto_id=projeto_id)
    alvo = ara_projeto_id or SugerirRestricao._ara_do_passo_identificar(analise)
    return SugestaoDeRestricaoOut(
        ara_projeto_id=alvo or projeto_id,
        action_id=ACAO_DE_SUGESTAO,
        aviso=AVISO_DE_PROPOSTA,
        candidatas=[
            CandidataARestricaoOut(
                no_id=c.no_id,
                titulo=c.titulo,
                racional=c.racional,
                udes_alcancados=c.udes_alcancados,
                fracao=c.fracao,
            )
            for c in candidatas
        ],
    )
