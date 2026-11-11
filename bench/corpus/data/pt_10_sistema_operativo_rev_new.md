é um software que gerencia os recursos de um dispositivo, como a memória e o processamento, permite a execução de programas e aplicativos, define qual programa recebe atenção do processador, cria um sistema de arquivos, e fornece uma interface entre o computador e o . Embora possa ser executado imediatamente após a máquina ser ligada, a maioria dos computadores pessoais de hoje o executa através de outro programa armazenado em uma memória não-volátil ROM chamado BIOS num processo chamado "bootstrapping", conceito em inglês usado para designar processos autossustentáveis, ou seja, capazes de prosseguirem sem ajuda externa. Após executar testes e iniciar os componentes da máquina (monitores, discos, etc), o BIOS procura pelo sistema operacional em alguma unidade de armazenamento, geralmente o Disco Rígido, e a partir daí, o sistema operacional "toma" o controle da máquina. O sistema operacional reveza sua execução com a de outros programas, como se estivesse vigiando, controlando e orquestrando todo o processo computacional.

Segundo Tanenbaum, pela perspectiva do usuário ou programador, existem dois modos distintos de conceituar um sistema operacional:
* <u>numa visão de cima para baixo (top-down)</u>: é uma abstração do hardware, fazendo o papel de intermediário entre os programas (software) e os componentes físicos do computador (hardware); ou
* <u>numa visão de baixo para cima (bottom-up)</u>: é um gerenciador de recursos, i.e., que controla as aplicações (processos) a executar, como, quando e com quais recursos (memória, disco, periféricos).

Um sistema operacional é projetado para ocultar as particularidades de hardware (ditas "de baixo nível") e, com sua atuação, criar uma máquina abstrata que fornece às aplicações serviços compreensíveis ao usuário (ditas "de alto nível").

## História
thumb|Sistema operacional em linha de comando.|213x213px
Na primeira geração (aproximadamente 1945-1955), os computadores eram tão grandes que ocupavam salas imensas, ou mesmo andares inteiros. Foram basicamente construídos com válvulas e painéis, e os sistemas operacionais "não existiam". Os programadores, que também eram os operadores, controlavam o computador por meio de chaves, fios e luzes de aviso.

Nomes como Howard Aiken, John von Neumann, John Adam Presper Eckert Jr, William Mauchley e Konrad Zuse formaram, com suas contribuições, a base humana para o sucesso na construção dos computadores primitivos.

Na geração seguinte (aproximadamente 1955-1965), foram criados os sistemas em lote (batch systems), que permitiram um melhor uso dos recursos computacionais. A base do sistema operacional era um programa monitor, usado para enfileirar tarefas (jobs). O usuário foi afastado do computador; cada programa era escrito em cartões perfurados, que por sua vez eram carregados, juntamente com o respectivo compilador (normalmente Fortran ou Cobol), por um operador, usando uma linguagem de controle chamada JCL (job control language).

No início da computação os primeiros sistemas operacionais eram únicos, pois cada mainframe vendido necessitava de um sistema operacional específico. Esse problema era resultado de arquiteturas diferentes e da linguagem que cada máquina utilizava. Após essa fase, iniciou-se a pesquisa de sistemas operacionais que automatizassem a troca de tarefas (jobs), pois os sistemas eram monousuários e tinham cartões perfurados como entrada (eliminando, assim, o trabalho de pessoas que eram contratadas apenas para trocar os cartões perfurados).

Diz-se que Alan Turing era um mestre nos primeiros Manchester Mark I, e que já estava derivando a concepção primitiva de um sistema operacional a partir dos princípios da máquina de Turing universal.

Um dos primeiros sistemas operacionais de propósito geral foi o CTSS, desenvolvido no MIT. Após o CTSS, o MIT, os laboratórios Bell da AT&T e a General Electric desenvolveram o Multics, cujo objetivo era suportar centenas de usuários. Apesar do fracasso comercial, o Multics serviu como base para o estudo e desenvolvimento de sistemas operacionais. Um dos desenvolvedores do Multics, que trabalhava para a Bell, Ken Thompson, começou a reescrever o Multics num conceito menos ambicioso, criando o Unics (em 1969), que mais tarde passou a chamar-se Unix.

Os sistemas operacionais eram geralmente programados em assembly, até mesmo o Unix em seu início. Então, Dennis Ritchie (também da Bell) criou a linguagem C a partir da linguagem B, que havia sido criada por Thompson. Finalmente, Thompson e Ritchie reescreveram o Unix em C. O Unix criou um ecossistema de versões, onde destacam-se: System V e derivados (HP-UX, AIX); família BSD (FreeBSD, NetBSD, OpenBSD, etc.), Linux e até o Mac OS X (que deriva do Mach e FreeBSD). O BSD foi lançado em 1977, sendo ele um sistema operacional fortemente baseado no Unix, focado principalmente para a execução em máquinas específicas de alto desempenho, como o famoso computador VAX, o qual foi uma referência de hardware na época.

Durante a década de 70, o Unix foi distribuído gratuitamente (incluindo seu código fonte) para universidades e órgãos governamentais norte-americanos, o que conferiu muita popularidade a este sistema. Sua interface era totalmente em modo texto, sem interface gráfica. Quando começaram a aparecer os computadores pessoais, houve a necessidade de um sistema operacional de utilização mais fácil. Em 1980, Bill Gates e seu colega de faculdade, Paul Allen, fundadores da Microsoft, compram o sistema QDOS ("Quick and Dirty Operating System") de Tim Paterson por US$ 50 mil e batizaram-no de MS-DOS (Microsoft Disk Operating System). O DOS original, de desenvolvimento da IBM, foi o sistema operativo que a IBM apresentou aquando do lançamento do primeiro PC, vendeu muitas cópias, como o sistema operativo nos computadores pessoais desenvolvidos pela IBM. IBM convidou a Microsoft para uma parceria para o desenvolvimento da versão 2 do IBM OS/2. Após o fim da breve parceria, a IBM prosseguiu sozinha com o desenvolvimento do OS/2, a que deu o nome de OS/2 Warp, fazendo concorrência direta ao MS Windows 95.

No começo da década de 1990, o finlandês Linus Torvalds, na altura, estudante de computação, escreveu um comentário numa lista de discussão da Usenet dizendo que estava desenvolvendo um núcleo de sistema operacional e perguntou se alguém gostaria de o auxiliar na tarefa. Este foi o primeiro passo em direção ao desenvolvimento do sistema operativo Linux.

## Visão geral
Existem vários sistemas operativos; entre eles, os mais utilizados no dia a dia, normalmente utilizados em computadores domésticos, são o Windows, Linux e macOS.
thumb|200px|O OS/360 foi colocado na estrutura principal de todos os computadores IBM no início de 1964, incluindo os computadores que ajudaram a NASA a colocar o homem na lua
Um computador com o sistema operativo instalado poderá não dar acesso a todo o seu conteúdo dependendo do utilizador; isso, pois com um sistema operativo, podemos estabelecer permissões a vários utilizadores que trabalham com este.

Para isso existem dois tipos de contas que podem ser criadas num sistema operativo, as contas de Administrador e as contas limitadas.

A conta Administrador é uma conta que oferece todo o acesso à máquina, desde a gestão de pastas, ficheiros e software de trabalho ou entretenimento ao controle de todo o seu hardware instalado.

A conta Limitada é uma conta que não tem permissões para aceder a algumas pastas ou instalar software que seja instalado na raiz do sistema ou então que tenha ligação com algum hardware que altere o seu funcionamento normal ou personalizado pelo Administrador. Para que este tipo de conta possa ter acesso a outros conteúdos do disco ou de software, o administrador poderá personalizar a conta oferecendo permissões a algumas funções do sistema como também poderá retirar acessos a certas áreas do sistema.

O sistema operativo funciona com a iniciação de processos que este irá precisar para funcionar corretamente. Esses processos poderão ser ficheiros que necessitam de ser frequentemente atualizados, ou ficheiros que processam dados úteis para o sistema.

Poderemos ter acesso a vários processos do sistema operativo a partir do gestor de tarefas, onde se encontram todos os processos que estão em funcionamento desde o arranque do sistema operativo até a sua utilização atual. Pode-se também visualizar a utilização da memória por cada processo, no caso de o sistema operativo começar a mostrar erros ou falhas de acesso a programas tornando-se lento, pode-se verificar no gestor de tarefas qual dos processos estará bloqueado ou com elevado número de processamento que está a afetar o funcionamento normal da memória.

## Estrutura em camada

A estruturação em camadas é um modelo de sistema operacional que o divide em várias camadas sobrepostas. Cada camada proporciona um conjunto de funções que pode ser usado por outras camadas.

Uma das maiores vantagens desse modelo de camadas é isolar o sistema operacional, facilitando sua alteração e depuração, além de criar uma hierarquia de níveis de modos, protegendo as camadas mais internas.

O empilhamento de várias camadas de software faz com que cada pedido de uma aplicação demore mais tempo para chegar até o dispositivo periférico ou recurso a ser acessado, prejudicando o desempenho do sistema.

## Funcionamento
Um sistema operacional possui as seguintes funções:

# gerenciamento de processos;
# gerenciamento de memória;
# gerenciamento de recursos;
# entrada e saída de dados;
# sistema de arquivos.

### Gerenciamento de processos
O sistema operacional multitarefa é preparado para dar ao usuário a ilusão que o número de processos em execução simultânea no computador é maior que o número de processadores instalados. Cada processo recebe uma fatia do tempo e a alternância entre vários processos é tão rápida que o usuário pensa que sua execução é simultânea.

São utilizados algoritmos de escalonamento para determinar qual processo será executado em determinado momento e por quanto tempo.

Os processos podem comunicar-se, isto é conhecido como IPC (Inter-Process Communication). Os mecanismos geralmente utilizados são:

* pipes;
* named pipes;
* memória compartilhada;
* soquetes (sockets);
* trocas de mensagens.

O sistema operacional, normalmente, deve possibilitar o multiprocessamento (SMP ou NUMA). Neste caso, processos diferentes e threads podem ser executados em diferentes processadores. Para essa tarefa, ele deve ser reentrante e interrompível, o que significa que pode ser interrompido no meio da execução de uma tarefa.

### Gerenciamento de memória

O sistema operacional tem acesso completo à memória do sistema e deve permitir que os processos dos usuários tenham acesso seguro à memória quando o requisitam.
thumb|150px|direita|O primeiro servidor para [[World Wide Web|WWW rodou em um NeXTSTEP baseado no BSD.]]
Vários sistemas operacionais usam memória virtual, que possui 3 funções básicas:
# Assegurar que cada processo tenha seu próprio espaço de endereçamento, começando em zero, para evitar ou resolver o problema de relocação (Tanenbaum, 1999);
# Prover proteção da memória para impedir que um processo utilize um endereço de memória que não lhe pertença;
# Possibilitar que uma aplicação utilize mais memória do que a fisicamente existente.

#### Swapping
Dentro de gerenciamento de memória, pode não ser possível manter todos os processos em memória, muitas vezes por não existir memória suficiente para alocar aquele processo. Para solucionar esse problema existe um mecanismo chamado swapping, onde a gerência de memória reserva uma área do disco para o seu uso em determinadas situações, e um processo é completamente copiado da memória para o disco; este processo é retirado da fila do processador e mais tarde será novamente copiado para a memória; Então, o processo ficará ativo na fila novamente. O resultado desse revezamento no disco é que o sistema operacional consegue executar mais processos do que caberia em um mesmo instante na memória. Swapping impõe aos programas um grande custo em termos de tempo de execução, pois é necessário copiar todo o processo para o disco e mais tarde copiar novamente todo o processo para a memória. Em sistemas onde o usuário interage com o programa durante sua execução, o mecanismo de swapping é utilizado em último caso, quando não se é possível manter todos os processos na memória, visto que a queda no desempenho do sistema é imediatamente sentida pelo usuário.

### Gerenciamento de recursos
Uma das tarefas com extrema importância atribuída ao sistema operacional é o gerenciamento de recursos, que tem a função de definir políticas para gerenciar o uso dos recursos de hardware pelos aplicativos, resolvendo disputas e conflitos. Vários programas de entrada de dados competem pela vez na CPU (Unidade Central de Processamento) e demandam memória, espaço em disco e largura. O sistema operacional tem a função de cuidar de cada aplicativo e para que os mesmos tenham recursos necessários para o melhor funcionamento e gerencia a capacidade limitada do sistema para que possa atender todas as necessidades de aplicativos e usuários.

### Entrada e saída de dados
Sistemas operacionais controlam e gerenciam a entrada e saída (E/S) de dispositivos por três razões. Primeiro, porque a maioria do hardware do dispositivo utiliza uma interface de baixo nível, a interface do software é complexa. Em segundo lugar, porque um dispositivo é um recurso compartilhado, um sistema operacional fornece acesso de acordo com as políticas que tornam a partilha justa e segura. Em terceiro lugar, um sistema operacional define uma interface de alto nível que esconde detalhes e permite que um programador possa usar um conjunto coerente e uniforme das operações ao interagir com os dispositivos.

O subsistema de E/S pode ser divididos em três peças conceituais:
# Uma interface abstrata que consiste funções de E/S de alto nível que os processos possam usar para executar I / O;
# Um conjunto de dispositivos físicos;
# Software de driver de dispositivo que conecta os dois.

### Sistema de arquivos
A memória principal do computador é volátil, e seu tamanho é limitado pelo custo do hardware. Assim, os usuários necessitam de algum método para armazenar e recuperar informações de modo permanente.

Um arquivo é um conjunto de bytes, normalmente armazenado em um dispositivo periférico não volátil (p.ex., disco), que pode ser lido e gravado por um ou mais processos.

## Interface de uso
Os sistemas operacionais fornecem abstração de hardware para que seus recursos possam ser usados de maneira correta e padronizada, mas para ser possível operar um computador, é necessário fornecer também uma interface para que o usuário possa desfrutar dos recursos do sistema. Atualmente (2009) as principais interfaces de uso são as seguintes:

### Interface de terminal
A interface de terminal, também chamada de interface de linha de comando ou "CLI" (Command Line Interface) funciona exclusivamente com o teclado. Os comandos são digitados a partir de um prompt e são interpretados por um interpretador de comandos, conhecidos também por shells, bastante comuns em sistemas padrão POSIX. Um exemplo de interpretador de comandos seria o Bash.

Usada geralmente por usuários avançados e em atividades específicas, como gerenciamento remoto, utiliza poucos recursos de hardware em comparação a interface gráfica.

### Interface textual
thumb|Aplicativo com interface textual, rodando no sistema operacional FreeDOS
Assim como a interface de terminal, a interface textual também é baseada em texto, porém também tem à disposição um ambiente de trabalho composto por menus, janelas e botões. Esse tipo de interface tinha um uso difundido em aplicações baseadas no MS-DOS, que, inclusive, nas versões mais recentes contava com um gerenciador de programas e arquivos baseados nesse tipo de interface (o DOS Shell).

Essa interface é muito rara, praticamente restrita a sistemas implementados na década de 1980 e início da década de 1990. Esse ambiente ainda prescinde do uso mouse, embora seja possível usá-lo através do uso da biblioteca ncurses no desenvolvimento dos softwares.

### Interface gráfica
Nesse tipo de interface, também chamada GUI (Graphic User Interface) além de menus, janelas e botões também existem figuras, tanto vetoriais quanto fotografias. O usuário interage com esse tipo de interface usando o mouse, podendo também usar o teclado e teclas de atalho, ou então usando toques e gestos em touchscreens. A interface gráfica permite atuar com algumas aplicações que seriam impossíveis através da linha de comando puramente, como edição de imagem e vídeo.

Acrescentar facilidade de uso e agilidade é o objetivo da interface gráfica, tendo a desvantagem de consumir muito mais memória que interfaces de linha de comando. Ao contrário das interfaces textuais e de terminal, as interfaces gráficas dependem de um servidor gráfico para funcionar e se comunicar com o sistema, e no caso dos sistemas para desktops e laptops, inclui um gerenciador de janelas em muitos casos, para que seja possível usar mais de um aplicativo na mesma tela. Em sistemas padrão POSIX é comum existir mais de um ambiente gráfico para o mesmo sistema, podendo ser escolhido a critério do usuário.

### Interface de voz
Interfaces de voz, ou VUI (Voice User Interface), são aquelas em que o usuário interage com o sistema por meio de comandos sonoros. Sendo de desenvolvimento relativamente recente, tem sua aplicação em dispositivos adaptados para cegos e recentemente têm aparecido também para uso geral em smartphones, tablets e desktops.

## Tipos de sistemas
### Sistema Mono-programado
Também chamados como sistema mono-tarefa, o sistema operacional mono-programado possui apenas um processador, realiza alocação de memória para somente um processo e um usuário por vez. Apresenta também uma CPU ociosa durante E/S e sua implementação é feita de forma simples.

### Sistema em Lote
O sistema em lote é 
