import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../providers/lider_provider.dart';
import '../widgets/agencia_status_badge.dart';

/// Sprint 3, Parte D (painel de liderança) + os 3 extras: eleição sob
/// demanda, indicador de agências ativas, histórico de líderes na tela.
class PainelLiderancaScreen extends StatelessWidget {
  const PainelLiderancaScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final lider = context.watch<LiderProvider>();

    return Scaffold(
      appBar: AppBar(title: const Text('Painel de liderança')),
      body: RefreshIndicator(
        onRefresh: () => lider.atualizar(),
        child: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('Líder atual', style: Theme.of(context).textTheme.labelLarge),
                    const SizedBox(height: 8),
                    Text(
                      lider.liderAtual != null ? 'Agência ${lider.liderAtual}' : 'Desconhecida',
                      style: Theme.of(context).textTheme.headlineSmall,
                    ),
                    if (lider.erro != null) ...[
                      const SizedBox(height: 8),
                      Text(lider.erro!, style: const TextStyle(color: Colors.red)),
                    ],
                  ],
                ),
              ),
            ),
            const SizedBox(height: 16),
            FilledButton.icon(
              icon: lider.forcandoEleicao
                  ? const SizedBox(width: 16, height: 16, child: CircularProgressIndicator(strokeWidth: 2))
                  : const Icon(Icons.how_to_vote),
              label: const Text('Forçar nova eleição'),
              onPressed: lider.forcandoEleicao ? null : lider.forcarEleicao,
            ),
            const SizedBox(height: 24),
            Text('Agências', style: Theme.of(context).textTheme.titleMedium),
            if (lider.agenciasAtivas.isEmpty) const Text('Consultando...'),
            ...lider.agenciasAtivas.map((a) => AgenciaStatusBadge(status: a, ehLider: a.id == lider.liderAtual)),
            const SizedBox(height: 24),
            Text('Histórico de líderes', style: Theme.of(context).textTheme.titleMedium),
            if (lider.historico.isEmpty) const Text('Nenhuma troca de liderança registrada ainda.'),
            ...lider.historico.reversed.map(
              (e) => ListTile(
                leading: const Icon(Icons.flag_outlined),
                title: Text('Agência ${e.detalhes['id_agencia']} tornou-se líder'),
                subtitle: Text(e.horaParede),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
