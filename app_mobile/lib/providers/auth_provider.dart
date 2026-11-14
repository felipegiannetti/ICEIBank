import 'package:flutter/foundation.dart';

import '../services/api_client.dart';
import '../services/auth_service.dart';
import '../services/storage_service.dart';

/// Espelha frontend/src/context/AuthContext.jsx (Sprint 1): guarda
/// token/idConta, expoe login/logout/autenticado. Usa Hive (via
/// StorageService) no lugar do localStorage do navegador.
class AuthProvider extends ChangeNotifier {
  final StorageService _storage;

  String? _token;
  int? _idConta;
  String _agenciaUrl;

  AuthProvider(this._storage)
      : _token = _storage.token,
        _idConta = _storage.idConta,
        _agenciaUrl = _storage.agenciaUrl;

  String? get token => _token;
  int? get idConta => _idConta;
  String get agenciaUrl => _agenciaUrl;
  bool get autenticado => _token != null && _idConta != null;

  ApiClient get apiClient => ApiClient(agenciaUrl: _agenciaUrl, token: _token);

  Future<void> trocarAgencia(String url) async {
    _agenciaUrl = url;
    await _storage.salvarAgenciaUrl(url);
    notifyListeners();
  }

  Future<void> login(int idConta, String senha) async {
    final authService = AuthService(ApiClient(agenciaUrl: _agenciaUrl));
    final token = await authService.login(idConta, senha);
    await _storage.salvarSessao(token: token, idConta: idConta);
    _token = token;
    _idConta = idConta;
    notifyListeners();
  }

  Future<void> logout() async {
    await _storage.limparSessao();
    _token = null;
    _idConta = null;
    notifyListeners();
  }
}
