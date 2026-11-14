import 'package:connectivity_plus/connectivity_plus.dart';

/// Deteccao de conectividade (Sprint 3 - offline-first): o Stream dispara
/// quando ha (ou deixa de haver) alguma interface de rede ativa, para a
/// FilaPendenteProvider tentar sincronizar automaticamente ao reconectar.
/// connectivity_plus so sabe dizer se existe uma interface de rede ativa -
/// nao garante que a agencia especifica esteja alcancavel; essa
/// confirmacao real so vem quando a chamada HTTP de sincronizacao funciona.
class ConnectivityService {
  Stream<bool> get mudancas => Connectivity()
      .onConnectivityChanged
      .map((resultados) => resultados.any((r) => r != ConnectivityResult.none));

  Future<bool> estaConectado() async {
    final resultados = await Connectivity().checkConnectivity();
    return resultados.any((r) => r != ConnectivityResult.none);
  }
}
