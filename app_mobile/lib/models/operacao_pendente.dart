enum TipoOperacao { deposito, saque }

extension TipoOperacaoApi on TipoOperacao {
  /// Valor exatamente como a API espera (ver SincronizarRequest.tipo no backend).
  String get valorApi => this == TipoOperacao.deposito ? 'DEPOSITO' : 'SAQUE';
}

/// Operacao de deposito/saque feita offline, guardada localmente (Hive) ate
/// ser sincronizada com a agencia (Sprint 3, Parte F). Guardada como Map
/// simples (sem TypeAdapter gerado por build_runner) - decisao deliberada
/// para nao depender de code generation (ver RESPOSTAS.md).
class OperacaoPendente {
  final String id; // id local (nao e o id da conta) - so para remover da fila depois
  final int idConta;
  final TipoOperacao tipo;
  final double valor;
  final List<int> vetorConhecido;
  final DateTime criadaEm;

  const OperacaoPendente({
    required this.id,
    required this.idConta,
    required this.tipo,
    required this.valor,
    required this.vetorConhecido,
    required this.criadaEm,
  });

  Map<String, dynamic> toMap() => {
        'id': id,
        'idConta': idConta,
        'tipo': tipo.name,
        'valor': valor,
        'vetorConhecido': vetorConhecido,
        'criadaEm': criadaEm.toIso8601String(),
      };

  factory OperacaoPendente.fromMap(Map<dynamic, dynamic> map) => OperacaoPendente(
        id: map['id'] as String,
        idConta: map['idConta'] as int,
        tipo: TipoOperacao.values.byName(map['tipo'] as String),
        valor: (map['valor'] as num).toDouble(),
        vetorConhecido: (map['vetorConhecido'] as List).map((e) => e as int).toList(),
        criadaEm: DateTime.parse(map['criadaEm'] as String),
      );
}
