"""Esqueleto do caso de uso genérico — ele NUNCA destrava o núcleo."""


class AdicionarNo:
    def agir(self, projeto, **kw):
        return projeto.adicionar_no(**kw)
