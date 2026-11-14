import 'api_client.dart';

/// Espelha frontend/src/api/client.js::api.login (Sprint 1).
class AuthService {
  final ApiClient _client;

  AuthService(this._client);

  /// Retorna o access_token (JWT) recebido do backend.
  Future<String> login(int idConta, String senha) async {
    final dados = await _client.post(
      '/auth/login',
      corpo: {'id_conta': idConta, 'senha': senha},
      autenticado: false,
    );
    return dados['access_token'] as String;
  }
}
