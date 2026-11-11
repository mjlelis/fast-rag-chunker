thumb|350px|right|Uma função criptográfica de embaralhamento (especificamente, [[SHA-1) funcionando.  Note que mesmo pequenas mudanças no código-fonte alteram drasticamente a saída do resultado, pelo chamado efeito avalanche.]]

Uma função de dispersão criptográfica ou função hash criptográfica é uma função hash considerada praticamente impossível de inverter, isto é, de recriar o valor de entrada utilizando somente o valor de dispersão. Essas funções hash unidirecionais têm sido chamadas de "os operários da criptografia moderna". Os dados de entrada costumam ser chamados de mensagem, e o valor de dispersão mensagem resumida ou simplesmente resumo.

Uma função de dispersão criptográfica deve possuir quatro propriedades principais:
* deve ser fácil computar o valor de dispersão para qualquer mensagem
* deve ser difícil gerar uma mensagem a partir de seu resumo
* deve ser difícil modificar a mensagem sem modificar o seu resumo
* deve ser difícil encontrar duas mensagens diferentes com o mesmo resumo.

Funções hash criptográficas possuem várias aplicações em segurança da informação, principalmente em assinatura digital, código de autenticação de mensagem (MACs), e outras formas de autenticação. Elas também podem ser utilizadas como funções hash, para indexar dados em tabelas hash, para impressão digital, para detectar dados duplicados ou identificar arquivos únicos, e como checksum para detectar corrupção de dados acidental. De fato, no contexto da segurança da informação, valores de dispersão criptográficos são às vezes conhecidos como impressão digital, checksums, ou apenas valores de dispersão, apesar de todos esses termos se referirem a funções mais gerais com propriedades e propósitos diferentes.

## Propriedades

Muitas funções hash criptográficas são projetadas para receber uma cadeia de caracteres de qualquer tamanho como entrada e produzir um valor hash de tamanho fixo.

Uma função hash criptográfica deve ser capaz de aguentar todo tipo de ataque cripto-analítico conhecido. No mínimo, ela deve possuir as seguintes propriedades:

* Resistência à pré-imagem
*: Dado um valor hash h deve ser difícil encontrar qualquer mensagem m tal que h = hash(m). Este conceito está relacionado ao da função de mão única (ou função unidirecional). Funções que não possuem essa propriedade estão vulneráveis a ataques de pré-imagem.
* Resistência à segunda pré-imagem
*: Dada uma entrada m<sub>1</sub> deve ser difícil encontrar outra entrada m<sub>2</sub> tal que . Funções que não possuem essa propriedade estão vulneráveis a ataques de segunda pré-imagem.
* Resistência à colisão
*: Deve ser difícil encontrar duas mensagens diferentes m<sub>1</sub> e m<sub>2</sub> tal que . Tal par é chamado de colisão hash criptográfica. Essa propriedade também é conhecida como forte resistência à colisão. Ela requer um valor hash com pelo menos o dobro do comprimento necessário para resistência à pré-imagem; caso contrário, colisões podem ser encontradas através de um ataque do aniversário.

Uma função com todos esses critérios ainda pode possuir propriedades indesejadas. Atualmente, funções hash criptográficas populares estão vulneráveis a ataques de extensão de comprimento: dado  e  mas não m, escolhendo um m adequado um atacante pode calcular  onde || denota concatenação. Essa propriedade pode ser usada para quebrar esquemas de autenticação ingênuos baseados em funções hash. A construção HMAC contorna esses problemas.

Idealmente, o projetista da função deve desejar por condições mais fortes. Deve ser impossível para um adversário encontrar duas mensagens com resumos substancialmente similares; ou inferir qualquer informação útil sobre os dados a partir de seu resumo. Portanto, uma função hash criptográfica deve se comportar tão semelhante quanto possível a uma função aleatória ainda sendo determinística e eficientemente computável.

Algoritmos de checksum, tais como CRC32 e outras verificação de redundância cíclicas, são projetadas para atender requisitos mais fracos, e são geralmente inapropriados para atuar como funções hash criptográficas. Por exemplo, um CRC foi utilizado para a integridade de mensagens na encriptação WEP padrão, mas um ataque que explorava a linearidade do checksum foi logo descoberto.

### Grau de dificuldade

Na prática criptográfica, “dificuldade” geralmente significa “quase certamente longe do alcance de qualquer adversário que deve ser impedido de quebrar o sistema enquanto a segurança de tal sistema for importante”. O significado do termo, portanto, depende da aplicação, já que o esforço que o agente malicioso deve colocar na tarefa é normalmente proporcional ao que ele espera conseguir. Entretanto, como o esforço necessário geralmente cresce rapidamente com o comprimento do resumo, até um atacante com um grande poder de processamento pode ser neutralizado adicionando algumas dúzias de bits ao resumo.

Em algumas análises teóricas “dificuldade” tem um significado matemático específico, como "não solucionável em tempo polinomial assintótico". Essas interpretações de dificuldade são importantes no estudo de funções hash criptográficas provadas seguras mas não costumam ter uma forte relação com segurança na prática. Por exemplo, um algoritmo de tempo exponencial pode ser rápido o bastante para realizar um ataque factível. Reciprocamente, um algoritmo de tempo polinomial (e.g., um que requer n<sup>20</sup> passos por chaves de n-dígitos) pode ser lento demais para usos práticos.

## Ilustração

Uma ilustração do uso potencial de uma dispersão criptográfica é a seguinte: Alice propõe um problema matemático complicado para Bob e afirma ser capaz de resolvê-lo. Bob quer tentar resolvê-lo sozinho, mas primeiro precisa ter certeza de que Alice não está blefando. Portanto, Alice escreve a solução, computa o valor hash e diz a Bob tal valor (mantendo a solução em segredo). Então, quando Bob vier com sua solução alguns dias depois, Alice pode provar que ela já tinha a solução, tirando o valor hash da solução de Bob e comparando-o ao valor que ela havia calculado. (Este é um exemplo simples de esquema de comprometimento; numa prática real, Alice e Bob seriam programas de computador, e o segredo algo menos facilmente falsificado como uma afirmação de solução a um enigma).

## Aplicações

### Verificação da integridade de arquivos ou mensagens

Uma importante aplicação desses hashes de segurança é na verificação da integridade de mensagens. Determinar se qualquer alteração foi feita a uma mensagem (ou um arquivo), por exemplo, pode ser realizado comparando mensagens resumidas, calculadas antes e depois da transmissão (ou qualquer outro evento).

Por essa razão, muitos algoritmos de assinatura digital apenas confirmam a autenticidade do resumo de uma mensagem para ser "autenticado". Verificar a autenticidade do resumo de uma mensagem é considerado prova de que a mensagem em si é autêntica.

Hashes MD5, SHA1, ou SHA2 são ocasionalmente informados juntos de seus arquivos em websites e fóruns o que permite a verificação de integridade. Essa prática estabelece uma cadeia de confiança, contanto que as hashes sejam postadas em sites autenticados por HTTPS.

### Verificação de senha

Uma aplicação relacionada é a verificação de senha (inventada por Roger Needham). Armazenar todas as senhas de um usuário como purotexto pode resultar em uma quebra massiva de segurança caso o arquivo de senha seja comprometido. Uma maneira de reduzir esse perigo é de apenas armazenar o resumo de cada senha. Para autenticar um usuário, calcula-se o resumo da senha fornecida pelo usuário e o compara-se ao resumo armazenado. (Note que essa abordagem impede que a senha original seja recuperada se esquecida ou perdida, e terá que ser substituída por uma nova.) A senha, geralmente, é concatenada com um valor aleatório, não-secreto conhecido como sal, antes de ser aplicada a função hash. O sal é armazenado junto ao hash da senha. Como usuários devem possuir sais diferentes, é impraticável armazenar tabelas de valores hash pré-computados para senhas comuns. Funções de alongamento de chave, como PBKDF2, Bcrypt ou Scrypt, costumam utilizar chamadas repetidas de hash criptográficos para aumentar o tempo necessário de um ataque de força bruta sobre o resumo das senhas armazenadas.

Em 2013, uma Password Hashing Competition foi anunciada para escolher um novo algoritmo padrão para computar hash de senhas.

### Prova-de-trabalho

Um sistema a prova-de-trabalho (ou protocolo, ou função) é uma medida econômica para deter ataques de negação de serviço e outros abusos de serviço como spam. O sistema solicita ao solicitante do serviço que faça algum trabalho, o que normalmente significa tempo de processamento para o computador. Uma característica chave desses esquemas é sua assimetria: esse trabalho deve ser moderadamente difícil (mas factível) para o solicitante e fácil de verificar para o fornecedor do serviço. Um sistema muito popular - utilizado em mineração de bitcoin e hashcash - utiliza inversões parciais de hash para provar que o trabalho foi realizado, como um símbolo de boa-vontade para mandar um e-mail. O remetente é solicitado a encontrar a mensagem cujo valor hash começa com um número de bits zero. O trabalho médio que o remetente precisa realizar para encontrar a mensagem válida é exponencial no número de bits zero necessários no valor hash, enquanto o beneficiário pode verificar a validação da mensagem executando uma única função hash. Por exemplo, em hashcash, o remetente é solicitado a gerar um cabeçalho cujo valor hash SHA1 de 160 bits tenha seus primeiros 20 bits como 0. O remetente terá que tentar, em média, 2<sup>20</sup> vezes até encontrar um cabeçalho válido.

### Identificador de arquivo ou dados

Um resumo de mensagem também pode servir como um identificador confiável de arquivo; diversos sistemas de gerenciadores de código fonte, como Git, Mercurial e Monotone, usam o sha1sum de vários tipos de conteúdo (conteúdo de arquivo, árvores de diretório, informação ancestral, etc.) para identificá-los univocamente. Hashes são usados para identificar arquivos em redes de compartilhamento de arquivos. Por exemplo, em um link ed2k, uma variação do hash MD4 é combinado com o tamanho do arquivo, fornecendo informação suficiente para a localização das fontes do arquivo, baixando o arquivo e verificando seus conteúdos. Magnet-links são outros exemplos. Tais hashes de arquivo costumam aparecer no começo de listas de hash ou em árvores de hash o que propicia ainda mais benefícios.

Uma das principais aplicações de uma função hash é permitir uma rápida visualização dos dados em uma tabela hash. Por serem funções hash com propriedades específicas, funções hash criptográficas também podem ser utilizadas para essas aplicações.

Entretanto, comparadas a funções hash padrão, funções hash criptográficas tendem a ser computacionalmente mais caras. Por essa razão, elas costumam ser usadas em contextos onde é necessário que usuários protejam a si mesmo contra a possibilidade de falsificação (criação de dados com o mesmo resumo que os dados esperados) por agentes maliciosos em potencial.

### Geradores pseudo-aleatórios e derivação de chave

Funções hash também podem ser utilizadas para gerar bits pseudo-aleatórios, ou para derivar novas chaves ou senhas de uma única e segura chave ou senha.

## Funções hash baseadas em cifras de bloco

Há diversos métodos de utilizar uma cifra de bloco para construir funções hash criptográficas, especificamente uma função de compressão unidirecional.

Esse método é semelhante ao modo de operação de uma cifra de bloco geralmente utilizado em encriptação. Muitas funções hash conhecidas, como MD4, MD5, SHA-1 e SHA-2 são construídas de componentes semelhantes a cifras de bloco, projetados para esse propósito, com feedback para garantir que a função resultante não seja inversível. Os finalistas da competição de função hash da NIST projetistas do SHA-3, incluíram funções semelhantes a bloco de cifras como componentes (e.g., Skein, BLAKE) apesar da função selecionada, Keccak, ao contrário, ter sido construída sobre uma esponja criptográfica.

Uma cifra de bloco padrão como a AES pode ser utilizada no lugar dessas cifras de bloco personalizadas; isso pode ser útil quando um sistema embarcado precisa implementar funções de encriptação e hash utilizando um tamanho mínimo de código ou área de hardware. Entretanto, essa abordagem pode ter um custo de eficiência e segurança. As cifras em função hash são construídas para calcular hash: elas utilizam chaves e bloco de grande comprimento, podem mudar eficientemente de chaves em cada bloco, e foram projetadas e corrigidas para resistir a ataques de chave relacionadas. Cifras de propósito geral costumam possuir objetivos de projeto diferentes. Em particular, AES possui tamanhos de chave e blocos que torna não-trivial a geração de valores hash longos; encriptação AES torna-se menos eficiente quando a chave muda a cada bloco; e ataques de chave relacionadas a tornam potencialmente menos segura para uso em função hash do que em encriptação.

## A construção Merkle–Damgård
thumb|400px|right|A construção hash Merkle-Damgård.
Uma função hash deve ser capaz de processar uma mensagem de comprimento arbitrário produzindo uma saída de comprimento fixo. Isso pode ser alcançado, através da quebra da entrada em blocos de tamanhos iguais, e operar sobre elas, em sequência, utilizando funções de compressão unidirecional. A função de compressão pode ser especialmente projetada para calcular o hash ou construída a partir de uma cifra de blocos. A função hash construída com a construção Merkle-Damgård é tão resistente a colisão quanto a sua função de compressão; qualquer colisão para a função hash total pode ser rastreada a uma colisão em uma das funções de compressão.

O último bloco processado deve ter um "preenchimento" acrescentado a seu comprimento inequivocamente (prática conhecida como padding); isso é crucial para a segurança dessa construção. Essa construção é chamada de Merkle-Damgård. Funções hash largamente utilizadas, incluindo SHA-1 e MD5, utilizam essa construção.

A construção possui certas falhas inerentes, como ataques de extensão de comprimento e gerar-e-colar, e não pode ser paralelizada. Por isso, muitos participantes da competição de função hash de NIST costumam utilizar construções diferentes, e às vezes, originais.

## Uso na construção de outras primitivas criptográficas
Funções hash podem ser utilizadas na construção de outras primitivas criptográficas. Para que essas outras primitivas sejam criptograficamente seguras, alguns cuidados devem ser tomados para construí-las corretamente.

Autenticadores de mensagem (MACs) (também chamados de função hash chaveadas) costumam ser construídos a partir de função hash. HMAC é um MAC.

Assim como cifras de bloco podem ser utilizadas para construir funções hash, funções hash também podem ser utilizadas para construir cifras de bloco. A cifra de Feistel utilizando funções hash podem ser provadas seguras caso a função hash utilizada seja segura. Além disso, muitas funções hash (como SHA-1 2 SHA-2) são construídas utilizando uma cifra de bloco de propósito especial em uma Davies-Meyer ou outra construção. Essa cifra também pode ser utilizada em modo de operação convencional, sem as mesmas garantias de segurança. Por exemplo, SHACAL, BEAR e LION.

Geradores de números pseudoaleatórios (GNPAs) podem ser construídos a partir de funções hash. Isso é feito combinando uma semente aleatória e secreta a um contador e fornecendo essa combinação a função hash.

Algumas função hash, tais como Skein, Keccak e RadioGatún fornecem como saída uma cadeia arbitrariamente longa e podem ser utilizadas como cifra de fluxo, e cifras de fluxo podem ser construídas de funções hash com resumo de comprimento fixo. Frequentemente, isso é feito construindo, primeiro, um gerador de números pseudoaleatórios criptograficamente seguro e usando seu fluxo de bytes aleatórios como fluxo de chave (keystream). SEAL é uma cifra de fluxo que utiliza SHA-1 para gerar tabelas internas, que são então utilizadas em um gerador de fluxo de chave com certa relação ao algoritmo de hash. SEAL não possui garantia de ser tão forte (ou fraca) quanto SHA-1. Similarmente, a expansão de chave das cifras de fluxo HC-128 e HC-256 fazem alto uso da função hash SHA256.

## Concatenação de funções hash criptográficas
Concatenar saídas de múltiplas funções hash provê resistência a colisões tão fortes quanto os algoritmos inclusos no resultado concatenado. Por exemplo, uma versão antiga da TSL/SSL usa somas da MD5 e SHA-1 concatenadas - isso garante que o método de detectar colisões em uma das funções não permite falsificação do tráfego protegido por ambas as funções.

Para funções hash Merkle-Damgård, a função concatenada é tão resistente a colisão quanto seu componente mais forte, mas nunca mais resistente a colisão. Joux nota que 2 colisões levam a n colisões: se encontrar duas mensagens com a mesma hash MD5 é factível, então não é mais difícil encontrar quantas mensagens quanto o atacante desejar com hashes MD5 idênticas. Entre as n mensagens com a mesma hash MD5, é provável que haja uma colisão em SHA-1. O trabalho adicional necessário para encontrar a colisão em SHA-1 (além da busca de aniversário exponencial) é polinomial. Esse argumento é sumarizado por [http://article.gmane.org/gmane.comp.encryption.general/5154 Finney].

## Algoritmos hash criptográficos
Há uma lista longa de algoritmos hash criptográficos, apesar de muitos terem sido mostrados vulneráveis e não devem mais ser utilizados. Mesmo que uma função hash nunca tenha sido quebrada, um ataque bem sucedido quanto uma variante mais fraca, pode enfraquecer a confiança de profissionais da área e levar a seu abandono. Por exemplo, em Agosto de 2004, foram descobertas fraquezas em um número de funções hash bastante populares na época, incluindo SHA-0, RIPEMD, e MD5. Isso colocou em questão a segurança a
