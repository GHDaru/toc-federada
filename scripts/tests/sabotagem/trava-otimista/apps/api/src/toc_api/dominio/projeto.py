"""Esqueleto do agregado Projeto — só a forma que o portão inspeciona."""
from dataclasses import dataclass, field


@dataclass(slots=True)
class Projeto:
    versao: int = 1
    versao_lida: int = field(default=0, init=False, repr=False, compare=False)

    def confirmar_gravacao(self) -> None:
        self.versao_lida = self.versao

    def _avancar(self) -> None:
        self.versao += 1
