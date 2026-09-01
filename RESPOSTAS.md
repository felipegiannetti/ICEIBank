# RESPOSTAS - ICEIBank

## Sprint 1

### Parte B - Relogio de Lamport (secao 6.4)

**1. Por que `max(contador_local, timestampRecebido) + 1` ao receber, em vez de adotar o timestamp recebido diretamente?**

Porque o relogio de Lamport precisa preservar a ordem causal em ambas as direcoes: o evento de recebimento tem que ficar depois de todos os eventos locais que ja aconteceram nesta agencia (por isso o `max` com o contador local - se a agencia ja estava em um contador mais alto, adotar cegamente o timestamp recebido faria o novo evento parecer que aconteceu "antes" de eventos locais que na verdade o precederam) e tambem depois do evento de envio na outra ponta (por isso o `+1` sobre o maior dos dois - garante que o recebimento sempre tem um timestamp estritamente maior que o do envio que o causou). Adotar o timestamp recebido diretamente quebraria a primeira garantia; usar so o contador local sem olhar o recebido quebraria a segunda.

**2. Agencia 0 esta no contador 10 e recebe uma mensagem com timestamp 3. Qual o novo valor?**

`max(10, 3) + 1 = 11`. O timestamp recebido (3) e descartado no sentido de nao "voltar" o relogio - ele so serve para eventualmente empurrar o contador para frente, nunca para atrasa-lo. Isso implica que uma agencia que processa muitos eventos rapidamente (contador alto) praticamente nunca tem seu relogio puxado para tras por uma agencia mais lenta: o `max` garante que o relogio de cada processo e monotonicamente crescente, independente da velocidade das outras agencias. Por outro lado, uma agencia lenta (contador baixo) que recebe uma mensagem de uma agencia rapida tem seu contador "empurrado para frente" de uma vez (no exemplo, se fosse o inverso - agencia lenta no 3 recebendo de uma rapida no 10 - ela pularia para 11), o que mostra que o relogio logico nao mede "quantos eventos essa agencia processou", so a ordem causal.

### Parte D - Transferencias (secao 8.3)

_A preencher._

### Parte E - Linha do tempo (secao 10.3)

_A preencher._

### Parte F - Autenticacao JWT (secao 11.3)

_A preencher._

### Parte G - Frontend (secao 12.3)

_A preencher._

### Funcionalidade adicional

_A preencher: descricao das duas funcionalidades escolhidas (historico de transacoes e limite diario configuravel de saque/transferencia) e justificativa da escolha._
