import { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { ApiError, api } from "../api/client";
import AgenciaSelector from "../components/AgenciaSelector";
import ErrorBanner from "../components/ErrorBanner";
import { IconBank } from "../components/icons";
import { useAuth } from "../context/AuthContext";

export default function LoginPage() {
  const location = useLocation();
  const [idConta, setIdConta] = useState(
    location.state?.idConta !== undefined ? String(location.state.idConta) : ""
  );
  const [senha, setSenha] = useState("");
  const [erro, setErro] = useState(null);
  const [carregando, setCarregando] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  async function aoSubmeter(evento) {
    evento.preventDefault();
    setErro(null);
    setCarregando(true);
    try {
      const resposta = await api.login(parseInt(idConta, 10), senha);
      login(resposta.access_token, parseInt(idConta, 10));
      navigate("/conta");
    } catch (e) {
      setErro(e instanceof ApiError ? e.message : "Falha inesperada ao conectar.");
    } finally {
      setCarregando(false);
    }
  }

  return (
    <div className="auth-shell">
      <div className="auth-visual">
        <span className="auth-selo">
          <IconBank style={{ width: 18, height: 18 }} />
          ICEIBank
        </span>
        <div className="auth-visual-conteudo">
          <h2>Seu dinheiro, em qualquer agência, sempre sincronizado.</h2>
          <p>
            Contas particionadas entre agências, transferências locais e entre agências, e cada
            operação carimbada com relógio lógico de Lamport para manter a ordem causal do sistema.
          </p>
        </div>
        <p style={{ position: "relative", zIndex: 1, fontSize: "0.78rem", opacity: 0.7 }}>
          Sprint 1 · REST/MVC + Relógio de Lamport
        </p>
      </div>

      <div className="auth-form-side">
        <div className="auth-card">
          <div className="brand">
            <div className="brand-mark">IB</div>
            <span className="brand-nome">ICEIBank</span>
          </div>

          <h1>Bem-vindo de volta</h1>
          <p className="auth-subtitulo">Entre com a sua conta para continuar.</p>

          <AgenciaSelector />

          {location.state?.contaCriada && (
            <p className="sucesso" style={{ marginBottom: 16 }}>
              Conta criada com sucesso! Faça login para continuar.
            </p>
          )}

          <form onSubmit={aoSubmeter}>
            <label>
              Número da conta
              <input
                type="number"
                value={idConta}
                onChange={(e) => setIdConta(e.target.value)}
                placeholder="Ex.: 0"
                required
              />
            </label>
            <label>
              Senha
              <input
                type="password"
                value={senha}
                onChange={(e) => setSenha(e.target.value)}
                placeholder="Sua senha"
                required
              />
            </label>
            <button type="submit" disabled={carregando}>
              {carregando && <span className="spinner" />}
              {carregando ? "Entrando..." : "Entrar"}
            </button>
          </form>

          <ErrorBanner erro={erro} />

          <p className="auth-rodape">
            Ainda não tem conta? <Link to="/cadastro">Criar conta</Link>
          </p>
        </div>
      </div>
    </div>
  );
}
