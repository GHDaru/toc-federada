"""Casos de uso da Árvore da Realidade Atual (ARA, M2) — sobre as portas.

O caso de uso mais importante deste arquivo é o que **não** tem repositório:
`ValidarTextoDeUde`. Validar a formulação de um Efeito Indesejável (UDE) é função pura
de domínio, e por isso o caso de uso precisa de um rastreador e de mais nada. Na 4ª
geração da linhagem a mesma operação era uma chamada de rede a um provedor de modelo de
linguagem feita **do navegador** (`tocbuilderv3/services/geminiService.ts:16`, com a
chave no cliente); a assinatura aqui é a prova executável de que a dependência sumiu.

Camada pura: nenhum import de framework, banco ou cliente de inteligência artificial (IA).
"""
from __future__ import annotations

from uuid import UUID, uuid4

from ..dominio.ara import (
    ConectorE,
    EstadoDoExame,
    Exame,
    FichaDeUde,
    ParecerDeJulgamento,
    ProjetoARA,
    StatusDeValidacao,
    novo_projeto_ara,
)
from ..dominio.analise import RelatorioEstrutural
from ..dominio.criterios_ude import ValidacaoFormal, validar_formalmente
from ..dominio.erros import NaoEncontrado
from ..dominio.grafo import No
from ..dominio.identidade import DonoDoProjeto
from ..dominio.portas import Rastreador, Relogio, RepositorioDeARA, SpanDeTraco
from .casos_de_uso import CasoDeUso


class ValidarTextoDeUde(CasoDeUso):
    """Sem repositório, sem relógio, sem rede: só a função pura e o traço (P5)."""

    nome = "validar_texto_de_ude"

    def executar(self, *, dono: DonoDoProjeto, texto: str, idioma: str = "pt") -> ValidacaoFormal:
        return validar_formalmente(texto, idioma=idioma)

    def anotar_resultado(self, span: SpanDeTraco, resultado: ValidacaoFormal) -> None:
        # Grandeza, nunca o texto: o enunciado é conteúdo do usuário (ADR 0006).
        span.atributo("toc.criterios_reprovados", len(resultado.reprovacoes))
        span.atributo("toc.pendencias_de_julgamento", len(resultado.pendencias_de_julgamento))
        span.atributo("toc.versao_do_lexico", resultado.versao_do_lexico)


class _ComRepositorioDeARA(CasoDeUso):
    def __init__(
        self,
        *,
        rastreador: Rastreador,
        repositorio: RepositorioDeARA,
        relogio: Relogio | None = None,
    ) -> None:
        super().__init__(rastreador=rastreador)
        self._repositorio = repositorio
        self._relogio = relogio

    def _agora(self):
        if self._relogio is None:  # pragma: no cover - erro de composição
            raise RuntimeError(f"{type(self).__name__} precisa de um relógio")
        return self._relogio.agora()

    def _carregar(self, dono: DonoDoProjeto, projeto_id: UUID) -> ProjetoARA:
        ara = self._repositorio.obter_ara(dono.inquilino_id, projeto_id)
        if ara is None:
            raise NaoEncontrado(str(projeto_id))
        return ara


class CriarProjetoARA(_ComRepositorioDeARA):
    nome = "criar_projeto_ara"

    def executar(
        self, *, dono: DonoDoProjeto, nome: str, descricao_do_problema: str = ""
    ):
        ara = novo_projeto_ara(
            id=uuid4(),
            dono=dono,
            nome=nome,
            descricao_do_problema=descricao_do_problema,
            em=self._agora(),
        )
        self._repositorio.salvar_ara(ara)
        return ara.projeto


class _SobreARA(_ComRepositorioDeARA):
    def executar(self, *, dono: DonoDoProjeto, projeto_id: UUID, **kw):
        ara = self._carregar(dono, projeto_id)
        resultado = self.agir(ara, em=self._agora(), **kw)
        self._repositorio.salvar_ara(ara)
        self._ara = ara
        return resultado

    def agir(self, ara: ProjetoARA, *, em, **kw):  # pragma: no cover - contrato
        raise NotImplementedError


class _ComStatusNoTraco(_SobreARA):
    """Anota no span o estado a que o UDE chegou — grandeza e enum, nunca texto."""

    _no_id: UUID | None = None

    def anotar_resultado(self, span: SpanDeTraco, resultado) -> None:
        if self._no_id is None:
            return
        span.atributo("toc.status_do_ude", self._ara.status(self._no_id).value)
        span.atributo(
            "toc.criterios_reprovados",
            len(self._ara.validacao(self._no_id).reprovacoes),
        )


class MarcarUde(_ComStatusNoTraco):
    nome = "marcar_ude"

    def agir(self, ara, *, em, no_id: UUID, ficha: FichaDeUde | None = None) -> FichaDeUde:
        self._no_id = no_id
        return ara.marcar_ude(no_id, ficha=ficha, em=em)


class DesmarcarUde(_SobreARA):
    nome = "desmarcar_ude"

    def agir(self, ara, *, em, no_id: UUID) -> None:
        ara.desmarcar_ude(no_id, em=em)


class EditarFichaDeUde(_SobreARA):
    nome = "editar_ficha_de_ude"

    def agir(self, ara, *, em, no_id: UUID, ficha: FichaDeUde) -> FichaDeUde:
        return ara.editar_ficha(no_id, ficha, em=em)


class ReformularUde(_ComStatusNoTraco):
    """Edita o texto e REEXECUTA a validação formal no mesmo comando (RF-10)."""

    nome = "reformular_ude"

    def agir(self, ara, *, em, no_id: UUID, texto: str) -> No:
        self._no_id = no_id
        return ara.reformular(no_id, texto, em=em)


class RegistrarParecer(_SobreARA):
    nome = "registrar_parecer"

    def agir(self, ara, *, em, no_id: UUID, parecer: ParecerDeJulgamento) -> None:
        ara.registrar_parecer(no_id, parecer, em=em)


class MudarStatusDeUde(_SobreARA):
    nome = "mudar_status_de_ude"

    def agir(
        self,
        ara,
        *,
        em,
        no_id: UUID,
        status: StatusDeValidacao,
        justificativa: str = "",
    ) -> StatusDeValidacao:
        return ara.mudar_status(no_id, status, justificativa=justificativa, em=em)

    def anotar_resultado(self, span: SpanDeTraco, resultado) -> None:
        span.atributo("toc.status_do_ude", resultado.value)


class ExaminarElo(_SobreARA):
    nome = "examinar_elo"

    def agir(
        self, ara, *, em, aresta_id: UUID, estado: EstadoDoExame, reserva: str = ""
    ) -> Exame:
        return ara.examinar_elo(aresta_id, estado, reserva=reserva, em=em)

    def anotar_resultado(self, span: SpanDeTraco, resultado: Exame) -> None:
        span.atributo("toc.exame_do_elo", resultado.estado.value)


class FormarConectorE(_SobreARA):
    nome = "formar_conector_e"

    def agir(self, ara, *, em, arestas: tuple[UUID, ...]) -> ConectorE:
        return ara.formar_conector_e(tuple(arestas), em=em)


class DesfazerConectorE(_SobreARA):
    nome = "desfazer_conector_e"

    def agir(self, ara, *, em, conector_id: UUID) -> None:
        ara.desfazer_conector_e(conector_id, em=em)


class AnalisarArvore(_SobreARA):
    """Leitura pura do grafo. Grava porque o evento `AnaliseEstruturalGerada` é
    somente-acréscimo e faz parte da memória do projeto (RF-31) — o grafo não muda."""

    nome = "analisar_arvore"

    def agir(self, ara, *, em) -> RelatorioEstrutural:
        return ara.analisar(em=em)

    def anotar_resultado(self, span: SpanDeTraco, resultado: RelatorioEstrutural) -> None:
        for chave, valor in resultado.resumo().items():
            span.atributo(f"toc.{chave}", valor)


class AbrirProjetoARA(_ComRepositorioDeARA):
    """A leitura do M2: o projeto do M1 mais ficha, status, parecer, exame e conector.

    Pela porta separada `RepositorioDeARA` — o M1 continua sem conhecer semântica da
    Teoria das Restrições (TOC), que é a RN-04 da spec 004. Como todo caso de uso de
    leitura, existe para que a verificação de capacidade (`toc:read`) tenha por onde
    acontecer na camada de aplicação, e não na rota (Anexo B §B.7.2).
    """

    nome = "abrir_projeto_ara"

    def executar(self, *, dono: DonoDoProjeto, projeto_id: UUID) -> ProjetoARA:
        return self._carregar(dono, projeto_id)
