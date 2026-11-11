thumb|400px|direita|Exemplo de Árvore B

Em ciência da computação, uma árvore B é uma estrutura de dados em árvore, auto-balanceada, que armazena dados classificados e permite pesquisas, acesso sequencial, inserções e remoções em tempo logarítmico. A árvore B é uma generalização de uma árvore de pesquisa binária em que um nó pode ter mais que dois filhos. Diferente das árvores de pesquisa binária auto-balanceadas, a árvore B é bem adaptada para sistemas de armazenamento que leem e escrevem blocos de dados relativamente grandes, como discos.

É normalmente usada em bancos de dados e sistemas de arquivos e foi projetada para funcionar especialmente em memória secundária como um disco magnético ou outros dispositivos de armazenamento secundário. As árvores B são semelhantes as árvores preto e vermelho, mas são melhores para minimizar operações de E/S de disco. Muitos sistemas de bancos de dados usam árvores B ou variações da mesma para armazenar informações. Dentre suas propriedades ela permite a inserção, remoção e busca de chaves numa complexidade temporal logarítmica e, por esse motivo, é muito empregada em aplicações que necessitam manipular grandes quantidades de informação tais como um banco de dados ou um sistemas de arquivos.

Inventada por Rudolf Bayer e Edward Meyers McCreight em 1971 enquanto trabalhavam no Boeing Scientific Research Labs, a origem do nome (árvore B) não foi definida por estes. Especula-se que o B venha da palavra balanceamento, do nome de um de seus inventores Bayer ou de Boeing, nome da empresa.

Árvores B são uma generalização das árvores binária de busca, pois cada nó de uma árvore binária armazena uma única chave de busca, enquanto as árvores B armazenam um número maior do que um de chaves de busca em cada nó, ou no termo mais usual para essa árvore, em cada página. Como a ideia principal das árvores B é trabalhar com dispositivos de memória secundária, quanto menos acessos a disco a estrutura de dados proporcionar, melhor será o desempenho do sistema na operação de busca sobre os dados manipulados.

## Visão geral
thumb|400px|direita|Árvore-B de ordem 2(Bayer & McCreight 1972) ou ordem 5 (Knuth 1998).
Os dispositivos de memória de um computador consistem na memória principal e secundária, sendo cada uma delas com suas características. A memória primária é mais conhecida como memória volátil de endereçamento direto (RAM), esta por sua vez apresenta baixo tempo de acesso, porém armazena um volume relativamente pequeno de informação e altos custos. Já a memória secundária, possui um endereçamento indireto, armazena um grande volume de informação e possui um acesso (seek) muito lento quando comparada com a memória primária. A árvore B é uma solução para cenários em que o volume de informação é alto (e este não pode ser armazenado diretamente em memória primária) e, portanto, apenas algumas páginas da árvore podem ser carregadas em memória primária.

As árvores B são organizadas por nós, tais como os das árvores binárias de busca, mas estes apresentam um conjunto de chaves maior do que um e são usualmente chamados de páginas. As chaves em cada página são, no momento da inserção, ordenadas de forma crescente e para cada chave há dois endereços para páginas filhas, sendo que, o endereço à esquerda é para uma página filha com um conjunto de chaves menor e o à direita para uma página filha com um conjunto de chaves maior. A figura acima demonstra essa organização de dados característica. Se um nó interno x contém n[x] chaves, então x tem n[x] + 1 filhos. As chaves do nó x são usadas como pontos de divisão que separam o intervalo de chaves manipuladas por x em x[x] subintervalos, cada qual manipulado por um filho de x.

Vale lembrar que todo este endereçamento está gravado em arquivo (memória secundária) e que um acesso a uma posição do arquivo é uma operação muito lenta. Através da paginação é possível carregar em memória primária uma grande quantidade de registros contidos numa única página e assim decidir qual a próxima página que o algoritmo de busca irá carregar em memória primária caso esta chave buscada não esteja na primeira página carregada. Após carregada uma página em memória primária, a busca de chave pode ser realizada linearmente sobre o conjunto de chaves ou através de busca binária.

## Definição

### Nó ou página
Um nó ou página, geralmente é representado por um conjunto de elementos apontando para seus filhos. Alguns autores consideram a ordem de uma árvore B como sendo a quantidade de registros que a página pode suportar. Outros consideram a ordem como a quantidade de campos apontadores. Todo nó da árvore tem um mínimo de registros definido pela metade da ordem, arredondando-se para baixo, caso a árvore seja de ordem ímpar, exceto a raiz da árvore, que pode ter o mínimo de um registro. Por exemplo, os nós de uma árvore de ordem 5, podem ter, no mínimo<math>\lfloor5/2\rfloor</math> registros, ou seja, dois registros. A quantidade de filhos que um nó pode ter é sempre a quantidade de registros do nó mais 1 (V+1). Por exemplo, se um nó tem 4 registros, este nó terá obrigatoriamente 5 apontamentos para os nós filhos.

Para definir uma árvore B devemos esclarecer os conceitos de ordem e página folha de acordo com cada autor Bayer e McCreight, Além disso, servem como base para o desenvolvimento do código de árvores preto e vermelho.

Existem três situações na mudança de árvore B para árvore rubro-negra:

* Caso o nó só possua uma chave, basta transformá-lo num nó de cor preta e ligá-lo aos seus filhos correspondentes.
* Caso o nó possua duas chaves, a chave mais à esquerda será transformada num nó preto e a mais à direita, num nó vermelho. O nó preto terá como filho da esquerda o primeiro nó filho da antiga árvore e como filho da direita o novo nó vermelho. Este, por sua vez, terá como filhos os dois filhos restantes da lista de filhos da árvore original.
* Caso o nó possua três chaves, a chave do meio será transformada num nó vermelho e terá como filhos as antigas chaves adjacentes que serão nós pretos com os antigos filhos da árvore B.

Aplicando essas situações, deve-se checar se as propriedades de árvores rubro-negra são mantidas como o valor do nó da esquerda ser menor que o nó atual.

## Variações
As árvores B não são as únicas estruturas de dados usadas em aplicações que demandam a manipulação de grande volume de dados, também existem variações desta que proporcionam determinadas características como as árvores B+ e B*. Estas, por sua vez, se assemelham muito com as árvores B, mas possuem propriedades diferentes.
* As árvores B+ possuem seus dados armazenados somente em seus nós folha e, seus nós internos e raiz, são apenas referências para as chaves que estão em nós folha. Assim é possível manter ponteiros em seus nós folha para um acesso sequencial ordenado das chaves contidas no arquivo.
* Árvores B* diferem das árvores B em relação ao particionamento de suas páginas. A estratégia dessa variação é realizar o particionamento de duas páginas irmãs somente quando estas estiverem completamente cheias e, claro, isso somente é possível através da redistribuição de chaves entre estas páginas filhas. Estando completamente cheias, as chaves são redistribuídas entre três páginas diferentes que são as duas irmãs anteriores e uma nova criada.

## Comparação com as variações
Se compararmos as árvores B com suas variações podemos enumerar algumas características importantes para a escolha de implementação destas:
* Árvores B+:
*# A principal característica proporcionada por esta variação é o fato de permitir o acesso sequencial das chaves por meio de seu sequence set de maneira mais eficiente do que o realizado em árvores B .

}}

## Bibliografia
*

*

*

## Ligações externas
* [http://slady.net/java/bt/view.php Applet de uma árvore B segundo a definição de Bayer & McCreight (1972)]
* [https://web.archive.org/web/20120626143441/http://ats.oka.nu/b-tree/b-tree.manual.html Animação em Flash de uma árvore B]
* [https://web.archive.org/web/20120223163741/http://groups.engin.umd.umich.edu/CIS/course.des/cis350/treetool/ Applet de uma árvore B, árvore AVL, árvore binária]
* [http://cis.stvincent.edu/html/tutorials/swd/btree/btree.html Código em C++ de uma árvore B]
* [https://web.archive.org/web/20170331115357/http://www.inf.ufrgs.br/~pmdusso/works/Relatorio_CPD_Disk_Guru.htm Aplicação em MS Visual C# que implementa um árvore B orientada a objetos]
*[https://www.cs.usfca.edu/~galles/visualization/BTree.html Visualizador de árvores B pelo departamento de Ciência da Computação da Universidade de São Francisco]

Categoria:Estruturas de dados

