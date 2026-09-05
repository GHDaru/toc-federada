"""Adaptadores da porta `ProvedorDeIdentidade` — o falso do desenvolvimento e o que nega.

Siglas, uma vez: **APH** — Aplicação ↔ Harness · **JSON** — *JavaScript Object Notation*.

**Este arquivo não é a introspecção.** A troca real do token da fundação por identidade
(`POST /auth/introspect`, §B.6 do Anexo B do Padrão APH) é a `PortaDeIntrospeccao` de
`dominio/federacao/portas.py`, com o seu adaptador próprio. O que existe aqui é o mínimo
para o desenvolvimento andar sem inventar login: um registro fechado de personas
**fictícias** (ADR 0006), lido de variável de ambiente do servidor (P7).

O registro é montado pela **mesma** função que traduz a resposta da introspecção —
`principal_de_introspeccao` —, e não por um construtor paralelo. Um segundo caminho de
nascimento de identidade é exatamente o que o RF-07 da spec 006 proíbe; o falso alimenta
o caminho verdadeiro com um corpo de mentira, em vez de abrir um caminho de mentira.

Duas regras que este módulo trata como inegociáveis:

1. **Fora de desenvolvimento, o falso não existe.** A fábrica devolve `ProvedorQueNegaTudo`
   em qualquer outro ambiente. O caminho errado — "cai no falso quando o real não está
   montado" — seria um login próprio com outro nome, que é o que o P2 proíbe.
2. **Toda dúvida vira `None`.** Token desconhecido, registro ilegível, ambiente errado: a
   resposta é a mesma e não diz o motivo (§B.6.5 — a distinção é oráculo para quem testa
   tokens).
"""
from __future__ import annotations

import json
from typing import Mapping

from ...dominio.erros import ErroDeDominio
from ...dominio.federacao.principal import Principal, principal_de_introspeccao
from ..configuracao import Configuracao

#: Os únicos ambientes em que um adaptador de mentira pode responder.
AMBIENTES_DE_MENTIRA = frozenset({"desenvolvimento", "teste"})

#: A persona padrão do desenvolvimento — **fictícia por regra** (ADR 0006: "Facilitadora
#: TOC", "Instituição Horizonte"). Nenhum dado real de pessoa entra aqui, nunca.
TOKEN_DE_DESENVOLVIMENTO = "tok-desenvolvimento-facilitadora"

INTROSPECCAO_DE_DESENVOLVIMENTO = {
    "active": True,
    "user": {"id": "usr-facilitadora", "name": "Facilitadora TOC"},
    "tenant_id": "inq-horizonte",
    "capabilities": ["toc:read", "toc:write"],
    "app_id": "toc-federada",
}

PERSONA_DE_DESENVOLVIMENTO: tuple[str, Principal] = (
    TOKEN_DE_DESENVOLVIMENTO,
    principal_de_introspeccao(INTROSPECCAO_DE_DESENVOLVIMENTO),
)


class ProvedorQueNegaTudo:
    """Fail-closed puro: nenhum token identifica ninguém.

    É o que roda quando não há adaptador real de introspecção montado. O serviço sobe, o
    `/saude` responde e **diz** qual provedor está de pé — e toda rota devolve `401`.
    Subir negando é observável; subir aceitando uma identidade de mentira, não.
    """

    def identificar(self, token: str) -> Principal | None:
        return None


class ProvedorDeIdentidadeFalso:
    """Registro fechado `token → principal`. Não decodifica nada do que o cliente manda.

    O §B.9.5 diz que "a aplicação também não confia: o `payload` do handshake é dado, e a
    identidade só existe depois da introspecção". Um falso que derivasse o inquilino do
    formato do token ensinaria o hábito contrário — por isso ele só consulta um registro
    montado no servidor.
    """

    def __init__(self, registro: Mapping[str, Principal]) -> None:
        self._registro = dict(registro)

    def identificar(self, token: str) -> Principal | None:
        return self._registro.get(token)


def _registro_do_ambiente(bruto: str | None) -> dict[str, Principal] | None:
    """Lê `TOC_IDENTIDADES_FALSAS`. Devolve `None` quando o texto não é utilizável.

    `None` (ilegível) e `{}` (legível e vazio) são coisas diferentes: o primeiro faz a
    fábrica cair no provedor que nega tudo, porque configuração quebrada não pode virar
    permissão.
    """
    if bruto is None:
        return None
    try:
        cru = json.loads(bruto)
    except ValueError:
        return None
    if not isinstance(cru, dict):
        return None

    registro: dict[str, Principal] = {}
    for token, dados in cru.items():
        if not isinstance(dados, dict):
            return None
        try:
            registro[str(token)] = principal_de_introspeccao(
                {
                    "active": True,
                    "user": {
                        "id": dados.get("usuario_id"),
                        "name": dados.get("nome_de_exibicao", ""),
                    },
                    "tenant_id": dados.get("inquilino_id"),
                    "capabilities": list(dados.get("capabilities", ())),
                    **({"app_id": dados["app_id"]} if "app_id" in dados else {}),
                }
            )
        except ErroDeDominio:
            return None
    return registro


def criar_provedor_de_identidade(config: Configuracao):
    """Escolhe o adaptador por ambiente. Um lugar só sabe da escolha (padrão da fábrica).

    Quando o adaptador real de introspecção estiver montado, é aqui que ele entra — e a
    assinatura já é a que ele precisa: recebe a configuração, devolve a porta.
    """
    if config.ambiente.strip().lower() not in AMBIENTES_DE_MENTIRA:
        return ProvedorQueNegaTudo()

    registro = _registro_do_ambiente(config.identidades_falsas)
    if registro is None and config.identidades_falsas is not None:
        return ProvedorQueNegaTudo()
    if registro is None:
        token, persona = PERSONA_DE_DESENVOLVIMENTO
        registro = {token: persona}
    return ProvedorDeIdentidadeFalso(registro)
