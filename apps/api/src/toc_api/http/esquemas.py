"""Os esquemas Pydantic — e eles vivem AQUI, na borda, nunca no domínio.

O contrato P3-1 do `import-linter` proíbe `toc_api.dominio` de importar `pydantic`, e o
P3-2 proíbe `toc_api.aplicacao` de fazê-lo. A razão não é purismo: uma entidade que herda
de `BaseModel` valida no construtor do framework, e a regra de negócio passa a viver na
anotação de tipo — invisível para o teste de domínio, indisponível para quem não estiver
dentro de uma requisição. As regras da Teoria das Restrições (TOC) precisam rodar sem
rede e sem banco, e é por isso que a tradução mora aqui e só aqui.

**Entrada é esquema fechado.** Todo modelo de pedido usa `extra="forbid"`: campo
desconhecido é rejeitado na borda, nunca repassado adiante. É a mesma disciplina que o
Anexo A do Padrão APH (Aplicação ↔ Harness) exige do snapshot no §A.4 —
`additionalProperties: false` em todos os níveis fechados.

**Saída é projeção, não o agregado.** Nenhum modelo de resposta expõe evento de domínio,
identificador de inquilino ou qualquer coisa que o cliente não tenha pedido: a tela é
dado, e dado de menos é mais barato de corrigir do que dado de mais.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from ..dominio.analise import RelatorioEstrutural
from ..dominio.ara import (
    ConectorE,
    Exame,
    FichaDeUde,
    ParecerDeJulgamento,
    ProjetoARA,
    StatusDeValidacao,
)
from ..dominio.criterios_ude import ValidacaoFormal
from ..dominio.formulacao import AvisoDeFormulacao
from ..dominio.nuvem import (
    ChaveDaAresta,
    Injecao,
    NuvemDeConflito,
    PapelDaEntidade,
    Premissa,
    ReferenciaDeSemeadura,
    ValidacaoDaNuvem,
)
from ..dominio.grafo import ArestaCausal, No
from ..dominio.projeto import Projeto
from ..dominio.valores import PosicaoNoCanvas


class Pedido(BaseModel):
    """Base de todo corpo de entrada: esquema FECHADO."""

    model_config = ConfigDict(extra="forbid")


class Resposta(BaseModel):
    model_config = ConfigDict(extra="forbid")


# -- valores compartilhados ----------------------------------------------------------


class PosicaoIO(Resposta):
    x: float = 0.0
    y: float = 0.0

    @classmethod
    def de(cls, posicao: PosicaoNoCanvas) -> "PosicaoIO":
        return cls(x=posicao.x, y=posicao.y)

    def para_dominio(self) -> PosicaoNoCanvas:
        return PosicaoNoCanvas(self.x, self.y)


# -- M1: projeto, nó, aresta ---------------------------------------------------------


class NoOut(Resposta):
    id: UUID
    titulo: str
    descricao: str
    tipo: str
    posicao: PosicaoIO
    recolhido: bool

    @classmethod
    def de(cls, no: No) -> "NoOut":
        return cls(
            id=no.id,
            titulo=no.titulo,
            descricao=no.descricao,
            tipo=no.tipo,
            posicao=PosicaoIO.de(no.posicao),
            recolhido=no.recolhido,
        )


class ArestaOut(Resposta):
    id: UUID
    origem_id: UUID
    destino_id: UUID
    rotulo: str

    @classmethod
    def de(cls, aresta: ArestaCausal) -> "ArestaOut":
        return cls(
            id=aresta.id,
            origem_id=aresta.origem_id,
            destino_id=aresta.destino_id,
            rotulo=aresta.rotulo,
        )


class ProjetoResumoOut(Resposta):
    """O que a lista e a lixeira mostram — sem carregar nó nem aresta (RF-02, RF-07)."""

    id: UUID
    nome: str
    ferramenta: str
    descricao_do_problema: str
    estado: str
    versao: int
    criado_em: datetime
    alterado_em: datetime
    excluido_em: datetime | None = None

    @classmethod
    def de(cls, projeto: Projeto) -> "ProjetoResumoOut":
        return cls(
            id=projeto.id,
            nome=projeto.nome,
            ferramenta=projeto.ferramenta,
            descricao_do_problema=projeto.descricao_do_problema,
            estado=projeto.estado.value,
            versao=projeto.versao,
            criado_em=projeto.criado_em,
            alterado_em=projeto.alterado_em,
            excluido_em=projeto.excluido_em,
        )


class ProjetoOut(ProjetoResumoOut):
    """RF-03: metadados, nós e arestas num carregamento consistente."""

    nos: list[NoOut] = Field(default_factory=list)
    arestas: list[ArestaOut] = Field(default_factory=list)

    @classmethod
    def de(cls, projeto: Projeto) -> "ProjetoOut":
        resumo = ProjetoResumoOut.de(projeto)
        return cls(
            **resumo.model_dump(),
            nos=[NoOut.de(n) for n in projeto.nos],
            arestas=[ArestaOut.de(a) for a in projeto.arestas],
        )


class ExclusaoDeNoOut(Resposta):
    """RF-15: a resposta declara o RAIO — quais arestas saíram junto."""

    no_id: UUID
    arestas_removidas: list[UUID]


class CriarProjetoIn(Pedido):
    nome: str
    descricao_do_problema: str = ""


class CriarNoIn(Pedido):
    titulo: str
    descricao: str = ""
    posicao: PosicaoIO | None = None


class EditarNoIn(Pedido):
    """PATCH parcial. Nenhum campo informado é recusa, não é sucesso vazio."""

    titulo: str | None = None
    descricao: str | None = None
    posicao: PosicaoIO | None = None
    recolhido: bool | None = None


class LigarIn(Pedido):
    origem_id: UUID
    destino_id: UUID
    rotulo: str = ""


class EditarArestaIn(Pedido):
    rotulo: str


# -- M2: Árvore da Realidade Atual (ARA) ---------------------------------------------


class VereditoOut(Resposta):
    codigo: str
    caracteristica: str
    nome: str
    classe: str
    regra: str
    enunciado: str
    veredito: str
    motivo: str
    trecho: str


class ValidacaoOut(Resposta):
    """RF-06..RF-09: veredito por critério, com o trecho que o motivou.

    `pendencias_de_julgamento` sai separado das `reprovacoes` de propósito: o RF-08 diz
    que o indeterminado "conta como pendência de julgamento, não como reprovação", e
    misturar os dois numa lista só reintroduziria o chute que a spec proíbe.
    """

    texto: str
    idioma: str
    versao_do_lexico: str
    aprovado_nos_decidiveis: bool
    vereditos: list[VereditoOut]
    reprovacoes: list[str]
    pendencias_de_julgamento: list[str]

    @classmethod
    def de(cls, validacao: ValidacaoFormal) -> "ValidacaoOut":
        return cls(
            texto=validacao.texto,
            idioma=validacao.idioma,
            versao_do_lexico=validacao.versao_do_lexico,
            aprovado_nos_decidiveis=validacao.aprovado_nos_decidiveis,
            vereditos=[
                VereditoOut(
                    codigo=v.criterio.codigo,
                    caracteristica=v.criterio.caracteristica,
                    nome=v.criterio.nome,
                    classe=v.criterio.classe.value,
                    regra=v.criterio.regra,
                    enunciado=v.criterio.enunciado,
                    veredito=v.veredito.value,
                    motivo=v.motivo,
                    trecho=v.trecho,
                )
                for v in validacao.vereditos
            ],
            reprovacoes=[v.criterio.codigo for v in validacao.reprovacoes],
            pendencias_de_julgamento=[
                v.criterio.codigo for v in validacao.pendencias_de_julgamento
            ],
        )


class FichaIO(Resposta):
    area_impactada: str = ""
    objetivo_afetado: str = ""
    evidencias: list[str] = Field(default_factory=list)
    frequencia: str = ""
    impactos_estimados: str = ""

    @classmethod
    def de(cls, ficha: FichaDeUde) -> "FichaIO":
        return cls(
            area_impactada=ficha.area_impactada,
            objetivo_afetado=ficha.objetivo_afetado,
            evidencias=list(ficha.evidencias),
            frequencia=ficha.frequencia,
            impactos_estimados=ficha.impactos_estimados,
        )

    def para_dominio(self) -> FichaDeUde:
        return FichaDeUde(
            area_impactada=self.area_impactada,
            objetivo_afetado=self.objetivo_afetado,
            evidencias=tuple(self.evidencias),
            frequencia=self.frequencia,
            impactos_estimados=self.impactos_estimados,
        )


class ParecerOut(Resposta):
    autor: str
    origem: str
    favoravel: bool
    justificativa: str
    instante: datetime
    proposta_id: str | None = None
    criterios: list[str] = Field(default_factory=list)

    @classmethod
    def de(cls, parecer: ParecerDeJulgamento) -> "ParecerOut":
        return cls(
            autor=parecer.autor,
            origem=parecer.origem.value,
            favoravel=parecer.favoravel,
            justificativa=parecer.justificativa,
            instante=parecer.instante,
            proposta_id=parecer.proposta_id,
            criterios=list(parecer.criterios),
        )


class ExameOut(Resposta):
    aresta_id: UUID
    estado: str
    reserva: str

    @classmethod
    def de(cls, aresta_id: UUID, exame: Exame) -> "ExameOut":
        return cls(aresta_id=aresta_id, estado=exame.estado.value, reserva=exame.reserva)


class EloOut(Resposta):
    """RF-19: a leitura de suficiência montada dos textos ATUAIS dos nós."""

    aresta_id: UUID
    leitura: str
    exame: ExameOut


class ConectorOut(Resposta):
    id: UUID
    destino_id: UUID
    arestas: list[UUID]

    @classmethod
    def de(cls, conector: ConectorE) -> "ConectorOut":
        return cls(
            id=conector.id,
            destino_id=conector.destino_id,
            arestas=list(conector.arestas),
        )


class ConectorLidoOut(ConectorOut):
    """RF-24: "Se A **e** B, então C"."""

    leitura: str


class UdeOut(Resposta):
    no_id: UUID
    titulo: str
    status: str
    ficha: FichaIO
    validacao: ValidacaoOut
    pareceres: list[ParecerOut]


class StatusOut(Resposta):
    no_id: UUID
    status: str


class AlcanceOut(Resposta):
    no_id: UUID
    udes_alcancados: list[UUID]
    fracao: float


class RelatorioOut(Resposta):
    """RF-26..RF-31. `causa_raiz_candidata` é `null` no empate — de propósito.

    O RN-12 manda apontar, nunca concluir: com duas entradas empatadas, devolver a
    primeira seria concluir escondido. As candidatas ficam na lista; a conclusão é do
    humano.
    """

    fragmentos: list[list[UUID]]
    entradas: list[UUID]
    alcances: list[AlcanceOut]
    udes_nao_alcancados: list[UUID]
    elos_nao_examinados: list[UUID]
    orfaos: list[UUID]
    ciclos: list[list[UUID]]
    nos_em_ciclo: list[UUID]
    causas_raiz_candidatas: list[UUID]
    causa_raiz_candidata: UUID | None = None
    observacoes: list[str]
    total_de_nos: int
    total_de_udes: int
    resumo: dict[str, int]

    @classmethod
    def de(cls, relatorio: RelatorioEstrutural) -> "RelatorioOut":
        return cls(
            fragmentos=[list(f) for f in relatorio.fragmentos],
            entradas=list(relatorio.entradas),
            alcances=[
                AlcanceOut(
                    no_id=a.no_id,
                    udes_alcancados=list(a.udes_alcancados),
                    fracao=a.fracao,
                )
                for a in relatorio.alcances
            ],
            udes_nao_alcancados=list(relatorio.udes_nao_alcancados),
            elos_nao_examinados=list(relatorio.elos_nao_examinados),
            orfaos=list(relatorio.orfaos),
            ciclos=[list(c) for c in relatorio.ciclos],
            nos_em_ciclo=sorted(relatorio.nos_em_ciclo, key=str),
            causas_raiz_candidatas=list(relatorio.causas_raiz_candidatas),
            causa_raiz_candidata=relatorio.causa_raiz_candidata,
            observacoes=list(relatorio.observacoes),
            total_de_nos=relatorio.total_de_nos,
            total_de_udes=relatorio.total_de_udes,
            resumo=relatorio.resumo(),
        )


class AraOut(Resposta):
    """A leitura inteira do M2: o projeto do M1 mais a semântica da ferramenta."""

    projeto: ProjetoOut
    udes: list[UdeOut]
    elos: list[EloOut]
    conectores: list[ConectorLidoOut]
    resumo_por_status: dict[str, int]

    @classmethod
    def de(cls, ara: ProjetoARA) -> "AraOut":
        return cls(
            projeto=ProjetoOut.de(ara.projeto),
            udes=[ude_out(ara, no_id) for no_id in sorted(ara.udes, key=str)],
            elos=[
                EloOut(
                    aresta_id=a.id,
                    leitura=ara.leitura_do_elo(a.id),
                    exame=ExameOut.de(a.id, ara.exame(a.id)),
                )
                for a in ara.arestas
            ],
            conectores=[
                ConectorLidoOut(
                    **ConectorOut.de(c).model_dump(),
                    leitura=ara.leitura_do_conector(c.id),
                )
                for c in ara.conectores
            ],
            resumo_por_status={
                status.value: quantos
                for status, quantos in ara.resumo_por_status().items()
            },
        )


def ude_out(ara: ProjetoARA, no_id: UUID) -> UdeOut:
    return UdeOut(
        no_id=no_id,
        titulo=ara.projeto.no(no_id).titulo,
        status=ara.status(no_id).value,
        ficha=FichaIO.de(ara.ficha(no_id)),
        validacao=ValidacaoOut.de(ara.validacao(no_id)),
        pareceres=[ParecerOut.de(p) for p in ara.pareceres(no_id)],
    )


# -- pedidos do M2 -------------------------------------------------------------------


class ValidarTextoIn(Pedido):
    texto: str
    idioma: str = "pt"


class MarcarUdeIn(Pedido):
    ficha: FichaIO | None = None


class ReformularIn(Pedido):
    texto: str


class ParecerIn(Pedido):
    """O autor NÃO vem do cliente: vem do principal da introspecção (RF-16).

    Na 4ª geração da linhagem, `validado_por` era texto devolvido pelo modelo de
    linguagem (`tocbuilderv3/types.ts:171-213`) — quem validou era o que alguém disse que
    tinha validado. Aqui o campo não existe no pedido, e é por isso que "Validado"
    significa alguma coisa.
    """

    favoravel: bool
    justificativa: str
    criterios: list[str] = Field(default_factory=list)


class MudarStatusIn(Pedido):
    status: StatusDeValidacao
    justificativa: str = ""


class ExaminarEloIn(Pedido):
    estado: str
    reserva: str = ""


class ConectorIn(Pedido):
    arestas: list[UUID]


# -- M3: Nuvem de Conflito (spec 007) --------------------------------------------------
#
# A tradução do M3 segue a mesma regra dos anteriores, e ela aparece aqui com força: o
# **papel** e a **chave da aresta** viajam como texto (`"A"`, `"D_D_PRIME"`), e a
# conversão para o enum do domínio acontece nesta camada — errar o nome vira `422` na
# borda, nunca `KeyError` lá dentro.


class AvisoOut(Resposta):
    """RF-09/RI-05: aviso pedagógico, com explicação e exemplo — nunca bloqueio."""

    codigo: str
    explicacao: str
    exemplo: str

    @classmethod
    def de(cls, aviso: AvisoDeFormulacao) -> "AvisoOut":
        return cls(
            codigo=aviso.codigo.value,
            explicacao=aviso.explicacao,
            exemplo=aviso.exemplo,
        )


class EntidadeDaNuvemOut(Resposta):
    papel: str
    no_id: UUID
    texto: str
    posicao: PosicaoIO
    avisos: list[AvisoOut]


class SemeaduraOut(Resposta):
    """INT-06: a costura com a Árvore da Realidade Futura, ainda sem destino."""

    injecao_id: UUID
    projeto_destino_id: UUID | None

    @classmethod
    def de(cls, semeadura: ReferenciaDeSemeadura) -> "SemeaduraOut":
        return cls(
            injecao_id=semeadura.injecao_id,
            projeto_destino_id=semeadura.projeto_destino_id,
        )


class InjecaoOut(Resposta):
    id: UUID
    premissa_id: UUID
    texto: str
    status: str
    separacao: str | None
    semeadura: SemeaduraOut | None

    @classmethod
    def de(cls, injecao: Injecao) -> "InjecaoOut":
        return cls(
            id=injecao.id,
            premissa_id=injecao.premissa_id,
            texto=injecao.texto,
            status=injecao.status.value,
            separacao=injecao.separacao.value if injecao.separacao else None,
            semeadura=SemeaduraOut.de(injecao.semeadura) if injecao.semeadura else None,
        )


class PremissaOut(Resposta):
    id: UUID
    aresta: str
    texto: str
    ordem: int
    estado: str
    justificativa: str
    injecoes: list[InjecaoOut]

    @classmethod
    def de(cls, premissa: Premissa, injecoes: tuple[Injecao, ...]) -> "PremissaOut":
        return cls(
            id=premissa.id,
            aresta=premissa.aresta.value,
            texto=premissa.texto,
            ordem=premissa.ordem,
            estado=premissa.estado.value,
            justificativa=premissa.justificativa,
            injecoes=[InjecaoOut.de(i) for i in injecoes],
        )


class ArestaDaNuvemOut(Resposta):
    chave: str
    classe: str
    aresta_id: UUID
    leitura: str
    premissas: list[PremissaOut]


class OrigemOut(Resposta):
    """INT-05: de onde a nuvem veio — tipado, com a leitura pronta para a tela."""

    ferramenta: str
    projeto_id: UUID
    nos: list[UUID]
    leitura: str


class NuvemOut(Resposta):
    id: UUID
    nome: str
    ferramenta: str
    descricao_do_problema: str
    racional: str
    criado_em: datetime
    alterado_em: datetime
    origem: OrigemOut | None
    entidades: list[EntidadeDaNuvemOut]
    arestas: list[ArestaDaNuvemOut]

    @classmethod
    def de(cls, nuvem: NuvemDeConflito, idioma: str = "pt") -> "NuvemOut":
        avisos = nuvem.avisos_de_formulacao(idioma)
        return cls(
            id=nuvem.projeto.id,
            nome=nuvem.projeto.nome,
            ferramenta=nuvem.projeto.ferramenta,
            descricao_do_problema=nuvem.projeto.descricao_do_problema,
            racional=nuvem.racional,
            criado_em=nuvem.projeto.criado_em,
            alterado_em=nuvem.projeto.alterado_em,
            origem=(
                OrigemOut(
                    ferramenta=nuvem.origem.ferramenta,
                    projeto_id=nuvem.origem.projeto_id,
                    nos=list(nuvem.origem.nos),
                    leitura=nuvem.leitura_da_origem(),
                )
                if nuvem.origem
                else None
            ),
            entidades=[
                EntidadeDaNuvemOut(
                    papel=papel.value,
                    no_id=nuvem.entidade(papel).id,
                    texto=nuvem.texto(papel),
                    posicao=PosicaoIO.de(nuvem.entidade(papel).posicao),
                    avisos=[AvisoOut.de(a) for a in avisos[papel]],
                )
                for papel in PapelDaEntidade
            ],
            arestas=[
                ArestaDaNuvemOut(
                    chave=chave.value,
                    classe=nuvem.classe(chave).value,
                    aresta_id=nuvem.aresta(chave).id,
                    leitura=nuvem.leitura(chave),
                    premissas=[
                        PremissaOut.de(p, nuvem.injecoes_da_premissa(p.id))
                        for p in nuvem.premissas(chave)
                    ],
                )
                for chave in ChaveDaAresta
            ],
        )


class CompletudeOut(Resposta):
    sustentadas: int
    total: int


class AvisosDaEntidadeOut(Resposta):
    papel: str
    avisos: list[AvisoOut]


class ValidacaoDaNuvemOut(Resposta):
    """RF-14: progresso, avisos e pendências — informa e prioriza, nunca trava."""

    completude: CompletudeOut
    modelada: bool
    arestas_sem_premissa: list[str]
    arestas_sem_injecao: list[str]
    separacoes_ausentes: list[str]
    avisos: list[AvisosDaEntidadeOut]

    @classmethod
    def de(cls, validacao: ValidacaoDaNuvem) -> "ValidacaoDaNuvemOut":
        sustentadas, total = validacao.completude
        return cls(
            completude=CompletudeOut(sustentadas=sustentadas, total=total),
            modelada=validacao.modelada,
            arestas_sem_premissa=[c.value for c in validacao.arestas_sem_premissa],
            arestas_sem_injecao=[c.value for c in validacao.arestas_sem_injecao],
            separacoes_ausentes=[s.value for s in validacao.separacoes_ausentes],
            avisos=[
                AvisosDaEntidadeOut(
                    papel=papel.value, avisos=[AvisoOut.de(a) for a in lista]
                )
                for papel, lista in validacao.avisos.items()
            ],
        )


class PosicaoDeSolucaoOut(Resposta):
    """RF-31: uma das **sete** posições da visão de solução — vazia é pendência."""

    chave: str
    classe: str
    leitura: str
    pendente: bool
    injecoes: list[InjecaoOut]


class SolucaoOut(Resposta):
    posicoes: list[PosicaoDeSolucaoOut]

    @classmethod
    def de(cls, nuvem: NuvemDeConflito) -> "SolucaoOut":
        visao = nuvem.visao_de_solucao()
        return cls(
            posicoes=[
                PosicaoDeSolucaoOut(
                    chave=chave.value,
                    classe=nuvem.classe(chave).value,
                    leitura=nuvem.leitura(chave),
                    pendente=not injecoes,
                    injecoes=[InjecaoOut.de(i) for i in injecoes],
                )
                for chave, injecoes in visao.items()
            ]
        )


class LinhaDaMatrizOut(Resposta):
    chave: str
    leitura: str
    premissas: list[PremissaOut]


class MatrizOut(Resposta):
    """RF-34: a matriz aresta × premissas × injeções — projeção do MESMO dado."""

    linhas: list[LinhaDaMatrizOut]

    @classmethod
    def de(cls, nuvem: NuvemDeConflito) -> "MatrizOut":
        return cls(
            linhas=[
                LinhaDaMatrizOut(
                    chave=chave.value,
                    leitura=nuvem.leitura(chave),
                    premissas=[PremissaOut.de(p, injecoes) for p, injecoes in itens],
                )
                for chave, itens in nuvem.matriz().items()
            ]
        )


class ArquivamentoOut(Resposta):
    """RF-15: o ato responde QUANTAS injeções foram junto — nunca em silêncio."""

    premissa_id: UUID
    injecoes_arquivadas: int


class GeracaoOut(Resposta):
    """A pré-visualização (RI-06): dado estruturado, **nada aplicado**.

    `action_id` diz por onde a aplicação passa: a ação governada do catálogo, que nasce
    `action_proposal` e atravessa a máquina de estados do servidor (RF-23). Devolver o
    resultado junto do nome da ação é o que permite à interface montar o diff e o botão
    sem inventar rota nenhuma.
    """

    action_id: str
    resultado: dict[str, Any]
    aviso: str


class SugestaoDePremissaOut(Resposta):
    texto: str
    injecoes: list["SugestaoDeInjecaoOut"]


class SugestaoDeInjecaoOut(Resposta):
    texto: str
    separacao: str | None


class SugestoesDePremissaOut(Resposta):
    action_id: str
    aresta: str
    sugestoes: list[SugestaoDePremissaOut]
    aviso: str


class SugestoesDeInjecaoOut(Resposta):
    action_id: str
    premissa_id: UUID
    sugestoes: list[SugestaoDeInjecaoOut]
    aviso: str


# -- entrada do M3 ---------------------------------------------------------------------


class TextoDaEntidadeIn(Pedido):
    texto: str


class RacionalIn(Pedido):
    racional: str = ""


class PremissaIn(Pedido):
    texto: str


class OrdemDePremissasIn(Pedido):
    ordem: list[UUID]


class EstadoDaPremissaIn(Pedido):
    estado: str
    justificativa: str = ""


class InjecaoIn(Pedido):
    texto: str
    separacao: str | None = None


class TextoDaInjecaoIn(Pedido):
    texto: str


class SeparacaoIn(Pedido):
    separacao: str | None = None


class StatusDeInjecaoIn(Pedido):
    status: str
    justificativa: str = ""


class NarrativaIn(Pedido):
    narrativa: str = ""


class DerivacaoIn(Pedido):
    """INT-05: o pedido do encadeamento — a ARA de origem e os UDEs que motivam a nuvem."""

    ara_projeto_id: UUID
    no_ids: list[UUID]
    nome: str


SugestaoDePremissaOut.model_rebuild()
