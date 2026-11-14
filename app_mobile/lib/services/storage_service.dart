import '../config/agencias.dart';

/// Estado de sessao (token/idConta/agenciaUrl) - mirror simples, em memoria,
/// de frontend/src/api/client.js (Sprint 1). Sera substituido por
/// armazenamento persistente (Hive) na Parte F, junto com o cache de conta
/// e a fila de operacoes pendentes do modo offline-first.
class StorageService {
  String? _token;
  int? _idConta;
  String? _agenciaUrl;

  String? get token => _token;
  int? get idConta => _idConta;
  String get agenciaUrl => _agenciaUrl ?? agencias.first.url;

  Future<void> salvarSessao({required String token, required int idConta}) async {
    _token = token;
    _idConta = idConta;
  }

  Future<void> salvarAgenciaUrl(String url) async {
    _agenciaUrl = url;
  }

  Future<void> limparSessao() async {
    _token = null;
    _idConta = null;
  }
}
