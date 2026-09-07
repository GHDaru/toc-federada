# Fixture `versao-do-agregado` — base VÁLIDA mínima de `scripts/check-versao-do-agregado.sh`

Siglas deste documento, uma vez: **ARA** — Árvore da Realidade Atual · **UDE** — Efeito
Indesejável (*undesirable effect*) · **M1** — Núcleo de Diagramas Lógicos · **ADR** —
*Architecture Decision Record* (registro de decisão arquitetural) · **AST** — *Abstract
Syntax Tree* (árvore sintática abstrata) · **SQL** — *Structured Query Language*.

Um esqueleto de fonte com a forma que o portão lê por AST, e só ela:

- **um núcleo sintético** (`dominio/projeto.py`) com o registro de raízes de ferramenta, o
  `_avancar` que move a versão, a chave `sob_a_raiz`, e uma mutação **pública**
  (`descrever_problema`) que avança por dentro;
- **duas raízes de ferramenta registradas**, de propósito diferentes entre si:
  `ProjetoSintetico` avança direto (`self.projeto._avancar`), delega ao núcleo
  (`adicionar_efeito`) e tem um auxiliar **privado** cujo chamador já avançou;
  `ProjetoSegundo` avança **pela mutação pública do núcleo** e tem um `__post_init__`, que
  é construção e não mutação;
- **um adaptador** (`infra/persistencia/repositorio_projetos.py`) em que todo `salvar_*`
  anota o agregado que recebe e passa pela trava (`_gravar_projeto`).

As duas raízes existem porque o portão exige ao menos duas: um denominador de um só não
distingue "todas em dia" de "a única que existe está em dia".

Não é código executável nem cópia do serviço: o portão não importa nem roda nada, e o
fixture existe para que as sabotagens o derrubem em terreno controlado. As cinco estão em
`scripts/tests/run-sabotagem.sh`, quatro por direção do defeito — mutação de estado próprio
sem avanço de versão (o defeito da ARA em pessoa: marcar UDE, registrar parecer e mudar
status para `validado` sem `_avancar`), escrita de agregado sem a trava, raiz registrada
sem caminho de escrita, e caminho de escrita novo para um agregado fora do registro.

Base 100% sintética (ADR 0006): nenhum nome, enunciado de trabalho ou data de pessoa.
Decisão que criou este fixture: `docs/adr/0016-versao-do-agregado-como-portao-derivado-do-registro.md`.
