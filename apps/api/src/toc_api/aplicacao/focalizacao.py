"""Casos de uso do M6 — a jornada dos cinco passos sobre as portas (spec 009).

Siglas, uma vez neste arquivo: **M6** — Focalização · **M1** — Núcleo de Diagramas
Lógicos · **TOC** — Teoria das Restrições · **ARA** — Árvore da Realidade Atual · **NC** —
Nuvem de Conflito · **ARF** — Árvore da Realidade Futura · **APR** — Árvore de
Pré-Requisitos · **AT** — Árvore de Transição · **OTel** — OpenTelemetry · **RF/RN/RNF** —
requisito funcional / regra de negócio / requisito não funcional.

Três coisas que este arquivo faz e que não são óbvias:

1. **Carregar, agir na raiz, gravar.** Todo caso de uso mutador carrega a análise pela
   porta do M6, chama a operação **na raiz do agregado** e grava pela mesma porta. Não
   existe caminho que toque o `Projeto` do M1 direto: quem tentasse receberia
   `MutacaoForaDaRaiz` do próprio domínio.

2. **A validação do vínculo é DAQUI, não do domínio** (RNF-04, plano 009 decisão 2). O
   domínio guarda o vínculo como referência opaca e só aplica a regra canônica (RN-06);
   quem pergunta "esse projeto existe? é deste inquilino? é da ferramenta declarada? está
   vivo?" é `VincularFerramenta`, no servidor. A separação é o que faz a suíte de domínio
   rodar offline e, ao mesmo tempo, impede um cartão de jornada apontando para o nada.

3. **O span carrega grandeza, nunca texto de pessoa** (ADR 0006, P5). Passo, tipo de
   restrição, contagem de pendências e de vínculos — sim. Descrição da restrição,
   justificativa, decisão, nota — nunca.

Camada pura: nenhum import de framework, banco ou cliente de inteligência artificial (P3).
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from ..dominio.erros import NaoEncontrado
from ..dominio.focalizacao import (
    FERRAMENTA_FOCALIZACAO,
    AnaliseDeFocalizacao,
    DecisaoHerdada,
    EntradaDaLinhaDoTempo,
    MapaDaJornada,
    NotaDePasso,
    PassoDeFocalizacao,
    Restricao,
    SistemaAnalisado,
    TipoDeFerramentaVinculada,
    TipoDePasso,
    TipoDeRestricao,
    VereditoDeHeranca,
    VinculoDeFerramenta,
    VinculoInvalido,
    mapa_da_jornada,
    mapa_do_ciclo,
    nova_analise_de_focalizacao,
)
from ..dominio.identidade import DonoDoProjeto
from ..dominio.portas import (
    Rastreador,
    Relogio,
    RepositorioDaJornada,
    RepositorioDeFocalizacao,
    SpanDeTraco,
)
from ..dominio.projeto import Projeto
from .casos_de_uso import CasoDeUso


class _ComRepositorioDeFocalizacao(CasoDeUso):
    """Carrega pela porta do M6, sempre pelo inquilino do dono."""

    def __init__(
        self,
        *,
        rastreador: Rastreador,
        repositorio: RepositorioDeFocalizacao | RepositorioDaJornada,
        relogio: Relogio | None = None,
    ) -> None:
        super().__init__(rastreador=rastreador)
        self._repositorio = repositorio
        self._relogio = relogio

    def _agora(self):
        if self._relogio is None:  # pragma: no cover - erro de composição
            raise RuntimeError(f"{type(self).__name__} precisa de um relógio")
        return self._relogio.agora()

    def _carregar(self, dono: DonoDoProjeto, projeto_id: UUID) -> AnaliseDeFocalizacao:
        analise = self._repositorio.obter_focalizacao(dono.inquilino_id, projeto_id)
        if analise is None:
            # Projeto de outro inquilino, inexistente, ou que não é uma análise de
            # focalização: a resposta é a mesma, pelo mesmo motivo do M1 — distinguir
            # vazaria a existência alheia.
            raise NaoEncontrado(str(projeto_id))
        return analise


class _SobreAAnalise(_ComRepositorioDeFocalizacao):
    """Carregar → agir na raiz → gravar. O molde de todo caso de uso mutador do M6."""

    def executar(self, *, dono: DonoDoProjeto, projeto_id: UUID, **kw):
        analise = self._carregar(dono, projeto_id)
        resultado = self.agir(analise, em=self._agora(), **kw)
        self._repositorio.salvar_focalizacao(analise)
        self._analise = analise
        return resultado

    def agir(self, analise: AnaliseDeFocalizacao, *, em, **kw):  # pragma: no cover
        raise NotImplementedError

    def anotar_resultado(self, span: SpanDeTraco, resultado: Any) -> None:
        """O estado da jornada DEPOIS da mutação — grandeza, nunca texto (ADR 0006)."""
        analise = getattr(self, "_analise", None)
        if analise is None:  # pragma: no cover - só se `executar` for sobrescrito
            return
        for chave, valor in mapa_da_jornada(analise).resumo().items():
            if chave in ("estado", "passo_atual"):
                span.atributo(f"toc.{chave}", str(valor))
            elif isinstance(valor, bool):
                span.atributo(f"toc.{chave}", valor)
            elif isinstance(valor, int):
                span.atributo(f"toc.{chave}", valor)


# ---------------------------------------------------------------------------------------
# RF-01..RF-04 — criar, abrir, listar
# ---------------------------------------------------------------------------------------


class CriarAnaliseDeFocalizacao(_ComRepositorioDeFocalizacao):
    """RF-01/RF-02: a análise nasce com o primeiro ciclo aberto em `identificar`."""

    nome = "criar_analise_de_focalizacao"

    def executar(
        self,
        *,
        dono: DonoDoProjeto,
        nome: str,
        sistema: str,
        descricao_do_sistema: str = "",
        analise_id: UUID | None = None,
    ) -> Projeto:
        analise = nova_analise_de_focalizacao(
            id=analise_id or uuid4(),
            dono=dono,
            nome=nome,
            sistema=SistemaAnalisado(nome=sistema, descricao=descricao_do_sistema),
            em=self._agora(),
        )
        self._repositorio.salvar_focalizacao(analise)
        return analise.projeto


class AbrirAnaliseDeFocalizacao(_ComRepositorioDeFocalizacao):
    """Leitura do agregado inteiro — ciclos, passos, restrições, vínculos e herança."""

    nome = "abrir_analise_de_focalizacao"

    def executar(self, *, dono: DonoDoProjeto, projeto_id: UUID) -> AnaliseDeFocalizacao:
        return self._carregar(dono, projeto_id)


class MapaDaJornadaDaAnalise(_ComRepositorioDeFocalizacao):
    """RF-12: o mapa do ciclo aberto. Leitura pura — não grava evento nenhum.

    `ciclo_id` opcional abre um ciclo FECHADO em modo somente leitura (RF-17/RI-04).
    """

    nome = "mapa_da_jornada"

    def executar(
        self, *, dono: DonoDoProjeto, projeto_id: UUID, ciclo_id: UUID | None = None
    ) -> MapaDaJornada:
        analise = self._carregar(dono, projeto_id)
        if ciclo_id is None:
            return mapa_da_jornada(analise)
        return mapa_do_ciclo(analise, ciclo_id)

    def anotar_resultado(self, span: SpanDeTraco, resultado: MapaDaJornada) -> None:
        for chave, valor in resultado.resumo().items():
            span.atributo(f"toc.{chave}", str(valor) if isinstance(valor, str) else valor)


class LinhaDoTempoDaAnalise(_ComRepositorioDeFocalizacao):
    """RF-17: os ciclos em ordem, com restrição, datas e desfecho."""

    nome = "linha_do_tempo_da_analise"

    def executar(
        self, *, dono: DonoDoProjeto, projeto_id: UUID
    ) -> tuple[EntradaDaLinhaDoTempo, ...]:
        return self._carregar(dono, projeto_id).linha_do_tempo()

    def anotar_resultado(self, span: SpanDeTraco, resultado) -> None:
        span.atributo("toc.ciclos", len(resultado))


@dataclass(frozen=True, slots=True)
class LinhaDaListagem:
    """RF-03/RI-07: passo atual e restrição vigente como colunas de primeira classe."""

    projeto_id: UUID
    nome: str
    sistema: str
    ciclo: int
    passo_atual: TipoDePasso
    restricao: str | None
    tipo_de_restricao: TipoDeRestricao | None
    pendencias: int
    herancas_pendentes: int
    alterado_em: Any


class ListarAnalisesDeFocalizacao(_ComRepositorioDeFocalizacao):
    """RF-03: a listagem que mostra ONDE cada análise está, sem abrir uma a uma.

    Ela carrega cada análise para computar o passo atual — e isso é uma consulta por
    análise, declarada e não escondida. Na escala da v1 (dezenas de análises por
    inquilino) é barato; se um dia deixar de ser, o caminho é uma projeção de leitura no
    adaptador, não um campo desnormalizado no agregado, que envelheceria em silêncio.

    Exige a porta composta `RepositorioDaJornada`: listar é do M1 (`listar`), abrir é do
    M6 (`obter_focalizacao`).
    """

    nome = "listar_analises_de_focalizacao"

    def executar(
        self, *, dono: DonoDoProjeto, incluir_excluidas: bool = False
    ) -> list[LinhaDaListagem]:
        projetos = [
            p
            for p in self._repositorio.listar(
                dono.inquilino_id, incluir_excluidos=incluir_excluidas
            )
            if p.ferramenta == FERRAMENTA_FOCALIZACAO
        ]
        linhas: list[LinhaDaListagem] = []
        for projeto in projetos:
            analise = self._repositorio.obter_focalizacao(dono.inquilino_id, projeto.id)
            if analise is None:  # pragma: no cover - só com adaptador incoerente
                continue
            mapa = mapa_da_jornada(analise)
            linhas.append(
                LinhaDaListagem(
                    projeto_id=projeto.id,
                    nome=projeto.nome,
                    sistema=analise.sistema.nome,
                    ciclo=mapa.ordem,
                    passo_atual=mapa.passo_atual,
                    restricao=None if mapa.restricao is None else mapa.restricao.descricao,
                    tipo_de_restricao=None if mapa.restricao is None else mapa.restricao.tipo,
                    pendencias=sum(len(p.pendencias) for p in mapa.passos),
                    herancas_pendentes=mapa.herancas_pendentes,
                    alterado_em=projeto.alterado_em,
                )
            )
        return linhas

    def anotar_resultado(self, span: SpanDeTraco, resultado: list[LinhaDaListagem]) -> None:
        span.atributo("toc.analises", len(resultado))


class ExcluirAnaliseDeFocalizacao(_SobreAAnalise):
    """RF-04: exclusão suave do M1 — ciclos, passos, restrições e vínculos juntos."""

    nome = "excluir_analise_de_focalizacao"

    def agir(self, analise: AnaliseDeFocalizacao, *, em) -> AnaliseDeFocalizacao:
        analise.excluir(em=em)
        return analise

    def anotar_resultado(self, span: SpanDeTraco, resultado) -> None:
        span.atributo("toc.excluida", True)


class RestaurarAnaliseDeFocalizacao(_SobreAAnalise):
    """US-02: volta com ciclos, passos, restrições e vínculos intactos."""

    nome = "restaurar_analise_de_focalizacao"

    def agir(self, analise: AnaliseDeFocalizacao, *, em) -> AnaliseDeFocalizacao:
        analise.restaurar(em=em)
        return analise


# ---------------------------------------------------------------------------------------
# RF-05..RF-08 — a restrição
# ---------------------------------------------------------------------------------------


class RegistrarRestricao(_SobreAAnalise):
    """RF-05/RF-06: a entidade que dá nome à teoria, com autoria por evento."""

    nome = "registrar_restricao"

    def agir(
        self,
        analise: AnaliseDeFocalizacao,
        *,
        em,
        descricao: str,
        tipo: TipoDeRestricao | str,
        justificativa: str,
        autor: str,
        origem=None,
    ) -> Restricao:
        return analise.registrar_restricao(
            descricao=descricao,
            tipo=tipo,
            justificativa=justificativa,
            autor=autor,
            origem=origem,
            em=em,
        )

    def anotar_resultado(self, span: SpanDeTraco, resultado: Restricao) -> None:
        # Tipo e presença de origem são vocabulário nosso; a descrição e a justificativa
        # são texto de quem escreveu, e não entram em span nem em log (ADR 0006).
        span.atributo("toc.tipo_de_restricao", resultado.tipo.value)
        span.atributo("toc.tem_origem", resultado.origem is not None)
        super().anotar_resultado(span, resultado)


class EditarRestricao(_SobreAAnalise):
    """RF-07: descrição e justificativa. **Sem `tipo`** — trocar alvo é recomeço (RN-03).

    A assinatura não tem por onde receber o tipo, de propósito: a regra vira
    impossibilidade de chamada em vez de uma recusa que alguém possa esquecer de escrever.
    """

    nome = "editar_restricao"

    def agir(
        self,
        analise: AnaliseDeFocalizacao,
        *,
        em,
        descricao: str | None = None,
        justificativa: str | None = None,
    ) -> Restricao:
        return analise.editar_restricao(
            descricao=descricao, justificativa=justificativa, em=em
        )


# ---------------------------------------------------------------------------------------
# RF-09..RF-11 — avanço, reabertura e notas
# ---------------------------------------------------------------------------------------


class ConcluirPasso(_SobreAAnalise):
    """RF-09: o avanço é ato explícito, com autor, data e a decisão que o encerra."""

    nome = "concluir_passo"

    def agir(
        self,
        analise: AnaliseDeFocalizacao,
        *,
        em,
        passo: TipoDePasso | str,
        decisao: str,
        autor: str,
    ) -> PassoDeFocalizacao:
        self._passo = TipoDePasso(passo)
        return analise.concluir_passo(passo, decisao=decisao, autor=autor, em=em)

    def anotar(self, span: SpanDeTraco, **kwargs) -> None:
        super().anotar(span, **kwargs)
        if kwargs.get("passo") is not None:
            span.atributo("toc.passo", str(TipoDePasso(kwargs["passo"]).value))


class ReabrirPassoAnterior(_SobreAAnalise):
    """RF-10: o passo anterior volta — sem apagar a decisão que o havia concluído."""

    nome = "reabrir_passo_anterior"

    def agir(
        self, analise: AnaliseDeFocalizacao, *, em, justificativa: str, autor: str
    ) -> PassoDeFocalizacao:
        return analise.reabrir_passo_anterior(
            justificativa=justificativa, autor=autor, em=em
        )

    def anotar_resultado(self, span: SpanDeTraco, resultado: PassoDeFocalizacao) -> None:
        span.atributo("toc.passo_reaberto", resultado.tipo.value)
        span.atributo("toc.decisoes_no_historico", len(resultado.decisoes))
        super().anotar_resultado(span, resultado)


class AnotarPasso(_SobreAAnalise):
    """RF-11: nota acumulável com autoria — anotar não conclui e não avança."""

    nome = "anotar_passo"

    def agir(
        self,
        analise: AnaliseDeFocalizacao,
        *,
        em,
        passo: TipoDePasso | str,
        texto: str,
        autor: str,
    ) -> NotaDePasso:
        return analise.anotar_passo(passo, texto=texto, autor=autor, em=em)

    def anotar(self, span: SpanDeTraco, **kwargs) -> None:
        super().anotar(span, **kwargs)
        if kwargs.get("passo") is not None:
            span.atributo("toc.passo", str(TipoDePasso(kwargs["passo"]).value))


# ---------------------------------------------------------------------------------------
# RF-14 / RNF-04 — os vínculos de ferramenta, validados NO SERVIDOR
# ---------------------------------------------------------------------------------------


class EstadoDoVinculo(str, Enum):
    """RNF-04: o estado do projeto vinculado, sempre legível — nunca erro opaco."""

    ATIVO = "ativo"
    ARQUIVADO = "arquivado"
    AUSENTE = "ausente"


@dataclass(frozen=True, slots=True)
class VinculoResolvido:
    """O cartão do RI-03: tipo, nome do projeto, estado e a navegação direta."""

    passo: TipoDePasso
    vinculo_id: UUID
    ferramenta: str
    projeto_id: UUID
    papel: str
    canonico: bool
    justificativa: str
    estado: EstadoDoVinculo
    nome: str
    legenda: str


#: A legenda de cada estado — texto do domínio da aplicação, e não da tela: ela viaja no
#: corpo da resposta para que o cliente não reconstrua a frase por `if` (§A.7 do Anexo A).
LEGENDA_DO_VINCULO: dict[EstadoDoVinculo, str] = {
    EstadoDoVinculo.ATIVO: "projeto ativo",
    EstadoDoVinculo.ARQUIVADO: (
        "referência a projeto arquivado — o vínculo continua, e restaurar o projeto o "
        "devolve inteiro"
    ),
    EstadoDoVinculo.AUSENTE: (
        "o projeto referenciado não existe mais para este inquilino; o vínculo fica "
        "declarado como pendente em vez de sumir em silêncio"
    ),
}


class _ComProjetosEAnalises(_SobreAAnalise):
    """Precisa das DUAS portas: a do M6 para a análise, a do M1 para o projeto de destino."""

    def _projeto_alvo(self, dono: DonoDoProjeto, alvo_id: UUID) -> Projeto | None:
        return self._repositorio.obter(dono.inquilino_id, alvo_id)


class VincularFerramenta(_ComProjetosEAnalises):
    """RF-14 + RNF-04: o vínculo existe, é do inquilino, é da ferramenta e está vivo.

    A ordem das checagens é a ordem da fronteira: primeiro "existe para você?" (que
    responde igual para inexistente e para alheio, como todo o resto do M1), depois "é o
    que você disse que é?", depois "está vivo?". Só então o domínio aplica a RN-06.
    """

    nome = "vincular_ferramenta"

    def executar(
        self,
        *,
        dono: DonoDoProjeto,
        projeto_id: UUID,
        passo: TipoDePasso | str,
        tipo: TipoDeFerramentaVinculada | str,
        alvo_id: UUID,
        papel: str = "",
        justificativa: str = "",
    ) -> VinculoDeFerramenta:
        analise = self._carregar(dono, projeto_id)
        alvo = self._projeto_alvo(dono, alvo_id)
        if alvo is None:
            raise VinculoInvalido(
                "alvo_inexistente",
                f"o projeto {alvo_id} não existe para este inquilino",
            )
        declarada = TipoDeFerramentaVinculada(tipo)
        if alvo.ferramenta != declarada.value:
            raise VinculoInvalido(
                "ferramenta_divergente",
                f"o vínculo declara {declarada.value!r} e o projeto {alvo_id} é da "
                f"ferramenta {alvo.ferramenta!r}",
            )
        if alvo.excluido_em is not None:
            raise VinculoInvalido(
                "alvo_arquivado",
                f"o projeto {alvo_id} está arquivado; restaure-o antes de vinculá-lo",
            )

        vinculo = analise.vincular_ferramenta(
            passo,
            tipo=declarada,
            projeto_id=alvo_id,
            papel=papel,
            justificativa=justificativa,
            em=self._agora(),
        )
        self._repositorio.salvar_focalizacao(analise)
        self._analise = analise
        return vinculo

    def anotar_resultado(self, span: SpanDeTraco, resultado: VinculoDeFerramenta) -> None:
        span.atributo("toc.ferramenta_vinculada", resultado.tipo.value)
        span.atributo("toc.vinculo_canonico", resultado.canonico)
        super().anotar_resultado(span, resultado)


class RemoverVinculo(_SobreAAnalise):
    nome = "remover_vinculo"

    def agir(
        self, analise: AnaliseDeFocalizacao, *, em, passo: TipoDePasso | str, vinculo_id: UUID
    ) -> None:
        analise.remover_vinculo(passo, vinculo_id, em=em)


class ResolverVinculos(_ComRepositorioDeFocalizacao):
    """RNF-04: o estado de cada projeto vinculado — ativo, arquivado ou ausente.

    Leitura pura: não grava nada. Ela é o que transforma "o vínculo é navegável nos dois
    sentidos" em algo que a tela consegue desenhar sem inventar estado, e é o que impede o
    "dado órfão silencioso" que o requisito nomeia.
    """

    nome = "resolver_vinculos"

    def executar(
        self, *, dono: DonoDoProjeto, projeto_id: UUID
    ) -> list[VinculoResolvido]:
        analise = self._carregar(dono, projeto_id)
        resolvidos: list[VinculoResolvido] = []
        for passo, vinculo in analise.vinculos_do_projeto_todos():
            alvo = self._repositorio.obter(dono.inquilino_id, vinculo.projeto_id)
            if alvo is None:
                estado, nome = EstadoDoVinculo.AUSENTE, ""
            elif alvo.excluido_em is not None:
                estado, nome = EstadoDoVinculo.ARQUIVADO, alvo.nome
            else:
                estado, nome = EstadoDoVinculo.ATIVO, alvo.nome
            resolvidos.append(
                VinculoResolvido(
                    passo=passo,
                    vinculo_id=vinculo.id,
                    ferramenta=vinculo.tipo.value,
                    projeto_id=vinculo.projeto_id,
                    papel=vinculo.papel,
                    canonico=vinculo.canonico,
                    justificativa=vinculo.justificativa,
                    estado=estado,
                    nome=nome,
                    legenda=LEGENDA_DO_VINCULO[estado],
                )
            )
        return resolvidos

    def anotar_resultado(self, span: SpanDeTraco, resultado: list[VinculoResolvido]) -> None:
        span.atributo("toc.vinculos", len(resultado))
        span.atributo(
            "toc.vinculos_degradados",
            sum(1 for v in resultado if v.estado is not EstadoDoVinculo.ATIVO),
        )


class ReferenciasDaFerramenta(_ComRepositorioDeFocalizacao):
    """L-03: a navegação de volta — quais análises citam este projeto de ferramenta.

    Resolve por **consulta ao M6**, sem campo novo em M2–M4: é o que evita o acoplamento
    reverso que obrigaria a ARA a saber que a focalização existe.
    """

    nome = "referencias_da_ferramenta"

    def executar(
        self, *, dono: DonoDoProjeto, alvo_id: UUID
    ) -> list[tuple[Projeto, TipoDePasso, VinculoDeFerramenta]]:
        achados: list[tuple[Projeto, TipoDePasso, VinculoDeFerramenta]] = []
        for projeto in self._repositorio.listar(dono.inquilino_id):
            if projeto.ferramenta != FERRAMENTA_FOCALIZACAO:
                continue
            analise = self._repositorio.obter_focalizacao(dono.inquilino_id, projeto.id)
            if analise is None:  # pragma: no cover - só com adaptador incoerente
                continue
            for passo, vinculo in analise.vinculos_do_projeto(alvo_id):
                achados.append((projeto, passo, vinculo))
        return achados

    def anotar_resultado(self, span: SpanDeTraco, resultado: list) -> None:
        span.atributo("toc.referencias", len(resultado))


# ---------------------------------------------------------------------------------------
# RF-15/RF-16 — recomeço e anti-inércia
# ---------------------------------------------------------------------------------------


class JulgarDecisaoHerdada(_SobreAAnalise):
    """RN-05: manter é decisão tão explícita quanto revogar, e as duas têm justificativa."""

    nome = "julgar_decisao_herdada"

    def agir(
        self,
        analise: AnaliseDeFocalizacao,
        *,
        em,
        decisao_id: UUID,
        veredito: VereditoDeHeranca | str,
        justificativa: str,
        autor: str,
    ) -> DecisaoHerdada:
        return analise.julgar_heranca(
            decisao_id,
            veredito=veredito,
            justificativa=justificativa,
            autor=autor,
            em=em,
        )

    def anotar_resultado(self, span: SpanDeTraco, resultado: DecisaoHerdada) -> None:
        span.atributo("toc.veredito", resultado.veredito.value)
        span.atributo("toc.passo_de_origem", resultado.passo.value)
        super().anotar_resultado(span, resultado)


class Recomecar(_SobreAAnalise):
    """RF-15: fecha o ciclo, abre o próximo — e **nada** do anterior é apagado (RN-04)."""

    nome = "recomecar"

    def agir(self, analise: AnaliseDeFocalizacao, *, em):
        fechado = analise.ciclo_aberto.ordem
        novo = analise.recomecar(em=em)
        self._fechado = fechado
        return novo

    def anotar_resultado(self, span: SpanDeTraco, resultado) -> None:
        span.atributo("toc.ciclo_fechado", getattr(self, "_fechado", 0))
        span.atributo("toc.ciclo_aberto", resultado.ordem)
        span.atributo("toc.herancas_pendentes", len(resultado.herancas_pendentes()))


# ---------------------------------------------------------------------------------------
# RF-19 — a única assistência do módulo, e ela nasce PROPOSTA
# ---------------------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class CandidataARestricao:
    """Uma candidata a restrição, derivada da Árvore da Realidade Atual vinculada.

    `racional` é montado por **função pura sobre o grafo** — quantos Efeitos Indesejáveis
    aquela entrada alcança e que fração da dor percebida ela explica. Nenhum provedor de
    modelo é chamado daqui (ADR 0007): quem fala com modelo é a fundação, pelo catálogo
    governado, e o que este caso de uso entrega é o material sobre o qual ela falaria.
    """

    no_id: UUID
    titulo: str
    racional: str
    udes_alcancados: int
    fracao: float


class SugerirRestricao(_ComRepositorioDeFocalizacao):
    """RF-19: candidatas a partir das causas raiz da ARA vinculada ao passo `identificar`.

    **Não grava nada.** O resultado é rascunho até virar `action_proposal` aceita — e é o
    caso de uso `RegistrarRestricao`, chamado pelo executor do catálogo depois do gate
    humano, que escreve. Recusar a proposta deixa a análise byte a byte intacta, e há
    teste medindo isso.

    Sem ARA vinculada, devolve lista vazia: **a ferramenta ajuda, nunca condiciona**
    (RF-06). A jornada guiada é completa por construção com o catálogo ausente (RF-20).
    """

    nome = "sugerir_restricao"

    def executar(
        self, *, dono: DonoDoProjeto, projeto_id: UUID, ara_projeto_id: UUID | None = None
    ) -> list[CandidataARestricao]:
        analise = self._carregar(dono, projeto_id)
        alvo = ara_projeto_id or self._ara_do_passo_identificar(analise)
        if alvo is None:
            return []
        obter_ara = getattr(self._repositorio, "obter_ara", None)
        if obter_ara is None:  # pragma: no cover - composição sem o M2
            return []
        ara = obter_ara(dono.inquilino_id, alvo)
        if ara is None or ara.projeto.excluido_em is not None:
            return []

        # `analisar` do domínio da ARA emite evento na memória do projeto; aqui a leitura
        # é sobre a cópia carregada e NÃO é gravada — sugerir não escreve na ARA.
        relatorio = ara.analisar(em=self._agora())
        candidatas: list[CandidataARestricao] = []
        for alcance in sorted(
            relatorio.alcances, key=lambda a: (-a.fracao, str(a.no_id))
        ):
            if not alcance.udes_alcancados:
                continue
            titulo = ara.projeto.no(alcance.no_id).titulo
            candidatas.append(
                CandidataARestricao(
                    no_id=alcance.no_id,
                    titulo=titulo,
                    racional=(
                        f"entrada da árvore que alcança {len(alcance.udes_alcancados)} de "
                        f"{relatorio.total_de_udes} Efeito(s) Indesejável(is) "
                        f"({alcance.fracao:.0%} da dor percebida)"
                        + (
                            " — está num ciclo causal e ficou fora do cálculo de causa "
                            "raiz candidata (RF-29)"
                            if alcance.no_id in relatorio.nos_em_ciclo
                            else ""
                        )
                    ),
                    udes_alcancados=len(alcance.udes_alcancados),
                    fracao=alcance.fracao,
                )
            )
        return candidatas

    @staticmethod
    def _ara_do_passo_identificar(analise: AnaliseDeFocalizacao) -> UUID | None:
        passo = analise.ciclo_aberto.passo(TipoDePasso.IDENTIFICAR)
        for vinculo in passo.vinculos:
            if vinculo.tipo is TipoDeFerramentaVinculada.ARA:
                return vinculo.projeto_id
        return None

    def anotar_resultado(self, span: SpanDeTraco, resultado: list) -> None:
        span.atributo("toc.candidatas", len(resultado))


__all__ = [
    "LEGENDA_DO_VINCULO",
    "CandidataARestricao",
    "AbrirAnaliseDeFocalizacao",
    "AnotarPasso",
    "ConcluirPasso",
    "CriarAnaliseDeFocalizacao",
    "EditarRestricao",
    "EstadoDoVinculo",
    "ExcluirAnaliseDeFocalizacao",
    "JulgarDecisaoHerdada",
    "LinhaDaListagem",
    "LinhaDoTempoDaAnalise",
    "ListarAnalisesDeFocalizacao",
    "MapaDaJornadaDaAnalise",
    "ReabrirPassoAnterior",
    "ReferenciasDaFerramenta",
    "Recomecar",
    "RegistrarRestricao",
    "RemoverVinculo",
    "ResolverVinculos",
    "RestaurarAnaliseDeFocalizacao",
    "SugerirRestricao",
    "VincularFerramenta",
    "VinculoResolvido",
]
