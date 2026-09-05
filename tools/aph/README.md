# `tools/aph` — o ambiente para rodar a suíte de conformidade sem escrever fora daqui

> Siglas, uma vez: **APH** — Aplicação ↔ Harness (o padrão da fronteira, `GHDaru/protocolos`)
> · **ESM** — *ECMAScript Modules* · **JSON** — *JavaScript Object Notation*.

A suíte de conformidade do **Nível 1 (Observador)** vive em `GHDaru/protocolos`, que para
este projeto é **somente leitura** (P1 da constituição). Ela precisa de `ajv` e
`ajv-formats`, e o jeito documentado de obtê-las é `npm install` **dentro** do repositório
dela — o que seria escrever lá.

O arranjo deste diretório resolve isso sem tocar em nada de fora:

| Item | O que é |
|---|---|
| `conformidade` | símbolico para `protocolos/conformidade` — a suíte **original**, não uma cópia |
| `padrao` | símbolico para `protocolos/padrao` — os schemas normativos que a suíte lê |
| `package.json` + `node_modules/` | as duas dependências, **nossas**, versionadas só como declaração |

A execução exige duas bandeiras do Node:

```bash
node --preserve-symlinks --preserve-symlinks-main conformidade/suite.mjs http://localhost:8123
```

Sem `--preserve-symlinks`, o Node resolve o **caminho real** do módulo e volta a procurar
`node_modules` dentro de `protocolos` — onde ele não existe. Com as bandeiras, a resolução
acontece por este diretório, e o `../padrao/schemas` que a suíte lê por caminho relativo
cai no símbolico `padrao` ao lado.

Quem roda isto por você é o portão [`../../scripts/check-conformidade-aph.sh`](../../scripts/check-conformidade-aph.sh),
que sobe o serviço, espera o `/saude` responder e devolve o veredito da suíte com o código
de saída dela.

**Nada aqui é cópia da norma.** Os dois símbolicos apontam para o original; se `protocolos`
mudar, a próxima execução já mede contra a versão nova — que é exatamente o que se quer de
um instrumento de conformidade. A fricção está relatada em
[`../../mensagens/004-para-protocolos-rodar-a-suite-sem-escrever-no-repo.md`](../../mensagens/004-para-protocolos-rodar-a-suite-sem-escrever-no-repo.md).

## Montar do zero

```bash
cd tools/aph
ln -sfn /caminho/para/protocolos/conformidade conformidade
ln -sfn /caminho/para/protocolos/padrao       padrao
npm install
```
