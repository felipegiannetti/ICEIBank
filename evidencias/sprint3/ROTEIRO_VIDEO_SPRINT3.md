# Roteiro do vídeo de apresentação — ICEIBank Sprint 3
### Na tela: o emulador/dispositivo com o app Flutter, 3 terminais das agências e (quando precisar) o PowerShell. Tudo que é de backend puro (algoritmo de Bully) você **explica falando**, apontando os logs no terminal.

Duração alvo: 9–12 minutos. Grave com o **OBS Studio** (botão **Pausar gravação**, usado nos pontos em que você vai derrubar/subir uma agência ou trocar de janela sem isso aparecer gravado).

---

## Antes de gravar (fora da câmera)

**1. Estado limpo.** Suba as 3 agências (Sprint 1/2, RabbitMQ no ar) e confirme no terminal de cada uma que a eleição inicial converge para a agência 2 (`Invoke-RestMethod http://localhost:400{0,1,2}/bully/lider`).

**2. Emulador/dispositivo com o app Flutter** já instalado e aberto na tela de login (ver `app_mobile/README.md` para gerar as pastas de plataforma e rodar `flutter run` pela primeira vez).

**3. Conta de teste** criada em alguma agência (reaproveite uma das contas dos sprints anteriores, ou crie uma nova):
```powershell
Invoke-RestMethod -Uri "http://localhost:4000/contas" -Method Post -ContentType "application/json" -Body '{"id":0,"nome_aluno":"Ana","senha":"senha123","saldo_inicial":500}'
```

**4. Janelas visíveis:** emulador/dispositivo (espelhado na tela, se for um aparelho físico), e os 3 terminais das agências lado a lado (ou minimizados, só para pausar e derrubar um deles quando precisar).

---

## Bloco 1 — Introdução (30s)

**FAÇA:** Tela de login do app Flutter.

**FALE:** "Oi, eu sou [seu nome], e este é o Sprint 3 do ICEIBank. Até aqui, as 3 agências eram pares - nenhuma tinha autoridade sobre as outras. Agora elas elegem uma líder entre si usando o algoritmo de Bully, e nasce o primeiro cliente mobile do projeto: este app Flutter, que reaproveita a mesma API REST e já mostra a líder atual na tela."

---

## Bloco 2 — Eleição inicial (1,5 min)

**FAÇA:** Mostre os 3 terminais das agências já rodando, com os logs de `ELEICAO_INICIADA`/`TORNOU_LIDER`/`LIDER_ANUNCIADO` visíveis (role para cima se precisar).

**FALE:** "Ao subir, cada agência dispara sua própria eleição: manda uma mensagem para quem tem ID maior que o seu. Se ninguém responder, ela mesma vence e avisa as outras. Reparem que mais de uma agência pode se declarar líder por um instante - isso é esperado, é só o sistema convergindo; o resultado final é sempre a agência de maior ID entre as ativas, que aqui é a agência 2."

**FAÇA:** Rode nas 3 agências (ou mostre já rodado):
```powershell
Invoke-RestMethod -Uri "http://localhost:4000/bully/lider" -Method Get
Invoke-RestMethod -Uri "http://localhost:4001/bully/lider" -Method Get
Invoke-RestMethod -Uri "http://localhost:4002/bully/lider" -Method Get
```

**FALE:** "As 3 concordam: a líder é a agência 2." *(print para `eleicao-inicial.png`)*

---

## Bloco 3 — App Flutter: fluxo bancário (2 min)

**FAÇA:** Faça login no app (conta 0, senha `senha123`).

**FALE:** "O app reaproveita exatamente a mesma API do frontend web: login por JWT, consulta de saldo, depósito, saque e transferência."

**FAÇA:** Deposite um valor, depois saque, depois faça uma transferência local (entre contas da mesma agência) e uma entre agências. Mostre o tratamento de erro tentando, por exemplo, um saque maior que o saldo.

**FALE:** "Erros da API aparecem direto na tela - saldo insuficiente, conta não encontrada, token expirado - igual ao frontend web."

---

## Bloco 4 — Painel de liderança no app (1,5 min)

**FAÇA:** Abra o painel de liderança (ícone no topo da tela principal).

**FALE:** "Este painel consulta `/bully/lider` a cada 5 segundos. Mostra a líder atual, quais das 3 agências estão respondendo agora - essa é uma das funcionalidades extras -, e o histórico de trocas de liderança, outra funcionalidade extra."

**FAÇA:** Aponte o indicador de agências ativas (bolinha verde/vermelha por agência) e a lista de histórico. *(print para `app-lider-atual.png`)*

**FAÇA:** Toque em "Forçar nova eleição" (terceira funcionalidade extra).

**FALE:** "Esse botão dispara uma eleição manualmente, sem precisar derrubar nenhuma agência - útil para demonstrar o algoritmo sob controle."

---

## Bloco 5 — Failover automático, com o app aberto (2 min) — um ponto de pausa

**FALE:** "Agora o ponto central: o que acontece se a líder cair de verdade?"

**FAÇA (⏸ PAUSAR a gravação):** derrube o terminal da **agência 2** (líder atual, `Ctrl+C`). **▶ Retome.**

**FAÇA:** Sem tocar em nada no app, espere alguns segundos (o heartbeat do backend roda a cada 3s por padrão) e aponte a tela do painel de liderança atualizando sozinha.

**FALE:** "Sem eu reiniciar o app nem atualizar a tela manualmente, o painel percebe a troca: a nova líder passa a ser a agência 1, a de maior ID entre as duas que sobraram." *(print do antes/depois para `app-failover.png`, e também `failover.png` olhando o terminal/PowerShell)*

**FAÇA:** No terminal das agências restantes, aponte os logs `LIDER_NAO_RESPONDEU` e a nova `TORNOU_LIDER`.

**FALE:** "No log: a agência 1 percebeu que a líder não respondeu, esqueceu ela e iniciou uma nova eleição - sem nenhuma intervenção manual."

---

## Bloco 6 — Histórico de liderança (1 min)

**FAÇA (⏸ PAUSAR, se precisar trocar de janela):** rode:
```powershell
cd agencia
.\.venv\Scripts\python.exe historico_lideranca.py
```
**▶ Retome.**

**FALE:** "Este script lê os logs das 3 agências e reconstrói a linha do tempo de lideranças - a mesma eleição inicial, e depois a troca que acabamos de ver." *(print para `historico-lideranca.png`)*

---

## Bloco 7 — Sincronização offline-first: o conflito no backend (1,5 min)

**FAÇA:** Consulte o saldo da conta pelo PowerShell e guarde o `vetor_atual`:
```powershell
$token = (Invoke-RestMethod -Uri "http://localhost:4000/auth/login" -Method Post -ContentType "application/json" -Body '{"id_conta":0,"senha":"senha123"}').access_token
$headers = @{ Authorization = "Bearer $token" }
$saldo = Invoke-RestMethod -Uri "http://localhost:4000/contas/0" -Headers $headers
$vetorAntigo = $saldo.vetor_atual
```

**FAÇA:** Faça um depósito direto (simulando uma mudança "enquanto o app estava offline"):
```powershell
Invoke-RestMethod -Uri "http://localhost:4000/contas/0/depositar" -Method Post -Headers $headers -ContentType "application/json" -Body '{"valor": 10}'
```

**FAÇA:** Tente sincronizar usando o `$vetorAntigo` (desatualizado):
```powershell
$corpo = @{ tipo = "DEPOSITO"; valor = 50; vetor_conhecido = $vetorAntigo } | ConvertTo-Json
Invoke-RestMethod -Uri "http://localhost:4000/contas/0/sincronizar" -Method Post -Headers $headers -ContentType "application/json" -Body $corpo
```

**FALE:** "A agência recusa com 409: o vetor que eu tinha não é mais igual ao vetor atual, porque um depósito aconteceu no meio do caminho. Ela devolve o estado real da conta, e não aplica a operação cegamente." *(print para `conflito-sincronizacao.png`)*

---

## Bloco 8 — App Flutter em modo offline-first (2 min) — um ponto de pausa

**FAÇA:** No app, com a conta logada, ative o **modo avião** no dispositivo/emulador.

**FAÇA:** Faça um depósito pelo app.

**FALE:** "Sem conexão, o depósito não falha: ele aparece na tela com um selo de pendente, e o saldo mostrado já reflete esse depósito de forma otimista."

*(print para `app-offline.png`)*

**FAÇA (⏸ PAUSAR, se precisar):** desative o modo avião. **▶ Retome.**

**FAÇA:** Aponte a tela do app sincronizando sozinho, sem tocar em nada.

**FALE:** "Ao reconectar, o app detecta a conectividade de volta e sincroniza a operação pendente automaticamente - o selo de pendente desaparece sozinho." *(print do antes/depois para `app-sincronizacao.png`)*

**FAÇA (opcional, se der tempo):** Repita o cenário de conflito pelo app: operação offline + mudança por fora (PowerShell/frontend web) antes de reconectar, mostrando o aviso visível de conflito na tela.

---

## Bloco 9 — Decisões de projeto e encerramento (1 min)

**FALE** (com o app ou o terminal parado na tela):
- "As rotas `/bully/eleicao` e `/bully/coordenador` são propositalmente sem autenticação, fiel ao roteiro - isso é discutido no RESPOSTAS.md."
- "A líder eleita hoje é só informativa - nenhuma operação bancária é coordenada por ela ainda. Isso é exatamente o papel que ela vai assumir no Sprint 4, coordenando transações distribuídas."
- "O armazenamento local do app usa Hive, guardando o saldo e o vetor em cache, e a fila de pendentes - sem precisar de gerador de código."
- "Tudo dos Sprints 1 e 2 continua funcionando: particionamento, JWT, mensageria e relógio vetorial."

**FALE (encerramento):** "Isso cobre o algoritmo de Bully, o heartbeat com failover automático, o app Flutter com o fluxo bancário completo e o painel de liderança, e a sincronização offline-first. No Sprint 4 vem o deploy em containers e as transações distribuídas de verdade, com a líder coordenando. Obrigado!"

**FAÇA:** Pare a gravação.

---

## Checklist rápido

- [ ] Eleição inicial: as 3 agências concordam sobre a líder (agência 2)
- [ ] App Flutter: login, saldo, depósito, saque, transferência local e entre agências
- [ ] Painel de liderança: líder atual, agências ativas, histórico, botão de eleição sob demanda
- [ ] Failover: líder derrubada, painel do app atualiza sozinho para a nova líder
- [ ] `historico_lideranca.py` mostrando a linha do tempo completa
- [ ] Conflito de sincronização (409) reproduzido no backend
- [ ] App em modo avião: operação pendente visível, sem erro
- [ ] App reconectando e sincronizando sozinho
- [ ] Decisões de projeto explicadas (sem auth no Bully, líder só informativa, Hive sem codegen)
