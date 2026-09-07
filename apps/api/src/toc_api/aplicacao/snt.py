"""Casos de uso do M5 — a Árvore de Estratégia & Táticas (S&T) sobre as portas (spec 010).

Siglas, uma vez neste arquivo: **M5** — Estratégia & Táticas · **S&T** — Estratégia &
Táticas (*Strategy & Tactics*) · **M1** — Núcleo de Diagramas Lógicos · **OTel** —
OpenTelemetry · **APH** — Aplicação ↔ Harness · **ADR** — *Architecture Decision Record*
(Registro de Decisão Arquitetural) · **RF/RN/RNF** — requisito funcional / regra de
negócio / requisito não funcional da spec 010.

Quatro coisas que este arquivo faz e que não são óbvias:

1. **Carregar, agir, gravar — e a raiz no meio.** Todo caso de uso mutador carrega o
   agregado pela porta da ferramenta, chama a operação **na raiz** (`ArvoreSnT`) e grava
   pela mesma porta. Não existe caminho que toque o `Projeto` do M1 direto: quem tentasse
   receberia `MutacaoForaDaRaiz` do próprio domínio.
2. **O span carrega grandeza e número, nunca texto de pessoa** (ADR 0006, P5). Número do
   passo, contagem de excluídos, status e quantidade de pendências — sim. Estratégia,
   tática e premissa — nunca.
3. **O autor da mudança de status vem do principal**, e por isso `MudarStatusDoPassoDaSnT`
   **não tem** parâmetro `autor`. A linhagem mudava status sem registrar quem
   (`tocbuilderv3/types.ts:270-275` não tem autoria em lugar nenhum); aqui a identidade é
   a da fundação, e não um campo que alguém manda.
4. **Prever a renumeração é LEITURA.** `PreverRenumeracao` não grava evento nenhum — é
   função pura sobre a estrutura, e por isso um principal só-leitura a alcança. A
   alternativa (mover, mostrar, desfazer) escreveria um fato que ninguém pediu.

**Nenhuma ação de catálogo `toc.*` nasce aqui** — a INT-04 da spec 010 declara isso
explicitamente, e não por omissão: o round 010 não inclui assistência de inteligência
artificial para a S&T. Quando entrar, é decisão nova sob o ADR 0007.

Camada pura: nenhum import de framework, banco ou cliente de inteligência artificial (P3).
"""
from __future__ import annotations

from uuid import UUID, uuid4

from ..dominio.erros import NaoEncontrado
from ..dominio.grafo import No
from ..dominio.identidade import DonoDoProjeto
from ..dominio.portas import Rastreador, Relogio, RepositorioDaSnT, SpanDeTraco
from ..dominio.projeto import Projeto
from ..dominio.snt import (
    ArvoreSnT,
    CategoriaDoPasso,
    FichaDoPasso,
    PendenciasDaArvore,
    PremissasDoPasso,
    StatusDoPasso,
    exportar_arvore_snt,
    nova_arvore_snt,
)
from .casos_de_uso import CasoDeUso


class _ComSnT(CasoDeUso):
    """Carrega pela porta da ferramenta, sempre pelo inquilino do dono."""

    def __init__(
        self,
        *,
        rastreador: Rastreador,
        repositorio: RepositorioDaSnT,
        relogio: Relogio | None = None,
    ) -> None:
        super().__init__(rastreador=rastreador)
        self._repositorio = repositorio
        self._relogio = relogio

    def _agora(self):
        if self._relogio is None:  # pragma: no cover - erro de composição
            raise RuntimeError(f"{type(self).__name__} precisa de um relógio")
        return self._relogio.agora()

    def _carregar(self, dono: DonoDoProjeto, projeto_id: UUID) -> ArvoreSnT:
        arvore = self._repositorio.obter_snt(dono.inquilino_id, projeto_id)
        if arvore is None:
            # Projeto de outro inquilino, inexistente, ou que não é uma S&T: a resposta é a
            # mesma, pelo mesmo motivo do M1 — distinguir vazaria a existência alheia.
            raise NaoEncontrado(str(projeto_id))
        return arvore


class CriarProjetoSnT(_ComSnT):
    """RF-01: a S&T nasce com meta global obrigatória e nenhum passo."""

    nome = "criar_projeto_snt"

    def executar(
        self,
        *,
        dono: DonoDoProjeto,
        nome: str,
        meta_global: str,
        descricao_do_problema: str = "",
    ) -> Projeto:
        arvore = nova_arvore_snt(
            id=uuid4(),
            dono=dono,
            nome=nome,
            meta_global=meta_global,
            descricao_do_problema=descricao_do_problema,
            em=self._agora(),
        )
        self._repositorio.salvar_snt(arvore)
        return arvore.projeto


class AbrirProjetoSnT(_ComSnT):
    nome = "abrir_projeto_snt"

    def executar(self, *, dono: DonoDoProjeto, projeto_id: UUID) -> ArvoreSnT:
        return self._carregar(dono, projeto_id)

    def anotar_resultado(self, span: SpanDeTraco, resultado: ArvoreSnT) -> None:
        span.atributo("toc.passos", len(resultado.passos))


class PendenciasDaSnT(_ComSnT):
    """RF-14/RF-17: função pura sobre o agregado já gravado — **não** grava nada."""

    nome = "pendencias_da_snt"

    def executar(self, *, dono: DonoDoProjeto, projeto_id: UUID) -> PendenciasDaArvore:
        return self._carregar(dono, projeto_id).pendencias()

    def anotar_resultado(self, span: SpanDeTraco, resultado: PendenciasDaArvore) -> None:
        for chave, valor in resultado.resumo().items():
            span.atributo(f"toc.{chave}", valor)


class ExportarSnT(_ComSnT):
    """RF-21: o documento canônico — e ele **não carrega número** (RN-01)."""

    nome = "exportar_snt"

    def executar(self, *, dono: DonoDoProjeto, projeto_id: UUID) -> dict:
        return exportar_arvore_snt(self._carregar(dono, projeto_id))

    def anotar_resultado(self, span: SpanDeTraco, resultado: dict) -> None:
        span.atributo("toc.passos", len(resultado.get("passos", ())))


class PreverRenumeracao(_ComSnT):
    """RI-05: os números que o mover produziria. Consulta pura — nada muta, nada grava."""

    nome = "prever_renumeracao"

    def executar(
        self,
        *,
        dono: DonoDoProjeto,
        projeto_id: UUID,
        no_id: UUID,
        novo_pai_id: UUID | None,
        posicao: int | None = None,
    ) -> dict[UUID, str]:
        arvore = self._carregar(dono, projeto_id)
        return arvore.previa_da_renumeracao(
            no_id, novo_pai_id=novo_pai_id, posicao=posicao
        )

    def anotar_resultado(self, span: SpanDeTraco, resultado: dict) -> None:
        span.atributo("toc.passos", len(resultado))


class _SobreSnT(_ComSnT):
    """Carrega, age na raiz, grava. O `dono` vem do principal, nunca do pedido."""

    def executar(self, *, dono: DonoDoProjeto, projeto_id: UUID, **kw):
        arvore = self._carregar(dono, projeto_id)
        resultado = self.agir(arvore, em=self._agora(), dono=dono, **kw)
        self._repositorio.salvar_snt(arvore)
        return resultado

    def agir(self, arvore: ArvoreSnT, *, em, dono: DonoDoProjeto, **kw):  # pragma: no cover
        raise NotImplementedError


class EditarMetaGlobal(_SobreSnT):
    nome = "editar_meta_global"

    def agir(self, arvore, *, em, dono, meta_global: str) -> str:
        return arvore.editar_meta_global(meta_global, em=em)


class AdicionarPassoDaSnT(_SobreSnT):
    """RF-04: filho ou raiz, em posição entre irmãos — **sem parâmetro de número**."""

    nome = "adicionar_passo_da_snt"

    def agir(
        self,
        arvore,
        *,
        em,
        dono,
        estrategia: str,
        tatica: str = "",
        pai_id: UUID | None = None,
        posicao: int | None = None,
        paralela: str = "",
        necessidade_ao_pai: str = "",
        suficiencia_dos_filhos: str = "",
        categoria: CategoriaDoPasso | str = CategoriaDoPasso.NENHUMA,
    ) -> No:
        no = arvore.adicionar_passo(
            estrategia=estrategia,
            tatica=tatica,
            pai_id=pai_id,
            posicao=posicao,
            premissas=PremissasDoPasso(
                paralela=paralela,
                necessidade_ao_pai=necessidade_ao_pai,
                suficiencia_dos_filhos=suficiencia_dos_filhos,
            ),
            categoria=categoria,
            em=em,
        )
        self._numero = arvore.numero(no.id)
        return no

    def anotar_resultado(self, span: SpanDeTraco, resultado: No) -> None:
        span.atributo("toc.numero", getattr(self, "_numero", ""))


class EditarPassoDaSnT(_SobreSnT):
    nome = "editar_passo_da_snt"

    def agir(
        self,
        arvore,
        *,
        em,
        dono,
        no_id: UUID,
        estrategia: str | None = None,
        tatica: str | None = None,
        categoria: CategoriaDoPasso | str | None = None,
    ) -> FichaDoPasso:
        return arvore.editar_passo(
            no_id, estrategia=estrategia, tatica=tatica, categoria=categoria, em=em
        )


class EditarPremissasDoPasso(_SobreSnT):
    """RF-12: as três premissas gravam sempre — ausência é pendência, nunca trava (RN-06)."""

    nome = "editar_premissas_do_passo"

    def agir(
        self,
        arvore,
        *,
        em,
        dono,
        no_id: UUID,
        paralela: str | None = None,
        necessidade_ao_pai: str | None = None,
        suficiencia_dos_filhos: str | None = None,
    ) -> FichaDoPasso:
        return arvore.editar_premissas(
            no_id,
            paralela=paralela,
            necessidade_ao_pai=necessidade_ao_pai,
            suficiencia_dos_filhos=suficiencia_dos_filhos,
            em=em,
        )


class MoverPassoDaSnT(_SobreSnT):
    """RF-08: leva a subárvore inteira e renumera os dois lados (RF-07)."""

    nome = "mover_passo_da_snt"

    def agir(
        self,
        arvore,
        *,
        em,
        dono,
        no_id: UUID,
        novo_pai_id: UUID | None,
        posicao: int | None = None,
    ) -> tuple[str, str]:
        return arvore.mover_passo(
            no_id, novo_pai_id=novo_pai_id, posicao=posicao, em=em
        )

    def anotar_resultado(self, span: SpanDeTraco, resultado: tuple[str, str]) -> None:
        span.atributo("toc.numero_anterior", resultado[0])
        span.atributo("toc.numero", resultado[1])


class ExcluirSubarvore(_SobreSnT):
    """RN-05: a subárvore exata, e a CONTAGEM vai para o traço (DoD 11)."""

    nome = "excluir_subarvore"

    def agir(self, arvore, *, em, dono, no_id: UUID) -> tuple[UUID, ...]:
        return arvore.excluir_subarvore(no_id, em=em)

    def anotar_resultado(self, span: SpanDeTraco, resultado: tuple[UUID, ...]) -> None:
        span.atributo("toc.passos_excluidos", len(resultado))


class MudarStatusDoPassoDaSnT(_SobreSnT):
    """RN-03: o autor vem do PRINCIPAL — não existe parâmetro `autor` nesta assinatura."""

    nome = "mudar_status_do_passo_da_snt"

    def agir(
        self, arvore, *, em, dono, no_id: UUID, status: StatusDoPasso | str
    ) -> FichaDoPasso:
        return arvore.mudar_status(
            no_id, StatusDoPasso(status), autor=dono.usuario_id, em=em
        )

    def anotar_resultado(self, span: SpanDeTraco, resultado: FichaDoPasso) -> None:
        span.atributo("toc.status_do_passo", resultado.status.value)


__all__ = [
    "AbrirProjetoSnT",
    "AdicionarPassoDaSnT",
    "CriarProjetoSnT",
    "EditarMetaGlobal",
    "EditarPassoDaSnT",
    "EditarPremissasDoPasso",
    "ExcluirSubarvore",
    "ExportarSnT",
    "MoverPassoDaSnT",
    "MudarStatusDoPassoDaSnT",
    "PendenciasDaSnT",
    "PreverRenumeracao",
]
