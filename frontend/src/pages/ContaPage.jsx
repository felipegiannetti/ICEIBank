import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { ApiError, api } from "../api/client";
import AppShell from "../components/AppShell";
import ErrorBanner from "../components/ErrorBanner";
import { IconArrowDown, IconArrowUp, IconEye, IconEyeOff, IconGauge, IconList, IconSwap } from "../components/icons";
import { useAuth } from "../context/AuthContext";

const ACOES = [
  { to: "/depositar", label: "Depositar", Icone: IconArrowDown },
  { to: "/sacar", label: "Sacar", Icone: IconArrowUp },
  { to: "/transferir", label: "Transferir", Icone: IconSwap },
  { to: "/historico", label: "Extrato", Icone: IconList },
  { to: "/limite", label: "Limite", Icone: IconGauge },
];

export default function ContaPage() {
  const { idConta } = useAuth();
  const [conta, setConta] = useState(null);
  const [erro, setErro] = useState(null);
  const [visivel, setVisivel] = useState(true);

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
    <AppShell titulo="Minha conta" subtitulo="Visão geral do seu saldo e ações rápidas.">
      {conta && (
        <div className="saldo-card entrada">
          <div className="saldo-topo">
            <p className="rotulo">Saldo disponível</p>
            <button
              type="button"
              className="toggle-visibilidade"
              onClick={() => setVisivel((v) => !v)}
              title={visivel ? "Ocultar saldo" : "Mostrar saldo"}
              aria-label={visivel ? "Ocultar saldo" : "Mostrar saldo"}
            >
              {visivel ? <IconEye /> : <IconEyeOff />}
            </button>
          </div>
          <p className="saldo">{visivel ? `R$ ${conta.saldo.toFixed(2)}` : "R$ ••••••"}</p>
          <p className="conta-info">
            Conta {conta.id} — {conta.nome_aluno}
          </p>
        </div>
      )}

      <ErrorBanner erro={erro} />

      <div className="acoes-grid entrada entrada-atraso-1">
        {ACOES.map(({ to, label, Icone }) => (
          <Link key={to} to={to} className="acao-item">
            <span className="acao-icone">
              <Icone />
            </span>
            <span>{label}</span>
          </Link>
        ))}
      </div>
    </AppShell>
  );
}
