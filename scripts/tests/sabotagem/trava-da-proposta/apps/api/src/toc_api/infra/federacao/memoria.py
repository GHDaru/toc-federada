"""Esqueleto do duplo em memória — a MESMA trava, e cópia na fronteira."""
from copy import deepcopy

from ...dominio.federacao.proposta import ChaveDeIdempotenciaReutilizada, CorridaDeDecisao


class RepositorioDePropostasEmMemoria:
    def _exigir_estado_lido(self, inquilino_id, proposta) -> None:
        guardada = self.itens.get((inquilino_id, proposta.proposal_id))
        if guardada is None:
            return
        if proposta.estado_lido != guardada.estado:
            raise CorridaDeDecisao(
                proposta.proposal_id,
                estado_lido=proposta.estado_lido,
                estado_atual=guardada.estado,
            )

    def _exigir_chave_livre(self, inquilino_id, proposta) -> None:
        raise ChaveDeIdempotenciaReutilizada(proposta.idempotency_key, proposal_id="outra")

    def salvar(self, inquilino_id, usuario_id, proposta) -> None:
        with self._trava:
            self._exigir_estado_lido(inquilino_id, proposta)
            self._exigir_chave_livre(inquilino_id, proposta)
            proposta.confirmar_gravacao()
            self.itens[(inquilino_id, proposta.proposal_id)] = deepcopy(proposta)

    def obter(self, inquilino_id: str, proposal_id: str):
        with self._trava:
            achada = self.itens.get((inquilino_id, proposal_id))
            if achada is None:
                return None
            copia = deepcopy(achada)
        copia.estado_lido = copia.estado
        return copia

    def aguardar_desfecho(self, inquilino_id, proposal_id):
        for _ in range(TENTATIVAS_DE_ESPERA):
            proposta = self.obter(inquilino_id, proposal_id)
            if proposta is None or proposta.terminal:
                return proposta
            time.sleep(PAUSA_DA_ESPERA)
        return self.obter(inquilino_id, proposal_id)
