"""Esqueleto do caso de uso — a reserva ANTES do efeito, que é a peça central."""


class _ComGovernanca(CasoDeUso):
    def _reservar(self, proposta, principal) -> None:
        inquilino, usuario = self._exigir_identidade(principal)
        self._propostas.salvar(inquilino, usuario, proposta)

    def _executar(self, proposta, acao, principal, *, reservar: bool = True) -> None:
        agora = self._relogio.agora()
        proposta.transicionar("executar", em=agora)
        if reservar:
            self._reservar(proposta, principal)
        status, mensagem = self._executor.executar(
            action_id=acao.action_id, args=dict(proposta.args), principal=principal
        )
        proposta.concluir(desfecho=Desfecho(status=status), em=agora)


class DecidirProposta(_ComGovernanca):
    def executar(self, *, principal, proposal_id, aprovado, idempotency_key=None):
        proposta = self._propostas.obter(inquilino, proposal_id)
        if idempotency_key and proposta.mesma_chave(idempotency_key):
            return self._desfecho_da_mesma_chave(inquilino, proposta)
        return self._como_resultado(proposta)
