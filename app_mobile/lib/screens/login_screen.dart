import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../config/agencias.dart';
import '../providers/auth_provider.dart';
import '../services/api_exception.dart';

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final _formKey = GlobalKey<FormState>();
  final _idContaController = TextEditingController();
  final _senhaController = TextEditingController();
  bool _carregando = false;
  String? _erro;

  @override
  void dispose() {
    _idContaController.dispose();
    _senhaController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final auth = context.watch<AuthProvider>();

    return Scaffold(
      appBar: AppBar(title: const Text('ICEIBank')),
      body: Padding(
        padding: const EdgeInsets.all(24),
        child: Form(
          key: _formKey,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              DropdownButtonFormField<String>(
                initialValue: auth.agenciaUrl,
                decoration: const InputDecoration(labelText: 'Agência'),
                items: agencias
                    .map((a) => DropdownMenuItem(value: a.url, child: Text('Agência ${a.id} (${a.url})')))
                    .toList(),
                onChanged: (url) {
                  if (url != null) auth.trocarAgencia(url);
                },
              ),
              const SizedBox(height: 16),
              TextFormField(
                controller: _idContaController,
                decoration: const InputDecoration(labelText: 'Número da conta'),
                keyboardType: TextInputType.number,
                validator: (v) => (v == null || v.isEmpty) ? 'Informe o número da conta' : null,
              ),
              const SizedBox(height: 12),
              TextFormField(
                controller: _senhaController,
                decoration: const InputDecoration(labelText: 'Senha'),
                obscureText: true,
                validator: (v) => (v == null || v.isEmpty) ? 'Informe a senha' : null,
              ),
              const SizedBox(height: 24),
              if (_erro != null) ...[
                Text(_erro!, style: TextStyle(color: Theme.of(context).colorScheme.error)),
                const SizedBox(height: 12),
              ],
              FilledButton(
                onPressed: _carregando ? null : _entrar,
                child: _carregando
                    ? const SizedBox(height: 20, width: 20, child: CircularProgressIndicator(strokeWidth: 2))
                    : const Text('Entrar'),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Future<void> _entrar() async {
    if (!_formKey.currentState!.validate()) return;
    setState(() {
      _carregando = true;
      _erro = null;
    });
    try {
      final auth = context.read<AuthProvider>();
      await auth.login(int.parse(_idContaController.text), _senhaController.text);
    } on ApiException catch (erro) {
      setState(() => _erro = erro.mensagem);
    } finally {
      if (mounted) setState(() => _carregando = false);
    }
  }
}
