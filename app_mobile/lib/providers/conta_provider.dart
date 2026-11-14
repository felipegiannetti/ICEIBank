import 'package:flutter/foundation.dart';

import '../models/conta.dart';
import '../services/api_exception.dart';
import '../services/conta_service.dart';
import 'auth_provider.dart';

/// Fluxo bancário (Sprint 1/2): saldo, depósito, saque, transferência.
class ContaProvider extends ChangeNotifier {
  final AuthProvider _auth;
  late ContaService _service;

  Conta? _conta;
  bool _carregando = false;
  String? _erro;

  ContaProvider(this._auth) {
    _service = ContaService(_auth.apiClient);
  }

  Conta? get conta => _conta;
  bool get carregando => _carregando;
  String? get erro => _erro;

  /// Chamado pelo ChangeNotifierProxyProvider quando o AuthProvider muda
  /// (login, troca de agência) - recria o cliente HTTP com as credenciais atuais.
  void atualizarCliente() {
    _service = ContaService(_auth.apiClient);
  }

  Future<void> carregar() async {
    final idConta = _auth.idConta;
    if (idConta == null) return;
    _carregando = true;
    _erro = null;
    notifyListeners();

    try {
      _conta = await _service.consultarSaldo(idConta);
    } on ApiException catch (erro) {
      _erro = erro.mensagem;
    }

    _carregando = false;
    notifyListeners();
  }

  Future<String?> depositar(double valor) => _operar(() => _service.depositar(_auth.idConta!, valor));
  Future<String?> sacar(double valor) => _operar(() => _service.sacar(_auth.idConta!, valor));

  Future<String?> _operar(Future<Conta> Function() chamada) async {
    if (_auth.idConta == null) return 'Sessão inválida.';
    try {
      _conta = await chamada();
      notifyListeners();
      return null;
    } on ApiException catch (erro) {
      notifyListeners();
      return erro.mensagem;
    }
  }

  Future<String?> transferir(int idDestino, double valor) async {
    final idConta = _auth.idConta;
    if (idConta == null) return 'Sessão inválida.';
    try {
      await _service.transferir(idConta, idDestino, valor);
      await carregar();
      return null;
    } on ApiException catch (erro) {
      return erro.mensagem;
    }
  }
}
