class LiderInfo {
  final int idAgencia;
  final int? liderAtual;

  const LiderInfo({required this.idAgencia, required this.liderAtual});

  factory LiderInfo.fromJson(Map<String, dynamic> json) =>
      LiderInfo(idAgencia: json['id_agencia'] as int, liderAtual: json['lider_atual'] as int?);
}
