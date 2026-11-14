class AgenciaConfig {
  final int id;
  final String url;

  const AgenciaConfig({required this.id, required this.url});
}

/// Espelha agencia/app/config.py (AGENCIAS) - mesmo OFFSET (0) e mesmas 3
/// portas das 3 agencias.
///
/// IMPORTANTE (emulador x dispositivo):
/// - Emulador Android: "localhost" do PC e "10.0.2.2" dentro do emulador -
///   por isso o default abaixo usa 10.0.2.2.
/// - Simulador iOS: "localhost" funciona direto (troque para 127.0.0.1).
/// - Dispositivo físico (USB ou mesma rede Wi-Fi): troque pelo IP da sua
///   máquina na rede local (ex. "http://192.168.0.10:4000").
/// Se voce mudar o OFFSET em agencia/app/config.py, atualize as portas aqui.
const List<AgenciaConfig> agencias = [
  AgenciaConfig(id: 0, url: 'http://10.0.2.2:4000'),
  AgenciaConfig(id: 1, url: 'http://10.0.2.2:4001'),
  AgenciaConfig(id: 2, url: 'http://10.0.2.2:4002'),
];
