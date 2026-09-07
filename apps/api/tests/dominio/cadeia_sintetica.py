"""A cadeia sintética das cinco ferramentas da "Instituição Horizonte" (ADR 0006).

Siglas, uma vez neste arquivo: **ARA** — Árvore da Realidade Atual · **UDE** — Efeito
Indesejável · **NC** — Nuvem de Conflito · **ARF** — Árvore da Realidade Futura · **APR**
— Árvore de Pré-Requisitos · **AT** — Árvore de Transição · **OI** — Objetivo
Intermediário · **S&T** — Estratégia & Táticas · **TOC** — Teoria das Restrições · **ADR**
— *Architecture Decision Record* (Registro de Decisão Arquitetural).

Ela existe para a exportação consolidada (spec 011, RF-31 e RF-32) ter o que exportar: um
**projeto multi-ferramenta de verdade**, com a cadeia percorrida ponta a ponta e com o
estado que só a ferramenta conhece — ficha de UDE, parecer, exame de elo, conector "E",
premissa, injeção, espelho, ramo negativo, par obstáculo↔OI, elipse e ficha de passo. Se a
fixture fosse um projeto vazio, a ida e volta provaria que zero é igual a zero.

Nenhum dado real de pessoa entra aqui (ADR 0006): a instituição é fictícia e os autores
são **papéis** ("papel:facilitadora"), nunca nomes.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import UUID, uuid4

from toc_api.dominio.apr import ProjetoAPR
from toc_api.dominio.ara import (
    FichaDeUde,
    OrigemDoParecer,
    ParecerDeJulgamento,
    ProjetoARA,
    StatusDeValidacao,
    novo_projeto_ara,
)
from toc_api.dominio.arf import ProjetoARF
from toc_api.dominio.at import ProjetoAT, StatusDoPasso
from toc_api.dominio.encadeamento import (
    derivar_apr_de_arf,
    derivar_at_de_oi,
    promover_udes_para_nc,
    semear_arf_de_injecao,
)
from toc_api.dominio.identidade import DonoDoProjeto
from toc_api.dominio.nuvem import ChaveDaAresta, NuvemDeConflito, StatusDeInjecao
from toc_api.dominio.referencia import ReferenciaCruzada
from toc_api.dominio.snt import ArvoreSnT, CategoriaDoPasso, nova_arvore_snt
from toc_api.dominio.suficiencia import EstadoDoExame

AGORA = datetime(2026, 9, 6, 10, 0, tzinfo=timezone.utc)
DONO = DonoDoProjeto(inquilino_id="instituicao-horizonte", usuario_id="u-facilitadora")

UDES = (
    "A taxa de evasão no primeiro semestre é de 22%.",
    "O caixa da instituição fecha o trimestre negativo.",
)
INJECAO = "faseamento orçamentário condicionado a marco de receita"
EFEITO_FUTURO = "as duas frentes recebem verba no trimestre"
OBSTACULO = "Há apenas uma pessoa treinada no acompanhamento do marco"
OI = "Existem três pessoas treinadas e escaladas para o acompanhamento do marco"


@dataclass(frozen=True, slots=True)
class CadeiaSintetica:
    """As cinco ferramentas encadeadas mais os quatro vínculos que as costuram."""

    ara: ProjetoARA
    nuvem: NuvemDeConflito
    arf: ProjetoARF
    apr: ProjetoAPR
    at: ProjetoAT
    vinculos: tuple[ReferenciaCruzada, ...]

    @property
    def projetos(self) -> tuple[object, ...]:
        return (self.ara, self.nuvem, self.arf, self.apr, self.at)


def montar_cadeia(dono: DonoDoProjeto = DONO) -> CadeiaSintetica:
    """Percorre ARA → NC → ARF → APR → AT com estado em cada ferramenta."""
    ara = novo_projeto_ara(
        id=uuid4(), dono=dono, nome="Realidade atual da Instituição Horizonte", em=AGORA
    )
    udes: list[UUID] = []
    for enunciado in UDES:
        no = ara.adicionar_efeito(titulo=enunciado, em=AGORA, descricao="observado em três turmas")
        ara.marcar_ude(
            no.id,
            em=AGORA,
            ficha=FichaDeUde(
                area_impactada="coordenação de graduação",
                objetivo_afetado="retenção no primeiro ano",
                evidencias=("relatório sintético de matrícula",),
                frequencia="todo semestre",
                impactos_estimados="12 turmas",
            ),
        )
        ara.registrar_parecer(
            no.id,
            ParecerDeJulgamento(
                autor="papel:facilitadora",
                origem=OrigemDoParecer.HUMANO,
                favoravel=True,
                justificativa="a queixa é contínua e está na esfera da coordenação",
                instante=AGORA,
                criterios=("queixa_continua", "esfera_de_influencia"),
            ),
            em=AGORA,
        )
        ara.mudar_status(no.id, StatusDeValidacao.VALIDADO, em=AGORA)
        udes.append(no.id)
    causa = ara.adicionar_efeito(titulo="O acolhimento do primeiro ano não é acompanhado.", em=AGORA)
    elo_um = ara.ligar(causa.id, udes[0], em=AGORA)
    elo_dois = ara.ligar(causa.id, udes[1], em=AGORA)
    ara.examinar_elo(
        elo_um.id, EstadoDoExame.COM_RESERVA, em=AGORA, reserva="falta medir a coorte de 2025"
    )
    outra_causa = ara.adicionar_efeito(titulo="A tutoria de pares foi descontinuada.", em=AGORA)
    elo_tres = ara.ligar(outra_causa.id, udes[0], em=AGORA)
    ara.formar_conector_e((elo_um.id, elo_tres.id), em=AGORA)
    ara.drenar_eventos()

    promocao = promover_udes_para_nc(
        ara, no_ids=tuple(udes), id=uuid4(), nome="Dilema da expansão", em=AGORA
    )
    nuvem = promocao.nuvem
    premissa = nuvem.registrar_premissa(
        ChaveDaAresta.D_D_PRIME, "o orçamento é indivisível dentro do exercício", em=AGORA
    )
    nuvem.registrar_premissa(
        ChaveDaAresta.A_B, "sem receita nova a instituição não se sustenta", em=AGORA
    )
    injecao = nuvem.registrar_injecao(premissa.id, INJECAO, em=AGORA)
    nuvem.mudar_status_de_injecao(injecao.id, StatusDeInjecao.ESCOLHIDA, em=AGORA)
    nuvem.editar_racional("o grupo aceitou o faseamento por unanimidade", em=AGORA)
    nuvem.drenar_eventos()

    semeadura = semear_arf_de_injecao(
        nuvem, injecao_id=injecao.id, id=uuid4(), nome="Futuro da expansão", em=AGORA
    )
    arf = semeadura.arf
    semente = arf.injecoes[0]
    efeito = arf.adicionar_efeito_futuro(titulo=EFEITO_FUTURO, em=AGORA)
    elo_da_arf = arf.ligar(semente.id, efeito.id, em=AGORA)
    arf.examinar_elo(elo_da_arf.id, EstadoDoExame.SUFICIENTE, em=AGORA)
    arf.espelhar_ude(efeito.id, arf.udes_da_cadeia[0], em=AGORA)
    colateral = arf.adicionar_efeito_futuro(titulo="A equipe de matrícula fica sobrecarregada", em=AGORA)
    arf.ligar(efeito.id, colateral.id, em=AGORA)
    arf.marcar_ramo_negativo(colateral.id, em=AGORA)
    arf.drenar_eventos()

    derivacao = derivar_apr_de_arf(
        arf, no_id=efeito.id, id=uuid4(), nome="Implantação do faseamento", em=AGORA
    )
    apr = derivacao.apr
    obstaculo = apr.adicionar_obstaculo(titulo=OBSTACULO, em=AGORA)
    objetivo_intermediario = apr.adicionar_objetivo_intermediario(titulo=OI, em=AGORA)
    par = apr.parear(obstaculo.id, objetivo_intermediario.id, em=AGORA)
    apr.julgar_par(
        par.id,
        autor="papel:gestora",
        valido=True,
        justificativa="o treinamento remove o impedimento",
        em=AGORA,
    )
    apr.drenar_eventos()

    derivacao_at = derivar_at_de_oi(
        apr, no_id=objetivo_intermediario.id, id=uuid4(), nome="Transição do acompanhamento", em=AGORA
    )
    at = derivacao_at.at
    passo = at.registrar_passo(
        acao="Escalar três pessoas para o acompanhamento do marco",
        necessidade="o marco precisa de acompanhamento semanal",
        resultado_esperado="o marco é acompanhado sem depender de uma pessoa",
        em=AGORA,
    )
    at.mudar_status(passo.id, StatusDoPasso.EM_EXECUCAO, em=AGORA)
    at.drenar_eventos()

    vinculos = (
        promocao.referencia,
        semeadura.referencia,
        derivacao.referencia,
        derivacao_at.referencia,
    )
    return CadeiaSintetica(ara=ara, nuvem=nuvem, arf=arf, apr=apr, at=at, vinculos=vinculos)


def montar_snt(dono: DonoDoProjeto = DONO) -> ArvoreSnT:
    """Uma S&T sintética — a ferramenta que exporta pelo documento canônico dela."""
    arvore = nova_arvore_snt(
        id=uuid4(),
        dono=dono,
        nome="Plano da Instituição Horizonte",
        meta_global="Atender o dobro de pessoas com a estrutura atual",
        em=AGORA,
    )
    raiz = arvore.adicionar_passo(
        estrategia="Reduzir o tempo de espera pela metade",
        em=AGORA,
        tatica="Enxergar a fila em tempo real",
    )
    arvore.adicionar_passo(
        pai_id=raiz.id,
        estrategia="Eliminar a espera por conferência",
        em=AGORA,
        tatica="Conferir por amostragem",
    )
    arvore.drenar_eventos()
    return arvore
