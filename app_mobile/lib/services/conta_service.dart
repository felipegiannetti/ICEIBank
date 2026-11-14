import '../models/conta.dart';
import 'api_client.dart';

/// Fluxo bancario (Sprint 1/2) + sincronizacao offline-first (Sprint 3,
/// Parte E) - espelha frontend/src/api/client.js::api (saldo, deposito,
/// saque, transferencia) e adiciona /sincronizar.
class ContaService {
  final ApiClient _client;

  ContaService(this._client);

  Future<Conta> consultarSaldo(int id) async {
    final dados = await _client.get('/contas/$id');
    return Conta.fromJson(dados as Map<String, dynamic>);
  }

  Future<Conta> depositar(int id, double valor) async {
    final dados = await _client.post('/contas/$id/depositar', corpo: {'valor': valor});
    return Conta.fromJson(dados as Map<String, dynamic>);
  }

  Future<Conta> sacar(int id, double valor) async {
    final dados = await _client.post('/contas/$id/sacar', corpo: {'valor': valor});
    return Conta.fromJson(dados as Map<String, dynamic>);
  }

  Future<Map<String, dynamic>> transferir(int idOrigem, int idDestino, double valor) async {
    final dados = await _client.post(
      '/transferencias',
      corpo: {'id_origem': idOrigem, 'id_destino': idDestino, 'valor': valor},
    );
    return dados as Map<String, dynamic>;
  }

  /// Sprint 3 - offline-first (Parte E). Em caso de conflito, a ApiException
  /// lancada tem status 409 e `dados` preenchido com
  /// {erro, vetor_conhecido, vetor_atual, conta_atual} - quem chama
  /// (FilaPendenteProvider) decide o que fazer.
  Future<Conta> sincronizar({
    required int idConta,
    required String tipo,
    required double valor,
    required List<int> vetorConhecido,
  }) async {
    final dados = await _client.post(
      '/contas/$idConta/sincronizar',
      corpo: {'tipo': tipo, 'valor': valor, 'vetor_conhecido': vetorConhecido},
    );
    return Conta.fromJson(dados as Map<String, dynamic>);
  }
}
