import { useState } from "react";
import { ApiError, api } from "../api/client";
import AppShell from "../components/AppShell";
import ErrorBanner from "../components/ErrorBanner";
import { useAuth } from "../context/AuthContext";

export default function TransferenciaPage() {
  const { idConta } = useAuth();
  const [idDestino, setIdDestino] = useState("");
  const [valor, setValor] = useState("");
  const [resultado, setResultado] = useState(null);
  const [erro, setErro] = useState(null);
  const [carregando, setCarregando] = useState(false);

  async function aoSubmeter(evento) {
    evento.preventDefault();
    setErro(null);
    setResultado(null);
    setCarregando(true);
    try {
      // O backend decide sozinho se e uma transferencia local ou entre
      // agencias (particionamento por id_conta % 3) - o frontend nao
      // precisa saber a diferenca, so exibe o resultado.
      const resposta = await api.transferir(idConta, parseInt(idDestino, 10), parseFloat(valor));
      setResultado(resposta.mensagem);
      setValor("");
      setIdDestino("");
    } catch (e) {
      setErro(e instanceof ApiError ? e.message : "Falha inesperada ao conectar.");
    } finally {
      setCarregando(false);
    }
  }

  return (
    <AppShell titulo="Transferir" subtitulo={`Origem: conta ${idConta} (a sua)`}>
      <div className="card entrada">
        <form onSubmit={aoSubmeter}>
          <label>
            Conta de destino
            <input
              type="number"
              value={idDestino}
              onChange={(e) => setIdDestino(e.target.value)}
              placeholder="Número da conta"
              required
            />
          </label>
          <label>
            Valor
            <div className="campo-com-icone">
              <span style={{ position: "absolute", left: 14, color: "var(--texto-fraco)", fontWeight: 700 }}>
                R$
              </span>
              <input
                type="number"
                step="0.01"
                min="0.01"
                value={valor}
                onChange={(e) => setValor(e.target.value)}
                placeholder="0,00"
                style={{ paddingLeft: 40 }}
                required
              />
            </div>
          </label>
          <button type="submit" disabled={carregando}>
            {carregando && <span className="spinner" />}
            {carregando ? "Transferindo..." : "Transferir"}
          </button>
        </form>

        {resultado && <p className="sucesso" style={{ marginTop: 16 }}>{resultado}</p>}
        {erro && <div style={{ marginTop: 16 }}><ErrorBanner erro={erro} /></div>}
      </div>
    </AppShell>
  );
}
