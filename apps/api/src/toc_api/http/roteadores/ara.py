"""A superfície HTTP da Árvore da Realidade Atual (ARA) — M2, spec 005.

Uma rota por comando do agregado, como no M1. Três decisões desta borda merecem estar
escritas, porque cada uma corrige um defeito nomeado da 4ª geração da linhagem:

1. **`POST /toc/ara/validacoes` não toca projeto nenhum.** Validar a formulação de um
   Efeito Indesejável (UDE) é função pura de domínio, e por isso é a única operação da ARA
   que um principal com `toc:read` alcança. Na linhagem, a mesma operação era uma chamada
   de rede a um provedor de modelo de linguagem feita **do navegador**, com a chave no
   cliente (`tocbuilderv3/services/geminiService.ts:16`, defeito D-01/D-08).
2. **O autor de um parecer vem do principal, nunca do corpo do pedido** (RF-16). Na
   linhagem, `validado_por` era texto devolvido pelo modelo
   (`tocbuilderv3/types.ts:171-213`): quem validou era quem alguém dissesse. E a origem é
   sempre `HUMANO` nesta superfície — parecer de catálogo nasce `action_proposal` e entra
   por outra porta, no ciclo 006.
3. **O nó da ARA nasce com o tipo `efeito` por decisão do SERVIDOR** (F-15: todo nó é um
   efeito; "causa" é posição na cadeia, não tipo de nó). O cliente não escolhe o tipo, e
   por isso não pode errá-lo.
"""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Response, status

from ...aplicacao.ara import (
    AbrirProjetoARA,
    AdicionarEfeito,
    AnalisarArvore,
    CriarProjetoARA,
    DesfazerConectorE,
    DesmarcarUde,
    EditarArestaDaARA,
    EditarFichaDeUde,
    EditarNoDaARA,
    ExaminarElo,
    ExcluirArestaDaARA,
    ExcluirNoDaARA,
    FormarConectorE,
    LigarNaARA,
    MarcarUde,
    MoverNoDaARA,
    MudarStatusDeUde,
    RecolherNoDaARA,
    ReformularUde,
    RegistrarParecer,
    ValidarTextoDeUde,
)
from ...dominio.ara import (
    EstadoDoExame,
    OrigemDoParecer,
    ParecerDeJulgamento,
)
from ...dominio.erros import DadoInvalido
from ..dependencias import ExecutorDependente
from ..esquemas import (
    AraOut,
    ArestaOut,
    ConectorIn,
    ConectorOut,
    CriarNoIn,
    EditarArestaIn,
    EditarNoIn,
    ExclusaoDeNoOut,
    LigarIn,
    CriarProjetoIn,
    ExameOut,
    ExaminarEloIn,
    FichaIO,
    MarcarUdeIn,
    MudarStatusIn,
    NoOut,
    ParecerIn,
    ProjetoOut,
    ReformularIn,
    RelatorioOut,
    StatusOut,
    ValidacaoOut,
    ValidarTextoIn,
)

roteador = APIRouter(prefix="/toc/ara", tags=["ara"])


@roteador.post("/validacoes", response_model=ValidacaoOut)
def validar_texto(corpo: ValidarTextoIn, executor: ExecutorDependente) -> ValidacaoOut:
    """RF-06: veredito por critério decidível, com o trecho que o motivou. Sem rede."""
    validacao = executor.rodar(
        ValidarTextoDeUde, texto=corpo.texto, idioma=corpo.idioma
    )
    return ValidacaoOut.de(validacao)


@roteador.post("/projetos", status_code=status.HTTP_201_CREATED, response_model=ProjetoOut)
def criar_projeto_ara(corpo: CriarProjetoIn, executor: ExecutorDependente) -> ProjetoOut:
    projeto = executor.rodar(
        CriarProjetoARA,
        nome=corpo.nome,
        descricao_do_problema=corpo.descricao_do_problema,
    )
    return ProjetoOut.de(projeto)


@roteador.get("/projetos/{projeto_id}", response_model=AraOut)
def abrir_ara(projeto_id: UUID, executor: ExecutorDependente) -> AraOut:
    """A leitura inteira: grafo, UDEs com ficha e status, elos com exame, conectores."""
    return AraOut.de(executor.rodar(AbrirProjetoARA, projeto_id=projeto_id))


@roteador.post(
    "/projetos/{projeto_id}/efeitos",
    status_code=status.HTTP_201_CREATED,
    response_model=NoOut,
)
def adicionar_efeito(
    projeto_id: UUID, corpo: CriarNoIn, executor: ExecutorDependente
) -> NoOut:
    """O tipo é `efeito` e vem do servidor (F-15) — o cliente não o escolhe.

    Roda `AdicionarEfeito`, que passa pela raiz `ProjetoARA`. Antes rodava o
    `AdicionarNo` genérico do M1 com o tipo certo no argumento: dava o mesmo nó e não era
    a mesma coisa — era a ferramenta indo ao núcleo por fora da própria raiz, no mesmo
    caminho que as rotas de `/toc/projetos` abriam para qualquer um.
    """
    no = executor.rodar(
        AdicionarEfeito,
        projeto_id=projeto_id,
        titulo=corpo.titulo,
        descricao=corpo.descricao,
        posicao=corpo.posicao.para_dominio() if corpo.posicao else None,
    )
    return NoOut.de(no)


@roteador.patch("/projetos/{projeto_id}/nos/{no_id}", response_model=NoOut)
def editar_no_da_ara(
    projeto_id: UUID, no_id: UUID, corpo: EditarNoIn, executor: ExecutorDependente
) -> NoOut:
    """O espelho do PATCH do M1, pela raiz — e com a revalidação que o M1 não conhece.

    Mudar o TÍTULO de um Efeito Indesejável reexecuta a validação formal aqui dentro
    (RF-10). Pela rota genérica, o veredito anterior ficava pendurado sobre um texto que
    já não era o dele.
    """
    resultado = None
    if corpo.titulo is not None or corpo.descricao is not None:
        resultado = executor.rodar(
            EditarNoDaARA,
            projeto_id=projeto_id,
            no_id=no_id,
            titulo=corpo.titulo,
            descricao=corpo.descricao,
        )
    if corpo.posicao is not None:
        resultado = executor.rodar(
            MoverNoDaARA,
            projeto_id=projeto_id,
            no_id=no_id,
            posicao=corpo.posicao.para_dominio(),
        )
    if corpo.recolhido is not None:
        resultado = executor.rodar(
            RecolherNoDaARA, projeto_id=projeto_id, no_id=no_id, recolhido=corpo.recolhido
        )
    if resultado is None:
        raise DadoInvalido(
            "editar_no: informe ao menos um de titulo, descricao, posicao ou recolhido"
        )
    return NoOut.de(resultado)


@roteador.delete("/projetos/{projeto_id}/nos/{no_id}", response_model=ExclusaoDeNoOut)
def excluir_no_da_ara(
    projeto_id: UUID, no_id: UUID, executor: ExecutorDependente
) -> ExclusaoDeNoOut:
    """Devolve o RAIO (RF-15). Pela raiz, a ficha do Efeito Indesejável é ARQUIVADA."""
    removidas = executor.rodar(ExcluirNoDaARA, projeto_id=projeto_id, no_id=no_id)
    return ExclusaoDeNoOut(no_id=no_id, arestas_removidas=list(removidas))


# -- elos de suficiência ---------------------------------------------------------------


@roteador.post(
    "/projetos/{projeto_id}/arestas",
    status_code=status.HTTP_201_CREATED,
    response_model=ArestaOut,
)
def ligar_na_ara(
    projeto_id: UUID, corpo: LigarIn, executor: ExecutorDependente
) -> ArestaOut:
    """O elo nasce COM exame (`nao_examinado`) — é o que faz a suficiência ser dado."""
    aresta = executor.rodar(
        LigarNaARA,
        projeto_id=projeto_id,
        origem_id=corpo.origem_id,
        destino_id=corpo.destino_id,
        rotulo=corpo.rotulo,
    )
    return ArestaOut.de(aresta)


@roteador.patch("/projetos/{projeto_id}/arestas/{aresta_id}", response_model=ArestaOut)
def editar_aresta_da_ara(
    projeto_id: UUID, aresta_id: UUID, corpo: EditarArestaIn, executor: ExecutorDependente
) -> ArestaOut:
    aresta = executor.rodar(
        EditarArestaDaARA, projeto_id=projeto_id, aresta_id=aresta_id, rotulo=corpo.rotulo
    )
    return ArestaOut.de(aresta)


@roteador.delete(
    "/projetos/{projeto_id}/arestas/{aresta_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def excluir_aresta_da_ara(
    projeto_id: UUID, aresta_id: UUID, executor: ExecutorDependente
) -> Response:
    """Leva junto o exame e a citação do elo em conector E (RN-11)."""
    executor.rodar(ExcluirArestaDaARA, projeto_id=projeto_id, aresta_id=aresta_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# -- UDE: marcador, ficha, reformulação, parecer, status ------------------------------


@roteador.post(
    "/projetos/{projeto_id}/nos/{no_id}/ude",
    status_code=status.HTTP_201_CREATED,
    response_model=FichaIO,
)
def marcar_ude(
    projeto_id: UUID, no_id: UUID, corpo: MarcarUdeIn, executor: ExecutorDependente
) -> FichaIO:
    ficha = executor.rodar(
        MarcarUde,
        projeto_id=projeto_id,
        no_id=no_id,
        ficha=corpo.ficha.para_dominio() if corpo.ficha else None,
    )
    return FichaIO.de(ficha)


@roteador.delete(
    "/projetos/{projeto_id}/nos/{no_id}/ude", status_code=status.HTTP_204_NO_CONTENT
)
def desmarcar_ude(projeto_id: UUID, no_id: UUID, executor: ExecutorDependente) -> Response:
    executor.rodar(DesmarcarUde, projeto_id=projeto_id, no_id=no_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@roteador.put("/projetos/{projeto_id}/nos/{no_id}/ficha", response_model=FichaIO)
def editar_ficha(
    projeto_id: UUID, no_id: UUID, corpo: FichaIO, executor: ExecutorDependente
) -> FichaIO:
    ficha = executor.rodar(
        EditarFichaDeUde, projeto_id=projeto_id, no_id=no_id, ficha=corpo.para_dominio()
    )
    return FichaIO.de(ficha)


@roteador.post("/projetos/{projeto_id}/nos/{no_id}/reformulacoes", response_model=NoOut)
def reformular(
    projeto_id: UUID, no_id: UUID, corpo: ReformularIn, executor: ExecutorDependente
) -> NoOut:
    """RF-10: editar o texto REEXECUTA a validação formal no mesmo comando."""
    no = executor.rodar(
        ReformularUde, projeto_id=projeto_id, no_id=no_id, texto=corpo.texto
    )
    return NoOut.de(no)


@roteador.post(
    "/projetos/{projeto_id}/nos/{no_id}/pareceres",
    status_code=status.HTTP_204_NO_CONTENT,
)
def registrar_parecer(
    projeto_id: UUID, no_id: UUID, corpo: ParecerIn, executor: ExecutorDependente
) -> Response:
    """O autor é o principal e a origem é `humano` — nenhum dos dois vem do cliente."""
    parecer = ParecerDeJulgamento(
        autor=executor.principal.dono().usuario_id,
        origem=OrigemDoParecer.HUMANO,
        favoravel=corpo.favoravel,
        justificativa=corpo.justificativa,
        instante=executor.relogio.agora(),
        criterios=tuple(corpo.criterios),
    )
    executor.rodar(RegistrarParecer, projeto_id=projeto_id, no_id=no_id, parecer=parecer)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@roteador.put("/projetos/{projeto_id}/nos/{no_id}/status", response_model=StatusOut)
def mudar_status(
    projeto_id: UUID, no_id: UUID, corpo: MudarStatusIn, executor: ExecutorDependente
) -> StatusOut:
    """RN-10: `Validado` exige decidíveis verdes E parecer humano favorável."""
    status_novo = executor.rodar(
        MudarStatusDeUde,
        projeto_id=projeto_id,
        no_id=no_id,
        status=corpo.status,
        justificativa=corpo.justificativa,
    )
    return StatusOut(no_id=no_id, status=status_novo.value)


# -- exame de suficiência e conector E ------------------------------------------------


@roteador.put("/projetos/{projeto_id}/arestas/{aresta_id}/exame", response_model=ExameOut)
def examinar_elo(
    projeto_id: UUID, aresta_id: UUID, corpo: ExaminarEloIn, executor: ExecutorDependente
) -> ExameOut:
    """RF-22: `insuficiente` e `com_reserva` exigem a reserva escrita — o domínio cobra."""
    try:
        estado = EstadoDoExame(corpo.estado)
    except ValueError as erro:
        raise DadoInvalido(
            f"estado de exame desconhecido: {corpo.estado!r}; esperado um de "
            f"{[e.value for e in EstadoDoExame]}"
        ) from erro
    exame = executor.rodar(
        ExaminarElo,
        projeto_id=projeto_id,
        aresta_id=aresta_id,
        estado=estado,
        reserva=corpo.reserva,
    )
    return ExameOut.de(aresta_id, exame)


@roteador.post(
    "/projetos/{projeto_id}/conectores",
    status_code=status.HTTP_201_CREATED,
    response_model=ConectorOut,
)
def formar_conector(
    projeto_id: UUID, corpo: ConectorIn, executor: ExecutorDependente
) -> ConectorOut:
    conector = executor.rodar(
        FormarConectorE, projeto_id=projeto_id, arestas=tuple(corpo.arestas)
    )
    return ConectorOut.de(conector)


@roteador.delete(
    "/projetos/{projeto_id}/conectores/{conector_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def desfazer_conector(
    projeto_id: UUID, conector_id: UUID, executor: ExecutorDependente
) -> Response:
    executor.rodar(DesfazerConectorE, projeto_id=projeto_id, conector_id=conector_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# -- análise estrutural ----------------------------------------------------------------


@roteador.post("/projetos/{projeto_id}/analises", response_model=RelatorioOut)
def analisar(projeto_id: UUID, executor: ExecutorDependente) -> RelatorioOut:
    """RF-26..RF-31: fragmentos, entradas, alcance, elos não examinados, ciclos, candidata.

    É `POST` e exige `toc:write` porque **grava**: o evento `AnaliseEstruturalGerada`
    entra na memória do projeto (RF-31). O grafo não muda, mas a história do projeto sim,
    e chamar isso de leitura seria a exceção por onde a regra vaza.
    """
    return RelatorioOut.de(executor.rodar(AnalisarArvore, projeto_id=projeto_id))
