Em ciência da computação, uma tabela de dispersão (também conhecida por tabela de espalhamento ou tabela hash, do inglês hash) é uma estrutura de dados especial, que associa chaves de pesquisa a valores. Seu objetivo é, a partir de uma chave simples, fazer uma busca rápida e obter o valor desejado. É algumas vezes traduzida como tabela de escrutínio.

## História
A história da tabela de dispersão é incerta. Há quem credite sua criação a H. P. Luhn que, em 1953, teve a ideia enquanto trabalhava na IBM. Outra hipótese é de que foram inventadas pelos autores de compiladores para linguagens de programação nos anos 1960, como truque para manter as listas de variáveis de usuário e seus respectivos valores. Um interpretador de linguagem BASIC, por exemplo, não é muito mais do que uma calculadora com uma tabela de dispersão em que as variáveis e seus valores são armazenados.

## Complexidade e usos comuns
Tabelas  de dispersão são tipicamente utilizadas para implementar vetores associativos, conjuntos e caches. São tipicamente usadas para indexação de grandes volumes de informação (como bases de dados). A implementação típica busca uma função de dispersão que seja de complexidade <math>O(1)</math>, não importando o número de registros na tabela (desconsiderando colisões). O ganho com relação a outras estruturas associativas (como um vetor simples) passa a ser maior conforme a quantidade de dados aumenta. Outros exemplos de uso das tabelas de dispersão são as tabelas de transposição em jogos de xadrez para computador até mesmo em serviços de DHCP.

## Função de espalhamento
frame|direita|Tabela de dispersão com vetor simples e com vetor de listas.
A função de espalhamento ou função de dispersão é a responsável por gerar um índice a partir de determinada chave. Caso a função seja mal escolhida, toda a tabela terá um mau desempenho.

O ideal para a função de espalhamento é que sejam sempre fornecidos índices únicos para as chaves de entrada. A função perfeita seria a que, para quaisquer entradas A e B, sendo A diferente de B, fornecesse saídas diferentes. Quando as entradas A e B são diferentes e, passando pela função de espalhamento, geram a mesma saída, acontece o que chamamos de colisão.

Na prática, funções de espalhamento perfeitas ou quase perfeitas são encontradas apenas onde a colisão é intolerável (por exemplo, nas funções de dispersão da criptografia), ou quando conhecemos previamente o conteúdo da tabela armazenada. Nas tabelas de dispersão comuns a colisão é apenas indesejável, diminuindo o desempenho do sistema. Muitos programas funcionam sem que seu responsável suspeite que a função de espalhamento seja ruim e esteja atrapalhando o desempenho.

Por causa das colisões, muitas tabelas de dispersão são aliadas com alguma outra estrutura de dados, tal como uma lista encadeada ou até mesmo com árvores balanceadas. Em outras oportunidades a colisão é solucionada dentro da própria tabela.

### Tipos
; Método da divisão (método da congruência linear)
<math>h (k) = k \pmod m</math>

* Potências de dois devem ser evitadas para valores de <math>m</math>.
* <math>m</math> deve ser um número primo distante de pequenas potências de dois (<math>m</math> grande).

Exemplo:

<math>
k = 10028;

m = 5013;

h (10028) = 10028 mod 5013;

h (10028) = 2

</math>

(<math>m</math> é o tamanho da tabela)

; Método da multiplicação (método da congruência linear multiplicativo)
<math>h(k) = (m * (kA \pmod 1))</math>

* <math>m</math> normalmente é uma potência de dois.
* <math>A</math> é uma constante, tal que <math>0 < A < 1</math>.
* Extrair a parte fracionária de kA, ou seja, <math>kA \pmod 1</math>.
* Utilizar o piso do resultado.

Exemplo:

<math>
k = 123456;

m = 1024;

A = 0.61803\ldots;

\begin{align}
h(k) & = 1024*(123456*0.61803\ldots \pmod 1) \\
& = 1024*(76300,0041151\ldots \pmod 1) \\
& = 1024*0,0041151\ldots \\
& = 4.21386\ldots \\
& = 4
\end{align}
</math>

### Exemplo de função de espalhamento e colisão
Imagine que seja necessário utilizar uma tabela de dispersão para otimizarmos uma busca de nomes de uma lista telefônica (dado o nome, temos que obter o endereço e o telefone). Nesse caso, poderíamos armazenar toda a lista telefônica em um vetor e criar uma função de espalhamento que funcionasse de acordo com o seguinte critério. Para cada nome começado com a letra A, devolver 0. Para cada nome começado com a letra B, devolver 1, e assim por diante. Por fim, Para cada nome começado com a letra Z, devolver 25 (Alfabeto com 26 letras).

O exemplo anterior poderia ser implementado, em C, da seguinte forma:
<syntaxhighlight lang="c">
int hashExemplo(char *chave)
{
return (chave[0]-97);
}
</syntaxhighlight>

Agora inserimos alguns nomes em nossa lista telefônica:

:José da Silva; Rua das Almas, 35; Telefone (31) 3888-9999
:Ricardo Souza; Rua dos Coqueiros, 54; Telefone (31) 3222-4444
:Orlando Nogueira; Rua das Oliveiras, 125; Telefone (31) 3444-5555

Nossa função distribuiria os nomes assim:

frame|center

Agora inserimos mais um nome:

:Renato Porto; Rua dos Elefantes, 687; Telefone (31) 3333-5555

E temos uma colisão:

frame|center

Verifica-se que, com a função hashExemplo, a ocorrência de colisões ocorre assim que uma nova entrada na lista telefônica, com um nome iniciando-se pela letra R, for adicionada. Tem-se então uma colisão com a letra R. Outro exemplo, se for adicionado "João Siqueira", a entrada estaria em conflito com o "José da Silva".

## Colisões
A função de dispersão pode calcular o mesmo índice para duas chaves diferentes, uma situação chamada colisão. Por conta disso, a função deve ser projetada para evitar ao máximo a ocorrência de colisões. Por mais bem projetada que seja a função de dispersão, sempre haverá colisões. A estrutura de dispersão utiliza mecanismos para tratar as colisões, que dependem de características da tabela usada.

Um bom método de resolução de colisões é essencial, não importando a qualidade da função de espalhamento. Considere um exemplo derivado do paradoxo do aniversário: mesmo que considerarmos que a função selecionará índices aleatórios uniformemente em um vetor de um milhão de posições, há uma chance de 95% de haver uma colisão antes de inserirmos 2500 registros.

### Mecanismos de tratamento
Os mecanismos mais comuns para tratamento de colisões são: endereçamento aberto e encadeamento.

#### Endereçamento aberto
No método de endereçamento aberto os registros em conflito são armazenados dentro da própria tabela de dispersão. A resolução das colisões é realizada através de buscas padronizadas dentro da própria tabela. A forma mais simples de fazer a busca é procurar linearmente na tabela até encontrar um registro vazio ou o registro buscado. Outras formas utilizadas incrementam o índice exponencialmente: caso o registro não seja encontrado na décima posição, será buscado na centésima, depois na milésima. A inserção tem que seguir o mesmo critério da busca. Outra forma mais complexa de implementar o endereçamento aberto é criar uma nova função de espalhamento que resolva o novo conflito (também chamado de dispersão dupla). Na prática, o que acontece nesse caso é que o vetor da tabela é formado por uma seqüência de funções de espalhamento auxiliares, em que a chave de entrada será o valor gerado pela função anterior. Esse tipo de implementação pode ser útil em casos muito específicos, com enormes quantidades de dados, mas normalmente a sobrecarga não justifica a experiência.

Possui três estratégias: tentativa linear (incremental), tentativa quadrática e dispersão dupla.

Para a estratégia linear, é utilizada uma segunda função matemática para calcular a posição em que deve ser feita a próxima prova, a função de redispersão.

<math>rh(pos, tentativas) = (pos + tentativas) mod Ttabela</math>

Desta forma eliminamos o agrupamento primário porém geramos outro fenômeno conhecido como agrupamento secundário. Ocorre que as chaves de valores diferentes e mesmo valor de dispersão possuem a mesma sequência de provas.

Para a estratégia quadrática:

<math>rh(pos, tentativas) = (pos + tentativas^{2}) mod Ttabela</math>

Para reduzir o agrupamento primário, procura-se por um lugar livre através da fórmula: <math>h+n2</math>, em que <math>h</math> representa o índice da colisão e <math>n</math> o sequencial de busca pela nova posição.

Para a estratégia de dispersão dupla:

<math>rh(ch, tentativas) = (h2(ch) + tentativas) mod Ttabela</math>

Utilizamos então a função <math>h2(ch)</math>:

<math>h2(ch) = 1 + ch mod(Ttabela - 1)</math>

#### Encadeamento
A informação é armazenada em estruturas encadeadas fora da tabela de dispersão. Encontra-se uma posição disponível na tabela e indicamos que esta posição é a que deve ser buscada em seguida. Os mais conhecidos são encadeamento separado e endereçamento aberto.

O encadeamento separado é a solução mais simples, em que normalmente um registro aponta para uma lista encadeada em que são armazenados os registros em conflito. A inserção na tabela requer uma busca e inserção dentro da lista encadeada; uma remoção requer atualizar os índices dentro da lista, como se faria normalmente. Estruturas de dados alternativas podem ser utilizadas no lugar das listas encadeadas. Por exemplo, se utilizarmos uma árvore balanceada, podemos melhorar o tempo médio de acesso da tabela de dispersão para <math>O(log n)</math> ao invés de <math>O(n)</math>. Mas como as listas de colisão são projetadas para serem curtas, a sobrecarga causada pela manutenção das árvores pode fazer o desempenho cair. Apesar disso, as árvores podem ser utilizadas como proteção contra ataques que buscam criar sobrecarga propositalmente - descobrindo uma forma da função gerar repetidamente o mesmo índice - e derrubar o sistema (ataques DOS). Nesse caso, uma árvore balanceada ajudaria o sistema a se manter estável, por ser uma estrutura com grande capacidade de crescimento.

#### Indexação perfeita
Se tivermos uma relação fixa de registros, podemos obter uma função que indexe os itens sem que ocorra uma colisão, chamada função de espalhamento perfeita. Podemos até mesmo buscar uma função de espalhamento perfeita mínima, que, além de não causar colisões, preenche todas as posições da tabela. As funções de espalhamento perfeitas fazem o tempo de acesso aos dados ser de <math>O(1)</math> no pior caso.

Existem métodos que atualizam a função de espalhamento de acordo com a entrada, de forma que nunca ocorra colisão. O inconveniente dessa técnica é que a própria atualização da função de espalhamento causa sobrecarga do sistema.

## Problemas e comparações com outras estruturas
Apesar das tabelas de dispersão terem em média tempo constante de busca, o tempo gasto no desenvolvimento é significativo. Avaliar uma boa função de espalhamento é um trabalho duro e profundamente relacionado à estatística. Na maioria dos casos soluções mais simples como uma lista encadeada devem ser levados em consideração. Isso não é um problema a não ser que você esteja criando todas as suas estruturas de dados a partir do zero.

Os dados na memória ficam aleatoriamente distribuídos, o que também causa sobrecarga no sistema. Além disso, e mais importante, o tempo gasto na depuração e remoção de erros é maior do que nas árvores balanceadas, que também podem ser levadas em conta para solução do mesmo tipo de problema.

No entanto, a maioria das linguagens de programação modernas e bibliotecas auxiliares para linguagens de baixo e médio nível dispõem de boas estruturas de dados usando tabelas de dispersão implementadas de forma bem consistente, prontas para serem usadas, mitigando não só a questão de tempo de desenvolvimento e depuração, como tendo soluções para o espalhamento em memória.  Com isso em mente, as limitações, abaixo, podem ser uma consideração mais importante.

## Limitações
A tabela de dispersão é uma estrutura de dados do tipo dicionário, que não permite armazenar elementos repetidos, recuperar elementos sequencialmente (ordenação), nem recuperar o elemento antecessor e sucessor. Para otimizar a função de dispersão é necessário conhecer a natureza da chave a ser utilizada. No pior caso, a ordem das operações pode ser <math>O(N)</math>, caso em que todos os elementos inseridos colidirem. As tabelas de dispersão com endereçamento aberto podem necessitar de redimensionamento.

### Aplicação
Suas aplicações incluem banco de dados, implementações das tabelas de símbolos dos compiladores, na programação de jogos para acessar rapidamente a posição para qual o personagem irá se mover e na implementação de um dicionário.

Em redes de computadores, NAT, Network Address Translation, também conhecido como masquerading é uma técnica que consiste em reescrever os endereços IP utilizando-se de uma tabela hash.

## Ligações externas
* [http://www.dca.fee.unicamp.br/cursos/EA876/apostila/HTML/node26.html Apostila sobre tabelas de dispersão]
*
*
*
* [https://web.archive.org/web/20140330005130/http://talkera.org.cp-in-1.webhostbox.net/wp/?p=45 Hashmap en Java]

Categoria:Estruturas de dados
Categoria:Algoritmos de busca
Categoria:Hashing

