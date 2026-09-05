"""Projetos, nós e arestas — a superfície HTTP do M1 (spec 004).

Cada rota é **um comando nomeado do agregado**, com evento e traço próprios. Não existe
`PUT` de estado inteiro do projeto, e a ausência é deliberada: o `saveProjectState` da 4ª
geração da linhagem (`tocbuilderv3/services/mockApiService.ts:286-301`) tornava toda
escrita uma substituição cega, e é ele que esta forma aposenta.

A rota não decide acesso e não conhece repositório: ela traduz JavaScript Object Notation
(JSON) em argumento, chama `executor.rodar(<caso de uso>)` e traduz o resultado de volta.
Quem verifica a capacidade é a camada de aplicação (Anexo B §B.7.2).
"""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Response, status

from ...aplicacao.grafo import (
    AdicionarNo,
    EditarAresta,
    EditarNo,
    ExcluirAresta,
    ExcluirNo,
    LigarNos,
    MoverNo,
    RecolherNo,
)
from ...aplicacao.projetos import (
    AbrirProjeto,
    CriarProjeto,
    ExcluirProjeto,
    ListarLixeira,
    ListarProjetos,
    RestaurarProjeto,
)
from ...dominio.erros import DadoInvalido
from ..dependencias import ExecutorDependente
from ..esquemas import (
    ArestaOut,
    CriarNoIn,
    CriarProjetoIn,
    EditarArestaIn,
    EditarNoIn,
    ExclusaoDeNoOut,
    LigarIn,
    NoOut,
    ProjetoOut,
    ProjetoResumoOut,
)

roteador = APIRouter(prefix="/toc/projetos", tags=["projetos"])


@roteador.post("", status_code=status.HTTP_201_CREATED, response_model=ProjetoOut)
def criar_projeto(corpo: CriarProjetoIn, executor: ExecutorDependente) -> ProjetoOut:
    projeto = executor.rodar(
        CriarProjeto,
        nome=corpo.nome,
        descricao_do_problema=corpo.descricao_do_problema,
    )
    return ProjetoOut.de(projeto)


@roteador.get("", response_model=list[ProjetoResumoOut])
def listar_projetos(executor: ExecutorDependente) -> list[ProjetoResumoOut]:
    return [ProjetoResumoOut.de(p) for p in executor.rodar(ListarProjetos)]


# Declarada ANTES de `/{projeto_id}`: o roteador casa na ordem, e um `{projeto_id}`
# tipado como UUID recusaria "lixeira" com 422 antes de esta rota ser alcançada.
@roteador.get("/lixeira", response_model=list[ProjetoResumoOut])
def listar_lixeira(executor: ExecutorDependente) -> list[ProjetoResumoOut]:
    return [ProjetoResumoOut.de(p) for p in executor.rodar(ListarLixeira)]


@roteador.get("/{projeto_id}", response_model=ProjetoOut)
def abrir_projeto(projeto_id: UUID, executor: ExecutorDependente) -> ProjetoOut:
    return ProjetoOut.de(executor.rodar(AbrirProjeto, projeto_id=projeto_id))


@roteador.delete("/{projeto_id}", response_model=ProjetoResumoOut)
def excluir_projeto(projeto_id: UUID, executor: ExecutorDependente) -> ProjetoResumoOut:
    """Exclusão SUAVE (RF-06): a linha fica, o estado muda, e a lixeira a mostra."""
    return ProjetoResumoOut.de(executor.rodar(ExcluirProjeto, projeto_id=projeto_id))


@roteador.post("/{projeto_id}/restaurar", response_model=ProjetoResumoOut)
def restaurar_projeto(projeto_id: UUID, executor: ExecutorDependente) -> ProjetoResumoOut:
    return ProjetoResumoOut.de(executor.rodar(RestaurarProjeto, projeto_id=projeto_id))


# -- nós -----------------------------------------------------------------------------


@roteador.post(
    "/{projeto_id}/nos", status_code=status.HTTP_201_CREATED, response_model=NoOut
)
def criar_no(projeto_id: UUID, corpo: CriarNoIn, executor: ExecutorDependente) -> NoOut:
    no = executor.rodar(
        AdicionarNo,
        projeto_id=projeto_id,
        titulo=corpo.titulo,
        descricao=corpo.descricao,
        posicao=corpo.posicao.para_dominio() if corpo.posicao else None,
    )
    return NoOut.de(no)


@roteador.patch("/{projeto_id}/nos/{no_id}", response_model=NoOut)
def editar_no(
    projeto_id: UUID, no_id: UUID, corpo: EditarNoIn, executor: ExecutorDependente
) -> NoOut:
    """PATCH parcial. Cada grupo de campos vira o SEU comando de domínio.

    Título e descrição são `NoEditado`; posição é `NoMovido`; recolher é `NoRecolhido`.
    Um único `PUT` de nó inteiro esconderia os três eventos num só e apagaria a diferença
    entre "arrastei" e "reescrevi" — que é a diferença de que o desfazer por episódio
    (RF-22) depende.
    """
    resultado = None
    if corpo.titulo is not None or corpo.descricao is not None:
        resultado = executor.rodar(
            EditarNo,
            projeto_id=projeto_id,
            no_id=no_id,
            titulo=corpo.titulo,
            descricao=corpo.descricao,
        )
    if corpo.posicao is not None:
        resultado = executor.rodar(
            MoverNo,
            projeto_id=projeto_id,
            no_id=no_id,
            posicao=corpo.posicao.para_dominio(),
        )
    if corpo.recolhido is not None:
        resultado = executor.rodar(
            RecolherNo, projeto_id=projeto_id, no_id=no_id, recolhido=corpo.recolhido
        )
    if resultado is None:
        raise DadoInvalido(
            "editar_no: informe ao menos um de titulo, descricao, posicao ou recolhido"
        )
    return NoOut.de(resultado)


@roteador.delete("/{projeto_id}/nos/{no_id}", response_model=ExclusaoDeNoOut)
def excluir_no(
    projeto_id: UUID, no_id: UUID, executor: ExecutorDependente
) -> ExclusaoDeNoOut:
    """Devolve o RAIO (RF-15): quais arestas saíram junto, para o cliente não adivinhar."""
    removidas = executor.rodar(ExcluirNo, projeto_id=projeto_id, no_id=no_id)
    return ExclusaoDeNoOut(no_id=no_id, arestas_removidas=list(removidas))


# -- arestas -------------------------------------------------------------------------


@roteador.post(
    "/{projeto_id}/arestas", status_code=status.HTTP_201_CREATED, response_model=ArestaOut
)
def ligar(projeto_id: UUID, corpo: LigarIn, executor: ExecutorDependente) -> ArestaOut:
    aresta = executor.rodar(
        LigarNos,
        projeto_id=projeto_id,
        origem_id=corpo.origem_id,
        destino_id=corpo.destino_id,
        rotulo=corpo.rotulo,
    )
    return ArestaOut.de(aresta)


@roteador.patch("/{projeto_id}/arestas/{aresta_id}", response_model=ArestaOut)
def editar_aresta(
    projeto_id: UUID, aresta_id: UUID, corpo: EditarArestaIn, executor: ExecutorDependente
) -> ArestaOut:
    aresta = executor.rodar(
        EditarAresta, projeto_id=projeto_id, aresta_id=aresta_id, rotulo=corpo.rotulo
    )
    return ArestaOut.de(aresta)


@roteador.delete("/{projeto_id}/arestas/{aresta_id}", status_code=status.HTTP_204_NO_CONTENT)
def excluir_aresta(projeto_id: UUID, aresta_id: UUID, executor: ExecutorDependente) -> Response:
    executor.rodar(ExcluirAresta, projeto_id=projeto_id, aresta_id=aresta_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
