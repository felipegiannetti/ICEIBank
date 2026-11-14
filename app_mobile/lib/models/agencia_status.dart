class AgenciaStatus {
  final int id;
  final String url;
  final bool ativa;

  const AgenciaStatus({required this.id, required this.url, required this.ativa});

  factory AgenciaStatus.fromJson(Map<String, dynamic> json) =>
      AgenciaStatus(id: json['id'] as int, url: json['url'] as String, ativa: json['ativa'] as bool);
}
