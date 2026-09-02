import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { ApiError, api } from "../api/client";
import ErrorBanner from "../components/ErrorBanner";
import { useAuth } from "../context/AuthContext";

export default function HistoricoPage() {
  const { idConta } = useAuth();
  const [eventos, setEventos] = useState([]);
  const [erro, setErro] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    carregar();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function carregar() {
    setErro(null);
    try {
      const resposta = await api.historico(idConta);
      setEventos(resposta.eventos);
    } catch (e) {
      setErro(e instanceof ApiError ? e.message : "Falha inesperada ao conectar.");
    }
  }

  return (
    <div className="page">
      <h1>Histórico da conta {idConta}</h1>
      <ErrorBanner erro={erro} />
      <table>
        <thead>
          <tr>
            <th>Lamport</th>
            <th>Tipo</th>
            <th>Data/hora</th>
            <th>Detalhes</th>
          </tr>
        </thead>
        <tbody>
          {eventos.map((evento, indice) => (
            <tr key={indice}>
              <td>{evento.timestamp_lamport}</td>
              <td>{evento.tipo}</td>
              <td>{new Date(evento.hora_parede).toLocaleString("pt-BR")}</td>
              <td>{JSON.stringify(evento.detalhes)}</td>
            </tr>
          ))}
          {eventos.length === 0 && !erro && (
            <tr>
              <td colSpan={4}>Nenhum evento encontrado.</td>
            </tr>
          )}
        </tbody>
      </table>
      <button className="secundario" onClick={() => navigate("/conta")}>
        Voltar
      </button>
    </div>
  );
}
