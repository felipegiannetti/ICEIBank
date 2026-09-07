# ICEIBank

Banco simplificado, particionado em agências independentes, desenvolvido como projeto de sistemas distribuídos ao longo do semestre. Cada sprint evolui sobre o código do anterior e aplica um conceito diferente de sistemas distribuídos sobre o mesmo domínio: transferência de dinheiro entre contas.

| Sprint | Unidade da ementa | Tecnologia | Conceito de sistemas distribuídos |
|---|---|---|---|
| **1 (este)** | Desenvolvimento Web | API REST / MVC | Relógio lógico de Lamport |
| 2 | Comunicação indireta | Mensageria / Pub-Sub | Relógio vetorial |
| 3 | Desenvolvimento Móvel | App Flutter | Consenso (eleição de líder) |
| 4 | Computação em Nuvem | Containers | Transações distribuídas (2PC/Saga) |

---

## Sumário

- [Visão geral do Sprint 1](#visão-geral-do-sprint-1)
- [Arquitetura](#arquitetura)
- [Tecnologias](#tecnologias)
- [Estrutura do repositório](#estrutura-do-repositório)
- [Como rodar o projeto](#como-rodar-o-projeto)
- [Endpoints da API](#endpoints-da-api)
- [Relógio de Lamport](#relógio-de-lamport)
- [Autenticação (JWT)](#autenticação-jwt)
- [Funcionalidades adicionais](#funcionalidades-adicionais)
- [Frontend](#frontend)
- [Limitação conhecida](#limitação-conhecida-e-proposital)
- [Evidências e vídeo de apresentação](#evidências-e-vídeo-de-apresentação)
- [Documentação de decisões e respostas](#documentação-de-decisões-e-respostas)
- [Roadmap dos próximos sprints](#roadmap-dos-próximos-sprints)

---

## Visão geral do Sprint 1

Nesta primeira entrega, cada agência do banco é um serviço REST independente (arquitetura MVC), com endpoints para criar conta, consultar saldo, depositar, sacar e transferir. Toda operação é registrada com um timestamp de **relógio lógico de Lamport**. Além do backend, este sprint inclui autenticação via **JWT** protegendo as rotas e um **frontend web em React** que consome essa API.

O que esta entrega cobre:
- Um serviço de agência (código único, executado 3 vezes com identidades diferentes = 3 agências).
- Partição de contas entre as 3 agências (`id_conta % 3`).
- CRUD de contas + depósito/saque, tudo carimbado com relógio de Lamport.
- Transferência dentro da mesma agência (local) e entre agências diferentes (via chamada REST direta entre agências).
- Um script que mescla os logs das 3 agências em uma única linha do tempo, ordenada por relógio de Lamport.
- Autenticação via JWT protegendo as rotas da API.
- Um frontend funcional (React) que consome a API autenticada.
- Duas funcionalidades adicionais: histórico de transações por conta e limite diário configurável de saque/transferência.

O que este sprint **não** resolve, de propósito: se uma transferência entre agências falhar no meio do caminho, o débito já aplicado não é revertido automaticamente. Isso é intencional — é exatamente o problema que o Sprint 4 (transações distribuídas) vai resolver com 2PC ou Saga. Ver [Limitação conhecida](#limitação-conhecida-e-proposital).

---

## Arquitetura

### Particionamento

Cada conta pertence a exatamente **uma** agência (partição, não replicação): dado o número da conta, a agência responsável é `id_conta % 3`. O número de agências é fixo em 3 neste sprint.

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
├── controllers/     → rotas FastAPI (auth, contas, transferências)
└── services/        → relógio de Lamport e registro de eventos (JSONL)
```

### Transferência local vs. entre agências

- **Local** (origem e destino na mesma agência): débito e crédito acontecem no mesmo processo, carimbados com `evento_local()`.
- **Entre agências**: a agência de origem debita localmente e faz uma chamada REST (`POST /contas/{id}/creditar-remoto`) para a agência de destino, usando `ao_enviar()`/`ao_receber()` do relógio de Lamport para preservar a ordem causal entre os dois processos.

---

## Tecnologias

**Backend**
- Python 3.12 + [FastAPI](https://fastapi.tiangolo.com/)
- [PyJWT](https://pyjwt.readthedocs.io/) — emissão/validação de tokens JWT
- [bcrypt](https://pypi.org/project/bcrypt/) — hash de senha
- [httpx](https://www.python-httpx.org/) — chamadas HTTP assíncronas entre agências
- Armazenamento em memória (sem banco de dados, por escopo deste sprint)

**Frontend**
- [React 18](https://react.dev/) + [Vite](https://vitejs.dev/)
- [react-router-dom](https://reactrouter.com/)
- CSS puro (sem framework), com paleta azul/roxo/branco e componentes inspirados em apps bancários

---

## Estrutura do repositório

```
ICEIBank/
├── agencia/                       # Backend — serviço de agência (FastAPI)
│   ├── requirements.txt
│   ├── app/
│   │   ├── main.py                # monta a app, CORS, injeta estado por agência
│   │   ├── config.py               # particionamento, portas, segredos
│   │   ├── security.py             # JWT, hash de senha, autorização por dono
│   │   ├── models/conta.py         # Conta, ContaStore, limite diário
│   │   ├── views/                  # schemas Pydantic (request/response)
│   │   ├── controllers/            # rotas: auth, contas, transferências
│   │   └── services/               # RelogioLamport, RegistroEventos
│   ├── data/                       # logs *.jsonl gerados em runtime (não versionado)
│   └── mesclar_logs.py             # linha do tempo unificada por Lamport
├── frontend/                       # Frontend — React + Vite
│   └── src/
│       ├── api/client.js           # cliente HTTP (injeta JWT, trata erros)
│       ├── context/AuthContext.jsx
│       ├── components/             # AppShell (sidebar), ícones, seletor de agência
│       └── pages/                  # login, cadastro, conta, depósito, saque,
│                                    # transferência, extrato, limite, perfil
├── evidencias/sprint1/             # Prints e vídeo de apresentação, organizados por parte
├── RESPOSTAS.md                    # Respostas conceituais + decisões de design
└── ROTEIRO_SPRINT_1.md             # Enunciado original do sprint
```

---

## Como rodar o projeto

### Pré-requisitos
- Python 3.12+
- Node.js 18+ e npm

### 1. Backend — as 3 agências

```powershell
cd agencia
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Abra **3 terminais** e rode um comando em cada, variando `AGENCIA_ID`:

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

As agências sobem em `http://localhost:4000`, `4001` e `4002`.

### 2. Frontend

```powershell
cd frontend
npm install
npm run dev
```

Abra `http://localhost:5173`.

### 3. Linha do tempo unificada

Depois de gerar algumas operações, rode:

```powershell
cd agencia
.\.venv\Scripts\python.exe mesclar_logs.py
```

Mostra todos os eventos das 3 agências, mesclados e ordenados por timestamp de Lamport.

---

## Endpoints da API

| Método | Rota | Autenticação | Descrição |
|---|---|---|---|
| `POST` | `/auth/login` | — | Login (`id_conta` + `senha`) → retorna JWT |
| `POST` | `/contas` | pública | Cria conta (cadastro) |
| `GET` | `/contas/{id}` | JWT + dono | Consulta saldo |
| `POST` | `/contas/{id}/depositar` | JWT + dono | Depósito |
| `POST` | `/contas/{id}/sacar` | JWT + dono | Saque (respeita limite diário) |
| `POST` | `/transferencias` | JWT (dono da origem) | Transferência local ou entre agências |
| `POST` | `/contas/{id}/creditar-remoto` | segredo interno | Chamada agência→agência (não é de usuário) |
| `GET` | `/contas/{id}/historico` | JWT + dono | Histórico de eventos da conta (filtros `limit`, `tipo`) |
| `GET` | `/contas/{id}/limite` | JWT + dono | Consulta limite diário |
| `PUT` | `/contas/{id}/limite` | JWT + dono | Atualiza limite diário |

Todas as rotas com `{id}` aplicam o guard de particionamento (`id % 3` precisa bater com a agência) e retornam erros no formato `{"erro": "..."}`.

---

## Relógio de Lamport

Implementado em `agencia/app/services/lamport_clock.py`, com as três regras clássicas:

1. **Evento local** → incrementa o contador.
2. **Ao enviar** uma mensagem para outra agência → incrementa e anexa o valor.
3. **Ao receber** → `contador = max(contador_local, timestamp_recebido) + 1`.

Cada evento é gravado em `agencia/data/eventos-agencia-{N}.jsonl`, com `timestamp_lamport` (o relógio lógico) e `hora_parede` (o relógio físico, só para comparação — nunca usado em nenhuma decisão do sistema). O `mesclar_logs.py` junta os logs das 3 agências numa única linha do tempo ordenada pelo relógio lógico, o que deixa visível na prática que eventos concorrentes (sem relação causal) podem empatar no mesmo timestamp — a limitação que motiva o relógio vetorial do Sprint 2.

---

## Autenticação (JWT)

- **Credencial**: `id_conta` + `senha` — a própria conta é a identidade, sem um cadastro de usuário separado.
- **Token**: HS256, expira em 30 minutos.
- **Autorização por dono**: uma conta só pode operar nela mesma; numa transferência, o token precisa ser dono da conta de **origem** (mas pode enviar para qualquer destino).
- **`POST /contas` é público**, mesmo com JWT ativo — decisão deliberada para evitar um paradoxo de bootstrap (não existe token antes de existir a primeira conta). Justificado em detalhe no [`RESPOSTAS.md`](RESPOSTAS.md).
- **Chamada `creditar-remoto`** (agência → agência) usa um segredo compartilhado interno (`X-Internal-Secret`), não o JWT do usuário — é um domínio de confiança diferente (serviço-a-serviço).

---

## Funcionalidades adicionais

Além do escopo mínimo do sprint, foram implementadas duas funcionalidades extras (descritas em detalhe no [`RESPOSTAS.md`](RESPOSTAS.md)):

1. **Histórico de transações por conta** (`GET /contas/{id}/historico`) — reaproveita o próprio log de eventos do relógio de Lamport, filtrando pela conta pedida, com filtros opcionais de tipo e quantidade.
2. **Limite diário configurável de saque/transferência** — cada conta tem um limite diário (com valor padrão), configurável pelo dono, que acumula o uso ao longo do dia e bloqueia operações que o ultrapassariam — mesmo com saldo suficiente.

---

## Frontend

Aplicação React com:
- **Login e cadastro** de conta, com seletor da agência de entrada.
- **Dashboard** com saldo (opção de ocultar/mostrar), e ações rápidas (depositar, sacar, transferir, extrato, limite).
- **Extrato** estilizado como lista de transações, com o timestamp de Lamport de cada evento.
- **Limite diário** com barra de progresso do uso do dia.
- **Perfil** com o resumo dos dados da conta.
- Tratamento visível de todo erro retornado pela API (nunca só no console).
- Paleta azul-claro/roxo/branco, com uma barra lateral de navegação inspirada em aplicativos bancários.

---

## Limitação conhecida (e proposital)

Se a agência de destino de uma transferência cair no meio da operação, o débito já aplicado na agência de origem **não é revertido automaticamente** — o sistema responde com erro 502 e registra a inconsistência no log (evento `TRANSFERENCIA_FALHOU`), mas o valor fica temporariamente "perdido" até resolução manual. Essa é exatamente a lacuna que o **Sprint 4** resolve de verdade, com uma transação distribuída (2PC ou Saga).

---

## Evidências e vídeo de apresentação

Todas as evidências de teste (prints com timestamp real e o vídeo de apresentação) estão em [`evidencias/sprint1/`](evidencias/sprint1/), organizadas em subpastas por parte do roteiro:

```
evidencias/sprint1/
├── apresentacao-sprint1.mp4        # vídeo de apresentação (via Git LFS)
├── parte-c-contas/
├── parte-d-transferencias/
├── parte-e-linha-do-tempo/
├── parte-f-auth/
├── parte-g-frontend/
├── extra-historico/
└── extra-limite/
```

> O vídeo é versionado via **Git LFS** (arquivo grande) — rode `git lfs pull` após clonar se ele não baixar automaticamente.

---

## Documentação de decisões e respostas

Todas as perguntas conceituais do roteiro (relógio de Lamport, transferências, linha do tempo, JWT, frontend) e as justificativas de design (modelo de credencial, autorização, segredo interno, escolha do limite diário) estão respondidas em detalhe em [`RESPOSTAS.md`](RESPOSTAS.md).

---

## Roadmap dos próximos sprints

- **Sprint 2** — Comunicação indireta via mensageria/Pub-Sub, com relógio vetorial substituindo o escalar de Lamport.
- **Sprint 3** — App mobile em Flutter, com consenso via eleição de líder.
- **Sprint 4** — Deploy em containers, com transações distribuídas de verdade (2PC/Saga) resolvendo a limitação conhecida deste sprint.
