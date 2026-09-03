import { useEffect, useState } from "react";
import { ApiError, api } from "../api/client";
import AppShell from "../components/AppShell";
import ErrorBanner from "../components/ErrorBanner";
import { useAuth } from "../context/AuthContext";

export default function HistoricoPage() {
  const { idConta } = useAuth();
  const [eventos, setEventos] = useState([]);
  const [erro, setErro] = useState(null);

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
    <AppShell>
      <div className="page-header">
        <h1>Histórico</h1>
        <p>Eventos registrados para a conta {idConta}, mais recentes primeiro.</p>
      </div>

      <ErrorBanner erro={erro} />

      <div className="card" style={{ padding: 0, overflow: "hidden" }}>
        <div className="tabela-wrap" style={{ border: "none", borderRadius: 0 }}>
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
                  <td>
                    <span className="tag-evento">{evento.tipo}</span>
                  </td>
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
        </div>
      </div>
    </AppShell>
  );
}
