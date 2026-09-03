import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { ApiError, api, getAgenciaUrl } from "../api/client";
import AppShell from "../components/AppShell";
import ErrorBanner from "../components/ErrorBanner";
import { IconBank, IconGauge, IconLogout } from "../components/icons";
import { useAuth } from "../context/AuthContext";

export default function PerfilPage() {
  const { idConta, logout } = useAuth();
  const [conta, setConta] = useState(null);
  const [limite, setLimite] = useState(null);
  const [erro, setErro] = useState(null);

  useEffect(() => {
    carregar();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function carregar() {
    setErro(null);
    try {
      const [respostaConta, respostaLimite] = await Promise.all([
        api.consultarSaldo(idConta),
        api.consultarLimite(idConta),
      ]);
      setConta(respostaConta);
      setLimite(respostaLimite);
    } catch (e) {
      setErro(e instanceof ApiError ? e.message : "Falha inesperada ao conectar.");
    }
  }

  const inicial = conta?.nome_aluno ? conta.nome_aluno.charAt(0).toUpperCase() : String(idConta);

  return (
    <AppShell titulo="Perfil" subtitulo="Seus dados de identificação nesta agência.">
      <div className="card entrada" style={{ textAlign: "center", paddingTop: 36, paddingBottom: 32 }}>
        <div
          className="avatar"
          style={{ width: 76, height: 76, fontSize: "1.8rem", margin: "0 auto 16px" }}
        >
          {inicial}
        </div>
        {conta && <h2 style={{ fontSize: "1.3rem" }}>{conta.nome_aluno}</h2>}
        <p style={{ color: "var(--texto-suave)", marginTop: 4, fontSize: "0.9rem" }}>
          Conta nº {idConta}
        </p>
      </div>

      <ErrorBanner erro={erro} />

      <div className="card entrada entrada-atraso-1">
        <div className="stack">
          <div className="linha-limite">
            <span className="rotulo">Nome</span>
            <span className="valor">{conta?.nome_aluno ?? "—"}</span>
          </div>
          <div className="linha-limite">
            <span className="rotulo">Número da conta</span>
            <span className="valor">{idConta}</span>
          </div>
          <div className="linha-limite">
            <span className="rotulo">Agência (porta de entrada)</span>
            <span className="valor">{getAgenciaUrl()}</span>
          </div>
          <div className="linha-limite">
            <span className="rotulo">Saldo atual</span>
            <span className="valor">{conta ? `R$ ${conta.saldo.toFixed(2)}` : "—"}</span>
          </div>
          <div className="linha-limite">
            <span className="rotulo">Limite diário</span>
            <span className="valor">{limite ? `R$ ${limite.limite_diario.toFixed(2)}` : "—"}</span>
          </div>
        </div>
      </div>

      <div className="acoes-grid entrada entrada-atraso-2" style={{ gridTemplateColumns: "repeat(3, 1fr)" }}>
        <Link to="/limite" className="acao-item">
          <span className="acao-icone">
            <IconGauge />
          </span>
          <span>Ajustar limite</span>
        </Link>
        <Link to="/historico" className="acao-item">
          <span className="acao-icone">
            <IconBank />
          </span>
          <span>Ver extrato</span>
        </Link>
        <button
          type="button"
          onClick={logout}
          className="acao-item"
          style={{ background: "none", border: "none", padding: 0, boxShadow: "none", cursor: "pointer" }}
        >
          <span className="acao-icone">
            <IconLogout />
          </span>
          <span>Sair</span>
        </button>
      </div>
    </AppShell>
  );
}
