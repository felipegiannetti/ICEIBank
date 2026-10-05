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

**Decisoes de design (exigidas pela secao 11.1):**

- **Credenciais:** `id_conta` + `senha`. A conta E a identidade - nao existe um cadastro de "usuario" separado no sistema, entao reaproveitar o id da conta como identificador de login evita inventar uma tabela paralela de usuarios. A senha e definida no proprio `POST /contas` (que virou, na pratica, o "cadastro").
- **`POST /contas` continua uma rota publica (sem JWT), mesmo a secao 11.1 listando "criar conta" entre as rotas que devem exigir token.** Isso e uma decisao deliberada: com o modelo de credencial escolhido (a propria conta e a identidade), exigir um JWT para criar a primeira conta seria um paradoxo de bootstrap - nao existe nenhum jeito de obter um token antes de existir pelo menos uma conta com senha. `POST /contas` funciona como uma rota de "cadastro" (signup), analoga a de qualquer aplicacao real onde o cadastro nao exige estar logado. Todas as outras rotas que leem ou modificam uma conta ja existente (`GET /contas/{id}`, depositar, sacar, transferir, historico, limite) exigem JWT normalmente.
- **Chamada interna `creditar-remoto`:** usa um cabecalho `X-Internal-Secret` comparado com um segredo compartilhado entre as 3 agencias (mesmo `config.py`), em vez de reaproveitar o JWT de usuario. Justificativa: essa chamada e um hop agencia-para-agencia que acontece depois que o debito ja foi autorizado localmente (o dono da conta de origem ja provou sua identidade via JWT na chamada `/transferencias`); nao existe uma "conta" fazendo a chamada para a outra agencia, entao um JWT de usuario seria a forma errada de modelar essa confianca - e um dominio de confianca diferente (servico-para-servico), tratado como tal.

**1. Diferenca entre autenticacao e autorizacao. A implementacao verifica so uma, ou as duas? Um usuario autenticado consegue sacar de uma conta que nao e dele?**

Autenticacao e confirmar QUEM esta fazendo a chamada (o JWT prova que a pessoa possui as credenciais de uma conta valida); autorizacao e decidir O QUE essa identidade pode fazer. A implementacao verifica as duas, em camadas separadas: a dependencia `get_id_conta_autenticada` (em `security.py`) so autentica (decodifica e valida o token, sem olhar para qual conta esta sendo acessada); a dependencia `exigir_dono` (rotas com `{id_conta}` no path) e a checagem manual em `transferir` (`body.id_origem != id_autenticado`) sao a autorizacao, aplicadas em cima da autenticacao. Com essas duas camadas, um usuario autenticado **nao** consegue sacar, depositar, consultar ou alterar o limite de uma conta que nao e dele - a tentativa retorna `403 Forbidden` (testado no Cenario 3, secao de evidencias). Numa transferencia, ele so pode ser a conta de ORIGEM (o dono decidindo mandar dinheiro), mas pode mandar para qualquer conta de destino - o que faz sentido, ja que "receber uma transferencia" nao deveria exigir autorizacao de quem recebe.

**2. Por que o servidor nao precisa consultar um banco de dados para validar a assinatura de um JWT a cada requisicao? Implicacoes para escalabilidade comparado a sessoes em memoria?**

Porque a assinatura do JWT (HMAC-SHA256 com a `JWT_SECRET_KEY`) e uma funcao matematica que qualquer instancia que conheca o segredo consegue recalcular e comparar localmente, sem nenhuma consulta externa - o token carrega dentro dele mesmo tudo que o servidor precisa saber (`sub`, `iat`, `exp`), so protegido contra adulteracao pela assinatura. Isso e bem diferente de sessoes guardadas em memoria (ou em um banco) no servidor, onde cada requisicao precisaria bater em um armazenamento compartilhado para confirmar que aquela sessao ainda existe e e valida. Em termos de escalabilidade, isso significa que JWT e "stateless": qualquer uma das 3 agencias (ou N replicas futuras de uma mesma agencia) consegue validar o mesmo token sem precisar sincronizar estado de sessao entre elas, o que elimina um ponto de gargalo/dependencia compartilhada - o custo e que, ao contrario de uma sessao em banco, nao da pra revogar um token individual antes do `exp` sem alguma estrutura adicional (ex.: uma blacklist), porque nenhum servidor "sabe" que aquele token deveria parar de ser aceito.

**3. O que aconteceria se a chave secreta do JWT vazasse?**

Qualquer pessoa de posse da chave secreta conseguiria forjar tokens validos para QUALQUER conta (bastaria montar um payload `{"sub": "<id_conta_qualquer>", "exp": <futuro>}` e assinar com a chave vazada), sem precisar saber a senha de ninguem - ja que a validacao do token so confere a assinatura, nao volta a checar a senha original. Isso quebraria completamente a autenticacao do sistema: um atacante poderia se passar por qualquer conta e, dado que a autorizacao inteira depende de "o token e desta conta", teria acesso irrestrito para sacar, transferir e alterar o limite de qualquer conta do banco. A mitigacao e tratar a chave como segredo real (nunca commitar no repositorio - por isso `JWT_SECRET_KEY` vem de variavel de ambiente com um default so de desenvolvimento), e ter um plano de rotacao de chave caso vaze (o que invalidaria todos os tokens emitidos ate entao, forcando reautenticacao geral).

### Parte G - Frontend (secao 12.3)

**Nota tecnica:** a API precisou ganhar `CORSMiddleware` (em `agencia/app/main.py`) para aceitar chamadas vindas de outra origem (o frontend em `http://localhost:5173`, servido pelo Vite, e um processo completamente separado da agencia em `http://localhost:4000`) - sem isso, o navegador bloqueia a requisicao antes mesmo dela chegar na API (erro de preflight). `allow_origins=["*"]` foi usado porque a autenticacao e via header `Authorization: Bearer` (nao cookie), entao nao ha risco de CSRF que a restricao de origem normalmente mitigaria.

**Tela de cadastro:** alem do login, o frontend ganhou uma pagina `/cadastro` que chama `POST /contas` diretamente (rota publica, ver justificativa na Parte F) - o formulario pede numero da conta, nome, senha e deposito inicial opcional, junto com o mesmo seletor de agencia do login (a conta precisa ser criada na agencia correta, regra `id % 3`). Ao concluir, redireciona para `/login` ja com o numero da conta preenchido e uma mensagem de sucesso.

**Identidade visual:** paleta azul claro/roxo/branco (tokens CSS em `index.css` - `--azul`, `--roxo`, `--gradiente-primario`), fonte "Plus Jakarta Sans", cartoes com sombra suave e cantos arredondados, e uma barra lateral de navegacao (`components/AppShell.jsx`, com icones em `components/icons.jsx`) para as paginas autenticadas, inspirada em aplicativos bancarios (saldo em destaque com opcao de ocultar, acoes rapidas com icones, extrato estilizado como lista de transacoes com cor por credito/debito, limite diario com barra de progresso). A barra lateral colapsa para uma faixa horizontal com rolagem em telas estreitas.

**Pagina de perfil:** `/perfil` (acessada pelo avatar/numero da conta na barra lateral) reune nome, numero da conta, agencia atual, saldo e limite diario num só lugar, com atalhos para ajustar o limite, ver o extrato ou sair - nao ha edicao de dados aqui, ja que a API nao expoe nenhum endpoint para alterar nome/senha neste sprint.

**1. Como o frontend "lembra" de reenviar o token em cada requisicao depois do login?**

O token retornado por `/auth/login` e guardado no `localStorage` do navegador (`api/client.js`, funcao `setSessao`), que persiste entre navegacoes de pagina (ao contrario de uma variavel em memoria, que se perderia a cada re-render). Toda chamada feita atraves do wrapper `request()` do `api/client.js` le esse token do `localStorage` e anexa automaticamente o cabecalho `Authorization: Bearer <token>` antes de disparar o `fetch` - as paginas (`DepositoPage`, `SaquePage`, etc.) nunca lidam com o token diretamente, so chamam `api.depositar(...)`, `api.sacar(...)` etc., e o cabecalho e injetado de forma transparente.

**2. Se o token expirar no meio de uma operacao, o que acontece?**

A API responde `401` com `{"erro": "Token expirado."}`. O wrapper `request()` intercepta qualquer resposta `401` numa chamada autenticada e chama `limparSessao()` automaticamente (apaga o token do `localStorage`), alem de lancar um `ApiError` com a mensagem do backend. A pagina que fez a chamada captura esse erro no seu `try/catch` e exibe a mensagem via `ErrorBanner` - ou seja, a pessoa usuaria VE a mensagem de erro (nao e um erro generico silencioso), mas nesta implementacao ela precisa navegar manualmente de volta para `/login` depois disso (o `ProtectedRoute` so bloqueia a entrada em rotas protegidas numa navegacao nova, nao redireciona automaticamente uma pagina ja aberta no meio de uma operacao falha). Isso e uma limitacao conhecida da implementacao atual - o ideal seria o `ApiError` de 401 disparar um redirecionamento automatico para `/login`, o que nao foi implementado neste sprint.

**3. Onde ficam o Model, a View e o Controller no frontend?**

- **Model:** `src/api/client.js` (as funcoes de acesso a API e o estado persistido - token, id da conta, URL da agencia - no `localStorage`) e os dados retornados pela API que cada pagina guarda em `useState` (ex.: `conta`, `eventos`, `limite`).
- **View:** o JSX de `src/pages/*.jsx` e `src/components/*.jsx` - a parte puramente de apresentacao (formularios, tabelas, banners de erro/sucesso).
- **Controller:** os handlers de submit de cada pagina (`aoSubmeter`, `carregarSaldo`, etc.) e o `AuthContext` (`src/context/AuthContext.jsx`), que orquestram a chamada ao Model (`api.*`) e atualizam o estado que a View renderiza.

A separacao e razoavelmente clara porque cada pagina segue o mesmo padrao (estado + handler + JSX no mesmo arquivo), mas nao e uma separacao arquitetural rigida como um MVC de backend - em uma aplicacao React idiomatica, Model/View/Controller tendem a ficar mais entrelacados dentro do proprio componente do que em camadas de arquivos totalmente separadas; o `api/client.js` isolado e o `AuthContext` compartilhado sao os pontos onde essa separacao fica mais explicita.

### Funcionalidade adicional

Foram implementadas duas funcionalidades adicionais (alem do minimo de uma exigido pela secao 2.1), cada uma com commit e evidencia proprios.

#### 1. Historico de transacoes por conta

**O que faz:** `GET /contas/{id}/historico` (protegido por JWT + dono da conta) retorna a lista de eventos registrados para uma conta especifica, do mais recente para o mais antigo, com dois filtros opcionais via query string: `limit` (quantidade maxima de eventos) e `tipo` (ex.: `?tipo=SAQUE` retorna so os saques).

**Como foi implementada:** reaproveita o log de eventos ja existente (`agencia/data/eventos-agencia-{N}.jsonl`) em vez de criar uma estrutura de dados nova. O metodo `RegistroEventos.listar_eventos()` le o `.jsonl` da propria agencia e filtra as linhas cujo campo `detalhes` referencia a conta pedida, em qualquer uma das chaves usadas pelos diferentes tipos de evento (`id`, `id_origem`, `id_destino`, `id_conta`). Isso funciona sem precisar consultar outras agencias: pelo particionamento (secao 5 do roteiro), so a agencia dona de uma conta grava eventos que a referenciam - o debito de uma transferencia e gravado pela agencia de origem, o credito remoto e gravado pela agencia de destino no proprio arquivo dela para a propria conta dela.

**Por que essa escolha:** e a funcionalidade que mais aproveita trabalho ja feito na Parte B (o registro de eventos ja existia para fins de auditoria/linha do tempo) e reforca visualmente, no dia a dia de quem usa o sistema, o mesmo conceito central do sprint - o carimbo de relogio de Lamport em cada operacao - agora exposto como uma feature de produto (extrato) e nao so como log interno.

**Evidencia:** `evidencias/sprint1/extra-historico/funcionalidade-adicional-historico.png`.

#### 2. Limite diario configuravel de saque/transferencia

**O que faz:** cada conta tem um limite diario de saque/transferencia (valor default de `R$ 1000,00`, definido em `config.DEFAULT_LIMITE_DIARIO`), que soma o total sacado + transferido (na ponta de origem) ao longo do dia corrente e bloqueia a operacao quando o total ultrapassaria o limite - mesmo que o saldo em conta seja suficiente. O dono da conta pode consultar (`GET /contas/{id}/limite`) e alterar (`PUT /contas/{id}/limite`) o proprio limite a qualquer momento.

**Como foi implementada:** a `Conta` (`models/conta.py`) ganhou 3 campos: `limite_diario`, `uso_diario` (quanto ja foi usado hoje) e `data_uso_diario` (para saber quando resetar). O metodo `consumir_limite_diario(valor)` reseta `uso_diario` para 0 automaticamente se `data_uso_diario` for de um dia anterior (reset "preguicoso", sem precisar de nenhum scheduler rodando em background), e levanta `LimiteExcedidoError` se `uso_diario + valor > limite_diario`. Esse metodo e chamado exclusivamente no lado do DEBITO - em `sacar` e no debito de `transferir` - nunca em `depositar` nem no credito (local ou remoto) de uma transferencia recebida, ja que o limite existe para conter o quanto uma conta pode *tirar* dinheiro, nao o quanto pode receber. Uma rejeicao por limite gera um evento (`SAQUE_REJEITADO_LIMITE` ou `TRANSFERENCIA_REJEITADA_LIMITE`) carimbado com `relogio.evento_local()`, no mesmo espirito do `TRANSFERENCIA_FALHOU` ja existente na Parte D - toda tentativa relevante fica registrada, mesmo as que nao se concretizam. O saldo so e debitado depois que a checagem de limite passa, entao uma tentativa rejeitada nunca deixa a conta com saldo debitado por engano.

**Por que essa escolha (e por que diario, nao por operacao):** entre as duas variantes sugeridas pelo roteiro (limite por operacao ou por dia), o limite diario foi escolhido por exigir estado que persiste entre chamadas (ao contrario de um limite por operacao, que e uma comparacao sem memoria) - e um exercicio mais realista de regra de negocio com estado, e mais parecido com como bancos de verdade implementam limite de saque diario.

**Evidencia:** `evidencias/sprint1/extra-limite/funcionalidade-adicional-limite.png`.

## Sprint 2

### Nota de transparencia sobre uso de IA (exigida pelo roteiro)

Este sprint foi desenvolvido com apoio extensivo do Claude (Anthropic, modelo Sonnet 5), usado nao so para rascunho/revisao, mas para a implementacao completa do backend (relogio vetorial, mensageria com RabbitMQ/pika, os 4 extras) e das mudancas no frontend, a partir do roteiro fornecido e de decisoes de design discutidas e aprovadas ao longo do processo (ex.: qual biblioteca de RabbitMQ usar, quais das 4 sugestoes de funcionalidade adicional implementar, como tratar o estorno de saldo quando a publicacao falha). Todo o codigo gerado foi executado e testado de ponta a ponta contra um RabbitMQ real (Docker local, com topologia validada via RabbitMQ Manager) antes de ser aceito - inclusive dois bugs reais foram encontrados e corrigidos durante essa validacao (ver Parte C e a funcionalidade de dead-letter queue abaixo). Declaro estar em condicoes de explicar e defender qualquer trecho entregue.

### Parte B - Relogio vetorial (secao 6.4)

**1. Com 3 agencias, o vetor tem 3 posicoes. Se o sistema crescesse para 10, o que aconteceria com o tamanho de cada vetor? Isso e um problema?**

O vetor cresce linearmente com o numero de agencias (processos) do sistema - com 10 agencias, cada vetor (e cada mensagem que carrega um, via `ao_enviar`/`ao_receber`) passaria a ter 10 posicoes em vez de 3. Isso nao e um problema de corretude - o algoritmo funciona perfeitamente para qualquer N -, mas e um problema real de escalabilidade: o overhead de espaco cresce O(N) por mensagem e por evento gravado no log, o que fica caro (ou proibitivo) em sistemas com centenas ou milhares de processos - exatamente o cenario que motivou os artigos originais de Fidge e Mattern a proporem otimizacoes. Na pratica, sistemas de grande escala evitam carregar um vetor completo em toda mensagem usando aproximacoes (ex.: relogios de Lamport combinados com particionamento, dotted version vectors, ou rastrear so um subconjunto de processos "interessados" em vez do sistema inteiro).

**2. `V1 = [3, 1, 0]` e `V2 = [3, 2, 0]`: qual aconteceu primeiro, ou sao concorrentes?**

V1 aconteceu ANTES de V2. Comparando posicao a posicao: `3<=3`, `1<=2`, `0<=0` - V1 e menor ou igual a V2 em TODA posicao, e os vetores sao diferentes, entao V1 dominou. (Confirmado pelo teste automatizado `test_antes` em `tests/test_relogio_vetorial.py`.)

**3. `V1 = [3, 1, 0]` e `V2 = [1, 3, 0]`: qual aconteceu primeiro, ou sao concorrentes?**

Sao CONCORRENTES. Nem V1 domina V2 (`3 > 1` na posicao 0 falha a condicao `V1<=V2`), nem V2 domina V1 (`3 > 1` na posicao 1 falha a condicao `V2<=V1`) - nenhum dos dois "viu" tudo que o outro tinha visto, entao nenhum pode ter causado o outro. (Confirmado pelo teste `test_concorrentes`.)

### Parte C - Publish/Subscribe entre agencias (secao 7.5)

**1. No passo 4 (agencia volta), o que aconteceu exatamente quando ela reconectou? A mensagem "sumiu" por falha da mensageria, ou por outro motivo?**

Reproduzi esse cenario com um RabbitMQ real (Docker local): derrubei a agencia 1, transferi da conta 0 para a conta 1 (resposta 200, mensagem publicada mesmo com a agencia 1 fora do ar), confirmei no RabbitMQ Manager que a mensagem ficou retida (`fila-agencia-1` com 1 mensagem *Ready*, 0 consumidores), e so entao subi a agencia 1 de novo **sem recriar a conta 1**. A mensagem NAO sumiu por falha da mensageria - pelo contrario, o RabbitMQ funcionou exatamente como esperado: a mensagem foi entregue automaticamente assim que o consumidor da agencia 1 reconectou. O problema foi outro: como as contas vivem so em memoria (um dict, sem persistencia em disco), quando o processo da agencia 1 morreu ele "esqueceu" a conta 1 - ela deixou de existir. Quando a mensagem finalmente chegou, o handler `aplicar_credito()` procurou a conta 1, nao encontrou, registrou o evento `CREDITO_REMOTO_FALHOU`, publicou uma confirmacao de falha de volta para a agencia de origem (que registrou `CREDITO_FALHOU`), e a propria mensagem foi rejeitada com `nack(requeue=False)`, caindo na dead-letter queue (`dlq-agencia-1`) em vez de ficar tentando reprocessar para sempre.

**2. Compare com o Sprint 1 (chamada REST direta): o que melhorou, o que continua sendo um problema em aberto?**

No Sprint 1, se a agencia de destino estivesse fora do ar no momento exato da chamada REST, a chamada falhava na hora (erro de conexao) e a mensagem era perdida definitivamente - nao havia nenhuma retencao ou retry. Agora, com RabbitMQ, a mensagem NUNCA se perde por indisponibilidade temporaria - ela fica gravada em disco pelo broker (fila durable + mensagem persistente, `delivery_mode=2`) ate alguem consumi-la, nao importa quanto tempo a agencia fique fora do ar. Isso resolve de verdade o problema da camada de transporte. O que continua em aberto e a diferenca entre "a mensagem nao se perde" e "o sistema esta correto": como o ESTADO da aplicacao (quais contas existem) ainda nao e durable, uma mensagem garantidamente entregue pode chegar a um destino que nao tem mais onde aplica-la. Ou seja, resolvemos a confiabilidade da entrega, mas nao a persistencia do estado - e essa lacuna so fecha de verdade com um banco de dados persistente (fora do escopo deste sprint) e, para garantir atomicidade completa entre debito e credito mesmo sob falha, com uma transacao distribuida de verdade (2PC/Saga), o assunto do Sprint 4.

**3. O consumidor de mensagens processa creditos sem verificar token JWT. Isso e um problema de seguranca?**

Em principio, sim - e uma superficie de ataque real: hoje, qualquer processo que consiga se conectar na mesma instancia RabbitMQ (com a `RABBITMQ_URL`) pode publicar diretamente uma mensagem com routing key `agencia.N.creditar` e a agencia de destino aplica o credito sem nenhuma verificacao de quem mandou aquilo - efetivamente "dinheiro de graca", sem nenhum debito correspondente em lugar nenhum. No ambiente de desenvolvimento (Docker local com `guest/guest`, ou uma instancia CloudAMQP pessoal cuja URL so o aluno conhece), o risco pratico e baixo porque ter acesso ao proprio broker ja equivale, na pratica, a "ser uma agencia" do sistema. Mas numa arquitetura de producao real isso seria um problema genuino, e a mitigacao seria parecida com a decisao tomada no Sprint 1 para a chamada REST direta entre agencias (o `X-Internal-Secret`): incluir na propria mensagem alguma forma de autenticacao/assinatura (ex.: um HMAC assinado com um segredo compartilhado so entre agencias) que o handler de credito verificasse antes de aplicar, ou isolar o acesso ao broker via rede/credenciais por agencia (cada agencia com seu proprio usuario RabbitMQ, com permissao de publicar so nas routing keys que faz sentido ela publicar).

### Parte D - Linha do tempo causal (secao 8.3)

**1. O que no relogio vetorial torna essa comparacao confiavel, algo que o Lamport nao permitia?**

O relogio de Lamport reduz toda a historia causal de um evento a um unico numero escalar - comparando dois numeros, so da para concluir "um e maior" ou "sao iguais", nunca se um realmente descende causalmente do outro ou se e so uma coincidencia de contagem entre processos independentes. O relogio vetorial, em vez de colapsar tudo num numero, preserva uma "impressao digital" separada do progresso de CADA processo (uma posicao por agencia). Comparar dois vetores posicao a posicao permite verificar a condicao completa "V1 domina V2 em TODAS as posicoes" - o que so e verdade se V1 realmente incorporou (via as regras de `ao_enviar`/`ao_receber`) tudo que V2 tinha visto ate aquele momento. E exatamente essa comparacao completa, e nao parcial, que garante detectar concorrencia com certeza: se nenhum vetor domina o outro em todas as posicoes, e matematicamente impossivel que um tenha causado o outro.

**2. Encontre, no seu teste, um par de eventos classificado como concorrente. Faz sentido?**

No meu teste, o script apontou (entre varios outros) o par `[agencia-0] CRIAR_CONTA ([1,0,0])` x `[agencia-1] CRIAR_CONTA ([0,1,0])`. Faz todo sentido: sao o primeiro evento de cada uma dessas duas agencias, criadas por dois comandos `Invoke-RestMethod` disparados manualmente em sequencia rapida, sem nenhuma mensagem trocada entre as duas agencias ate aquele ponto - nenhuma das duas "sabe" que a outra existe nesse momento, entao nao ha absolutamente nenhuma relacao de causa e efeito entre a criacao de uma conta e a da outra. Ja o par formado pelo debito (`TRANSFERENCIA_PUBLICADA`, vetor `[3,0,0]`) e o credito remoto correspondente (`TRANSFERENCIA_CREDITO_REMOTO`, vetor `[3,2,0]`) da mesma transferencia **nao** aparece entre os concorrentes - o `--causais` confirma que a relacao entre os dois e sempre ANTES, como esperado (o debito e a causa direta do credito).

**3. O algoritmo de comparacao e O(n^2). Isso seria um problema com milhoes de eventos? Como tornar mais escalavel?**

Sim, seria um problema serio - com 1 milhao de eventos, comparar todos os pares significa ~5*10^11 comparacoes, inviavel de rodar do zero a cada analise. Para escalar, algumas ideias em alto nivel: (1) nao comparar todos os pares "as cegas" - restringir a analise a eventos dentro de uma janela de tempo relevante, ja que eventos muito distantes no tempo real quase sempre ja tem uma ordem clara; (2) indexar eventos por processo e usar a monotonicidade de cada componente do vetor para podar comparacoes obviamente decididas sem processar o vetor inteiro; (3) processar de forma incremental/streaming (mesclar_logs.py hoje sempre rele e reprocessa o historico inteiro do zero), guardando o resultado de comparacoes ja feitas em vez de refazer tudo a cada execucao; (4) em sistemas reais de grande escala, normalmente nao se faz uma varredura O(n^2) exaustiva - usam-se estruturas de dados especializadas (bancos orientados a eventos, CRDTs) que ja mantem a ordem parcial organizada internamente.

### Funcionalidade adicional (Sprint 2)

O roteiro deste sprint exige pelo menos uma funcionalidade adicional (secao 2.1); foram implementadas as **4** sugeridas no roteiro, cada uma com commit e evidencia proprios.

#### 1. Dead-letter queue (DLQ)

**O que faz:** quando um credito remoto falha porque a conta de destino nao existe (o cenario da Parte C - agencia reiniciou e perdeu o estado em memoria), a mensagem correspondente e desviada para uma fila separada (`dlq-agencia-N`) em vez de ser descartada silenciosamente. Dois endpoints internos (protegidos pelo mesmo `X-Internal-Secret` do Sprint 1): `GET /interno/dlq` mostra (sem remover) as mensagens paradas, e `POST /interno/dlq/reprocessar` tenta reaplicar cada uma - util depois de recriar a conta que faltava.

**Como foi implementada:** a `fila-agencia-N` (a fila normal de credito) e declarada com os argumentos `x-dead-letter-exchange`/`x-dead-letter-routing-key` apontando para uma segunda exchange (`iceibank.dlx`) e uma fila `dlq-agencia-N`. Quando o handler `aplicar_credito()` decide rejeitar a mensagem (`nack(requeue=False)`, porque a conta nao existe), o proprio RabbitMQ redireciona automaticamente a mensagem para a DLQ - nenhum codigo especifico de "mover para a DLQ" precisou ser escrito, so a topologia correta. O reprocessamento reaproveita o MESMO handler `aplicar_credito()` usado pelo consumidor normal, garantindo que o comportamento (incluindo o dedupe por `id_transferencia` e a confirmacao publicada de volta) seja identico nos dois caminhos.

**Por que essa escolha:** e a funcionalidade que mais fecha o ciclo da limitacao conhecida descrita na propria secao 2 do roteiro (agencia reinicia, perde o estado, credito nao encontra onde ser aplicado) - em vez de so documentar o problema, ele fica com um caminho de recuperacao real.

**Bug real encontrado e corrigido durante o teste:** a primeira versao de `espiar_fila()`/`reprocessar_fila()` devolvia cada mensagem a fila (`nack` com `requeue=True`) uma a uma, dentro do mesmo loop de leitura - como so havia 1 mensagem de verdade na fila de teste, a mesma mensagem era lida e devolvida repetidamente ate o limite do loop, aparecendo 20 vezes duplicada na resposta de `GET /interno/dlq`. Corrigido consultando antes, via `queue_declare(passive=True)`, quantas mensagens existem de verdade, e so devolvendo todas ao final (depois de ler exatamente essa quantidade).

**Evidencia:** `evidencias/sprint2/extra-dlq/funcionalidade-adicional-dlq.png`.

#### 2. Confirmacao de entrega

**O que faz:** depois que a agencia de destino aplica (ou falha em aplicar) um credito remoto, ela publica um segundo evento de confirmacao de volta para a agencia de origem, que atualiza o status da transferencia (`PENDENTE` -> `CONFIRMADA` ou `FALHOU`) e registra isso no proprio log. O frontend consulta `GET /transferencias/{id_transferencia}` em polling (a cada 1s, por ate 15s) ate a transferencia sair de `PENDENTE`, mostrando "publicada - aguardando confirmacao" e depois "confirmada" (ou o motivo da falha) sem o usuario precisar atualizar a pagina.

**Como foi implementada:** a agencia de origem publica na routing key `agencia.<destino>.creditar` e passa a **tambem** consumir sua propria fila `fila-confirmacoes-agencia-N`, ligada a routing key `agencia.N.confirmacao`. A agencia de destino, apos processar o credito (com sucesso ou nao), publica de volta nessa routing key com `{sucesso, motivo, vetor_envio}` - o vetor viaja junto, entao a origem executa `ao_receber()` ao processar a confirmacao, fechando o ciclo causal completo (debito -> publicacao -> credito remoto -> confirmacao) no relogio vetorial.

**Por que essa escolha:** sem isso, a resposta HTTP de uma transferencia entre agencias vira so "foi publicada", e o usuario nunca saberia se o dinheiro realmente chegou (ou por que nao chegou) sem ir olhar o extrato da outra agencia manualmente - a confirmacao fecha esse ciclo de forma genuinamente assincrona, sem o cliente precisar ficar re-consultando as duas agencias.

**Evidencia:** `evidencias/sprint2/extra-confirmacao/funcionalidade-adicional-confirmacao.png`.

#### 3. Fila de auditoria

**O que faz:** um processo independente das 3 agencias (`python auditor.py`, nao participa do particionamento nem do relogio vetorial) escuta TUDO que e publicado na exchange `iceibank.eventos` - credito remoto, confirmacoes e alertas de saldo baixo, de qualquer agencia - e mantem um log central (`data/auditoria.jsonl`), alem de imprimir cada evento no console.

**Como foi implementada:** a exchange principal e do tipo *topic*, entao uma fila ligada com a routing key coringa `#` recebe copia de toda mensagem publicada nela, seja qual for a routing key especifica - o auditor nao precisa saber de antemao quais routing keys existem hoje ou vao existir no futuro (uma quinta funcionalidade que publicasse em outra routing key qualquer ja seria capturada automaticamente, sem alterar o auditor).

**Por que essa escolha:** e a demonstracao mais direta do padrao Publish/Subscribe do roteiro - "quem publica nao sabe (nem precisa saber) quem vai consumir" -, mostrando um consumidor inteiramente novo entrando no sistema sem qualquer mudanca nas 3 agencias existentes.

**Evidencia:** `evidencias/sprint2/extra-auditoria/funcionalidade-adicional-auditoria.png`.

#### 4. Notificacao de saldo baixo

**O que faz:** sempre que um debito (saque, ou o lado de origem de uma transferencia) faz o saldo de uma conta cruzar para baixo de um limite configuravel (`ICEI_SALDO_BAIXO_LIMITE`, default R$ 50), a agencia publica um alerta num topico separado (`alerta.saldo_baixo.N`). O dashboard do frontend mostra um aviso visivel com o saldo atual e o limite.

**Como foi implementada:** o alerta so dispara no CRUZAMENTO da fronteira (`saldo_antes >= limite > saldo_depois`), nunca a cada operacao - assim uma conta que ja esta abaixo do limite nao gera um alerta novo a cada saque subsequente. A propria agencia que publica o alerta tambem o consome (fila `fila-alertas-agencia-N`), guardando em memoria por conta; `GET /contas/{id}/notificacoes` expoe isso ao frontend. Mesmo sendo a mesma agencia publicando e consumindo, o alerta continua sendo uma mensagem de verdade (nao uma chamada de funcao direta) - e por isso que o auditor (funcionalidade 3) tambem consegue ve-lo sem qualquer acoplamento com essa funcionalidade.

**Por que essa escolha:** e a funcionalidade que mais reaproveita a infraestrutura de mensageria ja construida (mesma exchange, mesmo padrao de publicar/consumir) para resolver um problema de produto genuino (avisar a pessoa usuaria antes que o saldo acabe), sem precisar de nenhuma peca de infraestrutura nova.

**Evidencia:** `evidencias/sprint2/extra-saldo-baixo/funcionalidade-adicional-saldo-baixo.png`.

### Evidencias do Sprint 2 (indice)

Todos os prints foram feitos com a aplicacao rodando contra um RabbitMQ gerenciado no CloudAMQP (3 agencias + frontend + auditor), com `Get-Date` visivel no terminal ou a hora do sistema na barra de tarefas.

| Pasta | Arquivo | O que mostra |
|---|---|---|
| `parte-a-rabbitmq/` | `rabbitmq-topologia-exchanges.png` | Exchanges `iceibank.eventos` e `iceibank.dlx` (topic, duraveis) no RabbitMQ Manager |
| `parte-a-rabbitmq/` | `rabbitmq-topologia-filas.png` | Filas por agencia (`fila-agencia-N`, com DLX/DLK), DLQs, confirmacoes, alertas e auditoria |
| `parte-c-mensageria/` | `transferencia-assincrona.png` | Transferencia 0 -> 1 publicada (`PENDENTE`) e depois `CONFIRMADA`; logs das duas agencias com os vetores; saldo da conta 1 = 130 |
| `parte-c-mensageria/` | `resiliencia-fila-manager.png` | Agencia 1 fora do ar: `fila-agencia-1` retem 1 mensagem (*Ready*) |
| `parte-c-mensageria/` | `resiliencia-fila.png` | Transferencia respondida com 200 (`PENDENTE`) e, quando a agencia 1 volta, `CREDITO_REMOTO_FALHOU` (conta nao encontrada) |
| `parte-c-mensageria/` | `regressao-frontend.png` | Extrato no frontend (login por JWT) com o vetor de cada evento |
| `parte-d-linha-do-tempo/` | `linha-do-tempo-causal.png` | `mesclar_logs.py --causais`: pares concorrentes entre agencias e pares debito -> credito classificados como `ANTES` |
| `extra-dlq/` | `funcionalidade-adicional-dlq.png` | `GET /interno/dlq` com a mensagem parada em `dlq-agencia-1` |
| `extra-dlq/` | `funcionalidade-adicional-dlq-reprocessar.png` | Conta recriada, `POST /interno/dlq/reprocessar` (`aplicadas: 1`) e saldo da conta 1 = 115 |
| `extra-confirmacao/` | `funcionalidade-adicional-confirmacao.png` | Frontend exibindo "Confirmada — o credito ja foi aplicado na conta de destino" |
| `extra-auditoria/` | `funcionalidade-adicional-auditoria.png` | `auditor.py` capturando `agencia.1.creditar` e `agencia.0.confirmacao` |
| `extra-saldo-baixo/` | `funcionalidade-adicional-saldo-baixo.png` | Dashboard com o aviso de saldo baixo (R$ 40,00, abaixo do limite de R$ 50,00) |
