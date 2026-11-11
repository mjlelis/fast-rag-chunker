thumb|300px|Uma captura de tela do compilador [[GNU Compiler Collection|GCC versão 4.0.2 rodando em uma janela xterm. Um programa simples está sendo compilado e então executado.]]

Um compilador é um programa de computador (ou um grupo de programas) que, a partir de um código fonte escrito em uma linguagem compilada, cria um programa semanticamente equivalente, porém escrito em outra linguagem, código objeto. Classicamente, um compilador traduz um programa de uma linguagem textual
facilmente entendida por um ser humano para uma linguagem de máquina ,
específica para um processador e sistema operacional. Atualmente, porém,
são comuns compiladores que geram código para uma máquina virtual que
é, depois, interpretada por um interpretador. Ele é chamado compilador por razões históricas; nos primeiros anos da programação automática, existiam programas que percorriam bibliotecas de sub-rotinas e as reunia, ou compilava, as subrotinas necessárias para executar uma determinada tarefa.

O nome "compilador" é usado principalmente para os programas que traduzem o código fonte de uma linguagem de programação de alto nível para uma linguagem de programação de baixo nível (por exemplo, Assembly ou código de máquina). Contudo alguns autores citam exemplos de compiladores que traduzem para linguagens de alto nível como C. Para alguns autores um programa que faz uma tradução entre linguagens de alto nível é normalmente chamado um tradutor, filtro ou conversor de linguagem. Um programa que traduz uma linguagem de programação de baixo nível para uma linguagem de programação de alto nível é um descompilador. Um programa que faz uma tradução entre uma linguagem de montagem e o código de máquina é denominado montador (assembler).

## História
thumb|200px|[[Grace Hopper em 1984.]]

Os softwares para os primeiros computadores foram escritos principalmente em linguagem assembly por muitos anos. As linguagens de alto nível de programação não foram inventadas até que os benefícios de ser capaz de reutilizar software em diferentes tipos de CPUs passassem a ser significativamente maiores do que o custo de se escrever um compilador. A capacidade de memória muito limitada dos primeiros computadores também criava muitos problemas técnicos na implementação de um compilador.

No final da década de 1950, as linguagens de programação independentes de máquina foram propostas. Posteriormente, vários compiladores experimentais foram desenvolvidos. O primeiro compilador foi escrito por Grace Hopper, em 1952, para a linguagem de programação A-0. Antes de 1957, foram desenvolvidos esforços e várias contribuições ao desenvolvimento de linguagens de alto nível foram feitas. Entre estes, o desenvolvimento da Short Code (UNIVAC), Speedcoding no IBM 701, o Whirlwind, o BACAIC e o PRINT. A equipe de desenvolvimento do FORTRAN liderada por John Backus na IBM é geralmente creditada como tendo introduzido o primeiro compilador completo em 1957 (embora tenha ocorrido simultaneamente o desenvolvimento do algebraic translator de Laning e Zierler

Em muitos domínios de aplicação a ideia de usar uma linguagem de alto nível rapidamente ganhou força. Por causa da funcionalidade de expansão apoiada por linguagens de programação recentes e a complexidade crescente de arquiteturas de computadores, os compiladores tornaram-se mais e mais complexos.

Os primeiros compiladores foram escritos em linguagem assembly. O primeiro compilador de auto-hospedagem - capaz de compilar seu próprio código-fonte em uma linguagem de alto nível - foi criado para o Lisp por Tim Hart e Levin Mike no MIT em 1962.

## Características
thumb|esquerda|120px|O processo da compilação.
Normalmente, o código fonte é escrito em uma linguagem de programação de alto nível, com grande capacidade de abstração, e o código objeto é escrito em uma linguagem de baixo nível, como uma sequência de instruções a ser executada pelo microprocessador.

O processo de compilação é composto de análise e síntese. A análise tem como objetivo entender o código fonte e representá-lo em uma estrutura intermediária. A síntese constrói o código objecto a partir desta representação intermediária.

A análise pode ser subdividida ainda em análise léxica, análise sintática, análise semântica e geração de código intermediário. É também conhecida como front end.

Um compilador é chamado de Just-in-time compiler (JIT) quando seu processo de compilação acontece apenas quando o código é chamado. Um JIT pode fazer otimizações às instruções a medida que as compila. Normalmente é responsável por mudanças no código fonte destinadas de acordo com decisões tomadas em tempo de compilação. Por exemplo, um programa em C permite instruções condicionais para o pré-processador que podem incluir ou não parte do código caso uma assertiva lógica seja verdadeira ou falsa, ou simplesmente um termo esteja definido ou não. Tecnicamente, pré-processadores são muito mais simples que compiladores e são vistos, pelos desenvolvedores, como programas à parte, apesar dessa visão não ser necessariamente compartilhada pelo usuário.

Outra parte separada do compilador que muitos usuários vêem como integrada é o linker, cuja função é unir vários programas já compilados de uma forma independente e unificá-los em um programa executável. Isso inclui colocar o programa final em um formato compatível com as necessidades do sistema operacional para carregá-lo em memória e colocá-lo em execução.

## Fases da compilação
### Análise léxica

A análise léxica é a primeira fase do compilador. A função do analisador léxico, também denominado scanner, é ler o código-fonte, caractere a caractere, buscando a separação e identificação dos elementos componentes do programa-fonte, denominados símbolos léxicos ou tokens. É também de responsabilidade desta fase a eliminação de elementos "decorativos" do programa, tais como espaços em branco, marcas de formatação de texto e comentários. Existem disponíveis uma série de geradores automáticos de analisadores léxicos, como por exemplo, o lex. O objetivo dos geradores automáticos é limitar o esforço de programação de um analisador léxico especificando-se apenas os tokens a ser reconhecidos.

### Análise sintática

A análise sintática, ou análise gramatical é o processo de se determinar se uma cadeia de símbolos léxicos pode ser gerada por uma gramática. O analisador sintático é o cerne do compilador, responsável por verificar se os símbolos contidos no programa fonte formam um programa válido, ou não. No caso de analisadores sintáticos top-down, temos a opção de escrevê-los à mão ou gerá-los de forma automática, mas os analisadores bottom-up só podem ser gerados automaticamente. A maioria dos métodos de análise sintática, cai em uma dessas duas classes denominadas top-down e bottom-up. Entre os métodos top-down os mais importantes são a análise sintática descendente recursiva e a análise sintática preditiva não-recursiva. Entre os métodos de análise sintática bottom-up os mais importantes são a análise sintática de precedência de operadores, análise sintática LR canônico, análise sintática LALR e análise sintática SLR. como por exemplo, o Yacc, o Bison e o JavaCC.

### Análise semântica

As análises léxica e sintática não estão preocupadas com o significado ou semântica dos programas que elas processam. O papel do analisador semântico é prover métodos pelos quais as estruturas construídas pelo analisador sintático possam ser avaliadas ou executadas. As gramáticas livres de contexto não são suficientemente poderosas para descrever uma série de construções das linguagens de programação, como por exemplo regras de escopo, regras de visibilidade e consistência de tipos. É papel do analisador semântico assegurar que todas as regras sensíveis ao contexto da linguagem estejam analisadas e verificadas quanto à sua validade. Um exemplo de tarefa própria do analisador semântico é a checagem de tipos de variáveis em expressões. Um dos mecanismos comumente utilizados por implementadores de compiladores é a Gramática de Atributos, que consiste em uma gramática livre de contexto acrescentada de um conjunto finito de atributos e um conjunto finito de predicados sobre estes atributos.

### Geração de código intermediário
thumb|200px|Exemplo de código de três endereços e um [[Grafos acíclicos dirigidos|DAG correspondente para uma expressão aritmética.]]

Na fase de geração de código intermediário, ocorre a transformação da árvore sintática em uma representação intermediária do código fonte. Esta linguagem intermediária é mais próxima da linguagem objeto do que o código fonte, mas ainda permite uma manipulação mais fácil do que se código assembly ou código de máquina fosse utilizado. Um tipo popular de linguagem intermediária é conhecido como código de três endereços. Neste tipo de código uma sentença típica tem a forma <code>X := A op B</code>, onde X, A e B são operandos e op uma operação qualquer. Uma forma prática de representar sentenças de três endereços é através do uso de quádruplas (operador, argumento 1, argumento 2 e, resultado). Este esquema de representação de código intermediário é preferido por diversos compiladores, principalmente aqueles que executam extensivas otimizações de código, uma vez que o código intermediário pode ser rearranjado de uma maneira conveniente com facilidade. Outras representações de código intermediário comumente usadas são as triplas, (similares as quádruplas exceto pelo fato de que os resultados não são nomeados explicitamente) as árvores, os grafos acíclicos dirigidos(DAG) e a notação polonesa.

### Otimização de código

A otimização de código é a estratégia de examinar o código intermediário, produzido durante a fase de geração de código com objetivo de produzir, através de algumas técnicas, um código que execute com bastante eficiência.

### Geração de código final

A fase de geração de código final é a última fase da compilação. A geração de um bom código objeto é difícil devido aos detalhes particulares das máquinas para os quais o código é gerado. Contudo, é uma fase importante, pois uma boa geração de código pode ser, por exemplo, duas vezes mais rápida que um algoritmo de geração de código ineficiente.

## Tratamento de erros
thumb|esquerda|300px|Tratamento de erro de execução em uma aplicação [[Java (linguagem de programação)|Java no Eclipse.]]
O tratamento de erros está voltado a falhas devido a muitas causas: erros no compilador, erros na elaboração do programa a ser compilado, erros no ambiente (hardware, sistema operacional), dados incorretos, etc. As tarefas relacionadas ao tratamento de erros consistem em detectar cada erro, reportá-lo ao usuário e possivelmente fazer algum reparo para que o processamento possa continuar.

Os erros podem ser classificados em erros léxicos, erros sintáticos, erros não independentes de contexto (semânticos), erros de execução e erros de limite. Os erros léxicos ocorrem quando um token identificado não pertence a gramática da linguagem fonte. Os erros sintáticos ocorrem quando alguma estrutura de frase não está de acordo com a gramática, como por exemplo parênteses sem correspondência. Os erros não independentes de contexto em geral são associados a não declaração de objetos como variáveis e erros de tipos. Os erros de execução ocorrem após a compilação, quando o programa já está sendo executado. Um exemplo típico é o da divisão por zero. Os erros de limite, ocorrem durante a execução e estão relacionados as características da máquina na qual o programa está sendo executado, como por exemplo, estouro de pilha.

A recuperação de erros em analisadores sintáticos top-down é mais fácil de implementar do que em analisadores bottom-up. O problema é que diferente de um analisador top-down, este último não sabe quais símbolos são esperados na entrada, somente os que já foram processados. Pode-se usar neste caso técnicas como, por exemplo, a técnica de panic-mode que procura em tabelas sintáticas em busca de símbolos válidos na entrada.

## Notas

## Ver também
* Ciência da computação
* Compilador Just in Time (JIT)
* Linguagens formais
* Linguagem de programação
* Interpretador
* Linker

## Bibliografia
*
*
*
*
*
*
*
*

## Ligações externas

*
*

Categoria:Programação

