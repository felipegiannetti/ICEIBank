import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { ApiError, api } from "../api/client";
import ErrorBanner from "../components/ErrorBanner";
import { useAuth } from "../context/AuthContext";

export default function SaquePage() {
  const { idConta } = useAuth();
  const [valor, setValor] = useState("");
  const [resultado, setResultado] = useState(null);
  const [erro, setErro] = useState(null);
  const navigate = useNavigate();

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
    <div className="page">
      <h1>Sacar</h1>
      <p>Conta {idConta}</p>
      <form onSubmit={aoSubmeter}>
        <label>
          Valor
          <input
            type="number"
            step="0.01"
            min="0.01"
            value={valor}
            onChange={(e) => setValor(e.target.value)}
            required
          />
        </label>
        <button type="submit">Sacar</button>
      </form>
      {resultado && <p className="sucesso">{resultado}</p>}
      <ErrorBanner erro={erro} />
      <button className="secundario" onClick={() => navigate("/conta")}>
        Voltar
      </button>
    </div>
  );
}
