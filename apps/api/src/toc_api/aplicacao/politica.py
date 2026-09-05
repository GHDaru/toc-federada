"""A política de autorização — função pura, **fora** do modelo de linguagem (APH-7.2).

Siglas, uma vez: **APH** — Aplicação ↔ Harness · **HTTP** — *HyperText Transfer Protocol*.

Duas classes, e a segunda existe para ser sabotagem, não produto.

`PoliticaPorCapability` é a de verdade: `principal.pode(capability)`, e nada mais. Nenhuma
entrada de texto de modelo, nenhuma leitura de payload de tela, nenhum `if` sobre a origem
da proposta. O §B.7.2 é explícito: a derivação é política pura, verificada nos **casos de
uso** — não na camada de rota.

`PoliticaSempreVerdadeira` é o contraexemplo que a norma nomeia (APH-7.2) e que a spec 006
manda ter na suíte (RF-20): *"a suíte DEVE conter a sabotagem que troca a política por
`lambda: True` e vê os testes de recusa falharem"*. Ela vive no código de produção, e não
no teste, por um motivo simples: assim ela aparece na leitura de quem audita a política, com
a docstring dizendo o que é. Um portão executável confere que ela não é injetada em lugar
nenhum — `scripts/check-politica.sh`.
"""
from __future__ import annotations

from typing import Protocol, runtime_checkable

from ..dominio.federacao.principal import Principal


@runtime_checkable
class PoliticaDeAutorizacao(Protocol):
    def permite(self, principal: Principal, capability: str) -> bool: ...


class PoliticaPorCapability:
    """A política do produto: capability da introspecção, e só ela.

    Fail-closed por construção — `Principal.pode` devolve `False` para o que não está na
    lista, inclusive para o principal anônimo, cuja lista é vazia.
    """

    def permite(self, principal: Principal, capability: str) -> bool:
        return principal.pode(capability)


class PoliticaSempreVerdadeira:
    """**NÃO-CONFORMIDADE DECLARADA** (APH-7.2). Existe só para a sabotagem da RF-20.

    Injetá-la em composição de produção é o defeito que o `scripts/check-politica.sh`
    recusa. O valor dela é medir os testes de recusa: com esta política, eles têm de
    deixar de passar — e é isso que prova que eles olham para a política, em vez de
    passarem por acaso.
    """

    def permite(self, principal: Principal, capability: str) -> bool:  # noqa: ARG002
        return True
