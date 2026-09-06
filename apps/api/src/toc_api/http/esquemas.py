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
from typing import Any, Literal
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


# -- a proposta de ação, pela superfície da própria aplicação (spec 006, RI-01) ----------
#
# Por que estes três modelos existem, já que o fio do Anexo A também decide proposta: o
# §A.6 decide **dentro de uma sessão de conversa**, que é o caminho do hospedeiro. A
# interface desta aplicação não conversa para aceitar um diff que ela já mostrou inteiro —
# ela precisa do identificador da proposta em **dado estruturado**, e a borda federada
# (`POST /aph/actions/{action_id}`) devolve `{"result": <texto>}` por contrato do
# hospedeiro. Ler o `proposal_id` de dentro de uma frase seria o cliente discriminando por
# mensagem, que é exatamente o que o §A.7 proíbe. Mesmos casos de uso, mesma máquina de
# estados, mesmo traço: o que muda é o consumidor.


class PropostaIn(Pedido):
    """O pedido que leva uma ação governada ao gate humano.

    `origem` é **dado, nunca desvio de fluxo** (APH-5.9, ADR 0009 da irmã): ela descreve a
    procedência do CONTEÚDO, que só o cliente conhece — o servidor não tem como saber se a
    frase foi digitada por uma pessoa ou produzida pela assistência. O padrão é `ia`
    porque esta superfície nasce para o conteúdo assistido; edição humana direta não passa
    por proposta nenhuma, passa pelos comandos do agregado.
    """

    action_id: str
    args: dict[str, Any] = Field(default_factory=dict)
    origem: Literal["humano", "ia"] = "ia"
    #: O `context_hash` do §A.4, quando a tela que originou a proposta o declara.
    contexto_hash: str | None = None


class DecisaoIn(Pedido):
    """O gate humano: confirmar ou recusar. Mesmos campos do §A.6, mesmos significados."""

    aprovado: bool
    context_hash: str | None = None
    idempotency_key: str | None = None


class DesfechoDeAlvoOut(Resposta):
    """APH-5.9(b): lote responde alvo a alvo — sete executaram e um não é dado, não prosa."""

    target: str
    status: str
    message: str = ""


class PropostaOut(Resposta):
    """A proposta como a superfície de confirmação a mostra (RI-01/RI-03 da spec 006).

    `alvos` e `quantidade_de_alvos` viajam **antes** da decisão porque a contagem de
    afetados é o que a pessoa precisa ler para decidir; `status` e `outcomes` só existem
    depois dela. `estado` é o da máquina de estados; `status` é o desfecho do §A.3 — os
    dois aparecem porque respondem perguntas diferentes ("onde ela está" e "no que deu").
    """

    proposal_id: str
    action_id: str
    titulo: str
    risk: str
    requires_confirmation: bool
    origem: str
    estado: str
    alvos: list[str]
    quantidade_de_alvos: int
    criada_em: datetime
    vence_em: datetime
    status: str | None = None
    mensagem: str = ""
    outcomes: list[DesfechoDeAlvoOut] = Field(default_factory=list)

    @classmethod
    def de(cls, proposta: Any, *, titulo: str) -> "PropostaOut":
        desfecho = proposta.desfecho
        return cls(
            proposal_id=proposta.proposal_id,
            action_id=proposta.action_id,
            titulo=titulo,
            risk=proposta.risk,
            requires_confirmation=proposta.requer_confirmacao,
            origem=proposta.origem.value,
            estado=proposta.estado,
            alvos=list(proposta.alvos),
            quantidade_de_alvos=proposta.quantidade_de_alvos,
            criada_em=proposta.criada_em,
            vence_em=proposta.vence_em,
            status=desfecho.status if desfecho else None,
            mensagem=desfecho.mensagem if desfecho else "",
            outcomes=[
                DesfechoDeAlvoOut(target=alvo, status=status, message=msg)
                for alvo, status, msg in (desfecho.outcomes if desfecho else ())
            ],
        )


# ---------------------------------------------------------------------------------------
# M4 · Árvores de Futuro e Implementação (spec 008)
#
# A projeção segue a mesma disciplina do M2 e do M3: **saída é projeção, não o agregado**.
# O que sai daqui é o que a tela precisa — papel, leitura montada, resumo quantitativo —,
# nunca o evento de domínio nem o identificador do inquilino.
# ---------------------------------------------------------------------------------------


class NoDaArvoreOut(Resposta):
    """Um nó com o PAPEL na ferramenta — a diferença visual e semântica do M4 (RI-01)."""

    id: UUID
    papel: str
    titulo: str
    descricao: str = ""
    posicao: PosicaoIO = PosicaoIO()
    recolhido: bool = False

    @classmethod
    def de(cls, no: No, papel: str) -> "NoDaArvoreOut":
        return cls(
            id=no.id,
            papel=papel,
            titulo=no.titulo,
            descricao=no.descricao,
            posicao=PosicaoIO.de(no.posicao),
            recolhido=no.recolhido,
        )


class CriarNoDaArvoreIn(Pedido):
    papel: str
    titulo: str
    descricao: str = ""
    posicao: PosicaoIO | None = None


class EditarNoDaArvoreIn(Pedido):
    titulo: str | None = None
    descricao: str | None = None


class MudarPapelIn(Pedido):
    papel: str


class LigarIn(Pedido):
    origem_id: UUID
    destino_id: UUID
    rotulo: str = ""


# -- E4.1 · Árvore da Realidade Futura ---------------------------------------------------


class ExameDoEloOut(Resposta):
    estado: str
    reserva: str = ""

    @classmethod
    def de(cls, exame) -> "ExameDoEloOut":
        return cls(estado=exame.estado.value, reserva=exame.reserva)


class EloDaArfOut(Resposta):
    """A aresta de SUFICIÊNCIA, com a leitura montada dos textos atuais (RF-03)."""

    id: UUID
    origem_id: UUID
    destino_id: UUID
    rotulo: str = ""
    leitura: str
    exame: ExameDoEloOut


class ConectorDaArfOut(Resposta):
    id: UUID
    destino_id: UUID
    arestas: list[UUID]
    leitura: str


class EspelhoOut(Resposta):
    no_id: UUID
    ude_id: UUID
    projeto_de_origem_id: UUID | None = None


class EspelharIn(Pedido):
    no_id: UUID
    ude_id: UUID
    projeto_de_origem_id: UUID | None = None


class RamoNegativoOut(Resposta):
    id: UUID
    raiz_id: UUID
    estado: str
    injecao_de_corte_id: UUID | None = None
    justificativa: str = ""
    autor: str = ""

    @classmethod
    def de(cls, ramo) -> "RamoNegativoOut":
        return cls(
            id=ramo.id,
            raiz_id=ramo.raiz_id,
            estado=ramo.estado.value,
            injecao_de_corte_id=ramo.injecao_de_corte_id,
            justificativa=ramo.justificativa,
            autor=ramo.autor,
        )


class MarcarRamoIn(Pedido):
    no_id: UUID


class MudarRamoIn(Pedido):
    """O autor de um `aceito` vem do PRINCIPAL, nunca daqui — a regra do parecer do M2."""

    estado: str
    injecao_de_corte_id: UUID | None = None
    justificativa: str = ""


class CoberturaOut(Resposta):
    ude_id: UUID
    espelhado_por: UUID | None = None
    alcancado: bool = False


class VerificacaoDaArfOut(Resposta):
    """RF-11: o relatório estrutural — pendências com identificador, para o foco no canvas."""

    eds_sem_caminho: list[UUID]
    injecoes_sem_efeito: int
    injecoes_sem_efeito_ids: list[UUID]
    ramos_abertos: list[UUID]
    cobertura: list[CoberturaOut]
    sem_origem_vinculada: bool
    pronta: bool

    @classmethod
    def de(cls, verificacao) -> "VerificacaoDaArfOut":
        return cls(
            eds_sem_caminho=list(verificacao.eds_sem_caminho),
            injecoes_sem_efeito=len(verificacao.injecoes_sem_efeito),
            injecoes_sem_efeito_ids=list(verificacao.injecoes_sem_efeito),
            ramos_abertos=list(verificacao.ramos_abertos),
            cobertura=[
                CoberturaOut(
                    ude_id=c.ude_id, espelhado_por=c.espelhado_por, alcancado=c.alcancado
                )
                for c in verificacao.cobertura
            ],
            sem_origem_vinculada=verificacao.sem_origem_vinculada,
            pronta=verificacao.pronta,
        )


class PontaOut(Resposta):
    """A extremidade tipada de uma costura — ferramenta, projeto, elementos e papel."""

    ferramenta: str
    projeto_id: UUID
    elementos: list[UUID] = []
    papel: str = ""

    @classmethod
    def de(cls, ponta) -> "PontaOut | None":
        if ponta is None:
            return None
        return cls(
            ferramenta=ponta.ferramenta,
            projeto_id=ponta.projeto_id,
            elementos=list(ponta.elementos),
            papel=ponta.papel,
        )


class ArfOut(Resposta):
    id: UUID
    nome: str
    ferramenta: str
    descricao_do_problema: str = ""
    versao: int
    origem: PontaOut | None = None
    udes_da_cadeia: list[UUID] = []
    nos: list[NoDaArvoreOut]
    elos: list[EloDaArfOut]
    conectores: list[ConectorDaArfOut]
    espelhos: list[EspelhoOut]
    ramos: list[RamoNegativoOut]
    verificacao: VerificacaoDaArfOut

    @classmethod
    def de(cls, arf) -> "ArfOut":
        projeto = arf.projeto
        return cls(
            id=projeto.id,
            nome=projeto.nome,
            ferramenta=projeto.ferramenta,
            descricao_do_problema=projeto.descricao_do_problema,
            versao=projeto.versao,
            origem=PontaOut.de(arf.origem),
            udes_da_cadeia=list(arf.udes_da_cadeia),
            nos=[NoDaArvoreOut.de(n, arf.papel_do_no(n.id).value) for n in arf.nos],
            elos=[
                EloDaArfOut(
                    id=a.id,
                    origem_id=a.origem_id,
                    destino_id=a.destino_id,
                    rotulo=a.rotulo,
                    leitura=arf.leitura_do_elo(a.id),
                    exame=ExameDoEloOut.de(arf.exame(a.id)),
                )
                for a in arf.arestas
            ],
            conectores=[
                ConectorDaArfOut(
                    id=c.id,
                    destino_id=c.destino_id,
                    arestas=list(c.arestas),
                    leitura=arf.leitura_do_conector(c.id),
                )
                for c in arf.conectores
            ],
            espelhos=[
                EspelhoOut(
                    no_id=no_id,
                    ude_id=e.ude_id,
                    projeto_de_origem_id=e.projeto_de_origem_id,
                )
                for no_id, e in arf.espelhos()
            ],
            ramos=[RamoNegativoOut.de(r) for r in arf.ramos()],
            verificacao=VerificacaoDaArfOut.de(arf.verificar()),
        )


class CriarArfIn(Pedido):
    nome: str
    descricao_do_problema: str = ""


class ExameIn(Pedido):
    estado: str
    reserva: str = ""


class ConectorDeSuficienciaIn(Pedido):
    arestas: list[UUID]


# -- E4.2 · Árvore de Pré-Requisitos -----------------------------------------------------


class DependenciaOut(Resposta):
    """A aresta de NECESSIDADE: "A precisa existir antes de B" (RF-16, RN-05)."""

    id: UUID
    antes_id: UUID
    depois_id: UUID
    leitura: str


class DependenciaIn(Pedido):
    antes_id: UUID
    depois_id: UUID


class JulgamentoOut(Resposta):
    autor: str
    valido: bool
    justificativa: str
    instante: datetime


class JulgamentoIn(Pedido):
    """O autor vem do principal — nunca do corpo do pedido (RN-07 com a regra do M2)."""

    valido: bool
    justificativa: str


class ParOut(Resposta):
    id: UUID
    obstaculo_id: UUID
    objetivo_intermediario_id: UUID
    teste_de_validade: str
    julgamentos: list[JulgamentoOut]

    @classmethod
    def de(cls, apr, par) -> "ParOut":
        return cls(
            id=par.id,
            obstaculo_id=par.obstaculo_id,
            objetivo_intermediario_id=par.objetivo_intermediario_id,
            teste_de_validade=apr.leitura_do_teste_de_validade(par.id),
            julgamentos=[
                JulgamentoOut(
                    autor=j.autor,
                    valido=j.valido,
                    justificativa=j.justificativa,
                    instante=j.instante,
                )
                for j in par.julgamentos
            ],
        )


class ParearIn(Pedido):
    obstaculo_id: UUID
    objetivo_intermediario_id: UUID


class ElipseOut(Resposta):
    id: UUID
    destino_id: UUID
    dependencias: list[UUID]
    leitura: str


class ElipseIn(Pedido):
    dependencias: list[UUID]


class SequenciamentoOut(Resposta):
    camadas: list[list[UUID]]
    ramos_paralelos: list[list[UUID]]
    elipses: list[UUID]
    ciclos: list[list[UUID]]
    obstaculos_sem_oi: list[UUID]
    objetivos_sem_obstaculo: list[UUID]
    bloqueado: bool
    completo: bool

    @classmethod
    def de(cls, sequencia) -> "SequenciamentoOut":
        return cls(
            camadas=[list(c) for c in sequencia.camadas],
            ramos_paralelos=[list(r) for r in sequencia.ramos_paralelos],
            elipses=list(sequencia.elipses),
            ciclos=[list(c) for c in sequencia.ciclos],
            obstaculos_sem_oi=list(sequencia.obstaculos_sem_oi),
            objetivos_sem_obstaculo=list(sequencia.objetivos_sem_obstaculo),
            bloqueado=sequencia.bloqueado,
            completo=sequencia.completo,
        )


class LinhaDoResumoOut(Resposta):
    camada: int | None = None
    objetivo_intermediario: str | None = None
    objetivo_intermediario_id: UUID | None = None
    obstaculo: str | None = None
    obstaculo_id: UUID | None = None
    depende_de: list[str] = []
    julgamento: str = ""


class ResumoDaAprOut(Resposta):
    """RF-25: a tabela que vai à reunião, na ordem das camadas."""

    linhas: list[LinhaDoResumoOut]


class AvisoDeVerbalizacaoOut(Resposta):
    codigo: str
    trecho: str
    explicacao: str
    exemplo: str


class VerbalizacaoOut(Resposta):
    """RF-20/RN-08: aviso com trecho apontado — orientação, nunca veto."""

    papel: str
    veredito: str
    avisos: list[AvisoDeVerbalizacaoOut]
    versao_do_lexico: str

    @classmethod
    def de(cls, avaliacao) -> "VerbalizacaoOut":
        return cls(
            papel=avaliacao.papel.value,
            veredito=avaliacao.veredito.value,
            avisos=[
                AvisoDeVerbalizacaoOut(
                    codigo=a.codigo.value,
                    trecho=a.trecho,
                    explicacao=a.explicacao,
                    exemplo=a.exemplo,
                )
                for a in avaliacao.avisos
            ],
            versao_do_lexico=avaliacao.versao_do_lexico,
        )


class AprOut(Resposta):
    id: UUID
    nome: str
    ferramenta: str
    descricao_do_problema: str = ""
    versao: int
    origem: PontaOut | None = None
    objetivo: NoDaArvoreOut
    nos: list[NoDaArvoreOut]
    dependencias: list[DependenciaOut]
    pares: list[ParOut]
    elipses: list[ElipseOut]
    sequenciamento: SequenciamentoOut

    @classmethod
    def de(cls, apr) -> "AprOut":
        projeto = apr.projeto
        return cls(
            id=projeto.id,
            nome=projeto.nome,
            ferramenta=projeto.ferramenta,
            descricao_do_problema=projeto.descricao_do_problema,
            versao=projeto.versao,
            origem=PontaOut.de(apr.origem),
            objetivo=NoDaArvoreOut.de(apr.objetivo, "objetivo"),
            nos=[NoDaArvoreOut.de(n, apr.papel_do_no(n.id).value) for n in apr.nos],
            dependencias=[
                DependenciaOut(
                    id=a.id,
                    antes_id=a.origem_id,
                    depois_id=a.destino_id,
                    leitura=apr.leitura_da_dependencia(a.id),
                )
                for a in apr.arestas
            ],
            pares=[ParOut.de(apr, p) for p in apr.pares()],
            elipses=[
                ElipseOut(
                    id=e.id,
                    destino_id=e.destino_id,
                    dependencias=list(e.dependencias),
                    leitura=apr.leitura_da_elipse(e.id),
                )
                for e in apr.elipses()
            ],
            sequenciamento=SequenciamentoOut.de(apr.sequenciar()),
        )


class CriarAprIn(Pedido):
    nome: str
    objetivo: str
    descricao_do_problema: str = ""


# -- E4.3 · Árvore de Transição ----------------------------------------------------------


class PassoOut(Resposta):
    id: UUID
    acao: str
    necessidade: str
    resultado_esperado: str
    status: str
    motivo_do_bloqueio: str = ""
    resultado_real: str = ""
    divergente: bool = False
    leitura: str

    @classmethod
    def de(cls, no_id: UUID, ficha) -> "PassoOut":
        return cls(
            id=no_id,
            acao=ficha.acao,
            necessidade=ficha.necessidade,
            resultado_esperado=ficha.resultado_esperado,
            status=ficha.status.value,
            motivo_do_bloqueio=ficha.motivo_do_bloqueio,
            resultado_real=ficha.resultado_real,
            divergente=ficha.divergente,
            leitura=ficha.leitura(),
        )


class RegistrarPassoIn(Pedido):
    """RN-10: os três campos são obrigatórios — sem valor padrão e sem exceção."""

    acao: str
    necessidade: str
    resultado_esperado: str
    posicao: PosicaoIO | None = None


class EditarPassoIn(Pedido):
    acao: str | None = None
    necessidade: str | None = None
    resultado_esperado: str | None = None


class StatusDoPassoIn(Pedido):
    status: str
    motivo: str = ""
    resultado_real: str = ""


class PrecedenciaIn(Pedido):
    antes_id: UUID
    depois_id: UUID


class PrecedenciaOut(Resposta):
    id: UUID
    antes_id: UUID
    depois_id: UUID


class AtOut(Resposta):
    id: UUID
    nome: str
    ferramenta: str
    descricao_do_problema: str = ""
    versao: int
    alvo: PontaOut | None = None
    passos: list[PassoOut]
    precedencias: list[PrecedenciaOut]
    ordem_de_leitura: list[UUID]
    inalcancaveis: list[UUID]
    resumo: dict[str, int]

    @classmethod
    def de(cls, at) -> "AtOut":
        projeto = at.projeto
        return cls(
            id=projeto.id,
            nome=projeto.nome,
            ferramenta=projeto.ferramenta,
            descricao_do_problema=projeto.descricao_do_problema,
            versao=projeto.versao,
            alvo=PontaOut.de(at.alvo),
            passos=[PassoOut.de(no_id, ficha) for no_id, ficha in at.fichas()],
            precedencias=[
                PrecedenciaOut(id=a.id, antes_id=a.origem_id, depois_id=a.destino_id)
                for a in at.precedencias
            ],
            ordem_de_leitura=list(at.ordem_de_leitura()),
            inalcancaveis=list(at.passos_inalcancaveis()),
            resumo=at.resumo_de_execucao(),
        )


class CriarAtIn(Pedido):
    nome: str
    descricao_do_problema: str = ""


# -- E4.4 · o encadeamento ---------------------------------------------------------------


class PromocaoIn(Pedido):
    ara_projeto_id: UUID
    no_ids: list[UUID]
    nome: str


class SemeaduraIn(Pedido):
    nc_projeto_id: UUID
    injecao_id: UUID
    nome: str


class DerivacaoDeAprIn(Pedido):
    arf_projeto_id: UUID
    no_id: UUID
    nome: str
    objetivo: str | None = None


class DerivacaoDeAtIn(Pedido):
    apr_projeto_id: UUID
    no_id: UUID
    nome: str


class EloDaCadeiaOut(Resposta):
    referencia_id: UUID
    tipo: str
    origem: PontaOut
    destino: PontaOut
    estado: str
    motivo: str = ""


class CadeiaOut(Resposta):
    """RF-41: a travessia inteira, com o estado por elo — pendente NUNCA some (US-18)."""

    elos: list[EloDaCadeiaOut]
    ferramentas: list[str]
    resumo: dict[str, int]

    @classmethod
    def de(cls, cadeia) -> "CadeiaOut":
        return cls(
            elos=[
                EloDaCadeiaOut(
                    referencia_id=e.referencia_id,
                    tipo=e.tipo.value,
                    origem=PontaOut.de(e.origem),
                    destino=PontaOut.de(e.destino),
                    estado=e.estado.value,
                    motivo=e.motivo,
                )
                for e in cadeia.elos
            ],
            ferramentas=list(cadeia.ferramentas()),
            resumo=cadeia.resumo(),
        )


class ReferenciaOut(Resposta):
    id: UUID
    tipo: str
    origem: PontaOut
    destino: PontaOut
    estado: str
    motivo: str = ""

    @classmethod
    def de(cls, referencia) -> "ReferenciaOut":
        return cls(
            id=referencia.id,
            tipo=referencia.tipo.value,
            origem=PontaOut.de(referencia.origem),
            destino=PontaOut.de(referencia.destino),
            estado=referencia.estado.value,
            motivo=referencia.motivo,
        )


# ---------------------------------------------------------------------------------------
# M6 · Focalização (spec 009) — a jornada dos cinco passos
#
# A saída é PROJEÇÃO, e aqui isso tem consequência declarada: o cartão de vínculo carrega
# tipo, nome e estado do projeto de destino, e **nenhum conteúdo dele**. Copiar o título de
# um nó da Árvore da Realidade Atual para dentro desta resposta seria a sétima cópia que o
# núcleo M1 existe para impedir — e envelheceria no primeiro `PUT` do outro módulo.
# ---------------------------------------------------------------------------------------


class SistemaIO(Resposta):
    nome: str
    descricao: str = ""


class OrigemDaRestricaoOut(Resposta):
    """INT-02: de onde a restrição veio — a causa raiz de uma ARA, tipada."""

    ferramenta: str
    projeto_id: UUID
    no_id: UUID


class RestricaoOut(Resposta):
    id: UUID
    descricao: str
    tipo: Literal["fisica", "politica", "de_mercado"]
    justificativa: str
    autor: str
    registrada_em: datetime
    origem: OrigemDaRestricaoOut | None = None

    @classmethod
    def de(cls, restricao) -> "RestricaoOut":
        return cls(
            id=restricao.id,
            descricao=restricao.descricao,
            tipo=restricao.tipo.value,
            justificativa=restricao.justificativa,
            autor=restricao.autor,
            registrada_em=restricao.registrada_em,
            origem=None
            if restricao.origem is None
            else OrigemDaRestricaoOut(
                ferramenta=restricao.origem.ferramenta,
                projeto_id=restricao.origem.projeto_id,
                no_id=restricao.origem.no_id,
            ),
        )


class DecisaoOut(Resposta):
    texto: str
    autor: str
    instante: datetime


class NotaOut(Resposta):
    id: UUID
    texto: str
    autor: str
    instante: datetime


class ReaberturaOut(Resposta):
    justificativa: str
    autor: str
    instante: datetime


class VinculoOut(Resposta):
    """RI-03: o cartão — tipo, projeto, estado e navegação. Sem conteúdo do outro módulo."""

    id: UUID
    ferramenta: Literal["ara", "nc", "arf", "apr", "at"]
    projeto_id: UUID
    papel: str = ""
    justificativa: str = ""
    canonico: bool = True
    estado: Literal["ativo", "arquivado", "ausente"] = "ativo"
    nome: str = ""
    legenda: str = ""

    @classmethod
    def de(cls, vinculo, resolvido=None) -> "VinculoOut":
        return cls(
            id=vinculo.id,
            ferramenta=vinculo.tipo.value,
            projeto_id=vinculo.projeto_id,
            papel=vinculo.papel,
            justificativa=vinculo.justificativa,
            canonico=vinculo.canonico,
            estado="ativo" if resolvido is None else resolvido.estado.value,
            nome="" if resolvido is None else resolvido.nome,
            legenda="" if resolvido is None else resolvido.legenda,
        )


class PendenciaOut(Resposta):
    passo: str
    regra: str
    detalhe: str


class PassoNaJornadaOut(Resposta):
    tipo: Literal["identificar", "explorar", "subordinar", "elevar", "recomecar"]
    estado: Literal["pendente", "em_andamento", "concluido"]
    decisao: str = ""
    autor_da_decisao: str = ""
    decisoes: list[DecisaoOut] = Field(default_factory=list)
    notas: list[NotaOut] = Field(default_factory=list)
    reaberturas: list[ReaberturaOut] = Field(default_factory=list)
    vinculos: list[VinculoOut] = Field(default_factory=list)
    canonicas: list[str] = Field(default_factory=list)
    avisos: list[str] = Field(default_factory=list)
    herdado: list[str] = Field(default_factory=list)
    pendencias: list[PendenciaOut] = Field(default_factory=list)


class DecisaoHerdadaOut(Resposta):
    id: UUID
    ciclo_de_origem: int
    passo: str
    texto: str
    veredito: Literal["pendente", "mantida", "revogada"]
    justificativa: str = ""
    autor: str = ""
    julgada_em: datetime | None = None


class JornadaOut(Resposta):
    """RF-12: o mapa do ciclo — os cinco passos com estado, herança e pendências."""

    ciclo_id: UUID
    ordem: int
    estado: Literal["aberto", "fechado"]
    somente_leitura: bool
    passo_atual: str
    restricao: RestricaoOut | None = None
    passos: list[PassoNaJornadaOut] = Field(default_factory=list)
    heranca: list[DecisaoHerdadaOut] = Field(default_factory=list)
    herancas_pendentes: int = 0
    ciclos_no_total: int = 1
    passos_concluidos: int = 0

    @classmethod
    def de(cls, mapa, ciclo, *, resolvidos=None) -> "JornadaOut":
        por_vinculo = {r.vinculo_id: r for r in (resolvidos or [])}
        concluidos, _ = mapa.progresso
        return cls(
            ciclo_id=mapa.ciclo_id,
            ordem=mapa.ordem,
            estado=mapa.estado.value,
            # RI-04: ciclo fechado abre somente leitura — e quem diz isso é o servidor,
            # não um `if` na tela.
            somente_leitura=mapa.estado.value == "fechado",
            passo_atual=mapa.passo_atual.value,
            restricao=None if mapa.restricao is None else RestricaoOut.de(mapa.restricao),
            passos=[
                PassoNaJornadaOut(
                    tipo=p.tipo.value,
                    estado=p.estado.value,
                    decisao=p.decisao,
                    autor_da_decisao=p.autor_da_decisao,
                    decisoes=[
                        DecisaoOut(texto=d.texto, autor=d.autor, instante=d.instante)
                        for d in ciclo.passo(p.tipo).decisoes
                    ],
                    notas=[
                        NotaOut(id=n.id, texto=n.texto, autor=n.autor, instante=n.instante)
                        for n in ciclo.passo(p.tipo).notas
                    ],
                    reaberturas=[
                        ReaberturaOut(
                            justificativa=r.justificativa, autor=r.autor, instante=r.instante
                        )
                        for r in ciclo.passo(p.tipo).reaberturas
                    ],
                    vinculos=[VinculoOut.de(v, por_vinculo.get(v.id)) for v in p.vinculos],
                    canonicas=[c.value for c in p.canonicas],
                    avisos=list(p.avisos),
                    herdado=list(p.herdado),
                    pendencias=[
                        PendenciaOut(passo=x.passo.value, regra=x.regra, detalhe=x.detalhe)
                        for x in p.pendencias
                    ],
                )
                for p in mapa.passos
            ],
            heranca=[
                DecisaoHerdadaOut(
                    id=h.id,
                    ciclo_de_origem=h.ciclo_de_origem,
                    passo=h.passo.value,
                    texto=h.texto,
                    veredito=h.veredito.value,
                    justificativa=h.justificativa,
                    autor=h.autor,
                    julgada_em=h.julgada_em,
                )
                for h in mapa.heranca
            ],
            herancas_pendentes=mapa.herancas_pendentes,
            ciclos_no_total=mapa.ciclos_no_total,
            passos_concluidos=concluidos,
        )


class CicloNaLinhaOut(Resposta):
    """RF-17: uma linha da história da análise."""

    ciclo_id: UUID
    ordem: int
    estado: Literal["aberto", "fechado"]
    restricao: str | None = None
    tipo_de_restricao: str | None = None
    aberto_em: datetime
    fechado_em: datetime | None = None
    decisoes: int = 0
    vinculos: int = 0
    herancas: int = 0
    herancas_pendentes: int = 0
    passo_atual: str = "identificar"

    @classmethod
    def de(cls, entrada) -> "CicloNaLinhaOut":
        return cls(
            ciclo_id=entrada.ciclo_id,
            ordem=entrada.ordem,
            estado=entrada.estado.value,
            restricao=entrada.restricao,
            tipo_de_restricao=None
            if entrada.tipo_de_restricao is None
            else entrada.tipo_de_restricao.value,
            aberto_em=entrada.aberto_em,
            fechado_em=entrada.fechado_em,
            decisoes=entrada.decisoes,
            vinculos=entrada.vinculos,
            herancas=entrada.herancas,
            herancas_pendentes=entrada.herancas_pendentes,
            passo_atual=entrada.passo_atual.value,
        )


class AnaliseResumoOut(Resposta):
    """RF-03/RI-07: passo atual e restrição vigente como colunas de primeira classe."""

    projeto_id: UUID
    nome: str
    sistema: str
    ciclo: int
    passo_atual: str
    restricao: str | None = None
    tipo_de_restricao: str | None = None
    pendencias: int = 0
    herancas_pendentes: int = 0
    alterado_em: datetime

    @classmethod
    def de(cls, linha) -> "AnaliseResumoOut":
        return cls(
            projeto_id=linha.projeto_id,
            nome=linha.nome,
            sistema=linha.sistema,
            ciclo=linha.ciclo,
            passo_atual=linha.passo_atual.value,
            restricao=linha.restricao,
            tipo_de_restricao=None
            if linha.tipo_de_restricao is None
            else linha.tipo_de_restricao.value,
            pendencias=linha.pendencias,
            herancas_pendentes=linha.herancas_pendentes,
            alterado_em=linha.alterado_em,
        )


class AnaliseOut(Resposta):
    """A leitura inteira: o projeto do M1, o sistema analisado, a jornada e a história."""

    projeto: ProjetoResumoOut
    sistema: SistemaIO
    jornada: JornadaOut
    linha_do_tempo: list[CicloNaLinhaOut] = Field(default_factory=list)

    @classmethod
    def de(cls, analise, mapa, *, resolvidos=None) -> "AnaliseOut":
        return cls(
            projeto=ProjetoResumoOut.de(analise.projeto),
            sistema=SistemaIO(
                nome=analise.sistema.nome, descricao=analise.sistema.descricao
            ),
            jornada=JornadaOut.de(
                mapa, analise.ciclo(mapa.ciclo_id), resolvidos=resolvidos
            ),
            linha_do_tempo=[CicloNaLinhaOut.de(e) for e in analise.linha_do_tempo()],
        )


class ReferenciaReversaOut(Resposta):
    """L-03: quem cita este projeto de ferramenta — resolvido por consulta ao M6."""

    analise_id: UUID
    analise_nome: str
    passo: str
    vinculo: VinculoOut


# -- entrada do M6 -----------------------------------------------------------------------


class CriarAnaliseIn(Pedido):
    nome: str = Field(min_length=1, max_length=200)
    sistema: str = Field(min_length=1, max_length=200)
    descricao_do_sistema: str = Field(default="", max_length=4000)


class RestricaoIn(Pedido):
    descricao: str = Field(min_length=1, max_length=300)
    tipo: Literal["fisica", "politica", "de_mercado"]
    justificativa: str = Field(min_length=1, max_length=4000)
    autor: str = Field(min_length=1, max_length=200)
    origem: OrigemDaRestricaoOut | None = None


class EditarRestricaoIn(Pedido):
    """RF-07: **sem `tipo`** — trocar o alvo da análise é recomeçar, não editar (RN-03).

    A ausência do campo é o requisito: um esquema fechado (`extra="forbid"`) recusa
    `tipo` na borda, com `422`, antes de qualquer caso de uso ser montado.
    """

    descricao: str | None = Field(default=None, min_length=1, max_length=300)
    justificativa: str | None = Field(default=None, min_length=1, max_length=4000)


class ConclusaoDePassoIn(Pedido):
    decisao: str = Field(min_length=1, max_length=4000)
    autor: str = Field(min_length=1, max_length=200)


class ReaberturaIn(Pedido):
    justificativa: str = Field(min_length=1, max_length=4000)
    autor: str = Field(min_length=1, max_length=200)


class NotaIn(Pedido):
    texto: str = Field(min_length=1, max_length=4000)
    autor: str = Field(min_length=1, max_length=200)


class VinculoIn(Pedido):
    ferramenta: Literal["ara", "nc", "arf", "apr", "at"]
    projeto_id: UUID
    papel: str = Field(default="", max_length=200)
    justificativa: str = Field(default="", max_length=4000)


class VeredictoIn(Pedido):
    veredito: Literal["mantida", "revogada"]
    justificativa: str = Field(min_length=1, max_length=4000)
    autor: str = Field(min_length=1, max_length=200)


class CandidataARestricaoOut(Resposta):
    """RF-19: a candidata que `toc.suggest_constraint` propõe — nó de origem + racional."""

    no_id: UUID
    titulo: str
    racional: str
    udes_alcancados: int = 0
    fracao: float = 0.0


class SugestaoDeRestricaoOut(Resposta):
    ara_projeto_id: UUID
    action_id: str
    aviso: str
    candidatas: list[CandidataARestricaoOut] = Field(default_factory=list)
