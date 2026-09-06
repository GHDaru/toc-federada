"""Esqueleto do adaptador do núcleo — as oito portas de escrita e a exclusão definitiva."""


class RepositorioDeProjetosSQL:
    def salvar(self, projeto) -> None:
        with self._sessao.begin() as s:
            self._gravar_projeto(s, projeto)
        projeto.confirmar_gravacao()

    def salvar_ara(self, ara) -> None:
        with self._sessao.begin() as s:
            self._gravar_projeto(s, ara.projeto)
        ara.projeto.confirmar_gravacao()

    def salvar_nuvem(self, nuvem) -> None:
        with self._sessao.begin() as s:
            self._gravar_projeto(s, nuvem.projeto)
        nuvem.projeto.confirmar_gravacao()

    def salvar_arf(self, arf) -> None:
        with self._sessao.begin() as s:
            self._gravar_projeto(s, arf.projeto)
        arf.projeto.confirmar_gravacao()

    def salvar_apr(self, apr) -> None:
        with self._sessao.begin() as s:
            self._gravar_projeto(s, apr.projeto)
        apr.projeto.confirmar_gravacao()

    def salvar_at(self, at) -> None:
        with self._sessao.begin() as s:
            self._gravar_projeto(s, at.projeto)
        at.projeto.confirmar_gravacao()

    def salvar_focalizacao(self, analise) -> None:
        with self._sessao.begin() as s:
            self._gravar_projeto(s, analise.projeto)
        analise.projeto.confirmar_gravacao()

    def salvar_referencia(self, referencia) -> None:
        with self._sessao.begin() as s:
            self._gravar_referencia(s, referencia)
        referencia.confirmar_gravacao()

    def excluir_definitivamente(self, inquilino_id, projeto_id) -> bool:
        with self._sessao.begin() as s:
            resultado = s.execute(delete(tabela_projeto).where(tabela_projeto.c.id == projeto_id))
        return bool(resultado.rowcount)
