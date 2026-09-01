# RESPOSTAS - ICEIBank

## Sprint 1

### Parte B - Relogio de Lamport (secao 6.4)

**1. Por que `max(contador_local, timestampRecebido) + 1` ao receber, em vez de adotar o timestamp recebido diretamente?**

Porque o relogio de Lamport precisa preservar a ordem causal em ambas as direcoes: o evento de recebimento tem que ficar depois de todos os eventos locais que ja aconteceram nesta agencia (por isso o `max` com o contador local - se a agencia ja estava em um contador mais alto, adotar cegamente o timestamp recebido faria o novo evento parecer que aconteceu "antes" de eventos locais que na verdade o precederam) e tambem depois do evento de envio na outra ponta (por isso o `+1` sobre o maior dos dois - garante que o recebimento sempre tem um timestamp estritamente maior que o do envio que o causou). Adotar o timestamp recebido diretamente quebraria a primeira garantia; usar so o contador local sem olhar o recebido quebraria a segunda.

**2. Agencia 0 esta no contador 10 e recebe uma mensagem com timestamp 3. Qual o novo valor?**

`max(10, 3) + 1 = 11`. O timestamp recebido (3) e descartado no sentido de nao "voltar" o relogio - ele so serve para eventualmente empurrar o contador para frente, nunca para atrasa-lo. Isso implica que uma agencia que processa muitos eventos rapidamente (contador alto) praticamente nunca tem seu relogio puxado para tras por uma agencia mais lenta: o `max` garante que o relogio de cada processo e monotonicamente crescente, independente da velocidade das outras agencias. Por outro lado, uma agencia lenta (contador baixo) que recebe uma mensagem de uma agencia rapida tem seu contador "empurrado para frente" de uma vez (no exemplo, se fosse o inverso - agencia lenta no 3 recebendo de uma rapida no 10 - ela pularia para 11), o que mostra que o relogio logico nao mede "quantos eventos essa agencia processou", so a ordem causal.

### Parte D - Transferencias (secao 8.3)

**1. Por que a transferencia local nao precisa de `ao_enviar()`/`ao_receber()`, mas a transferencia entre agencias precisa?**

`ao_enviar()`/`ao_receber()` existem para sincronizar o relogio logico quando ha uma mensagem real cruzando a fronteira entre dois processos independentes - e so nesse caso que um processo precisa "aprender" sobre o progresso do relogio do outro. Na transferencia local, debito e credito acontecem dentro do mesmo processo (mesma agencia, mesmo `RelogioLamport`), entao os dois eventos ja compartilham o mesmo contador e `evento_local()` sozinho ja garante que o credito recebe um timestamp maior que o debito - nao ha nenhuma mensagem sendo enviada para fora, entao nao ha nada para "enviar" ou "receber" logicamente. Na transferencia entre agencias, o debito acontece no relogio da agencia de origem e o credito acontece no relogio de outra agencia (outro processo, outro contador); sem `ao_enviar()` no lado de quem chama e `ao_receber()` no lado de quem atende, o relogio da agencia de destino nao teria como saber que o evento de credito precisa ficar causalmente depois do debito que o originou.

**2. Reproduzindo a falha conhecida (agencia de destino derrubada): o saldo da origem foi revertido?**

Nao. O saldo da conta de origem (conta 0, agencia 0) foi debitado normalmente (de 130 para 105) antes da tentativa de chamada REST para a agencia de destino, e como a chamada falhou (`httpx.HTTPError`, agencia 1 fora do ar), a resposta foi 502 mas o debito ja aplicado nao foi desfeito - o `except` so registra o evento `TRANSFERENCIA_FALHOU` no log, sem nenhum rollback do saldo. Em termos de consistencia bancaria, isso e uma violacao real de atomicidade: a operacao "transferir" deveria ser tudo-ou-nada (debitar e creditar juntos, ou nenhum dos dois), mas aqui ela fica parcialmente aplicada - o dinheiro sai da conta de origem e nao chega a lugar nenhum, ate que a agencia de destino volte e algum processo manual (ou, no Sprint 4, um mecanismo automatico) resolva a inconsistencia.

**3. Duas formas possiveis de corrigir isso no Sprint 4 (em alto nivel):**

- **Two-Phase Commit (2PC):** um coordenador (poderia ser a propria agencia de origem) primeiro pergunta a agencia de destino se ela esta pronta para receber o credito ("prepare"), sem aplicar nada ainda; so depois que AMBAS as agencias confirmam que estao prontas e que o debito e o credito podem ser aplicados, o coordenador manda o "commit" para as duas. Se qualquer uma falhar na fase de preparacao, ninguem aplica nada e a transferencia e abortada por completo - nunca fica parcialmente aplicada.
- **Saga (compensacao):** a transferencia e tratada como uma sequencia de passos locais, cada um com uma acao compensatoria associada. O debito e aplicado normalmente, mas se o passo seguinte (creditar na agencia de destino) falhar, um passo de compensacao e disparado automaticamente para desfazer o debito (devolver o valor a conta de origem), em vez de deixar a inconsistencia registrada so no log para resolucao manual como acontece hoje.

### Parte E - Linha do tempo (secao 10.3)

**Observacao (passo 3 da tarefa):** rodando `mesclar_logs.py` depois de criar uma conta em cada uma das 3 agencias (sem nenhuma transferencia entre elas ainda) e depois um deposito independente em duas agencias diferentes, a linha do tempo unificada mostrou:

```
[Lamport 1] (...T00:51:18...) agencia-0 - CRIAR_CONTA {id: 0, ...}
[Lamport 1] (...T00:51:20...) agencia-1 - CRIAR_CONTA {id: 1, ...}
[Lamport 1] (...T00:51:22...) agencia-2 - CRIAR_CONTA {id: 2, ...}
[Lamport 2] (...T00:51:22.383109...) agencia-0 - DEPOSITO {id: 0, valor: 10, ...}
[Lamport 2] (...T00:51:22.383109...) agencia-2 - DEPOSITO {id: 2, valor: 10, ...}
[Lamport 3] (...) agencia-0 - TRANSFERENCIA_DEBITO {id_origem: 0, id_destino: 1, valor: 15}
[Lamport 5] (...) agencia-1 - TRANSFERENCIA_CREDITO_REMOTO {id_conta: 1, valor: 15, origem_agencia: 0}
```

**1. O que significa ver dois eventos com timestamps diferentes, sem saber se um influenciou o outro?**

Significa que a unica garantia que o relogio de Lamport da e em uma direcao so: se A aconteceu antes de B causalmente, entao `timestamp(A) < timestamp(B)`. Ele nao garante a volta - ou seja, ver `timestamp(A) < timestamp(B)` NAO prova que A causou ou influenciou B; pode ser so uma coincidencia da ordem em que os contadores avancaram em processos completamente independentes. Na pratica, isso significa que a linha do tempo unificada por Lamport e util para reconstruir uma ordem *consistente com* a causalidade (nunca inverte uma relacao causal real), mas nao e confiavel para *inferir* causalidade a partir dos numeros sozinhos - seria preciso ir ao conteudo dos eventos (ex.: um `TRANSFERENCIA_CREDITO_REMOTO` citando explicitamente a `origem_agencia` e o `id_origem`) para saber se ha uma relacao real.

**2. Os empates observados (Lamport 1 entre as 3 agencias, Lamport 2 entre agencia-0 e agencia-2) sao causalmente relacionados ou concorrentes? A ordem por `hora_parede` bate com a ordem por Lamport?**

Sao genuinamente concorrentes: as 3 contas foram criadas em 3 processos que, ate aquele momento, nunca haviam trocado nenhuma mensagem entre si - nao ha nenhuma cadeia de `ao_enviar`/`ao_receber` conectando esses eventos, entao nao existe "antes" ou "depois" causal entre eles, so o acaso de todos comecarem do mesmo contador inicial (0) e serem o primeiro evento de cada processo. A `hora_parede` mostra isso claramente: os 3 eventos empatados em Lamport 1 tem horarios de parede bem diferentes (`00:51:18`, `00:51:20`, `00:51:22` - quase 4 segundos de diferenca no mundo real, porque cada `Invoke-RestMethod` foi disparado em sequencia manualmente), enquanto o Lamport os trata como se fossem "do mesmo instante logico". Ja o empate em Lamport 2 (`agencia-0` e `agencia-2`, ambos DEPOSITO) tem `hora_parede` praticamente identica ate o microssegundo (`00:51:22.383109` nos dois) - pura coincidencia de velocidade de execucao, nao prova nem contradiz nada sobre a relacao causal. Ou seja: a ordem por hora de parede NAO bate de forma confiavel com a ordem por Lamport (nem deveria) - Lamport ordena por causalidade logica, hora de parede ordena por relogio fisico, e as duas coisas so coincidem quando processos que se comunicam entre si tambem estao com os relogios fisicos bem sincronizados, o que nao e garantido em um sistema distribuido real.

**3. O relogio de Lamport sozinho seria suficiente para distinguir com certeza "A e B sao concorrentes" de "A aconteceu antes de B"? Por que isso motiva o relogio vetorial?**

Nao. Como mostrado acima, dois eventos com o MESMO timestamp de Lamport sao claramente concorrentes (isso o Lamport ate ajuda a perceber, embora indiretamente, ja que se fossem causalmente relacionados um teria estritamente que ser maior que o outro), mas dois eventos com timestamps DIFERENTES podem ser tanto causalmente relacionados quanto concorrentes - o relogio de Lamport, sozinho, nao tem como diferenciar esses dois casos so olhando os numeros. Isso e exatamente a limitacao que motiva o relogio vetorial (Sprint 2): em vez de um unico contador escalar por processo, cada processo mantem um vetor com um contador para CADA processo do sistema, o que permite comparar dois timestamps e concluir com certeza se um domina o outro em todas as posicoes (causalmente relacionados) ou se nenhum domina o outro em todas as posicoes (genuinamente concorrentes) - uma garantia bidirecional que o relogio escalar de Lamport nao oferece.

### Parte F - Autenticacao JWT (secao 11.3)

_A preencher._

### Parte G - Frontend (secao 12.3)

_A preencher._

### Funcionalidade adicional

_A preencher: descricao das duas funcionalidades escolhidas (historico de transacoes e limite diario configuravel de saque/transferencia) e justificativa da escolha._
