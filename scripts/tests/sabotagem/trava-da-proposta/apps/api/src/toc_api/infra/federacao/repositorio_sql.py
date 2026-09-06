"""Esqueleto do adaptador SQL da proposta — a trava e a tradução da unicidade."""
from ...dominio.federacao.proposta import ChaveDeIdempotenciaReutilizada, CorridaDeDecisao


class RepositorioDePropostasSQL:
    def __init__(self, fabrica_de_sessao):
        self._sessao = fabrica_de_sessao

    def salvar(self, inquilino_id, usuario_id, proposta) -> None:
        with self._sessao() as sessao:
            try:
                if not proposta.estado_lido:
                    sessao.execute(insert(proposta_de_acao).values(**valores))
                else:
                    resultado = sessao.execute(
                        update(proposta_de_acao)
                        .where(
                            proposta_de_acao.c.proposal_id == proposta.proposal_id,
                            proposta_de_acao.c.tenant_id == inquilino_id,
                            proposta_de_acao.c.estado == proposta.estado_lido,
                        )
                        .values(**atualizaveis)
                    )
                    if resultado.rowcount == 0:
                        atual = sessao.execute(select(proposta_de_acao.c.estado)).first()
                        sessao.rollback()
                        raise CorridaDeDecisao(
                            proposta.proposal_id,
                            estado_lido=proposta.estado_lido,
                            estado_atual=atual.estado if atual else "<inexistente>",
                        )
                sessao.commit()
            except IntegrityError as erro:
                sessao.rollback()
                raise self._traduzir(erro, inquilino_id, proposta) from erro
        proposta.confirmar_gravacao()

    def _traduzir(self, erro, inquilino_id, proposta):
        if NOME_DO_INDICE_DE_IDEMPOTENCIA in str(erro) and proposta.idempotency_key:
            return ChaveDeIdempotenciaReutilizada(
                proposta.idempotency_key, proposal_id="<dona>"
            )
        return CorridaDeDecisao(
            proposta.proposal_id, estado_lido=proposta.estado_lido, estado_atual="<existente>"
        )

    def obter(self, inquilino_id, proposal_id):
        return self._reidratar(linha) if linha else None

    def aguardar_desfecho(self, inquilino_id, proposal_id):
        for _ in range(TENTATIVAS_DE_ESPERA):
            proposta = self.obter(inquilino_id, proposal_id)
            if proposta is None or proposta.terminal:
                return proposta
            time.sleep(PAUSA_DA_ESPERA)
        return self.obter(inquilino_id, proposal_id)

    @staticmethod
    def _reidratar(linha):
        proposta = PropostaDeAcao(**campos)
        proposta.estado_lido = proposta.estado
        return proposta


class RepositorioDeTracoSQL:
    """Somente insere e lê — a ausência de `UPDATE`/`DELETE` é o requisito (APH-5.5)."""

    def registrar(self, traco) -> None:
        with self._sessao() as sessao:
            sessao.execute(insert(traco_de_execucao).values(**valores))
            sessao.commit()

    def listar(self, inquilino_id, *, usuario_id=None):
        return []
