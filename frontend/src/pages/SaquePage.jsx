import { useState } from "react";
import { ApiError, api } from "../api/client";
import AppShell from "../components/AppShell";
import ErrorBanner from "../components/ErrorBanner";
import { useAuth } from "../context/AuthContext";

export default function SaquePage() {
  const { idConta } = useAuth();
  const [valor, setValor] = useState("");
  const [resultado, setResultado] = useState(null);
  const [erro, setErro] = useState(null);

  async function aoSubmeter(evento) {
    evento.preventDefault();
    setErro(null);
    setResultado(null);
    try {
      const conta = await api.sacar(idConta, parseFloat(valor));
      setResultado(`Saque concluído. Novo saldo: R$ ${conta.saldo.toFixed(2)}`);
      setValor("");
    } catch (e) {
      setErro(e instanceof ApiError ? e.message : "Falha inesperada ao conectar.");
    }
  }

  return (
    <AppShell>
      <div className="page-header">
        <h1>Sacar</h1>
        <p>Conta {idConta}</p>
      </div>

      <div className="card">
        <form onSubmit={aoSubmeter}>
          <label>
            Valor
            <input
              type="number"
              step="0.01"
              min="0.01"
              value={valor}
              onChange={(e) => setValor(e.target.value)}
              placeholder="0.00"
              required
            />
          </label>
          <button type="submit">Sacar</button>
        </form>

        {resultado && <p className="sucesso" style={{ marginTop: 16 }}>{resultado}</p>}
        {erro && <div style={{ marginTop: 16 }}><ErrorBanner erro={erro} /></div>}
      </div>
    </AppShell>
  );
}
