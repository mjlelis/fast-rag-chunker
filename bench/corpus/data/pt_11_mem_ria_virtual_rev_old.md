thumb|250px|O programa acha que tem uma grande gama de endereços contíguos, mas, na realidade, as partes que está a utilizar estão dispersas em torno da [[RAM e as partes inactivas são guardadas em um arquivo em disco.]]

Memória virtual (também conhecido como armazenamento virtual ou swap) é uma técnica em memória do computador que usa a memória secundária como um cache para armazenamento secundário. Houve duas motivações principais: permitir o compartilhamento seguro e eficiente da memória entre vários programas e remover os transtornos de programação de uma quantidade pequena e limitada na memória principal.

A memória virtual consiste em recursos de hardware e software com três funções básicas:
* (i) realocação (ou recolocação), para assegurar que cada processo (aplicação) tenha o seu próprio espaço de endereçamento, começando em zero;
* (ii) proteção, para impedir que um processo utilize um endereço de memória que não lhe pertença;
* (iii) paginação (paging) ou troca (swapping), que possibilita a uma aplicação utilizar mais memória do que a fisicamente existente (essa é a função mais conhecida).

Simplificadamente, um usuário ou programador vê um espaço de endereçamento virtual, que pode ser igual, maior ou menor que a memória física (normalmente chamada memória DRAM - Dynamic Random Access Memory).

A memória virtual deixou os programadores despreocupados com quanto de memória seu programa irá precisar para rodar no computador e se o respectivo programa poderia rodar com outros sem travar, podendo o programador se preocupar mais com a tarefa de programação do que com quanto o programa irá gastar de memória. A melhoria é significativa quando você usa memória virtual em um computador que não tem a mesma. ou os mainframes da década de 1960, geralmente não tinham a funcionalidade da memória virtual, com as excepções notáveis do Atlas B5000 e o Apple Lisa.

A memória virtual foi inicialmente criada para possibilitar a um programa ser executado em um computador com uma quantidade de memória principal (física) menor que o tamanho de todo o espaço utilizado pelo próprio programa. Ou seja, o espaço ocupado pelas instruções, dados e pilha de execução de um programa pode ser maior que o espaço em memória principal disponível. Por exemplo, um programa que ocupa um total de 64 MiB pode ser executado em um computador com apenas 32 MiB disponíveis para o programa, bastando que o sistema operacional se encarregue de manter sempre na memória principal as partes adequadas à execução naquele momento.

A memória virtual foi desenvolvida por volta de 1959-1962, na Universidade de Manchester para o Computador Atlas, terminado em 1962. A ideia é atribuída a John Fotheringham, no entanto, Fritz-Rudolf Güntsch, um cientista alemão, pioneiro da ciência computacional e, mais tarde, o criador do mainframe Telefunken TR 440, alega ter inventado o conceito em 1957, na sua tese de doutorado Logischer Entwurf eines digitalen Rechengerätes mit mehreren asynchron laufenden Trommeln und automatischem Schnellspeicherbetrieb (Conceito lógico para um sistema digital computacional com múltiplos sistemas assíncronos de armazenamento e modo de memória rápida automática).

## Funcionamento
Existem dois mecanismos principais para implementação da memória virtual: paginação e segmentação

Na paginação a memória física é dividida em blocos de bytes contíguos denominados molduras de páginas (page frames), geralmente com tamanho de 4 KiB (arquiteturas x86 e x86-64) ou 8 KiB (arquiteturas RISC) de tamanho. Por sua vez, o espaço de memória de um processo (contendo as instruções e dados do programa) é dividido em páginas que são fisicamente armazenadas nas molduras e possuem o mesmo tamanho destas.

Na segmentação existem vários espaços de endereçamento para cada aplicação (os segmentos). Neste caso, o endereçamento consiste em um par ordenado deslocamento, onde o deslocamento é a posição do byte dentro do segmento.

Na arquitetura x86 (32 e 64 bits), são usadas a segmentação e a paginação. O espaço de endereçamento de uma aplicação é dividido em segmentos, onde é determinado um endereço lógico, que consiste no par [segmento:deslocamento]; o dispositivo de segmentação converte esse endereço para um endereço linear (virtual); finalmente, o dispositivo de paginação converte o endereço virtual para físico, localizando a moldura de página que contém os dados solicitados.

O endereço virtual é encaminhado para a unidade de gerenciamento de memória (MMU - Memory Management Unit), um dispositivo do processador, cuja função é transformar o endereço virtual em físico e solicitar este último endereço ao controlador de memória. A conversão de endereços virtuais em físicos baseia-se em tabelas de páginas, que são estruturas de dados mantidas pelo sistema operativo. Este espaço é dividido em dois: o espaço do núcleo (kernel space) e o espaço do usuário (user space). O primeiro é único e protegido das aplicações comuns, e armazena, além do próprio código do núcleo, uma estrutura que descreve toda a memória física; este espaço é limitado a um gigabyte (1024 MB). Cada aplicação recebe um espaço de endereçamento de até 3 GiB para armazenar o código e os dados do programa.

Caso a memória física seja menor do que a necessária para conter todas as aplicações, o Linux pode alocar espaço em meios de armazenamento diversos (disco rígido, dispositivo de rede e outros). Este espaço é tradicionalmente conhecido como espaço de troca (swap space), embora o mecanismo adotado seja a paginação.

### Windows em 32 bits
Analogamente ao Linux, as versões atuais do Windows de 32 bits usam um espaço de endereçamento de 4 GiB divididos em duas partes. Por padrão, o Windows reserva 2 GiB para o núcleo e permite que cada aplicação use até 2 GiB. Entretanto, é possível alterar essa configuração, e permitir que uma aplicação use até 3 GiB. Neste caso, obviamente, o espaço do núcleo será reduzido para um gigabyte .

Diferentemente do Linux, o Windows usa apenas arquivos para paginação (paging files). Pode usar até 16 desses arquivos, e cada um pode ocupar até 4095 MiB de espaço em disco.

## Espaços virtuais
Um sistema operacional convencional separa a memória virtual em espaço do núcleo e espaço do usuário, onde podem ser implementados threads(Tarefas).

### Espaço de usuário

### Espaço de núcleo
O espaço do núcleo é estritamente reservado para o núcleo, extensões do núcleo e alguns drivers de dispositivos. Em muitos sistemas operacionais, o espaço de memória ocupada pelo núcleo nunca é paginada no disco. De outro lado, o espaço de memória do usuário (no qual funcionam todos os aplicativos de modo usuário) pode ser paginada no disco sempre que necessário.

Cada processo no espaço de usuário executa no seu próprio espaço de memória virtual e, exceto se requisitado, não pode acessar a memória de outro processo. Essa é a base de proteção de memória nos principais sistemas operacionais de hoje. Dependendo do privilégio, os processos podem requisitar ao núcleo o mapeamento de parte de outros espaços de memória de processos para os seus próprios como é o caso de depuradores. Os programas podem, inclusive, requisitar áreas de memória compartilhadas com outros processos.

Uma outra abordagem de sistemas operacionais experimentais é ter um único espaço de endereços para todo software e invocar a linguagem de programação da máquina virtual para certificar-se de que memória arbitrária não possa ser acessada - os aplicativos simplesmente não podem adquirir nenhuma referência dos objetos os quais não são permitidos o acesso. Essa abordagem tem sido implementada no JXOS, Unununium bem como no projeto de pesquisa da Microsoft Singularity.

; Bibliografia
*
*
*
*

## Ver também
* Computador
* Dispositivo de armazenamento em massa
* Gerenciamento de memória
* Formas de armazenamento de dados

## Ligações externas
*
*

Categoria:Gerenciamento de memória

