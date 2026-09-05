"""A superfície HTTP da Nuvem de Conflito (NC) — M3, spec 007, sob `/toc/nc`.

Siglas, uma vez: **NC** — Nuvem de Conflito · **ARA** — Árvore da Realidade Atual ·
**UDE** — Efeito Indesejável · **TOC** — Teoria das Restrições · **TRIZ** — Teoria da
Resolução Inventiva de Problemas · **HTTP** — *HyperText Transfer Protocol* · **FSM** —
máquina de estados finitos.

Quatro decisões desta borda, cada uma fechando um defeito nomeado da 4ª geração:

1. **Não existe rota que crie ou exclua entidade ou aresta** (RF-03). A topologia é fixa
   (RN-01) e a ausência da rota é a forma mais barata de garanti-la — um teste conta as
   rotas publicadas e reprova qualquer `POST`/`DELETE` sobre entidade ou aresta.
2. **Gerar não aplica.** `POST …/geracoes` devolve a pré-visualização estruturada e o
   `action_id` da ação governada; quem escreve é a proposta aceita na FSM do servidor
   (ciclo 006), nunca esta rota. Recusar, portanto, é de graça — nada foi tocado (RF-24).
3. **A derivação a partir da ARA é rota própria** (`POST /toc/nc/derivacoes`, INT-05): o
   dono e o inquilino saem do agregado de origem, e o cliente não os informa.
4. **O papel e a chave da aresta chegam como texto e são convertidos AQUI.** Nome errado
   vira `422` na borda, com a lista do que era esperado — nunca `KeyError` lá dentro.
"""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, status

from ...aplicacao.nuvem import (
    AbrirProjetoNC,
    ArquivarPremissa,
    ClassificarInjecao,
    CriarProjetoNC,
    DerivarNuvemDeUdes,
    DesafiarPremissa,
    EditarEntidadeDaNuvem,
    EditarInjecao,
    EditarPremissa,
    EditarRacionalDaNuvem,
    GerarNuvemPorNarrativa,
    MudarStatusDeInjecao,
    RegistrarInjecao,
    RegistrarPremissa,
    ReordenarPremissas,
    RevigorarPremissa,
    SugerirInjecoes,
    SugerirPremissas,
    ValidarNuvem,
)
from ...dominio.erros import DadoInvalido
from ...dominio.nuvem import (
    ChaveDaAresta,
    EstadoDaPremissa,
    PapelDaEntidade,
    SeparacaoTRIZ,
    StatusDeInjecao,
)
from ..dependencias import ExecutorDependente
from ..esquemas import (
    ArquivamentoOut,
    CriarProjetoIn,
    DerivacaoIn,
    EstadoDaPremissaIn,
    GeracaoOut,
    InjecaoIn,
    InjecaoOut,
    MatrizOut,
    NarrativaIn,
    NuvemOut,
    OrdemDePremissasIn,
    PremissaIn,
    PremissaOut,
    RacionalIn,
    SeparacaoIn,
    SolucaoOut,
    StatusDeInjecaoIn,
    SugestaoDeInjecaoOut,
    SugestaoDePremissaOut,
    SugestoesDeInjecaoOut,
    SugestoesDePremissaOut,
    TextoDaEntidadeIn,
    TextoDaInjecaoIn,
    ValidacaoDaNuvemOut,
)

roteador = APIRouter(prefix="/toc/nc", tags=["nuvem-de-conflito"])

#: Os identificadores das ações governadas que este módulo declara no catálogo `toc.*`
#: (INT-02..INT-04). A rota de geração os devolve ao cliente para que a interface saiba
#: por onde a aplicação passa — e para que ninguém invente um caminho de escrita direto.
ACAO_DE_GERACAO = "toc.generate_conflict_cloud"
ACAO_DE_PREMISSAS = "toc.suggest_assumptions"
ACAO_DE_INJECOES = "toc.suggest_injections"

AVISO_DE_PROPOSTA = (
    "nada foi aplicado: leve este resultado à ação governada do catálogo, que nasce "
    "action_proposal e espera o gate humano"
)


def _papel(bruto: str) -> PapelDaEntidade:
    try:
        return PapelDaEntidade(bruto)
    except ValueError as erro:
        raise DadoInvalido(
            f"papel desconhecido: {bruto!r}; esperado um de "
            f"{[p.value for p in PapelDaEntidade]}"
        ) from erro


def _chave(bruto: str) -> ChaveDaAresta:
    try:
        return ChaveDaAresta(bruto)
    except ValueError as erro:
        raise DadoInvalido(
            f"chave de aresta desconhecida: {bruto!r}; esperado uma de "
            f"{[c.value for c in ChaveDaAresta]}"
        ) from erro


def _separacao(bruto: str | None) -> SeparacaoTRIZ | None:
    if bruto is None:
        return None
    try:
        return SeparacaoTRIZ(bruto)
    except ValueError as erro:
        raise DadoInvalido(
            f"separação TRIZ desconhecida: {bruto!r}; esperado uma de "
            f"{[s.value for s in SeparacaoTRIZ]}"
        ) from erro


def _premissa_com_injecoes(executor: ExecutorDependente, projeto_id: UUID, premissa_id: UUID):
    nuvem = executor.rodar(AbrirProjetoNC, projeto_id=projeto_id)
    return PremissaOut.de(
        nuvem.premissa(premissa_id), nuvem.injecoes_da_premissa(premissa_id)
    )


# -- projeto ----------------------------------------------------------------------------


@roteador.post("/projetos", status_code=status.HTTP_201_CREATED, response_model=NuvemOut)
def criar_projeto_nc(corpo: CriarProjetoIn, executor: ExecutorDependente) -> NuvemOut:
    """RF-02: uma chamada, a nuvem inteira — 5 entidades, 7 arestas, racional vazio."""
    projeto = executor.rodar(
        CriarProjetoNC,
        nome=corpo.nome,
        descricao_do_problema=corpo.descricao_do_problema,
    )
    return NuvemOut.de(executor.rodar(AbrirProjetoNC, projeto_id=projeto.id))


@roteador.post("/derivacoes", status_code=status.HTTP_201_CREATED, response_model=NuvemOut)
def derivar_de_udes(corpo: DerivacaoIn, executor: ExecutorDependente) -> NuvemOut:
    """INT-05 — o encadeamento: os UDEs da ARA viram o ponto de partida do dilema.

    O inquilino e o dono da nuvem nova vêm da ARA de origem, nunca do corpo do pedido; um
    projeto de outro inquilino é indistinguível de inexistente, como em todo o M1.
    """
    nuvem = executor.rodar(
        DerivarNuvemDeUdes,
        projeto_id=corpo.ara_projeto_id,
        no_ids=tuple(corpo.no_ids),
        nome=corpo.nome,
    )
    return NuvemOut.de(nuvem)


@roteador.get("/projetos/{projeto_id}", response_model=NuvemOut)
def abrir_nuvem(projeto_id: UUID, executor: ExecutorDependente) -> NuvemOut:
    """A leitura inteira: entidades com aviso, arestas com leitura, premissas e injeções."""
    return NuvemOut.de(executor.rodar(AbrirProjetoNC, projeto_id=projeto_id))


@roteador.get("/projetos/{projeto_id}/validacao", response_model=ValidacaoDaNuvemOut)
def validar(projeto_id: UUID, executor: ExecutorDependente) -> ValidacaoDaNuvemOut:
    """RF-14: completude, avisos e pendências. Leitura pura — não grava evento nenhum."""
    return ValidacaoDaNuvemOut.de(executor.rodar(ValidarNuvem, projeto_id=projeto_id))


@roteador.get("/projetos/{projeto_id}/solucao", response_model=SolucaoOut)
def visao_de_solucao(projeto_id: UUID, executor: ExecutorDependente) -> SolucaoOut:
    """RF-31: as SETE posições, incluindo D⇸C e D↯D′ — as que o v3 nunca renderizou."""
    return SolucaoOut.de(executor.rodar(AbrirProjetoNC, projeto_id=projeto_id))


@roteador.get("/projetos/{projeto_id}/matriz", response_model=MatrizOut)
def matriz(projeto_id: UUID, executor: ExecutorDependente) -> MatrizOut:
    """RF-34: aresta × premissas × injeções — a vista tabular do mesmo dado."""
    return MatrizOut.de(executor.rodar(AbrirProjetoNC, projeto_id=projeto_id))


# -- entidades e racional ---------------------------------------------------------------


@roteador.put("/projetos/{projeto_id}/entidades/{papel}", response_model=NuvemOut)
def editar_entidade(
    projeto_id: UUID, papel: str, corpo: TextoDaEntidadeIn, executor: ExecutorDependente
) -> NuvemOut:
    """RF-05: edita o texto de UMA entidade. Criar e excluir não existem (RF-03)."""
    executor.rodar(
        EditarEntidadeDaNuvem,
        projeto_id=projeto_id,
        papel=_papel(papel),
        texto=corpo.texto,
    )
    return NuvemOut.de(executor.rodar(AbrirProjetoNC, projeto_id=projeto_id))


@roteador.put("/projetos/{projeto_id}/racional", response_model=NuvemOut)
def editar_racional(
    projeto_id: UUID, corpo: RacionalIn, executor: ExecutorDependente
) -> NuvemOut:
    executor.rodar(
        EditarRacionalDaNuvem, projeto_id=projeto_id, racional=corpo.racional
    )
    return NuvemOut.de(executor.rodar(AbrirProjetoNC, projeto_id=projeto_id))


# -- premissas ---------------------------------------------------------------------------


@roteador.post(
    "/projetos/{projeto_id}/arestas/{chave}/premissas",
    status_code=status.HTTP_201_CREATED,
    response_model=PremissaOut,
)
def registrar_premissa(
    projeto_id: UUID, chave: str, corpo: PremissaIn, executor: ExecutorDependente
) -> PremissaOut:
    premissa = executor.rodar(
        RegistrarPremissa, projeto_id=projeto_id, chave=_chave(chave), texto=corpo.texto
    )
    return PremissaOut.de(premissa, ())


@roteador.put("/projetos/{projeto_id}/premissas/{premissa_id}", response_model=PremissaOut)
def editar_premissa(
    projeto_id: UUID, premissa_id: UUID, corpo: PremissaIn, executor: ExecutorDependente
) -> PremissaOut:
    executor.rodar(
        EditarPremissa, projeto_id=projeto_id, premissa_id=premissa_id, texto=corpo.texto
    )
    return _premissa_com_injecoes(executor, projeto_id, premissa_id)


@roteador.put(
    "/projetos/{projeto_id}/arestas/{chave}/premissas/ordem",
    response_model=list[PremissaOut],
)
def reordenar_premissas(
    projeto_id: UUID, chave: str, corpo: OrdemDePremissasIn, executor: ExecutorDependente
) -> list[PremissaOut]:
    premissas = executor.rodar(
        ReordenarPremissas,
        projeto_id=projeto_id,
        chave=_chave(chave),
        ordem=tuple(corpo.ordem),
    )
    nuvem = executor.rodar(AbrirProjetoNC, projeto_id=projeto_id)
    return [PremissaOut.de(p, nuvem.injecoes_da_premissa(p.id)) for p in premissas]


@roteador.put(
    "/projetos/{projeto_id}/premissas/{premissa_id}/estado", response_model=PremissaOut
)
def mudar_estado_da_premissa(
    projeto_id: UUID,
    premissa_id: UUID,
    corpo: EstadoDaPremissaIn,
    executor: ExecutorDependente,
) -> PremissaOut:
    """RF-13: desafiar exige justificativa; revigorar é o caminho de volta, com evento."""
    try:
        estado = EstadoDaPremissa(corpo.estado)
    except ValueError as erro:
        raise DadoInvalido(
            f"estado de premissa desconhecido: {corpo.estado!r}; esperado um de "
            f"{[e.value for e in EstadoDaPremissa]}"
        ) from erro
    if estado is EstadoDaPremissa.DESAFIADA:
        executor.rodar(
            DesafiarPremissa,
            projeto_id=projeto_id,
            premissa_id=premissa_id,
            justificativa=corpo.justificativa,
        )
    else:
        executor.rodar(
            RevigorarPremissa, projeto_id=projeto_id, premissa_id=premissa_id
        )
    return _premissa_com_injecoes(executor, projeto_id, premissa_id)


@roteador.delete(
    "/projetos/{projeto_id}/premissas/{premissa_id}", response_model=ArquivamentoOut
)
def arquivar_premissa(
    projeto_id: UUID, premissa_id: UUID, executor: ExecutorDependente
) -> ArquivamentoOut:
    """RF-15: arquivar leva as injeções junto — e a resposta diz QUANTAS foram."""
    quantas = executor.rodar(
        ArquivarPremissa, projeto_id=projeto_id, premissa_id=premissa_id
    )
    return ArquivamentoOut(premissa_id=premissa_id, injecoes_arquivadas=quantas)


# -- injeções -----------------------------------------------------------------------------


@roteador.post(
    "/projetos/{projeto_id}/premissas/{premissa_id}/injecoes",
    status_code=status.HTTP_201_CREATED,
    response_model=InjecaoOut,
)
def registrar_injecao(
    projeto_id: UUID, premissa_id: UUID, corpo: InjecaoIn, executor: ExecutorDependente
) -> InjecaoOut:
    """RN-04: a premissa está no CAMINHO da rota — não existe injeção sem ela."""
    injecao = executor.rodar(
        RegistrarInjecao,
        projeto_id=projeto_id,
        premissa_id=premissa_id,
        texto=corpo.texto,
        separacao=_separacao(corpo.separacao),
    )
    return InjecaoOut.de(injecao)


@roteador.put("/projetos/{projeto_id}/injecoes/{injecao_id}", response_model=InjecaoOut)
def editar_injecao(
    projeto_id: UUID,
    injecao_id: UUID,
    corpo: TextoDaInjecaoIn,
    executor: ExecutorDependente,
) -> InjecaoOut:
    return InjecaoOut.de(
        executor.rodar(
            EditarInjecao,
            projeto_id=projeto_id,
            injecao_id=injecao_id,
            texto=corpo.texto,
        )
    )


@roteador.put(
    "/projetos/{projeto_id}/injecoes/{injecao_id}/separacao", response_model=InjecaoOut
)
def classificar_injecao(
    projeto_id: UUID, injecao_id: UUID, corpo: SeparacaoIn, executor: ExecutorDependente
) -> InjecaoOut:
    """RF-18: a classificação TRIZ vale para qualquer injeção; `null` a remove."""
    return InjecaoOut.de(
        executor.rodar(
            ClassificarInjecao,
            projeto_id=projeto_id,
            injecao_id=injecao_id,
            separacao=_separacao(corpo.separacao),
        )
    )


@roteador.put(
    "/projetos/{projeto_id}/injecoes/{injecao_id}/status", response_model=InjecaoOut
)
def mudar_status_da_injecao(
    projeto_id: UUID,
    injecao_id: UUID,
    corpo: StatusDeInjecaoIn,
    executor: ExecutorDependente,
) -> InjecaoOut:
    """RN-08: a FSM é do domínio — voltar a `candidata` exige justificativa e dá 409."""
    try:
        novo = StatusDeInjecao(corpo.status)
    except ValueError as erro:
        raise DadoInvalido(
            f"status de injeção desconhecido: {corpo.status!r}; esperado um de "
            f"{[s.value for s in StatusDeInjecao]}"
        ) from erro
    return InjecaoOut.de(
        executor.rodar(
            MudarStatusDeInjecao,
            projeto_id=projeto_id,
            injecao_id=injecao_id,
            status=novo,
            justificativa=corpo.justificativa,
        )
    )


# -- geração assistida (pré-visualização; a escrita é da proposta) -------------------------


@roteador.post("/projetos/{projeto_id}/geracoes", response_model=GeracaoOut)
def gerar(
    projeto_id: UUID, corpo: NarrativaIn, executor: ExecutorDependente
) -> GeracaoOut:
    """RF-21/RF-23: devolve a nuvem proposta **validada por esquema**, sem aplicar nada.

    Quem aplica é a ação governada `toc.generate_conflict_cloud`, que nasce
    `action_proposal` e atravessa a máquina de estados do servidor (ciclo 006). Esta rota
    existe para a pré-visualização em diff (RI-06) — e por isso recusar não custa nada:
    não houve escrita para desfazer (RF-24).
    """
    resultado = executor.rodar(
        GerarNuvemPorNarrativa, projeto_id=projeto_id, narrativa=corpo.narrativa
    )
    return GeracaoOut(
        action_id=ACAO_DE_GERACAO,
        resultado=resultado.como_dicionario(),
        aviso=AVISO_DE_PROPOSTA,
    )


@roteador.post(
    "/projetos/{projeto_id}/arestas/{chave}/sugestoes/premissas",
    response_model=SugestoesDePremissaOut,
)
def sugerir_premissas(
    projeto_id: UUID, chave: str, corpo: NarrativaIn, executor: ExecutorDependente
) -> SugestoesDePremissaOut:
    """RF-26/INT-03: refinar UMA aresta sem regenerar a nuvem que o grupo já validou."""
    alvo = _chave(chave)
    sugestoes = executor.rodar(
        SugerirPremissas, projeto_id=projeto_id, chave=alvo, narrativa=corpo.narrativa
    )
    return SugestoesDePremissaOut(
        action_id=ACAO_DE_PREMISSAS,
        aresta=alvo.value,
        sugestoes=[
            SugestaoDePremissaOut(
                texto=s.texto,
                injecoes=[
                    SugestaoDeInjecaoOut(
                        texto=i.texto,
                        separacao=i.separacao.value if i.separacao else None,
                    )
                    for i in s.injecoes
                ],
            )
            for s in sugestoes
        ],
        aviso=AVISO_DE_PROPOSTA,
    )


@roteador.post(
    "/projetos/{projeto_id}/premissas/{premissa_id}/sugestoes/injecoes",
    response_model=SugestoesDeInjecaoOut,
)
def sugerir_injecoes(
    projeto_id: UUID, premissa_id: UUID, executor: ExecutorDependente
) -> SugestoesDeInjecaoOut:
    """RF-26/INT-04: injeções para UMA premissa; cada uma nasce proposta individual."""
    sugestoes = executor.rodar(
        SugerirInjecoes, projeto_id=projeto_id, premissa_id=premissa_id
    )
    return SugestoesDeInjecaoOut(
        action_id=ACAO_DE_INJECOES,
        premissa_id=premissa_id,
        sugestoes=[
            SugestaoDeInjecaoOut(
                texto=s.texto, separacao=s.separacao.value if s.separacao else None
            )
            for s in sugestoes
        ],
        aviso=AVISO_DE_PROPOSTA,
    )
