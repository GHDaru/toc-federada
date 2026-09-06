"""As portas do domínio — todo efeito sai por aqui (P3, brief §0.3).

São `typing.Protocol` e não classes-base: o adaptador não herda nada nosso, e o duplo do
teste conforma pela FORMA. É o padrão lido em `ghdaru` —
`apps/api/src/ghdaru_api/documents/ports/storage.py` — trazido para cá, não copiado:
aqui toda leitura carrega o inquilino na assinatura, que é o que faz o isolamento ser um
fato de tipo e não de disciplina.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, ContextManager, Mapping, Protocol, Sequence, runtime_checkable
from uuid import UUID

from .apr import ProjetoAPR
from .ara import ProjetoARA
from .arf import ProjetoARF
from .at import ProjetoAT
from .federacao.principal import Principal
from .focalizacao import AnaliseDeFocalizacao
from .nuvem import NuvemDeConflito
from .projeto import Projeto
from .referencia import ReferenciaCruzada


@runtime_checkable
class Relogio(Protocol):
    """O tempo é efeito. O domínio recebe o instante; quem o lê é o adaptador."""

    def agora(self) -> datetime: ...


@runtime_checkable
class SpanDeTraco(Protocol):
    def atributo(self, chave: str, valor: str | int | float | bool) -> None: ...


@runtime_checkable
class Rastreador(Protocol):
    """Traço como porta: a aplicação não importa OpenTelemetry (P3 e P5 juntos).

    P5 exige span de nascença; P3 proíbe a aplicação de conhecer o SDK. A porta resolve
    os dois: `infra/observabilidade/otel.py` traz o adaptador real e o nulo.
    """

    def span(
        self, nome: str, **atributos: str | int | float | bool
    ) -> ContextManager[SpanDeTraco]: ...


@runtime_checkable
class RepositorioDeProjetos(Protocol):
    """Persistência do agregado Projeto.

    **Nenhuma leitura sem inquilino** (invariante 1 do `data-model.md` do ciclo 003): o
    `inquilino_id` é o primeiro parâmetro posicional de toda consulta, e não tem valor
    padrão. Uma consulta sem ele não compila mentalmente nem roda.
    """

    def salvar(self, projeto: Projeto) -> None: ...

    def obter(self, inquilino_id: str, projeto_id: UUID) -> Projeto | None: ...

    def listar(
        self,
        inquilino_id: str,
        *,
        usuario_id: str | None = None,
        incluir_excluidos: bool = False,
    ) -> list[Projeto]: ...


@runtime_checkable
class RepositorioDeARA(Protocol):
    """Persistência do projeto do tipo Árvore da Realidade Atual (ARA), M2.

    Porta SEPARADA da `RepositorioDeProjetos` de propósito. O M1 não conhece semântica da
    Teoria das Restrições (RN-04 da spec 004), e uma porta única obrigaria a assinatura do
    núcleo a mencionar Efeito Indesejável, ficha e exame de elo — a fronteira que impede a
    sétima cópia de canvas morreria na porta. O adaptador pode implementar as duas; o
    domínio continua com duas.

    A regra do inquilino é a mesma e não tem exceção: primeiro parâmetro posicional, sem
    valor padrão.
    """

    def salvar_ara(self, ara: "ProjetoARA") -> None: ...

    def obter_ara(self, inquilino_id: str, projeto_id: UUID) -> "ProjetoARA | None": ...


@runtime_checkable
class ProvedorDeIdentidade(Protocol):
    """Troca o token da fundação por um `Principal` — ou por nada (P2, Anexo B §B.6).

    Esta aplicação **não tem login**: não há entidade usuário, não há senha e não há
    sessão local. O que existe é esta porta, e do outro lado dela mora a introspecção do
    hospedeiro (`POST /auth/introspect`). O adaptador real é da borda; o domínio só
    conhece a forma.

    **Devolve `None` para todo caso que não seja identidade ativa**, sem distinguir
    "inexistente" de "expirado" de "já consumido". Não é preguiça: o §B.6.5 do Anexo B
    proíbe a distinção, porque ela é "oráculo para quem testa tokens". Uma porta com três
    exceções diferentes por motivo reintroduziria o oráculo do lado de dentro.

    **Como o adaptador real se encaixa aqui.** A troca de verdade é a
    `PortaDeIntrospeccao.trocar_grant` de `dominio/federacao/portas.py`, que devolve o
    mesmo `Principal` e **levanta** `IntrospeccaoInvalida` em vez de devolver `None`. Um
    adaptador desta porta é aquele embrulhado num `try/except` de uma linha. As duas
    formas coexistem de propósito: a de lá é a semântica da federação (o erro tem código
    estável e vai para o traço), a daqui é a que a borda HTTP consome, onde toda recusa
    vira o mesmo `401` sem motivo (§B.6.5).

    Síncrona por decisão declarada: os casos de uso desta aplicação são síncronos, e o
    FastAPI roda handler síncrono em pool de trabalho. Um adaptador real com `httpx`
    usa o cliente síncrono; se algum dia a troca precisar ser assíncrona, muda-se a porta
    e os dois lados, nunca só um.
    """

    def identificar(self, token: str) -> "Principal | None": ...


@runtime_checkable
class RepositorioDeNuvens(Protocol):
    """Persistência do projeto do tipo Nuvem de Conflito (NC), M3.

    Porta SEPARADA da `RepositorioDeARA` pelo mesmo motivo que aquela é separada da do M1
    (spec 004, RN-04): cada ferramenta acrescenta a sua semântica **sobre** o núcleo, e uma
    porta única obrigaria a assinatura a mencionar premissa, injeção e separação TRIZ
    (Teoria da Resolução Inventiva de Problemas) para quem não tem nada com isso. O
    adaptador pode implementar as três; o domínio continua com três.

    A regra do inquilino não tem exceção: primeiro parâmetro posicional, sem valor padrão.
    """

    def salvar_nuvem(self, nuvem: "NuvemDeConflito") -> None: ...

    def obter_nuvem(self, inquilino_id: str, projeto_id: UUID) -> "NuvemDeConflito | None": ...


@runtime_checkable
class RepositorioDaCosturaM2M3(RepositorioDeARA, RepositorioDeNuvens, Protocol):
    """As duas portas juntas — a forma que o encadeamento M2 → M3 exige (INT-05).

    Derivar uma nuvem **lê** uma Árvore da Realidade Atual (ARA) e **grava** uma Nuvem de
    Conflito. Declarar a exigência como um `Protocol` composto é o que impede o caso de uso
    de receber um repositório que só sabe metade do caminho — e é mais honesto do que um
    `Any` com comentário pedindo cuidado.
    """


# ---------------------------------------------------------------------------------------
# M4 · Árvores de Futuro e Implementação (spec 008)
#
# Uma porta por ferramenta, pelo mesmo motivo das três anteriores (RN-04 da spec 004): o
# núcleo não conhece semântica da Teoria das Restrições, e uma porta única obrigaria a
# assinatura do M1 a mencionar ramo negativo, par obstáculo↔objetivo intermediário e ficha
# de passo. O adaptador implementa todas; o domínio continua com uma por ferramenta.
# ---------------------------------------------------------------------------------------


@runtime_checkable
class RepositorioDeARF(Protocol):
    """Persistência do projeto do tipo Árvore da Realidade Futura (ARF), M4 · E4.1."""

    def salvar_arf(self, arf: "ProjetoARF") -> None: ...

    def obter_arf(self, inquilino_id: str, projeto_id: UUID) -> "ProjetoARF | None": ...


@runtime_checkable
class RepositorioDeAPR(Protocol):
    """Persistência do projeto do tipo Árvore de Pré-Requisitos (APR), M4 · E4.2."""

    def salvar_apr(self, apr: "ProjetoAPR") -> None: ...

    def obter_apr(self, inquilino_id: str, projeto_id: UUID) -> "ProjetoAPR | None": ...


@runtime_checkable
class RepositorioDeAT(Protocol):
    """Persistência do projeto do tipo Árvore de Transição (AT), M4 · E4.3."""

    def salvar_at(self, at: "ProjetoAT") -> None: ...

    def obter_at(self, inquilino_id: str, projeto_id: UUID) -> "ProjetoAT | None": ...


@runtime_checkable
class RepositorioDeReferencias(Protocol):
    """Persistência da `ReferenciaCruzada` — agregado PRÓPRIO, fora dos projetos (RF-33).

    `listar_referencias` aceita `projeto_id` como filtro opcional porque a vista da cadeia
    (RF-41) parte de um projeto e precisa das referências que o tocam — nos dois sentidos.
    O inquilino continua sendo o primeiro parâmetro posicional e sem valor padrão: a
    fronteira é a consulta, aqui como em todo o resto.
    """

    def salvar_referencia(self, referencia: "ReferenciaCruzada") -> None: ...

    def obter_referencia(
        self, inquilino_id: str, referencia_id: UUID
    ) -> "ReferenciaCruzada | None": ...

    def listar_referencias(
        self, inquilino_id: str, *, projeto_id: UUID | None = None
    ) -> list["ReferenciaCruzada"]: ...


@runtime_checkable
class RepositorioDaCadeia(
    RepositorioDeARA,
    RepositorioDeNuvens,
    RepositorioDeARF,
    RepositorioDeAPR,
    RepositorioDeAT,
    RepositorioDeReferencias,
    Protocol,
):
    """As seis portas juntas — a forma que o encadeamento do M4 exige (E4.4).

    Promover lê uma Árvore da Realidade Atual e grava uma Nuvem de Conflito **mais** uma
    referência; semear lê a nuvem e grava a Árvore da Realidade Futura; derivar desce até
    a Árvore de Transição. Declarar a exigência como `Protocol` composto é o que impede o
    caso de uso de receber um repositório que só sabe metade do caminho — e é mais honesto
    do que um `Any` com comentário pedindo cuidado.
    """


# ---------------------------------------------------------------------------------------
# M6 · Focalização (spec 009)
#
# Uma porta própria, pelo mesmo motivo das anteriores (RN-04 da spec 004): o núcleo não
# conhece semântica da Teoria das Restrições, e uma porta única obrigaria a assinatura do
# M1 a mencionar ciclo de focalização, restrição e decisão herdada. O adaptador implementa
# todas; o domínio continua com uma por ferramenta.
# ---------------------------------------------------------------------------------------


@runtime_checkable
class RepositorioDeFocalizacao(Protocol):
    """Persistência da `AnaliseDeFocalizacao` — a jornada dos cinco passos (M6).

    A regra do inquilino não tem exceção aqui tampouco: primeiro parâmetro posicional, sem
    valor padrão.
    """

    def salvar_focalizacao(self, analise: "AnaliseDeFocalizacao") -> None: ...

    def obter_focalizacao(
        self, inquilino_id: str, projeto_id: UUID
    ) -> "AnaliseDeFocalizacao | None": ...


@runtime_checkable
class RepositorioDaJornada(RepositorioDeFocalizacao, RepositorioDeProjetos, Protocol):
    """As duas portas juntas — a forma que a validação de vínculo exige (RNF-04).

    Criar um vínculo **lê** o projeto de destino (existência, inquilino, ferramenta e
    estado) e **grava** a análise. Declarar a exigência como `Protocol` composto é o que
    impede o caso de uso de receber um repositório que só sabe metade do caminho: sem a
    metade de leitura, a validação de vínculo viraria disciplina em vez de tipo, e um
    vínculo para um projeto de outro inquilino entraria em silêncio.

    O que ela deliberadamente **não** compõe: as portas do M2, M3 e M4. O vínculo é opaco
    no domínio (plano 009, decisão 2) e a borda valida o projeto pelo NÚCLEO — ferramenta
    e inquilino bastam. Compor as seis portas aqui acoplaria o M6 à evolução de todas elas
    para não ganhar nada.
    """


@runtime_checkable
class RepositorioDaSugestaoDeRestricao(RepositorioDaJornada, RepositorioDeARA, Protocol):
    """A forma que `toc.suggest_constraint` exige (RF-19, INT-05).

    Sugerir a restrição **lê** a Árvore da Realidade Atual vinculada ao passo `identificar`
    (para tirar dela as causas raiz candidatas) e **grava** a análise, quando a proposta é
    aceita. É a única operação do M6 que precisa conhecer outro módulo por dentro — e por
    isso é a única que declara a porta composta, em vez de todo o módulo carregar o
    acoplamento.
    """


@runtime_checkable
class MotorDeGeracaoDeNuvem(Protocol):
    """A porta da assistência do M3 — e o que ela devolve **não é texto** (RF-21).

    **Não é um provedor de modelo** (ADR 0007: nenhum SDK — *Software Development Kit* —
    de provedor no produto). É a porta pela qual a assistência chega; quem fala com modelo
    é a fundação, pelo catálogo governado. O adaptador deste ciclo é determinístico e
    local, e declara-se como tal.

    O tipo de retorno é a lição inteira do ciclo: `Mapping`, nunca `str`. Na 4ª geração da
    linhagem a geração devolvia markdown cru (`tocbuilderv3/services/geminiService.ts:173`)
    e um parser por expressão regular tentava reconstruir a nuvem — devolvendo `null`
    inteiro a qualquer variação de formato. Aqui a estrutura é o contrato, e quem a valida
    é `toc_api.dominio.geracao.ResultadoDeGeracao`, no servidor, antes de a proposta
    existir (RF-22, RNF-04).
    """

    def gerar_nuvem(
        self, *, narrativa: str, contexto: Mapping[str, Any]
    ) -> Mapping[str, Any]: ...

    def sugerir_premissas(
        self, *, aresta: str, narrativa: str, contexto: Mapping[str, Any]
    ) -> Sequence[Mapping[str, Any]]: ...

    def sugerir_injecoes(
        self, *, premissa: str, contexto: Mapping[str, Any]
    ) -> Sequence[Mapping[str, Any]]: ...
