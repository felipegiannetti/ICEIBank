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

**Evidencia:** `evidencias/sprint1/funcionalidade-adicional-historico.png`.

#### 2. Limite diario configuravel de saque/transferencia

**O que faz:** cada conta tem um limite diario de saque/transferencia (valor default de `R$ 1000,00`, definido em `config.DEFAULT_LIMITE_DIARIO`), que soma o total sacado + transferido (na ponta de origem) ao longo do dia corrente e bloqueia a operacao quando o total ultrapassaria o limite - mesmo que o saldo em conta seja suficiente. O dono da conta pode consultar (`GET /contas/{id}/limite`) e alterar (`PUT /contas/{id}/limite`) o proprio limite a qualquer momento.

**Como foi implementada:** a `Conta` (`models/conta.py`) ganhou 3 campos: `limite_diario`, `uso_diario` (quanto ja foi usado hoje) e `data_uso_diario` (para saber quando resetar). O metodo `consumir_limite_diario(valor)` reseta `uso_diario` para 0 automaticamente se `data_uso_diario` for de um dia anterior (reset "preguicoso", sem precisar de nenhum scheduler rodando em background), e levanta `LimiteExcedidoError` se `uso_diario + valor > limite_diario`. Esse metodo e chamado exclusivamente no lado do DEBITO - em `sacar` e no debito de `transferir` - nunca em `depositar` nem no credito (local ou remoto) de uma transferencia recebida, ja que o limite existe para conter o quanto uma conta pode *tirar* dinheiro, nao o quanto pode receber. Uma rejeicao por limite gera um evento (`SAQUE_REJEITADO_LIMITE` ou `TRANSFERENCIA_REJEITADA_LIMITE`) carimbado com `relogio.evento_local()`, no mesmo espirito do `TRANSFERENCIA_FALHOU` ja existente na Parte D - toda tentativa relevante fica registrada, mesmo as que nao se concretizam. O saldo so e debitado depois que a checagem de limite passa, entao uma tentativa rejeitada nunca deixa a conta com saldo debitado por engano.

**Por que essa escolha (e por que diario, nao por operacao):** entre as duas variantes sugeridas pelo roteiro (limite por operacao ou por dia), o limite diario foi escolhido por exigir estado que persiste entre chamadas (ao contrario de um limite por operacao, que e uma comparacao sem memoria) - e um exercicio mais realista de regra de negocio com estado, e mais parecido com como bancos de verdade implementam limite de saque diario.

**Evidencia:** `evidencias/sprint1/funcionalidade-adicional-limite.png`.
