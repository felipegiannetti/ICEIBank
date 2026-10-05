# Roteiro do vídeo de apresentação — ICEIBank Sprint 2
### Só o software na tela: o app (`localhost:5173`) e o RabbitMQ Manager. Nenhum terminal, nenhum arquivo de código.

Duração alvo: 9–11 minutos. Tudo que é de backend (relógio vetorial, publisher confirms, DLQ) você **explica falando**, apontando o que aparece no app e no Manager.

---

## Antes de gravar (fora da câmera)

**1. Ferramenta:** use o **OBS Studio** (tem botão **Pausar gravação**, que você vai usar em dois pontos para mexer no terminal sem aparecer). O Xbox Game Bar não pausa.

**2. Estado limpo.** Pare as agências e o auditor (`Ctrl+C`) e suba de novo, para as contas voltarem ao zero. Depois deixe só o app e o Manager visíveis.
- Agências 0, 1, 2 e auditor: os mesmos comandos de antes.
- Frontend: `npm run dev`.

**3. Criar as contas de teste** (na aba T do PowerShell, com `Entrar`/`$seg` definidos como antes):
```powershell
Invoke-RestMethod -Uri "http://localhost:4000/contas" -Method Post -ContentType "application/json" -Body '{"id":0,"nome_aluno":"Ana","senha":"senha123","saldo_inicial":500}'
Invoke-RestMethod -Uri "http://localhost:4001/contas" -Method Post -ContentType "application/json" -Body '{"id":1,"nome_aluno":"Bia","senha":"senha123","saldo_inicial":100}'
Invoke-RestMethod -Uri "http://localhost:4000/contas" -Method Post -ContentType "application/json" -Body '{"id":3,"nome_aluno":"Carlos","senha":"senha123","saldo_inicial":80}'
```

| Conta | Agência | Saldo | Para quê |
|---|---|---|---|
| 0 (Ana) | 0 (porta 4000) | R$ 500 | conta principal da demo |
| 1 (Bia) | 1 (porta 4001) | R$ 100 | destino das transferências entre agências |
| 3 (Carlos) | 0 (porta 4000) | R$ 80 | transferência local e alerta de saldo baixo |

Senha de todas: `senha123`.

**4. Esvaziar a fila de auditoria** no Manager: **Queues → `fila-auditoria` → Purge Messages** (ela acumula mensagens quando o auditor fica desligado).

**5. Abas do navegador.** Deixe só duas: **ICEIBank** (na tela de login) e **RabbitMQ Manager → Queues** (já logado, atualização de 5 s). **Feche** a aba do painel "Instances/AMQP details" do CloudAMQP, para a senha nunca aparecer. Zoom em 110–125%.

**6. Deixe prontos, mas fechados**, os dois comandos que você vai rodar com a gravação **pausada**:
- parar a agência 1 (`Ctrl+C` na aba dela) e subir de novo (`$env:AGENCIA_ID=1` + `python -m app.main`);
- o reprocessamento da DLQ (bloco do Bloco 8).

---

## Bloco 1 — Introdução (30s)

**FAÇA:** Tela de login do ICEIBank.

**FALE:** "Oi, eu sou [seu nome], e este é o Sprint 2 do ICEIBank. No Sprint 1, uma agência creditava a conta de outra por uma chamada REST direta: se a agência de destino estivesse fora do ar, a chamada falhava na hora. Agora essa comunicação é por mensageria assíncrona, com RabbitMQ, e o relógio de Lamport dá lugar ao relógio vetorial."

---

## Bloco 2 — A topologia no RabbitMQ (1 a 1,5 min)

**FAÇA:** Aba do Manager → **Exchanges**, depois **Queues**.

**FALE:** "O broker é um RabbitMQ gerenciado no CloudAMQP. Aqui estão as exchanges: `iceibank.eventos`, do tipo topic e durável, por onde as agências publicam, e `iceibank.dlx`, para mensagens que falham."

**FAÇA:** Aba **Queues**.

**FALE:** "Cada agência tem uma fila de crédito, `fila-agencia-0`, `1` e `2`, ligadas pela routing key `agencia.N.creditar`. Quem publica não sabe quem consome: só a fila da agência de destino recebe. As filas e as mensagens são duráveis, então uma mensagem fica gravada em disco até alguém consumir. Tem também uma fila de confirmações e uma de alertas por agência, uma fila de auditoria e uma dead-letter queue por agência."

---

## Bloco 3 — Transferência entre agências, assíncrona (2 min)

**FAÇA:** Faça login com **conta 0**, agência 0. Vá em **Transferir** → conta de destino `1`, valor `30`.

**FALE, enquanto clica:** "Conta 0 está na agência 0 e a conta 1 na agência 1. Antes, o servidor chamava a outra agência direto; agora ele só publica uma mensagem."

**FAÇA:** Mostre a mensagem **"Publicada — aguardando confirmação…"** e, logo depois, **"Confirmada — o crédito já foi aplicado…"**.

**FALE:** "A resposta só diz que a mensagem foi publicada. O crédito é aplicado do outro lado, e a agência de destino publica uma confirmação de volta, que o app acompanha com polling. Por isso aparece primeiro 'aguardando' e depois 'confirmada'. Essa confirmação de entrega é uma das funcionalidades extras."

**FAÇA:** Volte ao **Transferir**, conta de destino `3`, valor `10` (transferência **local**).

**FALE:** "Esta é local, mesma agência: concluída na hora, sem passar pela mensageria. A decisão local ou remota continua sendo pelo particionamento, `id % 3`."

---

## Bloco 4 — Extrato e relógio vetorial (1,5 min)

**FAÇA:** **Extrato** da conta 0.

**FALE:** "Cada evento carrega um vetor, com uma posição por agência. No Sprint 1 era um número só. As regras: evento local incrementa a própria posição; ao enviar, anexa o vetor; ao receber, faz o máximo posição a posição e incrementa a própria."

**FAÇA:** Aponte a **transferência publicada** e a **confirmada**.

**FALE:** "Reparem como o vetor da confirmação já carrega a posição da agência 1: ela incorporou o que a agência 0 tinha feito. Comparando dois vetores posição a posição, dá para saber com certeza se um evento aconteceu antes do outro, ou se são concorrentes, quando nenhum domina o outro em todas as posições. Com Lamport, dois números diferentes não provavam nada disso."

---

## Bloco 5 — Resiliência: agência fora do ar (3 min) — dois pontos de pausa

**FALE:** "Agora o cenário central: e se a agência de destino estiver fora do ar?"

**FAÇA (⏸ PAUSAR a gravação):** derrube a **agência 1** (`Ctrl+C`). **▶ Retome.**

**FAÇA:** No app, **Transferir** → conta `1`, valor `15`.

**FALE:** "A agência 1 está fora do ar, mas a transferência foi aceita. A mensagem foi publicada e o broker confirmou."

**FAÇA:** Mostre que fica **"Publicada — aguardando confirmação"**. No Manager, **Queues → `fila-agencia-1`**: **Ready = 1**, **Consumers = 0**.

**FALE:** "A mensagem não se perdeu: está retida na fila, durável, esperando a agência 1 voltar. No Sprint 1 essa chamada teria falhado na hora."

**FAÇA (⏸ PAUSAR):** suba a **agência 1** de novo. **▶ Retome.**

**FAÇA:** No Manager, mostre `fila-agencia-1` em **0** e a **`dlq-agencia-1` com 1 mensagem**. No app, abra o **Extrato da conta 0**.

**FALE:** "A agência voltou e recebeu a mensagem, mas as contas ficam só em memória. Ao reiniciar, ela esqueceu a conta 1. O crédito não achou onde ser aplicado, então a mensagem foi para a dead-letter queue em vez de se perder em silêncio, e a agência de origem foi avisada: no extrato aparece a falha do crédito remoto. Esta é a limitação que sobra: a entrega é confiável, mas o estado ainda não é durável. Isso só fecha de verdade com persistência e, para garantir atomicidade entre débito e crédito, com transações distribuídas, no Sprint 4."

---

## Bloco 6 — Recuperando pela DLQ (1,5 min)

**FAÇA:** No app, vá em **Criar conta**, agência **1**, número `1`, nome `Bia`, senha `senha123`, depósito `100`.

**FALE:** "Primeiro recrio a conta que faltava, pelo próprio app."

**FAÇA (⏸ PAUSAR):** rode o reprocessamento da DLQ da agência 1:
```powershell
Invoke-RestMethod -Uri "http://localhost:4001/interno/dlq/reprocessar" -Method Post -Headers $seg
```
**▶ Retome.**

**FAÇA:** No Manager, mostre `dlq-agencia-1` em **0**. No app, faça login com **conta 1** (agência 1): saldo **R$ 115**.

**FALE:** "Reprocessei a fila de mensagens mortas: o crédito pendente foi aplicado, 100 do cadastro mais 15 da transferência. É a funcionalidade extra de dead-letter queue, com um endpoint administrativo protegido por segredo interno."

---

## Bloco 7 — Outras funcionalidades extras (1,5 min)

**FAÇA:** Saia e faça login com **conta 3** (agência 0, saldo R$ 90). **Sacar** `50`. Volte ao **Início**.

**FALE:** "O saldo caiu de 90 para 40, cruzando o limite de alerta de 50. A agência publicou um evento num tópico separado, consumiu o alerta, e o aviso de saldo baixo aparece aqui. Ele só dispara no cruzamento, não a cada saque."

**FAÇA:** No Manager, **Queues → `fila-auditoria`**: mostre **Consumers = 1** e as taxas de mensagens.

**FALE:** "E aqui a fila de auditoria: um consumidor independente das três agências, ligado com routing key `#`, que recebe uma cópia de tudo que é publicado, crédito, confirmações e alertas, e mantém um log central, sem nenhuma mudança nas agências."

---

## Bloco 8 — Decisões de projeto e encerramento (1,5 min)

**FALE** (com o app ou o Manager parado na tela):
- "A topologia é declarada por todas as agências ao subir, de forma idempotente, inclusive a fila das outras agências. Assim, uma mensagem para uma agência que ainda não subiu fica retida em vez de descartada."
- "O publicador usa *publisher confirms*. Se a publicação falha, eu tenho certeza de que a mensagem não saiu, então estorno o débito e o limite diário. Diferente do Sprint 1, onde o resultado de uma chamada podia ficar incerto."
- "O consumidor de mensagens não verifica JWT, porque um token HTTP não viaja numa mensagem AMQP. Quem tem acesso ao broker já é, na prática, uma agência. Num cenário de produção, eu assinaria as mensagens ou daria credenciais separadas por agência."
- "Tudo do Sprint 1 continua funcionando: particionamento, autenticação JWT e o frontend."

**FALE (encerramento):** "Isso cobre mensageria, relógio vetorial, a linha do tempo causal e as quatro funcionalidades extras. No Sprint 3 vem o app em Flutter com eleição de líder, e no Sprint 4 as transações distribuídas, que resolvem a limitação que mostrei. Obrigado!"

**FAÇA:** Pare a gravação.

---

## Checklist rápido
- [ ] Topologia mostrada no Manager (exchanges, filas por agência, DLQ)
- [ ] Transferência entre agências: "publicada" → "confirmada"
- [ ] Transferência local, para contrastar
- [ ] Extrato com vetores explicado (concorrente vs. causal)
- [ ] Agência derrubada: mensagem retida (Ready = 1), agência volta, mensagem vai para a DLQ
- [ ] Limitação explicada (contas em memória → Sprint 4)
- [ ] DLQ reprocessada: saldo da conta 1 = R$ 115
- [ ] Saldo baixo no dashboard e fila de auditoria com 1 consumidor
- [ ] Decisões de projeto (topologia, estorno, consumidor sem JWT)
- [ ] Nenhum terminal, `.env` ou tela "AMQP details" apareceu na gravação
