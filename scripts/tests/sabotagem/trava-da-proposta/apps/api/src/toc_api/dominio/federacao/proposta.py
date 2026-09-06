"""Esqueleto do agregado — o estado lido e a confirmação de gravação."""


class CorridaDeDecisao(TransicaoInvalida):
    def __init__(self, proposal_id, *, estado_lido, estado_atual):
        super().__init__("INVALID_TRANSITION", "outra decisão chegou antes")
        self.estado_lido = estado_lido
        self.estado_atual = estado_atual


class ChaveDeIdempotenciaReutilizada(TransicaoInvalida):
    def __init__(self, idempotency_key, *, proposal_id):
        super().__init__("IDEMPOTENCY_KEY_REUSED", "uma chave, uma execução")


class PropostaDeAcao:
    estado_lido: str = field(default="", init=False, repr=False, compare=False)

    def confirmar_gravacao(self) -> None:
        self.estado_lido = self.estado

    def mesma_chave(self, idempotency_key) -> bool:
        return idempotency_key is not None and self.idempotency_key == idempotency_key
