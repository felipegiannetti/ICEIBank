import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { ApiError, api } from "../api/client";
import AgenciaSelector from "../components/AgenciaSelector";
import ErrorBanner from "../components/ErrorBanner";
import { useAuth } from "../context/AuthContext";

export default function LoginPage() {
  const [idConta, setIdConta] = useState("");
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
    <div className="page">
      <h1>ICEIBank</h1>
      <AgenciaSelector />
      <form onSubmit={aoSubmeter}>
        <label>
          Número da conta
          <input
            type="number"
            value={idConta}
            onChange={(e) => setIdConta(e.target.value)}
            required
          />
        </label>
        <label>
          Senha
          <input
            type="password"
            value={senha}
            onChange={(e) => setSenha(e.target.value)}
            required
          />
        </label>
        <button type="submit" disabled={carregando}>
          {carregando ? "Entrando..." : "Entrar"}
        </button>
      </form>
      <ErrorBanner erro={erro} />
    </div>
  );
}
