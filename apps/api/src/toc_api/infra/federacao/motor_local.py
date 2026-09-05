"""O motor de conversa local — determinístico, sem provedor de modelo (ADR 0007).

Siglas, uma vez: **APH** — Aplicação ↔ Harness · **IA** — inteligência artificial ·
**SSE** — *Server-Sent Events* · **UDE** — Efeito Indesejável.

**Por que este adaptador existe e o que ele não é.** O ADR 0007 é categórico: nenhuma
biblioteca de provedor de inteligência artificial no produto — quem fala com modelo é a
fundação, e esta aplicação **se descreve** (catálogo e snapshot) e **governa** (máquina de
estados e traço). A violação canônica que a linhagem nos legou é
`tocbuilderv3/services/geminiService.ts:16`, que inicializava o cliente do provedor **no
navegador**, com a chave junto.

Então o que produz o turno? Este motor: prosa determinística montada a partir do que a
própria aplicação sabe — a tela em que a pessoa está, o inventário que ela pode operar. É o
lado da aplicação do fio, exercitável de ponta a ponta e verificável pela suíte de
conformidade **sem** chamar ninguém. Quando a fundação repassar o fio dela, troca-se o
adaptador — a porta `MotorDeConversa` já está no lugar, e nada acima dela muda.

O turno é fatiado em pedaços de propósito: o fio é *streaming* tipado, e um turno de um
evento só não exercitaria nem o `seq` monotônico nem o cancelamento cooperativo.
"""
from __future__ import annotations

from typing import Iterator

from ...dominio.federacao.principal import Principal
from ...dominio.federacao.snapshot import SnapshotDeContexto


class MotorDeConversaLocal:
    """Implementa `MotorDeConversa`. Não emite o terminador: quem o garante é a borda."""

    def responder(
        self,
        *,
        texto: str,
        snapshot: SnapshotDeContexto | None,
        principal: Principal,
    ) -> Iterator[tuple[str, dict]]:
        yield (
            "thinking",
            {
                "text": (
                    "Roteando o pedido pelo catálogo declarado; nenhum provedor de "
                    "inteligência artificial é consultado por esta aplicação (ADR 0007)."
                )
            },
        )
        yield ("content", {"text": "Recebi a sua mensagem. "})
        if snapshot is not None:
            # O snapshot entra como DADO: o que é dito sobre ele é a identidade da tela e
            # a contagem de campos, nunca o conteúdo dos campos (APH-7.3).
            yield (
                "content",
                {
                    "text": (
                        f"Estou vendo a tela `{snapshot.screen_id}` "
                        f"({len(snapshot.campos)} campo(s) liberados pelo registro). "
                    )
                },
            )
        else:
            yield ("content", {"text": "Sem contexto de tela nesta mensagem. "})
        if principal.anonimo:
            yield (
                "content",
                {
                    "text": (
                        "Esta sessão não tem identidade da fundação, então nenhuma ação do "
                        "catálogo está disponível — ausência é a fronteira, não recusa."
                    )
                },
            )
        else:
            yield (
                "content",
                {"text": f"Você opera como `{principal.usuario_id}` no inquilino do embarque. "}
            )
        yield ("content", {"text": "Toda ação mutadora nasce proposta e espera a sua decisão."})
