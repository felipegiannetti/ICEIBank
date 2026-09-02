import { createContext, useContext, useState } from "react";
import { getIdConta, getToken, limparSessao, setSessao } from "../api/client";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [token, setToken] = useState(getToken());
  const [idConta, setIdConta] = useState(getIdConta());

  function login(novoToken, novoIdConta) {
    setSessao(novoToken, novoIdConta);
    setToken(novoToken);
    setIdConta(novoIdConta);
  }

  function logout() {
    limparSessao();
    setToken(null);
    setIdConta(null);
  }

  const valor = { token, idConta, autenticado: Boolean(token), login, logout };

  return <AuthContext.Provider value={valor}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  return useContext(AuthContext);
}
