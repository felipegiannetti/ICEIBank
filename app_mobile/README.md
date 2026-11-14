# ICEIBank - App mobile (Flutter)

App Flutter do Sprint 3: fluxo bancário completo (login, saldo, depósito, saque, transferência) e painel de liderança (eleição Bully).

Este código foi escrito **sem o Flutter SDK instalado na máquina onde foi gerado** - por isso os passos abaixo incluem comandos que você precisa rodar localmente antes do primeiro `flutter run`.

## 1. Gerar as pastas de plataforma (android/ios/...)

Este diretório só tem `pubspec.yaml` e `lib/` - as pastas `android/`, `ios/` etc. (geradas normalmente por `flutter create`) ainda não existem. Dentro de `app_mobile/`, rode:

```bash
flutter create . --project-name app_mobile --org com.iceibank
```

Isso cria as pastas de plataforma preservando o `pubspec.yaml` e o `lib/` já escritos.

## 2. Instalar as dependências

```bash
flutter pub get
```

Depois disso, rode `flutter analyze` para pegar qualquer erro de sintaxe/import antes de abrir o emulador.

## 3. Liberar tráfego HTTP (sem TLS) no Android

O backend roda em `http://` (sem HTTPS), e o Android bloqueia tráfego não criptografado por padrão a partir da API 28. Depois do passo 1, edite `android/app/src/main/AndroidManifest.xml` e adicione `android:usesCleartextTraffic="true"` na tag `<application>`:

```xml
<application
    android:usesCleartextTraffic="true"
    ...>
```

(No iOS, se for testar no simulador, adicione uma exceção de App Transport Security equivalente em `ios/Runner/Info.plist` caso necessário.)

## 4. Apontar para as 3 agências

Veja `lib/config/agencias.dart`. O padrão já usa `10.0.2.2` (o alias do emulador Android para o `localhost` do seu PC):

- **Emulador Android**: já funciona com o padrão (`10.0.2.2`).
- **Simulador iOS**: troque para `127.0.0.1`.
- **Dispositivo físico** (USB ou mesma rede Wi-Fi do seu PC): troque pelo IP da sua máquina na rede local, ex. `http://192.168.0.10:4000`.

## 5. Rodar

Com as 3 agências (Sprint 1/2/3) e o RabbitMQ no ar:

```bash
flutter run
```

## Decisões de implementação (ver RESPOSTAS.md para a versão completa)

- **State management**: `provider` (ChangeNotifier) - `AuthProvider` espelha `frontend/src/context/AuthContext.jsx`.
- **Painel de liderança**: consulta `GET /bully/lider` a cada 5s, com fallback sequencial pelas 3 agências conhecidas se a atual não responder.
