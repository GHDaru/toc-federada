"""O Principal — a identidade que só existe depois da introspecção (§B.6 do Anexo B).

Siglas, uma vez: **APH** — Aplicação ↔ Harness · **TTL** — *Time To Live* (tempo de vida).

Este módulo é onde o P2 (federação por contrato) vira código. Três invariantes, e nenhuma
delas é opinião — as três estão escritas na norma com contraexemplo medido:

1. **Não existe construtor a partir do handshake.** `principal_de_introspeccao` exige
   `active: true`; o payload do handshake não tem esse campo, e é por isso que um
   handshake forjado não vira autorização (§B.6.2, §B.9.5).
2. **`{active:false}` não explica por quê.** Distinguir expirado de consumido de
   inexistente é dar oráculo a quem testa token (§B.6.5). O nosso erro carrega **um** só
   código, `GRANT_INATIVO`.
3. **Capability é `recurso:verbo` sem curinga** (§B.7.1). Curinga transforma concessão em
   cheque em branco e torna incalculável a interseção do §B.6.7.

E uma decisão de leitura, que a spec 006 fixa na RF-19: as capabilities recebidas são
**teto do hospedeiro**, não retrato do usuário. O APH-9.4b é 🧪 e sem laboratório; a norma
mediu o caso em que uma usuária sem nenhuma capability `toc:*` abre o embarque e a
aplicação recebe `["toc:read","toc:write"]` (§B.6.7, e a nossa
`mensagens/003-para-ghdaru-o-que-falta-para-embarcar-a-toc.md` documenta o mesmo). Por
isso a verificação local acontece **sempre**, em todo caso de uso, e nunca é dispensada
por "o hospedeiro já filtrou".
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Mapping

from ..erros import ErroDeDominio
from ..identidade import DonoDoProjeto

FORMA_DE_CAPABILITY = re.compile(r"^[a-z][a-z0-9-]+:[a-z][a-z0-9-]+$")


class IntrospeccaoInvalida(ErroDeDominio):
    """A resposta da introspecção não produz identidade. Carrega código estável."""

    def __init__(self, codigo: str, detalhe: str) -> None:
        super().__init__(f"{codigo}: {detalhe}")
        self.codigo = codigo
        self.detalhe = detalhe


class CapabilityInvalida(ErroDeDominio):
    """Forma fora de `recurso:verbo`, ou curinga (§B.7.1)."""


@dataclass(frozen=True, slots=True)
class Capability:
    """`recurso:verbo`, validada na construção. Sem curinga, em caso nenhum."""

    valor: str

    def __post_init__(self) -> None:
        if not FORMA_DE_CAPABILITY.match(self.valor):
            raise CapabilityInvalida(
                f"capability {self.valor!r} fora da forma recurso:verbo sem curinga (§B.7.1)"
            )

    def __str__(self) -> str:  # pragma: no cover - conveniência de log
        return self.valor


def _instante(bruto: Any) -> datetime | None:
    if not isinstance(bruto, str) or not bruto:
        return None
    texto = bruto.replace("Z", "+00:00")
    try:
        instante = datetime.fromisoformat(texto)
    except ValueError:
        return None
    return instante if instante.tzinfo else instante.replace(tzinfo=timezone.utc)


@dataclass(frozen=True, slots=True)
class Principal:
    """Quem está do outro lado — usuário, inquilino e o **teto** de capabilities.

    Nunca guarda o grant: ele é trocado e descartado (RF-08, RNF-01). O que fica é o que
    a introspecção afirmou.
    """

    usuario_id: str | None
    nome_de_exibicao: str
    inquilino_id: str | None
    capabilities: tuple[Capability, ...] = ()
    expira_em: datetime | None = None
    app_id: str | None = None
    anonimo: bool = False
    capabilities_recusadas: tuple[str, ...] = field(default=())

    def pode(self, capability: str) -> bool:
        """Fail-closed: a ausência da capability é `False`, nunca exceção silenciosa."""
        return any(c.valor == capability for c in self.capabilities)

    def expirado_em(self, instante: datetime) -> bool:
        return self.expira_em is not None and instante >= self.expira_em

    def dono(self) -> DonoDoProjeto:
        """A chave de isolamento do M1/M2, derivada **só** daqui."""
        if self.anonimo or not self.inquilino_id or not self.usuario_id:
            raise IntrospeccaoInvalida(
                "SEM_IDENTIDADE",
                "sessão sem identidade não alcança dado de inquilino nenhum",
            )
        return DonoDoProjeto(inquilino_id=self.inquilino_id, usuario_id=self.usuario_id)

    def __repr__(self) -> str:
        # Sem e-mail e sem nome no `repr`: identificador de inquilino é opaco e não é dado
        # de pessoa (ADR 0006); nome e e-mail são, e caem em log de exceção por acidente.
        return (
            f"Principal(usuario_id={self.usuario_id!r}, inquilino_id={self.inquilino_id!r}, "
            f"capabilities={[c.valor for c in self.capabilities]!r}, anonimo={self.anonimo!r})"
        )


def principal_anonimo() -> Principal:
    """A sessão sem identidade: existe, e não alcança nada.

    Ela é o que permite a superfície conversacional do Nível 1 ser exercida de fora (a
    suíte de conformidade é caixa-preta e não tem grant) **sem** abrir uma janela: sem
    inquilino não há consulta possível, e sem capability o catálogo composto é vazio —
    ausência é a fronteira (§B.7.3), não uma recusa que revela o que existe.
    """
    return Principal(
        usuario_id=None,
        nome_de_exibicao="",
        inquilino_id=None,
        capabilities=(),
        anonimo=True,
    )


def principal_de_introspeccao(resposta: Mapping[str, Any]) -> Principal:
    """Traduz a resposta de `POST /auth/introspect` em Principal — ou recusa.

    É o **único** construtor de identidade da aplicação. Não existe um segundo que aceite
    o payload do handshake, e a ausência é o requisito (RF-07).
    """
    if resposta.get("active") is not True:
        # §B.6.5: um código só, sem oráculo. Quem lê o log não descobre se o token
        # existiu, se venceu ou se já tinha sido usado — porque a resposta não diz.
        raise IntrospeccaoInvalida(
            "GRANT_INATIVO", "a introspecção não reconheceu a credencial apresentada"
        )

    usuario = resposta.get("user")
    if not isinstance(usuario, Mapping) or not usuario.get("id"):
        raise IntrospeccaoInvalida(
            "INTROSPECCAO_SEM_USUARIO", "resposta ativa sem `user.id`"
        )

    inquilino = resposta.get("tenant_id")
    if not isinstance(inquilino, str) or not inquilino.strip():
        raise IntrospeccaoInvalida("INTROSPECCAO_SEM_TENANT", "resposta ativa sem `tenant_id`")

    brutas = resposta.get("capabilities")
    if not isinstance(brutas, (list, tuple)):
        raise IntrospeccaoInvalida(
            "INTROSPECCAO_SEM_CAPABILITIES",
            "resposta ativa sem `capabilities` — sem elas não há autorização, e presumir "
            "lista vazia esconderia um defeito do hospedeiro",
        )

    app_id = resposta.get("app_id")
    # §B.6.4: resposta de GRANT (a que traz `app_id`) não pode conter `role`. Papel pleno
    # entregue a terceiro convida autorização por papel fora do escopo concedido.
    if app_id is not None and "role" in resposta:
        raise IntrospeccaoInvalida(
            "INTROSPECCAO_GRANT_COM_ROLE",
            "resposta de grant trouxe `role` — proibido pelo §B.6.4",
        )

    aceitas: list[Capability] = []
    recusadas: list[str] = []
    for bruta in brutas:
        if not isinstance(bruta, str):
            recusadas.append(repr(bruta))
            continue
        try:
            aceitas.append(Capability(bruta))
        except CapabilityInvalida:
            # Fail-closed e aditivo: a capability malformada (curinga, por exemplo) não
            # entra e não derruba o embarque — quem errou foi o hospedeiro, e derrubar
            # transformaria o defeito dele em indisponibilidade nossa. O registro em
            # `capabilities_recusadas` é o que faz o defeito aparecer no traço.
            recusadas.append(bruta)

    return Principal(
        usuario_id=str(usuario["id"]),
        nome_de_exibicao=str(usuario.get("name") or ""),
        inquilino_id=inquilino,
        capabilities=tuple(aceitas),
        expira_em=_instante(resposta.get("expires_at")),
        app_id=str(app_id) if isinstance(app_id, str) else None,
        capabilities_recusadas=tuple(recusadas),
    )
