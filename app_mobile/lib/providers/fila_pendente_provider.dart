import 'dart:async';

import 'package:flutter/foundation.dart';

import '../models/operacao_pendente.dart';
import '../services/api_exception.dart';
import '../services/connectivity_service.dart';
import '../services/conta_service.dart';
import '../services/storage_service.dart';
import 'auth_provider.dart';
import 'conta_provider.dart';

/// Sincroniza a fila de operações pendentes (Sprint 3, Parte F) assim que a
/// conectividade volta, sem a pessoa usuária precisar tocar em nada.
class FilaPendenteProvider extends ChangeNotifier {
  final AuthProvider _auth;
  final StorageService _storage;
  final ContaProvider _contaProvider;
  late ContaService _service;
  StreamSubscription<bool>? _assinatura;

  bool _sincronizando = false;
  final List<String> _ultimosConflitos = [];

  FilaPendenteProvider(this._auth, this._storage, this._contaProvider, ConnectivityService connectivity) {
    _service = ContaService(_auth.apiClient);
    _assinatura = connectivity.mudancas.listen((conectado) {
      if (conectado) sincronizarTudo();
    });
  }

  bool get sincronizando => _sincronizando;
  List<String> get ultimosConflitos => List.unmodifiable(_ultimosConflitos);

  /// Chamado pelo ChangeNotifierProxyProvider quando o AuthProvider muda.
  void atualizarCliente() {
    _service = ContaService(_auth.apiClient);
  }

  Future<void> sincronizarTudo() async {
    final idConta = _auth.idConta;
    if (idConta == null || _sincronizando) return;

    final pendentes = _storage.listarPendentes(idConta);
    if (pendentes.isEmpty) return;

    _sincronizando = true;
    notifyListeners();

    for (final operacao in pendentes) {
      try {
        final contaAtualizada = await _service.sincronizar(
          idConta: operacao.idConta,
          tipo: operacao.tipo.valorApi,
          valor: operacao.valor,
          vetorConhecido: operacao.vetorConhecido,
        );
        await _storage.removerPendente(operacao.id);
        _contaProvider.aplicarContaAtualizada(contaAtualizada);
      } on ApiException catch (erro) {
        if (erro.semConexao) {
          // Ainda sem conexão de fato (falso positivo do connectivity_plus,
          // ou a agência caiu) - interrompe e tenta tudo de novo na próxima vez.
          break;
        }

        // 409 (conflito de vetor) ou erro "de negócio" (ex.: saldo
        // insuficiente no momento da sincronização): decisão de design
        // (ver RESPOSTAS.md, Parte E/F) - descarta a operação em vez de
        // tentar de novo sozinha (evita risco de aplicar duas vezes ou
        // entrar em loop) e avisa a pessoa usuária de forma visível.
        await _storage.removerPendente(operacao.id);
        _registrarConflito(operacao, erro);
      }
    }

    _contaProvider.recarregarPendentes();
    _sincronizando = false;
    notifyListeners();
  }

  void _registrarConflito(OperacaoPendente operacao, ApiException erro) {
    final descricaoTipo = operacao.tipo == TipoOperacao.deposito ? 'Depósito' : 'Saque';
    if (erro.status == 409) {
      final contaAtual = erro.dados is Map ? (erro.dados as Map)['conta_atual'] as Map? : null;
      if (contaAtual != null) {
        _storage.salvarContaCache(
          operacao.idConta,
          saldo: (contaAtual['saldo'] as num).toDouble(),
          vetorAtual: (contaAtual['vetor_atual'] as List).map((e) => e as int).toList(),
        );
      }
      _ultimosConflitos.insert(
        0,
        '$descricaoTipo de R\$ ${operacao.valor.toStringAsFixed(2)} não pôde ser sincronizado: '
        'o saldo da conta mudou enquanto o app estava offline.',
      );
    } else {
      _ultimosConflitos.insert(0, '$descricaoTipo de R\$ ${operacao.valor.toStringAsFixed(2)} rejeitado: ${erro.mensagem}');
    }
  }

  void limparConflitos() {
    _ultimosConflitos.clear();
    notifyListeners();
  }

  @override
  void dispose() {
    _assinatura?.cancel();
    super.dispose();
  }
}
