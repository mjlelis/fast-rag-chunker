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

## Interface de uso
Os sistemas operacionais fornecem abstração de hardware para que seus recursos possam ser usados de maneira correta e padronizada, mas para ser possível operar um computador, é necessário fornecer também uma interface para que o usuário possa desfrutar dos recursos do sistema. Atualmente (2009) as principais interfaces de uso são as seguintes:

## Sistemas operacionais modernos
Um sistema computacional moderno consiste em um ou mais processadores, memória principal, discos, impressoras, teclado, , monitor, interfaces de rede e outros dispositivos de entrada e saída. Os computadores têm um dispositivo de software denominado sistema operacional, cujo trabalho é fornecer aos programas do usuário um modelo de computador melhor, mais simples e mais limpo e lidar com o gerenciamento de todos os recursos mencionados.

Um dos conceitos mais fundamentais dos sistemas operacionais modernos é a distinção entre o programa e a atividade de executá-lo. O programa é apenas um conjunto estático de diretrizes e sua execução é uma atividade dinâmica.

## Exemplos de sistemas operacionais
### Para desktop/servidores

### Para dispositivos móveis (tablets e smartphones)

† - descontinuado

## Ver também
* Inter-Process Communication
* Pseudossistema operacional
* Root no Android
* Sistema distribuído
* Sistema operacional de Tempo-Real
* Sistema operacional em disco
* Sistema operacional móvel
* Sistema operacional Hobby

## Bibliografia
* BACH, Maurice J. The design of the Unix operating system. Upper Saddle River: Prentice Hall. 1990.
* BOVET Daniel P.; CESATI, Marco. Understanding de Linux kernel. 3.ed. Sebastopol: O'Reilly. 2005.
* MCKUSICK, Marshall K.; NEVILLE-NEIL, George V. The design and implementation of the FreeBSD operating system. Upper Saddle River: Addison-Wesley. 2004.
* RUSSINOVITCH, Mark E.; SOLOMON, David A. Microsoft Windows internals. 4.ed. Redmond: Microsoft Press. 2005.
* SILBERSCHATZ, Avi; GALVIN, Peter B.; GAGNE, Greg. Operating system concepts. 7.ed. Hoboken: Wiley. 2005.
* STALLINGS, William. Operating systems: internals and design principles. 5.ed. Upper Saddle River: Pearson Prentice Hall. 2004.
* TANENBAUM, Andrew. Sistemas operacionais modernos. Rio de Janeiro: LTC. 1999.

