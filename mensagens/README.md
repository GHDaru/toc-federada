# Mensagens para outros repositórios

O princípio **P1** da constituição do projeto
([`docs/governance/constitution.md`](../docs/governance/constitution.md)) proíbe escrever
fora de `GHDaru/toc-federada`. Encontrada uma lacuna em `maestro`, `protocolos`, `ghdaru`
ou `gestaodeprioridades`, a regra é **relatar e parar**.

Relatar em conversa não basta: a conversa se perde, e o achado morre com o contexto do
agente. Esta pasta é onde o relato vira **artefato versionado** — endereçado, datado,
verificável por caminho de arquivo, e pronto para o humano levar ao repositório de
destino.

## Convenção de nome

```
NNN-para-<repositório>-<breve-descrição>.md
```

- `NNN` — sequencial de três dígitos, único nesta pasta, nunca reaproveitado;
- `<repositório>` — o destino: `maestro`, `protocolos`, `ghdaru`, `gestaodeprioridades`;
- `<breve-descrição>` — kebab-case, o assunto em três ou quatro palavras.

## O que uma mensagem deve conter

1. **Destino e data**, mais o commit exato do repositório de destino que foi lido — um
   achado sem essa âncora envelhece sem avisar.
2. **Evidência por caminho e linha.** Nunca "parece que"; sempre `arquivo:linha` e o que
   se lê ali (regra R1: executado, com o que voltou colado).
3. **Consequência**: o que quebra, para quem, quando.
4. **Sugestão**, quando houver — separada do achado, para que quem recebe possa aceitar o
   diagnóstico e recusar o remédio.
5. **Estado**: aberta · respondida · resolvida no destino · retirada.

## Como elas chegam ao destino — e não é por cópia

A convenção foi estabelecida pela irmã `gestaodeprioridades` e conferida na prática por
ela: os repositórios de destino **não têm caixa de entrada**. A mensagem nasce **aqui**,
que é onde o artefato versionado vive; o que atravessa a fronteira é o **aviso** de que
ela existe — issue no repositório de destino, aberta **com aprovação explícita do Product
Steward** (P1, caso a caso), ou leitura direta pelo time de lá, que cita a mensagem por
caminho. Nunca se copia o arquivo para o destino: duplicar o artefato cria duas verdades
e nenhum dono.

## Índice

| Nº | Destino | Assunto | Estado |
|---|---|---|---|
| [001](001-para-daruskills-defeitos-do-gerador-de-site.md) | `GHDaru/daruskills` | sete achados no gerador `spec-to-code-docs` | aberta |
| [002](002-para-maestro-pisos-absolutos-de-ciclo.md) | `GHDaru/maestro` | pisos de retroatividade absolutos reprovam repositório recém-instalado | aberta |
| [003](003-para-ghdaru-o-que-falta-para-embarcar-a-toc.md) | `GHDaru/ghdaru` | o que falta no lado hospedeiro para a `toc-federada` embarcar (sete achados, um bloqueio da irmã retirado) | aberta |
| [004](004-para-protocolos-rodar-a-suite-sem-escrever-no-repo.md) | `GHDaru/protocolos` | a suíte de conformidade não roda a partir de um clone somente-leitura | aberta |
| [005](005-para-protocolos-codigo-de-conflito-de-versao-no-a7.md) | `GHDaru/protocolos` | o registro mínimo do §A.7 não tem código para conflito de versão de agregado | aberta |
| [006](006-para-maestro-colchete-anula-a-razao-do-artefato.md) | `GHDaru/maestro` | um `[` no texto faz o `check-conformance.sh` chamar de "sem razão" 401 caracteres de razão | aberta |

> Toda mensagem nova entra no fim da tabela, com o próximo número livre. O estado muda
> conforme o destino responde: aberta → respondida → resolvida, ou retirada.
