import 'package:flutter/material.dart';

class SaldoCard extends StatelessWidget {
  final bool carregando;
  final double saldo;
  final int pendentes;

  const SaldoCard({super.key, required this.carregando, required this.saldo, required this.pendentes});

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Saldo', style: Theme.of(context).textTheme.labelLarge),
            const SizedBox(height: 8),
            carregando
                ? const SizedBox(height: 32, width: 32, child: CircularProgressIndicator(strokeWidth: 3))
                : Text('R\$ ${saldo.toStringAsFixed(2)}', style: Theme.of(context).textTheme.headlineMedium),
            if (pendentes > 0) ...[
              const SizedBox(height: 12),
              Chip(
                avatar: const Icon(Icons.sync_problem, size: 18),
                label: Text('$pendentes operação(ões) pendente(s) de sincronização'),
                backgroundColor: Colors.orange.withValues(alpha: 0.15),
              ),
            ],
          ],
        ),
      ),
    );
  }
}
