import '../models/agencia_status.dart';
import '../models/evento_lideranca.dart';
import '../models/lider_info.dart';
import 'api_client.dart';

/// Consome as rotas /bully/* (Sprint 3, Partes A/B e os 3 extras). Essas
/// rotas sao publicas (sem JWT) - ver RESPOSTAS.md, Parte A.
class BullyService {
  final ApiClient _client;

  BullyService(this._client);

  Future<LiderInfo> consultarLider() async {
    final dados = await _client.get('/bully/lider', autenticado: false);
    return LiderInfo.fromJson(dados as Map<String, dynamic>);
  }

  /// Funcionalidade adicional: eleição sob demanda.
  Future<void> forcarEleicao() => _client.post('/bully/eleicao/forcar', autenticado: false);

  /// Funcionalidade adicional: indicador de agências ativas.
  Future<List<AgenciaStatus>> agenciasAtivas() async {
    final dados = await _client.get('/bully/agencias-ativas', autenticado: false);
    return ((dados as Map<String, dynamic>)['agencias'] as List)
        .map((e) => AgenciaStatus.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  /// Funcionalidade adicional: histórico de líderes na tela.
  Future<List<EventoLideranca>> historico() async {
    final dados = await _client.get('/bully/historico', autenticado: false);
    return ((dados as Map<String, dynamic>)['linha_do_tempo_lideres'] as List)
        .map((e) => EventoLideranca.fromJson(e as Map<String, dynamic>))
        .toList();
  }
}
