"""A superfície HTTP do M5 — a árvore de Estratégia & Táticas sob `/toc/snt` (spec 010).

Siglas, uma vez neste arquivo: **M5** — Estratégia & Táticas · **S&T** — Estratégia &
Táticas (*Strategy & Tactics*) · **M1** — Núcleo de Diagramas Lógicos · **HTTP** —
*HyperText Transfer Protocol* · **RF/RN/RI** — requisito funcional / regra de negócio /
requisito de interface da spec 010.

Quatro decisões desta borda, cada uma com motivo:

1. **Nenhuma rota de escrita aceita número de passo** (RF-06). Não é disciplina: os
   esquemas de entrada não têm o campo, e um teste de contrato lê o OpenAPI publicado e
   conta. O contraexemplo é o formulário da quarta geração, onde o número era obrigatório,
   texto livre e sem validação (`tocbuilderv3/components/SnTStepEditorModal.tsx:56-57`).
2. **Prever é rota própria, e é leitura.** `POST …/previas-de-mover` e
   `GET …/previa-de-exclusao` respondem o que aconteceria — a renumeração e a contagem —
   sem gravar nada. É o que permite a interface cumprir o RI-05 e o RI-06 sem escrever um
   fato que ninguém pediu, e é por isso que uma observadora só-leitura as alcança.
   `POST` na prévia de mover não é contradição: o pedido tem corpo (alvo, destino,
   posição) e um `GET` com três parâmetros de consulta seria pior de ler e de cachear
   errado.
3. **O autor da mudança de status vem do principal.** O corpo do pedido tem um campo só,
   `status`; quem mudou é a identidade da fundação. Na linhagem, status não tinha autoria
   nenhuma (RN-03).
4. **A exclusão devolve a árvore inteira**, e não `204`: quem exclui uma subárvore precisa
   ver a renumeração que sobrou, e uma resposta vazia obrigaria a interface a um segundo
   pedido para descobrir o que mudou.
"""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, status

from ...aplicacao.snt import (
    AbrirProjetoSnT,
    AdicionarPassoDaSnT,
    CriarProjetoSnT,
    EditarMetaGlobal,
    EditarPassoDaSnT,
    EditarPremissasDoPasso,
    ExcluirSubarvore,
    ExportarSnT,
    MoverPassoDaSnT,
    MudarStatusDoPassoDaSnT,
    PendenciasDaSnT,
    PreverRenumeracao,
)
from ...dominio.erros import DadoInvalido
from ...dominio.snt import CategoriaDoPasso, StatusDoPasso
from ..dependencias import ExecutorDependente
from ..esquemas import (
    AcompanhamentoOut,
    AdicionarPassoIn,
    CriarSnTIn,
    EditarPassoDaSnTIn,
    FichaDoPassoOut,
    LinhaDaSnTOut,
    MetaGlobalIn,
    MoverPassoIn,
    MudancaDeNumeroOut,
    PassoDaSnTOut,
    PremissasDoPassoIn,
    PreviaDeExclusaoOut,
    PreviaDeMoverIn,
    PreviaDeMoverOut,
    SnTOut,
    StatusDoPassoSnTIn,
    TabelaDaSnTOut,
)

roteador = APIRouter(prefix="/toc/snt", tags=["estrategia-e-taticas"])


def _valor(bruto: str, enumeracao, campo: str):
    """Converte texto em enum de domínio — e recusa na BORDA, com a lista do esperado."""
    try:
        return enumeracao(bruto)
    except ValueError as erro:
        raise DadoInvalido(
            f"{campo} desconhecido: {bruto!r}; esperado um de "
            f"{[e.value for e in enumeracao]}"
        ) from erro


# ---------------------------------------------------------------------------------------
# F5.1.1 · o projeto S&T com meta global
# ---------------------------------------------------------------------------------------


@roteador.post("/projetos", status_code=status.HTTP_201_CREATED, response_model=SnTOut)
def criar_snt(corpo: CriarSnTIn, executor: ExecutorDependente) -> SnTOut:
    """RF-01: a meta global é obrigatória — S&T sem alvo não decompõe nada."""
    projeto = executor.rodar(
        CriarProjetoSnT,
        nome=corpo.nome,
        meta_global=corpo.meta_global,
        descricao_do_problema=corpo.descricao_do_problema,
    )
    return SnTOut.de(executor.rodar(AbrirProjetoSnT, projeto_id=projeto.id))


@roteador.get("/projetos/{projeto_id}", response_model=SnTOut)
def abrir_snt(projeto_id: UUID, executor: ExecutorDependente) -> SnTOut:
    return SnTOut.de(executor.rodar(AbrirProjetoSnT, projeto_id=projeto_id))


@roteador.put("/projetos/{projeto_id}/meta-global", response_model=SnTOut)
def editar_meta_global(
    projeto_id: UUID, corpo: MetaGlobalIn, executor: ExecutorDependente
) -> SnTOut:
    """RF-02: a meta tem evento próprio — mudar o alvo do plano não é editar metadado."""
    executor.rodar(EditarMetaGlobal, projeto_id=projeto_id, meta_global=corpo.meta_global)
    return SnTOut.de(executor.rodar(AbrirProjetoSnT, projeto_id=projeto_id))


# ---------------------------------------------------------------------------------------
# F5.1.2 · passos, numeração derivada e movimentação
# ---------------------------------------------------------------------------------------


@roteador.post(
    "/projetos/{projeto_id}/passos",
    status_code=status.HTTP_201_CREATED,
    response_model=PassoDaSnTOut,
)
def adicionar_passo(
    projeto_id: UUID, corpo: AdicionarPassoIn, executor: ExecutorDependente
) -> PassoDaSnTOut:
    """RF-04: filho ou raiz, em posição entre irmãos — o número sai calculado."""
    no = executor.rodar(
        AdicionarPassoDaSnT,
        projeto_id=projeto_id,
        estrategia=corpo.estrategia,
        tatica=corpo.tatica,
        pai_id=corpo.pai_id,
        posicao=corpo.posicao,
        paralela=corpo.paralela,
        necessidade_ao_pai=corpo.necessidade_ao_pai,
        suficiencia_dos_filhos=corpo.suficiencia_dos_filhos,
        categoria=(
            _valor(corpo.categoria, CategoriaDoPasso, "categoria do passo")
            if corpo.categoria is not None
            else CategoriaDoPasso.NENHUMA
        ),
    )
    arvore = executor.rodar(AbrirProjetoSnT, projeto_id=projeto_id)
    return PassoDaSnTOut.de(arvore, no.id)


@roteador.get("/projetos/{projeto_id}/passos/{no_id}", response_model=FichaDoPassoOut)
def abrir_ficha_do_passo(
    projeto_id: UUID, no_id: UUID, executor: ExecutorDependente
) -> FichaDoPassoOut:
    """Tela 6.2: o passo com as três premissas nas posições de leitura (RI-03)."""
    arvore = executor.rodar(AbrirProjetoSnT, projeto_id=projeto_id)
    return FichaDoPassoOut.de(arvore, no_id)


@roteador.patch("/projetos/{projeto_id}/passos/{no_id}", response_model=FichaDoPassoOut)
def editar_passo(
    projeto_id: UUID, no_id: UUID, corpo: EditarPassoDaSnTIn, executor: ExecutorDependente
) -> FichaDoPassoOut:
    executor.rodar(
        EditarPassoDaSnT,
        projeto_id=projeto_id,
        no_id=no_id,
        estrategia=corpo.estrategia,
        tatica=corpo.tatica,
        categoria=(
            _valor(corpo.categoria, CategoriaDoPasso, "categoria do passo")
            if corpo.categoria is not None
            else None
        ),
    )
    arvore = executor.rodar(AbrirProjetoSnT, projeto_id=projeto_id)
    return FichaDoPassoOut.de(arvore, no_id)


@roteador.put(
    "/projetos/{projeto_id}/passos/{no_id}/premissas", response_model=FichaDoPassoOut
)
def editar_premissas(
    projeto_id: UUID, no_id: UUID, corpo: PremissasDoPassoIn, executor: ExecutorDependente
) -> FichaDoPassoOut:
    """RF-12/RN-06: grava sempre — premissa ausente é pendência, nunca trava."""
    executor.rodar(
        EditarPremissasDoPasso,
        projeto_id=projeto_id,
        no_id=no_id,
        paralela=corpo.paralela,
        necessidade_ao_pai=corpo.necessidade_ao_pai,
        suficiencia_dos_filhos=corpo.suficiencia_dos_filhos,
    )
    arvore = executor.rodar(AbrirProjetoSnT, projeto_id=projeto_id)
    return FichaDoPassoOut.de(arvore, no_id)


@roteador.post("/projetos/{projeto_id}/previas-de-mover", response_model=PreviaDeMoverOut)
def prever_renumeracao(
    projeto_id: UUID, corpo: PreviaDeMoverIn, executor: ExecutorDependente
) -> PreviaDeMoverOut:
    """RI-05: a renumeração ANTES de confirmar. Leitura — nada muta, nada grava."""
    atual = executor.rodar(AbrirProjetoSnT, projeto_id=projeto_id)
    prevista = executor.rodar(
        PreverRenumeracao,
        projeto_id=projeto_id,
        no_id=corpo.no_id,
        novo_pai_id=corpo.novo_pai_id,
        posicao=corpo.posicao,
    )
    numeros_de_hoje = atual.numeros()
    return PreviaDeMoverOut(
        mudancas=[
            MudancaDeNumeroOut(
                no_id=no_id, numero_atual=numeros_de_hoje.get(no_id, ""), numero_novo=novo
            )
            for no_id, novo in prevista.items()
            if numeros_de_hoje.get(no_id) != novo
        ]
    )


@roteador.put("/projetos/{projeto_id}/passos/{no_id}/posicao", response_model=SnTOut)
def mover_passo(
    projeto_id: UUID, no_id: UUID, corpo: MoverPassoIn, executor: ExecutorDependente
) -> SnTOut:
    """RF-08: leva a subárvore inteira; a resposta é a árvore já renumerada."""
    executor.rodar(
        MoverPassoDaSnT,
        projeto_id=projeto_id,
        no_id=no_id,
        novo_pai_id=corpo.novo_pai_id,
        posicao=corpo.posicao,
    )
    return SnTOut.de(executor.rodar(AbrirProjetoSnT, projeto_id=projeto_id))


@roteador.get(
    "/projetos/{projeto_id}/passos/{no_id}/previa-de-exclusao",
    response_model=PreviaDeExclusaoOut,
)
def prever_exclusao(
    projeto_id: UUID, no_id: UUID, executor: ExecutorDependente
) -> PreviaDeExclusaoOut:
    """RF-09: "N passos serão excluídos" — a contagem ANTES de confirmar, sem apagar."""
    arvore = executor.rodar(AbrirProjetoSnT, projeto_id=projeto_id)
    return PreviaDeExclusaoOut(
        no_id=no_id,
        numero=arvore.numero(no_id),
        passos=arvore.contar_subarvore(no_id),
        primeiro_nivel=[
            PassoDaSnTOut.de(arvore, filho) for filho in arvore.filhos(no_id)
        ],
    )


@roteador.delete("/projetos/{projeto_id}/passos/{no_id}", response_model=SnTOut)
def excluir_subarvore(
    projeto_id: UUID, no_id: UUID, executor: ExecutorDependente
) -> SnTOut:
    """RN-05: a subárvore EXATA. Os demais passos ficam — o defeito F-07 não atravessa."""
    executor.rodar(ExcluirSubarvore, projeto_id=projeto_id, no_id=no_id)
    return SnTOut.de(executor.rodar(AbrirProjetoSnT, projeto_id=projeto_id))


# ---------------------------------------------------------------------------------------
# E5.2 · status e acompanhamento
# ---------------------------------------------------------------------------------------


@roteador.put(
    "/projetos/{projeto_id}/passos/{no_id}/status", response_model=FichaDoPassoOut
)
def mudar_status(
    projeto_id: UUID, no_id: UUID, corpo: StatusDoPassoSnTIn, executor: ExecutorDependente
) -> FichaDoPassoOut:
    """RN-03: transição livre entre os quatro valores; o AUTOR vem do principal."""
    executor.rodar(
        MudarStatusDoPassoDaSnT,
        projeto_id=projeto_id,
        no_id=no_id,
        status=_valor(corpo.status, StatusDoPasso, "status do passo"),
    )
    arvore = executor.rodar(AbrirProjetoSnT, projeto_id=projeto_id)
    return FichaDoPassoOut.de(arvore, no_id)


@roteador.get("/projetos/{projeto_id}/acompanhamento", response_model=AcompanhamentoOut)
def acompanhamento(projeto_id: UUID, executor: ExecutorDependente) -> AcompanhamentoOut:
    """RF-17: contagens, pendências e progresso — todos da MESMA função pura."""
    return AcompanhamentoOut.de(executor.rodar(PendenciasDaSnT, projeto_id=projeto_id))


@roteador.get("/projetos/{projeto_id}/tabela", response_model=TabelaDaSnTOut)
def tabela(projeto_id: UUID, executor: ExecutorDependente) -> TabelaDaSnTOut:
    """RF-19: a vista tabular indentada, em ordem estrutural fixa."""
    arvore = executor.rodar(AbrirProjetoSnT, projeto_id=projeto_id)
    return TabelaDaSnTOut(
        linhas=[
            LinhaDaSnTOut(
                no_id=linha.no_id,
                numero=linha.numero,
                nivel=linha.nivel,
                pai_id=linha.pai_id,
                estrategia=linha.estrategia,
                tatica=linha.tatica,
                categoria=linha.categoria.value,
                status=linha.status.value,
                filhos=linha.filhos,
                tem_premissa_paralela=linha.tem_premissa_paralela,
                tem_premissa_de_necessidade=linha.tem_premissa_de_necessidade,
                tem_premissa_de_suficiencia=linha.tem_premissa_de_suficiencia,
            )
            for linha in arvore.linhas()
        ]
    )


@roteador.get("/projetos/{projeto_id}/exportacao")
def exportar(projeto_id: UUID, executor: ExecutorDependente) -> dict:
    """RF-21: o documento canônico — e ele **não carrega número** (RN-01)."""
    return executor.rodar(ExportarSnT, projeto_id=projeto_id)
