class EventoLideranca {
  final String agencia;
  final String tipo;
  final List<int> vetor;
  final String horaParede;
  final Map<String, dynamic> detalhes;

  const EventoLideranca({
    required this.agencia,
    required this.tipo,
    required this.vetor,
    required this.horaParede,
    required this.detalhes,
  });

  factory EventoLideranca.fromJson(Map<String, dynamic> json) => EventoLideranca(
        agencia: json['agencia'] as String,
        tipo: json['tipo'] as String,
        vetor: (json['timestamp_vetorial'] as List).map((e) => e as int).toList(),
        horaParede: json['hora_parede'] as String,
        detalhes: Map<String, dynamic>.from(json['detalhes'] as Map),
      );
}
