class Conta {
  final int id;
  final String nomeAluno;
  final double saldo;
  final List<int>? vetorAtual;

  const Conta({required this.id, required this.nomeAluno, required this.saldo, this.vetorAtual});

  factory Conta.fromJson(Map<String, dynamic> json) => Conta(
        id: json['id'] as int,
        nomeAluno: json['nome_aluno'] as String? ?? '',
        saldo: (json['saldo'] as num).toDouble(),
        vetorAtual: (json['vetor_atual'] as List?)?.map((e) => e as int).toList(),
      );
}
