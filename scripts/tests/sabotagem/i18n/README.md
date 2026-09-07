# Base válida do portão de internacionalização

> Siglas: **i18n** — internacionalização · **JSX** — JavaScript XML · **RF** — requisito
> funcional da spec 011.

O que esta base tem, e cada item existe para uma sabotagem poder tirá-lo:

- **dois dicionários em paridade** (`pt.ts` e `en.ts`, 5 chaves cada) — a sabotagem
  remove uma chave da tradução (pendência) ou acrescenta uma chave só na tradução (erro);
- **um componente conforme** (`Barra.tsx`), com todo texto vindo de `t(...)`, mais um
  símbolo solto (`×`) que **não** é texto de gente — se o portão o acusasse, ele estaria
  reprovando o certo;
- **um literal legítimo declarado** (`Rodape.tsx`, o endônimo "Português") com a exceção
  correspondente em `scripts/i18n/excecoes.txt`, com motivo — a sabotagem apaga o motivo;
- **o mecanismo** (`index.tsx`) com a guarda do RF-09 (lança em chave ausente) e a queda
  do RF-10 (língua-fonte + registro) — a sabotagem devolve o `return chave` da linhagem
  (`tocbuilderv3/i18n/I18nProvider.tsx:41`).

A base é mínima de propósito: ela não é a interface do produto, é o **mínimo que o portão
precisa ver para responder certo**.
