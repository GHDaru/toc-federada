"""Esqueleto do registro único do §A.7 — só a linha que o portão procura."""
CODIGOS_PROPRIOS = {
    "MUTATION_REFUSED": "operação válida em geral, recusada NESTE estado do agregado (409)",
    "VERSION_CONFLICT": (
        "a escrita partiu de uma versão do agregado que já não é a do banco: outra "
        "pessoa gravou antes (409)"
    ),
}
