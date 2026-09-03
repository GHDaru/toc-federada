# ADR 0006 — Base sintética desde o dia 1: nenhum dado real de pessoa em fixture, captura, spec ou exemplo

- **Status**: Aceita
- **Data**: 2026-09-03 · **Ciclo**: 001
- **Decisor**: Product Steward (a contrapartida — poder abrir o repositório — é decisão
  externa e de longo raio, fora do alcance da R3)
- **Sucede**: nenhum
- **Princípios tocados**: **P7** — o princípio fala de segredo técnico (chave,
  credencial); este ADR (Architecture Decision Record, registro de decisão arquitetural)
  estende o mesmo espírito ao dado pessoal: o que não pode vazar não entra no artefato.
  Nenhum princípio é emendado.

## Contexto

A irmã `gestaodeprioridades` nasceu com a base real do Product Steward e paga por isso até
hoje. Medido no repositório dela (contagens apenas — nenhum dado copiado, e é este ADR
que explica por quê):

```text
$ python3 - <<'EOF'
import json
d = json.load(open('/home/user/gestaodeprioridades/prototipo/dados/fixture.json'))
print('tarefas:', len(d['tarefas']))
print('valores distintos em responsavel:', len({t.get('responsavel') for t in d['tarefas']}))
EOF
tarefas: 114
valores distintos em responsavel: 6
$ ls /home/user/gestaodeprioridades/docs/jornadas/capturas/ | wc -l
21
```

**114 tarefas com o enunciado real do trabalho, 6 valores distintos de responsável e 21
capturas de tela** exibindo tudo isso 🟢. As consequências lá são estruturais: o
repositório é **obrigatoriamente privado** (aviso no topo do
`gestaodeprioridades/CLAUDE.md` 🟢), abrir exige trocar a base e regerar todas as capturas
(ADR 0015 de lá), e foi preciso um ADR adicional só para garantir que **o deploy** não
exponha a base (ADR 0019 de lá: *"o que vai ao ar usa base sintética, e isso é
pré-condição de deploy"*). A dívida nasceu no primeiro fixture e nunca mais saiu.

Esta aplicação parte do zero: não existe fixture ainda, e o dado que os processos de
pensamento manipulam — Efeitos Indesejáveis (UDEs), conflitos, premissas — é ainda mais
sensível que uma lista de tarefas: descreve problemas organizacionais e comportamento de
pessoas nomeadas.

## Decisão

1. **Nenhum dado real de pessoa entra neste repositório** — nem nome, nem enunciado de
   trabalho, nem data de desempenho, nem narrativa de conflito real — em fixture, captura
   de tela, spec, exemplo, teste ou documentação. A regra vale para dados da irmã, da
   linhagem TOC-Builder e de qualquer uso real da aplicação.
2. **Toda base de exemplo é sintética e declaradamente fictícia**: personas de papel
   ("Facilitadora TOC", "Coordenação de Operações"), organizações inventadas
   ("Instituição Horizonte") e narrativas construídas para exercitar o domínio.
3. **A base sintética é gerada com assimetrias deliberadas** — empates, campos ausentes,
   árvores malformadas — porque o valor de teste de uma base real está nas suas
   patologias, e uma sintética ingênua não as tem (é a consequência negativa nº 1, e a
   mitigação mora aqui).
4. **Isto é regra, não estado**: quem colar um dado real reverte a possibilidade de
   repositório aberto inteira. O aviso vive no `CLAUDE.md` (o arquivo que todo agente lê
   primeiro), e toda spec com fixture ou captura declara a origem sintética.

## Alternativas consideradas — descartadas com número

- **Usar a base real da irmã como fixture inicial.** Descartada: são **114 tarefas** com
  enunciado real e **6 responsáveis** (medição acima) — o mesmo ato tornaria este
  repositório obrigatoriamente privado no dia 1, como lá, e violaria a regra de
  privacidade que o próprio `CLAUDE.md` da irmã impõe a quem a lê.
- **Começar com dado real e anonimizar antes de abrir.** Descartada: é o caminho que a
  irmã tomou sem escolher, e o custo está medido — **21 capturas** a regerar, um ADR de
  triagem (0015 de lá) e um ADR de pré-condição de deploy (0019 de lá) só para conter o
  vazamento. Anonimizar depois é reescrever história em todo artefato que tocou o dado;
  não deixar entrar custa zero.
- **Dado real cifrado/mascarado no repositório.** Descartada: máscara em dado de texto
  livre (enunciado de UDE, narrativa de conflito) é reidentificável por contexto, e a
  captura de tela — que o P6 obriga a gerar — exibiria o dado decifrado de qualquer
  forma. As 21 capturas da irmã são exatamente essa superfície.

## Consequências

- (+) O repositório **pode ser aberto** sem triagem retroativa — a dívida do ADR 0015 da
  irmã não existe aqui e não pode nascer.
- (+) Capturas, jornadas e specs circulam livremente (revisor externo, site de produto,
  handoff) sem lista de quem pode ver.
- (−) **Base sintética não tem as patologias de base real** — os empates acidentais, os
  campos preenchidos errado, o vocabulário torto de quem escreve UDE de verdade. O risco
  é validar o domínio contra dados comportados. Mitigação na decisão 3 (assimetrias
  deliberadas), que custa esforço de geração a cada fixture.
- (−) A regra **não tem portão executável**: nenhum script distingue nome real de nome
  fictício. Fica como as regras da irmã que dependem de leitura — declarada no arquivo
  que todo agente lê primeiro, verificada por revisão humana. 🔴 Lacuna assumida, risco
  médio; um verificador léxico (lista de bloqueio com os nomes da base da irmã) pode
  nascer por decisão futura.

## O que este ADR NÃO decide

- **Se o repositório será de fato aberto** — este ADR remove o impedimento; abrir é
  decisão do Product Steward, externa e à parte.
- O conteúdo da base sintética (quantos projetos, quais narrativas) — specs dos ciclos
  002 e 004.
- Como a aplicação em produção tratará dados reais dos usuários (retenção, isolamento por
  tenant, exportação) — matéria das specs de M8 e M7.

## Registro

- `CLAUDE.md` — o aviso "a base é sintética desde o dia 1", no arquivo lido primeiro
- `docs/governance/constitution.md` — P7, cujo espírito este ADR estende
- `/home/user/gestaodeprioridades/docs/adr/0015-a-base-real-nas-capturas.md` e
  `/home/user/gestaodeprioridades/docs/adr/0019-o-que-vai-ao-ar-usa-base-sintetica.md` —
  o custo medido de não ter esta regra
