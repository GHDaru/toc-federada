# 007 — para `GHDaru/protocolos`: o `ghd.handshake` não carrega idioma, e a aplicação embarcada não tem como saber em que língua abrir

> Siglas deste documento: **APH** — Aplicação ↔ Harness (o padrão da fronteira) · **TOC**
> — Teoria das Restrições · **i18n** — internacionalização · **UI** — interface de usuário
> · **ADR** — *Architecture Decision Record* (Registro de Decisão Arquitetural). Da
> constituição deste projeto: **P1** — fronteira de escrita única (relatar e parar) ·
> **P2** — federação por contrato · **R1** — verifique antes de afirmar.

- **Destino**: `GHDaru/protocolos` — a **norma** (Anexo B, Federação). Com cópia de
  interesse para `GHDaru/ghdaru`, que é quem emite o `ghd.handshake` hoje.
- **Commit lido**: `04eca6d4a267358be2e2a583f8ceef22deb137f5` (2026-08-14). Clone em
  `/home/user/protocolos`, **somente leitura** (P1).
- **Somas de verificação dos arquivos citados** (`md5sum`, executado em 2026-09-06):

  ```text
  416849a770fdd291fbcdbfbe3eb8550b  padrao/anexo-b-federacao.md
  c1983c90318ebbe79cf89543f8448c95  padrao/schemas/federacao-manifesto.schema.json
  ```

- **Origem do achado**: execução do épico E8.3 (internacionalização) da spec 011 da
  `toc-federada`, que declarou a lacuna **L-02** antes de encontrá-la: *"o idioma
  declarado pelo embarque depende de o hospedeiro enviá-lo no envelope `ghd.*`; a spec 003
  não o inclui entre os quatro parâmetros de admissão — a lacuna vira mensagem ao
  hospedeiro por `mensagens/NNN` (P1: relatar e parar)"*.
- **Estado**: **aberta**.

## O achado

O `payload` do `ghd.handshake` está fixado na tabela do §B.3 do Anexo B:

> `padrao/anexo-b-federacao.md:71`
>
> ```text
> | `ghd.handshake` | hospedeiro → app | `{ token, tenant: {id, name}, capabilities[], theme: {tokens} }` | ✅ |
> ```

Quatro campos, e **nenhum deles é o idioma**. O §B.4.3 (linha 97) cuida do tema
("tokens de tema, quando houver, chegam pelo `ghd.handshake` e são parciais por desenho"),
e o §B.4.2 (linha 95) lista o que o hospedeiro publica por aplicação admitida — também sem
idioma. A busca no schema do manifesto não devolve nada:

```text
$ grep -n "locale\|language\|idioma" padrao/schemas/federacao-manifesto.schema.json
$ echo $?
1
```

Ou seja: **a norma diz como o hospedeiro passa a aparência (tema) e não diz como ele passa
a língua.** As duas são exatamente o mesmo tipo de coisa — preferência de apresentação que
pertence ao contexto do embarque e não à aplicação.

## A consequência, e para quem

Uma aplicação embarcada tem três saídas, e as três são ruins:

1. **Abrir sempre na língua-fonte dela.** A pessoa está numa plataforma em inglês, clica
   numa ferramenta e ela abre em português. É a experiência que o §B.8.1 evita para
   navegação ("dois menus na mesma janela é defeito de composição") e que aqui reaparece
   como duas línguas na mesma janela.
2. **Ler o idioma do navegador.** Contradiz o modelo do anexo, em que o **inquilino** é a
   autoridade sobre a apresentação (é o que o tema já estabelece): duas pessoas do mesmo
   inquilino veriam a mesma ferramenta em línguas diferentes por causa da configuração do
   sistema operacional delas.
3. **Inventar um campo no `payload`.** É o que a `toc-federada` faz hoje — e é por isso
   que esta mensagem existe. Nosso lado lê `payload.locale` **se ele vier**, trata valor
   desconhecido como ausência e cai para a língua-fonte com registro em log estruturado
   (`apps/web/src/i18n/index.tsx`, `resolverIdiomaEfetivo`). Funciona, e **é combinação
   privada**: exatamente a classe de coisa que o §B.1 do anexo existe para impedir, porque
   a segunda aplicação federada vai inventar `payload.lang` ou `payload.language`, e aí
   são dois protocolos.

O custo assimétrico é o de sempre: enquanto o campo não está na norma, cada aplicação paga
uma tradução privada; depois que estiver, o hospedeiro paga um campo a mais numa mensagem
que ele já monta.

## Sugestão (separada do achado, para poder ser recusada)

Acrescentar ao `payload` do `ghd.handshake` um campo **opcional**:

```text
| `ghd.handshake` | hospedeiro → app | `{ token, tenant: {id, name}, capabilities[], theme: {tokens}, locale? }` |
```

com uma cláusula no mesmo espírito do §B.4.3, que já é o precedente perfeito:

> **B.4.4** O idioma do embarque, quando houver, chega pelo `ghd.handshake` em `locale`,
> como etiqueta BCP 47 (por exemplo `pt-BR`, `en`). Ele é **dado, nunca instrução**: a
> aplicação **DEVE** funcionar sem ele, e **DEVE** tratar valor que ela não fala como
> ausência — caindo para a língua-fonte dela, e não para uma tela em duas línguas. A
> preferência explícita da pessoa, quando a aplicação a guarda, **precede** o valor do
> embarque.

Três notas sobre a forma, e cada uma tem motivo:

- **opcional, não obrigatório** — tornar `locale` obrigatório quebraria hospedeiro que já
  implementou o handshake, e a regra do §B.4.3 para tema já provou que "parcial por
  desenho" funciona;
- **`locale` e não `lang`** — é o nome que o resto do ecossistema usa para o par
  língua+região, e o §B.2 já fixa `snake_case` e inglês nos campos de protocolo;
- **a precedência dita na norma** — sem ela, cada aplicação decide se a escolha da pessoa
  vence o embarque ou o contrário, e a mesma plataforma se comporta de dois jeitos.

## O que a `toc-federada` fez enquanto isso

Nada que dependa da resposta: a resolução do idioma efetivo é **função pura** com a ordem
`preferência da pessoa → idioma do embarque → língua-fonte` e o **motivo** da escolha
anexado ao resultado (spec 011, RF-12 e RF-14). Se o campo entrar na norma com outro nome,
muda-se uma linha de leitura do `payload`; a decisão em si não se move.
