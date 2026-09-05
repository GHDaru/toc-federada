"""Governança de execução: qual capability cada caso de uso exige, e quem a cobra.

Siglas, uma vez: **APH** — Aplicação ↔ Harness · **HTTP** — *HyperText Transfer Protocol*
· **ARA** — Árvore da Realidade Atual · **UDE** — Efeito Indesejável.

**O que este módulo é.** O §B.7.2 do Anexo B do Padrão APH manda que a derivação
perfil → capability seja "política pura fora do modelo, em código verificável, e
verificada nos **casos de uso**, não na camada de rota", e registra a armadilha logo em
seguida: auditar autorização olhando `Depends(...)`/middleware na rota, num código que
segue essa regra, "produz falso positivo sistemático — três equipes independentes caíram
nela na primeira rodada de federação, inclusive sobre o próprio código".

Três peças, e nenhuma delas tem `if` sobre origem, papel ou texto de modelo:

1. **`POLITICA`** — tabela `classe de caso de uso → capability exigida`. É dado, lido por
   teste. Não existe caminho em que um campo do pedido entre na conta (P2, item 3).
2. **`exigir_capacidade`** — a única função DESTE núcleo (M1 e M2) que decide acesso.
   Ela não decide sozinha: delega à `PoliticaDeAutorizacao` de `aplicacao.politica`, que
   é a mesma que a superfície federada usa. É isso que faz a sabotagem da RF-20 (trocar a
   política por `PoliticaSempreVerdadeira`) derrubar TAMBÉM os testes de recusa daqui —
   uma política, um contraexemplo, dois lados medidos.
3. **`Executor`** — o único caminho por onde um caso de uso do núcleo roda a pedido de
   alguém. Ele **constrói** o caso de uso com as portas que recebeu, e por isso a
   verificação não é contornável: quem o recebe (o roteador HTTP hoje, o fio
   conversacional amanhã) nunca recebe o repositório nem o relógio, e não tem com o que
   montar um caso de uso por fora.

**Fail-closed é literal** (RNF-04 da spec 004): caso de uso ausente da tabela é NEGADO,
não liberado. A ausência de regra é a situação em que um sistema costuma abrir a porta por
omissão, e é a que `PoliticaAusente` fecha.

Camada pura: zero import de FastAPI, Pydantic, SQLAlchemy, httpx ou OpenTelemetry.
"""
from __future__ import annotations

import inspect
from dataclasses import dataclass, field
from typing import Any

from ..dominio.erros import ErroDeDominio
from ..dominio.federacao.principal import Principal
from ..dominio.portas import Rastreador, Relogio
from .ara import (
    AbrirProjetoARA,
    AnalisarArvore,
    CriarProjetoARA,
    DesfazerConectorE,
    DesmarcarUde,
    EditarFichaDeUde,
    ExaminarElo,
    FormarConectorE,
    MarcarUde,
    MudarStatusDeUde,
    RegistrarParecer,
    ReformularUde,
    ValidarTextoDeUde,
)
from .casos_de_uso import CasoDeUso
from .nuvem import (
    AbrirProjetoNC,
    AplicarGeracaoDeNuvem,
    ArquivarPremissa,
    ClassificarInjecao,
    CriarProjetoNC,
    DerivarNuvemDeUdes,
    DesafiarPremissa,
    EditarEntidadeDaNuvem,
    EditarInjecao,
    EditarPremissa,
    EditarRacionalDaNuvem,
    GerarNuvemPorNarrativa,
    MudarStatusDeInjecao,
    RegistrarInjecao,
    RegistrarPremissa,
    ReordenarPremissas,
    RevigorarPremissa,
    SugerirInjecoes,
    SugerirPremissas,
    ValidarNuvem,
)
from .grafo import (
    AdicionarNo,
    EditarAresta,
    EditarNo,
    ExcluirAresta,
    ExcluirNo,
    LigarNos,
    MoverNo,
    RecolherNo,
)
from .politica import PoliticaDeAutorizacao, PoliticaPorCapability
from .projetos import (
    AbrirProjeto,
    CriarProjeto,
    ExcluirProjeto,
    ListarLixeira,
    ListarProjetos,
    RestaurarProjeto,
)

#: O vocabulário desta aplicação, na forma `recurso:verbo` do §B.7.1 — sem curinga, que
#: "transforma concessão em cheque em branco". São os dois nomes que o guia do hospedeiro
#: usa como exemplo do que uma aplicação federada declara
#: (`ghdaru/docs/integration/guia-desenvolvedor-app-federada.md`, leitura apenas).
TOC_LEITURA = "toc:read"
TOC_ESCRITA = "toc:write"


class AutorizacaoNegada(ErroDeDominio):
    """A política recusou. Fail-closed (RNF-04).

    Carrega `capability` e `operacao` porque a borda precisa dizer O QUE faltou sem
    reconstruir a frase por texto — o cliente discrimina por código e por dado, nunca por
    mensagem (Anexo A §A.7).
    """

    def __init__(self, capability: str, operacao: str) -> None:
        super().__init__(f"{operacao}: exige a capability {capability}")
        self.capability = capability
        self.operacao = operacao


class PoliticaAusente(ErroDeDominio):
    """Caso de uso sem entrada na `POLITICA`. **Nega** — nunca libera.

    Não é `AutorizacaoNegada` porque a causa é outra e a diferença importa para quem
    depura: ali faltou capability ao principal, aqui falta regra ao sistema. As duas
    terminam em recusa; só uma é defeito nosso, e o teste de cobertura da política impede
    que ele chegue a produção.
    """

    def __init__(self, classe: type) -> None:
        super().__init__(
            f"{classe.__name__} não está na política de capabilities — negado por "
            f"omissão (fail-closed). Registre-o em toc_api.aplicacao.governanca.POLITICA."
        )
        self.classe = classe


#: `classe → capability`. Tabela, não código: quem lê sabe o que cada operação exige sem
#: seguir ramo nenhum. **Ler é operação governada** e exige `toc:read` — não existe
#: operação "pública" nesta aplicação.
POLITICA: dict[type[CasoDeUso], str] = {
    # M1 — projetos
    AbrirProjeto: TOC_LEITURA,
    ListarProjetos: TOC_LEITURA,
    ListarLixeira: TOC_LEITURA,
    CriarProjeto: TOC_ESCRITA,
    ExcluirProjeto: TOC_ESCRITA,
    RestaurarProjeto: TOC_ESCRITA,
    # M1 — nós e arestas
    AdicionarNo: TOC_ESCRITA,
    EditarNo: TOC_ESCRITA,
    MoverNo: TOC_ESCRITA,
    RecolherNo: TOC_ESCRITA,
    ExcluirNo: TOC_ESCRITA,
    LigarNos: TOC_ESCRITA,
    EditarAresta: TOC_ESCRITA,
    ExcluirAresta: TOC_ESCRITA,
    # M2 — ARA
    AbrirProjetoARA: TOC_LEITURA,
    # Validar o texto de um UDE é função pura e NÃO grava nada: é a única operação da ARA
    # que um principal só-leitura alcança.
    ValidarTextoDeUde: TOC_LEITURA,
    CriarProjetoARA: TOC_ESCRITA,
    MarcarUde: TOC_ESCRITA,
    DesmarcarUde: TOC_ESCRITA,
    EditarFichaDeUde: TOC_ESCRITA,
    ReformularUde: TOC_ESCRITA,
    RegistrarParecer: TOC_ESCRITA,
    MudarStatusDeUde: TOC_ESCRITA,
    ExaminarElo: TOC_ESCRITA,
    FormarConectorE: TOC_ESCRITA,
    DesfazerConectorE: TOC_ESCRITA,
    # `AnalisarArvore` não muta o grafo, mas ACRESCENTA `AnaliseEstruturalGerada` à
    # memória do projeto (RF-31 da spec 005) e por isso grava. Operação que grava exige
    # `toc:write`; chamá-la de leitura porque "só lê o grafo" seria a exceção por onde a
    # regra vaza.
    AnalisarArvore: TOC_ESCRITA,
    # M3 — Nuvem de Conflito (spec 007)
    AbrirProjetoNC: TOC_LEITURA,
    # `ValidarNuvem` é função pura sobre o agregado já gravado: completude, avisos de
    # formulação e pendências. Não grava nada — é a irmã de `ValidarTextoDeUde` no M3.
    ValidarNuvem: TOC_LEITURA,
    CriarProjetoNC: TOC_ESCRITA,
    DerivarNuvemDeUdes: TOC_ESCRITA,
    EditarEntidadeDaNuvem: TOC_ESCRITA,
    EditarRacionalDaNuvem: TOC_ESCRITA,
    RegistrarPremissa: TOC_ESCRITA,
    EditarPremissa: TOC_ESCRITA,
    ReordenarPremissas: TOC_ESCRITA,
    DesafiarPremissa: TOC_ESCRITA,
    RevigorarPremissa: TOC_ESCRITA,
    ArquivarPremissa: TOC_ESCRITA,
    RegistrarInjecao: TOC_ESCRITA,
    EditarInjecao: TOC_ESCRITA,
    ClassificarInjecao: TOC_ESCRITA,
    MudarStatusDeInjecao: TOC_ESCRITA,
    # A assistência do M3 não grava no agregado (gerar e sugerir devolvem rascunho), e
    # ainda assim exige `toc:write`: ela **consome a fundação em nome do inquilino** e só
    # existe para desembocar em proposta mutadora. Classificá-la como leitura daria a um
    # principal só-leitura o poder de acionar o catálogo assistido — que é justamente o
    # que a RF-27 manda esconder de quem não escreve.
    GerarNuvemPorNarrativa: TOC_ESCRITA,
    SugerirPremissas: TOC_ESCRITA,
    SugerirInjecoes: TOC_ESCRITA,
    AplicarGeracaoDeNuvem: TOC_ESCRITA,
}


def capacidade_de(classe: type[CasoDeUso]) -> str:
    try:
        return POLITICA[classe]
    except KeyError:
        raise PoliticaAusente(classe) from None


def exigir_capacidade(
    politica: PoliticaDeAutorizacao, principal: Principal, classe: type[CasoDeUso]
) -> None:
    """A ÚNICA chamada do núcleo M1/M2 que decide acesso. Não deve haver uma segunda.

    `tests/aplicacao/test_governanca_de_capacidades.py` conta as chamadas por árvore
    sintática: uma aqui, ZERO na camada HTTP. Um segundo ponto de decisão é um segundo
    lugar para esquecer de decidir.
    """
    capability = capacidade_de(classe)
    if not politica.permite(principal, capability):
        raise AutorizacaoNegada(capability, classe.nome)


@dataclass(frozen=True)
class Executor:
    """Verifica a capability, monta o caso de uso e o roda. Um caminho só.

    O `dono` NUNCA vem do pedido: vem de `Principal.dono()`, que só existe depois da
    introspecção (P2, RNF-03). `Executor.rodar` não tem parâmetro `dono` — e um teste
    confere a assinatura.
    """

    principal: Principal
    rastreador: Rastreador
    repositorio: Any
    relogio: Relogio
    politica: PoliticaDeAutorizacao = field(default_factory=PoliticaPorCapability)
    #: A porta da assistência do M3 (`MotorDeGeracaoDeNuvem`), quando o serviço a compõe.
    #: É `None` por padrão e injetada **só** nos casos de uso cujo construtor a pede — a
    #: mesma regra de `repositorio` e `relogio`. Um caso de uso que a peça e não a receba
    #: falha alto (`_exigir_motor`), nunca inventa resultado.
    motor: Any | None = None

    def rodar(self, classe: type[CasoDeUso], /, **argumentos: Any) -> Any:
        exigir_capacidade(self.politica, self.principal, classe)
        return self._montar(classe).rodar(dono=self.principal.dono(), **argumentos)

    def _montar(self, classe: type[CasoDeUso]) -> CasoDeUso:
        """Injeta só o que o construtor do caso de uso pede.

        `ValidarTextoDeUde` não tem repositório nem relógio — é função pura de domínio com
        um span em volta —, enquanto os demais têm os três. Ler a assinatura evita uma
        segunda tabela de "quem precisa de quê", que envelheceria em silêncio.
        """
        disponiveis = {
            "rastreador": self.rastreador,
            "repositorio": self.repositorio,
            "relogio": self.relogio,
            "motor": self.motor,
        }
        pedidos = inspect.signature(classe.__init__).parameters
        return classe(**{k: v for k, v in disponiveis.items() if k in pedidos})


__all__ = [
    "POLITICA",
    "TOC_ESCRITA",
    "TOC_LEITURA",
    "AutorizacaoNegada",
    "Executor",
    "PoliticaAusente",
    "capacidade_de",
    "exigir_capacidade",
]
