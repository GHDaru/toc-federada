"""As portas do domínio — todo efeito sai por aqui (P3, brief §0.3).

São `typing.Protocol` e não classes-base: o adaptador não herda nada nosso, e o duplo do
teste conforma pela FORMA. É o padrão lido em `ghdaru` —
`apps/api/src/ghdaru_api/documents/ports/storage.py` — trazido para cá, não copiado:
aqui toda leitura carrega o inquilino na assinatura, que é o que faz o isolamento ser um
fato de tipo e não de disciplina.
"""
from __future__ import annotations

from datetime import datetime
from typing import ContextManager, Protocol, runtime_checkable
from uuid import UUID

from .ara import ProjetoARA
from .projeto import Projeto


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
