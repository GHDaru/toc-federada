# 004 — para `GHDaru/protocolos`: rodar a suíte de conformidade sem escrever no repositório dela

> Siglas, uma vez: **APH** — Aplicação ↔ Harness (o padrão da fronteira) · **JSON** —
> *JavaScript Object Notation* · **ESM** — *ECMAScript Modules* (o sistema de módulos do
> JavaScript moderno) · **CI** — integração contínua.

- **Destino**: `GHDaru/protocolos`
- **Data**: 2026-09-05
- **Commit lido**: `04eca6d4a267358be2e2a583f8ceef22deb137f5` (2026-08-14 — "Instantaneo
  regravado: a obrigacao (e) do APH-5.9 (spec 040)")
- **Estado**: aberta
- **Quem relata**: `GHDaru/toc-federada`, ciclo de implementação das specs 003 e 006
  (federação APH), depois de rodar a suíte contra o nosso serviço — **11/11, exit 0, sem
  perfil de adaptação**.

## O achado, em uma frase

A suíte de conformidade do Nível 1 é o instrumento certo e ela **não roda a partir de um
clone somente-leitura**: as instruções pedem `npm install` **dentro** de
`conformidade/`, e quem consome a norma tratando `protocolos` como laboratório de leitura
não pode fazer isso.

## Evidência

1. `conformidade/README.md:9-10` — as instruções de uso são literais:

   ```bash
   cd conformidade && npm install
   node suite.mjs https://sua-app.exemplo.com   # exit 0 = apto nos itens verificáveis
   ```

2. `conformidade/package.json:9-12` — as duas dependências que faltam num clone limpo:

   ```json
   "dependencies": {
     "ajv": "^8.20.0",
     "ajv-formats": "^3.0.1"
   }
   ```

3. `conformidade/suite.mjs:33-34` — os imports que exigem essas dependências, e que são
   **ESM com especificador nu** (`import Ajv2020 from "ajv/dist/2020.js"`). Isso importa
   para o remédio: em ESM, `NODE_PATH` **não** é consultado, então "instalar noutro lugar e
   apontar a variável de ambiente" não funciona, ao contrário do que funcionaria com
   `require`.

4. `conformidade/suite.mjs:36` — os schemas são lidos por caminho **relativo ao arquivo**:

   ```js
   const DIR_SCHEMAS = resolve(dirname(fileURLToPath(import.meta.url)), "../padrao/schemas");
   ```

   Ou seja: copiar `suite.mjs` para outro lugar quebra a leitura dos schemas, e é por isso
   que "copiar a suíte" também não é remédio.

5. Não há `conformidade/package-lock.json` no clone lido (verificado: `ls` responde que o
   arquivo não existe). Sem arquivo de trava, a execução de hoje e a de amanhã não são
   necessariamente a mesma — o que enfraquece um instrumento cujo valor inteiro é ser
   reprodutível.

## Consequência

Para **qualquer** aplicação que trate `protocolos` como repositório de consulta — que é o
que a nossa constituição manda (P1: "escreva somente no seu repositório") —, a suíte só
roda depois de um arranjo local. O nosso é este, e está versionado em
[`../tools/aph/package.json`](../tools/aph/package.json):

```
tools/aph/
  conformidade -> /caminho/para/protocolos/conformidade   (símbolico)
  padrao       -> /caminho/para/protocolos/padrao         (símbolico)
  node_modules/                                            (ajv e ajv-formats, nossos)
```

e a execução precisa de duas bandeiras do Node para funcionar:

```bash
node --preserve-symlinks --preserve-symlinks-main conformidade/suite.mjs http://localhost:8123
```

Sem `--preserve-symlinks`, o Node resolve o **caminho real** do módulo, a busca por
`node_modules` volta para dentro de `protocolos`, e o `import` de `ajv` falha. Funciona —
mas é conhecimento que cada adotante vai redescobrir sozinho, e o §7 do próprio padrão
descreve a suíte como o instrumento de quem quer se autodeclarar.

## Sugestões (o diagnóstico acima independe destas)

Em ordem de custo crescente, e qualquer uma resolve:

1. **Publicar `conformidade/package-lock.json`** e uma linha no README dizendo que a
   instalação pode acontecer fora do repositório, com as duas bandeiras acima. É
   documentação; custo quase zero, e tira o passo de redescoberta.
2. **Aceitar `--schemas <dir>` na linha de comando**, com o caminho relativo de hoje como
   valor padrão. Isso desbloqueia a cópia da suíte para fora, que é o remédio mais óbvio
   e hoje o único que não funciona.
3. **Empacotar a suíte** (`npm pack` ou publicação) para o adotante consumi-la como
   dependência. É a forma que elimina o problema de vez, e é a mais cara.

## O que não estamos pedindo

Nada no comportamento dos 11 checks. Rodamos a suíte inteira contra o nosso serviço, ela
exercitou o que promete exercitar e o resultado foi **APTO, 11/11 verificados, 12 itens a
autodeclarar** — inclusive o caminho 🟡 do `snapshot-fechado`, que no nosso caso deu ✅
porque a borda rejeita com `INVALID_CONTEXT`. O instrumento está certo; o que falta é o
degrau de entrada para quem não pode escrever no repositório dele.
