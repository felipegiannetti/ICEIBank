import { NavLink } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import {
  IconArrowDown,
  IconArrowUp,
  IconGauge,
  IconHome,
  IconList,
  IconLogout,
  IconSwap,
} from "./icons";

const LINKS = [
  { to: "/conta", label: "Início", Icone: IconHome },
  { to: "/depositar", label: "Depositar", Icone: IconArrowDown },
  { to: "/sacar", label: "Sacar", Icone: IconArrowUp },
  { to: "/transferir", label: "Transferir", Icone: IconSwap },
  { to: "/historico", label: "Extrato", Icone: IconList },
  { to: "/limite", label: "Limite", Icone: IconGauge },
];

function saudacaoDoDia() {
  const hora = new Date().getHours();
  if (hora < 12) return "Bom dia";
  if (hora < 18) return "Boa tarde";
  return "Boa noite";
}

export default function AppShell({ children, titulo, subtitulo }) {
  const { idConta, logout } = useAuth();

  return (
    <div className="app-shell">
      <aside className="app-sidebar">
        <div className="sidebar-brand">
          <div className="brand-mark">IB</div>
          <span className="brand-nome">ICEIBank</span>
        </div>

        <nav className="sidebar-nav">
          {LINKS.map(({ to, label, Icone }) => (
            <NavLink key={to} to={to} className={({ isActive }) => (isActive ? "sidebar-link ativo" : "sidebar-link")}>
              <Icone />
              <span>{label}</span>
            </NavLink>
          ))}
        </nav>

        <div className="sidebar-rodape">
          <NavLink to="/perfil" className="sidebar-perfil-link" title="Ver perfil">
            <div className="avatar">{String(idConta ?? "?")}</div>
            <div className="sidebar-usuario">
              <div className="conta-label">Conta</div>
              <div className="conta-numero">Nº {idConta}</div>
            </div>
          </NavLink>
          <button type="button" className="btn-icone" onClick={logout} title="Sair" aria-label="Sair">
            <IconLogout />
          </button>
        </div>
      </aside>

      <div className="app-main">
        <div className="app-topbar entrada">
          <p className="saudacao">
            {saudacaoDoDia()}, <strong>conta {idConta}</strong>
          </p>
        </div>

        <main className="app-content">
          <div className="content-inner">
            {(titulo || subtitulo) && (
              <div className="page-header entrada">
                {titulo && <h1>{titulo}</h1>}
                {subtitulo && <p>{subtitulo}</p>}
              </div>
            )}
            {children}
          </div>
        </main>
      </div>
    </div>
  );
}
