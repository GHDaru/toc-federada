"""Esqueleto do adaptador SQL — as três portas de escrita e a trava."""
from ...dominio.erros import ConflitoDeVersao, NaoEncontrado


def _para_agregado(linha, nos, arestas):
    projeto = Projeto()
    projeto.eventos = ()
    projeto.versao_lida = linha.versao
    return projeto


class RepositorioDeProjetosSQL:
    def __init__(self, sessao):
        self._sessao = sessao

    def salvar(self, projeto) -> None:
        with self._sessao.begin() as s:
            self._gravar_projeto(s, projeto)
            self._reconciliar_grafo(s, projeto)
        projeto.confirmar_gravacao()

    def salvar_ara(self, ara) -> None:
        projeto = ara.projeto
        with self._sessao.begin() as s:
            self._gravar_projeto(s, projeto)
            self._reconciliar_grafo(s, projeto)
            self._reconciliar_ara(s, ara)
        projeto.confirmar_gravacao()

    def salvar_nuvem(self, nuvem) -> None:
        projeto = nuvem.projeto
        with self._sessao.begin() as s:
            self._gravar_projeto(s, projeto)
            self._reconciliar_grafo(s, projeto)
            self._reconciliar_nuvem(s, nuvem)
        projeto.confirmar_gravacao()

    def salvar_arf(self, arf) -> None:
        projeto = arf.projeto
        with self._sessao.begin() as s:
            self._gravar_projeto(s, projeto)
            self._reconciliar_grafo(s, projeto)
        projeto.confirmar_gravacao()

    def salvar_apr(self, apr) -> None:
        projeto = apr.projeto
        with self._sessao.begin() as s:
            self._gravar_projeto(s, projeto)
            self._reconciliar_grafo(s, projeto)
        projeto.confirmar_gravacao()

    def salvar_at(self, at) -> None:
        projeto = at.projeto
        with self._sessao.begin() as s:
            self._gravar_projeto(s, projeto)
            self._reconciliar_grafo(s, projeto)
        projeto.confirmar_gravacao()

    def salvar_focalizacao(self, analise) -> None:
        """M6 — a jornada dos cinco passos (spec 009): a mesma trava, o mesmo caminho."""
        with self._sessao.begin() as s:
            self._gravar_projeto(s, analise.projeto)
            self._reconciliar_focalizacao(s, analise)
        analise.projeto.confirmar_gravacao()

    def salvar_referencia(self, referencia) -> None:
        with self._sessao.begin() as s:
            self._gravar_referencia(s, referencia)
        referencia.confirmar_gravacao()

    def _gravar_referencia(self, s, referencia) -> None:
        existe = s.execute(
            select(tabela_referencia.c.versao).where(
                tabela_referencia.c.id == referencia.id,
            )
        ).first()
        if referencia.versao_lida == 0:
            if existe is not None:
                raise ConflitoDeVersao(
                    f"referencia:{referencia.id}", versao_lida=0, versao_atual=existe.versao
                )
            s.execute(insert(tabela_referencia).values(**_referencia_para_linha(referencia)))
            return
        if existe is None:
            raise NaoEncontrado(str(referencia.id))
        resultado = s.execute(
            update(tabela_referencia)
            .where(
                tabela_referencia.c.id == referencia.id,
                tabela_referencia.c.versao == referencia.versao_lida,
            )
            .values(**_referencia_para_linha(referencia))
        )
        if resultado.rowcount == 0:
            atual = s.execute(
                select(tabela_referencia.c.versao).where(
                    tabela_referencia.c.id == referencia.id,
                )
            ).first()
            if atual is None:
                raise NaoEncontrado(str(referencia.id))
            raise ConflitoDeVersao(
                f"referencia:{referencia.id}",
                versao_lida=referencia.versao_lida,
                versao_atual=atual.versao,
            )

    def _gravar_projeto(self, s, projeto) -> None:
        linha = _para_linha(projeto)
        existe = s.execute(
            select(tabela_projeto.c.versao).where(
                tabela_projeto.c.id == projeto.id,
                tabela_projeto.c.tenant_id == projeto.dono.inquilino_id,
            )
        ).first()
        if projeto.versao_lida == 0:
            if existe is not None:
                raise ConflitoDeVersao(
                    f"projeto:{projeto.id}", versao_lida=0, versao_atual=existe.versao
                )
            s.execute(insert(tabela_projeto).values(**linha))
            return
        if existe is None:
            raise NaoEncontrado(str(projeto.id))
        resultado = s.execute(
            update(tabela_projeto)
            .where(
                tabela_projeto.c.id == projeto.id,
                tabela_projeto.c.tenant_id == projeto.dono.inquilino_id,
                tabela_projeto.c.versao == projeto.versao_lida,
            )
            .values(**linha)
        )
        if resultado.rowcount == 0:
            atual = s.execute(
                select(tabela_projeto.c.versao).where(
                    tabela_projeto.c.id == projeto.id,
                )
            ).first()
            if atual is None:
                raise NaoEncontrado(str(projeto.id))
            raise ConflitoDeVersao(
                f"projeto:{projeto.id}",
                versao_lida=projeto.versao_lida,
                versao_atual=atual.versao,
            )

    def _reconciliar_grafo(self, s, projeto) -> None:
        s.execute(delete(tabela_no).where(tabela_no.c.id.notin_(ids_de_no)))

    def _reconciliar_ara(self, s, ara) -> None:
        pass

    def _reconciliar_nuvem(self, s, nuvem) -> None:
        pass
