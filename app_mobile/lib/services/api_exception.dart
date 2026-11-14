class ApiException implements Exception {
  final int status;
  final String mensagem;

  /// Corpo JSON decodificado da resposta de erro, quando houver (ex.: o 409
  /// de /contas/{id}/sincronizar traz vetor_conhecido/vetor_atual/conta_atual).
  final dynamic dados;

  ApiException(this.status, this.mensagem, {this.dados});

  /// true quando a chamada nem chegou a sair (sem rede, host fora do ar,
  /// tempo esgotado) - e o sinal usado pelo fluxo offline-first para
  /// decidir se guarda a operacao na fila local em vez de so mostrar erro.
  bool get semConexao => status == 0;

  @override
  String toString() => mensagem;
}
