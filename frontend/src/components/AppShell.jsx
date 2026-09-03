import { NavLink } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

const LINKS = [
  { to: "/conta", label: "Saldo" },
  { to: "/depositar", label: "Depositar" },
  { to: "/sacar", label: "Sacar" },
  { to: "/transferir", label: "Transferir" },
  { to: "/historico", label: "Histórico" },
  { to: "/limite", label: "Limite" },
];

export default function AppShell({ children }) {
  const { idConta, logout } = useAuth();

  return (
    <div className="app-shell">
      <header className="app-navbar">
        <div className="brand">
          <div className="brand-mark">IB</div>
          <span className="brand-nome">ICEIBank</span>
        </div>

        <nav className="nav-links">
          {LINKS.map((link) => (
            <NavLink
              key={link.to}
              to={link.to}
              className={({ isActive }) => (isActive ? "ativo" : "")}
            >
              {link.label}
            </NavLink>
          ))}
        </nav>

        <div className="navbar-usuario">
          <span className="pill-conta">Conta {idConta}</span>
          <button type="button" className="link-sair" onClick={logout}>
            Sair
          </button>
        </div>
      </header>

      <main className="app-content">
        <div className="content-inner">{children}</div>
      </main>
    </div>
  );
}
