"""Casos de uso do agregado Projeto — a fatia vertical mínima do esqueleto.

Existem quatro, e são os que provam que o chão funciona ponta a ponta: criar, listar,
excluir (suave) e restaurar. As ferramentas da TOC entram por cima disto nos ciclos 004
em diante; nada aqui conhece Efeito Indesejável, premissa ou injeção.

Camada pura: zero import de SQLAlchemy, FastAPI, Pydantic ou OpenTelemetry — o
`import-linter` (contrato P3-2) reprova se alguém mudar isso.
"""
from __future__ import annotations

from uuid import UUID, uuid4

from ..dominio.erros import NaoEncontrado
from ..dominio.identidade import DonoDoProjeto
from ..dominio.portas import Rastreador, Relogio, RepositorioDeProjetos
from ..dominio.projeto import Projeto
from .casos_de_uso import CasoDeUso


class _ComRepositorio(CasoDeUso):
    def __init__(
        self,
        *,
        rastreador: Rastreador,
        repositorio: RepositorioDeProjetos,
        relogio: Relogio | None = None,
    ) -> None:
        super().__init__(rastreador=rastreador)
        self._repositorio = repositorio
        self._relogio = relogio

    def _exigir_relogio(self) -> Relogio:
        if self._relogio is None:  # pragma: no cover - erro de composição, não de uso
            raise RuntimeError(f"{type(self).__name__} precisa de um relógio")
        return self._relogio

    def _carregar(self, dono: DonoDoProjeto, projeto_id: UUID) -> Projeto:
        """Carrega SEMPRE pelo inquilino do dono — a fronteira é a consulta.

        Fora do inquilino a resposta é `NaoEncontrado`, nunca "proibido": distinguir os
        dois vazaria a existência do projeto alheio.
        """
        projeto = self._repositorio.obter(dono.inquilino_id, projeto_id)
        if projeto is None:
            raise NaoEncontrado(str(projeto_id))
        return projeto


class CriarProjeto(_ComRepositorio):
    nome = "criar_projeto"

    def executar(
        self,
        *,
        dono: DonoDoProjeto,
        nome: str,
        ferramenta: str = "generico",
        descricao_do_problema: str = "",
    ) -> Projeto:
        agora = self._exigir_relogio().agora()
        projeto = Projeto(
            id=uuid4(),
            dono=dono,
            nome=nome,
            ferramenta=ferramenta,
            descricao_do_problema=descricao_do_problema,
            criado_em=agora,
            alterado_em=agora,
        )
        self._repositorio.salvar(projeto)
        return projeto


class ListarProjetos(_ComRepositorio):
    nome = "listar_projetos"

    def executar(
        self, *, dono: DonoDoProjeto, incluir_excluidos: bool = False
    ) -> list[Projeto]:
        return self._repositorio.listar(
            dono.inquilino_id, incluir_excluidos=incluir_excluidos
        )


class ExcluirProjeto(_ComRepositorio):
    nome = "excluir_projeto"

    def executar(self, *, dono: DonoDoProjeto, projeto_id: UUID) -> Projeto:
        projeto = self._carregar(dono, projeto_id)
        projeto.excluir(em=self._exigir_relogio().agora())
        self._repositorio.salvar(projeto)
        return projeto


class RestaurarProjeto(_ComRepositorio):
    nome = "restaurar_projeto"

    def executar(self, *, dono: DonoDoProjeto, projeto_id: UUID) -> Projeto:
        projeto = self._repositorio.obter(dono.inquilino_id, projeto_id)
        if projeto is None:
            raise NaoEncontrado(str(projeto_id))
        projeto.restaurar(em=self._exigir_relogio().agora())
        self._repositorio.salvar(projeto)
        return projeto
