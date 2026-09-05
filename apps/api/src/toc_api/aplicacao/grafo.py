"""Casos de uso do grafo (M1) — orquestração pura sobre as portas.

Cada um faz o mesmo trio: carrega o agregado **pelo inquilino**, chama a regra no
domínio, grava. A regra não mora aqui; se morasse, o domínio não seria testável sozinho.

O span é aberto pela classe-base (`CasoDeUso.rodar`), inclusive quando o caso de uso
recusa — "traço de toda ação, inclusive recusas" (brief §4; spec 004, RF-26).

Camada pura: zero import de SQLAlchemy, FastAPI, Pydantic ou OpenTelemetry — o contrato
P3-2 do `import-linter` reprova quem mudar isso.
"""
from __future__ import annotations

from uuid import UUID

from ..dominio.grafo import ArestaCausal, No
from ..dominio.identidade import DonoDoProjeto
from ..dominio.portas import SpanDeTraco
from ..dominio.valores import TIPO_DE_NO_PADRAO, PosicaoNoCanvas
from .projetos import _ComRepositorio


class _SobreProjeto(_ComRepositorio):
    """Carrega, deixa a subclasse agir sobre o agregado, grava. Uma vez só."""

    def executar(self, *, dono: DonoDoProjeto, projeto_id: UUID, **kw):
        projeto = self._carregar(dono, projeto_id)
        resultado = self.agir(projeto, em=self._exigir_relogio().agora(), **kw)
        self._repositorio.salvar(projeto)
        return resultado

    def agir(self, projeto, *, em, **kw):  # pragma: no cover - contrato
        raise NotImplementedError


class AdicionarNo(_SobreProjeto):
    nome = "adicionar_no"

    def agir(
        self,
        projeto,
        *,
        em,
        titulo: str,
        descricao: str = "",
        tipo: str = TIPO_DE_NO_PADRAO,
        posicao: PosicaoNoCanvas | None = None,
    ) -> No:
        return projeto.adicionar_no(
            titulo=titulo, descricao=descricao, tipo=tipo, posicao=posicao, em=em
        )


class EditarNo(_SobreProjeto):
    nome = "editar_no"

    def agir(
        self, projeto, *, em, no_id: UUID, titulo: str | None = None,
        descricao: str | None = None,
    ) -> No:
        return projeto.editar_no(no_id, titulo=titulo, descricao=descricao, em=em)


class MoverNo(_SobreProjeto):
    nome = "mover_no"

    def agir(self, projeto, *, em, no_id: UUID, posicao: PosicaoNoCanvas) -> No:
        return projeto.mover_no(no_id, posicao, em=em)


class RecolherNo(_SobreProjeto):
    nome = "recolher_no"

    def agir(self, projeto, *, em, no_id: UUID, recolhido: bool) -> No:
        return projeto.recolher_no(no_id, recolhido, em=em)


class ExcluirNo(_SobreProjeto):
    """Devolve o RAIO — os identificadores das arestas que saíram junto (RF-15)."""

    nome = "excluir_no"

    def agir(self, projeto, *, em, no_id: UUID) -> list[UUID]:
        return projeto.excluir_no(no_id, em=em)

    def anotar_resultado(self, span: SpanDeTraco, resultado) -> None:
        span.atributo("toc.arestas_removidas", len(resultado))


class LigarNos(_SobreProjeto):
    nome = "ligar_nos"

    def agir(
        self, projeto, *, em, origem_id: UUID, destino_id: UUID, rotulo: str = ""
    ) -> ArestaCausal:
        return projeto.ligar(origem_id, destino_id, rotulo=rotulo, em=em)


class EditarAresta(_SobreProjeto):
    nome = "editar_aresta"

    def agir(self, projeto, *, em, aresta_id: UUID, rotulo: str) -> ArestaCausal:
        return projeto.editar_aresta(aresta_id, rotulo, em=em)


class ExcluirAresta(_SobreProjeto):
    nome = "excluir_aresta"

    def agir(self, projeto, *, em, aresta_id: UUID) -> None:
        projeto.excluir_aresta(aresta_id, em=em)
