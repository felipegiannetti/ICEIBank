import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { ApiError, api } from "../api/client";
import ErrorBanner from "../components/ErrorBanner";
import { useAuth } from "../context/AuthContext";

export default function LimitePage() {
  const { idConta } = useAuth();
  const [limite, setLimite] = useState(null);
  const [novoLimite, setNovoLimite] = useState("");
  const [erro, setErro] = useState(null);
  const [sucesso, setSucesso] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    carregar();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function carregar() {
    setErro(null);
    try {
      const resposta = await api.consultarLimite(idConta);
      setLimite(resposta);
    } catch (e) {
      setErro(e instanceof ApiError ? e.message : "Falha inesperada ao conectar.");
    }
  }

  async function aoSubmeter(evento) {
    evento.preventDefault();
    setErro(null);
    setSucesso(null);
    try {
      const resposta = await api.atualizarLimite(idConta, parseFloat(novoLimite));
      setLimite(resposta);
      setSucesso("Limite atualizado.");
      setNovoLimite("");
    } catch (e) {
      setErro(e instanceof ApiError ? e.message : "Falha inesperada ao conectar.");
    }
  }

  return (
    <div className="page">
      <h1>Limite diário</h1>
      {limite && (
        <div className="saldo-card">
          <p>Limite diário: R$ {limite.limite_diario.toFixed(2)}</p>
          <p>Já usado hoje: R$ {limite.uso_diario_atual.toFixed(2)}</p>
          <p>Restante hoje: R$ {limite.restante_hoje.toFixed(2)}</p>
        </div>
      )}
      <form onSubmit={aoSubmeter}>
        <label>
          Novo limite diário
          <input
            type="number"
            step="0.01"
            min="0.01"
            value={novoLimite}
            onChange={(e) => setNovoLimite(e.target.value)}
            required
          />
        </label>
        <button type="submit">Atualizar</button>
      </form>
      {sucesso && <p className="sucesso">{sucesso}</p>}
      <ErrorBanner erro={erro} />
      <button className="secundario" onClick={() => navigate("/conta")}>
        Voltar
      </button>
    </div>
  );
}
