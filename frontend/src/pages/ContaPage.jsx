import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { ApiError, api } from "../api/client";
import ErrorBanner from "../components/ErrorBanner";
import { useAuth } from "../context/AuthContext";

export default function ContaPage() {
  const { idConta, logout } = useAuth();
  const [conta, setConta] = useState(null);
  const [erro, setErro] = useState(null);

  useEffect(() => {
    carregarSaldo();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function carregarSaldo() {
    setErro(null);
    try {
      const resposta = await api.consultarSaldo(idConta);
      setConta(resposta);
    } catch (e) {
      setErro(e instanceof ApiError ? e.message : "Falha inesperada ao conectar.");
    }
  }

  return (
    <div className="page">
      <h1>Minha conta</h1>
      {conta && (
        <div className="saldo-card">
          <p>
            Conta {conta.id} — {conta.nome_aluno}
          </p>
          <p className="saldo">Saldo: R$ {conta.saldo.toFixed(2)}</p>
        </div>
      )}
      <ErrorBanner erro={erro} />
      <nav className="menu">
        <Link to="/depositar">Depositar</Link>
        <Link to="/sacar">Sacar</Link>
        <Link to="/transferir">Transferir</Link>
        <Link to="/historico">Histórico</Link>
        <Link to="/limite">Limite diário</Link>
      </nav>
      <button className="secundario" onClick={logout}>
        Sair
      </button>
    </div>
  );
}
