"""A superfície HTTP das três árvores do M4 — `/toc/arf`, `/toc/apr` e `/toc/at`.

Siglas, uma vez neste arquivo: **M4** — Árvores de Futuro e Implementação · **ARF** —
Árvore da Realidade Futura · **APR** — Árvore de Pré-Requisitos · **AT** — Árvore de
Transição · **UDE** — Efeito Indesejável · **OI** — Objetivo Intermediário · **HTTP** —
*HyperText Transfer Protocol* · **RF/RN** — requisito funcional / regra de negócio.

Quatro decisões desta borda, cada uma com motivo:

1. **Três prefixos, três roteadores.** ARF, APR e AT são ferramentas distintas com lógicas
   distintas (suficiência × necessidade × precedência), e um prefixo comum convidaria a
   rota compartilhada — que é exatamente onde as duas lógicas se misturariam (RN-05).
2. **O papel entra no corpo e é convertido AQUI.** Nome errado vira `422` na borda, com a
   lista do que era esperado — nunca `KeyError` lá dentro.
3. **O autor de um julgamento e de um ramo aceito vem do PRINCIPAL**, nunca do corpo do
   pedido. É a mesma regra do parecer do M2 (RF-16 de lá), e ela existe porque na 4ª
   geração da linhagem "quem validou" era texto que alguém mandava.
4. **Não existe rota assistida de ramo negativo** (RF-10). A ausência é a decisão do round
   008, e o teste de contrato a mede no OpenAPI publicado — prova negativa, não prosa.
"""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Response, status

from ...aplicacao.arvores import (
    AbrirProjetoAPR,
    AbrirProjetoARF,
    AbrirProjetoAT,
    AceitarRamoNegativo,
    AdicionarNoDaAPR,
    AdicionarNoDaARF,
    AvaliarVerbalizacao,
    CriarProjetoAPR,
    CriarProjetoARF,
    CriarProjetoAT,
    DeclararDependencia,
    DesfazerConectorEDaARF,
    DesfazerElipse,
    DesfazerEspelho,
    DesfazerPar,
    EditarFichaDoPasso,
    EditarNoDaAPR,
    EditarNoDaARF,
    EspelharUde,
    ExaminarEloDaARF,
    ExcluirArestaDaARF,
    ExcluirDependencia,
    ExcluirNoDaAPR,
    ExcluirNoDaARF,
    ExcluirPasso,
    ExcluirPrecedencia,
    FormarConectorEDaARF,
    FormarElipse,
    JulgarTesteDeValidade,
    LigarNaARF,
    MarcarRamoNegativo,
    MoverNoDaAPR,
    MoverNoDaARF,
    MudarPapelNaAPR,
    MudarPapelNaARF,
    MudarStatusDoPasso,
    ParearObstaculo,
    PrecederPasso,
    ReabrirRamoNegativo,
    RegistrarPasso,
    ResumoDaAPR,
    SequenciarAPR,
    TratarRamoNegativo,
    VerificarARF,
)
from ...dominio.apr import PapelNaAPR
from ...dominio.arf import EstadoDoRamo, PapelNaARF
from ...dominio.at import StatusDoPasso
from ...dominio.erros import DadoInvalido
from ...dominio.suficiencia import EstadoDoExame
from ..dependencias import ExecutorDependente
from ..esquemas import (
    AprOut,
    ArfOut,
    AtOut,
    ConectorDeSuficienciaIn,
    CriarAprIn,
    CriarArfIn,
    CriarAtIn,
    CriarNoDaArvoreIn,
    DependenciaIn,
    DependenciaOut,
    EditarNoDaArvoreIn,
    EditarPassoIn,
    ElipseIn,
    ElipseOut,
    EloDaArfOut,
    EspelhoOut,
    EspelharIn,
    ExameIn,
    JulgamentoIn,
    LigarIn,
    LinhaDoResumoOut,
    MarcarRamoIn,
    MudarPapelIn,
    MudarRamoIn,
    NoDaArvoreOut,
    ParOut,
    ParearIn,
    PassoOut,
    PrecedenciaIn,
    PrecedenciaOut,
    RamoNegativoOut,
    RegistrarPassoIn,
    ResumoDaAprOut,
    SequenciamentoOut,
    StatusDoPassoIn,
    VerbalizacaoOut,
    VerificacaoDaArfOut,
)

arf = APIRouter(prefix="/toc/arf", tags=["arvore-da-realidade-futura"])
apr = APIRouter(prefix="/toc/apr", tags=["arvore-de-pre-requisitos"])
at = APIRouter(prefix="/toc/at", tags=["arvore-de-transicao"])


def _valor(bruto: str, enumeracao, campo: str):
    """Converte texto em enum de domínio — e recusa na BORDA, com a lista do esperado."""
    try:
        return enumeracao(bruto)
    except ValueError as erro:
        raise DadoInvalido(
            f"{campo} desconhecido: {bruto!r}; esperado um de "
            f"{[e.value for e in enumeracao]}"
        ) from erro


# =======================================================================================
# E4.1 · Árvore da Realidade Futura
# =======================================================================================


@arf.post("/projetos", status_code=status.HTTP_201_CREATED, response_model=ArfOut)
def criar_arf(corpo: CriarArfIn, executor: ExecutorDependente) -> ArfOut:
    """RF-01: a ARF do zero. Sem cadeia vinculada não há espelho de UDE (RF-07)."""
    projeto = executor.rodar(
        CriarProjetoARF,
        nome=corpo.nome,
        descricao_do_problema=corpo.descricao_do_problema,
    )
    return ArfOut.de(executor.rodar(AbrirProjetoARF, projeto_id=projeto.id))


@arf.get("/projetos/{projeto_id}", response_model=ArfOut)
def abrir_arf(projeto_id: UUID, executor: ExecutorDependente) -> ArfOut:
    return ArfOut.de(executor.rodar(AbrirProjetoARF, projeto_id=projeto_id))


@arf.post(
    "/projetos/{projeto_id}/nos",
    status_code=status.HTTP_201_CREATED,
    response_model=NoDaArvoreOut,
)
def adicionar_no_da_arf(
    projeto_id: UUID, corpo: CriarNoDaArvoreIn, executor: ExecutorDependente
) -> NoDaArvoreOut:
    papel = _valor(corpo.papel, PapelNaARF, "papel")
    no = executor.rodar(
        AdicionarNoDaARF,
        projeto_id=projeto_id,
        papel=papel,
        titulo=corpo.titulo,
        descricao=corpo.descricao,
        posicao=corpo.posicao.para_dominio() if corpo.posicao else None,
    )
    return NoDaArvoreOut.de(no, papel.value)


@arf.patch("/projetos/{projeto_id}/nos/{no_id}", response_model=NoDaArvoreOut)
def editar_no_da_arf(
    projeto_id: UUID, no_id: UUID, corpo: EditarNoDaArvoreIn, executor: ExecutorDependente
) -> NoDaArvoreOut:
    no = executor.rodar(
        EditarNoDaARF,
        projeto_id=projeto_id,
        no_id=no_id,
        titulo=corpo.titulo,
        descricao=corpo.descricao,
    )
    arvore = executor.rodar(AbrirProjetoARF, projeto_id=projeto_id)
    return NoDaArvoreOut.de(no, arvore.papel_do_no(no_id).value)


@arf.put("/projetos/{projeto_id}/nos/{no_id}/papel", response_model=NoDaArvoreOut)
def mudar_papel_na_arf(
    projeto_id: UUID, no_id: UUID, corpo: MudarPapelIn, executor: ExecutorDependente
) -> NoDaArvoreOut:
    """RF-02: o papel muda enquanto não houver vínculo que o proíba."""
    papel = _valor(corpo.papel, PapelNaARF, "papel")
    no = executor.rodar(MudarPapelNaARF, projeto_id=projeto_id, no_id=no_id, papel=papel)
    return NoDaArvoreOut.de(no, papel.value)


@arf.delete("/projetos/{projeto_id}/nos/{no_id}", status_code=status.HTTP_204_NO_CONTENT)
def excluir_no_da_arf(
    projeto_id: UUID, no_id: UUID, executor: ExecutorDependente
) -> Response:
    executor.rodar(ExcluirNoDaARF, projeto_id=projeto_id, no_id=no_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@arf.post(
    "/projetos/{projeto_id}/arestas",
    status_code=status.HTTP_201_CREATED,
    response_model=EloDaArfOut,
)
def ligar_na_arf(
    projeto_id: UUID, corpo: LigarIn, executor: ExecutorDependente
) -> EloDaArfOut:
    """RF-03: aresta de suficiência — "Se origem, então destino" —, com exame de nascença."""
    executor.rodar(
        LigarNaARF,
        projeto_id=projeto_id,
        origem_id=corpo.origem_id,
        destino_id=corpo.destino_id,
        rotulo=corpo.rotulo,
    )
    arvore = ArfOut.de(executor.rodar(AbrirProjetoARF, projeto_id=projeto_id))
    return next(
        e for e in arvore.elos
        if e.origem_id == corpo.origem_id and e.destino_id == corpo.destino_id
    )


@arf.delete(
    "/projetos/{projeto_id}/arestas/{aresta_id}", status_code=status.HTTP_204_NO_CONTENT
)
def excluir_aresta_da_arf(
    projeto_id: UUID, aresta_id: UUID, executor: ExecutorDependente
) -> Response:
    executor.rodar(ExcluirArestaDaARF, projeto_id=projeto_id, aresta_id=aresta_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@arf.put("/projetos/{projeto_id}/arestas/{aresta_id}/exame", response_model=EloDaArfOut)
def examinar_elo_da_arf(
    projeto_id: UUID, aresta_id: UUID, corpo: ExameIn, executor: ExecutorDependente
) -> EloDaArfOut:
    executor.rodar(
        ExaminarEloDaARF,
        projeto_id=projeto_id,
        aresta_id=aresta_id,
        estado=_valor(corpo.estado, EstadoDoExame, "estado do exame"),
        reserva=corpo.reserva,
    )
    arvore = ArfOut.de(executor.rodar(AbrirProjetoARF, projeto_id=projeto_id))
    return next(e for e in arvore.elos if e.id == aresta_id)


@arf.post(
    "/projetos/{projeto_id}/conectores",
    status_code=status.HTTP_201_CREATED,
    response_model=ArfOut,
)
def formar_conector_da_arf(
    projeto_id: UUID, corpo: ConectorDeSuficienciaIn, executor: ExecutorDependente
) -> ArfOut:
    executor.rodar(FormarConectorEDaARF, projeto_id=projeto_id, arestas=corpo.arestas)
    return ArfOut.de(executor.rodar(AbrirProjetoARF, projeto_id=projeto_id))


@arf.delete(
    "/projetos/{projeto_id}/conectores/{conector_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def desfazer_conector_da_arf(
    projeto_id: UUID, conector_id: UUID, executor: ExecutorDependente
) -> Response:
    executor.rodar(DesfazerConectorEDaARF, projeto_id=projeto_id, conector_id=conector_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@arf.post(
    "/projetos/{projeto_id}/espelhos",
    status_code=status.HTTP_201_CREATED,
    response_model=EspelhoOut,
)
def espelhar_ude(
    projeto_id: UUID, corpo: EspelharIn, executor: ExecutorDependente
) -> EspelhoOut:
    """RF-04: o efeito futuro passa a ser o Efeito Desejável de um UDE da cadeia."""
    espelho = executor.rodar(
        EspelharUde,
        projeto_id=projeto_id,
        no_id=corpo.no_id,
        ude_id=corpo.ude_id,
        projeto_de_origem_id=corpo.projeto_de_origem_id,
    )
    return EspelhoOut(
        no_id=corpo.no_id,
        ude_id=espelho.ude_id,
        projeto_de_origem_id=espelho.projeto_de_origem_id,
    )


@arf.delete(
    "/projetos/{projeto_id}/espelhos/{no_id}", status_code=status.HTTP_204_NO_CONTENT
)
def desfazer_espelho(
    projeto_id: UUID, no_id: UUID, executor: ExecutorDependente
) -> Response:
    executor.rodar(DesfazerEspelho, projeto_id=projeto_id, no_id=no_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@arf.post(
    "/projetos/{projeto_id}/ramos",
    status_code=status.HTTP_201_CREATED,
    response_model=RamoNegativoOut,
)
def marcar_ramo_negativo(
    projeto_id: UUID, corpo: MarcarRamoIn, executor: ExecutorDependente
) -> RamoNegativoOut:
    """RF-08: o efeito colateral da injeção vira dado — marcação MANUAL (RF-10)."""
    ramo = executor.rodar(MarcarRamoNegativo, projeto_id=projeto_id, no_id=corpo.no_id)
    return RamoNegativoOut.de(ramo)


@arf.put("/projetos/{projeto_id}/ramos/{ramo_id}", response_model=RamoNegativoOut)
def mudar_ramo_negativo(
    projeto_id: UUID, ramo_id: UUID, corpo: MudarRamoIn, executor: ExecutorDependente
) -> RamoNegativoOut:
    """RN-04: `tratado` exige a injeção de corte; `aceito` exige justificativa.

    O **autor** do aceite vem do principal, nunca do corpo do pedido: quem aceitou um
    efeito colateral é quem estava autenticado, e não quem alguém disser.
    """
    estado = _valor(corpo.estado, EstadoDoRamo, "estado do ramo")
    if estado is EstadoDoRamo.TRATADO:
        if corpo.injecao_de_corte_id is None:
            raise DadoInvalido(
                "tratar um ramo negativo exige `injecao_de_corte_id` — a injeção que o "
                "corta (RN-04)"
            )
        ramo = executor.rodar(
            TratarRamoNegativo,
            projeto_id=projeto_id,
            ramo_id=ramo_id,
            injecao_id=corpo.injecao_de_corte_id,
        )
    elif estado is EstadoDoRamo.ACEITO:
        ramo = executor.rodar(
            AceitarRamoNegativo,
            projeto_id=projeto_id,
            ramo_id=ramo_id,
            justificativa=corpo.justificativa,
            autor=executor.principal.dono().usuario_id,
        )
    else:
        ramo = executor.rodar(ReabrirRamoNegativo, projeto_id=projeto_id, ramo_id=ramo_id)
    return RamoNegativoOut.de(ramo)


@arf.post("/projetos/{projeto_id}/verificacoes", response_model=VerificacaoDaArfOut)
def verificar_arf(projeto_id: UUID, executor: ExecutorDependente) -> VerificacaoDaArfOut:
    """RF-11/RF-13: função pura + evento com o resumo — por isso é `POST`, e não `GET`."""
    return VerificacaoDaArfOut.de(executor.rodar(VerificarARF, projeto_id=projeto_id))


# =======================================================================================
# E4.2 · Árvore de Pré-Requisitos
# =======================================================================================


@apr.post("/projetos", status_code=status.HTTP_201_CREATED, response_model=AprOut)
def criar_apr(corpo: CriarAprIn, executor: ExecutorDependente) -> AprOut:
    """RF-14: a APR nasce COM o objetivo — não existe APR sem o topo dela."""
    projeto = executor.rodar(
        CriarProjetoAPR,
        nome=corpo.nome,
        objetivo=corpo.objetivo,
        descricao_do_problema=corpo.descricao_do_problema,
    )
    return AprOut.de(executor.rodar(AbrirProjetoAPR, projeto_id=projeto.id))


@apr.get("/projetos/{projeto_id}", response_model=AprOut)
def abrir_apr(projeto_id: UUID, executor: ExecutorDependente) -> AprOut:
    return AprOut.de(executor.rodar(AbrirProjetoAPR, projeto_id=projeto_id))


@apr.post(
    "/projetos/{projeto_id}/nos",
    status_code=status.HTTP_201_CREATED,
    response_model=NoDaArvoreOut,
)
def adicionar_no_da_apr(
    projeto_id: UUID, corpo: CriarNoDaArvoreIn, executor: ExecutorDependente
) -> NoDaArvoreOut:
    """RN-08: o obstáculo mal verbalizado É registrado — o aviso vem por outra rota."""
    papel = _valor(corpo.papel, PapelNaAPR, "papel")
    no = executor.rodar(
        AdicionarNoDaAPR,
        projeto_id=projeto_id,
        papel=papel,
        titulo=corpo.titulo,
        descricao=corpo.descricao,
        posicao=corpo.posicao.para_dominio() if corpo.posicao else None,
    )
    return NoDaArvoreOut.de(no, papel.value)


@apr.patch("/projetos/{projeto_id}/nos/{no_id}", response_model=NoDaArvoreOut)
def editar_no_da_apr(
    projeto_id: UUID, no_id: UUID, corpo: EditarNoDaArvoreIn, executor: ExecutorDependente
) -> NoDaArvoreOut:
    no = executor.rodar(
        EditarNoDaAPR,
        projeto_id=projeto_id,
        no_id=no_id,
        titulo=corpo.titulo,
        descricao=corpo.descricao,
    )
    arvore = executor.rodar(AbrirProjetoAPR, projeto_id=projeto_id)
    return NoDaArvoreOut.de(no, arvore.papel_do_no(no_id).value)


@apr.put("/projetos/{projeto_id}/nos/{no_id}/papel", response_model=NoDaArvoreOut)
def mudar_papel_na_apr(
    projeto_id: UUID, no_id: UUID, corpo: MudarPapelIn, executor: ExecutorDependente
) -> NoDaArvoreOut:
    papel = _valor(corpo.papel, PapelNaAPR, "papel")
    no = executor.rodar(MudarPapelNaAPR, projeto_id=projeto_id, no_id=no_id, papel=papel)
    return NoDaArvoreOut.de(no, papel.value)


@apr.delete("/projetos/{projeto_id}/nos/{no_id}", status_code=status.HTTP_204_NO_CONTENT)
def excluir_no_da_apr(
    projeto_id: UUID, no_id: UUID, executor: ExecutorDependente
) -> Response:
    """O objetivo é indestrutível (RF-14): a recusa vem do domínio, com regra nomeada."""
    executor.rodar(ExcluirNoDaAPR, projeto_id=projeto_id, no_id=no_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@apr.get(
    "/projetos/{projeto_id}/nos/{no_id}/verbalizacao", response_model=VerbalizacaoOut
)
def avaliar_verbalizacao(
    projeto_id: UUID, no_id: UUID, executor: ExecutorDependente, idioma: str = "pt"
) -> VerbalizacaoOut:
    """RF-20: leitura pura — e por isso alcançável por quem só tem `toc:read`."""
    return VerbalizacaoOut.de(
        executor.rodar(
            AvaliarVerbalizacao, projeto_id=projeto_id, no_id=no_id, idioma=idioma
        )
    )


@apr.post(
    "/projetos/{projeto_id}/dependencias",
    status_code=status.HTTP_201_CREATED,
    response_model=DependenciaOut,
)
def declarar_dependencia(
    projeto_id: UUID, corpo: DependenciaIn, executor: ExecutorDependente
) -> DependenciaOut:
    """RF-16: "A precisa existir antes de B" — e NÃO há exame de elo neste projeto."""
    aresta = executor.rodar(
        DeclararDependencia,
        projeto_id=projeto_id,
        antes_id=corpo.antes_id,
        depois_id=corpo.depois_id,
    )
    arvore = executor.rodar(AbrirProjetoAPR, projeto_id=projeto_id)
    return DependenciaOut(
        id=aresta.id,
        antes_id=aresta.origem_id,
        depois_id=aresta.destino_id,
        leitura=arvore.leitura_da_dependencia(aresta.id),
    )


@apr.delete(
    "/projetos/{projeto_id}/dependencias/{aresta_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def excluir_dependencia(
    projeto_id: UUID, aresta_id: UUID, executor: ExecutorDependente
) -> Response:
    executor.rodar(ExcluirDependencia, projeto_id=projeto_id, aresta_id=aresta_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@apr.post(
    "/projetos/{projeto_id}/pares",
    status_code=status.HTTP_201_CREATED,
    response_model=ParOut,
)
def parear_obstaculo(
    projeto_id: UUID, corpo: ParearIn, executor: ExecutorDependente
) -> ParOut:
    par = executor.rodar(
        ParearObstaculo,
        projeto_id=projeto_id,
        obstaculo_id=corpo.obstaculo_id,
        oi_id=corpo.objetivo_intermediario_id,
    )
    return ParOut.de(executor.rodar(AbrirProjetoAPR, projeto_id=projeto_id), par)


@apr.delete(
    "/projetos/{projeto_id}/pares/{par_id}", status_code=status.HTTP_204_NO_CONTENT
)
def desfazer_par(projeto_id: UUID, par_id: UUID, executor: ExecutorDependente) -> Response:
    executor.rodar(DesfazerPar, projeto_id=projeto_id, par_id=par_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@apr.post(
    "/projetos/{projeto_id}/pares/{par_id}/julgamentos",
    status_code=status.HTTP_201_CREATED,
    response_model=ParOut,
)
def julgar_teste_de_validade(
    projeto_id: UUID, par_id: UUID, corpo: JulgamentoIn, executor: ExecutorDependente
) -> ParOut:
    """RN-07: o autor é o principal; o julgamento acumula e nunca sobrescreve."""
    par = executor.rodar(
        JulgarTesteDeValidade,
        projeto_id=projeto_id,
        par_id=par_id,
        autor=executor.principal.dono().usuario_id,
        valido=corpo.valido,
        justificativa=corpo.justificativa,
    )
    return ParOut.de(executor.rodar(AbrirProjetoAPR, projeto_id=projeto_id), par)


@apr.post(
    "/projetos/{projeto_id}/elipses",
    status_code=status.HTTP_201_CREATED,
    response_model=ElipseOut,
)
def formar_elipse(
    projeto_id: UUID, corpo: ElipseIn, executor: ExecutorDependente
) -> ElipseOut:
    """RF-19: "A **e** B precisam existir antes de C" — conjunção de NECESSIDADE."""
    elipse = executor.rodar(
        FormarElipse, projeto_id=projeto_id, dependencias=corpo.dependencias
    )
    arvore = executor.rodar(AbrirProjetoAPR, projeto_id=projeto_id)
    return ElipseOut(
        id=elipse.id,
        destino_id=elipse.destino_id,
        dependencias=list(elipse.dependencias),
        leitura=arvore.leitura_da_elipse(elipse.id),
    )


@apr.delete(
    "/projetos/{projeto_id}/elipses/{elipse_id}", status_code=status.HTTP_204_NO_CONTENT
)
def desfazer_elipse(
    projeto_id: UUID, elipse_id: UUID, executor: ExecutorDependente
) -> Response:
    executor.rodar(DesfazerElipse, projeto_id=projeto_id, elipse_id=elipse_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@apr.post("/projetos/{projeto_id}/sequenciamentos", response_model=SequenciamentoOut)
def sequenciar(projeto_id: UUID, executor: ExecutorDependente) -> SequenciamentoOut:
    """RF-23/RF-26: camadas, ramos paralelos e o ciclo que BLOQUEIA (RN-06)."""
    return SequenciamentoOut.de(executor.rodar(SequenciarAPR, projeto_id=projeto_id))


@apr.get("/projetos/{projeto_id}/resumo", response_model=ResumoDaAprOut)
def resumo_da_apr(projeto_id: UUID, executor: ExecutorDependente) -> ResumoDaAprOut:
    """RF-25: obstáculo · objetivo intermediário · de quem depende, na ordem das camadas."""
    linhas = executor.rodar(ResumoDaAPR, projeto_id=projeto_id)
    return ResumoDaAprOut(
        linhas=[
            LinhaDoResumoOut(
                camada=linha.camada,
                objetivo_intermediario=linha.objetivo_intermediario,
                objetivo_intermediario_id=linha.objetivo_intermediario_id,
                obstaculo=linha.obstaculo,
                obstaculo_id=linha.obstaculo_id,
                depende_de=list(linha.depende_de),
                julgamento=linha.julgamento,
            )
            for linha in linhas
        ]
    )


# =======================================================================================
# E4.3 · Árvore de Transição
# =======================================================================================


@at.post("/projetos", status_code=status.HTTP_201_CREATED, response_model=AtOut)
def criar_at(corpo: CriarAtIn, executor: ExecutorDependente) -> AtOut:
    projeto = executor.rodar(
        CriarProjetoAT, nome=corpo.nome, descricao_do_problema=corpo.descricao_do_problema
    )
    return AtOut.de(executor.rodar(AbrirProjetoAT, projeto_id=projeto.id))


@at.get("/projetos/{projeto_id}", response_model=AtOut)
def abrir_at(projeto_id: UUID, executor: ExecutorDependente) -> AtOut:
    return AtOut.de(executor.rodar(AbrirProjetoAT, projeto_id=projeto_id))


@at.post(
    "/projetos/{projeto_id}/passos",
    status_code=status.HTTP_201_CREATED,
    response_model=PassoOut,
)
def registrar_passo(
    projeto_id: UUID, corpo: RegistrarPassoIn, executor: ExecutorDependente
) -> PassoOut:
    """RN-10: a tripla é obrigatória — a recusa vem do domínio, antes de qualquer nó."""
    no = executor.rodar(
        RegistrarPasso,
        projeto_id=projeto_id,
        acao=corpo.acao,
        necessidade=corpo.necessidade,
        resultado_esperado=corpo.resultado_esperado,
        posicao=corpo.posicao.para_dominio() if corpo.posicao else None,
    )
    arvore = executor.rodar(AbrirProjetoAT, projeto_id=projeto_id)
    return PassoOut.de(no.id, arvore.ficha(no.id))


@at.patch("/projetos/{projeto_id}/passos/{no_id}", response_model=PassoOut)
def editar_passo(
    projeto_id: UUID, no_id: UUID, corpo: EditarPassoIn, executor: ExecutorDependente
) -> PassoOut:
    ficha = executor.rodar(
        EditarFichaDoPasso,
        projeto_id=projeto_id,
        no_id=no_id,
        acao=corpo.acao,
        necessidade=corpo.necessidade,
        resultado_esperado=corpo.resultado_esperado,
    )
    return PassoOut.de(no_id, ficha)


@at.delete(
    "/projetos/{projeto_id}/passos/{no_id}", status_code=status.HTTP_204_NO_CONTENT
)
def excluir_passo(projeto_id: UUID, no_id: UUID, executor: ExecutorDependente) -> Response:
    executor.rodar(ExcluirPasso, projeto_id=projeto_id, no_id=no_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@at.put("/projetos/{projeto_id}/passos/{no_id}/status", response_model=PassoOut)
def mudar_status_do_passo(
    projeto_id: UUID, no_id: UUID, corpo: StatusDoPassoIn, executor: ExecutorDependente
) -> PassoOut:
    """RF-30: bloquear exige motivo, concluir exige o real — e o esperado NÃO é apagado."""
    ficha = executor.rodar(
        MudarStatusDoPasso,
        projeto_id=projeto_id,
        no_id=no_id,
        status=_valor(corpo.status, StatusDoPasso, "status do passo"),
        motivo=corpo.motivo,
        resultado_real=corpo.resultado_real,
    )
    return PassoOut.de(no_id, ficha)


@at.post(
    "/projetos/{projeto_id}/precedencias",
    status_code=status.HTTP_201_CREATED,
    response_model=PrecedenciaOut,
)
def preceder_passo(
    projeto_id: UUID, corpo: PrecedenciaIn, executor: ExecutorDependente
) -> PrecedenciaOut:
    aresta = executor.rodar(
        PrecederPasso,
        projeto_id=projeto_id,
        antes_id=corpo.antes_id,
        depois_id=corpo.depois_id,
    )
    return PrecedenciaOut(
        id=aresta.id, antes_id=aresta.origem_id, depois_id=aresta.destino_id
    )


@at.delete(
    "/projetos/{projeto_id}/precedencias/{aresta_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def excluir_precedencia(
    projeto_id: UUID, aresta_id: UUID, executor: ExecutorDependente
) -> Response:
    executor.rodar(ExcluirPrecedencia, projeto_id=projeto_id, aresta_id=aresta_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
