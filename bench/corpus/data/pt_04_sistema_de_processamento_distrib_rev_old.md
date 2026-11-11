Чичилэнд - новый мир– мультфильм про машинки для детей – серия 52

thumb|direita|418x418px|Sistema de processamento distribuído

Um sistema de processamento distribuído ou paralelo é um sistema que interliga vários nós de processamento (computadores individuais, não necessariamente homogéneos) de maneira que um processo de grande consumo seja executado no nó "mais disponível", ou mesmo subdividido por vários nós. Conseguindo-se, portanto, ganhos óbvios nestas soluções: uma tarefa qualquer, se divisível em várias subtarefas pode ser realizada em paralelo.

A nomenclatura geralmente utilizada neste contexto é HPC (High Performance Computing) e/ou DPC (Distributed/Parallel Computing).

## Desenvolvimento
Este é um assunto muito vasto e, embora com alguma idade, só em 2001 se começou a falar em padrões para estas soluções, que são utilizadas (em larga escala) geralmente nos meios científicos e outros de cálculo intensivo pela sua extensibilidade. São bastante flexíveis, já que permitem a coexistência de sistemas desenhados especificamente para isso (por exemplo, a arquitectura NUMA), de sistemas desktop, e mesmo de sistemas considerados obsoletos, mas não o suficiente para permitir a coexistência de soluções semelhantes.

Antes de avançar, será necessário distinguir um sistema de multiprocessamento paralelo (SMP) de um sistema distribuído. Para um sistema ser de processamento distribuído, uma ou várias unidades de processamento (CPU) estará separada fisicamente da(s) outra(s), enquanto que num sistema SMP todas as unidades de processamento se encontram na mesma máquina. Ambos sistemas são capazes de processamento paralelo, e qualquer um deles pode ser visto como elemento de um sistema distribuído!

Com os desenvolvimentos nesta área, surgiram soluções por software que fazem, geralmente (mas não necessariamente), alterações no núcleo do sistema operativo e que, na maioria dos casos, não são compatíveis entre elas, e dificilmente entre versões diferentes da mesma solução. Assentam, no entanto, em arquitecturas de comunicação padrão, como é o caso da Parallel Virtual Machine e Message Passing Interface. Resumidamente, estas arquitecturas conseguem transportar um processo (tarefa) e o seu contexto (ficheiros abertos, etc.) pela rede até outro nó. O nó que originou o processo passa, assim, a ser apenas um receptor dos resultados desse processo.

Actualmente, a principal barreira destes sistemas é implementar mecanismos de Inter-Process Communication (IPC), os Distributed IPC, dada a sua extrema complexidade.

## Arquitetura
A Figura 1 ilustra as várias camadas de interoperabilidade de um sistema distribuído. Através do gateway a rede pública tem acesso a um supercomputador, sem ter conhecimento disso, dado que só conhece o gateway. Qualquer aplicação executada no gateway (preparada para ser paralelizada) pode ser distribuída por vários nós, entregando os resultados mais rápido do que se fosse processada por apenas um nó.
## Definição
De acordo com TANENBAUM, “Um sistema distribuído é um conjunto de computadores independentes que se apresenta a seus usuários como um sistema único e coerente”, “Definimos um sistema distribuído como sendo aquele no qual os componentes de hardware ou software, localizados em computadores interligados em rede, se comunicam e coordenam ações apenas enviando mensagens entre si.”

Assim, a computação distribuída consiste em adicionar o poder computacional de diversos computadores interligados por uma rede de computadores. A união desses diversos computadores com o objetivo de compartilhar a execução de tarefas, é conhecida como sistema distribuído.

## Características
Abaixo características de um sistema distribuído. Conforme definição de COULORIS :

Segurança: A criptografia pode ser usada para proporcionar proteção adequada para os recursos compartilhados e para manter informações sigilosas em segredo, quando transmitidas em mensagens de uma rede. Os ataques de negação de serviço ainda são um problema.

Escalabilidade: um sistema distribuído é considerado escalável se o custo de adição de um usuário for um valor constante, em termos dos recursos que devem ser adicionados. Os algoritmos usados para acessar os dados compartilhados devem evitar gargalos de desempenho, e os dados devem ser estruturados hierarquicamente para se obter os melhores tempos de acesso. Os dados acessados frequentemente podem ser replicados.

Tratamento de falhas: qualquer processo, computador ou rede pode falhar, independentemente dos outros. Portanto, cada componente precisa conhecer as maneiras possíveis pela quais os componentes de que depende podem falhar e ser projetado de forma a tratar cada uma dessas falhas apropriadamente.

Concorrência: a presença de múltiplos usuários em um sistema destruído é uma fonte de pedidos concorrentes para seus recursos. Em ambiente concorrente, cada recurso deve ser projetado para manter a consistência nos estados de seus dados.

Transparência: o objetivo é tornar certos aspectos da distribuição invisíveis para o programador de aplicativos, param que este se preocupe apenas com o projeto de seu aplicativo em particular. Por exemplo, ele não precisa estar preocupado com sua localização ou com os detalhes sobre como suas operações serão acessadas por outros componentes, nem se será replicado ou migrado. As falhas de rede e processos podem ser apresentadas aos programadores de aplicativos na forma de exceções - mas elas devem ser tratadas.

## Organização
Organizar a interação entre cada computador é essencial. Visando poder usar o maior número possível de máquinas e tipos de computadores, o protocolo ou canal de comunicação não pode conter ou usar nenhuma informação que possa não ser entendida por certas máquinas. Cuidados especiais também devem ser tomados para que as mensagens sejam entregues corretamente e que as mensagens inválidas sejam rejeitadas, caso contrário, levaria o sistema a cair ou até o resto da rede.

Outro fator de importância, é a habilidade de mandar softwares para outros computadores de uma maneira portável de tal forma que ele possa executar e interagir com a rede existente. Isso pode não ser possível ou prático quando usando hardware e recursos diferentes, onde cada caso deve ser tratado separadamente com cross-compiling ou reescrevendo software.

## Modelos de computação distribuída

### Peer-to-peer (P2P)

É uma arquitetura de sistemas distribuídos caracterizada pela descentralização das funções na rede, onde cada nó realiza tanto funções de servidor quanto de cliente.

### Objetos distribuídos
Semelhante ao peer-to-peer (do inglês peer-to-peer, que significa ponto-a-ponto) é um formato de rede de computadores em que a principal característica é descentralização das funções convencionais de rede, onde o computador de cada usuário conectado acaba por realizar funções de servidor e de cliente ao mesmo tempo.

Seu principal objetivo é a transmissão de arquivos e seu surgimento possibilitou o compartilhamento em massa de músicas e filmes. Com a crescente utilização da rede P2P para este fim, cada vez mais surgem programas para este fim, porém nem sempre eles atendem às expectativas do usuário.

Diversas redes operam hoje em dia nestes moldes de compartilhamento, entre elas Kademlia, Gnutela, Kad Network e SoulSeek. Alguns programas valem a pena ser citados quando o assunto é compartilhamento P2P: μTorrent, BitTorrent, SoulSeek, Ares Galaxy, Shareaza, DreaMule, iMesh e Morpheus. Caso prefira, acesse a categoria de Compartilhadores P2P do Baixaki e conheça mais programas que operam deste modo.

Mas com um Middleware intermediando o processo de comunicação.

## Hardware
A organização do hardware em sistemas com várias UCPs se dá por:

### Sistemas paralelos

* É constituído de vários processadores tipicamente homogêneos e localizados em um mesmo computador.
* Multicomputadores - Cada processador possui sua própria memória local.
* Multiprocessadores - Os processadores compartilham memória.

#### Arquiteturas
* Multiprocessadores em barramento.
* Multiprocessador.
* Multiprocessador homogêneo.
* Multiprocessador heterogêneo.

## Software
* Fracamente acoplados - um software que serve de interface entre o computador (hardware) e os humanos (peopleware) , que permite a execução de diversos outros softwares (aplicativos)....
* Fortemente acoplados -  permitem que máquinas e usuários de um sistema distribuído sejam fundamentalmente independentes e ainda interagir de forma limitada quando isto for necessário, compartilhando discos, impressoras e outros recursos.

## Sistemas operacionais
* Sistema operacional (SO) é um software que serve de interface entre o computador (hardware) e os humanos (peopleware) , que permite a execução de diversos outros softwares (aplicativos).
* SO de máquinas monoprocessadas.
* SO Multiprocessadores é uma extensão de SOs de máquinas monoprocessadas, a principal diferença sendo que os dados da memória são acessados por vários processadores e, portanto, necessitam de proteção com relação aos acessos concorrentes.
* SOs Multicomputadores são uma alternativas para o buffering de mensagens e pontos de bloqueio, alguns SOs disponibilizam uma abstração de memória compartilhada.
* SOs de rede:  existe uma independência entre os computadores.

Sistemas fortemente acoplados Neste sistema existe vários processadores compartilhando
uma memória, e gerenciado por apenas um S.O.

Múltiplos processadores permitem que vários programas sejam executados ao mesmo tempo e em tempo real.Com
isso será possível aumentar a capacidade de computação adicionando apenas processadores.

## Exemplos
* os sistemas operacionais mais conhecidos hoje são: Windows, GNU/Linux, MacOS(Apple).
* Um exemplo clássico de computação distribuída é o projeto Seti at home que visa procurar em sinais de rádio interplanetários algum vestígio de vida extraterrestre.

* O exemplo mais moderno desse paradigma é o BOINC, que é um framework de grade computacional no qual diversos projetos podem rodar suas aplicações, como fazem os projetos World Community Grid, SETI@Home, ClimatePrediction.net, Einstein@Home, PrimeGrid e OurGrid.

## Soluções
### Software
* Scyld (Beowulf)
* openMosix
* openSSI
* Open Source Cluster Application Resources (OSCAR)

## Ver também
* Arquitetura multicamada
* Modelo em três camadas
* Cliente-servidor
* Cluster
* Lista de protocolos de redes
* Protocolo RPC
* Redes de computadores
* Sistema de processamento distribuído
* Sockets
* Processamento digital de sinais
* Eletrônica digital

## Referências

## Ligações externas
*
*
*
*
* [https://codigo35.com/2022/05/31/falhas-em-sistemas-distribuidos/ Falhas em Sistemas Distribuídos]

Categoria:Computação distribuída

