# Veredito — rejulgamento

> Julgamento **às cegas** por crítico independente em contexto fresco: ele não
> sabia qual documento era de quem, e foi instruído a escolher A ou B sem empate.
> Rodada: rodada 1 — rejulgamento da visão após retrabalho.
> Barra (documento B): docs/produto/visao.md da irmã (segunda comparação).
> **Transcrição literal do que o crítico devolveu** — não editada, não resumida,
> não suavizada, inclusive onde reprova o nosso lado.

- **Escolha**: documento **A** — nosso documento

## Por que

Vence pelo critério de maior peso — VERIFICABILIDADE — e sem depender de tamanho.

**1) Verificabilidade (peso máximo): A ganha de forma decisiva.** A cola oito blocos `console` com o comando exato e a saída literal. Reexecutei os oito, de /home/user, e os oito reproduzem byte a byte:
- `ls -d TOC-Builder TOC-Builder-APP TOC-Builder-V2 tocbuilderv3` + o laço dos natimortos → exatamente as cinco linhas de visao.md:108-118 (`toc_backend: 1 arquivo(s) [LICENSE]` … `tocmaterials: 0 arquivo(s) []`).
- `grep -n "new GoogleGenAI"` nas quatro gerações → quatro vezes `16:const ai = new GoogleGenAI({ apiKey: process.env.API_KEY });` (visao.md:244-247).
- `md5sum */api_specifications.md` → `ae5b3c3a6d153fb82fa9256e2b45e96a` nas quatro, e `wc -l` = 435 (visao.md:266-269, 278).
- `wc -l mockApiService.ts` → 377 / 473 / 565 / 594 (visao.md:272-275).
- `python3 docs/produto/dados/medir-base.py | grep -E ...` → as seis linhas de visao.md:408-413 idênticas, inclusive `UDEs medidos: 12 · passam nos 8 critérios decidíveis: 3 (U-01, U-02, U-03) · reprovam: 9`.
- `grep -rn "localStorage" tocbuilderv3 | wc -l` → 16, em exatamente os 5 arquivos nomeados em visao.md:345-346.
- `find ... -iname "*test*"` → 0; `grep focaliza|five focusing|cinco passos` → 0; `grep drum|tambor|throughput` → 0; `grep analytics|telemetr|...` → 0; `grep -c araProjectId|sourceUdeId|...` → 0.
- `grep -n "disabled: true"` nos quatro Sidebar → as 16 linhas de visao.md:289-308, com os números de linha certos (45-48, 45-48, 53-56, 55-58).

**B não cola um único comando.** Suas afirmações numéricas são verdadeiras — eu as recalculei com script próprio sobre `prototipo/dados/fixture.json` e todas batem: 13 notas distintas, 106 empates (93,0%), `E=5` em 114/114, `D=3,704` em 112/114, nota máxima 5,37, 2 acima de 5,00, 29 tarefas com 3/3/3, 33 "alta" contra 19 normalizadas, e 16 mudanças de faixa quando se usam os limiares reais do código (`kanban-v0.tsx:86-87`, `v>=4` / `v>=2.5`) — mas quem lê B **não tem como reexecutar nada**: não há comando, nem nome de script dentro de visao.md. Pelo critério declarado ("evidência colada e comando reexecutável vence afirmação declarada"), a diferença é estrutural, não de grau. Confirmei ainda que todas as citações `arquivo:linha` de B são exatas (`:7`, `:21`, `:245`, `:500`, `:521`, `:547`, `:598`, `:630`, `:695`, `:749`, `:822`), e que os caminhos citados por A existem (`modulos.md`, `rounds.md`, `dados/README.md`, `dados/medir-base.py`, `roadmap.md`, `adr/README.md`).

**2) Honestidade: empate técnico.** B tem o gesto mais raro dos dois — publica a própria falsidade em vez de apagá-la, duas vezes ("A redação anterior dizia… **É falso, e a justificativa também**", §2 e §6.1), com a álgebra que a derruba. A responde com estrutura: §8 traz três lacunas com **assunção-enquanto-durar, risco e ciclo de fechamento**, e a L-01 admite que tudo que o documento afirma sobre utilidade é inferência a partir de código, porque a instrumentação medida é zero. A também declara que 4 das 11 características de UDE não são decidíveis por função alguma — conferi a lista em `constants.ts:123-133` e as quatro apontadas (1, 4, 5, 7) são de fato as de julgamento.

**3) Densidade de decisão: B ganha o melhor exemplo isolado.** O trecho do ADR 0012 em B (§6.17) descarta três alternativas por número medido — desempate declarado resolve 48 de 106, recalibrar λ resolve 2 em 2000 valores varridos, pesos diferentes resolvem 3 a 6 — e conferi contra `docs/adr/0012-criterio-de-desempate.md:56,72,75`: os números estão lá. A não tem nada tão afiado numa só decisão; compensa em quantidade (cada D-NN com destino declarado, o corte de escopo do ADR 0005 ancorado em duas contagens zero, o 3-de-12 virando critério de aceite).

**4) Utilidade: A por pouco.** A converte a medição em critério de aceite executável antes de existir produto ("o mesmo conjunto de doze UDEs… tem de devolver os mesmos 9 reprovados com o mesmo motivo"). B entrega a linha exata a corrigir, o que também é útil, mas seu critério de pronto é menos operável.

**5) Clareza: B por pouco.** B flui melhor e entrega uma leitura completa em 277 linhas. A tem 495 e carrega ruído visual: 44 selos 🟢 e um bloco final que conta os próprios emojis — ver "maior lacuna".

Somando pelos pesos declarados: A vence o critério 1 com folga, empata o 2, perde o 3 por pouco, ganha o 4 por pouco e perde o 5 por pouco. Vitória de A. A extensão maior de A não é gordura injustificada — cobre nove repositórios, doze defeitos medidos e uma base sintética própria —, mas também não é ela que decide: o que decide é que oito afirmações de A eu pude derrubar com um comando e não derrubei, enquanto as de B tive de reconstruir por fora do documento.

## A maior lacuna restante

A circularidade da base que sustenta o número mais importante de A — e que A declara pela metade. O critério de aceite do módulo M2 é "3 dos 12 UDEs passam" (visao.md:70-73, 412), medido pelo `medir-base.py` sobre a base sintética da Instituição Horizonte. Mas essa base foi **escrita pelo mesmo autor que escreveu as checagens**, e escrita explicitamente "com as patologias típicas de oficina" que as checagens procuram (visao.md:403-404). Ou seja: o 3-de-12 não é uma medição do mundo, é uma medição do acordo do autor consigo mesmo — a linha `divergências entre o esperado na base e o medido: 0` prova exatamente isso, que o esperado e o medido coincidem, o que é tautologia e não evidência. A L-03 chega perto ("escrita por nós, não colhida de oficina") mas assume o risco errado: declara incerteza sobre a *representatividade* da distribuição, quando o problema é que uma base autoral **não pode falsear** os critérios que a geraram. O documento B, apesar de todos os seus outros défices, mediu contra uma base que não escreveu — e por isso seus achados (as 8 tarefas invisíveis, os 13 degraus para 114 tarefas) o surpreenderam, que é o sinal de que a medição estava fazendo trabalho.

Duas lacunas menores, na mesma família: (a) o bloco `console` final de A (visao.md:484-489) conta os próprios emojis do documento — verifica a decoração do texto, não um fato sobre o mundo; é cerimônia com aparência de evidência, e ocupa o lugar de nobreza (a última palavra do documento) que deveria ser de uma medição real; (b) A promete em visao.md:236-237 que "cada D-NN pertence a exatamente um round" mas não roda nenhum portão que verifique essa cobertura — é a única afirmação estrutural do documento sem comando atrás dela, justo num documento cuja tese é que afirmação sem comando não vale.

## Defeitos factuais apontados

- NENHUM defeito de reprodução encontrado em nenhum dos dois documentos. Executei os 8 blocos console de A e recalculei por script próprio as 11 afirmações numéricas de B; todos reproduzem. Os itens abaixo são imprecisões menores, registradas para rastreabilidade, e NÃO são falhas de reprodução.
- MENOR — /home/user/toc-federada/docs/produto/visao.md:220 e :62: A cita `tocbuilderv3/constants.ts:122-133` para 'as onze características' e `:120-137` para 'definição e critérios'. Conferido com `grep -n "" constants.ts`: a linha 122 é o cabeçalho 'Características de um UDE bem articulado:' e os onze itens ocupam 123-133; o intervalo 120-137 estende-se até dentro do bloco seguinte ('Tipos de UDEs:', linha 135). O conteúdo afirmado está correto — os onze itens existem e os quatro apontados como indecidíveis (1, 4, 5, 7) são exatamente os das linhas 123, 126, 127 e 129 —, apenas o recorte inclui uma linha de cabeçalho e transborda duas linhas.
- MENOR — /home/user/toc-federada/docs/produto/visao.md:258: A descreve os perfis da linhagem como 'USER/ADMINISTRATOR/SUPERUSER, tocbuilderv3/types.ts:234'. A linha 234 é `export type UserProfileName = 'GUEST' | 'USER' | 'ADMINISTRATOR' | 'SUPERUSER';` — são quatro valores, e o 'GUEST' fica de fora da enumeração do texto. Não altera o argumento (identidade simulada), mas a citação é parcial.
- MENOR — /home/user/gestaodeprioridades/docs/produto/visao.md:226-234: B apresenta a tabela de medidas ('Notas distintas 13', 'Tarefas que empatam 106 (93%)', 'E = 5 em 114 de 114', 'D = 3,704 em 112 de 114') sem comando nem nome de script no corpo do documento. Recalculei todas as quatro contra `prototipo/dados/fixture.json` e todas conferem (13 / 106 = 93,0% / 114 de 114 / 112 de 114), assim como 5,37, '2 passam de 5,00', '16 mudam de faixa' (com os limiares reais do código, `kanban-v0.tsx:86-87`), '33 contra 19' e as oito tarefas empatadas em 3,57 nas posições 8-15 da frente Neogrid. O defeito é de forma, não de fato: nenhum leitor consegue reexecutar a partir do documento.
- MENOR — /home/user/gestaodeprioridades/docs/produto/visao.md:78-79: B afirma que 'a razão entre a nota atual e a normalizada é 1,1 em todas, sem exceção'. Recalculando, a razão dá {1,0998, 1,0999, 1,1000, 1,1011} — a dispersão vem do arredondamento da nota a duas casas em `kanban-v0.tsx:22` (`.toFixed(2)`), não da fórmula. A tese de B está certa (o fator é constante e a ordem não muda em nenhuma das 114), mas o 'sem exceção' vale para a álgebra e não para o número exibido na tela, distinção que o próprio documento faria bem em marcar já que é ele quem insiste em calcular em vez de descrever.
