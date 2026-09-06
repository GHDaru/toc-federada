"""Esqueleto do registro único do §A.7 — código próprio, mas documentado."""

CODIGOS_PROPRIOS = {
    "IDEMPOTENCY_KEY_REUSED": (
        "a chave da confirmação já pertence a OUTRA proposta deste inquilino (409)"
    ),
    "VERSION_CONFLICT": (
        "a escrita partiu de uma versão do agregado que já não é a do banco (409)"
    ),
}
