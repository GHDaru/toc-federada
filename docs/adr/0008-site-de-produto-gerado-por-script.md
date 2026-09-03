# ADR 0008 — Site de produto gerado por script versionado, nunca escrito à mão

- **Status**: Aceita
- **Data**: 2026-09-03 · **Ciclo**: 001
- **Decisor**: agente construtor do ciclo 001, sob a regra R3 (decisão registrada;
  confirmação no gate humano do ciclo 001)
- **Sucede**: nenhum
- **Princípios tocados**: **P6** — o site é rastreabilidade viva: uma projeção gerada das
  specs, não uma segunda fonte de verdade. Nenhum princípio é emendado. As regras R1 e R2
  entram de lado: todo número exibido no site é **contado pelo gerador na hora da
  geração**, nunca declarado à mão.

## Contexto

Este ADR (Architecture Decision Record, registro de decisão arquitetural) decide como
nasce o site de documentação de produto — a visão navegável de módulos, requisitos,
roadmap e rastreabilidade que humanos usam para acompanhar a aplicação.

A barra de comparação é o site do projeto ECS, gerado pela skill `spec-to-code-docs`.
Medido:

```text
$ wc -l daruskills/spec-to-code-docs/generate.py daruskills/spec-to-code-docs/render.py
 1162 daruskills/spec-to-code-docs/generate.py
 1482 daruskills/spec-to-code-docs/render.py
 2644 total
$ ls /home/user/ECS/docs/product-site/*.html | wc -l
5
$ wc -l /home/user/ECS/docs/product-site/*.html | tail -1
 2064 total
```

O gerador existente tem **2.644 linhas** de Python e produziu, no ECS, **5 páginas HTML
com 2.064 linhas** 🟢 — índice, módulos, roadmap, progresso e matriz de rastreabilidade.

O método já registrou o que acontece com artefato-índice mantido à mão: o portão
`scripts/check-adr.sh` deste repositório existe porque, no canônico, *"a hand-written
index of machine-readable files ages in silence"* (`scripts/check-adr.sh:11` 🟢 — o
índice de ADRs ficou congelado por sete ciclos exibindo como vigente uma decisão
revertida). Um site de produto escrito à mão é esse mesmo defeito, multiplicado por cada
página.

## Decisão

1. **O site de produto é 100% gerado por script versionado neste repositório.** Nenhuma
   página do site é editada à mão; mudança no site é mudança no gerador ou nas specs que
   ele lê.
2. **O gerador é o `spec-to-code-docs` vendorizado em `tools/product-site/`** 🟡
   PLANEJADO (a vendorização é entrega deste ciclo 001), **com atribuição** à origem
   (`daruskills/spec-to-code-docs`) registrada no diretório vendorizado e em
   `THIRD-PARTY` — verificada a origem, o diretório da skill não carrega arquivo de
   licença próprio (`find daruskills -maxdepth 2 -iname 'license*'` devolve vazio 🟢), e
   confirmar os termos com o Product Steward fica como pendência declarada da
   vendorização.
3. **Adaptado, não usado cru**: o gerador aprende o vocabulário deste corpus — requisitos
   de interface (RI-NN) como tipo próprio, selos 🟢🟡🔴, lacunas L-NN, a taxonomia
   Módulo ⊃ Épico ⊃ Feature ⊃ Story do ADR 0004 e os cabeçalhos verbatim das specs (o
   formato da spec existe para o gerador; o gerador depende dele — a *forcing function*
   do princípio VI do método).
4. **Todo número do site é contado na geração** (R1/R2): totais de requisitos, cobertura
   de fontes, progresso por módulo — o gerador conta e imprime quanto examinou; nada de
   número digitado.
5. **A geração entra no fluxo do ciclo**: mexeu em spec, regera o site no mesmo pull
   request — o mesmo contrato da jornada viva (P6).

## Alternativas consideradas — descartadas com número

- **Escrever o site à mão.** Descartada: a barra do ECS tem **2.064 linhas de HTML em 5
  páginas** (medição acima), e este corpus nasce com 12 specs planejadas — cada mudança
  de requisito exigiria editar as páginas afetadas à mão, e o precedente medido do
  ecossistema é que índice manual **congela em silêncio** (`scripts/check-adr.sh:4-11`
  🟢: sete ciclos exibindo decisão revertida como vigente).
- **Escrever um gerador novo.** Descartada: **2.644 linhas** já escritas, operantes e com
  barra de saída conhecida (o site do ECS) contra reescrever do zero por preferência.
  A adaptação (decisão 3) é o delta que interessa; o motor não é.
- **Referenciar o gerador no lugar de vendorizar** (rodar de `daruskills/`). Descartada:
  `daruskills` é repositório externo — dependência de caminho fora desta fronteira quebra
  o CI de qualquer máquina que não tenha o clone irmão, e a adaptação da decisão 3
  exigiria **escrever lá**, violando o P1. Vendorizar traz o código para dentro da
  fronteira de escrita, com atribuição.

## Consequências

- (+) O site não mente por desatualização: ou reflete as specs, ou a geração falha —
  nunca o meio-termo silencioso.
- (+) Rastreabilidade navegável (spec ↔ requisito ↔ módulo ↔ roadmap) sem manutenção
  manual de links.
- (−) **Vendorizar é adotar 2.644 linhas de código alheio**: correção da origem não chega
  sozinha, e defeito do gerador vira defeito nosso para diagnosticar — o preço de não
  depender de repositório externo.
- (−) O acoplamento forte ao formato de spec corta nos dois sentidos: um construtor que
  mude um cabeçalho verbatim quebra a geração — e o site passa a ser, na prática, um
  portão de formato que ninguém declarou como portão. Fica declarado aqui.

## O que este ADR NÃO decide

- O conteúdo e o design das páginas (navegação, workflow com donos, nota de honestidade)
  — matéria da spec do site neste ciclo 001 e da barra do gauntlet.
- Onde o site é publicado — decisão de deploy, junto com o ADR 0002/ciclo 003.
- A licença final da vendorização — pendência declarada na decisão 2, com dono (Product
  Steward).
- Se o gerador vendorizado será re-sincronizado com a origem — cada re-sincronização é
  decisão nova.

## Registro

- `tools/product-site/` 🟡 PLANEJADO — o gerador vendorizado, com atribuição
- `daruskills/spec-to-code-docs/` — a origem medida (leitura)
- `/home/user/ECS/docs/product-site/` — a barra de comparação medida (leitura)
- `docs/produto/modulos.md` e as specs de `specs/` — os insumos que o gerador lê
