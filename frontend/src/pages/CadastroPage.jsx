import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { ApiError, api } from "../api/client";
import AgenciaSelector from "../components/AgenciaSelector";
import ErrorBanner from "../components/ErrorBanner";
import { IconBank } from "../components/icons";

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
      <div className="auth-visual">
        <span className="auth-selo">
          <IconBank style={{ width: 18, height: 18 }} />
          ICEIBank
        </span>
        <div className="auth-visual-conteudo">
          <h2>Abra sua conta em segundos.</h2>
          <p>
            Escolha o número da conta e a agência responsável por ela (regra <code>id % 3</code>),
            defina uma senha e comece a usar — depósitos, saques e transferências, tudo protegido por
            autenticação JWT.
          </p>
        </div>
        <p style={{ position: "relative", zIndex: 1, fontSize: "0.78rem", opacity: 0.7 }}>
          Sprint 2 · Mensageria (Pub/Sub) + Relógio Vetorial
        </p>
      </div>

      <div className="auth-form-side">
        <div className="auth-card">
          <div className="brand">
            <div className="brand-mark">IB</div>
            <span className="brand-nome">ICEIBank</span>
          </div>

          <h1>Criar conta</h1>
          <p className="auth-subtitulo">
            O número da conta precisa pertencer à agência selecionada abaixo.
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
              <div className="campo-com-icone">
                <span style={{ position: "absolute", left: 14, color: "var(--texto-fraco)", fontWeight: 700 }}>
                  R$
                </span>
                <input
                  type="number"
                  step="0.01"
                  min="0"
                  value={saldoInicial}
                  onChange={(e) => setSaldoInicial(e.target.value)}
                  placeholder="0,00"
                  style={{ paddingLeft: 40 }}
                />
              </div>
            </label>
            <button type="submit" disabled={carregando}>
              {carregando && <span className="spinner" />}
              {carregando ? "Criando..." : "Criar conta"}
            </button>
          </form>

          <ErrorBanner erro={erro} />

          <p className="auth-rodape">
            Já tem conta? <Link to="/login">Entrar</Link>
          </p>
        </div>
      </div>
    </div>
  );
}
