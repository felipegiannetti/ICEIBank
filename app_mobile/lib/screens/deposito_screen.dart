import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../providers/conta_provider.dart';

class DepositoScreen extends StatefulWidget {
  const DepositoScreen({super.key});

  @override
  State<DepositoScreen> createState() => _DepositoScreenState();
}

class _DepositoScreenState extends State<DepositoScreen> {
  final _formKey = GlobalKey<FormState>();
  final _valorController = TextEditingController();
  bool _enviando = false;
  String? _erro;
  bool _ficouPendente = false;

  @override
  void dispose() {
    _valorController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Depositar')),
      body: Padding(
        padding: const EdgeInsets.all(24),
        child: Form(
          key: _formKey,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              TextFormField(
                controller: _valorController,
                decoration: const InputDecoration(labelText: 'Valor (R\$)'),
                keyboardType: const TextInputType.numberWithOptions(decimal: true),
                validator: (v) {
                  final valor = double.tryParse(v ?? '');
                  if (valor == null || valor <= 0) return 'Informe um valor válido';
                  return null;
                },
              ),
              const SizedBox(height: 24),
              if (_erro != null) Text(_erro!, style: TextStyle(color: Theme.of(context).colorScheme.error)),
              if (_ficouPendente)
                const Text('Sem conexão agora - o depósito foi guardado e será sincronizado automaticamente.'),
              const SizedBox(height: 12),
              FilledButton(
                onPressed: _enviando ? null : _confirmar,
                child: _enviando
                    ? const SizedBox(height: 20, width: 20, child: CircularProgressIndicator(strokeWidth: 2))
                    : const Text('Confirmar depósito'),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Future<void> _confirmar() async {
    if (!_formKey.currentState!.validate()) return;
    setState(() {
      _enviando = true;
      _erro = null;
      _ficouPendente = false;
    });
    final conta = context.read<ContaProvider>();
    final valor = double.parse(_valorController.text);
    final pendentesAntes = conta.pendentes.length;
    final erro = await conta.depositar(valor);
    if (!mounted) return;
    if (erro != null) {
      setState(() {
        _erro = erro;
        _enviando = false;
      });
      return;
    }
    if (conta.pendentes.length > pendentesAntes) {
      setState(() {
        _ficouPendente = true;
        _enviando = false;
      });
      return;
    }
    Navigator.of(context).pop();
  }
}
