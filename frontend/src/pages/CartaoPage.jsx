import { useEffect, useState } from "react";
import { ApiError, api } from "../api/client";
import AppShell from "../components/AppShell";
import ErrorBanner from "../components/ErrorBanner";
import { IconCopy, IconEye, IconEyeOff } from "../components/icons";
import { useAuth } from "../context/AuthContext";

// O ICEIBank não emite cartões de verdade - isto é um cartão virtual
// cosmético, gerado no próprio navegador a partir do número/nome da conta,
// só para dar uma identidade visual à conta dentro do app. Determinístico
// (mesma conta sempre gera o mesmo cartão) e nunca enviado ao backend.
function hashDeterministico(texto) {
  let h = 0;
  for (let i = 0; i < texto.length; i++) {
    h = (h << 5) - h + texto.charCodeAt(i);
    h |= 0;
  }
  return Math.abs(h);
}

function gerarCartaoVirtual(idConta, nomeAluno) {
  const h = hashDeterministico(`icei-cartao-${idConta}-${nomeAluno ?? ""}`);
  const bloco2 = String(1000 + (h % 9000)).padStart(4, "0");
  const bloco3 = String(1000 + (Math.floor(h / 9000) % 9000)).padStart(4, "0");
  const bloco4 = String(idConta % 10000).padStart(4, "0");
  const mes = String(1 + (h % 12)).padStart(2, "0");
  const ano = String(29 + (Math.floor(h / 97) % 6));
  const cvv = String(100 + (Math.floor(h / 7) % 900));
  return {
    numero: ["5412", bloco2, bloco3, bloco4],
    validade: `${mes}/${ano}`,
    cvv,
  };
}

export default function CartaoPage() {
  const { idConta } = useAuth();
  const [conta, setConta] = useState(null);
  const [erro, setErro] = useState(null);
  const [visivel, setVisivel] = useState(false);
  const [copiado, setCopiado] = useState(false);

  useEffect(() => {
    carregar();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function carregar() {
    setErro(null);
    try {
      const resposta = await api.consultarSaldo(idConta);
      setConta(resposta);
    } catch (e) {
      setErro(e instanceof ApiError ? e.message : "Falha inesperada ao conectar.");
    }
  }

  const cartao = gerarCartaoVirtual(idConta, conta?.nome_aluno);
  const numeroCompleto = cartao.numero.join("");

  async function copiarNumero() {
    try {
      await navigator.clipboard.writeText(numeroCompleto);
      setCopiado(true);
      setTimeout(() => setCopiado(false), 2000);
    } catch {
      // Clipboard pode não estar disponível (ex.: contexto sem HTTPS) - sem efeito visível.
    }
  }

  return (
    <AppShell titulo="Cartão virtual" subtitulo="Seu cartão para compras online, gerado automaticamente para esta conta.">
      <ErrorBanner erro={erro} />

      <div className="cartao-visual entrada">
        <div className="cartao-topo">
          <span className="cartao-selo">Virtual</span>
          <button
            type="button"
            className="toggle-visibilidade"
            onClick={() => setVisivel((v) => !v)}
            title={visivel ? "Ocultar dados" : "Mostrar dados"}
            aria-label={visivel ? "Ocultar dados" : "Mostrar dados"}
          >
            {visivel ? <IconEye /> : <IconEyeOff />}
          </button>
        </div>

        <div className="cartao-chip" aria-hidden="true" />

        <p className="cartao-numero">
          {visivel
            ? cartao.numero.join("  ")
            : `••••  ••••  ••••  ${cartao.numero[3]}`}
        </p>

        <div className="cartao-rodape">
          <div>
            <span className="cartao-rotulo">Titular</span>
            <p className="cartao-valor">{conta?.nome_aluno ?? `Conta ${idConta}`}</p>
          </div>
          <div>
            <span className="cartao-rotulo">Validade</span>
            <p className="cartao-valor">{visivel ? cartao.validade : "••/••"}</p>
          </div>
          <div>
            <span className="cartao-rotulo">CVV</span>
            <p className="cartao-valor">{visivel ? cartao.cvv : "•••"}</p>
          </div>
        </div>

        <p className="cartao-marca">ICEIBank</p>
      </div>

      <button
        type="button"
        className="secundario cartao-botao-copiar"
        onClick={copiarNumero}
        disabled={!conta}
      >
        <IconCopy />
        {copiado ? "Número copiado!" : "Copiar número do cartão"}
      </button>

      <div className="card entrada entrada-atraso-1">
        <div className="stack">
          <div className="linha-limite">
            <span className="rotulo">Conta vinculada</span>
            <span className="valor">{idConta}</span>
          </div>
          <div className="linha-limite">
            <span className="rotulo">Tipo</span>
            <span className="valor">Virtual (uso online)</span>
          </div>
          <div className="linha-limite">
            <span className="rotulo">Status</span>
            <span className="valor">Ativo</span>
          </div>
        </div>
        <p style={{ color: "var(--texto-suave)", fontSize: "0.8rem", marginTop: 16, lineHeight: 1.5 }}>
          Este cartão é uma representação visual gerada no próprio aplicativo a partir dos dados
          da sua conta - não é emitido por uma bandeira real e não deve ser usado em compras
          reais fora deste projeto.
        </p>
      </div>
    </AppShell>
  );
}
