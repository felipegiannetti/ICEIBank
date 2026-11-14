import 'dart:math';

import 'package:flutter/foundation.dart';

import '../models/conta.dart';
import '../models/operacao_pendente.dart';
import '../services/api_exception.dart';
import '../services/conta_service.dart';
import '../services/storage_service.dart';
import 'auth_provider.dart';

/// Fluxo bancário (Sprint 1/2: saldo, depósito, saque, transferência) +
/// offline-first (Sprint 3, Parte F): toda operação de escrita tenta ir
/// direto para a agência; se não houver conexão (ApiException.semConexao),
/// cai para a fila de pendentes com atualização otimista local.
class ContaProvider extends ChangeNotifier {
  final AuthProvider _auth;
  final StorageService _storage;
  late ContaService _service;

  Conta? _conta;
  bool _carregando = false;
  String? _erro;
  List<OperacaoPendente> _pendentes = [];

  ContaProvider(this._auth, this._storage) {
    _service = ContaService(_auth.apiClient);
  }

  Conta? get conta => _conta;
  bool get carregando => _carregando;
  String? get erro => _erro;
  List<OperacaoPendente> get pendentes => List.unmodifiable(_pendentes);

  /// Saldo otimista: saldo oficial (ultima leitura/sincronizacao
  /// confirmada pelo backend) + o efeito de cada operacao ainda pendente.
  double get saldoExibido {
    final base = _conta?.saldo ?? 0;
    return _pendentes.fold<double>(
      base,
      (acc, op) => op.tipo == TipoOperacao.deposito ? acc + op.valor : acc - op.valor,
    );
  }

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

    _pendentes = _storage.listarPendentes(idConta);
    try {
      _conta = await _service.consultarSaldo(idConta);
      await _storage.salvarContaCache(idConta, saldo: _conta!.saldo, vetorAtual: _conta!.vetorAtual ?? const []);
    } on ApiException catch (erro) {
      if (erro.semConexao) {
        final cache = _storage.contaCache(idConta);
        if (cache != null) {
          _conta = Conta(
            id: idConta,
            nomeAluno: _conta?.nomeAluno ?? '',
            saldo: (cache['saldo'] as num).toDouble(),
            vetorAtual: (cache['vetorAtual'] as List).map((e) => e as int).toList(),
          );
          _erro = 'Sem conexão - mostrando o último saldo conhecido.';
        } else {
          _erro = 'Sem conexão e sem dados salvos localmente ainda.';
        }
      } else {
        _erro = erro.mensagem;
      }
    }

    _carregando = false;
    notifyListeners();
  }

  Future<String?> depositar(double valor) => _operar(TipoOperacao.deposito, valor);
  Future<String?> sacar(double valor) => _operar(TipoOperacao.saque, valor);

  /// Tenta a operação online; se não houver conexão, guarda como pendente
  /// com atualização otimista. Retorna uma mensagem de erro "de negócio"
  /// (ex.: saldo insuficiente) ou null se deu certo / ficou pendente.
  Future<String?> _operar(TipoOperacao tipo, double valor) async {
    final idConta = _auth.idConta;
    if (idConta == null) return 'Sessão inválida.';

    try {
      _conta = tipo == TipoOperacao.deposito
          ? await _service.depositar(idConta, valor)
          : await _service.sacar(idConta, valor);
      await _storage.salvarContaCache(idConta, saldo: _conta!.saldo, vetorAtual: _conta!.vetorAtual ?? const []);
      notifyListeners();
      return null;
    } on ApiException catch (erro) {
      if (!erro.semConexao) {
        notifyListeners();
        return erro.mensagem;
      }
    }

    // Sem conexão: UI otimista - guarda na fila de pendentes com o vetor
    // conhecido mais recente (da última leitura/sincronização bem sucedida).
    final vetorConhecido = _conta?.vetorAtual ?? const [0, 0, 0];
    final operacao = OperacaoPendente(
      id: _gerarIdLocal(),
      idConta: idConta,
      tipo: tipo,
      valor: valor,
      vetorConhecido: vetorConhecido,
      criadaEm: DateTime.now(),
    );
    await _storage.salvarPendente(operacao);
    _pendentes = _storage.listarPendentes(idConta);
    notifyListeners();
    return null;
  }

  Future<String?> transferir(int idDestino, double valor) async {
    final idConta = _auth.idConta;
    if (idConta == null) return 'Sessão inválida.';
    // Transferências sempre exigem conexão - não entram na fila offline
    // (o endpoint /sincronizar só cobre depósito/saque; ver RESPOSTAS.md).
    try {
      await _service.transferir(idConta, idDestino, valor);
      await carregar();
      return null;
    } on ApiException catch (erro) {
      return erro.mensagem;
    }
  }

  /// Chamado pela FilaPendenteProvider depois de sincronizar (200 ou 409) -
  /// atualiza o saldo/vetor oficiais e a lista de pendentes.
  void aplicarContaAtualizada(Conta contaAtualizada) {
    _conta = contaAtualizada;
    _storage.salvarContaCache(_conta!.id, saldo: _conta!.saldo, vetorAtual: _conta!.vetorAtual ?? const []);
    recarregarPendentes();
  }

  void recarregarPendentes() {
    final idConta = _auth.idConta;
    if (idConta != null) {
      _pendentes = _storage.listarPendentes(idConta);
    }
    notifyListeners();
  }

  String _gerarIdLocal() {
    final aleatorio = Random().nextInt(999999);
    return '${DateTime.now().microsecondsSinceEpoch}-$aleatorio';
  }
}
