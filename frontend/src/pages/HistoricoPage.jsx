import { useEffect, useState } from "react";
import { ApiError, api } from "../api/client";
import AppShell from "../components/AppShell";
import ErrorBanner from "../components/ErrorBanner";
import { IconArrowDown, IconArrowUp, IconBank, IconGauge, IconSwap } from "../components/icons";
import { useAuth } from "../context/AuthContext";

function descreverEvento(evento, idConta) {
  const d = evento.detalhes || {};
  switch (evento.tipo) {
    case "CRIAR_CONTA":
      return { Icone: IconBank, classe: "", titulo: "Conta criada", meta: "Depósito inicial", sinal: 1, valor: d.saldo_inicial };
    case "DEPOSITO":
      return { Icone: IconArrowDown, classe: "credito", titulo: "Depósito", meta: "Dinheiro recebido", sinal: 1, valor: d.valor };
    case "SAQUE":
      return { Icone: IconArrowUp, classe: "debito", titulo: "Saque", meta: "Dinheiro sacado", sinal: -1, valor: d.valor };
    case "TRANSFERENCIA_DEBITO":
      return { Icone: IconSwap, classe: "debito", titulo: "Transferência enviada", meta: `Para conta ${d.id_destino}`, sinal: -1, valor: d.valor };
    case "TRANSFERENCIA_CREDITO":
      return { Icone: IconSwap, classe: "credito", titulo: "Transferência recebida", meta: `De conta ${d.id_origem}`, sinal: 1, valor: d.valor };
    case "TRANSFERENCIA_CREDITO_REMOTO":
      return { Icone: IconSwap, classe: "credito", titulo: "Transferência recebida", meta: `De outra agência (nº ${d.origem_agencia})`, sinal: 1, valor: d.valor };
    case "TRANSFERENCIA_FALHOU":
      return { Icone: IconSwap, classe: "debito", titulo: "Transferência falhou", meta: "Agência de destino indisponível", sinal: null, valor: d.valor };
    case "SAQUE_REJEITADO_LIMITE":
    case "TRANSFERENCIA_REJEITADA_LIMITE":
      return { Icone: IconGauge, classe: "", titulo: "Operação rejeitada", meta: "Limite diário excedido", sinal: null, valor: d.valor };
    case "LIMITE_ATUALIZADO":
      return { Icone: IconGauge, classe: "", titulo: "Limite atualizado", meta: `Novo limite: R$ ${Number(d.novo_limite).toFixed(2)}`, sinal: null, valor: null };
    default:
      return { Icone: IconBank, classe: "", titulo: evento.tipo, meta: JSON.stringify(d), sinal: null, valor: null };
  }
}

export default function HistoricoPage() {
  const { idConta } = useAuth();
  const [eventos, setEventos] = useState([]);
  const [erro, setErro] = useState(null);
  const [carregado, setCarregado] = useState(false);

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
    } finally {
      setCarregado(true);
    }
  }

  return (
    <AppShell titulo="Extrato" subtitulo="Seus eventos mais recentes, do mais novo para o mais antigo.">
      <ErrorBanner erro={erro} />

      <div className="card entrada" style={{ padding: "8px 24px" }}>
        <div className="extrato-lista">
          {eventos.map((evento, indice) => {
            const info = descreverEvento(evento, idConta);
            const { Icone } = info;
            return (
              <div
                key={indice}
                className="extrato-item"
                style={{ animationDelay: `${Math.min(indice, 8) * 0.04}s` }}
              >
                <span className={`extrato-icone ${info.classe}`}>
                  <Icone />
                </span>
                <div className="extrato-info">
                  <p className="extrato-tipo">{info.titulo}</p>
                  <p className="extrato-meta">{info.meta}</p>
                </div>
                <div className="extrato-lado-direito">
                  {info.valor != null && info.sinal != null && (
                    <p className={`extrato-valor ${info.sinal > 0 ? "positivo" : "negativo"}`}>
                      {info.sinal > 0 ? "+" : "−"} R$ {Number(info.valor).toFixed(2)}
                    </p>
                  )}
                  <p className="extrato-lamport">Vetor [{evento.timestamp_vetorial.join(", ")}]</p>
                </div>
              </div>
            );
          })}

          {carregado && eventos.length === 0 && !erro && (
            <p className="estado-vazio">Nenhum evento encontrado ainda.</p>
          )}
        </div>
      </div>
    </AppShell>
  );
}
