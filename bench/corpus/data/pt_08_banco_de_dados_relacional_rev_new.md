Um banco de dados relacional é um banco de dados que modela os dados de uma forma que eles sejam percebidos pelo usuário como tabelas, ou mais formalmente relações.

O termo é aplicado aos próprios dados, quando organizados dessa forma, ou a um Sistema Gerenciador de Banco de Dados Relacional (SGBDR)  – do inglês Relational database management system (RDBMS) – um programa de computador que implementa a abstração.

## Histórico
Os Bancos de dados relacionais (BDR) surgiram em meados da década de 1970. Porém, apenas alguns anos mais tarde as empresas passaram a utilizá-los no lugar de arquivos simples (do inglês flat file), bancos de dados hierárquicos e em rede.

### As 13 regras
Em 1985, Edgar Frank Codd, criador do modelo relacional, publicou um artigo onde definia 13 regras para que um Sistema Gerenciador de Banco de Dados (SGBD) fosse considerado relacional:

# Regra Fundamental:
#* Um SGBD relacional deve gerir os seus dados usando apenas suas capacidades relacionais
# Regra da informação:
#* Toda informação deve ser representada de uma única forma, como dados em uma tabela
# Regra da garantia de acesso:
#* Todo o dado (valor atómico) pode ser acedido logicamente (e unicamente) usando o nome da tabela, o valor da chave primária da linha e o nome da coluna.
# Tratamento sistemático de valores nulos:
#* Os valores nulos (diferente do zero, da string vazia, da string de caracteres em brancos e outros valores não nulos) existem para representar dados não existentes de forma sistemática e independente do tipo de dado.
# Catálogo dinâmico on-line baseado no modelo relacional:
#* A descrição do banco de dados é representada no nível lógico como dados ordinários (isto é, em tabelas), permitindo que usuários autorizados apliquem as mesmas formas de manipular dados aplicada aos dados comuns ao consultá-las.
# Regra da sub-linguagem abrangente:
#* Um sistema relacional pode suportar várias linguagens e formas de uso, porém deve possuir ao menos uma linguagem com sintaxe bem definida e expressa por cadeia de caracteres e com habilidade de apoiar a definição de dados, a definição de visões, a manipulação de dados, as restrições de integridade, a autorização e a fronteira de transações.
# Regra da atualização de visões:
#* Toda visão que for teoricamente atualizável será também atualizável pelo sistema.
# Inserção, atualização e eliminação de alto nível:
#* Qualquer conjunto de dados que pode ser manipulado com um único comando para retornar informações, também deve ser manipulado com um único comando para operações de inserção, atualização e exclusão. Simplificando, significa dizer que as operações de manipulação de dados devem poder ser aplicadas a várias linhas de uma vez, ao invés de apenas uma por vez.
# Independência dos dados físicos:
#* Programas de aplicação ou atividades de terminal permanecem logicamente inalteradas quaisquer que sejam as modificações na representação de armazenagem ou métodos de acesso internos.
# Independência lógica de dados
#* Programas de aplicação ou atividades de terminal permanecem logicamente inalteradas quaisquer que sejam as mudanças de informação que permitam teoricamente a não alteração das tabelas base.
# Independência de integridade:
#* As relações de integridade específicas de um banco de dados relacional devem ser definidas em uma sub-linguagem de dados e armazenadas no catálogo (e não em programas).
# Independência de distribuição:
#* A linguagem de manipulação de dados deve possibilitar que as aplicações permaneçam inalteradas estejam os dados centralizados ou distribuídos fisicamente.
# Regra da Não-subversão:
#* Se o sistema relacional possui uma linguagem de baixo nível (um registro por vez), não deve ser possível subverter ou ignorar as regras de integridade e restrições definidas no alto nível (muitos registros por vez).

## Por que usar um Banco de Dados Relacional?
Os Bancos de Dados Relacionais foram desenvolvidos para prover acesso facilitado aos dados, possibilitando que os usuários utilizassem uma grande variedade de abordagens no tratamento das informações. Pois, enquanto em um banco de dados hierárquico os usuários precisam definir as questões de negócios de maneira específica, iniciando pela sua raiz, nos Bancos de Dados Relacionais os usuários podem fazer perguntas relacionadas aos negócios por meio de vários pontos.

A linguagem padrão dos Bancos de Dados Relacionais é a Structured Query Language, ou simplesmente SQL, como é mais conhecida.

## O Modelo Relacional
Um Banco de Dados Relacional segue o Modelo Relacional.

A arquitetura de um banco de dados relacional pode ser descrita de maneira informal ou formal. Na descrição informal estamos preocupados com aspectos práticos da utilização e usamos os termos tabela, linha e coluna. Na descrição formal estamos preocupados com a semântica formal do modelo e usamos termos como relação (tabela), tupla(linhas) e atributo(coluna).

### Tabelas (ou relações, ou entidades)
Todos os dados de um banco de dados relacional (BDR) são armazenados em tabelas. Uma tabela é uma simples estrutura de linhas e colunas. Em uma tabela, cada linha contém um mesmo conjunto de colunas. Em um banco de dados podem existir uma ou centenas de tabelas, sendo que o limite pode ser imposto tanto pela ferramenta de software utilizada, quanto pelos recursos de hardware disponíveis no equipamento.

As tabelas associam-se entre si por meio de regras de relacionamentos, que consistem em associar um ou vários atributos de uma tabela com um ou vários atributos de outra tabela.

* Exemplo: A tabela funcionário relaciona-se com a tabela cargo. Por este relacionamento, esta última tabela fornece a lista de cargos para a tabela funcionário.

Modelo teórico usado para representar conceitualmente um BD, Idealizado por Codd (1970). Baseado numa estrutura de dados simples chamada relação. É o modelo mais amplamente usado, principalmente em aplicações convencionais de BD.

### Registros (ou tuplas)
Cada linha formada por uma lista ordenada de colunas representa um registro, ou tupla. Os registros não precisam conter informações em todas as colunas, podendo assumir valores nulos quando assim se fizer necessário.

Resumidamente, um registro é uma instância de uma tabela, ou entidade.

O start da modelagem se dá a partir das ENTIDADES. Uma entidade é uma representação de um conjunto de informações sobre determinado conceito do sistema. Toda entidade possui ATRIBUTOS, que são as informações que referenciam a entidade.

Para exemplificar no sistema de controle de Biblioteca, partimos do conceito principal que é o empréstimo de obras por usuários da biblioteca. A partir deste conceito inicial, vamos ramificando e descobrindo novos conceitos. Podemos iniciar nosso raciocínio da seguinte forma:

"Uma biblioteca possui Obras literárias que podem ser tomadas em empréstimos pelos usuários credenciados."

Podemos rapidamente enxergar um cadastro de livros, um cadastro de usuários e um registro de empréstimos, certo? É essa visão que temos que ter ao modelarmos um banco, isto é, devemos detectar as informações que devemos armazenar.

Para identificar se aquele conceito pode ser uma entidade você deve apenas se perguntar: "Eu desejo armazenar quais informações sobre este conceito?" Se houver informações a serem armazenadas, você tem uma ENTIDADE. Exemplificando: Eu desejo armazenar os seguintes dados do livro: Título, Autor, Editora, Ano, Edição e Volume. Temos então a entidade Livro.

* Exemplo: O empregado Pedro é uma instância (registro) da tabela funcionário, e a função Analista Comercial é a instância (registro) da tabela cargo. Uma associação entre estas duas tabelas criaria a seguinte instância de relacionamento: Pedro é Analista Comercial, onde o verbo ser representa uma ligação entre os registros distintos.

### Colunas (atributos)
As colunas de uma tabela são também chamadas de atributos. Ex.: O campo Nome, ou endereço de uma tabela de um BD relacional.

### Chave
As tabelas relacionam-se umas as outras através de chaves. Uma chave é um conjunto de um ou mais atributos que determinam a unicidade de cada registro.

Por exemplo, se um banco de dados tem como chaves Código do Produto e ID Sistema, sempre que acontecer uma inserção de dados o sistema de gerenciamento de banco de dados irá fazer uma consulta para identificar se o registro já não se encontra gravado na tabela. Neste caso, um novo registro não será criado, resultando esta operação apenas da alteração do registro existente.

A unicidade dos registros, determinada por sua chave, também é fundamental para a criação dos índices.

Temos dois tipos de chaves:
* Chave primária: (PK - Primary Key) é um identificador exclusivo de todas as informações de cada registro dando-lhe unicidade. A chave primária nunca se repetirá.
* Chave Estrangeira: (FK - Foreign Key) é a chave formada através de um relacionamento com a chave primária de outra tabela. Define um relacionamento entre as tabelas e pode ocorrer repetidas vezes. Caso a chave primária seja composta na origem, a chave estrangeira também o será.

## Relacionamentos

Com o advento do Modelo de Entidades e Relacionamentos foi causada uma confusão entre os termos relação e relacionamento

O Modelo Relacional, quando descrito de forma matemática, é definido como um modelo formado por relações (no sentido matemático) entre os domínios. Cada tupla é um elemento do conjunto relação.

Ou seja, a relação é a tabela.

Um relacionamento do Modelo de Entidades e Relacionamentos é uma associação entre entidades distintas. Não há relação direta entre o nome relacionamento e o nome relação.

Porém, um relacionamento, do Modelo de Entidades e Relacionamentos é traduzido para a criação de atributos com chaves externas do Modelo Relacional. Esta tradução é feita ligando-se um campo de uma tabela X com um campo de uma tabela Y, por meio da inclusão do campo chave da tabela Y como um campo (conhecido como chave estrangeira) da tabela X.

Por meio das chaves estrangeiras, é possível implementar restrições nos SGBDR.

Existem alguns tipos de relacionamentos possíveis no MER:

* Um para um (1 para 1) - indica que as tabelas têm relação unívoca entre si. Você escolhe qual tabela vai receber a chave estrangeira;
* Um para muitos (1 para N) - a chave primária da tabela que tem o lado 1 está para ir para a tabela do lado N. No lado N ela é chamada de chave estrangeira;
* Muitos para muitos (N para N) - quando tabelas têm entre si relação n..n, é necessário criar uma nova tabela com as chaves primárias das tabelas envolvidas, ficando assim uma chave composta, ou seja, formada por diversos campos-chave de outras tabelas. A relação então se reduz para uma relação 1..n, sendo que o lado n ficará com a nova tabela criada.

Os relacionamentos 1 para 1 e 1 para N podem ser mapeados diretamente em chaves estrangeiras nas tabelas originais. Já o relacionamento N para N  exige o uso de uma tabela auxiliar.

No relacionamento N:N não há chave estrangeira.

## Modelagem
### Normalização
A normalização de dados é um processo que simplifica grupos complexos de dados para evitar redundâncias e possibilitar um maior desempenho nas pesquisas. Uma tabela está na primeira forma normal quando seus atributos não contêm grupos de repetição, ou seja, multivalorados.

Exemplo:

!ClienteID !! Nome !! Telefone

Esta tabela logo acima não está na primeira forma normal porque apresenta grupos de repetição (possibilidade de mais de um telefone por cliente).

Já estas tabelas logo abaixo, Cliente e Telefone, estão na primeira forma normal.

Tabela Cliente:

!ClienteID !! Nome

Tabela Telefone:

!ClienteID !! Telefone

### Segunda Forma Normal (FN2)
Uma relação está na FN2 quando duas condições são satisfeitas:

1 - A relação está na 1FN;

2 - Todo atributo da tabela seja dependente funcional da chave completa e não de parte da chave. Ou seja, Todos os atributos não-chave dependem funcionalmente de toda a chave primária.

### Terceira Forma Normal (FN3)
A 3FN exige que não existam atributos transitivamente dependentes da chave.

Um exemplo de uma tabela 2FN que não atende o critério para 3FN é:

! <u>Torneio</u> !! <u>Ano</u> !! Vencedor!! Data de nascimento do vencedor

A chave primária composta é {Torneio, Ano}.

A tabela não está na terceira forma normal porque o atributo "data de nascimento do vencedor" é dependente transitivamente de {Torneio, Ano} via o atributo "Vencedor". O fato da data de nascimento do vencedor não ser dependente do vencedor torna a tabela vulnerável a inconsistências lógicas, já que nada impediria de uma mesma pessoa aparecer com datas de nascimento diferentes em dois registros.

Para atender a terceira forma normal, a mesma informação deveria ser dividida em duas tabelas:

! <u>Torneio</u> !! <u>Ano</u> !! Vencedor

! <u>Jogador</u> !! Data de nascimento

As duas tabelas acima estão na terceira forma normal.

## Quota de mercado
De acordo com a DB-Engines, em março de 2021, os sistemas mais usados foram:

*Oracle Database
*MySQL
*Microsoft SQL Server
*PostgreSQL (free)
*IBM Db2
*SQLite (free)
*Microsoft Access
*MariaDB (free)
*Hive (free)
*Teradata
*Microsoft Azure SQL Database

De acordo com a empresa de pesquisa Gartner, em 2011, os cinco principais fornecedores de banco de dados relacional de software proprietário por receita foram Oracle (48,8%), IBM (20,2%), Microsoft (17,0%), SAP incluindo Sybase (4,6%) e Teradata (3,7 %).

## Ver também
* Administração de dados
* Banco de dados
* Data warehouse
* Ciência da Computação
* Arquitetura de dados
* Modelo de Entidades e Relacionamentos

Categoria:Sistemas de gerenciamento de banco de dados

Categoria:Tipos de bancos de dados

