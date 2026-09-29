# ICEIBank

Banco simplificado, particionado em agências independentes, desenvolvido como projeto de sistemas distribuídos ao longo do semestre. Cada sprint evolui sobre o código do anterior e aplica um conceito diferente de sistemas distribuídos sobre o mesmo domínio: transferência de dinheiro entre contas.

| Sprint | Unidade da ementa | Tecnologia | Conceito de sistemas distribuídos |
|---|---|---|---|
| 1 | Desenvolvimento Web | API REST / MVC | Relógio lógico de Lamport |
| **2 (este)** | Comunicação indireta | Mensageria / Pub-Sub | Relógio vetorial |
| 3 | Desenvolvimento Móvel | App Flutter | Consenso (eleição de líder) |
| 4 | Computação em Nuvem | Containers | Transações distribuídas (2PC/Saga) |

---

## Sumário

- [Visão geral](#visão-geral)
- [Arquitetura](#arquitetura)
- [Tecnologias](#tecnologias)
- [Estrutura do repositório](#estrutura-do-repositório)
- [Como rodar o projeto](#como-rodar-o-projeto)
- [Endpoints da API](#endpoints-da-api)
- [Relógio vetorial](#relógio-vetorial)
- [Mensageria (RabbitMQ)](#mensageria-rabbitmq)
- [Autenticação (JWT)](#autenticação-jwt)
- [Funcionalidades adicionais](#funcionalidades-adicionais)
- [Frontend](#frontend)
- [Limitação conhecida](#limitação-conhecida-e-proposital)
- [Evidências e vídeo de apresentação](#evidências-e-vídeo-de-apresentação)
- [Documentação de decisões e respostas](#documentação-de-decisões-e-respostas)
- [Roadmap dos próximos sprints](#roadmap-dos-próximos-sprints)

---

## Visão geral

### Sprint 1 (concluído)

Cada agência do banco é um serviço REST independente (arquitetura MVC), com endpoints para criar conta, consultar saldo, depositar, sacar e transferir, autenticação via **JWT** e um **frontend web em React**. Toda operação era registrada com um **relógio lógico de Lamport**. A transferência entre agências era uma chamada REST síncrona direta — se a agência de destino estivesse fora do ar, a chamada falhava na hora e o débito já aplicado ficava "pendurado" (inconsistência conhecida e proposital).

### Sprint 2 (este)

Substitui a chamada REST direta entre agências por **mensageria assíncrona (RabbitMQ, Publish/Subscribe)**: a agência de origem publica um evento numa exchange, e a agência de destino consome quando puder — mesmo que esteja temporariamente fora do ar. Como consequência direta dessa mudança, o **relógio de Lamport dá lugar ao relógio vetorial**, que permite determinar com certeza se dois eventos são causalmente relacionados ou genuinamente concorrentes.

O que este sprint entrega:
- RabbitMQ configurado (exchange `topic`, uma fila por agência, dead-letter queue).
- Relógio vetorial substituindo o relógio de Lamport.
- Transferência entre agências publicada como mensagem, consumida de forma assíncrona.
- Um script de linha do tempo que identifica pares de eventos comprovadamente **concorrentes** entre agências diferentes.
- Quatro funcionalidades adicionais: dead-letter queue, confirmação de entrega, fila de auditoria e notificação de saldo baixo.
- Particionamento, JWT e o frontend do Sprint 1 continuam funcionando (regressão verificada).

O que este sprint melhora, e o que ainda não resolve: a mensageria durável resolve o problema mais visível do Sprint 1 — uma mensagem publicada para uma agência fora do ar não se perde mais, fica retida na fila até a agência voltar. Mas isso **não** resolve tudo: como as contas ainda vivem em memória (sem persistência em disco/banco), se a agência de destino **reiniciar** antes de consumir a mensagem, a conta que deveria receber o crédito não existe mais quando a agência volta — a mensagem chega, mas não encontra onde aplicar o valor (esse cenário exato é reproduzido e documentado; ver [Limitação conhecida](#limitação-conhecida-e-proposital)).

---

## Arquitetura

### Particionamento

Cada conta pertence a exatamente **uma** agência (partição, não replicação): dado o número da conta, a agência responsável é `id_conta % 3`. O número de agências é fixo em 3.

```
conta 0 → agência 0        conta 3 → agência 0
conta 1 → agência 1        conta 4 → agência 1
conta 2 → agência 2        conta 5 → agência 2
```

### MVC explícito no backend

```
agencia/app/
├── models/          → dados e regras de domínio (Conta, ContaStore, limite diário)
├── views/           → schemas Pydantic de request/response (camada de serialização)
├── controllers/     → rotas FastAPI (auth, contas, transferências, interno)
└── services/        → relógio vetorial, mensageria (RabbitMQ), handlers, registro de eventos
```

### Transferência local vs. entre agências

- **Local** (origem e destino na mesma agência): débito e crédito acontecem no mesmo processo, carimbados com `evento_local()`.
- **Entre agências**: a agência de origem debita localmente, publica um evento na exchange do RabbitMQ (`ao_enviar()`) e responde `200` informando que a transferência foi **publicada** (`status: PENDENTE`) — a aplicação do crédito é assíncrona. A agência de destino consome a mensagem quando puder (`ao_receber()`), aplica o crédito e publica uma confirmação de volta, que a origem consome e usa para atualizar o status da transferência (`CONFIRMADA`/`FALHOU`). Se a **publicação** falhar de forma confirmada (broker fora do ar, mensagem não roteável), o débito e o consumo do limite diário são estornados na hora.

---

## Tecnologias

**Backend**
- Python 3.12 + [FastAPI](https://fastapi.tiangolo.com/)
- [PyJWT](https://pyjwt.readthedocs.io/) — emissão/validação de tokens JWT
- [bcrypt](https://pypi.org/project/bcrypt/) — hash de senha
- [pika](https://pika.readthedocs.io/) — cliente RabbitMQ (AMQP)
- [python-dotenv](https://pypi.org/project/python-dotenv/) — carrega `agencia/.env`
- Armazenamento em memória (sem banco de dados, por escopo do projeto)

**Infraestrutura**
- [RabbitMQ](https://www.rabbitmq.com/) — local via Docker (desenvolvimento) ou [CloudAMQP](https://www.cloudamqp.com/) (broker gerenciado)

**Frontend**
- [React 18](https://react.dev/) + [Vite](https://vitejs.dev/)
- [react-router-dom](https://reactrouter.com/)
- CSS puro (sem framework), com paleta azul/roxo/branco e componentes inspirados em apps bancários

---

## Estrutura do repositório

```
ICEIBank/
├── agencia/                        # Backend — serviço de agência (FastAPI)
│   ├── requirements.txt
│   ├── .env.example                # variáveis de ambiente (copie para .env)
│   ├── app/
│   │   ├── main.py                 # monta a app, CORS, lifespan (publicador + consumidores)
│   │   ├── config.py                # particionamento, portas, segredos, topologia RabbitMQ
│   │   ├── security.py              # JWT, hash de senha, autorização por dono
│   │   ├── models/conta.py          # Conta, ContaStore, limite diário
│   │   ├── views/                   # schemas Pydantic (request/response)
│   │   ├── controllers/             # rotas: auth, contas, transferências, interno (DLQ)
│   │   └── services/
│   │       ├── relogio_vetorial.py  # RelogioVetorial + comparar_vetores
│   │       ├── event_log.py         # RegistroEventos (JSONL)
│   │       ├── mensageria.py        # Publicador, Consumidor, topologia RabbitMQ
│   │       └── handlers.py          # handlers de crédito/confirmação/alerta
│   ├── data/                        # logs *.jsonl gerados em runtime (não versionado)
│   ├── mesclar_logs.py              # linha do tempo unificada + pares concorrentes
│   ├── auditor.py                   # consumidor independente (fila de auditoria)
│   └── tests/                       # testes unitários (relógio vetorial)
├── frontend/                        # Frontend — React + Vite
│   └── src/
│       ├── api/client.js            # cliente HTTP (injeta JWT, trata erros)
│       ├── context/AuthContext.jsx
│       ├── components/              # AppShell (sidebar), ícones, seletor de agência
│       └── pages/                   # login, cadastro, conta, depósito, saque,
│                                     # transferência, extrato, limite, perfil
├── evidencias/
│   ├── sprint1/                     # prints + vídeo do Sprint 1
│   └── sprint2/                     # prints + vídeo do Sprint 2, por parte do roteiro
├── RESPOSTAS.md                     # respostas conceituais + decisões de design
├── ROTEIRO_SPRINT_1.md              # enunciado original do Sprint 1
└── ROTEIRO_SPRINT_2.md              # enunciado original do Sprint 2
```

---

## Como rodar o projeto

### Pré-requisitos
- Python 3.12+
- Node.js 18+ e npm
- Um broker RabbitMQ — local via Docker, **ou** uma instância gratuita no [CloudAMQP](https://www.cloudamqp.com/) (plano "Little Lemur")

### 1. RabbitMQ

**Opção A — Docker local (desenvolvimento):**
```powershell
docker run -d --name rabbitmq-iceibank -p 5672:5672 -p 15672:15672 rabbitmq:3-management
```
Painel de administração em `http://localhost:15672` (usuário/senha `guest`/`guest`).

**Opção B — CloudAMQP:** crie uma instância gratuita e copie a **AMQP URL** (`amqps://usuario:senha@host.cloudamqp.com/vhost`).

Configure em `agencia/.env` (copie de `agencia/.env.example`):
```
RABBITMQ_URL=amqp://guest:guest@localhost:5672/
```

### 2. Backend — as 3 agências

```powershell
cd agencia
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Abra **3 terminais** e rode um comando em cada, variando `AGENCIA_ID` (o `.env` é lido automaticamente):

```powershell
# Terminal 1
$env:AGENCIA_ID=0
.\.venv\Scripts\python.exe -m app.main

# Terminal 2
$env:AGENCIA_ID=1
.\.venv\Scripts\python.exe -m app.main

# Terminal 3
$env:AGENCIA_ID=2
.\.venv\Scripts\python.exe -m app.main
```

As agências sobem em `http://localhost:4000`, `4001` e `4002`, e cada uma declara a topologia completa do RabbitMQ (exchanges e filas) ao subir.

### 3. Frontend

```powershell
cd frontend
npm install
npm run dev
```

Abra `http://localhost:5173`.

### 4. Linha do tempo unificada

Depois de gerar algumas operações, rode:

```powershell
cd agencia
.\.venv\Scripts\python.exe mesclar_logs.py [--causais]
```

Mostra todos os eventos das 3 agências, ordenados por hora de parede, e os pares de eventos **concorrentes** identificados via relógio vetorial. Com `--causais`, mostra também os pares débito→crédito remoto de cada transferência entre agências, confirmando que nunca aparecem como concorrentes.

### 5. Fila de auditoria (opcional)

```powershell
cd agencia
.\.venv\Scripts\python.exe auditor.py
```

Consumidor independente que escuta todos os eventos publicados por qualquer agência (ver [Funcionalidades adicionais](#funcionalidades-adicionais)).

---

## Endpoints da API

| Método | Rota | Autenticação | Descrição |
|---|---|---|---|
| `POST` | `/auth/login` | — | Login (`id_conta` + `senha`) → retorna JWT |
| `POST` | `/contas` | pública | Cria conta (cadastro) |
| `GET` | `/contas/{id}` | JWT + dono | Consulta saldo |
| `POST` | `/contas/{id}/depositar` | JWT + dono | Depósito |
| `POST` | `/contas/{id}/sacar` | JWT + dono | Saque (respeita limite diário) |
| `POST` | `/transferencias` | JWT (dono da origem) | Transferência local (síncrona) ou entre agências (publica na fila) |
| `GET` | `/transferencias/{id_transferencia}` | JWT (dono da origem) | Status de uma transferência entre agências (`PENDENTE`/`CONFIRMADA`/`FALHOU`) |
| `GET` | `/contas/{id}/historico` | JWT + dono | Histórico de eventos da conta (filtros `limit`, `tipo`) |
| `GET` | `/contas/{id}/limite` | JWT + dono | Consulta limite diário |
| `PUT` | `/contas/{id}/limite` | JWT + dono | Atualiza limite diário |
| `GET` | `/contas/{id}/notificacoes` | JWT + dono | Alertas de saldo baixo já recebidos |
| `GET` | `/interno/dlq` | segredo interno | Espia as mensagens na dead-letter queue desta agência |
| `POST` | `/interno/dlq/reprocessar` | segredo interno | Tenta reaplicar as mensagens da DLQ |

Todas as rotas com `{id}` aplicam o guard de particionamento (`id % 3` precisa bater com a agência) e retornam erros no formato `{"erro": "..."}`. A rota `POST /contas/{id}/creditar-remoto` do Sprint 1 foi **removida** — o crédito remoto agora chega exclusivamente via mensageria.

---

## Relógio vetorial

Implementado em `agencia/app/services/relogio_vetorial.py`, substituindo o relógio de Lamport do Sprint 1. Um vetor de contadores, uma posição por agência, com três regras:

1. **Evento local** → incrementa a própria posição.
2. **Ao enviar** uma mensagem → incrementa a própria posição e anexa o vetor inteiro.
3. **Ao receber** um vetor `V` → `vetor[i] = max(vetor[i], V[i])` para cada posição `i`, depois incrementa a própria posição.

Comparando dois vetores posição a posição (`comparar_vetores`), dá para determinar com certeza se um evento aconteceu **antes** do outro, ou se são **concorrentes** (nenhum domina o outro em todas as posições) — algo que o relógio de Lamport, sozinho, não garantia (dois timestamps escalares diferentes podiam ser causais ou apenas coincidência). Cada evento é gravado em `agencia/data/eventos-agencia-{N}.jsonl` com `timestamp_vetorial` (lista) e `hora_parede` (só para comparação). O `mesclar_logs.py` usa essa comparação para listar, de forma automática, todos os pares de eventos comprovadamente concorrentes entre agências diferentes.

---

## Mensageria (RabbitMQ)

```
exchange topic "iceibank.eventos"
  agencia.N.creditar     -> fila-agencia-N               (crédito remoto)
  agencia.N.confirmacao  -> fila-confirmacoes-agencia-N   (confirmação de entrega)
  alerta.saldo_baixo.N   -> fila-alertas-agencia-N        (notificação de saldo baixo)
  #                      -> fila-auditoria                (fila de auditoria)
exchange topic "iceibank.dlx"
  agencia.N.morta        -> dlq-agencia-N                 (dead-letter)
```

Toda agência declara essa topologia inteira (as 3 agências, não só a própria) ao subir — a operação é idempotente e garante que uma mensagem publicada para uma agência que ainda não subiu (ou que caiu) fique retida em vez de ser descartada. O publisher usa *publisher confirms* + `mandatory=True` (uma publicação só é considerada bem-sucedida quando o broker confirma que a mensagem foi roteada); os consumidores rodam em threads próprias, com `prefetch=1` e ack manual.

---

## Autenticação (JWT)

- **Credencial**: `id_conta` + `senha` — a própria conta é a identidade, sem um cadastro de usuário separado.
- **Token**: HS256, expira em 30 minutos.
- **Autorização por dono**: uma conta só pode operar nela mesma; numa transferência, o token precisa ser dono da conta de **origem** (mas pode enviar para qualquer destino).
- **`POST /contas` é público**, mesmo com JWT ativo — decisão deliberada para evitar um paradoxo de bootstrap (não existe token antes de existir a primeira conta). Justificado em detalhe no [`RESPOSTAS.md`](RESPOSTAS.md).
- **Rotas `/interno/*`** (DLQ) usam um segredo compartilhado (`X-Internal-Secret`), não o JWT do usuário — é um domínio de confiança diferente (operação administrativa, não uma ação de uma conta).
- O consumidor de mensagens do RabbitMQ **não** verifica JWT (não há como um token HTTP viajar numa mensagem AMQP) — a discussão sobre essa superfície de confiança está no [`RESPOSTAS.md`](RESPOSTAS.md).

---

## Funcionalidades adicionais

**Sprint 1:**
1. **Histórico de transações por conta** (`GET /contas/{id}/historico`) — reaproveita o próprio log de eventos, com filtros opcionais de tipo e quantidade.
2. **Limite diário configurável de saque/transferência** — cada conta tem um limite diário, configurável pelo dono, que acumula o uso ao longo do dia.

**Sprint 2** (descritas em detalhe no [`RESPOSTAS.md`](RESPOSTAS.md)):
3. **Dead-letter queue** — créditos remotos que falham (conta não encontrada) vão para uma DLQ por agência, inspecionável e reprocessável via `/interno/dlq`.
4. **Confirmação de entrega** — a agência de destino confirma de volta o resultado do crédito; a origem atualiza o status da transferência e o frontend acompanha isso com polling.
5. **Fila de auditoria** — um consumidor independente (`auditor.py`) escuta tudo que é publicado, de qualquer agência, sem acoplamento com elas.
6. **Notificação de saldo baixo** — alerta publicado (e consumido) quando o saldo de uma conta cruza um limite configurável.

---

## Frontend

Aplicação React com:
- **Login e cadastro** de conta, com seletor da agência de entrada.
- **Dashboard** com saldo (opção de ocultar/mostrar), aviso de saldo baixo e ações rápidas.
- **Transferência** com acompanhamento de status (publicada → aguardando confirmação → confirmada/falhou) via polling.
- **Extrato** estilizado como lista de transações, mostrando o **vetor** de cada evento.
- **Limite diário** com barra de progresso do uso do dia.
- **Perfil** com o resumo dos dados da conta.
- Tratamento visível de todo erro retornado pela API (nunca só no console).

---

## Limitação conhecida (e proposital)

A mensageria durável resolveu o problema de **entrega** do Sprint 1 (uma mensagem publicada para uma agência fora do ar não se perde mais — fica retida na fila até ela voltar). Mas como as contas ainda vivem só em memória (sem persistência em disco/banco), se a agência de destino **reiniciar** antes de consumir a mensagem, a conta que deveria receber o crédito deixa de existir — a mensagem chega, mas não encontra onde aplicar o valor. Esse cenário exato foi reproduzido: a mensagem cai na dead-letter queue (`CREDITO_REMOTO_FALHOU` + confirmação de falha para a origem), e só é resolvida recriando a conta e reprocessando a DLQ manualmente (`POST /interno/dlq/reprocessar`). Ou seja: resolvemos a confiabilidade da **entrega**, mas não a persistência do **estado** — isso continua em aberto até uma solução de armazenamento durável e, para atomicidade completa entre débito e crédito mesmo sob falha, uma transação distribuída de verdade (2PC/Saga), assunto do **Sprint 4**.

---

## Evidências e vídeo de apresentação

Todas as evidências de teste (prints com timestamp real e o vídeo de apresentação) estão em `evidencias/`, organizadas por sprint e por parte do roteiro:

```
evidencias/
├── sprint1/
│   ├── apresentacao-sprint1.mp4     # vídeo de apresentação (via Git LFS)
│   ├── parte-c-contas/
│   ├── parte-d-transferencias/
│   ├── parte-e-linha-do-tempo/
│   ├── parte-f-auth/
│   ├── parte-g-frontend/
│   ├── extra-historico/
│   └── extra-limite/
└── sprint2/
    ├── parte-a-rabbitmq/
    ├── parte-c-mensageria/
    ├── parte-d-linha-do-tempo/
    ├── extra-dlq/
    ├── extra-confirmacao/
    ├── extra-auditoria/
    └── extra-saldo-baixo/
```

> Vídeos são versionados via **Git LFS** — rode `git lfs pull` após clonar se não baixarem automaticamente.

---

## Documentação de decisões e respostas

Todas as perguntas conceituais dos dois roteiros (relógio de Lamport e vetorial, transferências, mensageria, linha do tempo, JWT, frontend) e as justificativas de design (modelo de credencial, autorização, segredos, escolha do limite diário, estorno em caso de falha de publicação) estão respondidas em detalhe em [`RESPOSTAS.md`](RESPOSTAS.md), incluindo a declaração de uso de IA exigida pelo roteiro do Sprint 2.

---

## Roadmap dos próximos sprints

- **Sprint 3** — App mobile em Flutter, com consenso via eleição de líder.
- **Sprint 4** — Deploy em containers, com transações distribuídas de verdade (2PC/Saga) resolvendo a limitação conhecida deste sprint.
