"""Casos de uso das três árvores do M4 — ARF, APR e AT — sobre as portas (spec 008).

Siglas, uma vez neste arquivo: **M4** — Árvores de Futuro e Implementação · **ARF** —
Árvore da Realidade Futura · **APR** — Árvore de Pré-Requisitos · **AT** — Árvore de
Transição · **OI** — Objetivo Intermediário · **UDE** — Efeito Indesejável · **TOC** —
Teoria das Restrições · **OTel** — OpenTelemetry · **RF/RN/RNF** — requisito funcional /
regra de negócio / requisito não funcional.

Três coisas que este arquivo faz e que não são óbvias:

1. **Carregar, agir, gravar — e a raiz no meio.** Todo caso de uso mutador carrega o
   agregado pela porta da ferramenta, chama a operação **na raiz** e grava pela mesma
   porta. Não existe caminho que toque o `Projeto` do M1 direto: quem tentasse receberia
   `MutacaoForaDaRaiz` do próprio domínio.
2. **O span carrega grandeza, nunca texto de pessoa** (ADR 0006, P5). Papel, contagem,
   identificador de referência — sim. Enunciado de obstáculo, justificativa de ramo
   aceito, ação de passo — nunca.
3. **Verificar e sequenciar GRAVAM.** As duas acrescentam evento à memória do projeto
   (RF-13, RF-26), então exigem `toc:write` na política — chamá-las de leitura porque "só
   leem o grafo" seria a exceção por onde a regra vaza. É a mesma decisão já tomada para
   `AnalisarArvore` no M2.

Camada pura: nenhum import de framework, banco ou cliente de inteligência artificial (P3).
"""
from __future__ import annotations

from typing import Any, Sequence
from uuid import UUID, uuid4

from ..dominio.apr import (
    ElipseDeSimultaneidade,
    LinhaDoResumo,
    PapelNaAPR,
    ParObstaculoOI,
    ProjetoAPR,
    Sequenciamento,
    novo_projeto_apr,
)
from ..dominio.arf import (
    EspelhoDeUde,
    EstadoDoRamo,
    PapelNaARF,
    ProjetoARF,
    RamoNegativo,
    VerificacaoDaARF,
    novo_projeto_arf,
)
from ..dominio.at import FichaDePasso, ProjetoAT, StatusDoPasso, novo_projeto_at
from ..dominio.erros import NaoEncontrado
from ..dominio.grafo import ArestaCausal, No
from ..dominio.identidade import DonoDoProjeto
from ..dominio.portas import (
    Rastreador,
    Relogio,
    RepositorioDeAPR,
    RepositorioDeARF,
    RepositorioDeAT,
    SpanDeTraco,
)
from ..dominio.projeto import Projeto
from ..dominio.suficiencia import ConectorE, EstadoDoExame, Exame
from ..dominio.valores import PosicaoNoCanvas
from ..dominio.verbalizacao import VerbalizacaoAvaliada
from .casos_de_uso import CasoDeUso


class _ComRepositorio(CasoDeUso):
    """Carrega pela porta da ferramenta, sempre pelo inquilino do dono."""

    def __init__(
        self,
        *,
        rastreador: Rastreador,
        repositorio: Any,
        relogio: Relogio | None = None,
    ) -> None:
        super().__init__(rastreador=rastreador)
        self._repositorio = repositorio
        self._relogio = relogio

    def _agora(self):
        if self._relogio is None:  # pragma: no cover - erro de composição
            raise RuntimeError(f"{type(self).__name__} precisa de um relógio")
        return self._relogio.agora()


# ---------------------------------------------------------------------------------------
# E4.1 · Árvore da Realidade Futura
# ---------------------------------------------------------------------------------------


class _ComARF(_ComRepositorio):
    def _carregar(self, dono: DonoDoProjeto, projeto_id: UUID) -> ProjetoARF:
        arf = self._repositorio.obter_arf(dono.inquilino_id, projeto_id)
        if arf is None:
            # Projeto de outro inquilino, inexistente, ou que não é uma ARF: a resposta é a
            # mesma, pelo mesmo motivo do M1 — distinguir vazaria a existência alheia.
            raise NaoEncontrado(str(projeto_id))
        return arf


class CriarProjetoARF(_ComARF):
    """RF-01: cria a ARF do zero. Sem cadeia vinculada, o espelho de UDE não existe (RF-07)."""

    nome = "criar_projeto_arf"

    def executar(
        self,
        *,
        dono: DonoDoProjeto,
        nome: str,
        descricao_do_problema: str = "",
        udes_da_cadeia: Sequence[UUID] = (),
    ) -> Projeto:
        arf = novo_projeto_arf(
            id=uuid4(),
            dono=dono,
            nome=nome,
            descricao_do_problema=descricao_do_problema,
            udes_da_cadeia=tuple(udes_da_cadeia),
            em=self._agora(),
        )
        self._repositorio.salvar_arf(arf)
        return arf.projeto


class AbrirProjetoARF(_ComARF):
    nome = "abrir_projeto_arf"

    def executar(self, *, dono: DonoDoProjeto, projeto_id: UUID) -> ProjetoARF:
        return self._carregar(dono, projeto_id)


class _SobreARF(_ComARF):
    """Carrega, age pela raiz, grava. O `agir` é o que cada mutação implementa."""

    def executar(self, *, dono: DonoDoProjeto, projeto_id: UUID, **kw):
        arf = self._carregar(dono, projeto_id)
        resultado = self.agir(arf, em=self._agora(), **kw)
        self._repositorio.salvar_arf(arf)
        return resultado

    def agir(self, arf: ProjetoARF, *, em, **kw):  # pragma: no cover - contrato
        raise NotImplementedError


class AdicionarNoDaARF(_SobreARF):
    """RF-02: o papel entra na chamada — injeção e efeito futuro nascem distintos."""

    nome = "adicionar_no_da_arf"

    def agir(
        self,
        arf,
        *,
        em,
        papel: PapelNaARF,
        titulo: str,
        descricao: str = "",
        posicao: PosicaoNoCanvas | None = None,
        proposta_id: str | None = None,
    ) -> No:
        self._papel = PapelNaARF(papel)
        self._proposta_id = proposta_id
        criar = (
            arf.adicionar_injecao
            if self._papel is PapelNaARF.INJECAO
            else arf.adicionar_efeito_futuro
        )
        return criar(titulo=titulo, descricao=descricao, posicao=posicao, em=em)

    def anotar_resultado(self, span: SpanDeTraco, resultado: No) -> None:
        # O papel é vocabulário nosso; o TÍTULO é da pessoa e não entra em span (ADR 0006).
        span.atributo("toc.papel", self._papel.value)
        # RF-43/RNF-03: quando o elemento nasce de uma proposta aceita, o traço diz de
        # QUAL proposta — é o que torna a mutação vinda de modelo distinguível de edição
        # humana um mês depois.
        if self._proposta_id:
            span.atributo("toc.proposta_id", self._proposta_id)


class EditarNoDaARF(_SobreARF):
    nome = "editar_no_da_arf"

    def agir(self, arf, *, em, no_id: UUID, titulo=None, descricao=None) -> No:
        return arf.editar_no(no_id, titulo=titulo, descricao=descricao, em=em)


class MoverNoDaARF(_SobreARF):
    nome = "mover_no_da_arf"

    def agir(self, arf, *, em, no_id: UUID, posicao: PosicaoNoCanvas) -> No:
        return arf.mover_no(no_id, posicao, em=em)


class ExcluirNoDaARF(_SobreARF):
    nome = "excluir_no_da_arf"

    def agir(self, arf, *, em, no_id: UUID) -> list[UUID]:
        return arf.excluir_no(no_id, em=em)

    def anotar_resultado(self, span: SpanDeTraco, resultado: list[UUID]) -> None:
        span.atributo("toc.arestas_removidas", len(resultado))


class MudarPapelNaARF(_SobreARF):
    nome = "mudar_papel_na_arf"

    def agir(self, arf, *, em, no_id: UUID, papel: PapelNaARF) -> No:
        self._papel = PapelNaARF(papel)
        return arf.mudar_papel(no_id, self._papel, em=em)

    def anotar_resultado(self, span: SpanDeTraco, resultado: No) -> None:
        span.atributo("toc.papel", self._papel.value)


class LigarNaARF(_SobreARF):
    """RF-03: aresta de suficiência — e o exame de elo nasce com ela."""

    nome = "ligar_na_arf"

    def agir(self, arf, *, em, origem_id: UUID, destino_id: UUID, rotulo: str = "") -> ArestaCausal:
        return arf.ligar(origem_id, destino_id, rotulo=rotulo, em=em)


class ExcluirArestaDaARF(_SobreARF):
    nome = "excluir_aresta_da_arf"

    def agir(self, arf, *, em, aresta_id: UUID) -> None:
        arf.excluir_aresta(aresta_id, em=em)


class ExaminarEloDaARF(_SobreARF):
    nome = "examinar_elo_da_arf"

    def agir(self, arf, *, em, aresta_id: UUID, estado: EstadoDoExame, reserva: str = "") -> Exame:
        return arf.examinar_elo(aresta_id, EstadoDoExame(estado), reserva=reserva, em=em)

    def anotar_resultado(self, span: SpanDeTraco, resultado: Exame) -> None:
        span.atributo("toc.exame", resultado.estado.value)


class FormarConectorEDaARF(_SobreARF):
    nome = "formar_conector_e_da_arf"

    def agir(self, arf, *, em, arestas: Sequence[UUID]) -> ConectorE:
        return arf.formar_conector_e(tuple(arestas), em=em)

    def anotar_resultado(self, span: SpanDeTraco, resultado: ConectorE) -> None:
        span.atributo("toc.arestas_no_conector", len(resultado.arestas))


class DesfazerConectorEDaARF(_SobreARF):
    nome = "desfazer_conector_e_da_arf"

    def agir(self, arf, *, em, conector_id: UUID) -> None:
        arf.desfazer_conector_e(conector_id, em=em)


class EspelharUde(_SobreARF):
    """RF-04: o efeito futuro passa a ser o Efeito Desejável de um UDE da cadeia."""

    nome = "espelhar_ude"

    def agir(self, arf, *, em, no_id: UUID, ude_id: UUID, projeto_de_origem_id=None) -> EspelhoDeUde:
        return arf.espelhar_ude(
            no_id, ude_id, projeto_de_origem_id=projeto_de_origem_id, em=em
        )

    def anotar_resultado(self, span: SpanDeTraco, resultado: EspelhoDeUde) -> None:
        span.atributo("toc.ude_espelhado", str(resultado.ude_id))


class DesfazerEspelho(_SobreARF):
    nome = "desfazer_espelho"

    def agir(self, arf, *, em, no_id: UUID) -> None:
        arf.desfazer_espelho(no_id, em=em)


class MarcarRamoNegativo(_SobreARF):
    """RF-08: o efeito colateral da injeção vira dado, com estado e dono da decisão."""

    nome = "marcar_ramo_negativo"

    def agir(self, arf, *, em, no_id: UUID) -> RamoNegativo:
        return arf.marcar_ramo_negativo(no_id, em=em)

    def anotar_resultado(self, span: SpanDeTraco, resultado: RamoNegativo) -> None:
        span.atributo("toc.ramo_negativo", resultado.estado.value)


class TratarRamoNegativo(_SobreARF):
    nome = "tratar_ramo_negativo"

    def agir(self, arf, *, em, ramo_id: UUID, injecao_id: UUID) -> RamoNegativo:
        return arf.tratar_ramo(ramo_id, injecao_id=injecao_id, em=em)

    def anotar_resultado(self, span: SpanDeTraco, resultado: RamoNegativo) -> None:
        span.atributo("toc.ramo_negativo", resultado.estado.value)


class AceitarRamoNegativo(_SobreARF):
    """RN-04: aceitar exige justificativa e autor — e o span guarda quem, não o quê."""

    nome = "aceitar_ramo_negativo"

    def agir(self, arf, *, em, ramo_id: UUID, justificativa: str, autor: str) -> RamoNegativo:
        return arf.aceitar_ramo(ramo_id, justificativa=justificativa, autor=autor, em=em)

    def anotar_resultado(self, span: SpanDeTraco, resultado: RamoNegativo) -> None:
        span.atributo("toc.ramo_negativo", resultado.estado.value)


class ReabrirRamoNegativo(_SobreARF):
    nome = "reabrir_ramo_negativo"

    def agir(self, arf, *, em, ramo_id: UUID) -> RamoNegativo:
        return arf.reabrir_ramo(ramo_id, em=em)


class VerificarARF(_SobreARF):
    """RF-11/RF-13: função pura + evento com o resumo. Grava, logo exige `toc:write`."""

    nome = "verificar_arf"

    def agir(self, arf, *, em) -> VerificacaoDaARF:
        return arf.gerar_verificacao(em=em)

    def anotar_resultado(self, span: SpanDeTraco, resultado: VerificacaoDaARF) -> None:
        for chave, valor in resultado.resumo().items():
            span.atributo(f"toc.{chave}", valor)


# ---------------------------------------------------------------------------------------
# E4.2 · Árvore de Pré-Requisitos
# ---------------------------------------------------------------------------------------


class _ComAPR(_ComRepositorio):
    def _carregar(self, dono: DonoDoProjeto, projeto_id: UUID) -> ProjetoAPR:
        apr = self._repositorio.obter_apr(dono.inquilino_id, projeto_id)
        if apr is None:
            raise NaoEncontrado(str(projeto_id))
        return apr


class CriarProjetoAPR(_ComAPR):
    """RF-14: a APR nasce COM o objetivo — não existe APR sem o topo dela."""

    nome = "criar_projeto_apr"

    def executar(
        self,
        *,
        dono: DonoDoProjeto,
        nome: str,
        objetivo: str,
        descricao_do_problema: str = "",
    ) -> Projeto:
        apr = novo_projeto_apr(
            id=uuid4(),
            dono=dono,
            nome=nome,
            objetivo=objetivo,
            descricao_do_problema=descricao_do_problema,
            em=self._agora(),
        )
        self._repositorio.salvar_apr(apr)
        return apr.projeto


class AbrirProjetoAPR(_ComAPR):
    nome = "abrir_projeto_apr"

    def executar(self, *, dono: DonoDoProjeto, projeto_id: UUID) -> ProjetoAPR:
        return self._carregar(dono, projeto_id)


class AvaliarVerbalizacao(_ComAPR):
    """RF-20: função pura sobre o texto atual. Não grava — é a irmã de `ValidarNuvem`."""

    nome = "avaliar_verbalizacao"

    def executar(
        self, *, dono: DonoDoProjeto, projeto_id: UUID, no_id: UUID, idioma: str = "pt"
    ) -> VerbalizacaoAvaliada:
        return self._carregar(dono, projeto_id).avaliar_verbalizacao(no_id, idioma=idioma)

    def anotar_resultado(self, span: SpanDeTraco, resultado: VerbalizacaoAvaliada) -> None:
        span.atributo("toc.veredito", resultado.veredito.value)
        span.atributo("toc.avisos", len(resultado.avisos))


class ResumoDaAPR(_ComAPR):
    """RF-25: a tabela que vai à reunião. Leitura pura, sem evento."""

    nome = "resumo_da_apr"

    def executar(
        self, *, dono: DonoDoProjeto, projeto_id: UUID
    ) -> tuple[LinhaDoResumo, ...]:
        return self._carregar(dono, projeto_id).tabela_resumo()

    def anotar_resultado(self, span: SpanDeTraco, resultado) -> None:
        span.atributo("toc.linhas_do_resumo", len(resultado))


class _SobreAPR(_ComAPR):
    def executar(self, *, dono: DonoDoProjeto, projeto_id: UUID, **kw):
        apr = self._carregar(dono, projeto_id)
        resultado = self.agir(apr, em=self._agora(), **kw)
        self._repositorio.salvar_apr(apr)
        return resultado

    def agir(self, apr: ProjetoAPR, *, em, **kw):  # pragma: no cover - contrato
        raise NotImplementedError


class AdicionarNoDaAPR(_SobreAPR):
    nome = "adicionar_no_da_apr"

    def agir(
        self,
        apr,
        *,
        em,
        papel: PapelNaAPR,
        titulo: str,
        descricao: str = "",
        posicao: PosicaoNoCanvas | None = None,
        proposta_id: str | None = None,
    ) -> No:
        self._papel = PapelNaAPR(papel)
        self._proposta_id = proposta_id
        criar = (
            apr.adicionar_obstaculo
            if self._papel is PapelNaAPR.OBSTACULO
            else apr.adicionar_objetivo_intermediario
        )
        return criar(titulo=titulo, descricao=descricao, posicao=posicao, em=em)

    def anotar_resultado(self, span: SpanDeTraco, resultado: No) -> None:
        span.atributo("toc.papel", self._papel.value)
        if self._proposta_id:
            span.atributo("toc.proposta_id", self._proposta_id)


class EditarNoDaAPR(_SobreAPR):
    nome = "editar_no_da_apr"

    def agir(self, apr, *, em, no_id: UUID, titulo=None, descricao=None) -> No:
        return apr.editar_no(no_id, titulo=titulo, descricao=descricao, em=em)


class MoverNoDaAPR(_SobreAPR):
    nome = "mover_no_da_apr"

    def agir(self, apr, *, em, no_id: UUID, posicao: PosicaoNoCanvas) -> No:
        return apr.mover_no(no_id, posicao, em=em)


class ExcluirNoDaAPR(_SobreAPR):
    nome = "excluir_no_da_apr"

    def agir(self, apr, *, em, no_id: UUID) -> list[UUID]:
        return apr.excluir_no(no_id, em=em)


class MudarPapelNaAPR(_SobreAPR):
    nome = "mudar_papel_na_apr"

    def agir(self, apr, *, em, no_id: UUID, papel: PapelNaAPR) -> No:
        self._papel = PapelNaAPR(papel)
        return apr.mudar_papel(no_id, self._papel, em=em)

    def anotar_resultado(self, span: SpanDeTraco, resultado: No) -> None:
        span.atributo("toc.papel", self._papel.value)


class DeclararDependencia(_SobreAPR):
    """RF-16: "A precisa existir antes de B" — condição necessária, sem exame de elo."""

    nome = "declarar_dependencia"

    def agir(self, apr, *, em, antes_id: UUID, depois_id: UUID) -> ArestaCausal:
        return apr.depender(antes_id, depois_id, em=em)


class ExcluirDependencia(_SobreAPR):
    nome = "excluir_dependencia"

    def agir(self, apr, *, em, aresta_id: UUID) -> None:
        apr.excluir_dependencia(aresta_id, em=em)


class ParearObstaculo(_SobreAPR):
    nome = "parear_obstaculo"

    def agir(
        self, apr, *, em, obstaculo_id: UUID, oi_id: UUID, proposta_id: str | None = None
    ) -> ParObstaculoOI:
        self._proposta_id = proposta_id
        return apr.parear(obstaculo_id, oi_id, em=em)

    def anotar_resultado(self, span: SpanDeTraco, resultado: ParObstaculoOI) -> None:
        if self._proposta_id:
            span.atributo("toc.proposta_id", self._proposta_id)


class DesfazerPar(_SobreAPR):
    nome = "desfazer_par"

    def agir(self, apr, *, em, par_id: UUID) -> None:
        apr.desfazer_par(par_id, em=em)


class JulgarTesteDeValidade(_SobreAPR):
    """RN-07: julgamento com autor e data, acumulável — nunca campo calculado."""

    nome = "julgar_teste_de_validade"

    def agir(
        self, apr, *, em, par_id: UUID, autor: str, valido: bool, justificativa: str
    ) -> ParObstaculoOI:
        return apr.julgar_par(
            par_id, autor=autor, valido=valido, justificativa=justificativa, em=em
        )

    def anotar_resultado(self, span: SpanDeTraco, resultado: ParObstaculoOI) -> None:
        span.atributo("toc.julgamentos", len(resultado.julgamentos))


class FormarElipse(_SobreAPR):
    nome = "formar_elipse"

    def agir(self, apr, *, em, dependencias: Sequence[UUID]) -> ElipseDeSimultaneidade:
        return apr.formar_elipse(tuple(dependencias), em=em)

    def anotar_resultado(self, span: SpanDeTraco, resultado: ElipseDeSimultaneidade) -> None:
        span.atributo("toc.dependencias_na_elipse", len(resultado.dependencias))


class DesfazerElipse(_SobreAPR):
    nome = "desfazer_elipse"

    def agir(self, apr, *, em, elipse_id: UUID) -> None:
        apr.desfazer_elipse(elipse_id, em=em)


class SequenciarAPR(_SobreAPR):
    """RF-23/RF-26: camadas, ramos paralelos, elipses e o ciclo que bloqueia."""

    nome = "sequenciar_apr"

    def agir(self, apr, *, em) -> Sequenciamento:
        return apr.gerar_sequenciamento(em=em)

    def anotar_resultado(self, span: SpanDeTraco, resultado: Sequenciamento) -> None:
        for chave, valor in resultado.resumo().items():
            span.atributo(f"toc.{chave}", valor)


# ---------------------------------------------------------------------------------------
# E4.3 · Árvore de Transição
# ---------------------------------------------------------------------------------------


class _ComAT(_ComRepositorio):
    def _carregar(self, dono: DonoDoProjeto, projeto_id: UUID) -> ProjetoAT:
        at = self._repositorio.obter_at(dono.inquilino_id, projeto_id)
        if at is None:
            raise NaoEncontrado(str(projeto_id))
        return at


class CriarProjetoAT(_ComAT):
    nome = "criar_projeto_at"

    def executar(
        self, *, dono: DonoDoProjeto, nome: str, descricao_do_problema: str = ""
    ) -> Projeto:
        at = novo_projeto_at(
            id=uuid4(),
            dono=dono,
            nome=nome,
            descricao_do_problema=descricao_do_problema,
            em=self._agora(),
        )
        self._repositorio.salvar_at(at)
        return at.projeto


class AbrirProjetoAT(_ComAT):
    nome = "abrir_projeto_at"

    def executar(self, *, dono: DonoDoProjeto, projeto_id: UUID) -> ProjetoAT:
        return self._carregar(dono, projeto_id)


class _SobreAT(_ComAT):
    def executar(self, *, dono: DonoDoProjeto, projeto_id: UUID, **kw):
        at = self._carregar(dono, projeto_id)
        resultado = self.agir(at, em=self._agora(), **kw)
        self._repositorio.salvar_at(at)
        return resultado

    def agir(self, at: ProjetoAT, *, em, **kw):  # pragma: no cover - contrato
        raise NotImplementedError


class RegistrarPasso(_SobreAT):
    """RN-10: a tripla é obrigatória — sem ela, nada nasce."""

    nome = "registrar_passo"

    def agir(
        self,
        at,
        *,
        em,
        acao: str,
        necessidade: str,
        resultado_esperado: str,
        posicao: PosicaoNoCanvas | None = None,
        proposta_id: str | None = None,
    ) -> No:
        self._proposta_id = proposta_id
        return at.registrar_passo(
            acao=acao,
            necessidade=necessidade,
            resultado_esperado=resultado_esperado,
            posicao=posicao,
            em=em,
        )

    def anotar_resultado(self, span: SpanDeTraco, resultado: No) -> None:
        if self._proposta_id:
            span.atributo("toc.proposta_id", self._proposta_id)


class EditarFichaDoPasso(_SobreAT):
    nome = "editar_ficha_do_passo"

    def agir(
        self, at, *, em, no_id: UUID, acao=None, necessidade=None, resultado_esperado=None
    ) -> FichaDePasso:
        return at.editar_ficha(
            no_id,
            acao=acao,
            necessidade=necessidade,
            resultado_esperado=resultado_esperado,
            em=em,
        )


class PrecederPasso(_SobreAT):
    nome = "preceder_passo"

    def agir(self, at, *, em, antes_id: UUID, depois_id: UUID) -> ArestaCausal:
        return at.preceder(antes_id, depois_id, em=em)


class ExcluirPrecedencia(_SobreAT):
    nome = "excluir_precedencia"

    def agir(self, at, *, em, aresta_id: UUID) -> None:
        at.excluir_precedencia(aresta_id, em=em)


class ExcluirPasso(_SobreAT):
    nome = "excluir_passo"

    def agir(self, at, *, em, no_id: UUID) -> list[UUID]:
        return at.excluir_no(no_id, em=em)


class MudarStatusDoPasso(_SobreAT):
    """RF-30: a divergência entre esperado e real vai para o span e para o evento."""

    nome = "mudar_status_do_passo"

    def agir(
        self,
        at,
        *,
        em,
        no_id: UUID,
        status: StatusDoPasso,
        motivo: str = "",
        resultado_real: str = "",
    ) -> FichaDePasso:
        return at.mudar_status(
            no_id,
            StatusDoPasso(status),
            motivo=motivo,
            resultado_real=resultado_real,
            em=em,
        )

    def anotar_resultado(self, span: SpanDeTraco, resultado: FichaDePasso) -> None:
        span.atributo("toc.status_do_passo", resultado.status.value)
        span.atributo("toc.divergente", resultado.divergente)


__all__ = [
    "AbrirProjetoAPR",
    "AbrirProjetoARF",
    "AbrirProjetoAT",
    "AceitarRamoNegativo",
    "AdicionarNoDaAPR",
    "AdicionarNoDaARF",
    "AvaliarVerbalizacao",
    "CriarProjetoAPR",
    "CriarProjetoARF",
    "CriarProjetoAT",
    "DeclararDependencia",
    "DesfazerConectorEDaARF",
    "DesfazerElipse",
    "DesfazerEspelho",
    "DesfazerPar",
    "EditarFichaDoPasso",
    "EditarNoDaAPR",
    "EditarNoDaARF",
    "EspelharUde",
    "ExaminarEloDaARF",
    "ExcluirArestaDaARF",
    "ExcluirDependencia",
    "ExcluirNoDaAPR",
    "ExcluirNoDaARF",
    "ExcluirPasso",
    "ExcluirPrecedencia",
    "FormarConectorEDaARF",
    "FormarElipse",
    "JulgarTesteDeValidade",
    "LigarNaARF",
    "MarcarRamoNegativo",
    "MoverNoDaAPR",
    "MoverNoDaARF",
    "MudarPapelNaAPR",
    "MudarPapelNaARF",
    "MudarStatusDoPasso",
    "ParearObstaculo",
    "PrecederPasso",
    "ReabrirRamoNegativo",
    "RegistrarPasso",
    "ResumoDaAPR",
    "SequenciarAPR",
    "TratarRamoNegativo",
    "VerificarARF",
]
