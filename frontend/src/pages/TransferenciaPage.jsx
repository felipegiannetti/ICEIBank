import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { ApiError, api } from "../api/client";
import ErrorBanner from "../components/ErrorBanner";
import { useAuth } from "../context/AuthContext";

export default function TransferenciaPage() {
  const { idConta } = useAuth();
  const [idDestino, setIdDestino] = useState("");
  const [valor, setValor] = useState("");
  const [resultado, setResultado] = useState(null);
  const [erro, setErro] = useState(null);
  const navigate = useNavigate();

  async function aoSubmeter(evento) {
    evento.preventDefault();
    setErro(null);
    setResultado(null);
    try {
      // O backend decide sozinho se e uma transferencia local ou entre
      // agencias (particionamento por id_conta % 3) - o frontend nao
      // precisa saber a diferenca, so exibe o resultado.
      const resposta = await api.transferir(idConta, parseInt(idDestino, 10), parseFloat(valor));
      setResultado(resposta.mensagem);
      setValor("");
      setIdDestino("");
    } catch (e) {
      setErro(e instanceof ApiError ? e.message : "Falha inesperada ao conectar.");
    }
  }

  return (
    <div className="page">
      <h1>Transferir</h1>
      <p>Origem: conta {idConta} (a sua)</p>
      <form onSubmit={aoSubmeter}>
        <label>
          Conta de destino
          <input
            type="number"
            value={idDestino}
            onChange={(e) => setIdDestino(e.target.value)}
            required
          />
        </label>
        <label>
          Valor
          <input
            type="number"
            step="0.01"
            min="0.01"
            value={valor}
            onChange={(e) => setValor(e.target.value)}
            required
          />
        </label>
        <button type="submit">Transferir</button>
      </form>
      {resultado && <p className="sucesso">{resultado}</p>}
      <ErrorBanner erro={erro} />
      <button className="secundario" onClick={() => navigate("/conta")}>
        Voltar
      </button>
    </div>
  );
}
