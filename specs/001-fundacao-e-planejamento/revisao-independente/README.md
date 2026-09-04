# Revisão independente do ciclo 001 — os vereditos, na íntegra

> Siglas deste documento: **DoD** — *Definition of Done* (definição de pronto);
> **ADR** — *Architecture Decision Record* (registro de decisão arquitetural).

O método exige revisão independente em contexto fresco: **quem executa não verifica**.
No ciclo 001 essa revisão foi um *gauntlet* — cada peça do trabalho posta lado a lado
com a peça equivalente de um projeto de referência, **sem rótulo**, e julgada por um
crítico que não sabia qual documento era de quem e foi obrigado a escolher um, sem
empate. As referências foram o corpus da aplicação irmã `GHDaru/gestaodeprioridades`
e o do `PROJETO_ECS`.

Este diretório existe porque a revisão independente **precisa ser auditável**. Dizer
"venceu 13 de 14" é um placar; sem os vereditos, é só um relato. Aqui estão os
14 textos como o crítico os devolveu — não editados, não resumidos, não suavizados,
inclusive o que nos reprovou e os que apontaram defeito no vencedor.

**Placar: 13 de 14.**

## Rodada 1 — o corpus de planejamento contra a barra

| Peça | Escolha do crítico |
|---|---|
| [visao-vs-visao](visao-vs-visao.md) | **a barra** |
| [spec-modulo-vs-ecs](spec-modulo-vs-ecs.md) | nosso |
| [spec-fronteira-vs-ecs](spec-fronteira-vs-ecs.md) | nosso |
| [plan-vs-plan](plan-vs-plan.md) | nosso |
| [adr-vs-adr](adr-vs-adr.md) | nosso |
| [roadmap-vs-roadmap](roadmap-vs-roadmap.md) | nosso |
| [site-index-vs-ecs](site-index-vs-ecs.md) | nosso |
| [site-rastreabilidade-vs-ecs](site-rastreabilidade-vs-ecs.md) | nosso |
| [site-modulos-e-roadmap](site-modulos-e-roadmap.md) | nosso |
| [claude-md-e-constituicao](claude-md-e-constituicao.md) | nosso |

A derrota é a peça mais útil deste diretório. O crítico achou um bloco de console em
`docs/produto/visao.md` que colava uma saída que o comando ao lado **não produzia** —
violação da regra R1 do próprio projeto — e nomeou a lacuna que decidiu: a visão media
a linhagem e não media o domínio. As duas coisas foram corrigidas, e a segunda gerou
a base sintética de `docs/produto/dados/`.

## Rejulgamento, depois do retrabalho

| Peça | Escolha do crítico |
|---|---|
| [rejulgamento](rejulgamento.md) | nosso |

O crítico do rejulgamento reexecutou os oito blocos de console da visão e todos
reproduziram byte a byte. E, mesmo dando a vitória, apontou que o número central era
**circular**: a base fora escrita por quem escreveu as checagens. Isso gerou o conjunto
de controle, que encontrou um falso negativo real das checagens — o achado mais valioso
do ciclo, e ele veio de uma crítica ao documento vencedor.

## Rodada 2 — o fechamento do ciclo

| Peça | Escolha do crítico |
|---|---|
| [qa-report-vs-irma](qa-report-vs-irma.md) | nosso |
| [dod-vs-irma](dod-vs-irma.md) | nosso |
| [portoes-vs-irma](portoes-vs-irma.md) | nosso |

Aqui a barra foi um ciclo **fechado** da irmã, não um em andamento. As lacunas que estes
três críticos apontaram no nosso lado foram corrigidas no mesmo ciclo: o agregador de
evidência não rodava o portão de privacidade, e a revisão independente não tinha artefato
auditável — que é exatamente o que este diretório passou a ser.

## Como ler um veredito

Cada arquivo traz a escolha, o raciocínio do crítico, a maior lacuna restante e os
defeitos factuais que ele conseguiu provar executando comandos dos dois lados. O
documento **A** é sempre o nosso; o **B**, o da barra.
