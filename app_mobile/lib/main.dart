import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import 'providers/auth_provider.dart';
import 'providers/conta_provider.dart';
import 'providers/lider_provider.dart';
import 'screens/home_screen.dart';
import 'screens/login_screen.dart';
import 'services/storage_service.dart';

void main() {
  runApp(const IceiBankApp());
}

class IceiBankApp extends StatelessWidget {
  const IceiBankApp({super.key});

  @override
  Widget build(BuildContext context) {
    final storage = StorageService();

    return MultiProvider(
      providers: [
        ChangeNotifierProvider(create: (_) => AuthProvider(storage)),
        ChangeNotifierProxyProvider<AuthProvider, ContaProvider>(
          create: (context) => ContaProvider(context.read<AuthProvider>()),
          update: (context, auth, contaProvider) {
            contaProvider!.atualizarCliente();
            return contaProvider;
          },
        ),
        ChangeNotifierProvider(create: (_) => LiderProvider()..iniciar()),
      ],
      child: MaterialApp(
        title: 'ICEIBank',
        debugShowCheckedModeBanner: false,
        theme: ThemeData(colorSchemeSeed: Colors.indigo, useMaterial3: true),
        home: const _Raiz(),
      ),
    );
  }
}

class _Raiz extends StatelessWidget {
  const _Raiz();

  @override
  Widget build(BuildContext context) {
    final auth = context.watch<AuthProvider>();
    return auth.autenticado ? const HomeScreen() : const LoginScreen();
  }
}
