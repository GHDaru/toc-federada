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
from ..dominio.portas import Rastreador, Relogio, RepositorioDeProjetos, SpanDeTraco
from ..dominio.projeto import Projeto
from ..dominio.referencia import sincronizar_referencias
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

    def _sincronizar_referencias(
        self, dono: DonoDoProjeto, projeto_id: UUID, *, excluido: bool
    ) -> int:
        """RF-35/RN-12: a exclusão suave SUSPENDE as referências que tocam o projeto.

        E a restauração as reativa. A referência **nunca** é apagada por efeito colateral
        — apagar referência é ação própria, com evento (RN-12). Quem faz a suspensão é o
        caso de uso, e não um gatilho de banco, porque é aqui que existe o instante da
        operação e o traço que a relata.

        O repositório do M1 não conhece referência cruzada (a porta é outra, do M4): sem
        ela composta, não há o que sincronizar, e o caso de uso segue — é a mesma
        composição parcial que a fábrica de persistência já admite.
        """
        listar = getattr(self._repositorio, "listar_referencias", None)
        salvar = getattr(self._repositorio, "salvar_referencia", None)
        if listar is None or salvar is None:
            return 0
        mudadas = sincronizar_referencias(
            listar(dono.inquilino_id, projeto_id=projeto_id),
            projeto_id=projeto_id,
            excluido=excluido,
            motivo=f"projeto {projeto_id} excluído",
            em=self._exigir_relogio().agora(),
        )
        for referencia in mudadas:
            salvar(referencia)
        return len(mudadas)

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
        self._suspensas = self._sincronizar_referencias(dono, projeto_id, excluido=True)
        return projeto

    def anotar_resultado(self, span: SpanDeTraco, resultado: Projeto) -> None:
        span.atributo("toc.referencias_suspensas", getattr(self, "_suspensas", 0))


class RestaurarProjeto(_ComRepositorio):
    nome = "restaurar_projeto"

    def executar(self, *, dono: DonoDoProjeto, projeto_id: UUID) -> Projeto:
        projeto = self._repositorio.obter(dono.inquilino_id, projeto_id)
        if projeto is None:
            raise NaoEncontrado(str(projeto_id))
        projeto.restaurar(em=self._exigir_relogio().agora())
        self._repositorio.salvar(projeto)
        self._reativadas = self._sincronizar_referencias(dono, projeto_id, excluido=False)
        return projeto

    def anotar_resultado(self, span: SpanDeTraco, resultado: Projeto) -> None:
        span.atributo("toc.referencias_reativadas", getattr(self, "_reativadas", 0))


class AbrirProjeto(_ComRepositorio):
    """RF-03: metadados, nós e arestas num carregamento consistente.

    Existe como caso de uso, e não como consulta solta do roteador, porque **ler também é
    operação governada**: exige `toc:read`, e a verificação de capacidade acontece na
    camada de aplicação (Anexo B §B.7.2 do Padrão APH — Aplicação ↔ Harness). Uma rota que
    falasse com o repositório direto passaria por fora dela.
    """

    nome = "abrir_projeto"

    def executar(self, *, dono: DonoDoProjeto, projeto_id: UUID) -> Projeto:
        return self._carregar(dono, projeto_id)


class ListarLixeira(_ComRepositorio):
    """RF-07: só os projetos excluídos, com a data de exclusão.

    Separado de `ListarProjetos(incluir_excluidos=True)` de propósito: aquele devolve
    ativos **e** excluídos juntos, que não é a lixeira de tela nenhuma. Filtrar no
    roteador funcionaria e seria regra de negócio fora do lugar.
    """

    nome = "listar_lixeira"

    def executar(self, *, dono: DonoDoProjeto) -> list[Projeto]:
        todos = self._repositorio.listar(dono.inquilino_id, incluir_excluidos=True)
        return [p for p in todos if p.excluido_em is not None]
