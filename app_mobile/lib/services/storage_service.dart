import 'package:hive_flutter/hive_flutter.dart';

import '../config/agencias.dart';
import '../models/operacao_pendente.dart';

/// Armazenamento local (Sprint 3 - offline-first): sessao (mirror do
/// localStorage do frontend web), cache de saldo/vetor por conta, e a fila
/// de operacoes pendentes de sincronizacao. Guarda tudo como Maps/valores
/// primitivos simples - sem TypeAdapter gerado por build_runner (decisao
/// deliberada, ver RESPOSTAS.md).
class StorageService {
  static const _boxSessao = 'sessao';
  static const _boxContaCache = 'conta_cache';
  static const _boxFilaPendente = 'fila_pendente';

  static Future<void> iniciar() async {
    await Hive.initFlutter();
    await Hive.openBox(_boxSessao);
    await Hive.openBox(_boxContaCache);
    await Hive.openBox(_boxFilaPendente);
  }

  Box get _sessao => Hive.box(_boxSessao);
  Box get _contaCache => Hive.box(_boxContaCache);
  Box get _filaPendente => Hive.box(_boxFilaPendente);

  // --- sessao (token/idConta/agenciaUrl) ------------------------------

  String? get token => _sessao.get('token') as String?;
  int? get idConta => _sessao.get('idConta') as int?;
  String get agenciaUrl => (_sessao.get('agenciaUrl') as String?) ?? agencias.first.url;

  Future<void> salvarSessao({required String token, required int idConta}) async {
    await _sessao.put('token', token);
    await _sessao.put('idConta', idConta);
  }

  Future<void> salvarAgenciaUrl(String url) => _sessao.put('agenciaUrl', url);

  Future<void> limparSessao() async {
    await _sessao.delete('token');
    await _sessao.delete('idConta');
  }

  // --- cache de conta (saldo + vetor_atual mais recentes) -------------

  Map<String, dynamic>? contaCache(int idConta) {
    final valor = _contaCache.get(idConta.toString());
    return valor == null ? null : Map<String, dynamic>.from(valor as Map);
  }

  Future<void> salvarContaCache(int idConta, {required double saldo, required List<int> vetorAtual}) =>
      _contaCache.put(idConta.toString(), {'saldo': saldo, 'vetorAtual': vetorAtual});

  // --- fila de operacoes pendentes -------------------------------------

  List<OperacaoPendente> listarPendentes(int idConta) {
    final lista = _filaPendente.values
        .map((v) => OperacaoPendente.fromMap(v as Map))
        .where((op) => op.idConta == idConta)
        .toList();
    lista.sort((a, b) => a.criadaEm.compareTo(b.criadaEm));
    return lista;
  }

  Future<void> salvarPendente(OperacaoPendente operacao) => _filaPendente.put(operacao.id, operacao.toMap());

  Future<void> removerPendente(String id) => _filaPendente.delete(id);
}
