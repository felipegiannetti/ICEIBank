import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { ApiError, api } from "../api/client";
import AppShell from "../components/AppShell";
import ErrorBanner from "../components/ErrorBanner";
import { useAuth } from "../context/AuthContext";

const ACOES = [
  { to: "/depositar", label: "Depositar", icone: "↓" },
  { to: "/sacar", label: "Sacar", icone: "↑" },
  { to: "/transferir", label: "Transferir", icone: "⇄" },
  { to: "/historico", label: "Histórico", icone: "≡" },
  { to: "/limite", label: "Limite diário", icone: "◔" },
];

export default function ContaPage() {
  const { idConta } = useAuth();
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
    <AppShell>
      <div className="page-header">
        <h1>Minha conta</h1>
        <p>Visão geral do seu saldo e ações rápidas.</p>
      </div>

      {conta && (
        <div className="saldo-card">
          <p className="rotulo">Saldo disponível</p>
          <p className="saldo">R$ {conta.saldo.toFixed(2)}</p>
          <p className="conta-info">
            Conta {conta.id} — {conta.nome_aluno}
          </p>
        </div>
      )}

      <ErrorBanner erro={erro} />

      <div className="menu-grid">
        {ACOES.map((acao) => (
          <Link key={acao.to} to={acao.to} className="menu-item">
            <span className="icone">{acao.icone}</span>
            {acao.label}
          </Link>
        ))}
      </div>
    </AppShell>
  );
}
