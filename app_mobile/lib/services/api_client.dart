import 'dart:convert';
import 'dart:io';

import 'package:http/http.dart' as http;

import 'api_exception.dart';

/// Cliente HTTP generico - espelha frontend/src/api/client.js (Sprint 1):
/// mesma convencao de erro do backend ({"erro": "..."}), mesmo header
/// "Authorization: Bearer <token>".
class ApiClient {
  final String agenciaUrl;
  final String? token;
  final Duration timeout;

  ApiClient({required this.agenciaUrl, this.token, this.timeout = const Duration(seconds: 5)});

  Future<dynamic> _requisitar(
    String metodo,
    String caminho, {
    Map<String, dynamic>? corpo,
    bool autenticado = true,
  }) async {
    final uri = Uri.parse('$agenciaUrl$caminho');
    final headers = {'Content-Type': 'application/json'};
    if (autenticado && token != null) {
      headers['Authorization'] = 'Bearer $token';
    }

    http.Response resposta;
    try {
      final corpoJson = corpo != null ? jsonEncode(corpo) : null;
      if (metodo == 'GET') {
        resposta = await http.get(uri, headers: headers).timeout(timeout);
      } else if (metodo == 'POST') {
        resposta = await http.post(uri, headers: headers, body: corpoJson).timeout(timeout);
      } else if (metodo == 'PUT') {
        resposta = await http.put(uri, headers: headers, body: corpoJson).timeout(timeout);
      } else {
        throw ArgumentError('Método HTTP não suportado: $metodo');
      }
    } on SocketException {
      throw ApiException(0, 'Não foi possível conectar à agência. Verifique sua conexão ou o servidor.');
    } on HttpException {
      throw ApiException(0, 'Não foi possível conectar à agência.');
    } on FormatException {
      rethrow;
    } catch (_) {
      // TimeoutException ou qualquer outra falha de rede - tratada igual a
      // "sem conexao", que e o sinal usado pelo fluxo offline-first.
      throw ApiException(0, 'Não foi possível conectar à agência (tempo esgotado).');
    }

    dynamic dados;
    try {
      dados = resposta.body.isNotEmpty ? jsonDecode(resposta.body) : null;
    } catch (_) {
      dados = null;
    }

    if (resposta.statusCode < 200 || resposta.statusCode >= 300) {
      final mensagem = (dados is Map && dados['erro'] != null) ? dados['erro'] as String : 'Erro ${resposta.statusCode}';
      throw ApiException(resposta.statusCode, mensagem, dados: dados);
    }

    return dados;
  }

  Future<dynamic> get(String caminho, {bool autenticado = true}) =>
      _requisitar('GET', caminho, autenticado: autenticado);

  Future<dynamic> post(String caminho, {Map<String, dynamic>? corpo, bool autenticado = true}) =>
      _requisitar('POST', caminho, corpo: corpo, autenticado: autenticado);

  Future<dynamic> put(String caminho, {Map<String, dynamic>? corpo, bool autenticado = true}) =>
      _requisitar('PUT', caminho, corpo: corpo, autenticado: autenticado);
}
