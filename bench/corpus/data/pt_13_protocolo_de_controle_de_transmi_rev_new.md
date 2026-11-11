Protocolo de Controle de Transmissão (do inglês: Transmission Control Protocol, abreviado TCP) é um dos protocolos de comunicação, da camada de transporte da rede de computadores do Modelo OSI, que dão suporte a rede global Internet, verificando se os dados são enviados na sequência correta e sem erros via rede. É complementado pelo protocolo da Internet, normalmente chamado de, TCP/IP.

Neste protocolo da camada de transporte (camada 4 OSI) se assentam a maioria das aplicações cibernéticas, como o SSH, FTP, HTTP — portanto, a World Wide Web, Os autores do artigo, Vinton G. Cerf e Robert Kahn descreveram um protocolo de interconexão para compartilhamento de recursos usando comutação de pacotes ao longo dos nós. Um componente central de controle deste modelo foi o Transmission Control Program, que incorporou os elos e serviços orientados para datagrama entre hosts. O programa de controle de transmissão monolítico foi dividido depois dentro de uma arquitetura modular formada de um Protocolo de controle de transmissão na camada orientada a conexão e o Protocolo de internet na camada de interconexão. O modelo se torna informalmente conhecido como TCP/IP, embora formalmente tenha sido chamado de Internet Protocol Suite.

## Características técnicas

! colspan="1"|+
! colspan="4"|Bits 0 - 3
! colspan="6"|4 - 9
! colspan="6"|10 - 15
! colspan="16"|16 - 31

! colspan="1"|0

! colspan="1"|32

! colspan="1"|64

! colspan="1"|96

! colspan="1"|128

! colspan="1"|160

! colspan="1"|224

! + !! 10 !! 11 !! 12 !! 13 !! 14 !! 15

As características fundamentais do TCP são:
* Orientado à conexão - A aplicação envia um pedido de conexão para o destino e usa a "conexão" para transferir dados. Portanto, se faz necessário o estabelecimento de uma conexão, por meio de uma sequência de passos definida no protocolo para que os dois pontos da conexão possam interagir entre si.
* Handshake - Mecanismo de estabelecimento e finalização de conexão a três e quatro tempos, respectivamente, o que permite a autenticação e encerramento de uma sessão completa. O TCP garante que, no final da conexão, todos os pacotes foram bem recebidos.
* Ponto a ponto - uma conexão TCP é estabelecida entre dois pontos. A princípio, pacotes de broadcasting parecem violar esse princípio, mas o que ocorre é que é enviado um pacote com um endereço especial em seu cabeçalho que qualquer computador em sua rede pode responder a esse pacote, mesmo que não esteja explicitamente endereçado pra ele.
* Confiabilidade - O TCP usa várias técnicas para proporcionar uma entrega confiável dos pacotes de dados que, dependendo da aplicação, gera uma grande vantagem que tem em relação ao UDP. Aliado a outros fatores, o protocolo se mantém bastante difundido nas redes de computadores. O TCP permite a recuperação de pacotes perdidos, a eliminação de pacotes duplicados, a recuperação de dados corrompidos e pode recuperar a ligação em caso de problemas no sistema e na rede.
* Full duplex - É possível a transferência simultânea em ambas direções (cliente-servidor) durante toda a sessão. Apesar disso, em alguns momentos, o protocolo necessita que algum pacotes de dados cheguem para que se dê o envio de outros, o que limita as transmissões.
* Entrega ordenada - A aplicação faz a entrega ao TCP de blocos de dados com um tamanho arbitrário num fluxo (ou stream) de dados, tipicamente em octetos. O TCP parte estes dados em segmentos de tamanho especificado pelo valor MTU. Porém, a circulação dos pacotes ao longo da rede (utilizando um protocolo de encaminhamento, na camada inferior, como o IP) pode fazer com que os pacotes não cheguem ordenados. O TCP garante a reconstrução do stream no destinatário mediante os  números de sequência.
* Controle de fluxo - O TCP usa o campo janela ou window para controlar o fluxo. O receptor, à medida que recebe os dados, envia mensagens ACK (=Acknowledgement), confirmando a recepção de um segmento; como funcionalidade extra, estas mensagens podem especificar o tamanho máximo do buffer no campo (janela) do segmento TCP, determinando a quantidade máxima de bytes aceita pelo receptor. O transmissor pode transmitir segmentos com um número de bytes que deverá estar confinado ao tamanho da janela permitido: o menor valor entre sua capacidade de envio e a capacidade informada pelo receptor.
* Controle de congestionamento - Baseado no número de mensagens de reconhecimentos ACK (=Acknowledgement) recebidos pelo remetente por unidade de tempo calculada com os dados do tempo de ida e de volta, ou em inglês RTT (Round Trip Travel), o protocolo prediz o quanto a rede está congestionada e diminui sua taxa de transmissão de modo que o núcleo da rede não se sobrecarregue. Esse tipo de comportamento, a princípio ineficiente, se baseia fortemente na teoria dos jogos - especificamente em jogos simétricos que, dentre várias coisas, difunde a ideia de que se ninguém recua um pouco, para dar passagem aos demais, todos perdem.

## Funcionamento do protocolo
O protocolo TCP especifica três fases durante uma conexão: estabelecimento da ligação, transferência e término de ligação. O estabelecimento da ligação é feito em três passos, enquanto que o término é feito em quatro. Durante a inicialização são inicializados alguns parâmetros, como o Sequence Number (número de sequência) para garantir a entrega ordenada e robustez durante a transferência.

### Estabelecimento da conexão
Para estabelecer uma conexão, o TCP usa um three-way handshake (acordo de três vias). Antes que o cliente tente se conectar com o servidor, o servidor deve primeiro ligar e escutar a sua própria porta, para só depois abri-la para conexões: isto é chamado de abertura passiva. Uma vez que a abertura passiva esteja estabelecida, um cliente pode iniciar uma abertura ativa. Para estabelecer uma conexão, o acordo de três vias (ou 3 etapas) é realizado:
thumb|1.SYN : Solicitação inicial de conexão feita pelo cliente por um segmento com flag SYN ativa
thumb|2.SYN+ACK : Resposta do servidor a requisição de conexão, gerando um número de sequência aleatório B e fazendo o ACK da requisição
thumb|3.ACK : O cliente recebe o segmento do servidor e envia o ACK reconhecendo a resposta do servidor. A flag SYN zera e a partir desse ponto os dados começam a ser trocados.
# SYN: A abertura ativa é realizada por meio do envio de um segmento (unidade de dados da camada de transporte) com uma flag SYN pelo cliente ao servidor. O cliente define o número de sequência de segmento como um valor aleatório A.
# SYN+ACK: Em resposta, o servidor responde com um segmento SYN-ACK. O número de reconhecimento (ACKnowledgment) é definido como sendo um a mais que o número de sequência recebido, i.e. A+1, e o número de sequência que o servidor escolhe para o pacote é outro número aleatório B.
# ACK: Finalmente, o cliente envia um ACK de volta ao servidor. O número de sequência é definido ao valor de reconhecimento recebido, i.e. A+1, e o número de reconhecimento é definido como um a mais que o número de sequência recebido, i.e B+1.

Neste ponto, o cliente e o servidor receberam um reconhecimento de conexão. As etapas 1 e 2 estabelecem o parâmetro (número de sequência) de conexão para uma direção e ele é reconhecido. As etapas 2 e 3 estabelecem o parâmetro de conexão (número de sequência) para a outra direção e ele é reconhecido. Com isto, uma comunicação full-duplex é estabelecida.

Tipicamente, numa ligação TCP existe aquele designado de servidor (que abre um socket e espera passivamente por ligações) num extremo, e o cliente no outro. O cliente inicia a ligação enviando um pacote TCP com a flag SYN ativa e espera-se que o servidor aceite a ligação enviando um pacote SYN+ACK. Se, durante um determinado espaço de tempo, esse pacote não for recebido ocorre um timeout e o pacote SYN é reenviado. O estabelecimento da ligação é concluído por parte do cliente, confirmando a aceitação do servidor respondendo-lhe com um pacote ACK.

Durante estas trocas, são trocados números de sequência iniciais (ISN) entre os interlocutores que irão servir para identificar os dados ao longo do fluxo, bem como servir de contador de bytes transmitidos durante a fase de transferência de dados (sessão).

No final desta fase, o servidor inscreve o cliente como uma ligação estabelecida numa tabela própria que contém um limite de conexões, o backlog. No caso do backlog ficar completamente preenchido a ligação é rejeitada ignorando (silenciosamente) todos os subsequentes pacotes SYN.

### Transferência de dados (sessão)
Durante a fase de transferência o TCP está equipado com vários mecanismos que asseguram a confiabilidade e robustez: números de sequência que garantem a entrega ordenada, código detector de erros (checksum) para detecção de falhas em segmentos específicos, confirmação de recepção e temporizadores que permitem o ajuste e contorno de eventuais atrasos e perdas de segmentos.

Como se pode observar pelo cabeçalho TCP, existem permanentemente um par de números de sequência, doravante referidos como número de sequência e número de confirmação (ACKnowledgement). O emissor determina o seu próprio número de sequência e o receptor confirma o segmento usando como número ACK o número de sequência do emissor. Para manter a confiabilidade, o receptor confirma os segmentos indicando que recebeu um determinado número de bytes contíguos. Uma das melhorias introduzidas no TCP foi a possibilidade do receptor confirmar blocos fora da ordem esperada. Esta característica designa-se por selective ACK, ou apenas SACK.

A remontagem ordenada dos segmentos é feita usando os números de sequência, de 32 bit, que reiniciam a zero quando ultrapassam o valor máximo, 2<sup>31</sup>-1, tomando o valor da diferença. Assim, a escolha do ISN torna-se vital para a robustez deste protocolo.

O campo checksum permite assegurar a integridade do segmento. Este campo é expresso em complemento para um consistindo na soma dos valores (em complemento para um) da trama. A escolha da operação de soma em complemento para um deve-se ao fato de esta poder ser calculada da mesma forma para múltiplos desse comprimento - 16 bit, 32 bit, 64 bit, etc - e o resultado, quando encapsulado, será o mesmo. A verificação deste campo por parte do receptor é feita com a recomputação da soma em complemento para um que dará -0 caso o pacote tenha sido recebido intacto.

Esta técnica (checksum), embora muito inferior a outros métodos detectores, como o CRC, é parcialmente compensada com a aplicação do CRC ou outros testes de integridade melhores ao nível da camada 2, logo abaixo do TCP, como no caso do PPP e Ethernet. Contudo, isto não torna este campo redundante: com efeito, estudos de tráfego revelam que a introdução de erro é bastante frequente entre hops protegidos por CRC e que este campo detecta a maioria desses erros.

As confirmações de recepção (ACK) servem também ao emissor para determinar as condições da rede. Dotados de temporizadores, tanto os emissores como receptores podem alterar o fluxo dos dados, contornar eventuais problemas de congestão e, em alguns casos, prevenir o congestionamento da rede. O protocolo está dotado de mecanismos para obter o máximo de performance da rede sem a congestionar — o envio de tramas por um emissor mais rápido que qualquer um dos intermediários (hops) ou mesmo do receptor pode inutilizar a rede. São exemplo a janela deslizante, o algoritmo de início-lento

### Adequação de parâmetros
thumb|esquerda|210px|Neste simples exemplo só está a ser considerada a janela do servidor. O cliente tem a percepção do estado da janela do servidor a cada ACK recebido.
O cabeçalho TCP possui um parâmetro que permite indicar o espaço livre atual do receptor (emissor quando envia a indicação): a janela (ou window). Assim, o emissor fica a saber que só poderá ter em trânsito aquela quantidade de informação até esperar pela confirmação (ACK) de um dos pacotes - que por sua vez trará, com certeza, uma atualização da janela. Curiosamente, a pilha TCP no Windows foi concebida para se auto-ajustar na maioria dos ambientes e, nas versões atuais, o valor padrão é superior em comparação com versões mais antigas.

Porém, devido ao tamanho do campo, que não pode ser expandido, os limites aparentes da janela variam entre 2 e 65535, o que é bastante pouco em redes de alto débito e hardware de alta performance. Para contornar essa limitação é usado uma Opção especial que permite obter múltiplos do valor da janela, chamado de escala da janela, ou TCP window scale; este valor indica quantas vezes o valor da janela, de 16 bit, deve ser operado por deslocamento de bits (para a esquerda) para obter os múltiplos, podendo variar entre 0 e 14. Assim, torna-se possível obter janelas de 1 gigabyte. O parâmetro de escala é definido unicamente durante o estabelecimento da ligação.

### Término da ligação
thumb|210px|Término de conexão.
A fase de encerramento da sessão TCP é um processo de quatro fases, em que cada interlocutor responsabiliza-se pelo encerramento do seu lado da ligação. Quando um deles pretende finalizar a sessão, envia um pacote com a flag FIN ativa, ao qual deverá receber uma resposta ACK. Por sua vez, o outro interlocutor irá proceder da mesma forma, enviando um FIN ao qual deverá ser respondido um ACK.

Pode ocorrer, no entanto, que um dos lados não encerre a sessão. Chama-se a este tipo de evento de conexão semi-aberta. O lado que não encerrou a sessão poderá continuar a enviar informação pela conexão, mas o outro lado não.

## Portas ou serviços
O TCP introduz o conceito de porta tipicamente associado a um serviço (camada aplicação)/ligação específica. Assim, cada um dos intervenientes na conexão dispõe de uma porta associada (um valor de 16 bit) que dificilmente será o mesmo do interlocutor. Alguns serviços (que fazem uso de protocolos específicos) são tipicamente acessíveis em portas fixas, conhecidas como portas bem conhecidas, que são aqueles numerados do 1 ao 1023. Além destas, existem ainda duas gamas de portas, registradas e privadas ou dinâmicas. As portas bem conhecidas são atribuídas pela Internet Assigned Numbers Authority (IANA) e são tipicamente utilizados por processos com direitos de sistema ou super-utilizador. Nestas portas encontram-se em escuta passiva os serviços triviais, como HTTP, SSH, FTP, etc. Todos os protocolos da suite IP se encontram registrados dentro desta gama.

A gama de portas privadas segue regras de atribuição específicas do sistema operativo e serve para abrir ligações a outras máquinas, como surfar na rede, por exemplo.

## Utilização do IP para entrega de dados

O TCP, tal como o UDP, usa o IP para a entrega dos datagramas à rede, e os pontos de acesso à aplicação são identificados por portas acessadas por multiplexação, tal como acontece com o UDP, o que permite múltiplas ligações em cada host. As portas podem ser associadas com uma aplicação (Processo).

O IP trata o pacote TCP como dados e não interpreta qualquer conteúdo da mensagem do TCP, sendo que os dados TCP viajam pela rede em datagramas IP. Os roteadores que interligam as redes apenas verificam o cabeçalho IP, quando fazem o envio dos datagramas. O TCP no destino interpreta as mensagem do protocolo TCP.

## Ver também
* bic-tcp
* Lista de protocolos de redes
* SCTP

## Ligações externas
* [http://www.ietf.org/rfc/rfc793.txt RFC 793]

Categoria:Protocolos de camada de transporte

