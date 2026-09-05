"""O arranque do serviço — onde a admissão do §B.4 recusa subir, e o processo morre.

Siglas, uma vez: **APH** — Aplicação ↔ Harness · **HTTP** — *HyperText Transfer Protocol*.

A cláusula §B.4.1 do Anexo B é literal: *"a aplicação DEVE recusar-se a subir quando faltar
parâmetro obrigatório, com erro categorizado que diga qual faltou. Subir pela metade,
funcionar até alguém clicar, ou perguntar ao usuário o que o operador deveria ter
configurado são não-conformidades."*

Isso é comportamento de **processo**, não de objeto: por isso mora aqui, e não em
`criar_app`. Quem sobe o serviço em produção usa este módulo:

    uvicorn --factory toc_api.http.arranque:aplicacao

e, faltando qualquer parâmetro, o processo termina com código diferente de zero, com o
código de recusa na **última linha** do log — e sem abrir porta nenhuma (RF-04).

`criar_app` continua funcionando sem admissão, e a assimetria é declarada: é o modo de
desenvolvimento, que não tem introspecção, logo não tem identidade da fundação, logo tem
catálogo composto vazio. Fail-closed, não permissivo.
"""
from __future__ import annotations

import json
import os
import sys
from typing import Mapping, TextIO

from ..dominio.federacao.admissao import OBRIGATORIOS, AdmissaoRecusada, exigir_admissao
from .app import criar_app

CODIGO_DE_SAIDA_DA_RECUSA = 78  # EX_CONFIG do sysexits.h: erro de configuração


def verificar_admissao(ambiente: Mapping[str, str], saida: TextIO) -> None:
    """Confere os parâmetros e **encerra o processo** quando falta algum.

    O log é estruturado (uma linha JSON) porque falha de admissão é o primeiro evento que
    alguém procura num agregador — e uma frase em prosa não se filtra por código.
    """
    try:
        admissao = exigir_admissao(ambiente)
    except AdmissaoRecusada as recusa:
        saida.write(
            json.dumps(
                {
                    "nivel": "critical",
                    "evento": "admissao_recusada",
                    "codigo": recusa.codigo,
                    "parametro": recusa.parametro,
                    "detalhe": recusa.detalhe,
                    "referencia": "Anexo B §B.4.1 · specs/003-esqueleto-federado/contracts/parametros-de-admissao.md",
                    "obrigatorios": [p.variavel for p in OBRIGATORIOS],
                },
                ensure_ascii=False,
            )
            + "\n"
        )
        saida.flush()
        raise SystemExit(CODIGO_DE_SAIDA_DA_RECUSA) from None
    saida.write(
        json.dumps(
            {
                "nivel": "info",
                "evento": "admissao_aceita",
                "app_id": admissao.app_id,
                "host_origin": admissao.host_origin,
                "embed_url": admissao.embed_url,
            },
            ensure_ascii=False,
        )
        + "\n"
    )
    saida.flush()


def aplicacao():  # noqa: ANN201 - fábrica do uvicorn
    """A fábrica de produção: admite **antes** de existir servidor."""
    verificar_admissao(os.environ, sys.stderr)
    return criar_app()


if __name__ == "__main__":  # pragma: no cover - exercitado por subprocesso no teste
    verificar_admissao(os.environ, sys.stderr)
    print(
        json.dumps({"nivel": "info", "evento": "admissao_verificada"}, ensure_ascii=False),
        file=sys.stderr,
    )
