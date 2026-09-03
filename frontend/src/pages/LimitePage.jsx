import { useEffect, useState } from "react";
import { ApiError, api } from "../api/client";
import AppShell from "../components/AppShell";
import ErrorBanner from "../components/ErrorBanner";
import { useAuth } from "../context/AuthContext";

export default function LimitePage() {
  const { idConta } = useAuth();
  const [limite, setLimite] = useState(null);
  const [novoLimite, setNovoLimite] = useState("");
  const [erro, setErro] = useState(null);
  const [sucesso, setSucesso] = useState(null);

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
    <AppShell>
      <div className="page-header">
        <h1>Limite diário</h1>
        <p>Quanto a conta {idConta} pode sacar/transferir por dia.</p>
      </div>

      {limite && (
        <div className="card">
          <div className="stack">
            <div className="linha-limite">
              <span className="rotulo">Limite diário</span>
              <span className="valor">R$ {limite.limite_diario.toFixed(2)}</span>
            </div>
            <div className="linha-limite">
              <span className="rotulo">Já usado hoje</span>
              <span className="valor">R$ {limite.uso_diario_atual.toFixed(2)}</span>
            </div>
            <div className="linha-limite">
              <span className="rotulo">Restante hoje</span>
              <span className="valor">R$ {limite.restante_hoje.toFixed(2)}</span>
            </div>
          </div>
        </div>
      )}

      <div className="card">
        <form onSubmit={aoSubmeter}>
          <label>
            Novo limite diário
            <input
              type="number"
              step="0.01"
              min="0.01"
              value={novoLimite}
              onChange={(e) => setNovoLimite(e.target.value)}
              placeholder="0.00"
              required
            />
          </label>
          <button type="submit">Atualizar</button>
        </form>

        {sucesso && <p className="sucesso" style={{ marginTop: 16 }}>{sucesso}</p>}
        {erro && <div style={{ marginTop: 16 }}><ErrorBanner erro={erro} /></div>}
      </div>
    </AppShell>
  );
}
