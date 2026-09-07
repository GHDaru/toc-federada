"""E1.4 — os dois casos de uso da portabilidade (spec 011, RF-25..RF-32).

Siglas, uma vez neste arquivo: **ARA** — Árvore da Realidade Atual · **NC** — Nuvem de
Conflito · **ARF** — Árvore da Realidade Futura · **APR** — Árvore de Pré-Requisitos ·
**AT** — Árvore de Transição · **S&T** — Estratégia & Táticas · **JSON** — *JavaScript
Object Notation* · **OTel** — OpenTelemetry · **RF/RN** — requisito funcional / regra de
negócio · **ADR** — *Architecture Decision Record*.

**O que esta camada acrescenta ao domínio** (que já sabe exportar, converter e importar):

1. **Achar a análise inteira a partir de um ponto dela.** A pessoa pede "exporta este
   projeto"; o que ela quer é a cadeia — e a cadeia é definida pelos vínculos, não pela
   tela onde ela está. A travessia é por vínculo, nos dois sentidos, a partir de qualquer
   elo (a mesma regra do RF-41 do M4).
2. **Ler e gravar pelas portas**, cada agregado pela porta da ferramenta dele.
3. **Traço** (P5): grandeza e identificador no span, nunca o texto que a pessoa escreveu.

Camada pura: zero import de SQLAlchemy, FastAPI, Pydantic ou OpenTelemetry — o
`import-linter` (contrato P3-2) reprova se alguém mudar isso.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Mapping
from uuid import UUID

from ..dominio.apr import FERRAMENTA_APR
from ..dominio.ara import FERRAMENTA_ARA
from ..dominio.arf import FERRAMENTA_ARF
from ..dominio.at import FERRAMENTA_AT
from ..dominio.erros import NaoEncontrado
from ..dominio.exportacao import (
    RelatoDeImportacao,
    exportar_consolidado,
    importar_consolidado,
)
from ..dominio.focalizacao import FERRAMENTA_FOCALIZACAO
from ..dominio.identidade import DonoDoProjeto
from ..dominio.legado import converter_legado, reconhecer_legado
from ..dominio.nuvem import FERRAMENTA_NC
from ..dominio.portas import Rastreador, Relogio, SpanDeTraco
from ..dominio.projeto import Projeto
from ..dominio.snt import FERRAMENTA_SNT
from .casos_de_uso import CasoDeUso

#: `ferramenta → (nome do método de leitura, nome do método de escrita)`. Uma tabela, e não
#: uma cadeia de `if`: acrescentar ferramenta é acrescentar linha, e a linha que falta
#: aparece como `KeyError` no teste — não como projeto exportado pela metade.
PORTA_POR_FERRAMENTA: dict[str, tuple[str, str]] = {
    FERRAMENTA_ARA: ("obter_ara", "salvar_ara"),
    FERRAMENTA_NC: ("obter_nuvem", "salvar_nuvem"),
    FERRAMENTA_ARF: ("obter_arf", "salvar_arf"),
    FERRAMENTA_APR: ("obter_apr", "salvar_apr"),
    FERRAMENTA_AT: ("obter_at", "salvar_at"),
    FERRAMENTA_SNT: ("obter_snt", "salvar_snt"),
    FERRAMENTA_FOCALIZACAO: ("obter_focalizacao", "salvar_focalizacao"),
}

FORMATO_PROPRIO = "consolidado"
FORMATO_LEGADO = "legado"


@dataclass(frozen=True, slots=True)
class ResultadoDaImportacaoGravada:
    """O que a importação devolve à borda: o relato, o formato lido e o que nasceu."""

    relato: RelatoDeImportacao
    formato: str
    projetos_criados: tuple[UUID, ...] = ()


class _ComPortas(CasoDeUso):
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

    def _exigir_relogio(self) -> Relogio:
        if self._relogio is None:  # pragma: no cover - erro de composição, não de uso
            raise RuntimeError(f"{type(self).__name__} precisa de um relógio")
        return self._relogio

    def _carregar_agregado(self, dono: DonoDoProjeto, projeto: Projeto) -> Any:
        """Cada ferramenta pela porta dela; o M1 genérico é o próprio `Projeto`."""
        portas = PORTA_POR_FERRAMENTA.get(projeto.ferramenta)
        if portas is None:
            return projeto
        ler = getattr(self._repositorio, portas[0], None)
        if ler is None:
            return projeto
        agregado = ler(dono.inquilino_id, projeto.id)
        return projeto if agregado is None else agregado

    def _projeto(self, dono: DonoDoProjeto, projeto_id: UUID) -> Projeto:
        """Fora do inquilino a resposta é `NaoEncontrado`, nunca "proibido"."""
        projeto = self._repositorio.obter(dono.inquilino_id, projeto_id)
        if projeto is None:
            raise NaoEncontrado(str(projeto_id))
        return projeto


class ExportarConsolidado(_ComPortas):
    """RF-31: a análise inteira num arquivo, a partir de qualquer ponto dela."""

    nome = "exportar_consolidado"

    def executar(self, *, dono: DonoDoProjeto, projeto_id: UUID) -> dict:
        raiz = self._projeto(dono, projeto_id)
        referencias = self._referencias(dono)
        alcancados = self._alcancar(raiz.id, referencias)

        agregados = []
        for identificador in sorted(alcancados, key=str):
            projeto = self._repositorio.obter(dono.inquilino_id, identificador)
            if projeto is None:
                # O vínculo aponta para um projeto que não está mais no inquilino. Ele
                # **não** some do arquivo por acidente: o vínculo correspondente cai fora
                # logo abaixo, porque uma das pontas não veio.
                continue
            agregados.append(self._carregar_agregado(dono, projeto))

        presentes = {self._id(a) for a in agregados}
        vinculos = [
            r
            for r in referencias
            if r.origem.projeto_id in presentes and r.destino.projeto_id in presentes
        ]
        return exportar_consolidado(
            agregados, vinculos=vinculos, exportado_em=self._exigir_relogio().agora()
        )

    def anotar_resultado(self, span: SpanDeTraco, resultado: Any) -> None:
        if isinstance(resultado, Mapping):
            span.atributo("toc.projetos_exportados", len(resultado.get("projetos", [])))
            span.atributo("toc.vinculos_exportados", len(resultado.get("vinculos", [])))

    def _referencias(self, dono: DonoDoProjeto) -> list[Any]:
        listar = getattr(self._repositorio, "listar_referencias", None)
        return [] if listar is None else list(listar(dono.inquilino_id))

    @staticmethod
    def _id(agregado: Any) -> UUID:
        return (agregado.projeto if hasattr(agregado, "projeto") else agregado).id

    @staticmethod
    def _alcancar(raiz: UUID, referencias) -> set[UUID]:
        """Fecho transitivo por vínculo, nos DOIS sentidos.

        Nos dois sentidos porque a pessoa pode pedir a exportação estando na Árvore de
        Transição, que é a ponta da cadeia: subir só para o destino traria um arquivo com
        um projeto e nenhum vínculo — tecnicamente correto e inútil.
        """
        alcancados = {raiz}
        fila = [raiz]
        while fila:
            atual = fila.pop()
            for referencia in referencias:
                pontas = (referencia.origem.projeto_id, referencia.destino.projeto_id)
                if atual not in pontas:
                    continue
                for outra in pontas:
                    if outra not in alcancados:
                        alcancados.add(outra)
                        fila.append(outra)
        return alcancados


class ImportarConsolidado(_ComPortas):
    """RF-25..RF-30: reconhece o formato, valida inteiro, e só então grava."""

    nome = "importar_consolidado"

    def executar(
        self,
        *,
        dono: DonoDoProjeto,
        documento: Any,
        teto_de_bytes: int | None = None,
        novo_id: Callable[[], UUID] | None = None,
    ) -> ResultadoDaImportacaoGravada:
        formato = FORMATO_LEGADO if reconhecer_legado(documento) else FORMATO_PROPRIO
        descartes = ()
        if formato == FORMATO_LEGADO:
            # O teto (RF-30) é configuração da borda com padrão no domínio: quem chama
            # pode apertá-lo, ninguém pode afrouxá-lo em silêncio — o padrão está
            # declarado em `dominio/legado.LIMITE_PADRAO_DE_TAMANHO`.
            limite = {} if teto_de_bytes is None else {"teto_de_bytes": teto_de_bytes}
            convertido, relato = converter_legado(documento, **limite)
            if convertido is None:
                return ResultadoDaImportacaoGravada(relato, formato)
            documento, descartes = convertido, relato.descartes

        argumentos = {} if novo_id is None else {"novo_id": novo_id}
        resultado = importar_consolidado(documento, dono=dono, **argumentos)
        if not resultado.relato.aceito:
            return ResultadoDaImportacaoGravada(resultado.relato, formato)

        criados: list[UUID] = []
        for agregado in resultado.projetos:
            self._gravar(agregado)
            criados.append(ExportarConsolidado._id(agregado))
        salvar_referencia = getattr(self._repositorio, "salvar_referencia", None)
        if salvar_referencia is not None:
            for vinculo in resultado.vinculos:
                salvar_referencia(vinculo)

        relato = RelatoDeImportacao(
            contagens=resultado.relato.contagens,
            problemas=(),
            # Os descartes da conversão do formato antigo (histórico de conversa, saída de
            # modelo, identidade de origem) viajam junto com os da importação: quem leu o
            # arquivo tem de ver a lista inteira do que ficou de fora (RN-06).
            descartes=tuple(descartes) + resultado.relato.descartes,
        )
        return ResultadoDaImportacaoGravada(relato, formato, tuple(criados))

    def _gravar(self, agregado: Any) -> None:
        projeto = agregado.projeto if hasattr(agregado, "projeto") else agregado
        portas = PORTA_POR_FERRAMENTA.get(projeto.ferramenta)
        if portas is None:
            self._repositorio.salvar(projeto)
            return
        salvar = getattr(self._repositorio, portas[1], None)
        if salvar is None:  # pragma: no cover - composição parcial
            self._repositorio.salvar(projeto)
            return
        salvar(agregado)

    def anotar_resultado(self, span: SpanDeTraco, resultado: Any) -> None:
        if not isinstance(resultado, ResultadoDaImportacaoGravada):  # pragma: no cover
            return
        span.atributo("toc.formato", resultado.formato)
        span.atributo("toc.projetos_importados", len(resultado.projetos_criados))
        span.atributo("toc.nos_importados", int(resultado.relato.contagens.get("nos", 0)))
        span.atributo("toc.arestas_importadas", int(resultado.relato.contagens.get("arestas", 0)))
        span.atributo("toc.vinculos_importados", int(resultado.relato.contagens.get("vinculos", 0)))
        span.atributo("toc.descartes_declarados", len(resultado.relato.descartes))
        # Recusa também é traço (brief §4). O número de problemas entra SEM o texto deles:
        # o caminho do campo é estrutura, mas o motivo pode citar valor do arquivo.
        span.atributo("toc.problemas", len(resultado.relato.problemas))


__all__ = [
    "FORMATO_LEGADO",
    "FORMATO_PROPRIO",
    "PORTA_POR_FERRAMENTA",
    "ExportarConsolidado",
    "ImportarConsolidado",
    "ResultadoDaImportacaoGravada",
]
