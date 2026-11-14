import 'package:flutter/material.dart';

class SaldoCard extends StatelessWidget {
  final bool carregando;
  final double saldo;

  const SaldoCard({super.key, required this.carregando, required this.saldo});

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
          ],
        ),
      ),
    );
  }
}
