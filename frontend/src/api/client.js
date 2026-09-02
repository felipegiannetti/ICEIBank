const AGENCIA_URL_KEY = "icei_agencia_url";
const TOKEN_KEY = "icei_token";
const ID_CONTA_KEY = "icei_id_conta";

export function getAgenciaUrl() {
  return localStorage.getItem(AGENCIA_URL_KEY) || "http://localhost:4000";
}

export function setAgenciaUrl(url) {
  localStorage.setItem(AGENCIA_URL_KEY, url);
}

export function getToken() {
  return localStorage.getItem(TOKEN_KEY);
}

export function getIdConta() {
  const valor = localStorage.getItem(ID_CONTA_KEY);
  return valor ? parseInt(valor, 10) : null;
}

export function setSessao(token, idConta) {
  localStorage.setItem(TOKEN_KEY, token);
  localStorage.setItem(ID_CONTA_KEY, String(idConta));
}

export function limparSessao() {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(ID_CONTA_KEY);
}

export class ApiError extends Error {
  constructor(status, mensagem) {
    super(mensagem);
    this.status = status;
  }
}

async function request(path, { method = "GET", body, autenticado = true } = {}) {
  const headers = { "Content-Type": "application/json" };
  if (autenticado) {
    const token = getToken();
    if (token) headers["Authorization"] = `Bearer ${token}`;
  }

  let resposta;
  try {
    resposta = await fetch(`${getAgenciaUrl()}${path}`, {
      method,
      headers,
      body: body ? JSON.stringify(body) : undefined,
    });
  } catch {
    throw new ApiError(0, "Não foi possível conectar à agência. Verifique se o servidor está rodando.");
  }

  let dados = null;
  try {
    dados = await resposta.json();
  } catch {
    dados = null;
  }

  if (!resposta.ok) {
    if (resposta.status === 401 && autenticado) {
      limparSessao();
    }
    const mensagem = dados?.erro || `Erro ${resposta.status}`;
    throw new ApiError(resposta.status, mensagem);
  }

  return dados;
}

export const api = {
  login: (idConta, senha) =>
    request("/auth/login", { method: "POST", body: { id_conta: idConta, senha }, autenticado: false }),

  consultarSaldo: (id) => request(`/contas/${id}`),

  depositar: (id, valor) => request(`/contas/${id}/depositar`, { method: "POST", body: { valor } }),

  sacar: (id, valor) => request(`/contas/${id}/sacar`, { method: "POST", body: { valor } }),

  transferir: (idOrigem, idDestino, valor) =>
    request("/transferencias", { method: "POST", body: { id_origem: idOrigem, id_destino: idDestino, valor } }),

  historico: (id, params = {}) => {
    const query = new URLSearchParams(
      Object.fromEntries(Object.entries(params).filter(([, v]) => v !== undefined && v !== ""))
    ).toString();
    return request(`/contas/${id}/historico${query ? `?${query}` : ""}`);
  },

  consultarLimite: (id) => request(`/contas/${id}/limite`),

  atualizarLimite: (id, novoLimite) =>
    request(`/contas/${id}/limite`, { method: "PUT", body: { novo_limite: novoLimite } }),
};
