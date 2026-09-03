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
  const [carregando, setCarregando] = useState(false);

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
    setCarregando(true);
    try {
      const resposta = await api.atualizarLimite(idConta, parseFloat(novoLimite));
      setLimite(resposta);
      setSucesso("Limite atualizado com sucesso.");
      setNovoLimite("");
    } catch (e) {
      setErro(e instanceof ApiError ? e.message : "Falha inesperada ao conectar.");
    } finally {
      setCarregando(false);
    }
  }

  const percentualUsado = limite ? Math.min(100, (limite.uso_diario_atual / limite.limite_diario) * 100) : 0;
  const emAlerta = percentualUsado >= 80;

  return (
    <AppShell titulo="Limite diário" subtitulo={`Quanto a conta ${idConta} pode sacar/transferir hoje.`}>
      {limite && (
        <div className="card entrada">
          <div className="limite-resumo">
            <span className="valor-grande">R$ {limite.restante_hoje.toFixed(2)}</span>
            <span className="valor-total">restante de R$ {limite.limite_diario.toFixed(2)}</span>
          </div>
          <div className="barra-progresso">
            <div
              className={`barra-progresso-preenchimento ${emAlerta ? "alerta" : ""}`}
              style={{ width: `${percentualUsado}%` }}
            />
          </div>
          <div className="stack" style={{ marginTop: 18 }}>
            <div className="linha-limite">
              <span className="rotulo">Já usado hoje</span>
              <span className="valor">R$ {limite.uso_diario_atual.toFixed(2)}</span>
            </div>
            <div className="linha-limite">
              <span className="rotulo">Limite diário configurado</span>
              <span className="valor">R$ {limite.limite_diario.toFixed(2)}</span>
            </div>
          </div>
        </div>
      )}

      <div className="card entrada entrada-atraso-1">
        <form onSubmit={aoSubmeter}>
          <label>
            Novo limite diário
            <div className="campo-com-icone">
              <span style={{ position: "absolute", left: 14, color: "var(--texto-fraco)", fontWeight: 700 }}>
                R$
              </span>
              <input
                type="number"
                step="0.01"
                min="0.01"
                value={novoLimite}
                onChange={(e) => setNovoLimite(e.target.value)}
                placeholder="0,00"
                style={{ paddingLeft: 40 }}
                required
              />
            </div>
          </label>
          <button type="submit" disabled={carregando}>
            {carregando && <span className="spinner" />}
            {carregando ? "Atualizando..." : "Atualizar limite"}
          </button>
        </form>

        {sucesso && <p className="sucesso" style={{ marginTop: 16 }}>{sucesso}</p>}
        {erro && <div style={{ marginTop: 16 }}><ErrorBanner erro={erro} /></div>}
      </div>
    </AppShell>
  );
}
