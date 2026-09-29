import { useRef, useState } from "react";
import { ApiError, api } from "../api/client";
import AppShell from "../components/AppShell";
import ErrorBanner from "../components/ErrorBanner";
import { useAuth } from "../context/AuthContext";

const INTERVALO_POLLING_MS = 1000;
const TENTATIVAS_MAX_POLLING = 15;

const ROTULOS_STATUS = {
  PENDENTE: "Publicada — aguardando confirmação da agência de destino...",
  CONFIRMADA: "Confirmada — o crédito já foi aplicado na conta de destino.",
  FALHOU: "A agência de destino não conseguiu aplicar o crédito (veja o motivo abaixo).",
  CONCLUIDA: "Transferência concluída (mesma agência).",
};

export default function TransferenciaPage() {
  const { idConta } = useAuth();
  const [idDestino, setIdDestino] = useState("");
  const [valor, setValor] = useState("");
  const [status, setStatus] = useState(null);
  const [motivo, setMotivo] = useState(null);
  const [erro, setErro] = useState(null);
  const [carregando, setCarregando] = useState(false);
  const tentativasRef = useRef(0);

  function pararEmBreve() {
    tentativasRef.current = TENTATIVAS_MAX_POLLING;
  }

  async function acompanharStatus(idTransferencia) {
    tentativasRef.current = 0;
    const verificar = async () => {
      tentativasRef.current += 1;
      try {
        const resposta = await api.statusTransferencia(idTransferencia);
        setStatus(resposta.status);
        setMotivo(resposta.motivo);
        if (resposta.status === "PENDENTE" && tentativasRef.current < TENTATIVAS_MAX_POLLING) {
          setTimeout(verificar, INTERVALO_POLLING_MS);
        }
      } catch {
        // Se a consulta de status falhar (ex.: agencia reiniciou), so para
        // de tentar - a mensagem "aguardando confirmação" ja fica visível.
      }
    };
    verificar();
  }

  async function aoSubmeter(evento) {
    evento.preventDefault();
    setErro(null);
    setStatus(null);
    setMotivo(null);
    pararEmBreve();
    setCarregando(true);
    try {
      // O backend decide sozinho se e uma transferencia local ou entre
      // agencias (particionamento por id_conta % 3) - o frontend nao
      // precisa saber a diferenca. Entre agencias, a entrega e assincrona
      // (mensageria) - por isso o acompanhamento de status abaixo.
      const resposta = await api.transferir(idConta, parseInt(idDestino, 10), parseFloat(valor));
      setStatus(resposta.status);
      if (resposta.id_transferencia) {
        acompanharStatus(resposta.id_transferencia);
      }
      setValor("");
      setIdDestino("");
    } catch (e) {
      setErro(e instanceof ApiError ? e.message : "Falha inesperada ao conectar.");
    } finally {
      setCarregando(false);
    }
  }

  return (
    <AppShell titulo="Transferir" subtitulo={`Origem: conta ${idConta} (a sua)`}>
      <div className="card entrada">
        <form onSubmit={aoSubmeter}>
          <label>
            Conta de destino
            <input
              type="number"
              value={idDestino}
              onChange={(e) => setIdDestino(e.target.value)}
              placeholder="Número da conta"
              required
            />
          </label>
          <label>
            Valor
            <div className="campo-com-icone">
              <span style={{ position: "absolute", left: 14, color: "var(--texto-fraco)", fontWeight: 700 }}>
                R$
              </span>
              <input
                type="number"
                step="0.01"
                min="0.01"
                value={valor}
                onChange={(e) => setValor(e.target.value)}
                placeholder="0,00"
                style={{ paddingLeft: 40 }}
                required
              />
            </div>
          </label>
          <button type="submit" disabled={carregando}>
            {carregando && <span className="spinner" />}
            {carregando ? "Transferindo..." : "Transferir"}
          </button>
        </form>

        {status && (
          <p className={status === "FALHOU" ? "error-banner" : "sucesso"} style={{ marginTop: 16 }}>
            {ROTULOS_STATUS[status] || status}
            {motivo && ` (${motivo})`}
          </p>
        )}
        {erro && <div style={{ marginTop: 16 }}><ErrorBanner erro={erro} /></div>}
      </div>
    </AppShell>
  );
}
