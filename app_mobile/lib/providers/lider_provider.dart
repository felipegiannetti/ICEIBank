import 'dart:async';

import 'package:flutter/foundation.dart';

import '../config/agencias.dart';
import '../models/agencia_status.dart';
import '../models/evento_lideranca.dart';
import '../services/api_client.dart';
import '../services/api_exception.dart';
import '../services/bully_service.dart';

/// Painel de liderança (Sprint 3, Parte D) + os 3 extras (eleição sob
/// demanda, agências ativas, histórico de líderes). Consulta
/// GET /bully/lider periodicamente, com fallback para outra agência
/// conhecida se a atual não responder.
class LiderProvider extends ChangeNotifier {
  static const _intervalo = Duration(seconds: 5);

  int? _liderAtual;
  List<AgenciaStatus> _agenciasAtivas = const [];
  List<EventoLideranca> _historico = const [];
  bool _forcandoEleicao = false;
  String? _erro;
  Timer? _timer;

  int? get liderAtual => _liderAtual;
  List<AgenciaStatus> get agenciasAtivas => _agenciasAtivas;
  List<EventoLideranca> get historico => _historico;
  bool get forcandoEleicao => _forcandoEleicao;
  String? get erro => _erro;

  void iniciar() {
    _consultarTudo();
    _timer ??= Timer.periodic(_intervalo, (_) => _consultarTudo());
  }

  Future<void> atualizar() => _consultarTudo();

  @override
  void dispose() {
    _timer?.cancel();
    super.dispose();
  }

  Future<void> _consultarTudo() async {
    await _consultarLiderComFallback();
    await _consultarAgenciasAtivas();
    await _consultarHistorico();
  }

  /// Tenta /bully/lider em cada agência conhecida, na ordem, até uma
  /// responder - a resposta diz qual é a líder do ponto de vista dela.
  Future<void> _consultarLiderComFallback() async {
    for (final agencia in agencias) {
      try {
        final bully = BullyService(ApiClient(agenciaUrl: agencia.url));
        final info = await bully.consultarLider();
        _liderAtual = info.liderAtual;
        _erro = null;
        notifyListeners();
        return;
      } on ApiException {
        continue; // essa agência não respondeu - tenta a próxima
      }
    }
    _erro = 'Nenhuma das agências respondeu.';
    notifyListeners();
  }

  Future<void> _consultarAgenciasAtivas() async {
    for (final agencia in agencias) {
      try {
        final bully = BullyService(ApiClient(agenciaUrl: agencia.url));
        _agenciasAtivas = await bully.agenciasAtivas();
        notifyListeners();
        return;
      } on ApiException {
        continue;
      }
    }
  }

  Future<void> _consultarHistorico() async {
    for (final agencia in agencias) {
      try {
        final bully = BullyService(ApiClient(agenciaUrl: agencia.url));
        _historico = await bully.historico();
        notifyListeners();
        return;
      } on ApiException {
        continue;
      }
    }
  }

  /// Funcionalidade adicional: eleição sob demanda.
  Future<void> forcarEleicao() async {
    _forcandoEleicao = true;
    notifyListeners();
    for (final agencia in agencias) {
      try {
        final bully = BullyService(ApiClient(agenciaUrl: agencia.url));
        await bully.forcarEleicao();
        break;
      } on ApiException {
        continue;
      }
    }
    await Future.delayed(const Duration(seconds: 1)); // dá tempo da eleição rodar
    await _consultarTudo();
    _forcandoEleicao = false;
    notifyListeners();
  }
}
