"""Casos de uso da Nuvem de Conflito (NC, M3) — sobre as portas (spec 007).

Siglas, uma vez neste arquivo: **NC** — Nuvem de Conflito · **ARA** — Árvore da Realidade
Atual · **UDE** — Efeito Indesejável · **TOC** — Teoria das Restrições · **TRIZ** — Teoria
da Resolução Inventiva de Problemas · **IA** — inteligência artificial · **FSM** — máquina
de estados finitos · **OTel** — OpenTelemetry.

Três coisas que este arquivo faz e que não são óbvias:

1. **Gerar e aplicar são casos de uso diferentes.** `GerarNuvemPorNarrativa` chama a porta
   da assistência, valida o resultado contra o esquema versionado e **não grava nada**;
   `AplicarGeracaoDeNuvem` é o que escreve, e exige o identificador da proposta que o
   autorizou (RF-23, RF-25). Separá-los é o que torna a recusa barata: recusar é não
   chamar o segundo, e por isso o projeto fica byte a byte intacto (RF-24).
2. **Sugerir é rascunho.** `SugerirPremissas` e `SugerirInjecoes` devolvem propostas
   tipadas e não tocam o agregado (RN-05); quem as aplica é a FSM de proposta do ciclo
   006, uma proposta por sugestão (RF-26).
3. **O traço carrega grandeza, nunca texto.** Narrativa colada pela pessoa e enunciado de
   premissa não entram em span (ADR 0006) — o que entra é quanto, qual chave de aresta e
   qual proposta.

Camada pura: nenhum import de framework, banco ou cliente de IA (P3).
"""
from __future__ import annotations

from typing import Any, Mapping, Sequence
from uuid import UUID, uuid4

from ..dominio.ara import ProjetoARA
from ..dominio.erros import NaoEncontrado
from ..dominio.eventos import ORIGEM_HUMANA
from ..dominio.geracao import (
    InjecaoProposta,
    PremissaProposta,
    ResultadoDeGeracao,
    ResultadoDeGeracaoInvalido,
)
from ..dominio.identidade import DonoDoProjeto
from ..dominio.nuvem import (
    ChaveDaAresta,
    Injecao,
    NuvemDeConflito,
    PapelDaEntidade,
    Premissa,
    SeparacaoTRIZ,
    StatusDeInjecao,
    ValidacaoDaNuvem,
    derivar_nuvem_de_udes,
    novo_projeto_nc,
)
from ..dominio.portas import (
    MotorDeGeracaoDeNuvem,
    Rastreador,
    Relogio,
    RepositorioDaCosturaM2M3,
    RepositorioDeNuvens,
    SpanDeTraco,
)
from .casos_de_uso import CasoDeUso


class _ComRepositorioDeNuvens(CasoDeUso):
    def __init__(
        self,
        *,
        rastreador: Rastreador,
        repositorio: RepositorioDeNuvens,
        relogio: Relogio | None = None,
        motor: MotorDeGeracaoDeNuvem | None = None,
    ) -> None:
        super().__init__(rastreador=rastreador)
        self._repositorio = repositorio
        self._relogio = relogio
        self._motor = motor

    def _agora(self):
        if self._relogio is None:  # pragma: no cover - erro de composição
            raise RuntimeError(f"{type(self).__name__} precisa de um relógio")
        return self._relogio.agora()

    def _exigir_motor(self) -> MotorDeGeracaoDeNuvem:
        """Sem motor composto, a assistência **falha alto** — nunca finge um resultado.

        É a mesma regra do sumidouro de traço da federação (APH-5.5): descobrir a ausência
        depois de responder seria descobrir tarde demais, e um resultado inventado aqui
        seria conteúdo sem origem entrando na nuvem.
        """
        if self._motor is None:
            raise RuntimeError(
                f"{type(self).__name__} precisa do motor de geração (porta "
                "MotorDeGeracaoDeNuvem); sem ele a assistência não existe neste serviço"
            )
        return self._motor

    def _carregar(self, dono: DonoDoProjeto, projeto_id: UUID) -> NuvemDeConflito:
        nuvem = self._repositorio.obter_nuvem(dono.inquilino_id, projeto_id)
        if nuvem is None:
            raise NaoEncontrado(str(projeto_id))
        return nuvem


class CriarProjetoNC(_ComRepositorioDeNuvens):
    """RF-02: cria a nuvem inteira — 5 entidades e 7 arestas — num ato atômico."""

    nome = "criar_projeto_nc"

    def executar(self, *, dono: DonoDoProjeto, nome: str, descricao_do_problema: str = ""):
        nuvem = novo_projeto_nc(
            id=uuid4(),
            dono=dono,
            nome=nome,
            descricao_do_problema=descricao_do_problema,
            em=self._agora(),
        )
        self._repositorio.salvar_nuvem(nuvem)
        return nuvem.projeto


class AbrirProjetoNC(_ComRepositorioDeNuvens):
    """A leitura do M3: topologia, racional, premissas, injeções e as duas costuras."""

    nome = "abrir_projeto_nc"

    def executar(self, *, dono: DonoDoProjeto, projeto_id: UUID) -> NuvemDeConflito:
        return self._carregar(dono, projeto_id)


class ValidarNuvem(_ComRepositorioDeNuvens):
    """RF-14: completude, avisos de formulação e pendências. Não muta, não grava."""

    nome = "validar_nuvem"

    def executar(
        self, *, dono: DonoDoProjeto, projeto_id: UUID, idioma: str = "pt"
    ) -> ValidacaoDaNuvem:
        return self._carregar(dono, projeto_id).validar(idioma)

    def anotar_resultado(self, span: SpanDeTraco, resultado: ValidacaoDaNuvem) -> None:
        for chave, valor in resultado.resumo().items():
            span.atributo(f"toc.{chave}", valor)


class _SobreNuvem(_ComRepositorioDeNuvens):
    """Carrega, age, grava. O `agir` é o que cada mutação implementa."""

    def executar(self, *, dono: DonoDoProjeto, projeto_id: UUID, **kw):
        nuvem = self._carregar(dono, projeto_id)
        resultado = self.agir(nuvem, em=self._agora(), **kw)
        self._repositorio.salvar_nuvem(nuvem)
        self._nuvem = nuvem
        return resultado

    def agir(self, nuvem: NuvemDeConflito, *, em, **kw):  # pragma: no cover - contrato
        raise NotImplementedError


class EditarEntidadeDaNuvem(_SobreNuvem):
    nome = "editar_entidade_da_nuvem"

    def agir(self, nuvem, *, em, papel: PapelDaEntidade, texto: str):
        self._papel = PapelDaEntidade(papel)
        return nuvem.editar_entidade(self._papel, texto, em=em)

    def anotar_resultado(self, span: SpanDeTraco, resultado) -> None:
        # O papel é vocabulário nosso; o TEXTO é da pessoa e não entra em span (ADR 0006).
        span.atributo("toc.papel", self._papel.value)


class EditarRacionalDaNuvem(_SobreNuvem):
    nome = "editar_racional_da_nuvem"

    def agir(self, nuvem, *, em, racional: str) -> str:
        return nuvem.editar_racional(racional, em=em)

    def anotar_resultado(self, span: SpanDeTraco, resultado: str) -> None:
        span.atributo("toc.racional_caracteres", len(resultado))


class DerivarNuvemDeUdes(_SobreNuvem):
    """INT-05 — o encadeamento M2 → M3, como caso de uso governado.

    Lê a ARA pelo `projeto_id` recebido e **grava uma nuvem nova**; o dono da nuvem vem do
    agregado de origem, nunca do pedido, e é isso que faz o isolamento por inquilino ser
    consequência do tipo, e não de disciplina de quem chama.
    """

    nome = "derivar_nuvem_de_udes"

    def __init__(
        self,
        *,
        rastreador: Rastreador,
        repositorio: RepositorioDaCosturaM2M3,
        relogio: Relogio | None = None,
    ) -> None:
        super().__init__(rastreador=rastreador, repositorio=repositorio, relogio=relogio)

    def executar(
        self,
        *,
        dono: DonoDoProjeto,
        projeto_id: UUID,
        no_ids: Sequence[UUID],
        nome: str,
    ) -> NuvemDeConflito:
        ara: ProjetoARA | None = self._repositorio.obter_ara(dono.inquilino_id, projeto_id)
        if ara is None:
            # Projeto de outro inquilino, inexistente, ou que não é uma ARA: a resposta é
            # a mesma, pelo mesmo motivo do M1 — distinguir vazaria a existência alheia.
            raise NaoEncontrado(str(projeto_id))
        self._udes = tuple(no_ids)
        nuvem = derivar_nuvem_de_udes(
            ara, no_ids=self._udes, id=uuid4(), nome=nome, em=self._agora()
        )
        self._repositorio.salvar_nuvem(nuvem)
        return nuvem

    def anotar_resultado(self, span: SpanDeTraco, resultado: NuvemDeConflito) -> None:
        span.atributo("toc.udes_de_origem", len(self._udes))
        span.atributo("toc.projeto_derivado", str(resultado.projeto.id))


# -- premissas -------------------------------------------------------------------------


class RegistrarPremissa(_SobreNuvem):
    nome = "registrar_premissa"

    def agir(
        self,
        nuvem,
        *,
        em,
        chave: ChaveDaAresta,
        texto: str,
        origem: str = ORIGEM_HUMANA,
        proposta_id: str | None = None,
    ) -> Premissa:
        self._chave = ChaveDaAresta(chave)
        return nuvem.registrar_premissa(
            self._chave, texto, em=em, origem=origem, proposta_id=proposta_id
        )

    def anotar_resultado(self, span: SpanDeTraco, resultado: Premissa) -> None:
        span.atributo("toc.aresta", self._chave.value)


class EditarPremissa(_SobreNuvem):
    nome = "editar_premissa"

    def agir(self, nuvem, *, em, premissa_id: UUID, texto: str) -> Premissa:
        return nuvem.editar_premissa(premissa_id, texto, em=em)


class ReordenarPremissas(_SobreNuvem):
    nome = "reordenar_premissas"

    def agir(self, nuvem, *, em, chave: ChaveDaAresta, ordem: Sequence[UUID]):
        return nuvem.reordenar_premissas(ChaveDaAresta(chave), tuple(ordem), em=em)


class DesafiarPremissa(_SobreNuvem):
    nome = "desafiar_premissa"

    def agir(self, nuvem, *, em, premissa_id: UUID, justificativa: str) -> Premissa:
        return nuvem.desafiar_premissa(
            premissa_id, justificativa=justificativa, em=em
        )


class RevigorarPremissa(_SobreNuvem):
    nome = "revigorar_premissa"

    def agir(self, nuvem, *, em, premissa_id: UUID) -> Premissa:
        return nuvem.revigorar_premissa(premissa_id, em=em)


class ArquivarPremissa(_SobreNuvem):
    """RF-15: devolve QUANTAS injeções foram arquivadas junto — e o span também diz."""

    nome = "arquivar_premissa"

    def agir(self, nuvem, *, em, premissa_id: UUID) -> int:
        return nuvem.arquivar_premissa(premissa_id, em=em)

    def anotar_resultado(self, span: SpanDeTraco, resultado: int) -> None:
        span.atributo("toc.injecoes_arquivadas", resultado)


# -- injeções ---------------------------------------------------------------------------


class RegistrarInjecao(_SobreNuvem):
    nome = "registrar_injecao"

    def agir(
        self,
        nuvem,
        *,
        em,
        premissa_id: UUID,
        texto: str,
        separacao: SeparacaoTRIZ | None = None,
        origem: str = ORIGEM_HUMANA,
        proposta_id: str | None = None,
    ) -> Injecao:
        return nuvem.registrar_injecao(
            premissa_id,
            texto,
            separacao=separacao,
            em=em,
            origem=origem,
            proposta_id=proposta_id,
        )

    def anotar_resultado(self, span: SpanDeTraco, resultado: Injecao) -> None:
        span.atributo("toc.status_da_injecao", resultado.status.value)


class EditarInjecao(_SobreNuvem):
    nome = "editar_injecao"

    def agir(self, nuvem, *, em, injecao_id: UUID, texto: str) -> Injecao:
        return nuvem.editar_injecao(injecao_id, texto, em=em)


class ClassificarInjecao(_SobreNuvem):
    nome = "classificar_injecao"

    def agir(
        self, nuvem, *, em, injecao_id: UUID, separacao: SeparacaoTRIZ | None
    ) -> Injecao:
        return nuvem.classificar_injecao(injecao_id, separacao, em=em)

    def anotar_resultado(self, span: SpanDeTraco, resultado: Injecao) -> None:
        span.atributo(
            "toc.separacao_triz", resultado.separacao.value if resultado.separacao else ""
        )


class MudarStatusDeInjecao(_SobreNuvem):
    """RN-08: a FSM é do domínio; o caso de uso só a atravessa e a anota no traço."""

    nome = "mudar_status_de_injecao"

    def agir(
        self,
        nuvem,
        *,
        em,
        injecao_id: UUID,
        status: StatusDeInjecao,
        justificativa: str = "",
    ) -> Injecao:
        return nuvem.mudar_status_de_injecao(
            injecao_id, StatusDeInjecao(status), justificativa=justificativa, em=em
        )

    def anotar_resultado(self, span: SpanDeTraco, resultado: Injecao) -> None:
        span.atributo("toc.status_da_injecao", resultado.status.value)
        span.atributo("toc.tem_semeadura", resultado.semeadura is not None)


# -- geração assistida -------------------------------------------------------------------


class GerarNuvemPorNarrativa(_ComRepositorioDeNuvens):
    """RF-21/RF-22: narrativa → estrutura validada. **Não grava nada.**

    A ordem importa e é a regra: chamar a porta, validar contra o esquema versionado,
    devolver o objeto tipado. Se a validação falhar, a exceção sobe e o agregado nunca foi
    tocado — falha fechada de verdade, não `try` em volta de uma escrita já feita.
    """

    nome = "gerar_nuvem_por_narrativa"

    def executar(
        self, *, dono: DonoDoProjeto, projeto_id: UUID, narrativa: str
    ) -> ResultadoDeGeracao:
        motor = self._exigir_motor()
        nuvem = self._carregar(dono, projeto_id)
        bruto = motor.gerar_nuvem(narrativa=narrativa, contexto=contexto_da_nuvem(nuvem))
        return ResultadoDeGeracao.de_dicionario(bruto)

    def anotar_resultado(self, span: SpanDeTraco, resultado: ResultadoDeGeracao) -> None:
        span.atributo("toc.versao_do_resultado", resultado.versao)
        span.atributo("toc.premissas_propostas", resultado.total_de_premissas)
        span.atributo("toc.injecoes_propostas", resultado.total_de_injecoes)


class SugerirPremissas(_ComRepositorioDeNuvens):
    """RF-26/INT-03: sugestões para UMA aresta. Rascunho: o agregado não é tocado."""

    nome = "sugerir_premissas"

    def executar(
        self,
        *,
        dono: DonoDoProjeto,
        projeto_id: UUID,
        chave: ChaveDaAresta,
        narrativa: str = "",
    ) -> tuple[PremissaProposta, ...]:
        motor = self._exigir_motor()
        nuvem = self._carregar(dono, projeto_id)
        self._chave = ChaveDaAresta(chave)
        brutas = motor.sugerir_premissas(
            aresta=self._chave.value,
            narrativa=narrativa,
            contexto=contexto_da_nuvem(nuvem),
        )
        return tuple(_premissa_proposta(bruta) for bruta in brutas)

    def anotar_resultado(self, span: SpanDeTraco, resultado) -> None:
        span.atributo("toc.aresta", self._chave.value)
        span.atributo("toc.premissas_propostas", len(resultado))


class SugerirInjecoes(_ComRepositorioDeNuvens):
    """RF-26/INT-04: sugestões para UMA premissa, com separação TRIZ quando couber."""

    nome = "sugerir_injecoes"

    def executar(
        self, *, dono: DonoDoProjeto, projeto_id: UUID, premissa_id: UUID
    ) -> tuple[InjecaoProposta, ...]:
        motor = self._exigir_motor()
        nuvem = self._carregar(dono, projeto_id)
        premissa = nuvem.premissa(premissa_id)
        brutas = motor.sugerir_injecoes(
            premissa=premissa.texto, contexto=contexto_da_nuvem(nuvem)
        )
        return tuple(_injecao_proposta(bruta) for bruta in brutas)

    def anotar_resultado(self, span: SpanDeTraco, resultado) -> None:
        span.atributo("toc.injecoes_propostas", len(resultado))


class AplicarGeracaoDeNuvem(_SobreNuvem):
    """RF-23/RF-25: o que a proposta ACEITA escreve, com a origem declarada nos eventos.

    O `proposta_id` não tem valor padrão de propósito: aplicar sem proposta é o caminho que
    a RN-05 fecha, e um argumento opcional seria exatamente esse caminho com outro nome.
    """

    nome = "aplicar_geracao_de_nuvem"

    def agir(
        self,
        nuvem,
        *,
        em,
        resultado: ResultadoDeGeracao,
        proposta_id: str,
    ):
        self._proposta_id = proposta_id
        if not isinstance(resultado, ResultadoDeGeracao):
            # Conteúdo de modelo só entra tipado: um dicionário cru aqui teria escapado da
            # validação de esquema, que é a linha que RF-22 e RNF-04 protegem.
            raise ResultadoDeGeracaoInvalido(
                "NAO_VALIDADO",
                "a aplicação recebe um ResultadoDeGeracao já validado, nunca dado cru",
            )
        return nuvem.aplicar_geracao(resultado, em=em, proposta_id=proposta_id)

    def anotar_resultado(self, span: SpanDeTraco, resultado) -> None:
        span.atributo("toc.proposta_id", self._proposta_id)
        span.atributo("toc.premissas_aplicadas", resultado.premissas)
        span.atributo("toc.injecoes_aplicadas", resultado.injecoes)


# -- apoio ------------------------------------------------------------------------------


def contexto_da_nuvem(nuvem: NuvemDeConflito) -> dict[str, Any]:
    """O estado atual que acompanha a narrativa (INT-02) — dado, nunca instrução.

    A fronteira do item 7 da constituição vale aqui: o que sai daqui é **conteúdo**, e
    quem o receber trata como camada não-confiável. Por isso o contexto é um dicionário
    de textos e contagens, sem verbo, sem pedido e sem nada que se pareça com comando.
    """
    return {
        "entidades": {papel.value: nuvem.texto(papel) for papel in PapelDaEntidade},
        "racional": nuvem.racional,
        "premissas": {
            chave.value: [p.texto for p in nuvem.premissas(chave)]
            for chave in ChaveDaAresta
        },
        "completude": list(nuvem.validar().completude),
    }


def _premissa_proposta(bruta: Mapping[str, Any]) -> PremissaProposta:
    return PremissaProposta(
        texto=str(bruta["texto"]),
        injecoes=tuple(_injecao_proposta(i) for i in bruta.get("injecoes") or ()),
    )


def _injecao_proposta(bruta: Mapping[str, Any]) -> InjecaoProposta:
    separacao = bruta.get("separacao")
    return InjecaoProposta(
        texto=str(bruta["texto"]),
        separacao=SeparacaoTRIZ(separacao) if separacao else None,
    )


__all__ = [
    "AbrirProjetoNC",
    "AplicarGeracaoDeNuvem",
    "ArquivarPremissa",
    "ClassificarInjecao",
    "CriarProjetoNC",
    "DerivarNuvemDeUdes",
    "DesafiarPremissa",
    "EditarEntidadeDaNuvem",
    "EditarInjecao",
    "EditarPremissa",
    "EditarRacionalDaNuvem",
    "GerarNuvemPorNarrativa",
    "MudarStatusDeInjecao",
    "RegistrarInjecao",
    "RegistrarPremissa",
    "ReordenarPremissas",
    "RevigorarPremissa",
    "SugerirInjecoes",
    "SugerirPremissas",
    "ValidarNuvem",
    "contexto_da_nuvem",
]
