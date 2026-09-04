# Veredito — portoes-vs-irma

> Julgamento **às cegas** por crítico independente em contexto fresco: ele não
> sabia qual documento era de quem, e foi instruído a escolher A ou B sem empate.
> Rodada: rodada 2 — fechamento do ciclo.
> Barra (documento B): portões próprios da irmã em scripts/.
> **Transcrição literal do que o crítico devolveu** — não editada, não resumida,
> não suavizada, inclusive onde reprova o nosso lado.

- **Escolha**: documento **A** — nosso documento

## Por que

A (toc-federada) vence porque é o único conjunto que PROVA que reprova, e a prova roda sem dependência externa. Executei tudo:

CONJUNTO A — códigos de saída colados:
  check-caminhos EXIT=0 · "arquivos varridos: 76 · caminhos conferidos: 701 · isentos declarados: 138 · entregas futuras declaradas: 70 · moldes ignorados: 13"
  check-adrs-sucessao EXIT=0 · "ADRs examinados: 8 · linhas de tabela no índice: 9 · linhas em docs/records/decisoes.jsonl: 8 · verificações executadas: 32"
  check-rounds EXIT=0 · "rounds examinados: 11 · conferências de campo: 77 · arestas de dependência: 15 · ciclos encontrados: 0 · defeitos medidos: 12 · alocados: 10 · declarados sem round: 2"
  check-specs EXIT=0 · "verificações: artefatos 48 · seções e status 185 · tipos de requisito 71 · linhas de Constitution Check 204 · tokens ART 60 · tokens TAIL 48 · specs pontuadas 12 = 628" · "sinais medidos ao todo: 166"
  check-vazamento EXIT=0 · "arquivos varridos: 195 · linhas varridas: 51485 · registros JSON inspecionados: 2557 · sinais aplicados: 3 · campos de pessoa vigiados: 21"
  scripts/tests/run-sabotagem.sh EXIT=0 · "portões cobertos: 5 · bases válidas aceitas: 5/5 · sabotagens declaradas: 27 · reprovadas pelo motivo certo: 27/27"
  scripts/evidencia.sh EXIT=0 · "Portões executados: 6 · verdes: 6 · vermelhos: 0"

CONJUNTO B — códigos de saída colados:
  check-caminhos EXIT=0 · "arquivos varridos: 63 · caminhos conferidos: 280 · isentos declarados: 66 · moldes ignorados: 6"
  check-adrs EXIT=0 · "ADRs examinados: 19 · relações de sucessão conferidas: 3"
  check-rounds EXIT=0 · "rounds lidos: 5 · defeitos lidos de visao.md §6: 17 · alocados: 16 · não-corrigidos com motivo: 1 · duplicados: 0"
  scripts/evidencia.sh EXIT=1 (8 aptidões; 7 verdes, 1 vermelha — testar-prototipo.mjs, ERR_MODULE_NOT_FOUND: playwright)
  node scripts/check-manifesto.mjs EXIT=0 · "⊘ `ajv` e `ajv-formats` não estão instalados. **Nada examinado.**"

Medem o que importa ou o que é fácil? Os dois medem a coisa certa (caminho entre crases, par de sucessão, campos de round) e os dois declaram o denominador (R2) — nisso empatam bem. A diferença é a segunda lei: reprovar. A tem 27 mutações sobre 5 portões, cada uma exigindo o TRECHO de motivo na saída (não basta "saiu ≠ 0"), rodando sobre cópia em mktemp, com zero dependência de rede, node ou repositório vizinho. B tem sabotagem em UM lugar só (check-manifesto.mjs, 9 mutações de schema) e ela é inerte neste ambiente: saiu 0 dizendo "Nada examinado". Os três portões próprios de B — caminhos, adrs, rounds — nunca foram vistos reprovando por um teste versionado; o próprio comentário de check-adrs.sh:44-48 confessa que o bug do `[:1]` foi achado "por revisão de código, não por execução, porque nenhum caso de teste exercitava sucessão múltipla". É a admissão da lacuna, e ela continua aberta.

Confirmei sabotando os dois lados com a MESMA mutação (prosa citando "Superseded by" em vez da declaração real no Status): B saiu VERDE, A saiu VERMELHO com a mensagem certa. Detalhe em "defeitos_factuais".

Honestidade: os dois são honestos acima da média. B tem o melhor cabeçalho de todo o material — check-rounds.sh:8-19 lista os SEIS buracos que a revisão independente derrubou, e o portão imprime "NÃO verificado aqui: ... isso é julgamento". A responde com "O que este portão NÃO mede" em três portões e com o rodapé de evidencia.sh: "Estes números dizem que os portões rodaram, não que sabem reprovar" — que é a frase mais honesta dos dois conjuntos, porque separa "rodou" de "sabe reprovar" e aponta para onde a segunda prova mora.

Utilidade para quem herda: A traz o esqueleto reutilizável (scripts/tests/sabotagem/<portão>/ com base válida + tabela de mutação com motivo exigido) que qualquer projeto novo copia e enche. B traz portões bons e nenhum arnês para provar que eles reprovam. Um projeto novo prefere herdar A: pega os mesmos portões (a linhagem é a mesma, A é a segunda geração deles), mais rígidos (4 invariantes por ADR contra 3, par de sucessão conferido POR NÚMERO nos dois sentidos, FUTUROS separado de ISENTOS, PADRAO_DIR para citação de diretório), mais um portão que B não tem (check-vazamento, com 3 sinais e 4 sabotagens) — e, sobretudo, a prova executável de que cada um deles reprova.

## A maior lacuna restante

A maior lacuna é do vencedor, e é de coerência entre o que ele diz e o que faz: /home/user/toc-federada/scripts/evidencia.sh:2 declara em inglês "runs every gate of this project and prints the evidence block", mas a lista PORTOES (linhas 34-41) tem SEIS entradas e omite scripts/check-vazamento.sh — o portão de privacidade, que é a invariante mais consequente do projeto (é o que sustenta a regra "base sintética desde o dia 1" e a possibilidade de o repositório ser aberto). Rodei: `grep -c "check-vazamento" scripts/evidencia.sh` devolve 0. O bloco que vai para o qa-report anuncia "Portões executados: 6 · verdes: 6 · vermelhos: 0" enquanto existem 7 portões próprios em disco (o commit mais recente, 00c576e, é justamente "o critério de vazamento passa a medir vazamento, e prova que reprova" — o portão foi endurecido e não foi ligado ao agregador). É exatamente o defeito da família R2 que o projeto herdou da irmã: verde cujo denominador esconde o que não foi olhado. Correção de uma linha, mas até lá quem lê o qa-report supõe que a privacidade foi conferida no fechamento, e não foi.

Do lado de B a maior lacuna é estrutural e mais cara: nenhum dos três portões próprios tem sabotagem versionada, e o repositório que tem dado real de pessoa não tem portão executável de vazamento algum (`grep -rln "vazamento|sintétic|publicavel" scripts/` só casa uma isenção dentro de check-caminhos.sh; scripts/check-publicavel.sh está declarado como entregável futuro e não existe). A regra vive no aviso em prosa do CLAUDE.md, sem função de aptidão.

## Defeitos factuais apontados

- B · GRAVE, reproduzido: /home/user/gestaodeprioridades/scripts/check-adrs.sh:62 satisfaz a reciprocidade com a mera STRING 'Superseded by' em qualquer lugar do arquivo (`if "Superseded by" not in open(outro[0], encoding="utf-8").read():`). Copiei docs/ + o script para um diretório temporário (base: EXIT=0, 'ADRs examinados: 19 · relações de sucessão conferidas: 3'), troquei em docs/adr/0014-...md:3 a linha `- **Status**: **Decidido.** **Superseded by [ADR 0016](...)**` por `- **Status**: Aceita` mais uma linha de PROSA contendo as palavras 'Superseded by'. Resultado: o portão saiu VERDE, EXIT=0, imprimindo 'nenhuma sucessão é unilateral' — com um ADR sucedido cujo status voltou a ser 'Aceita'. É literalmente o cenário que originou a regra R5 (dois ADRs contraditórios os dois 'Aceita'). O mesmo ataque contra /home/user/toc-federada/scripts/check-adrs-sucessao.sh saiu 1: 'ADR 0002 sucede o ADR 0001, e 0001-decisao-base.md não declara "Superseded by" nomeando 0002' — A lê a declaração só na linha de Status e exige que o SUCESSOR seja nomeado.
- B · GRAVE: a única prova de sabotagem do conjunto (scripts/check-manifesto.mjs, 9 mutações) não roda e sai VERDE. Executado: `node scripts/check-manifesto.mjs` → '⊘ `ajv` e `ajv-formats` não estão instalados. **Nada examinado.**' EXIT=0. Mesmo apontando APH_SCHEMAS para /home/user/protocolos/padrao/schemas (que EXISTE, com federacao-manifesto.schema.json), o resultado é o mesmo, porque falta a dependência node. Ou seja: a evidência de que B reprova alguma coisa vale 0/9 neste ambiente, e evidencia.sh a exibe como 'manifesto (Anexo B) código 0 · Nada examinado' — verde sobre nada. É verbalmente honesto (diz que não examinou), mas em CI é um portão que não pode reprovar.
- B · o agregador não reproduz: `bash scripts/evidencia.sh` saiu 1 aqui, por Error [ERR_MODULE_NOT_FOUND]: Cannot find package 'playwright' imported from /home/user/gestaodeprioridades/scripts/testar-prototipo.mjs. O script trata o vermelho corretamente ('✗ pelo menos uma aptidão reprovou — o bloco acima NÃO pode ser colado como verde'), o que é bom comportamento; mas a evidência de fechamento do projeto depende de um navegador instalado. O de A saiu 0 sem nenhuma dependência além de bash/python3.
- A · o portão de vazamento está fora do agregador: scripts/evidencia.sh:2 afirma 'runs every gate of this project'; a lista PORTOES (34-41) tem 6 entradas e não inclui scripts/check-vazamento.sh, que existe, roda e sai 0 sobre 195 arquivos / 51485 linhas / 2557 registros JSON. `grep -c "check-vazamento" scripts/evidencia.sh` = 0. O cabeçalho contradiz a lista, e o bloco gerado diz 'Portões executados: 6' sem dizer que o sétimo ficou de fora.
- A · ponto cego na própria regra R4, que B não tem: check-caminhos.sh define RAIZES = ('docs','specs','mensagens') e NÃO varre scripts/ — a versão de B varre ('docs','specs','mensagens','scripts'). Consequência concreta e verificada: /home/user/toc-federada/scripts/README.md:31 cita `plugin/maestro/` entre crases e `ls /home/user/toc-federada/plugin` responde 'No such file or directory'. O padrão PADRAO_DIR de A pegaria esse caminho — o portão só não olha para o arquivo. É o mesmo defeito de classe que a R4 existe para fechar, dentro do repositório que escreveu a regra.
- A · o verde de check-caminhos.sh cobre 70 'entregas futuras declaradas', isto é, 70 caminhos citados que NÃO existem, isentados por uma lista de caminhos exatos (FUTUROS) — mais 138 isentos. É declarado na saída, e a lista é por caminho exato com o ciclo que cria cada um (o que impede que um typo seja engolido), então não é tapete; mas o denominador honesto do portão é 701 conferidos de 909 caminhos vistos, e quem lê 'todo caminho citado entre crases existe' precisa ler a linha de cima para saber disso.
- A · em dados reais a reciprocidade de sucessão nunca foi exercitada: a saída traz 'sucessões declaradas: 0 · sucedidos declarados: 0'. Não é defeito do portão (as 6 sabotagens de adrs-sucessao cobrem esse caminho de código, e reproduzi uma delas à mão), mas é o limite honesto do verde: dos 32 checks executados, nenhum tocou o par de sucessão do repositório de verdade.
