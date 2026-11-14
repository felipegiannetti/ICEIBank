import 'package:flutter/material.dart';

import '../models/agencia_status.dart';

/// Funcionalidade adicional: indicador de agências ativas.
class AgenciaStatusBadge extends StatelessWidget {
  final AgenciaStatus status;
  final bool ehLider;

  const AgenciaStatusBadge({super.key, required this.status, this.ehLider = false});

  @override
  Widget build(BuildContext context) {
    final cor = status.ativa ? Colors.green : Colors.red;
    return ListTile(
      leading: Icon(Icons.circle, color: cor, size: 16),
      title: Text('Agência ${status.id}${ehLider ? " (líder)" : ""}'),
      subtitle: Text(status.url),
      trailing: Text(status.ativa ? 'ativa' : 'fora do ar'),
    );
  }
}
