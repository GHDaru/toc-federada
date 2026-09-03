# ADR 0005 — Escopo do domínio v1: processos de pensamento completos + focalização; DBR e contabilidade de ganho ficam fora

- **Status**: Aceita
- **Data**: 2026-09-03 · **Ciclo**: 001
- **Decisor**: agente construtor do ciclo 001, sob a regra R3 (decisão registrada;
  confirmação no gate humano do ciclo 001)
- **Sucede**: nenhum
- **Princípios tocados**: nenhum

## Contexto

Este ADR (Architecture Decision Record, registro de decisão arquitetural) corta o escopo
da primeira versão da aplicação de Teoria das Restrições (TOC). A TOC tem três corpos de
ferramenta: os **processos de pensamento** (árvores lógicas e nuvem de conflito), a
**focalização** (os cinco passos sobre a restrição) e o corpo **operacional/financeiro** —
tambor-pulmão-corda (DBR, *Drum-Buffer-Rope*), gestão de pulmões e contabilidade de ganho
(*throughput accounting*).

A linhagem TOC-Builder — quatro gerações de protótipo frontend mais os repositórios
natimortos — é a evidência do que o produto sempre foi. Medido sobre os nove diretórios,
não lembrado:

```text
$ for d in TOC-Builder TOC-Builder-APP TOC-Builder-V2 tocbuilderv3 \
           toc_backend toc_frontend tocbackend tocfrontend tocmaterials; do
    n=$(grep -rniE 'tambor|drum|pulm[aã]o|buffer|focaliza|throughput' "$d" 2>/dev/null \
        | grep -v node_modules | grep -v 'package-lock' | wc -l); echo "$d: $n"; done
TOC-Builder: 0
TOC-Builder-APP: 0
TOC-Builder-V2: 0
tocbuilderv3: 0
toc_backend: 0
toc_frontend: 0
tocbackend: 0
tocfrontend: 0
tocmaterials: 0
```

**Zero ocorrências** de tambor/drum/pulmão/buffer/throughput em toda a linhagem 🟢 — em
quatro gerações, ninguém pediu nem esboçou o corpo operacional. E o mesmo grep devolve
zero para `focaliza`: **a jornada dos cinco passos de focalização nunca foi implementada**
— não porque foi rejeitada, mas porque nenhuma geração chegou lá. Já a Estratégia &
Táticas (S&T) existe na linhagem — 16 arquivos do `tocbuilderv3` citam `SnT` 🟢:

```text
$ grep -rli 'SnT\|estratégia' tocbuilderv3 | grep -v node_modules | wc -l
16
```

## Decisão

1. **Entram na v1 os processos de pensamento completos**: Árvore da Realidade Atual (ARA)
   com validação formal de Efeitos Indesejáveis (UDEs), Nuvem de Conflito (NC) com
   premissas e injeções, Árvore da Realidade Futura (ARF), Árvore de Pré-Requisitos (APR),
   Árvore de Transição (AT) e Estratégia & Táticas (S&T) — módulos M1–M5 de
   `docs/produto/modulos.md`, incluindo o **encadeamento** entre ferramentas (UDE da ARA
   alimenta a NC; injeção da NC semeia a ARF; a ARF gera obstáculos da APR).
2. **Entra a focalização** (módulo M6): registro da restrição e jornada guiada pelos
   cinco passos (identificar → explorar → subordinar → elevar → recomeçar), costurando as
   ferramentas. É conteúdo **novo** — o grep acima prova que nenhuma geração o teve — e é
   o que transforma um editor de diagramas em uma aplicação de TOC.
3. **Ficam fora da v1**: tambor-pulmão-corda (DBR), gestão de pulmões e contabilidade de
   ganho (throughput accounting). **Zero ocorrências na linhagem** (saída colada acima).
   Entrada futura é decisão nova, por ADR que suceda este.

## Alternativas consideradas — descartadas com número

- **Incluir DBR e contabilidade de ganho na v1.** Descartada: **0 ocorrências em 9
  diretórios** de linhagem (medição acima) — não há demanda demonstrada, não há esboço a
  honrar, e o corpo operacional exige dados de fluxo produtivo (ordens, capacidade,
  ganho por unidade) que nenhum dos oito módulos planejados coleta. Seria escopo inteiro
  novo dentro de um roadmap de 12 ciclos já cheio.
- **Cortar S&T da v1.** Descartada: a ferramenta existe na linhagem — **16 arquivos** do
  `tocbuilderv3` a citam (medição acima) — e cortá-la faria a sucessora nascer menor que
  o protótipo que ela aposenta. Ela fica, com ciclo próprio (010) e volume menor de
  requisitos (M5 é o menor módulo de ferramenta).
- **Cortar a focalização (só as árvores).** Descartada: sem os cinco passos, as seis
  ferramentas são editores desconexos — a focalização é o fio que dá à aplicação o nome
  que ela tem. O custo é limitado: M6 está dimensionado como módulo pequeno (15–25
  requisitos funcionais, um ciclo — 009).

## Consequências

- (+) O corte é defensável por evidência: cada "fora" tem um grep com saída zero colada,
  não uma opinião.
- (+) M6 dá identidade de produto (jornada TOC) em vez de identidade de utilitário
  (desenhador de árvores).
- (−) **Quem procurar a TOC operacional — DBR, pulmões, ganho — não encontra nada na
  v1**, nem um esboço; se um usuário real a pedir, a entrada custa ADR novo, modelagem de
  domínio nova e provavelmente mais de um ciclo. O risco foi aceito com base na linhagem,
  que pode subestimar demanda futura de um público que os protótipos nunca alcançaram.
- (−) O encadeamento entre ferramentas (decisão 1) cria acoplamento entre módulos M2–M4
  que o roadmap paga no ciclo 008 — cortar uma ferramenta depois deste ADR quebra o fio.

## O que este ADR NÃO decide

- Os requisitos de cada ferramenta — specs dos ciclos 004–010, sob a taxonomia do ADR 0004.
- A ordem de entrega dos módulos — `docs/roadmap.md`.
- Os critérios formais de validação de UDE e de suficiência causal — regra de negócio
  (RN-NN) das specs de M2–M4.
- Se DBR entra algum dia — este ADR não proíbe; exige decisão nova com demanda real.

## Registro

- `docs/produto/modulos.md` — M1–M8, o mapa que este corte delimita
- `docs/produto/visao.md` — o produto que o corte serve
- `tocbuilderv3/` e demais diretórios da linhagem — a base da medição (leitura)
