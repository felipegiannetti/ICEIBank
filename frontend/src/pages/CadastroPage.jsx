import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { ApiError, api } from "../api/client";
import AgenciaSelector from "../components/AgenciaSelector";
import ErrorBanner from "../components/ErrorBanner";

export default function CadastroPage() {
  const [id, setId] = useState("");
  const [nomeAluno, setNomeAluno] = useState("");
  const [senha, setSenha] = useState("");
  const [saldoInicial, setSaldoInicial] = useState("");
  const [erro, setErro] = useState(null);
  const [carregando, setCarregando] = useState(false);
  const navigate = useNavigate();

  async function aoSubmeter(evento) {
    evento.preventDefault();
    setErro(null);
    setCarregando(true);
    try {
      const idNumerico = parseInt(id, 10);
      await api.criarConta(idNumerico, nomeAluno, senha, saldoInicial ? parseFloat(saldoInicial) : 0);
      navigate("/login", { state: { contaCriada: true, idConta: idNumerico } });
    } catch (e) {
      setErro(e instanceof ApiError ? e.message : "Falha inesperada ao conectar.");
    } finally {
      setCarregando(false);
    }
  }

  return (
    <div className="auth-shell">
      <div className="auth-card">
        <div className="brand">
          <div className="brand-mark">IB</div>
          <span className="brand-nome">ICEIBank</span>
        </div>

        <h1>Criar conta</h1>
        <p className="auth-subtitulo">
          Escolha a agência de acordo com o número da conta (o número precisa pertencer à agência
          selecionada — regra <code>id % 3</code>).
        </p>

        <AgenciaSelector />

        <form onSubmit={aoSubmeter}>
          <label>
            Número da conta
            <input
              type="number"
              value={id}
              onChange={(e) => setId(e.target.value)}
              placeholder="Ex.: 0"
              required
            />
          </label>
          <label>
            Nome
            <input
              type="text"
              value={nomeAluno}
              onChange={(e) => setNomeAluno(e.target.value)}
              placeholder="Seu nome"
              required
            />
          </label>
          <label>
            Senha
            <input
              type="password"
              value={senha}
              onChange={(e) => setSenha(e.target.value)}
              placeholder="Mínimo de 4 caracteres"
              minLength={4}
              required
            />
          </label>
          <label>
            Depósito inicial (opcional)
            <input
              type="number"
              step="0.01"
              min="0"
              value={saldoInicial}
              onChange={(e) => setSaldoInicial(e.target.value)}
              placeholder="0.00"
            />
          </label>
          <button type="submit" disabled={carregando}>
            {carregando ? "Criando..." : "Criar conta"}
          </button>
        </form>

        <ErrorBanner erro={erro} />

        <p className="auth-rodape">
          Já tem conta? <Link to="/login">Entrar</Link>
        </p>
      </div>
    </div>
  );
}
