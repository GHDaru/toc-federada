"""Identidade federada (§B.6, §B.7) — o Principal só existe depois da introspecção.

Siglas: **APH** — Aplicação ↔ Harness · **TTL** — *Time To Live* (tempo de vida).

O que estes testes fixam, e o motivo de cada um estar aqui:

- Não há construtor a partir do payload do handshake (§B.6.2, RF-07). Confiar no
  handshake é o defeito que a norma proíbe pelo nome.
- `{active:false}` não distingue expirado de consumido de inexistente (§B.6.5).
- Capability é `recurso:verbo` **sem curinga** (§B.7.1): curinga é cheque em branco.
- As capabilities da introspecção são **teto**, não retrato do usuário (§B.6.7 / APH-9.4b,
  medido e sem laboratório) — por isso existe `pode()` e não existe `é_admin`.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from toc_api.dominio.federacao.principal import (
    Capability,
    CapabilityInvalida,
    IntrospeccaoInvalida,
    Principal,
    principal_anonimo,
    principal_de_introspeccao,
)

AGORA = datetime(2026, 9, 5, 12, 0, tzinfo=timezone.utc)

RESPOSTA_DE_GRANT = {
    "active": True,
    "user": {"id": "u-horizonte-01", "name": "Facilitadora TOC", "email": "facilitadora@exemplo"},
    "tenant_id": "instituicao-horizonte",
    "capabilities": ["toc:read", "toc:write"],
    "app_id": "toc",
    "expires_at": "2026-09-05T12:30:00Z",
}


def test_resposta_de_grant_ativo_vira_principal() -> None:
    principal = principal_de_introspeccao(RESPOSTA_DE_GRANT)

    assert principal.usuario_id == "u-horizonte-01"
    assert principal.inquilino_id == "instituicao-horizonte"
    assert principal.capabilities == (Capability("toc:read"), Capability("toc:write"))
    assert principal.pode("toc:read") is True
    assert principal.pode("toc:write") is True
    assert principal.pode("toc:admin") is False


def test_active_falso_nao_produz_principal_e_nao_distingue_o_motivo() -> None:
    """§B.6.5: expirado, consumido e inexistente respondem a mesma coisa."""
    with pytest.raises(IntrospeccaoInvalida) as erro:
        principal_de_introspeccao({"active": False})

    assert erro.value.codigo == "GRANT_INATIVO"
    texto = str(erro.value).lower()
    for oraculo in ("expirado", "consumido", "inexistente"):
        assert oraculo not in texto


def test_payload_de_handshake_nao_constroi_identidade() -> None:
    """RF-07: o handshake é dado; a identidade vem da introspecção.

    Um payload de handshake tem `token`, `tenant`, `capabilities` e `theme` — e nenhum
    `active`. Sem `active: true` explícito, não há Principal, e é isso que impede um
    handshake forjado de virar autorização.
    """
    handshake = {
        "token": "ghdg_grant_sintetico",
        "tenant": {"id": "instituicao-horizonte", "name": "Instituição Horizonte"},
        "capabilities": ["toc:read", "toc:write"],
        "theme": {"tokens": {"color-primary": "#123456"}},
    }

    with pytest.raises(IntrospeccaoInvalida) as erro:
        principal_de_introspeccao(handshake)

    assert erro.value.codigo == "GRANT_INATIVO"


def test_resposta_sem_capabilities_e_recusada() -> None:
    """`INTROSPECCAO_SEM_CAPABILITIES` do contrato: sem capabilities não há autorização,
    e presumir lista vazia silenciosamente esconderia um defeito do hospedeiro."""
    resposta = {k: v for k, v in RESPOSTA_DE_GRANT.items() if k != "capabilities"}

    with pytest.raises(IntrospeccaoInvalida) as erro:
        principal_de_introspeccao(resposta)

    assert erro.value.codigo == "INTROSPECCAO_SEM_CAPABILITIES"


def test_resposta_sem_tenant_e_recusada() -> None:
    resposta = {k: v for k, v in RESPOSTA_DE_GRANT.items() if k != "tenant_id"}

    with pytest.raises(IntrospeccaoInvalida) as erro:
        principal_de_introspeccao(resposta)

    assert erro.value.codigo == "INTROSPECCAO_SEM_TENANT"


def test_curinga_de_capability_e_recusado_na_composicao() -> None:
    """§B.7.1 / RF-18: `toc:*` torna a interseção do §B.6.7 incalculável."""
    for curinga in ("toc:*", "*:*", "*"):
        with pytest.raises(CapabilityInvalida):
            Capability(curinga)


def test_capability_fora_da_forma_recurso_verbo_e_recusada() -> None:
    for invalida in ("toc", "TOC:read", "toc:", ":read", "toc read"):
        with pytest.raises(CapabilityInvalida):
            Capability(invalida)


def test_capability_desconhecida_do_hospedeiro_e_ignorada_nao_derruba_o_embarque() -> None:
    """Evolução aditiva: o hospedeiro pode conceder capability de outro módulo.

    Recusar o embarque inteiro por causa de uma capability que não é nossa transformaria
    a evolução do hospedeiro em queda nossa. O que ela **não** faz é autorizar nada aqui.
    """
    resposta = {**RESPOSTA_DE_GRANT, "capabilities": ["toc:read", "prioridades:write"]}

    principal = principal_de_introspeccao(resposta)

    assert principal.pode("toc:read") is True
    assert principal.pode("prioridades:write") is True
    assert principal.pode("toc:write") is False


def test_curinga_vindo_do_hospedeiro_e_descartado_sem_derrubar_e_sem_autorizar() -> None:
    """O curinga é recusado como concessão — mas quem erra é o hospedeiro, não o usuário.

    Fail-closed: a capability curinga não entra, e não vira `toc:read` nem `toc:write`.
    """
    resposta = {**RESPOSTA_DE_GRANT, "capabilities": ["toc:*"]}

    principal = principal_de_introspeccao(resposta)

    assert principal.capabilities == ()
    assert principal.pode("toc:read") is False
    assert principal.pode("toc:write") is False
    assert "toc:*" in principal.capabilities_recusadas


def test_principal_expirado_e_reconhecido_como_tal() -> None:
    """RF-13: `expires_at` vencido encerra a sessão embarcada, sem renovar por conta própria."""
    principal = principal_de_introspeccao(RESPOSTA_DE_GRANT)

    assert principal.expirado_em(AGORA) is False
    assert principal.expirado_em(AGORA + timedelta(minutes=31)) is True


def test_resposta_de_grant_com_role_e_recusada() -> None:
    """§B.6.4: resposta de grant NÃO DEVE conter `role`.

    Aceitá-la em silêncio seria carregar para dentro da aplicação um papel pleno concedido
    a terceiro — exatamente o convite que a cláusula fecha. Recusar aqui é o que faz o
    defeito do hospedeiro aparecer no dia em que ele acontece.
    """
    resposta = {**RESPOSTA_DE_GRANT, "role": "admin"}

    with pytest.raises(IntrospeccaoInvalida) as erro:
        principal_de_introspeccao(resposta)

    assert erro.value.codigo == "INTROSPECCAO_GRANT_COM_ROLE"


def test_resposta_de_sessao_de_usuario_com_role_e_aceita() -> None:
    """A primeira das três respostas do §B.6.3 tem `role` e é legítima — o que o §B.6.4
    proíbe é `role` na resposta de **grant** (que se reconhece por `app_id`)."""
    resposta = {k: v for k, v in RESPOSTA_DE_GRANT.items() if k != "app_id"}
    resposta["user"] = {**resposta["user"], "role": "gestora"}

    principal = principal_de_introspeccao(resposta)

    assert principal.usuario_id == "u-horizonte-01"


def test_principal_anonimo_nao_tem_inquilino_nem_capability() -> None:
    """A sessão sem identidade existe — e não alcança nada.

    Ausência é a fronteira (§B.7.3): sem capability, nenhuma ação entra no catálogo que o
    modelo vê, e sem inquilino nenhuma consulta de repositório é sequer construível.
    """
    anonimo = principal_anonimo()

    assert anonimo.inquilino_id is None
    assert anonimo.capabilities == ()
    assert anonimo.pode("toc:read") is False
    assert anonimo.anonimo is True


def test_o_grant_nunca_entra_no_principal() -> None:
    """RNF-01: o grant é trocado e descartado; nada que o guarde pode existir aqui."""
    principal = principal_de_introspeccao(RESPOSTA_DE_GRANT)

    assert not hasattr(principal, "token")
    assert not hasattr(principal, "grant")
    assert "ghdg_" not in repr(principal)


def test_dono_do_projeto_sai_do_principal_e_nao_do_handshake() -> None:
    """A chave de isolamento do M1/M2 (`DonoDoProjeto`) é derivada da introspecção."""
    principal = principal_de_introspeccao(RESPOSTA_DE_GRANT)

    dono = principal.dono()

    assert dono.inquilino_id == "instituicao-horizonte"
    assert dono.usuario_id == "u-horizonte-01"


def test_principal_anonimo_nao_produz_dono() -> None:
    with pytest.raises(IntrospeccaoInvalida) as erro:
        principal_anonimo().dono()

    assert erro.value.codigo == "SEM_IDENTIDADE"


def test_principal_e_imutavel() -> None:
    principal: Principal = principal_de_introspeccao(RESPOSTA_DE_GRANT)

    with pytest.raises(Exception):
        principal.capabilities = ()  # type: ignore[misc]
