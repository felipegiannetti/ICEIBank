import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../providers/auth_provider.dart';
import '../providers/conta_provider.dart';
import '../providers/fila_pendente_provider.dart';
import '../widgets/erro_banner.dart';
import '../widgets/saldo_card.dart';
import 'deposito_screen.dart';
import 'painel_lideranca_screen.dart';
import 'saque_screen.dart';
import 'transferencia_screen.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  @override
  void initState() {
    super.initState();
    Future.microtask(() {
      if (!mounted) return;
      context.read<ContaProvider>().carregar();
      context.read<FilaPendenteProvider>().sincronizarTudo();
    });
  }

  @override
  Widget build(BuildContext context) {
    final conta = context.watch<ContaProvider>();
    final auth = context.watch<AuthProvider>();
    final fila = context.watch<FilaPendenteProvider>();

    return Scaffold(
      appBar: AppBar(
        title: Text('Conta ${auth.idConta ?? ''}'),
        actions: [
          IconButton(
            icon: const Icon(Icons.account_tree_outlined),
            tooltip: 'Painel de liderança',
            onPressed: () =>
                Navigator.of(context).push(MaterialPageRoute(builder: (_) => const PainelLiderancaScreen())),
          ),
          IconButton(icon: const Icon(Icons.logout), tooltip: 'Sair', onPressed: auth.logout),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: () => conta.carregar(),
        child: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            if (conta.erro != null) ErroBanner(mensagem: conta.erro!),
            ...fila.ultimosConflitos.map((msg) => ErroBanner(mensagem: msg)),
            if (fila.ultimosConflitos.isNotEmpty)
              Align(
                alignment: Alignment.centerRight,
                child: TextButton(onPressed: fila.limparConflitos, child: const Text('Ok, entendi')),
              ),
            SaldoCard(carregando: conta.carregando, saldo: conta.saldoExibido, pendentes: conta.pendentes.length),
            const SizedBox(height: 24),
            Wrap(
              spacing: 12,
              runSpacing: 12,
              children: [
                FilledButton.icon(
                  icon: const Icon(Icons.add),
                  label: const Text('Depositar'),
                  onPressed: () =>
                      Navigator.of(context).push(MaterialPageRoute(builder: (_) => const DepositoScreen())),
                ),
                FilledButton.icon(
                  icon: const Icon(Icons.remove),
                  label: const Text('Sacar'),
                  onPressed: () =>
                      Navigator.of(context).push(MaterialPageRoute(builder: (_) => const SaqueScreen())),
                ),
                FilledButton.icon(
                  icon: const Icon(Icons.swap_horiz),
                  label: const Text('Transferir'),
                  onPressed: () =>
                      Navigator.of(context).push(MaterialPageRoute(builder: (_) => const TransferenciaScreen())),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}
