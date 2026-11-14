import 'package:flutter/material.dart';

class ErroBanner extends StatelessWidget {
  final String mensagem;

  const ErroBanner({super.key, required this.mensagem});

  @override
  Widget build(BuildContext context) {
    final cores = Theme.of(context).colorScheme;
    return Container(
      margin: const EdgeInsets.only(bottom: 16),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(color: cores.errorContainer, borderRadius: BorderRadius.circular(8)),
      child: Row(
        children: [
          Icon(Icons.error_outline, color: cores.onErrorContainer),
          const SizedBox(width: 8),
          Expanded(child: Text(mensagem, style: TextStyle(color: cores.onErrorContainer))),
        ],
      ),
    );
  }
}
