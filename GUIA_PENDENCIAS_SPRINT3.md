# Guia passo a passo — o que falta para fechar a Sprint 3

> **Atualização:** depois que você instalou o Android Studio (passo 1), o Claude rodou todo o resto desta sessão sozinho: subiu o emulador `Pixel_7` via linha de comando (headless, sem abrir a janela gráfica), instalou a NDK que faltava, compilou e instalou o app real, e capturou **todas as 8 evidências obrigatórias + os 3 extras** (já estão em `evidencias/sprint3/`, commitadas) clicando de verdade no app via `adb`. Os detalhes de como cada uma foi reproduzida estão na nota de transparência do `RESPOSTAS.md` (seção Sprint 3). **O que realmente falta agora é só o vídeo de apresentação** — pule direto para a seção 5 deste guia. O restante abaixo (seções 1-4) ficou como referência caso você queira reproduzir algo você mesma/o, mas não é mais necessário para fechar a sprint.

Este guia cobria originalmente o que ficou pendente depois da implementação: instalar o que falta, rodar tudo junto, e capturar cada evidência pedida pelo roteiro (`ROTEIRO_SPRINT_3.md`, seção 4.2).

Já está pronto e commitado: todo o backend (Bully, heartbeat, histórico, sincronização offline-first), todo o código do app Flutter (`app_mobile/`), as pastas `android/`/`ios/`/`web/` já geradas, o Flutter SDK já instalado nesta máquina em `C:\flutter`, e agora também todas as evidências de telas/respostas.

---

## 0. Deixar o `flutter` disponível no terminal (opcional, mas recomendado)

O Flutter já está instalado em `C:\flutter`, mas o comando `flutter` só funciona se `C:\flutter\bin` estiver no PATH. Para adicionar permanentemente:

1. Menu Iniciar → digite "variáveis de ambiente" → abra **"Editar as variáveis de ambiente do sistema"**.
2. Botão **"Variáveis de Ambiente..."**.
3. Em **"Variáveis do usuário"**, selecione `Path` → **Editar** → **Novo** → cole `C:\flutter\bin` → OK em tudo.
4. Feche e abra um **novo** terminal (PowerShell/Git Bash) para a mudança valer.
5. Confirme: `flutter --version`.

Se não quiser mexer no PATH, use o caminho completo em todo comando: `C:\flutter\bin\flutter.bat <comando>`. Os exemplos abaixo já assumem que você adicionou ao PATH (se não quiser, troque `flutter` por `C:\flutter\bin\flutter.bat`).

---

## 1. Instalar o Android Studio + emulador

Isso eu não consegui fazer por você (precisa de permissões de administrador que esta sessão não tinha).

1. Baixe em **https://developer.android.com/studio** e instale normalmente (Next, Next, Finish).
2. Na primeira abertura, o próprio Android Studio oferece o **"Setup Wizard"** — aceite instalar os componentes padrão (Android SDK, Android SDK Platform, Android Virtual Device). Isso baixa alguns GB, pode demorar.
3. Depois de instalado, abra **Android Studio → More Actions → Virtual Device Manager** (ou **Tools → Device Manager**).
4. **Create Device** → escolha um aparelho (ex. "Pixel 7") → **Next**.
5. Escolha uma imagem de sistema (ex. a mais recente com Google Play, "Tiramisu"/API 33 ou mais nova) → se pedir para baixar, baixe → **Next** → **Finish**.
6. Na lista de dispositivos virtuais, clique no ícone de **play (▶)** para ligar o emulador. Espere ele abrir completamente (pode levar 1-2 minutos na primeira vez).

### Confirmar que o Flutter enxerga tudo

Com o emulador ligado, abra um terminal na pasta do projeto e rode:

```powershell
flutter doctor
```

Isso deve mostrar `[√] Android toolchain` (sem erro) e, rodando `flutter devices`, o emulador deve aparecer na lista. Se `flutter doctor` pedir para aceitar licenças do Android:

```powershell
flutter doctor --android-licenses
```

(aceite todas digitando `y` quando pedido).

**Dispositivo físico, como alternativa:** se preferir usar seu próprio celular Android em vez de emulador, ative "Opções do desenvolvedor" (toque 7x em "Número da versão" em Configurações → Sobre o telefone) e depois "Depuração USB", conecte por cabo, e `flutter devices` deve mostrar o aparelho.

---

## 2. Rodar o app Flutter no emulador

```powershell
cd "C:\Users\felip\OneDrive\Desktop\Faculdade\5-quinto-periodo\LAB\ICEIBank\app_mobile"
flutter pub get
flutter run
```

Se aparecer mais de um dispositivo na lista (emulador + Chrome, por exemplo), o `flutter run` pergunta qual usar — escolha o emulador Android.

O app já está configurado (`lib/config/agencias.dart`) para falar com `http://10.0.2.2:400{0,1,2}` — esse é o apelido que o **emulador Android** usa para "o localhost do seu PC". Não precisa mudar nada para isso funcionar, desde que as agências estejam rodando no seu PC (próximo passo).

> **Nota sobre HTTP sem TLS**: o Android bloqueia tráfego HTTP puro por padrão. Eu já deixei isso resolvido — `android/app/src/main/AndroidManifest.xml` já tem `android:usesCleartextTraffic="true"`. Se por algum motivo der erro de conexão só no Android (e funcionar no `flutter run -d chrome`), confira se essa linha continua lá.

---

## 3. Subir o backend: as 3 agências + RabbitMQ

Isso é exatamente o que você já faz desde o Sprint 1/2 — nada novo aqui, só continuar usando o que já está configurado em `agencia/.env`.

1. Confirme que seu RabbitMQ está acessível (Docker local rodando, **ou** sua instância CloudAMQP ativa — o que você já usa).
2. Abra **3 terminais** na pasta `agencia/` e rode, um em cada:

```powershell
$env:AGENCIA_ID=0
.\.venv\Scripts\python.exe -m app.main
```
```powershell
$env:AGENCIA_ID=1
.\.venv\Scripts\python.exe -m app.main
```
```powershell
$env:AGENCIA_ID=2
.\.venv\Scripts\python.exe -m app.main
```

3. Espere alguns segundos e confirme que as 3 concordam sobre a líder:

```powershell
Invoke-RestMethod -Uri "http://localhost:4000/bully/lider" -Method Get
Invoke-RestMethod -Uri "http://localhost:4001/bully/lider" -Method Get
Invoke-RestMethod -Uri "http://localhost:4002/bully/lider" -Method Get
```

As 3 devem responder `lider_atual: 2` (a de maior ID).

4. Crie pelo menos uma conta de teste (ajuste o `id` para cair na agência que quiser — a regra é `id % 3`):

```powershell
Invoke-RestMethod -Uri "http://localhost:4000/contas" -Method Post -ContentType "application/json" -Body '{"id":0,"nome_aluno":"Ana","senha":"senha123","saldo_inicial":500}'
```

---

## 4. Coletar as evidências

Crie a pasta se ainda não existir (já deve existir, vazia, com `.gitkeep` em cada subpasta):

```powershell
New-Item -ItemType Directory -Force -Path evidencias/sprint3
```

Para cada print: deixe um terminal com `Get-Date` visível (ou o relógio do Windows na barra de tarefas) em algum canto da tela, para provar que é real. Uso a tecla de print screen do Windows (`Win + Shift + S`) para recortar só a janela relevante.

### 4.1 — `eleicao-inicial.png`
**O quê:** as 3 agências concordando sobre a mesma líder.
**Como:** com as 3 agências já rodando (passo 3), rode os 3 `Invoke-RestMethod` de `/bully/lider` do passo 3.3 lado a lado (ou em sequência) e capture a tela mostrando as 3 respostas com `lider_atual: 2`.

### 4.2 — `failover.png`
**O quê:** a líder caindo e uma nova eleição acontecendo sozinha.
**Como:**
1. Com as 3 agências rodando e a líder = agência 2, vá no terminal da agência 2 e aperte `Ctrl+C` para derrubá-la.
2. Espere ~5 segundos (o heartbeat roda a cada 3s).
3. Rode de novo `/bully/lider` nas agências 0 e 1 — ambas devem agora responder `lider_atual: 1`.
4. Capture a tela mostrando a sequência: o terminal da agência 2 sendo fechado + a nova resposta das agências 0/1.

### 4.3 — `historico-lideranca.png`
**O quê:** a saída do script de histórico.
**Como:** depois de reproduzir os passos 4.1 e 4.2 (para ter eventos de verdade no log), rode:
```powershell
cd agencia
.\.venv\Scripts\python.exe historico_lideranca.py
```
Capture a saída completa no terminal (os dois blocos: "Histórico de eventos" e "Linha do tempo de líderes").

### 4.4 — `app-lider-atual.png`
**O quê:** o app Flutter mostrando a líder atual.
**Como:** com as 3 agências rodando, abra o app no emulador (passo 2), faça login, toque no ícone de "painel de liderança" (canto superior direito) e capture a tela mostrando "Líder atual: Agência 2".

### 4.5 — `app-failover.png`
**O quê:** o painel do app atualizando sozinho após a queda da líder.
**Como:** com o app já aberto no painel de liderança (tela anterior), derrube a agência líder (`Ctrl+C` no terminal dela) **sem tocar em nada no app**. Espere ~5-10s (o app consulta a cada 5s) e capture a tela mostrando que "Líder atual" mudou sozinho. Se conseguir, tire duas capturas (antes/depois) ou grave como GIF curto.

### 4.6 — `conflito-sincronizacao.png`
**O quê:** o backend recusando uma sincronização desatualizada (409).
**Como** (reproduzindo a seção 9.5 do roteiro, via PowerShell):
```powershell
# 1. Login e pega o token
$login = Invoke-RestMethod -Uri "http://localhost:4000/auth/login" -Method Post -ContentType "application/json" -Body '{"id_conta":0,"senha":"senha123"}'
$headers = @{ Authorization = "Bearer $($login.access_token)" }

# 2. Consulta o saldo e guarda o vetor atual
$conta = Invoke-RestMethod -Uri "http://localhost:4000/contas/0" -Headers $headers
$vetorAntigo = $conta.vetor_atual

# 3. Faz uma mudanca "por fora" (simulando algo que aconteceu enquanto o app estava offline)
Invoke-RestMethod -Uri "http://localhost:4000/contas/0/depositar" -Method Post -Headers $headers -ContentType "application/json" -Body '{"valor": 10}'

# 4. Tenta sincronizar usando o vetor ANTIGO -> deve dar erro 409
$corpo = @{ tipo = "DEPOSITO"; valor = 50; vetor_conhecido = $vetorAntigo } | ConvertTo-Json
try {
  Invoke-RestMethod -Uri "http://localhost:4000/contas/0/sincronizar" -Method Post -Headers $headers -ContentType "application/json" -Body $corpo
} catch {
  $_.ErrorDetails.Message
}
```
Capture a tela mostrando a última resposta: status 409 com `erro`, `vetor_conhecido`, `vetor_atual` e `conta_atual`.

### 4.7 — `app-offline.png`
**O quê:** o app em modo avião, com uma operação pendente na tela.
**Como:**
1. No emulador Android, abra a gaveta de configurações rápidas (deslize de cima para baixo) e ative o **modo avião**.
2. No app (já logado, na tela principal), toque em **Depositar**, digite um valor, confirme.
3. Deve aparecer a mensagem "Sem conexão agora - o depósito foi guardado...". Volte para a tela principal e capture mostrando o saldo otimista **e** o selo laranja "1 operação(ões) pendente(s) de sincronização".

### 4.8 — `app-sincronizacao.png`
**O quê:** o app sincronizando sozinho ao reconectar.
**Como:** com o app ainda na tela principal mostrando o selo "pendente" (do passo anterior), desative o modo avião no emulador. Sem tocar em mais nada, espere alguns segundos — o app deve detectar a conexão e sincronizar sozinho (o selo "pendente" desaparece e o saldo bate com o valor real). Capture antes/depois, ou grave como GIF curto.

> Dica para reproduzir um **conflito pelo app** (cenário da seção 10.2, item 5, opcional mas recomendado): repita o passo 4.7, e **antes** de desativar o modo avião, mude o saldo da mesma conta "por fora" (ex. com o `Invoke-RestMethod` de depósito do passo 4.6, usando outra conta de rede/terminal). Depois desative o modo avião no app e confirme que ele mostra o aviso de conflito (visível, não escondido) em vez de aplicar errado.

### Funcionalidades extras (3 capturas, uma por extra)

- **`extra-eleicao-sob-demanda/`**: no painel de liderança do app, toque em **"Forçar nova eleição"** e capture o resultado (o histórico de líderes ganhando uma nova entrada).
- **`extra-agencias-ativas/`**: no mesmo painel, capture a lista "Agências" mostrando os indicadores verde/vermelho (derrube uma agência antes, para ter pelo menos uma "fora do ar" na foto).
- **`extra-historico-lideres/`**: capture a lista "Histórico de líderes" do painel, já com pelo menos 2 entradas (da eleição inicial + de um failover ou eleição forçada).

---

## 5. Gravar o vídeo de apresentação

Já deixei um roteiro completo, bloco a bloco, com o que falar e o que fazer em cada momento:

**[`evidencias/sprint3/ROTEIRO_VIDEO_SPRINT3.md`](evidencias/sprint3/ROTEIRO_VIDEO_SPRINT3.md)**

Siga exatamente a ordem dele (ele já assume que você fez os passos 1-4 deste guia). Grave com OBS Studio (tem botão de pausar gravação, usado nos pontos em que você derruba/sobe uma agência). Salve o vídeo final como `evidencias/sprint3/apresentacao-sprint3.mp4`.

---

## 6. Revisão final e commit

1. Dê uma lida no [`RESPOSTAS.md`](RESPOSTAS.md) (seção "Sprint 3") — as respostas já estão escritas, mas vale ajustar para a sua própria voz/palavras antes de entregar, já que você vai precisar defender isso.
2. Depois de colocar os prints e o vídeo nas pastas de `evidencias/sprint3/`, comite:

```powershell
git add evidencias/sprint3
git commit -m "docs(evidencias): adiciona prints e video de apresentacao do Sprint 3"
```

3. Quando quiser subir tudo para o GitHub:
```powershell
git push
```
(Eu não fiz push de nada ainda — os commits estão só no seu repositório local.)

---

## Checklist rápido

- [ ] Android Studio instalado, emulador criado e ligado (`flutter doctor` sem erro de Android)
- [ ] `flutter run` abrindo o app no emulador
- [ ] 3 agências + RabbitMQ rodando juntos
- [ ] `eleicao-inicial.png`
- [ ] `failover.png`
- [ ] `historico-lideranca.png`
- [ ] `app-lider-atual.png`
- [ ] `app-failover.png`
- [ ] `conflito-sincronizacao.png`
- [ ] `app-offline.png`
- [ ] `app-sincronizacao.png`
- [ ] `extra-eleicao-sob-demanda/`
- [ ] `extra-agencias-ativas/`
- [ ] `extra-historico-lideres/`
- [ ] Vídeo `apresentacao-sprint3.mp4`
- [ ] RESPOSTAS.md revisado na sua voz
- [ ] Commit das evidências
- [ ] `git push`
